# Founder QA Playbook

**Status:** permanent engineering runbook and architecture contract  
**Scope:** the Camry Golden QA customer Mini Program path in isolated Cloud QA  
**Primary command:** `bash scripts/launch_golden_qa.sh --qa`  
**Release-gate order:** `docs/product/p20_founder_qa_checklist.md`  
**Production acceptance:** `docs/product/p24f_golden_production_qa_flow.md`

## 1. Purpose

Founder QA is production infrastructure: a deterministic way to validate the
complete customer workflow without manually rebuilding a case, request, token,
and Preview setup each time.

It is **not** another product flow. It is a shortcut into one freshly reset,
already-active Camry case. The product remains the normal customer journey;
Founder QA prepares that journey at a known state.

**User-facing objective:** a founder can scan one new Preview QR and reach the
active “上传保险卡” task for the current Golden Case.

**Out of scope:** production data, production deployment, production Mini
Program upload, and using a QA token against any non-QA store.

## 2. Golden QA Pipeline

```text
Camry Golden Seed
  [陈明 · 2020 Toyota Camry · active insurance-card request]
        │ reset removes only demo_name=camry_golden_qa + workbench_test=true
        ▼
Isolated QA Database (caseiq-qa / Cloud QA API)
        │ real seed + Request More + projection verification
        ▼
Golden Reset ──fails closed──► no token / do not Preview
        │ verified handoff.json (session-only; raw token never committed)
        ▼
Case Created ──► H5 task token minted ──► DevTools compile mode prepared
        │                                      │
        │                                      └─ pages/entry/entry?token=…
        ▼
Entry ──► Bootstrap ──► REQUEST_SENT ──► REQUEST_SUCCESS
  token       task load        wx.request          HTTP 2xx
        ▼
Task Home ──► Request Item ──► Receipt
```

| Stage | Inputs | Output / owner | Failure symptom |
|---|---|---|---|
| Golden Seed | `camry_golden_qa` fixture | Camry data + open insurance-card request / engineering | wrong task or no active work |
| QA database | `--qa`, Cloud QA configuration | writes only to `caseiq-qa` / platform | QA case appears in Production or no durable case |
| Golden reset | remove → seed → mint → verify | verified case, token, `handoff.json` / `launch_golden_qa.py` | `golden_reset_failed_closed` |
| Preview preparation | token + founder laptop | gitignored DevTools compile condition / `golden_qa_preview.py` | `preview_prepared=false`; stale or missing query |
| Entry | `pages/entry/entry?token=…` | token recognised and bootstrap starts / Mini Program | Start Claim, blank page, or token absent |
| Bootstrap | valid token + QA API | task plan and active case / Mini Program + API | `EARLY_EXIT`, `case_not_found`, loading does not end |
| Request | bootstrap request | `[QA_PATH] REQUEST_SENT` / Mini Program | no request log: client never attempted network |
| Response | QA API + legal domain | `[QA_PATH] REQUEST_SUCCESS` with HTTP 2xx / API | `REQUEST_FAIL`, domain/TLS/timeout/4xx/5xx |
| Task Home | task payload | actionable Task Home / Mini Program | generic home, blank shell, wrong case |
| Request Item | open insurance-card item | “上传保险卡” / projection | item absent, inactive, or wrong label |
| Receipt | completed submission | visible receipt plus broker projection / client + API | accepted data missing downstream |

`handoff.json` contains a raw session token and is intentionally gitignored.
`launch_status.json` is safe status only; it exposes a masked token.

## 3. Startup Checklist

Run these steps in order for every Founder QA session.

```bash
# 1. Build safety first; it clears any stale compile token.
cd miniapp && npm run build:gate

# 2. From repository root, reset the isolated QA Golden Case and prepare Preview.
bash scripts/launch_golden_qa.sh --qa

# 3. Optional: inspect safe launch status.
bash scripts/launch_golden_qa.sh --status
```

Stop immediately unless all are true:

- Build Gate passes; do not physical-Preview a failing package.
- launch result is `status=ready_to_scan`, target is `qa`, and
  `preview_prepared=true`.
- the output shows a fresh masked token and future `expires_at`.
- `docs/evidence/golden_qa/last_reset/handoff.json` says `target=qa` and
  `verification.ok=true`.
