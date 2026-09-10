"""Pytest configuration and session fixtures."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect

from server.database import engine

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

@pytest.fixture(scope="session", autouse=True)
def require_versioned_server_database() -> None:
    """Require the committed SQLite database; tests never load CSV fallback data."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    missing = [t for t in REQUIRED_TEST_TABLES if t not in existing_tables]

    if missing:
        pytest.fail(
            "The versioned server SQLite database is incomplete; missing tables: "
            + ", ".join(missing)
        )
