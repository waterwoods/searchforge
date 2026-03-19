# Offline Snapshot Alignment Sprint Report

## 1. Issue targeted

**What:** Validate and snapshot were separate steps. Andy had to manually run `snapshot_demo_answers.py` after `demo_quick_validate.sh` PASS. If forgotten, `demo_fallback.json` stayed stale. If snapshot ran before validation, offline pack could contain bad answers (e.g. Q2 without $14 fee).

**Why it mattered most:** Offline mode is the demo-safe fallback. When live fails, brokers click the 5 questions and get preset answers. If those answers were outdated or missing key content (e.g. Q2 $14), the fallback was less trustworthy. The manual two-step flow was fragile and easy to forget.

## 2. Changes made

| File | Change |
|------|--------|
| `scripts/demo_quick_validate.sh` | On validation PASS, runs `snapshot_demo_answers.py --port $PORT` to refresh `demo_fallback.json`. One command = validate + refresh offline pack. |
| `scripts/snapshot_demo_answers.py` | Added `--port` argument (default 8001) for consistency with `demo_quick_validate.sh`. |
| `scripts/demo_pre_checklist.sh` | Fixed 3→5: offline pack check (items ≥5, answers ≥5), "3 recommended questions" → "5 recommended questions". |
| `scripts/demo_prep_one_command.sh` | Fixed 3→5: "Validating 3 demo questions" → "5", "3 recommended questions" → "5" in fallback instructions. |
| `docs/DEMO_OFFLINE_PACK.md` | Fixed 3→5 throughout; added "Recommended" path: run `demo_quick_validate.sh` for auto-refresh on PASS. |
| `docs/BROKER_DEMO_OPERATOR_RUNBOOK.md` | Added note: `demo_quick_validate.sh` auto-runs snapshot on PASS. |

**Why it helps:** Running `bash scripts/demo_quick_validate.sh` with backend up now validates Q1–Q5 and, on PASS, refreshes `demo_fallback.json` in one step. Offline pack stays aligned with validated scenarios. No separate snapshot command to remember.

## 3. Re-test results

**What was tested:** Ran `bash scripts/demo_quick_validate.sh` with backend on 8001.

**Result:**
- Validation: 5/5 ok, Q2 $14=OK, Q5 claims=OK, Q4 discounts=OK
- Snapshot: Saved 5 items to `demo_fallback.json`, 25 sources
- Exit code: 0

**Before vs after:**

| Aspect | Before | After |
|--------|--------|-------|
| Offline Q2 answer | "具体的恢复费用在提供的上下文中没有明确说明" (no $14) | "恢复费约 $14（以 DMV 官网为准）" |
| Workflow | 2 steps: validate → manual snapshot | 1 step: validate (snapshot on PASS) |
| Alignment confidence | Manual, easy to forget | Automatic on every PASS |

**Better:** Offline pack now reflects validated answers. Q2 has $14 fee. One command refreshes both validation report and offline pack.

## 4. Operator impact

**Andy no longer needs to:**
- Manually run `python3 scripts/snapshot_demo_answers.py` after validation
- Remember the two-step flow
- Worry that offline pack is stale after validation PASS

**Cursor / OpenClaw can now:**
- Run `bash scripts/demo_quick_validate.sh` once; if PASS, offline pack is refreshed automatically
- Use the same command for pre-demo prep and offline-pack refresh

**New default pre-demo offline-refresh path:**
```bash
bash scripts/demo_quick_validate.sh
```
(Backend must be running. On PASS, `demo_fallback.json` is updated.)

For pre-demo checklist:
```bash
bash scripts/demo_pre_checklist.sh
```
(This invokes `demo_quick_validate.sh`, so offline pack is refreshed when validation passes.)

## 5. Future extraction note

**Reusable:**
- Validate-then-snapshot pattern: validation gates snapshot; snapshot only runs on PASS
- `--port` on snapshot script for consistency with validation
- Single entry point for "validate + refresh offline"

**California-specific:**
- The 5 questions, Q2 $14, Q4/Q5 checks are broker-demo specific
- `demo_fallback.json` structure (question, answer, sources) could become a "scenario pack" format
- Later: region-specific fallback config (e.g. `configs/regions/ca_auto_insurance.json`) with questions + fallback answers

**No heavy architecture changes.** Documentation only.

## 6. Remaining blocker(s)

None for this sprint. Offline pack alignment is addressed.

## 7. Recommended next sprint

**Target:** Add a lightweight "offline pack freshness" indicator in the UI (e.g. show `generated_at` from `demo_fallback.json` in the offline banner) so Andy can see at a glance when the pack was last refreshed.

**Why:** Increases confidence that offline mode is current. Low effort, high visibility.
