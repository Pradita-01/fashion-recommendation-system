from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db import Base


class CatalogVersion(Base):
    __tablename__ = "catalog_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    products: Mapped[list["Product"]] = relationship(
        back_populates="catalog_version"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Amazon's authoritative product identifier.
    parent_asin: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Source catalogue attributes.
    main_category: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    store: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    average_rating: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
    )

    rating_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Keep richer source attributes without prematurely normalizing them.
    features: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    categories: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # First representative image for the Day 1 catalogue UI.
    image_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    catalog_version_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_versions.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    catalog_version: Mapped[CatalogVersion] = relationship(
        back_populates="products"
    )