
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import execute_query

def clear_users():
    print("WARNING: This will delete ALL users and their data.")
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm != 'DELETE':
        print("Operation cancelled.")
        return

    try:
        print("Deleting habit_logs...")
        execute_query("DELETE FROM habit_logs")
        
        print("Deleting habits...")
        execute_query("DELETE FROM habits")
        
        print("Deleting tasks...")
        execute_query("DELETE FROM tasks")
        
        print("Deleting users...")
        execute_query("DELETE FROM users")
        
        print("✅ All user data has been removed successfully.")
        
    except Exception as e:
        print(f"❌ Error clearing data: {e}")

if __name__ == "__main__":
    clear_users()
