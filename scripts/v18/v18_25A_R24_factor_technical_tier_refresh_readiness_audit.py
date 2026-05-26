from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R24_REFRESH_READINESS_AUDIT_READY"
STATUS_TARGETS_MISSING = "WARN_V18_25A_R24_TARGET_INPUTS_MISSING"
STATUS_ZERO_TARGETS = "WARN_V18_25A_R24_ZERO_TARGETS"
STATUS_PRICE_LEDGER_GAP = "WARN_V18_25A_R24_PRICE_LEDGER_GAP_REVIEW_NEEDED"
STATUS_OPTIONAL_MISSING = "WARN_V18_25A_R24_OPTIONAL_INPUTS_MISSING"
STATUS_SCHEMA_PARTIAL = "WARN_V18_25A_R24_SCHEMA_PARTIAL"

MODE = "READ_ONLY_REFRESH_READINESS_AUDIT"

R23D_RESULT = "outputs/v18/price_integration/V18_25A_R23D_CURRENT_INTEGRATION_RESULT.csv"
R23E_LEDGER_RESULT = "outputs/v18/rolling_coverage/V18_25A_R23E_CURRENT_LEDGER_UPDATE_RESULT.csv"
R23E_COVERAGE = "outputs/v18/rolling_coverage/V18_25A_R23E_CURRENT_5DAY_COVERAGE_AFTER_UPDATE.csv"
PRICE_CACHE = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
FACTOR = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECHNICAL = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
R20_LEDGER_RESULT = "outputs/v18/rolling_coverage/V18_25A_R20_CURRENT_LEDGER_UPDATE_RESULT.csv"
PARTIAL_HOLDS = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_PARTIAL_HISTORY_HOLDS.csv"
EMPTY_HOLDS = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_EMPTY_OR_FAILED_HOLDS.csv"
RANKED_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"

OUT_TARGETS = "outputs/v18/readiness/V18_25A_R24_CURRENT_TARGETS.csv"
OUT_PRICE = "outputs/v18/readiness/V18_25A_R24_CURRENT_PRICE_LEDGER_READINESS.csv"
OUT_FACTOR = "outputs/v18/readiness/V18_25A_R24_CURRENT_FACTOR_READINESS.csv"
OUT_TECHNICAL = "outputs/v18/readiness/V18_25A_R24_CURRENT_TECHNICAL_READINESS.csv"
OUT_TIER = "outputs/v18/readiness/V18_25A_R24_CURRENT_TIER_READINESS.csv"
OUT_SUMMARY = "outputs/v18/readiness/V18_25A_R24_CURRENT_REFRESH_READINESS_SUMMARY.csv"
OUT_ACTION = "outputs/v18/readiness/V18_25A_R24_CURRENT_NEXT_ACTION_PLAN.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R24_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R24_CURRENT_REFRESH_READINESS_AUDIT_REPORT.md"

