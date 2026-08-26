from contextlib import contextmanager
from backend.settings import settings
import psycopg
from psycopg_pool import ConnectionPool

# Global connection pool
_pool = None

def init_pool():
    global _pool
    if _pool is None:
        _pool = ConnectionPool(conninfo=settings.database_url)

def close_pool():
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None

@contextmanager
def get_connection():
    if _pool is None:
        # Fallback for standalone scripts / pytest without lifespan
        with psycopg.connect(settings.database_url) as conn:
            yield conn
    else:
        with _pool.connection() as conn:
            yield conn

def init_db():
    """Initializes the database schema using Neon Postgres."""
    with get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
              device_id TEXT PRIMARY KEY,
              personas TEXT NOT NULL,
              health_flags TEXT NOT NULL,
              saved_locations TEXT,
              updated_at TEXT NOT NULL
            );
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS signal_cache (
              cache_key TEXT PRIMARY KEY,
              value_json TEXT NOT NULL,
              source TEXT NOT NULL,
              fetched_at TEXT NOT NULL,
              confidence REAL NOT NULL,
              freshness_min INTEGER
            );
        ''')
        conn.commit()

        # In case the table is altered since 14/15/16 docs had a slight difference
        # Execute each alter sequentially wrapped in a savepoint rollback wrapper
        for col, col_def in [("confidence", "REAL NOT NULL DEFAULT 1.0"), ("freshness_min", "INTEGER")]:
            try:
                with conn.transaction():
                    conn.execute(f"ALTER TABLE signal_cache ADD COLUMN {col} {col_def};")
            except psycopg.errors.DuplicateColumn:
                pass
