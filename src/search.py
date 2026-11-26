"""Hybrid product search in Qdrant: dense text + BM25 keywords + image vectors, fused with RRF, with exact filters."""
import atexit
import uuid
import warnings
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from qdrant_client import QdrantClient, models

from src.catalog import FACET_FIELDS, Product
from src.config import CANDIDATES_PER_SIGNAL, COLLECTION, QDRANT_PATH

BATCH = 64


@dataclass
class SearchQuery:
    text: str = ""
    filters: Dict[str, str] = field(default_factory=dict)  # facet name -> exact value
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    size: Optional[str] = None

    def has_filters(self) -> bool:
        return bool(self.filters) or self.min_price is not None or self.max_price is not None or bool(self.size)


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    # Embedded Qdrant locks its folder: one client per process.
    client = QdrantClient(path=QDRANT_PATH)
    atexit.register(client.close)  # close cleanly instead of during interpreter shutdown
    return client


def point_id(product_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"perfectfit:{product_id}"))


def create_collection(client: QdrantClient, text_dim: int, image_dim: int) -> None:
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        COLLECTION,
        vectors_config={
            "text": models.VectorParams(size=text_dim, distance=models.Distance.COSINE),
            "image": models.VectorParams(size=image_dim, distance=models.Distance.COSINE),
        },
        sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )
    # Payload indexes speed up filtering on a Qdrant server; embedded Qdrant ignores them (and warns).
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        for name in FACET_FIELDS + ("sizes",):
            client.create_payload_index(COLLECTION, name, models.PayloadSchemaType.KEYWORD)
        client.create_payload_index(COLLECTION, "price", models.PayloadSchemaType.FLOAT)


def index_products(client: QdrantClient, embedders, products: List[Product], image_paths: List[str], progress=None) -> None:
    """(Re)create the collection and upload every product with its three vectors."""
    create_collection(client, embedders.text_dim, embedders.image_dim)
    for start in range(0, len(products), BATCH):
        batch = products[start : start + BATCH]
        texts = [p.search_text() for p in batch]
        dense = embedders.text(texts)
        sparse = embedders.sparse(texts)
        images = embedders.image(image_paths[start : start + BATCH])
        client.upsert(
            COLLECTION,
            points=[
                models.PointStruct(
                    id=point_id(p.id),
                    vector={"text": d, "bm25": s, "image": i},
                    payload=p.to_dict(),
                )
                for p, d, s, i in zip(batch, dense, sparse, images)
            ],
        )
        if progress:
            progress(min(start + BATCH, len(products)), len(products))


def build_filter(q: SearchQuery) -> Optional[models.Filter]:
    must: List[models.Condition] = [
        models.FieldCondition(key=k, match=models.MatchValue(value=v)) for k, v in q.filters.items()
    ]
    if q.min_price is not None or q.max_price is not None:
        must.append(models.FieldCondition(key="price", range=models.Range(gte=q.min_price, lte=q.max_price)))
    if q.size:
        must.append(models.FieldCondition(key="sizes", match=models.MatchValue(value=q.size)))
    return models.Filter(must=must) if must else None


def _search_once(client, embedders, q: SearchQuery, image: Optional[bytes], limit: int) -> List[Product]:
    flt = build_filter(q)
    prefetch = []
    if q.text.strip():
        prefetch += [
            models.Prefetch(query=embedders.text_query(q.text), using="text", filter=flt, limit=CANDIDATES_PER_SIGNAL),
            models.Prefetch(query=embedders.sparse_query(q.text), using="bm25", filter=flt, limit=CANDIDATES_PER_SIGNAL),
            models.Prefetch(query=embedders.image_text([q.text])[0], using="image", filter=flt, limit=CANDIDATES_PER_SIGNAL),
        ]
    if image is not None:
        prefetch.append(
            models.Prefetch(query=embedders.image([image])[0], using="image", filter=flt, limit=CANDIDATES_PER_SIGNAL)
        )
    if not prefetch:
        return []
    result = client.query_points(
        COLLECTION,
        prefetch=prefetch,
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=limit,
        with_payload=True,
    )
    return [Product.from_dict(p.payload) for p in result.points]


# When nothing matches, drop filters in this order (gender last: the wrong department is rarely helpful)
RELAX_ORDER = ("size", "max_price", "min_price", "color", "category", "gender")


def _without(q: SearchQuery, name: str) -> SearchQuery:
    filters = {k: v for k, v in q.filters.items() if k != name}
    loose = SearchQuery(q.text, filters, q.min_price, q.max_price, q.size)
    if name in ("size", "max_price", "min_price"):
        setattr(loose, name, None)
    return loose


def search(client, embedders, q: SearchQuery, image: Optional[bytes] = None, limit: int = 8) -> Tuple[List[Product], bool]:
    """Return (products, relaxed). If the filters match nothing, drop them one by one and set relaxed=True."""
    products = _search_once(client, embedders, q, image, limit)
    relaxed = False
    for name in RELAX_ORDER:
        if products or not q.has_filters():
            break
        if name in q.filters or getattr(q, name, None) is not None:
            q = _without(q, name)
            relaxed = True
            products = _search_once(client, embedders, q, image, limit)
    return products, relaxed
