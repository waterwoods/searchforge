#!/usr/bin/env python3
"""
生成 AutoTuner 一页 PDF 报告
使用 matplotlib 创建专业的单页 PDF
"""

import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False


def get_color(color_name: str) -> Tuple[float, float, float]:
    """获取颜色RGB值"""
    colors = {
        'green': (0.2, 0.7, 0.3),
        'yellow': (0.9, 0.7, 0.1),
        'red': (0.9, 0.2, 0.2),
        'blue': (0.2, 0.4, 0.8),
        'gray': (0.5, 0.5, 0.5)
    }
    return colors.get(color_name, (0.5, 0.5, 0.5))


def evaluate_scenario(metrics: Dict) -> Dict:
    """评估单个场景"""
    # 质量
    q_color = 'green'
    if metrics['p_value'] >= 0.05:
        q_color = 'yellow'
    if metrics['buckets'] < 10:
        q_color = 'yellow'
    if metrics['delta_recall'] < -0.01:
        q_color = 'red'
    
    # SLA
    s_color = 'green'
    if metrics['delta_p95_ms'] > 5:
        s_color = 'yellow'
    if metrics['delta_p95_ms'] > 20:
        s_color = 'red'
    if metrics['safety_rate'] < 0.99:
        s_color = 'yellow'
    if metrics['safety_rate'] < 0.95:
        s_color = 'red'
    
    # 成本
    c_color = 'green' if metrics['cost_per_query'] <= 0.00005 else 'yellow'
    if metrics['cost_per_query'] > 0.0001:
        c_color = 'red'
    
    # 总判定
    colors = [q_color, s_color, c_color]
    if all(c == 'green' for c in colors):
        verdict = 'PASS'
    elif 'red' in colors:
        verdict = 'FAIL'
    else:
        verdict = 'WARN'
    
    return {
        'quality_color': q_color,
        'sla_color': s_color,
        'cost_color': c_color,
        'verdict': verdict
    }


