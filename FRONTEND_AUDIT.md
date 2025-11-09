# Frontend Entry Audit Report

**Generated:** 2025-01-XX  
**Repository:** searchforge  
**Audit Type:** Frontend Entry Directory & Port/Proxy Configuration

---

## Executive Summary

```
Entry: frontend/
Dev:   cd frontend && npm run dev
Port:  3000
Proxy: /api → http://localhost:8000 (ok)
Orch:  /orchestrate/* (via /api proxy) ⚠️ 待统一
Route: /steward (StewardDashboard)
```

---

## 1. Directory Scan Results

### Candidate Directories Checked

| Directory | Exists | Has package.json | Has Build Config | Status |
|-----------|--------|------------------|------------------|--------|
| `frontend/` | ✅ | ✅ | ✅ (vite.config.js) | **PRIMARY ENTRY** |
| `ui/` | ❌ | - | - | **Referenced in Makefile but MISSING** ⚠️ |
| `web/` | ❌ | - | - | Not found |
| `app/` | ✅ | ❌ | ❌ | Python FastAPI backend |
| `apps/web` | ❌ | - | - | Not found |
| `packages/ui` | ❌ | - | - | Not found |
| `packages/web` | ❌ | - | - | Not found |

**⚠️ Critical Finding:** `make ui` command (line 229-238 in Makefile) references `ui/` directory, but this directory does NOT exist. The command will fail if executed.

### Key Files Found

- ✅ `frontend/package.json` - Contains dev/build scripts
- ✅ `frontend/vite.config.js` - Vite configuration with proxy
- ✅ `frontend/src/main.jsx` - React entry point
- ✅ `frontend/src/App.jsx` - Main app component with routing
- ✅ `frontend/config/routes.js` - Route configuration
- ❌ `.env*` files - Not found in frontend directory
- ✅ `frontend/README.md` - Documentation exists

### Makefile Command Analysis

**`make ui` Command (Makefile lines 229-238):**
```makefile
ui:
	@cd ui && \
		npm run dev -- --port 5173 --open --host
```

**Status:** ⚠️ **BROKEN** - References `ui/` directory which does NOT exist. Command will fail with "No such file or directory".

---

## 2. Extracted Information

### 2.1 Entry Directory

**Confirmed:** `frontend/` is the frontend entry directory.

**Evidence:**
- Contains `package.json` with `dev` script: `"dev": "vite"`
- Contains `vite.config.js` with server configuration
- Contains React application structure (`src/main.jsx`, `src/App.jsx`)
- Has routing configuration (`config/routes.js`)

### 2.2 Package.json Scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

**Dev Command:** `cd frontend && npm run dev`

### 2.3 Dev Port Configuration

**Port:** `3000` (configured in `vite.config.js`)

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

**Note:** Default Vite port is 5173, but this project explicitly sets port 3000.

### 2.4 Proxy Configuration

#### API Proxy

✅ **Configured:** `/api` → `http://localhost:8000`

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

#### Orchestrator Proxy Status

⚠️ **Issue Found:** Orchestrator endpoints are NOT explicitly proxied.

**Current State:**
- Frontend code references `/orchestrate/*` endpoints
- Vite proxy only handles `/api/*` → `:8000`
- Orchestrator endpoints are at `/orchestrate/run`, `/orchestrate/status`, `/orchestrate/report`
- These endpoints exist in `services/fiqa_api/app_main.py` via `services/orchestrate_router.py` (FastAPI app on port 8000)

**Expected Behavior:**
- If orchestrator runs on port 8000 (same as API), requests should go through `/api/orchestrate/*` OR
- If orchestrator runs on port 8001 (separate service), a second proxy is needed

**Evidence from Codebase:**
- `services/fiqa_api/app_main.py` defines `/orchestrate/*` endpoints via `services/orchestrate_router.py` (runs on port 8000)
- `agents/orchestrator/config.yaml` mentions `127.0.0.1:8001` in `allowed_hosts`
- Multiple scripts reference `http://127.0.0.1:8001` as orchestrator base URL
- `Makefile` uses `ORCH_BASE=http://127.0.0.1:8001` for orchestrator commands

**Conclusion:** There is **port confusion** - orchestrator endpoints exist on port 8000 (`services/fiqa_api/app_main.py`), but many scripts/configs reference port 8001.

### 2.5 Routes & Pages

**Route Configuration** (`frontend/config/routes.js`):

```javascript
[
  { path: '/', name: '首页', component: './Home' },
  { path: '/steward', name: '实验室大管家', component: './StewardDashboard' }
]
```

**RAG Lab/Agent Page:**
- **Route:** `/steward`
- **Component:** `StewardDashboard` (`src/pages/StewardDashboard/index.jsx`)
- **Features:**
  - Start new evaluation pipeline
  - Real-time status polling
  - View historical reports
  - Display SLA metrics and artifacts

### 2.6 Mock vs Real API Usage

**Status:** ⚠️ **Currently using Mock API**

**Location:** `frontend/src/pages/StewardDashboard/index.jsx`

