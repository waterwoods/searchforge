# AutoTuner 文档索引

> 快速导航：AutoTuner 系统的所有工程文档

**版本**：v1.0  
**更新日期**：2025-10-08  
**维护者**：nanxinli

---

## 📚 核心文档

### 1. 主文档（必读）
**[AutoTuner_README.md](./AutoTuner_README.md)**  
完整的工程文档（1200+ 行），包含：
- 系统概览与架构
- 代码结构扫描（文件→职责→关键函数）
- I/O 契约表（数据结构、事件流、环境开关）
- 数据流与序列图（Mermaid 源码）
- 最小可依赖接口清单
- 快速校验与风险点分析
- 集成示例

**适用场景**：技术面试、团队培训、系统对接

---

## 📊 辅助文档

### 2. 测试覆盖面报告
**[TEST_COVERAGE_SUMMARY.md](./TEST_COVERAGE_SUMMARY.md)**  
- 98 个单元测试的详细分析
- 关键路径覆盖率（11/11，100%）
- 场景覆盖详情（9 个测试套件）
- 未覆盖场景与改进建议

**适用场景**：质量评估、测试规划

---

### 3. 交付总结
**[AUTOTUNER_DELIVERY_SUMMARY.md](./AUTOTUNER_DELIVERY_SUMMARY.md)**  
- 交付物清单（7 个文件）
- 完成情况统计（100% 达成）
- 文档质量指标（142% 达成率）
- 使用指南与后续改进建议

**适用场景**：项目交付、进度汇报

---

## 🗂️ Schema 定义

### 4. Action Schema
**[schemas/autotuner_action.schema.json](./schemas/autotuner_action.schema.json)**  
调优动作的 JSON Schema 定义，包含：
- 11 种动作类型枚举
- 字段类型与约束
- 完整示例

**适用场景**：接口对接、类型生成

---

### 5. Params Schema
**[schemas/autotuner_params.schema.json](./schemas/autotuner_params.schema.json)**  
搜索参数的 JSON Schema 定义，包含：
- 4 个参数的边界约束
- 3 个联合约束说明
- 完整示例

**适用场景**：参数验证、配置管理

---

## 🎨 流程图资源

### 6. Mermaid 图表源码
**[figs/autotuner_flow_mermaid.md](./figs/autotuner_flow_mermaid.md)**  
4 个 Mermaid 图表的源码：
1. 完整数据流图（25 节点）
2. 时序图（7 参与者）
3. 多参数调优流程图（14 步骤）
4. 系统架构图（6 模块）

**适用场景**：技术讲解、文档插图

---

### 7. 图表生成指南
**[figs/README.md](./figs/README.md)**  
PNG 图片生成指南，包含：
- 在线工具使用方法（Mermaid Live）
- 命令行工具安装与使用（mmdc）
- VS Code 插件使用
- 故障排查

**适用场景**：图表导出、演示准备

---

## 🧪 验证与测试

### 8. 契约验证脚本
**[../scripts/verify_autotuner_contracts.py](../scripts/verify_autotuner_contracts.py)**  
自动化验证脚本（可执行），包含：
- 5 个验证测试
- 参数裁剪、联合约束、决策逻辑、动作应用、边界情况

**运行方式**：
```bash
python scripts/verify_autotuner_contracts.py
```

**适用场景**：环境验证、回归测试

---

## 🚀 快速开始

### 初次使用（5 分钟）
1. 阅读 [AutoTuner_README.md](./AutoTuner_README.md) 的"系统概览"
2. 运行 [verify_autotuner_contracts.py](../scripts/verify_autotuner_contracts.py) 验证环境
3. 复制"最小接入示例"到你的项目

### 深入学习（30 分钟）
1. 完整阅读 [AutoTuner_README.md](./AutoTuner_README.md)
2. 查看 [autotuner_flow_mermaid.md](./figs/autotuner_flow_mermaid.md) 的流程图
3. 阅读 [TEST_COVERAGE_SUMMARY.md](./TEST_COVERAGE_SUMMARY.md)

### 集成开发（2 小时）
1. 研究 `modules/search/search_pipeline.py` 的集成示例
2. 运行 `scripts/autotuner_demo.py` 查看完整演示
3. 参考 `tests/test_decider.py` 编写单元测试

---

## 📖 文档结构

```
docs/
├── INDEX.md                          # 本文件（文档索引）
├── AutoTuner_README.md               # 主文档（1200+ 行）
├── TEST_COVERAGE_SUMMARY.md          # 测试覆盖面报告
├── AUTOTUNER_DELIVERY_SUMMARY.md     # 交付总结
├── schemas/
│   ├── autotuner_action.schema.json  # Action Schema
│   └── autotuner_params.schema.json  # Params Schema
└── figs/
    ├── README.md                      # 图表生成指南
    └── autotuner_flow_mermaid.md      # Mermaid 图表源码
```

---

## 🔗 相关资源

### 源代码
- **Brain 模块**：`modules/autotuner/brain/`
- **集成代码**：`modules/search/search_pipeline.py`
- **测试套件**：`tests/test_decider*.py`, `tests/test_memory*.py`, etc.

### 工具脚本
- **演示脚本**：`scripts/autotuner_demo.py`
- **验证脚本**：`scripts/verify_autotuner_contracts.py`
- **解释工具**：`scripts/explain_autotuner_logic.py`

### 外部资源
- [Mermaid 官方文档](https://mermaid.js.org/)
- [Mermaid Live Editor](https://mermaid.live/)
- [JSON Schema 规范](https://json-schema.org/)

---

## 💡 推荐阅读路径

### 路径 1：快速理解（适合面试准备）
1. [AutoTuner_README.md](./AutoTuner_README.md) § 系统概览
2. [autotuner_flow_mermaid.md](./figs/autotuner_flow_mermaid.md) § 完整数据流图
3. [AutoTuner_README.md](./AutoTuner_README.md) § I/O 契约表
4. [AutoTuner_README.md](./AutoTuner_README.md) § 最小可依赖接口

### 路径 2：深入学习（适合开发集成）
1. [AutoTuner_README.md](./AutoTuner_README.md) 全文
2. [TEST_COVERAGE_SUMMARY.md](./TEST_COVERAGE_SUMMARY.md)
3. `modules/autotuner/brain/` 源代码
4. `tests/test_decider.py` 单元测试

### 路径 3：质量评估（适合技术评审）
1. [AUTOTUNER_DELIVERY_SUMMARY.md](./AUTOTUNER_DELIVERY_SUMMARY.md)
2. [TEST_COVERAGE_SUMMARY.md](./TEST_COVERAGE_SUMMARY.md)
3. [schemas/](./schemas/) JSON Schema 文件
4. 运行验证脚本

---

## 📞 联系与反馈

**维护者**：nanxinli  
**项目路径**：`/Users/nanxinli/Documents/dev/searchforge`  
**文档版本**：v1.0  

如有问题或建议，请：
1. 查阅 [AutoTuner_README.md](./AutoTuner_README.md) 的"附录"
2. 运行 [verify_autotuner_contracts.py](../scripts/verify_autotuner_contracts.py) 排查问题
3. 参考 [TEST_COVERAGE_SUMMARY.md](./TEST_COVERAGE_SUMMARY.md) 的"故障排查"

---

**最后更新**：2025-10-08  
**文档状态**：✅ 完整交付
