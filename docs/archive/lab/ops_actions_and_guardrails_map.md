# Ops Copilot – Actions & Guardrails Map

本文档梳理了项目中现有的"行动建议/plan"输出、Guardrails/安全逻辑，以及适合挂接 OpsAction 和更强 Guardrail 的位置。

---

## 1. 现有 "action / plan / 建议" 输出梳理

### 1.1 搜索关键词结果

在整个仓库中搜索了以下关键词附近的逻辑：
- `safety_suggestions`
- `strategy_lab` / `StrategyLabResult`
- `recommended_actions`
- `plan` / `scenario` / `suggestion`

### 1.2 Ops / Mortgage 相关的行动/策略输出

| 文件路径 | 函数名 | 输出结构类型 | 性质（plan vs 执行） | 与健康状态/risk的关系 |
|---------|--------|-------------|---------------------|---------------------|
| `services/fiqa_api/ops_copilot/ops_runtime.py` | `run_safety_upgrade_for_system()` | `List[SaferConfigSuggestion]` | **纯建议（plan-only）** | 仅在 `band in ("degraded", "critical")` 时生成 |
| `services/fiqa_api/ops_copilot/ops_runtime.py` | `run_system_strategy_lab()` | `SystemStrategyLabResult` | **纯建议（plan-only）** | 总是运行，包含 baseline + scenarios |
| `services/fiqa_api/ops_copilot/ops_runtime.py` | `run_remediation_planner_agent()` | `RemediationPlannerOutput` | **纯建议（plan-only）** | 包含 `safety_suggestions` + `strategy_lab` + `plan_notes` |
| `services/fiqa_api/ops_copilot/ops_runtime.py` | `_generate_system_health_narrative()` | `Tuple[str, List[str], Dict]` | **纯建议（plan-only）** | 输出 `recommended_actions: List[str]` |
| `services/fiqa_api/mortgage/mortgage_agent_runtime.py` | `run_safety_upgrade_flow()` | `SafetyUpgradeResult` | **纯建议（plan-only）** | 仅在 `stress_band in ("tight", "high_risk")` 时生成 |
| `services/fiqa_api/mortgage/mortgage_agent_runtime.py` | `run_strategy_lab()` | `StrategyLabResult` | **纯建议（plan-only）** | 总是运行，包含 baseline + scenarios |
| `services/fiqa_api/mortgage/mortgage_agent_runtime.py` | `_generate_single_home_narrative()` | `Tuple[str, List[str], Dict]` | **纯建议（plan-only）** | 输出 `recommended_actions: List[str]` |

### 1.3 重点文件详细说明

#### `services/fiqa_api/ops_copilot/ops_runtime.py`

**关键函数：**
- `run_safety_upgrade_for_system()` (line 415-568): 生成 2-3 个 `SaferConfigSuggestion`，每个包含 `config_changes` dict 和 `estimated_result`
- `run_system_strategy_lab()` (line 575-699): 生成 `SystemStrategyLabResult`，包含 baseline + 最多 3 个 `SystemStrategyScenario`
- `run_remediation_planner_agent()` (line 900-979): 组合 safety_suggestions + strategy_lab + plan_notes
- `_generate_system_health_narrative()` (line 1047-1451): LLM 生成 narrative + recommended_actions

**输出结构：**
- `SaferConfigSuggestion`: `id`, `title`, `description`, `config_changes` (dict), `estimated_result` (SystemHealthCheckResult)
- `SystemStrategyLabResult`: `baseline_snapshot`, `baseline_health`, `scenarios` (List[SystemStrategyScenario])
- `recommended_actions`: `List[str]` (1-3 条)

**执行状态：** 所有输出都是 plan-only，没有真实 API 调用。

#### `services/fiqa_api/ops_copilot/graphs/system_health_graph.py`

**关键节点：**
- `_safety_upgrade_node()` (line 236-311): 调用 `run_safety_upgrade_for_system()`，输出 `safety_suggestions`
- `_strategy_lab_node()` (line 314-398): 调用 `run_system_strategy_lab()`，输出 `strategy_lab`
- `_llm_explanation_node()` (line 401-519): 调用 `_generate_system_health_narrative()`，输出 `narrative` + `recommended_actions`

