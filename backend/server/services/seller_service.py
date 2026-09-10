"""Seller service handling directory searching, filtering, and detailed analytics."""

from __future__ import annotations

from typing import Any
import pandas as pd

from server.database import get_db_connection, safe_read_sql
from server.queries import load_query
from server.services.risk_service import (
    get_all_sellers_df,
    get_cached_seller_data,
    get_seller_history,
)


def get_sellers_directory(
    search: str | None = None,
    category: str | None = None,
    risk_tier: str | None = None,
    risk_driver: str | None = None,
    sort_by: str = "risk_score",
    order: str = "desc",
    page: int = 1,
    limit: int = 20,
) -> dict[str, Any]:
    """Return paginated, sorted, and filtered seller records for the directory."""
    df = get_all_sellers_df().copy()
    _, history_dict, _ = get_cached_seller_data()

    # Filter out sellers with 0 orders for the active directory
    df = df[df["total_orders"] > 0]

    # Search (by seller_id, city, or state)
    if search:
        s = search.strip().lower()
        mask = (
            df["seller_id"].str.lower().str.contains(s, na=False)
            | df["city"].str.lower().str.contains(s, na=False)
            | df["state"].str.lower().str.contains(s, na=False)
        )
        df = df[mask]

    # Category Filter
    if category and category.lower() != "all":
        df = df[df["category"].str.lower() == category.strip().lower()]

    # Risk Tier Filter
    if risk_tier and risk_tier.upper() in ["LOW", "MEDIUM", "HIGH"]:
        df = df[df["risk_tier"] == risk_tier.upper()]

    # Risk Driver Filter
    if risk_driver and risk_driver.lower() != "all":
        df = df[df["primary_risk_driver"].str.lower() == risk_driver.strip().lower()]

    # Sorting
    valid_sort_cols = {
        "risk_score": "risk_score",
        "total_orders": "total_orders",
        "average_rating": "average_rating",
        "late_delivery_percentage": "late_delivery_percentage",
        "total_revenue": "total_revenue",
    }
    sort_col = valid_sort_cols.get(sort_by, "risk_score")
    ascending = order.lower() == "asc"
    df = df.sort_values(by=sort_col, ascending=ascending)

    total_records = len(df)
    total_pages = max(1, (total_records + limit - 1) // limit)
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    page_df = df.iloc[start_idx:end_idx]

    sellers_list = []
    for _, row in page_df.iterrows():
        sid = str(row["seller_id"])
        hist = history_dict.get(sid, [])
        sparkline = [
            {"period": h["period"], "risk_score": h["risk_score"]}
            for h in hist[-5:]
        ]
        sellers_list.append({
            "seller_id": sid,
            "category": str(row["category"]),
            "location": {
                "city": str(row["city"]),
                "state": str(row["state"]),
            },
            "risk_score": float(row["risk_score"]),
            "risk_tier": str(row["risk_tier"]),
            "primary_risk_driver": str(row["primary_risk_driver"]),
            "total_orders": int(row["total_orders"]),
            "is_sparse": bool(row["is_sparse"]),
            "average_rating": float(row["average_rating"]),
            "late_delivery_percentage": float(row["late_delivery_percentage"]),
            "risk_history": sparkline,
        })

    return {
        "total": total_records,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "sellers": sellers_list,
    }


def get_seller_details(seller_id: str) -> dict[str, Any] | None:
    """Return detailed performance and risk analytics for an individual seller."""
    df = get_all_sellers_df()
    match = df[df["seller_id"] == seller_id]
    if match.empty:
        return None

    row = match.iloc[0]
    history = get_seller_history(seller_id)

    # Compute average delivery days for this seller from orders (database agnostic)
    with get_db_connection() as conn:
        deliv_df = safe_read_sql(
            load_query("seller_delivery_times.sql"),
            conn,
            params={"seller_id": seller_id},
        )

    if not deliv_df.empty:
        delivered_dt = pd.to_datetime(deliv_df["order_delivered_customer_date"], errors="coerce")
        purchase_dt = pd.to_datetime(deliv_df["order_purchase_timestamp"], errors="coerce")
        day_diffs = (delivered_dt - purchase_dt).dt.total_seconds() / 86400.0
        valid_diffs = day_diffs.dropna()
        avg_delivery_days = round(float(valid_diffs.mean()), 1) if len(valid_diffs) else 12.0
    else:
        avg_delivery_days = 12.0

    return {
        "seller_id": str(row["seller_id"]),
        "category": str(row["category"]),
        "location": {
            "city": str(row["city"]),
            "state": str(row["state"]),
        },
        "risk_score": float(row["risk_score"]),
        "risk_tier": str(row["risk_tier"]),
        "primary_risk_driver": str(row["primary_risk_driver"]),
        "metrics": {
            "total_orders": int(row["total_orders"]),
            "total_items_sold": int(row["total_items_sold"]),
            "total_revenue": round(float(row["total_revenue"]), 2),
            "average_rating": float(row["average_rating"]),
            "late_delivery_percentage": float(row["late_delivery_percentage"]),
            "cancellation_rate": float(row["cancellation_rate"]),
            "avg_delivery_days": avg_delivery_days,
            "is_sparse": bool(row["is_sparse"]),
        },
        "risk_contributors": {
            "delivery_delay_penalty": float(row["delivery_delay_penalty"]),
            "review_score_penalty": float(row["review_score_penalty"]),
            "cancellation_penalty": float(row["cancellation_penalty"]),
        },
        "monthly_history": [
            {
                "period": h["period"],
                "orders": h["orders"],
                "avg_review": h["avg_review"],
                "late_deliveries": h["late_deliveries"],
                "risk_score": h["risk_score"],
            }
            for h in history
        ],
    }


def get_dynamic_filter_options() -> dict[str, list[str]]:
    """Return available unique categories, risk tiers, and primary risk drivers."""
    df = get_all_sellers_df()
    active = df[df["total_orders"] > 0]

    categories = sorted([c for c in active["category"].dropna().unique() if c and c != "other"])
    risk_tiers = ["LOW", "MEDIUM", "HIGH"]
    risk_drivers = ["Delivery Delays", "Negative Reviews", "Cancellations"]

    return {
        "categories": categories,
        "risk_tiers": risk_tiers,
        "risk_drivers": risk_drivers,
    }
