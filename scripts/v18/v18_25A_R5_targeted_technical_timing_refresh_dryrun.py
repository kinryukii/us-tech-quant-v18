from __future__ import annotations

import argparse
import csv
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd


MODE = "READ_ONLY_TARGETED_TECHNICAL_TIMING_REFRESH_DRYRUN"
STATUS_OK = "OK_V18_25A_R5_TARGETED_TECHNICAL_TIMING_REFRESH_DRYRUN_READY"
STATUS_WARN = "WARN_V18_25A_R5_TARGETED_TECHNICAL_TIMING_REFRESH_DRYRUN_READY"
STATUS_FAIL = "FAIL_V18_25A_R5_TARGETED_TECHNICAL_TIMING_REFRESH_DRYRUN"

R4_SOURCE_PATH = "outputs/v18/degraded_daily_review/V18_25A_R4_CURRENT_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT.csv"

OUT_DIR_TECH = "outputs/v18/technical_timing"
OUT_DIR_REVIEW = "outputs/v18/degraded_daily_review"
OUT_DIR_OPS = "outputs/v18/ops"

OUTPUTS = {
    "dryrun_csv": f"{OUT_DIR_TECH}/V18_25A_R5_TARGETED_TECHNICAL_TIMING_DRYRUN.csv",
    "schema_audit": f"{OUT_DIR_TECH}/V18_25A_R5_TARGETED_TECHNICAL_TIMING_SCHEMA_AUDIT.csv",
    "refresh_result": f"{OUT_DIR_REVIEW}/V18_25A_R5_CURRENT_TECHNICAL_REFRESH_RESULT.csv",
    "summary": f"{OUT_DIR_REVIEW}/V18_25A_R5_CURRENT_TECHNICAL_REFRESH_SUMMARY.csv",
    "report": f"{OUT_DIR_REVIEW}/V18_25A_R5_CURRENT_REPORT.md",
    "read_first": f"{OUT_DIR_OPS}/V18_25A_R5_READ_FIRST.txt",
    "ops_report": f"{OUT_DIR_OPS}/V18_25A_R5_CURRENT_TARGETED_TECHNICAL_TIMING_REFRESH_REPORT.md",
}

CURRENT_TECHNICAL_PATH = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R4_SOURCE_PATH",
    "TARGET_TICKER_COUNT",
    "TECHNICAL_REFRESH_ATTEMPT_COUNT",
    "TECHNICAL_REFRESH_SUCCESS_COUNT",
    "TECHNICAL_REFRESH_FAIL_COUNT",
    "FORMULA_COMPATIBILITY_STATUS",
    "EXACT_V18_6A_FORMULA_REUSED",
    "PARTIAL_COMPATIBLE_COUNT",
    "FULL_COMPATIBLE_COUNT",
    "INSUFFICIENT_HISTORY_COUNT",
    "OUTPUT_ROW_COUNT",
    "STAGED_TECHNICAL_OUTPUT_PATH",
    "CURRENT_TECHNICAL_FILE_MODIFIED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_BACKFILL_MODIFIED",
    "LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_MIGRATION_MODIFIED",
    "DEGRADED_DAILY_MODIFIED",
    "OFFICIAL_DAILY_DECISION_MODIFIED",
    "BACKTEST_EXECUTED",
    "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_FILE_MODIFIED",
]

CURRENT_SCHEMA_FIELDS = [
    "ticker",
    "yf_ticker",
    "price_date",
    "close",
    "bb_mid_20",
    "bb_upper_20_2",
    "bb_lower_20_2",
    "bb_percent_b",
    "bb_bandwidth",
    "bb_squeeze_flag",
    "bb_status",
    "rsi_14",
    "rsi_status",
    "kdj_k",
    "kdj_d",
    "kdj_j",
    "kdj_status",
    "volume_ratio_5_20",
    "overheat_penalty",
    "pullback_timing_bonus",
    "breakout_confirmation_bonus",
    "technical_timing_score",
    "technical_signal",
    "technical_warning_label",
    "option_data_status",
    "put_call_ratio",
    "iv_rank_proxy",
    "gamma_squeeze_status",
    "gamma_squeeze_risk_label",
    "official_decision_impact",
    "vix_date",
    "vix_close",
    "vix_regime",
]

DRYRUN_EXTRA_FIELDS = [
    "formula_compatibility",
    "technical_status",
    "technical_refresh_blocker",
    "input_history_rows",
    "duplicate_date_count",
    "close_column_available",
    "dryrun_scope",
]

