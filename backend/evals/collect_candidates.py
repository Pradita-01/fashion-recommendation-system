from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen


API_URL = "http://127.0.0.1:8000/v1/search"

BASE_DIR = Path(__file__).parent
QUERY_FILE = BASE_DIR / "dataset" / "queries.jsonl"
OUTPUT_FILE = BASE_DIR / "dataset" / "candidates.jsonl"


def load_queries() -> list[dict]:
    queries = []

    with QUERY_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            queries.append(
                json.loads(line)
            )

    return queries


def search(query: str) -> dict:
    encoded_query = quote(query)

    url = (
        f"{API_URL}"
        f"?q={encoded_query}"
        f"&page=1"
        f"&page_size=10"
    )

    with urlopen(url, timeout=120) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


def main() -> None:
    queries = load_queries()

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as output:
        for query in queries:
            query_id = query["query_id"]
            text = query["query"]

            print()
            print("=" * 80)
            print(f"{query_id}: {text}")
            print("=" * 80)

            response = search(text)

            results = response.get(
                "results",
                [],
            )

            candidates = []

            for rank, result in enumerate(
                results[:10],
                start=1,
            ):
                product = result.get(
                    "product",
                    {},
                )

                candidate = {
                    "rank": rank,
                    "product_id": product.get(
                        "id"
                    ),
                    "parent_asin": product.get(
                        "parent_asin"
                    ),
                    "title": product.get(
                        "title"
                    ),
                    "category": product.get(
                        "main_category"
                    ),
                    "store": product.get(
                        "store"
                    ),
                    "score": result.get(
                        "score"
                    ),
                    "relevance": None,
                }

                candidates.append(candidate)

                print(
                    f"{rank:2d}. "
                    f"{candidate['title']}"
                )

            record = {
                **query,
                "candidates": candidates,
            }

            output.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print()
    print(
        f"Saved candidates to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()