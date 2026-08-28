"""Analyze relationships between aggregated Olist business metrics.

The workflow creates separate order-level and customer-level analytical tables
before calculating correlations. One-to-many item, payment, and review tables
are aggregated first so repeated child rows cannot overweight an order.
Correlation is reported as an investigative relationship, not as causation.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

try:
    dataset_dtypes = import_module("scripts.ingest_data").DATASET_DTYPES
except ModuleNotFoundError:  # Supports direct execution from scripts/
    dataset_dtypes = import_module("ingest_data").DATASET_DTYPES

DATASET_DTYPES = dataset_dtypes

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
ANALYSIS_DATA_DIR = PROCESSED_DATA_DIR / "analysis"
CORRELATION_OUTPUT_DIR = PROJECT_ROOT / "output" / "correlation"
FIGURE_DIR = CORRELATION_OUTPUT_DIR / "figures"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
STRONG_THRESHOLD = 0.70
REDUNDANT_THRESHOLD = 0.80


def _read_processed(filename: str) -> pd.DataFrame:
    path = PROCESSED_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required processed file not found: {path}")
    return pd.read_csv(path, dtype=DATASET_DTYPES.get(filename))


def _parse_column(df: pd.DataFrame, column: str, date_format: str) -> pd.DataFrame:
    """Parse a required date column explicitly and reject invalid non-empty values."""
    if column not in df.columns:
        raise KeyError(f"Required date column not found: {column}")
    original = df[column]
    parsed = pd.to_datetime(original, format=date_format, errors="coerce")
    invalid = original.notna() & parsed.isna()
    if invalid.any():
        raise ValueError(
            f"{column} has {int(invalid.sum())} invalid values for {date_format}"
        )
    result = df.copy()
    result[column] = parsed
    return result


def build_order_features() -> pd.DataFrame:
    """Build one row per order from the processed Olist tables."""
    orders = _read_processed("olist_orders_dataset.csv")
    for column in (
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
    ):
        orders = _parse_column(orders, column, TIMESTAMP_FORMAT)
    orders = _parse_column(orders, "order_estimated_delivery_date", DATE_FORMAT)

    items = _read_processed("olist_order_items_dataset.csv")
    item_metrics = (
        items.groupby("order_id", as_index=False)
        .agg(
            order_item_count=("order_item_id", "count"),
            total_freight_value=("freight_value", "sum"),
            total_item_price=("price", "sum"),
            average_item_price=("price", "mean"),
        )
    )
    payments = _read_processed("olist_order_payments_dataset.csv")
    payment_metrics = (
        payments.groupby("order_id", as_index=False)
        .agg(
            order_revenue=("payment_value", "sum"),
            payment_record_count=("payment_sequential", "count"),
        )
    )
    reviews = _read_processed("olist_order_reviews_dataset.csv")
    review_metrics = (
        reviews.groupby("order_id", as_index=False)
        .agg(review_score=("review_score", "mean"), review_count=("review_id", "count"))
    )

    result = orders.merge(item_metrics, on="order_id", how="left", validate="one_to_one")
    result = result.merge(payment_metrics, on="order_id", how="left", validate="one_to_one")
    result = result.merge(review_metrics, on="order_id", how="left", validate="one_to_one")

    seconds_per_day = 86400
    seconds_per_hour = 3600
    result["delivery_days"] = (
        result["order_delivered_customer_date"]
        - result["order_purchase_timestamp"]
    ).dt.total_seconds() / seconds_per_day
    result["delivery_delay_days"] = (
        result["order_delivered_customer_date"]
        - result["order_estimated_delivery_date"]
    ).dt.total_seconds() / seconds_per_day
    result["approval_delay_hours"] = (
        result["order_approved_at"] - result["order_purchase_timestamp"]
    ).dt.total_seconds() / seconds_per_hour
    return result


def build_customer_features(order_features: pd.DataFrame) -> pd.DataFrame:
    """Aggregate order metrics to one row per customer and add recency."""
    customer_features = (
        order_features.groupby("customer_id", as_index=False)
        .agg(
            order_count=("order_id", "count"),
            total_customer_spend=("order_revenue", "sum"),
            average_order_value=("order_revenue", "mean"),
            average_review_score=("review_score", "mean"),
            average_delivery_days=("delivery_days", "mean"),
        )
    )
    recency_path = PROCESSED_DATA_DIR / "temporal" / "customer_recency.csv"
    if recency_path.exists():
        recency = pd.read_csv(recency_path, dtype={"customer_id": "string"})
        customer_features = customer_features.merge(
            recency[["customer_id", "days_since_last_purchase"]],
            on="customer_id",
            how="left",
            validate="one_to_one",
        )
    return customer_features


def numeric_frame(df: pd.DataFrame, excluded: set[str]) -> pd.DataFrame:
    """Return numeric analysis columns while excluding identifiers."""
    candidates = df.drop(columns=[column for column in excluded if column in df.columns])
    numeric = candidates.select_dtypes(include="number")
    return numeric.apply(pd.to_numeric, errors="coerce")


def extract_relationships(
    correlation: pd.DataFrame, method: str, threshold: float
) -> pd.DataFrame:
    """Flatten the upper triangle into one row per feature pair."""
    rows: list[dict[str, Any]] = []
    for position, first in enumerate(correlation.columns):
        for second in correlation.columns[position + 1 :]:
            value = correlation.loc[first, second]
            if pd.notna(value):
                rows.append(
                    {
                        "feature_a": first,
                        "feature_b": second,
                        "method": method,
                        "correlation": float(value),
                        "absolute_correlation": abs(float(value)),
                        "strength": (
                            "strong" if abs(float(value)) >= threshold else "moderate_or_weak"
                        ),
                    }
                )
    return pd.DataFrame(rows).sort_values(
        "absolute_correlation", ascending=False
    ) if rows else pd.DataFrame(
        columns=["feature_a", "feature_b", "method", "correlation", "absolute_correlation", "strength"]
    )


def save_heatmap(correlation: pd.DataFrame, path: Path, title: str) -> None:
    """Save a labeled correlation heatmap."""
    fig, ax = plt.subplots(figsize=(11, 9))
    image = ax.imshow(correlation.to_numpy(), cmap="coolwarm", vmin=-1, vmax=1)
    ax.set(
        title=title,
        xticks=range(len(correlation.columns)),
        yticks=range(len(correlation.index)),
        xticklabels=correlation.columns,
        yticklabels=correlation.index,
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    fig.colorbar(image, ax=ax, label="Correlation")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_scatter(df: pd.DataFrame, x: str, y: str, path: Path, title: str) -> None:
    """Save a scatter plot when both requested features are available."""
    if x not in df or y not in df:
        return
    plot_data = df[[x, y]].dropna()
    if plot_data.empty:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(plot_data[x], plot_data[y], alpha=0.25, s=10)
    ax.set(title=title, xlabel=x, ylabel=y)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run_correlation_analysis() -> dict[str, Any]:
    """Run order- and customer-level correlation analysis."""
    order_features = build_order_features()
    customer_features = build_customer_features(order_features)
    order_numeric = numeric_frame(order_features, {"order_id", "customer_id"})
    customer_numeric = numeric_frame(customer_features, {"customer_id"})
    if order_numeric.empty or customer_numeric.empty:
        raise ValueError("No numeric features are available for correlation analysis")

    correlations: dict[str, dict[str, pd.DataFrame]] = {}
    relationship_parts: list[pd.DataFrame] = []
    for grain, numeric in (("order", order_numeric), ("customer", customer_numeric)):
        pearson = numeric.corr(method="pearson", min_periods=2)
        spearman = numeric.corr(method="spearman", min_periods=2)
        correlations[grain] = {"pearson": pearson, "spearman": spearman}
        relationship_parts.extend(
            [
                extract_relationships(pearson, "pearson", STRONG_THRESHOLD),
                extract_relationships(spearman, "spearman", STRONG_THRESHOLD),
            ]
        )

    relationships = pd.concat(relationship_parts, ignore_index=True)
    redundant = relationships[
        relationships["absolute_correlation"] >= REDUNDANT_THRESHOLD
    ].copy()

    ANALYSIS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    CORRELATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    order_features.to_csv(ANALYSIS_DATA_DIR / "order_relationship_features.csv", index=False)
    customer_features.to_csv(ANALYSIS_DATA_DIR / "customer_relationship_features.csv", index=False)
    relationships.to_csv(CORRELATION_OUTPUT_DIR / "relationship_pairs.csv", index=False)
    redundant.to_csv(CORRELATION_OUTPUT_DIR / "redundant_feature_candidates.csv", index=False)

    for grain, matrices in correlations.items():
        for method, matrix in matrices.items():
            matrix.to_csv(CORRELATION_OUTPUT_DIR / f"{method}_{grain}_correlations.csv")
            save_heatmap(
                matrix,
                FIGURE_DIR / f"{grain}_{method}_heatmap.png",
                f"{grain.title()}-Level {method.title()} Correlations",
            )

    save_scatter(
        order_features,
        "delivery_delay_days",
        "review_score",
        FIGURE_DIR / "delivery_delay_vs_review_score.png",
        "Delivery Delay versus Review Score (Order Level)",
    )
    save_scatter(
        order_features,
        "order_item_count",
        "order_revenue",
        FIGURE_DIR / "order_items_vs_revenue.png",
        "Order Items versus Revenue (Order Level)",
    )
    save_scatter(
        customer_features,
        "order_count",
        "total_customer_spend",
        FIGURE_DIR / "customer_orders_vs_spend.png",
        "Customer Order Count versus Spend (Customer Level)",
    )
    save_scatter(
        customer_features,
        "days_since_last_purchase",
        "order_count",
        FIGURE_DIR / "recency_vs_order_count.png",
        "Recency versus Order Count (Customer Level)",
    )

    strongest = relationships.head(10).to_dict(orient="records")
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "analysis_grains": {
            "order": {
                "rows": int(len(order_features)),
                "numeric_features": list(order_numeric.columns),
                "definition": "One row per order; items, payments, and reviews aggregated first.",
            },
            "customer": {
                "rows": int(len(customer_features)),
                "numeric_features": list(customer_numeric.columns),
                "definition": "One row per customer_id aggregated from order-level metrics.",
            },
        },
        "methods": {
            "pearson": "Linear association; sensitive to outliers.",
            "spearman": "Rank-based monotonic association; less sensitive to outliers.",
            "strong_threshold": STRONG_THRESHOLD,
            "redundant_feature_threshold": REDUNDANT_THRESHOLD,
            "minimum_pairwise_observations": 2,
        },
        "strongest_relationships": strongest,
        "correlation_caution": (
            "Correlation means variables move together; it does not prove that one causes "
            "the other. Reverse causality, confounding variables, shared time trends, and "
            "mathematical relationships remain possible explanations."
        ),
        "domain_cautions": [
            "Order count and total customer spend are mechanically related because spend accumulates across orders.",
            "Delivery delay and review score may be associated, but seller, product, and customer factors may confound the relationship.",
            "Missing delivery dates and reviews were preserved rather than globally imputed.",
        ],
        "outputs": {
            "analysis_data": str(ANALYSIS_DATA_DIR.relative_to(PROJECT_ROOT)),
            "reports": str(CORRELATION_OUTPUT_DIR.relative_to(PROJECT_ROOT)),
            "figures": str(FIGURE_DIR.relative_to(PROJECT_ROOT)),
        },
    }
    with (CORRELATION_OUTPUT_DIR / "correlation_summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(report, handle, indent=2, default=str)

    print("\n" + "=" * 70)
    print("CORRELATION ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"Order-level rows: {len(order_features):,}")
    print(f"Customer-level rows: {len(customer_features):,}")
    print(f"Strong relationships found: {len(relationships[relationships['absolute_correlation'] >= STRONG_THRESHOLD]):,}")
    print(f"Potentially redundant pairs: {len(redundant):,}")
    print(f"Reports saved to {CORRELATION_OUTPUT_DIR.relative_to(PROJECT_ROOT)}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run_correlation_analysis()


if __name__ == "__main__":
    main()
