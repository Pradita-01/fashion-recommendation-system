from __future__ import annotations

import math
from typing import Iterable


# ============================================================================
# HELPERS
# ============================================================================


def _as_relevance_list(
    relevances: Iterable[int | float],
) -> list[float]:
    return [float(value) for value in relevances]


# ============================================================================
# DCG
# ============================================================================


def dcg_at_k(
    relevances: Iterable[int | float],
    k: int = 10,
) -> float:
    if k <= 0:
        return 0.0

    values = _as_relevance_list(relevances)[:k]

    score = 0.0

    for rank, relevance in enumerate(values, start=1):
        score += relevance / math.log2(rank + 1)

    return score


# ============================================================================
# nDCG
# ============================================================================


def ndcg_at_k(
    relevances: Iterable[int | float],
    k: int = 10,
) -> float:
    if k <= 0:
        return 0.0

    values = _as_relevance_list(relevances)

    if not values:
        return 0.0

    actual = dcg_at_k(values, k=k)

    ideal_values = sorted(values, reverse=True)

    ideal = dcg_at_k(
        ideal_values,
        k=k,
    )

    if ideal == 0.0:
        return 0.0

    return actual / ideal


# ============================================================================
# Reciprocal Rank
# ============================================================================


def reciprocal_rank(
    relevances: Iterable[int | float],
) -> float:
    """
    Reciprocal rank of the first relevant result.

    A relevance value > 0 is considered relevant.
    """

    values = _as_relevance_list(relevances)

    for rank, relevance in enumerate(values, start=1):
        if relevance > 0:
            return 1.0 / rank

    return 0.0


def mean_reciprocal_rank(
    relevance_lists: Iterable[Iterable[int | float]],
) -> float:
    """
    Mean Reciprocal Rank across multiple queries.
    """

    values = [
        reciprocal_rank(relevances)
        for relevances in relevance_lists
    ]

    if not values:
        return 0.0

    return sum(values) / len(values)


# ============================================================================
# Recall
# ============================================================================


def recall_at_k(
    ranked_relevances: Iterable[int | float],
    relevance: dict[str, int] | None = None,
    k: int = 10,
) -> float:
    """
    Recall at K.

    When `relevance` is supplied:
        denominator = all known relevant products.

    When `relevance` is omitted:
        the function uses the positive relevance values supplied.
        This form is retained for compatibility with unit tests.
    """

    if k <= 0:
        return 0.0

    ranked_values = _as_relevance_list(
        ranked_relevances
    )[:k]

    if relevance is not None:
        total_relevant = sum(
            1
            for score in relevance.values()
            if float(score) > 0
        )

        if total_relevant == 0:
            return 0.0

        retrieved_relevant = sum(
            1
            for score in ranked_values
            if score > 0
        )

        return min(
            retrieved_relevant / total_relevant,
            1.0,
        )

    # Compatibility form.
    total_relevant = sum(
        1
        for score in ranked_values
        if score > 0
    )

    if total_relevant == 0:
        return 0.0

    retrieved_relevant = sum(
        1
        for score in ranked_values
        if score > 0
    )

    return min(
        retrieved_relevant / total_relevant,
        1.0,
    )


# ============================================================================
# Single-query evaluation
# ============================================================================


def evaluate_query(
    relevance: Iterable[int | float],
    total_relevant: int,
    k: int = 10,
) -> dict[str, float]:
    """
    Evaluate one ranked query.

    This compatibility API is used by the existing unit tests and
    evaluation utilities.
    """

    values = _as_relevance_list(relevance)[:k]

    ndcg = ndcg_at_k(
        values,
        k=k,
    )

    retrieved_relevant = sum(
        1
        for score in values
        if score > 0
    )

    if total_relevant <= 0:
        recall = 0.0
    else:
        recall = min(
            retrieved_relevant / total_relevant,
            1.0,
        )

    rr = reciprocal_rank(values)

    return {
        "ndcg_at_k": ndcg,
        "recall_at_k": recall,
        "reciprocal_rank": rr,
    }


# ============================================================================
# Dataset evaluation
# ============================================================================


def evaluate_dataset(
    relevance_lists: Iterable[Iterable[int | float]],
    total_relevant_per_query: Iterable[int],
    k: int = 10,
) -> dict[str, float]:
    """
    Evaluate a collection of ranked queries.

    Returns mean nDCG, mean Recall, and MRR.
    """

    relevance_lists = list(relevance_lists)
    total_relevant_per_query = list(
        total_relevant_per_query
    )

    if not relevance_lists:
        return {
            "ndcg_at_k": 0.0,
            "recall_at_k": 0.0,
            "mrr": 0.0,
        }

    query_metrics = []

    for relevances, total_relevant in zip(
        relevance_lists,
        total_relevant_per_query,
    ):
        query_metrics.append(
            evaluate_query(
                relevance=relevances,
                total_relevant=total_relevant,
                k=k,
            )
        )

    return {
        "ndcg_at_k": sum(
            item["ndcg_at_k"]
            for item in query_metrics
        ) / len(query_metrics),

        "recall_at_k": sum(
            item["recall_at_k"]
            for item in query_metrics
        ) / len(query_metrics),

        "mrr": mean_reciprocal_rank(
            relevance_lists
        ),
    }


# ============================================================================
# Mean helper
# ============================================================================


def mean_metric(
    values: Iterable[int | float],
) -> float:
    values_list = [
        float(value)
        for value in values
    ]

    if not values_list:
        return 0.0

    return sum(values_list) / len(values_list)


# ============================================================================
# Modern convenience API
# ============================================================================


def mrr_at_k(
    relevances: Iterable[int | float],
    k: int = 10,
) -> float:
    return reciprocal_rank(
        _as_relevance_list(relevances)[:k]
    )


def calculate_metrics(
    relevances: Iterable[int | float],
    relevance: dict[str, int] | None = None,
    k: int = 10,
) -> dict[str, float]:
    values = _as_relevance_list(relevances)

    return {
        "ndcg_at_10": ndcg_at_k(
            values,
            k=k,
        ),
        "recall_at_10": recall_at_k(
            values,
            relevance,
            k=k,
        ),
        "mrr": mrr_at_k(
            values,
            k=k,
        ),
    }
