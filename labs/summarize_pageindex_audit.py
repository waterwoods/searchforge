#!/usr/bin/env python3
"""
PageIndex Manual Audit Aggregator

Reads pageindex_manual_audit_10.json with human annotations and produces summary.
Annotations: "更相关", "相当", "更差"
Target: ≥7/10 marked as "更相关" = PASS

Updates pageindex_canary_live.json with human_audit_summary.
"""

import json
import sys
from pathlib import Path

def main():
    # Paths
    report_dir = Path(__file__).parent.parent / 'reports'
    
    # Try 20-sample file first, fallback to 10-sample
    audit_20_path = report_dir / 'pageindex_manual_audit_20.json'
    audit_10_path = report_dir / 'pageindex_manual_audit_10.json'
    
    if audit_20_path.exists():
        audit_path = audit_20_path
        print("📖 Reading manual audit samples (20)...")
    else:
        audit_path = audit_10_path
        print("📖 Reading manual audit samples (10)...")
    
    canary_path = report_dir / 'pageindex_canary_live.json'
    
    with open(audit_path, 'r', encoding='utf-8') as f:
        samples = json.load(f)
    
    # Count annotations
    counts = {
        '更相关': 0,  # better
        '相当': 0,    # same
        '更差': 0     # worse
    }
    
    for sample in samples:
        note = sample.get('note', '').strip()
        if note in counts:
            counts[note] += 1
        elif note == '':
            print(f"⚠️  Sample {sample['id']} has no annotation!")
        else:
            print(f"⚠️  Sample {sample['id']} has invalid annotation: '{note}'")
    
    total = len(samples)
    better = counts['更相关']
    same = counts['相当']
    worse = counts['更差']
    
    # Pass threshold: 70% of total samples
    pass_threshold = int(total * 0.7)  # 7 for 10 samples, 14 for 20 samples
    passed = better >= pass_threshold
    
    # Summary
    summary = {
        'total': total,
        'better': better,  # PageIndex better
        'same': same,
        'worse': worse,
        'pass': passed,
        'pass_threshold': pass_threshold,
        'better_ratio': round(better / total, 3) if total > 0 else 0
    }
    
    print("\n" + "=" * 60)
    print("人工审核汇总")
    print("=" * 60)
    print(f"总样本数: {total}")
    print(f"PageIndex 更相关: {better} ({summary['better_ratio']:.1%})")
    print(f"两者相当: {same}")
    print(f"Baseline 更好: {worse}")
    print(f"通过阈值: ≥{pass_threshold}/{total} (70%)")
    print(f"结果: {'✅ PASS' if passed else '❌ FAIL'}")
    print("=" * 60)
    
    # Update canary report
    print(f"\n📝 Updating {canary_path}...")
    with open(canary_path, 'r', encoding='utf-8') as f:
        canary_report = json.load(f)
    
    canary_report['human_audit_summary'] = summary
    
    # Update verdict with OR-gate logic
    chapter_hit_ok = canary_report.get('chapter_hit_rate', 0) >= 0.6
    human_audit_ok = passed
    
    quality_ok = canary_report.get('delta_ndcg', 0) >= 8 and canary_report.get('p_value', 1) < 0.05
    latency_ok = canary_report.get('delta_p95_ms', 999) <= 5
    
    # OR-gate: chapter_hit_rate ≥ 0.6 OR human_audit ≥ 70%
    gate_pass = quality_ok and latency_ok and (chapter_hit_ok or human_audit_ok)
    
    if gate_pass:
        canary_report['verdict'] = 'PASS'
        if chapter_hit_ok and human_audit_ok:
            canary_report['verdict_reason'] = f'Both chapter hit rate and human audit pass (≥{pass_threshold}/{total} better)'
        elif human_audit_ok:
            canary_report['verdict_reason'] = f'Human audit confirms quality (≥{pass_threshold}/{total} better, OR-gate passed)'
        else:
            canary_report['verdict_reason'] = f'Chapter hit rate ≥ 0.6 (OR-gate passed)'
    else:
        canary_report['verdict'] = 'FAIL'
        canary_report['verdict_reason'] = 'Neither chapter_hit_rate nor human_audit meet threshold'
    
    canary_report['gate_logic'] = {
        'chapter_hit_ok': chapter_hit_ok,
        'human_audit_ok': human_audit_ok,
        'or_gate_pass': chapter_hit_ok or human_audit_ok
    }
    
    with open(canary_path, 'w', encoding='utf-8') as f:
        json.dump(canary_report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Updated canary report with human_audit_summary")
    
    # Final verdict
    print(f"\n【人审判定】")
    print(f"{better}/{total} 样本 PageIndex 表现更优 — {'通过' if passed else '未通过'}")
    
    # Print OR-gate status
    canary_report = {}
    if canary_path.exists():
        with open(canary_path, 'r', encoding='utf-8') as f:
            canary_report = json.load(f)
        
        chapter_hit = canary_report.get('chapter_hit_rate', 0)
        gate_pass = chapter_hit >= 0.6 or passed
        print(f"\n【OR 门禁】")
        print(f"  章节命中率: {chapter_hit:.2%} {'✅' if chapter_hit >= 0.6 else '❌'}")
        print(f"  人工审核: {better}/{total} {'✅' if passed else '❌'}")
        print(f"  最终判定: {'✅ PASS' if gate_pass else '❌ FAIL'} (OR 逻辑)")
    
    return summary

if __name__ == '__main__':
    summary = main()
    sys.exit(0 if summary['pass'] else 1)

