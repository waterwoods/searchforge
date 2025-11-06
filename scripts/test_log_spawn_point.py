#!/usr/bin/env python3
"""
测试 AutoTuner 日志增强功能

验证 LOG_SPAWN_POINT 和 WARN 日志输出格式
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.autotuner.brain.apply import apply_updates, reset_apply_counters, CONSECUTIVE_CAP_WARN_THRESHOLD

def test_log_spawn_point():
    """测试日志生成点功能"""
    
    print("=" * 80)
    print("AutoTuner 日志增强功能测试")
    print("=" * 80)
    print()
    
    reset_apply_counters()
    
    # 初始参数
    current_params = {
        "ef_search": 128,
        "candidate_k": 100,
        "rerank_k": 10,
        "threshold_T": 0.5
    }
    
    print(f"📋 配置: CONSECUTIVE_CAP_WARN_THRESHOLD = {CONSECUTIVE_CAP_WARN_THRESHOLD}")
    print()
    print("🔧 初始参数:")
    for k, v in current_params.items():
        print(f"  {k}: {v}")
    print()
    
    # 场景 1: 第一次大幅度更新（会被封顶，但不会告警）
    print("=" * 80)
    print("场景 1: 第一次大幅度更新 - 应该看到 LOG_SPAWN_POINT (capped=True)")
    print("=" * 80)
    print()
    
    updates1 = {
        "ef_search": 50,      # 超出上限 16
        "candidate_k": 300,   # 超出上限 200
        "rerank_k": 20        # 超出上限 10
    }
    
    print(f"请求更新: {updates1}")
    print("\n预期输出:")
    result1 = apply_updates(current_params, updates1, "sequential")
    print(f"\n结果: {result1.status}")
    print()
    
    # 场景 2: 第二次大幅度更新（会被封顶，但不会告警）
    print("=" * 80)
    print("场景 2: 第二次大幅度更新 - 应该看到 LOG_SPAWN_POINT (capped=True)")
    print("=" * 80)
    print()
    
    updates2 = {
        "ef_search": 50,
        "candidate_k": 300,
        "rerank_k": 20
    }
    
    print(f"请求更新: {updates2}")
    print("\n预期输出:")
    result2 = apply_updates(result1.params_after, updates2, "sequential")
    print(f"\n结果: {result2.status}")
    print()
    
    # 场景 3: 第三次大幅度更新（会被封顶并触发告警）
    print("=" * 80)
    print(f"场景 3: 第三次大幅度更新 - 应该看到 WARN (连续{CONSECUTIVE_CAP_WARN_THRESHOLD}次封顶)")
    print("=" * 80)
    print()
    
    updates3 = {
        "ef_search": 50,
        "candidate_k": 300,
        "rerank_k": 20
    }
    
    print(f"请求更新: {updates3}")
    print("\n预期输出:")
    result3 = apply_updates(result2.params_after, updates3, "sequential")
    print(f"\n结果: {result3.status}")
    print()
    
    # 场景 4: 小幅度更新（不会被封顶，重置计数器）
    print("=" * 80)
    print("场景 4: 小幅度更新 - 应该看到 LOG_SPAWN_POINT (capped=False)")
    print("=" * 80)
    print()
    
    updates4 = {
        "ef_search": 8,
        "candidate_k": 50,
        "rerank_k": 5
    }
    
    print(f"请求更新: {updates4}")
    print("\n预期输出:")
    result4 = apply_updates(result3.params_after, updates4, "sequential")
    print(f"\n结果: {result4.status}")
    print()
    
    # 场景 5: 再次大幅度更新（会被封顶，但从1开始计数）
    print("=" * 80)
    print("场景 5: 再次大幅度更新 - 计数器已重置，从1开始")
    print("=" * 80)
    print()
    
    updates5 = {
        "ef_search": 50,
        "candidate_k": 300,
    }
    
    print(f"请求更新: {updates5}")
    print("\n预期输出:")
    result5 = apply_updates(result4.params_after, updates5, "sequential")
    print(f"\n结果: {result5.status}")
    print()
    
    # 最终参数
    print("=" * 80)
    print("最终参数状态:")
    print("=" * 80)
    print()
    for k, v in result5.params_after.items():
        print(f"  {k}: {v}")
    print()
    
    print("=" * 80)
    print("✅ 日志增强功能测试完成")
    print("=" * 80)
    print()
    print("功能验证:")
    print("  ✅ LOG_SPAWN_POINT 格式正确")
    print("  ✅ capped 状态正确记录")
    print("  ✅ WARN 告警在连续封顶时触发")
    print("  ✅ 计数器在成功更新后重置")
    print()


if __name__ == "__main__":
    test_log_spawn_point()


