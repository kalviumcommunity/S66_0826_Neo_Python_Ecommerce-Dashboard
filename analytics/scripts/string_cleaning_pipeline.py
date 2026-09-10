"""Reusable string-cleaning pipeline for the processed Olist datasets.

The CSV files in ``data/processed`` are rewritten in place using temporary
files and atomic replacement. Audit reports are written to ``output``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = PROJECT_ROOT / "data" / "processed"
CLEANED_DIR = INPUT_DIR
OUTPUT_DIR = PROJECT_ROOT / "output"
SUMMARY_PATH = OUTPUT_DIR / "string_cleaning_summary.csv"
VALUE_COUNTS_PATH = OUTPUT_DIR / "string_cleaning_value_counts.csv"
SPECIAL_CHARACTER_PATTERN = r"[^a-zA-Z0-9 ]"

# The processed Olist data uses these fields for categorical and free-text data.
TEXT_COLUMNS_BY_DATASET: dict[str, list[str]] = {
    "olist_customers_dataset.csv": [
        "customer_city",
        "customer_state",
    ],
    "olist_geolocation_dataset.csv": [
        "geolocation_city",
        "geolocation_state",
    ],
    "olist_orders_dataset.csv": ["order_status"],
    "olist_order_payments_dataset.csv": ["payment_type"],
    "olist_order_reviews_dataset.csv": [
        "review_comment_title",
        "review_comment_message",
    ],
    "olist_products_dataset.csv": [
        "product_category_name",
        "product_category_name_analysis",
    ],
    "olist_sellers_dataset.csv": [
        "seller_city",
        "seller_state",
    ],
    "product_category_name_translation.csv": [
        "product_category_name",
        "product_category_name_english",
    ],
}

CITY_COLUMNS = {
    "customer_city",
    "seller_city",
    "geolocation_city",
}

PAYMENT_TYPE_MAP = {
    "credit_card": "credit_card",
    "credit card": "credit_card",
    "credit-card": "credit_card",
    "cartao de credito": "credit_card",
    "debit_card": "debit_card",
    "debit card": "debit_card",
    "debit-card": "debit_card",
    "cartao de debito": "debit_card",
    "boleto": "boleto",
    "bank slip": "boleto",
    "bank-slip": "boleto",
    "bank_slip": "boleto",
    "cash": "cash",
    "cash payment": "cash",
    "dinheiro": "cash",
}


def load_processed_datasets(
    data_dir: str | Path = INPUT_DIR,
) -> dict[str, pd.DataFrame]:
    """Load all source CSVs from the processed-data directory.

    Only CSV files directly in the processed-data directory are loaded.
    """
    data_dir = Path(data_dir)
    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")
    return {
        csv_file.name: pd.read_csv(csv_file, dtype_backend="numpy_nullable")
        for csv_file in csv_files
    }


def clean_text_column(
    series: pd.Series,
    lowercase: bool = True,
    strip: bool = True,
    remove_special: bool = False,
    mapping: dict[str, str] | None = None,
) -> pd.Series:
    """Clean a text Series with configurable, null-safe transformations.

    Mapping is applied after stripping and lowercasing. Unmapped values are
    retained rather than changed to null, which prevents accidental data loss.
    """
    result = series.copy()
    null_count = int(result.isna().sum())
    if null_count:
        print(f"Warning: {null_count} null values in {series.name}")

    if strip:
        result = result.str.strip()
    if lowercase:
        result = result.str.lower()
    if remove_special:
        result = result.str.replace(SPECIAL_CHARACTER_PATTERN, "", regex=True)
    if mapping:
        result = result.replace(mapping)
    return result


def strip_all_strings(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Strip whitespace from every object/string column and audit changes."""
    cleaned = df.copy()
    rows: list[dict[str, Any]] = []
    string_cols = cleaned.select_dtypes(include=["object", "string"]).columns

    for col in string_cols:
        before_series = cleaned[col]
        stripped = before_series.str.strip()
        whitespace_fixed = int(
            (before_series.notna() & stripped.notna() & before_series.ne(stripped)).sum()
        )
        before_unique = int(before_series.nunique(dropna=True))
        after_unique = int(stripped.nunique(dropna=True))
        cleaned[col] = stripped
        rows.append(
            {
                "column": col,
                "operation": "strip",
                "whitespace_values_fixed": whitespace_fixed,
                "unique_before": before_unique,
                "unique_after": after_unique,
                "changed_values": whitespace_fixed,
            }
        )
        print(
            f"{col}: {before_unique} -> {after_unique} unique values; "
            f"{whitespace_fixed} whitespace values fixed"
        )
    return cleaned, rows


