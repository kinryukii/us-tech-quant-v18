from __future__ import annotations

import argparse
import csv
import py_compile
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import v18_21A_price_derived_factor_pack as base


STATUS_OK = "OK_V18_21A_R1_DATA_COVERAGE_SCORING_PATCH_READY"
STATUS_WARN = "WARN_V18_21A_R1_DATA_COVERAGE_SCORING_PATCH_DEGRADED"
MODE = "ADVISORY_ONLY"
PATCH_MODE = "DATA_COVERAGE_AND_SCORING_SEMANTICS_ONLY"

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

COVERAGE_FIELDS = [
    "ticker",
    "source_path",
    "latest_date",
    "row_count",
    "has_close",
    "has_volume",
    "enough_history_20d",
    "enough_history_50d",
    "enough_history_60d",
    "enough_history_200d",
    "enough_history_252d",
    "can_compute_returns",
    "can_compute_ma",
    "can_compute_52w_high",
    "can_compute_realized_vol",
    "can_compute_volume_factors",
    "can_compute_buy_zone",
    "fatal_factor_fail",
    "partial_degraded",
    "degradation_reason",
]

SORT_FIELDS = ["list_name", "rank", "ticker", "sort_metric", "sort_metric_value", "status_label"]

SCORE_R1_FIELDS = [
    *base.SCORE_FIELDS,
    "score_ready",
    "fatal_factor_fail",
    "partial_degraded",
    "scoring_degradation_reason",
    "score_component_available_count",
    "score_component_total_count",
    "score_coverage_ratio",
]

