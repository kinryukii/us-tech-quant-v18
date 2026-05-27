from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_29A_BACKTEST_READINESS_READY"
STATUS_WARN = "WARN_V18_29A_BACKTEST_READINESS_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_29A_BACKTEST_READINESS_ERROR"
MODE = "READ_ONLY_HISTORICAL_BACKTEST_READINESS_AUDIT"

CURRENT_RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
THEME_CLASSIFICATION = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
TECHNICAL_TIMING = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
SIGNAL_FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"

OUT_AUDIT = "outputs/v18/backtest/V18_29A_BACKTEST_READINESS_AUDIT.csv"
OUT_REPORT = "outputs/v18/read_center/V18_29A_BACKTEST_READINESS_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_29A_READ_FIRST.txt"

EXPECTED_CURRENT_ROWS = 252
HORIZONS = [1, 3, 5, 10, 20]

PROTECTED_FILES = [
    CURRENT_RECOMMENDATIONS,
    CURRENT_CANDIDATES,
    THEME_CLASSIFICATION,
    "state/v18/reference/V18_TICKER_THEME_MAP.csv",
    TECHNICAL_TIMING,
    SIGNAL_FREEZE_LEDGER,
    "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv",
]
PROTECTED_DIRS = [
    "state/v18/price_cache",
    "outputs/v18/factor_pack",
    "outputs/v18/technical_timing",
    "state/v18/trading",
    "outputs/v18/official_daily",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "CURRENT_RECOMMENDATION_ROW_COUNT",
    "CURRENT_RANKED_CANDIDATE_ROW_COUNT",
    "THEME_CLASSIFICATION_ROW_COUNT",
    "TECHNICAL_TIMING_AVAILABLE",
    "TECHNICAL_TIMING_MATCHED_COUNT",
    "SIGNAL_FREEZE_LEDGER_AVAILABLE",
    "LATEST_SIGNAL_FREEZE_RUN_ID",
    "LATEST_SIGNAL_FREEZE_DATE",
    "LATEST_SIGNAL_FREEZE_TICKER_COUNT",
    "LATEST_SIGNAL_FREEZE_MATCHES_CURRENT_RECOMMENDATIONS",
    "PRICE_CACHE_CANDIDATE_COVERAGE_COUNT",
    "LATEST_PRICE_DATE_MIN",
    "LATEST_PRICE_DATE_MAX",
    "FORWARD_1D_FILLABLE_COUNT",
    "FORWARD_3D_FILLABLE_COUNT",
    "FORWARD_5D_FILLABLE_COUNT",
    "FORWARD_10D_FILLABLE_COUNT",
    "FORWARD_20D_FILLABLE_COUNT",
    "HISTORICAL_SIGNAL_FREEZE_RUN_COUNT",
    "HISTORICAL_RECOMMENDATION_TIER_SNAPSHOT_COUNT",
    "SURVIVORSHIP_BIAS_RISK",
    "LOOKAHEAD_BIAS_RISK",
    "DATE_ALIGNMENT_RISK",
    "ETF_MACRO_CONTAMINATION_RISK",
    "TRANSACTION_COST_MODEL_READY",
    "R29B_SCOPE_RECOMMENDATION",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "FORBIDDEN_MODIFIED",
]

AUDIT_FIELDS = [
    "audit_category",
    "check_name",
    "status",
    "value",
    "expected_or_threshold",
    "severity",
    "audit_comment",
]


def norm(value: object) -> str:
    return str(value or "").strip()


