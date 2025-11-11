# Experiment Operations API Contract (v1)

This document defines the explicit contract for the experiment operations API. It covers the versioned endpoints exposed under `/api/v1/experiment/*`, the legacy aliases under `/api/experiment/*`, request and response shapes, error semantics, timeouts, and example usage.

## Endpoint Matrix

| Method | Path | Description | Request Body | Response Body | Timeout / Limits |
| ------ | ---- | ----------- | ------------ | ------------- | ---------------- |
| GET | `/api/v1/experiment/status/{job_id}` | Fetch the latest status for a submitted experiment job. | — | [`StatusResponse`](#statusresponse) | Upstream lookup capped at 6s. |
| GET | `/api/v1/experiment/logs/{job_id}` | Return the most recent log lines for a job. | — | [`LogsResponse`](#logsresponse) | Tail size defaults to 200 lines, bounded `[1, 1000]`. |
| GET | `/api/v1/experiment/review` | Retrieve normalized metrics and metadata for a job; optionally include suggestion context. | — | [`ReviewResponse`](#reviewresponse) | Manifest + log merge; upstream lookups capped at 6s total. |
| POST | `/api/v1/experiment/apply` | Kick off a follow-up experiment run derived from the supplied job. | [`ApplyRequest`](#applyrequest) | [`ApplyResponse`](#applyresponse) | HTTP invocation to `/api/experiment/run` is limited to 6s. |

> Legacy aliases (`/api/experiment/status`, `/api/experiment/logs`, `/api/experiment/review`, `/api/experiment/apply`) forward to the v1 handlers to preserve behaviour. Responses remain backward-compatible for existing consumers while adhering to the schema below.

## Schemas

> All numeric timestamps are UNIX epoch seconds (`float`). Optional properties may be omitted or explicitly set to `null`.

### `JobId`

```
pattern: ^[a-f0-9]{6,}$
```

### `ReviewResponse`

```json
{
  "job_id": "d4f2ac5b19e2",
  "summary": {
    "p95_ms": 934.5,
    "err_rate": 0.002,
    "recall_at_10": 0.672,
    "cost_tokens": 8120
  },
  "baseline": {
    "summary": {
      "p95_ms": 845.0,
      "err_rate": 0.001,
      "recall_at_10": 0.689,
      "cost_tokens": 7600
    },
    "source": "artifacts/sla/baseline.json"
  },
  "meta": {
    "poll": "/api/experiment/status/d4f2ac5b19e2",
    "logs": "/api/experiment/logs/d4f2ac5b19e2",
    "suggest_enabled": true,
    "manifest_path": "artifacts/manifests/d4f2ac5b19e2.json",
    "baseline_path": "artifacts/sla/baseline.json",
    "job_status": {
      "status": "SUCCEEDED",
      "rc": 0,
      "started": 1731160127.42,
      "ended": 1731160781.57
    }
  }
}
```

### `ApplyRequest`

```json
{
  "job_id": "d4f2ac5b19e2",
  "preset": "smoke-fast",
  "changes": {
    "top_k": 40,
    "rerank": false
  }
}
```

### `ApplyResponse`

```json
{
  "job_id": "f9c1b8074ca3",
  "poll": "/api/experiment/status/f9c1b8074ca3",
  "logs": "/api/experiment/logs/f9c1b8074ca3",
  "started_at": 1731161120.04,
  "preset": "smoke-fast",
  "overrides": {
    "top_k": 40,
    "rerank": false
  },
  "source_job_id": "d4f2ac5b19e2"
}
```

### `StatusResponse`

```json
{
  "job_id": "d4f2ac5b19e2",
  "status": "RUNNING",
  "rc": null,
  "started": 1731160127.42,
  "ended": null,
  "poll": "/api/experiment/status/d4f2ac5b19e2",
  "logs": "/api/experiment/logs/d4f2ac5b19e2"
}
```

### `LogsResponse`

```json
{
  "job_id": "d4f2ac5b19e2",
  "tail": "METRICS p95_ms=934 err_rate=0.002 recall@10=0.672 cost_tokens=8120\n...",
  "lines": 200
}
```

### `Error`

```json
{
  "error": "invalid_job_id",
  "code": "invalid_job_id",
  "detail": "job_id must match ^[a-f0-9]{6,}$"
}
```

## Error Codes

| HTTP | Code | Description |
| ---- | ---- | ----------- |
| 400 | `invalid_job_id` | `job_id` fails regex validation. |
| 400 | `invalid_tail` | `tail` query parameter is outside `[1, 1000]`. |
| 404 | `not_found` | The requested job (or manifest) could not be located. |
| 408 | `upstream_timeout` | Upstream call to the experiment runner exceeded 6s. |
| 429 | `rate_limited` | The downstream runner rejected the request due to throttling. |
| 502 | `experiment_unreachable` | Connectivity error while calling the legacy runner. |
| 503 | `busy` | Experiment runner reported capacity exhaustion. |

All errors use the uniform payload shape `{ "error": "<code>", "code": "<code>", "detail": "<optional detail>" }`.

## Timeouts & Limits

- **Upstream timeout:** 6 seconds for any call made to the legacy `/api/experiment/run` entry point.
- **Log pagination:** `tail` parameter defaults to 200 lines with inclusive bounds `[1, 1000]`.
- **Job identifiers:** Must match `^[a-f0-9]{6,}$`. Inputs are case-sensitive and must be lowercase hex.

## Versioning

- The canonical surface is versioned via the URL namespace `/api/v1/experiment/*`.
- Backward-compatible aliases remain available at `/api/experiment/*` and proxy the v1 handlers.
- Future breaking changes require bumping the path prefix (e.g., `/api/v2/experiment/*`) while preserving previous versions for at least one release cycle.
- Clients should not rely on response field ordering and must tolerate additional fields.

## Copy/Paste cURL Examples

```
# Review
curl "$BASE/api/v1/experiment/review?job_id=<id>&suggest=1" | jq

# Apply
curl -X POST "$BASE/api/v1/experiment/apply" \
  -H 'content-type: application/json' \
  --data '{"job_id":"<id>","preset":"smoke-fast"}'

# Status
curl "$BASE/api/v1/experiment/status/<id>" | jq

# Logs
curl "$BASE/api/v1/experiment/logs/<id>?tail=50" | jq
```

Replace `BASE` with the desired host (defaults to `http://localhost:8000`). The same commands work with the legacy `/api/experiment/*` prefix.

