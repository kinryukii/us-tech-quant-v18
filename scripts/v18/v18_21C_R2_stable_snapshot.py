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


STATUS_OK = "OK_V18_21C_R2_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_21C_R2_STABLE_SNAPSHOT_VALIDATION_FAILED"
MODE = "SNAPSHOT_ONLY"
SNAPSHOT_ONLY = "TRUE"
PREFIX = "V18_21C_R2_stable_factor_effectiveness_forward_match_quality_plan"

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
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "SIMULATION_POSITION_MODIFIED": "FALSE",
    "FORWARD_TRACKER_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
    "STABLE_SNAPSHOT_MODIFIED": "TRUE",
}

FILES = [
    "scripts/v18/v18_21C_factor_effectiveness_read_center.py",
    "scripts/v18/run_v18_21C_factor_effectiveness_read_center.ps1",
    "scripts/v18/v18_21C_R1_sample_maturity_forward_match_patch.py",
    "scripts/v18/run_v18_21C_R1_sample_maturity_forward_match_patch.ps1",
    "scripts/v18/v18_21C_R2_forward_match_key_quality_plan.py",
    "scripts/v18/run_v18_21C_R2_forward_match_key_quality_plan.ps1",
    "outputs/v18/factor_effectiveness/V18_21C_CURRENT_EFFECTIVENESS_READINESS_AUDIT.csv",
    "outputs/v18/factor_effectiveness/V18_21C_CURRENT_FACTOR_BUCKET_RESEARCH_SUMMARY.csv",
    "outputs/v18/factor_effectiveness/V18_21C_CURRENT_FACTOR_EVIDENCE_GAP_AUDIT.csv",
    "outputs/v18/factor_effectiveness/V18_21C_CURRENT_FORWARD_OUTCOME_SOURCE_AUDIT.csv",
    "outputs/v18/factor_effectiveness/V18_21C_CURRENT_RESEARCH_CONCLUSION_SUMMARY.csv",
    "outputs/v18/ops/V18_21C_READ_FIRST.txt",
    "outputs/v18/ops/V18_21C_CURRENT_FACTOR_EFFECTIVENESS_RESEARCH_REPORT.md",
    "outputs/v18/factor_effectiveness/V18_21C_R1_CURRENT_FORWARD_MATCH_QUALITY_AUDIT.csv",
    "outputs/v18/factor_effectiveness/V18_21C_R1_CURRENT_HORIZON_MATURITY_AUDIT.csv",
    "outputs/v18/factor_effectiveness/V18_21C_R1_CURRENT_BUCKET_DISTRIBUTION_AUDIT.csv",
    "outputs/v18/factor_effectiveness/V18_21C_R1_CURRENT_FACTOR_MATURITY_SCORECARD.csv",
    "outputs/v18/factor_effectiveness/V18_21C_R1_CURRENT_RESEARCH_CONCLUSION_SUMMARY.csv",
    "outputs/v18/ops/V18_21C_R1_READ_FIRST.txt",
    "outputs/v18/ops/V18_21C_R1_CURRENT_SAMPLE_MATURITY_FORWARD_MATCH_REPORT.md",
    "outputs/v18/factor_effectiveness/V18_21C_R2_CURRENT_FORWARD_SOURCE_KEY_AVAILABILITY_AUDIT.csv",
    "outputs/v18/factor_effectiveness/V18_21C_R2_CURRENT_MATCH_FAILURE_REASON_AUDIT.csv",
    "outputs/v18/factor_effectiveness/V18_21C_R2_CURRENT_MULTI_HORIZON_READINESS_PLAN.csv",
    "outputs/v18/factor_effectiveness/V18_21C_R2_CURRENT_FORWARD_RESEARCH_KEY_UPGRADE_PLAN.csv",
    "outputs/v18/factor_effectiveness/V18_21C_R2_CURRENT_RESEARCH_CONCLUSION_SUMMARY.csv",
    "outputs/v18/ops/V18_21C_R2_READ_FIRST.txt",
    "outputs/v18/ops/V18_21C_R2_CURRENT_FORWARD_MATCH_KEY_QUALITY_REPORT.md",
]

