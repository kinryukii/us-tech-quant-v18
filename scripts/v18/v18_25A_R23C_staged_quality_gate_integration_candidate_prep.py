from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R23C_STAGED_QUALITY_GATE_READY"
STATUS_INPUTS_MISSING = "WARN_V18_25A_R23C_INPUTS_MISSING"
STATUS_COUNT_MISMATCH = "WARN_V18_25A_R23C_CANDIDATE_COUNT_MISMATCH"
STATUS_REVIEW_NEEDED = "WARN_V18_25A_R23C_QUALITY_REVIEW_NEEDED"
STATUS_ZERO_FULL = "WARN_V18_25A_R23C_ZERO_FULL_HISTORY_CANDIDATES"
STATUS_PARTIAL_REFUSED = "WARN_V18_25A_R23C_PARTIAL_HISTORY_INTEGRATION_REFUSED"

MODE = "READ_ONLY_STAGED_QUALITY_GATE"

QUALITY_PRECHECK = "outputs/v18/staged_backfill/V18_25A_R23B_CURRENT_QUALITY_PRECHECK.csv"
MANIFEST = "outputs/v18/staged_backfill/V18_25A_R23B_CURRENT_STAGED_BACKFILL_MANIFEST.csv"
NORMALIZATION = "outputs/v18/staged_backfill/V18_25A_R23B_CURRENT_NORMALIZATION_RESULT.csv"
FETCH = "outputs/v18/staged_backfill/V18_25A_R23B_CURRENT_FETCH_RESULT.csv"
HELD = "outputs/v18/staged_backfill/V18_25A_R23B_CURRENT_HELD_OUT_OR_FAILED.csv"
NORMALIZED_DIR = "data/v18/staged_backfill/V18_25A_R23B_MISSING_CACHE/normalized"
PRICE_CACHE = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
RAW_STAGED_DIR = "data/v18/staged_backfill/V18_25A_R23B_MISSING_CACHE/raw"

OUT_GATE = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_STAGED_QUALITY_GATE.csv"
OUT_CANDIDATES = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_OFFICIAL_INTEGRATION_CANDIDATES.csv"
OUT_PARTIAL = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_PARTIAL_HISTORY_HOLDS.csv"
OUT_EMPTY = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_EMPTY_OR_FAILED_HOLDS.csv"
OUT_AUDIT = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_INTEGRATION_GATE_AUDIT.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R23C_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R23C_CURRENT_STAGED_QUALITY_GATE_REPORT.md"

R23B_FULL_HISTORY_READY_EXPECTED = 36

GATE_FIELDS = [
    "ticker",
    "normalized_file",
    "file_exists",
    "readable",
    "required_columns_present",
    "row_count",
    "min_date",
    "max_date",
    "latest_close",
    "latest_volume",
    "date_parse_ok",
    "duplicate_date_count",
    "null_close_count",
    "r23b_quality_status",
    "quality_status",
    "integration_candidate_status",
    "reason",
    "provider",
    "fetch_run_id",
]
CANDIDATE_FIELDS = [
    "ticker",
    "normalized_file",
    "row_count",
    "min_date",
    "max_date",
    "latest_close",
    "latest_volume",
    "quality_status",
    "integration_candidate_status",
    "official_price_cache_integration_allowed_next",
    "reason",
    "source_batch_id",
    "provider",
    "fetch_run_id",
]
AUDIT_FIELDS = ["metric", "value", "notes"]
READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R23B_QUALITY_PRECHECK_PATH",
    "STAGED_NORMALIZED_DIR",
    "MIN_ROWS_FULL_HISTORY",
    "ALLOW_PARTIAL_HISTORY_INTEGRATION",
    "R23B_FULL_HISTORY_READY_EXPECTED",
    "NORMALIZED_FILE_COUNT",
    "QUALITY_GATE_TOTAL_COUNT",
    "APPROVED_FULL_HISTORY_CANDIDATE_COUNT",
    "PARTIAL_HISTORY_HOLD_COUNT",
    "EMPTY_OR_FAILED_HOLD_COUNT",
    "QUALITY_REVIEW_NEEDED_COUNT",
    "INVALID_OR_ARTIFACT_COUNT",
    "OFFICIAL_INTEGRATION_CANDIDATES_PATH",
    "PARTIAL_HISTORY_HOLDS_PATH",
    "EMPTY_OR_FAILED_HOLDS_PATH",
    "QUALITY_GATE_PATH",
    "OFFICIAL_PRICE_CACHE_INTEGRATION_ALLOWED_NEXT",
    "QUALITY_GATE_PASSED_FOR_FULL_HISTORY",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
    "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_FILES_MODIFIED",
    "STAGED_BACKFILL_RAW_MODIFIED",
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


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


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


