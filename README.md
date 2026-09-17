# CodePilot Agent

CodePilot Agent is an autonomous Python code-repair system built around a LangGraph `StateGraph`. It takes a bug report, an error message, or both; explores a repository; inspects candidate files; diagnoses a root cause; generates a targeted patch; validates the patch; applies it; runs tests; and, when tests still fail, analyzes the failure and retries.

**Live demo:** https://codepilot-agent.onrender.com/

Built with **LangGraph, LangChain, Groq, Gradio, pytest, Python, and optional Docker-based test execution**.

The benchmark included in this repository uses a selected set of **12 Python programs from QuixBugs**.

---

## How it works

```text
Bug report / error output / both
              |
              v
       Error Analysis
       Turn the problem signal into search clues
              |
              v
   Repository Exploration
   List files and search for relevant keywords
              |
              v
      Code Inspection
      Read the candidate source files
              |
              v
   Root Cause Hypothesis
   Identify the target file and explain the defect
              |
              v
     Patch Generation
     Produce an exact OLD -> NEW code replacement
              |
              v
     Patch Validation
     Require the OLD snippet to exist exactly once
              |
              v
     Patch Application
     Apply the validated replacement
              |
              v
      Test Execution
      Run the configured test command
              |
        +-----+-----+
        |           |
       PASS        FAIL
        |           |
        v           v
     SUCCESS   Failure Analysis
                    |
                    v
              Iteration Check
                    |
                    v
                  RETRY
```

The graph contains these ten nodes:

1. `error_analysis`
2. `repository_exploration`
3. `code_inspection`
4. `root_cause_hypothesis`
5. `patch_generation`
6. `patch_validation`
7. `patch_application`
8. `test_execution`
9. `failure_analysis`
10. `iteration_check`

`DebugState` is the shared `TypedDict` passed through the graph.

---

## Latest recorded benchmark result

The latest evaluation artifact included in this repository is:

`evaluation/results/batch_20260916_191608.json`

It contains the following results:

| Metric | Result |
|---|---:|
| **Repair rate** | **12 / 12 (100%)** |
| **First-attempt success** | **11 / 12 (91.7%)** |
| Requiring retries | 1 (`max_sublist_sum`) |
| Failed | 0 |

### Per-bug results

| Bug | Passed | Iterations used | Target file recorded |
|---|:---:|---:|:---:|
| `bucketsort` | ✅ | 1 | `bucketsort.py` |
| `bitcount` | ✅ | 1 | `bitcount.py` |
| `mergesort` | ✅ | 1 | `mergesort.py` |
| `levenshtein` | ✅ | 1 | `levenshtein.py` |
| `gcd` | ✅ | 1 | `gcd.py` |
| `flatten` | ✅ | 1 | `flatten.py` |
| `sqrt` | ✅ | 1 | `sqrt.py` |
| `to_base` | ✅ | 1 | `to_base.py` |
| `next_permutation` | ✅ | 1 | `next_permutation.py` |
| `kth` | ✅ | 1 | `kth.py` |
| `powerset` | ✅ | 1 | `powerset.py` |
| `max_sublist_sum` | ✅ | 3 | `max_sublist_sum.py` |

These numbers describe the bundled evaluation artifact; they are not a guarantee that every future LLM run will reproduce the same outcome.

The repository also contains historical evaluation findings in `evaluation/FINDINGS.md`, including an earlier run with lower results and documented retry-loop/mis-targeting problems.

---

## Input modes

The agent is designed to work with:

| Input mode | Description |
|---|---|
| Bug report only | A plain-English description of the expected behavior and observed problem |
| Error output only | A traceback, assertion, or test failure without a separate description |
| Bug report + error output | Both sources of evidence together |

The repository includes experiments for all three modes, including an error-only Levenshtein case and a deliberately vague mergesort report.

---

## Running locally

### 1. Clone the repository

```bash
git clone https://github.com/souradipdey166/CodePilot-Agent-.git
cd CodePilot-Agent-
```

### 2. Create a virtual environment

Python 3.11 is the documented deployment target for this project.

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The repository pins the main runtime dependencies, including:

