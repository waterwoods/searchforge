# Insurance Paid-Pilot Readiness Report

**Generated**: 2026-03-05  
**Scope**: California Auto Insurance Broker Assistant — commercialization gap check and implementation plan  
**Primary Goal**: First paid pilot with 陈奎 in 2–3 weeks

---

## 1. Executive Verdict

### Are we close enough to sell?

**Yes.** The demo is 85% ready. It passes `demo_quick_validate.sh`, has offline fallback, gov+insurer diversity, and a broker-focused UI. You can demo it today and charge manually within 1–2 weeks.

### What is the fastest monetization path?

1. **This week**: Run `demo_quick_validate.sh` → PASS. Customize UI for 陈奎 (rename, 5 questions). Schedule 15-min live demo.
2. **Next week**: Deploy backend to Cloud Run (`deploy_rag_demo.sh`). Deploy frontend (Vercel/Netlify) or share local URL for pilot.
3. **Week 3**: Manual payment (Zelle/Venmo/WeChat). Send invoice. Get first testimonial.

### What should be ignored right now?

- Multi-tenant auth
- Stripe / full billing integration
- LLM answer generation (retrieval + snippets suffice for MVP)
- JobHunter, Mortgage, Vitals, Code Lookup
- Repo cleanup, deprecated code removal
- China / Europe expansion (defer until after first customer)

---

## 2. Current Readiness Score

| Dimension | Score (0–10) | Notes |
|-----------|--------------|-------|
| **Demo reliability** | 8 | `run_demo_local.sh` works; offline fallback; quick_validate PASS (2026-02-21). Risk: Qdrant cold start, env vars. |
| **Answer quality** | 7 | 3 questions validated; gov+insurer mix enforced. SR-22, 续保/折扣 in SCENARIOS but not in quick_validate. |
| **Deployability** | 7 | `deploy_rag_demo.sh` works; `.env.cloudrun` required. Frontend not deployed (no public URL). |
| **Broker customization** | 8 | `DemoPage.tsx`, `demoCopy.ts`, `SAMPLE_QUESTIONS`, `SCENARIOS` — all configurable. "给陈奎 Demo" already in header. |
| **Payment readiness** | 2 | No payment flow. Manual invoice/Zelle/Venmo is viable. |
| **Maintenance burden** | 6 | One-click ingest, quick_validate, demo_prepare_tomorrow exist. Collection naming fragmented; port mismatch (8000 vs 8001). |

**Overall**: 6.3 / 10 — sufficient for a paid pilot with manual payment and single-tenant use.

---

## 3. Top Failure Risks

### Top 5 likely failure points for a real broker demo

1. **Backend / Qdrant unreachable**
   - **Cause**: `.env` / `.env.cloudrun` missing or wrong; Qdrant Cloud cold start; network/VPN.
   - **Mitigation**: Run `demo_prepare_tomorrow.sh` night before; use Offline mode if backend fails; verify `QDRANT_URL`, `QDRANT_API_KEY` in `.env.cloudrun`.
   - **Files**: `scripts/run_demo_local.sh`, `configs/demo.env.example`, `services/fiqa_api/clients.py`

2. **`auto_insurance_demo_core` empty or stale**
   - **Cause**: One-click ingest not run; discovery run missing; collection deleted.
   - **Mitigation**: `bash scripts/run_demo_ingest_oneclick.sh` before demo; ensure `results/auto_insurance_discovery/runs/` has a run with `passing.json` or `RUN_REVIEW.md`.
   - **Files**: `scripts/run_demo_ingest_oneclick.sh`, `scripts/build_demo_core_collection.py`

3. **Translation fails (Chinese query → English search)**
   - **Cause**: `TRANSLATION_ENABLED=1`, `TRANSLATION_PROVIDER=argos` not set; Argos API down.
   - **Mitigation**: `run_demo_local.sh` sets these; if Argos fails, queries still run in English (degraded). Test with `scripts/smoke_test_translation_query.sh`.
   - **Files**: `services/fiqa_api/utils/translation.py`, `scripts/run_demo_local.sh`

4. **Wrong question returns poor results**
   - **Cause**: Broker asks SR-22, 保费上涨, or niche question not well covered in `auto_insurance_demo_core`.
   - **Mitigation**: Stick to 5 validated questions in demo; add 1–2 broker-specific questions to `SAMPLE_QUESTIONS` and re-run quick_validate.
   - **Files**: `ui/src/pages/DemoPage.tsx` (SAMPLE_QUESTIONS, SCENARIOS), `scripts/demo_quick_validate.py`

