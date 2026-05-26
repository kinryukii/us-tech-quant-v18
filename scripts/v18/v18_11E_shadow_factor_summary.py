from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
INPUT_REL = Path("outputs/v18/factor_research/V18_11C_CURRENT_CALENDAR_VWAP_RV_SHADOW_FACTORS.csv")

MODE = "SHADOW_ONLY"
OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_WEIGHT_CHANGE = "DISABLED"
AUTO_PROMOTION = "DISABLED"
AUTO_TRADE = "DISABLED"
OFFICIAL_TRADING_IMPACT = "NONE"
CANDIDATE_TRACKER_STATE_MODIFIED = "False"
FACTOR_WEIGHTS_MODIFIED = "False"


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


def as_float(value: str) -> Optional[float]:
    try:
        s = str(value or "").strip()
        if not s or "UNAVAILABLE" in s:
            return None
        return float(s)
    except Exception:
        return None


def key(row: Dict[str, str]) -> Tuple[str, str]:
    return (str(row.get("ticker", "")).strip().upper(), str(row.get("base_date", "")).strip())


def dedupe(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    seen = set()
    for row in rows:
        k = key(row)
        if k in seen:
            continue
        seen.add(k)
        out.append(row)
    return out


def metric_rows(
    section: str,
    rows: List[Dict[str, str]],
    metric: str,
    reverse: bool,
    limit: int = 10,
    predicate=None,
    note: str = "",
) -> List[Dict[str, str]]:
    candidates = []
    for row in rows:
        val = as_float(row.get(metric, ""))
        if val is None:
            continue
        if predicate is not None and not predicate(val, row):
            continue
        candidates.append((val, row))
    candidates.sort(key=lambda x: x[0], reverse=reverse)

    out = []
    for idx, (val, row) in enumerate(candidates[:limit], start=1):
        out.append(
            summary_row(
                section=section,
                rank=str(idx),
                row=row,
                metric_name=metric,
                metric_value=f"{val:.6f}",
                status=row.get("vwap_proxy_status", "") if "vwap" in metric else row.get("realized_volatility_status", ""),
                note=note,
            )
        )
    return out


def summary_row(
    section: str,
    rank: str = "",
    row: Optional[Dict[str, str]] = None,
    metric_name: str = "",
    metric_value: str = "",
    status: str = "",
    note: str = "",
) -> Dict[str, str]:
    row = row or {}
    return {
        "section": section,
        "rank": rank,
        "ticker": row.get("ticker", ""),
        "base_date": row.get("base_date", ""),
        "snapshot_date": row.get("snapshot_date", ""),
        "metric_name": metric_name,
        "metric_value": metric_value,
        "status": status,
        "note": note,
        "mode": MODE,
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_weight_change": AUTO_WEIGHT_CHANGE,
        "auto_promotion": AUTO_PROMOTION,
        "auto_trade": AUTO_TRADE,
    }


def tickers(rows: List[Dict[str, str]], limit: int = 10) -> str:
    vals = [str(r.get("ticker", "")).strip().upper() for r in rows if str(r.get("ticker", "")).strip()]
    return ", ".join(vals[:limit]) if vals else "NONE"


def active_count(rows: List[Dict[str, str]], field: str, active_values: set[str]) -> Tuple[int, int]:
    active = [r for r in rows if str(r.get(field, "")).strip() in active_values]
    return len(active), len({key(r) for r in active})


def generate(root: Path) -> Dict[str, str]:
    input_path = root / INPUT_REL
    rows, _ = read_csv(input_path)
    deduped = dedupe(rows)

    out_dir = root / "outputs/v18/factor_research"
    summary_csv = out_dir / "V18_11E_CURRENT_SHADOW_FACTOR_SUMMARY.csv"
    report_md = out_dir / "V18_11E_CURRENT_SHADOW_FACTOR_SUMMARY.md"
    read_first = out_dir / "V18_11E_READ_FIRST.txt"

    raw_count = len(rows)
    unique_ticker_count = len({str(r.get("ticker", "")).strip().upper() for r in rows if str(r.get("ticker", "")).strip()})
    unique_ticker_base_count = len({key(r) for r in rows})
    duplicate_count = raw_count - unique_ticker_base_count
    duplicate_warning = "DUPLICATES_FOUND" if duplicate_count > 0 else "NO_DUPLICATE_TICKER_BASE_DATE_ROWS"

    opex_raw, opex_unique = active_count(rows, "options_expiry_pressure_status", {"MONTHLY_OPEX_FRIDAY", "MONTHLY_OPEX_WEEK"})
    month_raw, month_unique = active_count(rows, "month_end_window_status", {"IN_FINAL_3_TRADING_DAYS"})
    quarter_raw, quarter_unique = active_count(rows, "quarter_end_window_status", {"IN_FINAL_5_TRADING_DAYS"})
    relief_raw, relief_unique = active_count(rows, "opex_relief_status", {"POST_OPEX_RELIEF_WINDOW_1_TO_3_TRADING_DAYS"})

    summary: List[Dict[str, str]] = [
        summary_row("status", metric_name="MODE", metric_value=MODE, status="OK", note="SHADOW_ONLY summary; no official trading impact."),
        summary_row("status", metric_name="OFFICIAL_DECISION_IMPACT", metric_value=OFFICIAL_DECISION_IMPACT, status="OK", note="Official decisions unchanged."),
        summary_row("status", metric_name="OFFICIAL_TRADING_IMPACT", metric_value=OFFICIAL_TRADING_IMPACT, status="OK", note="No buy/sell logic or factor weights changed."),
        summary_row("counts", metric_name="raw_candidate_row_count", metric_value=str(raw_count), status="OK"),
        summary_row("counts", metric_name="unique_ticker_count", metric_value=str(unique_ticker_count), status="OK"),
        summary_row("counts", metric_name="unique_ticker_base_date_count", metric_value=str(unique_ticker_base_count), status="OK"),
        summary_row("duplicate_warning", metric_name="duplicate_ticker_base_date_count", metric_value=str(duplicate_count), status=duplicate_warning),
        summary_row("calendar_opex", metric_name="opex_pressure_active_raw_row_count", metric_value=str(opex_raw), status="CALENDAR_PROXY_ONLY", note="No options chain / OI / IV used."),
        summary_row("calendar_opex", metric_name="opex_pressure_active_unique_ticker_base_date_count", metric_value=str(opex_unique), status="CALENDAR_PROXY_ONLY", note="No options chain / OI / IV used."),
        summary_row("calendar_opex", metric_name="month_end_active_count", metric_value=str(month_raw), status="CALENDAR_AVAILABLE"),
        summary_row("calendar_opex", metric_name="quarter_end_active_count", metric_value=str(quarter_raw), status="CALENDAR_AVAILABLE"),
        summary_row("calendar_opex", metric_name="post_opex_relief_active_count", metric_value=str(relief_raw), status="CALENDAR_PROXY_ONLY", note="No options chain / OI / IV used."),
    ]

    high_rv = metric_rows("top_10_realized_volatility", deduped, "realized_volatility_factor", True, note="Daily close realized volatility.")
    pos_vwap = metric_rows(
        "top_10_positive_vwap_proxy_deviation",
        deduped,
        "vwap_deviation_factor",
        True,
        predicate=lambda v, _r: v > 0,
        note="PROXY_ONLY_DAILY_OHLCV; not true intraday VWAP.",
    )
    neg_vwap = metric_rows(
        "top_10_negative_vwap_proxy_deviation",
        deduped,
        "vwap_deviation_factor",
        False,
        predicate=lambda v, _r: v < 0,
        note="PROXY_ONLY_DAILY_OHLCV; not true intraday VWAP.",
    )
    reclaim = metric_rows(
        "vwap_reclaim_support_candidates",
        deduped,
        "vwap_reclaim_support_factor",
        True,
        limit=50,
        predicate=lambda v, _r: v > 0,
        note="PROXY_ONLY_DAILY_OHLCV; not true intraday VWAP.",
    )
    summary.extend(high_rv)
    summary.extend(pos_vwap)
    summary.extend(neg_vwap)
    summary.extend(reclaim)

    fields = [
        "section",
        "rank",
        "ticker",
        "base_date",
        "snapshot_date",
        "metric_name",
        "metric_value",
        "status",
        "note",
        "mode",
        "official_decision_impact",
        "auto_weight_change",
        "auto_promotion",
        "auto_trade",
    ]
    write_csv(summary_csv, summary, fields)

    opex_note = "CALENDAR_PROXY_ONLY. No options chain / OI / IV used."
    vwap_note = "PROXY_ONLY_DAILY_OHLCV. Not true intraday VWAP."
    report_lines = [
        "# V18.11E Shadow Factor Summary",
        "",
        "## 1. Status And Safety Guards",
        "",
        f"- STATUS: `OK_V18_11E_SHADOW_FACTOR_SUMMARY_READY`",
        f"- MODE: `{MODE}`",
        f"- OFFICIAL_DECISION_IMPACT: `{OFFICIAL_DECISION_IMPACT}`",
        f"- AUTO_WEIGHT_CHANGE: `{AUTO_WEIGHT_CHANGE}`",
        f"- AUTO_PROMOTION: `{AUTO_PROMOTION}`",
        f"- AUTO_TRADE: `{AUTO_TRADE}`",
        f"- OFFICIAL_TRADING_IMPACT: `{OFFICIAL_TRADING_IMPACT}`",
        f"- CANDIDATE_TRACKER_STATE_MODIFIED: `{CANDIDATE_TRACKER_STATE_MODIFIED}`",
        f"- FACTOR_WEIGHTS_MODIFIED: `{FACTOR_WEIGHTS_MODIFIED}`",
        "",
        "## 2. Candidate Row Count",
        "",
        f"- RAW_CANDIDATE_ROW_COUNT: `{raw_count}`",
        "",
        "## 3. Unique Ticker Count",
        "",
        f"- UNIQUE_TICKER_COUNT: `{unique_ticker_count}`",
        "",
        "## 4. Unique Ticker + Base Date Count",
        "",
        f"- UNIQUE_TICKER_BASE_DATE_COUNT: `{unique_ticker_base_count}`",
        "",
        "## 5. Calendar/OPEX Warnings",
        "",
        f"- OPEX_PRESSURE_ACTIVE_RAW_ROW_COUNT: `{opex_raw}`",
        f"- OPEX_PRESSURE_ACTIVE_UNIQUE_TICKER_BASE_DATE_COUNT: `{opex_unique}`",
        f"- MONTH_END_ACTIVE_COUNT: `{month_raw}`",
        f"- QUARTER_END_ACTIVE_COUNT: `{quarter_raw}`",
        f"- POST_OPEX_RELIEF_ACTIVE_COUNT: `{relief_raw}`",
        f"- OPEX_METHOD: `{opex_note}`",
        "",
        "## 6. Top 10 Realized Volatility",
        "",
        table(high_rv),
        "",
        "## 7. Top 10 Positive VWAP Proxy Deviation",
        "",
        f"`{vwap_note}`",
        "",
        table(pos_vwap),
        "",
        "## 8. Top 10 Negative VWAP Proxy Deviation",
        "",
        f"`{vwap_note}`",
        "",
        table(neg_vwap),
        "",
        "## 9. VWAP Reclaim Support Candidates",
        "",
        f"`{vwap_note}`",
        "",
        table(reclaim[:10]),
        "",
        "## 10. Duplicate Snapshot/Base Date Warning",
        "",
        f"- DUPLICATE_WARNING: `{duplicate_warning}`",
        f"- DUPLICATE_TICKER_BASE_DATE_COUNT: `{duplicate_count}`",
        "",
        "## 11. Official Impact Statement",
        "",
        "This report is SHADOW_ONLY and has no official trading impact. It does not change official decisions, buy/sell logic, factor weights, or candidate tracker state.",
        "",
    ]
    report_md.write_text("\n".join(report_lines), encoding="utf-8")

    read_first.write_text(
        f"""V18.11E SHADOW FACTOR SUMMARY READ FIRST

STATUS:
OK_V18_11E_SHADOW_FACTOR_SUMMARY_READY

MODE:
{MODE}

OFFICIAL_DECISION_IMPACT:
{OFFICIAL_DECISION_IMPACT}

AUTO_WEIGHT_CHANGE:
{AUTO_WEIGHT_CHANGE}

AUTO_PROMOTION:
{AUTO_PROMOTION}

AUTO_TRADE:
{AUTO_TRADE}

OFFICIAL_TRADING_IMPACT:
{OFFICIAL_TRADING_IMPACT}

CANDIDATE_TRACKER_STATE_MODIFIED:
{CANDIDATE_TRACKER_STATE_MODIFIED}

FACTOR_WEIGHTS_MODIFIED:
{FACTOR_WEIGHTS_MODIFIED}

RAW_CANDIDATE_ROW_COUNT:
{raw_count}

UNIQUE_TICKER_COUNT:
{unique_ticker_count}

UNIQUE_TICKER_BASE_DATE_COUNT:
{unique_ticker_base_count}

DUPLICATE_WARNING:
{duplicate_warning}

DUPLICATE_TICKER_BASE_DATE_COUNT:
{duplicate_count}

OPEX_PRESSURE_ACTIVE_RAW_ROW_COUNT:
{opex_raw}

OPEX_PRESSURE_ACTIVE_UNIQUE_TICKER_BASE_DATE_COUNT:
{opex_unique}

MONTH_END_ACTIVE_COUNT:
{month_raw}

QUARTER_END_ACTIVE_COUNT:
{quarter_raw}

POST_OPEX_RELIEF_ACTIVE_COUNT:
{relief_raw}

TOP_HIGH_RV_TICKERS:
{tickers(high_rv)}

TOP_POSITIVE_VWAP_PROXY_DEVIATION_TICKERS:
{tickers(pos_vwap)}

TOP_NEGATIVE_VWAP_PROXY_DEVIATION_TICKERS:
{tickers(neg_vwap)}

VWAP_RECLAIM_CANDIDATES:
{tickers(reclaim, 50)}

VWAP_METHOD:
PROXY_ONLY_DAILY_OHLCV; Not true intraday VWAP

OPEX_METHOD:
CALENDAR_PROXY_ONLY; No options chain / OI / IV used

SUMMARY_CSV:
{summary_csv}

SUMMARY_REPORT:
{report_md}
""",
        encoding="utf-8",
    )

    return {
        "STATUS": "OK_V18_11E_SHADOW_FACTOR_SUMMARY_READY",
        "RAW_CANDIDATE_ROW_COUNT": str(raw_count),
        "UNIQUE_TICKER_COUNT": str(unique_ticker_count),
        "UNIQUE_TICKER_BASE_DATE_COUNT": str(unique_ticker_base_count),
        "DUPLICATE_WARNING": duplicate_warning,
        "OPEX_PRESSURE_ACTIVE_RAW_ROW_COUNT": str(opex_raw),
        "OPEX_PRESSURE_ACTIVE_UNIQUE_TICKER_BASE_DATE_COUNT": str(opex_unique),
        "MONTH_END_ACTIVE_COUNT": str(month_raw),
        "QUARTER_END_ACTIVE_COUNT": str(quarter_raw),
        "POST_OPEX_RELIEF_ACTIVE_COUNT": str(relief_raw),
        "TOP_HIGH_RV_TICKERS": tickers(high_rv),
        "TOP_POSITIVE_VWAP_PROXY_DEVIATION_TICKERS": tickers(pos_vwap),
        "TOP_NEGATIVE_VWAP_PROXY_DEVIATION_TICKERS": tickers(neg_vwap),
        "VWAP_RECLAIM_CANDIDATES": tickers(reclaim, 50),
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "SUMMARY_CSV": str(summary_csv),
        "SUMMARY_REPORT": str(report_md),
        "READ_FIRST": str(read_first),
    }


def table(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return "| rank | ticker | base_date | metric | value | status |\n|---:|---|---|---|---:|---|\n|  | NONE |  |  |  |  |"
    lines = ["| rank | ticker | base_date | metric | value | status |", "|---:|---|---|---|---:|---|"]
    for r in rows:
        lines.append(
            f"| {r['rank']} | {r['ticker']} | {r['base_date']} | {r['metric_name']} | {r['metric_value']} | {r['status']} |"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT_DEFAULT))
    args = ap.parse_args()
    result = generate(Path(args.root))
    for k, v in result.items():
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
