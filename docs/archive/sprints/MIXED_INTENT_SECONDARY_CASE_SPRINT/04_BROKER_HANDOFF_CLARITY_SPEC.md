# Broker Handoff Clarity Spec

**Sprint:** Mixed-Intent + Secondary Case Strategy  
**Purpose:** Define how mixed-intent should appear in broker view; keep summaries and next steps clear.

---

## 1. How Mixed-Intent Appears in Broker View

| Element | Content |
|---------|---------|
| **conversation_summary** | Primary intent first; then "Also asked: [secondary]" when present |
| **broker_next_step** | One main action; optional "Also: [secondary action]" when needed |
| **secondary_issue_note** | Optional field: brief note for broker (e.g. "Customer also asked about premium review") |
| **Workbench display** | Primary category/focus; secondary as badge or note if present |

---

## 2. Summary Format

**Single intent:**
```
Add car to existing policy. Collected: year, model. 1 customer message(s). Latest: 我想加一辆2024 X5...
```

**Mixed intent (V1):**
```
Add car to existing policy. Also asked: garaging proof 是什么. Collected: year, model. 1 customer message(s). Latest: 我想加一辆车，然后这个 garaging proof 又是什么？...
```

Or:
```
Payment failed / lapse risk. Also: dec page 发过了. Collected: client says sent. 1 customer message(s). Latest: payment failed 怎么办，另外 dec page 我上周发过了...
```

---

## 3. Broker Next Step Format

**Single intent:** One operational sentence.

**Mixed intent (V1):** Main action first; append "If customer also asked about [X], address that separately or note for follow-up."

Example:
```
Verify payment status with carrier; if client says dec page was sent, confirm with underwriting. If customer also asked about premium review, address that separately.
```

---

## 4. Avoid Messy Case Handoff

| Anti-pattern | Fix |
|--------------|-----|
| One case with 4 unrelated bullet points | One primary; secondary as note |
| broker_next_step lists 5 actions | One main; secondary as "Also" |
| conversation_summary is raw dump | Structured: intent + collected + secondary + count |
| Broker cannot tell what to do first | Primary first; secondary explicit |

---

## 5. Workbench Visibility

| Location | What to show |
|----------|--------------|
| Case card / list | Primary category; optional "mixed" badge |
| Case detail | conversation_summary with "Also asked" when present |
| broker_next_step | Main action; secondary in same block if needed |
| secondary_issue_note | New optional field; show when present |

---

*End of Spec*