def norm_ticker(value: object) -> str:
    return norm(value).upper()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def to_float(value: object) -> Optional[float]:
    try:
        text = norm(value)
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def parse_date(value: object) -> Optional[dt.date]:
    text = norm(value)
    if not text:
        return None
    text = text.replace("/", "-")
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%m-%d-%Y", "%Y%m%d"):
        try:
            return dt.datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def parse_dt(value: object) -> dt.datetime:
    text = norm(value)
    if not text:
        return dt.datetime.min
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        parsed_date = parse_date(text)
        if parsed_date:
            return dt.datetime.combine(parsed_date, dt.time.min)
    return dt.datetime.min


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_sig(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return "MISSING"
    stat = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"{stat.st_size}:{stat.st_mtime_ns}:{digest.hexdigest()}"


def dir_sig(path: Path) -> str:
    if not path.exists() or not path.is_dir():
        return "MISSING"
    parts: List[str] = []
    for child in sorted(path.rglob("*")):
        if child.is_file():
            rel = child.relative_to(path).as_posix()
            stat = child.stat()
            parts.append(f"{rel}:{stat.st_size}:{stat.st_mtime_ns}")
    return "|".join(parts)


def protected_sig(root: Path) -> Dict[str, str]:
    sig: Dict[str, str] = {}
    for rel in PROTECTED_FILES:
        sig[f"file:{rel}"] = file_sig(root / rel)
    for rel in PROTECTED_DIRS:
        sig[f"dir:{rel}"] = dir_sig(root / rel)
    return sig


def ticker_counts(rows: Sequence[Dict[str, str]]) -> Counter:
    return Counter(norm_ticker(row.get("ticker")) for row in rows if norm_ticker(row.get("ticker")))


def duplicate_count(rows: Sequence[Dict[str, str]]) -> int:
    counts = ticker_counts(rows)
    return sum(1 for count in counts.values() if count > 1)


def numeric_parse_count(rows: Sequence[Dict[str, str]], column: str) -> int:
    return sum(1 for row in rows if to_float(row.get(column)) is not None)


def add_audit(
    rows: List[Dict[str, object]],
    category: str,
    check: str,
    status: str,
    value: object,
    expected: object,
    severity: str,
    comment: str,
) -> None:
    rows.append(
        {
            "audit_category": category,
            "check_name": check,
            "status": status,
            "value": value,
            "expected_or_threshold": expected,
            "severity": severity,
            "audit_comment": comment,
        }
    )


def read_price_dates(path: Path) -> List[dt.date]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return []
            lower = {field.lower().strip(): field for field in reader.fieldnames}
            date_col = lower.get("date") or lower.get("price_date") or lower.get("timestamp")
            close_col = lower.get("close") or lower.get("adj_close") or lower.get("adj close")
            if not date_col or not close_col:
                return []
            dates: List[dt.date] = []
            for row in reader:
                parsed = parse_date(row.get(date_col))
                close = to_float(row.get(close_col))
                if parsed and close is not None:
                    dates.append(parsed)
            return sorted(set(dates))
    except Exception:
        return []


def price_file_for_ticker(root: Path, ticker: str) -> Optional[Path]:
    candidates = [
        root / "state/v18/price_cache" / f"{ticker}.csv",
        root / "outputs/v18/price_cache" / f"{ticker}.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def latest_freeze_group(ledger: Sequence[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in ledger:
        grouped[norm(row.get("run_id"))].append(row)
    if not grouped:
        return "", []

    def sort_key(item: Tuple[str, List[Dict[str, str]]]) -> Tuple[dt.datetime, dt.date, str]:
        run_id, rows = item
        latest_ts = max((parse_dt(row.get("run_timestamp")) for row in rows), default=dt.datetime.min)
        latest_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in rows), default=dt.date.min)
        return latest_ts, latest_date, run_id

    run_id, rows = max(grouped.items(), key=sort_key)
    return run_id, rows


def count_historical_recommendation_snapshots(root: Path) -> int:
    rec_dir = root / "outputs/v18/recommendations"
    if not rec_dir.exists():
        return 0
    count = 0
    for path in rec_dir.rglob("*.csv"):
        name = path.name.upper()
        if name == "V18_CURRENT_RECOMMENDATION_TIERS.CSV":
            continue
        if "RECOMMENDATION_TIERS" in name and "CURRENT" not in name:
            count += 1
    return count


def count_candidate_snapshots(root: Path) -> int:
    cand_dir = root / "outputs/v18/candidates"
    if not cand_dir.exists():
        return 0
    return sum(1 for path in cand_dir.glob("*.csv") if "RANKED_CANDIDATES" in path.name.upper() and "CURRENT" not in path.name.upper())


def cost_model_ready(root: Path) -> bool:
    patterns = ["*TRANSACTION*COST*.csv", "*SLIPPAGE*.csv", "*COMMISSION*.csv"]
    for base in [root / "state/v18", root / "outputs/v18"]:
        if base.exists():
            for pattern in patterns:
                if any(base.rglob(pattern)):
                    return True
    return False


