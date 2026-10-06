from __future__ import annotations

import sys
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from embedding.bge_m3 import BGEEmbeddingModel
from evals.metrics import mrr_at_k, ndcg_at_k, recall_at_k
from reranking.bge_reranker import BGEReranker
from shared.db import SessionLocal
from search.hybrid_search import HybridSearch
from sparse.bm25 import BM25SparseModel
from vector_store.qdrant import QdrantVectorStore


# ---------------------------------------------------------------------------
# Models / stores
# ---------------------------------------------------------------------------

embedding_model = BGEEmbeddingModel()
sparse_model = BM25SparseModel()
vector_store = QdrantVectorStore()


# ---------------------------------------------------------------------------
# Retrieval configuration
# ---------------------------------------------------------------------------

DENSE_TOP_K = 50
SPARSE_TOP_K = 50
FUSION_TOP_K = 50
RERANK_CANDIDATES = 20
FINAL_TOP_K = 10


# ---------------------------------------------------------------------------
# Golden relevance
# ---------------------------------------------------------------------------

def relevance_lookup(
    query_record: dict[str, Any],
) -> dict[str, int]:
    return {
        str(item["product_id"]): int(item["relevance"])
        for item in query_record["items"]
    }


# ---------------------------------------------------------------------------
# Product ID extraction
# ---------------------------------------------------------------------------

def extract_product_id(
    result: dict[str, Any],
) -> str | None:
    product = result.get("product")

    if product is None:
        return None

    product_id = getattr(product, "id", None)

    if product_id is None:
        return None

    return str(product_id)


def extract_ranked_ids(
    results: list[dict[str, Any]],
) -> list[str]:
    ranked_ids: list[str] = []

    for result in results:
        product_id = extract_product_id(result)

        if product_id is not None:
            ranked_ids.append(product_id)

    return ranked_ids


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def calculate_query_metrics(
    ranked_ids: list[str],
    relevance: dict[str, int],
) -> dict[str, float]:

    ranked_relevance = [
        relevance.get(product_id, 0)
        for product_id in ranked_ids[:FINAL_TOP_K]
    ]

    return {
        "ndcg_at_10": float(
            ndcg_at_k(
                ranked_relevance,
                k=FINAL_TOP_K,
            )
        ),
        "recall_at_10": float(
            recall_at_k(
                ranked_relevance,
                relevance,
                k=FINAL_TOP_K,
            )
        ),
        "mrr": float(
            mrr_at_k(
                ranked_relevance,
                k=FINAL_TOP_K,
            )
        ),
    }


