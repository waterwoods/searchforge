#!/usr/bin/env python3
"""
生成 AutoTuner 一页成果报告
包含三维度评估（质量/SLA/成本）和时序曲线
输出 Markdown 和 PDF
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


def evaluate_quality(metrics: Dict) -> Tuple[str, str]:
    """
    评估质量维度
    返回: (颜色等级, 评估文本)
    """
    issues = []
    color = 'green'
    
    # 规则1: p-value < 0.05 显著性
    if metrics['p_value'] < 0.05:
        issues.append('✅ 统计显著 (p<0.05)')
    else:
        issues.append('⚠️ 统计不显著')
        color = 'yellow'
    
    # 规则2: 至少10个桶
    if metrics['buckets'] >= 10:
        issues.append(f'✅ 样本充足 ({metrics["buckets"]}桶)')
    else:
        issues.append(f'⚠️ 样本不足 ({metrics["buckets"]}桶)')
        color = 'yellow'
    
    # 规则3: 召回率提升
    if metrics['delta_recall'] > 0.01:
        issues.append(f'✅ 召回率显著提升 (+{metrics["delta_recall"]:.3f})')
    elif metrics['delta_recall'] >= -0.01:
        issues.append(f'✓ 召回率稳定 ({metrics["delta_recall"]:.3f})')
    else:
        issues.append(f'❌ 召回率下降 ({metrics["delta_recall"]:.3f})')
        color = 'red'
    
    return color, '\n'.join(issues)


def evaluate_sla(metrics: Dict) -> Tuple[str, str]:
    """
    评估 SLA 维度
    返回: (颜色等级, 评估文本)
    """
    issues = []
    color = 'green'
    
    # 规则1: ΔP95 <= +5ms (允许小幅增加)
    if metrics['delta_p95_ms'] <= 5:
        issues.append(f'✅ P95延迟优秀 ({metrics["delta_p95_ms"]:.1f}ms)')
    elif metrics['delta_p95_ms'] <= 20:
        issues.append(f'✓ P95延迟可接受 (+{metrics["delta_p95_ms"]:.1f}ms)')
        color = 'yellow' if color == 'green' else color
    else:
        issues.append(f'❌ P95延迟过高 (+{metrics["delta_p95_ms"]:.1f}ms)')
        color = 'red'
    
    # 规则2: Safety rate >= 0.99
    if metrics['safety_rate'] >= 0.99:
        issues.append(f'✅ 安全率优秀 ({metrics["safety_rate"]:.3f})')
    elif metrics['safety_rate'] >= 0.95:
        issues.append(f'✓ 安全率良好 ({metrics["safety_rate"]:.3f})')
        color = 'yellow' if color == 'green' else color
    else:
        issues.append(f'❌ 安全率不足 ({metrics["safety_rate"]:.3f})')
        color = 'red'
    
    # 规则3: Apply rate >= 0.95
    if metrics['apply_rate'] >= 0.95:
        issues.append(f'✅ 应用率优秀 ({metrics["apply_rate"]:.3f})')
    elif metrics['apply_rate'] >= 0.90:
        issues.append(f'✓ 应用率良好 ({metrics["apply_rate"]:.3f})')
    else:
        issues.append(f'⚠️ 应用率偏低 ({metrics["apply_rate"]:.3f})')
        color = 'yellow' if color == 'green' else color
    
    return color, '\n'.join(issues)


def evaluate_cost(metrics: Dict) -> Tuple[str, str]:
    """
    评估成本维度
    返回: (颜色等级, 评估文本)
    """
    issues = []
    cost = metrics['cost_per_query']
    
    # 成本阈值
    if cost <= 0.00005:
        color = 'green'
        issues.append(f'✅ 成本优秀 (${cost:.6f}/查询)')
    elif cost <= 0.0001:
        color = 'yellow'
        issues.append(f'✓ 成本可接受 (${cost:.6f}/查询)')
    else:
        color = 'red'
        issues.append(f'❌ 成本过高 (${cost:.6f}/查询)')
    
    # 月度成本估算 (假设1M查询/月)
    monthly_cost = cost * 1_000_000
    issues.append(f'📊 月度估算: ${monthly_cost:.2f} (1M查询)')
    
    return color, '\n'.join(issues)


def overall_verdict(quality_color: str, sla_color: str, cost_color: str) -> str:
    """
    综合判定
    全绿=PASS，有黄无红=WARN，含红=FAIL
    """
    colors = [quality_color, sla_color, cost_color]
    
    if all(c == 'green' for c in colors):
        return 'PASS'
    elif 'red' in colors:
        return 'FAIL'
    else:
        return 'WARN'


def generate_markdown_report(data: Dict, plots_info: Dict, output_path: Path):
    """生成 Markdown 报告"""
    scenarios = data['scenarios']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    md = f"""# AutoTuner 一页成果卡：0–1 小时召回率追踪

**生成时间**: {timestamp}  
**数据来源**: {data['source_dir']}  
**实验模式**: {scenarios['A']['mode'].upper()}  
**场景数量**: {len(scenarios)}

---

## 📊 执行摘要

本报告汇总了 AutoTuner 在三个核心场景（A/B/C）下的实验表现，基于 0-1 小时的实时数据，从**质量**、**SLA** 和**成本**三个维度进行全面评估。

### 场景概览

