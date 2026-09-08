"""Pytest configuration and session fixtures."""

from __future__ import annotations

import pytest

from s66_0826_neo_python_ecommerce_dashboard.database import init_db_if_needed


@pytest.fixture(scope="session", autouse=True)
def ensure_database_initialized() -> None:
    """Ensure SQLite database has all required tables and views loaded before running test suite."""
    init_db_if_needed()
