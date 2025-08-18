#!/usr/bin/env bash
set -euo pipefail

echo "[lint] Python: ruff + black + mypy"
python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
python3 -m pip install -r backend/requirements.txt >/dev/null 2>&1 || true
python3 -m pip install black ruff mypy >/dev/null 2>&1 || true

TARGETS=(
  backend/app/admin_api
  backend/app/api/v1/api.py
  backend/app/core/db.py
)

python3 -m ruff check "${TARGETS[@]}" || exit 1
python3 -m black --check "${TARGETS[@]}" || exit 1
python3 -m mypy "${TARGETS[@]}" || true

echo "[lint] JS/TS: eslint + prettier"
if [ -f frontend/package.json ]; then
  cd frontend
  npm ci --no-audit --no-fund --prefer-offline
  npx eslint . || exit 1
  npx prettier -c . || exit 1
fi

echo "[lint] Secret scan (soft)"
if command -v trufflehog >/dev/null 2>&1; then
  trufflehog filesystem --no-update --fail=false . || true
fi

echo "Lint done"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Lint: Backend (ruff/black/mypy soft)"
if [ -d "$ROOT_DIR/backend" ]; then
  pushd "$ROOT_DIR/backend" >/dev/null
  if command -v ruff >/dev/null 2>&1; then ruff check . || true; fi
  if command -v ruff >/dev/null 2>&1; then ruff format --check . || true; fi
  if command -v black >/dev/null 2>&1; then black --check . || true; fi
  if command -v mypy >/dev/null 2>&1; then mypy . || true; fi
  popd >/dev/null
else
  echo "(skip) backend not found"
fi

echo "==> Lint: Frontend (eslint/prettier soft)"
if [ -d "$ROOT_DIR/frontend" ]; then
  pushd "$ROOT_DIR/frontend" >/dev/null
  if command -v npm >/dev/null 2>&1; then
    npm run -s lint || true
    if command -v npx >/dev/null 2>&1; then npx prettier -c . || true; fi
  fi
  popd >/dev/null
else
  echo "(skip) frontend not found"
fi

echo "==> Secret scan (trufflehog soft)"
if command -v trufflehog >/dev/null 2>&1; then
  trufflehog filesystem --no-update --since-commit HEAD~50 || true
else
  echo "(skip) trufflehog not installed"
fi

echo "OK"