PS_FILES = [
    "scripts/v18/run_v18_21C_R2_stable_snapshot.ps1",
    "scripts/v18/run_v18_21C_factor_effectiveness_read_center.ps1",
    "scripts/v18/run_v18_21C_R1_sample_maturity_forward_match_patch.ps1",
    "scripts/v18/run_v18_21C_R2_forward_match_key_quality_plan.ps1",
]
PY_FILES = [
    "scripts/v18/v18_21C_R2_stable_snapshot.py",
    "scripts/v18/v18_21C_factor_effectiveness_read_center.py",
    "scripts/v18/v18_21C_R1_sample_maturity_forward_match_patch.py",
    "scripts/v18/v18_21C_R2_forward_match_key_quality_plan.py",
]

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "SNAPSHOT_ONLY", "POLICY_APPLIED", "SIGNAL_SNAPSHOT_ROW_COUNT",
    "SIGNAL_SNAPSHOT_HISTORY_COUNT", "FORWARD_OUTCOME_SOURCE_COUNT", "FORWARD_OUTCOME_MATCHED_SIGNAL_COUNT",
    "HIGH_CONFIDENCE_MATCH_COUNT", "MEDIUM_CONFIDENCE_MATCH_COUNT", "LOW_CONFIDENCE_MATCH_COUNT",
    "UNMATCHED_OR_AMBIGUOUS_COUNT", "HIGH_QUALITY_FORWARD_SOURCE_COUNT", "MEDIUM_QUALITY_FORWARD_SOURCE_COUNT",
    "TICKER_DATE_ONLY_SOURCE_COUNT", "TICKER_ONLY_LOW_CONFIDENCE_SOURCE_COUNT", "HORIZON_1D_USABLE_COUNT",
    "HORIZON_3D_USABLE_COUNT", "HORIZON_5D_USABLE_COUNT", "HORIZON_10D_USABLE_COUNT",
    "HORIZON_20D_USABLE_COUNT", "MULTI_HORIZON_READINESS_STATUS", "FORWARD_KEY_UPGRADE_PLAN_READY",
    "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT", "PRODUCTION_PROMOTION_ALLOWED_COUNT",
    "RESEARCH_CONCLUSION_STATUS", "EFFECTIVENESS_EVIDENCE_STATUS", "TRUE_5DAY_UNIQUE_COVERAGE_MET",
    "COVERAGE_WINDOW_COMPLETE", "DAILY_TRUST_LEVEL", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "PRICE_CACHE_MODIFIED", "RANKING_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED", "PRICE_FACTOR_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED",
    "SIMULATION_POSITION_MODIFIED", "FORWARD_TRACKER_MODIFIED", "PROMOTION_DEMOTION_MODIFIED",
    "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED", "EXTERNAL_DATA_FETCHED",
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
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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


