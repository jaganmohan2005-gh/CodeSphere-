"""
CodeSphere - Routes Package
---------------------------
Exports all route blueprints:
- auth_bp: Authentication & profiles
- admin_bp: Administrative console
- student_bp: Student dashboard, practice problems, and analytics
- assessment_bp: Timed assessments
- ai_bp: AI Learning Assistant
- notification_bp: Notifications
"""

from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.student import student_bp
from app.routes.assessment import assessment_bp
from app.routes.ai import ai_bp
from app.routes.notification import notification_bp

__all__ = [
    'auth_bp',
    'admin_bp',
    'student_bp',
    'assessment_bp',
    'ai_bp',
    'notification_bp'
]
