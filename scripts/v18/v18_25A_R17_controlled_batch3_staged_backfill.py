from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
import traceback
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R17_BATCH3_STAGED_BACKFILL_READY"
STATUS_WARN = "WARN_V18_25A_R17_BATCH3_STAGED_BACKFILL_READY"
STATUS_FAIL = "FAIL_V18_25A_R17_BATCH3_STAGED_BACKFILL"
MODE = "CONTROLLED_BATCH3_STAGED_BACKFILL_SELECTED_CANDIDATES_ONLY"
FETCH_PROVIDER = "yfinance"

R16_READ_FIRST = "outputs/v18/ops/V18_25A_R16_READ_FIRST.txt"
R16_CANDIDATES = "outputs/v18/staged_backfill/V18_25A_R16_CURRENT_BATCH3_CANDIDATE_PLAN.csv"
R16_HELD_OUT = "outputs/v18/staged_backfill/V18_25A_R16_CURRENT_BATCH3_HELD_OUT_REVIEW.csv"
R16_EXCLUDED = "outputs/v18/staged_backfill/V18_25A_R16_CURRENT_BATCH3_EXCLUDED_TICKERS.csv"
DEGRADED_DAILY = "outputs/v18/degraded_daily/V18_25A_CURRENT_DEGRADED_DAILY_OUTPUT.csv"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

STAGED_DIR = "data/v18/staged_backfill/V18_25A_BATCH3"
RAW_DIR = "data/v18/staged_backfill/V18_25A_BATCH3/raw"
NORMALIZED_DIR = "data/v18/staged_backfill/V18_25A_BATCH3/normalized"
COMBINED_NORMALIZED = "data/v18/staged_backfill/V18_25A_BATCH3/V18_25A_BATCH3_COMBINED_NORMALIZED.csv"
STAGED_MANIFEST = "data/v18/staged_backfill/V18_25A_BATCH3/MANIFEST.csv"

OUT_RESULT = "outputs/v18/staged_backfill/V18_25A_R17_CURRENT_BATCH3_STAGED_BACKFILL_RESULT.csv"
OUT_QUALITY = "outputs/v18/staged_backfill/V18_25A_R17_CURRENT_BATCH3_STAGED_BACKFILL_QUALITY_AUDIT.csv"
OUT_FETCH_MANIFEST = "outputs/v18/staged_backfill/V18_25A_R17_CURRENT_BATCH3_FETCH_MANIFEST.csv"
OUT_HELD_OUT = "outputs/v18/staged_backfill/V18_25A_R17_CURRENT_BATCH3_HELD_OUT_NOT_FETCHED.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R17_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R17_CURRENT_BATCH3_STAGED_BACKFILL_REPORT.md"

MIN_FULL_HISTORY_ROWS = 1000
MIN_PARTIAL_HISTORY_ROWS = 1
MARKET_PROXY_SYMBOLS = {"VIX", "^VIX", "SPY", "QQQ", "DIA", "IWM", "TLT", "GLD"}
NON_TICKER_ARTIFACTS = {"TICKERS", "SYMBOL", "SYMBOLS", "TICKER"}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R16_SOURCE_PATH",
    "STAGED_BATCH3_DIR",
    "BATCH3_CANDIDATE_COUNT",
    "FETCH_ATTEMPT_COUNT",
    "FETCH_SUCCESS_COUNT",
    "FETCH_FULL_HISTORY_READY_COUNT",
    "FETCH_PARTIAL_HISTORY_COUNT",
    "FETCH_EMPTY_COUNT",
    "FETCH_FAIL_COUNT",
    "NORMALIZATION_FAIL_COUNT",
    "QUALITY_REVIEW_NEEDED_COUNT",
    "HELD_OUT_NOT_FETCHED_COUNT",
    "RAW_FILE_COUNT",
    "NORMALIZED_FILE_COUNT",
    "COMBINED_NORMALIZED_CREATED",
    "EXTERNAL_DATA_FETCHED",
    "FETCH_PROVIDER",
    "OFFICIAL_PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "OFFICIAL_MARKET_PROXY_MODIFIED",
    "STAGED_MARKET_PROXY_MODIFIED",
    "STAGED_STOCK_BACKFILL_MODIFIED",
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
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_FILE_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]

