"""SQL Filtering & Grouping Analysis Pipeline.

Demonstrates and executes queries with WHERE, GROUP BY, HAVING, and ORDER BY:
- WHERE filters raw rows before aggregation.
- GROUP BY groups rows by dimensions.
- HAVING filters aggregated group metrics.
- ORDER BY sorts the resulting records.
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
DB_PATH = PROJECT_ROOT / "data" / "analytics.db"
QUERIES_DIR = PROJECT_ROOT / "queries"
OUTPUT_DIR = PROJECT_ROOT / "output" / "sql_filtering"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

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


def ensure_database(db_url: str, processed_dir: Path) -> None:
    """Ensure SQLite database is populated with processed tables."""
    engine = create_engine(db_url)
    inspector = inspect(engine)
    required = ["orders", "order_items", "order_payments", "sellers", "products", "order_reviews"]
    missing = [t for t in required if not inspector.has_table(t)]

    if missing:
        print(f"Tables missing ({missing}). Loading processed CSVs into database...")
        for filename, table_name in TABLE_MAPPING.items():
            file_path = processed_dir / filename
            if not file_path.exists():
                continue
            dtypes = DATASET_DTYPES.get(filename)
            df = pd.read_csv(file_path, dtype=dtypes)
            df.to_sql(table_name, engine, if_exists="replace", index=False)
            print(f"  ✓ Loaded table '{table_name}' ({len(df):,} rows)")


def execute_query(engine: Any, query_path: Path) -> pd.DataFrame:
    """Read and execute a SQL query file."""
    if not query_path.exists():
        raise FileNotFoundError(f"Query file not found: {query_path}")
    with open(query_path, "r", encoding="utf-8") as f:
        sql = f.read()
    return pd.read_sql(sql, engine)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute SQL filtering and grouping queries with WHERE, GROUP BY, HAVING, and ORDER BY."
    )
    parser.add_argument("--db-file", type=Path, default=DB_PATH)
    parser.add_argument("--queries-dir", type=Path, default=QUERIES_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite:///{args.db_file}"

    print(f"Starting SQL filtering & grouping pipeline (DB: {args.db_file.name})...")
    ensure_database(db_url, args.processed_dir)
    engine = create_engine(db_url)

    summary: dict[str, Any] = {
        "pipeline": "SQL Filtering & Grouping",
        "database": str(args.db_file),
        "queries_executed": {},
    }

    # 1. High Volume Sellers (HAVING total_orders >= 50 and avg review < 4.0)
    sellers_query = args.queries_dir / "high_volume_sellers.sql"
    print(f"Executing {sellers_query.name}...")
    sellers_df = execute_query(engine, sellers_query)
    sellers_out = args.output_dir / "high_volume_sellers.csv"
    sellers_df.to_csv(sellers_out, index=False)
    print(f"✓ Saved {len(sellers_df)} high-volume seller records to {sellers_out}")
    summary["queries_executed"]["high_volume_sellers"] = {
        "query_file": sellers_query.name,
        "matched_sellers_count": len(sellers_df),
        "total_revenue_affected": float(sellers_df["total_revenue"].sum().round(2)) if not sellers_df.empty else 0.0,
        "lowest_review_score": float(sellers_df["avg_review_score"].min()) if not sellers_df.empty else None,
    }

    # 2. Top Product Categories (HAVING total_revenue >= 50,000)
    cats_query = args.queries_dir / "top_product_categories.sql"
    print(f"Executing {cats_query.name}...")
    cats_df = execute_query(engine, cats_query)
    cats_out = args.output_dir / "top_product_categories.csv"
    cats_df.to_csv(cats_out, index=False)
    print(f"✓ Saved {len(cats_df)} top category records to {cats_out}")
    summary["queries_executed"]["top_product_categories"] = {
        "query_file": cats_query.name,
        "qualifying_categories_count": len(cats_df),
        "top_category": str(cats_df.iloc[0]["category_name"]) if not cats_df.empty else None,
        "top_category_revenue": float(cats_df.iloc[0]["total_revenue"]) if not cats_df.empty else None,
    }

    # 3. Monthly Order Thresholds (HAVING orders >= 1000 and revenue >= 150000)
    months_query = args.queries_dir / "monthly_order_thresholds.sql"
    print(f"Executing {months_query.name}...")
    months_df = execute_query(engine, months_query)
    months_out = args.output_dir / "monthly_order_thresholds.csv"
    months_df.to_csv(months_out, index=False)
    print(f"✓ Saved {len(months_df)} qualifying operating months to {months_out}")
    summary["queries_executed"]["monthly_order_thresholds"] = {
        "query_file": months_query.name,
        "qualifying_months_count": len(months_df),
        "peak_month": str(months_df.loc[months_df["total_revenue"].idxmax(), "year_month"]) if not months_df.empty else None,
        "peak_revenue": float(months_df["total_revenue"].max()) if not months_df.empty else None,
    }

    # Save summary JSON
    summary_file = args.output_dir / "filtering_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved filtering summary report to {summary_file}")

    print("\n=======================================================")
    print("  SQL Filtering & Grouping Analysis Summary")
    print("=======================================================")
    print(f"  • High-Volume Underperforming Sellers: {summary['queries_executed']['high_volume_sellers']['matched_sellers_count']} sellers flagged")
    print(f"  • Major Revenue Categories (>= 50k BRL): {summary['queries_executed']['top_product_categories']['qualifying_categories_count']} categories (Top: {summary['queries_executed']['top_product_categories']['top_category']})")
    print(f"  • High-Volume Operating Months (>= 1k orders): {summary['queries_executed']['monthly_order_thresholds']['qualifying_months_count']} months")
    print("=======================================================")

    print("\nSQL filtering pipeline completed successfully!")


if __name__ == "__main__":
    main()
