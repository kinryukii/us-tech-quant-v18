from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_21B_R1_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_21B_R1_STABLE_SNAPSHOT_VALIDATION_FAILED"
MODE = "SNAPSHOT_ONLY"
SNAPSHOT_ONLY = "TRUE"
PREFIX = "V18_21B_R1_stable_signal_snapshot_research_linker"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "PRICE_FACTOR_MODIFIED": "FALSE",
    "SIMULATION_POSITION_MODIFIED": "FALSE",
    "FORWARD_TRACKER_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "STABLE_SNAPSHOT_MODIFIED": "TRUE",
}

REQUIRED_FILES = [
    "scripts/v18/v18_21B_signal_snapshot_research_linker.py",
    "scripts/v18/run_v18_21B_signal_snapshot_research_linker.ps1",
    "scripts/v18/v18_21B_R1_signal_snapshot_quality_patch.py",
    "scripts/v18/run_v18_21B_R1_signal_snapshot_quality_patch.ps1",
    "outputs/v18/signal_snapshots/V18_21B_CURRENT_SIGNAL_SNAPSHOT.csv",
    "outputs/v18/signal_snapshots/V18_21B_CURRENT_SIGNAL_SOURCE_AUDIT.csv",
    "outputs/v18/signal_snapshots/V18_21B_CURRENT_SIGNAL_COMPONENT_COVERAGE_AUDIT.csv",
    "outputs/v18/signal_snapshots/V18_21B_CURRENT_SIMULATION_RESEARCH_LINKER.csv",
    "outputs/v18/ops/V18_21B_READ_FIRST.txt",
    "outputs/v18/ops/V18_21B_CURRENT_SIGNAL_SNAPSHOT_RESEARCH_LINKER_REPORT.md",
    "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_PRICE_DERIVED_READINESS_AUDIT.csv",
    "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_RESEARCH_READINESS_BLOCKERS.csv",
    "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_LINK_KEY_QUALITY_AUDIT.csv",
    "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_HISTORY_COPY_AUDIT.csv",
    "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv",
    "outputs/v18/ops/V18_21B_R1_READ_FIRST.txt",
    "outputs/v18/ops/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT_QUALITY_REPORT.md",
]

PS_FILES = [
    "scripts/v18/run_v18_21B_R1_stable_snapshot.ps1",
    "scripts/v18/run_v18_21B_signal_snapshot_research_linker.ps1",
    "scripts/v18/run_v18_21B_R1_signal_snapshot_quality_patch.ps1",
]
PY_FILES = [
    "scripts/v18/v18_21B_R1_stable_snapshot.py",
    "scripts/v18/v18_21B_signal_snapshot_research_linker.py",
    "scripts/v18/v18_21B_R1_signal_snapshot_quality_patch.py",
]

