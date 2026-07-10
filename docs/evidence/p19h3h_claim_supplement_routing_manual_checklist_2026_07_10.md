# P19H-3h — Claim Supplement Routing Manual WeCom Checklist

**Date:** 2026-07-10  
**Deploy commit:** `fdba4b7` — fix: route Claim supplements away from Add Car Phase 2  
**Live backend:** https://fiqa-api-g7zatxrycq-uw.a.run.app  
**Revision:** `fiqa-api-00198-5sj`

Use a **WeCom test account** with an existing **submitted Claim** (intake submitted to broker). Optional: also have an open **Add Car Phase 2** case on the same external user to reproduce the original bug.

---

## 1. Plate supplement on submitted Claim

**Send:**

```
补充一下，对方车牌是 ABC123
```

**Expected:**

- Reply says the info was recorded on the **current accident / Claim** (e.g.「已记到您当前的事故记录里」).
- **Must NOT** ask for Add Car Phase 2 fields:
  - 提车日期
  - 停放 ZIP
  - 联系电话
- **Must NOT** create a new Add Car case.
- **Must NOT** show a new accident confirm card (「继续当前事故 / 开始新的事故记录」).

---

## 2. Insurance supplement

**Send:**

```
对方保险是 State Farm
```

**Expected:**

- Appends to the **same Claim** (supplement ack, not Phase 2 prompt).
- No Add Car lane switch unless user explicitly asks.

---

## 3. Status card unchanged

**Send:**

```
进度
```

**Expected:**

- Status card shows **current Claim** status.
- No Add Car Phase 2 missing-fields prompt mixed into the reply.

---

## 4. Explicit Add Car still works

**Send:**

```
我要加车
```

**Expected:**

- Routes to **Add Car** / lane-switch behavior (unchanged).
- Does not incorrectly treat as Claim supplement.

---

## 5. Broker Workbench readback

Open **Broker Workbench** for the test Claim.

**Expected:**

- Claim timeline contains the plate supplement event (ABC123).
- `known_facts` or summary includes **ABC123** if extractor supports it.
- `other_party_info` includes **State Farm** after step 2 if extractor supports it.
- **No duplicate Add Car case** created from Claim supplement messages.
- `broker_done` remains **manual** (not auto-set by supplement).

---

## Pass / fail

| Step | Pass | Notes |
|------|------|-------|
| 1 Plate supplement | ☐ | |
| 2 Insurance supplement | ☐ | |
| 3 Status card | ☐ | |
| 4 Explicit Add Car | ☐ | |
| 5 Workbench | ☐ | |

**Tester:** _____________ **Time (PT):** _____________
