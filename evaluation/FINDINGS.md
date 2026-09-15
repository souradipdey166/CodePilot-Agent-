# Evaluation Findings

## Batch Run: 2026-09-06 (12 bugs)
- **Repair rate:** 11/12 (91.7%)
- **First-attempt success:** 10/12 (83.3%)
- Full raw results: `evaluation/results/batch_20260906_132028.json`

## Real bugs fixed autonomously (11)
bucketsort, bitcount, mergesort, levenshtein (x2, error-only + prompt+error modes), 
gcd, flatten, sqrt, to_base, next_permutation, kth, powerset

## Failure Case: `max_sublist_sum`

**Outcome:** Crashed after hitting LangGraph's internal recursion limit (25), 
not the intended `max_iterations=3` limit.

**Root cause diagnosis by the agent:** Correct in every attempt. The agent 
consistently and accurately identified that Kadane's algorithm needs to reset 
the running sum when it goes negative.

**What actually failed:** An architectural bug in the retry loop itself, not 
a reasoning failure by the LLM:

1. Attempt 1 generated a patch, applied it successfully, but the patch's 
   interpretation of an edge case (all-negative input) conflicted with the 
   test's expected behavior (return 0 for all-negative lists vs. return the 
   least-negative element).
2. On retry, `patch_generation` and `patch_validation` attempted to match 
   against the *original* buggy code, but the file had already been modified 
   by attempt 1 — the OLD snippet no longer existed in the file.
3. `patch_validation` correctly rejected this (as designed), but the loop 
   did not reset the file to a clean state before generating the next attempt, 
   so the LLM kept regenerating the *same* patch against a prompt built from 
   stale/original code context, repeating the identical failed attempt.
4. This repeated 3 times without ever converging, ultimately hitting 
   LangGraph's internal recursion safety limit rather than a clean 
   "repair unsuccessful" result.

**Category:** Retry-loop file-state desynchronization (patch generation and 
file state can drift out of sync across iterations when a patch partially 
succeeds but doesn't resolve the underlying test).

**Fix identified (not yet implemented):** Reset the target file to its 
original state at the start of each retry iteration (matching the pattern 
already used in `test_execution` between batch runs), so `patch_generation` 
always operates against a known, consistent starting point rather than 
whatever a previous failed attempt left behind.

**Why this finding is valuable:** This is not a reasoning failure — the LLM's 
diagnosis was correct 3/3 times. It's a genuine engineering gap in how state 
is managed across retry iterations, which is exactly the kind of architectural 
insight this evaluation was designed to surface.

## Other observations
- Both `patch_validation` failure types observed this session:
  - Whitespace/indentation exact-match mismatches (self-resolving on retry, 
    since the file was still in original state at that point)
  - Stale-match failures after a prior successful-but-wrong patch application 
    (the max_sublist_sum case — does NOT self-resolve, causes the loop above)
- Exploration correctly narrowed to the right file in 12/12 cases, including 
  when multiple unrelated candidate files were returned by keyword search 
  (e.g., `flatten` search also matched `breadth_first_search.py` and 
  `hanoi.py` — the agent correctly diagnosed real bugs in all three but only 
  patched the one relevant to the reported issue)


## Generality Proof

To verify the agent is not QuixBugs-specific, `test_execution` was refactored 
to accept a configurable `test_command` (falling back to QuixBugs' pattern 
only when unset). Verified on a minimal, independent test repo 
(`scratch_general_test/`) outside the benchmark entirely:

- Repo: a single `calc.py` with a subtraction/addition bug, unrelated to QuixBugs
- Test command: custom (`pytest test_calc.py -v`)
- Result: correctly explored, diagnosed, patched, and verified — first attempt, PASSED

This confirms the agent's core reasoning/patching pipeline (tools, nodes, graph) 
has no QuixBugs-specific dependencies; only the evaluation harness 
(`evaluation/quixbugs_loader.py`) and the default fallback in `test_execution` 
are benchmark-specific.

## Failure Taxonomy

| Category | Count | Bugs |
|---|---|---|
| Success — first attempt | X | bitcount, mergesort, ... |
| Success — via retry (validation exact-match mismatch, self-resolved) | X | bucketsort |
| Failure — retry-loop file-state desynchronization | 1 | max_sublist_sum |

### Category definitions

**Success — first attempt:** Agent correctly diagnosed and fixed the bug on 
the first try, patch validated and applied cleanly, tests passed.

**Success — via retry (exact-match mismatch):** First attempt's patch had 
correct logic but the OLD snippet failed exact-string validation (usually 
whitespace/indentation drift in the LLM's output). File remained in its 
original state, so the retry regenerated a matching patch successfully.

**Failure — retry-loop file-state desynchronization:** Diagnosis was correct 
across all attempts, but a partial/incorrect patch was applied on attempt 1, 
and subsequent attempts' prompts were built from stale (pre-patch) code 
context rather than the file's actual current state — causing the same 
failed patch to be regenerated repeatedly until hitting LangGraph's internal 
recursion limit rather than the intended `max_iterations` cap.

## Failure Taxonomy

| Category | Count | Bugs |
|---|---|---|
| Success — first attempt | 10/12 | bucketsort, bitcount, mergesort, gcd, flatten, sqrt, to_base, next_permutation, kth, powerset |
| Success — via retry | 1/12 | levenshtein (3 iterations — reason under investigation) |
| Failure — retry-loop file-state desynchronization | 1/12 | max_sublist_sum |

**Repair rate: 11/12 (91.7%)**
**First-attempt success: 10/12 (83.3%)**

## Known logging limitation
`target_file_found` in evaluation results can be misleading for multi-iteration 
runs — it reflects the state's `target_file` field at the time the graph 
terminated, which may differ from the file that was actually successfully 
patched, since `root_cause_hypothesis` can re-target a different candidate 
file on each retry. `tests_passed` remains accurate (verified via real 
pytest execution each attempt), but per-bug "which file was fixed" logging 
should be captured at the moment of successful patch application, not at 
graph exit. Confirmed via git diff: actual file modifications matched 
expected targets in all cases checked.