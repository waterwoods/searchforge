# P26G — Default Intake Tasks & Persistent Customer Resume

**Date:** 2026-07-18  
**Mode:** Production Loop — flow contract repair only  
**Verdict:** **GO FOR QA** (code + automated gates). Founder device QA required before FOUNDER FLOW COMPLETE.

## One objective

A new customer claim exposes Constitution default intake tasks immediately, without Broker Request More / a second QR, and can return later via a server-validated resume token to the same active case.

## Explicitly out of scope

- P26B Voice Story  
- P26C Guided Photos  
- Lightweight account landing page / case-history UI  
- Task Home redesign  

## Root cause (proven)

1. **Access gate:** `issue_customer_launch_token` only ran from Send Request / Request More. Customer Start Claim returned `{ok:true}` with no resume token (`customer_start_claim_response` stripped `case_id`). Mini Program resume = `mp_prototype_resume_token` set only after Entry opened with a launch token → QR required.
2. **Phase gate:** `_build_new_case_record` set `claim_phase=broker_review` for all creates. Constitution `_customer_today` / `_is_waiting_broker` collapsed to「先不用操作」when no Slice1 action.
3. **Insurance actionability gate:** `_has_open_insurance_path` required a Slice1 open request. Request-item submit required `request_item_id`. Cap2 checklist classed insurance as `request_more`.

## Architecture decision

| Layer | Owner |
|-------|--------|
| Default plan SSOT | `default_intake_plan.py` |
| Merge + Today / states | Constitution (`constitution_projection.py`) + `task_source` |
| Broker follow-ups | Slice1 open request (`broker_requested`) |
| Resume | Signed H5 intake token issued on customer Start Claim; client persists; Entry validates via server |

## Verification

| Check | Result |
|-------|--------|
| `tests/test_p26g_default_intake_and_resume.py` | **PASS** |
| `tests/test_constitution_projection_customer_tasks.py` | **PASS** |
| `tests/test_constitution_projection_api.py` | **PASS** |
| `tests/test_p20_customer_start_claim.py` | **PASS** |
| `tests/test_p20_send_request_command_service.py` | **PASS** |
| `tests/test_p20_slice1_e2e.py` | **PASS** |
| miniapp startClaim / Entry / task cards / photos | **PASS** |
| `cd miniapp && npm run build:gate` | **PASS** |

## Founder QA (device) — required

1. Fresh Start Claim → immediately see default tasks (no Chen Kui Request More)  
2. Complete tasks in reasonable order  
3. Exit mini program → reopen without new QR → same Task Home  
4. Broker adds one exceptional follow-up → added without resetting claim  

**Do not declare FOUNDER FLOW COMPLETE until the above passes on device.**

## STOP

Do not begin P26B / P26C / account landing / case history.
