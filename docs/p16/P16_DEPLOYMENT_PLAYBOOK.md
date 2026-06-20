# P16 Deployment Playbook

**Date:** 2026-06-20  
**Status:** Frozen — paid pilot phase  
**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md`

---

## North Star

One stable QA URL. Always.

Pilot users, brokers, screenshots, demo scripts, onboarding docs, and QA reports  
reference **only** the stable QA URL. Preview URLs are engineering-internal only.

---

## Stable QA URL

```
https://ui-smoky-beta.vercel.app/add-car
```

**Backend:**

```
https://fiqa-api-1013093472160.us-west1.run.app
```

---

## Stable QA URL Only Rule — 冻结规则

下列规则在 paid pilot 阶段冻结，不允许例外。

1. Preview URL 仅限工程内部使用。
2. Preview URL 不得作为最终 QA URL 返回给 Andy 或任何人。
3. Preview URL 不得出现在：
   - demo 脚本
   - pilot 文档
   - 截图说明
   - 发给 broker 的消息
   - 发给客户的消息
   - 任何 release report
4. 每次 Vercel 部署完成后，**立即**将新 deployment alias 到稳定域名：`ui-smoky-beta.vercel.app`
5. 所有验证（CORS / 提取 / 功能 QA）必须针对稳定域名执行。
6. 如果稳定 QA URL 失败但 preview URL 成功，**部署未完成**。必须先修好 alias，再报告结果。
7. 不得将新 preview URL 添加到 Cloud Run `ALLOWED_ORIGINS`。
8. 如果在 preview URL 上遇到 CORS 报错，**不要**通过白名单 preview URL 来修复。那是症状，不是原因。
9. 正确修复路径：Deploy → Alias → 从稳定 QA URL 测试 → 验证 CORS。
10. 最终部署报告只能包含：

```
QA URL:
https://ui-smoky-beta.vercel.app/add-car
```

---

## Deployment Flow

### Frontend Deploy

```bash
# 1. Deploy to Vercel
cd ui && vercel --prod --yes

# 2. Capture the preview URL from the output (engineering-internal only)
#    e.g. https://ui-xxxx-andys-projects-1f411b73.vercel.app

# 3. IMMEDIATELY alias to stable QA URL
vercel alias https://ui-xxxx-andys-projects-1f411b73.vercel.app ui-smoky-beta.vercel.app

# 4. Verify alias
curl -s -o /dev/null -w "%{http_code}" https://ui-smoky-beta.vercel.app/add-car
# Expected: 200
```

**Why alias first:** Every Vercel deploy creates a new unique preview domain. That domain  
is NOT in `ALLOWED_ORIGINS` on Cloud Run. Testing from it will fail with CORS errors.  
The stable alias (`ui-smoky-beta.vercel.app`) is already whitelisted — always test from there.

### Backend Deploy (when backend changed)

```bash
# Deploy paid pilot posture
bash scripts/deploy_paid_pilot.sh

# Verify health
curl -s https://fiqa-api-1013093472160.us-west1.run.app/health/live
# Expected: {"ok": true}
```

### CORS Validation

```bash
curl -s -X OPTIONS https://fiqa-api-1013093472160.us-west1.run.app/api/intake/add-car/extract \
  -H "Origin: https://ui-smoky-beta.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -i | grep -E "HTTP/|access-control-allow-origin"
# Expected: HTTP/2 200 + access-control-allow-origin: https://ui-smoky-beta.vercel.app
```

If CORS fails: `ui-smoky-beta.vercel.app` must be in `ALLOWED_ORIGINS` on Cloud Run.  
Check: `gcloud run services describe fiqa-api --region us-west1 --project optimal-disk-472305-e2 --format='value(spec.template.spec.containers[0].env)'`

### Functional Validation

```bash
# Extraction smoke test
curl -s -X POST https://fiqa-api-1013093472160.us-west1.run.app/api/intake/add-car/extract \
  -H "Origin: https://ui-smoky-beta.vercel.app" \
  -F "customer_name=Test User" \
  -F "phone=6265550000" \
  -F "garaging_zip=91101" | python3 -c "import sys,json; r=json.load(sys.stdin); print('OK' if r.get('packet') else 'FAIL')"
