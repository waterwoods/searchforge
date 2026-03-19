#!/bin/bash
# demo_e2e_check.sh - End-to-end demo check for HR-facing online demo
# Runs smoke tests and prints deployment instructions

set -e

CLOUD_RUN_URL="${CLOUD_RUN_URL:-https://fiqa-api-g7zatxrycq-uw.a.run.app}"

echo "=========================================="
echo "Demo E2E Check - HR-Facing Online Demo"
echo "=========================================="
echo ""

# Run smoke test
echo "[1/2] Running Cloud Run smoke tests..."
if bash scripts/smoke_cloud_run.sh; then
    echo "✅ Cloud Run smoke tests passed"
else
    echo "❌ Cloud Run smoke tests failed"
    exit 1
fi

echo ""
echo "[2/2] Deployment Checklist"
echo "=========================================="
echo ""
echo "✅ Cloud Run Backend:"
echo "   URL: $CLOUD_RUN_URL"
echo "   Status: Running"
echo ""
echo "📋 Vercel Frontend Setup:"
echo "   1. Set environment variable in Vercel dashboard:"
echo "      Name:  VITE_API_BASE_URL"
echo "      Value: $CLOUD_RUN_URL"
echo ""
echo "   2. Or use Vercel CLI:"
echo "      vercel env add VITE_API_BASE_URL production"
echo "      (paste: $CLOUD_RUN_URL)"
echo ""
echo "   3. Redeploy frontend after setting env var:"
echo "      vercel --prod"
echo ""
echo "🧪 Test Commands:"
echo "   # Health check"
echo "   curl -i $CLOUD_RUN_URL/healthz"
echo "   curl -i $CLOUD_RUN_URL/readyz"
echo ""
echo "   # Query endpoint"
echo "   curl -i -X POST $CLOUD_RUN_URL/api/query \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"question\":\"What is diversification?\",\"top_k\":10}'"
echo ""
echo "   # Demo summary (always returns 200)"
echo "   curl -i $CLOUD_RUN_URL/api/metrics/demo-summary"
echo ""
echo "✅ CORS Configuration:"
echo "   Cloud Run is configured to allow all origins (*) for demo"
echo "   No CORS errors expected when frontend calls Cloud Run"
echo ""
echo "=========================================="
echo "✅ Demo E2E check complete!"
echo "=========================================="
