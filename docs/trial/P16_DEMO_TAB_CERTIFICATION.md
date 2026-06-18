# P16 Demo Tab Certification — RESTORE-DEMO-TABS-SPRINT

**Date:** 2026-06-06  
**URL:** `https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake`  
**Deployment:** `dpl_2tzhtecntoYKBRwa7BTfoSVVRThd` · `index-CEY2l3TS.js`

---

## Tab restoration certification

| Check | Method | Result |
|-------|--------|--------|
| 客户报送 tab visible | Browser snapshot | ✅ |
| 办公室工作台 tab visible | Browser snapshot | ✅ |
| 场景仿真 tab visible | Browser snapshot | ✅ |
| Default tab = 客户报送 | Browser snapshot + title | ✅ |
| Office Visibility workbench intact | Click 办公室工作台 → paste + demo queue + cards | ✅ |
| 我的办理 not a top tab | Browser snapshot | ✅ (supervised mode) |
| API queue loads (no 401) | Workbench shows case cards + Copy buttons | ✅ |

---

## Acceptance case simulation (AC03 / AC05 / AC07)

**Command:** `PYTHONPATH=. LLM_GENERATION_ENABLED=0 python3 scripts/run_p16z24_add_car_sprint.py`  
**Timestamp:** 2026-06-06T14:19:38Z (fresh run this sprint)

These cases exercise **triage backend** only. Tab visibility is a **frontend build-flag** concern and does not alter triage paths. Re-run confirms no regression from tab-restoration deploy.

| Case | Title | service_type | case_quality | Verdict |
|------|-------|--------------|--------------|---------|
| **AC03** | VIN缺失 · Honda · 中文 | `add_car` | 100 | **PASS** |
| **AC05** | 保险卡已上传 · Tesla | `add_car` | 100 | **PASS** |
| **AC07** | Teen driver · Honda · English | `add_car` | 100 | **PASS** |

### AC03 highlights

- Collected: year, make_model, zip, primary_driver
- Still needed: vin, delivery_date
- Office step: 联系客户补齐车架号、提车日期，然后出报价

### AC05 highlights

- 3-turn conversation; insurance card signal preserved
- Collected: year, make_model, vin, zip, delivery_date, primary_driver, materials
- Office step: 联系客户补齐姓名、电话，然后出报价

### AC07 highlights

- English teen-driver thread routes `add_car` on turn 2
- Collected: year, make_model, vin, zip, primary_driver (teen)
- Office step: 联系客户补齐提车日期、姓名、电话，然后出报价

---

## Office Visibility regression check

Compared to pre-fix deployment (`index-DMOKMAa_.js`):

| Office Visibility feature | Still present after tab fix? |
|---------------------------|----------------------------|
| Product-only queue cards | ✅ |
| Vehicle summary on cards | ✅ |
| 办公室侧下一步 | ✅ (via live queue) |
| Paste-first workbench layout | ✅ |
| Demo queue / practice scenarios | ✅ |
| Engineer chrome hidden | ✅ (`productOnlyUi` still true) |

---

## GO / NO GO

| Criterion | Status |
|-----------|--------|
| 3 tabs restored on Waterwoods | ✅ |
| Office Visibility preserved | ✅ |
| AC03 / AC05 / AC07 pass | ✅ |
| Deploy alias updated | ✅ |

### **Verdict: GO**

Waterwoods Preview is certified for supervised demo (Wu Miss script) with full 3-tab layout and unchanged triage acceptance.

---

## Remaining risk

| Risk | Mitigation |
|------|------------|
| Future redeploy omits `SUPERVISED_DEMO=1` | Persist both flags in Vercel Preview dashboard; add deploy checklist line |
| Production still single-tab | Expected until separate prod promotion decision |