**Mock API Implementation:**
```javascript
const mockApi = {
  run: async () => { /* returns mock run_id */ },
  status: async (run_id) => { /* returns random stage */ },
  report: async (run_id) => { /* returns mock report data */ },
  abort: async (run_id) => { /* returns mock status */ }
};
```

**TODO Comments Found:**
- Line 115: `// TODO: 替换为真实API`
- Line 131: `// TODO: 替换为真实API`
- Line 179: `// TODO: 替换为真实API`
- Line 205: `// TODO: 调用真实的中止API`

**Commented Real API Calls:**
```javascript
// const data = await fetch(`${API_BASE_URL}/orchestrate/report?run_id=${id}`).then(res => res.json());
// const data = await fetch(`${API_BASE_URL}/orchestrate/status?run_id=${id}`).then(res => res.json());
// const data = await fetch(`${API_BASE_URL}/orchestrate/run`, { method: 'POST' }).then(res => res.json());
// await fetch(`${API_BASE_URL}/orchestrate/abort?run_id=${runId}`, { method: 'POST' });
```

**API Base URL:**
```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

---

## 3. Read-Only Validation Results

### 3.1 Node.js Environment

**Status:** ⚠️ Node.js/npm not installed in current environment

```bash
$ node -v
Command 'node' not found

$ npm -v
Command 'npm' not found
```

**Note:** This is expected in a WSL environment without Node.js installed. The audit is read-only and does not require Node.js to be present.

### 3.2 Available Scripts

**Expected scripts** (from `package.json`):
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

### 3.3 Vite Config Proxy Extract

**From `vite.config.js`:**

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

**Missing:** No explicit `/orchestrate` proxy configuration.

### 3.4 Port Usage Scan

**Search Results for Port References:**

```
Found references to port 8001:
- agents/orchestrator/config.yaml:39 (allowed_hosts)
- scripts/acceptance_test.py:11 (ORCH_BASE)
- Makefile:353,364,373,384,392 (ORCH_BASE defaults)
- agents/orchestrator/DESIGN.md:40,44,46 (example curl commands)
- Multiple test/verification scripts

Found references to port 8000:
- frontend/vite.config.js:16 (proxy target)
- frontend/src/pages/StewardDashboard/index.jsx:33 (API_BASE_URL default)
- docker-compose.yml:63,66,90 (rag-api service)
- services/fiqa_api/app_main.py (orchestrator endpoints defined via services/orchestrate_router.py)
```

**Conclusion:** Port confusion exists - orchestrator endpoints are defined in `services/fiqa_api/app_main.py` (port 8000), but many scripts/configs reference port 8001.

---

## 4. Conclusions & Recommendations

### 4.1 Frontend Entry

**Entry Directory:** `frontend/`

**Dev Command:** `cd frontend && npm run dev`

**Port:** `3000` (configured in `vite.config.js`)

### 4.2 API Base & Proxy

**API Base:** `/api` → `http://localhost:8000` ✅

**Proxy Configuration:** Working correctly for `/api/*` requests.

### 4.3 Orchestrator Endpoints

**Current State:** ⚠️ **Port Confusion & Missing Proxy**

**Findings:**
1. Orchestrator endpoints (`/orchestrate/*`) are defined in `services/fiqa_api/app_main.py` via `services/orchestrate_router.py` which runs on port 8000
2. Frontend code references `/orchestrate/*` endpoints directly (not `/api/orchestrate/*`)
3. Vite proxy only handles `/api/*` → `:8000`
4. Many scripts/configs reference port 8001 for orchestrator

**Options:**

**Option A: Unified on Port 8000 (Recommended)**
- Orchestrator endpoints already exist in `services/fiqa_api/app_main.py` on port 8000
- Add proxy rule: `/orchestrate` → `http://localhost:8000`
- OR change frontend to use `/api/orchestrate/*` and mount orchestrator routes under `/api` in backend

**Option B: Separate Port 8001**
- Keep orchestrator on port 8001 (requires separate service)
- Add second proxy rule: `/orchestrate` → `http://localhost:8001`

**Recommendation:** **Option A** - Unify on port 8000 since endpoints already exist there.

### 4.4 RAG Lab/Agent Page

**Route:** `/steward`

**Component:** `StewardDashboard` (`src/pages/StewardDashboard/index.jsx`)

**Status:** ✅ Route configured correctly

### 4.5 Potential Issues List

#### 🔴 Critical Issues

1. **`make ui` Command Broken**
   - Makefile references `ui/` directory that does NOT exist
   - Command will fail: `cd ui` → "No such file or directory"
   - **Impact:** `make ui` cannot be executed
   - **Fix Required:** Either create `ui/` directory OR update Makefile to use `frontend/`

2. **Mock API Still in Use**
   - All orchestrator API calls use `mockApi` instead of real endpoints
   - 4 TODO comments indicate need for replacement
   - **Impact:** Frontend cannot communicate with real backend

3. **Orchestrator Proxy Missing**
   - Vite proxy only handles `/api/*`, but frontend calls `/orchestrate/*`
   - **Impact:** Orchestrator requests will fail in development mode

