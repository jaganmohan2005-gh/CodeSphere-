"""
CodeSphere - AI Learning Assistant Routes
-----------------------------------------
Interactive educational interface providing programming concept explanations,
progressive coding hints, code error diagnosis, personalized study plans,
and persistent conversation history with student data isolation.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.routes.decorators import student_required
from app.models.ai import AIConversation, AIMessage
from app.models.question import Question
from app.models.submission import StudentProgress
from app.models.assessment import AssessmentAttempt
from app.services.ai_service import ai_service
from app.services.analytics_service import analytics_service

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')


@ai_bp.route('/')
@login_required
@student_required
def assistant():
    """Main AI Learning Assistant portal with chat history and interactive tools."""
    # Fetch student's own conversations (enforcing isolation)
    conversations = AIConversation.query.filter_by(user_id=current_user.id)\
        .order_by(AIConversation.updated_at.desc()).all()

    active_conv_id = request.args.get('conv_id', type=int)
    active_conv = None
    if active_conv_id:
        active_conv = AIConversation.query.filter_by(id=active_conv_id, user_id=current_user.id).first()

    if not active_conv and conversations:
        active_conv = conversations[0]

    # Published questions list for hint tool dropdown
    questions = Question.query.filter_by(is_published=True).order_by(Question.title).all()

    # Student progress for study plan generator
    analytics = analytics_service.get_student_analytics(current_user.id)

    return render_template(
        'ai/assistant.html',
        conversations=conversations,
        active_conv=active_conv,
        questions=questions,
        analytics=analytics
    )


@ai_bp.route('/conversations/new', methods=['POST'])
@login_required
@student_required
def new_conversation():
    """Creates a new empty chat session."""
    title = request.form.get('title', 'New Placement Tutoring Session').strip()
    conv = AIConversation(
        user_id=current_user.id,
        title=title[:140] if title else 'New Placement Tutoring Session',
        topic='General Tutoring'
    )
    db.session.add(conv)
    db.session.commit()
    return redirect(url_for('ai.assistant', conv_id=conv.id))


@ai_bp.route('/conversations/<int:conv_id>/delete', methods=['POST'])
@login_required
@student_required
def delete_conversation(conv_id):
    """Deletes an AI conversation (student data isolation enforced)."""
    conv = AIConversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    db.session.delete(conv)
    db.session.commit()
    flash("Learning conversation removed.", "info")
    return redirect(url_for('ai.assistant'))


@ai_bp.route('/chat', methods=['POST'])
@login_required
@student_required
def chat():
    """
    AJAX endpoint for chat conversations with the AI Assistant.
    Validates rate limits and request length.
    """
    if ai_service.is_rate_limited(current_user.id):
        return jsonify({
            'error': 'Rate limit reached (max 15 requests/min). Please pause for a moment to let our tutor catch up.'
        }), 429

    data = request.get_json() or {}
    message_text = data.get('message', '').strip()
    conv_id = data.get('conversation_id')

    if not message_text:
        return jsonify({'error': 'Message content cannot be empty.'}), 400

    if len(message_text) > 4000:
        return jsonify({'error': 'Message is too long. Please shorten your query.'}), 400

    # Retrieve or create conversation
    conv = None
    if conv_id:
        conv = AIConversation.query.filter_by(id=conv_id, user_id=current_user.id).first()

    if not conv:
        conv = AIConversation(
            user_id=current_user.id,
            title=message_text[:40] + ('...' if len(message_text) > 40 else ''),
            topic='General Tutoring'
        )
        db.session.add(conv)
        db.session.flush()

    # Save User message
    user_msg = AIMessage(
        conversation_id=conv.id,
        sender='user',
        content=message_text,
        is_fallback=False
    )
    db.session.add(user_msg)

    # Generate response
    ai_resp = ai_service.explain_concept(message_text)

    # Save Assistant response
    assistant_msg = AIMessage(
        conversation_id=conv.id,
        sender='assistant',
        content=ai_resp['content'],
        is_fallback=ai_resp.get('is_fallback', False)
    )
    db.session.add(assistant_msg)

    conv.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'status': 'success',
        'conversation_id': conv.id,
        'response': ai_resp['content'],
        'is_fallback': ai_resp.get('is_fallback', False),
        'model': ai_resp.get('model', 'CodeSphere AI Tutor')
    })


@ai_bp.route('/hint', methods=['POST'])
@login_required
@student_required
def get_hint():
    """
    AJAX endpoint for progressive hints on a specific problem.
    """
    if ai_service.is_rate_limited(current_user.id):
        return jsonify({'error': 'Rate limit reached. Please wait a moment.'}), 429

    data = request.get_json() or {}
    question_id = data.get('question_id')
    hint_level = int(data.get('hint_level', 1))
    current_code = data.get('current_code', '')

    question = Question.query.filter_by(id=question_id, is_published=True).first_or_404()

    hint_resp = ai_service.get_progressive_hint(
        question_title=question.title,
        question_description=question.description,
        current_code=current_code,
        hint_level=hint_level
    )

    return jsonify({
        'status': 'success',
        'hint': hint_resp['content'],
        'hint_level': hint_level,
        'is_fallback': hint_resp.get('is_fallback', False)
    })


@ai_bp.route('/debug', methods=['POST'])
@login_required
@student_required
def debug_code():
    """
    AJAX endpoint for code error diagnosis and logic explanation.
    """
    if ai_service.is_rate_limited(current_user.id):
        return jsonify({'error': 'Rate limit reached. Please wait a moment.'}), 429

    data = request.get_json() or {}
    question_title = data.get('question_title', 'Coding Question')
    code = data.get('code', '').strip()
    language = data.get('language', 'python')
    error_message = data.get('error_message', '')
    expected_output = data.get('expected_output', '')
    actual_output = data.get('actual_output', '')

    if not code:
        return jsonify({'error': 'Please provide code for analysis.'}), 400

    debug_resp = ai_service.diagnose_code_error(
        question_title=question_title,
        code=code,
        language=language,
        error_message=error_message,
        expected_output=expected_output,
        actual_output=actual_output
    )

    return jsonify({
        'status': 'success',
        'diagnosis': debug_resp['content'],
        'is_fallback': debug_resp.get('is_fallback', False)
    })


@ai_bp.route('/study-plan', methods=['POST'])
@login_required
@student_required
def generate_study_plan():
    """
    Generates a personalized study plan using real student analytics.
    """
    if ai_service.is_rate_limited(current_user.id):
        return jsonify({'error': 'Rate limit reached. Please wait a moment.'}), 429

    data = request.get_json() or {}
    weeks = int(data.get('weeks', 4))
    target_role = data.get('target_role') or (current_user.profile.target_role if current_user.profile else 'Software Engineer')

    analytics = analytics_service.get_student_analytics(current_user.id)
    weak_topics = analytics.get('weak_topics', [])
    solved_count = analytics.get('total_solved', 0)

    plan_resp = ai_service.generate_study_plan(
        target_role=target_role,
        available_weeks=weeks,
        weak_topics=weak_topics,
        solved_count=solved_count
    )

    return jsonify({
        'status': 'success',
        'plan': plan_resp['plan'],
        'weeks': weeks,
        'is_fallback': plan_resp.get('is_fallback', False)
    })
