# Final report — ROLE C 7–8 Turn Live Battery + Issue Harvest

## Environment

- **Backend:** `http://127.0.0.1:8001` (live process on workstation; `/health/live` 200).
- **Why not remote:** No guaranteed Cloud Run URL or credentials in this run; local demo stack satisfied “reachable API + Role C + OpenAI” (Role C returned `llm_used: true`, `gpt-4o-mini`).
- **Artifacts:** Full per-turn capture written to workspace `.tmp_role_c_harvest.json` (local only; not committed). Wall clock: `2026-03-30T01:58:20Z` → `2026-03-30T02:00:38Z` (~2.3 min API time for 45 customer turns + 6 persist probes).

## Cases executed

C1–C6 as in `02_BATTERY_SPEC.md` (45 Role C + triage turns total).

## Directly verified

- Multi-turn Role C + triage through 7–8 turns without HTTP failures.
- `lifecycle_status` progression to `handoff_pending` and, after formal-submit probe, `handed_off` with `case_id`.
- **Append path:** `formal_submitted_at` unchanged after `append-message`; `updated_at` advanced (case `case_ae05f43fb8ba`).

## Top issues (ranked)

1. **`name` extraction gap vs `handoff_ready` / `quote_ready`** — Multiple runs (C2–C5) kept `still_needed_fields: ["name"]` after the customer explicitly gave a Chinese name, while `handoff_ready` stayed true and office-forward replies fired. Persist probes saved cases in that inconsistent state. **Hurts right rail and broker trust.**
2. **Post–handoff-pending reply loop** — Late turns (e.g. C1 turns 3–7) repeated the same deductible deferral block and did not answer direct questions (“几天内回复”). **Hurts listening quality and demo credibility.**
3. **Copy contradicts structured state** — Replies such as “资料已到办公室” / “已进入办公室处理阶段” while structured bar still shows missing `name`. **Trust and state coherence.**
4. **Triage classification noise** — e.g. C1 post-complete `issue_category: missing_document`; C3 turn 1 empty `collected_fields` / `still_needed_fields`. **Workbench / analytics and edge stability.**
5. **Simulation realism leaks** — Lines prefixed with `客户:` (C4, C6); repeated placeholder identity (陈奎 / 123-456-7890); obvious synthetic VINs. **Persona fidelity, not engine logic.**

## Strengths observed

- Add-Car lane stayed mostly on-task across personas.
- `formal_submitted_at` vs `updated_at` story holds on append (spot check).
- Role C difficulty “tough” produced more probing customer language than “realistic” in places.

## Recommended next sprint (product-valued)

Bounded **identity extraction + handoff_pending copy guardrails**: reconcile `handoff_ready` with required contact fields, and make late-turn replies answer timing / submit questions without repeating one template. (No architecture sprint.)