5. **UI shows "Offline" or error during live demo**
   - **Cause**: Backend down; CORS; proxy misconfigured; port mismatch.
   - **Mitigation**: Use Offline mode as fallback (3 sample questions load from `demo_fallback.json` or `DEFAULT_FALLBACK_ITEMS`). Ensure Vite proxy targets 8001 (`vite.config.ts`).
   - **Files**: `ui/src/pages/DemoPage.tsx`, `ui/vite.config.ts`, `ui/src/assets/demo_fallback.json`

---

## 4. Fastest Path to First Cash

### Minimum sellable version ("first paid pilot")

| Component | Status | Action |
|-----------|--------|--------|
| **Demo UI** | ✅ | Rename for 陈奎; ensure 5 sample questions visible |
| **Backend** | ✅ | `mode=demo` → `auto_insurance_demo_core`; translation; gov+insurer diversity |
| **Data** | ✅ | `auto_insurance_demo_core` ≥20 docs; re-run one-click ingest if thin |
| **Validation** | ✅ | `demo_quick_validate.sh` PASS |
| **Payment** | ❌ | **Manual**: Zelle / Venmo / WeChat. Send invoice PDF. |
| **Onboarding** | ❌ | **Manual**: 3-step email ("1. Open URL 2. Try 5 questions 3. Copy to client") |
| **Support** | ❌ | **Manual**: WeChat / email; no ticketing |

### What can be manual at first

- Payment collection (Zelle, Venmo, WeChat, bank transfer)
- Onboarding (email with URL + 3 steps)
- Support (direct message)
- Terms of use (simple one-pager; can paste in email)

### What should NOT be built yet

- Stripe / Paddle / LemonSqueezy
- Multi-tenant auth
- Usage limits / rate limiting
- LLM answer generation (retrieval-only is enough)
- Billing dashboard
- China / Europe region config

### Simplest payment path

1. **Zelle / Venmo / WeChat**: Share your handle. Send invoice (PDF or simple table: "CA Auto Insurance Broker AI — Pilot $X/mo — Due [date]").
2. **Stripe Payment Link** (if you want a link): Create product "Broker Pro Pilot $29/mo", get payment link, add to landing or email. No integration needed.
3. **Manual invoice**: Google Doc / Notion template; send as PDF.

### Simplest onboarding path

1. Email 陈奎: "Here's your pilot: [URL]. Try these 5 questions. Copy answers to clients via the 复制给客户 button."
2. Optional: 1-page PDF "How to use" (screenshot + 3 steps).

### Simplest support path

- WeChat / email for questions
- If bug: you fix, redeploy, notify. No ticketing system.

### Version roadmap

| Version | When | What |
|---------|------|------|
| **First paid pilot** | Week 1–2 | Demo works; 5 questions; manual payment; manual onboarding |
| **After first payment** | Week 3 | Stripe link (optional); testimonial quote; 1–2 more questions from feedback |
| **After first testimonial** | Week 4+ | Landing page with testimonial; Stripe checkout; optional LLM generation |

---

## 5. Manual Work Reduction Plan

### Division of labor

| Task | Owner | Notes |
|------|-------|-------|
| **Direction, pricing, final decisions** | You | Non-delegable |
| **Customer meetings, demos** | You | 15–30 min; use prepared script |
| **Repetitive testing** | **Cursor** | Run `demo_quick_validate.sh`; fix failures; add test cases |
| **Repetitive content updates** | **Cursor** | Edit `DemoPage.tsx`, `demoCopy.ts`, `SAMPLE_QUESTIONS` |
| **Repo cleanup** | **Cursor** | Low priority; defer |
| **Repeated demo setup** | **Cursor** | Document in `docs/DEMO_FOR_CHENKUI_ACCEPTANCE.md`; script `run_demo_local.sh` |
| **Lead research** | **ChatGPT** | "Find CA auto insurance brokers in [city]" |
| **Summary writing** | **ChatGPT** | Meeting notes, one-pagers, outreach copy |
| **Daily ingest, discovery runs** | **OpenClaw** | `run_demo_ingest_oneclick.sh`, `discover_auto_insurance_sources.py` — schedule via cron or OpenClaw |
| **Snapshot offline pack** | **OpenClaw** | `snapshot_demo_answers.py` — run after ingest |

### What Cursor can handle directly

- Edit `ui/src/pages/DemoPage.tsx` (questions, copy, scenarios)
- Edit `ui/src/utils/demoCopy.ts` (copy formats)
- Add validation rules to `scripts/demo_quick_validate.py`
- Fix bugs in `routes/query.py`, `search_core.py`
- Update `docs/DEMO_FOR_CHENKUI_ACCEPTANCE.md`
- Run and interpret `demo_quick_validate.sh`

