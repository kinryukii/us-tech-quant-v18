from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import os
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


PATCH_VERSION = "V18.47C-R2"
PATCH_NAME = "Top20 90-Day Risk Event Auto Fetcher"
LOOKAHEAD_DAYS = 90

CACHE_COLUMNS = [
    "snapshot_date",
    "snapshot_timestamp",
    "lookahead_days",
    "ticker",
    "rank",
    "tracking_tier",
    "event_scope",
    "event_type",
    "event_date",
    "event_time",
    "days_to_event",
    "source_name",
    "source_status",
    "source_confidence",
    "source_conflict_flag",
    "raw_event_label",
    "raw_provider_payload_summary",
    "fetch_attempted",
    "fetch_success",
    "provider_error",
    "cache_write_timestamp",
]

DIAG_COLUMNS = [
    "ticker",
    "rank",
    "tracking_tier",
    "company_event_found",
    "earnings_date_found",
    "days_to_earnings",
    "macro_events_within_7d",
    "macro_events_within_30d",
    "macro_events_within_90d",
    "manual_seed_present",
    "auto_provider_attempted",
    "auto_provider_success",
    "source_conflict_flag",
    "final_risk_reference_score",
    "final_event_risk_level",
    "buy_aggressiveness_reference",
    "sell_review_reference",
    "unknown_reason",
    "recommended_fix",
]

SEED_COLUMNS = [
    "ticker",
    "company_name",
    "rank",
    "tracking_tier",
    "manual_next_earnings_date",
    "manual_event_date",
    "manual_event_type",
    "manual_event_risk_level",
    "manual_event_reason",
    "source_note",
    "last_reviewed_date",
    "active",
    "safe_to_copy_to_manual_seed",
]

RISK_TO_BUY = {
    "LOW_PASS": "NORMAL_REVIEW",
    "MEDIUM_REDUCE_SIZE": "SMALL_SIZE_ONLY_REFERENCE",
    "HIGH_HOLD_REVIEW": "NO_CHASE_REFERENCE",
    "EXTREME_NO_NEW_BUYS": "NO_NEW_BUYS_REFERENCE",
    "UNKNOWN_REVIEW": "EVENT_DATA_UNKNOWN_REVIEW_REQUIRED",
}

RISK_TO_SELL = {
    "LOW_PASS": "NO_EVENT_SELL_REVIEW_REQUIRED",
    "MEDIUM_REDUCE_SIZE": "REVIEW_POSITION_SIZE",
    "HIGH_HOLD_REVIEW": "REVIEW_HOLDING_RISK",
    "EXTREME_NO_NEW_BUYS": "REDUCE_RISK_REVIEW",
    "UNKNOWN_REVIEW": "EVENT_DATA_UNKNOWN_REVIEW_REQUIRED",
}


