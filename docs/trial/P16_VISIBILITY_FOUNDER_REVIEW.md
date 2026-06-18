# P16 Visibility — Founder Review

**Persona:** Chen Kui (陈奎) office — product-only pilot  
**Question horizon:** 5-second desk scan after customer formal submit

---

## Can Chen Kui immediately find the new customer case?

| Before | After |
|--------|-------|
| Scroll past ~11 demo/action cards | **#7 in realistic queue; #1 if only demo noise** |
| Card shows WeChat wall of text | **“2024 Tesla Model Y” headline + case ID** |

**Answer:** **Yes**, when the case lands on the loaded page (API already returns it on page 1).

---

## Can office identify vehicle / missing info / next step within 5 seconds?

| Signal | Visible on card (after) |
|--------|-------------------------|
| Vehicle | Bold `primary_vehicle_summary` |
| Case ID | Mono short ID, copyable |
| Submitted status | Green 已正式送达 + status strip |
| Missing fields | Orange 待补问 line |
| Next step | 办公室侧下一步 preview (中文) |

**Answer:** **Yes** — no need to open full case for triage scan.

---

## Would this increase pilot trust?

| Trust factor | Impact |
|--------------|--------|
| Customer submits → office sees it | **High** — fixes “did it arrive?” anxiety |
| Same case ID as customer portal | **High** — copyable ID on card |
| Demo noise demoted | **Medium** — cleaner trial desk |
| Urgent cancel/pay still on top | **High** — office knows priorities preserved |

**Answer:** **Yes** — aligns product behavior with certified backend truth.

---

## Founder verdict

| Question | Verdict |
|----------|---------|
| Ready for Chen Kui desk trial? | **Yes** |
| Blockers? | None for visibility scope |
| Follow-up (out of sprint)? | Optional: “新近报送” pin if queue >50 |

---

## Sign-off

**Founder simulation: APPROVE** for visibility sprint GO.