### What OpenClaw can handle outside the repo

- Run `discover_auto_insurance_sources.py` on schedule
- Run `run_demo_ingest_oneclick.sh` weekly
- Run `snapshot_demo_answers.py` after ingest
- Send you a summary (e.g., "Ingest complete; 28 docs in auto_insurance_demo_core")

### What should remain human-only

- Customer meetings and demos
- Pricing and contract negotiation
- Payment collection (until Stripe automated)
- Final approval of copy and positioning
- Deciding which questions to add/remove

### Where you are still likely to waste time (if not redesigned)

1. **Pre-demo validation**: Run `demo_quick_validate.sh` and `demo_prepare_tomorrow.sh` the night before. Add to calendar.
2. **Env/keys**: Keep `.env.cloudrun` in a secure place; document required vars in `configs/demo.env.example`.
3. **Repeated ingest**: If you add URLs manually, you still run `build_demo_core_collection.py` — consider a small script that reads from a "broker URLs" file.
4. **Summary writing**: Use ChatGPT to draft meeting notes and one-pagers; you edit and approve.

---

## 6. Modern Model / Agent Fit

### Retrieval only vs retrieval + generation

| Mode | Current | Recommendation |
|------|---------|----------------|
| **Retrieval only** | ✅ Default | **Keep for MVP.** Snippets + bullets + steps + citations are enough for brokers. |
| **Retrieval + LLM generation** | Optional (`generate_answer=True`) | **Defer.** Add after first testimonial if broker asks for "full paragraph answer." |

### Where a stronger reasoning model would help

- **Query expansion**: "保费涨了" → "premium increase factors California" — current translation handles this.
- **Answer synthesis**: Combining 3–5 snippets into one coherent paragraph — not critical for MVP.
- **Multi-hop**: "Compare Geico vs State Farm minimum coverage" — niche; defer.

### Where plain retrieval is enough

- Minimum coverage (15/30/5)
- Registration suspension / reinstatement
- License / compliance lookup (insurance.ca.gov)
- SR-22 (if in corpus)
- Common discounts (if in corpus)

### LLM answer generation: now or later?

**Later.** Current flow: retrieval → snippets → `buildHighlights` (bullets, steps) → copy-to-client-ready. Brokers value citations; synthesized text can wait.

### Agent-style workflows: now or after first customer?

**After first customer.** Agent workflows (multi-step reasoning, tool use, planning) add complexity. For a single broker pilot, retrieval + simple UI is sufficient.

### "Latest-model compatible architecture" — practical meaning

| Component | Current | Future-ready |
|-----------|---------|--------------|
| **Embeddings** | `all-MiniLM-L6-v2` / `bge-small-en-v1.5` (384 dim) | Env var `EMBEDDING_MODEL`; swap in `clients.py` |
| **Vector DB** | Qdrant Cloud | `qdrant_adapter.py`; could add Milvus/Pinecone via adapter |
| **LLM** | OpenAI (optional) | `llm_client.py`; model in env |
| **Translation** | Argos | `translation.py`; provider in env |

### Region-specific configuration (US / China / Europe)

**Existing**: `COLLECTION_MAP` in `routes/query.py` and `search_core.py` maps `demo_auto_insurance` → `auto_insurance_demo_core`.

**Proposed**: "Common base + region config pack"

- **Base**: `services/fiqa_api/` — query route, search_core, translation, clients.
- **Region pack**: JSON/YAML per region, e.g. `configs/regions/ca_auto_insurance.json`:
  ```json
  {
    "collection": "auto_insurance_demo_core",
    "gov_domains": ["dmv.ca.gov", "insurance.ca.gov"],
    "sample_questions": [...]
  }
  ```
- **Refactor later**: Load region config at startup; use for collection, diversity rules, sample questions. Not needed for 陈奎 pilot.

---

## 7. Broker-Specific Customization Plan (陈奎 Version)

### What to rename/reposition in the UI

| Current | 陈奎 Version |
|---------|--------------|
| "加州汽车保险智能助手（给陈奎 Demo）" | "陈奎专属 · 加州汽车保险智能助手" or "保险经纪人智能助手 — 陈奎版" |
| "Ask questions about car insurance in California (中英文均可)" | "客户常问的问题，一键查官方答案，直接复制发微信" |
| "数据来源：加州 DMV / 加州保险监管机构 / 主流保险公司官方页面" | Keep (builds trust) |

**Files**: `ui/src/pages/DemoPage.tsx` lines 402–405.

