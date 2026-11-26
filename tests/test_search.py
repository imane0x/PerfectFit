from src.search import SearchQuery, build_filter, search


def ids(products):
    return [p.id for p in products]


def test_text_search_ranks_relevant_first(indexed, embedders):
    products, relaxed = search(indexed, embedders, SearchQuery(text="red dress"))
    assert ids(products)[0] == "1"
    assert relaxed is False


def test_filters_are_exact(indexed, embedders):
    products, relaxed = search(indexed, embedders, SearchQuery(text="shirt", filters={"gender": "Women"}))
    assert set(ids(products)) <= {"1", "4", "5"}
    assert ids(products)[0] == "4"
    assert not relaxed


def test_price_and_size_filters(indexed, embedders):
    q = SearchQuery(text="shirt", max_price=50, size="M")
    products, relaxed = search(indexed, embedders, q)
    assert ids(products) == ["4"]
    assert not relaxed


def test_relaxes_filters_when_nothing_matches(indexed, embedders):
    # No red shirts for men: colour is dropped first, category and gender are kept
    q = SearchQuery(text="red shirt", filters={"category": "Shirts", "color": "Red", "gender": "Men"})
    products, relaxed = search(indexed, embedders, q)
    assert relaxed is True
    assert ids(products) == ["3"]


def test_image_only_search(indexed, embedders):
    products, _ = search(indexed, embedders, SearchQuery(), image=b"navy check shirt")
    assert ids(products)[0] == "3"


def test_empty_query_returns_nothing(indexed, embedders):
    assert search(indexed, embedders, SearchQuery()) == ([], False)


def test_build_filter_none_without_conditions():
    assert build_filter(SearchQuery(text="x")) is None
