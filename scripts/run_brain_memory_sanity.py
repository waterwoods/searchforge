#!/usr/bin/env python3
"""
AutoTuner Brain 记忆层验证脚本

验证记忆驱动的决策行为：
1. 先训练记忆（喂入满足SLO的ef=160观测）
2. 测试三个典型场景的决策行为
"""

import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.autotuner.brain.fixtures import get_fixture_by_name
from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.contracts import TuningInput, SLO, Guards, MemorySample
from modules.autotuner.brain.memory import get_memory
import time


def format_params(params):
    """格式化参数字典为简洁字符串"""
    return f"ef={params['ef']}, T={params['T']}, Ncand_max={params['Ncand_max']}, rerank_mult={params['rerank_mult']}"


def train_memory_with_ef(memory, ef: int, count: int = 20):
    """
    训练记忆，使用指定的ef值
    
    Args:
        memory: 记忆实例
        ef: ef值
        count: 训练样本数量
    """
    print(f"训练记忆：ef={ef}，样本数={count}")
    
    bucket_id = "medium_candidates"  # 对应Ncand_max=1000
    
    for i in range(count):
        sample = MemorySample(
            bucket_id=bucket_id,
            ef=ef,
            T=500,
            Ncand_max=1000,
            p95_ms=150.0,  # 满足SLO (<=200)
            recall_at10=0.87,  # 满足SLO (>=0.85)
            ts=time.time()
        )
        memory.observe(sample)
    
    print(f"训练完成：甜点ef={ef}")


def test_scenario(memory, scenario_name: str, params: dict, expected_behavior: str):
    """
    测试单个场景
    
    Args:
        memory: 记忆实例
        scenario_name: 场景名称
        params: 参数配置
        expected_behavior: 期望行为描述
    """
    print(f"\n--- {scenario_name} ---")
    print(f"期望：{expected_behavior}")
    
    inp = TuningInput(
        p95_ms=90.0,  # 低延迟
        recall_at10=0.80,  # 低召回
        qps=100.0,
        params=params,
        slo=SLO(p95_ms=200.0, recall_at10=0.85),
        guards=Guards(cooldown=False, stable=True),
        near_T=False,
        last_action=None,
        adjustment_count=0
    )
    
    print(f"当前参数: {format_params(params)}")
    
    # 决策
    action = decide_tuning_action(inp)
    
    print(f"决策: {action.kind} (step={action.step}, reason='{action.reason}')")
    
    # 应用动作
    new_params = params.copy()
    if action.kind == "bump_ef":
        new_params["ef"] += int(action.step)
    elif action.kind == "drop_ef":
        new_params["ef"] += int(action.step)  # step已经是负数
    elif action.kind == "noop":
        pass
    
    print(f"新参数: {format_params(new_params)}")
    
    return action


def run_memory_sanity_check():
    """运行记忆验证检查"""
    print("AutoTuner Brain 记忆层验证")
    print("=" * 50)
    
    # 获取记忆实例
    memory = get_memory()
    
    # 清空现有记忆
    memory.ring_buffer.clear()
    memory.ewma_data.clear()
    memory.sweet_spots.clear()
    memory.last_update.clear()
    
    # 设置环境变量
    os.environ['MEMORY_ENABLED'] = '1'
    os.environ['MEMORY_TTL_SEC'] = '3600'  # 1小时，避免过期
    
    # 1. 训练阶段：喂入满足SLO的ef=160观测
    print("\n阶段1：训练记忆")
    print("-" * 30)
    train_memory_with_ef(memory, ef=160, count=20)
    
    # 2. 测试阶段：三个典型场景
    print("\n阶段2：测试决策")
    print("-" * 30)
    
    base_params = {
        'ef': 128,
        'T': 500,
        'Ncand_max': 1000,
        'rerank_mult': 3
    }
    
    # 场景1：当前ef=128，期望nudge_ef→+16
    params1 = base_params.copy()
    action1 = test_scenario(
        memory, 
        "场景1：ef=128 → 甜点160",
        params1,
        "期望 nudge_ef → +16"
    )
    
    # 场景2：当前ef=192，期望nudge_ef→-16
    params2 = base_params.copy()
    params2['ef'] = 192
    action2 = test_scenario(
        memory,
        "场景2：ef=192 → 甜点160", 
        params2,
        "期望 nudge_ef → -16"
    )
    
    # 场景3：记忆过期测试
    print("\n--- 场景3：记忆过期测试 ---")
    print("期望：走原逻辑")
    
    # 让记忆过期
    memory.last_update["medium_candidates"] = time.time() - 7200  # 2小时前
    
    params3 = base_params.copy()
    action3 = test_scenario(
        memory,
        "场景3：记忆过期",
        params3, 
        "期望走原逻辑 bump_ef → +32"
    )
    
    # 总结
    print("\n" + "=" * 50)
    print("验证结果总结")
    print("=" * 50)
    
    results = [
        ("场景1", action1.kind, action1.step, action1.reason),
        ("场景2", action2.kind, action2.step, action2.reason),
        ("场景3", action3.kind, action3.step, action3.reason)
    ]
    
    for scenario, kind, step, reason in results:
        print(f"{scenario}: {kind} (step={step}, reason='{reason}')")
    
    # 验证期望
    success_count = 0
    
    if action1.kind == "bump_ef" and action1.step == 16:
        print("✅ 场景1通过：记忆驱动小步靠拢")
        success_count += 1
    else:
        print("❌ 场景1失败：未按预期靠拢")
    
    if action2.kind == "drop_ef" and action2.step == -16:
        print("✅ 场景2通过：记忆驱动小步靠拢")
        success_count += 1
    else:
        print("❌ 场景2失败：未按预期靠拢")
    
    if action3.kind == "bump_ef" and action3.step == 32:
        print("✅ 场景3通过：记忆过期回退原逻辑")
        success_count += 1
    else:
        print("❌ 场景3失败：未按预期回退")
    
    print(f"\n总体结果：{success_count}/3 场景通过")
    
    if success_count == 3:
        print("🎉 记忆层验证成功！")
        return True
    else:
        print("⚠️ 记忆层验证需要优化")
        return False


if __name__ == "__main__":
    success = run_memory_sanity_check()
    sys.exit(0 if success else 1)

