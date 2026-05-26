# Security Cleanup + First Real Deploy Report

**Date**: 2026-03-11  
**Sprint**: Security Cleanup + First Real Deploy Sprint

---

## 1. Security cleanup done

### Files cleaned (credentials redacted)

| File | Change |
|------|--------|
| `results/auto_insurance/CLOUD_UPSERT_REPORT.md` | Replaced full QDRANT_URL and QDRANT_API_KEY in Python/cURL examples with env var references and placeholders |
| `docs/archive/QDRANT_CONFIG_DISCOVERY_REPORT.md` | Replaced full QDRANT_URL and QDRANT_API_KEY in `.env.cloudrun` sample with placeholders |
| `docs/archive/INSURANCE_DEMO_REVALIDATION_REPORT.md` | Masked Qdrant URL in log excerpt |
| `docs/archive/INSURANCE_503_ROOT_CAUSE_REPORT.md` | Masked Qdrant URL in log excerpt |
| `DEPLOYMENT_STATUS.md` | Replaced real cluster URL with generic placeholder |
| `scripts/migrate_local_qdrant_to_cloud.py` | Replaced real URL and API key in help-text example with placeholders |
| `configs/demo.env.example` | Replaced real cluster URL in comment with generic example |
| `docs/QDRANT_CLOUD_MIGRATION.md` | Replaced real cluster URL in example with generic format |

### Likely secret leakage

- **None remaining** in tracked files. Grep for JWT pattern and cluster ID returned no matches after cleanup.

### Qdrant key rotation

- **Required.** Credentials were exposed in reports/docs. See `docs/QDRANT_KEY_ROTATION_NOTE.md` for steps.

---

## 2. Env/secret prep status

### Backend (.env.cloudrun)

| Variable | Status | Notes |
|----------|--------|-------|
| QDRANT_URL | Human confirmation | From Qdrant Cloud dashboard |
| QDRANT_API_KEY | Human confirmation | From Qdrant Cloud; rotate if previously exposed |
| QDRANT_COLLECTION | Default set | `auto_insurance_demo_core` in template |
| OPENAI_API_KEY | Human confirmation | For LLM triage; omit for rule-only |
| ALLOWED_ORIGINS | Human confirmation | Vercel URL(s) after frontend deploy |

### Frontend (Vercel)

| Variable | Status | Notes |
|----------|--------|-------|
| VITE_API_BASE_URL | Human confirmation | Cloud Run URL after backend deploy |

### .env.cloudrun

- **Exists** (gitignored). Not modified; may contain real values.
- **Template**: `configs/demo.env.example` updated with explicit "HUMAN CONFIRMATION REQUIRED" section.
- **Deploy script**: Masks Qdrant URL in console output when using Qdrant Cloud.

---

## 3. Deployment prep status

### Backend readiness

- `scripts/deploy_rag_demo.sh` loads `.env.cloudrun`, validates Qdrant, deploys to Cloud Run
- `services/fiqa_api/Dockerfile.cloudrun` present
- Qdrant URL masked in deploy output

### Frontend readiness

- `ui/vercel.json` has SPA rewrites for `/workbench/*`
- `ui/src/api/config.ts` uses `VITE_API_BASE_URL` for production
- Build: `cd ui && npm run build`

### Improvements made

- Security: Redacted credentials in 8 files
- Deploy script: Mask Qdrant URL in output
- Template: Added human-confirmation section to `configs/demo.env.example`
- Docs: Added `docs/QDRANT_KEY_ROTATION_NOTE.md`, linked from `DEPLOYMENT_MANUAL_STEPS.md`

---

## 4. Remaining manual steps

1. **Rotate Qdrant API key** (recommended): See `docs/QDRANT_KEY_ROTATION_NOTE.md`
2. **Backend**: Ensure `.env.cloudrun` has QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, ALLOWED_ORIGINS (or omit LLM/ALLOWED_ORIGINS for minimal demo)
3. **Backend deploy**: `bash scripts/deploy_rag_demo.sh` → note Cloud Run URL
4. **Frontend**: In Vercel, set `VITE_API_BASE_URL` = Cloud Run URL
5. **Frontend deploy**: `cd ui && vercel --prod`

---

## 5. Exact next commands

```bash
# 1. Backend (after .env.cloudrun is filled)
bash scripts/deploy_rag_demo.sh

# 2. Note the Cloud Run URL printed at end, e.g. https://fiqa-api-xxx.run.app

# 3. Frontend (after VITE_API_BASE_URL set in Vercel)
cd ui && vercel --prod

# 4. Smoke test
curl <Cloud Run URL>/healthz
curl <Cloud Run URL>/readyz
# Open https://<vercel>.vercel.app/workbench/unified-intake
# Paste "Notice: Policy will be cancelled in 7 days" → verify triage
```

---

## 6. 中文总结

- **先把什么危险处理掉了**：从 8 个文件中移除了暴露的 Qdrant URL 和 API Key，包括 CLOUD_UPSERT_REPORT.md、QDRANT_CONFIG_DISCOVERY_REPORT.md 等。仓库中已无完整密钥。
- **现在 deployment 还差什么**：需要你在 `.env.cloudrun` 里填 QDRANT_URL、QDRANT_API_KEY、OPENAI_API_KEY、ALLOWED_ORIGINS；在 Vercel 里设 VITE_API_BASE_URL。建议先轮换 Qdrant API Key。
- **你已经自动做了什么**：脱敏报告文件、更新模板和文档、在 deploy 脚本中隐藏 Qdrant URL 输出、新增 Qdrant 密钥轮换说明。
- **我最后只需要手动做哪几步**：(1) 轮换 Qdrant API Key（建议）；(2) 编辑 `.env.cloudrun` 填好上述变量；(3) 运行 `bash scripts/deploy_rag_demo.sh`；(4) 在 Vercel 设 `VITE_API_BASE_URL`；(5) 运行 `cd ui && vercel --prod`；(6) 按文档做 smoke test。