def tier_count_text(tier_counts: Counter) -> str:
    labels = [
        "CORE_CANDIDATE",
        "WATCHLIST_STRONG",
        "TACTICAL_ENTRY",
        "OVERHEATED_WAIT",
        "SPECULATIVE_SATELLITE",
        "DEFENSIVE_HEDGE",
        "ETF_OR_MACRO_EXPOSURE",
        "DO_NOT_PRIORITIZE",
    ]
    return "; ".join(f"{label}={tier_counts.get(label, 0)}" for label in labels)


def markdown_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: Optional[int] = None) -> str:
    selected = list(rows[:limit] if limit is not None else rows)
    if not selected:
        return "_None._\n"
    header = "| " + " | ".join(fields) + " |"
    sep = "| " + " | ".join(["---"] * len(fields)) + " |"
    lines = [header, sep]
    for row in selected:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    lines = [f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS]
    write_text(path, "\n".join(lines) + "\n")


def build_report(values: Dict[str, object], audit_rows: Sequence[Dict[str, object]]) -> str:
    def rows_for(category: str) -> List[Dict[str, object]]:
        return [row for row in audit_rows if row.get("audit_category") == category]

    top_rows = list(audit_rows[:20])
    report = [
        "# V18.29A Historical Backtest Readiness Audit",
        "",
        "## Read First",
        "```text",
        "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS),
        "```",
        "",
        "## Current Recommendation Tier Readiness",
        markdown_table(rows_for("recommendation_tier_file"), AUDIT_FIELDS),
        "## Ranked Candidate Readiness",
        markdown_table(rows_for("ranked_candidates"), AUDIT_FIELDS),
        "## Theme Classification Readiness",
        markdown_table(rows_for("theme_classification"), AUDIT_FIELDS),
        "## Technical Timing Readiness",
        markdown_table(rows_for("technical_timing"), AUDIT_FIELDS),
        "## Signal Freeze Ledger Readiness",
        markdown_table(rows_for("signal_freeze_ledger"), AUDIT_FIELDS),
        "## Price Cache / Forward Return Availability",
        markdown_table(rows_for("price_cache"), AUDIT_FIELDS),
        "## Bias and Data-Leakage Risk Review",
        markdown_table(
            rows_for("survivorship_bias")
            + rows_for("lookahead_bias")
            + rows_for("date_alignment")
            + rows_for("etf_macro_contamination")
            + rows_for("transaction_cost_model"),
            AUDIT_FIELDS,
        ),
        "## R29B Scope Recommendation",
        f"**R29B_SCOPE_RECOMMENDATION:** {values.get('R29B_SCOPE_RECOMMENDATION')}",
        "",
        markdown_table(rows_for("r29b_scope_recommendation"), AUDIT_FIELDS),
        "## Explicit Next-Step Recommendation",
        "- Use R29B for latest-freeze forward validation only when future price bars become available, or for a limited historical signal-freeze backtest using frozen rank/score fields.",
        "- Do not claim a full historical recommendation-tier backtest until recommendation-tier snapshots are generated per historical freeze date.",
        "- Keep ETF/macro exposures separate from single-stock performance summaries.",
        "",
        "## Audit Row Preview",
        markdown_table(top_rows, AUDIT_FIELDS),
    ]
    return "\n".join(report) + "\n"


