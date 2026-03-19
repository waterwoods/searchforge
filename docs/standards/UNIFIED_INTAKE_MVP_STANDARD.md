# Unified Intake MVP — Product Standard

**Purpose:** Define the minimum quality bar for the Unified Intake broker workbench mainline.

---

## 1. One-Entry Standard

The page must make these points obvious within a few seconds:

1. This is the one place to paste inbound broker/customer message text
2. Raw text can be pasted without cleanup first
3. Triage creates one structured case rather than a generic chat answer
4. The entry area stays short and action-first rather than explanation-heavy

Supported input framing:

- customer text
- forwarded notice or email excerpt
- OCR text copied from a screenshot

Do not frame the product as a generic assistant, inbox, or CRM.
Keep quick-start examples limited to the strongest few walkthroughs.
If a founder-demo starter queue is shown, it must stay clearly secondary to the paste-first entry.

---

## 2. Workbench Standard

After triage, the active case must clearly separate:

- broker-owned next move
- what the client should prepare
- the client-facing draft to review before sending

Reopened cases must remain fast to scan:

- urgency and current work state are visible
- recent cases show enough context to know the next move faster
- lightweight follow-up context (`waiting_on`, `next_contact_by`, note/activity trail) survives reopen
- recent-case cards favor next move and tracking state over long preview detail

The active case should visually prioritize:

- one dominant broker-owned next move
- client prep as secondary guidance
- the draft reply as ready-to-review support, not the primary focal point

---

## 3. Demo-Honesty Standard

Always distinguish:

- **Real now:** text triage, structured case card, local saved cases, status, follow-up fields, notes/activity, copy draft
- **Real now:** local workbench summary counts derived from the current saved-case queue
- **Local/demo-only:** saved-case memory is local to the current demo environment
- **Demo-assisted:** founder-demo starter queue uses mock/demo-safe input messages but runs through the same local triage + saved-case flow
- **Deferred:** inbox sync, OCR upload inside the product, CRM history, auto-send, automation, collaboration

Never imply direct inbox integration or automatic outbound action.

---

## 4. Output Standard

Every supported case must still produce the six required triage outputs:

- `issue_category`
- `urgency`
- `manual_followup_needed`
- `broker_next_step`
- `client_prep`
- `client_reply_draft`

Quality expectations:

- broker next step is actionable
- broker next step reads like a practical broker work instruction, not a generic summary
- client prep is specific enough to guide the next ask
- client draft is professional, editable, and short enough to feel like a broker-ready starting point
- client draft should follow the narrow proxy style in `docs/CHEN_KUI_REPLY_STYLE_PROXY.md`: conclusion first, next step second, short and office-natural
- client draft avoids stiff template tone (e.g. over-formal salutations or sign-offs)
- client draft should match the likely client language when the input clearly points to Chinese vs English
- when standard insurance / DMV terms matter (`SR-22`, `declaration page`, `garaging proof`, `VIN`), keep the term in English and add a short Chinese gloss only when useful
- mixed Chinese + English inputs should prefer one sendable client language instead of sounding like a generic bilingual assistant
- high-risk cases visibly feel higher urgency than routine notices
- the page should make founder-demo business value legible without fake analytics: what needs attention now, what is waiting on the client, and which cases were triaged first

---

## 5. Validation Standard

Before handoff or demo use, run the relevant checks:

- `npm run build` in `ui/`
- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py`
- `bash scripts/guardrail_inbox_triage.sh`
- `bash scripts/unified_intake_smoke_check.sh`

Use API or browser verification when the change affects saved-case behavior or the visible walkthrough.

---

*End of standard*
