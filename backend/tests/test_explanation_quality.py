from explanation.quality import ExplanationQuality


def test_valid_explanation_passes() -> None:
    explanation = (
        "This product matches because the title describes "
        "it as a summer beach dress."
    )

    assert ExplanationQuality.validate(explanation) is True


def test_empty_explanation_fails() -> None:
    assert ExplanationQuality.validate("") is False


def test_none_explanation_fails() -> None:
    assert ExplanationQuality.validate(None) is False


def test_uncertain_explanation_fails() -> None:
    explanation = (
        "I don't know whether this product is suitable "
        "for the requested occasion."
    )

    assert ExplanationQuality.validate(explanation) is False