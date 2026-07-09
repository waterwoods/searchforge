# P19H-3f-2 — True End Card on Broker Done

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Deploy:** No

---

## 1. Goal

Close the Claim Story Recorder loop:

| Ceremony | Meaning |
|----------|---------|
| **Start Card** | Formal accident record begins (`【事故记录已开始 ✅】`) |
| **True End Card** | Broker/office confirms record phase complete (`【陈总已确认 ✅】`) |

**Hard rule:** System never auto-ends a case. Only explicit broker/office `broker_done` triggers End Card.

---

## 2. Start vs End contract

```text
True End Card is emitted only after broker/office confirms the record is done.
System milestones are not End Cards.
C1 complete / enough info / brief generated are stage-complete messages, not final endings.
```

| Audience | Meaning |
|----------|---------|
| **Customer** | 陈总已经确认，目前这次事故资料整理阶段结束。如果后面有新情况，可以继续联系陈总。 |
| **Broker** | Case leaves active follow-up queue after `broker_done`. |

---

## 3. `broker_done` action

**Endpoint:** `POST /api/inbox/cases/{case_id}/broker-done`

| Step | Behavior |
|------|----------|
| Validate | Formal `service_lane=claim` only |
| Reject | `wecom_media_intake`, non-claim lanes |
| State | `claim_phase=broker_done`, `claim_end_card_state.broker_done_at` |
| Timeline | Append `broker_done` event (`actor=broker`, `source=workbench`) |
| WeCom | Send True End Card once if channel + send infra available |
| Response | Enriched case + `end_card_preview`, `end_card_sent`, `already_done` |

---

## 4. End Card copy

```
【陈总已确认 ✅】

这次事故资料已经整理完成，并交给陈总确认。
目前这份事故记录的收集阶段已结束。
如果后面有新的照片、文件或保险公司回复，您可以继续发给陈总。

这条消息不代表保险公司已经结案，也不代表赔付结果。
```

Must NOT say: 保险公司已结案 · 一定会赔 · 对方全责 · coverage approved · claim filed · carrier accepted

---

## 5. Idempotency

- Second `POST` returns `already_done: true`
- No duplicate `broker_done` timeline event
- No second End Card send (`claim_end_card_state.end_card_sent_at` dedup)

---

## 6. Timeline event

```json
{
  "event_type": "broker_done",
  "actor": "broker",
  "source_channel": "workbench",
  "text": "陈总已确认，事故资料收集阶段结束",
  "metadata": { "source": "workbench" }
}
```

---

## 7. Workbench UI

- Button: **陈总已确认 / 结束收集**
- Placement: drawer action area (non-primary)
- Visible: formal Claim only, not raw inbound, not already done
- Toast: 已标记陈总确认，并发送结束提醒 (or 已标记陈总确认 when send skipped)

---

## 8. Queue behavior

After `broker_done`:

- Case **removed from default active broker queue** (`filter_broker_workbench_cases`)
- Case **not deleted** — still retrievable via direct GET
- Display label: `Claim · 已确认 / 已交接`
- Next step copy: `当前收集阶段已结束`

---

## 9. Tests / build

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3f2_true_end_card_on_broker_done.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3f1_case_boundary_policy.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3f1c_start_card_only_intake_policy.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19h3e1_claim_timeline_case_brief.py -q
cd ui && npm run build
```

---

## 10. Constraints (held)

| Constraint | Status |
|------------|--------|
| No schema migration | ✅ extra bag only |
| No OCR/ASR | ✅ |
| No fault/coverage/carrier filing | ✅ |
| No LLM brief | ✅ |
| No auto close | ✅ broker action only |
| Start Card policy preserved | ✅ |
| Raw inbound hidden policy preserved | ✅ |

---

## 11. Known limitations

- Add Car `broker_done` / Done Card remains on existing `PATCH /confirm` path (Track B0.3)
- End Card send requires WeCom channel binding on case; local/dev may preview only
- Done cases hidden from default queue; no dedicated “closed cases” filter yet

---

## 12. Next recommended prompt

1. **P19H-3f-2 deploy smoke** — live WeCom End Card on broker_done
2. **Pilot Demo Script / Chen readiness** — full Start → Record → End walkthrough

---

## Changed files

- `services/fiqa_api/wecom/reply.py` — `build_claim_end_card_reply()`
- `services/fiqa_api/wecom/claim_end_card.py` — send helper
- `services/fiqa_api/inbox_triage/case_store.py` — `mark_claim_broker_done()`
- `services/fiqa_api/inbox_triage/claim_workbench_display.py` — done display + visibility
- `services/fiqa_api/inbox_triage/workbench_enrichment.py` — queue filter
- `services/fiqa_api/routes/inbox_triage.py` — `POST broker-done`
- `ui/src/api/inboxTriage.ts` — `markClaimBrokerDone()`
- `ui/src/features/intake/utils/claimWorkbenchDisplay.ts` — helpers
- `ui/src/pages/DocumentIntakeInboxPage.tsx` — broker action button
- `tests/test_p19h3f2_true_end_card_on_broker_done.py`
