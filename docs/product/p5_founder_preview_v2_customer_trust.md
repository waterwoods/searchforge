# Founder Preview V2 — Customer Trust Reality Walk

**Date:** 2026-07-25  
**Mode:** Founder / customer feelings — not Engineering QA  
**Persona:** 58-year-old Chinese-speaking customer, minor accident, hands shaking, not technical  
**Scope:** Entire S1–S6 journey + Home → Start → Review → Receipt → Waiting  
**Verdict:** **CONDITIONAL GO** for Chen Preview / controlled pilot rehearsal  
**Overall Founder Score:** **6.8 / 10**

---

## 1. Overall Founder Score — 6.8 / 10

| Lens | Score | One line |
|------|------:|----------|
| Customer Trust (matched S3) | 7.5 | “They know me” is finally believable |
| Calmness under stress | 6.0 | Opening gate + “审核” + dense receipt still raise pulse |
| Continuity (am I done?) | 5.5 | Receipt / Waiting / safety copy compete for meaning |
| Human office feel | 6.5 | 陈总 helps; chip cards + double titles still feel like app |
| Demo readiness for Chen | 7.0 | Path exists; tiny human polish + flag discipline required |

**Not a 4.** The matched path no longer forces identity theater.  
**Not an 8.** Parents would still pause on waiting language, double headlines, and “这是不是正式报案”.

---

## 2. Top 10 remaining UX problems

| # | Problem | Where | Why it hurts | Sev |
|---|---------|-------|--------------|-----|
| 1 | **Double “今天发生了什么？”** | Smart panel + form card | Same question twice → feels like buggy software | **P0** |
| 2 | **“审核” as waiting state** | Receipt / Task Home / Case Status | Sounds like underwriting rejection risk, not “陈总在看” | **P0** |
| 3 | **Opening “正在确认…” gate** | Home + Start Claim | First emotion is delay/suspicion, not help | **P0** |
| 4 | **Receipt is a dashboard** | Receipt | 提交时间 / 下一步 / 会联系 / 可能还需 / disclaimer → “我做完了吗？” | **P0** |
| 5 | **Safety line creates doubt** | Start Claim footer + Receipt | Necessary legally; currently reads as “这次不算数” | **P1** |
| 6 | **Triple “办公室已了解您”** | Signal + chip label + subtitle | Trust becomes marketing spam | **P1** |
| 7 | **VIN in default subtitle** | Start Claim (legacy / flag-off) | Technical jargon for parents | **P1** |
| 8 | **Ambiguous “多位客户”** | Contact gate | CRM language; may scare (“搞错人了”) | **P1** |
| 9 | **Stale “知道了，继续报案” button** | Soft notice still looks clickable | Suggests a gate even when story already open | **P1** |
| 10 | **Review “请确认资料”** | Review | Returns to form-admin tone after emotional storytelling | **P1** |

---

## 3. Top 10 improvements (tiny, human — not architecture)

1. **One headline only** on matched path — panel owns story OR form owns story, never both.  
2. Say **“陈总正在看”** / **“陈总会尽快联系您”** — retire **“审核”** in customer UI.  
3. Replace “正在确认案件状态” with **“正在为您准备…”** or show Home shell with no anxious subtitle.  
4. Receipt becomes **three lines max:** 已收到 · 陈总会联系您 · 先不用操作.  
5. Move safety disclaimer to a quiet secondary line / “了解更多”, not peer of Next Step.  
6. Say “办公室已了解您” **once**.  
7. Delete **VIN** from customer-facing start copy forever.  
8. Ambiguous: “我们想先跟您确认一下是哪位客户” — not “多位客户”.  
9. Stale: banner text only — no fake button if story is already available.  
10. Review title → **“交给陈总前看一眼”** (or skip Review when only 4 fields + no photos).

---

## 4. Emotional Journey

Persona walks S3 (best path), then notes drops on other paths.

| Step | Trust | Stress | Confidence | Confusion | Momentum | Note |
|------|------:|-------:|-----------:|----------:|---------:|------|
| Open Mini Program | 6 | 7 | 5 | 4 | 5 | Hopeful but tense |
| Service Home “今天需要办理什么？” | 6 | 6 | 5 | 5 | 5 | Bank-app polite, not accident-warm |
| “正在确认…” | 5 | 7 | 4 | 6 | 3 | **Drop #1** — software delay |
| Chips “办公室已了解您” | 8 | 5 | 7 | 3 | 7 | Trust peak |
| Double headline + form fields | 7 | 5 | 6 | 5 | 6 | Soft drop — “为什么问两遍？” |
| Fill 4 facts | 7 | 5 | 7 | 3 | 7 | Good if voice works |
| Submit | 7 | 6 | 6 | 4 | 6 | Finger hesitation on CTA |
| Review “请确认资料” | 6 | 6 | 5 | 5 | 4 | Admin tone |
| Receipt dense + 正式报案 disclaimer | 5 | 7 | 4 | 7 | 3 | **Biggest drop** |
| “等待陈总审核” | 5 | 7 | 4 | 6 | 2 | Fear of rejection / did it fail? |
| Contact Chen option | 7 | 5 | 6 | 3 | 4 | Relief valve |