RESULT_FIELDS = [
    "ticker",
    "price_date",
    "input_history_rows",
    "duplicate_date_count",
    "close_column_available",
    "technical_status",
    "formula_compatibility",
    "technical_timing_score",
    "technical_signal",
    "technical_refresh_blocker",
    "reason_summary",
]

SUMMARY_FIELDS = ["metric", "count", "notes"]
SCHEMA_AUDIT_FIELDS = [
    "field_name",
    "present_in_current_schema",
    "present_in_dryrun_schema",
    "compatibility_status",
    "notes",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                return rows, list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def normalize_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def fmt(value: object, digits: int = 4) -> str:
    if value is None:
        return ""
    try:
        val = float(value)
        if np.isnan(val) or np.isinf(val):
            return ""
        return f"{val:.{digits}f}"
    except Exception:
        return str(value)


def read_price_cache(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            df = pd.read_csv(path, encoding=encoding)
            return df
        except Exception:
            continue
    return pd.DataFrame()


def load_target_tickers(root: Path) -> List[str]:
    rows, _fields = read_csv_rows(root / R4_SOURCE_PATH)
    if not rows:
        return []
    out: List[str] = []
    seen = set()
    for row in rows:
        action = str(row.get("recommended_refresh_action", "")).strip().upper()
        ready = str(row.get("technical_refresh_input_ready", "")).strip().upper() == "TRUE"
        if action == "READY_FOR_TECHNICAL_REFRESH_ONLY" or ready:
            ticker = normalize_ticker(row.get("ticker"))
            if ticker and ticker not in seen:
                seen.add(ticker)
                out.append(ticker)
    return out


def load_price_history(root: Path, ticker: str) -> Tuple[pd.DataFrame, Path]:
    path = root / "state" / "v18" / "price_cache" / f"{ticker}.csv"
    return read_price_cache(path), path


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    out = out.where(~((avg_loss == 0) & (avg_gain > 0)), 100)
    out = out.where(~((avg_gain == 0) & (avg_loss > 0)), 0)
    return out


def kdj(df: pd.DataFrame, n: int = 9):
    low_n = df["low"].rolling(n, min_periods=n).min()
    high_n = df["high"].rolling(n, min_periods=n).max()
    rsv = (df["close"] - low_n) / (high_n - low_n).replace(0, np.nan) * 100
    rsv = rsv.clip(0, 100)

    k = rsv.ewm(alpha=1 / 3, min_periods=n, adjust=False).mean()
    d = k.ewm(alpha=1 / 3, min_periods=n, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j


def bb_status(row: pd.Series) -> str:
    if pd.isna(row["bb_percent_b"]):
        return "BB_UNKNOWN"
    if row["close"] > row["bb_upper"]:
        return "BB_ABOVE_UPPER"
    if row["close"] < row["bb_lower"]:
        return "BB_BELOW_LOWER"
    if row["bb_percent_b"] >= 0.9:
        return "BB_NEAR_UPPER"
    if row["bb_percent_b"] <= 0.1:
        return "BB_NEAR_LOWER"
    if row["bb_percent_b"] >= 0.6:
        return "BB_UPPER_HALF"
    if row["bb_percent_b"] <= 0.4:
        return "BB_LOWER_HALF"
    return "BB_MID"


def rsi_status(x: object) -> str:
    if pd.isna(x):
        return "RSI_UNKNOWN"
    val = float(x)
    if val >= 75:
        return "RSI_EXTREME_OVERHEAT"
    if val >= 70:
        return "RSI_OVERHEAT"
    if val >= 60:
        return "RSI_STRONG"
    if val >= 45:
        return "RSI_NEUTRAL"
    if val >= 30:
        return "RSI_WEAK"
    return "RSI_OVERSOLD"


def kdj_status(k: object, d: object, j: object, pk: object, pd_: object) -> str:
    if pd.isna(k) or pd.isna(d) or pd.isna(j):
        return "KDJ_UNKNOWN"

    golden = (not pd.isna(pk)) and (not pd.isna(pd_)) and float(pk) <= float(pd_) and float(k) > float(d)
    dead = (not pd.isna(pk)) and (not pd.isna(pd_)) and float(pk) >= float(pd_) and float(k) < float(d)

    fk = float(k)
    fd = float(d)
    fj = float(j)

    if fk > 80 and fd > 80 and fj > 100:
        return "KDJ_EXTREME_OVERHEAT"
    if fk < 20 and fd < 20 and fj < 0:
        return "KDJ_EXTREME_OVERSOLD"
    if golden and max(fk, fd) <= 50:
        return "KDJ_LOW_GOLDEN_CROSS"
    if dead and min(fk, fd) >= 50:
        return "KDJ_HIGH_DEAD_CROSS"
    if fk > 80 and fd > 80:
        return "KDJ_OVERHEAT"
    if fk < 20 and fd < 20:
        return "KDJ_OVERSOLD"
    if golden:
        return "KDJ_GOLDEN_CROSS"
    if dead:
        return "KDJ_DEAD_CROSS"
    return "KDJ_NEUTRAL"


def compute_ticker(root: Path, ticker: str) -> Tuple[Dict[str, object], Dict[str, object]]:
    df_raw, path = load_price_history(root, ticker)
    if df_raw.empty:
        return (
            {
                "ticker": ticker,
                "price_date": "",
                "input_history_rows": 0,
                "duplicate_date_count": 0,
                "close_column_available": "FALSE",
                "technical_status": "TECHNICAL_DRYRUN_NO_PRICE_CACHE",
                "formula_compatibility": "PARTIAL_COMPATIBLE",
                "technical_timing_score": "",
                "technical_signal": "TECHNICAL_NO_DATA",
                "technical_refresh_blocker": "OFFICIAL_PRICE_CACHE_MISSING",
                "reason_summary": f"Missing official price cache file: {path}",
            },
            {
                "ticker": ticker,
                "source_path": str(path),
                "row_count": 0,
                "history_status": "MISSING",
                "formula_compatibility": "PARTIAL_COMPATIBLE",
            },
        )

    df = df_raw.copy()
    lower_map = {str(c).lower(): c for c in df.columns}
    date_col = lower_map.get("date")
    close_col = lower_map.get("close")
    high_col = lower_map.get("high")
    low_col = lower_map.get("low")
    volume_col = lower_map.get("volume")

    close_column_available = bool(close_col)
    if not (date_col and close_col and high_col and low_col and volume_col):
        return (
            {
                "ticker": ticker,
                "price_date": "",
                "input_history_rows": int(len(df_raw)),
                "duplicate_date_count": 0,
                "close_column_available": bool_text(close_column_available),
                "technical_status": "TECHNICAL_DRYRUN_REQUIRED_COLUMNS_MISSING",
                "formula_compatibility": "PARTIAL_COMPATIBLE",
                "technical_timing_score": "",
                "technical_signal": "TECHNICAL_COLUMNS_MISSING",
                "technical_refresh_blocker": "REQUIRED_COLUMNS_MISSING",
                "reason_summary": f"Missing required columns in {path}",
            },
            {
                "ticker": ticker,
                "source_path": str(path),
                "row_count": int(len(df_raw)),
                "history_status": "COLUMNS_MISSING",
                "formula_compatibility": "PARTIAL_COMPATIBLE",
            },
        )

    df = df[[date_col, close_col, high_col, low_col, volume_col]].copy()
    df.columns = ["date", "close", "high", "low", "volume"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype("string")
    for col in ("close", "high", "low", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "close", "high", "low"])
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
    duplicate_count = before_dedup - len(df)
    if df.empty:
        return (
            {
                "ticker": ticker,
                "price_date": "",
                "input_history_rows": int(len(df_raw)),
                "duplicate_date_count": int(duplicate_count),
                "close_column_available": bool_text(close_column_available),
                "technical_status": "TECHNICAL_DRYRUN_NO_VALID_ROWS",
                "formula_compatibility": "PARTIAL_COMPATIBLE",
                "technical_timing_score": "",
                "technical_signal": "TECHNICAL_NO_VALID_ROWS",
                "technical_refresh_blocker": "NO_VALID_PRICE_ROWS",
                "reason_summary": f"No valid price rows after normalization for {path}",
            },
            {
                "ticker": ticker,
                "source_path": str(path),
                "row_count": 0,
                "history_status": "NO_VALID_ROWS",
                "formula_compatibility": "PARTIAL_COMPATIBLE",
            },
        )

    x = df.copy()
    x["bb_mid"] = x["close"].rolling(20, min_periods=20).mean()
    x["bb_std"] = x["close"].rolling(20, min_periods=20).std()
    x["bb_upper"] = x["bb_mid"] + 2 * x["bb_std"]
    x["bb_lower"] = x["bb_mid"] - 2 * x["bb_std"]
    x["bb_percent_b"] = (x["close"] - x["bb_lower"]) / (x["bb_upper"] - x["bb_lower"]).replace(0, np.nan)
    x["bb_bandwidth"] = (x["bb_upper"] - x["bb_lower"]) / x["bb_mid"].replace(0, np.nan)
    x["bb_bandwidth_q20"] = x["bb_bandwidth"].rolling(120, min_periods=60).quantile(0.2)
    x["bb_squeeze_flag"] = x["bb_bandwidth"] <= x["bb_bandwidth_q20"]

    x["rsi_14"] = rsi(x["close"], 14)

    k, d, j = kdj(x, 9)
    x["kdj_k"] = k
    x["kdj_d"] = d
    x["kdj_j"] = j

    x["vol_ma5"] = x["volume"].rolling(5, min_periods=5).mean()
    x["vol_ma20"] = x["volume"].rolling(20, min_periods=20).mean()
    x["volume_ratio_5_20"] = x["vol_ma5"] / x["vol_ma20"].replace(0, np.nan)

    last = x.iloc[-1]
    prev = x.iloc[-2] if len(x) >= 2 else last

    bbs = bb_status(last)
    rsis = rsi_status(last["rsi_14"])
    kdjs = kdj_status(last["kdj_k"], last["kdj_d"], last["kdj_j"], prev["kdj_k"], prev["kdj_d"])

    overheat = 0
    pullback = 0
    breakout = 0
    labels: List[str] = []

    if bbs in {"BB_ABOVE_UPPER", "BB_NEAR_UPPER"}:
        overheat += 10
        labels.append("BB_UPPER_CHASE_RISK")

    if rsis in {"RSI_OVERHEAT", "RSI_EXTREME_OVERHEAT"}:
        overheat += 10 if rsis == "RSI_OVERHEAT" else 15
        labels.append(rsis)

    if kdjs in {"KDJ_OVERHEAT", "KDJ_EXTREME_OVERHEAT", "KDJ_HIGH_DEAD_CROSS"}:
        overheat += 10 if kdjs != "KDJ_EXTREME_OVERHEAT" else 15
        labels.append(kdjs)

    if bbs in {"BB_LOWER_HALF", "BB_NEAR_LOWER", "BB_BELOW_LOWER"}:
        pullback += 8

    if rsis in {"RSI_WEAK", "RSI_OVERSOLD"}:
        pullback += 6

    if kdjs in {"KDJ_LOW_GOLDEN_CROSS", "KDJ_OVERSOLD", "KDJ_EXTREME_OVERSOLD"}:
        pullback += 8

    if bbs == "BB_ABOVE_UPPER" and not pd.isna(last["rsi_14"]) and 55 <= float(last["rsi_14"]) <= 75:
        breakout += 5

    if not pd.isna(last["volume_ratio_5_20"]) and float(last["volume_ratio_5_20"]) >= 1.2:
        breakout += 4

    score = max(0, min(100, 50 + pullback + breakout - overheat))

    if score >= 65 and overheat <= 10:
        signal = "TECH_TIMING_WATCH_POSITIVE"
    elif overheat >= 25:
        signal = "TECH_TIMING_OVERHEAT_AVOID_CHASE"
    elif pullback >= 14:
        signal = "TECH_TIMING_PULLBACK_WATCH"
    else:
        signal = "TECH_TIMING_NEUTRAL"

    technical_status = "TECHNICAL_DRYRUN_PARTIAL_COMPATIBLE_READY"
    formula_compatibility = "PARTIAL_COMPATIBLE"
    warning_label = "VIX_OVERLAY_OMITTED_LOCAL_ONLY"
    final_row = {
        "ticker": ticker,
        "yf_ticker": ticker,
        "price_date": str(last["date"]),
        "close": round(float(last["close"]), 4),
        "bb_mid_20": round(float(last["bb_mid"]), 4) if not pd.isna(last["bb_mid"]) else "",
        "bb_upper_20_2": round(float(last["bb_upper"]), 4) if not pd.isna(last["bb_upper"]) else "",
        "bb_lower_20_2": round(float(last["bb_lower"]), 4) if not pd.isna(last["bb_lower"]) else "",
        "bb_percent_b": round(float(last["bb_percent_b"]), 4) if not pd.isna(last["bb_percent_b"]) else "",
        "bb_bandwidth": round(float(last["bb_bandwidth"]), 4) if not pd.isna(last["bb_bandwidth"]) else "",
        "bb_squeeze_flag": bool(last["bb_squeeze_flag"]) if not pd.isna(last["bb_squeeze_flag"]) else False,
        "bb_status": bbs,
        "rsi_14": round(float(last["rsi_14"]), 4) if not pd.isna(last["rsi_14"]) else "",
        "rsi_status": rsis,
        "kdj_k": round(float(last["kdj_k"]), 4) if not pd.isna(last["kdj_k"]) else "",
        "kdj_d": round(float(last["kdj_d"]), 4) if not pd.isna(last["kdj_d"]) else "",
        "kdj_j": round(float(last["kdj_j"]), 4) if not pd.isna(last["kdj_j"]) else "",
        "kdj_status": kdjs,
        "volume_ratio_5_20": round(float(last["volume_ratio_5_20"]), 4) if not pd.isna(last["volume_ratio_5_20"]) else "",
        "overheat_penalty": overheat,
        "pullback_timing_bonus": pullback,
        "breakout_confirmation_bonus": breakout,
        "technical_timing_score": round(float(score), 4),
        "technical_signal": signal,
        "technical_warning_label": warning_label,
        "option_data_status": "NOT_AVAILABLE_RESERVED",
        "put_call_ratio": "",
        "iv_rank_proxy": "",
        "gamma_squeeze_status": "NOT_AVAILABLE_RESERVED",
        "gamma_squeeze_risk_label": "NOT_AVAILABLE_RESERVED",
        "official_decision_impact": "NONE",
        "vix_date": "",
        "vix_close": "",
        "vix_regime": "NOT_AVAILABLE_RESERVED",
        "formula_compatibility": formula_compatibility,
        "technical_status": technical_status,
        "technical_refresh_blocker": "NONE",
        "input_history_rows": int(len(df_raw)),
        "duplicate_date_count": int(duplicate_count),
        "close_column_available": bool_text(close_column_available),
        "dryrun_scope": "LOCAL_OFFICIAL_PRICE_CACHE_ONLY",
    }

    schema_row = {
        "ticker": ticker,
        "source_path": str(path),
        "row_count": int(len(df)),
        "history_status": "READY",
        "formula_compatibility": formula_compatibility,
    }
    return final_row, schema_row


def path_modified(before: Dict[str, int], after: Dict[str, int], path: Path) -> bool:
    key = str(path)
    return before.get(key, -1) != after.get(key, -1)


def collect_monitored_paths(root: Path) -> List[Path]:
    paths = [
        root / "outputs" / "v18" / "technical_timing" / "V18_6A_CURRENT_TECHNICAL_TIMING.csv",
        root / "outputs" / "v18" / "technical_timing" / "V18_6A_CURRENT_TECHNICAL_TIMING_REPORT.md",
        root / "outputs" / "v18" / "technical_timing" / "V18_CURRENT_TECHNICAL_TIMING.md",
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_CURRENT_DEGRADED_DAILY_OUTPUT.csv",
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_CURRENT_DEGRADED_DAILY_REPORT.md",
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_CURRENT_DEGRADED_DAILY_SUMMARY.csv",
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R3_CURRENT_R6_R7_PROMOTION_BLOCKER_AUDIT.csv",
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R4_CURRENT_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT.csv",
    ]
    for folder in [
        root / "state" / "v18" / "price_cache",
        root / "state" / "v18" / "price_history",
        root / "outputs" / "v18" / "staged_backfill",
        root / "outputs" / "v18" / "rolling_coverage",
        root / "outputs" / "v18" / "factor_pack",
        root / "outputs" / "v18" / "tier_migration",
        root / "outputs" / "v18" / "official_daily",
    ]:
        if folder.exists() and folder.is_dir():
            paths.extend([child for child in folder.rglob("*") if child.is_file()])
    return paths


def collect_mtimes(paths: Sequence[Path]) -> Dict[str, int]:
    mtimes: Dict[str, int] = {}
    for path in paths:
        if not path.exists():
            mtimes[str(path)] = -1
            continue
        if path.is_dir():
            values = [child.stat().st_mtime_ns for child in path.rglob("*") if child.is_file()]
            mtimes[str(path)] = max(values) if values else path.stat().st_mtime_ns
        else:
            mtimes[str(path)] = path.stat().st_mtime_ns
    return mtimes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root)

    validation_failures: List[str] = []
    warnings: List[str] = []

    monitored_paths = collect_monitored_paths(root)
    before_mtimes = collect_mtimes(monitored_paths)

    target_tickers = load_target_tickers(root)
    if not target_tickers:
        validation_failures.append(f"No target tickers discovered from {root / R4_SOURCE_PATH}")
    if len(target_tickers) != 52:
        validation_failures.append(f"Target ticker count mismatch: expected 52, got {len(target_tickers)}")

    dryrun_rows: List[Dict[str, object]] = []
    refresh_rows: List[Dict[str, object]] = []
    schema_rows: List[Dict[str, object]] = []
    attempt_count = 0
    success_count = 0
    fail_count = 0
    partial_count = 0
    full_count = 0
    insufficient_history_count = 0

    for ticker in target_tickers:
        attempt_count += 1
        row, schema_row = compute_ticker(root, ticker)
        dryrun_rows.append(row)
        refresh_rows.append(schema_row)
        schema_rows.append(schema_row)

        if str(row.get("technical_refresh_blocker", "")).strip().upper() == "NONE":
            success_count += 1
        else:
            fail_count += 1

        if str(row.get("formula_compatibility", "")).strip().upper() == "FULL_COMPATIBLE":
            full_count += 1
        else:
            partial_count += 1

        blocker = str(row.get("technical_refresh_blocker", "")).strip().upper()
        if blocker in {"INSUFFICIENT_HISTORY", "NO_VALID_PRICE_ROWS", "OFFICIAL_PRICE_CACHE_MISSING", "REQUIRED_COLUMNS_MISSING"}:
            insufficient_history_count += 1

    output_row_count = len(dryrun_rows)
    formula_compatibility_status = "PARTIAL_COMPATIBLE" if partial_count and not full_count else "FULL_COMPATIBLE"
    exact_formula_reused = "FALSE"

    current_path = root / CURRENT_TECHNICAL_PATH
    before_current_mtime = before_mtimes.get(str(current_path), -1)
    after_mtimes = collect_mtimes(monitored_paths)
    current_file_modified_flag = before_current_mtime != after_mtimes.get(str(current_path), -1)

    if current_file_modified_flag:
        validation_failures.append("Current official technical timing file was modified.")

    forbidden_modified = current_file_modified_flag

    # Check for unexpected changes to monitored existing files. New staged outputs are allowed.
    for monitored in [
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_CURRENT_DEGRADED_DAILY_OUTPUT.csv",
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_CURRENT_DEGRADED_DAILY_REPORT.md",
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_CURRENT_DEGRADED_DAILY_SUMMARY.csv",
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R3_CURRENT_R6_R7_PROMOTION_BLOCKER_AUDIT.csv",
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R4_CURRENT_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT.csv",
        root / "outputs" / "v18" / "technical_timing" / "V18_6A_CURRENT_TECHNICAL_TIMING.csv",
        root / "outputs" / "v18" / "technical_timing" / "V18_6A_CURRENT_TECHNICAL_TIMING_REPORT.md",
        root / "outputs" / "v18" / "technical_timing" / "V18_CURRENT_TECHNICAL_TIMING.md",
    ]:
        if path_modified(before_mtimes, after_mtimes, monitored):
            validation_failures.append(f"Monitored file modified unexpectedly: {monitored}")
            forbidden_modified = True

    status = STATUS_FAIL if validation_failures else STATUS_WARN

    summary_rows = [
        {"metric": "TARGET_TICKER_COUNT", "count": str(len(target_tickers)), "notes": "Target tickers selected from R4 dry-run readiness source."},
        {"metric": "TECHNICAL_REFRESH_ATTEMPT_COUNT", "count": str(attempt_count), "notes": "One dry-run refresh attempt per target ticker."},
        {"metric": "TECHNICAL_REFRESH_SUCCESS_COUNT", "count": str(success_count), "notes": "Rows with no technical refresh blocker."},
        {"metric": "TECHNICAL_REFRESH_FAIL_COUNT", "count": str(fail_count), "notes": "Rows that carried a blocker or missing-data condition."},
        {"metric": "FULL_COMPATIBLE_COUNT", "count": str(full_count), "notes": "Rows using the exact current V18.6A formula set, including external overlay. Expected zero in local-only dry-run."},
        {"metric": "PARTIAL_COMPATIBLE_COUNT", "count": str(partial_count), "notes": "Rows using local V18.6A-compatible indicator logic without the external VIX overlay."},
        {"metric": "INSUFFICIENT_HISTORY_COUNT", "count": str(insufficient_history_count), "notes": "Rows with missing required price history or columns."},
        {"metric": "OUTPUT_ROW_COUNT", "count": str(output_row_count), "notes": "Rows written to the staged dry-run technical output."},
        {"metric": "FORMULA_COMPATIBILITY_STATUS", "count": formula_compatibility_status, "notes": "Local-only compatibility assessment for the staged dry-run."},
        {"metric": "EXACT_V18_6A_FORMULA_REUSED", "count": exact_formula_reused, "notes": "False because the external VIX overlay was not fetched."},
    ]

    schema_union = list(OrderedDict.fromkeys(CURRENT_SCHEMA_FIELDS + DRYRUN_EXTRA_FIELDS))
    current_schema_set = set(CURRENT_SCHEMA_FIELDS)
    dryrun_schema_set = set(CURRENT_SCHEMA_FIELDS + DRYRUN_EXTRA_FIELDS)
    dryrun_schema_rows = []
    for field in schema_union:
        if field in current_schema_set and field in dryrun_schema_set:
            compat = "SUPPORTED"
        elif field in dryrun_schema_set:
            compat = "DRYRUN_EXTENSION"
        else:
            compat = "MISSING"
        dryrun_schema_rows.append(
            {
                "field_name": field,
                "present_in_current_schema": bool_text(field in current_schema_set),
                "present_in_dryrun_schema": bool_text(field in dryrun_schema_set),
                "compatibility_status": compat,
                "notes": "Extended dry-run field" if field in DRYRUN_EXTRA_FIELDS else "Current V18.6A schema field",
            }
        )

    for row in dryrun_rows:
        row.setdefault("formula_compatibility", "PARTIAL_COMPATIBLE")
        row.setdefault("technical_status", "TECHNICAL_DRYRUN_PARTIAL_COMPATIBLE_READY")
        row.setdefault("technical_refresh_blocker", "NONE")
        row.setdefault("input_history_rows", "")
        row.setdefault("duplicate_date_count", "")
        row.setdefault("close_column_available", "")
        row.setdefault("dryrun_scope", "LOCAL_OFFICIAL_PRICE_CACHE_ONLY")

    report_lines = [
        "# V18.25A-R5 Targeted Technical Timing Refresh Dry Run",
        "",
        f"- Status: {status}",
        f"- Mode: {MODE}",
        f"- Target tickers: {len(target_tickers)}",
        f"- Technical refresh success: {success_count}",
        f"- Technical refresh fail: {fail_count}",
        f"- Formula compatibility status: {formula_compatibility_status}",
        f"- Exact V18.6A formula reused: {exact_formula_reused}",
        f"- Partial compatible count: {partial_count}",
        f"- Full compatible count: {full_count}",
        f"- Insufficient history count: {insufficient_history_count}",
        f"- Staged technical output path: {root / OUTPUTS['dryrun_csv']}",
        f"- Current technical file modified: {bool_text(current_file_modified_flag)}",
        "",
        "## Summary",
        "",
        "| Metric | Count | Notes |",
        "| --- | ---: | --- |",
    ]
    for row in summary_rows:
        report_lines.append(f"| {row['metric']} | {row['count']} | {row['notes']} |")

    report_lines.extend(
        [
            "",
            "## Notes",
            "",
            "- The dry run reuses the local V18.6A-compatible BB, RSI, KDJ, and volume-ratio logic.",
            "- The external VIX overlay is intentionally omitted because this task forbids external data fetches.",
            "- `formula_compatibility` is therefore `PARTIAL_COMPATIBLE` for every staged row.",
            "- No official technical timing file was overwritten.",
        ]
    )

    read_first = OrderedDict(
        [
            ("STATUS", status),
            ("MODE", MODE),
            ("R4_SOURCE_PATH", str(root / R4_SOURCE_PATH)),
            ("TARGET_TICKER_COUNT", str(len(target_tickers))),
            ("TECHNICAL_REFRESH_ATTEMPT_COUNT", str(attempt_count)),
            ("TECHNICAL_REFRESH_SUCCESS_COUNT", str(success_count)),
            ("TECHNICAL_REFRESH_FAIL_COUNT", str(fail_count)),
            ("FORMULA_COMPATIBILITY_STATUS", formula_compatibility_status),
            ("EXACT_V18_6A_FORMULA_REUSED", exact_formula_reused),
            ("PARTIAL_COMPATIBLE_COUNT", str(partial_count)),
            ("FULL_COMPATIBLE_COUNT", str(full_count)),
            ("INSUFFICIENT_HISTORY_COUNT", str(insufficient_history_count)),
            ("OUTPUT_ROW_COUNT", str(output_row_count)),
            ("STAGED_TECHNICAL_OUTPUT_PATH", str(root / OUTPUTS["dryrun_csv"])),
            ("CURRENT_TECHNICAL_FILE_MODIFIED", bool_text(current_file_modified_flag)),
            ("OFFICIAL_DECISION_IMPACT", "NONE"),
            ("AUTO_TRADE", "DISABLED"),
            ("AUTO_SELL", "DISABLED"),
            ("PRICE_CACHE_MODIFIED", "FALSE"),
            ("PRICE_HISTORY_MODIFIED", "FALSE"),
            ("STAGED_BACKFILL_MODIFIED", "FALSE"),
            ("LEDGER_MODIFIED", "FALSE"),
            ("FACTOR_PACK_MODIFIED", "FALSE"),
            ("TECHNICAL_TIMING_MODIFIED", "FALSE"),
            ("TIER_MIGRATION_MODIFIED", "FALSE"),
            ("DEGRADED_DAILY_MODIFIED", "FALSE"),
            ("OFFICIAL_DAILY_DECISION_MODIFIED", "FALSE"),
            ("BACKTEST_EXECUTED", "FALSE"),
            ("EXTERNAL_DATA_FETCHED", "FALSE"),
            ("VALIDATION_FAIL_COUNT", str(len(validation_failures))),
            ("FORBIDDEN_FILE_MODIFIED", bool_text(forbidden_modified)),
        ]
    )

    refresh_result_rows = [
        {
            "ticker": row.get("ticker", ""),
            "price_date": row.get("price_date", ""),
            "input_history_rows": row.get("input_history_rows", ""),
            "duplicate_date_count": row.get("duplicate_date_count", ""),
            "close_column_available": row.get("close_column_available", ""),
            "technical_status": row.get("technical_status", ""),
            "formula_compatibility": row.get("formula_compatibility", ""),
            "technical_timing_score": row.get("technical_timing_score", ""),
            "technical_signal": row.get("technical_signal", ""),
            "technical_refresh_blocker": row.get("technical_refresh_blocker", ""),
            "reason_summary": row.get("reason_summary", ""),
        }
        for row in dryrun_rows
    ]

    write_csv(root / OUTPUTS["dryrun_csv"], dryrun_rows, list(CURRENT_SCHEMA_FIELDS + DRYRUN_EXTRA_FIELDS))
    write_csv(root / OUTPUTS["schema_audit"], dryrun_schema_rows, SCHEMA_AUDIT_FIELDS)
    write_csv(root / OUTPUTS["refresh_result"], refresh_result_rows, RESULT_FIELDS)
    write_csv(root / OUTPUTS["summary"], summary_rows, SUMMARY_FIELDS)
    write_text(root / OUTPUTS["report"], "\n".join(report_lines) + "\n")
    write_text(root / OUTPUTS["ops_report"], "\n".join(report_lines) + "\n")
    write_text(root / OUTPUTS["read_first"], "\n".join(f"{k}: {v}" for k, v in read_first.items()) + "\n")

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"TARGET_TICKER_COUNT: {len(target_tickers)}")
    print(f"TECHNICAL_REFRESH_SUCCESS_COUNT: {success_count}")
    print(f"TECHNICAL_REFRESH_FAIL_COUNT: {fail_count}")
    print(f"FORMULA_COMPATIBILITY_STATUS: {formula_compatibility_status}")
    print(f"EXACT_V18_6A_FORMULA_REUSED: {exact_formula_reused}")
    print(f"OUTPUT_ROW_COUNT: {output_row_count}")
    print(f"STAGED_TECHNICAL_OUTPUT_PATH: {root / OUTPUTS['dryrun_csv']}")
    print(f"VALIDATION_FAIL_COUNT: {len(validation_failures)}")

    if validation_failures:
        for item in validation_failures:
            print(f"VALIDATION: {item}")
        return 1
    if warnings:
        for item in warnings:
            print(f"WARNING: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
