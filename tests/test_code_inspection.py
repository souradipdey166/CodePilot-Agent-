from agent.nodes import error_analysis, repository_exploration, code_inspection
from agent.state import DebugState

state: DebugState = {
    "repo_path": "quixbugs_data/python_programs",
    "bug_report": "The bucketsort function is not sorting correctly. Given [3, 1, 2] with k=4, it should return [1, 2, 3] but returns something wrong.",
    "error_output": "", "relevant_files": [], "inspected_files": [],
    "hypothesis": "", "patch_old": "", "patch_new": "", "target_file": "",
    "test_command": "", "test_output": "", "tests_passed": False,
    "iteration": 0, "max_iterations": 3, "history": []
}

state = error_analysis(state)
state = repository_exploration(state)
state = code_inspection(state)

print("\nInspected files:", state["inspected_files"])
print("\nContent of bucketsort.py:")
print(state["_inspected_content"]["bucketsort.py"])