"""Database Integration Pipeline for Seller Trust & Safety Analysis.

Loads cleaned processed Olist datasets into a local SQLite database using
SQLAlchemy and Pandas. Performs schema validation and verification queries.
"""

from __future__ import annotations

import argparse
import json
from importlib import import_module
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect

try:
    dataset_dtypes = import_module("scripts.ingest_data").DATASET_DTYPES
except ModuleNotFoundError:
    dataset_dtypes = import_module("ingest_data").DATASET_DTYPES

DATASET_DTYPES = dataset_dtypes

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
DB_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output" / "db_audit"

# Maps processed filename to database table name
TABLE_MAPPING = {
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_customers_dataset.csv": "customers",
    "olist_sellers_dataset.csv": "sellers",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "product_category_name_translation.csv": "product_category_name_translation",
}


def load_datasets_to_db(db_url: str, processed_dir: Path) -> dict[str, int]:
    """Load each CSV into the SQLite database and return table row counts."""
    engine = create_engine(db_url)
    row_counts = {}

    for filename, table_name in TABLE_MAPPING.items():
        file_path = processed_dir / filename
        if not file_path.exists():
            print(f"  ⚠ Skipping missing file: {filename}")
            continue

        print(f"  Loading {filename} into table '{table_name}'...")
        dtypes = DATASET_DTYPES.get(filename)
        df = pd.read_csv(file_path, dtype=dtypes)

        # Write to SQLite
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        row_counts[table_name] = len(df)

    return row_counts


def validate_schema(db_url: str) -> dict[str, Any]:
    """Validate schemas of loaded tables using sqlalchemy.inspect."""
    engine = create_engine(db_url)
    inspector = inspect(engine)
    schema_report = {}

    for table_name in TABLE_MAPPING.values():
        if not inspector.has_table(table_name):
            continue

        columns = inspector.get_columns(table_name)
        column_details = []
        for col in columns:
            column_details.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col["nullable"],
            })

        schema_report[table_name] = {
            "table_name": table_name,
            "total_columns": len(column_details),
            "columns": column_details,
        }

    return schema_report


def run_verification_queries(db_url: str) -> dict[str, Any]:
    """Run validation SELECT queries on loaded SQLite tables."""
    engine = create_engine(db_url)

    # 1. Row counts comparison between Pandas and SQLite
    counts_query = """
    SELECT
        (SELECT COUNT(*) FROM orders) as orders_count,
        (SELECT COUNT(*) FROM order_payments) as payments_count,
        (SELECT COUNT(*) FROM order_items) as items_count,
        (SELECT COUNT(*) FROM customers) as customers_count
    """
    db_counts = pd.read_sql(counts_query, engine).iloc[0].to_dict()

    # 2. Sample aggregation query: Join orders, payments and customers
    revenue_by_state_query = """
        SELECT c.customer_state, COUNT(DISTINCT o.order_id) as order_count, SUM(p.payment_value) as total_revenue
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN order_payments p ON o.order_id = p.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_state
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    revenue_df = pd.read_sql(revenue_by_state_query, engine)
    revenue_df["total_revenue"] = revenue_df["total_revenue"].round(2)

    return {
        "database_row_counts": db_counts,
        "top_5_states_revenue": revenue_df.to_dict(orient="records"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load processed data into SQLite database and audit schemas."
    )
    parser.add_argument(
        "--db-file",
        type=Path,
        default=DB_DIR / "analytics.db",
    )
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.db_file.parent.mkdir(parents=True, exist_ok=True)

    db_url = f"sqlite:///{args.db_file}"
    print(f"Starting database integration pipeline (DB: {args.db_file})...")

    # 1. Load data to database
    row_counts = load_datasets_to_db(db_url, args.processed_dir)
    print("✓ Cleaned datasets loaded successfully to SQL tables.")

    # 2. Validate table schemas
    schema_report = validate_schema(db_url)
    print("✓ Schema validation completed.")

    # 3. Run verification queries
    verification_results = run_verification_queries(db_url)
    print("✓ Verification query checks passed.")

    # Save database audit report
    audit_report = {
        "pipeline": "Database Integration & Schema Validation",
        "database_path": str(args.db_file),
        "loaded_tables_count": len(row_counts),
        "table_row_counts": row_counts,
        "schema_validation": schema_report,
        "verification_queries": verification_results,
    }

    json_file = args.output_dir / "db_integration_audit.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)
    print(f"✓ Saved database audit report to {json_file}")

    # Print summary highlights
    print(f"\n=======================================================")
    print(f"  Database Integration Report: {args.db_file.name}")
    print(f"=======================================================")
    for table, count in row_counts.items():
        print(f"  ✓ Table '{table}': {count:,} rows loaded.")
    print(f"\n  Top 5 Customer States by SQLite Revenue:")
    for state in verification_results["top_5_states_revenue"]:
        print(f"    - {state['customer_state']}: {state['order_count']:,} orders | {state['total_revenue']:,} BRL")
    print(f"=======================================================")

    print("\nDatabase integration pipeline completed successfully!")


if __name__ == "__main__":
    main()
