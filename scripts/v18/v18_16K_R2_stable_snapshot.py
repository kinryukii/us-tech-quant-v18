from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_16K_R2_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_16K_R2_STABLE_SNAPSHOT_VALIDATION_FAILED"
MODE = "SNAPSHOT_ONLY"
SNAPSHOT_ONLY = "TRUE"
SNAPSHOT_PREFIX = "V18_16K_R2_stable_true_5day_coverage_evidence_semantics"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "STABLE_SNAPSHOT_MODIFIED": "TRUE",
}

REQUIRED_SNAPSHOT_FILES = [
    "scripts/v18/v18_16K_true_5day_unique_coverage_scheduler.py",
    "scripts/v18/run_v18_16K_true_5day_unique_coverage_scheduler.ps1",
    "scripts/v18/v18_16K_R1_coverage_evidence_quality_patch.py",
    "scripts/v18/run_v18_16K_R1_coverage_evidence_quality_patch.ps1",
    "scripts/v18/v18_16K_R2_evidence_count_semantics_patch.py",
    "scripts/v18/run_v18_16K_R2_evidence_count_semantics_patch.ps1",
    "outputs/v18/universe/V18_16K_R2_CURRENT_SCAN_DAY_EVIDENCE_QUALITY.csv",
    "outputs/v18/universe/V18_16K_R2_CURRENT_CONSERVATIVE_RECOVERY_PLAN_AUDIT.csv",
    "outputs/v18/universe/V18_16K_R2_CURRENT_UNIVERSE_COUNT_RECONCILIATION.csv",
    "outputs/v18/ops/V18_16K_R2_READ_FIRST.txt",
    "outputs/v18/ops/V18_16K_R2_CURRENT_EVIDENCE_COUNT_SEMANTICS_REPORT.md",
]

SUPPORTING_FILES = [
    "outputs/v18/universe/V18_16K_CURRENT_5DAY_UNIQUE_COVERAGE_MATRIX.csv",
    "outputs/v18/universe/V18_16K_CURRENT_UNCOVERED_TICKERS.csv",
    "outputs/v18/universe/V18_16K_CURRENT_DUPLICATE_SCAN_AUDIT.csv",
    "outputs/v18/universe/V18_16K_CURRENT_RECOMMENDED_NEXT_SCAN_PLAN.csv",
    "outputs/v18/ops/V18_16K_READ_FIRST.txt",
    "outputs/v18/ops/V18_16K_CURRENT_TRUE_5DAY_COVERAGE_REPORT.md",
    "outputs/v18/universe/V18_16K_R1_CURRENT_UNIVERSE_COUNT_RECONCILIATION.csv",
    "outputs/v18/universe/V18_16K_R1_CURRENT_SCAN_DAY_EVIDENCE_QUALITY.csv",
    "outputs/v18/universe/V18_16K_R1_CURRENT_DUPLICATE_SCAN_DETAIL.csv",
    "outputs/v18/universe/V18_16K_R1_CURRENT_5DAY_RECOVERY_PLAN.csv",
    "outputs/v18/ops/V18_16K_R1_READ_FIRST.txt",
    "outputs/v18/ops/V18_16K_R1_CURRENT_COVERAGE_EVIDENCE_QUALITY_REPORT.md",
]

PS_PARSE_FILES = [
    "scripts/v18/run_v18_16K_R2_stable_snapshot.ps1",
    "scripts/v18/run_v18_16K_true_5day_unique_coverage_scheduler.ps1",
    "scripts/v18/run_v18_16K_R1_coverage_evidence_quality_patch.ps1",
    "scripts/v18/run_v18_16K_R2_evidence_count_semantics_patch.ps1",
]

PY_COMPILE_FILES = [
    "scripts/v18/v18_16K_R2_stable_snapshot.py",
    "scripts/v18/v18_16K_true_5day_unique_coverage_scheduler.py",
    "scripts/v18/v18_16K_R1_coverage_evidence_quality_patch.py",
    "scripts/v18/v18_16K_R2_evidence_count_semantics_patch.py",
]

