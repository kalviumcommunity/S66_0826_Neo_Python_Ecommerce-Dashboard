"""Validate multi-source joins for the processed Olist datasets.

The primary integration joins customers to orders on ``customer_id`` using a
validated one-to-one left join. Payment rows are aggregated to order level
before their optional integration so that one-to-many payments cannot create
phantom order rows or double-count revenue. Source CSVs are never modified.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any

import pandas as pd

try:
    dataset_dtypes = import_module("scripts.ingest_data").DATASET_DTYPES
except ModuleNotFoundError:  # Supports direct execution from scripts/
    dataset_dtypes = import_module("ingest_data").DATASET_DTYPES

DATASET_DTYPES = dataset_dtypes

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
INTEGRATED_DATA_DIR = PROCESSED_DATA_DIR / "integrated"
MERGE_OUTPUT_DIR = PROJECT_ROOT / "output" / "merge_validation"

CUSTOMERS_FILE = "olist_customers_dataset.csv"
ORDERS_FILE = "olist_orders_dataset.csv"
PAYMENTS_FILE = "olist_order_payments_dataset.csv"
JOIN_KEY = "customer_id"


def _read_processed(filename: str) -> pd.DataFrame:
    """Read one processed CSV with the project's identifier dtype mapping."""
    path = PROCESSED_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required processed file not found: {path}")
    return pd.read_csv(path, dtype=DATASET_DTYPES.get(filename))


def _key_profile(df: pd.DataFrame, dataset: str, key: str) -> dict[str, Any]:
    """Summarize key quality before a merge."""
    if key not in df.columns:
        raise KeyError(f"Join key {key!r} is missing from {dataset}")
    return {
        "dataset": dataset,
        "key": key,
        "rows": int(len(df)),
        "distinct_keys": int(df[key].nunique(dropna=True)),
        "null_keys": int(df[key].isna().sum()),
        "duplicate_key_rows": int(df[key].duplicated(keep=False).sum()),
        "max_rows_per_key": int(df.groupby(key, dropna=False).size().max())
        if len(df)
        else 0,
        "dtype": str(df[key].dtype),
    }


def _require_compatible_keys(left: pd.DataFrame, right: pd.DataFrame, key: str) -> None:
    """Reject missing or incompatible merge keys before pandas performs a join."""
    if key not in left.columns or key not in right.columns:
        raise KeyError(f"Join key {key!r} must exist in both input tables")
    if str(left[key].dtype) != str(right[key].dtype):
        raise TypeError(
            f"Join key dtype mismatch for {key!r}: "
            f"left={left[key].dtype}, right={right[key].dtype}"
        )


def compare_join_types(
    left: pd.DataFrame,
    right: pd.DataFrame,
    key: str,
    validation: str = "one_to_one",
) -> pd.DataFrame:
    """Compare explicit inner, left, right, and outer join row counts."""
    rows: list[dict[str, Any]] = []
    for join_type in ("inner", "left", "right", "outer"):
        merged = pd.merge(
            left,
            right,
            on=key,
            how=join_type,
            validate=validation,
            indicator=True,
            suffixes=("_left", "_right"),
        )
        rows.append(
            {
                "join_type": join_type,
                "result_rows": int(len(merged)),
                "distinct_join_keys": int(merged[key].nunique(dropna=True)),
                "left_only_rows": int((merged["_merge"] == "left_only").sum()),
                "right_only_rows": int((merged["_merge"] == "right_only").sum()),
                "matched_rows": int((merged["_merge"] == "both").sum()),
            }
        )
    return pd.DataFrame(rows)


