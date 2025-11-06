"""
AutoTuner Brain - 记忆钩子

实现记忆驱动的决策钩子，在常规决策前尝试使用历史甜点
"""

import os
import json
import time
from typing import Optional

from .contracts import TuningInput, Action, SweetSpot
from .memory import Memory


def pre_decide_with_memory(inp: TuningInput, mem: Memory) -> Optional[Action]:
    """
    记忆驱动的预决策钩子
    
    若存在有效的甜点记忆，返回小步靠拢动作
    
    Args:
        inp: 调优输入数据
        mem: 记忆实例
        
    Returns:
        记忆驱动的动作，如果没有有效记忆则返回None
    """
    # 检查记忆功能是否启用
    if not _is_memory_enabled():
        return None
    
    # 计算流量桶ID
    bucket_id = mem.default_bucket_of(inp)
    
    # 查询甜点
    sweet_spot = mem.query(bucket_id)
    if not sweet_spot or not sweet_spot.meets_slo:
        return None
    
    # 检查当前ef是否接近甜点ef
    current_ef = inp.params.get('ef', 128)
    sweet_ef = sweet_spot.ef
    
    # 定义最小步长
    step_min = 16  # 比常规步长32更小的步长
    
    # 如果差距足够大，执行小步靠拢
    if abs(current_ef - sweet_ef) > step_min:
        # 计算靠拢方向和步长
        if current_ef < sweet_ef:
            # 当前ef较小，需要增加
            step = step_min
            action_kind = "bump_ef"
        else:
            # 当前ef较大，需要减少
            step = -step_min
            action_kind = "drop_ef"
        
        # 记录记忆命中事件
        age_s = time.time() - (time.time() - sweet_spot.age_s)
        _log_event(
            "MEMORY_LOOKUP",
            bucket=bucket_id,
            matched=True,
            sweet_ef=sweet_ef,
            age_s=round(age_s, 1)
        )
        
        return Action(
            kind=action_kind,
            step=step,
            reason="follow_memory"
        )
    else:
        # 已经接近甜点，不需要调整
        age_s = time.time() - (time.time() - sweet_spot.age_s)
        _log_event(
            "MEMORY_LOOKUP", 
            bucket=bucket_id,
            matched=True,
            sweet_ef=sweet_ef,
            age_s=round(age_s, 1),
            note="already_at_sweet_spot"
        )
        
        return Action(
            kind="noop",
            step=0.0,
            reason="at_sweet_spot"
        )


def _is_memory_enabled() -> bool:
    """检查记忆功能是否启用"""
    return os.environ.get('MEMORY_ENABLED', '1') == '1'


def _log_event(event_type: str, **kwargs):
    """打印JSON格式的事件日志"""
    log_entry = {"event": event_type, "timestamp": time.time()}
    log_entry.update(kwargs)
    print(json.dumps(log_entry, separators=(',', ':')))

