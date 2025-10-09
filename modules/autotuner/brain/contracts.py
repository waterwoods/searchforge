"""
AutoTuner Brain - 数据模型与类型契约

定义核心的数据结构和类型契约，确保类型安全和清晰的接口。
"""

from typing import Dict, Any, Literal, Optional, Union
from dataclasses import dataclass
import time


@dataclass
class SLO:
    """服务级别目标 (Service Level Objectives)"""
    p95_ms: float
    recall_at10: float


@dataclass
class Guards:
    """守护条件，用于控制调优行为"""
    cooldown: bool  # 是否在冷却期
    stable: bool    # 状态是否稳定


@dataclass
class TuningInput:
    """
    调优输入数据
    
    包含当前性能指标、参数配置、SLO目标和守护条件
    """
    # 性能指标
    p95_ms: float
    recall_at10: float
    qps: float
    
    # 当前参数配置（至少包含以下参数）
    params: Dict[str, Any]  # 包含: ef, T, Ncand_max, rerank_mult
    
    # 服务级别目标
    slo: SLO
    
    # 守护条件
    guards: Guards
    
    # 候选数是否接近T的边界（由外部计算）
    near_T: bool
    
    # 抗震荡机制相关字段
    last_action: Optional['Action'] = None  # 上一轮的动作
    adjustment_count: int = 0  # 连续同方向调整次数


ActionKind = Literal[
    "noop",
    "bump_ef", "drop_ef",
    "bump_T", "drop_T", 
    "bump_rerank", "drop_rerank",
    "bump_ncand", "drop_ncand",
    "rollback",
    "multi_knob"  # New multi-knob action type
]


@dataclass
class Action:
    """
    调优动作
    
    包含动作类型、调整幅度和可解释的原因
    支持单参数和多参数调整模式
    """
    kind: ActionKind
    step: float  # 调整幅度，正负皆可（单参数模式）
    reason: str  # 可读的解释说明
    age_sec: float = 0.0  # 动作年龄（秒），用于冷却判断
    
    # Multi-knob support (new fields)
    updates: Optional[Dict[str, Union[int, float]]] = None  # 多参数更新字典
    mode: Literal["sequential", "atomic"] = "sequential"  # 应用模式


@dataclass
class MemorySample:
    """
    记忆样本
    
    用于存储观测到的性能数据点
    """
    bucket_id: str
    ef: int
    T: int
    Ncand_max: int
    p95_ms: float
    recall_at10: float
    ts: float  # 时间戳


@dataclass
class SweetSpot:
    """
    甜点
    
    存储某个流量桶的最优参数配置
    """
    ef: int
    T: int
    meets_slo: bool  # 是否满足SLO
    age_s: float  # 甜点年龄（秒）
    ewma_p95: float  # EWMA延迟
    ewma_recall: float  # EWMA召回


@dataclass
class MultiKnobResult:
    """
    多参数调整结果
    
    包含应用结果、回滚信息和统计
    """
    status: Literal["applied", "rejected", "rolled_back"]
    params_before: Dict[str, Any]
    params_after: Dict[str, Any]
    updates_applied: Dict[str, Union[int, float]]
    clipped: bool = False
    clipped_reason: str = ""
    rollback_snapshot: Optional[Dict[str, Any]] = None
    rejection_reason: str = ""
