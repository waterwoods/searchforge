# 守门人变更清单

**执行时间**: 2025-11-07  
**目标**: 固化"6点提速配置"为默认路径，默认走快路

---

## 📋 1. 变更文件清单

### 新增文件

| 文件路径 | 说明 |
|---------|------|
| `.github/pull_request_template.md` | PR 模板，强制粘贴烟测指标与胜者配置 |
| `GATEKEEPER_CHANGES.md` | 本变更清单文档 |

### 修改文件

| 文件路径 | 主要变更 |
|---------|---------|
| `docker-compose.dev.yml` | 添加 `FAST_MODE_DEFAULT=1`，增强守门人标记 |
| `Makefile` | 新增 `preflight`, `warmup`, `smoke`, `grid-dev`, `full-validate` 目标；增强 help 文档 |
| `scripts/warmup.sh` | 添加守门人标记 |
| `scripts/smoke.sh` | 添加守门人标记与 FULL/PROD 模式警告 |
| `scripts/run_grid_dev.sh` | 添加守门人标记与 FULL/PROD 模式警告 |
| `scripts/full_validation.sh` | 添加守门人标记与 FULL/PROD 模式警告 |
| `.gitignore` | 重新组织并添加守门人标记，确保数据外置 |
| `.dockerignore` | 重新组织并添加守门人标记，轻仓构建 |

### 未改动文件

| 文件路径 | 说明 |
|---------|------|
| `docker-compose.yml` | 已有外置卷配置，无需修改 |
| `configs/dev_defaults.yaml` | 已有开发阈值配置，无需修改 |
| `dev.env` | 已有环境变量配置，无需修改 |
| `docs/DEV_MODE_CONFIG.md` | 已有完整文档，无需修改 |
| `QUICKSTART_DEV.md` | 已有快速上手指南，无需修改 |

---

## 🔍 2. 关键 diff 摘要

### A. docker-compose.dev.yml

```diff
   environment:
     PYTHONDONTWRITEBYTECODE: "1"
-    DEV_MODE: "1"
+    DEV_MODE: "1"  # 开发模式标识（守门人：默认走快路）
+    FAST_MODE_DEFAULT: "1"  # 默认快速模式
   volumes:
-    - ./experiments:/app/experiments:ro
+    # 【守门人】开发态只读挂载（代码热更新）
+    - ./experiments:/app/experiments:ro
```

### B. Makefile - 新增守门人目标

```makefile
# ========================================
# 守门人：快速开发闭环目标
# ========================================

preflight: ## 前置检查（DEV_MODE + 外置卷 + 健康闸）
warmup: ## 两道闸预热（embeddings + ready）
smoke: preflight warmup ## 烟测最小闭环（sample=30）
grid-dev: preflight warmup ## 并行小批实验（2-3槽）
full-validate: ## 完整验证流程（dev-restart → warmup → smoke → grid-dev）
```

### C. scripts/*.sh - 守门人标记与警告

```bash
# smoke.sh / run_grid_dev.sh / full_validation.sh
# 【守门人】默认走快路：sample=30, fast_mode=true, rerank=false

# 守门人：检查 FULL 或 PROD 模式标记
if [ "${FULL:-0}" = "1" ] || [ "${PROD:-0}" = "1" ]; then
    echo "🔴 警告：FULL=1 或 PROD=1 已设置，将运行完整/生产模式！"
    sleep 2
fi
```

### D. .github/pull_request_template.md - 强制烟测指标

```markdown
## ✅ 烟测指标（必填）

请在提交 PR 前运行烟测并粘贴结果：

Job ID: ___________________
recall_at_10: ______________
p95_ms: ___________________
source: runner
```

### E. .gitignore / .dockerignore - 守门人标记

```
# === 守门人：Git 忽略清单 ===
# 目标：轻仓仓库，数据外置

# 数据与模型（外置卷）
data/
models/
experiments/data/
```

---

## 🧪 3. 验证清单

### 3.1 配置验证

- ✅ `make help` 显示守门人目标
- ✅ `.github/pull_request_template.md` 存在且包含烟测指标要求
- ✅ `docker-compose.dev.yml` 设置 `DEV_MODE=1` 和 `FAST_MODE_DEFAULT=1`
- ✅ `.gitignore` 和 `.dockerignore` 标记守门人并忽略数据/模型/产物
- ✅ 所有脚本添加守门人标记与 FULL/PROD 警告

### 3.2 功能验证（需运行时验证）

**前置条件：** 服务需要运行（`make dev-up` 或 `make dev-restart`）

```bash
# 1. 验证 Makefile 目标
make help | grep "守门人"
# 预期：显示 preflight, warmup, smoke, grid-dev, full-validate

# 2. 验证 preflight 检查（需容器运行）
# make preflight
# 预期：检查 DEV_MODE、外置卷、健康端点

# 3. 验证 warmup 脚本（需容器运行）
# bash scripts/warmup.sh
# 预期：2-5s 内两道闸通过

# 4. 验证 smoke 脚本（需容器运行）
# bash scripts/smoke.sh
# 预期：10-15s 完成，产出 recall@10 和 p95_ms

# 5. 验证 grid-dev 脚本（需容器运行）
# bash scripts/run_grid_dev.sh
# 预期：20-30s 完成，生成 reports/winners_dev.json

# 6. 验证完整流程（需容器运行）
# bash scripts/full_validation.sh
# 预期：总耗时 < 30s
```

