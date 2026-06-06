# Evaluation Criteria

## Dimensions (evaluate separately)

1. **Playbook** — Stays on Add-Car (`issue_category` / intent) vs drift to premium_review, missing_document, unclear, etc.
2. **Extraction** — Year/model, CA ZIP, delivery, driver signals match merged customer text (`collected_fields` / `still_needed_fields`).
3. **Materials intent** — `follow_up_type` and reply match: **already_sent** vs **prospective send** (要不要 / 看看行吗) vs neutral `new_info`.
4. **Customer-facing reply** — Sensible, office-realistic, language match (ZH vs EN), no false promises on price.
5. **Broker-facing** — `broker_next_step` / handoff text useful; `quote_ready_status` consistent with slots.

## Classification labels

| Label | Meaning |
|-------|---------|
| **Strong** | Correct category, extraction and state aligned, reply and broker step clearly useful; no misleading claims. |
| **Acceptable** | Minor wording imperfections or conservative extra ask, but **no wrong vehicle/ZIP/driver** and no trust harm. |
| **Weak** | Partial success: e.g. late handoff, redundant question, muddled side-question handling, or broker text vague but recoverable by human. |
| **Trust-breaking** | Wrong vehicle after correction, false “already sent” handling, wrong category that sends broker down wrong path, or customer reply that invents price/coverage. |

## Evidence

Each classification should cite **last turn** `handoff_ready`, `follow_up_type`, `quote_ready_status`, `collected_fields`, and a short snippet of `client_reply_draft` / `broker_next_step`.
