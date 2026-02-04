# LifeSync Terminal Commands

Here are the essential commands for managing your LifeSync application.

## 1. Database Operations

### 🔍 View Data (Debug)
See what is currently inside the database (Users, Habits, Tasks).
```powershell
python backend/debug_data.py
```

### 🛠️ Initialize / Reset Database (Migration)
Creates the necessary tables if they don't exist. Useful for first-time setup or if you dropped tables.
```powershell
python backend/migrate_db.py
```

### 🚀 Optimize Database
Creates indexes to make queries faster. Run this periodically or after setup.
```powershell
python backend/optimize_db.py
```

### ⚠️ Clear All User Data (DANGER)
**WARNING**: This deletes ALL users, habits, and tasks. Use only for testing.
```powershell
python backend/clear_users.py
```

## 2. Running the Application

### 🟢 Start Backend Server
Starts the Flask API server.
```powershell
cd backend
python app.py
```

## 3. Environment Setup
Install required Python libraries.
```powershell
pip install -r backend/requirements.txt
```
