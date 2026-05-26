"""
Audit / export scaffolding — stable call sites for a future WORM + broker export worker.

Today: forwards to ``track_event`` only. Do not use for compliance claims yet.
"""

from __future__ import annotations

from typing import Any

from services.fiqa_api.analytics.minimal_events import track_event


def record_intake_case_mutation(
    *,
    action: str,
    case_id: str | None,
    session_id: str | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "action": action,
        "case_id": case_id,
        "session_id": session_id,
    }
    if metadata:
        for k, v in metadata.items():
            if k not in payload:
                payload[k] = v
    track_event("audit_intake_mutation", payload)


def future_export_bundle_keys() -> tuple[str, ...]:
    """Document keys intended for a signed case export (implementation TBD)."""
    return (
        "case_id",
        "config_client_id",
        "tenant_id_nullable_v1",
        "git_sha",
        "schema_epoch",
        "support_export_manifest_version",
        "triage_contract_version",
        "exported_at",
        "export_bundle_signature_alg",
        "request_trace_id",
        "deployment_id",
        "turns_redacted",
    )
