"""
Task model for LifeSync Dashboard.
"""
from datetime import date, datetime
import sys
sys.path.append('..')
from utils.db import execute_query


class Task:
    """Task model for managing daily tasks."""
    
    def __init__(self, id=None, user_id=None, title=None, description=None,
                 is_completed=False, due_date=None, priority='medium',
                 category='general', created_at=None, completed_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.is_completed = is_completed
        self.due_date = due_date
        self.priority = priority
        self.category = category
        self.created_at = created_at
        self.completed_at = completed_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """Convert task to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'is_completed': self.is_completed,
            'due_date': str(self.due_date) if self.due_date else None,
            'priority': self.priority,
            'category': self.category,
            'created_at': str(self.created_at) if self.created_at else None,
            'completed_at': str(self.completed_at) if self.completed_at else None
        }
    
    @staticmethod
    def create(user_id, title, description=None, due_date=None, priority='medium', category='general'):
        """Create a new task."""
        query = """
            INSERT INTO tasks (user_id, title, description, due_date, priority, category)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """
        task_id = execute_query(query, (user_id, title, description, due_date, priority, category), fetch_one=True)['id']
        return Task.get_by_id(task_id)
    
    @staticmethod
    def get_by_id(task_id):
        """Get task by ID."""
        query = "SELECT * FROM tasks WHERE id = %s"
        result = execute_query(query, (task_id,), fetch_one=True)
        if result:
            return Task(**result)
        return None
    
    @staticmethod
    def get_all_by_user(user_id, include_completed=True, target_date=None):
        """Get all tasks for a user."""
        if target_date:
            if include_completed:
                query = """
                    SELECT * FROM tasks 
                    WHERE user_id = %s AND (due_date = %s OR due_date IS NULL)
                    ORDER BY is_completed, priority DESC, created_at DESC
                """
                params = (user_id, target_date)
            else:
                query = """
                    SELECT * FROM tasks 
                    WHERE user_id = %s AND is_completed = FALSE AND (due_date = %s OR due_date IS NULL)
                    ORDER BY priority DESC, created_at DESC
                """
                params = (user_id, target_date)
        else:
            if include_completed:
                query = """
                    SELECT * FROM tasks 
                    WHERE user_id = %s
                    ORDER BY is_completed, due_date, priority DESC, created_at DESC
                """
                params = (user_id,)
            else:
                query = """
                    SELECT * FROM tasks 
                    WHERE user_id = %s AND is_completed = FALSE
                    ORDER BY due_date, priority DESC, created_at DESC
                """
                params = (user_id,)
        
        results = execute_query(query, params, fetch_all=True)
        return [Task(**r).to_dict() for r in results]
    
    @staticmethod
    def get_by_date(user_id, target_date):
        """Get tasks for a specific date."""
        query = """
            SELECT * FROM tasks 
            WHERE user_id = %s AND due_date = %s
            ORDER BY is_completed, priority DESC, created_at DESC
        """
        results = execute_query(query, (user_id, target_date), fetch_all=True)
        return [Task(**r).to_dict() for r in results]
    
    def update(self, **kwargs):
        """Update task attributes."""
        allowed_fields = ['title', 'description', 'due_date', 'priority', 'category']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in kwargs:
                updates.append(f"{field} = %s")
                values.append(kwargs[field])
                setattr(self, field, kwargs[field])
        
        if updates:
            values.append(self.id)
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s"
            execute_query(query, tuple(values))
    
    def toggle_complete(self):
        """Toggle task completion status."""
        self.is_completed = not self.is_completed
        if self.is_completed:
            query = "UPDATE tasks SET is_completed = TRUE, completed_at = NOW() WHERE id = %s"
        else:
            query = "UPDATE tasks SET is_completed = FALSE, completed_at = NULL WHERE id = %s"
        execute_query(query, (self.id,))
        return self.is_completed
    
    def delete(self):
        """Delete the task."""
        query = "DELETE FROM tasks WHERE id = %s"
        execute_query(query, (self.id,))
    
    @staticmethod
    def get_stats_for_date(user_id, target_date):
        """Get task statistics for a specific date."""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END) as completed
            FROM tasks 
            WHERE user_id = %s AND due_date = %s
        """
        result = execute_query(query, (user_id, target_date), fetch_one=True)
        return {
            'total': result['total'] or 0,
            'completed': result['completed'] or 0,
            'percentage': round((result['completed'] or 0) / (result['total'] or 1) * 100, 1)
        }
    
    @staticmethod
    def get_dates_with_tasks(user_id, start_date=None, end_date=None):
        """Get all unique dates that have tasks for a user, with task counts."""
        if start_date and end_date:
            query = """
                SELECT 
                    due_date,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END) as completed
                FROM tasks 
                WHERE user_id = %s AND due_date IS NOT NULL 
                    AND due_date >= %s AND due_date <= %s
                GROUP BY due_date
                ORDER BY due_date
            """
            params = (user_id, start_date, end_date)
        else:
            query = """
                SELECT 
                    due_date,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END) as completed
                FROM tasks 
                WHERE user_id = %s AND due_date IS NOT NULL
                GROUP BY due_date
                ORDER BY due_date
            """
            params = (user_id,)
        
        results = execute_query(query, params, fetch_all=True)
        return [{
            'date': str(r['due_date']),
            'total': r['total'],
            'completed': r['completed'] or 0,
            'percentage': round((r['completed'] or 0) / r['total'] * 100, 1) if r['total'] > 0 else 0
        } for r in results]
    
    @staticmethod
    def get_overdue_tasks(user_id):
        """Get all incomplete tasks with due dates in the past."""
        query = """
            SELECT * FROM tasks 
            WHERE user_id = %s AND is_completed = FALSE 
                AND due_date < CURRENT_DATE
            ORDER BY due_date, priority DESC, created_at DESC
        """
        results = execute_query(query, (user_id,), fetch_all=True)
        return [Task(**r).to_dict() for r in results]
    
    @staticmethod
    def get_no_date_tasks(user_id):
        """Get all tasks without a due date (backlog)."""
        query = """
            SELECT * FROM tasks 
            WHERE user_id = %s AND due_date IS NULL
            ORDER BY priority DESC, created_at DESC
        """
        results = execute_query(query, (user_id,), fetch_all=True)
        return [Task(**r).to_dict() for r in results]
    
    @staticmethod
    def bulk_update_date(task_ids, new_date):
        """Update due_date for multiple tasks at once."""
        if not task_ids:
            return 0
        
        placeholders = ','.join(['%s'] * len(task_ids))
        query = f"""
            UPDATE tasks 
            SET due_date = %s 
            WHERE id IN ({placeholders})
        """
        params = [new_date] + list(task_ids)
        execute_query(query, tuple(params))
        return len(task_ids)