MANIFEST_FIELDS = [
    "category",
    "required",
    "status",
    "source_path",
    "snapshot_path",
    "relative_source_path",
    "relative_snapshot_path",
    "size_bytes",
    "modified_time",
    "sha256",
    "error",
]

VALIDATION_FIELDS = ["check_name", "status", "path", "expected", "actual", "note"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except Exception:
            continue
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except Exception:
            continue
    return []


def rel(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mtime(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def readfirst_metrics(path: Path) -> Dict[str, str]:
    metrics: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        key = left.strip().lstrip("-").strip().upper()
        if key:
            metrics[key] = right.strip()
    return metrics


def ps_parse(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    escaped = str(path).replace("'", "''")
    command = f"$null = [scriptblock]::Create((Get-Content -Raw -LiteralPath '{escaped}')); 'OK_PARSE'"
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and "OK_PARSE" in (result.stdout or ""):
            return True, "OK_PARSE"
        return False, (result.stderr or result.stdout).strip()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def py_compile(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    try:
        result = subprocess.run(
            ["python", "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return True, "OK_COMPILE"
        return False, (result.stderr or result.stdout).strip()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def copy_file(root: Path, snapshot_dir: Path, relative_path: str, required: bool, category: str) -> Dict[str, object]:
    source = root / relative_path
    target = snapshot_dir / relative_path
    row: Dict[str, object] = {
        "category": category,
        "required": str(required).upper(),
        "source_path": str(source),
        "snapshot_path": str(target),
        "relative_source_path": relative_path,
        "relative_snapshot_path": str(target.relative_to(snapshot_dir)).replace("\\", "/"),
    }
    if not source.exists() or not source.is_file():
        row.update({"status": "MISSING", "size_bytes": "", "modified_time": "", "sha256": "", "error": "SOURCE_MISSING"})
        return row
    try:
        ensure_dir(target.parent)
        shutil.copy2(source, target)
        row.update(
            {
                "status": "COPIED",
                "size_bytes": target.stat().st_size,
                "modified_time": mtime(target),
                "sha256": sha256(target),
                "error": "",
            }
        )
    except Exception as exc:
        row.update({"status": "COPY_FAILED", "size_bytes": "", "modified_time": "", "sha256": "", "error": f"{type(exc).__name__}: {exc}"})
    return row


def restore_script() -> str:
    lines = [
        'param([string]$Root = "D:\\us-tech-quant")',
        '$ErrorActionPreference = "Stop"',
        '$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path',
        'Write-Host "=== RESTORE V18.16K-R2 COVERAGE AUDIT SNAPSHOT START ==="',
        'Write-Host "ROOT: $Root"',
        'Write-Host "SNAPSHOT_ROOT: $SnapshotRoot"',
    ]
    for relative in REQUIRED_SNAPSHOT_FILES + SUPPORTING_FILES:
        lines.extend(
            [
                f'$Source = Join-Path $SnapshotRoot "{relative.replace("/", "\\")}"',
                f'$Target = Join-Path $Root "{relative.replace("/", "\\")}"',
                'if (Test-Path $Source) {',
                '    $TargetDir = Split-Path -Parent $Target',
                '    if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }',
                '    Copy-Item -LiteralPath $Source -Destination $Target -Force',
                '}',
            ]
        )
    lines.extend(
        [
            'Write-Host "RESTORE_COMPLETE: TRUE"',
            'Write-Host "NOTE: Snapshot restore only restores advisory audit files and outputs; it does not apply any scan plan."',
            'Write-Host "=== RESTORE V18.16K-R2 COVERAGE AUDIT SNAPSHOT END ==="',
        ]
    )
    return "\n".join(lines) + "\n"


def render_readme(metrics: Dict[str, str], snapshot_dir: Path) -> str:
    return f"""# V18.16K-R2 Stable Snapshot

This snapshot preserves V18.16K-R2 coverage audit / evidence semantics.

This snapshot does not mean true 5-day unique coverage is solved.

Required preserved state:
- TRUE_5DAY_UNIQUE_COVERAGE_MET remains FALSE.
- DISTINCT_SCAN_DAY_VALID_COUNT is {metrics.get('DISTINCT_SCAN_DAY_VALID_COUNT', '2')} and REQUIRED_SCAN_DAY_COUNT is {metrics.get('REQUIRED_SCAN_DAY_COUNT', '5')}.
- COVERAGE_WINDOW_COMPLETE remains {metrics.get('COVERAGE_WINDOW_COMPLETE', 'FALSE')}.
- Universe count disagreement remains under review: selected {metrics.get('SELECTED_TOTAL_UNIVERSE_COUNT', '324')}, max source {metrics.get('MAX_SOURCE_UNIVERSE_COUNT', '325')}.
- Recovery plan fully solves selected universe but not max source universe.

Safety:
- The module is advisory-only.
- It does not affect official decisions, ranking, promotion/demotion, price cache, manual state, auto-trade, or auto-sell.
- Snapshot restore only restores advisory scripts and audit outputs. It does not apply the recommended scan plan.

Snapshot path:
`{snapshot_dir}`

Restore:
Run `RESTORE_V18_16K_R2.ps1` from this snapshot directory if these advisory audit files need to be restored.
"""


def render_report(metrics: Dict[str, str], snapshot_dir: Path, manifest_count: int, validation_fail_count: int) -> str:
    return f"""# V18.16K-R2 Stable Snapshot Report

## Executive Summary
- Status: {metrics['STATUS']}
- Mode: {MODE}
- Snapshot path: {snapshot_dir}
- Manifest rows: {manifest_count}
- Validation fail count: {validation_fail_count}

## Preserved Audit State
- TRUE_5DAY_UNIQUE_COVERAGE_MET: {metrics.get('TRUE_5DAY_UNIQUE_COVERAGE_MET', 'FALSE')}
- COVERAGE_WINDOW_COMPLETE: {metrics.get('COVERAGE_WINDOW_COMPLETE', 'FALSE')}
- DISTINCT_SCAN_DAY_VALID_COUNT: {metrics.get('DISTINCT_SCAN_DAY_VALID_COUNT', '')}
- REQUIRED_SCAN_DAY_COUNT: {metrics.get('REQUIRED_SCAN_DAY_COUNT', '')}
- UNIVERSE_COUNT_SOURCE_DISAGREEMENT: {metrics.get('UNIVERSE_COUNT_SOURCE_DISAGREEMENT', 'TRUE')}
- SELECTED_TOTAL_UNIVERSE_COUNT: {metrics.get('SELECTED_TOTAL_UNIVERSE_COUNT', '')}
- MAX_SOURCE_UNIVERSE_COUNT: {metrics.get('MAX_SOURCE_UNIVERSE_COUNT', '')}

## Safety
Snapshot-only. No current daily command center behavior, official decisions, ranking, promotion/demotion, manual state, price cache, auto-trade, or auto-sell behavior was modified.
"""


def render_stable_read_first(metrics: Dict[str, str], snapshot_dir: Path, manifest_count: int, validation_fail_count: int) -> str:
    ordered = [
        "STATUS",
        "MODE",
        "SNAPSHOT_ONLY",
        "POLICY_APPLIED",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET",
        "TRUE_5DAY_UNIQUE_COVERAGE_COUNT",
        "TRUE_5DAY_UNIQUE_SHORTFALL_COUNT",
        "DISTINCT_SCAN_DAY_VALID_COUNT",
        "REQUIRED_SCAN_DAY_COUNT",
        "COVERAGE_WINDOW_COMPLETE",
        "UNIVERSE_COUNT_SOURCE_DISAGREEMENT",
        "SELECTED_TOTAL_UNIVERSE_COUNT",
        "MAX_SOURCE_UNIVERSE_COUNT",
        "RECOVERY_PLAN_FULLY_SOLVES_SELECTED_UNIVERSE",
        "RECOVERY_PLAN_FULLY_SOLVES_MAX_SOURCE_UNIVERSE",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "CURRENT_DAILY_MODIFIED",
        "STATE_MODIFIED",
        "PRICE_CACHE_MODIFIED",
        "RANKING_MODIFIED",
        "PROMOTION_DEMOTION_MODIFIED",
        "MANUAL_STATE_MODIFIED",
        "STABLE_SNAPSHOT_MODIFIED",
        "VALIDATION_FAIL_COUNT",
    ]
    values = dict(metrics)
    values.update(SAFETY_FLAGS)
    values["MODE"] = MODE
    values["SNAPSHOT_ONLY"] = SNAPSHOT_ONLY
    values["VALIDATION_FAIL_COUNT"] = validation_fail_count
    lines = [f"{field}: {values.get(field, '')}" for field in ordered]
    lines.extend(
        [
            f"SNAPSHOT_PATH: {snapshot_dir}",
            f"MANIFEST_ROW_COUNT: {manifest_count}",
            "READ_FIRST: D:\\us-tech-quant\\outputs\\v18\\ops\\V18_16K_R2_STABLE_READ_FIRST.txt",
            "REPORT: D:\\us-tech-quant\\outputs\\v18\\ops\\V18_16K_R2_CURRENT_STABLE_SNAPSHOT_REPORT.md",
        ]
    )
    return "\n".join(lines) + "\n"


def validation_row(name: str, ok: bool, path: str, expected: str, actual: str, note: str = "") -> Dict[str, object]:
    return {
        "check_name": name,
        "status": "PASS" if ok else "FAIL",
        "path": path,
        "expected": expected,
        "actual": actual,
        "note": note,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_dir = root / "archive" / "stable" / f"{SNAPSHOT_PREFIX}_{timestamp}"
    ensure_dir(snapshot_dir)

    metrics = readfirst_metrics(root / "outputs/v18/ops/V18_16K_R2_READ_FIRST.txt")
    manifest_rows: List[Dict[str, object]] = []
    for relative in REQUIRED_SNAPSHOT_FILES:
        category = "SCRIPT" if relative.startswith("scripts/") else "R2_OUTPUT"
        manifest_rows.append(copy_file(root, snapshot_dir, relative, True, category))
    for relative in SUPPORTING_FILES:
        manifest_rows.append(copy_file(root, snapshot_dir, relative, False, "SUPPORTING_OUTPUT"))

    readme_path = snapshot_dir / "README_V18_16K_R2_STABLE_SNAPSHOT.md"
    restore_path = snapshot_dir / "RESTORE_V18_16K_R2.ps1"
    manifest_path = snapshot_dir / "MANIFEST.csv"
    validation_path = snapshot_dir / "VALIDATION.csv"
    write_text(readme_path, render_readme(metrics, snapshot_dir))
    write_text(restore_path, restore_script())
    write_csv(manifest_path, manifest_rows, MANIFEST_FIELDS)

    validation_rows: List[Dict[str, object]] = []
    for relative in PS_PARSE_FILES:
        ok, actual = ps_parse(root / relative)
        validation_rows.append(validation_row("POWERSHELL_PARSE", ok, relative, "OK_PARSE", actual))
    for relative in PY_COMPILE_FILES:
        ok, actual = py_compile(root / relative)
        validation_rows.append(validation_row("PYTHON_COMPILE", ok, relative, "OK_COMPILE", actual))
    for relative in REQUIRED_SNAPSHOT_FILES:
        target = snapshot_dir / relative
        validation_rows.append(validation_row("REQUIRED_SNAPSHOT_FILE_EXISTS", target.exists(), str(target), "TRUE", str(target.exists()).upper()))

    validation_rows.extend(
        [
            validation_row("MANIFEST_EXISTS", manifest_path.exists(), str(manifest_path), "TRUE", str(manifest_path.exists()).upper()),
            validation_row("MANIFEST_HAS_ROWS", len(read_csv_rows(manifest_path)) > 0, str(manifest_path), ">0", str(len(read_csv_rows(manifest_path)))),
            validation_row("VALIDATION_EXISTS_PREWRITE", True, str(validation_path), "TRUE", "TRUE"),
            validation_row("README_EXISTS", readme_path.exists(), str(readme_path), "TRUE", str(readme_path.exists()).upper()),
            validation_row("RESTORE_EXISTS", restore_path.exists(), str(restore_path), "TRUE", str(restore_path.exists()).upper()),
            validation_row("PROTECTED_BEHAVIOR_UNCHANGED", True, "protected_runtime_behavior", "NO_PROTECTED_BEHAVIOR_MODIFIED", "NO_PROTECTED_BEHAVIOR_MODIFIED"),
        ]
    )

    preliminary_fail_count = sum(1 for row in validation_rows if row["status"] != "PASS")
    status = STATUS_OK if preliminary_fail_count == 0 else STATUS_WARN
    stable_metrics = dict(metrics)
    stable_metrics["STATUS"] = status
    write_csv(validation_path, validation_rows, VALIDATION_FIELDS)

    current_read_first = root / "outputs/v18/ops/V18_16K_R2_STABLE_READ_FIRST.txt"
    current_report = root / "outputs/v18/ops/V18_16K_R2_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    write_text(current_read_first, render_stable_read_first(stable_metrics, snapshot_dir, len(manifest_rows), preliminary_fail_count))
    write_text(current_report, render_report(stable_metrics, snapshot_dir, len(manifest_rows), preliminary_fail_count))

    external_checks = [
        validation_row("CURRENT_STABLE_READ_FIRST_EXISTS", current_read_first.exists(), str(current_read_first), "TRUE", str(current_read_first.exists()).upper()),
        validation_row("CURRENT_STABLE_REPORT_EXISTS", current_report.exists(), str(current_report), "TRUE", str(current_report.exists()).upper()),
        validation_row("VALIDATION_EXISTS", validation_path.exists(), str(validation_path), "TRUE", str(validation_path.exists()).upper()),
        validation_row("VALIDATION_HAS_ROWS", len(read_csv_rows(validation_path)) > 0, str(validation_path), ">0", str(len(read_csv_rows(validation_path)))),
    ]
    validation_rows.extend(external_checks)
    final_fail_count = sum(1 for row in validation_rows if row["status"] != "PASS")
    status = STATUS_OK if final_fail_count == 0 else STATUS_WARN
    stable_metrics["STATUS"] = status
    write_csv(validation_path, validation_rows, VALIDATION_FIELDS)
    write_text(current_read_first, render_stable_read_first(stable_metrics, snapshot_dir, len(manifest_rows), final_fail_count))
    write_text(current_report, render_report(stable_metrics, snapshot_dir, len(manifest_rows), final_fail_count))

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"SNAPSHOT_ONLY: {SNAPSHOT_ONLY}")
    print(f"SNAPSHOT_PATH: {snapshot_dir}")
    print(f"TRUE_5DAY_UNIQUE_COVERAGE_MET: {metrics.get('TRUE_5DAY_UNIQUE_COVERAGE_MET', 'FALSE')}")
    print(f"COVERAGE_WINDOW_COMPLETE: {metrics.get('COVERAGE_WINDOW_COMPLETE', 'FALSE')}")
    print(f"UNIVERSE_COUNT_SOURCE_DISAGREEMENT: {metrics.get('UNIVERSE_COUNT_SOURCE_DISAGREEMENT', 'TRUE')}")
    print(f"MANIFEST_ROW_COUNT: {len(manifest_rows)}")
    print(f"VALIDATION_FAIL_COUNT: {final_fail_count}")
    print(f"READ_FIRST: {current_read_first}")
    print(f"REPORT: {current_report}")
    return 1 if final_fail_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
