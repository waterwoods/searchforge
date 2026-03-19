# 南加州汽车保险 Broker RAG 数据源清单与抓取规范

## 1. 数据源清单（按优先级排序）

### 优先级 P0（核心官方与法规）

#### 1.1 加州 DMV 保险要求
- **name**: California DMV Insurance Requirements
- **base_url**: https://www.dmv.ca.gov
- **content_types**: 
  - `eligibility`: 最低保险要求、责任险标准
  - `compliance`: 合规检查、SR-22 要求
  - `faq`: 常见问题
- **expected_value**: 
  - 提供加州法定最低责任险要求（15/30/5）
  - SR-22 文件说明
  - 无保险驾驶处罚
  - 对 Broker 销售与合规咨询至关重要
- **crawl_difficulty**: `easy`
- **legal_note**: 
  - 公开政府信息，允许抓取
  - 遵守 robots.txt（通常允许）
  - 建议延迟 1-2 秒/请求

#### 1.2 加州保险局（CDI）
- **name**: California Department of Insurance
- **base_url**: https://www.insurance.ca.gov
- **content_types**:
  - `regulations`: 保险法规
  - `consumer_guides`: 消费者指南
  - `complaints`: 投诉流程
  - `licensing`: 经纪人执照要求
- **expected_value**:
  - 保险法规解释
  - 消费者权益保护
  - 投诉处理流程
- **crawl_difficulty**: `easy`
- **legal_note**: 政府公开信息，允许抓取

### 优先级 P1（主流保险公司官网）

#### 1.3 State Farm
- **name**: State Farm Auto Insurance
- **base_url**: https://www.statefarm.com
- **content_types**:
  - `coverage`: 保障类型说明（Liability/Collision/Comprehensive）
  - `claims`: 理赔流程、在线报案
  - `faq`: 常见问题
  - `rates`: 费率因素、折扣说明
  - `multi_lang`: 西语页面（espanol.statefarm.com）
- **expected_value**:
  - 保障差异对比（全险 vs 责任险）
  - 理赔步骤详解
  - 折扣项目（好司机、多车、学生）
  - 西语客户支持
- **crawl_difficulty**: `medium`
- **legal_note**: 
  - 检查 robots.txt
  - 避免抓取个人账户页面
  - 仅抓取公开帮助中心/FAQ

#### 1.4 GEICO
- **name**: GEICO Auto Insurance
- **base_url**: https://www.geico.com
- **content_types**:
  - `coverage`: 保障选项、免赔额说明
  - `claims`: 理赔中心、24/7 报案
  - `faq`: 常见问题库
  - `multi_lang`: 西语支持
- **expected_value**:
  - 在线报价流程
  - 保障类型对比
  - 理赔时间线
  - 移动应用功能
- **crawl_difficulty**: `medium`
- **legal_note**: 遵守 robots.txt，仅公开内容

#### 1.5 Progressive
- **name**: Progressive Auto Insurance
- **base_url**: https://www.progressive.com
- **content_types**:
  - `coverage`: 保障选项、附加险
  - `claims`: 理赔流程、快照程序
  - `faq`: 常见问题
  - `tools`: 报价工具说明
- **expected_value**:
  - 快照（Snapshot）程序说明
  - 保障套餐对比
  - 理赔在线跟踪
- **crawl_difficulty**: `medium`
- **legal_note**: 遵守 robots.txt

#### 1.6 Allstate
- **name**: Allstate Auto Insurance
- **base_url**: https://www.allstate.com
- **content_types**:
  - `coverage`: 保障类型、免赔额
  - `claims`: 理赔流程、快速理赔
  - `faq`: 常见问题
  - `multi_lang`: 西语支持
- **expected_value**:
  - 保障差异说明
  - 理赔时间承诺
  - 折扣项目
- **crawl_difficulty**: `medium`
- **legal_note**: 遵守 robots.txt

#### 1.7 Farmers Insurance
- **name**: Farmers Auto Insurance
- **base_url**: https://www.farmers.com
- **content_types**:
  - `coverage`: 保障选项
  - `claims`: 理赔流程
  - `faq`: 常见问题
- **expected_value**:
  - 保障类型说明
  - 理赔流程
- **crawl_difficulty**: `medium`
- **legal_note**: 遵守 robots.txt

