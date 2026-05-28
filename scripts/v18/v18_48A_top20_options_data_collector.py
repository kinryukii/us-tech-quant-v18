from __future__ import annotations

import argparse
import csv
import importlib.util
import math
import time
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any


PATCH_VERSION = "V18.48A"
PATCH_NAME = "Top20 Options Data Collector"

SNAPSHOT_COLUMNS = [
    "snapshot_date",
    "snapshot_timestamp",
    "ticker",
    "rank",
    "tracking_tier",
    "event_risk_level",
    "days_to_earnings",
    "underlying_price",
    "provider",
    "provider_status",
    "expiration_date",
    "days_to_expiration",
    "option_type",
    "strike",
    "moneyness_target",
    "actual_moneyness_pct",
    "bid",
    "ask",
    "mid",
    "last_price",
    "volume",
    "open_interest",
    "implied_volatility",
    "contract_symbol",
    "currency",
    "in_the_money",
    "bid_ask_spread",
    "bid_ask_spread_pct",
    "liquidity_status",
    "selected_contract_reason",
    "raw_expiration_count",
    "raw_chain_call_count",
    "raw_chain_put_count",
    "fetch_error",
    "notes",
]

DIAG_COLUMNS = [
    "snapshot_date",
    "snapshot_timestamp",
    "ticker",
    "rank",
    "tracking_tier",
    "fetch_attempted",
    "fetch_success",
    "provider",
    "provider_error_type",
    "provider_error_message",
    "underlying_price_found",
    "expiration_count",
    "selected_expiration_count",
    "snapshot_contract_count",
    "options_available",
    "options_unavailable_reason",
    "request_duration_seconds",
]


def clean(value: object, default: str = "UNKNOWN") -> str:
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


def parse_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, float) and math.isnan(value):
            return None
        text = str(value).strip()
        if not text or text.lower() == "nan" or text == "UNKNOWN":
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def parse_date(value: object) -> date | None:
    text = clean(value, "")
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def norm_ticker(value: object) -> str:
    text = clean(value, "").upper().strip("'\"")
    if text.startswith("$"):
        text = text[1:]
    return text if text and not text.isdigit() else ""


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


def find_event_risk(root: Path) -> tuple[Path | None, dict[str, dict[str, str]]]:
    path = root / "outputs" / "v18" / "event_risk" / "V18_47C_TOP20_EVENT_EARNINGS_RISK.csv"
    if not path.exists():
        return None, {}
    return path, {norm_ticker(row.get("ticker")): row for row in read_csv(path) if norm_ticker(row.get("ticker"))}


def selected_tickers(top20: list[dict[str, str]], tracker: dict[str, dict[str, str]]) -> list[str]:
    current = [norm_ticker(row.get("ticker")) for row in top20 if norm_ticker(row.get("ticker"))]
    selected = list(dict.fromkeys(current))
    for ticker, row in tracker.items():
        if clean(row.get("tracking_tier")) == "TIER_1_CORE" and ticker not in selected:
            selected.append(ticker)
    return selected[:30]


def row_for_ticker(ticker: str, top20: list[dict[str, str]]) -> dict[str, str]:
    for row in top20:
        if norm_ticker(row.get("ticker")) == ticker:
            return row
    return {"ticker": ticker, "rank": "NOT_CURRENT_TOP20"}


def choose_expirations(expirations: list[str], asof: date) -> list[tuple[str, str]]:
    buckets = [
        ("DTE_7_14", 7, 14),
        ("DTE_21_45", 21, 45),
        ("DTE_45_75", 45, 75),
        ("DTE_76_120", 76, 120),
    ]
    parsed: list[tuple[str, date, int]] = []
    for exp in expirations:
        dt = parse_date(exp)
        if dt:
            parsed.append((exp, dt, (dt - asof).days))
    selected: list[tuple[str, str]] = []
    used: set[str] = set()
    for bucket, lo, hi in buckets:
        candidates = [(exp, dte) for exp, _, dte in parsed if lo <= dte <= hi and exp not in used]
        if not candidates:
            continue
        midpoint = (lo + hi) / 2
        exp, _ = min(candidates, key=lambda item: abs(item[1] - midpoint))
        selected.append((bucket, exp))
        used.add(exp)
    return selected


