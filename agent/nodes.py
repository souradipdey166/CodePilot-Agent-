from agent.state import DebugState
from patch_generator import call_llm
from tools.file_tools import list_files
from tools.search_tools import search_text
from tools.file_tools import read_file
from tools.patch_tools import apply_patch
import subprocess
from pathlib import Path


def error_analysis(state: DebugState) -> DebugState:
    """Turn the raw bug report/error into a concrete search plan."""
    prompt = f"""You are debugging a Python program.

BUG REPORT:
{state.get('bug_report', 'None provided')}

ERROR OUTPUT (if any):
{state.get('error_output', 'None provided')}

Based on this, list:
1. What symptoms suggest is wrong (in plain terms)
2. What function names, keywords, or behaviors to search for in the codebase

Keep this brief — a few sentences, not a full analysis."""

    analysis = call_llm(prompt)
    print(f"\n[ERROR ANALYSIS]\n{analysis}\n")

    state["history"] = state.get("history", []) + [{"step": "error_analysis", "output": analysis}]
    state["hypothesis"] = analysis  # placeholder until root_cause_hypothesis refines it further
    return state



def repository_exploration(state: DebugState) -> DebugState:
    """Search the repo using clues from the error analysis to find candidate files."""
    repo_path = state["repo_path"]

    all_files = list_files(repo_path)
    print(f"\n[EXPLORE] Repo has {len(all_files)} files")

    # Ask the LLM to pick 2-3 concrete search terms from its own earlier analysis
    prompt = f"""Based on this analysis:
{state['hypothesis']}

List ONLY 2-3 short, concrete search keywords (function names or key terms) 
to grep for in the codebase. One per line, no explanation, no numbering."""

    keywords_raw = call_llm(prompt)
    keywords = [k.strip("- ").strip() for k in keywords_raw.splitlines() if k.strip()]
    print(f"[EXPLORE] Searching for keywords: {keywords}")

    candidate_files = set()
    for kw in keywords[:3]:
        matches = search_text(repo_path, kw)
        for m in matches:
            candidate_files.add(m["file"])

    # Fallback: if search found nothing, just consider all files (small QuixBugs programs are cheap to scan)
    if not candidate_files:
        candidate_files = set(all_files)

    print(f"[EXPLORE] Candidate files: {candidate_files}")

    state["relevant_files"] = list(candidate_files)
    state["history"] = state.get("history", []) + [{"step": "repository_exploration", "candidates": list(candidate_files)}]
    return state


def code_inspection(state: DebugState) -> DebugState:
    """Read the contents of candidate files found during exploration."""
    repo_path = state["repo_path"]
    candidates = state["relevant_files"]

    inspected = {}
    #for filename in candidates:
    for filename in candidates[:5]:  # cap at 3 files to avoid context bloat
        try:
            content = read_file(repo_path, filename)
            inspected[filename] = content
        except Exception as e:
            print(f"[INSPECT] Could not read {filename}: {e}")

    print(f"\n[INSPECT] Read {len(inspected)} file(s): {list(inspected.keys())}")

    state["inspected_files"] = list(inspected.keys())
    state["history"] = state.get("history", []) + [{"step": "code_inspection", "files_read": list(inspected.keys())}]
    # Store the actual content in state so root_cause_hypothesis can use it
    state["inspected_content"] = inspected  # underscore prefix = internal, not in original TypedDict
    return state

