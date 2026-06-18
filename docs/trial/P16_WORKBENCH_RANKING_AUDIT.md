# P16 Workbench Ranking Audit

**Case under investigation:** `case_ea74d66fa3ba` (2024 Tesla Model Y, formal submit)

---

## Functions inspected

| Function | File | Role |
|----------|------|------|
| `orderCasesForWorkbench()` | `ui/src/features/intake/utils/intakePure.ts` | Client-side re-sort after API fetch |
| `getCaseWorkbenchScore()` | same | Priority score from attention + urgency |
| `getCaseAttentionState()` | same | Maps case → action vs tracking |
| `loadRecent()` | `BrokerWorkbenchTab.tsx` | Fetches page, then `orderCasesForWorkbench(cases)` |

---

## Why server #1 became UI #12

### Step 1 — API returns newest first

`list_recent_cases_for_read()` / Postgres `list_record_ids_recent` orders by **`updated_at` DESC**.  
Fresh formal submit is **#1** on the wire.

### Step 2 — UI replaces server order

```typescript
const ordered = orderCasesForWorkbench(cases);
setRecentCases(ordered);
```

Sort comparator: higher `getCaseWorkbenchScore()` wins; tie → newer `updated_at`.

### Step 3 — Score breakdown for `case_ea74d66fa3ba` (before fix)

| Field | Value | Score effect |
|-------|-------|--------------|
| `lifecycle_status` | `handed_off` | None in score fn |
| `formal_submitted_at` | recent | **Not used (gap)** |
| `waiting_on` | `none` | Tracking / parked |
| `next_contact_by` | empty | No due-today bonus |
| `manual_followup_needed` | false | No action bump |
| `urgency` | medium | +8 |
| **Total** | | **8** |

Attention label: **暂存** (parked) — correct for office semantics, fatal for queue rank.

### Step 4 — Demo / action cases above it

Founder demo seeds (and similar action cases) typically have:

- `waiting_on: broker` → +50 on action base (+100)
- `next_contact_by: today` → +60
- `urgency: high` → +15  
- **Total ≈ 175**

Roughly **11 cases** in the loaded page scored **150–175**, pushing the Tesla submit to **UI #12** while API rank stayed **#1**.

---

## UI_QUEUE_SCOPE_ISSUE (ranking aspect)

- Re-sort applies to **entire loaded page** (50 cases) with no “recent customer submit” lane.
- Product-only mode renders one flat list — demotion equals scroll distance.
- `formal_submitted_at` was displayed on cards (non–product-only) but **not in score**.

---

## After-fix score model (same case)

| Component | Points |
|-----------|--------|
| Attention (parked) | 0 |
| Urgency medium | +8 |
| Recent formal submission boost (`handed_off` + `<24h`) | **+165** |
| Founder demo penalty | 0 (real customer text) |
| **Total** | **173** |

**Simulated ranks:**

| Queue mix | UI rank |
|-----------|---------|
| Demo seeds only (12) | **#1** |
| Demos + urgent cancel/payment (pilot-realistic) | **#7** (first screen) |

Urgent same-day cancellation / high payment-fail (175–180) remain above fresh add-car — **no workflow regression**.

---

## Audit conclusion

| Question | Answer |
|----------|--------|
| Root cause confirmed? | **Yes** — client score ignores recent formal submit; demo action scores dominate |
| API/DB defect? | **No** |
| Minimal fix path? | Score boost + demo deprioritization + product-only card fields |
