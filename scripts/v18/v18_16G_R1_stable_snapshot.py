from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_16G_R1_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_16G_R1_STABLE_SNAPSHOT_VALIDATION_FAILED"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
SNAPSHOT_ONLY = "TRUE"
SNAPSHOT_PREFIX = "V18_16G_R1_stable_run_triggered_rolling_universe_scan"

CRITICAL_FILES = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/run_v18_16F_current_daily_with_rolling_universe_scan.ps1",
    "scripts/v18/v18_16F_current_daily_with_rolling_universe_scan.py",
    "outputs/v18/ops/V18_16F_READ_FIRST.txt",
    "outputs/v18/read_center/V18_16F_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN.md",
    "outputs/v18/ops/V18_16F_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN_SUMMARY.csv",
    "outputs/v18/ops/V18_16F_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN_INPUT_AUDIT.csv",
    "scripts/v18/run_v18_16A_universe_rolling_state_builder.ps1",
    "scripts/v18/v18_16A_universe_rolling_state_builder.py",
    "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
    "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv",
    "outputs/v18/universe/V18_16A_CURRENT_UNIVERSE_ROLLING_STATE_AUDIT.csv",
    "outputs/v18/universe/V18_16A_CURRENT_UNIVERSE_ROLLING_STATE_REPORT.md",
    "outputs/v18/ops/V18_16A_READ_FIRST.txt",
    "state/v18/universe/V18_MANUAL_UNIVERSE_ADDITIONS.csv",
    "outputs/v18/universe/V18_16A_P1_CURRENT_MANUAL_UNIVERSE_ADDITION_AUDIT.csv",
    "outputs/v18/ops/V18_16A_P1_READ_FIRST.txt",
    "scripts/v18/run_v18_16B_rolling_scan_scheduler.ps1",
    "scripts/v18/v18_16B_rolling_scan_scheduler.py",
    "outputs/v18/universe/V18_16B_CURRENT_ROLLING_SCAN_PLAN.csv",
    "outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv",
    "outputs/v18/universe/V18_16B_CURRENT_ROLLING_SCAN_SCHEDULER_REPORT.md",
    "outputs/v18/ops/V18_16B_READ_FIRST.txt",
    "scripts/v18/run_v18_16C_scan_scoped_data_update.ps1",
    "scripts/v18/v18_16C_scan_scoped_data_update.py",
    "outputs/v18/data/V18_16C_CURRENT_SCAN_SCOPED_PRICE_UPDATE_AUDIT.csv",
    "outputs/v18/risk/V18_16C_CURRENT_SCAN_SCOPED_EVENT_UPDATE_AUDIT.csv",
    "outputs/v18/universe/V18_16C_CURRENT_SCAN_SCOPED_DATA_UPDATE_SUMMARY.csv",
    "outputs/v18/universe/V18_16C_CURRENT_SCAN_SCOPED_DATA_UPDATE_REPORT.md",
    "outputs/v18/ops/V18_16C_READ_FIRST.txt",
    "outputs/v18/data/V18_16C_P1_SCOPED_YFINANCE_SMOKE_PRICE_AUDIT.csv",
    "outputs/v18/ops/V18_16C_P1_READ_FIRST.txt",
    "outputs/v18/data/V18_16C_P2_YFINANCE_CACHE_REPAIR_PRICE_AUDIT.csv",
    "outputs/v18/ops/V18_16C_P2_READ_FIRST.txt",
    "outputs/v18/data/V18_16C_P3_LOCAL_PRICE_SOURCE_DISCOVERY.csv",
    "outputs/v18/data/V18_16C_P3_LOCAL_CACHE_BOOTSTRAP_AUDIT.csv",
    "outputs/v18/ops/V18_16C_P3_READ_FIRST.txt",
    "scripts/v18/run_v18_16D_priority_based_light_scanner.ps1",
    "scripts/v18/v18_16D_priority_based_light_scanner.py",
    "outputs/v18/universe/V18_16D_CURRENT_PRIORITY_LIGHT_SCAN_RESULT.csv",
    "outputs/v18/universe/V18_CURRENT_PRIORITY_LIGHT_SCAN_RESULT.csv",
    "outputs/v18/universe/V18_16D_CURRENT_PRIORITY_LIGHT_SCAN_REPORT.md",
    "outputs/v18/ops/V18_16D_READ_FIRST.txt",
    "outputs/v18/ops/V18_CURRENT_PRIORITY_LIGHT_SCAN_READ_FIRST.txt",
    "scripts/v18/run_v18_16E_promotion_demotion_engine.ps1",
    "scripts/v18/v18_16E_promotion_demotion_engine.py",
    "outputs/v18/universe/V18_16E_CURRENT_PROMOTION_DEMOTION_AUDIT.csv",
    "outputs/v18/universe/V18_CURRENT_PROMOTION_DEMOTION_AUDIT.csv",
    "outputs/v18/universe/V18_16E_CURRENT_PROMOTION_DEMOTION_REPORT.md",
    "outputs/v18/ops/V18_16E_READ_FIRST.txt",
    "outputs/v18/ops/V18_CURRENT_PROMOTION_DEMOTION_READ_FIRST.txt",
    "scripts/v18/run_v18_14C_ranked_candidate_forward_tracker.ps1",
    "scripts/v18/v18_14C_ranked_candidate_forward_tracker.py",
    "scripts/v18/run_v18_14D_ranked_candidate_forward_price_filler.ps1",
    "scripts/v18/v18_14D_ranked_candidate_forward_price_filler.py",
    "scripts/v18/run_v18_14E_current_daily_with_forward_tracker.ps1",
    "scripts/v18/v18_14E_current_daily_with_forward_tracker.py",
    "scripts/v18/run_v18_15A_manual_position_trade_feedback.ps1",
    "scripts/v18/v18_15A_manual_position_trade_feedback.py",
    "scripts/v18/run_v18_15B_current_daily_with_manual_feedback.ps1",
    "scripts/v18/v18_15B_current_daily_with_manual_feedback.py",
    "state/v18/manual/V18_MANUAL_POSITIONS.csv",
    "state/v18/manual/V18_MANUAL_TRADE_LOG.csv",
    "scripts/v18/run_v18_15C_predevelopment_program_audit.ps1",
    "scripts/v18/v18_15C_predevelopment_program_audit.py",
    "outputs/v18/ops/V18_15C_READ_FIRST.txt",
    "outputs/v18/ops/V18_15C_CURRENT_PREDEVELOPMENT_PROGRAM_AUDIT_REPORT.md",
    "outputs/v18/ops/V18_15C_CURRENT_RANKING_FACTOR_LINEAGE_AUDIT.csv",
    "scripts/v18/run_v18_16G_R1_stable_snapshot.ps1",
    "scripts/v18/v18_16G_R1_stable_snapshot.py",
]

