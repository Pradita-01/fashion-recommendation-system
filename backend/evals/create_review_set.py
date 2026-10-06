from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "dataset" / "candidates.jsonl"
OUTPUT_FILE = BASE_DIR / "dataset" / "golden_review.jsonl"


def load_candidates() -> list[dict]:
    records = []

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def main() -> None:
    records = load_candidates()

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as output:

        for record in records:
            review_candidates = []

            for candidate in record["candidates"]:
                review_candidates.append(
                    {
                        "rank": candidate["rank"],
                        "product_id": candidate["product_id"],
                        "parent_asin": candidate["parent_asin"],
                        "title": candidate["title"],
                        "category": candidate["category"],
                        "store": candidate["store"],
                        "retrieval_score": candidate["score"],
                        "relevance": None,
                        "reviewed": False,
                    }
                )

            review_record = {
                "query_id": record["query_id"],
                "query": record["query"],
                "language": record["language"],
                "category": record["category"],
                "candidates": review_candidates,
            }

            output.write(
                json.dumps(
                    review_record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(
        f"Created review set with "
        f"{len(records)} queries."
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()