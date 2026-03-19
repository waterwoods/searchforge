# Local Development Verification Steps

This document provides step-by-step verification for local development setup.

## Prerequisites

- Python 3.8+ installed
- Node.js 18+ and npm installed
- Backend dependencies installed (see main README)
- Frontend dependencies installed: `cd ui && npm install`

## Quick Verification

### 1. Backend Health Check

```bash
# Test backend is running
curl -sS http://localhost:8000/healthz
# Expected: {"ok": true, "status": "healthy", ...}

curl -sS http://localhost:8000/readyz
# Expected: {"ok": true, "clients_ready": true, ...}
```

### 2. Backend API Test

```bash
# Test query endpoint
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5173" \
  -d '{"question":"test","top_k":1}'

# Expected: JSON response with "ok": true and "sources" array
```

### 3. Frontend Access

1. Open browser: `http://localhost:5173/demo`
2. Check browser console (F12) for errors
3. Submit a test query
4. Verify results are displayed

## Detailed Verification

### Step 1: Start Backend

**Option A: Using dev script**
```bash
./scripts/dev_local.sh
```

**Option B: Manual start**
```bash
# From repo root
python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8000 --reload
```

**Verify:**
- Backend responds to `/healthz` (200 OK)
- Backend responds to `/readyz` (200 OK when ready)
- No errors in terminal output

### Step 2: Configure Frontend

**Check environment file:**
```bash
cd ui
cat .env.local
# Should contain: VITE_API_BASE_URL=http://localhost:8000
```

**If missing, create it:**
```bash
cd ui
cp .env.example .env.local
# Edit .env.local and set VITE_API_BASE_URL=http://localhost:8000
```

### Step 3: Start Frontend

```bash
cd ui
npm run dev
```

**Verify:**
- Frontend starts on port 5173
- No errors in terminal
- Browser can access `http://localhost:5173`

### Step 4: Test Demo Page

1. **Open demo page:**
   - Navigate to: `http://localhost:5173/demo`

2. **Check browser console (F12):**
   - No CORS errors
   - No network errors
   - API calls show 200 OK

3. **Submit test query:**
   - Enter: "加州最低汽车保险要求是什么？"
   - Click "Ask"
   - Verify results appear

4. **Verify response:**
   - Results show title, text, score
   - Request latency is displayed
   - No "Failed to fetch" error

### Step 5: CORS Verification

**Test CORS headers:**
```bash
curl -v -X OPTIONS http://localhost:8000/api/query \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  2>&1 | grep -i "access-control"
```

**Expected:**
- `Access-Control-Allow-Origin: *` (in dev mode)
- `Access-Control-Allow-Methods: *`
- `Access-Control-Allow-Headers: *`

## Common Issues

### Issue: "Failed to fetch"

**Causes:**
1. Backend not running
2. Wrong API base URL in `.env.local`
3. CORS misconfiguration
4. Network/firewall blocking

**Solutions:**
1. Check backend: `curl http://localhost:8000/healthz`
2. Verify `.env.local`: `cat ui/.env.local`
3. Check CORS: Backend should have `ALLOW_ALL_CORS=1` (default)
4. Use dev script: `./scripts/dev_local.sh`

### Issue: CORS errors in browser

**Check:**
- Backend CORS config allows `localhost:5173`
- In dev mode, `ALLOW_ALL_CORS=1` should allow all origins
- Check backend logs for CORS-related errors

**Fix:**
- Ensure backend has `ALLOW_ALL_CORS=1` (default)
- Or set `ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`

### Issue: Port already in use

**Check:**
```bash
# Check what's using port 8000
lsof -i :8000

# Check what's using port 5173
lsof -i :5173
```

**Fix:**
- Stop existing processes
- Or use different ports: `BACKEND_PORT=8001 FRONTEND_PORT=5174 ./scripts/dev_local.sh`

## Environment Variables

### Backend (.env or environment)

- `ALLOW_ALL_CORS=1` - Allow all origins (dev mode, default)
- `ALLOWED_ORIGINS=...` - Specific origins (production)
- `PORT=8000` - Backend port (default: 8000)

### Frontend (ui/.env.local)

- `VITE_API_BASE_URL=http://localhost:8000` - Backend API URL

## Success Criteria

✅ Backend responds to `/healthz` and `/readyz`  
✅ Frontend loads at `http://localhost:5173/demo`  
✅ Demo page can submit queries  
✅ Results are displayed correctly  
✅ No CORS errors in browser console  
✅ Request latency is shown  
✅ Source URLs are clickable  

## Next Steps

Once verified, you can:
- Test with different queries (Chinese, English, mixed)
- Check backend logs for query processing
- Verify Qdrant Cloud connection
- Test with production Cloud Run URL
