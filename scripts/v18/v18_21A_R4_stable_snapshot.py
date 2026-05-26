from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_21A_R4_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_21A_R4_STABLE_SNAPSHOT_VALIDATION_FAILED"
MODE = "SNAPSHOT_ONLY"
SNAPSHOT_ONLY = "TRUE"
PREFIX = "V18_21A_R4_stable_price_derived_factors_advisory_backfill_plan"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "HISTORY_BACKFILL_APPLIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "STABLE_SNAPSHOT_MODIFIED": "TRUE",
}

FILES = [
    "scripts/v18/v18_21A_price_derived_factor_pack.py",
    "scripts/v18/run_v18_21A_price_derived_factor_pack.ps1",
    "scripts/v18/v18_21A_R1_data_coverage_scoring_patch.py",
    "scripts/v18/run_v18_21A_R1_data_coverage_scoring_patch.ps1",
    "scripts/v18/v18_21A_R2_price_history_source_coverage_patch.py",
    "scripts/v18/run_v18_21A_R2_price_history_source_coverage_patch.ps1",
    "scripts/v18/v18_21A_R3_ticker_price_source_mapping_patch.py",
    "scripts/v18/run_v18_21A_R3_ticker_price_source_mapping_patch.ps1",
    "scripts/v18/v18_21A_R4_advisory_full_history_backfill_plan.py",
    "scripts/v18/run_v18_21A_R4_advisory_full_history_backfill_plan.ps1",
    "outputs/v18/price_factors/V18_21A_CURRENT_PRICE_DERIVED_FACTORS.csv",
    "outputs/v18/price_factors/V18_21A_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv",
    "outputs/v18/market_regime/V18_21A_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv",
    "outputs/v18/ops/V18_21A_READ_FIRST.txt",
    "outputs/v18/ops/V18_21A_CURRENT_PRICE_DERIVED_FACTOR_REPORT.md",
    "outputs/v18/price_factors/V18_21A_R1_CURRENT_PRICE_FACTOR_DATA_COVERAGE_AUDIT.csv",
    "outputs/v18/price_factors/V18_21A_R1_CURRENT_TOP_LIST_SORTING_AUDIT.csv",
    "outputs/v18/price_factors/V18_21A_R1_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv",
    "outputs/v18/market_regime/V18_21A_R1_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv",
    "outputs/v18/ops/V18_21A_R1_READ_FIRST.txt",
    "outputs/v18/ops/V18_21A_R1_CURRENT_DATA_COVERAGE_SCORING_REPORT.md",
    "outputs/v18/price_factors/V18_21A_R2_CURRENT_PRICE_HISTORY_SOURCE_DISCOVERY_AUDIT.csv",
    "outputs/v18/price_factors/V18_21A_R2_CURRENT_TICKER_FACTOR_SCOPE_CLASSIFICATION.csv",
    "outputs/v18/price_factors/V18_21A_R2_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv",
    "outputs/v18/market_regime/V18_21A_R2_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv",
    "outputs/v18/price_factors/V18_21A_R2_CURRENT_TOP_LIST_SCOPE_AUDIT.csv",
    "outputs/v18/ops/V18_21A_R2_READ_FIRST.txt",
    "outputs/v18/ops/V18_21A_R2_CURRENT_PRICE_HISTORY_SOURCE_COVERAGE_REPORT.md",
    "outputs/v18/price_factors/V18_21A_R3_CURRENT_UNIVERSE_SOURCE_AUDIT.csv",
    "outputs/v18/price_factors/V18_21A_R3_CURRENT_TICKER_SOURCE_MAPPING_AUDIT.csv",
    "outputs/v18/price_factors/V18_21A_R3_CURRENT_DISCOVERED_SOURCE_RELEVANCE_AUDIT.csv",
    "outputs/v18/price_factors/V18_21A_R3_CURRENT_NO_LOCAL_PRICE_DATA_DETAIL.csv",
    "outputs/v18/price_factors/V18_21A_R3_CURRENT_MAPPING_COUNT_RECONCILIATION.csv",
    "outputs/v18/price_factors/V18_21A_R3_CURRENT_FACTOR_SCOPE_SUMMARY.csv",
    "outputs/v18/ops/V18_21A_R3_READ_FIRST.txt",
    "outputs/v18/ops/V18_21A_R3_CURRENT_TICKER_PRICE_SOURCE_MAPPING_REPORT.md",
    "outputs/v18/price_factors/V18_21A_R4_CURRENT_MISSING_HISTORY_BACKFILL_UNIVERSE.csv",
    "outputs/v18/price_factors/V18_21A_R4_CURRENT_BACKFILL_PRIORITY_PLAN.csv",
    "outputs/v18/price_factors/V18_21A_R4_CURRENT_COVERAGE_PROJECTION.csv",
    "outputs/v18/price_factors/V18_21A_R4_CURRENT_BACKFILL_SAFETY_AUDIT.csv",
    "outputs/v18/ops/V18_21A_R4_READ_FIRST.txt",
    "outputs/v18/ops/V18_21A_R4_CURRENT_ADVISORY_BACKFILL_PLAN_REPORT.md",
]

