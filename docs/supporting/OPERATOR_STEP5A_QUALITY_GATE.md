# Step 5A: Quality Gate for Auto Insurance Daily Pipeline

## Overview

质量闸门（Quality Gate）是 Auto Insurance Daily Pipeline 的入库前过滤步骤，确保只有高质量、相关的文档进入 Qdrant 集合 `auto_insurance_v2_clean`。

## 功能

质量闸门会过滤以下类型的坏数据：

1. **非 allowlist 域名**：只允许指定域名的文档
2. **二进制文件**：PDF、Excel、Word、图片、视频等
3. **文本过短**：默认 < 800 字符
4. **非汽车保险主题**：通过关键词匹配判断相关性

## 配置

### Allowlist 域名

默认允许的域名：
- `dmv.ca.gov`
- `insurance.ca.gov`
- `geico.com`
- `progressive.com`

#### 如何扩展 Allowlist

方法 1：通过配置文件（推荐）

编辑 `results/auto_insurance/daily_targets.json`：

```json
{
  "target_urls": [...],
  "allowed_domains": [
    "dmv.ca.gov",
    "insurance.ca.gov",
    "geico.com",
    "progressive.com",
    "newdomain.com"  // 添加新域名
  ]
}
```

方法 2：修改代码默认值

编辑 `pipelines/quality_gate_auto_insurance.py`，修改 `DEFAULT_ALLOWLIST_DOMAINS`：

```python
DEFAULT_ALLOWLIST_DOMAINS = {
    "dmv.ca.gov",
    "insurance.ca.gov",
    "geico.com",
    "progressive.com",
    "newdomain.com"  # 添加新域名
}
```

### 最小字符数（阈值分层）

**阈值分层策略**：
- **Ingest（页面级）**：800 字符（保持不变）
- **Quality Gate（chunk 级）**：240 字符（默认，可调整）

**重要**：Ingest 在页面级别使用 800 字符过滤，而质量闸门在 chunk 级别使用更低的阈值（默认 240），因为 chunk 通常比完整页面短。

修改方法：

1. **通过环境变量**（推荐）：
   ```bash
   export QUALITY_GATE_MIN_CHARS=1000
   ./scripts/run_auto_insurance_daily.sh
   ```

2. **在 daily 脚本中**：修改 `scripts/run_auto_insurance_daily.sh` 中的 ingest 和 quality gate 参数：
   ```bash
   # Ingest step
   --min-chars 1000
   
   # Quality gate step (uses $QUALITY_GATE_MIN_CHARS, default 800)
   export QUALITY_GATE_MIN_CHARS=1000
   ```

**快速检查**：
```bash
# 检查 ingest 和 quality gate 是否使用相同阈值
grep -E "min-chars|QUALITY_GATE_MIN_CHARS" scripts/run_auto_insurance_daily.sh
```

### 关键词匹配阈值

默认值：至少命中 2 个关键词（`MIN_KEYWORD_HITS = 2`）

修改方法：编辑 `pipelines/quality_gate_auto_insurance.py`，修改 `MIN_KEYWORD_HITS` 常量，或在脚本中传递 `--min-keyword-hits` 参数。

#### 关键词列表

**英文关键词**：
- insurance, auto, vehicle, liability, premium, coverage
- deductible, claim, policy, sr-22, dmv
- collision, comprehensive, bodily injury, property damage
- uninsured, underinsured, motorist, registration, license
- california, ca, minimum, requirement, mandatory, optional

**中文关键词**：
- 汽车保险, 车险, 理赔, 保单, 保费
- 责任险, 最低要求, sr-22
- 碰撞, 综合, 无保险, 未投保, 强制, 可选

## 输出文件

质量闸门会在 `results/auto_insurance/daily/YYYY-MM-DD/` 目录下生成：

1. **corpus_gated.jsonl**：通过质量闸门的文档（用于后续 embed 和 upsert）
2. **dropped.jsonl**：被过滤的文档（包含 `reason` 字段说明原因）
3. **run_summary.json**：质量闸门统计信息（JSON 格式）
4. **FILTER_REPORT.md**：详细的过滤报告（Markdown 格式）

### run_summary.json 结构

```json
{
  "timestamp": "2026-02-20T10:30:00Z",
  "quality_gate": {
    "total": 100,
    "passed": 85,
    "dropped": 15,
    "pass_rate": 85.0,
    "drop_reasons": {
      "domain_not_allowed": 2,
      "binary_url": 1,
      "text_too_short": 5,
      "not_insurance_related": 7
    }
  },
  "config": {
    "min_chars": 800,
    "min_keyword_hits": 2,
    "allow_domains": ["dmv.ca.gov", "insurance.ca.gov", ...]
  }
}
```

### FILTER_REPORT.md 内容