- `langgraph==0.6.11`
- `langchain-groq==0.3.8`
- `gradio==4.44.1`
- `pytest==8.4.2`
- `python-dotenv==1.2.1`
- `langsmith==0.4.37`
- `huggingface_hub==0.24.7`
- `fastapi==0.115.14`
- `starlette==0.46.2`

### 4. Configure environment variables

Create a local `.env` file:

```dotenv
GROQ_API_KEY=your_groq_api_key
```

Optional LangSmith tracing:

```dotenv
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=codepilot-agent
```

**Never commit or distribute real API keys.** Keep `.env` local.

### 5. Start the Gradio application

```bash
python app.py
```

The application binds to `0.0.0.0` and uses the `PORT` environment variable when supplied; otherwise it defaults to port `7860`.

---

## Using the UI

The Gradio interface accepts:

- **GitHub URL** — optionally clone a public repository automatically.
- **Repo path** — local repository path when no GitHub URL is supplied.
- **Bug report** — natural-language problem description.
- **Error output / traceback** — optional failing test or traceback output.
- **Test command** — optional custom command. If omitted, the benchmark-style QuixBugs test command is constructed from the selected target filename.

The UI returns:

- final success/failure status;
- the recorded agent trajectory;
- the generated `OLD -> NEW` patch;
- recent test output.

---

## Running the 12-bug benchmark

The benchmark runner is implemented in `evaluation/run_evaluation.py`, with the selected benchmark cases listed in `tests/test_batch_12.py`.

Run it with:

```bash
python -m tests.test_batch_12
```

The selected cases are:

```text
bucketsort
bitcount
mergesort
levenshtein
gcd
flatten
sqrt
to_base
next_permutation
kth
powerset
max_sublist_sum
```

Before each benchmark case, `evaluation/quixbugs_loader.py` resets the corresponding QuixBugs source file to its Git version. After the run, the batch is written to `evaluation/results/` as a timestamped JSON file.

### Benchmark methodology note

The evaluation is LLM-driven and therefore can have run-to-run variance. The current harness also records `target_file_found` from the final state rather than independently proving which file was modified. In addition, the default test command is derived from the selected target filename. For that reason, the raw result JSON should be read together with `evaluation/FINDINGS.md` when interpreting benchmark claims.

---

## General repository support

The core agent is not hard-coded to the QuixBugs programs. `test_execution()` accepts a configurable `test_command`, and the repository includes a small independent example under `scratch_general_test/`.

The general flow is:

```text
repository -> explore -> inspect -> diagnose -> patch -> validate -> test
```

For a custom repository, provide a repository path or GitHub URL and an appropriate test command in the UI.

---

## Project structure

```text
.
├── agent/
│   ├── state.py              # DebugState TypedDict
│   ├── nodes.py              # Ten LangGraph nodes
│   ├── graph.py              # StateGraph wiring and retry routing
│   └── pipeline.py           # Sequential pipeline implementation
│
├── tools/
│   ├── file_tools.py         # File listing and file reading
│   ├── search_tools.py       # Text search
│   └── patch_tools.py        # Exact OLD -> NEW replacement
│
├── evaluation/
│   ├── quixbugs_loader.py    # Benchmark file/test pairing and Git reset
│   ├── run_evaluation.py     # Batch runner and metrics
│   ├── results/               # Recorded batch JSON results
│   ├── FINDINGS.md            # Evaluation findings and failure taxonomy
│   └── SAFETY.md              # Existing safety notes
│
├── quixbugs_data/             # Bundled QuixBugs benchmark data
├── tests/                     # Experiment and validation scripts
├── patch_generator.py          # Groq / ChatGroq interface
├── app.py                     # Gradio web UI
└── requirements.txt            # Pinned Python dependencies
```

---

## Patch strategy

The agent deliberately generates a narrow patch rather than asking the LLM to rewrite a complete file.

The patch format is:

```text
OLD:
<exact existing lines>

NEW:
<replacement lines>
```

Before writing the file, `patch_validation()` checks that the OLD snippet exists **exactly once**. This prevents accidental application when the requested text is absent or ambiguous.

The original file contents are retained in state before patch application, but the current implementation does not expose a separate rollback operation.

