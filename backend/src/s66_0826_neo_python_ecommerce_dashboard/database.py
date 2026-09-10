"""Database connection, session management, and unified query execution."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from s66_0826_neo_python_ecommerce_dashboard.config import DATABASE_URL


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