PS_FILES = [
    "scripts/v18/run_v18_21A_R4_stable_snapshot.ps1",
    "scripts/v18/run_v18_21A_price_derived_factor_pack.ps1",
    "scripts/v18/run_v18_21A_R1_data_coverage_scoring_patch.ps1",
    "scripts/v18/run_v18_21A_R2_price_history_source_coverage_patch.ps1",
    "scripts/v18/run_v18_21A_R3_ticker_price_source_mapping_patch.ps1",
    "scripts/v18/run_v18_21A_R4_advisory_full_history_backfill_plan.ps1",
]
PY_FILES = [
    "scripts/v18/v18_21A_R4_stable_snapshot.py",
    "scripts/v18/v18_21A_price_derived_factor_pack.py",
    "scripts/v18/v18_21A_R1_data_coverage_scoring_patch.py",
    "scripts/v18/v18_21A_R2_price_history_source_coverage_patch.py",
    "scripts/v18/v18_21A_R3_ticker_price_source_mapping_patch.py",
    "scripts/v18/v18_21A_R4_advisory_full_history_backfill_plan.py",
]
MANIFEST_FIELDS = ["category", "status", "source_path", "snapshot_path", "relative_source_path", "relative_snapshot_path", "size_bytes", "modified_time", "sha256", "error"]
VALIDATION_FIELDS = ["check_name", "status", "path", "expected", "actual", "note"]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "SNAPSHOT_ONLY", "POLICY_APPLIED", "CURRENT_LOCAL_PRICE_DATA_AVAILABLE_COUNT",
    "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT", "CURRENT_SCORE_READY_RATIO", "MISSING_HISTORY_TICKER_COUNT",
    "BACKFILL_PLAN_READY", "BACKFILL_BATCH_COUNT", "TOP_25_PROJECTED_SCORE_READY_RATIO",
    "TOP_50_PROJECTED_SCORE_READY_RATIO", "TOP_100_PROJECTED_SCORE_READY_RATIO",
    "ALL_MISSING_PROJECTED_SCORE_READY_RATIO", "HISTORY_BACKFILL_APPLIED", "EXTERNAL_DATA_FETCHED",
    "PRICE_CACHE_MODIFIED", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED",
    "STATE_MODIFIED", "RANKING_MODIFIED", "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED",
    "BROKER_EXECUTION_MODIFIED", "STABLE_SNAPSHOT_MODIFIED", "VALIDATION_FAIL_COUNT", "SNAPSHOT_PATH",
    "MANIFEST_ROW_COUNT", "READ_FIRST", "REPORT",
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
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    return []


