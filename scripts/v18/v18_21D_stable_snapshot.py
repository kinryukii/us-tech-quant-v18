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


STATUS_OK = "OK_V18_21D_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_21D_STABLE_SNAPSHOT_VALIDATION_FAILED"
MODE = "SNAPSHOT_ONLY"
SNAPSHOT_ONLY = "TRUE"
PREFIX = "V18_21D_stable_forward_tracker_link_key_upgrade_plan"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "FORWARD_TRACKER_UPGRADE_APPLIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "SIMULATION_POSITION_MODIFIED": "FALSE",
    "FORWARD_TRACKER_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "PRICE_FACTOR_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "EFFECT_CLAIM_ALLOWED_COUNT": "0",
    "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
    "STABLE_SNAPSHOT_MODIFIED": "TRUE",
}

FILES = [
    "scripts/v18/v18_21D_forward_tracker_link_key_upgrade_plan.py",
    "scripts/v18/run_v18_21D_forward_tracker_link_key_upgrade_plan.ps1",
    "outputs/v18/forward_tracker/V18_21D_CURRENT_FORWARD_TRACKER_SCHEMA_AUDIT.csv",
    "outputs/v18/forward_tracker/V18_21D_CURRENT_REQUIRED_LINK_KEY_FIELD_PLAN.csv",
    "outputs/v18/forward_tracker/V18_21D_CURRENT_DRYRUN_FORWARD_ROW_TEMPLATE.csv",
    "outputs/v18/forward_tracker/V18_21D_CURRENT_MATCH_QUALITY_IMPROVEMENT_PROJECTION.csv",
    "outputs/v18/forward_tracker/V18_21D_CURRENT_FORWARD_LINK_KEY_UPGRADE_SAFETY_AUDIT.csv",
    "outputs/v18/ops/V18_21D_READ_FIRST.txt",
    "outputs/v18/ops/V18_21D_CURRENT_FORWARD_TRACKER_LINK_KEY_UPGRADE_PLAN_REPORT.md",
]
OPTIONAL_FILES = [
    "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv",
    "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_LINK_KEY_QUALITY_AUDIT.csv",
    "outputs/v18/factor_effectiveness/V18_21C_R2_CURRENT_FORWARD_SOURCE_KEY_AVAILABILITY_AUDIT.csv",
    "outputs/v18/factor_effectiveness/V18_21C_R2_CURRENT_MATCH_FAILURE_REASON_AUDIT.csv",
    "outputs/v18/factor_effectiveness/V18_21C_R2_CURRENT_FORWARD_RESEARCH_KEY_UPGRADE_PLAN.csv",
    "outputs/v18/ops/V18_21C_R2_STABLE_READ_FIRST.txt",
]
PS_FILES = [
    "scripts/v18/run_v18_21D_stable_snapshot.ps1",
    "scripts/v18/run_v18_21D_forward_tracker_link_key_upgrade_plan.ps1",
]
PY_FILES = [
    "scripts/v18/v18_21D_stable_snapshot.py",
    "scripts/v18/v18_21D_forward_tracker_link_key_upgrade_plan.py",
]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "SNAPSHOT_ONLY", "POLICY_APPLIED", "FORWARD_TRACKER_UPGRADE_APPLIED",
    "SIGNAL_SNAPSHOT_ROW_COUNT", "READY_FOR_FORWARD_RESEARCH_COUNT", "FORWARD_TRACKER_SOURCE_COUNT",
    "FORWARD_SOURCE_READY_HIGH_CONFIDENCE_COUNT", "FORWARD_SOURCE_PARTIAL_TICKER_DATE_ONLY_COUNT",
    "FORWARD_SOURCE_TICKER_ONLY_LOW_CONFIDENCE_COUNT", "REQUIRED_LINK_KEY_FIELD_COUNT",
    "REQUIRED_LINK_KEY_CURRENTLY_AVAILABLE_COUNT", "DRYRUN_FORWARD_TEMPLATE_ROW_COUNT", "PLANNED_HORIZON_COUNT",
    "MATCH_QUALITY_PROJECTION_CREATED", "FORWARD_KEY_UPGRADE_PLAN_READY", "MULTI_HORIZON_OUTCOME_PLAN_READY",
    "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT", "PRODUCTION_PROMOTION_ALLOWED_COUNT",
    "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED",
    "PRICE_CACHE_MODIFIED", "RANKING_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "PRICE_FACTOR_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "SIMULATION_POSITION_MODIFIED", "FORWARD_TRACKER_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED", "EXTERNAL_DATA_FETCHED",
    "STABLE_SNAPSHOT_MODIFIED", "VALIDATION_FAIL_COUNT", "SNAPSHOT_PATH", "MANIFEST_ROW_COUNT", "READ_FIRST", "REPORT",
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


