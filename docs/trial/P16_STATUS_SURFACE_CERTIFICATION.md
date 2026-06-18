# P16 Status Surface Certification

**Sprint:** P16-P1-CUSTOMER-STATUS-SURFACE-SPRINT  
**Date:** 2026-06-07  
**Preview URL:** https://ui-emtvr6y44-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer  
**Evidence:** `docs/trial/P16_STATUS_SURFACE_SIMULATION_REPORT.md`

---

## 1. North Star Compliance

**Customer Must Always Know The Status** — can the customer answer without calling the office?

| Question | Surface | Result |
|----------|---------|--------|
| Did I submit my request? | **Status** section: `Saved — Not Yet Submitted` or `Submitted To Office` | ✅ |
| What is still missing? | **Still Needed** bullet list from `still_needed_fields` (never count-only) | ✅ |
| What is the current contact state? | **Contact State**: Waiting For Customer / Office Reviewing / Broker Reviewing | ✅ |

---

## 2. Constitution Compliance (Rules 1–7)

| Rule | Review | Result |
|------|--------|--------|
| **1 — No Login** | Phone + optional name entry only; no OTP, no password | ✅ |
| **2 — Phone Is The Return Key** | Active-case lookup by normalized phone; new-device return (Sim G) | ✅ |
| **3 — One Customer = One Active Case** | Second `start-add-car` → 409 (Sim F) | ✅ |
| **4 — Progress = Missing Fields (+ status dimensions)** | Three sections: Status, Still Needed, Contact State; no fake progress bar | ✅ |
| **5 — Only Broker Closes** | No customer close control on status card | ✅ |
| **6 — Broker Controls Final Action** | Continue Request + Contact Broker CTAs only | ✅ |
| **7 — One Active Add-Car Case** | Lookup returns single newest case; block second vehicle | ✅ |

**SLA constraint:** No hard timing promises. Optional broker expectation copy only (`Your broker usually responds within one business day` on Broker Reviewing). ✅

---

## 3. Preview Verification

| Check | Result |
|-------|--------|
| Customer tab loads | ✅ HTTP 200 |
| Status surface strings in bundle | ✅ `Active Add-Car Request`, `Contact State`, `Still Needed` |
| No login gate added | ✅ |
| API target | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |

**Manual QA path:** Open Preview → 客户报送 tab → enter phone → active case shows three-section status card.

---

## 4. Deployment Result

| Artifact | URL / ID |
|----------|----------|
| **Preview (QA)** | https://ui-emtvr6y44-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer |
| Vercel deployment | `ui-emtvr6y44-andys-projects-1f411b73.vercel.app` |
| Bundle | `index-CfDJTcYx.js` |
| Local API simulations | 8/8 PASS @ `:8001` |

**Backend note:** Cloud Run revision pending promotion for `status_label` / `contact_state` on `/customer/active-case`. UI includes client-side resolution fallback until backend ships.

---

## Verdict

```
╔══════════════════════════════════════════════════════════╗
║  P16-P1 CUSTOMER STATUS SURFACE                          ║
║                                                          ║
║  CONDITIONAL GO                                          ║
║                                                          ║
║  Preview URL works · Status card ships · No login/OTP    ║
║  Promote Cloud Run for submitted-case API live truth     ║
╚══════════════════════════════════════════════════════════╝
```

**Preview URL:** https://ui-emtvr6y44-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

---

*End of P16 Status Surface Certification*
