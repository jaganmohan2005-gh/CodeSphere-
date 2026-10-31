"""
CodeSphere - Route Decorators & Access Control
----------------------------------------------
Enforces role-based authorization (Admin vs. Student) and prevents
unauthorized privilege escalation or cross-tenant data leakage.
"""

from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """
    Decorator to restrict route access exclusively to users with administrator role.
    Aborts with 403 Forbidden or redirects to admin login if unauthenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in with administrator credentials.", "warning")
            return redirect(url_for('auth.admin_login'))
        if not current_user.is_admin:
            flash("Access denied: Administrator privileges required.", "danger")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """
    Decorator to restrict route access to active student accounts.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in to access student features.", "warning")
            return redirect(url_for('auth.login'))
        if not current_user.is_student:
            flash("This section is tailored for student accounts.", "info")
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function
