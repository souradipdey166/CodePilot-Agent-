from agent.nodes import (
    error_analysis, repository_exploration, code_inspection,
    root_cause_hypothesis, patch_generation, patch_validation,
    patch_application, test_execution, failure_analysis, iteration_check
)
from agent.state import DebugState

def run_pipeline(state: DebugState) -> DebugState:
    state = error_analysis(state)
    state = repository_exploration(state)
    state = code_inspection(state)

    while state["iteration"] < state["max_iterations"]:
        state = root_cause_hypothesis(state)
        state = patch_generation(state)
        state = patch_validation(state)
        state = patch_application(state)
        state = test_execution(state)

        if state["tests_passed"]:
            print(f"\n✅ SUCCESS on iteration {state['iteration'] + 1}")
            return state

        state = failure_analysis(state)
        state = iteration_check(state)

    print(f"\n❌ FAILED after {state['max_iterations']} iterations")
    return state