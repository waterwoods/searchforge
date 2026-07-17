# P20 Founder Form Gate + Start Claim Submit Fix — Finalization

**Date:** 2026-07-16  
**Verdict:** CONDITIONAL
**Release:** NO — pending manual Founder Form QA (physical device)  
**Capability 4 started:** NO

## Root cause (retained regression record)

The Mini Program Start Claim **提交给陈总** CTA stayed disabled even though all
Business Contract Must Have fields were filled.

Cause: hidden artificial minimum-length gates in `computeCanSubmit`:

- `description.trim().length >= 10`
- `accidentLocation.trim().length >= 3`

Founder live values failed both with no visible explanation:

- `被车后装` = 4 chars (< 10)
- `路口` = 2 chars (< 3)

These thresholds were engineering leftovers, not Business Contract rules. The
Business Contract requires Must Have fields to be **non-empty**, not a minimum
length. This is the exact class of failure the Founder Form Gate now blocks.

## Corrected Start Claim contract

Required (enables CTA):

- accident description — non-empty
- accident date/time — non-empty broker-readable text (`Today 9 am`, `今天上午 9 点`, `2026-07-16 09:00`)
- accident location — non-empty
- injury — `yes` / `no` / `unknown` (`没有受伤` → canonical `no`)
- contact — only when reachability is not already known (Mini Program session is known → not required)

Never blocks submit: VIN, vehicle information, insurance card, photos, police,
other driver, any Request More field.

## Founder Form Gate (permanent)

- **SSOT:** `docs/product/p20_product_north_star.md` §I "Founder Form Gate"
- **References (no conflicting copies):**
  - `AGENTS.md` — mandatory P20 behavior (enforce §I when a form changes)
  - `docs/product/p20_production_loop_template.md` — hard-gate + quick-check list
  - this evidence doc — regression origin + QA steps
- **Permanent checks:** visible = canonical; independent required fields;
  complete → enabled; optional never blocks; no hidden rule without contract +
  visible reason; submit validates + shows first invalid; disabled CTA is not
  the only signal; normalized payload; single-flight; downstream visible;
  DevTools + device smoke; user-completable without Cursor guidance.

## Tests

| Suite | Result |
|---|---|
| `miniapp/tests/startClaimValidation.test.ts` (new) | PASS |
| `miniapp/tests/startClaimPage.test.ts` (extended) | PASS |
| All Mini Program tests | 210/210 PASS |
| Component gates | PASS |
| Preview preflight | PASS |
| `tests/test_p20_customer_start_claim.py` | PASS |
| `tests/test_p20_mvp_request_gating.py` | PASS |
| `tests/test_p20_case_intake_command_service.py` | PASS |
| `git diff --check` | PASS |

## Mini Program Preview

| Item | Value |
|---|---|
| AppID | `wxa610932351416622` |
| apiProfile | `qa` |
| API base | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Component gates | PASS |
| Preview preflight | PASS |

## Founder phone QA steps (max 10)

1. Open `miniapp/` in WeChat DevTools; confirm AppID `wxa610932351416622` and `apiProfile=qa`.
2. 清缓存 → 全部清除.
3. 重新编译.
4. Click **Preview**; scan the QR with iPhone WeChat.
5. Fill 事故经过: `被车后装`.
6. Fill 事故时间: `Today 9 am`; 事故地点: `路口`; select 没有受伤.
7. Confirm **提交给陈总** becomes enabled (and incomplete forms show what is missing).
8. Tap once; confirm loading closes and the success receipt appears.
9. Open Workbench `https://ui-smoky-beta.vercel.app/workbench/document-intake`.
10. Confirm exactly one new Draft Claim; find it by the description/time below.

## Human-readable claim to find

- **Description:** `被车后装`
- **Time:** `Today 9 am`
- **Location:** `路口`
- **Injury:** 没有受伤 (no)

No raw case ID required.

## Remaining blockers

- WeChat admin proof that request 合法域名 includes
  `fiqa-api-g7zatxrycq-uw.a.run.app` is not recorded in the repository.
- Manual physical-device Founder Form + Navigation QA and authoritative
  downstream exactly-one verification remain required before Release.

## Reliability Gate re-audit addendum

### Defect class and root cause

The original state/payload fix passed, but failure classification and invalid
submit recovery were not yet complete:

- `miniapp/utils/startClaimLifecycle.ts::mapStartClaimError` grouped the API
  health preflight failure with generic transport, grouped auth/config failures
  with 4xx validation, and offered blind retry for server validation.
- The timeout message promised `不会重复创建` before physical downstream
  exactly-one evidence existed.
- `miniapp/pages/start-claim/start-claim.ts::_focusFirstInvalid` showed a toast
  but did not focus or scroll to the invalid field.
- `buildStartClaimPayload` trimmed values without first writing the normalized
  values back to the canonical/rendered model, so whitespace-normalized payload
  text could differ from the value still bound to the visible control.
- `miniapp/utils/requestErrors.ts::buildRequestDiagnostic` recorded duration but
  omitted the required request start/end timestamps.

Prior tests checked generic transport/domain/timeout and visible errors, but did
not assert not-sent vs auth/config classification, retry safety, actual invalid
field scrolling, visible/canonical/payload equality after normalization, or
timestamp completeness.

### Permanent gate strengthened

North Star §I now explicitly requires:

- invalid submit skips API and focuses/scrolls the first invalid field;
- typed not-sent, transport, DNS/domain/TLS, timeout, auth/config, 4xx, and 5xx
  handling with safe retry;
- safe device diagnostics with timestamps and command identity; and
- no unverified no-duplicate promise.

The Production Loop quick check references these same SSOT rules.

### Re-audit test evidence

- All Mini Program tests: **235/235 PASS**
- Component completeness / usingComponents path-case-existence /
  app.json registration: **PASS**
- Preview preflight: **PASS**
- Focused backend Start Claim / command idempotency / MVP gating:
  **17/17 PASS**
- IDE lint diagnostics: **PASS**
- `git diff --check`: **PASS**
- QA API `/health`: **HTTP 200**, TLS verification result **0**

### Configuration status

- AppID: `wxa610932351416622` — confirmed in `miniapp/project.config.json`
- apiProfile: `qa` — confirmed by Preview preflight
- API base: `https://fiqa-api-g7zatxrycq-uw.a.run.app` — confirmed
- TLS: valid from this environment (`curl` verify result 0)
- launch token: empty; Start Claim does not require a stale task token
- compile condition: `condition: {}` in project config
- legal domain: **UNVERIFIED in WeChat admin**
- clean cache / full compile / current Preview: **physical QA action required**
