#!/usr/bin/env python
"""V18.40A KDJ + MACD shadow layer.

Research-only oscillator diagnostics for the current V18 candidate universe.
This script reads current candidate aliases and local cached OHLCV files only.
It does not modify rankings, ledgers, trading/account state, or factor weights.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


MODE = "SHADOW_ONLY_RESEARCH_ONLY_KDJ_MACD_OSCILLATOR_LAYER"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FORBIDDEN_MODIFIED = "FALSE"

PRICE_CACHE = "state/v18/price_cache"
CURRENT_FULL_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
CURRENT_RANKED_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
TECHNICAL_FULL = "outputs/v18/technical_timing/V18_35D_FULL_UNIVERSE_TECHNICAL_TIMING.csv"
TECHNICAL_CURRENT = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"

OUT_SIGNALS = "outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv"
OUT_SUMMARY = "outputs/v18/ops/V18_40A_KDJ_MACD_SHADOW_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_40A_KDJ_MACD_SHADOW_REPORT.md"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_KDJ_MACD_SHADOW_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_40A_READ_FIRST.txt"

SIGNAL_COLUMNS = [
    "run_id",
    "asof_date",
    "ticker",
    "company_name_or_chinese_name_if_available",
    "candidate_rank",
    "composite_candidate_score",
    "factor_pack_score",
    "technical_timing_score",
    "kdj_k",
    "kdj_d",
    "kdj_j",
    "kdj_signal",
    "kdj_risk_label",
    "macd_dif",
    "macd_dea",
    "macd_histogram",
    "macd_signal",
    "macd_momentum_label",
    "combined_oscillator_label",
    "shadow_confirmation_score",
    "shadow_risk_score",
    "official_decision_impact",
]

SUMMARY_COLUMNS = [
    "run_id",
    "asof_date",
    "status",
    "mode",
    "candidate_count",
    "price_available_count",
    "price_missing_count",
    "kdj_calculable_count",
    "kdj_not_calculable_count",
    "macd_calculable_count",
    "macd_not_calculable_count",
    "kdj_golden_cross_count",
    "kdj_dead_cross_count",
    "macd_golden_cross_count",
    "macd_dead_cross_count",
    "kdj_overbought_count",
    "kdj_oversold_count",
    "kdj_j_extreme_high_count",
    "kdj_j_extreme_low_count",
    "positive_confirmation_count",
    "risk_warning_count",
    "official_decision_impact",
    "auto_trade",
    "auto_sell",
    "ranking_formula_modified",
    "factor_weights_modified",
    "freeze_ledger_modified",
    "broker_api_used",
    "order_execution_used",
    "forbidden_modified",
]


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as f:
                reader = csv.DictReader(f)
                return [dict(r) for r in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def norm(value: object) -> str:
    return str(value or "").strip().upper()


def clean(value: object) -> str:
    return str(value or "").strip()


def to_float(value: object) -> float | None:
    try:
        text = clean(value)
        if not text or text.upper() in {"NAN", "NONE", "NULL"}:
            return None
        number = float(text)
        if math.isnan(number) or math.isinf(number):
            return None
        return number
    except Exception:
        return None


def fmt(value: float | None, digits: int = 4) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def clamp(value: int, lo: int = -3, hi: int = 3) -> int:
    return max(lo, min(hi, value))


def index_by_ticker(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        ticker = norm(row.get("ticker") or row.get("yf_ticker"))
        if ticker and ticker not in out:
            out[ticker] = row
    return out


def select_candidate_input(root: Path) -> tuple[Path, list[dict[str, str]], list[str], str]:
    for rel in (CURRENT_FULL_CANDIDATES, CURRENT_RANKED_CANDIDATES):
        path = root / rel
        rows, fields = read_csv(path)
        if rows:
            return path, rows, fields, "OK"
    return root / CURRENT_FULL_CANDIDATES, [], [], "MISSING_CANDIDATE_INPUT"


def load_prices(path: Path) -> tuple[list[dict[str, float | str]], str]:
    rows, fields = read_csv(path)
    if not path.exists():
        return [], "PRICE_CACHE_FILE_MISSING"
    lower = {f.lower(): f for f in fields}
    required = {"date", "open", "high", "low", "close", "volume"}
    if not rows or not required.issubset(set(lower)):
        return [], "PRICE_CACHE_UNREADABLE_OR_SCHEMA_MISSING"

    out: list[dict[str, float | str]] = []
    for row in rows:
        date = clean(row.get(lower["date"]))[:10]
        close = to_float(row.get(lower["close"]))
        if not date or close is None:
            continue
        high = to_float(row.get(lower["high"])) or close
        low = to_float(row.get(lower["low"])) or close
        open_ = to_float(row.get(lower["open"])) or close
        volume = to_float(row.get(lower["volume"])) or 0.0
        out.append({"date": date, "open": open_, "high": high, "low": low, "close": close, "volume": volume})
    out.sort(key=lambda r: str(r["date"]))
    return out, "OK" if out else "NO_PARSEABLE_PRICE_ROWS"


def ema(values: list[float], period: int) -> list[float | None]:
    if not values:
        return []
    alpha = 2.0 / (period + 1.0)
    out: list[float | None] = []
    current: float | None = None
    for value in values:
        if current is None:
            current = value
        else:
            current = (value * alpha) + (current * (1.0 - alpha))
        out.append(current)
    return out


def calculate_kdj(prices: list[dict[str, float | str]], lookback: int = 9) -> dict[str, object]:
    if len(prices) < lookback + 1:
        return {"calculable": False, "reason": "INSUFFICIENT_KDJ_HISTORY"}

    k_values: list[float | None] = []
    d_values: list[float | None] = []
    k_prev = 50.0
    d_prev = 50.0

    for idx, row in enumerate(prices):
        if idx + 1 < lookback:
            k_values.append(None)
            d_values.append(None)
            continue
        window = prices[idx + 1 - lookback : idx + 1]
        highest_high = max(float(r["high"]) for r in window)
        lowest_low = min(float(r["low"]) for r in window)
        denom = highest_high - lowest_low
        if denom <= 0:
            k_values.append(None)
            d_values.append(None)
            continue
        close = float(row["close"])
        rsv = ((close - lowest_low) / denom) * 100.0
        k_current = (k_prev * (2.0 / 3.0)) + (rsv * (1.0 / 3.0))
        d_current = (d_prev * (2.0 / 3.0)) + (k_current * (1.0 / 3.0))
        k_prev = k_current
        d_prev = d_current
        k_values.append(k_current)
        d_values.append(d_current)

    valid = [(k, d) for k, d in zip(k_values, d_values) if k is not None and d is not None]
    if len(valid) < 2:
        return {"calculable": False, "reason": "INSUFFICIENT_VALID_KDJ_POINTS"}

    prev_k, prev_d = valid[-2]
    k, d = valid[-1]
    assert k is not None and d is not None and prev_k is not None and prev_d is not None
    j = (3.0 * k) - (2.0 * d)

    signals: list[str] = []
    if prev_k <= prev_d and k > d:
        signals.append("KDJ_GOLDEN_CROSS")
    if prev_k >= prev_d and k < d:
        signals.append("KDJ_DEAD_CROSS")
    if not signals:
        signals.append("KDJ_NEUTRAL")

    risks: list[str] = []
    if k >= 80.0 or d >= 80.0:
        risks.append("KDJ_OVERBOUGHT")
    if k <= 20.0 or d <= 20.0:
        risks.append("KDJ_OVERSOLD")
    if j >= 100.0:
        risks.append("KDJ_J_EXTREME_HIGH")
    if j <= 0.0:
        risks.append("KDJ_J_EXTREME_LOW")
    if not risks:
        risks.append("KDJ_NEUTRAL")

    return {
        "calculable": True,
        "k": k,
        "d": d,
        "j": j,
        "signal": ";".join(signals),
        "risk": ";".join(risks),
    }


def calculate_macd(prices: list[dict[str, float | str]], fast: int = 12, slow: int = 26, signal_period: int = 9) -> dict[str, object]:
    min_rows = slow + signal_period
    if len(prices) < min_rows:
        return {"calculable": False, "reason": "INSUFFICIENT_MACD_HISTORY"}
    closes = [float(r["close"]) for r in prices]
    fast_ema = ema(closes, fast)
    slow_ema = ema(closes, slow)
    dif_values = [
        (f - s) if f is not None and s is not None else None
        for f, s in zip(fast_ema, slow_ema)
    ]
    valid_dif = [float(v) for v in dif_values if v is not None]
    dea_values = ema(valid_dif, signal_period)
    if len(valid_dif) < signal_period + 1 or len(dea_values) < 2:
        return {"calculable": False, "reason": "INSUFFICIENT_VALID_MACD_POINTS"}

    dif = valid_dif[-1]
    dea = float(dea_values[-1])
    prev_dif = valid_dif[-2]
    prev_dea = float(dea_values[-2])
    hist = dif - dea
    prev_hist = prev_dif - prev_dea

    signals: list[str] = []
    if prev_dif <= prev_dea and dif > dea:
        signals.append("MACD_GOLDEN_CROSS")
    if prev_dif >= prev_dea and dif < dea:
        signals.append("MACD_DEAD_CROSS")
    if dif >= 0 and dea >= 0:
        signals.append("MACD_ABOVE_ZERO")
    elif dif < 0 and dea < 0:
        signals.append("MACD_BELOW_ZERO")
    if not signals:
        signals.append("MACD_NEUTRAL")

    momentum: list[str] = []
    if hist > prev_hist:
        momentum.append("MACD_HIST_EXPANDING")
        momentum.append("MACD_MOMENTUM_IMPROVING")
    elif hist < prev_hist:
        momentum.append("MACD_HIST_CONTRACTING")
        momentum.append("MACD_MOMENTUM_WEAKENING")
    else:
        momentum.append("MACD_NEUTRAL")

    return {
        "calculable": True,
        "dif": dif,
        "dea": dea,
        "hist": hist,
        "prev_hist": prev_hist,
        "signal": ";".join(signals),
        "momentum": ";".join(momentum),
    }


def name_from_row(row: dict[str, str]) -> str:
    for col in (
        "company_name",
        "chinese_name",
        "company_chinese_name",
        "name",
        "security_name",
        "company_name_or_chinese_name_if_available",
    ):
        value = clean(row.get(col))
        if value:
            return value
    return ""


def technical_score_for(ticker: str, candidate: dict[str, str], tech_indexes: list[dict[str, dict[str, str]]]) -> str:
    value = clean(candidate.get("technical_timing_score"))
    if value:
        return value
    for idx in tech_indexes:
        row = idx.get(ticker)
        if row:
            value = clean(row.get("technical_timing_score"))
            if value:
                return value
    return ""


def factor_score_for(candidate: dict[str, str]) -> str:
    for col in ("factor_pack_score", "factor_score", "raw105_factor_pack_score"):
        value = clean(candidate.get(col))
        if value:
            return value
    return ""


def combined_label(kdj: dict[str, object], macd: dict[str, object], confirmation_score: int, risk_score: int) -> str:
    if not kdj.get("calculable") and not macd.get("calculable"):
        return "OSCILLATOR_NOT_CALCULABLE"
    if confirmation_score >= 2 and risk_score == 0:
        return "OSCILLATOR_POSITIVE_CONFIRMATION"
    if risk_score >= 2 and confirmation_score <= 0:
        return "OSCILLATOR_RISK_WARNING"
    if confirmation_score > 0 and risk_score > 0:
        return "OSCILLATOR_MIXED"
    if confirmation_score > 0:
        return "OSCILLATOR_MILD_CONFIRMATION"
    if risk_score > 0:
        return "OSCILLATOR_MILD_RISK"
    return "OSCILLATOR_NEUTRAL"


def build_outputs(root: Path) -> tuple[str, dict[str, object]]:
    run_id = f"V18_40A_{stamp()}"
    asof_date = today()
    candidate_path, candidates, _, candidate_status = select_candidate_input(root)

    tech_full, _ = read_csv(root / TECHNICAL_FULL)
    tech_current, _ = read_csv(root / TECHNICAL_CURRENT)
    tech_indexes = [index_by_ticker(tech_full), index_by_ticker(tech_current)]

    signal_rows: list[dict[str, object]] = []
    counters: Counter[str] = Counter()

    for candidate in candidates:
        ticker = norm(candidate.get("ticker") or candidate.get("yf_ticker"))
        if not ticker:
            continue

        prices, price_status = load_prices(root / PRICE_CACHE / f"{ticker}.csv")
        if price_status == "OK":
            counters["price_available_count"] += 1
        else:
            counters["price_missing_count"] += 1

        kdj = calculate_kdj(prices)
        macd = calculate_macd(prices)
        if kdj.get("calculable"):
            counters["kdj_calculable_count"] += 1
        else:
            counters["kdj_not_calculable_count"] += 1
        if macd.get("calculable"):
            counters["macd_calculable_count"] += 1
        else:
            counters["macd_not_calculable_count"] += 1

        kdj_signal = clean(kdj.get("signal")) or "KDJ_NEUTRAL"
        kdj_risk = clean(kdj.get("risk")) or "KDJ_NEUTRAL"
        macd_signal = clean(macd.get("signal")) or "MACD_NEUTRAL"
        macd_momentum = clean(macd.get("momentum")) or "MACD_NEUTRAL"

        confirmation = 0
        risk = 0
        if "KDJ_GOLDEN_CROSS" in kdj_signal:
            confirmation += 1
            counters["kdj_golden_cross_count"] += 1
        if "KDJ_DEAD_CROSS" in kdj_signal:
            confirmation -= 1
            risk += 1
            counters["kdj_dead_cross_count"] += 1
        if "MACD_GOLDEN_CROSS" in macd_signal:
            confirmation += 1
            counters["macd_golden_cross_count"] += 1
        if "MACD_DEAD_CROSS" in macd_signal:
            confirmation -= 1
            risk += 1
            counters["macd_dead_cross_count"] += 1
        if "KDJ_OVERBOUGHT" in kdj_risk:
            counters["kdj_overbought_count"] += 1
            risk += 1
        if "KDJ_OVERSOLD" in kdj_risk:
            counters["kdj_oversold_count"] += 1
            confirmation += 1
        if "KDJ_J_EXTREME_HIGH" in kdj_risk:
            counters["kdj_j_extreme_high_count"] += 1
            risk += 1
        if "KDJ_J_EXTREME_LOW" in kdj_risk:
            counters["kdj_j_extreme_low_count"] += 1
            confirmation += 1
        if macd.get("calculable"):
            hist = float(macd.get("hist", 0.0))
            prev_hist = float(macd.get("prev_hist", 0.0))
            if hist > 0 and hist > prev_hist:
                confirmation += 1
            if hist < 0 and hist < prev_hist:
                confirmation -= 1
                risk += 1

        confirmation = clamp(confirmation)
        risk = clamp(risk, 0, 3)
        if confirmation > 0:
            counters["positive_confirmation_count"] += 1
        if risk > 0:
            counters["risk_warning_count"] += 1

        signal_rows.append(
            {
                "run_id": run_id,
                "asof_date": asof_date,
                "ticker": ticker,
                "company_name_or_chinese_name_if_available": name_from_row(candidate),
                "candidate_rank": clean(candidate.get("rank") or candidate.get("candidate_rank")),
                "composite_candidate_score": clean(candidate.get("composite_candidate_score")),
                "factor_pack_score": factor_score_for(candidate),
                "technical_timing_score": technical_score_for(ticker, candidate, tech_indexes),
                "kdj_k": fmt(kdj.get("k") if kdj.get("calculable") else None),
                "kdj_d": fmt(kdj.get("d") if kdj.get("calculable") else None),
                "kdj_j": fmt(kdj.get("j") if kdj.get("calculable") else None),
                "kdj_signal": kdj_signal,
                "kdj_risk_label": kdj_risk,
                "macd_dif": fmt(macd.get("dif") if macd.get("calculable") else None),
                "macd_dea": fmt(macd.get("dea") if macd.get("calculable") else None),
                "macd_histogram": fmt(macd.get("hist") if macd.get("calculable") else None),
                "macd_signal": macd_signal,
                "macd_momentum_label": macd_momentum,
                "combined_oscillator_label": combined_label(kdj, macd, confirmation, risk),
                "shadow_confirmation_score": confirmation,
                "shadow_risk_score": risk,
                "official_decision_impact": OFFICIAL_DECISION_IMPACT,
            }
        )

    status = "OK_V18_40A_KDJ_MACD_SHADOW_LAYER_READY" if candidates else f"FAIL_V18_40A_{candidate_status}"
    summary = {
        "run_id": run_id,
        "asof_date": asof_date,
        "status": status,
        "mode": MODE,
        "candidate_count": len(candidates),
        "price_available_count": counters["price_available_count"],
        "price_missing_count": counters["price_missing_count"],
        "kdj_calculable_count": counters["kdj_calculable_count"],
        "kdj_not_calculable_count": counters["kdj_not_calculable_count"],
        "macd_calculable_count": counters["macd_calculable_count"],
        "macd_not_calculable_count": counters["macd_not_calculable_count"],
        "kdj_golden_cross_count": counters["kdj_golden_cross_count"],
        "kdj_dead_cross_count": counters["kdj_dead_cross_count"],
        "macd_golden_cross_count": counters["macd_golden_cross_count"],
        "macd_dead_cross_count": counters["macd_dead_cross_count"],
        "kdj_overbought_count": counters["kdj_overbought_count"],
        "kdj_oversold_count": counters["kdj_oversold_count"],
        "kdj_j_extreme_high_count": counters["kdj_j_extreme_high_count"],
        "kdj_j_extreme_low_count": counters["kdj_j_extreme_low_count"],
        "positive_confirmation_count": counters["positive_confirmation_count"],
        "risk_warning_count": counters["risk_warning_count"],
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "ranking_formula_modified": "FALSE",
        "factor_weights_modified": "FALSE",
        "freeze_ledger_modified": "FALSE",
        "broker_api_used": "FALSE",
        "order_execution_used": "FALSE",
        "forbidden_modified": FORBIDDEN_MODIFIED,
        "candidate_input_path": candidate_path.as_posix(),
    }

    write_csv(root / OUT_SIGNALS, signal_rows, SIGNAL_COLUMNS)
    write_csv(root / OUT_SUMMARY, [summary], SUMMARY_COLUMNS)
    report = render_report(summary, signal_rows)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_CURRENT_REPORT, report)
    write_text(root / OUT_READ_FIRST, render_read_first(summary))

    return status, summary


def table(rows: list[dict[str, object]], columns: list[str]) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(col)) for col in columns) + " |")
    return lines


def render_report(summary: dict[str, object], signal_rows: list[dict[str, object]]) -> str:
    top20 = sorted(signal_rows, key=lambda r: float(clean(r.get("candidate_rank")) or "999999"))[:20]
    positive = sorted(
        [r for r in signal_rows if int(r.get("shadow_confirmation_score") or 0) > 0],
        key=lambda r: (int(r.get("shadow_confirmation_score") or 0), -int(float(clean(r.get("candidate_rank")) or "999999"))),
        reverse=True,
    )[:20]
    risks = sorted(
        [r for r in signal_rows if int(r.get("shadow_risk_score") or 0) > 0],
        key=lambda r: (int(r.get("shadow_risk_score") or 0), -int(float(clean(r.get("candidate_rank")) or "999999"))),
        reverse=True,
    )[:20]

    cols = [
        "candidate_rank",
        "ticker",
        "kdj_signal",
        "kdj_risk_label",
        "macd_signal",
        "macd_momentum_label",
        "shadow_confirmation_score",
        "shadow_risk_score",
        "combined_oscillator_label",
    ]
    lines = [
        "# V18.40A KDJ + MACD Shadow Report",
        "",
        "## Status",
        f"- STATUS: {summary.get('status')}",
        f"- MODE: {summary.get('mode')}",
        f"- RUN_ID: {summary.get('run_id')}",
        f"- ASOF_DATE: {summary.get('asof_date')}",
        "",
        "## Counts",
        f"- Candidate count: {summary.get('candidate_count')}",
        f"- Price available / missing count: {summary.get('price_available_count')} / {summary.get('price_missing_count')}",
        f"- KDJ calculable / not calculable count: {summary.get('kdj_calculable_count')} / {summary.get('kdj_not_calculable_count')}",
        f"- MACD calculable / not calculable count: {summary.get('macd_calculable_count')} / {summary.get('macd_not_calculable_count')}",
        f"- KDJ golden / dead cross count: {summary.get('kdj_golden_cross_count')} / {summary.get('kdj_dead_cross_count')}",
        f"- MACD golden / dead cross count: {summary.get('macd_golden_cross_count')} / {summary.get('macd_dead_cross_count')}",
        f"- KDJ overbought / oversold count: {summary.get('kdj_overbought_count')} / {summary.get('kdj_oversold_count')}",
        f"- KDJ J extreme high / low count: {summary.get('kdj_j_extreme_high_count')} / {summary.get('kdj_j_extreme_low_count')}",
        "",
        "## Top 20 Candidate Oscillator Summary",
        *table(top20, cols),
        "",
        "## Top Positive Oscillator Confirmations",
        *table(positive, cols),
        "",
        "## Top Risk Oscillator Warnings",
        *table(risks, cols),
        "",
        "## Safety",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- RANKING_FORMULA_MODIFIED: FALSE",
        "- FACTOR_WEIGHTS_MODIFIED: FALSE",
        "- FREEZE_LEDGER_MODIFIED: FALSE",
        "- BROKER_API_USED: FALSE",
        "- ORDER_EXECUTION_USED: FALSE",
        "",
        "## Interpretation",
        "- `shadow_confirmation_score` and `shadow_risk_score` are research-only diagnostic fields.",
        "- This layer does not feed official ranking, candidate selection, freeze ledger, or trading/account logic.",
    ]
    return "\n".join(lines) + "\n"


def render_read_first(summary: dict[str, object]) -> str:
    lines = [
        f"STATUS: {summary.get('status')}",
        f"MODE: {summary.get('mode')}",
        f"RUN_ID: {summary.get('run_id')}",
        f"CANDIDATE_COUNT: {summary.get('candidate_count')}",
        f"PRICE_AVAILABLE_COUNT: {summary.get('price_available_count')}",
        f"PRICE_MISSING_COUNT: {summary.get('price_missing_count')}",
        f"KDJ_CALCULABLE_COUNT: {summary.get('kdj_calculable_count')}",
        f"MACD_CALCULABLE_COUNT: {summary.get('macd_calculable_count')}",
        "OFFICIAL_DECISION_IMPACT: NONE",
        "AUTO_TRADE: DISABLED",
        "AUTO_SELL: DISABLED",
        "RANKING_FORMULA_MODIFIED: FALSE",
        "FACTOR_WEIGHTS_MODIFIED: FALSE",
        "FREEZE_LEDGER_MODIFIED: FALSE",
        "BROKER_API_USED: FALSE",
        "ORDER_EXECUTION_USED: FALSE",
        "FORBIDDEN_MODIFIED: FALSE",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="V18.40A KDJ + MACD shadow layer")
    parser.add_argument("--root", default="D:/us-tech-quant")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    status, _ = build_outputs(root)
    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
