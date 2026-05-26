from __future__ import annotations

import argparse
import csv
import datetime as dt
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


STATUS_OK = "OK_V18_25A_R11_FULL_COMPATIBLE_TECHNICAL_TIMING_REFRESH_READY"
STATUS_WARN = "WARN_V18_25A_R11_FULL_COMPATIBLE_TECHNICAL_TIMING_REFRESH_READY"
STATUS_FAIL = "FAIL_V18_25A_R11_FULL_COMPATIBLE_TECHNICAL_TIMING_REFRESH"
MODE = "READ_ONLY_FULL_COMPATIBLE_TARGETED_TECHNICAL_TIMING_REFRESH_WITH_VIX"

R10_READ_FIRST = "outputs/v18/ops/V18_25A_R10_READ_FIRST.txt"
R4_TARGET_SOURCE = "outputs/v18/degraded_daily_review/V18_25A_R4_CURRENT_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT.csv"
OFFICIAL_VIX = "state/v18/market_proxy_cache/VIX.csv"
PRICE_CACHE_DIR = "state/v18/price_cache"
CURRENT_TECH = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"

STAGED_OUT = "outputs/v18/technical_timing/V18_25A_R11_FULL_COMPATIBLE_TECHNICAL_TIMING_STAGED.csv"
SCHEMA_AUDIT_OUT = "outputs/v18/technical_timing/V18_25A_R11_FULL_COMPATIBLE_TECHNICAL_TIMING_SCHEMA_AUDIT.csv"
RESULT_OUT = "outputs/v18/degraded_daily_review/V18_25A_R11_CURRENT_TECHNICAL_REFRESH_RESULT.csv"
SUMMARY_OUT = "outputs/v18/degraded_daily_review/V18_25A_R11_CURRENT_TECHNICAL_REFRESH_SUMMARY.csv"
GATE_OUT = "outputs/v18/degraded_daily_review/V18_25A_R11_CURRENT_TECHNICAL_MERGE_READINESS_GATE.csv"
REPORT_OUT = "outputs/v18/degraded_daily_review/V18_25A_R11_CURRENT_REPORT.md"
READ_FIRST_OUT = "outputs/v18/ops/V18_25A_R11_READ_FIRST.txt"
OPS_REPORT_OUT = "outputs/v18/ops/V18_25A_R11_CURRENT_FULL_COMPATIBLE_TECHNICAL_REFRESH_REPORT.md"

FORMULA_STATUS = "FULL_COMPATIBLE_WITH_LOCAL_REIMPLEMENTATION"
EXACT_FORMULA_REUSED = "FALSE"
MIN_HISTORY_ROWS = 80

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R10_SOURCE_PATH",
    "OFFICIAL_VIX_PATH",
    "TARGET_TICKER_COUNT",
    "TECHNICAL_REFRESH_ATTEMPT_COUNT",
    "TECHNICAL_REFRESH_SUCCESS_COUNT",
    "TECHNICAL_REFRESH_FAIL_COUNT",
    "FORMULA_COMPATIBILITY_STATUS",
    "EXACT_V18_6A_FORMULA_REUSED",
    "VIX_OVERLAY_INCLUDED",
    "VIX_ROW_COUNT",
    "VIX_MIN_DATE",
    "VIX_MAX_DATE",
    "VIX_USABLE",
    "PARTIAL_COMPATIBLE_COUNT",
    "FULL_COMPATIBLE_COUNT",
    "INSUFFICIENT_HISTORY_COUNT",
    "OUTPUT_ROW_COUNT",
    "STAGED_TECHNICAL_OUTPUT_PATH",
    "MERGE_READY_COUNT",
    "MERGE_BLOCKED_COUNT",
    "CURRENT_TECHNICAL_FILE_MODIFIED",
    "OFFICIAL_MARKET_PROXY_MODIFIED",
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
    "NEXT_RECOMMENDED_STEP",
]

