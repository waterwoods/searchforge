#!/usr/bin/env python3
"""
验证 RAG QueryRewriter V2 升级的快速检查脚本
"""

import os
import json


def check_v2_features():
    """检查 V2 新增功能"""
    
    print("=" * 60)
    print("🔍 验证 V2 新增功能")
    print("=" * 60)
    
    results = []
    
    # 1. 检查 JSON 输出
    json_path = "reports/rag_rewrite_ab.json"
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # 检查必需字段
        checks = [
            ("results_a" in data, "包含 Group A 结果"),
            ("results_b" in data, "包含 Group B 结果"),
            ("analysis" in data, "包含分析数据"),
            ("statistical" in data["analysis"], "包含统计分析"),
        ]
        
        # 检查 results_a 的第一条记录
        if data["results_a"]:
            first_result = data["results_a"][0]
            checks.extend([
                ("rewrite_tokens_in" in first_result, "记录输入 Tokens"),
                ("rewrite_tokens_out" in first_result, "记录输出 Tokens"),
                ("rewrite_failed" in first_result, "记录失败状态"),
                ("rewrite_latency_ms" in first_result, "记录改写延迟"),
            ])
        
        # 检查统计数据
        if "statistical" in data["analysis"]:
            stats = data["analysis"]["statistical"]
            checks.extend([
                ("p_value_recall" in stats, "计算 Recall p-value"),
                ("p_value_p95" in stats, "计算 P95 p-value"),
                ("significance_color" in stats, "确定显著性颜色"),
                ("permutation_trials" in stats, "记录 Permutation trials"),
            ])
        
        # 检查成本数据
        if "group_a" in data["analysis"]:
            group_a = data["analysis"]["group_a"]
            checks.extend([
                ("avg_tokens_in" in group_a, "计算平均输入 Tokens"),
                ("avg_tokens_out" in group_a, "计算平均输出 Tokens"),
                ("cost_per_query" in group_a, "计算每查询成本"),
                ("avg_rewrite_latency_ms" in group_a, "计算平均改写延迟"),
                ("failure_rate_pct" in group_a, "计算失败率"),
            ])
        
        print("\n📊 JSON 数据检查:")
        all_passed = True
        for check, desc in checks:
            status = "✓" if check else "✗"
            print(f"  {status} {desc}")
            if not check:
                all_passed = False
        
        results.append(("JSON 数据完整性", all_passed))
    else:
        print(f"  ✗ JSON 文件不存在: {json_path}")
        results.append(("JSON 数据完整性", False))
    
    # 2. 检查 HTML 报告
    html_path = "reports/rag_rewrite_ab.html"
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        checks = [
            ("Recall@10 Delta" in html_content, "显示 Recall Delta"),
            ("p-value" in html_content.lower(), "显示 p-value"),
            ("Avg Tokens" in html_content, "显示 Token 指标"),
            ("Cost per Query" in html_content, "显示成本指标"),
            ("失败 & 重试" in html_content, "显示失败记录"),
            ("统计显著性" in html_content, "显示统计显著性"),
            ("Permutation Test" in html_content, "说明统计方法"),
            ("GREEN" in html_content or "YELLOW" in html_content or "RED" in html_content, 
             "显示显著性颜色"),
        ]
        
        print("\n📄 HTML 报告检查:")
        all_passed = True
        for check, desc in checks:
            status = "✓" if check else "✗"
            print(f"  {status} {desc}")
            if not check:
                all_passed = False
        
        file_size = os.path.getsize(html_path)
        print(f"\n  文件大小: {file_size / 1024:.1f} KB")
        
        results.append(("HTML 报告完整性", all_passed))
    else:
        print(f"  ✗ HTML 文件不存在: {html_path}")
        results.append(("HTML 报告完整性", False))
    
    # 3. 检查关键数字
    if os.path.exists(json_path):
        print("\n📈 关键指标:")
        
        analysis = data["analysis"]
        
        print(f"  Recall 提升: {analysis['deltas']['recall_delta_pct']:+.1f}%")
        print(f"  p-value (Recall): {analysis['statistical']['p_value_recall']:.4f}")
        print(f"  P95 延迟增加: {analysis['deltas']['p95_delta_ms']:+.0f}ms")
        print(f"  每查询成本: ${analysis['group_a']['cost_per_query']:.6f}")
        print(f"  平均 Tokens In: {analysis['group_a']['avg_tokens_in']:.0f}")
        print(f"  平均 Tokens Out: {analysis['group_a']['avg_tokens_out']:.0f}")
        print(f"  失败率: {analysis['group_a']['failure_rate_pct']:.2f}%")
        print(f"  显著性: {analysis['statistical']['significance_color']}")
        
        # 验收标准检查
        checks = [
            (analysis['deltas']['recall_delta_pct'] != 0, "Delta Recall 非零"),
            (analysis['statistical']['p_value_recall'] <= 1.0, "p-value 在有效范围"),
            (analysis['group_a']['avg_tokens_in'] > 0, "Tokens In > 0"),
            (analysis['group_a']['avg_tokens_out'] > 0, "Tokens Out > 0"),
            (analysis['group_a']['cost_per_query'] >= 0, "Cost 非负"),
            (analysis['statistical']['significance_color'] in ['GREEN', 'YELLOW', 'RED'], 
             "显著性颜色有效"),
        ]
        
        print("\n✅ 验收标准:")
        all_passed = True
        for check, desc in checks:
            status = "✓" if check else "✗"
            print(f"  {status} {desc}")
            if not check:
                all_passed = False
        
        results.append(("关键指标有效性", all_passed))
    
    return results


def print_summary(results):
    """打印总结"""
    
    print("\n" + "=" * 60)
    print("📋 验证总结")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status} - {name}")
    
    all_passed = all(passed for _, passed in results)
    
    print()
    if all_passed:
        print("🎉 " + "=" * 54 + " 🎉")
        print("║  V2 升级验证全部通过！统计分析和成本指标已就绪！" + " " * 8 + "║")
        print("🎉 " + "=" * 54 + " 🎉")
        print()
        print("📊 查看报告:")
        print("   HTML: open reports/rag_rewrite_ab.html")
        print("   JSON: cat reports/rag_rewrite_ab.json")
        print()
        print("📖 详细文档:")
        print("   cat RAG_REWRITER_V2_SUMMARY.md")
        return 0
    else:
        print("⚠️  部分验证未通过，请检查上述错误信息")
        return 1


def main():
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "RAG QueryRewriter V2 验证工具" + " " * 19 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    results = check_v2_features()
    return print_summary(results)


if __name__ == "__main__":
    import sys
    sys.exit(main())
