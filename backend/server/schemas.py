"""Pydantic schemas and response models for API endpoints."""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Endpoint Group 1 — Overview Dashboard
# ---------------------------------------------------------------------------
class TargetsOverview(BaseModel):
    average_review_score: float = 4.0
    late_delivery_percentage: float = 10.0
    cancellation_rate: float = 1.5


class BadgesOverview(BaseModel):
    review_score_status: str = "On Target"
    late_delivery_status: str = "Within Limits"
    cancellation_status: str = "On Target"


class OverviewResponse(BaseModel):
    total_sellers: int = Field(..., description="Total active sellers")
    high_risk_sellers: int = Field(..., description="Count of high-risk sellers")
    high_risk_change_percent: float = Field(..., description="MoM percentage change in high-risk sellers")
    average_review_score: float = Field(..., description="Mean review score across all orders")
    late_delivery_percentage: float = Field(..., description="Proportion of delivered orders that were late")
    cancellation_rate: float = Field(..., description="Proportion of orders that were canceled")
    targets: TargetsOverview | None = None
    badges: BadgesOverview | None = None


# ---------------------------------------------------------------------------
# Endpoint Group 2 — Average Review Score Trend
# ---------------------------------------------------------------------------
class ReviewTrendPoint(BaseModel):
    period: str = Field(..., description="Time period in YYYY-MM format")
    average_review_score: float = Field(..., description="Average review score for the period")
    total_reviews: int | None = None


class ReviewTrendResponse(BaseModel):
    target_score: float = Field(default=4.0, description="Target review score reference value")
    trend: list[ReviewTrendPoint] = Field(..., description="Historical time-series of review scores")


# ---------------------------------------------------------------------------
# Endpoint Group 3 — Sellers Per Risk Tier
# ---------------------------------------------------------------------------
class RiskDistributionResponse(BaseModel):
    low: int = Field(..., description="Low-risk seller count (< 30 risk score)")
    medium: int = Field(..., description="Medium-risk seller count (30-70 risk score)")
    high: int = Field(..., description="High-risk seller count (> 70 risk score)")
    total: int = Field(..., description="Total seller count")


# ---------------------------------------------------------------------------
# Endpoint Group 4 — Review Score Distribution
# ---------------------------------------------------------------------------
class StarDistribution(BaseModel):
    one_star: int = Field(..., alias="1_star")
    two_star: int = Field(..., alias="2_star")
    three_star: int = Field(..., alias="3_star")
    four_star: int = Field(..., alias="4_star")
    five_star: int = Field(..., alias="5_star")

    model_config = {"populate_by_name": True}


class ReviewDistributionResponse(BaseModel):
    distribution: StarDistribution
    positive_review_percentage: float = Field(..., description="Percentage of reviews >= 4 stars")


# ---------------------------------------------------------------------------
# Endpoint Group 5 — Top Categories by Risk
# ---------------------------------------------------------------------------
class CategoryRiskItem(BaseModel):
    category: str = Field(..., description="Category name")
    risk_score: float = Field(..., description="Category risk score (0-100)")
    total_orders: int | None = None


class CategoryRiskResponse(BaseModel):
    categories: list[CategoryRiskItem]


# ---------------------------------------------------------------------------
# Endpoint Group 6 — Seller Directory
# ---------------------------------------------------------------------------
class Location(BaseModel):
    city: str
    state: str


class RiskHistoryPoint(BaseModel):
    period: str
    risk_score: float


class SellerRecord(BaseModel):
    seller_id: str
    category: str
    location: Location
    risk_score: float
    risk_tier: Literal["LOW", "MEDIUM", "HIGH"]
    primary_risk_driver: str
    total_orders: int
    is_sparse: bool
    average_rating: float
    late_delivery_percentage: float
    risk_history: list[RiskHistoryPoint] = []


class SellerListResponse(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    sellers: list[SellerRecord]


# ---------------------------------------------------------------------------
# Endpoint Group 7 — Seller Details
# ---------------------------------------------------------------------------
class SellerMetrics(BaseModel):
    total_orders: int
    total_items_sold: int
    total_revenue: float
    average_rating: float
    late_delivery_percentage: float
    cancellation_rate: float
    avg_delivery_days: float
    is_sparse: bool


class RiskContributors(BaseModel):
    delivery_delay_penalty: float
    review_score_penalty: float
    cancellation_penalty: float


class MonthlyHistoryPoint(BaseModel):
    period: str
    orders: int
    avg_review: float
    late_deliveries: int
    risk_score: float


class SellerDetailResponse(BaseModel):
    seller_id: str
    category: str
    location: Location
    risk_score: float
    risk_tier: Literal["LOW", "MEDIUM", "HIGH"]
    primary_risk_driver: str
    metrics: SellerMetrics
    risk_contributors: RiskContributors
    monthly_history: list[MonthlyHistoryPoint]


# ---------------------------------------------------------------------------
# Endpoint Group 8 — Filter Options
# ---------------------------------------------------------------------------
class FilterOptionsResponse(BaseModel):
    categories: list[str]
    risk_tiers: list[str]
    risk_drivers: list[str]


# ---------------------------------------------------------------------------
# Formal Business KPIs
# ---------------------------------------------------------------------------
class KPIDetail(BaseModel):
    kpi_name: str
    description: str
    formula: str
    owner: str
    unit: str
    target_min: float | None = None
    target_max: float | None = None
    computed_value: float
    within_target: bool
    status: str
    deviation_notes: list[str] = []


class KPIReportResponse(BaseModel):
    total_kpis: int
    passing: int
    failing: int
    kpis: list[KPIDetail]
