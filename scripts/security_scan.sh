#!/usr/bin/env bash

# Security scan aggregator
# - Python: pip-audit, bandit, safety
# - Node: audit-ci or npm audit
# - Secrets: gitleaks

set +e
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORTS_DIR="$REPO_ROOT/reports"
TMP_DIR="$REPORTS_DIR/tmp"
TOOLS_DIR="$REPO_ROOT/.tools"
PY_VENV="$TOOLS_DIR/venv"

mkdir -p "$REPORTS_DIR" "$TMP_DIR" "$TOOLS_DIR"

log() { printf "\033[34m[scan]\033[0m %s\n" "$*"; }
warn() { printf "\033[33m[warn]\033[0m %s\n" "$*"; }
ok() { printf "\033[32m[ok]\033[0m %s\n" "$*"; }

ensure_python_tools() {
  if ! command -v python3 >/dev/null 2>&1; then
    warn "python3 не найден; пропускаю python-сканы"
    return 1
  fi
  if [ ! -d "$PY_VENV" ]; then
    log "Создаю локальное venv для утилит: $PY_VENV"
    python3 -m venv "$PY_VENV" || return 1
  fi
  # shellcheck disable=SC1091
  . "$PY_VENV/bin/activate"
  python -m pip install --upgrade pip >/dev/null 2>&1
  python -m pip install --quiet pip-audit bandit safety >/dev/null 2>&1 || true
  # Попытка через uv при наличии
  if ! command -v pip-audit >/dev/null 2>&1 || ! command -v bandit >/dev/null 2>&1 || ! command -v safety >/dev/null 2>&1; then
    if command -v uv >/dev/null 2>&1; then
      log "Устанавливаю python-утилиты через uv"
      uv pip install --quiet pip-audit bandit safety >/dev/null 2>&1 || true
    fi
  fi
  echo "$PY_VENV/bin"
}

ensure_gitleaks() {
  if command -v gitleaks >/dev/null 2>&1; then
    echo "gitleaks"
    return 0
  fi
  local bin_dir="$TOOLS_DIR/bin"
  mkdir -p "$bin_dir"
  local target="$bin_dir/gitleaks"
  if [ -x "$target" ]; then
    echo "$target"
    return 0
  fi
  log "gitleaks не найден — попробую скачать локально"
  # Try to download latest release for darwin/linux amd64
  uname_s=$(uname -s | tr '[:upper:]' '[:lower:]')
  uname_m=$(uname -m)
  case "$uname_m" in
    x86_64|amd64) arch="x64" ;;
    arm64|aarch64) arch="arm64" ;;
    *) arch="x64" ;;
  esac
  url="https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_${uname_s}_${arch}.tar.gz"
  tmp_tgz="$TMP_DIR/gitleaks.tgz"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$tmp_tgz" || true
  elif command -v wget >/dev/null 2>&1; then
    wget -q "$url" -O "$tmp_tgz" || true
  fi
  if [ -s "$tmp_tgz" ]; then
    tar -xzf "$tmp_tgz" -C "$bin_dir" >/dev/null 2>&1 || true
    if [ -x "$bin_dir/gitleaks" ]; then
      echo "$bin_dir/gitleaks"
      return 0
    fi
  fi
  # Fallback: Homebrew (macOS)
  if command -v brew >/dev/null 2>&1; then
    log "Пробую установить gitleaks через Homebrew"
    brew install gitleaks >/dev/null 2>&1 || true
    if command -v gitleaks >/dev/null 2>&1; then
      echo "gitleaks"
      return 0
    fi
  fi
  warn "Не удалось установить gitleaks"
  return 1
}

PATH_ADDED=""
if py_bin_dir=$(ensure_python_tools); then
  export PATH="$py_bin_dir:$PATH"
  PATH_ADDED="1"
fi

########################
# Python: pip-audit
########################
log "Python: pip-audit"
pip_audit_txt="$REPORTS_DIR/security_python_pip_audit.txt"
pip_audit_json="$TMP_DIR/pip_audit.json"
pip_audit_args=()
if [ -f "$REPO_ROOT/backend/requirements.txt" ]; then
  pip_audit_args=( -r "$REPO_ROOT/backend/requirements.txt" )
