"""Analytics endpoints for macro KPIs, risk distributions, trends, and formal PRD metrics."""

from __future__ import annotations

from fastapi import APIRouter

from server.schemas import (
    CategoryRiskResponse,
    KPIReportResponse,
    OverviewResponse,
    ReviewDistributionResponse,
    ReviewTrendResponse,
    RiskDistributionResponse,
)
from server.services.analytics_service import (
    get_formal_kpi_report,
    get_overview_analytics,
    get_review_distribution_analytics,
    get_review_trend_analytics,
    get_risk_distribution_analytics,
)
from server.services.risk_service import get_category_risk_data

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", response_model=OverviewResponse)
def get_overview() -> OverviewResponse:
    """Level 1 Executive Overview KPIs, targets, and status context badges."""
    return OverviewResponse(**get_overview_analytics())


@router.get("/review-trend", response_model=ReviewTrendResponse)
def get_review_trend() -> ReviewTrendResponse:
    """Level 2 Longitudinal average review score trend with target benchmark line."""
    return ReviewTrendResponse(**get_review_trend_analytics())


@router.get("/risk-distribution", response_model=RiskDistributionResponse)
def get_risk_distribution() -> RiskDistributionResponse:
    """Level 3 Distribution of sellers across Low, Medium, and High risk tiers."""
    return RiskDistributionResponse(**get_risk_distribution_analytics())


@router.get("/review-distribution", response_model=ReviewDistributionResponse)
def get_review_distribution() -> ReviewDistributionResponse:
    """Level 3 Breakdown of review score ratings from 1 to 5 stars and positive review percentage."""
    return ReviewDistributionResponse(**get_review_distribution_analytics())


@router.get("/category-risk", response_model=CategoryRiskResponse)
def get_category_risk() -> CategoryRiskResponse:
    """Level 3 Product categories ranked by composite risk score."""
    return CategoryRiskResponse(categories=get_category_risk_data())


@router.get("/kpis", response_model=KPIReportResponse)
def get_formal_kpis() -> KPIReportResponse:
    """Formal business KPIs validated against target boundaries defined in the PRD."""
    return KPIReportResponse(**get_formal_kpi_report())
