import os
import re
import pathlib

from services.fiqa_api.settings import REPO_ROOT

ENV_FILE_DEFAULT = str((REPO_ROOT / ".env").resolve())


def _parse_line(line: str):
    line = line.strip()
    if not line or line.startswith("#"):
        return None, None
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
    if not m:
        return None, None
    k, v = m.group(1), m.group(2)
    # strip surrounding quotes if any
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1]
    return k, v


def load_env_from_file(path: str | None = None) -> dict:
    path = path or os.getenv("ENV_FILE", ENV_FILE_DEFAULT)
    p = pathlib.Path(path)
    loaded: dict[str, str] = {}
    if not p.exists():
        return loaded
    for line in p.read_text().splitlines():
        k, v = _parse_line(line)
        if not k:
            continue
        # do not overwrite existing process env
        if os.environ.get(k) is None:
            os.environ[k] = v
            loaded[k] = v
        else:
            loaded[k] = os.environ[k]
    return loaded


def _to_int(value: str, default: int) -> int:
    try:
        cleaned = (value or "").strip()
        return int(cleaned) if cleaned else default
    except ValueError:
        return default


def _to_float(value: str, default: float | None = None) -> float | None:
    cleaned = (value or "").strip()
    if not cleaned:
        return default
    try:
        return float(cleaned)
    except ValueError:
        return default


def _mask(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:6] + "..." + key[-4:]


def get_llm_conf() -> dict:
    # load file each time (cheap; ensures hot reload without restart)
    loaded = load_env_from_file()

    model = (os.getenv("LLM_MODEL") or "").strip() or "gpt-4o-mini"
    api_key = (os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    max_tokens = _to_int(os.getenv("LLM_MAX_TOKENS", "256"), 256)
    budget = _to_float(os.getenv("LLM_BUDGET_USD", "0.0"), 0.0) or 0.0

    input_cost = _to_float(os.getenv("LLM_INPUT_PER_MTOK") or os.getenv("LLM_INPUT_PERK") or "")
    output_cost = _to_float(os.getenv("LLM_OUTPUT_PER_MTOK") or os.getenv("LLM_OUTPUT_PERK") or "")

    present = bool(api_key)
    src = "file" if any(key in loaded for key in ("LLM_MODEL", "LLM_API_KEY", "OPENAI_API_KEY")) else "env"

    return {
        "model": model,
        "api_key": api_key,
        "api_key_masked": _mask(api_key),
        "max_tokens": max_tokens,
        "budget_usd": budget,
        "key_present": present,
        "source": src,
        "input_per_mtok": input_cost,
        "output_per_mtok": output_cost,
    }

