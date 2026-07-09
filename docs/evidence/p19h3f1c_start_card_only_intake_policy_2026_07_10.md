# P19H-3f-1c — Start Card Only Intake Policy — Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Deploy:** No (code + tests only)

---

## 1. Goal

Tighten product boundary: **No Start Card / Start Ceremony = no broker business queue item.**

Random WeCom inbound (photo, text, narrative) must not appear in Chen's main Workbench queue as「待确认材料」or half-case work items.

---

## 2. Policy

```text
Only Start Ceremony creates customer-facing workflow.
Before Start Ceremony, inbound messages are raw inbound, not broker tasks.
```

See: `docs/p19h3f1c_start_card_only_intake_policy.md`

---

## 3. Before behavior

- `wecom_media_intake` rows appeared in Office Review Queue with「待确认材料」label
- Random photos created visible intake rows that looked like broker tasks
- Customer copy asked「这是加车资料、保单…还是理赔照片？」— implied a task had started

---

## 4. After behavior

| Surface | Behavior |
|---------|----------|
| **Default API list** | Excludes `service_lane=wecom_media_intake` |
| **Debug API** | `include_raw_inbound=true` shows raw rows (labeled Raw Inbound Log) |
| **Workbench UI** | Office Review Queue shows Claim / Add Car / formal cases only |
| **Data** | Existing `wecom_media_intake` rows retained; not deleted |
| **Customer** | Neutral pre-ceremony ack; no「已进入案件」language |

---

## 5. What changed

| File | Change |
|------|--------|
| `workbench_enrichment.py` | `is_raw_inbound_case`, `filter_broker_workbench_cases` |
| `case_truth_repository.py` | `list_broker_workbench_cases_for_read`, office list filter |
| `routes/inbox_triage.py` | Default list excludes raw inbound; `include_raw_inbound` debug param |
| `reply.py` | Pre-Start Ceremony customer copy tightened |
| `claim_workbench_display.py` | Raw inbound labels → Raw Inbound Log / 技术收件记录 |
| `DocumentIntakeInboxPage.tsx` | Queue filter excludes `wecom_media_intake` |
| `workbenchCaseOpen.ts` | `isBrokerBusinessQueueLane` helper |
| `tests/test_p19h3f1c_start_card_only_intake_policy.py` | New policy tests |

---

## 6. Customer copy

```
收到。
如果您要正式开始理赔，请回复「我要理赔」。
没有开始事故记录前，这些信息不会进入陈总的正式案件整理流程。
```

---

## 7. Broker UI behavior

- **Shows:** Claim cases, Add Vehicle cases, other formal workflow cases
- **Hides:** `wecom_media_intake`, random inbound,「待确认材料」as work items
- **Debug:** API `include_raw_inbound=true` only — not demo default

---

## 8. Tests / build

| Command | Result |
|---------|--------|
| `pytest tests/test_p19h3f1c_start_card_only_intake_policy.py tests/test_p19h3f1_case_boundary_policy.py -q` | PASS (27) |
| `pytest tests -q -k "claim"` | PASS |
| `pytest tests -q -k "h5"` | PASS |
| `npm run build` (ui) | PASS |
| `npx tsx workbenchCaseOpen.test.ts` | PASS |
| `npx tsx claimWorkbenchDisplay.test.ts` | PASS |

---

## 9. Constraints

- No schema change
- No new DB table
- No workflow expansion (OCR/ASR, fault/coverage, carrier filing)
- Start Card policy preserved
- Explicit「我要理赔」flow preserved
- Add Vehicle / H5 formal entries preserved

---

## 10. Known limitations

- `wecom_media_intake` rows still created internally for random photos (technical buffer)
- PG office-scoped list total may be approximate when DB-primary reads + raw rows coexist
- No dedicated「Raw Inbound Log」UI tab in demo — debug via API param only
- Promote holding → formal case (broker action) not implemented in this sprint

---

## 11. Next recommended step

1. **Deploy smoke** — verify Workbench queue on Cloud Run excludes raw inbound
2. **P19H-3f-2** — True End Card on Broker Done

---

## Verdict

**GO** — policy enforced at API + UI visibility layer  
**STOP** — no deploy in this sprint
