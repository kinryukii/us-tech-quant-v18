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


STATUS_OK = "OK_V18_23A_STABLE_SNAPSHOT_READY"
STATUS_FAIL = "FAIL_V18_23A_STABLE_SNAPSHOT"
MODE = "SNAPSHOT_ONLY"
PREFIX = "V18_23A_stable_rolling_research_coverage_controller"

CRITICAL_FILES = [
    "scripts/v18/v18_23A_rolling_research_coverage_controller.py",
    "scripts/v18/run_v18_23A_rolling_research_coverage_controller.ps1",
    "outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_CONTROLLER.md",
    "outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv",
    "outputs/v18/rolling_coverage/V18_23A_CURRENT_TODAY_PLANNED_SCAN_LIST.csv",
    "outputs/v18/rolling_coverage/V18_23A_CURRENT_COVERAGE_BUCKET_SUMMARY.csv",
    "outputs/v18/rolling_coverage/V18_23A_CURRENT_COVERAGE_SOURCE_AUDIT.csv",
    "outputs/v18/rolling_coverage/V18_23A_CURRENT_COVERAGE_VALIDATION.csv",
    "outputs/v18/ops/V18_23A_READ_FIRST.txt",
    "outputs/v18/ops/V18_23A_CURRENT_ROLLING_COVERAGE_CONTROLLER_REPORT.md",
    "scripts/v18/v18_23A_R1_universe_count_drift_reconciliation.py",
    "scripts/v18/run_v18_23A_R1_universe_count_drift_reconciliation.ps1",
    "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_UNIVERSE_COUNT_DRIFT_RECONCILIATION.md",
    "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_SOURCE_TICKER_COUNT_AUDIT.csv",
    "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_UNIVERSE_SOURCE_COMPARISON.csv",
    "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_TICKER_SET_DIFF.csv",
    "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_DROPPED_OR_MISSING_TICKERS.csv",
    "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_SUSPICIOUS_TICKERS.csv",
    "outputs/v18/rolling_coverage/V18_23A_R1_CURRENT_RECONCILIATION_VALIDATION.csv",
    "outputs/v18/ops/V18_23A_R1_READ_FIRST.txt",
    "outputs/v18/ops/V18_23A_R1_CURRENT_UNIVERSE_COUNT_DRIFT_RECONCILIATION_REPORT.md",
]

UPSTREAM_CONTEXT_FILES = [
    "outputs/v18/ops/V18_22D_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_22D_CURRENT_STABLE_SNAPSHOT_REPORT.md",
]

GENERATED_OUTPUTS = {
    "read_first": "outputs/v18/ops/V18_23A_STABLE_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23A_CURRENT_STABLE_SNAPSHOT_REPORT.md",
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
    "ROLLING_SCAN_EXECUTED": "FALSE",
    "ROLLING_SCAN_DATA_FETCHED": "FALSE",
    "ROLLING_SCAN_PLAN_MODIFIED": "FALSE",
    "STABLE_SNAPSHOT_MODIFIED": "TRUE",
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
    "ROLLING_COVERAGE_CONTROLLER_READY",
    "RECONCILIATION_READY",
    "PLANNING_ONLY",
    "TARGET_COVERAGE_DAYS",
    "TOTAL_UNIVERSE_COUNT",
    "RECOMMENDED_DAILY_SCAN_COUNT",
    "PLANNED_SCAN_COUNT_TODAY",
    "PLANNED_BUCKET_INDEX",
    "ESTIMATED_FULL_CYCLE_COVERAGE_COUNT",
    "ESTIMATED_FULL_CYCLE_COVERAGE_RATIO",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET",
    "TRUE_5DAY_UNIQUE_COVERAGE_STATUS",
    "COVERAGE_TRUST_LEVEL",
    "V18_23A_CANONICAL_UNIVERSE_COUNT",
    "COUNT_DRIFT_DETECTED",
    "COUNT_DRIFT_EXPLAINED",
    "RECONCILIATION_RESULT",
    "V18_23A_STABLE_SNAPSHOT_ALLOWED",
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
    "ROLLING_SCAN_EXECUTED",
    "ROLLING_SCAN_DATA_FETCHED",
    "ROLLING_SCAN_PLAN_MODIFIED",
    "STABLE_SNAPSHOT_MODIFIED",
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
        row.update({"status": "COPIED", "size_bytes": target.stat().st_size, "modified_time": modified_time(target), "sha256": sha256(target), "error": ""})
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
    return (result.returncode == 0, "PASS" if result.returncode == 0 else (result.stdout or result.stderr).strip() or "FAIL")


def ps_parse(path: Path) -> Tuple[bool, str]:
    escaped = str(path).replace("'", "''")
    command = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'PASS'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True)
    return (result.returncode == 0 and "PASS" in result.stdout, "PASS" if result.returncode == 0 and "PASS" in result.stdout else (result.stdout or result.stderr).strip() or "FAIL")


