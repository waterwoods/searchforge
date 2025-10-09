# AutoTuner 测试覆盖面总结

## 测试统计

### 核心测试套件运行结果

| 测试文件 | 用例数 | 通过 | 失败 | 覆盖场景 |
|---------|-------|------|------|---------|
| `test_decider.py` | 20 | 20 | 0 | 单参数决策逻辑 |
| `test_memory_basic.py` | 7 | 7 | 0 | 记忆系统基础功能 |
| `test_apply_atomic.py` | 24 | 24 | 0 | 参数应用与原子化 |
| `test_constraints_joint.py` | 21 | 21 | 0 | 联合约束验证 |
| `test_multi_knob_decider.py` | 8 | 7 | 1* | 多参数决策 |
| `test_decider_with_memory.py` | 5 | 5 | 0 | 记忆钩子集成 |
| `test_hysteresis_cooldown.py` | 4 | 4 | 0 | 防震荡机制 |
| `test_rr_and_cooldown.py` | 3 | 3 | 0 | 轮询与冷却 |
| `test_adversarial_safety.py` | 6 | 6 | 0 | 边界安全测试 |

**总计**：98 个测试用例，97 通过，1 失败*

\* 失败用例说明：`test_latency_drop_selection` 测试中预期值 `-64` 与实际值 `-32` 不匹配，这是因为代码中已将步长从 `-64` 调整为 `-32` 以提高安全性（见 `multi_knob_decider.py:16`），测试用例需要更新预期值。

---

## 场景覆盖详情

### 1. 决策逻辑（test_decider.py - 20 个用例）

#### 守护与保护机制
- ✅ 冷却期返回 noop
- ✅ 滞回带内不调整
- ✅ 不稳定状态保守操作

#### 性能指标驱动
- ✅ 高延迟 + 召回富余 → 降 ef
- ✅ 高延迟 + ef 已最小 → 降 ncand
- ✅ 低召回 + 延迟富余 → 升 ef
- ✅ 低召回 + ef 已最大 → 升 rerank
- ✅ 临界区优化（near_T）→ 升 T

#### 边界情况
- ✅ 参数到达最小值时的行为
- ✅ 参数到达最大值时的行为
- ✅ 极端指标值处理

#### 防震荡机制
- ✅ 连续相同动作冷却
- ✅ 自适应步长调整
- ✅ 震荡检测与抑制

---

### 2. 记忆系统（test_memory_basic.py - 7 个用例）

#### 基础功能
- ✅ 记忆样本创建
- ✅ 环形缓冲（Ring Buffer）
- ✅ EWMA 指数移动平均计算

#### 甜点发现
- ✅ 甜点更新逻辑
- ✅ 甜点查询与过期检查
- ✅ 分桶策略（default_bucket_of）

#### 集成测试
- ✅ 多样本观测与收敛
- ✅ TTL 过期处理

---

### 3. 参数应用（test_apply_atomic.py - 24 个用例）

#### 单参数应用
- ✅ bump_ef / drop_ef
- ✅ bump_T / drop_T
- ✅ bump_rerank / drop_rerank
- ✅ bump_ncand / drop_ncand
- ✅ noop / rollback

#### 多参数应用
- ✅ sequential 模式（顺序应用）
- ✅ atomic 模式（原子应用）
- ✅ 可行性预测（feasibility pre-projection）
- ✅ 渐进缩减（progressive shrinking）
- ✅ 回滚机制（rollback on failure）

#### 统计跟踪
- ✅ 决策计数器
- ✅ 参数更新计数器
- ✅ 裁剪与拒绝统计

---

### 4. 约束验证（test_constraints_joint.py - 21 个用例）

#### 边界约束
- ✅ ef ∈ [64, 256]
- ✅ T ∈ [200, 1200]
- ✅ Ncand_max ∈ [500, 2000]
- ✅ rerank_mult ∈ [2, 6]

#### 联合约束
- ✅ rerank_mult ≤ Ncand_max × 0.1
- ✅ ef ≤ 4 × Ncand_max
- ✅ 归一化 T/1000 ∈ [0, 1]

#### 裁剪与修复
- ✅ clip_params（边界裁剪）
- ✅ clip_joint（联合约束裁剪）
- ✅ is_param_valid（有效性检查）
- ✅ validate_joint_constraints（联合验证）

---

### 5. 多参数决策（test_multi_knob_decider.py - 8 个用例）

#### 预设策略
- ✅ latency_drop bundle（降延迟）
- ✅ recall_gain bundle（提升召回）
- ✅ steady_nudge bundle（稳态微调）

#### 选择逻辑
- ✅ 性能指标驱动
- ✅ 宏观偏置（L/R bias）
- ✅ 轮询策略（round-robin）
- ✅ 记忆甜点触发

#### 冷却与微步
- ✅ 冷却期微步调整
- ✅ 冷却计数器管理

---

