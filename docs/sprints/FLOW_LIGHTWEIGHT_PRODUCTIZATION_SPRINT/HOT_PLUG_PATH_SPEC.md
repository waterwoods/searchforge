# Hot-Plug Path Spec

Realistic assessment of **onboarding another client** without overselling.

## Same industry (another auto broker office)

**Close for:** Handoff phrases, UI copy, reply overrides — all keyed by `client_id` + `configs/clients/<id>/`.

**Still requires work:**

- Deploy/runtime: set `CLIENT_ID` (or pass `client_id` on API calls from a future multi-tenant UI).
- Knowledge/RAG paths: `knowledge_paths.py` still references client folders explicitly for some assets — review when adding a production second client.
- Founder QA: run guardrail + a short manual demo script for the new folder.

**Verdict:** *Prototype-hot-plug ready* for **copy + handoff voice**; not full “zero-touch SaaS tenant.”

## Cross-industry

**Reusable:** Persistence patterns, session pattern, scenario runner harness, “structured triage output” contract.

**Heavy lift:** New industry pack (markers, templates, rules), new lexicon, likely new triage branches or LLM prompts — out of scope for this sprint.

## Explainability

After this sprint, a founder can point to:

1. **Engine** — `triage.py` + `case_store.py`  
2. **Industry pack** — `configs/industries/insurance/`  
3. **Client pack** — `configs/clients/<id>/`  
4. **Common copy** — `configs/common/workflow_defaults.json`, `soft_route_inbox.json`  
5. **Tests** — `scripts/guardrail_inbox_triage.sh`

The largest remaining explainability gap is still **orchestration density** inside `triage.py` — documented, not hidden, but not yet “small files per flow.”
