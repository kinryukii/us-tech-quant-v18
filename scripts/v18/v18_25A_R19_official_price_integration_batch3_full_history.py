from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R19_OFFICIAL_BATCH3_FULL_HISTORY_INTEGRATION_READY"
STATUS_WARN = "WARN_V18_25A_R19_OFFICIAL_BATCH3_FULL_HISTORY_INTEGRATION_READY"
STATUS_FAIL = "FAIL_V18_25A_R19_OFFICIAL_BATCH3_FULL_HISTORY_INTEGRATION"
MODE = "OFFICIAL_PRICE_CACHE_INTEGRATION_BATCH3_FULL_HISTORY_ONLY_WITH_BACKUP"
BATCH_ID = "V18_25A_BATCH3"

R18_READ_FIRST = "outputs/v18/ops/V18_25A_R18_READ_FIRST.txt"
R18_FULL = "outputs/v18/staged_backfill/V18_25A_R18_CURRENT_BATCH3_FULL_HISTORY_CANDIDATES.csv"
R18_GATE = "outputs/v18/staged_backfill/V18_25A_R18_CURRENT_BATCH3_INTEGRATION_GATE.csv"
R18_AUDIT = "outputs/v18/staged_backfill/V18_25A_R18_CURRENT_BATCH3_STAGED_QUALITY_AUDIT.csv"
R18_PARTIAL = "outputs/v18/staged_backfill/V18_25A_R18_CURRENT_BATCH3_HELD_OUT_PARTIAL_HISTORY.csv"
R18_INVALID = "outputs/v18/staged_backfill/V18_25A_R18_CURRENT_BATCH3_INVALID_ARTIFACTS.csv"
STAGED_DIR = "data/v18/staged_backfill/V18_25A_BATCH3"
STAGED_NORMALIZED = "data/v18/staged_backfill/V18_25A_BATCH3/normalized"
STAGED_COMBINED = "data/v18/staged_backfill/V18_25A_BATCH3/V18_25A_BATCH3_COMBINED_NORMALIZED.csv"
STAGED_MANIFEST = "data/v18/staged_backfill/V18_25A_BATCH3/MANIFEST.csv"
PRICE_CACHE_DIR = "state/v18/price_cache"
BACKUP_ROOT = "archive/v18/price_cache_backups"

OUT_PLAN = "outputs/v18/staged_backfill/V18_25A_R19_CURRENT_OFFICIAL_BATCH3_INTEGRATION_PLAN.csv"
OUT_RESULT = "outputs/v18/staged_backfill/V18_25A_R19_CURRENT_OFFICIAL_BATCH3_INTEGRATION_RESULT.csv"
OUT_HELD_OUT = "outputs/v18/staged_backfill/V18_25A_R19_CURRENT_HELD_OUT_TICKERS.csv"
OUT_BACKUP_MANIFEST = "outputs/v18/staged_backfill/V18_25A_R19_CURRENT_BACKUP_MANIFEST.csv"
OUT_RETEST = "outputs/v18/rolling_coverage/V18_25A_R19_CURRENT_BATCH3_LOCAL_RETEST.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R19_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R19_CURRENT_OFFICIAL_BATCH3_INTEGRATION_REPORT.md"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "BATCH_ID",
    "R18_SOURCE_PATH",
    "STAGED_SOURCE_PATH",
    "OFFICIAL_PRICE_CACHE_DIR",
    "BACKUP_DIR",
    "RESTORE_SCRIPT_PATH",
    "BATCH3_CANDIDATE_COUNT",
    "FULL_HISTORY_CANDIDATE_COUNT",
    "INTEGRATION_ATTEMPT_COUNT",
    "INTEGRATION_SUCCESS_COUNT",
    "INTEGRATION_FAIL_COUNT",
    "HELD_OUT_COUNT",
    "PRICE_ONLY_PARTIAL_HELD_OUT_COUNT",
    "INVALID_ARTIFACT_HELD_OUT_COUNT",
    "QUALITY_REVIEW_HELD_OUT_COUNT",
    "SUSPICIOUS_DATA_HELD_OUT_COUNT",
    "OFFICIAL_PRICE_CACHE_MODIFIED",
    "OFFICIAL_PRICE_HISTORY_MODIFIED",
    "STAGED_BACKFILL_MODIFIED",
    "LEDGER_MODIFIED",
    "ROLLING_SCAN_EXECUTED",
    "LOCAL_RETEST_EXECUTED",
    "LOCAL_PRICE_SUCCESS_COUNT_AFTER_INTEGRATION",
    "FULL_HISTORY_READY_COUNT_AFTER_INTEGRATION",
    "RETEST_SUCCESS_RATIO",
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

