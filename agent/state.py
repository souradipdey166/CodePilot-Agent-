from typing import TypedDict

class DebugState(TypedDict):
    repo_path: str
    bug_report: str
    error_output: str

    relevant_files: list[str]
    inspected_files: list[str]
    inspected_content: dict[str, str]

    hypothesis: str
    patch_old: str
    patch_new: str
    target_file: str

    validation_passed: bool
    apply_success: bool
    original_content: str
    diagnosis_wrong: bool

    test_command: str
    test_output: str
    tests_passed: bool

    iteration: int
    max_iterations: int
    history: list[dict]