#### 1.8 Nationwide
- **name**: Nationwide Auto Insurance
- **base_url**: https://www.nationwide.com
- **content_types**:
  - `coverage`: 保障选项、免赔额说明
  - `claims`: 理赔流程、在线报案
  - `faq`: 常见问题
  - `multi_lang`: 多语言支持页面
- **expected_value**:
  - 保障类型说明与对比
  - 理赔流程详解
  - 折扣项目说明
  - 多语言客户支持
- **crawl_difficulty**: `medium`
- **legal_note**: 遵守 robots.txt，仅抓取公开帮助中心/FAQ

#### 1.9 USAA（如适用）
- **name**: USAA Auto Insurance
- **base_url**: https://www.usaa.com
- **content_types**:
  - `coverage`: 保障选项
  - `claims`: 理赔流程
  - `eligibility`: 会员资格要求
- **expected_value**:
  - 军人/退伍军人专属信息
  - 保障说明
- **crawl_difficulty**: `hard`（部分内容需登录）
- **legal_note**: 仅抓取公开页面

### 优先级 P2（专业对比与指南）

#### 1.10 NerdWallet 保险对比
- **name**: NerdWallet Auto Insurance Guide
- **base_url**: https://www.nerdwallet.com
- **content_types**:
  - `comparison`: 保险公司对比
  - `guides`: 购买指南
  - `faq`: 常见问题
- **expected_value**:
  - 多公司对比
  - 购买建议
  - 费率因素解释
- **crawl_difficulty**: `easy`
- **legal_note**: 遵守 robots.txt

#### 1.11 ValuePenguin 保险指南
- **name**: ValuePenguin Auto Insurance
- **base_url**: https://www.valuepenguin.com
- **content_types**:
  - `comparison`: 对比分析
  - `guides`: 购买指南
  - `rates`: 费率分析
- **expected_value**:
  - 保障类型对比
  - 费率因素
  - 省钱技巧
- **crawl_difficulty**: `easy`
- **legal_note**: 遵守 robots.txt

#### 1.12 The Zebra 保险对比
- **name**: The Zebra Auto Insurance
- **base_url**: https://www.thezebra.com
- **content_types**:
  - `comparison`: 对比工具
  - `guides`: 购买指南
  - `faq`: 常见问题
- **expected_value**:
  - 实时报价对比
  - 保障解释
- **crawl_difficulty**: `easy`
- **legal_note**: 遵守 robots.txt

### 优先级 P2.5（多语言支持 - 中文优先）

#### 1.13 加州保险局（CDI）消费者中文信息页
- **name**: California Department of Insurance - Chinese Consumer Information
- **base_url**: https://www.insurance.ca.gov
- **content_types**:
  - `guides`: 中文消费者指南
  - `faq`: 中文常见问题
  - `regulations`: 中文法规说明
- **expected_value**:
  - 服务中文客户（加州重要群体）
  - 保险基本概念中文解释
  - 消费者权益保护中文说明
  - 投诉流程中文指南
- **crawl_difficulty**: `easy`
- **legal_note**: 政府公开信息，允许抓取。遵守 robots.txt
- **note**: 占位数据源，后续 Prompt 2 实现抓取

#### 1.14 加州 DMV 车辆/保险相关中文说明页
- **name**: California DMV - Chinese Vehicle/Insurance Information
- **base_url**: https://www.dmv.ca.gov
- **content_types**:
  - `eligibility`: 中文保险要求说明
  - `compliance`: 中文合规指南
  - `faq`: 中文常见问题
- **expected_value**:
  - 最低保险要求中文解释
  - SR-22 文件中文说明
  - 车辆注册保险要求中文指南
- **crawl_difficulty**: `easy`
- **legal_note**: 公开政府信息，允许抓取。遵守 robots.txt
- **note**: 占位数据源，后续 Prompt 2 实现抓取

#### 1.15 主流保险公司官网中文/Language Assistance 页面
- **name**: Major Insurers - Chinese Language Assistance Pages
- **base_url**: 
  - https://www.nationwide.com (Language Assistance / 中文)
  - https://www.statefarm.com (中文支持页面)
  - https://www.geico.com (Language Assistance / 中文)
- **content_types**:
  - `multi_lang`: 中文帮助页面
  - `guides`: 中文购买指南
  - `faq`: 中文常见问题
  - `claims`: 中文理赔指南
- **expected_value**:
  - 服务中文客户
  - 保险产品中文说明
  - 理赔流程中文指南
  - 多语言客户支持信息
