# Add-Car Edge-Case Hardening + Broker Confidence — Final Report

Consolidated summary; mirrors the sprint chat report structure.

## Sprint theme

- **Chosen:** Add-Car edge-case hardening + broker confidence.  
- **Why now:** Real customers are messy; the flagship flow must not look “wrong playbook” or “wrong car” in front of a broker.

## Document set created

- `00_INDEX.md` through `09_FINAL_REPORT.md` in this folder.

## Baseline edge-case audit (pre-fix)

- **Biggest strength:** Quote-ready rules + materials-sent + garaging side-Q handling already mature.  
- **Biggest broker-confidence risk:** Template order treated **premium-review before add-car** when both markers fired.  
- **Biggest fragile edge case:** `_extract_add_car_vehicle_concrete` unreachable branches for **宝马/本田/丰田** after `if not model:`.  
- **Biggest commercial-feel risk:** Customer asks **“便宜吗/大概多少钱”** mid–add-car and hears **renewal** wording.

## Loops 1–3 (executed)

1. **Audit + run packs** — Identified issues above; ACE scenarios drafted.  
2. **Fix + sim** — Code + JSON + runner; tuned `expected_handoff_after_turn` for ACE04/ACE12.  
3. **Retest** — `guardrail_inbox_triage.sh` PASS; 63/63 multi-turn strong; stress + handoff timing PASS.

## Loop 4

- **Not run** — No single additional fix cleared the “low risk / high ROI / evidence-backed” bar without scope creep.

## Code changes summary

- `services/fiqa_api/inbox_triage/triage.py`  
- `configs/customer_entry_multi_turn_simulations.json`  
- `scripts/run_add_car_edge_case_simulations.py`

## Deployment

- **Backend:** Redeploy recommended for any environment that should show these triage changes.  
- **Frontend:** No change.  
- **Verified in prod this session:** No — local and guardrail only.

## Final judgment

- **Biggest gain:** Correct office playbook for **add-car + price worry** + **accurate Chinese vehicle line**.  
- **Biggest remaining weakness:** Very long threads with **multiple vehicles** without explicit correction still rely on broker reading raw messages.  
- **Serious broker review:** **Yes, stronger** after this sprint, pending founder UI spot-check and backend deploy to review environment.
