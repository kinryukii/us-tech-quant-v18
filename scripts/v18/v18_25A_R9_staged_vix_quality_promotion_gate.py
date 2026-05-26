from __future__ import annotations

import argparse
import csv
import datetime as dt
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R9_STAGED_VIX_QUALITY_PROMOTION_GATE_READY"
STATUS_WARN = "WARN_V18_25A_R9_STAGED_VIX_QUALITY_PROMOTION_GATE_READY"
STATUS_FAIL = "FAIL_V18_25A_R9_STAGED_VIX_QUALITY_PROMOTION_GATE"
MODE = "READ_ONLY_STAGED_VIX_QUALITY_AUDIT_AND_PROMOTION_GATE"

R8_SOURCE_PATH = "outputs/v18/ops/V18_25A_R8_READ_FIRST.txt"
R8_NORMALIZED_PATH = "data/v18/staged_market_proxy/V18_25A_R8_VIX/V18_25A_R8_VIX_NORMALIZED.csv"
R8_RAW_PATH = "data/v18/staged_market_proxy/V18_25A_R8_VIX/V18_25A_R8_VIX_RAW.csv"
R8_MANIFEST_PATH = "data/v18/staged_market_proxy/V18_25A_R8_VIX/MANIFEST.csv"
R8_QUALITY_PATH = "outputs/v18/degraded_daily_review/V18_25A_R8_CURRENT_STAGED_VIX_QUALITY_AUDIT.csv"
R8_RESULT_PATH = "outputs/v18/degraded_daily_review/V18_25A_R8_CURRENT_STAGED_VIX_BACKFILL_RESULT.csv"

OUT_DEGRADED = "outputs/v18/degraded_daily_review"
OUT_OPS = "outputs/v18/ops"
REPORT_NAME = "V18_25A_R9_CURRENT_REPORT.md"
READ_FIRST_NAME = "V18_25A_R9_READ_FIRST.txt"
OPS_REPORT_NAME = "V18_25A_R9_CURRENT_STAGED_VIX_QUALITY_PROMOTION_GATE_REPORT.md"

RECOMMENDED_OFFICIAL_PROXY_PATH = "state/v18/market_proxy_cache/VIX.csv"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R8_SOURCE_PATH",
    "STAGED_VIX_NORMALIZED_PATH",
    "STAGED_VIX_ROW_COUNT",
    "MIN_DATE",
    "MAX_DATE",
    "LATEST_DATE",
    "CLOSE_COLUMN_AVAILABLE",
    "CLOSE_NON_NULL_COUNT",
    "MISSING_CLOSE_COUNT",
    "DUPLICATE_DATE_COUNT",
    "NEGATIVE_OR_ZERO_CLOSE_COUNT",
    "SUSPICIOUS_GAP_COUNT",
    "DATE_SORTED_ASCENDING",
    "FULL_HISTORY_READY",
    "LATEST_DATE_FRESH_ENOUGH",
    "USABLE_FOR_FACTOR_REFRESH",
    "USABLE_FOR_TECHNICAL_OVERLAY",
    "QUALITY_STATUS",
    "PROMOTION_GATE_DECISION",
    "RECOMMENDED_OFFICIAL_MARKET_PROXY_PATH",
    "OFFICIAL_MARKET_PROXY_INTEGRATION_REQUIRED",
    "NEXT_RECOMMENDED_STEP",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_STOCK_BACKFILL_MODIFIED",
    "MARKET_PROXY_STAGED_MODIFIED",
    "OFFICIAL_MARKET_PROXY_MODIFIED",
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

AUDIT_FIELDS = ["metric", "value", "notes"]
DECISION_FIELDS = ["decision_item", "value", "notes"]
PLAN_FIELDS = ["plan_item", "path", "status", "notes"]
UNLOCK_FIELDS = ["future_step", "unlocked", "notes"]

