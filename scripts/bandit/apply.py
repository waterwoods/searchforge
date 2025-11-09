#!/usr/bin/env python3
"""
Bandit policy applier with safety gates.

Performs health checks, optional dry-run, and policy application via the admin API.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import io_utils


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str) -> dict:
    request = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8") or "{}")


def _health_gate(base: str) -> tuple[bool, dict, dict]:
    emb = _get_json(f"{base}/api/health/embeddings")
    ready = _get_json(f"{base}/ready")
    ok = bool(emb.get("ok")) and bool(ready.get("ok"))
    return ok, emb, ready


def _current_policy(base: str) -> dict:
    return _get_json(f"{base}/api/admin/policy/current")


def _audit(tag: str, **fields: str) -> None:
    pairs = " ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[{tag}] {pairs}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bandit safe policy switcher")
    parser.add_argument("--arm", required=True, choices={"fast_v1", "balanced_v1", "quality_v1"})
    parser.add_argument("--base", default="http://localhost:8000")
    parser.add_argument("--dryrun", action="store_true", help="Validate but do not apply")
    parser.add_argument("--print-json", action="store_true", help="Emit result JSON to stdout")
    args = parser.parse_args()

    state_path = io_utils.resolve_state_path()

    with io_utils.file_lock(state_path, exclusive=True):
        try:
            ok, _emb, _ready = _health_gate(args.base)
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            _audit("SELECT_ABORT", arm=args.arm, reason=f"health_check_error:{exc}", base=args.base)
            sys.exit(3)

        if not ok:
            _audit("SELECT_ABORT", arm=args.arm, reason="health_gate_failed", base=args.base)
            if args.print_json:
                json.dump(
                    {"ok": False, "applied": None, "previous": None, "reason": "health_gate_failed"},
                    sys.stdout,
                    ensure_ascii=False,
                )
                sys.stdout.write("\n")
            sys.exit(3)

        try:
            current = _current_policy(args.base)
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            _audit("SELECT_ABORT", arm=args.arm, reason=f"fetch_current_error:{exc}", base=args.base)
            sys.exit(4)

        prev_arm = current.get("policy_name", "unknown")
        timestamp = datetime.now(timezone.utc).isoformat()

        if args.dryrun:
            _audit("BANDIT_SELECT", arm=args.arm, applied_at=timestamp, prev=prev_arm, base=args.base, mode="dryrun")
            payload = {"ok": True, "dryrun": True, "applied": None, "previous": prev_arm, "ts": timestamp}
            if args.print_json:
                json.dump(payload, sys.stdout, ensure_ascii=False)
                sys.stdout.write("\n")
            return

        try:
            _post_json(f"{args.base}/api/admin/policy/apply?name={urllib.parse.quote(args.arm)}")
            after = _current_policy(args.base)
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            _audit("SELECT_ABORT", arm=args.arm, reason=f"apply_error:{exc}", base=args.base)
            sys.exit(5)

        applied_arm = after.get("policy_name")
        if applied_arm != args.arm:
            _audit("SELECT_ABORT", arm=args.arm, reason=f"post_check_mismatch:{applied_arm}", base=args.base)
            if args.print_json:
                json.dump(
                    {"ok": False, "applied": applied_arm, "previous": prev_arm, "ts": timestamp},
                    sys.stdout,
                    ensure_ascii=False,
                )
                sys.stdout.write("\n")
            sys.exit(6)

        _audit("BANDIT_SELECT", arm=args.arm, applied_at=timestamp, prev=prev_arm, base=args.base)

        if args.print_json:
            json.dump(
                {"ok": True, "applied": args.arm, "previous": prev_arm, "ts": timestamp},
                sys.stdout,
                ensure_ascii=False,
            )
            sys.stdout.write("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:  # pragma: no cover
        sys.exit(130)

