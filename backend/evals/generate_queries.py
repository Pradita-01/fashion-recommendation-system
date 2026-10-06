from __future__ import annotations

import json
from pathlib import Path


QUERIES = [
    # English — semantic
    {
        "query_id": "q01",
        "query": "comfortable beach outfit for summer",
        "language": "en",
        "category": "semantic",
    },
    {
        "query_id": "q02",
        "query": "lightweight summer dress",
        "language": "en",
        "category": "semantic",
    },
    {
        "query_id": "q03",
        "query": "soft comfortable cotton clothes",
        "language": "en",
        "category": "semantic",
    },
    {
        "query_id": "q04",
        "query": "women's casual summer dress",
        "language": "en",
        "category": "semantic",
    },
    {
        "query_id": "q05",
        "query": "cotton beach cover up",
        "language": "en",
        "category": "semantic",
    },
    {
        "query_id": "q06",
        "query": "comfortable summer clothes",
        "language": "en",
        "category": "semantic",
    },
    {
        "query_id": "q07",
        "query": "lightweight clothes for hot weather",
        "language": "en",
        "category": "semantic",
    },
    {
        "query_id": "q08",
        "query": "casual outfit for vacation",
        "language": "en",
        "category": "semantic",
    },
    {
        "query_id": "q09",
        "query": "breathable summer clothing",
        "language": "en",
        "category": "semantic",
    },
    {
        "query_id": "q10",
        "query": "comfortable beach clothing",
        "language": "en",
        "category": "semantic",
    },

    # English — explicit attributes / intent
    {
        "query_id": "q11",
        "query": "women's lightweight cotton dress",
        "language": "en",
        "category": "attribute",
    },
    {
        "query_id": "q12",
        "query": "soft cotton casual outfit",
        "language": "en",
        "category": "attribute",
    },
    {
        "query_id": "q13",
        "query": "summer dress for a beach vacation",
        "language": "en",
        "category": "intent",
    },
    {
        "query_id": "q14",
        "query": "comfortable clothes for walking",
        "language": "en",
        "category": "intent",
    },
    {
        "query_id": "q15",
        "query": "lightweight outfit for hot weather",
        "language": "en",
        "category": "intent",
    },

    # Multilingual
    {
        "query_id": "q16",
        "query": "வெயில்கால கடற்கரை பயணத்திற்கு வசதியான உடைகள்",
        "language": "ta",
        "category": "multilingual",
    },
    {
        "query_id": "q17",
        "query": "கோடைக்காலத்திற்கு இலகுவான வசதியான உடைகள்",
        "language": "ta",
        "category": "multilingual",
    },
    {
        "query_id": "q18",
        "query": "गर्मियों में समुद्र तट की यात्रा के लिए आरामदायक कपड़े",
        "language": "hi",
        "category": "multilingual",
    },

    # Vague / underspecified
    {
        "query_id": "q19",
        "query": "summer clothes",
        "language": "en",
        "category": "vague",
    },
    {
        "query_id": "q20",
        "query": "comfortable clothes",
        "language": "en",
        "category": "vague",
    },
]


def main() -> None:
    output_path = (
        Path(__file__).parent
        / "dataset"
        / "queries.jsonl"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for query in QUERIES:
            file.write(
                json.dumps(
                    query,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(
        f"Wrote {len(QUERIES)} evaluation queries "
        f"to {output_path}"
    )


if __name__ == "__main__":
    main()