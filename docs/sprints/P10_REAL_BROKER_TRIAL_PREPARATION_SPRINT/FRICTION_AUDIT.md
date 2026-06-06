# Friction Audit — TOP 50 Broker Confusions

**Method:** Act as Chen Kui's assistant who knows insurance and WeChat, not AI/RAG/vectors/PostgreSQL. Attempt to start a 7-day trial from BROKER_ONE_PAGER + URL only.

**Severity:** Critical / High / Medium / Low  
**Probability:** Likely / Possible / Unlikely

---

| # | Confusion | Severity | Probability | Fix |
|---|-----------|----------|-------------|-----|
| 1 | "Which tab do I use?" — lands on 客户报送, playbook says workbench | Critical | Likely | Default broker trial to 办公室工作台 tab; one-line banner: "经纪人请点这里" |
| 2 | "Load founder demo queue" vs 加载演示队列 — English in docs, Chinese in UI | High | Likely | Align one-pager to UI label; or rename button to match docs |
| 3 | Is this connected to WeChat? | Critical | Likely | First screen + one-pager: "复制粘贴，不连微信" |
| 4 | Does it auto-send to my customer? | Critical | Likely | Green tag on every tab: "不自动发送" |
| 5 | What is a "case"? | High | Likely | Replace with 服务记录 in broker-facing copy |
| 6 | What is Unified Intake? | Medium | Likely | Use 客户消息整理 or product Chinese name consistently |
| 7 | Customer Entry vs 办公室工作台 — why two doors? | High | Likely | Trial one-pager: "您只用办公室工作台；客户报送是给客户用的" |
| 8 | Add-Car-first banner vs cancellation demo story | High | Likely | Reconcile: either lead demo with cancellation or rewrite all trial docs for Add-Car-first |
| 9 | Where is Simulation Assistant? — playbook Day 1 step 3 | Critical | Likely | Product-only UI hides tab; add in-workbench "练习场景" or update playbook |
| 10 | What is SIM1/SIM2/SIM3? — trial_launch_check mentions them | High | Possible | Remove SIM IDs from broker path; use scenario names only |
| 11 | What is 场景仿真? | Medium | Possible | Rename to 练习模式 or hide entirely in product-only |
| 12 | What is 我的办理? | Medium | Likely | Explain: customer-facing request tracker — brokers can ignore |
| 13 | Pilot intro alert wall of text on first open | High | Likely | Collapse by default for returning users; 3-bullet version for trial |
| 14 | 加载演示队列 takes 15–30 seconds — is it broken? | High | Likely | Progress bar + "正在加载13条示例，请稍候" |
| 15 | 13 cases / cancellation opens first — how do I know? | Medium | Likely | Auto-open cancellation case after queue load |
| 16 | What is Case focus? | Medium | Likely | Already 案件类型 in some places — unify to 这件什么事 |
| 17 | What is Your next move? | Low | Possible | UI already uses 下一步 — docs should match |
| 18 | What are Collected / Still needed chips? | Medium | Likely | Onboarding tooltip: 已收集 / 还缺什么 |
| 19 | Human confirmation recommended — 请核实此信息 | Medium | Possible | Keep; add one-line explainer on first sight |
| 20 | Does it read screenshots? | High | Likely | One-pager says no — repeat in UI paste area |
| 21 | Can I upload PDF/photo? | High | Possible | If attachment exists, say what works; if not, hide upload |
| 22 | What languages work? | Low | Possible | "中文英文都可以粘贴" on paste card |
| 23 | Why is first paste slow? | High | Likely | "第一次可能慢30秒" + retry button |
| 24 | 503 / embedding_warming — what do I do? | Critical | Possible | Broker message: "系统启动中，请1分钟后再试或微信创始人" |
| 25 | What happens to my cases after I close browser? | High | Likely | "已保存到安全数据库" (prod) vs "演示模式仅本机" (local) — must be honest |
| 26 | Is `/demo` the product? | Medium | Unlikely | Remove from broker materials; sidebar hidden in product-only |
| 27 | Is this a CRM? | Medium | Likely | "不是CRM — 只做消息整理和草稿" |
| 28 | Can my assistant use it? | Low | Likely | Yes — same URL; no separate login (no auth yet) |
| 29 | 服务记录编号 — long monospace ID | Medium | Likely | Show short ID + copy full; explain "对单用" |
| 30 | PG 已镜像 / PG 缺失 tags | Critical | Likely | Hide all pg_mirror tags from product-only UI |
| 31 | 路由/指标 debug tag | High | Possible | Hide in product-only |
| 32 | 数据接口 localhost:8001 | Critical | Likely | Hide API endpoint label from broker UI |
| 33 | Filter: 镜像异常 / 旧识别 / 测试 | High | Likely | Hide engineer filters; keep 全部 + 24h |
| 34 | 管理 → 标为测试 / 归档隐藏 | Medium | Possible | Rename or tuck under advanced |
| 35 | Queue filters 正式 vs 测试 — what's 正式? | Medium | Possible | Broker label: 真实客户 vs 练习 |
| 36 | 持久化服务记录总数 — what is 持久化? | Medium | Likely | Say 已保存的记录 |
| 37 | 高风险（本页） — high risk of what? | Medium | Likely | 需当天处理 |
| 38 | 与客户报送同源 — what does that mean? | Medium | Likely | "客户在微信入口提交的也会出现在这里" |
| 39 | Copy case snapshot — where is it? | Medium | Likely | Prominent button when asking for support |
| 40 | How do I paste a follow-up? | Medium | Likely | Highlight 更新客户新消息 on case detail |
| 41 | Waiting on client vs done — what's the difference? | Medium | Possible | Status picker with Chinese examples |
| 42 | Draft is in wrong language | High | Likely | Edit before copy — note in playbook; improve client pack |
| 43 | Draft mentions wrong vehicle/name | Critical | Possible | Human confirmation badge + edit workflow |
| 44 | Add-car structured form vs paste triage — two workflows? | High | Likely | Trial script: pick ONE entry (paste OR 办理加车报价) |
| 45 | 加车旗舰路径 maturity vs cancellation | High | Likely | Set expectation: cancellation/missing doc = paste path |
| 46 | Do I need to clean the message first? | Low | Likely | "原样粘贴" on paste box |
| 47 | Who do I call for help? | Medium | Likely | WeChat/email in header footer — not buried in PDF |
| 48 | Is my data shared with other brokers? | Medium | Possible | "您的数据仅您的办公室" |
| 49 | Trial free but then what price? | Medium | Likely | State $99/month pilot on one-pager if that's the offer |
| 50 | 7 days vs 1 month — playbook mentions both | Medium | Possible | One sentence: 7天试用，满意再付月费 |

---

## Top 5 friction clusters (fix first)

1. **Wrong front door** — Customer Entry default vs workbench-first trial docs  
2. **Hidden training** — Simulation tab off in product-only; playbook requires it  
3. **Engineer chrome** — PG tags, API endpoint, mirror filters  
4. **Story split** — Add-Car-first UI vs cancellation-first demo/trial narrative  
5. **Expectation gap** — no WeChat sync, manual paste is the workflow

---

*End of friction audit*
