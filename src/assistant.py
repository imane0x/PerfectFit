"""One shopping turn: understand the request (text and/or image), search, then answer about real products only."""
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.catalog import Catalog, Product
from src.config import CATEGORY_MATCH_THRESHOLD, MAX_PRODUCTS_SHOWN, RESULTS_FOR_LLM
from src.search import SearchQuery, search

logger = logging.getLogger(__name__)

ANY = "any"

PARSE_SYSTEM = (
    "You turn a shopper's request into a product search for an online fashion store. "
    "If an image is attached, it shows what the shopper wants: describe the item in it (type, colour, pattern, "
    "material, style) inside search_text, combined with anything the shopper wrote. "
    "item_type is the kind of item in one or two plain words (for example: dress, sneakers, watch, handbag). "
    "Set color or gender only when the shopper explicitly asks for it or the image makes it unambiguous; "
    "otherwise use \"any\". search_text is a short English description of the wanted item, without prices."
)

ANSWER_SYSTEM = (
    "You are PerfectFit, a friendly and concise shopping assistant. You get the shopper's request and a list of "
    "candidate products from the store. Only talk about products from that list and never invent products, prices "
    "or details.\n"
    "matching_ids: ids of candidates that are the requested kind of item and meet what the shopper asked for "
    "(colour, gender, style...). Leave it empty only if no candidate does.\n"
    "alternative_ids: if matching_ids is empty, up to three candidates that come closest; otherwise empty. Leave "
    "it empty too if nothing in the list is a sensible alternative.\n"
    "answer: two or three sentences in the shopper's language about the products you picked. If there are "
    "matches, present them. If not, say honestly that the store does not have it and present the alternatives. "
    "Do not mention ids, the list, the search, other stores or store sections."
)


@dataclass
class Turn:
    answer: str
    products: List[Product] = field(default_factory=list)
    exact_match: bool = False
    query: Optional[SearchQuery] = None


def parse_schema(facets: Dict[str, List[str]], with_price: bool) -> dict:
    # Category is not an enum: small models choose badly from dozens of values, so the model names the item
    # type freely and Assistant.match_category maps it to a real category by embedding similarity.
    props: dict = {"search_text": {"type": "string"}, "item_type": {"type": "string"}}
    for name, values in facets.items():
        if name != "category":
            props[name] = {"type": "string", "enum": [ANY] + values}
    if with_price:
        props["min_price"] = {"type": ["number", "null"]}
        props["max_price"] = {"type": ["number", "null"]}
    return {"type": "object", "properties": props, "required": list(props)}


def _words(text: str) -> set:
    return set(re.findall(r"[a-z]+", text.lower()))


# Words that justify a gender filter in a text-only request
GENDER_WORDS = {
    "Men": {"men", "man", "mens", "male", "guy", "guys", "him", "husband", "boyfriend"},
    "Women": {"women", "woman", "womens", "female", "lady", "ladies", "her", "wife", "girlfriend"},
    "Boys": {"boy", "boys", "son"},
    "Girls": {"girl", "girls", "daughter"},
    "Unisex": {"unisex"},
}


def _mentioned(name: str, value: str, user_words: set) -> bool:
    if name == "gender":
        return bool(GENDER_WORDS.get(value, _words(value)) & user_words)
    return bool(_words(value) & user_words)


def to_query(raw: dict, facets: Dict[str, List[str]], user_text: str, has_image: bool = False) -> SearchQuery:
    """Validate model output against the real catalog values; anything unknown is dropped.

    Without an image, colour and gender filters are kept only if the shopper actually mentioned them,
    because small models like to guess them. Category is set separately by Assistant.match_category.
    """
    q = SearchQuery(text=str(raw.get("search_text") or user_text).strip())
    user_words = _words(user_text)
    for name, values in facets.items():
        v = raw.get(name)
        if name == "category" or not (isinstance(v, str) and v in values):
            continue
        if name in ("color", "gender") and not has_image and not _mentioned(name, v, user_words):
            continue
        q.filters[name] = v
    for key in ("min_price", "max_price"):
        v = raw.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
            setattr(q, key, float(v))
    return q