---

## ⏱️ 4. 性能基准（预期）

| 操作流程 | 预期耗时 | 关键指标 |
|---------|---------|---------|
| `make dev-restart` | 5-10s | 容器重启 |
| `make warmup` / `bash scripts/warmup.sh` | 2-5s | 两道闸就绪 |
| `make smoke` / `bash scripts/smoke.sh` | 10-15s | recall@10 > 0.9, p95_ms < 1000 |
| `make grid-dev` / `bash scripts/run_grid_dev.sh` | 20-30s | 3个作业完成 |
| `make full-validate` | < 30s | 端到端闭环 |

---

## 🔙 5. 如何回滚

### 方法 1: Git 回滚（推荐）

```bash
# 查看变更
git status
git diff

# 回滚所有变更
git checkout -- docker-compose.dev.yml Makefile scripts/*.sh .gitignore .dockerignore

# 删除新增文件
rm -f .github/pull_request_template.md GATEKEEPER_CHANGES.md
```

### 方法 2: 手动恢复

如果需要保留部分变更：

1. **恢复 Makefile**: 移除 `preflight`, `warmup`, `smoke`, `grid-dev`, `full-validate` 目标
2. **恢复脚本**: 移除脚本开头的守门人标记与 FULL/PROD 警告
3. **恢复 docker-compose.dev.yml**: 移除 `FAST_MODE_DEFAULT=1`
4. **删除 PR 模板**: `rm .github/pull_request_template.md`

---

## 📊 6. 成功判据

### 配置层面 ✅

- [x] Makefile 新增 5 个守门人目标
- [x] Makefile help 显示守门人章节
- [x] 所有脚本添加守门人标记
- [x] PR 模板强制烟测指标
- [x] .gitignore/.dockerignore 标记守门人

### 运行层面（需服务运行）

- [ ] `make preflight` 通过 DEV_MODE/外置卷/健康检查
- [ ] `make warmup` 在 2-5s 内完成
- [ ] `make smoke` 产出非零 recall@10 和 p95_ms
- [ ] `make grid-dev` 生成 reports/winners_dev.json
- [ ] `make full-validate` 端到端 < 30s

---

## 💡 7. 使用指南

### 日常开发流程

```bash
# 1. 改代码
vim services/fiqa_api/routes/search.py

# 2. 快速验证（一键）
make dev-restart && make warmup && make smoke

# 3. 查看日志（可选）
make dev-logs
```

### 提交 PR 前

```bash
# 运行完整验证
make full-validate

# 查看烟测结果（粘贴到 PR）
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rag-api sh -c '
  cd /app/.runs
  LATEST=$(ls -t | grep -v ".json" | head -1)
  cat $LATEST/metrics.json | python3 -m json.tool
'

# 查看胜者配置（粘贴到 PR）
cat reports/winners_dev.json | python3 -m json.tool
```

### 切换到生产模式

```bash
# 方法 1: 环境变量覆盖
FULL=1 bash scripts/smoke.sh

# 方法 2: 直接调用 API
curl -X POST http://localhost:8000/api/experiment/run \
  -H 'content-type: application/json' \
  -d '{
    "sample": 1000,
    "top_k": 50,
    "dataset_name": "fiqa_50k_v1",
    "qrels_name": "fiqa_qrels_50k_v1",
    "use_hybrid": true,
    "rerank": true,
    "fast_mode": false
  }'
```

---

## 🎯 8. 下一步建议

### 可选增强（未实现）

1. **Git Hooks**: 创建 `.githooks/pre-push` 本地校验烟测通过才允许推送
   ```bash
   # scripts/setup_hooks.sh
   ln -sf ../../scripts/prepush.sh .git/hooks/pre-push
   ```

2. **CI/CD 集成**: 在 GitHub Actions 中自动运行 `make smoke`
   ```yaml
   # .github/workflows/smoke-test.yml
   - name: Run smoke test
     run: make smoke
   ```

3. **Metrics Dashboard**: 可视化展示历史烟测指标趋势

4. **Auto-tuner 集成**: 自动调整开发阈值以平衡速度与质量

### 维护建议

- **定期审计**: 每周检查 reports/winners_dev.json 确保开发阈值仍然合理
- **文档更新**: 随着新功能添加，更新 QUICKSTART_DEV.md
- **指标监控**: 跟踪烟测 p95_ms 趋势，及时发现性能回退

---

## 📚 9. 相关文档

- [QUICKSTART_DEV.md](QUICKSTART_DEV.md) - 快速上手指南
- [docs/DEV_MODE_CONFIG.md](docs/DEV_MODE_CONFIG.md) - 开发模式配置详解
- [.github/pull_request_template.md](.github/pull_request_template.md) - PR 模板
- [Makefile](Makefile) - 完整命令列表（`make help`）

---

**维护者**: AI (Cursor)  
**审核者**: andy  
**版本**: v1.0 (2025-11-07)

