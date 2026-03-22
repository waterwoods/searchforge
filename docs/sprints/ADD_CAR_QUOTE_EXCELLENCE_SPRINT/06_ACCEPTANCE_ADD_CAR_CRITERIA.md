# Acceptance / Add-Car Criteria

**Sprint:** Add-Car Quote Excellence  
**Purpose:** Practical criteria for add-car excellence.

---

## 1. Ask-Next Quality

| Criterion | Pass When |
|-----------|-----------|
| No redundant ask | Never ask for field already provided |
| Natural order | vehicle → zip → delivery/driver |
| Acknowledgement | "好的，2024年的。" before next ask when applicable |
| One ask per turn | 1–2 items max, not 6 |

---

## 2. Quote-Readiness Usefulness

| Criterion | Pass When |
|-----------|-----------|
| Handoff threshold | vehicle + zip + (delivery or driver) |
| No under-filled handoff | Never hand off with only year or only zip |
| First-turn handoff | When full info in T1, hand off immediately |

---

## 3. broker_next_step Usefulness

| Criterion | Pass When |
|-----------|-----------|
| Actionable | "Run quote" + "Confirm delivery/driver" |
| Concrete when possible | Vehicle (year, model) mentioned |
| No generic | Not "Review and follow up" only |

---

## 4. Handoff Timing

| Criterion | Pass When |
|-----------|-----------|
| HT1 | Add-car + driver T3 — ask driver T2, handoff T3 |
| HT5 | Correction — T2 correct, T3 zip+delivery, handoff T3 |
| HT8 | Add-car + garaging same turn — answer, handoff T2 |

---

## 5. Realistic Corrections

| Criterion | Pass When |
|-----------|-----------|
| Vehicle correction | "不是X5，是X3" → collected shows X3 |
| ZIP correction | "ZIP 改成 92620" → collected shows 92620 |
| Driver correction | "是我老婆开" → collected shows primary_driver |

---

## 6. Founder Demo Quality

| Criterion | Pass When |
|-----------|-----------|
| 4–6 flows demoable | Add-car variants (full T1, partial, correction, garaging, coverage) |
| No awkward moments | No "please provide more context" for clear add-car |
| Broker summary useful | Broker can act without re-reading raw messages |

---

*See also: 07_FOUNDER_INSPECTION_NOTES.md*
