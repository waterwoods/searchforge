# P27 — Production Polish Closeout

**Date:** 2026-07-18  
**Baseline:** `07cbb62` (`chore(p27): deep commit baseline before Batch 1 polish`)  
**Closeout HEAD (pre-final):** `d4d6183` (P27-B2 polish) + closeout evidence/test cleanup  

## Scope (feature complete — presentation only)

P27 did **not** change:

- Constitution resolvers / contracts
- Projection merge logic / API shapes
- Timeline event model
- Resume / session contracts
- Backend services, state machine, workflow, AI logic

P27 **did** change:

- Broker claim workspace copy & panel composition (one 理赔结论 + one 下一步)
- Request More Chinese-first office copy
- Frozen status vocabulary: `等待客户` / `等待经纪人` / `已完成` / `需补充材料`
- Customer trust language (removed sync/system narration)
- Display-only status labels on Task Home / request-item / H5

## Architecture freeze verification

| Surface | Changed in P27? | Evidence |
|---------|-----------------|----------|
| Constitution | No | `miniapp/utils/resolveCustomerConstitution.ts` untouched |
| Projection / Slice1 merge logic | No | No services/ changes; merge helpers display-only |
| Timeline | No | No timeline model edits |
| Resume | No | Golden Flow Session/Resume layer PASS on QA |
| Backend / API contracts | No | `services/` empty in `07cbb62..HEAD` |
| Request More flow | Display copy only | QA Golden Flow Broker Follow-Up PASS |
| Customer Task Home | Status label copy only | build:gate + taskHome tests PASS |
| Broker Workbench | Presentation only | QA UI bundle markers verified |

## Regression summary

| Check | Result |
|-------|--------|
| UI: claimPilotCopy / claimWorkbenchDisplay / MVP / checklist / Structured Request More / requestDraftAutosave / inboxTriage.requestMore | PASS |
| Mini Program Build Gate | PASS |
| Miniapp: resolveTaskViewModel, slice1RequestItem, resolveCustomerTaskCards, taskHomePage, productionCustomerConstitution, resolveCustomerConstitution, goldenUiJourney, receiptPage | PASS |
| `ui npm run build` | PASS |
| `bash scripts/run_claim_release_gate.sh --qa` | **READY FOR FOUNDER QA** |
| QA Golden Customer Flow | PASS (36 assertions, Resume/Constitution/Timeline/Projection layers) |
| QA Golden UI Journey | PASS |
| Live QA bundle (`ui-smoky-beta.vercel.app`) | Chinese Request More + 理赔结论 + frozen status present; `AI Insurance Service Desk` absent |

## Closeout cleanup

- Removed dead prototype imports from `miniapp/tests/resolveCustomerConstitution.test.ts` (modules not in tree; production coverage remains in `productionCustomerConstitution.test.ts`).

## QA deployment

| Item | Value |
|------|-------|
| Workbench URL | https://ui-smoky-beta.vercel.app/workbench/unified-intake |
| P27-B2 deploy commit | `d4d6183` |
| QA API | https://fiqa-api-g7zatxrycq-uw.a.run.app |

## Remaining technical debt (not P27 blockers)

1. `guardrail_inbox_triage.sh` client-identity append expectation drift (pre-existing; P27 did not touch triage).
2. Document drawer still stacks Claim Brief + Accident Basics + Evidence (secondary overlap).
3. Miniapp WeChat Preview packaging is separate from Vercel UI deploy.
4. Add-car workbench still has some demo-queue / mixed bilingual paths (out of claim-first P27 scope).

## Risks

- **Low:** Copy-only deploy; no contract change.
- **Low:** Status vocabulary freeze may still meet raw English `simple_status` from older cases until normalized at display (normalizer covers known variants).
- **Ops:** Founder must hard-refresh workbench; WeChat customer copy needs Preview package if validating mini program.

## Verdict

**P27 COMPLETE**
