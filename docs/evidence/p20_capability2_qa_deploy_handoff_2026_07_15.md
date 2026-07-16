# P20 Capability 2 — QA Deploy + Manual Handoff

**Date:** 2026-07-15  
**Verdict:** READY_FOR_MANUAL_QA (browser acceptance still required)  
**Environment:** founder/QA shared pilot (`caseiq` / `caseiq-pilot-pg` / Cloud Run `fiqa-api` / `ui-smoky-beta.vercel.app`)

## Identifiers

| Item | Value |
|---|---|
| Branch | `sprint/p16-trust-layer` |
| Feature commit | `6d92e9dcb69ffae1986f19557e6d17404c3f46d3` |
| Hotfix commit | `877b566ba0f7136a2b0a28f68e42791bbb8ee951` |
| Backend revision | `fiqa-api-00209-5sv` |
| UI alias | https://ui-smoky-beta.vercel.app |
| UI deployment | https://ui-am0exlnwx-andys-projects-1f411b73.vercel.app |
| QA case ID | `case_09a1fb2954cb` |
| Draft ID | `draft_5d13dbab3f3d` v1 |

## Live automated checks

- CreateClaim TEST claim accepted; VIN missing; admin draft
- SaveRequestDraft VIN selected with customer instruction
- GET refresh preserves draft
- Timeline: case_created, missing_information_assessed, request_draft_saved
- No open Request More group; no customer next action; no invite/token/QR
- Unauthenticated CreateClaim → 401
- Office ownership enforcement currently **disabled** (cross-office GET still 200)

## Manual browser acceptance

Open `https://ui-smoky-beta.vercel.app/workbench/document-intake` and inspect case `case_09a1fb2954cb`.
