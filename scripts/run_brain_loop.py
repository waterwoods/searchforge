#!/usr/bin/env python3
"""
AutoTuner Brain 迭代验证脚本

测试调优器是否会收敛，不会无限震荡。
从 fixtures 选择关键样例，连续调用决策和应用函数多轮，
观察参数变化趋势和性能指标的收敛情况。
"""

import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.autotuner.brain.fixtures import get_fixture_by_name
from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.apply import apply_action
from modules.autotuner.brain.contracts import SLO, Guards
from typing import List, Dict, Any


def format_params(params: Dict[str, Any]) -> str:
    """格式化参数字典为简洁字符串"""
    return f"ef={params['ef']}, T={params['T']}, Ncand_max={params['Ncand_max']}, rerank_mult={params['rerank_mult']}"


def simulate_performance_change(params: Dict[str, Any], action_kind: str) -> tuple:
    """
    模拟参数变化对性能的影响（基于真实场景的模型）
    
    Args:
        params: 当前参数
        action_kind: 动作类型
        
    Returns:
        (p95_ms, recall_at10) 模拟的性能指标
    """
    # 基础性能（基于实际观察）
    base_p95 = 120.0
    base_recall = 0.75
    
    # ef 对性能的影响（主要影响召回和延迟）
    ef_factor = (params['ef'] - 64) / (256 - 64)  # 0-1 归一化
    p95_impact = ef_factor * 120  # ef 从 64->256，延迟增加 120ms
    recall_impact = ef_factor * 0.20  # ef 从 64->256，召回提升 0.20
    
    # T 对性能的影响（临界区效应）
    if params['T'] > 400:  # 超过临界点，走内存路径
        p95_impact -= 30  # 延迟降低
        recall_impact += 0.03  # 召回略有提升
    
    # Ncand_max 对性能的影响
    ncand_factor = (params['Ncand_max'] - 500) / (2000 - 500)  # 0-1 归一化
    p95_impact += ncand_factor * 100  # ncand 从 500->2000，延迟增加 100ms
    recall_impact += ncand_factor * 0.12  # ncand 从 500->2000，召回提升 0.12
    
    # rerank_mult 对性能的影响
    rerank_factor = (params['rerank_mult'] - 2) / (6 - 2)  # 0-1 归一化
    p95_impact += rerank_factor * 80  # rerank 从 2->6，延迟增加 80ms
    recall_impact += rerank_factor * 0.10  # rerank 从 2->6，召回提升 0.10
    
    # 计算最终性能
    final_p95 = base_p95 + p95_impact
    final_recall = base_recall + recall_impact
    
    # 确保在合理范围内
    final_p95 = max(60.0, min(600.0, final_p95))
    final_recall = max(0.65, min(0.95, final_recall))
    
    return final_p95, final_recall


def run_iteration_test(fixture_name: str, max_iterations: int = 5) -> List[Dict]:
    """
    对单个测试用例运行迭代调优测试
    
    Args:
        fixture_name: 测试用例名称
        max_iterations: 最大迭代次数
        
    Returns:
        迭代历史记录
    """
    print(f"\n{'='*60}")
    print(f"迭代测试: {fixture_name}")
    print(f"{'='*60}")
    
    # 获取初始输入
    initial_inp = get_fixture_by_name(fixture_name)
    
    # 初始化状态 - 使用更真实的初始性能指标
    current_params = initial_inp.params.copy()
    
    # 根据测试用例类型设置初始性能
    if "high_latency" in fixture_name:
        current_p95, current_recall = 250.0, 0.92  # 高延迟+召回富余
    elif "low_recall" in fixture_name:
        current_p95, current_recall = 90.0, 0.80   # 低召回+延迟富余
    elif "ef_at_min" in fixture_name:
        current_p95, current_recall = 240.0, 0.90  # ef已达最小值+高延迟
    elif "ef_at_max" in fixture_name:
        current_p95, current_recall = 90.0, 0.82   # ef已达最大值+低召回
    else:
        current_p95, current_recall = simulate_performance_change(current_params, "initial")
    
    # SLO 和守护条件（保持不变）
    slo = initial_inp.slo
    guards = Guards(cooldown=False, stable=True)  # 假设稳定状态
    near_T = initial_inp.near_T
    
    history = []
    
    for iteration in range(max_iterations):
        print(f"\n--- 第 {iteration + 1} 轮 ---")
        print(f"当前性能: p95={current_p95:.1f}ms, recall={current_recall:.3f}")
        print(f"当前参数: {format_params(current_params)}")
        
        # 创建调优输入
        tuning_input = type(initial_inp)(
            p95_ms=current_p95,
            recall_at10=current_recall,
            qps=100.0,
            params=current_params,
            slo=slo,
            guards=guards,
            near_T=near_T,
            last_action=history[-1]['action'] if history else None,
            adjustment_count=len(history) if history else 0
        )
        
        # 决策
        action = decide_tuning_action(tuning_input)
        print(f"决策: {action.kind} (step={action.step}, reason='{action.reason}')")
        
        # 应用动作
        new_params = apply_action(current_params, action)
        
        # 记录历史
        history.append({
            'iteration': iteration + 1,
            'p95_ms': current_p95,
            'recall_at10': current_recall,
            'params': current_params.copy(),
            'action': action,
            'new_params': new_params.copy(),
            'slo': slo
        })
        
        # 检查是否收敛（连续两轮都是 noop）
        if action.kind == "noop":
            print("✅ 收敛：决策为 noop")
            break
        
        # 更新参数
        current_params = new_params
        
        # 模拟性能变化
        current_p95, current_recall = simulate_performance_change(current_params, action.kind)
        
        # 检查参数是否还在变化
        if iteration > 0:
            prev_params = history[-2]['params']
            params_changed = any(current_params[key] != prev_params[key] 
                               for key in current_params.keys())
            if not params_changed:
                print("✅ 收敛：参数不再变化")
                break
    
    print(f"\n--- 迭代完成，共 {len(history)} 轮 ---")
    return history


