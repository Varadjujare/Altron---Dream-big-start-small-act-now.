"""
Habit model for LifeSync Dashboard.
"""
from datetime import date, datetime
import sys
sys.path.append('..')
from utils.db import execute_query, get_db_cursor


class Habit:
    """Habit model for tracking daily habits."""
    
    def __init__(self, id=None, user_id=None, name=None, description=None,
                 color='#4CAF50', icon='✓', is_active=True, sort_order=0,
                 created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.description = description
        self.color = color
        self.icon = icon
        self.is_active = is_active
        self.sort_order = sort_order
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """Convert habit to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': str(self.created_at) if self.created_at else None
        }
    
    @staticmethod
    def create(user_id, name, description=None, color='#4CAF50', icon='✓'):
        """Create a new habit."""
        query = """
            INSERT INTO habits (user_id, name, description, color, icon)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """
        habit_id = execute_query(query, (user_id, name, description, color, icon), fetch_one=True)['id']
        return Habit.get_by_id(habit_id)
    
    @staticmethod
    def get_by_id(habit_id):
        """Get habit by ID."""
        query = "SELECT * FROM habits WHERE id = %s"
        result = execute_query(query, (habit_id,), fetch_one=True)
        if result:
            return Habit(**result)
        return None
    
    @staticmethod
    def get_all_by_user(user_id, active_only=True):
        """Get all habits for a user."""
        if active_only:
            query = "SELECT * FROM habits WHERE user_id = %s AND is_active = TRUE ORDER BY sort_order, id"
        else:
            query = "SELECT * FROM habits WHERE user_id = %s ORDER BY sort_order, id"
        results = execute_query(query, (user_id,), fetch_all=True)
        return [Habit(**r).to_dict() for r in results]
    
    def update(self, **kwargs):
        """Update habit attributes."""
        allowed_fields = ['name', 'description', 'color', 'icon', 'is_active', 'sort_order']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in kwargs:
                updates.append(f"{field} = %s")
                values.append(kwargs[field])
                setattr(self, field, kwargs[field])
        
        if updates:
            values.append(self.id)
            query = f"UPDATE habits SET {', '.join(updates)} WHERE id = %s"
            execute_query(query, tuple(values))
    
    def delete(self):
        """Delete the habit."""
        query = "DELETE FROM habits WHERE id = %s"
        execute_query(query, (self.id,))
    
    # Habit Logging Methods
    @staticmethod
    def toggle_completion(habit_id, completion_date):
        """Toggle habit completion for a specific date."""
        if isinstance(completion_date, str):
            completion_date = datetime.strptime(completion_date, '%Y-%m-%d').date()
        
        # Check if already completed
        check_query = "SELECT id FROM habit_logs WHERE habit_id = %s AND completed_date = %s"
        existing = execute_query(check_query, (habit_id, completion_date), fetch_one=True)
        
        if existing:
            # Remove completion (undo)
            delete_query = "DELETE FROM habit_logs WHERE habit_id = %s AND completed_date = %s"
            execute_query(delete_query, (habit_id, completion_date))
            return {'completed': False, 'date': str(completion_date)}
        else:
            # Add completion
            insert_query = "INSERT INTO habit_logs (habit_id, completed_date) VALUES (%s, %s)"
            execute_query(insert_query, (habit_id, completion_date))
            return {'completed': True, 'date': str(completion_date)}
    
    @staticmethod
    def get_logs_for_month(user_id, year, month):
        """Get all habit completions for a specific month."""
        query = """
            SELECT h.id as habit_id, h.name, hl.completed_date
            FROM habits h
            LEFT JOIN habit_logs hl ON h.id = hl.habit_id 
                AND EXTRACT(YEAR FROM hl.completed_date) = %s 
                AND EXTRACT(MONTH FROM hl.completed_date) = %s
            WHERE h.user_id = %s AND h.is_active = TRUE
            ORDER BY h.sort_order, h.id, hl.completed_date
        """
        results = execute_query(query, (year, month, user_id), fetch_all=True)
        
        # Group by habit
        habits_data = {}
        for row in results:
            habit_id = row['habit_id']
            if habit_id not in habits_data:
                habits_data[habit_id] = {
                    'id': habit_id,
                    'name': row['name'],
                    'completed_dates': []
                }
            if row['completed_date']:
                habits_data[habit_id]['completed_dates'].append(str(row['completed_date']))
        
        return list(habits_data.values())
    
    @staticmethod
    def get_completion_status(user_id, target_date):
        """Get completion status for all habits on a specific date."""
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        query = """
            SELECT h.id, h.name, h.color, h.icon,
                   CASE WHEN hl.id IS NOT NULL THEN TRUE ELSE FALSE END as is_completed
            FROM habits h
            LEFT JOIN habit_logs hl ON h.id = hl.habit_id AND hl.completed_date = %s
            WHERE h.user_id = %s AND h.is_active = TRUE
            ORDER BY h.sort_order, h.id
        """
        results = execute_query(query, (target_date, user_id), fetch_all=True)
        return results
