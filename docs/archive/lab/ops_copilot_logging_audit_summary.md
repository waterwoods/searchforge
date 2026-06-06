# Ops Copilot 日志/安全日志盘点总结

## 1. 现有日志记录位置和字段

### 1.1 ops_runtime.py 中的日志

**日志位置：**
- `run_health_analyst_agent()` - 无显式日志（但调用的函数有日志）
- `run_remediation_planner_agent()` - 无显式日志
- `build_ops_action_plan()` - 有 `logger.warning()` 用于错误处理
- `validate_ops_action_plan()` - 有 `logger.info()` 记录验证结果
- `_generate_system_health_narrative()` - 有大量结构化日志记录 LLM 调用
- `apply_ops_output_guardrails()` - 无显式日志（但会调用 `log_security_event()`）

**记录的字段：**
- `event=ops_llm_explanation` - LLM 解释调用日志
  - `request_id`
  - `model`
  - `success`
  - `fallback_used`
  - `latency_ms`
  - `tokens`
  - `cost_usd_est`
  - `reason` (当失败时)

- `[ACTION_PLANNER_VALIDATION]` - 验证日志
  - `actions` (数量)
  - `blocked` (数量)
  - `require_human` (数量)
  - `is_high_risk`

- `[SAFETY_UPGRADE]`, `[STRATEGY_LAB]`, `[RAG]` - 各种警告日志（错误时）

### 1.2 system_health_graph.py 中的日志

**日志位置：**
- `_health_check_node()` - 节点完成/失败日志
- `_safety_upgrade_node()` - 节点完成/失败日志
- `_strategy_lab_node()` - 节点完成/失败日志
- `_action_planner_node()` - 节点完成/失败日志
- `_llm_explanation_node()` - 节点完成/失败日志

**记录的字段：**
- `event=ops_node_complete` / `event=ops_node_failed`
  - `node` (节点名：health_check, safety_upgrade, strategy_lab, action_planner, llm_explanation)
  - `request_id`
  - `latency_ms`
  - `band` (health band)
  - `score` (health score)
  - `risk_flags` (逗号分隔的列表)
  - `service_name`
  - `suggestions_count` (safety_upgrade 节点)
  - `scenarios_count` (strategy_lab 节点)
  - `strategy_improved` (strategy_lab 节点)
  - `actions_count` (action_planner 节点)
  - `hard_block` (action_planner 节点)
  - `num_actions_blocked` (action_planner 节点)
  - `num_actions_require_human` (action_planner 节点)
  - `llm_fallback_used` (llm_explanation 节点)
  - `model` (llm_explanation 节点)
  - `has_context` (llm_explanation 节点)
  - `log_error_count` (llm_explanation 节点)

- `event=ops_semantic_tools_complete`
  - `request_id`
  - `service_name`
  - `log_error_count`
  - `runbook_fetched`
  - `incident_count`
  - `rag_snippets_count`

## 2. security_events.log_security_event() 调用位置

### 2.1 调用位置

1. **ops_runtime.py - `guard_tool_call()` 函数（2处）**
   - 第 117 行：当工具处于 dry_run_only 模式时
   - 第 135 行：当工具在指定环境中不被允许时

2. **ops_runtime.py - `apply_ops_output_guardrails()` 函数（1处）**
   - 第 1949 行：当 narrative 或 recommended_actions 被调整时

### 2.2 event_type 类型

- `tool_call_blocked` - 工具调用被阻止
- `narrative_guardrail_adjusted` - LLM 生成的 narrative 被安全护栏调整

### 2.3 context 字段示例

**tool_call_blocked 的 context：**
```python
{
    "tool": "apply_config_change",
    "reason": "dry_run_only_mode" 或 "not_allowed_in_env_prod",
    "environment": "prod",
    "allowed_envs": ["staging"],  # 仅当 reason 为 not_allowed_in_env 时
    # ... 其他 context 字段
}
```

