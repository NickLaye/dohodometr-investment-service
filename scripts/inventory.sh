#!/usr/bin/env bash

# Inventory script: collects environment and repo metadata into inventory.txt at repo root

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_FILE="$REPO_ROOT/inventory.txt"

print_section() {
  local title="$1"
  {
    echo "==== $title ===="
  } >> "$OUTPUT_FILE"
}

print_kv() {
  local key="$1"; shift
  local value="$*"
  echo "$key: $value" >> "$OUTPUT_FILE"
}

run_version() {
  local label="$1"; shift
  local cmd=("$@")
  if command -v "${cmd[0]}" >/dev/null 2>&1; then
    local ver
    ver="$(${cmd[@]} 2>&1 | head -n 1)"
    print_kv "$label" "$ver"
  else
    print_kv "$label" "not installed"
  fi
}

# Reset output
{
  echo "Project inventory report"
  echo "Generated: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo "Repository root: $REPO_ROOT"
  echo ""
} > "$OUTPUT_FILE"

# 1) System versions
print_section "System Versions"
run_version "python" python --version
run_version "python3" python3 --version
run_version "node" node -v
run_version "npm" npm -v
run_version "pnpm" pnpm -v
run_version "docker" docker -v

# docker compose (plugin) and legacy docker-compose
if command -v docker >/dev/null 2>&1; then
  dc_ver="$(docker compose version 2>&1 | head -n 1)"
  if echo "$dc_ver" | grep -qi "compose"; then
    print_kv "docker compose" "$dc_ver"
  else
    print_kv "docker compose" "unavailable"
  fi
else
  print_kv "docker compose" "docker not installed"
fi
run_version "docker-compose" docker-compose -v
run_version "java" java -version
echo "" >> "$OUTPUT_FILE"

# 2) Dependency managers and lock files
print_section "Dependency Managers and Lock Files"
IGNORE_DIRS=(
  -name node_modules -o -name .git -o -name .venv -o -name venv -o -name .tox -o -name dist -o -name build -o -name .next -o -name coverage -o -name frontend/coverage -o -name backend/.hypothesis
)

dependency_patterns=(
  'package.json' 'package-lock.json' 'npm-shrinkwrap.json' 'yarn.lock' 'pnpm-lock.yaml' 'pnpm-workspace.yaml'
  'Pipfile' 'Pipfile.lock' 'poetry.lock' 'requirements*.txt' 'requirements.in' 'pyproject.toml'
  'go.mod' 'go.sum' 'Cargo.toml' 'Cargo.lock' 'composer.json' 'composer.lock' 'Gemfile' 'Gemfile.lock'
  'build.gradle' 'build.gradle.kts' 'gradle.lockfile' 'pom.xml'
)

found_any=false
for pat in "${dependency_patterns[@]}"; do
  # shellcheck disable=SC2016
  results=$(find "$REPO_ROOT" \
    \( -type d \( -name node_modules -o -name .git -o -name .venv -o -name venv -o -name .tox -o -name dist -o -name build -o -name .next -o -name coverage -o -name frontend/coverage -o -name .hypothesis \) -prune \) -o \
    \( -type f -name "$pat" -print \))
  if [ -n "$results" ]; then
    found_any=true
    while IFS= read -r line; do
      echo "$line" >> "$OUTPUT_FILE"
    done <<< "$results"
  fi
done
if [ "$found_any" = false ]; then
  echo "(none found)" >> "$OUTPUT_FILE"
fi
echo "" >> "$OUTPUT_FILE"

# 3) Test directories
print_section "Test Directories"
tests_found=false

tests_results=$(find "$REPO_ROOT" \
  \( -type d \( -name node_modules -o -name .git -o -name .venv -o -name venv -o -name .tox -o -name dist -o -name build -o -name .next -o -name coverage \) -prune \) -o \
  \( -type d \( -name tests -o -path "*/src/*/tests" -o -path "*/frontend/*/tests" -o -path "*/e2e/*" \) -print \))

if [ -n "$tests_results" ]; then
  tests_found=true
  echo "$tests_results" >> "$OUTPUT_FILE"
fi
if [ "$tests_found" = false ]; then
  echo "(none found)" >> "$OUTPUT_FILE"
fi
echo "" >> "$OUTPUT_FILE"

# 4) Config files
print_section "Config Files"
config_patterns=(
  'pytest.ini' 'pyproject.toml' 'jest.config.*' 'vitest.config.*' 'eslint.*' 'ruff.toml' 'mypy.ini' 'tsconfig.json'
  'Dockerfile*' 'docker-compose.*' 'Makefile' '.pre-commit-config.yaml' '.editorconfig' '.nvmrc'
)

configs_found=false
for pat in "${config_patterns[@]}"; do
  results=$(find "$REPO_ROOT" \
    \( -type d \( -name node_modules -o -name .git -o -name .venv -o -name venv -o -name dist -o -name build -o -name .next \) -prune \) -o \
    \( -type f -name "$pat" -print \))
  if [ -n "$results" ]; then
    configs_found=true
    echo "$results" >> "$OUTPUT_FILE"
  fi
done
if [ "$configs_found" = false ]; then
  echo "(none found)" >> "$OUTPUT_FILE"
fi
echo "" >> "$OUTPUT_FILE"

# 5) pre-commit installed?
print_section "pre-commit"
if command -v pre-commit >/dev/null 2>&1; then
  print_kv "pre-commit" "$(pre-commit --version 2>&1)"
else
  print_kv "pre-commit" "not installed"
fi
echo "" >> "$OUTPUT_FILE"

echo "Report written to $OUTPUT_FILE"


