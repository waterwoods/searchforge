# Canary Deployment System

配置版本化 + 金丝雀发布 + 一键回滚系统，让任意一套检索参数可以安全上线、10% 灰度验证、SLO 失败自动回滚。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Config        │    │   Canary        │    │   SLO           │
│   Manager       │    │   Executor      │    │   Monitor       │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • 版本化配置     │    │ • 90/10流量切分  │    │ • SLO监控       │
│ • last_good指针  │    │ • 指标收集       │    │ • 自动回滚       │
│ • active指针     │    │ • 实时监控       │    │ • 违规检测       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Audit         │
                    │   Logger        │
                    ├─────────────────┤
                    │ • 操作审计       │
                    │ • 事件追踪       │
                    │ • 日志导出       │
                    └─────────────────┘
```

## 核心功能

### 1. 配置版本化管理
- **配置预设**: `configs/presets/*.yaml` 存储版本化配置
- **参数快照**: 记录 `latency_guard`/`recall_bias` 与派生参数
- **状态指针**: 维护 `last_good` 和 `active` 配置指针

### 2. 金丝雀执行器
- **流量切分**: 90% 流量到 `last_good`，10% 流量到 `candidate`
- **指标收集**: 每5秒桶收集 p95_ms、recall@10、response_count、slo_violations
- **实时监控**: 连续监控性能指标和SLO合规性

### 3. SLO监控与自动回滚
- **SLO规则**: p95 ≤ 1200ms && recall@10 ≥ 0.30
- **自动回滚**: 连续2个桶不达标自动回滚到 `last_good`
- **审计日志**: 所有操作记录到 `reports/canary/audit.log`

## 使用方法

### 命令行工具

```bash
# 列出可用配置预设
python scripts/canary_cli.py list

# 查看当前状态
python scripts/canary_cli.py status

# 启动金丝雀部署
python scripts/canary_cli.py start candidate_high_recall

# 停止并推广候选配置
python scripts/canary_cli.py stop --promote

# 停止并回滚
python scripts/canary_cli.py stop --rollback

# 查看指标
python scripts/canary_cli.py metrics --config candidate_high_recall

# 导出结果
python scripts/canary_cli.py export --output reports/canary

# 查看审计日志
python scripts/canary_cli.py audit --hours 24
```

### 演示脚本

```bash
# 运行完整演示
python scripts/demo_canary.py
```

### 编程接口

```python
from modules.canary import get_canary_executor, get_config_manager

# 获取组件实例
config_manager = get_config_manager()
canary_executor = get_canary_executor()

# 启动金丝雀部署
result = canary_executor.start_canary("candidate_high_recall")

# 执行搜索请求（自动流量切分）
results, config_used = canary_executor.execute_search(
    query="machine learning",
    collection_name="documents"
)

# 停止部署
result = canary_executor.stop_canary(promote=True)
```

## 配置格式

### 配置预设示例

```yaml
# configs/presets/candidate_high_recall.yaml
metadata:
  name: "candidate_high_recall"
  description: "High recall optimized configuration"
  version: "1.1.0"
  tags: ["candidate", "high-recall"]

# 宏旋钮
macro_knobs:
  latency_guard: 0.3
  recall_bias: 0.8

# 派生参数快照
derived_params:
  T: 500
  Ncand_max: 1200
  batch_size: 256
  ef: 224
  rerank_multiplier: 5

# 检索配置
retriever:
  type: hybrid
  alpha: 0.7
  vector_top_k: 300
  bm25_top_k: 300
  top_k: 50

# 重排序配置
reranker:
  type: cross_encoder
  model: cross-encoder/ms-marco-MiniLM-L-6-v2
  top_k: 50

# SLO目标
slo:
  p95_ms: 1200
  recall_at_10: 0.30
```

## 输出文件

### 1. 金丝雀结果
- **文件**: `reports/canary/canary_result.json`
- **内容**: 部署状态、指标摘要、回滚原因等

```json
{
  "deployment_id": "canary_1234567890_1234",
  "start_time": "2024-01-01T12:00:00Z",
  "end_time": "2024-01-01T12:05:00Z",
  "status": "rolled_back",
  "active_config": "last_good",
  "candidate_config": "candidate_high_recall",
  "traffic_split": {"active": 0.9, "candidate": 0.1},
  "metrics_summary": {
    "active_config": {...},
    "candidate_config": {...}
  },
  "rollback_reason": "SLO violation: p95_latency failed for 2 consecutive buckets",
  "total_requests": 150,
  "duration_seconds": 300.0
}
```

### 2. 指标数据
- **文件**: `reports/canary/metrics.json`
- **内容**: 每5秒桶的性能指标

```json
{
  "export_timestamp": "2024-01-01T12:05:00Z",
  "bucket_duration_sec": 5,
  "total_buckets": 60,
  "buckets": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "duration_sec": 5,
      "p95_ms": 850.5,
      "recall_at_10": 0.35,
      "response_count": 25,
      "slo_violations": 2,
      "config_name": "candidate_high_recall"
    }
  ]
}
```

### 3. 审计日志
- **文件**: `reports/canary/audit.log`
- **内容**: 所有操作的审计记录

```json
{
  "event_id": "audit_1234567890_1234",
  "event_type": "canary_start",
  "timestamp": "2024-01-01T12:00:00Z",
  "deployment_id": "canary_1234567890_1234",
  "user_id": "admin",
  "config_name": "candidate_high_recall",
  "details": {
    "candidate_config": "candidate_high_recall",
    "traffic_split": {"active": 0.9, "candidate": 0.1},
    "action": "start_canary_deployment"
  },
  "success": true,
  "error_message": null
}
```

## SLO规则配置

默认SLO规则：
- **延迟**: p95 ≤ 1200ms
- **召回率**: recall@10 ≥ 0.30
- **违规阈值**: 连续2个桶不达标触发回滚

可通过编程方式自定义SLO规则：

```python
from modules.canary import get_slo_monitor, SLORule

slo_monitor = get_slo_monitor()

# 添加自定义SLO规则
custom_rule = SLORule(
    name="custom_latency",
    metric="p95_ms",
    operator="le",
    threshold=800.0,
    consecutive_buckets=3
)

slo_monitor.add_slo_rule(custom_rule)
```

## 监控和告警

系统提供实时监控能力：

```python
# 获取当前状态
status = canary_executor.get_current_status()
print(f"Deployment: {status['deployment_id']}")
print(f"Status: {status['status']}")
print(f"Total requests: {status['total_requests']}")

# 获取指标摘要
metrics = metrics_collector.get_summary_stats("candidate_high_recall", window_minutes=10)
print(f"Avg P95: {metrics['avg_p95_ms']:.2f} ms")
print(f"Avg Recall: {metrics['avg_recall_at_10']:.3f}")
print(f"SLO violations: {metrics['total_slo_violations']}")

# 获取SLO违规历史
violations = slo_monitor.get_violations(config_name="candidate_high_recall")
for violation in violations:
    print(f"SLO violation: {violation.rule_name} - {violation.metric_value} vs {violation.threshold}")
```

## 最佳实践

1. **配置管理**
   - 始终保留 `last_good` 配置作为稳定基线
   - 候选配置命名使用描述性名称（如 `candidate_high_recall`）
   - 定期备份配置预设

2. **金丝雀部署**
   - 从小流量开始（10%），逐步增加
   - 监控关键指标至少10分钟再决定推广
   - 准备快速回滚方案

3. **SLO监控**
   - 设置合理的SLO阈值
   - 监控连续违规而非单次违规
   - 及时响应自动回滚

4. **审计和日志**
   - 定期导出审计日志
   - 分析回滚原因并优化配置
   - 建立监控仪表板

## 故障排除

### 常见问题

1. **金丝雀启动失败**
   - 检查候选配置是否存在
   - 确认没有其他金丝雀部署在运行
   - 验证配置格式正确

2. **SLO违规频繁**
   - 检查SLO阈值设置是否合理
   - 分析性能指标趋势
   - 调整候选配置参数

3. **自动回滚未触发**
   - 确认SLO监控正在运行
   - 检查违规阈值配置
   - 验证指标收集正常

### 调试命令

```bash
# 查看详细状态
python scripts/canary_cli.py status

# 查看实时指标
python scripts/canary_cli.py metrics --window 5

# 查看审计日志
python scripts/canary_cli.py audit --hours 1

# 导出所有数据进行分析
python scripts/canary_cli.py export
```

## 扩展功能

系统设计支持以下扩展：

1. **多环境支持**: 支持测试、预生产、生产环境
2. **A/B测试**: 支持多候选配置同时测试
3. **自定义指标**: 支持添加自定义性能指标
4. **告警集成**: 集成外部监控和告警系统
5. **可视化仪表板**: 提供Web界面监控

## 贡献指南

1. 遵循现有代码风格
2. 添加适当的单元测试
3. 更新文档和示例
4. 通过所有测试用例

## 许可证

本项目采用与主项目相同的许可证。


