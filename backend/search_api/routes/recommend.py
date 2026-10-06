from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from embedding.bge_m3 import BGEEmbeddingModel
from search.hybrid_search import HybridSearch
from search.lightweight_ranker import LightweightRanker
from search_api.services.parse_schema import ParsedQuery
from search_api.services.parser import QueryParser
from shared.db import SessionLocal
from shared.schemas import SearchResult
from sparse.bm25 import BM25SparseModel
from vector_store.qdrant import QdrantVectorStore


# ============================================================================
# Router
# ============================================================================

router = APIRouter(
    prefix="/v1/recommend",
    tags=["recommendations"],
)


# ============================================================================
# Request / Response Schemas
# ============================================================================

class RecommendationRequest(BaseModel):
    """
    User request for an end-to-end fashion recommendation.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural-language fashion query.",
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of recommendations.",
    )


class RecommendationResponse(BaseModel):
    """
    Complete end-to-end recommendation response.

    Contains:
    - original user query
    - Gemini's structured understanding
    - ranked product recommendations
    """

    query: str
    parsed_query: ParsedQuery
    results: list[SearchResult]


# ============================================================================
# Pipeline Components
# ============================================================================

# NOTE:
# This route currently has its own pipeline instances.
# Reranking is intentionally disabled because the evaluation showed that
# hybrid retrieval without the BGE reranker performed better on the current
# manually reviewed evaluation set.

embedding_model = BGEEmbeddingModel()

sparse_model = BM25SparseModel()

vector_store = QdrantVectorStore()

hybrid_search = HybridSearch(
    embedding_model=embedding_model,
    sparse_model=sparse_model,
    vector_store=vector_store,
    reranker=None,
)

lightweight_ranker = LightweightRanker()

query_parser = QueryParser()


# ============================================================================
# Retrieval Configuration
# ============================================================================

DENSE_TOP_K = 50
SPARSE_TOP_K = 50
FUSION_TOP_K = 50


# ============================================================================
# End-to-End Recommendation Endpoint
# ============================================================================

@router.post(
    "",
    response_model=RecommendationResponse,
)
def recommend(
    request: RecommendationRequest,
) -> RecommendationResponse:
    """
    End-to-end fashion recommendation pipeline.

    Flow:

        User query
            ↓
        Gemini query understanding
            ↓
        Normalized semantic query
            ↓
        BGE-M3 dense retrieval
            +
        BM25 sparse retrieval
            ↓
        RRF hybrid fusion
            ↓
        Lightweight structured ranking
            ↓
        Final product recommendations
    """

    # ------------------------------------------------------------------------
    # 1. Clean and validate the user query
    # ------------------------------------------------------------------------

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query must not be empty.",
        )

    # ------------------------------------------------------------------------
    # 2. Gemini query understanding
    # ------------------------------------------------------------------------

    try:
        parsed_query = query_parser.parse(query)

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Query parsing temporarily unavailable.",
        ) from exc

    # ------------------------------------------------------------------------
    # 3. Build retrieval query
    #
    # Gemini converts multilingual natural language into a concise
    # normalized English semantic query.
    #
    # Example:
    #
    # Tamil:
    #   "கோடைக்கு லேசான வசதியான உடைகள்"
    #
    # normalized_query:
    #   "lightweight comfortable clothes for summer"
    # ------------------------------------------------------------------------

    retrieval_query = (
        parsed_query.normalized_query.strip()
        or query
    )

    # ------------------------------------------------------------------------
    # 4. Hybrid retrieval + lightweight ranking
    # ------------------------------------------------------------------------

    try:
        with SessionLocal() as db:

            results = hybrid_search.search(
                query=retrieval_query,
                db=db,
                dense_top_k=DENSE_TOP_K,
                sparse_top_k=SPARSE_TOP_K,
                fusion_top_k=FUSION_TOP_K,
                final_top_k=request.limit,
            )

            # ---------------------------------------------------------------
            # 5. Structured ranking
            #
            # Uses parsed season/attributes together with lexical signals.
            # ---------------------------------------------------------------

            results = lightweight_ranker.rank(
                query=retrieval_query,
                results=results,
                parsed_query=parsed_query,
            )

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Recommendation retrieval temporarily unavailable.",
        ) from exc

    # ------------------------------------------------------------------------
    # 6. Convert internal search results into API response schema
    # ------------------------------------------------------------------------

    response_results: list[SearchResult] = []

    for result in results[: request.limit]:

        product = result.get("product")

        if product is None:
            continue

        response_results.append(
            SearchResult(
                product=product,
                score=float(result.get("score", 0.0)),
            )
        )

    # ------------------------------------------------------------------------
    # 7. Return complete E2E response
    # ------------------------------------------------------------------------

    return RecommendationResponse(
        query=query,
        parsed_query=parsed_query,
        results=response_results,
    )