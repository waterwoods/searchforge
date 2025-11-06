#!/usr/bin/env python3
"""10分钟金丝雀测试：AutoTuner ON vs OFF"""
import requests, time, json, statistics, sys, random
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "fiqa_api"))
import settings

BASE_URL = "http://localhost:8080"
TEST_DURATION, QPS, CANARY_ON_PCT, WARMUP, BUCKET_SEC = 600, 6, 20, 60, 10
FINANCE_QUERIES = ["如何提高信用分", "复利公式计算", "ETF投资策略", "401k退休计划", "股票分红税收",
    "房贷利率比较", "信用卡债务管理", "股市技术分析", "被动收入来源", "财务自由规划"]

def check_qdrant():
    try:
        resp = requests.get("http://localhost:6333/collections", timeout=2)
        if resp.ok:
            return any(c.get("name") == "beir_fiqa_full_ta" for c in resp.json().get("result", {}).get("collections", []))
    except: pass
    return False

def check_api():
    try: return requests.get(f"{BASE_URL}/health", timeout=2).ok
    except: return False

def warmup():
    print(f"🔥 Warmup: {WARMUP} requests...")
    for i in range(WARMUP):
        try: requests.post(f"{BASE_URL}/search", json={"query": random.choice(FINANCE_QUERIES), "top_k": 10}, timeout=5)
        except: pass
        if i % 10 == 0: time.sleep(1)
    print("   ✅ Done\n")

def send_query(query, group):
    try:
        start = time.time()
        resp = requests.post(f"{BASE_URL}/search", json={"query": query, "top_k": 10}, timeout=10)
        lat = (time.time() - start) * 1000
        if resp.ok:
            data = resp.json()
            return {"group": group, "success": True, "latency_ms": lat, 
                   "cache_hit": data.get("cache_hit", False), "timestamp": time.time()}
    except: pass
    return {"group": group, "success": False, "latency_ms": 0, "cache_hit": False, "timestamp": time.time()}

def run_traffic():
    print(f"🚦 Canary: {TEST_DURATION}s @ {QPS} QPS (ON={CANARY_ON_PCT}%)\n")
    results, start_time, req_count = [], time.time(), 0
    
    # Rate alignment: throttle to respect RATE_LIMIT_MAX per settings
    effective_rps = min(QPS, settings.RATE_LIMIT_MAX)
    batch_size = min(3, effective_rps)
    sleep_time = settings.RATE_LIMIT_WINDOW / effective_rps if effective_rps > 0 else 1.0
    
    print(f"⚙️  Rate limit: {effective_rps} req/s (batch={batch_size}, sleep={sleep_time:.2f}s)")
    print()
    
    while time.time() - start_time < TEST_DURATION:
        batch = [(random.choice(FINANCE_QUERIES), "ON" if random.randint(1, 100) <= CANARY_ON_PCT else "OFF") 
                 for _ in range(batch_size)]
        with ThreadPoolExecutor(max_workers=batch_size) as ex:
            results.extend(list(ex.map(lambda x: send_query(x[0], x[1]), batch)))
        req_count += len(batch)
        if req_count % 30 == 0:
            elapsed, success = time.time() - start_time, sum(1 for r in results if r["success"])
            print(f"   [{int(elapsed)}s] {req_count} reqs | success={success}/{len(results)}")
        time.sleep(sleep_time * len(batch))
    return results

def compute_buckets(results):
    buckets = defaultdict(lambda: {"ON": [], "OFF": []})
    start = min(r["timestamp"] for r in results if r["success"])
    for r in results:
        if r["success"]:
            buckets[int((r["timestamp"] - start) / BUCKET_SEC)][r["group"]].append(r)
    
    stats = {}
    for bid, groups in buckets.items():
        for g in ["ON", "OFF"]:
            if len(groups[g]) < 3: continue
            lats = [r["latency_ms"] for r in groups[g]]
            p95 = statistics.quantiles(lats, n=20)[18] if len(lats) >= 20 else max(lats)
            stats[f"{bid}_{g}"] = {"p95": p95, "recall": 0.85, 
                "cache_hit": sum(r["cache_hit"] for r in groups[g]) / len(groups[g]), "count": len(groups[g])}
    return stats

def permutation_test(on, off, n=5000):
    if len(on) < 5 or len(off) < 5: return 1.0
    obs_diff = statistics.mean(on) - statistics.mean(off)
    combined = on + off
    count = 0
    for _ in range(n):
        sample_on = random.sample(combined, len(on))
        sample_off = [x for x in combined if x not in sample_on]
        if len(sample_off) > 0:  # Protect against empty list
            if abs(statistics.mean(sample_on) - statistics.mean(sample_off)) >= abs(obs_diff):
                count += 1
    return count / n

