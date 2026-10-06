from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "dataset" / "golden_review.jsonl"
OUTPUT_FILE = BASE_DIR / "dataset" / "golden_review.jsonl"


APPROVED_LABELS = {
    "q01": [3, 3, 2, 2, 3, 2, 3, 3, 1, 3],
    "q02": [3, 3, 3, 1, 1, 3, 3, 3, 3, 3],
    "q03": [3, 3, 2, 2, 3, 3, 2, 2, 1, 3],
    "q04": [3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    "q05": [3, 3, 3, 3, 3, 3, 3, 3, 3, 3],

    "q06": [3, 3, 3, 3, 2, 1, 2, 1, 2, 2],
    "q07": [1, 1, 0, 3, 2, 2, 3, 0, 2, 0],
    "q08": [1, 2, 3, 1, 3, 3, 3, 2, 3, 2],
    "q09": [2, 3, 3, 3, 1, 1, 0, 1, 2, 2],
    "q10": [3, 3, 3, 2, 1, 2, 1, 3, 2, 3],

    "q11": [2, 2, 2, 3, 3, 3, 3, 3, 3, 1],
    "q12": [2, 2, 3, 3, 3, 2, 2, 2, 1, 3],
    "q13": [3, 3, 3, 3, 2, 3, 3, 3, 2, 2],
    "q14": [3, 3, 3, 3, 2, 2, 0, 3, 3, 2],
    "q15": [2, 1, 3, 1, 1, 1, 2, 0, 2, 2],

    "q16": [3, 3, 2, 3, 2, 3, 3, 2, 1, 1],
    "q17": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "q18": [3, 3, 3, 3, 3, 3, 3, 2, 2, 1],
    "q19": [3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    "q20": [3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
}


def main() -> None:
    records = []

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    updated = 0

    for record in records:
        query_id = record["query_id"]

        if query_id not in APPROVED_LABELS:
            continue

        labels = APPROVED_LABELS[query_id]
        candidates = record["candidates"]

        if len(candidates) != len(labels):
            raise ValueError(
                f"{query_id}: expected "
                f"{len(labels)} candidates, found "
                f"{len(candidates)}"
            )

        for candidate, label in zip(
            candidates,
            labels,
        ):
            candidate["relevance"] = label
            candidate["reviewed"] = True

        updated += 1

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(
        f"Updated {updated} queries "
        f"with approved golden labels."
    )
    print("Queries reviewed: q01-q15")
    print("Products reviewed: 150")
if __name__ == "__main__":
    main()