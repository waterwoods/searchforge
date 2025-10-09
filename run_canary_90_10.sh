#!/bin/bash
# Canary Deployment: 90% OFF / 10% ON (rewrite)
# 10-20 minute realistic test with production gates

cd /Users/nanxinli/Documents/dev/searchforge

# Create logs directory if it doesn't exist
mkdir -p logs

LOG_FILE="logs/canary_10pct_run.log"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ⚙️ 灰度模拟验证（10%流量，约10–20分钟）                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  Rewrite OFF: 90% traffic"
echo "  Rewrite ON:  10% traffic (canary)"
echo "  Duration: 10-20 minutes (600-1200s)"
echo "  QPS: 12"
echo "  Buckets: 10s"
echo "  Async: Enabled"
echo "  Cache: Enabled"
echo ""
echo "Logging to: $LOG_FILE"
echo ""

# Create canary test script
cat > /tmp/canary_90_10.py << 'PYEOF'
#!/usr/bin/env python3
import os
import sys
import time
sys.path.insert(0, '/Users/nanxinli/Documents/dev/searchforge')

from labs.run_rag_rewrite_ab_live import *

# Override config for canary deployment
TEST_CONFIG["mode"] = "live"
TEST_CONFIG["duration_per_side_sec"] = 600  # 10 minutes per side (total 20 min)
TEST_CONFIG["bucket_sec"] = 10
TEST_CONFIG["target_qps"] = 12

print("=" * 80)
print("🚀 灰度模拟验证：90/10 流量分配")
print("=" * 80)
print(f"   Group A (灰度 ON):  10% 流量 = 60s @ {TEST_CONFIG['target_qps']} QPS")
print(f"   Group B (控制 OFF): 90% 流量 = 540s @ {TEST_CONFIG['target_qps']} QPS")
print(f"   总时长: {600}s (~10分钟)")
print(f"   优化: Async=True, Cache=True")
print()

start_total = time.time()

# Adjust durations for 90/10 split
TEST_CONFIG_ORIGINAL = TEST_CONFIG.copy()

# Run ON group (canary) - 10% traffic
print("=" * 80)
print("🅰️  Phase 1/2: Running Canary (10% traffic, rewrite=ON)")
print("=" * 80)
TEST_CONFIG["duration_per_side_sec"] = 60
results_canary, _ = run_ab_test_live()

# Run OFF group (control) - 90% traffic  
print("\n" + "=" * 80)
print("🅱️  Phase 2/2: Running Control (90% traffic, rewrite=OFF)")
print("=" * 80)
TEST_CONFIG["duration_per_side_sec"] = 540
_, results_control = run_ab_test_live()

# Restore config and analyze
TEST_CONFIG.update(TEST_CONFIG_ORIGINAL)

total_duration = time.time() - start_total

print("\n" + "=" * 80)
print("📊 统计分析中...")
print("=" * 80)
analysis = analyze_results_production(results_canary, results_control)

# Generate report with custom header
output_html = "reports/rag_rewrite_ab.html"
output_json = "reports/rag_rewrite_ab.json"

# Create custom header for canary test
canary_header = "⚙️ 灰度模拟验证（10%流量，约10–20分钟）"

