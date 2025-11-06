#!/usr/bin/env python3
"""快速注入测试数据到 core.metrics（用于验收 app_v2）"""
import sys
import time
import random
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.metrics import metrics_sink

def inject_realistic_samples(count=300, duration_sec=60):
    """注入真实感的测试样本（模拟 60s 的流量，QPS=5）"""
    print(f"[INJECT] 开始注入 {count} 条样本（模拟 {duration_sec}s 流量）...")
    
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - (duration_sec * 1000)
    
    # 模拟不同的性能特征
    base_latencies = [45, 52, 48, 55, 60, 58, 62, 70, 65, 58]
    base_recalls = [0.82, 0.85, 0.83, 0.87, 0.84, 0.86, 0.85, 0.88, 0.84, 0.86]
    
    for i in range(count):
        # 均匀分布在 60s 时间窗口内
        ts = start_ms + int((i / count) * duration_sec * 1000)
        
        # 添加一些变化：模拟性能波动
        variation = random.uniform(0.8, 1.2)
        spike = 1.5 if i % 50 == 0 else 1.0  # 每 50 个样本有一次尖峰
        
        latency = base_latencies[i % len(base_latencies)] * variation * spike
        recall = min(1.0, base_recalls[i % len(base_recalls)] * random.uniform(0.95, 1.05))
        
        sample = {
            "ts": int(ts),
            "latency_ms": round(latency, 2),
            "recall_at10": round(recall, 4),
            "mode": "on",
            "profile": "balanced"
        }
        
        metrics_sink.push(sample)
        
        if (i + 1) % 50 == 0:
            print(f"[INJECT] 进度: {i+1}/{count} ({(i+1)/count*100:.0f}%)")
    
    print(f"[INJECT] ✅ 完成！注入 {count} 条样本")
    print(f"[INJECT] 时间跨度: {duration_sec}s (从 {start_ms} 到 {now_ms})")
    
    # 验证
    samples = metrics_sink.snapshot_last_60s(int(time.time() * 1000))
    print(f"[INJECT] 验证: core.metrics 中有 {len(samples)} 条 60s 内的样本")

if __name__ == "__main__":
    inject_realistic_samples(count=300, duration_sec=60)