### Biggest emotional drop

**Submit → Receipt / Waiting.**

Why: The customer finished the hard part (telling the story). Instead of one calm human sentence, they get status pills, multiple next-step sections, “可能还需补充,” and “不代表正式报案.” Momentum dies. Stress returns. The question becomes: *Did this count? Should I call Chen anyway?*

---

## 5. Trust Journey

| Moment | Trust moves | Why |
|--------|-------------|-----|
| Home brand “陈总保险办公室” | ↑ | Named office |
| Context checking copy | ↓ | Feels like system deciding whether you’re allowed |
| Known chips (S3) | ↑↑ | “They already know me” |
| Repeated trust phrases | ↓ slight | Feels automated |
| Vehicle chooser (S2) | → / slight ↑ | One clear decision — Lemonade-like |
| Stale notice (S4) | → | OK if not a trap; button still looks like a gate |
| Blank (S5/S6) | → | Honest blank better than fake identity — but colder |
| Ambiguous Contact + blank | ↑ vs old trap | Escape exists; “多位客户” still scares |
| Safety disclaimer after submit | ↓↓ | Undermines “I already told the office” |
| “审核” | ↓↓ | Institutional, not familial |

---

## 6. Workflow Journey

```text
Home → (context check) → Start Claim
  → [S3 chips | S2 vehicle | S4 notice | S5 blank | Ambiguous gate]
  → Accident facts (4)
  → Submit
  → Review? (still present in product surface)
  → Receipt
  → Task Home / Waiting
```

| Challenge | Answer |
|-----------|--------|
| Can one step disappear? | **Yes — Review** when only Start Claim Must Haves and no photo work |
| Can one click disappear? | **Yes — stale “知道了”** if story already visible |
| Can one page disappear? | **Receipt should collapse toward Task Home** or become a 3-line toast-page |
| Can confirmation disappear? | **Yes — double story headline** |
| Can anything become automatic without hurting trust? | Preselect single vehicle (done). Auto-land cursor in story (not yet). Do **not** auto-create second claim. |

S1 Continue-only is correct. Do not soften One Active Case for “simplicity.”

---

## 7. Things Chen will probably notice

1. Flag OFF → whole “they know me” path invisible — demo looks like old form.  
2. Customer still asks him on WeChat: “提交了吗？算不算报案？”  
3. “审核” makes him sound like an insurer adjuster.  
4. Receipt / Task Home naming overlap (“我的报案” vs receipt vs case status).  
5. Ambiguous customers will call him anyway — blank escape helps only if they dare tap it.  
6. Voice-to-text quality will matter more than chips for 58-year-olds.  
7. English placeholder “Today 9 am” on datetime may look careless to him.

---

## 8. Things customers will probably notice

1. “为什么上面问一遍、下面又问一遍今天发生了什么？”  
2. “审核是不是没过？”  
3. “不代表正式报案 — 那我白填了？”  
4. Character count “xx 字” feels like homework.  
5. Chip cards feel like an app, not a person — but name/car still comforting.  
6. “正在确认您的案件状态” → “是不是出问题了？”  
7. Too many blue buttons after success → paralysis.

---

## 9. Things engineers are overthinking

- Capability package purity vs whether the second headline exists  
- Confirm-step schema elegance vs whether a stale banner needs a button  
- Mode enum completeness vs receipt emotional landing  
- “confidence_signal” as a field name (customers never see the name — but UI still renders three trust lines)  
- Perfect degrade taxonomy when blank path copy still mentions VIN in legacy mode

---

## 10. Things founders are underthinking

- **Post-submit calm is half the product.** Trust Start without Trust Landing is unfinished.  
- **“审核” is an emotional bug**, not a translation nit.  
- **Disclaimer placement** can undo the entire matched-path win.  
- **Demo flag discipline** — if Chen sees blank form once, he loses faith in the sprint.  
- **Parents do not want choices after success** — they want one sentence and permission to put the phone down.  
- Service Home question is still generic productivity software.

---

## 11. Unnecessary complexity

- Two cards stacking the same question (panel + form)  
- Receipt sections that restate each other (下一步 / 陈总会联系 / 可能还需)  
- Parallel surfaces: Receipt + Task Home + Case Status + start-claim-success  
- Soft-notice option button that doesn’t gate anything  
- “why ask time” helper under a field parents already understand  
- Visible character counter on a trauma story box

---

## 12. Hidden technical / cold language

