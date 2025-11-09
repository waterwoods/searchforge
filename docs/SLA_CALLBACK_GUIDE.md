# SLA 小样本回调 + 对齐前置闸使用指南

## 概述

本实现添加了以下功能：

1. **前置对齐检查**：`orchestrate.run` 在执行实验前自动运行 `orchestrate.policy.audit`
2. **小样本 smoke 测试**：使用 SAMPLE=30 快速验证
3. **SLA 自动回调**：基于真实结果自动更新 `configs/SLA_POLICY.yaml`
4. **一键快速测试**：`orchestrate.quick` 组合所有步骤
5. **每日健康检查**：`orchestrate.health-sweep` 一键完成完整流程

## 新增 Makefile 目标

### `orchestrate.preflight`
运行数据集对齐检查（前置闸）。

```bash
make orchestrate.policy.audit DATASET=fiqa_para_50k
```

### `orchestrate.run`
运行 orchestrator 实验（自动包含前置检查）。

```bash
make orchestrate.run DATASET=fiqa_para_50k SAMPLE=30 TOPK=10
```

**注意**：此目标会自动先运行 `orchestrate.preflight`，对齐检查失败会阻断实验。

### `orchestrate.quick`
一键快速 smoke 测试（SAMPLE=30, TOPK=10，默认值）。

```bash
make orchestrate.quick DATASET=fiqa_para_50k
```

### `orchestrate.update-sla`
基于最新实验结果更新 SLA_POLICY.yaml。

```bash
make orchestrate.update-sla
```

### `orchestrate.health-sweep` ⭐ **推荐**
每日健康检查：一键完成对齐检查 → smoke 测试 → 报告拉取 → SLA 更新 → 验收总结。

```bash
make orchestrate.health-sweep DATASET=fiqa_para_50k SAMPLE=30 TOPK=10
```

## 完整工作流程

### 方式一：一键健康检查（推荐）

```bash
make orchestrate.health-sweep DATASET=fiqa_para_50k SAMPLE=30 TOPK=10
```

这会自动执行：
1. ✅ 预检对齐（如果失败会立即停止）
2. ✅ 运行小样本 smoke 测试
3. ✅ 等待实验完成（最多 30 分钟）
4. ✅ 拉取报告并更新 SLA
5. ✅ 验证所有 artifacts
6. ✅ 输出验收总结（PASS/FAIL）

**验收标准**：
- `status == "completed"`
- `artifacts_ok == true`
- `winners.json` 包含 `dataset/queries_path/qrels_path/id_normalization`
- `sla_verdict == "pass"`（如果失败会输出诊断线索）

### 方式二：手动分步执行

#### 1. 运行对齐检查

```bash
make orchestrate.policy.audit DATASET=fiqa_para_50k
```

预期输出：
```
✅ Dataset alignment passed for 'fiqa_para_50k' (mismatch_rate=0.0)
```

#### 2. 运行小样本 smoke 测试

```bash
make orchestrate.run DATASET=fiqa_para_50k SAMPLE=30 TOPK=10
```

这会：
- 自动运行前置对齐检查
- 启动 orchestrator 实验
- 将 run_id 保存到 `.last_run`

#### 3. 等待实验完成并获取报告

```bash
# 检查状态
make orchestrate.status

# 获取报告
make orchestrate.report | tee /tmp/_report.json
```

#### 4. 基于结果更新 SLA

```bash
make orchestrate.update-sla
```

这会：
- 从 `reports/{run_id}/winners.json` 提取指标
- 计算安全阈值：
  - `recall_at_10_min = max(0.3, min(0.99, 0.9 * actual_recall))`
  - `p95_ms_max = max(50.0, 1.1 * actual_p95)`
- 更新 `configs/SLA_POLICY.yaml`（保留 `cost_max`）

#### 5. 验证更新后的 SLA

再次运行 smoke 测试，应该通过 SLA 检查：

```bash
make orchestrate.run DATASET=fiqa_para_50k SAMPLE=30 TOPK=10
make orchestrate.report | jq '{run_id, artifacts, sla_verdict}'
```

预期输出应显示 `sla_verdict: "pass"`。

## 一键快速测试

使用 `orchestrate.quick` 可以一次性完成前置检查 + smoke 测试：

```bash
make orchestrate.quick DATASET=fiqa_para_50k SAMPLE=30 TOPK=10
```

## 脚本说明

### `scripts/update_sla_from_results.py`

用于从实验结果更新 SLA 策略的 Python 脚本。

**用法**：
```bash
# 从 .last_run 读取 run_id
python3 scripts/update_sla_from_results.py

# 指定 run_id
python3 scripts/update_sla_from_results.py --run-id orch-20240101120000-abc123

# 指定 winners.json 路径
python3 scripts/update_sla_from_results.py --winners-json reports/orch-xxx/winners.json

# 指定 SLA 文件路径
python3 scripts/update_sla_from_results.py --sla-path configs/SLA_POLICY.yaml
```

