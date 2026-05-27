from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import traceback
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRYRUN = "OK_V18_25A_R23B_DRYRUN_STAGED_BACKFILL_PLAN_VALIDATED"
STATUS_OK = "OK_V18_25A_R23B_CONTROLLED_STAGED_BACKFILL_READY"
STATUS_FETCH_NOT_AUTH = "WARN_V18_25A_R23B_EXTERNAL_FETCH_NOT_AUTHORIZED"
STATUS_PLAN_MISSING = "WARN_V18_25A_R23B_PLAN_MISSING"
STATUS_NO_APPROVED = "WARN_V18_25A_R23B_NO_APPROVED_TICKERS"
STATUS_PARTIAL_FETCH = "WARN_V18_25A_R23B_PARTIAL_FETCH_FAILURE"
STATUS_REVIEW = "WARN_V18_25A_R23B_QUALITY_REVIEW_NEEDED"
STATUS_ZERO_FULL = "WARN_V18_25A_R23B_ZERO_FULL_HISTORY_READY"

MODE_DRYRUN = "DRYRUN_NO_FETCH"
MODE_EXECUTE = "CONTROLLED_STAGED_BACKFILL_EXECUTION"

PLAN_PATH = "outputs/v18/staged_backfill/V18_25A_R23_CURRENT_BACKFILL_PLAN.csv"
CANDIDATES_PATH = "outputs/v18/staged_backfill/V18_25A_R23_CURRENT_MISSING_CACHE_CANDIDATES.csv"
EXCLUDED_PATH = "outputs/v18/staged_backfill/V18_25A_R23_CURRENT_EXCLUDED_INVALID_OR_ARTIFACTS.csv"
PRICE_CACHE = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

STAGED_DIR = "data/v18/staged_backfill/V18_25A_R23B_MISSING_CACHE"
RAW_DIR = "data/v18/staged_backfill/V18_25A_R23B_MISSING_CACHE/raw"
NORMALIZED_DIR = "data/v18/staged_backfill/V18_25A_R23B_MISSING_CACHE/normalized"
MANIFEST_DIR = "data/v18/staged_backfill/V18_25A_R23B_MISSING_CACHE/manifest"
COMBINED_NORMALIZED = "data/v18/staged_backfill/V18_25A_R23B_MISSING_CACHE/manifest/V18_25A_R23B_COMBINED_NORMALIZED.csv"
STAGED_MANIFEST = "data/v18/staged_backfill/V18_25A_R23B_MISSING_CACHE/manifest/MANIFEST.csv"

OUT_FETCH = "outputs/v18/staged_backfill/V18_25A_R23B_CURRENT_FETCH_RESULT.csv"
OUT_NORM = "outputs/v18/staged_backfill/V18_25A_R23B_CURRENT_NORMALIZATION_RESULT.csv"
OUT_MANIFEST = "outputs/v18/staged_backfill/V18_25A_R23B_CURRENT_STAGED_BACKFILL_MANIFEST.csv"
OUT_QUALITY = "outputs/v18/staged_backfill/V18_25A_R23B_CURRENT_QUALITY_PRECHECK.csv"
OUT_HELD = "outputs/v18/staged_backfill/V18_25A_R23B_CURRENT_HELD_OUT_OR_FAILED.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R23B_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R23B_CURRENT_CONTROLLED_STAGED_BACKFILL_REPORT.md"

MIN_FULL_HISTORY_ROWS = 1000
MIN_PARTIAL_HISTORY_ROWS = 1

