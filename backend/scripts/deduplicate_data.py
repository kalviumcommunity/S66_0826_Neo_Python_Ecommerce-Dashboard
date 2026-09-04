"""Detect and safely deduplicate Olist processed datasets.

The default workflow removes only confirmed exact duplicate rows from the
geolocation table. Near-duplicate key groups are reported for review because
repeated business keys can be legitimate in Olist's relational tables.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

if __package__:
    from .ingest_data import DATASET_DTYPES
else:  # Direct execution: python scripts/<script>.py
    from ingest_data import DATASET_DTYPES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
DEDUPLICATED_DATA_DIR = PROCESSED_DATA_DIR / "deduplicated"
DEDUP_REPORT_DIR = PROJECT_ROOT / "output" / "deduplication"
AUDIT_PATH = DEDUP_REPORT_DIR / "removed_duplicates_audit.csv"
SUMMARY_PATH = DEDUP_REPORT_DIR / "deduplication_summary.json"
DECISIONS_PATH = DEDUP_REPORT_DIR / "deduplication_decisions.json"
NEAR_DUPLICATE_DIR = DEDUP_REPORT_DIR / "near_duplicates"

# These are candidate uniqueness keys for detection only. A repeated key is
# not automatically an error unless the table grain makes it unique.
NEAR_DUPLICATE_KEYS: dict[str, list[str]] = {
    "olist_customers_dataset.csv": ["customer_id"],
    "olist_order_items_dataset.csv": ["order_id", "order_item_id"],
    "olist_order_payments_dataset.csv": ["order_id", "payment_sequential"],
    "olist_order_reviews_dataset.csv": ["review_id", "order_id"],
    "olist_orders_dataset.csv": ["order_id"],
    "olist_products_dataset.csv": ["product_id"],
    "olist_sellers_dataset.csv": ["seller_id"],
    "product_category_name_translation.csv": ["product_category_name"],
}

# A ZIP prefix can legitimately map to multiple coordinates, cities, and
# spellings, so it is intentionally not used as a near-duplicate key.
EXACT_DEDUPLICATION_DATASETS = {"olist_geolocation_dataset.csv"}


def _percentage(count: int, total: int) -> float:
    """Return a safe rounded percentage."""
    return round(count / total * 100, 2) if total else 0.0


def detect_exact_duplicates(
    df: pd.DataFrame, dataset_name: str = "dataset"
) -> tuple[int, pd.DataFrame]:
    """Find exact duplicate rows and return their count and all group members."""
    duplicate_mask = df.duplicated(keep=False)
    exact_count = int(df.duplicated().sum())
    duplicate_rows = df.loc[duplicate_mask].copy()

    print("\nEXACT DUPLICATE DETECTION")
    print("=" * 60)
    print(f"Dataset: {dataset_name}")
    print(f"Exact duplicates found: {exact_count:,}")
    print(f"Total duplicate rows including originals: {len(duplicate_rows):,}")
    if not duplicate_rows.empty:
        print("\nSample duplicate rows:")
        print(duplicate_rows.head(10).to_string(index=False))
    return exact_count, duplicate_rows


def detect_near_duplicates(
    df: pd.DataFrame, key_columns: list[str], dataset_name: str = "dataset"
) -> tuple[pd.DataFrame, int]:
    """Find rows sharing a configured key and return rows plus group count."""
    missing_columns = [column for column in key_columns if column not in df.columns]
    if missing_columns:
        raise KeyError(f"Near-duplicate keys missing from {dataset_name}: {missing_columns}")

    duplicate_mask = df.duplicated(subset=key_columns, keep=False)
    duplicate_rows = df.loc[duplicate_mask].copy()
    group_count = int(duplicate_rows.groupby(key_columns, dropna=False).ngroups)

    print("\nNEAR-DUPLICATE DETECTION")
    print("=" * 60)
    print(f"Dataset: {dataset_name}")
    print(f"Key columns: {key_columns}")
    print(f"Records with duplicate keys: {len(duplicate_rows):,}")
    print(f"Unique key combinations with duplicates: {group_count:,}")
    return duplicate_rows, group_count


def remove_exact_duplicates(
    df: pd.DataFrame, keep: str = "first"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Remove exact duplicates and return the result plus removed source rows."""
    if keep not in {"first", "last"}:
        raise ValueError("Exact deduplication supports keep='first' or keep='last'.")

    rows_before = len(df)
    kept_mask = ~df.duplicated(keep=keep)
    deduplicated = df.loc[kept_mask].copy()
    removed = df.loc[~kept_mask].copy()

    print("\nEXACT DUPLICATE REMOVAL")
    print("=" * 60)
    print(f"Keep strategy: {keep}")
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {len(deduplicated):,}")
    print(
        f"Rows removed: {len(removed):,} "
        f"({_percentage(len(removed), rows_before):.2f}%)"
    )
    return deduplicated, removed