**依赖**：
- `ruamel.yaml`（用于保留 YAML 注释和格式）
- 如果未安装，脚本会提示安装

### `scripts/daily_health_sweep.sh`

每日健康检查脚本，执行完整的工作流程。

**功能**：
1. 预检对齐（失败会立即停止）
2. 运行 smoke 测试并等待完成
3. 拉取报告并更新 SLA
4. 验证所有 artifacts
5. 输出验收总结（JSON 格式）

**验收总结格式**：
```json
{
  "run_id": "orch-20240101120000-abc123",
  "status": "completed",
  "sla_verdict": "pass",
  "metrics": {
    "recall_at_10": 0.7234,
    "p95_ms": 456.78
  },
  "dataset": "fiqa_para_50k",
  "queries_path": "experiments/data/fiqa/fiqa_hard_50k.jsonl",
  "qrels_path": "experiments/data/fiqa/fiqa_qrels_hard_50k_v1.tsv",
  "id_normalization": "digits-only/no-leading-zero",
  "artifacts_ok": true
}
```

**失败时的诊断线索**：
如果 `sla_verdict == "fail"`，脚本会输出：
1. 最近一次对齐检查的 `mismatch_rate`
2. `events.jsonl` 中的阻塞事件（ALIGNMENT_BLOCK/BUDGET_BLOCK/RUNNER_TIMEOUT）
3. `failTopN.csv` 和 `ab_diff.csv` 的前 5 行

## 安全机制

1. **对齐检查失败阻断**：如果 `mismatch_rate > 0`，`orchestrate.policy.audit` 会失败并退出
2. **SLA 阈值边界**：
   - `recall_at_10_min` 限制在 [0.3, 0.99]
   - `p95_ms_max` 最小值为 50ms
3. **成本上限保留**：更新 SLA 时自动保留 `cost_max` 原值

## 示例输出

### 对齐检查通过
```
Checking alignment: collection=fiqa_para_50k, qrels=experiments/data/fiqa/fiqa_qrels_hard_50k_v1.tsv
✅ Dataset alignment passed for 'fiqa_para_50k' (mismatch_rate=0.0)
```

### SLA 更新
```
📊 Loading metrics from reports/orch-20240101120000-abc123/winners.json
   recall_at_10: 0.7234
   p95_ms: 456.78
✅ Updated configs/SLA_POLICY.yaml
   recall_at_10_min: 0.651
   p95_ms_max: 502.46
   cost_max: 5.0 (preserved)
```

### 健康检查通过
```
==========================================
Step 5/5: Acceptance Summary
==========================================
{
  "run_id": "orch-20240101120000-abc123",
  "status": "completed",
  "sla_verdict": "pass",
  "metrics": {
    "recall_at_10": 0.7234,
    "p95_ms": 456.78
  },
  "dataset": "fiqa_para_50k",
  "queries_path": "experiments/data/fiqa/fiqa_hard_50k.jsonl",
  "qrels_path": "experiments/data/fiqa/fiqa_qrels_hard_50k_v1.tsv",
  "id_normalization": "digits-only/no-leading-zero",
  "artifacts_ok": true
}

==========================================
✅ ACCEPTANCE: PASS

All checks passed:
  - Status: completed
  - SLA Verdict: pass
  - Artifacts: OK
  - Winners.json structure: OK
==========================================

🎉 Daily Health Sweep completed successfully!
```

## 故障排查

### 对齐检查失败
- 检查 Qdrant 集合是否存在
- 验证 qrels 文件路径是否正确
- 确认集合中的文档 ID 格式与 qrels 匹配

### SLA 更新失败
- 确认 `.last_run` 文件存在
- 检查 `reports/{run_id}/winners.json` 是否存在
- 验证 winners.json 中包含 `winner.metrics` 字段

### 实验未通过 SLA
- 检查 `configs/SLA_POLICY.yaml` 中的阈值是否合理
- 考虑重新运行 `orchestrate.update-sla` 调整阈值
- 查看诊断线索（对齐率、阻塞事件、失败样本）

### 健康检查失败
运行 `make orchestrate.health-sweep` 时如果失败，会输出详细的诊断信息：
- 对齐检查的 `mismatch_rate`
- `events.jsonl` 中的阻塞事件
- `failTopN.csv` 的前 5 行

## 回滚机制

如果策略或门控导致连续失败，可以回滚配置：

```bash
git checkout -- configs/SLA_POLICY.yaml configs/policies.json
```

然后重新运行健康检查。

## 新增 Makefile 目标

### `orchestrate.preflight`
运行数据集对齐检查（前置闸）。

