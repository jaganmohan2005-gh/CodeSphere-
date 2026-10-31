"""
CodeSphere - Application Factory Module
---------------------------------------
Initializes and binds the Flask application, database ORM, authentication manager,
CSRF protection, route blueprints, template context processors, and error handlers.
"""

import os
from datetime import datetime
from flask import Flask, render_template
from config import config_by_name
from app.extensions import db, login_manager, csrf
from app.models.notification import Notification
from flask_login import current_user


def create_app(config_name=None):
    """
    Application factory pattern to construct and configure the Flask app.
    Supports 'development', 'testing', and 'production' environments.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Initialize extensions with application context
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.student import student_bp
    from app.routes.assessment import assessment_bp
    from app.routes.ai import ai_bp
    from app.routes.notification import notification_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(notification_bp)

    # Context processors: inject unread notifications & current year into all templates
    @app.context_processor
    def inject_global_template_vars():
        unread_count = 0
        if current_user.is_authenticated:
            try:
                unread_count = Notification.query.filter_by(
                    user_id=current_user.id,
                    is_read=False
                ).count()
            except Exception:
                unread_count = 0
        return {
            'unread_notifications_count': unread_count,
            'current_year': datetime.utcnow().year,
            'openai_configured': bool(app.config.get('OPENAI_API_KEY'))
        }

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Custom CLI Command for Database Seeding
    @app.cli.command('seed-db')
    def seed_db_command():
        """CLI command to seed sample categories, questions, assessments, and accounts."""
        from app.services.seed_service import seed_database
        with app.app_context():
            db.create_all()
            seed_database(
                admin_username=app.config.get('DEFAULT_ADMIN_USERNAME', 'admin'),
                admin_email=app.config.get('DEFAULT_ADMIN_EMAIL', 'admin@codesphere.io'),
                admin_password=app.config.get('DEFAULT_ADMIN_PASSWORD', 'Admin@CodeSphere2026!')
            )
            print("CodeSphere database initialized and seeded successfully!")

    return app
