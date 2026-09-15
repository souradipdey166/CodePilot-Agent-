from pathlib import Path

QUIXBUGS_ROOT = Path("quixbugs_data")
PROGRAMS_DIR = QUIXBUGS_ROOT / "python_programs"
TESTCASES_DIR = QUIXBUGS_ROOT / "python_testcases"

def list_bug_names() -> list[str]:
    """List all buggy program names (without .py), excluding bundled test files."""
    names = []
    for f in PROGRAMS_DIR.glob("*.py"):
        if f.stem.endswith("_test"):
            continue
        # Only include if a matching real test exists in python_testcases/
        test_file = TESTCASES_DIR / f"test_{f.stem}.py"
        if test_file.exists():
            names.append(f.stem)
    return sorted(names)

def get_bug_file_path(bug_name: str) -> Path:
    """Path to the buggy program file the agent will read/edit."""
    return PROGRAMS_DIR / f"{bug_name}.py"

def get_test_file_path(bug_name: str) -> Path:
    """Path to the real test file used to verify the fix."""
    return TESTCASES_DIR / f"test_{bug_name}.py"

def get_bug_source(bug_name: str) -> str:
    """Read the current (buggy or fixed) source code."""
    return get_bug_file_path(bug_name).read_text(encoding="utf-8")


import subprocess

def reset_bug(bug_name: str):
    """Restore a bug's source file to its original (buggy) state using git."""
    relative_path = f"python_programs/{bug_name}.py"
    subprocess.run(["git", "checkout", "--", relative_path], cwd=QUIXBUGS_ROOT, check=True)