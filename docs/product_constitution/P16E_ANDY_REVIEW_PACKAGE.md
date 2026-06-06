# P16-E Andy Review Package

**5-minute founder review — Sprint A on Vercel Preview**

---

## 1. Preview URL

https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app/workbench/unified-intake

You may need to **log in with Vercel** (Deployment Protection). Alternative: open while logged into Vercel dashboard → project `ui` → latest Preview deployment.

---

## 2. Click first

1. Confirm you land on **办公室工作台** (not 客户报送).
2. Read the **wayfinding banner** (paste WeChat here).
3. Click **加载演示队列** — wait for progress; cancellation case should open.
4. Click inline **取消/付款风险** — confirm text fills paste box.
5. Click **开始整理** once — confirm loading copy (~30s message).

---

## 3. Verify in 5 minutes

- [ ] Only 2 tabs: 客户报送 + 办公室工作台 (no 我的办理, no 场景仿真)
- [ ] No PG / 镜像异常 / debug chrome on workbench
- [ ] Paste placeholder says 原样粘贴微信
- [ ] Filters: 全部 / 需今天处理 / 24小时内 (after queue loads)
- [ ] API calls succeed (queue populates; no CORS error in DevTools)

---

## 4. Ignore

- ~1,360 dirty repo-root docs (not in this deploy)
- Production URL `ui-smoky-beta.vercel.app` — still pre-Sprint A
- Chunk size build warnings
- OpenAI 429 in local guardrail logs

---

## 5. Changed vs Production

| | Production | This Preview |
|--|------------|--------------|
| Env | No product_only | `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` |
| Default tab | 客户报送 | 办公室工作台 |
| Tabs | 4+ | 2 |
| Sprint A UX | No | Yes |

---

## 6. Still broken / risky

- Vercel login wall for brokers (not trial-ready URL yet)
- 5 uncommitted `ui/` files included in CLI deploy
- Add-Car tab suffix / header copy mismatch
- Demo queue not proven from your browser on this origin
- Saved Vercel Preview env still empty (must use `-b` flags on redeploy)

---

## 7. Approve merge?

**Not yet** — complete 5-minute checklist first. If checklist passes → merge `sprint-a/broker-front-door` to main is reasonable **after** cleaning `ui/` dirty files.

---

## 8. Approve Production deploy?

**NO** — Preview review only. Production needs merge + dashboard env vars + explicit founder gate.

---

*End of P16-E Andy Review Package*
