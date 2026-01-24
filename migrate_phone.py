
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from utils.db import execute_query

def migrate():
    print("Running migration: Adding phone_number to users table...")
    try:
        # Check if column exists (simple way: select it, if fail, add it)
        # SQLite doesn't support IF NOT EXISTS in ALTER TABLE directly in all versions, 
        # but we can just try adding it and ignore error if it exists.
        
        query = "ALTER TABLE users ADD COLUMN phone_number TEXT;"
        execute_query(query)
        print("Migration successful: phone_number column added.")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "no such table" not in str(e).lower():
            print(f"Migration finished (might already exist): {e}")
        else:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
