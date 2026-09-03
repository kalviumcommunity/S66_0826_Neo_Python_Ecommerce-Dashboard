import json
import os
from datetime import datetime
from pathlib import Path

import chardet
import pandas as pd


BACKEND_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_FILE = str(BACKEND_ROOT / "data/processed/olist_products_dataset.csv")
EXPECTED_COLUMNS = [
    "product_id",
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
    "product_category_name_missing",
    "product_name_lenght_missing",
    "product_description_lenght_missing",
    "product_photos_qty_missing",
    "product_weight_g_missing",
    "product_length_cm_missing",
    "product_height_cm_missing",
    "product_width_cm_missing",
    "product_category_name_analysis",
]
OUTPUT_REPORT = str(BACKEND_ROOT / "output/validation_report/olist_products_intake_report.json")


def validate_file_exists(filepath):
    """Check if file exists and is non-empty."""
    if not os.path.exists(filepath):
        return False, f"FAIL: File does not exist: {filepath}"

    if os.path.getsize(filepath) == 0:
        return False, f"FAIL: File is empty: {filepath}"

    return True, f"PASS: File exists and has content: {filepath}"


def validate_file_format(filepath, allowed_formats=("csv",)):
    """Check if file extension is supported."""
    extension = filepath.split(".")[-1].lower()

    if extension not in allowed_formats:
        return False, f"FAIL: Unsupported format: {extension}. Allowed: {allowed_formats}"

    return True, f"PASS: Format valid: {extension}"


def validate_schema(df, expected_columns):
    """Validate that DataFrame has all expected columns."""
    missing = set(expected_columns) - set(df.columns)
    extra = set(df.columns) - set(expected_columns)

    issues = []
    if missing:
        issues.append(f"Missing columns: {missing}")
    if extra:
        issues.append(f"Unexpected columns: {extra}")

    if not issues:
        return True, f"PASS: Schema valid: {len(df.columns)} columns present"
    return False, f"FAIL: {' | '.join(issues)}"


def detect_encoding(filepath):
    """Detect file encoding with confidence."""
    with open(filepath, "rb") as f:
        result = chardet.detect(f.read(10000))

    encoding = result.get("encoding") or "utf-8"
    if encoding.lower() == "ascii":
        encoding = "utf-8"
    confidence = result.get("confidence", 0)

    return encoding, f"PASS: Detected: {encoding} (confidence: {confidence:.1%})"


def capture_dataset_stats(filepath, df):
    """Log row count and file size."""
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    row_count = len(df)
    col_count = len(df.columns)

    return {
        "rows": row_count,
        "columns": col_count,
        "file_size_mb": round(file_size_mb, 2),
        "bytes": os.path.getsize(filepath),
    }


def write_intake_report(report):
    os.makedirs(os.path.dirname(OUTPUT_REPORT), exist_ok=True)
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)


def generate_intake_report(filepath, expected_columns):
    """Generate complete intake validation report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "filepath": filepath,
        "validations": {},
    }

    file_exists, msg = validate_file_exists(filepath)
    report["validations"]["file_exists"] = msg
    if not file_exists:
        write_intake_report(report)
        return report

    format_valid, msg = validate_file_format(filepath)
    report["validations"]["format"] = msg
    if not format_valid:
        write_intake_report(report)
        return report

    encoding, msg = detect_encoding(filepath)
    report["validations"]["encoding"] = msg

    try:
        df = pd.read_csv(filepath, encoding=encoding)
    except (UnicodeDecodeError, pd.errors.ParserError, OSError) as exc:
        report["validations"]["data_read"] = f"FAIL: Unable to read file: {exc}"
        write_intake_report(report)
        return report

    schema_valid, msg = validate_schema(df, expected_columns)
    report["validations"]["schema"] = msg

    stats = capture_dataset_stats(filepath, df)
    report["statistics"] = stats

    write_intake_report(report)
    return report


if __name__ == "__main__":
    intake_report = generate_intake_report(SAMPLE_FILE, EXPECTED_COLUMNS)
    print(json.dumps(intake_report, indent=2, default=str))
    if any(
        isinstance(message, str) and message.startswith("FAIL:")
        for message in intake_report["validations"].values()
    ):
        raise SystemExit(1)
