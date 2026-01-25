"""
Database utility functions for LifeSync Dashboard.
Provides abstracted database connection and query execution using PostgreSQL (psycopg2)
with ThreadedConnectionPool for high performance.
"""
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import Config
import time

# Global connection pool
_db_pool = None

def init_db_pool():
    """Initialize the database connection pool."""
    global _db_pool
    if _db_pool is None:
        try:
            print(f"🔌 Initializing DB Pool: {Config.PG_HOST}...")
            _db_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                host=Config.PG_HOST,
                user=Config.PG_USER,
                password=Config.PG_PASSWORD,
                dbname=Config.PG_DATABASE,
                port=Config.PG_PORT,
                sslmode='require',  # Force SSL for Aiven/Neon/Supabase
                connect_timeout=10
            )
            print("✅ DB Pool created successfully")
        except Exception as e:
            print(f"❌ Error creating DB pool: {e}")
            import traceback
            traceback.print_exc()
            raise

def get_db_connection():
    """Get a connection from the pool."""
    global _db_pool
    if _db_pool is None:
        init_db_pool()
    
    try:
        connection = _db_pool.getconn()
        return connection
    except Exception as e:
        print(f"❌ Error getting connection from pool: {e}")
        # Try to re-initialize pool if it failed
        if _db_pool is None or _db_pool.closed:
             init_db_pool()
             return _db_pool.getconn()
        raise

@contextmanager
def get_db_cursor(dictionary=True):
    """Context manager for database operations using connection pool."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        # RealDictCursor allows accessing columns by name
        cursor_factory = RealDictCursor if dictionary else None
        cursor = connection.cursor(cursor_factory=cursor_factory)
        yield cursor, connection
        connection.commit()
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if connection and _db_pool:
            # Return connection to the pool instead of closing it
            _db_pool.putconn(connection)

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute a query and optionally fetch results."""
    with get_db_cursor() as (cursor, connection):
        cursor.execute(query, params or ())
        
        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        else:
            # Handle INSERT RETURNING id
            try:
                if cursor.description:
                    row = cursor.fetchone()
                    if row and 'id' in row:
                        return row['id']
                    return row
            except Exception:
                pass
            return cursor.rowcount

def execute_many(query, params_list):
    """Execute multiple queries with different parameters."""
    with get_db_cursor() as (cursor, connection):
        cursor.executemany(query, params_list)
        return cursor.rowcount

def close_pool():
    """Close the connection pool (application shutdown)."""
    global _db_pool
    if _db_pool:
        _db_pool.closeall()
        print("🔌 DB Pool closed")
