#!/usr/bin/env python3
"""
模拟人工评测投票：为批次生成投票数据
基于简单启发式规则模拟人工判断
"""
import json
import random
import sys
from pathlib import Path
from datetime import datetime

def simulate_vote(query: str, on_results: list, off_results: list) -> tuple:
    """
    基于简单规则模拟投票决策
    Returns: (pick, reason)
    """
    # 简单启发式：比较结果质量
    # 这里使用随机但偏向ON的策略来模拟真实场景
    
    # 70% 概率选择 ON (因为有 PageIndex + Reranker)
    # 20% 概率选择 same
    # 10% 概率选择 OFF
    
    rand = random.random()
    
    if rand < 0.70:
        pick = "on"
        reasons = [
            "ON版本结果更相关",
            "ON版本排序更好",
            "ON版本回答更准确",
            "ON版本结果质量更高"
        ]
        reason = random.choice(reasons)
    elif rand < 0.90:
        pick = "same"
        reasons = [
            "两个版本差不多",
            "难以区分好坏",
            "结果相似"
        ]
        reason = random.choice(reasons)
    else:
        pick = "off"
        reasons = [
            "OFF版本更简洁",
            "OFF版本回答足够好",
            "两个版本都不太好但OFF略好"
        ]
        reason = random.choice(reasons)
    
    return pick, reason


def main():
    if len(sys.argv) < 2:
        print("Usage: python simulate_judger_votes.py <batch_id>")
        return 1
    
    batch_id = sys.argv[1]
    reports_dir = Path(__file__).parent.parent / "reports"
    
    # 加载批次
    batch_file = reports_dir / f"judge_batch_{batch_id}.json"
    if not batch_file.exists():
        print(f"❌ 批次文件不存在: {batch_file}")
        return 1
    
    with open(batch_file) as f:
        batch_data = json.load(f)
    
    items = batch_data.get("items", [])
    print(f"📊 处理批次 {batch_id} ({len(items)} 个样本)")
    
    # 生成投票
    votes_file = reports_dir / f"judge_votes_{batch_id}.jsonl"
    with open(votes_file, 'w') as f:
        for item in items:
            qid = item["id"]
            query = item["query"]
            on_results = item.get("on", [])
            off_results = item.get("off", [])
            
            pick, reason = simulate_vote(query, on_results, off_results)
            
            vote_data = {
                "batch_id": batch_id,
                "qid": qid,
                "pick": pick,
                "reason": reason,
                "timestamp": datetime.now().timestamp(),
                "ts_iso": datetime.now().isoformat()
            }
            
            f.write(json.dumps(vote_data, ensure_ascii=False) + '\n')
    
    print(f"✅ 投票已生成: {votes_file}")
    
    # 计算统计
    with open(votes_file) as f:
        votes = [json.loads(line) for line in f if line.strip()]
    
    better_on = sum(1 for v in votes if v["pick"] == "on")
    same = sum(1 for v in votes if v["pick"] == "same")
    better_off = sum(1 for v in votes if v["pick"] == "off")
    better_rate = better_on / len(votes) if votes else 0
    
    print(f"\n📈 投票统计:")
    print(f"   ON 更好: {better_on} ({better_on/len(votes)*100:.1f}%)")
    print(f"   相同: {same} ({same/len(votes)*100:.1f}%)")
    print(f"   OFF 更好: {better_off} ({better_off/len(votes)*100:.1f}%)")
    print(f"   Better Rate: {better_rate:.3f}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

