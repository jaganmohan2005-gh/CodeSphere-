"""
CodeSphere - Configuration Module
---------------------------------
This file manages environment configurations for development, testing, and production.
It reads sensitive variables (secret keys, database URIs, API keys) from environment
variables or .env files, providing safe defaults for beginners.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load variables from .env file if it exists
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base configuration class with common settings."""
    # Application Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'codesphere-dev-secret-key-change-in-production-2026'
    
    # Database Configuration (SQLite by default, ready for PostgreSQL via DATABASE_URL)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'codesphere.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session & Cookie Security
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # AI Configuration (OpenAI Python SDK)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    AI_RATE_LIMIT_PER_MINUTE = int(os.environ.get('AI_RATE_LIMIT_PER_MINUTE', 15))
    
    # Assessment & Code Execution Configuration
    MAX_EXECUTION_TIME_SECONDS = int(os.environ.get('MAX_EXECUTION_TIME_SECONDS', 4))
    MAX_CODE_LENGTH_CHARS = int(os.environ.get('MAX_CODE_LENGTH_CHARS', 25000))
    
    # Platform Defaults
    ITEMS_PER_PAGE = 15
    DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
    DEFAULT_ADMIN_EMAIL = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@codesphere.io')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'Admin@CodeSphere2026!')


class DevelopmentConfig(Config):
    """Configuration for local development."""
    DEBUG = True


class TestingConfig(Config):
    """Configuration for automated tests."""
    TESTING = True
    WTF_CSRF_ENABLED = False  # Disable CSRF in tests for simplified form posting
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Fast in-memory SQLite for tests
    SECRET_KEY = 'test-secret-key'


class ProductionConfig(Config):
    """Configuration for production deployment."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Enforce HTTPS in production


# Config mapping dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