**执行状态：** 所有节点都是 plan-only，没有真实执行。

#### `services/fiqa_api/mortgage/mortgage_agent_runtime.py`

**关键函数：**
- `run_safety_upgrade_flow()` (line ~1900+): 生成 `SafetyUpgradeResult`，包含 `safer_homes` 列表和 `primary_suggestion`
- `run_strategy_lab()` (line 2087-2270): 生成 `StrategyLabResult`，包含 baseline + scenarios
- `_generate_single_home_narrative()` (line ~2400+): LLM 生成 narrative + recommended_actions

**执行状态：** 所有输出都是 plan-only，没有真实 API 调用。

#### `services/fiqa_api/mortgage/graphs/single_home_graph.py`

**关键节点：**
- `_safety_upgrade_node()` (line 135-141): 调用 `run_safety_upgrade_flow()`，输出 `safety_upgrade`
- `_strategy_lab_node()` (line 333-357): 调用 `run_strategy_lab()`，输出 `strategy_lab`
- `_llm_explanation_node()` (line 360-385): 调用 `_generate_single_home_narrative()`，输出 `borrower_narrative` + `recommended_actions`

**执行状态：** 所有节点都是 plan-only，没有真实执行。

### 1.4 总结

**目前所有动作都是 plan-only，没有真实 API 调用。**

- Ops Copilot: `safety_suggestions` 和 `strategy_lab` 都是"建议配置变更"，没有实际修改系统配置
- Mortgage Agent: `safety_upgrade` 和 `strategy_lab` 都是"建议更安全的方案"，没有实际执行
- `recommended_actions` 都是文本建议，没有结构化执行逻辑
- 所有输出都通过 `apply_*_output_guardrails()` 进行后处理，但只是调整文本，不执行动作

**未来风险点：** 如果未来添加真实执行工具（如 `apply_config_change`），需要在 `guard_tool_call()` 中加强校验。

---

## 2. 现有 Guardrails / 安全逻辑梳理（按层）

### 2.1 输入级 Guardrails (Input-level)

| 文件路径 | 函数名 | 作用 | 验证失败处理 |
|---------|--------|------|-------------|
| `services/fiqa_api/ops_copilot/input_validation.py` | `validate_system_snapshot()` | CPU/Mem/Disk: 0-100%, Latency ≥0, Error rate: 0-1, QPS ≥0, Service name 非空, Environment ∈ {prod, staging, dev} | 返回 `List[str]` 错误消息，应由调用方返回 400 Bad Request |
| `services/fiqa_api/mortgage/input_validation.py` | `validate_stress_request_inputs()` | Monthly income >0, List price >0, Down payment: 0-1, Other debts ≥0, HOA ≥0, Tax rate ≥0, Insurance ratio ≥0, Risk preference ∈ {conservative, neutral, aggressive} | 返回 `List[str]` 错误消息，应由调用方返回 400 Bad Request |

**安全日志：** 输入验证失败时，应由调用方记录 `input_validation_failed` 事件（通过 `log_security_event()`）。

### 2.2 规则 / 风险评估级 (Rule / Risk-level)

#### Ops Copilot - `SystemHealthCheckResult`

**字段：**
- `hard_block: bool`
- `soft_warning: bool`
- `risk_flags: List[str]`

**判断条件（`ops_runtime.py` line 387-396）：**
- `hard_block = True` 当：
  - `band == "critical"` 或
  - `"high_error_rate" in risk_flags` 或
  - `"disk_near_full" in risk_flags`
- `soft_warning = True` 当：
  - `band == "degraded"` 或
  - `(band == "warning" and len(risk_flags) > 0)`

**Critical/hard_block 时的保守逻辑：**
- 在 `apply_ops_output_guardrails()` 中强制添加紧急语言
- 在 `guard_tool_call()` 中，所有敏感工具默认 `dry_run_only=True`

#### Mortgage Agent - `RiskAssessment`

**字段：**
- `hard_block: bool`
- `soft_warning: bool`
- `risk_flags: List[str]`

