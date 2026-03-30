"""
Role C — bounded LLM customer lines for Add-Car simulation only.

Generates the next customer message given prior replay turns. Uses the same
OpenAI credentials as triage when available; otherwise callers should surface
an honest unavailable state.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

# Aligned with simulation UI persona ids
PERSONA_GUIDANCE_ZH: dict[str, str] = {
    "price_sensitive": "价格敏感：关心保费、deductible、比价，语气务实但仍在办加车。",
    "elderly": "年长客户：口语、可能少量错别字，动作慢一些，但信息真实。",
    "materials_first": "材料先发型：强调微信/已上传过驾照或 dec，担心办公室没收到。",
    "family_vehicle": "家庭车辆：配偶/家里另一台车、谁主开等会自然提到。",
    "fragmented": "信息很碎：每次只给一小点信息，短句多，但仍在补充加车所需字段。",
    "mixed_zh_en": "中英混说：叙述中文、车险术语常用英文（VIN、ZIP、coverage 等）。",
}

DIFFICULTY_GUIDANCE: dict[str, str] = {
    "smooth": "顺畅：配合度较高，信息相对集中，少量口语即可。",
    "realistic": "真实：可有口误后自纠、改口、碎句、追问一句半句，仍围绕加车。",
    "tough": "刁钻：更挑剔、多追问、价格/材料/家庭压力更明显，但仍只谈加车与投保准备。",
}

VALID_PERSONAS = frozenset(PERSONA_GUIDANCE_ZH.keys())
VALID_DIFFICULTIES = frozenset(DIFFICULTY_GUIDANCE.keys())


def _strip_customer_message(raw: str, max_chars: int = 520) -> str:
    t = (raw or "").strip()
    t = re.sub(r"^[\s\"'「」]+|[\s\"'」]+$", "", t)
    # Single-line-ish for triage UX
    t = re.sub(r"\s+", " ", t)
    if len(t) > max_chars:
        t = t[: max_chars - 1].rstrip() + "…"
    return t


def generate_role_c_customer_turn(
    *,
    persona_id: str,
    optional_note: str,
    difficulty: str,
    max_turns: int,
    next_customer_turn_1based: int,
    conversation_turns: list[dict[str, Any]],
    client_label: str = "California auto insurance broker assistant",
    client_pack_id: str | None = None,
) -> tuple[str, bool, str | None]:
    """
    Returns (customer_message, llm_attempted, model_name_or_none).

    - llm_attempted False + empty message: no API key / import failure — not an LLM call.
    - llm_attempted True + empty message: called model but got nothing or exception.
    """
    pid = (persona_id or "").strip()
    if pid not in VALID_PERSONAS:
        pid = "price_sensitive"
    diff = (difficulty or "").strip().lower()
    if diff not in VALID_DIFFICULTIES:
        diff = "realistic"

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        logger.info("Role C simulation: no OPENAI_API_KEY, skipping LLM")
        return "", False, None

    try:
        from openai import OpenAI
    except ImportError as e:
        logger.warning("Role C simulation: OpenAI import failed: %s", e)
        return "", False, None

    model = os.getenv("ROLE_C_SIMULATION_MODEL") or os.getenv("LLM_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    note = (optional_note or "").strip()[:200]
    persona_zh = PERSONA_GUIDANCE_ZH[pid]
    diff_zh = DIFFICULTY_GUIDANCE[diff]

    lines: list[str] = []
    for t in conversation_turns:
        role = (t.get("role") or "").strip().lower()
        text = (t.get("text") or "").strip()
        if not text:
            continue
        if role == "customer":
            lines.append(f"客户: {text}")
        elif role == "system":
            lines.append(f"办公室/系统回复摘要: {text}")

    transcript = "\n".join(lines) if lines else "（尚无对话，这是第一轮客户发言。）"

    pack_hint = ""
    cid = (client_pack_id or "").strip()[:64]
    if cid:
        pack_hint = (
            f"\n- Demo uses client pack id `{cid}`; keep tone consistent with CA auto Add-Car intake. "
            "Do not invent carrier names or policy numbers."
        )

    system = f"""You are a simulator for QA/demo only. You play ONE customer turn.

Context: North-American-Chinese customer texting a {client_label} about **adding a new vehicle / Add-Car quote intake** in California. Not a chatbot for general knowledge.

Hard rules:
- Output ONLY the customer's next message text. No labels, no quotes, no JSON, no bullet list.
- Stay strictly on Add-Car / new vehicle quote prep (vehicle, zip, dates, drivers, VIN/DL/materials, coverage worries). Do NOT discuss unrelated topics (weather, politics, coding, other insurance lines except as one short aside that still ties back to this car).
- {persona_zh}
- {diff_zh}{pack_hint}
- This is customer turn {next_customer_turn_1based} of at most {max_turns}. If enough core details already appear in the transcript, you may confirm, correct, or ask one focused follow-up — still sound human.
- Prefer 1–3 short sentences. Mixed Chinese/English allowed when it fits the persona.
- No role-play meta ("作为AI"). No greeting spam if mid-conversation."""

    user = f"""Optional scenario note from the demo operator (may be empty): {note or "（无）"}

Transcript so far:
{transcript}

Write the customer's NEXT message only."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.65,
            max_tokens=220,
        )
        content = ""
        if response.choices:
            content = (response.choices[0].message.content or "").strip()
        out = _strip_customer_message(content)
        if not out:
            return "", True, model
        return out, True, model
    except Exception as e:
        logger.warning("Role C simulation LLM call failed: %s", e)
        return "", True, None
