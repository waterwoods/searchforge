from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any
import os
import json
import requests  # 已在项目中使用
DEFAULT_ADMIN_URL = os.environ.get("RAG_ADMIN_URL", "http://localhost:8000/admin/params")

@dataclass
class ParamChange:
    """单次参数修改建议"""
    top_k: Optional[int] = None
    batch_size: Optional[int] = None
    note: str = ""

class ParameterExecutor:
    """
    最小执行器：
    - local_hook: 可注入本地函数(单测/离线演示)
    - rag_api: 调用 /admin/params（后续接线时开启）
    """
    def __init__(self, mode: str = "local", local_hook: Optional[Callable[[ParamChange], bool]] = None, dry_run: bool = True):
        self.mode = mode
        self.local_hook = local_hook or (lambda _: True)
        self.dry_run = dry_run

    def apply(self, change: ParamChange) -> bool:
        if self.dry_run:
            # 只打印，不落地
            print(f"[DRY-RUN] ParamChange => {change}")
            return True

        if self.mode == "local":
            return bool(self.local_hook(change))

        if self.mode == "rag_api":
            payload: Dict[str, Any] = {k: v for k, v in change.__dict__.items() if v is not None and k != "note"}
            payload["note"] = change.note
            r = requests.post(DEFAULT_ADMIN_URL, json=payload, timeout=5)
            ok = r.status_code // 100 == 2
            if not ok:
                print(f"[Executor] rag_api apply failed: {r.status_code} {r.text}")
            return ok

        print(f"[Executor] unsupported mode={self.mode}")
        return False
