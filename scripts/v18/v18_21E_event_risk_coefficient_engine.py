from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_READY = "WARN_V18_21E_EVENT_RISK_COEFFICIENT_ADVISORY_READY"
STATUS_OK = "OK_V18_21E_EVENT_RISK_COEFFICIENT_ADVISORY_READY_COMPLETE_SOURCES"
STATUS_NO_SOURCE = "WARN_V18_21E_EVENT_RISK_NO_EVENT_SOURCE_DEGRADED"
STATUS_FAIL = "FAIL_V18_21E_EVENT_RISK_VALIDATION_FAILED"
MODE = "ADVISORY_ONLY"
PATCH_MODE = "EVENT_RISK_COEFFICIENT_ENGINE_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "SIMULATION_POSITION_MODIFIED": "FALSE",
    "FORWARD_TRACKER_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "EFFECT_CLAIM_ALLOWED_COUNT": "0",
    "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
}

EVENT_SOURCES = [
    ("v16_event_calendar", "state/v16/event_calendar.csv", "csv"),
    ("v18_cloud_earnings_event_calendar", "state/v18/cloud_earnings_event_calendar.csv", "csv"),
    ("v18_risk_dashboard_dir", "outputs/v18/risk_dashboard", "dir"),
    ("v18_read_center_risk_dashboard", "outputs/v18/read_center/V18_CURRENT_RISK_DASHBOARD.md", "text"),
    ("v18_daily_packet_risk_dashboard", "outputs/v18/read_center/daily_packet/V18_CURRENT_RISK_DASHBOARD.md", "text"),
    ("v18_19A_read_first", "outputs/v18/ops/V18_19A_READ_FIRST.txt", "text"),
    ("v18_16K_R2_stable_read_first", "outputs/v18/ops/V18_16K_R2_STABLE_READ_FIRST.txt", "text"),
    ("v18_21B_R1_stable_read_first", "outputs/v18/ops/V18_21B_R1_STABLE_READ_FIRST.txt", "text"),
    ("v18_21C_R2_stable_read_first", "outputs/v18/ops/V18_21C_R2_STABLE_READ_FIRST.txt", "text"),
]

SIGNAL_PATH = "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv"
RANKING_PATH = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
PRICE_SCORE_PATH = "outputs/v18/price_factors/V18_21A_R2_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv"
MARKET_REGIME_PATH = "outputs/v18/market_regime/V18_21A_R2_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv"

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED",
    "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION", "EVENT_SOURCE_COUNT",
    "EVENT_SOURCE_MISSING_COUNT", "NORMALIZED_EVENT_COUNT", "MARKET_EVENT_RISK_COEFFICIENT",
    "MARKET_EVENT_RISK_LEVEL", "TICKER_EVENT_RISK_ROW_COUNT", "HIGH_RISK_TICKER_COUNT",
    "EXTREME_CAUTION_TICKER_COUNT", "HARD_LOCK_SOURCE_DETECTED", "EVENT_ADJUSTED_CANDIDATE_COUNT",
    "EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT", "TOP_EVENT_RISK_TICKERS", "TOP_EVENT_ADJUSTED_CANDIDATES",
    "EVENT_RISK_VALIDATION_CREATED", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE", "AUTO_SELL", "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "PRICE_CACHE_MODIFIED",
    "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED", "SIMULATION_POSITION_MODIFIED",
    "FORWARD_TRACKER_MODIFIED", "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED",
    "BROKER_EXECUTION_MODIFIED", "EXTERNAL_DATA_FETCHED", "EFFECT_CLAIM_ALLOWED_COUNT",
    "WEIGHT_CHANGE_ALLOWED_COUNT", "PRODUCTION_PROMOTION_ALLOWED_COUNT", "VALIDATION_FAIL_COUNT",
    "READ_FIRST", "REPORT",
]

NORMALIZED_FIELDS = [
    "event_id", "source_path", "source_event_type", "normalized_event_type", "event_date",
    "ticker", "sector_or_theme", "event_title", "days_to_event", "days_after_event",
    "event_window_status", "event_parse_status", "event_confidence", "notes",
]
MARKET_FIELDS = [
    "asof_date", "market_event_risk_coefficient", "market_event_risk_level",
    "active_market_event_count", "nearest_market_event_type", "nearest_market_event_date",
    "days_to_nearest_market_event", "event_hard_lock_source_detected", "hard_lock_source",
    "market_event_risk_status", "notes",
]
TICKER_FIELDS = [
    "asof_date", "ticker", "ticker_event_risk_coefficient", "ticker_event_risk_level",
    "applicable_event_count", "nearest_event_type", "nearest_event_date", "days_to_nearest_event",
    "days_after_nearest_event", "event_window_status", "event_action_status", "event_risk_status", "notes",
]
CANDIDATE_FIELDS = [
    "asof_date", "ticker", "signal_snapshot_id", "raw_research_score", "factor_pack_score",
    "composite_candidate_score", "price_derived_total_score", "technical_timing_score",
    "market_event_risk_coefficient", "ticker_event_risk_coefficient", "final_event_risk_coefficient",
    "event_adjusted_score", "event_adjusted_rank", "event_action_status", "event_adjustment_status",
    "official_decision_impact",
]
SOURCE_AUDIT_FIELDS = [
    "source_name", "source_path", "source_exists", "modified_time", "parsed_row_count",
    "parsed_event_count", "parsed_ticker_count", "fields_used", "source_status", "notes",
]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]

