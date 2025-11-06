#!/usr/bin/env python3
"""
AutoTuner Sanity Test A: Pipeline 烟囱跑（2 分钟）

验证 DECIDE→APPLY 事件链和指标落盘完整。
使用模拟模式（Qdrant 不可用时自动回落）。
"""

import sys
import os
import json
import time
from typing import Dict, Any, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.autotuner.brain.contracts import TuningInput, Action, SLO, Guards, MemorySample
from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.multi_knob_decider import decide_multi_knob
from modules.autotuner.brain.apply import apply_action, apply_updates, get_apply_counters, reset_apply_counters
from modules.autotuner.brain.memory import get_memory


class PipelineSanityTest:
    """Pipeline 烟囱测试"""
    
    def __init__(self, duration_sec: int = 120, bucket_sec: int = 10, qps: int = 10):
        self.duration_sec = duration_sec
        self.bucket_sec = bucket_sec
        self.qps = qps
        
        # 事件统计
        self.events = {
            'BRAIN_DECIDE': 0,
            'PARAMS_APPLIED': 0,
            'PARAMS_REJECTED': 0,
            'NOOP': 0
        }
        
        # 指标记录
        self.metrics_history = []
        
        # 参数历史
        self.params_history = []
        
        # SLO 配置
        self.slo = SLO(p95_ms=1200.0, recall_at10=0.85)
        
        # 初始参数
        self.current_params = {
            'ef': 128,
            'T': 500,
            'Ncand_max': 1000,
            'rerank_mult': 2
        }
        
        # 冷却计数
        self.cooldown_ticks = 0
        
    def simulate_metrics(self, tick: int) -> Dict[str, float]:
        """
        模拟性能指标
        
        初始阶段：高延迟 (1500ms)、高召回 (0.92)
        中间阶段：延迟逐渐下降
        最终阶段：达到或接近 SLO
        """
        total_ticks = self.duration_sec // self.bucket_sec
        progress = tick / total_ticks
        
        # 模拟延迟下降（在调优后）
        if tick < 3:
            p95_ms = 1500.0  # 初始高延迟
        elif tick < 6:
            p95_ms = 1400.0 - (tick - 3) * 50  # 逐渐下降
        elif tick < 9:
            p95_ms = 1300.0 - (tick - 6) * 30
        else:
            p95_ms = 1200.0 + (tick % 3) * 10  # 围绕 SLO 波动
        
        # 召回随延迟变化略有下降
        if tick < 3:
            recall = 0.92
        elif tick < 6:
            recall = 0.90
        elif tick < 9:
            recall = 0.88
        else:
            recall = 0.86
        
        return {
            'p95_ms': p95_ms,
            'recall_at10': recall,
            'qps': float(self.qps)
        }
    
    def run_tick(self, tick: int) -> Dict[str, Any]:
        """运行单个时间片"""
        # 获取模拟指标
        metrics = self.simulate_metrics(tick)
        
        # 记录指标
        self.metrics_history.append({
            'tick': tick,
            'timestamp': time.time(),
            **metrics,
            'params': self.current_params.copy()
        })
        
        # 构造决策输入（使用 multi_knob 决策器）
        tuning_input = TuningInput(
            p95_ms=metrics['p95_ms'],
            recall_at10=metrics['recall_at10'],
            qps=metrics['qps'],
            params=self.current_params.copy(),
            slo=self.slo,
            guards=Guards(cooldown=(self.cooldown_ticks > 0), stable=True),
            near_T=False
        )
        
        # 决策（优先使用 multi_knob，回落到单参数）
        action = decide_multi_knob(tuning_input)
        self.events['BRAIN_DECIDE'] += 1
        
        tick_result = {
            'tick': tick,
            'metrics': metrics,
            'action': {
                'kind': action.kind,
                'reason': action.reason,
                'mode': action.mode,
                'updates': action.updates
            },
            'params_before': self.current_params.copy()
        }
        
        # 应用动作
        if action.kind == "noop":
            self.events['NOOP'] += 1
            tick_result['params_after'] = self.current_params.copy()
            tick_result['applied'] = False
            
            # 减少冷却计数
            if self.cooldown_ticks > 0:
                self.cooldown_ticks -= 1
        else:
            # 应用更新
            if action.kind == "multi_knob" and action.updates:
                # Multi-knob 应用（顺序模式）
                result = apply_updates(self.current_params, action.updates, action.mode)
                
                if result.status == "applied":
                    self.current_params = result.params_after
                    self.events['PARAMS_APPLIED'] += 1
                    self.cooldown_ticks = 2  # 设置冷却
                    tick_result['applied'] = True
                else:
                    self.events['PARAMS_REJECTED'] += 1
                    tick_result['applied'] = False
                
                tick_result['params_after'] = result.params_after
                tick_result['apply_status'] = result.status
            else:
                # 单参数应用
                new_params = apply_action(self.current_params, action)
                self.current_params = new_params
                self.events['PARAMS_APPLIED'] += 1
                self.cooldown_ticks = 2
                tick_result['applied'] = True
                tick_result['params_after'] = new_params
        
        self.params_history.append(self.current_params.copy())
        return tick_result
    
    def run(self) -> Dict[str, Any]:
        """运行完整的管道测试"""
        print("\n" + "=" * 60)
        print("  [PIPELINE] AutoTuner 烟囱测试")
        print("=" * 60)
        print(f"配置: duration={self.duration_sec}s, bucket={self.bucket_sec}s, qps={self.qps}")
        print(f"SLO: p95≤{self.slo.p95_ms}ms, recall≥{self.slo.recall_at10}")
        print(f"模式: 仿真（Qdrant 不可用）")
        print(f"决策: Multi-knob（顺序模式，Atomic/Rollback 已冻结）")
        print()
        
        reset_apply_counters()
        
        # 运行所有时间片
        num_ticks = self.duration_sec // self.bucket_sec
        tick_results = []
        
        start_time = time.time()
        
        for tick in range(num_ticks):
            tick_result = self.run_tick(tick)
            tick_results.append(tick_result)
            
            # 打印进度
            if tick % 3 == 0:
                print(f"Tick {tick:2d}: p95={tick_result['metrics']['p95_ms']:6.1f}ms, "
                      f"recall={tick_result['metrics']['recall_at10']:.3f}, "
                      f"action={tick_result['action']['kind']}, "
                      f"applied={tick_result.get('applied', False)}")
        
        elapsed_time = time.time() - start_time
        
        # 计算统计指标
        total_decisions = self.events['BRAIN_DECIDE']
        total_applied = self.events['PARAMS_APPLIED']
        total_rejected = self.events['PARAMS_REJECTED']
        total_noop = self.events['NOOP']
        
        apply_rate = total_applied / total_decisions if total_decisions > 0 else 0.0
        
        # 计算安全率（没有导致参数越界或违反约束）
        safe_count = sum(1 for r in tick_results if self._check_params_safe(r.get('params_after', {})))
        safety_rate = safe_count / len(tick_results) if tick_results else 0.0
        
        # 验证事件链
        events_ok = (self.events['BRAIN_DECIDE'] >= 1 and self.events['PARAMS_APPLIED'] >= 1)
        
        # 验证指标存在
        metrics_ok = all('p95_ms' in m and 'recall_at10' in m for m in self.metrics_history)
        
        # 综合判断
        passed = (
            events_ok and 
            metrics_ok and 
            apply_rate >= 0.2 and 
            safety_rate >= 0.95
        )
        
        # 生成报告
        report = {
            'test_name': 'Pipeline Sanity Test',
            'timestamp': time.time(),
            'config': {
                'duration_sec': self.duration_sec,
                'bucket_sec': self.bucket_sec,
                'qps': self.qps,
                'mode': 'simulation'
            },
            'events': self.events,
            'statistics': {
                'total_decisions': total_decisions,
                'total_applied': total_applied,
                'total_rejected': total_rejected,
                'total_noop': total_noop,
                'apply_rate': round(apply_rate, 3),
                'safety_rate': round(safety_rate, 3)
            },
            'validation': {
                'events_ok': events_ok,
                'metrics_ok': metrics_ok,
                'apply_rate_ok': apply_rate >= 0.2,
                'safety_rate_ok': safety_rate >= 0.95
            },
            'result': 'PASS' if passed else 'FAIL',
            'elapsed_time': round(elapsed_time, 2),
            'metrics_history': self.metrics_history[-5:],  # 最后 5 条
            'params_history': self.params_history[-5:],    # 最后 5 条
            'tick_results': tick_results
        }
        
        # 打印结果
        print("\n" + "=" * 60)
        print("  测试结果")
        print("=" * 60)
        print(f"事件统计:")
        print(f"  - BRAIN_DECIDE: {total_decisions}")
        print(f"  - PARAMS_APPLIED: {total_applied}")
        print(f"  - PARAMS_REJECTED: {total_rejected}")
        print(f"  - NOOP: {total_noop}")
        print(f"\n性能指标:")
        print(f"  - Apply Rate: {apply_rate:.1%} (门槛: ≥20%)")
        print(f"  - Safety Rate: {safety_rate:.1%} (门槛: ≥95%)")
        print(f"\n验证结果:")
        print(f"  - Events OK: {'✅' if events_ok else '❌'} (DECIDE≥1 且 APPLIED≥1)")
        print(f"  - Metrics OK: {'✅' if metrics_ok else '❌'} (p95_ms/recall_at10 存在)")
        print(f"  - Apply Rate: {'✅' if apply_rate >= 0.2 else '❌'} ({apply_rate:.1%})")
        print(f"  - Safety Rate: {'✅' if safety_rate >= 0.95 else '❌'} ({safety_rate:.1%})")
        print(f"\n总结: {'✅ PASS' if passed else '❌ FAIL'}")
        print(f"耗时: {elapsed_time:.2f}s")
        print("=" * 60 + "\n")
        
        return report
    
    def _check_params_safe(self, params: Dict[str, Any]) -> bool:
        """检查参数是否在安全范围内"""
        if not params:
            return True
        
        safe_ranges = {
            'ef': (64, 256),
            'T': (200, 1200),
            'Ncand_max': (500, 2000),
            'rerank_mult': (2, 6)
        }
        
        for param, (min_val, max_val) in safe_ranges.items():
            if param in params:
                if not (min_val <= params[param] <= max_val):
                    return False
        
        return True


def main():
    """主入口"""
    # 创建测试实例
    test = PipelineSanityTest(duration_sec=120, bucket_sec=10, qps=10)
    
    # 运行测试
    report = test.run()
    
    # 保存报告
    os.makedirs('reports', exist_ok=True)
    report_path = 'reports/autotuner_sanity_pipeline.json'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"报告已保存: {report_path}\n")
    
    # 返回退出码
    return 0 if report['result'] == 'PASS' else 1


if __name__ == "__main__":
    sys.exit(main())