QUALITY_FIELDS = [
    "ticker",
    "fetch_attempted",
    "fetch_success",
    "fetch_empty",
    "fetch_fail",
    "raw_row_count",
    "normalized_row_count",
    "min_date",
    "max_date",
    "latest_date",
    "close_column_available",
    "close_non_null_count",
    "duplicate_date_count_before_cleaning",
    "duplicate_date_count_after_cleaning",
    "negative_or_zero_close_count",
    "suspicious_gap_count",
    "full_history_ready",
    "price_only_partial",
    "quality_status",
    "staged_raw_path",
    "staged_normalized_path",
    "error_message",
]

RESULT_FIELDS = [
    "ticker",
    "candidate_priority_rank",
    "fetch_provider",
    "fetch_status",
    "quality_status",
    "raw_row_count",
    "normalized_row_count",
    "min_date",
    "max_date",
    "latest_date",
    "staged_raw_path",
    "staged_normalized_path",
    "error_message",
]

MANIFEST_FIELDS = ["ticker", "file_type", "relative_path", "exists", "row_count", "notes"]
HELD_OUT_FIELDS = ["ticker", "hold_reason", "classification", "not_fetched_reason"]


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


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


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


def is_true(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value).strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def rel_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def snapshot_forbidden(root: Path, allowed_staged_dir: Path) -> Dict[str, Tuple[int, int]]:
    forbidden = [
        root / "state/v18/price_cache",
        root / "data/v18/price_history",
        root / "data/v18/staged_backfill",
        root / "state/v18/market_proxy_cache",
        root / "data/v18/staged_market_proxy",
        root / "state/v18/rolling_coverage",
        root / "outputs/v18/factor_pack",
        root / "outputs/v18/technical_timing",
        root / "outputs/v18/tier_migration",
        root / "outputs/v18/degraded_daily",
        root / "outputs/v18/official_daily_decision",
        root / "outputs/v18/daily_decision",
        root / "state/v18/official_daily_decision",
    ]
    out: Dict[str, Tuple[int, int]] = {}
    for base in forbidden:
        if not base.exists():
            continue
        paths = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
        for path in paths:
            try:
                path.resolve().relative_to(allowed_staged_dir.resolve())
                continue
            except ValueError:
                pass
            stat = path.stat()
            out[rel_path(root, path)] = (int(stat.st_mtime_ns), int(stat.st_size))
    return out


