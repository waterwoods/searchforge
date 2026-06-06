# Safe Refactor / Risk Guard Spec

## Non-negotiables

1. **No clean rewrite** of `triage_conversation` or case append in a “productization” pass.
2. **Guardrail green** before merge: `bash scripts/guardrail_inbox_triage.sh`.
3. **Reversible changes:** Prefer config additions with code defaults over deleting fallbacks.
4. **Client isolation:** Never apply one broker’s `reply_overrides` to another client by implicit fallback.

## Pre-merge checklist (Unified Intake)

- [ ] `LLM_GENERATION_ENABLED=0` scenario packs pass (guardrail runs them).
- [ ] Client-aware tests: `scripts/test_client_aware_handoff.py --direct`
- [ ] Append identity: `scripts/test_client_identity_append.py --direct`
- [ ] If routes or triage touched: run full guardrail (includes multi-turn, adversarial, boundary, handoff timing).

## Red flags (stop and reassess)

- Moving **conditional policy** into JSON without new scenarios.
- Changing **persist_case** conditions without explicit design review.
- Caching templates **without** client key (this sprint fixes reply template cache keying).

## If something fails

1. Reproduce with the smallest script from guardrail output.  
2. Revert the last change; re-run guardrail.  
3. Re-apply in smaller commits (config-only vs code-only).
