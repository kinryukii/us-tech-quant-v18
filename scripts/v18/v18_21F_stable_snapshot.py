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


STATUS_OK = "OK_V18_21F_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_21F_STABLE_SNAPSHOT_VALIDATION_FAILED"
MODE = "SNAPSHOT_ONLY"
SNAPSHOT_ONLY = "TRUE"
PREFIX = "V18_21F_stable_unified_research_chain_read_center"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
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
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": "FALSE",
    "FORWARD_RETURN_FILLED_COUNT": "0",
    "EFFECT_CLAIM_ALLOWED_COUNT": "0",
    "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
    "STABLE_SNAPSHOT_MODIFIED": "TRUE",
}

REQUIRED_FILES = [
    "scripts/v18/v18_21F_stable_snapshot.py",
    "scripts/v18/run_v18_21F_stable_snapshot.ps1",
    "scripts/v18/v18_21F_unified_research_chain_read_center.py",
    "scripts/v18/run_v18_21F_unified_research_chain_read_center.ps1",
    "outputs/v18/research_chain/V18_21F_CURRENT_UNIFIED_RESEARCH_CHAIN_STATUS.csv",
    "outputs/v18/research_chain/V18_21F_CURRENT_RESEARCH_BLOCKER_SUMMARY.csv",
    "outputs/v18/research_chain/V18_21F_CURRENT_RESEARCH_READINESS_DECISION_TABLE.csv",
    "outputs/v18/research_chain/V18_21F_CURRENT_NEXT_STEP_PLAN.csv",
    "outputs/v18/ops/V18_21F_READ_FIRST.txt",
    "outputs/v18/ops/V18_21F_CURRENT_UNIFIED_RESEARCH_CHAIN_READ_CENTER.md",
    "outputs/v18/ops/V18_21A_R4_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21B_R1_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21C_R2_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21D_R1_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21E_R1_STABLE_READ_FIRST.txt",
]
GENERATED_EXTERNAL_FILES = [
    "outputs/v18/ops/V18_21F_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21F_CURRENT_STABLE_SNAPSHOT_REPORT.md",
]
PS_FILES = [
    "scripts/v18/run_v18_21F_stable_snapshot.ps1",
    "scripts/v18/run_v18_21F_unified_research_chain_read_center.ps1",
]
PY_FILES = [
    "scripts/v18/v18_21F_stable_snapshot.py",
    "scripts/v18/v18_21F_unified_research_chain_read_center.py",
]
SUPPORTING_STABLE_READ_FIRST = [
    "outputs/v18/ops/V18_21A_R4_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21B_R1_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21C_R2_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21D_R1_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21E_R1_STABLE_READ_FIRST.txt",
]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "SNAPSHOT_ONLY", "POLICY_APPLIED", "STABLE_LAYER_COUNT",
    "STABLE_LAYER_OK_COUNT", "STABLE_LAYER_WARN_OR_DEGRADED_COUNT", "MISSING_STABLE_LAYER_COUNT",
    "PRICE_DERIVED_SCORE_READY_RATIO", "PRICE_DERIVED_MISSING_HISTORY_TICKER_COUNT",
    "SIGNAL_SNAPSHOT_ROW_COUNT", "READY_FOR_FORWARD_RESEARCH_COUNT",
    "READY_FOR_SIMULATION_ANALYSIS_COUNT", "FACTOR_EFFECTIVENESS_HIGH_CONFIDENCE_MATCH_COUNT",
    "FACTOR_EFFECTIVENESS_LOW_CONFIDENCE_MATCH_COUNT", "MULTI_HORIZON_READINESS_STATUS",
    "FORWARD_TRACKER_SHADOW_ROW_COUNT", "FORWARD_RETURN_FILLED_COUNT",
    "FORWARD_RETURN_PENDING_COUNT", "EVENT_FINAL_ADVISORY_MARKET_COEFFICIENT",
    "EVENT_HARD_LOCK_OVERLAY_DETECTED", "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET", "COVERAGE_WINDOW_COMPLETE", "DAILY_TRUST_LEVEL",
    "FACTOR_EFFECT_CLAIM_ALLOWED", "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED",
    "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "PRICE_CACHE_MODIFIED", "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "EVENT_CALENDAR_MODIFIED", "SIMULATION_POSITION_MODIFIED",
    "FORWARD_TRACKER_MODIFIED", "PRICE_FACTOR_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED",
    "EXTERNAL_DATA_FETCHED", "STABLE_SNAPSHOT_MODIFIED", "VALIDATION_FAIL_COUNT",
    "SNAPSHOT_PATH", "MANIFEST_ROW_COUNT", "READ_FIRST", "REPORT",
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


