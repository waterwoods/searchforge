"""
ecommerce_agent_graph.py - Ecommerce After-Sales Agent Graph

Minimal runnable ecommerce after-sales agent workflow using LangGraph to chain tools:
- order_tool.get_order_or_raise
- refund_tool.calculate_refund_amount

This is a minimal implementation that can be extended to support more scenarios and features.
"""

import logging
from datetime import datetime
from typing import TypedDict, Optional, List, Dict, Any

from langgraph.graph import StateGraph, END

from services.fiqa_api.observability.langsmith_tracing import maybe_traceable

logger = logging.getLogger(__name__)

from ..schemas import (
    EcommerceAgentRequest,
    EcommerceAgentResponse,
    Order,
    RefundCalculation,
    AgentStep,
    RefundReason,
)
from ..tools.order_tool import get_order_or_raise
from ..tools.refund_tool import check_refund_eligibility, calculate_refund_amount
from ..response_generator import EcommerceResponseFacts, generate_customer_reply
from ..ecommerce_rag_retriever import retrieve_policy_snippets
from ..ecommerce_judge import judge_refund_decision
from ..nl_to_intent import parse_user_message, EcommerceNLParseError


class EcommerceAgentState(TypedDict, total=False):
    """LangGraph state for ecommerce after-sales agent workflow."""
    
    # Input
    request: EcommerceAgentRequest
    
    # Intent classification (currently fixed to "refund")
    intent: str
    
    # Intermediate results
    order: Order
    refund_reason: Optional[RefundReason]
    refund_eligible: Optional[bool]
    refund: Optional[RefundCalculation]
    policy_context: Optional[List[Dict[str, Any]]]  # RAG-retrieved policy snippets
    
    # Judge results
    judgement: Optional[Dict[str, Any]]  # RefundJudgement result stored as dict
    requires_manual_review: Optional[bool]  # Whether to block and require manual review
    
    # Metadata
    ticket_id: Optional[str]  # Reserved field, currently unused
    agent_steps: List[AgentStep]
    final_response: str  # Natural language response returned to user
    llm_metrics: Optional[List[Dict[str, Any]]]  # LLM call metrics for cost/latency tracking


@maybe_traceable(name="classify_intent")
def classify_intent(state: EcommerceAgentState) -> Dict[str, Any]:
    """
    Node: Classify user intent using LLM-based NL parsing.
    
    Extracts intent, order_id, and refund reason from user message using LLM.
    Falls back to safe defaults if parsing fails.
    """
    # Initialize agent_steps if it doesn't exist
    agent_steps: List[AgentStep] = state.get("agent_steps", [])
    
    # Get request and user message
    request = state.get("request")
    if not request:
        raise ValueError("Missing request in state")
    
    user_message = request.user_message
    original_order_id = request.order_id
    
    # Initialize llm_metrics if it doesn't exist
    llm_metrics: List[Dict[str, Any]] = state.get("llm_metrics", [])
    
    # Try to parse using LLM
    parse_error = None
    parsed = None
    
    try:
        parsed = parse_user_message(user_message, default_order_id=original_order_id, metrics_list=llm_metrics)
    except EcommerceNLParseError as e:
        parse_error = str(e)
        logger.warning(f"NL parsing failed, using fallback: {parse_error}")
    
    # Use parsed result or fallback to defaults
    if parsed:
        intent = parsed.intent
        parsed_order_id = parsed.order_id
        reason_type = parsed.reason_type
        reason_description = parsed.reason_description
    else:
        # Fallback to safe defaults
        intent = "refund"
        parsed_order_id = None
        reason_type = "OTHER"  # Use default reason type for fallback
        reason_description = user_message or "Refund request"
    
    # Update request.order_id if it was empty and we parsed one
    # (This ensures query_order node can access the parsed order_id)
    
    # Construct RefundReason - always create one (either from parsed result or fallback)
    refund_reason = RefundReason(
        reason_type=reason_type or "OTHER",  # type: ignore
        description=reason_description or user_message or "Refund request",
    )
    
    # Record step
    step_outputs = {
        "intent": intent,
        "parsed_order_id": parsed_order_id,
        "reason_type": reason_type,
        "reason_description": reason_description,
    }
    if parse_error:
        step_outputs["error"] = parse_error
    
    step = AgentStep(
        step_id="classify_intent_1",
        step_name="classify_intent",
        status="done",
        timestamp=datetime.utcnow().isoformat(),
        inputs={
            "user_message": user_message,
            "original_order_id": original_order_id,
        },
        outputs=step_outputs,
    )
    agent_steps.append(step)
    
    # Prepare return dict
    # refund_reason is always created (either from parsed result or fallback)
    result = {
        "intent": intent,
        "agent_steps": agent_steps,
        "llm_metrics": llm_metrics,
        "refund_reason": refund_reason,  # Always present now
    }
    
    # Update request.order_id if it was empty and we parsed one
    if not original_order_id and parsed_order_id:
        # Create a new request object with updated order_id
        # LangGraph will merge this into state, so query_order can access it
        updated_request = EcommerceAgentRequest(
            user_message=request.user_message,
            order_id=parsed_order_id,
            order=request.order
        )
        result["request"] = updated_request
    
    return result


