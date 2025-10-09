#!/usr/bin/env python3
"""
生成步长衰减图 (Step Damping Visualization)

展示自适应步长随调整次数的变化
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 无 GUI 后端

def generate_step_damping_plot():
    """生成步长衰减图表"""
    
    # 定义不同场景的步长序列
    scenarios = {
        "正常衰减 (连续调整)": {
            "steps": [32, 16, 8, 4, 2, 1],
            "color": "#2E86AB",
            "marker": "o",
            "linestyle": "-"
        },
        "记忆命中后 (初始×0.5)": {
            "steps": [16, 8, 4, 2, 1, 0.5],
            "color": "#A23B72",
            "marker": "s",
            "linestyle": "--"
        },
        "连续改进 (步长增加)": {
            "steps": [32, 32, 40, 40, 48, 48],
            "color": "#F18F01",
            "marker": "^",
            "linestyle": "-."
        },
        "出现倒退 (步长骤减)": {
            "steps": [32, 32, 16, 16, 8, 8],
            "color": "#C73E1D",
            "marker": "v",
            "linestyle": ":"
        }
    }
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # === 左图：步长变化曲线 ===
    for label, config in scenarios.items():
        steps = config["steps"]
        adjustments = list(range(len(steps)))
        
        ax1.plot(
            adjustments,
            steps,
            color=config["color"],
            marker=config["marker"],
            markersize=10,
            linewidth=2.5,
            linestyle=config["linestyle"],
            label=label,
            alpha=0.9
        )
    
    ax1.set_xlabel("调整次数", fontsize=14, fontweight='bold')
    ax1.set_ylabel("步长 (step size)", fontsize=14, fontweight='bold')
    ax1.set_title("自适应步长衰减曲线", fontsize=16, fontweight='bold', pad=20)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(fontsize=11, loc='upper right', framealpha=0.9)
    ax1.set_ylim(bottom=0)
    
    # 添加参考线
    ax1.axhline(y=32, color='gray', linestyle=':', alpha=0.5, linewidth=1)
    ax1.text(5.2, 33, 'base_step=32', fontsize=9, color='gray')
    
    # === 右图：累计调整量 ===
    for label, config in scenarios.items():
        steps = config["steps"]
        cumulative = []
        total = 0
        for step in steps:
            total += step
            cumulative.append(total)
        
        adjustments = list(range(len(cumulative)))
        
        ax2.plot(
            adjustments,
            cumulative,
            color=config["color"],
            marker=config["marker"],
            markersize=10,
            linewidth=2.5,
            linestyle=config["linestyle"],
            label=label,
            alpha=0.9
        )
    
    ax2.set_xlabel("调整次数", fontsize=14, fontweight='bold')
    ax2.set_ylabel("累计调整量", fontsize=14, fontweight='bold')
    ax2.set_title("累计参数变化", fontsize=16, fontweight='bold', pad=20)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend(fontsize=11, loc='upper left', framealpha=0.9)
    ax2.set_ylim(bottom=0)
    
    # 整体布局
    plt.tight_layout()
    
    # 保存图表
    output_path = "/Users/nanxinli/Documents/dev/searchforge/docs/figs/step_damping.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ 图表已保存到: {output_path}")
    
    plt.close()


def generate_comparison_plot():
    """生成步长策略对比图"""
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 不同策略的步长序列
    strategies = {
        "指数衰减 (×0.5)": [32, 16, 8, 4, 2, 1],
        "线性衰减 (-8)": [32, 24, 16, 8, 0, -8],
        "固定步长": [32, 32, 32, 32, 32, 32],
        "自适应 (连续改进×1.25)": [32, 32, 40, 50, 62, 77]
    }
    
    colors = ["#2E86AB", "#A23B72", "#F18F01", "#06A77D"]
    markers = ["o", "s", "^", "d"]
    
    for (label, steps), color, marker in zip(strategies.items(), colors, markers):
        adjustments = list(range(len(steps)))
        ax.plot(
            adjustments,
            steps,
            color=color,
            marker=marker,
            markersize=12,
            linewidth=3,
            label=label,
            alpha=0.85
        )
    
    # 标注问题区域
    ax.axhspan(-10, 0, alpha=0.2, color='red', label='负步长区域 (错误!)')
    ax.axhspan(50, 100, alpha=0.1, color='orange', label='过大步长 (可能过冲)')
    
    ax.set_xlabel("调整次数", fontsize=14, fontweight='bold')
    ax.set_ylabel("步长", fontsize=14, fontweight='bold')
    ax.set_title("不同步长策略对比", fontsize=18, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=12, loc='upper left', framealpha=0.95)
    ax.set_ylim(-12, 85)
    
    plt.tight_layout()
    
    output_path = "/Users/nanxinli/Documents/dev/searchforge/docs/figs/step_strategy_comparison.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ 对比图已保存到: {output_path}")
    
    plt.close()


def generate_hysteresis_plot():
    """生成滞回带示意图"""
    
    import numpy as np
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # 模拟 P95 延迟变化
    time_ticks = np.arange(0, 50, 1)
    
    # 真实 P95（带噪声）
    np.random.seed(42)
    noise = np.random.normal(0, 15, len(time_ticks))
    base_p95 = 500 + 50 * np.sin(time_ticks * 0.3) + noise
    
    # SLO 阈值
    slo_target = 500
    slo_upper = 600
    slo_lower = 400
    
    # 滞回带
    hyst_upper = 550
    hyst_lower = 450
    
    # 绘制曲线
    ax.plot(time_ticks, base_p95, color='#2E86AB', linewidth=2.5, label='实际 P95 延迟', alpha=0.8)
    
    # SLO 线
    ax.axhline(y=slo_target, color='green', linestyle='-', linewidth=2, label='SLO 目标 (500ms)', alpha=0.7)
    ax.axhline(y=slo_upper, color='red', linestyle='--', linewidth=2, label='SLO 上界 (600ms)', alpha=0.7)
    ax.axhline(y=slo_lower, color='blue', linestyle='--', linewidth=2, label='SLO 下界 (400ms)', alpha=0.7)
    
    # 滞回带
    ax.axhspan(hyst_lower, hyst_upper, alpha=0.2, color='yellow', label='滞回带 (±50ms)')
    
    # 标注动作点
    action_points = []
    last_action = None
    cooldown = 0
    
    for i, p95 in enumerate(base_p95):
        if cooldown > 0:
            cooldown -= 1
            continue
        
        if p95 > hyst_upper and (last_action != 'drop_ef'):
            action_points.append((i, p95, 'drop_ef', 'red'))
            last_action = 'drop_ef'
            cooldown = 5
        elif p95 < hyst_lower and (last_action != 'bump_ef'):
            action_points.append((i, p95, 'bump_ef', 'green'))
            last_action = 'bump_ef'
            cooldown = 5
    
    # 绘制动作标记
    for x, y, action, color in action_points:
        ax.scatter(x, y, s=200, c=color, marker='*', edgecolors='black', linewidths=1.5, zorder=5)
        ax.annotate(
            action,
            xy=(x, y),
            xytext=(x, y + 40),
            fontsize=9,
            color=color,
            weight='bold',
            ha='center',
            arrowprops=dict(arrowstyle='->', color=color, lw=1.5)
        )
    
    ax.set_xlabel("时间 (ticks)", fontsize=14, fontweight='bold')
    ax.set_ylabel("P95 延迟 (ms)", fontsize=14, fontweight='bold')
    ax.set_title("滞回带机制示意图", fontsize=18, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=11, loc='upper right', framealpha=0.95)
    ax.set_ylim(350, 650)
    
    plt.tight_layout()
    
    output_path = "/Users/nanxinli/Documents/dev/searchforge/docs/figs/hysteresis_demo.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ 滞回带图已保存到: {output_path}")
    
    plt.close()


if __name__ == "__main__":
    print("🎨 生成 AutoTuner 决策算法可视化图表...")
    
    try:
        generate_step_damping_plot()
        generate_comparison_plot()
        generate_hysteresis_plot()
        
        print("\n✅ 所有图表生成完成！")
        print("\n生成的文件：")
        print("  1. step_damping.png - 自适应步长衰减曲线")
        print("  2. step_strategy_comparison.png - 步长策略对比")
        print("  3. hysteresis_demo.png - 滞回带机制示意图")
        
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        print("\n请确保安装了 matplotlib:")
        print("  pip install matplotlib")