def df_records(df: Any) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in df.to_dict("records")]
    except Exception:
        return []


def nearest_contract(rows: list[dict[str, Any]], target: float) -> dict[str, Any] | None:
    valid = [row for row in rows if parse_float(row.get("strike")) is not None]
    if not valid:
        return None
    return min(valid, key=lambda row: abs(float(row["strike"]) - target))


def unique_contracts(rows: list[tuple[str, str, dict[str, Any]]]) -> list[tuple[str, str, dict[str, Any]]]:
    seen: set[tuple[str, str]] = set()
    out = []
    for option_type, reason, row in rows:
        key = (option_type, clean(row.get("contractSymbol"), "") or str(row.get("strike")))
        if key not in seen:
            seen.add(key)
            out.append((option_type, reason, row))
    return out


def liquidity_status(bid: float | None, ask: float | None, oi: float | None, volume: float | None, spread_pct: float | None) -> str:
    if bid is None or ask is None:
        return "UNUSABLE"
    if bid <= 0 or ask <= 0 or ask < bid:
        return "UNUSABLE"
    if spread_pct is None:
        return "UNKNOWN"
    oi_value = oi or 0
    volume_value = volume or 0
    if spread_pct <= 0.10 and oi_value >= 100 and volume_value >= 10:
        return "GOOD"
    if spread_pct <= 0.25 and oi_value >= 20:
        return "OK"
    if bid > 0 and ask > 0:
        return "THIN"
    return "UNKNOWN"


def snapshot_row(
    snapshot_date: str,
    timestamp: str,
    ticker: str,
    rank: str,
    tier: str,
    event: dict[str, str],
    underlying: float,
    expiration: str,
    dte: int,
    option_type: str,
    moneyness_target: str,
    contract: dict[str, Any],
    raw_call_count: int,
    raw_put_count: int,
    raw_exp_count: int,
) -> dict[str, str]:
    strike = parse_float(contract.get("strike"))
    bid = parse_float(contract.get("bid"))
    ask = parse_float(contract.get("ask"))
    last_price = parse_float(contract.get("lastPrice"))
    volume = parse_float(contract.get("volume"))
    oi = parse_float(contract.get("openInterest"))
    iv = parse_float(contract.get("impliedVolatility"))
    mid = ((bid + ask) / 2) if bid is not None and ask is not None and ask >= bid else None
    spread = (ask - bid) if bid is not None and ask is not None and ask >= bid else None
    spread_pct = (spread / mid) if spread is not None and mid and mid > 0 else None
    actual_moneyness = ((strike - underlying) / underlying) if strike is not None and underlying > 0 else None
    liq = liquidity_status(bid, ask, oi, volume, spread_pct)
    return {
        "snapshot_date": snapshot_date,
        "snapshot_timestamp": timestamp,
        "ticker": ticker,
        "rank": rank,
        "tracking_tier": tier,
        "event_risk_level": clean(event.get("final_event_risk_level")),
        "days_to_earnings": clean(event.get("days_to_earnings")),
        "underlying_price": f"{underlying:.4f}",
        "provider": "yfinance",
        "provider_status": "OK",
        "expiration_date": expiration,
        "days_to_expiration": str(dte),
        "option_type": option_type,
        "strike": str(strike) if strike is not None else "UNKNOWN",
        "moneyness_target": moneyness_target,
        "actual_moneyness_pct": f"{actual_moneyness:.4f}" if actual_moneyness is not None else "UNKNOWN",
        "bid": str(bid) if bid is not None else "UNKNOWN",
        "ask": str(ask) if ask is not None else "UNKNOWN",
        "mid": f"{mid:.4f}" if mid is not None else "UNKNOWN",
        "last_price": str(last_price) if last_price is not None else "UNKNOWN",
        "volume": str(volume) if volume is not None else "UNKNOWN",
        "open_interest": str(oi) if oi is not None else "UNKNOWN",
        "implied_volatility": str(iv) if iv is not None else "UNKNOWN",
        "contract_symbol": clean(contract.get("contractSymbol")),
        "currency": clean(contract.get("currency")),
        "in_the_money": clean(contract.get("inTheMoney")),
        "bid_ask_spread": f"{spread:.4f}" if spread is not None else "UNKNOWN",
        "bid_ask_spread_pct": f"{spread_pct:.4f}" if spread_pct is not None else "UNKNOWN",
        "liquidity_status": liq,
        "selected_contract_reason": "nearest available strike for target moneyness; data-quality only",
        "raw_expiration_count": str(raw_exp_count),
        "raw_chain_call_count": str(raw_call_count),
        "raw_chain_put_count": str(raw_put_count),
        "fetch_error": "NONE",
        "notes": "Read-only options data snapshot; no options trade recommendation and no order instruction.",
    }