def root_cause_hypothesis(state: DebugState) -> DebugState:
    """Reason over inspected code and identify the exact buggy file and root cause."""

    inspected = state.get("inspected_content", {})
    repo_path = Path(state["repo_path"]).resolve()

    MAX_FILE_CHARS = 12000 # added new

    code_blocks = "\n\n".join(
        f"FILE: {name}\n{content[:MAX_FILE_CHARS]}" # added new
        for name, content in inspected.items()
    )

    # On retry, give the LLM the latest test evidence.
    retry_context = ""

    if state.get("iteration", 0) > 0:
        retry_context = f"""
LATEST TEST OUTPUT:
{state.get('test_output', 'No test output available.')}

PREVIOUS FAILURE ANALYSIS:
{state.get('failure_analysis', 'No failure analysis available.')}

This is a RETRY.
Prioritize the latest test failure over the original bug report.
Do not re-diagnose an already fixed problem unless the new evidence
shows that it is still the cause.
"""

    prompt = f"""You are debugging a Python program.

ORIGINAL BUG REPORT:
{state['bug_report']}

{retry_context}

INSPECTED CODE:
{code_blocks}

Identify the exact file containing the bug.

Return EXACTLY this format:

TARGET_FILE:
<exact filename copied from the FILE names above>

ROOT_CAUSE:
<what is wrong and why>

IMPORTANT:
- TARGET_FILE must refer to one of the files shown above.
- Copy the filename exactly from the FILE labels.
- Do not invent a filename.
- Focus on the actual code and test evidence.
"""

    response = call_llm(prompt)

    print(f"\n[ROOT CAUSE]\n{response}\n")

    target_file = ""
    hypothesis = response

    # ---------------------------------------------------------
    # Parse LLM response
    # ---------------------------------------------------------
    if "TARGET_FILE:" in response and "ROOT_CAUSE:" in response:

        target_file = (
            response.split("TARGET_FILE:", 1)[1]
            .split("ROOT_CAUSE:", 1)[0]
            .strip()
            .strip("`")
        )

        hypothesis = response.split("ROOT_CAUSE:", 1)[1].strip()

    # ---------------------------------------------------------
    # Normalize the filename
    # ---------------------------------------------------------
    normalized_target = None

    target_normalized = target_file.replace("\\", "/").strip()

    for inspected_file in inspected:

        inspected_path = Path(inspected_file).resolve()

        try:
            relative_path = inspected_path.relative_to(repo_path).as_posix()
        except ValueError:
            relative_path = ""

        absolute_path = inspected_path.as_posix()
        filename_only = inspected_path.name

        possible_names = {
            absolute_path,
            relative_path,
            filename_only
        }

        if target_normalized in possible_names:
            normalized_target = inspected_file
            break

    # ---------------------------------------------------------
    # Safety check
    # ---------------------------------------------------------
    if normalized_target is None:

        print(
            f"[ROOT CAUSE] Invalid target file: {target_file}"
        )

        target_file = ""

    else:

        # Use the exact key from inspected_content
        target_file = normalized_target

        print(
            f"[ROOT CAUSE] Target file normalized to: {target_file}"
        )

    # ---------------------------------------------------------
    # Update state
    # ---------------------------------------------------------
    state["target_file"] = target_file
    state["hypothesis"] = hypothesis

    state["history"] = state.get("history", []) + [{
        "step": "root_cause_hypothesis",
        "target_file": target_file,
        "output": hypothesis
    }]

    return state


def _strip_code_fence(text: str) -> str:
    """Remove markdown code fences and language hints if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]  # drop opening ```python or ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # drop closing ```
        text = "\n".join(lines)
    return text.strip()


def patch_generation(state: DebugState) -> DebugState:
    """Generate a targeted old->new code snippet based on the hypothesis."""
    inspected = state.get("inspected_content", {})
    target_file = state["target_file"]
    current_code = inspected.get(target_file, "")

    prompt = f"""Based on this diagnosis:
{state['hypothesis']}

CURRENT CODE in {target_file}:
{current_code}

Output a targeted patch as EXACTLY two blocks, nothing else:

OLD:
<the exact original lines to replace, copied verbatim from the code above>

NEW:
<the corrected replacement lines>

Keep OLD as short and specific as possible — just the buggy line(s), not the whole function."""

    response = call_llm(prompt)
    print(f"\n[PATCH GENERATION]\n{response}\n")

    old_code, new_code = "", ""
    if "OLD:" in response and "NEW:" in response:
        old_part = response.split("OLD:")[1].split("NEW:")[0].strip()
        new_part = response.split("NEW:")[1].strip()
        old_code = _strip_code_fence(old_part)
        new_code = _strip_code_fence(new_part)

    state["patch_old"] = old_code
    state["patch_new"] = new_code
    state["history"] = state.get("history", []) + [{"step": "patch_generation", "old": old_code, "new": new_code}]
    return state



def patch_validation(state: DebugState) -> DebugState:
    """Verify the patch's OLD snippet actually exists, uniquely, before applying."""
    repo_path = state["repo_path"]
    target_file = state["target_file"]
    old_code = state["patch_old"]

    current_content = read_file(repo_path, target_file)
    occurrences = current_content.count(old_code)

    if occurrences == 0:
        print(f"\n[VALIDATE] FAILED: OLD snippet not found in {target_file} (exact match failed)")
        state["validation_passed"] = False
    elif occurrences > 1:
        print(f"\n[VALIDATE] FAILED: OLD snippet found {occurrences} times (ambiguous)")
        state["validation_passed"] = False
    else:
        print(f"\n[VALIDATE] OK: OLD snippet found exactly once in {target_file}")
        state["validation_passed"] = True

    state["history"] = state.get("history", []) + [{"step": "patch_validation", "passed": state["validation_passed"]}]
    return state



