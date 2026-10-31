"""
CodeSphere - Student Experience & Practice Routes
-------------------------------------------------
Handles the student dashboard, self-paced coding practice problem bank,
interactive code submission & sandboxed test runner, and performance analytics.
Strictly protected to enforce student data isolation.
"""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.routes.decorators import student_required
from app.models.question import Question, Category, TestCase
from app.models.assessment import Assessment, AssessmentAttempt
from app.models.submission import Submission, SubmissionTestResult, StudentProgress
from app.models.notification import Notification
from app.services.analytics_service import analytics_service
from app.services.code_executor import code_executor

student_bp = Blueprint('student', __name__)


@student_bp.route('/')
def home():
    """Landing redirection: redirects authenticated users to their dashboard, otherwise to landing/login."""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard' if current_user.is_admin else 'student.dashboard'))
    return redirect(url_for('auth.login'))


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    """Renders student dashboard with progress summary, upcoming assessments, and personalized metrics."""
    analytics = analytics_service.get_student_analytics(current_user.id)
    
    # Active/available assessments
    available_assessments = Assessment.query.filter_by(is_published=True).all()
    
    # Check if student has active in-progress assessment attempt
    active_attempt = AssessmentAttempt.query.filter_by(
        user_id=current_user.id,
        status='in_progress'
    ).first()

    return render_template(
        'student/dashboard.html',
        analytics=analytics,
        available_assessments=available_assessments,
        active_attempt=active_attempt
    )


