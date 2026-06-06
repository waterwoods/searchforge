# P16-X Phase 6 — Top 50 Friction Points

**Date:** 2026-06-01  
**Ranked by:** Probability × Impact (P×I, max 25)  
**Source:** P16-X Phases 1–5 live Preview simulation  
**Rule:** Friction only — no feature proposals

---

## Scoring key

| P (Probability) | Meaning |
|-----------------|---------|
| 5 | >80% of trial users hit this |
| 4 | 50–80% |
| 3 | 30–50% |
| 2 | 10–30% |
| 1 | &lt;10% |

| I (Impact) | Meaning |
|------------|---------|
| 5 | Abandon product or trial |
| 4 | Skip lifecycle step (no follow-up / no close) |
| 3 | Slowdown or trust loss |
| 2 | Annoyance |
| 1 | Cosmetic |

---

## Top 50 (ranked)

| Rank | ID | Friction | P | I | P×I | Phase |
|------|-----|----------|---|---|-----|-------|
| 1 | F-001 | **No continuation cue after copy draft** — user exits to WeChat permanently | 5 | 5 | **25** | Chen Kui |
| 2 | F-002 | **Append follow-up hidden until queue reopen** | 4 | 5 | **20** | Lifecycle |
| 3 | F-003 | **30s first triage wait** with no in-view progress on mobile/small viewport | 4 | 4 | **16** | Role C |
| 4 | F-004 | **Top paste box ambiguous** after first case (new vs same thread) | 4 | 4 | **16** | Assistant |
| 5 | F-005 | **English broker_next_step / queue preview** on Chinese UI | 4 | 4 | **16** | Role C |
| 6 | F-006 | **Result card below fold** — user never scrolls to draft | 4 | 4 | **16** | Role C |
| 7 | F-007 | **Broker vs customer identity** unclear from title alone | 3 | 5 | **15** | Role C |
| 8 | F-008 | **No sent / waiting-on-client state** after copy | 5 | 3 | **15** | Lifecycle |
| 9 | F-009 | **Status change buried** in kebab menu | 4 | 3 | **12** | Close |
| 10 | F-010 | **Demo queue 15–30s load** competes with real work | 3 | 4 | **12** | Chen Kui |
| 11 | F-011 | Duplicate-looking queue rows after demo load | 3 | 4 | **12** | Trust |
| 12 | F-012 | **快速体验（可选）** above queue — wrong priority on Day 2+ | 4 | 3 | **12** | Trial |
| 13 | F-013 | Multiple collapses (整理明细 / 标签 / 字段) — scan paralysis | 4 | 3 | **12** | Role C |
| 14 | F-014 | **开始整理 disabled as「已打开」** without explaining append path | 3 | 4 | **12** | Reopen |
| 15 | F-015 | No empty-queue CTA「粘贴第一条紧急消息」| 3 | 4 | **12** | Day 1 |
| 16 | F-016 | Trust line「不自动发送」below brand — missed if no scroll | 3 | 4 | **12** | Role C |
| 17 | F-017 | **No Work now / Waiting split** in product_only | 3 | 4 | **12** | Cap 5 |
| 18 | F-018 | Case ID monospace — looks like engineer tool | 3 | 3 | **9** | Trust |
| 19 | F-019 | **Two copy buttons** (header + collapse) — which is canonical? | 3 | 3 | **9** | Draft |
| 20 | F-020 | Alert banner redundant with subtitle (paste instructions ×3) | 4 | 2 | **8** | Density |
| 21 | F-021 |「清空」required before next case — extra step | 3 | 3 | **9** | Throughput |
| 22 | F-022 | No copy-success feedback | 4 | 2 | **8** | Draft |
| 23 | F-023 | Loading spinner not sticky — user clicks twice | 2 | 4 | **8** | Triage |
| 24 | F-024 | Practice scenario buttons look like production queue | 3 | 3 | **9** | Confusion |
| 25 | F-025 | **Customer tab absent** — wrong link to Production customer UX | 2 | 5 | **10** | Distribution |
| 26 | F-026 | Production URL still pre-P16-I customer chrome | 2 | 5 | **10** | FP-001 |
| 27 | F-027 | No in-app Day 7 value / minutes-saved | 4 | 2 | **8** | Cap 6 |
| 28 | F-028 | Dark header + brand card duplicate title | 3 | 2 | **6** | Polish |
| 29 | F-029 |「需您修改后再发」without edit affordance in-app | 3 | 3 | **9** | Draft |
| 30 | F-030 | Boundary / 案件边界 collapsed — append mistakes | 2 | 4 | **8** | Follow-up |
| 31 | F-031 | No mobile validation | 3 | 3 | **9** | Assistant |
| 32 | F-032 | Queue refresh timestamp — no「new since last visit」| 3 | 3 | **9** | Reopen |
| 33 | F-033 | Formal vs informal submit concepts leak in dev strings | 2 | 3 | **6** | Engineer |
| 34 | F-034 | Add-car structured fields in collapse on non-add-car case | 2 | 3 | **6** | Noise |
| 35 | F-035 | No pricing / trial terms in UI | 3 | 2 | **6** | Cap 6 |
| 36 | F-036 | Founder must explain 30s wait | 4 | 2 | **8** | Trial |
| 37 | F-037 |「整理结果」step numbers ①②③ — broker impatience | 3 | 2 | **6** | Scan |
| 38 | F-038 | UTC / timing footnotes in customer bundle (Production) | 2 | 3 | **6** | Customer |
| 39 | F-039 | Session lost on clear browser data | 2 | 4 | **8** | Continuity |
| 40 | F-040 | No keyboard shortcut to focus paste | 2 | 2 | **4** | Power user |
| 41 | F-041 | Demo queue English case summaries | 3 | 2 | **6** | Demo |
| 42 | F-042 | Floating widget (browser extension) overlaps content | 2 | 2 | **4** | Env |
| 43 | F-043 | `undefined` prefix bug on programmatic fill (edge) | 1 | 3 | **3** | QA |
| 44 | F-044 | 刷新列表 without pull-to-refresh on mobile | 2 | 2 | **4** | Mobile |
| 45 | F-045 | No print-friendly case glance | 1 | 2 | **2** | Assistant |
| 46 | F-046 | Chen Kui branding on URL shared to staff — privacy feel | 2 | 2 | **4** | Trust |
| 47 | F-047 | Observation log not linked from UI | 3 | 1 | **3** | Cap 6 |
| 48 | F-048 | CORS on non-alias deploy URLs | 2 | 3 | **6** | Ops |
| 49 | F-049 | Second paste without 清空 may overwrite in-progress UI state | 2 | 3 | **6** | Edge |
| 50 | F-050 | No haptic/audio ack on copy (mobile) | 1 | 1 | **1** | Polish |

---

## P×I tier summary

| Tier | Count | Theme |
|------|-------|-------|
| **20–25** | 2 | Post-submit abandonment |
| **15–19** | 4 | Continuation + language + layout |
| **12–14** | 12 | Lifecycle discoverability |
| **8–11** | 18 | Trust, density, trial ops |
| **≤7** | 14 | Polish, edge, deferred |

---

## Top 5 abandonment vectors

1. **Copy → leave → never return** (F-001)
2. **Cannot find follow-up without training** (F-002, F-004)
3. **First wait + below-fold result** (F-003, F-006)
4. **Wrong URL / wrong persona** (F-007, F-025, F-026)
5. **Trust erosion EN/ZH mix** (F-005, F-011)

---

*End of P16-X Phase 6 — Top 50 Friction Points*