- **crawl_difficulty**: `medium`
- **legal_note**: 遵守 robots.txt，仅抓取公开帮助页面
- **note**: 占位数据源，后续 Prompt 2 实现抓取。包含 Nationwide 及 1-2 家其他主流保险公司示例

### 优先级 P3（多语言支持 - 西语）

#### 1.16 西语保险资源
- **name**: Chinese Auto Insurance Guides
- **base_url**: 
  - https://www.nerdwallet.com/article/insurance/chinese
  - https://www.insurance.ca.gov (中文页面)
- **content_types**:
  - `guides`: 中文购买指南
  - `faq`: 中文常见问题
- **expected_value**:
  - 服务中文客户
  - 基本保险概念解释
- **crawl_difficulty**: `easy`
- **legal_note**: 遵守 robots.txt

#### 1.16 西语保险资源
- **name**: Spanish Auto Insurance Resources
- **base_url**:
  - https://www.insurance.ca.gov/01-consumers/spanish/
  - 各保险公司西语页面
- **content_types**:
  - `guides`: 西语指南
  - `faq`: 西语常见问题
- **expected_value**:
  - 服务西语客户（加州重要群体）
  - 基本概念解释
- **crawl_difficulty**: `easy`
- **legal_note**: 遵守 robots.txt

### 优先级 P4（补充资源）

#### 1.17 Insurance.com 对比工具
- **name**: Insurance.com
- **base_url**: https://www.insurance.com
- **content_types**:
  - `comparison`: 对比工具
  - `guides`: 购买指南
- **expected_value**:
  - 补充对比信息
- **crawl_difficulty**: `easy`
- **legal_note**: 遵守 robots.txt

#### 1.18 Bankrate 保险指南
- **name**: Bankrate Auto Insurance
- **base_url**: https://www.bankrate.com/insurance
- **content_types**:
  - `guides`: 购买指南
  - `rates`: 费率分析
- **expected_value**:
  - 补充指南信息
- **crawl_difficulty**: `easy`
- **legal_note**: 遵守 robots.txt

---

## 2. 统一抓取规范

### 2.1 目标字段定义

每个抓取的文档应包含以下字段：

```json
{
  "title": "文档标题（H1 或 <title> 标签）",
  "main_text": "清洗后的主要内容（纯文本）",
  "source_url": "原始 URL（完整路径）",
  "language": "语言代码（en/es/zh）",
  "last_updated": "最后更新时间（ISO 8601 格式，如 2024-01-15T10:30:00Z）",
  "content_type": "内容类型（faq/coverage/claims/eligibility/rates/comparison）",
  "metadata": {
    "site_name": "站点名称",
    "section": "页面所属部分（如 help/faq/claims）",
    "word_count": 字数统计,
    "chunk_index": "如果是分块，记录块索引",
    "parent_url": "如果是分块，记录父页面 URL"
  }
}
```

### 2.2 清洗规则

#### 2.2.1 必须移除的内容
- 导航栏（`<nav>`、`<header>` 中的导航链接）
- 页脚（`<footer>`、版权信息、链接列表）
- 广告内容（`<div class="ad">`、`<aside>` 中的广告）
- Cookie 横幅（`<div class="cookie-banner">`）
- 社交媒体分享按钮（仅移除按钮，保留分享链接文本）
- 评论区域（`<div class="comments">`）
- 相关推荐（`<div class="related">`、`<div class="recommended">`）
- JavaScript 代码块（`<script>` 标签）
- 样式表（`<style>` 标签）
- 隐藏元素（`display: none`、`visibility: hidden`）

#### 2.2.2 保留的内容
- 主标题（`<h1>`、`<h2>`、`<h3>`）
- 正文段落（`<p>`）
- 列表（`<ul>`、`<ol>`、`<li>`）
- 表格（`<table>`，转换为文本格式）
- 重要链接文本（保留链接文本，移除 `<a>` 标签）
- 强调文本（`<strong>`、`<em>`，保留文本）

#### 2.2.3 文本清洗步骤
1. **HTML 解析**: 使用 BeautifulSoup 或类似工具解析 HTML
2. **选择主内容区域**: 
   - 优先选择 `<main>`、`<article>`、`<div class="content">` 等
   - 如无明确标记，选择最大文本块
3. **移除指定元素**: 按 2.2.1 规则移除
4. **提取文本**: 转换为纯文本，保留段落分隔
5. **清理空白**: 
   - 合并多个连续空格为单个空格
   - 移除行首行尾空白
   - 保留段落间的单个换行
