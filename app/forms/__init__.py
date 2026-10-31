"""
CodeSphere - Forms Package
--------------------------
Exports WTF form classes for authentication, administration, question management,
and timed assessments.
"""

from app.forms.auth_forms import (
    RegistrationForm,
    LoginForm,
    AdminLoginForm,
    ProfileEditForm,
    PasswordResetRequestForm,
    PasswordResetForm
)
from app.forms.question_forms import (
    CategoryForm,
    QuestionForm,
    TestCaseForm
)
from app.forms.assessment_forms import AssessmentForm

__all__ = [
    'RegistrationForm',
    'LoginForm',
    'AdminLoginForm',
    'ProfileEditForm',
    'PasswordResetRequestForm',
    'PasswordResetForm',
    'CategoryForm',
    'QuestionForm',
    'TestCaseForm',
    'AssessmentForm'
]