DIRS_TO_COPY = [
    "state/v18/provider_cache/yfinance",
    "state/v18/price_cache",
]

PS_PARSE = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/run_v18_16A_universe_rolling_state_builder.ps1",
    "scripts/v18/run_v18_16B_rolling_scan_scheduler.ps1",
    "scripts/v18/run_v18_16C_scan_scoped_data_update.ps1",
    "scripts/v18/run_v18_16D_priority_based_light_scanner.ps1",
    "scripts/v18/run_v18_16E_promotion_demotion_engine.ps1",
    "scripts/v18/run_v18_16F_current_daily_with_rolling_universe_scan.ps1",
    "scripts/v18/run_v18_16G_R1_stable_snapshot.ps1",
]

PY_COMPILE = [
    "scripts/v18/v18_16A_universe_rolling_state_builder.py",
    "scripts/v18/v18_16B_rolling_scan_scheduler.py",
    "scripts/v18/v18_16C_scan_scoped_data_update.py",
    "scripts/v18/v18_16D_priority_based_light_scanner.py",
    "scripts/v18/v18_16E_promotion_demotion_engine.py",
    "scripts/v18/v18_16F_current_daily_with_rolling_universe_scan.py",
    "scripts/v18/v18_16G_R1_stable_snapshot.py",
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
            pass
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(base: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def first_value(path: Path, key: str) -> str:
    target = key.upper()
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        if k.strip().upper().lstrip("- ").strip() == target:
            return v.strip()
    return ""


def stable_baseline(root: Path) -> Dict[str, Tuple[float, str]]:
    base = root / "archive/stable"
    out: Dict[str, Tuple[float, str]] = {}
    if not base.exists():
        return out
    for folder in base.iterdir():
        if folder.is_dir():
            manifest = folder / "MANIFEST.csv"
            out[str(folder.resolve())] = (folder.stat().st_mtime, sha256(manifest))
    return out


def stable_modified(before: Dict[str, Tuple[float, str]], root: Path, new_snapshot: Path) -> bool:
    after = stable_baseline(root)
    new_key = str(new_snapshot.resolve())
    for key, value in before.items():
        if key == new_key:
            continue
        if after.get(key) != value:
            return True
    return False


def parse_ps(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    ps_path = str(path.resolve()).replace("'", "''")
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f"$p='{ps_path}'; $t=$null; $e=$null; [System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$e) > $null; if ($e.Count -gt 0) {{ $e | ForEach-Object {{ $_.Message }}; exit 1 }}"]
    proc = subprocess.run(command, text=True, capture_output=True, timeout=60)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def compile_py(path: Path) -> Tuple[bool, str]:
    try:
        ast.parse(read_text(path), filename=str(path))
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def dangerous_hits(paths: Iterable[Path], root: Path) -> List[str]:
    tokens = ["BUY_NOW", "SELL_NOW", "EXECUTE_LIVE_ORDER", "LIVE_TRADE", "LIVE_SELL"]
    hits: List[str] = []
    for path in paths:
        text = read_text(path)
        in_token_block = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            upper = line.upper()
            stripped = upper.strip()
            if "TOKENS =" in upper or "DANGEROUS" in upper:
                in_token_block = True
            safe = "DISABLED" in upper or "DO NOT" in upper or "TOKEN" in upper or "HITS.APPEND" in upper or " IN UPPER" in upper or in_token_block
            for token in tokens:
                if token in upper and not safe:
                    hits.append(f"{path}:{line_no}:{token}")
            if "AUTO_TRADE" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{path}:{line_no}:AUTO_TRADE_ENABLED")
            if "AUTO_SELL" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{path}:{line_no}:AUTO_SELL_ENABLED")
            if in_token_block and (stripped.endswith("]") or stripped.endswith(")")):
                in_token_block = False
    return hits


def manifest_row(root: Path, snapshot: Path, src: Path, dst: Path, category: str, status: str, error: str = "") -> Dict[str, object]:
    size = ""
    digest = ""
    modified = ""
    if dst.exists() and dst.is_file():
        stat = dst.stat()
        size = stat.st_size
        digest = sha256(dst)
        modified = dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    return {
        "category": category, "status": status, "required": "YES", "source_path": str(src),
        "snapshot_path": str(dst), "relative_source_path": rel(root, src),
        "relative_snapshot_path": rel(snapshot, dst), "size_bytes": size,
        "last_write_time": modified, "sha256": digest, "error": error,
    }


def copy_file(root: Path, snapshot: Path, rel_path: str, category: str = "critical") -> Dict[str, object]:
    src = root / rel_path
    dst = snapshot / rel_path
    if not src.exists() or not src.is_file():
        return manifest_row(root, snapshot, src, dst, category, "MISSING_CRITICAL", "Source file missing")
    try:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        return manifest_row(root, snapshot, src, dst, category, "COPIED")
    except Exception as exc:
        return manifest_row(root, snapshot, src, dst, category, "COPY_FAIL", f"{type(exc).__name__}: {exc}")


def copy_dir(root: Path, snapshot: Path, rel_dir: str) -> List[Dict[str, object]]:
    src_dir = root / rel_dir
    rows: List[Dict[str, object]] = []
    if not src_dir.exists():
        return rows
    for src in sorted(p for p in src_dir.rglob("*") if p.is_file()):
        rel_path = rel(root, src)
        rows.append(copy_file(root, snapshot, rel_path, "cache_directory"))
    return rows


def run_validation(root: Path, label: str, args: Sequence[str]) -> Dict[str, object]:
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root / "scripts/v18/run_v18_current_daily_command_center.ps1"), *args]
    proc = subprocess.run(command, cwd=str(root), text=True, capture_output=True, timeout=900)
    return {
        "check_name": label,
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "path": " ".join(command),
        "expected": "exit0",
        "actual": f"exit={proc.returncode}",
        "note": "\n".join((proc.stdout + proc.stderr).splitlines()[-12:]),
    }


