"""Time-Series Analysis Pipeline for Seller Trust & Safety Analysis.

Transforms raw Olist order data into temporal business intelligence using:
1. Daily time-series construction with order volume and revenue.
2. Rolling averages (7-day and 30-day) to smooth noise and reveal trends.
3. Resampling (weekly and monthly) for aggregated period views.
4. Period-over-period (WoW and MoM) growth rates using .pct_change().
5. Cumulative metrics to track platform-wide momentum over time.
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
TIME_SERIES_DATA_DIR = PROCESSED_DATA_DIR / "time_series"
OUTPUT_DIR = PROJECT_ROOT / "output" / "time_series_analysis"


def _load_orders_with_payments() -> pd.DataFrame:
    """Merge the temporal orders table with payment totals, parse timestamps."""
    # Primary source: temporal enriched orders
    orders_path = TEMPORAL_DATA_DIR / "orders_with_time_features.csv"
    if not orders_path.exists():
        raise FileNotFoundError(f"Required input not found: {orders_path}")

    orders = pd.read_csv(orders_path)

    # Bring in payment totals from integrated layer
    pay_path = INTEGRATED_DATA_DIR / "orders_with_payment_totals.csv"
    if pay_path.exists():
        payments = pd.read_csv(pay_path, usecols=["order_id", "total_payment_value"])
        orders = orders.merge(payments, on="order_id", how="left")
    else:
        # Fallback: use order_revenue already in temporal file
        orders["total_payment_value"] = orders.get("order_revenue", np.nan)

    # Coerce the purchase date to datetime
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )
    orders = orders.dropna(subset=["order_purchase_timestamp"])

    # Use total_payment_value as the primary revenue column; fallback to order_revenue
    if "total_payment_value" not in orders.columns or orders["total_payment_value"].isna().all():
        orders["revenue"] = orders.get("order_revenue", 0.0).fillna(0.0)
    else:
        orders["revenue"] = orders["total_payment_value"].fillna(
            orders.get("order_revenue", 0.0).fillna(0.0)
        )

    return orders


def build_daily_series(orders: pd.DataFrame) -> pd.DataFrame:
    """Aggregate order-level data to a complete daily time-series.

    Computes:
    - order_count: number of orders placed per day.
    - daily_revenue: sum of payment value per day.
    - 7-day and 30-day rolling averages for both metrics.
    - Cumulative order count and cumulative revenue.
    """
    print("Building daily time-series...")

    # Set purchase timestamp as the index for resampling
    daily = (
        orders.set_index("order_purchase_timestamp")
        .resample("D")
        .agg(
            order_count=("order_id", "count"),
            daily_revenue=("revenue", "sum"),
        )
    )

    # Fill any missing days with 0 (ensures a contiguous date range)
    daily = daily.asfreq("D", fill_value=0)

    # Rolling averages
    daily["order_count_7d_ma"] = daily["order_count"].rolling(window=7, min_periods=1).mean().round(2)
    daily["order_count_30d_ma"] = daily["order_count"].rolling(window=30, min_periods=1).mean().round(2)
    daily["revenue_7d_ma"] = daily["daily_revenue"].rolling(window=7, min_periods=1).mean().round(2)
    daily["revenue_30d_ma"] = daily["daily_revenue"].rolling(window=30, min_periods=1).mean().round(2)

    # Cumulative metrics
    daily["cumulative_orders"] = daily["order_count"].cumsum()
    daily["cumulative_revenue"] = daily["daily_revenue"].cumsum().round(2)

    daily.index.name = "date"
    daily = daily.reset_index()

    print(f"  → Daily series: {len(daily)} days "
          f"({daily['date'].min().date()} to {daily['date'].max().date()})")
    return daily


def build_weekly_series(daily: pd.DataFrame) -> pd.DataFrame:
    """Resample daily series to weekly aggregations with WoW growth rates.

    Computes:
    - weekly order count, revenue, and average rolling metrics.
    - Week-over-week (WoW) percentage change for order count and revenue.
    """
    print("Building weekly time-series...")

    weekly = (
        daily.set_index("date")
        .resample("W")
        .agg(
            weekly_orders=("order_count", "sum"),
            weekly_revenue=("daily_revenue", "sum"),
            avg_daily_orders=("order_count", "mean"),
            avg_daily_revenue=("daily_revenue", "mean"),
            revenue_7d_ma_end=("revenue_7d_ma", "last"),
        )
    )

    # Period-over-period growth
    weekly["wow_order_count_pct"] = weekly["weekly_orders"].pct_change().mul(100).round(2)
    weekly["wow_revenue_pct"] = weekly["weekly_revenue"].pct_change().mul(100).round(2)

    # Cumulative running totals at week granularity
    weekly["cumulative_weekly_orders"] = weekly["weekly_orders"].cumsum()
    weekly["cumulative_weekly_revenue"] = weekly["weekly_revenue"].cumsum().round(2)

    weekly.index.name = "week_ending"
    weekly = weekly.reset_index()

    print(f"  → Weekly series: {len(weekly)} weeks")
    return weekly


def build_monthly_series(daily: pd.DataFrame) -> pd.DataFrame:
    """Resample daily series to monthly aggregations with MoM growth rates.

    Computes:
    - monthly order count, revenue, and average daily rate.
    - Month-over-month (MoM) percentage change for order count and revenue.
    - 3-month rolling average of monthly revenue to capture medium-term trend.
    """
    print("Building monthly time-series...")

    monthly = (
        daily.set_index("date")
        .resample("ME")
        .agg(
            monthly_orders=("order_count", "sum"),
            monthly_revenue=("daily_revenue", "sum"),
            avg_daily_orders=("order_count", "mean"),
            avg_daily_revenue=("daily_revenue", "mean"),
            peak_daily_orders=("order_count", "max"),
            peak_daily_revenue=("daily_revenue", "max"),
        )
    )

    # Period-over-period growth
    monthly["mom_order_count_pct"] = monthly["monthly_orders"].pct_change().mul(100).round(2)
    monthly["mom_revenue_pct"] = monthly["monthly_revenue"].pct_change().mul(100).round(2)

    # 3-month rolling average of monthly revenue (medium-term smoothing)
    monthly["revenue_3mo_rolling_avg"] = (
        monthly["monthly_revenue"].rolling(window=3, min_periods=1).mean().round(2)
    )

    # Cumulative monthly totals
    monthly["cumulative_monthly_orders"] = monthly["monthly_orders"].cumsum()
    monthly["cumulative_monthly_revenue"] = monthly["monthly_revenue"].cumsum().round(2)

    monthly.index.name = "month_ending"
    monthly = monthly.reset_index()

    print(f"  → Monthly series: {len(monthly)} months")
    return monthly


def compute_trend_summary(
    daily: pd.DataFrame,
    weekly: pd.DataFrame,
    monthly: pd.DataFrame,
) -> dict[str, Any]:
    """Derive executive-level trend insights from the three time-series views."""
    # Most recent 3 months vs previous 3 months
    last_6 = monthly.tail(6)
    recent_3 = last_6.tail(3)
    prior_3 = last_6.head(3)

    recent_rev = float(recent_3["monthly_revenue"].sum())
    prior_rev = float(prior_3["monthly_revenue"].sum())
    revenue_acceleration_pct = (
        round((recent_rev - prior_rev) / prior_rev * 100, 2) if prior_rev else None
    )

    recent_orders = int(recent_3["monthly_orders"].sum())
    prior_orders = int(prior_3["monthly_orders"].sum())
    order_acceleration_pct = (
        round((recent_orders - prior_orders) / prior_orders * 100, 2) if prior_orders else None
    )

    # Longest consecutive revenue growth streak (monthly)
    growth_flags = monthly["mom_revenue_pct"].dropna() > 0
    max_streak = 0
    current_streak = 0
    for flag in growth_flags:
        if flag:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    # Average WoW revenue growth
    avg_wow_revenue_growth = float(weekly["wow_revenue_pct"].dropna().mean().round(2))

    return {
        "date_range": {
            "start": str(daily["date"].min().date()),
            "end": str(daily["date"].max().date()),
            "total_days": int(len(daily)),
        },
        "platform_totals": {
            "total_orders": int(daily["order_count"].sum()),
            "total_revenue": float(daily["daily_revenue"].sum().round(2)),
            "peak_daily_orders": int(daily["order_count"].max()),
            "peak_daily_revenue": float(daily["daily_revenue"].max().round(2)),
        },
        "trend_insights": {
            "recent_3_months_vs_prior_3_months_revenue_pct": revenue_acceleration_pct,
            "recent_3_months_vs_prior_3_months_order_pct": order_acceleration_pct,
            "longest_consecutive_mom_revenue_growth_streak_months": max_streak,
            "avg_wow_revenue_growth_pct": avg_wow_revenue_growth,
        },
        "weekly_summary": {
            "total_weeks": int(len(weekly)),
            "avg_weekly_orders": float(weekly["weekly_orders"].mean().round(2)),
            "avg_weekly_revenue": float(weekly["weekly_revenue"].mean().round(2)),
        },
        "monthly_summary": {
            "total_months": int(len(monthly)),
            "avg_monthly_orders": float(monthly["monthly_orders"].mean().round(2)),
            "avg_monthly_revenue": float(monthly["monthly_revenue"].mean().round(2)),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Time-Series Analysis Pipeline for Olist datasets."
    )
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DATA_DIR)
    parser.add_argument("--integrated-dir", type=Path, default=INTEGRATED_DATA_DIR)
    parser.add_argument("--temporal-dir", type=Path, default=TEMPORAL_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--time-series-dir", type=Path, default=TIME_SERIES_DATA_DIR)
    args = parser.parse_args()

    args.time_series_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Starting time-series analysis pipeline...")

    # 1. Load base data
    orders = _load_orders_with_payments()
    print(f"Loaded {len(orders):,} orders spanning purchase timestamps.")

    # 2. Build time-series views
    daily = build_daily_series(orders)
    weekly = build_weekly_series(daily)
    monthly = build_monthly_series(daily)

    # 3. Export time-series CSVs
    daily_file = args.time_series_dir / "daily_time_series.csv"
    daily.to_csv(daily_file, index=False)
    print(f"✓ Saved daily time-series to {daily_file}")

    weekly_file = args.time_series_dir / "weekly_time_series.csv"
    weekly.to_csv(weekly_file, index=False)
    print(f"✓ Saved weekly time-series to {weekly_file}")

    monthly_file = args.time_series_dir / "monthly_time_series.csv"
    monthly.to_csv(monthly_file, index=False)
    print(f"✓ Saved monthly time-series to {monthly_file}")

    # 4. Trend summary report
    summary = compute_trend_summary(daily, weekly, monthly)

    summary_file = args.output_dir / "time_series_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved trend summary to {summary_file}")

    # 5. Export trend metrics CSV (monthly view for easy comparison)
    trend_cols = [
        "month_ending", "monthly_orders", "monthly_revenue",
        "mom_order_count_pct", "mom_revenue_pct",
        "revenue_3mo_rolling_avg", "cumulative_monthly_revenue",
    ]
    monthly[trend_cols].to_csv(args.output_dir / "trend_metrics.csv", index=False)
    print(f"✓ Saved trend metrics to {args.output_dir / 'trend_metrics.csv'}")

    print("\nTime-series analysis pipeline completed successfully!")


if __name__ == "__main__":
    main()
