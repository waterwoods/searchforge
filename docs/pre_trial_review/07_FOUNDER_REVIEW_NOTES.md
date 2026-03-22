# Founder Review Notes

**Sprint:** Pre-Trial Review Sprint  
**Created:** 2026-03-18

---

## 1. Before First Trial

| Step | Action |
|------|--------|
| 1 | Run `bash scripts/trial_launch_check.sh` — must PASS |
| 2 | Run `bash scripts/run_demo_local.sh` |
| 3 | Open http://localhost:5173/workbench/unified-intake |
| 4 | Load founder demo queue — verify 13 cases; cancellation opens first |
| 5 | Run SIM1, SIM2, SIM3 in Simulation Assistant |
| 6 | Read `docs/trial/FOUNDER_LAUNCH_NOTES.md` |
| 7 | Bring `docs/trial/BROKER_TRIAL_ONE_PAGER.md` |
| 8 | Copy `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md` for broker |

---

## 2. What to Inspect During First 3–5 Real Conversations

| Watch for | Why |
|-----------|-----|
| Broker hesitates at paste | May not know what to paste; give example |
| Broker ignores Collected chips | May not trust; point out Human confirmation |
| Broker rewrites draft completely | Draft quality; note for iteration |
| Broker can't find next move | Visibility; may need UI tweak |
| Broker confused on reopen | Resume here; waiting_on clarity |
| **Talk to Agent flow** | If customer says "联系人工" — does it work? |
| **Correction / already_sent** | Does broker see when customer said "already sent"? |

---

## 3. Trust-Breaking vs Acceptable

| Trust-breaking (fix now) | Acceptable (fix next or defer) |
|--------------------------|--------------------------------|
| Broker says "I can't use this" | Manual evidence pack |
| Talk to Agent routes wrong | Copy case snapshot works |
| Next move always generic | Some scenarios need refinement |
| Broker can't find next move | — |

---

## 4. Post-Trial

1. Copy observation log to `results/trial_logs/{broker}_{date}.md`
2. Fill Friction Classification table
3. Use `docs/trial/FIX_NOW_QUEUE_SPEC.md`
4. Copy `docs/trial/FIX_NOW_QUEUE_TEMPLATE.md`; fill and save
5. Add fix-now items to next sprint backlog

---

*End of Founder Review Notes*
