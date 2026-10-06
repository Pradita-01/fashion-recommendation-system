from evals.metrics import (
    dcg_at_k,
    evaluate_dataset,
    evaluate_query,
    mean_reciprocal_rank,
    ndcg_at_k,
    reciprocal_rank,
)


def test_reciprocal_rank_first_result():
    assert reciprocal_rank([3, 0, 0]) == 1.0


def test_reciprocal_rank_third_result():
    assert reciprocal_rank([0, 0, 3]) == 1 / 3


def test_reciprocal_rank_no_relevant_result():
    assert reciprocal_rank([0, 0, 0]) == 0.0


def test_dcg_rewards_earlier_relevance():
    early = dcg_at_k([3, 2, 0], 3)
    late = dcg_at_k([0, 2, 3], 3)

    assert early > late


def test_ndcg_perfect_ranking():
    assert ndcg_at_k([3, 2, 1], 3) == 1.0


def test_ndcg_empty_relevance():
    assert ndcg_at_k([0, 0, 0], 3) == 0.0


def test_evaluate_query():
    result = evaluate_query(
        relevance=[3, 2, 0, 0],
        total_relevant=2,
        k=3,
    )

    assert result["ndcg_at_k"] > 0
    assert result["recall_at_k"] == 1.0
    assert result["reciprocal_rank"] == 1.0


def test_mean_reciprocal_rank():
    result = mean_reciprocal_rank(
        [
            [3, 0, 0],
            [0, 3, 0],
        ]
    )

    assert result == (1.0 + 0.5) / 2


def test_evaluate_dataset():
    result = evaluate_dataset(
        relevance_lists=[
            [3, 2, 0],
            [0, 3, 0],
        ],
        total_relevant_per_query=[
            2,
            1,
        ],
        k=3,
    )

    assert 0 < result["ndcg_at_k"] <= 1
    assert result["recall_at_k"] == 1.0
    assert result["mrr"] == 0.75