# Root cause and fix spec

## Symptoms

- User sees **Network Error** (often axios `error.message === "Network Error"`) when submitting Add-Car / customer message on the **deployed** HTTPS Vercel UI.
- Browser console may show failed XHR/fetch to API; sometimes CORS wording, often generic network failure.

## Suspected causes (pre-check)

| Hypothesis | Mechanism |
|------------|-----------|
| Missing `VITE_API_BASE_URL` on Vercel build | Production bundle uses empty `API_BASE_URL` → requests hit Vercel origin, not Cloud Run |
| `VITE_API_BASE_URL=http://localhost:...` baked into Vercel build | **Mixed content**: HTTPS page cannot call `http://localhost` → browser blocks → axios Network Error |
| Wrong Cloud Run URL | DNS / TLS / 404 on wrong service |
| `ALLOWED_ORIGINS` omitting real frontend origin | CORS preflight or response blocked → Network Error surface in axios |
| Backend down / timeout | Less common; usually visible as timeout or HTTP status |

## Actual confirmed cause (this sprint)

**Class of failure (configuration / build-time):** For production builds, `ui/src/api/config.ts` sets `API_BASE_URL` from `VITE_API_BASE_URL`. If that variable is **missing** or set to **`http://localhost` / `http://127.0.0.1`**, the browser on `https://*.vercel.app` **cannot** complete a successful call to the real Cloud Run API: either the request goes to the wrong host or **mixed-content** blocks it. That surfaces as axios **Network Error** (request failed, no usable response).

**Current production alias (`https://ui-smoky-beta.vercel.app`) — directly verified in this sprint:**

- Deployed JS bundle contains `https://fiqa-api-1013093472160.us-west1.run.app`.
- `OPTIONS` + `POST https://…/api/inbox/triage` from that origin return **200** with `access-control-allow-origin: https://ui-smoky-beta.vercel.app`.
- In-browser flow: **POST triage succeeded (200)** after Add-Car starter submit.

So: **the live production alias is not failing with Network Error at time of verification**; the sprint still addresses the **recurring misconfiguration class** and documents the alignment checks.

## Fix strategy

1. **Evidence:** curl + browser network log against production URLs.
2. **Prevention:** Fail **Vercel** production builds unless `VITE_API_BASE_URL` is a non-localhost **https://** URL, so a broken bundle cannot be deployed from CI.

## Acceptance criteria

- [x] Document symptoms vs confirmed vs inferred.
- [x] Confirm Cloud Run triage + CORS for production frontend origin.
- [x] Confirm current deployed bundle embeds correct HTTPS API base.
- [x] Local `npm run build` without `VERCEL=1` still succeeds.
- [x] `VERCEL=1` build without valid `VITE_API_BASE_URL` fails fast with a clear error.
