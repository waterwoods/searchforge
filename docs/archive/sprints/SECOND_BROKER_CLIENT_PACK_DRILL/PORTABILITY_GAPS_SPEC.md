# Portability Gaps Spec

## A. Real gaps (engine or shared config)

1. **Materials-sent warm path (`triage.py`)**  
   Hardcoded ZH/EN such as: *您说材料已发，**办公室**会按加车报价流程…* — ignores client pack “本所” voice.

2. **Premium / “先问问多少钱” stitching (`triage.py` ~636)**  
   Appends *具体数字要等**办公室**按车型和地址算出来* — can bypass concise `reply_overrides` feel.

3. **Many other handoff suffixes** (coverage question, doc clarification suffixes, “why still chasing”, etc.)  
   Mix of **办公室** / generic lines not loaded from client config.

4. **Industry `markers.json` still names Chen Kui** under `talk_to_agent`  
   Second broker customers who say another agent’s name won’t match unless we add per-client marker extensions or keep names out of industry.

5. **Add-car rules + soft-route copy**  
   Industry/common only — second broker cannot tune “next question” or button reroute text without sharing or new config layers.

6. **Frontend `DEFAULT_UI_COPY`**  
   Chen-specific; only safe if API always succeeds and `?client=` is always set for non-Chen demos.

## B. Operational / false portability

- **`get_handoff_phrases` fallback to `chen_kui`** when a client folder is incomplete — must be documented in onboarding checklists.

## C. Minimal next fixes (same-industry, still no tenancy platform)

| Fix | Effort | Impact |
|-----|--------|--------|
| Move handoff “stitched” sentences into `configs/common/` or client-overridable map keyed by `client_id` | Medium | High voice consistency |
| Remove broker proper nouns from industry `talk_to_agent`; optional `configs/clients/<id>/talk_to_agent_markers.json` | Medium | Cleaner industry boundary |
| Per-client optional `soft_route_inbox.json` overlay | Small–medium | Button path sounds like broker |
| Optional per-client `add_car_rules` overlay | Medium | Second broker tuning without forking industry file |

## D. What not to do yet

- Full multi-tenant auth, per-row DB isolation, dynamic config CDN — out of scope for this drill.
