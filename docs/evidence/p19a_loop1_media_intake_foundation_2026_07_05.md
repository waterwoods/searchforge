# P19A Loop 1 — WeCom Media Intake Foundation Evidence

**Date:** 2026-07-05  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **PASS (local + tests)** — no deploy this loop

---

## 1. Implemented scope

| Item | Status |
|------|--------|
| WeCom `image` / `file` message detection in `sync_msg` + `slice` | **Done** |
| `media_id` extraction + normalization | **Done** |
| WeCom `/cgi-bin/media/get` download helper | **Done** |
| Private GCS upload (`caseiq-wecom-media-qa`) | **Done** |
| Attachment metadata in `case_attachments` JSON | **Done** |
| Safe case binding (add_car → minimal lane → single case → unassigned) | **Done** |
| Safe customer acknowledgement replies | **Done** |
| `msg_id` dedup (attachment + message_processed + reply_dedup) | **Done** |
| OCR / LLM / vision | **Not introduced** |
| Schema migration | **None** |
| Cloud Run / Vercel deploy | **None** |

---

## 2. Changed / added files

**New modules**

- `services/fiqa_api/wecom/media_download.py` — WeCom media GET, size guard
- `services/fiqa_api/wecom/media_storage.py` — GCS path + upload (mockable)
- `services/fiqa_api/wecom/media_intake.py` — orchestration, binding, metadata

**Updated**

- `services/fiqa_api/wecom/sync_msg.py` — `pull_customer_messages` (text + image + file)
- `services/fiqa_api/wecom/normalize.py` — `normalize_media_message`
- `services/fiqa_api/wecom/slice.py` — media branch before text intent path
- `services/fiqa_api/wecom/reply.py` — `build_media_intake_reply`
- `services/fiqa_api/inbox_triage/case_store.py` — `append_wecom_gcs_attachment_metadata`
- `services/fiqa_api/inbox_triage/intake_service_lanes.py` — `SERVICE_LANE_WECOM_MEDIA_INTAKE`
- `requirements.txt` — `google-cloud-storage>=2.14.0`
- `tests/test_wecom_media_intake.py` — new test suite

---

## 3. Attachment metadata shape

Stored in `case_attachments[]` (no Postgres binary):

```json
{
  "attachment_id": "att_...",
  "source": "wecom",
  "external_userid": "...",
  "customer_label": "企业微信客户（尾号 mxcw）",
  "msg_id": "...",
  "msgtype": "image",
  "media_id": "...",
  "storage_uri": "gs://caseiq-wecom-media-qa/wecom/<external_userid>/<yyyy>/<mm>/<msg_id>.jpg",
  "mime_type": "image/jpeg",
  "size_bytes": 123456,
  "received_at": "2026-07-05T...",
  "bound_case_id": "case_...",
  "binding_confidence": "high",
  "document_type": "unknown_document",
  "document_type_confidence": "unknown",
  "ocr_status": "not_started",
  "ocr_draft": null,
  "broker_confirmed": false
}
```

Unassigned intake adds:

```json
{
  "bound_case_id": null,
  "binding_confidence": "unknown",
  "intake_status": "unassigned",
  "broker_action": "attach_to_case_or_ask_customer"
}
```

Holding case lane: `wecom_media_intake` (JSON string only — no schema change).

---

## 4. GCS path pattern

```
gs://caseiq-wecom-media-qa/wecom/<external_userid>/<yyyy>/<mm>/<msg_id>.<ext>
```

- Bucket env override: `WECOM_MEDIA_GCS_BUCKET` (default `caseiq-wecom-media-qa`)
- Never public; metadata stores `storage_uri` only
- Supported mime: `image/jpeg`, `image/png`, `application/pdf`

---

## 5. Binding behavior

| Priority | Condition | Confidence |
|----------|-----------|------------|
| 1 | Single open `add_car` case for `external_userid` | high |
| 2 | Single open `policy_review` / `claim_lite` / `coverage_risk` | medium (coverage: high) |
| 3 | Exactly one other open substantive case | medium |
| 4 | Zero or multiple ambiguous cases | unassigned → `wecom_media_intake` holding case |

---

## 6. Safe replies (no OCR language)

| Context | Copy |
|---------|------|
| Bound service case | 收到图片，我先把它放到您的服务 case 里，陈总会人工查看确认。 |
| Unassigned | 收到图片。为了放到正确的服务事项里，请问这是加车资料、保单/续保资料、理赔照片，还是 DMV/停保通知？ |
| Coverage risk | 收到通知图片。这个属于高风险保单状态问题… |
| Claim | 收到事故照片。请先确认人是否安全… |

---

## 7. Tests

```bash
PYTHONPATH=. python3 -m pytest \
  tests/test_wecom_media_intake.py \
  tests/test_wecom_minimal_lanes.py \
  tests/test_wecom_intent.py \
  tests/test_wecom_slice.py \
  tests/test_wecom_active_case.py \
  tests/test_wecom_reply.py \
  tests/test_wecom_identity_b0_extractors.py -q
```

**Result:** 129 passed

Coverage includes: media detection, download mocks, GCS path/upload mocks, binding, replies, dedup, slice integration, text-lane regression via existing suites.

---

## 8. Simulated smoke (mocked media)

| Scenario | Result |
|----------|--------|
| A — Active Add Vehicle case | Attachment bound, safe ack, `ocr_status=not_started` |
| B — Premium `policy_review` case | Attached to policy case |
| C — No active case | `media_unassigned`, disambiguation reply, holding case created |
| D — Duplicate `msg_id` | Single attachment, duplicate skipped |
| E — Text lanes | Existing regression tests pass (Start Card, Premium, Claim, Coverage) |

---

## 9. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Result:** PASS (unchanged live stack — no deploy this loop)

---

## 10. Guardrails confirmed

| Constraint | Honored |
|------------|---------|
| No OCR / LLM | Yes |
| No schema migration | Yes |
| No Cloud SQL / VPC / Secret / callback change | Yes |
| No deploy | Yes |
| No Neon | Yes |
| No public GCS URL | Yes |
| No `smartsearchx-bucket` | Yes |
| Text/button lanes preserved | Yes (regression tests pass) |

---

## 11. Known gaps (P19B+)

- No Workbench attachment preview / signed URL
- No broker confirm UI for attachments
- No OCR / document classification
- No guided upload buttons
- Live WeCom image smoke requires deploy + real `media_id`
- `video` msgtype deferred

---

## 12. Next loop recommendation

**P19A Loop 2 / deploy gate:** Deploy to Cloud Run `fiqa-api` revision with `google-cloud-storage` dependency; run one synthetic `media_id` smoke on QA (no real customer images). Then consider P19B checklist / broker confirmation — not started in this loop.

**GO** for P19A Loop 2 planning; **HOLD** on live media smoke until deploy explicitly approved.
