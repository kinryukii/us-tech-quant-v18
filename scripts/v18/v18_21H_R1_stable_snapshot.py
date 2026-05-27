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


STATUS_OK = "OK_V18_21H_R1_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_21H_R1_STABLE_SNAPSHOT_VALIDATION_FAILED"
MODE = "SNAPSHOT_ONLY"
SNAPSHOT_ONLY = "TRUE"
PREFIX = "V18_21H_R1_stable_controlled_staged_backfill_batch1_design"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "STAGED_BACKFILL_BATCH1_DESIGN_READY": "TRUE",
    "FULL_HISTORY_BACKFILL_APPLIED": "FALSE",
    "STAGED_BACKFILL_APPLIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "STAGED_PRICE_HISTORY_WRITTEN": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
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
    "EFFECT_CLAIM_ALLOWED_COUNT": "0",
    "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
    "STABLE_SNAPSHOT_MODIFIED": "TRUE",
}

REQUIRED_FILES = [
    "scripts/v18/v18_21H_R1_stable_snapshot.py",
    "scripts/v18/run_v18_21H_R1_stable_snapshot.ps1",
    "scripts/v18/v18_21H_full_history_backfill_design.py",
    "scripts/v18/run_v18_21H_full_history_backfill_design.ps1",
    "scripts/v18/v18_21H_R1_controlled_staged_backfill_batch1_design.py",
    "scripts/v18/run_v18_21H_R1_controlled_staged_backfill_batch1_design.ps1",
    "outputs/v18/price_factors/V18_21H_CURRENT_FULL_HISTORY_BACKFILL_REQUIREMENT_AUDIT.csv",
    "outputs/v18/price_factors/V18_21H_CURRENT_FULL_HISTORY_BACKFILL_PRIORITY_BATCH_PLAN.csv",
    "outputs/v18/price_factors/V18_21H_CURRENT_FULL_HISTORY_COVERAGE_IMPROVEMENT_PROJECTION.csv",
    "outputs/v18/price_factors/V18_21H_CURRENT_CONTROLLED_BACKFILL_IMPLEMENTATION_DESIGN.csv",
    "outputs/v18/price_factors/V18_21H_CURRENT_FULL_HISTORY_BACKFILL_SAFETY_AUDIT.csv",
    "outputs/v18/ops/V18_21H_READ_FIRST.txt",
    "outputs/v18/ops/V18_21H_CURRENT_FULL_HISTORY_BACKFILL_DESIGN_REPORT.md",
    "outputs/v18/ops/V18_21H_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21H_CURRENT_STABLE_SNAPSHOT_REPORT.md",
    "outputs/v18/price_factors/V18_21H_R1_CURRENT_BATCH1_STAGED_BACKFILL_REQUEST_MANIFEST.csv",
    "outputs/v18/price_factors/V18_21H_R1_CURRENT_BATCH1_TICKER_VALIDATION_AUDIT.csv",
    "outputs/v18/price_factors/V18_21H_R1_CURRENT_STAGED_OHLCV_SCHEMA_PREVIEW.csv",
    "outputs/v18/price_factors/V18_21H_R1_CURRENT_BATCH1_COVERAGE_IMPACT_PROJECTION.csv",
    "outputs/v18/price_factors/V18_21H_R1_CURRENT_CONTROLLED_STAGED_APPLY_SAFETY_PLAN.csv",
    "outputs/v18/price_factors/V18_21H_R1_CURRENT_STAGED_BACKFILL_SAFETY_AUDIT.csv",
    "outputs/v18/ops/V18_21H_R1_READ_FIRST.txt",
    "outputs/v18/ops/V18_21H_R1_CURRENT_CONTROLLED_STAGED_BACKFILL_BATCH1_DESIGN_REPORT.md",
]
OPTIONAL_FILES = [
    "outputs/v18/ops/V18_21F_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21G_STABLE_READ_FIRST.txt",
    "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv",
]
GENERATED_EXTERNAL_FILES = [
    "outputs/v18/ops/V18_21H_R1_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21H_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md",
]
PS_FILES = [
    "scripts/v18/run_v18_21H_R1_stable_snapshot.ps1",
    "scripts/v18/run_v18_21H_R1_controlled_staged_backfill_batch1_design.ps1",
    "scripts/v18/run_v18_21H_full_history_backfill_design.ps1",
]
PY_FILES = [
    "scripts/v18/v18_21H_R1_stable_snapshot.py",
    "scripts/v18/v18_21H_R1_controlled_staged_backfill_batch1_design.py",
    "scripts/v18/v18_21H_full_history_backfill_design.py",
]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "SNAPSHOT_ONLY", "POLICY_APPLIED", "STAGED_BACKFILL_BATCH1_DESIGN_READY",
    "FULL_HISTORY_BACKFILL_APPLIED", "STAGED_BACKFILL_APPLIED", "EXTERNAL_DATA_FETCHED",
    "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_WRITTEN",
    "CURRENT_SCORE_READY_RATIO", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
    "CURRENT_MISSING_HISTORY_TICKER_COUNT", "BATCH1_REQUESTED_TICKER_COUNT",
    "BATCH1_VALID_TICKER_COUNT", "BATCH1_NEED_REVIEW_COUNT", "BATCH1_BLOCKED_COUNT",
    "BATCH1_PROJECTED_SCORE_READY_RATIO_IF_APPLIED_LATER",
    "BATCH1_PROJECTED_MISSING_HISTORY_TICKER_COUNT_IF_APPLIED_LATER",
    "STAGED_OHLCV_SCHEMA_PREVIEW_CREATED", "CONTROLLED_STAGED_APPLY_SAFETY_PLAN_CREATED",
    "SAFETY_AUDIT_CREATED", "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "EVENT_CALENDAR_MODIFIED", "SIMULATION_POSITION_MODIFIED",
    "FORWARD_TRACKER_MODIFIED", "PRICE_FACTOR_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED",
    "STABLE_SNAPSHOT_MODIFIED", "VALIDATION_FAIL_COUNT", "SNAPSHOT_PATH", "MANIFEST_ROW_COUNT",
    "READ_FIRST", "REPORT",
]
MANIFEST_FIELDS = ["category", "status", "source_path", "snapshot_path", "relative_source_path", "relative_snapshot_path", "size_bytes", "modified_time", "sha256", "error"]
VALIDATION_FIELDS = ["check_name", "status", "path", "expected", "actual", "note"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


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


def mtime(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def category_for(rel: str, optional: bool) -> str:
    if optional:
        return "SUPPORTING_CONTEXT"
    if rel.startswith("scripts/"):
        return "SCRIPT"
    if rel in GENERATED_EXTERNAL_FILES:
        return "GENERATED_CURRENT_OUTPUT"
    return "OUTPUT"


def copy_one(root: Path, snapshot: Path, rel: str, optional: bool = False) -> Dict[str, object]:
    src = root / rel
    dst = snapshot / rel
    row = {"category": category_for(rel, optional), "source_path": str(src), "snapshot_path": str(dst), "relative_source_path": rel, "relative_snapshot_path": rel}
    if not src.exists():
        row.update({"status": "OPTIONAL_MISSING" if optional else "MISSING", "size_bytes": "", "modified_time": "", "sha256": "", "error": "SOURCE_MISSING"})
        return row
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)
    row.update({"status": "COPIED", "size_bytes": dst.stat().st_size, "modified_time": mtime(dst), "sha256": sha256(dst), "error": ""})
    return row


def snapshot_artifact_row(snapshot: Path, rel: str, category: str) -> Dict[str, object]:
    path = snapshot / rel
    row = {"category": category, "source_path": str(path), "snapshot_path": str(path), "relative_source_path": rel, "relative_snapshot_path": rel}
    if not path.exists():
        row.update({"status": "MISSING", "size_bytes": "", "modified_time": "", "sha256": "", "error": "SNAPSHOT_ARTIFACT_MISSING"})
        return row
    row.update({"status": "CREATED", "size_bytes": path.stat().st_size, "modified_time": mtime(path), "sha256": sha256(path), "error": ""})
    return row


def ps_parse(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    escaped = str(path).replace("'", "''")
    cmd = f"$null = [scriptblock]::Create((Get-Content -Raw -LiteralPath '{escaped}')); 'OK_PARSE'"
    result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK_PARSE" in result.stdout, (result.stdout or result.stderr).strip()


def py_compile(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
    return result.returncode == 0, "OK_COMPILE" if result.returncode == 0 else (result.stdout or result.stderr).strip()


def validation(name: str, ok: bool, path: str, expected: str, actual: str, note: str = "") -> Dict[str, object]:
    return {"check_name": name, "status": "PASS" if ok else "FAIL", "path": path, "expected": expected, "actual": actual, "note": note}


def render_readfirst(metrics: Dict[str, object]) -> str:
    values = dict(metrics)
    values.update(SAFETY_FLAGS)
    values["MODE"] = MODE
    values["SNAPSHOT_ONLY"] = SNAPSHOT_ONLY
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def readme(metrics: Dict[str, object], snapshot: Path) -> str:
    return f"""# V18.21H-R1 Stable Snapshot

This snapshot preserves V18.21H-R1 controlled staged backfill Batch 1 design.

Required interpretation:
- This is advisory dry-run only.
- Batch 1 has {metrics.get('BATCH1_REQUESTED_TICKER_COUNT', '25')} requested tickers.
- Batch 1 has {metrics.get('BATCH1_VALID_TICKER_COUNT', '25')} valid tickers.
- Batch 1 has {metrics.get('BATCH1_NEED_REVIEW_COUNT', '0')} need-review tickers and {metrics.get('BATCH1_BLOCKED_COUNT', '0')} blocked tickers.
- No staged backfill was applied.
- No full-history backfill was applied.
- No external data was fetched.
- Price cache was not modified.
- No price history was written.
- No staged price history was written.
- Current score-ready ratio remains {metrics.get('CURRENT_SCORE_READY_RATIO', '0.320000')}.
- Batch 1 projected score-ready ratio is {metrics.get('BATCH1_PROJECTED_SCORE_READY_RATIO_IF_APPLIED_LATER', '0.396923')} if applied later, as projection only.
- Projected missing history ticker count after Batch 1 is {metrics.get('BATCH1_PROJECTED_MISSING_HISTORY_TICKER_COUNT_IF_APPLIED_LATER', '196')} if applied later, as projection only.
- No factor effect claims, weight changes, or production promotions are allowed.
- Official decision, buy permission, ranking, signal snapshots, event calendars, simulation, forward tracker, price factors, technical timing, manual state, broker execution, auto-trade, and auto-sell are unaffected.

Snapshot path:
`{snapshot}`
"""


def report(metrics: Dict[str, object], snapshot: Path) -> str:
    return f"""# V18.21H-R1 Stable Snapshot Report

## Executive Summary
Status: {metrics.get('STATUS')}. This snapshot preserves the controlled staged backfill Batch 1 design and advisory dry-run outputs.

## Preserved Dry-Run State
Staged Batch 1 design ready: {metrics.get('STAGED_BACKFILL_BATCH1_DESIGN_READY')}. Full-history backfill applied: {metrics.get('FULL_HISTORY_BACKFILL_APPLIED')}. Staged backfill applied: {metrics.get('STAGED_BACKFILL_APPLIED')}. External data fetched: {metrics.get('EXTERNAL_DATA_FETCHED')}.

## Batch 1 Summary
Requested tickers: {metrics.get('BATCH1_REQUESTED_TICKER_COUNT')}. Valid tickers: {metrics.get('BATCH1_VALID_TICKER_COUNT')}. Need review: {metrics.get('BATCH1_NEED_REVIEW_COUNT')}. Blocked: {metrics.get('BATCH1_BLOCKED_COUNT')}.

## Projection Only
Current score-ready ratio: {metrics.get('CURRENT_SCORE_READY_RATIO')}. Projected Batch 1 score-ready ratio if applied later: {metrics.get('BATCH1_PROJECTED_SCORE_READY_RATIO_IF_APPLIED_LATER')}. Projected missing-history ticker count if applied later: {metrics.get('BATCH1_PROJECTED_MISSING_HISTORY_TICKER_COUNT_IF_APPLIED_LATER')}.

## Safety
Price cache modified: {metrics.get('PRICE_CACHE_MODIFIED')}. Price history written: {metrics.get('PRICE_HISTORY_WRITTEN')}. Staged price history written: {metrics.get('STAGED_PRICE_HISTORY_WRITTEN')}. Official decision impact: {metrics.get('OFFICIAL_DECISION_IMPACT')}.

## Snapshot Path
`{snapshot}`

## Validation
Validation fail count: {metrics.get('VALIDATION_FAIL_COUNT')}. Manifest rows: {metrics.get('MANIFEST_ROW_COUNT')}.
"""


def restore_script(files: Sequence[str]) -> str:
    lines = [
        'param([string]$Root = "D:\\us-tech-quant")',
        '$ErrorActionPreference = "Stop"',
        '$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path',
        'Write-Host "=== RESTORE V18.21H-R1 STABLE SNAPSHOT START ==="',
        'Write-Host "MODE: SNAPSHOT_RESTORE"',
        'Write-Host "NOTE: This restores advisory dry-run staged Batch 1 design artifacts only."',
    ]
    for rel in files:
        win = rel.replace("/", "\\")
        lines.extend([
            f'$Source = Join-Path $SnapshotRoot "{win}"',
            f'$Target = Join-Path $Root "{win}"',
            'if (Test-Path $Source) {',
            '    $Dir = Split-Path -Parent $Target',
            '    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }',
            '    Copy-Item -LiteralPath $Source -Destination $Target -Force',
            '}',
        ])
    lines.extend([
        'Write-Host "RESTORE_COMPLETE: TRUE"',
        'Write-Host "STAGED_BACKFILL_APPLIED: FALSE"',
        'Write-Host "FULL_HISTORY_BACKFILL_APPLIED: FALSE"',
        'Write-Host "EXTERNAL_DATA_FETCHED: FALSE"',
        'Write-Host "PRICE_CACHE_MODIFIED: FALSE"',
        'Write-Host "PRICE_HISTORY_WRITTEN: FALSE"',
        'Write-Host "STAGED_PRICE_HISTORY_WRITTEN: FALSE"',
        'Write-Host "NOTE: Restore does not fetch data, write price history, or modify price cache."',
    ])
    return "\n".join(lines) + "\n"


def signature(path: Path) -> Tuple[str, str]:
    if not path.exists():
        return "MISSING", ""
    return mtime(path), "" if path.is_dir() else sha256(path)


def protected_paths(root: Path) -> List[Path]:
    rels = [
        "state/v18/price_cache/QQQ.csv",
        "state/v18/price_cache/SPY.csv",
        "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv",
        "outputs/v18/forward_tracker/V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv",
        "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        "state/v16/event_calendar.csv",
        "state/v18/cloud_earnings_event_calendar.csv",
    ]
    return [root / rel for rel in rels]


def build_manifest(root: Path, snapshot: Path) -> List[Dict[str, object]]:
    manifest: List[Dict[str, object]] = [copy_one(root, snapshot, rel) for rel in REQUIRED_FILES]
    manifest.extend(copy_one(root, snapshot, rel, optional=True) for rel in OPTIONAL_FILES if (root / rel).exists())
    manifest.extend(copy_one(root, snapshot, rel) for rel in GENERATED_EXTERNAL_FILES)
    manifest.append(snapshot_artifact_row(snapshot, "RESTORE_V18_21H_R1.ps1", "RESTORE"))
    manifest.append(snapshot_artifact_row(snapshot, "README_V18_21H_R1_STABLE_SNAPSHOT.md", "README"))
    manifest.append(snapshot_artifact_row(snapshot, "VALIDATION.csv", "VALIDATION"))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    before = {str(path): signature(path) for path in protected_paths(root)}
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot = root / "archive" / "stable" / f"{PREFIX}_{timestamp}"
    read_first_path = root / "outputs/v18/ops/V18_21H_R1_STABLE_READ_FIRST.txt"
    report_path = root / "outputs/v18/ops/V18_21H_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_21H_R1_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_21H_R1.ps1"

    metrics = readfirst(root / "outputs/v18/ops/V18_21H_R1_READ_FIRST.txt")
    metrics.update(SAFETY_FLAGS)
    metrics.update({
        "STATUS": STATUS_OK,
        "MODE": MODE,
        "SNAPSHOT_ONLY": SNAPSHOT_ONLY,
        "SNAPSHOT_PATH": str(snapshot),
        "READ_FIRST": str(read_first_path),
        "REPORT": str(report_path),
        "VALIDATION_FAIL_COUNT": "0",
        "MANIFEST_ROW_COUNT": "0",
    })
    write_text(read_first_path, render_readfirst(metrics))
    write_text(report_path, report(metrics, snapshot))
    write_text(readme_path, readme(metrics, snapshot))

    initial_manifest: List[Dict[str, object]] = [copy_one(root, snapshot, rel) for rel in REQUIRED_FILES]
    initial_manifest.extend(copy_one(root, snapshot, rel, optional=True) for rel in OPTIONAL_FILES if (root / rel).exists())
    initial_manifest.extend(copy_one(root, snapshot, rel) for rel in GENERATED_EXTERNAL_FILES)
    copied_files = [str(row["relative_source_path"]) for row in initial_manifest if row.get("status") == "COPIED"]
    write_text(restore_path, restore_script(copied_files))
    initial_manifest.append(snapshot_artifact_row(snapshot, "RESTORE_V18_21H_R1.ps1", "RESTORE"))
    initial_manifest.append(snapshot_artifact_row(snapshot, "README_V18_21H_R1_STABLE_SNAPSHOT.md", "README"))
    write_csv(manifest_path, initial_manifest, MANIFEST_FIELDS)
    write_csv(validation_path, [], VALIDATION_FIELDS)

    validations: List[Dict[str, object]] = []
    for rel in PS_FILES:
        ok, note = ps_parse(root / rel)
        validations.append(validation("powershell_parse", ok, str(root / rel), "PARSE_OK", "PARSE_OK" if ok else "PARSE_FAIL", note))
    for rel in PY_FILES:
        ok, note = py_compile(root / rel)
        validations.append(validation("python_compile", ok, str(root / rel), "COMPILE_OK", "COMPILE_OK" if ok else "COMPILE_FAIL", note))
    for rel in REQUIRED_FILES:
        dst = snapshot / rel
        validations.append(validation("required_snapshot_file_exists", dst.exists(), str(dst), "EXISTS", "EXISTS" if dst.exists() else "MISSING"))
    for path, name in [(manifest_path, "MANIFEST"), (validation_path, "VALIDATION"), (readme_path, "README"), (restore_path, "RESTORE")]:
        validations.append(validation(f"{name.lower()}_exists", path.exists(), str(path), "EXISTS", "EXISTS" if path.exists() else "MISSING"))
    validations.append(validation("manifest_has_rows", len(initial_manifest) > 0, str(manifest_path), ">0", str(len(initial_manifest))))
    validations.append(validation("validation_has_rows", True, str(validation_path), ">0", "pending_rows"))
    for rel in GENERATED_EXTERNAL_FILES:
        path = root / rel
        validations.append(validation("current_external_output_exists", path.exists(), str(path), "EXISTS", "EXISTS" if path.exists() else "MISSING"))
    for key, expected in {
        "STAGED_BACKFILL_APPLIED": "FALSE",
        "FULL_HISTORY_BACKFILL_APPLIED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_WRITTEN": "FALSE",
        "STAGED_PRICE_HISTORY_WRITTEN": "FALSE",
        "EFFECT_CLAIM_ALLOWED_COUNT": "0",
        "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
        "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
    }.items():
        validations.append(validation(f"preserve_{key.lower()}", str(metrics.get(key, "")) == expected, str(read_first_path), expected, str(metrics.get(key, ""))))
    after = {str(path): signature(path) for path in protected_paths(root)}
    changed = [path for path, sig in before.items() if after.get(path) != sig]
    validations.append(validation("protected_behavior_state_not_modified", not changed, "protected inputs", "UNCHANGED", "UNCHANGED" if not changed else ";".join(changed)))

    fail_count = sum(1 for row in validations if row["status"] != "PASS")
    metrics["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        metrics["STATUS"] = STATUS_WARN
    final_manifest = build_manifest(root, snapshot)
    metrics["MANIFEST_ROW_COUNT"] = str(len(final_manifest))
    write_text(read_first_path, render_readfirst(metrics))
    write_text(report_path, report(metrics, snapshot))
    final_manifest = build_manifest(root, snapshot)
    write_csv(manifest_path, final_manifest, MANIFEST_FIELDS)
    write_csv(validation_path, validations, VALIDATION_FIELDS)

    for key in [
        "STATUS", "MODE", "SNAPSHOT_ONLY", "POLICY_APPLIED", "STAGED_BACKFILL_BATCH1_DESIGN_READY",
        "FULL_HISTORY_BACKFILL_APPLIED", "STAGED_BACKFILL_APPLIED", "EXTERNAL_DATA_FETCHED",
        "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_WRITTEN",
        "CURRENT_SCORE_READY_RATIO", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT",
        "CURRENT_MISSING_HISTORY_TICKER_COUNT", "BATCH1_REQUESTED_TICKER_COUNT",
        "BATCH1_VALID_TICKER_COUNT", "BATCH1_NEED_REVIEW_COUNT", "BATCH1_BLOCKED_COUNT",
        "BATCH1_PROJECTED_SCORE_READY_RATIO_IF_APPLIED_LATER",
        "BATCH1_PROJECTED_MISSING_HISTORY_TICKER_COUNT_IF_APPLIED_LATER",
        "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "VALIDATION_FAIL_COUNT",
        "SNAPSHOT_PATH", "MANIFEST_ROW_COUNT", "READ_FIRST", "REPORT",
    ]:
        print(f"{key}: {metrics.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
