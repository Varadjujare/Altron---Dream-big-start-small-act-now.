"""
User model for LifeSync Dashboard.
"""
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import sys
sys.path.append('..')
from utils.db import execute_query, get_db_cursor


class User(UserMixin):
    """User model for authentication and preferences."""
    
    def __init__(self, id=None, username=None, email=None, password_hash=None, 
                 theme_preference='dark', created_at=None, updated_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.theme_preference = theme_preference
        self.created_at = created_at
        self.updated_at = updated_at
    
    def set_password(self, password):
        """Hash and set the password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify the password."""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary (excluding password)."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'theme_preference': self.theme_preference,
            'created_at': str(self.created_at) if self.created_at else None
        }
    
    @staticmethod
    def create(username, email, password):
        """Create a new user."""
        password_hash = generate_password_hash(password)
        query = """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s) RETURNING id
        """
        result = execute_query(query, (username, email, password_hash), fetch_one=True)
        if not result:
             raise Exception("Database insert failed: No ID returned")
        user_id = result['id']
        return User.get_by_id(user_id)
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID."""
        query = "SELECT * FROM users WHERE id = %s"
        result = execute_query(query, (user_id,), fetch_one=True)
        if result:
            return User(**result)
        return None
    
    @staticmethod
    def get_by_email(email):
        """Get user by email."""
        query = "SELECT * FROM users WHERE email = %s"
        result = execute_query(query, (email,), fetch_one=True)
        if result:
            return User(**result)
        return None
    
    @staticmethod
    def get_by_username(username):
        """Get user by username."""
        query = "SELECT * FROM users WHERE username = %s"
        result = execute_query(query, (username,), fetch_one=True)
        if result:
            return User(**result)
        return None
    
    def update_theme(self, theme):
        """Update user's theme preference."""
        query = "UPDATE users SET theme_preference = %s WHERE id = %s"
        execute_query(query, (theme, self.id))
        self.theme_preference = theme
