#!/bin/bash
# OpenClaw MVP Smoke Test Script
# 路径: ~/ai-tools/openclaw
# 用途: 一键启动 OpenClaw 并测试执行 ls 命令

set -e

OPENCLAW_DIR="$HOME/ai-tools/openclaw"
OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"
GATEWAY_PORT=18789

echo "🦞 OpenClaw MVP Smoke Test"
echo "=========================="
echo ""

# 检查 Node.js 版本
echo "📋 检查环境..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

# 加载 nvm 并使用 Node 22
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    source "$HOME/.nvm/nvm.sh"
    nvm use 22 2>/dev/null || echo "⚠️  无法切换到 Node 22，使用当前版本"
fi

NODE_VERSION=$(node --version)
echo "✅ Node.js: $NODE_VERSION"

# 检查 pnpm
if ! command -v pnpm &> /dev/null; then
    echo "❌ pnpm 未安装，正在安装..."
    npm install -g pnpm
fi
echo "✅ pnpm: $(pnpm --version)"

# 检查 OpenClaw 目录
if [ ! -d "$OPENCLAW_DIR" ]; then
    echo "❌ OpenClaw 目录不存在: $OPENCLAW_DIR"
    exit 1
fi
echo "✅ OpenClaw 目录: $OPENCLAW_DIR"

# 检查 Ollama
echo ""
echo "🔍 检查 Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama 未安装"
    echo ""
    echo "请先安装 Ollama:"
    echo "  curl -fsSL https://ollama.ai/install.sh | sh"
    echo ""
    echo "然后拉取模型:"
    echo "  ollama pull llama3.3"
    echo ""
    echo "或者使用其他方式安装 Ollama（需要 sudo 权限）"
    echo ""
    read -p "是否继续测试（将使用已配置的模型）? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Ollama 已安装: $(ollama --version 2>&1 | head -1)"
    
    # 检查 Ollama 服务
    if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
        echo "⚠️  Ollama 服务未运行，正在启动..."
        ollama serve > /dev/null 2>&1 &
        sleep 3
    fi
    
    # 检查模型
    if ! ollama list | grep -q "llama3.3"; then
        echo "⚠️  模型 llama3.3 未安装，正在拉取..."
        ollama pull llama3.3
    fi
    echo "✅ Ollama 服务运行中"
fi

# 检查配置文件
if [ ! -f "$OPENCLAW_CONFIG" ]; then
    echo "⚠️  配置文件不存在: $OPENCLAW_CONFIG"
    echo "   将使用默认配置"
fi

# 切换到 OpenClaw 目录
cd "$OPENCLAW_DIR"

# 检查构建
if [ ! -d "dist" ]; then
    echo ""
    echo "🔨 构建 OpenClaw..."
    source "$HOME/.nvm/nvm.sh" 2>/dev/null || true
    nvm use 22 2>/dev/null || true
    pnpm build
fi

# 设置环境变量
export OLLAMA_API_KEY="ollama-local"
export OPENCLAW_STATE_DIR="$HOME/.openclaw"
export OPENCLAW_CONFIG_PATH="$OPENCLAW_CONFIG"

# 检查 Gateway 是否已运行
echo ""
echo "🚀 检查 Gateway 状态..."
if curl -s "http://127.0.0.1:$GATEWAY_PORT/health" > /dev/null 2>&1; then
    echo "✅ Gateway 已在运行"
    GATEWAY_RUNNING=true
else
    echo "⚠️  Gateway 未运行，将在后台启动..."
    GATEWAY_RUNNING=false
fi

# 启动 Gateway（如果未运行）
if [ "$GATEWAY_RUNNING" = false ]; then
    echo ""
    echo "🚀 启动 Gateway..."
    source "$HOME/.nvm/nvm.sh" 2>/dev/null || true
    nvm use 22 2>/dev/null || true
    
    # 在后台启动 Gateway
    pnpm openclaw gateway --port $GATEWAY_PORT > /tmp/openclaw-gateway.log 2>&1 &
    GATEWAY_PID=$!
    echo "✅ Gateway 已启动 (PID: $GATEWAY_PID)"
    
    # 等待 Gateway 就绪
    echo "⏳ 等待 Gateway 就绪..."
    for i in {1..30}; do
        if curl -s "http://127.0.0.1:$GATEWAY_PORT/health" > /dev/null 2>&1; then
            echo "✅ Gateway 就绪"
            break
        fi
        sleep 1
    done
    
    if ! curl -s "http://127.0.0.1:$GATEWAY_PORT/health" > /dev/null 2>&1; then
        echo "❌ Gateway 启动失败，查看日志: /tmp/openclaw-gateway.log"
        exit 1
    fi
fi

# 测试执行 ls 命令
echo ""
echo "🧪 测试执行 ls 命令..."
echo ""

# 使用 agent 命令发送消息
source "$HOME/.nvm/nvm.sh" 2>/dev/null || true
nvm use 22 2>/dev/null || true

TEST_MESSAGE="List files in current directory using ls command"
echo "📤 发送消息: \"$TEST_MESSAGE\""
echo ""

# 使用 openclaw agent 命令
RESPONSE=$(pnpm openclaw agent --message "$TEST_MESSAGE" 2>&1) || true

echo "📥 响应:"
echo "$RESPONSE"
echo ""

# 检查响应中是否包含 ls 输出
if echo "$RESPONSE" | grep -q "ls\|file\|directory"; then
    echo "✅ 测试通过: Agent 成功响应"
else
    echo "⚠️  测试结果不确定，请手动验证"
fi

echo ""
echo "📊 Gateway 状态:"
curl -s "http://127.0.0.1:$GATEWAY_PORT/health" | head -20 || echo "无法获取状态"

echo ""
echo "✅ Smoke Test 完成"
echo ""
echo "💡 提示:"
echo "  - Gateway 运行在: http://127.0.0.1:$GATEWAY_PORT"
echo "  - Dashboard: http://127.0.0.1:$GATEWAY_PORT/"
echo "  - 查看日志: tail -f /tmp/openclaw-gateway.log"
echo "  - 停止 Gateway: kill $GATEWAY_PID (如果已启动)"