def remove_near_duplicates(
    df: pd.DataFrame,
    key_columns: list[str],
    keep_strategy: str = "most_complete",
) -> pd.DataFrame:
    """Remove near duplicates when explicitly requested by a caller.

    The default workflow does not call this function. It is available for a
    reviewed table/key configuration and keeps the original index for audit.
    """
    if keep_strategy not in {"most_complete", "first", "last"}:
        raise ValueError("keep_strategy must be most_complete, first, or last")
    if keep_strategy == "most_complete":
        completeness = df.notna().sum(axis=1)
        order = df.assign(_completeness=completeness).sort_values(
            key_columns + ["_completeness"], ascending=[True] * len(key_columns) + [False]
        )
        return order.drop_duplicates(subset=key_columns, keep="first").drop(
            columns="_completeness"
        )
    return df.drop_duplicates(subset=key_columns, keep=keep_strategy).copy()


def log_removed_duplicates(
    df_original: pd.DataFrame,
    df_kept: pd.DataFrame,
    removed_records: pd.DataFrame,
    dataset_name: str,
    reason: str = "exact_duplicate_keep_first",
) -> pd.DataFrame:
    """Add audit metadata, including the source row retained for each duplicate."""
    if removed_records.empty:
        return pd.DataFrame()

    original_hashes = pd.util.hash_pandas_object(df_original, index=False)
    kept_hashes = pd.util.hash_pandas_object(df_kept, index=False)
    kept_row_by_hash = pd.Series(df_kept.index.to_numpy(), index=kept_hashes).to_dict()
    removed_hashes = original_hashes.loc[removed_records.index]
    kept_row_numbers = removed_hashes.map(kept_row_by_hash).astype(int)

    audit_records = removed_records.copy()
    audit_records.insert(0, "dataset", dataset_name)
    audit_records.insert(1, "source_row_number", audit_records.index.astype(int))
    audit_records.insert(2, "kept_source_row_number", kept_row_numbers.to_numpy())
    audit_records.insert(3, "removal_reason", reason)
    audit_records.insert(4, "removal_timestamp", datetime.now(timezone.utc).isoformat())
    return audit_records.reset_index(drop=True)