def evaluate_results(
    query_records: list[dict[str, Any]],
    results_by_query: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:

    per_query: list[dict[str, Any]] = []

    for query_record in query_records:

        query_id = str(query_record["query_id"])

        relevance = relevance_lookup(query_record)

        results = results_by_query.get(query_id, [])

        ranked_ids = extract_ranked_ids(results)

        metrics = calculate_query_metrics(
            ranked_ids=ranked_ids,
            relevance=relevance,
        )

        per_query.append(
            {
                "query_id": query_id,
                "query": query_record["query"],
                **metrics,
            }
        )

    if not per_query:
        return {
            "mean": {
                "ndcg_at_10": 0.0,
                "recall_at_10": 0.0,
                "mrr": 0.0,
            },
            "per_query": [],
        }

    return {
        "mean": {
            "ndcg_at_10": mean(
                item["ndcg_at_10"]
                for item in per_query
            ),
            "recall_at_10": mean(
                item["recall_at_10"]
                for item in per_query
            ),
            "mrr": mean(
                item["mrr"]
                for item in per_query
            ),
        },
        "per_query": per_query,
    }


# ---------------------------------------------------------------------------
# Dense-only retrieval
# ---------------------------------------------------------------------------

def run_dense(
    query_records: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:

    results_by_query: dict[str, list[dict[str, Any]]] = {}

    print()
    print("Running DENSE retrieval:")
    print("  BGE-M3 + Qdrant dense")

    with SessionLocal() as db:

        for index, query_record in enumerate(
            query_records,
            start=1,
        ):

            query_id = str(query_record["query_id"])
            query = str(query_record["query"])

            print(
                f"  [{index:02d}/{len(query_records):02d}] "
                f"{query_id}: {query}"
            )

            query_vector = embedding_model.embed(query)

            points = vector_store.search_dense(
                query_vector=query_vector,
                limit=DENSE_TOP_K,
            )

            product_ids = [
                int(point.id)
                for point in points
            ]

            if not product_ids:
                results_by_query[query_id] = []
                continue

            from shared.models import Product

            products = (
                db.query(Product)
                .filter(Product.id.in_(product_ids))
                .all()
            )

            product_by_id = {
                product.id: product
                for product in products
            }

            results: list[dict[str, Any]] = []

            for point in points:

                product = product_by_id.get(
                    int(point.id)
                )

                if product is None:
                    continue

                results.append(
                    {
                        "product": product,
                        "score": float(point.score),
                    }
                )

            results_by_query[query_id] = results

    return results_by_query


# ---------------------------------------------------------------------------
# Sparse-only retrieval
# ---------------------------------------------------------------------------

def run_sparse(
    query_records: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:

    results_by_query: dict[str, list[dict[str, Any]]] = {}

    print()
    print("Running SPARSE retrieval:")
    print("  BM25 + Qdrant sparse")

    with SessionLocal() as db:

        for index, query_record in enumerate(
            query_records,
            start=1,
        ):

            query_id = str(query_record["query_id"])
            query = str(query_record["query"])

            print(
                f"  [{index:02d}/{len(query_records):02d}] "
                f"{query_id}: {query}"
            )

            sparse_indices, sparse_values = sparse_model.embed(query)

            points = vector_store.search_sparse(
                indices=sparse_indices,
                values=sparse_values,
                limit=SPARSE_TOP_K,
            )

            product_ids = [
                int(point.id)
                for point in points
            ]

            if not product_ids:
                results_by_query[query_id] = []
                continue

            from shared.models import Product

            products = (
                db.query(Product)
                .filter(Product.id.in_(product_ids))
                .all()
            )

            product_by_id = {
                product.id: product
                for product in products
            }

            results: list[dict[str, Any]] = []

            for point in points:

                product = product_by_id.get(
                    int(point.id)
                )

                if product is None:
                    continue

                results.append(
                    {
                        "product": product,
                        "score": float(point.score),
                    }
                )

            results_by_query[query_id] = results

    return results_by_query


# ---------------------------------------------------------------------------
# Hybrid retrieval
# ---------------------------------------------------------------------------

def run_hybrid(
    query_records: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:

    results_by_query: dict[str, list[dict[str, Any]]] = {}

    hybrid_search = HybridSearch(
        embedding_model=embedding_model,
        sparse_model=sparse_model,
        vector_store=vector_store,
        reranker=None,
    )

    print()
    print("Running HYBRID retrieval:")
    print("  BGE-M3 dense + BM25 sparse + RRF")

    with SessionLocal() as db:

        for index, query_record in enumerate(
            query_records,
            start=1,
        ):

            query_id = str(query_record["query_id"])
            query = str(query_record["query"])

            print(
                f"  [{index:02d}/{len(query_records):02d}] "
                f"{query_id}: {query}"
            )

            results = hybrid_search.search(
                query=query,
                db=db,
                dense_top_k=DENSE_TOP_K,
                sparse_top_k=SPARSE_TOP_K,
                fusion_top_k=FUSION_TOP_K,
                final_top_k=FINAL_TOP_K,
            )

            results_by_query[query_id] = results

    return results_by_query


# ---------------------------------------------------------------------------
# Hybrid + dedicated reranker
# ---------------------------------------------------------------------------

def run_hybrid_reranked(
    query_records: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:

    results_by_query: dict[str, list[dict[str, Any]]] = {}

    reranker = BGEReranker()

    hybrid_search = HybridSearch(
        embedding_model=embedding_model,
        sparse_model=sparse_model,
        vector_store=vector_store,
        reranker=reranker,
    )

    print()
    print("Running HYBRID + RERANKER:")
    print("  BGE-M3 + BM25 + RRF + BGE reranker")

    with SessionLocal() as db:

        for index, query_record in enumerate(
            query_records,
            start=1,
        ):

            query_id = str(query_record["query_id"])
            query = str(query_record["query"])

            print(
                f"  [{index:02d}/{len(query_records):02d}] "
                f"{query_id}: {query}"
            )

            results = hybrid_search.search(
                query=query,
                db=db,
                dense_top_k=DENSE_TOP_K,
                sparse_top_k=SPARSE_TOP_K,
                fusion_top_k=RERANK_CANDIDATES,
                final_top_k=FINAL_TOP_K,
            )

            results_by_query[query_id] = results

    return results_by_query


# ---------------------------------------------------------------------------
# Run one experiment
# ---------------------------------------------------------------------------

def evaluate_experiment(
    name: str,
    query_records: list[dict[str, Any]],
    results_by_query: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:

    metrics = evaluate_results(
        query_records=query_records,
        results_by_query=results_by_query,
    )

    mean_metrics = metrics["mean"]

    print()
    print(
        f"{name:<24}"
        f"nDCG@10={mean_metrics['ndcg_at_10']:.4f}  "
        f"Recall@10={mean_metrics['recall_at_10']:.4f}  "
        f"MRR={mean_metrics['mrr']:.4f}"
    )

    return metrics


# ---------------------------------------------------------------------------
# Main ablation
# ---------------------------------------------------------------------------

def run_ablation(
    queries: list[dict[str, Any]],
) -> dict[str, Any]:

    dense_results = run_dense(queries)

    dense_metrics = evaluate_experiment(
        "DENSE",
        queries,
        dense_results,
    )

    sparse_results = run_sparse(queries)

    sparse_metrics = evaluate_experiment(
        "SPARSE",
        queries,
        sparse_results,
    )

    hybrid_results = run_hybrid(queries)

    hybrid_metrics = evaluate_experiment(
        "HYBRID",
        queries,
        hybrid_results,
    )

    reranked_results = run_hybrid_reranked(queries)

    reranked_metrics = evaluate_experiment(
        "HYBRID + RERANKER",
        queries,
        reranked_results,
    )

    print()
    print("=" * 78)
    print("RETRIEVAL ABLATION SUMMARY")
    print("=" * 78)
    print()
    print(
        f"{'Experiment':<24}"
        f"{'nDCG@10':>12}"
        f"{'Recall@10':>14}"
        f"{'MRR':>10}"
    )
    print("-" * 78)

    experiments = [
        ("Dense", dense_metrics),
        ("Sparse", sparse_metrics),
        ("Hybrid", hybrid_metrics),
        ("Hybrid + Reranker", reranked_metrics),
    ]

    for name, result in experiments:

        values = result["mean"]

        print(
            f"{name:<24}"
            f"{values['ndcg_at_10']:>12.4f}"
            f"{values['recall_at_10']:>14.4f}"
            f"{values['mrr']:>10.4f}"
        )

    print()

    return {
        "configuration": {
            "dense_top_k": DENSE_TOP_K,
            "sparse_top_k": SPARSE_TOP_K,
            "fusion_top_k": FUSION_TOP_K,
            "rerank_candidates": RERANK_CANDIDATES,
            "final_top_k": FINAL_TOP_K,
        },
        "dense": dense_metrics,
        "sparse": sparse_metrics,
        "hybrid": hybrid_metrics,
        "hybrid_reranker": reranked_metrics,
    }


if __name__ == "__main__":

    from evals.run_eval import load_golden_queries

    golden_queries = load_golden_queries()

    report = run_ablation(
        queries=golden_queries,
    )

    print(report)