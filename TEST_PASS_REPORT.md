# NON-DESTRUCTIVE TEST PASS REPORT

## 1. GIT: Staged Files

```
docs/dev/port-usage-after.txt
docs/dev/port-usage.txt
scripts/ui_smoke.md
ui/src/api/orchestrate.ts
ui/src/components/chat/StewardChat.tsx
ui/src/pages/StewardDashboard/index.jsx
ui/src/theme.ts
ui/src/utils/serialize.js
ui/vite.config.ts
```

**Note:** `ui/package.json` and `ui/.gitignore` were created (minimal scaffold) but not staged per guardrails.

---

## 2. PROXY: Vite Proxy '/orchestrate' Block

```typescript
'/orchestrate': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,
    rewrite: (path) => path.replace(/^\/orchestrate\b/, '/api/experiment'),
},
```

**Status:** ✓ Rewrite rule present and correct. Path `/orchestrate/*` → `/api/experiment/*`.

---

## 3. CURL: Smoke Test Results

| Endpoint | Method | Status Code | Body (first 200B) | Result |
|----------|--------|-------------|-------------------|--------|
| `http://localhost:8000/ready` | GET | **200** | (empty) | ✓ PASS |
| `http://localhost:8000/api/experiment/run` | POST | **202** | `{"ok":true,"status":"QUEUED","job_id":"63f360ae0c8f","poll":"/api/experiment/status/63f360ae0c8f","logs":"/api/experiment/logs/63f360ae0c8f"}` | ✓ PASS |
| `http://localhost:5173/orchestrate/run` | POST | **202** | `{"ok":true,"status":"QUEUED","job_id":"7953a143bd3c","poll":"/api/experiment/status/7953a143bd3c","logs":"/api/experiment/logs/7953a143bd3c"}` | ✓ PASS |
| `http://localhost:5173/orchestrate/status?job_id=does-not-exist` | GET | **404** | `{"detail":"Not Found"}` | ✓ PASS (expected) |

**Evidence:**
- Health endpoint returns 200 ✓
- Direct backend run returns 202 (Accepted) ✓
- Proxy rewrite `/orchestrate/run` → `/api/experiment/run` returns 202 (same class) ✓
- Proxy status endpoint returns 404 for non-existent job (expected) ✓

---

## 4. POLLER: Single Poller Guard Verification

**Location:** `ui/src/pages/StewardDashboard/index.jsx`

**Key Findings:**

1. **Single Timer Reference:**
   - Line 162: `const pollIntervalRef = useRef(null);` - Single ref for timer handle

2. **Explicit Stop Function:**
   - Lines 165-170: `stopPolling()` function that:
     - Checks if `pollIntervalRef.current` exists
     - Calls `clearInterval(pollIntervalRef.current)`
     - Sets `pollIntervalRef.current = null`

3. **Guarded Start:**
   - Line 213: `handlePollStatus(id)` calls `stopPolling()` **before** starting new interval
   - Line 214: `pollIntervalRef.current = setInterval(...)` - Only one interval active

4. **Cleanup on Termination:**
   - Lines 234, 248, 253: `stopPolling()` called on failure/success/error conditions
   - Lines 184-188: `useEffect` cleanup calls `stopAllPolling()` on unmount

5. **Additional Safety:**
   - Line 262: `handleRun()` calls `stopAllPolling()` before starting new run
   - Line 313: `handleAbort()` calls `stopAllPolling()`

**Verdict:** ✓ Single poller enforcement confirmed. Timer is always stopped before starting a new one, and cleanup is handled on component unmount.

---

## 5. VERDICT

### ✅ **PASS**

**Criteria Met:**
- ✓ `ready` endpoint returns 200
- ✓ Backend run (`/api/experiment/run`) returns 202 (Accepted)
- ✓ Proxy run (`/orchestrate/run`) returns 202 (same class as backend)
- ✓ Proxy status endpoint returns expected 404 for non-existent job
- ✓ Single poller guard found and verified in `StewardDashboard/index.jsx`

**Additional Notes:**
- All new UI files staged successfully
- Proxy rewrite verified end-to-end
- No dev server started (existing instance on port 5173 used for testing)
- Minimal `ui/package.json` and `ui/.gitignore` created (not staged per guardrails)

**No commits made** (as requested).

