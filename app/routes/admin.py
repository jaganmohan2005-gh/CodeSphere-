"""
CodeSphere - Administrator Management Routes
--------------------------------------------
Provides comprehensive administration over students, coding questions,
categories, formal assessments, test case management, and CSV result exports.
Protected by the strict @admin_required decorator.
"""

import io
import csv
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.routes.decorators import admin_required
from app.models.user import User, StudentProfile
from app.models.question import Category, Question, TestCase
from app.models.assessment import Assessment, AssessmentQuestion, AssessmentAttempt, AttemptAnswer
from app.models.submission import Submission
from app.models.notification import Notification
from app.services.analytics_service import analytics_service
from app.forms.question_forms import CategoryForm, QuestionForm, TestCaseForm
from app.forms.assessment_forms import AssessmentForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# -----------------------------------------------------------------------------
# MODULE 2: Admin Dashboard
# -----------------------------------------------------------------------------
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Renders the administrative dashboard with real-time database-calculated statistics."""
    stats = analytics_service.get_admin_dashboard_stats()
    return render_template('admin/dashboard.html', stats=stats)


# -----------------------------------------------------------------------------
# MODULE 3: Student Management
# -----------------------------------------------------------------------------
@admin_bp.route('/students')
@login_required
@admin_required
def students_list():
    """Lists registered students with search, filter, and activation status."""
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all')

    query = User.query.filter_by(role='student')

    if search_query:
        query = query.join(StudentProfile, isouter=True).filter(
            (User.username.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%')) |
            (StudentProfile.full_name.ilike(f'%{search_query}%'))
        )

    if status_filter == 'active':
        query = query.filter(User.is_active_account == True)
    elif status_filter == 'inactive':
        query = query.filter(User.is_active_account == False)

    students = query.order_by(User.created_at.desc()).all()
    return render_template('admin/students.html', students=students, search_query=search_query, status_filter=status_filter)


@admin_bp.route('/students/<int:student_id>')
@login_required
@admin_required
def student_detail(student_id):
    """Inspects detailed profile, assessment history, and coding analytics for a specific student."""
    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    analytics = analytics_service.get_student_analytics(student.id)
    return render_template('admin/student_detail.html', student=student, analytics=analytics)


@admin_bp.route('/students/<int:student_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_student_status(student_id):
    """Activates or deactivates a student account."""
    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    student.is_active_account = not student.is_active_account
    db.session.commit()

    status_str = "activated" if student.is_active_account else "deactivated"
    flash(f"Student account '{student.username}' has been {status_str}.", "success")
    return redirect(url_for('admin.student_detail', student_id=student.id))


# -----------------------------------------------------------------------------
# MODULE 4: Question Category Management
# -----------------------------------------------------------------------------
@admin_bp.route('/categories')
@login_required
@admin_required
def categories_list():
    """Displays all question categories with question counts."""
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
@admin_required
def category_create():
    """Creates a new question category."""
    form = CategoryForm()
    if form.validate_on_submit():
        existing = Category.query.filter(
            (Category.name == form.name.data.strip()) | (Category.slug == form.slug.data.strip().lower())
        ).first()
        if existing:
            flash("A category with this name or slug already exists.", "warning")
            return render_template('admin/category_form.html', form=form, action="Create")

        cat = Category(
            name=form.name.data.strip(),
            slug=form.slug.data.strip().lower(),
            description=form.description.data.strip() if form.description.data else None,
            icon=form.icon.data
        )
        db.session.add(cat)
        db.session.commit()
        flash(f"Category '{cat.name}' created successfully.", "success")
        return redirect(url_for('admin.categories_list'))

    return render_template('admin/category_form.html', form=form, action="Create")


@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def category_edit(category_id):
    """Edits an existing category."""
    cat = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=cat)

    if form.validate_on_submit():
        cat.name = form.name.data.strip()
        cat.slug = form.slug.data.strip().lower()
        cat.description = form.description.data.strip() if form.description.data else None
        cat.icon = form.icon.data
        db.session.commit()
        flash(f"Category '{cat.name}' updated.", "success")
        return redirect(url_for('admin.categories_list'))

    return render_template('admin/category_form.html', form=form, action="Edit", category=cat)


@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def category_delete(category_id):
    """Safely deletes a category only if no questions reference it."""
    cat = Category.query.get_or_404(category_id)
    if not cat.can_be_safely_deleted():
        flash(f"Cannot delete category '{cat.name}': It currently contains {cat.question_count} coding questions. Please reassign or delete the questions first.", "danger")
        return redirect(url_for('admin.categories_list'))

    db.session.delete(cat)
    db.session.commit()
    flash(f"Category '{cat.name}' deleted successfully.", "success")
    return redirect(url_for('admin.categories_list'))


# -----------------------------------------------------------------------------
# MODULE 5: Coding Question Management
# -----------------------------------------------------------------------------
@admin_bp.route('/questions')
@login_required
@admin_required
def questions_list():
    """Lists all coding questions with search and category filters."""
    category_id = request.args.get('category_id', type=int)
    difficulty = request.args.get('difficulty', '')
    search = request.args.get('q', '').strip()

    query = Question.query

    if category_id:
        query = query.filter(Question.category_id == category_id)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    if search:
        query = query.filter(Question.title.ilike(f'%{search}%'))

    questions = query.order_by(Question.created_at.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'admin/questions.html',
        questions=questions,
        categories=categories,
        selected_cat=category_id,
        selected_diff=difficulty,
        search_query=search
    )


@admin_bp.route('/questions/create', methods=['GET', 'POST'])
@login_required
@admin_required
def question_create():
    """Creates a new coding question."""
    form = QuestionForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]

    if form.validate_on_submit():
        base_slug = form.title.data.lower().strip().replace(' ', '-')
        slug = "".join([c for c in base_slug if c.isalnum() or c == '-'])
        # Ensure unique slug
        counter = 1
        original_slug = slug
        while Question.query.filter_by(slug=slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1

        question = Question(
            category_id=form.category_id.data,
            title=form.title.data.strip(),
            slug=slug,
            difficulty=form.difficulty.data,
            description=form.description.data,
            constraints=form.constraints.data,
            sample_input=form.sample_input.data,
            sample_output=form.sample_output.data,
            explanation=form.explanation.data,
            time_complexity_expected=form.time_complexity_expected.data,
            space_complexity_expected=form.space_complexity_expected.data,
            starter_code_python=form.starter_code_python.data,
            starter_code_java=form.starter_code_java.data,
            starter_code_cpp=form.starter_code_cpp.data,
            is_published=form.is_published.data
        )
        db.session.add(question)
        db.session.flush()

        # If sample input and output were provided, automatically create a default sample TestCase
        if form.sample_input.data and form.sample_output.data:
            sample_tc = TestCase(
                question_id=question.id,
                input_data=form.sample_input.data,
                expected_output=form.sample_output.data,
                is_hidden=False,
                points=10
            )
            db.session.add(sample_tc)

        db.session.commit()
        flash(f"Question '{question.title}' created! Now add additional hidden and public test cases below.", "success")
        return redirect(url_for('admin.question_test_cases', question_id=question.id))

    return render_template('admin/question_form.html', form=form, action="Create")


@admin_bp.route('/questions/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def question_edit(question_id):
    """Edits an existing question's problem statement and metadata."""
    question = Question.query.get_or_404(question_id)
    form = QuestionForm(obj=question)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]

    if form.validate_on_submit():
        question.category_id = form.category_id.data
        question.title = form.title.data.strip()
        question.difficulty = form.difficulty.data
        question.description = form.description.data
        question.constraints = form.constraints.data
        question.sample_input = form.sample_input.data
        question.sample_output = form.sample_output.data
        question.explanation = form.explanation.data
        question.time_complexity_expected = form.time_complexity_expected.data
        question.space_complexity_expected = form.space_complexity_expected.data
        question.starter_code_python = form.starter_code_python.data
        question.starter_code_java = form.starter_code_java.data
        question.starter_code_cpp = form.starter_code_cpp.data
        question.is_published = form.is_published.data

        db.session.commit()
        flash(f"Question '{question.title}' updated successfully.", "success")
        return redirect(url_for('admin.questions_list'))

    return render_template('admin/question_form.html', form=form, action="Edit", question=question)


