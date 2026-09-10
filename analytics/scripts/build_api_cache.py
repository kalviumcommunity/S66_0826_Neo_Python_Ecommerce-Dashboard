"""Precompute seller-risk data so dashboard API reads are fast on SQLite."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# The cache writer updates the API's SQLite database in the sibling backend.
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from server.config import DATABASE_URL
from server.services.risk_service import compute_seller_risk_dataset


def refresh_api_cache() -> None:
    """Write risk, history, and category dashboard cache tables to SQLite."""
    sellers, history_by_seller, categories = compute_seller_risk_dataset()
    history_rows = [
        {"seller_id": seller_id, **point}
        for seller_id, points in history_by_seller.items()
        for point in points
    ]
    engine = create_engine(DATABASE_URL)

    sellers.to_sql("api_seller_risk", engine, if_exists="replace", index=False)
    pd.DataFrame(history_rows).to_sql("api_seller_risk_history", engine, if_exists="replace", index=False)
    pd.DataFrame(categories).to_sql("api_category_risk", engine, if_exists="replace", index=False)

    with engine.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_api_seller_risk_seller ON api_seller_risk(seller_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_api_history_seller_period ON api_seller_risk_history(seller_id, period)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_api_category_risk_category ON api_category_risk(category)"))


if __name__ == "__main__":
    refresh_api_cache()
    print("Dashboard API cache refreshed in server/analytics.db")
