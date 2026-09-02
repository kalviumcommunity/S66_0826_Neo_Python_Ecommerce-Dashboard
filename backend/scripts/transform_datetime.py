"""Transform Olist date columns into auditable temporal analysis outputs.

The workflow preserves the processed source CSVs and writes derived temporal
features, aggregations, figures, and audit reports to separate directories.
Olist timestamps are timezone-naive because the source does not provide a
reliable timezone offset; they are not silently treated as UTC.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from importlib import import_module

try:
    dataset_dtypes = import_module("scripts.ingest_data").DATASET_DTYPES
except ModuleNotFoundError:  # Supports direct execution: python scripts/transform_datetime.py
    dataset_dtypes = import_module("ingest_data").DATASET_DTYPES

DATASET_DTYPES = dataset_dtypes


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
TEMPORAL_DATA_DIR = PROCESSED_DATA_DIR / "temporal"
DATETIME_OUTPUT_DIR = PROJECT_ROOT / "output" / "datetime"
FIGURE_DIR = DATETIME_OUTPUT_DIR / "figures"

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

ORDER_TIMESTAMP_COLUMNS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
]
ORDER_DATE_COLUMNS = ["order_estimated_delivery_date"]

DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class DateTransformationError(ValueError):
    """Raised when a date transformation violates an expected invariant."""


def _json_value(value: Any) -> Any:
    """Convert pandas and datetime values into JSON-compatible values."""
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def parse_datetime_column(
    df: pd.DataFrame,
    column: str,
    date_format: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Parse one column with an explicit format and return an audit record."""
    if column not in df.columns:
        raise KeyError(f"Required datetime column not found: {column}")

    original = df[column].copy()
    parsed = pd.to_datetime(original, format=date_format, errors="coerce")
    invalid_mask = original.notna() & parsed.isna()

    if not pd.api.types.is_datetime64_any_dtype(parsed):
        raise DateTransformationError(
            f"{column} did not produce a datetime dtype; got {parsed.dtype}"
        )

    if invalid_mask.any():
        invalid_samples = original.loc[invalid_mask].head(5).tolist()
        raise DateTransformationError(
            f"{column} contains {int(invalid_mask.sum())} invalid non-empty values "
            f"for format {date_format}: {invalid_samples}"
        )

    result = df.copy()
    result[column] = parsed
    audit = {
        "column": column,
        "format": date_format,
        "dtype_before": str(original.dtype),
        "dtype_after": str(parsed.dtype),
        "rows": len(df),
        "original_nulls": int(original.isna().sum()),
        "parsed_nulls": int(parsed.isna().sum()),
        "invalid_non_empty_values": int(invalid_mask.sum()),
        "status": "success",
    }
    return result, audit


def parse_orders(orders: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Parse all Olist order event columns using their documented formats."""
    result = orders.copy()
    audits: list[dict[str, Any]] = []
    for column in ORDER_TIMESTAMP_COLUMNS:
        result, audit = parse_datetime_column(result, column, TIMESTAMP_FORMAT)
        audits.append(audit)
    for column in ORDER_DATE_COLUMNS:
        result, audit = parse_datetime_column(result, column, DATE_FORMAT)
        audits.append(audit)
    return result, audits


def add_time_features(orders: pd.DataFrame) -> pd.DataFrame:
    """Add vectorized calendar and clock features from purchase timestamps."""
    result = orders.copy()
    purchase = result["order_purchase_timestamp"]
    result["purchase_day_of_week"] = purchase.dt.day_name()
    result["purchase_day_number"] = purchase.dt.dayofweek
    result["purchase_hour"] = purchase.dt.hour
    result["purchase_week"] = purchase.dt.isocalendar().week.astype("Int64")
    result["purchase_month"] = purchase.dt.month
    result["purchase_quarter"] = purchase.dt.quarter
    result["purchase_year"] = purchase.dt.year
    result["purchase_date"] = purchase.dt.date.astype("string")
    return result


def build_order_revenue(
    orders: pd.DataFrame, payments: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate payments once per order before joining to avoid double counting."""
    payment_totals = (
        payments.groupby("order_id", as_index=False, dropna=False)["payment_value"]
        .sum(min_count=1)
        .rename(columns={"payment_value": "order_revenue"})
    )
    result = orders.merge(payment_totals, on="order_id", how="left", validate="one_to_one")
    result["order_revenue"] = result["order_revenue"].fillna(0)
    return result


def build_weekly_metrics(orders: pd.DataFrame) -> pd.DataFrame:
    """Create weekly count, unique-customer, revenue, and average-value metrics."""
    return (
        orders.set_index("order_purchase_timestamp")
        .resample("W")
        .agg(
            order_count=("order_id", "count"),
            customer_count=("customer_id", "nunique"),
            revenue=("order_revenue", "sum"),
            average_order_value=("order_revenue", "mean"),
        )
        .reset_index()
    )


def build_day_hour_metrics(orders: pd.DataFrame) -> pd.DataFrame:
    """Aggregate order activity by readable day and hour."""
    result = (
        orders.groupby(
            ["purchase_day_of_week", "purchase_day_number", "purchase_hour"],
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "count"),
            revenue=("order_revenue", "sum"),
            average_order_value=("order_revenue", "mean"),
        )
    )
    return result.sort_values(["purchase_day_number", "purchase_hour"])