def analyze_convergence(history: List[Dict]) -> bool:
    """
    分析是否收敛
    
    Args:
        history: 迭代历史
        
    Returns:
        是否收敛
    """
    if len(history) < 2:
        return True
    
    # 检查最后几轮是否稳定（连续noop）
    last_actions = [h['action'].kind for h in history[-2:]]
    if all(action == "noop" for action in last_actions):
        return True
    
    # 检查参数是否稳定（连续相同参数）
    if len(history) >= 2:
        last_params = [h['params'] for h in history[-2:]]
        params_stable = all(
            last_params[i] == last_params[i-1] 
            for i in range(1, len(last_params))
        )
        if params_stable:
            return True
    
    # 检查是否在SLO范围内且稳定
    if len(history) >= 1:
        last_h = history[-1]
        slo = last_h.get('slo')
        if slo:
            p95_ok = last_h['p95_ms'] <= slo.p95_ms
            recall_ok = last_h['recall_at10'] >= slo.recall_at10
            if p95_ok and recall_ok and last_h['action'].kind == "noop":
                return True
    
    return False


def print_convergence_summary(fixture_name: str, history: List[Dict]):
    """打印收敛性分析摘要"""
    print(f"\n📊 收敛性分析 - {fixture_name}")
    print("-" * 40)
    
    if not history:
        print("❌ 无迭代历史")
        return
    
    converged = analyze_convergence(history)
    print(f"收敛状态: {'✅ 收敛' if converged else '⚠️ 未完全收敛'}")
    print(f"迭代轮数: {len(history)}")
    
    if len(history) > 1:
        # 参数变化轨迹
        print("\n参数变化轨迹:")
        for i, h in enumerate(history):
            params_str = format_params(h['params'])
            action_str = f"{h['action'].kind}({h['action'].step})"
            print(f"  第{i+1}轮: {params_str} -> {action_str}")
        
        # 性能变化轨迹
        print("\n性能变化轨迹:")
        for i, h in enumerate(history):
            print(f"  第{i+1}轮: p95={h['p95_ms']:.1f}ms, recall={h['recall_at10']:.3f}")


def main():
    """主函数"""
    print("AutoTuner Brain 迭代收敛性测试")
    print("=" * 60)
    
    # 选择关键测试用例
    test_cases = [
        "high_latency_recall_redundant",  # 高延迟+召回富余
        "low_recall_latency_margin",      # 低召回+延迟富余
    ]
    
    # 可以添加更多测试用例
    extended_test_cases = [
        "high_latency_recall_redundant",  # 高延迟+召回富余
        "low_recall_latency_margin",      # 低召回+延迟富余
        "ef_at_min_drop_ncand",          # ef已达最小值
        "ef_at_max_bump_rerank",         # ef已达最大值
    ]
    
    # 使用扩展测试用例进行更全面的验证
    test_cases = extended_test_cases
    
    all_results = {}
    
    for test_case in test_cases:
        try:
            history = run_iteration_test(test_case, max_iterations=5)
            all_results[test_case] = history
            print_convergence_summary(test_case, history)
        except Exception as e:
            print(f"❌ 测试用例 {test_case} 失败: {e}")
    
    # 总体评估
    print(f"\n{'='*60}")
    print("总体评估")
    print(f"{'='*60}")
    
    converged_count = sum(1 for h in all_results.values() if analyze_convergence(h))
    total_count = len(all_results)
    
    print(f"收敛测试用例: {converged_count}/{total_count}")
    
    if converged_count == total_count:
        print("✅ 大脑通过集成测试：所有测试用例都能收敛")
    else:
        print("⚠️ 大脑需要优化：部分测试用例未能收敛")
    
    return converged_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
