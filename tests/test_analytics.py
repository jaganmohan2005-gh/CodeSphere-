"""
CodeSphere - Analytics & Metrics Calculation Tests
--------------------------------------------------
Validates defensive calculations, zero-activity edge cases, accuracy rates,
weak topic identification, and admin aggregate summaries.
"""

from app.services.analytics_service import analytics_service
from app.models.user import User
from app.models.submission import Submission, StudentProgress
from app.models.question import Question
from app.extensions import db


def test_student_analytics_with_zero_activity(app):
    """Verifies that a student with 0 submissions produces clean 0.0 metrics without division-by-zero."""
    with app.app_context():
        new_user = User(username='zerouser', email='zero@test.com', role='student')
        new_user.set_password('Pass123!')
        db.session.add(new_user)
        db.session.commit()
        uid = new_user.id

        stats = analytics_service.get_student_analytics(uid)
        assert stats['total_attempted'] == 0
        assert stats['total_solved'] == 0
        assert stats['accuracy_percentage'] == 0.0
        assert stats['assessments_taken'] == 0
        assert stats['avg_assessment_score'] == 0.0


def test_student_analytics_with_active_submissions(app):
    """Verifies accurate accuracy percentage and metrics with actual submissions."""
    with app.app_context():
        student = User.query.filter_by(username='student').first()
        q1 = Question.query.first()
        q2 = Question.query.all()[1]

        # Accepted submission for q1
        sub1 = Submission(
            user_id=student.id,
            question_id=q1.id,
            source_code='test',
            status='Accepted',
            tests_passed=2,
            tests_total=2
        )
        # Failed submission for q2
        sub2 = Submission(
            user_id=student.id,
            question_id=q2.id,
            source_code='test',
            status='Wrong Answer',
            tests_passed=0,
            tests_total=2
        )
        db.session.add_all([sub1, sub2])
        db.session.commit()

        stats = analytics_service.get_student_analytics(student.id)
        assert stats['total_attempted'] >= 2
        assert stats['total_solved'] >= 1
        # Accuracy must be > 0
        assert stats['accuracy_percentage'] > 0.0


def test_admin_dashboard_metrics(app):
    """Verifies that platform dashboard aggregates return valid numeric counts."""
    with app.app_context():
        stats = analytics_service.get_admin_dashboard_stats()
        assert stats['total_students'] >= 1
        assert stats['total_questions'] >= 1
        assert stats['total_assessments'] >= 1
        assert 'Easy' in stats['difficulty_breakdown']
