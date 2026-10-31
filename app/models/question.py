"""
CodeSphere - Question and Category Models
-----------------------------------------
Defines category classification, coding problems, starter templates,
and test cases (both public samples and hidden test cases).
"""

from datetime import datetime
from app.extensions import db


class Category(db.Model):
    """
    Topic category for coding questions (e.g., Arrays, Dynamic Programming, SQL).
    Supports safe deletion verification to prevent orphaned questions.
    """
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), default='bi-code-slash', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    questions = db.relationship('Question', backref='category', lazy='dynamic')
    progress_records = db.relationship('StudentProgress', backref='category', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def question_count(self):
        """Returns the total number of questions currently in this category."""
        return self.questions.count()

    def can_be_safely_deleted(self):
        """Returns True if no questions reference this category."""
        return self.questions.count() == 0

    def __repr__(self):
        return f"<Category {self.name}>"


class Question(db.Model):
    """
    Individual coding problem entity with detailed requirements,
    difficulty ranking, starter codes, and complexity benchmarks.
    """
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    difficulty = db.Column(db.String(20), default='Easy', nullable=False)  # 'Easy', 'Medium', 'Hard'
    description = db.Column(db.Text, nullable=False)
    constraints = db.Column(db.Text, nullable=True)
    sample_input = db.Column(db.Text, nullable=True)
    sample_output = db.Column(db.Text, nullable=True)
    explanation = db.Column(db.Text, nullable=True)
    time_complexity_expected = db.Column(db.String(50), default='O(N)', nullable=True)
    space_complexity_expected = db.Column(db.String(50), default='O(1)', nullable=True)

    # Multi-language starter code templates
    starter_code_python = db.Column(db.Text, nullable=True)
    starter_code_java = db.Column(db.Text, nullable=True)
    starter_code_cpp = db.Column(db.Text, nullable=True)

    is_published = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    test_cases = db.relationship('TestCase', backref='question', cascade='all, delete-orphan', lazy='joined')
    assessment_questions = db.relationship('AssessmentQuestion', backref='question', cascade='all, delete-orphan', lazy='dynamic')
    submissions = db.relationship('Submission', backref='question', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def public_test_cases(self):
        """Returns test cases that students are allowed to view (is_hidden == False)."""
        return [tc for tc in self.test_cases if not tc.is_hidden]

    @property
    def hidden_test_cases(self):
        """Returns hidden validation test cases used for official grading."""
        return [tc for tc in self.test_cases if tc.is_hidden]

    def __repr__(self):
        return f"<Question {self.id}: {self.title} ({self.difficulty})>"


class TestCase(db.Model):
    """
    Test cases used to validate student code solutions.
    Can be public (sample test case) or hidden (grading test case).
    """
    __test__ = False  # Instruct Pytest not to collect this database model as a test suite
    __tablename__ = 'test_cases'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False, index=True)
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    is_hidden = db.Column(db.Boolean, default=False, nullable=False)  # Hidden from student UI
    points = db.Column(db.Integer, default=10, nullable=False)

    # Relationships
    test_results = db.relationship('SubmissionTestResult', backref='test_case', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f"<TestCase {self.id} for Question {self.question_id} (Hidden: {self.is_hidden})>"
