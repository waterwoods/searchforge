# Assessment Framework Spec — 12 Macro Goals

**Purpose:** Define what each goal means for **Unified Intake** and how assessors should score it.

**Scoring labels:** Done | Mostly there | Partial | Weak | Missing

**Completion:** Rough percentage (honest band, not false precision).

**Next priority:** Yes | No | Later — based on **narrow paid pilot** and **simplicity**.

---

## Goal 1 — Narrow product positioning

**Means:** Single clear job story: paste → structured case → editable draft → human-controlled handoff; no platform oversell. Aligned with `docs/STANDARD_SCENARIO_PACKAGE.md` and narrow positioning sprint.

**Evidence types:** Founder-facing docs, UI first-screen copy, demo script consistency.

---

## Goal 2 — Frontend feels like a formal service-entry portal

**Means:** Customer Entry reads as **intentional intake** (office-branded, calm, minimal confusion), not an internal dev console or demo playground.

**Evidence types:** `UnifiedIntakePage.tsx` structure, `ui_copy` from client config, absence of confusing dual-purpose chrome where it hurts the broker pitch.

---

## Goal 3 — Final output feels handoff-ready

**Means:** Broker can take **one screen** (or copy block) to the office: category, urgency, next step, collected/needed, draft — credible as a **case result**, not a chat log only.

**Evidence types:** Triage JSON fields, workbench presentation, known semantic edge cases.

---

## Goal 4 — Add-Car flagship path is truly strong

**Means:** Highest-frequency path is **demo-stable**: multi-turn collection, corrections, materials branches, closure/handoff copy, transaction clarity.

**Evidence types:** Markers/rules configs, targeted acceptance (`PRE_BROKER`), scenario packs.

---

## Goal 5 — Human-handoff boundaries are clear

**Means:** Customer understands **what happens next**; broker understands **when human is required**; append vs new issue is not dangerously ambiguous; **no auto-send** implied.

**Evidence types:** Append boundary externalization, handoff phrases, guardrail batteries (`run_case_boundary_battery.py`, etc.).

---

## Goal 6 — Hot-plug / client-pack structure progressing

**Means:** Same engine + industry pack + client pack can swap **voice and broker-specific copy** without silent wrong-office behavior; isolation tests exist.

**Evidence types:** `config_loader.py`, `SECOND_BROKER_CLIENT_PACK_DRILL` outcomes, cross-client A/B scripts in guardrail.

---

## Goal 7 — Database / persistence planned appropriately

**Means:** Persistence matches **pilot honesty**: demo-safe local JSON is OK if narrative is honest; any “production database” ambition is either scoped or explicitly deferred — no accidental promise of enterprise durability.

**Evidence types:** `case_store.py`, env overrides, paid pilot goal non-goals.

---

## Goal 8 — Real pilot feedback readiness

**Means:** Founder can run a **short trial** with observation templates, launch check scripts, and a broker workflow that does not require fake integrations.

**Evidence types:** `docs/trial/*`, `scripts/trial_launch_check.sh`, `trial_readiness_check.sh`, pre-broker acceptance judgment.

---

## Goal 9 — Validation / regression discipline

**Means:** Changes to triage/UI/config are **hard to ship without catching** major regressions on core scenarios, boundaries, and client isolation.

**Evidence types:** `guardrail_inbox_triage.sh` breadth, scenario JSON packs, targeted runners.

---

## Goal 10 — Same-industry migration readiness

**Means:** Second broker is **credible as a drill**, not a fantasy: known leaks listed, fixes prioritized, replication time estimate realistic.

**Evidence types:** Second broker drill report, `socal_precision` pack, residual engine strings audit.

---

## Goal 11 — Sales / monetization framing clear

**Means:** What they pay for, pilot length, success signals, and **what is not included** are documented and consistent with build.

**Evidence types:** `insurance_paid_pilot_goal.md`, monetization specs, standard package wording.

---

## Goal 12 — Product simplicity preserved

**Means:** Surface area and narrative stay **narrow**; avoid becoming an accidental “platform” in UX or code paths without matching capability.

**Evidence types:** UI complexity, number of parallel modes, founder sprint warnings (NARROW_POSITIONING).

---

## Anti-patterns (do not do in scoring)

- Inflating % because “a lot was built.”
- Treating documentation alone as “done” without UI/engine alignment.
- Ignoring known failing or weak acceptance cases.

---

*End of framework spec*