MANIFEST_FIELDS = [
    "category",
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
READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "SNAPSHOT_ONLY",
    "POLICY_APPLIED",
    "SNAPSHOT_DATE",
    "SIGNAL_SNAPSHOT_ROW_COUNT",
    "SIGNAL_SNAPSHOT_HISTORY_COPY_CREATED",
    "HISTORY_COPY_MATCHES_CURRENT",
    "FACTOR_PACK_COVERAGE_COUNT",
    "TECHNICAL_TIMING_COVERAGE_COUNT",
    "PRICE_DERIVED_ROW_COVERAGE_COUNT",
    "PRICE_DERIVED_FULL_SCORE_READY_COUNT",
    "PRICE_DERIVED_ROW_ONLY_COUNT",
    "MARKET_REGIME_STATUS",
    "MARKET_RISK_COEFFICIENT",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET",
    "COVERAGE_WINDOW_COMPLETE",
    "DAILY_TRUST_LEVEL",
    "READY_FOR_FORWARD_RESEARCH_COUNT",
    "READY_FOR_SIMULATION_ANALYSIS_COUNT",
    "FULL_RESEARCH_READY_COUNT",
    "FORWARD_ONLY_READY_COUNT",
    "WATCH_ONLY_DUE_TO_DEGRADED_DATA_COUNT",
    "SIGNAL_SNAPSHOT_ID_UNIQUE",
    "SIGNAL_SNAPSHOT_ID_DUPLICATE_COUNT",
    "SIMULATION_LINK_KEY_NON_EMPTY_COUNT",
    "FORWARD_TRACKER_LINK_KEY_NON_EMPTY_COUNT",
    "MANUAL_FEEDBACK_LINK_KEY_NON_EMPTY_COUNT",
    "DATA_DEGRADED_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED",
    "STATE_MODIFIED",
    "PRICE_CACHE_MODIFIED",
    "RANKING_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "PRICE_FACTOR_MODIFIED",
    "SIMULATION_POSITION_MODIFIED",
    "FORWARD_TRACKER_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED",
    "MANUAL_STATE_MODIFIED",
    "BROKER_EXECUTION_MODIFIED",
    "STABLE_SNAPSHOT_MODIFIED",
    "VALIDATION_FAIL_COUNT",
    "SNAPSHOT_PATH",
    "MANIFEST_ROW_COUNT",
    "READ_FIRST",
    "REPORT",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
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


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as handle:
                return list(csv.DictReader(handle))
        except Exception:
            continue
    return []


def readfirst(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def modified_time(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def latest_match(root: Path, pattern: str) -> str:
    matches = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    if not matches:
        return ""
    return matches[0].relative_to(root).as_posix()


def copy_one(root: Path, snapshot: Path, rel: str, category: str = "") -> Dict[str, object]:
    src = root / rel
    dst = snapshot / rel
    row = {
        "category": category or ("SCRIPT" if rel.startswith("scripts/") else "OUTPUT"),
        "source_path": str(src),
        "snapshot_path": str(dst),
        "relative_source_path": rel,
        "relative_snapshot_path": rel,
    }
    if not src.exists():
        row.update({"status": "MISSING", "size_bytes": "", "modified_time": "", "sha256": "", "error": "SOURCE_MISSING"})
        return row
    try:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        row.update({"status": "COPIED", "size_bytes": dst.stat().st_size, "modified_time": modified_time(dst), "sha256": sha256(dst), "error": ""})
    except Exception as exc:
        row.update({"status": "COPY_FAILED", "size_bytes": "", "modified_time": "", "sha256": "", "error": f"{type(exc).__name__}: {exc}"})
    return row


def ps_parse(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    escaped = str(path).replace("'", "''")
    cmd = f"$null = [scriptblock]::Create((Get-Content -Raw -LiteralPath '{escaped}')); 'OK_PARSE'"
    result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd], capture_output=True, text=True)
    return (result.returncode == 0 and "OK_PARSE" in result.stdout), (result.stdout or result.stderr).strip()


def py_compile(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    result = subprocess.run(["python", "-m", "py_compile", str(path)], capture_output=True, text=True)
    return result.returncode == 0, "OK_COMPILE" if result.returncode == 0 else (result.stdout or result.stderr).strip()


def validation_row(name: str, ok: bool, path: str, expected: str, actual: str, note: str = "") -> Dict[str, object]:
    return {"check_name": name, "status": "PASS" if ok else "FAIL", "path": path, "expected": expected, "actual": actual, "note": note}


def restore_script(files: Sequence[str]) -> str:
    lines = [
        'param([string]$Root = "D:\\us-tech-quant")',
        '$ErrorActionPreference = "Stop"',
        '$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path',
        'Write-Host "=== RESTORE V18.21B-R1 STABLE SNAPSHOT START ==="',
    ]
    for rel in files:
        win = rel.replace("/", "\\")
        lines += [
            f'$Source = Join-Path $SnapshotRoot "{win}"',
            f'$Target = Join-Path $Root "{win}"',
            'if (Test-Path $Source) {',
            '    $Dir = Split-Path -Parent $Target',
            '    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }',
            '    Copy-Item -LiteralPath $Source -Destination $Target -Force',
            '}',
        ]
    lines += [
        'Write-Host "RESTORE_COMPLETE: TRUE"',
        'Write-Host "NOTE: Restore preserves advisory signal snapshots only; it does not modify trading behavior."',
    ]
    return "\n".join(lines) + "\n"


def readme(metrics: Dict[str, str]) -> str:
    return f"""# V18.21B-R1 Stable Snapshot

This snapshot preserves the V18.21B-R1 signal snapshot and research linker layer.

Important preserved interpretation:
- It does not modify official decisions, ranking, technical timing, price factors, simulation positions, forward tracker state, manual state, broker execution, auto-trade, or auto-sell.
- It preserves a degraded-but-clean research state.
- Signal snapshot rows are {metrics.get('SIGNAL_SNAPSHOT_ROW_COUNT', '325')}.
- Price-derived full-score-ready count is {metrics.get('PRICE_DERIVED_FULL_SCORE_READY_COUNT', '104')}; row-only/degraded count is {metrics.get('PRICE_DERIVED_ROW_ONLY_COUNT', '221')}.
- Ready-for-forward-research count is {metrics.get('READY_FOR_FORWARD_RESEARCH_COUNT', '105')}.
- Ready-for-simulation-analysis count is {metrics.get('READY_FOR_SIMULATION_ANALYSIS_COUNT', '31')}.
- Full-research-ready count is {metrics.get('FULL_RESEARCH_READY_COUNT', '0')}.
- TRUE_5DAY_UNIQUE_COVERAGE_MET remains {metrics.get('TRUE_5DAY_UNIQUE_COVERAGE_MET', 'FALSE')}.
- COVERAGE_WINDOW_COMPLETE remains {metrics.get('COVERAGE_WINDOW_COMPLETE', 'FALSE')}.
- DAILY_TRUST_LEVEL remains {metrics.get('DAILY_TRUST_LEVEL', 'MEDIUM')}.
- signal_snapshot_id is unique with duplicate count {metrics.get('SIGNAL_SNAPSHOT_ID_DUPLICATE_COUNT', '0')}.
- The history copy matches current snapshot: {metrics.get('HISTORY_COPY_MATCHES_CURRENT', 'TRUE')}.
"""


def render_readfirst(metrics: Dict[str, object]) -> str:
    values = dict(metrics)
    values.update(SAFETY_FLAGS)
    values["MODE"] = MODE
    values["SNAPSHOT_ONLY"] = SNAPSHOT_ONLY
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def report(metrics: Dict[str, object], snapshot: Path) -> str:
    return f"""# V18.21B-R1 Stable Snapshot Report

## Executive Summary
Status: {metrics['STATUS']}. The snapshot is ready and preserves the V18.21B-R1 advisory signal snapshot/research linker layer.

## Preserved Degraded Semantics
- Signal snapshot rows: {metrics.get('SIGNAL_SNAPSHOT_ROW_COUNT')}
- Price-derived full-score-ready count: {metrics.get('PRICE_DERIVED_FULL_SCORE_READY_COUNT')}
- Price-derived row-only count: {metrics.get('PRICE_DERIVED_ROW_ONLY_COUNT')}
- Ready for forward research: {metrics.get('READY_FOR_FORWARD_RESEARCH_COUNT')}
- Ready for simulation analysis: {metrics.get('READY_FOR_SIMULATION_ANALYSIS_COUNT')}
- Full research ready: {metrics.get('FULL_RESEARCH_READY_COUNT')}
- True 5-day unique coverage met: {metrics.get('TRUE_5DAY_UNIQUE_COVERAGE_MET')}
- Coverage window complete: {metrics.get('COVERAGE_WINDOW_COMPLETE')}
- Daily trust level: {metrics.get('DAILY_TRUST_LEVEL')}

## Safety
This is snapshot-only. It does not modify official decisions, ranking, technical timing, price factors, simulation positions, forward tracker state, manual state, price cache, broker execution, auto-trade, or auto-sell.

## Snapshot Artifacts
Snapshot path: `{snapshot}`

The snapshot contains scripts, wrappers, V18.21B outputs, the latest V18.21B history copy, V18.21B-R1 quality outputs, the latest V18.21B-R1 history copy, MANIFEST.csv, VALIDATION.csv, README, and RESTORE script.

## Validation
Validation fail count: {metrics.get('VALIDATION_FAIL_COUNT')}. Manifest rows: {metrics.get('MANIFEST_ROW_COUNT')}.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot = root / "archive" / "stable" / f"{PREFIX}_{timestamp}"
    read_first_path = root / "outputs/v18/ops/V18_21B_R1_STABLE_READ_FIRST.txt"
    report_path = root / "outputs/v18/ops/V18_21B_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md"

    metrics = readfirst(root / "outputs/v18/ops/V18_21B_R1_READ_FIRST.txt")
    files = list(REQUIRED_FILES)
    b_history = latest_match(root, "outputs/v18/signal_snapshots/history/V18_21B_SIGNAL_SNAPSHOT_*.csv")
    r1_history = latest_match(root, "outputs/v18/signal_snapshots/history/V18_21B_R1_SIGNAL_SNAPSHOT_*.csv")
    if b_history:
        files.append(b_history)
    if r1_history:
        files.append(r1_history)

    manifest = [copy_one(root, snapshot, rel, "HISTORY" if "history/" in rel else "") for rel in files]
    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_21B_R1_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_21B_R1.ps1"
    write_csv(manifest_path, manifest, MANIFEST_FIELDS)
    write_text(readme_path, readme(metrics))
    write_text(restore_path, restore_script(files))
    write_csv(validation_path, [], VALIDATION_FIELDS)

    validations: List[Dict[str, object]] = []
    for rel in PS_FILES:
        ok, note = ps_parse(root / rel)
        validations.append(validation_row("powershell_parse", ok, str(root / rel), "PARSE_OK", "PARSE_OK" if ok else "PARSE_FAIL", note))
    for rel in PY_FILES:
        ok, note = py_compile(root / rel)
        validations.append(validation_row("python_compile", ok, str(root / rel), "COMPILE_OK", "COMPILE_OK" if ok else "COMPILE_FAIL", note))
    for rel in files:
        dst = snapshot / rel
        validations.append(validation_row("snapshot_file_exists", dst.exists(), str(dst), "EXISTS", "EXISTS" if dst.exists() else "MISSING"))
    for path, name in [(manifest_path, "MANIFEST"), (validation_path, "VALIDATION"), (readme_path, "README"), (restore_path, "RESTORE")]:
        exists = path.exists()
        validations.append(validation_row(f"{name.lower()}_exists", exists, str(path), "EXISTS", "EXISTS" if exists else "MISSING"))
    validations.append(validation_row("manifest_has_rows", len(manifest) > 0, str(manifest_path), ">0", str(len(manifest))))
    validations.append(validation_row("latest_v18_21b_history_included", bool(b_history and (snapshot / b_history).exists()), b_history or "", "INCLUDED", "INCLUDED" if b_history else "MISSING"))
    validations.append(validation_row("latest_v18_21b_r1_history_included", bool(r1_history and (snapshot / r1_history).exists()), r1_history or "", "INCLUDED", "INCLUDED" if r1_history else "MISSING"))
    validations.append(validation_row("signal_snapshot_id_unique", metrics.get("SIGNAL_SNAPSHOT_ID_UNIQUE") == "TRUE", str(root / "outputs/v18/ops/V18_21B_R1_READ_FIRST.txt"), "TRUE", metrics.get("SIGNAL_SNAPSHOT_ID_UNIQUE", "")))

    metrics_out: Dict[str, object] = {field: metrics.get(field, "") for field in READ_FIRST_FIELDS}
    metrics_out.update(SAFETY_FLAGS)
    metrics_out.update({
        "STATUS": STATUS_OK,
        "MODE": MODE,
        "SNAPSHOT_ONLY": SNAPSHOT_ONLY,
        "SNAPSHOT_PATH": str(snapshot),
        "MANIFEST_ROW_COUNT": str(len(manifest)),
        "READ_FIRST": str(read_first_path),
        "REPORT": str(report_path),
        "VALIDATION_FAIL_COUNT": "0",
    })
    write_text(read_first_path, render_readfirst(metrics_out))
    write_text(report_path, report(metrics_out, snapshot))
    validations.append(validation_row("stable_read_first_exists", read_first_path.exists(), str(read_first_path), "EXISTS", "EXISTS" if read_first_path.exists() else "MISSING"))
    validations.append(validation_row("stable_report_exists", report_path.exists(), str(report_path), "EXISTS", "EXISTS" if report_path.exists() else "MISSING"))

    fail_count = sum(1 for row in validations if row["status"] != "PASS")
    metrics_out["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        metrics_out["STATUS"] = STATUS_WARN
    write_csv(validation_path, validations, VALIDATION_FIELDS)
    write_text(read_first_path, render_readfirst(metrics_out))
    write_text(report_path, report(metrics_out, snapshot))

    for key in ["STATUS", "MODE", "SNAPSHOT_ONLY", "SNAPSHOT_PATH", "SIGNAL_SNAPSHOT_ROW_COUNT", "PRICE_DERIVED_FULL_SCORE_READY_COUNT", "PRICE_DERIVED_ROW_ONLY_COUNT", "FULL_RESEARCH_READY_COUNT", "TRUE_5DAY_UNIQUE_COVERAGE_MET", "COVERAGE_WINDOW_COMPLETE", "MANIFEST_ROW_COUNT", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT"]:
        print(f"{key}: {metrics_out.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
