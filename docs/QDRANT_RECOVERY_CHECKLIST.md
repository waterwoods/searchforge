# Qdrant Recovery Checklist

Use when Qdrant Cloud cluster is active again (after pause/404). All steps are in-repo; no external dashboard actions in this checklist.

## Prerequisites (Andy does manually)

- [ ] Qdrant Cloud cluster is **active** (not paused)
- [ ] QDRANT_URL and QDRANT_API_KEY in `.env.cloudrun` or `.env`

## Recovery Sequence

### 1. Verify Qdrant connection

```bash
python3 scripts/verify_qdrant_cloud.py
```

**Expected:** Connection OK, collection exists.

**If fail:** Check Qdrant dashboard, cluster status, env vars.

---

### 2. Start backend

```bash
bash scripts/run_demo_local.sh
```

Or start backend only:

```bash
TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001
```

**Watch:** Terminal for startup logs. Look for Qdrant connection messages.

---

### 3. Quick validate (live path)

In another terminal:

```bash
bash scripts/demo_quick_validate.sh
```

**Expected:** Report in `results/demo_quick_validate/<timestamp>/REPORT.md` with PASS.

**If fail:** Check `validate_log.txt` and `q1.json`, `q2.json`, `q3.json` for error details. Common: 404 (collection missing), timeout (cluster cold).

---

### 4. Snapshot offline pack

```bash
python3 scripts/snapshot_demo_answers.py
```

**Expected:** `Saved 3 items to ui/src/assets/demo_fallback.json`

**If fail:** Backend may not be up, or Qdrant/LLM returned empty. Offline demo still works via DEFAULT_FALLBACK_ITEMS.

---

### 5. Pre-demo checklist

```bash
bash scripts/demo_pre_checklist.sh
```

**Expected:** Live validate ✅, "Use Live path" in CHECKLIST.md.

---

### 6. Demo readiness

- Open http://localhost:5173/demo
- Status bar should show **Live** (green)
- Ask any of the 5 questions — should return real-time results

---

## Exact Command Order

```bash
# 1. Verify Qdrant
python3 scripts/verify_qdrant_cloud.py

# 2. Start demo (backend + UI)
bash scripts/run_demo_local.sh
# Wait for "Demo ready"

# 3. In another terminal: validate
bash scripts/demo_quick_validate.sh

# 4. Snapshot offline pack
python3 scripts/snapshot_demo_answers.py

# 5. Pre-demo checklist
bash scripts/demo_pre_checklist.sh
```

---

## Logs / Output to Watch

| Step | Where | What to look for |
|------|-------|------------------|
| verify_qdrant_cloud | stdout | "Connection OK" or error |
| run_demo_local | terminal | "Backend healthy" or "Offline Fallback" |
| demo_quick_validate | REPORT.md | PASS / FAIL |
| snapshot_demo_answers | stdout | "Saved 3 items" |
| demo_pre_checklist | CHECKLIST.md | Live validate ✅ |

---

## If Something Fails

| Failure | Next step |
|---------|-----------|
| verify_qdrant_cloud fails | Check Qdrant dashboard, cluster active, env vars |
| Backend won't start | Check logs for Qdrant/embedding errors |
| demo_quick_validate FAIL | Inspect q1.json/q2.json/q3.json for API error |
| Snapshot fails | Offline demo still works; retry when backend + Qdrant OK |
