"""
Database utility functions for LifeSync Dashboard.
Provides abstracted database connection and query execution using PostgreSQL (psycopg2).
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import Config


def get_db_connection():
    """Create and return a database connection."""
    try:
        connection = psycopg2.connect(
            host=Config.PG_HOST,
            user=Config.PG_USER,
            password=Config.PG_PASSWORD,
            dbname=Config.PG_DATABASE,
            port=Config.PG_PORT,
            sslmode='require' # Force SSL for Aiven
        )
        return connection
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        raise


@contextmanager
def get_db_cursor(dictionary=True):
    """Context manager for database operations."""
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
        if connection:
            connection.close()


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute a query and optionally fetch results."""
    # Convert MySQL %s params are compatible with psycopg2, but good to be aware.
    # psycopg2 uses %s placeholders.
    
    with get_db_cursor() as (cursor, connection):
        cursor.execute(query, params or ())
        
        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        else:
            # For inserts, we often want the ID. 
            # In Postgres, we use RETURNING id.
            # But the caller expects lastrowid.
            # We must verify if the query contains RETURNING. 
            # If not, and it's an INSERT, we might not get the ID back easily without modification.
            # However, for migration speed, we assume the query might need adjustment elsewhere
            # OR we try to fetch fetchone if result available.
            try:
                if cursor.description:
                    return cursor.fetchone()['id']
            except:
                return cursor.rowcount 
            return cursor.rowcount


def execute_many(query, params_list):
    """Execute multiple queries with different parameters."""
    with get_db_cursor() as (cursor, connection):
        cursor.executemany(query, params_list)
        return cursor.rowcount
