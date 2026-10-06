from __future__ import annotations

import json
from pathlib import Path

from evals.metrics import evaluate_query


BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "dataset" / "golden_review.jsonl"


def main() -> None:
    results = []

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)

            if record["query_id"] not in {
                "q01",
                "q02",
                "q03",
                "q04",
                "q05",
                "q06",
                "q07",
                "q08",
                "q09",
                "q10",
                "q11",
                "q12",
                "q13",
                "q14",
                "q15",
                "q16",
                "q17",
                "q18",
                "q19",
                "q20"
            }:
                continue

            candidates = record["candidates"]

            relevance = [
                candidate["relevance"]
                for candidate in candidates
            ]

            if any(
                score is None
                for score in relevance
            ):
                raise ValueError(
                    f"{record['query_id']} "
                    "contains unlabeled candidates."
                )

            total_relevant = sum(
                score > 0
                for score in relevance
            )

            metrics = evaluate_query(
                relevance=relevance,
                total_relevant=total_relevant,
                k=10,
            )

            results.append(
                {
                    "query_id": record["query_id"],
                    "query": record["query"],
                    **metrics,
                }
            )

    if not results:
        raise RuntimeError(
            "No reviewed queries found."
        )

    mean_ndcg = sum(
        result["ndcg_at_k"]
        for result in results
    ) / len(results)

    mean_recall = sum(
        result["recall_at_k"]
        for result in results
    ) / len(results)

    mrr = sum(
        result["reciprocal_rank"]
        for result in results
    ) / len(results)

    print()
    print("=" * 70)
    print("GOLDEN EVALUATION — q01 to q15")
    print("=" * 70)

    for result in results:
        print()
        print(
            f"{result['query_id']}: "
            f"{result['query']}"
        )
        print(
            f"  nDCG@10   = "
            f"{result['ndcg_at_k']:.4f}"
        )
        print(
            f"  Recall@10 = "
            f"{result['recall_at_k']:.4f}"
        )
        print(
            f"  RR        = "
            f"{result['reciprocal_rank']:.4f}"
        )

    print()
    print("-" * 70)
    print("MEAN RESULTS")
    print("-" * 70)

    print(
        f"nDCG@10   : {mean_ndcg:.4f}"
    )
    print(
        f"Recall@10 : {mean_recall:.4f}"
    )
    print(
        f"MRR       : {mrr:.4f}"
    )
    print("-" * 70)


if __name__ == "__main__":
    main()