def fetch_ticker_options(
    yf: Any,
    ticker: str,
    rank: str,
    tier: str,
    event: dict[str, str],
    asof: date,
    snapshot_date: str,
    timestamp: str,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    start = time.time()
    diag = {
        "snapshot_date": snapshot_date,
        "snapshot_timestamp": timestamp,
        "ticker": ticker,
        "rank": rank,
        "tracking_tier": tier,
        "fetch_attempted": "TRUE",
        "fetch_success": "FALSE",
        "provider": "yfinance",
        "provider_error_type": "NONE",
        "provider_error_message": "NONE",
        "underlying_price_found": "FALSE",
        "expiration_count": "0",
        "selected_expiration_count": "0",
        "snapshot_contract_count": "0",
        "options_available": "FALSE",
        "options_unavailable_reason": "UNKNOWN",
        "request_duration_seconds": "0.00",
    }
    try:
        obj = yf.Ticker(ticker)
        price = None
        try:
            fast = getattr(obj, "fast_info", None)
            if fast:
                price = parse_float(fast.get("last_price") if hasattr(fast, "get") else getattr(fast, "last_price", None))
        except Exception:
            price = None
        if price is None:
            hist = obj.history(period="5d")
            if hist is not None and not hist.empty:
                price = parse_float(hist["Close"].dropna().iloc[-1])
        if price is None or price <= 0:
            raise ValueError("UNDERLYING_PRICE_UNAVAILABLE")
        diag["underlying_price_found"] = "TRUE"
        expirations = list(obj.options or [])
        diag["expiration_count"] = str(len(expirations))
        if not expirations:
            raise ValueError("NO_OPTION_EXPIRATIONS_AVAILABLE")
        selected_exps = choose_expirations(expirations, asof)
        diag["selected_expiration_count"] = str(len(selected_exps))
        if not selected_exps:
            raise ValueError("NO_EXPIRATIONS_IN_TARGET_DTE_BUCKETS")
        rows: list[dict[str, str]] = []
        for bucket, exp in selected_exps:
            chain = obj.option_chain(exp)
            calls = df_records(chain.calls)
            puts = df_records(chain.puts)
            exp_date = parse_date(exp)
            dte = (exp_date - asof).days if exp_date else 0
            targets = [
                ("CALL", "ATM", nearest_contract(calls, price)),
                ("CALL", "OTM_5PCT", nearest_contract(calls, price * 1.05)),
                ("CALL", "OTM_10PCT", nearest_contract(calls, price * 1.10)),
                ("PUT", "ATM", nearest_contract(puts, price)),
                ("PUT", "OTM_5PCT", nearest_contract(puts, price * 0.95)),
                ("PUT", "OTM_10PCT", nearest_contract(puts, price * 0.90)),
            ]
            for option_type, reason, contract in unique_contracts([(a, b, c) for a, b, c in targets if c is not None]):
                rows.append(snapshot_row(snapshot_date, timestamp, ticker, rank, tier, event, price, exp, dte, option_type, f"{bucket}_{reason}", contract, len(calls), len(puts), len(expirations)))
        diag["fetch_success"] = "TRUE" if rows else "FALSE"
        diag["snapshot_contract_count"] = str(len(rows))
        diag["options_available"] = "TRUE" if rows else "FALSE"
        diag["options_unavailable_reason"] = "NONE" if rows else "NO_SELECTED_CONTRACTS"
        return rows, diag
    except Exception as exc:  # noqa: BLE001 - each ticker failure is isolated
        diag["provider_error_type"] = type(exc).__name__
        diag["provider_error_message"] = str(exc)[:300]
        diag["options_unavailable_reason"] = str(exc)[:160] or type(exc).__name__
        return [], diag
    finally:
        diag["request_duration_seconds"] = f"{time.time() - start:.2f}"


def merge_history(history_path: Path, snapshot_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    history = read_csv(history_path) if history_path.exists() else []
    merged: dict[tuple[str, str, str, str, str, str], dict[str, str]] = {}
    for row in history + snapshot_rows:
        key = (
            clean(row.get("snapshot_date"), ""),
            clean(row.get("ticker"), ""),
            clean(row.get("expiration_date"), ""),
            clean(row.get("option_type"), ""),
            clean(row.get("strike"), ""),
            clean(row.get("contract_symbol"), ""),
        )
        if all(key):
            merged[key] = {column: clean(row.get(column)) for column in SNAPSHOT_COLUMNS}
    rows = list(merged.values())
    rows.sort(key=lambda row: (row["snapshot_date"], row["ticker"], row["expiration_date"], row["option_type"], parse_float(row["strike"]) or 0))
    return rows


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(column), "") for column in columns) + " |")
    return "\n".join(lines)