@student_bp.route('/practice')
@login_required
@student_required
def practice_list():
    """Lists published coding practice problems with filtering by category and difficulty."""
    cat_slug = request.args.get('category', '')
    difficulty = request.args.get('difficulty', '')
    search = request.args.get('q', '').strip()

    query = Question.query.filter_by(is_published=True)

    if cat_slug:
        cat = Category.query.filter_by(slug=cat_slug).first()
        if cat:
            query = query.filter(Question.category_id == cat.id)

    if difficulty:
        query = query.filter(Question.difficulty == difficulty)

    if search:
        query = query.filter(Question.title.ilike(f'%{search}%'))

    questions = query.order_by(Question.created_at.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()

    # Track student solved state for each question
    solved_q_ids = set(
        r[0] for r in db.session.query(Submission.question_id)
        .filter(Submission.user_id == current_user.id, Submission.status == 'Accepted')
        .all()
    )

    return render_template(
        'student/practice_list.html',
        questions=questions,
        categories=categories,
        solved_q_ids=solved_q_ids,
        selected_cat=cat_slug,
        selected_diff=difficulty,
        search_query=search
    )


@student_bp.route('/practice/<slug>')
@login_required
@student_required
def practice_solve(slug):
    """
    Interactive coding workbench for solving an individual problem.
    Provides split-screen problem description and editor.
    """
    question = Question.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    # Fetch student's most recent code for this question if exists
    latest_sub = Submission.query.filter_by(
        user_id=current_user.id,
        question_id=question.id
    ).order_by(Submission.submitted_at.desc()).first()

    starter_code = latest_sub.source_code if latest_sub else (question.starter_code_python or "# Write your Python solution here\nimport sys\n\ndef solve():\n    pass\n\nif __name__ == '__main__':\n    solve()\n")

    return render_template(
        'student/practice_solve.html',
        question=question,
        starter_code=starter_code,
        public_test_cases=question.public_test_cases
    )


@student_bp.route('/practice/<slug>/run-tests', methods=['POST'])
@login_required
@student_required
def practice_run_tests(slug):
    """
    AJAX endpoint to run student's code against public sample test cases.
    Does not permanently record a submission.
    """
    question = Question.query.filter_by(slug=slug, is_published=True).first_or_404()
    data = request.get_json() or {}
    code = data.get('code', '')
    language = data.get('language', 'python')

    # Run exclusively against public test cases
    sample_tests = question.public_test_cases
    if not sample_tests:
        # Fallback if no public test cases defined, create ad-hoc from sample input
        sample_tests = [TestCase(
            id=0,
            question_id=question.id,
            input_data=question.sample_input or "",
            expected_output=question.sample_output or "",
            is_hidden=False,
            points=10
        )]

    eval_result = code_executor.evaluate_submission(
        code=code,
        language=language,
        test_cases=sample_tests,
        is_assessment=False
    )

    return jsonify({
        'status': eval_result.status,
        'execution_time_ms': eval_result.execution_time_ms,
        'tests_passed': eval_result.tests_passed,
        'tests_total': eval_result.tests_total,
        'error_message': eval_result.error_message,
        'test_details': eval_result.test_details
    })


@student_bp.route('/practice/<slug>/submit', methods=['POST'])
@login_required
@student_required
def practice_submit(slug):
    """
    AJAX endpoint to officially submit a solution. Evaluates against all
    (public and hidden) test cases, records Submission and TestResults,
    and updates student topic progress.
    """
    question = Question.query.filter_by(slug=slug, is_published=True).first_or_404()
    data = request.get_json() or {}
    code = data.get('code', '')
    language = data.get('language', 'python')

    # Fetch all test cases (both public and hidden)
    test_cases = question.test_cases
    if not test_cases:
        test_cases = [TestCase(
            id=0,
            question_id=question.id,
            input_data=question.sample_input or "",
            expected_output=question.sample_output or "",
            is_hidden=False,
            points=10
        )]

    eval_result = code_executor.evaluate_submission(
        code=code,
        language=language,
        test_cases=test_cases,
        is_assessment=False
    )

    # 1. Record official Submission in database
    submission = Submission(
        user_id=current_user.id,
        question_id=question.id,
        source_code=code,
        language=language,
        status=eval_result.status,
        execution_time_ms=eval_result.execution_time_ms,
        tests_passed=eval_result.tests_passed,
        tests_total=eval_result.tests_total
    )
    db.session.add(submission)
    db.session.flush()

    # 2. Record detailed test case results
    for td in eval_result.test_details:
        if td.get('test_case_id') and td['test_case_id'] > 0:
            tr = SubmissionTestResult(
                submission_id=submission.id,
                test_case_id=td['test_case_id'],
                is_passed=td['is_passed'],
                actual_output=td['actual_output'],
                error_message=td['error_message'],
                execution_time_ms=td['execution_time_ms']
            )
            db.session.add(tr)

    # 3. Update or create StudentProgress for question's category
    progress = StudentProgress.query.filter_by(
        user_id=current_user.id,
        category_id=question.category_id
    ).first()

    if not progress:
        progress = StudentProgress(
            user_id=current_user.id,
            category_id=question.category_id,
            questions_attempted=1,
            questions_solved=1 if eval_result.is_accepted else 0
        )
        db.session.add(progress)
    else:
        # Check if already previously solved
        previously_solved = Submission.query.filter_by(
            user_id=current_user.id,
            question_id=question.id,
            status='Accepted'
        ).count() > 0

        # Recalculate distinct attempted and solved
        progress.questions_attempted = db.session.query(Submission.question_id)\
            .join(Question)\
            .filter(Submission.user_id == current_user.id, Question.category_id == question.category_id)\
            .distinct().count()

        progress.questions_solved = db.session.query(Submission.question_id)\
            .join(Question)\
            .filter(Submission.user_id == current_user.id, Question.category_id == question.category_id, Submission.status == 'Accepted')\
            .distinct().count()

    progress.recalculate_accuracy()
    db.session.commit()

    return jsonify({
        'status': eval_result.status,
        'submission_id': submission.id,
        'execution_time_ms': eval_result.execution_time_ms,
        'tests_passed': eval_result.tests_passed,
        'tests_total': eval_result.tests_total,
        'error_message': eval_result.error_message,
        'test_details': eval_result.test_details
    })


@student_bp.route('/analytics')
@login_required
@student_required
def analytics():
    """Displays student performance metrics, progress charts, weak topics, and assessment history."""
    metrics = analytics_service.get_student_analytics(current_user.id)
    return render_template('student/analytics.html', metrics=metrics)


@student_bp.route('/submissions')
@login_required
@student_required
def submissions_history():
    """Lists student's personal submission history (isolated strictly to current_user)."""
    submissions = Submission.query.filter_by(user_id=current_user.id)\
        .order_by(Submission.submitted_at.desc()).all()
    return render_template('student/submissions.html', submissions=submissions)
