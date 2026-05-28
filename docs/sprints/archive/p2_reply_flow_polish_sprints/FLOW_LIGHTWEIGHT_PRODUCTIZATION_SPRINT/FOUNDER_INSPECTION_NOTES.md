# Founder Inspection Notes

**How to explain the product architecture in a meeting**

1. **“The engine”** — One Python module (`triage.py`) decides what the customer sees next and when the broker gets a handoff. It is intentionally dense; we are not rewriting it this quarter in one shot.

2. **“The insurance pack”** — JSON under `configs/industries/insurance/` for markers, reply templates, category guidance, and add-car “what to ask next” lines.

3. **“The client pack”** — JSON under `configs/clients/chen_kui/` (and `demo_broker/` for demos) for office voice: handoff phrases, UI labels, optional reply overrides.

4. **“Common tuning”** — `configs/common/` for workflow fallbacks and soft-route button copy (reroute + first message when the model was vague).

5. **“Proof it works”** — One command runs dozens of scripted conversations: `bash scripts/guardrail_inbox_triage.sh`.

**What improved this sprint**

- Reply templates respect **which client** is active (overrides no longer hardwired to one folder name in code).
- Soft-route customer-facing lines can be edited in **`configs/common/soft_route_inbox.json`** without opening the route file.
- Add-car config on disk matches what the engine reads for **driver-only** follow-up prompts.

**What to say when asked “is it multi-tenant?”**

- “**Config and API are client-aware**; production multi-tenant still needs hosting, auth, and knowledge path review.”
