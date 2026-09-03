"""Enforce explicit pandas dtypes for the processed Olist datasets.

This script reads CSV files from ``data/processed`` and replaces each source
CSV with a newly generated, type-enforced CSV after validation succeeds.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output"
TYPE_LOG_PATH = OUTPUT_DIR / "type_conversion_log.csv"
DTYPE_REPORT_PATH = OUTPUT_DIR / "dtype_conversion_report.csv"
TYPE_SCHEMA_PATH = OUTPUT_DIR / "type_schema.json"

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

DATASET_DATE_COLUMNS = {
    "olist_orders_dataset.csv": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "olist_order_items_dataset.csv": ["shipping_limit_date"],
    "olist_order_reviews_dataset.csv": [
        "review_creation_date",
        "review_answer_timestamp",
    ],
}

DATE_FORMATS = {
    "order_estimated_delivery_date": DATE_FORMAT,
}
CURRENCY_PREFIX_PATTERN = re.compile(
    r"^(?:R\$|US\$|USD|BRL|EUR|€|£|\$)\s*", re.IGNORECASE
)

DATASET_CURRENCY_COLUMNS = {
    "olist_order_items_dataset.csv": ["price", "freight_value"],
    "olist_order_payments_dataset.csv": ["payment_value"],
}

DATASET_BOOLEAN_COLUMNS = {
    "olist_orders_dataset.csv": [
        "order_approved_at_missing",
        "order_delivered_carrier_date_missing",
        "order_delivered_customer_date_missing",
    ],
    "olist_products_dataset.csv": [
        "product_category_name_missing",
        "product_name_lenght_missing",
        "product_description_lenght_missing",
        "product_photos_qty_missing",
        "product_weight_g_missing",
        "product_length_cm_missing",
        "product_height_cm_missing",
        "product_width_cm_missing",
    ],
    "olist_order_reviews_dataset.csv": [
        "review_comment_title_missing",
        "review_comment_message_missing",
    ],
}

DATASET_TYPE_MAPPINGS = {
    "olist_customers_dataset.csv": {
        "customer_id": "string",
        "customer_unique_id": "string",
        "customer_zip_code_prefix": "string",
        "customer_city": "string",
        "customer_state": "string",
    },
    "olist_geolocation_dataset.csv": {
        "geolocation_zip_code_prefix": "string",
        "geolocation_lat": "Float64",
        "geolocation_lng": "Float64",
        "geolocation_city": "string",
        "geolocation_state": "string",
    },
    "olist_order_items_dataset.csv": {
        "order_id": "string",
        "order_item_id": "Int64",
        "product_id": "string",
        "seller_id": "string",
        "price": "Float64",
        "freight_value": "Float64",
    },
    "olist_order_payments_dataset.csv": {
        "order_id": "string",
        "payment_sequential": "Int64",
        "payment_type": "string",
        "payment_installments": "Int64",
        "payment_value": "Float64",
    },
    "olist_order_reviews_dataset.csv": {
        "review_id": "string",
        "order_id": "string",
        "review_score": "Int64",
        "review_comment_title": "string",
        "review_comment_message": "string",
    },
    "olist_orders_dataset.csv": {
        "order_id": "string",
        "customer_id": "string",
        "order_status": "string",
    },
    "olist_products_dataset.csv": {
        "product_id": "string",
        "product_category_name": "string",
        "product_category_name_analysis": "string",
        "product_name_lenght": "Float64",
        "product_description_lenght": "Float64",
        "product_photos_qty": "Float64",
        "product_weight_g": "Float64",
        "product_length_cm": "Float64",
        "product_height_cm": "Float64",
        "product_width_cm": "Float64",
    },
    "olist_sellers_dataset.csv": {
        "seller_id": "string",
        "seller_zip_code_prefix": "string",
        "seller_city": "string",
        "seller_state": "string",
    },
    "product_category_name_translation.csv": {
        "product_category_name": "string",
        "product_category_name_english": "string",
    },
}


def cast_columns_to_types(
    df: pd.DataFrame, type_mapping: dict[str, str]
) -> tuple[pd.DataFrame, dict[str, dict[str, str]]]:
    """Explicitly cast mapped columns and return a per-column conversion log."""
    df_typed = df.copy()
    conversion_log: dict[str, dict[str, str]] = {}

    for col, target_dtype in type_mapping.items():
        if col not in df.columns:
            print(f"Warning: Column {col} not found in DataFrame")
            continue

        original_dtype = df[col].dtype
        try:
            df_typed[col] = df_typed[col].astype(target_dtype)
            conversion_log[col] = {
                "from": str(original_dtype),
                "to": str(target_dtype),
                "status": "success",
            }
            print(f"✓ {col}: {original_dtype} -> {target_dtype}")
        except Exception as exc:
            conversion_log[col] = {
                "from": str(original_dtype),
                "to": str(target_dtype),
                "status": "failed",
                "error": str(exc),
            }
            print(f"✗ {col}: Conversion failed - {exc}")
            raise

    return df_typed, conversion_log


def convert_string_dates_to_datetime(
    df: pd.DataFrame, date_columns: list[str], date_format: str | None = None
) -> pd.DataFrame:
    """Convert date columns using an explicit format when supplied."""
    df_typed = df.copy()
    for col in date_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue
        try:
            df_typed[col] = pd.to_datetime(df_typed[col], format=date_format)
            print(f"✓ {col}: Converted to datetime using {date_format}")
        except Exception as exc:
            print(f"✗ {col}: Conversion failed - {exc}")
            print(f"  Sample values: {df[col].head(3).tolist()}")
            print(f"  Expected format: {date_format}")
            raise
    return df_typed


def _normalize_currency_value(value: object) -> object:
    """Normalize common currency prefixes and decimal conventions.

    Supports values such as ``$1,250.75``, ``R$ 1.250,75``, and ``EUR 12.50``.
    Ambiguous single separators are treated as decimal separators unless exactly
    three trailing digits indicate a thousands separator.
    """
    if pd.isna(value):
        return value
    text = str(value).strip()
    text = CURRENCY_PREFIX_PATTERN.sub("", text)
    text = text.replace(" ", "")
    comma_pos, dot_pos = text.rfind(","), text.rfind(".")
    if comma_pos >= 0 and dot_pos >= 0:
        if comma_pos > dot_pos:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif comma_pos >= 0:
        fractional_digits = len(text) - comma_pos - 1
        text = text.replace(",", ".") if fractional_digits != 3 else text.replace(",", "")
    elif text.count(".") > 1:
        text = text.replace(".", "")
    return text


def convert_currency_to_float(df: pd.DataFrame, currency_columns: list[str]) -> pd.DataFrame:
    """Normalize common currency formats and convert columns to Float64."""
    df_typed = df.copy()
    for col in currency_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue
        try:
            original_nulls = int(df[col].isna().sum())
            cleaned = df_typed[col].map(_normalize_currency_value)
            converted = pd.to_numeric(cleaned, errors="coerce").astype("Float64")
            df_typed[col] = converted
            failed = max(0, int(df_typed[col].isna().sum()) - original_nulls)
            if failed > 0:
                print(f"⚠ {col}: {failed} values could not be converted")
            print(f"✓ {col}: Normalized currency and converted to Float64")
        except Exception as exc:
            print(f"✗ {col}: Conversion failed - {exc}")
            raise
    return df_typed


def convert_integers_to_boolean(df: pd.DataFrame, boolean_columns: list[str]) -> pd.DataFrame:
    """Convert common binary representations to pandas nullable boolean."""
    df_typed = df.copy()
    mapping: dict[Any, bool] = {
        "yes": True, "no": False, "y": True, "n": False,
        "true": True, "false": False, "1": True, "0": False,
        1: True, 0: False,
    }

    for col in boolean_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue
        unique_values = df[col].dropna().unique()
        sample_values = list(unique_values[:5])
        print(
            f"  {col} unique values sample: {sample_values}"
            f" ({len(unique_values)} total)"
        )
        if pd.api.types.is_bool_dtype(df[col]):
            converted = df_typed[col].astype("boolean")
        elif pd.api.types.is_numeric_dtype(df[col]):
            converted = df_typed[col].map({0: False, 1: True}).astype("boolean")
        else:
            normalized = df_typed[col].astype("string").str.strip().str.lower()
            converted = normalized.map(mapping).astype("boolean")
        df_typed[col] = converted
        print(f"✓ {col}: Converted to boolean")
    return df_typed


def compare_dtypes(
    df_original: pd.DataFrame,
    df_typed: pd.DataFrame,
    dataset: str | None = None,
) -> pd.DataFrame:
    """Return an in-memory before-and-after dtype comparison."""
    comparison = pd.DataFrame({
        "column": df_original.columns,
        "dtype_before": df_original.dtypes.astype(str).values,
        "dtype_after": df_typed.dtypes.astype(str).values,
        "changed": (df_original.dtypes != df_typed.dtypes).values,
    })
    if dataset is not None:
        comparison.insert(0, "dataset", dataset)
    return comparison


def _conversion_rows(
    dataset: str, before: pd.DataFrame, after: pd.DataFrame
) -> list[dict[str, Any]]:
    """Build audit rows for every column in one dataset."""
    rows = []
    for col in before.columns:
        rows.append({
            "dataset": dataset,
            "column": col,
            "dtype_before": str(before[col].dtype),
            "dtype_after": str(after[col].dtype),
            "changed": bool(before[col].dtype != after[col].dtype),
            "status": "success",
        })
    return rows


def _validate_frame(original: pd.DataFrame, typed: pd.DataFrame) -> None:
    """Validate structural invariants before replacing the source CSV."""
    if len(original) != len(typed):
        raise ValueError("Row count changed during type enforcement")
    if list(original.columns) != list(typed.columns):
        raise ValueError("Column list changed during type enforcement")


def process_dataset(
    csv_path: Path, df_original: pd.DataFrame
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Convert one already-loaded processed CSV and return audit rows."""
    df_original = pd.read_csv(csv_path, dtype_backend="numpy_nullable")
    df_typed = df_original.copy()
    date_columns = [
        col for col in DATASET_DATE_COLUMNS.get(csv_path.name, [])
        if col in df_original.columns
    ]
    timestamp_columns = [col for col in date_columns if col not in DATE_FORMATS]
    if timestamp_columns:
        df_typed = convert_string_dates_to_datetime(
            df_typed, timestamp_columns, date_format=TIMESTAMP_FORMAT
        )
    for col, format_for_column in DATE_FORMATS.items():
        if col in date_columns:
            df_typed = convert_string_dates_to_datetime(
                df_typed, [col], date_format=format_for_column
            )
    df_typed = convert_currency_to_float(
        df_typed, DATASET_CURRENCY_COLUMNS.get(csv_path.name, [])
    )
    df_typed = convert_integers_to_boolean(
        df_typed, DATASET_BOOLEAN_COLUMNS.get(csv_path.name, [])
    )

    mapping = DATASET_TYPE_MAPPINGS.get(csv_path.name, {})
    df_typed, cast_log = cast_columns_to_types(df_typed, mapping)

    _validate_frame(df_original, df_typed)
    rows = _conversion_rows(csv_path.name, df_original, df_typed)
    for row in rows:
        cast_entry = cast_log.get(row["column"])
        if cast_entry is not None:
            row["status"] = cast_entry["status"]
            if "error" in cast_entry:
                row["error"] = cast_entry["error"]
    return df_typed, rows


