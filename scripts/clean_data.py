import logging
from pathlib import Path

import numpy as np
import pandas as pd

# 1. CONFIGURATION
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOG_FILE = PROJECT_ROOT / "output" / "data_cleaning.log"

# 2. LOGGING SETUP
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# 3. HELPER FUNCTIONS

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert all column names to a clean, consistent format."""
    df = df.copy()
    df.columns = [
        str(column).strip().lower().replace(" ", "_").replace("-", "_")
        for column in df.columns
    ]
    return df.loc[:, ~df.columns.duplicated()].copy()


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Remove empty rows and fill missing values in a safe, dataset-friendly way."""
    df = df.copy().dropna(how="all").copy()

    for column in df.columns:
        if df[column].dtype == object:
            df[column] = df[column].astype(str).str.strip()
            df[column] = df[column].replace({"nan": np.nan, "None": np.nan, "": np.nan})

    numeric_like_columns = [
        column for column in df.columns if any(keyword in column for keyword in ("amount", "price", "payment", "freight", "value", "total", "score", "rating", "lat", "lng", "latitude", "longitude"))
    ]

    for column in numeric_like_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        if df[column].notna().any():
            df[column] = df[column].fillna(df[column].median())

    for column in df.columns:
        if any(keyword in column for keyword in ("date", "time", "timestamp")):
            df[column] = pd.to_datetime(df[column], errors="coerce")

    return df


def ingest_data(filepath: str | Path) -> pd.DataFrame:
    """Read a CSV file from disk and return a Pandas DataFrame."""
    try:
        df = pd.read_csv(filepath)
        logging.info("Ingested %s rows from %s", len(df), filepath)
        return df
    except FileNotFoundError:
        logging.error("File not found: %s", filepath)
        raise
    except Exception as exc:
        logging.exception("Failed to read file: %s", filepath)
        raise RuntimeError(f"Unable to read input file: {filepath}") from exc


def process_data(df: pd.DataFrame, filename: str | None = None) -> pd.DataFrame:
    """Apply data cleaning rules to raw data before saving output."""
    rows_before = len(df)

    df = normalize_columns(df)
    df = df.drop_duplicates().copy()
    df = clean_missing_values(df)

    rows_after = len(df)
    logging.info(
        "Processed %s: %s rows -> %s rows",
        filename or "dataset",
        rows_before,
        rows_after,
    )
    return df


def output_results(df: pd.DataFrame, output_path: str | Path) -> None:
    """Save processed data to a CSV file in the output folder."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info("Saved cleaned output to %s", output_path)
    print(f"✓ Saved {len(df)} records to {output_path}")


def clean_all_raw_data(raw_dir: str | Path = RAW_DATA_DIR, output_dir: str | Path = OUTPUT_DIR) -> list[tuple[str, int, int]]:
    """Process every CSV in the raw folder and write cleaned versions to output."""
    raw_dir = Path(raw_dir)
    output_dir = Path(output_dir)

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    summary = []

    for input_file in sorted(raw_dir.glob("*.csv")):
        print(f"Processing {input_file.name}...")
        raw_df = ingest_data(input_file)
        cleaned_df = process_data(raw_df, input_file.name)
        output_file = output_dir / input_file.name
        output_results(cleaned_df, output_file)
        summary.append((input_file.name, len(raw_df), len(cleaned_df)))

    return summary


# 4. MAIN EXECUTION

def main() -> None:
    """Run the end-to-end data cleaning workflow from raw CSVs to output CSVs."""
    try:
        print("Starting data cleaning workflow...")
        logging.info("Starting data cleaning workflow.")

        summary = clean_all_raw_data()

        print("Workflow completed successfully.")
        for file_name, before_count, after_count in summary:
            print(f"{file_name}: {before_count} -> {after_count} rows")

        logging.info("Workflow completed successfully.")
    except Exception as exc:
        logging.exception("Workflow failed.")
        print(f"Error: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
