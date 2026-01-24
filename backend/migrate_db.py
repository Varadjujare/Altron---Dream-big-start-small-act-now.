
import os
import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# SQL file path - Adjusted to step out of backend/ and into database/
SQL_FILE_PATH = Path(__file__).parent.parent / 'database' / 'sql_queries_pg.sql'

def get_connection(db_name=None):
    """Create a database connection."""
    try:
        connection = psycopg2.connect(
            host=os.getenv('PG_HOST'),
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD'),
            port=int(os.getenv('PG_PORT', 5432)),
            dbname=db_name or os.getenv('PG_DATABASE')
        )
        return connection
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def parse_sql_file(file_path):
    """Read and parse SQL file into individual statements."""
    if not os.path.exists(file_path):
        print(f"❌ SQL file not found at: {file_path}")
        return []
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    statements = []
    
    # Remove lines starting with --
    clean_lines = [line for line in content.splitlines() if not line.strip().startswith('--')]
    clean_content = '\n'.join(clean_lines)
    
    # Split by semicolon
    raw_statements = clean_content.split(';')
    
    for stmt in raw_statements:
        trimmed = stmt.strip()
        if trimmed:
            statements.append(trimmed)
            
    return statements

def migrate():
    print("="*50)
    print("🚀 Starting Database Migration to PostgreSQL")
    print("="*50)
    
    target_db = os.getenv('PG_DATABASE', 'lifesync_db')
    print(f"🎯 Target Database: {target_db}")

    print("🔌 Connecting to PostgreSQL server...")
    conn = get_connection(target_db)
    if not conn:
        print("❌ Could not connect to PostgreSQL server. Check your .env credentials.")
        return
    
    conn.autocommit = True # Useful for some DDL, though we can also commit.
    cursor = conn.cursor()
    
    try:
        statements = parse_sql_file(SQL_FILE_PATH)
        print(f"📄 Found {len(statements)} SQL statements.")
        
        executed_count = 0
        for i, statement in enumerate(statements):
            # Postgres doesn't need USE, we connected to DB.
            # Skip CREATE DATABASE if strict, but our script usually handles tables.
            stmt_upper = statement.upper()
            if stmt_upper.startswith("CREATE DATABASE") or stmt_upper.startswith("USE "):
                print(f"   ⏭️  Skipping DB setup command: {statement[:30]}...")
                continue
                
            try:
                cursor.execute(statement)
                # conn.commit() # autocommit matches simplified flow or commit after each
                # In psycopg2 with autocommit=True, no need to commit.
                # If autocommit is False (default), we must commit. It's safer to not rely on autocommit for DDL.
                conn.commit()
                executed_count += 1
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"   ⚠️  Object already exists (skipping)")
                    conn.rollback() # Important in PG to clear error state
                else:
                    print(f"   ⚠️  Error on statement {i+1}: {e}")
                    conn.rollback()

        print(f"\n✅ Migration script finished. Executed {executed_count} statements.")
        
        # Verify
        print("\n🔍 Verifying tables...")
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"📊 Found tables in '{target_db}': {', '.join(tables)}")
        
        if 'users' in tables and 'habits' in tables:
            print("\n🎉 SUCCESS: Database initialized and ready!")
        else:
            print("\n⚠️  WARNING: key tables missing. Check logs.")

    except Exception as e:
        print(f"❌ Fatal error during migration: {e}")
    finally:
        if conn:
            conn.close()
            print("🔌 Connection closed.")

if __name__ == "__main__":
    migrate()
