
import sys
import os
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from flask_login import UserMixin

# Mock config
class Config:
    SECRET_KEY = 'test'
    PG_HOST = os.getenv('PG_HOST', 'localhost')
    PG_USER = os.getenv('PG_USER', 'postgres')
    PG_PASSWORD = os.getenv('PG_PASSWORD', 'password')
    PG_DATABASE = os.getenv('PG_DATABASE', 'lifesync_db')
    PG_PORT = int(os.getenv('PG_PORT', 5432))

# Mock app structure
from backend.routes.analytics import analytics_bp
from backend.utils.db import execute_query

# Create app
app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(analytics_bp)

# Mock Login
class User(UserMixin):
    id = 1  # Assuming user ID 1 exists from debug_data output

# Patch current_user
import flask_login
flask_login.current_user = User()

def test_endpoints():
    print("--- Testing Analytics Optimization ---")
    
    with app.test_request_context('/api/analytics/weekly'):
        try:
            from backend.routes.analytics import get_weekly_stats
            print("\nCalling get_weekly_stats...")
            response, status = get_weekly_stats()
            print(f"Status: {status}")
            data = response.get_json()
            if data['success']:
                print("✅ Success!")
                print("Daily Stats:", len(data['daily_stats']))
                print("Weekly Percentage:", data['weekly_percentage'])
            else:
                print("❌ Failed:", data.get('message'))
        except Exception as e:
            print(f"❌ Error in weekly: {e}")
            import traceback
            traceback.print_exc()

    with app.test_request_context('/api/analytics/streaks'):
        try:
            from backend.routes.analytics import get_streaks
            print("\nCalling get_streaks...")
            response, status = get_streaks()
            print(f"Status: {status}")
            data = response.get_json()
            if data['success']:
                print("✅ Success!")
                print("Habits Count:", len(data['habits']))
                print("Total Current Streak:", data['totals']['total_current_streak'])
            else:
                print("❌ Failed:", data.get('message'))
        except Exception as e:
            print(f"❌ Error in streaks: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_endpoints()
