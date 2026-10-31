"""
CodeSphere - Code Execution Sandboxing Tests
--------------------------------------------
Validates subprocess isolation, security compliance scanning (blocking os, subprocess, sockets),
time limit enforcement (infinite loop termination), and test case evaluation.
"""

from app.services.code_executor import code_executor
from app.models.question import TestCase


def test_code_executor_basic_execution():
    """Verifies that benign algorithmic code executes and prints expected output."""
    code = """import sys
lines = sys.stdin.read().strip().splitlines()
nums = list(map(int, lines[0].split()))
print(sum(nums))
"""
    stdout, stderr, exec_time, tle, err = code_executor.execute_python_code(code, "10 20 30")
    assert stdout.strip() == "60"
    assert not err
    assert not tle
    assert exec_time >= 0


def test_code_executor_blocks_malicious_system_calls():
    """Verifies that security checks block os, subprocess, and socket imports."""
    malicious_scripts = [
        "import os\nos.system('dir')",
        "from os import path",
        "import subprocess\nsubprocess.run(['ls'])",
        "import socket\ns = socket.socket()",
        "__import__('os').system('echo hack')",
    ]

    for script in malicious_scripts:
        is_safe, error = code_executor.check_security_compliance(script)
        assert not is_safe
        assert "Security Violation" in error

        # Execution should be immediately halted
        stdout, stderr, exec_time, tle, err = code_executor.execute_python_code(script, "")
        assert err is True
        assert "Security Violation" in stderr


def test_code_executor_time_limit_exceeded():
    """Verifies that infinite loops are halted cleanly by the subprocess timeout."""
    infinite_loop_code = """
import time
while True:
    time.sleep(0.1)
"""
    # Use a small timeout for rapid test
    custom_executor = code_executor.__class__(timeout_seconds=1)
    stdout, stderr, exec_time, tle, err = custom_executor.execute_python_code(infinite_loop_code, "")
    assert tle is True
    assert "Time Limit Exceeded" in stderr


def test_code_executor_evaluates_test_cases():
    """Verifies end-to-end evaluation against sample TestCase models."""
    tc1 = TestCase(id=1, question_id=1, input_data="hello", expected_output="HELLO", is_hidden=False, points=10)
    tc2 = TestCase(id=2, question_id=1, input_data="world", expected_output="WORLD", is_hidden=True, points=10)

    solution_code = """import sys
print(sys.stdin.read().strip().upper())
"""

    result = code_executor.evaluate_submission(solution_code, 'python', [tc1, tc2])
    assert result.status == 'Accepted'
    assert result.tests_passed == 2
    assert result.tests_total == 2