def changed_paths(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    paths = sorted(set(before) | set(after))
    return [path for path in paths if before.get(path) != after.get(path)]


def parse_date(value: object) -> Optional[dt.date]:
    text = str(value or "").strip()[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def flatten_columns(df):
    if hasattr(df.columns, "to_flat_index"):
        flat = []
        for col in df.columns.to_flat_index():
            if isinstance(col, tuple):
                parts = [str(part) for part in col if str(part) and str(part) != "None"]
                flat.append("_".join(parts))
            else:
                flat.append(str(col))
        df = df.copy()
        df.columns = flat
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


def normalize_frame(raw_df, ticker: str, source: str):
    import pandas as pd

    df = flatten_columns(raw_df)
    if df is None or df.empty:
        return pd.DataFrame(), 0, "empty dataframe"
    df = df.copy()
    if "Date" not in df.columns and "date" not in [str(c).lower() for c in df.columns]:
        df = df.reset_index()
    rename = {col: standard_col_name(str(col), ticker) for col in df.columns}
    df = df.rename(columns=rename)
    if "date" not in df.columns:
        return pd.DataFrame(), 0, "date column missing"

    keep = [col for col in ["date", "open", "high", "low", "close", "adj_close", "volume"] if col in df.columns]
    out = df[keep].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date
    out = out[out["date"].notna()].copy()
    for col in ["open", "high", "low", "close", "adj_close", "volume"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    duplicate_before = int(out.duplicated(subset=["date"]).sum())
    out = out.sort_values("date").drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
    out["ticker"] = ticker
    out["source"] = source
    cols = [col for col in ["date", "open", "high", "low", "close", "adj_close", "volume", "ticker", "source"] if col in out.columns]
    out = out[cols]
    return out, duplicate_before, ""


def suspicious_gap_count(dates: List[dt.date]) -> int:
    if len(dates) < 2:
        return 0
    count = 0
    for prev, curr in zip(dates, dates[1:]):
        if (curr - prev).days > 14:
            count += 1
    return count


def fetch_ticker(ticker: str):
    import yfinance as yf

    return yf.download(ticker, period="max", interval="1d", auto_adjust=False, progress=False, threads=False)


def configure_yfinance_cache(cache_dir: Path) -> None:
    ensure_dir(cache_dir)
    import yfinance as yf
    import yfinance.cache as yf_cache

    yf.set_tz_cache_location(str(cache_dir))
    yf_cache.set_cache_location(str(cache_dir))


def render_report(values: Dict[str, str], failed_sample: str) -> str:
    return f"""# V18.25A-R17 Controlled Batch3 Staged Backfill

Generated: {dt.datetime.now().isoformat(timespec="seconds")}

Status: {values['STATUS']}

Mode: {MODE}

Candidates: {values['BATCH3_CANDIDATE_COUNT']}

Fetch success: {values['FETCH_SUCCESS_COUNT']}

Full history ready: {values['FETCH_FULL_HISTORY_READY_COUNT']}

Partial history: {values['FETCH_PARTIAL_HISTORY_COUNT']}

Empty/fail: {values['FETCH_EMPTY_COUNT']} / {values['FETCH_FAIL_COUNT']}

Failed or empty sample: {failed_sample}

Staged directory: {values['STAGED_BATCH3_DIR']}

Next step: {values['NEXT_RECOMMENDED_STEP']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    staged_dir = root / STAGED_DIR
    raw_dir = root / RAW_DIR
    normalized_dir = root / NORMALIZED_DIR
    cache_dir = staged_dir / ".yfinance_cache"
    before_forbidden = snapshot_forbidden(root, staged_dir)

    r16 = parse_read_first(root / R16_READ_FIRST)
    candidate_rows, _ = read_csv(root / R16_CANDIDATES)
    held_out_rows, _ = read_csv(root / R16_HELD_OUT)
    daily_rows, _ = read_csv(root / DEGRADED_DAILY)

    held_out = {norm_ticker(row.get("ticker")) for row in held_out_rows}
    high_trust = {
        norm_ticker(row.get("ticker"))
        for row in daily_rows
        if str(row.get("trust_level", "")).upper() == "HIGH"
        or str(row.get("output_bucket", "")).upper().startswith("HIGH_TRUST")
    }

    candidates = [row for row in candidate_rows if is_true(row.get("batch3_candidate"))]
    tickers = [norm_ticker(row.get("ticker")) for row in candidates]
    candidate_priority = {norm_ticker(row.get("ticker")): row.get("batch3_priority_rank", row.get("priority_rank", "")) for row in candidates}

    validation_failures: List[str] = []
    if r16.get("STATUS") != "OK_V18_25A_R16_BATCH3_CANDIDATE_SELECTION_PLAN_READY":
        validation_failures.append("R16 status is not OK.")
    if not (root / R16_CANDIDATES).exists():
        validation_failures.append("R16 candidate source file is missing.")
    if len(tickers) > 65:
        validation_failures.append("Candidate count exceeds 65.")
    if len(set(tickers)) != len(tickers):
        validation_failures.append("Candidate tickers are not unique.")
    illegal = sorted(set(tickers) & (held_out | high_trust | MARKET_PROXY_SYMBOLS))
    if illegal:
        validation_failures.append("Illegal candidate tickers present: " + ",".join(illegal[:12]))
    non_ticker_artifacts = sorted(set(tickers) & NON_TICKER_ARTIFACTS)

    ensure_dir(raw_dir)
    ensure_dir(normalized_dir)

    quality_rows: List[Dict[str, object]] = []
    result_rows: List[Dict[str, object]] = []
    manifest_rows: List[Dict[str, object]] = []
    combined_frames = []

    provider_import_ok = True
    provider_import_error = ""
    try:
        import pandas as pd  # noqa: F401
        import yfinance  # noqa: F401
        configure_yfinance_cache(cache_dir)
    except Exception as exc:
        provider_import_ok = False
        provider_import_error = str(exc)
        validation_failures.append("Provider import failed: " + provider_import_error)

    for ticker in tickers:
        raw_path = raw_dir / f"{ticker}.csv"
        normalized_path = normalized_dir / f"{ticker}.csv"
        row_base = {
            "ticker": ticker,
            "fetch_attempted": "TRUE",
            "fetch_success": "FALSE",
            "fetch_empty": "FALSE",
            "fetch_fail": "FALSE",
            "raw_row_count": 0,
            "normalized_row_count": 0,
            "min_date": "",
            "max_date": "",
            "latest_date": "",
            "close_column_available": "FALSE",
            "close_non_null_count": 0,
            "duplicate_date_count_before_cleaning": 0,
            "duplicate_date_count_after_cleaning": 0,
            "negative_or_zero_close_count": 0,
            "suspicious_gap_count": 0,
            "full_history_ready": "FALSE",
            "price_only_partial": "FALSE",
            "quality_status": "FETCH_FAIL",
            "staged_raw_path": str(raw_path),
            "staged_normalized_path": str(normalized_path),
            "error_message": "",
        }
        if validation_failures or not provider_import_ok:
            row_base["fetch_fail"] = "TRUE"
            row_base["error_message"] = "; ".join(validation_failures) or provider_import_error
            quality_rows.append(dict(row_base))
            continue
        if ticker in NON_TICKER_ARTIFACTS:
            row_base["fetch_attempted"] = "FALSE"
            row_base["fetch_fail"] = "TRUE"
            row_base["quality_status"] = "QUALITY_REVIEW_NEEDED"
            row_base["error_message"] = "non-ticker artifact from R16 candidate plan; not fetched"
            quality_rows.append(dict(row_base))
            continue
        try:
            raw_df = fetch_ticker(ticker)
            raw_row_count = int(len(raw_df.index)) if raw_df is not None else 0
            row_base["raw_row_count"] = raw_row_count
            if raw_df is None or raw_df.empty:
                row_base["fetch_empty"] = "TRUE"
                row_base["quality_status"] = "FETCH_EMPTY"
                row_base["error_message"] = "provider returned empty history"
                quality_rows.append(dict(row_base))
                continue

            ensure_dir(raw_path.parent)
            raw_df.to_csv(raw_path)
            normalized_df, duplicate_before, norm_error = normalize_frame(raw_df, ticker, FETCH_PROVIDER)
            row_base["duplicate_date_count_before_cleaning"] = duplicate_before
            if norm_error:
                row_base["fetch_success"] = "TRUE"
                row_base["quality_status"] = "NORMALIZATION_FAIL"
                row_base["error_message"] = norm_error
                quality_rows.append(dict(row_base))
                continue
            if normalized_df.empty:
                row_base["fetch_empty"] = "TRUE"
                row_base["quality_status"] = "FETCH_EMPTY"
                row_base["error_message"] = "normalized history is empty"
                quality_rows.append(dict(row_base))
                continue

            normalized_df.to_csv(normalized_path, index=False)
            dates = [parse_date(value) for value in normalized_df["date"].tolist()]
            clean_dates = [value for value in dates if value is not None]
            close_available = "close" in normalized_df.columns
            close_non_null = int(normalized_df["close"].notna().sum()) if close_available else 0
            negative_close = int((normalized_df["close"] <= 0).sum()) if close_available else 0
            duplicate_after = int(normalized_df.duplicated(subset=["date"]).sum())
            gaps = suspicious_gap_count(clean_dates)
            normalized_count = int(len(normalized_df.index))
            min_date = min(clean_dates).isoformat() if clean_dates else ""
            max_date = max(clean_dates).isoformat() if clean_dates else ""
            latest_date = max_date
            full_history_ready = normalized_count >= MIN_FULL_HISTORY_ROWS and close_available and close_non_null > 0 and negative_close == 0
            partial = normalized_count >= MIN_PARTIAL_HISTORY_ROWS and not full_history_ready
            if full_history_ready:
                quality_status = "FETCH_SUCCESS_FULL_HISTORY"
            elif partial:
                quality_status = "FETCH_SUCCESS_PARTIAL_HISTORY"
            else:
                quality_status = "QUALITY_REVIEW_NEEDED"

            row_base.update({
                "fetch_success": "TRUE",
                "normalized_row_count": normalized_count,
                "min_date": min_date,
                "max_date": max_date,
                "latest_date": latest_date,
                "close_column_available": str(close_available).upper(),
                "close_non_null_count": close_non_null,
                "duplicate_date_count_after_cleaning": duplicate_after,
                "negative_or_zero_close_count": negative_close,
                "suspicious_gap_count": gaps,
                "full_history_ready": str(full_history_ready).upper(),
                "price_only_partial": str(partial).upper(),
                "quality_status": quality_status,
            })
            if gaps > 0 or negative_close > 0 or not close_available:
                row_base["quality_status"] = "QUALITY_REVIEW_NEEDED"
            quality_rows.append(dict(row_base))
            combined_frames.append(normalized_df)
        except Exception as exc:
            row_base["fetch_fail"] = "TRUE"
            row_base["quality_status"] = "FETCH_FAIL"
            row_base["error_message"] = f"{type(exc).__name__}: {exc}"
            quality_rows.append(dict(row_base))

    try:
        if combined_frames:
            import pandas as pd

            combined = pd.concat(combined_frames, ignore_index=True)
            combined = combined.sort_values(["ticker", "date"]).reset_index(drop=True)
            ensure_dir((root / COMBINED_NORMALIZED).parent)
            combined.to_csv(root / COMBINED_NORMALIZED, index=False)
    except Exception:
        validation_failures.append("Combined normalized write failed: " + traceback.format_exc(limit=1))

    for q in quality_rows:
        result_rows.append({
            "ticker": q["ticker"],
            "candidate_priority_rank": candidate_priority.get(str(q["ticker"]), ""),
            "fetch_provider": FETCH_PROVIDER,
            "fetch_status": q["quality_status"],
            "quality_status": q["quality_status"],
            "raw_row_count": q["raw_row_count"],
            "normalized_row_count": q["normalized_row_count"],
            "min_date": q["min_date"],
            "max_date": q["max_date"],
            "latest_date": q["latest_date"],
            "staged_raw_path": q["staged_raw_path"],
            "staged_normalized_path": q["staged_normalized_path"],
            "error_message": q["error_message"],
        })
        raw_path = Path(str(q["staged_raw_path"]))
        norm_path = Path(str(q["staged_normalized_path"]))
        manifest_rows.extend([
            {"ticker": q["ticker"], "file_type": "raw", "relative_path": rel_path(root, raw_path), "exists": str(raw_path.exists()).upper(), "row_count": q["raw_row_count"], "notes": q["quality_status"]},
            {"ticker": q["ticker"], "file_type": "normalized", "relative_path": rel_path(root, norm_path), "exists": str(norm_path.exists()).upper(), "row_count": q["normalized_row_count"], "notes": q["quality_status"]},
        ])

    combined_path = root / COMBINED_NORMALIZED
    combined_created = combined_path.exists()
    manifest_rows.append({
        "ticker": "ALL",
        "file_type": "combined_normalized",
        "relative_path": rel_path(root, combined_path),
        "exists": str(combined_created).upper(),
        "row_count": sum(to_int(row.get("normalized_row_count")) for row in quality_rows),
        "notes": "Combined normalized Batch3 staged history.",
    })

    held_out_not_fetched = [
        {
            "ticker": norm_ticker(row.get("ticker")),
            "hold_reason": row.get("hold_reason", ""),
            "classification": row.get("classification", ""),
            "not_fetched_reason": "R17 fetch is restricted to R16 selected Batch3 candidates only.",
        }
        for row in held_out_rows
    ]

    fetch_attempt = sum(1 for row in quality_rows if row["fetch_attempted"] == "TRUE")
    success_count = sum(1 for row in quality_rows if row["fetch_success"] == "TRUE")
    full_count = sum(1 for row in quality_rows if row["quality_status"] == "FETCH_SUCCESS_FULL_HISTORY")
    partial_count = sum(1 for row in quality_rows if row["quality_status"] == "FETCH_SUCCESS_PARTIAL_HISTORY")
    empty_count = sum(1 for row in quality_rows if row["fetch_empty"] == "TRUE")
    fail_count = sum(1 for row in quality_rows if row["fetch_fail"] == "TRUE")
    norm_fail_count = sum(1 for row in quality_rows if row["quality_status"] == "NORMALIZATION_FAIL")
    review_count = sum(1 for row in quality_rows if row["quality_status"] == "QUALITY_REVIEW_NEEDED")
    raw_file_count = len(list(raw_dir.glob("*.csv"))) if raw_dir.exists() else 0
    norm_file_count = len(list(normalized_dir.glob("*.csv"))) if normalized_dir.exists() else 0

    write_csv(root / OUT_RESULT, result_rows, RESULT_FIELDS)
    write_csv(root / OUT_QUALITY, quality_rows, QUALITY_FIELDS)
    write_csv(root / OUT_FETCH_MANIFEST, manifest_rows, MANIFEST_FIELDS)
    write_csv(root / STAGED_MANIFEST, manifest_rows, MANIFEST_FIELDS)
    write_csv(root / OUT_HELD_OUT, held_out_not_fetched, HELD_OUT_FIELDS)

    after_forbidden = snapshot_forbidden(root, staged_dir)
    modified_forbidden = changed_paths(before_forbidden, after_forbidden)
    forbidden_modified = bool(modified_forbidden)
    if forbidden_modified:
        validation_failures.append("Forbidden files modified: " + ";".join(modified_forbidden[:10]))
    if fetch_attempt != len(set(tickers)):
        if non_ticker_artifacts:
            validation_failures.append("Non-ticker artifacts skipped without fetch: " + ",".join(non_ticker_artifacts))
        else:
            validation_failures.append("Fetch attempt count does not match unique candidate tickers.")
    if not combined_created and success_count > 0:
        validation_failures.append("Combined normalized file was not created.")

    validation_fail_count = len(validation_failures)
    if validation_fail_count or not quality_rows:
        status = STATUS_FAIL if not quality_rows or success_count == 0 or forbidden_modified else STATUS_WARN
    elif empty_count or fail_count or norm_fail_count or review_count or partial_count:
        status = STATUS_WARN
    else:
        status = STATUS_OK

    failed_or_empty = [str(row["ticker"]) for row in quality_rows if row["fetch_empty"] == "TRUE" or row["fetch_fail"] == "TRUE" or row["quality_status"] == "NORMALIZATION_FAIL"]
    values = {
        "STATUS": status,
        "MODE": MODE,
        "R16_SOURCE_PATH": str(root / R16_READ_FIRST),
        "STAGED_BATCH3_DIR": str(staged_dir),
        "BATCH3_CANDIDATE_COUNT": str(len(tickers)),
        "FETCH_ATTEMPT_COUNT": str(fetch_attempt),
        "FETCH_SUCCESS_COUNT": str(success_count),
        "FETCH_FULL_HISTORY_READY_COUNT": str(full_count),
        "FETCH_PARTIAL_HISTORY_COUNT": str(partial_count),
        "FETCH_EMPTY_COUNT": str(empty_count),
        "FETCH_FAIL_COUNT": str(fail_count),
        "NORMALIZATION_FAIL_COUNT": str(norm_fail_count),
        "QUALITY_REVIEW_NEEDED_COUNT": str(review_count),
        "HELD_OUT_NOT_FETCHED_COUNT": str(len(held_out_not_fetched)),
        "RAW_FILE_COUNT": str(raw_file_count),
        "NORMALIZED_FILE_COUNT": str(norm_file_count),
        "COMBINED_NORMALIZED_CREATED": str(combined_created).upper(),
        "EXTERNAL_DATA_FETCHED": str(success_count > 0).upper(),
        "FETCH_PROVIDER": FETCH_PROVIDER,
        "OFFICIAL_PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "OFFICIAL_MARKET_PROXY_MODIFIED": "FALSE",
        "STAGED_MARKET_PROXY_MODIFIED": "FALSE",
        "STAGED_STOCK_BACKFILL_MODIFIED": "TRUE",
        "LEDGER_MODIFIED": "FALSE",
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
        "VALIDATION_FAIL_COUNT": str(validation_fail_count),
        "FORBIDDEN_FILE_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": "Review R17 staged quality audit, then run a separate Batch3 staged quality/integration gate.",
    }
    failed_sample = ", ".join(failed_or_empty[:12])
    write_text(root / OUT_REPORT, render_report(values, failed_sample))
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if status != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