def find_unmatched_records(
    left: pd.DataFrame, right: pd.DataFrame, key: str
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Return original left/right records whose keys have no counterpart."""
    right_keys = right[key].dropna().drop_duplicates()
    left_keys = left[key].dropna().drop_duplicates()
    unmatched_left = left.loc[~left[key].isin(right_keys)].copy()
    unmatched_right = right.loc[~right[key].isin(left_keys)].copy()
    counts = {
        "unmatched_left_rows": int(len(unmatched_left)),
        "unmatched_right_rows": int(len(unmatched_right)),
        "unmatched_left_keys": int(unmatched_left[key].nunique(dropna=True)),
        "unmatched_right_keys": int(unmatched_right[key].nunique(dropna=True)),
    }
    return unmatched_left, unmatched_right, counts


def build_payment_totals(payments: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the payment many-side to one row per order."""
    return (
        payments.groupby("order_id", as_index=False, dropna=False)
        .agg(
            total_payment_value=("payment_value", "sum"),
            payment_record_count=("payment_sequential", "count"),
        )
    )


def run_merge_validation() -> dict[str, Any]:
    """Run and report customer/order and order/payment integration checks."""
    customers = _read_processed(CUSTOMERS_FILE)
    orders = _read_processed(ORDERS_FILE)
    payments = _read_processed(PAYMENTS_FILE)
    _require_compatible_keys(customers, orders, JOIN_KEY)

    customer_profile = _key_profile(customers, CUSTOMERS_FILE, JOIN_KEY)
    order_profile = _key_profile(orders, ORDERS_FILE, JOIN_KEY)
    unmatched_customers, orphaned_orders, unmatched_counts = find_unmatched_records(
        customers, orders, JOIN_KEY
    )

    merged = pd.merge(
        customers,
        orders,
        on=JOIN_KEY,
        how="left",
        validate="one_to_one",
        indicator=True,
        suffixes=("_customer", "_order"),
    )
    if len(merged) != len(customers):
        raise AssertionError(
            "The validated one-to-one customer/order left join changed the customer row count"
        )
    duplicate_join_rows = int(merged[JOIN_KEY].duplicated(keep=False).sum())
    if duplicate_join_rows:
        raise AssertionError("Customer/order merge produced duplicate join keys")

    join_comparison = compare_join_types(customers, orders, JOIN_KEY)
    customer_order_output = INTEGRATED_DATA_DIR / "customer_order_view.csv"

    payment_totals = build_payment_totals(payments)
    orders_with_payments = pd.merge(
        orders,
        payment_totals,
        on="order_id",
        how="left",
        validate="one_to_one",
        indicator=True,
        suffixes=("_order", "_payment"),
    )
    payment_orphans = payments.loc[~payments["order_id"].isin(orders["order_id"])].copy()

    MERGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    INTEGRATED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    unmatched_customers.to_csv(
        MERGE_OUTPUT_DIR / "unmatched_customers.csv", index=False, encoding="utf-8"
    )
    orphaned_orders.to_csv(
        MERGE_OUTPUT_DIR / "orphaned_orders.csv", index=False, encoding="utf-8"
    )
    payment_orphans.to_csv(
        MERGE_OUTPUT_DIR / "orphaned_payments.csv", index=False, encoding="utf-8"
    )
    merged.drop(columns="_merge").to_csv(
        customer_order_output, index=False, encoding="utf-8"
    )
    join_comparison.to_csv(
        MERGE_OUTPUT_DIR / "join_type_comparison.csv", index=False, encoding="utf-8"
    )
    pd.DataFrame([customer_profile, order_profile]).to_csv(
        MERGE_OUTPUT_DIR / "key_profile.csv", index=False, encoding="utf-8"
    )
    orders_with_payments.drop(columns="_merge").to_csv(
        INTEGRATED_DATA_DIR / "orders_with_payment_totals.csv",
        index=False,
        encoding="utf-8",
    )

    report: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "primary_join": {
            "join_type": "left",
            "left_table": CUSTOMERS_FILE,
            "right_table": ORDERS_FILE,
            "join_key": [JOIN_KEY],
            "validation": "one_to_one",
            "left_rows": int(len(customers)),
            "right_rows": int(len(orders)),
            "result_rows": int(len(merged)),
            "row_change_from_left": int(len(merged) - len(customers)),
            "duplicate_join_rows": duplicate_join_rows,
            **unmatched_counts,
            "reasoning": (
                "A left join preserves every processed customer record while enriching it "
                "with its matching Olist order record. one_to_one validation prevents silent "
                "row multiplication."
            ),
        },
        "key_profiles": [customer_profile, order_profile],
        "payment_integration": {
            "source_table": PAYMENTS_FILE,
            "aggregation_key": "order_id",
            "payment_rows": int(len(payments)),
            "aggregated_order_rows": int(len(payment_totals)),
            "orphaned_payment_rows": int(len(payment_orphans)),
            "reasoning": (
                "Payments are many-side records, so they are aggregated by order_id before "
                "joining to the order-level table."
            ),
        },
        "outputs": {
            "integrated_data": str(INTEGRATED_DATA_DIR.relative_to(PROJECT_ROOT)),
            "reports": str(MERGE_OUTPUT_DIR.relative_to(PROJECT_ROOT)),
        },
    }
    report_path = MERGE_OUTPUT_DIR / "customer_order_join_report.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, default=str)

    print("\n" + "=" * 70)
    print("MULTI-SOURCE MERGE VALIDATION COMPLETE")
    print("=" * 70)
    print(f"Customers: {len(customers):,}")
    print(f"Orders: {len(orders):,}")
    print(f"Validated left-join result: {len(merged):,}")
    print(f"Unmatched customers: {unmatched_counts['unmatched_left_rows']:,}")
    print(f"Orphaned orders: {unmatched_counts['unmatched_right_rows']:,}")
    print(f"Orphaned payments: {len(payment_orphans):,}")
    print(f"Reports saved to {MERGE_OUTPUT_DIR.relative_to(PROJECT_ROOT)}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run_merge_validation()


if __name__ == "__main__":
    main()
