# Current Architecture — Module Guide (Founder-Readable)

This guide explains **what each major piece does** in plain language. Technical names point to real files so engineers can drill in.

---

## 1. `triage.py` — the triage engine (“main brain”)

**Path:** `services/fiqa_api/inbox_triage/triage.py`

**What it does:**

- Takes customer text (and optional conversation history, soft-route hints, case context) and produces a **structured triage result**: category, urgency, broker next step, client prep, draft reply, whether a human must follow up, etc.
- Applies **rule-based** logic (keywords, markers, workflow state) and can use an **LLM** when enabled — with fallbacks when LLM is off.
- Owns **workflow state keys** (collection stage, handoff readiness, what to ask next, lifecycle status) that must stay consistent with persistence.
- Implements **complex product behaviors**: add-car progression, append vs new-issue boundaries, handoff stitching, document/payment mixed intents, etc.

**Why it matters:** This is the **highest-concentration** of product behavior. Most “the product feels wrong” bugs trace here — but **wording-only** fixes should usually go to **config first**.

**Founder shorthand:** *这里是“主脑”：决定怎么分类、怎么追问、什么时候移交办公室。*

---

## 2. `config_loader.py` — configuration loader (“装载层”)

**Path:** `services/fiqa_api/inbox_triage/config_loader.py`

**What it does:**

- Loads JSON from `configs/` relative to repo root.
- Exposes getters: insurance markers, document item markers, handoff phrases, stitched phrases, category templates, merged reply templates (industry + client overrides), add-car rules, soft-route copy, UI copy, active `CLIENT_ID`.

**Why it matters:** This file encodes **which file wins** when industry and client disagree. Understanding it prevents accidental **cross-client bleed** (e.g. falling back to Chen Kui when a phrase is missing).

**Founder shorthand:** *这里负责“按客户装文案和规则”，决定行业默认和客户覆盖怎么合并。*

---

## 3. `routes/inbox_triage.py` — HTTP API (“前台接待”) 

**Path:** `services/fiqa_api/routes/inbox_triage.py`

**What it does:**

- Defines **REST endpoints** under `/api/inbox/`: triage, client config, case listing, attachments, scenario logic center, etc.
- Normalizes input, wires **session** and **case persistence**, passes `client_id` / conversation into the engine.
- Applies **soft_route** hints (quick-start buttons) using copy from `get_soft_route_inbox_copy()`.

**Why it matters:** This is the **contract** between UI and engine. Changes here affect **every client** unless carefully gated.

**Founder shorthand:** *这是 API 层：网页点什么、发什么 JSON，都在这里进门。*

---

## 4. `case_store.py` — case persistence (“ lightweight 档案柜 ”)

**Path:** `services/fiqa_api/inbox_triage/case_store.py`

**What it does:**

- Saves **demo-safe** case records to JSON (path configurable via env), with status, notes, attachments, message history, workflow fields.

**Why it matters:** Powers the **broker workbench** view and **append** continuity (“same case vs new issue”). Wrong changes can corrupt case shape or break UI expectations.

**Founder shorthand:** *demo 用的案例存储：办公室工作台看到的历史案件在这里。*

---

## 5. Client configuration — industry + client packs (“文案与词库”)

**Industry pack:** `configs/industries/insurance/`

- **`markers.json`** — Keyword buckets for intents (cancellation, questions, documents, etc.) and structured document item labels.
- **`reply_templates.json`** — Baseline reply drafts per scenario key.
- **`category_templates.json`** — Broker/client guidance per issue category.
- **`add_car_rules.json`** — Next-question prompts for the add-car collector.

**Client pack:** `configs/clients/<client_id>/`

- **`handoff_phrases.json`** — What the customer sees when ready for the office; optional `stitched` advanced copy (boundaries, caveats).
- **`reply_overrides.json`** — Per-key overrides over industry templates.
- **`ui_copy.json`** — Strings for Unified Intake UI (titles, buttons, handoff cards).

**Founder shorthand:** *行业目录是“车险通用词库+模板”；客户目录是“这家办公室怎么说”。*

---

## 6. `UnifiedIntakePage.tsx` — unified UI (“门面”) 

**Path:** `ui/src/pages/UnifiedIntakePage.tsx`

**What it does:**

- Customer entry + broker workbench tabs, quick-start buttons, triage calls, case management UX.
- Merges **server `ui_copy`** with **frontend defaults** (see `clientConfig.ts`).

**Why it matters:** Most **founder-visible** product is here + `ui_copy.json`. Code defaults still exist — if JSON is empty, Chen-style defaults may show until pack is filled.

**Founder shorthand:** *用户看到的页面逻辑在这里；文案优先从后端客户配置来。*

---

## 7. `clientConfig.ts` — UI config types & defaults

**Path:** `ui/src/api/clientConfig.ts`

**What it does:**

- Fetches `GET /api/inbox/client-config` and merges with **`DEFAULT_UI_COPY`** (currently Chen-flavored fallbacks).

**Why it matters:** New UI fields need **both** backend allowlist in `get_ui_copy()` and TypeScript `UiCopy` + defaults.

---

## 8. Scenario runners & guardrail (“回归题库”) 

**Main pack:** `configs/inbox_triage_scenarios.json` — labeled inputs and expected category/urgency/manual flags for **rule mode**.

**Guardrail:** `scripts/guardrail_inbox_triage.sh` — runs scenario runner, persistence checks, multi-turn simulations, adversarial packs, **client A/B isolation** scripts, etc.

**Why it matters:** This is how you prove a copy or logic change didn’t break **another broker** or **core scenarios**.

**Founder shorthand:** *这些脚本是“自动化考卷”；上线前要让主 guardrail 变绿。*

---

## 9. App entry (wiring only)

**Path:** `services/fiqa_api/app_main.py`

Includes `inbox_triage_router` so `/api/inbox/*` is live. Rarely edited for client work.

---

## Conceptual summary

- **Engine** decides behavior; **config** decides wording and many thresholds; **UI** presents it.
- **Client pack** is the **hot-plug** surface for a new broker **without** rewriting the engine.
- **Guardrail** is the **proof** that hot-plug didn’t leak or regress.

---

*Next: [FILE_FOLDER_RESPONSIBILITY_MAP.md](./FILE_FOLDER_RESPONSIBILITY_MAP.md)*
