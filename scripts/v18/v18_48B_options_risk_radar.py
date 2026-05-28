from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


PATCH_VERSION = "V18.48B"
PATCH_NAME = "Options Risk Radar"

RADAR_COLUMNS = [
    "snapshot_date", "snapshot_timestamp", "ticker", "rank", "tracking_tier", "event_risk_level",
    "days_to_earnings", "underlying_price", "options_snapshot_available", "options_contract_count",
    "good_liquidity_count", "ok_liquidity_count", "thin_liquidity_count", "unusable_liquidity_count",
    "liquidity_risk_score", "liquidity_risk_level", "atm_iv_near", "atm_iv_mid", "atm_iv_far",
    "iv_level_score", "iv_level_label", "expected_move_pct_near", "expected_move_pct_mid",
    "expected_move_pct_far", "expected_move_score", "expected_move_level", "put_call_iv_skew_score",
    "put_call_volume_ratio", "put_call_open_interest_ratio", "skew_risk_score", "skew_risk_level",
    "earnings_options_risk_score", "earnings_options_risk_level", "overall_options_risk_score",
    "overall_options_risk_level", "buy_aggressiveness_reference", "sell_review_reference",
    "options_risk_reason", "data_quality", "notes",
]

DETAIL_COLUMNS = [
    "snapshot_date", "ticker", "expiration_date", "days_to_expiration", "dte_bucket", "underlying_price",
    "atm_call_mid", "atm_put_mid", "atm_call_iv", "atm_put_iv", "atm_straddle_expected_move",
    "atm_straddle_expected_move_pct", "iv_sqrt_time_expected_move_pct", "selected_expected_move_pct",
    "otm_5_call_iv", "otm_5_put_iv", "otm_10_call_iv", "otm_10_put_iv", "put_call_iv_skew",
    "put_call_volume_ratio", "put_call_open_interest_ratio", "good_contract_count", "ok_contract_count",
    "thin_contract_count", "unusable_contract_count", "dte_bucket_liquidity_status",
    "dte_bucket_options_risk_score", "dte_bucket_options_risk_level", "calculation_notes",
]

SUMMARY_COLUMNS = [
    "snapshot_date", "ticker_count", "low_risk_count", "medium_risk_count", "high_risk_count",
    "extreme_risk_count", "unknown_review_count", "normal_review_count", "small_size_reference_count",
    "no_chase_reference_count", "no_new_buys_reference_count", "reduce_risk_review_count",
    "average_options_risk_score", "median_options_risk_score", "good_liquidity_contract_count",
    "ok_liquidity_contract_count", "thin_liquidity_contract_count", "unusable_liquidity_contract_count",
]

BUCKETS = {
    "NEAR": (7, 14, 10),
    "MID": (21, 45, 30),
    "FAR": (45, 75, 60),
    "EXTENDED": (76, 120, 90),
}

WEIGHTS = {
    "expected_move": 0.30,
    "iv": 0.25,
    "skew": 0.20,
    "liquidity": 0.15,
    "earnings": 0.10,
}


