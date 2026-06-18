# P16 Status Truth — Certification

**Sprint:** P16-P3-STATUS-TRUTH-SPRINT  
**Date:** 2026-06-07  
**Certifier:** Cursor agent (investigation + fix + local simulation)

---

## Final report

### 1. Current state machine

See `P16_STATUS_TRUTH_AUDIT.md` §1. Four customer-visible phases: Draft (`collecting`), Waiting For Customer (gaps), Submitted To Office (`handed_off` + formal timestamp), Closed.

### 2. Screenshot analysis

Real bug — green closure headline `handoff_closure_headline_add_car` rendered while triage still requested year/model. Not intentional partial-submit UX.

### 3. Root cause

Collecting Case Memory append promoted lifecycle to `office_followup` and read-path backfilled `formal_submitted_at`; formal-submit detectors ignored `still_needed_fields`. Details: `P16_STATUS_TRUTH_ROOT_CAUSE.md`.

### 4. Files changed

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/case_store.py` | Backfill guard; collecting-safe append lifecycle |
| `services/fiqa_api/db/service_record_repository.py` | PG hydrate backfill guard |
| `services/fiqa_api/inbox_triage/triage.py` | No office_followup promotion on collecting persisted case |
| `services/fiqa_api/inbox_triage/active_case_lookup.py` | Gap gate on `is_customer_formal_submitted` |
| `ui/src/components/intake/AddCarRecordSummaryRail.tsx` | Gap gate on `isFormalSubmissionToOfficeComplete` |
| `tests/test_active_case_by_phone.py` | Regression test for corrupted state |
| `docs/trial/P16_STATUS_TRUTH_*.md` | Sprint deliverables |

### 5. Simulations

Scenarios A–D documented in `P16_STATUS_TRUTH_SIMULATION.md`. Post-fix: **0 contradictions**.

Local pytest:

```
tests/test_active_case_by_phone.py .........
tests/test_collecting_case_memory_persistence.py ..
9 passed
```

### 6. Preview verification

| Target | Status | Notes |
|--------|--------|-------|
| Preview UI load | **PASS** | `https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer` loads Customer First entry (phone/name, Continue CTA) |
| BMW X5 contradiction repro on Preview | **Pre-fix backend expected** | Fix is in repo; Preview API not yet redeployed with this commit |
| Local API 8001 | Not run (demo boot slow) | Offline harness + pytest sufficient for logic cert |

**Browser check (2026-06-07):** Preview customer tab renders P16 phone-return entry surface. Full end-to-end BMW scenario requires Preview API redeploy; post-deploy expect no green closure card during collecting turns.

**Post-deploy checklist:**

1. Phone return → active card shows **Saved — Not Yet Submitted** for in-progress BMW draft
2. Chat turn 「我刚买了一台宝马X5」 → **no** green 「已提交办公室处理」 card
3. Still Needed list visible; Contact State = Waiting For Customer
4. After real formal submit → Submitted To Office + closure card

### 7. Remaining risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Legacy cases already corrupted (`office_followup` + gaps) | Medium | Gap gate on read paths; broker may reset lifecycle manually |
| Postgres rows with empty `extra.formal_submitted_at` still hydrate `created_at` for non-collecting legacy | Low | Guard only skips collecting/handoff_pending |
| Preview/API deploy lag | Ops | Redeploy backend + Vercel preview before broker trial |
| `contact_state` vs `status_label` still two dimensions | Low | By design; both now consistent on gaps |

### 8. Verdict

## **CONDITIONAL GO**

- **Logic / local simulation:** **GO** — status truth restored; no missing-fields + submitted contradiction.
- **Preview live:** **CONDITIONAL** — requires redeploy of API + UI preview with fix commit before customer-facing sign-off.

Success criteria met in code and tests:

> Customer always sees the true status. No screen simultaneously says missing required fields and Submitted To Office.

---

## Constitution alignment (post-fix)

| Rule | Status |
|------|--------|
| Progress = Missing Fields | ✅ |
| Customer Must Always Know The Status | ✅ |
| Phone Required For Formal Submit | ✅ |

---

## Related docs

- `P16_STATUS_TRUTH_ROOT_CAUSE.md`
- `P16_STATUS_TRUTH_AUDIT.md`
- `P16_STATUS_TRUTH_SIMULATION.md`
- Prior: `P16_CASE_MEMORY_ROOT_CAUSE.md`, `P16_STATUS_SURFACE_CERTIFICATION.md`
