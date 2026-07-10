# P19H-3h-1G — Append-first, Split-later Manual WeCom Checklist

**Date:** 2026-07-10  
**Policy:** Append-first, Split-later (先归档，后拆分)  
**Backend deployed:** `a119bb247` · `fiqa-api-00195-9lz`  
**Prerequisite:** P19H-3h-1F append-first patch live on pilot backend  
**Environment:** Chen pilot WeCom KF

---

## Pre-check

- [ ] Backend revision `fiqa-api-00195-9lz` (GIT_SHA `a119bb247`) serving 100% traffic
- [ ] Claim H5 MVP frontend live at `https://ui-smoky-beta.vercel.app`
- [ ] Broker Workbench accessible for timeline verification

---

## Manual WeCom test

### 1. Send: 我要理赔

**Expected:**
- Start Card should show H5 Claim intake link.
- It should **not** show legacy injury menu as the primary path.

| Pass |
|------|
| |

### 2. Click H5 link

**Expected:**
- H5 Claim page opens.
- Steps are clear.

| Pass |
|------|
| |

### 3. Return to WeCom and send ordinary narrative

Send: `昨天在 Santa Ana 红绿灯被追尾，对方是 State Farm。`

**Expected:**
- It should append to current Claim.
- It should **NOT** ask「继续当前事故还是开始新事故」.

| Pass |
|------|
| |

### 4. Send supplement

Send: `补充一下，对方车牌是 ABC123。`

**Expected:**
- Append to current Claim.
- No new-case confirm.

| Pass |
|------|
| |

### 5. Send status request

Send: `进度`

**Expected:**
- Status Card appears.
- If H5 not submitted, it includes H5 continue link.
- If H5 submitted, no incorrect continue link.

| Pass |
|------|
| |

### 6. Send explicit new accident

Send: `这是另一个事故，不是刚才那个。`

**Expected:**
- It may trigger explicit new accident confirm or broker warning.
- This is the **rare exception** — not the default for ordinary supplements.

| Pass |
|------|
| |

### 7. Open Broker Workbench

**Expected:**
- One current Claim row is visible.
- Timeline contains H5/task/chat supplements.
- No duplicate claim created for ordinary supplements.
- `possible_multi_claim_context` or similar broker flag appears only if relevant.
- `broker_done` remains manual.

| Pass |
|------|
| |

---

## Regression guards

- [ ] Lane switch (Add Car → Claim) still shows confirm; H5 Start Card on confirm
- [ ] Broker Done End Card unchanged
- [ ] Legacy injury quick-reply still works on legacy cases
- [ ] Random photo before Claim start still hidden (no silent case create)

---

## Sign-off

| Role | Name | Date | GO/HOLD |
|------|------|------|---------|
| Engineer | | | |
| Founder | Andy | | |

**Notes:**
