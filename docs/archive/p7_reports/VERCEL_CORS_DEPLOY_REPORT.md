# Get Real Vercel URL + Prepare CORS Report

**Generated:** 2025-03-11  
**Mission:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Frontend deploy result

| Status | **Failure** |
|--------|-------------|
| **Blocker** | Vercel CLI not installed (`vercel: command not found`) |
| **Real Vercel URL** | **Unknown** — cannot obtain without deployment |

**What was inspected:**
- `ui/vercel.json` — buildCommand: `npm run build`, output: `dist`, SPA rewrites OK
- `ui/package.json` — Node >=20, build script ready
- `ui/src/api/config.ts` — uses `VITE_API_BASE_URL` for production API base
- Frontend env: `ui/.env` and `ui/.env.local` both have `VITE_API_BASE_URL=http://localhost:8000` (local dev)

**Manual step required:**

1. Install Vercel CLI: `npm i -g vercel`
2. Authenticate: `vercel login`
3. Deploy from `ui/`:
   ```bash
   cd ui
   vercel env add VITE_API_BASE_URL production
   # When prompted, enter: https://fiqa-api-g7zatxrycq-uw.a.run.app
   vercel --prod
   ```
4. After deploy, Vercel will print the deployment URL (e.g. `https://searchforge-ui-xxx.vercel.app`). **Copy that URL** — it is your real Vercel URL.

**Alternative (Vercel Dashboard):**
- Connect repo to Vercel at https://vercel.com
- Set `VITE_API_BASE_URL` = `https://fiqa-api-g7zatxrycq-uw.a.run.app` in Project Settings → Environment Variables
- Deploy; the production URL will be shown (e.g. `https://your-project.vercel.app`)

---

## 2. Correct ALLOWED_ORIGINS value

| When | Value |
|------|-------|
| **After you have the real Vercel URL** | `ALLOWED_ORIGINS=https://<your-real-vercel-url>` |
| **Example** | `ALLOWED_ORIGINS=https://searchforge-ui-abc123.vercel.app` |

**Where to set it:** `.env.cloudrun` (line 61)

Uncomment and replace:
```bash
# Before (commented):
# ALLOWED_ORIGINS=https://your-project.vercel.app

# After (with your real URL, no trailing slash):
ALLOWED_ORIGINS=https://your-actual-vercel-url.vercel.app
```

If you have multiple URLs (e.g. preview + production), use comma-separated:
```bash
ALLOWED_ORIGINS=https://your-project.vercel.app,https://your-project-git-main-xxx.vercel.app
```

---

## 3. Next backend step

**Option A — Redeploy with deploy script (recommended):**

1. Add `ALLOWED_ORIGINS=<real Vercel URL>` to `.env.cloudrun`
2. Run:
   ```bash
   bash scripts/deploy_rag_demo.sh
   ```

**Option B — Update env only (no full redeploy):**

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project optimal-disk-472305-e2 \
  --update-env-vars "ALLOWED_ORIGINS=https://YOUR-REAL-VERCEL-URL.vercel.app"
```

Replace `YOUR-REAL-VERCEL-URL` with your actual Vercel deployment URL.

**CORS status:** Not fixed until you complete the above. The backend will accept requests from the Vercel origin only after `ALLOWED_ORIGINS` is set and deployed.

---

## 4. 中文总结

| 项目 | 说明 |
|------|------|
| **前端发出去没有** | 没有。Vercel CLI 未安装，无法自动部署。 |
| **真正的 Vercel URL 是什么** | 未知。需要你先手动部署前端才能得到。 |
| **ALLOWED_ORIGINS 现在该填什么** | 等你拿到真实 Vercel URL 后，在 `.env.cloudrun` 第 61 行填：`ALLOWED_ORIGINS=https://你的vercel地址.vercel.app` |
| **我下一步只需要做什么** | 1) 安装 `vercel` CLI 并 `vercel login`；2) `cd ui && vercel env add VITE_API_BASE_URL production` 填 `https://fiqa-api-g7zatxrycq-uw.a.run.app`；3) `vercel --prod` 部署；4) 复制部署后的 URL；5) 在 `.env.cloudrun` 里加 `ALLOWED_ORIGINS=该URL`；6) 运行 `bash scripts/deploy_rag_demo.sh` 重新部署后端。 |

---

*Backend URL (Cloud Run):* `https://fiqa-api-g7zatxrycq-uw.a.run.app`