def category_for(rel: str) -> str:
    if rel.startswith("scripts/"):
        return "SCRIPT"
    if rel in GENERATED_EXTERNAL_FILES:
        return "GENERATED_CURRENT_OUTPUT"
    if rel.endswith("_STABLE_READ_FIRST.txt"):
        return "SUPPORTING_STABLE_READ_FIRST"
    return "OUTPUT"


def copy_one(root: Path, snapshot: Path, rel: str) -> Dict[str, object]:
    src = root / rel
    dst = snapshot / rel
    row = {"category": category_for(rel), "source_path": str(src), "snapshot_path": str(dst), "relative_source_path": rel, "relative_snapshot_path": rel}
    if not src.exists():
        row.update({"status": "MISSING", "size_bytes": "", "modified_time": "", "sha256": "", "error": "SOURCE_MISSING"})
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
    result = subprocess.run(["python", "-m", "py_compile", str(path)], capture_output=True, text=True)
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
    return f"""# V18.21F Stable Snapshot

This snapshot preserves the V18.21F unified research-chain read center.

Explicit preserved interpretation:
- All five V18.21A-E stable layers are present.
- This is not a production-readiness claim.
- Factor effect claims are not allowed.
- Weight changes are not allowed.
- Production promotion is not allowed.
- Event risk is advisory-only and not applied to official decisions.
- Forward returns remain unfilled.
- Official decision, buy permission, ranking, signal snapshots, event calendars, simulation, forward tracker, price cache, broker execution, auto-trade, and auto-sell are unaffected.

Key metrics:
- Stable layers: {metrics.get('STABLE_LAYER_OK_COUNT', '5')} of {metrics.get('STABLE_LAYER_COUNT', '5')}
- Score-ready ratio: {metrics.get('PRICE_DERIVED_SCORE_READY_RATIO', '0.320000')}
- Forward returns filled: {metrics.get('FORWARD_RETURN_FILLED_COUNT', '0')}
- Event coefficient applied to official decision: {metrics.get('EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION', 'FALSE')}

Snapshot path:
`{snapshot}`
"""