| Phrase | Feel | Prefer |
|--------|------|--------|
| 正在确认您的案件状态 | System gate | 正在为您准备 |
| 案件 | Legal file | 报案 / 这次事故 |
| 审核 | Underwriting | 陈总正在看 / 陈总会联系您 |
| 多位客户 | CRM match | 我们想先跟您确认一下 |
| VIN | Tech/parts | delete |
| 资料概要 | Admin | 您刚才说的 |
| 请确认资料 | Form | 交给陈总前看一眼 |
| 不代表已向保险公司正式报案 | Fear (true but harsh) | Keep, but quieter and after reassurance |
| 加载失败 | App error | 一会儿再试，或联系陈总 |
| Today 9 am | Bilingual flex | 今天上午 9 点 only |

---

## 13. Remaining “software feeling”

1. Chip grid as product UI (acceptable if one trust line)  
2. Double titles / double cards  
3. Char count  
4. Status pills  
5. Disabled CTA with long `disabledReason` essays  
6. “正在加载提交前检查…”  
7. Multiple secondary buttons after success  
8. Home “今天需要办理什么？” (portal, not care)

---

## 14. Still doesn’t feel like talking to Chen’s office

Chen would roughly say:

> “我知道你是谁。今天怎么了？说完就行。我看了找你。先别慌。”

Current product still sometimes says:

> “正在确认案件状态 → 请确认资料 → 资料已提交等待审核 → 不代表正式报案 → 可能还需补充。”

Gap is not matching. Gap is **landing and waiting voice**.

---

## 15. GO / CONDITIONAL GO / NO GO

# **CONDITIONAL GO**

**Why not NO GO:**  
Matched S3 path finally earns “they know me.” Ambiguous is no longer a trap. Stale no longer blocks. Blank degrade is honest. Build Gate passes. Architecture is not the blocker.

**Why not full GO:**  
A stressed parent can still lose the plot **after** submit, and can still feel software **during** open/check and double headlines. Chen’s first real customer should not meet “审核” anxiety or a receipt dashboard.

**Conditions before first real Pilot customer:**

1. Kill double story headline (P0 copy/layout).  
2. Replace customer-facing **审核** with human waiting copy (P0).  
3. Collapse Receipt to calm 3-line landing (P0).  
4. Soften opening context copy (P0/P1).  
5. Founder physical Preview with flag ON for S2/S3/S5 + one submit→waiting walk.  
6. Keep pilot flag OFF until that Preview is signed.

---

## 16. If progressing — final tiny improvements before first real Pilot

**Must (same day polish):**

1. One “今天发生了什么？” only.  
2. “陈总正在看 / 会联系您” — no 审核.  
3. Receipt: 已收到 · 下一步由陈总联系您 · 先不用操作.  
4. Opening: remove anxious “确认后才能…”.  
5. Delete VIN from start subtitles.

**Should (before first live customer):**

6. Say 办公室已了解您 once.  
7. Stale = text banner only.  
8. Ambiguous copy without “多位客户”.  
9. Safety disclaimer demoted below reassurance.  
10. Hide or soften char count.

**Later (do not block pilot):**

- Auto-focus story field  
- Consider skipping Review on minimal Start Claim  
- Service Home question → more accident-warm  
- Merge redundant success surfaces over time  

---

## Challenge to history (Founder challenge)

| Old decision | Challenge | Recommendation |
|--------------|-----------|----------------|
| Keep Review as always-on confirm | For 4-field Start Claim it reintroduces form fear | Allow skip when nothing missing / no photos |
| “审核” as status vocabulary | Wrong emotion for broker office | Constitution/customer copy: prefer 陈总在看 |
| Loud safety disclaimer everywhere | Truth without reassurance destroys trust | Truth stays; order becomes: reassure → then quiet legal |
| Receipt as information-rich page | Engineers love completeness; parents need calm | Completeness belongs in “查看已提交”, not first screen |
| Service Home generic question | Portal thinking | Accident-first greeting when no active case |

**Capability boundaries:** Do **not** change C01/C02 for these. All remaining pain is presentation / waiting voice / post-submit calm — still C03 + existing customer surfaces, not AMS.

---

## Benchmark (experience, not UI copy)

| Product | Lesson we still miss |
|---------|----------------------|
| **Lemonade** | Story is the product; after submit, one calm beat |
| **GEICO** | Logged-in path feels faster than guest — we only win if flag ON |
| **Progressive** | Guest path must not feel punished — our blank is OK, waiting copy is not |
| **Apple** | After action, permission to stop; we still offer three next buttons |
| **WeChat life services** | Named human + short status; we over-section |

---

## Bottom line for the Founder

You should feel:

> I know exactly what still feels wrong.  
> None of it is architecture.  
> Tiny human improvements remain — mostly **one headline**, **waiting voice**, and **post-submit calm**.

**Good enough for Chen’s first Pilot tomorrow morning with a real stranger?**  
**Not yet — CONDITIONAL.**  
**Good enough for Chen Preview / office rehearsal this week after the P0 copy fixes?**  
**Yes.**
