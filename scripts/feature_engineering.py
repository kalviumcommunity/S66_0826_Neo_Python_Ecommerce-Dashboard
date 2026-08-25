"""Feature Engineering Pipeline for Seller Trust & Safety Analysis.

Generates value-driving features from processed and integrated datasets:
1. Ratio Features: Spend per order, freight ratio, on-time delivery ratio.
2. Binned / Tiered Features: Customer spend tiers, order frequency tiers, seller activity tiers.
3. Composite Scores: Customer RFM (Recency, Frequency, Monetary) score & Seller Trust/Risk score.
"""

from __future__ import annotations

import argparse
import json
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    dataset_dtypes = import_module("scripts.ingest_data").DATASET_DTYPES
except ModuleNotFoundError:
    dataset_dtypes = import_module("ingest_data").DATASET_DTYPES

DATASET_DTYPES = dataset_dtypes

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
INTEGRATED_DATA_DIR = PROCESSED_DATA_DIR / "integrated"
TEMPORAL_DATA_DIR = PROCESSED_DATA_DIR / "temporal"
FEATURE_DATA_DIR = PROCESSED_DATA_DIR / "features"
OUTPUT_DIR = PROJECT_ROOT / "output" / "feature_engineering"


def read_dataset(path: Path, filename: str) -> pd.DataFrame:
    """Read a CSV file with predefined string data type specs if applicable."""
    file_path = path / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Required input dataset not found: {file_path}")
    dtypes = DATASET_DTYPES.get(filename)
    return pd.read_csv(file_path, dtype=dtypes)


