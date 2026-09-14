import json
from datetime import datetime
from pathlib import Path
from agent.graph import build_graph
from agent.state import DebugState
from evaluation.quixbugs_loader import list_bug_names, reset_bug

BUG_REPORTS = {
    "bucketsort": "The bucketsort function is not sorting correctly. Given [3, 1, 2] with k=4, it should return [1, 2, 3].",
    "bitcount": "The bitcount function should count 1-bits in a number's binary representation. bitcount(127) should return 7, bitcount(128) should return 1.",
    "mergesort": "The mergesort function is not working",
    "levenshtein": "",
    "gcd": "The gcd function should return the greatest common divisor of two numbers, but it's returning wrong results for some inputs.",
    "flatten": "The flatten function is supposed to take a nested list and return a single flat list, but it's not fully flattening nested structures.",
    "sqrt": "The sqrt function should compute the square root of a number using Newton's method, but the result is inaccurate.",
    "to_base": "The to_base function should convert a number to a given base and return the digits, but it's producing incorrect output.",
    "next_permutation": "The next_permutation function should return the next lexicographic permutation of a list, but it's returning wrong results.",
    "kth": "The kth function should find the kth smallest element in a list, but it's returning incorrect elements.",
    "powerset": "The powerset function should return all subsets of a list, but it's missing some subsets or including wrong ones.",
    "max_sublist_sum": "The max_sublist_sum function should find the maximum sum of any contiguous sublist, but it's returning wrong values for some inputs."
}

def run_batch(bug_names: list[str], error_reports: dict = None):
    app = build_graph()
    results = []
    error_reports = error_reports or {}

    for bug_name in bug_names:
        print(f"\n{'='*60}\nBUG: {bug_name}\n{'='*60}")
        reset_bug(bug_name)

        state: DebugState = {
            "repo_path": "quixbugs_data/python_programs",
            "bug_report": BUG_REPORTS.get(bug_name, f"The {bug_name} function has a bug."),
            "error_output": error_reports.get(bug_name, ""),
            "relevant_files": [], "inspected_files": [],
            "inspected_content": {},
            "hypothesis": "", "patch_old": "", "patch_new": "", "target_file": "",
            "validation_passed": False, "apply_success": False,
            "original_content": "", "diagnosis_wrong": False,
            "test_command": "", "test_output": "", "tests_passed": False,
            "iteration": 0, "max_iterations": 3, "history": []
        }

        try:
            result = app.invoke(state)
            results.append({
                "bug_name": bug_name,
                "passed": result["tests_passed"],
                "iterations_used": result["iteration"] + 1,
                "first_attempt_success": result["tests_passed"] and result["iteration"] == 0,
                "target_file_found": result.get("target_file", "")
            })
        except Exception as e:
            print(f"CRASHED: {e}")
            results.append({"bug_name": bug_name, "passed": False, "error": str(e)})

        reset_bug(bug_name)

    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    first_attempt = sum(1 for r in results if r.get("first_attempt_success"))

    print(f"\n\n=== EVALUATION SUMMARY ===")
    print(f"Repair rate: {passed}/{total} ({100*passed/total:.1f}%)")
    print(f"First-attempt success: {first_attempt}/{total} ({100*first_attempt/total:.1f}%)")

    Path("evaluation/results").mkdir(parents=True, exist_ok=True)
    out_path = Path("evaluation/results") / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved to {out_path}")

    return results