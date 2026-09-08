"""Seller risk scoring and categorization engine."""

from __future__ import annotations

import sqlite3
import threading
from typing import Any
import pandas as pd

from s66_0826_neo_python_ecommerce_dashboard.config import (
    DB_PATH,
    RISK_THRESHOLD_LOW,
    RISK_THRESHOLD_MEDIUM,
    SPARSE_ORDER_THRESHOLD,
)
from s66_0826_neo_python_ecommerce_dashboard.database import init_db_if_needed, safe_read_sql

_cache_lock = threading.Lock()
_seller_cache: pd.DataFrame | None = None
_seller_history_cache: dict[str, list[dict[str, Any]]] | None = None
_category_risk_cache: list[dict[str, Any]] | None = None


def compute_seller_risk_dataset() -> tuple[pd.DataFrame, dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Compute comprehensive seller metrics, composite risk scores, and category risks directly from SQLite."""
    init_db_if_needed()
    conn = sqlite3.connect(str(DB_PATH))

    # 1. Primary Category per Seller
    seller_cat_query = """
    WITH seller_cat AS (
        SELECT 
            oi.seller_id,
            COALESCE(t.product_category_name_english, p.product_category_name, 'other') AS category,
            COUNT(*) as cat_count,
            ROW_NUMBER() OVER (PARTITION BY oi.seller_id ORDER BY COUNT(*) DESC) as rn
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        LEFT JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
        GROUP BY oi.seller_id, category
    )
    SELECT seller_id, category FROM seller_cat WHERE rn = 1;
    """
    df_cats = safe_read_sql(seller_cat_query, conn)

    # 2. Seller Overall Metrics
    seller_metrics_query = """
    WITH seller_orders AS (
        SELECT 
            oi.seller_id,
            o.order_id,
            o.order_status,
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date,
            o.order_purchase_timestamp,
            CASE WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END AS is_late,
            CASE WHEN o.order_status = 'canceled' THEN 1 ELSE 0 END AS is_canceled
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        GROUP BY oi.seller_id, o.order_id
    ),
    seller_reviews AS (
        SELECT 
            oi.seller_id,
            AVG(r.review_score) AS avg_review
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN order_reviews r ON o.order_id = r.order_id
        GROUP BY oi.seller_id
    ),
    seller_revenue AS (
        SELECT
            oi.seller_id,
            COUNT(oi.order_item_id) AS total_items_sold,
            SUM(oi.price) AS total_revenue
        FROM order_items oi
        GROUP BY oi.seller_id
    ),
    seller_agg AS (
        SELECT 
            so.seller_id,
            COUNT(DISTINCT so.order_id) AS total_orders,
            SUM(CASE WHEN so.order_status = 'delivered' THEN 1 ELSE 0 END) AS delivered_orders,
            SUM(so.is_late) AS late_orders,
            SUM(so.is_canceled) AS canceled_orders
        FROM seller_orders so
        GROUP BY so.seller_id
    )
    SELECT 
        s.seller_id,
        COALESCE(s.seller_city, 'unknown') AS city,
        COALESCE(s.seller_state, 'unknown') AS state,
        COALESCE(sa.total_orders, 0) AS total_orders,
        COALESCE(sa.delivered_orders, 0) AS delivered_orders,
        COALESCE(sa.late_orders, 0) AS late_orders,
        COALESCE(sa.canceled_orders, 0) AS canceled_orders,
        COALESCE(sr.avg_review, 5.0) AS average_rating,
        COALESCE(srev.total_items_sold, 0) AS total_items_sold,
        COALESCE(srev.total_revenue, 0.0) AS total_revenue
    FROM sellers s
    LEFT JOIN seller_agg sa ON s.seller_id = sa.seller_id
    LEFT JOIN seller_reviews sr ON s.seller_id = sr.seller_id
    LEFT JOIN seller_revenue srev ON s.seller_id = srev.seller_id;
    """
    df = safe_read_sql(seller_metrics_query, conn)
    df = df.merge(df_cats, on="seller_id", how="left")
    df["category"] = df["category"].fillna("other")

    # Rates & Penalties
    df["late_delivery_percentage"] = (
        (df["late_orders"] / df["delivered_orders"].replace(0, 1)) * 100.0
    ).round(2)
    # If seller had 0 delivered orders, late_delivery_percentage is 0.0
    df.loc[df["delivered_orders"] == 0, "late_delivery_percentage"] = 0.0

    df["cancellation_rate"] = (
        (df["canceled_orders"] / df["total_orders"].replace(0, 1)) * 100.0
    ).round(2)
    df.loc[df["total_orders"] == 0, "cancellation_rate"] = 0.0

    df["average_rating"] = df["average_rating"].round(2)

    # Risk penalties (0 to 100 scale)
    df["delivery_delay_penalty"] = (df["late_delivery_percentage"] * 2.0).clip(upper=100.0).round(2)
    df["review_score_penalty"] = ((5.0 - df["average_rating"]) * 25.0).clip(lower=0.0, upper=100.0).round(2)
    df["cancellation_penalty"] = (df["cancellation_rate"] * 10.0).clip(upper=100.0).round(2)

    # Composite Risk Score (adheres to DASHBOARD_THINKING.md weights)
    df["risk_score"] = (
        0.45 * df["delivery_delay_penalty"]
        + 0.35 * df["review_score_penalty"]
        + 0.20 * df["cancellation_penalty"]
    ).round(1)

    # Risk Tiers: Low (< 30), Medium (30 - 70), High (> 70)
    df["risk_tier"] = "LOW"
    df.loc[df["risk_score"] >= RISK_THRESHOLD_LOW, "risk_tier"] = "MEDIUM"
    df.loc[df["risk_score"] > RISK_THRESHOLD_MEDIUM, "risk_tier"] = "HIGH"

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
    df["is_sparse"] = df["total_orders"] < SPARSE_ORDER_THRESHOLD

    # 3. Monthly Risk History per Seller
    monthly_history_query = """
    WITH seller_monthly_orders AS (
        SELECT 
            oi.seller_id,
            strftime('%Y-%m', o.order_purchase_timestamp) AS period,
            o.order_id,
            o.order_status,
            CASE WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END AS is_late,
            CASE WHEN o.order_status = 'canceled' THEN 1 ELSE 0 END AS is_canceled
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_purchase_timestamp IS NOT NULL
        GROUP BY oi.seller_id, o.order_id
    ),
    seller_monthly_reviews AS (
        SELECT 
            oi.seller_id,
            strftime('%Y-%m', o.order_purchase_timestamp) AS period,
            AVG(r.review_score) AS avg_review
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN order_reviews r ON o.order_id = r.order_id
        WHERE o.order_purchase_timestamp IS NOT NULL
        GROUP BY oi.seller_id, strftime('%Y-%m', o.order_purchase_timestamp)
    ),
    monthly_agg AS (
        SELECT 
            smo.seller_id,
            smo.period,
            COUNT(DISTINCT smo.order_id) AS orders,
            SUM(CASE WHEN smo.order_status = 'delivered' THEN 1 ELSE 0 END) AS delivered_orders,
            SUM(smo.is_late) AS late_deliveries,
            SUM(smo.is_canceled) AS canceled_orders
        FROM seller_monthly_orders smo
        GROUP BY smo.seller_id, smo.period
    )
    SELECT 
        ma.seller_id,
        ma.period,
        ma.orders,
        ma.delivered_orders,
        ma.late_deliveries,
        ma.canceled_orders,
        COALESCE(smr.avg_review, 5.0) AS avg_review
    FROM monthly_agg ma
    LEFT JOIN seller_monthly_reviews smr ON ma.seller_id = smr.seller_id AND ma.period = smr.period
    ORDER BY ma.period ASC;
    """
    df_history = safe_read_sql(monthly_history_query, conn)
    conn.close()

    df_history["late_pct"] = (
        (df_history["late_deliveries"] / df_history["delivered_orders"].replace(0, 1)) * 100.0
    ).fillna(0.0)
    df_history["cancel_pct"] = (
        (df_history["canceled_orders"] / df_history["orders"].replace(0, 1)) * 100.0
    ).fillna(0.0)
    df_history["d_pen"] = (df_history["late_pct"] * 2.0).clip(upper=100.0)
    df_history["r_pen"] = ((5.0 - df_history["avg_review"]) * 25.0).clip(lower=0.0, upper=100.0)
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
                "avg_review": round(float(row["avg_review"]), 2),
                "late_deliveries": int(row["late_deliveries"]),
                "risk_score": float(row["risk_score"]),
            }
            for _, row in group.iterrows()
        ]

    # 4. Top Categories by Risk
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
