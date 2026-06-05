# Wu Miss Demo Script — P16 Add-Car (5 minutes)

**Audience:** Wu Miss (supervised) + founder narrates value  
**URL:** https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake  
**Pre-flight:** `bash scripts/reset_p16_supervised_demo.sh` (or incognito + reset per Part 0)

**30-second value line (founder says first):**
> 客户微信发来乱消息 → 系统自动整理成办公室能用的 case → 经纪人核对后再联系客户。一个客户同时只有一个进行中的 case。

---

## Part 0 — Reset (30 sec, before demo)

1. Open URL in **incognito** (or run reset script).
2. Confirm **three primary tabs** visible: **客户报送 · 办公室工作台 · 场景仿真** (requires Preview build with `VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1`; local dev shows four tabs including 我的办理 unless both product flags are set).
3. Default landing tab is **客户报送**. **我的办理** is under 客户报送 →「查看我的办理」.
4. Founder: "今天演示加车报价，客户报 → 办公室整理 → 您确认后联系。"

---

## Part 1 — AC03 Missing VIN (~90 sec)

**Story:** Customer bought Honda but VIN not ready — broker cannot quote yet.

| Step | Who | Action |
|------|-----|--------|
| 1 | Wu Miss | Tab **客户报送** |
| 2 | Wu Miss | Click **办理加车报价** (or paste in message box) |
| 3 | Wu Miss | Send turn 1: `你好，我新买了2022 Honda Accord，想加保。` |
| 4 | Wu Miss | Send turn 2: `邮编92618，这周六提车，主驾是我。VIN我晚点拍给你可以吗？` |
| 5 | Founder | Point to: **2022 Honda Accord** recognized, **还缺 车架号**, checklist visible |
| 6 | Founder | Tab **办公室工作台** → open same case → **下一步** shows Chinese: `联系客户补齐车架号、提车日期，然后出报价` |
| 7 | Founder | "VIN 没齐不能继续报价 — 系统在帮办公室列缺口，不是乱猜。" |

**Expected:** Vehicle extracted; VIN in still-needed; handoff **not** ready; broker next step Chinese; no fake completed case.

**Do NOT:** Force persist as "done" or skip VIN gap.

---

## Part 2 — AC05 Full Lifecycle (~2 min)

**Story:** Tesla add-car with insurance card mention — full customer → broker → return → append.

| Step | Who | Action |
|------|-----|--------|
| 1 | Reset | Incognito or `bash scripts/reset_p16_supervised_demo.sh` |
| 2 | Wu Miss | **客户报送** → turn 1: `我买了台2024 Tesla Model Y，想加到保单。` |
| 3 | Wu Miss | turn 2: `刚才微信发了现有保险卡照片，你们收到了吗？` |
| 4 | Wu Miss | turn 3: `VIN 7SAYGDEE5PA123456，邮编90024，下周三提车，我开。` |
| 5 | Wu Miss | Complete formal submit to office when prompted |
| 6 | Founder | **办公室工作台** → case title `客户咨询加车报价`, vehicle **2024 Tesla Model Y**, next step Chinese (name/phone if still needed) |
| 7 | Wu Miss | Close tab / simulate "return later" |
| 8 | Wu Miss | **客户报送** →「查看我的办理」→ continue same active case |
| 9 | Wu Miss | Append: `我叫李华，手机626-555-0199` |
| 10 | Founder | Same case ID; timeline shows append; broker step updates |

**Expected:** One active case; Chinese broker step; materials signal acknowledged; lifecycle visible on return.

**Founder explains:** "客户不用重复讲故事 — 同一条服务记录追加就行。"

---

## Part 3 — AC07 Teen Driver (~90 sec)

**Story:** English teen-driver add-car — complex but structured.

| Step | Who | Action |
|------|-----|--------|
| 1 | Reset | Fresh session |
| 2 | Wu Miss | **客户报送** → turn 1: `Adding a 2021 Honda Civic for my son who just got his license.` |
| 3 | Wu Miss | turn 2: `He's 17, primary driver. VIN 2HGFC2F59MH123456, ZIP 92801, car already in driveway.` |
| 4 | Wu Miss | Submit to office |
| 5 | Founder | **办公室工作台** → **2021 Honda Civic**, teen driver captured, next step Chinese e.g. `联系客户补齐提车日期、姓名、电话，然后出报价` |
| 6 | Founder | "英文客户消息一样整理成中文办公室步骤 — 陈魁团队看得懂。" |

**Expected:** `add_car` route; primary_driver captured; Chinese office next step (not English `Run quote…`).

---

## If something breaks

| Symptom | Fallback |
|---------|----------|
| Empty queue / network error | Hard refresh; confirm waterwoods URL; check founder logged-in API key in Preview env |
| English broker step | Hard refresh after backend deploy; UI synthesizes Chinese from still-needed as fallback |
| Customer tab missing | Use local `http://localhost:5173/workbench/unified-intake` or redeploy Preview with `VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1` |
| SSO/login wall | Do not use hash-only deploy URLs; use waterwoods alias |

---

*End — total ≤ 5 minutes with founder pacing.*
