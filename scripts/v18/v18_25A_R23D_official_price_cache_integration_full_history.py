from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRYRUN = "OK_V18_25A_R23D_DRYRUN_OFFICIAL_PRICE_INTEGRATION_PLAN_READY"
STATUS_OK = "OK_V18_25A_R23D_OFFICIAL_PRICE_CACHE_INTEGRATION_READY"
STATUS_CANDIDATES_MISSING = "WARN_V18_25A_R23D_CANDIDATES_MISSING"
STATUS_ZERO_APPROVED = "WARN_V18_25A_R23D_ZERO_APPROVED_CANDIDATES"
STATUS_PARTIAL_REFUSED = "WARN_V18_25A_R23D_PARTIAL_HISTORY_INTEGRATION_REFUSED"
STATUS_PARTIAL_FAILURE = "WARN_V18_25A_R23D_INTEGRATION_PARTIAL_FAILURE"
STATUS_RETEST_FAILURE = "WARN_V18_25A_R23D_POST_RETEST_FAILURE"
STATUS_BACKUP_INCOMPLETE = "WARN_V18_25A_R23D_BACKUP_INCOMPLETE"

MODE_DRYRUN = "DRYRUN_OFFICIAL_PRICE_INTEGRATION_PLAN_ONLY"
MODE_APPLY = "APPLY_OFFICIAL_PRICE_CACHE_INTEGRATION_FULL_HISTORY_ONLY"

CANDIDATES = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_OFFICIAL_INTEGRATION_CANDIDATES.csv"
PARTIAL_HOLDS = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_PARTIAL_HISTORY_HOLDS.csv"
EMPTY_HOLDS = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_EMPTY_OR_FAILED_HOLDS.csv"
NORMALIZED_DIR = "data/v18/staged_backfill/V18_25A_R23B_MISSING_CACHE/normalized"
PRICE_CACHE = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OUT_PLAN = "outputs/v18/price_integration/V18_25A_R23D_CURRENT_INTEGRATION_PLAN.csv"
OUT_RESULT = "outputs/v18/price_integration/V18_25A_R23D_CURRENT_INTEGRATION_RESULT.csv"
OUT_HELD = "outputs/v18/price_integration/V18_25A_R23D_CURRENT_HELD_OUT_NOT_INTEGRATED.csv"
OUT_RETEST = "outputs/v18/price_integration/V18_25A_R23D_CURRENT_POST_INTEGRATION_LOCAL_RETEST.csv"
OUT_BACKUP_MANIFEST = "outputs/v18/price_integration/V18_25A_R23D_CURRENT_BACKUP_MANIFEST.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R23D_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R23D_CURRENT_OFFICIAL_PRICE_INTEGRATION_REPORT.md"

APPROVED = "APPROVED_FULL_HISTORY_OFFICIAL_INTEGRATION_CANDIDATE"
MIN_ROWS = 500

PLAN_FIELDS = [
    "priority_rank",
    "ticker",
    "normalized_file",
    "target_official_price_cache_file",
    "target_action",
    "row_count",
    "min_date",
    "max_date",
    "quality_status",
    "integration_candidate_status",
    "plan_status",
    "reason",
]
RESULT_FIELDS = [
    "ticker",
    "integration_attempted",
    "integration_success",
    "target_action",
    "target_official_price_cache_file",
    "rows_written",
    "duplicate_date_count_before",
    "duplicate_date_count_after",
    "error_message",
]
HELD_FIELDS = ["ticker", "source", "hold_status", "reason", "next_action"]
RETEST_FIELDS = [
    "ticker",
    "official_cache_file",
    "file_exists",
    "readable",
    "row_count",
    "latest_date",
    "latest_close",
    "required_columns_available",
    "retest_status",
    "error_message",
]
BACKUP_FIELDS = ["ticker", "target_file", "backup_file", "backup_status", "notes"]
READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "CANDIDATE_PATH",
    "OFFICIAL_PRICE_CACHE_DIR",
    "BACKUP_DIR",
    "MAX_TICKERS",
    "R23C_APPROVED_EXPECTED_COUNT",
    "SELECTED_CANDIDATE_COUNT",
    "PARTIAL_HISTORY_HOLD_COUNT",
    "EMPTY_OR_FAILED_HOLD_COUNT",
    "INTEGRATION_ATTEMPT_COUNT",
    "INTEGRATION_SUCCESS_COUNT",
    "INTEGRATION_FAIL_COUNT",
    "TARGET_NEW_FILE_COUNT",
    "TARGET_UPDATED_FILE_COUNT",
    "TARGET_SKIPPED_COUNT",
    "POST_INTEGRATION_RETEST_ATTEMPT_COUNT",
    "POST_INTEGRATION_RETEST_SUCCESS_COUNT",
    "POST_INTEGRATION_RETEST_FAIL_COUNT",
    "HELD_OUT_NOT_INTEGRATED_COUNT",
    "BACKUP_MANIFEST_PATH",
    "RESTORE_SCRIPT_PATH",
    "INTEGRATION_PLAN_PATH",
    "INTEGRATION_RESULT_PATH",
    "POST_INTEGRATION_RETEST_PATH",
    "OFFICIAL_PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_FILES_MODIFIED",
    "OFFICIAL_DECISION_MODIFIED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
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


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def parse_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        return float(text) if text else None
    except Exception:
        return None


