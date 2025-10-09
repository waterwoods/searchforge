"""
AutoTuner Brain - 纯函数决策引擎

提供可单测、可扩展的 AutoTuner 大脑最小版：
- 纯函数决策逻辑
- 参数约束与应用
- 小样本回归验证
- 完整的单元测试覆盖
"""

from .contracts import TuningInput, Action, SLO, Guards
from .decider import decide_tuning_action
from .constraints import clip_params, hysteresis
from .apply import apply_action

__all__ = [
    'TuningInput',
    'Action', 
    'SLO',
    'Guards',
    'decide_tuning_action',
    'clip_params',
    'hysteresis',
    'apply_action'
]