def build_report(top20_source: str, tracker_source: str, event_source: str, selected: list[str], snapshot_rows: list[dict[str, str]], diag_rows: list[dict[str, str]]) -> str:
    liq = Counter(row["liquidity_status"] for row in snapshot_rows)
    available = [row for row in diag_rows if row["options_available"] == "TRUE"]
    unavailable = [row for row in diag_rows if row["options_available"] != "TRUE"]
    dte = Counter(row["moneyness_target"].split("_ATM")[0].split("_OTM")[0] for row in snapshot_rows)
    thin = [row for row in snapshot_rows if row["liquidity_status"] in {"THIN", "UNUSABLE"}]
    sections = [
        f"# {PATCH_VERSION} Top20 Options Data Collector Report",
        "",
        "V18.48A is data collection only. It does not recommend options trades, does not suggest buying calls or puts, and does not generate order instructions.",
        "",
        "## Sources",
        markdown_table([
            {"metric": "CURRENT_TOP20_SOURCE", "value": top20_source},
            {"metric": "TRACKER_SOURCE", "value": tracker_source},
            {"metric": "EVENT_RISK_SOURCE", "value": event_source},
            {"metric": "SELECTED_TICKER_COUNT", "value": str(len(selected))},
        ], ["metric", "value"]),
        "",
        "## Tickers with options data available",
        markdown_table(available, ["ticker", "rank", "tracking_tier", "snapshot_contract_count"]),
        "",
        "## Tickers with options data unavailable",
        markdown_table(unavailable, ["ticker", "rank", "provider_error_type", "options_unavailable_reason"]),
        "",
        "## Liquidity distribution",
        markdown_table([{"liquidity_status": key, "count": str(value)} for key, value in sorted(liq.items())], ["liquidity_status", "count"]),
        "",
        "## DTE bucket coverage",
        markdown_table([{"dte_bucket": key, "count": str(value)} for key, value in sorted(dte.items())], ["dte_bucket", "count"]),
        "",
        "## THIN / UNUSABLE option liquidity",
        markdown_table(thin[:80], ["ticker", "expiration_date", "option_type", "strike", "moneyness_target", "liquidity_status", "bid_ask_spread_pct", "open_interest", "volume"]),
        "",
        "## Safety statement",
        "V18.48A does not change official ranking, factor weights, buy/sell permissions, final_action, event risk scoring, trading execution, broker behavior, order behavior, or signal freeze ledgers.",
        "",
        "## Suggested next step",
        "V18.48B Options Risk Radar.",
    ]
    return "\n".join(sections) + "\n"


