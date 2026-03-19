# Insurance Broker Demo Operations Package

**Generated:** 2026-03-06  
**Scope:** California Auto Insurance Broker Assistant — Demo readiness for 陈魁

---

## 1. What Was Improved

### UI / Copy Changes

| Change | File | Description |
|--------|------|-------------|
| Empty answer fallback | `ui/src/pages/DemoPage.tsx` | When `demo_fallback.json` has empty answers (e.g. snapshot ran without LLM), merge with `DEFAULT_FALLBACK_ITEMS` so offline demo shows proper broker answers |
| Offline banner | `ui/src/pages/DemoPage.tsx` | "演示模式（离线）" → "离线演示模式" badge; "Refresh Offline Pack" → "刷新离线包" |
| Offline badge styling | `ui/src/pages/DemoPage.css` | Added `.demo-offline-badge` for clearer visual emphasis |
| Header | `ui/src/pages/DemoPage.tsx` | "加州汽车保险智能助手（给陈魁 Demo）" → "加州汽车保险经纪助手" (broker-neutral) |

### Script / Checklist Changes

| Change | File | Description |
|--------|------|-------------|
| Env loading | `scripts/demo_pre_checklist.sh` | Load both `.env` and `.env.cloudrun` |
| Fallback answer check | `scripts/demo_pre_checklist.sh` | Report "Items with answers" count |
| Which path to use | `scripts/demo_pre_checklist.sh` | CHECKLIST.md now says "Use Live path" or "Use Offline path" explicitly |

### Docs / Runbook Changes

| New/Updated | Path |
|-------------|------|
| Operator runbook | `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md` |
| One-page checklist | `docs/BROKER_DEMO_CHECKLIST.md` |
| 15-min demo script | `docs/BROKER_DEMO_SCRIPT_15MIN.md` |
| Fallback script | `docs/BROKER_DEMO_FALLBACK_SCRIPT.md` |
| What to say guide | `docs/BROKER_DEMO_WHAT_TO_SAY.md` |
| Pre-demo flow | `docs/PRE_DEMO_FLOW.md` |
| Qdrant recovery | `docs/QDRANT_RECOVERY_CHECKLIST.md` |
| Broker product description | `docs/BROKER_PRODUCT_DESCRIPTION.md` |
| Invite message | `docs/BROKER_INVITE_MESSAGE.md` |
| Follow-up message | `docs/BROKER_FOLLOWUP_MESSAGE.md` |

---

## 2. Offline Demo Hardening Status

### What Is Now Smoother

- **Empty answers fixed:** Offline mode always shows broker-relevant answers (merge with DEFAULT_FALLBACK_ITEMS when JSON has empty answer)
- **Clearer offline signal:** "离线演示模式" badge + orange banner
- **Broker-neutral header:** "加州汽车保险经纪助手" works for any broker demo
- **Chinese button:** "刷新离线包" instead of "Refresh Offline Pack"

### What Is Still Awkward

- **3 questions only in Offline:** Questions 4–5 (savings, claims) have no pre-saved answers; must use Live
- **No custom questions in Offline:** Typing a question fails; user must click the 3 buttons
- **Backend error banner:** Still technical ("Backend unreachable"); acceptable for operator, not ideal for end-user

### Broker-Demo Safe?

**Yes.** Offline path is broker-demo safe. The 3 questions cover: new car coverage, registration suspended, license/compliance. All broker-relevant. Answers and citations display correctly. "复制给客户" works.

---

## 3. Broker Operator Pack

| Item | Path |
|------|------|
| Runbook | `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md` |
| Checklist | `docs/BROKER_DEMO_CHECKLIST.md` |
| Demo script | `docs/BROKER_DEMO_SCRIPT_15MIN.md` |
| Fallback script | `docs/BROKER_DEMO_FALLBACK_SCRIPT.md` |
| What to say | `docs/BROKER_DEMO_WHAT_TO_SAY.md` |

---

## 4. Broker-Facing Package

| Item | Path |
|------|------|
| Product description | `docs/BROKER_PRODUCT_DESCRIPTION.md` |
| 5 sample questions | In `BROKER_PRODUCT_DESCRIPTION.md` |
| Live vs Offline explanation | In `BROKER_PRODUCT_DESCRIPTION.md` |
| Invite message | `docs/BROKER_INVITE_MESSAGE.md` |
| Follow-up message | `docs/BROKER_FOLLOWUP_MESSAGE.md` |

---

## 5. Pre-Demo Automation

### What Is Automated