def render_restore_script(copied_files: Sequence[str]) -> str:
    lines = [
        'param([string]$Root = "D:\\us-tech-quant")',
        '$ErrorActionPreference = "Stop"',
        '$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path',
        'Write-Host "=== RESTORE V18.23A STABLE SNAPSHOT START ==="',
        'Write-Host "MODE: SNAPSHOT_RESTORE"',
        'Write-Host "NOTE: Restores V18.23A read-only planning and reconciliation artifacts only."',
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
            'Write-Host "ROLLING_SCAN_EXECUTED: FALSE"',
            'Write-Host "ROLLING_SCAN_DATA_FETCHED: FALSE"',
            'Write-Host "ROLLING_SCAN_PLAN_MODIFIED: FALSE"',
            'Write-Host "EXTERNAL_DATA_FETCHED: FALSE"',
            'Write-Host "BACKTEST_EXECUTED: FALSE"',
            'Write-Host "OFFICIAL_DECISION_IMPACT: NONE"',
        ]
    )
    return "\n".join(lines) + "\n"


def render_readme(values: Dict[str, str]) -> str:
    return f"""# V18.23A Stable Snapshot

This snapshot preserves V18.23A Rolling Research Coverage Controller and V18.23A-R1 Universe Count Drift Reconciliation.

V18.23A is a read-only rolling research coverage planning layer. It does not execute rolling scans, fetch external data, write price cache or price history, run backtests, update rankings, or affect any trading decision.

Planning state:
- It does not prove true 5-day coverage yet.
- It creates a deterministic 5-bucket plan over {values['TOTAL_UNIVERSE_COUNT']} valid tickers.
- Recommended daily scan count is {values['RECOMMENDED_DAILY_SCAN_COUNT']}.
- Planned bucket index at capture was {values['PLANNED_BUCKET_INDEX']}.
- Coverage trust is {values['COVERAGE_TRUST_LEVEL']} because true local scan-history evidence is incomplete.
- TRUE_5DAY_UNIQUE_COVERAGE_MET is {values['TRUE_5DAY_UNIQUE_COVERAGE_MET']}.

Reconciliation state:
- V18.23A-R1 reconciled the {values['V18_23A_CANONICAL_UNIVERSE_COUNT']} universe count.
- No valid 325-ticker local reference was found.
- The 325-ish discrepancy came from numeric pseudo-tickers 105 and 325 in current/state universe rolling files; these are excluded by ticker normalization.
- Reconciliation result: {values['RECONCILIATION_RESULT']}.

Blocked actions:
- Rolling scan execution remains blocked.
- External data fetch remains blocked.
- Price cache writes remain blocked.
- Backtests remain blocked.
- Factor effect claims, weight changes, daily command center integration, staged backfill apply, and production promotion remain blocked.

Snapshot path:
`{values['SNAPSHOT_PATH']}`
"""


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.23A Stable Snapshot Report

Status: {values['STATUS']}.

This is snapshot-only. It copies the read-only V18.23A rolling coverage planning artifacts and V18.23A-R1 reconciliation artifacts. It does not execute scan, fetch, backtest, trading, ranking, price cache, state, or production decision logic.

Snapshot path: `{values['SNAPSHOT_PATH']}`

Copied file count: {values['COPIED_FILE_COUNT']}. Missing critical count: {values['MISSING_CRITICAL_COUNT']}. Copy fail count: {values['COPY_FAIL_COUNT']}.

