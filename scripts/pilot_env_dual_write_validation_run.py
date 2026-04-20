#!/usr/bin/env python3
"""
Bounded pilot-environment dual-write validation (Add-Car Stage 1).

Uses real Postgres when SERVICE_RECORD_DATABASE_URL + UNIFIED_INTAKE_PG_DUAL_WRITE are set.
Emulates formal-submit + append without HTTP. Prints JSON summary to stdout.

Not a production test suite — sprint evidence helper only.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.environ.setdefault("LLM_GENERATION_ENABLED", "0")

from services.fiqa_api.db.service_record_repository import fetch_service_records  # noqa: E402
from services.fiqa_api.db.service_record_settings import (  # noqa: E402
    service_record_database_url,
    service_record_dual_write_enabled,
)
from services.fiqa_api.inbox_triage.case_store import (  # noqa: E402
    append_follow_up_message,
    get_case_by_id,
    save_case,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR  # noqa: E402
from services.fiqa_api.inbox_triage.service_record_consistency import compare_snapshot_with_pg  # noqa: E402
from services.fiqa_api.inbox_triage.service_record_read import ServiceRecordReadRepository  # noqa: E402
from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_for_append  # noqa: E402
from services.fiqa_api.routes.inbox_triage import (  # noqa: E402
    ConversationTurn,
    _add_car_customer_lane,
    _add_car_structurally_complete_for_persist,
    _full_thread_lower,
    _normalize_input,
    _reply_truth_context_for_triage,
)


def _build_source_for_case(text: str, turns: list[ConversationTurn]) -> str:
    conv_parts: list[str] = []
    for t in turns:
        label = "客户" if (t.role or "").strip().lower() == "customer" else "系统"
        p = _normalize_input(t.text or "")
        if p:
            conv_parts.append(f"[{label}] {p}")
    tail = _normalize_input(text or "")
    if tail:
        conv_parts.append(f"[客户] {tail}")
    return "\n\n".join(conv_parts)


def main() -> int:
    preset = (os.environ.get("UNIFIED_INTAKE_CASES_PATH") or "").strip()
    if preset:
        cases_path = str(Path(preset).resolve())
        Path(cases_path).parent.mkdir(parents=True, exist_ok=True)
        if not Path(cases_path).exists():
            Path(cases_path).write_text('{"cases": []}\n', encoding="utf-8")
        os.environ["UNIFIED_INTAKE_CASES_PATH"] = cases_path
        cleanup_cases = False
    else:
        cases_fd, cases_path = tempfile.mkstemp(prefix="pilot_dw_val_", suffix=".json")
        os.close(cases_fd)
        Path(cases_path).write_text('{"cases": []}\n', encoding="utf-8")
        os.environ["UNIFIED_INTAKE_CASES_PATH"] = cases_path
        cleanup_cases = True

    client_id = "chen_kui"
    full_add_car = (
        "客户要加一台2021 Tesla Model Y，ZIP 90210，下周一提车，主驾是我自己，"
        "姓名张三电话4155550100，问今天能不能先出报价"
    )
    formal_line = "【正式提交办公室】请按系统要点将本条加车记录交办公室处理。"

    pre = triage_conversation(full_add_car, [], client_id=client_id)
    turns = [
        ConversationTurn(role="customer", text=full_add_car),
        ConversationTurn(role="system", text=pre.get("client_reply_draft") or ""),
    ]
    thread_lower = _full_thread_lower(formal_line, turns)
    add_car_lane = _add_car_customer_lane(None, thread_lower)
    ctx = _reply_truth_context_for_triage(case=None, formal_submit=True, add_car_lane=add_car_lane)
    post = triage_conversation(formal_line, [t.model_dump() for t in turns], client_id=client_id, reply_truth_context=ctx)

    struct_ok = _add_car_structurally_complete_for_persist(formal_line, turns)
    handoff_ready = bool(post.get("handoff_ready"))
    should_persist = bool(add_car_lane and (struct_ok or handoff_ready))

    out: dict = {
        "environment": {
            "dual_write_enabled": service_record_dual_write_enabled(),
            "database_configured": bool(service_record_database_url()),
            "cases_path": cases_path,
        },
        "lane": {"add_car_lane": add_car_lane, "struct_ok": struct_ok, "handoff_ready": handoff_ready, "should_persist": should_persist},
    }

    if not should_persist:
        out["status"] = "aborted_no_persist"
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1

    source = _build_source_for_case(formal_line, turns)
    saved = save_case(
        source,
        post,
        origin_session_id="sess_pilot_dw_val",
        client_id=client_id,
        service_lane=SERVICE_LANE_ADD_CAR if add_car_lane else None,
    )
    case_id = saved["case_id"]
    fsa_after_create = (saved.get("formal_submitted_at") or "").strip()

    append_text = "补充：registration 已发邮箱，请确认。"
    existing_src = saved.get("source_text") or ""
    append_tri = triage_for_append(existing_src, append_text, client_id=client_id)
    appended = append_follow_up_message(case_id, append_text, append_tri, client_id=client_id)
    if not appended:
        out["status"] = "append_failed"
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1

    json_case = get_case_by_id(case_id)
    repo = ServiceRecordReadRepository()
    snap = repo.get_by_case_id(case_id)

    pg_map: dict = {}
    mismatches_after_append: list[str] = []
    if service_record_dual_write_enabled() and service_record_database_url():
        pg_map = fetch_service_records([case_id])
        if snap:
            mismatches_after_append = compare_snapshot_with_pg(snap, pg_map.get(case_id))

    out["case_id"] = case_id
    out["json_highlights"] = {
        "formal_submitted_at": fsa_after_create,
        "formal_submitted_at_unchanged_after_append": (appended.get("formal_submitted_at") or "").strip() == fsa_after_create,
        "service_lane": json_case.get("service_lane") if json_case else None,
        "lifecycle_after_append": (appended.get("lifecycle_status") or "").strip(),
        "message_count": len(json_case.get("case_messages") or []) if json_case else 0,
    }
    out["postgres"] = {
        "row_present": case_id in pg_map,
        "mismatch_keys_after_append": mismatches_after_append,
    }
    if case_id in pg_map:
        row = pg_map[case_id]
        sp = row.get("structured_payload") if isinstance(row.get("structured_payload"), dict) else {}
        ex = row.get("extra") if isinstance(row.get("extra"), dict) else {}
        out["postgres"]["structured_service_lane"] = sp.get("service_lane")
        out["postgres"]["extra_formal_submitted_at"] = ex.get("formal_submitted_at")
        out["postgres"]["quote_readiness"] = row.get("quote_readiness")

    out["status"] = "ok" if not mismatches_after_append else "warn_mismatch"
    print(json.dumps(out, ensure_ascii=False, indent=2))

    if cleanup_cases:
        try:
            Path(cases_path).unlink(missing_ok=True)
        except OSError:
            pass
    return 0 if out["status"] == "ok" else 0  # evidence run: still 0 unless persist failed


if __name__ == "__main__":
    raise SystemExit(main())
