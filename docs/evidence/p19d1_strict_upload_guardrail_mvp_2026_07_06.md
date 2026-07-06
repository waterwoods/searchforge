# P19D-1 — Strict Upload Guardrail MVP

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Implementation evidence — strict WeCom upload guardrail (no OCR, no deploy)

---

## Product principle (confirmed)

P19D-1 is **strict upload guardrail**, not bulk upload enhancement.

| Confirmed | Detail |
|-----------|--------|
| Default | One image per prompt cycle / normal slot |
| Bulk upload | Not a normal path — excess images quarantined |
| OCR | After guardrail; quarantined images `eligible_for_ocr=false` |
| H5 guided task page | Out of scope — subsequent sprint |

**North star:** Reduce wrong-upload opportunities; Spark Driver-style one-step-one-evidence.

---

## Implemented behavior

### Promote vs quarantine

| Status | Meaning |
|--------|---------|
| **Promoted** | Normal case evidence; appears in main Workbench attachments; `eligible_for_ocr=true` |
| **Quarantined** | Received and stored; separate “Quarantined Uploads” section; not auto-OCR; needs customer/broker confirm |

### Upload limits

| Context | Rule |
|---------|------|
| Normal slot | `max_primary_images = 1` |
| Widened slots (`registration`, `insurance_card`) | max 2 |
| Widened slot (`dmv_notice`) | max 3 |
| Global bulk mistake | >3 images within 120s from same `external_userid` → only 1st promoted, rest quarantined, `bulk_upload_paused` |
| Claim lane (`claim_lite`) | Up to 5 per batch; 6th+ quarantined; batch confirm reply |

### Decision table

| Images in 120s window | Normal slot | Widened slot (max 2) | Claim lane |
|----------------------|-------------|----------------------|------------|
| 1 | Promote | Promote | Promote |
| 2–3 | 1st promote, rest quarantine + confirm reply | Promote up to slot max, rest quarantine | All promote (up to 5) + batch confirm |
| >3 | 1st promote only, rest quarantine + pause reply | Same bulk pause | Claim exception: up to 5 promote, 6+ quarantine |

---

## Customer copy (safe, no OCR language)

| Scenario | Copy (zh) |
|----------|-----------|
| Single image | 收到图片，我先把它放到您的服务 case 里，陈总会人工查看确认。 |
| 2–3 images normal | 已收到多张图片…请确认…当前系统会先处理第一张，其余先标记为待确认。 |
| >3 bulk mistake | 已收到多张图片…请先暂停上传…陈总会人工查看。 |
| Claim batch | 已收到这一批事故照片。请确认这些都是同一次事故的照片，确认后再继续上传下一批。 |

No “已识别”, no coverage/claim/driving advice in guardrail replies.

---

## Workbench badge behavior

| Attachment state | Badges |
|------------------|--------|
| Promoted | Accepted · Eligible for OCR later |
| Quarantined | Needs Review · Bulk upload paused (when applicable) · Not eligible for OCR |

Quarantined items render in a compact **Quarantined Uploads (N)** subsection with yellow background. Inbox attachment count excludes quarantined.

---

## Data shape (additive JSON only)

```json
{
  "intake_status": "promoted | quarantined",
  "guardrail_status": "accepted | bulk_confirm_needed | bulk_upload_paused | claim_batch_confirm_needed",
  "slot_assignment": "unknown_document | null",
  "slot_max": 1,
  "bulk_group_id": "bulk_...",
  "bulk_sequence": 1,
  "bulk_window_seconds": 120,
  "requires_customer_confirm": false,
  "eligible_for_ocr": true,
  "quarantine_reason": null
}
```

Legacy attachments without fields default to `intake_status=promoted`, `guardrail_status=accepted`, `eligible_for_ocr=false`.

**No schema migration.**

---

## Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/upload_guardrail.py` | **New** — rolling window, promote/quarantine decision |
| `services/fiqa_api/wecom/media_intake.py` | Integrate guardrail before persist |
| `services/fiqa_api/wecom/reply.py` | Guardrail customer copy |
| `services/fiqa_api/inbox_triage/case_attachment_api.py` | Expose guardrail fields in API |
| `ui/src/api/inboxTriage.ts` | CaseAttachment guardrail types |
| `ui/src/features/intake/utils/attachmentDisplay.ts` | Partition + count helpers |
| `ui/src/features/intake/components/CaseAttachmentsPanel.tsx` | Badges + quarantined section |
| `tests/test_wecom_upload_guardrail.py` | **New** — 20 unit/integration tests |
| `tests/test_workbench_attachment_api.py` | Guardrail sanitize tests |
| `ui/src/features/intake/utils/attachmentDisplay.test.ts` | Frontend helper tests |

---

## Tests

```text
PYTHONPATH=. python3 -m pytest tests/test_wecom_upload_guardrail.py -q     → 20 passed
PYTHONPATH=. python3 -m pytest tests/test_wecom_media_intake.py tests/test_workbench_attachment_api.py -q → 36 passed
PYTHONPATH=. python3 -m pytest tests/test_wecom_minimal_lanes.py ... -q    → 103 passed
cd ui && npm run build                                                     → PASS
npx tsx ui/src/features/intake/utils/attachmentDisplay.test.ts             → PASS
```

### Simulated smoke scenarios

| Scenario | Result |
|----------|--------|
| A — Single image | Promoted, normal ack, metadata stored |
| B — Three images add_car | 1 promote + 2 quarantine, confirm reply |
| C — Five claim images | All 5 promoted, claim batch reply |
| D — Ten images | 1 promote + 9 quarantine, pause copy, no OCR eligibility on quarantined |
| E — Regression | P19A intake + P19B preview metadata intact; text lanes unchanged |

---

## QA gate

```text
bash scripts/check_chen_kui_demo_environment.sh --cloud-api → PASS
```

- Cloud SQL private DB (`10.73.0.3`, `caseiq`)
- Secret: `fiqa-service-record-database-url-cloudsql-private`
- Neon is NOT QA truth

---

## Constraints honored

| Item | Status |
|------|--------|
| OCR / LLM / vision | ❌ Not introduced |
| H5 / 小程序 | ❌ Not done |
| Schema migration | ❌ None |
| Cloud config change | ❌ None |
| Public GCS URL | ❌ None |
| Full external_userid in UI | ❌ Not exposed |
| Deploy | ❌ Not done |
| Neon as QA truth | ❌ Not used |

---

## Known limitations

1. Rolling window uses existing `case_attachments` metadata scan (no Redis, no new tables).
2. Slot assignment defaults to `unknown_document` until guided slot editor (P19D-2+).
3. Widened slot max only applies when `slot_assignment` is set explicitly on the attachment.
4. Simultaneous callback batch with identical timestamps may have unstable ordering within the same second.
5. Live WeCom smoke not run — deploy required for production guardrail validation.

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| P19D-1 MVP code + tests | **GO** |
| Deploy / live guardrail smoke | **HOLD** — deploy not performed this loop |

---

*End P19D-1 evidence — STOP before H5 / OCR / P19D-1.5 / P19D-2.*