def run(root: Path) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("V18_29A_%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)
    audit_rows: List[Dict[str, object]] = []

    recs = read_csv(root / CURRENT_RECOMMENDATIONS)
    candidates = read_csv(root / CURRENT_CANDIDATES)
    themes = read_csv(root / THEME_CLASSIFICATION)

    rec_tickers = {norm_ticker(row.get("ticker")) for row in recs if norm_ticker(row.get("ticker"))}
    candidate_tickers = {norm_ticker(row.get("ticker")) for row in candidates if norm_ticker(row.get("ticker"))}
    theme_tickers = {norm_ticker(row.get("ticker")) for row in themes if norm_ticker(row.get("ticker"))}

    rec_dup = duplicate_count(recs)
    cand_dup = duplicate_count(candidates)
    theme_dup = duplicate_count(themes)
    missing_tier = sum(1 for row in recs if not norm(row.get("recommendation_tier")))
    missing_action = sum(1 for row in recs if not norm(row.get("recommendation_action")))
    unknown_theme = sum(1 for row in recs if norm(row.get("primary_theme")).upper() in {"", "UNKNOWN"})
    tier_counts = Counter(norm(row.get("recommendation_tier")) for row in recs if norm(row.get("recommendation_tier")))

    add_audit(audit_rows, "recommendation_tier_file", "row_count", "PASS" if len(recs) == EXPECTED_CURRENT_ROWS else "FAIL", len(recs), EXPECTED_CURRENT_ROWS, "CRITICAL", "Current recommendation tier output must preserve the current candidate universe.")
    add_audit(audit_rows, "recommendation_tier_file", "duplicate_tickers", "PASS" if rec_dup == 0 else "FAIL", rec_dup, 0, "CRITICAL", "Duplicate recommendation tickers would make joins unsafe.")
    add_audit(audit_rows, "recommendation_tier_file", "missing_recommendation_tier", "PASS" if missing_tier == 0 else "FAIL", missing_tier, 0, "CRITICAL", "Every row needs a tier before any backtest grouping.")
    add_audit(audit_rows, "recommendation_tier_file", "missing_recommendation_action", "PASS" if missing_action == 0 else "FAIL", missing_action, 0, "CRITICAL", "Every row needs an operator action label.")
    add_audit(audit_rows, "recommendation_tier_file", "unknown_primary_theme", "PASS" if unknown_theme == 0 else "FAIL", unknown_theme, 0, "CRITICAL", "Unknown themes would contaminate tier/theme attribution.")
    add_audit(audit_rows, "recommendation_tier_file", "tier_counts", "PASS", tier_count_text(tier_counts), "non-empty controlled tiers", "INFO", "Current calibrated tier distribution.")

    rank_present = bool(candidates and "rank" in candidates[0])
    score_present = bool(candidates and "composite_candidate_score" in candidates[0])
    score_numeric = numeric_parse_count(candidates, "composite_candidate_score")
    add_audit(audit_rows, "ranked_candidates", "row_count", "PASS" if len(candidates) == EXPECTED_CURRENT_ROWS else "FAIL", len(candidates), EXPECTED_CURRENT_ROWS, "CRITICAL", "Ranked candidates are the current universe anchor.")
    add_audit(audit_rows, "ranked_candidates", "duplicate_tickers", "PASS" if cand_dup == 0 else "FAIL", cand_dup, 0, "CRITICAL", "Duplicate ranked tickers would invalidate set comparisons.")
    add_audit(audit_rows, "ranked_candidates", "rank_column_present", "PASS" if rank_present else "FAIL", bool_text(rank_present), "TRUE", "CRITICAL", "Rank is required for rank-bucket backtests.")
    add_audit(audit_rows, "ranked_candidates", "composite_candidate_score_present", "PASS" if score_present else "FAIL", bool_text(score_present), "TRUE", "CRITICAL", "Composite score is required for score-bucket tests.")
    add_audit(audit_rows, "ranked_candidates", "score_numeric_parse_success", "PASS" if score_numeric == len(candidates) else "FAIL", score_numeric, len(candidates), "CRITICAL", "All current candidate scores should parse numerically.")

    theme_unknown = sum(1 for row in themes if norm(row.get("primary_theme")).upper() in {"", "UNKNOWN"})
    missing_theme_rank = sum(1 for row in themes if not norm(row.get("theme_rank")))
    etf_macro = sum(
        1
        for row in themes
        if norm(row.get("industry_group")).upper() == "ETF"
        or norm(row.get("primary_theme")).upper() == "OTHER" and "ETF" in norm(row.get("secondary_theme")).upper()
    )
    add_audit(audit_rows, "theme_classification", "row_count", "PASS" if len(themes) == EXPECTED_CURRENT_ROWS else "FAIL", len(themes), EXPECTED_CURRENT_ROWS, "CRITICAL", "Theme classification must cover the full current universe.")
    add_audit(audit_rows, "theme_classification", "duplicate_tickers", "PASS" if theme_dup == 0 else "FAIL", theme_dup, 0, "CRITICAL", "Duplicate theme rows would make theme joins ambiguous.")
    add_audit(audit_rows, "theme_classification", "unknown_primary_theme_count", "PASS" if theme_unknown == 0 else "FAIL", theme_unknown, 0, "CRITICAL", "R28A-R2 should have eliminated UNKNOWN themes.")
    add_audit(audit_rows, "theme_classification", "missing_theme_rank_count", "PASS" if missing_theme_rank == 0 else "WARN", missing_theme_rank, 0, "MEDIUM", "Theme rank is useful for theme-relative backtests.")
    add_audit(audit_rows, "theme_classification", "etf_macro_exposure_count", "PASS", etf_macro, "track separately", "MEDIUM", "ETF/macro instruments should be separated from single-stock conclusions.")

    timing_path = root / TECHNICAL_TIMING
    timing_available = timing_path.exists()
    timing_rows = read_csv(timing_path) if timing_available else []
    timing_tickers = {norm_ticker(row.get("ticker")) for row in timing_rows if norm_ticker(row.get("ticker"))}
    timing_matched = len(rec_tickers & timing_tickers)
    timing_score_numeric = numeric_parse_count(timing_rows, "technical_timing_score") if timing_available else 0
    overheat_numeric = numeric_parse_count(timing_rows, "overheat_penalty") if timing_available and timing_rows and "overheat_penalty" in timing_rows[0] else 0
    label_columns = ["bb_status", "rsi_status", "technical_warning_label"]
    overheat_labels_available = any(timing_rows and column in timing_rows[0] for column in label_columns)
    add_audit(audit_rows, "technical_timing", "file_present", "PASS" if timing_available else "WARN", bool_text(timing_available), "TRUE", "MEDIUM", "Technical timing is useful but missing timing should not mutate recommendations.")
    add_audit(audit_rows, "technical_timing", "matched_ticker_count", "PASS" if timing_matched == len(recs) else "WARN", timing_matched, len(recs), "MEDIUM", "Timing coverage should match the recommendation universe.")
    add_audit(audit_rows, "technical_timing", "technical_score_numeric_parse_success", "PASS" if timing_available and timing_score_numeric == len(timing_rows) else "WARN", timing_score_numeric, len(timing_rows), "MEDIUM", "Technical scores should parse if timing is used in later tests.")
    add_audit(audit_rows, "technical_timing", "overheat_penalty_numeric_parse_success", "PASS" if not timing_rows or overheat_numeric == len(timing_rows) else "WARN", overheat_numeric, len(timing_rows), "LOW", "Overheat penalty is optional but should parse when present.")
    add_audit(audit_rows, "technical_timing", "overheat_labels_available", "PASS" if overheat_labels_available else "WARN", bool_text(overheat_labels_available), "TRUE", "LOW", "Overheat labels help explain tier downgrades.")

    ledger_path = root / SIGNAL_FREEZE_LEDGER
    ledger_available = ledger_path.exists()
    ledger_rows = read_csv(ledger_path) if ledger_available else []
    latest_run_id, latest_rows = latest_freeze_group(ledger_rows)
    latest_signal_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in latest_rows), default=dt.date.min)
    latest_signal_date_text = "" if latest_signal_date == dt.date.min else latest_signal_date.isoformat()
    latest_freeze_tickers = {norm_ticker(row.get("ticker")) for row in latest_rows if norm_ticker(row.get("ticker"))}
    latest_matches = bool(latest_freeze_tickers) and latest_freeze_tickers == rec_tickers
    freeze_join_count = len(latest_freeze_tickers & rec_tickers)
    current_missing_from_freeze = len(rec_tickers - latest_freeze_tickers)
    historical_signal_runs = len({norm(row.get("run_id")) for row in ledger_rows if norm(row.get("run_id"))})
    add_audit(audit_rows, "signal_freeze_ledger", "file_present", "PASS" if ledger_available else "WARN", bool_text(ledger_available), "TRUE", "HIGH", "A freeze ledger is required for non-lookahead historical signal tests.")
    add_audit(audit_rows, "signal_freeze_ledger", "latest_run_id", "PASS" if latest_run_id else "WARN", latest_run_id, "non-empty", "HIGH", "Latest freeze run selected by run_timestamp/signal_date.")
    add_audit(audit_rows, "signal_freeze_ledger", "latest_signal_date", "PASS" if latest_signal_date_text else "WARN", latest_signal_date_text, "non-empty", "HIGH", "Latest freeze signal date.")
    add_audit(audit_rows, "signal_freeze_ledger", "latest_frozen_ticker_count", "PASS" if len(latest_freeze_tickers) == len(recs) else "WARN", len(latest_freeze_tickers), len(recs), "HIGH", "Latest frozen ticker count should match current recommendations.")
    add_audit(audit_rows, "signal_freeze_ledger", "latest_freeze_matches_current_recommendations", "PASS" if latest_matches else "WARN", bool_text(latest_matches), "TRUE", "HIGH", f"Recommendation tiers join onto latest freeze for {freeze_join_count} tickers; current missing from freeze: {current_missing_from_freeze}.")
    add_audit(audit_rows, "signal_freeze_ledger", "historical_signal_freeze_run_count", "PASS" if historical_signal_runs > 1 else "WARN", historical_signal_runs, "> 1", "MEDIUM", "Multiple frozen runs are needed for a limited historical signal-freeze backtest.")

    price_dates_by_ticker: Dict[str, List[dt.date]] = {}
    max_dates: List[dt.date] = []
    min_dates: List[dt.date] = []
    for ticker in sorted(rec_tickers):
        path = price_file_for_ticker(root, ticker)
        dates = read_price_dates(path) if path else []
        if dates:
            price_dates_by_ticker[ticker] = dates
            min_dates.append(dates[0])
            max_dates.append(dates[-1])
    price_coverage = len(price_dates_by_ticker)
    latest_price_date_min = min(max_dates).isoformat() if max_dates else ""
    latest_price_date_max = max(max_dates).isoformat() if max_dates else ""
    forward_fillable: Dict[int, int] = {}
    for horizon in HORIZONS:
        count = 0
        for ticker in latest_freeze_tickers or rec_tickers:
            future_dates = [date for date in price_dates_by_ticker.get(ticker, []) if latest_signal_date != dt.date.min and date > latest_signal_date]
            if len(future_dates) >= horizon:
                count += 1
        forward_fillable[horizon] = count

    add_audit(audit_rows, "price_cache", "candidate_price_coverage_count", "PASS" if price_coverage >= len(recs) * 0.95 else "WARN", price_coverage, f">= {int(len(recs) * 0.95)}", "HIGH", "Local price cache coverage for current recommendation tickers.")
    add_audit(audit_rows, "price_cache", "latest_price_date_min", "PASS" if latest_price_date_min else "WARN", latest_price_date_min, "non-empty", "HIGH", "Minimum latest available price date across covered tickers.")
    add_audit(audit_rows, "price_cache", "latest_price_date_max", "PASS" if latest_price_date_max else "WARN", latest_price_date_max, "non-empty", "HIGH", "Maximum latest available price date across covered tickers.")
    for horizon in HORIZONS:
        add_audit(audit_rows, "price_cache", f"forward_{horizon}d_fillable_count", "PASS" if forward_fillable[horizon] == len(latest_freeze_tickers or rec_tickers) else "WARN", forward_fillable[horizon], len(latest_freeze_tickers or rec_tickers), "MEDIUM", f"Ticker count with at least {horizon} price bars after latest signal date {latest_signal_date_text}.")

    historical_rec_snapshots = count_historical_recommendation_snapshots(root)
    historical_candidate_snapshots = count_candidate_snapshots(root)
    tx_cost_ready = cost_model_ready(root)
    current_only_recommendation_tiers = historical_rec_snapshots == 0
    survivorship_risk = "HIGH" if current_only_recommendation_tiers else "MEDIUM"
    lookahead_risk = "HIGH" if current_only_recommendation_tiers else "MEDIUM"
    date_alignment_risk = "HIGH" if min(forward_fillable.values() or [0]) == 0 else "MEDIUM"
    etf_macro_risk = "MEDIUM" if etf_macro or tier_counts.get("ETF_OR_MACRO_EXPOSURE", 0) else "LOW"
    tx_ready_text = bool_text(tx_cost_ready)

    add_audit(audit_rows, "historical_snapshots", "historical_candidate_snapshot_count", "PASS" if historical_candidate_snapshots > 0 else "WARN", historical_candidate_snapshots, "> 0", "MEDIUM", "Historical candidate snapshots can support reconstruction if they are date-aligned.")
    add_audit(audit_rows, "historical_snapshots", "historical_recommendation_tier_snapshot_count", "PASS" if historical_rec_snapshots > 0 else "WARN", historical_rec_snapshots, "> 0 for full tier backtest", "HIGH", "Full historical recommendation-tier tests need tier snapshots from each historical decision date.")
    add_audit(audit_rows, "survivorship_bias", "survivorship_bias_risk", "WARN" if survivorship_risk == "HIGH" else "PASS", survivorship_risk, "LOW/MEDIUM", "HIGH", "Applying the current 252-name universe backward would introduce survivorship bias.")
    add_audit(audit_rows, "lookahead_bias", "lookahead_bias_risk", "WARN" if lookahead_risk == "HIGH" else "PASS", lookahead_risk, "LOW/MEDIUM", "HIGH", "Current R28B recommendation tiers must not be projected onto historical freeze dates.")
    add_audit(audit_rows, "date_alignment", "date_alignment_risk", "WARN" if date_alignment_risk == "HIGH" else "PASS", date_alignment_risk, "LOW/MEDIUM", "HIGH", "Latest freeze forward returns may not be fillable until future price bars exist.")
    add_audit(audit_rows, "etf_macro_contamination", "etf_macro_contamination_risk", "WARN" if etf_macro_risk != "LOW" else "PASS", etf_macro_risk, "LOW or separated reporting", "MEDIUM", "ETF/macro exposures should be excluded or separately bucketed in single-stock tests.")
    add_audit(audit_rows, "transaction_cost_model", "transaction_cost_model_ready", "PASS" if tx_cost_ready else "WARN", tx_ready_text, "TRUE for implementation-quality return estimates", "MEDIUM", "Transaction-cost assumptions are needed before production-like performance claims.")

    current_valid = (
        len(recs) == EXPECTED_CURRENT_ROWS
        and len(candidates) == EXPECTED_CURRENT_ROWS
        and len(themes) == EXPECTED_CURRENT_ROWS
        and rec_dup == 0
        and cand_dup == 0
        and theme_dup == 0
        and missing_tier == 0
        and missing_action == 0
        and unknown_theme == 0
        and theme_unknown == 0
        and rank_present
        and score_present
        and score_numeric == len(candidates)
    )

    if not current_valid:
        scope = "NOT_READY_FIX_DATA_ALIGNMENT_FIRST"
    elif historical_rec_snapshots > 0 and historical_signal_runs > 1 and price_coverage >= len(recs) * 0.95:
        scope = "READY_FOR_FULL_HISTORICAL_RECOMMENDATION_TIER_BACKTEST"
    elif historical_signal_runs > 1 and price_coverage >= len(recs) * 0.95:
        scope = "READY_FOR_LIMITED_HISTORICAL_SIGNAL_FREEZE_BACKTEST"
    elif max(forward_fillable.values() or [0]) > 0:
        scope = "READY_FOR_LATEST_FREEZE_FORWARD_VALIDATION_ONLY"
    else:
        scope = "NOT_READY_WAIT_FOR_FUTURE_PRICE_DATA"

    add_audit(audit_rows, "r29b_scope_recommendation", "recommended_scope", "PASS" if scope.startswith("READY") else "WARN", scope, "at least limited non-lookahead scope", "HIGH", "Recommendation tiers are current-only; historical tier backtesting requires dated tier snapshots.")

    forbidden_modified = protected_sig(root) != protected_before
    status = STATUS_OK
    if forbidden_modified or not current_valid:
        status = STATUS_FAIL
    elif (
        not latest_matches
        or not timing_available
        or timing_matched != len(recs)
        or price_coverage < len(recs) * 0.95
        or historical_rec_snapshots == 0
        or min(forward_fillable.values() or [0]) == 0
        or scope != "READY_FOR_FULL_HISTORICAL_RECOMMENDATION_TIER_BACKTEST"
    ):
        status = STATUS_WARN

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "CURRENT_RECOMMENDATION_ROW_COUNT": len(recs),
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": len(candidates),
        "THEME_CLASSIFICATION_ROW_COUNT": len(themes),
        "TECHNICAL_TIMING_AVAILABLE": bool_text(timing_available),
        "TECHNICAL_TIMING_MATCHED_COUNT": timing_matched,
        "SIGNAL_FREEZE_LEDGER_AVAILABLE": bool_text(ledger_available),
        "LATEST_SIGNAL_FREEZE_RUN_ID": latest_run_id,
        "LATEST_SIGNAL_FREEZE_DATE": latest_signal_date_text,
        "LATEST_SIGNAL_FREEZE_TICKER_COUNT": len(latest_freeze_tickers),
        "LATEST_SIGNAL_FREEZE_MATCHES_CURRENT_RECOMMENDATIONS": bool_text(latest_matches),
        "PRICE_CACHE_CANDIDATE_COVERAGE_COUNT": price_coverage,
        "LATEST_PRICE_DATE_MIN": latest_price_date_min,
        "LATEST_PRICE_DATE_MAX": latest_price_date_max,
        "FORWARD_1D_FILLABLE_COUNT": forward_fillable.get(1, 0),
        "FORWARD_3D_FILLABLE_COUNT": forward_fillable.get(3, 0),
        "FORWARD_5D_FILLABLE_COUNT": forward_fillable.get(5, 0),
        "FORWARD_10D_FILLABLE_COUNT": forward_fillable.get(10, 0),
        "FORWARD_20D_FILLABLE_COUNT": forward_fillable.get(20, 0),
        "HISTORICAL_SIGNAL_FREEZE_RUN_COUNT": historical_signal_runs,
        "HISTORICAL_RECOMMENDATION_TIER_SNAPSHOT_COUNT": historical_rec_snapshots,
        "SURVIVORSHIP_BIAS_RISK": survivorship_risk,
        "LOOKAHEAD_BIAS_RISK": lookahead_risk,
        "DATE_ALIGNMENT_RISK": date_alignment_risk,
        "ETF_MACRO_CONTAMINATION_RISK": etf_macro_risk,
        "TRANSACTION_COST_MODEL_READY": tx_ready_text,
        "R29B_SCOPE_RECOMMENDATION": scope,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": bool_text(forbidden_modified),
    }

    write_csv(root / OUT_AUDIT, audit_rows, AUDIT_FIELDS)
    write_text(root / OUT_REPORT, build_report(values, audit_rows))
    write_read_first(root / OUT_READ_FIRST, values)

    if status == STATUS_FAIL:
        raise RuntimeError("Historical backtest readiness audit failed validation checks")
    return values