**判断条件（`risk_assessment.py`）：**
- `hard_block = True` 当：
  - `payment_above_safe_range > 20%` 或
  - `dti_ratio > 0.80` (80%)
- `soft_warning = True` 当：
  - `payment_above_safe_range` 在 10-20% 或
  - `dti_ratio` 在 tight 范围

**High_risk/hard_block 时的保守逻辑：**
- 在 `apply_mortgage_output_guardrails()` 中强制添加警告语言
- 在 LLM prompt 中明确要求使用 `risk_assessment` 结构指导输出

### 2.3 输出级 Guardrails (Output-level)

| 文件路径 | 函数名 | 输入/输出类型 | 修改逻辑 | 触发条件 |
|---------|--------|-------------|---------|---------|
| `services/fiqa_api/ops_copilot/ops_runtime.py` | `apply_ops_output_guardrails()` | 输入: `SystemHealthCheckResult`, `narrative: str`, `recommended_actions: List[str]`<br>输出: `Tuple[str, List[str]]` | 1. Critical/hard_block: 检查 narrative 是否包含紧急关键词，如缺失则前置 "⚠️ **CRITICAL**: "<br>2. Critical/hard_block: 检查 actions 是否包含应急关键词，如缺失则前置 "立即降低流量或增加副本数量，触发应急runbook"<br>3. Degraded: 如 narrative 缺少优先级语言，则追加提示<br>4. 确保 narrative 和 actions 非空 | `hard_block=True` 或 `band == "critical"` |
| `services/fiqa_api/mortgage/mortgage_agent_runtime.py` | `apply_mortgage_output_guardrails()` | 输入: `StressCheckResponse`, `narrative: str`, `recommended_actions: List[str]`<br>输出: `Tuple[str, List[str]]` | 1. Hard_block: 检查 narrative 是否包含警告关键词，如缺失则追加 "⚠️ **重要提示**: 基于当前的计算结果，这个房贷方案风险较高..."<br>2. Hard_block: 检查 actions 是否包含安全关键词，如缺失则前置 "考虑降低房价或提高首付比例，或咨询专业贷款顾问获取建议"<br>3. Soft_warning: 如 narrative 缺少谨慎语言，则追加提示<br>4. 确保 narrative 和 actions 非空 | `hard_block=True` 或 `stress_band == "high_risk"` |

**安全日志：** 所有 narrative/actions 调整都会记录 `narrative_guardrail_adjusted` 事件（line 1582-1593 in ops_runtime.py, line 2827-2839 in mortgage_agent_runtime.py）。

### 2.4 安全日志 / 审计级 (Logging / Audit-level)

**文件：** `services/fiqa_api/observability/security_events.py`

**函数：** `log_security_event(event_type, request_id, context)`

**Event types：**
- `input_validation_failed`: 输入验证失败
- `hard_blocked_request`: 请求被 hard_block（目前未直接记录，但可通过 health_result/risk_assessment 推断）
- `tool_call_blocked`: 敏感工具调用被阻止（`guard_tool_call()` 中记录）
- `narrative_guardrail_adjusted`: LLM narrative 被 guardrail 调整

**记录字段：**
- `event_type`: 事件类型
- `timestamp`: UTC 时间戳
- `request_id`: 请求 ID（可选）
- `context`: 上下文字典，包含：
  - `service_name`: 服务名（mortgage_agent / ops_copilot）
  - `band` / `stress_band`: 健康/压力等级
  - `hard_block`: hard_block 状态
  - `reason`: 原因（如 "hard_block_or_critical_without_urgency"）
  - `tool`: 工具名（tool_call_blocked 时）
  - `field`: 字段名（input_validation_failed 时）

**日志级别：** INFO（security logger）

### 2.5 总结

**现在 Guardrails 涵盖了输入验证 → 风险评估 → 输出兜底 → 安全日志四层。**

**最强的防御点：**
- 输出级 Guardrails：即使 LLM 生成过于乐观/平静的文本，也会被强制调整
- 风险评估级：hard_block/soft_warning 有明确的规则判断

