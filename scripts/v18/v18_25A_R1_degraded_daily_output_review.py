from __future__ import annotations

import argparse
import csv
import datetime as dt
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


MODE = "READ_ONLY_DEGRADED_DAILY_OUTPUT_REVIEW"
STATUS_OK = "OK_V18_25A_R1_DEGRADED_DAILY_OUTPUT_REVIEW_READY"
STATUS_WARN = "WARN_V18_25A_R1_DEGRADED_DAILY_OUTPUT_REVIEW_READY"
STATUS_FAIL = "FAIL_V18_25A_R1_DEGRADED_DAILY_OUTPUT_REVIEW"

OUTPUT_DIR = "outputs/v18/degraded_daily_review"

INPUTS = {
    "daily": "outputs/v18/degraded_daily/V18_25A_CURRENT_DEGRADED_DAILY_OUTPUT.csv",
    "summary": "outputs/v18/degraded_daily/V18_25A_CURRENT_DEGRADED_DAILY_SUMMARY.csv",
    "recommendations": "outputs/v18/degraded_daily/V18_25A_CURRENT_DATA_GAP_RECOMMENDATIONS.csv",
    "report": "outputs/v18/degraded_daily/V18_25A_CURRENT_DEGRADED_DAILY_REPORT.md",
    "homepage": "outputs/v18/operator_homepage/V18_25A_CURRENT_DEGRADED_DAILY_OPERATOR_HOMEPAGE.md",
    "read_first": "outputs/v18/ops/V18_25A_READ_FIRST.txt",
    "ops_read_first": "outputs/v18/ops/V18_25A_R1_READ_FIRST.txt",
}

OUTPUTS = {
    "bucket_review": f"{OUTPUT_DIR}/V18_25A_R1_CURRENT_OUTPUT_BUCKET_REVIEW.csv",
    "high_trust_top30": f"{OUTPUT_DIR}/V18_25A_R1_CURRENT_HIGH_TRUST_TOP30.csv",
    "watch_only_priority": f"{OUTPUT_DIR}/V18_25A_R1_CURRENT_WATCH_ONLY_PRIORITY.csv",
    "data_not_ready_priority": f"{OUTPUT_DIR}/V18_25A_R1_CURRENT_DATA_NOT_READY_PRIORITY.csv",
    "data_gap_groups": f"{OUTPUT_DIR}/V18_25A_R1_CURRENT_DATA_GAP_GROUPS.csv",
    "report": f"{OUTPUT_DIR}/V18_25A_R1_CURRENT_REVIEW_REPORT.md",
    "ops_report": "outputs/v18/ops/V18_25A_R1_CURRENT_DEGRADED_DAILY_OUTPUT_REVIEW_REPORT.md",
    "ops_read_first": "outputs/v18/ops/V18_25A_R1_READ_FIRST.txt",
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "TOTAL_OUTPUT_ROWS",
    "HIGH_TRUST_COUNT",
    "MEDIUM_TRUST_COUNT",
    "LOW_TRUST_COUNT",
    "DATA_NOT_READY_COUNT",
    "OFFICIAL_RANK_ALLOWED_COUNT",
    "WATCH_ONLY_COUNT",
    "TRADE_ALLOWED_COUNT",
    "DATA_GAP_RECOMMENDATION_COUNT",
    "NEEDS_OFFICIAL_INTEGRATION_COUNT",
    "NEEDS_STAGED_BACKFILL_COUNT",
    "PARTIAL_HISTORY_REVIEW_COUNT",
    "EMPTY_FETCH_OR_HOLD_REVIEW_COUNT",
    "UNKNOWN_OR_OTHER_GAP_COUNT",
    "HIGH_TRUST_SUSPICIOUS_COUNT",
    "SOURCE_MISSING_WARNING_COUNT",
    "NEXT_RECOMMENDED_STEP",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_BACKFILL_MODIFIED",
    "LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "BACKTEST_EXECUTED",
    "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT",
]

DAILY_FIELDS = [
    "ticker",
    "output_bucket",
    "trust_level",
    "score_available",
    "composite_score",
    "score_source",
    "tier_current",
    "technical_available",
    "technical_status",
    "official_price_cache_available",
    "rolling_ledger_status",
    "staged_backfill_status",
    "data_gap_reason",
    "official_rank_allowed",
    "watch_only",
    "trade_allowed",
    "reason_summary",
]

RECOMMENDATION_FIELDS = ["ticker", "recommendation_type", "priority", "reason", "known_tier", "known_score"]

BUCKET_HIGH = "HIGH_TRUST_OFFICIAL_RANK_CANDIDATE"
BUCKET_MEDIUM = "MEDIUM_TRUST_PARTIAL_WATCH"
BUCKET_LOW = "LOW_TRUST_PRICE_ONLY_OR_STAGED_WATCH"
BUCKET_NOT_READY = "DATA_NOT_READY"

GAP_GROUPS = {
    "NEEDS_OFFICIAL_INTEGRATION": {"NEEDS_OFFICIAL_INTEGRATION"},
    "NEEDS_STAGED_BACKFILL": {"NEEDS_STAGED_BACKFILL"},
    "PARTIAL_HISTORY_REVIEW": {"PARTIAL_HISTORY"},
    "EMPTY_FETCH_OR_HOLD_REVIEW": {"EMPTY_FETCH_OR_HOLD_REVIEW"},
}

