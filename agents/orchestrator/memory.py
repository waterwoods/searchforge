from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class MemoryRecord:
    run_id: str
    plan: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "plan": self.plan,
            "metadata": self.metadata,
        }


class RunMemory:
    """Simple JSONL-backed store for orchestrator runs."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_dir / "runs.jsonl"
        self._lock = threading.Lock()

    def register_plan(self, run_id: str, plan: Dict[str, Any]) -> None:
        record = MemoryRecord(run_id=run_id, plan=plan)
        self._append_record(record)
        self._write_record(record)

    def get(self, run_id: str) -> Optional[MemoryRecord]:
        record_path = self._record_path(run_id)
        if record_path.exists():
            with record_path.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
            return MemoryRecord(
                run_id=run_id,
                plan=data.get("plan") or {},
                metadata=data.get("metadata") or {},
            )

        if not self.index_path.exists():
            return None
        with self.index_path.open("r", encoding="utf-8") as fp:
            for line in fp:
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get("run_id") == run_id:
                    return MemoryRecord(
                        run_id=run_id,
                        plan=data.get("plan") or {},
                        metadata=data.get("metadata") or {},
                    )
        return None

    def update_metadata(self, run_id: str, updates: Dict[str, Any]) -> None:
        with self._lock:
            record = self.get(run_id) or MemoryRecord(run_id=run_id)
            record.metadata.update(updates)
            self._write_record(record)

    def _append_record(self, record: MemoryRecord) -> None:
        line = json.dumps(record.to_dict())
        with self._lock:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            with self.index_path.open("a", encoding="utf-8") as fp:
                fp.write(f"{line}\n")

    def _write_record(self, record: MemoryRecord) -> None:
        path = self._record_path(record.run_id)
        with path.open("w", encoding="utf-8") as fp:
            json.dump(record.to_dict(), fp)

    def _record_path(self, run_id: str) -> Path:
        return self.base_dir / f"{run_id}.json"

