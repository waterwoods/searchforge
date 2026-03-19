# Step 3 重启总结

## 当前状态

### ✅ 已完成
1. **代码更改**：所有翻译相关代码已更新
2. **argostranslate 安装**：已安装在用户和系统 Python 环境中
3. **语言包安装**：zh↔en 语言包已安装
4. **环境变量配置**：`.env.cloudrun` 已包含翻译配置
5. **后端重启**：已多次尝试重启

### ❌ 当前问题
1. **环境变量未加载**：调试端点显示 `enabled_env: "NOT_SET"`
2. **argostranslate 未找到**：后端进程无法导入 `argostranslate`
3. **翻译未应用**：`translation_applied: false`，`question_used` 仍然是中文

## 测试结果

### 调试端点 (`/api/debug/translation`)
```json
{
  "enabled_env": "NOT_SET",
  "provider": "NOT_SET",
  "argos_import_ok": false,
  "argos_has_zh_en": false,
  "error": "argostranslate not installed: No module named 'argostranslate'"
}
```

### 翻译查询测试
```json
{
  "ok": true,
  "translation_applied": false,
  "detected_lang": "zh",  // ✅ 语言检测工作正常
  "question_used": "加州最低汽车保险要求是什么？",  // ❌ 仍然是中文
  "sources_count": 5
}
```

## 根本原因分析

### 问题 1：环境变量未加载
- **现象**：`enabled_env: "NOT_SET"`
- **可能原因**：
  1. 后端进程在容器中运行，环境变量未传递
  2. `.env.cloudrun` 文件未在正确位置
  3. `load_dotenv()` 在代码中未正确执行

### 问题 2：argostranslate 未找到
- **现象**：`No module named 'argostranslate'`
- **可能原因**：
  1. 后端进程使用的 Python 环境与安装环境不同
  2. 后端在容器中运行，容器内未安装包
  3. Python 路径问题

### 问题 3：后端进程管理
- **现象**：多个后端进程在运行（root 用户）
- **可能原因**：
  1. 后端在 Docker 容器中运行
  2. 使用 systemd 或其他进程管理器
  3. 多个启动脚本同时运行

## 解决方案

### 方案 1：检查是否在容器中运行
```bash
# 检查进程是否在容器中
ps aux | grep uvicorn | head -1 | awk '{print $2}' | xargs -I {} cat /proc/{}/cgroup

# 如果显示 docker，则需要进入容器安装包
docker ps
docker exec -it <container_name> pip install argostranslate
docker exec -it <container_name> python -m argostranslate.argostranslate --install-packages zh en
docker restart <container_name>
```

### 方案 2：检查进程管理器
```bash
# 检查是否有 systemd 服务
systemctl list-units | grep uvicorn
systemctl list-units | grep searchforge

# 如果有服务，需要修改服务配置
sudo systemctl edit <service_name>
# 添加环境变量和 Python 路径
```

### 方案 3：直接修改运行中的进程环境（不推荐）
如果后端在容器外运行，可以：
1. 找到实际启动脚本
2. 修改启动脚本以包含环境变量
3. 重启服务

## 建议的下一步

1. **确定后端运行方式**：
   ```bash
   # 检查是否在容器中
   docker ps
   # 检查是否有 systemd 服务
   systemctl list-units | grep -E "uvicorn|searchforge|fiqa"
   # 检查启动脚本
   find . -name "*.sh" -exec grep -l "uvicorn.*app_main" {} \;
   ```

2. **根据运行方式修复**：
   - **Docker**：进入容器安装包并设置环境变量
   - **systemd**：修改服务配置文件
   - **手动启动**：确保使用正确的 Python 和环境变量

3. **验证修复**：
   ```bash
   # 测试调试端点
   curl -s http://localhost:8000/api/debug/translation | jq
   
   # 测试翻译查询
   curl -s -X POST http://localhost:8000/api/query \
     -H "Content-Type: application/json" \
     -d '{"question":"加州最低汽车保险要求是什么？","top_k":5,"translation_mode":"auto","collection":"fiqa"}' | jq '{translation_applied, detected_lang, question_used}'
   ```

## 文件位置

- 代码更改：`services/fiqa_api/routes/query.py`
- 环境配置：`.env.cloudrun`
- 重启脚本：`scripts/restart_backend_with_translation.sh`
- 测试脚本：`scripts/smoke_test_api_translation.sh`

## 当前进展

- ✅ 代码实现完成
- ✅ 依赖安装完成
- ⚠️  环境配置需要确认后端运行方式
- ⚠️  需要确定正确的重启方法
