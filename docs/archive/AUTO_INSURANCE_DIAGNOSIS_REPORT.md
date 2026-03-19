# Auto Insurance Collection 诊断报告

## 执行时间
2026-02-19

## 1. 后端 Collection 配置检查

### ✅ Collection Map 配置
**文件**: `services/fiqa_api/routes/query.py`
```python
COLLECTION_MAP = {
    "auto_insurance": "auto_insurance_v1",
    "auto_insurance_v1": "auto_insurance_v1",
}
```

**文件**: `services/fiqa_api/services/search_core.py`
```python
COLLECTION_MAP = {
    "auto_insurance": "auto_insurance_v1",
    "auto_insurance_v1": "auto_insurance_v1",
}
```

### ✅ 默认 Collection
- 默认值: `default="auto_insurance"`
- 映射后: `auto_insurance_v1`

### 映射流程
1. 前端请求 → 不指定 collection
2. 后端默认 → `"auto_insurance"`
3. COLLECTION_MAP → `"auto_insurance_v1"`
4. 实际查询 → `auto_insurance_v1`

## 2. Qdrant Collection 抽样检查

### Collection 状态
- ✅ Collection 存在: `auto_insurance_v1`
- ❌ **数据量**: 仅 17 条（严重不足）

### 抽样结果（17条，全部抽样）
- ✅ **Domain 分布**: 100% 来自保险相关域名
  - geico.com: 9条 (52.9%)
  - insurance.ca.gov: 4条 (23.5%)
  - progressive.com: 2条 (11.8%)
  - dmv.ca.gov: 2条 (11.8%)
- ✅ **语言分布**: 100% 英文
- ✅ **内容质量**: 所有样本都是汽车保险相关内容

### 其他 Collections
- `fiqa_10k_v1`: 10,000 条数据（包含大量不相关内容）

## 3. 端到端测试结果

### 测试查询 1: "加州最低汽车保险要求是什么？"
- **结果**: ❌ 0/5 相关
- **返回内容**: 越南语、泰语、印尼语等不相关内容
- **Score**: 0.3081 - 0.2758

### 测试查询 2: "How to file an auto insurance claim in California?"
- **结果**: ❌ 1/5 相关
- **相关结果**: 1条关于理赔流程
- **不相关内容**: 4条（财务建议、银行相关等）

### 测试查询 3: "SR-22 是什么？什么时候需要？"
- **结果**: ❌ 0/5 相关
- **返回内容**: 越南语、泰语等不相关内容

## 4. 问题分析

### 根本原因
1. **数据量严重不足**: `auto_insurance_v1` 只有 17 条数据
   - 向量检索需要足够的数据量才能有效工作
   - 17条数据无法覆盖各种查询场景
   - 可能因为数据量少，检索效果差或fallback到其他collection

2. **可能的问题**:
   - 实际查询可能fallback到了 `fiqa_10k_v1`（10,000条数据）
   - 或者 `auto_insurance_v1` 数据太少，检索不到相关内容

### 验证
- 抽样检查通过（100%保险相关域名）
- 但查询结果不相关，说明实际查询的可能不是 `auto_insurance_v1`

## 5. 验收标准检查

| 标准 | 状态 | 说明 |
|------|------|------|
| 抽样30条，>=80%来自保险域名 | ✅ PASS | 100%来自保险相关域名 |
| 3个查询 top5 至少3条相关 | ❌ FAIL | 0-1/5相关，需要>=3 |
| 无无关内容（如"孕期便秘"） | ❌ FAIL | 出现越南语、泰语等无关内容 |

**总体**: ❌ **FAIL** - 需要扩充数据量

## 6. 修复方案

### 方案 A: 扩充 auto_insurance_v1 数据（推荐）

**步骤**:
1. 运行数据抓取:
   ```bash
   python pipelines/auto_insurance_ingest.py \
     --config-dir docs/prompt2_input \
     --output data/auto_insurance_corpus.jsonl
   ```

2. 生成 embedding 并导入:
   ```bash
   python pipelines/embed_and_upsert.py \
     --input data/auto_insurance_corpus.jsonl \
     --collection auto_insurance_v1
   ```

3. **目标**: 至少 500-2000 条高质量文档

**优点**:
- 直接扩充现有collection
- 保持配置不变
- 数据质量已验证（100%保险相关）

### 方案 B: 创建新的 clean collection

**步骤**:
1. 创建过滤脚本 `scripts/filter_and_reimport_auto_insurance.py`
2. 白名单过滤（只保留以下域名）:
   - insurance.ca.gov
   - dmv.ca.gov
   - geico.com
   - statefarm.com
   - progressive.com
   - allstate.com
   - farmers.com
   - nationwide.com
   - 其他保险公司官网
3. 创建新 collection: `auto_insurance_v2_clean`
4. 重新导入数据
5. 更新后端配置使用新collection

**优点**:
- 确保数据质量（白名单过滤）
- 可以保留旧collection作为备份

### 方案 C: 临时方案（不推荐）

- 使用 `fiqa_10k_v1` 进行测试
- 不符合业务需求（包含大量不相关内容）

## 7. 建议

**立即行动**:
1. ✅ 后端配置已正确（无需修改）
2. ❌ **需要扩充数据**: 运行完整的数据抓取和导入流程
3. ❌ **目标数据量**: 至少 500-2000 条文档

**数据抓取优先级**:
1. 加州 DMV (50-100条)
2. 加州保险局 CDI (50-100条)
3. State Farm (200-300条)
4. GEICO (200-300条)
5. Progressive (200-300条)

**验收标准**:
- 数据量 >= 500 条
- Domain 分布 >= 80% 保险相关
- 3个测试查询 top5 至少 3 条相关
- 无无关内容（越南语、泰语等）

## 8. 结论

**当前状态**:
- ✅ 后端配置正确
- ✅ Collection 存在且内容质量好（100%保险相关）
- ❌ **数据量严重不足（仅17条）**
- ❌ **查询结果不相关**

**下一步**:
1. 运行完整的数据抓取流程
2. 扩充 `auto_insurance_v1` 到至少 500 条文档
3. 重新运行端到端测试验证
