"""
CodeSphere - Timed Assessment Experience Routes
------------------------------------------------
Manages student assessment flow: timed start, autosaving answers, question navigation,
secure server-side deadline validation, automated grading, and result releases.
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.routes.decorators import student_required
from app.models.question import Question, TestCase
from app.models.assessment import Assessment, AssessmentQuestion, AssessmentAttempt, AttemptAnswer
from app.models.submission import Submission, SubmissionTestResult, StudentProgress
from app.models.notification import Notification
from app.services.code_executor import code_executor

assessment_bp = Blueprint('assessment', __name__, url_prefix='/assessments')


@assessment_bp.route('/')
@login_required
def list_assessments():
    """Lists published assessments with student attempt indicators."""
    assessments = Assessment.query.filter_by(is_published=True).order_by(Assessment.created_at.desc()).all()
    
    # Map user's attempts per assessment
    user_attempts = {}
    if current_user.is_authenticated and current_user.is_student:
        attempts = AssessmentAttempt.query.filter_by(user_id=current_user.id).all()
        for att in attempts:
            user_attempts[att.assessment_id] = att

    return render_template('assessments/list.html', assessments=assessments, user_attempts=user_attempts)


@assessment_bp.route('/<int:assessment_id>/start', methods=['POST'])
@login_required
@student_required
def start_assessment(assessment_id):
    """
    Initializes a timed assessment attempt with server-side deadline enforcement.
    Prevents unauthorized retakes unless permitted by configuration.
    """
    assessment = Assessment.query.get_or_404(assessment_id)

    if not assessment.is_currently_available():
        flash("This assessment is currently unavailable or closed.", "warning")
        return redirect(url_for('assessment.list_assessments'))

    # Check for active unfinished attempt (safe resumption)
    active_attempt = AssessmentAttempt.query.filter_by(
        assessment_id=assessment.id,
        user_id=current_user.id,
        status='in_progress'
    ).first()

    if active_attempt:
        # Check if already expired server-side
        if active_attempt.is_expired:
            _finalize_attempt(active_attempt, is_timeout=True)
            flash("Your previous session timed out and was automatically submitted.", "warning")
            return redirect(url_for('assessment.view_result', attempt_id=active_attempt.id))
        flash("Resuming your active assessment session.", "info")
        return redirect(url_for('assessment.take_assessment', attempt_id=active_attempt.id))

    # Check retake policy if already completed
    past_attempt = AssessmentAttempt.query.filter_by(
        assessment_id=assessment.id,
        user_id=current_user.id
    ).filter(AssessmentAttempt.status.in_(['completed', 'timed_out', 'evaluated'])).first()

    if past_attempt and not assessment.retake_allowed:
        flash("You have already completed this assessment. Retakes are not permitted.", "info")
        return redirect(url_for('assessment.view_result', attempt_id=past_attempt.id))

    # Calculate strict server-side deadline
    now = datetime.utcnow()
    deadline = now + timedelta(minutes=assessment.duration_minutes)

    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        user_id=current_user.id,
        start_time=now,
        deadline_time=deadline,
        status='in_progress',
        max_possible_score=float(assessment.total_marks)
    )
    db.session.add(attempt)
    db.session.flush()

    # Pre-populate AttemptAnswer records for each assessment question
    for aq in assessment.assessment_questions:
        q = aq.question
        default_code = q.starter_code_python or f"# Solution for: {q.title}\nimport sys\n\ndef solve():\n    pass\n\nif __name__ == '__main__':\n    solve()\n"
        ans = AttemptAnswer(
            attempt_id=attempt.id,
            question_id=q.id,
            code=default_code,
            language='python',
            status='unanswered',
            score_awarded=0.0
        )
        db.session.add(ans)

    db.session.commit()
    flash(f"Assessment started! You have {assessment.duration_minutes} minutes.", "success")
    return redirect(url_for('assessment.take_assessment', attempt_id=attempt.id))


@assessment_bp.route('/attempt/<int:attempt_id>')
@login_required
@student_required
def take_assessment(attempt_id):
    """
    Renders the live assessment testing environment with timer countdown,
    question switcher, auto-save hook, and submission control.
    """
    attempt = AssessmentAttempt.query.get_or_404(attempt_id)

    # 1. Enforce student data isolation: students cannot access another student's attempt
    if attempt.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    # 2. Strict server-side deadline verification
    if attempt.status != 'in_progress':
        return redirect(url_for('assessment.view_result', attempt_id=attempt.id))

    if attempt.is_expired:
        _finalize_attempt(attempt, is_timeout=True)
        flash("Assessment time limit expired. Your saved answers have been submitted.", "warning")
        return redirect(url_for('assessment.view_result', attempt_id=attempt.id))

    # Load assessment questions and answers
    assessment = attempt.assessment
    aq_list = assessment.assessment_questions
    answers_map = {ans.question_id: ans for ans in attempt.answers}

    # Selected question index (1-based)
    current_q_idx = request.args.get('q', 1, type=int)
    if current_q_idx < 1 or current_q_idx > len(aq_list):
        current_q_idx = 1

    current_aq = aq_list[current_q_idx - 1]
    current_answer = answers_map.get(current_aq.question_id)

    return render_template(
        'assessments/take.html',
        attempt=attempt,
        assessment=assessment,
        aq_list=aq_list,
        current_q_idx=current_q_idx,
        current_aq=current_aq,
        current_answer=current_answer,
        answers_map=answers_map,
        remaining_seconds=attempt.remaining_seconds
    )


@assessment_bp.route('/attempt/<int:attempt_id>/autosave', methods=['POST'])
@login_required
@student_required
def autosave_answer(attempt_id):
    """
    AJAX endpoint to auto-save code for a question while the assessment is running.
    Validates server-side deadline before allowing write.
    """
    attempt = AssessmentAttempt.query.get_or_404(attempt_id)

    if attempt.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    if attempt.is_expired:
        _finalize_attempt(attempt, is_timeout=True)
        return jsonify({
            'status': 'expired',
            'message': 'Assessment deadline has passed. Automatically finalized.',
            'redirect_url': url_for('assessment.view_result', attempt_id=attempt.id)
        }), 200

    data = request.get_json() or {}
    question_id = data.get('question_id')
    code = data.get('code', '')
    language = data.get('language', 'python')

    answer = AttemptAnswer.query.filter_by(attempt_id=attempt.id, question_id=question_id).first()
    if answer:
        answer.code = code
        answer.language = language
        answer.status = 'saved' if code.strip() else 'unanswered'
        answer.last_saved_at = datetime.utcnow()
        db.session.commit()

    return jsonify({
        'status': 'saved',
        'remaining_seconds': attempt.remaining_seconds,
        'timestamp': datetime.utcnow().strftime('%H:%M:%S')
    })


@assessment_bp.route('/attempt/<int:attempt_id>/run-sample', methods=['POST'])
@login_required
@student_required
def run_sample_tests(attempt_id):
    """
    Runs code against sample test cases ONLY during assessment.
    Hidden assessment test cases are NEVER run or revealed here.
    """
    attempt = AssessmentAttempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    if attempt.is_expired:
        _finalize_attempt(attempt, is_timeout=True)
        return jsonify({'status': 'expired', 'message': 'Assessment deadline expired.'}), 400

    data = request.get_json() or {}
    question_id = data.get('question_id')
    code = data.get('code', '')
    language = data.get('language', 'python')

    question = Question.query.get_or_404(question_id)
    sample_tests = question.public_test_cases

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


@assessment_bp.route('/attempt/<int:attempt_id>/submit', methods=['POST'])
@login_required
@student_required
def submit_assessment(attempt_id):
    """
    Finalizes assessment submission, evaluates all questions against hidden test cases,
    computes scores, and records results.
    """
    attempt = AssessmentAttempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        abort(403)

    if attempt.status != 'in_progress':
        flash("This assessment attempt has already been submitted.", "info")
        return redirect(url_for('assessment.view_result', attempt_id=attempt.id))

    is_timeout = attempt.is_expired
    _finalize_attempt(attempt, is_timeout=is_timeout)

    flash("Assessment submitted and graded successfully!", "success")
    return redirect(url_for('assessment.view_result', attempt_id=attempt.id))


@assessment_bp.route('/attempt/<int:attempt_id>/result')
@login_required
def view_result(attempt_id):
    """
    Displays the student's assessment report, score percentage,
    pass/fail outcome, and question-level breakdown according to admin release settings.
    """
    attempt = AssessmentAttempt.query.get_or_404(attempt_id)

    # Access control: student who took the assessment or admin
    if attempt.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    assessment = attempt.assessment

    return render_template(
        'assessments/result.html',
        attempt=attempt,
        assessment=assessment,
        answers=attempt.answers,
        results_released=assessment.results_released_immediately or current_user.is_admin
    )


def _finalize_attempt(attempt: AssessmentAttempt, is_timeout: bool = False):
    """
    Internal helper to grade all answers, compute weighted scores,
    and update attempt and progress records.
    """
    assessment = attempt.assessment
    aq_map = {aq.question_id: aq for aq in assessment.assessment_questions}

    total_score = 0.0
    max_score = float(assessment.total_marks)

    for ans in attempt.answers:
        aq = aq_map.get(ans.question_id)
        allocated_marks = float(aq.marks) if aq else 10.0
        q = ans.question

        if not ans.code or not ans.code.strip():
            ans.status = 'unanswered'
            ans.score_awarded = 0.0
            continue

        # Evaluate against all test cases (both public and hidden)
        all_tests = q.test_cases
        if not all_tests:
            ans.status = 'passed'
            ans.score_awarded = allocated_marks
            total_score += allocated_marks
            continue

        eval_result = code_executor.evaluate_submission(
            code=ans.code,
            language=ans.language,
            test_cases=all_tests,
            is_assessment=True
        )

        ans.total_test_cases = eval_result.tests_total
        ans.test_cases_passed = eval_result.tests_passed

        # Pro-rata marks based on passed test cases
        if eval_result.tests_total > 0:
            fraction = eval_result.tests_passed / eval_result.tests_total
            earned_marks = round(fraction * allocated_marks, 1)
        else:
            earned_marks = 0.0

        ans.score_awarded = earned_marks
        total_score += earned_marks

        if eval_result.status == 'Accepted':
            ans.status = 'passed'
        elif eval_result.tests_passed > 0:
            ans.status = 'partial'
        else:
            ans.status = 'failed'

        # Store official submission record for student history
        sub = Submission(
            user_id=attempt.user_id,
            question_id=q.id,
            assessment_attempt_id=attempt.id,
            source_code=ans.code,
            language=ans.language,
            status=eval_result.status,
            execution_time_ms=eval_result.execution_time_ms,
            tests_passed=eval_result.tests_passed,
            tests_total=eval_result.tests_total
        )
        db.session.add(sub)

    attempt.submitted_at = datetime.utcnow()
    attempt.status = 'timed_out' if is_timeout else 'completed'
    attempt.total_score = round(total_score, 1)
    attempt.max_possible_score = max_score
    attempt.percentage = round((total_score / max_score * 100.0), 1) if max_score > 0 else 0.0
    attempt.is_passed = attempt.percentage >= assessment.pass_percentage

    # Create completion notification
    notif = Notification(
        user_id=attempt.user_id,
        title="Assessment Completed",
        message=f"You scored {attempt.percentage}% ({attempt.total_score}/{attempt.max_possible_score}) on '{assessment.title}'.",
        type="result",
        link=f"/assessments/attempt/{attempt.id}/result"
    )
    db.session.add(notif)
    db.session.commit()
