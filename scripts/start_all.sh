#!/bin/bash
set -euo pipefail

# Load environment variables
if [ -f .env ]; then
    echo "Loading .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Default ports
BACKEND=${BACKEND:-8011}
FRONTEND=${FRONTEND:-5173}
QDRANT=${QDRANT:-6333}
REDIS=${REDIS:-6379}

echo "Starting SearchForge with ports: Backend=$BACKEND, Frontend=$FRONTEND, Qdrant=$QDRANT, Redis=$REDIS"

# Create logs directory
mkdir -p logs

# Kill any existing processes on target ports
echo "Checking for existing processes on target ports..."
if lsof -i :$BACKEND > /dev/null 2>&1; then
    echo "Killing existing process on port $BACKEND..."
    lsof -ti :$BACKEND | xargs kill -9 2>/dev/null || true
fi
if lsof -i :$FRONTEND > /dev/null 2>&1; then
    echo "Killing existing process on port $FRONTEND..."
    lsof -ti :$FRONTEND | xargs kill -9 2>/dev/null || true
fi

# Check for Python environment
if command -v uv &> /dev/null; then
    echo "Using uv for Python environment..."
    PYTHON_CMD="uv run"
else
    echo "Using venv for Python environment..."
    if [ ! -d .venv ]; then
        echo "Creating virtual environment..."
        python3 -m venv .venv
    fi
    source .venv/bin/activate
    PYTHON_CMD="python"
fi

# Install backend dependencies if needed
echo "Installing backend dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt
$PYTHON_CMD -m pip install redis

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm ci
    cd ..
fi

# Start infrastructure services
echo "Starting infrastructure services..."
if [ -f "docker-compose.yml" ] || [ -f "compose.yml" ]; then
    COMPOSE_FILE=""
    if [ -f "docker-compose.yml" ]; then
        COMPOSE_FILE="docker-compose.yml"
    else
        COMPOSE_FILE="compose.yml"
    fi
    
    # Check if services are already running
    if curl -s http://localhost:$QDRANT/dashboard > /dev/null 2>&1 && redis-cli -p $REDIS ping > /dev/null 2>&1; then
        echo "Infrastructure services (Redis, Qdrant) are already running"
    else
        echo "Starting Redis and Qdrant with $COMPOSE_FILE..."
        docker compose -f $COMPOSE_FILE up -d redis qdrant
        
        # Wait for services to be ready
        echo "Waiting for services to be ready..."
        timeout 30 bash -c 'until curl -s http://localhost:'$QDRANT'/dashboard > /dev/null; do sleep 1; done' || {
            echo "Warning: Qdrant not ready after 30s, continuing..."
        }
        
        timeout 30 bash -c 'until redis-cli -p '$REDIS' ping > /dev/null; do sleep 1; done' || {
            echo "Warning: Redis not ready after 30s, continuing..."
        }
    fi
else
    echo "Warning: No docker-compose.yml or compose.yml found, skipping infrastructure startup"
fi

# Start backend
echo "Starting backend on port $BACKEND..."
cd services/fiqa_api
if [ "${NODE_ENV:-development}" = "development" ] || [ "${NODE_ENV:-development}" = "dev" ]; then
    $PYTHON_CMD -m uvicorn app_main:app --host 0.0.0.0 --port $BACKEND --reload > ../../logs/backend.log 2>&1 &
else
    $PYTHON_CMD -m uvicorn app_main:app --host 0.0.0.0 --port $BACKEND > ../../logs/backend.log 2>&1 &
fi
BACKEND_PID=$!
cd ../..

# Start frontend
echo "Starting frontend on port $FRONTEND..."
cd frontend
export VITE_API_BASE=http://localhost:$BACKEND
npm run dev -- --port $FRONTEND > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Store PIDs for stop script
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

# Print summary
echo ""
echo "✅ SearchForge started successfully!"
echo "🌐 Frontend: http://localhost:$FRONTEND"
echo "🔧 Backend API: http://localhost:$BACKEND"
echo "📊 Qdrant Dashboard: http://localhost:$QDRANT/dashboard"
echo "📝 Logs: logs/backend.log, logs/frontend.log"
echo ""
echo "To stop all services: ./scripts/stop_all.sh"
echo "To check health: ./scripts/health_check.sh"