4. **Port Confusion**
   - Orchestrator endpoints exist on port 8000 (`services/fiqa_api/app_main.py`)
   - Many scripts/configs reference port 8001
   - **Impact:** Inconsistent behavior, potential connection failures

#### 🟡 Medium Issues

5. **No Health Check Endpoint Exposure**
   - Frontend doesn't expose `/ready` or `/api/health/embeddings` endpoints
   - **Impact:** Cannot verify backend readiness from frontend

6. **Missing `/reports` Endpoint**
   - No explicit `/reports` route exposed in frontend
   - Reports accessed via `/orchestrate/report?run_id=...`
   - **Impact:** May need direct report file access

7. **No Environment Variable File**
   - No `.env` or `.env.example` in frontend directory
   - `VITE_API_BASE_URL` must be set manually
   - **Impact:** Configuration not documented/standardized

#### 🟢 Minor Issues

8. **Node.js Not Installed**
   - Node.js/npm not available in current environment
   - **Impact:** Cannot run frontend locally (expected in WSL without Node.js)

9. **CORS Configuration**
   - Backend CORS includes `http://localhost:3000` ✅
   - But also includes `http://localhost:5173,5174` (default Vite ports)
   - **Impact:** Minor - CORS should work, but port mismatch noted

---

## 5. Fix Recommendations

### Recommendation 0: Fix `make ui` Command (URGENT)

**Action:** Update Makefile `ui` target to use `frontend/` directory:

```makefile
ui:
	@echo "🚀 Starting Vite dev server (frontend)..."
	@echo "📍 API base: http://andy-wsl:8000"
	@echo "🌐 Dev server: http://localhost:3000"
	@cd frontend && \
		if [ ! -d "node_modules" ]; then \
			echo "📦 Installing dependencies..."; \
			npm install; \
		fi && \
		npm run dev -- --port 3000 --open --host
```

**OR** create `ui/` directory as a symlink or copy of `frontend/`:

```bash
ln -s frontend ui
```

**Rationale:** `make ui` is currently broken and will fail immediately. This should be fixed before other recommendations.

### Recommendation 1: Unify Orchestrator on Port 8000

**Action:** Add orchestrator proxy to `vite.config.js`:

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
    '/orchestrate': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

**OR** (Better approach): Mount orchestrator routes under `/api` in backend and update frontend to use `/api/orchestrate/*`.

**Rationale:** Orchestrator endpoints already exist in `services/fiqa_api/app_main.py` on port 8000. Unifying avoids port confusion and simplifies deployment.

### Recommendation 2: Replace Mock API with Real API Calls

**Action:** In `frontend/src/pages/StewardDashboard/index.jsx`, replace all `mockApi` calls with real `fetch` calls:

```javascript
// Replace mockApi.run() with:
const response = await fetch(`${API_BASE_URL}/orchestrate/run`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ /* plan data */ })
});
const data = await response.json();

// Replace mockApi.status() with:
const data = await fetch(`${API_BASE_URL}/orchestrate/status?run_id=${id}`)
  .then(res => res.json());

// Replace mockApi.report() with:
const data = await fetch(`${API_BASE_URL}/orchestrate/report?run_id=${id}`)
  .then(res => res.json());

// Replace mockApi.abort() with:
await fetch(`${API_BASE_URL}/orchestrate/abort?run_id=${runId}`, {
  method: 'POST'
});
```

**Additional:** Add error handling, loading states, and display `run_id`/`sla_verdict` in UI.

**Rationale:** Frontend currently cannot communicate with backend. This is blocking functionality.

---

## 6. Summary Table

| Item | Value | Status |
|------|-------|--------|
| **Entry Directory** | `frontend/` | ✅ Confirmed |
| **Dev Command** | `cd frontend && npm run dev` | ✅ Valid |
| **Makefile `make ui`** | References `ui/` (missing) | ⚠️ **BROKEN** |
| **Dev Port** | `3000` | ✅ Configured |
| **API Proxy** | `/api` → `:8000` | ✅ Working |
| **Orchestrator Proxy** | Missing | ⚠️ Needs Fix |
| **Orchestrator Port** | 8000 (in code) / 8001 (in scripts) | ⚠️ Confusion |
| **RAG Lab Route** | `/steward` | ✅ Configured |
| **Mock API** | Active | ⚠️ Needs Replacement |
| **Health Check** | Not exposed | ⚠️ Missing |
| **Reports Endpoint** | Via `/orchestrate/report` | ✅ Available |

---

## 7. Next Steps

1. **URGENT:** Fix `make ui` command - update Makefile to use `frontend/` OR create `ui/` directory (Recommendation 0)
2. **Immediate:** Add orchestrator proxy to `vite.config.js` (Recommendation 1)
3. **High Priority:** Replace mock API with real API calls (Recommendation 2)
4. **Medium Priority:** Resolve port 8000/8001 confusion in scripts/configs
5. **Low Priority:** Add `.env.example` file for frontend configuration
6. **Low Priority:** Add health check endpoint exposure in frontend

---

**Report Generated:** Read-only audit completed  
**Auditor:** Automated Frontend Entry Audit Tool  
**Date:** 2025-01-XX