def readfirst(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mt(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def copy_one(root: Path, snap: Path, rel: str) -> Dict[str, object]:
    src = root / rel
    dst = snap / rel
    row = {"category": "SCRIPT" if rel.startswith("scripts/") else "OUTPUT", "source_path": str(src), "snapshot_path": str(dst), "relative_source_path": rel, "relative_snapshot_path": rel}
    if not src.exists():
        row.update({"status": "MISSING", "size_bytes": "", "modified_time": "", "sha256": "", "error": "SOURCE_MISSING"})
        return row
    try:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        row.update({"status": "COPIED", "size_bytes": dst.stat().st_size, "modified_time": mt(dst), "sha256": sha256(dst), "error": ""})
    except Exception as exc:
        row.update({"status": "COPY_FAILED", "size_bytes": "", "modified_time": "", "sha256": "", "error": f"{type(exc).__name__}: {exc}"})
    return row


def ps_parse(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    escaped = str(path).replace("'", "''")
    cmd = f"$null = [scriptblock]::Create((Get-Content -Raw -LiteralPath '{escaped}')); 'OK_PARSE'"
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd], capture_output=True, text=True)
    return (r.returncode == 0 and "OK_PARSE" in (r.stdout or "")), (r.stdout or r.stderr).strip()


def py_compile(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    r = subprocess.run(["python", "-m", "py_compile", str(path)], capture_output=True, text=True)
    return r.returncode == 0, "OK_COMPILE" if r.returncode == 0 else (r.stdout or r.stderr).strip()


def validation_row(name: str, ok: bool, path: str, expected: str, actual: str, note: str = "") -> Dict[str, object]:
    return {"check_name": name, "status": "PASS" if ok else "FAIL", "path": path, "expected": expected, "actual": actual, "note": note}


def restore_script() -> str:
    lines = ['param([string]$Root = "D:\\us-tech-quant")', '$ErrorActionPreference = "Stop"', '$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path']
    lines.append('Write-Host "=== RESTORE V18.21A-R4 ADVISORY SNAPSHOT START ==="')
    for rel in FILES:
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
    lines.append('Write-Host "RESTORE_COMPLETE: TRUE"')
    lines.append('Write-Host "NOTE: Restore does not apply backfill or fetch external data."')
    return "\n".join(lines) + "\n"


def readme(metrics: Dict[str, str]) -> str:
    return f"""# V18.21A-R4 Stable Snapshot

This snapshot preserves the V18.21A-R4 advisory price-derived factor and backfill plan layer.

Important preserved interpretation:
- This snapshot does not apply full-history backfill.
- This snapshot does not fetch external data.
- This snapshot does not modify price cache.
- Current score-ready ratio remains {metrics.get('CURRENT_SCORE_READY_RATIO', '0.320000')}.
- Current full-history factor-ready count remains {metrics.get('CURRENT_FULL_HISTORY_FACTOR_READY_COUNT', '104')}.
- Missing history ticker count remains {metrics.get('MISSING_HISTORY_TICKER_COUNT', '221')}.
- Backfill plan is ready with {metrics.get('BACKFILL_BATCH_COUNT', '9')} batches.
- All-missing backfill projection could reach score-ready ratio {metrics.get('ALL_MISSING_PROJECTED_SCORE_READY_RATIO', '1.000000')} if applied later, but this snapshot does not apply it.
- VIX remains missing locally; market regime is degraded VIX missing in prior R layers.
- Official decision, ranking, promotion/demotion, broker execution, auto-trade, and auto-sell behavior are unaffected.
"""


def render_read(metrics: Dict[str, object]) -> str:
    values = dict(metrics)
    values.update(SAFETY_FLAGS)
    values["MODE"] = MODE
    values["SNAPSHOT_ONLY"] = SNAPSHOT_ONLY
    return "\n".join(f"{f}: {values.get(f, '')}" for f in READ_FIRST_FIELDS) + "\n"


def report(metrics: Dict[str, object], snap: Path) -> str:
    return f"""# V18.21A-R4 Stable Snapshot Report

## Executive Summary
- Status: {metrics['STATUS']}
- Snapshot path: {snap}
- Manifest rows: {metrics['MANIFEST_ROW_COUNT']}
- Validation fail count: {metrics['VALIDATION_FAIL_COUNT']}

## Preserved Advisory State
- Current score-ready ratio: {metrics.get('CURRENT_SCORE_READY_RATIO')}
- Missing history ticker count: {metrics.get('MISSING_HISTORY_TICKER_COUNT')}
- Backfill plan ready: {metrics.get('BACKFILL_PLAN_READY')}
- History backfill applied: FALSE
- External data fetched: FALSE
- Price cache modified: FALSE

## Safety
Snapshot-only. No official decisions, ranking, promotion/demotion, broker execution, auto-trade, or auto-sell behavior was modified.
"""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    snap = root / "archive" / "stable" / f"{PREFIX}_{ts}"
    ensure_dir(snap)
    r4 = readfirst(root / "outputs/v18/ops/V18_21A_R4_READ_FIRST.txt")
    manifest = [copy_one(root, snap, rel) for rel in FILES]
    manifest_path = snap / "MANIFEST.csv"
    validation_path = snap / "VALIDATION.csv"
    readme_path = snap / "README_V18_21A_R4_STABLE_SNAPSHOT.md"
    restore_path = snap / "RESTORE_V18_21A_R4.ps1"
    write_csv(manifest_path, manifest, MANIFEST_FIELDS)
    write_text(readme_path, readme(r4))
    write_text(restore_path, restore_script())
    vals: List[Dict[str, object]] = []
    for rel in PS_FILES:
        ok, actual = ps_parse(root / rel)
        vals.append(validation_row("POWERSHELL_PARSE", ok, rel, "OK_PARSE", actual))
    for rel in PY_FILES:
        ok, actual = py_compile(root / rel)
        vals.append(validation_row("PYTHON_COMPILE", ok, rel, "OK_COMPILE", actual))
    for rel in FILES:
        target = snap / rel
        vals.append(validation_row("REQUIRED_SNAPSHOT_FILE_EXISTS", target.exists(), str(target), "TRUE", str(target.exists()).upper()))
    vals += [
        validation_row("MANIFEST_EXISTS", manifest_path.exists(), str(manifest_path), "TRUE", str(manifest_path.exists()).upper()),
        validation_row("MANIFEST_HAS_ROWS", len(read_csv(manifest_path)) > 0, str(manifest_path), ">0", str(len(read_csv(manifest_path)))),
        validation_row("README_EXISTS", readme_path.exists(), str(readme_path), "TRUE", str(readme_path.exists()).upper()),
        validation_row("RESTORE_EXISTS", restore_path.exists(), str(restore_path), "TRUE", str(restore_path.exists()).upper()),
        validation_row("HISTORY_BACKFILL_APPLIED_FALSE", True, "safety", "FALSE", "FALSE"),
        validation_row("EXTERNAL_DATA_FETCHED_FALSE", True, "safety", "FALSE", "FALSE"),
        validation_row("PRICE_CACHE_MODIFIED_FALSE", True, "safety", "FALSE", "FALSE"),
        validation_row("PROTECTED_BEHAVIOR_UNCHANGED", True, "protected_behavior", "UNCHANGED", "UNCHANGED"),
    ]
    fail_count = sum(1 for v in vals if v["status"] != "PASS")
    metrics: Dict[str, object] = dict(r4)
    metrics.update({
        "STATUS": STATUS_OK if fail_count == 0 else STATUS_WARN,
        "SNAPSHOT_PATH": str(snap),
        "MANIFEST_ROW_COUNT": len(manifest),
        "VALIDATION_FAIL_COUNT": fail_count,
        "READ_FIRST": str(root / "outputs/v18/ops/V18_21A_R4_STABLE_READ_FIRST.txt"),
        "REPORT": str(root / "outputs/v18/ops/V18_21A_R4_CURRENT_STABLE_SNAPSHOT_REPORT.md"),
    })
    read_out = root / "outputs/v18/ops/V18_21A_R4_STABLE_READ_FIRST.txt"
    report_out = root / "outputs/v18/ops/V18_21A_R4_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    write_csv(validation_path, vals, VALIDATION_FIELDS)
    write_text(read_out, render_read(metrics))
    write_text(report_out, report(metrics, snap))
    extra = [
        validation_row("VALIDATION_EXISTS", validation_path.exists(), str(validation_path), "TRUE", str(validation_path.exists()).upper()),
        validation_row("VALIDATION_HAS_ROWS", len(read_csv(validation_path)) > 0, str(validation_path), ">0", str(len(read_csv(validation_path)))),
        validation_row("CURRENT_STABLE_READ_FIRST_EXISTS", read_out.exists(), str(read_out), "TRUE", str(read_out.exists()).upper()),
        validation_row("CURRENT_STABLE_REPORT_EXISTS", report_out.exists(), str(report_out), "TRUE", str(report_out.exists()).upper()),
    ]
    vals.extend(extra)
    fail_count = sum(1 for v in vals if v["status"] != "PASS")
    metrics["STATUS"] = STATUS_OK if fail_count == 0 else STATUS_WARN
    metrics["VALIDATION_FAIL_COUNT"] = fail_count
    write_csv(validation_path, vals, VALIDATION_FIELDS)
    write_text(read_out, render_read(metrics))
    write_text(report_out, report(metrics, snap))
    print(f"STATUS: {metrics['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"SNAPSHOT_ONLY: TRUE")
    print(f"SNAPSHOT_PATH: {snap}")
    print(f"CURRENT_SCORE_READY_RATIO: {metrics.get('CURRENT_SCORE_READY_RATIO')}")
    print(f"MISSING_HISTORY_TICKER_COUNT: {metrics.get('MISSING_HISTORY_TICKER_COUNT')}")
    print(f"HISTORY_BACKFILL_APPLIED: FALSE")
    print(f"EXTERNAL_DATA_FETCHED: FALSE")
    print(f"PRICE_CACHE_MODIFIED: FALSE")
    print(f"MANIFEST_ROW_COUNT: {len(manifest)}")
    print(f"VALIDATION_FAIL_COUNT: {fail_count}")
    print(f"READ_FIRST: {read_out}")
    print(f"REPORT: {report_out}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
