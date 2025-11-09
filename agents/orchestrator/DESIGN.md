# Orchestrator Design Log

## 本轮完成内容
- `agents/orchestrator/flow.py`：定义 `ExperimentPlan` / `ExperimentReport`，生成 `run_id`，写入事件日志与记忆索引；线程调度执行管线并扩展失败事件负载（`error.type/msg/hint/details`）、集成健康检测、超时与别名日志。
- `tools/run_eval.py`：实现 smoke/grid/ab 执行器，封装 FiQA runner 调度、白名单校验、限流、指数退避重试、总超时、主机别名映射与健康检查（`HEALTH_FAIL` / `RUNNER_TIMEOUT` 事件）。
- `tools/fetch_metrics.py`：读取 `.runs/<job>/metrics.json` 并输出 recall@10 / p95 / cost / count 汇总；辅助写入 `failTopN.csv`。
- `observe/logging.py`：JSONL 事件记录器扩展阶段事件 API，支持读取最近事件；`reports/events/<run_id>.jsonl` 记录全流程 RUN/SMOKE/GRID/AB 事件。
- `agents/orchestrator/memory.py`：记忆存储支持 `run_id.json` 元数据更新（阶段指标、状态、反思决策），便于回放。
- `services/fiqa_api/app_main.py`：提供 `/orchestrate/run`、`/orchestrate/status`、`/orchestrate/report` 接口（通过 `services/orchestrate_router.py` 挂载）；`/report` 返回所有产物相对路径。
- `Makefile`：新增 `orchestrate.diag`（健康检查 + 极小样本试跑 + `.runs` 快照），并使用主机别名默认指向 `http://127.0.0.1:8001` 的 orchestrator 服务。
- 数据产出：`reports/winners.final.json` 追加真实 run 记录，`reports/<run_id>/` 存储 Pareto / A/B 图与赢家摘要。
- 单测：新增 `tests/tools/test_run_eval.py`、`tests/tools/test_fetch_metrics.py`、`tests/observe/test_logging.py`、`tests/app/test_status.py`，强化 `tests/orchestrator/test_flow.py` 覆盖阶段封装与状态。

## Patterns Implemented
- Planning — `agents/orchestrator/planner.py` 从配置生成 smoke→grid→ab→select→publish 阶段，并依据样本量/并发约束拆分批次；逻辑确保同 seed 输出稳定组合，便于预算与复现。  
- Tools — `tools/run_eval.py`, `tools/fetch_metrics.py`, `tools/ab_test.py`, `tools/draw_pareto.py` 统一处理超时、指数退避重试、限流及域白名单，所有外部调用均经这些入口。  
- Reflection — `agents/orchestrator/reflection.py` 以失败率/方差阈值判断 keep/shrink/early_stop，并写入 `REFLECTION_DECISION` 事件用于后续决策与可见性。  
- Memory — `agents/orchestrator/memory.py` 使用 JSONL + per-run JSON 索引 run_id ←→ plan/阶段结果/元数据，实现回放与增量写入。  
- Observer — `observe/logging.py` 将阶段事件写入 `reports/events/<run_id>.jsonl`，同时提供读取最近事件 API 供 `/status` 和报告使用。  
- Guardian / MCP — 尚未启用；`tools/policy_apply.py` 保留策略守护挂载点，未来可在 MCP capability 暴露，当前轮仅记录计划。  

## Artifacts & Layout
- `reports/<run_id>/winners.json`：包含 `run_id`, `generated_at`, `dataset`, `winner{config_id,metrics,parameters}`, `ab{diff_table,baseline/challenger metrics}`, `grid_decision`。  
- `reports/<run_id>/winners.md`：Markdown 摘要，记录赢家配置、指标及参数清单。  
- `reports/<run_id>/pareto.png`：质量/延迟 Pareto 前沿散点图（候选配置标注）。  
- `reports/<run_id>/ab_diff.png`：Baseline 与候选的对比柱状图。  
- `reports/<run_id>/ab_diff.csv`：`metric,baseline,challenger,delta` 表格。  
- `reports/<run_id>/failTopN.csv`：常见失败原因 TopN（`reason,count`）。  
- `reports/events/<run_id>.jsonl`：阶段 & 事件流水（`run_id,event_type,payload,created_at`）。  
- `reports/winners.final.json`：全局赢家历史列表，每条含 `run_id`, `timestamp`, `winner`, `ab_diff`, `grid_decision`, `hash`。  
- `.runs/<job>/metrics.json`：每个阶段 runner 的原始指标；诊断命令会列出最近几条记录。

## Remaining / Future Work
- Guardian：`tools/policy_apply.py` 预留对接策略守护及 SLA 闸，目前仅记录挂载点，后续可读取 `SLA_POLICY.yaml` 提示风险并自动化回滚。
- MCP：所有 `tools/*` 均可作为未来 MCP 能力导出，当前版本尚未暴露（避免引入额外依赖）。

## cURL Quickstart

```bash
curl -s -X POST http://127.0.0.1:8001/orchestrate/run \
  -H 'content-type: application/json' \
  -d '{"collection":"fiqa_para_50k","mode":"full"}'

curl -s 'http://127.0.0.1:8001/orchestrate/status?run_id=<RUN_ID>'

curl -s 'http://127.0.0.1:8001/orchestrate/report?run_id=<RUN_ID>'
```

> Note：
> - `agents/orchestrator/config.yaml` 现默认 `mock_runner: false`，追加 `runner_cmd`、`runner_timeout_s`、`health_endpoints`、`host_aliases` 等配置。健康检查失败将写入 `HEALTH_FAIL` 事件并终止管线。
> - orchestration API 默认监听 `http://127.0.0.1:8001`，而真实检索后端通过 `base_url`/别名（例：`http://andy-wsl:8000` → `127.0.0.1:8000`）访问。
> - `make orchestrate.diag` 会执行健康检查 + 极小样本 runner + `.runs` 快照，建议在真实模式前先执行一次。

