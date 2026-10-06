import json
from pathlib import Path

lines = Path("backend/evals/dataset/golden_review.jsonl").read_text(
    encoding="utf-8"
).splitlines()

record = next(
    json.loads(line)
    for line in lines
    if json.loads(line)["query_id"] == "q17"
)

print("QUERY:")
print(record["query"])
print()

print("GOLDEN CANDIDATES:")
for x in record["candidates"]:
    print(
        f"{x['rank']:>2}. "
        f"id={x['product_id']} "
        f"relevance={x['relevance']} "
        f"title={x['title'][:120]}"
    )
