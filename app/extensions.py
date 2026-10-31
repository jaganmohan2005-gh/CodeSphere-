"""
CodeSphere - Flask Extensions Module
------------------------------------
This module initializes Flask extension instances without binding them
to a specific application instance yet. This pattern prevents circular
imports across models, routes, forms, and services.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialize database ORM instance
db = SQLAlchemy()

# Initialize authentication & session manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# Initialize Cross-Site Request Forgery (CSRF) protection
csrf = CSRFProtect()
