# P16-R Phase 7 — Real User Test Matrix

**Date:** 2026-06-01  
**Sprint:** P16-R Deployment Parity & Reality Closure  
**Rule:** Every row must cite **deployed URL** + evidence type

---

## Andy (founder)

| Field | Value |
|-------|-------|
| **Starting URL** | Local: `http://127.0.0.1:5173/workbench/unified-intake` · Preview: `https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake` |
| **Task** | Paste cancellation notice → submit → open queue → open case → copy draft → append follow-up |
| **Expected result** | Case in queue; draft editable; copy works; append on same case |
| **Evidence required** | 15-min log + timestamps; Preview requires screenshot after SSO fix |
| **P16-R status** | Local ✅ (`demo_quick_validate` PASS); Preview **blocked** (401 cold) |

---

## Customer (end customer)

| Field | Value |
|-------|-------|
| **Starting URL** | **No production customer URL** · Preview customer tab hidden (product_only) · Full dev local `:5174` or future customer route |
| **Task** | Open entry → type message → send → see trust line → optional handoff confirm |
| **Expected result** | P16-O: headline `请把您的需求发给我们`, CTA `发送给办公室`, no 3-button grid |
| **Evidence required** | Screenshot empty state + post-submit card; bundle grep on deployed URL |
| **P16-R status** | Local ✅; Preview bundle ✅ (cold UI ❌); Production ❌ pre-P16-O |

---

## Assistant (办公室助理)

| Field | Value |
|-------|-------|
| **Starting URL** | Same broker workbench URL as Andy |
| **Task** | Monitor queue → open case → copy draft for WeChat → mark next step |
| **Expected result** | Single office surface; no simulation tab; paste-first copy |
| **Evidence required** | Screenshot queue + draft panel; no 401 on URL |
| **P16-R status** | Local ✅; Preview **blocked** SSO; Production ❌ wrong tabs |

---

## Chen Kui (broker principal)

| Field | Value |
|-------|-------|
| **Starting URL** | Must **not** be Production `ui-smoky-beta` (wrong UI). Target: Preview alias after SSO off |
| **Task** | WeChat-forward cancellation paste → read urgency → copy reply draft |
| **Expected result** | &lt;10 min; no engineer tabs; Chinese office context |
| **Evidence required** | Timed screen recording; minutes-saved note |
| **P16-R status** | **Cannot start** — Preview 401; Production wrong surface |

---

## Role C (skeptical operator)

| Field | Value |
|-------|-------|
| **Starting URL** | Production `https://ui-smoky-beta.vercel.app/workbench/unified-intake` (cold stranger test) |
| **Task** | Open link from message → understand what to do in 10s |
| **Expected result** | Obvious paste/send; no SSO; no 4-tab confusion |
| **Evidence required** | Browser snapshot; 10s comprehension note |
| **P16-R status** | Production **fails** (4 tabs, 加车 default); Preview **fails** (401) |

---

## Matrix summary

| Role | URL today | Can complete task? | Evidence |
|------|-----------|-------------------|----------|
| Andy | Local | ✅ | guardrail + validate logs |
| Andy | Preview | ❌ cold | needs SSO off + E2E log |
| Customer | Production | ❌ | wrong UI |
| Customer | Preview bundle | 🟡 | grep only |
| Assistant | Preview | ❌ | SSO |
| Chen Kui | Any deployed | ❌ | no broker-stable URL |
| Role C | Production | ❌ | P16-Q snapshot still true |

---

*End of P16-R Phase 7 — Real User Test Matrix*
