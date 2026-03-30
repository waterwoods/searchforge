"""
Role C — reusable controlled LLM simulation service (Add-Car only).

Single core for:
- HTTP: POST /api/inbox/simulation-role-c-customer (simulation tab)
- Scripts/tests: import `next_role_c_customer_line` and optionally drive triage via HTTP or in-process calls

Knobs (intentionally few): persona_id, difficulty, max_turns, optional_note.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from services.fiqa_api.inbox_triage.role_c_customer_llm import (
    VALID_DIFFICULTIES,
    VALID_PERSONAS,
    generate_role_c_customer_turn,
)

# Aligned with SimulationRoleCCustomerRequest (routes/inbox_triage.py)
ROLE_C_MAX_TURNS_MIN = 3
# Allow headroom for script-injected formal-submit customer lines in truth-chain batteries (still bounded).
ROLE_C_MAX_TURNS_MAX = 12

__all__ = [
    "ROLE_C_MAX_TURNS_MAX",
    "ROLE_C_MAX_TURNS_MIN",
    "RoleCMaxTurnsReached",
    "RoleCNextTurnResult",
    "VALID_DIFFICULTIES",
    "VALID_PERSONAS",
    "clamp_max_turns",
    "next_role_c_customer_line",
    "normalize_role_c_transcript",
]


class RoleCMaxTurnsReached(ValueError):
    """Raised when the next customer turn would exceed max_turns."""


@dataclass(frozen=True)
class RoleCNextTurnResult:
    customer_message: str
    llm_attempted: bool
    model: str | None
    turn_index: int
    max_turns: int


def _strip_collapse(s: str) -> str:
    t = (s or "").strip()
    return re.sub(r"\s+", " ", t)


def normalize_role_c_transcript(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only customer/system pairs with non-empty text (same contract as the API route)."""
    out: list[dict[str, Any]] = []
    for t in raw:
        role = (t.get("role") or "").strip().lower()
        text = _strip_collapse(str(t.get("text") or ""))
        if not text:
            continue
        if role in ("system", "customer"):
            out.append({"role": role, "text": text})
    return out


def clamp_max_turns(n: int) -> int:
    return max(ROLE_C_MAX_TURNS_MIN, min(ROLE_C_MAX_TURNS_MAX, int(n)))


def next_role_c_customer_line(
    *,
    persona_id: str,
    optional_note: str,
    difficulty: str,
    max_turns: int,
    conversation_turns: list[dict[str, Any]],
    client_id: str | None = None,
) -> RoleCNextTurnResult:
    """
    Compute the next Role C customer message.

    Raises RoleCMaxTurnsReached if the replay is already at max customer turns.
    """
    mt = clamp_max_turns(max_turns)
    hist = normalize_role_c_transcript(conversation_turns)
    cust_done = sum(1 for t in hist if t["role"] == "customer")
    next_n = cust_done + 1
    if next_n > mt:
        raise RoleCMaxTurnsReached(f"next turn {next_n} exceeds max_turns={mt}")

    msg, llm_attempted, model = generate_role_c_customer_turn(
        persona_id=persona_id,
        optional_note=optional_note or "",
        difficulty=difficulty,
        max_turns=mt,
        next_customer_turn_1based=next_n,
        conversation_turns=hist,
        client_pack_id=(client_id or "").strip() or None,
    )
    return RoleCNextTurnResult(
        customer_message=msg,
        llm_attempted=llm_attempted,
        model=model,
        turn_index=next_n,
        max_turns=mt,
    )