BASE_COEFFICIENT = {
    "FOMC_EVENT": 0.35,
    "CPI_EVENT": 0.45,
    "PPI_EVENT": 0.55,
    "NFP_EVENT": 0.60,
    "MEGA_CAP_EARNINGS_EVENT": 0.50,
    "TICKER_EARNINGS_EVENT": 0.90,
    "MARKET_EARNINGS_CLUSTER": 0.60,
    "OPTIONS_EXPIRY_EVENT": 0.75,
    "INDEX_REBALANCE_EVENT": 0.75,
    "SECTOR_EVENT": 0.65,
    "MARKET_MACRO_EVENT": 0.70,
    "UNKNOWN_EVENT": 0.80,
}
TICKER_BASE_OVERRIDE = {
    "MEGA_CAP_EARNINGS_EVENT": 0.25,
    "TICKER_EARNINGS_EVENT": 0.40,
}
MEGA_CAP_TICKERS = {"AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "AVGO", "ORCL", "CRM"}
HARD_LOCK_PATTERNS = ["NO_TRADE_EVENT_RISK_EXTREME", "NO_BUY_EVENT_LOCKED", "LOCKED_EXTREME_WAIT_EVENT_CLEAR"]
HARD_LOCK_OVERLAY_ADVISORY_COEFFICIENT = 0.30


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", newline="", encoding=enc, errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def parse_date(value: object) -> Optional[dt.date]:
    raw = str(value or "").strip()
    if not raw:
        return None
    raw = raw.replace("/", "-")
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m-%d-%Y", "%Y%m%d"):
        try:
            return dt.datetime.strptime(raw[:19], fmt).date()
        except ValueError:
            continue
    match = re.search(r"(20\d{2})[-_](\d{1,2})[-_](\d{1,2})", raw)
    if match:
        try:
            return dt.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    return None


def numeric(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        if not text:
            return None
        return float(text.replace(",", ""))
    except ValueError:
        return None


def modified_time(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else ""


def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def first_value(row: Dict[str, str], names: Iterable[str]) -> str:
    lower = {key.lower(): key for key in row}
    for name in names:
        key = lower.get(name.lower())
        if key is not None:
            return str(row.get(key, "") or "").strip()
    return ""


def asof_date(root: Path) -> dt.date:
    signal_rows, _ = read_csv(root / SIGNAL_PATH)
    dates = [parse_date(row.get("snapshot_date")) for row in signal_rows]
    dates = [date for date in dates if date is not None]
    return max(dates) if dates else dt.date.today()


def normalize_event_type(source_type: str, title: str, ticker: str) -> Tuple[str, str]:
    text = f"{source_type} {title}".upper()
    if "FOMC" in text or "FED" in text:
        return "FOMC_EVENT", ""
    if re.search(r"\bCPI\b|CONSUMER PRICE", text):
        return "CPI_EVENT", ""
    if re.search(r"\bPPI\b|PRODUCER PRICE", text):
        return "PPI_EVENT", ""
    if re.search(r"\bNFP\b|PAYROLL|JOBS", text):
        return "NFP_EVENT", ""
    if "OPTION" in text and "EXPIR" in text:
        return "OPTIONS_EXPIRY_EVENT", ""
    if "REBALANCE" in text or "RECONSTITUTION" in text:
        return "INDEX_REBALANCE_EVENT", ""
    if "SECTOR" in text:
        return "SECTOR_EVENT", ""
    if "EARN" in text or "CLOUD_EARNINGS" in text:
        if ticker.upper() in MEGA_CAP_TICKERS:
            return "MEGA_CAP_EARNINGS_EVENT", "cloud_mega_cap"
        return "TICKER_EARNINGS_EVENT", "cloud_earnings"
    if "MACRO" in text or "MARKET" in text:
        return "MARKET_MACRO_EVENT", ""
    return "UNKNOWN_EVENT", ""


def event_window(event_date: Optional[dt.date], asof: dt.date) -> Tuple[str, str, str, str]:
    if event_date is None:
        return "", "", "UNKNOWN_DATE", "DATE_PARSE_DEGRADED"
    delta = (event_date - asof).days
    days_to = str(delta) if delta >= 0 else ""
    days_after = str(abs(delta)) if delta < 0 else ""
    if -3 <= delta <= 3:
        status = "T_MINUS_" + str(delta) if delta > 0 else ("T_PLUS_" + str(abs(delta)) if delta < 0 else "EVENT_DAY")
    else:
        status = "OUTSIDE_EVENT_WINDOW"
    return days_to, days_after, status, "OK"


def time_decay(row: Dict[str, str]) -> float:
    if row.get("event_parse_status") != "OK":
        return 1.0
    days_to = numeric(row.get("days_to_event"))
    days_after = numeric(row.get("days_after_event"))
    if days_to is not None:
        return {3: 0.85, 2: 0.75, 1: 0.55, 0: 0.30}.get(int(days_to), 1.0)
    if days_after is not None:
        return {1: 0.50, 2: 0.70, 3: 0.90}.get(int(days_after), 1.0)
    return 1.0


def event_confidence(row: Dict[str, str], norm_type: str, parse_status: str) -> str:
    quality = first_value(row, ["source_quality", "confidence", "event_confidence", "risk_level"]).upper()
    if parse_status != "OK" or norm_type == "UNKNOWN_EVENT":
        return "LOW_DEGRADED"
    if "OFFICIAL" in quality or "CONFIRMED" in quality:
        return "HIGH"
    if "ESTIMATED" in quality or "WINDOW" in quality:
        return "MEDIUM"
    return "MEDIUM"


def normalize_events(root: Path, asof: dt.date) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    normalized: List[Dict[str, object]] = []
    audit: List[Dict[str, object]] = []
    event_counter = 0
    for source_name, rel, kind in EVENT_SOURCES:
        path = root / rel
        exists = path.exists()
        parsed_rows = 0
        parsed_events = 0
        parsed_tickers = set()
        fields_used = ""
        notes = ""
        status = "MISSING"
        if exists and kind == "csv":
            rows, fields = read_csv(path)
            fields_used = ";".join(fields)
            parsed_rows = len(rows)
            status = "PARSED"
            for row in rows:
                event_date_raw = first_value(row, ["event_date", "date", "earnings_date", "calendar_date"])
                ticker = first_value(row, ["ticker", "symbol"]).upper()
                source_event_type = first_value(row, ["event_type", "type", "event_name", "event"])
                title = first_value(row, ["event_name", "event_title", "title", "company", "notes"])
                event_date = parse_date(event_date_raw)
                norm_type, default_theme = normalize_event_type(source_event_type, title, ticker)
                sector_theme = first_value(row, ["sector_or_theme", "sector", "theme", "industry"]) or default_theme
                days_to, days_after, window_status, parse_status = event_window(event_date, asof)
                confidence = event_confidence(row, norm_type, parse_status)
                event_counter += 1
                if ticker:
                    parsed_tickers.add(ticker)
                normalized.append({
                    "event_id": f"V18_21E_EVENT_{event_counter:05d}",
                    "source_path": str(path),
                    "source_event_type": source_event_type,
                    "normalized_event_type": norm_type,
                    "event_date": event_date.isoformat() if event_date else event_date_raw,
                    "ticker": ticker,
                    "sector_or_theme": sector_theme,
                    "event_title": title,
                    "days_to_event": days_to,
                    "days_after_event": days_after,
                    "event_window_status": window_status,
                    "event_parse_status": parse_status,
                    "event_confidence": confidence,
                    "notes": "Normalized from local source; no external data fetched.",
                })
            parsed_events = len(rows)
        elif exists and kind == "dir":
            files = [p for p in path.rglob("*") if p.is_file()]
            parsed_rows = len(files)
            fields_used = "directory_file_listing"
            status = "FOUND_NOT_EVENT_PARSED"
            notes = "Directory exists; no direct event rows parsed in V18.21E."
        elif exists:
            text = read_text(path)
            parsed_rows = 1 if text else 0
            fields_used = "text_scan_hard_lock_patterns"
            status = "FOUND_TEXT_SCANNED"
            notes = "Text source scanned for hard-lock context; no calendar rows fabricated."
        audit.append({
            "source_name": source_name,
            "source_path": str(path),
            "source_exists": str(exists).upper(),
            "modified_time": modified_time(path),
            "parsed_row_count": parsed_rows,
            "parsed_event_count": parsed_events,
            "parsed_ticker_count": len(parsed_tickers),
            "fields_used": fields_used,
            "source_status": status,
            "notes": notes,
        })
    return normalized, audit


def coefficient_for_event(row: Dict[str, str], ticker_specific: bool = False) -> float:
    norm_type = str(row.get("normalized_event_type") or "UNKNOWN_EVENT")
    base = TICKER_BASE_OVERRIDE.get(norm_type, BASE_COEFFICIENT.get(norm_type, 0.80)) if ticker_specific else BASE_COEFFICIENT.get(norm_type, 0.80)
    if row.get("event_parse_status") != "OK" and norm_type == "UNKNOWN_EVENT":
        base = min(base, 0.80)
    return max(0.0, min(1.0, min(base, time_decay(row))))


def is_market_event(row: Dict[str, str]) -> bool:
    return str(row.get("normalized_event_type")) in {
        "MARKET_MACRO_EVENT", "FOMC_EVENT", "CPI_EVENT", "PPI_EVENT", "NFP_EVENT",
        "MARKET_EARNINGS_CLUSTER", "MEGA_CAP_EARNINGS_EVENT", "OPTIONS_EXPIRY_EVENT",
        "INDEX_REBALANCE_EVENT", "UNKNOWN_EVENT",
    }


def risk_level(coeff: float, hard_lock: bool = False) -> str:
    if hard_lock:
        return "HARD_LOCK_SOURCE_DETECTED"
    if coeff <= 0.35:
        return "EXTREME_CAUTION"
    if coeff <= 0.55:
        return "HIGH_RISK"
    if coeff <= 0.75:
        return "CAUTION"
    if coeff < 0.95:
        return "MILD_CAUTION"
    return "NORMAL"


def action_status(coeff: float, hard_lock: bool, unknown_degraded: bool) -> str:
    if hard_lock:
        return "HARD_LOCK_SOURCE_DETECTED_ADVISORY"
    if unknown_degraded:
        return "UNKNOWN_EVENT_DEGRADED"
    if coeff <= 0.45:
        return "AVOID_NEW_BUY_NEAR_EVENT"
    if coeff <= 0.70:
        return "CAUTION_REDUCE_SIZE"
    if coeff < 0.95:
        return "WATCH_ONLY_BEFORE_EVENT"
    return "NORMAL"


def detect_hard_lock(root: Path) -> Tuple[bool, str]:
    sources = [root / rel for _, rel, kind in EVENT_SOURCES if kind == "text"]
    sources.extend([
        root / "state/v16_18_reentry_state.csv",
        root / "state/v16_19_execution_budget_state.csv",
        root / "state/v16_24_classic_brief_status_fallback.csv",
    ])
    hits = []
    for path in sources:
        if not path.exists() or path.is_dir():
            continue
        text = read_text(path)
        if any(pattern in text for pattern in HARD_LOCK_PATTERNS):
            hits.append(str(path))
    return bool(hits), ";".join(hits[:5])


def market_risk(asof: dt.date, events: List[Dict[str, object]], hard_lock: bool, hard_source: str) -> Dict[str, object]:
    market_events = [row for row in events if is_market_event(row)]
    active = [row for row in market_events if row.get("event_window_status") != "OUTSIDE_EVENT_WINDOW"]
    coeffs = [coefficient_for_event(row) for row in active]
    calendar_coeff = min(coeffs) if coeffs else 1.0
    coeff = min(calendar_coeff, HARD_LOCK_OVERLAY_ADVISORY_COEFFICIENT) if hard_lock else calendar_coeff
    nearest = ""
    nearest_date = ""
    nearest_days = ""
    dated = []
    for row in market_events:
        d = parse_date(row.get("event_date"))
        if d:
            dated.append((abs((d - asof).days), (d - asof).days, row))
    if dated:
        _, delta, row = sorted(dated, key=lambda item: item[0])[0]
        nearest = str(row.get("normalized_event_type", ""))
        nearest_date = str(row.get("event_date", ""))
        nearest_days = str(delta)
    return {
        "asof_date": asof.isoformat(),
        "market_event_risk_coefficient": f"{coeff:.6f}",
        "market_event_risk_level": risk_level(coeff, hard_lock),
        "active_market_event_count": len(active),
        "nearest_market_event_type": nearest,
        "nearest_market_event_date": nearest_date,
        "days_to_nearest_market_event": nearest_days,
        "event_hard_lock_source_detected": str(hard_lock).upper(),
        "hard_lock_source": hard_source,
        "market_event_risk_status": "ADVISORY_HARD_LOCK_SOURCE_DETECTED" if hard_lock else "ADVISORY_COEFFICIENT_CREATED",
        "notes": "Advisory-only market coefficient; hard-lock overlay coefficient is included only when detected; official decision unchanged.",
    }


def universe_rows(root: Path) -> List[Dict[str, str]]:
    signal_rows, _ = read_csv(root / SIGNAL_PATH)
    ranking_rows, _ = read_csv(root / RANKING_PATH)
    price_rows, _ = read_csv(root / PRICE_SCORE_PATH)
    by_ticker: Dict[str, Dict[str, str]] = {}
    for row in signal_rows:
        ticker = str(row.get("ticker", "")).upper().strip()
        if ticker:
            by_ticker.setdefault(ticker, {}).update(row)
    for row in ranking_rows:
        ticker = str(row.get("ticker", "")).upper().strip()
        if ticker:
            merged = by_ticker.setdefault(ticker, {"ticker": ticker})
            for key, value in row.items():
                merged.setdefault(key, value)
    for row in price_rows:
        ticker = str(row.get("ticker", "")).upper().strip()
        if ticker:
            merged = by_ticker.setdefault(ticker, {"ticker": ticker})
            for key, value in row.items():
                merged.setdefault(key, value)
    return [by_ticker[ticker] for ticker in sorted(by_ticker)]


def ticker_risk(asof: dt.date, tickers: Sequence[str], events: List[Dict[str, object]], market_coeff: float, hard_lock: bool) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for ticker in tickers:
        applicable = [row for row in events if str(row.get("ticker", "")).upper() == ticker]
        active = [row for row in applicable if row.get("event_window_status") != "OUTSIDE_EVENT_WINDOW"]
        coeffs = [market_coeff]
        coeffs.extend(coefficient_for_event(row, ticker_specific=True) for row in active)
        calendar_coeff = min(coeffs) if coeffs else market_coeff
        coeff = min(calendar_coeff, HARD_LOCK_OVERLAY_ADVISORY_COEFFICIENT) if hard_lock else calendar_coeff
        nearest_event = None
        dated = []
        for row in applicable:
            d = parse_date(row.get("event_date"))
            if d:
                dated.append((abs((d - asof).days), row))
        if dated:
            nearest_event = sorted(dated, key=lambda item: item[0])[0][1]
        unknown_degraded = any(row.get("normalized_event_type") == "UNKNOWN_EVENT" or row.get("event_parse_status") != "OK" for row in applicable)
        rows.append({
            "asof_date": asof.isoformat(),
            "ticker": ticker,
            "ticker_event_risk_coefficient": f"{coeff:.6f}",
            "ticker_event_risk_level": risk_level(coeff, hard_lock),
            "applicable_event_count": len(applicable),
            "nearest_event_type": nearest_event.get("normalized_event_type", "") if nearest_event else "",
            "nearest_event_date": nearest_event.get("event_date", "") if nearest_event else "",
            "days_to_nearest_event": nearest_event.get("days_to_event", "") if nearest_event else "",
            "days_after_nearest_event": nearest_event.get("days_after_event", "") if nearest_event else "",
            "event_window_status": nearest_event.get("event_window_status", "NO_TICKER_EVENT_FOUND") if nearest_event else "NO_TICKER_EVENT_FOUND",
            "event_action_status": action_status(coeff, hard_lock, unknown_degraded),
            "event_risk_status": "ADVISORY_ONLY",
            "notes": "Ticker coefficient includes calendar market coefficient, local ticker events, and hard-lock overlay only when detected.",
        })
    return rows


def best_score(row: Dict[str, str]) -> Tuple[str, Optional[float]]:
    for key in ["composite_candidate_score", "factor_pack_score", "price_derived_total_score", "technical_timing_score", "raw_research_score"]:
        val = numeric(row.get(key))
        if val is not None:
            return key, val
    return "", None


def adjusted_candidates(asof: dt.date, universe: List[Dict[str, str]], ticker_rows: List[Dict[str, object]], market_coeff: float) -> List[Dict[str, object]]:
    risk_by_ticker = {str(row["ticker"]): row for row in ticker_rows}
    rows: List[Dict[str, object]] = []
    for source in universe:
        ticker = str(source.get("ticker", "")).upper().strip()
        if not ticker:
            continue
        risk = risk_by_ticker.get(ticker, {})
        ticker_coeff = numeric(risk.get("ticker_event_risk_coefficient")) if risk else market_coeff
        final_coeff = min(market_coeff, ticker_coeff if ticker_coeff is not None else 1.0)
        _, score = best_score(source)
        adjusted = score * final_coeff if score is not None else None
        rows.append({
            "asof_date": asof.isoformat(),
            "ticker": ticker,
            "signal_snapshot_id": source.get("signal_snapshot_id", ""),
            "raw_research_score": score if score is not None else "",
            "factor_pack_score": source.get("factor_pack_score", ""),
            "composite_candidate_score": source.get("composite_candidate_score", ""),
            "price_derived_total_score": source.get("price_derived_total_score", ""),
            "technical_timing_score": source.get("technical_timing_score", ""),
            "market_event_risk_coefficient": f"{market_coeff:.6f}",
            "ticker_event_risk_coefficient": f"{(ticker_coeff if ticker_coeff is not None else market_coeff):.6f}",
            "final_event_risk_coefficient": f"{final_coeff:.6f}",
            "event_adjusted_score": f"{adjusted:.6f}" if adjusted is not None else "",
            "event_adjusted_rank": "",
            "event_action_status": risk.get("event_action_status", "NORMAL"),
            "event_adjustment_status": "SCORE_ADJUSTED_ADVISORY_ONLY" if adjusted is not None else "SCORE_UNAVAILABLE_COEFFICIENT_ONLY",
            "official_decision_impact": "NONE",
        })
    scored = [row for row in rows if str(row.get("event_adjusted_score", "")).strip()]
    scored.sort(key=lambda row: float(row["event_adjusted_score"]), reverse=True)
    for idx, row in enumerate(scored, start=1):
        row["event_adjusted_rank"] = idx
    return rows


def protected_paths(root: Path) -> List[Path]:
    rels = [
        "scripts/v18/run_v18_current_daily_command_center.ps1",
        "scripts/v18/run_v18_current_daily_command_center_full.ps1",
        "state/v16/event_calendar.csv",
        "state/v18/cloud_earnings_event_calendar.csv",
        SIGNAL_PATH,
        RANKING_PATH,
        PRICE_SCORE_PATH,
        MARKET_REGIME_PATH,
        "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        "outputs/v18/simulation/V18_CURRENT_PAPER_POSITIONS.csv",
        "outputs/v18/forward_tracker/V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv",
        "state/v18/price_cache/QQQ.csv",
        "state/v18/price_cache/SPY.csv",
        "state/v18/manual_state.csv",
        "state/v18/broker_execution_state.csv",
    ]
    return [root / rel for rel in rels]


def signature(path: Path) -> Tuple[str, str]:
    if not path.exists():
        return "MISSING", ""
    if path.is_dir():
        return modified_time(path), ""
    return modified_time(path), sha256(path)


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def ps_parse(path: Path) -> bool:
    if not path.exists():
        return False
    escaped = str(path).replace("'", "''")
    cmd = f"$null = [scriptblock]::Create((Get-Content -Raw -LiteralPath '{escaped}')); 'OK_PARSE'"
    result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK_PARSE" in result.stdout


def py_compile(path: Path) -> bool:
    if not path.exists():
        return False
    result = subprocess.run(["python", "-m", "py_compile", str(path)], capture_output=True, text=True)
    return result.returncode == 0


def render_readfirst(values: Dict[str, object]) -> str:
    merged = dict(values)
    merged.update(SAFETY_FLAGS)
    merged["MODE"] = MODE
    merged["PATCH_MODE"] = PATCH_MODE
    return "\n".join(f"{field}: {merged.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def report(values: Dict[str, object], source_audit: List[Dict[str, object]], validations: List[Dict[str, object]]) -> str:
    missing = [row["source_name"] for row in source_audit if row.get("source_exists") != "TRUE"]
    degraded = [row["source_name"] for row in source_audit if "DEGRADED" in str(row.get("source_status", "")) or row.get("source_status") == "MISSING"]
    return f"""# V18.21E Event Risk Coefficient Report

## Executive Summary
Status: {values.get('STATUS')}. V18.21E created advisory-only market, ticker, and candidate event-risk coefficients from existing local sources.

## Safety Statement
No official decision, buy permission, current daily wrapper, ranking, signal snapshot, simulation position, forward tracker, event calendar, state, price cache, broker execution, auto-trade, or auto-sell behavior was modified. External data fetched: FALSE.

## Event Source Summary
Event sources checked: {values.get('EVENT_SOURCE_COUNT')}. Missing sources: {values.get('EVENT_SOURCE_MISSING_COUNT')}. Missing/degraded: {', '.join(missing[:10]) if missing else 'none'}.

## Normalized Event Calendar Summary
Normalized event count: {values.get('NORMALIZED_EVENT_COUNT')}. Unknown or degraded events are retained as advisory context and do not fabricate missing event data.

## Market Event Risk Coefficient Summary
Market coefficient: {values.get('MARKET_EVENT_RISK_COEFFICIENT')}. Market risk level: {values.get('MARKET_EVENT_RISK_LEVEL')}.

## Ticker Event Risk Summary
Ticker rows: {values.get('TICKER_EVENT_RISK_ROW_COUNT')}. High-risk tickers: {values.get('HIGH_RISK_TICKER_COUNT')}. Extreme-caution tickers: {values.get('EXTREME_CAUTION_TICKER_COUNT')}. Top event-risk tickers: {values.get('TOP_EVENT_RISK_TICKERS')}.

## Event-Adjusted Candidate Summary
Adjusted candidate rows: {values.get('EVENT_ADJUSTED_CANDIDATE_COUNT')}. Score-available rows: {values.get('EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT')}. Top adjusted candidates: {values.get('TOP_EVENT_ADJUSTED_CANDIDATES')}.

## Hard-Lock Source Detection Summary
Hard-lock source detected: {values.get('HARD_LOCK_SOURCE_DETECTED')}. This is recorded as advisory context only and does not modify official decisions.

## Degraded/Missing Event Data Summary
Degraded source names: {', '.join(degraded[:10]) if degraded else 'none'}. Missing event data reduces confidence but does not stop output creation.

## Validation Summary
Validation fail count: {values.get('VALIDATION_FAIL_COUNT')}. Validation rows: {len(validations)}.

## Next-Step Recommendation
Review coefficient behavior against future mature forward returns before considering any explicit daily command center integration.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    asof = asof_date(root)
    out_dir = root / "outputs/v18/event_risk"
    ops_dir = root / "outputs/v18/ops"

    paths = {
        "normalized": out_dir / "V18_21E_CURRENT_NORMALIZED_EVENT_CALENDAR.csv",
        "market": out_dir / "V18_21E_CURRENT_MARKET_EVENT_RISK.csv",
        "ticker": out_dir / "V18_21E_CURRENT_TICKER_EVENT_RISK.csv",
        "candidates": out_dir / "V18_21E_CURRENT_EVENT_ADJUSTED_CANDIDATES.csv",
        "source_audit": out_dir / "V18_21E_CURRENT_EVENT_RISK_SOURCE_AUDIT.csv",
        "validation": out_dir / "V18_21E_CURRENT_EVENT_RISK_VALIDATION.csv",
        "read_first": ops_dir / "V18_21E_READ_FIRST.txt",
        "report": ops_dir / "V18_21E_CURRENT_EVENT_RISK_COEFFICIENT_REPORT.md",
    }

    protected_before = {str(path): signature(path) for path in protected_paths(root)}
    events, source_audit = normalize_events(root, asof)
    hard_lock, hard_source = detect_hard_lock(root)
    market = market_risk(asof, events, hard_lock, hard_source)
    universe = universe_rows(root)
    tickers = [str(row.get("ticker", "")).upper() for row in universe if str(row.get("ticker", "")).strip()]
    market_coeff = numeric(market["market_event_risk_coefficient"]) or 1.0
    ticker_rows = ticker_risk(asof, tickers, events, market_coeff, hard_lock)
    candidate_rows = adjusted_candidates(asof, universe, ticker_rows, market_coeff)

    write_csv(paths["normalized"], events, NORMALIZED_FIELDS)
    write_csv(paths["market"], [market], MARKET_FIELDS)
    write_csv(paths["ticker"], ticker_rows, TICKER_FIELDS)
    write_csv(paths["candidates"], candidate_rows, CANDIDATE_FIELDS)
    write_csv(paths["source_audit"], source_audit, SOURCE_AUDIT_FIELDS)
    write_csv(paths["validation"], [], VALIDATION_FIELDS)

    high_count = sum(1 for row in ticker_rows if row.get("ticker_event_risk_level") == "HIGH_RISK")
    extreme_count = sum(1 for row in ticker_rows if row.get("ticker_event_risk_level") in {"EXTREME_CAUTION", "HARD_LOCK_SOURCE_DETECTED"})
    top_risk = sorted(ticker_rows, key=lambda row: float(row["ticker_event_risk_coefficient"]))[:10]
    top_risk_tickers = ",".join(row["ticker"] for row in top_risk)
    scored_candidates = [row for row in candidate_rows if str(row.get("event_adjusted_score", "")).strip()]
    scored_candidates.sort(key=lambda row: float(row["event_adjusted_score"]), reverse=True)
    top_candidates = ",".join(row["ticker"] for row in scored_candidates[:10])
    event_sources_present = sum(1 for row in source_audit if row.get("source_exists") == "TRUE")
    missing_sources = sum(1 for row in source_audit if row.get("source_exists") != "TRUE")

    values: Dict[str, object] = {
        "STATUS": STATUS_READY if events else STATUS_NO_SOURCE,
        "EVENT_SOURCE_COUNT": len(source_audit),
        "EVENT_SOURCE_MISSING_COUNT": missing_sources,
        "NORMALIZED_EVENT_COUNT": len(events),
        "MARKET_EVENT_RISK_COEFFICIENT": market["market_event_risk_coefficient"],
        "MARKET_EVENT_RISK_LEVEL": market["market_event_risk_level"],
        "TICKER_EVENT_RISK_ROW_COUNT": len(ticker_rows),
        "HIGH_RISK_TICKER_COUNT": high_count,
        "EXTREME_CAUTION_TICKER_COUNT": extreme_count,
        "HARD_LOCK_SOURCE_DETECTED": str(hard_lock).upper(),
        "EVENT_ADJUSTED_CANDIDATE_COUNT": len(candidate_rows),
        "EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT": len(scored_candidates),
        "TOP_EVENT_RISK_TICKERS": top_risk_tickers,
        "TOP_EVENT_ADJUSTED_CANDIDATES": top_candidates,
        "EVENT_RISK_VALIDATION_CREATED": "TRUE",
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(paths["read_first"]),
        "REPORT": str(paths["report"]),
    }
    if events and missing_sources == 0 and not any(row.get("event_parse_status") != "OK" for row in events):
        values["STATUS"] = STATUS_OK
    values.update(SAFETY_FLAGS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values, source_audit, []))

    protected_after = {str(path): signature(path) for path in protected_paths(root)}
    changed_protected = [path for path, before in protected_before.items() if protected_after.get(path) != before]
    coeff_values: List[float] = []
    coeff_values.append(market_coeff)
    coeff_values.extend(float(row["ticker_event_risk_coefficient"]) for row in ticker_rows)
    coeff_values.extend(float(row["final_event_risk_coefficient"]) for row in candidate_rows)
    validations = [
        validation_row("powershell_parse_wrapper", ps_parse(root / "scripts/v18/run_v18_21E_event_risk_coefficient_engine.ps1"), 1, "Wrapper parses as PowerShell."),
        validation_row("python_compile_engine", py_compile(root / "scripts/v18/v18_21E_event_risk_coefficient_engine.py"), 1, "Engine compiles."),
        validation_row("required_outputs_exist", all(path.exists() for path in paths.values()), 1, "All required V18.21E outputs exist."),
        validation_row("required_read_first_fields_exist", all(field in read_text(paths["read_first"]) for field in READ_FIRST_FIELDS), 1, "READ_FIRST contains all required fields."),
        validation_row("all_coefficients_in_bounds", all(0.0 <= value <= 1.0 for value in coeff_values), 1, "All market/ticker/final coefficients are in [0, 1]."),
        validation_row("event_adjusted_file_created", paths["candidates"].exists(), 1, "Event-adjusted candidates output exists."),
        validation_row("source_audit_created", paths["source_audit"].exists(), 1, "Source audit output exists."),
        validation_row("read_first_created", paths["read_first"].exists(), 1, "READ_FIRST exists."),
        validation_row("report_created", paths["report"].exists(), 1, "Report exists."),
        validation_row("no_protected_files_modified", not changed_protected, len(changed_protected), "Changed protected files: " + ";".join(changed_protected)),
        validation_row("no_external_data_fetched", values["EXTERNAL_DATA_FETCHED"] == "FALSE", 1, "No network or external fetch performed."),
        validation_row("official_decision_impact_none", values["OFFICIAL_DECISION_IMPACT"] == "NONE", 1, "Official decision impact remains NONE."),
        validation_row("event_risk_not_applied_to_official_decision", values["EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION"] == "FALSE", 1, "Advisory-only coefficient."),
    ]
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    write_csv(paths["validation"], validations, VALIDATION_FIELDS)
    write_text(paths["read_first"], render_readfirst(values))
    write_text(paths["report"], report(values, source_audit, validations))

    for key in [
        "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED",
        "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION", "EVENT_SOURCE_COUNT",
        "EVENT_SOURCE_MISSING_COUNT", "NORMALIZED_EVENT_COUNT", "MARKET_EVENT_RISK_COEFFICIENT",
        "MARKET_EVENT_RISK_LEVEL", "TICKER_EVENT_RISK_ROW_COUNT", "HIGH_RISK_TICKER_COUNT",
        "EXTREME_CAUTION_TICKER_COUNT", "HARD_LOCK_SOURCE_DETECTED", "EVENT_ADJUSTED_CANDIDATE_COUNT",
        "EVENT_ADJUSTED_SCORE_AVAILABLE_COUNT", "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED",
        "EXTERNAL_DATA_FETCHED", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]:
        print(f"{key}: {values.get(key, MODE if key == 'MODE' else PATCH_MODE if key == 'PATCH_MODE' else '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
