from agent.pipeline import run_pipeline
from agent.state import DebugState

state: DebugState = {
    "repo_path": "quixbugs_data/python_programs",
    "bug_report": "The mergesort function is not working",
    "error_output": "", "relevant_files": [], "inspected_files": [],
    "hypothesis": "", "patch_old": "", "patch_new": "", "target_file": "",
    "test_command": "", "test_output": "", "tests_passed": False,
    "iteration": 0, "max_iterations": 3, "history": []
}

final_state = run_pipeline(state)

print("\n\n=== FINAL RESULT ===")
print("Tests passed:", final_state["tests_passed"])
print("Iterations used:", final_state["iteration"])
