# Step 3 Docker 容器修复总结

## 已完成

1. ✅ **argostranslate 安装**：已在容器中安装
2. ✅ **语言包安装**：zh↔en 语言包已安装
3. ✅ **docker-compose.yml 更新**：已添加翻译环境变量
4. ✅ **代码更改**：所有翻译相关代码已更新

## 当前状态

### 测试结果
- **调试端点**：`argos_import_ok: true` ✅，但 `argos_has_zh_en: false` ⚠️
- **环境变量**：`enabled_env: "NOT_SET"` ❌
- **翻译查询**：`detected_lang: "zh"` ✅，但 `translation_applied: false` ❌

### 问题
1. **环境变量未生效**：需要重建容器（`docker compose up -d --build`）而不是重启
2. **语言包验证**：需要验证语言包是否正确安装

## 下一步操作

### 选项 1：重建容器（推荐）
```bash
cd /home/andy/searchforge
docker compose up -d --build rag-api
# 等待容器启动
sleep 15
# 测试
curl -s http://localhost:8000/api/debug/translation | jq
```

### 选项 2：手动设置环境变量（临时）
```bash
# 在容器运行时设置（临时，重启后失效）
docker exec searchforge-rag-api-1 bash -c 'export TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos TRANSLATE_SOURCES_TO_ZH=1'
# 然后重启容器内的进程
```

### 选项 3：更新 .env.current 文件
```bash
# 如果使用 .env.current，添加：
echo "TRANSLATION_ENABLED=1" >> .env.current
echo "TRANSLATION_PROVIDER=argos" >> .env.current
echo "TRANSLATE_SOURCES_TO_ZH=1" >> .env.current
# 然后重启容器
docker compose restart rag-api
```

## 验证步骤

重建容器后，运行：

```bash
# 1. 检查调试端点
curl -s http://localhost:8000/api/debug/translation | jq

# 应该看到：
# {
#   "enabled_env": "1",
#   "provider": "argos",
#   "argos_import_ok": true,
#   "argos_has_zh_en": true
# }

# 2. 测试翻译查询
curl -s -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question":"加州最低汽车保险要求是什么？","top_k":5,"translation_mode":"auto","collection":"fiqa"}' | jq '{translation_applied, detected_lang, question_used}'

# 应该看到：
# {
#   "translation_applied": true,
#   "detected_lang": "zh",
#   "question_used": "What are the minimum auto insurance requirements in California?"
# }

# 3. 运行 Smoke Test
./scripts/smoke_test_api_translation.sh
```

## 文件更改

- ✅ `docker-compose.yml`：已添加翻译环境变量
- ✅ `services/fiqa_api/routes/query.py`：翻译逻辑已实现
- ✅ `services/fiqa_api/utils/translation.py`：翻译模块已更新
- ✅ `services/fiqa_api/app_main.py`：环境变量加载已修复

## 注意事项

- 环境变量更改需要**重建容器**才能生效（`docker compose up -d --build`）
- 仅重启容器（`docker compose restart`）不会应用新的环境变量
- 语言包已安装，但需要验证是否正确加载
