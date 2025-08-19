#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=admin/backend

echo "[backend] install deps"
pip install -r admin/backend/requirements.txt >/dev/null

echo "[backend] lint & type-check"
ruff admin/backend --fix
black admin/backend --check
mypy admin/backend

echo "[backend] tests"
pytest -q admin/backend

echo "[frontend] install deps"
pushd admin/frontend >/dev/null
npm i >/dev/null

echo "[frontend] lint"
npx eslint . --max-warnings=0
npx prettier -c "**/*.{js,jsx,ts,tsx,css,md,json}"

echo "[frontend] tests"
npm test --silent -- --ci
popd >/dev/null