def patch_application(state: DebugState) -> DebugState:
    """Apply the validated patch, storing original content for rollback."""
    if not state.get("validation_passed", False):
        print("\n[APPLY] Skipped — validation did not pass")
        state["apply_success"] = False
        return state

    repo_path = state["repo_path"]
    target_file = state["target_file"]

    # Store original content for rollback before touching the file
    full_path = Path(repo_path) / target_file
    original_content = full_path.read_text(encoding="utf-8")
    state["original_content"] = original_content

    success = apply_patch(repo_path, target_file, state["patch_old"], state["patch_new"])
    print(f"\n[APPLY] Patch applied: {success}")

    state["modified_files"] = [target_file] if success else []
    state["apply_success"] = success
    state["history"] = state.get("history", []) + [{"step": "patch_application", "success": success}]
    return state

import subprocess
import os

DOCKER_IMAGE = "code-agent-sandbox"

def test_execution(state: DebugState) -> DebugState:
    """Run the configured test command, inside Docker locally, or directly when deployed on HuggingFace Spaces."""
    repo_path = Path(state["repo_path"]).resolve()
    test_command = state.get("test_command", "").strip()
    use_docker = os.getenv("SPACE_ID") is None  # False when running on HF Spaces

    if not test_command:
        quixbugs_root = repo_path.parent
        bug_name = Path(state["target_file"]).stem
        test_command = f"python -m pytest python_testcases/test_{bug_name}.py -v --rootdir=/workspace"
        mount_root = quixbugs_root
    else:
        mount_root = repo_path

    try:
        if use_docker:
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{mount_root}:/workspace",
                "-w", "/workspace",
                DOCKER_IMAGE,
                "bash", "-c", test_command
            ]
        else:
            cmd = ["bash", "-c", f"cd {mount_root} && {test_command}"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        passed = result.returncode == 0
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        passed = False
        output = "Timed out"

    print(f"\n[TEST] Passed: {passed}")
    print(output[-1000:])

    state["test_output"] = output
    state["tests_passed"] = passed
    state["history"] = state.get("history", []) + [{"step": "test_execution", "passed": passed}]
    return state
'''
DOCKER_IMAGE = "code-agent-sandbox"

def test_execution(state: DebugState) -> DebugState:
    """Run the configured test command, inside Docker."""
    repo_path = Path(state["repo_path"]).resolve()
    test_command = state.get("test_command", "").strip()

    if not test_command:
        # Fallback to QuixBugs-style default if nothing was specified
        quixbugs_root = repo_path.parent
        bug_name = Path(state["target_file"]).stem
        test_command = f"python -m pytest python_testcases/test_{bug_name}.py -v --rootdir=/workspace"
        mount_root = quixbugs_root
    else:
        mount_root = repo_path

    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{mount_root}:/workspace",
                "-w", "/workspace",
                DOCKER_IMAGE,
                "bash", "-c", test_command
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        passed = result.returncode == 0
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        passed = False
        output = "Timed out"

    print(f"\n[TEST] Passed: {passed}")
    print(output[-1000:])

    state["test_output"] = output
    state["tests_passed"] = passed
    state["history"] = state.get("history", []) + [{"step": "test_execution", "passed": passed}]
    return state
'''
def failure_analysis(state: DebugState) -> DebugState:
    """Reconcile: was the diagnosis wrong, or just the patch?"""
    prompt = f"""Your previous hypothesis was:
{state['hypothesis']}

You patched:
OLD: {state['patch_old']}
NEW: {state['patch_new']}

But the test still failed with:
{state['test_output'][-800:]}

Was your ORIGINAL DIAGNOSIS wrong (wrong file/wrong root cause), or was the 
diagnosis right but the PATCH implementation wrong? State which, and why, briefly."""

    analysis = call_llm(prompt)
    print(f"\n[FAILURE ANALYSIS]\n{analysis}\n")

    diagnosis_wrong = "diagnosis" in analysis.lower()[:200]  # crude heuristic, improve later

    state["diagnosis_wrong"] = diagnosis_wrong
    state["history"] = state.get("history", []) + [{"step": "failure_analysis", "output": analysis}]
    return state


def iteration_check(state: DebugState) -> DebugState:
    """Increment iteration count, decide whether to stop."""
    state["iteration"] = state.get("iteration", 0) + 1
    print(f"\n[ITERATION CHECK] Now at iteration {state['iteration']}/{state['max_iterations']}")
    return state