def create_pdf_report(data: Dict, output_path: Path):
    """创建PDF报告"""
    scenarios = data['scenarios']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 创建PDF
    with PdfPages(output_path) as pdf:
        fig = plt.figure(figsize=(11, 8.5))  # Letter size
        fig.suptitle('AutoTuner 一页成果卡：0–1 小时召回率追踪', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        # 添加页眉信息
        header_text = f'生成时间: {timestamp} | 数据来源: ~/Downloads/autotuner_runs/ | 实验模式: LIVE'
        fig.text(0.5, 0.94, header_text, ha='center', fontsize=9, color='gray')
        
        # 创建子图布局
        gs = fig.add_gridspec(5, 3, left=0.08, right=0.92, top=0.88, bottom=0.08,
                              hspace=0.4, wspace=0.3)
        
        # 场景概览表
        ax_table = fig.add_subplot(gs[0, :])
        ax_table.axis('off')
        
        table_data = [['场景', '预设配置', '时长', '桶数', 'ΔRecall', 'ΔP95', 'P-value', '判定']]
        
        for scenario_key in sorted(scenarios.keys()):
            metrics = scenarios[scenario_key]
            eval_result = evaluate_scenario(metrics)
            
            verdict_symbol = {'PASS': '✅', 'WARN': '⚠️', 'FAIL': '❌'}[eval_result['verdict']]
            row = [
                f'{scenario_key}',
                f'{metrics["preset"][:20]}...' if len(metrics["preset"]) > 20 else metrics["preset"],
                f'{metrics["duration_sec"]}s',
                f'{metrics["buckets"]}',
                f'+{metrics["delta_recall"]:.3f}',
                f'+{metrics["delta_p95_ms"]:.1f}ms',
                f'{metrics["p_value"]:.3f}',
                f'{verdict_symbol} {eval_result["verdict"]}'
            ]
            table_data.append(row)
        
        table = ax_table.table(cellText=table_data, cellLoc='center', loc='center',
                               colWidths=[0.08, 0.25, 0.08, 0.08, 0.12, 0.12, 0.12, 0.15])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # 设置表头样式
        for i in range(len(table_data[0])):
            cell = table[(0, i)]
            cell.set_facecolor('#4472C4')
            cell.set_text_props(weight='bold', color='white')
        
        # 设置数据行样式
        for i in range(1, len(table_data)):
            for j in range(len(table_data[i])):
                cell = table[(i, j)]
                cell.set_facecolor('#F2F2F2' if i % 2 == 0 else 'white')
        
        ax_table.text(0.5, 1.2, '📊 场景概览', transform=ax_table.transAxes,
                     fontsize=12, fontweight='bold', ha='center')
        
        # 为每个场景创建三维度卡片
        row_offset = 1
        for idx, scenario_key in enumerate(sorted(scenarios.keys())):
            metrics = scenarios[scenario_key]
            eval_result = evaluate_scenario(metrics)
            
            col = idx
            
            # 场景标题
            ax_title = fig.add_subplot(gs[row_offset, col])
            ax_title.axis('off')
            ax_title.text(0.5, 0.5, f'场景 {scenario_key}\n{eval_result["verdict"]}', 
                         transform=ax_title.transAxes,
                         fontsize=11, fontweight='bold', ha='center', va='center',
                         bbox=dict(boxstyle='round,pad=0.5', 
                                  facecolor=get_color(eval_result['verdict'].lower() if eval_result['verdict'] != 'WARN' else 'yellow'),
                                  alpha=0.3))
            
            # 质量卡
            ax_q = fig.add_subplot(gs[row_offset + 1, col])
            ax_q.axis('off')
            q_color = get_color(eval_result['quality_color'])
            ax_q.add_patch(FancyBboxPatch((0.05, 0.05), 0.9, 0.9, 
                                         boxstyle="round,pad=0.05", 
                                         facecolor=q_color, alpha=0.2,
                                         edgecolor=q_color, linewidth=2))
            
            q_text = f"🎯 质量\n"
            q_text += f"p={metrics['p_value']:.3f}\n"
            q_text += f"桶数={metrics['buckets']}\n"
            q_text += f"ΔRecall=+{metrics['delta_recall']:.3f}"
            
            ax_q.text(0.5, 0.5, q_text, transform=ax_q.transAxes,
                     fontsize=8, ha='center', va='center')
            
            # SLA卡
            ax_s = fig.add_subplot(gs[row_offset + 2, col])
            ax_s.axis('off')
            s_color = get_color(eval_result['sla_color'])
            ax_s.add_patch(FancyBboxPatch((0.05, 0.05), 0.9, 0.9,
                                         boxstyle="round,pad=0.05",
                                         facecolor=s_color, alpha=0.2,
                                         edgecolor=s_color, linewidth=2))
            
            s_text = f"⚡ SLA\n"
            s_text += f"ΔP95=+{metrics['delta_p95_ms']:.1f}ms\n"
            s_text += f"安全={metrics['safety_rate']:.3f}\n"
            s_text += f"应用={metrics['apply_rate']:.3f}"
            
            ax_s.text(0.5, 0.5, s_text, transform=ax_s.transAxes,
                     fontsize=8, ha='center', va='center')
            
            # 成本卡
            ax_c = fig.add_subplot(gs[row_offset + 3, col])
            ax_c.axis('off')
            c_color = get_color(eval_result['cost_color'])
            ax_c.add_patch(FancyBboxPatch((0.05, 0.05), 0.9, 0.9,
                                         boxstyle="round,pad=0.05",
                                         facecolor=c_color, alpha=0.2,
                                         edgecolor=c_color, linewidth=2))
            
            monthly_cost = metrics['cost_per_query'] * 1_000_000
            c_text = f"💰 成本\n"
            c_text += f"${metrics['cost_per_query']:.6f}/查询\n"
            c_text += f"月估算: ${monthly_cost:.2f}\n"
            c_text += f"(1M查询)"
            
            ax_c.text(0.5, 0.5, c_text, transform=ax_c.transAxes,
                     fontsize=8, ha='center', va='center')
        
        # 添加页脚
        avg_delta_recall = sum(m['delta_recall'] for m in scenarios.values()) / len(scenarios)
        avg_delta_p95 = sum(m['delta_p95_ms'] for m in scenarios.values()) / len(scenarios)
        total_buckets = sum(m['buckets'] for m in scenarios.values())
        
        footer = f'总结: 平均召回率提升 +{avg_delta_recall:.3f} | 平均P95变化 +{avg_delta_p95:.1f}ms | 总桶数 {total_buckets}'
        fig.text(0.5, 0.03, footer, ha='center', fontsize=9, style='italic')
        
        fig.text(0.5, 0.01, '*本报告由 AutoTuner 自动生成*', 
                ha='center', fontsize=8, color='gray')
        
        # 保存到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()


def main():
    """主函数"""
    # 读取数据
    base_dir = Path(__file__).parent.parent / 'docs'
    metrics_path = base_dir / 'collected_metrics.json'
    
    if not metrics_path.exists():
        print(f"❌ 未找到指标文件: {metrics_path}")
        return
    
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    # 生成PDF
    output_pdf = base_dir / 'one_pager_autotuner.pdf'
    print(f"📄 生成 PDF 报告...")
    create_pdf_report(data, output_pdf)
    print(f"   ✅ {output_pdf}")
    
    return output_pdf


if __name__ == '__main__':
    main()

