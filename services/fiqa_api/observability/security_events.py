"""
security_events.py - Security Event Logging Module
==================================================
Records all security-related events (input validation failures, tool blocks, 
narrative guardrail adjustments, etc.) for audit and monitoring.

This module provides a "security black box" that logs all guardrail actions
without impacting the main request flow. All logging is exception-safe.
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

# Use a dedicated logger for security events
logger = logging.getLogger("security")


def log_security_event(
    event_type: str,
    request_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a security-related event in structured format.
    
    This function is exception-safe: any logging failure will not impact
    the main request flow.
    
    Args:
        event_type: Type of security event, e.g.:
            - "input_validation_failed" - Input validation failed
            - "hard_blocked_request" - Request was hard-blocked
            - "tool_call_blocked" - Sensitive tool call was blocked
            - "narrative_guardrail_adjusted" - LLM narrative was adjusted for safety
        request_id: Optional request ID for tracing (should match main request)
        context: Optional dictionary with additional context:
            - service_name: Service name (mortgage_agent, ops_copilot)
            - stress_band: Stress band (for mortgage) or health_band (for ops)
            - reason: Reason for the event (e.g., validation error details)
            - tool: Tool name (for tool_call_blocked)
            - field: Field name (for input validation)
            - any other relevant fields
    
    Example:
        log_security_event(
            event_type="input_validation_failed",
            request_id="req_123",
            context={
                "service_name": "mortgage_agent",
                "field": "monthly_income",
                "reason": "monthly_income must be > 0",
            }
        )
    """
    try:
        # Build structured log entry
        log_data: Dict[str, Any] = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        if request_id:
            log_data["request_id"] = request_id
        
        if context:
            log_data.update(context)
        
        # Log as INFO level (security events are important enough for INFO)
        logger.info(
            f"event=security_event "
            f"event_type={event_type} "
            f"request_id={request_id or 'unknown'} "
            f"context={_format_context(context)}"
        )
        
        # Also log as structured JSON if logger supports it (for log aggregation)
        # This ensures compatibility with log aggregation systems
        if hasattr(logger, "info") and context:
            # Try to log as JSON-structured data for better parsing
            try:
                import json
                logger.info(f"[SECURITY] {json.dumps(log_data)}")
            except Exception:
                # If JSON serialization fails, fall back to string format
                pass
    
    except Exception as e:
        # Exception-safe: never let logging failures break the main flow
        # Log to a fallback logger (stderr) if available, but don't raise
        try:
            fallback_logger = logging.getLogger("security_fallback")
            fallback_logger.warning(f"[SECURITY_LOG_FAILED] Failed to log security event: {e}")
        except Exception:
            # Even fallback logging failed - silently continue
            pass


def _format_context(context: Optional[Dict[str, Any]]) -> str:
    """
    Format context dict as a compact string for logging.
    
    Args:
        context: Optional context dictionary
    
    Returns:
        Formatted string representation
    """
    if not context:
        return "{}"
    
    try:
        # Format as key=value pairs for grep-friendly logs
        parts = []
        for key, value in context.items():
            # Convert value to string, handle None
            if value is None:
                parts.append(f"{key}=null")
            elif isinstance(value, (str, int, float, bool)):
                # Simple types - use as-is
                parts.append(f"{key}={value}")
            else:
                # Complex types - use repr() but truncate
                str_value = repr(value)
                if len(str_value) > 100:
                    str_value = str_value[:97] + "..."
                parts.append(f"{key}={str_value}")
        
        return "{" + ", ".join(parts) + "}"
    except Exception:
        # If formatting fails, return simple representation
        return repr(context)


__all__ = ["log_security_event"]