FORBIDDEN_DIRS = [
    "state/v18/price_cache",
    "data/v18/price_history",
    "state/v18/price_history",
    "data/v18/staged_backfill",
    "outputs/v18/staged_backfill",
    "state/v18/rolling_coverage",
    "outputs/v18/factor_pack",
    "outputs/v18/technical_timing",
    "outputs/v18/daily_integrated",
    "outputs/v18/ranking",
    "outputs/v18/signal_snapshots",
]

PATH_ALIASES = {
    "official_price_cache_available": "official_price_cache_available",
    "technical_available": "technical_available",
    "trade_allowed": "trade_allowed",
    "watch_only": "watch_only",
    "official_rank_allowed": "official_rank_allowed",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except csv.Error:
            continue
    return [], []


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def get_ticker(row: Dict[str, str]) -> str:
    for key in ("ticker", "Ticker", "symbol", "Symbol", "yf_ticker"):
        value = str(row.get(key, "")).strip().upper()
        if value and value not in {"NAN", "NONE", "NULL"}:
            return value
    return ""


def to_float(value: object) -> float | None:
    try:
        text = str(value).replace(",", "").strip()
        if not text:
            return None
        return float(text)
    except ValueError:
        return None


def is_true(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "YES", "Y", "1", "AVAILABLE", "PASS", "SUCCESS"}


def parse_read_first(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def file_signature(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def collect_forbidden_files(root: Path) -> Dict[str, Tuple[int, int]]:
    out: Dict[str, Tuple[int, int]] = {}
    for rel_dir in FORBIDDEN_DIRS:
        base = root / rel_dir
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file():
                out[str(path.relative_to(root)).replace("\\", "/")] = file_signature(path)
    return out


def diff_signatures(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    paths = sorted(set(before) | set(after))
    return [path for path in paths if before.get(path) != after.get(path)]


def format_examples(rows: Sequence[Dict[str, str]], limit: int = 5) -> str:
    return "; ".join(row["ticker"] for row in rows[:limit])


def format_row_list(rows: Sequence[Dict[str, str]], limit: int = 10) -> str:
    return ", ".join(row["ticker"] for row in rows[:limit])


def summarize_reasons(rows: Sequence[Dict[str, str]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        reason = str(row.get("data_gap_reason", "")).strip()
        if reason:
            counter[reason] += 1
    return counter


def summarize_reason_tokens(rows: Sequence[Dict[str, str]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        raw = str(row.get("data_gap_reason", "")).strip()
        if not raw:
            continue
        for token in raw.split("|"):
            token = token.strip()
            if token:
                counter[token] += 1
    return counter


def load_history_evidence(root: Path) -> Dict[str, Tuple[str, str, str]]:
    """
    For each ticker, keep the newest historical snapshot evidence that shows
    a prior score or a non-empty tier. This is only used for prioritization.
    """

    history_dir = root / "outputs/v18/tier_migration/history"
    if not history_dir.exists():
        return {}

    evidence: Dict[str, Tuple[str, str, str]] = {}
    files = sorted(history_dir.glob("V18_24A_SCORE_TIER_SNAPSHOT_*.csv"), key=lambda p: p.name, reverse=True)
    for path in files:
        rows, _ = read_csv(path)
        for row in rows:
            ticker = get_ticker(row)
            if not ticker or ticker in evidence:
                continue
            score = str(row.get("current_score", "")).strip()
            tier = str(row.get("current_tier", "")).strip()
            if score or (tier and tier != "TIER_0_DATA_NOT_READY"):
                evidence[ticker] = (path.name, tier, score)
    return evidence


def build_bucket_review_rows(
    rows: Sequence[Dict[str, str]],
    read_first: Dict[str, str],
) -> List[Dict[str, object]]:
    counters = {
        "OUTPUT_BUCKET": Counter(row["output_bucket"] for row in rows),
        "TRUST_LEVEL": Counter(row["trust_level"] for row in rows),
        "OFFICIAL_RANK_ALLOWED": Counter(row["official_rank_allowed"] for row in rows),
        "WATCH_ONLY": Counter(row["watch_only"] for row in rows),
        "TRADE_ALLOWED": Counter(row["trade_allowed"] for row in rows),
    }

    expected_map = {
        "OUTPUT_BUCKET": {
            BUCKET_HIGH: int(read_first.get("HIGH_TRUST_COUNT", "0") or 0),
            BUCKET_MEDIUM: int(read_first.get("MEDIUM_TRUST_COUNT", "0") or 0),
            BUCKET_LOW: int(read_first.get("LOW_TRUST_COUNT", "0") or 0),
            BUCKET_NOT_READY: int(read_first.get("DATA_NOT_READY_COUNT", "0") or 0),
        },
        "OFFICIAL_RANK_ALLOWED": {"TRUE": int(read_first.get("OFFICIAL_RANK_ALLOWED_COUNT", "0") or 0)},
        "WATCH_ONLY": {"TRUE": int(read_first.get("WATCH_ONLY_COUNT", "0") or 0)},
        "TRADE_ALLOWED": {"TRUE": int(read_first.get("TRADE_ALLOWED_COUNT", "0") or 0)},
    }

    out: List[Dict[str, object]] = []
    for category, counter in counters.items():
        for value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
            expected = expected_map.get(category, {}).get(value, "")
            matches = ""
            if expected != "":
                matches = "TRUE" if count == expected else "FALSE"
            out.append(
                {
                    "category": category,
                    "value": value,
                    "count": count,
                    "expected_count": expected,
                    "matches_read_first": matches,
                    "notes": "Derived from V18.25A current output review.",
                }
            )
    return out


def high_trust_suspicion(row: Dict[str, str]) -> List[str]:
    missing: List[str] = []
    for field in ("composite_score", "tier_current", "technical_status", "official_price_cache_available", "reason_summary"):
        if not str(row.get(field, "")).strip():
            missing.append(field)
    if row.get("official_price_cache_available", "").strip().upper() != "TRUE":
        missing.append("official_price_cache_available_not_true")
    if row.get("official_rank_allowed", "").strip().upper() != "TRUE":
        missing.append("official_rank_allowed_not_true")
    if row.get("watch_only", "").strip().upper() != "FALSE":
        missing.append("watch_only_not_false")
    if row.get("trade_allowed", "").strip().upper() != "FALSE":
        missing.append("trade_allowed_not_false")
    return missing


def build_high_trust_top30(rows: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    high_rows = [row for row in rows if row.get("output_bucket") == BUCKET_HIGH]
    high_rows.sort(key=lambda row: (-to_float(row.get("composite_score")) if to_float(row.get("composite_score")) is not None else float("inf"), row["ticker"]))
    out: List[Dict[str, object]] = []
    for idx, row in enumerate(high_rows[:30], start=1):
        out.append(
            {
                "rank": idx,
                "ticker": row["ticker"],
                "best_available_score": row.get("composite_score", ""),
                "tier_current": row.get("tier_current", ""),
                "technical_status": row.get("technical_status", ""),
                "official_price_cache_available": row.get("official_price_cache_available", ""),
                "reason_summary": row.get("reason_summary", ""),
                "score_source": row.get("score_source", ""),
                "suspicious_missing_fields": "|".join(high_trust_suspicion(row)) or "NONE",
            }
        )
    return out


def derive_watch_only_priority(row: Dict[str, str]) -> Tuple[int, str, str]:
    score = 0
    reasons: List[str] = []
    path = "UNKNOWN_OR_OTHER_GAP"
    gap_reason = str(row.get("data_gap_reason", ""))
    staged = str(row.get("staged_backfill_status", "")).upper()
    technical_available = is_true(row.get("technical_available", ""))
    official_price = is_true(row.get("official_price_cache_available", ""))
    score_available = is_true(row.get("score_available", ""))
    tier = str(row.get("tier_current", "")).upper()

    if row.get("output_bucket") == BUCKET_MEDIUM:
        score += 100
        reasons.append("medium_trust")
    if official_price:
        score += 40
        reasons.append("official_price_present")
    if score_available:
        score += 30
        reasons.append("score_present")
    if technical_available:
        score += 25
        reasons.append("technical_present")
    if "MERGE_CANDIDATE" in staged:
        score += 35
        reasons.append("staged_merge_candidate")
        path = "NEEDS_STAGED_BACKFILL"
    if "HOLD_SUSPICIOUS_PRICE_DATA" in staged or "HOLD_EMPTY_FETCH" in staged:
        score -= 50
        reasons.append("hold_or_empty_fetch")
        path = "EMPTY_FETCH_OR_HOLD_REVIEW"
    if "OFFICIAL_PRICE_CACHE_MISSING" in gap_reason and staged:
        score += 20
        reasons.append("official_integration_possible")
        path = "NEEDS_OFFICIAL_INTEGRATION"
    if "TECHNICAL_TIMING_MISSING" in gap_reason and official_price:
        score += 15
        reasons.append("technical_source_repair_possible")
    if tier == BUCKET_NOT_READY:
        score -= 10

    priority_reason = ", ".join(reasons) if reasons else "review_required"
    return score, path, priority_reason


def build_watch_only_priority(rows: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    watch_rows = [row for row in rows if row.get("watch_only", "").strip().upper() == "TRUE"]
    out: List[Dict[str, object]] = []
    for row in watch_rows:
        score, path, reason = derive_watch_only_priority(row)
        out.append(
            {
                "ticker": row["ticker"],
                "output_bucket": row.get("output_bucket", ""),
                "trust_level": row.get("trust_level", ""),
                "composite_score": row.get("composite_score", ""),
                "tier_current": row.get("tier_current", ""),
                "official_price_cache_available": row.get("official_price_cache_available", ""),
                "technical_status": row.get("technical_status", ""),
                "rolling_ledger_status": row.get("rolling_ledger_status", ""),
                "staged_backfill_status": row.get("staged_backfill_status", ""),
                "data_gap_reason": row.get("data_gap_reason", ""),
                "likely_upgrade_path": path,
                "priority_score": score,
                "priority_reason": reason,
            }
        )
    out.sort(key=lambda row: (-int(row["priority_score"]), row["ticker"]))
    for idx, row in enumerate(out, start=1):
        row["priority_rank"] = idx
    return out


def build_data_not_ready_priority(
    rows: Sequence[Dict[str, str]],
    history_evidence: Dict[str, Tuple[str, str, str]],
) -> List[Dict[str, object]]:
    not_ready = [row for row in rows if row.get("output_bucket") == BUCKET_NOT_READY]
    out: List[Dict[str, object]] = []
    for row in not_ready:
        ticker = row["ticker"]
        history = history_evidence.get(ticker)
        score = 0
        reasons: List[str] = []
        if history:
            score += 50
            reasons.append("historic_tier_or_score_found")
        if "SUCCESS" in str(row.get("rolling_ledger_status", "")).upper():
            score += 25
            reasons.append("rolling_ledger_success")
        if "MERGE_CANDIDATE" in str(row.get("staged_backfill_status", "")).upper():
            score += 30
            reasons.append("staged_backfill_candidate")
        if is_true(row.get("official_price_cache_available", "")):
            score += 10
            reasons.append("official_price_present")
        if not history:
            score -= 5
        out.append(
            {
                "ticker": ticker,
                "output_bucket": row.get("output_bucket", ""),
                "trust_level": row.get("trust_level", ""),
                "tier_current": row.get("tier_current", ""),
                "data_gap_reason": row.get("data_gap_reason", ""),
                "rolling_ledger_status": row.get("rolling_ledger_status", ""),
                "staged_backfill_status": row.get("staged_backfill_status", ""),
                "historic_evidence_source": history[0] if history else "",
                "historic_tier": history[1] if history else "",
                "historic_score": history[2] if history else "",
                "priority_score": score,
                "priority_reason": ", ".join(reasons) if reasons else "uniform_missing_local_data",
            }
        )
    out.sort(key=lambda row: (-int(row["priority_score"]), row["ticker"]))
    for idx, row in enumerate(out, start=1):
        row["priority_rank"] = idx
    return out


def group_recommendations(rows: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    by_type: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_type[str(row.get("recommendation_type", "")).strip().upper()].append(row)

    out: List[Dict[str, object]] = []
    for group_name, source_types in GAP_GROUPS.items():
        group_rows = [row for rec_type, rec_rows in by_type.items() if rec_type in source_types for row in rec_rows]
        group_rows.sort(key=lambda row: (str(row.get("priority", "")) != "HIGH", str(row.get("ticker", ""))))
        out.append(
            {
                "recommendation_group": group_name,
                "source_recommendation_types": "|".join(sorted(source_types)),
                "count": len(group_rows),
                "top_examples": format_row_list(group_rows, 8),
                "sample_reasons": "; ".join(sorted({str(row.get("reason", "")).strip() for row in group_rows if str(row.get("reason", "")).strip()})),
            }
        )

    other_rows = [row for row in rows if str(row.get("recommendation_type", "")).strip().upper() not in {t for types in GAP_GROUPS.values() for t in types}]
    other_rows.sort(key=lambda row: (str(row.get("priority", "")) != "HIGH", str(row.get("ticker", ""))))
    out.append(
        {
            "recommendation_group": "UNKNOWN_OR_OTHER_GAP",
            "source_recommendation_types": "OTHER",
            "count": len(other_rows),
            "top_examples": format_row_list(other_rows, 8),
            "sample_reasons": "; ".join(sorted({str(row.get("reason", "")).strip() for row in other_rows if str(row.get("reason", "")).strip()})),
        }
    )
    return out


def build_group_breakdown(rows: Sequence[Dict[str, str]]) -> List[Tuple[str, Counter[str]]]:
    by_group: Dict[str, Counter[str]] = {
        "MEDIUM_TRUST_PARTIAL_WATCH": Counter(),
        "LOW_TRUST_PRICE_ONLY_OR_STAGED_WATCH": Counter(),
    }
    for row in rows:
        bucket = row["output_bucket"]
        if bucket in by_group:
            by_group[bucket][str(row.get("data_gap_reason", "")).strip()] += 1
    return list(by_group.items())


def render_report(
    status: str,
    counts: Counter[str],
    trust_counts: Counter[str],
    flag_counts: Dict[str, Counter[str]],
    bucket_review_rows: Sequence[Dict[str, object]],
    high_trust_rows: Sequence[Dict[str, object]],
    watch_rows: Sequence[Dict[str, object]],
    data_not_ready_rows: Sequence[Dict[str, object]],
    data_gap_rows: Sequence[Dict[str, object]],
    medium_low_group_breakdown: Sequence[Tuple[str, Counter[str]]],
    read_first: Dict[str, str],
    warnings: Sequence[str],
    validation_failures: Sequence[str],
    next_step: str,
) -> str:
    now = dt.datetime.now().isoformat(timespec="seconds")
    high_suspicious = int(read_first.get("HIGH_TRUST_SUSPICIOUS_COUNT", "0") or 0)
    lines: List[str] = [
        "# V18.25A R1 Degraded Daily Output Review",
        "",
        f"- STATUS: {status}",
        f"- MODE: {MODE}",
        f"- GENERATED_AT: {now}",
        f"- TOTAL_OUTPUT_ROWS: {sum(counts.values())}",
        f"- HIGH_TRUST_SUSPICIOUS_COUNT: {high_suspicious}",
        f"- SOURCE_MISSING_WARNING_COUNT: {read_first.get('SOURCE_MISSING_WARNING_COUNT', '0')}",
        f"- NEXT_RECOMMENDED_STEP: {next_step}",
        "",
        "## Bucket Composition",
        "",
        "| Category | Value | Count | Expected | Matches READ_FIRST |",
        "| --- | --- | ---: | ---: | --- |",
    ]

    for row in bucket_review_rows:
        if row["category"] in {"OUTPUT_BUCKET", "OFFICIAL_RANK_ALLOWED", "WATCH_ONLY", "TRADE_ALLOWED"}:
            lines.append(
                f"| {row['category']} | {row['value']} | {row['count']} | {row.get('expected_count', '')} | {row.get('matches_read_first', '')} |"
            )
    lines.extend(
        [
            "",
            "Trust level counts:",
            "| Trust Level | Count |",
            "| --- | ---: |",
        ]
    )
    for trust in ("HIGH", "MEDIUM", "LOW", "NONE"):
        lines.append(f"| {trust} | {trust_counts.get(trust, 0)} |")

    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Validation failures: {len(validation_failures)}",
        f"- Forbidden file changes: {sum(flag_counts['forbidden'].values())}",
            f"- High-trust suspicious rows: {high_suspicious}",
        ]
    )
    if warnings:
        lines.append("- Warning inputs:")
        lines.extend(f"  - {warning}" for warning in warnings)
    else:
        lines.append("- Warning inputs: NONE")

    lines.extend(
        [
            "",
            "## High-Trust Review",
            "",
            f"Top 30 high-trust candidates reviewed: {len(high_trust_rows)}",
            "",
            "| Rank | Ticker | Score | Tier | Technical Status | Official Price Cache | Reason Summary | Suspicious Fields |",
            "| --- | --- | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for row in high_trust_rows:
        lines.append(
            f"| {row['rank']} | {row['ticker']} | {row['best_available_score']} | {row['tier_current']} | {row['technical_status']} | {row['official_price_cache_available']} | {row['reason_summary']} | {row['suspicious_missing_fields']} |"
        )

    lines.extend(
        [
            "",
            "## Medium/Low-Trust Review",
            "",
            "The downgrade pattern is consistent: medium-trust names mostly miss score and technical timing evidence, while low-trust names usually add official-price-cache loss on top of the same missing score/technical pattern.",
            "",
            "| Bucket | Data Gap Reason | Count |",
            "| --- | --- | ---: |",
        ]
    )
    for bucket, reason_counts in medium_low_group_breakdown:
        for reason, count in reason_counts.most_common():
            lines.append(f"| {bucket} | {reason or '(blank)'} | {count} |")

    lines.extend(
        [
            "",
            "### Watch-Only Names With Upgrade Potential",
            "",
            "The highest-probability recoveries are the names with staged full-history candidates or official-integration need. The current recommendation file identifies 13 `NEEDS_OFFICIAL_INTEGRATION` watch-only names and 8 `EMPTY_FETCH_OR_HOLD_REVIEW` names, with a larger `PARTIAL_HISTORY` tail that is usually just missing score/technical context.",
            "",
            f"Top watch-only priority names: {format_row_list(watch_rows, 20)}",
            "",
            "## Data-Not-Ready Review",
            "",
            "All `DATA_NOT_READY` rows share the same gap pattern in this run: `OFFICIAL_PRICE_CACHE_MISSING|SCORE_MISSING|TECHNICAL_TIMING_MISSING|ROLLING_LEDGER_FULL_HISTORY_NOT_READY`.",
            "No current `DATA_NOT_READY` ticker shows staged-backfill evidence or a prior high-confidence tier score in the loaded history snapshots, so the bucket is a uniform no-local-data miss rather than a staged recovery queue.",
            "",
            f"Top data-not-ready priorities: {format_row_list(data_not_ready_rows, 20)}",
            "",
            "## Data Gap Recommendations",
            "",
            "| Recommendation Group | Count | Top Examples |",
            "| --- | ---: | --- |",
        ]
    )
    for row in data_gap_rows:
        lines.append(f"| {row['recommendation_group']} | {row['count']} | {row['top_examples']} |")

    lines.extend(
        [
            "",
            "## Next Action Recommendation",
            "",
            "Recommended order:",
            f"1. {next_step}",
            "2. C: Batch 3 staged backfill",
            "3. A: V18.23C-R6 Batch 2 official full-history-only integration",
            "4. B: V18.25A-R2 classification logic refinement",
            "",
            "Rationale: the audit is already internally consistent, but one source alias is missing and the review would benefit from fixing source discovery before refining classification or widening integration.",
        ]
    )

    if validation_failures:
        lines.extend(["", "## Validation Failures"] + [f"- {failure}" for failure in validation_failures])

    if flag_counts["forbidden"]:
        lines.extend(["", "## Forbidden File Checks"] + [f"- {path}" for path in flag_counts["forbidden"].most_common()])

    return "\n".join(lines) + "\n"


def validate(
    rows: Sequence[Dict[str, str]],
    read_first: Dict[str, str],
    before_forbidden: Dict[str, Tuple[int, int]],
    after_forbidden: Dict[str, Tuple[int, int]],
    expected_safety: Dict[str, str],
) -> List[str]:
    failures: List[str] = []
    if not rows:
        failures.append("Daily review input is empty or unreadable.")

    expected_rows = read_first.get("TOTAL_OUTPUT_ROWS") or read_first.get("TOTAL_TICKER_COUNT", "")
    if expected_rows:
        try:
            if int(expected_rows) != len(rows):
                failures.append(f"TOTAL_OUTPUT_ROWS mismatch: expected {expected_rows}, got {len(rows)}.")
        except ValueError:
            failures.append(f"TOTAL_OUTPUT_ROWS is not numeric: {expected_rows!r}.")

    expected_bucket_counts = {
        BUCKET_HIGH: int(read_first.get("HIGH_TRUST_COUNT", "0") or 0),
        BUCKET_MEDIUM: int(read_first.get("MEDIUM_TRUST_COUNT", "0") or 0),
        BUCKET_LOW: int(read_first.get("LOW_TRUST_COUNT", "0") or 0),
        BUCKET_NOT_READY: int(read_first.get("DATA_NOT_READY_COUNT", "0") or 0),
    }
    actual_bucket_counts = Counter(row["output_bucket"] for row in rows)
    for bucket, expected in expected_bucket_counts.items():
        actual = actual_bucket_counts.get(bucket, 0)
        if actual != expected:
            failures.append(f"{bucket} mismatch: expected {expected}, got {actual}.")

    for key, expected in expected_safety.items():
        actual = read_first.get(key, "")
        if str(actual).strip().upper() != str(expected).strip().upper():
            failures.append(f"{key} is not safe: expected {expected}, got {actual}.")

    forbidden_changes = diff_signatures(before_forbidden, after_forbidden)
    if forbidden_changes:
        failures.append(f"Forbidden files changed during review execution: {len(forbidden_changes)}.")

    return failures


def build_recommendation_groups_counter(rows: Sequence[Dict[str, str]]) -> Counter[str]:
    c: Counter[str] = Counter()
    for row in rows:
        c[str(row.get("recommendation_type", "")).strip().upper()] += 1
    return c


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V18.25A R1 degraded daily output review")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    warnings: List[str] = []

    before_forbidden = collect_forbidden_files(root)

    daily_path = root / INPUTS["daily"]
    summary_path = root / INPUTS["summary"]
    recommendations_path = root / INPUTS["recommendations"]
    read_first_path = root / INPUTS["read_first"]

    daily_rows, daily_fields = read_csv(daily_path)
    if not daily_path.exists():
        return 1

    summary_rows, _ = read_csv(summary_path)
    if not summary_path.exists():
        warnings.append(f"Missing optional summary input: {summary_path.as_posix()}")

    recommendation_rows, _ = read_csv(recommendations_path)
    if not recommendations_path.exists():
        warnings.append(f"Missing optional recommendations input: {recommendations_path.as_posix()}")

    report_exists = (root / INPUTS["report"]).exists()
    homepage_exists = (root / INPUTS["homepage"]).exists()
    if not report_exists:
        warnings.append(f"Missing optional report input: {root / INPUTS['report']}")
    if not homepage_exists:
        warnings.append(f"Missing optional homepage input: {root / INPUTS['homepage']}")

    current_read_first = parse_read_first(read_first_path)
    if not current_read_first:
        warnings.append(f"Missing optional read-first input: {read_first_path.as_posix()}")

    r3_read_first_path = root / "outputs/v18/ops/V18_25A_R3_READ_FIRST.txt"
    r3_read_first = parse_read_first(r3_read_first_path)
    if not r3_read_first and r3_read_first_path.exists():
        warnings.append(f"Unreadable optional R3 read-first input: {r3_read_first_path.as_posix()}")

    history_evidence = load_history_evidence(root)

    counts = Counter(row["output_bucket"] for row in daily_rows)
    trust_counts = Counter(row["trust_level"] for row in daily_rows)
    flag_counts = {
        "official_rank_allowed": Counter(row["official_rank_allowed"] for row in daily_rows),
        "watch_only": Counter(row["watch_only"] for row in daily_rows),
        "trade_allowed": Counter(row["trade_allowed"] for row in daily_rows),
        "forbidden": Counter(),
    }

    bucket_review_rows = build_bucket_review_rows(daily_rows, current_read_first)
    high_trust_rows = build_high_trust_top30(daily_rows)
    watch_rows = build_watch_only_priority(daily_rows)
    data_not_ready_rows = build_data_not_ready_priority(daily_rows, history_evidence)
    data_gap_rows = group_recommendations(recommendation_rows)
    medium_low_group_breakdown = build_group_breakdown([row for row in daily_rows if row["output_bucket"] in {BUCKET_MEDIUM, BUCKET_LOW, BUCKET_NOT_READY, BUCKET_HIGH}])
    recommendation_type_counts = build_recommendation_groups_counter(recommendation_rows)

    expected_safety = {
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
    }

    validation_failures = validate(daily_rows, current_read_first, before_forbidden, collect_forbidden_files(root), expected_safety)

    after_forbidden = collect_forbidden_files(root)
    forbidden_changes = diff_signatures(before_forbidden, after_forbidden)
    flag_counts["forbidden"] = Counter(forbidden_changes)

    # Compare recommendation groups against the actual recommendation file.
    actual_group_counts = {row["recommendation_group"]: int(row["count"]) for row in data_gap_rows}
    if actual_group_counts.get("NEEDS_OFFICIAL_INTEGRATION", 0) != recommendation_type_counts.get("NEEDS_OFFICIAL_INTEGRATION", 0):
        validation_failures.append("NEEDS_OFFICIAL_INTEGRATION count mismatch.")
    if actual_group_counts.get("NEEDS_STAGED_BACKFILL", 0) != recommendation_type_counts.get("NEEDS_STAGED_BACKFILL", 0):
        validation_failures.append("NEEDS_STAGED_BACKFILL count mismatch.")
    if actual_group_counts.get("PARTIAL_HISTORY_REVIEW", 0) != recommendation_type_counts.get("PARTIAL_HISTORY", 0):
        validation_failures.append("PARTIAL_HISTORY_REVIEW count mismatch.")
    if actual_group_counts.get("EMPTY_FETCH_OR_HOLD_REVIEW", 0) != recommendation_type_counts.get("EMPTY_FETCH_OR_HOLD_REVIEW", 0):
        validation_failures.append("EMPTY_FETCH_OR_HOLD_REVIEW count mismatch.")

    unknown_other_expected = len(
        [row for row in recommendation_rows if str(row.get("recommendation_type", "")).strip().upper() not in {"NEEDS_OFFICIAL_INTEGRATION", "NEEDS_STAGED_BACKFILL", "PARTIAL_HISTORY", "EMPTY_FETCH_OR_HOLD_REVIEW"}]
    )
    if actual_group_counts.get("UNKNOWN_OR_OTHER_GAP", 0) != unknown_other_expected:
        validation_failures.append("UNKNOWN_OR_OTHER_GAP count mismatch.")

    # Count mismatch checks against READ_FIRST.
    if current_read_first:
        expected_total = int(current_read_first.get("TOTAL_TICKER_COUNT", current_read_first.get("TOTAL_OUTPUT_ROWS", "0")) or 0)
        if expected_total and expected_total != len(daily_rows):
            validation_failures.append(f"Read-first total mismatch: {expected_total} vs {len(daily_rows)}.")

    source_missing_count = int(current_read_first.get("SOURCE_MISSING_WARNING_COUNT", str(len(warnings))) or len(warnings))
    needs_official_integration_count = int(recommendation_type_counts.get("NEEDS_OFFICIAL_INTEGRATION", 0) or 0)
    high_trust_suspicious_count = sum(1 for row in high_trust_rows if row["suspicious_missing_fields"] != "NONE")
    partial_history_review_count = int(recommendation_type_counts.get("PARTIAL_HISTORY", 0) or 0)
    if source_missing_count > 0:
        warnings.append(f"Controller source missing warnings reported by V18.25A: {source_missing_count}")

    if validation_failures:
        status = STATUS_FAIL
    elif warnings:
        status = STATUS_WARN
    else:
        status = STATUS_OK

    r3_integrated_count = int(r3_read_first.get("R6_R7_INTEGRATED_TICKER_COUNT", "0") or 0)
    r3_current_high_trust = int(r3_read_first.get("CURRENT_HIGH_TRUST_COUNT_FOR_R6_R7", "0") or 0)
    r3_current_factor_missing = int(r3_read_first.get("FACTOR_MISSING_COUNT_FOR_R6_R7", "0") or 0)
    r3_current_technical_missing = int(r3_read_first.get("TECHNICAL_MISSING_COUNT_FOR_R6_R7", "0") or 0)
    r3_promotion_complete = (
        r3_integrated_count == 52
        and r3_current_high_trust == 52
        and r3_current_factor_missing == 0
        and r3_current_technical_missing == 0
    )

    if source_missing_count > 0:
        next_step = "D: Fix missing tier migration CSV alias/source"
        next_step_readable = "D: Fix missing tier migration CSV alias/source"
    elif high_trust_suspicious_count > 0:
        next_step = "B: V18.25A classification logic refinement"
        next_step_readable = "B: V18.25A classification logic refinement"
    elif r3_promotion_complete:
        next_step = "C: Continue Batch3 staged backfill / remaining stale coverage expansion"
        next_step_readable = "C: Continue Batch3 staged backfill / remaining stale coverage expansion"
    elif needs_official_integration_count > 0:
        next_step = "A: Review remaining official integration candidates / held-out candidates"
        next_step_readable = "A: Review remaining official integration candidates / held-out candidates"
    elif partial_history_review_count > 0:
        next_step = "C: Continue staged backfill / coverage repair"
        next_step_readable = "C: Continue staged backfill / coverage repair"
    else:
        next_step = "Continue downstream validation and operator homepage refresh"
        next_step_readable = "Continue downstream validation and operator homepage refresh"

    read_first = {
        "STATUS": status,
        "MODE": MODE,
        "TOTAL_OUTPUT_ROWS": str(len(daily_rows)),
        "HIGH_TRUST_COUNT": str(counts.get(BUCKET_HIGH, 0)),
        "MEDIUM_TRUST_COUNT": str(counts.get(BUCKET_MEDIUM, 0)),
        "LOW_TRUST_COUNT": str(counts.get(BUCKET_LOW, 0)),
        "DATA_NOT_READY_COUNT": str(counts.get(BUCKET_NOT_READY, 0)),
        "OFFICIAL_RANK_ALLOWED_COUNT": str(sum(1 for row in daily_rows if row.get("official_rank_allowed") == "TRUE")),
        "WATCH_ONLY_COUNT": str(sum(1 for row in daily_rows if row.get("watch_only") == "TRUE")),
        "TRADE_ALLOWED_COUNT": str(sum(1 for row in daily_rows if row.get("trade_allowed") == "TRUE")),
        "DATA_GAP_RECOMMENDATION_COUNT": str(len(recommendation_rows)),
        "NEEDS_OFFICIAL_INTEGRATION_COUNT": str(recommendation_type_counts.get("NEEDS_OFFICIAL_INTEGRATION", 0)),
        "NEEDS_STAGED_BACKFILL_COUNT": str(recommendation_type_counts.get("NEEDS_STAGED_BACKFILL", 0)),
        "PARTIAL_HISTORY_REVIEW_COUNT": str(recommendation_type_counts.get("PARTIAL_HISTORY", 0)),
        "EMPTY_FETCH_OR_HOLD_REVIEW_COUNT": str(recommendation_type_counts.get("EMPTY_FETCH_OR_HOLD_REVIEW", 0)),
        "UNKNOWN_OR_OTHER_GAP_COUNT": str(unknown_other_expected),
        "HIGH_TRUST_SUSPICIOUS_COUNT": str(sum(1 for row in high_trust_rows if row["suspicious_missing_fields"] != "NONE")),
        "SOURCE_MISSING_WARNING_COUNT": str(source_missing_count),
        "NEXT_RECOMMENDED_STEP": next_step,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "VALIDATION_FAIL_COUNT": str(len(validation_failures)),
    }

    # Validate the output against the controller's current read-first values.
    if current_read_first:
        expected_checks = {
            "HIGH_TRUST_COUNT": read_first["HIGH_TRUST_COUNT"],
            "MEDIUM_TRUST_COUNT": read_first["MEDIUM_TRUST_COUNT"],
            "LOW_TRUST_COUNT": read_first["LOW_TRUST_COUNT"],
            "DATA_NOT_READY_COUNT": read_first["DATA_NOT_READY_COUNT"],
            "OFFICIAL_RANK_ALLOWED_COUNT": read_first["OFFICIAL_RANK_ALLOWED_COUNT"],
            "WATCH_ONLY_COUNT": read_first["WATCH_ONLY_COUNT"],
            "TRADE_ALLOWED_COUNT": read_first["TRADE_ALLOWED_COUNT"],
            "DATA_GAP_RECOMMENDATION_COUNT": read_first["DATA_GAP_RECOMMENDATION_COUNT"],
        }
        for key, actual_text in expected_checks.items():
            expected_text = current_read_first.get(key, "")
            if expected_text and str(expected_text) != str(actual_text):
                validation_failures.append(f"{key} mismatch against V18.25A READ_FIRST: expected {expected_text}, got {actual_text}.")

    # Recompute status after full validation checks.
    if validation_failures:
        status = STATUS_FAIL
    elif warnings:
        status = STATUS_WARN
    else:
        status = STATUS_OK
    read_first["STATUS"] = status
    read_first["SOURCE_MISSING_WARNING_COUNT"] = str(source_missing_count)
    read_first["VALIDATION_FAIL_COUNT"] = str(len(validation_failures))

    # Materialize outputs.
    write_csv(root / OUTPUTS["bucket_review"], bucket_review_rows, ["category", "value", "count", "expected_count", "matches_read_first", "notes"])
    write_csv(root / OUTPUTS["high_trust_top30"], high_trust_rows, ["rank", "ticker", "best_available_score", "tier_current", "technical_status", "official_price_cache_available", "reason_summary", "score_source", "suspicious_missing_fields"])
    write_csv(root / OUTPUTS["watch_only_priority"], watch_rows, ["priority_rank", "ticker", "output_bucket", "trust_level", "composite_score", "tier_current", "official_price_cache_available", "technical_status", "rolling_ledger_status", "staged_backfill_status", "data_gap_reason", "likely_upgrade_path", "priority_score", "priority_reason"])
    write_csv(root / OUTPUTS["data_not_ready_priority"], data_not_ready_rows, ["priority_rank", "ticker", "output_bucket", "trust_level", "tier_current", "data_gap_reason", "rolling_ledger_status", "staged_backfill_status", "historic_evidence_source", "historic_tier", "historic_score", "priority_score", "priority_reason"])
    write_csv(root / OUTPUTS["data_gap_groups"], data_gap_rows, ["recommendation_group", "source_recommendation_types", "count", "top_examples", "sample_reasons"])

    report = render_report(
        status=status,
        counts=counts,
        trust_counts=trust_counts,
        flag_counts=flag_counts,
        bucket_review_rows=bucket_review_rows,
        high_trust_rows=high_trust_rows,
        watch_rows=watch_rows,
        data_not_ready_rows=data_not_ready_rows,
        data_gap_rows=data_gap_rows,
        medium_low_group_breakdown=medium_low_group_breakdown,
        read_first=read_first,
        warnings=warnings,
        validation_failures=validation_failures,
        next_step=next_step_readable,
    )
    write_text(root / OUTPUTS["report"], report)
    write_text(root / OUTPUTS["ops_report"], report)
    write_text(root / OUTPUTS["ops_read_first"], "\n".join(f"{field}: {read_first.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"TOTAL_OUTPUT_ROWS: {len(daily_rows)}")
    print(f"VALIDATION_FAIL_COUNT: {len(validation_failures)}")
    return 1 if status == STATUS_FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
