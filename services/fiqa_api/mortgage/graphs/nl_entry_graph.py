# services/fiqa_api/mortgage/graphs/nl_entry_graph.py

"""
NLU Entry Graph - Minimal LangGraph for natural language to structured slots.

This graph demonstrates how an English query turns into structured mortgage fields
and distinguishes between "enough info to run stress check" vs "missing required fields".
"""

import logging
from typing import TypedDict, Optional, List

from langgraph.graph import StateGraph, END

from services.fiqa_api.mortgage.nl_to_stress_request import (
    PartialStressRequest,
    NLToStressRequestOutput,
)
from services.fiqa_api.mortgage.graphs.single_home_graph import (
    _nl_to_stress_request_node,
    _need_more_info_router,
    SingleHomeGraphState,
)

logger = logging.getLogger(__name__)


def _build_nl_entry_graph() -> StateGraph:
    """
    Build and compile a minimal NLU-only graph.
    
    Flow:
    nl_entry → nl_to_stress_request → need_more_info_router → END
    """
    graph = StateGraph(SingleHomeGraphState)
    
    graph.add_node("nl_to_stress_request", _nl_to_stress_request_node)
    
    graph.set_entry_point("nl_to_stress_request")
    
    graph.add_conditional_edges(
        "nl_to_stress_request",
        _need_more_info_router,
        {
            "have_enough_info": END,
            "need_more_info": END,
        },
    )
    
    return graph.compile()


def run_nl_entry_graph(
    user_text: str,
    *,
    config: Optional[dict] = None,
) -> dict:
    """
    Run the NLU entry graph with a user text query.
    
    Args:
        user_text: Natural language query from user
        config: Optional LangGraph config
        
    Returns:
        Final state dictionary with:
        - partial_request: PartialStressRequest with extracted fields
        - missing_required_fields: List of missing required field names
        - nl_intent_type: Intent classification
        - Router decision: "have_enough_info" or "need_more_info"
    """
    graph = _build_nl_entry_graph()
    
    initial_state: SingleHomeGraphState = {
        "user_text": user_text,
        "partial_request": None,
        "missing_required_fields": None,
        "nl_intent_type": None,
        "agent_steps": [],
        "errors": [],
    }
    
    final_state = graph.invoke(initial_state, config=config)
    
    # Determine which branch the router took
    missing = final_state.get("missing_required_fields") or []
    partial_request = final_state.get("partial_request")
    
    if len(missing) == 0 and partial_request is not None:
        router_decision = "have_enough_info"
    else:
        router_decision = "need_more_info"
    
    return {
        "partial_request": final_state.get("partial_request"),
        "missing_required_fields": final_state.get("missing_required_fields") or [],
        "nl_intent_type": final_state.get("nl_intent_type"),
        "router_decision": router_decision,
    }

