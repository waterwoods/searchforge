# P19H-3e-1 — Claim Story Timeline + Case Brief Foundation

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Feature foundation — timeline + deterministic brief + Workbench hero  
**Deploy:** No (per sprint scope)

---

## 1. Goal

WeChat-native Claim Story Recorder + Case Builder foundation:

- Customer messages/photos in WeChat append to one `claim_timeline[]`
- System generates deterministic `claim_case_brief`
- Chen opens Workbench and sees Brief first (10-second scan)

---

## 2. Product principle

| Principle | Implementation |
|-----------|----------------|
| Customer sees next step | Story-centric WeCom copy; injury quick replies only |
| AI records first, organizes second | Timeline append on ingest; brief computed at read |
| Chen sees Brief first | `ClaimCaseBriefPanel` hero above collapsed checklist |

---

## 3. `claim_timeline` shape

Stored on case JSON extra (no schema migration). Max 50 events.

```json
{
  "event_id": "evt_<uuid>",
  "event_type": "customer_text | customer_photo | claim_started | basics_complete | customer_voice_stub",
  "source_channel": "wecom",
  "created_at": "ISO-8601Z",
  "actor": "customer | system",
  "message_id": "wm_...",
  "attachment_id": null,
  "text": "...",
  "metadata": {}
}
```

Idempotency: `message_id`, `customer_photo` + `attachment_id`, `basics_complete`, `claim_started` (once).

---

## 4. `claim_case_brief` shape

Computed in `build_claim_case_brief()` — deterministic, no LLM.

```json
{
  "summary": "...",
  "customer": { "name", "phone", "wecom_external_userid" },
  "key_facts": {
    "accident_datetime", "accident_location", "accident_description",
    "injury_status", "police_involved", "other_party_info", "own_vehicle_info"
  },
  "evidence_received": {
    "photo_count", "photo_sources", "voice_count", "has_basics",
    "slots_received", "slots_missing", "unassigned_wecom_photos"
  },
  "missing_info": [{ "key", "label", "severity", "reason" }],
  "next_best_question": "single short question",
  "confidence": "low | medium | high",
  "source_event_ids": [],
  "brief_updated_at": "...",
  "brief_version": 1
}
```

---

## 5. WeCom copy changes

| Area | Change |
|------|--------|
| Claim start | Story-centric intro; safety + one-message basics ask; disclaimer |
| After basics | `【事故信息已记录 ✅】`; continue in WeChat; optional H5 secondary |
| Photo ack Tier A | `收到照片，已记到这份事故记录里 ✅` — no H5 nag |
| C1 button | `补充事故资料` (was `上传事故照片`) |

Forbidden language guarded in tests (no 已报案 / 对方全责 / 一定会赔 / 已受理).

---

## 6. Injury quick replies

**Full implementation** via WeCom msgmenu on claim start:

- [没有受伤] → `injury_status=no`
- [有人受伤] → `injury_status=yes` + manual handle escalation
- [不确定] → `injury_status=unknown`

Timeline captures quick reply in `customer_text` with `metadata.quick_reply_key=injury_status`.

---

## 7. Workbench layout changes

Claim drawer order:

1. **ClaimCaseBriefPanel** (hero) — 事故摘要, key facts, 还缺什么, 建议问客户, 最近记录
2. Accident Basics (collapsed)
3. Evidence Checklist (collapsed by default) — 照片清单（H5 分步状态）

---

## 8. Tests

`tests/test_p19h3e1_claim_timeline_case_brief.py` — 11 tests covering timeline, dedup, image bind, basics_complete, brief shape, missing-info priority, forbidden copy, enrichment, Add Vehicle isolation, injury quick replies.

---

## 9. Regressions

| Suite | Result |
|-------|--------|
| `test_p19h3d_wecom_claim_image_binding.py` | PASS (copy expectations updated) |
| `test_p19h3c_r3_claim_identity_resolver_foundation.py` | PASS |
| `test_p19h3c3c_h5_claim_slot_persistence.py` | PASS |
| `test_p19h3c3a_claim_evidence_summary_backend.py` | PASS |
| `test_p19h3c3ab_get_case_enrichment_parity.py` | PASS |
| `test_p19h3c2_claim_c1_h5_button.py` | PASS |
| `test_p19h2_claim_wecom_basics.py` | PASS |
| `test_p19h2_simplified_claim_wecom_basics.py` | PASS |
| `pytest -k claim` | PASS |
| `pytest -k h5` | PASS |

---

## 10. Frontend build

`cd ui && npm run build` — PASS

---

## 11. QA gate

`bash scripts/check_chen_kui_demo_environment.sh --cloud-api` — see run output at commit time.

---

## 12. Constraints honored

- No schema migration
- No OCR / ASR / damage AI
- No fault / coverage / carrier filing
- No slot assignment
- No deploy

---

## 13. Known limitations

- Deterministic summary only (no LLM brief)
- No full timeline UI (preview max 3 events in drawer)
- No auto gap-question send to customer
- No phone summary event yet
- Voice stub helper ready; WeCom voice path not wired in 3e-1

---

## 14. Next recommended sprint

1. **P19H-3e-1 Deploy + Claim Story Smoke**
2. **P19H-3e-2** — Timeline UI + LLM brief / auto-gap-ask

---

## 15. GO / HOLD

**GO** — foundation complete for internal trial; deploy smoke is next explicit step.
