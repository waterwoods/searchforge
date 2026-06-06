# P16-Y Phase 4 — Failure Analysis

**Date:** 2026-06-01  
**Sprint:** P16-Y Case Intelligence Hardening  
**Source:** 50-case battery (before fixes), `p16y_battery_before.json`  
**Runtime:** Rules-based triage (LLM quota exhausted — same path as production fallback)

---

## Executive summary

| Metric | Before fixes |
|--------|--------------|
| Avg score | **85.6 / 100** |
| Cases below 80 | **11 / 50** (22%) |
| Worst case | Y44 (67) — multi-turn correction |
| Best case | Y01 (97) — cancellation + deadline |

**Primary failure mode:** Classification gaps on non-wedge intents (address, coverage, UW questionnaire), not draft quality or broker action text.

---

## Recurring failure patterns (ranked)

| Rank | Pattern | Cases | Avg loss | Root cause |
|------|---------|-------|----------|------------|
| 1 | **Address / garaging change → unclear** | Y11–Y13 | −12 pts each | No `_is_address_change_request` in classifier |
| 2 | **Coverage Q&A → unclear** | Y27, Y28, Y37 | −12 pts each | No coverage-question lane; full-width ？ missed |
| 3 | **Add-driver → missing_document** | Y14 | −12 pts | 驾照 + 需要 matched doc chase before add-driver |
| 4 | **UW questionnaire → missing_signature** | Y30 | −16 pts | “signed form” triggered signature lane |
| 5 | **核保 follow-up → unclear** | Y31 | −16 pts | Chinese UW markers absent |
| 6 | **Renewal shop-around → unclear** | Y34 | −12 pts | “renews” hit renewal_reminder path incorrectly |
| 7 | **Screenshot-only → no notice_image gap** | Y38 | −8 pts | No still_needed when image mentioned without body |
| 8 | **Multi-turn correction weak** | Y44, Y45 | −8 to −21 pts | Prior turn not in summary/collected |
| 9 | **Deadline not in structured output** | Y02, Y10, Y29–Y31 | −4 to −9 pts | Deadline only in broker prose, not summary/collected |
| 10 | **Policy number not extracted** | Y34, Y35 | −4 pts | No policy # in collected_fields or summary |

---

## Failure by dimension

### Understanding (−2.8 avg vs ceiling)

| Failure | Count |
|---------|-------|
| Wrong category | 10 cases |
| Urgency off by one | 2 cases (Y30, Y31 pre-fix) |
| Summary missing intent | 6 cases |

### Missing Info (−8.1 avg vs ceiling)

| Failure | Count |
|---------|-------|
| No still_needed when expected | 1 (Y38 notice_image) |
| Deadline not surfaced | ~8 cases with explicit dates |
| Policy number not captured | 2 cases |
| Collected fields empty on cancellation emoji-only | Y02 |

### Office Actionability (0 gap)

**No failures** — broker_next_step and client_prep templates are strong on all 50 cases. Generic fallback rarely triggered.

### Multi-message (−3.5 avg vs ceiling)

| Failure | Count |
|---------|-------|
| Prior turn context weak | Y43, Y44, Y45 |
| Correction not changing category | Y44 (pre-fix) |

---

## Cases unchanged after fixes (still ≤88)

These pass but are not “excellent” — acceptable for pilot, not distillation showcase:

- Y02, Y04, Y05 — cancellation without explicit deadline in collected_fields (Chinese notices)
- Y43 — multi-turn DL resend; prior UW turn weak in summary
- Y44, Y45 — multi-turn premium/correction; summary merge still thin
- Y49 — human handoff (86 — draft phrase check strict)

---

## Fix impact (see Phase 7)

| Pattern | Cases fixed | Avg gain |
|---------|-------------|----------|
| Address / coverage / driver / UW | Y11–Y14, Y27–Y31, Y34, Y37 | +12 to +16 each |
| Notice image gap | Y38 | +8 |
| Multi-turn correction | Y44 | +12 |

**Post-fix avg: 88.6 / 100 (+3.0)**

---

## Key insight

> **The engine already writes good broker steps. It fails when it mis-labels the case type or omits structured gaps (deadline, notice image, policy #).**  
> Fixing classification + extraction yields more office time saved than rewriting drafts.

---

*End of P16-Y Phase 4 — Failure Analysis*
