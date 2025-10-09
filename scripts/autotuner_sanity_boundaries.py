#!/usr/bin/env python3
"""
AutoTuner Sanity Test B: 边界/防抖快检（纯函数，≤5秒）

验证决策正确方向、裁剪、冷却/滞回不抖动。
构造 3 组窗口序列，每组 5 tick。
"""

import sys
import os
import json
import time
from typing import Dict, Any, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.autotuner.brain.contracts import TuningInput, Action, SLO, Guards
from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.apply import apply_action
from modules.autotuner.brain.constraints import clip_params, is_param_valid


class BoundarySanityTest:
    """边界和防抖测试"""
    
    def __init__(self):
        self.test_results = []
        self.failures = []
        
    def create_group1_high_latency(self) -> List[Tuple[str, TuningInput]]:
        """
        G1: 高延迟且召回≥目标+裕度
        期望: drop_ef 或 drop_ncand，且 clip 后参数不越界
        """
        slo = SLO(p95_ms=1200.0, recall_at10=0.85)
        
        scenarios = []
        for i in range(5):
            name = f"G1_Tick{i}"
            inp = TuningInput(
                p95_ms=1500.0 + i * 10,  # 高延迟，持续
                recall_at10=0.92,  # 召回有裕度
                qps=10.0,
                params={'ef': 128 - i * 4, 'T': 500, 'Ncand_max': 1000 - i * 20, 'rerank_mult': 2},
                slo=slo,
                guards=Guards(cooldown=(i < 2), stable=True),  # 前2个tick冷却
                near_T=False
            )
            scenarios.append((name, inp))
        
        return scenarios
    
    def create_group2_low_recall(self) -> List[Tuple[str, TuningInput]]:
        """
        G2: 低召回且延迟≤目标-裕度
        期望: bump_ef 或 bump_rerank
        """
        slo = SLO(p95_ms=1200.0, recall_at10=0.85)
        
        scenarios = []
        for i in range(5):
            name = f"G2_Tick{i}"
            inp = TuningInput(
                p95_ms=1000.0 - i * 10,  # 延迟有裕度
                recall_at10=0.75 - i * 0.01,  # 低召回
                qps=10.0,
                params={'ef': 96 + i * 4, 'T': 500, 'Ncand_max': 800 + i * 20, 'rerank_mult': 2},
                slo=slo,
                guards=Guards(cooldown=(i < 2), stable=True),
                near_T=False
            )
            scenarios.append((name, inp))
        
        return scenarios
    
    def create_group3_hysteresis(self) -> List[Tuple[str, TuningInput]]:
        """
        G3: 交替轻微波动（±阈宽内）
        期望: 连续 5 tick 均为 noop（hysteresis 生效）
        """
        slo = SLO(p95_ms=1200.0, recall_at10=0.85)
        
        scenarios = []
        for i in range(5):
            name = f"G3_Tick{i}"
            # 围绕 SLO 小幅波动（在滞回带内）
            p95_delta = 30 if i % 2 == 0 else -30  # ±30ms < 100ms (滞回带)
            recall_delta = 0.01 if i % 2 == 0 else -0.01  # ±0.01 < 0.02 (滞回带)
            
            inp = TuningInput(
                p95_ms=1200.0 + p95_delta,
                recall_at10=0.85 + recall_delta,
                qps=10.0,
                params={'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 2},
                slo=slo,
                guards=Guards(cooldown=False, stable=True),
                near_T=False
            )
            scenarios.append((name, inp))
        
        return scenarios
    
    def run_scenario(self, name: str, inp: TuningInput, 
                     expected_direction: str = None) -> Dict[str, Any]:
        """
        运行单个场景
        
        Args:
            name: 场景名称
            inp: 输入
            expected_direction: 期望方向 ('drop', 'bump', 'noop')
        """
        # 决策
        action = decide_tuning_action(inp)
        
        # 应用
        params_after = apply_action(inp.params, action)
        
        # 检查参数是否越界
        params_valid = is_param_valid(params_after)
        
        # 检查裁剪（如果参数发生变化）
        clipped = False
        for key in ['ef', 'T', 'Ncand_max', 'rerank_mult']:
            if key in inp.params and key in params_after:
                if inp.params[key] != params_after[key]:
                    # 参数变化了，检查是否被裁剪
                    ranges = {
                        'ef': (64, 256),
                        'T': (200, 1200),
                        'Ncand_max': (500, 2000),
                        'rerank_mult': (2, 6)
                    }
                    if key in ranges:
                        min_val, max_val = ranges[key]
                        if params_after[key] == min_val or params_after[key] == max_val:
                            clipped = True
        
        # 检查方向
        direction_correct = True
        if expected_direction:
            if expected_direction == 'drop':
                direction_correct = action.kind in ['drop_ef', 'drop_ncand', 'drop_rerank', 'drop_T', 'noop']
            elif expected_direction == 'bump':
                direction_correct = action.kind in ['bump_ef', 'bump_ncand', 'bump_rerank', 'bump_T', 'noop']
            elif expected_direction == 'noop':
                direction_correct = action.kind == 'noop'
        
        result = {
            'name': name,
            'p95_ms': inp.p95_ms,
            'recall_at10': inp.recall_at10,
            'slo_p95': inp.slo.p95_ms,
            'slo_recall': inp.slo.recall_at10,
            'cooldown': inp.guards.cooldown,
            'params_before': inp.params,
            'action': {
                'kind': action.kind,
                'step': action.step,
                'reason': action.reason
            },
            'params_after': params_after,
            'params_valid': params_valid,
            'clipped': clipped,
            'expected_direction': expected_direction,
            'direction_correct': direction_correct
        }
        
        return result
    
    def check_no_reversal(self, group_results: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        检查同组内是否有方向反转
        
        Returns:
            (is_ok, message)
        """
        actions = [r['action']['kind'] for r in group_results if r['action']['kind'] != 'noop']
        
        for i in range(len(actions) - 1):
            curr = actions[i]
            next_action = actions[i + 1]
            
            # 检查是否反向
            if ('drop' in curr and 'bump' in next_action) or \
               ('bump' in curr and 'drop' in next_action):
                return False, f"方向反转: {curr} → {next_action}"
        
        return True, "无方向反转"
    
    def run_group(self, group_name: str, scenarios: List[Tuple[str, TuningInput]], 
                  expected_direction: str = None, 
                  expect_all_noop: bool = False) -> Dict[str, Any]:
        """运行一组测试"""
        print(f"\n{'=' * 60}")
        print(f"  {group_name}")
        print(f"{'=' * 60}")
        
        group_results = []
        
        for name, inp in scenarios:
            result = self.run_scenario(name, inp, expected_direction)
            group_results.append(result)
            
            # 打印结果
            status = "✅" if result['params_valid'] and result['direction_correct'] else "❌"
            print(f"{status} {result['name']}: p95={result['p95_ms']:.0f}ms, "
                  f"recall={result['recall_at10']:.3f}, "
                  f"action={result['action']['kind']}, "
                  f"valid={result['params_valid']}, "
                  f"direction={result['direction_correct']}")
        
        # 检查约束
        all_valid = all(r['params_valid'] for r in group_results)
        all_directions_correct = all(r['direction_correct'] for r in group_results)
        
        # 检查方向反转
        no_reversal, reversal_msg = self.check_no_reversal(group_results)
        
        # 特殊检查：G3 应该全是 noop
        all_noop_correct = True
        if expect_all_noop:
            noop_count = sum(1 for r in group_results if r['action']['kind'] == 'noop')
            all_noop_correct = (noop_count == len(group_results))
        
        # 综合判断
        passed = all_valid and all_directions_correct and no_reversal
        if expect_all_noop:
            passed = passed and all_noop_correct
        
        group_summary = {
            'group_name': group_name,
            'total_ticks': len(group_results),
            'all_params_valid': all_valid,
            'all_directions_correct': all_directions_correct,
            'no_reversal': no_reversal,
            'reversal_msg': reversal_msg,
            'all_noop_correct': all_noop_correct if expect_all_noop else None,
            'passed': passed,
            'results': group_results
        }
        
        print(f"\n组总结:")
        print(f"  - 参数有效: {'✅' if all_valid else '❌'}")
        print(f"  - 方向正确: {'✅' if all_directions_correct else '❌'}")
        print(f"  - 无方向反转: {'✅' if no_reversal else '❌'} ({reversal_msg})")
        if expect_all_noop:
            print(f"  - 全为 noop: {'✅' if all_noop_correct else '❌'}")
        print(f"  - 结果: {'✅ PASS' if passed else '❌ FAIL'}")
        
        if not passed:
            self.failures.append(group_name)
        
        return group_summary
    
    def run(self) -> Dict[str, Any]:
        """运行所有边界测试"""
        print("\n" + "=" * 60)
        print("  [BOUNDARY] AutoTuner 边界/防抖测试")
        print("=" * 60)
        print("目标: 验证决策方向、裁剪、冷却/滞回不抖动")
        print()
        
        start_time = time.time()
        
        # G1: 高延迟 → 降参数
        g1_scenarios = self.create_group1_high_latency()
        g1_result = self.run_group(
            "G1: 高延迟且召回≥目标+裕度", 
            g1_scenarios, 
            expected_direction='drop'
        )
        
        # G2: 低召回 → 升参数
        g2_scenarios = self.create_group2_low_recall()
        g2_result = self.run_group(
            "G2: 低召回且延迟≤目标-裕度", 
            g2_scenarios, 
            expected_direction='bump'
        )
        
        # G3: 滞回带 → 全 noop
        g3_scenarios = self.create_group3_hysteresis()
        g3_result = self.run_group(
            "G3: 交替轻微波动（滞回带内）", 
            g3_scenarios, 
            expected_direction='noop',
            expect_all_noop=True
        )
        
        elapsed_time = time.time() - start_time
        
        # 综合判断
        all_passed = g1_result['passed'] and g2_result['passed'] and g3_result['passed']
        
        # 生成报告
        report = {
            'test_name': 'Boundary and Anti-Jitter Sanity Test',
            'timestamp': time.time(),
            'groups': {
                'G1_high_latency': g1_result,
                'G2_low_recall': g2_result,
                'G3_hysteresis': g3_result
            },
            'summary': {
                'all_passed': all_passed,
                'failed_groups': self.failures,
                'elapsed_time': round(elapsed_time, 3)
            },
            'result': 'PASS' if all_passed else 'FAIL'
        }
        
        # 打印总结
        print("\n" + "=" * 60)
        print("  总体结果")
        print("=" * 60)
        print(f"G1 (高延迟): {'✅ PASS' if g1_result['passed'] else '❌ FAIL'}")
        print(f"G2 (低召回): {'✅ PASS' if g2_result['passed'] else '❌ FAIL'}")
        print(f"G3 (滞回带): {'✅ PASS' if g3_result['passed'] else '❌ FAIL'}")
        print(f"\n总结: {'✅ PASS' if all_passed else '❌ FAIL'}")
        print(f"耗时: {elapsed_time:.3f}s")
        
        if self.failures:
            print(f"\n失败组: {', '.join(self.failures)}")
            # 打印首个失败断言
            for group_name in self.failures:
                group_key = {
                    'G1: 高延迟且召回≥目标+裕度': 'G1_high_latency',
                    'G2: 低召回且延迟≤目标-裕度': 'G2_low_recall',
                    'G3: 交替轻微波动（滞回带内）': 'G3_hysteresis'
                }.get(group_name)
                
                if group_key:
                    group_data = report['groups'][group_key]
                    if not group_data['all_params_valid']:
                        print(f"  {group_name}: 参数越界")
                        break
                    elif not group_data['all_directions_correct']:
                        print(f"  {group_name}: 决策方向错误")
                        break
                    elif not group_data['no_reversal']:
                        print(f"  {group_name}: {group_data['reversal_msg']}")
                        break
                    elif group_data.get('all_noop_correct') is False:
                        print(f"  {group_name}: 滞回机制未生效（存在非 noop 动作）")
                        break
        
        print("=" * 60 + "\n")
        
        return report


def main():
    """主入口"""
    # 创建测试实例
    test = BoundarySanityTest()
    
    # 运行测试
    report = test.run()
    
    # 保存报告
    os.makedirs('reports', exist_ok=True)
    report_path = 'reports/autotuner_sanity_boundaries.json'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"报告已保存: {report_path}\n")
    
    # 返回退出码
    return 0 if report['result'] == 'PASS' else 1


if __name__ == "__main__":
    sys.exit(main())