| 场景 | 预设配置 | 时长 | 桶数 | 判定 |
|:----:|:--------|:----:|:----:|:----:|
"""
    
    # 为每个场景计算判定
    verdicts = {}
    for scenario_key in sorted(scenarios.keys()):
        metrics = scenarios[scenario_key]
        q_color, _ = evaluate_quality(metrics)
        s_color, _ = evaluate_sla(metrics)
        c_color, _ = evaluate_cost(metrics)
        verdict = overall_verdict(q_color, s_color, c_color)
        verdicts[scenario_key] = verdict
        
        verdict_emoji = {'PASS': '✅', 'WARN': '⚠️', 'FAIL': '❌'}[verdict]
        md += f"| **{scenario_key}** | {metrics['preset']} | {metrics['duration_sec']}s | {metrics['buckets']} | {verdict_emoji} **{verdict}** |\n"
    
    md += "\n---\n\n"
    
    # 三维度评估详情
    md += "## 🎯 三维度合并评估\n\n"
    
    for scenario_key in sorted(scenarios.keys()):
        metrics = scenarios[scenario_key]
        verdict = verdicts[scenario_key]
        
        md += f"### 场景 {scenario_key}: {metrics['preset']}\n\n"
        md += f"**综合判定**: **{verdict}**\n\n"
        
        # 质量卡
        q_color, q_text = evaluate_quality(metrics)
        md += f"#### 🎯 质量维度 ({q_color.upper()})\n\n"
        md += f"```\n{q_text}\n```\n\n"
        
        # SLA卡
        s_color, s_text = evaluate_sla(metrics)
        md += f"#### ⚡ SLA维度 ({s_color.upper()})\n\n"
        md += f"```\n{s_text}\n```\n\n"
        
        # 成本卡
        c_color, c_text = evaluate_cost(metrics)
        md += f"#### 💰 成本维度 ({c_color.upper()})\n\n"
        md += f"```\n{c_text}\n```\n\n"
        
        # 时序曲线
        if scenario_key in plots_info:
            plot_info = plots_info[scenario_key]
            recall_plot = Path(plot_info['recall_plot']).name
            p95_plot = Path(plot_info['p95_plot']).name
            
            md += f"#### 📈 时序曲线\n\n"
            md += f"**召回率趋势 (0-{plot_info['duration']//60}分钟)**\n\n"
            md += f"![Recall]({recall_plot})\n\n"
            md += f"**P95延迟趋势 (0-{plot_info['duration']//60}分钟)**\n\n"
            md += f"![P95]({p95_plot})\n\n"
        
        md += "---\n\n"
    
    # 总结
    md += "## 🎉 总结\n\n"
    
    pass_count = sum(1 for v in verdicts.values() if v == 'PASS')
    warn_count = sum(1 for v in verdicts.values() if v == 'WARN')
    fail_count = sum(1 for v in verdicts.values() if v == 'FAIL')
    
    md += f"- ✅ **通过**: {pass_count} 个场景\n"
    md += f"- ⚠️ **警告**: {warn_count} 个场景\n"
    md += f"- ❌ **失败**: {fail_count} 个场景\n\n"
    
    overall = 'PASS' if fail_count == 0 and warn_count == 0 else ('WARN' if fail_count == 0 else 'FAIL')
    md += f"**总体判定**: **{overall}**\n\n"
    
    # 关键数字
    avg_delta_recall = sum(m['delta_recall'] for m in scenarios.values()) / len(scenarios)
    avg_delta_p95 = sum(m['delta_p95_ms'] for m in scenarios.values()) / len(scenarios)
    avg_cost = sum(m['cost_per_query'] for m in scenarios.values()) / len(scenarios)
    
    md += f"### 关键数字\n\n"
    md += f"- 平均召回率提升: **+{avg_delta_recall:.3f}**\n"
    md += f"- 平均P95变化: **+{avg_delta_p95:.1f} ms**\n"
    md += f"- 平均每查询成本: **${avg_cost:.6f}**\n"
    md += f"- 总实验桶数: **{sum(m['buckets'] for m in scenarios.values())}**\n\n"
    
    md += "---\n\n"
    md += "*本报告由 AutoTuner 自动生成*\n"
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)
    
    return overall, {
        'avg_delta_recall': avg_delta_recall,
        'avg_delta_p95': avg_delta_p95,
        'avg_cost': avg_cost,
        'pass_count': pass_count,
        'warn_count': warn_count,
        'fail_count': fail_count
    }


def main():
    """主函数"""
    # 读取数据
    base_dir = Path(__file__).parent.parent / 'docs'
    metrics_path = base_dir / 'collected_metrics.json'
    plots_path = base_dir / 'plots' / 'plots_info.json'
    
    if not metrics_path.exists():
        print(f"❌ 未找到指标文件: {metrics_path}")
        return
    
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    plots_info = {}
    if plots_path.exists():
        with open(plots_path, 'r') as f:
            plots_info = json.load(f)
    
    # 生成 Markdown 报告
    output_md = base_dir / 'RESULTS_SUMMARY.md'
    print(f"📝 生成 Markdown 报告...")
    verdict, summary = generate_markdown_report(data, plots_info, output_md)
    print(f"   ✅ {output_md}")
    
    # 打印终端摘要
    total_buckets = sum(m['buckets'] for m in data['scenarios'].values())
    print(f"\n{'='*60}")
    print(f"[曲线] {'/'.join(sorted(data['scenarios'].keys()))} 曲线已生成（总桶数: {total_buckets}）")
    print(f"[汇总] Verdict={verdict} | ΔRecall={summary['avg_delta_recall']:.3f} | ΔP95={summary['avg_delta_p95']:.1f}ms | 成本=${summary['avg_cost']:.6f}")
    print(f"{'='*60}")
    
    return output_md


if __name__ == '__main__':
    main()

