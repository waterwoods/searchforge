#!/usr/bin/env python3
"""
AutoTuner Brain Sanity Check Script

本地快速验证 AutoTuner Brain 的决策逻辑和参数应用。
逐条读取 fixtures，调用 decide_tuning_action() 和 apply_action()，
打印决策过程和参数变化。
"""

import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.autotuner.brain.fixtures import create_fixtures
from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.apply import apply_action


def format_params(params):
    """格式化参数字典为简洁字符串"""
    return f"ef={params['ef']}, T={params['T']}, Ncand_max={params['Ncand_max']}, rerank_mult={params['rerank_mult']}"


def run_sanity_check():
    """运行 sanity 检查"""
    print("AutoTuner Brain Sanity Check")
    print("=" * 50)
    
    fixtures = create_fixtures()
    
    for i, fixture in enumerate(fixtures, 1):
        print(f"\n{i}. {fixture.name}")
        print("-" * 30)
        
        # 获取输入数据
        inp = fixture.tuning_input
        
        # 显示当前状态
        print(f"Current: p95={inp.p95_ms}ms, recall={inp.recall_at10:.2f}, qps={inp.qps}")
        print(f"SLO: p95<={inp.slo.p95_ms}ms, recall>={inp.slo.recall_at10:.2f}")
        print(f"Guards: cooldown={inp.guards.cooldown}, stable={inp.guards.stable}, near_T={inp.near_T}")
        print(f"Old params: {format_params(inp.params)}")
        
        # 决策
        action = decide_tuning_action(inp)
        
        # 应用动作
        new_params = apply_action(inp.params, action)
        
        # 显示结果
        print(f"Action: {action.kind} (step={action.step}, reason='{action.reason}')")
        print(f"New params: {format_params(new_params)}")
        
        # 显示参数变化
        changes = []
        for key in ['ef', 'T', 'Ncand_max', 'rerank_mult']:
            old_val = inp.params[key]
            new_val = new_params[key]
            if old_val != new_val:
                delta = new_val - old_val
                changes.append(f"{key}: {old_val}→{new_val} ({delta:+d})")
        
        if changes:
            print(f"Changes: {', '.join(changes)}")
        else:
            print("Changes: none")
    
    print("\n" + "=" * 50)
    print(f"Sanity check completed. Processed {len(fixtures)} test cases.")


if __name__ == "__main__":
    run_sanity_check()