def build_restore_script(snapshot: Path) -> str:
    file_lines = ",\n".join(f'    "{p}"' for p in CRITICAL_FILES if p.startswith("scripts/") or p.startswith("state/v18/universe") or p.startswith("state/v18/manual"))
    return f'''param(
    [string]$Root = "D:\\us-tech-quant",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$Snapshot = "{snapshot}"
Write-Host "=== V18.16G-R1 STABLE SNAPSHOT RESTORE ==="
Write-Host "SNAPSHOT: $Snapshot"
Write-Host "ROOT: $Root"
Write-Host "APPLY: $Apply"
Write-Host "SNAPSHOT_ONLY: TRUE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
if (-not (Test-Path -LiteralPath $Snapshot)) {{ throw "MISSING_SNAPSHOT: $Snapshot" }}
$Files = @(
{file_lines}
)
foreach ($File in $Files) {{
    $Src = Join-Path $Snapshot $File
    $Dst = Join-Path $Root $File
    if (Test-Path -LiteralPath $Src) {{
        Write-Host "RESTORE_FILE: $File"
        if ($Apply) {{
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dst) | Out-Null
            Copy-Item -LiteralPath $Src -Destination $Dst -Force
        }}
    }}
}}
if (-not $Apply) {{ Write-Host "DRYRUN_ONLY. Re-run with -Apply to restore." }}
'''