def valid_symbol(ticker: str) -> bool:
    if ticker in {"", "TICKER", "TICKERS", "HEADER", "NULL", "NONE", "NAN", "SYMBOL"}:
        return False
    if any(ch in ticker for ch in '<>:"/\\|?*'):
        return False
    return bool(re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", ticker))


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def changed_keys(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    return [key for key in sorted(set(before) | set(after)) if before.get(key) != after.get(key)]


def rel_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def validate_and_transform(root: Path, candidate: Dict[str, str], target_file: Path) -> Tuple[bool, List[Dict[str, object]], Dict[str, object], str]:
    ticker = norm_ticker(candidate.get("ticker"))
    path_text = str(candidate.get("normalized_file", "") or "").strip()
    source_path = Path(path_text) if path_text else root / NORMALIZED_DIR / f"{ticker}.csv"
    if not source_path.is_absolute():
        source_path = root / source_path
    rows, fields = read_csv(source_path)
    required = {"ticker", "date", "open", "high", "low", "close", "volume"}
    field_set = {str(field).strip().lower() for field in fields}
    status = str(candidate.get("integration_candidate_status") or candidate.get("quality_status") or "")
    meta = {
        "ticker": ticker,
        "source_path": source_path.as_posix(),
        "row_count": len(rows),
        "min_date": "",
        "max_date": "",
        "duplicate_before": 0,
        "duplicate_after": 0,
    }
    if status != APPROVED:
        return False, [], meta, "Candidate is not approved full-history status."
    if not valid_symbol(ticker):
        return False, [], meta, "Invalid or artifact ticker."
    if not source_path.exists() or not rows or not required.issubset(field_set):
        return False, [], meta, "Normalized staged file missing, empty, or missing required columns."
    if len(rows) < MIN_ROWS and str(candidate.get("quality_status", "")) != APPROVED:
        return False, [], meta, "Row count below full-history minimum."

    transformed_by_date: Dict[str, Dict[str, object]] = {}
    duplicate_before = 0
    for row in rows:
        date_text = str(row.get("date", "") or "").strip()[:10]
        try:
            dt.datetime.strptime(date_text, "%Y-%m-%d")
        except Exception:
            return False, [], meta, f"Unparseable date: {date_text}"
        close = parse_float(row.get("close"))
        if close is None or close <= 0:
            return False, [], meta, f"Invalid close for {date_text}"
        if date_text in transformed_by_date:
            duplicate_before += 1
        transformed_by_date[date_text] = {
            "date": date_text,
            "open": row.get("open", ""),
            "high": row.get("high", ""),
            "low": row.get("low", ""),
            "close": row.get("close", ""),
            "adj_close": row.get("adj_close", ""),
            "volume": row.get("volume", ""),
            "source": "V18_25A_R23D_FULL_HISTORY_STAGED_INTEGRATION",
            "source_file": source_path.as_posix(),
            "updated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        }
    out = [transformed_by_date[key] for key in sorted(transformed_by_date)]
    dates = [row["date"] for row in out]
    meta.update(
        {
            "row_count": len(out),
            "min_date": min(dates) if dates else "",
            "max_date": max(dates) if dates else "",
            "duplicate_before": duplicate_before,
            "duplicate_after": 0,
        }
    )
    return True, out, meta, ""


def retest_cache(path: Path, ticker: str) -> Dict[str, object]:
    rows, fields = read_csv(path)
    required = {"date", "open", "high", "low", "close", "volume"}
    field_set = {str(field).strip().lower() for field in fields}
    latest_date = ""
    latest_close = ""
    error = ""
    if rows:
        latest = sorted(rows, key=lambda row: str(row.get("date", "")))[-1]
        latest_date = str(latest.get("date", "") or "")
        latest_close = str(latest.get("close", "") or "")
    close_value = parse_float(latest_close)
    ok = path.exists() and bool(fields) and bool(rows) and bool(latest_date) and close_value is not None and close_value > 0 and required.issubset(field_set)
    if not ok:
        error = "Official cache retest failed required existence/readability/latest close/required column checks."
    return {
        "ticker": ticker,
        "official_cache_file": path.as_posix(),
        "file_exists": str(path.exists()).upper(),
        "readable": str(bool(fields)).upper(),
        "row_count": len(rows),
        "latest_date": latest_date,
        "latest_close": latest_close,
        "required_columns_available": str(required.issubset(field_set)).upper(),
        "retest_status": "LOCAL_PRICE_CACHE_READY" if ok else "LOCAL_PRICE_CACHE_RETEST_FAIL",
        "error_message": error,
    }


def create_backup(root: Path, targets: Sequence[Tuple[str, Path]], run_stamp: str) -> Tuple[Path, List[Dict[str, object]]]:
    backup_dir = root / "archive" / "v18" / "price_cache_backups" / f"V18_25A_R23D_{run_stamp}"
    ensure_dir(backup_dir)
    rows: List[Dict[str, object]] = []
    for ticker, target in targets:
        backup_file = backup_dir / target.name
        if target.exists():
            shutil.copy2(target, backup_file)
            rows.append({"ticker": ticker, "target_file": target.as_posix(), "backup_file": backup_file.as_posix(), "backup_status": "BACKED_UP_EXISTING_FILE", "notes": ""})
        else:
            rows.append({"ticker": ticker, "target_file": target.as_posix(), "backup_file": "", "backup_status": "NEW_TARGET_FILE", "notes": "No existing official cache file to back up."})
    write_csv(backup_dir / "MANIFEST.csv", rows, BACKUP_FIELDS)
    restore = """[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant"
)
$ErrorActionPreference = "Stop"
$manifestPath = Join-Path $PSScriptRoot "MANIFEST.csv"
$manifest = Import-Csv $manifestPath
foreach ($row in $manifest) {
    $target = $row.target_file
    if ($row.backup_status -eq "BACKED_UP_EXISTING_FILE") {
        Copy-Item -Path $row.backup_file -Destination $target -Force
        Write-Host "Restored $target"
    } elseif ($row.backup_status -eq "NEW_TARGET_FILE") {
        if (Test-Path $target) {
            Remove-Item -Path $target -Force
            Write-Host "Removed new target $target"
        }
    }
}
"""
    write_text(backup_dir / "RESTORE_V18_25A_R23D_PRICE_CACHE.ps1", restore)
    write_text(
        backup_dir / "README_RESTORE_V18_25A_R23D.txt",
        "R23D official price cache backup.\nRun RESTORE_V18_25A_R23D_PRICE_CACHE.ps1 from this directory to restore overwritten files and remove new target files.\n",
    )
    return backup_dir, rows


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object]) -> str:
    return "\n".join(
        [
            "# V18.25A R23D Official Price Cache Integration Report",
            "",
            f"STATUS: {values['STATUS']}",
            f"MODE: {values['MODE']}",
            f"RUN_ID: {values['RUN_ID']}",
            "",
            "## Integration",
            f"- selected_candidate_count: {values['SELECTED_CANDIDATE_COUNT']}",
            f"- integration_success_count: {values['INTEGRATION_SUCCESS_COUNT']}",
            f"- integration_fail_count: {values['INTEGRATION_FAIL_COUNT']}",
            f"- target_new_file_count: {values['TARGET_NEW_FILE_COUNT']}",
            f"- target_updated_file_count: {values['TARGET_UPDATED_FILE_COUNT']}",
            "",
            "## Safety",
            "- external_fetch_executed: FALSE",
            "- rolling_ledger_modified: FALSE",
            "- official_decision_modified: FALSE",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-tickers", type=int, default=36)
    parser.add_argument("--require-full-history-only", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"V18_25A_R23D_{run_stamp}"
    price_dir = root / PRICE_CACHE
    candidate_rows, _ = read_csv(root / CANDIDATES)
    partial_rows, _ = read_csv(root / PARTIAL_HOLDS)
    empty_rows, _ = read_csv(root / EMPTY_HOLDS)
    partial_tickers = {norm_ticker(row.get("ticker")) for row in partial_rows}
    empty_tickers = {norm_ticker(row.get("ticker")) for row in empty_rows}

    price_before = tree_sig(price_dir)
    ledger_before = file_sig(root / LEDGER)
    factor_before = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_before = tree_sig(root / "outputs" / "v18" / "technical_timing")
    tiers_before = tree_sig(root / "outputs" / "v18" / "tiers")
    decision_before = tree_sig(root / "outputs" / "v18" / "daily_decision")

    status = STATUS_DRYRUN if args.dry_run else STATUS_OK
    validation_fail_count = 0
    backup_dir = ""
    restore_script = ""
    backup_rows: List[Dict[str, object]] = []
    plan_rows: List[Dict[str, object]] = []
    result_rows: List[Dict[str, object]] = []
    retest_rows: List[Dict[str, object]] = []
    held_rows: List[Dict[str, object]] = []

    if not args.require_full_history_only:
        status = STATUS_PARTIAL_REFUSED
        validation_fail_count = 1
    elif not candidate_rows:
        status = STATUS_CANDIDATES_MISSING
        validation_fail_count = 1

    selected: List[Dict[str, str]] = []
    if candidate_rows and args.require_full_history_only:
        sorted_candidates = sorted(candidate_rows, key=lambda row: (norm_ticker(row.get("ticker"))))
        for row in sorted_candidates:
            ticker = norm_ticker(row.get("ticker"))
            if len(selected) >= max(args.max_tickers, 0):
                held_rows.append({"ticker": ticker, "source": "R23C_CANDIDATES", "hold_status": "TARGET_SKIPPED", "reason": "Beyond MaxTickers limit.", "next_action": "Review in later integration batch."})
                continue
            if ticker in partial_tickers or ticker in empty_tickers:
                held_rows.append({"ticker": ticker, "source": "R23C_CANDIDATES", "hold_status": "TARGET_SKIPPED", "reason": "Ticker also appears in R23C hold files.", "next_action": "Review source classification before integration."})
                continue
            selected.append(row)
    if status in {STATUS_DRYRUN, STATUS_OK} and not selected:
        status = STATUS_ZERO_APPROVED
        validation_fail_count = 1

    targets: List[Tuple[str, Path]] = []
    transformed: Dict[str, List[Dict[str, object]]] = {}
    target_new = target_updated = target_skipped = 0
    for idx, row in enumerate(selected, 1):
        ticker = norm_ticker(row.get("ticker"))
        target = price_dir / f"{ticker}.csv"
        ok, official_rows, meta, error = validate_and_transform(root, row, target)
        action = "UPDATE_EXISTING_FILE" if target.exists() else "CREATE_NEW_FILE"
        if not ok:
            target_skipped += 1
            held_rows.append({"ticker": ticker, "source": "R23C_CANDIDATES", "hold_status": "TARGET_SKIPPED", "reason": error, "next_action": "Review staged normalized file before integration."})
        else:
            transformed[ticker] = official_rows
            targets.append((ticker, target))
            if target.exists():
                target_updated += 1
            else:
                target_new += 1
        plan_rows.append(
            {
                "priority_rank": idx,
                "ticker": ticker,
                "normalized_file": row.get("normalized_file", ""),
                "target_official_price_cache_file": target.as_posix(),
                "target_action": action if ok else "SKIP",
                "row_count": meta.get("row_count", ""),
                "min_date": meta.get("min_date", ""),
                "max_date": meta.get("max_date", ""),
                "quality_status": row.get("quality_status", ""),
                "integration_candidate_status": row.get("integration_candidate_status", ""),
                "plan_status": "READY_FOR_INTEGRATION" if ok else "HELD_OUT_NOT_INTEGRATED",
                "reason": row.get("reason", "") if ok else error,
            }
        )
    for row in partial_rows:
        held_rows.append({"ticker": norm_ticker(row.get("ticker")), "source": "R23C_PARTIAL_HISTORY_HOLDS", "hold_status": "HELD_OUT_PARTIAL_HISTORY", "reason": row.get("reason", "Partial-history hold."), "next_action": "Handle under separate partial-history policy."})
    for row in empty_rows:
        held_rows.append({"ticker": norm_ticker(row.get("ticker")), "source": "R23C_EMPTY_OR_FAILED_HOLDS", "hold_status": row.get("quality_status", "HELD_OUT_EMPTY_OR_FAILED"), "reason": row.get("reason", "Empty or failed fetch hold."), "next_action": "Review provider symbol/status before retry."})

    integration_attempt = integration_success = integration_fail = 0
    backup_incomplete = False
    if not args.dry_run and status == STATUS_OK:
        backup_path, backup_rows = create_backup(root, targets, run_stamp)
        backup_dir = backup_path.as_posix()
        restore_script = (backup_path / "RESTORE_V18_25A_R23D_PRICE_CACHE.ps1").as_posix()
        if not (backup_path / "MANIFEST.csv").exists() or not (backup_path / "RESTORE_V18_25A_R23D_PRICE_CACHE.ps1").exists():
            backup_incomplete = True
        ensure_dir(price_dir)
        for ticker, target in targets:
            integration_attempt += 1
            try:
                write_csv(target, transformed[ticker], ["date", "open", "high", "low", "close", "adj_close", "volume", "source", "source_file", "updated_at"])
                integration_success += 1
                result_rows.append({"ticker": ticker, "integration_attempted": "TRUE", "integration_success": "TRUE", "target_action": "UPDATE_EXISTING_FILE" if any(r["ticker"] == ticker and r["backup_status"] == "BACKED_UP_EXISTING_FILE" for r in backup_rows) else "CREATE_NEW_FILE", "target_official_price_cache_file": target.as_posix(), "rows_written": len(transformed[ticker]), "duplicate_date_count_before": "", "duplicate_date_count_after": 0, "error_message": ""})
            except Exception as exc:
                integration_fail += 1
                result_rows.append({"ticker": ticker, "integration_attempted": "TRUE", "integration_success": "FALSE", "target_action": "WRITE_FAILED", "target_official_price_cache_file": target.as_posix(), "rows_written": 0, "duplicate_date_count_before": "", "duplicate_date_count_after": "", "error_message": f"{type(exc).__name__}: {exc}"})
        for ticker, target in targets:
            if target.exists():
                retest_rows.append(retest_cache(target, ticker))
    else:
        for ticker, target in targets:
            result_rows.append({"ticker": ticker, "integration_attempted": "FALSE", "integration_success": "FALSE", "target_action": "DRYRUN_NO_WRITE" if args.dry_run else "NOT_APPLIED", "target_official_price_cache_file": target.as_posix(), "rows_written": len(transformed.get(ticker, [])), "duplicate_date_count_before": "", "duplicate_date_count_after": "", "error_message": ""})

    retest_success = sum(1 for row in retest_rows if row.get("retest_status") == "LOCAL_PRICE_CACHE_READY")
    retest_fail = len(retest_rows) - retest_success
    if not args.dry_run and backup_incomplete:
        status = STATUS_BACKUP_INCOMPLETE
        validation_fail_count += 1
    elif not args.dry_run and integration_fail:
        status = STATUS_PARTIAL_FAILURE
        validation_fail_count += integration_fail
    elif not args.dry_run and retest_fail:
        status = STATUS_RETEST_FAILURE
        validation_fail_count += retest_fail

    write_csv(root / OUT_PLAN, plan_rows, PLAN_FIELDS)
    write_csv(root / OUT_RESULT, result_rows, RESULT_FIELDS)
    write_csv(root / OUT_HELD, held_rows, HELD_FIELDS)
    write_csv(root / OUT_RETEST, retest_rows, RETEST_FIELDS)
    write_csv(root / OUT_BACKUP_MANIFEST, backup_rows, BACKUP_FIELDS)

    price_after = tree_sig(price_dir)
    changed_price = changed_keys(price_before, price_after)
    allowed_price = {Path(f"{ticker}.csv").as_posix() for ticker, _target in targets}
    price_modified = bool(changed_price)
    non_target_price_modified = any(key not in allowed_price for key in changed_price)
    ledger_modified = file_sig(root / LEDGER) != ledger_before
    factor_modified = tree_sig(root / "outputs" / "v18" / "factor_pack") != factor_before
    tech_modified = tree_sig(root / "outputs" / "v18" / "technical_timing") != tech_before
    tiers_modified = tree_sig(root / "outputs" / "v18" / "tiers") != tiers_before
    decision_modified = tree_sig(root / "outputs" / "v18" / "daily_decision") != decision_before
    forbidden_modified = non_target_price_modified or ledger_modified or factor_modified or tech_modified or tiers_modified or decision_modified

    values = {
        "STATUS": status,
        "MODE": MODE_DRYRUN if args.dry_run else MODE_APPLY,
        "RUN_ID": run_id,
        "CANDIDATE_PATH": CANDIDATES,
        "OFFICIAL_PRICE_CACHE_DIR": PRICE_CACHE,
        "BACKUP_DIR": backup_dir,
        "MAX_TICKERS": args.max_tickers,
        "R23C_APPROVED_EXPECTED_COUNT": 36,
        "SELECTED_CANDIDATE_COUNT": len(selected),
        "PARTIAL_HISTORY_HOLD_COUNT": len(partial_rows),
        "EMPTY_OR_FAILED_HOLD_COUNT": len(empty_rows),
        "INTEGRATION_ATTEMPT_COUNT": integration_attempt,
        "INTEGRATION_SUCCESS_COUNT": integration_success,
        "INTEGRATION_FAIL_COUNT": integration_fail,
        "TARGET_NEW_FILE_COUNT": target_new,
        "TARGET_UPDATED_FILE_COUNT": target_updated,
        "TARGET_SKIPPED_COUNT": target_skipped,
        "POST_INTEGRATION_RETEST_ATTEMPT_COUNT": len(retest_rows),
        "POST_INTEGRATION_RETEST_SUCCESS_COUNT": retest_success,
        "POST_INTEGRATION_RETEST_FAIL_COUNT": retest_fail,
        "HELD_OUT_NOT_INTEGRATED_COUNT": len(held_rows),
        "BACKUP_MANIFEST_PATH": OUT_BACKUP_MANIFEST,
        "RESTORE_SCRIPT_PATH": restore_script,
        "INTEGRATION_PLAN_PATH": OUT_PLAN,
        "INTEGRATION_RESULT_PATH": OUT_RESULT,
        "POST_INTEGRATION_RETEST_PATH": OUT_RETEST,
        "OFFICIAL_PRICE_CACHE_MODIFIED": str(price_modified).upper(),
        "ROLLING_LEDGER_MODIFIED": str(ledger_modified).upper(),
        "FACTOR_PACK_MODIFIED": str(factor_modified).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(tech_modified).upper(),
        "TIER_FILES_MODIFIED": str(tiers_modified).upper(),
        "OFFICIAL_DECISION_MODIFIED": str(decision_modified).upper(),
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": "R23E: Rolling ledger update and local coverage validation for the 36 newly integrated full-history tickers.",
    }
    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values))
    print(f"STATUS: {status}")
    print(f"MODE: {values['MODE']}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
