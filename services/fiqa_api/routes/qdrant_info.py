"""
Qdrant information and version checking routes.
"""
from fastapi import APIRouter
import os
import requests
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/qdrant", tags=["qdrant"])


def _normalize_tag(s: str) -> str:
    """Normalize version tag by removing 'v' prefix and stripping whitespace."""
    return (s or "").lstrip("v").strip()


@router.get("/version.tag")
def qdrant_version_tag():
    """
    Check if Qdrant runtime version matches the configured QDRANT_TAG.
    
    Returns:
        dict with qdrant_tag_env, qdrant_version_runtime, and match boolean
    """
    env_tag = os.getenv("QDRANT_TAG", "")
    
    try:
        r = requests.get("http://qdrant:6333/telemetry", timeout=3)
        r.raise_for_status()
        telemetry_data = r.json()
        # Qdrant telemetry structure: {"result": {"app": {"version": "1.8.4"}}}
        ver = (
            telemetry_data.get("result", {}).get("app", {}).get("version")
            or telemetry_data.get("app", {}).get("version") 
            or telemetry_data.get("version") 
            or ""
        )
    except Exception as e:
        logger.warning(f"Failed to fetch Qdrant telemetry: {e}")
        ver = ""
    
    return {
        "qdrant_tag_env": env_tag,
        "qdrant_version_runtime": ver,
        "match": _normalize_tag(env_tag) == _normalize_tag(ver),
    }