# Property order matters: the model picks products first, then writes about exactly those.
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "matching_ids": {"type": "array", "items": {"type": "string"}, "maxItems": MAX_PRODUCTS_SHOWN},
        "alternative_ids": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        "answer": {"type": "string"},
    },
    "required": ["matching_ids", "alternative_ids", "answer"],
}


class Assistant:
    def __init__(self, catalog: Catalog, client, embedders, vlm):
        self.catalog = catalog
        self.client = client
        self.embedders = embedders
        self.vlm = vlm
        self.facets = catalog.facets()
        self.with_price = catalog.has_prices()
        self.categories = self.facets.get("category", [])
        self._category_vectors = embedders.text(self.categories) if self.categories else []

    def match_category(self, item_type: str) -> Optional[str]:
        """Nearest catalog category to a free-text item type, or None if nothing is close enough."""
        if not item_type.strip() or not self.categories:
            return None
        if item_type.strip().lower() in (ANY, "item", "product", "something"):
            return None
        q = self.embedders.text([item_type])[0]
        scores = [sum(a * b for a, b in zip(q, c)) for c in self._category_vectors]
        best = max(range(len(scores)), key=scores.__getitem__)
        logger.info("item_type %r -> %s (%.3f)", item_type, self.categories[best], scores[best])
        return self.categories[best] if scores[best] >= CATEGORY_MATCH_THRESHOLD else None

    def understand(self, text: str, image: Optional[bytes]) -> SearchQuery:
        user = f"Shopper: {text or '(no text, only the image)'}"
        raw = self.vlm.json(PARSE_SYSTEM, user, parse_schema(self.facets, self.with_price), [image] if image else None)
        q = to_query(raw, self.facets, text, has_image=image is not None)
        category = self.match_category(str(raw.get("item_type") or ""))
        if category:
            q.filters["category"] = category
        logger.info("Parsed query: %s", q)
        return q

    def respond(self, text: str, image: Optional[bytes], q: SearchQuery, candidates: List[Product], relaxed: bool) -> Turn:
        if not candidates:
            return Turn("Sorry, I couldn't find anything like that in the store.", query=q)
        note = (
            "\nNote: nothing in the store matches all of the shopper's requirements; these are the nearest items."
            if relaxed
            else ""
        )
        listing = "\n".join(p.summary() for p in candidates)
        user = f"Shopper request: {text or '(an image of the wanted item)'}\n\nCandidate products:\n{listing}{note}"
        raw = self.vlm.json(ANSWER_SYSTEM, user, ANSWER_SCHEMA, [image] if image else None)

        by_id = {p.id: p for p in candidates}

        def pick(key: str) -> List[Product]:
            ids = raw.get(key) if isinstance(raw.get(key), list) else []
            return [by_id[i] for i in dict.fromkeys(map(str, ids)) if i in by_id]

        answer = str(raw.get("answer") or "").strip()
        if not answer:  # model failed to produce usable output: fall back to the search ranking
            return Turn("Here is what I found in the store.", candidates[:MAX_PRODUCTS_SHOWN], False, q)
        matches = pick("matching_ids")
        if matches:
            return Turn(answer, matches[:MAX_PRODUCTS_SHOWN], not relaxed, q)
        return Turn(answer, pick("alternative_ids"), False, q)

    def ask(self, text: str, image: Optional[bytes] = None) -> Turn:
        q = self.understand(text, image)
        candidates, relaxed = search(self.client, self.embedders, q, image, limit=RESULTS_FOR_LLM)
        return self.respond(text, image, q, candidates, relaxed)


_assistant: Optional[Assistant] = None


def get_assistant() -> Assistant:
    """Build the assistant once per process (loads catalog, embedding models, Qdrant and the VLM client)."""
    global _assistant
    if _assistant is None:
        from src.catalog import get_catalog
        from src.config import COLLECTION
        from src.embeddings import get_embedders
        from src.llm import get_vlm
        from src.search import get_client

        client = get_client()
        if not client.collection_exists(COLLECTION):
            raise RuntimeError("No product index found. Run `python ingest.py` first.")
        _assistant = Assistant(get_catalog(), client, get_embedders(), get_vlm())
    return _assistant
