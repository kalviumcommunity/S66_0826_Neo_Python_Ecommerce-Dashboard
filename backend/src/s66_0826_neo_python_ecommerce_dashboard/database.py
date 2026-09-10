"""Database connection, session management, and schema initialization."""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from s66_0826_neo_python_ecommerce_dashboard.config import (
    DATABASE_URL,
    DATA_DIR,
    DB_PATH,
    PROCESSED_DATA_DIR,
    QUERIES_DIR,
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

_init_lock = threading.Lock()

REQUIRED_TABLES = [
    "orders",
    "order_items",
    "order_payments",
    "customers",
    "sellers",
    "order_reviews",
    "products",
    "product_category_name_translation",
    "agg_seller_performance",
]

TABLE_CSV_MAPPING = {
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_customers_dataset.csv": "customers",
    "olist_sellers_dataset.csv": "sellers",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "product_category_name_translation.csv": "product_category_name_translation",
}


def init_db_if_needed() -> None:
    """Check whether required SQLite tables exist, and initialize them from processed CSVs if missing."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with _init_lock:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view');")
        existing_tables = {row[0] for row in cursor.fetchall()}
        missing = [t for t in REQUIRED_TABLES if t not in existing_tables]

        if not missing:
            conn.close()
            return

        print(f"Database tables missing ({missing}). Initializing SQLite database from processed CSVs...")

        # Load CSVs
        missing_csvs: list[str] = []
        for csv_file, table_name in TABLE_CSV_MAPPING.items():
            if table_name not in existing_tables:
                csv_path = PROCESSED_DATA_DIR / csv_file
                if not csv_path.exists():
                    missing_csvs.append(str(csv_path))
                    continue

                print(f"  Loading {csv_file} -> '{table_name}'...")
                df = pd.read_csv(csv_path, low_memory=False)
                df.to_sql(table_name, engine, if_exists="replace", index=False)

        if missing_csvs:
            conn.close()
            raise FileNotFoundError(
                "Missing processed CSV files required to initialize the database: " + ", ".join(missing_csvs)
            )

        # Create Views and Pre-Aggregated Tables
        scripts = [
            "vw_monthly_revenue.sql",
            "vw_active_customers.sql",
            "agg_daily_revenue.sql",
            "agg_seller_performance.sql",
        ]
        for script_name in scripts:
            script_path = QUERIES_DIR / script_name
            if script_path.exists():
                print(f"  Executing {script_name}...")
                with open(script_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())

        conn.commit()
        conn.close()
        print("✓ Database initialization complete.")


def safe_read_sql(query: str, conn: sqlite3.Connection, params: Any = None) -> pd.DataFrame:
    """Execute SQL query safely, returning a DataFrame or raising a clear HTTPException on missing schema."""
    try:
        return pd.read_sql_query(query, conn, params=params)
    except sqlite3.OperationalError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database schema error: {exc}. Please verify required tables exist.",
        ) from exc


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining a SQLAlchemy session."""
    init_db_if_needed()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_raw_sqlite() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for obtaining a raw sqlite3 connection with Row factory."""
    init_db_if_needed()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
