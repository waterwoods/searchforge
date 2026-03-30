# Founder Inspection Notes

## What to skim first

1. `configs/clients/socal_precision/handoff_phrases.json` → `stitched.append_boundary` — **this is the new “voice dial”** for append-boundary customer text.
2. `services/fiqa_api/inbox_triage/triage.py` — search `_APPEND_BOUNDARY_DEFAULTS` — **engine defaults** if a client omits the block.

## Quick manual check

- **Client B append after add-car, billing pivot:** draft should read **本所** / **转交本所**, not **办公室**.
- **Client A:** same scenario should still read like before (**办公室** continuity) if no config change.

## What did not move

- **Rules** for same vs new vs borderline remain in Python.
- Broker-facing **Case boundary:** lines are still English in code—fine for internal workbench; not customer chat.

## Risk posture

- **Low** if guardrails green: defaults preserve Chen-path wording; only clients that **opt in** with `append_boundary` change.

## A/B wording comparison (high level)

| Moment | Client A (defaults) | Client B (socal pack) |
|--------|---------------------|------------------------|
| New issue continuity (add-car prior) | 加车这边**办公室**会继续跟进 | 加车核价事项**本所**会继续跟进 |
| Billing tail | …转给**办公室**核实 | …转交**本所**核实 |
| Borderline | …整理给**办公室** | …转交**本所** |

## Before / after leak check (one-liner)

- **Before:** B forced **办公室** on append boundary despite **本所** elsewhere.
- **After:** B boundary copy aligns with second-broker pack; A unchanged without edits.
