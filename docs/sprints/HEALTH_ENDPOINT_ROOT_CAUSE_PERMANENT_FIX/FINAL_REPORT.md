# Health Endpoint Root-Cause + Permanent Fix Report

## 1. Sprint theme

- **Investigated:** Recurring **404 on `GET /healthz`** against Cloud Run while other health endpoints looked fine.  
- **Why now:** False deploy alarms and wasted debugging time; ops need one trustworthy contract.

## 2. Current endpoint audit

| Endpoint | Defined in app? | Cloud Run public URL (pre-fix) |
|----------|-----------------|--------------------------------|
| `/healthz` | Yes (`app_main.py`, `health/ready.py`) | **404** — **Google HTML** error page |
| `/readyz` | Yes | **200** — JSON from app |
| `/health/live` | Yes | **200** — JSON from app |
| `/api/healthz` | **Added this sprint** | **404** until new revision deployed (was “no route”; still reached app) |

**Deploy scripts (pre-fix):** `scripts/deploy_rag_demo.sh` curled `/healthz` and reported failure.  
**Container `HEALTHCHECK` (pre-fix):** `curl` to **localhost** `/healthz` — usually still hits uvicorn inside the pod (not the same as public URL).

**Code citations:** `services/fiqa_api/app_main.py` (`healthz`, `health_live`, router includes); `services/fiqa_api/health/ready.py` (`/healthz`, `/readyz`); `services/fiqa_api/Dockerfile.cloudrun` (`CMD` + `HEALTHCHECK`).

## 3. Reproduction / evidence

- **Direct:** `curl -i https://fiqa-api-g7zatxrycq-uw.a.run.app/healthz` → HTML 404 from Google; `/readyz` and `/health/live` → 200 JSON.  
- **Direct:** `/api/healthz` before deploy → `{"detail":"Not Found"}` (proves traffic reached FastAPI, unlike `/healthz`).  
- **Code:** `app.routes` includes `/healthz` — so “route missing” hypothesis falsified for app code.  
- **Inferred:** Local `/healthz` works when served by `app_main:app` (standard dev).

## 4. Root-cause judgment

**Single cause:** **Google Cloud Run’s HTTP frontend handles `GET /healthz` and returns its own 404 HTML before the request is forwarded to the container.**  

`/healthz` is **not** “missing in FastAPI” and **not** explained by router prefixing alone.  

`/readyz` and `/health/live` **reach the app**, so they behave as expected.

## 5. What was changed

| Area | Change |
|------|--------|
| `services/fiqa_api/app_main.py` | Added `GET /api/healthz` (liveness alias → `health_live`); SPA skip list uses explicit `healthz`/`readyz` + `health/`; root JSON lists `liveness` + `health_cloud_run`. |
| `services/fiqa_api/Dockerfile.cloudrun` | `HEALTHCHECK` → `/health/live`. |
| `scripts/deploy_rag_demo.sh` | Liveness: `/health/live` → `/api/healthz` → `/healthz`; summary curl hints updated. |
| `scripts/deploy_and_verify_cloud_run.sh` | Same liveness ladder; final checklist uses **LIVE_OK**. |
| `scripts/smoke_cloud_run.sh` | Liveness uses `/health/live` (+ fallbacks). |
| `scripts/warmup_for_demo.sh` | Tries `/health/live` and `/api/healthz` before `/healthz`. |
| `docs/runbooks/KNOWN_DEPLOYMENT_GOTCHAS.md` | New §1 Cloud Run `/healthz`; renumbered sections. |
| `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` | Cloud Run liveness guidance. |
| `docs/runbooks/COLD_START_DEMO_DAY_RUNBOOK.md` | Warmup description aligned. |
| `docs/sprints/HEALTH_ENDPOINT_ROOT_CAUSE_PERMANENT_FIX/*` | Blueprint, audit, evidence, decision, execution, acceptance, founder notes, this report. |