def clean(value: object, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def norm_ticker(value: object) -> str:
    text = clean(value, "").upper().strip("'\"")
    if text.startswith("$"):
        text = text[1:]
    return text if text and not text.isdigit() else ""


def parse_float(value: object) -> float | None:
    try:
        text = clean(value, "")
        if not text or text.upper() in {"UNKNOWN", "NONE", "NAN"}:
            return None
        value_float = float(text)
        if math.isnan(value_float):
            return None
        return value_float
    except (TypeError, ValueError):
        return None


def parse_int(value: object, default: int = 0) -> int:
    try:
        text = clean(value, "")
        if not text or text.upper() in {"UNKNOWN", "NONE", "NAN"}:
            return default
        return int(float(text))
    except (TypeError, ValueError):
        return default


def fmt_float(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "UNKNOWN"
    return f"{value:.{digits}f}"


def fmt_score(value: float | None) -> str:
    if value is None:
        return "UNKNOWN"
    return f"{value:.2f}"


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


def selected_tickers(top20: list[dict[str, str]], snapshot_rows: list[dict[str, str]]) -> list[str]:
    snapshot_rank: dict[str, int] = {}
    for row in snapshot_rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker and ticker not in snapshot_rank:
            snapshot_rank[ticker] = parse_int(row.get("rank"), 999999)
    if snapshot_rank:
        return [ticker for ticker, _ in sorted(snapshot_rank.items(), key=lambda item: (item[1], item[0]))]
    return [norm_ticker(row.get("ticker")) for row in top20 if norm_ticker(row.get("ticker"))][:20]


def bucket_for_dte(dte: int) -> str | None:
    for bucket, (lo, hi, _) in BUCKETS.items():
        if lo <= dte <= hi:
            return bucket
    return None


def choose_bucket_expirations(rows: list[dict[str, str]]) -> dict[str, str]:
    by_bucket: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for row in rows:
        exp = clean(row.get("expiration_date"), "")
        dte = parse_int(row.get("days_to_expiration"), -1)
        bucket = bucket_for_dte(dte)
        if exp and bucket:
            by_bucket[bucket].append((exp, dte))
    selected: dict[str, str] = {}
    for bucket, candidates in by_bucket.items():
        midpoint = BUCKETS[bucket][2]
        selected[bucket] = min(candidates, key=lambda item: abs(item[1] - midpoint))[0]
    return selected


def rows_by_type_moneyness(rows: list[dict[str, str]], option_type: str, token: str) -> list[dict[str, str]]:
    option_type = option_type.upper()
    token = token.upper()
    return [
        row for row in rows
        if clean(row.get("option_type"), "").upper() == option_type and token in clean(row.get("moneyness_target"), "").upper()
    ]


def first_float(rows: list[dict[str, str]], column: str) -> float | None:
    for row in rows:
        value = parse_float(row.get(column))
        if value is not None:
            return value
    return None


def sum_float(rows: list[dict[str, str]], column: str) -> float:
    return sum(parse_float(row.get(column)) or 0.0 for row in rows)


def classify_iv(iv: float | None) -> tuple[float | None, str]:
    if iv is None:
        return None, "UNKNOWN"
    if iv < 0.30:
        return 15, "LOW"
    if iv < 0.50:
        return 35, "MEDIUM"
    if iv < 0.80:
        return 60, "HIGH"
    return 80, "EXTREME"


def classify_expected_move(value: float | None) -> tuple[float | None, str]:
    if value is None:
        return None, "UNKNOWN"
    if value < 0.04:
        return 15, "LOW"
    if value < 0.07:
        return 35, "MEDIUM"
    if value < 0.12:
        return 60, "HIGH"
    return 85, "EXTREME"


def classify_skew(skew: float | None) -> tuple[float | None, str]:
    if skew is None:
        return None, "UNKNOWN"
    if skew <= 0.03:
        return 15, "LOW"
    if skew <= 0.08:
        return 35, "MEDIUM"
    if skew <= 0.15:
        return 60, "HIGH"
    return 80, "EXTREME"


def classify_score(score: float | None) -> str:
    if score is None:
        return "UNKNOWN_REVIEW"
    if score <= 25:
        return "LOW"
    if score <= 50:
        return "MEDIUM"
    if score <= 75:
        return "HIGH"
    return "EXTREME"


def classify_liquidity(good: int, ok: int, thin: int, unusable: int, total: int) -> tuple[float | None, str]:
    if total <= 0:
        return None, "UNKNOWN"
    usable = good + ok
    if unusable == 0 and usable / total >= 0.70:
        return 10, "LOW"
    if unusable <= max(1, int(total * 0.10)) and usable / total >= 0.45:
        return 35, "MEDIUM"
    if unusable / total >= 0.50:
        return 85, "EXTREME"
    if thin + unusable >= usable or unusable >= 3:
        return 60, "HIGH"
    return 35, "MEDIUM"


def classify_earnings(days: int | None, expected_move_level: str, liquidity_level: str) -> tuple[float | None, str]:
    if days is None:
        return None, "UNKNOWN"
    if 0 <= days <= 1:
        score = 90
    elif days <= 7:
        score = 75
    elif days <= 14:
        score = 55
    elif days <= 30:
        score = 35
    else:
        score = 15
    if expected_move_level in {"HIGH", "EXTREME"}:
        score += 10
    if liquidity_level in {"HIGH", "EXTREME"}:
        score += 10
    score = min(score, 100)
    return float(score), classify_score(float(score))


def reference_for_level(level: str) -> tuple[str, str]:
    buy_map = {
        "LOW": "NORMAL_REVIEW",
        "MEDIUM": "SMALL_SIZE_ONLY_REFERENCE",
        "HIGH": "NO_CHASE_REFERENCE",
        "EXTREME": "NO_NEW_BUYS_REFERENCE",
        "UNKNOWN_REVIEW": "OPTIONS_DATA_UNKNOWN_REVIEW_REQUIRED",
    }
    sell_map = {
        "LOW": "NO_OPTIONS_SELL_REVIEW_REQUIRED",
        "MEDIUM": "REVIEW_POSITION_SIZE",
        "HIGH": "REVIEW_HOLDING_RISK",
        "EXTREME": "REDUCE_RISK_REVIEW",
        "UNKNOWN_REVIEW": "OPTIONS_DATA_UNKNOWN_REVIEW_REQUIRED",
    }
    return buy_map.get(level, buy_map["UNKNOWN_REVIEW"]), sell_map.get(level, sell_map["UNKNOWN_REVIEW"])


def data_quality(options_available: bool, detail_rows: list[dict[str, str]], skew_score: float | None, liquidity_score: float | None) -> str:
    if not options_available:
        return "OPTIONS_SNAPSHOT_MISSING"
    if liquidity_score is None:
        return "INSUFFICIENT_LIQUIDITY_DATA"
    if not detail_rows:
        return "PARTIAL"
    if all(clean(row.get("selected_expected_move_pct")) == "UNKNOWN" for row in detail_rows):
        return "INSUFFICIENT_ATM_DATA"
    if skew_score is None:
        return "INSUFFICIENT_SKEW_DATA"
    if any("UNKNOWN" in clean(row.get("calculation_notes")) for row in detail_rows):
        return "PARTIAL"
    return "COMPLETE"


def average(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)


def build_detail_row(snapshot_date: str, ticker: str, bucket: str, exp_rows: list[dict[str, str]]) -> dict[str, str]:
    dte = parse_int(exp_rows[0].get("days_to_expiration"), 0)
    underlying = first_float(exp_rows, "underlying_price")
    calls_atm = rows_by_type_moneyness(exp_rows, "CALL", "ATM")
    puts_atm = rows_by_type_moneyness(exp_rows, "PUT", "ATM")
    calls_5 = rows_by_type_moneyness(exp_rows, "CALL", "OTM_5PCT")
    puts_5 = rows_by_type_moneyness(exp_rows, "PUT", "OTM_5PCT")
    calls_10 = rows_by_type_moneyness(exp_rows, "CALL", "OTM_10PCT")
    puts_10 = rows_by_type_moneyness(exp_rows, "PUT", "OTM_10PCT")

    atm_call_mid = first_float(calls_atm, "mid")
    atm_put_mid = first_float(puts_atm, "mid")
    atm_call_iv = first_float(calls_atm, "implied_volatility")
    atm_put_iv = first_float(puts_atm, "implied_volatility")
    atm_iv = average([atm_call_iv, atm_put_iv])
    atm_straddle = atm_call_mid + atm_put_mid if atm_call_mid is not None and atm_put_mid is not None else None
    straddle_pct = atm_straddle / underlying if atm_straddle is not None and underlying and underlying > 0 else None
    iv_move_pct = atm_iv * math.sqrt(dte / 365) if atm_iv is not None and dte > 0 else None
    selected_move_pct = straddle_pct if straddle_pct is not None else iv_move_pct

    otm_5_call_iv = first_float(calls_5, "implied_volatility")
    otm_5_put_iv = first_float(puts_5, "implied_volatility")
    otm_10_call_iv = first_float(calls_10, "implied_volatility")
    otm_10_put_iv = first_float(puts_10, "implied_volatility")
    skew_values = []
    if otm_5_call_iv is not None and otm_5_put_iv is not None:
        skew_values.append(otm_5_put_iv - otm_5_call_iv)
    if otm_10_call_iv is not None and otm_10_put_iv is not None:
        skew_values.append(otm_10_put_iv - otm_10_call_iv)
    skew = sum(skew_values) / len(skew_values) if skew_values else None

    put_rows = [row for row in exp_rows if clean(row.get("option_type"), "").upper() == "PUT"]
    call_rows = [row for row in exp_rows if clean(row.get("option_type"), "").upper() == "CALL"]
    call_volume = sum_float(call_rows, "volume")
    put_volume = sum_float(put_rows, "volume")
    call_oi = sum_float(call_rows, "open_interest")
    put_oi = sum_float(put_rows, "open_interest")
    volume_ratio = put_volume / call_volume if call_volume > 0 else None
    oi_ratio = put_oi / call_oi if call_oi > 0 else None

    liq = Counter(clean(row.get("liquidity_status")) for row in exp_rows)
    liq_score, liq_level = classify_liquidity(liq.get("GOOD", 0), liq.get("OK", 0), liq.get("THIN", 0), liq.get("UNUSABLE", 0), len(exp_rows))
    move_score, _ = classify_expected_move(selected_move_pct)
    iv_score, _ = classify_iv(atm_iv)
    skew_score, _ = classify_skew(skew)
    component_scores = [score for score in [move_score, iv_score, skew_score, liq_score] if score is not None]
    bucket_score = sum(component_scores) / len(component_scores) if component_scores else None

    notes = []
    notes.append("STRADDLE_EXPECTED_MOVE_USED" if straddle_pct is not None else "IV_SQRT_TIME_EXPECTED_MOVE_USED" if iv_move_pct is not None else "EXPECTED_MOVE_UNKNOWN")
    if skew is None:
        notes.append("SKEW_UNKNOWN")
    if liq_score is None:
        notes.append("LIQUIDITY_UNKNOWN")

    return {
        "snapshot_date": snapshot_date,
        "ticker": ticker,
        "expiration_date": clean(exp_rows[0].get("expiration_date")),
        "days_to_expiration": str(dte),
        "dte_bucket": bucket,
        "underlying_price": fmt_float(underlying),
        "atm_call_mid": fmt_float(atm_call_mid),
        "atm_put_mid": fmt_float(atm_put_mid),
        "atm_call_iv": fmt_float(atm_call_iv),
        "atm_put_iv": fmt_float(atm_put_iv),
        "atm_straddle_expected_move": fmt_float(atm_straddle),
        "atm_straddle_expected_move_pct": fmt_float(straddle_pct),
        "iv_sqrt_time_expected_move_pct": fmt_float(iv_move_pct),
        "selected_expected_move_pct": fmt_float(selected_move_pct),
        "otm_5_call_iv": fmt_float(otm_5_call_iv),
        "otm_5_put_iv": fmt_float(otm_5_put_iv),
        "otm_10_call_iv": fmt_float(otm_10_call_iv),
        "otm_10_put_iv": fmt_float(otm_10_put_iv),
        "put_call_iv_skew": fmt_float(skew),
        "put_call_volume_ratio": fmt_float(volume_ratio),
        "put_call_open_interest_ratio": fmt_float(oi_ratio),
        "good_contract_count": str(liq.get("GOOD", 0)),
        "ok_contract_count": str(liq.get("OK", 0)),
        "thin_contract_count": str(liq.get("THIN", 0)),
        "unusable_contract_count": str(liq.get("UNUSABLE", 0)),
        "dte_bucket_liquidity_status": liq_level,
        "dte_bucket_options_risk_score": fmt_score(bucket_score),
        "dte_bucket_options_risk_level": classify_score(bucket_score),
        "calculation_notes": ";".join(notes),
    }


def weighted_overall(components: dict[str, float | None]) -> tuple[float | None, str]:
    available = {key: value for key, value in components.items() if value is not None}
    if len(available) < 3:
        return None, "UNKNOWN_REVIEW"
    denominator = sum(WEIGHTS[key] for key in available)
    score = sum(available[key] * WEIGHTS[key] for key in available) / denominator
    return score, classify_score(score)


def build_report(snapshot_path: Path, event_path: Path | None, radar_rows: list[dict[str, str]], summary: dict[str, str]) -> str:
    high = [row for row in radar_rows if row["overall_options_risk_level"] == "HIGH"]
    extreme = [row for row in radar_rows if row["overall_options_risk_level"] == "EXTREME"]
    unknown = [row for row in radar_rows if row["overall_options_risk_level"] == "UNKNOWN_REVIEW"]
    liq = Counter(row["liquidity_risk_level"] for row in radar_rows)
    elevated_move = [row for row in radar_rows if row["expected_move_level"] in {"HIGH", "EXTREME"}]
    earnings = [row for row in radar_rows if row["earnings_options_risk_level"] in {"HIGH", "EXTREME"}]

    def table(rows: list[dict[str, str]], columns: list[str]) -> str:
        lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
        for row in rows:
            lines.append("| " + " | ".join(clean(row.get(column), "") for column in columns) + " |")
        return "\n".join(lines)

    sections = [
        f"# {PATCH_VERSION} Top20 Options Risk Radar Report",
        "",
        "V18.48B is a read-only options risk-reference layer based on V18.48A option snapshots.",
        "",
        "## Sources",
        table([
            {"metric": "OPTIONS_SNAPSHOT_SOURCE", "value": str(snapshot_path)},
            {"metric": "EVENT_RISK_SOURCE", "value": str(event_path) if event_path else "NONE"},
        ], ["metric", "value"]),
        "",
        "## Top20 options risk distribution",
        table([summary], ["ticker_count", "low_risk_count", "medium_risk_count", "high_risk_count", "extreme_risk_count", "unknown_review_count"]),
        "",
        "## HIGH options risk tickers",
        table(high, ["ticker", "rank", "overall_options_risk_score", "expected_move_level", "liquidity_risk_level", "options_risk_reason"]),
        "",
        "## EXTREME options risk tickers",
        table(extreme, ["ticker", "rank", "overall_options_risk_score", "expected_move_level", "liquidity_risk_level", "options_risk_reason"]),
        "",
        "## UNKNOWN_REVIEW tickers",
        table(unknown, ["ticker", "rank", "data_quality", "options_risk_reason"]),
        "",
        "## Liquidity risk distribution",
        table([{"liquidity_risk_level": key, "count": str(value)} for key, value in sorted(liq.items())], ["liquidity_risk_level", "count"]),
        "",
        "## Expected move observations",
        table(elevated_move, ["ticker", "expected_move_pct_near", "expected_move_pct_mid", "expected_move_pct_far", "expected_move_level"]),
        "",
        "## Earnings/options risk observations",
        table(earnings, ["ticker", "days_to_earnings", "earnings_options_risk_score", "earnings_options_risk_level"]),
        "",
        "## Safety statement",
        "V18.48B does not predict direction, earnings outcomes, or stock prices. It does not recommend options trades, calls, puts, or spreads. It does not change official ranking, factor weights, buy/sell permissions, final_action, event risk scoring, trading execution, broker behavior, order behavior, or signal freeze ledgers.",
        "",
        "## Suggested next step",
        "V18.49A Risk-Adjusted Ranking Layer or V18.49B Entry/Exit Plan Generator, depending on readiness.",
    ]
    return "\n".join(sections) + "\n"


def write_read_first(path: Path, values: dict[str, str]) -> None:
    order = [
        "STATUS", "PATCH_VERSION", "PATCH_NAME", "OPTIONS_SNAPSHOT_FOUND", "OPTIONS_SNAPSHOT_PATH",
        "OPTIONS_HISTORY_FOUND", "OPTIONS_HISTORY_PATH", "EVENT_RISK_SOURCE_FOUND", "EVENT_RISK_SOURCE_PATH",
        "TOP20_TOTAL_COUNT", "RADAR_ROW_COUNT", "DETAIL_ROW_COUNT", "LOW_OPTIONS_RISK_COUNT",
        "MEDIUM_OPTIONS_RISK_COUNT", "HIGH_OPTIONS_RISK_COUNT", "EXTREME_OPTIONS_RISK_COUNT",
        "UNKNOWN_OPTIONS_RISK_COUNT", "NORMAL_REVIEW_COUNT", "SMALL_SIZE_ONLY_REFERENCE_COUNT",
        "NO_CHASE_REFERENCE_COUNT", "NO_NEW_BUYS_REFERENCE_COUNT", "REDUCE_RISK_REVIEW_COUNT",
        "CURRENT_ALIAS_WRITTEN", "OFFICIAL_RANKING_CHANGED", "FACTOR_WEIGHTS_CHANGED",
        "OFFICIAL_BUY_PERMISSION_CHANGED", "OFFICIAL_SELL_PERMISSION_CHANGED",
        "OPTIONS_TRADE_RECOMMENDATION_CREATED", "OPTIONS_TRADE_EXECUTION_ALLOWED",
        "TRADING_EXECUTION_ALLOWED", "AUTO_TRADE", "AUTO_SELL", "BROKER_API_USED", "ORDER_EXECUTION_USED",
        "RADAR_PATH", "DETAIL_PATH", "SUMMARY_PATH", "CURRENT_REPORT_PATH", "VALIDATION_NOTES",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{key}: {values.get(key, '')}" for key in order) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build read-only V18.48B options risk radar from V18.48A snapshots.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write-current", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    options_dir = root / "outputs" / "v18" / "options"
    snapshot_path = options_dir / "V18_48A_TOP20_OPTIONS_SNAPSHOT.csv"
    history_path = options_dir / "V18_48A_TOP20_OPTIONS_HISTORY.csv"
    event_path, events = find_event_risk(root)
    top20_path, top20 = find_top20(root)
    _, tracker = find_tracker(root)

    snapshot_rows = read_csv(snapshot_path) if snapshot_path.exists() else []
    selected = selected_tickers(top20, snapshot_rows)
    snapshot_date = clean(snapshot_rows[0].get("snapshot_date"), datetime.now().date().isoformat()) if snapshot_rows else datetime.now().date().isoformat()
    by_ticker: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in snapshot_rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker:
            by_ticker[ticker].append(row)

    radar_rows: list[dict[str, str]] = []
    detail_rows: list[dict[str, str]] = []

    top20_by_ticker = {norm_ticker(row.get("ticker")): row for row in top20}
    for ticker in selected:
        rows = by_ticker.get(ticker, [])
        source = top20_by_ticker.get(ticker, {})
        event = events.get(ticker, {})
        rank = clean(source.get("rank") or source.get("freshness_eligible_rank") or (rows[0].get("rank") if rows else ""))
        tier = clean(tracker.get(ticker, {}).get("tracking_tier") or (rows[0].get("tracking_tier") if rows else ""))
        event_level = clean(event.get("final_event_risk_level") or event.get("earnings_risk_level") or (rows[0].get("event_risk_level") if rows else ""))
        days_raw = event.get("days_to_earnings") or (rows[0].get("days_to_earnings") if rows else "")
        days_to_earnings = parse_int(days_raw, -999999)
        days_value = days_to_earnings if days_to_earnings != -999999 else None
        underlying = first_float(rows, "underlying_price")

        selected_expirations = choose_bucket_expirations(rows)
        ticker_detail_rows = []
        for bucket, exp in selected_expirations.items():
            exp_rows = [row for row in rows if clean(row.get("expiration_date"), "") == exp]
            if exp_rows:
                detail = build_detail_row(snapshot_date, ticker, bucket, exp_rows)
                ticker_detail_rows.append(detail)
                detail_rows.append(detail)

        liq = Counter(clean(row.get("liquidity_status")) for row in rows)
        good, ok, thin, unusable = liq.get("GOOD", 0), liq.get("OK", 0), liq.get("THIN", 0), liq.get("UNUSABLE", 0)
        liq_score, liq_level = classify_liquidity(good, ok, thin, unusable, len(rows))

        iv_by_bucket = {}
        move_by_bucket = {}
        for detail in ticker_detail_rows:
            bucket = detail["dte_bucket"]
            atm_iv = average([parse_float(detail.get("atm_call_iv")), parse_float(detail.get("atm_put_iv"))])
            iv_by_bucket[bucket] = atm_iv
            move_by_bucket[bucket] = parse_float(detail.get("selected_expected_move_pct"))

        iv_basis = average([iv_by_bucket.get("NEAR"), iv_by_bucket.get("MID"), iv_by_bucket.get("FAR")])
        iv_score, iv_label = classify_iv(iv_basis)
        move_basis = average([move_by_bucket.get("NEAR"), move_by_bucket.get("MID"), move_by_bucket.get("FAR")])
        move_score, move_level = classify_expected_move(move_basis)
        skew_basis = average([parse_float(detail.get("put_call_iv_skew")) for detail in ticker_detail_rows])
        skew_score, skew_level = classify_skew(skew_basis)
        volume_ratio = average([parse_float(detail.get("put_call_volume_ratio")) for detail in ticker_detail_rows])
        oi_ratio = average([parse_float(detail.get("put_call_open_interest_ratio")) for detail in ticker_detail_rows])
        earnings_score, earnings_level = classify_earnings(days_value, move_level, liq_level)
        overall_score, overall_level = weighted_overall({
            "expected_move": move_score,
            "iv": iv_score,
            "skew": skew_score,
            "liquidity": liq_score,
            "earnings": earnings_score,
        })
        buy_ref, sell_ref = reference_for_level(overall_level)
        quality = data_quality(bool(rows), ticker_detail_rows, skew_score, liq_score)
        if overall_level == "UNKNOWN_REVIEW":
            quality = "UNKNOWN_REVIEW_REQUIRED" if quality == "PARTIAL" else quality
        reason_parts = [
            f"EXPECTED_MOVE={move_level}",
            f"IV={iv_label}",
            f"SKEW={skew_level}",
            f"LIQUIDITY={liq_level}",
            f"EARNINGS_OPTIONS={earnings_level}",
        ]
        radar_rows.append({
            "snapshot_date": snapshot_date,
            "snapshot_timestamp": timestamp,
            "ticker": ticker,
            "rank": rank,
            "tracking_tier": tier,
            "event_risk_level": event_level,
            "days_to_earnings": str(days_value) if days_value is not None else "UNKNOWN",
            "underlying_price": fmt_float(underlying),
            "options_snapshot_available": "TRUE" if rows else "FALSE",
            "options_contract_count": str(len(rows)),
            "good_liquidity_count": str(good),
            "ok_liquidity_count": str(ok),
            "thin_liquidity_count": str(thin),
            "unusable_liquidity_count": str(unusable),
            "liquidity_risk_score": fmt_score(liq_score),
            "liquidity_risk_level": liq_level,
            "atm_iv_near": fmt_float(iv_by_bucket.get("NEAR")),
            "atm_iv_mid": fmt_float(iv_by_bucket.get("MID")),
            "atm_iv_far": fmt_float(iv_by_bucket.get("FAR")),
            "iv_level_score": fmt_score(iv_score),
            "iv_level_label": iv_label,
            "expected_move_pct_near": fmt_float(move_by_bucket.get("NEAR")),
            "expected_move_pct_mid": fmt_float(move_by_bucket.get("MID")),
            "expected_move_pct_far": fmt_float(move_by_bucket.get("FAR")),
            "expected_move_score": fmt_score(move_score),
            "expected_move_level": move_level,
            "put_call_iv_skew_score": fmt_float(skew_basis),
            "put_call_volume_ratio": fmt_float(volume_ratio),
            "put_call_open_interest_ratio": fmt_float(oi_ratio),
            "skew_risk_score": fmt_score(skew_score),
            "skew_risk_level": skew_level,
            "earnings_options_risk_score": fmt_score(earnings_score),
            "earnings_options_risk_level": earnings_level,
            "overall_options_risk_score": fmt_score(overall_score),
            "overall_options_risk_level": overall_level,
            "buy_aggressiveness_reference": buy_ref,
            "sell_review_reference": sell_ref,
            "options_risk_reason": ";".join(reason_parts),
            "data_quality": quality,
            "notes": "Read-only options risk reference; no options trade recommendation, no order instruction, no ranking/weight/permission/trading changes.",
        })

    radar_rows.sort(key=lambda row: parse_int(row.get("rank"), 999999))
    detail_rows.sort(key=lambda row: (parse_int(next((r.get("rank") for r in radar_rows if r["ticker"] == row["ticker"]), "999999"), 999999), row["ticker"], parse_int(row.get("days_to_expiration"), 999999)))

    out_radar = options_dir / "V18_48B_TOP20_OPTIONS_RISK_RADAR.csv"
    out_detail = options_dir / "V18_48B_TOP20_OPTIONS_RISK_RADAR_DETAIL.csv"
    out_summary = options_dir / "V18_48B_TOP20_OPTIONS_RISK_SUMMARY.csv"
    report_path = root / "outputs" / "v18" / "read_center" / "V18_48B_TOP20_OPTIONS_RISK_RADAR_REPORT.md"
    current_path = root / "outputs" / "v18" / "read_center" / "V18_CURRENT_TOP20_OPTIONS_RISK_RADAR.md"
    read_first_path = root / "outputs" / "v18" / "ops" / "V18_48B_READ_FIRST.txt"

    risk = Counter(row["overall_options_risk_level"] for row in radar_rows)
    refs = Counter(row["buy_aggressiveness_reference"] for row in radar_rows)
    sell_refs = Counter(row["sell_review_reference"] for row in radar_rows)
    scores = [parse_float(row.get("overall_options_risk_score")) for row in radar_rows]
    numeric_scores = [score for score in scores if score is not None]
    total_liq = Counter()
    for row in radar_rows:
        total_liq["GOOD"] += parse_int(row.get("good_liquidity_count"))
        total_liq["OK"] += parse_int(row.get("ok_liquidity_count"))
        total_liq["THIN"] += parse_int(row.get("thin_liquidity_count"))
        total_liq["UNUSABLE"] += parse_int(row.get("unusable_liquidity_count"))

    summary = {
        "snapshot_date": snapshot_date,
        "ticker_count": str(len(radar_rows)),
        "low_risk_count": str(risk.get("LOW", 0)),
        "medium_risk_count": str(risk.get("MEDIUM", 0)),
        "high_risk_count": str(risk.get("HIGH", 0)),
        "extreme_risk_count": str(risk.get("EXTREME", 0)),
        "unknown_review_count": str(risk.get("UNKNOWN_REVIEW", 0)),
        "normal_review_count": str(refs.get("NORMAL_REVIEW", 0)),
        "small_size_reference_count": str(refs.get("SMALL_SIZE_ONLY_REFERENCE", 0)),
        "no_chase_reference_count": str(refs.get("NO_CHASE_REFERENCE", 0)),
        "no_new_buys_reference_count": str(refs.get("NO_NEW_BUYS_REFERENCE", 0)),
        "reduce_risk_review_count": str(sell_refs.get("REDUCE_RISK_REVIEW", 0)),
        "average_options_risk_score": fmt_score(sum(numeric_scores) / len(numeric_scores) if numeric_scores else None),
        "median_options_risk_score": fmt_score(statistics.median(numeric_scores) if numeric_scores else None),
        "good_liquidity_contract_count": str(total_liq.get("GOOD", 0)),
        "ok_liquidity_contract_count": str(total_liq.get("OK", 0)),
        "thin_liquidity_contract_count": str(total_liq.get("THIN", 0)),
        "unusable_liquidity_contract_count": str(total_liq.get("UNUSABLE", 0)),
    }

    write_csv(out_radar, radar_rows, RADAR_COLUMNS)
    write_csv(out_detail, detail_rows, DETAIL_COLUMNS)
    write_csv(out_summary, [summary], SUMMARY_COLUMNS)
    report = build_report(snapshot_path, event_path, radar_rows, summary)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    current_written = False
    if args.write_current and radar_rows:
        current_path.write_text(report, encoding="utf-8")
        current_written = True

    has_score = bool(numeric_scores)
    if not snapshot_path.exists():
        status = "WARN_V18_48B_OPTIONS_SNAPSHOT_MISSING"
    elif risk.get("UNKNOWN_REVIEW", 0) > 0 and has_score:
        status = "WARN_V18_48B_OPTIONS_RISK_PARTIAL_DATA"
    else:
        status = "PASS" if has_score else "WARN_V18_48B_OPTIONS_RISK_PARTIAL_DATA"

    values = {
        "STATUS": status,
        "PATCH_VERSION": PATCH_VERSION,
        "PATCH_NAME": PATCH_NAME,
        "OPTIONS_SNAPSHOT_FOUND": "TRUE" if snapshot_path.exists() else "FALSE",
        "OPTIONS_SNAPSHOT_PATH": str(snapshot_path),
        "OPTIONS_HISTORY_FOUND": "TRUE" if history_path.exists() else "FALSE",
        "OPTIONS_HISTORY_PATH": str(history_path),
        "EVENT_RISK_SOURCE_FOUND": "TRUE" if event_path else "FALSE",
        "EVENT_RISK_SOURCE_PATH": str(event_path) if event_path else "NONE",
        "TOP20_TOTAL_COUNT": str(len(selected)),
        "RADAR_ROW_COUNT": str(len(radar_rows)),
        "DETAIL_ROW_COUNT": str(len(detail_rows)),
        "LOW_OPTIONS_RISK_COUNT": str(risk.get("LOW", 0)),
        "MEDIUM_OPTIONS_RISK_COUNT": str(risk.get("MEDIUM", 0)),
        "HIGH_OPTIONS_RISK_COUNT": str(risk.get("HIGH", 0)),
        "EXTREME_OPTIONS_RISK_COUNT": str(risk.get("EXTREME", 0)),
        "UNKNOWN_OPTIONS_RISK_COUNT": str(risk.get("UNKNOWN_REVIEW", 0)),
        "NORMAL_REVIEW_COUNT": str(refs.get("NORMAL_REVIEW", 0)),
        "SMALL_SIZE_ONLY_REFERENCE_COUNT": str(refs.get("SMALL_SIZE_ONLY_REFERENCE", 0)),
        "NO_CHASE_REFERENCE_COUNT": str(refs.get("NO_CHASE_REFERENCE", 0)),
        "NO_NEW_BUYS_REFERENCE_COUNT": str(refs.get("NO_NEW_BUYS_REFERENCE", 0)),
        "REDUCE_RISK_REVIEW_COUNT": str(sell_refs.get("REDUCE_RISK_REVIEW", 0)),
        "CURRENT_ALIAS_WRITTEN": "TRUE" if current_written else "FALSE",
        "OFFICIAL_RANKING_CHANGED": "FALSE",
        "FACTOR_WEIGHTS_CHANGED": "FALSE",
        "OFFICIAL_BUY_PERMISSION_CHANGED": "FALSE",
        "OFFICIAL_SELL_PERMISSION_CHANGED": "FALSE",
        "OPTIONS_TRADE_RECOMMENDATION_CREATED": "FALSE",
        "OPTIONS_TRADE_EXECUTION_ALLOWED": "FALSE",
        "TRADING_EXECUTION_ALLOWED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "BROKER_API_USED": "FALSE",
        "ORDER_EXECUTION_USED": "FALSE",
        "RADAR_PATH": str(out_radar),
        "DETAIL_PATH": str(out_detail),
        "SUMMARY_PATH": str(out_summary),
        "CURRENT_REPORT_PATH": str(current_path),
        "VALIDATION_NOTES": "READ_ONLY_OPTIONS_RISK_REFERENCE_NO_OPTIONS_TRADES_NO_RANKING_WEIGHT_PERMISSION_FINAL_ACTION_EVENT_SCORING_TRADING_BROKER_ORDER_OR_SIGNAL_FREEZE_CHANGES",
    }
    write_read_first(read_first_path, values)

    print(f"STATUS: {status}")
    print(f"RADAR_ROW_COUNT: {len(radar_rows)}")
    print(f"DETAIL_ROW_COUNT: {len(detail_rows)}")
    print(f"HIGH_OPTIONS_RISK_COUNT: {risk.get('HIGH', 0)}")
    print(f"EXTREME_OPTIONS_RISK_COUNT: {risk.get('EXTREME', 0)}")
    print(f"UNKNOWN_OPTIONS_RISK_COUNT: {risk.get('UNKNOWN_REVIEW', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
