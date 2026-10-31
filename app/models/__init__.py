"""
CodeSphere - Models Package
---------------------------
Exports all SQLAlchemy models for convenient imports across routes, forms,
services, and unit tests.
"""

from app.models.user import User, StudentProfile
from app.models.question import Category, Question, TestCase
from app.models.assessment import Assessment, AssessmentQuestion, AssessmentAttempt, AttemptAnswer
from app.models.submission import Submission, SubmissionTestResult, StudentProgress
from app.models.ai import AIConversation, AIMessage
from app.models.notification import Notification

__all__ = [
    'User',
    'StudentProfile',
    'Category',
    'Question',
    'TestCase',
    'Assessment',
    'AssessmentQuestion',
    'AssessmentAttempt',
    'AttemptAnswer',
    'Submission',
    'SubmissionTestResult',
    'StudentProgress',
    'AIConversation',
    'AIMessage',
    'Notification'
]
