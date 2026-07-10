# P19H-3i — Claim Task Dashboard Manual WeCom Retest Checklist

**Date:** 2026-07-10  
**Backend:** `e61e12e28` / `fiqa-api-00199-5c9`  
**Frontend:** `https://ui-smoky-beta.vercel.app`  
**Feature commit:** `7ac5362` (deployed via `e61e12e`)

---

## A. Existing submitted Claim: progress

Send in real WeCom test account:

```
进度
```

Expected:

- [ ] Reply shows current Claim status
- [ ] Status: **已提交给陈总审核** / **等待陈总查看**
- [ ] Includes button/link: **继续补充事故资料**
- [ ] Does **not** start a new Claim
- [ ] Does **not** ask Add Car fields

---

## B. Recover H5 link commands

Send each separately:

```
补资料
链接
事故资料
继续填写
```

Expected:

- [ ] All return same active Claim H5 link (or valid task link)
- [ ] Copy is about continuing/supplementing the current accident
- [ ] No new Claim
- [ ] No Add Car prompt

---

## C. Open H5 Dashboard

Click H5 link from WeCom.

Expected:

- [ ] Top section title: **我的事故资料**
- [ ] Shows **已收到** / **还缺** / **下一步**
- [ ] If already submitted: **资料已提交给陈总审核**
- [ ] Subtitle allows continued supplement / upload
- [ ] Wizard still visible below dashboard

---

## D. Text supplement (insurance)

Send:

```
对方保险是 State Farm
```

Expected:

- [ ] Reply: **已记录到您当前的事故记录里**
- [ ] Includes H5 link or clear way to open H5
- [ ] Mentions customer text supplement / **陈总会查看**
- [ ] Workbench timeline shows raw text
- [ ] Known facts show State Farm (label **客户文字补充** if provenance visible)

---

## E. Plate supplement

Send:

```
补充一下，对方车牌是 ABC123
```

Expected:

- [ ] Reply: **已记录到当前事故**
- [ ] Includes H5 link
- [ ] Does **NOT** ask: 提车日期 / 停放 ZIP / 联系电话
- [ ] Workbench shows ABC123 + timeline raw text

---

## F. Photo supplement

Send a photo.

Expected:

- [ ] Photo attached to current Claim
- [ ] Reply says photo **已收到**
- [ ] Reply mentions **进度** or **链接** to open H5 (inline URL optional)
- [ ] Workbench shows photo in attachments/timeline

---

## G. Explicit Add Car

Send:

```
我要加车
```

Expected:

- [ ] Add Car path still works (explicit intent allowed)

---

## H. Broker Workbench

Open Workbench for the test case.

Expected:

- [ ] Case visible
- [ ] Dashboard facts visible
- [ ] Customer display name visible
- [ ] Timeline shows raw supplement texts
- [ ] `broker_done` remains manual only

---

## Notes

- Live automated smoke: `docs/evidence/p19h3i_claim_task_dashboard_smoke_3i_smoke_224257.json` (**PASS**)
- H5 intake regression smoke: `docs/evidence/p19h3h_claim_h5_intake_smoke_3h_smoke_223843.json` (**PASS**)
