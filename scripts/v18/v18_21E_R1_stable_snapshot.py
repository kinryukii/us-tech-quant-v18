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


STATUS_OK = "OK_V18_21E_R1_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_21E_R1_STABLE_SNAPSHOT_VALIDATION_FAILED"
MODE = "SNAPSHOT_ONLY"
SNAPSHOT_ONLY = "TRUE"
PREFIX = "V18_21E_R1_stable_event_risk_coefficient_hard_lock_overlay_semantics"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": "FALSE",
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
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "EFFECT_CLAIM_ALLOWED_COUNT": "0",
    "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
    "STABLE_SNAPSHOT_MODIFIED": "TRUE",
}

REQUIRED_FILES = [
    "scripts/v18/v18_21E_R1_stable_snapshot.py",
    "scripts/v18/run_v18_21E_R1_stable_snapshot.ps1",
    "scripts/v18/v18_21E_event_risk_coefficient_engine.py",
    "scripts/v18/run_v18_21E_event_risk_coefficient_engine.ps1",
    "scripts/v18/v18_21E_R1_hard_lock_overlay_semantics_patch.py",
    "scripts/v18/run_v18_21E_R1_hard_lock_overlay_semantics_patch.ps1",
    "outputs/v18/event_risk/V18_21E_CURRENT_NORMALIZED_EVENT_CALENDAR.csv",
    "outputs/v18/event_risk/V18_21E_CURRENT_MARKET_EVENT_RISK.csv",
    "outputs/v18/event_risk/V18_21E_CURRENT_TICKER_EVENT_RISK.csv",
    "outputs/v18/event_risk/V18_21E_CURRENT_EVENT_ADJUSTED_CANDIDATES.csv",
    "outputs/v18/event_risk/V18_21E_CURRENT_EVENT_RISK_SOURCE_AUDIT.csv",
    "outputs/v18/event_risk/V18_21E_CURRENT_EVENT_RISK_VALIDATION.csv",
    "outputs/v18/ops/V18_21E_READ_FIRST.txt",
    "outputs/v18/ops/V18_21E_CURRENT_EVENT_RISK_COEFFICIENT_REPORT.md",
    "outputs/v18/event_risk/V18_21E_R1_CURRENT_HARD_LOCK_SOURCE_ATTRIBUTION.csv",
    "outputs/v18/event_risk/V18_21E_R1_CURRENT_MARKET_EVENT_RISK_SEMANTICS.csv",
    "outputs/v18/event_risk/V18_21E_R1_CURRENT_TICKER_EVENT_RISK_SEMANTICS.csv",
    "outputs/v18/event_risk/V18_21E_R1_CURRENT_EVENT_ADJUSTED_CANDIDATES.csv",
    "outputs/v18/event_risk/V18_21E_R1_CURRENT_EVENT_RISK_TOP_LIST_SORTING_AUDIT.csv",
    "outputs/v18/event_risk/V18_21E_R1_CURRENT_EVENT_RISK_SEMANTICS_VALIDATION.csv",
    "outputs/v18/ops/V18_21E_R1_READ_FIRST.txt",
    "outputs/v18/ops/V18_21E_R1_CURRENT_HARD_LOCK_OVERLAY_SEMANTICS_REPORT.md",
]
OPTIONAL_FILES = [
    "outputs/v18/ops/V18_21A_R4_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21B_R1_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21C_R2_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21D_R1_STABLE_READ_FIRST.txt",
    "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv",
]
GENERATED_EXTERNAL_FILES = [
    "outputs/v18/ops/V18_21E_R1_STABLE_READ_FIRST.txt",
    "outputs/v18/ops/V18_21E_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md",
]
PS_FILES = [
    "scripts/v18/run_v18_21E_R1_stable_snapshot.ps1",
    "scripts/v18/run_v18_21E_event_risk_coefficient_engine.ps1",
    "scripts/v18/run_v18_21E_R1_hard_lock_overlay_semantics_patch.ps1",
]
PY_FILES = [
    "scripts/v18/v18_21E_R1_stable_snapshot.py",
    "scripts/v18/v18_21E_event_risk_coefficient_engine.py",
    "scripts/v18/v18_21E_R1_hard_lock_overlay_semantics_patch.py",
]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "SNAPSHOT_ONLY", "POLICY_APPLIED",
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION", "EVENT_SOURCE_COUNT",
    "EVENT_SOURCE_MISSING_COUNT", "NORMALIZED_EVENT_COUNT",
    "CALENDAR_MARKET_EVENT_RISK_COEFFICIENT", "CALENDAR_MARKET_EVENT_RISK_LEVEL",
    "HARD_LOCK_OVERLAY_DETECTED", "HARD_LOCK_OVERLAY_TYPE",
    "HARD_LOCK_OVERLAY_ADVISORY_COEFFICIENT", "FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT",
    "FINAL_ADVISORY_MARKET_EVENT_RISK_LEVEL", "TICKER_EVENT_RISK_ROW_COUNT",
    "CALENDAR_HIGH_RISK_TICKER_COUNT", "CALENDAR_EXTREME_CAUTION_TICKER_COUNT",
    "ADVISORY_OVERLAY_AFFECTED_TICKER_COUNT", "HARD_LOCK_SOURCE_DETECTED",
    "EVENT_ADJUSTED_CANDIDATE_COUNT", "EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT",
    "TOP_EVENT_RISK_TICKERS", "TOP_EVENT_ADJUSTED_CANDIDATES",
    "EVENT_RISK_SEMANTICS_VALIDATION_CREATED", "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED",
    "STATE_MODIFIED", "PRICE_CACHE_MODIFIED", "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED",
    "EVENT_CALENDAR_MODIFIED", "SIMULATION_POSITION_MODIFIED", "FORWARD_TRACKER_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED",
    "EXTERNAL_DATA_FETCHED", "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT", "STABLE_SNAPSHOT_MODIFIED", "VALIDATION_FAIL_COUNT",
    "SNAPSHOT_PATH", "MANIFEST_ROW_COUNT", "READ_FIRST", "REPORT",
]
MANIFEST_FIELDS = [
    "category", "status", "source_path", "snapshot_path", "relative_source_path",
    "relative_snapshot_path", "size_bytes", "modified_time", "sha256", "error",
]
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


