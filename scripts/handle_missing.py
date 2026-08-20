"""Analyze and safely handle missing values in ingested Olist datasets.

The Olist source contains several meaningful nulls. This workflow therefore
preserves source columns where a null represents an unavailable business event
or optional customer input, while adding explicit missingness indicators for
analysis.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from scripts.ingest_data import DATASET_DTYPES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INGESTED_DATA_DIR = PROJECT_ROOT / "data" / "ingested"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
MISSING_DATA_REPORT_DIR = PROJECT_ROOT / "output" / "missing_data"
DECISIONS_PATH = PROJECT_ROOT / "output" / "imputation_decisions.json"

ORDER_DATE_COLUMNS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

ORDER_MISSINGNESS_COLUMNS = [
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
]

PRODUCT_METADATA_COLUMNS = [
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
]

PRODUCT_DIMENSION_COLUMNS = [
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]


def _percentage(count: int, row_count: int) -> float:
    """Return a rounded percentage without dividing by zero."""
    return round(count / row_count * 100, 2) if row_count else 0.0


def analyze_missing_values(df: pd.DataFrame, dataset_name: str = "dataset") -> pd.DataFrame:
    """Compute null counts, percentages, types, and treatment context."""
    row_count = len(df)
    null_counts = df.isna().sum()
    missing_analysis = pd.DataFrame(
        {
            "dataset": dataset_name,
            "column": df.columns,
            "null_count": null_counts.to_numpy(),
            "null_percentage": [
                _percentage(int(count), row_count) for count in null_counts
            ],
            "data_type": [str(dtype) for dtype in df.dtypes],
            "unique_count": [int(df[column].nunique(dropna=True)) for column in df.columns],
        }
    )
    missing_analysis["null_meaning"] = missing_analysis["column"].map(
        lambda column: missing_value_meaning(dataset_name, str(column))
    )

    print("=" * 70)
    print(f"BEFORE MISSING-DATA TREATMENT - {dataset_name}")
    print("=" * 70)
    print(missing_analysis.to_string(index=False))
    print(f"\nTotal rows: {row_count}")
    print(f"Total cells: {row_count * len(df.columns)}")
    print(f"Missing cells: {int(df.isna().sum().sum())}")
    print("=" * 70)
    return missing_analysis


def missing_value_meaning(dataset_name: str, column: str) -> str:
    """Return the Olist business interpretation for a nullable column."""
    if dataset_name == "olist_order_reviews_dataset.csv" and column in {
        "review_comment_title",
        "review_comment_message",
    }:
        return "Optional customer-provided text; null means no text was supplied."
    if dataset_name == "olist_orders_dataset.csv" and column in ORDER_MISSINGNESS_COLUMNS:
        return "Operational event date may be unavailable for incomplete or cancelled orders."
    if dataset_name == "olist_products_dataset.csv" and column == "product_category_name":
        return "Product category is unavailable in the source catalog."
    if dataset_name == "olist_products_dataset.csv" and column in PRODUCT_METADATA_COLUMNS:
        return "Optional product metadata is unavailable in the source catalog."
    if dataset_name == "olist_products_dataset.csv" and column in PRODUCT_DIMENSION_COLUMNS:
        return "Physical product measurement is unavailable in the source catalog."
    return "No missing values expected or no dataset-specific treatment configured."


def impute_mean_median(
    df: pd.DataFrame, numerical_cols: list[str], strategy: str = "median"
) -> pd.DataFrame:
    """Fill selected numeric nulls with a mean or median.

    This helper is intentionally opt-in and is not used for Olist identifiers,
    dates, review text, or product dimensions in the default workflow.
    """
    if strategy not in {"mean", "median"}:
        raise ValueError("strategy must be 'mean' or 'median'")
    result = df.copy()
    for column in numerical_cols:
        if column not in result or not result[column].isna().any():
            continue
        value = result[column].mean() if strategy == "mean" else result[column].median()
        if pd.notna(value):
            null_count = int(result[column].isna().sum())
            result[column] = result[column].fillna(value)
            print(f"  Filled {null_count} values in {column} with {strategy} ({value:.2f})")
    return result


def impute_mode(df: pd.DataFrame, categorical_cols: list[str]) -> pd.DataFrame:
    """Fill selected categorical nulls with their mode; opt-in only."""
    result = df.copy()
    for column in categorical_cols:
        if column not in result or not result[column].isna().any():
            continue
        modes = result[column].mode(dropna=True)
        if not modes.empty:
            null_count = int(result[column].isna().sum())
            result[column] = result[column].fillna(modes.iloc[0])
            print(f"  Filled {null_count} values in {column} with mode {modes.iloc[0]!r}")
    return result


def impute_forward_fill(df: pd.DataFrame, time_series_cols: list[str]) -> pd.DataFrame:
    """Forward-fill explicitly selected, already ordered time-series columns."""
    result = df.copy()
    for column in time_series_cols:
        if column in result and result[column].isna().any():
            null_count = int(result[column].isna().sum())
            result[column] = result[column].ffill()
            print(f"  Forward-filled {null_count} values in {column}")
    return result


def drop_rows_with_nulls(df: pd.DataFrame, critical_cols: list[str]) -> pd.DataFrame:
    """Drop rows with null critical fields; never used by default for Olist."""
    missing_columns = [column for column in critical_cols if column not in df.columns]
    if missing_columns:
        raise KeyError(f"Critical columns not found: {missing_columns}")
    before = len(df)
    result = df.dropna(subset=critical_cols).copy()
    print(f"  Dropped {before - len(result)} rows with null in {critical_cols}")
    return result


def add_missing_indicator(df: pd.DataFrame, column: str) -> tuple[pd.DataFrame, str]:
    """Add a boolean indicator for null values in a source column."""
    indicator = f"{column}_missing"
    result = df.copy(deep=False)
    result[indicator] = result[column].isna()
    return result, indicator


def _decision(
    dataset: str,
    column: str,
    strategy: str,
    before: pd.Series,
    after: pd.Series,
    reasoning: str,
    risk: str,
    value_used: Any = None,
    indicator: str | None = None,
) -> dict[str, Any]:
    """Build one auditable treatment decision."""
    return {
        "dataset": dataset,
        "column": column,
        "strategy": strategy,
        "null_count_before": int(before.isna().sum()),
        "null_percentage_before": _percentage(int(before.isna().sum()), len(before)),
        "null_count_after": int(after.isna().sum()),
        "rows_affected": int(before.isna().sum()),
        "value_used": value_used,
        "missingness_indicator": indicator,
        "business_reasoning": reasoning,
        "risk_assessment": risk,
    }


def apply_dataset_treatment(
    df: pd.DataFrame, dataset_name: str
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Apply the documented Olist treatment for one dataset."""
    result = df.copy()
    decisions: list[dict[str, Any]] = []

    if dataset_name == "olist_order_reviews_dataset.csv":
        for column in ("review_comment_title", "review_comment_message"):
            if column in result:
                before = result[column].copy()
                result, indicator = add_missing_indicator(result, column)
                decisions.append(
                    _decision(
                        dataset_name,
                        column,
                        "preserve_null_add_indicator",
                        before,
                        result[column],
                        "Missing review text means the customer did not provide that optional text.",
                        "Low",
                        indicator=indicator,
                    )
                )

    elif dataset_name == "olist_orders_dataset.csv":
        original_date_values = {
            column: result[column].copy()
            for column in ORDER_DATE_COLUMNS
            if column in result
        }
        for column in ORDER_DATE_COLUMNS:
            if column in result:
                result[column] = pd.to_datetime(result[column], errors="coerce")
        for column in ORDER_MISSINGNESS_COLUMNS:
            if column in result:
                before = original_date_values[column]
                result, indicator = add_missing_indicator(result, column)
                decisions.append(
                    _decision(
                        dataset_name,
                        column,
                        "preserve_null_add_indicator",
                        before,
                        result[column],
                        "Operational event dates are naturally absent for incomplete, unavailable, or cancelled orders; global date imputation would invent events.",
                        "Medium",
                        indicator=indicator,
                    )
                )

    elif dataset_name == "olist_products_dataset.csv":
        for column in PRODUCT_METADATA_COLUMNS + PRODUCT_DIMENSION_COLUMNS:
            if column in result:
                before = result[column].copy()
                result, indicator = add_missing_indicator(result, column)
                decisions.append(
                    _decision(
                        dataset_name,
                        column,
                        "preserve_null_add_indicator",
                        before,
                        result[column],
                        "Catalog metadata or physical measurements are unavailable in the source; arbitrary mode or median values would misrepresent the product.",
                        "Low",
                        indicator=indicator,
                    )
                )
        if "product_category_name" in result:
            result["product_category_name_analysis"] = result["product_category_name"].fillna(
                "unknown"
            )
            decisions.append(
                {
                    "dataset": dataset_name,
                    "column": "product_category_name_analysis",
                    "strategy": "derived_unknown_label",
                    "null_count_before": int(df["product_category_name"].isna().sum()),
                    "null_count_after": int(result["product_category_name_analysis"].isna().sum()),
                    "rows_affected": int(df["product_category_name"].isna().sum()),
                    "value_used": "unknown",
                    "missingness_indicator": "product_category_name_missing",
                    "business_reasoning": "Provide a safe grouping value for category analysis while preserving the original nullable category column.",
                    "risk_assessment": "Low",
                }
            )

    else:
        for column in result.columns:
            if result[column].isna().any():
                decisions.append(
                    _decision(
                        dataset_name,
                        str(column),
                        "preserve_null_no_treatment",
                        result[column].copy(),
                        result[column],
                        "No dataset-specific missing-value treatment is required.",
                        "Low",
                    )
                )

    return result, decisions


