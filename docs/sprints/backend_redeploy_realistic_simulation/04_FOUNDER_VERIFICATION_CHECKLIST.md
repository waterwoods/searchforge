# Founder Verification Checklist — Backend Redeploy

**Use this after deployment to verify the realistic simulation fixes are live.**

## Quick Test (Production API)

**Backend URL:** `https://fiqa-api-1013093472160.us-west1.run.app`

### 1. 找陈奎 (Talk to Agent shorthand)
```bash
curl -s -X POST "https://fiqa-api-1013093472160.us-west1.run.app/api/inbox/triage" \
  -H "Content-Type: application/json" \
  -d '{"text": "找陈奎"}' | jq '.issue_category, .urgency, .handoff_ready'
```
**Expected:** `"customer_requested_human"`, `"medium"`, `true`

### 2. 急死了 保单要停了 (Cancellation urgency)
```bash
curl -s -X POST "https://fiqa-api-1013093472160.us-west1.run.app/api/inbox/triage" \
  -H "Content-Type: application/json" \
  -d '{"text": "急死了 保单要停了"}' | jq '.issue_category, .urgency'
```
**Expected:** `"cancellation_warning"`, `"critical"`

### 3. 联系人工 (Existing Talk to Agent)
```bash
curl -s -X POST "https://fiqa-api-1013093472160.us-west1.run.app/api/inbox/triage" \
  -H "Content-Type: application/json" \
  -d '{"text": "联系人工"}' | jq '.issue_category, .handoff_ready'
```
**Expected:** `"customer_requested_human"`, `true`

## Frontend Smoke Test

1. Open Unified Intake: `https://<vercel>/workbench/unified-intake`
2. Paste "找陈奎" → should show handoff-ready, 联系人工
3. Paste "急死了 保单要停了" → should show 付款/账单, critical

## Pass/Fail

- [ ] Scenario 1 passed
- [ ] Scenario 2 passed
- [ ] Scenario 3 passed
- [ ] Frontend smoke passed (optional)
