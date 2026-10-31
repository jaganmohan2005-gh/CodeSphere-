"""
CodeSphere - AI Assistant & Fallback Engine Tests
-------------------------------------------------
Validates that the AI service gracefully degrades to rich rule-based educational tutoring
when OpenAI API keys are absent or network errors occur, correctly labels fallbacks,
and enforces sliding window rate limits.
"""

from app.services.ai_service import ai_service


def test_ai_fallback_concept_explanation(app):
    """Verifies fallback tutor engine explains core CS concepts offline."""
    with app.app_context():
        res = ai_service.explain_concept('Dynamic Programming', 'Python')
        assert res['status'] in ['success', 'fallback']
        assert 'Dynamic Programming' in res['content'] or 'DP' in res['content']
        assert res['is_fallback'] is True  # In testing with no key configured


def test_ai_fallback_progressive_hints(app):
    """Verifies progressive hints can be generated for levels 1, 2, and 3."""
    with app.app_context():
        h1 = ai_service.get_progressive_hint('Two Sum', 'Find two numbers adding up to target', '', 1)
        assert h1['hint_level'] == 1
        assert h1['is_fallback'] is True

        h2 = ai_service.get_progressive_hint('Two Sum', 'Find two numbers adding up to target', '', 2)
        assert h2['hint_level'] == 2

        h3 = ai_service.get_progressive_hint('Two Sum', 'Find two numbers adding up to target', '', 3)
        assert h3['hint_level'] == 3


def test_ai_fallback_code_error_diagnostics(app):
    """Verifies error diagnosis for common Python exceptions in fallback mode."""
    with app.app_context():
        res = ai_service.diagnose_code_error(
            question_title='Array Iteration',
            code='arr = [1, 2, 3]\nprint(arr[10])',
            language='python',
            error_message='IndexError: list index out of range'
        )
        assert res['is_fallback'] is True
        assert 'Index' in res['content']


def test_ai_fallback_study_plan_generation(app):
    """Verifies personalized study plan formulation based on target role and weak areas."""
    with app.app_context():
        plan = ai_service.generate_study_plan(
            target_role='Backend SDE',
            available_weeks=4,
            weak_topics=['Trees', 'Graphs'],
            solved_count=5
        )
        assert plan['is_fallback'] is True
        assert plan['weeks'] == 4
        assert 'Week 1' in plan['plan']


def test_ai_rate_limiter():
    """Verifies in-memory sliding window rate limiter blocks excessive requests."""
    test_user_id = 99999
    # Limit is 5 for this test
    for _ in range(5):
        assert not ai_service.is_rate_limited(test_user_id, max_per_minute=5)

    # 6th request within 1 minute should be rate limited
    assert ai_service.is_rate_limited(test_user_id, max_per_minute=5)
