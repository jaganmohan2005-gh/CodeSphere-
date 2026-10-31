"""
CodeSphere - Timed Assessment Automated Tests
---------------------------------------------
Validates assessment configuration, timed sessions, autosaving, server-side deadline
validation, weighted score grading, retake policies, and CSV export.
"""

from datetime import datetime, timedelta
from app.models.assessment import Assessment, AssessmentQuestion, AssessmentAttempt, AttemptAnswer
from app.models.question import Question
from app.models.user import User
from app.extensions import db


def test_admin_create_assessment(admin_client, app):
    """Verifies that an administrator can construct and publish a timed assessment."""
    with app.app_context():
        questions = Question.query.limit(2).all()
        q1_id, q2_id = questions[0].id, questions[1].id

    resp = admin_client.post('/admin/assessments/create', data={
        'title': 'Mid-Term Coding Drive 2026',
        'difficulty': 'Medium',
        'duration_minutes': 90,
        'pass_percentage': 60.0,
        'results_released_immediately': True,
        'retake_allowed': False,
        'is_published': True,
        'selected_questions': [str(q1_id), str(q2_id)],
        f'marks_{q1_id}': 50,
        f'marks_{q2_id}': 50
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app.app_context():
        asm = Assessment.query.filter_by(title='Mid-Term Coding Drive 2026').first()
        assert asm is not None
        assert asm.duration_minutes == 90
        assert asm.total_marks == 100
        assert asm.question_count == 2


def test_student_start_assessment_and_deadline_calculation(auth_client, app):
    """Verifies starting an assessment sets exact server-side start and deadline timestamps."""
    with app.app_context():
        asm = Assessment.query.filter_by(is_published=True).first()
        asm_id = asm.id
        duration = asm.duration_minutes

    start_resp = auth_client.post(f'/assessments/{asm_id}/start', follow_redirects=True)
    assert start_resp.status_code == 200
    assert b"Assessment started" in start_resp.data or b"Resuming" in start_resp.data

    with app.app_context():
        student = User.query.filter_by(username='student').first()
        attempt = AssessmentAttempt.query.filter_by(
            assessment_id=asm_id,
            user_id=student.id,
            status='in_progress'
        ).first()

        assert attempt is not None
        assert attempt.start_time is not None
        assert attempt.deadline_time is not None
        # Deadline should equal start_time + duration
        expected_diff = attempt.deadline_time - attempt.start_time
        assert int(expected_diff.total_seconds()) == duration * 60
        assert not attempt.is_expired


def test_autosave_assessment_answer(auth_client, app):
    """Tests autosaving code for an assessment question."""
    with app.app_context():
        asm = Assessment.query.filter_by(is_published=True).first()
        asm_id = asm.id

    auth_client.post(f'/assessments/{asm_id}/start', follow_redirects=True)

    with app.app_context():
        student = User.query.filter_by(username='student').first()
        attempt = AssessmentAttempt.query.filter_by(user_id=student.id, status='in_progress').first()
        attempt_id = attempt.id
        q_id = attempt.answers[0].question_id

    resp = auth_client.post(f'/assessments/attempt/{attempt_id}/autosave', json={
        'question_id': q_id,
        'code': '# Autosaved solution draft\nimport sys\nprint("hello world")',
        'language': 'python'
    })

    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'saved'

    with app.app_context():
        ans = AttemptAnswer.query.filter_by(attempt_id=attempt_id, question_id=q_id).first()
        assert '# Autosaved solution draft' in ans.code
        assert ans.status == 'saved'


def test_server_side_deadline_enforcement(auth_client, app):
    """
    Verifies that if a student's timer has expired on the server,
    attempting to autosave or take the assessment auto-submits with timed_out status.
    """
    with app.app_context():
        asm = Assessment.query.filter_by(is_published=True).first()
        asm_id = asm.id

    auth_client.post(f'/assessments/{asm_id}/start', follow_redirects=True)

    with app.app_context():
        student = User.query.filter_by(username='student').first()
        attempt = AssessmentAttempt.query.filter_by(user_id=student.id, status='in_progress').first()
        # Manually backdate deadline to simulate expiration
        attempt.deadline_time = datetime.utcnow() - timedelta(minutes=5)
        db.session.commit()
        attempt_id = attempt.id

    # Accessing the assessment page when deadline is past triggers timeout finalization
    resp = auth_client.get(f'/assessments/attempt/{attempt_id}', follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        updated_attempt = AssessmentAttempt.query.get(attempt_id)
        assert updated_attempt.status == 'timed_out'
        assert updated_attempt.submitted_at is not None



def test_admin_export_assessment_csv(admin_client, app):
    """Verifies that administrators can export results to a downloadable CSV."""
    with app.app_context():
        asm = Assessment.query.first()
        asm_id = asm.id

    resp = admin_client.get(f'/admin/assessments/{asm_id}/export-csv')
    assert resp.status_code == 200
    assert resp.mimetype == 'text/csv'
    assert b"Attempt ID,Student Username,Student Email" in resp.data