6. **语言检测**: 使用 `langdetect` 或类似库检测语言
7. **时间提取**: 
   - 优先从 `<meta property="article:modified_time">` 提取
   - 其次从页面文本中提取日期（如 "Last updated: 2024-01-15"）
   - 如无，使用抓取时间

### 2.3 切块策略

#### 2.3.1 基础切块规则
- **目标块大小**: 300-800 字符（中文字符按 2 字符计算）
- **重叠策略**: 相邻块之间重叠 50-100 字符，确保语义连续性
- **切分点优先级**:
  1. 段落边界（`<p>` 标签）
  2. 标题边界（`<h1>`-`<h6>`）
  3. 列表项边界（`<li>`）
  4. 句子边界（句号、问号、感叹号）
  5. 逗号（仅在必要时）

#### 2.3.2 语义切块（高级）
- 使用句子嵌入模型（如 `sentence-transformers`）计算语义相似度
- 当相邻句子语义相似度 > 0.85 时，优先保持在同一块
- 当语义相似度 < 0.5 时，强制切分
- 确保每个块包含完整的语义单元（如一个问答对、一个概念解释）

#### 2.3.3 特殊内容处理
- **FAQ 页面**: 每个 Q&A 对作为一个独立块
- **表格**: 转换为文本后，按行切分或整体保留
- **列表**: 每个列表项可作为独立块，或合并为一个大块
- **代码块**: 如包含代码示例，整体保留为一个块

### 2.4 去重策略

#### 2.4.1 文档级去重
- **方法**: 使用内容哈希（MD5 或 SHA256）
- **计算**: `hash(title + main_text[:500])`
- **存储**: 维护已抓取文档的哈希集合
- **判断**: 如哈希已存在，跳过该文档

#### 2.4.2 块级去重
- **方法**: 使用块内容哈希
- **计算**: `hash(chunk_text)`
- **判断**: 如块哈希已存在，跳过该块
- **阈值**: 相似度 > 95% 视为重复

#### 2.4.3 URL 去重
- 维护已访问 URL 集合
- 规范化 URL（移除查询参数、锚点、尾部斜杠）
- 如 URL 已访问，跳过

### 2.5 输出格式

#### 2.5.1 JSONL 格式
每行一个 JSON 对象，符合以下结构：

```json
{
  "id": "唯一标识符（UUID 或 hash）",
  "title": "文档标题",
  "text": "块文本内容",
  "source_url": "原始 URL",
  "language": "en",
  "last_updated": "2024-01-15T10:30:00Z",
  "content_type": "faq",
  "metadata": {
    "site_name": "State Farm",
    "section": "help/faq",
    "word_count": 450,
    "chunk_index": 0,
    "parent_url": "https://www.statefarm.com/help/faq"
  },
  "embedding_ready": true
}
```

#### 2.5.2 文件命名规范
- 格式: `{site_name}_{content_type}_{date}.jsonl`
- 示例: `statefarm_faq_20240115.jsonl`
- 日期格式: `YYYYMMDD`

#### 2.5.3 目录结构
```
data/
  raw/
    statefarm/
      statefarm_faq_20240115.jsonl
      statefarm_coverage_20240115.jsonl
    geico/
      geico_claims_20240115.jsonl
  processed/
    chunks/
      all_chunks_20240115.jsonl
  metadata/
    crawl_log_20240115.json
    deduplication_hashes.json
```

---

## 3. 最小可跑样本计划（48 小时）

### 3.1 目标站点选择（3-5 个）

#### 阶段 1（24 小时）: 核心官方 + 1 个保险公司
1. **加州 DMV** (P0)
   - 目标: 50-100 条文档
   - 重点: 最低保险要求、SR-22、合规信息
2. **加州保险局（CDI）** (P0)
   - 目标: 50-100 条文档
   - 重点: 法规、消费者指南
3. **State Farm** (P1)
   - 目标: 200-300 条文档
   - 重点: FAQ、保障说明、理赔流程

#### 阶段 2（24 小时）: 补充 2 个保险公司
4. **GEICO** (P1)
   - 目标: 200-300 条文档
   - 重点: FAQ、保障对比、理赔指南
5. **Progressive** (P1)
   - 目标: 200-300 条文档
   - 重点: 保障选项、理赔流程

