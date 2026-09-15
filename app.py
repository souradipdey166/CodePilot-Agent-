import os
import stat
import subprocess
import tempfile
import shutil
from pathlib import Path
import gradio as gr
from agent.graph import build_graph
from agent.state import DebugState

app_graph = build_graph()

def _remove_readonly(func, path, excinfo):
    """Clear the read-only bit and retry deletion (needed for git's .git folder on Windows)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clone_github_repo(github_url: str) -> str:
    """Clone a GitHub repo into a temp folder, return the local path."""
    repo_name = github_url.rstrip("/").split("/")[-1].replace(".git", "")
    local_path = Path(tempfile.gettempdir()) / repo_name
    if local_path.exists():
        shutil.rmtree(local_path, onerror=_remove_readonly)
    subprocess.run(["git", "clone", "--depth", "1", github_url, str(local_path)], check=True)
    return str(local_path)

def run_agent(github_url, repo_path, bug_report, error_output, test_command):
    actual_repo_path = repo_path.strip()

    if github_url.strip():
        try:
            actual_repo_path = clone_github_repo(github_url.strip())
        except Exception as e:
            return f"❌ Failed to clone repo: {e}", "", "", ""

    if not actual_repo_path:
        return "❌ Please provide either a repo path or a GitHub URL.", "", "", ""

    state: DebugState = {
        "repo_path": actual_repo_path,
        "bug_report": bug_report.strip(),
        "error_output": error_output.strip(),
        "relevant_files": [], "inspected_files": [], "inspected_content": {},
        "hypothesis": "", "patch_old": "", "patch_new": "", "target_file": "",
        "validation_passed": False, "apply_success": False,
        "original_content": "", "diagnosis_wrong": False,
        "test_command": test_command.strip(),
        "test_output": "", "tests_passed": False,
        "iteration": 0, "max_iterations": 3, "history": []
    }

    try:
        result = app_graph.invoke(state)
    except Exception as e:
        return f"❌ Crashed: {e}", "", "", ""

    status = "✅ SUCCESS" if result["tests_passed"] else "❌ FAILED after all attempts"
    trajectory = "\n\n".join(
        f"[{h['step'].upper()}]\n{h.get('output', h)}" for h in result["history"]
    )
    patch_diff = f"FILE: {result['target_file']}\n\nOLD:\n{result['patch_old']}\n\nNEW:\n{result['patch_new']}"
    test_result = result["test_output"][-1500:]

    return status, trajectory, patch_diff, test_result

with gr.Blocks(title="Autonomous Python Repair Agent") as demo:
    gr.Markdown("# 🤖 Autonomous Python Repair Agent")
    gr.Markdown(
        "A LangGraph-based agent that explores a codebase, diagnoses a bug, "
        "generates a patch, validates it, applies it, and verifies the fix "
        "with real (Docker-sandboxed) test execution — retrying with failure "
        "feedback if needed. Benchmarked on QuixBugs (40 real algorithmic bugs). "
        "You can also point it at any public GitHub repo below."
    )

    with gr.Row():
        with gr.Column():
            github_url = gr.Textbox(
                label="GitHub URL (optional — clones automatically, overrides Repo path below)",
                placeholder="https://github.com/username/repo"
            )
            repo_path = gr.Textbox(
                label="Repo path (used if GitHub URL is empty)",
                value="quixbugs_data/python_programs",
                placeholder="e.g. quixbugs_data/python_programs"
            )
            bug_report = gr.Textbox(
                label="Bug report (plain English, optional)",
                placeholder="e.g. The bitcount function returns wrong counts",
                lines=2
            )
            error_output = gr.Textbox(
                label="Error output / traceback (optional)",
                placeholder="Paste a stack trace or assertion error here",
                lines=3
            )
            test_command = gr.Textbox(
                label="Test command (leave blank for QuixBugs default)",
                placeholder="e.g. cd src && pytest test_check.py -v"
            )
            run_btn = gr.Button("Run Agent", variant="primary")

        with gr.Column():
            status = gr.Textbox(label="Result")
            trajectory = gr.Textbox(label="Agent Trajectory", lines=12)
            patch_diff = gr.Textbox(label="Generated Patch", lines=6)
            test_result = gr.Textbox(label="Test Output", lines=8)

    run_btn.click(
        run_agent,
        inputs=[github_url, repo_path, bug_report, error_output, test_command],
        outputs=[status, trajectory, patch_diff, test_result]
    )

    gr.Examples(
        examples=[
            ["", "quixbugs_data/python_programs", "The bitcount function should count 1-bits. bitcount(127) should return 7, bitcount(128) should return 1.", "", ""],
            ["", "quixbugs_data/python_programs", "", 'AssertionError: levenshtein("electron", "neutron") returned 8, expected 3', ""],
        ],
        inputs=[github_url, repo_path, bug_report, error_output, test_command]
    )

if __name__ == "__main__":
    demo.launch(
    server_name="0.0.0.0",
    server_port=7860
)