from types import SimpleNamespace

from search.lightweight_ranker import LightweightRanker


def product(
    title: str,
    description: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        title=title,
        description=description,
    )


def test_title_match_gets_boost():
    ranker = LightweightRanker()

    results = [
        {
            "product": product("Outdoor Sun Hat"),
            "score": 0.030,
        },
        {
            "product": product("Lightweight Summer Dress"),
            "score": 0.029,
        },
    ]

    ranked = ranker.rank(
        "lightweight summer dress",
        results,
    )

    assert ranked[0]["product"].title == "Lightweight Summer Dress"


def test_semantic_order_is_preserved_when_no_lexical_match():
    ranker = LightweightRanker()

    results = [
        {
            "product": product("Beautiful Cotton Summer Dress"),
            "score": 0.030,
        },
        {
            "product": product("Casual Beach Outfit"),
            "score": 0.029,
        },
    ]

    ranked = ranker.rank(
        "வெயில்கால கடற்கரை பயணத்திற்கு வசதியான உடைகள்",
        results,
    )

    assert ranked[0]["product"].title == "Beautiful Cotton Summer Dress"
    assert ranked[1]["product"].title == "Casual Beach Outfit"


def test_empty_results_are_safe():
    ranker = LightweightRanker()

    assert ranker.rank("summer dress", []) == []


def test_empty_query_does_not_change_results():
    ranker = LightweightRanker()

    results = [
        {
            "product": product("Summer Dress"),
            "score": 0.030,
        },
        {
            "product": product("Beach Hat"),
            "score": 0.029,
        },
    ]

    ranked = ranker.rank("", results)

    assert ranked[0]["product"].title == "Summer Dress"
    assert ranked[1]["product"].title == "Beach Hat"