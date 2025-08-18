#!/usr/bin/env bash

set -o pipefail

ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
mkdir -p "$REPORTS_DIR"

LINT_LOG="$REPORTS_DIR/frontend_lint.txt"
TYPES_LOG="$REPORTS_DIR/frontend_types.txt"
UNIT_LOG="$REPORTS_DIR/frontend_unit.txt"
SUMMARY_MD="$REPORTS_DIR/frontend_summary.md"

rm -f "$LINT_LOG" "$TYPES_LOG" "$UNIT_LOG" "$SUMMARY_MD"

run_step() {
  local step_name="$1"
  local make_target="$2"
  local log_file="$3"

  echo "Running $step_name..." >&2
  tmp_out="$(mktemp)"
  if make "$make_target" >"$tmp_out" 2>&1; then
    echo "OK" >"$log_file"
    echo "[$step_name] ✅ OK" >&2
    echo "__OK__"  # marker to caller
  else
    mv "$tmp_out" "$log_file"
    echo "[$step_name] ❌ Failed. See: $log_file" >&2
    echo "__FAIL__"  # marker to caller
  fi
  [ -f "$tmp_out" ] && rm -f "$tmp_out"
}

lint_status=$(run_step "Lint" "fe-lint" "$LINT_LOG")
types_status=$(run_step "Types" "fe-types" "$TYPES_LOG")
unit_status=$(run_step "Unit" "fe-test" "$UNIT_LOG")

status_to_emoji() {
  if [[ "$1" == "__OK__" ]]; then echo "✅"; else echo "❌"; fi
}

head_or_full() {
  local f="$1"
  if [[ ! -s "$f" ]]; then
    echo "(empty)"
    return
  fi
  # If file contains only "OK"
  if [[ "$(cat "$f" | tr -d '\n' | tr -d '\r')" == "OK" ]]; then
    echo "OK"
    return
  fi
  echo '```'
  head -n 80 "$f"
  if [[ $(wc -l < "$f") -gt 80 ]]; then
    echo "... (truncated)"
  fi
  echo '```'
}

{
  echo "# Frontend Quality Summary"
  echo
  echo "## Lint $(status_to_emoji "$lint_status")"
  head_or_full "$LINT_LOG"
  echo
  echo "## Types $(status_to_emoji "$types_status")"
  head_or_full "$TYPES_LOG"
  echo
  echo "## Unit $(status_to_emoji "$unit_status")"
  head_or_full "$UNIT_LOG"
} > "$SUMMARY_MD"

echo "Summary written to $SUMMARY_MD" >&2

# exit code: non-zero if any step failed
exit_code=0
[[ "$lint_status" != "__OK__" ]] && exit_code=1
[[ "$types_status" != "__OK__" ]] && exit_code=1
[[ "$unit_status" != "__OK__" ]] && exit_code=1
exit $exit_code


