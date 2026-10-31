"""
CodeSphere - Submission and Progress Models
-------------------------------------------
Tracks student code executions, test case verifications, execution metrics,
and aggregated topic-wise proficiency for analytics.
"""

from datetime import datetime
from app.extensions import db


class Submission(db.Model):
    """
    Code submission record for either self-paced practice or timed assessments.
    Maintains status, execution metrics, and full history.
    """
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False, index=True)
    assessment_attempt_id = db.Column(db.Integer, db.ForeignKey('assessment_attempts.id'), nullable=True, index=True)

    source_code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(30), default='python', nullable=False)

    # Status: 'Accepted', 'Wrong Answer', 'Time Limit Exceeded', 'Runtime Error', 'Compilation Error'
    status = db.Column(db.String(40), default='Pending', nullable=False, index=True)
    execution_time_ms = db.Column(db.Float, default=0.0, nullable=False)
    memory_kb = db.Column(db.Float, default=0.0, nullable=False)

    tests_passed = db.Column(db.Integer, default=0, nullable=False)
    tests_total = db.Column(db.Integer, default=0, nullable=False)

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    test_results = db.relationship('SubmissionTestResult', backref='submission', cascade='all, delete-orphan', lazy='joined')

    @property
    def is_accepted(self):
        """Returns True if all test cases passed successfully."""
        return self.status == 'Accepted'

    def __repr__(self):
        return f"<Submission {self.id} User:{self.user_id} Question:{self.question_id} Status:{self.status}>"


class SubmissionTestResult(db.Model):
    """
    Detailed validation result for an individual test case within a submission.
    """
    __tablename__ = 'submission_test_results'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False, index=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_cases.id'), nullable=False, index=True)

    is_passed = db.Column(db.Boolean, default=False, nullable=False)
    actual_output = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    execution_time_ms = db.Column(db.Float, default=0.0, nullable=False)

    def __repr__(self):
        return f"<SubmissionTestResult {self.id} Sub:{self.submission_id} TC:{self.test_case_id} Passed:{self.is_passed}>"


class StudentProgress(db.Model):
    """
    Topic-wise performance summary table for each student, updated after
    submissions and assessments to drive real-time analytics and AI study plans.
    """
    __tablename__ = 'student_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)

    questions_attempted = db.Column(db.Integer, default=0, nullable=False)
    questions_solved = db.Column(db.Integer, default=0, nullable=False)
    accuracy_rate = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 - 100.0%
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'category_id', name='uq_user_category_progress'),
    )

    def recalculate_accuracy(self):
        """Safely recomputes accuracy percentage avoiding division by zero."""
        if self.questions_attempted > 0:
            self.accuracy_rate = round((self.questions_solved / self.questions_attempted) * 100.0, 1)
        else:
            self.accuracy_rate = 0.0

    def __repr__(self):
        return f"<StudentProgress User:{self.user_id} Cat:{self.category_id} Solved:{self.questions_solved}/{self.questions_attempted}>"