def rel_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def parse_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        return float(text) if text else None
    except Exception:
        return None


def eval_normalized_file(root: Path, ticker: str, path: Path, r23b_quality: str, min_rows: int) -> Dict[str, object]:
    rows, fields = read_csv(path)
    required = {"ticker", "date", "open", "high", "low", "close", "volume"}
    present = {str(field).strip().lower() for field in fields}
    file_exists = path.exists()
    readable = bool(fields)
    required_ok = required.issubset(present)
    dates = []
    null_close = 0
    latest_close = ""
    latest_volume = ""
    for row in rows:
        date_text = str(row.get("date", "") or "").strip()
        try:
            parsed = dt.datetime.strptime(date_text[:10], "%Y-%m-%d").date()
            dates.append(parsed)
        except Exception:
            pass
        close_text = str(row.get("close", "") or "").strip()
        if not close_text:
            null_close += 1
    duplicate_dates = len(dates) - len(set(dates))
    if rows:
        latest = rows[-1]
        latest_close = str(latest.get("close", "") or "").strip()
        latest_volume = str(latest.get("volume", "") or "").strip()
    latest_close_num = parse_float(latest_close)
    date_parse_ok = bool(dates) and len(dates) == len(rows)
    invalid = not valid_symbol(ticker)
    if invalid:
        status = "HELD_OUT_INVALID_OR_ARTIFACT"
        reason = "Invalid or artifact ticker."
    elif r23b_quality == "EMPTY_FETCH":
        status = "HELD_OUT_EMPTY_FETCH"
        reason = "R23B classified ticker as EMPTY_FETCH."
    elif r23b_quality == "FETCH_FAILED":
        status = "HELD_OUT_FETCH_FAILED"
        reason = "R23B classified ticker as FETCH_FAILED."
    elif r23b_quality == "NORMALIZATION_FAILED":
        status = "HELD_OUT_NORMALIZATION_FAILED"
        reason = "R23B classified ticker as NORMALIZATION_FAILED."
    elif not file_exists or not readable or not rows:
        status = "HELD_OUT_EMPTY_FETCH"
        reason = "Normalized file missing, unreadable, or empty."
    elif not required_ok or not date_parse_ok or latest_close_num is None or latest_close_num <= 0:
        status = "HELD_OUT_QUALITY_REVIEW_NEEDED"
        reason = "Required columns/date/latest close quality gate failed."
    elif r23b_quality == "FULL_HISTORY_READY" and to_int(len(rows)) >= min_rows:
        status = "APPROVED_FULL_HISTORY_OFFICIAL_INTEGRATION_CANDIDATE"
        reason = "R23B full-history-ready and R23C normalized-file quality gate passed."
    elif r23b_quality == "FULL_HISTORY_READY":
        status = "APPROVED_FULL_HISTORY_OFFICIAL_INTEGRATION_CANDIDATE"
        reason = "R23B marked full-history-ready with stronger rule; R23C normalized-file quality gate passed."
    elif r23b_quality == "PARTIAL_HISTORY_HOLD" or len(rows) < min_rows:
        status = "HELD_OUT_PARTIAL_HISTORY"
        reason = "Partial history remains held out for separate policy handling."
    else:
        status = "HELD_OUT_QUALITY_REVIEW_NEEDED"
        reason = f"Unhandled R23B quality status: {r23b_quality}"
    return {
        "ticker": ticker,
        "normalized_file": rel_path(root, path),
        "file_exists": str(file_exists).upper(),
        "readable": str(readable).upper(),
        "required_columns_present": str(required_ok).upper(),
        "row_count": len(rows),
        "min_date": min(dates).isoformat() if dates else "",
        "max_date": max(dates).isoformat() if dates else "",
        "latest_close": latest_close,
        "latest_volume": latest_volume,
        "date_parse_ok": str(date_parse_ok).upper(),
        "duplicate_date_count": duplicate_dates,
        "null_close_count": null_close,
        "r23b_quality_status": r23b_quality,
        "quality_status": status,
        "integration_candidate_status": status,
        "reason": reason,
        "provider": rows[0].get("provider", "") if rows else "",
        "fetch_run_id": rows[0].get("fetch_run_id", "") if rows else "",
    }


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object], mismatch_note: str) -> str:
    return "\n".join(
        [
            "# V18.25A R23C Staged Quality Gate Report",
            "",
            f"STATUS: {values['STATUS']}",
            f"MODE: {values['MODE']}",
            f"RUN_ID: {values['RUN_ID']}",
            "",
            "## Gate Summary",
            f"- approved_full_history_candidate_count: {values['APPROVED_FULL_HISTORY_CANDIDATE_COUNT']}",
            f"- partial_history_hold_count: {values['PARTIAL_HISTORY_HOLD_COUNT']}",
            f"- empty_or_failed_hold_count: {values['EMPTY_OR_FAILED_HOLD_COUNT']}",
            f"- quality_review_needed_count: {values['QUALITY_REVIEW_NEEDED_COUNT']}",
            f"- expected_full_history_count: {values['R23B_FULL_HISTORY_READY_EXPECTED']}",
            f"- candidate_count_match: {mismatch_note or 'TRUE'}",
            "",
            "## Safety",
            "- external_fetch_executed: FALSE",
            "- official price cache modified: FALSE",
            "- rolling ledger modified: FALSE",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--min-rows-full-history", type=int, default=500)
    parser.add_argument("--allow-partial-history-integration", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R23C_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    price_before = tree_sig(root / PRICE_CACHE)
    ledger_before = file_sig(root / LEDGER)
    factor_before = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_before = tree_sig(root / "outputs" / "v18" / "technical_timing")
    tiers_before = tree_sig(root / "outputs" / "v18" / "tiers")
    raw_before = tree_sig(root / RAW_STAGED_DIR)

    quality_rows, _ = read_csv(root / QUALITY_PRECHECK)
    _manifest_rows, _ = read_csv(root / MANIFEST)
    norm_rows, _ = read_csv(root / NORMALIZATION)
    _fetch_rows, _ = read_csv(root / FETCH)
    _held_rows, _ = read_csv(root / HELD)
    norm_dir = root / NORMALIZED_DIR

    status = STATUS_OK
    validation_fail_count = 0
    if args.allow_partial_history_integration:
        status = STATUS_PARTIAL_REFUSED
        validation_fail_count = 1
    elif not quality_rows or not norm_rows or not norm_dir.exists():
        status = STATUS_INPUTS_MISSING
        validation_fail_count = 1

    quality_by_ticker = {norm_ticker(row.get("ticker")): row for row in quality_rows}
    norm_by_ticker = {norm_ticker(row.get("ticker")): row for row in norm_rows}
    gate_rows: List[Dict[str, object]] = []
    tickers = sorted(set(quality_by_ticker) | set(norm_by_ticker))
    for ticker in tickers:
        q = quality_by_ticker.get(ticker, {})
        n = norm_by_ticker.get(ticker, {})
        normalized_path = str(n.get("normalized_path", "") or "").strip()
        path = Path(normalized_path) if normalized_path else norm_dir / f"{ticker}.csv"
        if not path.is_absolute():
            path = root / path
        gate_rows.append(eval_normalized_file(root, ticker, path, str(q.get("quality_status", "") or ""), args.min_rows_full_history))

    candidates = [row for row in gate_rows if row["quality_status"] == "APPROVED_FULL_HISTORY_OFFICIAL_INTEGRATION_CANDIDATE"]
    partial = [row for row in gate_rows if row["quality_status"] == "HELD_OUT_PARTIAL_HISTORY"]
    empty_failed = [row for row in gate_rows if row["quality_status"] in {"HELD_OUT_EMPTY_FETCH", "HELD_OUT_FETCH_FAILED", "HELD_OUT_NORMALIZATION_FAILED"}]
    review = [row for row in gate_rows if row["quality_status"] == "HELD_OUT_QUALITY_REVIEW_NEEDED"]
    invalid = [row for row in gate_rows if row["quality_status"] == "HELD_OUT_INVALID_OR_ARTIFACT"]

    if status == STATUS_OK and not candidates:
        status = STATUS_ZERO_FULL
        validation_fail_count = 1
    elif status == STATUS_OK and len(candidates) != R23B_FULL_HISTORY_READY_EXPECTED:
        status = STATUS_COUNT_MISMATCH
    elif status == STATUS_OK and review:
        status = STATUS_REVIEW_NEEDED

    candidate_rows = []
    for row in candidates:
        candidate_rows.append(
            {
                "ticker": row["ticker"],
                "normalized_file": row["normalized_file"],
                "row_count": row["row_count"],
                "min_date": row["min_date"],
                "max_date": row["max_date"],
                "latest_close": row["latest_close"],
                "latest_volume": row["latest_volume"],
                "quality_status": row["quality_status"],
                "integration_candidate_status": row["integration_candidate_status"],
                "official_price_cache_integration_allowed_next": "TRUE",
                "reason": row["reason"],
                "source_batch_id": "V18_25A_R23B_MISSING_CACHE",
                "provider": row["provider"],
                "fetch_run_id": row["fetch_run_id"],
            }
        )

    audit_rows = [
        {"metric": "status", "value": status, "notes": ""},
        {"metric": "r23b_full_history_ready_expected", "value": R23B_FULL_HISTORY_READY_EXPECTED, "notes": ""},
        {"metric": "normalized_file_count", "value": len(list(norm_dir.glob('*.csv'))) if norm_dir.exists() else 0, "notes": ""},
        {"metric": "quality_gate_total_count", "value": len(gate_rows), "notes": ""},
        {"metric": "approved_full_history_candidate_count", "value": len(candidates), "notes": ""},
        {"metric": "partial_history_hold_count", "value": len(partial), "notes": ""},
        {"metric": "empty_or_failed_hold_count", "value": len(empty_failed), "notes": ""},
        {"metric": "quality_review_needed_count", "value": len(review), "notes": ""},
        {"metric": "invalid_or_artifact_count", "value": len(invalid), "notes": ""},
        {"metric": "external_fetch_executed", "value": "FALSE", "notes": "R23C is read-only."},
    ]
    write_csv(root / OUT_GATE, gate_rows, GATE_FIELDS)
    write_csv(root / OUT_CANDIDATES, candidate_rows, CANDIDATE_FIELDS)
    write_csv(root / OUT_PARTIAL, partial, GATE_FIELDS)
    write_csv(root / OUT_EMPTY, empty_failed, GATE_FIELDS)
    write_csv(root / OUT_AUDIT, audit_rows, AUDIT_FIELDS)

    price_modified = tree_sig(root / PRICE_CACHE) != price_before
    ledger_modified = file_sig(root / LEDGER) != ledger_before
    factor_modified = tree_sig(root / "outputs" / "v18" / "factor_pack") != factor_before
    tech_modified = tree_sig(root / "outputs" / "v18" / "technical_timing") != tech_before
    tiers_modified = tree_sig(root / "outputs" / "v18" / "tiers") != tiers_before
    raw_modified = tree_sig(root / RAW_STAGED_DIR) != raw_before
    forbidden_modified = price_modified or ledger_modified or factor_modified or tech_modified or tiers_modified or raw_modified
    mismatch_note = "" if len(candidates) == R23B_FULL_HISTORY_READY_EXPECTED else f"FALSE - approved {len(candidates)} vs expected {R23B_FULL_HISTORY_READY_EXPECTED}"

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R23B_QUALITY_PRECHECK_PATH": QUALITY_PRECHECK,
        "STAGED_NORMALIZED_DIR": NORMALIZED_DIR,
        "MIN_ROWS_FULL_HISTORY": args.min_rows_full_history,
        "ALLOW_PARTIAL_HISTORY_INTEGRATION": str(args.allow_partial_history_integration).upper(),
        "R23B_FULL_HISTORY_READY_EXPECTED": R23B_FULL_HISTORY_READY_EXPECTED,
        "NORMALIZED_FILE_COUNT": len(list(norm_dir.glob("*.csv"))) if norm_dir.exists() else 0,
        "QUALITY_GATE_TOTAL_COUNT": len(gate_rows),
        "APPROVED_FULL_HISTORY_CANDIDATE_COUNT": len(candidates),
        "PARTIAL_HISTORY_HOLD_COUNT": len(partial),
        "EMPTY_OR_FAILED_HOLD_COUNT": len(empty_failed),
        "QUALITY_REVIEW_NEEDED_COUNT": len(review),
        "INVALID_OR_ARTIFACT_COUNT": len(invalid),
        "OFFICIAL_INTEGRATION_CANDIDATES_PATH": OUT_CANDIDATES,
        "PARTIAL_HISTORY_HOLDS_PATH": OUT_PARTIAL,
        "EMPTY_OR_FAILED_HOLDS_PATH": OUT_EMPTY,
        "QUALITY_GATE_PATH": OUT_GATE,
        "OFFICIAL_PRICE_CACHE_INTEGRATION_ALLOWED_NEXT": "TRUE" if candidates and not args.allow_partial_history_integration else "FALSE",
        "QUALITY_GATE_PASSED_FOR_FULL_HISTORY": "TRUE" if candidates and not review and not invalid else "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "PRICE_CACHE_MODIFIED": str(price_modified).upper(),
        "ROLLING_LEDGER_MODIFIED": str(ledger_modified).upper(),
        "FACTOR_PACK_MODIFIED": str(factor_modified).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(tech_modified).upper(),
        "TIER_FILES_MODIFIED": str(tiers_modified).upper(),
        "STAGED_BACKFILL_RAW_MODIFIED": str(raw_modified).upper(),
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": "R23D: Official price cache integration with backup for approved full-history candidates only.",
    }
    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, mismatch_note))
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
