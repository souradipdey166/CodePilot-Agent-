from langgraph.graph import StateGraph, END
from agent.state import DebugState
from agent.nodes import (
    error_analysis, repository_exploration, code_inspection,
    root_cause_hypothesis, patch_generation, patch_validation,
    patch_application, test_execution, failure_analysis, iteration_check
)

def route_after_test(state: DebugState) -> str:
    """Decide: done, retry, or give up."""
    if state["tests_passed"]:
        return "success"
    if state["iteration"] >= state["max_iterations"]:
        return "give_up"
    return "retry"

def build_graph():
    graph = StateGraph(DebugState)

    graph.add_node("error_analysis", error_analysis)
    graph.add_node("repository_exploration", repository_exploration)
    graph.add_node("code_inspection", code_inspection)
    graph.add_node("root_cause_hypothesis", root_cause_hypothesis)
    graph.add_node("patch_generation", patch_generation)
    graph.add_node("patch_validation", patch_validation)
    graph.add_node("patch_application", patch_application)
    graph.add_node("test_execution", test_execution)
    graph.add_node("failure_analysis", failure_analysis)
    graph.add_node("iteration_check", iteration_check)

    graph.set_entry_point("error_analysis")
    graph.add_edge("error_analysis", "repository_exploration")
    graph.add_edge("repository_exploration", "code_inspection")
    graph.add_edge("code_inspection", "root_cause_hypothesis")
    graph.add_edge("root_cause_hypothesis", "patch_generation")
    graph.add_edge("patch_generation", "patch_validation")
    graph.add_edge("patch_validation", "patch_application")
    graph.add_edge("patch_application", "test_execution")

    graph.add_conditional_edges(
        "test_execution",
        route_after_test,
        {
            "success": END,
            "retry": "failure_analysis",
            "give_up": END
        }
    )
    graph.add_edge("failure_analysis", "iteration_check")
    #graph.add_edge("iteration_check", "root_cause_hypothesis")
    graph.add_edge("iteration_check", "code_inspection")

    return graph.compile()