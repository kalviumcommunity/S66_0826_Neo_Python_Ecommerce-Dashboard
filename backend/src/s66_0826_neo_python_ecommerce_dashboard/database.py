"""Database connection, session management, and unified query execution."""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from s66_0826_neo_python_ecommerce_dashboard.config import (
    DATABASE_URL,
    DATA_DIR,
    DB_PATH,
    PROCESSED_DATA_DIR,
    QUERIES_DIR,
)

# Create a single unified SQLAlchemy Engine
is_sqlite = "sqlite" in DATABASE_URL
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    pool_pre_ping=True,
    **({} if is_sqlite else {"pool_size": 10, "max_overflow": 20}),
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
    """One-time fallback for testing or fresh environments if tables do not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with _init_lock:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        missing = [t for t in REQUIRED_TABLES if t not in existing_tables]

        if not missing:
            return

        print(f"Database tables missing ({missing}). Initializing database...")

        # Load CSVs
        for csv_file, table_name in TABLE_CSV_MAPPING.items():
            if table_name not in existing_tables:
                csv_path = PROCESSED_DATA_DIR / csv_file
                if csv_path.exists():
                    print(f"  Loading {csv_file} -> '{table_name}'...")
                    df = pd.read_csv(csv_path, low_memory=False)
                    df.to_sql(table_name, engine, if_exists="replace", index=False)

        # Re-check inspector for agg_seller_performance
        inspector = inspect(engine)
        if "agg_seller_performance" not in inspector.get_table_names():
            agg_script = QUERIES_DIR / "agg_seller_performance.sql"
            if agg_script.exists():
                print("  Executing agg_seller_performance.sql...")
                with engine.begin() as conn:
                    with open(agg_script, "r", encoding="utf-8") as f:
                        for statement in f.read().split(";"):
                            stmt = statement.strip()
                            if stmt:
                                conn.execute(text(stmt))

        print("✓ Database initialization complete.")


def safe_read_sql(query: str, conn: Any, params: Any = None) -> pd.DataFrame:
    """Execute SQL query safely through SQLAlchemy connection, returning a DataFrame."""
    try:
        if isinstance(query, str):
            # Use SQLAlchemy text() for parameter safety and cross-dialect compatibility
            sql_stmt = text(query)
        else:
            sql_stmt = query
        return pd.read_sql_query(sql_stmt, conn, params=params)
    except (sqlite3.OperationalError, SQLAlchemyError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database query error: {exc}. Please verify schema and connection.",
        ) from exc


@contextmanager
def get_db_connection() -> Generator[Any, None, None]:
    """Single unified context manager for obtaining a database connection from the connection pool."""
    with engine.connect() as conn:
        yield conn


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining a SQLAlchemy ORM session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
