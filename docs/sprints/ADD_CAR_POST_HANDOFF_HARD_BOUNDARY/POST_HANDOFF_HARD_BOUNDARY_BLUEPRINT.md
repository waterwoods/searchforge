# Post-Handoff Hard Boundary Blueprint — Add-Car (Chen Kui / Unified Intake)

## Purpose

After Add-Car reaches **handoff** (资料齐 / 已提交办公室), the product should feel like a **bounded service request**, not an endless WeChat thread.

## Three explicit states (post-handoff)

| State | Meaning | Product behavior |
|-------|---------|------------------|
| **A. Same-request continuation** | Still the same Add-Car quote request | Append to the same case; customer copy frames “本条加车 / 同一服务记录”. |
| **B. New issue** | Different operational topic (账单、理赔、续保、删车等) | Classify `case_boundary=new_issue`; broker prefix + customer draft + **explicit “提交新问题”** guidance. |
| **C. Borderline / human-confirm** | Pivot language but unclear domain (e.g. “还有一个问题”, 营业时间) | `case_boundary=borderline`; `human_confirmation_required`; neutral forwarding copy. |

## System map (this sprint)

| Layer | Responsibility |
|-------|------------------|
| **Rule brain** | `triage_for_append` + `_classify_append_case_boundary` in `services/fiqa_api/inbox_triage/triage.py` |
| **Persistence** | `append_follow_up_message` in `case_store.py` — `case_boundary`, `case_messages`, `conversation_summary` tags |
| **Customer UI** | Post-handoff closure card + optional **same-case append** Collapse in `ui/src/pages/UnifiedIntakePage.tsx` |
| **Broker UI** | Boundary tags + append lane labels on recent-case cards |
| **Copy** | `configs/clients/chen_kui/ui_copy.json` + API `get_ui_copy` whitelist |

## Non-goals

Full ticketing, thread splitting automation, LLM replacement of rules, multi-tenant auth.

## References

- Scenario pack: `configs/case_boundary_append_scenarios.json` (CB-01 … CB-23)
- Runner: `scripts/run_case_boundary_battery.py`
