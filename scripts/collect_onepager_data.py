#!/usr/bin/env python3
"""
收集 AutoTuner 实验的 one_pager 数据
从 ~/Downloads/autotuner_runs/ 目录递归查找所有场景数据
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def find_latest_scenario_data(base_dir: Path) -> Dict[str, Dict]:
    """
    从 base_dir 递归查找所有场景的 one_pager.json
    返回格式: {'A': {...}, 'B': {...}, 'C': {...}}
    """
    scenarios = {}
    
    # 遍历所有子目录
    for root, dirs, files in os.walk(base_dir):
        root_path = Path(root)
        
        # 查找 one_pager.json
        if 'one_pager.json' in files:
            json_path = root_path / 'one_pager.json'
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                
                scenario = data.get('scenario')
                if scenario:
                    # 提取时间戳（从路径中）
                    timestamp = None
                    for part in root_path.parts:
                        if part.startswith('20251008'):
                            timestamp = part
                            break
                    
                    # 如果已有该场景，比较时间戳选最新的
                    if scenario not in scenarios or (timestamp and timestamp > scenarios[scenario].get('timestamp', '')):
                        scenarios[scenario] = {
                            'data': data,
                            'path': str(json_path),
                            'timestamp': timestamp or '',
                            'root_dir': str(root_path.parent.parent)
                        }
            except Exception as e:
                print(f"⚠️  读取 {json_path} 失败: {e}")
    
    return scenarios


def extract_metrics(scenario_data: Dict) -> Dict:
    """提取关键指标"""
    data = scenario_data['data']
    comparison = data.get('comparison', {})
    
    return {
        'scenario': data.get('scenario', 'Unknown'),
        'preset': data.get('preset', 'Unknown'),
        'mode': data.get('mode', 'unknown'),
        'duration_sec': data.get('duration_sec', 0),
        'buckets': comparison.get('run_params', {}).get('buckets_per_side', 0),
        'delta_recall': comparison.get('delta_recall', 0),
        'delta_p95_ms': comparison.get('delta_p95_ms', 0),
        'p_value': comparison.get('p_value', 1.0),
        'safety_rate': comparison.get('safety_rate', 0),
        'apply_rate': comparison.get('apply_rate', 0),
        'cost_per_query': estimate_cost(data),
        'qps': data.get('qps', 0),
        'timestamp': scenario_data.get('timestamp', ''),
        'path': scenario_data.get('path', ''),
    }


def estimate_cost(data: Dict) -> float:
    """
    估算每查询成本（简化模型）
    基于参数变化频率和复杂度
    """
    multi_stats = data.get('multi_knob', {}).get('metrics', {}).get('stats', {})
    params_applied = multi_stats.get('PARAMS_APPLIED', 0)
    duration = data.get('duration_sec', 1)
    qps = data.get('qps', 1)
    
    total_queries = duration * qps
    if total_queries == 0:
        return 0.0
    
    # 每次参数调整的成本（假设）
    apply_cost = 0.00001  # $0.00001 per apply
    baseline_cost = 0.00003  # baseline query cost
    
    cost = baseline_cost + (params_applied / total_queries) * apply_cost
    return cost


def main():
    """主函数"""
    base_dir = Path.home() / 'Downloads' / 'autotuner_runs'
    
    if not base_dir.exists():
        print(f"❌ 目录不存在: {base_dir}")
        return
    
    print(f"🔍 扫描目录: {base_dir}")
    scenarios = find_latest_scenario_data(base_dir)
    
    if not scenarios:
        print("❌ 未找到任何场景数据")
        return
    
    print(f"✅ 找到 {len(scenarios)} 个场景: {', '.join(sorted(scenarios.keys()))}")
    
    # 提取并汇总指标
    results = {}
    for scenario_key in sorted(scenarios.keys()):
        metrics = extract_metrics(scenarios[scenario_key])
        results[scenario_key] = metrics
        print(f"\n📊 场景 {scenario_key}:")
        print(f"   模式: {metrics['mode']}")
        print(f"   时长: {metrics['duration_sec']}s")
        print(f"   ΔRecall: {metrics['delta_recall']:.4f}")
        print(f"   ΔP95: {metrics['delta_p95_ms']:.2f} ms")
        print(f"   P-value: {metrics['p_value']:.4f}")
    
    # 保存结果
    output_path = Path(__file__).parent.parent / 'docs' / 'collected_metrics.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'source_dir': str(base_dir),
            'scenarios': results
        }, f, indent=2)
    
    print(f"\n✅ 数据已保存到: {output_path}")
    return results


if __name__ == '__main__':
    main()

