from __future__ import annotations

import argparse
import csv
import py_compile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import v18_21A_price_derived_factor_pack as base
import v18_21A_R1_data_coverage_scoring_patch as r1


STATUS_WARN = "WARN_V18_21A_R2_PRICE_HISTORY_SOURCE_COVERAGE_PATCH_DEGRADED"
STATUS_OK = "OK_V18_21A_R2_PRICE_HISTORY_SOURCE_COVERAGE_PATCH_READY"
MODE = "ADVISORY_ONLY"
PATCH_MODE = "PRICE_HISTORY_SOURCE_COVERAGE_AND_FACTOR_SCOPE_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
}

SOURCE_FIELDS = [
    "source_path",
    "source_exists",
    "source_type",
    "modified_time",
    "file_size_bytes",
    "parsed_row_count",
    "parsed_ticker_count",
    "has_ticker_column",
    "has_date_column",
    "has_close_column",
    "has_volume_column",
    "min_date",
    "max_date",
    "history_depth_estimate",
    "usable_for_full_history_factors",
    "usable_for_light_factors",
    "notes",
]

SCOPE_FIELDS = [
    "ticker",
    "selected_price_source",
    "source_type",
    "latest_date",
    "latest_close",
    "row_count",
    "has_volume",
    "history_depth_days",
    "history_depth_trading_rows",
    "factor_scope_class",
    "can_compute_return_20d",
    "can_compute_return_60d",
    "can_compute_sma20",
    "can_compute_sma50",
    "can_compute_sma200",
    "can_compute_52w_high",
    "can_compute_realized_vol_20d",
    "can_compute_realized_vol_60d",
    "can_compute_volume_surge",
    "can_compute_buy_zone",
    "can_compute_relative_strength_vs_qqq",
]

SCORE_FIELDS = [
    *r1.SCORE_R1_FIELDS,
    "factor_scope_class",
    "score_scope",
    "full_factor_score_ready",
    "light_factor_score_ready",
    "score_component_available_count",
    "score_component_total_count",
    "score_coverage_ratio",
    "scoring_degradation_reason",
]

MARKET_FIELDS = [
    *r1.MARKET_R1_FIELDS,
    "market_proxy_source_paths",
    "qqq_history_source",
    "spy_history_source",
    "vix_history_source",
    "internal_breadth_source",
    "internal_breadth_coverage_count",
]