- DevTools uses Compile Mode **`pages/entry/entry (Golden QA session)`** with
  entry path `pages/entry/entry`; do not select a historical `service-home`
  condition.
- Mini Program profile is `apiProfile=qa`, and the request host is
  `fiqa-api-qa-g7zatxrycq-uw.a.run.app`.
- DevTools request合法域名 includes that QA host.

Then: **清缓存 → 全部清除 → 重新编译 → generate a new Preview QR → scan once**.
The QR must be generated after the token was prepared; do not reuse an old QR.

## 4. Three-Minute Debug Checklist

Debug strictly top-to-bottom. Prove the first failed stage; never guess at a
later stage.

```text
Compile Mode → Entry → Token → REQUEST_SENT → REQUEST_SUCCESS
     → Task Home → Request Item
```

| Step | Expected | Failure symptom | Typical root causes |
|---|---|---|---|
| 1. Compile Mode | Golden QA session points to `pages/entry/entry?token=…` | wrong first page, Start Claim, stale session | selected wrong condition; Build Gate cleared a prior token; old QR |
| 2. Entry | Entry renders a shell, then bootstraps | blank / `wx://not-found` | package gate skipped; page omitted; stale Preview package |
| 3. Token | safe path log reports `hasToken=true`; token is unexpired | `hasToken=false`, `case_not_found`, unauthorised | missing query; expired/stale token; reset and API use different stores |
| 4. `REQUEST_SENT` | `[QA_PATH] REQUEST_SENT` appears | no sent log | Entry/bootstrap exited early; client configuration or navigation issue |
| 5. `REQUEST_SUCCESS` | `[QA_PATH] REQUEST_SUCCESS` and HTTP 2xx | `REQUEST_FAIL`, timeout, 4xx/5xx | wrong API profile/host; legal domain, TLS, CORS, auth, or QA API outage |
| 6. Task Home | one active Camry case and actionable task shell | generic home, infinite loading, wrong case | malformed bootstrap payload; resume/token binding failure; client routing defect |
| 7. Request Item | “上传保险卡” is active | no item / wrong label / inactive | seed or Request More projection failed; wrong case; stale client payload |

Use Remote Debug Console logs only in their safe form:

```text
[QA_PATH] ENTRY { hasToken: true, ... }
[QA_PATH] BOOTSTRAP { ... }
[QA_PATH] REQUEST_SENT { method: "GET", path: "/api/h5/tasks/{token}/intake" }
[QA_PATH] REQUEST_SUCCESS { httpStatus: 200, ... }
```

Never paste raw tokens, customer data, or request bodies into evidence.

## 5. Lessons Learned (P36)

| Failure | Symptom | Root cause | Fix | Prevention |
|---|---|---|---|---|
| Wrong Compile Mode | QA opened an unrelated page or Build Gate failed | DevTools condition selected `service-home` or other historic entry | choose Golden QA Entry; clear cache and full compile | startup checklist requires the named compile mode |
| Missing token | Entry starts a fresh flow or `hasToken=false` | token was never injected, was cleared, or old QR was scanned | rerun launch locally; create a new QR | do not reuse QR; verify `preview_prepared=true` |
| Golden reset failed | no safe ready state, `golden_reset_failed_closed` | seed, mint, or verification did not complete | fix reported reset cause, then rerun once | reset is fail-closed; never Preview without verified handoff |
| Seed wrote to Production | QA test data contaminated Production | QA clients or storage URLs historically pointed at Production | freeze Cloud QA host and prove QA/Production separation | QA and Production never share API URL, DB, credentials, or client profile |
| `case_not_found` | bootstrap or intake returns 404 | stale token, reset to a different store, or remote reset could not write laptop compile config | ensure reset target is QA, token is current, and local Preview prep completed | inspect target + handoff; Cloud Run must not claim `preview_prepared=true` |
| Pipeline treated as separate parts | time lost debugging screens before seed/token | reset, Preview, client route, and API response were diagnosed independently | use the ordered pipeline and first-failure rule | Golden QA is one pipeline; one broken stage breaks the flow |

P36 also established the durable isolation boundary: QA clients use
`https://fiqa-api-qa-g7zatxrycq-uw.a.run.app`; Production remains a different
host and database. See `docs/evidence/p36_t7_closeout_2026_07_21.md`.

## 6. Engineering Principles