fi
if command -v pip-audit >/dev/null 2>&1; then
  pip-audit "${pip_audit_args[@]}" -f json >"$pip_audit_json" 2>/dev/null || true
  pip-audit "${pip_audit_args[@]}" >"$pip_audit_txt" 2>/dev/null || true
else
  warn "pip-audit недоступен"
  : >"$pip_audit_txt"
fi

########################
# Python: bandit (scoped + excludes)
########################
log "Python: bandit"
bandit_txt="$REPORTS_DIR/security_python_bandit.txt"
bandit_json="$TMP_DIR/bandit.json"
if command -v bandit >/dev/null 2>&1; then
  EXCLUDES=".venv,tests,coverage,htmlcov,dist,build,__pycache__,.mypy_cache,.pytest_cache,**/*.min.js"
  if [ -d "$REPO_ROOT/backend/app" ]; then
    (cd "$REPO_ROOT/backend" && bandit -r app -x "$EXCLUDES" -f json -o "$bandit_json" >/dev/null 2>&1 || true)
    (cd "$REPO_ROOT/backend" && bandit -r app -x "$EXCLUDES" >"$bandit_txt" 2>/dev/null || true)
  elif [ -d "$REPO_ROOT/backend" ]; then
    (cd "$REPO_ROOT/backend" && bandit -r . -x "$EXCLUDES" -f json -o "$bandit_json" >/dev/null 2>&1 || true)
    (cd "$REPO_ROOT/backend" && bandit -r . -x "$EXCLUDES" >"$bandit_txt" 2>/dev/null || true)
  else
    bandit -r "$REPO_ROOT" -x "$EXCLUDES" -f json -o "$bandit_json" >/dev/null 2>&1 || true
    bandit -r "$REPO_ROOT" -x "$EXCLUDES" >"$bandit_txt" 2>/dev/null || true
  fi
else
  warn "bandit недоступен"
  : >"$bandit_txt"
fi

########################
# Python: safety
########################
log "Python: safety"
safety_txt="$REPORTS_DIR/security_python_safety.txt"
safety_json="$TMP_DIR/safety.json"
safety_args=( check --full-report )
if [ -f "$REPO_ROOT/backend/requirements.txt" ]; then
  safety_args+=( --file "$REPO_ROOT/backend/requirements.txt" )
fi
if command -v safety >/dev/null 2>&1; then
  safety --json "${safety_args[@]}" >"$safety_json" 2>/dev/null || true
  safety "${safety_args[@]}" >"$safety_txt" 2>/dev/null || true
else
  warn "safety недоступен"
  : >"$safety_txt"
fi

########################
# Node: audit-ci / npm audit
########################
log "Node: audit-ci / npm audit"
node_txt="$REPORTS_DIR/security_node.txt"
npm_audit_json="$TMP_DIR/npm_audit.json"
if [ -d "$REPO_ROOT/frontend" ] && command -v npm >/dev/null 2>&1; then
  (cd "$REPO_ROOT/frontend" && npx --yes audit-ci -m >"$node_txt" 2>/dev/null) || true
  (cd "$REPO_ROOT/frontend" && npm audit --json >"$npm_audit_json" 2>/dev/null) || true
else
  warn "frontend или npm недоступны — пропускаю node-аудит"
  : >"$node_txt"
fi

########################
# Secrets: gitleaks
########################
log "Secrets: gitleaks"
gitleaks_bin="$(ensure_gitleaks)"
if [ -n "$gitleaks_bin" ] && [ -x "$gitleaks_bin" ]; then
  "$gitleaks_bin" detect --no-banner -s "$REPO_ROOT" -r "$REPORTS_DIR/gitleaks.json" >/dev/null 2>&1 || true
