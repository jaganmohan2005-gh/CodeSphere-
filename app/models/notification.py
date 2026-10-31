"""
CodeSphere - Notification Model
-------------------------------
Tracks personalized real-time notifications for students regarding published
assessments, graded results, and recommended study tasks.
"""

from datetime import datetime
from app.extensions import db


class Notification(db.Model):
    """
    User notification record supporting dynamic event triggers and read states.
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Types: 'info', 'assessment', 'result', 'recommendation', 'success'
    type = db.Column(db.String(30), default='info', nullable=False)
    link = db.Column(db.String(200), nullable=True)  # Optional internal URL target
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    @property
    def badge_class(self):
        """Returns appropriate Bootstrap badge color class based on notification type."""
        mapping = {
            'assessment': 'badge-primary-soft',
            'result': 'badge-success-soft',
            'recommendation': 'badge-info-soft',
            'warning': 'badge-warning-soft',
            'info': 'badge-secondary-soft'
        }
        return mapping.get(self.type, 'badge-primary-soft')

    def mark_as_read(self):
        """Marks notification as read."""
        self.is_read = True

    def __repr__(self):
        return f"<Notification {self.id} User:{self.user_id} Title:'{self.title}' Read:{self.is_read}>"
