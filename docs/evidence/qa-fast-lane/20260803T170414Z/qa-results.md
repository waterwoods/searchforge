# QA Fast Lane Results — 20260803T170414Z

Generated: 2026-08-03T17:04:17Z

| Step | Status | Detail |
|------|--------|--------|
| broker_discover | PASS | case_2f54f2227a96 |
| primary_status | PASS | queue='Customer completing default intake; Request More only if exceptional' header=None |
| request_more | PASS | http 201 |
| supplement_ack | SKIP | http 422: {'detail': {'outcome': 'rejected', 'command_id': 'ack-supp-19e9ffd734984773', 'correlation_id': 'ack-supp-19e9ffd734984773', 'idempotency_key': 'ack-supplement- |
| office_accept | PASS | first=200 second=200 |
| timeline | PASS | events=1 |
| screenshots | PASS | fallback_after_pw_error:html_snapshot http=200 |
| report | PASS | GO |

**Overall:** PASS (automated portion)
