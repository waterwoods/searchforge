# Founder Inspection Notes — What to Skim First

Use this as a **15-minute reading order** before demos or hiring conversations.

---

## 1. Start here (5 min)

| Doc | Why |
|-----|-----|
| `01_FLOW_ARCHITECTURE_BLUEPRINT.md` | One-page mental model + mermaid |
| `02_CURRENT_FLOW_SYSTEM_MAP.md` | Layers + responsibility table |

---

## 2. Add-car (5 min)

| Doc | Why |
|-----|-----|
| `03_ADD_CAR_FLOW_DEEP_DIVE.md` | Flagship flow end-to-end |

---

## 3. “Why does engineering say it’s in one file?” (5 min)

| Look at | What you’ll see |
|---------|------------------|
| `services/fiqa_api/inbox_triage/triage.py` — function list / `triage_conversation` | Volume of orchestration + commercial branches |
| `configs/clients/chen_kui/handoff_phrases.json` | What you *can* edit without Python |
| `configs/clients/chen_kui/ui_copy.json` | Portal wording the product sees |
| `scripts/guardrail_inbox_triage.sh` | What must stay green before ship |

---

## 4. Questions to ask the team after reading

1. **Which customer-visible strings are still hardcoded in Python?** (Handoff patches, reroute messages, edge-case replies.)
2. **Which script proves add-car timing?** (`run_handoff_timing_simulations.py` + add-car batteries.)
3. **Do we want `ask_driver_only` editable from Rules Center?** If yes, align `config_loader` with `triage.py`.

---

## 5. Red flags (not seen today, watch for)

- Changing `triage_conversation` **without** updating scenario packs.
- Adding a new flow **without** deciding: marker pack vs code vs LLM.
- Duplicating handoff strings in UI **and** backend **and** email templates **without** an inventory.

---

## 6. Green flags (current strengths)

- Clear **single deployment unit** (FastAPI service + static UI).
- **Guardrail** encodes “definition of done” for intake.
- **Client pack** pattern (`CLIENT_ID`, `handoff_phrases`, `ui_copy`) already supports white-label iteration.