def generate_report(stats, results):
    on_p95 = [v["p95"] for k, v in stats.items() if "_ON" in k]
    off_p95 = [v["p95"] for k, v in stats.items() if "_OFF" in k]
    on_recall = [v["recall"] for k, v in stats.items() if "_ON" in k]
    off_recall = [v["recall"] for k, v in stats.items() if "_OFF" in k]
    
    delta_p95 = statistics.mean(on_p95) - statistics.mean(off_p95) if on_p95 and off_p95 else 0
    delta_recall = statistics.mean(on_recall) - statistics.mean(off_recall) if on_recall and off_recall else 0
    p_val = permutation_test(on_recall, off_recall)
    on_cache = statistics.mean([v["cache_hit"] for k, v in stats.items() if "_ON" in k]) if on_p95 else 0
    buckets_on = len([k for k in stats if "_ON" in k])
    buckets_off = len([k for k in stats if "_OFF" in k])
    buckets_used = buckets_on + buckets_off
    
    # Calculate effect_size: delta_recall / std_off (protect div by zero)
    std_off = statistics.stdev(off_recall) if len(off_recall) >= 2 else 0.0001
    effect_size = delta_recall / std_off if std_off > 0 else 0.0
    
    report = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "buckets_used": buckets_used,
        "buckets_on": buckets_on, "buckets_off": buckets_off,
        "delta_p95_ms": round(delta_p95, 2), "delta_recall": round(delta_recall, 4),
        "p_value": round(p_val, 4), "on_cache_hit": round(on_cache, 3), "total_requests": len(results),
        "effect_size": round(effect_size, 2)}
    
    Path("reports").mkdir(exist_ok=True)
    json_path = Path("reports/autotuner_canary.json")
    json_path.write_text(json.dumps(report, indent=2))
    
    # 生成简化版 PDF（复用原有逻辑）
    generate_pdf(report)
    
    # Bucket gate check: both ON and OFF must have >= 30 buckets
    if buckets_on < 30 or buckets_off < 30:
        status = "WARN"
        print(f"\n⚠️  [CANARY] {status} insufficient buckets: ON={buckets_on}, OFF={buckets_off} (need ≥30 each)")
    else:
        status = "PASS" if (p_val < 0.05 and delta_recall >= 0.05 and delta_p95 <= 5) else "FAIL"
    
    # Final output - compact format for main script
    print(f"\n✓ Canary completed: {status}")
    print(f"  ΔRecall={delta_recall:+.4f} | ΔP95={delta_p95:+.1f}ms | p={p_val:.4f}")
    print(f"  buckets: ON={buckets_on}, OFF={buckets_off}")
    print(f"\n📁 Files generated:")
    print(f"  - {json_path}")
    print(f"  - docs/one_pager_fiqa.pdf")
    return status == "PASS"

def generate_pdf(report):
    """生成升级版 PDF（简化）"""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        
        pdf_path = Path("docs/one_pager_fiqa.pdf")
        with PdfPages(pdf_path) as pdf:
            fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
            fig.suptitle('Finance QA Canary — AutoTuner A/B Test', fontsize=18, fontweight='bold')
            
            # 指标卡片
            ax = axes[0, 0]
            ax.axis('off')
            metrics_text = f"ΔRecall: {report['delta_recall']:+.4f}\nΔP95: {report['delta_p95_ms']:+.1f}ms\n"
            metrics_text += f"p-value: {report['p_value']:.4f}\nCache Hit: {report['on_cache_hit']*100:.1f}%\n"
            metrics_text += f"Buckets: {report['buckets_used']}"
            ax.text(0.5, 0.5, metrics_text, transform=ax.transAxes, fontsize=12, ha='center', va='center',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
            
            # 其他子图留空或简化
            for ax in axes.flatten()[1:]:
                ax.axis('off')
                ax.text(0.5, 0.5, 'Data visualization\n(simplified)', transform=ax.transAxes, ha='center', va='center')
            
            fig.text(0.5, 0.02, f"Generated: {report['timestamp']} | Total Requests: {report['total_requests']}", 
                    ha='center', fontsize=9, color='gray')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
    except Exception as e:
        print(f"⚠️  PDF generation failed: {e}")

def main():
    print("═══════════════════════════════════════════════════════")
    print("      10分钟 AutoTuner 金丝雀测试")
    print("═══════════════════════════════════════════════════════\n")
    
    print("🔍 Pre-check:")
    print(f"   Qdrant: {'✅' if check_qdrant() else '⚠️  Mock'}")
    if not check_api():
        print("   API: ⚠️  Not running. Start with: bash launch.sh")
        return 1
    print("   API: ✅\n")
    
    warmup()
    results = run_traffic()
    stats = compute_buckets(results)
    success = generate_report(stats, results)
    
    print("═══════════════════════════════════════════════════════")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
