"""Load raw project data with explicit parsing parameters and audit output."""

import json
from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
INGESTED_DATA_DIR = PROJECT_ROOT / "data" / "ingested"


def ingest_csv(
    filepath: str | Path,
    delimiter: str = ",",
    encoding: str = "utf-8",
    dtype_dict=None,
) -> pd.DataFrame:
    """Load a CSV file with explicit parsing parameters.

    Args:
        filepath: Path to the CSV file.
        delimiter: Field delimiter; comma by default, but semicolon and tab are valid.
        encoding: File encoding; UTF-8 is standard, but latin-1 and cp1252 may be used.
        dtype_dict: Optional mapping of column names to pandas data types.

    Returns:
        A DataFrame containing the loaded records.
    """
    try:
        df = pd.read_csv(
            filepath,
            delimiter=delimiter,
            encoding=encoding,
            dtype=dtype_dict,
        )
        print(f"✓ CSV loaded: {filepath}")
        print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"  Columns: {list(df.columns)}")
        return df
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        raise
    except UnicodeDecodeError:
        print(f"Encoding error: Could not decode with {encoding}")
        print("Try: latin-1, iso-8859-1, or cp1252")
        raise
    except pd.errors.ParserError as exc:
        print(f"CSV parsing error: Could not parse {filepath}")
        raise ValueError(f"Invalid CSV structure: {filepath}") from exc


def ingest_json(filepath: str | Path, is_nested: bool = False) -> pd.DataFrame:
    """Load a JSON file, optionally flattening nested records into columns.

    Args:
        filepath: Path to the JSON file.
        is_nested: When true, flatten nested dictionaries using dotted column names.

    Returns:
        A DataFrame containing the loaded records.
    """
    try:
        if is_nested:
            with open(filepath, encoding="utf-8") as file:
                records = json.load(file)
            df = pd.json_normalize(records)
            print("✓ Nested JSON flattened to tabular format")
        else:
            df = pd.read_json(filepath)

        print(f"✓ JSON loaded: {filepath}")
        print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"  Columns: {list(df.columns)}")
        return df
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        raise


def ingest_csv_with_fallback(
    filepath: str | Path,
    delimiters: tuple[str, ...] = (",",),
    fallback_encodings: tuple[str, ...] | None = None,
    min_columns: int | None = None,
) -> pd.DataFrame:
    """Load a CSV by trying each delimiter and encoding combination.

    UTF-8 is attempted first because it is the expected encoding for the Olist data.
    The latin-1 fallback is intentionally retained for legacy source files, although
    successful decoding with latin-1 should still be reviewed for text accuracy.

    Args:
        filepath: Path to the CSV file.
        delimiters: Delimiters to try in order.
        fallback_encodings: Encodings to try for each delimiter.
        min_columns: Optional minimum number of columns required for success. This
            prevents a wrong delimiter from being accepted as a one-column result.
    """
    if fallback_encodings is None:
        fallback_encodings = ("utf-8", "latin-1", "iso-8859-1", "cp1252")

    try:
        for delimiter in delimiters:
            for encoding in fallback_encodings:
                try:
                    df = pd.read_csv(
                        filepath,
                        delimiter=delimiter,
                        encoding=encoding,
                    )
                    if min_columns is not None and df.shape[1] < min_columns:
                        continue

                    print(
                        f"✓ Successfully loaded with delimiter={delimiter!r}, encoding={encoding!r}"
                    )
                    print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
                    return df
                except (UnicodeDecodeError, pd.errors.ParserError):
                    continue
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        raise

    combinations = ", ".join(
        f"delimiter={delimiter!r}, encoding={encoding!r}"
        for delimiter in delimiters
        for encoding in fallback_encodings
    )
    raise ValueError(f"Could not load {filepath} with any combination: {combinations}")


def document_ingestion(df: pd.DataFrame, source_file: str | Path) -> pd.DataFrame:
    """Print a detailed ingestion report for an audit trail."""
    print(f"\n{'=' * 60}")
    print(f"INGESTION REPORT: {source_file}")
    print(f"{'=' * 60}")
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")
    print("\nColumn Names & Data Types:")
    print(df.dtypes)
    print("\nNull Values Per Column:")
    print(df.isnull().sum())
    print("\nFirst 3 Rows:")
    print(df.head(3).to_string())
    print(f"{'=' * 60}\n")
    return df


def ingest_all_raw_csvs(
    raw_dir: str | Path = RAW_DATA_DIR,
    output_dir: str | Path = INGESTED_DATA_DIR,
) -> list[tuple[str, int, int]]:
    """Ingest every raw CSV and save an uncleaned copy to the ingested directory."""
    raw_dir = Path(raw_dir)
    output_dir = Path(output_dir)

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    source_files = sorted(raw_dir.glob("*.csv"))
    if not source_files:
        raise FileNotFoundError(f"No CSV files found in raw data directory: {raw_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    summary = []

    for source_file in source_files:
        df = ingest_csv_with_fallback(source_file, min_columns=2)
        document_ingestion(df, source_file.name)
        output_file = output_dir / source_file.name
        df.to_csv(output_file, index=False, encoding="utf-8")
        summary.append((source_file.name, df.shape[0], df.shape[1]))
        print(f"✓ Saved ingested data: {output_file}")

    return summary


def main() -> None:
    """Run ingestion for all CSV files in data/raw."""
    print("Starting Olist data ingestion...\n")
    summary = ingest_all_raw_csvs()
    print("\n✓ All raw CSV files ingested and saved to data/ingested/")
    for filename, rows, columns in summary:
        print(f"  {filename}: {rows} rows × {columns} columns")


if __name__ == "__main__":
    main()
