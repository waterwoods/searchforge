# Prompt 1 补丁版 - Diff 总结

## 📋 变更概览

本次补丁在现有数据源规范不变的前提下，补充了两个关键数据源类别：

1. ✅ 将 **Nationwide** 加入 P1 主流保险公司分组
2. ✅ 新增 **P2.5 多语言（中文优先）** 分组，包含 3 个中文数据源

---

## 🆕 新增数据源详情

### 1. P1 分组新增：Nationwide

**数据源 ID**: `ds_007a`  
**优先级**: P1（主流保险公司）  
**名称**: Nationwide Auto Insurance  
**基础 URL**: https://www.nationwide.com

**字段信息**:
- **content_types**: coverage, claims, faq, multi_lang
- **expected_value**: 保障类型说明与对比、理赔流程详解、折扣项目说明、多语言客户支持
- **crawl_difficulty**: medium
- **legal_note**: 遵守robots.txt，仅抓取公开帮助中心/FAQ
- **estimated_documents**: 250
- **language**: en

**目标 URL**:
- https://www.nationwide.com/personal/insurance/auto/
- https://www.nationwide.com/personal/insurance/auto/coverage/
- https://www.nationwide.com/personal/insurance/auto/claims/
- https://www.nationwide.com/help/

---

### 2. P2.5 分组新增：中文数据源（3个）

#### 2.1 加州保险局（CDI）消费者中文信息页

**数据源 ID**: `ds_011`  
**优先级**: P2.5（多语言支持 - 中文优先）  
**名称**: California Department of Insurance - Chinese Consumer Information  
**基础 URL**: https://www.insurance.ca.gov

**字段信息**:
- **content_types**: guides, faq, regulations
- **expected_value**: 服务中文客户（加州重要群体）、保险基本概念中文解释、消费者权益保护中文说明、投诉流程中文指南
- **crawl_difficulty**: easy
- **legal_note**: 政府公开信息，允许抓取。遵守robots.txt
- **estimated_documents**: 100
- **language**: zh
- **note**: 占位数据源，后续 Prompt 2 实现抓取

**目标 URL**:
- https://www.insurance.ca.gov/01-consumers/chinese/

---

#### 2.2 加州 DMV 车辆/保险相关中文说明页

**数据源 ID**: `ds_012`  
**优先级**: P2.5（多语言支持 - 中文优先）  
**名称**: California DMV - Chinese Vehicle/Insurance Information  
**基础 URL**: https://www.dmv.ca.gov

**字段信息**:
- **content_types**: eligibility, compliance, faq
- **expected_value**: 最低保险要求中文解释、SR-22文件中文说明、车辆注册保险要求中文指南
- **crawl_difficulty**: easy
- **legal_note**: 公开政府信息，允许抓取。遵守robots.txt
- **estimated_documents**: 50
- **language**: zh
- **note**: 占位数据源，后续 Prompt 2 实现抓取

**目标 URL**:
- https://www.dmv.ca.gov/portal/chinese/

---

#### 2.3 主流保险公司官网中文/Language Assistance 页面

**数据源 ID**: `ds_013`  
**优先级**: P2.5（多语言支持 - 中文优先）  
**名称**: Major Insurers - Chinese Language Assistance Pages  
**基础 URL**: https://www.nationwide.com（主要），包含其他保险公司

**字段信息**:
- **content_types**: multi_lang, guides, faq, claims
- **expected_value**: 服务中文客户、保险产品中文说明、理赔流程中文指南、多语言客户支持信息
- **crawl_difficulty**: medium
- **legal_note**: 遵守robots.txt，仅抓取公开帮助页面
- **estimated_documents**: 150
- **language**: zh
- **note**: 占位数据源，后续 Prompt 2 实现抓取。包含 Nationwide 及 1-2 家其他主流保险公司示例

**目标 URL**:
- https://www.nationwide.com/help/language-assistance/
- https://www.statefarm.com/help/language-assistance
- https://www.geico.com/help/language-assistance/

---

## 📊 数据源统计变化