TARGET_FIELDS = ["ticker", "source_batch", "included", "exclusion_reason"]
PRICE_FIELDS = ["ticker", "official_price_cache_present", "local_price_cache_readable", "price_row_count", "min_price_date", "max_price_date", "latest_close", "rolling_ledger_present", "rolling_ledger_success_within_lookback", "rolling_ledger_last_success_date", "price_ledger_ready", "reason"]
FACTOR_FIELDS = ["ticker", "factor_pack_row_present", "factor_score_present", "factor_pack_rank_present", "factor_missing_reason", "factor_refresh_needed", "factor_ready"]
TECH_FIELDS = ["ticker", "technical_timing_row_present", "technical_timing_score_present", "technical_status_present", "technical_missing_reason", "technical_refresh_needed", "technical_ready"]
TIER_FIELDS = ["ticker", "tier_row_present", "current_tier", "trust_level", "ranking_allowed_status", "tier_missing_reason", "tier_refresh_needed", "tier_ready"]
SUMMARY_FIELDS = ["ticker", "source_batch", "price_ledger_ready", "factor_ready", "technical_ready", "tier_ready", "overall_classification", "next_actions"]
ACTION_FIELDS = ["action", "ticker_count", "tickers", "notes"]
AUDIT_FIELDS = ["metric", "value", "notes"]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "RUN_ID", "PRIMARY_R23_TARGET_COUNT", "INCLUDE_BATCH3_HISTORY", "TOTAL_TARGET_COUNT", "DEDUPED_TARGET_COUNT",
    "EXCLUDED_PARTIAL_HISTORY_COUNT", "EXCLUDED_EMPTY_OR_FAILED_COUNT", "PRICE_LEDGER_READY_COUNT", "PRICE_LEDGER_NOT_READY_COUNT",
    "FACTOR_ROW_PRESENT_COUNT", "FACTOR_ROW_MISSING_COUNT", "TECHNICAL_ROW_PRESENT_COUNT", "TECHNICAL_ROW_MISSING_COUNT",
    "TIER_ROW_PRESENT_COUNT", "TIER_ROW_MISSING_COUNT", "ALREADY_FULLY_READY_COUNT", "READY_FOR_FACTOR_BUILD_COUNT",
    "READY_FOR_TECHNICAL_REFRESH_COUNT", "READY_FOR_TIER_RECLASSIFICATION_COUNT", "READY_FOR_RANKING_RECHECK_COUNT",
    "HOLD_REVIEW_NEEDED_COUNT", "NEXT_ACTION_PLAN_PATH", "REFRESH_READINESS_SUMMARY_PATH", "PRICE_LEDGER_READINESS_PATH",
    "FACTOR_READINESS_PATH", "TECHNICAL_READINESS_PATH", "TIER_READINESS_PATH", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE",
    "AUTO_SELL", "EXTERNAL_FETCH_EXECUTED", "BACKTEST_EXECUTED", "PRICE_CACHE_MODIFIED", "ROLLING_LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "TIER_FILES_MODIFIED", "OFFICIAL_DECISION_MODIFIED",
    "VALIDATION_FAIL_COUNT", "FORBIDDEN_MODIFIED", "NEXT_RECOMMENDED_STEP",
]


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
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def norm_key(value: str) -> str:
    return "".join(ch for ch in str(value or "").strip().lower() if ch.isalnum())


def find_col(fields: Sequence[str], aliases: Sequence[str]) -> Optional[str]:
    by_norm = {norm_key(field): field for field in fields}
    for alias in aliases:
        hit = by_norm.get(norm_key(alias))
        if hit:
            return hit
    return None


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def parse_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        return float(text) if text else None
    except Exception:
        return None


