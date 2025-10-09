"""
AutoTuner Brain - 动作应用器

将调优动作应用到参数配置，返回新的参数集。
"""

from typing import Dict, Any, Optional
from .contracts import Action, MultiKnobResult
from .constraints import clip_params, clip_joint
from .autotuner_config import ENABLE_ATOMIC, ENABLE_ROLLBACK

# Global counters for statistics
_apply_counters = {
    "clipped_count": 0,
    "rejected_by_joint": 0,
    "rollback_count": 0,
    "decide_total": 0,
    "ef_search_updates": 0,
    "candidate_k_updates": 0,
    "rerank_k_updates": 0,
    "threshold_T_updates": 0
}

def get_apply_counters() -> Dict[str, int]:
    """Get current apply statistics."""
    return _apply_counters.copy()

def reset_apply_counters():
    """Reset apply statistics."""
    global _apply_counters
    _apply_counters = {
        "clipped_count": 0,
        "rejected_by_joint": 0,
        "rollback_count": 0,
        "decide_total": 0,
        "ef_search_updates": 0,
        "candidate_k_updates": 0,
        "rerank_k_updates": 0,
        "threshold_T_updates": 0
    }


def _make_feasible_updates(current_params: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make updates feasible through progressive shrinking.
    
    Priority: reduce rerank_k delta, then ef delta, then ease candidate_k delta magnitude.
    """
    from .constraints import clip_joint, get_param_ranges
    
    feasible_updates = updates.copy()
    
    # Test initial feasibility
    test_params = current_params.copy()
    for key, value in feasible_updates.items():
        if key in test_params:
            test_params[key] = test_params[key] + value
        else:
            test_params[key] = value
    
    clipped_params, was_clipped, reason = clip_joint(test_params, simulate_only=True)
    if not was_clipped:
        return feasible_updates
    
    # Progressive shrinking with priority order
    shrink_attempts = [
        # Priority 1: reduce rerank_k delta
        lambda u: {k: v * 0.5 if k == "rerank_mult" else v for k, v in u.items()},
        # Priority 2: reduce ef delta  
        lambda u: {k: v * 0.5 if k == "ef" else v for k, v in u.items()},
        # Priority 3: ease candidate_k delta magnitude
        lambda u: {k: v * 0.5 if k == "Ncand_max" else v for k, v in u.items()},
        # Priority 4: reduce threshold_T delta
        lambda u: {k: v * 0.5 if k == "T" else v for k, v in u.items()},
    ]
    
    for shrink_func in shrink_attempts:
        feasible_updates = shrink_func(feasible_updates)
        
        # Test feasibility
        test_params = current_params.copy()
        for key, value in feasible_updates.items():
            if key in test_params:
                test_params[key] = test_params[key] + value
            else:
                test_params[key] = value
        
        clipped_params, was_clipped, reason = clip_joint(test_params, simulate_only=True)
        if not was_clipped:
            return feasible_updates
    
    # If still infeasible, return empty dict (will trigger single-knob downgrade)
    return {}


def _track_per_knob_updates(updates: Dict[str, Any]):
    """Track per-knob update counts."""
    for key, value in updates.items():
        if key == "ef_search" or key == "ef":
            _apply_counters["ef_search_updates"] += 1
        elif key == "candidate_k" or key == "Ncand_max":
            _apply_counters["candidate_k_updates"] += 1
        elif key == "rerank_k" or key == "rerank_mult":
            _apply_counters["rerank_k_updates"] += 1
        elif key == "threshold_T" or key == "T":
            _apply_counters["threshold_T_updates"] += 1


def apply_action(params: Dict[str, Any], action: Action) -> Dict[str, Any]:
    """
    将调优动作应用到参数配置
    
    Args:
        params: 当前参数字典
        action: 调优动作
        
    Returns:
        应用动作后的新参数字典（不可变式）
    """
    # Handle multi-knob actions
    if action.kind == "multi_knob" and action.updates:
        result = apply_updates(params, action.updates, action.mode)
        return result.params_after
    
    # Legacy single-knob actions
    new_params = params.copy()
    
    # 根据动作类型应用相应的参数调整
    if action.kind == "bump_ef":
        new_params["ef"] = new_params.get("ef", 128) + int(action.step)
        
    elif action.kind == "drop_ef":
        new_params["ef"] = new_params.get("ef", 128) + int(action.step)
        
    elif action.kind == "bump_T":
        new_params["T"] = new_params.get("T", 500) + int(action.step)
        
    elif action.kind == "drop_T":
        new_params["T"] = new_params.get("T", 500) + int(action.step)
        
    elif action.kind == "bump_rerank":
        new_params["rerank_mult"] = new_params.get("rerank_mult", 2) + int(action.step)
        
    elif action.kind == "drop_rerank":
        new_params["rerank_mult"] = new_params.get("rerank_mult", 2) + int(action.step)
        
    elif action.kind == "bump_ncand":
        new_params["Ncand_max"] = new_params.get("Ncand_max", 1000) + int(action.step)
        
    elif action.kind == "drop_ncand":
        new_params["Ncand_max"] = new_params.get("Ncand_max", 1000) + int(action.step)
        
    elif action.kind == "rollback":
        # 本版本 rollback 等同于 noop，保留接口
        pass
        
    # noop 不需要任何调整
    
    # 应用参数约束，确保所有参数都在合法范围内
    clipped_params = clip_params(new_params)
    
    return clipped_params


def compute_parameter_delta(old_params: Dict[str, Any], new_params: Dict[str, Any]) -> Dict[str, int]:
    """
    计算参数变化量
    
    Args:
        old_params: 原始参数
        new_params: 新参数
        
    Returns:
        参数变化量字典
    """
    delta = {}
    for key in set(old_params.keys()) | set(new_params.keys()):
        old_val = old_params.get(key, 0)
        new_val = new_params.get(key, 0)
        delta[key] = new_val - old_val
    
    return delta


def apply_updates(current_params: Dict[str, Any], updates: Dict[str, Any], mode: str, 
                   simulate_failure: bool = False) -> MultiKnobResult:
    """
    Apply multi-knob updates with sequential or atomic mode.
    
    Args:
        current_params: Current parameter state
        updates: Dictionary of parameter updates to apply
        mode: "sequential" or "atomic" application mode
        simulate_failure: If True, simulate downstream failure for rollback testing
        
    Returns:
        MultiKnobResult with application status and details
    """
    # Increment decide_total counter
    _apply_counters["decide_total"] += 1
    
    params_before = current_params.copy()
    
    # ⚠️ Feature Freeze: Atomic mode is disabled, force sequential mode
    if not ENABLE_ATOMIC and mode == "atomic":
        mode = "sequential"
    
    if mode == "sequential":
        # Sequential mode: feasibility pre-projection with progressive shrinking
        feasible_updates = _make_feasible_updates(current_params, updates)
        
        if not feasible_updates:
            # Downgrade to single-knob update (keep first key only)
            if updates:
                first_key = list(updates.keys())[0]
                feasible_updates = {first_key: updates[first_key]}
            else:
                return MultiKnobResult(
                    status="rejected",
                    params_before=params_before,
                    params_after=params_before,
                    updates_applied={},
                    rejection_reason="NO_FEASIBLE_UPDATES"
                )
        
        # Apply feasible updates
        new_params = current_params.copy()
        for key, value in feasible_updates.items():
            if key in new_params:
                new_params[key] = new_params[key] + value
            else:
                new_params[key] = value
        
        # Final validation
        clipped_params, was_clipped, reason = clip_joint(new_params, simulate_only=True)
        if was_clipped:
            _apply_counters["rejected_by_joint"] += 1
            return MultiKnobResult(
                status="rejected",
                params_before=params_before,
                params_after=params_before,
                updates_applied={},
                rejection_reason=f"JOINT_CONSTRAINT: {reason}"
            )
        
        # Track per-knob updates
        _track_per_knob_updates(feasible_updates)
        
        return MultiKnobResult(
            status="applied",
            params_before=params_before,
            params_after=new_params,
            updates_applied=feasible_updates.copy()
        )
    
    elif mode == "atomic":
        # ⚠️ Feature Freeze: Atomic mode should be disabled via config
        # This code path is kept for future re-enablement but should not be reached
        if not ENABLE_ATOMIC:
            # Fallback to sequential mode
            return apply_updates(current_params, updates, "sequential", simulate_failure)
        
        # Atomic mode: merge updates, apply joint constraints, handle rollback
        new_params = current_params.copy()
        
        # Apply all updates
        for key, value in updates.items():
            if key in new_params:
                new_params[key] = new_params[key] + value
            else:
                new_params[key] = value
        
        # ⚠️ Feature Freeze: Rollback is disabled, skip snapshot creation
        rollback_snapshot = current_params.copy() if ENABLE_ROLLBACK else None
        
        # Apply joint constraints
        clipped_params, was_clipped, reason = clip_joint(new_params, simulate_only=False)
        
        if was_clipped:
            _apply_counters["clipped_count"] += 1
        
        # ⚠️ Feature Freeze: Rollback is disabled, skip rollback simulation
        if simulate_failure and ENABLE_ROLLBACK:
            _apply_counters["rollback_count"] += 1
            return MultiKnobResult(
                status="rolled_back",
                params_before=params_before,
                params_after=rollback_snapshot,
                updates_applied=updates.copy(),
                clipped=was_clipped,
                clipped_reason=reason,
                rollback_snapshot=rollback_snapshot
            )
        elif simulate_failure and not ENABLE_ROLLBACK:
            # Rollback disabled: reject instead of rollback
            return MultiKnobResult(
                status="rejected",
                params_before=params_before,
                params_after=params_before,
                updates_applied={},
                rejection_reason="ROLLBACK_DISABLED_SIMULATED_FAILURE"
            )
        
        # Track per-knob updates
        _track_per_knob_updates(updates)
        
        return MultiKnobResult(
            status="applied",
            params_before=params_before,
            params_after=clipped_params,
            updates_applied=updates.copy(),
            clipped=was_clipped,
            clipped_reason=reason,
            rollback_snapshot=rollback_snapshot
        )
    
    else:
        raise ValueError(f"Unknown mode: {mode}")


def validate_action_application(params: Dict[str, Any], action: Action) -> bool:
    """
    验证动作应用是否会产生有效的参数配置
    
    Args:
        params: 当前参数
        action: 调优动作
        
    Returns:
        动作应用是否有效
    """
    try:
        new_params = apply_action(params, action)
        # 检查新参数是否在合法范围内
        from .constraints import is_param_valid
        return is_param_valid(new_params)
    except Exception:
        return False