```bash
make orchestrate.policy.audit DATASET=fiqa_para_50k
```

### `orchestrate.run`
运行 orchestrator 实验（自动包含前置检查）。

```bash
make orchestrate.run DATASET=fiqa_para_50k SAMPLE=30 TOPK=10
```

**注意**：此目标会自动先运行 `orchestrate.preflight`，对齐检查失败会阻断实验。

### `orchestrate.quick`
一键快速 smoke 测试（SAMPLE=30, TOPK=10，默认值）。

```bash
make orchestrate.quick DATASET=fiqa_para_50k
```

### `orchestrate.update-sla`
基于最新实验结果更新 SLA_POLICY.yaml。

```bash
make orchestrate.update-sla
```

## 完整工作流程

### 1. 运行对齐检查

```bash
make orchestrate.policy.audit DATASET=fiqa_para_50k
```

预期输出：
```
✅ Dataset alignment passed for 'fiqa_para_50k' (mismatch_rate=0.0)
```

### 2. 运行小样本 smoke 测试

```bash
make orchestrate.run DATASET=fiqa_para_50k SAMPLE=30 TOPK=10
```

这会：
- 自动运行前置对齐检查
- 启动 orchestrator 实验
- 将 run_id 保存到 `.last_run`

### 3. 等待实验完成并获取报告

```bash
# 检查状态
make orchestrate.status

# 获取报告
make orchestrate.report | tee /tmp/_report.json
```

### 4. 基于结果更新 SLA

```bash
make orchestrate.update-sla
```

这会：
- 从 `reports/{run_id}/winners.json` 提取指标
- 计算安全阈值：
  - `recall_at_10_min = max(0.3, min(0.99, 0.9 * actual_recall))`
  - `p95_ms_max = max(50.0, 1.1 * actual_p95)`
- 更新 `configs/SLA_POLICY.yaml`（保留 `cost_max`）

### 5. 验证更新后的 SLA

再次运行 smoke 测试，应该通过 SLA 检查：

```bash
make orchestrate.run DATASET=fiqa_para_50k SAMPLE=30 TOPK=10
make orchestrate.report | jq '{run_id, artifacts, sla_verdict}'
```

预期输出应显示 `sla_verdict: "pass"`。

## 一键快速测试

使用 `orchestrate.quick` 可以一次性完成前置检查 + smoke 测试：

```bash
make orchestrate.quick DATASET=fiqa_para_50k SAMPLE=30 TOPK=10
```

## 脚本说明

### `scripts/update_sla_from_results.py`

用于从实验结果更新 SLA 策略的 Python 脚本。

**用法**：
```bash
# 从 .last_run 读取 run_id
python3 scripts/update_sla_from_results.py

# 指定 run_id
python3 scripts/update_sla_from_results.py --run-id orch-20240101120000-abc123

# 指定 winners.json 路径
python3 scripts/update_sla_from_results.py --winners-json reports/orch-xxx/winners.json

# 指定 SLA 文件路径
python3 scripts/update_sla_from_results.py --sla-path configs/SLA_POLICY.yaml
```

**依赖**：
- `ruamel.yaml`（用于保留 YAML 注释和格式）
- 如果未安装，脚本会提示安装

## 安全机制

1. **对齐检查失败阻断**：如果 `mismatch_rate > 0`，`orchestrate.policy.audit` 会失败并退出
2. **SLA 阈值边界**：
   - `recall_at_10_min` 限制在 [0.3, 0.99]
   - `p95_ms_max` 最小值为 50ms
3. **成本上限保留**：更新 SLA 时自动保留 `cost_max` 原值

## 示例输出

### 对齐检查通过
```
Checking alignment: collection=fiqa_para_50k, qrels=experiments/data/fiqa/fiqa_qrels_hard_50k_v1.tsv
✅ Dataset alignment passed for 'fiqa_para_50k' (mismatch_rate=0.0)
```

### SLA 更新
```
📊 Loading metrics from reports/orch-20240101120000-abc123/winners.json
   recall_at_10: 0.7234
   p95_ms: 456.78
✅ Updated configs/SLA_POLICY.yaml
   recall_at_10_min: 0.651
   p95_ms_max: 502.46
   cost_max: 5.0 (preserved)
```

## 故障排查

### 对齐检查失败
- 检查 Qdrant 集合是否存在
- 验证 qrels 文件路径是否正确
- 确认集合中的文档 ID 格式与 qrels 匹配

### SLA 更新失败
- 确认 `.last_run` 文件存在
- 检查 `reports/{run_id}/winners.json` 是否存在
- 验证 winners.json 中包含 `winner.metrics` 字段

### 实验未通过 SLA
- 检查 `configs/SLA_POLICY.yaml` 中的阈值是否合理
- 考虑重新运行 `orchestrate.update-sla` 调整阈值

