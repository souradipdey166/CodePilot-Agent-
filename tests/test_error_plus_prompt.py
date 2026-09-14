from agent.graph import build_graph
from agent.state import DebugState

app = build_graph()

state: DebugState = {
    "repo_path": "quixbugs_data/python_programs",
    "bug_report": "The levenshtein distance function seems to be overcounting edits.",
    "error_output": 'AssertionError: levenshtein("electron", "neutron") returned 8, expected 3',
    "relevant_files": [], "inspected_files": [], "inspected_content": {},
    "hypothesis": "", "patch_old": "", "patch_new": "", "target_file": "",
    "validation_passed": False, "apply_success": False,
    "original_content": "", "diagnosis_wrong": False,
    "test_command": "", "test_output": "", "tests_passed": False,
    "iteration": 0, "max_iterations": 3, "history": []
}

result = app.invoke(state)
print("\n=== FINAL ===")
print("Passed:", result["tests_passed"])