def build_activity_pivot(orders: pd.DataFrame) -> pd.DataFrame:
    """Return an hour-by-weekday order-volume table."""
    pivot = pd.pivot_table(
        orders,
        values="order_id",
        index="purchase_hour",
        columns="purchase_day_of_week",
        aggfunc="count",
        fill_value=0,
    )
    return pivot.reindex(columns=DAY_ORDER, fill_value=0).sort_index()


def build_customer_recency(orders: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """Calculate reproducible days since each customer's latest purchase."""
    last_purchase = (
        orders.groupby("customer_id", as_index=False)["order_purchase_timestamp"]
        .max()
        .rename(columns={"order_purchase_timestamp": "last_purchase_timestamp"})
    )
    last_purchase["days_since_last_purchase"] = (
        as_of - last_purchase["last_purchase_timestamp"]
    ).dt.days
    last_purchase["inactive_30_days"] = last_purchase["days_since_last_purchase"] >= 30
    last_purchase["inactive_60_days"] = last_purchase["days_since_last_purchase"] >= 60
    last_purchase["inactive_90_days"] = last_purchase["days_since_last_purchase"] >= 90
    return last_purchase


def find_peak_windows(day_hour_metrics: pd.DataFrame, limit: int = 5) -> list[dict[str, Any]]:
    """Return the busiest day/hour combinations by order count."""
    peaks = day_hour_metrics.sort_values(
        ["order_count", "revenue"], ascending=[False, False]
    ).head(limit)
    return [
        {
            "day_of_week": row.purchase_day_of_week,
            "hour": int(row.purchase_hour),
            "order_count": int(row.order_count),
            "revenue": float(row.revenue),
            "average_order_value": float(row.average_order_value),
        }
        for row in peaks.itertuples(index=False)
    ]


def create_figures(
    orders: pd.DataFrame,
    weekly_metrics: pd.DataFrame,
    activity_pivot: pd.DataFrame,
    recency: pd.DataFrame,
) -> None:
    """Write the required temporal distribution and trend figures."""
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    hourly = orders.groupby("purchase_hour").size().reindex(range(24), fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(hourly.index, hourly.values)
    ax.set(title="Olist Orders by Purchase Hour", xlabel="Hour of day", ylabel="Orders")
    ax.set_xticks(range(24))
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "hourly_order_volume.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(weekly_metrics["order_purchase_timestamp"], weekly_metrics["order_count"])
    ax.set(title="Weekly Order Trend", xlabel="Week", ylabel="Orders")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "weekly_order_trend.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 7))
    image = ax.imshow(activity_pivot.to_numpy(), aspect="auto", cmap="YlOrRd")
    ax.set(
        title="Order Activity by Hour and Day",
        xlabel="Day of week",
        ylabel="Hour of day",
        xticks=range(len(activity_pivot.columns)),
        xticklabels=activity_pivot.columns,
        yticks=range(len(activity_pivot.index)),
        yticklabels=activity_pivot.index,
    )
    fig.colorbar(image, ax=ax, label="Orders")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "day_hour_activity_heatmap.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(recency["days_since_last_purchase"], bins=30)
    ax.set(
        title="Customer Recency Distribution",
        xlabel="Days since last purchase",
        ylabel="Customers",
    )
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "customer_recency_distribution.png", dpi=150)
    plt.close(fig)


def _read_processed(filename: str) -> pd.DataFrame:
    path = PROCESSED_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required processed file not found: {path}")
    return pd.read_csv(path, dtype=DATASET_DTYPES.get(filename))


def run_datetime_pipeline(as_of: str | None = None) -> dict[str, Any]:
    """Run the complete temporal transformation workflow."""
    orders_raw = _read_processed("olist_orders_dataset.csv")
    payments = _read_processed("olist_order_payments_dataset.csv")
    orders, date_audits = parse_orders(orders_raw)
    orders = add_time_features(orders)
    orders = build_order_revenue(orders, payments)

    max_purchase = orders["order_purchase_timestamp"].max()
    if pd.isna(max_purchase):
        raise DateTransformationError("No valid order purchase timestamps were found")
    if as_of is None:
        reference_date = max_purchase
    else:
        reference_date = pd.to_datetime(as_of, format=TIMESTAMP_FORMAT, errors="raise")
    if reference_date < max_purchase:
        raise DateTransformationError("The as-of timestamp cannot precede the latest purchase")

    weekly_metrics = build_weekly_metrics(orders)
    day_hour_metrics = build_day_hour_metrics(orders)
    activity_pivot = build_activity_pivot(orders)
    recency = build_customer_recency(orders, reference_date)
    peaks = find_peak_windows(day_hour_metrics)

    TEMPORAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATETIME_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    orders.to_csv(TEMPORAL_DATA_DIR / "orders_with_time_features.csv", index=False)
    recency.to_csv(TEMPORAL_DATA_DIR / "customer_recency.csv", index=False)
    weekly_metrics.to_csv(TEMPORAL_DATA_DIR / "weekly_order_metrics.csv", index=False)
    day_hour_metrics.to_csv(TEMPORAL_DATA_DIR / "day_hour_metrics.csv", index=False)
    activity_pivot.to_csv(TEMPORAL_DATA_DIR / "activity_pivot.csv")
    date_audit = pd.DataFrame(date_audits)
    date_audit.to_csv(DATETIME_OUTPUT_DIR / "datetime_column_audit.csv", index=False)
    create_figures(orders, weekly_metrics, activity_pivot, recency)

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timezone_note": "Source Olist timestamps are timezone-naive; no UTC conversion was applied.",
        "timestamp_format": TIMESTAMP_FORMAT,
        "date_format": DATE_FORMAT,
        "input_files": [
            "data/processed/olist_orders_dataset.csv",
            "data/processed/olist_order_payments_dataset.csv",
        ],
        "rows_processed": int(len(orders)),
        "customers": int(recency["customer_id"].nunique()),
        "date_min": _json_value(orders["order_purchase_timestamp"].min()),
        "date_max": _json_value(orders["order_purchase_timestamp"].max()),
        "weeks": int(len(weekly_metrics)),
        "as_of": reference_date.isoformat(),
        "peak_activity_windows": peaks,
        "recency": {
            "min_days": int(recency["days_since_last_purchase"].min()),
            "max_days": int(recency["days_since_last_purchase"].max()),
            "median_days": float(recency["days_since_last_purchase"].median()),
            "inactive_90_days": int(recency["inactive_90_days"].sum()),
        },
        "outputs": {
            "temporal_data": str(TEMPORAL_DATA_DIR.relative_to(PROJECT_ROOT)),
            "reports": str(DATETIME_OUTPUT_DIR.relative_to(PROJECT_ROOT)),
            "figures": str(FIGURE_DIR.relative_to(PROJECT_ROOT)),
        },
    }
    with (DATETIME_OUTPUT_DIR / "datetime_transformation_summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(summary, handle, indent=2, default=str)
    with (DATETIME_OUTPUT_DIR / "peak_activity_windows.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(peaks, handle, indent=2, default=str)
    with (DATETIME_OUTPUT_DIR / "recency_summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(summary["recency"], handle, indent=2, default=str)

    print("\n" + "=" * 70)
    print("DATE AND TIME TRANSFORMATION COMPLETE")
    print("=" * 70)
    print(f"Date range: {summary['date_min']} to {summary['date_max']}")
    print(f"Parsed purchase dtype: {orders['order_purchase_timestamp'].dtype}")
    print(f"Weeks represented: {summary['weeks']:,}")
    print(f"Customers analyzed: {summary['customers']:,}")
    print(f"Customers inactive for 90+ days: {summary['recency']['inactive_90_days']:,}")
    print(f"Peak window: {peaks[0]['day_of_week']} at {peaks[0]['hour']:02d}:00")
    print(f"Reports saved to {DATETIME_OUTPUT_DIR.relative_to(PROJECT_ROOT)}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-of",
        help=(
            "Optional reference timestamp in YYYY-MM-DD HH:MM:SS format. "
            "Defaults to the latest purchase timestamp for reproducibility."
        ),
    )
    args = parser.parse_args()
    run_datetime_pipeline(as_of=args.as_of)


if __name__ == "__main__":
    main()