### 6. 记忆钩子集成（test_decider_with_memory.py - 5 个用例）

- ✅ 记忆启用时优先查询
- ✅ 有甜点时靠拢动作
- ✅ 无甜点时回退到规则决策
- ✅ 已在甜点位置时 noop
- ✅ 记忆禁用时跳过钩子

---

### 7. 防震荡机制（test_hysteresis_cooldown.py - 4 个用例）

- ✅ 滞回带判断（hysteresis band）
- ✅ 冷却期强制 noop
- ✅ 连续调整计数
- ✅ 自适应步长缩减

---

### 8. 轮询与冷却（test_rr_and_cooldown.py - 3 个用例）

- ✅ Bundle 轮询状态管理
- ✅ 冷却期倒计时
- ✅ 轮询索引递增

---

### 9. 边界安全测试（test_adversarial_safety.py - 6 个用例）

- ✅ 恶意超大参数输入
- ✅ 负数参数输入
- ✅ 零值参数输入
- ✅ 极端 SLO 值
- ✅ 空参数字典
- ✅ 缺失必需字段

---

## 关键路径覆盖率

| 路径 | 覆盖 | 测试用例 |
|------|------|---------|
| 记忆钩子 → 甜点靠拢 | ✅ | test_decider_with_memory.py |
| 记忆钩子 → 规则决策 | ✅ | test_decider_with_memory.py |
| 冷却期 → noop | ✅ | test_decider.py::test_cooldown_returns_noop |
| 滞回带 → noop | ✅ | test_decider.py::test_hysteresis_band |
| 高延迟 + 召回富余 → 降 ef | ✅ | test_decider.py::test_high_latency_recall_redundant_drops_ef |
| 低召回 + 延迟富余 → 升 ef | ✅ | test_decider.py::test_low_recall_latency_margin_bumps_ef |
| near_T → 升 T | ✅ | test_decider.py::test_near_T_boundary_optimization_bumps_T |
| 单参数应用 → 边界裁剪 | ✅ | test_apply_atomic.py::test_single_knob_clip |
| 多参数应用 → 联合约束 | ✅ | test_apply_atomic.py::test_multi_knob_joint_constraint |
| 可行性预测 → 渐进缩减 | ✅ | test_apply_atomic.py::test_feasibility_shrinking |
| 原子应用 → 回滚 | ✅ | test_apply_atomic.py::test_atomic_rollback |

**覆盖率**：11/11 关键路径（100%）

---

## 未覆盖场景（待补充）

### 1. 性能测试
- ⚠️ 高并发场景（>1000 QPS）
- ⚠️ 长时间运行稳定性（>24小时）
- ⚠️ 内存泄漏检测

### 2. 集成测试
- ⚠️ 与 Qdrant 向量数据库的真实交互
- ⚠️ 与 SearchPipeline 的端到端集成
- ⚠️ 多实例并发调优

### 3. 边缘案例
- ⚠️ 网络分区导致的记忆不一致
- ⚠️ 极端流量突变（0→10000 QPS）
- ⚠️ SLO 动态调整

---

## 测试运行指南

### 运行所有 AutoTuner 测试
```bash
cd /Users/nanxinli/Documents/dev/searchforge
pytest tests/test_decider*.py tests/test_memory*.py tests/test_apply*.py tests/test_constraints*.py tests/test_multi_knob*.py -v
```

### 运行契约验证脚本
```bash
python scripts/verify_autotuner_contracts.py
```

### 运行特定测试
```bash
# 只运行决策器测试
pytest tests/test_decider.py -v

# 只运行记忆系统测试
pytest tests/test_memory_basic.py -v

# 运行带覆盖率报告
pytest tests/ -k "decider or memory" --cov=modules.autotuner.brain --cov-report=html
```

---

## 测试质量评估

### 优点
- ✅ 覆盖面广（98 个用例，11 个关键路径）
- ✅ 边界情况测试充分
- ✅ 契约验证自动化
- ✅ 防震荡机制验证完整

### 改进建议
1. **增加性能基准测试**：确保调优不会引入性能倒退
2. **补充集成测试**：端到端验证与 SearchPipeline 的集成
3. **添加压力测试**：验证高并发场景下的稳定性
4. **覆盖率报告**：定期生成覆盖率报告（目标 >90%）

---

## 测试维护

### 测试更新检查清单
- [ ] 新增功能是否有对应测试用例？
- [ ] 参数范围变更是否更新约束测试？
- [ ] 决策逻辑调整是否更新决策测试？
- [ ] 预设 Bundle 修改是否更新多参数测试？
- [ ] 契约变更是否更新 Schema 和验证脚本？

### 定期维护任务
- **每周**：运行完整测试套件，确保无回归
- **每月**：审查失败用例，更新过期测试
- **每季度**：评估覆盖率，补充缺失场景

---

**最后更新**：2025-10-08  
**维护者**：nanxinli  
**版本**：v1.0
