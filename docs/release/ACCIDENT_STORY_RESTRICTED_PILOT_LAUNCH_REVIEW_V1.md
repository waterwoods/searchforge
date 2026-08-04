# Accident Story — Restricted Pilot Launch Review V1

**Generated:** 2026-08-04T21:40:27Z  
**Classification:** **READY WITH ONE MANUAL PRE-LAUNCH ACTION**

## Evidence summary

| Area | Result |
|------|--------|
| Deterministic / live canary (PR D) | 20/20 + 20/20 |
| Five-case local rehearsal | 5/5 PASS |
| Five-case Cloud QA rehearsal | 5/5 PASS |
| Kill switch / manual intake | PASS |
| Broker Brief layers + fallback visibility | Fixed + tested |
| Durable metrics | Postgres SSOT |
| New trace redaction | PASS |
| Historical LangSmith cleanup | PARTIAL — 15 redacted, 8 immutable |

## Genuine launch blockers

1. **One manual pre-launch action:** In LangSmith UI, delete/move remaining immutable pre-fix runs named `normalize_story` / `LangGraph` / … from before 2026-08-04 (see `docs/evidence/pilot-rehearsal-pr-e/langsmith-cleanup/BATCH_CLEANUP_REPORT.json`). New runs are safe; this does not block office rehearsal but should be finished before broader sharing of the LangSmith project.

## Not blockers

- Not Production-ready (by design)
- Not real-customer accuracy evidence
- Frontend Workbench UI for fallback tag ships with this PR; QA API brief fields already deployed

## Decision

**READY WITH ONE MANUAL PRE-LAUNCH ACTION**