def write_failure(root: Path, error: BaseException) -> None:
    values: Dict[str, object] = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("V18_29A_%Y%m%d_%H%M%S"),
        "CURRENT_RECOMMENDATION_ROW_COUNT": 0,
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": 0,
        "THEME_CLASSIFICATION_ROW_COUNT": 0,
        "TECHNICAL_TIMING_AVAILABLE": "FALSE",
        "TECHNICAL_TIMING_MATCHED_COUNT": 0,
        "SIGNAL_FREEZE_LEDGER_AVAILABLE": "FALSE",
        "LATEST_SIGNAL_FREEZE_RUN_ID": "",
        "LATEST_SIGNAL_FREEZE_DATE": "",
        "LATEST_SIGNAL_FREEZE_TICKER_COUNT": 0,
        "LATEST_SIGNAL_FREEZE_MATCHES_CURRENT_RECOMMENDATIONS": "FALSE",
        "PRICE_CACHE_CANDIDATE_COVERAGE_COUNT": 0,
        "LATEST_PRICE_DATE_MIN": "",
        "LATEST_PRICE_DATE_MAX": "",
        "FORWARD_1D_FILLABLE_COUNT": 0,
        "FORWARD_3D_FILLABLE_COUNT": 0,
        "FORWARD_5D_FILLABLE_COUNT": 0,
        "FORWARD_10D_FILLABLE_COUNT": 0,
        "FORWARD_20D_FILLABLE_COUNT": 0,
        "HISTORICAL_SIGNAL_FREEZE_RUN_COUNT": 0,
        "HISTORICAL_RECOMMENDATION_TIER_SNAPSHOT_COUNT": 0,
        "SURVIVORSHIP_BIAS_RISK": "UNKNOWN",
        "LOOKAHEAD_BIAS_RISK": "UNKNOWN",
        "DATE_ALIGNMENT_RISK": "UNKNOWN",
        "ETF_MACRO_CONTAMINATION_RISK": "UNKNOWN",
        "TRANSACTION_COST_MODEL_READY": "FALSE",
        "R29B_SCOPE_RECOMMENDATION": "NOT_READY_FIX_DATA_ALIGNMENT_FIRST",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "UNKNOWN",
    }
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, f"# V18.29A Historical Backtest Readiness Audit Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.29A historical backtest readiness audit.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        values = run(root)
        print(f"STATUS: {values['STATUS']}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return 0
    except Exception as exc:
        write_failure(root, exc)
        print(f"STATUS: {STATUS_FAIL}")
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
