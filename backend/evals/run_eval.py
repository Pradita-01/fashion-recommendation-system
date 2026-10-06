from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Project path
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

EVAL_DIR = PROJECT_ROOT / "backend" / "evals"
DATASET_DIR = EVAL_DIR / "dataset"

# IMPORTANT:
# The golden labels live in golden_review.jsonl.
# candidates.jsonl is the generated retrieval output and is NOT the
# human-labelled golden dataset.
GOLDEN_FILE = DATASET_DIR / "golden_review.jsonl"

REPORT_DIR = EVAL_DIR / "reports"
REPORT_FILE = REPORT_DIR / "retrieval_ablation_report.json"


# ---------------------------------------------------------------------------
# Imports from the project
# ---------------------------------------------------------------------------
from statistics import mean

from evals.metrics import (  # noqa: E402
    mrr_at_k,
    ndcg_at_k,
    recall_at_k,
)


# ---------------------------------------------------------------------------
# Golden dataset loading
# ---------------------------------------------------------------------------


def load_golden_queries() -> list[dict[str, Any]]:
    """
    Load the manually reviewed evaluation dataset.

    Expected JSONL structure:

    {
        "query_id": "q01",
        "query": "comfortable beach outfit for summer",
        "candidates": [
            {
                "product_id": "...",
                "relevance": 3
            },
            ...
        ]
    }

    Each query must contain exactly 10 labelled candidates.
    """

    if not GOLDEN_FILE.exists():
        raise FileNotFoundError(
            f"\nGolden review file not found:\n{GOLDEN_FILE}\n"
        )

    queries: list[dict[str, Any]] = []

    with GOLDEN_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, raw_line in enumerate(file, start=1):

            line = raw_line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in {GOLDEN_FILE} "
                    f"at line {line_number}."
                ) from exc

            query_id = str(record.get("query_id", "")).strip()
            query = str(record.get("query", "")).strip()

            if not query_id:
                raise ValueError(
                    f"Line {line_number} is missing query_id."
                )

            if not query:
                raise ValueError(
                    f"{query_id} is missing the query text."
                )

            # ---------------------------------------------------------------
            # CORRECT STRUCTURE:
            #
            # The candidate list is nested inside the query record.
            # ---------------------------------------------------------------

            candidates = record.get("candidates")

            if candidates is None:
                raise ValueError(
                    f"{query_id} is missing the 'candidates' field."
                )

            if not isinstance(candidates, list):
                raise ValueError(
                    f"{query_id} has an invalid 'candidates' field. "
                    "Expected a list."
                )

            if len(candidates) != 10:
                raise ValueError(
                    f"{query_id} has {len(candidates)} candidates; "
                    "expected 10."
                )

            # ---------------------------------------------------------------
            # Validate every candidate
            # ---------------------------------------------------------------

            normalized_candidates: list[dict[str, Any]] = []

            for candidate_index, candidate in enumerate(candidates, start=1):

                if not isinstance(candidate, dict):
                    raise ValueError(
                        f"{query_id} candidate #{candidate_index} "
                        "is not an object."
                    )

                if candidate.get("product_id") is None:
                    raise ValueError(
                        f"{query_id} candidate #{candidate_index} "
                        "is missing product_id."
                    )

                if candidate.get("relevance") is None:
                    raise ValueError(
                        f"{query_id} candidate #{candidate_index} "
                        "is missing relevance."
                    )

                try:
                    relevance = int(candidate["relevance"])
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"{query_id} candidate #{candidate_index} "
                        "has invalid relevance: "
                        f"{candidate['relevance']!r}"
                    ) from exc

                normalized_candidates.append(
                    {
                        **candidate,
                        "product_id": str(candidate["product_id"]),
                        "relevance": relevance,
                    }
                )

            queries.append(
                {
                    "query_id": query_id,
                    "query": query,
                    "items": normalized_candidates,
                }
            )

    queries.sort(
        key=lambda item: item["query_id"]
    )

    if not queries:
        raise ValueError(
            "No golden queries were found."
        )

    return queries


# ---------------------------------------------------------------------------
# Relevance lookup
# ---------------------------------------------------------------------------


def relevance_lookup(
    query_record: dict[str, Any],
) -> dict[str, int]:
    """
    Convert the golden candidate list into:

        product_id -> relevance score
    """

    return {
        str(item["product_id"]): int(item["relevance"])
        for item in query_record["items"]
    }


# ---------------------------------------------------------------------------
# Metric calculation
# ---------------------------------------------------------------------------


def calculate_metrics(
    ranked_product_ids: list[str],
    relevance: dict[str, int],
    k: int = 10,
) -> dict[str, float]:

    ranked_relevances = [
        relevance.get(product_id, 0)
        for product_id in ranked_product_ids[:k]
    ]

    return {
        "ndcg_at_10": float(
            ndcg_at_k(
                ranked_relevances,
                k=k,
            )
        ),
        "recall_at_10": float(
            recall_at_k(
                ranked_relevances,
                relevance,
                k=k,
            )
        ),
        "mrr": float(
            mrr_at_k(
                ranked_relevances,
                k=k,
            )
        ),
    }


# ---------------------------------------------------------------------------
# Safe metric averaging
# ---------------------------------------------------------------------------


def average_results(
    results: list[dict[str, Any]],
) -> dict[str, float]:

    if not results:
        return {
            "ndcg_at_10": 0.0,
            "recall_at_10": 0.0,
            "mrr": 0.0,
        }

    return {
        "ndcg_at_10": mean(
            [float(item["ndcg_at_10"]) for item in results]
        ),
        "recall_at_10": mean(
            [float(item["recall_at_10"]) for item in results]
        ),
        "mrr": mean(
            [float(item["mrr"]) for item in results]
        ),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:

    print()
    print("=" * 78)
    print("FASHION RECOMMENDATION — GOLDEN EVALUATION")
    print("=" * 78)
    print()

    print(f"Golden dataset:")
    print(f"  {GOLDEN_FILE}")
    print()

    queries = load_golden_queries()

    print(
        f"Loaded {len(queries)} golden queries."
    )

    total_candidates = sum(
        len(query["items"])
        for query in queries
    )

    print(
        f"Loaded {total_candidates} manually labelled candidates."
    )

    print()

    # -----------------------------------------------------------------------
    # IMPORTANT:
    #
    # At this point we have validated the golden dataset.
    #
    # The actual retrieval ablation is performed by ablation.py.
    # -----------------------------------------------------------------------

    try:
        from evals.ablation import run_ablation
    except ImportError as exc:
        raise RuntimeError(
            "Could not import evals.ablation.run_ablation()."
        ) from exc

    print("Running retrieval ablation...")
    print()

    report = run_ablation(
        queries=queries,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REPORT_FILE.open(
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
    print("EVALUATION COMPLETE")
    print("=" * 78)
    print()

    print(
        f"Report written to:\n{REPORT_FILE}"
    )

    print()


if __name__ == "__main__":
    main()