"""
CodeSphere - User and Profile Models
------------------------------------
Defines user authentication, roles (Admin vs. Student), account status,
and student profile information.
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    """
    Core User entity for authentication, role-based authorization,
    and platform relationship tracking.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'admin' or 'student'
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    assessment_attempts = db.relationship('AssessmentAttempt', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    ai_conversations = db.relationship('AIConversation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    progress_records = db.relationship('StudentProgress', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    # Password management
    def set_password(self, password):
        """Hashes the plain password using Werkzeug's secure hashing algorithm."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies the input password against the stored secure hash."""
        return check_password_hash(self.password_hash, password)

    # Role checking helpers
    @property
    def is_admin(self):
        """Returns True if the user has administrator privileges."""
        return self.role == 'admin'

    @property
    def is_student(self):
        """Returns True if the user is a student."""
        return self.role == 'student'

    # Flask-Login override to handle deactivated accounts
    @property
    def is_active(self):
        """Flask-Login checks this property to permit login."""
        return self.is_active_account

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class StudentProfile(db.Model):
    """
    Extended profile information for students, including academic background,
    target roles, and social/portfolio links.
    """
    __tablename__ = 'student_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    college = db.Column(db.String(150), nullable=True)
    degree = db.Column(db.String(100), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)
    target_role = db.Column(db.String(100), default='Software Engineer', nullable=True)
    preferred_language = db.Column(db.String(30), default='python', nullable=False)
    github_url = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<StudentProfile {self.full_name} for User {self.user_id}>"


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login callback to reload the user object from the user ID stored in session."""
    return db.session.get(User, int(user_id))
