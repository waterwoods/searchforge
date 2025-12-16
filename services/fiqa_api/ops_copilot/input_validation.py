"""
input_validation.py - Ops Copilot Input Validation
===================================================
Hard error validation for system snapshot inputs.

This module performs "hard error" validation - it checks for clearly invalid
system metrics (negative values, out-of-range percentages, etc.) that would
cause errors in downstream calculations.
"""

from typing import List
from services.fiqa_api.ops_copilot.schemas import SystemSnapshot


def validate_system_snapshot(snapshot: SystemSnapshot) -> List[str]:
    """
    Validate system snapshot inputs and return a list of error messages.
    
    Returns an empty list if all inputs are valid. If the list is non-empty,
    the request should be rejected with a 400 Bad Request.
    
    This function performs "hard error" validation only:
    - Checks for negative values where they're not allowed
    - Checks for out-of-range percentages (0-100%)
    - Checks for out-of-range error rates (0-1)
    - Does NOT check for "extreme but valid" values (those are handled by health check rules)
    
    Args:
        snapshot: SystemSnapshot instance to validate
    
    Returns:
        List of error message strings (empty if valid)
    
    Example:
        errors = validate_system_snapshot(snapshot)
        if errors:
            # Reject request with 400
            raise HTTPException(status_code=400, detail={"errors": errors})
    """
    errors: List[str] = []
    
    # 1. CPU percentage must be in range 0-100
    if snapshot.cpu_pct < 0:
        errors.append("cpu_pct cannot be negative")
    elif snapshot.cpu_pct > 100:
        errors.append("cpu_pct cannot exceed 100%")
    
    # 2. Memory percentage must be in range 0-100
    if snapshot.mem_pct < 0:
        errors.append("mem_pct cannot be negative")
    elif snapshot.mem_pct > 100:
        errors.append("mem_pct cannot exceed 100%")
    
    # 3. Disk percentage must be in range 0-100
    if snapshot.disk_pct < 0:
        errors.append("disk_pct cannot be negative")
    elif snapshot.disk_pct > 100:
        errors.append("disk_pct cannot exceed 100%")
    
    # 4. P95 latency must be non-negative
    if snapshot.p95_latency_ms < 0:
        errors.append("p95_latency_ms cannot be negative")
    
    # 5. Error rate must be in range 0-1
    if snapshot.error_rate < 0:
        errors.append("error_rate cannot be negative")
    elif snapshot.error_rate > 1.0:
        errors.append("error_rate cannot exceed 1.0 (100%)")
    
    # 6. QPS must be non-negative
    if snapshot.qps < 0:
        errors.append("qps cannot be negative")
    
    # 7. Service name must be non-empty
    if not snapshot.service_name or not snapshot.service_name.strip():
        errors.append("service_name cannot be empty")
    
    # 8. Environment must be one of the allowed values
    if snapshot.environment not in ("prod", "staging", "dev"):
        errors.append(f"environment must be one of: prod, staging, dev (got: {snapshot.environment})")
    
    return errors


__all__ = ["validate_system_snapshot"]


