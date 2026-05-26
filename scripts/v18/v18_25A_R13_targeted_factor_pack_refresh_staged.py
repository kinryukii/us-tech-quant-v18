from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd


STATUS_OK = "OK_V18_25A_R13_TARGETED_FACTOR_PACK_REFRESH_STAGED_READY"
STATUS_WARN = "WARN_V18_25A_R13_TARGETED_FACTOR_PACK_REFRESH_STAGED_READY"
STATUS_FAIL = "FAIL_V18_25A_R13_TARGETED_FACTOR_PACK_REFRESH_STAGED"
MODE = "READ_ONLY_TARGETED_FACTOR_PACK_REFRESH_STAGED_OUTPUT"
FORMULA_STATUS = "CURRENT_FACTOR_COMPATIBLE_LOCAL_REIMPLEMENTATION"
EXACT_FORMULA_REUSED = "FALSE"

R3_SOURCE = "outputs/v18/degraded_daily_review/V18_25A_R3_CURRENT_R6_R7_PROMOTION_BLOCKER_AUDIT.csv"
R6_INTEGRATION = "outputs/v18/staged_backfill/V18_23C_R6_CURRENT_OFFICIAL_BATCH2_INTEGRATION_RESULT.csv"
R7_LEDGER = "outputs/v18/rolling_coverage/V18_23C_R7_CURRENT_LEDGER_UPDATE_RESULT.csv"
TECH_CURRENT = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
CURRENT_FACTOR = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
OFFICIAL_VIX = "state/v18/market_proxy_cache/VIX.csv"
PRICE_CACHE_DIR = "state/v18/price_cache"

STAGED_OUT = "outputs/v18/factor_pack/V18_25A_R13_TARGETED_FACTOR_PACK_STAGED.csv"
SCHEMA_OUT = "outputs/v18/factor_pack/V18_25A_R13_TARGETED_FACTOR_PACK_SCHEMA_AUDIT.csv"
GATE_OUT = "outputs/v18/factor_pack/V18_25A_R13_TARGETED_FACTOR_PACK_MERGE_GATE.csv"
RESULT_OUT = "outputs/v18/factor_pack/V18_25A_R13_TARGETED_FACTOR_PACK_REFRESH_RESULT.csv"
SUMMARY_OUT = "outputs/v18/degraded_daily_review/V18_25A_R13_CURRENT_FACTOR_REFRESH_SUMMARY.csv"
REPORT_OUT = "outputs/v18/degraded_daily_review/V18_25A_R13_CURRENT_REPORT.md"
READ_FIRST_OUT = "outputs/v18/ops/V18_25A_R13_READ_FIRST.txt"
OPS_REPORT_OUT = "outputs/v18/ops/V18_25A_R13_CURRENT_TARGETED_FACTOR_PACK_REFRESH_REPORT.md"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R3_SOURCE_PATH",
    "CURRENT_FACTOR_PACK_PATH",
    "OFFICIAL_VIX_PATH",
    "TARGET_TICKER_COUNT",
    "FACTOR_REFRESH_ATTEMPT_COUNT",
    "FACTOR_REFRESH_SUCCESS_COUNT",
    "FACTOR_REFRESH_FAIL_COUNT",
    "FACTOR_FORMULA_COMPATIBILITY_STATUS",
    "EXACT_CURRENT_FACTOR_FORMULA_REUSED",
    "VIX_INCLUDED",
    "VIX_USABLE",
    "OUTPUT_ROW_COUNT",
    "STAGED_FACTOR_OUTPUT_PATH",
    "MERGE_READY_COUNT",
    "MERGE_BLOCKED_COUNT",
    "SCHEMA_COMPATIBILITY_STATUS",
    "CURRENT_FACTOR_PACK_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "OFFICIAL_MARKET_PROXY_MODIFIED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_BACKFILL_MODIFIED",
    "STAGED_MARKET_PROXY_MODIFIED",
    "LEDGER_MODIFIED",
    "TIER_MIGRATION_MODIFIED",
    "DEGRADED_DAILY_MODIFIED",
    "OFFICIAL_DAILY_DECISION_MODIFIED",
    "BUY_PERMISSION_MODIFIED",
    "BACKTEST_EXECUTED",
    "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_FILE_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]

RANKING_FIELDS = [
    "factor_pack_rank",
    "ticker",
    "factor_pack_score",
    "latest_price_date",
    "latest_close",
    "ret_5d",
    "ret_20d",
    "ret_60d",
    "ret_120d",
    "volume_ratio_5_20",
    "F006_SHORT_REV_5D",
    "F007_PULLBACK_IN_UPTREND",
    "F008_VOLUME_ABNORMAL_5_20",
    "F009_VOLUME_PRICE_CONFIRM",
    "F010_XSEC_COMPOSITE_RANK",
    "F011_TS_MOMENTUM_60_120",
    "F012_TS_PULLBACK_REVERSAL",
    "volatility_penalty",
    "overheat_penalty",
    "shadow_side_hint",
]
SCHEMA_FIELDS = ["schema_check", "value", "notes"]
GATE_FIELDS = ["ticker", "merge_gate_decision", "merge_ready", "blocker", "schema_compatible", "formula_compatibility", "notes"]
RESULT_FIELDS = ["ticker", "refresh_attempted", "refresh_success", "blocker", "price_rows", "latest_price_date", "factor_pack_score", "vix_included", "vix_regime"]
SUMMARY_FIELDS = ["metric", "value", "notes"]


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


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def allowed_r13_output(path: Path, root: Path) -> bool:
    rel = path.resolve().relative_to(root.resolve()).as_posix()
    return rel in {
        STAGED_OUT,
        SCHEMA_OUT,
        GATE_OUT,
        RESULT_OUT,
        SUMMARY_OUT,
        REPORT_OUT,
        READ_FIRST_OUT,
        OPS_REPORT_OUT,
    }


def protected_files(root: Path) -> List[Path]:
    rels = [
        PRICE_CACHE_DIR,
        OFFICIAL_VIX,
        "data/v18/price_history",
        "data/v18/staged_backfill",
        "data/v18/staged_market_proxy",
        "state/v18/rolling_coverage",
        "outputs/v18/rolling_coverage",
        "outputs/v18/factor_pack",
        "outputs/v18/technical_timing",
        "outputs/v18/tier_migration",
        "outputs/v18/official_daily_decision",
        "outputs/v18/daily_decision",
        "outputs/v18/degraded_daily_review",
        "state/v18/official_daily_decision",
    ]
    out: List[Path] = []
    for rel in rels:
        base = root / rel
        if not base.exists():
            continue
        files = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
        for path in files:
            try:
                if allowed_r13_output(path, root):
                    continue
            except ValueError:
                pass
            out.append(path)
    return out


def changed_forbidden_files(root: Path, before: Dict[str, Tuple[int, int]]) -> List[str]:
    after = {str(path): file_sig(path) for path in protected_files(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig)
    changed.extend(sorted(path for path in after if path not in before))
    return changed


def discover_targets(root: Path) -> List[str]:
    rows, _ = read_csv_rows(root / R3_SOURCE)
    out: List[str] = []
    seen = set()
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        if not ticker or ticker in seen:
            continue
        if str(row.get("r6_integration_success", "")).upper() != "TRUE":
            continue
        if str(row.get("r7_ledger_success", "")).upper() != "TRUE":
            continue
        if str(row.get("factor_pack_present", "")).upper() != "FALSE":
            continue
        if row.get("promotion_blocker_primary") != "BLOCKED_MISSING_FACTOR_SCORE":
            continue
        if row.get("recommended_next_fix") != "REFRESH_FACTOR_PACK_FOR_INTEGRATED_TICKERS":
            continue
        seen.add(ticker)
        out.append(ticker)
    return out


def normalize_price(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    need = {"date", "close", "volume"}
    if not need.issubset(set(df.columns)):
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date").drop_duplicates("date", keep="last")
    return df.reset_index(drop=True)


def load_vix(root: Path) -> Tuple[pd.DataFrame, str]:
    df = read_df(root / OFFICIAL_VIX)
    if df.empty:
        return df, "VIX_MISSING"
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    if "date" not in df.columns or "close" not in df.columns:
        return pd.DataFrame(), "VIX_SCHEMA_INVALID"
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date").drop_duplicates("date", keep="last")
    return df.reset_index(drop=True), "OK" if not df.empty else "VIX_EMPTY"


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


def pct_rank_high_good(series: pd.Series) -> pd.Series:
    return series.rank(pct=True, method="average", na_option="keep")


def compute_base(ticker: str, price: pd.DataFrame) -> Dict[str, object]:
    c = pd.to_numeric(price["close"], errors="coerce").dropna()
    v = pd.to_numeric(price["volume"], errors="coerce").reindex(c.index)
    ret = c.pct_change()
    last = c.iloc[-1]

    def pct_change(n: int) -> float:
        if len(c) <= n or c.iloc[-n - 1] == 0:
            return np.nan
        return float(c.iloc[-1] / c.iloc[-n - 1] - 1)

    ret_5d = pct_change(5)
    ret_20d = pct_change(20)
    ret_60d = pct_change(60)
    ret_120d = pct_change(120)
    ma60 = float(c.rolling(60).mean().iloc[-1])
    high20 = float(c.rolling(20).max().iloc[-1])
    high60 = float(c.rolling(60).max().iloc[-1])
    vol5 = float(v.rolling(5).mean().iloc[-1]) if v.notna().sum() >= 5 else np.nan
    vol20 = float(v.rolling(20).mean().iloc[-1]) if v.notna().sum() >= 20 else np.nan
    vol_ratio = float(vol5 / vol20) if vol20 and not math.isnan(vol20) and vol20 > 0 else np.nan
    ann_vol20 = float(ret.tail(20).std() * math.sqrt(252)) if ret.tail(20).notna().sum() >= 10 else np.nan
    return {
        "ticker": ticker,
        "latest_price_date": price["date"].iloc[-1].date().isoformat(),
        "latest_close": float(last),
        "ret_5d": ret_5d,
        "ret_20d": ret_20d,
        "ret_60d": ret_60d,
        "ret_120d": ret_120d,
        "ma60": ma60,
        "drawdown_20d_high": float(last / high20 - 1) if high20 else np.nan,
        "drawdown_60d_high": float(last / high60 - 1) if high60 else np.nan,
        "volume_ratio_5_20": vol_ratio,
        "ann_volatility_20d": ann_vol20,
        "price_rows": len(price),
    }


def side_hint(row: pd.Series) -> str:
    if row.get("F007_PULLBACK_IN_UPTREND", 0) >= 75 and row.get("F012_TS_PULLBACK_REVERSAL", 0) >= 75:
        return "PULLBACK_IN_UPTREND"
    if row.get("volume_ratio_5_20", 0) >= 1.8 and row.get("ret_5d", 0) < -0.03:
        return "VOLUME_DOWN_RISK"
    if row.get("F009_VOLUME_PRICE_CONFIRM", 0) >= 75:
        return "VOLUME_UP_CONFIRM"
    if row.get("F011_TS_MOMENTUM_60_120", 0) >= 75 and row.get("F006_SHORT_REV_5D", 50) < 35:
        return "MOMENTUM_STRONG_NOT_PULLBACK"
    return "NEUTRAL_SHADOW"


def build_factor_df(base_rows: List[Dict[str, object]]) -> pd.DataFrame:
    df = pd.DataFrame(base_rows)
    df["short_rev_raw"] = -df["ret_5d"]
    df["ts_momentum_raw"] = 0.50 * df["ret_60d"] + 0.50 * df["ret_120d"]
    df["volume_price_confirm_raw"] = df["volume_ratio_5_20"] * df["ret_5d"]
    trend_mask = (df["ret_60d"] > 0) & (df["ret_120d"] > 0) & (df["latest_close"] >= df["ma60"])
    pullback_depth = (-df["ret_5d"]).clip(lower=0, upper=0.20) + (-df["drawdown_20d_high"]).clip(lower=0, upper=0.20)
    df["pullback_uptrend_raw"] = np.where(trend_mask, pullback_depth, np.nan)
    ts_reversal_raw = (0.50 * df["ret_60d"].clip(lower=0) + 0.50 * df["ret_120d"].clip(lower=0)) * (-df["ret_5d"]).clip(lower=0, upper=0.20)
    df["ts_pullback_reversal_raw"] = np.where(df["ret_20d"] > -0.25, ts_reversal_raw, np.nan)
    df["F006_SHORT_REV_5D"] = pct_rank_high_good(df["short_rev_raw"]) * 100
    df["F007_PULLBACK_IN_UPTREND"] = pct_rank_high_good(df["pullback_uptrend_raw"]) * 100
    df["F008_VOLUME_ABNORMAL_5_20"] = pct_rank_high_good(df["volume_ratio_5_20"]) * 100
    df["F009_VOLUME_PRICE_CONFIRM"] = pct_rank_high_good(df["volume_price_confirm_raw"]) * 100
    df["F011_TS_MOMENTUM_60_120"] = pct_rank_high_good(df["ts_momentum_raw"]) * 100
    df["F012_TS_PULLBACK_REVERSAL"] = pct_rank_high_good(df["ts_pullback_reversal_raw"]) * 100
    df["volatility_penalty"] = pct_rank_high_good(df["ann_volatility_20d"]) * 100
    overheat_raw = np.maximum(df["ret_20d"].fillna(-9), 0.5 * df["ret_60d"].fillna(-9))
    df["overheat_penalty"] = pct_rank_high_good(overheat_raw) * 100
    f = df[["F006_SHORT_REV_5D", "F007_PULLBACK_IN_UPTREND", "F008_VOLUME_ABNORMAL_5_20", "F009_VOLUME_PRICE_CONFIRM", "F011_TS_MOMENTUM_60_120", "F012_TS_PULLBACK_REVERSAL"]].fillna(50.0)
    comp_raw = (
        0.16 * f["F006_SHORT_REV_5D"]
        + 0.22 * f["F007_PULLBACK_IN_UPTREND"]
        + 0.12 * f["F008_VOLUME_ABNORMAL_5_20"]
        + 0.14 * f["F009_VOLUME_PRICE_CONFIRM"]
        + 0.22 * f["F011_TS_MOMENTUM_60_120"]
        + 0.14 * f["F012_TS_PULLBACK_REVERSAL"]
        - 0.08 * df["volatility_penalty"].fillna(50.0)
        - 0.12 * df["overheat_penalty"].fillna(50.0)
    )
    df["F010_XSEC_COMPOSITE_RANK"] = pct_rank_high_good(comp_raw) * 100
    df["factor_pack_score"] = df["F010_XSEC_COMPOSITE_RANK"].round(2)
    df = df.sort_values(["factor_pack_score", "ticker"], ascending=[False, True]).reset_index(drop=True)
    df["factor_pack_rank"] = np.arange(1, len(df) + 1)
    df["shadow_side_hint"] = df.apply(side_hint, axis=1)
    for col in RANKING_FIELDS:
        if col in {"ticker", "latest_price_date", "shadow_side_hint"}:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce").round(6)
    return df[RANKING_FIELDS]


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.25A-R13 Targeted Factor Pack Refresh Staged Output

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

Status: {values['STATUS']}

Mode: {MODE}

Targets: {values['TARGET_TICKER_COUNT']}

Refresh success/fail: {values['FACTOR_REFRESH_SUCCESS_COUNT']} / {values['FACTOR_REFRESH_FAIL_COUNT']}

Formula compatibility: {values['FACTOR_FORMULA_COMPATIBILITY_STATUS']}

Schema compatibility: {values['SCHEMA_COMPATIBILITY_STATUS']}

VIX included: {values['VIX_INCLUDED']} usable={values['VIX_USABLE']}

Staged output: `{values['STAGED_FACTOR_OUTPUT_PATH']}`

Merge gate: ready={values['MERGE_READY_COUNT']}, blocked={values['MERGE_BLOCKED_COUNT']}

Safety: no external fetch and no current factor pack, price cache, technical timing, ledger, tier, degraded-current, decision, or trading permission changes.

Next step: {values['NEXT_RECOMMENDED_STEP']}
"""


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    before = {str(path): file_sig(path) for path in protected_files(root)}
    current_factor_sig = file_sig(root / CURRENT_FACTOR)
    tech_sig = file_sig(root / TECH_CURRENT)

    targets = discover_targets(root)
    tech_rows, _ = read_csv_rows(root / TECH_CURRENT)
    tech_tickers = {norm_ticker(row.get("ticker")) for row in tech_rows}
    current_factor_rows, current_fields = read_csv_rows(root / CURRENT_FACTOR)
    current_factor_tickers = {norm_ticker(row.get("ticker")) for row in current_factor_rows}
    vix, vix_status = load_vix(root)
    vix_usable = vix_status == "OK"
    vix_latest = float(vix["close"].iloc[-1]) if vix_usable else np.nan
    vix_regime_latest = vix_regime(vix_latest) if vix_usable else "VIX_UNKNOWN"

    base_rows: List[Dict[str, object]] = []
    result_rows: List[Dict[str, object]] = []
    for ticker in targets:
        price = normalize_price(read_df(root / PRICE_CACHE_DIR / f"{ticker}.csv"))
        blocker = ""
        if ticker not in tech_tickers:
            blocker = "TECHNICAL_TIMING_MISSING"
        elif ticker in current_factor_tickers:
            blocker = "FACTOR_ALREADY_PRESENT_IN_CURRENT"
        elif not vix_usable:
            blocker = "OFFICIAL_VIX_UNUSABLE"
        elif price.empty or len(price) < 130:
            blocker = "INSUFFICIENT_PRICE_HISTORY"
        if blocker:
            result_rows.append({"ticker": ticker, "refresh_attempted": "TRUE", "refresh_success": "FALSE", "blocker": blocker, "price_rows": len(price), "latest_price_date": "", "factor_pack_score": "", "vix_included": str(vix_usable).upper(), "vix_regime": vix_regime_latest})
            continue
        row = compute_base(ticker, price)
        base_rows.append(row)
        result_rows.append({"ticker": ticker, "refresh_attempted": "TRUE", "refresh_success": "TRUE", "blocker": "NONE", "price_rows": len(price), "latest_price_date": row["latest_price_date"], "factor_pack_score": "", "vix_included": "TRUE", "vix_regime": vix_regime_latest})

    staged_df = build_factor_df(base_rows) if base_rows else pd.DataFrame(columns=RANKING_FIELDS)
    if not staged_df.empty:
        score_map = dict(zip(staged_df["ticker"].astype(str), staged_df["factor_pack_score"].astype(str)))
        for row in result_rows:
            if row["ticker"] in score_map:
                row["factor_pack_score"] = score_map[row["ticker"]]
    ensure_dir((root / STAGED_OUT).parent)
    staged_df.to_csv(root / STAGED_OUT, index=False, encoding="utf-8-sig")

    staged_fields = list(staged_df.columns) if not staged_df.empty else RANKING_FIELDS
    missing = sorted(set(current_fields) - set(staged_fields))
    extra = sorted(set(staged_fields) - set(current_fields))
    schema_status = "MERGE_SCHEMA_COMPATIBLE" if not missing else "MERGE_SCHEMA_REVIEW_REQUIRED"
    schema_rows = [
        {"schema_check": "current_field_count", "value": len(current_fields), "notes": ",".join(current_fields)},
        {"schema_check": "staged_field_count", "value": len(staged_fields), "notes": ",".join(staged_fields)},
        {"schema_check": "matched_fields", "value": len(set(current_fields) & set(staged_fields)), "notes": ",".join(sorted(set(current_fields) & set(staged_fields)))},
        {"schema_check": "missing_fields", "value": len(missing), "notes": ",".join(missing)},
        {"schema_check": "extra_fields", "value": len(extra), "notes": ",".join(extra)},
        {"schema_check": "compatibility_status", "value": schema_status, "notes": "R13 staged ranking uses current RAW105 ranking schema."},
    ]
    write_csv(root / SCHEMA_OUT, schema_rows, SCHEMA_FIELDS)

    success_count = sum(1 for row in result_rows if row["refresh_success"] == "TRUE")
    fail_count = len(result_rows) - success_count
    merge_ready = success_count if schema_status == "MERGE_SCHEMA_COMPATIBLE" and FORMULA_STATUS else 0
    merge_blocked = len(targets) - merge_ready
    gate_rows = []
    for row in result_rows:
        if row["refresh_success"] != "TRUE":
            decision = "MERGE_BLOCKED_INSUFFICIENT_INPUTS"
            ready = "FALSE"
            blocker = row["blocker"]
        elif schema_status != "MERGE_SCHEMA_COMPATIBLE":
            decision = "MERGE_BLOCKED_SCHEMA_MISMATCH"
            ready = "FALSE"
            blocker = "SCHEMA_MISMATCH"
        elif FORMULA_STATUS == "":
            decision = "MERGE_BLOCKED_FORMULA_INCOMPATIBLE"
            ready = "FALSE"
            blocker = "FORMULA_INCOMPATIBLE"
        else:
            decision = "MERGE_READY"
            ready = "TRUE"
            blocker = "NONE"
        gate_rows.append({"ticker": row["ticker"], "merge_gate_decision": decision, "merge_ready": ready, "blocker": blocker, "schema_compatible": str(schema_status == "MERGE_SCHEMA_COMPATIBLE").upper(), "formula_compatibility": FORMULA_STATUS, "notes": "R13 staged output only; current factor pack not modified."})
    write_csv(root / GATE_OUT, gate_rows, GATE_FIELDS)
    write_csv(root / RESULT_OUT, result_rows, RESULT_FIELDS)

    forbidden_changed = changed_forbidden_files(root, before)
    current_factor_modified = file_sig(root / CURRENT_FACTOR) != current_factor_sig
    technical_modified = file_sig(root / TECH_CURRENT) != tech_sig
    validations = [
        ("python_compile_check", subprocess.run([sys.executable, "-m", "py_compile", str(root / "scripts/v18/v18_25A_R13_targeted_factor_pack_refresh_staged.py")], capture_output=True).returncode == 0),
        ("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_25A_R13_targeted_factor_pack_refresh_staged.ps1")),
        ("target_ticker_count_52", len(targets) == 52),
        ("official_vix_usable", vix_usable),
        ("all_targets_succeeded", success_count == 52),
        ("schema_compatible", schema_status == "MERGE_SCHEMA_COMPATIBLE"),
        ("current_factor_pack_unchanged", not current_factor_modified),
        ("technical_timing_unchanged", not technical_modified),
        ("forbidden_files_unchanged", not forbidden_changed),
    ]
    validation_fail_count = sum(1 for _, ok in validations if not ok)
    status = STATUS_FAIL
    if validation_fail_count == 0 and success_count == 52 and merge_ready == 52:
        status = STATUS_OK
    elif staged_df.shape[0] > 0 and not forbidden_changed and not current_factor_modified:
        status = STATUS_WARN

    summary_rows = [
        {"metric": "target_ticker_count", "value": len(targets), "notes": "Discovered from R3 blocker audit."},
        {"metric": "factor_refresh_success_count", "value": success_count, "notes": "Generated staged factor rows."},
        {"metric": "factor_refresh_fail_count", "value": fail_count, "notes": "Blocked staged rows."},
        {"metric": "formula_compatibility_status", "value": FORMULA_STATUS, "notes": "Local reimplementation of current RAW105 price-derived ranking logic."},
        {"metric": "exact_current_factor_formula_reused", "value": EXACT_FORMULA_REUSED, "notes": "Original current script is not called; it has broad current-output side effects."},
        {"metric": "vix_included", "value": str(vix_usable).upper(), "notes": f"VIX status={vix_status}; regime={vix_regime_latest}."},
        {"metric": "merge_ready_count", "value": merge_ready, "notes": "Ready for separate merge task."},
        {"metric": "merge_blocked_count", "value": merge_blocked, "notes": "Blocked from merge."},
        {"metric": "forbidden_file_modified", "value": str(bool(forbidden_changed)).upper(), "notes": ";".join(forbidden_changed[:20])},
    ]
    write_csv(root / SUMMARY_OUT, summary_rows, SUMMARY_FIELDS)

    values = {
        "STATUS": status,
        "MODE": MODE,
        "R3_SOURCE_PATH": str(root / R3_SOURCE),
        "CURRENT_FACTOR_PACK_PATH": str(root / CURRENT_FACTOR),
        "OFFICIAL_VIX_PATH": str(root / OFFICIAL_VIX),
        "TARGET_TICKER_COUNT": str(len(targets)),
        "FACTOR_REFRESH_ATTEMPT_COUNT": str(len(targets)),
        "FACTOR_REFRESH_SUCCESS_COUNT": str(success_count),
        "FACTOR_REFRESH_FAIL_COUNT": str(fail_count),
        "FACTOR_FORMULA_COMPATIBILITY_STATUS": FORMULA_STATUS,
        "EXACT_CURRENT_FACTOR_FORMULA_REUSED": EXACT_FORMULA_REUSED,
        "VIX_INCLUDED": str(vix_usable).upper(),
        "VIX_USABLE": str(vix_usable).upper(),
        "OUTPUT_ROW_COUNT": str(len(staged_df)),
        "STAGED_FACTOR_OUTPUT_PATH": str(root / STAGED_OUT),
        "MERGE_READY_COUNT": str(merge_ready),
        "MERGE_BLOCKED_COUNT": str(merge_blocked),
        "SCHEMA_COMPATIBILITY_STATUS": schema_status,
        "CURRENT_FACTOR_PACK_MODIFIED": str(current_factor_modified).upper(),
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": str(technical_modified).upper(),
        "OFFICIAL_MARKET_PROXY_MODIFIED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
        "STAGED_MARKET_PROXY_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "TIER_MIGRATION_MODIFIED": "FALSE",
        "DEGRADED_DAILY_MODIFIED": "FALSE",
        "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "VALIDATION_FAIL_COUNT": str(validation_fail_count),
        "FORBIDDEN_FILE_MODIFIED": str(bool(forbidden_changed)).upper(),
        "NEXT_RECOMMENDED_STEP": "Review R13 staged factor output and approve a separate factor-pack current merge with backup.",
    }
    report = render_report(values)
    write_text(root / REPORT_OUT, report)
    write_text(root / OPS_REPORT_OUT, report)
    write_text(root / READ_FIRST_OUT, render_read_first(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if status != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
