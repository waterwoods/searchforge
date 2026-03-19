# Small-Business Readiness — Evaluation / SLA Criteria

**Sprint:** Small-Business Readiness Stress Test  
**Date:** 2026-03-14

---

## Practical Standards

### A. Turn 1 Latency

| Level | Target | Notes |
|-------|--------|-------|
| **Acceptable** | ≤ 8 s warm | Broker feels "it’s working" |
| **Tolerable** | 8–12 s warm | Noticeable but usable |
| **Risky** | 12–20 s warm | "Is it broken?" risk |
| **Too slow** | > 20 s warm | Likely abandonment |

**Cold start:** 5–15 s extra is expected; first request after idle. Mitigation: warmup script, keep-alive.

---

### B. Multi-Turn Responsiveness

| Level | Target | Notes |
|-------|--------|-------|
| **Acceptable** | Turn 2+ simple < 2 s | Fast path (rules) |
| **Tolerable** | Turn 2+ simple 2–5 s | Still acceptable |
| **Risky** | Turn 2+ simple > 5 s | Should use fast path |

---

### C. Language Smoothness

| Level | Criterion |
|-------|-----------|
| **Strong** | Feels like a real office assistant; no robotic markers |
| **Acceptable** | Occasional formal phrasing; generally natural |
| **Weak** | "Thank you for reaching out", "Feel free to ask", teaching tone |
| **Risky** | Generic, legal-sounding, or obviously AI |

---

### D. Case Report Usefulness

| Level | Criterion |
|-------|-----------|
| **Strong** | Accurately reflects conversation; clear next step; broker can act |
| **Acceptable** | Minor inaccuracies; next step actionable |
| **Weak** | Wrong collected/still needed; next step vague |
| **Risky** | Misleading; could cause wrong broker action |

---

### E. Trust / Safety Perception

| Level | Criterion |
|-------|-----------|
| **Strong** | "Human confirmation recommended" visible; broker knows nothing auto-sends |
| **Acceptable** | Trust boundary visible; minor confusion possible |
| **Weak** | Unclear what is AI vs human; auto-send ambiguity |
| **Risky** | Could appear to auto-send; no clear human gate |

---

### F. What Counts as Too Risky for Demo/Pilot

- Turn 1 consistently > 20 s warm
- Case report wrong in core scenarios (cancellation, add-car, missing-doc)
- Language so robotic that broker would not send draft to client
- Trust boundary invisible (broker thinks it auto-sends)
- Guardrail / regression scripts fail

---

*Used for: Baseline audit, scenario evaluation, final judgment*