def compare_before_after(
    df_original: pd.DataFrame,
    df_deduplicated: pd.DataFrame,
    dataset_name: str,
    exact_duplicates_before: int,
    near_duplicate_records: int = 0,
    near_duplicate_groups: int = 0,
) -> dict[str, Any]:
    """Create before/after metrics for one dataset."""
    rows_before = len(df_original)
    rows_after = len(df_deduplicated)
    return {
        "dataset": dataset_name,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_removed": rows_before - rows_after,
        "removal_percentage": _percentage(rows_before - rows_after, rows_before),
        "columns_before": len(df_original.columns),
        "columns_after": len(df_deduplicated.columns),
        "nulls_before": int(df_original.isna().sum().sum()),
        "nulls_after": int(df_deduplicated.isna().sum().sum()),
        "exact_duplicates_before": exact_duplicates_before,
        "exact_duplicates_after": int(df_deduplicated.duplicated().sum()),
        "near_duplicate_records_reported": near_duplicate_records,
        "near_duplicate_groups_reported": near_duplicate_groups,
        "deduplication_applied": rows_before != rows_after,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _load_dataset(input_path: Path) -> pd.DataFrame:
    """Load a processed dataset while preserving configured identifiers."""
    return pd.read_csv(input_path, dtype=DATASET_DTYPES.get(input_path.name))


def process_dataset(input_path: Path, detect_only: bool = False) -> tuple[dict[str, Any], pd.DataFrame]:
    """Detect duplicates and optionally remove configured exact duplicates."""
    dataset_name = input_path.name
    original = _load_dataset(input_path)
    exact_count, _ = detect_exact_duplicates(original, dataset_name)

    deduplicated = original.copy()
    removed = pd.DataFrame()
    if not detect_only and dataset_name in EXACT_DEDUPLICATION_DATASETS:
        deduplicated, removed = remove_exact_duplicates(original, keep="first")

    near_rows = pd.DataFrame()
    near_groups = 0
    key_columns = NEAR_DUPLICATE_KEYS.get(dataset_name)
    if key_columns:
        near_rows, near_groups = detect_near_duplicates(
            deduplicated, key_columns, dataset_name
        )
        if not near_rows.empty:
            near_rows = near_rows.copy()
            near_rows.insert(0, "source_row_number", near_rows.index.astype(int))
            near_rows.insert(0, "dataset", dataset_name)
            NEAR_DUPLICATE_DIR.mkdir(parents=True, exist_ok=True)
            near_rows.to_csv(
                NEAR_DUPLICATE_DIR / f"{input_path.stem}_near_duplicates.csv",
                index=False,
                encoding="utf-8",
            )

    if not detect_only and dataset_name in EXACT_DEDUPLICATION_DATASETS:
        DEDUPLICATED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        deduplicated.to_csv(
            DEDUPLICATED_DATA_DIR / dataset_name,
            index=False,
            encoding="utf-8",
        )

    comparison = compare_before_after(
        original,
        deduplicated,
        dataset_name,
        exact_count,
        len(near_rows),
        near_groups,
    )
    comparison["input"] = str(input_path.relative_to(PROJECT_ROOT))
    if not detect_only and dataset_name in EXACT_DEDUPLICATION_DATASETS:
        comparison["output"] = str(
            (DEDUPLICATED_DATA_DIR / dataset_name).relative_to(PROJECT_ROOT)
        )
    else:
        comparison["output"] = None
    comparison["near_duplicate_keys"] = key_columns

    audit_records = log_removed_duplicates(
        original, deduplicated, removed, dataset_name
    )
    return comparison, audit_records


def run_deduplication(
    input_dir: str | Path = PROCESSED_DATA_DIR,
    detect_only: bool = False,
) -> dict[str, Any]:
    """Run duplicate detection across all processed CSV files."""
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Processed data directory not found: {input_dir}")

    csv_files = sorted(input_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No processed CSV files found in {input_dir}")

    summaries: list[dict[str, Any]] = []
    audit_parts: list[pd.DataFrame] = []
    decisions: list[dict[str, Any]] = []
    for input_path in csv_files:
        comparison, audit_records = process_dataset(input_path, detect_only=detect_only)
        summaries.append(comparison)
        if not audit_records.empty:
            audit_parts.append(audit_records)
        decisions.append(
            {
                "dataset": input_path.name,
                "exact_strategy": (
                    "detect_only"
                    if detect_only
                    else (
                        "keep_first"
                        if input_path.name in EXACT_DEDUPLICATION_DATASETS
                        else "report_only"
                    )
                ),
                "near_duplicate_strategy": "report_only",
                "business_reasoning": (
                    "Exact duplicate geolocation rows are redundant; repeated ZIP prefixes "
                    "are not removed because they can represent legitimate coordinates or cities."
                    if input_path.name == "olist_geolocation_dataset.csv"
                    else "Repeated business keys require table-specific review before removal."
                ),
            }
        )

    audit = pd.concat(audit_parts, ignore_index=True) if audit_parts else pd.DataFrame()
    if not audit.empty:
        audit.to_csv(AUDIT_PATH, index=False, encoding="utf-8")
    elif AUDIT_PATH.exists():
        AUDIT_PATH.unlink()

    summary = {
        "input_directory": str(input_dir.relative_to(PROJECT_ROOT)),
        "deduplicated_output_directory": str(
            DEDUPLICATED_DATA_DIR.relative_to(PROJECT_ROOT)
        ),
        "detect_only": detect_only,
        "dataset_count": len(summaries),
        "total_rows_removed": int(sum(item["rows_removed"] for item in summaries)),
        "audit_file": str(AUDIT_PATH.relative_to(PROJECT_ROOT)) if not audit.empty else None,
        "datasets": summaries,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    DEDUP_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with SUMMARY_PATH.open("w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, indent=2, allow_nan=False)
    with DECISIONS_PATH.open("w", encoding="utf-8") as decisions_file:
        json.dump(decisions, decisions_file, indent=2, allow_nan=False)

    return summary


def main() -> None:
    """Run the safe default deduplication workflow."""
    print("\n" + "=" * 70)
    print("STARTING OLIST DEDUPLICATION WORKFLOW")
    print("=" * 70)
    summary = run_deduplication()
    print("\n" + "=" * 70)
    print("DEDUPLICATION FINAL SUMMARY")
    print("=" * 70)
    print(f"Datasets analyzed: {summary['dataset_count']}")
    print(f"Total rows removed: {summary['total_rows_removed']:,}")
    print(f"Audit file: {summary['audit_file'] or 'No rows removed'}")
    print(f"Summary: {SUMMARY_PATH.relative_to(PROJECT_ROOT)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