## 6. Validation summary

- **Code:** `/api/healthz`, `/health/live`, `/healthz`, `/readyz` all present on `app.routes` after change.  
- **Production (this sprint, without redeploy):** `/health/live` and `/readyz` still 200; `/api/healthz` becomes 200 **after** deploying a revision that includes this commit.  
- **Deploy script logic:** No longer treats Google’s `/healthz` 404 as the primary liveness gate.

## 7. Deployment judgment

- **Backend redeploy:** **Yes** — required for **`/api/healthz`** to exist in production.  
- **Deploy performed in this sprint:** **No** (code + docs + scripts only from this workspace session).  
- **Current production truth:** Public `/healthz` may still be Google 404; trust **`/health/live`** and **`/readyz`**.

## 8. Final operational judgment

- **Permanently fixed?** **Yes, for ops confusion** — the false “app is broken” signal from Cloud Run `/healthz` is explained and bypassed in scripts/docs. **No** — we cannot force Google to deliver public `/healthz` to the container from app code.  
- **Use going forward:** **Liveness** = `/health/live` (or `/api/healthz` after deploy). **Readiness** = `/readyz`.  
- **Trust:** Scripts and monitoring should prefer those URLs on Cloud Run.

## 9. 中文宏观总结

- **`/healthz` 为什么一直 404：** 很多时候不是 FastAPI 没挂路由，而是 **Cloud Run 外层的 Google 前端直接回了 404 网页**，请求根本没进容器。  
- **真正该用哪个：** **存活（liveness）用 `/health/live`**（部署后也 **`/api/healthz`**）；**就绪/依赖看 `/readyz`**。  
- **这次改了什么：** 部署脚本、Docker 健康检查、预热脚本、运维文档改成认上述契约；代码里加了 **`/api/healthz`** 别名；修了 SPA 兜底路径里 `health` 前缀误伤 `healthz` 的隐患。  
- **以后还会不会被干扰：** 按新契约检查后，**不会再因为 Cloud Run 上公共 `/healthz` 的 Google 404 而误判后端挂了**；若有人仍只盯 `/healthz`，仍可能看到 404，但那是 **已知平台行为**，不是回归信号。

## 10. COPY/PASTE FOUNDER BLOCK

```
Root cause: Public GET /healthz on Cloud Run is often answered by Google’s HTTP frontend (HTML 404) before the request reaches our container — not a missing FastAPI route.

Canonical endpoints: Liveness = GET /health/live (and GET /api/healthz after next backend deploy). Readiness = GET /readyz.

Deploy script: Updated to use /health/live first (then /api/healthz, then /healthz). No more “healthz FAILED = app broken” as the only story.

Production match: After you deploy this revision, /api/healthz will return 200 JSON like /health/live. Public /healthz may still 404 at Google — ignore for ops.

Status: Closed for false-alarm purposes; platform /healthz quirk remains, contract documented.
```

## 11. REQUIRED SHORT OVERVIEW

### 为什么做这件事

反复出现的 **`/healthz` 404** 让部署结果看起来失败，消耗信任与调试时间，需要搞清楚是 **应用** 还是 **平台** 的问题。

### 主要用了什么方法/技术

代码审计（FastAPI 路由、Dockerfile、脚本）、对生产 URL 的 **`curl -i` 对比**（Google HTML vs FastAPI JSON）、把 **liveness 探针** 改到可达路径并补充 **`/api/healthz`** 别名。

### 这轮最大的结论

**404 来自 Google 边缘对 `/healthz` 的处理，不是应用没注册路由。** **`/health/live` 与 `/readyz` 才是 Cloud Run 上可靠的探针路径。**

### 现在还差什么

**把包含本改动的后端镜像部署到 Cloud Run**，以便生产环境 **`/api/healthz`** 返回 200；部署后用 `curl` 验收 `health/live`、`api/healthz`、`readyz` 即可。
