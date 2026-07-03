"""WeCom admin diagnostics — secret resolution, fingerprints, sync_msg error mapping."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

SECRET_ENV_KEYS: tuple[str, ...] = (
    "WECOM_KF_SECRET",
    "WECOM_CORP_SECRET",
    "WECOM_SECRET",
    "WECOM_AGENT_SECRET",
)

SYNC_MSG_SECRET_KEYS: tuple[str, ...] = (
    "WECOM_KF_SECRET",
    "WECOM_AGENT_SECRET",
)

GETTOKEN_AGENT_FALLBACK_WARNING = (
    "WARNING: gettoken PASS does not imply kf/sync_msg permission."
)

SYNC_MSG_AGENT_FALLBACK_WARNING = (
    "WARNING: WECOM_KF_SECRET is unset; using WECOM_AGENT_SECRET. "
    "sync_msg may return 48002 even when gettoken passes."
)


@dataclass(frozen=True)
class SyncMsgDiagnostic:
    errcode: int
    summary: str
    next_action: str


@dataclass(frozen=True)
class ErrcodeCause:
    label: str
    probability_pct: int


@dataclass(frozen=True)
class BlockerSummary:
    errcode: int | None
    category: str
    owner: str
    admin_minutes: str
    engineering_days: str
    business_risk: str


SYNC_MSG_ERRCODE_MEANINGS: dict[int, str] = {
    0: "sync_msg permission works.",
    40001: "Invalid secret or CorpID mismatch.",
    48002: "API has no permission.",
    48007: "KF account not authorized to this app.",
    60020: "Outbound IP not in 企业可信IP.",
    95011: "联合版 / 独立版 Secret mode mismatch.",
    95012: "联合版 / 独立版 Secret mode mismatch.",
}

SYNC_MSG_ERRCODE_CAUSES: dict[int, tuple[ErrcodeCause, ...]] = {
    48002: (
        ErrcodeCause("Wrong Secret class", 35),
        ErrcodeCause("Callable App not configured", 30),
        ErrcodeCause("KF account not API-managed", 25),
        ErrcodeCause("Other", 10),
    ),
    48007: (
        ErrcodeCause("KF account not bound to app", 45),
        ErrcodeCause("Wrong open_kfid", 35),
        ErrcodeCause("Other", 20),
    ),
    40001: (
        ErrcodeCause("Secret / CorpID mismatch", 50),
        ErrcodeCause("Wrong Secret class", 30),
        ErrcodeCause("Other", 20),
    ),
    60020: (
        ErrcodeCause("Cloud Run IP not whitelisted", 70),
        ErrcodeCause("Other", 30),
    ),
    95011: (
        ErrcodeCause("联合版 / 独立版 Secret mismatch", 80),
        ErrcodeCause("Other", 20),
    ),
    95012: (
        ErrcodeCause("联合版 / 独立版 Secret mismatch", 80),
        ErrcodeCause("Other", 20),
    ),
}


def secret_fingerprint(value: str) -> str:
    """Safe fingerprint: first 4 + last 4 + length. Never returns the full secret."""
    v = (value or "").strip()
    if not v:
        return "(unset)"
    if len(v) <= 8:
        masked = f"{v[:2]}…{v[-2:]}" if len(v) > 4 else "****"
        return f"{masked} (len={len(v)})"
    return f"{v[:4]}…{v[-4:]} (len={len(v)})"


def resolve_secret(
    env: dict[str, str] | None = None,
    *,
    keys: tuple[str, ...] = SECRET_ENV_KEYS,
) -> tuple[str | None, str | None]:
    source = env if env is not None else os.environ
    for key in keys:
        val = (source.get(key) or "").strip()
        if val:
            return key, val
    return None, None


def gettoken_agent_fallback_warning(
    secret_key: str | None,
    env: dict[str, str] | None = None,
) -> str | None:
    """Warn when agent secret is used because KF secret is unset."""
    source = env if env is not None else os.environ
    kf_set = bool((source.get("WECOM_KF_SECRET") or "").strip())
    if not kf_set and secret_key == "WECOM_AGENT_SECRET":
        return GETTOKEN_AGENT_FALLBACK_WARNING
    return None


def sync_msg_agent_fallback_warning(
    secret_key: str | None,
    env: dict[str, str] | None = None,
) -> str | None:
    source = env if env is not None else os.environ
    kf_set = bool((source.get("WECOM_KF_SECRET") or "").strip())
    if not kf_set and secret_key == "WECOM_AGENT_SECRET":
        return SYNC_MSG_AGENT_FALLBACK_WARNING
    return None


def map_sync_msg_errcode(errcode: int | None) -> SyncMsgDiagnostic:
    code = int(errcode if errcode is not None else -1)
    mapping: dict[int, tuple[str, str]] = {
        0: (
            "SUCCESS: sync_msg permission works.",
            "Send a personal WeChat test message to the KF account, then re-run "
            "with WECOM_TEST_CALLBACK_TOKEN from the callback event if message_count is 0.",
        ),
        48002: (
            "API permission mismatch. Check KF Secret, 可调用接口的应用, app permissions.",
            "Enterprise WeCom Admin → 微信客服 → API → 可调用接口的应用 → add "
            "CaseIQ AI Adapter. Confirm WECOM_KF_SECRET is the 微信客服 Secret "
            "(not the self-built app Secret). Re-run validate_wecom_sync_msg.py.",
        ),
        48007: (
            "KF account not authorized to this app. Check 通过API管理微信客服账号.",
            "Enterprise WeCom Admin → 微信客服 → API → 通过API管理微信客服账号 → "
            "bind the target 客服账号 to CaseIQ AI Adapter. Confirm "
            "WECOM_TEST_OPEN_KF_ID matches that account. Re-run validate_wecom_sync_msg.py.",
        ),
        95011: (
            "联合版 / 独立版 Secret mode mismatch.",
            "Confirm your WeCom edition (联合版 vs 独立版). Copy the Secret from the "
            "matching 微信客服 console section. Update WECOM_KF_SECRET in .env.cloudrun.",
        ),
        95012: (
            "联合版 / 独立版 Secret mode mismatch.",
            "Confirm your WeCom edition (联合版 vs 独立版). Copy the Secret from the "
            "matching 微信客服 console section. Update WECOM_KF_SECRET in .env.cloudrun.",
        ),
        60020: (
            "IP not trusted. Check 企业可信IP.",
            "Enterprise WeCom Admin → 应用管理 → 企业可信IP → add Cloud Run egress IP "
            "(or your current outbound IP). Re-run validate_wecom_sync_msg.py.",
        ),
        40001: (
            "Invalid secret / corp mismatch.",
            "Re-copy WECOM_CORP_ID from 我的企业 → 企业信息 → 企业ID and "
            "WECOM_KF_SECRET from 微信客服 → API. Ensure both belong to the same corp.",
        ),
    }
    summary, next_action = mapping.get(
        code,
        (
            f"Unexpected errcode {code}.",
            "Check errmsg in WeCom API docs. Verify corp, secret class, KF account, "
            "and callback configuration.",
        ),
    )
    return SyncMsgDiagnostic(errcode=code, summary=summary, next_action=next_action)


def sync_msg_errcode_meaning(errcode: int | None) -> str:
    code = int(errcode if errcode is not None else -1)
    return SYNC_MSG_ERRCODE_MEANINGS.get(code, f"Unexpected errcode {code}.")


def sync_msg_errcode_causes(errcode: int | None) -> tuple[ErrcodeCause, ...]:
    code = int(errcode if errcode is not None else -1)
    return SYNC_MSG_ERRCODE_CAUSES.get(code, (ErrcodeCause("Unknown / check errmsg", 100),))


def sync_msg_blocker_summary(errcode: int | None) -> BlockerSummary:
    code = int(errcode if errcode is not None else -1)
    admin_config_codes = {48002, 48007, 60020, 95011, 95012}
    credential_codes = {40001}

    if code == 0:
        return BlockerSummary(
            errcode=0,
            category="None",
            owner="—",
            admin_minutes="0 min",
            engineering_days="0 days",
            business_risk="LOW",
        )
    if code in admin_config_codes:
        return BlockerSummary(
            errcode=code,
            category="Admin Configuration",
            owner="Admin",
            admin_minutes="30 min",
            engineering_days="0 days",
            business_risk="LOW",
        )
    if code in credential_codes:
        return BlockerSummary(
            errcode=code,
            category="Credential Mismatch",
            owner="Admin + Engineering",
            admin_minutes="15 min",
            engineering_days="0–1 days",
            business_risk="LOW",
        )
    return BlockerSummary(
        errcode=code if code >= 0 else None,
        category="Investigation Required",
        owner="Engineering",
        admin_minutes="—",
        engineering_days="2–4 days",
        business_risk="MEDIUM",
    )


def track_a_ready(sync_msg_errcode: int | None, *, message_count: int = 0) -> bool:
    code = int(sync_msg_errcode if sync_msg_errcode is not None else -1)
    return code == 0


def track_a_green_ready(sync_msg_errcode: int | None, *, message_count: int = 0) -> bool:
    code = int(sync_msg_errcode if sync_msg_errcode is not None else -1)
    return code == 0 and int(message_count) > 0


def parse_sync_msg_response(data: dict[str, Any]) -> dict[str, Any]:
    """Extract safe diagnostic fields from kf/sync_msg JSON."""
    msg_list = data.get("msg_list") or []
    message_count = len(msg_list) if isinstance(msg_list, list) else 0
    has_more = data.get("has_more")
    next_cursor = data.get("next_cursor")
    out: dict[str, Any] = {
        "errcode": data.get("errcode"),
        "errmsg": data.get("errmsg", ""),
        "message_count": message_count,
        "has_next": bool(int(has_more or 0) == 1),
    }
    if next_cursor:
        out["next_cursor"] = str(next_cursor)
    return out
