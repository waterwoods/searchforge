# P19H-3f-2 — Lane Switch Confirm Card (Add Car → Claim)

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Bug fix + product boundary — no schema migration

---

## 1. Symptom

User in active **Add Car** flow sends:

> 我现在要进行理赔

System incorrectly replied:

> 收到，我已记录您的其他问题。我们先完成当前请求，陈总会人工跟进其他事项。

This violated the product rule: explicit Claim start intent must not be swallowed by Add Car as a generic “other question.”

---

## 2. Root cause

| Step | What happened |
|------|----------------|
| 1 | Active Add Car case exists for user |
| 2 | `classify_wecom_intent("我现在要进行理赔")` → `claim_intake` / high / `menu_text` |
| 3 | `is_claim_guided_start_message("我现在要进行理赔")` → **False** (phrase missing from explicit markers) |
| 4 | `should_route_claim_guided_workflow()` → **False** |
| 5 | Message fell through to `minimal_lanes` → `secondary_topic_deferred` |
| 6 | `build_secondary_topic_deferred_reply()` emitted “先完成当前请求…” |

**Likely cause confirmed:** routing gate required `is_claim_guided_start_message()` but the phrase list was incomplete; non-matching high-confidence claim text was deferred instead of lane-switch prompted.

---

## 3. Product rule

1. Random chat / photo → no case  
2. Start Card / Start Ceremony → formal workflow  
3. Pre-Start → not in broker default queue  
4. **Active Add Car + explicit Claim start** → must not defer  
5. Cross-lane switch is a big action → **confirm card first**, not immediate Claim  
6. Only after user confirms → create Claim + Claim Start Card  
7. Add Car case retained (paused), not deleted  

---

## 4. Fix summary

| Area | Change |
|------|--------|
| `claim_basics.py` | Expanded explicit start markers (`我现在要进行理赔`, `进行理赔`, `我要记录事故`, …); tightened non-explicit accident phrases to holding ack |
| `claim_basics.py` | Lane switch confirm = `开始事故记录` (not `开始理赔` as confirm) |
| `claim_basics.py` | `ingest_claim_lane_switch_confirm()` creates Claim + Start Card after confirm |
| `case_store.py` | `lane_switch_pending` on case JSON for idempotency |
| `reply.py` | New confirm card copy + msgmenu buttons |
| `intent.py` | Click ids: `lane_switch_start_claim`, `lane_switch_continue_add_car` |
| `slice.py` | Route lane-switch clicks + menu payload on confirm card |

---

## 5. Confirm card copy

```text
您现在是想开始一份新的事故/理赔记录吗？

如果是，我会先暂停当前加车资料收集，并开始事故记录。

这不代表已经向保险公司正式报案。

[开始事故记录]  [继续加车]
```

---

## 6. Start Card after confirm

Only after `[开始事故记录]` / “开始事故记录”:

- `【事故记录已开始 ✅】`
- 陈总办公室值班助手
- 有没有受伤 + injury quick replies
- Claim in Workbench default queue
- Add Car case preserved

---

## 7. Cancel path

`[继续加车]` / “继续加车”:

- No Claim created  
- Reply: `好的，我们继续完成加车资料。`  
- Clears `lane_switch_pending`  

---

## 8. Idempotency

Stored on Add Car case `lane_switch_pending`:

```json
{
  "pending_lane_switch": "add_car_to_claim",
  "source_case_id": "<add_car_case_id>",
  "created_at": "...",
  "confirmed_claim_id": "<claim_id after confirm>"
}
```

- Repeated explicit intent while pending → re-send confirm card  
- Repeated confirm → same Claim, no duplicate  
- Cancel clears pending  

---

## 9. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3f2_lane_switch_confirm_card.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3f1_case_boundary_policy.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3f1c_start_card_only_intake_policy.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3f2_true_end_card_on_broker_done.py -q
PYTHONPATH=. python3 -m pytest tests -q -k "claim"
PYTHONPATH=. python3 -m pytest tests -q -k "h5"
```

All **PASS** before deploy.

---

## 10. Deploy

| Item | Value |
|------|-------|
| Backend | Cloud Run `fiqa-api` via `bash scripts/deploy_paid_pilot.sh` |
| Frontend | **No change** — backend-only fix |
| Smoke script | `scripts/p19h3f2_deploy_lane_switch_smoke.py` |

Post-deploy GIT_SHA: `d2e5a10c9` (image built from working tree pre-commit; revision `fiqa-api-00185-nlb`)

---

## 11. Smoke results

| Smoke | Expected | Result |
|-------|----------|--------|
| A — `我现在要进行理赔` | Confirm card, no Start Card | **PASS** |
| B — `开始事故记录` | Claim + Start Card, Add Car preserved | **PASS** |
| C — `继续加车` | No Claim, continue Add Car | **PASS** |
| D — Costco 追尾 narrative | Holding ack, no confirm | **PASS** |
| E — Regression | Solo 我要理赔 + photo intake | **PASS** |

Evidence JSON: `docs/evidence/p19h3f2_smoke_run_3f2_ls_191720.json` — `all_pass: true`

---

## 12. Constraints preserved

- No schema / no new DB table  
- No random auto Claim  
- No fault / coverage / carrier filing  
- No auto close  
- Start Card only policy preserved  
- Raw inbound hidden from default queue preserved  
- `broker_done` / End Card regression preserved  

---

## 13. Known limitations

- `lane_switch_pending` is case JSON only (no TTL); confirm is also intent-based on next message  
- Broker contact option removed from confirm card (simplified to 2-button confirm/cancel per P19H-3f-2 spec)  
- Broad accident phrases (`我撞车了`, `我发生车祸了`) no longer auto-start Claim without explicit ceremony phrase  

---

## 14. Next recommended prompt

**Pilot Demo Script / Chen readiness** — end-to-end demo path with Add Car interrupt → confirm → Claim Start Card on phone.
