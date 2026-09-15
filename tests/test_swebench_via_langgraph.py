import sys
sys.path.append("../agent")  # adjust if needed to reach your SWE-bench repo clone

from agent.nodes import (
    initial_test_run, error_analysis, repository_exploration, code_inspection,
    root_cause_hypothesis, patch_generation, patch_validation,
    patch_application, test_execution
)
from agent.state import DebugState

# Point at a repo you already have cloned from tonight's SWE-bench work
state: DebugState = {
    "repo_path": "../agent/workspace/sympy__sympy-11400",  # adjust path to your actual SWE-bench clone
    "bug_report": "",  # intentionally empty — we're starting from the test failure instead
    "test_command": 'pip install -e . --quiet; pip install pytest hypothesis --quiet; python -m pytest sympy/printing/tests/test_ccode.py::test_ccode_sinc -v',
    "error_output": "", "relevant_files": [], "inspected_files": [],
    "hypothesis": "", "patch_old": "", "patch_new": "", "target_file": "",
    "test_output": "", "tests_passed": False,
    "iteration": 0, "max_iterations": 3, "history": []
}

state = initial_test_run(state)
state = error_analysis(state)
state = repository_exploration(state)
state = code_inspection(state)
state = root_cause_hypothesis(state)
state = patch_generation(state)
state = patch_validation(state)
state = patch_application(state)
state = test_execution(state)

print("\n=== FINAL RESULT ===")
print("Tests passed:", state["tests_passed"])