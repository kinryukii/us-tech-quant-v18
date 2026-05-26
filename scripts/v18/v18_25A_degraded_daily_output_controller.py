from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


MODE = "READ_ONLY_DEGRADED_DAILY_OUTPUT_CONTROLLER"
STATUS_OK = "OK_V18_25A_DEGRADED_DAILY_OUTPUT_CONTROLLER_READY"
STATUS_WARN = "WARN_V18_25A_DEGRADED_DAILY_OUTPUT_CONTROLLER_READY"
STATUS_FAIL = "FAIL_V18_25A_DEGRADED_DAILY_OUTPUT_CONTROLLER"

BUCKET_HIGH = "HIGH_TRUST_OFFICIAL_RANK_CANDIDATE"
BUCKET_MEDIUM = "MEDIUM_TRUST_PARTIAL_WATCH"
BUCKET_LOW = "LOW_TRUST_PRICE_ONLY_OR_STAGED_WATCH"
BUCKET_NOT_READY = "DATA_NOT_READY"

OUTPUTS = {
    "daily": "outputs/v18/degraded_daily/V18_25A_CURRENT_DEGRADED_DAILY_OUTPUT.csv",
    "summary": "outputs/v18/degraded_daily/V18_25A_CURRENT_DEGRADED_DAILY_SUMMARY.csv",
    "recommendations": "outputs/v18/degraded_daily/V18_25A_CURRENT_DATA_GAP_RECOMMENDATIONS.csv",
    "report": "outputs/v18/degraded_daily/V18_25A_CURRENT_DEGRADED_DAILY_REPORT.md",
    "homepage": "outputs/v18/operator_homepage/V18_25A_CURRENT_DEGRADED_DAILY_OPERATOR_HOMEPAGE.md",
    "read_first": "outputs/v18/ops/V18_25A_READ_FIRST.txt",
    "ops_report": "outputs/v18/ops/V18_25A_CURRENT_DEGRADED_DAILY_OUTPUT_CONTROLLER_REPORT.md",
}

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

