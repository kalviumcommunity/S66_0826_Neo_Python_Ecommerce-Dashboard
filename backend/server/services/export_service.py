"""Export service for streaming CSV or JSON data dumps."""

from __future__ import annotations

import csv
import io
from typing import Any

from server.services.analytics_service import (
    get_formal_kpi_report,
    get_overview_analytics,
    get_review_distribution_analytics,
    get_review_trend_analytics,
    get_risk_distribution_analytics,
)
from server.services.risk_service import (
    get_all_sellers_df,
    get_category_risk_data,
)


def export_sellers_csv() -> str:
    """Generate a CSV string containing all seller records."""
    df = get_all_sellers_df()
    active = df[df["total_orders"] > 0]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "seller_id",
        "category",
        "city",
        "state",
        "risk_score",
        "risk_tier",
        "primary_risk_driver",
        "total_orders",
        "total_items_sold",
        "total_revenue",
        "average_rating",
        "late_delivery_percentage",
        "cancellation_rate",
        "is_sparse",
    ])

    for _, r in active.iterrows():
        writer.writerow([
            r["seller_id"],
            r["category"],
            r["city"],
            r["state"],
            r["risk_score"],
            r["risk_tier"],
            r["primary_risk_driver"],
            r["total_orders"],
            r["total_items_sold"],
            r["total_revenue"],
            r["average_rating"],
            r["late_delivery_percentage"],
            r["cancellation_rate"],
            r["is_sparse"],
        ])

    return output.getvalue()


def export_sellers_json() -> list[dict[str, Any]]:
    """Generate a list of dicts containing all seller records for JSON export."""
    df = get_all_sellers_df()
    active = df[df["total_orders"] > 0]

    return [
        {
            "seller_id": r["seller_id"],
            "category": r["category"],
            "location": {"city": r["city"], "state": r["state"]},
            "risk_score": float(r["risk_score"]),
            "risk_tier": r["risk_tier"],
            "primary_risk_driver": r["primary_risk_driver"],
            "total_orders": int(r["total_orders"]),
            "total_items_sold": int(r["total_items_sold"]),
            "total_revenue": float(r["total_revenue"]),
            "average_rating": float(r["average_rating"]),
            "late_delivery_percentage": float(r["late_delivery_percentage"]),
            "cancellation_rate": float(r["cancellation_rate"]),
            "is_sparse": bool(r["is_sparse"]),
        }
        for _, r in active.iterrows()
    ]


def export_analytics_summary() -> dict[str, Any]:
    """Generate a consolidated analytics payload for JSON export."""
    return {
        "overview": get_overview_analytics(),
        "review_trend": get_review_trend_analytics(),
        "risk_distribution": get_risk_distribution_analytics(),
        "review_distribution": get_review_distribution_analytics(),
        "category_risk": get_category_risk_data(),
        "formal_kpis": get_formal_kpi_report(),
    }


def export_analytics_csv() -> str:
    """Generate a summary metrics CSV report."""
    overview = get_overview_analytics()
    kpis = get_formal_kpi_report()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["section", "metric_name", "value", "target", "status"])

    # Overview metrics
    writer.writerow(["Overview", "Total Sellers", overview["total_sellers"], "N/A", "N/A"])
    writer.writerow(["Overview", "High-Risk Sellers", overview["high_risk_sellers"], "N/A", "N/A"])
    writer.writerow(["Overview", "Average Review Score", overview["average_review_score"], ">= 4.0", overview["badges"]["review_score_status"]])
    writer.writerow(["Overview", "Late Delivery %", overview["late_delivery_percentage"], "<= 10.0%", overview["badges"]["late_delivery_status"]])
    writer.writerow(["Overview", "Cancellation Rate %", overview["cancellation_rate"], "<= 1.5%", overview["badges"]["cancellation_status"]])

    # Formal KPIs
    for kpi in kpis.get("kpis", []):
        writer.writerow([
            "PRD_KPI",
            kpi["kpi_name"],
            kpi["computed_value"],
            f"{kpi.get('target_min', '')} - {kpi.get('target_max', '')} {kpi.get('unit', '')}",
            kpi.get("status", "PASS"),
        ])

    return output.getvalue()
