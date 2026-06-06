# Find All Real Secret Sources + Place Config Correctly Report

**Sprint:** Find All Real Secret Sources + Place Config Correctly Sprint  
**Date:** 2025-03-11  
**Target:** SearchForge → Chen Kui Insurance Unified Entry (Vercel + Cloud Run)

---

## 1. Required deployment vars

### Backend (Cloud Run) — required

| Variable | Purpose | Where referenced | Needs secret |
|----------|---------|------------------|--------------|
| `QDRANT_URL` | Qdrant instance URL | clients.py, deploy_rag_demo.sh | No |
| `QDRANT_API_KEY` | Qdrant Cloud auth | clients.py, deploy_rag_demo.sh | Yes |
| `QDRANT_COLLECTION` | Collection name | clients.py, deploy script; default `auto_insurance_demo_core` | No |
| `OPENAI_API_KEY` | Inbox triage LLM | triage.py, clients.py | Yes |
| `ALLOWED_ORIGINS` | CORS for Vercel | app_main.py | No |

### Backend — optional / feature-gated

| Variable | Purpose | Notes |
|----------|---------|-------|
| `LLM_GENERATION_ENABLED` | Enable LLM triage | Auto-set to 1 when OPENAI_API_KEY present in deploy script |
| `TRANSLATION_ENABLED` | Translation feature | Deploy script sets 1 |
| `TRANSLATION_PROVIDER` | Translation provider | Deploy script sets argos |
| `PROJECT_ID` | GCP project | Default: optimal-disk-472305-e2 |
| `REGION` | Cloud Run region | Default: us-west1 |

### Frontend (Vercel) — required

| Variable | Purpose | Where referenced |
|----------|---------|------------------|
| `VITE_API_BASE_URL` | Backend API URL | ui/src/api/config.ts, inboxTriage, code-lookup |

### Frontend — optional

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE` | Legacy; VITE_API_BASE_URL preferred |
| `VITE_API_PROXY_TARGET` | Dev proxy target (vite.config.ts) |
| `VITE_LANGFUSE_HOST` | Langfuse observability |
| `VITE_LANGFUSE_PROJECT_ID` | Langfuse project |
| `VITE_ORCH_BASE` | Orchestrate base path |
| `VITE_AUTOTUNER_TOKEN` | Dev-only autotuner |

### Legacy / stale / not for demo

| Variable | Notes |
|----------|-------|
| `CORS_ORIGINS` | Legacy; use ALLOWED_ORIGINS |
| `ALLOW_ALL_CORS` | When ALLOWED_ORIGINS unset, defaults allow-all |
| `.env.example` (root) | Uses auto_insurance_v1; use configs/demo.env.example for deploy |

---

## 2. Existing secret/config sources found

| Variable | Status | File location(s) | Confidence |
|----------|--------|-------------------|-------------|
| `QDRANT_URL` | Placeholder in template | configs/demo.env.example | High |
| `QDRANT_API_KEY` | Placeholder (empty) | configs/demo.env.example | High |
| `QDRANT_COLLECTION` | Present (auto_insurance_demo_core) | configs/demo.env.example | High |
| `OPENAI_API_KEY` | Placeholder (empty) | configs/demo.env.example | High |
| `ALLOWED_ORIGINS` | Placeholder (empty) | configs/demo.env.example | High |
| `VITE_API_BASE_URL` | Placeholder | ui/.env.example, ui/.env.local.example | High |
| `.env.cloudrun` | Present (git-ignored) | Repo root | High — contains user values; not inspected |
| `.env` | Present (git-ignored) | Repo root | Medium — local dev; not inspected |

**Note:** `.env.cloudrun` exists and is git-ignored. Do not assume it has all required values; verify manually.

---

## 3. Mismatches and misplaced config

| Issue | Affected files | Why it matters | Blocks deploy? |
|-------|----------------|----------------|----------------|
| Deploy script default QDRANT_COLLECTION was fiqa_10k_v1 | deploy_rag_demo.sh | Unified Intake needs auto_insurance_demo_core | **Fixed** — now defaults to auto_insurance_demo_core |
| Real-looking URL in ui/.env.local.example | ui/.env.local.example | Could leak deployment URL | **Fixed** — replaced with placeholder |
| Real-looking URL in ui/README.md | ui/README.md | Same | **Fixed** — replaced with generic example |
| Exposed secrets in tracked files | results/auto_insurance/CLOUD_UPSERT_REPORT.md, docs/archive/QDRANT_CONFIG_DISCOVERY_REPORT.md | Full QDRANT_API_KEY and QDRANT_URL in docs | **Security** — recommend rotate key, remove or redact from tracked files |
| Vercel env not in vercel.json | ui/vercel.json | Vercel.json has no env; must set in dashboard | No — expected; Vercel uses dashboard/CLI |

---

## 4. Safe fixes made

| File | Change |
|------|--------|
| `scripts/deploy_rag_demo.sh` | QDRANT_COLLECTION default: fiqa_10k_v1 → auto_insurance_demo_core |
| `ui/.env.local.example` | VITE_API_BASE_URL: real URL → placeholder `https://your-cloud-run-url.run.app` |
| `ui/README.md` | Vercel env example: real URL → generic `https://fiqa-api-xxx.run.app` |
| `configs/demo.env.example` | Added header comment: REQUIRED vs optional vars |
| `docs/runbooks/DEPLOYMENT_MANUAL_STEPS.md` | **Created** — manual steps, env table, post-deploy checklist |
| `docs/runbooks/INDEX.md` | Added link to DEPLOYMENT_MANUAL_STEPS |

