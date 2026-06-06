# Evaluation Criteria

Per scenario, answer **seven** questions using the last turn (or both turns for multi-turn).

## Checklist

1. **ZIP parse** — Is `zip` present in `collected_fields` when the customer gave a CA-style `9xxxx` garage ZIP in customer text?
2. **Driver parse** — Is `primary_driver` / driver logic **consistent with the words the customer used** (not only “some driver flag set”)?
3. **Materials Q vs statement** — Does `follow_up_type` treat **要不要 / 要不要先…发** as **not** `already_sent`, and **发你微信了 / 截图发你了** as `already_sent` when appropriate?
4. **Add-Car playbook** — `issue_category` stays `customer_question`, handoff/reply aligned with quote collection or materials-verify branch.
5. **Customer reply** — Sounds reasonable in Chinese; does not contradict the customer; addresses obvious questions when the last bubble asks one.
6. **Broker usefulness** — `broker_next_step` names the right next office action; structured fields match the thread.
7. **Classification** — One of four labels below.

## Four-way classification

| Label | Meaning |
|-------|---------|
| **Strong** | Logic correct; broker + customer outputs usable with at most tiny polish. |
| **Acceptable** | Logic correct or intentionally incomplete (e.g. missing delivery called out in `still_needed_fields`); minor broker string loss or generic reply. |
| **Weak** | Logic mostly OK but **reply** generic/ignores a clear question, or broker line loses important model context; fix polish or copy. |
| **Trust-breaking** | **Structured extraction or classification wrong** in a way that could mislead rating/bind (e.g. wrong primary driver); or customer reply contradicts facts. |

## Separation of concerns

- **Logic correctness** — ZIP/driver/materials classification, `collected_fields` truth vs message.
- **Reply quality** — `client_reply_draft` tone, answering questions, not echoing junk.
- **Broker usefulness** — Concrete vehicle, verify WeChat when customer says sent, confirm what is still missing.