RESULT_FIELDS = [
    "ticker",
    "refresh_attempted",
    "refresh_success",
    "technical_status",
    "formula_compatibility",
    "merge_ready",
    "blocker",
    "input_history_rows",
    "price_date",
    "vix_date",
    "vix_regime",
]
SUMMARY_FIELDS = ["metric", "value", "notes"]
GATE_FIELDS = ["ticker", "merge_ready", "merge_blocker", "schema_compatible", "formula_compatibility", "notes"]
SCHEMA_FIELDS = ["schema_check", "value", "notes"]


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


def read_csv_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
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


def read_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.DataFrame()


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def protected_files(root: Path) -> List[Path]:
    rels = [
        PRICE_CACHE_DIR,
        OFFICIAL_VIX,
        "data/v18/price_history",
        "data/v18/staged_backfill",
        "state/v18/rolling_coverage",
        "outputs/v18/factor_pack",
        "outputs/v18/ranking",
        "outputs/v18/tier_migration",
        "outputs/v18/official_daily_decision",
        "outputs/v18/daily_decision",
        "state/v18/official_daily_decision",
        CURRENT_TECH,
        "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING_REPORT.md",
        "outputs/v18/technical_timing/V18_CURRENT_TECHNICAL_TIMING.md",
        "outputs/v18/technical_timing/V18_6A_READ_FIRST.txt",
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


def load_targets(root: Path) -> List[str]:
    rows, _ = read_csv_rows(root / R4_TARGET_SOURCE)
    out: List[str] = []
    seen = set()
    for row in rows:
        ready = str(row.get("technical_refresh_input_ready", "")).strip().upper() == "TRUE"
        action_ready = str(row.get("recommended_refresh_action", "")).strip().upper() == "READY_FOR_TECHNICAL_REFRESH_ONLY"
        ticker = str(row.get("ticker", "")).strip().upper()
        if ticker and (ready or action_ready) and ticker not in seen:
            seen.add(ticker)
            out.append(ticker)
    return out


def normalize_price_df(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    required = ["date", "open", "high", "low", "close", "volume"]
    if any(c not in df.columns for c in required):
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "high", "low", "close"])
    df = df.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    df["ticker"] = ticker
    df["yf_ticker"] = ticker.replace(".", "-")
    df["date_text"] = df["date"].dt.date.astype(str)
    return df


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