@maybe_traceable(name="query_order")
def query_order(state: EcommerceAgentState) -> Dict[str, Any]:
    """
    Node: Query order information.
    
    Retrieves order_id from request and calls get_order_or_raise to get order details.
    """
    request = state.get("request")
    if not request:
        raise ValueError("Missing request in state")
    
    order_id = request.order_id
    if not order_id:
        raise ValueError("Missing order_id in request")
    
    # Call tool to query order
    order = get_order_or_raise(order_id)
    
    # Update agent_steps
    agent_steps: List[AgentStep] = state.get("agent_steps", [])
    step = AgentStep(
        step_id="query_order_1",
        step_name="query_order",
        status="completed",
        timestamp=datetime.utcnow().isoformat(),
        inputs={"order_id": order_id},
        outputs={"order_id": order.order_id, "status": order.status},
    )
    agent_steps.append(step)
    
    return {
        "order": order,
        "agent_steps": agent_steps,
    }


@maybe_traceable(name="check_refund_eligibility")
def check_refund(state: EcommerceAgentState) -> Dict[str, Any]:
    """
    Node: Check if order meets refund eligibility requirements.
    Uses refund_tool.check_refund_eligibility.
    """
    order = state.get("order")
    refund_reason = state.get("refund_reason")
    if order is None or refund_reason is None:
        raise ValueError("Missing order or refund_reason in state")

    eligible = check_refund_eligibility(order, refund_reason)

    agent_steps: List[AgentStep] = state.get("agent_steps", [])
    step = AgentStep(
        step_id="check_refund_eligibility_1",
        step_name="check_refund_eligibility",
        status="done",
        timestamp=datetime.utcnow().isoformat(),
        inputs={"order_id": order.order_id, "reason_type": refund_reason.reason_type},
        outputs={"eligible": eligible},
    )
    agent_steps.append(step)

    return {
        "refund_eligible": eligible,
        "agent_steps": agent_steps,
    }


@maybe_traceable(name="calculate_refund")
def calculate_refund(state: EcommerceAgentState) -> Dict[str, Any]:
    """
    Node: Calculate refund amount.
    
    First checks refund_eligible; only calculates refund amount when eligible is True.
    """
    order = state.get("order")
    refund_reason = state.get("refund_reason")
    eligible = state.get("refund_eligible")
    
    if not order:
        raise ValueError("Missing order in state")
    if refund_reason is None:
        raise ValueError("Missing refund_reason in state")
    
    # If eligible is False, skip calculation
    if eligible is False:
        agent_steps: List[AgentStep] = state.get("agent_steps", [])
        step = AgentStep(
            step_id="calculate_refund_1",
            step_name="calculate_refund",
            status="done",
            timestamp=datetime.utcnow().isoformat(),
            inputs={},
            outputs={"reason": "refund_not_eligible"},
        )
        agent_steps.append(step)
        return {"refund": None, "agent_steps": agent_steps}
    
    # If eligible is None, treat as not eligible
    if eligible is None:
        agent_steps: List[AgentStep] = state.get("agent_steps", [])
        step = AgentStep(
            step_id="calculate_refund_1",
            step_name="calculate_refund",
            status="done",
            timestamp=datetime.utcnow().isoformat(),
            inputs={},
            outputs={"reason": "refund_eligible_not_checked"},
        )
        agent_steps.append(step)
        return {"refund": None, "agent_steps": agent_steps}
    
    # eligible is True, call tool to calculate refund amount (using entire order.items)
    refund = calculate_refund_amount(order, refund_reason, items=None)
    
    # Update agent_steps
    agent_steps: List[AgentStep] = state.get("agent_steps", [])
    step = AgentStep(
        step_id="calculate_refund_1",
        step_name="calculate_refund",
        status="completed",
        timestamp=datetime.utcnow().isoformat(),
        inputs={"order_id": order.order_id, "reason_type": refund_reason.reason_type},
        outputs={
            "eligible": True,
            "eligible_amount": refund.eligible_amount,
            "reason": refund.reason,
            "policy_reference": refund.policy_reference,
        },
    )
    agent_steps.append(step)
    
    return {
        "refund": refund,
        "agent_steps": agent_steps,
    }


