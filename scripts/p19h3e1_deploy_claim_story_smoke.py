#!/usr/bin/env python3
"""P19H-3e-1 deploy smoke — QA Cloud SQL write + Cloud Run API readback."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

_env = REPO / ".env.cloudrun"
if _env.exists():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

os.environ["ENV"] = "prod"

from scripts.demo_db_resolve import apply_qa_postgres_env  # noqa: E402

apply_qa_postgres_env(for_write=True)

from services.fiqa_api.inbox_triage.case_store import (  # noqa: E402
    append_claim_timeline_event,
    bind_case_channel_identity,
    build_claim_timeline_event,
    patch_case_known_facts,
    save_case,
    update_case_workbench_flags,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import ingest_claim_injury_quick_reply
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.reply import build_claim_wecom_media_reply

FORBIDDEN = ("已报案", "一定会赔", "对方全责", "保险公司已收到", "已受理")


def _suffix() -> str:
    return datetime.now(timezone.utc).strftime("3e1_%H%M%S")


def _tag(case_id: str) -> None:
    update_case_workbench_flags(case_id, is_test=True)
    from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation, _persist_case_after_update

    row = _load_case_for_mutation(case_id)
    if row:
        row["demo_name"] = "p19h3e1_deploy_smoke"
        _persist_case_after_update(case_id, row)


def _api_get(path: str) -> dict:
    import urllib.request

    key = os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY", "")
    base = os.environ.get("CHEN_KUI_CLOUD_API_URL", "https://fiqa-api-g7zatxrycq-uw.a.run.app")
    req = urllib.request.Request(
        f"{base}{path}",
        headers={"X-Unified-Intake-Api-Key": key} if key else {},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _seed_story_case(suffix: str) -> tuple[str, str]:
    """Seed Claim story on Cloud SQL (same fields timeline/brief path as WeCom ingest)."""
    ext = f"wm_p19h3e1_smoke_{suffix}"
    story = "今天下午三点多，在 Costco 停车场出口被后车追尾，后保险杠被撞了，人没事。"
    saved = save_case(
        f"[客户] 我要理赔\n\n[客户] {story}",
        {
            "issue_category": "claim_intake",
            "urgency": "high",
            "manual_followup_needed": True,
            "broker_next_step": "Claim guided workflow",
            "client_prep": "",
            "client_reply_draft": "",
            "handoff_ready": True,
            "collected_fields": ["accident_datetime", "accident_location", "accident_description"],
            "still_needed_fields": [],
            "known_facts": {
                "accident_datetime": "今天下午三点多",
                "accident_location": "Costco 停车场出口",
                "accident_description": "被后车追尾，后保险杠被撞了",
                "injury_status": "no",
            },
            "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        },
        service_lane=SERVICE_LANE_CLAIM,
    )
    case_id = str(saved["case_id"])
    bind_case_channel_identity(case_id, wecom_external_userid=ext)
    append_claim_timeline_event(case_id, build_claim_timeline_event(event_type="claim_started", text="Claim story recording started"))
    append_claim_timeline_event(
        case_id,
        build_claim_timeline_event(event_type="customer_text", message_id=f"m_start_{suffix}", text="我要理赔"),
    )
    append_claim_timeline_event(
        case_id,
        build_claim_timeline_event(event_type="customer_text", message_id=f"m_story_{suffix}", text=story),
    )
    append_claim_timeline_event(
        case_id,
        build_claim_timeline_event(
            event_type="basics_complete",
            actor="system",
            metadata={
                "facts_snapshot": {
                    "accident_datetime": "今天下午三点多",
                    "accident_location": "Costco 停车场出口",
                    "accident_description": "被后车追尾，后保险杠被撞了",
                    "injury_status": "no",
                }
            },
        ),
    )
    update_claim_workflow_state(case_id, claim_phase=CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE)
    _tag(case_id)
    return case_id, ext


def smoke_a(case_id: str) -> dict:
    api = _api_get(f"/api/inbox/cases/{case_id}")
    brief = api.get("claim_case_brief") or {}
    summary = str(brief.get("summary") or "")
    facts = (brief.get("key_facts") or {}) if isinstance(brief.get("key_facts"), dict) else {}
    timeline = api.get("claim_timeline") or []
    types = [e.get("event_type") for e in timeline]
    return {
        "case_id": case_id,
        "timeline_types": types,
        "has_brief": bool(brief),
        "location_ok": "Costco" in str(facts.get("accident_location") or ""),
        "injury_no": facts.get("injury_status") == "no",
        "no_forbidden": not any(p in summary for p in FORBIDDEN),
        "pass": bool(brief and timeline and facts.get("injury_status") == "no" and not any(p in summary for p in FORBIDDEN)),
    }


def smoke_b(suffix: str) -> dict:
    ext_no = f"wm_p19h3e1_inj_no_{suffix}"
    r_no = ingest_claim_injury_quick_reply(
        normalize_text_message(
            {
                "msgid": f"inj_no_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext_no,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": ""},
                "menu_id": "claim_injury_no",
            }
        ),
        injury_value="no",
    )
    api_no = _api_get(f"/api/inbox/cases/{r_no['case_id']}")
    brief_no = api_no.get("claim_case_brief") or {}
    missing = brief_no.get("missing_info") or []
    first_key = missing[0]["key"] if missing else None

    ext_yes = f"wm_p19h3e1_inj_yes_{suffix}"
    r_yes = ingest_claim_injury_quick_reply(
        normalize_text_message(
            {
                "msgid": f"inj_yes_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext_yes,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": ""},
                "menu_id": "claim_injury_yes",
            }
        ),
        injury_value="yes",
    )
    api_yes = _api_get(f"/api/inbox/cases/{r_yes['case_id']}")
    reply_yes = str(r_yes.get("reply_text") or "")
    return {
        "injury_no_status": (api_no.get("known_facts") or {}).get("injury_status"),
        "injury_no_first_missing_not_injury": first_key != "injury_status" if first_key else True,
        "injury_yes_status": (api_yes.get("known_facts") or {}).get("injury_status"),
        "injury_yes_manual": bool(r_yes.get("needs_broker_manual_handle") or api_yes.get("manual_handle")),
        "injury_yes_no_h5_nag": "上传事故照片" not in reply_yes,
        "live_msgmenu_click": "HUMAN-PENDING",
        "pass": (
            (api_no.get("known_facts") or {}).get("injury_status") == "no"
            and (api_yes.get("known_facts") or {}).get("injury_status") == "yes"
            and bool(r_yes.get("needs_broker_manual_handle") or api_yes.get("manual_handle"))
            and "上传事故照片" not in reply_yes
        ),
    }


def smoke_c(case_id: str, ext: str, suffix: str) -> dict:
    cfg = load_wecom_kf_config()

    def _dl(*_a, **_k):
        return WeComMediaDownloadResult(content=b"\xff\xd8\xff", content_type="image/jpeg", filename="a.jpg")

    def _up(**_k):
        return {"storage_uri": "gs://smoke/x.jpg", "mime_type": "image/jpeg", "size_bytes": 3}

    result = ingest_wecom_media_message(
        normalize_media_message(
            {
                "msgid": f"img_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": "MEDIA_SMOKE"},
            }
        ),
        cfg,
        download_fn=_dl,
        upload_fn=_up,
    )
    api = _api_get(f"/api/inbox/cases/{case_id}")
    brief = api.get("claim_case_brief") or {}
    evidence = brief.get("evidence_received") or {}
    timeline = api.get("claim_timeline") or []
    photo_events = [e for e in timeline if e.get("event_type") == "customer_photo"]
    reply = str(result.get("reply_text") or "")
    copy_check = build_claim_wecom_media_reply(tier="A")
    return {
        "photo_events": len(photo_events),
        "photo_count_brief": evidence.get("photo_count", 0),
        "reply": reply[:120],
        "copy_template_ok": "收到照片" in copy_check and "已记到这份事故记录里" in copy_check,
        "pass": (
            len(photo_events) >= 1
            and int(evidence.get("photo_count") or 0) >= 1
            and "收到照片" in reply
            and "已记到这份事故记录里" in reply
            and "上传事故照片" not in reply
        ),
    }


def smoke_d(case_id: str) -> dict:
    single = _api_get(f"/api/inbox/cases/{case_id}")
    listed = _api_get("/api/inbox/cases?limit=50")
    row = next((c for c in (listed.get("cases") or []) if c.get("case_id") == case_id), None)
    return {
        "list_has_brief": bool((row or {}).get("claim_case_brief")),
        "list_has_timeline": bool((row or {}).get("claim_timeline")),
        "list_has_evidence_summary": bool((row or {}).get("claim_evidence_summary")),
        "single_has_brief": bool(single.get("claim_case_brief")),
        "single_has_timeline": bool(single.get("claim_timeline")),
        "pass": bool(
            row
            and row.get("claim_case_brief")
            and row.get("claim_timeline")
            and row.get("claim_evidence_summary")
            and single.get("claim_case_brief")
            and single.get("claim_timeline")
        ),
    }


def smoke_e(suffix: str) -> dict:
    ext = f"wm_p19h3e1_addcar_{suffix}"
    saved = save_case(
        "[客户] add car smoke",
        {
            "issue_category": "add_car",
            "urgency": "medium",
            "broker_next_step": "quote",
            "client_prep": "",
            "client_reply_draft": "",
            "manual_followup_needed": False,
        },
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    bind_case_channel_identity(saved["case_id"], wecom_external_userid=ext)
    cfg = load_wecom_kf_config()

    def _dl(*_a, **_k):
        return WeComMediaDownloadResult(content=b"\xff\xd8\xff", content_type="image/jpeg", filename="reg.jpg")

    def _up(**_k):
        return {"storage_uri": "gs://smoke/reg.jpg", "mime_type": "image/jpeg", "size_bytes": 3}

    result = ingest_wecom_media_message(
        normalize_media_message(
            {
                "msgid": f"addcar_img_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": "MEDIA_ADD"},
            }
        ),
        cfg,
        download_fn=_dl,
        upload_fn=_up,
    )
    api = _api_get(f"/api/inbox/cases/{saved['case_id']}")
    local = get_case_for_read(saved["case_id"]) or {}
    return {
        "outcome": result.get("active_case_outcome"),
        "service_lane": local.get("service_lane"),
        "no_claim_timeline": not local.get("claim_timeline"),
        "api_no_brief": not api.get("claim_case_brief"),
        "has_attachment": len(local.get("case_attachments") or []) >= 1,
        "pass": (
            result.get("active_case_outcome") == "media_attached_to_case"
            and local.get("service_lane") == SERVICE_LANE_ADD_CAR
            and not local.get("claim_timeline")
            and not api.get("claim_case_brief")
            and len(local.get("case_attachments") or []) >= 1
        ),
    }


def smoke_f(case_id: str) -> dict:
    from services.fiqa_api.inbox_triage.h5_task_link import mint_h5_claim_evidence_pack_link

    url = mint_h5_claim_evidence_pack_link(case_id=case_id, external_userid="wm_smoke")
    token = url.rstrip("/").split("/")[-1]
    import urllib.request

    base = os.environ.get("CHEN_KUI_CLOUD_API_URL", "https://fiqa-api-g7zatxrycq-uw.a.run.app")
    with urllib.request.urlopen(f"{base}/api/h5/tasks/{token}", timeout=60) as resp:
        meta = json.loads(resp.read().decode())
    return {
        "token_minted": bool(token),
        "lane": meta.get("lane"),
        "flow": meta.get("flow"),
        "pass": meta.get("lane") == "claim" and meta.get("flow") == "claim_evidence_pack",
    }


def main() -> int:
    suffix = _suffix()
    case_id, ext = _seed_story_case(suffix)
    out = {
        "suffix": suffix,
        "smokes": {
            "A": smoke_a(case_id),
            "B": smoke_b(suffix),
            "C": smoke_c(case_id, ext, suffix),
            "D": smoke_d(case_id),
            "E": smoke_e(suffix),
            "F": smoke_f(case_id),
        },
    }
    out["all_pass"] = all(s["pass"] for s in out["smokes"].values())
    print(json.dumps(out, ensure_ascii=False, indent=2), flush=True)
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
