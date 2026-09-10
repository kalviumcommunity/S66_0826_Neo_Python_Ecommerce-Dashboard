"""Seller risk scoring and categorization engine with Bayesian smoothing."""

from __future__ import annotations

import threading
from typing import Any
import pandas as pd

from server.config import (
    PRIOR_DELIVERY_WEIGHT,
    PRIOR_LATE_RATE,
    PRIOR_REVIEW_SCORE,
    PRIOR_REVIEW_WEIGHT,
    RISK_THRESHOLD_LOW,
    RISK_THRESHOLD_MEDIUM,
    SPARSE_ORDER_THRESHOLD,
)
from server.database import get_db_connection, safe_read_sql
from server.queries import load_query

_cache_lock = threading.Lock()
_seller_cache: pd.DataFrame | None = None
_seller_history_cache: dict[str, list[dict[str, Any]]] | None = None
_category_risk_cache: list[dict[str, Any]] | None = None


def compute_seller_risk_dataset() -> tuple[pd.DataFrame, dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Compute comprehensive seller metrics, Bayesian-smoothed risk scores, and category risks from the database."""
    with get_db_connection() as conn:
        # 1. Primary Category per Seller
        df_cats = safe_read_sql(load_query("seller_primary_category.sql"), conn)

        # 2. Seller Overall Metrics
        df = safe_read_sql(load_query("seller_risk_metrics.sql"), conn)
        df = df.merge(df_cats, on="seller_id", how="left")
        df["category"] = df["category"].fillna("other")

        # 3. Monthly Risk History per Seller
        df_history = safe_read_sql(load_query("seller_monthly_history.sql"), conn)

    # 4. Bayesian Smoothing & Penalty Calculations
    # Raw late delivery rate
    df["late_delivery_percentage"] = (
        (df["late_orders"] / df["delivered_orders"].replace(0, 1)) * 100.0
    ).round(2)
    df.loc[df["delivered_orders"] == 0, "late_delivery_percentage"] = 0.0

    # Empirical Bayes Smoothed Late Delivery Rate (prevents small-seller 1-order spike)
    df["smoothed_late_pct"] = (
        (df["late_orders"] + (PRIOR_DELIVERY_WEIGHT * PRIOR_LATE_RATE))
        / (df["delivered_orders"] + PRIOR_DELIVERY_WEIGHT)
        * 100.0
    ).round(2)

    # Cancellation rate
    df["cancellation_rate"] = (
        (df["canceled_orders"] / df["total_orders"].replace(0, 1)) * 100.0
    ).round(2)
    df.loc[df["total_orders"] == 0, "cancellation_rate"] = 0.0

    # Bayesian Smoothed Review Rating (IMDb formula pulling small sample sizes toward 4.09 platform mean)
    df["average_rating"] = (
        (df["review_count"] * df["raw_avg_review"] + PRIOR_REVIEW_WEIGHT * PRIOR_REVIEW_SCORE)
        / (df["review_count"] + PRIOR_REVIEW_WEIGHT)
    ).round(2)

    # Component Penalties (0 to 100 scale)
    df["delivery_delay_penalty"] = (df["smoothed_late_pct"] * 2.0).clip(upper=100.0).round(2)
    df["review_score_penalty"] = ((5.0 - df["average_rating"]) * 25.0).clip(lower=0.0, upper=100.0).round(2)
    df["cancellation_penalty"] = (df["cancellation_rate"] * 10.0).clip(upper=100.0).round(2)

    # Composite Risk Score
    df["risk_score"] = (
        0.45 * df["delivery_delay_penalty"]
        + 0.35 * df["review_score_penalty"]
        + 0.20 * df["cancellation_penalty"]
    ).round(1)

    df["is_sparse"] = df["total_orders"] < SPARSE_ORDER_THRESHOLD

    # Risk Tiers: Low (< 30), Medium (30 - 70), High (> 70)
    df["risk_tier"] = "LOW"
    df.loc[df["risk_score"] >= RISK_THRESHOLD_LOW, "risk_tier"] = "MEDIUM"
    df.loc[df["risk_score"] > RISK_THRESHOLD_MEDIUM, "risk_tier"] = "HIGH"

    # Small seller safeguard: do not label sparse sellers (< 5 orders) as HIGH risk unless extreme cancellation
    df.loc[df["is_sparse"] & (df["risk_tier"] == "HIGH") & (df["cancellation_rate"] < 50.0), "risk_tier"] = "MEDIUM"

    # Primary Risk Driver
    def determine_driver(row: pd.Series) -> str:
        d = row["delivery_delay_penalty"]
        r = row["review_score_penalty"]
        c = row["cancellation_penalty"]
        if d == 0 and r == 0 and c == 0:
            return "Delivery Delays"
        if d >= r and d >= c:
            return "Delivery Delays"
        if r >= d and r >= c:
            return "Negative Reviews"
        return "Cancellations"

    df["primary_risk_driver"] = df.apply(determine_driver, axis=1)

    # 5. Process Monthly History with Smoothing
    df_history["smoothed_late"] = (
        (df_history["late_deliveries"] + (PRIOR_DELIVERY_WEIGHT * PRIOR_LATE_RATE))
        / (df_history["delivered_orders"] + PRIOR_DELIVERY_WEIGHT)
        * 100.0
    ).round(2)
    df_history["smoothed_rev"] = (
        (df_history["review_count"] * df_history["avg_review"] + PRIOR_REVIEW_WEIGHT * PRIOR_REVIEW_SCORE)
        / (df_history["review_count"] + PRIOR_REVIEW_WEIGHT)
    ).round(2)
    df_history["cancel_pct"] = (
        (df_history["canceled_orders"] / df_history["orders"].replace(0, 1)) * 100.0
    ).fillna(0.0)

    df_history["d_pen"] = (df_history["smoothed_late"] * 2.0).clip(upper=100.0)
    df_history["r_pen"] = ((5.0 - df_history["smoothed_rev"]) * 25.0).clip(lower=0.0, upper=100.0)
    df_history["c_pen"] = (df_history["cancel_pct"] * 10.0).clip(upper=100.0)
    df_history["risk_score"] = (
        0.45 * df_history["d_pen"] + 0.35 * df_history["r_pen"] + 0.20 * df_history["c_pen"]
    ).round(1)

    history_dict: dict[str, list[dict[str, Any]]] = {}
    for seller_id, group in df_history.groupby("seller_id"):
        history_dict[str(seller_id)] = [
            {
                "period": row["period"],
                "orders": int(row["orders"]),
                "avg_review": round(float(row["smoothed_rev"]), 2),
                "late_deliveries": int(row["late_deliveries"]),
                "risk_score": float(row["risk_score"]),
            }
            for _, row in group.iterrows()
        ]

    # 6. Top Categories by Risk
    category_summary = (
        df.groupby("category")
        .agg(
            total_sellers=("seller_id", "count"),
            total_orders=("total_orders", "sum"),
            avg_risk=("risk_score", "mean"),
        )
        .reset_index()
    )
    category_summary["avg_risk"] = category_summary["avg_risk"].round(1)
    category_summary = category_summary.sort_values("avg_risk", ascending=False)
    category_risk_list = [
        {
            "category": row["category"],
            "risk_score": float(row["avg_risk"]),
            "total_orders": int(row["total_orders"]),
        }
        for _, row in category_summary.iterrows()
        if row["category"] != "other"
    ]

    return df, history_dict, category_risk_list


def get_cached_seller_data() -> tuple[pd.DataFrame, dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Retrieve or compute the cached seller analytics dataset."""
    global _seller_cache, _seller_history_cache, _category_risk_cache
    if _seller_cache is None or _seller_history_cache is None or _category_risk_cache is None:
        with _cache_lock:
            if _seller_cache is None or _seller_history_cache is None or _category_risk_cache is None:
                _seller_cache, _seller_history_cache, _category_risk_cache = compute_seller_risk_dataset()
    return _seller_cache, _seller_history_cache, _category_risk_cache


def get_all_sellers_df() -> pd.DataFrame:
    """Return the precalculated DataFrame of all sellers."""
    df, _, _ = get_cached_seller_data()
    return df


def get_seller_history(seller_id: str) -> list[dict[str, Any]]:
    """Return the monthly risk and order history for a specific seller."""
    _, history_dict, _ = get_cached_seller_data()
    return history_dict.get(seller_id, [])


def get_category_risk_data() -> list[dict[str, Any]]:
    """Return product categories ranked by composite risk score."""
    _, _, category_risk = get_cached_seller_data()
    return category_risk
