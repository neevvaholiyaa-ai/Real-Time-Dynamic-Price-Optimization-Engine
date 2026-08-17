"""
Database abstraction layer supporting SQLite for local development and PostgreSQL for production.
Provides unified query execution with automatic parameter dialect conversion and table initialization.
"""
import os
import sqlite3
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

DEFAULT_SQLITE_PATH = DATA_DIR / "auraprice.db"
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

def is_postgres() -> bool:
    return DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

def get_sqlite_path() -> str:
    if DATABASE_URL.startswith("sqlite:///"):
        return DATABASE_URL.replace("sqlite:///", "")
    return str(DEFAULT_SQLITE_PATH)

@contextmanager
def get_db_connection():
    """
    Yields a connection object with row factory set to return dictionary-like rows.
    """
    if is_postgres():
        try:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        except ImportError:
            raise RuntimeError("psycopg2 is required when connecting to PostgreSQL. Install psycopg2-binary.")
    else:
        db_path = get_sqlite_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

def _convert_query(query: str) -> str:
    """
    Converts '?' placeholders to '%s' if running on PostgreSQL.
    """
    if is_postgres():
        return query.replace("?", "%s")
    return query

def execute_query(query: str, params: Tuple = ()) -> None:
    """Executes an INSERT/UPDATE/DELETE query."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        converted = _convert_query(query)
        cursor.execute(converted, params)

def fetch_one(query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
    """Executes a SELECT query and returns a single row as a dict, or None."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        converted = _convert_query(query)
        cursor.execute(converted, params)
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)

def fetch_all(query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    """Executes a SELECT query and returns all rows as a list of dicts."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        converted = _convert_query(query)
        cursor.execute(converted, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def init_db() -> None:
    """Initializes the database schema if tables do not exist."""
    schema_statements = [
        # Users Table
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        # Products Table (user-owned, non-essential fields nullable)
        """
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT,
            brand TEXT,
            sku TEXT,
            location TEXT,
            cost_price REAL NOT NULL,
            current_price REAL NOT NULL,
            mrp REAL NOT NULL,
            minimum_price REAL,
            maximum_price REAL,
            target_margin REAL,
            stock_quantity INTEGER,
            average_daily_sales REAL,
            reorder_threshold INTEGER,
            competitor_price REAL,
            competitor_name TEXT,
            business_goal TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """,
        # Pricing Analyses Table
        """
        CREATE TABLE IF NOT EXISTS pricing_analyses (
            analysis_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            input_cost_price REAL,
            input_current_price REAL,
            input_mrp REAL,
            input_competitor_price REAL,
            input_stock_quantity INTEGER,
            input_daily_orders REAL,
            recommended_price REAL NOT NULL,
            price_change REAL,
            price_change_pct REAL,
            recommendation TEXT,
            margin_current_pct REAL,
            margin_recommended_pct REAL,
            margin_lift_pct REAL,
            competitor_gap_pct REAL,
            stock_runway_days REAL,
            expected_demand REAL,
            expected_revenue_30d REAL,
            expected_profit_30d REAL,
            confidence_level TEXT,
            confidence_details TEXT,
            guardrail_applied INTEGER DEFAULT 0,
            guardrail_details TEXT,
            min_allowed_price REAL,
            max_allowed_price REAL,
            insights TEXT,
            economic_drivers TEXT,
            feature_provenance TEXT,
            status TEXT DEFAULT 'pending',
            applied_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        );
        """,
        # Sales History Table (Actual historical data)
        """
        CREATE TABLE IF NOT EXISTS sales_history (
            record_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            period_date TEXT NOT NULL,
            units_sold INTEGER,
            selling_price REAL,
            revenue REAL,
            cost REAL,
            profit REAL,
            source TEXT DEFAULT 'user_input',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        );
        """,
        # Pricing History Table (Created when recommendation is applied)
        """
        CREATE TABLE IF NOT EXISTS pricing_history (
            history_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            analysis_id TEXT,
            old_price REAL NOT NULL,
            new_price REAL NOT NULL,
            change_pct REAL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        );
        """,
        # User Settings & Guardrails Table
        """
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            margin_floor_pct REAL DEFAULT 5.5,
            corridor_min_pct REAL DEFAULT -25.0,
            corridor_max_pct REAL DEFAULT 25.0,
            max_discount_pct REAL DEFAULT 40.0,
            max_price_change_pct REAL DEFAULT 15.0,
            never_below_cost INTEGER DEFAULT 1,
            never_above_mrp INTEGER DEFAULT 1,
            custom_price_floor REAL,
            custom_price_ceiling REAL,
            currency TEXT DEFAULT 'INR',
            store_name TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """
    ]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for stmt in schema_statements:
            cursor.execute(stmt)
        # Create indexes for fast lookup
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_user ON products(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_analyses_user ON pricing_analyses(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_analyses_product ON pricing_analyses(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_analyses_status ON pricing_analyses(user_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_sales_user ON sales_history(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_sales_product ON sales_history(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_history_user ON pricing_history(user_id);"
        ]
        for idx in indexes:
            try:
                cursor.execute(idx)
            except Exception:
                pass

# Initialize DB when module is imported
init_db()