@maybe_traceable(name="judge_decision")
def judge_decision(state: EcommerceAgentState) -> Dict[str, Any]:
    """
    Node: Rule-based judge to validate refund decision against policy.
    
    This node performs deterministic checks to ensure the refund decision
    is consistent with policy rules. If inconsistencies are detected,
    the decision is blocked and requires manual review.
    """
    order = state.get("order")
    refund = state.get("refund")
    refund_eligible = state.get("refund_eligible")
    refund_reason = state.get("refund_reason")
    
    # Call judge function
    judgement = judge_refund_decision(
        order=order,
        refund=refund,
        refund_eligible=refund_eligible,
        refund_reason=refund_reason,
    )
    
    # Convert to dict for state storage
    judgement_dict = judgement.to_dict()
    requires_manual_review = judgement.should_block
    
    # Update agent_steps
    agent_steps: List[AgentStep] = state.get("agent_steps", [])
    step = AgentStep(
        step_id="judge_decision_1",
        step_name="judge_decision",
        status="completed",
        timestamp=datetime.utcnow().isoformat(),
        inputs={
            "order_id": order.order_id if order else None,
            "refund_eligible": refund_eligible,
            "refund_amount": refund.eligible_amount if refund else None,
            "reason_type": refund_reason.reason_type if refund_reason else None,
        },
        outputs=judgement_dict,
    )
    agent_steps.append(step)
    
    return {
        "judgement": judgement_dict,
        "requires_manual_review": requires_manual_review,
        "agent_steps": agent_steps,
    }


@maybe_traceable(name="retrieve_policy")
def retrieve_policy(state: EcommerceAgentState) -> Dict[str, Any]:
    """
    Node: Retrieve relevant policy snippets based on user message and order/refund context.
    
    Constructs a query from user message and context, retrieves top-K policy snippets,
    and stores them in state.policy_context for use in response generation.
    """
    request = state.get("request")
    order = state.get("order")
    refund_reason = state.get("refund_reason")
    refund = state.get("refund")
    
    # Build query from user message and context
    query_parts = []
    
    # Base query: user message
    if request and request.user_message:
        query_parts.append(request.user_message)
    
    # Add order status if available
    if order:
        query_parts.append(f"order status: {order.status}")
    
    # Add refund reason if available
    if refund_reason:
        query_parts.append(f"refund reason: {refund_reason.reason_type}")
    
    # Add refund amount context if available
    if refund:
        query_parts.append(f"refund amount: {refund.eligible_amount}")
    
    query = " ".join(query_parts)
    
    # Retrieve policy snippets (k=3 by default)
    try:
        snippets = retrieve_policy_snippets(query, k=3)
        policy_context = [snippet.model_dump() for snippet in snippets]
    except Exception as e:
        # Log warning but don't fail the workflow
        logger.warning(f"Failed to retrieve policy snippets: {e}")
        policy_context = []
    
    # Update agent_steps
    agent_steps: List[AgentStep] = state.get("agent_steps", [])
    step = AgentStep(
        step_id="retrieve_policy_1",
        step_name="retrieve_policy",
        status="completed",
        timestamp=datetime.utcnow().isoformat(),
        inputs={"query": query},
        outputs={"snippets_count": len(policy_context)},
    )
    agent_steps.append(step)
    
    return {
        "policy_context": policy_context,
        "agent_steps": agent_steps,
    }


