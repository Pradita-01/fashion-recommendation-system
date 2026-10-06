from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_FILE = (
    PROJECT_ROOT
    / "backend"
    / "evals"
    / "dataset"
    / "golden_review.jsonl"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "backend"
    / "evals"
    / "reports"
    / "retrieval_ablation_report.json"
)

PARITY_REPORT_FILE = (
    PROJECT_ROOT
    / "backend"
    / "evals"
    / "reports"
    / "language_parity_report.json"
)


# ---------------------------------------------------------------------------
# Language mapping
# ---------------------------------------------------------------------------

LANGUAGE_BY_QUERY_ID = {
    "q16": "Tamil",
    "q17": "Tamil",
    "q18": "Hindi",
}


def language_for_query(query_id: str) -> str:
    return LANGUAGE_BY_QUERY_ID.get(
        query_id,
        "English",
    )


# ---------------------------------------------------------------------------
# Load golden queries
# ---------------------------------------------------------------------------

def load_queries() -> dict[str, str]:
    queries: dict[str, str] = {}

    with DATASET_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for raw_line in file:

            line = raw_line.strip()

            if not line:
                continue

            record = json.loads(line)

            query_id = str(record["query_id"])
            query = str(record["query"])

            queries[query_id] = query

    return queries


# ---------------------------------------------------------------------------
# Load retrieval report
# ---------------------------------------------------------------------------

def load_hybrid_results() -> list[dict[str, Any]]:
    if not REPORT_FILE.exists():
        raise FileNotFoundError(
            f"Retrieval report not found:\n{REPORT_FILE}"
        )

    with REPORT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        report = json.load(file)

    hybrid = report.get("hybrid")

    if not hybrid:
        raise ValueError(
            "The retrieval report does not contain hybrid results."
        )

    return hybrid.get("per_query", [])


# ---------------------------------------------------------------------------
# Calculate parity
# ---------------------------------------------------------------------------

def calculate_language_metrics(
    results: list[dict[str, Any]],
    queries: dict[str, str],
) -> dict[str, dict[str, Any]]:

    grouped: dict[str, list[dict[str, Any]]] = {}

    for result in results:

        query_id = str(result["query_id"])

        language = language_for_query(
            query_id
        )

        grouped.setdefault(
            language,
            [],
        ).append(result)

    output: dict[str, dict[str, Any]] = {}

    for language, language_results in grouped.items():

        ndcg_values = [
            float(item["ndcg_at_10"])
            for item in language_results
        ]

        recall_values = [
            float(item["recall_at_10"])
            for item in language_results
        ]

        mrr_values = [
            float(item["mrr"])
            for item in language_results
        ]

        output[language] = {
            "query_count": len(language_results),
            "queries": [
                {
                    "query_id": item["query_id"],
                    "query": queries.get(
                        str(item["query_id"]),
                        "",
                    ),
                    "ndcg_at_10": float(
                        item["ndcg_at_10"]
                    ),
                    "recall_at_10": float(
                        item["recall_at_10"]
                    ),
                    "mrr": float(
                        item["mrr"]
                    ),
                }
                for item in language_results
            ],
            "mean": {
                "ndcg_at_10": mean(ndcg_values),
                "recall_at_10": mean(recall_values),
                "mrr": mean(mrr_values),
            },
        }

    return output


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:

    print()
    print("=" * 78)
    print("MULTILINGUAL LANGUAGE PARITY")
    print("=" * 78)
    print()

    queries = load_queries()

    hybrid_results = load_hybrid_results()

    language_results = calculate_language_metrics(
        results=hybrid_results,
        queries=queries,
    )

    print(
        f"{'Language':<12}"
        f"{'Queries':>10}"
        f"{'nDCG@10':>14}"
        f"{'Recall@10':>14}"
        f"{'MRR':>10}"
    )

    print("-" * 78)

    for language in (
        "English",
        "Tamil",
        "Hindi",
    ):

        metrics = language_results.get(
            language
        )

        if metrics is None:
            continue

        values = metrics["mean"]

        print(
            f"{language:<12}"
            f"{metrics['query_count']:>10}"
            f"{values['ndcg_at_10']:>14.4f}"
            f"{values['recall_at_10']:>14.4f}"
            f"{values['mrr']:>10.4f}"
        )

    print()
    print("-" * 78)
    print("LANGUAGE PARITY DETAILS")
    print("-" * 78)

    for language in (
        "English",
        "Tamil",
        "Hindi",
    ):

        metrics = language_results.get(
            language
        )

        if metrics is None:
            continue

        print()
        print(language)

        for item in metrics["queries"]:

            print(
                f"  {item['query_id']}: "
                f"nDCG={item['ndcg_at_10']:.4f}, "
                f"Recall={item['recall_at_10']:.4f}, "
                f"MRR={item['mrr']:.4f}"
            )

    report = {
        "dataset": str(DATASET_FILE),
        "source_report": str(REPORT_FILE),
        "languages": language_results,
    }

    PARITY_REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with PARITY_REPORT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 78)
    print("LANGUAGE PARITY COMPLETE")
    print("=" * 78)
    print()
    print(
        f"Report written to:\n{PARITY_REPORT_FILE}"
    )
    print()


if __name__ == "__main__":
    main()