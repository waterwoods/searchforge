"""
Quiet Experiment Router - Minimal stub for Mini Dashboard
"""

import asyncio
import logging
from typing import Dict, Any
from dataclasses import dataclass, field
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ops/quiet_mode", tags=["quiet_experiment"])

# Global state (minimal implementation)
@dataclass
class QuietModeState:
    """Quiet mode state."""
    enabled: bool = False
    locked_params: Dict[str, Any] = field(default_factory=dict)

_quiet_mode = QuietModeState()
_state_lock = asyncio.Lock()


@router.get("/status")
async def get_quiet_status() -> Dict[str, Any]:
    """Get quiet mode status."""
    async with _state_lock:
        return {
            "ok": True,
            "enabled": _quiet_mode.enabled,
            "locked_params": _quiet_mode.locked_params
        }


@router.post("/enable")
async def enable_quiet_mode() -> Dict[str, Any]:
    """Enable quiet mode."""
    async with _state_lock:
        _quiet_mode.enabled = True
        logger.info("[QUIET] Quiet mode enabled")
        return {
            "ok": True,
            "enabled": True,
            "message": "Quiet mode enabled"
        }


@router.post("/disable")
async def disable_quiet_mode() -> Dict[str, Any]:
    """Disable quiet mode."""
    async with _state_lock:
        _quiet_mode.enabled = False
        logger.info("[QUIET] Quiet mode disabled")
        return {
            "ok": True,
            "enabled": False,
            "message": "Quiet mode disabled"
        }


async def start_experiment_loop():
    """Background loop placeholder (not used in Mini Dashboard)."""
    while True:
        await asyncio.sleep(60)  # No-op loop





































