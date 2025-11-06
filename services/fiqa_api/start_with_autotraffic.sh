#!/bin/bash
# Start FIQA API with Auto-Traffic enabled
#
# Usage:
#   ./start_with_autotraffic.sh
#
# The worker will automatically generate traffic every 20s and rebuild the dashboard

cd "$(dirname "$0")"

echo "🚀 Starting FIQA API with Auto-Traffic enabled..."
echo "   Worker will start automatically on boot"
echo "   Dashboard: http://localhost:8080/demo"
echo ""

export AUTO_TRAFFIC=1
uvicorn app:app --host 0.0.0.0 --port 8080

