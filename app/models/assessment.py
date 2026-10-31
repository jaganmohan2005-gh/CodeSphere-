"""
CodeSphere - Assessment Models
------------------------------
Defines formal timed assessments, question mark allocations, student attempts,
and persistent question answers with server-side deadline enforcement.
"""

from datetime import datetime, timedelta
from app.extensions import db


class Assessment(db.Model):
    """
    Formal timed assessment created by an administrator containing a set of
    questions with custom score weightings and strict duration rules.
    """
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), default='Medium', nullable=False)  # 'Easy', 'Medium', 'Hard', 'Comprehensive'
    duration_minutes = db.Column(db.Integer, default=60, nullable=False)  # 60, 90, 180, etc.
    
    # Scheduling availability window (optional start and end date)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)

    is_published = db.Column(db.Boolean, default=False, nullable=False)
    pass_percentage = db.Column(db.Float, default=50.0, nullable=False)
    results_released_immediately = db.Column(db.Boolean, default=True, nullable=False)
    retake_allowed = db.Column(db.Boolean, default=False, nullable=False)

    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    assessment_questions = db.relationship(
        'AssessmentQuestion', 
        backref='assessment', 
        cascade='all, delete-orphan', 
        order_by='AssessmentQuestion.order_index',
        lazy='joined'
    )
    attempts = db.relationship('AssessmentAttempt', backref='assessment', cascade='all, delete-orphan', lazy='dynamic')

    @property
    def total_marks(self):
        """Calculates total marks for the assessment by summing question marks."""
        return sum(aq.marks for aq in self.assessment_questions)

    @property
    def question_count(self):
        """Returns the number of questions in this assessment."""
        return len(self.assessment_questions)

    def is_currently_available(self):
        """Checks if current UTC time falls within the configured availability window."""
        now = datetime.utcnow()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return self.is_published

    def __repr__(self):
        return f"<Assessment {self.id}: {self.title} ({self.duration_minutes} mins)>"


class AssessmentQuestion(db.Model):
    """
    Junction entity connecting an Assessment to a Question with ordering
    and custom marks assignment.
    """
    __tablename__ = 'assessment_questions'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False, index=True)
    order_index = db.Column(db.Integer, default=1, nullable=False)
    marks = db.Column(db.Integer, default=10, nullable=False)

    def __repr__(self):
        return f"<AssessmentQuestion Assessment:{self.assessment_id} Question:{self.question_id} Marks:{self.marks}>"


class AssessmentAttempt(db.Model):
    """
    Tracks a student's attempt at an assessment.
    Enforces server-side deadline calculation to guarantee timing integrity.
    """
    __tablename__ = 'assessment_attempts'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Server-enforced timing
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    deadline_time = db.Column(db.DateTime, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=True)

    # Status: 'in_progress', 'completed', 'timed_out'
    status = db.Column(db.String(20), default='in_progress', nullable=False)
    
    # Scoring
    total_score = db.Column(db.Float, default=0.0, nullable=False)
    max_possible_score = db.Column(db.Float, default=0.0, nullable=False)
    percentage = db.Column(db.Float, default=0.0, nullable=False)
    is_passed = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    answers = db.relationship('AttemptAnswer', backref='attempt', cascade='all, delete-orphan', lazy='joined')
    submissions = db.relationship('Submission', backref='attempt', lazy='dynamic')

    def calculate_deadline(self, duration_minutes):
        """Computes server-side deadline from start_time + duration_minutes."""
        if self.start_time is None:
            self.start_time = datetime.utcnow()
        self.deadline_time = self.start_time + timedelta(minutes=duration_minutes)

    @property
    def is_expired(self):
        """Checks server-side if current UTC time has exceeded the deadline."""
        if self.deadline_time is None:
            return False
        return datetime.utcnow() >= self.deadline_time

    @property
    def remaining_seconds(self):
        """Returns the remaining seconds before the deadline, or 0 if expired."""
        if self.deadline_time is None:
            return 0
        diff = (self.deadline_time - datetime.utcnow()).total_seconds()
        return max(0, int(diff))

    @property
    def is_active(self):
        """Returns True if the attempt is in_progress and not expired."""
        return self.status == 'in_progress' and not self.is_expired

    def __repr__(self):
        return f"<AssessmentAttempt {self.id} User:{self.user_id} Assessment:{self.assessment_id} Status:{self.status}>"


class AttemptAnswer(db.Model):
    """
    Stores a student's answer code and evaluation status for a specific question
    within an assessment attempt. Enables autosaving and safe resumption.
    """
    __tablename__ = 'attempt_answers'

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('assessment_attempts.id'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False, index=True)
    
    code = db.Column(db.Text, nullable=True)
    language = db.Column(db.String(30), default='python', nullable=False)
    
    # Status: 'unanswered', 'saved', 'passed', 'failed', 'partial'
    status = db.Column(db.String(30), default='unanswered', nullable=False)
    score_awarded = db.Column(db.Float, default=0.0, nullable=False)
    test_cases_passed = db.Column(db.Integer, default=0, nullable=False)
    total_test_cases = db.Column(db.Integer, default=0, nullable=False)
    
    last_saved_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    question = db.relationship('Question', lazy='joined')

    @property
    def is_attempted(self):
        """Returns True if code was saved or submitted."""
        return bool(self.code and self.code.strip())

    def __repr__(self):
        return f"<AttemptAnswer Attempt:{self.attempt_id} Question:{self.question_id} Status:{self.status}>"