### 5 sample questions to include

1. **新车最低保险** — "我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？" ✅ (validated)
2. **注册暂停恢复** — "我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？" ✅ (validated)
3. **合规查询** — "客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？" ✅ (validated)
4. **SR-22** — "SR-22 是什么？什么时候需要？" (add to quick_validate)
5. **续保/折扣** — "客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？" (add to quick_validate)

**Action**: Add Q4, Q5 to `scripts/demo_quick_validate.py` and run validation. Add to `SAMPLE_QUESTIONS` in `DemoPage.tsx`.

### Broker pain points to highlight

1. **重复性问题** — 客户总问最低保额、注册恢复、合规查询；手动查 DMV/CDI 费时。
2. **权威来源** — 需要官方链接给客户，避免合规风险。
3. **一键复制** — "复制给客户（可直接发微信）" 减少复制粘贴。
4. **中英混合** — 客户用中文问，系统查英文资料，自动翻译显示。

### Data/docs to add first

- **SR-22**: Add dmv.ca.gov SR-22 page, insurer SR-22 pages to discovery seeds. Run `run_demo_ingest_oneclick.sh`.
- **Discounts / 续保**: Add insurer discount pages (multi-car, good driver, etc.) to discovery. Re-run ingest.
- **Optional**: 陈奎's own FAQ (if he has a doc) — add via `build_demo_core_collection.py --url-list`.

**Discovery seeds**: `scripts/discover_auto_insurance_sources.py`; `results/auto_insurance_discovery/` or `docs/auto_insurance_data_sources.md`.

### 15-minute live demo flow

| Minute | Action |
|--------|--------|
| 0–2 | Open demo URL. Show title: "保险经纪人智能助手 — 陈奎版". Point out data sources. |
| 2–5 | Click Q1 (新车最低保险). Show bullets, steps, citations. Click "复制给客户（可直接发微信）". Paste into WeChat mock. |
| 5–8 | Click Q2 (注册暂停恢复). Show dmv.ca.gov citation. Emphasize "官方来源". |
| 8–11 | Click Q3 (合规查询). Show insurance.ca.gov. "客户问合规，直接查这里." |
| 11–13 | Type a custom question (e.g. SR-22 or 续保). Show results. |
| 13–15 | "您平时客户最常问哪几个问题？我们可以加进去。" Collect feedback. |

### Feedback questions to ask 陈奎

1. "您客户最常问的 3 个问题是什么？"
2. "您觉得哪些来源（DMV、保险公司）最有用？"
3. "复制给客户的格式够用吗？需要改吗？"
4. "您愿意付多少钱/月用这个？（比如 $29、$49）"
5. "您能给我们一句推荐语吗？（用于其他经纪人）"

### Small changes to make him feel "this is for me"

1. **Header**: Add his name or "专属版" — `DemoPage.tsx` line 402.
2. **WeChat copy**: Ensure `buildCopyTextClientReady` format matches how he sends to clients (already good).
3. **One extra question**: Add his #1 client question to `SAMPLE_QUESTIONS` after the demo.
4. **Branding**: Optional — add his agency logo/name in a corner (low priority).

---

## 8. 7-Day Execution Plan

### Day 1: Validation and hardening

| Objective | Deliverables | Acceptance |
|-----------|--------------|------------|
| Demo runs and validates | Run `run_demo_local.sh`; run `demo_quick_validate.sh` | PASS |
| Ensure collection has data | Run `run_demo_ingest_oneclick.sh` if `auto_insurance_demo_core` &lt; 20 docs | Collection ≥ 20 points |
| Document env | Verify `.env.cloudrun` has QDRANT_*, OPENAI_API_KEY (optional) | `configs/demo.env.example` matches |

### Day 2: 陈奎 customization

| Objective | Deliverables | Acceptance |
|-----------|--------------|------------|
| Rename UI for 陈奎 | Edit `DemoPage.tsx` header, subtitle | "陈奎专属" or similar visible |
| Add 5th question | Add SR-22 or 续保 to `SAMPLE_QUESTIONS`; run quick_validate | 4–5 questions pass |
| Refresh offline pack | Run `snapshot_demo_answers.py` | `demo_fallback.json` has 5 items |

### Day 3: Deploy backend

| Objective | Deliverables | Acceptance |
|-----------|--------------|------------|
| Deploy to Cloud Run | Run `deploy_rag_demo.sh` | Service URL returns 200 for `/healthz`, `/api/query` |
| Test from curl | `curl -X POST $URL/api/query -d '{"question":"...","mode":"demo"}'` | Returns sources |

