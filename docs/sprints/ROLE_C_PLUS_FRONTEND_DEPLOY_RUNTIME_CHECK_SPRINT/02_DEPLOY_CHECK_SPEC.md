# Deploy & runtime check spec

## Frontend

| Step | Action |
|------|--------|
| Pre | `curl` production HTML; note main chunk filename under `/assets/index-*.js` |
| Check | `curl` that JS; count occurrences of `轻量多轮` and `逐轮快照` (expect ≥1 when Role C Plus is shipped) |
| Check | Same bundle: extract `fiqa-api*.run.app` — record canonical backend host |
| Deploy | From repo `ui/`: `vercel --prod` (per playbook) |
| Post | Re-run string checks; confirm alias `ui-smoky-beta.vercel.app` points at new deployment |

## Backend (read-only verification unless failing)

| Endpoint | Check |
|----------|--------|
| `POST /api/inbox/triage` | Add-car starter text; response includes `add_car_turn_intent` object when on Add-Car path |
| `POST /api/inbox/simulation-role-c-customer` | Valid body (`persona_id`, `difficulty`, `max_turns` 3–12, `conversation_turns`); expect 200 + `customer_message` or documented 503 if LLM disabled |

## When to redeploy backend

Only if live triage omits required fields for Role C Plus (`add_car_turn_intent` on Add-Car paths, normal triage shape) or simulation endpoint missing/500. This sprint found **no** such gap on the URL baked into Vercel production env.
