"""
Knowledge layer reference paths — where retrievable knowledge lives.

Used for future Qdrant ingestion. Inbox triage does NOT use RAG today.
Rules and config drive triage; knowledge is for explanatory retrieval.

See: docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md
"""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_ROOT = _REPO_ROOT / "knowledge"


def get_knowledge_paths_by_pack() -> dict[str, list[Path]]:
    """
    Return paths to knowledge files by pack (common, industry, client).

    Used by future ingestion to know what to embed and upsert.
    Returns only existing .md files.
    """
    paths: dict[str, list[Path]] = {"common": [], "industry": [], "client": []}
    if not KNOWLEDGE_ROOT.exists():
        return paths

    # Common
    common_dir = KNOWLEDGE_ROOT / "common"
    if common_dir.exists():
        paths["common"] = sorted(common_dir.glob("*.md"))

    # Industry (insurance)
    insurance_dir = KNOWLEDGE_ROOT / "industries" / "insurance"
    if insurance_dir.exists():
        paths["industry"] = sorted(insurance_dir.glob("*.md"))

    # Client (chen_kui)
    chen_kui_dir = KNOWLEDGE_ROOT / "clients" / "chen_kui"
    if chen_kui_dir.exists():
        paths["client"] = sorted(chen_kui_dir.glob("*.md"))

    return paths


def list_retrieval_ready_files() -> list[Path]:
    """Return all .md files under knowledge/ (excluding README.md)."""
    paths = get_knowledge_paths_by_pack()
    all_files: list[Path] = []
    for pack_list in paths.values():
        for p in pack_list:
            if p.name != "README.md":
                all_files.append(p)
    return sorted(all_files)