### Day 4: Deploy frontend (or share local)

| Objective | Deliverables | Acceptance |
|-----------|--------------|------------|
| Option A: Vercel/Netlify | Build `ui`; deploy; set `VITE_API_BASE_URL` to Cloud Run URL | Public demo URL works |
| Option B: Local share | Use ngrok or similar; share `https://xxx.ngrok.io/demo` | 陈奎 can access |

### Day 5: Demo rehearsal

| Objective | Deliverables | Acceptance |
|-----------|--------------|------------|
| 15-min script | Follow flow in Section 7 | Rehearse once |
| Prepare feedback form | 5 questions from Section 7 | Ready to ask |

### Day 6: Schedule and run demo

| Objective | Deliverables | Acceptance |
|-----------|--------------|------------|
| Demo with 陈奎 | 15-min live demo | He sees value; gives feedback |
| Capture feedback | Notes on questions, pricing, testimonial | Written down |

### Day 7: Payment and onboarding

| Objective | Deliverables | Acceptance |
|-----------|--------------|------------|
| Send invoice | PDF or table: Pilot $X/mo | Sent |
| Send onboarding email | URL + 3 steps + 5 questions | Sent |
| Optional: Stripe link | If preferred over Zelle/Venmo | Link ready |

---

## 9. Recommended Immediate Next Actions

1. **Run demo validation**
   ```bash
   cd /home/andy/searchforge
   bash scripts/run_demo_local.sh
   # In another terminal:
   bash scripts/demo_quick_validate.sh
   ```
   If FAIL: check `auto_insurance_demo_core`; run `bash scripts/run_demo_ingest_oneclick.sh`.

2. **Rename DemoPage header for 陈奎**
   - File: `ui/src/pages/DemoPage.tsx` line 402
   - Change to: "陈奎专属 · 加州汽车保险智能助手" or similar

3. **Add 5th sample question**
   - File: `ui/src/pages/DemoPage.tsx` — add SR-22 or 续保 to `SAMPLE_QUESTIONS`
   - Run `demo_quick_validate.sh` with updated questions (may need to edit `demo_quick_validate.py` to add Q4, Q5)

4. **Verify .env.cloudrun**
   - Ensure `QDRANT_URL`, `QDRANT_API_KEY` are set
   - `QDRANT_COLLECTION` can stay `fiqa_10k_v1`; demo uses `auto_insurance_demo_core` via `mode=demo`

5. **Deploy backend**
   ```bash
   cp configs/demo.env.example .env.cloudrun  # if not exists
   # Edit .env.cloudrun
   bash scripts/deploy_rag_demo.sh
   ```
   Note the service URL.

6. **Deploy frontend or set up shareable URL**
   - Vercel: `cd ui && npm run build && vercel --prod`
   - Or ngrok: `ngrok http 5173` and share URL + `/demo`

7. **Schedule 15-min demo with 陈奎**
   - Use public URL or ngrok
   - Prepare 5 feedback questions

8. **Create invoice template**
   - Simple: "CA Auto Insurance Broker AI — Pilot — $X/mo — Due [date]"
   - PDF or Google Doc

9. **Create onboarding email**
   - 3 steps: Open URL, try 5 questions, use 复制给客户
   - Attach or link 1-page "How to use" if desired

10. **Run demo_prepare_tomorrow the night before demo**
    ```bash
    bash scripts/demo_prepare_tomorrow.sh
    ```
    Ensures offline pack and validation are fresh.

---

## Appendix: Key File Reference

| Purpose | Path |
|---------|------|
| Demo UI | `ui/src/pages/DemoPage.tsx` |
| Demo copy utils | `ui/src/utils/demoCopy.ts` |
| Query API (mode=demo) | `services/fiqa_api/routes/query.py` |
| Search core (collection map, gov boost) | `services/fiqa_api/services/search_core.py` |
| Offline fallback | `ui/src/assets/demo_fallback.json` |
| Run demo local | `scripts/run_demo_local.sh` |
| Quick validate | `scripts/demo_quick_validate.sh`, `scripts/demo_quick_validate.py` |
| One-click ingest | `scripts/run_demo_ingest_oneclick.sh` |
| Build demo collection | `scripts/build_demo_core_collection.py` |
| Deploy Cloud Run | `scripts/deploy_rag_demo.sh` |
| Demo prepare (offline pack) | `scripts/demo_prepare_tomorrow.sh` |
| Env template | `configs/demo.env.example` |
| 陈奎 acceptance doc | `docs/DEMO_FOR_CHENKUI_ACCEPTANCE.md` |

---

*End of report*
