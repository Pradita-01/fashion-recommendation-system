from fastapi import APIRouter, HTTPException, Query

from search_api.services.parser import QueryParser

router = APIRouter(prefix="/v1/parse", tags=["parse"])

parser = QueryParser()


@router.get("")
def parse_query(
    q: str = Query(..., min_length=1, description="Natural-language fashion query."),
):
    try:
        return parser.parse(q.strip())
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Query parsing temporarily unavailable: {exc}",
        ) from exc