def validate_imputation(
    df_original: pd.DataFrame, df_imputed: pd.DataFrame
) -> dict[str, Any]:
    """Compare row counts, null counts, and columns before and after treatment."""
    missing_after = []
    for column in df_imputed.columns:
        null_count = int(df_imputed[column].isna().sum())
        missing_after.append(
            {
                "column": column,
                "null_count_after": null_count,
                "null_percentage_after": _percentage(null_count, len(df_imputed)),
                "data_type_after": str(df_imputed[column].dtype),
            }
        )

    shared_columns = df_original.columns.intersection(df_imputed.columns)
    new_null_counts = {}
    for column in shared_columns:
        original_mask = df_original[column].isna().reindex(df_imputed.index, fill_value=True)
        treated_mask = df_imputed[column].isna()
        new_null_counts[column] = int((treated_mask & ~original_mask).sum())

    unexpected_new_nulls = [
        column for column, count in new_null_counts.items() if count > 0
    ]
    report = {
        "rows_before": len(df_original),
        "rows_after": len(df_imputed),
        "rows_removed": len(df_original) - len(df_imputed),
        "total_nulls_before": int(df_original.isna().sum().sum()),
        "total_nulls_after": int(df_imputed.isna().sum().sum()),
        "columns_before": list(df_original.columns),
        "columns_after": list(df_imputed.columns),
        "missing_after": missing_after,
        "new_null_counts": new_null_counts,
        "unexpected_new_nulls": unexpected_new_nulls,
        "validation_status": "FAIL" if unexpected_new_nulls else "PASS",
    }
    print("\nAFTER MISSING-DATA TREATMENT")
    print(f"Rows: {report['rows_before']} -> {report['rows_after']}")
    print(f"Null cells: {report['total_nulls_before']} -> {report['total_nulls_after']}")
    return report