FETCH_FIELDS = [
    "ticker",
    "priority_rank",
    "provider",
    "fetch_attempted",
    "fetch_success",
    "fetch_empty",
    "fetch_failed",
    "raw_row_count",
    "raw_path",
    "fetch_timestamp",
    "error_message",
]
NORM_FIELDS = [
    "ticker",
    "normalization_attempted",
    "normalization_success",
    "normalization_failed",
    "normalized_row_count",
    "normalized_path",
    "duplicate_date_count_before_cleaning",
    "duplicate_date_count_after_cleaning",
    "error_message",
]
QUALITY_FIELDS = [
    "ticker",
    "row_count",
    "min_date",
    "max_date",
    "latest_close",
    "latest_volume",
    "has_required_ohlcv",
    "duplicate_date_count",
    "null_close_count",
    "full_history_ready_flag",
    "partial_history_flag",
    "quality_status",
    "notes",
]
MANIFEST_FIELDS = ["ticker", "file_type", "relative_path", "exists", "row_count", "notes"]
HELD_FIELDS = ["ticker", "priority_rank", "classification", "reason", "provider", "error_message"]
READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "PROVIDER",
    "ALLOW_EXTERNAL_FETCH",
    "PLAN_PATH",
    "STAGED_OUTPUT_DIR",
    "MAX_TICKERS",
    "R23_APPROVED_EXPECTED_COUNT",
    "SELECTED_TICKER_COUNT",
    "ALREADY_HAS_LOCAL_CACHE_NOW_COUNT",
    "FETCH_ATTEMPT_COUNT",
    "FETCH_SUCCESS_COUNT",
    "FETCH_EMPTY_COUNT",
    "FETCH_FAIL_COUNT",
    "NORMALIZATION_SUCCESS_COUNT",
    "NORMALIZATION_FAIL_COUNT",
    "FULL_HISTORY_READY_COUNT",
    "PARTIAL_HISTORY_HOLD_COUNT",
    "QUALITY_REVIEW_NEEDED_COUNT",
    "HELD_OUT_OR_FAILED_COUNT",
    "RAW_FILE_COUNT",
    "NORMALIZED_FILE_COUNT",
    "COMBINED_NORMALIZED_CREATED",
    "MANIFEST_PATH",
    "FETCH_RESULT_PATH",
    "NORMALIZATION_RESULT_PATH",
    "QUALITY_PRECHECK_PATH",
    "HELD_OUT_OR_FAILED_PATH",
    "OFFICIAL_PRICE_CACHE_INTEGRATION_ALLOWED_NOW",
    "QUALITY_GATE_REQUIRED_NEXT",
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
    "OFFICIAL_DECISION_MODIFIED",
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


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


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


def select_tickers(root: Path, plan_rows: List[Dict[str, str]], max_tickers: int) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], int]:
    rows = sorted(plan_rows, key=lambda row: (to_int(row.get("priority_rank"), 999999), norm_ticker(row.get("ticker"))))
    approved_expected = len(rows)
    selected: List[Dict[str, object]] = []
    held: List[Dict[str, object]] = []
    seen: set[str] = set()
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        rank = row.get("priority_rank", "")
        if ticker in seen:
            held.append({"ticker": ticker, "priority_rank": rank, "classification": "HELD_OUT_DUPLICATE", "reason": "Duplicate plan ticker.", "provider": row.get("proposed_provider", ""), "error_message": ""})
            continue
        seen.add(ticker)
        if not valid_symbol(ticker):
            held.append({"ticker": ticker, "priority_rank": rank, "classification": "INVALID_OR_ARTIFACT", "reason": "Invalid or artifact ticker.", "provider": row.get("proposed_provider", ""), "error_message": ""})
            continue
        if not is_true(row.get("never_success_status")) or str(row.get("missing_cache_status", "")).upper() != "MISSING_LOCAL_PRICE_CACHE":
            held.append({"ticker": ticker, "priority_rank": rank, "classification": "REVIEW_NEEDED", "reason": "Plan row is not an approved missing-cache never-success row.", "provider": row.get("proposed_provider", ""), "error_message": ""})
            continue
        if (root / PRICE_CACHE / f"{ticker}.csv").exists():
            held.append({"ticker": ticker, "priority_rank": rank, "classification": "ALREADY_HAS_LOCAL_CACHE_NOW", "reason": "Local price cache exists now; fetch skipped.", "provider": row.get("proposed_provider", ""), "error_message": ""})
            continue
        selected.append({"ticker": ticker, "priority_rank": rank, "provider": row.get("proposed_provider", "yfinance")})
    if len(selected) > max(max_tickers, 0):
        for row in selected[max(max_tickers, 0) :]:
            held.append({"ticker": row["ticker"], "priority_rank": row["priority_rank"], "classification": "REVIEW_NEEDED", "reason": "Beyond MaxTickers limit.", "provider": row["provider"], "error_message": ""})
        selected = selected[: max(max_tickers, 0)]
    return selected, held, approved_expected


