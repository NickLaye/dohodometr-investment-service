#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPORT_DIR="$ROOT_DIR/reports"
BACKEND_DIR="$ROOT_DIR/backend"

mkdir -p "$REPORT_DIR"

echo "[pytest_fail_report] Preparing backend venv..."
if [ -f "$BACKEND_DIR/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$BACKEND_DIR/.venv/bin/activate"
fi

cd "$BACKEND_DIR"

echo "[pytest_fail_report] Exporting test environment..."
export ENVIRONMENT="testing"
export DATABASE_URL="sqlite:///./test.db"
export REDIS_URL="redis://localhost:6379/1"

echo "[pytest_fail_report] Running full backend tests..."
set +e
pytest -q
STATUS=$?
set -e

if [ $STATUS -eq 0 ]; then
  echo "[pytest_fail_report] ✅ All tests passed"
  echo -n > "$REPORT_DIR/backend_failed.txt"
  exit 0
fi

echo "[pytest_fail_report] Tests failed. Generating JUnit XML..."
pytest -q --junitxml="$REPORT_DIR/junit-backend.xml" || true

echo "[pytest_fail_report] Parsing failures..."
export REPORT_DIR
FAILED_LIST=$(python - <<'PY'
import xml.etree.ElementTree as ET
import os
rep = os.environ['REPORT_DIR']
tree = ET.parse(os.path.join(rep, 'junit-backend.xml'))
root = tree.getroot()
failed = []
for tc in root.iter('testcase'):
    has_fail = any(child.tag in ('failure','error') for child in tc)
    if has_fail:
        cls = tc.get('classname') or ''
        name = tc.get('name') or ''
        file_attr = tc.get('file') or ''
        if file_attr:
            failed.append(f"{file_attr}::{name}")
        elif cls:
            failed.append(f"{cls}::{name}")
        else:
            failed.append(name)
print('\n'.join(sorted(set(failed))))
PY
)

printf "%s\n" "$FAILED_LIST" > "$REPORT_DIR/backend_failed.txt"
echo "[pytest_fail_report] Wrote failed tests to $REPORT_DIR/backend_failed.txt"

echo "[pytest_fail_report] Unique failure stack traces (first 30 lines each):"
python - <<'PY' | tee "$REPORT_DIR/backend_fail_stacks.txt"
import xml.etree.ElementTree as ET
import os
rep = os.environ['REPORT_DIR']
tree = ET.parse(os.path.join(rep, 'junit-backend.xml'))
root = tree.getroot()
seen_msgs = set()
for tc in root.iter('testcase'):
    for tag in ('failure','error'):
        el = tc.find(tag)
        if el is not None:
            msg = (el.text or '').strip()
            key = msg.split('\n')[:30]
            key_str = '\n'.join(key)
            if key_str in seen_msgs:
                continue
            seen_msgs.add(key_str)
            title = f"{tc.get('classname','')}::{tc.get('name','')}".strip(':')
            print('='*80)
            print(title)
            print('-'*80)
            print('\n'.join(key))
PY

exit $STATUS


