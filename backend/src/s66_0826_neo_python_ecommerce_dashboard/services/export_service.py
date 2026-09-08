"""Export service for streaming CSV or JSON data dumps."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from s66_0826_neo_python_ecommerce_dashboard.services.analytics_service import (
    get_formal_kpi_report,
    get_overview_analytics,
    get_review_distribution_analytics,
    get_review_trend_analytics,
    get_risk_distribution_analytics,
)
from s66_0826_neo_python_ecommerce_dashboard.services.risk_service import (
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
    """Generate a flattened CSV containing key platform KPI summaries."""
    analytics = export_analytics_summary()
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["section", "metric_name", "value", "unit"])

    overview = analytics["overview"]
    writer.writerow(["overview", "total_sellers", overview["total_sellers"], "count"])
    writer.writerow(["overview", "high_risk_sellers", overview["high_risk_sellers"], "count"])
    writer.writerow(["overview", "high_risk_change_percent", overview["high_risk_change_percent"], "%"])
    writer.writerow(["overview", "average_review_score", overview["average_review_score"], "rating"])
    writer.writerow(["overview", "late_delivery_percentage", overview["late_delivery_percentage"], "%"])
    writer.writerow(["overview", "cancellation_rate", overview["cancellation_rate"], "%"])

    risk = analytics["risk_distribution"]
    writer.writerow(["risk_distribution", "low_risk_sellers", risk["low"], "count"])
    writer.writerow(["risk_distribution", "medium_risk_sellers", risk["medium"], "count"])
    writer.writerow(["risk_distribution", "high_risk_sellers", risk["high"], "count"])

    for kpi in analytics["formal_kpis"]["kpis"]:
        writer.writerow(["platform_kpi", kpi["kpi_name"], kpi["computed_value"], kpi["unit"]])

    return output.getvalue()
