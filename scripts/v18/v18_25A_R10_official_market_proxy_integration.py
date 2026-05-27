from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R10_OFFICIAL_MARKET_PROXY_INTEGRATION_READY"
STATUS_WARN = "WARN_V18_25A_R10_OFFICIAL_MARKET_PROXY_INTEGRATION_READY"
STATUS_FAIL = "FAIL_V18_25A_R10_OFFICIAL_MARKET_PROXY_INTEGRATION"
MODE = "OFFICIAL_MARKET_PROXY_INTEGRATION_WITH_BACKUP"

R9_READ_FIRST = "outputs/v18/ops/V18_25A_R9_READ_FIRST.txt"
R9_GATE = "outputs/v18/degraded_daily_review/V18_25A_R9_CURRENT_PROMOTION_GATE_DECISION.csv"
R9_QUALITY = "outputs/v18/degraded_daily_review/V18_25A_R9_CURRENT_STAGED_VIX_QUALITY_AUDIT.csv"
STAGED_VIX = "data/v18/staged_market_proxy/V18_25A_R8_VIX/V18_25A_R8_VIX_NORMALIZED.csv"
STAGED_MANIFEST = "data/v18/staged_market_proxy/V18_25A_R8_VIX/MANIFEST.csv"
OFFICIAL_VIX = "state/v18/market_proxy_cache/VIX.csv"
BACKUP_ROOT = "archive/v18/market_proxy_backups"

OUT_DEGRADED = "outputs/v18/degraded_daily_review"
OUT_OPS = "outputs/v18/ops"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R9_SOURCE_PATH",
    "STAGED_VIX_SOURCE_PATH",
    "OFFICIAL_MARKET_PROXY_PATH",
    "BACKUP_DIR",
    "RESTORE_SCRIPT_PATH",
    "R9_PROMOTION_GATE_DECISION",
    "INTEGRATION_ATTEMPTED",
    "INTEGRATION_SUCCESS",
    "ROW_COUNT_STAGED",
    "ROW_COUNT_OFFICIAL",
    "MIN_DATE",
    "MAX_DATE",
    "LATEST_DATE",
    "CLOSE_COLUMN_AVAILABLE",
    "CLOSE_NON_NULL_COUNT",
    "FULL_HISTORY_READY",
    "USABLE_FOR_FACTOR_REFRESH",
    "USABLE_FOR_TECHNICAL_OVERLAY",
    "QUALITY_STATUS",
    "OFFICIAL_MARKET_PROXY_MODIFIED",
    "OFFICIAL_PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_STOCK_BACKFILL_MODIFIED",
    "STAGED_MARKET_PROXY_MODIFIED",
    "LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_MIGRATION_MODIFIED",
    "DEGRADED_DAILY_MODIFIED",
    "OFFICIAL_DAILY_DECISION_MODIFIED",
    "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE",
    "AUTO_SELL",
    "BACKTEST_EXECUTED",
    "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_FILE_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]

PLAN_FIELDS = ["plan_item", "path", "status", "notes"]
RESULT_FIELDS = ["result_item", "value", "notes"]
BACKUP_FIELDS = ["backup_item", "path", "status", "notes"]
QUALITY_FIELDS = ["metric", "value", "notes"]

