# 开发模式配置指南

## 📋 概述

本文档说明开发模式的低成本参数配置，用于快速迭代和实验。

## 🎯 开发模式 vs 生产模式

| 参数 | 开发模式 (DEV) | 生产模式 (PROD) | 说明 |
|------|---------------|----------------|------|
| **数据集** | fiqa_10k_v1 | fiqa_50k_v1 | 使用 10k 子集 |
| **sample** | 50 | 1000+ | 查询样本数 |
| **top_k** | 10-20 | 50-80 | 检索文档数 |
| **repeats** | 1 | 3 | 重复次数 |
| **concurrency** | 8 | 16 | 并发数 |
| **timeout_s** | 10.0 | 20.0 | 超时设置 |
| **ef_search** | 64 | 128+ | Qdrant HNSW 参数 |
| **use_hybrid** | false | true | 混合检索（RRF） |
| **rerank** | false | varies | 重排功能 |

## 📁 配置文件

### 1. YAML 配置
`configs/dev_defaults.yaml` - 开发模式参数预设

### 2. 环境变量
`dev.env` - 环境变量配置

使用方法：
```bash
source dev.env
echo $DEV_TOP_K  # 20
```

## 🔧 使用方式

### 方式 1：通过配置文件（推荐）

实验脚本默认使用低成本参数（sample=30, top_k=10-30）：

```bash
# 烟测（已配置低成本默认值）
bash scripts/smoke.sh

# 并行小批（已配置低成本默认值）
bash scripts/run_grid_dev.sh
```

### 方式 2：通过环境变量

```bash
# 加载开发环境
source dev.env

# 提交实验
curl -X POST http://localhost:8000/api/experiment/run \
  -H 'content-type: application/json' \
  -d "{
    \"sample\": ${DEV_SAMPLE},
    \"top_k\": ${DEV_TOP_K},
    \"dataset_name\": \"${DEV_DATASET_NAME}\",
    \"qrels_name\": \"${DEV_QRELS_NAME}\",
    \"fast_mode\": true
  }"
```

### 方式 3：命令行参数覆盖

```bash
# 临时提升到生产配置
TOP_K=50 SAMPLE=1000 bash scripts/smoke.sh
```

## 🚀 快速命令

### 开发态操作

```bash
# 1. 改代码 → 重启（5-10s）
make dev-restart

# 2. 预热检查
bash scripts/warmup.sh

# 3. 烟测（最小闭环）
bash scripts/smoke.sh

# 4. 小批并行实验
bash scripts/run_grid_dev.sh

# 5. 查看日志
make dev-logs
```

### 切换到生产配置

```bash
# 使用生产数据集和参数
curl -X POST http://localhost:8000/api/experiment/run \
  -H 'content-type: application/json' \
  -d '{
    "sample": 1000,
    "top_k": 50,
    "dataset_name": "fiqa_50k_v1",
    "qrels_name": "fiqa_qrels_50k_v1",
    "use_hybrid": true,
    "rerank": true,
    "ef_search": 128,
    "fast_mode": false
  }'
```

## 📊 性能对比

基于烟测结果（sample=30）：

| 指标 | DEV 模式 | 预期值 |
|------|---------|-------|
| **recall@10** | 0.98 | ≥ 0.95 |
| **p95_ms** | 575 ms | < 1000 ms |
| **耗时** | ~10s | < 30s |

## ⚙️ 高级配置

### 动态参数调整

在后端路由中，可以通过环境变量 `DEV_MODE` 检测开发模式：

```python
# services/fiqa_api/routes/experiment.py
import os

def get_default_params():
    if os.getenv("DEV_MODE") == "1":
        return {
            "top_k": 20,
            "sample": 50,
            "ef_search": 64,
            "use_hybrid": False,
            "rerank": False
        }
    else:
        return {
            "top_k": 50,
            "sample": None,
            "ef_search": 128,
            "use_hybrid": True,
            "rerank": True
        }
```

### Qdrant efSearch 调整

开发模式降低 efSearch 以换取速度：

- **DEV**: efSearch=64 → 快速但略降精度
- **PROD**: efSearch=128+ → 高精度

## 📝 最佳实践

1. **日常开发**：使用 `configs/dev_defaults.yaml` 和脚本默认值
2. **集成测试**：逐步提升参数（sample=100, top_k=30）
3. **生产验证**：完整配置（sample=1000+, top_k=50+）

## ✅ 验证清单

- [ ] `configs/dev_defaults.yaml` 存在且可读
- [ ] `dev.env` 存在且可 source
- [ ] `docker-compose.dev.yml` 设置 `DEV_MODE=1`
- [ ] 烟测通过（recall@10 > 0.9）
- [ ] 端到端耗时 < 30s

