"""
Altron Dashboard - Configuration Settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env from backend directory
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Debug: Print SMTP config at startup


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'lifesync-secret-key-change-in-production')
    
    # PostgreSQL Database Configuration
    PG_HOST = os.getenv('PG_HOST', 'localhost')
    PG_USER = os.getenv('PG_USER', 'postgres')
    PG_PASSWORD = os.getenv('PG_PASSWORD', 'password')
    PG_DATABASE = os.getenv('PG_DATABASE', 'lifesync_db')
    PG_PORT = int(os.getenv('PG_PORT', 5432))
    
    # Flask settings
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Session settings
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # SMTP Email Configuration (Gmail)
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')  # your.email@gmail.com
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # Gmail App Password
    SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'Altron Reports')
    SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', '')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
