#!/usr/bin/env python3
"""
mine_diff_cases.py - 挖掘对比模式的差异案例
"""
import json
import requests
from pathlib import Path
import time
import statistics

# 默认模板查询
DEFAULT_DEMO_QUERIES = [
    "How to invest in index funds?",
    "What are ETF expense ratios?",
    "Best retirement savings strategies",
    "How does compound interest work?",
    "What is a Roth IRA?",
    "Mortgage refinancing tips",
    "Credit score improvement guide",
    "Tax-loss harvesting explained",
    "Dollar cost averaging benefits",
    "401k contribution limits 2024"
]

API_BASE = "http://localhost:8080"
REPORTS_DIR = Path(__file__).parent.parent / "reports"


def load_or_create_demo_queries(queries_path: Path) -> list[str]:
    """加载或创建demo查询列表"""
    if queries_path.exists():
        with open(queries_path) as f:
            data = json.load(f)
            return data.get("queries", DEFAULT_DEMO_QUERIES)
    else:
        # 创建默认查询
        queries_path.parent.mkdir(exist_ok=True)
        with open(queries_path, 'w') as f:
            json.dump({"queries": DEFAULT_DEMO_QUERIES}, f, indent=2)
        print(f"✓ 创建默认查询文件: {queries_path}")
        return DEFAULT_DEMO_QUERIES


def call_search_api(query: str, mode: str) -> dict:
    """调用搜索API"""
    try:
        response = requests.get(
            f"{API_BASE}/search",
            params={"query": query, "mode": mode, "top_k": 10},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️  API调用失败 (mode={mode}): {e}")
        return None


def compute_doc_id_diff(off_ids: list[str], on_ids: list[str]) -> int:
    """计算doc_id集合差异数量"""
    off_set = set(off_ids)
    on_set = set(on_ids)
    return len(off_set.symmetric_difference(on_set))


def compute_rank_delta(off_ids: list[str], on_ids: list[str]) -> int:
    """计算OFF Top-1 在 ON 中的排名变化"""
    if not off_ids or not on_ids:
        return 0
    
    off_top1 = off_ids[0]
    try:
        on_rank = on_ids.index(off_top1) + 1  # 1-based
        return on_rank - 1  # 正数表示提升（在ON中排名更靠前）
    except ValueError:
        # OFF Top-1 不在 ON 结果中
        return -99


def extract_trigger_reason(query: str, off_result: dict, on_result: dict) -> str:
    """提取触发原因"""
    reasons = []
    
    # 长度触发
    if len(query) >= 15:
        reasons.append("len")
    
    # 关键词触发 (简化判断)
    keywords = ["etf", "yield", "roi", "401k", "bond", "tax", "credit", "mortgage", "invest", "fund"]
    if any(kw in query.lower() for kw in keywords):
        reasons.append("kw")
    
    # 分散度触发 (基于结果差异推断)
    if compute_doc_id_diff(off_result.get("doc_ids", []), on_result.get("doc_ids", [])) >= 5:
        reasons.append("dispersion")
    
    return "|".join(reasons) if reasons else "none"


def mine_diff_cases():
    """挖掘差异案例"""
    print("=" * 60)
    print("🔍 对比挖掘开始...")
    print("=" * 60)
    
    # 加载查询
    queries_path = REPORTS_DIR / "demo_queries.json"
    queries = load_or_create_demo_queries(queries_path)
    print(f"✓ 加载 {len(queries)} 条查询")
    
    # 对比结果
    compare_items = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] {query}")
        
        # 调用 OFF 和 ON
        off_result = call_search_api(query, "off")
        time.sleep(0.5)  # 避免触发限流（每秒最多3个请求）
        on_result = call_search_api(query, "on")
        time.sleep(0.5)
        
        if not off_result or not on_result:
            print("  ⚠️  跳过（API调用失败）")
            continue
        
        # 提取 doc_ids
        off_ids = off_result.get("doc_ids", [])
        on_ids = on_result.get("doc_ids", [])
        
        # 计算差异
        doc_diff = compute_doc_id_diff(off_ids, on_ids)
        rank_delta = compute_rank_delta(off_ids, on_ids)
        trigger_reason = extract_trigger_reason(query, off_result, on_result)
        
        # 提取 evidence_span (前50字)
        evidence_span = ""
        if on_result.get("answers"):
            evidence_span = on_result["answers"][0][:50]
        
        print(f"  doc_diff={doc_diff}, rank_delta={rank_delta}, trigger={trigger_reason}")
        
        compare_items.append({
            "query": query,
            "doc_id_diff": doc_diff,
            "best_rank_delta": rank_delta,
            "trigger_reason": trigger_reason,
            "evidence_span": evidence_span,
            "off": {
                "doc_ids": off_ids,
                "top3": off_result.get("answers", [])[:3]
            },
            "on": {
                "doc_ids": on_ids,
                "top3": on_result.get("answers", [])[:3]
            }
        })
    
    # 筛选前20条满足条件的样本
    filtered = [
        item for item in compare_items
        if item["doc_id_diff"] >= 1 or abs(item["best_rank_delta"]) >= 2
    ]
    filtered = sorted(filtered, key=lambda x: x["best_rank_delta"], reverse=True)[:20]
    
    # 计算统计信息
    improved_count = sum(1 for item in filtered if item["best_rank_delta"] > 0)
    median_rank_delta = statistics.median([item["best_rank_delta"] for item in filtered]) if filtered else 0
    
    # 保存 compare_batch_latest.json
    compare_batch = {
        "total": len(filtered),
        "improved_count": improved_count,
        "median_rank_delta": median_rank_delta,
        "items": filtered
    }
    
    compare_path = REPORTS_DIR / "compare_batch_latest.json"
    with open(compare_path, 'w') as f:
        json.dump(compare_batch, f, indent=2)
    print(f"\n✓ 保存对比数据: {compare_path}")
    
    # 保存 judge_batch_latest.json (兼容 /judge 渲染)
    judge_items = []
    for idx, item in enumerate(filtered):
        judge_items.append({
            "id": idx,
            "query": item["query"],
            "off": item["off"]["top3"],
            "on": item["on"]["top3"]
        })
    
    judge_batch = {
        "batch_id": "compare_latest",
        "total": len(judge_items),
        "items": judge_items
    }
    
    judge_path = REPORTS_DIR / "judge_batch_latest.json"
    with open(judge_path, 'w') as f:
        json.dump(judge_batch, f, indent=2)
    print(f"✓ 保存标注数据: {judge_path}")
    
    print("\n" + "=" * 60)
    print(f"✓ 完成！共筛选 {len(filtered)} 条样本")
    print(f"  改进样本: {improved_count}/{len(filtered)}")
    print(f"  中位排名提升: +{median_rank_delta}")
    print("=" * 60)
    
    return compare_batch


if __name__ == "__main__":
    mine_diff_cases()
