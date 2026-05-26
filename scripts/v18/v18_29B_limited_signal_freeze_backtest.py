from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import math
import statistics
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_29B_LIMITED_SIGNAL_FREEZE_BACKTEST_READY"
STATUS_WARN = "WARN_V18_29B_LIMITED_SIGNAL_FREEZE_BACKTEST_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_29B_LIMITED_SIGNAL_FREEZE_BACKTEST_ERROR"
MODE = "LIMITED_HISTORICAL_SIGNAL_FREEZE_BACKTEST"

SIGNAL_FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
THEME_CLASSIFICATION = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
CURRENT_RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
TECHNICAL_TIMING = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"

OUT_ROWS = "outputs/v18/backtest/V18_29B_LIMITED_SIGNAL_FREEZE_BACKTEST_ROWS.csv"
OUT_BUCKET_SUMMARY = "outputs/v18/backtest/V18_29B_LIMITED_SIGNAL_FREEZE_BUCKET_SUMMARY.csv"
OUT_RUN_SUMMARY = "outputs/v18/backtest/V18_29B_LIMITED_SIGNAL_FREEZE_RUN_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_29B_LIMITED_SIGNAL_FREEZE_BACKTEST_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_29B_READ_FIRST.txt"

HORIZONS = [1, 3, 5, 10, 20]
RANK_BUCKETS = ["TOP_10", "TOP_20", "TOP_30", "TOP_50", "TOP_100", "REST"]
SCORE_BUCKETS = [
    "score_quantile_1_highest",
    "score_quantile_2",
    "score_quantile_3",
    "score_quantile_4",
    "score_quantile_5_lowest",
]

PROTECTED_FILES = [
    SIGNAL_FREEZE_LEDGER,
    CURRENT_RECOMMENDATIONS,
    CURRENT_CANDIDATES,
    THEME_CLASSIFICATION,
    TECHNICAL_TIMING,
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
    "SIGNAL_FREEZE_LEDGER_AVAILABLE",
    "HISTORICAL_SIGNAL_FREEZE_RUN_COUNT",
    "TOTAL_FROZEN_ROWS",
    "UNIQUE_TICKER_COUNT",
    "PRICE_CACHE_COVERAGE_COUNT",
    "RUNS_WITH_1D_FILLABLE",
    "RUNS_WITH_3D_FILLABLE",
    "RUNS_WITH_5D_FILLABLE",
    "RUNS_WITH_10D_FILLABLE",
    "RUNS_WITH_20D_FILLABLE",
    "TOTAL_1D_FILLABLE_ROWS",
    "TOTAL_3D_FILLABLE_ROWS",
    "TOTAL_5D_FILLABLE_ROWS",
    "TOTAL_10D_FILLABLE_ROWS",
    "TOTAL_20D_FILLABLE_ROWS",
    "LATEST_FREEZE_RUN_ID",
    "LATEST_FREEZE_SIGNAL_DATE",
    "LATEST_FREEZE_INCLUDED_IN_METRICS",
    "CURRENT_RECOMMENDATION_TIERS_USED_HISTORICALLY",
    "FULL_RECOMMENDATION_TIER_BACKTEST_READY",
    "SURVIVORSHIP_BIAS_RISK",
    "LOOKAHEAD_BIAS_RISK",
    "DATE_ALIGNMENT_RISK",
    "TRANSACTION_COST_MODEL_READY",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "FORBIDDEN_MODIFIED",
]

ROW_FIELDS = [
    "run_id",
    "signal_date",
    "ticker",
    "frozen_rank",
    "frozen_score",
    "rank_bucket",
    "score_bucket",
    "entry_date",
    "entry_close",
    "forward_1d_date",
    "forward_1d_close",
    "forward_1d_return",
    "forward_3d_date",
    "forward_3d_close",
    "forward_3d_return",
    "forward_5d_date",
    "forward_5d_close",
    "forward_5d_return",
    "forward_10d_date",
    "forward_10d_close",
    "forward_10d_return",
    "forward_20d_date",
    "forward_20d_close",
    "forward_20d_return",
    "fillability_status",
    "data_warning",
]

