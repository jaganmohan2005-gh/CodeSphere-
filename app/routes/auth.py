"""
CodeSphere - Authentication Routes
----------------------------------
Handles student registration, user and administrator authentication,
account state checking, password hashing, secure sessions, and profile editing.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User, StudentProfile
from app.forms.auth_forms import (
    RegistrationForm,
    LoginForm,
    AdminLoginForm,
    ProfileEditForm,
    PasswordResetRequestForm,
    PasswordResetForm
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles new student account creation."""
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard' if current_user.is_student else 'admin.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            role='student',
            is_active_account=True
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # Obtain user.id for profile

        profile = StudentProfile(
            user_id=user.id,
            full_name=form.full_name.data.strip(),
            college=form.college.data.strip() if form.college.data else None,
            graduation_year=form.graduation_year.data,
            target_role=form.target_role.data,
            preferred_language='python'
        )
        db.session.add(profile)
        db.session.commit()

        flash("Account created successfully! Welcome to CodeSphere. Please sign in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles student and general sign-in with active account verification."""
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard' if current_user.is_student else 'admin.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.email_or_username.data.strip()
        user = User.query.filter(
            (User.email == identifier.lower()) | (User.username == identifier)
        ).first()

        if user and user.check_password(form.password.data):
            if not user.is_active_account:
                flash("Your account has been deactivated by an administrator. Please contact support.", "danger")
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember_me.data)
            flash(f"Welcome back, {user.username}!", "success")

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('admin.dashboard' if user.is_admin else 'student.dashboard'))

        flash("Invalid email/username or password. Please try again.", "danger")

    return render_template('auth/login.html', form=form)


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Dedicated sign-in portal for administrative personnel."""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

    form = AdminLoginForm()
    if form.validate_on_submit():
        identifier = form.email_or_username.data.strip()
        user = User.query.filter(
            (User.email == identifier.lower()) | (User.username == identifier)
        ).first()

        if user and user.check_password(form.password.data):
            if not user.is_admin:
                flash("Unauthorized access: This portal is reserved for platform administrators.", "danger")
                return render_template('auth/admin_login.html', form=form)
            if not user.is_active_account:
                flash("Administrator account is inactive.", "danger")
                return render_template('auth/admin_login.html', form=form)

            login_user(user)
            flash("Administrator session authenticated.", "success")
            return redirect(url_for('admin.dashboard'))

        flash("Invalid administrator credentials.", "danger")

    return render_template('auth/admin_login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Securely logs the user out and terminates active session."""
    logout_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Allows authenticated students to inspect and update their profile details."""
    form = ProfileEditForm()
    profile = current_user.profile

    if not profile:
        profile = StudentProfile(user_id=current_user.id, full_name=current_user.username)
        db.session.add(profile)
        db.session.commit()

    if form.validate_on_submit():
        profile.full_name = form.full_name.data.strip()
        profile.college = form.college.data.strip() if form.college.data else None
        profile.degree = form.degree.data.strip() if form.degree.data else None
        profile.graduation_year = form.graduation_year.data
        profile.target_role = form.target_role.data
        profile.preferred_language = form.preferred_language.data
        profile.github_url = form.github_url.data.strip() if form.github_url.data else None
        profile.linkedin_url = form.linkedin_url.data.strip() if form.linkedin_url.data else None
        profile.bio = form.bio.data.strip() if form.bio.data else None
        db.session.commit()

        flash("Profile updated successfully!", "success")
        return redirect(url_for('auth.profile'))

    elif request.method == 'GET':
        form.full_name.data = profile.full_name
        form.college.data = profile.college
        form.degree.data = profile.degree
        form.graduation_year.data = profile.graduation_year
        form.target_role.data = profile.target_role
        form.preferred_language.data = profile.preferred_language
        form.github_url.data = profile.github_url
        form.linkedin_url.data = profile.linkedin_url
        form.bio.data = profile.bio

    return render_template('auth/profile.html', form=form, profile=profile)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password recovery workflow endpoint."""
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        # Always display confirmation to prevent account enumeration
        flash("If an account exists with that email, reset instructions have been dispatched. (For local development, demo reset is available below).", "info")
        return render_template('auth/forgot_password.html', form=form, submitted=True, email=email)
    return render_template('auth/forgot_password.html', form=form, submitted=False)
