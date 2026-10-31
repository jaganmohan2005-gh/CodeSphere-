"""
CodeSphere - Database Seeding Service
-------------------------------------
Populates the database with initial standard curriculum data:
1. Core computer science & interview categories (Arrays, Strings, Trees, DP, SQL, etc.).
2. High-quality coding questions across difficulty tiers with public & hidden test cases.
3. Realistic sample timed assessments for campus placement prep.
4. Default secure administrator account and sample student account for testing.
"""

from datetime import datetime, timedelta
from app.extensions import db
from app.models.user import User, StudentProfile
from app.models.question import Category, Question, TestCase
from app.models.assessment import Assessment, AssessmentQuestion
from app.models.notification import Notification


def seed_database(admin_username='admin', admin_email='admin@codesphere.io', admin_password='Admin@CodeSphere2026!'):
    """
    Seeds comprehensive initial records into the active database.
    Safe to run repeatedly; checks for existing records before inserting.
    """

    # 1. Seed Categories
    category_definitions = [
        {"name": "Arrays", "slug": "arrays", "description": "Contiguous memory structures, prefix sums, sliding window, and two-pointer techniques.", "icon": "bi-grid-3x3"},
        {"name": "Strings", "slug": "strings", "description": "Character manipulation, pattern matching, anagrams, and palindromes.", "icon": "bi-fonts"},
        {"name": "Searching", "slug": "searching", "description": "Linear search, binary search, and search space reduction algorithms.", "icon": "bi-search"},
        {"name": "Sorting", "slug": "sorting", "description": "Quicksort, mergesort, heapsort, counting sort, and stability analysis.", "icon": "bi-arrow-down-up"},
        {"name": "Recursion", "slug": "recursion", "description": "Base conditions, recurrence relations, and backtracking.", "icon": "bi-arrow-repeat"},
        {"name": "Linked Lists", "slug": "linked-lists", "description": "Singly and doubly linked lists, pointer manipulation, and cycle detection.", "icon": "bi-link-45deg"},
        {"name": "Stacks", "slug": "stacks", "description": "LIFO processing, bracket matching, and monotonic stacks.", "icon": "bi-layers"},
        {"name": "Queues", "slug": "queues", "description": "FIFO structures, circular queues, and double-ended queues (deque).", "icon": "bi-distribute-horizontal"},
        {"name": "Trees", "slug": "trees", "description": "Binary trees, BSTs, DFS/BFS traversals, and lowest common ancestor.", "icon": "bi-diagram-3"},
        {"name": "Graphs", "slug": "graphs", "description": "Adjacency lists, BFS, DFS, Dijkstra's algorithm, and topological sort.", "icon": "bi-share"},
        {"name": "Greedy Algorithms", "slug": "greedy-algorithms", "description": "Locally optimal choice strategies, activity selection, and Huffman coding.", "icon": "bi-lightning-charge"},
        {"name": "Dynamic Programming", "slug": "dynamic-programming", "description": "Memoization, tabulation, optimal substructure, and knapsack variations.", "icon": "bi-cpu"},
        {"name": "Object-Oriented Programming", "slug": "oop", "description": "Encapsulation, inheritance, polymorphism, and SOLID principles.", "icon": "bi-boxes"},
        {"name": "DBMS", "slug": "dbms", "description": "Relational models, ACID properties, normalization, indexing, and transactions.", "icon": "bi-database"},
        {"name": "SQL", "slug": "sql", "description": "Queries, JOINs, aggregate grouping, subqueries, and window functions.", "icon": "bi-table"},
        {"name": "Operating Systems", "slug": "operating-systems", "description": "Processes, threads, CPU scheduling, synchronization, and virtual memory.", "icon": "bi-motherboard"},
        {"name": "Computer Networks", "slug": "computer-networks", "description": "OSI 7-layer model, TCP/IP, DNS, HTTP/HTTPS, routing, and sockets.", "icon": "bi-hdd-network"},
    ]

    cat_map = {}
    for item in category_definitions:
        cat = Category.query.filter_by(slug=item['slug']).first()
        if not cat:
            cat = Category(
                name=item['name'],
                slug=item['slug'],
                description=item['description'],
                icon=item['icon']
            )
            db.session.add(cat)
            db.session.flush()
        cat_map[cat.slug] = cat

    # 2. Seed Default Admin User
    admin = User.query.filter_by(username=admin_username).first()
    if not admin:
        admin = User(
            username=admin_username,
            email=admin_email,
            role='admin',
            is_active_account=True
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.flush()

        # Admin Profile
        admin_profile = StudentProfile(
            user_id=admin.id,
            full_name="Lead System Administrator",
            college="CodeSphere Engineering",
            degree="M.Tech Computer Science",
            target_role="Platform Administrator",
            bio="Administrator of CodeSphere intelligent assessment and prep ecosystem."
        )
        db.session.add(admin_profile)

    # 3. Seed Sample Student User
    demo_student = User.query.filter_by(username='student').first()
    if not demo_student:
        demo_student = User(
            username='student',
            email='student@codesphere.io',
            role='student',
            is_active_account=True
        )
        demo_student.set_password('Student@CodeSphere2026!')
        db.session.add(demo_student)
        db.session.flush()

        student_profile = StudentProfile(
            user_id=demo_student.id,
            full_name="Aarav Sharma",
            college="National Institute of Technology",
            degree="B.Tech Computer Science & Engineering",
            graduation_year=2026,
            target_role="Full Stack Software Engineer",
            preferred_language="python",
            bio="Passionate aspiring software engineer preparing for product placement rounds."
        )
        db.session.add(student_profile)

        # Welcome notification
        notif = Notification(
            user_id=demo_student.id,
            title="Welcome to CodeSphere!",
            message="Your intelligent placement prep journey starts here. Explore practice problems or take a timed assessment.",
            type="info"
        )
        db.session.add(notif)

    # 4. Seed High-Quality Coding Questions with Test Cases
    sample_questions = [
        {
            "category_slug": "arrays",
            "title": "Two Sum Target Indices",
            "slug": "two-sum-target-indices",
            "difficulty": "Easy",
            "description": "Given an array of integers `nums` and an integer `target`, return the indices of the two numbers such that they add up to `target`.\n\nYou may assume that each input has exactly one solution, and you may not use the same element twice. Return the indices separated by a space.",
            "constraints": "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\n-10^9 <= target <= 10^9",
            "sample_input": "2 7 11 15\n9",
            "sample_output": "0 1",
            "explanation": "Because nums[0] + nums[1] == 2 + 7 == 9, we return 0 1.",
            "time_complexity_expected": "O(N)",
            "space_complexity_expected": "O(N)",
            "starter_code_python": """# Two Sum Target Indices
import sys

def solve():
    lines = sys.stdin.read().strip().splitlines()
    if not lines:
        return
    nums = list(map(int, lines[0].split()))
    target = int(lines[1])
    
    # Write your solution using a Hash Map for O(N) time
    lookup = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in lookup:
            print(f"{lookup[diff]} {i}")
            return
        lookup[num] = i

if __name__ == '__main__':
    solve()
""",
            "test_cases": [
                {"input": "2 7 11 15\n9", "output": "0 1", "hidden": False, "points": 10},
                {"input": "3 2 4\n6", "output": "1 2", "hidden": False, "points": 10},
                {"input": "3 3\n6", "output": "0 1", "hidden": True, "points": 10},
                {"input": "-1 -2 -3 -4 -5\n-8", "output": "2 4", "hidden": True, "points": 10},
            ]
        },
        {
            "category_slug": "strings",
            "title": "Valid Anagram String",
            "slug": "valid-anagram-string",
            "difficulty": "Easy",
            "description": "Given two strings `s` and `t`, return `true` if `t` is an anagram of `s`, and `false` otherwise.\n\nAn Anagram is a word or phrase formed by rearranging the letters of a different word or phrase, typically using all the original letters exactly once.",
            "constraints": "1 <= s.length, t.length <= 5 * 10^4\ns and t consist of lowercase English letters.",
            "sample_input": "anagram\nnagaram",
            "sample_output": "true",
            "explanation": "Both strings contain the exact same character frequencies ('a':3, 'g':1, 'm':1, 'n':1, 'r':1).",
            "time_complexity_expected": "O(N)",
            "space_complexity_expected": "O(1) (26 characters)",
            "starter_code_python": """# Valid Anagram
import sys
from collections import Counter

def solve():
    lines = sys.stdin.read().strip().splitlines()
    if len(lines) < 2:
        return
    s, t = lines[0].strip(), lines[1].strip()
    
    # Check anagram condition
    if Counter(s) == Counter(t):
        print("true")
    else:
        print("false")

if __name__ == '__main__':
    solve()
""",
            "test_cases": [
                {"input": "anagram\nnagaram", "output": "true", "hidden": False, "points": 10},
                {"input": "rat\ncar", "output": "false", "hidden": False, "points": 10},
                {"input": "listen\nsilent", "output": "true", "hidden": True, "points": 10},
                {"input": "a\nab", "output": "false", "hidden": True, "points": 10},
            ]
        },
        {
            "category_slug": "arrays",
            "title": "Maximum Subarray Kadane",
            "slug": "maximum-subarray-kadane",
            "difficulty": "Medium",
            "description": "Given an integer array `nums`, find the subarray with the largest sum, and return its sum.\n\nA subarray is a contiguous non-empty sequence of elements within an array.",
            "constraints": "1 <= nums.length <= 10^5\n-10^4 <= nums[i] <= 10^4",
            "sample_input": "-2 1 -3 4 -1 2 1 -5 4",
            "sample_output": "6",
            "explanation": "The subarray [4, -1, 2, 1] has the largest sum 6.",
            "time_complexity_expected": "O(N)",
            "space_complexity_expected": "O(1)",
            "starter_code_python": """# Maximum Subarray using Kadane's Algorithm
import sys

def solve():
    raw = sys.stdin.read().strip()
    if not raw:
        return
    nums = list(map(int, raw.split()))
    
    # Kadane's algorithm
    max_so_far = nums[0]
    current_max = nums[0]
    for x in nums[1:]:
        current_max = max(x, current_max + x)
        max_so_far = max(max_so_far, current_max)
    print(max_so_far)

if __name__ == '__main__':
    solve()
""",
            "test_cases": [
                {"input": "-2 1 -3 4 -1 2 1 -5 4", "output": "6", "hidden": False, "points": 15},
                {"input": "1", "output": "1", "hidden": False, "points": 10},
                {"input": "5 4 -1 7 8", "output": "23", "hidden": True, "points": 15},
                {"input": "-5 -4 -1 -7 -8", "output": "-1", "hidden": True, "points": 15},
            ]
        },
        {
            "category_slug": "dynamic-programming",
            "title": "Climbing Stairs Ways",
            "slug": "climbing-stairs-ways",
            "difficulty": "Easy",
            "description": "You are climbing a staircase. It takes `n` steps to reach the top.\n\nEach time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?",
            "constraints": "1 <= n <= 45",
            "sample_input": "3",
            "sample_output": "3",
            "explanation": "There are three ways: 1+1+1, 1+2, 2+1.",
            "time_complexity_expected": "O(N)",
            "space_complexity_expected": "O(1)",
            "starter_code_python": """# Climbing Stairs (Fibonacci DP)
import sys

def solve():
    raw = sys.stdin.read().strip()
    if not raw:
        return
    n = int(raw)
    if n <= 2:
        print(n)
        return
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    print(b)

if __name__ == '__main__':
    solve()
""",
            "test_cases": [
                {"input": "2", "output": "2", "hidden": False, "points": 10},
                {"input": "3", "output": "3", "hidden": False, "points": 10},
                {"input": "5", "output": "8", "hidden": True, "points": 10},
                {"input": "10", "output": "89", "hidden": True, "points": 10},
            ]
        },
        {
            "category_slug": "stacks",
            "title": "Valid Parentheses Checker",
            "slug": "valid-parentheses-checker",
            "difficulty": "Easy",
            "description": "Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.\n\nAn input string is valid if open brackets are closed by the same type of brackets in the correct order.",
            "constraints": "1 <= s.length <= 10^4\ns consists of parentheses only '()[]{}'.",
            "sample_input": "()[]{}",
            "sample_output": "true",
            "explanation": "All bracket pairs are appropriately closed in correct order.",
            "time_complexity_expected": "O(N)",
            "space_complexity_expected": "O(N)",
            "starter_code_python": """# Valid Parentheses using Stack
import sys

def solve():
    s = sys.stdin.read().strip()
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    
    for char in s:
        if char in mapping:
            top = stack.pop() if stack else '#'
            if mapping[char] != top:
                print("false")
                return
        else:
            stack.append(char)
            
    print("true" if not stack else "false")

if __name__ == '__main__':
    solve()
""",
            "test_cases": [
                {"input": "()[]{}", "output": "true", "hidden": False, "points": 10},
                {"input": "(]", "output": "false", "hidden": False, "points": 10},
                {"input": "([{}])", "output": "true", "hidden": True, "points": 10},
                {"input": "(((((", "output": "false", "hidden": True, "points": 10},
            ]
        }
    ]

    created_questions = []
    for q_data in sample_questions:
        q = Question.query.filter_by(slug=q_data['slug']).first()
        cat = cat_map.get(q_data['category_slug'])
        if not cat:
            continue

        if not q:
            q = Question(
                category_id=cat.id,
                title=q_data['title'],
                slug=q_data['slug'],
                difficulty=q_data['difficulty'],
                description=q_data['description'],
                constraints=q_data['constraints'],
                sample_input=q_data['sample_input'],
                sample_output=q_data['sample_output'],
                explanation=q_data['explanation'],
                time_complexity_expected=q_data['time_complexity_expected'],
                space_complexity_expected=q_data['space_complexity_expected'],
                starter_code_python=q_data['starter_code_python'],
                is_published=True
            )
            db.session.add(q)
            db.session.flush()

            # Seed Test Cases
            for tc_data in q_data['test_cases']:
                tc = TestCase(
                    question_id=q.id,
                    input_data=tc_data['input'],
                    expected_output=tc_data['output'],
                    is_hidden=tc_data['hidden'],
                    points=tc_data['points']
                )
                db.session.add(tc)

        created_questions.append(q)

    # 5. Seed Sample Assessment
    assessment = Assessment.query.filter_by(title="Campus Placement Diagnostic Assessment 2026").first()
    if not assessment and created_questions:
        assessment = Assessment(
            title="Campus Placement Diagnostic Assessment 2026",
            description="Comprehensive initial screening assessment covering Arrays, Strings, Stacks, and Dynamic Programming. Standard placement round simulation.",
            difficulty="Medium",
            duration_minutes=60,
            is_published=True,
            pass_percentage=50.0,
            results_released_immediately=True,
            retake_allowed=True,
            created_by_user_id=admin.id
        )
        db.session.add(assessment)
        db.session.flush()

        for idx, q in enumerate(created_questions[:4], 1):
            aq = AssessmentQuestion(
                assessment_id=assessment.id,
                question_id=q.id,
                order_index=idx,
                marks=25
            )
            db.session.add(aq)

        # Notify student about assessment
        if demo_student:
            notif = Notification(
                user_id=demo_student.id,
                title="New Assessment Available",
                message=f"'{assessment.title}' is now live. Complete it within {assessment.duration_minutes} minutes.",
                type="assessment",
                link=f"/assessments/{assessment.id}"
            )
            db.session.add(notif)

    db.session.commit()
    return True
