"""Seller directory and detailed seller analytics endpoints."""

from __future__ import annotations

from typing import Literal
from fastapi import APIRouter, HTTPException, Query

from s66_0826_neo_python_ecommerce_dashboard.schemas import (
    FilterOptionsResponse,
    SellerDetailResponse,
    SellerListResponse,
)
from s66_0826_neo_python_ecommerce_dashboard.services.seller_service import (
    get_dynamic_filter_options,
    get_seller_details,
    get_sellers_directory,
)

router = APIRouter(prefix="/api/sellers", tags=["Sellers"])


@router.get("", response_model=SellerListResponse)
def list_sellers(
    search: str | None = Query(None, description="Search by seller ID, city, or state"),
    category: str | None = Query(None, description="Filter by product category"),
    risk_tier: Literal["LOW", "MEDIUM", "HIGH"] | None = Query(None, description="Filter by risk tier"),
    risk_driver: Literal["Delivery Delays", "Negative Reviews", "Cancellations"] | None = Query(
        None, description="Filter by primary risk driver"
    ),
    sort: str = Query("risk_score", description="Field to sort by (risk_score, total_orders, average_rating, late_delivery_percentage)"),
    order: Literal["asc", "desc"] = Query("desc", description="Sort direction"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
) -> SellerListResponse:
    """Level 4 Filterable, searchable, and paginated seller directory."""
    result = get_sellers_directory(
        search=search,
        category=category,
        risk_tier=risk_tier,
        risk_driver=risk_driver,
        sort_by=sort,
        order=order,
        page=page,
        limit=limit,
    )
    return SellerListResponse(**result)


@router.get("/filters", response_model=FilterOptionsResponse)
def get_filters() -> FilterOptionsResponse:
    """Dynamic filter dropdown options (categories, risk tiers, and primary risk drivers)."""
    return FilterOptionsResponse(**get_dynamic_filter_options())


@router.get("/{seller_id}", response_model=SellerDetailResponse)
def get_seller(seller_id: str) -> SellerDetailResponse:
    """Level 4 Detailed performance and risk analytics for an individual seller."""
    seller = get_seller_details(seller_id)
    if not seller:
        raise HTTPException(status_code=404, detail=f"Seller with ID '{seller_id}' not found")
    return SellerDetailResponse(**seller)
