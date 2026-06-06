# P16-Z4 Phase 7 — ROI Ranking

**Date:** 2026-06-02  
**Sprint:** P16-Z4 Case Continuity Sprint  
**Dimensions:** Value (1–5) · Difficulty (S/M/L) · Time (hours/days)  
**Scope:** Continuity only — no P17, no CRM, no platform

---

## Full ranking table (continuity improvements)

| Rank | Improvement | Value | Difficulty | Time | Type |
|------|-------------|-------|------------|------|------|
| 1 | FP-004 SSO off (trial access) | 5 | S | 5 min + redeploy | Access |
| 2 | Post-copy continuation one-liner | 5 | S | 15 min | Copy |
| 3 | Append card when `case_id` exists | 5 | S | 2 hr | UI |
| 4 | Auto-scroll to case after triage | 4 | S | 1 hr | UI |
| 5 | Copy toast + continuation hint | 4 | S | 1 hr | UI |
| 6 | Chinese broker_next_step product_only | 5 | M | 0.5 day | Config |
| 7 | Collapse paste when case open | 5 | M | 0.5 day | UI |
| 8 | conversation_summary merge (Y44) | 5 | M | 1–2 days | Engine |
| 9 | Render case_messages thread (5 lines) | 4 | M | 0.5 day | UI |
| 10 | Default-open activity after append | 4 | S | 2 hr | UI |
| 11 | waiting_on prompt after copy | 4 | M | 0.5 day | UI |
| 12 | Queue Chinese 下一步 snippet | 4 | M | 0.5 day | UI |
| 13 | P16-Y battery CI gate pre-trial | 4 | S | 2 hr | Process |
| 14 | claim_intake template tune | 3 | S | 0.5 day | Config |
| 15 | bill_sent_claimed rule (Y45) | 3 | M | 0.5 day | Engine |
| 16 | requires_new_case UX copy | 3 | S | 2 hr | Copy |
| 17 | Sticky 复制客户草稿 | 3 | M | 0.5 day | UI |
| 18 | Founder two-turn observation log | 5 | S | 1 hr | Process |
| 19 | Guardrail append sim in launch check | 4 | S | 1 hr | Process |
| 20 | Demote 快速体验 (P16-M #2) | 4 | S | 1 hr | UI |

---

## TOP 10 improvements under 1 day

| # | Item | Time | Impact |
|---|------|------|--------|
| 1 | FP-004 off | 5 min | Unblocks all continuity |
| 2 | Post-copy continuation line | 15 min | Turn-2 discoverability |
| 3 | Append on first persist | 2 hr | Core loop |
| 4 | Auto-scroll to case | 1 hr | Reduces hunt |
| 5 | Copy toast hint | 1 hr | Habit at exit |
| 6 | Default-open activity after append | 2 hr | Timeline feel |
| 7 | Collapse 快速体验 when case open | 1 hr | Noise reduction |
| 8 | requires_new_case friendly copy | 2 hr | Append trust |
| 9 | Founder two-turn log ritual | 1 hr | Evidence |
| 10 | Append sim in trial_launch_check | 1 hr | Regression |

**Batch total:** < 1 engineer-day

---

## TOP 10 improvements under 1 week

| # | Item | Time | Impact |
|---|------|------|--------|
| 1 | conversation_summary merge (Y44) | 1–2 days | Multi-turn case truth |
| 2 | Chinese broker_next_step templates | 0.5 day | L4 next action |
| 3 | Collapse top paste when case open | 0.5 day | Anti duplicate-case |
| 4 | case_messages thread in glance | 0.5 day | Timeline UX |
| 5 | waiting_on one-click after copy | 0.5 day | Office waiting state |
| 6 | Queue row Chinese 下一步 | 0.5 day | Monday workflow |
| 7 | claim_intake + hit_and_run config | 0.5 day | Claims wedge |
| 8 | bill_sent_claimed (Y45) | 0.5 day | Premium thread |
| 9 | Sticky copy + P16-M glance flatten | 1 day | Polish |
| 10 | Supervised Day 0 + 3 real two-turn cases | 2 days | Commercial proof |

**Week total:** ~5–6 engineer-days (fits 7-day sprint with buffer)

---

## ROI formula used

`score = (value × impact_on_continuity) / (days × risk)`

Highest scores cluster on **wire existing append + copy bridge** — zero new services.

---

*End of P16-Z4 Phase 7*