**明显还缺的点：**
- **还没有结构化 OpsAction 的校验**：目前 `recommended_actions` 是自由文本，无法验证其安全性
- **Tool-level guardrails 目前是 dry-run only**：`SENSITIVE_TOOLS` 中所有工具都标记为 `dry_run_only=True`，未来需要加强
- **没有对 strategy_lab scenarios 的校验**：scenarios 可能包含危险的配置变更建议，目前没有校验

---

## 3. LangGraph 中适合作为未来 OpsAction / safe_apply 挂钩的节点

**说明：** 项目中与"行动建议/plan"相关的 LangGraph workflow 有两个：
1. System Health Graph - Ops Copilot 的工作流
2. Single Home Graph - Mortgage Agent 的工作流

（注：还有一个 `nl_entry_graph.py`，但它是 NLU-only 的入口图，只做自然语言到结构化字段的转换，不生成行动建议，因此不在本文档讨论范围内。）

### 3.1 System Health Graph (`system_health_graph.py`)

**流程：**
```
entry → health_check → router →
    ├─ need_upgrade → safety_upgrade → strategy_lab → llm_explanation → END
    └─ skip_upgrade → strategy_lab → llm_explanation → END
```

**节点角色分析：**
- **分析角色（HealthAnalyst）**: `health_check` 节点（`_health_check_node()`）
  - 运行 `run_system_health_check()`，输出 `SystemHealthCheckResult`
  - 收集语义上下文（logs, runbooks, incidents）
  - 不生成行动建议

- **行动规划角色（RemediationPlanner）**: `safety_upgrade` + `strategy_lab` 节点
  - `safety_upgrade` (`_safety_upgrade_node()`): 生成 `List[SaferConfigSuggestion]`
  - `strategy_lab` (`_strategy_lab_node()`): 生成 `SystemStrategyLabResult`（包含 scenarios）
  - **这两个节点已经在生成结构化的场景/建议，只差把它们变成 OpsAction schema**

- **解释角色（Explainer）**: `llm_explanation` 节点（`_llm_explanation_node()`）
  - 生成 narrative + recommended_actions（文本）
  - 不生成结构化行动

**最适合作为 OpsAction 产生地：**
1. **`strategy_lab` 节点**（优先级最高）
   - 理由：`SystemStrategyLabResult.scenarios` 已经包含 `snapshot_after_change` 和 `health_result`，可以直接转换为 `OpsAction` schema
   - 每个 scenario 可以映射为一个 `OpsAction`，包含 `action_type`, `config_changes`, `estimated_impact`

2. **`safety_upgrade` 节点**（优先级次之）
   - 理由：`SaferConfigSuggestion` 已经包含 `config_changes` dict 和 `estimated_result`，可以转换为 `OpsAction`
   - 但建议数量较少（最多 3 个），不如 strategy_lab 丰富

### 3.2 Single Home Graph (`single_home_graph.py`)

**流程：**
```
entry → stress_check → router →
    ├─ need_upgrade → safety_upgrade → mortgage_programs → strategy_lab → llm_explanation → END
    └─ skip_upgrade → strategy_lab → llm_explanation → END
```

**节点角色分析：**
- **分析角色**: `stress_check` 节点（`_stress_check_node()`）
  - 运行 `run_stress_check()`，输出 `StressCheckResponse` + `RiskAssessment`
  - 不生成行动建议

- **行动规划角色**: `safety_upgrade` + `strategy_lab` 节点
  - `safety_upgrade` (`_safety_upgrade_node()`): 生成 `SafetyUpgradeResult`（包含 `safer_homes`）
  - `strategy_lab` (`_strategy_lab_node()`): 生成 `StrategyLabResult`（包含 scenarios）
  - **这两个节点已经在生成结构化的场景/建议，只差把它们变成 OpsAction schema**

- **解释角色**: `llm_explanation` 节点（`_llm_explanation_node()`）
  - 生成 borrower_narrative + recommended_actions（文本）
  - 不生成结构化行动

**最适合作为 OpsAction 产生地：**
1. **`strategy_lab` 节点**（优先级最高）
   - 理由：`StrategyLabResult.scenarios` 已经包含 `snapshot_after_change` 和 `stress_result`，可以直接转换为 `OpsAction` schema
   - 每个 scenario 可以映射为一个 `OpsAction`，包含 `action_type`, `parameter_changes`, `estimated_impact`

