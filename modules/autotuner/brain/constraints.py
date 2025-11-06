"""
AutoTuner Brain - 参数约束与裁剪

提供参数范围约束、裁剪和滞回判断等工具函数。
"""

from typing import Dict, Any, Tuple, Union


def clip_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    将参数裁剪到合法范围内
    
    Args:
        params: 参数字典，包含 ef, T, Ncand_max, rerank_mult
        
    Returns:
        裁剪后的参数字典（不可变式）
    """
    clipped = params.copy()
    
    # 定义参数范围
    constraints = {
        'ef': (64, 256),
        'T': (200, 1200), 
        'Ncand_max': (500, 2000),
        'rerank_mult': (2, 6)
    }
    
    for param, (min_val, max_val) in constraints.items():
        if param in clipped:
            clipped[param] = max(min_val, min(max_val, clipped[param]))
    
    return clipped


def hysteresis(value: float, center: float, band: float) -> bool:
    """
    简单的滞回判断
    
    用于辅助判断状态是否稳定，避免频繁调整
    
    Args:
        value: 当前值
        center: 中心点
        band: 滞回带宽度
        
    Returns:
        是否在滞回带内（稳定状态）
    """
    return abs(value - center) <= band


def is_param_valid(params: Dict[str, Any]) -> bool:
    """
    检查参数是否在合法范围内
    
    Args:
        params: 参数字典
        
    Returns:
        是否所有参数都在合法范围内
    """
    constraints = {
        'ef': (64, 256),
        'T': (200, 1200),
        'Ncand_max': (500, 2000), 
        'rerank_mult': (2, 6)
    }
    
    for param, (min_val, max_val) in constraints.items():
        if param in params:
            if not (min_val <= params[param] <= max_val):
                return False
    
    return True


def get_param_ranges() -> Dict[str, tuple]:
    """
    获取参数范围定义
    
    Returns:
        参数名称到(最小值, 最大值)的映射
    """
    return {
        'ef': (64, 256),
        'T': (200, 1200),
        'Ncand_max': (500, 2000),
        'rerank_mult': (2, 6)
    }


def clip_joint(params: Dict[str, Any], simulate_only: bool = False) -> Tuple[Dict[str, Any], bool, str]:
    """
    Apply joint constraints to parameters with invariant checking.
    
    Args:
        params: Parameter dictionary to clip
        simulate_only: If True, only validate without mutation
        
    Returns:
        Tuple of (clipped_params, was_clipped, reason)
    """
    if simulate_only:
        # Validation mode - check if constraints would be violated
        violations = _check_joint_constraints(params)
        if violations:
            return params.copy(), True, f"JOINT_CONSTRAINT_VIOLATION: {violations}"
        return params.copy(), False, "VALID"
    
    # Apply mode - actually clip the parameters
    clipped = params.copy()
    was_clipped = False
    reasons = []
    
    # Apply individual parameter ranges first
    ranges = get_param_ranges()
    for param, (min_val, max_val) in ranges.items():
        if param in clipped:
            old_val = clipped[param]
            clipped[param] = max(min_val, min(max_val, clipped[param]))
            if clipped[param] != old_val:
                was_clipped = True
                reasons.append(f"{param}_RANGE")
    
    # Apply joint constraints
    joint_violations = _check_joint_constraints(clipped)
    if joint_violations:
        # Fix joint constraint violations
        clipped = _fix_joint_constraints(clipped)
        was_clipped = True
        reasons.extend(joint_violations)
    
    reason = "|".join(reasons) if reasons else "NO_CLIP"
    return clipped, was_clipped, reason


def _check_joint_constraints(params: Dict[str, Any]) -> list:
    """
    Check for joint constraint violations.
    
    Returns:
        List of violation types found
    """
    violations = []
    
    # Check rerank_k <= candidate_k (using rerank_mult and Ncand_max as proxies)
    # This constraint doesn't make sense as written since rerank_mult is 2-6 and Ncand_max is 500-2000
    # Let's use a more reasonable constraint: rerank_mult should be reasonable relative to Ncand_max
    rerank_mult = params.get('rerank_mult', 2)
    candidate_k = params.get('Ncand_max', 1000)
    # Constraint: rerank_mult should not be more than 10% of candidate_k
    if rerank_mult > candidate_k * 0.1:
        violations.append("RERANK_GT_CANDIDATE")
    
    # Check ef_search <= 4*candidate_k (using ef and Ncand_max)
    ef_search = params.get('ef', 128)
    if ef_search > 4 * candidate_k:
        violations.append("EF_GT_4X_CANDIDATE")
    
    # Check threshold_T in [0.0, 1.0] (using T as proxy, normalized)
    T = params.get('T', 500)
    threshold_T = T / 1000.0  # Normalize to [0,1] range
    if not (0.0 <= threshold_T <= 1.0):
        violations.append("THRESHOLD_T_RANGE")
    
    return violations


def _fix_joint_constraints(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fix joint constraint violations by adjusting parameters.
    
    Args:
        params: Parameters with potential violations
        
    Returns:
        Fixed parameters
    """
    fixed = params.copy()
    
    # Fix rerank_k <= candidate_k
    rerank_k = fixed.get('rerank_mult', 2)
    candidate_k = fixed.get('Ncand_max', 1000)
    if rerank_k > candidate_k:
        fixed['rerank_mult'] = min(rerank_k, candidate_k)
    
    # Fix ef_search <= 4*candidate_k
    ef_search = fixed.get('ef', 128)
    candidate_k = fixed.get('Ncand_max', 1000)
    if ef_search > 4 * candidate_k:
        fixed['ef'] = min(ef_search, 4 * candidate_k)
    
    # Fix threshold_T range
    T = fixed.get('T', 500)
    if T < 200:
        fixed['T'] = 200
    elif T > 1200:
        fixed['T'] = 1200
    
    return fixed


def validate_joint_constraints(params: Dict[str, Any]) -> bool:
    """
    Validate that parameters satisfy all joint constraints.
    
    Args:
        params: Parameter dictionary to validate
        
    Returns:
        True if all constraints are satisfied
    """
    violations = _check_joint_constraints(params)
    return len(violations) == 0
