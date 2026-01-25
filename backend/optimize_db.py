
import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

def optimize():
    print("="*50)
    print("🚀 Optimizing Database Performance")
    print("="*50)
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('PG_HOST'),
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD'),
            port=int(os.getenv('PG_PORT', 5432)),
            dbname=os.getenv('PG_DATABASE')
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        indexes = [
            # Optimize Habit Logs Joins
            "CREATE INDEX IF NOT EXISTS idx_habit_logs_habit_date ON habit_logs (habit_id, completed_date);",
            
            # Optimize Habit Filtering
            "CREATE INDEX IF NOT EXISTS idx_habits_user_active ON habits (user_id, is_active);",
            
            # Optimize Task Date Filtering
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_date ON tasks (user_id, due_date);",
            
            # Optimize Task Completion Filtering
            "CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks (is_completed);"
        ]
        
        print("📊 Creating Indexes...")
        for idx in indexes:
            try:
                print(f"   👉 Executing: {idx}")
                cursor.execute(idx)
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
                
        print("\n✅ Optimization Complete! Database indexes applied.")
        
    except Exception as e:
        print(f"❌ Failed to connect or optimize: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    optimize()
