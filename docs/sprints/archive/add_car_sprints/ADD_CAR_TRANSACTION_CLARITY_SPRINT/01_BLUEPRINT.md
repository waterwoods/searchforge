# Add-Car Transaction Clarity Blueprint

**Sprint:** Add-Car Transaction Clarity (Chen Kui / Unified Entry)  
**Mission:** Reduce “open chat” feel; strengthen **transaction identity** + **handoff closure** together.

## Problem

Add-Car is functionally strong (hybrid intake, quote-ready, materials, corrections, workbench) but can still read as a capable chat thread rather than a **bounded business transaction**: start → collect → submit to office → done.

## Product outcome

| Dimension | Target |
|-----------|--------|
| Current transaction | Customer clearly sees they are in **加车报价** (not generic “messaging”). |
| Progress | Clear contrast: collecting vs quote-ready vs ready for office. |
| Closure | After handoff: **submitted to office / being processed**, not “assistant said something nice.” |
| Boundary | After closure: how to ask **something else** (new request), without endless single thread. |

## Non-goals

OCR, carrier APIs, multi-tenant auth, enterprise ticketing, LLM replacement of rules, non–Add-Car redesign.

## Design principles

1. **Semantics over labels** — copy and layout encode state, not only prettier words.  
2. **One combined fix** — title strip + closure block ship together so “transaction” and “finish” reinforce each other.  
3. **Config-first copy** — Chen Kui strings live in `configs/clients/chen_kui/ui_copy.json` where possible.  
4. **Minimal risk** — UI-only where possible; triage copy only where it improves office-realistic handoff.

## Implementation anchors

- **Customer UI:** `ui/src/pages/UnifiedIntakePage.tsx` — transaction ribbon, progress card title, handoff card structure, toasts.  
- **Client copy:** `configs/clients/chen_kui/ui_copy.json` + `ui/src/api/clientConfig.ts` + `services/fiqa_api/inbox_triage/config_loader.py`.  
- **System handoff reply:** `configs/clients/chen_kui/handoff_phrases.json` + targeted lines in `triage.py` for special add-car branches.

## Success signal

Founder/broker can answer “yes” to: Do I know what transaction this is? Do I know the office has it now? Do I know how to start a different issue?
