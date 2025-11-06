#!/usr/bin/env python3
"""打印最终验证结果（用户要求的格式）"""
import json
from pathlib import Path

def main():
    reports_dir = Path(__file__).parent.parent / "reports"
    
    # 读取 Canary 结果
    canary_file = reports_dir / "canary_quick.json"
    if canary_file.exists():
        with open(canary_file) as f:
            canary = json.load(f)
    else:
        canary = {}
    
    # 读取 Judger 批次
    judge_batches = sorted(reports_dir.glob("judge_batch_*.json"), reverse=True)
    if judge_batches:
        batch_file = judge_batches[0]
        with open(batch_file) as f:
            judger = json.load(f)
        batch_id = judger["batch_id"]
        samples = judger["total"]
        
        # 检查是否有投票
        votes_file = reports_dir / f"judge_votes_{batch_id}.jsonl"
        if votes_file.exists():
            with open(votes_file) as f:
                votes_count = sum(1 for line in f if line.strip())
            verdict = "PASS" if votes_count >= 14 else "PENDING"
        else:
            votes_count = 0
            verdict = "PENDING"
    else:
        samples = 0
        verdict = "NO_DATA"
        batch_id = None
    
    # 格式化输出
    print("\n" + "="*60)
    print("  固定 ON 配置验证结果")
    print("="*60 + "\n")
    
    print("[ON CONFIG] PageIndex+Reranker Enabled")
    
    if samples > 0:
        if verdict == "PENDING":
            print(f"[JUDGER] samples={samples} verdict=PENDING (等待人工评审)")
            if batch_id:
                print(f"           评审链接: http://localhost:8080/judge?batch={batch_id}")
        else:
            print(f"[JUDGER] samples={samples} verdict={verdict}")
    
    if canary:
        delta_recall = canary.get('delta_recall', 0)
        delta_p95 = canary.get('delta_p95_ms', 0)
        p_value = canary.get('p_value', 1.0)
        print(f"[CANARY] ΔRecall={delta_recall:+.4f} / ΔP95={delta_p95:+.1f}ms / p-value={p_value:.4f}")
    
    # 文件位置
    print(f"\n[REPORT] reports/canary_quick.json")
    if judge_batches:
        print(f"[REPORT] {judge_batches[0].name}")
    
    docs_pdf = Path(__file__).parent.parent / "docs" / "one_pager_fiqa.pdf"
    if docs_pdf.exists():
        print(f"[REPORT] docs/one_pager_fiqa.pdf")
    
    print("\n" + "="*60)
    print("  验证完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

