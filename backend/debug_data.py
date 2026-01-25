
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import execute_query
from datetime import datetime

def check_data():
    try:
        print("--- Checking Users ---")
        users = execute_query("SELECT id, username, email FROM users", fetch_all=True)
        if not users:
            print("No users found.")
            return

        for user in users:
            print(f"\nUser: {user['username']} (ID: {user['id']})")
            
            # Check Habits
            habits = execute_query("SELECT id, name, is_active FROM habits WHERE user_id = %s", (user['id'],), fetch_all=True)
            print(f"  Habits: {len(habits)}")
            for h in habits:
                print(f"    - {h['name']} (Active: {h['is_active']})")
                
                # Check Logs for this habit
                logs = execute_query("SELECT completed_date FROM habit_logs WHERE habit_id = %s ORDER BY completed_date DESC LIMIT 5", (h['id'],), fetch_all=True)
                print(f"      Logs ({len(logs)} recent): {[l['completed_date'] for l in logs]}")

            # Check Tasks
            tasks = execute_query("SELECT id, title, is_completed, due_date FROM tasks WHERE user_id = %s ORDER BY created_at DESC LIMIT 5", (user['id'],), fetch_all=True)
            print(f"  Tasks ({len(tasks)} recent):")
            for t in tasks:
                print(f"    - {t['title']} (Done: {t['is_completed']}, Due: {t['due_date']})")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_data()
