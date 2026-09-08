"""Configuration settings for the Seller Trust & Safety API."""

from __future__ import annotations

import os
from pathlib import Path

# Base directories
PACKAGE_DIR = Path(__file__).resolve().parent
SRC_DIR = PACKAGE_DIR.parent
BACKEND_DIR = SRC_DIR.parent

# Database & Data Paths
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = DATA_DIR / "analytics.db"
OUTPUT_DIR = BACKEND_DIR / "output"
KPI_RESULTS_FILE = OUTPUT_DIR / "kpi_report" / "kpi_results.json"

# SQLite connection string
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Risk Scoring Configuration adhering to DASHBOARD_THINKING.md
RISK_THRESHOLD_LOW = 30.0
RISK_THRESHOLD_MEDIUM = 70.0
SPARSE_ORDER_THRESHOLD = 5

# KPI Reference Targets
TARGET_REVIEW_SCORE = 4.0
TARGET_LATE_DELIVERY_PCT = 10.0
TARGET_CANCELLATION_RATE = 1.5