2. **`safety_upgrade` 节点**（优先级次之）
   - 理由：`SafetyUpgradeResult.safer_homes` 已经包含更安全的配置建议，可以转换为 `OpsAction`
   - 但主要针对 mortgage 场景，不如 strategy_lab 通用

### 3.3 建议

**未来 OpsAction schema 设计建议：**
- 从 `SystemStrategyScenario` / `StrategyScenario` 提取：
  - `action_type`: "reduce_qps", "add_replica", "reduce_error_rate" 等
  - `config_changes`: 从 `snapshot_after_change` 提取变更
  - `estimated_impact`: 从 `health_result` / `stress_result` 提取预期改善
  - `risk_level`: 基于 `estimated_result.band` / `estimated_result.stress_band` 计算

**未来 safe_apply 挂钩位置：**
- 在 `strategy_lab` 节点之后、`llm_explanation` 节点之前，添加一个 `validate_ops_actions` 节点
- 该节点校验所有生成的 `OpsAction`，确保：
  - 没有危险的配置变更（如删除所有副本）
  - estimated_impact 合理（不会导致更差的健康状态）
  - 符合环境限制（如 prod 环境不允许某些操作）

---

## 4. 现有测试里，哪里已经在 implicitly 测行动 & Guardrails？

### 4.1 测试脚本梳理

| 脚本名 | 目前断言了哪些"安全/行动相关"的东西 |
|--------|--------------------------------|
| `experiments/guardrails_test.py` | 1. 输入验证：negative values, out-of-range percentages<br>2. 输出 guardrails：high_risk 时 narrative 包含警告语言，critical 时 narrative 包含紧急语言<br>3. 输出 guardrails：hard_block 时 actions 包含安全建议 |
| `experiments/system_health_agent_smoke.py` | 1. Healthy case: `band="healthy"`, `hard_block=False`<br>2. Degraded case: `band in ("degraded", "warning")`, 至少一个 strategy scenario 改善<br>3. Critical case: `band="critical"`, `hard_block=True`, 至少一个 strategy scenario 改善 |
| `experiments/ops_copilot_demo.py` | 1. 展示 healthy/degraded/critical 三种场景的输出<br>2. 检查 safety_suggestions 和 strategy_lab 是否存在<br>3. 检查 narrative 和 recommended_actions 是否合理 |
| `experiments/ops_copilot_llm_eval.py` | 1. 检查 narrative 是否包含 service_name, health_band<br>2. 检查 recommended_actions 是否非空且合理<br>3. 检查 LLM 输出质量（但不直接测试 guardrails） |

### 4.2 总结

**现在测试主要覆盖了：**
- 输入验证：negative values, out-of-range percentages
- 风险评估：hard_block/soft_warning 的判断逻辑
- 输出 guardrails：critical/hard_block 时 narrative 和 actions 的调整
- Strategy lab：至少一个 scenario 改善的断言

**还没覆盖的典型风险行为（以后可以加到 `offline_ops_guardrail_eval.py`）：**
- **OpsAction 安全性校验**：如果未来有 OpsAction schema，需要测试：
  - 危险的配置变更（如删除所有副本、设置 QPS=0）是否被拒绝
  - estimated_impact 是否合理（不会导致更差的健康状态）
  - 环境限制（如 prod 环境不允许某些操作）是否生效
- **Tool-level guardrails**：测试 `guard_tool_call()` 是否正确阻止敏感工具调用
- **Strategy lab scenarios 安全性**：测试 scenarios 中的配置变更是否安全（不会导致系统崩溃）
- **输出 guardrails 边界情况**：测试 LLM 生成完全空白的 narrative/actions 时的处理
- **安全日志完整性**：测试所有 guardrail 调整是否都记录了安全事件

---

## 5. 输出要求

本文档控制在 2-3 页 A4 的量级，以表格 + 小段总结为主，方便快速扫一遍。所有引用都是现有代码里的结构名/函数名/字段名，没有发明新概念。

