# Stage 1 Founder-Validated Closeout

**Status:** READY TO FREEZE → **FOUNDER-VALIDATED (frozen)**  
**Date:** 2026-08-03  
**Branch:** `demo/known-customer-invite-overlay`

## Validated commit and tag

| Item | Value |
|------|--------|
| Validated commit | `826fa39` (`826fa39e71e88aa2fbf582aefb09e201fe03eec1`) |
| Annotated tag | `stage1-founder-validated-demo-2026-08-03` |
| Tag message | Founder-validated Stage 1: customer intake, Request More, supplement review, office acceptance, and evidence pack complete. |

## QA case

| Item | Value |
|------|--------|
| Case ID | `case_4e5adf36c637` |
| Case ref | `CLM-0031` |
| Persona | 陈明 · 2020 Toyota Camry (`chen_camry`) |
| Environment | Cloud QA only (`fiqa-api-qa`) |

## Validated workflow

Customer intake  
→ Request More (VIN)  
→ customer VIN supplement  
→ broker acknowledgement（已核对补充资料）  
→ office-material acceptance（确认资料已齐）  
→ office processing（办公室处理中）

Idempotency checked: one ack event, one accept event; open Request More blocked accept (409). No `broker_done` / Close on the path.

## Evidence folder (SSOT)

Primary pack (committed with validated commit):

`docs/evidence/qa-fast-lane/20260803T190949Z-final-phone/`

Supporting files: `qa-results.md`, `go-no-go.md`, `closure-summary.json`, `timeline-export.json`, `case-final.json`, ack/accept snapshots, `metrics.csv`.

Phase A / pre-phone workspace (partial, largely superseded):

`docs/evidence/stage1-founder-validation-2026-08-02/` — see classification in that folder’s README. Only unique non-duplicated diagnostics were retained for git.

## What “Founder-validated” means

- Founder phone + broker workbench path completed on Cloud QA for one Chen Camry case.
- The Stage 1 happy path above is proven end-to-end with evidence.
- Freeze candidate on commit `826fa39` is accepted; tag marks that freeze point.
- Safe baseline for Stage 2 product work without casually rebuilding the frozen path.

## What it does not mean

- Not customer / paid-pilot validation.
- Not a Production release or Production data certification.
- Not waterwoods retarget or Production behavior change.
- Not proof that every edge case, invite cold-start, or multi-instance invite store is hardened.
- Not authorization to start LangGraph, OCR expansion, or broad workflow refactoring.

## Known non-blocking Stage 2 issues

1. **Known-customer insurance-card upload is redundant.** ~~Known customers still asked for insurance-card upload.~~ **Addressed in Stage 2** (`stage2/known-customer-prefill-confirm`, commit `8b6ca01`, case `case_09ad6254614a`): CONFIRM_EXISTING → Cap2 `已有保单资料，客户已确认`. See `docs/evidence/STAGE2_FOUNDER_VALIDATED_CLOSEOUT.md`.
2. **Demo invite store is process-local.** ~~Cold start / second instance could miss invite tokens.~~ **Hardened in Stage 2** via Postgres-durable demo invite store on QA; still re-issue if an invite is expired/revoked.
3. **Stale customer context / revoked dit soft-fails** can block phone Stage 1 until Fresh reset / new invite (diagnosed 2026-08-02; not on the final GO path). Stage 2 adds Mini Program fail-closed when launch `dit` redeem fails (no silent fall-through to prior Active Case).
4. **Value metrics gaps:** broker-first-open time is not recorded; AI accept/edit/reject rates have no events yet (see Metrics V1 tool notes).
5. **Generic copy `请先完成这一步`** — Low / non-blocking (UX ledger L3); recorded at Stage 2 phone closeout.

## Frozen components (do not casually rebuild)

- Customer Start Claim → formal submit → workbench visibility for the Chen Camry QA path
- Request More (VIN) → same-session customer supplement → `broker_review_ready`
- Broker「已核对补充资料」+ idempotency
- Broker「确认资料已齐」/ office-materials accept + idempotency + open-Request-More accept block
- Claim Timeline events used for the above path
- Cloud QA targeting for Founder QA (`fiqa-api-qa`, min=0 / max=2 cost-saving posture)

Future Stage 2 work should extend beside this chain, not replace it without Founder decision.
