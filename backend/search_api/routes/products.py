from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.db import get_db
from shared.models import Product
from shared.schemas import ProductListResponse

router = APIRouter(prefix="/v1/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ProductListResponse:
    total = db.scalar(
        select(func.count()).select_from(Product)
    ) or 0

    products = db.scalars(
        select(Product)
        .order_by(Product.id)
        .offset(offset)
        .limit(limit)
    ).all()

    return ProductListResponse(
        items=products,
        total=total,
    )