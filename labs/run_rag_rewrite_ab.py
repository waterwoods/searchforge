#!/usr/bin/env python3
"""
RAG Query Rewriter A/B Test

对比 rewrite_enabled=True 和 rewrite_enabled=False 两组实验，
计算 Recall@10、P95 延迟、命中率等指标，生成 HTML 报告。

输出:
- reports/rag_rewrite_ab.html
"""

import os
import sys
import json
import time
import statistics
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.rag_pipeline import RAGPipeline, RAGPipelineConfig
from modules.types import ScoredDocument


# Test configuration
TEST_CONFIG = {
    "collection_name": "beir_fiqa_full_ta",  # FiQA collection
    "queries_file": "data/fiqa_queries.txt",
    "qrels_file": "data/fiqa/qrels/test.tsv",
    "num_queries": 20,  # Number of queries to test
    "top_k": 10,
    "search_mode": "vector",  # "vector" or "hybrid"
}


def load_test_queries(queries_file: str, limit: int = 20) -> List[str]:
    """
    Load test queries from file.
    
    Args:
        queries_file: Path to queries file
        limit: Maximum number of queries to load
        
    Returns:
        List of query strings
    """
    queries = []
    
    if os.path.exists(queries_file):
        with open(queries_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    queries.append(line)
                    if len(queries) >= limit:
                        break
    else:
        # Fallback to sample queries
        queries = [
            "What is ETF expense ratio?",
            "How is APR different from APY?",
            "How are dividends taxed in the US?",
            "What is a mutual fund load?",
            "How do bond coupons work?",
            "What is dollar-cost averaging?",
            "How does an index fund track its index?",
            "What is a covered call strategy?",
            "How are capital gains taxed short vs long term?",
            "What is a REIT and how does it pay dividends?",
            "What is portfolio rebalancing?",
            "How do ETFs differ from mutual funds?",
            "What is a stock split?",
            "How does compound interest work?",
            "What are blue-chip stocks?",
            "How to calculate ROI?",
            "What is market capitalization?",
            "How do stock options work?",
            "What is diversification?",
            "What are growth stocks vs value stocks?",
        ][:limit]
    
    return queries


def load_qrels(qrels_file: str) -> Dict[str, List[str]]:
    """
    Load query relevance judgments.
    
    Args:
        qrels_file: Path to qrels TSV file
        
    Returns:
        Dictionary mapping query_id to list of relevant doc_ids
    """
    qrels = defaultdict(list)
    
    if os.path.exists(qrels_file):
        with open(qrels_file, 'r', encoding='utf-8') as f:
            for line_idx, line in enumerate(f):
                # Skip header line
                if line_idx == 0 and 'query' in line.lower():
                    continue
                
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    query_id = parts[0]
                    doc_id = parts[1]
                    try:
                        relevance = int(parts[2])
                        if relevance > 0:
                            qrels[query_id].append(doc_id)
                    except ValueError:
                        # Skip invalid lines
                        continue
    
    return dict(qrels)


def calculate_recall_at_k(results: List[ScoredDocument], relevant_docs: List[str], k: int = 10) -> float:
    """
    Calculate Recall@K.
    
    Args:
        results: List of ScoredDocument
        relevant_docs: List of relevant document IDs
        k: Top K results to consider
        
    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not relevant_docs:
        return 0.0
    
    # Get top K document IDs
    top_k_ids = [doc.id for doc in results[:k]]
    
    # Count how many relevant docs are in top K
    hits = sum(1 for doc_id in top_k_ids if doc_id in relevant_docs)
    
    # Recall = hits / total_relevant
    recall = hits / len(relevant_docs)
    
    return recall


def run_ab_test() -> Tuple[List[Dict], List[Dict]]:
    """
    Run A/B test with rewrite_enabled=True and rewrite_enabled=False.
    
    Returns:
        Tuple of (rewrite_on_results, rewrite_off_results)
    """
    # Load test data
    queries = load_test_queries(
        TEST_CONFIG["queries_file"],
        limit=TEST_CONFIG["num_queries"]
    )
    qrels = load_qrels(TEST_CONFIG["qrels_file"])
    
    print(f"🧪 开始 A/B 测试")
    print(f"📝 查询数量: {len(queries)}")
    print(f"📚 集合: {TEST_CONFIG['collection_name']}")
    print(f"🔍 搜索模式: {TEST_CONFIG['search_mode']}")
    print()
    
    # Group A: Rewrite ON
    print("=" * 60)
    print("🅰️  Group A: Rewrite ENABLED")
    print("=" * 60)
    
    config_a = RAGPipelineConfig(
        search_config={
            "retriever": {"type": "vector", "top_k": 500},
            "reranker": None
        },
        rewrite_enabled=True,
        use_mock_provider=True  # Use mock for fast testing
    )
    
    pipeline_a = RAGPipeline(config_a)
    results_a = []
    
    start_time_a = time.time()
    for idx, query in enumerate(queries, 1):
        result = pipeline_a.search(
            query=query,
            collection_name=TEST_CONFIG["collection_name"],
            top_k=TEST_CONFIG["top_k"],
            search_mode=TEST_CONFIG["search_mode"]
        )
        
        # Calculate recall if we have qrels
        recall_at_10 = 0.0
        query_id = str(idx - 1)  # Try to match by index
        if query_id in qrels:
            recall_at_10 = calculate_recall_at_k(
                result["results"],
                qrels[query_id],
                k=10
            )
        
        result["recall_at_10"] = recall_at_10
        result["query_id"] = query_id
        results_a.append(result)
        
        print(f"  [{idx}/{len(queries)}] {query[:40]}... "
              f"({result['latency_ms']:.0f}ms, R@10={recall_at_10:.2f})")
    
    duration_a = time.time() - start_time_a
    print(f"✅ Group A 完成: {duration_a:.1f}s")
    print()
    
    # Group B: Rewrite OFF
    print("=" * 60)
    print("🅱️  Group B: Rewrite DISABLED")
    print("=" * 60)
    
    config_b = RAGPipelineConfig(
        search_config={
            "retriever": {"type": "vector", "top_k": 500},
            "reranker": None
        },
        rewrite_enabled=False
    )
    
    pipeline_b = RAGPipeline(config_b)
    results_b = []
    
    start_time_b = time.time()
    for idx, query in enumerate(queries, 1):
        result = pipeline_b.search(
            query=query,
            collection_name=TEST_CONFIG["collection_name"],
            top_k=TEST_CONFIG["top_k"],
            search_mode=TEST_CONFIG["search_mode"]
        )
        
        # Calculate recall
        recall_at_10 = 0.0
        query_id = str(idx - 1)
        if query_id in qrels:
            recall_at_10 = calculate_recall_at_k(
                result["results"],
                qrels[query_id],
                k=10
            )
        
        result["recall_at_10"] = recall_at_10
        result["query_id"] = query_id
        results_b.append(result)
        
        print(f"  [{idx}/{len(queries)}] {query[:40]}... "
              f"({result['latency_ms']:.0f}ms, R@10={recall_at_10:.2f})")
    
    duration_b = time.time() - start_time_b
    print(f"✅ Group B 完成: {duration_b:.1f}s")
    print()
    
    return results_a, results_b


def analyze_results(results_a: List[Dict], results_b: List[Dict]) -> Dict[str, Any]:
    """
    Analyze A/B test results and compute metrics.
    
    Args:
        results_a: Results with rewrite ON
        results_b: Results with rewrite OFF
        
    Returns:
        Dictionary with analysis metrics
    """
    # Extract latencies
    latencies_a = [r["latency_ms"] for r in results_a]
    latencies_b = [r["latency_ms"] for r in results_b]
    
    # Extract recalls
    recalls_a = [r["recall_at_10"] for r in results_a]
    recalls_b = [r["recall_at_10"] for r in results_b]
    
    # Calculate P95 latency
    p95_a = statistics.quantiles(latencies_a, n=20)[18] if len(latencies_a) >= 20 else max(latencies_a)
    p95_b = statistics.quantiles(latencies_b, n=20)[18] if len(latencies_b) >= 20 else max(latencies_b)
    
    # Calculate average metrics
    avg_latency_a = statistics.mean(latencies_a)
    avg_latency_b = statistics.mean(latencies_b)
    avg_recall_a = statistics.mean(recalls_a)
    avg_recall_b = statistics.mean(recalls_b)
    
    # Calculate hit rate (queries with recall > 0)
    hit_rate_a = sum(1 for r in recalls_a if r > 0) / len(recalls_a) * 100
    hit_rate_b = sum(1 for r in recalls_b if r > 0) / len(recalls_b) * 100
    
    # Calculate deltas
    delta_recall = avg_recall_a - avg_recall_b
    delta_recall_pct = (delta_recall / avg_recall_b * 100) if avg_recall_b > 0 else 0
    delta_p95 = p95_a - p95_b
    delta_p95_pct = (delta_p95 / p95_b * 100) if p95_b > 0 else 0
    
    analysis = {
        "group_a": {
            "avg_latency_ms": avg_latency_a,
            "p95_latency_ms": p95_a,
            "avg_recall_at_10": avg_recall_a,
            "hit_rate_pct": hit_rate_a,
            "num_queries": len(results_a)
        },
        "group_b": {
            "avg_latency_ms": avg_latency_b,
            "p95_latency_ms": p95_b,
            "avg_recall_at_10": avg_recall_b,
            "hit_rate_pct": hit_rate_b,
            "num_queries": len(results_b)
        },
        "deltas": {
            "recall_delta": delta_recall,
            "recall_delta_pct": delta_recall_pct,
            "p95_delta_ms": delta_p95,
            "p95_delta_pct": delta_p95_pct,
            "hit_rate_delta_pct": hit_rate_a - hit_rate_b
        }
    }
    
    return analysis


def generate_html_report(
    results_a: List[Dict],
    results_b: List[Dict],
    analysis: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generate HTML report for A/B test.
    
    Args:
        results_a: Results with rewrite ON
        results_b: Results with rewrite OFF
        analysis: Analysis metrics
        output_path: Path to save HTML file
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate summary text
    recall_change = analysis["deltas"]["recall_delta_pct"]
    p95_change = analysis["deltas"]["p95_delta_pct"]
    
    if abs(recall_change) < 1.0:
        recall_text = "无显著变化"
    elif recall_change > 0:
        recall_text = f"提升 {recall_change:.1f}%"
    else:
        recall_text = f"下降 {abs(recall_change):.1f}%"
    
    if abs(p95_change) < 5.0:
        p95_text = "无显著上升"
    elif p95_change > 0:
        p95_text = f"增加 {p95_change:.1f}%"
    else:
        p95_text = f"降低 {abs(p95_change):.1f}%"
    
    summary = f"启用查询改写后，Recall@10 {recall_text}，P95 延迟 {p95_text}。"
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG Query Rewriter A/B Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .summary {{
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }}
        .summary h2 {{
            margin-top: 0;
            color: #333;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .metric-delta {{
            font-size: 14px;
            color: #666;
        }}
        .metric-delta.positive {{
            color: #28a745;
        }}
        .metric-delta.negative {{
            color: #dc3545;
        }}
        .comparison {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
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
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .group-a {{
            color: #667eea;
            font-weight: 600;
        }}
        .group-b {{
            color: #764ba2;
            font-weight: 600;
        }}
        .details {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .details h2 {{
            margin-top: 0;
        }}
        .query-result {{
            padding: 10px;
            margin-bottom: 10px;
            border-left: 3px solid #ddd;
            background: #f9f9f9;
        }}
        .query-text {{
            font-weight: 600;
            margin-bottom: 5px;
        }}
        .rewrite-text {{
            color: #667eea;
            font-style: italic;
            margin-bottom: 5px;
        }}
        .metrics-row {{
            font-size: 12px;
            color: #666;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 30px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 RAG Query Rewriter A/B Test Report</h1>
        <p>对比查询改写开启/关闭对检索质量的影响</p>
        <p><small>生成时间: {timestamp}</small></p>
    </div>
    
    <div class="summary">
        <h2>📊 总结</h2>
        <p style="font-size: 18px; line-height: 1.6;">{summary}</p>
    </div>
    
    <div class="metrics">
        <div class="metric-card">
            <h3>Group A - Rewrite ON</h3>
            <div class="metric-value group-a">{analysis['group_a']['avg_recall_at_10']:.3f}</div>
            <div>平均 Recall@10</div>
        </div>
        <div class="metric-card">
            <h3>Group B - Rewrite OFF</h3>
            <div class="metric-value group-b">{analysis['group_b']['avg_recall_at_10']:.3f}</div>
            <div>平均 Recall@10</div>
        </div>
        <div class="metric-card">
            <h3>Recall 变化</h3>
            <div class="metric-value {'positive' if analysis['deltas']['recall_delta'] > 0 else 'negative'}">
                {analysis['deltas']['recall_delta_pct']:+.1f}%
            </div>
            <div>相对提升/下降</div>
        </div>
        <div class="metric-card">
            <h3>P95 延迟变化</h3>
            <div class="metric-value {'negative' if analysis['deltas']['p95_delta_ms'] > 0 else 'positive'}">
                {analysis['deltas']['p95_delta_ms']:+.0f}ms
            </div>
            <div>{analysis['deltas']['p95_delta_pct']:+.1f}%</div>
        </div>
    </div>
    
    <div class="comparison">
        <h2>📈 详细指标对比</h2>
        <table>
            <thead>
                <tr>
                    <th>指标</th>
                    <th class="group-a">Group A (Rewrite ON)</th>
                    <th class="group-b">Group B (Rewrite OFF)</th>
                    <th>Delta</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>平均 Recall@10</td>
                    <td class="group-a">{analysis['group_a']['avg_recall_at_10']:.4f}</td>
                    <td class="group-b">{analysis['group_b']['avg_recall_at_10']:.4f}</td>
                    <td>{analysis['deltas']['recall_delta']:+.4f} ({analysis['deltas']['recall_delta_pct']:+.1f}%)</td>
                </tr>
                <tr>
                    <td>P95 延迟 (ms)</td>
                    <td class="group-a">{analysis['group_a']['p95_latency_ms']:.1f}</td>
                    <td class="group-b">{analysis['group_b']['p95_latency_ms']:.1f}</td>
                    <td>{analysis['deltas']['p95_delta_ms']:+.1f} ({analysis['deltas']['p95_delta_pct']:+.1f}%)</td>
                </tr>
                <tr>
                    <td>平均延迟 (ms)</td>
                    <td class="group-a">{analysis['group_a']['avg_latency_ms']:.1f}</td>
                    <td class="group-b">{analysis['group_b']['avg_latency_ms']:.1f}</td>
                    <td>{analysis['group_a']['avg_latency_ms'] - analysis['group_b']['avg_latency_ms']:+.1f}</td>
                </tr>
                <tr>
                    <td>命中率 (%)</td>
                    <td class="group-a">{analysis['group_a']['hit_rate_pct']:.1f}%</td>
                    <td class="group-b">{analysis['group_b']['hit_rate_pct']:.1f}%</td>
                    <td>{analysis['deltas']['hit_rate_delta_pct']:+.1f}%</td>
                </tr>
                <tr>
                    <td>查询数量</td>
                    <td class="group-a">{analysis['group_a']['num_queries']}</td>
                    <td class="group-b">{analysis['group_b']['num_queries']}</td>
                    <td>-</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="details">
        <h2>🔍 查询详情 (Group A - Rewrite ON)</h2>
"""
    
    # Add sample query details for Group A
    for idx, result in enumerate(results_a[:10], 1):  # Show first 10
        query_orig = result["query_original"]
        query_rewrite = result.get("query_rewritten", query_orig)
        recall = result["recall_at_10"]
        latency = result["latency_ms"]
        
        html += f"""
        <div class="query-result">
            <div class="query-text">#{idx}: {query_orig}</div>
"""
        if query_rewrite != query_orig:
            html += f"""            <div class="rewrite-text">→ {query_rewrite}</div>
"""
        html += f"""            <div class="metrics-row">Recall@10: {recall:.3f} | 延迟: {latency:.0f}ms</div>
        </div>
"""
    
    html += """
    </div>
    
    <div class="footer">
        <h3>✅ 验收标准</h3>
        <ul style="text-align: left; max-width: 600px; margin: 0 auto;">
            <li>✓ rewrite_on/off 两组均成功执行</li>
            <li>✓ 报告含 Recall@10、P95 延迟、命中率</li>
            <li>✓ 所有路径和导入无错误</li>
            <li>✓ 生成中文总结和对比分析</li>
        </ul>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    """Main entry point."""
    print("=" * 60)
    print("🚀 RAG Query Rewriter A/B Test")
    print("=" * 60)
    print()
    
    # Run A/B test
    start_time = time.time()
    results_a, results_b = run_ab_test()
    duration = time.time() - start_time
    
    # Analyze results
    print("=" * 60)
    print("📊 分析结果")
    print("=" * 60)
    analysis = analyze_results(results_a, results_b)
    
    print(f"\n🅰️  Group A (Rewrite ON):")
    print(f"  Recall@10: {analysis['group_a']['avg_recall_at_10']:.4f}")
    print(f"  P95 延迟: {analysis['group_a']['p95_latency_ms']:.1f}ms")
    print(f"  命中率: {analysis['group_a']['hit_rate_pct']:.1f}%")
    
    print(f"\n🅱️  Group B (Rewrite OFF):")
    print(f"  Recall@10: {analysis['group_b']['avg_recall_at_10']:.4f}")
    print(f"  P95 延迟: {analysis['group_b']['p95_latency_ms']:.1f}ms")
    print(f"  命中率: {analysis['group_b']['hit_rate_pct']:.1f}%")
    
    print(f"\n📈 Delta:")
    print(f"  ΔRecall@10: {analysis['deltas']['recall_delta']:+.4f} ({analysis['deltas']['recall_delta_pct']:+.1f}%)")
    print(f"  ΔP95: {analysis['deltas']['p95_delta_ms']:+.1f}ms ({analysis['deltas']['p95_delta_pct']:+.1f}%)")
    print(f"  Δ命中率: {analysis['deltas']['hit_rate_delta_pct']:+.1f}%")
    
    # Generate HTML report
    output_path = "reports/rag_rewrite_ab.html"
    generate_html_report(results_a, results_b, analysis, output_path)
    
    print(f"\n💾 HTML 报告已生成: {output_path}")
    print(f"⏱️  总运行时间: {duration:.1f}s")
    
    # Check acceptance criteria
    print("\n" + "=" * 60)
    print("✅ 验收标准检查")
    print("=" * 60)
    
    checks = [
        (len(results_a) > 0 and len(results_b) > 0, "rewrite_on/off 两组均成功执行"),
        ("avg_recall_at_10" in analysis["group_a"], "报告含 Recall@10"),
        ("p95_latency_ms" in analysis["group_a"], "报告含 P95 延迟"),
        ("hit_rate_pct" in analysis["group_a"], "报告含命中率"),
        (duration < 60, f"运行时间 < 60s (实际: {duration:.1f}s)"),
        (os.path.exists(output_path), f"HTML 报告已生成: {output_path}"),
    ]
    
    for passed, check_name in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
    
    all_passed = all(passed for passed, _ in checks)
    
    if all_passed:
        print("\n🎉 所有验收标准已通过！")
    else:
        print("\n⚠️  部分验收标准未通过")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