### 3.2 目标文档数量
- **总计**: 500-2,000 条高质量文档
- **分布**:
  - 官方资源: 100-200 条
  - 保险公司 FAQ: 400-800 条
  - 保障说明: 200-400 条
  - 理赔指南: 200-400 条
  - 其他: 100-200 条

### 3.3 评估问题设计

#### 问题 1: 最低责任险要求
- **问题**: "加州法律要求的最低汽车责任险保额是多少？"
- **预期答案**: "15/30/5 - 即人身伤害每人最低 $15,000，每次事故 $30,000，财产损失 $5,000"
- **评估标准**: 
  - 准确度: 是否包含具体数字
  - 完整性: 是否解释三个数字含义

#### 问题 2: 保障类型差异
- **问题**: "碰撞险（Collision）和全险（Comprehensive）有什么区别？"
- **预期答案**: 应包含两者覆盖范围、适用场景、价格差异
- **评估标准**:
  - 准确性: 定义是否正确
  - 对比性: 是否清晰对比

#### 问题 3: 理赔流程
- **问题**: "发生车祸后，我应该如何申请理赔？"
- **预期答案**: 应包含报案步骤、所需文件、时间线
- **评估标准**:
  - 步骤完整性: 是否包含所有关键步骤
  - 实用性: 是否包含具体操作指导

#### 问题 4: SR-22 要求
- **问题**: "什么是 SR-22 文件？谁需要它？"
- **预期答案**: 应解释 SR-22 定义、适用人群、获取方式
- **评估标准**:
  - 定义准确性
  - 适用场景说明

#### 问题 5: 费率因素
- **问题**: "哪些因素会影响我的汽车保险费率？"
- **预期答案**: 应包含驾驶记录、车型、年龄、地点等因素
- **评估标准**:
  - 因素完整性: 是否涵盖主要因素
  - 解释清晰度

### 3.4 48 小时执行时间表

#### Day 1 (0-24 小时)
- **0-4h**: 环境搭建、爬虫框架准备
- **4-8h**: 抓取加州 DMV + CDI（100-200 条）
- **8-12h**: 抓取 State Farm FAQ/保障页面（200-300 条）
- **12-16h**: 数据清洗与切块
- **16-20h**: 去重与质量检查
- **20-24h**: 生成 JSONL 文件，初步验证

#### Day 2 (24-48 小时)
- **24-28h**: 抓取 GEICO（200-300 条）
- **28-32h**: 抓取 Progressive（200-300 条）
- **32-36h**: 数据清洗与切块
- **36-40h**: 合并所有数据，最终去重
- **40-44h**: 使用 5 个评估问题测试检索效果
- **44-48h**: 生成报告，准备 Prompt 2 输入

---

## 4. Prompt 2 输入契约

### 4.1 必需参数

#### 4.1.1 URL 列表文件
- **格式**: JSON 或 CSV
- **字段**:
  ```json
  {
    "urls": [
      {
        "url": "https://www.dmv.ca.gov/portal/vehicle-registration/insurance-requirements/",
        "site_name": "California DMV",
        "content_type": "eligibility",
        "priority": "P0",
        "expected_sections": ["minimum_requirements", "sr22", "compliance"]
      }
    ]
  }
  ```

#### 4.1.2 字段规范文件
- **格式**: JSON Schema
- **内容**: 定义输出字段结构（见 2.1 节）

#### 4.1.3 切块规则配置
- **格式**: JSON
- **内容**:
  ```json
  {
    "chunking": {
      "min_chunk_size": 300,
      "max_chunk_size": 800,
      "overlap_size": 50,
      "use_semantic_chunking": true,
      "semantic_threshold": 0.85,
      "split_on": ["paragraph", "heading", "sentence"]
    }
  }
  ```

#### 4.1.4 清洗规则配置
- **格式**: JSON
- **内容**:
  ```json
  {
    "cleaning": {
      "remove_selectors": [
        "nav",
        "footer",
        ".ad",
        ".cookie-banner",
        ".comments",
        ".related"
      ],
      "keep_selectors": [
        "main",
        "article",
        ".content",
        "h1, h2, h3",
        "p",
        "ul, ol, li"
      ],
      "text_cleaning": {
        "normalize_whitespace": true,
        "remove_empty_lines": true,
        "preserve_paragraphs": true
      }
    }
  }
  ```

