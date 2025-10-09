# AutoTuner Brain

可单测、可扩展的 AutoTuner 大脑最小版：纯函数决策 + 约束 + 应用器 + 小样本回归 + 单测。

## 特性

- **纯函数设计**：零 I/O、零网络、零全局状态（除测试/样例外）
- **清晰的类型与契约**：便于后续接到 Pipeline
- **最小策略**：可解释的决策逻辑，附 reason
- **完整测试覆盖**：单元测试与本地 sanity 运行脚本

## 核心组件

### 1. 数据模型 (`contracts.py`)
- `TuningInput`: 调优输入数据（性能指标、参数、SLO、守护条件）
- `Action`: 调优动作（类型、幅度、原因）
- `SLO`: 服务级别目标
- `Guards`: 守护条件

### 2. 决策逻辑 (`decider.py`)
实现最小规则集：
1. 守护：冷却期 → noop
2. 延迟超标且召回有冗余 → 降ef或降ncand
3. 召回不达标且延迟有余量 → 升ef或升rerank
4. 临界区优化 → 升T
5. 其他情况 → noop

### 3. 参数约束 (`constraints.py`)
- 参数范围裁剪：ef∈[64,256], T∈[200,1200], Ncand_max∈[500,2000], rerank_mult∈[2,6]
- 滞回判断工具函数

### 4. 动作应用 (`apply.py`)
- 将 Action 应用到参数配置
- 自动参数裁剪到合法范围
- 不可变式参数更新

### 5. 测试样例 (`fixtures.py`)
12 个测试场景覆盖主要决策路径和边界情况。

## 使用方法

### 运行单元测试
```bash
cd /Users/nanxinli/Documents/dev/searchforge
python -m pytest tests/test_decider.py -v
```

### 运行 Sanity 检查
```bash
cd /Users/nanxinli/Documents/dev/searchforge
python scripts/run_brain_sanity.py
```

### 在代码中使用
```python
from modules.autotuner.brain import decide_tuning_action, apply_action, TuningInput, SLO, Guards

# 创建输入
inp = TuningInput(
    p95_ms=250.0,
    recall_at10=0.92,
    qps=100.0,
    params={'ef': 128, 'T': 500, 'Ncand_max': 1000, 'rerank_mult': 3},
    slo=SLO(p95_ms=200.0, recall_at10=0.85),
    guards=Guards(cooldown=False, stable=True),
    near_T=False
)

# 决策
action = decide_tuning_action(inp)

# 应用
new_params = apply_action(inp.params, action)
```

## 验收标准

✅ **pytest 全部通过**：17 个测试用例，100% 通过率  
✅ **Sanity 脚本输出**：12 行测试用例，每行包含 kind, reason, 参数变化  
✅ **零 I/O/网络调用**：所有函数都是纯计算  
✅ **代码风格**：PEP8，类型注解齐全，关键处含 docstring

## 文件清单

创建/修改的文件：
- `modules/autotuner/brain/__init__.py`
- `modules/autotuner/brain/contracts.py`
- `modules/autotuner/brain/constraints.py`
- `modules/autotuner/brain/decider.py`
- `modules/autotuner/brain/apply.py`
- `modules/autotuner/brain/fixtures.py`
- `modules/autotuner/brain/README.md`
- `scripts/run_brain_sanity.py`
- `tests/test_decider.py`