# Expected: OK
```

Manual validation (< 3 min): open `https://ui-smoky-beta.vercel.app/add-car` →  
complete intent → info → upload → extract → verify packet → copy packet.

---

## DEPLOY_CHECKLIST

```
□ Frontend deployed (vercel --prod --yes)
□ Stable alias updated (vercel alias [preview] ui-smoky-beta.vercel.app)
□ Stable alias verified (HTTP 200 from ui-smoky-beta.vercel.app/add-car)
□ Backend deployed (if backend changed)
□ Backend health verified ({"ok": true})
□ CORS verified (preflight HTTP 200 + correct allow-origin header)
□ Extraction endpoint verified (packet returned)
□ Manual QA flow verified (intent → upload → packet → copy)
```

---

## Required Release Report Footer

每次部署报告**必须**以下面这个格式结尾。不得出现 preview URL。

```
DEPLOY_STATUS:
Frontend:    [deployed / skipped]
Backend:     [Cloud Run revision / skipped]
Alias:       ui-smoky-beta.vercel.app updated → [yes / no]
CORS:        [pass / fail]
Functional QA: [pass / fail]

QA URL:
https://ui-smoky-beta.vercel.app/add-car
```

如果 AI agent 在报告中输出了 preview URL 作为 QA URL，该报告无效，必须重新完成 alias 步骤后再报告。

---

## Preview URL Policy

| 场景 | 允许 |
|------|------|
| 工程内部调试 | ✅ |
| 部署完成后 alias 之前的临时确认 | ✅ |
| Demo / 演示 | ❌ |
| Pilot / broker 测试 | ❌ |
| 文档 | ❌ |
| 截图说明 | ❌ |
| Release report | ❌ |

---

## Cursor / AI Agent Rule

当 Cursor 或任何 AI agent 执行 P16 部署时：

1. **可以**在内部使用 preview URL 确认 Vercel 部署成功。
2. **必须**在 QA 之前完成 alias（`vercel alias [preview] ui-smoky-beta.vercel.app`）。
3. **必须**针对稳定 QA URL 运行所有验证。
4. **不得**要求 Andy 去测试 preview URL。
5. **不得**在最终报告中出现 preview URL。
6. 如果遇到 preview URL 的 CORS 报错，不得通过白名单修复 — 必须执行 alias 步骤。

违反以上规则的部署报告视为不完整，需重跑 alias + QA 流程。

---

## Reason — 为什么这套规则重要

Preview URL 和稳定 QA URL 在 alias 完成后指向同一个 build，功能完全相同。  
区别只有一个：Cloud Run 的 `ALLOWED_ORIGINS` 白名单只包含稳定域名，不包含 preview 域名。

使用 preview URL 的后果：
- CORS 报错 → `Extraction failed: Failed to fetch`
- Pilot 用户页面无法使用
- 文档链接失效（每次重新部署 preview URL 都会变）
- 需要紧急修复（白名单 preview URL 或 alias）

使用稳定 QA URL 的结果：
- 零 CORS 问题
- 文档链接永久有效
- Pilot 用户始终访问最新 build
- 部署流程可重复、可预期

---

## CORS Maintenance Rule

`ui-smoky-beta.vercel.app` is permanently whitelisted in `ALLOWED_ORIGINS` on Cloud Run.  
Do not add preview URLs to `ALLOWED_ORIGINS`. If a preview URL needs CORS access,  
that is a signal the stable alias step was skipped — fix the process, not the whitelist.

Current `ALLOWED_ORIGINS` includes `ui-smoky-beta.vercel.app`.  
Cloud Run service: `fiqa-api`, region: `us-west1`, project: `optimal-disk-472305-e2`.

---

## A/B Testing Rule

Current state: single stable QA URL only.

Multiple public QA URLs are not allowed until:

- 20+ real pilot cases logged (CK-001 through CK-020)
- Measurable conversion metrics established
- Explicit decision recorded in `P16_DECISION_FREEZE_V1.md`

---

*Related: `docs/CURRENT_PRODUCT_SHAPE.md` · `docs/p16/P16_DECISION_FREEZE_V1.md` · `scripts/deploy_paid_pilot.sh`*