FALSE_SAFETY = {
    "OFFICIAL_PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_MODIFIED": "FALSE",
    "STAGED_STOCK_BACKFILL_MODIFIED": "FALSE",
    "STAGED_MARKET_PROXY_MODIFIED": "FALSE",
    "LEDGER_MODIFIED": "FALSE",
    "FACTOR_PACK_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "TIER_MIGRATION_MODIFIED": "FALSE",
    "DEGRADED_DAILY_MODIFIED": "FALSE",
    "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "BACKTEST_EXECUTED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except csv.Error:
            continue
    return [], []


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def parse_read_first(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def lookup_rows(rows: Sequence[Dict[str, str]], key_col: str, value_col: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for row in rows:
        key = str(row.get(key_col, "")).strip()
        if key:
            out[key] = str(row.get(value_col, "")).strip()
    return out


def truthy(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "OK", "YES", "1"}


def parse_date(value: object) -> Optional[dt.date]:
    text = str(value or "").strip()[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def number_value(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip().replace(",", "")
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def protected_files(root: Path) -> List[Path]:
    rels = [
        "state/v18/price_cache",
        "data/v18/price_history",
        "data/v18/staged_backfill",
        "state/v18/rolling_coverage",
        "outputs/v18/factor_pack",
        "outputs/v18/ranking",
        "outputs/v18/technical_timing",
        "outputs/v18/tier_migration",
        "outputs/v18/official_daily_decision",
        "outputs/v18/daily_decision",
        "state/v18/official_daily_decision",
        STAGED_VIX,
        STAGED_MANIFEST,
        R9_READ_FIRST,
        R9_GATE,
        R9_QUALITY,
    ]
    out: List[Path] = []
    for rel in rels:
        base = root / rel
        if base.exists():
            if base.is_file():
                out.append(base)
            else:
                out.extend(path for path in base.rglob("*") if path.is_file())
    return out


def changed_forbidden_files(root: Path, before: Dict[str, Tuple[int, int]]) -> List[str]:
    after = {str(path): file_sig(path) for path in protected_files(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig)
    changed.extend(sorted(path for path in after if path not in before))
    return changed


def normalize_staged_rows(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> List[Dict[str, object]]:
    lower = {field.lower(): field for field in fields}
    date_col = lower.get("date", "")
    out_by_date: Dict[str, Dict[str, object]] = {}
    for row in rows:
        parsed = parse_date(row.get(date_col, "")) if date_col else None
        if parsed is None:
            continue
        item = {
            "date": parsed.isoformat(),
            "open": row.get(lower.get("open", ""), ""),
            "high": row.get(lower.get("high", ""), ""),
            "low": row.get(lower.get("low", ""), ""),
            "close": row.get(lower.get("close", ""), ""),
            "adj_close": row.get(lower.get("adj_close", ""), ""),
            "volume": row.get(lower.get("volume", ""), ""),
            "proxy_symbol": row.get(lower.get("proxy_symbol", ""), ""),
            "source": row.get(lower.get("source", ""), ""),
        }
        out_by_date[item["date"]] = item
    return [out_by_date[key] for key in sorted(out_by_date)]


def audit_rows(rows: Sequence[Dict[str, object]]) -> Dict[str, str]:
    dates = [str(row.get("date", "")) for row in rows if row.get("date")]
    close_values = [number_value(row.get("close")) for row in rows]
    close_non_null = sum(1 for value in close_values if value is not None)
    close_available = any("close" in row for row in rows)
    negative_or_zero = sum(1 for value in close_values if value is not None and value <= 0)
    duplicate_count = len(dates) - len(set(dates))
    full_history_ready = len(rows) >= 252 and close_available and close_non_null == len(rows) and negative_or_zero == 0 and duplicate_count == 0
    usable_factor = full_history_ready
    usable_technical = full_history_ready
    quality = "OK" if full_history_ready else "WARN" if rows and close_available else "FAIL"
    return {
        "row_count": str(len(rows)),
        "min_date": min(dates) if dates else "",
        "max_date": max(dates) if dates else "",
        "latest_date": max(dates) if dates else "",
        "close_column_available": str(close_available).upper(),
        "close_non_null_count": str(close_non_null),
        "duplicate_date_count": str(duplicate_count),
        "negative_or_zero_close_count": str(negative_or_zero),
        "full_history_ready": str(full_history_ready).upper(),
        "usable_for_factor_refresh": str(usable_factor).upper(),
        "usable_for_technical_overlay": str(usable_technical).upper(),
        "quality_status": quality,
    }


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def render_restore_script(root: Path, official_path: Path, backup_file: Path, existed_before: bool) -> str:
    official = str(official_path)
    backup = str(backup_file)
    if existed_before:
        action = f"""if (-not (Test-Path -LiteralPath "{backup}")) {{
    throw "Backup file missing: {backup}"
}}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent "{official}") | Out-Null
Copy-Item -LiteralPath "{backup}" -Destination "{official}" -Force
Write-Host "RESTORED: {official}"
"""
    else:
        action = f"""if (Test-Path -LiteralPath "{official}") {{
    Remove-Item -LiteralPath "{official}" -Force
    Write-Host "REMOVED_NEW_FILE: {official}"
}} else {{
    Write-Host "NO_FILE_TO_REMOVE: {official}"
}}
"""
    return f"""$ErrorActionPreference = "Stop"
Write-Host "===== RESTORE V18.25A-R10 MARKET PROXY START ====="
Write-Host "ROOT: {root}"
Write-Host "OFFICIAL_MARKET_PROXY_PATH: {official}"
Write-Host "EXISTED_BEFORE_INTEGRATION: {str(existed_before).upper()}"
{action}Write-Host "===== RESTORE V18.25A-R10 MARKET PROXY END ====="
"""


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.25A-R10 Official Market Proxy Integration With Backup

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

Status: {values['STATUS']}

Mode: {MODE}

Official market proxy path: `{values['OFFICIAL_MARKET_PROXY_PATH']}`

Backup directory: `{values['BACKUP_DIR']}`

Restore script: `{values['RESTORE_SCRIPT_PATH']}`

Rows integrated: staged={values['ROW_COUNT_STAGED']}, official={values['ROW_COUNT_OFFICIAL']}

Date range: {values['MIN_DATE']} to {values['MAX_DATE']}

Quality status: {values['QUALITY_STATUS']}

Safety: no external fetch, no stock price cache write, no official stock price history write, no rolling ledger/factor/technical/tier/decision/trading permission changes. OFFICIAL_DECISION_IMPACT remains NONE.

Next step: {values['NEXT_RECOMMENDED_STEP']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    script_path = root / "scripts/v18/v18_25A_R10_official_market_proxy_integration.py"
    wrapper_path = root / "scripts/v18/run_v18_25A_R10_official_market_proxy_integration.ps1"
    staged_path = root / STAGED_VIX
    official_path = root / OFFICIAL_VIX
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root / BACKUP_ROOT / f"V18_25A_R10_{timestamp}"
    backup_file = backup_dir / "VIX.csv.before_V18_25A_R10"
    restore_path = backup_dir / "RESTORE_V18_25A_R10_MARKET_PROXY.ps1"
    backup_manifest_path = backup_dir / "BACKUP_MANIFEST.csv"

    before = {str(path): file_sig(path) for path in protected_files(root)}

    r9_values = parse_read_first(root / R9_READ_FIRST)
    gate_rows, _ = read_csv(root / R9_GATE)
    gate_lookup = lookup_rows(gate_rows, "decision_item", "value")
    quality_rows, _ = read_csv(root / R9_QUALITY)
    quality_lookup = lookup_rows(quality_rows, "metric", "value")
    staged_rows_raw, staged_fields = read_csv(staged_path)
    staged_rows = normalize_staged_rows(staged_rows_raw, staged_fields)
    staged_audit = audit_rows(staged_rows)

    r9_gate = gate_lookup.get("promotion_gate_decision", r9_values.get("PROMOTION_GATE_DECISION", ""))
    preconditions = {
        "r9_status_ok": r9_values.get("STATUS", "").startswith("OK_"),
        "r9_promotion_ready": r9_gate == "PROMOTE_READY",
        "staged_file_exists": staged_path.exists(),
        "r9_quality_ok": quality_lookup.get("quality_status", r9_values.get("QUALITY_STATUS", "")) == "OK",
        "r9_full_history_ready": truthy(quality_lookup.get("full_history_ready", r9_values.get("FULL_HISTORY_READY", ""))),
        "r9_usable_factor": truthy(quality_lookup.get("usable_for_factor_refresh", r9_values.get("USABLE_FOR_FACTOR_REFRESH", ""))),
        "r9_usable_technical": truthy(quality_lookup.get("usable_for_technical_overlay", r9_values.get("USABLE_FOR_TECHNICAL_OVERLAY", ""))),
        "staged_rows_positive": len(staged_rows) > 0,
    }

    integration_attempted = False
    integration_success = False
    existed_before = official_path.exists()
    backup_status = "NOT_RUN"
    backup_notes = ""

    ensure_dir(backup_dir)
    if existed_before:
        shutil.copy2(official_path, backup_file)
        backup_status = "BACKED_UP_EXISTING"
        backup_notes = "Existing VIX.csv copied before integration."
    else:
        backup_status = "MISSING_BEFORE_INTEGRATION"
        backup_notes = "No existing official VIX.csv before integration."
    write_text(restore_path, render_restore_script(root, official_path, backup_file, existed_before))
    backup_manifest_rows = [
        {"backup_item": "backup_dir", "path": str(backup_dir), "status": "CREATED", "notes": "Timestamped R10 backup directory."},
        {"backup_item": "official_vix_before", "path": str(backup_file if existed_before else official_path), "status": backup_status, "notes": backup_notes},
        {"backup_item": "restore_script", "path": str(restore_path), "status": "CREATED", "notes": "Restores previous VIX.csv or removes new file if none existed before."},
    ]
    write_csv(backup_manifest_path, backup_manifest_rows, BACKUP_FIELDS)

    if all(preconditions.values()):
        integration_attempted = True
        ensure_dir(official_path.parent)
        write_csv(official_path, staged_rows, ["date", "open", "high", "low", "close", "adj_close", "volume", "proxy_symbol", "source"])
        integration_success = official_path.exists()

    official_rows_raw, official_fields = read_csv(official_path)
    official_rows = normalize_staged_rows(official_rows_raw, official_fields)
    official_audit = audit_rows(official_rows)
    forbidden_changed = changed_forbidden_files(root, before)

    validations = [
        ("python_compile_check", py_compile(script_path), str(script_path)),
        ("powershell_parse_check", ps_parse(wrapper_path), str(wrapper_path)),
        ("r9_promotion_gate_promote_ready", r9_gate == "PROMOTE_READY", r9_gate),
        ("official_market_proxy_exists", official_path.exists(), str(official_path)),
        ("backup_dir_exists", backup_dir.exists(), str(backup_dir)),
        ("restore_script_exists", restore_path.exists(), str(restore_path)),
        ("backup_manifest_exists", backup_manifest_path.exists(), str(backup_manifest_path)),
        ("no_external_fetch", True, "R10 does not import or call external data providers."),
        ("row_count_matches_staged", official_audit["row_count"] == staged_audit["row_count"], f"staged={staged_audit['row_count']} official={official_audit['row_count']}"),
        ("date_range_matches_staged", official_audit["min_date"] == staged_audit["min_date"] and official_audit["max_date"] == staged_audit["max_date"], f"staged={staged_audit['min_date']}..{staged_audit['max_date']} official={official_audit['min_date']}..{official_audit['max_date']}"),
        ("close_column_available", official_audit["close_column_available"] == "TRUE", official_audit["close_column_available"]),
        ("close_non_null_positive", int(official_audit["close_non_null_count"] or "0") > 0, official_audit["close_non_null_count"]),
        ("full_history_ready", official_audit["full_history_ready"] == "TRUE", official_audit["full_history_ready"]),
        ("usable_for_factor_refresh", official_audit["usable_for_factor_refresh"] == "TRUE", official_audit["usable_for_factor_refresh"]),
        ("usable_for_technical_overlay", official_audit["usable_for_technical_overlay"] == "TRUE", official_audit["usable_for_technical_overlay"]),
        ("forbidden_files_unchanged", not forbidden_changed, ";".join(forbidden_changed[:20])),
    ]
    for name, ok in preconditions.items():
        validations.append((f"precondition_{name}", ok, str(ok)))

    fail_count = sum(1 for _, ok, _ in validations if not ok)
    quality_status = official_audit["quality_status"]
    status = STATUS_FAIL
    if fail_count == 0 and integration_success and quality_status == "OK":
        status = STATUS_OK
    elif fail_count == 0 and integration_success:
        status = STATUS_WARN

    values: Dict[str, str] = {
        "STATUS": status,
        "MODE": MODE,
        "R9_SOURCE_PATH": str(root / R9_READ_FIRST),
        "STAGED_VIX_SOURCE_PATH": str(staged_path),
        "OFFICIAL_MARKET_PROXY_PATH": str(official_path),
        "BACKUP_DIR": str(backup_dir),
        "RESTORE_SCRIPT_PATH": str(restore_path),
        "R9_PROMOTION_GATE_DECISION": r9_gate,
        "INTEGRATION_ATTEMPTED": str(integration_attempted).upper(),
        "INTEGRATION_SUCCESS": str(integration_success).upper(),
        "ROW_COUNT_STAGED": staged_audit["row_count"],
        "ROW_COUNT_OFFICIAL": official_audit["row_count"],
        "MIN_DATE": official_audit["min_date"],
        "MAX_DATE": official_audit["max_date"],
        "LATEST_DATE": official_audit["latest_date"],
        "CLOSE_COLUMN_AVAILABLE": official_audit["close_column_available"],
        "CLOSE_NON_NULL_COUNT": official_audit["close_non_null_count"],
        "FULL_HISTORY_READY": official_audit["full_history_ready"],
        "USABLE_FOR_FACTOR_REFRESH": official_audit["usable_for_factor_refresh"],
        "USABLE_FOR_TECHNICAL_OVERLAY": official_audit["usable_for_technical_overlay"],
        "QUALITY_STATUS": quality_status,
        "OFFICIAL_MARKET_PROXY_MODIFIED": str(integration_success).upper(),
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "VALIDATION_FAIL_COUNT": str(fail_count),
        "FORBIDDEN_FILE_MODIFIED": str(bool(forbidden_changed)).upper(),
        "NEXT_RECOMMENDED_STEP": "Run V18.25A-R11 full-compatible technical timing refresh against official market_proxy_cache VIX.",
    }
    values.update(FALSE_SAFETY)
    values["OFFICIAL_MARKET_PROXY_MODIFIED"] = str(integration_success).upper()

    plan_rows = [
        {"plan_item": "precondition_r9_gate", "path": str(root / R9_READ_FIRST), "status": str(preconditions["r9_promotion_ready"]).upper(), "notes": f"R9 gate={r9_gate}."},
        {"plan_item": "backup_existing_official_vix", "path": str(backup_file), "status": backup_status, "notes": backup_notes},
        {"plan_item": "restore_script", "path": str(restore_path), "status": str(restore_path.exists()).upper(), "notes": "Generated before integration."},
        {"plan_item": "official_market_proxy_write", "path": str(official_path), "status": str(integration_success).upper(), "notes": "Copy staged normalized VIX into official market proxy cache."},
    ]
    result_rows = [
        {"result_item": "integration_attempted", "value": values["INTEGRATION_ATTEMPTED"], "notes": "Attempted only after all preconditions passed."},
        {"result_item": "integration_success", "value": values["INTEGRATION_SUCCESS"], "notes": "Official VIX.csv write result."},
        {"result_item": "row_count_staged", "value": values["ROW_COUNT_STAGED"], "notes": "Normalized staged source rows."},
        {"result_item": "row_count_official", "value": values["ROW_COUNT_OFFICIAL"], "notes": "Official market proxy rows after integration."},
        {"result_item": "forbidden_file_modified", "value": values["FORBIDDEN_FILE_MODIFIED"], "notes": "Forbidden file signature check."},
    ]
    quality_rows_out = [{"metric": key, "value": value, "notes": "Post-integration official VIX audit."} for key, value in official_audit.items()]

    out_degraded = root / OUT_DEGRADED
    out_ops = root / OUT_OPS
    write_csv(out_degraded / "V18_25A_R10_CURRENT_MARKET_PROXY_INTEGRATION_PLAN.csv", plan_rows, PLAN_FIELDS)
    write_csv(out_degraded / "V18_25A_R10_CURRENT_MARKET_PROXY_INTEGRATION_RESULT.csv", result_rows, RESULT_FIELDS)
    write_csv(out_degraded / "V18_25A_R10_CURRENT_MARKET_PROXY_BACKUP_MANIFEST.csv", backup_manifest_rows, BACKUP_FIELDS)
    write_csv(out_degraded / "V18_25A_R10_CURRENT_POST_INTEGRATION_QUALITY_AUDIT.csv", quality_rows_out, QUALITY_FIELDS)
    report = render_report(values)
    write_text(out_degraded / "V18_25A_R10_CURRENT_REPORT.md", report)
    write_text(out_ops / "V18_25A_R10_CURRENT_OFFICIAL_MARKET_PROXY_INTEGRATION_REPORT.md", report)
    write_text(out_ops / "V18_25A_R10_READ_FIRST.txt", render_read_first(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
