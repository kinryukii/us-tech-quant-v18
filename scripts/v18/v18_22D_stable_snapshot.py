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


STATUS_OK = "OK_V18_22D_STABLE_SNAPSHOT_READY"
STATUS_FAIL = "FAIL_V18_22D_STABLE_SNAPSHOT"
MODE = "SNAPSHOT_ONLY"
PREFIX = "V18_22D_stable_daily_research_operator_homepage"

CRITICAL_FILES = [
    "scripts/v18/v18_22D_daily_research_operator_homepage.py",
    "scripts/v18/run_v18_22D_daily_research_operator_homepage.ps1",
    "outputs/v18/operator_homepage/V18_22D_CURRENT_DAILY_RESEARCH_OPERATOR_HOMEPAGE.md",
    "outputs/v18/operator_homepage/V18_22D_CURRENT_OPERATOR_GATE_SUMMARY.csv",
    "outputs/v18/operator_homepage/V18_22D_CURRENT_OPERATOR_SOURCE_AUDIT.csv",
    "outputs/v18/operator_homepage/V18_22D_CURRENT_OPERATOR_VALIDATION.csv",
    "outputs/v18/ops/V18_22D_READ_FIRST.txt",
    "outputs/v18/ops/V18_22D_CURRENT_DAILY_RESEARCH_OPERATOR_HOMEPAGE_REPORT.md",
]

UPSTREAM_CONTEXT_FILES = [
    "outputs/v18/ops/V18_22A_READ_FIRST.txt",
    "outputs/v18/ops/V18_22A_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_22A_CURRENT_RESEARCH_COMMAND_CENTER_REPORT.md",
    "outputs/v18/ops/V18_22A_CURRENT_STABLE_SNAPSHOT_REPORT.md",
    "outputs/v18/ops/V18_22B_READ_FIRST.txt",
    "outputs/v18/ops/V18_22B_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_22B_CURRENT_DAILY_RESEARCH_COMMAND_CENTER_WRAPPER_REPORT.md",
    "outputs/v18/ops/V18_22B_CURRENT_STABLE_SNAPSHOT_REPORT.md",
    "outputs/v18/ops/V18_22C_READ_FIRST.txt",
    "outputs/v18/ops/V18_22C_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_22C_CURRENT_RESEARCH_PACKET_WRITER_REPORT.md",
    "outputs/v18/ops/V18_22C_CURRENT_STABLE_SNAPSHOT_REPORT.md",
]

GENERATED_OUTPUTS = {
    "read_first": "outputs/v18/ops/V18_22D_STABLE_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_22D_CURRENT_STABLE_SNAPSHOT_REPORT.md",
}

SAFETY_INVARIANTS = {
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "STAGED_PRICE_HISTORY_WRITTEN": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "EVENT_CALENDAR_MODIFIED": "FALSE",
    "SIMULATION_POSITION_MODIFIED": "FALSE",
    "FORWARD_TRACKER_MODIFIED": "FALSE",
    "PRICE_FACTOR_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "BACKTEST_EXECUTED": "FALSE",
    "BACKTEST_RESULTS_APPLIED": "FALSE",
    "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
    "WEIGHT_CHANGE_ALLOWED": "FALSE",
    "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
    "STAGED_BACKFILL_APPLY_ALLOWED": "FALSE",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": "FALSE",
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "SNAPSHOT_PATH",
    "SNAPSHOT_MODIFIED",
    "COPIED_FILE_COUNT",
    "MISSING_CRITICAL_COUNT",
    "COPY_FAIL_COUNT",
    "VALIDATION_FAIL_COUNT",
    "PYTHON_COMPILE_RESULT",
    "POWERSHELL_PARSE_RESULT",
    "OPERATOR_HOMEPAGE_READY",
    "SOURCE_CURRENT_AVAILABLE",
    "SOURCE_STABLE_AVAILABLE",
    "SOURCE_MISSING_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE",
    "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED",
    "STATE_MODIFIED",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_WRITTEN",
    "STAGED_PRICE_HISTORY_WRITTEN",
    "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED",
    "EVENT_CALENDAR_MODIFIED",
    "SIMULATION_POSITION_MODIFIED",
    "FORWARD_TRACKER_MODIFIED",
    "PRICE_FACTOR_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED",
    "MANUAL_STATE_MODIFIED",
    "BROKER_EXECUTION_MODIFIED",
    "EXTERNAL_DATA_FETCHED",
    "BACKTEST_EXECUTED",
    "BACKTEST_RESULTS_APPLIED",
    "FACTOR_EFFECT_CLAIM_ALLOWED",
    "WEIGHT_CHANGE_ALLOWED",
    "PRODUCTION_PROMOTION_ALLOWED",
    "STAGED_BACKFILL_APPLY_ALLOWED",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "RECOMMENDED_NEXT_ACTION",
    "MANIFEST_PATH",
    "VALIDATION_PATH",
    "README_PATH",
    "RESTORE_SCRIPT_PATH",
    "REPORT_PATH",
]

