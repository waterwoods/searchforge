# P19H-3c-3B — Workbench Evidence Checklist UI

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Scope:** Frontend UI only — no deploy, no schema change, no backend business rule change

---

## 1. Goal

Display P19H-3c-3A backend `claim_evidence_summary` in the Workbench Claim drawer so Chen can see, at a glance:

- Whether own-damage, other-party vehicle/plate, and scene photos are received / missing / skipped / need retake
- Source channel per slot (H5 / WeCom / broker upload)
- What to ask the customer next (`broker_next_action`)

---

## 2. Business value

Chen buys a **Broker Claim Service Copilot**, not a form system. After an accident he needs:

- 不漏资料 — know what evidence is still missing without scrolling WeChat
- 一打开就知道 — received / missing / next step visible in Workbench
- 下一步该问什么 — `broker_next_action` surfaced prominently

This sprint wires the 3A backend truth layer into the Claim drawer UI.

---

## 3. UI fields displayed

| Field | Display |
|-------|---------|
| Section title | 理赔照片 / Evidence Checklist |
| `summary_text` | Optional one-liner above slot list |
| Per-slot `label` | e.g. 自己车损照片 |
| Per-slot status icon + detail line | See §4 |
| `broker_next_action` | 下一步建议 subsection |

Drawer order (Claim cases):

1. Claim · Accident Basics card (unchanged)
2. **Evidence Checklist** (new)
3. Case attachments panel (unchanged)
4. Safety note inside basics card (unchanged)

---

## 4. Status icon / label mapping

| status | Icon | Label | Detail pattern |
|--------|------|-------|----------------|
| `received` | ✅ | 已收到 | 已收到 · {source} · {count} 张 |
| `missing` + required | ○ | 还缺 | 还缺 · 请客户补充 |
| `missing` + soft_required | ○ | 还缺 | 还缺 · 可补充，或记录无法提供原因 |
| `missing` + optional | ○ | 还缺 | 可选 · 有的话可以补充 |
| `skipped` | — | 已跳过 | 已跳过 · 原因：{skip_reason} |
| `needs_retake` | ↻ | 需重传 | 需重传 · 请陈总确认后联系客户补充 |

Required level labels (available in helpers): 必需 / 建议补充 / 可选

---

## 5. Source channel mapping

| source_channel | Label |
|----------------|-------|
| `h5_task` | H5 上传 |
| `wecom` | 微信上传 |
| `broker_upload` | Broker 上传 |
| `none` | 未上传 |
| other | 保留原文 / 其他 |

Skip reason keys mapped to Chinese (aligned with H5):

| key | Label |
|-----|-------|
| `no_other_party` | 没有对方车辆 / 单方事故 |
| `not_available` | 当时无法拍摄 |
| `hit_and_run` | 对方逃逸 |
| `customer_not_safe_to_collect` | 当时不安全未能拍摄 |

---

## 6. Fallback behavior

When `claim_evidence_summary` is absent or malformed:

- Drawer does not crash
- Claim Accident Basics card still renders
- Evidence section shows: **理赔照片状态暂未生成**
- Add Vehicle Workbench unaffected

---

## 7. Tests

`ui/src/features/intake/utils/claimWorkbenchDisplay.test.ts` — 8 scenarios:

1. Received H5 slot (自己车损照片 · 已收到 · H5 上传 · 1 张)
2. Missing soft-required slot (对方车辆 / 车牌照片)
3. Optional scene slot (现场照片 · 可选)
4. Skipped slot with `not_available` reason
5. Needs retake
6. `broker_next_action` payload present
7. Missing summary → `resolveClaimEvidenceSummary` returns null
8. Forbidden copy absent from format helpers

```bash
npx tsx ui/src/features/intake/utils/claimWorkbenchDisplay.test.ts
# claimWorkbenchDisplay.test: PASS
```

---

## 8. Build result

```bash
cd ui && npm run build
# ✓ built in ~20s
```

---

## 9. Backend regression result

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3c3a_claim_evidence_summary_backend.py -q
# 8 passed

PYTHONPATH=. python3 -m pytest tests/test_p19h3a_claim_workbench_visibility.py -q
# 8 passed
```

---

## 10. QA gate result

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# Result: PASS — QA UI + Cloud Run API + Cloud SQL aligned
```

---

## 11. Constraints honored

| Constraint | Status |
|------------|--------|
| No deploy | ✅ |
| No schema change | ✅ |
| No backend business rule change | ✅ |
| No H5 slot persistence | ✅ |
| No WeCom direct image binding | ✅ |
| No identity resolver | ✅ |
| No duplicate merge | ✅ |
| Forbidden filing/liability language in UI | ✅ |

---

## 12. Changed files

| File | Change |
|------|--------|
| `ui/src/api/inboxTriage.ts` | `ClaimEvidenceSummary` / `ClaimEvidenceSlot` types on `TriageResult` |
| `ui/src/features/intake/utils/claimWorkbenchDisplay.ts` | Evidence format helpers + `resolveClaimEvidenceSummary` |
| `ui/src/features/intake/components/ClaimEvidenceChecklist.tsx` | **NEW** — drawer checklist card |
| `ui/src/pages/DocumentIntakeInboxPage.tsx` | Render checklist after Accident Basics for Claim cases |
| `ui/src/features/intake/utils/claimWorkbenchDisplay.test.ts` | Extended unit tests |

---

## 13. Known limitations

- UI depends on backend 3A summary being deployed to Cloud Run before Chen sees live data in QA
- H5 skip reason persistence still deferred (P19H-3c-3C)
- WeCom direct image binding deferred
- Identity resolver deferred
- Phone summary deferred
- No attachment preview in checklist (attachments panel unchanged)

---

## 14. Next recommended prompt

**P19H-3c-3C** — H5 Slot Persistence / Skip Reason  
or **Deploy + Workbench Smoke** once UI is ready to ship to QA

---

## 15. GO / HOLD

**GO** — Frontend evidence checklist is implemented, tested, and build-clean. Ready for deploy sprint when Andy chooses.

**STOP**
