# P25 — Launch Golden QA (One-Click Founder Release Tool)

**Date:** 2026-07-18  
**Scope:** Internal release / verification tool only — not a customer or broker product feature.  
**North Star:** Reduce Founder Golden QA to one button → reset → token → Preview prep → scan once.  
**P26:** Not started.

---

## 1. Architecture

```
Founder (Broker Workbench · QA Tools)
        │  POST /api/inbox/support/launch-golden-qa
        │  (support auth + ENABLE_GOLDEN_QA_LAUNCH / local ENV)
        ▼
API / CLI  scripts/launch_golden_qa.py
        │  1) lock (reject concurrent)
        │  2) reset_camry_golden_qa --reseed
        │  3) prepare_devtools_preview(token)
        ▼
gitignored miniapp/project.private.config.json
        │  compile condition: pages/entry/entry?token=…
        ▼
Founder DevTools → Preview → scan once → Golden QA

Build safety:
  npm run build:gate  →  clearGoldenSessionTokensFromPrivateConfig()
                      →  fail-closed if clear fails
                      →  then evaluate gate (stale token = FAIL)
```

**Dual Preview path**

| Path | When | Writes private config on |
|------|------|---------------------------|
| API / CLI `prepare_devtools_preview` | Launch runs on Founder machine (`--local` / local API) | Laptop |
| Vite DEV `POST /__qa__/prepare-golden-preview` | Cloud reset OK but Preview inject on remote host fails | Laptop (DEV UI only) |

Durable status (no raw token): `docs/evidence/golden_qa/last_reset/launch_status.json`  
Session handoff (raw token, gitignored): `docs/evidence/golden_qa/last_reset/handoff.json`

**Visibility gates**

- UI: `isQaToolsEnabled()` → Vite `DEV` or `VITE_ENABLE_QA_TOOLS=1` (never default prod customer builds)
- API: `assert_support_export_authorized` + `golden_qa_launch_enabled()` (`ENABLE_GOLDEN_QA_LAUNCH=1` or local/dev `ENV`)

---

## 2. Files changed

| File | Role |
|------|------|
| `scripts/golden_qa_preview.py` | Inject / clear DevTools compile query |
| `scripts/launch_golden_qa.py` | Launch orchestration, lock, public status |
| `scripts/launch_golden_qa.sh` | CLI wrapper |
| `services/fiqa_api/routes/inbox_triage.py` | Support GET status + POST launch |
| `ui/src/features/intake/components/LaunchGoldenQaPanel.tsx` | QA Tools card |
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | Mount panel when QA tools enabled |
| `ui/src/api/inboxTriage.ts` | Client helpers |
| `ui/src/config/productSurface.ts` | `isQaToolsEnabled()` |
| `ui/vite.goldenQaPlugin.ts` | DEV-only local Preview inject |
| `ui/vite.config.ts` | Register plugin in development |
| `miniapp/scripts/build_gate.ts` | Clear session tokens before gate (fail-closed) |
| `tests/test_launch_golden_qa.py` | Prepare/clear, multi-launch, concurrent lock |

---

## 3. UI

Workbench → **QA Tools** (DEV / `VITE_ENABLE_QA_TOOLS=1` only):

- Button: **Launch Golden QA**
- Status: Idle → Running Reset… → Preparing Preview… → Ready to Scan
- Latest Case ID / Token expiration / Last run / Latest QA report path
- Never renders raw token (masked only; one-shot `devtools_launch_query` used only for local inject)

Reference mock (panel layout): `p25_launch_golden_qa_panel.png` (same folder).

---

## 4. Verification evidence

### Unit tests

```text
PYTHONPATH=. python3 -m pytest tests/test_launch_golden_qa.py -q
....  (4 passed)
```

### Multi-launch (local)

| Launch | Case ID | Token masked | Preview prepared |
|--------|---------|--------------|------------------|
| 1 | `case_6ff28347c08c` | `h5t1.eyJ…ee24f4` | true |
| 2 | `case_f25468e58b50` | `h5t1.eyJ…3a6999` | true |

- Fresh case + token each click  
- Preview compile query updated to latest token  
- Concurrent in-flight launch → `ok=false`, `failure_reason=launch_already_in_progress`

### Build Gate (token present → clear → PASS)

1. After launch 2: `project.private.config.json` entry query contained `token=h5t1.…`  
2. `cd miniapp && npm run build:gate` → **PASSED**  
3. After gate: `token_present False` (fail-closed clear ran before evaluation)

### Miniapp tests

`npm test` in miniapp: 304 pass (includes Build Gate stale-token evaluation tests).

---

## 5. Failure scenarios

| Scenario | Behavior |
|----------|----------|
| Reset fails | Status `failed`; concise `failure_reason`; no ready state |
| Preview inject fails (e.g. Cloud Run host) | Reset still OK → `ready_to_scan` + warning; UI may apply Vite DEV inject |
| Concurrent second click | Rejected: `launch_already_in_progress` |
| Launch disabled in prod-like ENV | HTTP 403 `golden_qa_launch_disabled` |
| Support auth missing (when key configured) | Existing support gate rejects |
| Build Gate clear fails | Gate **FAIL** (fail-closed); no package with leaked token |
| Stale token left uncleared | Gate evaluation still fails on `token=` in compile conditions |

---

## 6. Remaining risks

1. **Cloud Run launch + remote Preview:** API host cannot write Founder’s DevTools file — rely on CLI on laptop or Vite DEV inject.  
2. **Prod Workbench visibility:** Requires explicit `VITE_ENABLE_QA_TOOLS=1` + backend `ENABLE_GOLDEN_QA_LAUNCH=1` + support key if set.  
3. **One-shot query in API response:** Support-authorized only; UI must not display it (current panel does not).  
4. **In-process lock only:** Multi-worker Cloud Run may need redis/file lock later if concurrent founders hit different instances (acceptable for single-Founder QA).

---

## 7. Recommendation

**GO for Founder use via:**

```bash
bash scripts/launch_golden_qa.sh --qa
# or Workbench QA Tools → Launch Golden QA (local DEV UI + QA API)
```

Then: DevTools compile mode「pages/entry/entry (Golden QA session)」→ 清缓存 → Preview → scan once → run `p24f` Golden Production QA.

Do **not** start P26. Treat this as the release-verification shortcut only; product journey work stays on the Golden Case path.

---

## Operator quick ref

```bash
bash scripts/launch_golden_qa.sh --qa
bash scripts/launch_golden_qa.sh --local
bash scripts/launch_golden_qa.sh --status
bash scripts/launch_golden_qa.sh --clear-preview
cd miniapp && npm run build:gate   # auto-clears session tokens first
```
