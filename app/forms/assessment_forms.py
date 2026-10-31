"""
CodeSphere - Assessment Forms
-----------------------------
Form definitions for authoring, configuring, and publishing timed assessments.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, BooleanField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class AssessmentForm(FlaskForm):
    """Admin form to configure and publish timed assessments."""
    title = StringField('Assessment Title', validators=[
        DataRequired(),
        Length(min=5, max=150)
    ])
    description = TextAreaField('Description and Instructions', validators=[Optional()])
    difficulty = SelectField('Target Difficulty', choices=[
        ('Easy', 'Easy (Foundation)'),
        ('Medium', 'Medium (Standard Placement)'),
        ('Hard', 'Hard (Advanced Product Companies)'),
        ('Comprehensive', 'Comprehensive (Mixed Multi-Topic)')
    ], default='Medium')
    duration_minutes = IntegerField('Duration (Minutes)', validators=[
        DataRequired(),
        NumberRange(min=10, max=360, message="Duration must be between 10 and 360 minutes.")
    ], default=60)
    pass_percentage = FloatField('Passing Score Percentage (%)', validators=[
        DataRequired(),
        NumberRange(min=0.0, max=100.0)
    ], default=50.0)
    results_released_immediately = BooleanField('Release detailed results immediately upon submission', default=True)
    retake_allowed = BooleanField('Allow retakes if previously attempted', default=False)
    is_published = BooleanField('Publish assessment (Visible to students)', default=False)
    
    # We dynamically populate available questions in route handler
    submit = SubmitField('Save Assessment')