- `scripts/demo_pre_checklist.sh` — env, offline pack, backend health, live validate
- `scripts/run_demo_local.sh` — one-command start (backend + UI)
- `scripts/demo_quick_validate.sh` — 3-query live validation
- `scripts/snapshot_demo_answers.py` — refresh offline pack (when backend up)

### What Can Be Run Before Every Demo

```bash
bash scripts/demo_pre_checklist.sh
# Read results/demo_pre_checklist/<latest>/CHECKLIST.md
bash scripts/run_demo_local.sh
# Open http://localhost:5173/demo
```

### Recommended Repeatable Flow

See `docs/PRE_DEMO_FLOW.md`:

1. Run `demo_pre_checklist.sh`
2. Read CHECKLIST.md (which path: Live or Offline)
3. Run `run_demo_local.sh`
4. Confirm mode in browser (green Live / orange Offline)

---

## 6. Qdrant Recovery Prep

### Exact Commands (in order)

```bash
python3 scripts/verify_qdrant_cloud.py
bash scripts/run_demo_local.sh
# (in another terminal)
bash scripts/demo_quick_validate.sh
python3 scripts/snapshot_demo_answers.py
bash scripts/demo_pre_checklist.sh
```

### Exact Order

1. Verify Qdrant connection  
2. Start backend + UI  
3. Quick validate (3 queries)  
4. Snapshot offline pack  
5. Pre-demo checklist  

### Readiness Indicators

| Step | Indicator |
|------|------------|
| verify_qdrant_cloud | stdout: "Connection OK" |
| run_demo_local | "Backend healthy" or "Offline Fallback" |
| demo_quick_validate | REPORT.md: PASS |
| snapshot | "Saved 3 items to ..." |
| demo_pre_checklist | CHECKLIST.md: Live validate ✅ |

Full details: `docs/QDRANT_RECOVERY_CHECKLIST.md`

---

## 7. Work Split

### Cursor (AI in IDE)

- Code edits (DemoPage, demo_pre_checklist)
- Doc creation (runbook, checklist, script, broker-facing)
- One-off fixes and improvements

### OpenClaw (Automation)

- `snapshot_demo_answers.py` when backend is up (can be scheduled or triggered)
- `demo_quick_validate.sh` for live path checks
- `demo_pre_checklist.sh` before demos

### Andy (Manual)

- Start/stop demo (`run_demo_local.sh`)
- Wake Qdrant Cloud cluster (dashboard)
- Send invite / follow-up messages to 陈魁
- Run demo in meeting (click, talk)
- Decide Live vs Offline based on checklist

### Docs / Checklists / Scripts (Reduce Andy's Work)

- Pre-demo: `demo_pre_checklist.sh`, `PRE_DEMO_FLOW.md`
- During demo: `BROKER_DEMO_SCRIPT_15MIN.md`, `BROKER_DEMO_WHAT_TO_SAY.md`
- Fallback: `BROKER_DEMO_FALLBACK_SCRIPT.md`
- Post-demo: `BROKER_FOLLOWUP_MESSAGE.md`
- Qdrant recovery: `QDRANT_RECOVERY_CHECKLIST.md`
- Broker messaging: `BROKER_INVITE_MESSAGE.md`, `BROKER_FOLLOWUP_MESSAGE.md`

---

## 8. Next 15 Actions (Priority Order)

1. **Run demo once** — Use Offline path, click 3 questions, confirm UX
2. **Send invite to 陈魁** — Use `docs/BROKER_INVITE_MESSAGE.md`
3. **Schedule demo** — 15 min slot
4. **Before demo:** Run `demo_pre_checklist.sh`, read CHECKLIST.md
5. **Before demo:** Run `run_demo_local.sh`, confirm mode
6. **During demo:** Follow `BROKER_DEMO_SCRIPT_15MIN.md`
7. **If Live fails:** Follow `BROKER_DEMO_FALLBACK_SCRIPT.md`
8. **After demo:** Send follow-up using `BROKER_FOLLOWUP_MESSAGE.md`
9. **When Qdrant active:** Run `QDRANT_RECOVERY_CHECKLIST.md` sequence
10. **After Qdrant recovery:** Run `snapshot_demo_answers.py` to refresh offline pack
11. **Optional:** Add 4th/5th question to offline pack (requires code + snapshot)
12. **Optional:** Soften backend error copy for end-user (e.g. "服务暂时不可用，请使用上方推荐问题")
13. **Optional:** Document OpenClaw trigger for snapshot (e.g. after ingest)
14. **Optional:** Add `make demo-prep` target that runs checklist + prints summary
15. **Optional:** Create `scripts/demo_one_click.sh` that runs checklist → start → print URL + mode