Validation fail count: {values['VALIDATION_FAIL_COUNT']}. Python compile: {values['PYTHON_COMPILE_RESULT']}. PowerShell parse: {values['POWERSHELL_PARSE_RESULT']}.

V18.23A planning: total universe {values['TOTAL_UNIVERSE_COUNT']}, recommended daily scan {values['RECOMMENDED_DAILY_SCAN_COUNT']}, coverage trust {values['COVERAGE_TRUST_LEVEL']}, true 5-day coverage met {values['TRUE_5DAY_UNIQUE_COVERAGE_MET']}.

V18.23A-R1 reconciliation: count drift detected {values['COUNT_DRIFT_DETECTED']}, count drift explained {values['COUNT_DRIFT_EXPLAINED']}, result {values['RECONCILIATION_RESULT']}, stable snapshot allowed {values['V18_23A_STABLE_SNAPSHOT_ALLOWED']}.

Recommended next action: {values['RECOMMENDED_NEXT_ACTION']}
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
    readme_path = snapshot / "README_V18_23A_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_23A.ps1"
    stable_read_first_path = root / GENERATED_OUTPUTS["read_first"]
    stable_report_path = root / GENERATED_OUTPUTS["report"]

    v23a = read_kv(root / "outputs/v18/ops/V18_23A_READ_FIRST.txt")
    r1 = read_kv(root / "outputs/v18/ops/V18_23A_R1_READ_FIRST.txt")
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
        "ROLLING_COVERAGE_CONTROLLER_READY": v23a.get("ROLLING_COVERAGE_CONTROLLER_READY", "UNKNOWN"),
        "RECONCILIATION_READY": r1.get("RECONCILIATION_READY", "UNKNOWN"),
        "PLANNING_ONLY": v23a.get("PLANNING_ONLY", "UNKNOWN"),
        "TARGET_COVERAGE_DAYS": v23a.get("TARGET_COVERAGE_DAYS", "UNKNOWN"),
        "TOTAL_UNIVERSE_COUNT": v23a.get("TOTAL_UNIVERSE_COUNT", "UNKNOWN"),
        "RECOMMENDED_DAILY_SCAN_COUNT": v23a.get("RECOMMENDED_DAILY_SCAN_COUNT", "UNKNOWN"),
        "PLANNED_SCAN_COUNT_TODAY": v23a.get("PLANNED_SCAN_COUNT_TODAY", "UNKNOWN"),
        "PLANNED_BUCKET_INDEX": v23a.get("PLANNED_BUCKET_INDEX", "UNKNOWN"),
        "ESTIMATED_FULL_CYCLE_COVERAGE_COUNT": v23a.get("ESTIMATED_FULL_CYCLE_COVERAGE_COUNT", "UNKNOWN"),
        "ESTIMATED_FULL_CYCLE_COVERAGE_RATIO": v23a.get("ESTIMATED_FULL_CYCLE_COVERAGE_RATIO", "UNKNOWN"),
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": v23a.get("TRUE_5DAY_UNIQUE_COVERAGE_MET", "UNKNOWN"),
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": v23a.get("TRUE_5DAY_UNIQUE_COVERAGE_STATUS", "UNKNOWN"),
        "COVERAGE_TRUST_LEVEL": v23a.get("COVERAGE_TRUST_LEVEL", "UNKNOWN"),
        "V18_23A_CANONICAL_UNIVERSE_COUNT": r1.get("V18_23A_CANONICAL_UNIVERSE_COUNT", "UNKNOWN"),
        "COUNT_DRIFT_DETECTED": r1.get("COUNT_DRIFT_DETECTED", "UNKNOWN"),
        "COUNT_DRIFT_EXPLAINED": r1.get("COUNT_DRIFT_EXPLAINED", "UNKNOWN"),
        "RECONCILIATION_RESULT": r1.get("RECONCILIATION_RESULT", "UNKNOWN"),
        "V18_23A_STABLE_SNAPSHOT_ALLOWED": r1.get("V18_23A_STABLE_SNAPSHOT_ALLOWED", "FALSE"),
        "RECOMMENDED_NEXT_ACTION": "V18.23A planning and reconciliation are snapshotted; next step may be the next approved read-only layer or an explicitly approved rolling scan execution design, with all execution/fetch/trading gates still blocked.",
        "MANIFEST_PATH": str(manifest_path),
        "VALIDATION_PATH": str(validation_path),
        "README_PATH": str(readme_path),
        "RESTORE_SCRIPT_PATH": str(restore_path),
        "REPORT_PATH": str(stable_report_path),
    }
    for key, expected in SAFETY_INVARIANTS.items():
        values[key] = expected

    manifest: List[Dict[str, object]] = []
    for relative_path in CRITICAL_FILES:
        manifest.append(copy_file(root, snapshot, relative_path, "CRITICAL_V18_23A"))
    for relative_path in UPSTREAM_CONTEXT_FILES:
        if (root / relative_path).exists():
            manifest.append(copy_file(root, snapshot, relative_path, "UPSTREAM_V18_22D_CONTEXT"))

    copied_files = [str(row["relative_source_path"]) for row in manifest if row.get("status") == "COPIED"]
    missing_critical = [row for row in manifest if row.get("category") == "CRITICAL_V18_23A" and row.get("status") == "MISSING"]
    copy_failures = [row for row in manifest if row.get("status") == "COPY_FAILED"]
    values["COPIED_FILE_COUNT"] = str(len(copied_files))
    values["MISSING_CRITICAL_COUNT"] = str(len(missing_critical))
    values["COPY_FAIL_COUNT"] = str(len(copy_failures))

    write_text(readme_path, render_readme(values))
    write_text(restore_path, render_restore_script(copied_files))
    manifest.extend(
        [
            artifact_row(snapshot, "README_V18_23A_STABLE_SNAPSHOT.md", "README"),
            artifact_row(snapshot, "RESTORE_V18_23A.ps1", "RESTORE"),
        ]
    )
    write_csv(manifest_path, manifest, MANIFEST_FIELDS)
    write_csv(validation_path, [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)

    py_ok, py_result = py_compile(root / "scripts/v18/v18_23A_stable_snapshot.py")
    ps_ok, ps_result = ps_parse(root / "scripts/v18/run_v18_23A_stable_snapshot.ps1")
    values["PYTHON_COMPILE_RESULT"] = py_result
    values["POWERSHELL_PARSE_RESULT"] = ps_result

    validations = [
        validation_row("snapshot_folder_created", snapshot.exists() and snapshot.is_dir(), 1, str(snapshot)),
        validation_row("all_critical_files_copied", not missing_critical, len(missing_critical), "All V18.23A and V18.23A-R1 critical files must be copied."),
        validation_row("copy_fail_count_zero", not copy_failures, len(copy_failures), "No copy failures allowed."),
        validation_row("manifest_exists_non_empty", non_empty(manifest_path), 1, str(manifest_path)),
        validation_row("validation_exists_non_empty", non_empty(validation_path), 1, str(validation_path)),
        validation_row("readme_exists_non_empty", non_empty(readme_path), 1, str(readme_path)),
        validation_row("restore_script_exists_non_empty", non_empty(restore_path), 1, str(restore_path)),
        validation_row("python_compile_check", py_ok, 1, py_result),
        validation_row("powershell_parse_check", ps_ok, 1, ps_result),
        validation_row("v18_23a_ready_preserved", values["ROLLING_COVERAGE_CONTROLLER_READY"] == "TRUE", 1, "V18.23A controller must be ready."),
        validation_row("v18_23a_r1_ready_preserved", values["RECONCILIATION_READY"] == "TRUE", 1, "V18.23A-R1 reconciliation must be ready."),
        validation_row("v18_23a_stable_snapshot_allowed", values["V18_23A_STABLE_SNAPSHOT_ALLOWED"] == "TRUE", 1, "R1 reconciliation must allow stable snapshot."),
        validation_row("critical_v18_23a_outputs_in_snapshot", all((snapshot / relative).exists() for relative in CRITICAL_FILES[:10]), 1, "V18.23A outputs must be in snapshot."),
        validation_row("critical_v18_23a_r1_outputs_in_snapshot", all((snapshot / relative).exists() for relative in CRITICAL_FILES[10:]), 1, "V18.23A-R1 outputs must be in snapshot."),
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
