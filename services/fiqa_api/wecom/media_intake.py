"""WeCom image/file intake orchestration (P19A foundation — no OCR)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from services.fiqa_api.inbox_triage.case_store import (
    append_wecom_gcs_attachment_metadata,
    bind_case_channel_identity,
    save_case,
)
from services.fiqa_api.inbox_triage.case_truth_repository import (
    get_case_for_read,
    list_all_cases_for_read,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import (
    SERVICE_LANE_ADD_CAR,
    SERVICE_LANE_CLAIM_LITE,
    SERVICE_LANE_COVERAGE_RISK,
    SERVICE_LANE_POLICY_REVIEW,
    SERVICE_LANE_WECOM_MEDIA_INTAKE,
)
from services.fiqa_api.wecom.active_case_bridge import _record_wecom_evidence
from services.fiqa_api.wecom.config import WeComKfConfig
from services.fiqa_api.wecom.identity import wecom_customer_display_label
from services.fiqa_api.wecom.media_download import (
    WeComMediaDownloadError,
    WeComMediaDownloadResult,
    download_wecom_media,
)
from services.fiqa_api.wecom.media_storage import upload_wecom_media_to_gcs
from services.fiqa_api.wecom.reply import build_guardrail_media_reply, build_media_intake_reply
from services.fiqa_api.wecom.upload_guardrail import (
    apply_guardrail_to_attachment_metadata,
    evaluate_upload_guardrail,
)

logger = logging.getLogger(__name__)

_SUPPORTED_MSGTYPES = frozenset({"image", "file"})


@dataclass(frozen=True)
class MediaBindingDecision:
    case_id: str | None
    binding_confidence: str
    service_lane: str | None
    intake_status: str | None = None


def _log_event(event: str, payload: dict[str, Any]) -> None:
    logger.info("%s %s", event, json.dumps(payload, ensure_ascii=False))


def is_supported_media_msgtype(msgtype: str) -> bool:
    return (msgtype or "").lower() in _SUPPORTED_MSGTYPES


def _parse_received_at(normalized: dict[str, Any]) -> datetime:
    ts = normalized.get("received_at") or normalized.get("timestamp") or normalized.get("send_time")
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    if isinstance(ts, str) and ts.strip():
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def find_wecom_attachment_by_msg_id(msg_id: str) -> tuple[str | None, dict[str, Any] | None]:
    """Return (case_id, attachment_meta) when msg_id already ingested."""
    mid = (msg_id or "").strip()
    if not mid:
        return None, None
    for case in list_all_cases_for_read():
        cid = str(case.get("case_id") or "").strip()
        if not cid:
            continue
        for att in case.get("case_attachments") or []:
            if not isinstance(att, dict):
                continue
            if att.get("source") == "wecom" and att.get("msg_id") == mid:
                return cid, att
    return None, None


def _open_cases_for_external_userid(external_userid: str) -> list[dict[str, Any]]:
    ext = (external_userid or "").strip()
    if not ext:
        return []
    out: list[dict[str, Any]] = []
    for case in list_all_cases_for_read():
        if case.get("wecom_external_userid") != ext:
            continue
        if case.get("case_status") == "closed":
            continue
        out.append(case)
    return out


def resolve_media_case_binding(external_userid: str) -> MediaBindingDecision:
    """
    Minimal safe binding (P19A):
    1. Active add_car draft/case — high (one add_car only)
    2. Single open Premium/Claim/Coverage case — medium/high
    3. Exactly one other open case — medium
    4. Multiple or none — unassigned
    """
    ext = (external_userid or "").strip()
    if not ext:
        return MediaBindingDecision(None, "unknown", None, intake_status="unassigned")

    open_cases = _open_cases_for_external_userid(ext)
    substantive = [c for c in open_cases if c.get("service_lane") != SERVICE_LANE_WECOM_MEDIA_INTAKE]
    if not substantive:
        return MediaBindingDecision(None, "unknown", None, intake_status="unassigned")

    add_car_cases = [c for c in substantive if c.get("service_lane") == SERVICE_LANE_ADD_CAR]
    if len(add_car_cases) == 1:
        cid = str(add_car_cases[0]["case_id"])
        return MediaBindingDecision(cid, "high", SERVICE_LANE_ADD_CAR)
    if len(add_car_cases) > 1:
        return MediaBindingDecision(None, "unknown", None, intake_status="unassigned")

    minimal_lanes = {
        SERVICE_LANE_POLICY_REVIEW,
        SERVICE_LANE_CLAIM_LITE,
        SERVICE_LANE_COVERAGE_RISK,
    }
    minimal_cases = [c for c in substantive if c.get("service_lane") in minimal_lanes]
    if len(minimal_cases) == 1:
        lane = str(minimal_cases[0].get("service_lane") or "").strip()
        cid = str(minimal_cases[0]["case_id"])
        conf = "high" if lane == SERVICE_LANE_COVERAGE_RISK else "medium"
        return MediaBindingDecision(cid, conf, lane or None)
    if len(minimal_cases) > 1:
        return MediaBindingDecision(None, "unknown", None, intake_status="unassigned")

    if len(substantive) == 1:
        lane = str(substantive[0].get("service_lane") or "").strip() or None
        return MediaBindingDecision(str(substantive[0]["case_id"]), "medium", lane)

    return MediaBindingDecision(None, "unknown", None, intake_status="unassigned")


def _find_open_unassigned_intake_case(external_userid: str) -> str | None:
    for case in _open_cases_for_external_userid(external_userid):
        if case.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE:
            return str(case["case_id"])
    return None


def _find_or_create_unassigned_intake_case(
    normalized: dict[str, Any],
    *,
    customer_label: str,
) -> str:
    ext = str(normalized.get("external_userid") or "").strip()
    for case in _open_cases_for_external_userid(ext):
        if case.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE:
            return str(case["case_id"])
    triage_stub = {
        "issue_category": "wecom_media_intake",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": "WeCom media received — broker must attach to correct case or ask customer.",
        "client_prep": "",
        "client_reply_draft": "",
        "lifecycle_status": "collecting",
        "workbench_tags": ["WeCom", "Media Intake", "Unassigned"],
    }
    saved = save_case(
        f"[客户] WeCom: 图片待分类 ({customer_label})",
        triage_stub,
        status="new",
        service_lane=SERVICE_LANE_WECOM_MEDIA_INTAKE,
    )
    case_id = str(saved.get("case_id") or "").strip()
    if case_id and ext:
        bind_case_channel_identity(
            case_id,
            wecom_external_userid=ext,
            wecom_open_kf_id=str(normalized.get("open_kf_id") or "").strip() or None,
        )
    return case_id


def _build_attachment_metadata(
    normalized: dict[str, Any],
    *,
    storage: dict[str, Any],
    binding: MediaBindingDecision,
    customer_label: str,
) -> dict[str, Any]:
    received_at = _parse_received_at(normalized)
    meta: dict[str, Any] = {
        "attachment_id": f"att_{uuid4().hex[:12]}",
        "source": "wecom",
        "external_userid": str(normalized.get("external_userid") or ""),
        "customer_label": customer_label,
        "msg_id": str(normalized.get("msg_id") or ""),
        "msgtype": str(normalized.get("msgtype") or ""),
        "media_id": str(normalized.get("media_id") or ""),
        "storage_uri": storage["storage_uri"],
        "mime_type": storage.get("mime_type"),
        "size_bytes": storage.get("size_bytes"),
        "received_at": received_at.isoformat(),
        "bound_case_id": binding.case_id,
        "binding_confidence": binding.binding_confidence,
        "document_type": "unknown_document",
        "document_type_confidence": "unknown",
        "ocr_status": "not_started",
        "ocr_draft": None,
        "broker_confirmed": False,
    }
    if binding.case_id is None:
        meta["bound_case_id"] = None
        meta["intake_status"] = binding.intake_status or "unassigned"
        meta["broker_action"] = "attach_to_case_or_ask_customer"
    return meta


def ingest_wecom_media_message(
    normalized: dict[str, Any],
    cfg: WeComKfConfig,
    *,
    download_fn: Callable[..., WeComMediaDownloadResult] | None = None,
    upload_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Download WeCom media, upload to GCS, persist attachment metadata, return outcome.
  No OCR. Idempotent on msg_id.
    """
    msg_id = str(normalized.get("msg_id") or "").strip()
    msgtype = str(normalized.get("msgtype") or "").lower()
    external_userid = str(normalized.get("external_userid") or "").strip()
    media_id = str(normalized.get("media_id") or "").strip()

    if not is_supported_media_msgtype(msgtype):
        return {
            "outcome": "media_unsupported_type",
            "case_id": None,
            "case_created": False,
            "attachment_id": None,
            "reply_text": None,
        }

    existing_case_id, existing_att = find_wecom_attachment_by_msg_id(msg_id)
    if existing_att:
        lane = None
        if existing_case_id:
            case = get_case_for_read(existing_case_id)
            lane = str(case.get("service_lane") or "").strip() if case else None
        reply = build_media_intake_reply(
            bound=True,
            service_lane=lane,
            binding_confidence=str(existing_att.get("binding_confidence") or "unknown"),
        )
        _log_event(
            "wecom_media_intake_duplicate_v1",
            {"msg_id": msg_id, "case_id": existing_case_id},
        )
        return {
            "outcome": "duplicate_msg",
            "case_id": existing_case_id,
            "case_created": False,
            "attachment_id": existing_att.get("attachment_id"),
            "reply_text": reply,
            "active_case_outcome": "media_attached_to_case" if existing_case_id else "media_unassigned",
        }

    customer_label = wecom_customer_display_label(external_userid)
    binding = resolve_media_case_binding(external_userid)
    target_case_id = binding.case_id
    case_created = False
    bound_to_service_case = target_case_id is not None

    try:
        dl = download_fn or download_wecom_media
        downloaded = dl(cfg, media_id=media_id, msgtype=msgtype)
        up = upload_fn or upload_wecom_media_to_gcs
        storage = up(
            external_userid=external_userid,
            msg_id=msg_id,
            content=downloaded.content,
            mime_type=downloaded.content_type,
            msgtype=msgtype,
            filename=normalized.get("filename") or downloaded.filename,
            received_at=_parse_received_at(normalized),
        )
    except WeComMediaDownloadError as exc:
        _log_event("wecom_media_download_failed_v1", {"msg_id": msg_id, "error": str(exc)})
        return {
            "outcome": "media_download_failed",
            "case_id": None,
            "case_created": False,
            "attachment_id": None,
            "reply_text": build_media_intake_reply(bound=False, service_lane=None),
            "active_case_outcome": "media_download_failed",
            "error": str(exc),
        }
    except ValueError as exc:
        _log_event("wecom_media_storage_rejected_v1", {"msg_id": msg_id, "error": str(exc)})
        return {
            "outcome": "media_unsupported_type",
            "case_id": None,
            "case_created": False,
            "attachment_id": None,
            "reply_text": build_media_intake_reply(bound=False, service_lane=None),
            "active_case_outcome": "media_unsupported_type",
            "error": str(exc),
        }
    except Exception as exc:  # noqa: BLE001
        _log_event("wecom_media_storage_failed_v1", {"msg_id": msg_id, "error": str(exc)})
        return {
            "outcome": "media_download_failed",
            "case_id": None,
            "case_created": False,
            "attachment_id": None,
            "reply_text": build_media_intake_reply(bound=False, service_lane=None),
            "active_case_outcome": "media_download_failed",
            "error": str(exc),
        }

    att_meta = _build_attachment_metadata(
        normalized,
        storage=storage,
        binding=binding,
        customer_label=customer_label,
    )

    received_at = _parse_received_at(normalized)
    lane_for_guardrail = binding.service_lane
    if target_case_id and not lane_for_guardrail:
        pre_case = get_case_for_read(target_case_id)
        lane_for_guardrail = str(pre_case.get("service_lane") or "").strip() if pre_case else None

    guardrail = evaluate_upload_guardrail(
        external_userid=external_userid,
        received_at=received_at,
        service_lane=lane_for_guardrail,
        case_id=target_case_id,
        slot_assignment=str(att_meta.get("document_type") or "unknown_document"),
    )
    att_meta = apply_guardrail_to_attachment_metadata(att_meta, guardrail)

    if target_case_id is None:
        had_intake = _find_open_unassigned_intake_case(external_userid)
        target_case_id = _find_or_create_unassigned_intake_case(normalized, customer_label=customer_label)
        case_created = had_intake is None
        bound_to_service_case = False
        binding = MediaBindingDecision(target_case_id, "unknown", SERVICE_LANE_WECOM_MEDIA_INTAKE, "unassigned")
        att_meta["bound_case_id"] = None
        att_meta["binding_confidence"] = "unknown"
        att_meta["broker_action"] = "attach_to_case_or_ask_customer"
        # Guardrail intake_status (promoted/quarantined) preserved from apply_guardrail above.

    updated = append_wecom_gcs_attachment_metadata(target_case_id, att_meta)
    if updated is None:
        return {
            "outcome": "media_download_failed",
            "case_id": None,
            "case_created": False,
            "attachment_id": None,
            "reply_text": build_media_intake_reply(bound=False, service_lane=None),
            "active_case_outcome": "media_download_failed",
        }

    if msg_id and target_case_id:
        _record_wecom_evidence(target_case_id, msg_id)

    lane = binding.service_lane
    if target_case_id and not lane:
        case = get_case_for_read(target_case_id)
        lane = str(case.get("service_lane") or "").strip() if case else None

    reply_text = build_guardrail_media_reply(
        reply_kind=guardrail.reply_kind,
        bound=bound_to_service_case,
        service_lane=lane,
        binding_confidence=binding.binding_confidence,
    )
    active_outcome = "media_attached_to_case" if bound_to_service_case else "media_unassigned"

    _log_event(
        "wecom_media_intake_ok_v1",
        {
            "msg_id": msg_id,
            "case_id": target_case_id,
            "attachment_id": att_meta["attachment_id"],
            "binding_confidence": binding.binding_confidence,
            "active_case_outcome": active_outcome,
            "guardrail_status": guardrail.guardrail_status,
            "intake_status": att_meta.get("intake_status"),
        },
    )
    return {
        "outcome": active_outcome,
        "active_case_outcome": active_outcome,
        "case_id": target_case_id,
        "case_created": case_created,
        "attachment_id": att_meta["attachment_id"],
        "reply_text": reply_text,
        "binding_confidence": binding.binding_confidence,
        "service_lane": lane,
        "storage_uri": storage["storage_uri"],
        "guardrail_status": guardrail.guardrail_status,
        "intake_status": att_meta.get("intake_status"),
    }