1. Never debug by guessing; trace the execution path first.
2. Golden QA is one pipeline, not independent scripts and screens.
3. QA and Production must never share storage, host, credentials, or tokens.
4. One broken stage breaks the whole QA flow; find the first failed stage.
5. A reset is not ready until seed, token mint, and verification all pass.
6. A Preview is not valid until the current token is in its entry query.
7. Build safety precedes Preview; a package regression is a release blocker.
8. Logs and evidence are secret-free: record booleans, codes, hosts, paths,
   timestamps, and HTTP status—never raw tokens or PII.
9. Founder QA evidence supplements, never replaces, the P20 hard gates and
   Golden Production QA acceptance.

## 7. Operator Runbook

### Daily startup

1. Run the Startup Checklist.
2. In DevTools, select the Golden QA compile mode, clear all cache, full
   compile, and create a new Preview QR.
3. On the phone, scan once and wait for Task Home. Do not manually substitute a
   case ID or token.

### Phone verification

Expected visible sequence:

```text
Entry shell → Task Home → “上传保险卡” request item → submit → receipt
```

Expected screenshots/evidence:

- Task Home showing the active Camry case and one clear next action.
- Request item showing “上传保险卡”.
- Receipt after a real supported submission.
- Broker authoritative view showing the same accepted outcome
  (read-after-write).

Expected console evidence:

```text
[QA_PATH] ENTRY ... hasToken: true
[QA_PATH] BOOTSTRAP ...
[QA_PATH] REQUEST_SENT ...
[QA_PATH] REQUEST_SUCCESS ... httpStatus: 200
```

Expected HTTP evidence:

- task bootstrap/intake: HTTP 200;
- supported submission: HTTP 2xx;
- no `case_not_found`, token error, domain error, or retry-induced duplicate.

Record the date, masked token, case ID, environment/host, screenshots, safe
console sequence, HTTP status, and final GO/NO-GO in the relevant evidence
file. A blank screen is an automatic FAIL.

## 8. Recovery Playbook

**Target recovery time: 10–15 minutes.**

```text
0–2 min   Read launch status and the first missing QA_PATH event.
2–5 min   Confirm QA host/profile/database and the current compile mode.
5–10 min  Rerun Golden launch; verify fresh token + preview_prepared=true.
10–15 min Clear cache, full compile, new QR, retest only the failed stage onward.
```

Isolation and recovery order:

1. Check `bash scripts/launch_golden_qa.sh --status`.
2. If reset is failed or verification is not green, fix that error before
   touching the Mini Program; rerun `bash scripts/launch_golden_qa.sh --qa`.
3. If reset is ready but Preview is not prepared, run the command from the
   founder laptop. A remote API cannot write local DevTools configuration.
4. If no `REQUEST_SENT`, inspect compile mode, Entry, and token.
5. If sent but not successful, inspect QA host/profile, legal domain, and the
   safe `REQUEST_FAIL` code/status.
6. If the HTTP request succeeds but UI is wrong, compare Task Home and request
   item with the verified Golden projection; inspect the client only then.

Stop and escalate when the reset remains fail-closed after its built-in one
reseed recovery, the QA host/database cannot be proven, or any evidence points
to Production. Do not “try Production” to unblock QA.

## 9. Maintenance

### Update the Golden Seed

Change the fixture only when the supported production journey changes. Update
the seed, expected projection oracle, focused tests, and this playbook’s
expected Task Home/request item together. Preserve the tags
`demo_name=camry_golden_qa` and `workbench_test=true` so reset deletes only
test cases.

### Rotate QA data

Use `bash scripts/launch_golden_qa.sh --qa` to rotate the Golden Case and
token. Treat `handoff.json` and DevTools private configuration as session-only;
never commit them. Expired, stale, or unknown tokens are discarded—not repaired
in place.

### Add a Founder QA scenario

1. Define one supported user outcome and its deterministic initial state.
2. Give it isolated QA-only tags, seed data, token/entry path, projection
   oracle, and cleanup semantics.
3. Add a pipeline row, first-failure debug checks, safe logs, and automated
   reset/verification before giving it to a founder.
4. Keep the Camry scenario unchanged and run it after the addition.

Do not turn Golden QA into a scenario picker or a second product surface. New
scenarios must be justified by a repeated Founder QA need and must not weaken
the existing deterministic Camry path.
