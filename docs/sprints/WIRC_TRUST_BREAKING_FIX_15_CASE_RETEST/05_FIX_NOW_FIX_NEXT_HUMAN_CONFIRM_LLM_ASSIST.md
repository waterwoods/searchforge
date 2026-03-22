# Fix-Now / Fix-Next / Human-Confirm / LLM-Assist Spec

## Fix now (done this sprint)

| Item | Class | Notes |
|------|-------|--------|
| Prospective vs completed send | **A. Rule coverage** | New completion helper + expanded intent guard |
| Short unclear “发你” false positive | **A. Rule coverage** | Gate on `_message_claims_completed_material_send` |
| Broker summary “already sent” noise | **A. Rule coverage** | Segment-level completion only |
| Cancellation `screenshot_sent` over-trigger | **A. Rule coverage** | Completion-based |
| VIN + permission screenshot without 加车 | **C. First-turn tolerance** | Narrow `_is_add_vehicle_request` bridge |
| 行驶证/registration + permission without 加车 | **C. First-turn tolerance** | Same |
| Nissan Altima extraction / vehicle_context | **B. Lexicon** | markers + extraction lists |
| Add-car draft when zip+delivery present, driver missing | **A. Rule coverage** | Driver-only ask (zh/en) |

## Fix next (rule / lexicon, still deterministic)

| Item | Class |
|------|--------|
| Standalone 截图要不要先发你 — still often `unclear` | **C** — add minimal “screenshot permission” template under `unclear` or very light marker for 加车-adjacent doc offers |
| ZIP-only premium worry (WTR-F01) | **C / D** — optional premium_review bleed or explicit “garaging/ZIP affects rate” one-liner |
| More makes (Hyundai trims, Subaru, etc.) | **B** |
| English “screenshot OK?” without add-car markers | **A / C** |

## Human confirmation appropriate (D)

| Situation | Why |
|-----------|-----|
| Customer claims paid + sent + dispute deadline in same thread | High financial + reputational risk |
| Repeated “我发过了” vs carrier still chasing | Broker must verify channel + timestamp |
| Mixed claim + add-car in one short bubble | Already often LLM or handoff — broker triage |

## Candidate for future LLM assist (E) — precise

| Situation | Why not rules-only |
|-----------|---------------------|
| Long mixed-intent paragraphs (2+ flows, no clear last intent) | Needs discourse segmentation |
| Sarcasm / negation (“我当然没发啊”) | Fragile without a model |
| Novel doc types (“门店合同照片”) | Lexicon drift |
| Free-form “这样行不行” without 发/截图 cue | Ambiguous speech act |

**Do not** default to “needs AI” for VIN/screenshot permission — this sprint shows it is **rule-fixable** with the right guard ordering.