@maybe_traceable(name="generate_response")
def generate_response(state: EcommerceAgentState) -> Dict[str, Any]:
    """
    Node: Generate final natural language response message to user using LLM.
    
    This node:
    1. Checks judge result - if requires_manual_review is True, returns safe fallback response
    2. Otherwise, extracts facts from state (order, refund eligibility, refund amount, etc.)
    3. Constructs EcommerceResponseFacts object
    4. Calls LLM-based response generator to produce natural customer reply
    5. Falls back to rule-based template if LLM is unavailable
    
    Business logic (refund eligibility, amounts) is determined by tools layer.
    Judge layer ensures decisions are consistent with policy before generating response.
    This node only handles phrasing/communication.
    """
    order = state.get("order")
    eligible = state.get("refund_eligible")
    refund = state.get("refund")
    refund_reason_obj = state.get("refund_reason")
    policy_context = state.get("policy_context")
    requires_manual_review = state.get("requires_manual_review", False)
    judgement = state.get("judgement")
    
    if not order:
        raise ValueError("Missing order in state")
    
    # Check if manual review is required (judge blocked the decision)
    if requires_manual_review:
        # Return safe fallback response without calling LLM
        judge_reason = judgement.get("reason", "Policy validation failed") if judgement else "Policy validation failed"
        customer_reply = (
            f"We are currently unable to automatically process this request according to our refund policy. "
            f"A human support agent will review your case shortly. "
            f"Reason: {judge_reason}"
        )
        
        # Update agent_steps
        agent_steps: List[AgentStep] = state.get("agent_steps", [])
        step = AgentStep(
            step_id="generate_response_1",
            step_name="generate_response",
            status="completed",
            timestamp=datetime.utcnow().isoformat(),
            inputs={
                "order_id": order.order_id,
                "requires_manual_review": True,
                "judgement": judgement,
            },
            outputs={"final_response": customer_reply},
        )
        agent_steps.append(step)
        
        return {
            "final_response": customer_reply,
            "agent_steps": agent_steps,
        }
    
    # Normal flow: generate response using LLM
    # Construct policy_summary from RAG-retrieved policy_context
    policy_summary = None
    if policy_context and len(policy_context) > 0:
        # Extract text from top snippets and join them
        snippet_texts = [snippet.get("text", "") for snippet in policy_context[:3]]
        policy_summary = " | ".join(snippet_texts)
    elif refund:
        # Fallback to original policy_reference if RAG didn't return anything
        policy_summary = refund.policy_reference
    
    # Layer 1: Extract and structure facts from state (no LLM calls here)
    facts = EcommerceResponseFacts(
        order_id=order.order_id,
        order_status=order.status,
        refund_eligible=eligible,
        refund_amount=refund.eligible_amount if refund else None,
        currency="USD",  # Default currency, can be extended to support multi-currency
        refund_reason=refund.reason if refund else (
            refund_reason_obj.description if refund_reason_obj else None
        ),
        policy_summary=policy_summary,
        additional_notes=None,
    )
    
    # Initialize llm_metrics if it doesn't exist
    llm_metrics: List[Dict[str, Any]] = state.get("llm_metrics", [])
    
    # Layer 2: Call LLM to generate natural customer reply
    # generate_customer_reply handles LLM failures internally and falls back to template
    customer_reply = generate_customer_reply(facts, metrics_list=llm_metrics)
    
    # Update agent_steps
    agent_steps: List[AgentStep] = state.get("agent_steps", [])
    step = AgentStep(
        step_id="generate_response_1",
        step_name="generate_response",
        status="completed",
        timestamp=datetime.utcnow().isoformat(),
        inputs={
            "order_id": order.order_id,
            "facts": facts.model_dump(exclude_none=True),
            "requires_manual_review": False,
            "judgement": judgement,
        },
        outputs={"final_response": customer_reply},
    )
    agent_steps.append(step)
    
    return {
        "final_response": customer_reply,
        "agent_steps": agent_steps,
        "llm_metrics": llm_metrics,
    }


def build_ecommerce_agent_graph() -> StateGraph:
    """
    Build and return the ecommerce agent LangGraph.
    
    Returns:
        Uncompiled StateGraph instance
    """
    graph = StateGraph(EcommerceAgentState)
    
    # Add nodes
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("query_order", query_order)
    graph.add_node("check_refund_eligibility", check_refund)
    graph.add_node("calculate_refund", calculate_refund)
    graph.add_node("judge_decision", judge_decision)
    graph.add_node("retrieve_policy", retrieve_policy)
    graph.add_node("generate_response", generate_response)
    
    # Set entry point
    graph.set_entry_point("classify_intent")
    
    # Add edges (linear flow with judge inserted after calculate_refund)
    graph.add_edge("classify_intent", "query_order")
    graph.add_edge("query_order", "check_refund_eligibility")
    graph.add_edge("check_refund_eligibility", "calculate_refund")
    graph.add_edge("calculate_refund", "judge_decision")
    graph.add_edge("judge_decision", "retrieve_policy")
    graph.add_edge("retrieve_policy", "generate_response")
    graph.add_edge("generate_response", END)
    
    return graph


# Compiled version for convenient external calls
compiled_ecommerce_agent_graph = build_ecommerce_agent_graph().compile()


@maybe_traceable(name="ecommerce_after_sales_agent")
def run_ecommerce_agent(request: EcommerceAgentRequest) -> EcommerceAgentState:
    """
    Helper function to run the ecommerce agent, convenient for local testing.
    
    Args:
        request: EcommerceAgentRequest instance containing user message and order ID
    
    Returns:
        EcommerceAgentState after execution completes
    
    Note:
        This function is wrapped with LangSmith tracing. To enable tracing:
        - Set LANGSMITH_API_KEY environment variable
        - Optionally set LANGSMITH_PROJECT to organize traces in LangSmith UI
        - If not configured, the function runs normally without tracing (silent no-op)
    """
    state: EcommerceAgentState = {
        "request": request,
        "agent_steps": [],
        "llm_metrics": [],
    }
    
    result = compiled_ecommerce_agent_graph.invoke(state)
    return result
