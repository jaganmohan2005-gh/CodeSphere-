"""
CodeSphere - Question Management & Student Practice Tests
---------------------------------------------------------
Validates problem creation, difficulty classification, test case management,
and student practice execution.
"""

from app.models.question import Question, Category, TestCase
from app.extensions import db


def test_admin_create_question(admin_client, app):
    """Verifies that an admin can author a new coding question."""
    with app.app_context():
        cat = Category.query.first()
        cat_id = cat.id

    resp = admin_client.post('/admin/questions/create', data={
        'category_id': cat_id,
        'title': 'Reverse String in Place',
        'difficulty': 'Easy',
        'description': 'Write a function that reverses a string.',
        'constraints': '1 <= s.length <= 10^5',
        'sample_input': 'hello',
        'sample_output': 'olleh',
        'explanation': 'Reversed string order.',
        'time_complexity_expected': 'O(N)',
        'space_complexity_expected': 'O(1)',
        'starter_code_python': 'import sys\nprint(sys.stdin.read().strip()[::-1])',
        'is_published': True
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app.app_context():
        q = Question.query.filter_by(title='Reverse String in Place').first()
        assert q is not None
        assert q.difficulty == 'Easy'
        assert len(q.test_cases) >= 1  # Auto-created sample test case


def test_admin_add_hidden_test_case(admin_client, app):
    """Verifies adding a hidden grading test case to a question."""
    with app.app_context():
        q = Question.query.first()
        q_id = q.id
        initial_cases = len(q.test_cases)

    resp = admin_client.post(f'/admin/questions/{q_id}/test-cases', data={
        'input_data': 'hidden input 999',
        'expected_output': 'hidden output 999',
        'is_hidden': True,
        'points': 20
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app.app_context():
        q = Question.query.get(q_id)
        assert len(q.test_cases) == initial_cases + 1
        new_tc = [tc for tc in q.test_cases if tc.input_data == 'hidden input 999'][0]
        assert new_tc.is_hidden is True
        assert new_tc.points == 20


def test_student_run_sample_tests(auth_client, app):
    """Tests student running their code against public sample cases via AJAX."""
    with app.app_context():
        q = Question.query.filter_by(slug='two-sum-target-indices').first()
        slug = q.slug

    # Valid Python code
    valid_code = """import sys
lines = sys.stdin.read().strip().splitlines()
nums = list(map(int, lines[0].split()))
target = int(lines[1])
seen = {}
for i, n in enumerate(nums):
    diff = target - n
    if diff in seen:
        print(f"{seen[diff]} {i}")
        break
    seen[n] = i
"""

    resp = auth_client.post(f'/practice/{slug}/run-tests', json={
        'code': valid_code,
        'language': 'python'
    })

    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'Accepted'
    assert data['tests_passed'] > 0


def test_student_submit_solution(auth_client, app):
    """Tests student submitting a solution that is graded against all test cases."""
    with app.app_context():
        q = Question.query.filter_by(slug='valid-anagram-string').first()
        slug = q.slug

    correct_code = """import sys
from collections import Counter
lines = sys.stdin.read().strip().splitlines()
s, t = lines[0].strip(), lines[1].strip()
print("true" if Counter(s) == Counter(t) else "false")
"""

    resp = auth_client.post(f'/practice/{slug}/submit', json={
        'code': correct_code,
        'language': 'python'
    })

    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'Accepted'
    assert data['tests_passed'] == data['tests_total']