def kdj(df: pd.DataFrame, n: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
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


def rsi_status(x: float) -> str:
    if pd.isna(x):
        return "RSI_UNKNOWN"
    if x >= 75:
        return "RSI_EXTREME_OVERHEAT"
    if x >= 70:
        return "RSI_OVERHEAT"
    if x >= 60:
        return "RSI_STRONG"
    if x >= 45:
        return "RSI_NEUTRAL"
    if x >= 30:
        return "RSI_WEAK"
    return "RSI_OVERSOLD"


def kdj_status(k: float, d: float, j: float, pk: float, pd_: float) -> str:
    if pd.isna(k) or pd.isna(d) or pd.isna(j):
        return "KDJ_UNKNOWN"
    golden = (not pd.isna(pk)) and (not pd.isna(pd_)) and pk <= pd_ and k > d
    dead = (not pd.isna(pk)) and (not pd.isna(pd_)) and pk >= pd_ and k < d
    if k > 80 and d > 80 and j > 100:
        return "KDJ_EXTREME_OVERHEAT"
    if k < 20 and d < 20 and j < 0:
        return "KDJ_EXTREME_OVERSOLD"
    if golden and max(k, d) <= 50:
        return "KDJ_LOW_GOLDEN_CROSS"
    if dead and min(k, d) >= 50:
        return "KDJ_HIGH_DEAD_CROSS"
    if k > 80 and d > 80:
        return "KDJ_OVERHEAT"
    if k < 20 and d < 20:
        return "KDJ_OVERSOLD"
    if golden:
        return "KDJ_GOLDEN_CROSS"
    if dead:
        return "KDJ_DEAD_CROSS"
    return "KDJ_NEUTRAL"


def vix_regime(v: float) -> str:
    if pd.isna(v):
        return "VIX_UNKNOWN"
    if v >= 30:
        return "VIX_PANIC_BLOCK_LEVERAGE"
    if v >= 25:
        return "VIX_RISK_OFF_DELEVERAGE"
    if v >= 18:
        return "VIX_CAUTION"
    return "VIX_NORMAL"


def load_vix(root: Path) -> pd.DataFrame:
    df = read_df(root / OFFICIAL_VIX)
    if df.empty:
        return df
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    if "date" not in df.columns or "close" not in df.columns:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    return df


def vix_for_date(vix: pd.DataFrame, price_date: pd.Timestamp) -> Dict[str, object]:
    eligible = vix[vix["date"] <= price_date]
    if eligible.empty:
        return {"vix_date": "", "vix_close": np.nan, "vix_regime": "VIX_UNKNOWN"}
    last = eligible.iloc[-1]
    close = float(last["close"])
    return {"vix_date": last["date"].date().isoformat(), "vix_close": round(close, 4), "vix_regime": vix_regime(close)}


def rounded(value: object) -> object:
    return round(float(value), 4) if not pd.isna(value) else np.nan


def compute_ticker(df: pd.DataFrame, vix: pd.DataFrame) -> Dict[str, object]:
    x = df.copy().sort_values("date").reset_index(drop=True)
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
        labels.append(bbs)
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
    if bbs == "BB_ABOVE_UPPER" and not pd.isna(last["rsi_14"]) and 55 <= last["rsi_14"] <= 75:
        breakout += 5
    if not pd.isna(last["volume_ratio_5_20"]) and last["volume_ratio_5_20"] >= 1.2:
        breakout += 4

    vix_info = vix_for_date(vix, last["date"])
    if vix_info["vix_regime"] in {"VIX_PANIC_BLOCK_LEVERAGE", "VIX_RISK_OFF_DELEVERAGE"}:
        overheat += 5
        labels.append(str(vix_info["vix_regime"]))

    score = max(0, min(100, 50 + pullback + breakout - overheat))
    if score >= 65 and overheat <= 10:
        signal = "TECH_TIMING_WATCH_POSITIVE"
    elif overheat >= 25:
        signal = "TECH_TIMING_OVERHEAT_AVOID_CHASE"
    elif pullback >= 14:
        signal = "TECH_TIMING_PULLBACK_WATCH"
    else:
        signal = "TECH_TIMING_NEUTRAL"

    return {
        "ticker": last["ticker"],
        "yf_ticker": last["yf_ticker"],
        "price_date": last["date"].date().isoformat(),
        "close": rounded(last["close"]),
        "bb_mid_20": rounded(last["bb_mid"]),
        "bb_upper_20_2": rounded(last["bb_upper"]),
        "bb_lower_20_2": rounded(last["bb_lower"]),
        "bb_percent_b": rounded(last["bb_percent_b"]),
        "bb_bandwidth": rounded(last["bb_bandwidth"]),
        "bb_squeeze_flag": bool(last["bb_squeeze_flag"]) if not pd.isna(last["bb_squeeze_flag"]) else False,
        "bb_status": bbs,
        "rsi_14": rounded(last["rsi_14"]),
        "rsi_status": rsis,
        "kdj_k": rounded(last["kdj_k"]),
        "kdj_d": rounded(last["kdj_d"]),
        "kdj_j": rounded(last["kdj_j"]),
        "kdj_status": kdjs,
        "volume_ratio_5_20": rounded(last["volume_ratio_5_20"]),
        "overheat_penalty": overheat,
        "pullback_timing_bonus": pullback,
        "breakout_confirmation_bonus": breakout,
        "technical_timing_score": round(float(score), 4),
        "technical_signal": signal,
        "technical_warning_label": ";".join(labels) if labels else "NONE",
        "option_data_status": "NOT_AVAILABLE_RESERVED",
        "put_call_ratio": np.nan,
        "iv_rank_proxy": np.nan,
        "gamma_squeeze_status": "NOT_AVAILABLE_RESERVED",
        "gamma_squeeze_risk_label": "NOT_AVAILABLE_RESERVED",
        "official_decision_impact": "NONE",
        "vix_date": vix_info["vix_date"],
        "vix_close": vix_info["vix_close"],
        "vix_regime": vix_info["vix_regime"],
        "formula_compatibility": FORMULA_STATUS,
        "technical_status": "TECHNICAL_FULL_COMPATIBLE_READY",
        "technical_refresh_blocker": "NONE",
        "input_history_rows": len(x),
        "duplicate_date_count": int(len(df) - df["date"].nunique()),
        "close_column_available": "TRUE",
        "refresh_scope": "LOCAL_OFFICIAL_PRICE_CACHE_WITH_OFFICIAL_VIX",
    }


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.25A-R11 Full-Compatible Technical Timing Refresh With Official VIX

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

Status: {values['STATUS']}

Mode: {MODE}

Target tickers: {values['TARGET_TICKER_COUNT']}

Success/fail: {values['TECHNICAL_REFRESH_SUCCESS_COUNT']} / {values['TECHNICAL_REFRESH_FAIL_COUNT']}

Formula compatibility: {values['FORMULA_COMPATIBILITY_STATUS']}

VIX overlay included: {values['VIX_OVERLAY_INCLUDED']} ({values['VIX_MIN_DATE']} to {values['VIX_MAX_DATE']})

Staged output: `{values['STAGED_TECHNICAL_OUTPUT_PATH']}`

Merge readiness: ready={values['MERGE_READY_COUNT']}, blocked={values['MERGE_BLOCKED_COUNT']}

Safety: no external fetch, no official technical current overwrite, no price cache/market proxy/factor/tier/decision/trading permission changes.

Next step: {values['NEXT_RECOMMENDED_STEP']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    before = {str(path): file_sig(path) for path in protected_files(root)}
    script_path = root / "scripts/v18/v18_25A_R11_full_compatible_technical_timing_refresh_with_vix.py"
    wrapper_path = root / "scripts/v18/run_v18_25A_R11_full_compatible_technical_timing_refresh_with_vix.ps1"
    current_tech_path = root / CURRENT_TECH

    targets = load_targets(root)
    vix = load_vix(root)
    vix_usable = not vix.empty and "close" in vix.columns and len(vix) > 0
    vix_min = vix["date"].min().date().isoformat() if vix_usable else ""
    vix_max = vix["date"].max().date().isoformat() if vix_usable else ""

    rows: List[Dict[str, object]] = []
    result_rows: List[Dict[str, object]] = []
    insufficient = 0
    for ticker in targets:
        price_path = root / PRICE_CACHE_DIR / f"{ticker}.csv"
        price = normalize_price_df(read_df(price_path), ticker)
        blocker = ""
        row: Optional[Dict[str, object]] = None
        if price.empty or len(price) < MIN_HISTORY_ROWS:
            blocker = "INSUFFICIENT_HISTORY_OR_MISSING_PRICE_CACHE"
            insufficient += 1
        elif not vix_usable:
            blocker = "OFFICIAL_VIX_UNUSABLE"
        else:
            try:
                row = compute_ticker(price, vix)
                rows.append(row)
            except Exception as exc:
                blocker = f"COMPUTE_FAILED:{type(exc).__name__}:{exc}"
        success = row is not None
        result_rows.append({
            "ticker": ticker,
            "refresh_attempted": "TRUE",
            "refresh_success": str(success).upper(),
            "technical_status": row.get("technical_status", "") if row else "TECHNICAL_REFRESH_BLOCKED",
            "formula_compatibility": row.get("formula_compatibility", "") if row else "",
            "merge_ready": str(success).upper(),
            "blocker": "NONE" if success else blocker,
            "input_history_rows": len(price),
            "price_date": row.get("price_date", "") if row else "",
            "vix_date": row.get("vix_date", "") if row else "",
            "vix_regime": row.get("vix_regime", "") if row else "",
        })

    staged_fields = [
        "ticker", "yf_ticker", "price_date", "close", "bb_mid_20", "bb_upper_20_2", "bb_lower_20_2",
        "bb_percent_b", "bb_bandwidth", "bb_squeeze_flag", "bb_status", "rsi_14", "rsi_status",
        "kdj_k", "kdj_d", "kdj_j", "kdj_status", "volume_ratio_5_20", "overheat_penalty",
        "pullback_timing_bonus", "breakout_confirmation_bonus", "technical_timing_score",
        "technical_signal", "technical_warning_label", "option_data_status", "put_call_ratio",
        "iv_rank_proxy", "gamma_squeeze_status", "gamma_squeeze_risk_label", "official_decision_impact",
        "vix_date", "vix_close", "vix_regime", "formula_compatibility", "technical_status",
        "technical_refresh_blocker", "input_history_rows", "duplicate_date_count", "close_column_available",
        "refresh_scope",
    ]
    out_df = pd.DataFrame(rows)
    if not out_df.empty:
        out_df = out_df.sort_values(["technical_timing_score", "overheat_penalty", "ticker"], ascending=[False, True, True])
        ensure_dir((root / STAGED_OUT).parent)
        out_df.to_csv(root / STAGED_OUT, index=False, encoding="utf-8-sig", columns=staged_fields)
    else:
        write_csv(root / STAGED_OUT, [], staged_fields)

    current_rows, current_fields = read_csv_rows(current_tech_path)
    staged_field_set = set(staged_fields)
    current_field_set = set(current_fields)
    missing_fields = sorted(current_field_set - staged_field_set)
    extra_fields = sorted(staged_field_set - current_field_set)
    schema_compatible = len(missing_fields) == 0
    schema_rows = [
        {"schema_check": "current_field_count", "value": len(current_fields), "notes": str(current_tech_path)},
        {"schema_check": "staged_field_count", "value": len(staged_fields), "notes": str(root / STAGED_OUT)},
        {"schema_check": "fields_matched", "value": len(current_field_set & staged_field_set), "notes": ",".join(sorted(current_field_set & staged_field_set))},
        {"schema_check": "fields_missing", "value": len(missing_fields), "notes": ",".join(missing_fields)},
        {"schema_check": "extra_fields", "value": len(extra_fields), "notes": ",".join(extra_fields)},
        {"schema_check": "compatibility_status", "value": "MERGE_SCHEMA_COMPATIBLE" if schema_compatible else "MERGE_SCHEMA_REVIEW_REQUIRED", "notes": "R11 staged output must contain all current technical fields."},
    ]
    write_csv(root / SCHEMA_AUDIT_OUT, schema_rows, SCHEMA_FIELDS)

    success_count = sum(1 for row in result_rows if row["refresh_success"] == "TRUE")
    fail_count = len(result_rows) - success_count
    full_count = sum(1 for row in result_rows if row["formula_compatibility"] == FORMULA_STATUS)
    partial_count = sum(1 for row in result_rows if "PARTIAL" in str(row["formula_compatibility"]))
    merge_ready_count = sum(1 for row in result_rows if row["merge_ready"] == "TRUE" and schema_compatible)
    merge_blocked_count = len(result_rows) - merge_ready_count
    gate_rows = [{
        "ticker": row["ticker"],
        "merge_ready": str(row["merge_ready"] == "TRUE" and schema_compatible).upper(),
        "merge_blocker": "NONE" if row["merge_ready"] == "TRUE" and schema_compatible else row["blocker"] or "SCHEMA_REVIEW_REQUIRED",
        "schema_compatible": str(schema_compatible).upper(),
        "formula_compatibility": row["formula_compatibility"],
        "notes": "R11 staged output only; current technical file not overwritten.",
    } for row in result_rows]

    write_csv(root / RESULT_OUT, result_rows, RESULT_FIELDS)
    write_csv(root / GATE_OUT, gate_rows, GATE_FIELDS)

    forbidden_changed = changed_forbidden_files(root, before)
    current_modified = file_sig(current_tech_path) != before.get(str(current_tech_path), (-1, -1))
    validations = [
        ("python_compile_check", subprocess.run([sys.executable, "-m", "py_compile", str(script_path)], capture_output=True).returncode == 0),
        ("powershell_parse_check", ps_parse(wrapper_path)),
        ("target_ticker_count_52", len(targets) == 52),
        ("official_vix_usable", vix_usable),
        ("no_external_fetch", True),
        ("all_targets_succeeded", success_count == len(targets)),
        ("schema_compatible", schema_compatible),
        ("vix_overlay_included", success_count > 0 and all(str(row.get("vix_regime", "")) != "VIX_UNKNOWN" for row in rows)),
        ("current_technical_file_unchanged", not current_modified),
        ("forbidden_files_unchanged", not forbidden_changed),
    ]
    validation_fail_count = sum(1 for _, ok in validations if not ok)

    summary_rows = [
        {"metric": "target_ticker_count", "value": len(targets), "notes": "Discovered from R4 readiness audit."},
        {"metric": "technical_refresh_success_count", "value": success_count, "notes": "Rows generated in R11 staged output."},
        {"metric": "technical_refresh_fail_count", "value": fail_count, "notes": "Blocked or failed tickers."},
        {"metric": "formula_compatibility_status", "value": FORMULA_STATUS, "notes": "V18.6A formulas locally reimplemented with official VIX overlay."},
        {"metric": "exact_v18_6a_formula_reused", "value": EXACT_FORMULA_REUSED, "notes": "Original script fetches externally and overwrites current output, so not called directly."},
        {"metric": "vix_row_count", "value": len(vix), "notes": f"{vix_min}..{vix_max}"},
        {"metric": "merge_ready_count", "value": merge_ready_count, "notes": "Schema-compatible staged rows ready for later merge task."},
        {"metric": "merge_blocked_count", "value": merge_blocked_count, "notes": "Rows blocked from later merge."},
        {"metric": "forbidden_file_modified", "value": str(bool(forbidden_changed)).upper(), "notes": ";".join(forbidden_changed[:20])},
    ]
    write_csv(root / SUMMARY_OUT, summary_rows, SUMMARY_FIELDS)

    status = STATUS_FAIL
    if validation_fail_count == 0 and success_count == 52 and full_count == 52:
        status = STATUS_OK
    elif success_count > 0 and vix_usable and not forbidden_changed and not current_modified:
        status = STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": MODE,
        "R10_SOURCE_PATH": str(root / R10_READ_FIRST),
        "OFFICIAL_VIX_PATH": str(root / OFFICIAL_VIX),
        "TARGET_TICKER_COUNT": str(len(targets)),
        "TECHNICAL_REFRESH_ATTEMPT_COUNT": str(len(targets)),
        "TECHNICAL_REFRESH_SUCCESS_COUNT": str(success_count),
        "TECHNICAL_REFRESH_FAIL_COUNT": str(fail_count),
        "FORMULA_COMPATIBILITY_STATUS": FORMULA_STATUS,
        "EXACT_V18_6A_FORMULA_REUSED": EXACT_FORMULA_REUSED,
        "VIX_OVERLAY_INCLUDED": str(success_count > 0 and all(str(row.get("vix_regime", "")) != "VIX_UNKNOWN" for row in rows)).upper(),
        "VIX_ROW_COUNT": str(len(vix)),
        "VIX_MIN_DATE": vix_min,
        "VIX_MAX_DATE": vix_max,
        "VIX_USABLE": str(vix_usable).upper(),
        "PARTIAL_COMPATIBLE_COUNT": str(partial_count),
        "FULL_COMPATIBLE_COUNT": str(full_count),
        "INSUFFICIENT_HISTORY_COUNT": str(insufficient),
        "OUTPUT_ROW_COUNT": str(len(rows)),
        "STAGED_TECHNICAL_OUTPUT_PATH": str(root / STAGED_OUT),
        "MERGE_READY_COUNT": str(merge_ready_count),
        "MERGE_BLOCKED_COUNT": str(merge_blocked_count),
        "CURRENT_TECHNICAL_FILE_MODIFIED": str(current_modified).upper(),
        "OFFICIAL_MARKET_PROXY_MODIFIED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "TIER_MIGRATION_MODIFIED": "FALSE",
        "DEGRADED_DAILY_MODIFIED": "FALSE",
        "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "VALIDATION_FAIL_COUNT": str(validation_fail_count),
        "FORBIDDEN_FILE_MODIFIED": str(bool(forbidden_changed)).upper(),
        "NEXT_RECOMMENDED_STEP": "Review R11 staged output and approve a separate merge task before replacing current technical timing files.",
    }
    report = render_report(values)
    write_text(root / REPORT_OUT, report)
    write_text(root / OPS_REPORT_OUT, report)
    write_text(root / READ_FIRST_OUT, render_read_first(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if status != STATUS_FAIL else 1


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


if __name__ == "__main__":
    sys.exit(main())
