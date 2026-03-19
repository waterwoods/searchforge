#!/bin/bash
# 重启后端并启用翻译功能
# 需要 root 权限来终止旧进程

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "=========================================="
echo "重启后端（启用翻译）"
echo "=========================================="
echo ""

# 检查是否有 root 权限
if [ "$EUID" -eq 0 ]; then
    echo "✅ 以 root 用户运行"
    echo "正在终止旧进程..."
    pkill -9 -f uvicorn || true
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 2
else
    echo "⚠️  需要 root 权限来终止旧进程"
    echo "请先执行："
    echo "  sudo pkill -9 -f uvicorn"
    echo "  sudo lsof -ti :8000 | xargs sudo kill -9"
    echo ""
    read -p "已终止旧进程？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消"
        exit 1
    fi
fi

echo ""
echo "加载环境变量..."
set -a
if [ -f .env.cloudrun ]; then
    source .env.cloudrun
    echo "✅ 已加载 .env.cloudrun"
else
    echo "⚠️  .env.cloudrun 不存在"
fi
set +a

# 确保翻译环境变量已设置
export TRANSLATION_ENABLED=${TRANSLATION_ENABLED:-1}
export TRANSLATION_PROVIDER=${TRANSLATION_PROVIDER:-argos}
export TRANSLATE_SOURCES_TO_ZH=${TRANSLATE_SOURCES_TO_ZH:-1}

echo "环境变量："
echo "  TRANSLATION_ENABLED=$TRANSLATION_ENABLED"
echo "  TRANSLATION_PROVIDER=$TRANSLATION_PROVIDER"
echo "  TRANSLATE_SOURCES_TO_ZH=$TRANSLATE_SOURCES_TO_ZH"
echo ""

# 检查端口是否可用
if lsof -ti :8000 > /dev/null 2>&1; then
    echo "❌ 端口 8000 仍被占用"
    echo "请手动终止占用端口的进程"
    exit 1
fi

echo "启动后端..."
echo "日志文件: results/auto_insurance/backend_restart_$(date +%Y%m%d_%H%M%S).log"
LOG_FILE="results/auto_insurance/backend_restart_$(date +%Y%m%d_%H%M%S).log"
mkdir -p results/auto_insurance

python3 -m uvicorn services.fiqa_api.app_main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    > "$LOG_FILE" 2>&1 &

BACKEND_PID=$!
echo "后端进程 PID: $BACKEND_PID"
echo ""

echo "等待后端启动（10秒）..."
sleep 10

echo ""
echo "检查后端状态..."
if curl -s -f http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "✅ 后端已启动"
    echo ""
    echo "测试翻译功能..."
    echo ""
    
    # 测试调试端点
    echo "1. 调试端点："
    curl -s http://localhost:8000/api/debug/translation | jq '.' || echo "   ⚠️  调试端点返回错误"
    echo ""
    
    # 测试翻译查询
    echo "2. 翻译查询测试："
    curl -s -X POST http://localhost:8000/api/query \
        -H "Content-Type: application/json" \
        -d '{"question":"加州最低汽车保险要求是什么？","top_k":5,"translation_mode":"auto","collection":"auto_insurance_v2_clean"}' \
        | jq '{ok, translation_applied, detected_lang, question_used, sources_count: (.sources | length)}'
    echo ""
    
    echo "✅ 后端已启动并运行"
    echo "查看日志: tail -f $LOG_FILE"
else
    echo "❌ 后端启动失败"
    echo "查看日志: cat $LOG_FILE"
    exit 1
fi
