# P19H-2 — Claim WeCom Start Card + Accident Basics + C1 Evidence

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Claim WeCom guided basics — local tests + QA gate  
**Verdict:** **LOCAL PASS** · **REGRESSION PASS** · **QA GATE PASS** · **NO DEPLOY**

---

## 1. Goal

First Claim WeCom guided loop segment: start/safety card → accident basics collection → C1 Stage Complete. No H5 photos, no Workbench drawer, no OCR.

**Prerequisites:** P19H-0 (`21e9573`), P19H-1 (`d4a8d45`)

---

## 2. Source docs

| Doc | Purpose |
|-----|---------|
| `docs/p19h0_claim_case_builder_state_machine_recon.md` | Claim journey / C1 copy |
| `docs/evidence/p19h1_claim_state_machine_foundation_2026_07_08.md` | Phase predicates / guardrails |

---

## 3. Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/claim_basics.py` | **NEW** — routing, ingest, case create/update |
| `services/fiqa_api/wecom/claim_extractors.py` | **NEW** — accident basics extraction |
| `services/fiqa_api/wecom/reply.py` | Claim start / missing / C1 / question-safe replies |
| `services/fiqa_api/wecom/slice.py` | Route before minimal claim_lite lane |
| `services/fiqa_api/inbox_triage/case_store.py` | `update_claim_workflow_state()` |
| `tests/test_p19h2_claim_wecom_basics.py` | **NEW** — 14 tests |

---

## 4. Behavior implemented

| Trigger | Behavior |
|---------|----------|
| `我要理赔` / `我撞车了` / guided start | Create `service_lane=claim` case → Start Card |
| Full basics in one message | Save 3 fields → C1 card → `accident_basics_complete` |
| Partial basics | Merge fields → missing-items reply (no C1) |
| Multi-turn merge | Accumulate until 3 fields → C1 |
| `accident_basics_complete` + `进度`/`继续` | Step-1-done / next-photos reply (no generic menu, no H5 link) |
| `出事故了怎么办` (question-only) | Safe reply, no guided case |
| Substantive + question (405 撞车 怎么办) | **Unchanged** — claim_lite minimal lane |

---

## 5. Claim start triggers

`我要理赔` · `我撞车了` · `出事故了` · `发生事故了` · `车祸了` · `事故理赔` · `file a claim` · `claim` / `accident` (short)

---

## 6. Safety / Start Card copy

- Title: `【理赔资料收集】`
- Safety check (人是否安全)
- Injury → emergency + 陈总
- Asks: 事故时间 / 地点 / 简单描述
- Disclaimer: `这不代表已经正式报案`

---

## 7. Accident basics fields

| Field | Extraction |
|-------|------------|
| `accident_datetime` | 今天/昨天/刚才/上午/点/月/日期 patterns |
| `accident_location` | 在…/附近/Blvd/Ave/路/高速/城市名 |
| `accident_description` | Non-trivial remainder (≥8 chars) |

Stored in `collected_fields` + `known_facts` (Add Vehicle pattern).

---

## 8. Partial collection

- Saves clear fields only
- Reply shows ✅ received + ○ missing
- No C1 until `is_accident_basics_complete()` true

---

## 9. C1 completion

- `claim_phase = accident_basics_complete`
- `claim_flow_state.c1_stage_complete_sent_at` dedup
- C1 lists recorded time/place/description
- Next step: photos (no H5 URL — text note only)
- Disclaimer: `目前不代表已经正式报案`

---

## 10. Injury / manual_handle

- `有人受伤` etc. → `transition_to_manual_handle()` patch
- Start reply emphasizes emergency + 陈总
- `needs_broker_manual_handle` in ingest outcome

---

## 11. Safety forbidden phrase checks

Tests assert replies do not contain `CLAIM_FORBIDDEN_AUTOMATION_CLAIMS` phrases. C1 uses Chinese disclaimer only (avoids substring false positive on `claim 已正式提交`).

---

## 12. Persistence shape

```json
{
  "service_lane": "claim",
  "claim_phase": "accident_basics_in_progress | accident_basics_complete",
  "guided_workflow_state": "collecting_text_fields",
  "collected_fields": ["accident_datetime", "..."],
  "known_facts": {"accident_datetime": "...", ...},
  "claim_flow_state": {"c1_stage_complete_sent_at": "..."}
}
```

No schema migration.

---

## 13. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h2_claim_wecom_basics.py -q
# 14 passed
```

Regression: P19H-1, P19G-3.2, P19E-2, WeCom suite — **all passed**.

---

## 14. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**PASS** (2026-07-08)

---

## 15. Constraints

| Item | Status |
|------|--------|
| No H5 Claim photos | ✅ |
| No Workbench Claim drawer | ✅ |
| No OCR | ✅ |
| No schema migration | ✅ |
| No Cloud/callback change | ✅ |
| No deploy | ✅ |
| Add Vehicle unchanged | ✅ |
| claim_lite minimal lane preserved | ✅ |

---

## 16. Known limitations

- Datetime/location extraction is deterministic, not NLP-perfect
- No H5 Claim photo upload (P19H-3)
- No full Claim Progress Card (P19H-5)
- No Workbench Claim drawer (P19H-6)
- Media after C1 uses existing generic media ack
- Menu button `开始理赔资料收集` deferred (text-only P19H-2)
- Complex multi-claim restart limited to explicit restart markers

---

## 17. GO/HOLD for P19H-3

**GO** — Basics + C1 stable; safe to build H5 Claim photo flow on `accident_basics_complete` phase.

---

## STOP

| Item | Value |
|------|-------|
| Commit message | `feat: add Claim WeCom basics flow` |
| Deploy | No |
| OCR | No |
| H5 Claim | No |
| P19H-3 | **GO** |