def flatten_columns(df):
    if hasattr(df.columns, "to_flat_index"):
        cols = []
        for col in df.columns.to_flat_index():
            if isinstance(col, tuple):
                parts = [str(part) for part in col if str(part) and str(part) != "nan"]
                cols.append("_".join(parts))
            else:
                cols.append(str(col))
        df = df.copy()
        df.columns = cols
    return df


def standard_col_name(col: str, ticker: str) -> str:
    base = col.strip().lower().replace(" ", "_").replace(".", "_")
    suffix = f"_{ticker.lower()}"
    if base.endswith(suffix):
        base = base[: -len(suffix)]
    aliases = {
        "date": "date",
        "datetime": "date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "adj_close": "adj_close",
        "adjclose": "adj_close",
        "volume": "volume",
    }
    return aliases.get(base, base)


def normalize_frame(raw_df, ticker: str, provider: str, run_id: str, timestamp: str):
    import pandas as pd

    df = flatten_columns(raw_df)
    if "Date" not in df.columns and "date" not in [str(c).lower() for c in df.columns]:
        df = df.reset_index()
    df = df.rename(columns={col: standard_col_name(str(col), ticker) for col in df.columns})
    if "date" not in df.columns:
        return pd.DataFrame(), 0, "date column missing"
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype("string")
    for col in ["open", "high", "low", "close", "adj_close", "volume"]:
        if col in df.columns:
            out[col] = pd.to_numeric(df[col], errors="coerce")
    duplicate_before = int(out.duplicated(subset=["date"]).sum())
    out = out.dropna(subset=["date"]).sort_values("date").drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
    out.insert(0, "ticker", ticker)
    out["provider"] = provider
    out["fetch_run_id"] = run_id
    out["fetch_timestamp"] = timestamp
    out["source_quality"] = "STAGED_PROVIDER_RAW_NORMALIZED"
    cols = ["ticker", "date", "open", "high", "low", "close", "adj_close", "volume", "provider", "fetch_run_id", "fetch_timestamp", "source_quality"]
    for col in cols:
        if col not in out.columns:
            out[col] = ""
    return out[cols], duplicate_before, ""


def fetch_yfinance(ticker: str):
    import yfinance as yf

    return yf.download(ticker, period="max", interval="1d", auto_adjust=False, progress=False, threads=False)


def configure_yfinance_cache(cache_dir: Path) -> None:
    import yfinance as yf
    import yfinance.cache as yf_cache

    ensure_dir(cache_dir)
    yf.set_tz_cache_location(str(cache_dir))
    yf_cache.set_cache_location(str(cache_dir))


