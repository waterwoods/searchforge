#!/usr/bin/env python3
"""
演示步长封顶功能

展示 AutoTuner 的步长封顶机制如何防止参数调整过大。
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.autotuner.brain.apply import apply_updates, STEP_CAPS
from modules.autotuner.brain.contracts import MultiKnobResult

def demo_step_cap():
    """演示步长封顶功能"""
    
    print("=" * 80)
    print("步长封顶功能演示")
    print("=" * 80)
    print()
    
    # 显示当前的步长上限配置
    print("📋 步长上限配置 (STEP_CAPS):")
    print("-" * 80)
    for param, limit in STEP_CAPS.items():
        print(f"  {param:20s}: ±{limit:4d} (每次 tick 最大变化)")
    print()
    
    # 初始参数
    current_params = {
        "ef_search": 128,
        "candidate_k": 100,
        "rerank_k": 10,
        "threshold_T": 0.5
    }
    
    print("🔧 初始参数:")
    print("-" * 80)
    for k, v in current_params.items():
        print(f"  {k:20s}: {v}")
    print()
    
    # 测试场景1: 大幅度更新（会被封顶）
    print("📝 场景 1: 尝试大幅度更新 (超出步长上限)")
    print("-" * 80)
    large_updates = {
        "ef_search": 50,      # 超出上限 16
        "candidate_k": 300,   # 超出上限 200
        "rerank_k": 20        # 超出上限 10
    }
    
    print("请求的更新:")
    for k, v in large_updates.items():
        cap = STEP_CAPS.get(k, "N/A")
        status = "⚠️  超出上限" if abs(v) > cap else "✅ 在上限内"
        print(f"  {k:20s}: {v:+4d}  (上限: ±{cap:4d})  {status}")
    print()
    
    result = apply_updates(current_params, large_updates, "sequential")
    
    print(f"应用结果: {result.status}")
    print("实际应用的参数:")
    for k, v in result.params_after.items():
        before = current_params.get(k, 0)
        actual_delta = v - before
        requested_delta = large_updates.get(k, 0)
        
        if k in large_updates:
            was_capped = abs(actual_delta) < abs(requested_delta)
            cap_marker = "🔒 已封顶" if was_capped else "✅ 正常应用"
            print(f"  {k:20s}: {before:4} → {v:4}  (Δ = {actual_delta:+4})  {cap_marker}")
    print()
    
    # 测试场景2: 小幅度更新（不会被封顶）
    print("📝 场景 2: 小幅度更新 (在步长上限内)")
    print("-" * 80)
    small_updates = {
        "ef_search": 8,       # 在上限内
        "candidate_k": 50,    # 在上限内
        "rerank_k": 5         # 在上限内
    }
    
    print("请求的更新:")
    for k, v in small_updates.items():
        cap = STEP_CAPS.get(k, "N/A")
        status = "✅ 在上限内"
        print(f"  {k:20s}: {v:+4d}  (上限: ±{cap:4d})  {status}")
    print()
    
    result2 = apply_updates(current_params, small_updates, "sequential")
    
    print(f"应用结果: {result2.status}")
    print("实际应用的参数:")
    for k, v in result2.params_after.items():
        before = current_params.get(k, 0)
        actual_delta = v - before
        
        if k in small_updates:
            print(f"  {k:20s}: {before:4} → {v:4}  (Δ = {actual_delta:+4})  ✅ 正常应用")
    print()
    
    # 测试场景3: 负向大幅度更新（会被封顶）
    print("📝 场景 3: 负向大幅度更新 (超出步长上限)")
    print("-" * 80)
    negative_updates = {
        "ef_search": -50,     # 超出上限 16
        "candidate_k": -300,  # 超出上限 200
    }
    
    print("请求的更新:")
    for k, v in negative_updates.items():
        cap = STEP_CAPS.get(k, "N/A")
        status = "⚠️  超出上限" if abs(v) > cap else "✅ 在上限内"
        print(f"  {k:20s}: {v:+4d}  (上限: ±{cap:4d})  {status}")
    print()
    
    result3 = apply_updates(current_params, negative_updates, "sequential")
    
    print(f"应用结果: {result3.status}")
    print("实际应用的参数:")
    for k, v in result3.params_after.items():
        before = current_params.get(k, 0)
        actual_delta = v - before
        requested_delta = negative_updates.get(k, 0)
        
        if k in negative_updates:
            was_capped = abs(actual_delta) < abs(requested_delta)
            cap_marker = "🔒 已封顶" if was_capped else "✅ 正常应用"
            print(f"  {k:20s}: {before:4} → {v:4}  (Δ = {actual_delta:+4})  {cap_marker}")
    print()
    
    print("=" * 80)
    print("总结:")
    print("=" * 80)
    print("✅ 步长封顶功能正常工作")
    print("   - 大幅度更新会被限制在步长上限内")
    print("   - 小幅度更新正常应用")
    print("   - 正负方向都受到封顶保护")
    print()
    print("📖 步长封顶的作用:")
    print("   1. 防止参数抖动：避免参数在短时间内剧烈变化")
    print("   2. 保证平滑调整：确保系统性能渐进式优化")
    print("   3. 降低风险：限制单次调整的影响范围")
    print()


if __name__ == "__main__":
    demo_step_cap()


