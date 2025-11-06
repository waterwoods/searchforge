"""
AutoTuner Brain - 核心决策逻辑

实现纯函数的调优决策逻辑，基于性能指标和约束条件决定调优动作。
"""

from .contracts import TuningInput, Action, SLO, Guards
from .hook import pre_decide_with_memory
from .memory import get_memory


def decide_tuning_action(inp: TuningInput) -> Action:
    """
    基于输入决定调优动作
    
    实现最小规则集的决策逻辑，包含记忆钩子和抗震荡机制：
    0. 记忆钩子：优先使用历史甜点
    1. 守护：冷却期 -> noop
    2. 滞回带：小误差 -> noop
    3. 冷却时间：重复动作且间隔短 -> noop
    4. 延迟超标且召回有冗余 -> 降ef或降ncand
    5. 召回不达标且延迟有余量 -> 升ef或升rerank
    6. 临界区优化 -> 升T
    7. 其他情况 -> noop
    
    Args:
        inp: 调优输入数据
        
    Returns:
        调优动作
    """
    # 0. 记忆钩子：优先使用历史甜点
    mem = get_memory()
    memory_action = pre_decide_with_memory(inp, mem)
    if memory_action is not None:
        return memory_action
    
    # 1. 守护：冷却期直接返回noop
    if inp.guards.cooldown:
        return Action(
            kind="noop",
            step=0.0,
            reason="cooldown"
        )
    
    # 2. 滞回带：误差足够小时不再调整
    if (abs(inp.p95_ms - inp.slo.p95_ms) < 100 and 
        abs(inp.recall_at10 - inp.slo.recall_at10) < 0.02):
        return Action(
            kind="noop",
            step=0.0,
            reason="within_hysteresis_band"
        )
    
    # 3. 延迟超标且召回有冗余：优先降ef，否则降ncand
    if (inp.p95_ms > inp.slo.p95_ms and 
        inp.recall_at10 >= inp.slo.recall_at10 + 0.05):
        
        # 优先降ef
        if inp.params.get('ef', 128) > 64:  # 确保不会降到最小值以下
            action_kind = "drop_ef"
            base_step = -32.0
            reason = "high_latency_with_recall_redundancy"
        else:
            # ef已经是最小值，降ncand
            action_kind = "drop_ncand"
            base_step = -200.0
            reason = "high_latency_ef_at_min_drop_ncand"
        
        # 应用抗震荡机制
        final_action = _apply_anti_oscillation_logic(inp, action_kind, base_step, reason)
        if final_action:
            return final_action
    
    # 4. 召回不达标且延迟有余量：优先升ef，否则升rerank
    if (inp.recall_at10 < inp.slo.recall_at10 and 
        inp.p95_ms <= inp.slo.p95_ms - 100):
        
        # 优先升ef
        if inp.params.get('ef', 128) < 256:  # 确保不会超过最大值
            action_kind = "bump_ef"
            base_step = 32.0
            reason = "low_recall_with_latency_margin"
        else:
            # ef已经是最大值，升rerank
            action_kind = "bump_rerank"
            base_step = 1.0
            reason = "low_recall_ef_at_max_bump_rerank"
        
        # 应用抗震荡机制
        final_action = _apply_anti_oscillation_logic(inp, action_kind, base_step, reason)
        if final_action:
            return final_action
    
    # 5. 临界区优化：near_T且持续超标且稳定
    if (inp.near_T and 
        inp.p95_ms > inp.slo.p95_ms and 
        inp.guards.stable):
        
        action_kind = "bump_T"
        base_step = 100.0
        reason = "near_T_boundary_optimization"
        
        # 应用抗震荡机制
        final_action = _apply_anti_oscillation_logic(inp, action_kind, base_step, reason)
        if final_action:
            return final_action
    
    # 6. 其他情况：在SLO范围内或不确定状态
    return Action(
        kind="noop",
        step=0.0,
        reason="within_slo_or_uncertain"
    )


def _apply_anti_oscillation_logic(inp: TuningInput, action_kind: str, base_step: float, reason: str) -> Action:
    """
    应用抗震荡机制
    
    Args:
        inp: 调优输入数据
        action_kind: 动作类型
        base_step: 基础步长
        reason: 原因
        
    Returns:
        应用抗震荡机制后的动作，如果被阻止则返回 None
    """
    # 3. 冷却时间：若上一轮执行了相同动作且间隔 < 10 秒，则跳过本次
    if (inp.last_action and 
        inp.last_action.kind == action_kind and 
        inp.last_action.age_sec < 10):
        return Action(
            kind="noop",
            step=0.0,
            reason="cooldown_active"
        )
    
    # 4. 自适应步长：若连续两次在同方向调整，则步长减半
    step = base_step
    if inp.adjustment_count >= 2:
        step *= 0.5
    
    return Action(
        kind=action_kind,
        step=step,
        reason=reason
    )


def analyze_tuning_input(inp: TuningInput) -> dict:
    """
    分析调优输入，返回诊断信息（用于调试和测试）
    
    Args:
        inp: 调优输入数据
        
    Returns:
        包含分析结果的字典
    """
    analysis = {
        'latency_violation': inp.p95_ms > inp.slo.p95_ms,
        'recall_violation': inp.recall_at10 < inp.slo.recall_at10,
        'recall_redundancy': inp.recall_at10 >= inp.slo.recall_at10 + 0.05,
        'latency_margin': inp.p95_ms <= inp.slo.p95_ms - 100,
        'cooldown_active': inp.guards.cooldown,
        'stable_state': inp.guards.stable,
        'near_boundary': inp.near_T,
        'ef_at_min': inp.params.get('ef', 128) <= 64,
        'ef_at_max': inp.params.get('ef', 128) >= 256,
    }
    
    return analysis
