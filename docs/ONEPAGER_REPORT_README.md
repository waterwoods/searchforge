# AutoTuner 一页报告生成器

## 📋 概述

自动从 `~/Downloads/autotuner_runs/` 目录收集 AutoTuner 实验数据，生成包含以下内容的专业报告：

1. **0-1小时召回率追踪**：时序趋势图（Recall@10 和 P95 延迟）
2. **三维度评估**：质量、SLA、成本的综合评分
3. **多场景对比**：场景 A/B/C 的并排分析
4. **双格式输出**：Markdown 和 PDF

## 🚀 快速开始

### 一键生成完整报告

```bash
./scripts/run_full_report.sh
```

### 分步执行

```bash
# 1. 收集数据
python3 scripts/collect_onepager_data.py

# 2. 生成时序曲线
python3 scripts/plot_timeseries.py

# 3. 生成 Markdown 报告
python3 scripts/build_onepager.py

# 4. 生成 PDF 报告
python3 scripts/generate_pdf_report.py
```

## 📁 输出文件

执行完成后，会生成以下文件：

```
docs/
├── RESULTS_SUMMARY.md              # Markdown 格式报告
├── one_pager_autotuner.pdf         # PDF 格式报告
├── collected_metrics.json          # 原始指标数据
└── plots/
    ├── scenario_A_recall.png       # 场景A召回率曲线
    ├── scenario_A_p95.png          # 场景A P95延迟曲线
    ├── scenario_B_recall.png       # 场景B召回率曲线
    ├── scenario_B_p95.png          # 场景B P95延迟曲线
    ├── scenario_C_recall.png       # 场景C召回率曲线
    ├── scenario_C_p95.png          # 场景C P95延迟曲线
    └── plots_info.json             # 曲线元数据
```

## 🎯 评估标准

### 质量维度
- ✅ **绿色**：p < 0.05（统计显著）且 ΔRecall ≥ -0.01
- ⚠️ **黄色**：p ≥ 0.05 或样本不足（< 10桶）
- ❌ **红色**：ΔRecall < -0.01（召回率明显下降）

### SLA 维度
- ✅ **绿色**：ΔP95 ≤ 5ms 且 Safety ≥ 0.99
- ⚠️ **黄色**：ΔP95 ≤ 20ms 或 Safety ≥ 0.95
- ❌ **红色**：ΔP95 > 20ms 或 Safety < 0.95

### 成本维度
- ✅ **绿色**：≤ $0.00005/查询
- ⚠️ **黄色**：≤ $0.0001/查询
- ❌ **红色**：> $0.0001/查询

### 综合判定
- **PASS**：三个维度全绿
- **WARN**：有黄色但无红色
- **FAIL**：至少一个红色

## 📊 数据源要求

脚本会自动从以下位置查找实验数据：

```
~/Downloads/autotuner_runs/
├── 20251008_2120/
│   └── LOCAL_20251008_2120/
│       └── scenario_A/
│           └── one_pager.json
├── 20251008_1432/
│   ├── B_multi/
│   │   └── LOCAL_20251008_2332/
│   │       └── scenario_B/
│   │           └── one_pager.json
│   └── C_multi/
│       └── LOCAL_20251008_2332/
│           └── scenario_C/
│               └── one_pager.json
...
```

每个场景需要至少包含 `one_pager.json` 文件，内容格式参考：

```json
{
  "scenario": "A",
  "preset": "High-Latency, Low-Recall",
  "mode": "live",
  "duration_sec": 3600,
  "bucket_sec": 10,
  "qps": 12,
  "comparison": {
    "delta_p95_ms": 15.2,
    "delta_recall": 0.028,
    "p_value": 0.023,
    "safety_rate": 0.995,
    "apply_rate": 0.967
  }
}
```

## 🔧 依赖项

- Python 3.8+
- matplotlib
- numpy

所有依赖已包含在 `requirements.txt` 中。

## 📝 示例输出

### 终端摘要

```
============================================================
[曲线] A/B/C 曲线已生成（总桶数: 480）
[汇总] Verdict=WARN | ΔRecall=0.028 | ΔP95=15.2ms | 成本=$0.000038
============================================================
```

### 报告内容

- **场景概览表**：所有场景的关键指标和判定
- **三维度卡片**：每个场景的质量/SLA/成本详细评估
- **时序曲线**：召回率和P95延迟的演进趋势
- **总结统计**：平均指标和整体判定

## 🎨 特性

1. ✅ **自动发现**：递归扫描目录，自动定位最新实验
2. ✅ **多场景支持**：同时处理场景 A/B/C
3. ✅ **时序分析**：以10秒为桶，展示0-1小时趋势
4. ✅ **智能平滑**：使用 EWMA(α=0.3) 消除噪声
5. ✅ **颜色编码**：直观的红/黄/绿评级系统
6. ✅ **双格式输出**：同时生成 Markdown 和 PDF
7. ✅ **中文支持**：完整的中文标题和说明

## 🐛 故障排除

### 未找到数据

如果提示"未找到任何场景数据"，请检查：
1. 数据目录路径是否正确（`~/Downloads/autotuner_runs/`）
2. 子目录中是否包含 `one_pager.json` 文件
3. JSON 文件格式是否正确

### 曲线生成失败

如果曲线无法生成，可能是：
1. matplotlib 未安装：`pip install matplotlib`
2. 字体缺失（仅影响中文显示，不影响功能）

### PDF 生成警告

Emoji 字体警告（如 ⚠️ ✅ ❌）是正常的，不影响 PDF 生成。

## 📞 联系方式

如有问题，请查阅 `docs/AutoTuner_README.md` 或联系开发团队。