def copy_one(root: Path, snapshot: Path, rel: str) -> Dict[str, object]:
    src = root / rel
    dst = snapshot / rel
    row = {
        "category": "SCRIPT" if rel.startswith("scripts/") else "OUTPUT",
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
        row.update({"status": "COPIED", "size_bytes": dst.stat().st_size, "modified_time": mtime(dst), "sha256": sha256(dst), "error": ""})
    except Exception as exc:
        row.update({"status": "COPY_FAILED", "size_bytes": "", "modified_time": "", "sha256": "", "error": f"{type(exc).__name__}: {exc}"})
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


def restore_script() -> str:
    lines = ['param([string]$Root = "D:\\us-tech-quant")', '$ErrorActionPreference = "Stop"', '$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path', 'Write-Host "=== RESTORE V18.21C-R2 STABLE SNAPSHOT START ==="']
    for rel in FILES:
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
    lines.append('Write-Host "NOTE: Restore is advisory research only and does not apply key upgrades or production changes."')
    return "\n".join(lines) + "\n"


def readme(metrics: Dict[str, str]) -> str:
    return f"""# V18.21C-R2 Stable Snapshot

This snapshot preserves the V18.21C-R2 factor effectiveness research read center and forward match key quality plan.

Important preserved interpretation:
- This is a conservative research milestone, not a factor-effectiveness proof.
- No factor is marked effective.
- No weight change is allowed.
- No production promotion is allowed.
- Forward match quality remains low: {metrics.get('HIGH_CONFIDENCE_MATCH_COUNT', '0')} high-confidence, {metrics.get('MEDIUM_CONFIDENCE_MATCH_COUNT', '0')} medium-confidence, {metrics.get('LOW_CONFIDENCE_MATCH_COUNT', '20')} low-confidence matches.
- Multi-horizon readiness is {metrics.get('MULTI_HORIZON_READINESS_STATUS', 'NOT_READY_MULTI_HORIZON')}.
- Only 1D has {metrics.get('HORIZON_1D_USABLE_COUNT', '20')} usable returns; 3D/5D/10D/20D have {metrics.get('HORIZON_3D_USABLE_COUNT', '0')}/{metrics.get('HORIZON_5D_USABLE_COUNT', '0')}/{metrics.get('HORIZON_10D_USABLE_COUNT', '0')}/{metrics.get('HORIZON_20D_USABLE_COUNT', '0')} usable returns.
- The forward key upgrade plan is ready but not applied.
- TRUE_5DAY_UNIQUE_COVERAGE_MET remains {metrics.get('TRUE_5DAY_UNIQUE_COVERAGE_MET', 'FALSE')}.
- COVERAGE_WINDOW_COMPLETE remains {metrics.get('COVERAGE_WINDOW_COMPLETE', 'FALSE')}.
- DAILY_TRUST_LEVEL remains {metrics.get('DAILY_TRUST_LEVEL', 'MEDIUM')}.
- Official decision, ranking, technical timing, price factors, signal snapshots, simulation positions, forward tracker state, manual state, broker execution, auto-trade, and auto-sell are unaffected.
"""


def render_readfirst(metrics: Dict[str, object]) -> str:
    values = dict(metrics)
    values.update(SAFETY_FLAGS)
    values["MODE"] = MODE
    values["SNAPSHOT_ONLY"] = SNAPSHOT_ONLY
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def report(metrics: Dict[str, object], snapshot: Path) -> str:
    return f"""# V18.21C-R2 Stable Snapshot Report

## Executive Summary
Status: {metrics['STATUS']}. The stable snapshot preserves the advisory factor effectiveness research read center and forward key-quality plan.

## Preserved Research Semantics
- High-confidence matches: {metrics.get('HIGH_CONFIDENCE_MATCH_COUNT')}
- Medium-confidence matches: {metrics.get('MEDIUM_CONFIDENCE_MATCH_COUNT')}
- Low-confidence matches: {metrics.get('LOW_CONFIDENCE_MATCH_COUNT')}
- Multi-horizon readiness: {metrics.get('MULTI_HORIZON_READINESS_STATUS')}
- Effect claims allowed: {metrics.get('EFFECT_CLAIM_ALLOWED_COUNT')}
- Weight changes allowed: {metrics.get('WEIGHT_CHANGE_ALLOWED_COUNT')}
- Production promotions allowed: {metrics.get('PRODUCTION_PROMOTION_ALLOWED_COUNT')}

## Safety
Snapshot-only. No external data fetch, no forward key upgrade application, and no protected behavior/state changes.

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
    read_first_path = root / "outputs/v18/ops/V18_21C_R2_STABLE_READ_FIRST.txt"
    report_path = root / "outputs/v18/ops/V18_21C_R2_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_21C_R2_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_21C_R2.ps1"

    source_metrics = readfirst(root / "outputs/v18/ops/V18_21C_R2_READ_FIRST.txt")
    manifest = [copy_one(root, snapshot, rel) for rel in FILES]
    write_csv(manifest_path, manifest, MANIFEST_FIELDS)
    write_csv(validation_path, [], VALIDATION_FIELDS)
    write_text(readme_path, readme(source_metrics))
    write_text(restore_path, restore_script())

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
    for key, expected in [("EFFECT_CLAIM_ALLOWED_COUNT", "0"), ("WEIGHT_CHANGE_ALLOWED_COUNT", "0"), ("PRODUCTION_PROMOTION_ALLOWED_COUNT", "0"), ("EXTERNAL_DATA_FETCHED", "FALSE")]:
        validations.append(validation(f"preserve_{key.lower()}", str(source_metrics.get(key, SAFETY_FLAGS.get(key, ""))) == expected, str(root / "outputs/v18/ops/V18_21C_R2_READ_FIRST.txt"), expected, str(source_metrics.get(key, SAFETY_FLAGS.get(key, "")))))

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

    for key in ["STATUS", "MODE", "SNAPSHOT_ONLY", "SNAPSHOT_PATH", "HIGH_CONFIDENCE_MATCH_COUNT", "LOW_CONFIDENCE_MATCH_COUNT", "MULTI_HORIZON_READINESS_STATUS", "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT", "PRODUCTION_PROMOTION_ALLOWED_COUNT", "MANIFEST_ROW_COUNT", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT"]:
        print(f"{key}: {metrics.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
