#!/usr/bin/env python3
import subprocess
import sys
import time
import random
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORT_FILE = REPORTS_DIR / "flaky_report.md"


def run(cmd: List[str], cwd: Optional[Path] = None, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError as e:
        return 127, "", str(e)
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", e.stderr or "timeout"


def detect_backend_python() -> str:
    venv_python = PROJECT_ROOT / "backend" / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    # Fallbacks
    for exe in ("python3", "python"):
        if shutil.which(exe):
            return exe
    return sys.executable


def collect_pytest_tests() -> List[str]:
    backend_dir = PROJECT_ROOT / "backend"
    if not backend_dir.exists():
        return []
    python_exec = detect_backend_python()
    code, out, err = run([python_exec, "-m", "pytest", "--collect-only", "-q"], cwd=backend_dir)
    if code != 0:
        return []
    tests: List[str] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("<"):
            # e.g., <Module test_...>
            continue
        if "no tests ran" in line:
            continue
        if line.startswith("warnings summary"):
            break
        # Accept nodeids like file::class::test or file::test
        if ":" in line or line.endswith(".py"):
            tests.append(line)
    return tests


def run_pytest_nodeid(nodeid: str, repeats: int = 5) -> Tuple[int, List[int]]:
    backend_dir = PROJECT_ROOT / "backend"
    python_exec = detect_backend_python()
    failures = 0
    rc_list: List[int] = []
    for _ in range(repeats):
        code, out, err = run([python_exec, "-m", "pytest", nodeid, "-q"], cwd=backend_dir)
        rc_list.append(code)
        if code != 0:
            failures += 1
    return failures, rc_list


def backend_flaky_section(max_tests: int = 20, repeats: int = 5) -> Tuple[str, List[Tuple[str, int, int]]]:
    tests = collect_pytest_tests()
    if not tests:
        return "- Backend: тесты не найдены или сборка не удалась.\n", []
    sample_size = min(max_tests, len(tests))
    random.shuffle(tests)
    picked = tests[:sample_size]
    results: List[Tuple[str, int, int]] = []  # (nodeid, failures, repeats)
    for nodeid in picked:
        failures, _ = run_pytest_nodeid(nodeid, repeats=repeats)
        results.append((nodeid, failures, repeats))

    # Compose report section
    lines: List[str] = []
    lines.append("### Backend (pytest)\n")
    lines.append(f"Проверено тестов: {sample_size}, повторов: {repeats}.\n")
    # Sort flaky first: 0<failures<repeats by failures desc, then stable, then perma-fail
    flaky = [(n, f, repeats) for (n, f, repeats) in results if 0 < f < repeats]
    stable = [(n, f, repeats) for (n, f, repeats) in results if f == 0]
    broken = [(n, f, repeats) for (n, f, repeats) in results if f == repeats]
    flaky.sort(key=lambda x: x[1], reverse=True)
    lines.append("\n")
    lines.append("Флейки тесты:\n")
    if flaky:
        for (nodeid, f, r) in flaky:
            rate = f"{f}/{r}"
            lines.append(f"- {nodeid} — {rate}\n")
    else:
        lines.append("- не обнаружены\n")

    lines.append("\nСтабильные (0/{}):\n".format(repeats))
    for (nodeid, _, r) in stable:
        lines.append(f"- {nodeid}\n")

    lines.append("\nПостоянно падающие ({}/{}):\n".format(repeats, repeats))
    for (nodeid, f, r) in broken:
        lines.append(f"- {nodeid} — {f}/{r}\n")

    return "".join(lines) + "\n", flaky


def list_frontend_test_files() -> List[Path]:
    frontend_dir = PROJECT_ROOT / "frontend"
    if not frontend_dir.exists():
        return []
    exts = ("ts", "tsx", "js", "jsx", "mts", "cts", "mjs", "cjs")
    patterns = []
    for ext in exts:
        patterns.append(f"**/*.test.{ext}")
        patterns.append(f"**/*.spec.{ext}")
    files: List[Path] = []
    for pat in patterns:
        files.extend(frontend_dir.glob(pat))
    # unique
    return sorted(set(files))


def detect_frontend_runner() -> Optional[str]:
    # Prefer vitest, fallback to jest
    if shutil.which("npx"):
        code, _, _ = run(["npx", "--yes", "vitest", "--version"], cwd=PROJECT_ROOT / "frontend")
        if code == 0:
            return "vitest"
        code, _, _ = run(["npx", "--yes", "jest", "--version"], cwd=PROJECT_ROOT / "frontend")
        if code == 0:
            return "jest"
    return None


def time_frontend_test_file(runner: str, file_path: Path) -> Tuple[float, int]:
    start = time.time()
    if runner == "vitest":
        cmd = ["npx", "--yes", "vitest", "run", "--silent", str(file_path)]
    else:  # jest
        cmd = ["npx", "--yes", "jest", "--runInBand", "--silent", str(file_path)]
    code, out, err = run(cmd, cwd=PROJECT_ROOT / "frontend")
    duration = time.time() - start
    return duration, code


def run_frontend_test_file(runner: str, file_path: Path, repeats: int = 5) -> Tuple[int, List[int]]:
    failures = 0
    rcs: List[int] = []
    for _ in range(repeats):
        if runner == "vitest":
            cmd = ["npx", "--yes", "vitest", "run", "--silent", str(file_path)]
        else:
            cmd = ["npx", "--yes", "jest", "--runInBand", "--silent", str(file_path)]
        code, out, err = run(cmd, cwd=PROJECT_ROOT / "frontend")
        rcs.append(code)
        if code != 0:
            failures += 1
    return failures, rcs


def frontend_flaky_section(top_n: int = 10, repeats: int = 5) -> Tuple[str, List[Tuple[str, int, int]]]:
    runner = detect_frontend_runner()
    if not runner:
        return "- Frontend: vitest/jest не найдены, раздел пропущен.\n", []
    files = list_frontend_test_files()
    if not files:
        return "- Frontend: тестовые файлы не найдены.\n", []

    # Measure duration per file (best effort)
    timings: List[Tuple[Path, float, int]] = []  # (file, duration, rc)
    # Limit timing phase to at most 50 files to keep runtime reasonable
    sample = files[:50]
    for f in sample:
        dur, rc = time_frontend_test_file(runner, f)
        timings.append((f, dur, rc))
    timings.sort(key=lambda x: x[1])
    picked = [f for (f, _, _) in timings[: min(top_n, len(timings))]]

    results: List[Tuple[str, int, int]] = []  # (file, failures, repeats)
    for f in picked:
        failures, _ = run_frontend_test_file(runner, f, repeats=repeats)
        results.append((str(f.relative_to(PROJECT_ROOT)), failures, repeats))

    lines: List[str] = []
    lines.append("### Frontend ({}): ТОП-{} самых быстрых файлов, повторы {}\n".format(runner, len(picked), repeats))
    flaky = [(n, f, repeats) for (n, f, repeats) in results if 0 < f < repeats]
    stable = [(n, f, repeats) for (n, f, repeats) in results if f == 0]
    broken = [(n, f, repeats) for (n, f, repeats) in results if f == repeats]
    flaky.sort(key=lambda x: x[1], reverse=True)

    lines.append("\nФлейки тесты:\n")
    if flaky:
        for (name, f, r) in flaky:
            lines.append(f"- {name} — {f}/{r}\n")
    else:
        lines.append("- не обнаружены\n")

    lines.append("\nСтабильные (0/{}):\n".format(repeats))
    for (name, _, r) in stable:
        lines.append(f"- {name}\n")

    lines.append("\nПостоянно падающие ({}/{}):\n".format(repeats, repeats))
    for (name, f, r) in broken:
        lines.append(f"- {name} — {f}/{r}\n")

    return "".join(lines) + "\n", flaky


def write_report(header_lines: List[str], backend_section: str, frontend_section: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with REPORT_FILE.open("w", encoding="utf-8") as f:
        for h in header_lines:
            f.write(h)
        f.write("\n")
        f.write(backend_section)
        f.write("\n")
        f.write(frontend_section)


def main() -> int:
    random.seed(42)
    header = [
        "# Flaky Report\n",
        f"Сгенерировано: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "\n",
    ]

    backend_section, backend_flaky = backend_flaky_section(max_tests=20, repeats=5)
    frontend_section, frontend_flaky = frontend_flaky_section(top_n=10, repeats=5)

    write_report(header, backend_section, frontend_section)

    # Print top-10 flaky tests (combined backend+frontend) to stdout
    combined: List[Tuple[str, int, int]] = backend_flaky + frontend_flaky
    combined.sort(key=lambda x: x[1], reverse=True)
    top10 = combined[:10]
    if top10:
        print("TOP-10 flaky tests:")
        for name, f, r in top10:
            print(f"{name} — {f}/{r}")
    else:
        print("No flaky tests detected.")
    print(f"Report: {REPORT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