- 总文档数、通过数、丢弃数、通过率
- 按原因分类的丢弃统计
- 每个丢弃原因的样本文档（URL、标题、文本预览）

### dropped.jsonl 格式

每行一个 JSON 对象，包含原始文档字段 + `reason` 字段：

```json
{
  "id": "...",
  "title": "...",
  "text": "...",
  "source_url": "https://example.com/page.pdf",
  "reason": "binary_url"
}
```

常见 `reason` 值：
- `domain_not_allowed:example.com`：域名不在 allowlist
- `binary_url`：URL 指向二进制文件
- `text_too_short:450`：文本长度不足（数字为实际长度）
- `not_insurance_related`：关键词匹配不足

## 使用方法

### 手动运行质量闸门

```bash
cd ~/searchforge
source .env.cloudrun  # 如果需要

python3 pipelines/quality_gate_auto_insurance.py \
    --input results/auto_insurance/daily/2026-02-20/corpus_filtered.jsonl \
    --output-corpus results/auto_insurance/daily/2026-02-20/corpus_gated.jsonl \
    --output-dropped results/auto_insurance/daily/2026-02-20/dropped.jsonl \
    --report-dir results/auto_insurance/daily/2026-02-20 \
    --config results/auto_insurance/daily_targets.json \
    --min-chars 800
```

### 在 Daily Pipeline 中自动运行

质量闸门已集成到 `scripts/run_auto_insurance_daily.sh` 中，作为 Step 2.5 自动运行。

```bash
cd ~/searchforge
source .env.cloudrun
./scripts/run_auto_insurance_daily.sh
```

## 查看过滤结果

### 快速检查命令

```bash
# 1. 检查文档数量
wc -l results/auto_insurance/daily/*/corpus_filtered.jsonl
wc -l results/auto_insurance/daily/*/corpus_gated.jsonl

# 2. 查看过滤报告摘要
tail -n 20 results/auto_insurance/daily/*/FILTER_REPORT.md

# 3. 检查丢弃原因分布
grep -o '"reason":"[^"]*"' results/auto_insurance/daily/*/dropped.jsonl | sort | uniq -c
```

### 查看过滤报告

```bash
cat results/auto_insurance/daily/YYYY-MM-DD/FILTER_REPORT.md
```

### 查看丢弃的文档

```bash
# 查看前 10 条
head -n 10 results/auto_insurance/daily/YYYY-MM-DD/dropped.jsonl

# 查看特定原因的文档
grep "not_insurance_related" results/auto_insurance/daily/YYYY-MM-DD/dropped.jsonl | head -n 5
```

### 查看统计信息

```bash
cat results/auto_insurance/daily/YYYY-MM-DD/run_summary.json | jq '.quality_gate'
```

## 故障排查

### 问题：所有文档都被过滤了

可能原因：
1. Allowlist 配置错误：检查 `daily_targets.json` 中的 `allowed_domains`
2. 关键词阈值过高：降低 `MIN_KEYWORD_HITS` 或检查关键词列表
3. 最小字符数过高：降低 `--min-chars` 参数

### 问题：太多无关文档通过了

可能原因：
1. 关键词阈值过低：提高 `MIN_KEYWORD_HITS`
2. 关键词列表不完整：添加更多相关关键词
3. 最小字符数过低：提高 `--min-chars` 参数

### 问题：质量闸门脚本失败

检查：
1. 输入文件是否存在：`ls -la corpus_filtered.jsonl`
2. 配置文件格式是否正确：`cat daily_targets.json | jq`
3. Python 依赖是否安装：`pip list | grep -E "json|pathlib"`

## 集成到 Daily Pipeline

质量闸门在 Daily Pipeline 中的位置：

```
Step 1: Ingest/Crawl → corpus_raw.jsonl
Step 2: Diff Filter → corpus_filtered.jsonl
Step 2.5: Quality Gate → corpus_gated.jsonl + dropped.jsonl  ← 新增
Step 3: Embed and Upsert → 使用 corpus_gated.jsonl
Step 4: Evaluation
Step 5: Generate Daily Report
```

## 最佳实践

1. **定期审查 dropped.jsonl**：了解被过滤的内容类型，优化过滤规则
2. **监控通过率**：如果通过率异常低或高，调整阈值
3. **扩展关键词**：根据实际业务需求添加更多关键词
4. **保持 allowlist 更新**：只添加可信的域名
5. **版本控制配置**：将 `daily_targets.json` 纳入版本控制

## 相关文件

- `pipelines/quality_gate_auto_insurance.py`：质量闸门模块
- `scripts/run_auto_insurance_daily.sh`：Daily Pipeline 主脚本
- `results/auto_insurance/daily_targets.json`：配置文件（包含 allowlist）
- `docs/supporting/OPERATOR_PROMPT4.md`：Daily Pipeline 总体文档