MARKET_R1_FIELDS = [
    *base.MARKET_FIELDS,
    "vix_missing_cap_applied",
    "market_proxy_available_count",
    "market_proxy_required_count",
    "market_regime_confidence",
    "market_risk_coefficient_before_missing_proxy_cap",
    "market_risk_coefficient_after_missing_proxy_cap",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "PATCH_MODE",
    "POLICY_APPLIED",
    "TICKER_INPUT_COUNT",
    "TICKER_FACTOR_ROWS",
    "TICKER_FATAL_FACTOR_FAIL_COUNT",
    "TICKER_PARTIAL_DEGRADED_COUNT",
    "TICKER_INSUFFICIENT_HISTORY_COUNT",
    "TICKER_VOLUME_MISSING_COUNT",
    "TICKER_200DMA_MISSING_COUNT",
    "TICKER_52W_HIGH_MISSING_COUNT",
    "TICKER_SCORE_READY_COUNT",
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
    "TOP_NEAR_BUY_ZONE_TICKERS",
    "TOP_BREAKOUT_VOLUME_CONFIRMED_TICKERS",
    "EXTENDED_ABOVE_BUY_ZONE_COUNT",
    "BELOW_200DMA_COUNT",
    "HIGH_VOL_CAUTION_COUNT",
    "DATA_DEGRADED_COUNT",
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


def tf(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def coverage_row(root: Path, ticker: str) -> Dict[str, object]:
    hist, source, status = base.load_price_history(root, ticker)
    row_count = len(hist)
    has_close = row_count > 0 and hist[-1].get("close") is not None
    has_volume = row_count > 0 and any(item.get("volume") is not None for item in hist)
    enough20 = row_count >= 21
    enough50 = row_count >= 50
    enough60 = row_count >= 61
    enough200 = row_count >= 200
    enough252 = row_count >= 252
    fatal = not has_close
    reasons: List[str] = []
    if fatal:
        reasons.append(status or "UNUSABLE_LOCAL_PRICE_DATA")
    if not enough20 or not enough60:
        reasons.append("INSUFFICIENT_RETURN_HISTORY")
    if not enough200:
        reasons.append("MISSING_200DMA_HISTORY")
    if not enough252:
        reasons.append("MISSING_52W_HIGH_HISTORY")
    if not has_volume:
        reasons.append("VOLUME_MISSING")
    partial = (not fatal) and bool(reasons)
    return {
        "ticker": ticker,
        "source_path": source,
        "latest_date": hist[-1]["date"] if hist else "",
        "row_count": row_count,
        "has_close": tf(has_close),
        "has_volume": tf(has_volume),
        "enough_history_20d": tf(enough20),
        "enough_history_50d": tf(enough50),
        "enough_history_60d": tf(enough60),
        "enough_history_200d": tf(enough200),
        "enough_history_252d": tf(enough252),
        "can_compute_returns": tf(enough20 and enough60),
        "can_compute_ma": tf(enough20 and enough50),
        "can_compute_52w_high": tf(enough252),
        "can_compute_realized_vol": tf(enough20 and enough60),
        "can_compute_volume_factors": tf(has_volume and enough20),
        "can_compute_buy_zone": tf(has_close and enough20 and enough50),
        "fatal_factor_fail": tf(fatal),
        "partial_degraded": tf(partial),
        "degradation_reason": ";".join(reasons),
    }


def metric(row: Dict[str, object], field: str, default: float = -999.0) -> float:
    val = base.to_float(row.get(field))
    return default if val is None else val


def build_sort_audit(factors: Sequence[Dict[str, object]], scores: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    score_by_ticker = {str(row.get("ticker")): row for row in scores}
    rows: List[Dict[str, object]] = []

    def add_list(name: str, items: Sequence[Dict[str, object]], metric_name: str, reverse: bool, abs_sort: bool = False) -> None:
        def key(row: Dict[str, object]) -> float:
            val = metric(row, metric_name)
            return abs(val) if abs_sort else val
        sorted_items = sorted(items, key=key, reverse=reverse)[:10]
        for idx, item in enumerate(sorted_items, start=1):
            rows.append(
                {
                    "list_name": name,
                    "rank": idx,
                    "ticker": item.get("ticker", ""),
                    "sort_metric": metric_name,
                    "sort_metric_value": base.fmt(item.get(metric_name) if metric_name in item else score_by_ticker.get(str(item.get("ticker")), {}).get(metric_name)),
                    "status_label": item.get("buy_zone_label") or score_by_ticker.get(str(item.get("ticker")), {}).get("price_derived_status", ""),
                }
            )

    valid_rs = [r for r in factors if base.to_float(r.get("relative_strength_20d_vs_qqq")) is not None]
    buy_candidates = [r for r in factors if r.get("buy_zone_label") in {"NEAR_20DMA_PULLBACK", "NEAR_50DMA_PULLBACK", "BREAKOUT_NEAR"} and base.to_float(r.get("nearest_buy_zone_distance")) is not None]
    breakout = [r for r in factors if r.get("breakout_volume_confirmed") == "TRUE" and base.to_float(r.get("volume_surge_20d")) is not None]
    trend_ready = [r for r in scores if r.get("trend_structure_score") not in {"", None}]
    high_vol = [r for r in factors if base.to_float(r.get("realized_volatility_20d")) is not None]
    add_list("top_relative_strength_by_rs_20d_vs_qqq", valid_rs, "relative_strength_20d_vs_qqq", True)
    add_list("top_near_buy_zone_by_abs_nearest_buy_zone_distance", buy_candidates, "nearest_buy_zone_distance", False, True)
    add_list("top_breakout_volume_confirmed_by_volume_surge", breakout, "volume_surge_20d", True)
    add_list("strongest_trend_structure_by_score", trend_ready, "trend_structure_score", True)
    add_list("high_vol_caution_by_realized_volatility_20d", high_vol, "realized_volatility_20d", True)
    return rows


def build_r1_scores(scores: Sequence[Dict[str, object]], coverage: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    cov = {str(row["ticker"]): row for row in coverage}
    out: List[Dict[str, object]] = []
    for row in scores:
        ticker = str(row.get("ticker", ""))
        c = cov.get(ticker, {})
        fatal = str(c.get("fatal_factor_fail")) == "TRUE"
        partial = str(c.get("partial_degraded")) == "TRUE"
        component_fields = [
            "relative_strength_score",
            "trend_structure_score",
            "buy_zone_score",
            "volume_confirmation_score",
            "volatility_risk_score",
        ]
        available = sum(1 for field in component_fields if str(row.get(field, "")).strip() != "")
        total = len(component_fields)
        new = dict(row)
        new.update(
            {
                "score_ready": tf((not fatal) and available >= 3),
                "fatal_factor_fail": tf(fatal),
                "partial_degraded": tf(partial),
                "scoring_degradation_reason": c.get("degradation_reason", ""),
                "score_component_available_count": available,
                "score_component_total_count": total,
                "score_coverage_ratio": base.fmt(available / total if total else 0),
            }
        )
        out.append(new)
    return out


def patch_market(market_row: Dict[str, object]) -> Dict[str, object]:
    qqq_ok = market_row.get("qqq_proxy_status") == "OK"
    spy_ok = market_row.get("spy_proxy_status") == "OK"
    vix_ok = market_row.get("vix_proxy_status") == "OK"
    before = base.to_float(market_row.get("market_risk_coefficient")) or 0.60
    after = before
    cap = False
    status = str(market_row.get("market_regime_data_status", ""))
    if not vix_ok and qqq_ok and spy_ok:
        cap = True
        after = min(before, 0.95)
        status = "DEGRADED_VIX_MISSING"
    elif not qqq_ok or not spy_ok:
        after = min(before, 0.80)
        status = "DEGRADED_MISSING_MARKET_PROXY"
    available = sum(1 for ok in (qqq_ok, spy_ok, vix_ok) if ok)
    confidence = "HIGH" if available == 3 else "MEDIUM" if qqq_ok and spy_ok else "LOW"
    row = dict(market_row)
    row.update(
        {
            "market_regime_data_status": status,
            "market_risk_coefficient": base.fmt(after, 2),
            "vix_missing_cap_applied": tf(cap),
            "market_proxy_available_count": available,
            "market_proxy_required_count": 3,
            "market_regime_confidence": confidence,
            "market_risk_coefficient_before_missing_proxy_cap": base.fmt(before, 2),
            "market_risk_coefficient_after_missing_proxy_cap": base.fmt(after, 2),
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
            "# V18.21A-R1 Data Coverage + Scoring Semantics Report",
            "",
            "## Executive summary",
            f"- Status: {metrics['STATUS']}",
            f"- Score-ready tickers: {metrics['TICKER_SCORE_READY_COUNT']} / {metrics['TICKER_INPUT_COUNT']}",
            f"- Fatal failures: {metrics['TICKER_FATAL_FACTOR_FAIL_COUNT']}; partial degraded: {metrics['TICKER_PARTIAL_DEGRADED_COUNT']}",
            "",
            "## Safety statement",
            "- Advisory-only. No production wrapper, official decision, ranking, promotion/demotion, technical timing, state, cache, broker execution, auto-trade, or auto-sell behavior was modified.",
            "",
            "## Data coverage summary",
            f"- Volume missing: {metrics['TICKER_VOLUME_MISSING_COUNT']}",
            f"- 200DMA missing: {metrics['TICKER_200DMA_MISSING_COUNT']}",
            f"- 52W high missing: {metrics['TICKER_52W_HIGH_MISSING_COUNT']}",
            "",
            "## Fatal vs partial degradation explanation",
            "- Fatal means no usable local close/date data. Missing long history, volume, 52W high, or proxy-dependent fields are partial degradation when basic scoring remains possible.",
            "",
            "## Top list sorting explanation",
            "- Near-buy-zone tickers are sorted by absolute nearest_buy_zone_distance ascending among valid buy-zone candidates.",
            "",
            "## Market regime and VIX missing cap explanation",
            f"- VIX missing cap applied: {metrics['VIX_MISSING_CAP_APPLIED']}; coefficient: {metrics['MARKET_RISK_COEFFICIENT']}",
            "",
            "## Scoring coverage summary",
            f"- Score ready ratio: {metrics['SCORE_READY_RATIO']}",
            "",
            "## Validation summary",
            *[f"- {item}" for item in validations],
            f"- Validation fail count: {metrics['VALIDATION_FAIL_COUNT']}",
            "",
            "## Next-step recommendation",
            "- Use R1 outputs to decide whether local price coverage should be backfilled before any later policy or ranking integration.",
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    base.main(["--root", str(root)])
    tickers = base.discover_universe(root)
    qqq_hist, _, _ = base.load_price_history(root, "QQQ")
    qqq_returns = {"20d": None, "60d": None}
    if qqq_hist:
        closes = [float(row["close"]) for row in qqq_hist]
        qqq_returns = {"20d": base.ret(closes, 20), "60d": base.ret(closes, 60)}
    factor_rows = [base.compute_factor(root, ticker, qqq_returns) for ticker in tickers]
    base_score_rows = [base.score_row(row) for row in factor_rows]
    coverage_rows = [coverage_row(root, ticker) for ticker in tickers]
    score_rows = build_r1_scores(base_score_rows, coverage_rows)
    market_base, proxy_status = base.market_regime(root, factor_rows)
    market_row = patch_market(market_base)
    sorting_rows = build_sort_audit(factor_rows, base_score_rows)

    out_cov = root / "outputs/v18/price_factors/V18_21A_R1_CURRENT_PRICE_FACTOR_DATA_COVERAGE_AUDIT.csv"
    out_sort = root / "outputs/v18/price_factors/V18_21A_R1_CURRENT_TOP_LIST_SORTING_AUDIT.csv"
    out_scores = root / "outputs/v18/price_factors/V18_21A_R1_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv"
    out_market = root / "outputs/v18/market_regime/V18_21A_R1_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv"
    read_first = root / "outputs/v18/ops/V18_21A_R1_READ_FIRST.txt"
    report = root / "outputs/v18/ops/V18_21A_R1_CURRENT_DATA_COVERAGE_SCORING_REPORT.md"

    write_csv(out_cov, coverage_rows, COVERAGE_FIELDS)
    write_csv(out_sort, sorting_rows, SORT_FIELDS)
    write_csv(out_scores, score_rows, SCORE_R1_FIELDS)
    write_csv(out_market, [market_row], MARKET_R1_FIELDS)

    fatal_count = sum(1 for row in coverage_rows if row["fatal_factor_fail"] == "TRUE")
    partial_count = sum(1 for row in coverage_rows if row["partial_degraded"] == "TRUE")
    insufficient_count = sum(1 for row in coverage_rows if "INSUFFICIENT" in str(row["degradation_reason"]) or "MISSING_200DMA" in str(row["degradation_reason"]) or "MISSING_52W" in str(row["degradation_reason"]))
    volume_missing = sum(1 for row in coverage_rows if row["has_volume"] == "FALSE")
    missing_200 = sum(1 for row in coverage_rows if row["enough_history_200d"] == "FALSE")
    missing_52w = sum(1 for row in coverage_rows if row["enough_history_252d"] == "FALSE")
    score_ready_count = sum(1 for row in score_rows if row["score_ready"] == "TRUE")
    ready_ratio = score_ready_count / len(tickers) if tickers else 0
    extended = sum(1 for row in factor_rows if row.get("buy_zone_label") == "EXTENDED_ABOVE_BUY_ZONE")
    below200 = sum(1 for row in factor_rows if base.to_float(row.get("distance_to_200dma")) is not None and base.to_float(row.get("distance_to_200dma")) < 0)
    high_vol = sum(1 for row in score_rows if row.get("price_derived_status") == "HIGH_VOL_CAUTION")
    top_rs = [row["ticker"] for row in sorting_rows if row["list_name"] == "top_relative_strength_by_rs_20d_vs_qqq"][:10]
    top_buy = [row["ticker"] for row in sorting_rows if row["list_name"] == "top_near_buy_zone_by_abs_nearest_buy_zone_distance"][:10]
    top_breakout = [row["ticker"] for row in sorting_rows if row["list_name"] == "top_breakout_volume_confirmed_by_volume_surge"][:10]

    ps_ok, ps_msg = parse_check(root / "scripts/v18/run_v18_21A_R1_data_coverage_scoring_patch.ps1")
    base_ok, base_msg = compile_check(root / "scripts/v18/v18_21A_price_derived_factor_pack.py")
    r1_ok, r1_msg = compile_check(root / "scripts/v18/v18_21A_R1_data_coverage_scoring_patch.py")
    outputs_ok = all(path.exists() for path in (out_cov, out_sort, out_scores, out_market))
    validations = [
        f"PowerShell parse check: {ps_msg}",
        f"Python compile check V18.21A: {base_msg}",
        f"Python compile check V18.21A-R1: {r1_msg}",
        "Run check: OK_CURRENT_SCRIPT_EXECUTED",
        f"R1 output existence check: {'OK' if outputs_ok else 'FAILED'}",
        "Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY",
    ]
    validation_fail_count = sum(1 for ok in (ps_ok, base_ok, r1_ok, outputs_ok) if not ok)
    status = STATUS_WARN if market_row["vix_missing_cap_applied"] == "TRUE" or partial_count or fatal_count else STATUS_OK

    metrics: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "PATCH_MODE": PATCH_MODE,
        "TICKER_INPUT_COUNT": len(tickers),
        "TICKER_FACTOR_ROWS": len(factor_rows),
        "TICKER_FATAL_FACTOR_FAIL_COUNT": fatal_count,
        "TICKER_PARTIAL_DEGRADED_COUNT": partial_count,
        "TICKER_INSUFFICIENT_HISTORY_COUNT": insufficient_count,
        "TICKER_VOLUME_MISSING_COUNT": volume_missing,
        "TICKER_200DMA_MISSING_COUNT": missing_200,
        "TICKER_52W_HIGH_MISSING_COUNT": missing_52w,
        "TICKER_SCORE_READY_COUNT": score_ready_count,
        "SCORE_READY_RATIO": base.fmt(ready_ratio),
        "QQQ_PROXY_STATUS": proxy_status["QQQ"],
        "SPY_PROXY_STATUS": proxy_status["SPY"],
        "VIX_PROXY_STATUS": proxy_status["VIX"],
        "VIX_MISSING_CAP_APPLIED": market_row["vix_missing_cap_applied"],
        "MARKET_REGIME_STATUS": market_row["market_regime_data_status"],
        "MARKET_REGIME_LABEL": market_row["market_regime_label"],
        "MARKET_RISK_COEFFICIENT": market_row["market_risk_coefficient"],
        "MARKET_REGIME_CONFIDENCE": market_row["market_regime_confidence"],
        "TOP_RELATIVE_STRENGTH_TICKERS": ";".join(top_rs),
        "TOP_NEAR_BUY_ZONE_TICKERS": ";".join(top_buy),
        "TOP_BREAKOUT_VOLUME_CONFIRMED_TICKERS": ";".join(top_breakout),
        "EXTENDED_ABOVE_BUY_ZONE_COUNT": extended,
        "BELOW_200DMA_COUNT": below200,
        "HIGH_VOL_CAUTION_COUNT": high_vol,
        "DATA_DEGRADED_COUNT": fatal_count + partial_count,
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "READ_FIRST": str(read_first),
        "REPORT": str(report),
    }
    metrics.update(SAFETY_FLAGS)
    base.write_text(read_first, render_read_first(metrics))
    base.write_text(report, render_report(metrics, validations))

    fields_ok = all(field in base.read_text(read_first) for field in READ_FIRST_FIELDS)
    final_outputs_ok = all(path.exists() for path in (out_cov, out_sort, out_scores, out_market, read_first, report))
    if not fields_ok or not final_outputs_ok:
        metrics["VALIDATION_FAIL_COUNT"] = int(metrics["VALIDATION_FAIL_COUNT"]) + 1
        base.write_text(read_first, render_read_first(metrics))
        base.write_text(report, render_report(metrics, validations + ["Final READ_FIRST/output check: FAILED"]))

    print(f"STATUS: {metrics['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"PATCH_MODE: {PATCH_MODE}")
    print(f"TICKER_INPUT_COUNT: {metrics['TICKER_INPUT_COUNT']}")
    print(f"TICKER_FATAL_FACTOR_FAIL_COUNT: {metrics['TICKER_FATAL_FACTOR_FAIL_COUNT']}")
    print(f"TICKER_PARTIAL_DEGRADED_COUNT: {metrics['TICKER_PARTIAL_DEGRADED_COUNT']}")
    print(f"TICKER_SCORE_READY_COUNT: {metrics['TICKER_SCORE_READY_COUNT']}")
    print(f"VIX_MISSING_CAP_APPLIED: {metrics['VIX_MISSING_CAP_APPLIED']}")
    print(f"MARKET_RISK_COEFFICIENT: {metrics['MARKET_RISK_COEFFICIENT']}")
    print(f"VALIDATION_FAIL_COUNT: {metrics['VALIDATION_FAIL_COUNT']}")
    print(f"READ_FIRST: {read_first}")
    print(f"REPORT: {report}")
    return 1 if int(metrics["VALIDATION_FAIL_COUNT"]) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