#### 4.1.5 去重配置
- **格式**: JSON
- **内容**:
  ```json
  {
    "deduplication": {
      "method": "hash",
      "hash_algorithm": "md5",
      "document_hash_fields": ["title", "main_text"],
      "chunk_hash_fields": ["text"],
      "similarity_threshold": 0.95
    }
  }
  ```

### 4.2 可选参数

#### 4.2.1 抓取限制
- **格式**: JSON
- **内容**:
  ```json
  {
    "limits": {
      "max_pages_per_site": 500,
      "max_depth": 3,
      "delay_between_requests": 2,
      "timeout": 30,
      "max_retries": 3
    }
  }
  ```

#### 4.2.2 语言检测配置
- **格式**: JSON
- **内容**:
  ```json
  {
    "language_detection": {
      "enabled": true,
      "default_language": "en",
      "supported_languages": ["en", "es", "zh"],
      "min_confidence": 0.8
    }
  }
  ```

#### 4.2.3 输出配置
- **格式**: JSON
- **内容**:
  ```json
  {
    "output": {
      "format": "jsonl",
      "output_dir": "data/raw",
      "file_naming": "{site_name}_{content_type}_{date}.jsonl",
      "include_metadata": true,
      "compress": false
    }
  }
  ```

### 4.3 Prompt 2 输入文件结构

```
prompt2_input/
  urls.json                    # URL 列表
  field_schema.json           # 字段规范
  chunking_config.json        # 切块规则
  cleaning_config.json        # 清洗规则
  deduplication_config.json  # 去重配置
  crawl_limits.json          # 抓取限制（可选）
  language_config.json       # 语言检测（可选）
  output_config.json         # 输出配置（可选）
  README.md                  # 说明文档
```

### 4.4 Prompt 2 任务描述

**任务**: 基于提供的配置，实现一个自动化的网页抓取、清洗、切块与去重系统。

**要求**:
1. 读取 `urls.json`，按优先级抓取网页
2. 应用 `cleaning_config.json` 规则清洗内容
3. 应用 `chunking_config.json` 规则切分文本
4. 应用 `deduplication_config.json` 规则去重
5. 按照 `field_schema.json` 输出结构化数据
6. 生成抓取日志与统计报告

**输出**:
- JSONL 文件（按 `output_config.json` 配置）
- 抓取日志（成功/失败记录）
- 统计报告（文档数、块数、去重统计）

---

## 5. 数据源清单 JSON 格式

完整的数据源清单 JSON 文件：

```json
{
  "version": "1.0",
  "created_at": "2024-01-15T00:00:00Z",
  "data_sources": [
    {
      "id": "ds_001",
      "name": "California DMV Insurance Requirements",
      "base_url": "https://www.dmv.ca.gov",
      "priority": "P0",
      "content_types": ["eligibility", "compliance", "faq"],
      "expected_value": "提供加州法定最低责任险要求、SR-22文件说明、无保险驾驶处罚",
      "crawl_difficulty": "easy",
      "legal_note": "公开政府信息，允许抓取。遵守robots.txt，建议延迟1-2秒/请求",
      "target_urls": [
        "https://www.dmv.ca.gov/portal/vehicle-registration/insurance-requirements/",
        "https://www.dmv.ca.gov/portal/driver-education/insurance/"
      ],
      "estimated_documents": 50
    }
    // ... 其他数据源
  ]
}
```

---

## 6. 验收检查清单

- [ ] 数据源清单包含 10-15 个高价值来源
- [ ] 每个数据源包含所有必需字段（name, base_url, content_types, expected_value, crawl_difficulty, legal_note）
- [ ] 抓取规范明确定义目标字段、清洗规则、切块策略、去重策略
- [ ] 输出格式为 JSONL，便于嵌入 Qdrant
- [ ] MVP 计划包含 3-5 个站点，目标 500-2,000 条文档
- [ ] 定义了 5 个评估问题
- [ ] Prompt 2 输入契约包含所有必需参数
- [ ] 文档结构清晰，可直接交给 OpenClaw 执行

---

## 7. 后续步骤

1. **审查与确认**: 审查本清单，确认数据源优先级与抓取规范
2. **执行 Prompt 2**: 使用本规范生成爬虫脚本
3. **48 小时 MVP**: 执行最小可跑样本计划
4. **评估与迭代**: 使用 5 个评估问题测试检索效果
5. **扩展抓取**: 基于 MVP 结果，扩展到全部 15 个数据源
6. **质量监控**: 建立持续抓取与质量监控机制
