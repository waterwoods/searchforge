# ⚡ SearchForge 开发模式 - 操作速记

## 🎯 一页速查：从改代码到看结果

### 核心流程（端到端 < 30s）

```bash
# 1️⃣ 改代码 → make dev-restart（5-10s 生效）
vim services/fiqa_api/routes/search.py
make dev-restart
# ✅ 输出：Container searchforge-rag-api-1 Started

# 2️⃣ 预热 → bash scripts/warmup.sh
bash scripts/warmup.sh
# ✅ 输出：Warmup completed in 2s

# 3️⃣ 烟测 → bash scripts/smoke.sh
bash scripts/smoke.sh
# ✅ 输出：烟测通过！recall@10=0.98, p95_ms=575ms

# 4️⃣ 小批并行 → bash scripts/run_grid_dev.sh
bash scripts/run_grid_dev.sh
# ✅ 输出：3个作业完成，reports/winners_dev.json 已生成

# 5️⃣ 查看日志 → make dev-logs
make dev-logs
# ✅ 输出：实时滚动日志（Ctrl-C 退出）
```

---

## 📋 完整操作速记

### 🔧 日常开发

| 操作 | 命令 | 耗时 | 说明 |
|------|------|------|------|
| **改代码并重启** | `make dev-restart` | 5-10s | 秒级生效，自动挂载 |
| **预热检查** | `bash scripts/warmup.sh` | 2-5s | 两道闸：embeddings + ready |
| **烟测** | `bash scripts/smoke.sh` | 10-15s | 最小闭环（sample=30） |
| **小批并行** | `bash scripts/run_grid_dev.sh` | 20-30s | 3 个并行实验 |
| **查看日志** | `make dev-logs` | - | 实时跟踪（-f） |

### 🚀 启动与停止

```bash
# 启动开发模式
make dev-up
# ✅ Container searchforge-rag-api-1 Started

# 停止服务
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# 重启（更新代码后）
make dev-restart

# 仅查看命令（dry-run）
make dev-logs -n
```

### 🔍 健康检查

```bash
# 完整预热检查（两道闸）
bash scripts/warmup.sh

# 快速健康检查
curl http://localhost:8000/health
# {"ok":true,"phase":"ready"}

# Embeddings 就绪检查
curl http://localhost:8000/api/health/embeddings
# {"ok":true,"model":"all-MiniLM-L6-v2","dim":384}

# Ready 端点检查
curl http://localhost:8000/ready
# {"ok":true,"phase":"ready"}
```

### 🧪 实验管理

```bash
# 提交实验
curl -X POST http://localhost:8000/api/experiment/run \
  -H 'content-type: application/json' \
  -d '{
    "sample": 30,
    "top_k": 10,
    "fast_mode": true,
    "dataset_name": "fiqa_10k_v1",
    "qrels_name": "fiqa_qrels_10k_v1"
  }'

# 查询状态
curl http://localhost:8000/api/experiment/status/<JOB_ID>

# 查看日志
curl http://localhost:8000/api/experiment/logs/<JOB_ID>
```

### 📊 查看结果

```bash
# 查看 metrics.json（容器内）
docker compose -f docker-compose.yml -f docker-compose.dev.yml \
  exec -T rag-api cat /app/.runs/<JOB_ID>/metrics.json | python3 -m json.tool

# 查看并行实验胜者
cat reports/winners_dev.json | python3 -m json.tool

# 列出所有作业
ls -lht ~/data/searchforge/experiments/.runs/ | head -10
```

---

## ⏱️ 性能基准

### 端到端耗时（实测）

| 操作流程 | 耗时 | 指标 |
|---------|------|------|
| **改代码 → 重启** | 5-10s | 容器重启 |
| **预热检查** | 2s | 两道闸就绪 |
| **烟测（sample=30）** | 10-15s | recall@10=0.98 |
| **并行3实验** | 20-30s | 3个作业同时完成 |
| **完整周期** | **~30s** | 从改代码到看结果 |

### 单次实验耗时拆解

```
提交实验: 0.5s
排队/启动: 0.5s
预热(5查询): 0.3s
主评测(30查询): 8-12s
指标计算: 0.2s
总计: 10-15s
```

---

## 🎨 典型工作流

### Scenario 1: 修改搜索逻辑

