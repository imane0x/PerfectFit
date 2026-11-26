import pytest

from src.assistant import Assistant, parse_schema, to_query

FACETS = {"category": ["Dresses", "Shirts"], "color": ["Navy Blue", "Red"], "gender": ["Men", "Women"]}


class StubVLM:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def json(self, system, user, schema, images=None):
        self.calls.append({"user": user, "schema": schema, "images": images})
        return self.responses.pop(0)


def test_parse_schema_uses_catalog_values_and_free_item_type():
    schema = parse_schema(FACETS, with_price=False)
    assert "category" not in schema["properties"]
    assert schema["properties"]["item_type"] == {"type": "string"}
    assert schema["properties"]["color"]["enum"] == ["any", "Navy Blue", "Red"]
    assert "max_price" not in schema["properties"]
    assert "max_price" in parse_schema(FACETS, with_price=True)["properties"]


def test_to_query_drops_unknown_and_unmentioned_values():
    raw = {"search_text": "shirt", "color": "Red", "gender": "Women", "category": "Shirts"}
    q = to_query(raw, FACETS, "a shirt please")
    assert q.filters == {}  # colour/gender guessed, category comes from match_category


def test_to_query_keeps_mentioned_values():
    q = to_query({"search_text": "red dress", "color": "Red", "gender": "Women"}, FACETS, "red dress for my wife")
    assert q.filters == {"color": "Red", "gender": "Women"}


def test_women_does_not_count_as_men():
    q = to_query({"search_text": "shirt", "gender": "Men"}, FACETS, "women's shirt")
    assert q.filters == {}


def test_image_allows_visual_attributes():
    q = to_query({"search_text": "shirt", "color": "Navy Blue", "gender": "Men"}, FACETS, "like this", has_image=True)
    assert q.filters == {"color": "Navy Blue", "gender": "Men"}


def test_to_query_validates_prices():
    q = to_query({"search_text": "x", "max_price": 50, "min_price": -3}, FACETS, "under 50")
    assert q.max_price == 50.0 and q.min_price is None
    assert to_query({"search_text": "x", "max_price": True}, FACETS, "x").max_price is None


def test_to_query_falls_back_to_user_text():
    assert to_query({}, FACETS, "red dress").text == "red dress"


def make(catalog, embedders, indexed, *responses):
    return Assistant(catalog, indexed, embedders, StubVLM(*responses))


def test_match_category(catalog, embedders, indexed):
    a = make(catalog, embedders, indexed)
    assert a.match_category("dresses") == "Dresses"
    assert a.match_category("kayak") is None
    assert a.match_category("any") is None


def test_ask_returns_matches(catalog, embedders, indexed):
    a = make(
        catalog, embedders, indexed,
        {"search_text": "red dress", "item_type": "dresses", "color": "Red", "gender": "any"},
        {"matching_ids": ["1", "999"], "alternative_ids": [], "answer": "We have a red summer dress."},
    )
    turn = a.ask("red dress")
    assert turn.query.filters == {"category": "Dresses", "color": "Red"}
    assert [p.id for p in turn.products] == ["1"]  # unknown id 999 dropped
    assert turn.exact_match is True


def test_ask_no_match_shows_only_alternatives(catalog, embedders, indexed):
    a = make(
        catalog, embedders, indexed,
        {"search_text": "green dress", "item_type": "dresses", "color": "any", "gender": "any"},
        {"matching_ids": [], "alternative_ids": [], "answer": "Sorry, we don't have that."},
    )
    turn = a.ask("green dress")
    assert turn.products == [] and turn.exact_match is False


def test_relaxed_search_is_never_exact(catalog, embedders, indexed):
    a = make(
        catalog, embedders, indexed,
        {"search_text": "red shirt", "item_type": "shirts", "color": "Red", "gender": "Men"},
        {"matching_ids": ["3"], "alternative_ids": [], "answer": "Closest is a navy shirt."},
    )
    turn = a.ask("red shirt for men")
    assert turn.exact_match is False
    assert "nothing in the store matches" in a.vlm.calls[1]["user"]


def test_invalid_model_output_falls_back_to_ranking(catalog, embedders, indexed):
    a = make(catalog, embedders, indexed, {}, {})
    turn = a.ask("red dress")
    assert turn.products and turn.products[0].id == "1"


def test_image_is_passed_to_the_model(catalog, embedders, indexed):
    a = make(
        catalog, embedders, indexed,
        {"search_text": "navy check shirt", "item_type": "shirts", "color": "any", "gender": "any"},
        {"matching_ids": ["3"], "alternative_ids": [], "answer": "This one."},
    )
    a.ask("", image=b"navy check shirt")
    assert a.vlm.calls[0]["images"] == [b"navy check shirt"]
    assert a.vlm.calls[1]["images"] == [b"navy check shirt"]


@pytest.mark.parametrize("bad", ["../../etc/passwd", "/etc/passwd"])
def test_catalog_image_path_cannot_escape(catalog, bad):
    p = catalog.get("1")
    p.image = bad
    assert catalog.image_path(p) is None
