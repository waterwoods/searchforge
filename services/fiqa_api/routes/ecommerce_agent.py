"""
ecommerce_agent.py - Ecommerce Refund Agent HTTP Router
========================================================
HTTP API wrapper around the ecommerce refund agent for demos and Kubernetes deployment.

This router provides a minimal HTTP endpoint that wraps the ecommerce refund agent graph.
The agent handles after-sales inquiries, particularly refund requests, using a LangGraph
workflow that chains tools for order lookup, refund eligibility checking, and refund
calculation.

Endpoint:
    POST /api/ecommerce-agent/run

Usage Example (curl):
    curl -X POST http://localhost:8000/api/ecommerce-agent/run \
        -H "Content-Type: application/json" \
        -d '{"order_id": "AMZ10001", "user_message": "I want a refund"}'

Intended for:
    - Demo deployments
    - Kubernetes deployment with health checks
    - Integration testing
"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.fiqa_api.ecommerce.graphs.ecommerce_agent_graph import (
    run_ecommerce_agent,
    EcommerceAgentState,
)
from services.fiqa_api.ecommerce.schemas import EcommerceAgentRequest

logger = logging.getLogger(__name__)

# ========================================
# Router Setup
# ========================================

router = APIRouter()

# ========================================
# HTTP Request/Response Models
# ========================================


class EcommerceAgentHttpRequest(BaseModel):
    """HTTP request model for ecommerce agent endpoint."""

    order_id: str = Field(..., description="Order ID for the refund inquiry")
    user_message: str = Field(..., description="User's message or refund request")


class EcommerceAgentHttpResponse(BaseModel):
    """HTTP response model for ecommerce agent endpoint."""

    order_id: str = Field(..., description="Order ID")
    final_response: str = Field(..., description="Final agent response message to user")
    refund_eligible: Optional[bool] = Field(
        None, description="Whether the order is eligible for refund"
    )
    refund_amount: Optional[float] = Field(
        None, description="Refund amount if eligible"
    )
    currency: Optional[str] = Field(None, description="Currency code (e.g., USD)")
    raw_state: Optional[dict] = Field(
        None, description="Raw agent state for debugging (optional)"
    )


# ========================================
# Route Handler
# ========================================


@router.post("/ecommerce-agent/run", response_model=EcommerceAgentHttpResponse)
async def ecommerce_agent_run(request: EcommerceAgentHttpRequest):
    """
    Ecommerce refund agent endpoint.

    Takes order_id and user_message, runs the ecommerce refund agent workflow,
    and returns a structured response with refund eligibility and amount.

    Request body:
        order_id: str - Order ID for the refund inquiry (required, non-empty)
        user_message: str - User's message or refund request (required, non-empty)

    Returns:
        EcommerceAgentHttpResponse with:
            - order_id: str - Order ID
            - final_response: str - Agent's final response message
            - refund_eligible: bool | None - Refund eligibility status
            - refund_amount: float | None - Refund amount if eligible
            - currency: str | None - Currency code
            - raw_state: dict | None - Raw agent state (for debugging)

    Example request:
        {
            "order_id": "AMZ10001",
            "user_message": "I want a refund for my order"
        }

    Example response:
        {
            "order_id": "AMZ10001",
            "final_response": "We can process a refund of $50.00...",
            "refund_eligible": true,
            "refund_amount": 50.0,
            "currency": "USD",
            "raw_state": null
        }
    """
    try:
        # Input validation: ensure order_id and user_message are non-empty
        if not request.order_id or not request.order_id.strip():
            logger.warning(
                f"level=WARN endpoint=ecommerce_agent_run status=VALIDATION_ERROR "
                f"error='order_id is empty'"
            )
            raise HTTPException(
                status_code=400,
                detail="order_id cannot be empty",
            )

        if not request.user_message or not request.user_message.strip():
            logger.warning(
                f"level=WARN endpoint=ecommerce_agent_run status=VALIDATION_ERROR "
                f"error='user_message is empty'"
            )
            raise HTTPException(
                status_code=400,
                detail="user_message cannot be empty",
            )

        logger.info(
            f"level=INFO endpoint=ecommerce_agent_run "
            f"order_id={request.order_id} "
            f"user_message_length={len(request.user_message)}"
        )

        # Construct internal request model
        internal_request = EcommerceAgentRequest(
            user_message=request.user_message.strip(),
            order_id=request.order_id.strip(),
            order=None,  # Let the agent query the order
        )

        # Run the ecommerce agent in a thread pool to avoid blocking the event loop
        # run_ecommerce_agent is a synchronous function that may take time
        loop = asyncio.get_event_loop()
        agent_state: EcommerceAgentState = await loop.run_in_executor(
            None, run_ecommerce_agent, internal_request
        )

        # Extract fields from agent state
        order = agent_state.get("order")
        order_id = order.order_id if order else request.order_id
        final_response = agent_state.get("final_response", "")
        refund_eligible = agent_state.get("refund_eligible")
        refund_amount = None
        refund = agent_state.get("refund")
        if refund:
            refund_amount = refund.eligible_amount

        # Default currency (can be extended from order if needed)
        currency = "USD"

        # Build response
        response = EcommerceAgentHttpResponse(
            order_id=order_id,
            final_response=final_response,
            refund_eligible=refund_eligible,
            refund_amount=refund_amount,
            currency=currency,
            raw_state=None,  # Omit raw_state by default for cleaner API
            # Uncomment below for debugging:
            # raw_state={
            #     "agent_steps": [
            #         step.model_dump() if hasattr(step, "model_dump") else step
            #         for step in agent_state.get("agent_steps", [])
            #     ],
            #     "requires_manual_review": agent_state.get("requires_manual_review"),
            # },
        )

        logger.info(
            f"level=INFO endpoint=ecommerce_agent_run status=success "
            f"order_id={order_id} "
            f"refund_eligible={refund_eligible} "
            f"refund_amount={refund_amount}"
        )

        return response

    except HTTPException:
        # Re-raise HTTPExceptions (validation errors, etc.)
        raise

    except ValueError as ve:
        # Input validation errors from the agent
        logger.warning(
            f"level=WARN endpoint=ecommerce_agent_run status=VALIDATION_ERROR "
            f"error='{str(ve)}'",
            exc_info=True,
        )
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(ve)}",
        )

    except Exception as e:
        # Unexpected errors - log full traceback for debugging
        logger.exception(
            f"level=ERROR endpoint=ecommerce_agent_run status=ERROR "
            f"error_type={type(e).__name__} error='{str(e)}'"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please try again later.",
        )

