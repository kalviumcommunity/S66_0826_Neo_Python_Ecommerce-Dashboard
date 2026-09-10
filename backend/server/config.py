"""Configuration settings for the Backend Server."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directories
SERVER_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SERVER_DIR.parent
DATA_DIR = BACKEND_DIR / "data"

# Load environment variables from backend/.env if present
load_dotenv(BACKEND_DIR / ".env")

# Database & Data Paths
DB_PATH = SERVER_DIR / "analytics.db"
if not DB_PATH.exists() and (DATA_DIR / "analytics.db").exists():
    DB_PATH = DATA_DIR / "analytics.db"

PROCESSED_DATA_DIR = DATA_DIR / "processed"
QUERIES_DIR = BACKEND_DIR / "queries"
OUTPUT_DIR = BACKEND_DIR / "output"
KPI_RESULTS_FILE = OUTPUT_DIR / "kpi_report" / "kpi_results.json"

# Database connection string
_raw_db_url = os.getenv("DATABASE_URL")
if not _raw_db_url:
    DATABASE_URL = f"sqlite:///{DB_PATH}"
elif _raw_db_url.startswith("sqlite:///") and not _raw_db_url.startswith("sqlite:////"):
    _rel_sqlite_path = _raw_db_url.replace("sqlite:///", "", 1)
    DATABASE_URL = f"sqlite:///{BACKEND_DIR / _rel_sqlite_path}"
else:
    DATABASE_URL = _raw_db_url

# Risk Scoring Configuration adhering to DASHBOARD_THINKING.md
RISK_THRESHOLD_LOW = 30.0
RISK_THRESHOLD_MEDIUM = 70.0
SPARSE_ORDER_THRESHOLD = 5

# Bayesian Smoothing Parameters for Small/New Sellers
PRIOR_DELIVERY_WEIGHT = 10.0
PRIOR_LATE_RATE = 0.0811  # Platform baseline late delivery rate (~8.11%)
PRIOR_REVIEW_WEIGHT = 5.0
PRIOR_REVIEW_SCORE = 4.09  # Platform baseline review score (~4.09)

# KPI Reference Targets
TARGET_REVIEW_SCORE = 4.0
TARGET_LATE_DELIVERY_PCT = 10.0
TARGET_CANCELLATION_RATE = 1.5
