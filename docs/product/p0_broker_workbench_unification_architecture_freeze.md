# P0 Architecture Freeze — Broker Workbench Unification

**Status:** SUPERSEDED by Founder decision **D-015** (2026-07-22) — do not implement the unified-intake-as-primary path below  
**Superseding SSOT:** `ui/src/config/workbenchEnv.ts` · `docs/FOUNDER_QA_PLAYBOOK.md` · `docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md` · `docs/product/decision_log.md` (D-015)  
**Date (original freeze):** 2026-07-22  
**Scope (original):** Deployment, routing, and product-shell cleanup for Broker Workbench entry points  

---

## Founder override (D-015) — active

| Field | Decision |
|-------|----------|
| **Canonical Founder QA Broker Workbench** | `/workbench/document-intake` on the **QA Vercel Preview** alias |
| **QA bookmark (only)** | `https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/document-intake` |
| **API** | Cloud QA `https://fiqa-api-qa-g7zatxrycq-uw.a.run.app` (baked into that Preview) |
| **Production Workbench** | `https://ui-smoky-beta.vercel.app/workbench/document-intake` (Production API — not for Golden) |
| **Unified Intake** | Remains the overall web portal / App default; **not** the Founder QA daily Workbench |
| **Do not** | Redirect document-intake → unified-intake; redesign UI; start Claim Vehicle T6 |

**Root fix for ENVIRONMENT MISMATCH:** stop using `ui-smoky-beta` for Golden / Founder QA. Same path (`document-intake`), different host = different API.

---

## Historical proposal (not approved — kept for audit)

The remainder of this file is the **pre-approval** recommendation that unified-intake should replace document-intake. Founder rejected that product move for Founder QA. Implementation Commit 1 aligns **document-intake → Cloud QA** only.

---

**Trigger (original):** Founder PAT ENVIRONMENT MISMATCH — Golden seeded Cloud QA while daily Workbench bookmark used `ui-smoky-beta` + `/workbench/document-intake`

## P20 header (original)

**ONE OBJECTIVE**  
One primary Broker Workbench entry: one bookmark habit, one API environment per alias, zero Founder confusion between `document-intake` and `unified-intake`.

**OUT OF SCOPE**  
UI visual redesign of case rows, new broker features, merging Customer Entry into broker ops, deleting historical lab routes from the repo in this freeze.

**STOP RULE**  
Approve this freeze before any implementation commits. → **Superseded: Founder approved document-intake QA alignment instead.**

---

## 0. Current reality (code + ops) — still useful

| Surface | Route | Role today | Host for Founder QA |
|---------|-------|------------|---------------------|
| **A. document-intake** | `/workbench/document-intake` | **Canonical Founder QA Broker Workbench** | QA Preview `ui-waterwoods-…` only |
| **B. unified-intake** | `/workbench/unified-intake` | Overall web portal (Customer / Broker / Simulation) | Optional; not Founder QA PAT bookmark |

Facts:

- App default still navigates `/` → unified-intake (portal). That does **not** change Founder QA bookmark.
- Golden launcher SSOT prints QA Workbench as **document-intake** on Preview (`scripts/camry_golden_qa.py` `WORKBENCH_QA_URL`).
- `ui-smoky-beta` bakes **Production** API — never use for Cloud QA Golden cases.

---

## Environment strategy (active)

| Role | Host | Baked API | Bookmark path |
|------|------|-----------|---------------|
| **Founder QA / Golden** | `ui-waterwoods-andys-projects-1f411b73.vercel.app` | `fiqa-api-qa-…` | `/workbench/document-intake` |
| **Production / paid pilot** | `ui-smoky-beta.vercel.app` | Production `fiqa-api` / legacy Production host | `/workbench/document-intake` |

Preview/QA document-intake shows a **QA · TEST · API profile** header banner when the client is baked to Cloud QA. Production remains clean.

---

## Explicitly deferred (unchanged)

- Redirect document-intake → unified-intake  
- Workbench UI redesign / new broker features  
- Claim Vehicle T6  
- Renaming products  
- Retiring unified-intake portal  

---

*Original Q1–Q4 “unified-intake as sole primary” answers are void under D-015. Do not implement redirects from that proposal.*
