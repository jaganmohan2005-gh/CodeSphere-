"""
CodeSphere - Application Entry Point
------------------------------------
Executes the development server or production WSGI server (Gunicorn),
and manages database initialization and seeding.
"""

import os
import sys
from app import create_app
from app.extensions import db
from app.services.seed_service import seed_database

# Read environment (development, testing, production)
env_mode = os.environ.get('FLASK_ENV', 'development')
app = create_app(env_mode)


def initialize_and_seed():
    """Initializes tables and seeds standard curriculum and demo accounts."""
    with app.app_context():
        db.create_all()
        seed_database(
            admin_username=app.config.get('DEFAULT_ADMIN_USERNAME', 'admin'),
            admin_email=app.config.get('DEFAULT_ADMIN_EMAIL', 'admin@codesphere.io'),
            admin_password=app.config.get('DEFAULT_ADMIN_PASSWORD', 'Admin@CodeSphere2026!')
        )
        print("=" * 60)
        print(" CodeSphere Database Seeded Successfully!")
        print(" Default Admin Account:")
        print(f"   Username: {app.config.get('DEFAULT_ADMIN_USERNAME', 'admin')}")
        print("   Password: Admin@CodeSphere2026!")
        print(" Default Student Account:")
        print("   Username: student")
        print("   Password: Student@CodeSphere2026!")
        print("=" * 60)


# Ensure database tables exist automatically when running on Render or any server
with app.app_context():
    try:
        db.create_all()
        from app.models.user import User
        if User.query.count() == 0:
            print("First run detected. Seeding initial database records...")
            seed_database()
    except Exception as e:
        print(f"Notice during startup initialization: {e}")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'seed':
        initialize_and_seed()
    else:
        print("Starting CodeSphere server on http://127.0.0.1:5000 ...")
        app.run(host='127.0.0.1', port=5000, debug=True)