def clean(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except (OSError, UnicodeDecodeError, csv.Error):
        return []


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_int(value: object, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def parse_date(value: object) -> date | None:
    text = clean(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%Y%m%d"):
        try:
            source = text[:8] if fmt == "%Y%m%d" else text[:10]
            return datetime.strptime(source, fmt).date()
        except ValueError:
            continue
    return None


def norm_ticker(value: object) -> str:
    text = clean(value).upper().strip("'\"")
    if text.startswith("$"):
        text = text[1:]
    return text if text and not text.isdigit() else ""


def days_between(start: date, end: date) -> int:
    return (end - start).days


def source_date(row: dict[str, str]) -> date | None:
    for key in ["event_date", "manual_next_earnings_date", "manual_event_date", "earnings_date", "report_date", "next_earnings_date", "date", "calendar_date", "announcement_date"]:
        parsed = parse_date(row.get(key))
        if parsed:
            return parsed
    return None


def find_top20(root: Path) -> tuple[Path | None, list[dict[str, str]]]:
    paths = [
        root / "outputs" / "v18" / "candidates" / "V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        root / "outputs" / "v18" / "ranked_candidates" / "V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
    ]
    for path in paths:
        if path.exists():
            rows = [row for row in read_csv(path) if norm_ticker(row.get("ticker"))]
            rows.sort(key=lambda row: parse_int(row.get("rank") or row.get("freshness_eligible_rank") or row.get("original_full_rank"), 999999))
            return path, rows[:20]
    return None, []


def find_tracker(root: Path) -> tuple[Path | None, dict[str, dict[str, str]]]:
    path = root / "outputs" / "v18" / "tracking" / "V18_47B_TOP20_PRIORITY_TRACKER.csv"
    if not path.exists():
        return None, {}
    return path, {norm_ticker(row.get("ticker")): row for row in read_csv(path) if norm_ticker(row.get("ticker"))}


def cache_row(
    asof: date,
    timestamp: str,
    ticker: str,
    rank: str,
    tier: str,
    scope: str,
    event_type: str,
    event_date: date,
    source_name: str,
    source_status: str,
    confidence: str,
    raw_label: str,
    payload: str,
    attempted: str,
    success: str,
    error: str = "",
    event_time: str = "UNKNOWN",
    conflict: str = "FALSE",
) -> dict[str, str]:
    return {
        "snapshot_date": asof.isoformat(),
        "snapshot_timestamp": timestamp,
        "lookahead_days": str(LOOKAHEAD_DAYS),
        "ticker": ticker,
        "rank": rank,
        "tracking_tier": tier,
        "event_scope": scope,
        "event_type": event_type,
        "event_date": event_date.isoformat(),
        "event_time": event_time or "UNKNOWN",
        "days_to_event": str(days_between(asof, event_date)),
        "source_name": source_name,
        "source_status": source_status,
        "source_confidence": confidence,
        "source_conflict_flag": conflict,
        "raw_event_label": raw_label,
        "raw_provider_payload_summary": payload[:240],
        "fetch_attempted": attempted,
        "fetch_success": success,
        "provider_error": error[:240],
        "cache_write_timestamp": timestamp,
    }


def local_company_events(root: Path, top20: list[dict[str, str]], tracker: dict[str, dict[str, str]], asof: date, timestamp: str) -> tuple[list[dict[str, str]], set[str]]:
    sources = [
        root / "state" / "v18" / "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv",
        root / "state" / "v18" / "V18_47C_TOP20_EARNINGS_AUTO_CACHE.csv",
        root / "state" / "v18" / "cloud_earnings_event_calendar.csv",
        root / "state" / "v16" / "event_calendar.csv",
        root / "data" / "events" / "v16_earnings_overrides.csv",
        root / "state" / "v18" / "manual_event_overrides.csv",
        root / "state" / "v18" / "V18_47C_MANUAL_EVENT_OVERRIDES.csv",
    ]
    top = {norm_ticker(row.get("ticker")): row for row in top20}
    rows: list[dict[str, str]] = []
    manual_seed_present: set[str] = set()
    for path in sources:
        if not path.exists():
            continue
        for raw in read_csv(path):
            ticker = norm_ticker(raw.get("ticker") or raw.get("symbol"))
            if ticker not in top:
                continue
            if path.name == "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv":
                manual_seed_present.add(ticker)
                if clean(raw.get("active")).upper() != "TRUE":
                    continue
            event_date = source_date(raw)
            if not event_date:
                continue
            delta = days_between(asof, event_date)
            if delta < -3 or delta > LOOKAHEAD_DAYS:
                continue
            raw_type = clean(raw.get("event_type") or raw.get("manual_event_type") or raw.get("event_name") or "EARNINGS")
            event_type = "EARNINGS" if "EARN" in raw_type.upper() or "earn" in path.name.lower() else "MANUAL_COMPANY_EVENT"
            status = "MANUAL_SEED_USED" if path.name == "V18_47C_TOP20_EVENT_EARNINGS_SEED.csv" else "LOCAL_CACHE_USED"
            rows.append(cache_row(asof, timestamp, ticker, clean(top[ticker].get("rank")), clean(tracker.get(ticker, {}).get("tracking_tier")), "COMPANY", event_type, event_date, path.name, status, "HIGH" if status == "MANUAL_SEED_USED" else "MEDIUM", raw_type, clean(raw.get("notes") or raw.get("source_note") or raw.get("event_reason")), "FALSE", "TRUE"))
    return rows, manual_seed_present


def local_macro_events(root: Path, top20: list[dict[str, str]], tracker: dict[str, dict[str, str]], asof: date, timestamp: str) -> list[dict[str, str]]:
    path = root / "data" / "events" / "v16_macro_events.csv"
    if not path.exists():
        return []
    out: list[dict[str, str]] = []
    for raw in read_csv(path):
        event_date = source_date(raw)
        if not event_date:
            continue
        delta = days_between(asof, event_date)
        if delta < 0 or delta > LOOKAHEAD_DAYS:
            continue
        raw_name = clean(raw.get("event_name") or raw.get("event_type") or "OTHER_MACRO")
        upper = raw_name.upper()
        if "FOMC" in upper:
            event_type = "FOMC"
        elif "CPI" in upper:
            event_type = "CPI"
        elif "PCE" in upper:
            event_type = "PCE"
        elif "NFP" in upper or "NONFARM" in upper:
            event_type = "NFP"
        elif "GDP" in upper:
            event_type = "GDP"
        elif "UNEMPLOY" in upper:
            event_type = "UNEMPLOYMENT"
        else:
            event_type = "OTHER_MACRO"
        for candidate in top20:
            ticker = norm_ticker(candidate.get("ticker"))
            out.append(cache_row(asof, timestamp, ticker, clean(candidate.get("rank")), clean(tracker.get(ticker, {}).get("tracking_tier")), "MACRO", event_type, event_date, path.name, "LOCAL_MACRO_USED", "MEDIUM", raw_name, clean(raw.get("notes")), "FALSE", "TRUE", event_time=clean(raw.get("event_time_et"), "UNKNOWN")))
    return out


def http_json(url: str, timeout: int = 10) -> tuple[object | None, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="replace")), ""
    except Exception as exc:  # noqa: BLE001 - provider failures must be non-blocking
        return None, f"{type(exc).__name__}: {exc}"


def http_text(url: str, timeout: int = 20) -> tuple[str, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace"), ""
    except Exception as exc:  # noqa: BLE001 - provider failures must be non-blocking
        return "", f"{type(exc).__name__}: {exc}"


def alpha_bulk_cache_path(root: Path, asof: date) -> Path:
    return root / "state" / "v18" / f"V18_47C_R2_ALPHAVANTAGE_EARNINGS_CALENDAR_BULK_{asof.isoformat()}.csv"


def parse_alpha_bulk_csv(text: str) -> tuple[list[dict[str, str]], str]:
    stripped = text.strip()
    if not stripped:
        return [], "EMPTY_ALPHA_VANTAGE_RESPONSE"
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            payload = json.loads(stripped)
            return [], summarize_payload(payload)
        except json.JSONDecodeError:
            return [], stripped[:240]
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return [], "ALPHA_VANTAGE_RESPONSE_MISSING_CSV_HEADER"
    rows = [dict(row) for row in reader]
    if "symbol" not in {field.strip() for field in reader.fieldnames if field}:
        return [], "ALPHA_VANTAGE_CSV_MISSING_SYMBOL_COLUMN"
    if not rows:
        return [], "ALPHA_VANTAGE_CSV_EMPTY"
    return rows, ""


def alpha_vantage_bulk_events(
    root: Path,
    top20: list[dict[str, str]],
    tracker: dict[str, dict[str, str]],
    asof: date,
    timestamp: str,
    api_key: str,
    force_refresh: bool,
) -> tuple[list[dict[str, str]], Counter, dict[str, str]]:
    counts = Counter()
    meta = {
        "ALPHAVANTAGE_BULK_MODE": "TRUE",
        "ALPHAVANTAGE_BULK_REQUEST_ATTEMPTED": "FALSE",
        "ALPHAVANTAGE_BULK_REQUEST_SUCCESS": "FALSE",
        "ALPHAVANTAGE_BULK_CACHE_REUSED": "FALSE",
        "ALPHAVANTAGE_REQUEST_COUNT": "0",
        "ALPHAVANTAGE_PROVIDER_ERROR_SUMMARY": "NONE",
    }
    if not api_key:
        return [], counts, meta

    raw_cache = alpha_bulk_cache_path(root, asof)
    text = ""
    rows: list[dict[str, str]] = []
    parse_error = ""
    if raw_cache.exists() and not force_refresh:
        text = raw_cache.read_text(encoding="utf-8", errors="replace")
        rows, parse_error = parse_alpha_bulk_csv(text)
        if rows:
            meta["ALPHAVANTAGE_BULK_CACHE_REUSED"] = "TRUE"
        else:
            meta["ALPHAVANTAGE_PROVIDER_ERROR_SUMMARY"] = f"UNUSABLE_SAME_DAY_CACHE:{parse_error}"

    if not rows and (force_refresh or not raw_cache.exists()):
        counts["attempt"] += 1
        meta["ALPHAVANTAGE_BULK_REQUEST_ATTEMPTED"] = "TRUE"
        meta["ALPHAVANTAGE_REQUEST_COUNT"] = "1"
        url = "https://www.alphavantage.co/query?" + urllib.parse.urlencode(
            {"function": "EARNINGS_CALENDAR", "horizon": "3month", "apikey": api_key}
        )
        text, error = http_text(url)
        if error:
            counts["failed"] += 1
            meta["ALPHAVANTAGE_PROVIDER_ERROR_SUMMARY"] = error
        else:
            parsed_rows, parse_error = parse_alpha_bulk_csv(text)
            if parsed_rows:
                raw_cache.parent.mkdir(parents=True, exist_ok=True)
                raw_cache.write_text(text, encoding="utf-8")
                rows = parsed_rows
                counts["success"] += 1
                meta["ALPHAVANTAGE_BULK_REQUEST_SUCCESS"] = "TRUE"
            else:
                counts["failed"] += 1
                meta["ALPHAVANTAGE_PROVIDER_ERROR_SUMMARY"] = parse_error
    elif not rows and raw_cache.exists() and not force_refresh:
        # Request cap: do not spend another Alpha Vantage request when a same-day cache exists but is unusable.
        counts["failed"] += 1

    top = {norm_ticker(row.get("ticker")): row for row in top20}
    out: list[dict[str, str]] = []
    end = asof + timedelta(days=LOOKAHEAD_DAYS)
    for raw in rows:
        ticker = norm_ticker(raw.get("symbol"))
        if ticker not in top:
            continue
        event_date = parse_date(raw.get("reportDate"))
        if not event_date or not (asof <= event_date <= end):
            continue
        payload = ";".join(
            f"{key}={clean(raw.get(key))}"
            for key in ["symbol", "name", "reportDate", "fiscalDateEnding", "estimate", "currency"]
            if clean(raw.get(key))
        )
        out.append(
            cache_row(
                asof,
                timestamp,
                ticker,
                clean(top[ticker].get("rank")),
                clean(tracker.get(ticker, {}).get("tracking_tier")),
                "COMPANY",
                "EARNINGS",
                event_date,
                "ALPHAVANTAGE_BULK",
                "AUTO_CONFIRMED",
                "MEDIUM",
                "Alpha Vantage bulk earnings calendar",
                payload,
                meta["ALPHAVANTAGE_BULK_REQUEST_ATTEMPTED"],
                "TRUE",
                event_time=clean(raw.get("timeOfTheDay"), "UNKNOWN"),
            )
        )
    return out, counts, meta


def provider_events(root: Path, top20: list[dict[str, str]], tracker: dict[str, dict[str, str]], asof: date, timestamp: str, force_refresh: bool = False) -> tuple[list[dict[str, str]], dict[str, int], dict[str, str]]:
    keys = {
        "ALPHAVANTAGE": clean(os.environ.get("ALPHAVANTAGE_API_KEY")),
        "FINNHUB": clean(os.environ.get("FINNHUB_API_KEY")),
        "FMP": clean(os.environ.get("FMP_API_KEY")),
    }
    yfinance_enabled = importlib.util.find_spec("yfinance") is not None and clean(os.environ.get("V18_47C_R2_ENABLE_YFINANCE")).upper() == "TRUE"
    counts = Counter()
    errors: dict[str, str] = {}
    rows: list[dict[str, str]] = []
    end = asof + timedelta(days=LOOKAHEAD_DAYS)
    alpha_rows, alpha_counts, alpha_meta = alpha_vantage_bulk_events(root, top20, tracker, asof, timestamp, keys["ALPHAVANTAGE"], force_refresh)
    rows.extend(alpha_rows)
    counts.update(alpha_counts)

    for candidate in top20:
        ticker = norm_ticker(candidate.get("ticker"))
        rank = clean(candidate.get("rank"))
        tier = clean(tracker.get(ticker, {}).get("tracking_tier"))
        if keys["FINNHUB"]:
            counts["attempt"] += 1
            url = f"https://finnhub.io/api/v1/calendar/earnings?symbol={urllib.parse.quote(ticker)}&from={asof.isoformat()}&to={end.isoformat()}&token={urllib.parse.quote(keys['FINNHUB'])}"
            data, error = http_json(url)
            if error:
                counts["failed"] += 1
                errors[f"FINNHUB:{ticker}"] = error
            else:
                counts["success"] += 1
                event_date = extract_provider_date(data)
                if event_date and asof <= event_date <= end:
                    rows.append(cache_row(asof, timestamp, ticker, rank, tier, "COMPANY", "EARNINGS", event_date, "FINNHUB", "AUTO_PARTIAL", "MEDIUM", "Finnhub earnings calendar", summarize_payload(data), "TRUE", "TRUE"))
        if keys["FMP"]:
            counts["attempt"] += 1
            url = f"https://financialmodelingprep.com/api/v3/historical/earning_calendar/{urllib.parse.quote(ticker)}?apikey={urllib.parse.quote(keys['FMP'])}"
            data, error = http_json(url)
            if error:
                counts["failed"] += 1
                errors[f"FMP:{ticker}"] = error
            else:
                counts["success"] += 1
                event_date = extract_provider_date(data)
                if event_date and asof <= event_date <= end:
                    rows.append(cache_row(asof, timestamp, ticker, rank, tier, "COMPANY", "EARNINGS", event_date, "FMP", "AUTO_PARTIAL", "MEDIUM", "FMP earnings calendar", summarize_payload(data), "TRUE", "TRUE"))
        if yfinance_enabled:
            counts["attempt"] += 1
            try:
                import yfinance as yf  # type: ignore

                cal = yf.Ticker(ticker).calendar
                event_date = extract_provider_date(cal)
                counts["success"] += 1
                if event_date and asof <= event_date <= end:
                    rows.append(cache_row(asof, timestamp, ticker, rank, tier, "COMPANY", "EARNINGS", event_date, "YFINANCE", "AUTO_PARTIAL", "LOW", "yfinance calendar", summarize_payload(cal), "TRUE", "TRUE"))
            except Exception as exc:  # noqa: BLE001
                counts["failed"] += 1
                errors[f"YFINANCE:{ticker}"] = f"{type(exc).__name__}: {exc}"
    counts["success"] += len(rows) - counts["success"] if False else 0
    meta = {
        "ALPHAVANTAGE_ENABLED": "TRUE" if keys["ALPHAVANTAGE"] else "FALSE",
        "FINNHUB_ENABLED": "TRUE" if keys["FINNHUB"] else "FALSE",
        "FMP_ENABLED": "TRUE" if keys["FMP"] else "FALSE",
        "YFINANCE_FALLBACK_ENABLED": "TRUE" if yfinance_enabled else "FALSE",
    }
    return rows, counts, meta | alpha_meta | errors


def summarize_payload(data: object) -> str:
    text = json.dumps(data, default=str) if not isinstance(data, str) else data
    return text[:240]


def extract_provider_date(data: object) -> date | None:
    if isinstance(data, dict):
        for key in ["reportDate", "date", "earningsDate", "Earnings Date"]:
            parsed = parse_date(data.get(key))
            if parsed:
                return parsed
        for value in data.values():
            parsed = extract_provider_date(value)
            if parsed:
                return parsed
    if isinstance(data, list):
        for item in data:
            parsed = extract_provider_date(item)
            if parsed:
                return parsed
    if hasattr(data, "to_dict"):
        try:
            return extract_provider_date(data.to_dict())
        except Exception:
            return None
    return None


def mark_conflicts(rows: list[dict[str, str]]) -> int:
    by_ticker = defaultdict(set)
    for row in rows:
        if row["event_scope"] == "COMPANY" and row["event_type"] == "EARNINGS":
            by_ticker[row["ticker"]].add(row["event_date"])
    conflicted = {ticker for ticker, dates in by_ticker.items() if len(dates) > 1}
    for row in rows:
        if row["ticker"] in conflicted and row["event_scope"] == "COMPANY" and row["event_type"] == "EARNINGS":
            row["source_conflict_flag"] = "TRUE"
            if row["source_status"] != "MANUAL_SEED_USED":
                row["source_status"] = "AUTO_CONFLICT"
    return len(conflicted)


def score_company(days: int | None) -> int | None:
    if days is None:
        return None
    if 0 <= days <= 1:
        return 90
    if 2 <= days <= 7:
        return 75
    if 8 <= days <= 14:
        return 55
    if 15 <= days <= 30:
        return 35
    if 31 <= days <= 90:
        return 15
    return 0


def score_macro(days: int | None, event_type: str) -> int | None:
    if days is None:
        return None
    watched = {"FOMC", "CPI", "PCE", "NFP"}
    if days == 0 and event_type in watched:
        return 85
    if 0 <= days <= 1:
        return 70
    if 2 <= days <= 3:
        return 50
    if 4 <= days <= 7:
        return 25
    if 8 <= days <= 90:
        return 10
    return 0


def level_from_score(score: int | None) -> str:
    if score is None:
        return "UNKNOWN_REVIEW"
    if score <= 25:
        return "LOW_PASS"
    if score <= 50:
        return "MEDIUM_REDUCE_SIZE"
    if score <= 75:
        return "HIGH_HOLD_REVIEW"
    return "EXTREME_NO_NEW_BUYS"


def diagnostics(top20: list[dict[str, str]], tracker: dict[str, dict[str, str]], rows: list[dict[str, str]], manual_seed_present: set[str], provider_counts: Counter) -> list[dict[str, str]]:
    by_ticker = defaultdict(list)
    for row in rows:
        by_ticker[row["ticker"]].append(row)
    out: list[dict[str, str]] = []
    for candidate in top20:
        ticker = norm_ticker(candidate.get("ticker"))
        events = by_ticker[ticker]
        company = [row for row in events if row["event_scope"] == "COMPANY"]
        earnings = [row for row in company if row["event_type"] == "EARNINGS"]
        macro = [row for row in events if row["event_scope"] == "MACRO"]
        earnings_days = [parse_int(row["days_to_event"], 999999) for row in earnings]
        earnings_days = [day for day in earnings_days if day != 999999]
        best_earnings_days = min(earnings_days) if earnings_days else None
        macro_7 = sum(1 for row in macro if 0 <= parse_int(row["days_to_event"], 999999) <= 7)
        macro_30 = sum(1 for row in macro if 0 <= parse_int(row["days_to_event"], 999999) <= 30)
        macro_90 = sum(1 for row in macro if 0 <= parse_int(row["days_to_event"], 999999) <= 90)
        scores = []
        c_score = score_company(best_earnings_days)
        if c_score is not None:
            scores.append(c_score)
        for row in macro:
            m_score = score_macro(parse_int(row["days_to_event"], 999999), row["event_type"])
            if m_score is not None:
                scores.append(m_score)
        score = max(scores) if scores else None
        level = level_from_score(score)
        conflict = any(row["source_conflict_flag"] == "TRUE" for row in events)
        provider_attempted = any(row["fetch_attempted"] == "TRUE" for row in events) or provider_counts.get("attempt", 0) > 0
        provider_success = any(row["fetch_success"] == "TRUE" and row["source_name"] in {"ALPHAVANTAGE_BULK", "ALPHAVANTAGE", "FINNHUB", "FMP", "YFINANCE"} for row in events)
        if not earnings:
            unknown_reason = "NO_RELIABLE_EARNINGS_DATE"
            fix = "REVIEW_SEED_PROPOSAL_OR_FILL_MANUAL_SEED"
        elif conflict:
            unknown_reason = "AUTO_CONFLICT_REVIEW_REQUIRED"
            fix = "REVIEW_CONFLICT_AND_COPY_CONFIRMED_DATE_TO_MANUAL_SEED"
        else:
            unknown_reason = "NONE"
            fix = "NONE"
        out.append(
            {
                "ticker": ticker,
                "rank": clean(candidate.get("rank")),
                "tracking_tier": clean(tracker.get(ticker, {}).get("tracking_tier")),
                "company_event_found": "TRUE" if company else "FALSE",
                "earnings_date_found": "TRUE" if earnings else "FALSE",
                "days_to_earnings": str(best_earnings_days) if best_earnings_days is not None else "UNKNOWN",
                "macro_events_within_7d": str(macro_7),
                "macro_events_within_30d": str(macro_30),
                "macro_events_within_90d": str(macro_90),
                "manual_seed_present": "TRUE" if ticker in manual_seed_present else "FALSE",
                "auto_provider_attempted": "TRUE" if provider_attempted else "FALSE",
                "auto_provider_success": "TRUE" if provider_success else "FALSE",
                "source_conflict_flag": "TRUE" if conflict else "FALSE",
                "final_risk_reference_score": str(score) if score is not None else "UNKNOWN_REVIEW",
                "final_event_risk_level": level,
                "buy_aggressiveness_reference": RISK_TO_BUY[level],
                "sell_review_reference": RISK_TO_SELL[level],
                "unknown_reason": unknown_reason,
                "recommended_fix": fix,
            }
        )
    return out


def seed_proposals(top20: list[dict[str, str]], tracker: dict[str, dict[str, str]], diag: list[dict[str, str]], rows: list[dict[str, str]], asof: date) -> list[dict[str, str]]:
    by_ticker = defaultdict(list)
    for row in rows:
        by_ticker[row["ticker"]].append(row)
    out = []
    for candidate in top20:
        ticker = norm_ticker(candidate.get("ticker"))
        drow = next((row for row in diag if row["ticker"] == ticker), {})
        earnings = [row for row in by_ticker[ticker] if row["event_scope"] == "COMPANY" and row["event_type"] == "EARNINGS" and row["source_conflict_flag"] != "TRUE"]
        earnings.sort(key=lambda row: parse_int(row["days_to_event"], 999999))
        event_date = earnings[0]["event_date"] if earnings else ""
        safe = "TRUE" if event_date else "FALSE"
        out.append(
            {
                "ticker": ticker,
                "company_name": clean(candidate.get("company_name") or candidate.get("company")),
                "rank": clean(candidate.get("rank")),
                "tracking_tier": clean(tracker.get(ticker, {}).get("tracking_tier")),
                "manual_next_earnings_date": event_date,
                "manual_event_date": event_date,
                "manual_event_type": "EARNINGS" if event_date else "",
                "manual_event_risk_level": drow.get("final_event_risk_level", "UNKNOWN_REVIEW"),
                "manual_event_reason": "Review and copy only after confirming source date." if event_date else "No reliable auto date found; manual review required.",
                "source_note": clean(earnings[0]["source_name"] if earnings else "AUTO_MISSING"),
                "last_reviewed_date": asof.isoformat(),
                "active": "FALSE",
                "safe_to_copy_to_manual_seed": safe,
            }
        )
    return out


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def build_report(top20_source: str, tracker_source: str, provider_meta: dict[str, str], diag: list[dict[str, str]], seed_rows: list[dict[str, str]], conflict_count: int) -> str:
    levels = Counter(row["final_event_risk_level"] for row in diag)
    found = [row for row in diag if row["earnings_date_found"] == "TRUE"]
    missing = [row for row in diag if row["earnings_date_found"] != "TRUE"]
    sections = [
        f"# {PATCH_VERSION} Top20 90-Day Risk Event Auto Fetch Report",
        "",
        "V18.47C-R2 identifies upcoming risk events and writes reference-only risk fields. It does not predict event outcomes, earnings results, macro impact, Fed outcomes, or stock direction.",
        "",
        "## Sources and Providers",
        markdown_table([
            {"metric": "CURRENT_TOP20_SOURCE", "value": top20_source},
            {"metric": "TRACKER_SOURCE", "value": tracker_source},
            {"metric": "LOOKAHEAD_DAYS", "value": str(LOOKAHEAD_DAYS)},
            {"metric": "ALPHAVANTAGE_ENABLED", "value": provider_meta.get("ALPHAVANTAGE_ENABLED", "FALSE")},
            {"metric": "YFINANCE_FALLBACK_ENABLED", "value": provider_meta.get("YFINANCE_FALLBACK_ENABLED", "FALSE")},
            {"metric": "FINNHUB_ENABLED", "value": provider_meta.get("FINNHUB_ENABLED", "FALSE")},
            {"metric": "FMP_ENABLED", "value": provider_meta.get("FMP_ENABLED", "FALSE")},
        ], ["metric", "value"]),
        "",
        "## Company Event Coverage",
        markdown_table([
            {"metric": "EARNINGS_DATE_FOUND_COUNT", "value": str(len(found))},
            {"metric": "EARNINGS_DATE_MISSING_COUNT", "value": str(len(missing))},
            {"metric": "MULTI_SOURCE_CONFLICT_COUNT", "value": str(conflict_count)},
        ], ["metric", "value"]),
        "",
        "## Tickers with earnings dates found",
        markdown_table(found, ["ticker", "rank", "days_to_earnings", "final_event_risk_level"]),
        "",
        "## Tickers still missing earnings dates",
        markdown_table(missing, ["ticker", "rank", "unknown_reason", "recommended_fix"]),
        "",
        "## Risk reference distribution",
        markdown_table([{"risk_level": key, "count": str(value)} for key, value in sorted(levels.items())], ["risk_level", "count"]),
        "",
        "## Seed proposal rows safe to copy",
        markdown_table([row for row in seed_rows if row["safe_to_copy_to_manual_seed"] == "TRUE"], ["ticker", "manual_next_earnings_date", "manual_event_risk_level", "source_note"]),
        "",
        "## Safety statement",
        "Risk scores are reference-only. V18.47C-R2 does not change official ranking, factor weights, official buy permission, official sell permission, broker behavior, order behavior, or trading execution.",
        "",
        "## Suggested next step",
        "Rerun V18.47C and check UNKNOWN_REVIEW_COUNT. If coverage remains weak, review the seed proposal; if coverage is usable, proceed to V18.48A Top20 Options Data Collector.",
    ]
    return "\n".join(sections) + "\n"


def write_read_first(path: Path, values: dict[str, str]) -> None:
    order = [
        "STATUS", "PATCH_VERSION", "PATCH_NAME", "LOOKAHEAD_DAYS", "CURRENT_TOP20_SOURCE_FOUND", "CURRENT_TOP20_SOURCE_PATH",
        "TOP20_PRIORITY_TRACKER_FOUND", "TOP20_PRIORITY_TRACKER_PATH", "TOP20_TOTAL_COUNT", "API_KEYS_FOUND",
        "ALPHAVANTAGE_ENABLED", "ALPHAVANTAGE_BULK_MODE", "ALPHAVANTAGE_BULK_REQUEST_ATTEMPTED",
        "ALPHAVANTAGE_BULK_REQUEST_SUCCESS", "ALPHAVANTAGE_BULK_CACHE_REUSED", "ALPHAVANTAGE_REQUEST_COUNT",
        "YFINANCE_FALLBACK_ENABLED", "FINNHUB_ENABLED", "FMP_ENABLED", "FETCH_ATTEMPT_COUNT",
        "FETCH_SUCCESS_COUNT", "FETCH_FAILED_COUNT", "COMPANY_EVENT_FOUND_COUNT", "EARNINGS_DATE_FOUND_COUNT",
        "MACRO_EVENT_FOUND_COUNT_7D", "MACRO_EVENT_FOUND_COUNT_30D", "MACRO_EVENT_FOUND_COUNT_90D",
        "UNKNOWN_EVENT_DATA_COUNT", "MULTI_SOURCE_CONFLICT_COUNT", "SEED_PROPOSAL_FILL_BLANK_COUNT",
        "SAFE_TO_COPY_TO_MANUAL_SEED_COUNT", "CACHE_WRITTEN", "V18_47C_INTEGRATION_UPDATED",
        "OFFICIAL_RANKING_CHANGED", "FACTOR_WEIGHTS_CHANGED", "OFFICIAL_BUY_PERMISSION_CHANGED",
        "OFFICIAL_SELL_PERMISSION_CHANGED", "TRADING_EXECUTION_ALLOWED", "AUTO_TRADE", "AUTO_SELL",
        "BROKER_API_USED", "ORDER_EXECUTION_USED", "CACHE_PATH", "DIAGNOSTICS_PATH", "SEED_PROPOSAL_PATH",
        "SUMMARY_PATH", "REPORT_PATH", "VALIDATION_NOTES",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{key}: {values.get(key, '')}" for key in order) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V18.47C-R2 Top20 90-day risk event auto cache.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write-current", action="store_true")
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    asof = datetime.now().astimezone().date()
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    top20_source, top20 = find_top20(root)
    tracker_source, tracker = find_tracker(root)
    local_rows, seed_present = local_company_events(root, top20, tracker, asof, timestamp)
    macro_rows = local_macro_events(root, top20, tracker, asof, timestamp)
    provider_rows, provider_counts, provider_meta = provider_events(root, top20, tracker, asof, timestamp, args.force_refresh)
    all_rows = local_rows + macro_rows + provider_rows
    conflict_count = mark_conflicts(all_rows)
    diag_rows = diagnostics(top20, tracker, all_rows, seed_present, provider_counts)
    seed_rows = seed_proposals(top20, tracker, diag_rows, all_rows, asof)

    out_dir = root / "outputs" / "v18" / "event_risk"
    cache_path = out_dir / "V18_47C_R2_TOP20_90D_RISK_EVENT_CACHE.csv"
    diag_path = out_dir / "V18_47C_R2_TOP20_90D_RISK_EVENT_DIAGNOSTICS.csv"
    summary_path = out_dir / "V18_47C_R2_TOP20_90D_RISK_EVENT_SUMMARY.csv"
    seed_path = out_dir / "V18_47C_R2_TOP20_90D_SEED_PROPOSAL.csv"
    report_path = root / "outputs" / "v18" / "read_center" / "V18_47C_R2_TOP20_90D_RISK_EVENT_AUTO_FETCH_REPORT.md"
    read_first_path = root / "outputs" / "v18" / "ops" / "V18_47C_R2_READ_FIRST.txt"
    state_cache = root / "state" / "v18" / "V18_47C_TOP20_90D_RISK_EVENT_AUTO_CACHE.csv"

    write_csv(cache_path, all_rows, CACHE_COLUMNS)
    write_csv(state_cache, all_rows, CACHE_COLUMNS)
    write_csv(diag_path, diag_rows, DIAG_COLUMNS)
    write_csv(seed_path, seed_rows, SEED_COLUMNS)
    levels = Counter(row["final_event_risk_level"] for row in diag_rows)
    summary_rows = [
        {"summary_type": "COUNT", "summary_key": "TOP20_TOTAL_COUNT", "summary_value": str(len(top20))},
        {"summary_type": "COUNT", "summary_key": "EARNINGS_DATE_FOUND_COUNT", "summary_value": str(sum(1 for row in diag_rows if row["earnings_date_found"] == "TRUE"))},
        {"summary_type": "COUNT", "summary_key": "UNKNOWN_EVENT_DATA_COUNT", "summary_value": str(sum(1 for row in diag_rows if row["final_event_risk_level"] == "UNKNOWN_REVIEW"))},
        {"summary_type": "COUNT", "summary_key": "MULTI_SOURCE_CONFLICT_COUNT", "summary_value": str(conflict_count)},
    ] + [{"summary_type": "RISK", "summary_key": key, "summary_value": str(value)} for key, value in sorted(levels.items())] + [
        {"summary_type": "SAFETY", "summary_key": "OFFICIAL_RANKING_CHANGED", "summary_value": "FALSE"},
        {"summary_type": "SAFETY", "summary_key": "FACTOR_WEIGHTS_CHANGED", "summary_value": "FALSE"},
        {"summary_type": "SAFETY", "summary_key": "OFFICIAL_BUY_PERMISSION_CHANGED", "summary_value": "FALSE"},
        {"summary_type": "SAFETY", "summary_key": "OFFICIAL_SELL_PERMISSION_CHANGED", "summary_value": "FALSE"},
    ]
    write_csv(summary_path, summary_rows, ["summary_type", "summary_key", "summary_value"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(str(top20_source) if top20_source else "NONE", str(tracker_source) if tracker_source else "NONE", provider_meta, diag_rows, seed_rows, conflict_count), encoding="utf-8")

    api_keys_found = any(provider_meta.get(key) == "TRUE" for key in ["ALPHAVANTAGE_ENABLED", "FINNHUB_ENABLED", "FMP_ENABLED"])
    earnings_found = sum(1 for row in diag_rows if row["earnings_date_found"] == "TRUE")
    unknown_count = sum(1 for row in diag_rows if row["final_event_risk_level"] == "UNKNOWN_REVIEW")
    failed = provider_counts.get("failed", 0)
    attempts = provider_counts.get("attempt", 0)
    alpha_enabled = provider_meta.get("ALPHAVANTAGE_ENABLED") == "TRUE"
    alpha_bulk_ok = provider_meta.get("ALPHAVANTAGE_BULK_REQUEST_SUCCESS") == "TRUE" or provider_meta.get("ALPHAVANTAGE_BULK_CACHE_REUSED") == "TRUE"
    if alpha_enabled and not alpha_bulk_ok:
        status = "WARN_V18_47C_R2A_BULK_PROVIDER_FAILURE"
    elif earnings_found < 10:
        status = "WARN_V18_47C_R2A_LOW_EVENT_COVERAGE"
    else:
        status = "PASS"

    macro7 = sum(parse_int(row["macro_events_within_7d"]) for row in diag_rows)
    macro30 = sum(parse_int(row["macro_events_within_30d"]) for row in diag_rows)
    macro90 = sum(parse_int(row["macro_events_within_90d"]) for row in diag_rows)
    safe_seed = sum(1 for row in seed_rows if row["safe_to_copy_to_manual_seed"] == "TRUE")
    values = {
        "STATUS": status,
        "PATCH_VERSION": PATCH_VERSION,
        "PATCH_NAME": PATCH_NAME,
        "LOOKAHEAD_DAYS": str(LOOKAHEAD_DAYS),
        "CURRENT_TOP20_SOURCE_FOUND": "TRUE" if top20_source else "FALSE",
        "CURRENT_TOP20_SOURCE_PATH": str(top20_source) if top20_source else "NONE",
        "TOP20_PRIORITY_TRACKER_FOUND": "TRUE" if tracker_source else "FALSE",
        "TOP20_PRIORITY_TRACKER_PATH": str(tracker_source) if tracker_source else "NONE",
        "TOP20_TOTAL_COUNT": str(len(top20)),
        "API_KEYS_FOUND": "TRUE" if api_keys_found else "FALSE",
        "ALPHAVANTAGE_ENABLED": provider_meta.get("ALPHAVANTAGE_ENABLED", "FALSE"),
        "ALPHAVANTAGE_BULK_MODE": provider_meta.get("ALPHAVANTAGE_BULK_MODE", "TRUE"),
        "ALPHAVANTAGE_BULK_REQUEST_ATTEMPTED": provider_meta.get("ALPHAVANTAGE_BULK_REQUEST_ATTEMPTED", "FALSE"),
        "ALPHAVANTAGE_BULK_REQUEST_SUCCESS": provider_meta.get("ALPHAVANTAGE_BULK_REQUEST_SUCCESS", "FALSE"),
        "ALPHAVANTAGE_BULK_CACHE_REUSED": provider_meta.get("ALPHAVANTAGE_BULK_CACHE_REUSED", "FALSE"),
        "ALPHAVANTAGE_REQUEST_COUNT": provider_meta.get("ALPHAVANTAGE_REQUEST_COUNT", "0"),
        "YFINANCE_FALLBACK_ENABLED": provider_meta.get("YFINANCE_FALLBACK_ENABLED", "FALSE"),
        "FINNHUB_ENABLED": provider_meta.get("FINNHUB_ENABLED", "FALSE"),
        "FMP_ENABLED": provider_meta.get("FMP_ENABLED", "FALSE"),
        "FETCH_ATTEMPT_COUNT": str(attempts),
        "FETCH_SUCCESS_COUNT": str(provider_counts.get("success", 0)),
        "FETCH_FAILED_COUNT": str(failed),
        "COMPANY_EVENT_FOUND_COUNT": str(sum(1 for row in diag_rows if row["company_event_found"] == "TRUE")),
        "EARNINGS_DATE_FOUND_COUNT": str(earnings_found),
        "MACRO_EVENT_FOUND_COUNT_7D": str(macro7),
        "MACRO_EVENT_FOUND_COUNT_30D": str(macro30),
        "MACRO_EVENT_FOUND_COUNT_90D": str(macro90),
        "UNKNOWN_EVENT_DATA_COUNT": str(unknown_count),
        "MULTI_SOURCE_CONFLICT_COUNT": str(conflict_count),
        "SEED_PROPOSAL_FILL_BLANK_COUNT": str(sum(1 for row in seed_rows if not row["manual_next_earnings_date"])),
        "SAFE_TO_COPY_TO_MANUAL_SEED_COUNT": str(safe_seed),
        "CACHE_WRITTEN": "TRUE",
        "V18_47C_INTEGRATION_UPDATED": "TRUE",
        "OFFICIAL_RANKING_CHANGED": "FALSE",
        "FACTOR_WEIGHTS_CHANGED": "FALSE",
        "OFFICIAL_BUY_PERMISSION_CHANGED": "FALSE",
        "OFFICIAL_SELL_PERMISSION_CHANGED": "FALSE",
        "TRADING_EXECUTION_ALLOWED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "BROKER_API_USED": "FALSE",
        "ORDER_EXECUTION_USED": "FALSE",
        "CACHE_PATH": str(cache_path),
        "DIAGNOSTICS_PATH": str(diag_path),
        "SEED_PROPOSAL_PATH": str(seed_path),
        "SUMMARY_PATH": str(summary_path),
        "REPORT_PATH": str(report_path),
        "VALIDATION_NOTES": f"R2A_BULK_ALPHA_VANTAGE_MODE_REFERENCE_ONLY_NO_RANKING_WEIGHT_PERMISSION_TRADING_OR_BROKER_CHANGES;ALPHAVANTAGE_PROVIDER_ERROR_SUMMARY={provider_meta.get('ALPHAVANTAGE_PROVIDER_ERROR_SUMMARY', 'NONE')}",
    }
    write_read_first(read_first_path, values)
    print(f"STATUS: {status}")
    print(f"EARNINGS_DATE_FOUND_COUNT: {earnings_found}")
    print(f"UNKNOWN_EVENT_DATA_COUNT: {unknown_count}")
    print(f"CACHE_WRITTEN: TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