def parse_date(value: object) -> Optional[dt.date]:
    text = str(value or "").strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    try:
        return dt.datetime.strptime(text[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def valid_symbol(ticker: str) -> bool:
    if ticker in {"", "TICKER", "TICKERS", "HEADER", "NULL", "NONE", "NAN", "SYMBOL"}:
        return False
    if any(ch in ticker for ch in '<>:"/\\|?*'):
        return False
    return bool(re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", ticker))


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def rows_by_ticker(rows: List[Dict[str, str]], fields: Sequence[str]) -> Dict[str, Dict[str, str]]:
    col = find_col(fields, ["ticker", "symbol", "yf_ticker"])
    out: Dict[str, Dict[str, str]] = {}
    if not col:
        return out
    for row in rows:
        ticker = norm_ticker(row.get(col))
        if ticker and ticker not in out:
            out[ticker] = row
    return out


def price_readiness(root: Path, ticker: str, ledger_row: Optional[Dict[str, str]], ledger_fields: Sequence[str], today: dt.date) -> Dict[str, object]:
    path = root / PRICE_CACHE / f"{ticker}.csv"
    rows, fields = read_csv(path)
    dates = [parse_date(row.get("date")) for row in rows]
    dates = [d for d in dates if d]
    latest_close = ""
    if rows:
        latest = sorted(rows, key=lambda r: str(r.get("date", "")))[-1]
        latest_close = str(latest.get("close", "") or "")
    success_col = find_col(ledger_fields, ["last_success_scan_date", "last_success_date", "latest_success_date"])
    last_success = parse_date(ledger_row.get(success_col)) if ledger_row and success_col else None
    window_start = today - dt.timedelta(days=4)
    ledger_within = bool(last_success and window_start <= last_success <= today)
    required = {"date", "open", "high", "low", "close", "volume"}
    ok = path.exists() and bool(fields) and bool(rows) and bool(dates) and parse_float(latest_close) is not None and parse_float(latest_close) > 0 and bool(ledger_row) and ledger_within and required.issubset({f.lower() for f in fields})
    return {
        "ticker": ticker,
        "official_price_cache_present": str(path.exists()).upper(),
        "local_price_cache_readable": str(bool(fields)).upper(),
        "price_row_count": len(rows),
        "min_price_date": min(dates).isoformat() if dates else "",
        "max_price_date": max(dates).isoformat() if dates else "",
        "latest_close": latest_close,
        "rolling_ledger_present": str(bool(ledger_row)).upper(),
        "rolling_ledger_success_within_lookback": str(ledger_within).upper(),
        "rolling_ledger_last_success_date": last_success.isoformat() if last_success else "",
        "price_ledger_ready": str(ok).upper(),
        "reason": "" if ok else "Price cache or rolling ledger lookback success is not ready.",
    }


def present(value: object) -> bool:
    return str(value or "").strip() != ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--include-batch3-history", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-tickers", type=int, default=200)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R24_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    before = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": tree_sig(root / "outputs" / "v18" / "factor_pack"),
        "technical": tree_sig(root / "outputs" / "v18" / "technical_timing"),
        "tier": tree_sig(root / "outputs" / "v18" / "tier_migration"),
        "decision": tree_sig(root / "outputs" / "v18" / "daily_decision"),
    }

    r23d, _ = read_csv(root / R23D_RESULT)
    r23e, _ = read_csv(root / R23E_LEDGER_RESULT)
    ledger_rows, ledger_fields = read_csv(root / LEDGER)
    factor_rows, factor_fields = read_csv(root / FACTOR)
    tech_rows, tech_fields = read_csv(root / TECHNICAL)
    tier_rows, tier_fields = read_csv(root / "outputs/v18/tier_migration/V18_24A_CURRENT_SCORE_TIER_SNAPSHOT.csv")
    if not tier_rows:
        tier_rows, tier_fields = read_csv(root / "outputs/v18/tier_migration/V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT.csv")
    partial_rows, _ = read_csv(root / PARTIAL_HOLDS)
    empty_rows, _ = read_csv(root / EMPTY_HOLDS)
    r20_rows, _ = read_csv(root / R20_LEDGER_RESULT)
    ranked_rows, ranked_fields = read_csv(root / RANKED_CANDIDATES)

    status = STATUS_OK
    validation_fail_count = 0
    if not r23d or not r23e:
        status = STATUS_TARGETS_MISSING
        validation_fail_count = 1

    r23_success = {norm_ticker(row.get("ticker")) for row in r23d if is_true(row.get("integration_success"))}
    r23_ledger = {norm_ticker(row.get("ticker")) for row in r23e if is_true(row.get("ledger_update_success"))}
    primary = sorted(t for t in (r23_success & r23_ledger) if valid_symbol(t))
    batch3 = set()
    optional_missing = []
    if args.include_batch3_history:
        if r20_rows:
            batch3 = {norm_ticker(row.get("ticker")) for row in r20_rows if is_true(row.get("ledger_update_success")) or str(row.get("scan_result", "")).upper().startswith("SUCCESS")}
            batch3 = {t for t in batch3 if valid_symbol(t)}
        else:
            optional_missing.append(R20_LEDGER_RESULT)

    excluded_partial = {norm_ticker(row.get("ticker")) for row in partial_rows}
    excluded_empty = {norm_ticker(row.get("ticker")) for row in empty_rows}
    combined: Dict[str, set[str]] = {}
    for ticker in primary:
        combined.setdefault(ticker, set()).add("R23D_R23E")
    for ticker in batch3:
        combined.setdefault(ticker, set()).add("R19_R20")

    target_rows = []
    targets = []
    for ticker in sorted(combined):
        reason = ""
        included = True
        if ticker in excluded_partial:
            included = False
            reason = "Excluded by R23C partial-history hold."
        elif ticker in excluded_empty:
            included = False
            reason = "Excluded by R23C empty/failed hold."
        elif not valid_symbol(ticker):
            included = False
            reason = "Invalid or artifact ticker."
        if included and len(targets) < max(args.max_tickers, 0):
            targets.append(ticker)
        elif included:
            included = False
            reason = "Beyond MaxTickers limit."
        target_rows.append({"ticker": ticker, "source_batch": "BOTH" if len(combined[ticker]) > 1 else next(iter(combined[ticker])), "included": str(included).upper(), "exclusion_reason": reason})

    if status == STATUS_OK and not targets:
        status = STATUS_ZERO_TARGETS
        validation_fail_count = 1
    if status == STATUS_OK and optional_missing:
        status = STATUS_OPTIONAL_MISSING
    if status == STATUS_OK and (not factor_rows or not tech_rows or not ledger_rows):
        status = STATUS_SCHEMA_PARTIAL

    ledger_by = rows_by_ticker(ledger_rows, ledger_fields)
    factor_by = rows_by_ticker(factor_rows, factor_fields)
    tech_by = rows_by_ticker(tech_rows, tech_fields)
    tier_by = rows_by_ticker(tier_rows, tier_fields)
    ranked_by = rows_by_ticker(ranked_rows, ranked_fields)
    today = dt.date.today()

    price_out = []
    factor_out = []
    tech_out = []
    tier_out = []
    summary = []
    action_map: Dict[str, List[str]] = {k: [] for k in ["BUILD_FACTOR_ROWS", "REFRESH_TECHNICAL_TIMING", "REFRESH_TIER_CLASSIFICATION", "RANKING_RECHECK", "HOLD_PARTIAL_HISTORY", "HOLD_EMPTY_OR_FAILED", "HOLD_REVIEW_NEEDED", "NO_ACTION_ALREADY_READY"]}

    for ticker in targets:
        price = price_readiness(root, ticker, ledger_by.get(ticker), ledger_fields, today)
        price_ready = price["price_ledger_ready"] == "TRUE"
        price_out.append(price)

        f = factor_by.get(ticker)
        factor_score_col = find_col(factor_fields, ["factor_pack_score", "score", "current_score"])
        factor_rank_col = find_col(factor_fields, ["factor_pack_rank", "rank", "current_rank"])
        factor_score = present(f.get(factor_score_col)) if f and factor_score_col else False
        factor_rank = present(f.get(factor_rank_col)) if f and factor_rank_col else False
        factor_ready = bool(f and factor_score and factor_rank)
        factor_out.append({"ticker": ticker, "factor_pack_row_present": str(bool(f)).upper(), "factor_score_present": str(factor_score).upper(), "factor_pack_rank_present": str(factor_rank).upper(), "factor_missing_reason": "" if factor_ready else "Missing current factor row/score/rank.", "factor_refresh_needed": str(price_ready and not factor_ready).upper(), "factor_ready": str(factor_ready).upper()})

        tr = tech_by.get(ticker)
        tech_score_col = find_col(tech_fields, ["technical_timing_score", "score"])
        tech_status_col = find_col(tech_fields, ["technical_signal", "technical_status", "bb_status"])
        tech_score = present(tr.get(tech_score_col)) if tr and tech_score_col else False
        tech_status = present(tr.get(tech_status_col)) if tr and tech_status_col else False
        tech_ready = bool(tr and tech_score and tech_status)
        tech_out.append({"ticker": ticker, "technical_timing_row_present": str(bool(tr)).upper(), "technical_timing_score_present": str(tech_score).upper(), "technical_status_present": str(tech_status).upper(), "technical_missing_reason": "" if tech_ready else "Missing current technical row/score/status.", "technical_refresh_needed": str(price_ready and not tech_ready).upper(), "technical_ready": str(tech_ready).upper()})

        tier = tier_by.get(ticker)
        tier_col = find_col(tier_fields, ["current_tier", "tier_current"])
        trust_col = find_col(tier_fields, ["trust_level", "score_source_trust"])
        current_tier = str(tier.get(tier_col, "") if tier and tier_col else "")
        trust = str(tier.get(trust_col, "") if tier and trust_col else "")
        ranked = ticker in ranked_by
        tier_ready = bool(tier and current_tier and "DATA_NOT_READY" not in current_tier)
        tier_out.append({"ticker": ticker, "tier_row_present": str(bool(tier)).upper(), "current_tier": current_tier, "trust_level": trust, "ranking_allowed_status": "RANKED_CURRENTLY" if ranked else "NOT_IN_CURRENT_RANKING", "tier_missing_reason": "" if tier_ready else "Missing or data-not-ready tier row.", "tier_refresh_needed": str(price_ready and (factor_ready or tech_ready) and not tier_ready).upper(), "tier_ready": str(tier_ready).upper()})

        actions = []
        if not price_ready:
            overall = "HOLD_PRICE_LEDGER_NOT_READY"
            actions.append("HOLD_REVIEW_NEEDED")
        elif not factor_ready:
            overall = "READY_FOR_FACTOR_BUILD"
            actions.append("BUILD_FACTOR_ROWS")
        elif not tech_ready:
            overall = "READY_FOR_TECHNICAL_REFRESH"
            actions.append("REFRESH_TECHNICAL_TIMING")
        elif not tier_ready:
            overall = "READY_FOR_TIER_RECLASSIFICATION"
            actions.append("REFRESH_TIER_CLASSIFICATION")
        elif not ranked:
            overall = "READY_FOR_RANKING_IF_FACTOR_AND_TECHNICAL_READY"
            actions.append("RANKING_RECHECK")
        else:
            overall = "ALREADY_FULLY_READY"
            actions.append("NO_ACTION_ALREADY_READY")
        for action in actions:
            action_map[action].append(ticker)
        summary.append({"ticker": ticker, "source_batch": "BOTH" if len(combined[ticker]) > 1 else next(iter(combined[ticker])), "price_ledger_ready": str(price_ready).upper(), "factor_ready": str(factor_ready).upper(), "technical_ready": str(tech_ready).upper(), "tier_ready": str(tier_ready).upper(), "overall_classification": overall, "next_actions": ";".join(actions)})

    if status == STATUS_OK and any(row["price_ledger_ready"] != "TRUE" for row in price_out):
        status = STATUS_PRICE_LEDGER_GAP

    action_rows = [{"action": action, "ticker_count": len(tickers), "tickers": ",".join(tickers), "notes": ""} for action, tickers in action_map.items()]
    write_csv(root / OUT_TARGETS, target_rows, TARGET_FIELDS)
    write_csv(root / OUT_PRICE, price_out, PRICE_FIELDS)
    write_csv(root / OUT_FACTOR, factor_out, FACTOR_FIELDS)
    write_csv(root / OUT_TECHNICAL, tech_out, TECH_FIELDS)
    write_csv(root / OUT_TIER, tier_out, TIER_FIELDS)
    write_csv(root / OUT_SUMMARY, summary, SUMMARY_FIELDS)
    write_csv(root / OUT_ACTION, action_rows, ACTION_FIELDS)

    after = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": tree_sig(root / "outputs" / "v18" / "factor_pack"),
        "technical": tree_sig(root / "outputs" / "v18" / "technical_timing"),
        "tier": tree_sig(root / "outputs" / "v18" / "tier_migration"),
        "decision": tree_sig(root / "outputs" / "v18" / "daily_decision"),
    }
    mods = {k: before[k] != after[k] for k in before}
    forbidden = any(mods.values())

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "PRIMARY_R23_TARGET_COUNT": len(primary),
        "INCLUDE_BATCH3_HISTORY": str(args.include_batch3_history).upper(),
        "TOTAL_TARGET_COUNT": len(primary) + len(batch3),
        "DEDUPED_TARGET_COUNT": len(targets),
        "EXCLUDED_PARTIAL_HISTORY_COUNT": len([r for r in target_rows if "partial" in str(r["exclusion_reason"]).lower()]),
        "EXCLUDED_EMPTY_OR_FAILED_COUNT": len([r for r in target_rows if "empty" in str(r["exclusion_reason"]).lower() or "failed" in str(r["exclusion_reason"]).lower()]),
        "PRICE_LEDGER_READY_COUNT": sum(1 for r in price_out if r["price_ledger_ready"] == "TRUE"),
        "PRICE_LEDGER_NOT_READY_COUNT": sum(1 for r in price_out if r["price_ledger_ready"] != "TRUE"),
        "FACTOR_ROW_PRESENT_COUNT": sum(1 for r in factor_out if r["factor_pack_row_present"] == "TRUE"),
        "FACTOR_ROW_MISSING_COUNT": sum(1 for r in factor_out if r["factor_pack_row_present"] != "TRUE"),
        "TECHNICAL_ROW_PRESENT_COUNT": sum(1 for r in tech_out if r["technical_timing_row_present"] == "TRUE"),
        "TECHNICAL_ROW_MISSING_COUNT": sum(1 for r in tech_out if r["technical_timing_row_present"] != "TRUE"),
        "TIER_ROW_PRESENT_COUNT": sum(1 for r in tier_out if r["tier_row_present"] == "TRUE"),
        "TIER_ROW_MISSING_COUNT": sum(1 for r in tier_out if r["tier_row_present"] != "TRUE"),
        "ALREADY_FULLY_READY_COUNT": sum(1 for r in summary if r["overall_classification"] == "ALREADY_FULLY_READY"),
        "READY_FOR_FACTOR_BUILD_COUNT": len(action_map["BUILD_FACTOR_ROWS"]),
        "READY_FOR_TECHNICAL_REFRESH_COUNT": len(action_map["REFRESH_TECHNICAL_TIMING"]),
        "READY_FOR_TIER_RECLASSIFICATION_COUNT": len(action_map["REFRESH_TIER_CLASSIFICATION"]),
        "READY_FOR_RANKING_RECHECK_COUNT": len(action_map["RANKING_RECHECK"]),
        "HOLD_REVIEW_NEEDED_COUNT": len(action_map["HOLD_REVIEW_NEEDED"]),
        "NEXT_ACTION_PLAN_PATH": OUT_ACTION,
        "REFRESH_READINESS_SUMMARY_PATH": OUT_SUMMARY,
        "PRICE_LEDGER_READINESS_PATH": OUT_PRICE,
        "FACTOR_READINESS_PATH": OUT_FACTOR,
        "TECHNICAL_READINESS_PATH": OUT_TECHNICAL,
        "TIER_READINESS_PATH": OUT_TIER,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "PRICE_CACHE_MODIFIED": str(mods["price"]).upper(),
        "ROLLING_LEDGER_MODIFIED": str(mods["ledger"]).upper(),
        "FACTOR_PACK_MODIFIED": str(mods["factor"]).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(mods["technical"]).upper(),
        "TIER_FILES_MODIFIED": str(mods["tier"]).upper(),
        "OFFICIAL_DECISION_MODIFIED": str(mods["decision"]).upper(),
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden).upper(),
        "NEXT_RECOMMENDED_STEP": "R25: Build or stage missing factor and technical refresh plan for readiness-approved tickers only.",
    }
    write_text(root / OUT_READ_FIRST, "\n".join(f"{f}: {values.get(f, '')}" for f in READ_FIRST_FIELDS) + "\n")
    report = "\n".join([
        "# V18.25A R24 Refresh Readiness Audit Report",
        "",
        f"STATUS: {status}",
        f"MODE: {MODE}",
        f"RUN_ID: {run_id}",
        "",
        "## Summary",
        f"- primary_r23_target_count: {values['PRIMARY_R23_TARGET_COUNT']}",
        f"- deduped_target_count: {values['DEDUPED_TARGET_COUNT']}",
        f"- price_ledger_ready_count: {values['PRICE_LEDGER_READY_COUNT']}",
        f"- ready_for_factor_build_count: {values['READY_FOR_FACTOR_BUILD_COUNT']}",
        f"- ready_for_technical_refresh_count: {values['READY_FOR_TECHNICAL_REFRESH_COUNT']}",
        f"- ready_for_tier_reclassification_count: {values['READY_FOR_TIER_RECLASSIFICATION_COUNT']}",
        "",
        "## Safety",
        "- external_fetch_executed: FALSE",
        "- protected state modified: FALSE",
        "",
    ])
    write_text(root / OUT_REPORT, report)
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