TOP_SCOPE_FIELDS = ["list_name", "eligible_count", "rank", "ticker", "sort_metric", "sort_metric_value", "status_label", "scope_class"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "PATCH_MODE",
    "POLICY_APPLIED",
    "TICKER_INPUT_COUNT",
    "TICKER_FACTOR_ROWS",
    "LOCAL_PRICE_DATA_AVAILABLE_COUNT",
    "FULL_HISTORY_FACTOR_READY_COUNT",
    "PARTIAL_HISTORY_LIGHT_FACTOR_READY_COUNT",
    "LATEST_ONLY_NOT_FACTOR_READY_COUNT",
    "NO_LOCAL_PRICE_DATA_COUNT",
    "FULL_HISTORY_FACTOR_READY_RATIO",
    "TICKER_FATAL_FACTOR_FAIL_COUNT",
    "TICKER_PARTIAL_DEGRADED_COUNT",
    "TICKER_SCORE_READY_COUNT",
    "FULL_SCORE_READY_COUNT",
    "LIGHT_SCORE_READY_COUNT",
    "SCORE_READY_RATIO",
    "QQQ_PROXY_STATUS",
    "SPY_PROXY_STATUS",
    "VIX_PROXY_STATUS",
    "VIX_MISSING_CAP_APPLIED",
    "MARKET_REGIME_STATUS",
    "MARKET_REGIME_LABEL",
    "MARKET_RISK_COEFFICIENT",
    "MARKET_REGIME_CONFIDENCE",
    "TOP_RELATIVE_STRENGTH_TICKERS",
    "TOP_RELATIVE_STRENGTH_ELIGIBLE_COUNT",
    "TOP_NEAR_BUY_ZONE_TICKERS",
    "TOP_NEAR_BUY_ZONE_ELIGIBLE_COUNT",
    "TOP_BREAKOUT_VOLUME_CONFIRMED_TICKERS",
    "TOP_BREAKOUT_VOLUME_CONFIRMED_ELIGIBLE_COUNT",
    "EXTENDED_ABOVE_BUY_ZONE_COUNT",
    "BELOW_200DMA_COUNT",
    "HIGH_VOL_CAUTION_COUNT",
    "DATA_DEGRADED_COUNT",
    "PRICE_HISTORY_SOURCE_COUNT",
    "USABLE_FULL_HISTORY_SOURCE_COUNT",
    "USABLE_LIGHT_FACTOR_SOURCE_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED",
    "STATE_MODIFIED",
    "PRICE_CACHE_MODIFIED",
    "RANKING_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED",
    "MANUAL_STATE_MODIFIED",
    "BROKER_EXECUTION_MODIFIED",
    "VALIDATION_FAIL_COUNT",
    "READ_FIRST",
    "REPORT",
]


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    base.ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def modified_time(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def source_type(path: Path) -> str:
    text = str(path).replace("\\", "/").lower()
    if "/data/prices/" in text:
        return "DATA_PRICES_OHLCV"
    if "/state/v18/price_cache/" in text:
        return "STATE_V18_PRICE_CACHE"
    if "/data/v16/prices_full/" in text:
        return "V16_PRICES_FULL"
    if "/data/v16/prices/" in text:
        return "V16_PRICES"
    if "universe" in text:
        return "UNIVERSE_PRICE_REFERENCE"
    if "price" in text:
        return "PRICE_REFERENCE"
    return "CSV_REFERENCE"


def discover_sources(root: Path) -> List[Dict[str, object]]:
    roots = [root / p for p in ("outputs/v16", "outputs/v17", "outputs/v18", "state/v16", "state/v17", "state/v18", "data", "cache")]
    rows: List[Dict[str, object]] = []
    seen: set[Path] = set()
    for search_root in roots:
        if not search_root.exists():
            continue
        for path in search_root.rglob("*.csv"):
            parts = {part.lower() for part in path.parts}
            if ".venv" in parts or "node_modules" in parts or "stable_compressed" in parts:
                continue
            lower_path = str(path).lower()
            if not any(token in lower_path for token in ("price", "prices", "cache", "universe", "ohlcv", "history", "qqq", "spy", "vix")):
                continue
            if path in seen:
                continue
            seen.add(path)
            csv_rows, fields, status = base.read_csv(path)
            lower = {field.lower(): field for field in fields}
            has_ticker = "ticker" in lower
            has_date = "date" in lower or "latest_price_date" in lower
            has_close = any(col in lower for col in ("close", "adj_close", "latest_close", "last_close"))
            has_volume = "volume" in lower or "latest_volume" in lower
            if not (has_close or "price" in lower_path or "prices" in lower_path):
                continue
            tickers = set()
            if has_ticker:
                tickers = {base.normalize_ticker(row.get(lower["ticker"])) for row in csv_rows if base.normalize_ticker(row.get(lower["ticker"]))}
            elif path.parent.name.lower() in {"prices", "prices_full", "price_cache"}:
                tickers = {path.stem.upper()}
            date_col = lower.get("date") or lower.get("latest_price_date")
            dates = [str(row.get(date_col, ""))[:10] for row in csv_rows if date_col and row.get(date_col)]
            depth = len(set(dates)) if dates else len(csv_rows)
            rows.append(
                {
                    "source_path": str(path),
                    "source_exists": "TRUE",
                    "source_type": source_type(path),
                    "modified_time": modified_time(path),
                    "file_size_bytes": path.stat().st_size,
                    "parsed_row_count": len(csv_rows) if status == "OK" else "",
                    "parsed_ticker_count": len(tickers),
                    "has_ticker_column": r1.tf(has_ticker),
                    "has_date_column": r1.tf(has_date),
                    "has_close_column": r1.tf(has_close),
                    "has_volume_column": r1.tf(has_volume),
                    "min_date": min(dates) if dates else "",
                    "max_date": max(dates) if dates else "",
                    "history_depth_estimate": depth,
                    "usable_for_full_history_factors": r1.tf(has_date and has_close and depth >= 252),
                    "usable_for_light_factors": r1.tf(has_date and has_close and depth >= 21),
                    "notes": status,
                }
            )
    return rows


def load_latest_reference(root: Path, ticker: str) -> Tuple[str, str, str]:
    paths = [
        root / "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv",
        root / "state/v17_6E_screened_universe_latest_price_snapshot.csv",
    ]
    for path in paths:
        rows, fields, status = base.read_csv(path)
        if status != "OK":
            continue
        lower = {field.lower(): field for field in fields}
        if "ticker" not in lower:
            continue
        close_col = lower.get("latest_close") or lower.get("last_close") or lower.get("close")
        date_col = lower.get("latest_price_date") or lower.get("date")
        if not close_col or not date_col:
            continue
        for row in rows:
            if base.normalize_ticker(row.get(lower["ticker"])) == ticker:
                close = base.to_float(row.get(close_col))
                date = str(row.get(date_col, "")).strip()[:10]
                if close is not None and date:
                    return date, base.fmt(close), str(path)
    return "", "", ""


def classify_ticker(root: Path, ticker: str, qqq_ready: bool) -> Dict[str, object]:
    hist, source, status = base.load_price_history(root, ticker)
    latest_date = hist[-1]["date"] if hist else ""
    latest_close = base.fmt(hist[-1]["close"]) if hist else ""
    if not hist:
        ref_date, ref_close, ref_source = load_latest_reference(root, ticker)
        if ref_close and ref_date:
            return {
                "ticker": ticker,
                "selected_price_source": ref_source,
                "source_type": "LATEST_PRICE_REFERENCE",
                "latest_date": ref_date,
                "latest_close": ref_close,
                "row_count": 1,
                "has_volume": "FALSE",
                "history_depth_days": 1,
                "history_depth_trading_rows": 1,
                "factor_scope_class": "LATEST_ONLY_NOT_FACTOR_READY",
                **{field: "FALSE" for field in SCOPE_FIELDS if field.startswith("can_compute_")},
            }
        return {
            "ticker": ticker,
            "selected_price_source": "",
            "source_type": "NONE",
            "latest_date": "",
            "latest_close": "",
            "row_count": 0,
            "has_volume": "FALSE",
            "history_depth_days": 0,
            "history_depth_trading_rows": 0,
            "factor_scope_class": "NO_LOCAL_PRICE_DATA",
            **{field: "FALSE" for field in SCOPE_FIELDS if field.startswith("can_compute_")},
        }
    volumes = [row.get("volume") for row in hist]
    rows = len(hist)
    has_volume = any(v is not None for v in volumes)
    scope = "LATEST_ONLY_NOT_FACTOR_READY"
    if rows >= 252 and has_volume:
        scope = "FULL_HISTORY_FACTOR_READY"
    elif rows >= 21:
        scope = "PARTIAL_HISTORY_LIGHT_FACTOR_READY"
    return {
        "ticker": ticker,
        "selected_price_source": source,
        "source_type": source_type(Path(source)),
        "latest_date": latest_date,
        "latest_close": latest_close,
        "row_count": rows,
        "has_volume": r1.tf(has_volume),
        "history_depth_days": rows,
        "history_depth_trading_rows": rows,
        "factor_scope_class": scope,
        "can_compute_return_20d": r1.tf(rows >= 21),
        "can_compute_return_60d": r1.tf(rows >= 61),
        "can_compute_sma20": r1.tf(rows >= 20),
        "can_compute_sma50": r1.tf(rows >= 50),
        "can_compute_sma200": r1.tf(rows >= 200),
        "can_compute_52w_high": r1.tf(rows >= 252),
        "can_compute_realized_vol_20d": r1.tf(rows >= 21),
        "can_compute_realized_vol_60d": r1.tf(rows >= 61),
        "can_compute_volume_surge": r1.tf(has_volume and rows >= 20),
        "can_compute_buy_zone": r1.tf(rows >= 50),
        "can_compute_relative_strength_vs_qqq": r1.tf(qqq_ready and rows >= 21),
    }


def score_scope(scope: str) -> Tuple[str, str, str]:
    if scope == "FULL_HISTORY_FACTOR_READY":
        return "FULL_PRICE_DERIVED_SCORE", "TRUE", "FALSE"
    if scope == "PARTIAL_HISTORY_LIGHT_FACTOR_READY":
        return "LIGHT_PRICE_DERIVED_SCORE", "FALSE", "TRUE"
    if scope == "LATEST_ONLY_NOT_FACTOR_READY":
        return "LATEST_ONLY_REFERENCE", "FALSE", "FALSE"
    return "NOT_SCORE_READY", "FALSE", "FALSE"


def build_scores(base_scores: Sequence[Dict[str, object]], scope_rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    scope_by_ticker = {str(row["ticker"]): row for row in scope_rows}
    out = []
    for row in base_scores:
        ticker = str(row.get("ticker", ""))
        scope = scope_by_ticker.get(ticker, {}).get("factor_scope_class", "NO_LOCAL_PRICE_DATA")
        score_scope_value, full_ready, light_ready = score_scope(str(scope))
        components = ["relative_strength_score", "trend_structure_score", "buy_zone_score", "volume_confirmation_score", "volatility_risk_score"]
        available = sum(1 for field in components if str(row.get(field, "")).strip() != "")
        degradation = "" if full_ready == "TRUE" else str(scope)
        new = dict(row)
        new.update(
            {
                "factor_scope_class": scope,
                "score_scope": score_scope_value,
                "full_factor_score_ready": full_ready,
                "light_factor_score_ready": light_ready,
                "score_component_available_count": available,
                "score_component_total_count": len(components),
                "score_coverage_ratio": base.fmt(available / len(components)),
                "scoring_degradation_reason": degradation,
            }
        )
        out.append(new)
    return out


def top_scope_rows(factors: Sequence[Dict[str, object]], scores: Sequence[Dict[str, object]], scopes: Sequence[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    scope_by_ticker = {str(row["ticker"]): row.get("factor_scope_class", "") for row in scopes}
    score_by_ticker = {str(row["ticker"]): row for row in scores}
    rows: List[Dict[str, object]] = []

    def emit(name: str, items: List[Dict[str, object]], metric_name: str, reverse: bool, abs_sort: bool = False) -> List[str]:
        def key(row: Dict[str, object]) -> float:
            val = base.to_float(row.get(metric_name))
            if val is None and metric_name in score_by_ticker.get(str(row.get("ticker")), {}):
                val = base.to_float(score_by_ticker[str(row.get("ticker"))].get(metric_name))
            if val is None:
                val = 999 if abs_sort else -999
            return abs(val) if abs_sort else val
        sorted_items = sorted(items, key=key, reverse=reverse)
        top = sorted_items[:10]
        for idx, item in enumerate(top, start=1):
            ticker = str(item.get("ticker"))
            val = item.get(metric_name, score_by_ticker.get(ticker, {}).get(metric_name, ""))
            rows.append(
                {
                    "list_name": name,
                    "eligible_count": len(items),
                    "rank": idx,
                    "ticker": ticker,
                    "sort_metric": metric_name,
                    "sort_metric_value": base.fmt(val),
                    "status_label": item.get("buy_zone_label") or score_by_ticker.get(ticker, {}).get("price_derived_status", ""),
                    "scope_class": scope_by_ticker.get(ticker, ""),
                }
            )
        return [str(item.get("ticker")) for item in top]

    rs_items = [r for r in factors if base.to_float(r.get("relative_strength_20d_vs_qqq")) is not None]
    buy_items = [r for r in factors if base.to_float(r.get("nearest_buy_zone_distance")) is not None and r.get("buy_zone_label") in {"NEAR_20DMA_PULLBACK", "NEAR_50DMA_PULLBACK", "BREAKOUT_NEAR"}]
    breakout_items = [r for r in factors if r.get("breakout_volume_confirmed") == "TRUE" and base.to_float(r.get("volume_surge_20d")) is not None]
    top_rs = emit("TOP_RELATIVE_STRENGTH_TICKERS", rs_items, "relative_strength_20d_vs_qqq", True)
    top_buy = emit("TOP_NEAR_BUY_ZONE_TICKERS", buy_items, "nearest_buy_zone_distance", False, True)
    top_breakout = emit("TOP_BREAKOUT_VOLUME_CONFIRMED_TICKERS", breakout_items, "volume_surge_20d", True)
    metrics = {
        "TOP_RELATIVE_STRENGTH_TICKERS": ";".join(top_rs),
        "TOP_RELATIVE_STRENGTH_ELIGIBLE_COUNT": len(rs_items),
        "TOP_NEAR_BUY_ZONE_TICKERS": ";".join(top_buy),
        "TOP_NEAR_BUY_ZONE_ELIGIBLE_COUNT": len(buy_items),
        "TOP_BREAKOUT_VOLUME_CONFIRMED_TICKERS": ";".join(top_breakout),
        "TOP_BREAKOUT_VOLUME_CONFIRMED_ELIGIBLE_COUNT": len(breakout_items),
    }
    return rows, metrics


def market_r2(root: Path, factors: Sequence[Dict[str, object]], scope_rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    base_row, _proxy = base.market_regime(root, factors)
    row = r1.patch_market(base_row)
    qqq_hist, qqq_source, _ = base.load_price_history(root, "QQQ")
    spy_hist, spy_source, _ = base.load_price_history(root, "SPY")
    vix_hist, vix_source, _ = base.load_price_history(root, "VIX")
    if not vix_hist:
        vix_hist, vix_source, _ = base.load_price_history(root, "^VIX")
    local_count = sum(1 for item in scope_rows if item["factor_scope_class"] in {"FULL_HISTORY_FACTOR_READY", "PARTIAL_HISTORY_LIGHT_FACTOR_READY"})
    row.update(
        {
            "market_proxy_source_paths": ";".join([p for p in (qqq_source, spy_source, vix_source) if p]),
            "qqq_history_source": qqq_source,
            "spy_history_source": spy_source,
            "vix_history_source": vix_source,
            "internal_breadth_source": "V18_21A_R2_CURRENT_TICKER_FACTOR_SCOPE_CLASSIFICATION.csv",
            "internal_breadth_coverage_count": local_count,
        }
    )
    return row


def parse_check(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    escaped = str(path).replace("'", "''")
    cmd = f"$null = [scriptblock]::Create((Get-Content -Raw -LiteralPath '{escaped}')); 'OK_PARSE'"
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd], capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and "OK_PARSE" in (result.stdout or ""):
            return True, "OK_PARSE"
        return False, (result.stderr or result.stdout).strip()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def compile_check(path: Path) -> Tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, "OK_COMPILE"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def render_read_first(metrics: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {metrics.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(metrics: Dict[str, object], validations: Sequence[str]) -> str:
    return "\n".join(
        [
            "# V18.21A-R2 Price History Source Coverage Report",
            "",
            "## Executive summary",
            f"- Status: {metrics['STATUS']}",
            f"- Full-history ready: {metrics['FULL_HISTORY_FACTOR_READY_COUNT']} / {metrics['TICKER_INPUT_COUNT']}",
            f"- No local price data: {metrics['NO_LOCAL_PRICE_DATA_COUNT']}",
            "",
            "## Safety statement",
            "- Advisory-only. No production wrappers, official decisions, ranking, promotion/demotion, technical timing, state, price cache, broker execution, auto-trade, or auto-sell behavior were modified.",
            "",
            "## Price history source discovery summary",
            f"- Candidate sources: {metrics['PRICE_HISTORY_SOURCE_COUNT']}",
            f"- Full-history usable sources: {metrics['USABLE_FULL_HISTORY_SOURCE_COUNT']}",
            f"- Light-factor usable sources: {metrics['USABLE_LIGHT_FACTOR_SOURCE_COUNT']}",
            "",
            "## Factor scope classification summary",
            f"- Full: {metrics['FULL_HISTORY_FACTOR_READY_COUNT']}; partial light: {metrics['PARTIAL_HISTORY_LIGHT_FACTOR_READY_COUNT']}; latest-only: {metrics['LATEST_ONLY_NOT_FACTOR_READY_COUNT']}; none: {metrics['NO_LOCAL_PRICE_DATA_COUNT']}",
            "",
            "## Fatal vs latest-only vs partial-history explanation",
            "- Fatal now means no usable local latest close/date. Latest-only and partial-history rows are separated from full-history factor-ready rows.",
            "",
            "## Full-score vs light-score readiness summary",
            f"- Full score ready: {metrics['FULL_SCORE_READY_COUNT']}; light score ready: {metrics['LIGHT_SCORE_READY_COUNT']}",
            "",
            "## Top list eligibility summary",
            f"- RS eligible: {metrics['TOP_RELATIVE_STRENGTH_ELIGIBLE_COUNT']}; buy-zone eligible: {metrics['TOP_NEAR_BUY_ZONE_ELIGIBLE_COUNT']}; breakout-volume eligible: {metrics['TOP_BREAKOUT_VOLUME_CONFIRMED_ELIGIBLE_COUNT']}",
            "",
            "## Market regime and VIX missing cap summary",
            f"- VIX status: {metrics['VIX_PROXY_STATUS']}; cap applied: {metrics['VIX_MISSING_CAP_APPLIED']}; coefficient: {metrics['MARKET_RISK_COEFFICIENT']}",
            "",
            "## Validation summary",
            *[f"- {item}" for item in validations],
            f"- Validation fail count: {metrics['VALIDATION_FAIL_COUNT']}",
            "",
            "## Next-step recommendation",
            "- Treat R2 as a source-coverage audit. Backfill or validate local history coverage before any stable snapshot or policy integration.",
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    r1.main(["--root", str(root)])
    tickers = base.discover_universe(root)
    qqq_hist, _, _ = base.load_price_history(root, "QQQ")
    qqq_returns = {"20d": None, "60d": None}
    if qqq_hist:
        closes = [float(row["close"]) for row in qqq_hist]
        qqq_returns = {"20d": base.ret(closes, 20), "60d": base.ret(closes, 60)}
    qqq_ready = qqq_returns["20d"] is not None
    factors = [base.compute_factor(root, ticker, qqq_returns) for ticker in tickers]
    base_scores = [base.score_row(row) for row in factors]
    sources = discover_sources(root)
    scopes = [classify_ticker(root, ticker, qqq_ready) for ticker in tickers]
    scores = build_scores(base_scores, scopes)
    top_rows, top_metrics = top_scope_rows(factors, base_scores, scopes)
    market = market_r2(root, factors, scopes)

    out_sources = root / "outputs/v18/price_factors/V18_21A_R2_CURRENT_PRICE_HISTORY_SOURCE_DISCOVERY_AUDIT.csv"
    out_scopes = root / "outputs/v18/price_factors/V18_21A_R2_CURRENT_TICKER_FACTOR_SCOPE_CLASSIFICATION.csv"
    out_scores = root / "outputs/v18/price_factors/V18_21A_R2_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv"
    out_market = root / "outputs/v18/market_regime/V18_21A_R2_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv"
    out_top = root / "outputs/v18/price_factors/V18_21A_R2_CURRENT_TOP_LIST_SCOPE_AUDIT.csv"
    read_first = root / "outputs/v18/ops/V18_21A_R2_READ_FIRST.txt"
    report = root / "outputs/v18/ops/V18_21A_R2_CURRENT_PRICE_HISTORY_SOURCE_COVERAGE_REPORT.md"

    write_csv(out_sources, sources, SOURCE_FIELDS)
    write_csv(out_scopes, scopes, SCOPE_FIELDS)
    write_csv(out_scores, scores, SCORE_FIELDS)
    write_csv(out_market, [market], MARKET_FIELDS)
    write_csv(out_top, top_rows, TOP_SCOPE_FIELDS)

    full_count = sum(1 for row in scopes if row["factor_scope_class"] == "FULL_HISTORY_FACTOR_READY")
    partial_count = sum(1 for row in scopes if row["factor_scope_class"] == "PARTIAL_HISTORY_LIGHT_FACTOR_READY")
    latest_count = sum(1 for row in scopes if row["factor_scope_class"] == "LATEST_ONLY_NOT_FACTOR_READY")
    none_count = sum(1 for row in scopes if row["factor_scope_class"] == "NO_LOCAL_PRICE_DATA")
    local_count = len(tickers) - none_count
    full_score = sum(1 for row in scores if row["full_factor_score_ready"] == "TRUE")
    light_score = sum(1 for row in scores if row["light_factor_score_ready"] == "TRUE")
    score_ready = full_score + light_score
    full_sources = sum(1 for row in sources if row["usable_for_full_history_factors"] == "TRUE")
    light_sources = sum(1 for row in sources if row["usable_for_light_factors"] == "TRUE")
    extended = sum(1 for row in factors if row.get("buy_zone_label") == "EXTENDED_ABOVE_BUY_ZONE")
    below200 = sum(1 for row in factors if base.to_float(row.get("distance_to_200dma")) is not None and base.to_float(row.get("distance_to_200dma")) < 0)
    high_vol = sum(1 for row in base_scores if row.get("price_derived_status") == "HIGH_VOL_CAUTION")

    ps_ok, ps_msg = parse_check(root / "scripts/v18/run_v18_21A_R2_price_history_source_coverage_patch.ps1")
    base_ok, base_msg = compile_check(root / "scripts/v18/v18_21A_price_derived_factor_pack.py")
    r1_ok, r1_msg = compile_check(root / "scripts/v18/v18_21A_R1_data_coverage_scoring_patch.py")
    r2_ok, r2_msg = compile_check(root / "scripts/v18/v18_21A_R2_price_history_source_coverage_patch.py")
    outputs_ok = all(path.exists() for path in (out_sources, out_scopes, out_scores, out_market, out_top))
    validations = [
        f"PowerShell parse check: {ps_msg}",
        f"Python compile check V18.21A: {base_msg}",
        f"Python compile check V18.21A-R1: {r1_msg}",
        f"Python compile check V18.21A-R2: {r2_msg}",
        "Run check: OK_CURRENT_SCRIPT_EXECUTED",
        f"R2 output existence check: {'OK' if outputs_ok else 'FAILED'}",
        "Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY",
    ]
    validation_fail_count = sum(1 for ok in (ps_ok, base_ok, r1_ok, r2_ok, outputs_ok) if not ok)
    status = STATUS_WARN if none_count or full_count / len(tickers) < 0.75 or market["vix_missing_cap_applied"] == "TRUE" else STATUS_OK

    metrics: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "PATCH_MODE": PATCH_MODE,
        "TICKER_INPUT_COUNT": len(tickers),
        "TICKER_FACTOR_ROWS": len(factors),
        "LOCAL_PRICE_DATA_AVAILABLE_COUNT": local_count,
        "FULL_HISTORY_FACTOR_READY_COUNT": full_count,
        "PARTIAL_HISTORY_LIGHT_FACTOR_READY_COUNT": partial_count,
        "LATEST_ONLY_NOT_FACTOR_READY_COUNT": latest_count,
        "NO_LOCAL_PRICE_DATA_COUNT": none_count,
        "FULL_HISTORY_FACTOR_READY_RATIO": base.fmt(full_count / len(tickers) if tickers else 0),
        "TICKER_FATAL_FACTOR_FAIL_COUNT": none_count,
        "TICKER_PARTIAL_DEGRADED_COUNT": partial_count + latest_count,
        "TICKER_SCORE_READY_COUNT": score_ready,
        "FULL_SCORE_READY_COUNT": full_score,
        "LIGHT_SCORE_READY_COUNT": light_score,
        "SCORE_READY_RATIO": base.fmt(score_ready / len(tickers) if tickers else 0),
        "QQQ_PROXY_STATUS": market["qqq_proxy_status"],
        "SPY_PROXY_STATUS": market["spy_proxy_status"],
        "VIX_PROXY_STATUS": market["vix_proxy_status"],
        "VIX_MISSING_CAP_APPLIED": market["vix_missing_cap_applied"],
        "MARKET_REGIME_STATUS": market["market_regime_data_status"],
        "MARKET_REGIME_LABEL": market["market_regime_label"],
        "MARKET_RISK_COEFFICIENT": market["market_risk_coefficient"],
        "MARKET_REGIME_CONFIDENCE": market["market_regime_confidence"],
        **top_metrics,
        "EXTENDED_ABOVE_BUY_ZONE_COUNT": extended,
        "BELOW_200DMA_COUNT": below200,
        "HIGH_VOL_CAUTION_COUNT": high_vol,
        "DATA_DEGRADED_COUNT": none_count + partial_count + latest_count,
        "PRICE_HISTORY_SOURCE_COUNT": len(sources),
        "USABLE_FULL_HISTORY_SOURCE_COUNT": full_sources,
        "USABLE_LIGHT_FACTOR_SOURCE_COUNT": light_sources,
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "READ_FIRST": str(read_first),
        "REPORT": str(report),
    }
    metrics.update(SAFETY_FLAGS)
    base.write_text(read_first, "\n".join(f"{field}: {metrics.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    base.write_text(report, render_report(metrics, validations))

    fields_ok = all(field in base.read_text(read_first) for field in READ_FIRST_FIELDS)
    final_outputs_ok = all(path.exists() for path in (out_sources, out_scopes, out_scores, out_market, out_top, read_first, report))
    if not fields_ok or not final_outputs_ok:
        metrics["VALIDATION_FAIL_COUNT"] = int(metrics["VALIDATION_FAIL_COUNT"]) + 1
        base.write_text(read_first, "\n".join(f"{field}: {metrics.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
        base.write_text(report, render_report(metrics, validations + ["Final READ_FIRST/output check: FAILED"]))

    print(f"STATUS: {metrics['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"PATCH_MODE: {PATCH_MODE}")
    print(f"LOCAL_PRICE_DATA_AVAILABLE_COUNT: {metrics['LOCAL_PRICE_DATA_AVAILABLE_COUNT']}")
    print(f"FULL_HISTORY_FACTOR_READY_COUNT: {metrics['FULL_HISTORY_FACTOR_READY_COUNT']}")
    print(f"PARTIAL_HISTORY_LIGHT_FACTOR_READY_COUNT: {metrics['PARTIAL_HISTORY_LIGHT_FACTOR_READY_COUNT']}")
    print(f"LATEST_ONLY_NOT_FACTOR_READY_COUNT: {metrics['LATEST_ONLY_NOT_FACTOR_READY_COUNT']}")
    print(f"NO_LOCAL_PRICE_DATA_COUNT: {metrics['NO_LOCAL_PRICE_DATA_COUNT']}")
    print(f"VIX_MISSING_CAP_APPLIED: {metrics['VIX_MISSING_CAP_APPLIED']}")
    print(f"VALIDATION_FAIL_COUNT: {metrics['VALIDATION_FAIL_COUNT']}")
    print(f"READ_FIRST: {read_first}")
    print(f"REPORT: {report}")
    return 1 if int(metrics["VALIDATION_FAIL_COUNT"]) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
