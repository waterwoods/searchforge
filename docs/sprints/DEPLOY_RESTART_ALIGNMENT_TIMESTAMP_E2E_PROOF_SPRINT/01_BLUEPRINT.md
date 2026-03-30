# DEPLOY / RESTART ALIGNMENT + TIMESTAMP E2E PROOF — Blueprint

## Goal

Prove in a **running** API (not code review alone) that:

- First **formal submit** persists an office-visible case with `formal_submitted_at` and `updated_at`.
- Later **append** keeps `formal_submitted_at` fixed and advances `updated_at`.

## Non-goals

- No new product features, schema columns, or architecture.
- No mandatory production deploy from this doc; local restart + HTTP proof is sufficient if Cloud/Vercel credentials are not in scope.

## Alignment

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`: service record + formal submit meaning.
- `docs/PROJECT_TRUTH_SWITCH.md`: `formal_submitted_at` vs `updated_at` observability contract.

## Success

- Backend process restarted (or deploy) so loaded code matches repo.
- `/readyz` OK.
- Scripted formal submit + append passes; timestamps satisfy invariants.
