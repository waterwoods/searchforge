# P16-I Founder Review Package

**Date:** 2026-05-31  
**Sprint:** P16-I — UI Simplicity Implementation  
**Branch:** `sprint-a/broker-front-door`

---

## 1. What changed

- product_only trial is **broker workbench only** — no tab bar when single surface
- **Paste column renders first** (above queue) on all viewports
- **Cancellation-first copy** in header, subtitles, document title
- Case detail: **one primary copy button**, draft expanded, detail collapsed
- Queue: **single sorted list**, minimal row chrome

---

## 2. What was hidden (product_only)

| Element | Location |
|---------|----------|
| 客户报送 tab | UnifiedIntakePage |
| 我的办理 tab | Already hidden; unchanged |
| Simulation tab | Already hidden; unchanged |
| Tab suffix subtitles | UnifiedIntakePage |
| 显示产品说明 link | UnifiedIntakePage |
| Pilot intro tag wall | UnifiedIntakePage |
| 返回工作台 | AppLayout header |
| 复制摘要 | BrokerWorkbenchTab case detail |
| Status radio (inline) | Moved to overflow「状态」 |
| Queue filter Segmented | BrokerWorkbenchTab |
| 立即处理 / 等待或暂存 sections | Single list |
| Per-card tag explosion | Urgency + preview only |
| 与客户报送同源 | Queue card extra |
| Current-open anchor box | Queue sidebar |
| Pagination | Hidden in trial list |
| Follow-up CRM block | Case detail bottom |
| 客户可准备 card | Case detail |
| Add-car submission snapshot | product_only case detail |
| Duplicate append block (lab path) | Promoted block near glance |

---

## 3. What was collapsed

- **整理明细** (formerly Case 整理明细) — default closed in product_only
- Draft — default **open** in product_only
- Full conversation thread — unchanged (default closed)
- Structured fields / tags — inside collapsed detail

---

## 4. What was renamed

| Before | After (product_only) |
|--------|----------------------|
| Case 整理明细 | 整理明细 |
| portal_brand_tagline Add-Car | 粘贴客户消息 · 整理草稿 · 您确认后发送 |
| office_workbench_document_title | 办公室工作台 · 客户消息整理 |
| 粘贴客户新消息 (promoted) | 追加客户补充 |
| 服务记录队列 | 待处理 |
| 从客户消息整理服务记录 | 粘贴客户消息 |

---

## 5. What stayed

- Triage engine, API, schema — **unchanged**
- 加载演示队列 + inline practice seeds (merged into one card)
- Wayfinding alert on paste surface
- OfficeWorkbenchOneGlanceSummary (broker moat)
- 复制客户草稿 primary action
- Demo queue auto-open cancellation case
- Lab/full UI when product_only flag off

---

## 6. Before / after first screen

| Before (P16-H) | After (P16-I) |
|----------------|---------------|
| Two tabs + suffix noise | Single workbench surface |
| Add-Car tagline in header | Cancellation-first one-liner |
| Paste below demo + practice cards | Paste **first** full-width |
| 7 focal points above fold | **~3** (header, paste, primary CTA) |
| Tag wall intro | One trust line |

---

## 7. What Andy should inspect

1. Open `/workbench/unified-intake` with product_only build — paste visible without scroll?
2. Load demo queue — cancellation case opens; copy draft works?
3. Reopen case — **追加客户补充** visible near glance summary?
4. Header copy — no Add-Car flagship wording?
5. Authenticated preview URL (P16-G gate) — same experience as local

---

## 8. What Chen Kui would likely notice

**Positive:** Less confusion about which tab; paste is obvious; fewer buttons on case detail.  
**Neutral:** Demo card still present below paste (optional).  
**Risk:** If he bookmarks old customer tab URL — redirects to workbench (OK).

---

## 9. Remaining clutter

- Dark KPI app header wrapping white product (medium)
- Avatar + team block in product header (low)
- Demo card below paste on Day 0 (low — training value)
- Wayfinding Alert + trust line slight duplication (low)
- Customer portal code still in bundle (hidden, not deleted)

---

*End of P16-I Founder Review*
