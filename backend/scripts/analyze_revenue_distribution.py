"""Analyze order and customer revenue distributions.

Revenue is taken from the payment-aggregated order view so that multiple
payment rows do not double-count an order. Outputs are written to
``output/revenue_analysis``.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTEGRATED_DIR = PROJECT_ROOT / "data" / "processed" / "integrated"
OUTPUT_DIR = PROJECT_ROOT / "output" / "revenue_analysis"
ORDERS_FILE = INTEGRATED_DIR / "orders_with_payment_totals.csv"
CUSTOMER_ORDERS_FILE = INTEGRATED_DIR / "customer_order_view.csv"


def load_data() -> pd.DataFrame:
    """Load one row per order and attach the stable customer identifier."""
    orders = pd.read_csv(ORDERS_FILE)
    customer_orders = pd.read_csv(CUSTOMER_ORDERS_FILE)

    required_order_columns = {"order_id", "total_payment_value"}
    missing = required_order_columns - set(orders.columns)
    if missing:
        raise ValueError(f"Missing order columns: {sorted(missing)}")

    if orders["order_id"].duplicated().any():
        raise ValueError("orders_with_payment_totals.csv is not one row per order")

    customer_columns = ["order_id"]
    if "customer_unique_id" in customer_orders.columns:
        customer_columns.append("customer_unique_id")

    data = orders.merge(
        customer_orders[customer_columns],
        on="order_id",
        how="left",
        validate="one_to_one",
    )
    data["revenue"] = pd.to_numeric(data["total_payment_value"], errors="coerce")
    data = data.dropna(subset=["revenue"]).copy()
    
    if data.empty:
        raise ValueError("No valid revenue values found after coercion; nothing to analyze")
        
    if (data["revenue"] < 0).any():
        raise ValueError("Negative revenue values were found; review refunds before analysis")

    return data


def describe_revenue(revenue: pd.Series) -> tuple[pd.DataFrame, dict[str, float]]:
    """Calculate descriptive statistics, skewness, and excess kurtosis."""
    percentiles = revenue.quantile([0.25, 0.50, 0.75, 0.90, 0.95, 0.99])
    stats = {
        "count": int(revenue.size),
        "mean": float(revenue.mean()),
        "median": float(revenue.median()),
        "std": float(revenue.std()),
        "min": float(revenue.min()),
        "max": float(revenue.max()),
        "skewness": float(revenue.skew()),
        # pandas kurtosis is Fisher/excess kurtosis: normal distribution = 0.
        "excess_kurtosis": float(revenue.kurtosis()),
        "p25": float(percentiles.loc[0.25]),
        "p50": float(percentiles.loc[0.50]),
        "p75": float(percentiles.loc[0.75]),
        "p90": float(percentiles.loc[0.90]),
        "p95": float(percentiles.loc[0.95]),
        "p99": float(percentiles.loc[0.99]),
    }

    percentile_table = percentiles.rename("revenue").rename_axis("percentile").reset_index()
    percentile_table["percentile"] = percentile_table["percentile"].map(lambda value: f"P{int(value * 100)}")
    percentile_table["revenue"] = percentile_table["revenue"].round(2)
    return percentile_table, stats


def concentration_table(revenue: pd.Series) -> pd.DataFrame:
    """Measure how much revenue is contributed by the largest observations."""
    ordered = revenue.sort_values(ascending=False)
    rows = []
    for label, proportion in (("Top 1%", 0.01), ("Top 5%", 0.05), ("Top 10%", 0.10)):
        count = max(1, int(np.ceil(len(ordered) * proportion)))
        rows.append(
            {
                "group": label,
                "observations": count,
                "observation_share": count / len(ordered),
                "revenue": float(ordered.head(count).sum()),
                "revenue_share": float(ordered.head(count).sum() / ordered.sum()),
            }
        )
    return pd.DataFrame(rows)


def assign_segments(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    """Assign order tiers and, when possible, customer-value tiers."""
    result = data.copy()
    result["order_segment"] = pd.qcut(
        result["revenue"],
        q=[0, 0.25, 0.75, 1],
        labels=["Low-value", "Mid-value", "High-value"],
    )

    order_summary = (
        result.groupby("order_segment", observed=True)["revenue"]
        .agg(
            observation_count="count",
            mean="mean",
            median="median",
            minimum="min",
            maximum="max",
            total_revenue="sum",
        )
        .reset_index()
    )
    order_summary["observation_share"] = order_summary["observation_count"] / len(result)
    order_summary["revenue_share"] = order_summary["total_revenue"] / result["revenue"].sum()

    customer_summary = None
    if "customer_unique_id" in result.columns:
        customers = (
            result.dropna(subset=["customer_unique_id"])
            .groupby("customer_unique_id", as_index=False)
            .agg(
                customer_revenue=("revenue", "sum"),
                order_count=("order_id", "nunique"),
                average_order_value=("revenue", "mean"),
            )
        )
        customers["customer_segment"] = pd.qcut(
            customers["customer_revenue"],
            q=[0, 0.50, 0.90, 0.99, 1],
            labels=["Low-value", "Regular", "High-value", "VIP"],
        )
        customer_summary = (
            customers.groupby("customer_segment", observed=True)
            .agg(
                customer_count=("customer_unique_id", "count"),
                mean_revenue=("customer_revenue", "mean"),
                median_revenue=("customer_revenue", "median"),
                total_revenue=("customer_revenue", "sum"),
                mean_orders=("order_count", "mean"),
            )
            .reset_index()
        )
        customer_summary["customer_share"] = customer_summary["customer_count"] / len(customers)
        customer_summary["revenue_share"] = customer_summary["total_revenue"] / customers["customer_revenue"].sum()
        customer_output = customers.copy()
        customer_output[["customer_revenue", "average_order_value"]] = customer_output[
            ["customer_revenue", "average_order_value"]
        ].round(2)
        customer_output.to_csv(OUTPUT_DIR / "customer_revenue_segments.csv", index=False)

        customer_summary_output = customer_summary.copy()
        customer_currency_columns = ["mean_revenue", "median_revenue", "total_revenue"]
        customer_summary_output[customer_currency_columns] = customer_summary_output[
            customer_currency_columns
        ].round(2)
        customer_summary_output[["customer_share", "revenue_share", "mean_orders"]] = (
            customer_summary_output[["customer_share", "revenue_share", "mean_orders"]].round(6)
        )
        customer_summary_output.to_csv(
            OUTPUT_DIR / "customer_revenue_segment_summary.csv", index=False
        )

    return result, order_summary, customer_summary


def create_plots(data: pd.DataFrame) -> None:
    """Create raw, zoomed, KDE, log-scale, and segment plots."""
    revenue = data["revenue"]
    sns.set_theme(style="whitegrid")

    fig, axes = plt.subplots(1, 3, figsize=(20, 5))
    axes[0].hist(revenue, bins=50, edgecolor="black")
    axes[0].set_title("Order Revenue Distribution")
    axes[0].set_xlabel("Revenue")
    axes[0].set_ylabel("Number of Orders")

    sns.kdeplot(revenue, fill=True, ax=axes[1])
    axes[1].set_title("Order Revenue KDE")
    axes[1].set_xlabel("Revenue")

    axes[2].hist(np.log1p(revenue), bins=50, edgecolor="black")
    axes[2].set_title("Log-Transformed Revenue Distribution")
    axes[2].set_xlabel("log(1 + Revenue)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "revenue_distribution.png", dpi=150)
    plt.close(fig)

    # The maximum value stretches the raw x-axis, so provide a readable view
    # of the main distribution without removing observations from the analysis.
    p99 = revenue.quantile(0.99)
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    axes[0].hist(revenue, bins=50, range=(0, p99), edgecolor="black")
    axes[0].axvline(revenue.median(), color="crimson", linestyle="--", label="Median")
    axes[0].axvline(p99, color="darkorange", linestyle="--", label="P99")
    axes[0].set_title("Order Revenue Distribution up to P99")
    axes[0].set_xlabel("Revenue")
    axes[0].set_ylabel("Number of Orders")
    axes[0].legend()

    business_bins = [0, 25, 50, 75, 100, 150, 200, 300, 500, 1000, 2000, 5000, 15000]
    axes[1].hist(revenue, bins=business_bins, edgecolor="black")
    axes[1].set_title("Order Revenue with Business-Friendly Bins")
    axes[1].set_xlabel("Revenue")
    axes[1].set_ylabel("Number of Orders")
    axes[1].tick_params(axis="x", rotation=45)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "revenue_distribution_zoomed.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    sns.boxplot(data=data, x="order_segment", y="revenue", showfliers=False, ax=axes[0])
    axes[0].set_title("Revenue by Order Segment")
    axes[0].set_ylabel("Revenue")
    log_data = data.assign(log_revenue=np.log1p(data["revenue"]))
    sns.boxplot(data=log_data, x="order_segment", y="log_revenue", showfliers=False, ax=axes[1])
    axes[1].set_title("Log Revenue by Order Segment")
    axes[1].set_ylabel("log(1 + Revenue)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "revenue_segments.png", dpi=150)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_data()
    percentile_table, stats = describe_revenue(data["revenue"])
    concentration = concentration_table(data["revenue"])
    segmented_data, order_summary, customer_summary = assign_segments(data)
    create_plots(segmented_data)

    concentration_output = concentration.copy()
    concentration_output["revenue"] = concentration_output["revenue"].round(2)
    concentration_output[["observation_share", "revenue_share"]] = concentration_output[
        ["observation_share", "revenue_share"]
    ].round(6)

    order_summary_output = order_summary.copy()
    order_currency_columns = ["mean", "median", "minimum", "maximum", "total_revenue"]
    order_summary_output[order_currency_columns] = order_summary_output[order_currency_columns].round(2)
    order_summary_output[["observation_share", "revenue_share"]] = order_summary_output[
        ["observation_share", "revenue_share"]
    ].round(6)

    percentile_table.to_csv(OUTPUT_DIR / "revenue_percentiles.csv", index=False)
    concentration_output.to_csv(OUTPUT_DIR / "revenue_concentration.csv", index=False)
    order_summary_output.to_csv(OUTPUT_DIR / "order_revenue_segments.csv", index=False)

    report = {
        "source": ORDERS_FILE.relative_to(PROJECT_ROOT).as_posix(),
        "revenue_column": "total_payment_value",
        "analysis_grain": "order",
        "customer_grain": "customer_unique_id" if customer_summary is not None else None,
        "statistics": {
            key: round(value, 2) if key not in {"skewness", "excess_kurtosis"} else round(value, 6)
            for key, value in stats.items()
        },
        "interpretation": {
            "skewness": "Highly right-skewed; use median and percentiles with the mean." if stats["skewness"] > 1 else "Not highly right-skewed.",
            "kurtosis": "Very heavy tails; investigate extreme values." if stats["excess_kurtosis"] > 3 else "Not extremely heavy-tailed under the excess-kurtosis threshold.",
            "business_action": "Separate regular and high-value customers and investigate the top revenue contributors." if stats["skewness"] > 1 else "A single broad strategy may be reasonable, subject to segment checks.",
        },
    }
    (OUTPUT_DIR / "revenue_analysis_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    print("Revenue analysis complete")
    print(f"Orders analyzed: {stats['count']:,}")
    print(f"Mean: ${stats['mean']:,.2f}")
    print(f"Median: ${stats['median']:,.2f}")
    print(f"Skewness: {stats['skewness']:.2f}")
    print(f"Excess kurtosis: {stats['excess_kurtosis']:.2f}")
    print(f"Outputs: {OUTPUT_DIR.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