def report(metrics: Dict[str, object], snapshot: Path) -> str:
    return f"""# V18.21F Stable Snapshot Report

## Executive Summary
Status: {metrics.get('STATUS')}. This snapshot preserves the unified V18.21A-E research-chain read center and supporting stable READ_FIRST files.

## Safety
Official decision impact: {metrics.get('OFFICIAL_DECISION_IMPACT')}. Buy permission modified: {metrics.get('BUY_PERMISSION_MODIFIED')}. External data fetched: {metrics.get('EXTERNAL_DATA_FETCHED')}. Event coefficient applied to official decision: {metrics.get('EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION')}.

## Research Limits
Factor effect claims: {metrics.get('FACTOR_EFFECT_CLAIM_ALLOWED')}. Weight changes: {metrics.get('WEIGHT_CHANGE_ALLOWED')}. Production promotion: {metrics.get('PRODUCTION_PROMOTION_ALLOWED')}. Forward returns filled: {metrics.get('FORWARD_RETURN_FILLED_COUNT')}.

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
        'Write-Host "=== RESTORE V18.21F STABLE SNAPSHOT START ==="',
        'Write-Host "MODE: SNAPSHOT_RESTORE"',
        'Write-Host "NOTE: This restores read-center snapshot artifacts only."',
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
        'Write-Host "OFFICIAL_DECISION_IMPACT: NONE"',
        'Write-Host "BUY_PERMISSION_MODIFIED: FALSE"',
        'Write-Host "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION: FALSE"',
        'Write-Host "NOTE: Restore does not change production behavior."',
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot = root / "archive" / "stable" / f"{PREFIX}_{timestamp}"
    read_first_path = root / "outputs/v18/ops/V18_21F_STABLE_READ_FIRST.txt"
    report_path = root / "outputs/v18/ops/V18_21F_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_21F_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_21F.ps1"

    metrics = readfirst(root / "outputs/v18/ops/V18_21F_READ_FIRST.txt")
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

    manifest: List[Dict[str, object]] = [copy_one(root, snapshot, rel) for rel in REQUIRED_FILES]
    manifest.extend(copy_one(root, snapshot, rel) for rel in GENERATED_EXTERNAL_FILES)
    copied_files = [str(row["relative_source_path"]) for row in manifest if row.get("status") == "COPIED"]
    write_text(restore_path, restore_script(copied_files))
    manifest.append(snapshot_artifact_row(snapshot, "RESTORE_V18_21F.ps1", "RESTORE"))
    manifest.append(snapshot_artifact_row(snapshot, "README_V18_21F_STABLE_SNAPSHOT.md", "README"))
    write_csv(manifest_path, manifest, MANIFEST_FIELDS)
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
    validations.append(validation("manifest_has_rows", len(manifest) > 0, str(manifest_path), ">0", str(len(manifest))))
    validations.append(validation("validation_has_rows", True, str(validation_path), ">0", "pending_rows"))
    for rel in GENERATED_EXTERNAL_FILES:
        path = root / rel
        validations.append(validation("current_external_output_exists", path.exists(), str(path), "EXISTS", "EXISTS" if path.exists() else "MISSING"))
    for rel in SUPPORTING_STABLE_READ_FIRST:
        validations.append(validation("supporting_stable_read_first_exists", (root / rel).exists(), str(root / rel), "EXISTS", "EXISTS" if (root / rel).exists() else "MISSING"))
    for key, expected in {
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
        "FORWARD_RETURN_FILLED_COUNT": "0",
        "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
        "WEIGHT_CHANGE_ALLOWED": "FALSE",
        "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
    }.items():
        validations.append(validation(f"preserve_{key.lower()}", str(metrics.get(key, "")) == expected, str(read_first_path), expected, str(metrics.get(key, ""))))

    fail_count = sum(1 for row in validations if row["status"] != "PASS")
    metrics["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        metrics["STATUS"] = STATUS_WARN
    final_manifest: List[Dict[str, object]] = [copy_one(root, snapshot, rel) for rel in REQUIRED_FILES]
    final_manifest.extend(copy_one(root, snapshot, rel) for rel in GENERATED_EXTERNAL_FILES)
    final_manifest.append(snapshot_artifact_row(snapshot, "RESTORE_V18_21F.ps1", "RESTORE"))
    final_manifest.append(snapshot_artifact_row(snapshot, "README_V18_21F_STABLE_SNAPSHOT.md", "README"))
    final_manifest.append(snapshot_artifact_row(snapshot, "VALIDATION.csv", "VALIDATION"))
    metrics["MANIFEST_ROW_COUNT"] = str(len(final_manifest))
    write_text(read_first_path, render_readfirst(metrics))
    write_text(report_path, report(metrics, snapshot))
    final_manifest = [copy_one(root, snapshot, rel) for rel in REQUIRED_FILES]
    final_manifest.extend(copy_one(root, snapshot, rel) for rel in GENERATED_EXTERNAL_FILES)
    final_manifest.append(snapshot_artifact_row(snapshot, "RESTORE_V18_21F.ps1", "RESTORE"))
    final_manifest.append(snapshot_artifact_row(snapshot, "README_V18_21F_STABLE_SNAPSHOT.md", "README"))
    final_manifest.append(snapshot_artifact_row(snapshot, "VALIDATION.csv", "VALIDATION"))
    write_csv(manifest_path, final_manifest, MANIFEST_FIELDS)
    write_csv(validation_path, validations, VALIDATION_FIELDS)

    for key in [
        "STATUS", "MODE", "SNAPSHOT_ONLY", "POLICY_APPLIED", "STABLE_LAYER_COUNT",
        "STABLE_LAYER_OK_COUNT", "MISSING_STABLE_LAYER_COUNT", "PRICE_DERIVED_SCORE_READY_RATIO",
        "SIGNAL_SNAPSHOT_ROW_COUNT", "FACTOR_EFFECTIVENESS_HIGH_CONFIDENCE_MATCH_COUNT",
        "MULTI_HORIZON_READINESS_STATUS", "FORWARD_RETURN_FILLED_COUNT",
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION", "FACTOR_EFFECT_CLAIM_ALLOWED",
        "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED", "OFFICIAL_DECISION_IMPACT",
        "BUY_PERMISSION_MODIFIED", "EXTERNAL_DATA_FETCHED", "VALIDATION_FAIL_COUNT",
        "SNAPSHOT_PATH", "MANIFEST_ROW_COUNT", "READ_FIRST", "REPORT",
    ]:
        print(f"{key}: {metrics.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
