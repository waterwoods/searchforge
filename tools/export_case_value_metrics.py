#!/usr/bin/env python3
"""Export minimum case value metrics (V1) from existing case + Timeline fields.

Read-only. Cloud QA by default. Never targets Production. Never mutates cases.

Usage:
  PYTHONPATH=. python3 tools/export_case_value_metrics.py case_4e5adf36c637
  PYTHONPATH=. python3 tools/export_case_value_metrics.py case_a case_b --out-dir /tmp/metrics
  PYTHONPATH=. python3 tools/export_case_value_metrics.py --from-json path/to/case.json

Auth: loads `.env.cloudrun.qa` (UNIFIED_INTAKE_INTAKE_API_KEY) like QA Fast Lane.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLOUD_QA_API = "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app"
PRODUCTION_API = "https://fiqa-api-g7zatxrycq-uw.a.run.app"

CSV_COLUMNS = [
    "case_id",
    "customer_started_at",
    "formal_submitted_at",
    "time_to_formal_submit_sec",
    "time_to_broker_ready_sec",
    "first_request_more_at",
    "request_more_loops",
    "supplement_submitted_at",
    "supplement_turnaround_sec",
    "broker_supplement_reviewed_at",
    "office_materials_accepted_at",
    "time_to_office_accept_sec",
    "data_quality_notes",
]


def _load_qa_env() -> None:
    path = ROOT / ".env.cloudrun.qa"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, _, val = raw.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if key and key not in os.environ and val:
            os.environ[key] = val


def _assert_cloud_qa(api_base: str) -> None:
    url = (api_base or "").rstrip("/")
    if url == PRODUCTION_API or ("fiqa-api-" in url and "fiqa-api-qa" not in url):
        raise SystemExit("REFUSED: Production API hard-blocked for value metrics export.")
    if url != CLOUD_QA_API:
        raise SystemExit(f"REFUSED: API must be Cloud QA ({CLOUD_QA_API}), got {url!r}")


def _parse_ts(value: Any) -> datetime | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _fmt_ts(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sec_between(start: datetime | None, end: datetime | None) -> str:
    if start is None or end is None:
        return ""
    return str(int((end - start).total_seconds()))


def _iter_events(case: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for key in ("claim_timeline", "timeline_events"):
        raw = case.get(key)
        if isinstance(raw, list):
            events.extend(e for e in raw if isinstance(e, dict))
    for proj_key in (
        "p20_slice1_projection",
        "slice1_projection",
        "p20_case_intake_projection",
        "case_intake_projection",
    ):
        proj = case.get(proj_key)
        if not isinstance(proj, dict):
            continue
        latest = proj.get("latest_events")
        if isinstance(latest, list):
            events.extend(e for e in latest if isinstance(e, dict))
        for summary_key in ("timeline_summary",):
            summary = proj.get(summary_key)
            if isinstance(summary, list):
                events.extend(e for e in summary if isinstance(e, dict))
    return events


def _event_type(ev: dict[str, Any]) -> str:
    return str(ev.get("event_type") or ev.get("type") or "").strip()


def _event_ts(ev: dict[str, Any]) -> datetime | None:
    return _parse_ts(ev.get("created_at") or ev.get("timestamp"))


def _unique_event_times(events: list[dict[str, Any]], event_type: str) -> list[datetime]:
    """Deduplicate by event_id when present, else by timestamp."""
    seen: set[str] = set()
    times: list[datetime] = []
    for ev in events:
        if _event_type(ev) != event_type:
            continue
        t = _event_ts(ev)
        if t is None:
            continue
        eid = str(ev.get("event_id") or "").strip()
        key = eid if eid else f"{event_type}:{_fmt_ts(t)}"
        if key in seen:
            continue
        seen.add(key)
        times.append(t)
    return sorted(times)


def compute_case_value_metrics(case: dict[str, Any]) -> dict[str, Any]:
    """Derive V1 metrics from a case detail payload. Never fabricates missing times."""
    notes: list[str] = []
    case_id = str(case.get("case_id") or case.get("id") or "").strip()

    started = _parse_ts(case.get("created_at"))
    formal = _parse_ts(case.get("formal_submitted_at"))
    office = _parse_ts(case.get("office_materials_accepted_at"))

    if started is None:
        notes.append("missing:customer_started_at(created_at)")
    if formal is None:
        notes.append("missing:formal_submitted_at")
    elif started is not None and formal == started:
        notes.append(
            "note:formal_submitted_at_equals_created_at;"
            "pre_submit_dwell_not_separately_recorded"
        )

    # Initial broker-ready ≈ formal submit for this product shape.
    broker_ready = formal
    if broker_ready is None:
        notes.append("missing:broker_ready_timestamp")

    events = _iter_events(case)
    rm_times = _unique_event_times(events, "broker_request_more_created")
    # Fallback: open_request.created_at when timeline slice omitted the create event.
    if not rm_times:
        for proj_key in ("p20_slice1_projection", "slice1_projection", "p20_slice1_request_summary", "slice1_request_summary"):
            proj = case.get(proj_key)
            if not isinstance(proj, dict):
                continue
            open_req = proj.get("open_request") if proj_key.endswith("projection") else proj
            if not isinstance(open_req, dict):
                open_req = proj.get("open_request") if isinstance(proj.get("open_request"), dict) else proj
            created = _parse_ts(open_req.get("created_at") if isinstance(open_req, dict) else None)
            if created is not None:
                rm_times = [created]
                notes.append("note:request_more_from_open_request_created_at")
                break

    first_rm = rm_times[0] if rm_times else None
    rm_loops = len(rm_times)
    if first_rm is None:
        notes.append("missing:first_request_more_at")

    supp_times = _unique_event_times(events, "supplement_submitted")
    # Fallback: request item customer_response.submitted_at
    if not supp_times:
        for proj_key in ("p20_slice1_projection", "slice1_projection", "p20_slice1_request_summary", "slice1_request_summary"):
            proj = case.get(proj_key)
            if not isinstance(proj, dict):
                continue
            open_req = proj.get("open_request") if "projection" in proj_key else proj
            if not isinstance(open_req, dict):
                continue
            items = open_req.get("items") if isinstance(open_req.get("items"), list) else []
            for item in items:
                if not isinstance(item, dict):
                    continue
                resp = item.get("customer_response")
                if isinstance(resp, dict):
                    t = _parse_ts(resp.get("submitted_at") or item.get("satisfied_at"))
                    if t is not None:
                        supp_times.append(t)
            if supp_times:
                notes.append("note:supplement_from_request_item_response")
                break
    supp_times = sorted(supp_times)
    supplement_at = supp_times[0] if supp_times else None
    if supplement_at is None and first_rm is not None:
        notes.append("missing:supplement_submitted_at")

    ack_times = _unique_event_times(events, "broker_supplement_reviewed")
    ack_at = ack_times[0] if ack_times else None
    if ack_at is None and supplement_at is not None:
        notes.append("missing:broker_supplement_reviewed_at")

    if office is None:
        notes.append("missing:office_materials_accepted_at")

    # Explicitly never invent broker-open.
    if not _parse_ts(case.get("broker_confirmed_at")) and not any(
        _event_type(e) in ("broker_opened", "broker_case_opened", "broker_first_open") for e in events
    ):
        notes.append("unsupported:broker_first_open_not_recorded")

    notes.append("unsupported:ai_accept_edit_reject_rates_no_events")

    return {
        "case_id": case_id,
        "customer_started_at": _fmt_ts(started),
        "formal_submitted_at": _fmt_ts(formal),
        "time_to_formal_submit_sec": _sec_between(started, formal),
        "time_to_broker_ready_sec": _sec_between(started, broker_ready),
        "first_request_more_at": _fmt_ts(first_rm),
        "request_more_loops": rm_loops if first_rm is not None else "",
        "supplement_submitted_at": _fmt_ts(supplement_at),
        "supplement_turnaround_sec": _sec_between(first_rm, supplement_at),
        "broker_supplement_reviewed_at": _fmt_ts(ack_at),
        "office_materials_accepted_at": _fmt_ts(office),
        "time_to_office_accept_sec": _sec_between(started, office),
        "data_quality_notes": ";".join(notes),
    }


def _http_get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            body = json.loads(raw) if raw else {}
            if not isinstance(body, dict):
                raise SystemExit(f"unexpected_response:{url}")
            return body
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"http_{exc.code}:{url}:{raw[:300]}") from exc


def fetch_case(api: str, case_id: str) -> dict[str, Any]:
    key = (os.getenv("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()
    headers = {"Accept": "application/json"}
    if key:
        headers["X-Unified-Intake-Api-Key"] = key
    return _http_get_json(f"{api.rstrip('/')}/api/inbox/cases/{case_id}", headers)


def write_outputs(rows: list[dict[str, Any]], out_dir: Path, stem: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{stem}.json"
    csv_path = out_dir / f"{stem}.csv"
    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_COLUMNS})
    return json_path, csv_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export case value metrics V1 (read-only, Cloud QA).")
    parser.add_argument("case_ids", nargs="*", help="One or more QA case_id values")
    parser.add_argument("--from-json", action="append", default=[], help="Local case JSON fixture path")
    parser.add_argument("--api", default=CLOUD_QA_API, help="API base (Cloud QA only)")
    parser.add_argument(
        "--out-dir",
        default=str(ROOT / "artifacts" / "case_value_metrics"),
        help="Output directory for CSV/JSON",
    )
    parser.add_argument("--stem", default="case_value_metrics", help="Output filename stem")
    args = parser.parse_args(argv)

    if not args.case_ids and not args.from_json:
        parser.error("provide case_id(s) and/or --from-json")

    rows: list[dict[str, Any]] = []
    for path in args.from_json:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise SystemExit(f"invalid_case_json:{path}")
        rows.append(compute_case_value_metrics(payload))

    if args.case_ids:
        _load_qa_env()
        _assert_cloud_qa(args.api)
        for case_id in args.case_ids:
            case = fetch_case(args.api, case_id)
            rows.append(compute_case_value_metrics(case))

    json_path, csv_path = write_outputs(rows, Path(args.out_dir), args.stem)
    print(json.dumps({"rows": len(rows), "json": str(json_path), "csv": str(csv_path)}, indent=2))
    for row in rows:
        print(
            f"{row['case_id']}: formal={row['time_to_formal_submit_sec'] or 'MISSING'}s "
            f"rm_loops={row['request_more_loops']} "
            f"supp_turnaround={row['supplement_turnaround_sec'] or 'MISSING'}s "
            f"office={row['time_to_office_accept_sec'] or 'MISSING'}s"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
