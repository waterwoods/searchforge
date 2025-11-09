# P95 Latency Optimization Suite

**目标**: 在质量不降的前提下，系统化将 P95 从 ~1250ms 压到 <1000ms

---

## 📦 完整交付清单

### 1. 新增文件 (4个)

| 文件 | 说明 |
|------|------|
| `services/fiqa_api/routes/admin.py` | `/api/admin/warmup` 端点实现 |
| `scripts/run_latency_grid.sh` | 延迟优化网格搜索脚本 |
| `scripts/analyze_latency_winners.py` | 结果分析与 winners 生成脚本 |
| `LATENCY_OPTIMIZATION_SUITE.md` | 本交付文档 |

### 2. 修改文件 (4个)

| 文件 | 主要变更 |
|------|---------|
| `services/fiqa_api/app_main.py` | 注册 admin router |
| `experiments/fiqa_suite_runner.py` | 添加 latency_breakdown_ms 输出 |
| `Makefile` | 新增 `latency-grid` 目标 |
| `scripts/run_latency_grid.sh` | 修改为使用 Python 分析脚本 |

---

## ⚙️ 参数网格配置

### 开发阈值
- **efSearch**: {32, 64, 96}
- **concurrency**: {4, 8, 12}
- **warm_cache**: {0, 100} (预热 0/100 条查询)
- **固定参数**: Top-K=10, MMR=false

### 数据集
- **Gold**: fiqa_10k_v1 + fiqa_qrels_10k_v1
- **Hard**: fiqa_10k_v1 + fiqa_qrels_hard_10k_v1

### 总实验数
- 3 (efSearch) × 3 (concurrency) × 2 (warmup) × 2 (datasets) = **36 experiments**

---

## 🔧 核心功能实现

### 1. `/api/admin/warmup` 端点

**位置**: `services/fiqa_api/routes/admin.py`

**功能**:
- 运行指定数量的预热查询 (default: 100)
- 填充 embedding cache, BM25 cache, 连接池
- 返回统计信息: 查询数, 延迟, cache hit rate

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/admin/warmup \
  -H 'Content-Type: application/json' \
  -d '{"limit": 100, "timeout_sec": 300}'
```

**响应示例**:
```json
{
  "ok": true,
  "queries_run": 100,
  "duration_ms": 15234.56,
  "avg_latency_ms": 152.34,
  "p95_latency_ms": 234.56,
  "cache_hits": 45,
  "cache_misses": 55,
  "cache_hit_rate": 0.45
}
```

### 2. 延迟优化网格脚本

**位置**: `scripts/run_latency_grid.sh`

**流程**:
1. **参数网格生成**: 36 种配置组合
2. **预热处理**: warm_cache > 0 时自动调用 `/api/admin/warmup`
3. **并行提交**: 使用 `PARALLEL=3` 控制并发
4. **轮询完成**: 最多 300 次轮询 (每 5 秒)
5. **结果采集**: 从 container 读取 metrics.json
6. **分析生成**: 调用 Python 脚本生成报告

**运行方式**:
```bash
# 使用 Makefile 目标 (推荐)
make latency-grid

# 或直接运行脚本
bash scripts/run_latency_grid.sh
```

### 3. Python 分析脚本

**位置**: `scripts/analyze_latency_winners.py`

**功能**:
- 读取所有实验的 metrics.json
- 计算参数影响分析 (efSearch, concurrency, warm_cache)
- 识别 winners (p95 < 1000ms && recall > 0.90)
- 生成三档推荐配置
- 输出详细报告

### 4. metrics.json 增强

**位置**: `experiments/fiqa_suite_runner.py`

**新增字段**:
```json
{
  "metrics": {
    "median_ms": 567.89,
    ...
  },
  "latency_breakdown_ms": {
    "search": 450.23,
    "serialize": 45.67,
    "cache_hit_rate": 0.45
  }
}
```

---

## 📊 产出报告

### 1. `reports/winners_latency.json`

包含所有 p95 < 1000ms 且 recall > 0.90 的配置:

```json
{
  "winners": [
    {
      "job_id": "abc123def456",
      "name": "exp_gold_ef64_c8_w100",
      "dataset_type": "gold",
      "ef_search": 64,
      "concurrency": 8,
      "warm_cache": 100,
      "recall_at_10": 0.923,
      "p95_ms": 876.5,
      "p50_ms": 543.2,
      "winner": true
    }
  ],
  "total_winners": 12,
  "target_p95_ms": 1000,
  "min_recall": 0.90,
  "recommendations": {
    "balanced": {
      "tier": 2,
      "description": "P95 < 1000ms with recall > 0.90 (RECOMMENDED)",
      "config": {
        "ef_search": 64,
        "concurrency": 8,
        "warm_cache": 100
      },
      "expected_performance": {
        "p95_ms": 876.5,
        "recall_at_10": 0.923
      },
      "is_default": true
    }
  }
}
```

### 2. `reports/latency_grid_all.json`

包含所有 36 个实验的完整数据，附带参数影响分析。

### 3. `reports/latency_grid_summary.txt`

人类可读的汇总报告，包含:
- 参数→p95 曲线 (efSearch, concurrency, warm_cache)
- 三档推荐配置 (Speed-Optimized / Balanced / Quality-Optimized)
- 默认策略建议

示例输出:
```
================================================================================
P95 LATENCY OPTIMIZATION SUMMARY
================================================================================

Total experiments: 36
Winners (p95 < 1000ms, recall > 0.90): 12

================================================================================
Dataset: GOLD
================================================================================

Parameter Impact:

efSearch Impact:
  efSearch= 32: avg_p95=  1234ms, avg_recall=0.875
  efSearch= 64: avg_p95=   987ms, avg_recall=0.915
  efSearch= 96: avg_p95=   876ms, avg_recall=0.935

Concurrency Impact:
  concurrency= 4: avg_p95=  1123ms, avg_recall=0.905
  concurrency= 8: avg_p95=   945ms, avg_recall=0.910
  concurrency=12: avg_p95=   876ms, avg_recall=0.910

Warmup Impact:
  warm_cache=  0: avg_p95=  1087ms
  warm_cache=100: avg_p95=   923ms

================================================================================
RECOMMENDED CONFIGURATIONS
================================================================================

Tier 2: P95 < 1000ms with recall > 0.90 (RECOMMENDED)
  efSearch=64, concurrency=8, warm_cache=100
  Expected: p95=876ms, recall=0.923
  ⭐ DEFAULT RECOMMENDATION

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

---

## 🚀 使用方法

### 快速开始

```bash
# 1. 启动服务
make dev-up

# 2. 预热检查
make warmup

# 3. 运行延迟优化套件
make latency-grid
```

### 查看结果

```bash
# 查看汇总报告
cat reports/latency_grid_summary.txt

# 查看 winners
cat reports/winners_latency.json | jq '.winners[] | select(.winner==true)'

# 查看完整数据
cat reports/latency_grid_all.json | jq '.parameter_analysis'
```

---

## 🎯 验收标准

### 功能层面 ✅

- [x] 参数网格: efSearch ∈ {32,64,96}, concurrency ∈ {4,8,12}, warm_cache ∈ {0,100}
- [x] 数据集覆盖: Gold 和 Hard 各跑一轮
- [x] 缓存/预热: 实现 `/api/admin/warmup` 端点
- [x] 延迟分解: latency_breakdown_ms (search/serialize/cache_hit_rate)
- [x] 成本追踪: cost_per_query 在 metrics 中
- [x] 产出报告: winners_latency.json 和 latency_grid_summary.txt

### 性能层面 ⏳ (需实测)

- [ ] 找到至少 1 个配置: p95 < 1000ms && recall > 0.90
- [ ] 参数→p95 曲线清晰展示
- [ ] 三档推荐配置合理

---

## 🔍 技术细节

### 并发控制

**问题**: 36 个实验串行运行耗时过长

**解决**: 
- 使用 `PARALLEL=3` 控制并发提交
- 每批次提交后 sleep 2s 避免 API 过载
- 轮询检查状态，不阻塞主流程

### 容器内文件读取

**问题**: metrics.json 在容器内，宿主机无法直接读取

**解决**:
```bash
docker compose exec -T rag-api cat /app/.runs/{job_id}/metrics.json
```

### 预热时机

**问题**: warm_cache=100 时需要在实验前预热

**解决**:
- 在提交实验前检查 `warm_cache` 值
- 如果 > 0，先调用 `/api/admin/warmup?limit={warm_cache}`
- 记录预热时间和 cache hit rate

---

## 📝 限制与未来优化

### 当前限制

1. **预热粒度**: 预热查询是固定的 20 个样本查询循环
2. **并发限制**: PARALLEL=3 是硬编码的
3. **超时处理**: 如果某个实验超时，会阻塞后续实验

### 未来优化方向

1. **自适应预热**: 根据 cache hit rate 动态调整预热查询数
2. **智能参数搜索**: 使用贝叶斯优化代替网格搜索
3. **实时监控**: 添加 Prometheus metrics 追踪实验进度
4. **断点续传**: 支持失败实验的重试和断点续传

---

## 📚 相关文档

- `QUICKSTART_DEV.md` - 开发环境快速上手
- `docs/DEV_MODE_CONFIG.md` - 开发模式配置详解
- `DELIVERY_REPORT.md` - 守门人交付报告

---

**维护者**: AI (Cursor)  
**审核者**: andy  
**版本**: v1.0  
**日期**: 2025-11-07  
**状态**: ✅ 完整实现，待实测验证


