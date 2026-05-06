"""
Database connection layer — SQLite locally, PostgreSQL on Railway.
Import from here instead of importing sqlite3 directly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Railway uses postgres:// but SQLAlchemy needs postgresql://
_raw = os.getenv("DATABASE_URL", "")
DATABASE_URL = _raw.replace("postgres://", "postgresql://", 1) if _raw else ""
IS_POSTGRES  = bool(DATABASE_URL)

DB_PATH = Path(os.getenv("DB_PATH", str(Path(__file__).parent.parent / "data" / "traffic.db")))

# Dialect shortcuts
PH = "%s" if IS_POSTGRES else "?"
AI = "SERIAL PRIMARY KEY" if IS_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"


def get_conn():
    """Raw DB connection — use for writes."""
    if IS_POSTGRES:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    DB_PATH.parent.mkdir(exist_ok=True)
    import sqlite3
    return sqlite3.connect(str(DB_PATH))


def get_engine():
    """SQLAlchemy engine — use for pd.read_sql."""
    from sqlalchemy import create_engine
    if IS_POSTGRES:
        return create_engine(DATABASE_URL)
    DB_PATH.parent.mkdir(exist_ok=True)
    return create_engine(f"sqlite:///{DB_PATH}")


def execute(conn, sql, params=None):
    """Run a single write statement."""
    if IS_POSTGRES:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        cur.close()
    else:
        conn.execute(sql, params or ())
        conn.commit()


def executemany(conn, sql, rows):
    """Run a write statement for each row."""
    if IS_POSTGRES:
        cur = conn.cursor()
        cur.executemany(sql, rows)
        conn.commit()
        cur.close()
    else:
        conn.executemany(sql, rows)
        conn.commit()


def fetchone(conn, sql, params=None):
    """Fetch a single row."""
    if IS_POSTGRES:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        row = cur.fetchone()
        cur.close()
        return row
    return conn.execute(sql, params or ()).fetchone()
