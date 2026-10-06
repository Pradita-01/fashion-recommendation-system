from decimal import Decimal

from explanation.grounded import GroundedExplanation
from shared.models import Product


class FakeLLM:
    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt = ""

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


def make_product() -> Product:
    return Product(
        id=1,
        parent_asin="TEST123",
        title="Lightweight Linen Beach Shirt",
        description="Lightweight casual shirt suitable for summer.",
        main_category="AMAZON FASHION",
        store="Example Store",
        price=Decimal("29.99"),
        average_rating=Decimal("4.50"),
        rating_number=100,
        features=["Lightweight fabric", "Casual fit"],
        categories=["Shirts", "Beachwear"],
        details={"color": "Blue"},
        image_url=None,
        catalog_version_id=1,
    )


def test_grounded_explanation_returns_llm_explanation() -> None:
    llm = FakeLLM(
        '{"explanation": "This lightweight casual shirt fits your summer beach use."}'
    )

    service = GroundedExplanation(llm)

    result = service.explain(
        query="comfortable beach outfit for summer",
        product=make_product(),
    )

    assert result == (
        "This lightweight casual shirt fits your summer beach use."
    )


def test_grounded_prompt_contains_product_facts() -> None:
    llm = FakeLLM(
        '{"explanation": "This product matches the query."}'
    )

    service = GroundedExplanation(llm)

    service.explain(
        query="blue beach shirt",
        product=make_product(),
    )

    assert "Lightweight Linen Beach Shirt" in llm.last_prompt
    assert "Lightweight fabric" in llm.last_prompt
    assert "Blue" in llm.last_prompt


def test_grounded_explanation_rejects_invalid_json() -> None:
    llm = FakeLLM("not valid json")

    service = GroundedExplanation(llm)

    try:
        service.explain(
            query="beach shirt",
            product=make_product(),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "invalid explanation JSON" in str(exc)


def test_grounded_explanation_rejects_missing_explanation() -> None:
    llm = FakeLLM('{"other": "value"}')

    service = GroundedExplanation(llm)

    try:
        service.explain(
            query="beach shirt",
            product=make_product(),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "missing or invalid" in str(exc)