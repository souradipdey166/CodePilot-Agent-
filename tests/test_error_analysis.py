from agent.nodes import error_analysis
from agent.state import DebugState

state: DebugState = {
    "repo_path": "quixbugs_data/python_programs",
    "bug_report": "The bucketsort function is not sorting correctly. Given [3, 1, 2] with k=4, it should return [1, 2, 3] but returns something wrong.",
    "error_output": "",
    "relevant_files": [],
    "inspected_files": [],
    "hypothesis": "",
    "patch_old": "",
    "patch_new": "",
    "target_file": "",
    "test_command": "",
    "test_output": "",
    "tests_passed": False,
    "iteration": 0,
    "max_iterations": 3,
    "history": []
}

result = error_analysis(state)
print("Updated state hypothesis field:")
print(result["hypothesis"])