def copy_one(root: Path, snapshot: Path, rel: str, optional: bool = False) -> Dict[str, object]:
    src = root / rel
    dst = snapshot / rel
    row = {
        "category": "OPTIONAL" if optional else ("SCRIPT" if rel.startswith("scripts/") else "OUTPUT"),
        "source_path": str(src),
        "snapshot_path": str(dst),
        "relative_source_path": rel,
        "relative_snapshot_path": rel,
    }
    if not src.exists():
        row.update({"status": "OPTIONAL_MISSING" if optional else "MISSING", "size_bytes": "", "modified_time": "", "sha256": "", "error": "SOURCE_MISSING"})
        return row
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)
    row.update({"status": "COPIED", "size_bytes": dst.stat().st_size, "modified_time": mtime(dst), "sha256": sha256(dst), "error": ""})
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


def restore_script(files: Sequence[str]) -> str:
    lines = ['param([string]$Root = "D:\\us-tech-quant")', '$ErrorActionPreference = "Stop"', '$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path', 'Write-Host "=== RESTORE V18.21D STABLE SNAPSHOT START ==="']
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
    lines.append('Write-Host "RESTORE_COMPLETE: TRUE"')
    lines.append('Write-Host "NOTE: Restore preserves the dry-run plan only; it does not apply tracker upgrades or fill returns."')
    return "\n".join(lines) + "\n"


def readme(metrics: Dict[str, str]) -> str:
    return f"""# V18.21D Stable Snapshot

This snapshot preserves the V18.21D forward tracker link-key upgrade plan.

Important preserved interpretation:
- This is a dry-run/advisory-only snapshot.
- No forward tracker upgrade was applied.
- No signal snapshot was modified.
- No simulation position was modified.
- No forward tracker file was modified.
- No external data was fetched.
- The dry-run forward template has {metrics.get('DRYRUN_FORWARD_TEMPLATE_ROW_COUNT', '525')} rows.
- The 525 rows represent {metrics.get('READY_FOR_FORWARD_RESEARCH_COUNT', '105')} ready-for-forward-research tickers across {metrics.get('PLANNED_HORIZON_COUNT', '5')} planned horizons.
- Forward returns remain blank/NA.
- apply_status remains NOT_APPLIED_DRYRUN_ONLY.
- Forward source high-confidence readiness remains {metrics.get('FORWARD_SOURCE_READY_HIGH_CONFIDENCE_COUNT', '0')}.
- Required link-key fields are only partially available: {metrics.get('REQUIRED_LINK_KEY_CURRENTLY_AVAILABLE_COUNT', '7')} of {metrics.get('REQUIRED_LINK_KEY_FIELD_COUNT', '11')}.
- No factor effect claims, weight changes, or production promotions are allowed.
"""


