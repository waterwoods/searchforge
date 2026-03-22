# Queue Preview Chinese Consistency Blueprint

**Sprint:** Queue Preview Chinese + Workbench Language Consistency Sprint  
**Created:** 2026-03-20

---

## Why language consistency matters now

The Chen Kui Insurance Unified Entry product is increasingly credible:
- Customer entry is stronger
- Add-Car is more realistic
- Workbench is more office-like
- Persistence is understood
- Handoff quality is better

But remaining mixed language and internal wording still weakens polish and product trust. Brokers notice:
- Queue preview strings in English ("Ready to act", "Needs more info", "Quote-ready")
- Structured field labels in English ("Year", "Make/Model", "Collected:", "Missing:")
- Case focus labels mixing English ("Add car quote", "Claim intake") with Chinese
- Copy-case-snapshot output in English

## Why this is a high-ROI polish step

- **Low risk:** Wording-only changes; no logic or demo-queue behavior
- **High visibility:** Queue cards and case detail are the primary broker touchpoints
- **Quick win:** Concentrated in `UnifiedIntakePage.tsx` and a few helpers
- **Trust impact:** Consistent Chinese office language signals "this is a real tool for us"

## What this sprint will improve

1. **Queue readiness labels** — Replace English ("Ready to act", "Needs more info", etc.) with office-oriented Chinese
2. **Compact queue preview** — Replace "Collected:", "Missing:", flow names with Chinese equivalents
3. **Case focus labels** — Use consistent Chinese where broker-facing (加车报价, 事故报险, 保费复查, etc.)
4. **Structured field labels** — Broker-facing labels in Chinese (已收集 / 还缺 already exist for section headers; field names need Chinese)
5. **Case report one-liner** — "Ready for handoff" / "Collecting" → 可交办公室 / 信息收集中
6. **Draft readiness / copy-snapshot** — Minor wording polish for office tone

## What this sprint will NOT do

- Demo queue loading behavior
- Backend architecture or API
- OCR, quote engine, major workflow changes
- Major UI redesign
- SimulationAssistant internal display (lower priority; broker rarely sees)

---

*Part of Queue Preview Chinese + Workbench Language Consistency Sprint*
