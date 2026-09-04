"""Centralized SQL Metrics Computation Pipeline.

Executes standardized business SQL metric queries against the SQLite database,
ensuring consistent, reusable, and auditable metrics across the organization.

Metrics computed from centralized SQL files:
1. Monthly Active Users (queries/monthly_active_users.sql)
2. Revenue by Geographic Segment (queries/revenue_by_segment.sql)
3. Conversion & Fulfillment Rates (queries/conversion_rate.sql)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "analytics.db"
QUERIES_DIR = PROJECT_ROOT / "queries"
OUTPUT_DIR = PROJECT_ROOT / "output" / "sql_metrics"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def ensure_database(db_url: str, processed_dir: Path) -> None:
    """Ensure database has required tables loaded before running metric queries."""
    engine = create_engine(db_url)
    inspector = inspect(engine)
    required_tables = ["orders", "order_payments", "customers"]
    missing = [t for t in required_tables if not inspector.has_table(t)]

    if missing:
        print(f"Tables missing ({missing}). Initializing database from {processed_dir}...")
        try:
            from scripts.database_integration import load_datasets_to_db
        except ModuleNotFoundError:
            from database_integration import load_datasets_to_db
        load_datasets_to_db(db_url, processed_dir)


def run_sql_query_file(engine: Any, query_file: Path) -> pd.DataFrame:
    """Read an SQL file and execute it using SQLAlchemy engine into a DataFrame."""
    if not query_file.exists():
        raise FileNotFoundError(f"Query file not found: {query_file}")
    with open(query_file, "r", encoding="utf-8") as f:
        sql_query = f.read()
    return pd.read_sql(sql_query, engine)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute centralized SQL business metrics against analytics database."
    )
    parser.add_argument("--db-file", type=Path, default=DB_PATH)
    parser.add_argument("--queries-dir", type=Path, default=QUERIES_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite:///{args.db_file}"

    print(f"Starting centralized SQL metrics pipeline (DB: {args.db_file.name})...")
    ensure_database(db_url, args.processed_dir)
    engine = create_engine(db_url)

    metrics_summary: dict[str, Any] = {
        "pipeline": "Centralized SQL Metrics",
        "database": str(args.db_file),
        "metrics_computed": {},
    }

    # 1. Monthly Active Users
    mau_file = args.queries_dir / "monthly_active_users.sql"
    print(f"Executing {mau_file.name}...")
    mau_df = run_sql_query_file(engine, mau_file)
    mau_out = args.output_dir / "monthly_active_users.csv"
    mau_df.to_csv(mau_out, index=False)
    print(f"✓ Saved {len(mau_df)} monthly active user records to {mau_out}")
    metrics_summary["metrics_computed"]["monthly_active_users"] = {
        "query_file": str(mau_file.name),
        "total_months": len(mau_df),
        "peak_active_users_month": str(mau_df.loc[mau_df["monthly_active_users"].idxmax(), "year_month"]),
        "peak_monthly_active_users": int(mau_df["monthly_active_users"].max()),
        "avg_monthly_active_users": float(mau_df["monthly_active_users"].mean().round(2)),
    }

    # 2. Revenue by Geographic Segment
    rev_file = args.queries_dir / "revenue_by_segment.sql"
    print(f"Executing {rev_file.name}...")
    rev_df = run_sql_query_file(engine, rev_file)
    rev_out = args.output_dir / "revenue_by_segment.csv"
    rev_df.to_csv(rev_out, index=False)
    print(f"✓ Saved {len(rev_df)} state segment records to {rev_out}")
    top_state = rev_df.iloc[0]
    metrics_summary["metrics_computed"]["revenue_by_segment"] = {
        "query_file": str(rev_file.name),
        "total_segments": len(rev_df),
        "top_state": str(top_state["customer_state"]),
        "top_state_revenue": float(top_state["total_revenue"]),
        "top_state_share_pct": float(round((top_state["total_revenue"] / rev_df["total_revenue"].sum()) * 100, 2)),
    }

    # 3. Conversion & Fulfillment Rate
    conv_file = args.queries_dir / "conversion_rate.sql"
    print(f"Executing {conv_file.name}...")
    conv_df = run_sql_query_file(engine, conv_file)
    conv_out = args.output_dir / "conversion_rate.csv"
    conv_df.to_csv(conv_out, index=False)
    print(f"✓ Saved {len(conv_df)} monthly lifecycle records to {conv_out}")
    metrics_summary["metrics_computed"]["conversion_rate"] = {
        "query_file": str(conv_file.name),
        "total_months": len(conv_df),
        "avg_fulfillment_rate_pct": float(conv_df["fulfillment_rate_pct"].mean().round(2)),
        "avg_cancellation_rate_pct": float(conv_df["cancellation_rate_pct"].mean().round(2)),
    }

    # Save summary report
    summary_json_file = args.output_dir / "metrics_summary.json"
    with open(summary_json_file, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
    print(f"✓ Saved metrics summary to {summary_json_file}")

    print("\n=======================================================")
    print("  Centralized SQL Metrics Summary")
    print("=======================================================")
    print(f"  • Monthly Active Users: {metrics_summary['metrics_computed']['monthly_active_users']['total_months']} months tracked | Peak: {metrics_summary['metrics_computed']['monthly_active_users']['peak_monthly_active_users']:,} users ({metrics_summary['metrics_computed']['monthly_active_users']['peak_active_users_month']})")
    print(f"  • Top Revenue Segment: {top_state['customer_state'].upper()} with {top_state['total_revenue']:,} BRL ({metrics_summary['metrics_computed']['revenue_by_segment']['top_state_share_pct']}% of total)")
    print(f"  • Average Fulfillment Rate: {metrics_summary['metrics_computed']['conversion_rate']['avg_fulfillment_rate_pct']}%")
    print("=======================================================")

    print("\nCentralized SQL metrics pipeline completed successfully!")


if __name__ == "__main__":
    main()