---

## Test execution and sandboxing

The runtime checks whether a usable Docker CLI/daemon is available.

### With Docker available

Tests are run in a disposable container using the configured image name:

```text
code-agent-sandbox
```

The target repository is mounted at `/workspace`, and test execution has a 60-second subprocess timeout.

**Important:** this project snapshot does not include a `Dockerfile` for building `code-agent-sandbox`; a compatible image must already be available for the Docker branch to work.

### Without Docker

The code falls back to direct execution in the application process using `bash -c`.

That fallback is used by the current Render deployment described by the project. Because a user can supply a GitHub repository and a test command through the UI, the hosted service should be treated as a demonstration environment rather than a hardened code-execution sandbox.

For untrusted repositories, use a properly isolated environment and do not expose unrestricted command execution to the public internet.

---

## Important limitations

### 1. Repository exploration can mis-target files

Keyword search can return multiple candidate files. The LLM chooses from the inspected candidates, and historical runs documented cases where the wrong file was targeted. The latest bundled 12/12 result recorded the expected target for all twelve cases, but this remains an evaluation limitation.

### 2. Retry iterations can become inconsistent with the file on disk

A failed repair can leave a modified file on disk while the next reasoning step still has inspection context from before that modification. `evaluation/FINDINGS.md` documents this problem, including the earlier `max_sublist_sum` failure mode.

### 3. `target_file_found` is state-based logging

The batch runner records the final `target_file` state. On multi-iteration runs, that can differ from the file changed during an earlier attempt. Successful patch application should ideally record the actual file at the moment the patch is applied.

### 4. Exact-string patching is brittle

Whitespace, indentation, or formatting differences in an LLM-generated OLD snippet can cause validation to fail even when the intended logic is correct.

### 5. Test selection in the default QuixBugs path depends on the target filename

When `test_command` is empty, `test_execution()` constructs a pytest command from `state["target_file"]`. This is convenient for the benchmark, but it means evaluation should independently verify that the expected benchmark test was executed and that the expected program was modified.

### 6. The Graph and sequential pipeline are separate execution paths

`agent/pipeline.py` contains a sequential retry loop, while `agent/graph.py` defines the LangGraph retry routing. They should be kept behaviorally aligned when retry semantics are changed.

### 7. The benchmark is stochastic in practice

The LLM is called multiple times during a run, so the same bug can produce different exploration, diagnosis, patch, and retry trajectories across runs. Reported benchmark results therefore describe recorded runs, not deterministic guarantees.

---

## Observability

The project uses LangSmith-compatible environment variables for tracing. When tracing is enabled, LangChain/LangSmith can capture execution information for the graph and its model calls.

Configure:

```dotenv
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=codepilot-agent
```

---

## Deployment

The included application is compatible with a Render-style web service configuration:

```text
Git repository
      |
      v
Render Web Service
      |
      v
pip install -r requirements.txt
      |
      v
python app.py
      |
      v
Gradio -> LangGraph -> pytest
```

The application reads the hosting platform's `PORT` environment variable and binds to `0.0.0.0`.

The current source checks for a Docker daemon at runtime. In environments without Docker, it uses the direct-execution fallback described above.

---

## Contributing / development hygiene

Before publishing this project or sharing an archive:

- remove `.env` and any real credentials;
- do not include a local `venv/` directory;
- remove `__pycache__/` and `.pytest_cache/` artifacts;
- keep benchmark source files in a known clean Git state before evaluation;
- preserve the raw JSON result for every reported benchmark run;
- distinguish current benchmark results from historical findings.

The repository's `.gitignore` already excludes several local/runtime artifacts, but an archive should still be checked before distribution.

---

## Acknowledgement

This project uses the [QuixBugs](https://github.com/jkoppel/QuixBugs) benchmark as its bundled program-repair dataset.

QuixBugs contains Python and Java implementations of algorithmic programs, corresponding tests, and corrected Python programs. The CodePilot evaluation layer selects a subset of those Python cases for agent evaluation.

---

## License

The benchmark data under `quixbugs_data/` retains its upstream licensing and attribution. See `quixbugs_data/LICENSE` for the benchmark's license information.