def replace_csv(csv_path: Path, df_typed: pd.DataFrame) -> None:
    """Atomically replace the original CSV with a validated temporary CSV."""
    temporary_path = csv_path.with_name(f".{csv_path.name}.typed.tmp")
    df_typed.to_csv(temporary_path, index=False)
    temporary_path.replace(csv_path)


def main() -> None:
    """Replace every processed CSV with its type-enforced equivalent."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_files = sorted(PROCESSED_DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {PROCESSED_DATA_DIR}")

    audit_rows: list[dict[str, Any]] = []
    dtype_reports: list[pd.DataFrame] = []
    type_schema: dict[str, dict[str, str]] = {}
    for csv_path in csv_files:
        print(f"\nProcessing {csv_path.name}...")
        df_original = pd.read_csv(csv_path, dtype_backend="numpy_nullable")
        df_typed, rows = process_dataset(csv_path, df_original)
        audit_rows.extend(rows)
        dtype_reports.append(compare_dtypes(df_original, df_typed, csv_path.name))
        type_schema[csv_path.name] = {
            column: str(dtype) for column, dtype in df_typed.dtypes.items()
        }
        replace_csv(csv_path, df_typed)
        print(f"✓ Atomically replaced {csv_path}")

    pd.DataFrame(audit_rows).to_csv(TYPE_LOG_PATH, index=False)
    if dtype_reports:
        pd.concat(dtype_reports, ignore_index=True).to_csv(DTYPE_REPORT_PATH, index=False)
    with (OUTPUT_DIR / "type_conversion_log.json").open("w", encoding="utf-8") as handle:
        json.dump(audit_rows, handle, indent=2, default=str)
    with TYPE_SCHEMA_PATH.open("w", encoding="utf-8") as handle:
        json.dump(type_schema, handle, indent=2)
    print(f"\n✓ Conversion log saved to {TYPE_LOG_PATH}")
    print(f"✓ Dtype report saved to {DTYPE_REPORT_PATH}")
    print(f"✓ Type schema saved to {TYPE_SCHEMA_PATH}")


if __name__ == "__main__":
    main()
