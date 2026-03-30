# Validation, deploy, and manual testcase spec

## Simulation (rule path)

- **Primary script:** `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_na_chinese_20_case_sprint_battery.py`
- **Minimum scenario IDs to review:** S01 (happy path), S03 (微信发过了), S07 (太贵/换公司), S08 (还缺什么), S05 (配偶/多驾驶人)
- **Gate:** `bash scripts/guardrail_inbox_triage.sh` — expect PASS for release candidate.

## Deploy

| Surface | Documented command | Notes |
|--------|-------------------|--------|
| Frontend | `cd ui && vercel --prod` (see `docs/runbooks/DEPLOYMENT_PLAYBOOK.md`) | Confirm production alias points at latest deployment. |
| Backend | `bash scripts/deploy_rag_demo.sh` | Requires `.env.cloudrun`; may be long-running (image build + push). |

## Smoke checks (production)

1. `GET` Unified Intake page — HTTP 200, visible Add-Car chrome.  
2. `GET` `{API}/readyz` — `ok: true`, `intake_path_ready: true` (pilot stance: RAG clients may show not ready while intake is ready).  
3. `GET` `{API}/api/inbox/client-config?client=chen_kui` — JSON with `ui_copy`.  
4. `OPTIONS` `POST /api/inbox/triage` with `Origin: https://ui-smoky-beta.vercel.app` — 200.  
5. `POST /api/inbox/triage` with short Add-Car body — 200, expected triage fields present.

## Manual test cases (founder)

Each case: **title**, **first message**, **optional second message**, **what to watch**, **good**, **failure**.  
Style: realistic North-American Chinese Add-Car utterances; copy-paste friendly.

## Evidence discipline

Record: commands, URLs, HTTP outcomes, and whether backend **redeploy** was observed end-to-end or only **pre-existing** production was probed.
