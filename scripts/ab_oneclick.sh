#!/usr/bin/env bash
set -euo pipefail

# AB-oneclick: Auto tunnel (cloudflared/ngrok) + CORS + service startup
# Usage: bash scripts/ab_oneclick.sh

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTSERVICE_DIR="$PROJECT_ROOT/agentic_services/AgentService"
PORT=8672
TUNNEL_URL=""
TUNNEL_HOST=""

echo "🚀 AB-oneclick: Starting HTTPS tunnel and AgentService..."

# Try cloudflared first (priority)
if command -v cloudflared &>/dev/null; then
    echo "✅ Found cloudflared, starting tunnel..."
    
    # Start cloudflared in background
    # Use --protocol http2 for better stability
    cloudflared tunnel --url http://localhost:$PORT --protocol http2 > /tmp/cloudflared.log 2>&1 &
    TUNNEL_PID=$!
    
    # Wait for tunnel to establish (max 10 seconds)
    echo "⏳ Waiting for cloudflared tunnel to establish..."
    for i in {1..20}; do
        sleep 0.5
        
        # Try to extract URL from log file
        if [ -f /tmp/cloudflared.log ]; then
            # Look for the trycloudflare.com URL in the log (matches URLs in log messages)
            TUNNEL_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cloudflared.log | head -n1 || true)
            
            if [ -n "$TUNNEL_URL" ]; then
                echo "✅ Cloudflared tunnel established: $TUNNEL_URL"
                break
            fi
        fi
        
        if [ $i -eq 20 ]; then
            echo "⚠️  Cloudflared failed after 10s, trying ngrok..."
            kill $TUNNEL_PID 2>/dev/null || true
            TUNNEL_URL=""
        fi
    done
fi

# If cloudflared failed or not available, try ngrok
if [ -z "$TUNNEL_URL" ] && command -v ngrok &>/dev/null; then
    echo "✅ Found ngrok, starting tunnel..."
    
    # Start ngrok in background
    ngrok http $PORT --log=stdout > /tmp/ngrok.log 2>&1 &
    TUNNEL_PID=$!
    
    # Wait for ngrok to establish (max 10 seconds)
    echo "⏳ Waiting for ngrok tunnel to establish..."
    for i in {1..20}; do
        sleep 0.5
        
        # Try to query ngrok API
        TUNNEL_URL=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | \
            grep -Eo '"public_url":"https://[^"]+' | \
            sed 's/"public_url":"//' | \
            head -n1 || true)
        
        if [ -n "$TUNNEL_URL" ]; then
            echo "✅ Ngrok tunnel established: $TUNNEL_URL"
            break
        fi
        
        if [ $i -eq 20 ]; then
            echo "❌ Failed to get ngrok URL after 10s"
            kill $TUNNEL_PID 2>/dev/null || true
            TUNNEL_URL=""
        fi
    done
fi

# If both failed or neither available
if [ -z "$TUNNEL_URL" ]; then
    echo "❌ Neither cloudflared nor ngrok found!"
    echo ""
    echo "Please install one of the following:"
    echo "  cloudflared: brew install cloudflared"
    echo "  ngrok:       brew install ngrok (requires account + authtoken)"
    echo ""
    exit 1
fi

# Verify we got a valid tunnel URL
if [ -z "$TUNNEL_URL" ]; then
    echo "❌ Failed to establish tunnel. Please check tunnel logs:"
    echo "   cloudflared: /tmp/cloudflared.log"
    echo "   ngrok:       /tmp/ngrok.log"
    exit 1
fi

# Extract hostname (remove https:// prefix)
TUNNEL_HOST="${TUNNEL_URL#https://}"

echo ""
echo "🔐 Configuring CORS for tunnel domain..."

# Export environment variables for the service
export AGENTSVC_TOKEN=""
export CORS_ORIGINS="https://platform.openai.com,https://agentbuilder.openai.com,https://builder.openai.com,https://${TUNNEL_HOST}"

echo "✅ CORS_ORIGINS=${CORS_ORIGINS}"
echo "✅ AGENTSVC_TOKEN=(empty - no auth required)"

# Print and copy URL to clipboard
echo ""
echo "📋 Copying URL to clipboard..."
printf "%s" "$TUNNEL_URL" | pbcopy 2>/dev/null || true

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SERVICE_URL=$TUNNEL_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 URL copied to clipboard!"
echo ""
echo "🎯 Next steps:"
echo "   1. AgentBuilder → MCP → Add server"
echo "   2. Paste URL: $TUNNEL_URL"
echo "   3. Authentication: None"
echo "   4. Wait for 4 tools to appear"
echo ""
echo "🚀 Starting AgentService on port $PORT..."
echo ""

# Change to AgentService directory and start service
cd "$AGENTSERVICE_DIR"

# Start service with poetry (foreground)
# Use --timeout-keep-alive for SSE stability
poetry run uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 120