PLAN_FIELDS = [
    "ticker",
    "approved_for_integration",
    "staged_normalized_path",
    "official_price_cache_path",
    "r18_quality_status",
    "r18_gate_decision",
    "plan_status",
    "notes",
]
RESULT_FIELDS = [
    "ticker",
    "integration_attempted",
    "integration_success",
    "backup_status",
    "official_path",
    "row_count",
    "min_date",
    "max_date",
    "latest_date",
    "close_column_available",
    "close_non_null_count",
    "full_history_ready",
    "error_message",
]
HELD_OUT_FIELDS = ["ticker", "held_out_category", "quality_status", "integration_gate_decision", "reason"]
BACKUP_FIELDS = ["ticker", "official_path", "backup_path", "status", "notes"]
RETEST_FIELDS = [
    "ticker",
    "official_price_cache_available",
    "row_count",
    "min_date",
    "max_date",
    "latest_date",
    "close_column_available",
    "close_non_null_count",
    "full_history_ready",
    "local_retest_status",
]


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
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
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


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def snapshot_tree(root: Path, rels: Sequence[str]) -> Dict[str, Tuple[int, int]]:
    out: Dict[str, Tuple[int, int]] = {}
    for rel in rels:
        base = root / rel
        if not base.exists():
            continue
        files = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
        for path in files:
            out[path.resolve().relative_to(root).as_posix()] = file_sig(path)
    return out


