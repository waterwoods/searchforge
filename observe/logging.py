from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Event:
    run_id: str
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "created_at": self.created_at,
        }


class EventLogger:
    """Append-only JSONL event logger."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._locks: Dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def initialize(self, run_id: str) -> None:
        path = self._event_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    def log_event(self, run_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        event = Event(run_id=run_id, event_type=event_type, payload=payload)
        path = self._event_path(run_id)
        line = json.dumps(event.to_dict())
        lock = self._get_lock(run_id)
        with lock:
            with path.open("a", encoding="utf-8") as fp:
                fp.write(f"{line}\n")

    def log_stage_event(
        self,
        run_id: str,
        stage: str,
        status: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        event_type = f"{stage.upper()}_{status.upper()}"
        body = dict(payload or {})
        body.setdefault("stage", stage.upper())
        self.log_event(run_id, event_type, body)

    def read_events(self, run_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        path = self._event_path(run_id)
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as fp:
            lines = [line.strip() for line in fp if line.strip()]
        if limit is not None and limit > 0:
            lines = lines[-limit:]
        events: List[Dict[str, Any]] = []
        for line in lines:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events

    def _event_path(self, run_id: str) -> Path:
        return self.base_dir / f"{run_id}.jsonl"

    def _get_lock(self, run_id: str) -> threading.Lock:
        with self._locks_guard:
            if run_id not in self._locks:
                self._locks[run_id] = threading.Lock()
            return self._locks[run_id]