BUCKET_FIELDS = [
    "horizon",
    "bucket_type",
    "bucket_name",
    "observation_count",
    "fillable_count",
    "avg_forward_return",
    "median_forward_return",
    "win_rate",
    "loss_rate",
    "best_return",
    "worst_return",
    "standard_deviation",
    "spread_vs_rest",
    "spread_vs_lowest_bucket",
]

RUN_FIELDS = [
    "run_id",
    "signal_date",
    "frozen_row_count",
    "unique_ticker_count",
    "forward_1d_fillable_count",
    "forward_3d_fillable_count",
    "forward_5d_fillable_count",
    "forward_10d_fillable_count",
    "forward_20d_fillable_count",
    "included_in_metrics",
    "run_warning",
]


def norm(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


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


def to_int(value: object) -> Optional[int]:
    parsed = to_float(value)
    if parsed is None:
        return None
    return int(parsed)


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
        parsed = parse_date(text)
        if parsed:
            return dt.datetime.combine(parsed, dt.time.min)
    return dt.datetime.min


def fmt_float(value: Optional[float], digits: int = 6) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


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


def read_price_series(path: Path) -> List[Tuple[dt.date, float]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return []
        lower = {field.lower().strip(): field for field in reader.fieldnames}
        date_col = lower.get("date") or lower.get("price_date") or lower.get("timestamp")
        close_col = lower.get("close") or lower.get("adj_close") or lower.get("adj close")
        if not date_col or not close_col:
            return []
        by_date: Dict[dt.date, float] = {}
        for row in reader:
            date = parse_date(row.get(date_col))
            close = to_float(row.get(close_col))
            if date and close is not None and close > 0:
                by_date[date] = close
        return sorted(by_date.items())


def price_file_for_ticker(root: Path, ticker: str) -> Optional[Path]:
    candidates = [
        root / "state/v18/price_cache" / f"{ticker}.csv",
        root / "outputs/v18/price_cache" / f"{ticker}.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def rank_bucket(rank: Optional[int]) -> str:
    if rank is None:
        return "REST"
    if rank <= 10:
        return "TOP_10"
    if rank <= 20:
        return "TOP_20"
    if rank <= 30:
        return "TOP_30"
    if rank <= 50:
        return "TOP_50"
    if rank <= 100:
        return "TOP_100"
    return "REST"


def assign_score_buckets(rows: Sequence[Dict[str, str]]) -> Dict[Tuple[str, str], str]:
    by_run: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    for row in rows:
        run_id = norm(row.get("run_id"))
        ticker = norm_ticker(row.get("ticker"))
        score = frozen_score(row)
        if run_id and ticker and score is not None:
            by_run[run_id].append((ticker, score))

    output: Dict[Tuple[str, str], str] = {}
    for run_id, pairs in by_run.items():
        pairs_sorted = sorted(pairs, key=lambda item: (-item[1], item[0]))
        n = len(pairs_sorted)
        if n == 0:
            continue
        for idx, (ticker, _score) in enumerate(pairs_sorted):
            quantile = min(4, math.floor(idx * 5 / n))
            output[(run_id, ticker)] = SCORE_BUCKETS[quantile]
    return output


def frozen_rank(row: Dict[str, str]) -> Optional[int]:
    for column in ["source_rank", "rank", "factor_pack_rank"]:
        value = to_int(row.get(column))
        if value is not None:
            return value
    return None


def frozen_score(row: Dict[str, str]) -> Optional[float]:
    for column in ["composite_candidate_score", "factor_score", "score"]:
        value = to_float(row.get(column))
        if value is not None:
            return value
    return None


def latest_run(rows: Sequence[Dict[str, str]]) -> Tuple[str, dt.date]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[norm(row.get("run_id"))].append(row)
    if not grouped:
        return "", dt.date.min

    def key(item: Tuple[str, List[Dict[str, str]]]) -> Tuple[dt.datetime, dt.date, str]:
        run_id, run_rows = item
        latest_ts = max((parse_dt(row.get("run_timestamp")) for row in run_rows), default=dt.datetime.min)
        latest_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in run_rows), default=dt.date.min)
        return latest_ts, latest_date, run_id

    run_id, run_rows = max(grouped.items(), key=key)
    signal_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in run_rows), default=dt.date.min)
    return run_id, signal_date


