"""
CodeSphere - Question and Category Forms
----------------------------------------
Forms for creating and editing categories, coding questions, and test cases.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from app.models.question import Category


class CategoryForm(FlaskForm):
    """Category creation and update form."""
    name = StringField('Category Name', validators=[
        DataRequired(),
        Length(min=2, max=64)
    ])
    slug = StringField('Slug (URL friendly)', validators=[
        DataRequired(),
        Length(min=2, max=64)
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500)
    ])
    icon = SelectField('Category Icon', choices=[
        ('bi-grid-3x3', 'Grid / Arrays'),
        ('bi-fonts', 'Typography / Strings'),
        ('bi-search', 'Search / Searching'),
        ('bi-arrow-down-up', 'Sorting / Arrows'),
        ('bi-arrow-repeat', 'Repeat / Recursion'),
        ('bi-link-45deg', 'Link / Linked Lists'),
        ('bi-layers', 'Layers / Stacks'),
        ('bi-distribute-horizontal', 'Queue / Deque'),
        ('bi-diagram-3', 'Tree / Hierarchy'),
        ('bi-share', 'Graph / Network'),
        ('bi-cpu', 'CPU / Dynamic Programming'),
        ('bi-lightning-charge', 'Lightning / Greedy'),
        ('bi-boxes', 'Boxes / OOP'),
        ('bi-database', 'Database / DBMS'),
        ('bi-table', 'Table / SQL'),
        ('bi-motherboard', 'Motherboard / OS'),
        ('bi-hdd-network', 'Network / Computer Networks'),
        ('bi-code-slash', 'Generic Code')
    ], default='bi-code-slash')
    submit = SubmitField('Save Category')


class QuestionForm(FlaskForm):
    """Coding question management form."""
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    title = StringField('Question Title', validators=[
        DataRequired(),
        Length(min=4, max=150)
    ])
    difficulty = SelectField('Difficulty', choices=[
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard')
    ], default='Easy')
    description = TextAreaField('Problem Description (Supports Markdown)', validators=[
        DataRequired()
    ])
    constraints = TextAreaField('Constraints', validators=[Optional()])
    sample_input = TextAreaField('Sample Input', validators=[Optional()])
    sample_output = TextAreaField('Sample Output', validators=[Optional()])
    explanation = TextAreaField('Explanation', validators=[Optional()])
    time_complexity_expected = StringField('Expected Time Complexity', validators=[Optional(), Length(max=50)], default='O(N)')
    space_complexity_expected = StringField('Expected Space Complexity', validators=[Optional(), Length(max=50)], default='O(1)')
    starter_code_python = TextAreaField('Starter Code (Python 3)', validators=[Optional()])
    starter_code_java = TextAreaField('Starter Code (Java)', validators=[Optional()])
    starter_code_cpp = TextAreaField('Starter Code (C++)', validators=[Optional()])
    is_published = BooleanField('Published and Visible to Students', default=True)
    submit = SubmitField('Save Question')


class TestCaseForm(FlaskForm):
    """Individual test case creation form."""
    input_data = TextAreaField('Test Case Input (stdin)', validators=[DataRequired()])
    expected_output = TextAreaField('Expected Output (stdout)', validators=[DataRequired()])
    is_hidden = BooleanField('Hidden Test Case (Used for evaluation, hidden from students)', default=False)
    points = IntegerField('Marks / Points', validators=[DataRequired(), NumberRange(min=1, max=100)], default=10)
    submit = SubmitField('Save Test Case')
