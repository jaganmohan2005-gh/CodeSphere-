"""
CodeSphere - Role-Based Permissions & Data Isolation Tests
----------------------------------------------------------
Validates @admin_required enforcement, privilege separation, and tenant isolation
preventing students from accessing administrator tooling or other students' private attempts.
"""

from app.models.user import User
from app.models.assessment import AssessmentAttempt, Assessment
from app.extensions import db


def test_unauthenticated_blocked_from_admin(client):
    """Verifies unauthenticated visitors cannot access admin dashboard."""
    resp = client.get('/admin/dashboard', follow_redirects=False)
    assert resp.status_code == 302
    assert '/admin/login' in resp.headers.get('Location', '') or '/login' in resp.headers.get('Location', '')


def test_student_blocked_from_admin_dashboard(auth_client):
    """Verifies that an authenticated student receives 403 Forbidden when trying to access admin dashboard."""
    resp = auth_client.get('/admin/dashboard')
    assert resp.status_code == 403


def test_student_data_isolation_on_assessment_attempt(app, client):
    """
    Confirms student A cannot inspect or submit code to student B's assessment attempt.
    """
    with app.app_context():
        # Create student B
        student_b = User(username='student_b', email='b@college.edu', role='student')
        student_b.set_password('PassB2026!')
        db.session.add(student_b)
        db.session.flush()

        # Create attempt for student A ('student')
        student_a = User.query.filter_by(username='student').first()
        assessment = Assessment.query.first()
        
        attempt_a = AssessmentAttempt(
            assessment_id=assessment.id,
            user_id=student_a.id,
            status='in_progress',
            max_possible_score=100.0
        )
        attempt_a.calculate_deadline(assessment.duration_minutes)
        db.session.add(attempt_a)
        db.session.commit()
        attempt_a_id = attempt_a.id

    # Log in as Student B
    client.post('/login', data={
        'email_or_username': 'student_b',
        'password': 'PassB2026!'
    }, follow_redirects=True)

    # Student B tries to open Student A's attempt
    resp = client.get(f'/assessments/attempt/{attempt_a_id}')
    assert resp.status_code == 403

    # Student B tries to autosave code to Student A's attempt
    save_resp = client.post(f'/assessments/attempt/{attempt_a_id}/autosave', json={
        'question_id': 1,
        'code': 'print("malicious overwrite")',
        'language': 'python'
    })
    assert save_resp.status_code == 403
