# Case Boundary + New-Issue Separation — Blueprint

## Product goal

Unified Intake should behave more like a **service portal** than an endless chat: one primary operational case in view, explicit handling when the customer **pivots** to a different insurance task, and **broker-visible** hints when the same thread may mix topics.

## Scope (this sprint)

- **In scope:** Append flow (`triage_for_append`) after a case exists; customer copy; broker `broker_next_step` + `conversation_summary`; light workbench tags; rule-based classification only (no LLM required).
- **Out of scope:** OCR, carrier API, full ticketing, replacing rule brain, enterprise multi-channel.

## Definitions

### Continue current case

- Field completion (zip, driver, year/model), corrections to the **same** vehicle/task, “already sent”, document meaning questions in the same workflow, short quote-side questions (coverage) on an add-car thread.

### New issue

- Clear **different** operational domain than the thread’s primary case (e.g. add-car thread → claim, billing, remove vehicle), including many Chinese pivot phrases (“另外一个…”, “账单…”, “理赔…”).

### Borderline

- Pivot language without a clear domain anchor (“还有一个问题”), or **office-hours** style asks on a quote thread—better for **human confirmation** than automatic split.

## Architecture

1. **Prior domain** is inferred from existing `[客户]` / `[系统]` thread (add_car, claim, payment, etc.).
2. **Last message domains** (claim, billing, remove_car, add_car, office) are detected with existing intent markers plus small pivot lexicons.
3. **Cross-domain hit** → `new_issue`; **office on add-car** or **pivot-only** → `borderline`; else no boundary override (same case).
4. **Overrides** triage customer draft and enriches broker fields when boundary ≠ empty.

## Artifacts

| Artifact | Path |
|----------|------|
| Scenario pack | `configs/case_boundary_append_scenarios.json` |
| Runner | `scripts/run_case_boundary_battery.py` |
| Logic | `services/fiqa_api/inbox_triage/triage.py` (`triage_for_append`, helpers) |
| Persistence | `services/fiqa_api/inbox_triage/case_store.py` (`case_boundary` on append) |
| Workbench UI | `ui/src/pages/UnifiedIntakePage.tsx`, `ui/src/api/inboxTriage.ts` |
