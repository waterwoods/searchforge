#!/usr/bin/env python3
"""AutoTuner 契约验证脚本"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.autotuner.brain.contracts import TuningInput, SLO, Guards, Action
from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.apply import apply_action
from modules.autotuner.brain.constraints import clip_params, is_param_valid, validate_joint_constraints

def test_param_clipping():
    """测试参数裁剪"""
    print("测试 1: 参数边界裁剪")
    
    # 超出范围的参数
    bad_params = {'ef': 512, 'T': 2000, 'Ncand_max': 100, 'rerank_mult': 10}
    clipped = clip_params(bad_params)
    
    assert clipped['ef'] == 256, f"ef 裁剪失败: {clipped['ef']}"
    assert clipped['T'] == 1200, f"T 裁剪失败: {clipped['T']}"
    assert clipped['Ncand_max'] == 500, f"Ncand_max 裁剪失败: {clipped['Ncand_max']}"
    assert clipped['rerank_mult'] == 6, f"rerank_mult 裁剪失败: {clipped['rerank_mult']}"
    
    print("  ✅ 参数裁剪正常")

def test_joint_constraints():
    """测试联合约束"""
    print("测试 2: 联合约束验证")
    
    # 违反约束的参数
    bad_params = {'ef': 128, 'T': 500, 'Ncand_max': 500, 'rerank_mult': 100}
    is_valid = validate_joint_constraints(bad_params)
    
    assert not is_valid, "联合约束验证失败（应拒绝无效参数）"
    
    # 合法参数
    good_params = {'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3}
    is_valid = validate_joint_constraints(good_params)
    
    assert is_valid, "联合约束验证失败（应接受有效参数）"
    
    print("  ✅ 联合约束验证正常")

def test_decision_logic():
    """测试决策逻辑"""
    print("测试 3: 决策逻辑")
    
    # 禁用记忆系统以避免干扰
    os.environ['MEMORY_ENABLED'] = '0'
    
    # 高延迟 + 召回富余 → 应降 ef
    inp = TuningInput(
        p95_ms=250.0,
        recall_at10=0.92,
        qps=100.0,
        params={'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3},
        slo=SLO(p95_ms=200.0, recall_at10=0.85),
        guards=Guards(cooldown=False, stable=True),
        near_T=False
    )
    
    action = decide_tuning_action(inp)
    assert action.kind == "drop_ef", f"决策错误: 期望 drop_ef，实际 {action.kind}"
    
    print("  ✅ 决策逻辑正常")

def test_action_application():
    """测试动作应用"""
    print("测试 4: 动作应用")
    
    params = {'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3}
    action = Action(kind='drop_ef', step=-32.0, reason='test')
    
    new_params = apply_action(params, action)
    assert new_params['ef'] == 96, f"动作应用失败: 期望 96，实际 {new_params['ef']}"
    
    print("  ✅ 动作应用正常")

def test_boundary_cases():
    """测试边界情况"""
    print("测试 5: 边界情况")
    
    # 测试参数到达最小值时的行为
    params = {'ef': 64, 'T': 200, 'Ncand_max': 500, 'rerank_mult': 2}
    action = Action(kind='drop_ef', step=-32.0, reason='test')
    
    new_params = apply_action(params, action)
    # 应该被裁剪到最小值
    assert new_params['ef'] == 64, f"边界裁剪失败: ef 应保持在 64，实际 {new_params['ef']}"
    
    # 测试参数到达最大值时的行为
    params = {'ef': 256, 'T': 1200, 'Ncand_max': 2000, 'rerank_mult': 6}
    action = Action(kind='bump_ef', step=32.0, reason='test')
    
    new_params = apply_action(params, action)
    # 应该被裁剪到最大值
    assert new_params['ef'] == 256, f"边界裁剪失败: ef 应保持在 256，实际 {new_params['ef']}"
    
    print("  ✅ 边界情况处理正常")

if __name__ == '__main__':
    print("=== AutoTuner 契约验证 ===\n")
    
    try:
        test_param_clipping()
        test_joint_constraints()
        test_decision_logic()
        test_action_application()
        test_boundary_cases()
        
        print("\n✅ 所有验证通过！")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 验证失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
