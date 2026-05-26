from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import math
import re
from pathlib import Path
from statistics import stdev
from typing import Dict, Iterable, List, Optional, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")

OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_WEIGHT_CHANGE = "DISABLED"
AUTO_PROMOTION = "DISABLED"
AUTO_TRADE = "DISABLED"

FACTORS = [
    {
        "factor_name": "month_end_rebalance_factor",
        "factor_group": "calendar",
        "factor_type": "shadow_calendar_attention",
        "data_required": "trading calendar / candidate snapshot price_date",
        "implementation_status": "IMPLEMENTED_SHADOW_ONLY",
        "shadow_only": "True",
        "formula_note": "1.0 during final 3 trading days of month, else 0.0 neutral.",
    },
    {
        "factor_name": "quarter_end_rebalance_factor",
        "factor_group": "calendar",
        "factor_type": "shadow_calendar_attention",
        "data_required": "trading calendar / candidate snapshot price_date",
        "implementation_status": "IMPLEMENTED_SHADOW_ONLY",
        "shadow_only": "True",
        "formula_note": "1.0 during final 5 trading days of quarter, else 0.0 neutral.",
    },
    {
        "factor_name": "options_expiry_pressure_factor",
        "factor_group": "calendar_opex",
        "factor_type": "shadow_calendar_proxy",
        "data_required": "calendar only; no options chain used",
        "implementation_status": "IMPLEMENTED_CALENDAR_PROXY_ONLY",
        "shadow_only": "True",
        "formula_note": "Calendar-only OPEX week / monthly OPEX Friday proxy. Does not infer true options flow.",
    },
    {
        "factor_name": "opex_relief_factor",
        "factor_group": "calendar_opex",
        "factor_type": "shadow_calendar_proxy",
        "data_required": "calendar only; no options chain used",
        "implementation_status": "IMPLEMENTED_CALENDAR_PROXY_ONLY",
        "shadow_only": "True",
        "formula_note": "Calendar-only 1-3 trading day post-monthly-OPEX relief window proxy.",
    },
    {
        "factor_name": "realized_volatility_factor",
        "factor_group": "realized_volatility",
        "factor_type": "shadow_risk_context",
        "data_required": "daily close history",
        "implementation_status": "IMPLEMENTED_WHEN_PRICE_HISTORY_AVAILABLE",
        "shadow_only": "True",
        "formula_note": "Annualized stdev of daily close returns over 10D and 20D windows.",
    },
    {
        "factor_name": "vwap_position_factor",
        "factor_group": "vwap_proxy",
        "factor_type": "shadow_execution_context_proxy",
        "data_required": "daily OHLCV history; intraday VWAP not used",
        "implementation_status": "PROXY_ONLY_DAILY_OHLCV_WHEN_HISTORY_AVAILABLE",
        "shadow_only": "True",
        "formula_note": "Close above/below rolling daily OHLCV VWAP proxy. Not true intraday VWAP.",
    },
    {
        "factor_name": "vwap_deviation_factor",
        "factor_group": "vwap_proxy",
        "factor_type": "shadow_execution_context_proxy",
        "data_required": "daily OHLCV history; intraday VWAP not used",
        "implementation_status": "PROXY_ONLY_DAILY_OHLCV_WHEN_HISTORY_AVAILABLE",
        "shadow_only": "True",
        "formula_note": "(close - rolling daily OHLCV VWAP proxy) / proxy. Not true intraday VWAP.",
    },
    {
        "factor_name": "vwap_reclaim_support_factor",
        "factor_group": "vwap_proxy",
        "factor_type": "shadow_execution_context_proxy",
        "data_required": "daily OHLCV history; intraday VWAP not used",
        "implementation_status": "PROXY_ONLY_DAILY_OHLCV_WHEN_HISTORY_AVAILABLE",
        "shadow_only": "True",
        "formula_note": "Proxy reclaim if close finishes above proxy after prior close below or daily low touched proxy.",
    },
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: List[Dict[str, str]], fields: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fmt_num(value: Optional[float], digits: int = 6) -> str:
    if value is None or not math.isfinite(value):
        return ""
    return f"{value:.{digits}f}"


def parse_date(value: str) -> Optional[dt.date]:
    s = str(value or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(s[:10], fmt).date()
        except ValueError:
            pass
    return None


def embedded_price_date(row: Dict[str, str]) -> Tuple[Optional[dt.date], str]:
    text = row.get("source_row_text", "")
    m = re.search(r"(?:^|\|)\s*price_date=([0-9]{4}-[0-9]{2}-[0-9]{2})", text)
    if m:
        d = parse_date(m.group(1))
        if d:
            return d, "source_row_text.price_date"
    d = parse_date(row.get("snapshot_date", ""))
    if d:
        return d, "snapshot_date"
    return None, "DATA_UNAVAILABLE"


def weekdays_between(start: dt.date, end: dt.date) -> List[dt.date]:
    step = 1 if end >= start else -1
    out: List[dt.date] = []
    cur = start
    while True:
        if cur.weekday() < 5:
            out.append(cur)
        if cur == end:
            break
        cur += dt.timedelta(days=step)
    return out


def last_weekday_of_month(day: dt.date) -> dt.date:
    last_day = calendar.monthrange(day.year, day.month)[1]
    cur = dt.date(day.year, day.month, last_day)
    while cur.weekday() >= 5:
        cur -= dt.timedelta(days=1)
    return cur


def last_weekday_of_quarter(day: dt.date) -> dt.date:
    q_end_month = ((day.month - 1) // 3 + 1) * 3
    last_day = calendar.monthrange(day.year, q_end_month)[1]
    cur = dt.date(day.year, q_end_month, last_day)
    while cur.weekday() >= 5:
        cur -= dt.timedelta(days=1)
    return cur


def trading_days_to_end(day: dt.date, end: dt.date) -> Optional[int]:
    if day > end:
        return None
    days = weekdays_between(day, end)
    return max(len(days) - 1, 0)


def third_friday(year: int, month: int) -> dt.date:
    cur = dt.date(year, month, 1)
    fridays = []
    while cur.month == month:
        if cur.weekday() == 4:
            fridays.append(cur)
        cur += dt.timedelta(days=1)
    return fridays[2]


def opex_week_bounds(opex: dt.date) -> Tuple[dt.date, dt.date]:
    return opex - dt.timedelta(days=4), opex


def previous_month(year: int, month: int) -> Tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def trading_days_after(start: dt.date, count: int) -> List[dt.date]:
    out: List[dt.date] = []
    cur = start + dt.timedelta(days=1)
    while len(out) < count:
        if cur.weekday() < 5:
            out.append(cur)
        cur += dt.timedelta(days=1)
    return out


def calendar_values(base_date: Optional[dt.date]) -> Dict[str, str]:
    if base_date is None:
        return {
            "calendar_status": "DATA_UNAVAILABLE",
            "calendar_method": "DATA_UNAVAILABLE",
            "days_to_month_end": "DATA_UNAVAILABLE",
            "month_end_window_status": "DATA_UNAVAILABLE",
            "month_end_rebalance_factor": "DATA_UNAVAILABLE",
            "days_to_quarter_end": "DATA_UNAVAILABLE",
            "quarter_end_window_status": "DATA_UNAVAILABLE",
            "quarter_end_rebalance_factor": "DATA_UNAVAILABLE",
            "opex_date": "DATA_UNAVAILABLE",
            "options_expiry_pressure_status": "DATA_UNAVAILABLE",
            "options_expiry_pressure_factor": "DATA_UNAVAILABLE",
            "opex_relief_status": "DATA_UNAVAILABLE",
            "opex_relief_factor": "DATA_UNAVAILABLE",
        }

    month_end = last_weekday_of_month(base_date)
    q_end = last_weekday_of_quarter(base_date)
    dme = trading_days_to_end(base_date, month_end)
    dqe = trading_days_to_end(base_date, q_end)

    month_in = dme is not None and dme <= 2
    quarter_in = dqe is not None and dqe <= 4

    opex = third_friday(base_date.year, base_date.month)
    week_start, week_end = opex_week_bounds(opex)
    in_opex_week = week_start <= base_date <= week_end and base_date.weekday() < 5
    on_opex = base_date == opex

    py, pm = previous_month(base_date.year, base_date.month)
    prior_opex = third_friday(py, pm)
    relief_days = trading_days_after(prior_opex, 3)
    current_relief_days = trading_days_after(opex, 3)
    relief_set = set(relief_days + current_relief_days)
    in_relief = base_date in relief_set

    return {
        "calendar_status": "COMPUTABLE_NOW",
        "calendar_method": "WEEKDAY_TRADING_DAY_APPROX",
        "days_to_month_end": str(dme) if dme is not None else "OUT_OF_MONTH",
        "month_end_window_status": "IN_FINAL_3_TRADING_DAYS" if month_in else "OUT_OF_WINDOW",
        "month_end_rebalance_factor": "1.0" if month_in else "0.0",
        "days_to_quarter_end": str(dqe) if dqe is not None else "OUT_OF_QUARTER",
        "quarter_end_window_status": "IN_FINAL_5_TRADING_DAYS" if quarter_in else "OUT_OF_WINDOW",
        "quarter_end_rebalance_factor": "1.0" if quarter_in else "0.0",
        "opex_date": opex.isoformat(),
        "options_expiry_pressure_status": "MONTHLY_OPEX_FRIDAY" if on_opex else ("MONTHLY_OPEX_WEEK" if in_opex_week else "OUT_OF_WINDOW"),
        "options_expiry_pressure_factor": "1.0" if on_opex else ("0.5" if in_opex_week else "0.0"),
        "opex_relief_status": "POST_OPEX_RELIEF_WINDOW_1_TO_3_TRADING_DAYS" if in_relief else "OUT_OF_WINDOW",
        "opex_relief_factor": "1.0" if in_relief else "0.0",
    }


def unique_tickers(rows: Iterable[Dict[str, str]]) -> List[str]:
    seen = set()
    out = []
    for r in rows:
        t = str(r.get("ticker", "") or "").strip().upper()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def load_yfinance_history(tickers: List[str], use_yfinance: bool) -> Tuple[Dict[str, List[Dict[str, float]]], str]:
    if not use_yfinance:
        return {}, "YFINANCE_NOT_USED"
    try:
        import yfinance as yf  # type: ignore
    except Exception as exc:
        return {}, f"YFINANCE_IMPORT_FAILED: {type(exc).__name__}: {exc}"
    if not tickers:
        return {}, "NO_TICKERS"
    try:
        data = yf.download(
            tickers=tickers,
            period="90d",
            interval="1d",
            auto_adjust=False,
            progress=False,
            group_by="ticker",
            threads=True,
        )
    except Exception as exc:
        return {}, f"YFINANCE_DOWNLOAD_FAILED: {type(exc).__name__}: {exc}"

    out: Dict[str, List[Dict[str, float]]] = {}
    try:
        if len(tickers) == 1:
            t = tickers[0]
            out[t] = frame_to_history(data)
        else:
            for t in tickers:
                if t in data.columns.get_level_values(0):
                    out[t] = frame_to_history(data[t])
    except Exception as exc:
        return out, f"YFINANCE_PARSE_PARTIAL: {type(exc).__name__}: {exc}"
    return out, "YFINANCE_OK"


def frame_to_history(frame) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    for idx, r in frame.dropna(how="all").iterrows():
        vals = {}
        ok = True
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            try:
                v = float(r[col])
                if not math.isfinite(v):
                    ok = False
                vals[col.lower()] = v
            except Exception:
                ok = False
        if ok:
            vals["date_ord"] = idx.date().toordinal() if hasattr(idx, "date") else 0
            rows.append(vals)
    rows.sort(key=lambda x: x.get("date_ord", 0))
    return rows


def realized_vol(history: List[Dict[str, float]], window: int) -> Optional[float]:
    closes = [r["close"] for r in history if r.get("close") and r["close"] > 0]
    if len(closes) < window + 1:
        return None
    returns = []
    for prev, cur in zip(closes[-window - 1 : -1], closes[-window:]):
        if prev > 0:
            returns.append(cur / prev - 1.0)
    if len(returns) < window:
        return None
    return stdev(returns) * math.sqrt(252)


def vwap_proxy(history: List[Dict[str, float]], window: int = 20) -> Dict[str, Optional[float] | str]:
    if len(history) < window:
        return {"status": "PROXY_DATA_UNAVAILABLE"}
    recent = history[-window:]
    pv = 0.0
    vol = 0.0
    for r in recent:
        h, l, c, v = r["high"], r["low"], r["close"], r["volume"]
        if v <= 0:
            return {"status": "PROXY_DATA_UNAVAILABLE"}
        typical = (h + l + c) / 3.0
        pv += typical * v
        vol += v
    if vol <= 0:
        return {"status": "PROXY_DATA_UNAVAILABLE"}
    proxy = pv / vol
    last = history[-1]
    prev = history[-2] if len(history) >= window + 1 else None
    close = last["close"]
    low = last["low"]
    deviation = close / proxy - 1.0 if proxy else None
    position = 1.0 if close >= proxy else 0.0
    reclaim = 0.0
    if close >= proxy and low <= proxy:
        reclaim = 1.0
    if prev is not None and prev["close"] < proxy <= close:
        reclaim = 1.0
    return {
        "status": "PROXY_ONLY_DAILY_OHLCV",
        "proxy": proxy,
        "position": position,
        "deviation": deviation,
        "reclaim": reclaim,
    }


def extension_rows() -> List[Dict[str, str]]:
    rows = []
    for f in FACTORS:
        row = dict(f)
        row.update(
            {
                "official_decision_impact": OFFICIAL_DECISION_IMPACT,
                "auto_weight_change": AUTO_WEIGHT_CHANGE,
                "auto_promotion": AUTO_PROMOTION,
                "auto_trade": AUTO_TRADE,
            }
        )
        rows.append(row)
    return rows


def coverage_rows(use_yfinance: bool, history: Dict[str, List[Dict[str, float]]], candidate_count: int) -> List[Dict[str, str]]:
    any_history = any(len(v) >= 21 for v in history.values())
    rows = []
    for f in FACTORS:
        name = f["factor_name"]
        if name in {"month_end_rebalance_factor", "quarter_end_rebalance_factor"}:
            cls = "COMPUTABLE_NOW"
            status = "CALENDAR_AVAILABLE"
            note = "Computed from candidate base date using weekday trading-day approximation."
        elif name in {"options_expiry_pressure_factor", "opex_relief_factor"}:
            cls = "PROXY_ONLY"
            status = "CALENDAR_PROXY_ONLY"
            note = "Calendar-only OPEX proxy; no options chain, open interest, or flow data used."
        elif name == "realized_volatility_factor":
            cls = "COMPUTABLE_NOW" if any_history else "DATA_UNAVAILABLE"
            status = "DAILY_CLOSE_HISTORY_AVAILABLE" if any_history else "DATA_UNAVAILABLE"
            note = "Uses yfinance daily close history only when -UseYFinance is supplied." if use_yfinance else "No local daily close history source with sufficient lookback was found in this shadow run."
        else:
            cls = "PROXY_ONLY" if any_history else "DATA_UNAVAILABLE"
            status = "PROXY_ONLY_DAILY_OHLCV" if any_history else "PROXY_DATA_UNAVAILABLE"
            note = "Daily OHLCV proxy only; not true intraday VWAP." if any_history else "No local daily OHLCV history source with sufficient lookback was found in this shadow run."
        rows.append(
            {
                "factor_name": name,
                "coverage_class": cls,
                "factor_data_status": status,
                "candidate_count": str(candidate_count),
                "use_yfinance": str(use_yfinance),
                "official_decision_impact": OFFICIAL_DECISION_IMPACT,
                "auto_weight_change": AUTO_WEIGHT_CHANGE,
                "auto_promotion": AUTO_PROMOTION,
                "auto_trade": AUTO_TRADE,
                "note": note,
            }
        )
    return rows


def factor_value_rows(candidates: List[Dict[str, str]], history: Dict[str, List[Dict[str, float]]], yf_status: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for src in candidates:
        ticker = str(src.get("ticker", "") or "").strip().upper()
        base, base_source = embedded_price_date(src)
        cal = calendar_values(base)
        hist = history.get(ticker, [])
        rv10 = realized_vol(hist, 10)
        rv20 = realized_vol(hist, 20)
        rv_status = "COMPUTABLE_NOW" if rv10 is not None or rv20 is not None else "DATA_UNAVAILABLE"
        proxy = vwap_proxy(hist)
        proxy_status = str(proxy.get("status", "PROXY_DATA_UNAVAILABLE"))

        row = {
            "snapshot_date": src.get("snapshot_date", ""),
            "ticker": ticker,
            "base_date": base.isoformat() if base else "DATA_UNAVAILABLE",
            "base_date_source": base_source,
            "official_decision_impact": OFFICIAL_DECISION_IMPACT,
            "auto_weight_change": AUTO_WEIGHT_CHANGE,
            "auto_promotion": AUTO_PROMOTION,
            "auto_trade": AUTO_TRADE,
            "yf_history_status": yf_status,
            **cal,
            "options_expiry_pressure_method": "CALENDAR_PROXY_ONLY" if cal["calendar_status"] != "DATA_UNAVAILABLE" else "DATA_UNAVAILABLE",
            "opex_relief_method": "CALENDAR_PROXY_ONLY" if cal["calendar_status"] != "DATA_UNAVAILABLE" else "DATA_UNAVAILABLE",
            "realized_volatility_status": rv_status,
            "realized_volatility_factor": fmt_num(rv20) if rv20 is not None else "DATA_UNAVAILABLE",
            "realized_volatility_10d": fmt_num(rv10) if rv10 is not None else "DATA_UNAVAILABLE",
            "realized_volatility_20d": fmt_num(rv20) if rv20 is not None else "DATA_UNAVAILABLE",
            "vwap_proxy_status": proxy_status,
            "vwap_position_factor": fmt_num(proxy.get("position")) if proxy_status == "PROXY_ONLY_DAILY_OHLCV" else "PROXY_DATA_UNAVAILABLE",
            "vwap_deviation_factor": fmt_num(proxy.get("deviation")) if proxy_status == "PROXY_ONLY_DAILY_OHLCV" else "PROXY_DATA_UNAVAILABLE",
            "vwap_reclaim_support_factor": fmt_num(proxy.get("reclaim")) if proxy_status == "PROXY_ONLY_DAILY_OHLCV" else "PROXY_DATA_UNAVAILABLE",
            "vwap_proxy_value": fmt_num(proxy.get("proxy")) if proxy_status == "PROXY_ONLY_DAILY_OHLCV" else "PROXY_DATA_UNAVAILABLE",
            "vwap_method": "PROXY_ONLY_DAILY_OHLCV" if proxy_status == "PROXY_ONLY_DAILY_OHLCV" else "PROXY_DATA_UNAVAILABLE",
        }
        rows.append(row)
    return rows


def write_reports(root: Path, ext: List[Dict[str, str]], cov: List[Dict[str, str]], vals: List[Dict[str, str]], yf_status: str) -> None:
    reg_dir = root / "outputs/v18/factor_registry"
    research_dir = root / "outputs/v18/factor_research"
    ensure_dir(reg_dir)
    ensure_dir(research_dir)

    ext_csv = reg_dir / "V18_11A_CURRENT_FACTOR_REGISTRY_EXTENSION.csv"
    ext_report = reg_dir / "V18_11A_CURRENT_FACTOR_REGISTRY_EXTENSION_REPORT.md"
    ext_read = reg_dir / "V18_11A_READ_FIRST.txt"
    cov_csv = reg_dir / "V18_11B_CURRENT_FACTOR_COVERAGE_AUDIT.csv"
    cov_report = reg_dir / "V18_11B_CURRENT_FACTOR_COVERAGE_AUDIT_REPORT.md"
    cov_read = reg_dir / "V18_11B_READ_FIRST.txt"
    val_csv = research_dir / "V18_11C_CURRENT_CALENDAR_VWAP_RV_SHADOW_FACTORS.csv"
    val_report = research_dir / "V18_11C_CURRENT_CALENDAR_VWAP_RV_SHADOW_FACTOR_REPORT.md"
    val_read = research_dir / "V18_11C_READ_FIRST.txt"

    ext_fields = [
        "factor_name",
        "factor_group",
        "factor_type",
        "data_required",
        "implementation_status",
        "shadow_only",
        "official_decision_impact",
        "auto_weight_change",
        "auto_promotion",
        "auto_trade",
        "formula_note",
    ]
    cov_fields = [
        "factor_name",
        "coverage_class",
        "factor_data_status",
        "candidate_count",
        "use_yfinance",
        "official_decision_impact",
        "auto_weight_change",
        "auto_promotion",
        "auto_trade",
        "note",
    ]
    val_fields = [
        "snapshot_date",
        "ticker",
        "base_date",
        "base_date_source",
        "official_decision_impact",
        "auto_weight_change",
        "auto_promotion",
        "auto_trade",
        "yf_history_status",
        "calendar_status",
        "calendar_method",
        "days_to_month_end",
        "month_end_window_status",
        "month_end_rebalance_factor",
        "days_to_quarter_end",
        "quarter_end_window_status",
        "quarter_end_rebalance_factor",
        "opex_date",
        "options_expiry_pressure_status",
        "options_expiry_pressure_method",
        "options_expiry_pressure_factor",
        "opex_relief_status",
        "opex_relief_method",
        "opex_relief_factor",
        "realized_volatility_status",
        "realized_volatility_factor",
        "realized_volatility_10d",
        "realized_volatility_20d",
        "vwap_proxy_status",
        "vwap_method",
        "vwap_proxy_value",
        "vwap_position_factor",
        "vwap_deviation_factor",
        "vwap_reclaim_support_factor",
    ]

    write_csv(ext_csv, ext, ext_fields)
    write_csv(cov_csv, cov, cov_fields)
    write_csv(val_csv, vals, val_fields)

    computable = sum(1 for r in cov if r["coverage_class"] == "COMPUTABLE_NOW")
    proxy = sum(1 for r in cov if r["coverage_class"] == "PROXY_ONLY")
    unavailable = sum(1 for r in cov if r["coverage_class"] == "DATA_UNAVAILABLE")
    candidate_count = len(vals)

    ext_report.write_text(
        "\n".join(
            [
                "# V18.11A Factor Registry Extension",
                "",
                f"- FACTOR_COUNT: `{len(ext)}`",
                "- MODE: `SHADOW_ONLY_EXTENSION`",
                f"- OFFICIAL_DECISION_IMPACT: `{OFFICIAL_DECISION_IMPACT}`",
                f"- AUTO_WEIGHT_CHANGE: `{AUTO_WEIGHT_CHANGE}`",
                f"- AUTO_PROMOTION: `{AUTO_PROMOTION}`",
                f"- AUTO_TRADE: `{AUTO_TRADE}`",
                "- STATE_REGISTRY_MODIFIED: `False`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    cov_report.write_text(
        "\n".join(
            [
                "# V18.11B Factor Coverage Audit",
                "",
                f"- FACTOR_COUNT: `{len(cov)}`",
                f"- COMPUTABLE_COUNT: `{computable}`",
                f"- PROXY_ONLY_COUNT: `{proxy}`",
                f"- DATA_UNAVAILABLE_COUNT: `{unavailable}`",
                f"- YFINANCE_STATUS: `{yf_status}`",
                f"- OFFICIAL_DECISION_IMPACT: `{OFFICIAL_DECISION_IMPACT}`",
                f"- AUTO_WEIGHT_CHANGE: `{AUTO_WEIGHT_CHANGE}`",
                f"- AUTO_PROMOTION: `{AUTO_PROMOTION}`",
                f"- AUTO_TRADE: `{AUTO_TRADE}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    val_report.write_text(
        "\n".join(
            [
                "# V18.11C Calendar / VWAP Proxy / Realized Volatility Shadow Factors",
                "",
                f"- CANDIDATE_ROW_COUNT: `{candidate_count}`",
                f"- YFINANCE_STATUS: `{yf_status}`",
                "- OUTPUT_MODE: `SEPARATE_CSV_ONLY`",
                "- CANDIDATE_TRACKER_STATE_MODIFIED: `False`",
                "- VWAP_METHOD: `PROXY_ONLY_DAILY_OHLCV when daily OHLCV history is available; otherwise PROXY_DATA_UNAVAILABLE`",
                "- OPEX_METHOD: `CALENDAR_PROXY_ONLY`",
                f"- OFFICIAL_DECISION_IMPACT: `{OFFICIAL_DECISION_IMPACT}`",
                f"- AUTO_WEIGHT_CHANGE: `{AUTO_WEIGHT_CHANGE}`",
                f"- AUTO_PROMOTION: `{AUTO_PROMOTION}`",
                f"- AUTO_TRADE: `{AUTO_TRADE}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    for path, title, status in [
        (ext_read, "V18.11A FACTOR REGISTRY EXTENSION READ FIRST", "OK_V18_11A_SHADOW_REGISTRY_EXTENSION_READY"),
        (cov_read, "V18.11B FACTOR COVERAGE AUDIT READ FIRST", "OK_V18_11B_SHADOW_COVERAGE_AUDIT_READY"),
        (val_read, "V18.11C SHADOW FACTOR VALUES READ FIRST", "OK_V18_11C_SHADOW_FACTOR_VALUES_READY"),
    ]:
        path.write_text(
            f"""{title}

STATUS:
{status}

MODE:
SHADOW_ONLY

FACTOR_COUNT:
{len(ext)}

COMPUTABLE_COUNT:
{computable}

PROXY_ONLY_COUNT:
{proxy}

DATA_UNAVAILABLE_COUNT:
{unavailable}

CANDIDATE_ROW_COUNT:
{candidate_count}

YFINANCE_STATUS:
{yf_status}

OFFICIAL_DECISION_IMPACT:
{OFFICIAL_DECISION_IMPACT}

AUTO_WEIGHT_CHANGE:
{AUTO_WEIGHT_CHANGE}

AUTO_PROMOTION:
{AUTO_PROMOTION}

AUTO_TRADE:
{AUTO_TRADE}

STATE_REGISTRY_MODIFIED:
False

CANDIDATE_TRACKER_STATE_MODIFIED:
False
""",
            encoding="utf-8",
        )

    print("STATUS: OK_V18_11_SHADOW_FACTORS_READY")
    print(f"FACTOR_COUNT: {len(ext)}")
    print(f"COMPUTABLE_COUNT: {computable}")
    print(f"PROXY_ONLY_COUNT: {proxy}")
    print(f"DATA_UNAVAILABLE_COUNT: {unavailable}")
    print(f"CANDIDATE_ROW_COUNT: {candidate_count}")
    print(f"YFINANCE_STATUS: {yf_status}")
    print(f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}")
    print(f"AUTO_WEIGHT_CHANGE: {AUTO_WEIGHT_CHANGE}")
    print(f"AUTO_PROMOTION: {AUTO_PROMOTION}")
    print(f"AUTO_TRADE: {AUTO_TRADE}")
    print(f"V18_11A_EXTENSION: {ext_csv}")
    print(f"V18_11B_COVERAGE: {cov_csv}")
    print(f"V18_11C_VALUES: {val_csv}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT_DEFAULT))
    ap.add_argument("--use-yfinance", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    candidate_path = root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv"
    candidates, _ = read_csv(candidate_path)
    tickers = unique_tickers(candidates)
    history, yf_status = load_yfinance_history(tickers, args.use_yfinance)

    ext = extension_rows()
    cov = coverage_rows(args.use_yfinance, history, len(candidates))
    vals = factor_value_rows(candidates, history, yf_status)
    write_reports(root, ext, cov, vals, yf_status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