def build(root: Path) -> int:
    root = root.resolve()
    before_stable = stable_baseline(root)
    snapshot = root / "archive/stable" / f"{SNAPSHOT_PREFIX}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ensure_dir(snapshot)
    ops = root / "outputs/v18/ops"
    ensure_dir(ops)
    read_first_path = ops / "V18_16G_R1_READ_FIRST.txt"
    report_path = ops / "V18_16G_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_16G_R1_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_16G_R1.ps1"

    validations: List[Dict[str, object]] = []
    validations.append(run_validation(root, "OLD_DEFAULT_MODE", []))
    validations.append(run_validation(root, "OLD_FORWARD_MANUAL_MODE", ["-RunForwardTracker", "-RunManualFeedback"]))
    validations.append(run_validation(root, "ROLLING_SCAN_INTEGRATION_MODE", ["-RunUniverseRollingScan", "-RunForwardTracker", "-RunManualFeedback"]))
    for rel_path in PS_PARSE:
        ok, note = parse_ps(root / rel_path)
        validations.append({"check_name": f"POWERSHELL_PARSE_{Path(rel_path).name}", "status": "PASS" if ok else "FAIL", "path": rel_path, "expected": "parse_ok", "actual": "parse_ok" if ok else "parse_fail", "note": note})
    for rel_path in PY_COMPILE:
        ok, note = compile_py(root / rel_path)
        validations.append({"check_name": f"PY_COMPILE_{Path(rel_path).name}", "status": "PASS" if ok else "FAIL", "path": rel_path, "expected": "compile_ok", "actual": "compile_ok" if ok else "compile_fail", "note": note})

    manifest_rows = [copy_file(root, snapshot, p) for p in CRITICAL_FILES]
    for d in DIRS_TO_COPY:
        manifest_rows.extend(copy_dir(root, snapshot, d))
    write_text(restore_path, build_restore_script(snapshot))
    write_text(readme_path, f"# V18.16G-R1 Stable Snapshot\n\nCreated: {dt.datetime.now().isoformat(timespec='seconds')}\n\nSnapshot: {snapshot}\n\nRun-triggered rolling universe scan integration stable point.\n\nAUTO_TRADE: {AUTO_TRADE}\nAUTO_SELL: {AUTO_SELL}\nOFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}\nSNAPSHOT_ONLY: {SNAPSHOT_ONLY}\n")
    manifest_rows.append(manifest_row(root, snapshot, readme_path, readme_path, "snapshot_metadata", "COPIED"))
    manifest_rows.append(manifest_row(root, snapshot, restore_path, restore_path, "snapshot_metadata", "COPIED"))

    write_csv(validation_path, validations, ["check_name", "status", "path", "expected", "actual", "note"])
    manifest_rows.append(manifest_row(root, snapshot, validation_path, validation_path, "snapshot_metadata", "COPIED"))
    write_csv(manifest_path, manifest_rows, ["category", "status", "required", "source_path", "snapshot_path", "relative_source_path", "relative_snapshot_path", "size_bytes", "last_write_time", "sha256", "error"])
    manifest_rows.append(manifest_row(root, snapshot, manifest_path, manifest_path, "snapshot_metadata", "COPIED"))
    write_csv(manifest_path, manifest_rows, ["category", "status", "required", "source_path", "snapshot_path", "relative_source_path", "relative_snapshot_path", "size_bytes", "last_write_time", "sha256", "error"])

    stable_protection = "PASS" if not stable_modified(before_stable, root, snapshot) else "FAIL"
    dangerous = dangerous_hits([root / p for p in PS_PARSE + PY_COMPILE] + [readme_path, restore_path], root)
    copied = sum(1 for r in manifest_rows if r["status"] == "COPIED")
    copy_fail = sum(1 for r in manifest_rows if r["status"] == "COPY_FAIL")
    missing = sum(1 for r in manifest_rows if r["status"] == "MISSING_CRITICAL")
    ps_fail = sum(1 for v in validations if str(v["check_name"]).startswith("POWERSHELL_PARSE") and v["status"] != "PASS")
    py_fail = sum(1 for v in validations if str(v["check_name"]).startswith("PY_COMPILE") and v["status"] != "PASS")
    runtime_fail = sum(1 for v in validations if str(v["check_name"]) in {"OLD_DEFAULT_MODE", "OLD_FORWARD_MANUAL_MODE", "ROLLING_SCAN_INTEGRATION_MODE"} and v["status"] != "PASS")
    v16f = root / "outputs/v18/ops/V18_16F_READ_FIRST.txt"
    validation_fail = copy_fail + missing + ps_fail + py_fail + runtime_fail + len(dangerous) + (0 if stable_protection == "PASS" else 1)
    values = {
        "STATUS": STATUS_OK if validation_fail == 0 else STATUS_WARN,
        "SNAPSHOT_PATH": str(snapshot),
        "COPIED_FILE_COUNT": str(copied),
        "COPY_FAIL_COUNT": str(copy_fail),
        "MISSING_CRITICAL_COUNT": str(missing),
        "POWERSHELL_PARSE_PASS_COUNT": str(sum(1 for v in validations if str(v["check_name"]).startswith("POWERSHELL_PARSE") and v["status"] == "PASS")),
        "POWERSHELL_PARSE_FAIL_COUNT": str(ps_fail),
        "PYTHON_COMPILE_PASS_COUNT": str(sum(1 for v in validations if str(v["check_name"]).startswith("PY_COMPILE") and v["status"] == "PASS")),
        "PYTHON_COMPILE_FAIL_COUNT": str(py_fail),
        "RUNTIME_VALIDATION_RUN_COUNT": "3",
        "RUNTIME_VALIDATION_FAIL_COUNT": str(runtime_fail),
        "ROLLING_SCAN_INTEGRATION_VALIDATED": str(any(v["check_name"] == "ROLLING_SCAN_INTEGRATION_MODE" and v["status"] == "PASS" for v in validations)).upper(),
        "OLD_DEFAULT_MODE_VALIDATED": str(any(v["check_name"] == "OLD_DEFAULT_MODE" and v["status"] == "PASS" for v in validations)).upper(),
        "OLD_FORWARD_MANUAL_MODE_VALIDATED": str(any(v["check_name"] == "OLD_FORWARD_MANUAL_MODE" and v["status"] == "PASS" for v in validations)).upper(),
        "TOTAL_UNIVERSE_COUNT": first_value(v16f, "TOTAL_UNIVERSE_COUNT"),
        "TODAY_ROLLING_SCAN_COUNT": first_value(v16f, "TODAY_ROLLING_SCAN_COUNT"),
        "SCANNED_TICKER_COUNT": first_value(v16f, "SCANNED_TICKER_COUNT"),
        "CORE_DAILY_COUNT": first_value(v16f, "CORE_DAILY_COUNT"),
        "CANDIDATE_COUNT": first_value(v16f, "CANDIDATE_COUNT"),
        "STRONG_WATCH_COUNT": first_value(v16f, "STRONG_WATCH_COUNT"),
        "WATCHLIST_COUNT": first_value(v16f, "WATCHLIST_COUNT"),
        "RESEARCH_COUNT": first_value(v16f, "RESEARCH_COUNT"),
        "DANGEROUS_TOKEN_FINDING_COUNT": str(len(dangerous)),
        "STABLE_SNAPSHOT_PROTECTION_STATUS": stable_protection,
        "VALIDATION_FAIL_COUNT": str(validation_fail),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "SNAPSHOT_ONLY": SNAPSHOT_ONLY,
    }
    keys = list(values.keys())
    write_text(read_first_path, "\n".join(f"{k}: {values[k]}" for k in keys) + "\n")
    report = ["# V18.16G-R1 Stable Snapshot", "", *[f"- {k}: {values[k]}" for k in keys], "", "## Validation", "", *[f"- {v['check_name']}: {v['status']} {v.get('note', '')}" for v in validations[:20]], "", f"- MANIFEST: {manifest_path}", f"- VALIDATION: {validation_path}", f"- RESTORE_SCRIPT: {restore_path}"]
    write_text(report_path, "\n".join(report) + "\n")
    for key in ["STATUS", "SNAPSHOT_PATH", "COPIED_FILE_COUNT", "COPY_FAIL_COUNT", "MISSING_CRITICAL_COUNT", "ROLLING_SCAN_INTEGRATION_VALIDATED", "OLD_DEFAULT_MODE_VALIDATED", "OLD_FORWARD_MANUAL_MODE_VALIDATED", "TOTAL_UNIVERSE_COUNT", "TODAY_ROLLING_SCAN_COUNT", "SCANNED_TICKER_COUNT", "CORE_DAILY_COUNT", "CANDIDATE_COUNT", "STRONG_WATCH_COUNT", "WATCHLIST_COUNT", "RESEARCH_COUNT", "VALIDATION_FAIL_COUNT", "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT"]:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
