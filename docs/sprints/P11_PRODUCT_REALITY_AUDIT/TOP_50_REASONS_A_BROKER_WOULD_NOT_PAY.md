# TOP 50 Reasons a Broker Would NOT Pay

**Persona:** Chen Kui or similar California auto insurance broker evaluating Unified Intake after 7-day trial.  
**Scale:** Severity (Critical / High / Medium / Low) · Probability (Likely / Possible / Unlikely)

---

| # | Reason | Severity | Probability | Mitigation |
|---|--------|----------|-------------|------------|
| 1 | Opens wrong tab (客户报送) — never sees cancellation value | Critical | Likely | Default broker tab; kickoff shows 办公室工作台 only |
| 2 | Expected WeChat sync — paste feels like extra work | Critical | Likely | First-screen: "复制粘贴，不连微信"; win on triage speed |
| 3 | Draft wrong on real messages often enough to ignore | Critical | Likely | Fix-now queue; tune chen_kui client pack; human confirmation |
| 4 | No proven time savings on real cases after 7 days | Critical | Likely | Observation log; require 3+ real cases; measure one workflow |
| 5 | Cases lost on refresh / different device | Critical | Possible | Postgres-primary prod; honest local vs prod messaging |
| 6 | System down during business hours — handled manually anyway | Critical | Possible | deploy_paid_pilot + `/readyz`; founder SLA; status message |
| 7 | Thinks product auto-sends to customers | Critical | Likely | "不自动发送" on every screen; repeat in kickoff |
| 8 | Production URL unstable or localhost-only trial | High | Likely | Validate + deploy prod before trial; weekly probe |
| 9 | Engineer UI (PG 镜像, API URL, 路由/指标) — "not finished" | High | Likely | Hide all in product-only UI |
| 10 | Playbook requires Simulation Assistant — tab missing | High | Likely | Inline 练习场景 or update playbook |
| 11 | Add-Car-first UI vs cancellation-first pain | High | Likely | Lead story with cancellation; reconcile banners |
| 12 | First paste slow (30s+) with no explanation | High | Likely | Loading copy: "首次分析约30秒" |
| 13 | Demo queue load 15–30s — thinks broken | High | Likely | Progress bar + "正在加载13条示例" |
| 14 | Pricing unclear after free trial | High | Likely | $99/mo on one-pager; one sentence terms |
| 15 | No invoice / receipt for business records | High | Likely | PDF or WeChat invoice template |
| 16 | No written pilot terms (data, cancel, support) | High | Likely | 1-page Chinese pilot agreement |
| 17 | Assistant can't use without broker training each time | High | Possible | 15-min assistant script; demo queue for training |
| 18 | Mobile UX poor — brokers live on phone | High | Likely | Flag desktop-first in terms OR improve paste on mobile |
| 19 | Too many tabs (客户报送, 办公室工作台, 我的办理, 场景仿真) | High | Likely | Trial mode: one tab visible; wayfinding banner |
| 20 | "Case" / English mixed with Chinese — feels foreign | High | Likely | Replace with 服务记录; Chinese-first copy |
| 21 | Doesn't trust AI with client data | High | Possible | Explain secure database; founder-managed keys; no sharing |
| 22 | Data retention unclear after trial ends | High | Possible | State in pilot terms: keep or export cases |
| 23 | Single founder support — "what if he's unavailable?" | High | Likely | Document L1 responses; 24h response commitment |
| 24 | No reference broker / testimonial | High | Likely | Capture Day 7 quote if positive |
| 25 | Thinks it's a CRM replacement — disappointed | Medium | Likely | "不是CRM — 只做消息整理和草稿" |
| 26 | Thinks it reads screenshots — disappointed | Medium | Likely | Repeat in paste area: text only |
| 27 | Wrong vehicle/name in draft — trust broken once | Critical | Possible | Human confirmation + edit workflow; fix top errors |
| 28 | 7-day trial too short to hit real cancellation case | Medium | Likely | Demo queue + paste one real message Day 1 |
| 29 | 7 days vs 1 month — conflicting playbook language | Medium | Possible | "7天试用，满意再付月费" |
| 30 | Queue card tag overload — can't scan | Medium | Likely | Max 3 tags + expand |
| 31 | Filter labels (镜像异常, 旧识别, 测试) meaningless | Medium | Likely | Hide engineer filters; 全部 / 需今天处理 |
| 32 | Long monospace service record ID confusing | Medium | Likely | Short ID in list; full on detail |
| 33 | Pilot intro alert wall of text on first open | Medium | Likely | Collapse by default; 3-bullet version |
| 34 | Doesn't know how to paste follow-up | Medium | Likely | Highlight 更新客户新消息 |
| 35 | Copy case snapshot hard to find when stuck | Medium | Likely | Promote in support section |
| 36 | Draft in wrong language mix | Medium | Likely | Edit before copy; improve client pack |
| 37 | Two workflows (paste vs Add-Car form) — which to use? | Medium | Likely | Trial script: paste path for cancellation/missing doc |
| 38 | `/demo` RAG page confused with main product | Medium | Unlikely | Hidden in product-only sidebar |
| 39 | No multi-user login — assistant shares URL awkwardly | Medium | Possible | Accept for v1; document same-URL use |
| 40 | Can't integrate with existing AMS/CRM | Medium | Likely | Set expectation: side tool, not replacement |
| 41 | Carrier portal still required — duplicate effort | Medium | Likely | Position as WeChat-side triage only |
| 42 | $99 feels high for "copy-paste helper" | Medium | Likely | Prove minutes saved; compare to assistant hourly cost |
| 43 | $99 feels low — "must not be serious" | Low | Unlikely | Professional UI + invoice + terms |
| 44 | Worried about compliance / E&O if AI wrong | High | Possible | Human confirms all sends; not legal advice disclaimer |
| 45 | Competitor offers WeChat bot for free | Medium | Possible | Differentiate: structured case + draft + urgency |
| 46 | Already has assistant workflow that works | Medium | Likely | Target assistant time savings; broker bottleneck reduction |
| 47 | Seasonal business — not enough messages in trial week | Medium | Possible | Extend trial or use demo + 2 real cases minimum |
| 48 | Founder relationship — pays as favor, not value | Low | Possible | Separate value validation from relationship |
| 49 | Expects multi-office rollout before paying | Medium | Unlikely | Single-office pilot explicit in terms |
| 50 | Heard "AI" and assumes ChatGPT is enough | Medium | Possible | Show insurance-specific case structure + queue |

---

## Top 5 objection clusters

1. **Wrong front door** — lands on wrong tab; never reaches value (#1, #19)  
2. **Extra steps without savings** — no WeChat sync; must prove triage faster (#2, #4)  
3. **Trust gaps** — draft quality, engineer UI, downtime (#3, #6, #9)  
4. **Commercial ambiguity** — price, terms, invoice, data (#14–16, #22)  
5. **Story mismatch** — Add-Car UI vs cancellation pain (#11, #37)

---

*End of top 50 reasons a broker would not pay*
