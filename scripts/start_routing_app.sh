#!/bin/bash
# Start app_main with FAISS routing on port 8011
# =============================================

cd "$(dirname "$0")/.." || exit 1

echo "========================================================================"
echo "Starting app_main with FAISS Routing"
echo "========================================================================"
echo "Port: 8011"
echo "Features:"
echo "  - FAISS dual-lane routing"
echo "  - Auto-prewarm on startup"
echo "  - POST /search with X-Search-Route header"
echo "  - POST /ops/routing/flags for configuration"
echo "========================================================================"
echo ""
echo "Starting in 3 seconds..."
sleep 3

cd services || exit 1

# Fix OpenMP library conflict between numpy and FAISS
export KMP_DUPLICATE_LIB_OK=TRUE

python -m uvicorn fiqa_api.app_main:app --host 0.0.0.0 --port 8011 --reload