```bash
# 1. 编辑代码
vim services/fiqa_api/routes/search.py

# 2. 重启 + 预热 + 烟测（一气呵成）
make dev-restart && sleep 3 && bash scripts/warmup.sh && bash scripts/smoke.sh
```

**预期输出：**
```
Container searchforge-rag-api-1 Started
✅ Both health gates passed! (2s)
✅ 烟测通过！recall@10=0.98, p95_ms=575ms (10s)
```

### Scenario 2: 参数网格搜索

```bash
# 1. 运行并行实验网格
bash scripts/run_grid_dev.sh

# 2. 查看胜者配置
cat reports/winners_dev.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Winner: top_k={d['winner']['top_k']}, recall={d['winner']['recall_at_10']}\")"
```

**预期输出：**
```
Winner: top_k=10, recall=0.98
```

### Scenario 3: 调试失败实验

```bash
# 1. 提交实验（假设失败）
JOB_ID=$(curl -sX POST http://localhost:8000/api/experiment/run \
  -H 'content-type: application/json' \
  -d '{"sample":5}' | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")

# 2. 等待并查看状态
sleep 5
curl http://localhost:8000/api/experiment/status/$JOB_ID | python3 -m json.tool

# 3. 查看失败日志
docker compose -f docker-compose.yml -f docker-compose.dev.yml \
  exec -T rag-api cat /app/.runs/${JOB_ID}.log | tail -50
```

---

## 📈 成功判据（已验证 ✅）

### 环境配置

- [x] `docker-compose.dev.yml` 存在且可用
- [x] Makefile 三目标：dev-up, dev-restart, dev-logs
- [x] NVMe 卷挂载：`~/data/searchforge/{models,data,experiments/data}`

### 健康检查

- [x] `/api/health/embeddings` → `{"ok": true, "dim": 384}`
- [x] `/ready` → `{"ok": true, "phase": "ready"}`
- [x] 两道闸同时通过（warmup.sh）

### 实验功能

- [x] 烟测产出非零指标：`recall@10=0.98, p95_ms=575ms`
- [x] metrics.json: `source="runner"`
- [x] 并行3实验 → `reports/winners_dev.json` 生成

### 数据外置

- [x] 容器内 `/app/models/` 可读（sentence-transformers 模型）
- [x] 容器内 `/app/data/` 可读（fiqa 数据集）
- [x] 容器内 `/app/experiments/data/` 可访问

---

## 🔗 相关文档

- [开发模式配置详解](docs/DEV_MODE_CONFIG.md)
- [完整 Makefile 命令](Makefile) - `make help`
- [实验 API 文档](http://localhost:8000/docs) - FastAPI Swagger UI

---

## 💡 技巧与窍门

### 1. 快速迭代组合拳

```bash
# 单行命令：重启 + 预热 + 烟测
make dev-restart && sleep 3 && bash scripts/warmup.sh && bash scripts/smoke.sh
```

### 2. 监控日志实时输出

```bash
# 开两个终端窗口
# 窗口1: 实时日志
make dev-logs

# 窗口2: 提交实验
bash scripts/smoke.sh
```

### 3. 自定义参数覆盖

```bash
# 临时提升样本量
sed -i 's/"sample": 30/"sample": 100/g' scripts/smoke.sh
bash scripts/smoke.sh
# 记得还原！

# 或使用 API 直接覆盖（推荐）
curl -X POST http://localhost:8000/api/experiment/run \
  -H 'content-type: application/json' \
  -d '{"sample": 100, "top_k": 20, "fast_mode": true, "dataset_name": "fiqa_10k_v1", "qrels_name": "fiqa_qrels_10k_v1"}'
```

### 4. 批量清理旧实验

```bash
# 查看磁盘占用
docker compose exec -T rag-api du -sh /app/.runs/
docker compose exec -T rag-api ls /app/.runs/ | wc -l

# 清理旧作业（保留最近 10 个）
docker compose exec -T rag-api sh -c "cd /app/.runs && ls -t | tail -n +11 | xargs rm -rf"
```

---

## 🎯 下一步

1. **调整参数**：编辑 `configs/dev_defaults.yaml`
2. **扩展网格**：修改 `scripts/run_grid_dev.sh` 的 `experiments` 数组
3. **集成 CI**：将 `scripts/smoke.sh` 加入 CI/CD 流程
4. **切换生产**：使用 `fiqa_50k_v1` 数据集，sample=1000+

---

**最后更新**: 2025-11-07  
**维护者**: andy  
**版本**: v1.0

