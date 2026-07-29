# Chen Demo Invite — Physical Phone Entry (T4)

**Branch:** `demo/known-customer-invite-overlay`  
**Experience build name:** `0.3.0-chen-demo`  
**Do not:** invent a decorative QR WeChat cannot open; retarget waterwoods before Founder phone QA.

## Why there is no scannable WeChat QR yet

| Mechanism | Status |
|-----------|--------|
| `wxacode.getUnlimited` (native Mini Program QR) | **Not wired** in this codebase |
| HTTPS claim-task deep link QR | Exists for Request More tokens — **not** for Demo Invite `dit=` |
| T3/T4 entry payload | `pages/start-claim/start-claim?entry=form&dit=<opaque>` |

Until wxacode / URL Link is configured, **Experience Preview + compile query** is the supported physical path.

## Fastest real method (Chen Demo day)

### A. Operator (laptop)

1. Open QA Preview Document Intake (T3 Preview or newer):  
   `…/workbench/document-intake`
2. Open **陈总演示工具** → select 陈明 / 李娜 / 王先生 → **生成演示入口**
3. Copy **入口路径** (includes `entry=form&dit=…`)
4. If Active Case warning appears on the phone identity, **重置演示** + QA Console Fresh before switching scenarios

### B. Phone (WeChat Experience / Preview)

1. In WeChat DevTools (same AppID as QA):
   - `apiProfile: "qa"` in gitignored `config.local.ts`
   - Clear cache → **Full compile**
   - Upload Experience Version named **`0.3.0-chen-demo`**
2. On the phone: open that Experience Version
3. In DevTools **编译模式** (or Preview launch params), set path/query to the copied entry, e.g.  
   `pages/start-claim/start-claim?entry=form&dit=di_…`  
   Or use **预览** with custom compile condition carrying the same query
4. Phone opens Start Claim → redeems `dit` → shows mock chips → complete Story → Card → Photos → Receipt

### C. Second phone / second scenario

1. Reset + clear Active Case for that wx identity (support flow)
2. Generate a new invite for the other fixture
3. Open Experience again with the new `dit=`

## What Andy and Chen should do

| Role | Action |
|------|--------|
| Andy (laptop) | Generate invite in 陈总演示工具; watch Workbench for named demo case |
| Chen (phone) | Open Experience `0.3.0-chen-demo` with the compiled `dit` query; finish claim; later Continue for Request More |

## Backend prerequisites (QA only)

- `CHEN_DEMO_INVITE_ENABLED=1` on `fiqa-api-qa`
- Demo window: Cloud Run **min=1, max=1** (process-local invite store)
- Do **not** enable Production flags / Production service

## After Founder phone QA PASS

Only then consider retargeting waterwoods and restoring Cloud Run scale (min=0, max=2).
