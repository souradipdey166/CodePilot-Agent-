from agent.graph import build_graph
from agent.state import DebugState

app = build_graph()

state: DebugState = {
    "repo_path": "scratch_general_test",
    "bug_report": "The add function is not adding correctly.",
    "error_output": "",
    "relevant_files": [], "inspected_files": [], "inspected_content": {},
    "hypothesis": "", "patch_old": "", "patch_new": "", "target_file": "",
    "validation_passed": False, "apply_success": False,
    "original_content": "", "diagnosis_wrong": False,
    "test_command": "python -m pytest test_calc.py -v",  # custom, not QuixBugs
    "test_output": "", "tests_passed": False,
    "iteration": 0, "max_iterations": 3, "history": []
}

result = app.invoke(state)
print("\n=== FINAL ===")
print("Passed:", result["tests_passed"])