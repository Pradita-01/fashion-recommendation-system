from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from embedding.bge_m3 import BGEEmbeddingModel
from search.hybrid_search import HybridSearch
from search.lightweight_ranker import LightweightRanker
from search_api.services.parse_schema import ParsedQuery
from search_api.services.parser import QueryParser
from shared.db import get_db
from shared.schemas import SearchResponse, SearchResult
from sparse.bm25 import BM25SparseModel
from vector_store.qdrant import QdrantVectorStore


router = APIRouter(
    prefix="/v1/search",
    tags=["search"],
)


# ---------------------------------------------------------------------------
# Search components
# ---------------------------------------------------------------------------

embedding_model = BGEEmbeddingModel()
sparse_model = BM25SparseModel()
vector_store = QdrantVectorStore()
lightweight_ranker = LightweightRanker()

hybrid_search = HybridSearch(
    embedding_model=embedding_model,
    sparse_model=sparse_model,
    vector_store=vector_store,
    reranker=None,
)


# Gemini query parser.
#
# It is intentionally created once and reused by the FastAPI process.
query_parser = QueryParser()


# ---------------------------------------------------------------------------
# Retrieval configuration
# ---------------------------------------------------------------------------

DENSE_TOP_K = 50
SPARSE_TOP_K = 50
FUSION_TOP_K = 50
MAX_CANDIDATES = 100


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class SearchResponseWithParsedQuery(SearchResponse):
    """
    Existing SearchResponse plus the structured query interpretation.

    This keeps the existing API contract while exposing Gemini's
    understanding to the frontend.
    """

    parsed_query: ParsedQuery


# ---------------------------------------------------------------------------
# Search endpoint
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=SearchResponseWithParsedQuery,
)
def search_products(
    q: str = Query(
        ...,
        min_length=1,
        description="Natural-language fashion search query.",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="1-based result page.",
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=20,
        description="Number of products per page.",
    ),
    db: Session = Depends(get_db),
) -> SearchResponseWithParsedQuery:

    query = q.strip()

    # -----------------------------------------------------------------------
    # Empty query
    # -----------------------------------------------------------------------

    if not query:
        fallback_parsed = ParsedQuery(
            intent="search",
            category=None,
            occasion=None,
            season=None,
            attributes=[],
            language="en",
            normalized_query="",
        )

        return SearchResponseWithParsedQuery(
            query=q,
            parsed_query=fallback_parsed,
            results=[],
            page=page,
            page_size=page_size,
            total=0,
            has_next=False,
        )

    # -----------------------------------------------------------------------
    # Gemini query understanding
    # -----------------------------------------------------------------------
    #
    # IMPORTANT:
    #
    # Gemini is NOT selecting products.
    #
    # Gemini only converts:
    #
    #   Tamil / Hindi / German / French / etc.
    #
    # into a structured query and an English normalized query suitable
    # for the English-heavy Amazon Fashion catalogue.
    #
    # If Gemini is unavailable, we degrade gracefully to the original
    # query so the retrieval system continues working.
    # -----------------------------------------------------------------------

    try:
        parsed_query = query_parser.parse(query)

    except Exception:
        parsed_query = ParsedQuery(
            intent="search",
            category=None,
            occasion=None,
            season=None,
            attributes=[],
            language="unknown",
            normalized_query=query,
        )

    retrieval_query = (
        parsed_query.normalized_query.strip()
        or query
    )

    # -----------------------------------------------------------------------
    # Hybrid retrieval
    # -----------------------------------------------------------------------
    #
    # BGE-M3 -> multilingual semantic retrieval
    # BM25   -> lexical retrieval
    # RRF    -> reciprocal-rank fusion
    #
    # The important multilingual change is that retrieval uses
    # Gemini's normalized English semantic query.
    # -----------------------------------------------------------------------

    results = hybrid_search.search(
        query=retrieval_query,
        db=db,
        dense_top_k=DENSE_TOP_K,
        sparse_top_k=SPARSE_TOP_K,
        fusion_top_k=FUSION_TOP_K,
        final_top_k=MAX_CANDIDATES,
    )

    # -----------------------------------------------------------------------
    # Lightweight lexical/title ranker
    # -----------------------------------------------------------------------

    results = lightweight_ranker.rank(
        query=retrieval_query,
        results=results,
        parsed_query=parsed_query,
    )

    # -----------------------------------------------------------------------
    # Pagination
    # -----------------------------------------------------------------------

    start = (page - 1) * page_size
    end = start + page_size

    page_results = results[start:end]

    has_next = end < len(results)

    # -----------------------------------------------------------------------
    # API response
    # -----------------------------------------------------------------------

    return SearchResponseWithParsedQuery(
        query=query,
        parsed_query=parsed_query,
        results=[
            SearchResult(
                product=result["product"],
                score=float(result["score"]),
            )
            for result in page_results
        ],
        page=page,
        page_size=page_size,
        total=len(results),
        has_next=has_next,
    )
