"""
CodeSphere - Authentication Automated Tests
-------------------------------------------
Validates registration, password hashing, session state, student vs. admin logins,
deactivated account enforcement, and credential validations.
"""

from app.models.user import User


def test_student_registration_success(client, app):
    """Verifies that new students can register with valid credentials."""
    resp = client.post('/register', data={
        'username': 'newstudent',
        'email': 'newstudent@college.edu',
        'full_name': 'New Student',
        'college': 'State University',
        'graduation_year': 2026,
        'target_role': 'Software Engineer',
        'password': 'SecurePassword2026!',
        'confirm_password': 'SecurePassword2026!'
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username='newstudent').first()
        assert user is not None
        assert user.role == 'student'
        assert user.check_password('SecurePassword2026!')
        assert user.profile.full_name == 'New Student'


def test_duplicate_registration_rejected(client):
    """Ensures registration rejects duplicate usernames and emails."""
    # 'student' is pre-seeded
    resp = client.post('/register', data={
        'username': 'student',
        'email': 'different@college.edu',
        'full_name': 'Duplicate User',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }, follow_redirects=True)
    assert b"already taken" in resp.data or b"exists" in resp.data


def test_student_login_and_logout(client):
    """Tests student login with correct credentials and subsequent logout."""
    login_resp = client.post('/login', data={
        'email_or_username': 'student',
        'password': 'Student@CodeSphere2026!'
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b"Welcome back" in login_resp.data

    logout_resp = client.get('/logout', follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b"signed out" in logout_resp.data


def test_invalid_login_credentials(client):
    """Verifies that invalid passwords fail authentication."""
    resp = client.post('/login', data={
        'email_or_username': 'student',
        'password': 'WrongPassword123'
    }, follow_redirects=True)
    assert b"Invalid email/username or password" in resp.data


def test_deactivated_student_login_blocked(client, app):
    """Confirms deactivated student accounts are blocked from logging in."""
    with app.app_context():
        user = User.query.filter_by(username='student').first()
        user.is_active_account = False
        from app.extensions import db
        db.session.commit()

    resp = client.post('/login', data={
        'email_or_username': 'student',
        'password': 'Student@CodeSphere2026!'
    }, follow_redirects=True)
    assert b"account has been deactivated" in resp.data


def test_admin_portal_authentication(client):
    """Verifies administrator portal authentication."""
    resp = client.post('/admin/login', data={
        'email_or_username': 'admin',
        'password': 'Admin@CodeSphere2026!'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Platform Administration" in resp.data or b"Admin Dashboard" in resp.data


def test_student_blocked_from_admin_login(client):
    """Verifies that regular students cannot authenticate through the admin portal."""
    resp = client.post('/admin/login', data={
        'email_or_username': 'student',
        'password': 'Student@CodeSphere2026!'
    }, follow_redirects=True)
    assert b"Unauthorized access" in resp.data or b"reserved for platform administrators" in resp.data