MANIFEST_FIELDS = [
    "category",
    "status",
    "relative_source_path",
    "relative_snapshot_path",
    "source_path",
    "snapshot_path",
    "size_bytes",
    "modified_time",
    "sha256",
    "error",
]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_kv(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def modified_time(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def copy_file(root: Path, snapshot: Path, relative_path: str, category: str) -> Dict[str, object]:
    source = root / relative_path
    target = snapshot / relative_path
    row = {
        "category": category,
        "relative_source_path": relative_path,
        "relative_snapshot_path": relative_path,
        "source_path": str(source),
        "snapshot_path": str(target),
    }
    if not source.exists():
        row.update({"status": "MISSING", "size_bytes": "", "modified_time": "MISSING", "sha256": "", "error": "SOURCE_MISSING"})
        return row
    try:
        ensure_dir(target.parent)
        shutil.copy2(source, target)
        row.update(
            {
                "status": "COPIED",
                "size_bytes": target.stat().st_size,
                "modified_time": modified_time(target),
                "sha256": sha256(target),
                "error": "",
            }
        )
    except OSError as exc:
        row.update({"status": "COPY_FAILED", "size_bytes": "", "modified_time": "", "sha256": "", "error": str(exc)})
    return row


def artifact_row(snapshot: Path, relative_path: str, category: str) -> Dict[str, object]:
    path = snapshot / relative_path
    row = {
        "category": category,
        "relative_source_path": relative_path,
        "relative_snapshot_path": relative_path,
        "source_path": str(path),
        "snapshot_path": str(path),
    }
    if not path.exists():
        row.update({"status": "MISSING", "size_bytes": "", "modified_time": "MISSING", "sha256": "", "error": "ARTIFACT_MISSING"})
        return row
    row.update({"status": "CREATED", "size_bytes": path.stat().st_size, "modified_time": modified_time(path), "sha256": sha256(path), "error": ""})
    return row


def py_compile(path: Path) -> Tuple[bool, str]:
    result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
    if result.returncode == 0:
        return True, "PASS"
    return False, (result.stdout or result.stderr).strip() or "FAIL"


def ps_parse(path: Path) -> Tuple[bool, str]:
    escaped = str(path).replace("'", "''")
    command = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'PASS'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True)
    if result.returncode == 0 and "PASS" in result.stdout:
        return True, "PASS"
    return False, (result.stdout or result.stderr).strip() or "FAIL"


def render_restore_script(copied_files: Sequence[str]) -> str:
    lines = [
        'param([string]$Root = "D:\\us-tech-quant")',
        '$ErrorActionPreference = "Stop"',
        '$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path',
        'Write-Host "=== RESTORE V18.22D STABLE SNAPSHOT START ==="',
        'Write-Host "MODE: SNAPSHOT_RESTORE"',
        'Write-Host "NOTE: Restores V18.22D read-only operator homepage scripts and outputs only."',
    ]
    for relative_path in copied_files:
        win_path = relative_path.replace("/", "\\")
        lines.extend(
            [
                f'$Source = Join-Path $SnapshotRoot "{win_path}"',
                f'$Target = Join-Path $Root "{win_path}"',
                "if (Test-Path -LiteralPath $Source) {",
                "    $TargetDir = Split-Path -Parent $Target",
                "    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }",
                "    Copy-Item -LiteralPath $Source -Destination $Target -Force",
                "}",
            ]
        )
    lines.extend(
        [
            'Write-Host "RESTORE_COMPLETE: TRUE"',
            'Write-Host "OFFICIAL_DECISION_IMPACT: NONE"',
            'Write-Host "AUTO_TRADE: DISABLED"',
            'Write-Host "AUTO_SELL: DISABLED"',
            'Write-Host "EXTERNAL_DATA_FETCHED: FALSE"',
            'Write-Host "BACKTEST_EXECUTED: FALSE"',
        ]
    )
    return "\n".join(lines) + "\n"


def render_readme(values: Dict[str, str]) -> str:
    return f"""# V18.22D Stable Snapshot

This snapshot preserves the V18.22D Daily Research Operator Homepage layer.

It locks a clean, readable, verifiable daily research homepage state before future V18.23A rolling coverage controller work.

Preserved scope:
- V18.22D homepage generator script and PowerShell wrapper.
- V18.22D operator homepage Markdown.
- V18.22D gate summary, source audit, and validation CSVs.
- V18.22D READ_FIRST and implementation report.
- Available V18.22A, V18.22B, and V18.22C READ_FIRST/report context.

Safety interpretation:
- Snapshot-only.
- No external data fetched.
- No official decision, buy permission, ranking, signal snapshot, event calendar, simulation, forward tracker, price factor, technical timing, price cache, price history, manual state, broker execution, auto-trade, or auto-sell state was modified.
- Research gates remain blocked: factor effect claims, weight changes, production promotion, staged backfill apply, and daily command center integration are all FALSE.

Snapshot path:
`{values['SNAPSHOT_PATH']}`
"""


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.22D Stable Snapshot Report

## Summary
Status: {values['STATUS']}. This stable snapshot preserves the read-only V18.22D Daily Research Operator Homepage.

## Snapshot
Snapshot path: `{values['SNAPSHOT_PATH']}`

Copied file count: {values['COPIED_FILE_COUNT']}. Missing critical count: {values['MISSING_CRITICAL_COUNT']}. Copy fail count: {values['COPY_FAIL_COUNT']}.

## Validation
Validation fail count: {values['VALIDATION_FAIL_COUNT']}. Python compile: {values['PYTHON_COMPILE_RESULT']}. PowerShell parse: {values['POWERSHELL_PARSE_RESULT']}.

## Gate State
Factor effect claim allowed: {values['FACTOR_EFFECT_CLAIM_ALLOWED']}. Weight change allowed: {values['WEIGHT_CHANGE_ALLOWED']}. Production promotion allowed: {values['PRODUCTION_PROMOTION_ALLOWED']}. Staged backfill apply allowed: {values['STAGED_BACKFILL_APPLY_ALLOWED']}. Daily command center integration allowed: {values['DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED']}.

## Safety
Official decision impact: {values['OFFICIAL_DECISION_IMPACT']}. External data fetched: {values['EXTERNAL_DATA_FETCHED']}. Backtest executed: {values['BACKTEST_EXECUTED']}. Backtest results applied: {values['BACKTEST_RESULTS_APPLIED']}.

## Recommended Next Step
{values['RECOMMENDED_NEXT_ACTION']}
"""


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot = root / "archive/stable" / f"{PREFIX}_{timestamp}"
    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_22D_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_22D.ps1"
    stable_read_first_path = root / GENERATED_OUTPUTS["read_first"]
    stable_report_path = root / GENERATED_OUTPUTS["report"]

    d_read_first = read_kv(root / "outputs/v18/ops/V18_22D_READ_FIRST.txt")
    values: Dict[str, str] = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "SNAPSHOT_PATH": str(snapshot),
        "SNAPSHOT_MODIFIED": "TRUE",
        "COPIED_FILE_COUNT": "0",
        "MISSING_CRITICAL_COUNT": "0",
        "COPY_FAIL_COUNT": "0",
        "VALIDATION_FAIL_COUNT": "0",
        "PYTHON_COMPILE_RESULT": "FAIL",
        "POWERSHELL_PARSE_RESULT": "FAIL",
        "OPERATOR_HOMEPAGE_READY": d_read_first.get("OPERATOR_HOMEPAGE_READY", "UNKNOWN"),
        "SOURCE_CURRENT_AVAILABLE": d_read_first.get("SOURCE_CURRENT_AVAILABLE", "UNKNOWN"),
        "SOURCE_STABLE_AVAILABLE": d_read_first.get("SOURCE_STABLE_AVAILABLE", "UNKNOWN"),
        "SOURCE_MISSING_COUNT": d_read_first.get("SOURCE_MISSING_COUNT", "UNKNOWN"),
        "RECOMMENDED_NEXT_ACTION": "Proceed to V18.23A rolling coverage controller planning only after reading outputs/v18/ops/V18_22D_STABLE_READ_FIRST.txt; keep all research and production gates blocked until separately approved.",
        "MANIFEST_PATH": str(manifest_path),
        "VALIDATION_PATH": str(validation_path),
        "README_PATH": str(readme_path),
        "RESTORE_SCRIPT_PATH": str(restore_path),
        "REPORT_PATH": str(stable_report_path),
    }
    for key, expected in SAFETY_INVARIANTS.items():
        values[key] = d_read_first.get(key, expected)

    manifest: List[Dict[str, object]] = []
    for relative_path in CRITICAL_FILES:
        manifest.append(copy_file(root, snapshot, relative_path, "CRITICAL_V18_22D"))
    for relative_path in UPSTREAM_CONTEXT_FILES:
        if (root / relative_path).exists():
            manifest.append(copy_file(root, snapshot, relative_path, "UPSTREAM_CONTEXT"))

    copied_files = [str(row["relative_source_path"]) for row in manifest if row.get("status") == "COPIED"]
    missing_critical = [row for row in manifest if row.get("category") == "CRITICAL_V18_22D" and row.get("status") == "MISSING"]
    copy_failures = [row for row in manifest if row.get("status") == "COPY_FAILED"]
    values["COPIED_FILE_COUNT"] = str(len(copied_files))
    values["MISSING_CRITICAL_COUNT"] = str(len(missing_critical))
    values["COPY_FAIL_COUNT"] = str(len(copy_failures))

    write_text(readme_path, render_readme(values))
    write_text(restore_path, render_restore_script(copied_files))
    manifest.extend(
        [
            artifact_row(snapshot, "README_V18_22D_STABLE_SNAPSHOT.md", "README"),
            artifact_row(snapshot, "RESTORE_V18_22D.ps1", "RESTORE"),
        ]
    )
    write_csv(manifest_path, manifest, MANIFEST_FIELDS)
    write_csv(validation_path, [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)

    py_ok, py_result = py_compile(root / "scripts/v18/v18_22D_stable_snapshot.py")
    ps_ok, ps_result = ps_parse(root / "scripts/v18/run_v18_22D_stable_snapshot.ps1")
    values["PYTHON_COMPILE_RESULT"] = py_result
    values["POWERSHELL_PARSE_RESULT"] = ps_result

    validations = [
        validation_row("snapshot_folder_created", snapshot.exists() and snapshot.is_dir(), 1, str(snapshot)),
        validation_row("all_critical_files_copied", not missing_critical, len(missing_critical), "All critical V18.22D files must be copied."),
        validation_row("copy_fail_count_zero", not copy_failures, len(copy_failures), "No copy failures allowed."),
        validation_row("manifest_exists_non_empty", non_empty(manifest_path), 1, str(manifest_path)),
        validation_row("readme_exists_non_empty", non_empty(readme_path), 1, str(readme_path)),
        validation_row("restore_script_exists_non_empty", non_empty(restore_path), 1, str(restore_path)),
        validation_row("python_compile_check", py_ok, 1, py_result),
        validation_row("powershell_parse_check", ps_ok, 1, ps_result),
        validation_row("operator_homepage_ready_preserved", values["OPERATOR_HOMEPAGE_READY"] == "TRUE", 1, "V18.22D homepage must have been ready."),
    ]
    for key, expected in SAFETY_INVARIANTS.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))

    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    values["STATUS"] = STATUS_OK if fail_count == 0 else STATUS_FAIL

    write_csv(validation_path, validations, VALIDATION_FIELDS)
    manifest.append(artifact_row(snapshot, "VALIDATION.csv", "VALIDATION"))
    manifest.append(artifact_row(snapshot, "MANIFEST.csv", "MANIFEST"))
    write_csv(manifest_path, manifest, MANIFEST_FIELDS)
    write_text(stable_read_first_path, render_read_first(values))
    write_text(stable_report_path, render_report(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