def compute_customer_features(
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    recency_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Generate ratio, binned, and composite RFM features for customers."""
    print("Computing customer features...")
    
    # Aggregate payments to order level
    pay_agg = payments_df.groupby("order_id")["payment_value"].sum().reset_index()
    pay_agg.rename(columns={"payment_value": "total_order_payment"}, inplace=True)
    
    # Join orders with payment totals and customers
    merged_orders = orders_df.merge(pay_agg, on="order_id", how="left")
    merged_orders["total_order_payment"] = merged_orders["total_order_payment"].fillna(0.0)
    
    cust_orders = customers_df.merge(merged_orders, on="customer_id", how="left")
    
    # Calculate recency per customer if purchase timestamp is present
    if "order_purchase_timestamp" in cust_orders.columns:
        cust_orders["order_purchase_timestamp"] = pd.to_datetime(
            cust_orders["order_purchase_timestamp"], errors="coerce"
        )
        max_date = cust_orders["order_purchase_timestamp"].max()
        cust_orders["days_since_purchase"] = (max_date - cust_orders["order_purchase_timestamp"]).dt.days
    else:
        cust_orders["days_since_purchase"] = np.nan

    # Group by customer_unique_id
    customer_grp = cust_orders.groupby("customer_unique_id").agg(
        total_orders=("order_id", "nunique"),
        total_spend=("total_order_payment", "sum"),
        min_recency_days=("days_since_purchase", "min"),
        first_purchase_date=("order_purchase_timestamp", "min"),
        latest_purchase_date=("order_purchase_timestamp", "max"),
    ).reset_index()
    
    # Fill recency from temporal customer_recency if available
    if recency_df is not None and "recency_days" in recency_df.columns:
        customer_grp = customer_grp.merge(
            recency_df[["customer_unique_id", "recency_days"]],
            on="customer_unique_id",
            how="left",
        )
        customer_grp["min_recency_days"] = customer_grp["recency_days"].fillna(customer_grp["min_recency_days"])
        customer_grp.drop(columns=["recency_days"], inplace=True)

    customer_grp["min_recency_days"] = customer_grp["min_recency_days"].fillna(
        customer_grp["min_recency_days"].max() if len(customer_grp) and not customer_grp["min_recency_days"].isna().all() else 0
    )

    # 1. Ratio Features
    customer_grp["spend_per_order"] = (
        customer_grp["total_spend"] / customer_grp["total_orders"].replace(0, np.nan)
    ).round(2).fillna(0.0)

    # 2. Binned / Tiered Features
    # Spend Tiers (Quantile-based)
    spend_labels = ["Low", "Medium", "High", "VIP"]
    try:
        customer_grp["spend_tier"] = pd.qcut(
            customer_grp["total_spend"],
            q=4,
            labels=spend_labels,
            duplicates="drop",
        )
    except Exception:
        customer_grp["spend_tier"] = pd.cut(
            customer_grp["total_spend"],
            bins=4,
            labels=spend_labels,
        )

    # Frequency Tiers (Equal-width / Binned)
    freq_bins = [-np.inf, 1, 2, np.inf]
    freq_labels = ["Single Order", "Repeat Customer", "Frequent Customer"]
    customer_grp["frequency_tier"] = pd.cut(
        customer_grp["total_orders"],
        bins=freq_bins,
        labels=freq_labels,
    )

    # 3. Composite RFM Score
    # Recency Score (Inverted: lower recency days = higher score 1..5)
    r_labels = [5, 4, 3, 2, 1]
    try:
        customer_grp["r_score"] = pd.qcut(
            customer_grp["min_recency_days"],
            q=5,
            labels=r_labels,
            duplicates="drop",
        ).astype(int)
    except Exception:
        customer_grp["r_score"] = pd.cut(
            customer_grp["min_recency_days"],
            bins=5,
            labels=r_labels,
        ).fillna(3).astype(int)

    # Frequency Score (Higher frequency = higher score 1..5)
    customer_grp["f_score"] = pd.qcut(
        customer_grp["total_orders"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    # Monetary Score (Higher total spend = higher score 1..5)
    customer_grp["m_score"] = pd.qcut(
        customer_grp["total_spend"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    customer_grp["rfm_composite_score"] = (
        customer_grp["r_score"] + customer_grp["f_score"] + customer_grp["m_score"]
    )

    def assign_rfm_segment(row: pd.Series) -> str:
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        if m >= 4:
            return "High Value"
        if r >= 4 and f <= 2:
            return "New / Recent"
        if r <= 2 and f >= 3:
            return "At-Risk"
        if r <= 2 and f <= 2:
            return "Hibernating"
        return "Promising / Loyal"

    customer_grp["rfm_segment"] = customer_grp.apply(assign_rfm_segment, axis=1)

    summary = {
        "total_customers": int(len(customer_grp)),
        "spend_tier_distribution": customer_grp["spend_tier"].value_counts().to_dict(),
        "rfm_segment_distribution": customer_grp["rfm_segment"].value_counts().to_dict(),
        "avg_spend_per_order": float(customer_grp["spend_per_order"].mean()),
    }

    return customer_grp, summary


def compute_seller_features(
    sellers_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Generate ratio features, activity tiers, and seller trust/risk scores."""
    print("Computing seller features...")

    # Join order items with orders and reviews
    item_orders = order_items_df.merge(
        orders_df[["order_id", "order_status", "order_delivered_customer_date", "order_estimated_delivery_date"]],
        on="order_id",
        how="left",
    )
    
    # Calculate delivery delay in days
    item_orders["order_delivered_customer_date"] = pd.to_datetime(item_orders["order_delivered_customer_date"], errors="coerce")
    item_orders["order_estimated_delivery_date"] = pd.to_datetime(item_orders["order_estimated_delivery_date"], errors="coerce")
    item_orders["delivery_delay_days"] = (
        item_orders["order_delivered_customer_date"] - item_orders["order_estimated_delivery_date"]
    ).dt.days
    item_orders["is_late"] = (item_orders["delivery_delay_days"] > 0).astype(int)

    # Merge with reviews
    review_agg = reviews_df.groupby("order_id")["review_score"].mean().reset_index()
    item_orders = item_orders.merge(review_agg, on="order_id", how="left")

    # Aggregate metrics at seller level
    seller_agg = item_orders.groupby("seller_id").agg(
        total_items_sold=("order_item_id", "count"),
        total_orders=("order_id", "nunique"),
        total_revenue=("price", "sum"),
        total_freight=("freight_value", "sum"),
        late_orders=("is_late", "sum"),
        avg_review_score=("review_score", "mean"),
    ).reset_index()

    # Include sellers with 0 order items if any
    seller_df = sellers_df[["seller_id", "seller_city", "seller_state"]].merge(
        seller_agg, on="seller_id", how="left"
    )
    seller_df["total_items_sold"] = seller_df["total_items_sold"].fillna(0).astype(int)
    seller_df["total_orders"] = seller_df["total_orders"].fillna(0).astype(int)
    seller_df["total_revenue"] = seller_df["total_revenue"].fillna(0.0)
    seller_df["total_freight"] = seller_df["total_freight"].fillna(0.0)
    seller_df["late_orders"] = seller_df["late_orders"].fillna(0).astype(int)
    seller_df["avg_review_score"] = seller_df["avg_review_score"].fillna(
        seller_df["avg_review_score"].mean() if not seller_df["avg_review_score"].isna().all() else 3.0
    ).round(2)

    # 1. Ratio Features
    seller_df["freight_share_ratio"] = (
        seller_df["total_freight"] / (seller_df["total_revenue"] + seller_df["total_freight"]).replace(0, np.nan)
    ).round(4).fillna(0.0)

    seller_df["late_delivery_ratio"] = (
        seller_df["late_orders"] / seller_df["total_orders"].replace(0, np.nan)
    ).round(4).fillna(0.0)

    seller_df["on_time_delivery_ratio"] = (1.0 - seller_df["late_delivery_ratio"]).round(4)

    # 2. Tiered Features
    # Seller Activity Tier
    act_labels = ["Low Volume", "Mid Volume", "High Volume"]
    try:
        seller_df["seller_activity_tier"] = pd.qcut(
            seller_df["total_orders"].rank(method="first"),
            q=3,
            labels=act_labels,
        )
    except Exception:
        seller_df["seller_activity_tier"] = pd.cut(
            seller_df["total_orders"],
            bins=3,
            labels=act_labels,
        )

    # Review Rating Tier
    rating_bins = [0.0, 2.5, 3.5, 4.2, 5.0]
    rating_labels = ["Poor", "Fair", "Good", "Excellent"]
    seller_df["review_rating_tier"] = pd.cut(
        seller_df["avg_review_score"],
        bins=rating_bins,
        labels=rating_labels,
        include_lowest=True,
    )

    # 3. Composite Seller Trust & Risk Score (0 - 100 Scale)
    review_pts = (seller_df["avg_review_score"] / 5.0) * 50.0
    delivery_pts = seller_df["on_time_delivery_ratio"] * 50.0

    seller_df["seller_trust_score"] = (review_pts + delivery_pts).round(2)

    # Risk level classification
    risk_bins = [-np.inf, 60.0, 80.0, np.inf]
    risk_labels = ["High Risk", "Moderate Risk", "Low Risk"]
    seller_df["seller_risk_level"] = pd.cut(
        seller_df["seller_trust_score"],
        bins=risk_bins,
        labels=risk_labels,
    )

    summary = {
        "total_sellers": int(len(seller_df)),
        "risk_level_distribution": seller_df["seller_risk_level"].value_counts().to_dict(),
        "activity_tier_distribution": seller_df["seller_activity_tier"].value_counts().to_dict(),
        "avg_seller_trust_score": float(seller_df["seller_trust_score"].mean()),
        "avg_late_delivery_ratio": float(seller_df["late_delivery_ratio"].mean()),
    }

    return seller_df, summary


def compute_order_features(
    order_items_df: pd.DataFrame,
    payments_df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Compute order & item level ratio features and freight tiers."""
    print("Computing order level features...")
    
    order_features = order_items_df.copy()
    
    # 1. Ratio Features
    order_features["item_freight_ratio"] = (
        order_features["freight_value"] / (order_features["price"] + order_features["freight_value"]).replace(0, np.nan)
    ).round(4).fillna(0.0)

    # 2. Freight Cost Tier (pd.cut)
    freight_bins = [-np.inf, 15.0, 35.0, np.inf]
    freight_labels = ["Low Freight", "Moderate Freight", "High Freight"]
    order_features["freight_cost_tier"] = pd.cut(
        order_features["freight_value"],
        bins=freight_bins,
        labels=freight_labels,
    )

    summary = {
        "total_order_items": int(len(order_features)),
        "freight_tier_distribution": order_features["freight_cost_tier"].value_counts().to_dict(),
        "avg_item_freight_ratio": float(order_features["item_freight_ratio"].mean()),
    }

    return order_features, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Feature Engineering Pipeline for Olist datasets.")
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DATA_DIR)
    parser.add_argument("--integrated-dir", type=Path, default=INTEGRATED_DATA_DIR)
    parser.add_argument("--temporal-dir", type=Path, default=TEMPORAL_DATA_DIR)
    parser.add_argument("--feature-dir", type=Path, default=FEATURE_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    args.feature_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Starting feature engineering pipeline...")

    # Load required input CSVs
    customers_df = read_dataset(args.processed_dir, "olist_customers_dataset.csv")
    orders_df = read_dataset(args.processed_dir, "olist_orders_dataset.csv")
    payments_df = read_dataset(args.processed_dir, "olist_order_payments_dataset.csv")
    order_items_df = read_dataset(args.processed_dir, "olist_order_items_dataset.csv")
    sellers_df = read_dataset(args.processed_dir, "olist_sellers_dataset.csv")
    reviews_df = read_dataset(args.processed_dir, "olist_order_reviews_dataset.csv")

    recency_file = args.temporal_dir / "customer_recency.csv"
    recency_df = pd.read_csv(recency_file) if recency_file.exists() else None

    # 1. Customer Features & Composite RFM
    customer_features, cust_summary = compute_customer_features(
        customers_df, orders_df, payments_df, recency_df
    )
    cust_file = args.feature_dir / "customer_features.csv"
    customer_features.to_csv(cust_file, index=False)
    print(f"✓ Saved customer features to {cust_file}")

    # 2. Seller Features & Composite Trust/Risk Score
    seller_features, seller_summary = compute_seller_features(
        sellers_df, order_items_df, orders_df, reviews_df
    )
    seller_file = args.feature_dir / "seller_features.csv"
    seller_features.to_csv(seller_file, index=False)
    print(f"✓ Saved seller features to {seller_file}")

    # 3. Order Features & Freight Tiers
    order_features, order_summary = compute_order_features(
        order_items_df, payments_df
    )
    order_file = args.feature_dir / "order_features.csv"
    order_features.to_csv(order_file, index=False)
    print(f"✓ Saved order features to {order_file}")

    # 4. Generate Reports & JSON Summaries
    pipeline_summary = {
        "customer_summary": cust_summary,
        "seller_summary": seller_summary,
        "order_summary": order_summary,
    }

    summary_json_file = args.output_dir / "feature_summary.json"
    with open(summary_json_file, "w", encoding="utf-8") as f:
        json.dump(pipeline_summary, f, indent=2)
    print(f"✓ Saved pipeline summary report to {summary_json_file}")

    # RFM Distribution Export
    rfm_dist = customer_features["rfm_segment"].value_counts().reset_index()
    rfm_dist.columns = ["rfm_segment", "customer_count"]
    rfm_dist_file = args.output_dir / "rfm_distribution.csv"
    rfm_dist.to_csv(rfm_dist_file, index=False)
    print(f"✓ Saved RFM distribution to {rfm_dist_file}")

    # Seller Risk Distribution Export
    risk_dist = seller_features["seller_risk_level"].value_counts().reset_index()
    risk_dist.columns = ["seller_risk_level", "seller_count"]
    risk_dist_file = args.output_dir / "seller_risk_distribution.csv"
    risk_dist.to_csv(risk_dist_file, index=False)
    print(f"✓ Saved seller risk distribution to {risk_dist_file}")

    print("\nFeature engineering pipeline completed successfully!")


if __name__ == "__main__":
    main()