**Intentionally not touched:**

- `.env.cloudrun` — contains user secrets; never modified
- `.env` — local dev; never modified
- results/auto_insurance/*.md — contain historical secrets; recommend manual review/rotation

---

## 5. Final deployment map

### Vercel needs

| Variable | Source | Action |
|----------|--------|--------|
| `VITE_API_BASE_URL` | Manual | Set in Vercel dashboard = Cloud Run URL (no trailing slash) |

### Cloud Run needs (from .env.cloudrun)

| Variable | Source | Action |
|----------|--------|--------|
| `QDRANT_URL` | .env.cloudrun | Required; fill |
| `QDRANT_API_KEY` | .env.cloudrun | Required for Qdrant Cloud; fill |
| `QDRANT_COLLECTION` | .env.cloudrun | Default auto_insurance_demo_core; override if needed |
| `OPENAI_API_KEY` | .env.cloudrun | Required for LLM triage; fill or omit for rule-only |
| `ALLOWED_ORIGINS` | .env.cloudrun | Set Vercel URL(s) for CORS; unset = allow-all |

### Already present

- `configs/demo.env.example` — template with all vars
- `scripts/deploy_rag_demo.sh` — loads .env.cloudrun, validates, deploys
- `services/fiqa_api/Dockerfile.cloudrun` — Cloud Run build
- `ui/vercel.json` — SPA rewrites
- `.env.cloudrun` — exists, git-ignored (user must verify values)

### Still manual

1. Create `.env.cloudrun` from `configs/demo.env.example` (if not exists)
2. Fill: QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, ALLOWED_ORIGINS
3. Run `bash scripts/deploy_rag_demo.sh`
4. In Vercel: set `VITE_API_BASE_URL` = Cloud Run URL
5. Deploy frontend

### Optional

- `TRANSLATION_ENABLED`, `TRANSLATION_PROVIDER` — deploy script sets them
- `LLM_GENERATION_ENABLED` — auto-set when OPENAI_API_KEY present

---

## 6. Readiness verdict

**Ready after a few manual secret confirmations**

- Backend: Deploy script, Dockerfile, env template ready. User must fill .env.cloudrun.
- Frontend: Build works; Vercel needs VITE_API_BASE_URL after backend deploy.
- No blocking gaps. Execute `docs/runbooks/DEPLOYMENT_MANUAL_STEPS.md`.

---

## 7. 中文宏观总结

**真正需要的环境变量：**

- **后端：** QDRANT_URL、QDRANT_API_KEY（Qdrant Cloud 时）、QDRANT_COLLECTION、OPENAI_API_KEY（要 LLM 时）、ALLOWED_ORIGINS（Vercel 时）
- **前端：** VITE_API_BASE_URL（Cloud Run 地址）

**哪些已经在项目里找到了：**

- `configs/demo.env.example` 有完整模板
- `.env.cloudrun` 已存在且 git-ignored（未读取内容，需你自行确认是否已填好）
- 部署脚本、Dockerfile、Vercel 配置都已就绪

**哪些只是示例值：**

- demo.env.example 里的 QDRANT_URL、QDRANT_API_KEY、OPENAI_API_KEY 均为占位符
- ui/.env.example、ui/.env.local.example 的 VITE_API_BASE_URL 已改为占位符

**哪些还缺：**

- 你需要手动在 `.env.cloudrun` 里填：QDRANT_URL、QDRANT_API_KEY、OPENAI_API_KEY、ALLOWED_ORIGINS
- 在 Vercel 里设 VITE_API_BASE_URL

**你已经帮我放好了哪些非敏感配置：**

- 部署脚本默认 QDRANT_COLLECTION 改为 auto_insurance_demo_core
- ui 示例文件里的真实 URL 已换成占位符
- 新增 `docs/runbooks/DEPLOYMENT_MANUAL_STEPS.md` 手动步骤清单
- demo.env.example 增加 REQUIRED/optional 说明

**我最后还需要手动做哪几步：**

1. `cp configs/demo.env.example .env.cloudrun`（若还没有）
2. 编辑 `.env.cloudrun`，填 QDRANT_URL、QDRANT_API_KEY、OPENAI_API_KEY、ALLOWED_ORIGINS
3. `bash scripts/deploy_rag_demo.sh`，记下 Cloud Run URL
4. 在 Vercel 项目设置里添加 `VITE_API_BASE_URL` = Cloud Run URL
5. 部署前端，按 `docs/runbooks/DEPLOYMENT_MANUAL_STEPS.md` 做一次 post-deploy 验证

**安全提醒：** `results/auto_insurance/CLOUD_UPSERT_REPORT.md` 和 `docs/archive/QDRANT_CONFIG_DISCOVERY_REPORT.md` 中可能包含完整密钥。建议轮换 QDRANT_API_KEY，并从这些文件中移除或脱敏。