@admin_bp.route('/questions/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def question_delete(question_id):
    """Deletes a question and cascades associated test cases and submissions."""
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash(f"Question '{question.title}' deleted.", "success")
    return redirect(url_for('admin.questions_list'))


@admin_bp.route('/questions/<int:question_id>/test-cases', methods=['GET', 'POST'])
@login_required
@admin_required
def question_test_cases(question_id):
    """Manages public sample test cases and hidden evaluation test cases for a question."""
    question = Question.query.get_or_404(question_id)
    form = TestCaseForm()

    if form.validate_on_submit():
        tc = TestCase(
            question_id=question.id,
            input_data=form.input_data.data,
            expected_output=form.expected_output.data,
            is_hidden=form.is_hidden.data,
            points=form.points.data
        )
        db.session.add(tc)
        db.session.commit()
        flash("New test case registered successfully.", "success")
        return redirect(url_for('admin.question_test_cases', question_id=question.id))

    test_cases = question.test_cases
    return render_template('admin/question_test_cases.html', question=question, test_cases=test_cases, form=form)


@admin_bp.route('/test-cases/<int:test_case_id>/delete', methods=['POST'])
@login_required
@admin_required
def test_case_delete(test_case_id):
    """Deletes an individual test case."""
    tc = TestCase.query.get_or_404(test_case_id)
    q_id = tc.question_id
    db.session.delete(tc)
    db.session.commit()
    flash("Test case removed.", "info")
    return redirect(url_for('admin.question_test_cases', question_id=q_id))


# -----------------------------------------------------------------------------
# MODULE 6: Assessment Management
# -----------------------------------------------------------------------------
@admin_bp.route('/assessments')
@login_required
@admin_required
def assessments_list():
    """Lists all timed assessments with statistics and status."""
    assessments = Assessment.query.order_by(Assessment.created_at.desc()).all()
    return render_template('admin/assessments.html', assessments=assessments)


@admin_bp.route('/assessments/create', methods=['GET', 'POST'])
@login_required
@admin_required
def assessment_create():
    """Creates a new assessment with selected questions and mark weights."""
    form = AssessmentForm()
    available_questions = Question.query.filter_by(is_published=True).order_by(Question.title).all()

    if form.validate_on_submit():
        selected_q_ids = request.form.getlist('selected_questions')
        if not selected_q_ids:
            flash("Please select at least one coding question for this assessment.", "warning")
            return render_template('admin/assessment_form.html', form=form, questions=available_questions, action="Create")

        assessment = Assessment(
            title=form.title.data.strip(),
            description=form.description.data,
            difficulty=form.difficulty.data,
            duration_minutes=form.duration_minutes.data,
            pass_percentage=form.pass_percentage.data,
            results_released_immediately=form.results_released_immediately.data,
            retake_allowed=form.retake_allowed.data,
            is_published=form.is_published.data,
            created_by_user_id=current_user.id
        )
        db.session.add(assessment)
        db.session.flush()

        # Attach chosen questions with order and marks
        for idx, q_id in enumerate(selected_q_ids, 1):
            mark_key = f"marks_{q_id}"
            marks = int(request.form.get(mark_key, 25))
            aq = AssessmentQuestion(
                assessment_id=assessment.id,
                question_id=int(q_id),
                order_index=idx,
                marks=marks
            )
            db.session.add(aq)

        # If published, broadcast notification to all students
        if assessment.is_published:
            students = User.query.filter_by(role='student').all()
            for s in students:
                notif = Notification(
                    user_id=s.id,
                    title="New Assessment Published",
                    message=f"Assessment '{assessment.title}' is now open! Duration: {assessment.duration_minutes} mins.",
                    type="assessment",
                    link=f"/assessments/{assessment.id}"
                )
                db.session.add(notif)

        db.session.commit()
        flash(f"Assessment '{assessment.title}' created successfully!", "success")
        return redirect(url_for('admin.assessment_detail', assessment_id=assessment.id))

    return render_template('admin/assessment_form.html', form=form, questions=available_questions, action="Create")


@admin_bp.route('/assessments/<int:assessment_id>')
@login_required
@admin_required
def assessment_detail(assessment_id):
    """Shows assessment metrics: average marks, highest marks, completion rate, and student attempts."""
    assessment = Assessment.query.get_or_404(assessment_id)
    attempts = AssessmentAttempt.query.filter_by(assessment_id=assessment.id)\
        .order_by(AssessmentAttempt.created_at.desc()).all()

    completed_attempts = [a for a in attempts if a.status in ['completed', 'timed_out', 'evaluated']]
    completed_count = len(completed_attempts)
    total_enrolled = len(attempts)

    completion_rate = round((completed_count / total_enrolled * 100.0), 1) if total_enrolled > 0 else 0.0
    scores = [a.percentage for a in completed_attempts]
    avg_score = round(sum(scores) / completed_count, 1) if completed_count > 0 else 0.0
    highest_score = round(max(scores), 1) if scores else 0.0

    return render_template(
        'admin/assessment_detail.html',
        assessment=assessment,
        attempts=attempts,
        completed_count=completed_count,
        total_enrolled=total_enrolled,
        completion_rate=completion_rate,
        avg_score=avg_score,
        highest_score=highest_score
    )


@admin_bp.route('/assessments/<int:assessment_id>/toggle-publish', methods=['POST'])
@login_required
@admin_required
def assessment_toggle_publish(assessment_id):
    """Toggles assessment published status."""
    assessment = Assessment.query.get_or_404(assessment_id)
    assessment.is_published = not assessment.is_published
    db.session.commit()

    state = "published" if assessment.is_published else "unpublished"
    flash(f"Assessment '{assessment.title}' is now {state}.", "success")
    return redirect(url_for('admin.assessment_detail', assessment_id=assessment.id))


@admin_bp.route('/assessments/<int:assessment_id>/delete', methods=['POST'])
@login_required
@admin_required
def assessment_delete(assessment_id):
    """Deletes an assessment and its associated questions and attempts."""
    assessment = Assessment.query.get_or_404(assessment_id)
    db.session.delete(assessment)
    db.session.commit()
    flash(f"Assessment '{assessment.title}' deleted.", "success")
    return redirect(url_for('admin.assessments_list'))


@admin_bp.route('/assessments/<int:assessment_id>/export-csv')
@login_required
@admin_required
def assessment_export_csv(assessment_id):
    """Exports student assessment results and metrics into a downloadable CSV."""
    assessment = Assessment.query.get_or_404(assessment_id)
    attempts = AssessmentAttempt.query.filter_by(assessment_id=assessment.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    # Header row
    writer.writerow([
        'Attempt ID',
        'Student Username',
        'Student Email',
        'College',
        'Status',
        'Score Awarded',
        'Max Possible Score',
        'Percentage (%)',
        'Passed',
        'Start Time (UTC)',
        'Submission Time (UTC)'
    ])

    for a in attempts:
        user = a.user
        profile = user.profile
        college = profile.college if profile and profile.college else 'N/A'
        writer.writerow([
            a.id,
            user.username,
            user.email,
            college,
            a.status,
            a.total_score,
            a.max_possible_score,
            a.percentage,
            'Yes' if a.is_passed else 'No',
            a.start_time.strftime('%Y-%m-%d %H:%M:%S') if a.start_time else 'N/A',
            a.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if a.submitted_at else 'In Progress'
        ])

    csv_data = output.getvalue()
    filename = f"codesphere_assessment_{assessment.id}_results.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
