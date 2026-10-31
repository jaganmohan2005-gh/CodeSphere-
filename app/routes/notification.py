"""
CodeSphere - Notification Routes
--------------------------------
Provides notification retrieval, unread count polling, and mark-as-read actions.
"""

from flask import Blueprint, render_template, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.notification import Notification

notification_bp = Blueprint('notification', __name__, url_prefix='/notifications')


@notification_bp.route('/')
@login_required
def index():
    """Renders the notifications feed for the current user."""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).all()
    return render_template('notifications/index.html', notifications=notifications)


@notification_bp.route('/unread-count')
@login_required
def unread_count():
    """Returns unread notification count for the navbar badge."""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'unread_count': count})


@notification_bp.route('/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    """Marks an individual notification as read."""
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.mark_as_read()
    db.session.commit()
    return jsonify({'status': 'success'})


@notification_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Marks all notifications for current user as read."""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for('notification.index'))
