#!/usr/bin/env python3
import os
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CoverageStats:
    lines_total: int = 0
    lines_covered: int = 0

    @property
    def percent(self) -> float:
        if self.lines_total <= 0:
            return 0.0
        return (self.lines_covered / self.lines_total) * 100.0


def read_backend_cobertura(path: Path) -> CoverageStats:
    if not path.exists():
        return CoverageStats(0, 0)
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # Cobertura format: line-rate attribute at root (0..1)
        line_rate_attr = root.attrib.get("line-rate")
        if line_rate_attr is not None:
            # When only line-rate present without detailed totals, approximate using rate * 100 with virtual 100 lines
            rate = float(line_rate_attr)
            # Try to compute precise totals if available from 'lines-covered'/'lines-valid'
            lines_valid = root.attrib.get("lines-valid") or root.attrib.get("lines-valid".replace("-", "_"))
            lines_covered = root.attrib.get("lines-covered") or root.attrib.get("lines_covered")
            if lines_valid and lines_covered:
                total = int(float(lines_valid))
                covered = int(float(lines_covered))
                return CoverageStats(total, covered)
            # Fallback: assume 100 lines for weighting
            approx_total = 100
            approx_covered = int(round(rate * approx_total))
            return CoverageStats(approx_total, approx_covered)

        # Fallback: aggregate from class lines
        total = 0
        covered = 0
        for line in root.findall('.//line'):
            hits_attr = line.attrib.get('hits')
            if hits_attr is None:
                continue
            total += 1
            if int(hits_attr) > 0:
                covered += 1
        return CoverageStats(total, covered)
    except Exception as exc:
        print(f"[quality-gate] WARN: failed to parse backend coverage '{path}': {exc}")
        return CoverageStats(0, 0)


def read_frontend_lcov(lcov_paths: list[Path]) -> CoverageStats:
    total = 0
    covered = 0
    da_pattern = re.compile(r"^DA:(\d+),(\d+)")
    lf_pattern = re.compile(r"^LF:(\d+)")
    lh_pattern = re.compile(r"^LH:(\d+)")

    for lcov_path in lcov_paths:
        if not lcov_path.exists():
            continue
        try:
            file_total = 0
            file_covered = 0
            # Prefer LF/LH if present; else compute from DA
            has_lf_lh = False
            with lcov_path.open('r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    mlf = lf_pattern.match(line)
                    if mlf:
                        file_total += int(mlf.group(1))
                        has_lf_lh = True
                        continue
                    mlh = lh_pattern.match(line)
                    if mlh:
                        file_covered += int(mlh.group(1))
                        has_lf_lh = True
                        continue
                    if not has_lf_lh:
                        mda = da_pattern.match(line)
                        if mda:
                            file_total += 1
                            if int(mda.group(2)) > 0:
                                file_covered += 1
            total += file_total
            covered += file_covered
        except Exception as exc:
            print(f"[quality-gate] WARN: failed to parse lcov '{lcov_path}': {exc}")
            continue
    return CoverageStats(total, covered)


def find_lcov_candidates(project_root: Path) -> list[Path]:
    candidates: list[Path] = []
    # Typical vitest path
    candidates.append(project_root / 'frontend' / 'coverage' / 'lcov.info')
    # Jest default under coverage/lcov.info (frontend)
    candidates.append(project_root / 'frontend' / 'coverage' / 'lcov-report' / 'lcov.info')
    # As a fallback, any lcov.info under frontend
    for p in (project_root / 'frontend').rglob('lcov.info'):
        if p not in candidates:
            candidates.append(p)
    # Also allow root coverage file if exists
    if (project_root / 'coverage' / 'lcov.info').exists():
        candidates.append(project_root / 'coverage' / 'lcov.info')
    # Deduplicate while preserving order
    seen = set()
    unique: list[Path] = []
    for c in candidates:
        try:
            rp = c.resolve()
        except Exception:
            rp = c
        if rp not in seen and c.exists():
            seen.add(rp)
            unique.append(c)
    return unique


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    reports_dir = project_root / 'reports'
    reports_dir.mkdir(parents=True, exist_ok=True)

    backend_xml = reports_dir / 'coverage.xml'
    backend_stats = read_backend_cobertura(backend_xml)

    lcov_candidates = find_lcov_candidates(project_root)
    frontend_stats = read_frontend_lcov(lcov_candidates) if lcov_candidates else CoverageStats(0, 0)

    total_lines = backend_stats.lines_total + frontend_stats.lines_total
    total_covered = backend_stats.lines_covered + frontend_stats.lines_covered
    combined = CoverageStats(total_lines, total_covered)

    summary_md = [
        "# Quality Gate Summary",
        "",
        f"- Backend coverage: {backend_stats.percent:.2f}% ({backend_stats.lines_covered}/{backend_stats.lines_total} lines)",
        f"- Frontend coverage: {frontend_stats.percent:.2f}% ({frontend_stats.lines_covered}/{frontend_stats.lines_total} lines)",
        f"- Combined coverage: **{combined.percent:.2f}%** ({combined.lines_covered}/{combined.lines_total} lines)",
        "",
    ]

    out_path = reports_dir / 'quality_summary.md'
    out_path.write_text("\n".join(summary_md), encoding='utf-8')

    print("\n".join(summary_md))
    print(f"[quality-gate] Wrote summary → {out_path}")

    # Exit non-zero if combined < optional threshold via env (e.g., QUALITY_MIN=70)
    min_required = os.getenv('QUALITY_MIN')
    if min_required:
        try:
            threshold = float(min_required)
            if combined.percent + 1e-9 < threshold:
                print(f"[quality-gate] Combined coverage {combined.percent:.2f}% < threshold {threshold:.2f}%")
                return 2
        except ValueError:
            pass
    return 0


if __name__ == '__main__':
    sys.exit(main())


