"""
debug.py - Development helpers for verifying trace propagation.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Optional, Union
from datetime import datetime, timezone

from fastapi import APIRouter, Header, Request, Response

from services.fiqa_api import obs

router = APIRouter()

_RUNS_DIR = Path(".runs")
_OBS_URL_FILE = _RUNS_DIR / "obs_url.txt"
_TRACE_ID_FILE = _RUNS_DIR / "trace_id.txt"


def _read_runs_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""
    except OSError:
        return ""


@router.get("/debug/trace")
async def debug_trace(
    response: Response,
    request: Request,
    x_trace_id: Optional[str] = Header(None),
) -> Dict[str, str]:
    """
    Echo or mint a trace identifier for quick manual verification.

    The handler prefers, in order:
    1. Incoming X-Trace-Id header
    2. Request state populated by upstream middleware/handlers
    3. A freshly generated UUID (v4)
    """
    header_trace = (x_trace_id or "").strip()
    state_trace = getattr(request.state, "trace_id", "") or ""
    trace_id = header_trace or state_trace or str(uuid.uuid4())

    response.headers["X-Trace-Id"] = trace_id
    request.state.trace_id = trace_id

    obs_ctx = getattr(request.state, "obs_ctx", None)
    if not isinstance(obs_ctx, dict):
        obs_ctx = {}
    obs_ctx.setdefault("trace_id", trace_id)
    obs_ctx.setdefault("job_id", trace_id)
    request.state.obs_ctx = obs_ctx

    trace_url = obs.build_obs_url(trace_id)
    request.state.trace_url = trace_url

    return {"trace_id": trace_id}


@router.get("/obs/url", response_model=None)
async def get_latest_obs_url(request: Request) -> Response:
    format_hint = request.query_params.get("format", "").strip().lower()

    obs_url = _read_runs_file(_OBS_URL_FILE)
    trace_id = _read_runs_file(_TRACE_ID_FILE)

    mtime_iso = ""
    age_ms: Optional[int] = None
    stale = True
    try:
        stat_result = _OBS_URL_FILE.stat()
        mtime = datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc)
        mtime_iso = mtime.isoformat()
        age_ms = int((datetime.now(tz=timezone.utc) - mtime).total_seconds() * 1000)
        stale = age_ms >= 120_000
    except FileNotFoundError:
        pass
    except OSError:
        pass

    if not obs_url or not trace_id:
        return Response(status_code=204, headers={"Cache-Control": "no-store"})

    if format_hint == "txt":
        return Response(
            content=obs_url,
            media_type="text/plain",
            headers={"Cache-Control": "no-store"},
        )

    payload: Dict[str, Union[str, int, bool]] = {
        "url": obs_url,
        "trace_id": trace_id,
        "mtime_iso": mtime_iso,
        "age_ms": age_ms if age_ms is not None else 0,
        "stale": stale,
    }

    return Response(
        content=json.dumps(payload),
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )

