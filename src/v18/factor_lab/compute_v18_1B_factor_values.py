from __future__ import annotations

import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


ROOT = Path(r"D:\us-tech-quant")
VERSION = "V18.1B"

STATE_DIR = ROOT / "state" / "v18"
OUT_DIR = ROOT / "outputs" / "v18" / "factor_lab"
MANIFEST_DIR = ROOT / "outputs" / "v18" / "manifests"

REGISTRY_PATH = STATE_DIR / "factor_registry.csv"

OUT_CSV = OUT_DIR / "V18_1B_FACTOR_VALUES_CURRENT.csv"
OUT_MD = OUT_DIR / "V18_1B_FACTOR_VALUES_CURRENT.md"
READ_FIRST = OUT_DIR / "V18_1B_READ_FIRST.txt"
AUDIT_CSV = OUT_DIR / "V18_1B_FACTOR_COMPUTE_AUDIT.csv"
UNIVERSE_SNAPSHOT = STATE_DIR / "raw105_universe_for_factor_lab.csv"
MANIFEST_PATH = MANIFEST_DIR / "V18_1B_FACTOR_VALUE_MANIFEST.csv"

BENCHMARKS = ["QQQ", "XLK", "SMH"]


def ensure_dirs() -> None:
    for path in [STATE_DIR, OUT_DIR, MANIFEST_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def fail(message: str, code: int = 1) -> None:
    print("")
    print("V18_1B_STATUS: FAIL")
    print(f"REASON: {message}")
    print("")
    sys.exit(code)


def find_ticker_column(df: pd.DataFrame) -> Optional[str]:
    candidates = ["ticker", "Ticker", "symbol", "Symbol", "SYMBOL"]
    for col in candidates:
        if col in df.columns:
            return col
    return None


def clean_ticker(value: object) -> Optional[str]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None

    ticker = str(value).strip().upper()

    if not ticker:
        return None

    bad = {"NAN", "NONE", "NULL", "TICKER", "SYMBOL"}
    if ticker in bad:
        return None

    ticker = ticker.replace(".", "-")

    if len(ticker) > 12:
        return None

    return ticker


def discover_universe_from_csvs() -> Tuple[List[str], Optional[Path], str]:
    explicit_candidates = [
        ROOT / "outputs" / "v17" / "raw105_decision" / "v17_8A_raw105_full_decision_daily.csv",
        ROOT / "outputs" / "v17" / "raw105_decision" / "V17_8D_CURRENT_RAW105_DECISION_PANEL.csv",
        ROOT / "state" / "v17" / "raw105_universe.csv",
        ROOT / "state" / "raw105_universe.csv",
    ]

    search_roots = [
        ROOT / "state",
        ROOT / "outputs" / "v17",
        ROOT / "configs",
    ]

    csv_paths: List[Path] = []
    for path in explicit_candidates:
        if path.exists():
            csv_paths.append(path)

    for base in search_roots:
        if base.exists():
            csv_paths.extend(base.rglob("*.csv"))

    seen = set()
    unique_paths: List[Path] = []
    for path in csv_paths:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            unique_paths.append(path)

    best_path: Optional[Path] = None
    best_tickers: List[str] = []
    best_reason = "NO_CSV_WITH_TICKER_COLUMN_FOUND"

    for path in unique_paths:
        try:
            df = pd.read_csv(path)
        except Exception:
            continue

        col = find_ticker_column(df)
        if col is None:
            continue

        tickers = []
        for value in df[col].tolist():
            ticker = clean_ticker(value)
            if ticker is not None:
                tickers.append(ticker)

        tickers = sorted(set(tickers))

        if 80 <= len(tickers) <= 140:
            best_path = path
            best_tickers = tickers
            best_reason = "MATCH_80_TO_140_TICKERS"
            break

        if len(tickers) > len(best_tickers):
            best_path = path
            best_tickers = tickers
            best_reason = f"BEST_AVAILABLE_{len(tickers)}_TICKERS"

    return best_tickers, best_path, best_reason


def load_or_discover_universe() -> Tuple[List[str], str]:
    if UNIVERSE_SNAPSHOT.exists():
        df = pd.read_csv(UNIVERSE_SNAPSHOT)
        col = find_ticker_column(df)
        if col is not None:
            tickers = sorted(set(filter(None, (clean_ticker(x) for x in df[col].tolist()))))
            if len(tickers) >= 50:
                return tickers, f"SNAPSHOT:{UNIVERSE_SNAPSHOT}"

    tickers, source_path, reason = discover_universe_from_csvs()

    if len(tickers) < 50:
        fail(
            "UNIVERSE_DISCOVERY_FAILED. "
            "Could not find a usable RAW105-like ticker source with at least 50 tickers."
        )

    pd.DataFrame({"ticker": tickers}).to_csv(UNIVERSE_SNAPSHOT, index=False, encoding="utf-8-sig")

    source_text = str(source_path) if source_path is not None else "UNKNOWN"
    return tickers, f"DISCOVERED:{source_text};{reason}"


def download_prices(tickers: List[str]) -> pd.DataFrame:
    try:
        import yfinance as yf
    except Exception as exc:
        fail(f"YFINANCE_IMPORT_FAILED: {exc}")

    all_tickers = sorted(set(tickers + BENCHMARKS))

    print(f"PRICE_DOWNLOAD_TICKER_COUNT: {len(all_tickers)}")

    try:
        data = yf.download(
            tickers=all_tickers,
            period="220d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=True,
            group_by="column",
        )
    except Exception as exc:
        fail(f"YFINANCE_DOWNLOAD_FAILED: {exc}")

    if data is None or data.empty:
        fail("YFINANCE_DOWNLOAD_EMPTY")

    if isinstance(data.columns, pd.MultiIndex):
        if "Close" in data.columns.get_level_values(0):
            close = data["Close"].copy()
        elif "Adj Close" in data.columns.get_level_values(0):
            close = data["Adj Close"].copy()
        else:
            fail("PRICE_DATA_MISSING_CLOSE_LEVEL")
    else:
        if "Close" in data.columns:
            close = data[["Close"]].copy()
            close.columns = all_tickers[:1]
        else:
            fail("PRICE_DATA_MISSING_CLOSE_COLUMN")

    close = close.dropna(how="all")

    if close.empty:
        fail("CLOSE_PRICE_EMPTY_AFTER_DROPNA")

    return close


def compute_one_ticker(
    ticker: str,
    close: pd.DataFrame,
    qqq_ret20: Optional[float],
    qqq_ret60: Optional[float],
) -> List[Dict[str, object]]:
    if ticker not in close.columns:
        return [
            {
                "ticker": ticker,
                "factor_id": "ALL",
                "factor_name": "ALL",
                "factor_value": None,
                "rank_metric": None,
                "status": "MISSING_PRICE_COLUMN",
                "reason": "Ticker not present in downloaded close price table",
            }
        ]

    s = close[ticker].dropna()

    if len(s) < 65:
        return [
            {
                "ticker": ticker,
                "factor_id": "ALL",
                "factor_name": "ALL",
                "factor_value": None,
                "rank_metric": None,
                "status": "INSUFFICIENT_HISTORY",
                "reason": f"Only {len(s)} valid close prices",
            }
        ]

    last = float(s.iloc[-1])
    ret20 = float(s.iloc[-1] / s.iloc[-21] - 1.0)
    ret60 = float(s.iloc[-1] / s.iloc[-61] - 1.0)

    daily_ret = s.pct_change().dropna()
    vol20 = float(daily_ret.tail(20).std())

    ma5 = float(s.tail(5).mean())
    ma10 = float(s.tail(10).mean())
    ma20 = float(s.tail(20).mean())
    high20 = float(s.tail(20).max())

    dd20 = last / high20 - 1.0 if high20 > 0 else None
    dist_ma20 = last / ma20 - 1.0 if ma20 > 0 else None

    rel20 = None if qqq_ret20 is None else ret20 - qqq_ret20
    rel60 = None if qqq_ret60 is None else ret60 - qqq_ret60
    vol_adj = None if vol20 <= 0 else ret20 / vol20

    reclaim_ma10 = 1.0 if last > ma10 else 0.0
    reclaim_ma5 = 1.0 if last > ma5 else 0.0
    pullback_depth_ok = 1.0 if dd20 is not None and -0.15 <= dd20 <= -0.02 else 0.0
    pullback_repair = reclaim_ma10 + 0.5 * reclaim_ma5 + pullback_depth_ok + (dd20 if dd20 is not None else 0.0)

    neutral_target = 0.03
    dist_rank_metric = None if dist_ma20 is None else -abs(dist_ma20 - neutral_target)

    rows = [
        {
            "ticker": ticker,
            "factor_id": "F001",
            "factor_name": "REL_STRENGTH_20D",
            "factor_value": rel20,
            "rank_metric": rel20,
            "status": "OK" if rel20 is not None else "MISSING_BENCHMARK",
            "reason": "",
        },
        {
            "ticker": ticker,
            "factor_id": "F002",
            "factor_name": "REL_STRENGTH_60D",
            "factor_value": rel60,
            "rank_metric": rel60,
            "status": "OK" if rel60 is not None else "MISSING_BENCHMARK",
            "reason": "",
        },
        {
            "ticker": ticker,
            "factor_id": "F003",
            "factor_name": "VOL_ADJ_MOMENTUM_20D",
            "factor_value": vol_adj,
            "rank_metric": vol_adj,
            "status": "OK" if vol_adj is not None else "BAD_VOLATILITY",
            "reason": "",
        },
        {
            "ticker": ticker,
            "factor_id": "F004",
            "factor_name": "PULLBACK_REPAIR_20D",
            "factor_value": pullback_repair,
            "rank_metric": pullback_repair,
            "status": "OK",
            "reason": "",
        },
        {
            "ticker": ticker,
            "factor_id": "F005",
            "factor_name": "DIST_TO_MA20",
            "factor_value": dist_ma20,
            "rank_metric": dist_rank_metric,
            "status": "OK" if dist_ma20 is not None else "BAD_MA20",
            "reason": "",
        },
    ]

    return rows


def add_rank_and_zscore(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["factor_rank"] = None
    result["factor_zscore"] = None

    for factor_id, idx in result.groupby("factor_id").groups.items():
        if factor_id == "ALL":
            continue

        sub = result.loc[idx].copy()
        ok_mask = sub["status"].eq("OK") & sub["rank_metric"].notna()

        if ok_mask.sum() == 0:
            continue

        values = pd.to_numeric(sub.loc[ok_mask, "rank_metric"], errors="coerce")
        ranks = values.rank(ascending=False, method="min")

        mean = values.mean()
        std = values.std(ddof=0)

        result.loc[values.index, "factor_rank"] = ranks.astype(int)

        if std and std > 0:
            result.loc[values.index, "factor_zscore"] = (values - mean) / std
        else:
            result.loc[values.index, "factor_zscore"] = 0.0

    return result


def write_markdown(df: pd.DataFrame, universe_count: int, source: str) -> None:
    lines: List[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.extend(
        [
            "# V18.1B Factor Values Current",
            "",
            f"Generated: {now}",
            "",
            "## 1. Status",
            "",
            "- V18_1B_STATUS: `OK_FACTOR_VALUES_COMPUTED_SHADOW_ONLY`",
            "- OFFICIAL_DECISION_IMPACT: `NONE`",
            f"- UNIVERSE_COUNT: `{universe_count}`",
            f"- UNIVERSE_SOURCE: `{source}`",
            "",
            "## 2. Important Rule",
            "",
            "These factors are research/shadow-only. They do not change V17.8D BUY / NO_BUY decisions.",
            "",
        ]
    )

    ok_df = df[df["status"].eq("OK")].copy()

    for factor_id in sorted(ok_df["factor_id"].unique()):
        factor_df = ok_df[ok_df["factor_id"].eq(factor_id)].copy()
        factor_df = factor_df.sort_values("factor_rank").head(20)

        factor_name = factor_df["factor_name"].iloc[0] if not factor_df.empty else factor_id

        lines.extend(
            [
                f"## 3. Top 20 - {factor_id} {factor_name}",
                "",
                "| rank | ticker | factor_value | zscore |",
                "|---:|---|---:|---:|",
            ]
        )

        for _, row in factor_df.iterrows():
            rank = row.get("factor_rank", "")
            ticker = row.get("ticker", "")
            value = row.get("factor_value", "")
            zscore = row.get("factor_zscore", "")

            value_text = "" if pd.isna(value) else f"{float(value):.6f}"
            zscore_text = "" if pd.isna(zscore) else f"{float(zscore):.4f}"

            lines.append(f"| {rank} | {ticker} | {value_text} | {zscore_text} |")

        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def write_read_first(df: pd.DataFrame, universe_count: int, source: str) -> None:
    ok_count = int(df["status"].eq("OK").sum())
    fail_count = int((~df["status"].eq("OK")).sum())
    factor_count = int(df[df["factor_id"].ne("ALL")]["factor_id"].nunique())

    lines = [
        "=== V18.1B FACTOR VALUE COMPUTE READ FIRST ===",
        "",
        "STATUS:",
        "V18_1B_STATUS: OK_FACTOR_VALUES_COMPUTED_SHADOW_ONLY",
        "",
        "OFFICIAL_DECISION_IMPACT:",
        "NONE",
        "",
        "UNIVERSE:",
        f"UNIVERSE_COUNT: {universe_count}",
        f"UNIVERSE_SOURCE: {source}",
        "",
        "FACTOR SUMMARY:",
        f"FACTOR_COUNT: {factor_count}",
        f"FACTOR_VALUE_OK_COUNT: {ok_count}",
        f"FACTOR_VALUE_FAIL_OR_WARN_COUNT: {fail_count}",
        "",
        "OUTPUTS:",
        str(OUT_CSV),
        str(OUT_MD),
        str(AUDIT_CSV),
        str(MANIFEST_PATH),
        "",
        "NEXT_STEP:",
        "V18.2A should validate factor effectiveness using forward returns, IC, quantile spreads, and benchmark comparison.",
        "",
        "IMPORTANT:",
        "This version computes research/shadow factors only. It does not modify V17.8D official daily decision outputs.",
    ]

    READ_FIRST.write_text("\n".join(lines), encoding="utf-8")


def write_audit(df: pd.DataFrame, universe_count: int, source: str) -> None:
    rows = [
        {
            "version": VERSION,
            "status": "OK_FACTOR_VALUES_COMPUTED_SHADOW_ONLY",
            "official_decision_impact": "NONE",
            "universe_count": universe_count,
            "universe_source": source,
            "factor_rows": len(df),
            "ok_rows": int(df["status"].eq("OK").sum()),
            "non_ok_rows": int((~df["status"].eq("OK")).sum()),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    ]

    pd.DataFrame(rows).to_csv(AUDIT_CSV, index=False, encoding="utf-8-sig")


def write_manifest() -> None:
    rows = []
    for path in [OUT_CSV, OUT_MD, READ_FIRST, AUDIT_CSV, UNIVERSE_SNAPSHOT]:
        if path.exists():
            rows.append(
                {
                    "version": VERSION,
                    "path": str(path),
                    "length_bytes": path.stat().st_size,
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "purpose": "factor_value_compute_shadow_only",
                }
            )

    pd.DataFrame(rows).to_csv(MANIFEST_PATH, index=False, encoding="utf-8-sig")


def main() -> None:
    ensure_dirs()

    if not REGISTRY_PATH.exists():
        fail(f"FACTOR_REGISTRY_MISSING: {REGISTRY_PATH}. Run V18.1A first.")

    tickers, source = load_or_discover_universe()

    print("")
    print("=== V18.1B FACTOR VALUE COMPUTE START ===")
    print(f"UNIVERSE_COUNT: {len(tickers)}")
    print(f"UNIVERSE_SOURCE: {source}")

    close = download_prices(tickers)

    if "QQQ" not in close.columns:
        fail("QQQ_BENCHMARK_PRICE_MISSING")

    qqq = close["QQQ"].dropna()
    if len(qqq) < 65:
        fail("QQQ_BENCHMARK_INSUFFICIENT_HISTORY")

    qqq_ret20 = float(qqq.iloc[-1] / qqq.iloc[-21] - 1.0)
    qqq_ret60 = float(qqq.iloc[-1] / qqq.iloc[-61] - 1.0)

    all_rows: List[Dict[str, object]] = []
    for ticker in tickers:
        all_rows.extend(compute_one_ticker(ticker, close, qqq_ret20, qqq_ret60))

    df = pd.DataFrame(all_rows)
    df.insert(0, "factor_date", datetime.now().strftime("%Y-%m-%d"))
    df.insert(1, "version", VERSION)
    df["official_decision_impact"] = "NONE"
    df["source"] = "V18_FACTOR_LAB_SHADOW_ONLY"

    df = add_rank_and_zscore(df)

    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    write_markdown(df, len(tickers), source)
    write_read_first(df, len(tickers), source)
    write_audit(df, len(tickers), source)
    write_manifest()

    print("")
    print("=== V18.1B FACTOR VALUE COMPUTE READY ===")
    print("V18_1B_STATUS: OK_FACTOR_VALUES_COMPUTED_SHADOW_ONLY")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print(f"UNIVERSE_COUNT: {len(tickers)}")
    print(f"FACTOR_ROWS: {len(df)}")
    print("")
    print("READ_FIRST:")
    print(str(READ_FIRST))
    print("")
    print("FACTOR_VALUES:")
    print(str(OUT_CSV))
    print("")
    print("FACTOR_PANEL:")
    print(str(OUT_MD))
    print("")
    print("NEXT_VERSION:")
    print("V18.2A_FACTOR_VALIDATION_FORWARD_RETURNS")
    print("")
    print("=== DONE ===")


if __name__ == "__main__":
    main()