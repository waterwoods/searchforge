"""
AutoTuner Brain - 配置与功能开关

定义 AutoTuner 的功能开关标志，用于轻量级功能冰封。
保留核心路径（顺序决策 + 预投影 + 冷却/滞回），安全屏蔽非关键功能。
"""

import os

# ============================================================================
# 功能开关标志 (Feature Freeze Flags)
# ============================================================================

# 原子应用模式：多参数同时应用，失败则全部回滚
# 禁用后：仅使用顺序模式（sequential），逐参数应用并进行预投影验证
ENABLE_ATOMIC = False

# 回滚机制：参数应用失败后自动恢复到快照状态
# 禁用后：不创建回滚快照，失败时直接拒绝更新
ENABLE_ROLLBACK = False

# Bandit 算法：基于多臂老虎机的探索-利用策略
# 通过环境变量控制（默认关闭，确保基线稳定）
ENABLE_BANDIT = bool(int(os.getenv("ENABLE_BANDIT", "0")))

# 复杂步长调整：基于连续改进/回退的自适应步长
# 禁用后：使用固定步长，不进行动态缩放
ENABLE_COMPLEX_STEP = False

# Redis 持久化：将记忆数据持久化到 Redis
# 禁用后：仅使用内存缓存，不进行外部持久化
ENABLE_REDIS = False

# 持久化到文件系统
# 禁用后：不写入磁盘，仅内存驻留
ENABLE_PERSISTENCE = False


# ============================================================================
# 核心参数配置 (Core Parameters)
# ============================================================================

# 参数范围
PARAM_RANGES = {
    'ef': (32, 256),           # HNSW ef_search 范围
    'T': (200, 1000),          # 候选数阈值
    'Ncand_max': (400, 2000),  # 最大候选数
    'rerank_mult': (1, 5)      # 重排序倍数
}

# 冷却参数
COOLDOWN_TICKS = 2            # 冷却周期（决策轮次）
COOLDOWN_MIN_SEC = 10         # 最小冷却时间（秒）

# 滞回带参数
HYSTERESIS_P95_MS = 100       # P95 延迟滞回带（毫秒）
HYSTERESIS_RECALL = 0.02      # Recall 滞回带

# 记忆系统参数
MEMORY_RING_SIZE = 100        # 环形缓冲区大小
MEMORY_ALPHA = 0.2            # EWMA 平滑系数
MEMORY_TTL_SEC = 900          # 甜点过期时间（秒）= 15分钟


# ============================================================================
# 冻结功能说明 (Freeze Summary)
# ============================================================================

FREEZE_SUMMARY = """
AutoTuner 功能冰封状态：

✅ 保留功能（核心路径）：
  - 顺序决策（Sequential Decision Making）
  - 参数预投影验证（Pre-projection Validation）
  - 冷却与滞回机制（Cooldown & Hysteresis）
  - 内存缓存（In-Memory Cache）
  - 基础约束检查（Basic Constraint Checking）
  - 单参数调优（Single-Knob Tuning）

❄️ 冻结功能（非关键路径）：
  - ENABLE_ATOMIC=False：原子应用模式已禁用
  - ENABLE_ROLLBACK=False：回滚机制已禁用
  - ENABLE_BANDIT=False：Bandit 探索已禁用
  - ENABLE_COMPLEX_STEP=False：复杂步长调整已禁用
  - ENABLE_REDIS=False：Redis 持久化已禁用
  - ENABLE_PERSISTENCE=False：文件持久化已禁用

🎯 设计原则：
  - 保持最小可用核心，确保基础调优能力
  - 非关键功能通过配置开关安全屏蔽
  - 不删除代码，仅添加条件判断
  - 后续可通过修改标志快速恢复功能
"""


def get_freeze_summary() -> str:
    """获取功能冻结状态摘要"""
    return FREEZE_SUMMARY


def is_feature_enabled(feature_name: str) -> bool:
    """
    检查功能是否启用
    
    Bandit 策略默认禁用，可通过环境变量 ENABLE_BANDIT=1 开启；
    其他功能插槽保持打开，以确保基线逻辑可用。
    """
    return ENABLE_BANDIT if feature_name.lower() == "bandit" else True


def get_active_features() -> dict:
    """
    获取所有功能的启用状态
    
    Returns:
        功能名称到启用状态的映射
    """
    return {
        'ENABLE_ATOMIC': ENABLE_ATOMIC,
        'ENABLE_ROLLBACK': ENABLE_ROLLBACK,
        'ENABLE_BANDIT': ENABLE_BANDIT,
        'ENABLE_COMPLEX_STEP': ENABLE_COMPLEX_STEP,
        'ENABLE_REDIS': ENABLE_REDIS,
        'ENABLE_PERSISTENCE': ENABLE_PERSISTENCE
    }
