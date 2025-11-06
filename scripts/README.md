# SearchForge Launcher Scripts

This directory contains scripts for managing the SearchForge application with a single command.

## Quick Start

### Start All Services
```bash
./scripts/start_all.sh
```

### Check Service Health
```bash
./scripts/health_check.sh
```

### Stop All Services
```bash
./scripts/stop_all.sh
```

## What Each Script Does

### `start_all.sh`
- Loads environment variables from `.env` file (if present)
- Sets default ports: Backend=8011, Frontend=5173, Qdrant=6333, Redis=6379
- Detects Python environment (prefers `uv`, falls back to `venv`)
- Installs dependencies if needed:
  - Backend: `pip install -r requirements.txt`
  - Frontend: `npm ci`
- Starts infrastructure services:
  - Docker Compose: Redis and Qdrant
  - Waits for services to be ready (30s timeout)
- Starts backend (FastAPI/uvicorn) with auto-reload in development
- Starts frontend (Vite) with proper API base URL
- Prints a summary with all service URLs

### `stop_all.sh`
- Gracefully stops all running services
- Kills backend processes (uvicorn)
- Kills frontend processes (vite/node)
- Stops Docker services (Redis, Qdrant)
- Cleans up PID files

### `health_check.sh`
- Performs comprehensive health checks:
  - **Backend**: `GET /readyz` endpoint (expects `{"ok":true}`)
  - **Code Lookup**: `POST /api/agent/code_lookup` with ping message
  - **Frontend**: HTTP 200 response with HTML content
  - **Qdrant**: HTTP connectivity check
  - **Redis**: `PING` command (expects `PONG`)
- Returns exit code 0 if all services are healthy, 1 if any fail
- Provides clear PASS/FAIL status for each service

## Log Files

Service logs are written to the `logs/` directory:
- `logs/backend.log` - Backend API logs
- `logs/frontend.log` - Frontend development server logs
- `logs/backend.pid` - Backend process ID (for stop script)
- `logs/frontend.pid` - Frontend process ID (for stop script)

Docker service logs can be viewed with:
```bash
docker logs qdrant
docker logs redis
```

## Environment Variables

Create a `.env` file in the project root to customize ports:
```bash
BACKEND=8011
FRONTEND=5173
QDRANT=6333
REDIS=6379
NODE_ENV=development
```

## Troubleshooting

### Services Won't Start
1. Check if ports are available: `lsof -i :8011 -i :5173 -i :6333 -i :6379`
2. Ensure Docker is running: `docker ps`
3. Check logs: `tail -f logs/backend.log logs/frontend.log`

### Health Check Failures
1. Run individual checks:
   ```bash
   curl http://localhost:8011/readyz
   curl http://localhost:5173
   curl http://localhost:6333
   redis-cli -p 6379 ping
   ```

### Clean Restart
```bash
./scripts/stop_all.sh
# Wait a moment
./scripts/start_all.sh
```

## Requirements

- Python 3.8+ (with `uv` preferred, or `venv`)
- Node.js 16+ and npm
- Docker and Docker Compose
- Redis client (for health checks)
- curl (for HTTP health checks)
