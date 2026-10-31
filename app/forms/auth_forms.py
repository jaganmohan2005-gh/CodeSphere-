"""
CodeSphere - Authentication and Profile Forms
---------------------------------------------
Form definitions with server-side validation for registration, login,
profile management, and password reset flows.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError, NumberRange
from app.models.user import User


class RegistrationForm(FlaskForm):
    """Student registration form with validation against duplicate credentials."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=30, message="Username must be between 3 and 30 characters.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(message="Please provide a valid email address.")
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    college = StringField('College / University', validators=[
        Optional(),
        Length(max=150)
    ])
    graduation_year = IntegerField('Graduation Year', validators=[
        Optional(),
        NumberRange(min=2020, max=2035, message="Please enter a valid graduation year.")
    ])
    target_role = SelectField('Target Placement Role', choices=[
        ('Software Engineer', 'Software Engineer / SDE'),
        ('Full Stack Developer', 'Full Stack Developer'),
        ('Backend Engineer', 'Backend Engineer'),
        ('Frontend Engineer', 'Frontend Engineer'),
        ('Data Scientist / ML Engineer', 'Data Scientist / ML Engineer'),
        ('Cloud / DevOps Engineer', 'Cloud / DevOps Engineer')
    ], default='Software Engineer')
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Create Student Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.strip()).first()
        if user:
            raise ValidationError('This username is already taken. Please choose another.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.strip().lower()).first()
        if user:
            raise ValidationError('An account with this email already exists.')


class LoginForm(FlaskForm):
    """User authentication form supporting either email or username."""
    email_or_username = StringField('Email or Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class AdminLoginForm(FlaskForm):
    """Administrative portal sign-in form with distinct branding & validation."""
    email_or_username = StringField('Admin Username or Email', validators=[DataRequired()])
    password = PasswordField('Admin Password', validators=[DataRequired()])
    submit = SubmitField('Access Admin Console')


class ProfileEditForm(FlaskForm):
    """Student profile updates form."""
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    college = StringField('College / University', validators=[Optional(), Length(max=150)])
    degree = StringField('Degree & Branch', validators=[Optional(), Length(max=100)])
    graduation_year = IntegerField('Graduation Year', validators=[Optional(), NumberRange(min=2020, max=2035)])
    target_role = SelectField('Target Placement Role', choices=[
        ('Software Engineer', 'Software Engineer / SDE'),
        ('Full Stack Developer', 'Full Stack Developer'),
        ('Backend Engineer', 'Backend Engineer'),
        ('Frontend Engineer', 'Frontend Engineer'),
        ('Data Scientist / ML Engineer', 'Data Scientist / ML Engineer'),
        ('Cloud / DevOps Engineer', 'Cloud / DevOps Engineer')
    ])
    preferred_language = SelectField('Preferred Coding Language', choices=[
        ('python', 'Python 3'),
        ('java', 'Java (Standard)'),
        ('cpp', 'C++ 17/20')
    ], default='python')
    github_url = StringField('GitHub Profile URL', validators=[Optional(), Length(max=255)])
    linkedin_url = StringField('LinkedIn Profile URL', validators=[Optional(), Length(max=255)])
    bio = TextAreaField('About Me / Bio', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Profile')


class PasswordResetRequestForm(FlaskForm):
    """Request password reset link/code form."""
    email = StringField('Registered Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Password Reset Instructions')


class PasswordResetForm(FlaskForm):
    """Set new password form."""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Update Password')
