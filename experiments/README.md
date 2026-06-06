# experiments/ — SearchForge R&D

**Status:** LAB ONLY — optional  
**Unified Intake paid pilot:** Not used  
**Mounted in product_only:** No  
**Safe to ignore:** Yes (for operators, founders, support)  
**Archived:** No — active R&D scripts may still run here  
**Experimental:** Yes

---

## Historical purpose

SearchForge experiment runners: retrieval benchmarks, tuner sweeps, graph probes, offline eval batteries.

## Product truth

Unified Intake triage and workbench do **not** depend on this directory. Paid pilot validation uses `scripts/guardrail_inbox_triage.sh` and `scripts/trial_launch_check.sh`.

## When to use

Local R&D, reproducing old experiment results, extending SearchForge lab capability.

## Product path instead

```bash
bash scripts/run_demo_local.sh
bash scripts/guardrail_inbox_triage.sh
```

See: [`docs/archive/platform/README_LAB_INFRA.md`](../docs/archive/platform/README_LAB_INFRA.md)
