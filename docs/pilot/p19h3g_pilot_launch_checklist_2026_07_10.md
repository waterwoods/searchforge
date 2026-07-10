# P19H-3g — Chen Pilot Launch Checklist

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Production:** `a425fa461` · `fiqa-api-00190-989`  
**Demo script:** `docs/pilot/p19h3g_chen_demo_script_2026_07_10.md`

---

## Before pilot

### Environment & deploy

- [ ] Confirm Cloud Run revision: `curl -s https://fiqa-api-g7zatxrycq-uw.a.run.app/version` → `commit: a425fa461` (or newer on same branch)
- [ ] Confirm health: `/health/live` → 200, `/readyz` → 200, `intake_path_ready: true`
- [ ] Confirm **WeCom send env** on Cloud Run:
  - [ ] `WECOM_SLICE_SEND_REPLY=1` (or project equivalent)
  - [ ] Demo customer `external_userid` + `open_kf_id` bound
  - [ ] If send disabled: document **preview-only End Card** for demo day
- [ ] Confirm Workbench URL loads: https://ui-smoky-beta.vercel.app/workbench/unified-intake
- [ ] Confirm basic logging: Cloud Run logs accessible; no recurring claim-route 500s

### Data & demo hygiene

- [ ] **Clean demo/test users** — prefer fresh WeCom external user for scripted demo
- [ ] Optional QA seed refresh: `PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target qa`
- [ ] Remove or ignore stale `chen_kui_p18` rows if demo starts from Workbench list
- [ ] Prepare **customer disclaimer** ( verbal + card copy already in product ):
  - 「这只是事故资料记录，不代表已向保险公司正式报案」

### Operator readiness

- [ ] Run QA gate: `bash scripts/check_chen_kui_demo_environment.sh --cloud-api` (note seed FAIL is known non-core)
- [ ] Run claim pytest smoke:
  ```bash
  PYTHONPATH=. python3 -m pytest tests/test_p19h3f4_unified_status_card.py -q
  PYTHONPATH=. python3 -m pytest tests/test_p19h3f3_claim_collision_resolver.py -q
  PYTHONPATH=. python3 -m pytest tests/test_p19h3f2_true_end_card_on_broker_done.py -q
  ```
- [ ] **Prepare rollback command** (prior known-good revision):
  ```bash
  gcloud run services update-traffic fiqa-api \
    --region=us-west1 \
    --to-revisions=fiqa-api-00189-bmg=100
  ```
  (Adjust revision if newer rollback target documented in deploy evidence.)
- [ ] **Prepare Chen training note** — share demo script + 5-scene walkthrough
- [ ] Manual smoke: one full **WeCom → Workbench broker_done** on real device (HUMAN-PENDING in CI)

---

## During first week

### Daily tracking

| Metric | How to track |
|--------|----------------|
| Claims started | Count `claim_started` timeline events / new Claim rows |
| Status Card requests | WeCom logs + customer messages containing 进度/状态 |
| Collision Resolver triggers | `claim_collision_pending` set events |
| Broker Done count | `broker_done` timeline events |
| Errors / 500s | Cloud Run logs filter `severity>=ERROR` on `/api/inbox` |
| Chen feedback | `docs/trial/P16_BROKER_FEEDBACK.md` or observation log |

### Daily operator actions

- [ ] Morning: `/readyz` + Workbench opens
- [ ] Review any `claim_end_card_failed_v1` logs
- [ ] Confirm no raw inbound in default Workbench queue
- [ ] Collect Chen feedback (1–3 bullets): what saved time / what confused

---

## Success metrics

| Metric | Target |
|--------|--------|
| Chen understands case in <10 seconds | Brief + highlights sufficient on ≥80% of demo cases |
| Customer asks fewer repeated questions | Status Card reduces 「还要什么」follow-ups |
| No accidental Claim from random photo/text | Zero formal Claims without Start Ceremony |
| No mixed accident records | Collision Resolver used when 2+ accidents; no silent merge |
| broker_done closes collection cleanly | End Card sent (or preview + verbal); case leaves active queue |

---

## Stop conditions

**Stop pilot expansion and escalate immediately if:**

| Condition | Action |
|-----------|--------|
| Customer messages lost | Check WeCom ingest + Cloud SQL; rollback if regression |
| Wrong customer/case association | Stop demo; inspect `external_userid` binding |
| Repeated duplicate cases | Check msg_id dedup; file bug |
| Customer believes official claim was filed | Pause; reinforce disclaimer; review copy |
| Workbench cannot open formal Claim | Check API `/api/inbox/cases/{id}`; rollback if deploy issue |
| Claim-route 500s sustained | Rollback to prior revision; fix before resume |

---

## Rollback reference

| Item | Value |
|------|-------|
| Current production | `fiqa-api-00190-989` @ `a425fa461` |
| Prior revision (example) | `fiqa-api-00189-bmg` @ `e1aed6068` |
| Deploy script | `bash scripts/deploy_paid_pilot.sh` |
| Recovery (local) | `bash scripts/restore_8001_readiness.sh` |

---

## Related docs

- Audit: `docs/pilot/p19h3g_pilot_readiness_audit_chen_2026_07_10.md`
- Demo script: `docs/pilot/p19h3g_chen_demo_script_2026_07_10.md`
- Trial index: `docs/trial/INDEX.md`
- Founder path: `docs/FOUNDER_ONE_PATH.md`
