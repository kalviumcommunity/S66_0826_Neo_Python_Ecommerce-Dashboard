"""Anomaly Detection Pipeline for Seller Trust & Safety Analysis.

Applies two detection methodologies to Olist daily order volume and revenue:
1. Threshold-Based Detection: fixed limits for operational monitoring.
2. Statistical Detection: Rolling Z-scores (rolling mean & std) to find anomalies.

Logs anomalies with observed value, expected range, z-score, and severity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
INTEGRATED_DATA_DIR = PROCESSED_DATA_DIR / "integrated"
OUTPUT_DIR = PROJECT_ROOT / "output" / "anomaly_logs"


def load_daily_series(file_path: Path) -> pd.DataFrame:
    """Load customer order view and aggregate to daily grain."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    # Load file
    df = pd.read_csv(file_path)

    # Deduplicate at the order level to prevent multiple items inflating counts
    order_level = df.drop_duplicates(subset=["order_id"]).copy()
    order_level["order_purchase_timestamp"] = pd.to_datetime(
        order_level["order_purchase_timestamp"]
    )

    # Resample to contiguous daily time-series
    daily = (
        order_level.set_index("order_purchase_timestamp")
        .resample("D")
        .agg(
            order_count=("order_id", "count"),
            revenue=("total_payment_value", "sum"),
        )
        .fillna(0.0)
    )

    # Sort index
    daily = daily.sort_index()
    daily.index.name = "date"
    return daily.reset_index()


def detect_threshold_anomalies(
    df: pd.DataFrame,
    min_orders: int = 15,
    min_revenue: float = 2000.0,
    max_revenue: float = 120000.0,
) -> list[dict[str, Any]]:
    """Detect anomalies violating absolute operational boundaries."""
    anomalies = []

    # We filter out the first 30 days and last 30 days of the dataset to avoid ramp-up/ramp-down artifacts
    start_date = df["date"].min() + pd.Timedelta(days=30)
    end_date = df["date"].max() - pd.Timedelta(days=30)
    operational_df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    for _, row in operational_df.iterrows():
        date_str = str(row["date"].date())

        # Check Order Count
        if row["order_count"] < min_orders:
            anomalies.append({
                "date": date_str,
                "metric": "order_count",
                "observed_value": int(row["order_count"]),
                "detection_method": "threshold",
                "expected_range": f">= {min_orders}",
                "z_score": None,
                "severity": "Critical" if row["order_count"] < (min_orders / 2) else "Warning",
                "details": f"Daily orders fell below threshold of {min_orders}.",
            })

        # Check Revenue Low Boundary
        if row["revenue"] < min_revenue:
            anomalies.append({
                "date": date_str,
                "metric": "revenue",
                "observed_value": float(round(row["revenue"], 2)),
                "detection_method": "threshold",
                "expected_range": f">= {min_revenue}",
                "z_score": None,
                "severity": "Critical" if row["revenue"] < (min_revenue / 2) else "Warning",
                "details": f"Daily revenue fell below threshold of {min_revenue} BRL.",
            })

        # Check Revenue High Boundary (Spikes)
        if row["revenue"] > max_revenue:
            anomalies.append({
                "date": date_str,
                "metric": "revenue",
                "observed_value": float(round(row["revenue"], 2)),
                "detection_method": "threshold",
                "expected_range": f"<= {max_revenue}",
                "z_score": None,
                "severity": "Warning",
                "details": f"Daily revenue exceeded high threshold of {max_revenue} BRL.",
            })

    return anomalies


