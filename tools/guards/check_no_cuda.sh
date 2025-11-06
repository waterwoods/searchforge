#!/usr/bin/env bash
set -euo pipefail

echo "[GUARD] Checking for CUDA packages..."
pip freeze | tee /tmp/freeze.txt

if egrep -i '^(nvidia|torch[-_]?cuda)' /tmp/freeze.txt; then
  echo '[GUARD] ERROR: CUDA packages detected'
  exit 1
fi

echo "[GUARD] Checking torch CUDA availability..."
python - <<'PY'
try:
  import torch
  import json
  cuda_available = torch.cuda.is_available()
  cuda_version = getattr(torch.version, "cuda", None)
  result = {
    "torch_installed": True,
    "cuda_available": cuda_available,
    "cuda_version": cuda_version
  }
  print(json.dumps(result, indent=2))
  if cuda_available or cuda_version is not None:
    print("ERROR: CUDA visible in runtime", file=__import__('sys').stderr)
    exit(1)
except ImportError:
  print('{"torch_installed": false}')
PY

echo '[GUARD] OK-no-CUDA'

