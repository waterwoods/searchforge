#!/usr/bin/env bash
set -euo pipefail

# CF-oneclick: Cloudflared tunnel + CORS + service startup
# Usage: bash scripts/cf_oneclick.sh

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTSERVICE_DIR="$PROJECT_ROOT/agentic_services/AgentService"
PORT=8672
CF_URL=""

echo "🚀 CF-oneclick: Starting Cloudflared tunnel and AgentService..."

# Check if cloudflared is available
if ! command -v cloudflared &>/dev/null; then
    echo "❌ cloudflared not found!"
    echo ""
    echo "Please install cloudflared:"
    echo "  brew install cloudflared"
    echo ""
    exit 1
fi

echo "✅ Found cloudflared, starting tunnel..."

# Clean up old log
rm -f /tmp/cloudflared_oneclick.log

# Start cloudflared in background
# Use --protocol http2 for better stability
cloudflared tunnel --url http://localhost:$PORT --protocol http2 > /tmp/cloudflared_oneclick.log 2>&1 &
TUNNEL_PID=$!

echo "⏳ Waiting for cloudflared tunnel to establish (this may take up to 15 seconds)..."

# Wait for tunnel to establish (max 15 seconds, longer than ab-oneclick)
TUNNEL_URL=""
for i in {1..30}; do
    sleep 0.5
    
        # Try to extract URL from log file
        if [ -f /tmp/cloudflared_oneclick.log ]; then
            # Look for the trycloudflare.com URL in the log (matches URLs in log messages)
            TUNNEL_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cloudflared_oneclick.log | head -n1 || true)
        
        if [ -n "$TUNNEL_URL" ]; then
            echo "✅ Cloudflared tunnel established: $TUNNEL_URL"
            break
        fi
        
        # Check for errors in log
        if grep -q "ERR" /tmp/cloudflared_oneclick.log; then
            # Continue trying, but show warning after 10 seconds
            if [ $i -ge 20 ]; then
                echo "⚠️  Cloudflared showing errors, still trying... (check /tmp/cloudflared_oneclick.log for details)"
            fi
        fi
    fi
    
    if [ $i -eq 30 ]; then
        echo ""
        echo "❌ Failed to get cloudflared URL after 15 seconds"
        echo ""
        echo "Cloudflared log (/tmp/cloudflared_oneclick.log):"
        tail -20 /tmp/cloudflared_oneclick.log 2>/dev/null || echo "  (no log available)"
        echo ""
        echo "Common issues:"
        echo "  • Network connectivity problems"
        echo "  • Cloudflared version too old (try: brew upgrade cloudflared)"
        echo "  • Firewall blocking outbound connections"
        echo ""
        kill $TUNNEL_PID 2>/dev/null || true
        exit 1
    fi
done

# Extract hostname (remove https:// prefix)
CF_URL="${TUNNEL_URL#https://}"

echo ""
echo "🔐 Configuring CORS for cloudflared domain..."

# Export environment variables for the service
export AGENTSVC_TOKEN=""
export CORS_ORIGINS="https://platform.openai.com,https://agentbuilder.openai.com,https://builder.openai.com,https://${CF_URL}"

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
poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 120

