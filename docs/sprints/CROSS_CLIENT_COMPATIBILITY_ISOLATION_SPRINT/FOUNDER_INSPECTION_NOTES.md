# Founder Inspection Notes

## What to click / run

1. **Config diff:** Open `configs/clients/chen_kui/handoff_phrases.json` and `configs/clients/socal_precision/handoff_phrases.json` — scroll to `"stitched"`. Same keys; different tone.
2. **A/B runner:**  
   `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_cross_client_ab_scenarios.py -v`  
   Read drafts for ab_03 vs ab_04 and ab_05 vs ab_06 — clearest before/after isolation proof on Add-Car-adjacent paths.
3. **Full safety net:** `bash scripts/guardrail_inbox_triage.sh`

## What to be skeptical about

- **ab_10** still passes with 办公室 for **both** clients — that is intentional documentation of a **remaining** shared-engine leak (append new-issue Chinese), not a product win yet.
- **`get_handoff_phrases`** Chen fallback for **missing** client files is still real — incomplete third packs could pick up Chen handoff lines until files exist.

## Commercial framing

- **Demo / controlled pilot:** Credible that a second broker can run Add-Car flows with distinct stitched reassurance lines **without** code changes.
- **“Fully hot-plug” claim:** Still requires follow-up for append-boundary copy and a few add-car overlays (coverage suffix, etc.).

## 一眼结论

加车高频的「材料已发 / 要不要先发你 / 怎么还在追」三条话术，现在可以按客户在 JSON 里分家；同线程追加新问题的边界话术还在共用引擎里。
