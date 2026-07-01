"""WeCom KF callback configuration from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from services.fiqa_api.wecom.crypto import WXBizMsgCrypt


@dataclass(frozen=True)
class WeComKfConfig:
    token: str
    encoding_aes_key: str
    corp_id: str
    kf_secret: str = ""

    def crypto(self) -> WXBizMsgCrypt:
        return WXBizMsgCrypt(self.token, self.encoding_aes_key, self.corp_id)


def wecom_kf_configured() -> bool:
    return load_wecom_kf_config() is not None


def wecom_kf_api_configured() -> bool:
    """True when 微信客服 Secret is set (sync_msg / send_msg)."""
    cfg = load_wecom_kf_config()
    return bool(cfg and cfg.kf_secret)


@lru_cache(maxsize=1)
def load_wecom_kf_config() -> WeComKfConfig | None:
    token = (os.getenv("WECOM_KF_TOKEN") or os.getenv("WECOM_TOKEN") or "").strip()
    encoding_aes_key = (
        os.getenv("WECOM_KF_ENCODING_AES_KEY") or os.getenv("WECOM_ENCODING_AES_KEY") or ""
    ).strip()
    corp_id = (os.getenv("WECOM_CORP_ID") or os.getenv("WECOM_KF_CORP_ID") or "").strip()
    kf_secret = (
        os.getenv("WECOM_KF_SECRET")
        or os.getenv("WECOM_CORP_SECRET")
        or os.getenv("WECOM_SECRET")
        or os.getenv("WECOM_AGENT_SECRET")
        or ""
    ).strip()
    if not token or not encoding_aes_key or not corp_id:
        return None
    return WeComKfConfig(
        token=token,
        encoding_aes_key=encoding_aes_key,
        corp_id=corp_id,
        kf_secret=kf_secret,
    )
