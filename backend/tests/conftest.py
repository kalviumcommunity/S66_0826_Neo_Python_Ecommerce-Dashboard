"""Pytest configuration and session fixtures."""

from __future__ import annotations

import pandas as pd
import pytest
from sqlalchemy import inspect, text

from s66_0826_neo_python_ecommerce_dashboard.config import (
    DATA_DIR,
    PROCESSED_DATA_DIR,
    QUERIES_DIR,
)
from s66_0826_neo_python_ecommerce_dashboard.database import engine

REQUIRED_TEST_TABLES = [
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


@pytest.fixture(scope="session", autouse=True)
def ensure_database_initialized() -> None:
    """Ensure database has all required tables loaded before running test suite in CI."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    missing = [t for t in REQUIRED_TEST_TABLES if t not in existing_tables]

    if not missing:
        return

    print(f"\n[CI/Test Fixture] Database tables missing ({missing}). Initializing test tables...")

    for csv_file, table_name in TABLE_CSV_MAPPING.items():
        if table_name not in existing_tables:
            csv_path = PROCESSED_DATA_DIR / csv_file
            if csv_path.exists():
                df = pd.read_csv(csv_path, low_memory=False)
                df.to_sql(table_name, engine, if_exists="replace", index=False)

    inspector = inspect(engine)
    if "agg_seller_performance" not in inspector.get_table_names():
        agg_script = QUERIES_DIR / "agg_seller_performance.sql"
        if agg_script.exists():
            with engine.begin() as conn:
                with open(agg_script, "r", encoding="utf-8") as f:
                    for statement in f.read().split(";"):
                        stmt = statement.strip()
                        if stmt:
                            conn.execute(text(stmt))

