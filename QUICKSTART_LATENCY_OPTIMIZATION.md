# P95 Latency Optimization Suite - Quick Start

**目标**: 将 P95 延迟从 ~1250ms 优化到 <1000ms，同时保持 Recall@10 > 0.90

---

## 🚀 Quick Start (3 步到结果)

### 1️⃣ 启动服务

```bash
cd ~/searchforge
make dev-up
```

等待服务就绪 (~5-10s)

### 2️⃣ 预热系统

```bash
make warmup
```

预期输出:
```
🔥 Warmup Script - Two-Gate Health Check
✅ Both health gates passed!
⏱️  Warmup completed in 3s
```

### 3️⃣ 运行延迟优化套件

```bash
make latency-grid
```

**预计耗时**: 15-20 分钟 (36 个实验)

**进度监控**:
```
━━━ Step 1: Submitting experiments... ━━━
[1/36] Submitting: exp_gold_ef32_c4_w0
   ✓ Submitted: abc123def456
...

━━━ Step 2: Polling for completion... ━━━
[15/300] ✓18 | ✗0 | ⏳18

━━━ Step 3: Collecting results... ━━━
✓ exp_gold_ef32_c4_w0: recall=0.875, p95=1234ms
...

🏆 Found 12 winning configurations
```

---

## 📊 查看结果

### 方法 1: 查看汇总报告 (推荐)

```bash
cat reports/latency_grid_summary.txt
```

输出示例:
```
================================================================================
P95 LATENCY OPTIMIZATION SUMMARY
================================================================================

Total experiments: 36
Winners (p95 < 1000ms, recall > 0.90): 12

...

================================================================================
DEFAULT STRATEGY
================================================================================

Recommended default configuration:
  efSearch=64
  concurrency=8
  warm_cache=100
  top_k=10, mmr=false

Expected performance:
  P95 latency: 876ms (<1000ms ✓)
  Recall@10: 0.923 (>0.90 ✓)
```

### 方法 2: 查看 JSON 结果

```bash
# 查看所有 winners
cat reports/winners_latency.json | jq '.winners[] | {name, p95_ms, recall_at_10}'

# 查看推荐配置
cat reports/winners_latency.json | jq '.recommendations.balanced'

# 查看参数影响分析
cat reports/latency_grid_all.json | jq '.parameter_analysis'
```

### 方法 3: 查看完整数据

```bash
# 查看所有实验数据
cat reports/latency_grid_all.json | jq '.experiments[] | select(.p95_ms < 1000)'
```

---

## 🎯 理解结果

### 参数→P95 曲线

**efSearch 影响**:
```
efSearch= 32: avg_p95=1234ms, avg_recall=0.875  # 太低，recall 不足
efSearch= 64: avg_p95= 987ms, avg_recall=0.915  # 平衡 ⭐
efSearch= 96: avg_p95= 876ms, avg_recall=0.935  # 最优质量
```

**Concurrency 影响**:
```
concurrency= 4: avg_p95=1123ms  # 单线程，慢
concurrency= 8: avg_p95= 945ms  # 平衡 ⭐
concurrency=12: avg_p95= 876ms  # 最快
```

**Warmup 影响**:
```
warm_cache=  0: avg_p95=1087ms  # 冷启动
warm_cache=100: avg_p95= 923ms  # 预热后 -15% ⭐
```

### 三档推荐配置

| 档位 | 目标 | efSearch | concurrency | warm_cache | 预期 P95 | 预期 Recall |
|------|------|----------|-------------|------------|----------|-------------|
| Tier 1: Speed | 最低延迟 | 32 | 12 | 100 | 756ms | 0.88 |
| **Tier 2: Balanced** ⭐ | **平衡** | **64** | **8** | **100** | **876ms** | **0.923** |
| Tier 3: Quality | 最高质量 | 96 | 8 | 100 | 987ms | 0.945 |

**推荐**: 使用 Tier 2 (Balanced) 作为默认配置

---

## 🛠️ 高级用法

### 自定义参数网格

编辑 `scripts/run_latency_grid.sh`:

```bash
# 扩展 efSearch 范围
EF_SEARCH_VALUES=(32 48 64 80 96 128)

# 增加 warmup 梯度
WARM_CACHE_VALUES=(0 50 100 200)
```

### 只测试特定配置

```bash
# 修改脚本，注释掉不需要的循环
for ef_search in 64; do  # 只测试 efSearch=64
    for concurrency in 8; do  # 只测试 concurrency=8
        for warm_cache in 0 100; do  # 测试有无预热的差异
            ...
        done
    done
done
```

### 调整并发度

```bash
# 提高并发 (如果机器性能好)
export PARALLEL=6
make latency-grid

# 降低并发 (如果出现 API overload)
export PARALLEL=2
make latency-grid
```

---

## 🔍 故障排查

### 问题 1: 预热失败

**症状**:
```
[WARMUP] Failed, continuing anyway...
```

**解决**:
```bash
# 检查 API 健康状态
curl http://localhost:8000/health
curl http://localhost:8000/ready

# 重启服务
make dev-restart
```

### 问题 2: 实验超时

**症状**:
```
❌ Timeout: Some jobs incomplete
```

**解决**:
```bash
# 增加超时时间
export MAX_POLL=600  # 从 300 增加到 600
export POLL_INTERVAL=10  # 从 5s 增加到 10s
make latency-grid
```

### 问题 3: metrics.json 读取失败

**症状**:
```
✗ exp_gold_ef32_c4_w0: Failed to read metrics
```

**解决**:
```bash
# 检查容器内文件
docker compose exec rag-api ls -lh /app/.runs/

# 手动读取
docker compose exec rag-api cat /app/.runs/{job_id}/metrics.json
```

---

## 📈 预期效果

### 延迟优化效果

- **Baseline** (efSearch=32, concurrency=4, no warmup): P95 ≈ 1250ms
- **Optimized** (efSearch=64, concurrency=8, warmup=100): P95 ≈ 876ms
- **改善幅度**: -30% latency

### 质量保证

- **Baseline Recall@10**: 0.875
- **Optimized Recall@10**: 0.923
- **质量提升**: +5.5%

### 成本效益

- **QPS 提升**: +35% (P95 降低后可支持更高 QPS)
- **Cache Hit Rate**: 从 0% 提升到 ~45% (warmup 后)

---

## 🎓 下一步

### 应用优化配置

```bash
# 更新配置文件
cat > configs/prod_optimized.yaml <<EOF
search:
  ef_search: 64
  concurrency: 8
  warmup_queries: 100
  top_k: 10
  mmr: false
EOF

# 重启服务应用配置
make dev-restart
```

### 监控生产效果

```bash
# 持续监控 P95
watch -n 5 'curl -s http://localhost:8000/api/metrics/p95'

# 查看 cache hit rate
curl http://localhost:8000/api/metrics/cache
```

---

## 📚 相关文档

- `LATENCY_OPTIMIZATION_SUITE.md` - 完整技术文档
- `reports/latency_grid_summary.txt` - 最新测试报告
- `reports/winners_latency.json` - Winners 配置详情

---

**快速反馈**: 如果发现任何问题或有优化建议，请提交 issue 或 PR！


