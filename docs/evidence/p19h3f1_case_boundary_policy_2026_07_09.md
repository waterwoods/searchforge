# P19H-3f-1 — Case Boundary Policy + Smooth New Customer Claim Flow

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Scope:** P19H-3f-1A — Case Boundary + Holding + Start Card + new customer WeChat claim smoke  
**Deploy:** No

---

## 1. Goal

Enforce the Claim Story Recorder trust boundary:

> Random chat / random photo does **not** automatically create a formal Claim case.  
> A formal case begins only through explicit intent or controlled task entry.

After explicit start, the WeChat flow stays smooth: injury quick replies → one next step → story → photo ack → timeline + brief.

---

## 2. Core trust rule

| State | Customer sees | System |
|-------|---------------|--------|
| Consultation | Safe Q&A | No `service_lane=claim` |
| Holding / 待确认 | 【尚未开始事故记录】 | `wecom_media_intake` or holding ack only |
| Formal record | 【事故记录已开始 ✅】 | `service_lane=claim` + timeline |

---

## 3. What can create a formal Claim case

- Explicit start text: 我要理赔 / 开始理赔 / 我撞车了 / 新事故 / …
- Controlled task entry: H5 token on existing case; injury quick reply **inside** active Claim
- Lane-switch confirm during Add Vehicle: 开始理赔
- Menu / Start Card clicks (existing)

---

## 4. What cannot create a formal Claim case

- Random photo only → `wecom_media_intake` holding
- Random accident narrative (e.g. 昨晚 Costco 被追尾了) → holding ack
- Insurance question only (e.g. 这种情况要不要报保险？) → safe consultation reply
- Injury quick reply with no open Claim → holding gate (no `_create_claim_case()`)
- Passive accident keywords without explicit start

**Removed:** `should_route_claim_guided_workflow()` fallback via `has_accident_basics_signals()` alone.

---

## 5. Holding behavior

**Text / ambiguous narrative** — `ingest_claim_holding_ack()`:

```text
【尚未开始事故记录】
我已收到这条信息，但还没有建立正式事故记录。
如果这是理赔相关，请回复「我要理赔」或点击「开始记录这次事故」。
如果只是咨询问题，您可以继续直接问。
```

**Random photo** — tier C media reply uses same holding copy; attaches to `wecom_media_intake`, not Claim.

---

## 6. Start Card copy

After explicit formal start:

```text
【事故记录已开始 ✅】
我是陈总办公室的值班助手。
我会先帮陈总记录这次事故，您可以直接在微信里发文字、照片或语音。
陈总会人工确认后联系您。
请先确认：您和车上的人有没有受伤？
这只是事故资料记录，不代表已经向保险公司正式报案。
```

Injury quick replies: [没有受伤] [有人受伤] [不确定]

---

## 7. End Card

Deferred — not in 3f-1A scope.

---

## 8. Injury quick reply gate

| Context | Behavior |
|---------|----------|
| No active Claim | Holding gate — no case creation |
| Active Claim + no_injury | `injury_status=no`, prompt for story |
| Active Claim + has_injury | manual_handle, safety reply |
| Active Claim + unknown | `injury_status=unknown`, story prompt |

---

## 9. Workbench labeling

- Claim rows: `Claim · 记录中` / `Claim · Broker Review`
- Unassigned WeCom media: `待确认材料 · 未分配微信资料 · 不是正式 case`
- UI lane tag: `待确认材料` (was WeCom Photo / UNASSIGNED)

---

## 10. New customer simulation

| Scenario | Result |
|----------|--------|
| NC-1 random photo | No Claim case; holding copy |
| NC-2 Costco narrative | Holding ack; no Claim |
| NC-3 我要理赔 | Claim created; Start Card |
| NC-4 start → injury → story | Timeline + basics_complete |
| NC-5 injury alone | Holding gate |
| NC-6 insurance question | Safe reply; no Claim |

Simulator fixtures: `workflow_scenario_simulator.py` (NC-2..NC-6).

---

## 11. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3f1_case_boundary_policy.py -q
```

17 tests — boundary policy, timeline/brief after explicit start, scenarios NC-2..NC-6.

---

## 12. Regressions

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3e1_claim_timeline_case_brief.py -q   # PASS
PYTHONPATH=. python3 -m pytest tests/test_p19h3d_wecom_claim_image_binding.py -q    # PASS
PYTHONPATH=. python3 -m pytest tests/test_p19h3c_r3_claim_identity_resolver_foundation.py -q  # PASS
PYTHONPATH=. python3 -m pytest tests/test_p19h3c3c_h5_claim_slot_persistence.py -q  # PASS
PYTHONPATH=. python3 -m pytest tests/test_p19h2_claim_wecom_basics.py -q            # PASS
PYTHONPATH=. python3 -m pytest tests -q -k "claim" --ignore=tests/e2e              # PASS
PYTHONPATH=. python3 -m pytest tests -q -k "h5" --ignore=tests/e2e                # PASS
```

Updated existing tests that assumed narrative auto-starts Claim (now require explicit 我要理赔 + injury gate).

---

## 13. Frontend build

```bash
cd ui && npm run build   # PASS
```

---

## 14. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api   # PASS
```

---

## 15. Constraints honored

- No schema migration / no new DB tables
- No OCR / ASR / damage AI
- No fault / coverage / carrier filing automation
- No `highlights[]` / no LLM brief
- No full timeline UI / no complex progress card
- No deploy

---

## 16. Known limitations

- Holding Card buttons (开始记录这次事故 / 只是咨询) deferred — text-only for 3f-1A
- NC-1 image scenario tested via unit test with mocked download; not in `run_all_predefined_scenarios` (needs media mocks)
- Broker-promoted holding → formal case (Workbench) — future

---

## 17. Next recommended prompt

1. **P19H-3f-1 Deploy + New Customer Claim Boundary Smoke**
2. **P19H-3e-1b Claim Case Brief Highlights**

---

## 18. GO / HOLD

**GO** — Case boundary policy enforced; explicit start required; holding + Start Card copy shipped; tests + regressions + QA gate pass.

**STOP** — No deploy in this sprint.