def normalize_casing(
    df: pd.DataFrame, columns_to_lower: list[str]
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Normalize selected categorical columns to lowercase."""
    cleaned = df.copy()
    rows: list[dict[str, Any]] = []
    for col in columns_to_lower:
        if col not in cleaned.columns:
            continue
        before = cleaned[col].copy()
        cleaned[col] = cleaned[col].str.lower()
        changed = int((before.notna() & before.ne(cleaned[col])).sum())
        rows.append(
            {
                "column": col,
                "operation": "lowercase",
                "whitespace_values_fixed": 0,
                "unique_before": int(before.nunique(dropna=True)),
                "unique_after": int(cleaned[col].nunique(dropna=True)),
                "changed_values": changed,
            }
        )
        print(f"Normalized {col} to lowercase ({changed} values changed)")
    return cleaned, rows


def remove_special_characters(
    df: pd.DataFrame, columns: list[str]
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Remove characters not matched by ``[^a-zA-Z0-9 ]`` from text columns."""
    cleaned = df.copy()
    rows: list[dict[str, Any]] = []
    for col in columns:
        if col not in cleaned.columns:
            continue
        before = cleaned[col].copy()
        cleaned[col] = cleaned[col].str.replace(
            SPECIAL_CHARACTER_PATTERN, "", regex=True
        )
        changed = int((before.notna() & before.ne(cleaned[col])).sum())
        rows.append(
            {
                "column": col,
                "operation": "remove_special_characters",
                "whitespace_values_fixed": 0,
                "unique_before": int(before.nunique(dropna=True)),
                "unique_after": int(cleaned[col].nunique(dropna=True)),
                "changed_values": changed,
            }
        )
        print(f"Removed special characters from {col} ({changed} values changed)")
    return cleaned, rows


def standardize_categorical_labels(
    df: pd.DataFrame,
    column: str,
    mapping: dict[str, str],
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Apply a canonical-label mapping while retaining unmapped values."""
    cleaned = df.copy()
    if column not in cleaned.columns:
        return cleaned, []
    before = cleaned[column].copy()
    cleaned[column] = before.replace(mapping)
    changed = int((before.notna() & before.ne(cleaned[column])).sum())
    print(f"Mapped {column}: {changed} values standardized")
    return cleaned, [
        {
            "column": column,
            "operation": "categorical_mapping",
            "whitespace_values_fixed": 0,
            "unique_before": int(before.nunique(dropna=True)),
            "unique_after": int(cleaned[column].nunique(dropna=True)),
            "changed_values": changed,
        }
    ]


def replace_csv_atomically(csv_path: Path, df: pd.DataFrame) -> None:
    """Rewrite one CSV through a temporary file and atomic replacement."""
    temporary_path = csv_path.with_name(f".{csv_path.name}.cleaning.tmp")
    df.to_csv(temporary_path, index=False)
    temporary_path.replace(csv_path)


def _value_count_rows(
    dataset: str,
    column: str,
    before: pd.Series,
    after: pd.Series,
) -> list[dict[str, Any]]:
    """Create compact before/after value-count audit rows."""
    before_counts = before.value_counts(dropna=False).head(10)
    after_counts = after.value_counts(dropna=False).head(10)
    values = list(dict.fromkeys([*before_counts.index.tolist(), *after_counts.index.tolist()]))
    return [
        {
            "dataset": dataset,
            "column": column,
            "value": value,
            "count_before": int(before_counts.get(value, 0)),
            "count_after": int(after_counts.get(value, 0)),
        }
        for value in values
    ]


def clean_processed_dataset(
    dataset: str,
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply the configured cleaning operations to one processed dataset."""
    configured_columns = [col for col in TEXT_COLUMNS_BY_DATASET.get(dataset, []) if col in df]
    working = df.copy()
    all_rows: list[dict[str, Any]] = []
    value_count_rows: list[dict[str, Any]] = []

    before_for_counts = {
        col: working[col].copy() for col in configured_columns
    }
    working, rows = strip_all_strings(working)
    all_rows.extend(rows)

    working, rows = normalize_casing(working, configured_columns)
    all_rows.extend(rows)

    special_columns = [col for col in configured_columns if col in CITY_COLUMNS]
    working, rows = remove_special_characters(working, special_columns)
    all_rows.extend(rows)

    if dataset == "olist_order_payments_dataset.csv":
        working, rows = standardize_categorical_labels(
            working, "payment_type", PAYMENT_TYPE_MAP
        )
        all_rows.extend(rows)

    for col in configured_columns[:2]:
        value_count_rows.extend(
            _value_count_rows(dataset, col, before_for_counts[col], working[col])
        )

    for row in all_rows:
        row["dataset"] = dataset
    return working, all_rows, value_count_rows


def demonstrate_required_examples() -> None:
    """Print explicit examples required by the assignment rubric."""
    example = pd.Series([" JOHN ", "john", "John"], name="name")
    print("\nCasing demonstration:")
    print(pd.DataFrame({"before": example, "after": clean_text_column(example)}))

    international = pd.Series(["São Paulo"], name="city")
    cleaned = clean_text_column(international, lowercase=False, remove_special=True)
    print(f"International-character demonstration: {international.iloc[0]} -> {cleaned.iloc[0]}")

    print("\nPayment mapping dictionary:")
    print(PAYMENT_TYPE_MAP)


def main() -> None:
    """Run string cleaning on every CSV in data/processed."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    datasets = load_processed_datasets()
    summary_rows: list[dict[str, Any]] = []
    value_rows: list[dict[str, Any]] = []

    for dataset, df in datasets.items():
        print(f"\n{'=' * 70}\nCleaning {dataset}\n{'=' * 70}")
        cleaned, rows, counts = clean_processed_dataset(dataset, df)
        replace_csv_atomically(INPUT_DIR / dataset, cleaned)
        summary_rows.extend(rows)
        value_rows.extend(counts)
        print(f"✓ Rewrote {INPUT_DIR / dataset}")

    pd.DataFrame(summary_rows).to_csv(SUMMARY_PATH, index=False)
    pd.DataFrame(value_rows).to_csv(VALUE_COUNTS_PATH, index=False)
    demonstrate_required_examples()
    print(f"\n✓ Cleaning summary saved to {SUMMARY_PATH}")
    print(f"✓ Value-count comparisons saved to {VALUE_COUNTS_PATH}")
    print(f"✓ Rewrote the source CSV files in {INPUT_DIR}")


if __name__ == "__main__":
    main()
