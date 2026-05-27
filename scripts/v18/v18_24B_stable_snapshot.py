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


STATUS_OK = "OK_V18_24B_STABLE_SNAPSHOT_READY"
STATUS_FAIL = "FAIL_V18_24B_STABLE_SNAPSHOT"
MODE = "SNAPSHOT_ONLY"
PREFIX = "V18_24B_stable_tier_migration_operator_homepage"

CRITICAL_FILES = [
    "scripts/v18/v18_24A_dynamic_score_tier_migration_audit.py",
    "scripts/v18/run_v18_24A_dynamic_score_tier_migration_audit.ps1",
    "outputs/v18/tier_migration/V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT.md",
    "outputs/v18/tier_migration/V18_24A_CURRENT_SCORE_TIER_SNAPSHOT.csv",
    "outputs/v18/tier_migration/V18_24A_CURRENT_TIER_MOVEMENT_REPORT.csv",
    "outputs/v18/tier_migration/V18_24A_CURRENT_UPGRADES.csv",
    "outputs/v18/tier_migration/V18_24A_CURRENT_DOWNGRADES.csv",
    "outputs/v18/tier_migration/V18_24A_CURRENT_LARGE_SCORE_MOVES.csv",
    "outputs/v18/tier_migration/V18_24A_CURRENT_NEWLY_SCORE_READY.csv",
    "outputs/v18/tier_migration/V18_24A_CURRENT_DATA_NOT_READY_OR_BLOCKED.csv",
    "outputs/v18/tier_migration/V18_24A_CURRENT_TIER_SUMMARY.csv",
    "outputs/v18/tier_migration/V18_24A_CURRENT_SOURCE_AUDIT.csv",
    "outputs/v18/tier_migration/V18_24A_CURRENT_VALIDATION.csv",
    "outputs/v18/ops/V18_24A_READ_FIRST.txt",
    "outputs/v18/ops/V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT_REPORT.md",
    "scripts/v18/v18_24B_tier_migration_operator_homepage.py",
    "scripts/v18/run_v18_24B_tier_migration_operator_homepage.ps1",
    "outputs/v18/operator_homepage/V18_24B_CURRENT_TIER_MIGRATION_OPERATOR_HOMEPAGE.md",
    "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_TIER_SUMMARY.csv",
    "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_MOVEMENT_HIGHLIGHTS.csv",
    "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_TOP_TIER_CANDIDATES.csv",
    "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_DATA_NOT_READY_SUMMARY.csv",
    "outputs/v18/tier_migration/V18_24B_CURRENT_SOURCE_AUDIT.csv",
    "outputs/v18/tier_migration/V18_24B_CURRENT_VALIDATION.csv",
    "outputs/v18/ops/V18_24B_READ_FIRST.txt",
    "outputs/v18/ops/V18_24B_CURRENT_TIER_MIGRATION_OPERATOR_HOMEPAGE_REPORT.md",
]

OPTIONAL_CONTEXT = [
    "outputs/v18/ops/V18_23C_R3_READ_FIRST.txt",
    "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_5DAY_COVERAGE_AUDIT.csv",
    "outputs/v18/ops/V18_23A_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_22D_STABLE_READ_FIRST.txt",
]

GENERATED_OUTPUTS = {
    "read_first": "outputs/v18/ops/V18_24B_STABLE_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_24B_CURRENT_STABLE_SNAPSHOT_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "SNAPSHOT_PATH", "SNAPSHOT_MODIFIED", "COPIED_FILE_COUNT",
    "MISSING_CRITICAL_COUNT", "COPY_FAIL_COUNT", "VALIDATION_FAIL_COUNT", "PYTHON_COMPILE_RESULT",
    "POWERSHELL_PARSE_RESULT", "TIER_MIGRATION_AUDIT_READY", "TIER_MIGRATION_OPERATOR_HOMEPAGE_READY",
    "V18_24A_BASELINE_MODE", "CURRENT_TICKER_COUNT", "CURRENT_SCORE_SOURCE", "CURRENT_SCORE_SOURCE_TRUST",
    "TIER_1_CORE_CANDIDATE_COUNT", "TIER_2_STRONG_WATCHLIST_COUNT", "TIER_3_WATCHLIST_COUNT",
    "TIER_4_REVIEW_ONLY_COUNT", "TIER_5_WEAK_OR_BLOCKED_COUNT", "TIER_0_DATA_NOT_READY_COUNT",
    "MOVEMENT_REPORT_AVAILABLE", "TOTAL_MOVEMENT_COUNT", "UPGRADE_COUNT", "DOWNGRADE_COUNT",
    "LARGE_SCORE_MOVE_COUNT", "NEWLY_SCORE_READY_COUNT", "DATA_NOT_READY_OR_BLOCKED_COUNT",
    "TOP_TIER_CANDIDATE_COUNT", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "AUTO_TRADE",
    "AUTO_SELL", "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_WRITTEN",
    "LEDGER_MODIFIED", "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED", "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED", "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED",
    "FACTOR_EFFECT_CLAIM_ALLOWED", "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED", "TRUE_5DAY_UNIQUE_COVERAGE_MET",
    "TRUE_5DAY_UNIQUE_COVERAGE_STATUS", "RECOMMENDED_NEXT_ACTION", "MANIFEST_PATH", "VALIDATION_PATH",
    "README_PATH", "RESTORE_SCRIPT_PATH", "REPORT_PATH",
]

