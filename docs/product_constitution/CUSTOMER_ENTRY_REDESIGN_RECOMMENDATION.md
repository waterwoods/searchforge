# P16-H Phase 4 — Customer Entry Redesign Recommendation

**Date:** 2026-05-31  
**Scope:** 客户报送 tab (`CustomerEntryTab.tsx`, `configs/clients/chen_kui/ui_copy.json`)  
**Evidence:** Code audit, empty-state DOM structure, constitution cancellation-first wedge, founder walkthrough  
**Constraint:** Recommendation only — no implementation

---

## Current Approach (As Built)

```
Show workflow first  →  IntakeFlowStepTrack (3 steps always visible)
Show categories first →  6 quick-start buttons + dropdown
Show forms first     →  Add-car structured collapse (5 fields)
Message input        →  Below categories, de-emphasized placeholder
```

**Empty-state hierarchy today:**

1. Hero: 「加车报价 · 客户统一报送」
2. Tagline: 3 sentences, Add-Car-first
3. Flow track: 开始报送 → 补齐关键信息 → 办公室接手
4. Headline: 「建议从加车报价开始」
5. Numbered instructions ①②③
6. Primary button: 办理加车报价 (with badge)
7. Secondary: 联系人工
8. Tertiary: 其他事项 dropdown (4 more categories)
9. Collapse: 加车报价 · 结构化报送 (5 inputs)
10. Textarea: de-emphasized for non-add-car

This is **workflow-first, category-first, form-first** — optimized for Add-Car portal GTM, not constitution cancellation wedge or professional SaaS entry.

---

## Professional SaaS Approach (Benchmark)

Products that convert cold users (Stripe Checkout, Linear issue create, Calendly booking, Superhuman compose):

```
Describe problem first  →  One line: what this is + who it's for
Collect message first   →  Single textarea above fold
Reveal form later       →  Categories/fields after first submit or intent detection
```

**Pattern:** Reduce decisions before first keystroke. Let NLP/triage infer intent from free text.

---

## Evaluation Matrix

| Criterion | A: Current | B: Message-first | C: Hybrid |
|-----------|------------|------------------|-----------|
| Cold user 10s comprehension | Fail | Pass | Partial |
| Add-Car multi-turn collection | Strong | Weaker initially | Strong after detect |
| Cancellation/missing-doc intake | Weak (buried in dropdown) | Strong | Strong |
| Chen Kui trial alignment | Fail | Pass | Pass |
| Engineering risk | None (status quo) | Medium — reorder components | Low — copy + hide |
| Matches broker paste path story | No | Yes | Yes |
| End-customer self-serve maturity | High for add-car | Low until turn 2 | Medium |

---

## Recommendation: **C — Hybrid (message-first shell, progressive reveal)**

**Not A (current).** Current structure fails 10-second test, contradicts cancellation-first constitution, and trains Chen Kui archetype to ignore broker workbench.

**Not pure B.** Add-Car structured collection is genuinely useful for end customers who want quote intake — but it must not dominate empty state for broker-led trial.

### Hybrid specification

**Empty state (first viewport):**

1. **Problem-first headline (Chinese):**  
   「把您的车险问题发给办公室 — 取消通知、缺材料、加车报价都可以」
2. **One trust line:** 「不自动发送；办公室确认后再回复您」
3. **Single textarea (hero size):** placeholder with 3 examples inline (取消通知 / 缺材料 / 加车)
4. **One primary button:** 「发送给办公室」
5. **Optional secondary link:** 「我想结构化填写加车信息」→ expands form collapse

**After first message submitted:**

- Triage detects intent → show relevant flow (add-car step track only if add-car)
- Category buttons hidden unless user clicks「这不是我要办的」

**For product_only trial (Chen Kui):**

- **Hide entire 客户报送 tab** — hybrid applies post-trial when customer portal is GTM
- OR show tab with banner: 「客户自助入口 — 经纪人请用办公室工作台」

---

## Reasoning

### Why not keep current (A)?

1. **Constitution conflict:** North Star V1 §7 — cancellation-first wedge; customer portal is secondary for Chen Kui
2. **Dual-product confusion:** Andy demos workbench; customer tab tells opposite story
3. **Professional SaaS bar:** No successful SaaS asks 6 category decisions before first input
4. **P11 evidence:** Wrong-tab / wrong-surface abandonment scored Day 1 at 28/100 unsupervised

### Why not pure message-first (B)?

1. Add-Car **structured fields** reduce back-and-forth for end customers — real value
2. Multi-turn add-car engine already built — don't discard, **defer visibility**
3. Hybrid preserves investment in `AddCarRecordSummaryRail`, flow tracks, handoff cards

### Why hybrid wins

- **10-second test:** one textarea, one button — passes
- **Cancellation/missing-doc:** no wrong category click required
- **Add-car:** detected from text OR optional structured path
- **Broker trial:** tab hideable without deleting portal code
- **Lowest risk:** mostly copy reorder + conditional render — no new capability

---

## Screenshot Evidence Notes

P16-C visual review (local product_only `:4173`) confirmed:

- Broker tab selected by default ✅
- Customer tab still present with Add-Car copy ⚠️
- Browser automation could not capture live screenshots from founder session (localhost isolation) — recommendation based on component tree + P16-C checklist

**If screenshot were taken of 客户报送 empty state:** expect full viewport filled with buttons and flow track, zero message input above fold.

---

## Implementation Scope (For Future Sprint — NOT P16-H)

| Change | Effort | Capability |
|--------|--------|------------|
| Reorder CustomerEntryTab empty state | 4h | Cap 4 |
| Update `ui_copy.json` headlines | 1h | Cap 4 |
| Hide 客户报送 tab in product_only | 1h | Cap 1 |
| Progressive reveal after triage | 8h | Cap 4 |
| **Total** | ~14h | No new capability |

---

## Verdict

**Choose C — Hybrid.**  
Keep structured add-car **after** first message or behind explicit link.  
For Chen Kui trial: **hide customer tab entirely** until post-trial customer portal GTM.

---

*End of P16-H Phase 4 — Customer Entry Redesign Recommendation*