def detect_statistical_anomalies(
    df: pd.DataFrame,
    window: int = 14,
    z_threshold: float = 2.0,
) -> list[dict[str, Any]]:
    """Detect statistical anomalies using a rolling Z-score."""
    anomalies = []

    # Calculate rolling metrics
    for metric in ["order_count", "revenue"]:
        df[f"{metric}_roll_mean"] = df[metric].rolling(window=window, min_periods=7).mean()
        df[f"{metric}_roll_std"] = df[metric].rolling(window=window, min_periods=7).std()

        # Handle division by zero or NaN std
        df[f"{metric}_roll_std"] = df[f"{metric}_roll_std"].replace(0.0, np.nan)
        df[f"{metric}_zscore"] = (df[metric] - df[f"{metric}_roll_mean"]) / df[f"{metric}_roll_std"]

    # We evaluate points where a valid rolling window exists
    valid_df = df.dropna(subset=["order_count_roll_mean", "revenue_roll_mean"])

    for _, row in valid_df.iterrows():
        date_str = str(row["date"].date())

        for metric in ["order_count", "revenue"]:
            z = row[f"{metric}_zscore"]
            if pd.isna(z):
                continue

            if abs(z) > z_threshold:
                mean_val = row[f"{metric}_roll_mean"]
                std_val = row[f"{metric}_roll_std"]
                expected_min = max(0, mean_val - z_threshold * std_val)
                expected_max = mean_val + z_threshold * std_val

                severity = "Critical" if abs(z) > 3.0 else "Warning"
                direction = "drop" if z < 0 else "spike"

                anomalies.append({
                    "date": date_str,
                    "metric": metric,
                    "observed_value": float(round(row[metric], 2)) if metric == "revenue" else int(row[metric]),
                    "detection_method": "statistical_zscore",
                    "expected_range": f"{round(expected_min, 2)} to {round(expected_max, 2)}",
                    "z_score": float(round(z, 2)),
                    "severity": severity,
                    "details": f"Significant {direction} (Z-score: {round(z, 2)}).",
                })

    return anomalies


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute and log anomalies in daily orders and revenue."
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        default=INTEGRATED_DATA_DIR / "customer_order_item_view.csv",
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Running anomaly detection pipeline...")

    # 1. Load Daily aggregated series
    daily_df = load_daily_series(args.input_file)
    print(f"Aggregated daily timeseries loaded: {len(daily_df)} days.")

    # 2. Run Threshold-based alerts
    threshold_anomalies = detect_threshold_anomalies(
        daily_df, min_orders=15, min_revenue=2000.0, max_revenue=120000.0
    )
    print(f"✓ Found {len(threshold_anomalies)} threshold boundary violations.")

    # 3. Run Statistical Z-score alerts
    statistical_anomalies = detect_statistical_anomalies(
        daily_df, window=14, z_threshold=2.2
    )
    print(f"✓ Found {len(statistical_anomalies)} statistical anomalies (|Z| > 2.2).")

    # Combine anomalies
    all_anomalies = threshold_anomalies + statistical_anomalies

    # Save daily anomalies data as a CSV for reporting
    daily_anomalies_summary = daily_df.copy()
    daily_anomalies_summary["has_anomaly"] = daily_anomalies_summary["date"].map(
        lambda d: str(d.date()) in [a["date"] for a in all_anomalies]
    )
    daily_anomalies_summary.to_csv(args.output_dir / "daily_anomaly_metrics.csv", index=False)
    print(f"✓ Saved daily metrics to {args.output_dir / 'daily_anomaly_metrics.csv'}")

    # Export structured log report
    anomaly_report = {
        "pipeline": "Anomaly Detection & Logging",
        "total_anomalies_detected": len(all_anomalies),
        "threshold_violations": len(threshold_anomalies),
        "statistical_anomalies": len(statistical_anomalies),
        "anomalies": all_anomalies,
    }

    json_file = args.output_dir / "anomalies_log.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(anomaly_report, f, indent=2)
    print(f"✓ Saved structured anomaly log to {json_file}")

    # Print high severity highlights
    critical_alerts = [a for a in all_anomalies if a["severity"] == "Critical"]
    print(f"\n=======================================================")
    print(f"  Anomaly Detection Summary: {len(all_anomalies)} anomalies logged")
    print(f"  ({len(critical_alerts)} Critical alert(s) requiring immediate attention)")
    print(f"=======================================================")
    if critical_alerts:
        for alert in critical_alerts[:10]:
            print(
                f"  ✗ [CRITICAL] {alert['date']} - {alert['metric']}: "
                f"Observed {alert['observed_value']} (Expected: {alert['expected_range']}) "
                f"| {alert['details']}"
            )
        if len(critical_alerts) > 10:
            print(f"  ... and {len(critical_alerts) - 10} more Critical alerts.")
    else:
        print("  ✓ No critical anomalies detected.")
    print(f"=======================================================")

    print("\nAnomaly detection pipeline completed successfully!")


if __name__ == "__main__":
    main()