def quality_from_normalized(ticker: str, normalized_df, duplicate_before: int, notes: str = "") -> Dict[str, object]:
    import pandas as pd

    if normalized_df is None or normalized_df.empty:
        return {
            "ticker": ticker,
            "row_count": 0,
            "min_date": "",
            "max_date": "",
            "latest_close": "",
            "latest_volume": "",
            "has_required_ohlcv": "FALSE",
            "duplicate_date_count": duplicate_before,
            "null_close_count": 0,
            "full_history_ready_flag": "FALSE",
            "partial_history_flag": "FALSE",
            "quality_status": "EMPTY_FETCH",
            "notes": notes,
        }
    dates = pd.to_datetime(normalized_df["date"], errors="coerce")
    row_count = int(len(normalized_df.index))
    required = all(col in normalized_df.columns for col in ["open", "high", "low", "close", "volume"])
    null_close = int(normalized_df["close"].isna().sum()) if "close" in normalized_df.columns else row_count
    duplicate_after = int(normalized_df.duplicated(subset=["date"]).sum())
    close_non_null = row_count - null_close
    latest_row = normalized_df.sort_values("date").tail(1).iloc[0]
    full = row_count >= MIN_FULL_HISTORY_ROWS and required and close_non_null > 0 and duplicate_after == 0
    partial = row_count >= MIN_PARTIAL_HISTORY_ROWS and not full
    if full:
        status = "FULL_HISTORY_READY"
    elif partial:
        status = "PARTIAL_HISTORY_HOLD"
    else:
        status = "REVIEW_NEEDED"
    return {
        "ticker": ticker,
        "row_count": row_count,
        "min_date": dates.min().date().isoformat() if dates.notna().any() else "",
        "max_date": dates.max().date().isoformat() if dates.notna().any() else "",
        "latest_close": latest_row.get("close", ""),
        "latest_volume": latest_row.get("volume", ""),
        "has_required_ohlcv": str(required).upper(),
        "duplicate_date_count": duplicate_after,
        "null_close_count": null_close,
        "full_history_ready_flag": str(full).upper(),
        "partial_history_flag": str(partial).upper(),
        "quality_status": status,
        "notes": notes or f"duplicate_before_cleaning={duplicate_before}",
    }


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object]) -> str:
    return "\n".join(
        [
            "# V18.25A R23B Controlled Staged Backfill Report",
            "",
            f"STATUS: {values['STATUS']}",
            f"MODE: {values['MODE']}",
            f"RUN_ID: {values['RUN_ID']}",
            "",
            "## Execution",
            f"- selected_ticker_count: {values['SELECTED_TICKER_COUNT']}",
            f"- fetch_success_count: {values['FETCH_SUCCESS_COUNT']}",
            f"- fetch_empty_count: {values['FETCH_EMPTY_COUNT']}",
            f"- fetch_fail_count: {values['FETCH_FAIL_COUNT']}",
            f"- normalization_success_count: {values['NORMALIZATION_SUCCESS_COUNT']}",
            f"- full_history_ready_count: {values['FULL_HISTORY_READY_COUNT']}",
            f"- partial_history_hold_count: {values['PARTIAL_HISTORY_HOLD_COUNT']}",
            "",
            "## Safety",
            "- official price cache integration: FALSE",
            "- price cache modified: FALSE",
            "- rolling ledger modified: FALSE",
            "- staged raw writes only occur in controlled execution mode.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--max-tickers", type=int, default=58)
    parser.add_argument("--provider", default="yfinance")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-external-fetch", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R23B_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    fetch_timestamp = dt.datetime.now().replace(microsecond=0).isoformat()
    plan_path = root / PLAN_PATH
    staged_dir = root / STAGED_DIR
    raw_dir = root / RAW_DIR
    normalized_dir = root / NORMALIZED_DIR
    manifest_dir = root / MANIFEST_DIR
    combined_path = root / COMBINED_NORMALIZED

    price_before = tree_sig(root / PRICE_CACHE)
    ledger_before = file_sig(root / LEDGER)
    factor_before = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_before = tree_sig(root / "outputs" / "v18" / "technical_timing")
    tiers_before = tree_sig(root / "outputs" / "v18" / "tiers")
    decision_before = tree_sig(root / "outputs" / "v18" / "daily_decision")
    staged_before = tree_sig(staged_dir)

    plan_rows, _ = read_csv(plan_path)
    _candidate_rows, _ = read_csv(root / CANDIDATES_PATH)
    _excluded_rows, _ = read_csv(root / EXCLUDED_PATH)
    selected, held_rows, approved_expected = select_tickers(root, plan_rows, args.max_tickers) if plan_rows else ([], [], 0)

    mode = MODE_DRYRUN if args.dry_run else MODE_EXECUTE
    status = STATUS_DRYRUN if args.dry_run else STATUS_OK
    validation_fail_count = 0
    fetch_rows: List[Dict[str, object]] = []
    norm_rows: List[Dict[str, object]] = []
    quality_rows: List[Dict[str, object]] = []
    manifest_rows: List[Dict[str, object]] = []
    combined_frames = []

    if not plan_rows:
        status = STATUS_PLAN_MISSING
        validation_fail_count = 1
    elif not selected:
        status = STATUS_NO_APPROVED
        validation_fail_count = 1
    elif not args.dry_run and not args.allow_external_fetch:
        status = STATUS_FETCH_NOT_AUTH
        validation_fail_count = 1

    execute_fetch = bool(selected and not args.dry_run and args.allow_external_fetch and status == STATUS_OK)
    if args.dry_run or not execute_fetch:
        for row in selected:
            fetch_rows.append(
                {
                    "ticker": row["ticker"],
                    "priority_rank": row["priority_rank"],
                    "provider": args.provider,
                    "fetch_attempted": "FALSE",
                    "fetch_success": "FALSE",
                    "fetch_empty": "FALSE",
                    "fetch_failed": "FALSE",
                    "raw_row_count": 0,
                    "raw_path": "",
                    "fetch_timestamp": "",
                    "error_message": "DryRun/no-fetch planning only." if args.dry_run else "External fetch not executed.",
                }
            )
    else:
        ensure_dir(raw_dir)
        ensure_dir(normalized_dir)
        ensure_dir(manifest_dir)
        provider_import_error = ""
        if args.provider.lower() != "yfinance":
            provider_import_error = f"Unsupported provider: {args.provider}"
        else:
            try:
                import pandas as pd  # noqa: F401
                import yfinance  # noqa: F401

                configure_yfinance_cache(staged_dir / ".yfinance_cache")
            except Exception as exc:
                provider_import_error = f"{type(exc).__name__}: {exc}"
        for row in selected:
            ticker = str(row["ticker"])
            raw_path = raw_dir / f"{ticker}.csv"
            normalized_path = normalized_dir / f"{ticker}.csv"
            fetch_base = {
                "ticker": ticker,
                "priority_rank": row["priority_rank"],
                "provider": args.provider,
                "fetch_attempted": "TRUE",
                "fetch_success": "FALSE",
                "fetch_empty": "FALSE",
                "fetch_failed": "FALSE",
                "raw_row_count": 0,
                "raw_path": raw_path.as_posix(),
                "fetch_timestamp": fetch_timestamp,
                "error_message": "",
            }
            if provider_import_error:
                fetch_base["fetch_failed"] = "TRUE"
                fetch_base["error_message"] = provider_import_error
                fetch_rows.append(fetch_base)
                held_rows.append({"ticker": ticker, "priority_rank": row["priority_rank"], "classification": "FETCH_FAILED", "reason": "Provider unavailable.", "provider": args.provider, "error_message": provider_import_error})
                quality_rows.append(quality_from_normalized(ticker, None, 0, provider_import_error))
                quality_rows[-1]["quality_status"] = "FETCH_FAILED"
                continue
            try:
                raw_df = fetch_yfinance(ticker)
                raw_count = int(len(raw_df.index)) if raw_df is not None else 0
                fetch_base["raw_row_count"] = raw_count
                if raw_df is None or raw_df.empty:
                    fetch_base["fetch_empty"] = "TRUE"
                    fetch_base["error_message"] = "Provider returned empty history."
                    fetch_rows.append(fetch_base)
                    held_rows.append({"ticker": ticker, "priority_rank": row["priority_rank"], "classification": "EMPTY_FETCH", "reason": "Provider returned empty history.", "provider": args.provider, "error_message": ""})
                    quality_rows.append(quality_from_normalized(ticker, None, 0, "Provider returned empty history."))
                    continue
                raw_df.to_csv(raw_path)
                fetch_base["fetch_success"] = "TRUE"
                fetch_rows.append(fetch_base)
                try:
                    normalized_df, duplicate_before, norm_error = normalize_frame(raw_df, ticker, args.provider, run_id, fetch_timestamp)
                    if norm_error:
                        norm_rows.append({"ticker": ticker, "normalization_attempted": "TRUE", "normalization_success": "FALSE", "normalization_failed": "TRUE", "normalized_row_count": 0, "normalized_path": normalized_path.as_posix(), "duplicate_date_count_before_cleaning": duplicate_before, "duplicate_date_count_after_cleaning": "", "error_message": norm_error})
                        held_rows.append({"ticker": ticker, "priority_rank": row["priority_rank"], "classification": "NORMALIZATION_FAILED", "reason": "Normalization failed.", "provider": args.provider, "error_message": norm_error})
                        quality_rows.append(quality_from_normalized(ticker, None, duplicate_before, norm_error))
                        quality_rows[-1]["quality_status"] = "NORMALIZATION_FAILED"
                        continue
                    if normalized_df.empty:
                        norm_rows.append({"ticker": ticker, "normalization_attempted": "TRUE", "normalization_success": "FALSE", "normalization_failed": "TRUE", "normalized_row_count": 0, "normalized_path": normalized_path.as_posix(), "duplicate_date_count_before_cleaning": duplicate_before, "duplicate_date_count_after_cleaning": "", "error_message": "normalized history is empty"})
                        held_rows.append({"ticker": ticker, "priority_rank": row["priority_rank"], "classification": "EMPTY_FETCH", "reason": "Normalized history is empty.", "provider": args.provider, "error_message": ""})
                        quality_rows.append(quality_from_normalized(ticker, None, duplicate_before, "normalized history is empty"))
                        continue
                    normalized_df.to_csv(normalized_path, index=False)
                    duplicate_after = int(normalized_df.duplicated(subset=["date"]).sum())
                    norm_rows.append({"ticker": ticker, "normalization_attempted": "TRUE", "normalization_success": "TRUE", "normalization_failed": "FALSE", "normalized_row_count": len(normalized_df.index), "normalized_path": normalized_path.as_posix(), "duplicate_date_count_before_cleaning": duplicate_before, "duplicate_date_count_after_cleaning": duplicate_after, "error_message": ""})
                    quality = quality_from_normalized(ticker, normalized_df, duplicate_before)
                    quality_rows.append(quality)
                    if quality["quality_status"] != "FULL_HISTORY_READY":
                        held_rows.append({"ticker": ticker, "priority_rank": row["priority_rank"], "classification": quality["quality_status"], "reason": "Quality precheck did not classify as full-history ready.", "provider": args.provider, "error_message": ""})
                    combined_frames.append(normalized_df)
                except Exception as exc:
                    err = f"{type(exc).__name__}: {exc}"
                    norm_rows.append({"ticker": ticker, "normalization_attempted": "TRUE", "normalization_success": "FALSE", "normalization_failed": "TRUE", "normalized_row_count": 0, "normalized_path": normalized_path.as_posix(), "duplicate_date_count_before_cleaning": "", "duplicate_date_count_after_cleaning": "", "error_message": err})
                    held_rows.append({"ticker": ticker, "priority_rank": row["priority_rank"], "classification": "NORMALIZATION_FAILED", "reason": "Normalization exception.", "provider": args.provider, "error_message": err})
                    quality_rows.append(quality_from_normalized(ticker, None, 0, err))
                    quality_rows[-1]["quality_status"] = "NORMALIZATION_FAILED"
            except Exception as exc:
                err = f"{type(exc).__name__}: {exc}"
                fetch_base["fetch_failed"] = "TRUE"
                fetch_base["error_message"] = err
                fetch_rows.append(fetch_base)
                held_rows.append({"ticker": ticker, "priority_rank": row["priority_rank"], "classification": "FETCH_FAILED", "reason": "Fetch exception.", "provider": args.provider, "error_message": err})
                quality_rows.append(quality_from_normalized(ticker, None, 0, err))
                quality_rows[-1]["quality_status"] = "FETCH_FAILED"
        try:
            if combined_frames:
                import pandas as pd

                combined = pd.concat(combined_frames, ignore_index=True).sort_values(["ticker", "date"]).reset_index(drop=True)
                combined.to_csv(combined_path, index=False)
        except Exception as exc:
            validation_fail_count += 1
            held_rows.append({"ticker": "ALL", "priority_rank": "", "classification": "REVIEW_NEEDED", "reason": "Combined normalized write failed.", "provider": args.provider, "error_message": traceback.format_exc(limit=1) or str(exc)})

    for q in quality_rows:
        ticker = str(q.get("ticker", ""))
        raw_path = raw_dir / f"{ticker}.csv"
        norm_path = normalized_dir / f"{ticker}.csv"
        manifest_rows.extend(
            [
                {"ticker": ticker, "file_type": "raw", "relative_path": rel_path(root, raw_path), "exists": str(raw_path.exists()).upper(), "row_count": next((r.get("raw_row_count", 0) for r in fetch_rows if r.get("ticker") == ticker), 0), "notes": q.get("quality_status", "")},
                {"ticker": ticker, "file_type": "normalized", "relative_path": rel_path(root, norm_path), "exists": str(norm_path.exists()).upper(), "row_count": q.get("row_count", 0), "notes": q.get("quality_status", "")},
            ]
        )
    manifest_rows.append({"ticker": "ALL", "file_type": "combined_normalized", "relative_path": rel_path(root, combined_path), "exists": str(combined_path.exists()).upper(), "row_count": sum(to_int(q.get("row_count")) for q in quality_rows), "notes": "Combined normalized R23B staged history."})

    if execute_fetch:
        write_csv(root / STAGED_MANIFEST, manifest_rows, MANIFEST_FIELDS)
    write_csv(root / OUT_FETCH, fetch_rows, FETCH_FIELDS)
    write_csv(root / OUT_NORM, norm_rows, NORM_FIELDS)
    write_csv(root / OUT_MANIFEST, manifest_rows, MANIFEST_FIELDS)
    write_csv(root / OUT_QUALITY, quality_rows, QUALITY_FIELDS)
    write_csv(root / OUT_HELD, held_rows, HELD_FIELDS)

    fetch_attempt = sum(1 for row in fetch_rows if row.get("fetch_attempted") == "TRUE")
    fetch_success = sum(1 for row in fetch_rows if row.get("fetch_success") == "TRUE")
    fetch_empty = sum(1 for row in fetch_rows if row.get("fetch_empty") == "TRUE")
    fetch_fail = sum(1 for row in fetch_rows if row.get("fetch_failed") == "TRUE")
    norm_success = sum(1 for row in norm_rows if row.get("normalization_success") == "TRUE")
    norm_fail = sum(1 for row in norm_rows if row.get("normalization_failed") == "TRUE")
    full_count = sum(1 for row in quality_rows if row.get("quality_status") == "FULL_HISTORY_READY")
    partial_count = sum(1 for row in quality_rows if row.get("quality_status") == "PARTIAL_HISTORY_HOLD")
    review_count = sum(1 for row in quality_rows if row.get("quality_status") == "REVIEW_NEEDED")
    raw_count = len(list(raw_dir.glob("*.csv"))) if raw_dir.exists() else 0
    norm_count = len(list(normalized_dir.glob("*.csv"))) if normalized_dir.exists() else 0
    combined_created = combined_path.exists()

    if execute_fetch:
        if fetch_fail or fetch_empty or norm_fail:
            status = STATUS_PARTIAL_FETCH
        elif review_count:
            status = STATUS_REVIEW
        elif full_count == 0:
            status = STATUS_ZERO_FULL
        else:
            status = STATUS_OK

    price_modified = tree_sig(root / PRICE_CACHE) != price_before
    ledger_modified = file_sig(root / LEDGER) != ledger_before
    factor_modified = tree_sig(root / "outputs" / "v18" / "factor_pack") != factor_before
    tech_modified = tree_sig(root / "outputs" / "v18" / "technical_timing") != tech_before
    tiers_modified = tree_sig(root / "outputs" / "v18" / "tiers") != tiers_before
    decision_modified = tree_sig(root / "outputs" / "v18" / "daily_decision") != decision_before
    staged_modified = tree_sig(staged_dir) != staged_before
    forbidden_modified = price_modified or ledger_modified or factor_modified or tech_modified or tiers_modified or decision_modified

    values = {
        "STATUS": status,
        "MODE": mode,
        "RUN_ID": run_id,
        "PROVIDER": args.provider,
        "ALLOW_EXTERNAL_FETCH": str(args.allow_external_fetch).upper(),
        "PLAN_PATH": PLAN_PATH,
        "STAGED_OUTPUT_DIR": STAGED_DIR,
        "MAX_TICKERS": args.max_tickers,
        "R23_APPROVED_EXPECTED_COUNT": approved_expected,
        "SELECTED_TICKER_COUNT": len(selected),
        "ALREADY_HAS_LOCAL_CACHE_NOW_COUNT": sum(1 for row in held_rows if row.get("classification") == "ALREADY_HAS_LOCAL_CACHE_NOW"),
        "FETCH_ATTEMPT_COUNT": fetch_attempt,
        "FETCH_SUCCESS_COUNT": fetch_success,
        "FETCH_EMPTY_COUNT": fetch_empty,
        "FETCH_FAIL_COUNT": fetch_fail,
        "NORMALIZATION_SUCCESS_COUNT": norm_success,
        "NORMALIZATION_FAIL_COUNT": norm_fail,
        "FULL_HISTORY_READY_COUNT": full_count,
        "PARTIAL_HISTORY_HOLD_COUNT": partial_count,
        "QUALITY_REVIEW_NEEDED_COUNT": review_count,
        "HELD_OUT_OR_FAILED_COUNT": len(held_rows),
        "RAW_FILE_COUNT": raw_count,
        "NORMALIZED_FILE_COUNT": norm_count,
        "COMBINED_NORMALIZED_CREATED": str(combined_created).upper(),
        "MANIFEST_PATH": OUT_MANIFEST,
        "FETCH_RESULT_PATH": OUT_FETCH,
        "NORMALIZATION_RESULT_PATH": OUT_NORM,
        "QUALITY_PRECHECK_PATH": OUT_QUALITY,
        "HELD_OUT_OR_FAILED_PATH": OUT_HELD,
        "OFFICIAL_PRICE_CACHE_INTEGRATION_ALLOWED_NOW": "FALSE",
        "QUALITY_GATE_REQUIRED_NEXT": "TRUE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": str(fetch_attempt > 0).upper(),
        "BACKTEST_EXECUTED": "FALSE",
        "PRICE_CACHE_MODIFIED": str(price_modified).upper(),
        "ROLLING_LEDGER_MODIFIED": str(ledger_modified).upper(),
        "FACTOR_PACK_MODIFIED": str(factor_modified).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(tech_modified).upper(),
        "TIER_FILES_MODIFIED": str(tiers_modified).upper(),
        "OFFICIAL_DECISION_MODIFIED": str(decision_modified).upper(),
        "STAGED_BACKFILL_RAW_MODIFIED": str(staged_modified).upper(),
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": "R23C: Run staged quality gate and prepare official integration candidates only for full-history-ready staged files.",
    }
    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values))
    print(f"STATUS: {status}")
    print(f"MODE: {mode}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