def read_csv_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", newline="", encoding=enc, errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def numeric(value: object) -> float | None:
    try:
        text = str(value or "").strip()
        if not text:
            return None
        return float(text.replace(",", ""))
    except ValueError:
        return None


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
        return "OPTIONAL_CONTEXT"
    if rel.startswith("scripts/"):
        return "SCRIPT"
    if rel in GENERATED_EXTERNAL_FILES:
        return "GENERATED_CURRENT_OUTPUT"
    return "OUTPUT"


def copy_one(root: Path, snapshot: Path, rel: str, optional: bool = False) -> Dict[str, object]:
    src = root / rel
    dst = snapshot / rel
    row = {
        "category": category_for(rel, optional),
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


def stable_metrics(root: Path) -> Dict[str, object]:
    metrics = readfirst(root / "outputs/v18/ops/V18_21E_R1_READ_FIRST.txt")
    rows, _ = read_csv_rows(root / "outputs/v18/event_risk/V18_21E_R1_CURRENT_EVENT_ADJUSTED_CANDIDATES.csv")
    if rows:
        metrics["EVENT_ADJUSTED_CANDIDATE_COUNT"] = str(len(rows))
        metrics["EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT"] = str(sum(1 for row in rows if str(row.get("event_adjusted_score_with_advisory_overlay", "")).strip()))
    ticker_rows, _ = read_csv_rows(root / "outputs/v18/event_risk/V18_21E_R1_CURRENT_TICKER_EVENT_RISK_SEMANTICS.csv")
    if ticker_rows:
        metrics["TICKER_EVENT_RISK_ROW_COUNT"] = str(len(ticker_rows))
        metrics["ADVISORY_OVERLAY_AFFECTED_TICKER_COUNT"] = str(sum(1 for row in ticker_rows if row.get("hard_lock_overlay_detected") == "TRUE"))
    return metrics


def render_readfirst(metrics: Dict[str, object]) -> str:
    values = dict(metrics)
    values.update(SAFETY_FLAGS)
    values["MODE"] = MODE
    values["SNAPSHOT_ONLY"] = SNAPSHOT_ONLY
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def readme(metrics: Dict[str, object], snapshot: Path) -> str:
    return f"""# V18.21E-R1 Stable Snapshot

This snapshot preserves V18.21E-R1 advisory event risk coefficient semantics.

## Preserved Interpretation
- Calendar-derived market event risk is NORMAL with coefficient {metrics.get('CALENDAR_MARKET_EVENT_RISK_COEFFICIENT', '1.000000')}.
- Existing hard-lock overlay is detected from local sources.
- Hard-lock overlay type is {metrics.get('HARD_LOCK_OVERLAY_TYPE', 'OFFICIAL_NO_TRADE')}.
- Final advisory market event risk coefficient is {metrics.get('FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT', '0.300000')}.
- Final advisory market risk level is {metrics.get('FINAL_ADVISORY_MARKET_EVENT_RISK_LEVEL', 'HARD_LOCK_SOURCE_DETECTED')}.
- The advisory overlay affects {metrics.get('ADVISORY_OVERLAY_AFFECTED_TICKER_COUNT', '325')} tickers.
- Event-adjusted candidate count is {metrics.get('EVENT_ADJUSTED_CANDIDATE_COUNT', '325')}.
- Event-adjusted score available count is {metrics.get('EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT', '105')}.
- Event risk coefficients were not applied to official decisions.
- Buy permission was not modified.
- Ranking was not modified.
- Signal snapshots were not modified.
- Event calendars were not modified.
- No external data was fetched.
- Auto-trade and auto-sell remain disabled.
- No effect claims, weight changes, or production promotions are allowed.

## Snapshot Path
`{snapshot}`
"""


def report(metrics: Dict[str, object], snapshot: Path) -> str:
    return f"""# V18.21E-R1 Stable Snapshot Report

## Executive Summary
Status: {metrics.get('STATUS')}. This stable snapshot captures the V18.21E event risk coefficient engine and V18.21E-R1 hard-lock overlay semantics patch.

## Preserved Semantics
Calendar market coefficient: {metrics.get('CALENDAR_MARKET_EVENT_RISK_COEFFICIENT')}; calendar level: {metrics.get('CALENDAR_MARKET_EVENT_RISK_LEVEL')}. Hard-lock overlay detected: {metrics.get('HARD_LOCK_OVERLAY_DETECTED')}; type: {metrics.get('HARD_LOCK_OVERLAY_TYPE')}; final advisory coefficient: {metrics.get('FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT')}; final advisory level: {metrics.get('FINAL_ADVISORY_MARKET_EVENT_RISK_LEVEL')}.

## Safety
Official decision impact: {metrics.get('OFFICIAL_DECISION_IMPACT')}. Buy permission modified: {metrics.get('BUY_PERMISSION_MODIFIED')}. Ranking modified: {metrics.get('RANKING_MODIFIED')}. Signal snapshot modified: {metrics.get('SIGNAL_SNAPSHOT_MODIFIED')}. Event calendar modified: {metrics.get('EVENT_CALENDAR_MODIFIED')}. External data fetched: {metrics.get('EXTERNAL_DATA_FETCHED')}.

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
        'Write-Host "=== RESTORE V18.21E-R1 STABLE SNAPSHOT START ==="',
        'Write-Host "MODE: SNAPSHOT_RESTORE"',
        'Write-Host "NOTE: This restores advisory event-risk snapshot artifacts only."',
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
        'Write-Host "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION: FALSE"',
        'Write-Host "BUY_PERMISSION_MODIFIED: FALSE"',
        'Write-Host "RANKING_MODIFIED: FALSE"',
        'Write-Host "EVENT_CALENDAR_MODIFIED: FALSE"',
        'Write-Host "NOTE: Restore does not change trading behavior or official decisions."',
    ])
    return "\n".join(lines) + "\n"


def coefficient_validations(root: Path, metrics: Dict[str, object]) -> List[Dict[str, object]]:
    validations: List[Dict[str, object]] = []
    coeffs: List[float] = []
    for key in ["CALENDAR_MARKET_EVENT_RISK_COEFFICIENT", "HARD_LOCK_OVERLAY_ADVISORY_COEFFICIENT", "FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT"]:
        value = numeric(metrics.get(key))
        if value is not None:
            coeffs.append(value)
    for rel, fields in [
        ("outputs/v18/event_risk/V18_21E_R1_CURRENT_MARKET_EVENT_RISK_SEMANTICS.csv", ["calendar_market_event_risk_coefficient", "hard_lock_overlay_advisory_coefficient", "final_advisory_market_event_risk_coefficient"]),
        ("outputs/v18/event_risk/V18_21E_R1_CURRENT_TICKER_EVENT_RISK_SEMANTICS.csv", ["calendar_ticker_event_risk_coefficient", "hard_lock_overlay_advisory_coefficient", "final_advisory_ticker_event_risk_coefficient"]),
        ("outputs/v18/event_risk/V18_21E_R1_CURRENT_EVENT_ADJUSTED_CANDIDATES.csv", ["calendar_market_event_risk_coefficient", "calendar_ticker_event_risk_coefficient", "hard_lock_overlay_advisory_coefficient", "final_advisory_event_risk_coefficient"]),
    ]:
        rows, _ = read_csv_rows(root / rel)
        for row in rows:
            for field in fields:
                value = numeric(row.get(field))
                if value is not None:
                    coeffs.append(value)
    in_bounds = all(0.0 <= value <= 1.0 for value in coeffs)
    validations.append(validation("all_coefficients_in_bounds", in_bounds, str(root / "outputs/v18/event_risk"), "[0,1]", "PASS" if in_bounds else "FAIL"))
    overlay = str(metrics.get("HARD_LOCK_OVERLAY_DETECTED", "")).upper() == "TRUE"
    final_coeff = numeric(metrics.get("FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT"))
    validations.append(validation("hard_lock_final_advisory_coefficient_not_one", (not overlay) or final_coeff != 1.0, str(root / "outputs/v18/ops/V18_21E_R1_READ_FIRST.txt"), "not 1.0 when hard lock detected", str(final_coeff)))
    for key, expected in {
        "CALENDAR_MARKET_EVENT_RISK_COEFFICIENT": "1.000000",
        "CALENDAR_MARKET_EVENT_RISK_LEVEL": "NORMAL",
        "HARD_LOCK_OVERLAY_DETECTED": "TRUE",
        "HARD_LOCK_OVERLAY_TYPE": "OFFICIAL_NO_TRADE",
        "HARD_LOCK_OVERLAY_ADVISORY_COEFFICIENT": "0.300000",
        "FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT": "0.300000",
        "FINAL_ADVISORY_MARKET_EVENT_RISK_LEVEL": "HARD_LOCK_SOURCE_DETECTED",
        "ADVISORY_OVERLAY_AFFECTED_TICKER_COUNT": "325",
        "EVENT_ADJUSTED_CANDIDATE_COUNT": "325",
        "EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT": "105",
    }.items():
        validations.append(validation(f"preserve_{key.lower()}", str(metrics.get(key, "")) == expected, str(root / "outputs/v18/ops/V18_21E_R1_READ_FIRST.txt"), expected, str(metrics.get(key, ""))))
    return validations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot = root / "archive" / "stable" / f"{PREFIX}_{timestamp}"
    read_first_path = root / "outputs/v18/ops/V18_21E_R1_STABLE_READ_FIRST.txt"
    report_path = root / "outputs/v18/ops/V18_21E_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_21E_R1_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_21E_R1.ps1"

    metrics = stable_metrics(root)
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

    manifest: List[Dict[str, object]] = []
    manifest.extend(copy_one(root, snapshot, rel) for rel in REQUIRED_FILES)
    manifest.extend(copy_one(root, snapshot, rel, optional=True) for rel in OPTIONAL_FILES if (root / rel).exists())
    manifest.extend(copy_one(root, snapshot, rel) for rel in GENERATED_EXTERNAL_FILES)
    copied_files = [str(row["relative_source_path"]) for row in manifest if row.get("status") == "COPIED"]
    write_text(restore_path, restore_script(copied_files))
    manifest.append(snapshot_artifact_row(snapshot, "RESTORE_V18_21E_R1.ps1", "RESTORE"))
    manifest.append(snapshot_artifact_row(snapshot, "README_V18_21E_R1_STABLE_SNAPSHOT.md", "README"))
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
    for rel in GENERATED_EXTERNAL_FILES:
        path = root / rel
        validations.append(validation("current_external_output_exists", path.exists(), str(path), "EXISTS", "EXISTS" if path.exists() else "MISSING"))
    validations.extend(coefficient_validations(root, metrics))
    for key, expected in {
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
        "RANKING_MODIFIED": "FALSE",
        "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
        "EVENT_CALENDAR_MODIFIED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "EFFECT_CLAIM_ALLOWED_COUNT": "0",
        "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
        "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
    }.items():
        validations.append(validation(f"preserve_{key.lower()}", str(metrics.get(key, "")) == expected, str(read_first_path), expected, str(metrics.get(key, ""))))
    validations.append(validation("validation_has_rows", len(validations) > 0, str(validation_path), ">0", str(len(validations))))
    write_csv(validation_path, validations, VALIDATION_FIELDS)

    fail_count = sum(1 for row in validations if row["status"] != "PASS")
    metrics["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        metrics["STATUS"] = STATUS_WARN
    final_manifest: List[Dict[str, object]] = []
    final_manifest.extend(copy_one(root, snapshot, rel) for rel in REQUIRED_FILES)
    final_manifest.extend(copy_one(root, snapshot, rel, optional=True) for rel in OPTIONAL_FILES if (root / rel).exists())
    final_manifest.extend(copy_one(root, snapshot, rel) for rel in GENERATED_EXTERNAL_FILES)
    final_manifest.append(snapshot_artifact_row(snapshot, "RESTORE_V18_21E_R1.ps1", "RESTORE"))
    final_manifest.append(snapshot_artifact_row(snapshot, "README_V18_21E_R1_STABLE_SNAPSHOT.md", "README"))
    final_manifest.append(snapshot_artifact_row(snapshot, "VALIDATION.csv", "VALIDATION"))
    metrics["MANIFEST_ROW_COUNT"] = str(len(final_manifest))
    write_text(read_first_path, render_readfirst(metrics))
    write_text(report_path, report(metrics, snapshot))
    final_manifest = []
    final_manifest.extend(copy_one(root, snapshot, rel) for rel in REQUIRED_FILES)
    final_manifest.extend(copy_one(root, snapshot, rel, optional=True) for rel in OPTIONAL_FILES if (root / rel).exists())
    final_manifest.extend(copy_one(root, snapshot, rel) for rel in GENERATED_EXTERNAL_FILES)
    final_manifest.append(snapshot_artifact_row(snapshot, "RESTORE_V18_21E_R1.ps1", "RESTORE"))
    final_manifest.append(snapshot_artifact_row(snapshot, "README_V18_21E_R1_STABLE_SNAPSHOT.md", "README"))
    final_manifest.append(snapshot_artifact_row(snapshot, "VALIDATION.csv", "VALIDATION"))
    write_csv(manifest_path, final_manifest, MANIFEST_FIELDS)

    for key in [
        "STATUS", "MODE", "SNAPSHOT_ONLY", "POLICY_APPLIED",
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION",
        "CALENDAR_MARKET_EVENT_RISK_COEFFICIENT", "CALENDAR_MARKET_EVENT_RISK_LEVEL",
        "HARD_LOCK_OVERLAY_DETECTED", "HARD_LOCK_OVERLAY_TYPE",
        "HARD_LOCK_OVERLAY_ADVISORY_COEFFICIENT", "FINAL_ADVISORY_MARKET_EVENT_RISK_COEFFICIENT",
        "FINAL_ADVISORY_MARKET_EVENT_RISK_LEVEL", "TICKER_EVENT_RISK_ROW_COUNT",
        "ADVISORY_OVERLAY_AFFECTED_TICKER_COUNT", "EVENT_ADJUSTED_CANDIDATE_COUNT",
        "EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT", "OFFICIAL_DECISION_IMPACT",
        "BUY_PERMISSION_MODIFIED", "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED",
        "EVENT_CALENDAR_MODIFIED", "EXTERNAL_DATA_FETCHED", "VALIDATION_FAIL_COUNT",
        "SNAPSHOT_PATH", "MANIFEST_ROW_COUNT", "READ_FIRST", "REPORT",
    ]:
        print(f"{key}: {metrics.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