def changed_paths(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    keys = sorted(set(before) | set(after))
    return [key for key in keys if before.get(key) != after.get(key)]


def normalize_price_rows(rows: Sequence[Dict[str, str]], fields: Sequence[str], ticker: str) -> Tuple[List[Dict[str, str]], List[str]]:
    aliases = {field.lower(): field for field in fields}
    date_col = aliases.get("date")
    close_col = aliases.get("close")
    if not date_col or not close_col:
        raise ValueError("required date/close columns missing")
    output_fields = list(fields)
    if "ticker" not in [field.lower() for field in output_fields]:
        output_fields.append("ticker")

    cleaned: Dict[str, Dict[str, str]] = {}
    for row in rows:
        date_value = str(row.get(date_col, "")).strip()
        if not date_value:
            continue
        # R17 normalized data already uses ISO dates; retain the date portion if a timestamp appears.
        date_key = date_value[:10]
        new_row = {field: str(row.get(field, "")).strip() for field in fields}
        new_row[date_col] = date_key
        if "ticker" in new_row:
            new_row["ticker"] = ticker
        elif "Ticker" in new_row:
            new_row["Ticker"] = ticker
        else:
            new_row["ticker"] = ticker
        cleaned[date_key] = new_row
    return [cleaned[key] for key in sorted(cleaned)], output_fields


def price_quality(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> Dict[str, object]:
    aliases = {field.lower(): field for field in fields}
    date_col = aliases.get("date")
    close_col = aliases.get("close")
    dates = [str(row.get(date_col, "")).strip() for row in rows] if date_col else []
    close_values = [str(row.get(close_col, "")).strip() for row in rows] if close_col else []
    close_non_null = sum(1 for value in close_values if value)
    return {
        "row_count": len(rows),
        "min_date": min(dates) if dates else "",
        "max_date": max(dates) if dates else "",
        "latest_date": max(dates) if dates else "",
        "close_column_available": bool(close_col),
        "close_non_null_count": close_non_null,
    }


def render_restore_script(manifest_name: str) -> str:
    return f"""$ErrorActionPreference = "Stop"
$BackupDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $BackupDir "..\\..\\..\\..")
$Manifest = Join-Path $BackupDir "{manifest_name}"
if (-not (Test-Path -LiteralPath $Manifest)) {{
    throw "Backup manifest missing: $Manifest"
}}
Import-Csv -LiteralPath $Manifest | ForEach-Object {{
    $official = Join-Path $Root $_.official_path
    if ($_.status -eq "BACKED_UP_EXISTING") {{
        $backup = Join-Path $BackupDir $_.backup_path
        if (-not (Test-Path -LiteralPath $backup)) {{
            throw "Backup file missing: $backup"
        }}
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $official) | Out-Null
        Copy-Item -LiteralPath $backup -Destination $official -Force
        Write-Host "RESTORED: $official"
    }} elseif ($_.status -eq "MISSING_BEFORE_INTEGRATION") {{
        if (Test-Path -LiteralPath $official) {{
            Remove-Item -LiteralPath $official -Force
            Write-Host "REMOVED_NEW_FILE: $official"
        }}
    }}
}}
"""


def render_report(values: Dict[str, str], full_tickers: Sequence[str], held_tickers: Sequence[str]) -> str:
    return f"""# V18.25A-R19 Official Batch3 Price Cache Integration

Generated: {dt.datetime.now().isoformat(timespec="seconds")}

Status: {values['STATUS']}

Mode: {MODE}

Integrated full-history candidates: {values['INTEGRATION_SUCCESS_COUNT']} / {values['INTEGRATION_ATTEMPT_COUNT']}

Held out: {values['HELD_OUT_COUNT']} ({", ".join(held_tickers)})

Backup directory: {values['BACKUP_DIR']}

Restore script: {values['RESTORE_SCRIPT_PATH']}

Integrated tickers: {", ".join(full_tickers)}

Next step: {values['NEXT_RECOMMENDED_STEP']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    r18 = parse_read_first(root / R18_READ_FIRST)
    full_rows, _ = read_csv(root / R18_FULL)
    partial_rows, _ = read_csv(root / R18_PARTIAL)
    invalid_rows, _ = read_csv(root / R18_INVALID)
    audit_rows, _ = read_csv(root / R18_AUDIT)

    full_tickers = [norm_ticker(row.get("ticker")) for row in full_rows if norm_ticker(row.get("ticker"))]
    partial_tickers = [norm_ticker(row.get("ticker")) for row in partial_rows if norm_ticker(row.get("ticker"))]
    invalid_tickers = [norm_ticker(row.get("ticker")) for row in invalid_rows if norm_ticker(row.get("ticker"))]
    approved_set = set(full_tickers)
    held_out_set = set(partial_tickers) | set(invalid_tickers)

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root / BACKUP_ROOT / f"V18_25A_R19_{timestamp}"
    backup_price_rel = Path("state/v18/price_cache")
    restore_script = backup_dir / "RESTORE_V18_25A_R19_PRICE_CACHE.ps1"
    archive_manifest = backup_dir / "BACKUP_MANIFEST.csv"
    price_cache_dir = root / PRICE_CACHE_DIR
    staged_normalized_dir = root / STAGED_NORMALIZED

    protected_before = snapshot_tree(root, [
        "state/v18/price_cache",
        "data/v18/price_history",
        "data/v18/staged_backfill",
        "data/v18/staged_market_proxy",
        "state/v18/market_proxy_cache",
        "state/v18/rolling_coverage",
        "outputs/v18/factor_pack",
        "outputs/v18/technical_timing",
        "outputs/v18/tier_migration",
        "outputs/v18/degraded_daily",
        "outputs/v18/official_daily_decision",
        "outputs/v18/daily_decision",
        "state/v18/official_daily_decision",
    ])

    validation_failures: List[str] = []
    if not r18.get("STATUS", "").startswith("OK_V18_25A_R18"):
        validation_failures.append("R18 status is not OK")
    if r18.get("OFFICIAL_INTEGRATION_ALLOWED_NEXT_STEP") != "TRUE":
        validation_failures.append("R18 did not allow next-step integration")
    if to_int(r18.get("OFFICIAL_INTEGRATION_CANDIDATE_COUNT")) != len(full_tickers):
        validation_failures.append("R18 candidate count does not match full-history file")
    if len(full_tickers) != len(approved_set):
        validation_failures.append("Full-history candidates are not unique")
    if approved_set & held_out_set:
        validation_failures.append("Approved candidates overlap held-out tickers")
    if "TICKERS" in approved_set:
        validation_failures.append("Invalid artifact TICKERS is in approved set")

    plan_rows: List[Dict[str, object]] = []
    result_rows: List[Dict[str, object]] = []
    backup_rows: List[Dict[str, object]] = []
    retest_rows: List[Dict[str, object]] = []

    ensure_dir(backup_dir)
    ensure_dir(price_cache_dir)

    for ticker in full_tickers:
        staged_path = staged_normalized_dir / f"{ticker}.csv"
        official_path = price_cache_dir / f"{ticker}.csv"
        r18_row = next((row for row in full_rows if norm_ticker(row.get("ticker")) == ticker), {})
        gate_decision = str(r18_row.get("integration_gate_decision", "")).strip()
        quality_status = str(r18_row.get("quality_status", "")).strip()
        plan_status = "READY" if staged_path.exists() and gate_decision == "FULL_HISTORY_INTEGRATION_CANDIDATE" else "BLOCKED"
        if plan_status != "READY":
            validation_failures.append(f"{ticker}: staged file missing or R18 gate not ready")
        plan_rows.append({
            "ticker": ticker,
            "approved_for_integration": "TRUE",
            "staged_normalized_path": str(staged_path),
            "official_price_cache_path": str(official_path),
            "r18_quality_status": quality_status,
            "r18_gate_decision": gate_decision,
            "plan_status": plan_status,
            "notes": "Full-history-only Batch3 integration candidate.",
        })

    if validation_failures:
        status = STATUS_FAIL
    else:
        status = STATUS_OK

    # Backup first, then write only approved official cache files.
    if status != STATUS_FAIL:
        for ticker in full_tickers:
            official_path = price_cache_dir / f"{ticker}.csv"
            backup_rel = backup_price_rel / f"{ticker}.csv"
            backup_path = backup_dir / backup_rel
            if official_path.exists():
                ensure_dir(backup_path.parent)
                shutil.copy2(official_path, backup_path)
                backup_status = "BACKED_UP_EXISTING"
                notes = "Existing official cache copied before overwrite."
            else:
                backup_status = "MISSING_BEFORE_INTEGRATION"
                notes = "No official cache existed before integration."
            backup_rows.append({
                "ticker": ticker,
                "official_path": str(Path(PRICE_CACHE_DIR) / f"{ticker}.csv").replace("\\", "/"),
                "backup_path": str(backup_rel).replace("\\", "/"),
                "status": backup_status,
                "notes": notes,
            })
        write_csv(archive_manifest, backup_rows, BACKUP_FIELDS)
        write_text(restore_script, render_restore_script("BACKUP_MANIFEST.csv"))

        for ticker in full_tickers:
            staged_path = staged_normalized_dir / f"{ticker}.csv"
            official_path = price_cache_dir / f"{ticker}.csv"
            error_message = ""
            success = False
            quality = {
                "row_count": 0,
                "min_date": "",
                "max_date": "",
                "latest_date": "",
                "close_column_available": False,
                "close_non_null_count": 0,
            }
            try:
                staged_rows, staged_fields = read_csv(staged_path)
                normalized_rows, output_fields = normalize_price_rows(staged_rows, staged_fields, ticker)
                quality = price_quality(normalized_rows, output_fields)
                if quality["row_count"] <= 0:
                    raise ValueError("normalized rows empty")
                if not quality["close_column_available"] or int(quality["close_non_null_count"]) <= 0:
                    raise ValueError("close column invalid")
                write_csv(official_path, normalized_rows, output_fields)
                success = True
            except Exception as exc:
                error_message = str(exc)

            result_rows.append({
                "ticker": ticker,
                "integration_attempted": "TRUE",
                "integration_success": str(success).upper(),
                "backup_status": next((row["status"] for row in backup_rows if row["ticker"] == ticker), ""),
                "official_path": str(official_path),
                "row_count": quality["row_count"],
                "min_date": quality["min_date"],
                "max_date": quality["max_date"],
                "latest_date": quality["latest_date"],
                "close_column_available": str(bool(quality["close_column_available"])).upper(),
                "close_non_null_count": quality["close_non_null_count"],
                "full_history_ready": str(success).upper(),
                "error_message": error_message,
            })

    for ticker in full_tickers:
        official_path = price_cache_dir / f"{ticker}.csv"
        rows, fields = read_csv(official_path)
        quality = price_quality(rows, fields)
        success = official_path.exists() and quality["row_count"] > 0 and bool(quality["close_column_available"]) and int(quality["close_non_null_count"]) > 0
        retest_rows.append({
            "ticker": ticker,
            "official_price_cache_available": str(official_path.exists()).upper(),
            "row_count": quality["row_count"],
            "min_date": quality["min_date"],
            "max_date": quality["max_date"],
            "latest_date": quality["latest_date"],
            "close_column_available": str(bool(quality["close_column_available"])).upper(),
            "close_non_null_count": quality["close_non_null_count"],
            "full_history_ready": str(success).upper(),
            "local_retest_status": "PASS" if success else "FAIL",
        })

    held_out_rows: List[Dict[str, object]] = []
    for row in partial_rows:
        held_out_rows.append({
            "ticker": norm_ticker(row.get("ticker")),
            "held_out_category": "PRICE_ONLY_PARTIAL_HISTORY",
            "quality_status": row.get("quality_status", ""),
            "integration_gate_decision": row.get("integration_gate_decision", ""),
            "reason": "Held out by R18 price-only partial gate.",
        })
    for row in invalid_rows:
        held_out_rows.append({
            "ticker": norm_ticker(row.get("ticker")),
            "held_out_category": "INVALID_ARTIFACT",
            "quality_status": row.get("quality_status", ""),
            "integration_gate_decision": row.get("integration_gate_decision", ""),
            "reason": row.get("artifact_reason", "Invalid artifact held out."),
        })

    success_count = sum(1 for row in result_rows if row.get("integration_success") == "TRUE")
    fail_count = len(full_tickers) - success_count
    local_success_count = sum(1 for row in retest_rows if row.get("local_retest_status") == "PASS")
    full_history_ready_after = sum(1 for row in retest_rows if row.get("full_history_ready") == "TRUE")
    retest_ratio = f"{(local_success_count / len(full_tickers) if full_tickers else 0.0):.4f}"

    protected_after = snapshot_tree(root, [
        "state/v18/price_cache",
        "data/v18/price_history",
        "data/v18/staged_backfill",
        "data/v18/staged_market_proxy",
        "state/v18/market_proxy_cache",
        "state/v18/rolling_coverage",
        "outputs/v18/factor_pack",
        "outputs/v18/technical_timing",
        "outputs/v18/tier_migration",
        "outputs/v18/degraded_daily",
        "outputs/v18/official_daily_decision",
        "outputs/v18/daily_decision",
        "state/v18/official_daily_decision",
    ])
    changed = changed_paths(protected_before, protected_after)
    approved_cache_rels = {f"{PRICE_CACHE_DIR}/{ticker}.csv" for ticker in full_tickers}
    forbidden_changes = [
        rel for rel in changed
        if rel.replace("\\", "/") not in approved_cache_rels
    ]
    held_out_cache_changed = [
        rel for rel in changed
        if Path(rel).name.replace(".csv", "").upper() in held_out_set
    ]
    if held_out_cache_changed:
        validation_failures.append("Held-out official cache file changed")
    if forbidden_changes:
        validation_failures.append("Forbidden path changed")
    if fail_count:
        validation_failures.append("One or more approved integrations failed")
    if not restore_script.exists():
        validation_failures.append("Restore script missing")
    if not archive_manifest.exists():
        validation_failures.append("Backup manifest missing")

    final_fail_count = len(validation_failures)
    if final_fail_count:
        status = STATUS_WARN if success_count > 0 and not forbidden_changes else STATUS_FAIL
    else:
        status = STATUS_OK

    write_csv(root / OUT_PLAN, plan_rows, PLAN_FIELDS)
    write_csv(root / OUT_RESULT, result_rows, RESULT_FIELDS)
    write_csv(root / OUT_HELD_OUT, held_out_rows, HELD_OUT_FIELDS)
    write_csv(root / OUT_BACKUP_MANIFEST, backup_rows, BACKUP_FIELDS)
    write_csv(root / OUT_RETEST, retest_rows, RETEST_FIELDS)

    next_step = "Run a separate Batch3 rolling ledger update/local coverage validation for the 59 integrated full-history tickers."
    values = {
        "STATUS": status,
        "MODE": MODE,
        "BATCH_ID": BATCH_ID,
        "R18_SOURCE_PATH": str(root / R18_READ_FIRST),
        "STAGED_SOURCE_PATH": str(root / STAGED_NORMALIZED),
        "OFFICIAL_PRICE_CACHE_DIR": str(price_cache_dir),
        "BACKUP_DIR": str(backup_dir),
        "RESTORE_SCRIPT_PATH": str(restore_script),
        "BATCH3_CANDIDATE_COUNT": r18.get("R17_CANDIDATE_COUNT", str(len(audit_rows))),
        "FULL_HISTORY_CANDIDATE_COUNT": str(len(full_tickers)),
        "INTEGRATION_ATTEMPT_COUNT": str(len(full_tickers)),
        "INTEGRATION_SUCCESS_COUNT": str(success_count),
        "INTEGRATION_FAIL_COUNT": str(fail_count),
        "HELD_OUT_COUNT": str(len(held_out_rows)),
        "PRICE_ONLY_PARTIAL_HELD_OUT_COUNT": str(len(partial_rows)),
        "INVALID_ARTIFACT_HELD_OUT_COUNT": str(len(invalid_rows)),
        "QUALITY_REVIEW_HELD_OUT_COUNT": r18.get("QUALITY_REVIEW_HOLD_COUNT", "0"),
        "SUSPICIOUS_DATA_HELD_OUT_COUNT": "0",
        "OFFICIAL_PRICE_CACHE_MODIFIED": "TRUE" if success_count else "FALSE",
        "OFFICIAL_PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "ROLLING_SCAN_EXECUTED": "FALSE",
        "LOCAL_RETEST_EXECUTED": "TRUE",
        "LOCAL_PRICE_SUCCESS_COUNT_AFTER_INTEGRATION": str(local_success_count),
        "FULL_HISTORY_READY_COUNT_AFTER_INTEGRATION": str(full_history_ready_after),
        "RETEST_SUCCESS_RATIO": retest_ratio,
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "TIER_MIGRATION_MODIFIED": "FALSE",
        "DEGRADED_DAILY_MODIFIED": "FALSE",
        "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "BACKTEST_EXECUTED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "VALIDATION_FAIL_COUNT": str(final_fail_count),
        "FORBIDDEN_FILE_MODIFIED": "TRUE" if forbidden_changes else "FALSE",
        "NEXT_RECOMMENDED_STEP": next_step,
    }
    report = render_report(values, full_tickers, [row["ticker"] for row in held_out_rows])
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
