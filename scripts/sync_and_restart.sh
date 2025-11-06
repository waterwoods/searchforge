#!/bin/bash
# 快速同步文件并重启容器的脚本
# 使用方法: ./scripts/sync_and_restart.sh

set -e

REMOTE="andy-wsl"
REMOTE_DIR="~/searchforge"
PROJECT_ROOT="/Users/nanxinli/Documents/dev/searchforge"

echo "🔄 开始同步文件到 RTX3080..."

# 同步 docker-compose.yml
echo "📦 同步 docker-compose.yml..."
scp "${PROJECT_ROOT}/docker-compose.yml" "${REMOTE}:${REMOTE_DIR}/docker-compose.yml"

# 同步 app_main.py
echo "📦 同步 app_main.py..."
scp "${PROJECT_ROOT}/services/fiqa_api/app_main.py" "${REMOTE}:${REMOTE_DIR}/services/fiqa_api/app_main.py"

echo "✅ 文件同步完成"
echo ""
echo "🔄 重启容器..."

# 重启容器
ssh "${REMOTE}" "cd ${REMOTE_DIR} && docker compose up -d rag-api"

echo "⏳ 等待容器启动..."
sleep 5

# 检查容器状态
echo "📊 检查容器状态..."
ssh "${REMOTE}" "cd ${REMOTE_DIR} && docker compose ps rag-api | grep rag-api"

# 检查健康状态
echo "🏥 检查健康状态..."
ssh "${REMOTE}" "cd ${REMOTE_DIR} && docker compose exec -T rag-api curl -fsS http://localhost:8000/health || echo '健康检查失败'"

echo ""
echo "✅ 完成！"

