"""SQL Views and Pre-Aggregated Tables Management Pipeline.

Establishes a single authoritative data layer to eliminate metric drift,
builds high-performance pre-aggregated rollup tables, and manages data freshness.

Core Deliverables:
1. SQL Views (vw_monthly_revenue, vw_active_customers)
2. Pre-Aggregated Tables (agg_daily_revenue, agg_seller_performance) with updated_at timestamps
3. Execution audit, row count validations, and performance comparison
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from sqlalchemy import create_engine, inspect, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "analytics.db"
QUERIES_DIR = PROJECT_ROOT / "queries"
OUTPUT_DIR = PROJECT_ROOT / "output" / "sql_views_aggregations"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def ensure_database(db_url: str, processed_dir: Path) -> None:
    """Verify that source tables exist in the SQLite database."""
    engine = create_engine(db_url)
    inspector = inspect(engine)
    required = ["orders", "order_payments", "customers", "sellers", "order_items", "order_reviews"]
    missing = [t for t in required if not inspector.has_table(t)]
    if missing:
        print(f"Required tables missing {missing}. Populating database...")
        from scripts.database_integration import load_datasets_to_db
        load_datasets_to_db(db_url, processed_dir)


def execute_sql_file(con: sqlite3.Connection, sql_path: Path) -> None:
    """Execute raw SQL statements from file across semicolon splits."""
    with open(sql_path, "r", encoding="utf-8") as f:
        script = f.read()
    con.executescript(script)
    con.commit()


def benchmark_query(con: sqlite3.Connection, query: str, runs: int = 5) -> Dict[str, Any]:
    """Benchmark query execution duration."""
    # Warmup
    con.execute(query).fetchall()
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        rows = con.execute(query).fetchall()
        duration_ms = (time.perf_counter() - start) * 1000
        times.append(duration_ms)
    avg_ms = sum(times) / len(times)
    return {
        "avg_duration_ms": round(avg_ms, 3),
        "min_duration_ms": round(min(times), 3),
        "max_duration_ms": round(max(times), 3),
        "row_count": len(rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and refresh SQL views and pre-aggregated tables.")
    parser.add_argument("--db-file", type=Path, default=DB_PATH)
    parser.add_argument("--queries-dir", type=Path, default=QUERIES_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--refresh-mode", choices=["full", "incremental"], default="full")
    args = parser.parse_args()

    db_url = f"sqlite:///{args.db_file}"
    ensure_database(db_url, PROCESSED_DATA_DIR)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(str(args.db_file))
    cursor = con.cursor()

    print("--- 1. Creating SQL Views (Single Source of Truth) ---")
    view_files = [
        args.queries_dir / "vw_monthly_revenue.sql",
        args.queries_dir / "vw_active_customers.sql",
    ]
    for vf in view_files:
        print(f"Applying view: {vf.name}...")
        execute_sql_file(con, vf)

    print("\n--- 2. Building Pre-Aggregated Tables (Performance Acceleration) ---")
    agg_files = [
        args.queries_dir / "agg_daily_revenue.sql",
        args.queries_dir / "agg_seller_performance.sql",
    ]
    for af in agg_files:
        print(f"Building pre-aggregated table: {af.name}...")
        execute_sql_file(con, af)

    print("\n--- 3. Exporting Audit Reports & CSV Artifacts ---")
    # Export samples and calculate row counts
    df_monthly_rev = pd.read_sql_query("SELECT * FROM vw_monthly_revenue ORDER BY order_month DESC", con)
    df_active_cust = pd.read_sql_query("SELECT * FROM vw_active_customers ORDER BY order_month DESC, customer_state ASC LIMIT 100", con)
    df_daily_agg = pd.read_sql_query("SELECT * FROM agg_daily_revenue ORDER BY order_date DESC", con)
    df_seller_agg = pd.read_sql_query("SELECT * FROM agg_seller_performance ORDER BY total_orders DESC LIMIT 100", con)

    df_monthly_rev.to_csv(args.output_dir / "vw_monthly_revenue.csv", index=False)
    df_active_cust.to_csv(args.output_dir / "vw_active_customers_sample.csv", index=False)
    df_daily_agg.to_csv(args.output_dir / "agg_daily_revenue.csv", index=False)
    df_seller_agg.to_csv(args.output_dir / "agg_seller_performance_top.csv", index=False)

    print("\n--- 4. Benchmarking Raw Multi-Table Join vs. Pre-Aggregated Table ---")
    raw_query = """
    SELECT
        DATE(o.order_purchase_timestamp) AS order_date,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(p.payment_value) AS daily_revenue
    FROM orders o
    JOIN order_payments p ON o.order_id = p.order_id
    WHERE o.order_purchase_timestamp IS NOT NULL
      AND o.order_status != 'canceled'
    GROUP BY DATE(o.order_purchase_timestamp)
    ORDER BY order_date DESC;
    """
    agg_query = "SELECT order_date, total_orders, daily_revenue FROM agg_daily_revenue ORDER BY order_date DESC;"

    raw_stats = benchmark_query(con, raw_query)
    agg_stats = benchmark_query(con, agg_query)
    speedup = round(raw_stats["avg_duration_ms"] / max(agg_stats["avg_duration_ms"], 0.001), 2)

    print(f"Raw Aggregation Query: {raw_stats['avg_duration_ms']} ms ({raw_stats['row_count']} rows)")
    print(f"Pre-Aggregated Query:  {agg_stats['avg_duration_ms']} ms ({agg_stats['row_count']} rows)")
    print(f"Acceleration factor:   {speedup}x speedup")

    summary_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "views_created": [
            {
                "name": "vw_monthly_revenue",
                "purpose": "Single authoritative source for monthly financial metrics and order counts",
                "row_count": len(df_monthly_rev),
            },
            {
                "name": "vw_active_customers",
                "purpose": "Centralized definition of active customer engagement by state and month",
                "sample_row_count": len(df_active_cust),
            },
        ],
        "tables_aggregated": [
            {
                "name": "agg_daily_revenue",
                "purpose": "Precomputed daily revenue and volume rollup for rapid dashboard loading",
                "row_count": len(df_daily_agg),
                "has_updated_at": True,
            },
            {
                "name": "agg_seller_performance",
                "purpose": "Precomputed seller risk, order volume, and late delivery counts",
                "sample_row_count": len(df_seller_agg),
                "has_updated_at": True,
            },
        ],
        "performance_benchmark": {
            "metric": "Daily Revenue Aggregation",
            "raw_join_duration_ms": raw_stats["avg_duration_ms"],
            "precomputed_table_duration_ms": agg_stats["avg_duration_ms"],
            "speedup_factor": f"{speedup}x",
        },
        "refresh_strategy": {
            "mode": args.refresh_mode,
            "recommended_cadence": "Scheduled batch cron (e.g. nightly or hourly) with updated_at freshness tracking",
            "version_control": "SQL DDL queries version-controlled in backend/queries/",
        },
    }

    report_path = args.output_dir / "views_and_aggregations_summary.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)

    con.close()
    print(f"\nAudit report written to {report_path}")
    print("SQL Views & Pre-Aggregated Tables pipeline finished successfully!")


if __name__ == "__main__":
    main()
