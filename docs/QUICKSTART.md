# AutoTuner 快速开始指南

> 5 分钟快速理解 AutoTuner 系统

---

## 📖 阅读顺序

### 第一步：查看索引（1 分钟）
打开 **[INDEX.md](./INDEX.md)** 了解所有文档的结构。

### 第二步：理解核心概念（3 分钟）
阅读 **[AutoTuner_README.md](./AutoTuner_README.md)** 的以下章节：
1. **系统概览** - 了解 AutoTuner 是什么
2. **数据流与序列图** - 查看完整数据流图（Mermaid）
3. **最小可依赖接口** - 学习如何接入（3 个核心函数）

### 第三步：验证环境（1 分钟）
运行验证脚本：
```bash
cd /Users/nanxinli/Documents/dev/searchforge
python scripts/verify_autotuner_contracts.py
```

预期输出：
```
=== AutoTuner 契约验证 ===

测试 1: 参数边界裁剪 ✅
测试 2: 联合约束验证 ✅
测试 3: 决策逻辑 ✅
测试 4: 动作应用 ✅
测试 5: 边界情况 ✅

✅ 所有验证通过！
```

---

## 🚀 最小接入示例

```python
#!/usr/bin/env python3
"""最小接入示例（5 行代码）"""
import os
from modules.autotuner.brain.contracts import TuningInput, SLO, Guards
from modules.autotuner.brain.decider import decide_tuning_action
from modules.autotuner.brain.apply import apply_action

# 1. 启用 Brain
os.environ['BRAIN_ENABLED'] = '1'
os.environ['MEMORY_ENABLED'] = '1'

# 2. 准备输入数据
inp = TuningInput(
    p95_ms=250.0,              # 当前延迟
    recall_at10=0.82,          # 当前召回率
    qps=100.0,                 # 当前 QPS
    params={                   # 当前参数
        'ef': 128,
        'T': 500,
        'Ncand_max': 1000,
        'rerank_mult': 3
    },
    slo=SLO(                   # SLO 目标
        p95_ms=200.0,
        recall_at10=0.85
    ),
    guards=Guards(             # 守护条件
        cooldown=False,
        stable=True
    ),
    near_T=False
)

# 3. 决策
action = decide_tuning_action(inp)
print(f"决策: {action.kind}, 步长: {action.step}, 原因: {action.reason}")

# 4. 应用
new_params = apply_action(inp.params, action)
print(f"新参数: {new_params}")

# 5. 使用新参数执行查询
# your_search_function(**new_params)
```

**输出示例**：
```
决策: drop_ef, 步长: -32.0, 原因: high_latency_with_recall_redundancy
新参数: {'ef': 96, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3}
```

---

## 📊 核心数据结构

### TuningInput（输入）
| 字段 | 类型 | 说明 |
|------|------|------|
| `p95_ms` | float | 当前 P95 延迟 |
| `recall_at10` | float | Top10 召回率 |
| `params` | Dict | 当前参数 (ef, T, Ncand_max, rerank_mult) |
| `slo` | SLO | 服务级别目标 |
| `guards` | Guards | 守护条件 (冷却期, 稳定性) |

### Action（输出）
| 字段 | 类型 | 说明 |
|------|------|------|
| `kind` | str | 动作类型 (bump_ef, drop_ef, noop, ...) |
| `step` | float | 调整幅度 |
| `reason` | str | 解释说明 |

### 参数范围
| 参数 | 最小值 | 最大值 | 默认值 |
|------|--------|--------|--------|
| `ef` | 64 | 256 | 128 |
| `T` | 200 | 1200 | 500 |
| `Ncand_max` | 500 | 2000 | 1000 |
| `rerank_mult` | 2 | 6 | 3 |

---

## 🎨 可视化流程图

### 查看方式 1：在线渲染
1. 访问 https://mermaid.live/
2. 打开 `docs/figs/autotuner_flow_mermaid.md`
3. 复制"完整数据流图"的代码
4. 粘贴到编辑器，点击"Download PNG"

### 查看方式 2：VS Code 预览
1. 安装插件：`Markdown Preview Mermaid Support`
2. 打开 `docs/figs/autotuner_flow_mermaid.md`
3. 按 `Cmd+Shift+V`（Mac）预览

---

## 🔍 常见问题

### Q1: 如何启用 AutoTuner？
```bash
export BRAIN_ENABLED=1
export MEMORY_ENABLED=1
export SLO_P95_MS=200
export SLO_RECALL_AT10=0.85
```

### Q2: 如何调试决策逻辑？
使用 `analyze_tuning_input()` 函数：
```python
from modules.autotuner.brain.decider import analyze_tuning_input
analysis = analyze_tuning_input(inp)
print(analysis)  # 输出诊断信息
```

### Q3: 如何验证参数是否合法？
```python
from modules.autotuner.brain.constraints import is_param_valid, validate_joint_constraints

# 检查边界
is_param_valid(params)  # True/False

# 检查联合约束
validate_joint_constraints(params)  # True/False
```

### Q4: 如何查看测试覆盖面？
查看 **[TEST_COVERAGE_SUMMARY.md](./TEST_COVERAGE_SUMMARY.md)**

---

## 📚 进一步学习

### 深入理解
- **完整文档**：[AutoTuner_README.md](./AutoTuner_README.md)
- **流程图**：[figs/autotuner_flow_mermaid.md](./figs/autotuner_flow_mermaid.md)
- **测试覆盖**：[TEST_COVERAGE_SUMMARY.md](./TEST_COVERAGE_SUMMARY.md)

### 集成开发
- **源代码**：`modules/autotuner/brain/`
- **集成示例**：`modules/search/search_pipeline.py`
- **完整演示**：`scripts/autotuner_demo.py`

### JSON Schema
- **Action Schema**：[schemas/autotuner_action.schema.json](./schemas/autotuner_action.schema.json)
- **Params Schema**：[schemas/autotuner_params.schema.json](./schemas/autotuner_params.schema.json)

---

## ✅ 验证清单

- [ ] 阅读 INDEX.md
- [ ] 阅读 AutoTuner_README.md 的核心章节
- [ ] 运行 verify_autotuner_contracts.py
- [ ] 复制最小接入示例到项目
- [ ] 查看 Mermaid 流程图
- [ ] 运行单元测试（可选）

---

**祝你使用愉快！** 🎉

如有问题，请查阅完整文档或联系维护者。