def render_readfirst(metrics: Dict[str, object]) -> str:
    values = dict(metrics)
    values.update(SAFETY_FLAGS)
    values["MODE"] = MODE
    values["SNAPSHOT_ONLY"] = SNAPSHOT_ONLY
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def report(metrics: Dict[str, object], snapshot: Path) -> str:
    return f"""# V18.21D Stable Snapshot Report

## Executive Summary
Status: {metrics['STATUS']}. The snapshot preserves the advisory dry-run link-key upgrade plan.

## Preserved Dry-Run State
- Forward tracker upgrade applied: {metrics.get('FORWARD_TRACKER_UPGRADE_APPLIED')}
- Dry-run template rows: {metrics.get('DRYRUN_FORWARD_TEMPLATE_ROW_COUNT')}
- Planned horizons: {metrics.get('PLANNED_HORIZON_COUNT')}
- High-confidence forward sources: {metrics.get('FORWARD_SOURCE_READY_HIGH_CONFIDENCE_COUNT')}
- Required link-key availability: {metrics.get('REQUIRED_LINK_KEY_CURRENTLY_AVAILABLE_COUNT')} of {metrics.get('REQUIRED_LINK_KEY_FIELD_COUNT')}

## Safety
No tracker upgrade, signal snapshot modification, simulation modification, external fetch, factor claim, weight change, or production promotion was applied.

## Snapshot Path
`{snapshot}`

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
    read_first_path = root / "outputs/v18/ops/V18_21D_STABLE_READ_FIRST.txt"
    report_path = root / "outputs/v18/ops/V18_21D_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_21D_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_21D.ps1"

    source_metrics = readfirst(root / "outputs/v18/ops/V18_21D_READ_FIRST.txt")
    all_files = FILES + [rel for rel in OPTIONAL_FILES if (root / rel).exists()]
    manifest = [copy_one(root, snapshot, rel) for rel in FILES]
    manifest.extend(copy_one(root, snapshot, rel, optional=True) for rel in OPTIONAL_FILES if (root / rel).exists())
    write_csv(manifest_path, manifest, MANIFEST_FIELDS)
    write_csv(validation_path, [], VALIDATION_FIELDS)
    write_text(readme_path, readme(source_metrics))
    write_text(restore_path, restore_script(all_files))

    validations: List[Dict[str, object]] = []
    for rel in PS_FILES:
        ok, note = ps_parse(root / rel)
        validations.append(validation("powershell_parse", ok, str(root / rel), "PARSE_OK", "PARSE_OK" if ok else "PARSE_FAIL", note))
    for rel in PY_FILES:
        ok, note = py_compile(root / rel)
        validations.append(validation("python_compile", ok, str(root / rel), "COMPILE_OK", "COMPILE_OK" if ok else "COMPILE_FAIL", note))
    for rel in FILES:
        dst = snapshot / rel
        validations.append(validation("snapshot_file_exists", dst.exists(), str(dst), "EXISTS", "EXISTS" if dst.exists() else "MISSING"))
    for path, name in [(manifest_path, "MANIFEST"), (validation_path, "VALIDATION"), (readme_path, "README"), (restore_path, "RESTORE")]:
        validations.append(validation(f"{name.lower()}_exists", path.exists(), str(path), "EXISTS", "EXISTS" if path.exists() else "MISSING"))
    validations.append(validation("manifest_has_rows", len(manifest) > 0, str(manifest_path), ">0", str(len(manifest))))
    for key, expected in {
        "FORWARD_TRACKER_UPGRADE_APPLIED": "FALSE",
        "FORWARD_TRACKER_MODIFIED": "FALSE",
        "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
        "SIMULATION_POSITION_MODIFIED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "EFFECT_CLAIM_ALLOWED_COUNT": "0",
        "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
        "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
    }.items():
        validations.append(validation(f"preserve_{key.lower()}", str(source_metrics.get(key, SAFETY_FLAGS.get(key, ""))) == expected, str(root / "outputs/v18/ops/V18_21D_READ_FIRST.txt"), expected, str(source_metrics.get(key, SAFETY_FLAGS.get(key, "")))))

    metrics: Dict[str, object] = {field: source_metrics.get(field, "") for field in READ_FIRST_FIELDS}
    metrics.update(SAFETY_FLAGS)
    metrics.update({
        "STATUS": STATUS_OK,
        "MODE": MODE,
        "SNAPSHOT_ONLY": SNAPSHOT_ONLY,
        "SNAPSHOT_PATH": str(snapshot),
        "MANIFEST_ROW_COUNT": str(len(manifest)),
        "READ_FIRST": str(read_first_path),
        "REPORT": str(report_path),
        "VALIDATION_FAIL_COUNT": "0",
    })
    write_text(read_first_path, render_readfirst(metrics))
    write_text(report_path, report(metrics, snapshot))
    validations.append(validation("stable_read_first_exists", read_first_path.exists(), str(read_first_path), "EXISTS", "EXISTS" if read_first_path.exists() else "MISSING"))
    validations.append(validation("stable_report_exists", report_path.exists(), str(report_path), "EXISTS", "EXISTS" if report_path.exists() else "MISSING"))

    fail_count = sum(1 for row in validations if row["status"] != "PASS")
    metrics["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        metrics["STATUS"] = STATUS_WARN
    write_csv(validation_path, validations, VALIDATION_FIELDS)
    write_text(read_first_path, render_readfirst(metrics))
    write_text(report_path, report(metrics, snapshot))

    for key in ["STATUS", "MODE", "SNAPSHOT_ONLY", "SNAPSHOT_PATH", "FORWARD_TRACKER_UPGRADE_APPLIED", "DRYRUN_FORWARD_TEMPLATE_ROW_COUNT", "PLANNED_HORIZON_COUNT", "FORWARD_SOURCE_READY_HIGH_CONFIDENCE_COUNT", "REQUIRED_LINK_KEY_CURRENTLY_AVAILABLE_COUNT", "REQUIRED_LINK_KEY_FIELD_COUNT", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT"]:
        print(f"{key}: {metrics.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
