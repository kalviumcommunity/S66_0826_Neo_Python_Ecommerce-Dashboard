"""Validate and rewrite the processed Olist datasets in place.

The source CSVs in ``data/processed`` are loaded and validated. Validation
reports are written as one JSON file per dataset under ``output``. The source
CSV files are rewritten in place without validation columns.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORT_DIR = OUTPUT_DIR / "data_validation_reports"

MIN_VALID_DATE = pd.Timestamp("2016-01-01")

IDENTIFIER_COLUMNS = {
    "customer_id",
    "customer_unique_id",
    "order_id",
    "product_id",
    "seller_id",
    "review_id",
}
ZIP_COLUMNS = {
    "customer_zip_code_prefix",
    "seller_zip_code_prefix",
    "geolocation_zip_code_prefix",
}

DATASET_REQUIRED_COLUMNS: dict[str, list[str]] = {
    "olist_customers_dataset.csv": ["customer_id", "customer_unique_id"],
    "olist_geolocation_dataset.csv": ["geolocation_zip_code_prefix"],
    "olist_order_items_dataset.csv": ["order_id", "product_id", "seller_id"],
    "olist_order_payments_dataset.csv": ["order_id"],
    "olist_order_reviews_dataset.csv": ["review_id", "order_id"],
    "olist_orders_dataset.csv": ["order_id", "customer_id"],
    "olist_products_dataset.csv": ["product_id"],
    "olist_sellers_dataset.csv": ["seller_id"],
}

VALID_PAYMENT_TYPES = {"credit_card", "boleto", "voucher", "debit_card", "cash"}
VALID_ORDER_STATUSES = {
    "delivered",
    "shipped",
    "canceled",
    "unavailable",
    "invoiced",
    "processing",
    "created",
    "approved",
}


def _read_dtype_overrides(columns: list[str]) -> dict[str, str]:
    """Return string overrides for identifiers and ZIP prefixes."""
    return {
        column: "string"
        for column in columns
        if column in IDENTIFIER_COLUMNS or column in ZIP_COLUMNS
    }


def load_processed_datasets(
    processed_dir: str | Path = PROCESSED_DIR,
) -> dict[str, pd.DataFrame]:
    """Load direct CSV children of the processed directory."""
    processed_dir = Path(processed_dir)
    csv_files = sorted(processed_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {processed_dir}")

    datasets: dict[str, pd.DataFrame] = {}
    for csv_file in csv_files:
        header = pd.read_csv(csv_file, nrows=0).columns.tolist()
        datasets[csv_file.name] = pd.read_csv(
            csv_file,
            dtype=_read_dtype_overrides(header),
            dtype_backend="numpy_nullable",
        )
    return datasets


def _add_check(
    df: pd.DataFrame,
    name: str,
    condition: pd.Series,
) -> None:
    """Add a boolean validation column, treating unknown results as failures."""
    df[name] = condition.fillna(False).astype("boolean")


def _required_check(df: pd.DataFrame, column: str) -> pd.Series:
    """Check that a required column exists and contains no null values."""
    if column not in df.columns:
        return pd.Series(False, index=df.index, dtype="boolean")
    return df[column].notna()


def _valid_date_range(series: pd.Series) -> pd.Series:
    """Check dates are parseable, not before 2016, and not in the future."""
    parsed = pd.to_datetime(series, errors="coerce")
    return series.isna() | parsed.between(MIN_VALID_DATE, pd.Timestamp.now())


def _valid_nonnegative(series: pd.Series) -> pd.Series:
    """Check a numeric series is parseable and non-negative."""
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.notna() & numeric.ge(0)


def _valid_positive_integer(series: pd.Series) -> pd.Series:
    """Check a numeric series contains integer values greater than zero."""
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.notna() & numeric.ge(1) & numeric.mod(1).eq(0)


def _valid_identifier_format(series: pd.Series) -> pd.Series:
    """Check Olist identifiers are 32-character lowercase hexadecimal strings."""
    return series.str.fullmatch(r"[a-f0-9]{32}", na=False)


def _valid_zip_format(series: pd.Series) -> pd.Series:
    """Check ZIP prefixes contain exactly five digits."""
    return series.str.fullmatch(r"\d{5}", na=False)


def validate_dataset(dataset: str, source: pd.DataFrame) -> pd.DataFrame:
    """Add dataset-specific validation flags and an overall pass flag."""
    df = source.copy()
    validation_columns = [
        column for column in df.columns
        if column.startswith("valid_") or column == "passes_all_checks"
    ]
    df = df.drop(columns=validation_columns, errors="ignore")

    # Brazilian ZIP prefixes are five digits; restore leading zeroes that CSV
    # type inference may have removed during an earlier round-trip.
    for column in ZIP_COLUMNS.intersection(df.columns):
        df[column] = df[column].astype("string").str.zfill(5)

    for column in DATASET_REQUIRED_COLUMNS.get(dataset, []):
        _add_check(df, f"valid_{column}_not_null", _required_check(df, column))

    for column in df.columns:
        if column in IDENTIFIER_COLUMNS:
            _add_check(df, f"valid_{column}_format", _valid_identifier_format(df[column]))
        elif column in ZIP_COLUMNS:
            _add_check(df, f"valid_{column}_format", _valid_zip_format(df[column]))

    if dataset == "olist_order_items_dataset.csv":
        _add_check(df, "valid_order_item_id", _valid_positive_integer(df["order_item_id"]))
        _add_check(df, "valid_price", _valid_nonnegative(df["price"]))
        _add_check(df, "valid_freight_value", _valid_nonnegative(df["freight_value"]))
        _add_check(df, "valid_shipping_limit_date", _valid_date_range(df["shipping_limit_date"]))

    elif dataset == "olist_order_payments_dataset.csv":
        _add_check(df, "valid_payment_sequential", _valid_positive_integer(df["payment_sequential"]))
        _add_check(df, "valid_payment_installments", _valid_positive_integer(df["payment_installments"]))
        _add_check(df, "valid_payment_value", _valid_nonnegative(df["payment_value"]))
        _add_check(df, "valid_payment_type", df["payment_type"].isin(VALID_PAYMENT_TYPES))

    elif dataset == "olist_order_reviews_dataset.csv":
        score = pd.to_numeric(df["review_score"], errors="coerce")
        _add_check(df, "valid_review_score", score.between(1, 5))
        _add_check(df, "valid_review_creation_date", _valid_date_range(df["review_creation_date"]))
        _add_check(df, "valid_review_answer_timestamp", _valid_date_range(df["review_answer_timestamp"]))
        creation = pd.to_datetime(df["review_creation_date"], errors="coerce")
        answer = pd.to_datetime(df["review_answer_timestamp"], errors="coerce")
        _add_check(df, "valid_review_date_order", answer.isna() | creation.isna() | answer.ge(creation))

    elif dataset == "olist_orders_dataset.csv":
        _add_check(df, "valid_order_status", df["order_status"].isin(VALID_ORDER_STATUSES))
        date_columns = [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
        parsed_dates = {
            column: pd.to_datetime(df[column], errors="coerce")
            for column in date_columns
        }
        for column, parsed in parsed_dates.items():
            _add_check(df, f"valid_{column}", df[column].isna() | parsed.between(MIN_VALID_DATE, pd.Timestamp.now()))
        purchase = parsed_dates["order_purchase_timestamp"]
        approved = parsed_dates["order_approved_at"]
        carrier = parsed_dates["order_delivered_carrier_date"]
        delivered = parsed_dates["order_delivered_customer_date"]
        _add_check(df, "valid_approval_after_purchase", approved.isna() | purchase.isna() | approved.ge(purchase))
        _add_check(df, "valid_carrier_after_purchase", carrier.isna() | purchase.isna() | carrier.ge(purchase))
        _add_check(df, "valid_delivery_after_carrier", delivered.isna() | carrier.isna() | delivered.ge(carrier))

    elif dataset == "olist_geolocation_dataset.csv":
        latitude = pd.to_numeric(df["geolocation_lat"], errors="coerce")
        longitude = pd.to_numeric(df["geolocation_lng"], errors="coerce")
        _add_check(df, "valid_latitude", latitude.between(-90, 90))
        _add_check(df, "valid_longitude", longitude.between(-180, 180))

    elif dataset == "olist_products_dataset.csv":
        for column in [
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ]:
            _add_check(df, f"valid_{column}", _valid_nonnegative(df[column]))

    validation_columns = [column for column in df.columns if column.startswith("valid_")]
    df["passes_all_checks"] = df[validation_columns].all(axis=1)
    return df





def write_json_report(
    dataset: str,
    validated: pd.DataFrame,
    summary: list[dict[str, Any]],
) -> None:
    """Write one JSON validation report for a dataset."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    total = len(validated)
    passed = int(validated["passes_all_checks"].sum())
    failed = total - passed
    report = {
        "dataset": dataset,
        "records": total,
        "passed": passed,
        "failed": failed,
        "pass_percentage": round((passed / total) * 100, 2) if total else 0.0,
        "rules": summary,
    }
    report_path = REPORT_DIR / f"{Path(dataset).stem}_validation.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"✓ Validation report saved to {report_path}")


def build_reports(
    dataset: str,
    validated: pd.DataFrame,
) -> tuple[list[dict[str, Any]], pd.DataFrame]:
    """Build rule-level summary rows and failure counts."""
    validation_columns = [column for column in validated if column.startswith("valid_")]
    total = len(validated)
    summary = []
    for column in validation_columns:
        failed = int((~validated[column].fillna(False)).sum())
        summary.append({
            "dataset": dataset,
            "rule": column,
            "records": total,
            "passed": total - failed,
            "failed": failed,
        })

    return summary


def main() -> None:
    """Validate and rewrite every processed CSV in place."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    datasets = load_processed_datasets()

    for dataset, source in datasets.items():
        print(f"\nValidating {dataset} ({len(source)} records)...")
        validated = validate_dataset(dataset, source)
        summary = build_reports(dataset, validated)
        write_json_report(dataset, validated, summary)
        passed = int(validated["passes_all_checks"].sum())
        print(f"✓ Rewrote {dataset}: {passed}/{len(validated)} records passed")

    print(f"\n✓ Per-dataset JSON reports saved to {REPORT_DIR}")
    print(f"✓ Processed CSV files contain original data columns only")


if __name__ == "__main__":
    main()