def write_read_first(path: Path, values: dict[str, str]) -> None:
    order = [
        "STATUS", "PATCH_VERSION", "PATCH_NAME", "CURRENT_TOP20_SOURCE_FOUND", "CURRENT_TOP20_SOURCE_PATH",
        "TOP20_PRIORITY_TRACKER_FOUND", "TOP20_PRIORITY_TRACKER_PATH", "EVENT_RISK_SOURCE_FOUND", "EVENT_RISK_SOURCE_PATH",
        "SELECTED_TICKER_COUNT", "FETCH_ATTEMPT_COUNT", "FETCH_SUCCESS_COUNT", "FETCH_FAILED_COUNT",
        "OPTIONS_AVAILABLE_TICKER_COUNT", "OPTIONS_UNAVAILABLE_TICKER_COUNT", "SNAPSHOT_ROW_COUNT", "HISTORY_ROW_COUNT",
        "GOOD_LIQUIDITY_COUNT", "OK_LIQUIDITY_COUNT", "THIN_LIQUIDITY_COUNT", "UNUSABLE_LIQUIDITY_COUNT",
        "UNKNOWN_LIQUIDITY_COUNT", "CURRENT_ALIAS_WRITTEN", "OFFICIAL_RANKING_CHANGED", "FACTOR_WEIGHTS_CHANGED",
        "OFFICIAL_BUY_PERMISSION_CHANGED", "OFFICIAL_SELL_PERMISSION_CHANGED", "OPTIONS_TRADE_EXECUTION_ALLOWED",
        "TRADING_EXECUTION_ALLOWED", "AUTO_TRADE", "AUTO_SELL", "BROKER_API_USED", "ORDER_EXECUTION_USED",
        "SNAPSHOT_PATH", "HISTORY_PATH", "SUMMARY_PATH", "DIAGNOSTICS_PATH", "CURRENT_REPORT_PATH", "VALIDATION_NOTES",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{key}: {values.get(key, '')}" for key in order) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect read-only options data for current Top20 candidates.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write-current", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    asof = datetime.now().astimezone().date()
    snapshot_date = asof.isoformat()
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    top20_source, top20 = find_top20(root)
    tracker_source, tracker = find_tracker(root)
    event_source, events = find_event_risk(root)
    selected = selected_tickers(top20, tracker)
    yfinance_available = importlib.util.find_spec("yfinance") is not None

    snapshot_rows: list[dict[str, str]] = []
    diag_rows: list[dict[str, str]] = []
    if yfinance_available and selected:
        import yfinance as yf  # type: ignore

        for ticker in selected:
            source_row = row_for_ticker(ticker, top20)
            rank = clean(source_row.get("rank") or tracker.get(ticker, {}).get("latest_rank"))
            tier = clean(tracker.get(ticker, {}).get("tracking_tier"))
            rows, diag = fetch_ticker_options(yf, ticker, rank, tier, events.get(ticker, {}), asof, snapshot_date, timestamp)
            snapshot_rows.extend(rows)
            diag_rows.append(diag)
    else:
        reason = "YFINANCE_NOT_AVAILABLE" if not yfinance_available else "NO_SELECTED_TICKERS"
        for ticker in selected:
            source_row = row_for_ticker(ticker, top20)
            diag_rows.append({
                "snapshot_date": snapshot_date,
                "snapshot_timestamp": timestamp,
                "ticker": ticker,
                "rank": clean(source_row.get("rank") or tracker.get(ticker, {}).get("latest_rank")),
                "tracking_tier": clean(tracker.get(ticker, {}).get("tracking_tier")),
                "fetch_attempted": "FALSE",
                "fetch_success": "FALSE",
                "provider": "yfinance",
                "provider_error_type": reason,
                "provider_error_message": reason,
                "underlying_price_found": "FALSE",
                "expiration_count": "0",
                "selected_expiration_count": "0",
                "snapshot_contract_count": "0",
                "options_available": "FALSE",
                "options_unavailable_reason": reason,
                "request_duration_seconds": "0.00",
            })

    out_dir = root / "outputs" / "v18" / "options"
    snapshot_path = out_dir / "V18_48A_TOP20_OPTIONS_SNAPSHOT.csv"
    history_path = out_dir / "V18_48A_TOP20_OPTIONS_HISTORY.csv"
    summary_path = out_dir / "V18_48A_TOP20_OPTIONS_SUMMARY.csv"
    diag_path = out_dir / "V18_48A_TOP20_OPTIONS_PROVIDER_DIAGNOSTICS.csv"
    report_path = root / "outputs" / "v18" / "read_center" / "V18_48A_TOP20_OPTIONS_DATA_COLLECTOR_REPORT.md"
    current_report_path = root / "outputs" / "v18" / "read_center" / "V18_CURRENT_TOP20_OPTIONS_DATA_STATUS.md"
    read_first_path = root / "outputs" / "v18" / "ops" / "V18_48A_READ_FIRST.txt"

    history_rows = merge_history(history_path, snapshot_rows)
    write_csv(snapshot_path, snapshot_rows, SNAPSHOT_COLUMNS)
    write_csv(history_path, history_rows, SNAPSHOT_COLUMNS)
    write_csv(diag_path, diag_rows, DIAG_COLUMNS)
    liq = Counter(row["liquidity_status"] for row in snapshot_rows)
    summary_rows = [
        {"summary_type": "COUNT", "summary_key": "SELECTED_TICKER_COUNT", "summary_value": str(len(selected))},
        {"summary_type": "COUNT", "summary_key": "SNAPSHOT_ROW_COUNT", "summary_value": str(len(snapshot_rows))},
        {"summary_type": "COUNT", "summary_key": "HISTORY_ROW_COUNT", "summary_value": str(len(history_rows))},
    ] + [{"summary_type": "LIQUIDITY", "summary_key": key, "summary_value": str(value)} for key, value in sorted(liq.items())] + [
        {"summary_type": "SAFETY", "summary_key": "OPTIONS_TRADE_EXECUTION_ALLOWED", "summary_value": "FALSE"},
        {"summary_type": "SAFETY", "summary_key": "TRADING_EXECUTION_ALLOWED", "summary_value": "FALSE"},
    ]
    write_csv(summary_path, summary_rows, ["summary_type", "summary_key", "summary_value"])
    report = build_report(str(top20_source) if top20_source else "NONE", str(tracker_source) if tracker_source else "NONE", str(event_source) if event_source else "NONE", selected, snapshot_rows, diag_rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    current_alias_written = False
    if args.write_current and (snapshot_rows or diag_rows):
        current_report_path.write_text(report, encoding="utf-8")
        current_alias_written = True

    success = sum(1 for row in diag_rows if row["fetch_success"] == "TRUE")
    attempted = sum(1 for row in diag_rows if row["fetch_attempted"] == "TRUE")
    failed = sum(1 for row in diag_rows if row["fetch_attempted"] == "TRUE" and row["fetch_success"] != "TRUE")
    if not yfinance_available:
        status = "WARN_V18_48A_YFINANCE_NOT_AVAILABLE"
    elif attempted > 0 and success == 0:
        status = "WARN_V18_48A_NO_OPTIONS_DATA_AVAILABLE"
    elif failed > 0 and success > 0:
        status = "WARN_V18_48A_OPTIONS_PROVIDER_PARTIAL_FAILURE"
    else:
        status = "PASS"

    values = {
        "STATUS": status,
        "PATCH_VERSION": PATCH_VERSION,
        "PATCH_NAME": PATCH_NAME,
        "CURRENT_TOP20_SOURCE_FOUND": "TRUE" if top20_source else "FALSE",
        "CURRENT_TOP20_SOURCE_PATH": str(top20_source) if top20_source else "NONE",
        "TOP20_PRIORITY_TRACKER_FOUND": "TRUE" if tracker_source else "FALSE",
        "TOP20_PRIORITY_TRACKER_PATH": str(tracker_source) if tracker_source else "NONE",
        "EVENT_RISK_SOURCE_FOUND": "TRUE" if event_source else "FALSE",
        "EVENT_RISK_SOURCE_PATH": str(event_source) if event_source else "NONE",
        "SELECTED_TICKER_COUNT": str(len(selected)),
        "FETCH_ATTEMPT_COUNT": str(attempted),
        "FETCH_SUCCESS_COUNT": str(success),
        "FETCH_FAILED_COUNT": str(failed),
        "OPTIONS_AVAILABLE_TICKER_COUNT": str(sum(1 for row in diag_rows if row["options_available"] == "TRUE")),
        "OPTIONS_UNAVAILABLE_TICKER_COUNT": str(sum(1 for row in diag_rows if row["options_available"] != "TRUE")),
        "SNAPSHOT_ROW_COUNT": str(len(snapshot_rows)),
        "HISTORY_ROW_COUNT": str(len(history_rows)),
        "GOOD_LIQUIDITY_COUNT": str(liq.get("GOOD", 0)),
        "OK_LIQUIDITY_COUNT": str(liq.get("OK", 0)),
        "THIN_LIQUIDITY_COUNT": str(liq.get("THIN", 0)),
        "UNUSABLE_LIQUIDITY_COUNT": str(liq.get("UNUSABLE", 0)),
        "UNKNOWN_LIQUIDITY_COUNT": str(liq.get("UNKNOWN", 0)),
        "CURRENT_ALIAS_WRITTEN": "TRUE" if current_alias_written else "FALSE",
        "OFFICIAL_RANKING_CHANGED": "FALSE",
        "FACTOR_WEIGHTS_CHANGED": "FALSE",
        "OFFICIAL_BUY_PERMISSION_CHANGED": "FALSE",
        "OFFICIAL_SELL_PERMISSION_CHANGED": "FALSE",
        "OPTIONS_TRADE_EXECUTION_ALLOWED": "FALSE",
        "TRADING_EXECUTION_ALLOWED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "BROKER_API_USED": "FALSE",
        "ORDER_EXECUTION_USED": "FALSE",
        "SNAPSHOT_PATH": str(snapshot_path),
        "HISTORY_PATH": str(history_path),
        "SUMMARY_PATH": str(summary_path),
        "DIAGNOSTICS_PATH": str(diag_path),
        "CURRENT_REPORT_PATH": str(current_report_path),
        "VALIDATION_NOTES": "READ_ONLY_OPTIONS_DATA_COLLECTION_NO_OPTIONS_TRADES_NO_RANKING_WEIGHT_PERMISSION_TRADING_OR_BROKER_CHANGES",
    }
    write_read_first(read_first_path, values)
    print(f"STATUS: {status}")
    print(f"SELECTED_TICKER_COUNT: {len(selected)}")
    print(f"FETCH_SUCCESS_COUNT: {success}")
    print(f"SNAPSHOT_ROW_COUNT: {len(snapshot_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