else
  if command -v docker >/dev/null 2>&1; then
    log "Запускаю gitleaks через Docker"
    docker run --rm -v "$REPO_ROOT:/repo" ghcr.io/gitleaks/gitleaks:latest detect --no-banner -s /repo -r /repo/reports/gitleaks.json >/dev/null 2>&1 || true
  else
    warn "gitleaks не установлен — пропускаю"
  fi
fi

########################
# TL;DR summary
########################
tldr_file="$REPORTS_DIR/security_tldr.txt"
python3 - "$pip_audit_json" "$bandit_json" "$safety_json" "$npm_audit_json" "$REPORTS_DIR/gitleaks.json" <<'PY' >"$tldr_file"
import json, os, sys

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = f.read().strip()
            if not data:
                return None
            return json.loads(data)
    except Exception:
        return None

pip_audit = load_json(sys.argv[1]) if len(sys.argv) > 1 else None
bandit = load_json(sys.argv[2]) if len(sys.argv) > 2 else None
safety = load_json(sys.argv[3]) if len(sys.argv) > 3 else None
npm_audit = load_json(sys.argv[4]) if len(sys.argv) > 4 else None
gitleaks = load_json(sys.argv[5]) if len(sys.argv) > 5 else None

def count_pip_audit(obj):
    hi = cr = 0
    if not obj:
        return hi, cr
    # pip-audit JSON may be a list of packages with "vulns"
    if isinstance(obj, list):
        for pkg in obj:
            for v in pkg.get('vulns', []):
                sev = (v.get('severity') or '').upper()
                if sev == 'HIGH':
                    hi += 1
                elif sev == 'CRITICAL':
                    cr += 1
    elif isinstance(obj, dict):
        # Alternative structure: {"dependencies": [...], "vulnerabilities": [...]}
        vulns = obj.get('vulnerabilities') or []
        for v in vulns:
            sev = (v.get('severity') or '').upper()
            if sev == 'HIGH':
                hi += 1
            elif sev == 'CRITICAL':
                cr += 1
    return hi, cr

def count_bandit(obj):
    # Bandit has severities LOW/MEDIUM/HIGH only
    hi = 0
    if not obj:
        return hi, 0
    for r in obj.get('results', []):
        if (r.get('issue_severity') or '').upper() == 'HIGH':
            hi += 1
    return hi, 0

def count_safety(obj):
    hi = cr = 0
    if not obj:
        return hi, cr
    vulns = obj.get('vulnerabilities') or obj.get('issues') or []
    for v in vulns:
        sev = (v.get('severity') or v.get('severity').lower() if isinstance(v.get('severity'), str) else '').upper()
        if sev == 'HIGH':
            hi += 1
        elif sev == 'CRITICAL':
            cr += 1
    return hi, cr

def count_npm(obj):
    hi = cr = 0
    if not obj:
        return hi, cr
    meta = obj.get('metadata') or {}
    vuln = meta.get('vulnerabilities') or obj.get('vulnerabilities') or {}
    hi = int(vuln.get('high') or 0)
    cr = int(vuln.get('critical') or 0)
    return hi, cr

def count_gitleaks(obj):
    if not obj:
        return 0
    if isinstance(obj, list):
        return len(obj)
    if isinstance(obj, dict):
        findings = obj.get('findings')
        if isinstance(findings, list):
            return len(findings)
    return 0

phi, pcr = count_pip_audit(pip_audit)
bhi, bcr = count_bandit(bandit)
shi, scr = count_safety(safety)
nhi, ncr = count_npm(npm_audit)
gcount = count_gitleaks(gitleaks)

print("pip-audit: HIGH={}, CRITICAL={}".format(phi, pcr))
print("bandit: HIGH={}, CRITICAL={}".format(bhi, bcr))
print("safety: HIGH={}, CRITICAL={}".format(shi, scr))
print("node (npm audit): HIGH={}, CRITICAL={}".format(nhi, ncr))
print("gitleaks: findings={} (severity N/A)".format(gcount))
PY

ok "TL;DR сохранён: $tldr_file"
cat "$tldr_file" || true

exit 0


