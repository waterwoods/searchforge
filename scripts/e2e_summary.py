#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def main():
    runs = Path(".runs")

    def read_json(name: str):
        path = runs / name
        return json.loads(path.read_text(encoding="utf-8"))

    direct = read_json("direct_compat.json")
    on = read_json("realcheck_proxy_on.json")
    off = read_json("realcheck_proxy_off.json")
    report = read_json("realcheck_report.json")

    ok_direct = bool(direct.get("ok"))
    success_on = on.get("success_rate", 0.0)
    success_off = off.get("success_rate", 0.0)
    pass_simple = bool(report.get("pass_simple"))

    ok = ok_direct and success_on >= 0.95 and success_off >= 0.95 and pass_simple

    result = {
        "ok": ok,
        "direct_ok": ok_direct,
        "proxy_on_success": success_on,
        "proxy_off_success": success_off,
        "pass_simple": pass_simple,
    }

    runs.mkdir(exist_ok=True)
    (runs / "e2e_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("E2E MINI PASS" if ok else "E2E MINI FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

