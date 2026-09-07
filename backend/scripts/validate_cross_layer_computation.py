"""Cross-Layer Computational Validation Pipeline (SQL vs. Python).

Validates computational parity between SQL queries and Python/Pandas workflows,
detecting and diagnosing computation drift caused by:
- Definition mismatches
- Schema change drift & NULL vs. NaN treatment
- Precision, rounding, and floating point variances
- Aggregation semantics (pre-join vs. post-join multiplicity)

Generates automated parity comparisons, drift diagnosis reports, and tolerance assertions.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "analytics.db"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
QUERIES_DIR = PROJECT_ROOT / "queries"
OUTPUT_DIR = PROJECT_ROOT / "output" / "cross_layer_validation"

# Numerical tolerance thresholds
TOLERANCE_ABSOLUTE_COUNT = 0       # Discrete entity counts must match exactly
TOLERANCE_FINANCIAL_ABS = 0.05     # Up to 5 cents permitted for intermediate float sum rounding
TOLERANCE_RATIO_ABS = 0.001        # Ratio / percentage difference tolerance (0.1%)


def validate_order_status_distribution(
    con: sqlite3.Connection,
    processed_dir: Path,
    queries_dir: Path,
) -> Dict[str, Any]:
    """Test 1: Validate categorical status distribution between SQL and Python."""
    # SQL computation
    with open(queries_dir / "validation_order_status_distribution.sql", "r", encoding="utf-8") as f:
        sql_query = f.read()
    df_sql = pd.read_sql_query(sql_query, con)

    # Python computation directly from clean processed CSV
    df_orders = pd.read_csv(processed_dir / "olist_orders_dataset.csv", usecols=["order_id", "order_status"])
    df_py = (
        df_orders.groupby("order_status")["order_id"]
        .count()
        .reset_index()
        .rename(columns={"order_id": "order_count"})
        .sort_values(by=["order_count", "order_status"], ascending=[False, True])
        .reset_index(drop=True)
    )

    merged = pd.merge(df_sql, df_py, on="order_status", suffixes=("_sql", "_python"))
    merged["discrepancy"] = merged["order_count_sql"] - merged["order_count_python"]
    max_drift = int(merged["discrepancy"].abs().max())

    passed = max_drift <= TOLERANCE_ABSOLUTE_COUNT
    return {
        "test_name": "Order Status Distribution",
        "passed": passed,
        "max_absolute_drift": max_drift,
        "status_categories_checked": len(merged),
        "discrepancies": merged[merged["discrepancy"] != 0].to_dict(orient="records"),
        "comparison_sample": merged.to_dict(orient="records"),
    }


def validate_monthly_revenue(
    con: sqlite3.Connection,
    processed_dir: Path,
    queries_dir: Path,
) -> Dict[str, Any]:
    """Test 2: Validate monthly revenue and volume between SQL and Python."""
    # SQL computation
    with open(queries_dir / "validation_monthly_revenue_metrics.sql", "r", encoding="utf-8") as f:
        sql_query = f.read()
    df_sql = pd.read_sql_query(sql_query, con)

    # Python computation directly from clean processed CSVs
    df_orders = pd.read_csv(
        processed_dir / "olist_orders_dataset.csv",
        usecols=["order_id", "order_status", "order_purchase_timestamp"],
    )
    df_payments = pd.read_csv(
        processed_dir / "olist_order_payments_dataset.csv",
        usecols=["order_id", "payment_value"],
    )

    # Filter out canceled and null timestamps in Python to match authoritative business rule
    valid_orders = df_orders[
        (df_orders["order_purchase_timestamp"].notna()) & (df_orders["order_status"] != "canceled")
    ].copy()
    valid_orders["order_month"] = valid_orders["order_purchase_timestamp"].str.slice(0, 7)

    # Pre-aggregate payments by order_id before joining (preventing cardinality multiplication)
    order_payment_sum = df_payments.groupby("order_id")["payment_value"].sum().reset_index()

    merged_orders = pd.merge(valid_orders, order_payment_sum, on="order_id", how="left")
    merged_orders["payment_value"] = merged_orders["payment_value"].fillna(0.0)

    py_metrics = (
        merged_orders.groupby("order_month")
        .agg(
            total_orders=("order_id", "nunique"),
            total_revenue=("payment_value", "sum"),
            avg_payment_value=("payment_value", "mean"),
        )
        .reset_index()
    )
    py_metrics["total_revenue"] = py_metrics["total_revenue"].round(2)
    py_metrics["avg_payment_value"] = py_metrics["avg_payment_value"].round(2)

    comp = pd.merge(df_sql, py_metrics, on="order_month", suffixes=("_sql", "_python"))
    comp["order_diff"] = comp["total_orders_sql"] - comp["total_orders_python"]
    comp["revenue_diff"] = (comp["total_revenue_sql"] - comp["total_revenue_python"]).round(2)
    comp["avg_payment_diff"] = (comp["avg_payment_value_sql"] - comp["avg_payment_value_python"]).round(2)

    max_rev_diff = float(comp["revenue_diff"].abs().max())
    max_order_diff = int(comp["order_diff"].abs().max())

    passed = (max_order_diff <= TOLERANCE_ABSOLUTE_COUNT) and (max_rev_diff <= TOLERANCE_FINANCIAL_ABS)

    return {
        "test_name": "Monthly Revenue & Order Volume",
        "passed": passed,
        "max_order_drift": max_order_diff,
        "max_revenue_drift": max_rev_diff,
        "months_evaluated": len(comp),
        "discrepancies": comp[(comp["order_diff"] != 0) | (comp["revenue_diff"].abs() > TOLERANCE_FINANCIAL_ABS)].to_dict(orient="records"),
        "comparison_sample": comp.head(10).to_dict(orient="records"),
    }


def validate_seller_kpis(
    con: sqlite3.Connection,
    processed_dir: Path,
    queries_dir: Path,
) -> Dict[str, Any]:
    """Test 3: Validate seller-level aggregation between SQL and Python."""
    # SQL computation
    with open(queries_dir / "validation_seller_kpis.sql", "r", encoding="utf-8") as f:
        sql_query = f.read()
    df_sql = pd.read_sql_query(sql_query, con)

    # Python computation directly from CSVs
    df_orders = pd.read_csv(processed_dir / "olist_orders_dataset.csv", usecols=["order_id", "order_status"])
    df_items = pd.read_csv(processed_dir / "olist_order_items_dataset.csv", usecols=["order_id", "seller_id", "price"])
    df_reviews = pd.read_csv(processed_dir / "olist_order_reviews_dataset.csv", usecols=["order_id", "review_score"])

    # Keep only delivered orders
    delivered_orders = set(df_orders[df_orders["order_status"] == "delivered"]["order_id"])
    filtered_items = df_items[df_items["order_id"].isin(delivered_orders)].copy()

    # Pre-aggregate reviews by order_id
    order_reviews = df_reviews.groupby("order_id")["review_score"].mean().reset_index()
    items_with_reviews = pd.merge(filtered_items, order_reviews, on="order_id", how="left")

    py_seller = (
        items_with_reviews.groupby("seller_id")
        .agg(
            total_orders=("order_id", "nunique"),
            total_sales=("price", lambda x: round(float(np.nansum(x)), 2)),
            avg_review_score=("review_score", lambda x: round(float(np.nanmean(x)), 2) if len(x.dropna()) > 0 else 0.0),
        )
        .reset_index()
    )

    comp = pd.merge(df_sql, py_seller, on="seller_id", suffixes=("_sql", "_python"))
    comp["order_diff"] = comp["total_orders_sql"] - comp["total_orders_python"]
    comp["sales_diff"] = (comp["total_sales_sql"] - comp["total_sales_python"]).round(2)
    comp["review_diff"] = (comp["avg_review_score_sql"] - comp["avg_review_score_python"]).round(2)

    max_order_diff = int(comp["order_diff"].abs().max())
    max_sales_diff = float(comp["sales_diff"].abs().max())
    max_review_diff = float(comp["review_diff"].abs().max())

    passed = (max_order_diff <= TOLERANCE_ABSOLUTE_COUNT) and (max_sales_diff <= TOLERANCE_FINANCIAL_ABS) and (max_review_diff <= TOLERANCE_RATIO_ABS)

    return {
        "test_name": "Seller KPIs (Orders, Sales, Reviews)",
        "passed": passed,
        "max_order_drift": max_order_diff,
        "max_sales_drift": max_sales_diff,
        "max_review_score_drift": max_review_diff,
        "sellers_evaluated": len(comp),
        "discrepancies": comp[(comp["order_diff"] != 0) | (comp["sales_diff"].abs() > TOLERANCE_FINANCIAL_ABS)].to_dict(orient="records"),
        "comparison_sample": comp.head(10).to_dict(orient="records"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-layer computational validation (SQL vs. Python).")
    parser.add_argument("--db-file", type=Path, default=DB_PATH)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DATA_DIR)
    parser.add_argument("--queries-dir", type=Path, default=QUERIES_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(args.db_file))

    print("=== Starting Cross-Layer Computational Validation ===")

    print("1. Running Order Status Categorical Distribution Parity Check...")
    test1 = validate_order_status_distribution(con, args.processed_dir, args.queries_dir)
    print(f"   Status: {'PASSED' if test1['passed'] else 'FAILED'} (Max drift: {test1['max_absolute_drift']})")

    print("2. Running Monthly Revenue & Volume Parity Check...")
    test2 = validate_monthly_revenue(con, args.processed_dir, args.queries_dir)
    print(f"   Status: {'PASSED' if test2['passed'] else 'FAILED'} (Max rev drift: ${test2['max_revenue_drift']})")

    print("3. Running Seller KPIs Multi-Join Parity Check...")
    test3 = validate_seller_kpis(con, args.processed_dir, args.queries_dir)
    print(f"   Status: {'PASSED' if test3['passed'] else 'FAILED'} (Max sales drift: ${test3['max_sales_drift']})")

    con.close()

    all_passed = test1["passed"] and test2["passed"] and test3["passed"]

    report = {
        "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "PASSED" if all_passed else "FAILED",
        "tolerance_specifications": {
            "count_tolerance": TOLERANCE_ABSOLUTE_COUNT,
            "financial_amount_tolerance": TOLERANCE_FINANCIAL_ABS,
            "ratio_tolerance": TOLERANCE_RATIO_ABS,
        },
        "tests": [test1, test2, test3],
        "drift_mitigation_guidance": [
            "Cardianlity Multiplicity: Always pre-aggregate payments and reviews before joining to orders to avoid duplicated transaction sums.",
            "NULL vs NaN: SQL SUM ignores NULL while Python nan/None requires explicit .fillna(0.0) or np.nansum.",
            "Date Truncation: Use consistent string slicing (YYYY-MM) across both SQL strftime and Python str.slice.",
            "Status Inclusion: Verify delivered vs. canceled status filters are identically implemented.",
        ],
    }

    report_path = args.output_dir / "cross_layer_validation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Also output comparison CSVs for audit inspection
    pd.DataFrame(test1["comparison_sample"]).to_csv(args.output_dir / "order_status_comparison.csv", index=False)
    pd.DataFrame(test2["comparison_sample"]).to_csv(args.output_dir / "monthly_revenue_comparison.csv", index=False)
    pd.DataFrame(test3["comparison_sample"]).to_csv(args.output_dir / "seller_kpis_comparison.csv", index=False)

    print(f"\nComprehensive cross-layer audit report exported to {report_path}")
    print(f"Overall Cross-Layer Validation: {'SUCCESS' if all_passed else 'FAILURE'}")

    if not all_passed:
        raise ValueError("Computation drift detected exceeding configured tolerance thresholds!")


if __name__ == "__main__":
    main()
