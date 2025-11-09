#!/usr/bin/env bash
# warmup.sh - 两道闸就绪检查：/api/health/embeddings 与 /ready 都需要 ok:true
# 【守门人】默认走快路：DEV_MODE=1 开发态预热检查

set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-60}"
INTERVAL="${INTERVAL:-2}"

echo "🔥 Warmup Script - Two-Gate Health Check"
echo "   API Base: $API_BASE"
echo "   Max Attempts: $MAX_ATTEMPTS (每 ${INTERVAL}s 检查一次)"
echo ""

start_time=$(date +%s)

for i in $(seq 1 "$MAX_ATTEMPTS"); do
    echo "[$i/$MAX_ATTEMPTS] Checking health gates..."
    
    # 第一道闸：/api/health/embeddings
    embed_response=$(curl -fsS "$API_BASE/api/health/embeddings" 2>/dev/null || echo '{"ok":false}')
    embed_ok=$(echo "$embed_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null || echo "false")
    
    # 第二道闸：/ready
    ready_response=$(curl -fsS "$API_BASE/ready" 2>/dev/null || echo '{"ok":false}')
    ready_ok=$(echo "$ready_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null || echo "false")
    
    echo "   Embeddings: $embed_ok | Ready: $ready_ok"
    
    # 两道闸都通过才算成功
    if [ "$embed_ok" = "True" ] && [ "$ready_ok" = "True" ]; then
        end_time=$(date +%s)
        elapsed=$((end_time - start_time))
        
        echo ""
        echo "✅ Both health gates passed!"
        echo ""
        echo "📊 Final Status:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🔹 /api/health/embeddings:"
        echo "$embed_response" | python3 -m json.tool 2>/dev/null || echo "$embed_response"
        echo ""
        echo "🔹 /ready:"
        echo "$ready_response" | python3 -m json.tool 2>/dev/null || echo "$ready_response"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "⏱️  Warmup completed in ${elapsed}s"
        exit 0
    fi
    
    sleep "$INTERVAL"
done

# 超时退出
echo ""
echo "❌ Warmup timeout after $((MAX_ATTEMPTS * INTERVAL))s"
echo ""
echo "📋 Last responses:"
echo "Embeddings: $embed_response"
echo "Ready: $ready_response"
echo ""
echo "🔍 Checking container logs for embedding/model keywords..."
docker compose -f /home/andy/searchforge/docker-compose.yml -f /home/andy/searchforge/docker-compose.dev.yml logs --tail=80 rag-api | grep -iE 'embed|sbert|model' || true
exit 1

