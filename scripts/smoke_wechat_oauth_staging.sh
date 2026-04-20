#!/usr/bin/env bash
# Bounded smoke: optional WeChat binding start endpoint against a deployed (or local) API.
# Does not call Tencent; does not complete OAuth. Use after setting Cloud Run env from .env.cloudrun.
#
# Usage:
#   API_BASE_URL=https://your-service.run.app bash scripts/smoke_wechat_oauth_staging.sh
#   # or
#   bash scripts/smoke_wechat_oauth_staging.sh https://your-service.run.app
#
# Expectations (honest):
# - With WECHAT_APP_ID+SECRET on server: JSON has authorize_url (https://open.weixin.qq.com/...) and dev_simulate=false
# - Without credentials but WECHAT_BINDING_ALLOW_SIMULATE=1: dev_simulate=true, authorize_url null
# - Without credentials and simulate off: HTTP 503 wechat_oauth_not_configured
# - client_id must match a pack with wechat_binding_mode=live (e.g. socal_precision)

set -euo pipefail

API="${API_BASE_URL:-${1:-}}"
if [ -z "$API" ]; then
    echo "Usage: API_BASE_URL=https://your-api.run.app bash scripts/smoke_wechat_oauth_staging.sh"
    echo "   or: bash scripts/smoke_wechat_oauth_staging.sh https://your-api.run.app"
    exit 1
fi
API="${API%/}"
SID="${SMOKE_SESSION_ID:-staging_wechat_smoke01}"
CLIENT="${SMOKE_CLIENT_ID:-socal_precision}"
URL="${API}/api/inbox/wechat/binding/start?session_id=${SID}&client_id=${CLIENT}"

echo "GET ${URL}"
code=$(curl -sS -o /tmp/wechat_smoke_body.json -w "%{http_code}" "$URL") || true
echo "HTTP ${code}"
if command -v python3 &>/dev/null; then
    python3 <<'PY' 2>/dev/null || cat /tmp/wechat_smoke_body.json
import json
from pathlib import Path
p = Path("/tmp/wechat_smoke_body.json")
try:
    print(json.dumps(json.loads(p.read_text()), indent=2, ensure_ascii=False))
except Exception:
    print(p.read_text()[:2000])
PY
else
    cat /tmp/wechat_smoke_body.json
fi
echo ""

if [ "$code" = "200" ]; then
    if python3 <<'PY' 2>/dev/null
import json
j = json.load(open("/tmp/wechat_smoke_body.json"))
raise SystemExit(0 if j.get("dev_simulate") or j.get("authorize_url") else 1)
PY
    then
        echo "OK: start endpoint returned dev_simulate or authorize_url"
        exit 0
    fi
    echo "WARN: 200 but unexpected JSON shape"
    exit 1
fi

if [ "$code" = "503" ]; then
    echo "Expected when live client but no WeChat credentials and simulate disabled"
    exit 0
fi

if [ "$code" = "403" ]; then
    echo "wechat_binding_not_live_for_client — use SMOKE_CLIENT_ID=socal_precision or enable live in client pack"
    exit 1
fi

exit 1
