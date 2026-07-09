# P19H-3f-1c — Start Card Only Intake Policy

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Product boundary + workbench visibility — no schema, no deploy in this sprint

---

## Hard rule

```text
Only Start Ceremony creates customer-facing workflow.
Before Start Ceremony, inbound messages are raw inbound, not broker tasks.
```

Start Card / Start Ceremony is the **only** customer-facing entry into a business workflow.  
Pre-ceremony inbound may exist as technical log only — it must **not** appear in Chen's main Workbench queue.

---

## Allowed in broker business queue

1. **Claim** — after explicit「我要理赔」+ Start Card
2. **Add Vehicle** — after explicit Add Vehicle start ceremony / task entry
3. **H5 Task Page** — valid task context (equivalent Start Ceremony)
4. **Future mini program** — formal task entry
5. **Broker manual create/promote** — broker explicitly creates or promotes a case

---

## Not allowed in broker business queue

1. Random photo (no Start Ceremony)
2. Random text
3. Random accident story without start
4. Random insurance card
5. Random DMV notice
6.「看看这个」
7.「这个要不要报保险？」(consultation only)
8. Injury quick-reply alone (no open Claim)
9. Any inbound without Start Ceremony

These may remain in `wecom_media_intake` / raw inbound technical storage if the system already logs them.  
They must **not** surface as broker work items or「半个 case」.

---

## Implementation (P19H-3f-1c)

| Layer | Behavior |
|-------|----------|
| **API** `GET /api/inbox/cases` | Default excludes `service_lane=wecom_media_intake`. `include_raw_inbound=true` for debug only. |
| **Workbench UI** | Office Review Queue filters out `wecom_media_intake` rows. |
| **Data** | Existing `wecom_media_intake` rows are **not deleted**. |
| **Customer copy** | Neutral ack; no「已进入案件」/「陈总正在处理」language. |
| **Debug label** | Raw inbound labeled `Raw Inbound Log` / `技术收件记录` — not demo default. |

---

## Customer copy (pre-Start Ceremony)

```
收到。
如果您要正式开始理赔，请回复「我要理赔」。
没有开始事故记录前，这些信息不会进入陈总的正式案件整理流程。
```

**Do not say:** 已进入案件 · 已进入事故记录 · 陈总正在处理 · 已提交 · 已报案

---

## Related

- `docs/p19h3f1b_start_card_case_creation_ceremony.md`
- `docs/p19h3f_case_boundary_start_end_card_trust_contract_recon.md`
- `docs/evidence/p19h3f1c_start_card_only_intake_policy_2026_07_10.md`
- `tests/test_p19h3f1c_start_card_only_intake_policy.py`

**Next:** Deploy smoke · then P19H-3f-2 True End Card
