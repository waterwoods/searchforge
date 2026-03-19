# Prompt 2 输入文件说明

本目录包含 Prompt 2（爬虫实现）所需的所有配置文件和输入数据。

## 文件清单

### 核心配置文件

1. **data_sources.json**
   - 数据源清单（16个高价值来源）
   - 包含 URL、优先级、内容类型等信息
   - MVP 阶段使用 `mvp_sources` 字段中的 5 个数据源
   - **新增**: P2.5 优先级中文数据源（占位，后续 Prompt 2 实现抓取）

2. **field_schema.json**
   - 输出字段规范（JSON Schema）
   - 定义每个文档块必须包含的字段
   - 用于验证输出数据格式

3. **chunking_config.json**
   - 文本切块策略配置
   - 包含大小限制、重叠策略、语义切块参数
   - 特殊内容处理规则（FAQ、表格、列表等）

4. **cleaning_config.json**
   - HTML 清洗规则
   - 定义需要移除和保留的 HTML 元素
   - 文本清理步骤

5. **deduplication_config.json**
   - 去重策略配置
   - URL、文档、块三级去重
   - 哈希算法和相似度阈值

### 可选配置文件

6. **crawl_limits.json**
   - 抓取限制和速率控制
   - 并发数、延迟、重试策略
   - User-Agent 轮换

7. **language_config.json**
   - 语言检测配置
   - 支持的语言列表
   - 语言检测回退策略

8. **output_config.json**
   - 输出格式和目录结构
   - 文件命名规则
   - 日志和统计配置

### 评估文件

9. **evaluation_questions.json**
   - 5 个评估问题
   - 预期答案关键词
   - 评估标准

## 使用方法

### 步骤 1: 读取配置

```python
import json

# 读取数据源清单
with open('data_sources.json', 'r', encoding='utf-8') as f:
    data_sources = json.load(f)

# 读取字段规范
with open('field_schema.json', 'r', encoding='utf-8') as f:
    field_schema = json.load(f)

# 读取其他配置...
```

### 步骤 2: MVP 阶段（48小时）

使用 `data_sources.json` 中的 `mvp_sources` 字段：

```python
mvp_source_ids = data_sources['mvp_sources']
# ['ds_001', 'ds_002', 'ds_003', 'ds_004', 'ds_005']

mvp_sources = [
    ds for ds in data_sources['data_sources'] 
    if ds['id'] in mvp_source_ids
]
```

### 步骤 3: 执行抓取

按照配置文件的规则执行：
1. 遍历数据源 URL 列表
2. 应用清洗规则
3. 应用切块策略
4. 执行去重
5. 输出 JSONL 文件

### 步骤 4: 验证输出

使用 `field_schema.json` 验证输出格式：

```python
import jsonschema

# 验证每个文档块
jsonschema.validate(instance=document_chunk, schema=field_schema)
```

### 步骤 5: 评估检索效果

使用 `evaluation_questions.json` 中的问题测试 RAG 系统：

```python
with open('evaluation_questions.json', 'r', encoding='utf-8') as f:
    eval_questions = json.load(f)

for question in eval_questions['questions']:
    # 执行检索和问答
    results = rag_system.query(question['question'])
    # 评估结果...
```

## 输出目录结构

```
data/
  raw/
    california-dmv/
      california-dmv_eligibility_20240115.jsonl
    statefarm/
      statefarm_faq_20240115.jsonl
      statefarm_coverage_20240115.jsonl
  processed/
    chunks/
      all_chunks_20240115.jsonl
  metadata/
    crawl_log_20240115.json
    crawl_stats_20240115.json
    deduplication_hashes.json
```

## 注意事项

1. **遵守 robots.txt**: 所有抓取必须遵守目标网站的 robots.txt
2. **速率控制**: 使用 `crawl_limits.json` 中的延迟设置，避免被封
3. **数据质量**: 确保清洗后的文本质量高，去除导航、广告等无关内容
4. **去重**: 严格执行去重策略，避免重复数据
5. **语言检测**: 正确识别文档语言，特别是多语言站点
6. **中文数据源**: P2.5 优先级的中文数据源为占位数据源，需要在 Prompt 2 中实现具体抓取逻辑
7. **多语言 RAG**: 中文数据源将用于构建多语言 RAG 系统，提升对中文客户的服务能力
8. **错误处理**: 实现完善的错误处理和重试机制
9. **日志记录**: 记录所有抓取活动，便于调试和审计

## 下一步

完成 Prompt 2 后，将生成：
- 爬虫脚本（Python）
- 清洗和切块脚本
- 去重脚本
- 输出 JSONL 文件
- 抓取日志和统计报告

这些输出将用于后续的嵌入生成和向量数据库导入。