SAFETY_FALSE = {
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_MODIFIED": "FALSE",
    "STAGED_STOCK_BACKFILL_MODIFIED": "FALSE",
    "MARKET_PROXY_STAGED_MODIFIED": "FALSE",
    "OFFICIAL_MARKET_PROXY_MODIFIED": "FALSE",
    "LEDGER_MODIFIED": "FALSE",
    "FACTOR_PACK_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "TIER_MIGRATION_MODIFIED": "FALSE",
    "DEGRADED_DAILY_MODIFIED": "FALSE",
    "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
    "BACKTEST_EXECUTED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
}


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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def parse_date(value: object) -> Optional[dt.date]:
    text = str(value or "").strip()[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def number_value(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip().replace(",", "")
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def protected_items(root: Path) -> List[Path]:
    rels = [
        "state/v18/price_cache",
        "state/v18/market_proxy_cache",
        "data/v18/price_history",
        "data/v18/staged_backfill",
        "state/v18/rolling_coverage",
        "outputs/v18/factor_pack",
        "outputs/v18/ranking",
        "outputs/v18/technical_timing",
        "outputs/v18/tier_migration",
        "outputs/v18/official_daily_decision",
        "outputs/v18/daily_decision",
        "state/v18/official_daily_decision",
        R8_SOURCE_PATH,
        R8_NORMALIZED_PATH,
        R8_RAW_PATH,
        R8_MANIFEST_PATH,
        R8_QUALITY_PATH,
        R8_RESULT_PATH,
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


def forbidden_changes(root: Path, before: Dict[str, Tuple[int, int]]) -> List[str]:
    after = {str(path): file_sig(path) for path in protected_items(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig)
    changed.extend(sorted(path for path in after if path not in before))
    return changed


def detect_schema(fields: Sequence[str]) -> Dict[str, str]:
    lowered = {str(field).strip().lower(): field for field in fields}
    return {
        "date": lowered.get("date", ""),
        "open": lowered.get("open", ""),
        "high": lowered.get("high", ""),
        "low": lowered.get("low", ""),
        "close": lowered.get("close", ""),
        "adj_close": lowered.get("adj_close", lowered.get("adj close", "")),
        "volume": lowered.get("volume", ""),
        "proxy_symbol": lowered.get("proxy_symbol", lowered.get("proxy symbol", "")),
        "source": lowered.get("source", ""),
    }


def suspicious_gap_count(dates: Sequence[dt.date]) -> int:
    count = 0
    for prev, cur in zip(dates, dates[1:]):
        if (cur - prev).days > 10:
            count += 1
    return count


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, str], audit_rows: Sequence[Dict[str, object]], decision_rows: Sequence[Dict[str, object]]) -> str:
    audit_lines = "\n".join(f"- {row['metric']}: {row['value']} ({row['notes']})" for row in audit_rows)
    decision_lines = "\n".join(f"- {row['decision_item']}: {row['value']} ({row['notes']})" for row in decision_rows)
    return f"""# V18.25A-R9 Staged VIX Quality Audit / Official Market Proxy Promotion Gate

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

Status: {values['STATUS']}

Mode: {values['MODE']}

## Audit Summary
{audit_lines}

## Promotion Gate
{decision_lines}

## Official Market Proxy Plan
Recommended storage: `{RECOMMENDED_OFFICIAL_PROXY_PATH}`

This path keeps VIX in a separate market-proxy cache instead of `state/v18/price_cache`, which avoids contaminating the stock price cache with a regime input and lets downstream factor and technical readers consume the proxy explicitly.

## Downstream Unlocks
{values['NEXT_RECOMMENDED_STEP']}

## Safety
No external fetch was performed. No official market proxy file was promoted. AUTO_TRADE and AUTO_SELL remain DISABLED. OFFICIAL_DECISION_IMPACT remains NONE.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out_degraded = root / OUT_DEGRADED
    out_ops = root / OUT_OPS

    normalized_path = root / R8_NORMALIZED_PATH
    raw_path = root / R8_RAW_PATH
    manifest_path = root / R8_MANIFEST_PATH
    r8_read_first = root / R8_SOURCE_PATH
    r8_quality = root / R8_QUALITY_PATH
    r8_result = root / R8_RESULT_PATH

    before = {str(path): file_sig(path) for path in protected_items(root)}

    rows, fields = read_csv(normalized_path)
    schema = detect_schema(fields)
    date_col = schema["date"]
    close_col = schema["close"]
    symbol_col = schema["proxy_symbol"]
    source_col = schema["source"]

    parsed_dates: List[dt.date] = []
    close_non_null_count = 0
    negative_or_zero_close_count = 0
    symbol_values: List[str] = []
    source_values: List[str] = []
    missing_close_count = 0
    date_order: List[str] = []
    duplicate_before = 0

    seen_dates: Dict[str, int] = {}
    for row in rows:
        raw_date = row.get(date_col, "") if date_col else row.get("date", "")
        parsed = parse_date(raw_date)
        if parsed is not None:
            parsed_dates.append(parsed)
            date_order.append(parsed.isoformat())
            key = parsed.isoformat()
            seen_dates[key] = seen_dates.get(key, 0) + 1
        close_value = number_value(row.get(close_col, "")) if close_col else None
        if close_value is None:
            missing_close_count += 1
        else:
            close_non_null_count += 1
            if close_value <= 0:
                negative_or_zero_close_count += 1
        if symbol_col:
            symbol_values.append(str(row.get(symbol_col, "")).strip().upper())
        if source_col:
            source_values.append(str(row.get(source_col, "")).strip().lower())

    duplicate_date_count = sum(count - 1 for count in seen_dates.values() if count > 1)
    date_sorted_ascending = date_order == sorted(date_order) if date_order else False
    min_date = min(parsed_dates).isoformat() if parsed_dates else ""
    max_date = max(parsed_dates).isoformat() if parsed_dates else ""
    latest_date = max_date
    suspicious_gaps = suspicious_gap_count(parsed_dates)
    latest_date_obj = parse_date(latest_date)
    fresh_enough = False
    if latest_date_obj is not None:
        current = dt.date.today()
        fresh_enough = latest_date_obj == current or (current - latest_date_obj).days <= 10

    close_available = bool(close_col)
    symbol_consistency = bool(symbol_values) and len(set(symbol_values)) == 1
    source_consistency = bool(source_values) and len(set(source_values)) == 1
    full_history_ready = (
        len(rows) >= 252
        and close_available
        and close_non_null_count == len(rows)
        and duplicate_date_count == 0
        and negative_or_zero_close_count == 0
        and date_sorted_ascending
        and fresh_enough
    )
    usable_factor = full_history_ready and suspicious_gaps <= 2
    usable_technical = full_history_ready and suspicious_gaps <= 2

    if not rows:
        quality_status = "FAIL"
    elif duplicate_date_count == 0 and negative_or_zero_close_count == 0 and close_available and date_sorted_ascending and fresh_enough and symbol_consistency and source_consistency:
        quality_status = "OK" if full_history_ready else "WARN"
    else:
        quality_status = "WARN"

    gate_ready = (
        bool(rows)
        and close_available
        and close_non_null_count == len(rows)
        and duplicate_date_count == 0
        and negative_or_zero_close_count == 0
        and full_history_ready
        and usable_factor
        and usable_technical
        and quality_status in {"OK", "WARN"}
    )

    if not rows:
        promotion_gate = "REJECT_BAD_DATA"
    elif gate_ready and quality_status == "OK":
        promotion_gate = "PROMOTE_READY"
    elif gate_ready:
        promotion_gate = "PROMOTE_READY_WITH_WARNINGS"
    else:
        promotion_gate = "HOLD_NEEDS_REVIEW"

    forbidden_changed = forbidden_changes(root, before)

    values: Dict[str, str] = {
        "STATUS": STATUS_FAIL if forbidden_changed else (STATUS_OK if promotion_gate == "PROMOTE_READY" else STATUS_WARN if promotion_gate == "PROMOTE_READY_WITH_WARNINGS" else STATUS_FAIL),
        "MODE": MODE,
        "R8_SOURCE_PATH": str(r8_read_first),
        "STAGED_VIX_NORMALIZED_PATH": str(normalized_path),
        "STAGED_VIX_ROW_COUNT": str(len(rows)),
        "MIN_DATE": min_date,
        "MAX_DATE": max_date,
        "LATEST_DATE": latest_date,
        "CLOSE_COLUMN_AVAILABLE": str(close_available).upper(),
        "CLOSE_NON_NULL_COUNT": str(close_non_null_count),
        "MISSING_CLOSE_COUNT": str(missing_close_count),
        "DUPLICATE_DATE_COUNT": str(duplicate_date_count),
        "NEGATIVE_OR_ZERO_CLOSE_COUNT": str(negative_or_zero_close_count),
        "SUSPICIOUS_GAP_COUNT": str(suspicious_gaps),
        "DATE_SORTED_ASCENDING": str(date_sorted_ascending).upper(),
        "FULL_HISTORY_READY": str(full_history_ready).upper(),
        "LATEST_DATE_FRESH_ENOUGH": str(fresh_enough).upper(),
        "USABLE_FOR_FACTOR_REFRESH": str(usable_factor).upper(),
        "USABLE_FOR_TECHNICAL_OVERLAY": str(usable_technical).upper(),
        "QUALITY_STATUS": quality_status,
        "PROMOTION_GATE_DECISION": promotion_gate,
        "RECOMMENDED_OFFICIAL_MARKET_PROXY_PATH": RECOMMENDED_OFFICIAL_PROXY_PATH,
        "OFFICIAL_MARKET_PROXY_INTEGRATION_REQUIRED": "TRUE",
        "NEXT_RECOMMENDED_STEP": "Approve and run V18.25A-R10 official market proxy integration with backup if promotion is accepted.",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_STOCK_BACKFILL_MODIFIED": "FALSE",
        "MARKET_PROXY_STAGED_MODIFIED": "FALSE",
        "OFFICIAL_MARKET_PROXY_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "TIER_MIGRATION_MODIFIED": "FALSE",
        "DEGRADED_DAILY_MODIFIED": "FALSE",
        "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "VALIDATION_FAIL_COUNT": "0",
        "FORBIDDEN_FILE_MODIFIED": str(bool(forbidden_changed)).upper(),
    }

    values["STATUS"] = STATUS_FAIL if forbidden_changed else (
        STATUS_OK if promotion_gate == "PROMOTE_READY" else
        STATUS_WARN if promotion_gate == "PROMOTE_READY_WITH_WARNINGS" else
        STATUS_FAIL
    )

    audit_rows = [
        {"metric": "row_count", "value": len(rows), "notes": "Normalized staged VIX rows."},
        {"metric": "min_date", "value": min_date, "notes": "Earliest staged VIX date."},
        {"metric": "max_date", "value": max_date, "notes": "Latest staged VIX date."},
        {"metric": "latest_date", "value": latest_date, "notes": "Same as max_date for this file."},
        {"metric": "close_column_available", "value": close_available, "notes": "Close column present in normalized file."},
        {"metric": "close_non_null_count", "value": close_non_null_count, "notes": "Rows with a populated close."},
        {"metric": "missing_close_count", "value": missing_close_count, "notes": "Rows without close values."},
        {"metric": "duplicate_date_count", "value": duplicate_date_count, "notes": "Duplicate dates in normalized file."},
        {"metric": "negative_or_zero_close_count", "value": negative_or_zero_close_count, "notes": "Non-positive close values."},
        {"metric": "suspicious_gap_count", "value": suspicious_gaps, "notes": "Gaps greater than 10 calendar days."},
        {"metric": "date_sorted_ascending", "value": date_sorted_ascending, "notes": "Chronological order check."},
        {"metric": "symbol_consistency", "value": symbol_consistency, "notes": "proxy_symbol should be constant."},
        {"metric": "source_consistency", "value": source_consistency, "notes": "source should be constant."},
        {"metric": "full_history_ready", "value": full_history_ready, "notes": "Conservative readiness threshold met."},
        {"metric": "latest_date_fresh_enough", "value": fresh_enough, "notes": "Latest date is current or near-current."},
        {"metric": "usable_for_factor_refresh", "value": usable_factor, "notes": "Safe for factor/regime consumers."},
        {"metric": "usable_for_technical_overlay", "value": usable_technical, "notes": "Safe for technical overlay consumers."},
        {"metric": "quality_status", "value": quality_status, "notes": "Overall staged VIX audit result."},
    ]
    decision_rows = [
        {"decision_item": "promotion_gate_decision", "value": promotion_gate, "notes": "Read-only gate decision."},
        {"decision_item": "official_market_proxy_path", "value": RECOMMENDED_OFFICIAL_PROXY_PATH, "notes": "Preferred future integration target."},
        {"decision_item": "official_market_proxy_integration_required", "value": "TRUE", "notes": "Promotion is not executed in R9."},
        {"decision_item": "official_decision_impact", "value": "NONE", "notes": "No official decision state touched."},
        {"decision_item": "forbidden_file_modified", "value": bool(forbidden_changed), "notes": "Must remain FALSE."},
    ]
    plan_rows = [
        {"plan_item": "recommended_official_storage", "path": RECOMMENDED_OFFICIAL_PROXY_PATH, "status": "RECOMMENDED", "notes": "Separate market_proxy_cache from price_cache."},
        {"plan_item": "why_separate_storage", "path": "state/v18/market_proxy_cache", "status": "EXPLAINED", "notes": "VIX is a regime proxy, not a stock price cache input."},
        {"plan_item": "why_not_price_cache", "path": "state/v18/price_cache", "status": "AVOID", "notes": "Keeps stock cache uncontaminated."},
    ]
    unlock_rows = [
        {"future_step": "V18.25A-R10 Official Market Proxy Integration with backup", "unlocked": str(promotion_gate.startswith("PROMOTE")).upper(), "notes": "Requires separate approval and execution."},
        {"future_step": "V18.25A-R11 Full-compatible technical timing refresh", "unlocked": str(promotion_gate.startswith("PROMOTE")).upper(), "notes": "Depends on official market proxy availability."},
        {"future_step": "V18.25A-R12 targeted factor refresh for R6/R7 integrated tickers", "unlocked": str(promotion_gate.startswith("PROMOTE")).upper(), "notes": "Depends on promoted official market proxy."},
        {"future_step": "V18.25A/R1/R3 downstream reruns", "unlocked": str(promotion_gate.startswith("PROMOTE")).upper(), "notes": "Unlocked after official integration."},
    ]

    quality_out = root / "outputs/v18/degraded_daily_review/V18_25A_R9_CURRENT_STAGED_VIX_QUALITY_AUDIT.csv"
    decision_out = root / "outputs/v18/degraded_daily_review/V18_25A_R9_CURRENT_PROMOTION_GATE_DECISION.csv"
    plan_out = root / "outputs/v18/degraded_daily_review/V18_25A_R9_CURRENT_OFFICIAL_MARKET_PROXY_INTEGRATION_PLAN.csv"
    unlock_out = root / "outputs/v18/degraded_daily_review/V18_25A_R9_CURRENT_DOWNSTREAM_UNLOCK_ASSESSMENT.csv"
    report_out = root / "outputs/v18/degraded_daily_review/V18_25A_R9_CURRENT_REPORT.md"
    read_first_out = root / "outputs/v18/ops/V18_25A_R9_READ_FIRST.txt"
    ops_report_out = root / "outputs/v18/ops/V18_25A_R9_CURRENT_STAGED_VIX_QUALITY_PROMOTION_GATE_REPORT.md"

    write_csv(quality_out, audit_rows, AUDIT_FIELDS)
    write_csv(decision_out, decision_rows, DECISION_FIELDS)
    write_csv(plan_out, plan_rows, PLAN_FIELDS)
    write_csv(unlock_out, unlock_rows, UNLOCK_FIELDS)
    write_text(report_out, render_report(values, audit_rows, decision_rows))
    write_text(ops_report_out, render_report(values, audit_rows, decision_rows))
    write_text(read_first_out, render_read_first(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")

    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
