# Case Split / Secondary Issue Decision Spec

**Sprint:** Mixed-Intent + Secondary Case Strategy  
**Purpose:** Define when to keep one case, when to add a secondary issue marker, when to suggest a second case.

---

## 1. Keep One Case

| Condition | Action |
|-----------|--------|
| Same-goal clarification | Keep; no split |
| Same-goal correction | Keep; no split |
| Same-goal field addition (e.g. add-car zip) | Keep; no split |
| Secondary is quick answer (e.g. "garaging 是什么") | Keep; answer in draft; no split |
| Secondary is tightly coupled (payment + document already sent) | Keep; single case; broker handles both |
| Uncertain whether secondary is separate goal | Keep; mark secondary_issue_note; no split |

---

## 2. Add Secondary Issue Marker

| Condition | Action |
|-----------|--------|
| Different-goal side question detected | Add `secondary_issue_note` to case/summary |
| Side-question marker present (顺便, 另外, etc.) | Treat as secondary; add note |
| 2+ distinct flow markers, primary chosen | Add note: "Customer also asked about X" |
| Broker needs to know but one case suffices | Add to `conversation_summary` or `broker_next_step` |

**Format:** "Secondary: [brief description]" or "Also asked: [topic]"

---

## 3. Suggest / Create Second Case

| Condition | Action |
|-----------|--------|
| Explicit topic switch mid-conversation | Consider new case for new topic |
| Two unrelated urgent items (e.g. claim + cancellation) | Suggest second case in broker note |
| Customer says "先处理 X，Y 再说" | Split: X = case 1, Y = case 2 |
| V1: Defer automatic split | Manual broker decision; we mark only |

**V1 scope:** We do NOT auto-create second case. We mark and recommend. Broker decides.

---

## 4. Fallback When Uncertain

| Situation | Fallback |
|-----------|----------|
| Cannot tell primary vs secondary | Pick higher-urgency as primary; add "Possible secondary: X" |
| Both seem equal | Pick first-mentioned; add secondary note |
| Unclear if same-goal or different-goal | Treat as same-goal; keep one case |
| LLM unavailable, rules conflict | Prefer urgency; add generic "Review full message for other topics" |

---

## 5. Implementation Hooks

| Hook | Location | Purpose |
|------|----------|---------|
| `_classify_with_guardrails` | triage.py | Already picks primary when mixed |
| `_build_conversation_summary` | triage.py | Add secondary_issue_note when detected |
| `_is_turn1_lightweight_candidate` | triage.py | flow_count >= 2 → LLM; already routes mixed |
| Case schema | case_store.py | Add optional `secondary_issue_note` |
| Triage result | triage.py | Add optional `secondary_issue_note` |

---

*End of Spec*