MANIFEST_FIELDS = [
    "category", "status", "relative_source_path", "relative_snapshot_path", "source_path", "snapshot_path",
    "size_bytes", "modified_time", "sha256", "error",
]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]

SAFETY = {
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "STAGED_PRICE_HISTORY_WRITTEN": "FALSE",
    "LEDGER_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "FACTOR_PACK_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "BACKTEST_EXECUTED": "FALSE",
    "BACKTEST_RESULTS_APPLIED": "FALSE",
    "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
    "WEIGHT_CHANGE_ALLOWED": "FALSE",
    "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": "FALSE",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_kv(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


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
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else "MISSING"


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def copy_file(root: Path, snapshot: Path, relative_path: str, category: str) -> Dict[str, object]:
    source = root / relative_path
    target = snapshot / relative_path
    row: Dict[str, object] = {
        "category": category,
        "relative_source_path": relative_path,
        "relative_snapshot_path": relative_path,
        "source_path": str(source),
        "snapshot_path": str(target),
        "status": "PENDING",
        "size_bytes": "",
        "modified_time": "",
        "sha256": "",
        "error": "",
    }
    if not source.exists():
        row["status"] = "MISSING"
        row["error"] = "source file missing"
        return row
    try:
        ensure_dir(target.parent)
        shutil.copy2(source, target)
        row["status"] = "COPIED"
        row["size_bytes"] = target.stat().st_size
        row["modified_time"] = modified_time(source)
        row["sha256"] = sha256(target)
    except Exception as exc:  # noqa: BLE001
        row["status"] = "COPY_FAIL"
        row["error"] = str(exc)
    return row


def latest_history_files(root: Path) -> List[str]:
    history = root / "outputs/v18/tier_migration/history"
    out: List[str] = []
    for pattern in ("V18_24A_SCORE_TIER_SNAPSHOT_*.csv", "V18_24A_TIER_MOVEMENT_REPORT_*.csv"):
        matches = sorted(history.glob(pattern), key=lambda p: p.name, reverse=True) if history.exists() else []
        if matches:
            out.append(str(matches[0].relative_to(root)).replace("\\", "/"))
    return out


def py_compile(path: Path) -> Tuple[str, str]:
    result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
    return ("PASS" if result.returncode == 0 else "FAIL", (result.stderr or result.stdout).strip())


def ps_parse(path: Path) -> Tuple[str, str]:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    ok = result.returncode == 0 and "OK" in result.stdout
    return ("PASS" if ok else "FAIL", (result.stderr or result.stdout).strip())


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_readme(values: Dict[str, str]) -> str:
    return f"""# V18.24B Stable Snapshot

Created: {dt.datetime.now().isoformat(timespec='seconds')}

This snapshot preserves the V18.24A read-only dynamic score tier migration baseline and the V18.24B tier migration operator homepage integration.

V18.24A creates a read-only dynamic score tier migration baseline. V18.24B integrates tier migration into an operator homepage. This is baseline mode, so upgrades and downgrades are expected to be zero until future reruns compare against this baseline.

Current tier counts:
- Tier 1: {values['TIER_1_CORE_CANDIDATE_COUNT']}
- Tier 2: {values['TIER_2_STRONG_WATCHLIST_COUNT']}
- Tier 3: {values['TIER_3_WATCHLIST_COUNT']}
- Tier 4: {values['TIER_4_REVIEW_ONLY_COUNT']}
- Tier 5: {values['TIER_5_WEAK_OR_BLOCKED_COUNT']}
- Tier 0 data not ready: {values['TIER_0_DATA_NOT_READY_COUNT']}

Top tier candidate count: {values['TOP_TIER_CANDIDATE_COUNT']}.

These are read-only tier candidates, not buy recommendations. Official ranking changes, factor effect claims, weight changes, production promotion, daily command center integration, backtests, auto-trade, and auto-sell remain blocked.

TRUE_5DAY_UNIQUE_COVERAGE_MET remains {values['TRUE_5DAY_UNIQUE_COVERAGE_MET']} because ledger coverage is still partial after V18.23C-R3: {values['TRUE_5DAY_UNIQUE_COVERAGE_STATUS']}.

This snapshot is snapshot-only and does not execute scan, fetch, backtest, broker, or trading logic.
"""


def render_restore_script(manifest_name: str) -> str:
    return f"""param([string]$Root = "D:\\us-tech-quant")
$ErrorActionPreference = "Stop"
$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Manifest = Join-Path $SnapshotRoot "{manifest_name}"
if (-not (Test-Path -LiteralPath $Manifest)) {{ throw "Missing manifest: $Manifest" }}
Write-Host "=== RESTORE V18.24B SNAPSHOT START ==="
Import-Csv -LiteralPath $Manifest | Where-Object {{ $_.status -eq "COPIED" }} | ForEach-Object {{
    $src = Join-Path $SnapshotRoot $_.relative_snapshot_path
    $dest = Join-Path $Root $_.relative_source_path
    $parent = Split-Path -Parent $dest
    if (-not (Test-Path -LiteralPath $parent)) {{ New-Item -ItemType Directory -Path $parent | Out-Null }}
    Copy-Item -LiteralPath $src -Destination $dest -Force
}}
Write-Host "=== RESTORE V18.24B SNAPSHOT END ==="
exit 0
"""


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.24B Stable Snapshot Report

Status: {values['STATUS']}

Snapshot path: {values['SNAPSHOT_PATH']}

Copied files: {values['COPIED_FILE_COUNT']}. Missing critical: {values['MISSING_CRITICAL_COUNT']}. Copy failures: {values['COPY_FAIL_COUNT']}. Validation failures: {values['VALIDATION_FAIL_COUNT']}.

This snapshot is snapshot-only. It did not execute scan/fetch/backtest/trading logic and did not modify ranking, factor pack, technical timing, signal snapshot, price cache, ledger, official decision, buy permission, broker/manual execution, or trading state.

Recommended next action: {values['RECOMMENDED_NEXT_ACTION']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot = root / "archive/stable" / f"{PREFIX}_{timestamp}"
    ensure_dir(snapshot)

    v24a = read_kv(root / "outputs/v18/ops/V18_24A_READ_FIRST.txt")
    v24b = read_kv(root / "outputs/v18/ops/V18_24B_READ_FIRST.txt")
    py_result, py_notes = py_compile(root / "scripts/v18/v18_24B_stable_snapshot.py")
    ps_result, ps_notes = ps_parse(root / "scripts/v18/run_v18_24B_stable_snapshot.ps1")

    files_to_copy = list(dict.fromkeys(CRITICAL_FILES + latest_history_files(root) + OPTIONAL_CONTEXT))
    manifest_rows = [copy_file(root, snapshot, rel, "critical" if rel in CRITICAL_FILES else "context") for rel in files_to_copy]

    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_24B_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_24B.ps1"
    write_csv(manifest_path, manifest_rows, MANIFEST_FIELDS)

    missing_critical = sum(1 for row in manifest_rows if row["category"] == "critical" and row["status"] == "MISSING")
    copy_fail = sum(1 for row in manifest_rows if row["status"] == "COPY_FAIL")
    copied = sum(1 for row in manifest_rows if row["status"] == "COPIED")

    values: Dict[str, str] = {
        "STATUS": STATUS_OK,
        "MODE": MODE,
        "SNAPSHOT_PATH": str(snapshot),
        "SNAPSHOT_MODIFIED": "TRUE",
        "COPIED_FILE_COUNT": str(copied),
        "MISSING_CRITICAL_COUNT": str(missing_critical),
        "COPY_FAIL_COUNT": str(copy_fail),
        "VALIDATION_FAIL_COUNT": "0",
        "PYTHON_COMPILE_RESULT": py_result,
        "POWERSHELL_PARSE_RESULT": ps_result,
        "TIER_MIGRATION_AUDIT_READY": v24a.get("TIER_MIGRATION_AUDIT_READY", ""),
        "TIER_MIGRATION_OPERATOR_HOMEPAGE_READY": v24b.get("TIER_MIGRATION_OPERATOR_HOMEPAGE_READY", ""),
        "V18_24A_BASELINE_MODE": v24b.get("V18_24A_BASELINE_MODE", v24a.get("BASELINE_MODE", "")),
        "CURRENT_TICKER_COUNT": v24b.get("CURRENT_TICKER_COUNT", v24a.get("CURRENT_TICKER_COUNT", "")),
        "CURRENT_SCORE_SOURCE": v24b.get("CURRENT_SCORE_SOURCE", v24a.get("CURRENT_SCORE_SOURCE", "")),
        "CURRENT_SCORE_SOURCE_TRUST": v24b.get("CURRENT_SCORE_SOURCE_TRUST", v24a.get("CURRENT_SCORE_SOURCE_TRUST", "")),
        "TIER_1_CORE_CANDIDATE_COUNT": v24b.get("TIER_1_CORE_CANDIDATE_COUNT", ""),
        "TIER_2_STRONG_WATCHLIST_COUNT": v24b.get("TIER_2_STRONG_WATCHLIST_COUNT", ""),
        "TIER_3_WATCHLIST_COUNT": v24b.get("TIER_3_WATCHLIST_COUNT", ""),
        "TIER_4_REVIEW_ONLY_COUNT": v24b.get("TIER_4_REVIEW_ONLY_COUNT", ""),
        "TIER_5_WEAK_OR_BLOCKED_COUNT": v24b.get("TIER_5_WEAK_OR_BLOCKED_COUNT", ""),
        "TIER_0_DATA_NOT_READY_COUNT": v24b.get("TIER_0_DATA_NOT_READY_COUNT", ""),
        "MOVEMENT_REPORT_AVAILABLE": v24b.get("MOVEMENT_REPORT_AVAILABLE", ""),
        "TOTAL_MOVEMENT_COUNT": v24b.get("TOTAL_MOVEMENT_COUNT", ""),
        "UPGRADE_COUNT": v24b.get("UPGRADE_COUNT", ""),
        "DOWNGRADE_COUNT": v24b.get("DOWNGRADE_COUNT", ""),
        "LARGE_SCORE_MOVE_COUNT": v24b.get("LARGE_SCORE_MOVE_COUNT", ""),
        "NEWLY_SCORE_READY_COUNT": v24b.get("NEWLY_SCORE_READY_COUNT", ""),
        "DATA_NOT_READY_OR_BLOCKED_COUNT": v24b.get("DATA_NOT_READY_OR_BLOCKED_COUNT", ""),
        "TOP_TIER_CANDIDATE_COUNT": v24b.get("TOP_TIER_CANDIDATE_COUNT", ""),
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": v24b.get("TRUE_5DAY_UNIQUE_COVERAGE_MET", "FALSE"),
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": v24b.get("TRUE_5DAY_UNIQUE_COVERAGE_STATUS", ""),
        "RECOMMENDED_NEXT_ACTION": "Use the V18.24B stable homepage as the daily baseline; rerun V18.24A/V18.24B after future score or readiness changes to show real movement against this snapshot.",
        "MANIFEST_PATH": str(manifest_path),
        "VALIDATION_PATH": str(validation_path),
        "README_PATH": str(readme_path),
        "RESTORE_SCRIPT_PATH": str(restore_path),
        "REPORT_PATH": str(root / GENERATED_OUTPUTS["report"]),
    }
    values.update(SAFETY)

    write_text(readme_path, render_readme(values))
    write_text(restore_path, render_restore_script("MANIFEST.csv"))

    validations = [
        validation_row("python_compile_check", py_result == "PASS", 1, py_notes),
        validation_row("powershell_parse_check", ps_result == "PASS", 1, ps_notes),
        validation_row("snapshot_folder_created", snapshot.exists(), 1, str(snapshot)),
        validation_row("critical_files_copied", missing_critical == 0, missing_critical, "All V18.24A/B critical files must be copied."),
        validation_row("copy_fail_count_zero", copy_fail == 0, copy_fail, "No copy failures allowed."),
        validation_row("manifest_non_empty", non_empty(manifest_path), 1, str(manifest_path)),
        validation_row("readme_non_empty", non_empty(readme_path), 1, str(readme_path)),
        validation_row("restore_script_non_empty", non_empty(restore_path), 1, str(restore_path)),
        validation_row("v18_24a_outputs_present", all((snapshot / rel).exists() for rel in CRITICAL_FILES if "V18_24A" in rel), 1, "Critical V18.24A outputs/scripts must be present."),
        validation_row("v18_24b_outputs_present", all((snapshot / rel).exists() for rel in CRITICAL_FILES if "V18_24B" in rel), 1, "Critical V18.24B outputs/scripts must be present."),
    ]
    for key, expected in SAFETY.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    write_csv(validation_path, validations, VALIDATION_FIELDS)
    write_text(root / GENERATED_OUTPUTS["read_first"], render_read_first(values))
    write_text(root / GENERATED_OUTPUTS["report"], render_report(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