def current_etf_macro_tickers(root: Path) -> set[str]:
    path = root / THEME_CLASSIFICATION
    if not path.exists():
        return set()
    tickers: set[str] = set()
    for row in read_csv(path):
        ticker = norm_ticker(row.get("ticker"))
        industry = norm(row.get("industry_group")).upper()
        primary = norm(row.get("primary_theme")).upper()
        secondary = norm(row.get("secondary_theme")).upper()
        if ticker and (industry == "ETF" or primary == "OTHER" and "ETF" in secondary):
            tickers.add(ticker)
    return tickers


def cost_model_ready(root: Path) -> bool:
    patterns = ["*TRANSACTION*COST*.csv", "*SLIPPAGE*.csv", "*COMMISSION*.csv"]
    for base in [root / "state/v18", root / "outputs/v18"]:
        if base.exists():
            for pattern in patterns:
                if any(base.rglob(pattern)):
                    return True
    return False


def build_backtest_row(
    root: Path,
    ledger_row: Dict[str, str],
    score_bucket_map: Dict[Tuple[str, str], str],
    price_series: Dict[str, List[Tuple[dt.date, float]]],
    etf_macro: set[str],
) -> Dict[str, object]:
    run_id = norm(ledger_row.get("run_id"))
    ticker = norm_ticker(ledger_row.get("ticker"))
    signal_date = parse_date(ledger_row.get("signal_date"))
    rank = frozen_rank(ledger_row)
    score = frozen_score(ledger_row)
    series = price_series.get(ticker, [])
    warnings: List[str] = []
    if ticker in etf_macro:
        warnings.append("CURRENT_METADATA_ETF_OR_MACRO_FLAG")
    if signal_date is None:
        warnings.append("MISSING_SIGNAL_DATE")
    if not series:
        warnings.append("MISSING_PRICE_CACHE")

    entry_idx: Optional[int] = None
    entry_date: Optional[dt.date] = None
    entry_close: Optional[float] = None
    if signal_date and series:
        for idx, (date, close) in enumerate(series):
            if date >= signal_date:
                entry_idx = idx
                entry_date = date
                entry_close = close
                if date > signal_date:
                    warnings.append("ENTRY_AFTER_SIGNAL_DATE")
                break
    if entry_idx is None and series:
        warnings.append("NO_ENTRY_PRICE_ON_OR_AFTER_SIGNAL_DATE")

    output: Dict[str, object] = {
        "run_id": run_id,
        "signal_date": signal_date.isoformat() if signal_date else "",
        "ticker": ticker,
        "frozen_rank": rank if rank is not None else "",
        "frozen_score": fmt_float(score),
        "rank_bucket": rank_bucket(rank),
        "score_bucket": score_bucket_map.get((run_id, ticker), "score_quantile_unknown"),
        "entry_date": entry_date.isoformat() if entry_date else "",
        "entry_close": fmt_float(entry_close),
        "fillability_status": "UNFILLED",
        "data_warning": "",
    }

    filled_any = False
    for horizon in HORIZONS:
        date_key = f"forward_{horizon}d_date"
        close_key = f"forward_{horizon}d_close"
        return_key = f"forward_{horizon}d_return"
        output[date_key] = ""
        output[close_key] = ""
        output[return_key] = ""
        if entry_idx is None or entry_close is None:
            continue
        exit_idx = entry_idx + horizon
        if exit_idx >= len(series):
            continue
        exit_date, exit_close = series[exit_idx]
        if signal_date and exit_date <= signal_date:
            warnings.append(f"INVALID_{horizon}D_EXIT_NOT_AFTER_SIGNAL_DATE")
            continue
        output[date_key] = exit_date.isoformat()
        output[close_key] = fmt_float(exit_close)
        output[return_key] = fmt_float((exit_close / entry_close) - 1.0)
        filled_any = True

    if filled_any:
        missing = [str(horizon) for horizon in HORIZONS if not output.get(f"forward_{horizon}d_return")]
        output["fillability_status"] = "PARTIAL_FILL" if missing else "FULL_FILL"
        if missing:
            warnings.append("MISSING_HORIZONS_" + "_".join(missing))
    else:
        warnings.append("NO_FORWARD_RETURN_FILLABLE")
    output["data_warning"] = ";".join(dict.fromkeys(warnings))
    return output


