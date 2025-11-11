# Quick Backend Smoke

## Run It
- `make smoke-fast`
- `PRESET=smoke DETAIL=full TIMEOUT_SEC=300 make smoke-fast`

## What It Checks
- Submits a `/run` job with a tiny workload and polls `/status` every few seconds.
- Streams recent `/logs` output so you can spot regressions quickly.
- Stops on a terminal state or after the configured timeout and prints a JSON summary.

## Expected Output
- Progress lines showing detected mode (`proxy` vs `direct`) and the submitted `job_id`.
- Repeated status updates plus log snippets while the job runs.
- A final JSON block with `job_id`, `final_status`, `duration_sec`, `poll_url`, and `error_snippet`.

## Troubleshooting
- `404` responses usually mean the wrong base URL was picked—check which `/ready` endpoint is responding and ensure the proxy/API processes are running.
- `5xx` responses indicate the backend accepted the request yet failed internally; inspect the printed log tail and backend service logs.

