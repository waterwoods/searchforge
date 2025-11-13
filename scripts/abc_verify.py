#!/usr/bin/env python3
"""
ABC verifier for the RAG Lab stack.

Executes three phases:
  A - Data readiness (Qdrant seeding/check)
  B - Proxy path end-to-end (ok + degrade + Langfuse link)
  C - Trace freshness / Open in Langfuse endpoint

Only Python stdlib modules are used.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


RUNS_DIR = Path(".runs")
LOG_FILE = RUNS_DIR / "abc_verify.log"
ENV_FILE = Path(".env.current")
DEFAULT_COLLECTION = "fiqa_50k_v1"

PHASES = ("A", "B", "C")
PHASE_TIMEOUT_SECONDS = 8


class PhaseResult:
    def __init__(self, name: str, ok: bool, reason: str = "", details: Optional[Dict] = None):
        self.name = name
        self.ok = ok
        self.reason = reason.strip()
        self.details = details or {}


def ensure_runs_dir() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{timestamp}] {message}"
    ensure_runs_dir()
    with LOG_FILE.open("a", encoding="utf-8") as fp:
        fp.write(line + "\n")
    print(line)


def read_env_file() -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not ENV_FILE.exists():
        log("WARNING: .env.current missing; continuing with empty env")
        return env
    with ENV_FILE.open("r", encoding="utf-8") as fp:
        for raw_line in fp:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


def update_env_flag(key: str, value: str) -> None:
    lines: Iterable[str]
    existing = []
    if ENV_FILE.exists():
        with ENV_FILE.open("r", encoding="utf-8") as fp:
            existing = fp.readlines()
    else:
        log("INFO: .env.current missing; creating new file")
    updated = False
    result_lines = []
    for raw_line in existing:
        if "=" in raw_line and raw_line.split("=", 1)[0].strip() == key:
            result_lines.append(f"{key}={value}\n")
            updated = True
        else:
            result_lines.append(raw_line)
    if not updated:
        if result_lines and not result_lines[-1].endswith("\n"):
            result_lines[-1] = result_lines[-1] + "\n"
        result_lines.append(f"{key}={value}\n")
    with ENV_FILE.open("w", encoding="utf-8") as fp:
        fp.writelines(result_lines)
    log(f"Set {key}={value} in .env.current")


def run_command(command: Iterable[str], description: str, check: bool = True) -> subprocess.CompletedProcess:
    log(f"Running command: {' '.join(command)} ({description})")
    try:
        proc = subprocess.run(
            list(command),
            check=check,
            capture_output=True,
            text=True,
            timeout=PHASE_TIMEOUT_SECONDS * 10,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{description} timed out after {exc.timeout}s") from exc
    except subprocess.CalledProcessError as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        detail = stdout.strip() or stderr.strip() or str(exc)
        raise RuntimeError(f"{description} failed: {detail}") from exc
    except OSError as exc:
        raise RuntimeError(f"{description} failed: {exc}") from exc

    for stream_name, content in (("stdout", proc.stdout), ("stderr", proc.stderr)):
        if content:
            log(f"{description} {stream_name}:\n{content.strip()}")
    return proc


def save_json(path: Path, payload: Dict) -> None:
    ensure_runs_dir()
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, separators=(",", ":"))


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def http_get(url: str, accept: str = "application/json") -> Tuple[int, Dict[str, str], bytes]:
    log(f"HTTP GET {url}")
    headers = {"User-Agent": "abc-verify/1.0"}
    if accept:
        headers["Accept"] = accept
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=PHASE_TIMEOUT_SECONDS) as response:
            status = response.getcode()
            data = response.read()
            resp_headers = dict(response.headers.items())
    except HTTPError as exc:
        data = exc.read()
        raise RuntimeError(f"Request to {url} failed with HTTP {exc.code}: {data.decode('utf-8', 'ignore')}") from exc
    except URLError as exc:
        raise RuntimeError(f"Request to {url} failed: {exc.reason}") from exc
    return status, resp_headers, data


def http_post(url: str, payload: Dict, accept: str = "application/json") -> Tuple[int, Dict[str, str], bytes]:
    log(f"HTTP POST {url}")
    headers = {
        "User-Agent": "abc-verify/1.0",
        "Content-Type": "application/json",
    }
    if accept:
        headers["Accept"] = accept
    data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=PHASE_TIMEOUT_SECONDS) as response:
            status = response.getcode()
            body = response.read()
            resp_headers = dict(response.headers.items())
    except HTTPError as exc:
        data_err = exc.read()
        raise RuntimeError(
            f"Request to {url} failed with HTTP {exc.code}: {data_err.decode('utf-8', 'ignore')}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Request to {url} failed: {exc.reason}") from exc
    return status, resp_headers, body


def _probe_http_get(url: str, accept: str = "application/json") -> Tuple[int, bytes]:
    headers = {"User-Agent": "abc-verify/1.0"}
    if accept:
        headers["Accept"] = accept
    request = Request(url, headers=headers)
    with urlopen(request, timeout=PHASE_TIMEOUT_SECONDS) as response:
        return response.getcode(), response.read()


def wait_for_endpoint(url: str, description: str, timeout: float = 15.0, accept: str = "application/json") -> None:
    deadline = time.time() + timeout
    last_error: Optional[str] = None
    while time.time() < deadline:
        try:
            status, _ = _probe_http_get(url, accept=accept)
            if status == 200:
                log(f"{description} ready (HTTP {status})")
                return
            last_error = f"HTTP {status}"
        except Exception as exc:  # pragma: no cover - transient readiness probe
            last_error = str(exc)
        time.sleep(0.5)
    raise RuntimeError(f"{description} not ready after {timeout}s: {last_error}")


def parse_json_bytes(data: bytes) -> Dict:
    try:
        return json.loads(data.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Response body is not valid JSON: {exc}") from exc


def _resolve_expected_collection(
    env: Dict[str, str],
    seed_payload: Dict,
    check_payload: Dict,
) -> str:
    for key in ("COLLECTION", "QDRANT_COLLECTION", "QDRANT_COLLECTION_NAME"):
        value = env.get(key)
        if value:
            return value
    for payload in (check_payload, seed_payload):
        value = (payload or {}).get("collection")
        if isinstance(value, str) and value:
            return value
    return DEFAULT_COLLECTION


def phase_a(env: Dict[str, str]) -> PhaseResult:
    try:
        seed_path = RUNS_DIR / "qdrant_seed.json"
        check_path = RUNS_DIR / "qdrant_check.json"
        previous_seed_payload: Dict = {}
        if seed_path.exists():
            try:
                previous_seed_payload = load_json(seed_path)
            except Exception as exc:  # pragma: no cover - corrupted files
                log(f"WARNING: Failed to parse existing qdrant_seed.json before reseed: {exc}")
                previous_seed_payload = {}

        run_command(
            ("docker", "compose", "up", "-d", "qdrant", "retrieval-proxy", "rag-api"),
            "docker compose up",
        )
        run_command(("make", "seed-fiqa"), "make seed-fiqa")
        run_command(("make", "check-qdrant"), "make check-qdrant")

        if not seed_path.exists() or not check_path.exists():
            raise RuntimeError("Missing qdrant_seed.json or qdrant_check.json under .runs/")

        seed_payload = load_json(seed_path)
        check_payload = load_json(check_path)

        created = bool(seed_payload.get("created"))
        if not created and previous_seed_payload.get("forced"):
            created = True
        expected_collection = _resolve_expected_collection(env, seed_payload, check_payload)
        check_collection = check_payload.get("collection")
        status_value = check_payload.get("status")
        status_ok = status_value == "ok"
        collection_matches = check_collection == expected_collection
        ok = bool(status_ok and collection_matches)

        if ok:
            pass_reason = "created new" if created else "already exists"
            log(
                f"A health check ok for collection={check_collection} "
                f"(expected={expected_collection}, created={created}) → {pass_reason}"
            )
            phase_reason = ""
            summary_reason = pass_reason
        else:
            if not status_ok:
                fail_reason = f"health check status={status_value!r} (expected 'ok')"
            elif not collection_matches:
                fail_reason = (
                    f"collection mismatch (got {check_collection!r}, expected {expected_collection!r})"
                )
            else:
                fail_reason = "unknown failure during Phase A"
            log(
                f"A health check FAILED for collection={check_collection} "
                f"(expected={expected_collection}, status={status_value!r}) → {fail_reason}"
            )
            phase_reason = fail_reason
            summary_reason = fail_reason

        summary = {
            "ok": ok,
            "created": created,
            "reason": summary_reason,
            "collection": check_collection or expected_collection,
        }
        save_json(RUNS_DIR / "a_verify.json", summary)
        return PhaseResult("A", ok, phase_reason, summary)
    except Exception as exc:  # pylint: disable=broad-except
        reason = str(exc)
        summary = {"ok": False, "reason": reason}
        save_json(RUNS_DIR / "a_verify.json", summary)
        return PhaseResult("A", False, reason, summary)


def ensure_use_proxy_enabled() -> None:
    update_env_flag("USE_PROXY", "true")


def phase_b(env: Dict[str, str]) -> PhaseResult:
    try:
        ensure_use_proxy_enabled()
        run_command(
            ("docker", "compose", "restart", "rag-api", "retrieval-proxy"),
            "docker compose restart",
        )

        wait_for_endpoint("http://localhost:8000/health/ready", "rag-api /health/ready")
        wait_for_endpoint("http://localhost:7070/readyz", "retrieval-proxy /readyz", accept="application/json")
        time.sleep(5)

        env = read_env_file()
        proxy_url = env.get("PROXY_URL") or "http://localhost:7070"
        proxy_url = proxy_url.rstrip("/")

        ok_url = f"{proxy_url}/v1/search?q=test&k=16&budget_ms=400"
        status_ok, _, data_ok = http_get(ok_url)
        if status_ok != 200:
            raise RuntimeError(f"Proxy ok request returned HTTP {status_ok}")
        payload_ok = parse_json_bytes(data_ok)
        save_json(RUNS_DIR / "proxy_ok.json", payload_ok)

        if payload_ok.get("ret_code") != "OK" or payload_ok.get("degraded") is not False:
            raise RuntimeError("Proxy ok response missing ret_code=='OK' or degraded==false")

        deg_url = f"{proxy_url}/v1/search?q=test&k=16&budget_ms=50"
        status_deg, _, data_deg = http_get(deg_url)
        if status_deg != 200:
            raise RuntimeError(f"Proxy degrade request returned HTTP {status_deg}")
        payload_deg = parse_json_bytes(data_deg)
        save_json(RUNS_DIR / "proxy_deg.json", payload_deg)
        if payload_deg.get("ret_code") != "UPSTREAM_TIMEOUT" or payload_deg.get("degraded") is not True:
            raise RuntimeError("Proxy degrade response missing ret_code=='UPSTREAM_TIMEOUT' or degraded==true")

        # Trigger backend request to refresh trace.
        try:
            http_get("http://localhost:8000/api/query?q=test&k=8", accept="application/json")
        except RuntimeError as exc:
            if "HTTP 405" in str(exc):
                log("api/query returned 405; retrying via POST body")
                for attempt in range(3):
                    try:
                        http_post(
                            "http://localhost:8000/api/query",
                            {"question": "test", "top_k": 8},
                            accept="application/json",
                        )
                        break
                    except RuntimeError as retry_exc:
                        if "embedding_warming" in str(retry_exc) and attempt < 2:
                            wait_seconds = 2 * (attempt + 1)
                            log(
                                f"api/query returned embedding_warming; retrying in {wait_seconds}s "
                                f"(attempt {attempt + 2}/3)"
                            )
                            time.sleep(wait_seconds)
                            continue
                        raise
            else:
                raise

        obs_payload = None
        for attempt in range(3):
            status_obs, _, data_obs = http_get("http://localhost:8000/obs/url", accept="application/json")
            if status_obs == 204:
                if attempt < 2:
                    wait_seconds = 2 * (attempt + 1)
                    log(f"/obs/url returned 204; retrying in {wait_seconds}s (attempt {attempt + 2}/3)")
                    time.sleep(wait_seconds)
                    continue
                raise RuntimeError("/obs/url returned 204 No Content")
            obs_payload = parse_json_bytes(data_obs)
            break
        if obs_payload is None:
            raise RuntimeError("/obs/url did not return payload")

        save_json(RUNS_DIR / "obs_url.json", obs_payload)

        age_ms = obs_payload.get("age_ms")
        url = obs_payload.get("url") or obs_payload.get("obs_url")
        trace_id = obs_payload.get("trace_id")

        if not isinstance(age_ms, (int, float)):
            raise RuntimeError("/obs/url missing age_ms value")
        if age_ms >= 120000:
            raise RuntimeError("/obs/url age_ms too high (>=120000)")
        if not url or not isinstance(url, str) or not url.startswith("https://"):
            raise RuntimeError("/obs/url missing https url")
        if not trace_id or not isinstance(trace_id, str):
            raise RuntimeError("/obs/url missing trace_id")

        summary = {
            "ok": True,
            "proxy_ok": {"ret_code": payload_ok.get("ret_code"), "degraded": payload_ok.get("degraded")},
            "proxy_deg": {"ret_code": payload_deg.get("ret_code"), "degraded": payload_deg.get("degraded")},
            "obs": {"url": url, "trace_id": trace_id, "age_ms": age_ms},
        }
        save_json(RUNS_DIR / "b_verify.json", summary)
        return PhaseResult("B", True, "", summary)
    except Exception as exc:  # pylint: disable=broad-except
        reason = str(exc)
        summary = {"ok": False, "reason": reason}
        save_json(RUNS_DIR / "b_verify.json", summary)
        return PhaseResult("B", False, reason, summary)


def parse_obs_response(status: int, data: bytes, headers: Dict[str, str]) -> Dict:
    if status == 204:
        return {"ok": False, "url": "", "trace_id": "", "age_ms": None, "stale": True, "reason": "204 No Content"}
    text_type = headers.get("Content-Type") or headers.get("content-type", "")
    if "application/json" in text_type:
        payload = parse_json_bytes(data)
        return {
            "ok": True,
            "url": payload.get("url") or payload.get("obs_url") or "",
            "trace_id": payload.get("trace_id") or "",
            "age_ms": payload.get("age_ms"),
            "stale": payload.get("stale"),
            "payload": payload,
        }
    # fallback: treat response as text
    text = data.decode("utf-8").strip()
    return {
        "ok": True,
        "url": text,
        "trace_id": "",
        "age_ms": None,
        "stale": None,
    }


def phase_c(env: Dict[str, str]) -> PhaseResult:
    try:
        status, headers, data = http_get("http://localhost:8000/obs/url", accept="application/json")
        parsed = parse_obs_response(status, data, headers)

        if not parsed["ok"]:
            raise RuntimeError(parsed.get("reason") or "Obs endpoint returned no data")

        url = parsed["url"]
        trace_id = parsed["trace_id"]
        age_ms = parsed.get("age_ms")
        stale_flag = parsed.get("stale")

        if not url or not url.startswith("https://"):
            raise RuntimeError("Obs endpoint did not provide https URL")
        if not trace_id:
            raise RuntimeError("Obs endpoint missing trace_id")
        if age_ms is None:
            raise RuntimeError("Obs endpoint missing age_ms")
        if age_ms >= 120000:
            raise RuntimeError("Obs endpoint age_ms too high (>=120000)")
        if stale_flag is True:
            raise RuntimeError("Obs endpoint marked data as stale")

        summary = {
            "ok": True,
            "url": url,
            "trace_id": trace_id,
            "age_ms": age_ms,
            "stale": bool(stale_flag),
        }
        save_json(RUNS_DIR / "c_verify.json", summary)
        return PhaseResult("C", True, "", summary)
    except Exception as exc:  # pylint: disable=broad-except
        reason = str(exc)
        summary = {"ok": False, "reason": reason}
        save_json(RUNS_DIR / "c_verify.json", summary)
        return PhaseResult("C", False, reason, summary)


PHASE_FUNCTIONS = {
    "A": phase_a,
    "B": phase_b,
    "C": phase_c,
}


def run_phases(selected: Iterable[str]) -> Dict[str, PhaseResult]:
    env = read_env_file()
    results: Dict[str, PhaseResult] = {}
    for phase_name in selected:
        func = PHASE_FUNCTIONS[phase_name]
        log(f"--- Starting phase {phase_name} ---")
        start = time.time()
        result = func(env)
        elapsed = time.time() - start
        state = "PASS" if result.ok else "FAIL"
        reason = f": {result.reason}" if result.reason else ""
        log(f"--- Completed phase {phase_name} ({state}) in {elapsed:.1f}s{reason} ---")
        results[phase_name] = result
        if not result.ok:
            break
        env = read_env_file()
    return results


def print_summary(results: Dict[str, PhaseResult], selected: Iterable[str]) -> int:
    selected_set = set(selected)
    exit_code = 0
    for phase in PHASES:
        if phase not in selected_set:
            print(f"=== {phase} SKIP === (not requested)")
            continue
        result = results.get(phase)
        if result is None or not result.ok:
            exit_code = 1
            reason = ""
            if result and result.reason:
                reason = f" : {result.reason}"
            print(f"=== {phase} FAIL ==={reason}")
        else:
            print(f"=== {phase} PASS ===")
    if exit_code == 0:
        print("=== ABC PASS ===")
    else:
        print("=== ABC FAIL ===")
    return exit_code


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="ABC verifier for RAG Lab stack")
    parser.add_argument("--only", choices=PHASES, help="Run a single phase (A, B, or C)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    ensure_runs_dir()

    selected = [args.only] if args.only else list(PHASES)
    results = run_phases(selected)
    exit_code = print_summary(results, selected)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