### 变更前
- **总数据源数**: 13 个
- **P1 分组**: 5 个（State Farm, GEICO, Progressive, Allstate, Farmers）
- **多语言支持**: P3 分组（西语资源）

### 变更后
- **总数据源数**: 16 个（+3）
- **P1 分组**: 6 个（+1，新增 Nationwide）
- **P2.5 分组**: 3 个（新增，中文优先）
- **多语言支持**: P2.5（中文）+ P3（西语）

---

## 📝 文档更新清单

### 1. `docs/auto_insurance_data_sources.md`
- ✅ 在 P1 分组中添加 Nationwide（1.8）
- ✅ 新增 P2.5 分组（1.13-1.15）
- ✅ 更新后续编号（1.9-1.18）

### 2. `docs/prompt2_input/data_sources.json`
- ✅ 添加 `ds_007a`（Nationwide）
- ✅ 添加 `ds_011`（CDI 中文）
- ✅ 添加 `ds_012`（DMV 中文）
- ✅ 添加 `ds_013`（保险公司中文）
- ✅ 更新后续 ID 编号
- ✅ 添加 `total_sources: 16`

### 3. `docs/auto_insurance_rag_summary.md`
- ✅ 更新数据源清单（13 → 16 个）
- ✅ 添加 P2.5 分组说明
- ✅ 添加"中文用户支持"章节
- ✅ 更新语言分布说明

### 4. `docs/prompt2_input/README.md`
- ✅ 更新数据源数量说明（13 → 16）
- ✅ 添加中文数据源说明
- ✅ 添加多语言 RAG 说明

---

## 🎯 关键变更点

### 1. 新增优先级分组：P2.5
- **定位**: 多语言支持 - 中文优先
- **目的**: 专门服务中文客户，提升 RAG 系统对中文社区的服务能力
- **特点**: 所有数据源均为占位，需在 Prompt 2 中实现抓取

### 2. Nationwide 加入 P1
- **原因**: Nationwide 是主流保险公司之一，提供完整的多语言支持
- **价值**: 补充主流保险公司覆盖，增强数据源多样性

### 3. 中文数据源覆盖
- **官方资源**: CDI、DMV 中文页面
- **商业资源**: 主流保险公司中文支持页面
- **预期价值**: 帮助 Broker 更好地服务加州中文社区

---

## ✅ 验收检查

- [x] Nationwide 已加入 P1 分组，字段结构完整
- [x] P2.5 分组已创建，包含 3 个中文数据源
- [x] 所有数据源字段结构一致（name, base_url, content_types, expected_value, crawl_difficulty, legal_note）
- [x] 占位数据源已标注 `note` 字段
- [x] `auto_insurance_rag_summary.md` 已更新"中文用户支持"说明
- [x] `prompt2_input/README.md` 已说明中文数据源用于多语言 RAG
- [x] JSON 文件格式验证通过
- [x] 所有文档编号已更新

---

## 🚀 下一步行动

1. **Prompt 2 实现**: 在爬虫系统中实现 P2.5 中文数据源的抓取逻辑
2. **URL 验证**: 验证所有中文数据源的 URL 是否可访问
3. **语言检测**: 确保语言检测配置正确识别中文内容
4. **测试抓取**: 对中文数据源进行小规模测试抓取
5. **质量评估**: 评估中文内容的质量和对 Broker 业务的价值

---

## 📈 预期影响

### 数据量增长
- **新增文档数**: 约 300 条（Nationwide: 250 + 中文数据源: 300）
- **总文档数**: 从 2,000-5,000 条 → 2,300-5,300 条

### 语言分布优化
- **中文占比**: 从 5-10% → 8-15%
- **多语言覆盖**: 英语 + 西语 + 中文（三语支持）

### 业务价值提升
- **中文客户服务**: 显著提升对中文客户的服务能力
- **合规支持**: 中文法规和指南帮助 Broker 更好地服务中文社区
- **竞争优势**: 多语言 RAG 系统提供差异化竞争优势

---

**补丁完成时间**: 2024-02-19  
**版本**: Prompt 1 v1.1（补丁版）
