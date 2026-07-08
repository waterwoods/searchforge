# P19H-3d — WeCom Claim Image Binding MVP + C1 Multi-channel Copy

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Feature MVP — no deploy, no schema migration

---

## 1. Goal

Ship first-version WeCom direct photo binding into guided Claim cases while keeping H5 as the recommended upload path. Brokers see unassigned WeCom photos on Workbench without auto slot classification.

---

## 2. UX principle

| Path | Role |
|------|------|
| **H5 guided upload** | Primary / recommended — clearest, slot-aware |
| **WeCom direct photos** | Fallback / convenience — no repeat upload nag |
| **联系陈总** | Human escape hatch |

One Claim `case_id`, one evidence checklist — three paths are not three systems.

---

## 3. C1 copy change

C1 now tells customers:

- 推荐点击下面按钮分步上传事故照片，这样最清楚、也不容易漏。
- 如果您现在不方便，也可以直接把照片发到微信里。
- 不用重复上传；我们会统一整理到这个理赔记录里，陈总会人工确认后跟进。
- 这只是资料收集，不代表 claim 已正式提交。

Button unchanged: **上传事故照片**  
Secondary unchanged: **联系陈总**

---

## 4. Binding rules

WeCom image intake calls `resolve_wecom_media_binding()` which uses **Claim Identity Resolver** (`channel=wecom_media`, no text).

---

## 5. Tier A / B / C behavior

| Tier | Condition | Binding | Customer reply |
|------|-----------|---------|----------------|
| **A** | One recent open Claim (<72h), same user | Bind to Claim case | 照片已收到，我会先帮陈总整理到这个理赔记录里… |
| **B** | Multiple open Claims, or old open Claim | Quarantine — no silent bind | 照片已收到。为了避免把两次事故资料混在一起，陈总会人工确认后整理。 |
| **C** | No open Claim + image only | Quarantine — no Claim created | 照片已收到。如果这是理赔相关，请简单回复「我要理赔」… |

Add Vehicle: unchanged when no strong Claim match. When both Add Vehicle + Tier A Claim, image binds to Claim.

---

## 6. Attachment shape (Tier A)

```json
{
  "source": "wecom",
  "flow": "claim_multichannel_evidence",
  "slot_assignment": "unassigned",
  "source_channel": "wecom",
  "needs_broker_review": true,
  "eligible_for_ocr": false
}
```

No `claim_attachment_slots` slot marked `received`.

---

## 7. Workbench pending-classify display

`claim_evidence_summary.unassigned_wecom_photos`:

```json
{
  "count": 2,
  "items": [{ "attachment_id": "att_...", "filename": "wecom_image.jpg", ... }],
  "broker_next_action": "有 2 张微信照片待陈总人工归类。"
}
```

Workbench drawer section **待分类微信照片** shows count, filenames/metadata, and broker guidance. No assign buttons this sprint.

---

## 8. Tests

`tests/test_p19h3d_wecom_claim_image_binding.py` — 9 tests:

1. One recent open Claim → bind with unassigned metadata  
2. No open Claim + image → no Claim created  
3. Multiple open Claims → broker_confirm, no newest-wins  
4. Add Vehicle unaffected  
5. Workbench `unassigned_wecom_photos` enrichment  
6. C1 multi-channel copy  
7. C1 H5 button still valid  
8. Routing log identity tier/action  
9. Tier A/B/C reply copy

---

## 9. Regressions

```text
PYTHONPATH=. python3 -m pytest tests/test_p19h3d_wecom_claim_image_binding.py -q          → 9 passed
PYTHONPATH=. python3 -m pytest tests/test_p19h3c_r3_claim_identity_resolver_foundation.py -q → passed
PYTHONPATH=. python3 -m pytest tests/test_p19h3c3c_h5_claim_slot_persistence.py -q    → passed
PYTHONPATH=. python3 -m pytest tests/test_p19h3c3a_claim_evidence_summary_backend.py -q → passed
PYTHONPATH=. python3 -m pytest tests/test_p19h3c3ab_get_case_enrichment_parity.py -q    → passed
PYTHONPATH=. python3 -m pytest tests/test_p19h3c2_claim_c1_h5_button.py -q            → passed
PYTHONPATH=. python3 -m pytest tests -q -k "claim"                                      → passed
PYTHONPATH=. python3 -m pytest tests -q -k "h5"                                         → passed
```

---

## 10. Frontend build

```text
cd ui && npm run build → ✓ built in ~22s
```

---

## 11. QA gate

```text
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Result:** FAIL — pre-existing script error on section 3 (`/usr/bin/python3: Argument list too long` when passing large `/api/inbox/cases` JSON as argv). Sections 1–2 PASS (UI routes, Cloud Run readyz). **No deploy in this sprint** — new binding code not on Cloud Run yet.

---

## 12. Constraints honored

- No schema change / no new DB table  
- No AI image classification  
- No OCR  
- No auto slot assignment  
- No new Claim case from image alone  
- No merge UI  
- No deploy  

---

## 13. Known limitations

- Broker cannot assign pending WeCom photo to slot yet  
- Duplicate photo detection deferred  
- Image-only without open Claim quarantines  
- Multiple open Claims require human confirmation  
- No AI classification  

---

## 14. Next recommended prompt

- **P19H-3d Deploy + WeCom Image Smoke** — deploy + live Tier A/B/C smoke  
- **P19H-3d-2 Broker Manual Slot Assignment** — broker UI to assign unassigned WeCom photos to slots  

---

## 15. GO / HOLD

**GO** for code merge on `sprint/p16-trust-layer`.  
**HOLD** on broker demo until deploy smoke.  
**STOP** — no deploy this sprint.
