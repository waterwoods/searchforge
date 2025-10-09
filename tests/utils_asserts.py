"""
Test assertion utilities for AutoTuner Brain

Provides helper functions for common test assertions.
"""

from typing import Dict, Any


def assert_single_knob_change(prev_params: Dict[str, Any], next_params: Dict[str, Any]) -> None:
    """
    Assert that only one parameter knob changed between prev and next.
    
    Args:
        prev_params: Previous parameter state
        next_params: Next parameter state
        
    Raises:
        AssertionError: If more than one knob changed
    """
    changes = []
    all_keys = set(prev_params.keys()) | set(next_params.keys())
    
    for key in all_keys:
        prev_val = prev_params.get(key, 0)
        next_val = next_params.get(key, 0)
        if prev_val != next_val:
            changes.append((key, prev_val, next_val))
    
    assert len(changes) <= 1, f"Expected at most 1 knob change, got {len(changes)}: {changes}"


def assert_within_band(value: float, lo: float, hi: float) -> None:
    """
    Assert that a value is within the specified band [lo, hi].
    
    Args:
        value: Value to check
        lo: Lower bound (inclusive)
        hi: Upper bound (inclusive)
        
    Raises:
        AssertionError: If value is outside the band
    """
    assert lo <= value <= hi, f"Value {value} not in band [{lo}, {hi}]"


def assert_param_in_range(params: Dict[str, Any], param_name: str, min_val: int, max_val: int) -> None:
    """
    Assert that a parameter is within its valid range.
    
    Args:
        params: Parameter dictionary
        param_name: Name of parameter to check
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Raises:
        AssertionError: If parameter is outside range
    """
    value = params.get(param_name)
    assert value is not None, f"Parameter {param_name} not found in params"
    assert min_val <= value <= max_val, f"Parameter {param_name}={value} not in range [{min_val}, {max_val}]"


def assert_all_params_valid(params: Dict[str, Any]) -> None:
    """
    Assert that all parameters are within their valid ranges.
    
    Args:
        params: Parameter dictionary
        
    Raises:
        AssertionError: If any parameter is invalid
    """
    ranges = {
        'ef': (64, 256),
        'T': (200, 1200),
        'Ncand_max': (500, 2000),
        'rerank_mult': (2, 6)
    }
    
    for param_name, (min_val, max_val) in ranges.items():
        if param_name in params:
            assert_param_in_range(params, param_name, min_val, max_val)


def assert_action_properties(action, expected_kind: str = None, 
                           expected_step_range: tuple = None, 
                           expected_reason_contains: str = None) -> None:
    """
    Assert properties of an Action object.
    
    Args:
        action: Action object to validate
        expected_kind: Expected action kind
        expected_step_range: Expected step range (min, max)
        expected_reason_contains: Expected substring in reason
        
    Raises:
        AssertionError: If any assertion fails
    """
    assert action is not None, "Action should not be None"
    
    if expected_kind:
        assert action.kind == expected_kind, f"Expected kind {expected_kind}, got {action.kind}"
    
    if expected_step_range:
        min_step, max_step = expected_step_range
        assert min_step <= action.step <= max_step, f"Step {action.step} not in range [{min_step}, {max_step}]"
    
    if expected_reason_contains:
        assert expected_reason_contains in action.reason, f"Reason '{action.reason}' should contain '{expected_reason_contains}'"


def assert_step_growth(old_step: float, new_step: float, max_growth_factor: float = 3.0) -> None:
    """
    Assert that step growth is within reasonable bounds.
    
    Args:
        old_step: Previous step size
        new_step: New step size
        max_growth_factor: Maximum allowed growth factor
        
    Raises:
        AssertionError: If growth exceeds bounds
    """
    if old_step == 0:
        return  # Can't compute growth from zero
    
    growth_factor = abs(new_step / old_step)
    assert growth_factor <= max_growth_factor, f"Step growth factor {growth_factor} exceeds max {max_growth_factor}"


def assert_step_decay(old_step: float, new_step: float, min_decay_factor: float = 0.33) -> None:
    """
    Assert that step decay is within reasonable bounds.
    
    Args:
        old_step: Previous step size
        new_step: New step size
        min_decay_factor: Minimum allowed decay factor
        
    Raises:
        AssertionError: If decay exceeds bounds
    """
    if old_step == 0:
        return  # Can't compute decay from zero
    
    decay_factor = abs(new_step / old_step)
    assert decay_factor >= min_decay_factor, f"Step decay factor {decay_factor} below min {min_decay_factor}"


def assert_params_invariants(params: Dict[str, Any]) -> None:
    """
    Assert that parameters satisfy all joint constraints and invariants.
    
    Args:
        params: Parameter dictionary to validate
        
    Raises:
        AssertionError: If any invariant is violated
    """
    # Check individual parameter ranges
    assert_all_params_valid(params)
    
    # Check joint constraints
    rerank_k = params.get('rerank_mult', 2)
    candidate_k = params.get('Ncand_max', 1000)
    assert rerank_k <= candidate_k, f"rerank_k ({rerank_k}) > candidate_k ({candidate_k})"
    
    ef_search = params.get('ef', 128)
    assert ef_search <= 4 * candidate_k, f"ef_search ({ef_search}) > 4*candidate_k ({4 * candidate_k})"
    
    T = params.get('T', 500)
    threshold_T = T / 1000.0
    assert 0.0 <= threshold_T <= 1.0, f"threshold_T ({threshold_T}) not in [0.0, 1.0]"


def assert_updates_direction(updates: Dict[str, Any], expected_direction: str) -> None:
    """
    Assert that updates move in the expected direction.
    
    Args:
        updates: Update dictionary
        expected_direction: "latency_drop" or "recall_gain"
        
    Raises:
        AssertionError: If direction doesn't match expectation
    """
    if expected_direction == "latency_drop":
        # Should decrease ef_search and candidate_k, increase threshold_T
        assert updates.get('ef_search', 0) <= 0, "latency_drop should decrease ef_search"
        assert updates.get('candidate_k', 0) <= 0, "latency_drop should decrease candidate_k"
        assert updates.get('threshold_T', 0) >= 0, "latency_drop should increase threshold_T"
    elif expected_direction == "recall_gain":
        # Should increase ef_search and rerank_k, decrease threshold_T
        assert updates.get('ef_search', 0) >= 0, "recall_gain should increase ef_search"
        assert updates.get('rerank_k', 0) >= 0, "recall_gain should increase rerank_k"
        assert updates.get('threshold_T', 0) <= 0, "recall_gain should decrease threshold_T"


def assert_single_knob_change(prev_params: Dict[str, Any], next_params: Dict[str, Any]) -> None:
    """
    Assert that only one parameter knob changed between prev and next.
    
    Args:
        prev_params: Previous parameter state
        next_params: Next parameter state
        
    Raises:
        AssertionError: If more than one knob changed
    """
    changes = []
    all_keys = set(prev_params.keys()) | set(next_params.keys())
    
    for key in all_keys:
        prev_val = prev_params.get(key, 0)
        next_val = next_params.get(key, 0)
        if prev_val != next_val:
            changes.append((key, prev_val, next_val))
    
    assert len(changes) <= 1, f"Expected at most 1 knob change, got {len(changes)}: {changes}"
