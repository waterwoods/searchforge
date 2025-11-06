#!/usr/bin/env python3
"""
采样器：从历史结果中生成盲测评测批次
支持随机+分层采样策略，输出成对的 ON/OFF 结果
"""

import json
import random
import argparse
from pathlib import Path
from datetime import datetime


def load_latest_results():
    """加载最新的 smoke 或 canary 结果"""
    reports_dir = Path(__file__).parent.parent / "reports"
    
    # 尝试多个可能的结果文件
    candidates = [
        reports_dir / "fiqa_smoke_results.json",
        reports_dir / "canary_results.json",
    ]
    
    for path in candidates:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    
    # 如果没有找到，生成模拟数据
    print("⚠️  未找到历史结果，生成模拟数据用于演示")
    return generate_mock_data()


def generate_mock_data():
    """生成模拟的查询结果数据"""
    topics = ["ETF", "401k", "mortgage", "credit score", "tax deduction"]
    queries = [
        "What is an ETF?",
        "How to maximize 401k contributions?",
        "Should I refinance my mortgage?",
        "How to improve credit score quickly?",
        "What are common tax deductions?",
        "Best investment strategies for beginners",
        "Difference between Roth and traditional IRA",
        "How does compound interest work?",
        "When should I start saving for retirement?",
        "What is a good debt to income ratio?",
        "How to calculate mortgage payments?",
        "What are index funds?",
        "How to diversify investment portfolio?",
        "What is dollar cost averaging?",
        "Should I pay off debt or invest?",
        "How much emergency fund do I need?",
        "What is the best budgeting method?",
        "How to negotiate salary increase?",
        "What are tax-advantaged accounts?",
        "How to plan for early retirement?",
    ]
    
    results = []
    for q in queries:
        # 为每个查询生成 ON/OFF 两组结果
        results.append({
            "query": q,
            "topic": random.choice(topics),
            "query_length": len(q),
            "on_results": [
                {"title": f"ON Title {i+1}", "text": f"ON result {i+1} for: {q[:30]}...", "source": "mock", "score": 0.9 - i*0.1, "rerank_hit": 1} for i in range(3)
            ],
            "off_results": [
                {"title": f"OFF Title {i+1}", "text": f"OFF result {i+1} for: {q[:30]}...", "source": "mock", "score": 0.8 - i*0.1, "rerank_hit": 0} for i in range(3)
            ]
        })
    
    return results


