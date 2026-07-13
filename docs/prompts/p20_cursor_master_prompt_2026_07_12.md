# P20 Cursor Master Prompt (reusable preamble)

> Paste this preamble at the top of **every** Cursor Agent prompt working on the Insurance Task Platform, then append a short daily task (see `docs/prompts/p20_daily_task_prompt_template_2026_07_12.md`).
> This preamble is intentionally short — it points at the SSOT rather than repeating it.

---

```text
# INSURANCE TASK PLATFORM — MASTER PROMPT (P20)

Repository: /home/andy/searchforge
Branch: sprint/p16-trust-layer  (confirm before editing)

## READ FIRST (in this order)
1. docs/design/p20_production_constitution_master_design_2026_07_12.md   ← highest-level SSOT
2. The module SSOT relevant to today's task (e.g. p19m0 MP architecture,
   CASE_CONTRACT_V1, p20 repository audit, p18_9 AI red-team).
3. docs/design/p20_ssot_migration_map_2026_07_12.md  (which older docs are superseded)
4. docs/CURRENT_PRODUCT_SHAPE.md  (runtime/deploy truth)

## PRODUCT TRUTH (do not relitigate)
- Product = Insurance Task Platform; first vertical = Claim Intake.
- Native WeChat Mini Program = the only formal customer task surface.
- WeCom = entry / notification / reminder / broker communication.
- H5 = fallback / QA / historical / API reference (NOT primary).
- Cloud SQL = the only active DB SSOT. Neon is decommissioned — never reintroduce.
- JSON store = test/dev only.
- Backend owns workflow state. AI is advisory only.
- Customer experiences Tasks; internals manage Cases/Evidence/Timeline/Workflow.

## HARD RULES
- Inspect before editing (git status; read target files).
- Stay inside your Track's file ownership (A = miniapp UI, B = backend core,
  C = integration/security/testing). Track ownership is a CONCURRENCY SAFETY
  rule, not an excuse to ignore a necessary cross-layer interface change.
  Never SILENTLY cross a boundary. If a needed change spans tracks, STOP and
  report: why it is necessary, exact files, owner coordination required, and
  proposed sequence — proceed only after explicit coordination/approval.
  Multiple Agents must not edit overlapping files concurrently.
- No schema migration, deploy, publish, or push unless explicitly requested.
- No new heavy framework (Taro/React/Vue/uni-app); no Temporal/Camunda now.
- No feature invention; no unrelated refactor; no hidden scope expansion.
- Never overwrite customer-confirmed facts silently (provenance guard).
- Never commit secrets/tokens/customer data; never reset/stash/clean the tree.
- Preserve all unrelated working-tree changes.
- Label every WeChat capability: CONFIRMED / ASSUMED FOR PROTOTYPE /
  OFFICIAL VALIDATION REQUIRED. Never state unverified capability as fact.
- Never mark a manual/compliance item PASS without real verification.

## HOW TO WORK
1. INSPECT: repo reality + relevant files; classify findings
   (KEEP / HARDEN / EXTRACT / DEFER / BLOCKER).
2. DESIGN: answer docs/design/p20_design_review_checklist_2026_07_12.md.
3. IMPLEMENT: smallest durable change; additive contract fields only unless
   an explicit contract_version bump is approved.
4. TEST: add regression tests; keep existing tests green; provide evidence.
5. STOP GATES: pause and report if you would touch a Frozen boundary,
   migrate schema, deploy, push, weaken tenant isolation, make AI
   authoritative, or cannot honestly verify a manual item.
6. REPORT: update the handoff summary — what changed, evidence, checklist
   answers, code changed YES/NO, commit created YES/NO, risks for Founder.

## CONTRACT COORDINATION
- Track B owns and publishes docs/design/p20_task_contract_v0.md.
- Tracks A and C consume it; they must not redefine it independently.

## COMMIT POLICY
- Do not commit automatically. Return findings for Founder review first.
- Commit only after explicit approval. Never push unless explicitly asked.
```

---

*Keep this preamble stable. Update only when the P20 Constitution version bumps.*
