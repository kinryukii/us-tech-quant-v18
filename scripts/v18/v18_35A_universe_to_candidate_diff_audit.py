#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable


STATUS_OK = "OK_V18_35A_UNIVERSE_TO_CANDIDATE_AUDIT_READY"
STATUS_WARN = "WARN_V18_35A_UNIVERSE_TO_CANDIDATE_AUDIT_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_35A_UNIVERSE_TO_CANDIDATE_AUDIT_FAILED"

AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

BUCKETS = [
    "NOT_RECENTLY_SCANNED",
    "PRICE_DATA_UNAVAILABLE",
    "PRICE_STALE_OR_NOT_LATEST",
    "FACTOR_PACK_MISSING",
    "TECHNICAL_TIMING_MISSING",
    "HISTORY_INSUFFICIENT_OR_LATEST_ONLY",
    "FILTERED_BY_CURRENT_CANDIDATE_RULES",
    "PRESENT_IN_CANDIDATE_BUT_NOT_FREEZE",
    "ORPHAN_CANDIDATE_NOT_IN_TOTAL_UNIVERSE",
    "UNKNOWN_INSUFFICIENT_EVIDENCE",
    "IN_CURRENT_CANDIDATES",
    "IN_FREEZE_NOT_CANDIDATE",
]


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def run_id() -> str:
    return "V18_35A_" + datetime.now().strftime("%Y%m%d_%H%M%S")


