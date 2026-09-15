from agent.graph import build_graph
from agent.state import DebugState

app = build_graph()

state: DebugState = {
    "repo_path": "quixbugs_data/python_programs",
    "bug_report": "The bitcount function should count 1-bits in a number's binary representation. bitcount(127) should return 7, bitcount(128) should return 1.",
    "error_output": "", "relevant_files": [], "inspected_files": [],
    "inspected_content": {},
    "hypothesis": "", "patch_old": "", "patch_new": "", "target_file": "",
    "validation_passed": False, "apply_success": False,
    "original_content": "", "diagnosis_wrong": False,
    "test_command": "", "test_output": "", "tests_passed": False,
    "iteration": 0, "max_iterations": 3, "history": []
}

result = app.invoke(state)
print("\n=== FINAL ===")
print("Passed:", result["tests_passed"])