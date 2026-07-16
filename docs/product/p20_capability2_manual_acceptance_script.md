# P20 Capability 2 — Manual Acceptance Script

**Capability:** Broker New Case + Missing Information Review + Request Draft  
**Environment:** local Workbench `/workbench/document-intake` + API on 8001 with Postgres service records enabled  
**Do not:** Send Request More, generate QR/invite, deploy, or commit unless separately authorized

## Preconditions

1. Intake API authorized (office key) and optional `X-Org-Id` office assertion configured as in current pilot.
2. `SERVICE_RECORD_DATABASE_URL` set and migration `003_p20_case_intake_draft.sql` applied (or auto-ensure on first command).
3. Feature flag `P20_CASE_INTAKE_DRAFT` not set to `0`.

## Steps

| # | Action | Expected |
|---|---|---|
| 1 | Open Document Intake Workbench → click **New Claim** | Modal opens; TEST checkbox available |
| 2 | Check **Mark as TEST / QA**, leave VIN blank, create | Claim created; drawer opens; **TEST / QA** badge visible |
| 3 | Inspect Missing Information Checklist | **VIN** status `missing`; other gaps listed; no customer next action |
| 4 | Select VIN, edit customer label/instructions | Selection is local until save |
| 5 | Click **Save request draft** once | Success; draft id/version shown; timeline has `request_draft_saved` (via projection summary) |
| 6 | Refresh / reopen the case | Draft items and instructions preserved |
| 7 | Confirm no Request More / customer task | Structured Request More may show Slice 1 eligibility UI but **no open request**; customer_next_action remains none |
| 8 | If a value exists, click **Request correction** | Status `needs_correction`; previous value still shown (not deleted) |
| 9 | Cross-office denial (if office enforcement on) | Request with mismatched `X-Org-Id` returns 403 |

## Pass criteria

- Incomplete QA Claim created without SQL mutation
- Missing VIN appears and can be selected into a durable draft
- Draft survives refresh
- No active Request More group and no customer next action
- Confirmed/prior values are not silently deleted
- Unauthorized office cannot access the case when enforcement is enabled

## Auth posture note

Pilot auth remains intake API key + optional `X-Org-Id` office assertion. Real broker user identity / IAM is a remaining production blocker (documented in the capability report).