def _json_safe(value: Any) -> Any:
    """Convert pandas/numpy values to JSON-safe native values."""
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if not isinstance(value, (list, dict, tuple)) and bool(pd.isna(value)):
        return None
    return value


def process_dataset(input_path: Path, output_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Process one ingested CSV and save its treatment report and output."""
    dataset_name = input_path.name
    df = pd.read_csv(input_path, dtype=DATASET_DTYPES.get(dataset_name))
    before_analysis = analyze_missing_values(df, dataset_name)
    treated_df, decisions = apply_dataset_treatment(df, dataset_name)
    after_report = validate_imputation(df, treated_df)

    report = {
        "dataset": dataset_name,
        "input": str(input_path.relative_to(PROJECT_ROOT)),
        "output": str((output_dir / dataset_name).relative_to(PROJECT_ROOT)),
        "before_analysis": before_analysis.to_dict(orient="records"),
        "after_validation": after_report,
        "decisions": decisions,
    }
    report_path = MISSING_DATA_REPORT_DIR / f"{input_path.stem}_missing_treatment.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2, default=_json_safe, allow_nan=False)

    if after_report["validation_status"] != "PASS":
        raise ValueError(
            f"Post-treatment validation failed for {dataset_name}: "
            f"{after_report['unexpected_new_nulls']}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    treated_df.to_csv(output_dir / dataset_name, index=False, encoding="utf-8")
    return report, decisions


def handle_all_ingested_data(
    input_dir: str | Path = INGESTED_DATA_DIR,
    output_dir: str | Path = PROCESSED_DATA_DIR,
) -> dict[str, Any]:
    """Run missing-data analysis and treatment for every ingested CSV."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Ingested data directory not found: {input_dir}")

    csv_files = sorted(input_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in ingested data directory: {input_dir}")

    all_decisions: list[dict[str, Any]] = []
    dataset_summaries: list[dict[str, Any]] = []
    for input_path in csv_files:
        report, decisions = process_dataset(input_path, output_dir)
        after = report["after_validation"]
        all_decisions.extend(decisions)
        dataset_summaries.append(
            {
                "dataset": input_path.name,
                "rows_before": after["rows_before"],
                "rows_after": after["rows_after"],
                "rows_removed": after["rows_removed"],
                "total_nulls_before": after["total_nulls_before"],
                "total_nulls_after": after["total_nulls_after"],
            }
        )

    summary = {
        "input_directory": str(input_dir.relative_to(PROJECT_ROOT)),
        "output_directory": str(output_dir.relative_to(PROJECT_ROOT)),
        "dataset_count": len(dataset_summaries),
        "datasets": dataset_summaries,
    }
    with (MISSING_DATA_REPORT_DIR / "missing_treatment_summary.json").open(
        "w", encoding="utf-8"
    ) as summary_file:
        json.dump(summary, summary_file, indent=2, allow_nan=False)
    with DECISIONS_PATH.open("w", encoding="utf-8") as decisions_file:
        json.dump(all_decisions, decisions_file, indent=2, default=_json_safe, allow_nan=False)

    summary_rows = pd.DataFrame(dataset_summaries)
    summary_rows.to_csv(MISSING_DATA_REPORT_DIR / "missing_treatment_summary.csv", index=False)
    return summary


def main() -> None:
    """Run missing-data handling for all ingested Olist CSV files."""
    print("Starting Olist missing-data workflow...\n")
    try:
        summary = handle_all_ingested_data()
    except Exception as exc:
        print(f"\n✗ Missing-data workflow failed: {exc}")
        raise SystemExit(1) from exc

    print("\n✓ Missing-data workflow completed")
    print(f"  Datasets processed: {summary['dataset_count']}")
    print(f"  Processed files: {PROCESSED_DATA_DIR}")
    print(f"  Reports: {MISSING_DATA_REPORT_DIR}")
    print(f"  Decisions: {DECISIONS_PATH}")


if __name__ == "__main__":
    main()