def rel(root: Path, path: Path | None) -> str:
    if path is None:
        return "MISSING"
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def read_csv_rows(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def pick_existing(root: Path, candidates: list[str]) -> Path | None:
    for item in candidates:
        path = root / item
        if path.exists():
            return path
    return None


def pick_candidate_source(root: Path, expected_count: int | None) -> Path | None:
    candidates = [
        "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
        "outputs/v18/candidates/V18_RESTORED_RANKED_CANDIDATES_FROM_R29C_SNAPSHOT.csv",
        "outputs/v18/candidates/V18_25A_R27J_CURRENT_RANKED_CANDIDATES_PREVIEW.csv",
        "outputs/v18/candidates/V18_25A_R25F_CURRENT_RANKED_CANDIDATES_PREVIEW.csv",
    ]
    existing = [root / item for item in candidates if (root / item).exists()]
    if not existing:
        return None
    if expected_count:
        for path in existing:
            rows = read_csv_rows(path)
            if len(extract_set(rows, ["ticker"])) == expected_count:
                return path
    return existing[0]


def first_present(row: dict[str, str], names: list[str], default: str = "") -> str:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return str(value)
    return default


def truthy(value: str) -> bool:
    return str(value).strip().upper() in {"TRUE", "YES", "1", "Y"}


def extract_set(rows: list[dict[str, str]], ticker_cols: list[str]) -> set[str]:
    values: set[str] = set()
    for row in rows:
        ticker = norm_ticker(first_present(row, ticker_cols))
        if ticker:
            values.add(ticker)
    return values


def latest_freeze_set(rows: list[dict[str, str]]) -> tuple[str, set[str], int]:
    by_date: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        signal_date = str(row.get("signal_date", "")).strip()
        ticker = norm_ticker(row.get("ticker"))
        if signal_date and ticker:
            by_date.setdefault(signal_date, []).append(row)
    if not by_date:
        return "UNKNOWN", set(), 0
    latest_date = sorted(by_date)[-1]
    tickers = {norm_ticker(row.get("ticker")) for row in by_date[latest_date] if norm_ticker(row.get("ticker"))}
    return latest_date, tickers, len(by_date[latest_date])


def build_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        ticker = norm_ticker(row.get("ticker") or row.get("yf_ticker"))
        if ticker:
            indexed[ticker] = row
    return indexed


def determine_bucket(
    ticker: str,
    in_total: bool,
    in_candidates: bool,
    in_freeze: bool,
    in_factor: bool,
    in_timing: bool,
    in_recent_scan: bool,
    universe_row: dict[str, str],
    rolling_row: dict[str, str],
) -> tuple[str, str]:
    if in_candidates and not in_total:
        return "ORPHAN_CANDIDATE_NOT_IN_TOTAL_UNIVERSE", "Candidate ticker is not present in the total rolling universe source."
    if in_candidates and not in_freeze:
        return "PRESENT_IN_CANDIDATE_BUT_NOT_FREEZE", "Ticker is in current candidates but absent from the latest signal freeze."
    if in_candidates:
        return "IN_CURRENT_CANDIDATES", "Ticker is present in current ranked candidates."
    if in_freeze and not in_candidates:
        return "IN_FREEZE_NOT_CANDIDATE", "Ticker is present in latest freeze but absent from current ranked candidates."

    scan_status = first_present(rolling_row, ["last_scan_status"])
    selected_this_run = first_present(universe_row, ["selected_this_run"])
    last_scan_date = first_present(universe_row, ["last_scan_date"]) or first_present(rolling_row, ["last_success_scan_date", "last_attempt_scan_date"])
    price_cache_status = first_present(universe_row, ["price_cache_status"]) or first_present(rolling_row, ["local_price_available"])
    price_freshness_status = first_present(universe_row, ["price_freshness_status"])
    actual_depth = first_present(universe_row, ["actual_data_depth"])
    full_history_ready = first_present(rolling_row, ["full_history_ready"])

    if not in_recent_scan and not last_scan_date:
        return "NOT_RECENTLY_SCANNED", "No current scan-plan selection and no last scan date evidence was found."
    if price_cache_status in {"NOT_AVAILABLE", "MISSING", "UNAVAILABLE", "FALSE"} or scan_status.startswith("FAIL"):
        return "PRICE_DATA_UNAVAILABLE", "Price/cache evidence indicates unavailable or failed local scan data."
    if price_freshness_status and price_freshness_status not in {"OK", "FRESH", "LATEST", "NOT_UPDATED_BY_V18_16A"}:
        return "PRICE_STALE_OR_NOT_LATEST", f"Price freshness status is {price_freshness_status}."
    if not in_factor:
        return "FACTOR_PACK_MISSING", "Ticker is absent from the current factor-pack ranking evidence."
    if not in_timing:
        return "TECHNICAL_TIMING_MISSING", "Ticker is absent from the current technical-timing evidence."
    if actual_depth in {"LIGHT_DATA", "LATEST_ONLY", "UNKNOWN_NOT_UPDATED"} or full_history_ready == "FALSE":
        return "HISTORY_INSUFFICIENT_OR_LATEST_ONLY", "History depth evidence is insufficient or latest-only."

    universe_tier = first_present(universe_row, ["universe_tier"], "UNKNOWN")
    promotion_reason = first_present(universe_row, ["promotion_reason"])
    demotion_reason = first_present(universe_row, ["demotion_reason"])
    is_candidate = first_present(universe_row, ["is_candidate"])
    reason_bits = [f"universe_tier={universe_tier}"]
    if is_candidate:
        reason_bits.append(f"is_candidate={is_candidate}")
    if promotion_reason:
        reason_bits.append(f"promotion_reason={promotion_reason}")
    if demotion_reason:
        reason_bits.append(f"demotion_reason={demotion_reason}")
    return "FILTERED_BY_CURRENT_CANDIDATE_RULES", "; ".join(reason_bits)


def make_report(
    status: str,
    rid: str,
    generated_at: str,
    summary: dict[str, object],
    bucket_counts: Counter,
    samples: dict[str, list[str]],
    evidence_paths: list[str],
    warnings: list[str],
    current_report_path: str,
    detail_path: str,
    summary_path: str,
) -> str:
    lines = [
        "# V18.35A 总池到候选池差异审计",
        "",
        f"- STATUS: `{status}`",
        f"- RUN_ID: `{rid}`",
        f"- GENERATED_AT: `{generated_at}`",
        "",
        "## 一句话结论",
        (
            f"当前 rolling universe 总池为 `{summary['total_universe_count']}`，"
            f"current ranked candidates 为 `{summary['current_candidate_count']}`，"
            f"总池中未进入当前候选池为 `{summary['universe_not_in_candidates_count']}`。"
        ),
        (
            f"最新 signal freeze 数量为 `{summary['latest_signal_freeze_count']}`，"
            f"candidate 与 freeze 差异为 candidates_not_in_freeze=`{summary['candidates_not_in_freeze_count']}`，"
            f"freeze_not_in_candidates=`{summary['freeze_not_in_candidates_count']}`。"
        ),
        "",
        "这不是交易信号，也不是排名/候选生成逻辑变更；它只是解释为什么总池数量大于当前候选池数量。",
        "",
        "## 核心数量",
        f"- 总池数量: `{summary['total_universe_count']}`",
        f"- 当前候选数量: `{summary['current_candidate_count']}`",
        f"- 总池未进入候选数量: `{summary['universe_not_in_candidates_count']}`",
        f"- 候选但不在总池数量: `{summary['candidates_not_in_universe_count']}`",
        f"- 最新 freeze 数量: `{summary['latest_signal_freeze_count']}`",
        f"- freeze 是否匹配 current candidates: `{'YES' if summary['candidates_not_in_freeze_count'] == 0 and summary['freeze_not_in_candidates_count'] == 0 else 'NO'}`",
        "",
        "## 未进入候选池原因分布",
        "| exclusion_bucket | count |",
        "| --- | ---: |",
    ]
    for bucket, count in bucket_counts.most_common():
        if bucket == "IN_CURRENT_CANDIDATES":
            continue
        lines.append(f"| `{bucket}` | {count} |")
    lines.extend(["", "## 分桶样例"])
    for bucket in BUCKETS:
        if bucket not in samples or bucket == "IN_CURRENT_CANDIDATES":
            continue
        sample_text = ", ".join(samples[bucket][:20]) if samples[bucket] else "NONE"
        lines.append(f"- `{bucket}`: {sample_text}")
    lines.extend(
        [
            "",
            "## 是否说明丢票",
            "不直接说明丢票。这个审计只说明 total rolling universe 与 current ranked candidates 的集合差异，并按现有证据归因。",
            "如果某个 ticker 被标记为 `UNKNOWN_INSUFFICIENT_EVIDENCE`，含义是当前报告层证据不足，不能把它说成被规则过滤或数据缺失。",
            "",
            "## Operator Next Action",
            "- 若主要分桶是 `FILTERED_BY_CURRENT_CANDIDATE_RULES`，优先查看 rolling universe state 的 tier/promotion/demotion 字段。",
            "- 若出现 `FACTOR_PACK_MISSING` 或 `TECHNICAL_TIMING_MISSING`，优先查看对应 current factor/timing 文件是否覆盖该 ticker。",
            "- 若出现 orphan 或 candidate/freeze mismatch，再进入修复任务；本审计不会自动修复。",
            "",
            "## Evidence Source Paths",
        ]
    )
    for path in evidence_paths:
        lines.append(f"- `{path}`")
    lines.extend(
        [
            "",
            "## Warnings",
        ]
    )
    if warnings:
        lines.extend([f"- WARN: {warning}" for warning in warnings])
    else:
        lines.append("- NONE")
    lines.extend(
        [
            "",
            "## Output Files",
            f"- Current report: `{current_report_path}`",
            f"- Detail CSV: `{detail_path}`",
            f"- Summary CSV: `{summary_path}`",
            "",
            "## Final Conclusion",
            "这是解释性审计，不改变任何交易/排名/冻结逻辑。",
            "`AUTO_TRADE DISABLED`, `AUTO_SELL DISABLED`, `OFFICIAL_DECISION_IMPACT NONE`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()

    root = Path(args.root)
    rid = run_id()
    generated_at = now_iso()

    paths = {
        "universe": pick_existing(root, [
            "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
            "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv",
            "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv",
        ]),
        "candidate": None,
        "freeze": pick_existing(root, ["state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"]),
        "factor": pick_existing(root, ["outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"]),
        "timing": pick_existing(root, ["outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"]),
        "rolling_ledger": pick_existing(root, ["state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"]),
        "scan_plan": pick_existing(root, ["outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv"]),
        "freshness": pick_existing(root, ["outputs/v18/read_center/V18_CURRENT_DAILY_OUTPUT_FRESHNESS.md"]),
        "rolling_report": pick_existing(root, ["outputs/v18/read_center/V18_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN.md"]),
    }

    output_summary = root / "outputs/v18/ops/V18_35A_UNIVERSE_TO_CANDIDATE_DIFF_SUMMARY.csv"
    output_detail = root / "outputs/v18/ops/V18_35A_UNIVERSE_TO_CANDIDATE_DIFF_DETAIL.csv"
    output_report = root / "outputs/v18/read_center/V18_35A_UNIVERSE_TO_CANDIDATE_DIFF_REPORT.md"
    output_current = root / "outputs/v18/read_center/V18_CURRENT_UNIVERSE_TO_CANDIDATE_AUDIT.md"
    output_read_first = root / "outputs/v18/ops/V18_35A_READ_FIRST.txt"

    fail_reasons: list[str] = []
    warnings: list[str] = []
    if paths["universe"] is None:
        fail_reasons.append("missing core total universe source")
    universe_rows = read_csv_rows(paths["universe"])
    freeze_rows = read_csv_rows(paths["freeze"])
    latest_signal_date, freeze_set, latest_freeze_row_count = latest_freeze_set(freeze_rows)
    paths["candidate"] = pick_candidate_source(root, len(freeze_set) if freeze_set else None)
    if paths["candidate"] is None:
        fail_reasons.append("missing core current ranked candidate source")

    candidate_rows = read_csv_rows(paths["candidate"])
    canonical_candidate_path = root / "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
    canonical_candidate_count = len(extract_set(read_csv_rows(canonical_candidate_path), ["ticker"])) if canonical_candidate_path.exists() else 0
    if paths["candidate"] != canonical_candidate_path and canonical_candidate_count:
        warnings.append(
            "canonical current ranked candidate alias count differs from freeze/current-context count; "
            f"using freeze-matched candidate evidence {rel(root, paths['candidate'])}"
        )
    factor_rows = read_csv_rows(paths["factor"])
    timing_rows = read_csv_rows(paths["timing"])
    rolling_rows = read_csv_rows(paths["rolling_ledger"])
    scan_plan_rows = read_csv_rows(paths["scan_plan"])

    total_set = extract_set(universe_rows, ["ticker"])
    candidate_set = extract_set(candidate_rows, ["ticker"])
    factor_set = extract_set(factor_rows, ["ticker"])
    timing_set = extract_set(timing_rows, ["ticker", "yf_ticker"])
    recent_scan_set = {
        norm_ticker(row.get("ticker"))
        for row in scan_plan_rows
        if norm_ticker(row.get("ticker")) and truthy(row.get("selected_this_run", ""))
    }

    if not factor_set:
        warnings.append("optional factor-pack evidence missing or empty")
    if not timing_set:
        warnings.append("optional technical-timing evidence missing or empty")
    if not freeze_set:
        warnings.append("optional latest signal-freeze evidence missing or empty")
    if not recent_scan_set:
        warnings.append("optional current rolling scan-plan evidence missing or empty")

    universe_index = build_index(universe_rows)
    rolling_index = build_index(rolling_rows)
    factor_index = build_index(factor_rows)
    timing_index = build_index(timing_rows)
    candidate_index = build_index(candidate_rows)

    all_tickers = sorted(total_set | candidate_set | freeze_set)
    detail_rows: list[dict[str, object]] = []
    bucket_counts: Counter = Counter()
    samples: dict[str, list[str]] = {bucket: [] for bucket in BUCKETS}

    for ticker in all_tickers:
        universe_row = universe_index.get(ticker, {})
        rolling_row = rolling_index.get(ticker, {})
        candidate_row = candidate_index.get(ticker, {})
        factor_row = factor_index.get(ticker, {})
        timing_row = timing_index.get(ticker, {})
        in_total = ticker in total_set
        in_candidates = ticker in candidate_set
        in_freeze = ticker in freeze_set
        in_factor = ticker in factor_set
        in_timing = ticker in timing_set
        in_recent = ticker in recent_scan_set
        bucket, reason = determine_bucket(
            ticker,
            in_total,
            in_candidates,
            in_freeze,
            in_factor,
            in_timing,
            in_recent,
            universe_row,
            rolling_row,
        )
        bucket_counts[bucket] += 1
        if len(samples.setdefault(bucket, [])) < 20:
            samples[bucket].append(ticker)
        evidence = []
        if in_total:
            evidence.append(rel(root, paths["universe"]))
        if in_candidates:
            evidence.append(rel(root, paths["candidate"]))
        if in_freeze:
            evidence.append(rel(root, paths["freeze"]))
        if in_factor:
            evidence.append(rel(root, paths["factor"]))
        if in_timing:
            evidence.append(rel(root, paths["timing"]))
        if in_recent:
            evidence.append(rel(root, paths["scan_plan"]))

        detail_rows.append(
            {
                "ticker": ticker,
                "in_total_universe": str(in_total).upper(),
                "in_current_candidates": str(in_candidates).upper(),
                "in_latest_signal_freeze": str(in_freeze).upper(),
                "in_factor_pack": str(in_factor).upper(),
                "in_technical_timing": str(in_timing).upper(),
                "in_recent_rolling_scan": str(in_recent).upper(),
                "price_status": first_present(universe_row, ["price_cache_status"]) or first_present(rolling_row, ["local_price_available"], "UNKNOWN"),
                "freshness_status": first_present(universe_row, ["price_freshness_status"], "UNKNOWN"),
                "latest_price_date": first_present(candidate_row, ["latest_price_date"]) or first_present(factor_row, ["latest_price_date"]) or first_present(timing_row, ["price_date"]) or first_present(universe_row, ["latest_price_date"], "UNKNOWN"),
                "latest_scan_date": first_present(universe_row, ["last_scan_date"]) or first_present(rolling_row, ["last_success_scan_date", "last_attempt_scan_date"], "UNKNOWN"),
                "exclusion_bucket": bucket,
                "exclusion_reason": reason,
                "evidence_sources": ";".join(sorted(set(evidence))) if evidence else "UNKNOWN",
            }
        )

    universe_not_candidates = total_set - candidate_set
    candidates_not_universe = candidate_set - total_set
    candidates_not_freeze = candidate_set - freeze_set
    freeze_not_candidates = freeze_set - candidate_set

    if candidates_not_freeze or freeze_not_candidates:
        warnings.append("candidate set differs from latest signal freeze set")
    if candidates_not_universe:
        warnings.append("orphan candidates not present in total universe")
    unknown_missing_count = sum(1 for row in detail_rows if row["in_total_universe"] == "TRUE" and row["in_current_candidates"] == "FALSE" and row["exclusion_bucket"] == "UNKNOWN_INSUFFICIENT_EVIDENCE")
    if unknown_missing_count >= 10:
        warnings.append(f"many universe-not-candidate tickers have unknown classification: {unknown_missing_count}")

    status = STATUS_FAIL if fail_reasons else (STATUS_WARN if warnings else STATUS_OK)
    top_bucket = "NONE"
    missing_bucket_counts = Counter(row["exclusion_bucket"] for row in detail_rows if row["in_total_universe"] == "TRUE" and row["in_current_candidates"] == "FALSE")
    if missing_bucket_counts:
        top_bucket = missing_bucket_counts.most_common(1)[0][0]

    evidence_paths = [rel(root, path) for path in paths.values() if path is not None]
    summary: dict[str, object] = {
        "status": status,
        "run_id": rid,
        "generated_at": generated_at,
        "total_universe_count": len(total_set),
        "current_candidate_count": len(candidate_set),
        "latest_signal_freeze_count": len(freeze_set),
        "latest_signal_freeze_row_count": latest_freeze_row_count,
        "latest_signal_date": latest_signal_date,
        "universe_not_in_candidates_count": len(universe_not_candidates),
        "candidates_not_in_universe_count": len(candidates_not_universe),
        "candidates_not_in_freeze_count": len(candidates_not_freeze),
        "freeze_not_in_candidates_count": len(freeze_not_candidates),
        "top_exclusion_bucket": top_bucket,
        "exclusion_bucket_counts": ";".join(f"{bucket}={missing_bucket_counts.get(bucket, 0)}" for bucket in BUCKETS),
        "evidence_source_paths": ";".join(evidence_paths),
        "warning_count": len(warnings),
        "fail_count": len(fail_reasons),
        "fail_reason": "; ".join(fail_reasons),
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
    }
    for bucket in BUCKETS:
        summary[f"bucket_{bucket.lower()}_count"] = missing_bucket_counts.get(bucket, 0)

    summary_fields = list(summary.keys())
    detail_fields = [
        "ticker",
        "in_total_universe",
        "in_current_candidates",
        "in_latest_signal_freeze",
        "in_factor_pack",
        "in_technical_timing",
        "in_recent_rolling_scan",
        "price_status",
        "freshness_status",
        "latest_price_date",
        "latest_scan_date",
        "exclusion_bucket",
        "exclusion_reason",
        "evidence_sources",
    ]

    write_csv(output_summary, summary_fields, [summary])
    write_csv(output_detail, detail_fields, detail_rows)

    report = make_report(
        status,
        rid,
        generated_at,
        summary,
        missing_bucket_counts,
        samples,
        evidence_paths,
        warnings,
        rel(root, output_current),
        rel(root, output_detail),
        rel(root, output_summary),
    )
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(report, encoding="utf-8")
    output_current.write_text(report, encoding="utf-8")

    read_first = "\n".join(
        [
            f"STATUS: {status}",
            f"RUN_ID: {rid}",
            f"TOTAL_UNIVERSE_COUNT: {summary['total_universe_count']}",
            f"CURRENT_CANDIDATE_COUNT: {summary['current_candidate_count']}",
            f"LATEST_SIGNAL_FREEZE_COUNT: {summary['latest_signal_freeze_count']}",
            f"UNIVERSE_NOT_IN_CANDIDATES_COUNT: {summary['universe_not_in_candidates_count']}",
            f"CANDIDATES_NOT_IN_UNIVERSE_COUNT: {summary['candidates_not_in_universe_count']}",
            f"CANDIDATES_NOT_IN_FREEZE_COUNT: {summary['candidates_not_in_freeze_count']}",
            f"FREEZE_NOT_IN_CANDIDATES_COUNT: {summary['freeze_not_in_candidates_count']}",
            f"TOP_EXCLUSION_BUCKET: {summary['top_exclusion_bucket']}",
            f"WARNING_COUNT: {summary['warning_count']}",
            f"FAIL_COUNT: {summary['fail_count']}",
            f"REPORT: {rel(root, output_report)}",
            f"CURRENT_REPORT: {rel(root, output_current)}",
            f"DETAIL_CSV: {rel(root, output_detail)}",
            f"SUMMARY_CSV: {rel(root, output_summary)}",
            "OFFICIAL_DECISION_IMPACT: NONE",
            "AUTO_TRADE: DISABLED",
            "AUTO_SELL: DISABLED",
            "",
        ]
    )
    output_read_first.parent.mkdir(parents=True, exist_ok=True)
    output_read_first.write_text(read_first, encoding="utf-8")

    print(f"STATUS: {status}")
    print(f"RUN_ID: {rid}")
    print(f"TOTAL_UNIVERSE_COUNT: {summary['total_universe_count']}")
    print(f"CURRENT_CANDIDATE_COUNT: {summary['current_candidate_count']}")
    print(f"LATEST_SIGNAL_FREEZE_COUNT: {summary['latest_signal_freeze_count']}")
    print(f"UNIVERSE_NOT_IN_CANDIDATES_COUNT: {summary['universe_not_in_candidates_count']}")
    print(f"TOP_EXCLUSION_BUCKET: {summary['top_exclusion_bucket']}")
    print(f"WARNING_COUNT: {summary['warning_count']}")
    print(f"FAIL_COUNT: {summary['fail_count']}")
    print(f"REPORT: {output_current}")
    print(f"READ_FIRST: {output_read_first}")
    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