SUMMARY_FIELDS = ["metric", "value"]
RECOMMENDATION_FIELDS = ["ticker", "recommendation_type", "priority", "reason", "known_tier", "known_score"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "TOTAL_TICKER_COUNT",
    "HIGH_TRUST_COUNT",
    "MEDIUM_TRUST_COUNT",
    "LOW_TRUST_COUNT",
    "DATA_NOT_READY_COUNT",
    "OFFICIAL_RANK_ALLOWED_COUNT",
    "WATCH_ONLY_COUNT",
    "TRADE_ALLOWED_COUNT",
    "SOURCE_MISSING_WARNING_COUNT",
    "DATA_GAP_RECOMMENDATION_COUNT",
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

SAFETY_DEFAULTS = {
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

SOURCE_PATHS = {
    "factor_pack": "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    "technical_timing": "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
    "rolling_ledger": "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv",
    "tier_migration_snapshot": "outputs/v18/tier_migration/V18_24A_CURRENT_SCORE_TIER_SNAPSHOT.csv",
    "tier_migration_audit": "outputs/v18/tier_migration/V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT.csv",
    "staged_r5_quality": "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_TICKER_QUALITY_AUDIT.csv",
    "staged_r5_merge_candidates": "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_MERGE_CANDIDATES.csv",
    "staged_r5_hold_review": "outputs/v18/staged_backfill/V18_23C_R5_CURRENT_BATCH2_HOLD_REVIEW_TICKERS.csv",
}

FORBIDDEN_SCOPES = {
    "PRICE_CACHE_MODIFIED": ["state/v18/price_cache"],
    "PRICE_HISTORY_MODIFIED": ["data/v18/price_history", "state/v18/price_history"],
    "STAGED_BACKFILL_MODIFIED": ["data/v18/staged_backfill", "outputs/v18/staged_backfill"],
    "LEDGER_MODIFIED": ["state/v18/rolling_coverage"],
    "FACTOR_PACK_MODIFIED": ["outputs/v18/factor_pack"],
    "TECHNICAL_TIMING_MODIFIED": ["outputs/v18/technical_timing"],
    "OFFICIAL_DAILY_DECISION_MODIFIED": ["outputs/v18/daily_integrated"],
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


def get_first(row: Dict[str, str], keys: Iterable[str], default: str = "") -> str:
    lower = {key.lower(): key for key in row}
    for key in keys:
        real = lower.get(key.lower())
        if real is not None:
            value = str(row.get(real, "")).strip()
            if value:
                return value
    return default


def to_float(value: object) -> float | None:
    try:
        text = str(value).replace(",", "").strip()
        if not text:
            return None
        return float(text)
    except ValueError:
        return None


def trueish(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "YES", "Y", "1", "AVAILABLE", "PASS", "SUCCESS"}


def file_signature(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return (stat.st_mtime_ns, stat.st_size)


def collect_scope_signatures(root: Path) -> Dict[str, Dict[str, Tuple[int, int]]]:
    signatures: Dict[str, Dict[str, Tuple[int, int]]] = {}
    for flag, rel_dirs in FORBIDDEN_SCOPES.items():
        scoped: Dict[str, Tuple[int, int]] = {}
        for rel_dir in rel_dirs:
            base = root / rel_dir
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if path.is_file():
                    scoped[str(path.relative_to(root)).replace("\\", "/")] = file_signature(path)
        signatures[flag] = scoped
    return signatures


def diff_scope_signatures(before: Dict[str, Dict[str, Tuple[int, int]]], after: Dict[str, Dict[str, Tuple[int, int]]]) -> Dict[str, List[str]]:
    changed: Dict[str, List[str]] = {}
    for flag, before_files in before.items():
        after_files = after.get(flag, {})
        paths = sorted(set(before_files) | set(after_files))
        hits = [path for path in paths if before_files.get(path) != after_files.get(path)]
        changed[flag] = hits
    return changed


def index_by_ticker(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    indexed: Dict[str, Dict[str, str]] = {}
    for row in rows:
        ticker = get_ticker(row)
        if ticker and ticker not in indexed:
            indexed[ticker] = row
    return indexed


def load_sources(root: Path) -> Tuple[Dict[str, Dict[str, Dict[str, str]]], List[str], List[str]]:
    indexed_sources: Dict[str, Dict[str, Dict[str, str]]] = {}
    missing_warnings: List[str] = []
    source_notes: List[str] = []

    for source_name, rel_path in SOURCE_PATHS.items():
        path = root / rel_path
        rows, fields = read_csv(path)
        if not path.exists():
            missing_warnings.append(f"{source_name}: missing {rel_path}")
            indexed_sources[source_name] = {}
            continue
        indexed_sources[source_name] = index_by_ticker(rows)
        source_notes.append(f"{source_name}: exists rows={len(rows)} indexed_tickers={len(indexed_sources[source_name])}")

    latest_tier_files = sorted((root / "outputs/v18/tier_migration").glob("V18_24*_CURRENT_*.csv"), key=lambda p: p.stat().st_mtime_ns if p.exists() else 0, reverse=True)
    if latest_tier_files:
        for path in latest_tier_files:
            rows, _fields = read_csv(path)
            indexed = index_by_ticker(rows)
            if indexed:
                indexed_sources[f"tier_latest:{path.name}"] = indexed
                source_notes.append(f"tier_latest:{path.name}: rows={len(rows)} indexed_tickers={len(indexed)}")
                break

    staged_extra_files = sorted((root / "outputs/v18/staged_backfill").glob("V18_23C_R5_*.csv"))
    for path in staged_extra_files:
        key = f"staged_extra:{path.name}"
        if key in indexed_sources:
            continue
        rows, _fields = read_csv(path)
        indexed = index_by_ticker(rows)
        if indexed:
            indexed_sources[key] = indexed

    return indexed_sources, missing_warnings, source_notes


def price_cache_tickers(root: Path) -> set[str]:
    cache_dir = root / "state/v18/price_cache"
    if not cache_dir.exists():
        return set()
    return {path.stem.upper() for path in cache_dir.glob("*.csv") if path.is_file() and path.stat().st_size > 128}


def score_for_ticker(ticker: str, factor: Dict[str, Dict[str, str]], tier: Dict[str, Dict[str, str]]) -> Tuple[bool, str, str]:
    factor_row = factor.get(ticker, {})
    score = get_first(factor_row, ["composite_score", "factor_pack_score", "score", "total_score"])
    if score and to_float(score) is not None:
        return True, score, "factor_pack"
    tier_row = tier.get(ticker, {})
    score = get_first(tier_row, ["current_score", "factor_pack_score", "technical_timing_score", "score"])
    if score and to_float(score) is not None:
        return True, score, "tier_migration"
    return False, "", ""


def build_daily_rows(root: Path, sources: Dict[str, Dict[str, Dict[str, str]]]) -> List[Dict[str, object]]:
    factor = sources.get("factor_pack", {})
    technical = sources.get("technical_timing", {})
    ledger = sources.get("rolling_ledger", {})
    tier = sources.get("tier_migration_snapshot", {})
    staged_quality = sources.get("staged_r5_quality", {})
    staged_merge = sources.get("staged_r5_merge_candidates", {})
    staged_hold = sources.get("staged_r5_hold_review", {})
    official_price = price_cache_tickers(root)

    tickers = set(official_price)
    for indexed in sources.values():
        tickers.update(indexed.keys())

    rows: List[Dict[str, object]] = []
    for ticker in sorted(tickers):
        score_available, score, score_source = score_for_ticker(ticker, factor, tier)
        technical_row = technical.get(ticker, {})
        ledger_row = ledger.get(ticker, {})
        tier_row = tier.get(ticker, {})
        staged_row = staged_quality.get(ticker, {}) or staged_merge.get(ticker, {}) or staged_hold.get(ticker, {})

        technical_available = ticker in technical
        official_price_available = ticker in official_price
        staged_available = bool(staged_row)

        tier_current = get_first(tier_row, ["current_tier", "tier_current", "tier"], "")
        technical_status = get_first(technical_row, ["technical_signal", "technical_status", "technical_warning_label"], "")
        rolling_status = get_first(ledger_row, ["last_scan_status", "data_readiness_status", "failure_reason"], "")
        staged_status = get_first(staged_row, ["classification", "recommended_integration_action", "dry_run_action", "fetch_status"], "")

        gaps: List[str] = []
        if not official_price_available:
            gaps.append("OFFICIAL_PRICE_CACHE_MISSING")
        if not score_available:
            gaps.append("SCORE_MISSING")
        if not technical_available:
            gaps.append("TECHNICAL_TIMING_MISSING")
        if ledger_row and not trueish(get_first(ledger_row, ["full_history_ready"], "")):
            gaps.append("ROLLING_LEDGER_FULL_HISTORY_NOT_READY")
        if staged_status and any(token in staged_status.upper() for token in ("HOLD", "INSUFFICIENT", "BLOCK")):
            gaps.append("STAGED_BACKFILL_HOLD_OR_PARTIAL")

        has_major_gap = bool({"OFFICIAL_PRICE_CACHE_MISSING", "SCORE_MISSING"} & set(gaps))
        evidence_count = sum([score_available, technical_available, official_price_available, staged_available])

        if official_price_available and score_available and not has_major_gap:
            bucket = BUCKET_HIGH
            trust = "HIGH"
            official_rank_allowed = "TRUE"
            watch_only = "FALSE"
        elif evidence_count >= 2 and (score_available or technical_available or official_price_available):
            bucket = BUCKET_MEDIUM
            trust = "MEDIUM"
            official_rank_allowed = "FALSE"
            watch_only = "TRUE"
        elif evidence_count >= 1:
            bucket = BUCKET_LOW
            trust = "LOW"
            official_rank_allowed = "FALSE"
            watch_only = "TRUE"
        else:
            bucket = BUCKET_NOT_READY
            trust = "NONE"
            official_rank_allowed = "FALSE"
            watch_only = "FALSE"

        if not gaps:
            gaps.append("NO_MAJOR_DATA_GAP_DETECTED")
        reason_summary = "; ".join(
            [
                f"score={'yes' if score_available else 'no'}",
                f"technical={'yes' if technical_available else 'no'}",
                f"official_price={'yes' if official_price_available else 'no'}",
                f"staged={'yes' if staged_available else 'no'}",
                f"bucket={bucket}",
            ]
        )

        rows.append(
            {
                "ticker": ticker,
                "output_bucket": bucket,
                "trust_level": trust,
                "score_available": "TRUE" if score_available else "FALSE",
                "composite_score": score,
                "score_source": score_source,
                "tier_current": tier_current,
                "technical_available": "TRUE" if technical_available else "FALSE",
                "technical_status": technical_status,
                "official_price_cache_available": "TRUE" if official_price_available else "FALSE",
                "rolling_ledger_status": rolling_status,
                "staged_backfill_status": staged_status,
                "data_gap_reason": "|".join(gaps),
                "official_rank_allowed": official_rank_allowed,
                "watch_only": watch_only,
                "trade_allowed": "FALSE",
                "reason_summary": reason_summary,
            }
        )
    return rows


def build_recommendations(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    recommendations: List[Dict[str, object]] = []
    for row in rows:
        ticker = str(row["ticker"])
        gaps = str(row.get("data_gap_reason", ""))
        staged = str(row.get("staged_backfill_status", "")).upper()
        tier = str(row.get("tier_current", ""))
        score = str(row.get("composite_score", ""))
        important = bool(score or tier.startswith(("TIER_1", "TIER_2", "TIER_3")))

        if row.get("official_price_cache_available") == "FALSE" and staged:
            recommendations.append(make_reco(ticker, "NEEDS_OFFICIAL_INTEGRATION", "HIGH", "Staged evidence exists but official price cache is unavailable.", tier, score))
        if "TECHNICAL_TIMING_MISSING" in gaps and row.get("score_available") == "TRUE":
            recommendations.append(make_reco(ticker, "NEEDS_STAGED_BACKFILL", "MEDIUM", "Score exists but technical timing/local history evidence is incomplete.", tier, score))
        if "HOLD" in staged or "EMPTY" in staged or "NO_DATA" in staged:
            recommendations.append(make_reco(ticker, "EMPTY_FETCH_OR_HOLD_REVIEW", "HIGH", f"Staged status requires review: {staged}", tier, score))
        if "PARTIAL" in gaps or "INSUFFICIENT" in staged or "FULL_HISTORY_NOT_READY" in gaps:
            recommendations.append(make_reco(ticker, "PARTIAL_HISTORY", "MEDIUM", "History is partial or full-history readiness is not confirmed.", tier, score))
        if row.get("output_bucket") == BUCKET_NOT_READY and important:
            recommendations.append(make_reco(ticker, "NOT_READY_BUT_PREVIOUSLY_IMPORTANT", "HIGH", "Ticker is not ready but has previous score or tier importance.", tier, score))

    seen: set[Tuple[str, str]] = set()
    unique: List[Dict[str, object]] = []
    for reco in recommendations:
        key = (str(reco["ticker"]), str(reco["recommendation_type"]))
        if key not in seen:
            seen.add(key)
            unique.append(reco)
    return unique


def make_reco(ticker: str, reco_type: str, priority: str, reason: str, tier: str, score: str) -> Dict[str, object]:
    return {
        "ticker": ticker,
        "recommendation_type": reco_type,
        "priority": priority,
        "reason": reason,
        "known_tier": tier,
        "known_score": score,
    }


def render_report(rows: Sequence[Dict[str, object]], recommendations: Sequence[Dict[str, object]], missing: Sequence[str], status: str) -> str:
    counts = Counter(str(row["output_bucket"]) for row in rows)
    now = dt.datetime.now().isoformat(timespec="seconds")
    lines = [
        "# V18.25A Degraded Daily Output Controller",
        "",
        f"- STATUS: {status}",
        f"- MODE: {MODE}",
        f"- GENERATED_AT: {now}",
        f"- OFFICIAL_DECISION_IMPACT: NONE",
        f"- TOTAL_TICKER_COUNT: {len(rows)}",
        f"- HIGH_TRUST_COUNT: {counts.get(BUCKET_HIGH, 0)}",
        f"- MEDIUM_TRUST_COUNT: {counts.get(BUCKET_MEDIUM, 0)}",
        f"- LOW_TRUST_COUNT: {counts.get(BUCKET_LOW, 0)}",
        f"- DATA_NOT_READY_COUNT: {counts.get(BUCKET_NOT_READY, 0)}",
        f"- DATA_GAP_RECOMMENDATION_COUNT: {len(recommendations)}",
        "",
        "Trading gates remain strict: this controller never creates buy permission, auto-trade permission, auto-sell permission, or official daily decision impact.",
        "",
        "## Missing Source Warnings",
    ]
    if missing:
        lines.extend(f"- {warning}" for warning in missing)
    else:
        lines.append("- NONE")
    return "\n".join(lines) + "\n"


def validate(rows: Sequence[Dict[str, object]], source_ticker_count: int, safety: Dict[str, str], changed: Dict[str, List[str]]) -> List[str]:
    failures: List[str] = []
    if source_ticker_count > 0 and not rows:
        failures.append("Output CSV would be empty despite available ticker sources.")
    if any(str(row.get("trade_allowed")) != "FALSE" for row in rows):
        failures.append("At least one row has trade_allowed not FALSE.")
    if safety.get("OFFICIAL_DECISION_IMPACT") != "NONE":
        failures.append("OFFICIAL_DECISION_IMPACT is not NONE.")
    for flag in FORBIDDEN_SCOPES:
        if changed.get(flag):
            failures.append(f"{flag} changed files: {len(changed[flag])}")
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V18.25A degraded daily output controller")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    before = collect_scope_signatures(root)

    sources, missing_warnings, source_notes = load_sources(root)
    rows = build_daily_rows(root, sources)
    recommendations = build_recommendations(rows)
    source_ticker_count = len({ticker for indexed in sources.values() for ticker in indexed})

    after = collect_scope_signatures(root)
    changed = diff_scope_signatures(before, after)
    safety = dict(SAFETY_DEFAULTS)
    for flag, hits in changed.items():
        safety[flag] = "TRUE" if hits else "FALSE"

    validation_failures = validate(rows, source_ticker_count, safety, changed)
    status = STATUS_FAIL if validation_failures else (STATUS_WARN if missing_warnings else STATUS_OK)

    counts = Counter(str(row["output_bucket"]) for row in rows)
    read_first = {
        "STATUS": status,
        "MODE": MODE,
        "TOTAL_TICKER_COUNT": str(len(rows)),
        "HIGH_TRUST_COUNT": str(counts.get(BUCKET_HIGH, 0)),
        "MEDIUM_TRUST_COUNT": str(counts.get(BUCKET_MEDIUM, 0)),
        "LOW_TRUST_COUNT": str(counts.get(BUCKET_LOW, 0)),
        "DATA_NOT_READY_COUNT": str(counts.get(BUCKET_NOT_READY, 0)),
        "OFFICIAL_RANK_ALLOWED_COUNT": str(sum(1 for row in rows if row.get("official_rank_allowed") == "TRUE")),
        "WATCH_ONLY_COUNT": str(sum(1 for row in rows if row.get("watch_only") == "TRUE")),
        "TRADE_ALLOWED_COUNT": str(sum(1 for row in rows if row.get("trade_allowed") == "TRUE")),
        "SOURCE_MISSING_WARNING_COUNT": str(len(missing_warnings)),
        "DATA_GAP_RECOMMENDATION_COUNT": str(len(recommendations)),
        **safety,
        "VALIDATION_FAIL_COUNT": str(len(validation_failures)),
    }

    summary_rows = [{"metric": key, "value": value} for key, value in read_first.items()]
    summary_rows.extend({"metric": f"SOURCE_{idx}", "value": note} for idx, note in enumerate(source_notes, start=1))
    summary_rows.extend({"metric": f"VALIDATION_FAILURE_{idx}", "value": failure} for idx, failure in enumerate(validation_failures, start=1))

    write_csv(root / OUTPUTS["daily"], rows, DAILY_FIELDS)
    write_csv(root / OUTPUTS["summary"], summary_rows, SUMMARY_FIELDS)
    write_csv(root / OUTPUTS["recommendations"], recommendations, RECOMMENDATION_FIELDS)
    report = render_report(rows, recommendations, missing_warnings, status)
    write_text(root / OUTPUTS["report"], report)
    write_text(root / OUTPUTS["homepage"], report)
    write_text(root / OUTPUTS["ops_report"], report)
    write_text(root / OUTPUTS["read_first"], "\n".join(f"{field}: {read_first.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"TOTAL_TICKER_COUNT: {len(rows)}")
    print(f"VALIDATION_FAIL_COUNT: {len(validation_failures)}")
    return 1 if status == STATUS_FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