# Generate HTML with custom header
def generate_canary_html_report(results_a, results_b, analysis, output_path, custom_header):
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mode = "CANARY 10%"
    
    recall_change = analysis["deltas"]["recall_delta_pct"]
    p_value = analysis["statistical"]["p_value_recall"]
    gate_color = analysis["statistical"]["gate_color"]
    
    summary = f"灰度流量（10%）启用查询改写后，Recall@10 {recall_change:+.1f}% (p={p_value:.4f})，" \
              f"P95 延迟 {analysis['deltas']['p95_delta_ms']:+.0f}ms，" \
              f"每查询成本 ${analysis['group_a']['cost_per_query_usd']:.6f}。"
    
    # Force YELLOW if insufficient buckets
    if analysis['statistical']['buckets_used_a'] < 10 or analysis['statistical']['buckets_used_b'] < 10:
        gate_color = "YELLOW"
    
    gate_badges = {
        "GREEN": '<span class="badge-green">✓ 推荐扩大流量</span>',
        "YELLOW": '<span class="badge-yellow">~ 谨慎评估</span>',
        "RED": '<span class="badge-red">✗ 建议回滚</span>',
    }
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{custom_header} - RAG Query Rewriter Canary Test</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f7;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #ff9500 0%, #ff3b30 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .header .canary-tag {{ 
            background: rgba(255,255,255,0.2); 
            padding: 8px 16px; 
            border-radius: 8px; 
            display: inline-block;
            margin-top: 12px;
            font-weight: 600;
        }}
        .header .stats {{ font-size: 16px; margin: 12px 0; font-weight: 600; }}
        .badge-green {{ background: #34c759; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; }}
        .badge-yellow {{ background: #ff9500; color: white; padding: 8px 20px; border-radius: 20px; font-weight: 600; font-size: 14px; }}
        .badge-red {{ background: #ff3b30; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; }}
        .summary-box {{
            background: white;
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 24px;
            border-left: 4px solid #ff9500;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .summary-box h2 {{ margin-bottom: 12px; color: #333; }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .metric-card h3 {{
            font-size: 12px;
            text-transform: uppercase;
            color: #666;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: 700;
            color: #333;
            margin-bottom: 4px;
        }}
        .metric-value.positive {{ color: #34c759; }}
        .metric-value.negative {{ color: #ff3b30; }}
        .metric-subtitle {{ font-size: 13px; color: #888; }}
        .section {{
            background: white;
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .section h2 {{ margin-bottom: 16px; color: #333; }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
            font-size: 13px;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding: 24px;
            font-size: 13px;
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>{custom_header}</h1>
        <div class="canary-tag">🔬 RAG Query Rewriter - Canary Deployment Test</div>
        <p style="margin-top: 12px;">{mode} MODE | {gate_badges[gate_color]}</p>
        <div class="stats">
            📊 Samples: {analysis['group_a']['n_samples']:,} (ON-10%), {analysis['group_b']['n_samples']:,} (OFF-90%) | 
            🗂️ Buckets: {analysis['statistical']['buckets_used_a']} (ON), {analysis['statistical']['buckets_used_b']} (OFF)
        </div>
        <p style="opacity: 0.9; margin-top: 8px;">生成时间: {timestamp}</p>
    </div>
    
    <div class="summary-box">
        <h2>📊 灰度测试总结</h2>
        <p style="font-size: 16px;">{summary}</p>
        <p style="font-size: 13px; color: #666; margin-top: 12px;">
            统计方法: Permutation Test ({analysis['statistical']['permutation_trials']} trials) | 
            分桶数: {analysis['statistical']['buckets_used_a']} (A), {analysis['statistical']['buckets_used_b']} (B) |
            样本数: {analysis['group_a']['n_samples']} (A-10%), {analysis['group_b']['n_samples']} (B-90%)
        </p>
    </div>
    
    <h2 style="margin-bottom: 16px;">核心指标</h2>
    <div class="metrics-grid">
        <div class="metric-card">
            <h3>Recall@10 Delta</h3>
            <div class="metric-value {'positive' if analysis['deltas']['recall_delta'] > 0 else 'negative'}">
                {analysis['deltas']['recall_delta_pct']:+.1f}%
            </div>
            <div class="metric-subtitle">p = {analysis['statistical']['p_value_recall']:.4f}</div>
        </div>
        <div class="metric-card">
            <h3>P95 Latency Delta</h3>
            <div class="metric-value {'negative' if analysis['deltas']['p95_delta_ms'] > 0 else 'positive'}">
                {analysis['deltas']['p95_delta_ms']:+.0f}ms
            </div>
            <div class="metric-subtitle">p = {analysis['statistical']['p_value_p95']:.4f}</div>
        </div>
        <div class="metric-card">
            <h3>Cost per Query</h3>
            <div class="metric-value" style="font-size: 24px;">
                ${analysis['group_a']['cost_per_query_usd']:.6f}
            </div>
            <div class="metric-subtitle">ON vs ${analysis['group_b']['cost_per_query_usd']:.6f} OFF</div>
        </div>
        <div class="metric-card">
            <h3>Cache Hit Rate</h3>
            <div class="metric-value {'positive' if analysis['group_a']['cache_hit_rate_pct'] > 90 else ''}" style="font-size: 28px;">
                {analysis['group_a']['cache_hit_rate_pct']:.1f}%
            </div>
            <div class="metric-subtitle">Async: {analysis['group_a']['async_hit_rate_pct']:.1f}%</div>
        </div>
    </div>
    
    <div class="section">
        <h2>📈 Cost & SLA Analysis</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>ON (A - 10%)</th>
                <th>OFF (B - 90%)</th>
                <th>Delta</th>
            </tr>
            <tr>
                <td>Avg Tokens In</td>
                <td>{analysis['group_a']['avg_tokens_in']:.1f}</td>
                <td>0</td>
                <td>+{analysis['group_a']['avg_tokens_in']:.1f}</td>
            </tr>
            <tr>
                <td>Avg Tokens Out</td>
                <td>{analysis['group_a']['avg_tokens_out']:.1f}</td>
                <td>0</td>
                <td>+{analysis['group_a']['avg_tokens_out']:.1f}</td>
            </tr>
            <tr>
                <td>Cost per Query (USD)</td>
                <td>${analysis['group_a']['cost_per_query_usd']:.6f}</td>
                <td>${analysis['group_b']['cost_per_query_usd']:.6f}</td>
                <td>+${analysis['deltas']['cost_delta_usd']:.6f}</td>
            </tr>
            <tr>
                <td>Avg Rewrite Latency (ms)</td>
                <td>{analysis['group_a']['avg_rewrite_latency_ms']:.1f}</td>
                <td>0</td>
                <td>+{analysis['group_a']['avg_rewrite_latency_ms']:.1f}</td>
            </tr>
            <tr>
                <td>P95 E2E Latency (ms)</td>
                <td>{analysis['group_a']['p95_latency_ms']:.1f}</td>
                <td>{analysis['group_b']['p95_latency_ms']:.1f}</td>
                <td>{analysis['deltas']['p95_delta_ms']:+.1f}</td>
            </tr>
            <tr style="background: #fffacd;">
                <td><strong>Async Hit Rate</strong></td>
                <td><strong>{analysis['group_a']['async_hit_rate_pct']:.1f}%</strong></td>
                <td>-</td>
                <td>-</td>
            </tr>
            <tr style="background: #fffacd;">
                <td><strong>Cache Hit Rate</strong></td>
                <td><strong>{analysis['group_a']['cache_hit_rate_pct']:.1f}%</strong></td>
                <td>-</td>
                <td>-</td>
            </tr>
            <tr>
                <td><strong>Failure Rate</strong></td>
                <td><strong>{analysis['group_a']['failure_rate_pct']:.2f}%</strong></td>
                <td>0%</td>
                <td>+{analysis['group_a']['failure_rate_pct']:.2f}%</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>⚠️ Failures & Retries</h2>
"""
    
    if analysis.get('failures', []):
        html += """        <table>
            <tr>
                <th>Original Query</th>
                <th>Reason</th>
                <th>Retried</th>
                <th>Latency (ms)</th>
            </tr>
"""
        for f in analysis['failures'][:5]:
            html += f"""            <tr>
                <td>{f['query_original'][:50]}...</td>
                <td>{f.get('rewrite_error', 'Unknown')[:50]}</td>
                <td>{'✓' if f.get('rewrite_retried', False) else '✗'}</td>
                <td>{f.get('rewrite_latency_ms', 0):.0f}</td>
            </tr>
"""
        html += """        </table>
"""
    else:
        html += """        <p style="color: #34c759; font-weight: 600;">✓ No failures detected</p>
"""
    
    html += f"""    </div>
    
    <div class="footer">
        <p><strong>Pricing:</strong> Input ${analysis['pricing']['input_usd_per_1k']:.5f}/1K tokens | 
           Output ${analysis['pricing']['output_usd_per_1k']:.5f}/1K tokens</p>
        <p style="margin-top: 8px;">Mode: {mode} | Generated: {timestamp}</p>
        <p style="margin-top: 8px; color: #999;">Next Step: 如门禁通过，建议扩大至 50% 流量验证</p>
    </div>
</div>
</body>
</html>
"""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Save JSON
    import json
    json_path = output_path.replace('.html', '.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        def make_json_safe(obj):
            safe = {}
            for k, v in obj.items():
                if k in ['results', 'rewrite_metadata']:
                    continue
                elif isinstance(v, (int, float, str, bool, type(None))):
                    safe[k] = v
                else:
                    safe[k] = str(v)
            return safe
        
        json.dump({
            "test_type": "canary_10_pct",
            "results_a": [make_json_safe(r) for r in results_a],
            "results_b": [make_json_safe(r) for r in results_b],
            "analysis": {
                "group_a": analysis["group_a"],
                "group_b": analysis["group_b"],
                "deltas": analysis["deltas"],
                "statistical": analysis["statistical"],
                "pricing": analysis["pricing"],
                "failures_count": len(analysis.get("failures", [])),
            },
            "config": TEST_CONFIG,
            "timestamp": timestamp,
        }, f, indent=2, ensure_ascii=False)

generate_canary_html_report(results_canary, results_control, analysis, output_html, canary_header)

print(f"\n💾 报告已生成:")
print(f"  HTML: {output_html}")
print(f"  JSON: {output_json}")
print(f"⏱️  总运行时间: {total_duration:.1f}s")

# Print terminal summary in Chinese
print("\n" + "=" * 80)
print("🎯 灰度测试总结 (10% 流量)")
print("=" * 80)

delta_recall = analysis['deltas']['recall_delta']
delta_recall_pct = analysis['deltas']['recall_delta_pct']
p_value = analysis['statistical']['p_value_recall']
delta_p95 = analysis['deltas']['p95_delta_ms']
fail_rate = analysis['group_a']['failure_rate_pct'] / 100
cost = analysis['group_a']['cost_per_query_usd']
async_hit = analysis['group_a']['async_hit_rate_pct']
cache_hit = analysis['group_a']['cache_hit_rate_pct']

print(f"\n【核心指标】")
print(f"  ΔRecall@10: {delta_recall_pct:+.2f}% (绝对值: {delta_recall:+.4f})")
print(f"  ΔP95 延迟: {delta_p95:+.1f}ms")
print(f"  Cache Hit: {cache_hit:.1f}%")
print(f"  Async Hit: {async_hit:.1f}%")
print(f"  失败率: {fail_rate:.2%}")

print(f"\n【生产门禁检查】")

gates_passed = []
gates_failed = []

# Gate 1: Recall improvement
if delta_recall >= 0.05:
    gates_passed.append(f"✓ ΔRecall≥5% ({delta_recall:.4f})")
else:
    gates_failed.append(f"✗ ΔRecall≥5% ({delta_recall:.4f})")

# Gate 2: Statistical significance
if p_value < 0.05:
    gates_passed.append(f"✓ p<0.05 ({p_value:.4f})")
else:
    gates_failed.append(f"✗ p<0.05 ({p_value:.4f})")

# Gate 3: P95 latency
if delta_p95 <= 5:
    gates_passed.append(f"✓ ΔP95≤5ms ({delta_p95:.1f}ms)")
else:
    gates_failed.append(f"✗ ΔP95≤5ms ({delta_p95:.1f}ms)")

# Gate 4: Failure rate
if fail_rate < 0.01:
    gates_passed.append(f"✓ 失败率<1% ({fail_rate:.2%})")
else:
    gates_failed.append(f"✗ 失败率<1% ({fail_rate:.2%})")

# Gate 5: Cost
if cost <= 0.00005:
    gates_passed.append(f"✓ 成本≤$0.00005 (${cost:.6f})")
else:
    gates_failed.append(f"✗ 成本≤$0.00005 (${cost:.6f})")

for gate in gates_passed:
    print(f"  {gate}")
for gate in gates_failed:
    print(f"  {gate}")

# Additional metrics
print(f"\n【附加指标】")
print(f"  Cache Hit Rate: {cache_hit:.1f}% {'(✓ >90%)' if cache_hit > 90 else '(目标 >90%)'}")
print(f"  Async Hit Rate: {async_hit:.1f}%")
print(f"  每查询成本: ${cost:.6f}")
print(f"  平均 Tokens In: {analysis['group_a']['avg_tokens_in']:.1f}")
print(f"  平均 Tokens Out: {analysis['group_a']['avg_tokens_out']:.1f}")

# Overall verdict
all_gates_pass = len(gates_failed) == 0
cache_healthy = cache_hit > 90

print("\n" + "=" * 80)
if all_gates_pass and cache_healthy:
    print("✅ PASS - 所有门禁通过 + 缓存健康")
    print(f"   ΔRecall={delta_recall_pct:+.1f}%, ΔP95={delta_p95:+.1f}ms, p={p_value:.4f}")
    print(f"   cost=${cost:.6f}, fail={fail_rate:.2%}, cache_hit={cache_hit:.1f}%")
    print(f"   🎯 建议: 扩大至 50% 流量继续验证")
    verdict = "PASS"
    exit_code = 0
elif all_gates_pass:
    print("⚠️  WARN - 门禁通过但缓存命中率偏低")
    print(f"   cache_hit={cache_hit:.1f}% (目标 >90%)")
    print(f"   建议: 检查缓存配置或继续观察")
    verdict = "WARN"
    exit_code = 0
else:
    print("❌ FAIL - 部分门禁未通过")
    print(f"   未通过项: {len(gates_failed)}/{len(gates_passed) + len(gates_failed)}")
    print(f"   建议: 回滚或优化后重新测试")
    verdict = "FAIL"
    exit_code = 1

print("=" * 80)

sys.exit(exit_code)
PYEOF

# Run with logging
python /tmp/canary_90_10.py 2>&1 | tee "$LOG_FILE"
exit_code=${PIPESTATUS[0]}

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Test completed. Exit code: $exit_code                                 ║"
echo "║  Full log: $LOG_FILE                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"

exit $exit_code