**narrative_guardrail_adjusted 的 context：**
```python
{
    "service_name": "ops_copilot",
    "reason": "hard_block_or_critical_without_urgency",
    "band": "critical",
    "hard_block": True,
    "narrative_adjusted": True,
    "actions_adjusted": True,
}
```

## 3. action_plan 产生位置

### 3.1 产生位置

**函数/节点：** `_action_planner_node()` 函数（在 `system_health_graph.py` 中）

**节点名：** `action_planner`

**写入 state 的字段名：** `action_plan`

### 3.2 产生流程

1. 调用 `build_ops_action_plan()` 函数（在 `ops_runtime.py` 中）
   - 输入：`service_name`, `health_result`, `safety_suggestions`, `strategy_lab`
   - 输出：`OpsActionPlan` 对象

2. 调用 `validate_ops_action_plan()` 函数（在 `ops_runtime.py` 中）
   - 输入：`action_plan`, `health_result`
   - 输出：验证后的 `OpsActionPlan` 对象（可能被修改）

3. 写入到 state：`state["action_plan"] = action_plan`

### 3.3 相关日志

在 `_action_planner_node()` 中有结构化日志：
```python
logger.info(
    f"event=ops_node_complete node=action_planner "
    f"request_id={request_id} "
    f"latency_ms={step_duration} "
    f"band={band} "
    f"score={score} "
    f"actions_count={actions_count} "
    f"hard_block={hard_block} "
    f"num_actions_blocked={num_actions_blocked} "
    f"num_actions_require_human={num_actions_require_human}"
)
```

## 4. 是否有专门记录 safety_suggestions / strategy_lab / action_plan 的结构化日志

### 4.1 当前状态

**没有专门的结构化日志记录这些对象的完整内容。**

### 4.2 现有记录方式

1. **safety_suggestions：**
   - 只记录数量：`suggestions_count={len(safety_suggestions)}`
   - 位置：`_safety_upgrade_node()` 中的 `event=ops_node_complete` 日志

2. **strategy_lab：**
   - 只记录数量：`scenarios_count={len(strategy_lab.scenarios)}`
   - 只记录改进数量：`strategy_improved={improved_count}`
   - 位置：`_strategy_lab_node()` 中的 `event=ops_node_complete` 日志

3. **action_plan：**
   - 记录统计信息：
     - `actions_count`
     - `hard_block`
     - `num_actions_blocked`
     - `num_actions_require_human`
   - 位置：`_action_planner_node()` 中的 `event=ops_node_complete` 日志
   - **没有记录每个 action 的详细信息**（如 action_type, severity, target_service, require_human_approval, estimated_delta 等）

### 4.3 缺失的内容

- **safety_suggestions：** 没有记录每个 suggestion 的 id, title, estimated_result 等
- **strategy_lab：** 没有记录每个 scenario 的 id, title, health_result 等
- **action_plan：** 没有记录每个 action 的完整信息（action_type, severity, target_service, require_human_approval, estimated_delta, reason 等）

## 5. 建议：为 OpsActionPlan 添加审计日志

### 5.1 日志函数位置建议

**建议位置：** `services/fiqa_api/ops_copilot/ops_runtime.py`

**建议函数名：** `log_ops_action_plan(plan: OpsActionPlan, health_result: SystemHealthCheckResult, request_id: Optional[str] = None)`

**调用位置：** 在 `system_health_graph.py` 的 `_action_planner_node()` 函数中，在 `validate_ops_action_plan()` 之后调用

**理由：**
- `ops_runtime.py` 是核心运行时逻辑文件，与 `build_ops_action_plan()` 和 `validate_ops_action_plan()` 在同一模块，便于维护
- 在 graph 节点中调用，确保每次 action_plan 生成后都会记录
- 可以复用现有的 logger 和日志格式

### 5.2 建议日志字段

**必需字段：**
- `event=ops_action_plan_audit` (事件类型标识)
- `request_id` (请求 ID，用于追踪)
- `service_name` (目标服务名)
- `band` (健康等级：healthy, warning, degraded, critical)
- `score` (健康分数)
- `hard_block` (是否硬阻断)
- `num_actions` (action 总数)
- `num_actions_blocked` (被阻止的 action 数量)
- `num_actions_require_human` (需要人工审批的 action 数量)
- `timestamp` (生成时间)