def metric_row(horizon: int, bucket_type: str, bucket_name: str, rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    key = f"forward_{horizon}d_return"
    returns = [to_float(row.get(key)) for row in rows]
    filled = [value for value in returns if value is not None]
    wins = [value for value in filled if value > 0]
    losses = [value for value in filled if value < 0]
    return {
        "horizon": f"{horizon}D",
        "bucket_type": bucket_type,
        "bucket_name": bucket_name,
        "observation_count": len(rows),
        "fillable_count": len(filled),
        "avg_forward_return": fmt_float(statistics.mean(filled) if filled else None),
        "median_forward_return": fmt_float(statistics.median(filled) if filled else None),
        "win_rate": fmt_float(len(wins) / len(filled) if filled else None),
        "loss_rate": fmt_float(len(losses) / len(filled) if filled else None),
        "best_return": fmt_float(max(filled) if filled else None),
        "worst_return": fmt_float(min(filled) if filled else None),
        "standard_deviation": fmt_float(statistics.stdev(filled) if len(filled) > 1 else (0.0 if len(filled) == 1 else None)),
        "spread_vs_rest": "",
        "spread_vs_lowest_bucket": "",
    }


def add_spreads(summary: List[Dict[str, object]]) -> None:
    grouped: Dict[Tuple[str, str], Dict[str, Dict[str, object]]] = defaultdict(dict)
    for row in summary:
        grouped[(norm(row.get("horizon")), norm(row.get("bucket_type")))][norm(row.get("bucket_name"))] = row

    for (_horizon, bucket_type), rows_by_bucket in grouped.items():
        if bucket_type == "rank_bucket":
            rest_avg = to_float(rows_by_bucket.get("REST", {}).get("avg_forward_return"))
            for row in rows_by_bucket.values():
                avg = to_float(row.get("avg_forward_return"))
                if avg is not None and rest_avg is not None:
                    row["spread_vs_rest"] = fmt_float(avg - rest_avg)
        if bucket_type == "score_bucket":
            lowest_avg = to_float(rows_by_bucket.get("score_quantile_5_lowest", {}).get("avg_forward_return"))
            for row in rows_by_bucket.values():
                avg = to_float(row.get("avg_forward_return"))
                if avg is not None and lowest_avg is not None:
                    row["spread_vs_lowest_bucket"] = fmt_float(avg - lowest_avg)


def build_bucket_summary(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    summary: List[Dict[str, object]] = []
    for horizon in HORIZONS:
        for bucket in RANK_BUCKETS:
            bucket_rows = [row for row in rows if row.get("rank_bucket") == bucket]
            summary.append(metric_row(horizon, "rank_bucket", bucket, bucket_rows))
        for bucket in SCORE_BUCKETS:
            bucket_rows = [row for row in rows if row.get("score_bucket") == bucket]
            summary.append(metric_row(horizon, "score_bucket", bucket, bucket_rows))
    add_spreads(summary)
    return summary


def build_run_summary(rows: Sequence[Dict[str, object]], latest_run_id: str) -> List[Dict[str, object]]:
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[norm(row.get("run_id"))].append(row)
    output: List[Dict[str, object]] = []
    for run_id, run_rows in sorted(grouped.items(), key=lambda item: (norm(item[1][0].get("signal_date")), item[0])):
        fill_counts = {
            horizon: sum(1 for row in run_rows if norm(row.get(f"forward_{horizon}d_return")))
            for horizon in HORIZONS
        }
        included = any(count > 0 for count in fill_counts.values())
        warning_parts: List[str] = []
        if not included:
            warning_parts.append("NO_FILLABLE_FORWARD_RETURNS")
        if run_id == latest_run_id and not included:
            warning_parts.append("LATEST_FREEZE_EXCLUDED_FROM_FILLED_METRICS")
        output.append(
            {
                "run_id": run_id,
                "signal_date": norm(run_rows[0].get("signal_date")),
                "frozen_row_count": len(run_rows),
                "unique_ticker_count": len({norm_ticker(row.get("ticker")) for row in run_rows}),
                "forward_1d_fillable_count": fill_counts[1],
                "forward_3d_fillable_count": fill_counts[3],
                "forward_5d_fillable_count": fill_counts[5],
                "forward_10d_fillable_count": fill_counts[10],
                "forward_20d_fillable_count": fill_counts[20],
                "included_in_metrics": bool_text(included),
                "run_warning": ";".join(warning_parts),
            }
        )
    return output


def markdown_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: Optional[int] = None) -> str:
    selected = list(rows[:limit] if limit is not None else rows)
    if not selected:
        return "_None._\n"
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in selected:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def build_report(
    values: Dict[str, object],
    run_summary: Sequence[Dict[str, object]],
    bucket_summary: Sequence[Dict[str, object]],
) -> str:
    rank_perf = [row for row in bucket_summary if row.get("bucket_type") == "rank_bucket"]
    score_perf = [row for row in bucket_summary if row.get("bucket_type") == "score_bucket"]
    top_spread = [
        row for row in rank_perf
        if row.get("bucket_name") in {"TOP_10", "TOP_20", "TOP_30"} and norm(row.get("spread_vs_rest"))
    ]
    score_spread = [
        row for row in score_perf
        if row.get("bucket_name") == "score_quantile_1_highest" and norm(row.get("spread_vs_lowest_bucket"))
    ]
    report = [
        "# V18.29B Limited Historical Signal-Freeze Backtest",
        "",
        "## Read First",
        "```text",
        "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS),
        "```",
        "",
        "## Scope Limitations",
        "- This is a limited signal-freeze backtest, not a full recommendation-tier backtest.",
        "- Current recommendation_tier labels are not used historically.",
        "- Entry convention: close on the first cached trading date on or after signal_date.",
        "- Exit convention: close after N cached trading bars from entry; prices before or on signal_date are not used as forward endpoints.",
        "- Latest freezes with no future prices are included in coverage diagnostics and excluded from filled return metrics.",
        "",
        "## Historical Signal Freeze Run Coverage",
        markdown_table(run_summary, RUN_FIELDS),
        "## Forward Return Fillability By Run",
        markdown_table(run_summary, RUN_FIELDS),
        "## Rank Bucket Performance By Horizon",
        markdown_table(rank_perf, BUCKET_FIELDS),
        "## Score Bucket Performance By Horizon",
        markdown_table(score_perf, BUCKET_FIELDS),
        "## Top-Minus-Rest Spread",
        markdown_table(top_spread, BUCKET_FIELDS),
        "## Top-Minus-Bottom Score Bucket Spread",
        markdown_table(score_spread, BUCKET_FIELDS),
        "## Data Quality And Bias Warnings",
        f"- SURVIVORSHIP_BIAS_RISK: {values.get('SURVIVORSHIP_BIAS_RISK')}",
        f"- LOOKAHEAD_BIAS_RISK: {values.get('LOOKAHEAD_BIAS_RISK')}",
        f"- DATE_ALIGNMENT_RISK: {values.get('DATE_ALIGNMENT_RISK')}",
        f"- TRANSACTION_COST_MODEL_READY: {values.get('TRANSACTION_COST_MODEL_READY')}",
        "- ETF/macro instruments are flagged with current metadata when available, but are not silently removed.",
        "",
        "## Not A Full Recommendation-Tier Backtest",
        "Historical recommendation-tier snapshots do not exist, so this report only evaluates frozen rank and frozen score buckets from the signal freeze ledger.",
        "",
        "## Next-Step Recommendation",
        "- Wait for post-freeze local price bars before relying on forward-return metrics for the 2026-05-23 run.",
        "- Build dated recommendation-tier snapshots before attempting a full historical recommendation-tier backtest.",
        "- Add an explicit transaction-cost/slippage model before using results for production-like performance claims.",
    ]
    return "\n".join(report) + "\n"


def run(root: Path) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("V18_29B_%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)
    ledger_path = root / SIGNAL_FREEZE_LEDGER
    if not ledger_path.exists():
        raise FileNotFoundError(ledger_path)
    ledger_rows = read_csv(ledger_path)
    if not ledger_rows:
        raise RuntimeError("Signal freeze ledger is empty")

    missing_required = [
        idx for idx, row in enumerate(ledger_rows, start=1)
        if not norm(row.get("run_id")) or not norm_ticker(row.get("ticker")) or parse_date(row.get("signal_date")) is None
    ]
    if missing_required:
        raise RuntimeError(f"Signal freeze ledger has rows with missing run_id/ticker/signal_date: {len(missing_required)}")

    score_bucket_map = assign_score_buckets(ledger_rows)
    etf_macro = current_etf_macro_tickers(root)
    all_tickers = {norm_ticker(row.get("ticker")) for row in ledger_rows if norm_ticker(row.get("ticker"))}
    price_series: Dict[str, List[Tuple[dt.date, float]]] = {}
    for ticker in sorted(all_tickers):
        path = price_file_for_ticker(root, ticker)
        if path:
            series = read_price_series(path)
            if series:
                price_series[ticker] = series

    rows = [
        build_backtest_row(root, row, score_bucket_map, price_series, etf_macro)
        for row in ledger_rows
    ]
    latest_run_id, latest_signal_date = latest_run(ledger_rows)
    run_summary = build_run_summary(rows, latest_run_id)
    bucket_summary = build_bucket_summary(rows)

    runs_with_fillable = {
        horizon: sum(1 for row in run_summary if to_int(row.get(f"forward_{horizon}d_fillable_count")) and to_int(row.get(f"forward_{horizon}d_fillable_count")) > 0)
        for horizon in HORIZONS
    }
    total_fillable = {
        horizon: sum(1 for row in rows if norm(row.get(f"forward_{horizon}d_return")))
        for horizon in HORIZONS
    }
    latest_run_row = next((row for row in run_summary if row.get("run_id") == latest_run_id), {})
    latest_included = norm(latest_run_row.get("included_in_metrics")) == "TRUE"
    historical_run_count = len({norm(row.get("run_id")) for row in ledger_rows if norm(row.get("run_id"))})
    tx_ready = cost_model_ready(root)
    any_fillable = any(count > 0 for count in total_fillable.values())
    only_short_fillable = (total_fillable[1] > 0 or total_fillable[3] > 0) and total_fillable[5] == 0 and total_fillable[10] == 0 and total_fillable[20] == 0

    forbidden_modified = protected_sig(root) != protected_before
    status = STATUS_OK
    if forbidden_modified:
        status = STATUS_FAIL
    elif not any_fillable or only_short_fillable or not tx_ready:
        status = STATUS_WARN

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "SIGNAL_FREEZE_LEDGER_AVAILABLE": "TRUE",
        "HISTORICAL_SIGNAL_FREEZE_RUN_COUNT": historical_run_count,
        "TOTAL_FROZEN_ROWS": len(ledger_rows),
        "UNIQUE_TICKER_COUNT": len(all_tickers),
        "PRICE_CACHE_COVERAGE_COUNT": len(price_series),
        "RUNS_WITH_1D_FILLABLE": runs_with_fillable[1],
        "RUNS_WITH_3D_FILLABLE": runs_with_fillable[3],
        "RUNS_WITH_5D_FILLABLE": runs_with_fillable[5],
        "RUNS_WITH_10D_FILLABLE": runs_with_fillable[10],
        "RUNS_WITH_20D_FILLABLE": runs_with_fillable[20],
        "TOTAL_1D_FILLABLE_ROWS": total_fillable[1],
        "TOTAL_3D_FILLABLE_ROWS": total_fillable[3],
        "TOTAL_5D_FILLABLE_ROWS": total_fillable[5],
        "TOTAL_10D_FILLABLE_ROWS": total_fillable[10],
        "TOTAL_20D_FILLABLE_ROWS": total_fillable[20],
        "LATEST_FREEZE_RUN_ID": latest_run_id,
        "LATEST_FREEZE_SIGNAL_DATE": latest_signal_date.isoformat() if latest_signal_date != dt.date.min else "",
        "LATEST_FREEZE_INCLUDED_IN_METRICS": bool_text(latest_included),
        "CURRENT_RECOMMENDATION_TIERS_USED_HISTORICALLY": "FALSE",
        "FULL_RECOMMENDATION_TIER_BACKTEST_READY": "FALSE",
        "SURVIVORSHIP_BIAS_RISK": "MEDIUM",
        "LOOKAHEAD_BIAS_RISK": "LOW",
        "DATE_ALIGNMENT_RISK": "HIGH" if not any_fillable else "MEDIUM",
        "TRANSACTION_COST_MODEL_READY": bool_text(tx_ready),
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": bool_text(forbidden_modified),
    }

    write_csv(root / OUT_ROWS, rows, ROW_FIELDS)
    write_csv(root / OUT_BUCKET_SUMMARY, bucket_summary, BUCKET_FIELDS)
    write_csv(root / OUT_RUN_SUMMARY, run_summary, RUN_FIELDS)
    write_text(root / OUT_REPORT, build_report(values, run_summary, bucket_summary))
    write_read_first(root / OUT_READ_FIRST, values)

    if status == STATUS_FAIL:
        raise RuntimeError("Protected state modified during limited signal-freeze backtest")
    return values


def write_failure(root: Path, error: BaseException) -> None:
    values: Dict[str, object] = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("V18_29B_%Y%m%d_%H%M%S"),
        "SIGNAL_FREEZE_LEDGER_AVAILABLE": bool_text((root / SIGNAL_FREEZE_LEDGER).exists()),
        "HISTORICAL_SIGNAL_FREEZE_RUN_COUNT": 0,
        "TOTAL_FROZEN_ROWS": 0,
        "UNIQUE_TICKER_COUNT": 0,
        "PRICE_CACHE_COVERAGE_COUNT": 0,
        "RUNS_WITH_1D_FILLABLE": 0,
        "RUNS_WITH_3D_FILLABLE": 0,
        "RUNS_WITH_5D_FILLABLE": 0,
        "RUNS_WITH_10D_FILLABLE": 0,
        "RUNS_WITH_20D_FILLABLE": 0,
        "TOTAL_1D_FILLABLE_ROWS": 0,
        "TOTAL_3D_FILLABLE_ROWS": 0,
        "TOTAL_5D_FILLABLE_ROWS": 0,
        "TOTAL_10D_FILLABLE_ROWS": 0,
        "TOTAL_20D_FILLABLE_ROWS": 0,
        "LATEST_FREEZE_RUN_ID": "",
        "LATEST_FREEZE_SIGNAL_DATE": "",
        "LATEST_FREEZE_INCLUDED_IN_METRICS": "FALSE",
        "CURRENT_RECOMMENDATION_TIERS_USED_HISTORICALLY": "FALSE",
        "FULL_RECOMMENDATION_TIER_BACKTEST_READY": "FALSE",
        "SURVIVORSHIP_BIAS_RISK": "UNKNOWN",
        "LOOKAHEAD_BIAS_RISK": "UNKNOWN",
        "DATE_ALIGNMENT_RISK": "UNKNOWN",
        "TRANSACTION_COST_MODEL_READY": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "UNKNOWN",
    }
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, f"# V18.29B Limited Historical Signal-Freeze Backtest Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.29B limited historical signal-freeze backtest.")
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