def fetch_real_results(query: str, mode: str, top_k: int = 3) -> list:
    """调用真实 API 获取结果（beir_fiqa_full_ta）"""
    import requests
    import hashlib
    
    try:
        url = "http://localhost:8080/search"
        # POST request with JSON body for better compatibility
        payload = {"query": query, "top_k": top_k}
        params = {"mode": mode}  # mode as query param
        response = requests.post(url, json=payload, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "answers" in data:
                answers = data["answers"]
                # 转换为结构化格式
                results = []
                for i, ans in enumerate(answers[:top_k]):
                    if isinstance(ans, str):
                        # 使用文本内容生成唯一 ID
                        doc_id = hashlib.md5(ans[:100].encode()).hexdigest()[:12]
                        results.append({
                            "id": doc_id,
                            "title": f"Result {i+1}",
                            "text": ans[:200],
                            "snippet": ans[:200],
                            "source": "API",
                            "score": 0.9-i*0.1,
                            "rank": i+1
                        })
                    elif isinstance(ans, dict):
                        text = ans.get("text", str(ans))[:200]
                        # 使用文本内容生成唯一 ID（如果没有提供）
                        doc_id = ans.get("id")
                        if not doc_id:
                            doc_id = hashlib.md5(text[:100].encode()).hexdigest()[:12]
                        results.append({
                            "id": doc_id,
                            "title": ans.get("title", f"Result {i+1}"),
                            "text": text,
                            "snippet": text,
                            "source": ans.get("source", "API"),
                            "score": ans.get("score", 0.9-i*0.1),
                            "rank": i+1
                        })
                return results
        
        print(f"⚠️  API 调用失败: {response.status_code}")
        return []
    except Exception as e:
        print(f"⚠️  网络错误: {e}")
        return []


def extract_evidence_span(snippet: str, query: str) -> dict:
    """从 snippet 中提取证据范围（简化版：查找查询关键词）"""
    if not snippet or not query:
        return {"start": 0, "end": 0}
    
    # 简单实现：找到查询中第一个词在 snippet 中的位置
    query_words = query.lower().split()[:3]  # 取前3个词
    for word in query_words:
        if len(word) > 3:  # 跳过停用词
            idx = snippet.lower().find(word)
            if idx != -1:
                return {"start": max(0, idx-20), "end": min(len(snippet), idx+len(word)+20)}
    
    # 如果找不到，返回开头部分
    return {"start": 0, "end": min(50, len(snippet))}


def calculate_rank_delta(on_results: list, off_results: list) -> dict:
    """计算共同文档的排名变化"""
    # 构建 ID -> rank 映射
    on_ranks = {r["id"]: r["rank"] for r in on_results}
    off_ranks = {r["id"]: r["rank"] for r in off_results}
    
    # 找到共同文档
    common_ids = set(on_ranks.keys()) & set(off_ranks.keys())
    
    if not common_ids:
        return {"best_rank_delta": 0, "common_docs": 0}
    
    # 计算每个共同文档的 rank_delta = rank_off - rank_on (正数=排名提升)
    deltas = []
    for doc_id in common_ids:
        delta = off_ranks[doc_id] - on_ranks[doc_id]
        deltas.append(delta)
    
    best_delta = max(deltas) if deltas else 0
    return {"best_rank_delta": best_delta, "common_docs": len(common_ids)}


def create_compare_batch(n: int = 20) -> list:
    """创建对比集：固定 ON=PageIndex+Reranker, OFF=Baseline"""
    import time
    
    # 使用真实查询集（从 fiqa_queries.txt 或生成）
    queries = load_fiqa_queries(n)
    
    batch = []
    print(f"🔍 生成对比集 (n={n})...")
    
    for idx, query in enumerate(queries):
        print(f"  [{idx+1}/{len(queries)}] {query[:60]}...")
        
        # 获取 ON (PageIndex+Reranker) 和 OFF (Baseline) 的 Top-10
        on_results = fetch_real_results(query, "on", top_k=10)
        time.sleep(0.35)
        off_results = fetch_real_results(query, "off", top_k=10)
        time.sleep(0.35)
        
        if not on_results or not off_results:
            print(f"    ⚠️  跳过（API 失败）")
            continue
        
        # 计算 rank_delta
        rank_info = calculate_rank_delta(on_results, off_results)
        
        # 提取 ON Top-1 的 evidence_span
        if on_results:
            evidence_span = extract_evidence_span(on_results[0]["snippet"], query)
            on_results[0]["evidence_span"] = evidence_span
        
        # 获取触发原因（从现有逻辑）
        trigger_reason = get_trigger_reason(query, on_results)
        
        batch.append({
            "id": idx,
            "query": query,
            "on": on_results,
            "off": off_results,
            "best_rank_delta": rank_info["best_rank_delta"],
            "common_docs": rank_info["common_docs"],
            "trigger_reason": trigger_reason
        })
    
    return batch


def load_fiqa_queries(n: int) -> list:
    """加载真实 FIQA 查询"""
    queries_file = Path(__file__).parent.parent / "data" / "fiqa_queries.txt"
    
    if queries_file.exists():
        with open(queries_file) as f:
            queries = [line.strip() for line in f if line.strip()]
            return random.sample(queries, min(n, len(queries)))
    
    # Fallback: 生成模拟查询
    return [
        "What is an ETF?",
        "How to maximize 401k contributions?",
        "Should I refinance my mortgage?",
        "How to improve credit score quickly?",
        "What are common tax deductions?",
        "Best investment strategies for beginners",
        "Difference between Roth and traditional IRA",
        "How does compound interest work?",
        "When should I start saving for retirement?",
        "What is a good debt to income ratio?",
        "How to calculate mortgage payments?",
        "What are index funds?",
        "How to diversify investment portfolio?",
        "What is dollar cost averaging?",
        "Should I pay off debt or invest?",
        "How much emergency fund do I need?",
        "What is the best budgeting method?",
        "How to negotiate salary increase?",
        "What are tax-advantaged accounts?",
        "How to plan for early retirement?",
    ][:n]


def get_trigger_reason(query: str, results: list) -> str:
    """获取触发原因（长度/关键词/分散度）"""
    reasons = []
    
    # 长度检查
    if len(query) >= 50:
        reasons.append("len")
    
    # 关键词检查
    keywords = ["how to", "should i", "best", "calculate", "what is", "when to"]
    if any(kw in query.lower() for kw in keywords):
        reasons.append("kw")
    
    # 分散度检查（简化版）
    if results and len(results) >= 3:
        scores = [r.get("score", 0) for r in results[:3]]
        if max(scores) - min(scores) > 0.15:
            reasons.append("dispersion")
    
    return "|".join(reasons) if reasons else "none"


def stratified_sample(results, n=20, four_way=False):
    """分层采样：短查询 50% + 长查询 50% 或 四层分布（短/长/计算/策略）"""
    if four_way:
        # 四层分层：短(7) / 长(7) / 计算(8) / 策略(8)
        # 分类逻辑：按 query_length 和关键词
        compute_kw = ["calculate", "how much", "percent", "rate", "ratio", "cost", "payment"]
        strategy_kw = ["should i", "best", "when to", "how to", "strategy", "plan", "optimize"]
        
        compute_queries = []
        strategy_queries = []
        short_queries = []
        long_queries = []
        
        for r in results:
            q_lower = r["query"].lower()
            q_len = r["query_length"]
            
            # 优先按内容分类
            if any(kw in q_lower for kw in compute_kw):
                compute_queries.append(r)
            elif any(kw in q_lower for kw in strategy_kw):
                strategy_queries.append(r)
            # 否则按长度分类
            elif q_len < 50:
                short_queries.append(r)
            else:
                long_queries.append(r)
        
        # 分配数量（短/长/计算/策略≈7/7/8/8）
        n_short = 7 if n >= 30 else int(n * 0.23)
        n_long = 7 if n >= 30 else int(n * 0.23)
        n_compute = 8 if n >= 30 else int(n * 0.27)
        n_strategy = n - n_short - n_long - n_compute
        
        sampled = []
        sampled.extend(random.sample(short_queries, min(n_short, len(short_queries))))
        sampled.extend(random.sample(long_queries, min(n_long, len(long_queries))))
        sampled.extend(random.sample(compute_queries, min(n_compute, len(compute_queries))))
        sampled.extend(random.sample(strategy_queries, min(n_strategy, len(strategy_queries))))
        
        return sampled
    else:
        # 原有两层分层：短查询 50% + 长查询 50%
        sorted_by_length = sorted(results, key=lambda x: x["query_length"])
        median_idx = len(sorted_by_length) // 2
        
        short_queries = sorted_by_length[:median_idx]
        long_queries = sorted_by_length[median_idx:]
        
        n_short = n // 2
        n_long = n - n_short
        
        sampled = []
        if len(short_queries) >= n_short:
            sampled.extend(random.sample(short_queries, n_short))
        else:
            sampled.extend(short_queries)
        
        if len(long_queries) >= n_long:
            sampled.extend(random.sample(long_queries, n_long))
        else:
            sampled.extend(long_queries)
        
        return sampled


def create_batch(results, n=20, strategy="mixed", four_way=False):
    """创建评测批次"""
    import time
    
    # 去重
    unique_results = {r["query"]: r for r in results}.values()
    results = list(unique_results)
    target_n = n  # 保存目标值用于补足
    
    # 采样策略
    sample_n = min(n, len(results))  # 采样时不超过可用数
    if strategy == "random":
        sampled = random.sample(results, sample_n)
    elif strategy == "stratified":
        sampled = stratified_sample(results, sample_n, four_way=four_way)
    else:  # mixed: 50% random + 50% stratified
        n_random = sample_n // 2
        n_stratified = sample_n - n_random
        sampled = random.sample(results, n_random)
        remaining = [r for r in results if r not in sampled]
        sampled.extend(stratified_sample(remaining, n_stratified, four_way=four_way))
    
    # 自动补足：如果采样不足目标 n，随机补充（允许重复）
    initial_count = len(sampled)
    if initial_count < target_n:
        need = target_n - initial_count
        sampled.extend(random.choices(results, k=need))
        print(f"[SAMPLE] filled from {initial_count} → {len(sampled)} (auto-padded)")
    
    # 构建批次输出
    batch = []
    print("🔍 调用真实 API 生成 ON/OFF 结果 (beir_fiqa_full_ta)...")
    for idx, item in enumerate(sampled):
        query = item["query"]
        print(f"  [{idx+1}/{len(sampled)}] {query[:50]}...")
        
        # 调用真实 API (with delay to respect rate limit)
        on_results = fetch_real_results(query, "on")
        time.sleep(0.35)  # Respect rate limit (3 req/sec)
        off_results = fetch_real_results(query, "off")
        time.sleep(0.35)  # Respect rate limit
        
        # 如果 API 调用失败，使用模拟数据或跳过
        if not on_results or not off_results:
            print(f"    ⚠️  API 失败，使用历史数据")
            on_results = item.get("on_results", [])[:3]
            off_results = item.get("off_results", [])[:3]
            # 如果历史数据也没有，生成占位符
            if not on_results:
                on_results = [{"title": f"Placeholder {i+1}", "text": f"ON result for: {query[:50]}", "source": "placeholder", "score": 0.7-i*0.1} for i in range(3)]
            if not off_results:
                off_results = [{"title": f"Placeholder {i+1}", "text": f"OFF result for: {query[:50]}", "source": "placeholder", "score": 0.6-i*0.1} for i in range(3)]
        
        batch.append({
            "id": idx,
            "query": query,
            "on": on_results[:3],
            "off": off_results[:3],
            "metadata": {
                "topic": item.get("topic", "unknown"),
                "query_length": item["query_length"]
            }
        })
    
    return batch


def main():
    parser = argparse.ArgumentParser(description="生成人工评测采样批次")
    parser.add_argument("--n", type=int, default=20, help="采样数量 (默认 20)")
    parser.add_argument("--strategy", choices=["random", "stratified", "mixed"], 
                       default="mixed", help="采样策略 (默认 mixed)")
    parser.add_argument("--stratify", action="store_true", 
                       help="使用四层分层采样（短/长/计算/策略≈7/7/8/8）")
    parser.add_argument("--label", type=str, default=None, 
                       help="批次标签（如 'latest'），会创建带标签的符号链接")
    parser.add_argument("--compare", action="store_true",
                       help="对比模式：固定 ON=PageIndex+Reranker, OFF=Baseline，生成对比集")
    args = parser.parse_args()
    
    # 对比模式
    if args.compare:
        batch = create_compare_batch(n=args.n)
        
        # 保存对比集
        output_filename = f"compare_batch_{args.label}.json" if args.label else "compare_batch_latest.json"
        output_path = Path(__file__).parent.parent / "reports" / output_filename
        output_path.parent.mkdir(exist_ok=True)
        
        # 计算统计信息
        improved_count = sum(1 for item in batch if item.get("best_rank_delta", 0) > 0)
        rank_deltas = [item.get("best_rank_delta", 0) for item in batch]
        median_delta = sorted(rank_deltas)[len(rank_deltas)//2] if rank_deltas else 0
        
        # 统计触发原因
        reason_counts = {}
        for item in batch:
            reason = item.get("trigger_reason", "none")
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        top_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_reasons_str = ", ".join([f"{r}:{c}" for r, c in top_reasons])
        
        output_data = {
            "batch_id": args.label or "latest",
            "created_at": datetime.now().isoformat(),
            "total": len(batch),
            "improved_count": improved_count,
            "median_rank_delta": median_delta,
            "mode": "compare",
            "items": batch
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 对比集已生成: {output_path}")
        print(f"\n[COMPARE] n={len(batch)} | improved={improved_count}/{len(batch)} | median_rank_delta=+{median_delta} | top_reasons={top_reasons_str}")
        print(f"\n🔗 查看报告: http://localhost:8080/judge/report")
        return
    
    # 原有的普通模式
    # 加载结果
    print("📂 加载历史结果...")
    results = load_latest_results()
    print(f"✓ 加载 {len(results)} 条结果")
    
    # 创建批次
    four_way = args.stratify
    print(f"🎲 采样策略: {args.strategy}, 目标数量: {args.n}, 四层分层: {four_way}")
    batch = create_batch(results, n=args.n, strategy=args.strategy, four_way=four_way)
    
    # 保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(__file__).parent.parent / "reports" / f"judge_batch_{timestamp}.json"
    output_path.parent.mkdir(exist_ok=True)
    
    output_data = {
        "batch_id": timestamp,
        "created_at": datetime.now().isoformat(),
        "total": len(batch),
        "strategy": args.strategy,
        "four_way": four_way,
        "items": batch
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 批次已生成: {output_path}")
    print(f"   批次ID: {timestamp}")
    print(f"   样本数: {len(batch)}")
    
    # 如果指定了 label，创建符号链接或副本
    if args.label:
        label_path = Path(__file__).parent.parent / "reports" / f"judge_batch_{args.label}.json"
        import shutil
        shutil.copy(output_path, label_path)
        print(f"   标签: {args.label} -> {label_path.name}")
    
    print(f"\n🔗 访问标注页: http://localhost:8080/judge?batch={args.label or timestamp}")


if __name__ == "__main__":
    main()