**每个 action 的字段（数组形式）：**
- `actions[]` - 数组，每个元素包含：
  - `action_id` (action 唯一 ID)
  - `action_type` (action 类型：reduce_qps, add_replica, adjust_timeout 等)
  - `severity` (严重程度：info, warning, critical)
  - `target_service` (目标服务)
  - `require_human_approval` (是否需要人工审批)
  - `estimated_before_score` (执行前预估分数)
  - `estimated_after_score` (执行后预估分数)
  - `estimated_delta` (预估分数变化)
  - `source` (来源：safety_suggestions 或 strategy_lab)
  - `summary` (简要描述)

**可选字段：**
- `risk_flags` (风险标志列表)
- `notes` (plan 的备注信息)

### 5.3 建议记录场景

**建议只记录以下场景：**
- `band in {"degraded", "critical"}` - 只记录降级和严重情况的 action plan
- 或者：`num_actions > 0` - 只要有 action 就记录（更全面）

**理由：**
- degraded/critical 场景是最需要审计的，因为可能涉及生产环境变更
- 如果记录所有场景，日志量会很大，但 healthy/warning 场景的 action plan 通常为空或很少，审计价值较低
- 建议先实现只记录 degraded/critical，后续可根据需求扩展

### 5.4 日志格式建议

**结构化日志格式（JSON-like）：**
```python
logger.info(
    f"event=ops_action_plan_audit "
    f"request_id={request_id} "
    f"service_name={plan.service_name} "
    f"band={plan.band} "
    f"score={health_result.score} "
    f"hard_block={plan.hard_block} "
    f"num_actions={len(plan.actions)} "
    f"num_actions_blocked={plan.num_actions_blocked} "
    f"num_actions_require_human={plan.num_actions_require_human} "
    f"actions={_format_actions_for_log(plan.actions)}"
)
```

**或者使用 JSON 格式（如果 logger 支持）：**
```python
log_data = {
    "event": "ops_action_plan_audit",
    "request_id": request_id,
    "service_name": plan.service_name,
    "band": plan.band,
    "score": health_result.score,
    "hard_block": plan.hard_block,
    "num_actions": len(plan.actions),
    "num_actions_blocked": plan.num_actions_blocked,
    "num_actions_require_human": plan.num_actions_require_human,
    "actions": [
        {
            "action_id": action.action_id,
            "action_type": action.action_type,
            "severity": action.severity,
            "target_service": action.target_service,
            "require_human_approval": action.require_human_approval,
            "estimated_delta": action.estimated_delta,
            "source": action.source,
            "summary": action.summary,
        }
        for action in plan.actions
    ],
    "timestamp": plan.generated_at.isoformat(),
}
logger.info(f"[OPS_ACTION_PLAN_AUDIT] {json.dumps(log_data)}")
```

### 5.5 实现建议

1. **在 `ops_runtime.py` 中添加函数：**
   ```python
   def log_ops_action_plan(
       plan: OpsActionPlan,
       health_result: SystemHealthCheckResult,
       request_id: Optional[str] = None,
   ) -> None:
       """Log OpsActionPlan for audit purposes."""
       # 只记录 degraded/critical 场景
       if plan.band not in ("degraded", "critical"):
           return
       
       # 构建日志数据并记录
       # ...
   ```

2. **在 `system_health_graph.py` 的 `_action_planner_node()` 中调用：**
   ```python
   # 在 validate_ops_action_plan() 之后
   from services.fiqa_api.ops_copilot.ops_runtime import log_ops_action_plan
   log_ops_action_plan(action_plan, health_result, request_id)
   ```

3. **考虑使用专门的 logger：**
   - 可以使用 `logging.getLogger("ops_copilot.audit")` 创建专门的审计 logger
   - 这样可以单独配置审计日志的输出和级别

