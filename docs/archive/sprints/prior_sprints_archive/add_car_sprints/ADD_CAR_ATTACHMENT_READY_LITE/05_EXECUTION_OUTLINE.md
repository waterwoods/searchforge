# Execution Outline

**Sprint:** Add-Car Attachment-Ready Lite  
**Purpose:** Workstreams, implementation order, simulation plan, deployment approach.

---

## 1. Workstreams

| Workstream | Owner | Scope |
|------------|-------|-------|
| Backend case/state | Backend | case_attachments in case_store; add_attachment, list attachments |
| API upload | Backend | POST /api/inbox/cases/{id}/attachments |
| Workbench visibility | Frontend | Attachment badge, list, still-needed copy |
| Add-car simulations | QA | Attachment-ready scenarios in simulation pack |

---

## 2. Implementation Order

1. **Loop 1:** Minimal attachment-ready structure
   - case_attachments schema in case_store
   - add_attachment_to_case, get_case_attachments
   - POST /api/inbox/cases/{id}/attachments (multipart)
   - File storage: data/unified_intake_attachments/{case_id}/

2. **Loop 2:** Broker attachment visibility
   - UI: attachment badge on case card
   - UI: attachment list in case detail
   - still_needed copy when no attachment
   - broker_next_step augmentation when attachment present

3. **Loop 3:** Add-car attachment simulations
   - MT_add_car_vehicle_first_attachment_later
   - MT_add_car_quote_ready_no_attachment
   - MT_add_car_quote_ready_plus_attachment
   - MT_add_car_attachment_optional

---

## 3. Simulation / Validation Plan

- Run `bash scripts/guardrail_inbox_triage.sh`
- Run `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
- Add add-car attachment scenarios to config
- Manual: create add-car case, upload file, verify workbench display

---

## 4. Deployment Approach

- **Backend:** Redeploy if case_store or routes change
- **Frontend:** Redeploy if UnifiedIntakePage changes
- **Data:** case_attachments stored in case JSON; files on disk (local) or object storage (prod)

---

*See also: 06_ACCEPTANCE_ATTACHMENT_READY_CRITERIA.md*

---

## Loop 3: Attachment API Test

When server is running on 8001:
```bash
# Create case, upload, verify (requires httpx)
PYTHONPATH=. python3 -c "
import httpx
r = httpx.post('http://localhost:8001/api/inbox/triage', json={'text':'我想加2024 Tesla 90210下周提车','persist_case':True}, timeout=15)
cid = r.json().get('case_id')
if cid:
    f = {'file': ('reg.png', b'fake_png_content', 'image/png')}
    r2 = httpx.post(f'http://localhost:8001/api/inbox/cases/{cid}/attachments', files=f, timeout=15)
    print('Upload:', r2.status_code, r2.json().get('case_attachments'))
"
```
