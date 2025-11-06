#!/bin/bash
set -euo pipefail

echo "Stopping SearchForge services..."

# Stop backend processes
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm logs/backend.pid
    fi
fi

# Stop frontend processes
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm logs/frontend.pid
    fi
fi

# Kill any remaining uvicorn processes
echo "Stopping any remaining uvicorn processes..."
pkill -f "uvicorn.*app_main" || true

# Kill any remaining vite/node processes
echo "Stopping any remaining vite processes..."
pkill -f "vite.*dev" || true
pkill -f "node.*vite" || true

# Stop Docker services
echo "Stopping Docker services..."
if [ -f "docker-compose.yml" ] || [ -f "compose.yml" ]; then
    COMPOSE_FILE=""
    if [ -f "docker-compose.yml" ]; then
        COMPOSE_FILE="docker-compose.yml"
    else
        COMPOSE_FILE="compose.yml"
    fi
    
    echo "Stopping Redis and Qdrant..."
    docker compose -f $COMPOSE_FILE stop redis qdrant || true
else
    echo "No compose file found, skipping Docker services"
fi

echo ""
echo "✅ All SearchForge services stopped"
echo "📝 Logs are available in logs/ directory"
