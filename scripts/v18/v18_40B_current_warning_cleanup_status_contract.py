#!/usr/bin/env python
"""V18.40B current warning cleanup / operator clean status contract.

Read-only layer that reclassifies noisy current-vs-legacy warnings into an
operator-facing status contract. It does not mutate rankings, candidates,
ledgers, account state, broker/API state, or trading logic.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

READ38C = "outputs/v18/ops/V18_38C_R1_READ_FIRST.txt"
READ39A = "outputs/v18/ops/V18_39A_READ_FIRST.txt"
OUT_READ_FIRST = "outputs/v18/ops/V18_40B_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_40B_CURRENT_WARNING_CLEANUP_SUMMARY.csv"
OUT_DETAIL = "outputs/v18/ops/V18_40B_CURRENT_WARNING_CLEANUP_DETAIL.csv"
OUT_REPORT = "outputs/v18/read_center/V18_40B_CURRENT_WARNING_CLEANUP_STATUS_CONTRACT_REPORT.md"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_OPERATOR_CLEAN_STATUS.md"

DETAIL_FIELDS = ["category", "source", "source_count", "operator_classification", "daily_run_blocking", "notes"]
SUMMARY_FIELDS = [
    "status",
    "run_id",
    "blocking_current_failure_count",
    "fixable_current_warning_count",
    "expected_pending_forward_outcome_count",
    "expected_account_template_no_real_trading_count",
    "local_cache_ok_provider_warning_count",
    "stale_supporting_report_count",
    "historical_legacy_only_count",
    "daily_run_usable",
    "forward_research_usable",
    "buy_candidate_report_usable",
    "trading_execution_allowed",
    "next_recommended_step",
    "official_decision_impact",
    "auto_trade",
    "auto_sell",
    "ranking_modified",
    "factor_weights_modified",
    "broker_api_used",
    "order_execution_used",
]


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def to_int(value: object) -> int:
    try:
        text = str(value or "").strip()
        if not text:
            return 0
        return int(float(text))
    except Exception:
        return 0


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def add_detail(rows: list[dict[str, object]], category: str, source: str, count: int, classification: str, blocking: bool, notes: str) -> None:
    if count <= 0:
        return
    rows.append({
        "category": category,
        "source": source,
        "source_count": count,
        "operator_classification": classification,
        "daily_run_blocking": str(blocking).upper(),
        "notes": notes,
    })


def run(root: Path) -> int:
    run_id = f"V18_40B_CURRENT_WARNING_CLEANUP_{stamp()}"
    c38 = parse_kv(root / READ38C)
    a39 = parse_kv(root / READ39A)

    current_blocking = to_int(c38.get("CURRENT_FAIL_BLOCKING_COUNT"))
    current_stale = to_int(c38.get("CURRENT_REPORT_STALE_WARN_COUNT"))
    current_provider = to_int(c38.get("CURRENT_DATA_PROVIDER_WARN_COUNT"))
    expected_pending = to_int(c38.get("EXPECTED_PENDING_COUNT"))
    account_template = to_int(c38.get("ACCOUNT_TEMPLATE_WARN_COUNT"))
    historical_legacy = to_int(c38.get("HISTORICAL_LEGACY_COUNT")) + to_int(c38.get("LEGACY_FAIL_COUNT")) + to_int(c38.get("LEGACY_DATA_PROVIDER_WARN_COUNT")) + to_int(c38.get("LEGACY_REPORT_STALE_WARN_COUNT"))
    research_not_ready = to_int(c38.get("RESEARCH_NOT_READY_COUNT"))
    unknown_review = to_int(c38.get("UNKNOWN_REVIEW_COUNT"))
    data_quality_warnings = to_int(a39.get("DATA_QUALITY_WARNING_COUNT"))
    signal_count = to_int(a39.get("TOTAL_SIGNAL_COUNT"))
    latest_signal_date = a39.get("LATEST_SIGNAL_DATE", "")

    no_real_trading = (
        c38.get("AUTO_TRADE", AUTO_TRADE) == "DISABLED"
        and c38.get("BROKER_API_USED", "FALSE") == "FALSE"
        and c38.get("ORDER_EXECUTION_USED", "FALSE") == "FALSE"
    )
    signal_generation_usable = signal_count > 0 and bool(latest_signal_date) and data_quality_warnings == 0

    blocking_current_failure_count = current_blocking
    fixable_current_warning_count = 0
    local_cache_ok_provider_warning_count = 0
    if current_provider > 0:
        if signal_generation_usable:
            local_cache_ok_provider_warning_count = current_provider
        else:
            fixable_current_warning_count += current_provider
    stale_supporting_report_count = current_stale
    fixable_current_warning_count += current_stale
    if research_not_ready > 0:
        fixable_current_warning_count += research_not_ready
    if unknown_review > 0:
        fixable_current_warning_count += unknown_review

    expected_account_count = account_template if no_real_trading else 0
    if account_template and not no_real_trading:
        fixable_current_warning_count += account_template

    buy_candidate_report_usable = "TRUE" if signal_generation_usable and blocking_current_failure_count == 0 else "FALSE"
    daily_run_usable = "TRUE" if blocking_current_failure_count == 0 else "FALSE"
    forward_research_usable = "TRUE" if c38.get("FORWARD_RESEARCH_USABLE", "TRUE") == "TRUE" else "FALSE"
    trading_execution_allowed = "FALSE"

    if blocking_current_failure_count > 0:
        status = "FAIL_V18_40B_CURRENT_OPERATOR_STATUS_BLOCKED"
        next_step = "Fix blocking current failures before using today's operator reports."
    elif fixable_current_warning_count > 0:
        status = "WARN_V18_40B_CURRENT_OPERATOR_STATUS_FIXABLE_WARNINGS"
        next_step = "Daily run is usable; review fixable current warnings, but expected pending/account-template/legacy items are not blockers."
    else:
        status = "OK_V18_40B_CURRENT_OPERATOR_STATUS_CLEAN"
        next_step = "Daily run and buy-candidate report are usable in read-only mode."

    detail: list[dict[str, object]] = []
    add_detail(detail, "BLOCKING_CURRENT_FAILURE", "V18_38C_R1 CURRENT_FAIL_BLOCKING_COUNT", blocking_current_failure_count, "BLOCKING_CURRENT_FAILURE", True, "Current failures that block daily operator usability.")
    add_detail(detail, "FIXABLE_CURRENT_WARNING", "V18_38C_R1 RESEARCH_NOT_READY_COUNT", research_not_ready, "FIXABLE_CURRENT_WARNING", False, "Research readiness warning is actionable but not a trading/account failure.")
    add_detail(detail, "FIXABLE_CURRENT_WARNING", "V18_38C_R1 UNKNOWN_REVIEW_COUNT", unknown_review, "FIXABLE_CURRENT_WARNING", False, "Unknown current review items should be triaged.")
    add_detail(detail, "EXPECTED_PENDING_FORWARD_OUTCOME", "V18_38C_R1 EXPECTED_PENDING_COUNT", expected_pending, "EXPECTED_PENDING_FORWARD_OUTCOME", False, "Forward outcomes are pending due to future-price horizon immaturity.")
    add_detail(detail, "EXPECTED_ACCOUNT_TEMPLATE_NO_REAL_TRADING", "V18_38C_R1 ACCOUNT_TEMPLATE_WARN_COUNT", expected_account_count, "EXPECTED_ACCOUNT_TEMPLATE_NO_REAL_TRADING", False, "Account template warnings are expected when auto trading and broker/order execution are disabled.")
    add_detail(detail, "LOCAL_CACHE_OK_PROVIDER_WARNING", "V18_38C_R1 CURRENT_DATA_PROVIDER_WARN_COUNT", local_cache_ok_provider_warning_count, "LOCAL_CACHE_OK_PROVIDER_WARNING", False, "Provider warning is non-blocking because latest signal objects/candidates are usable from local cache.")
    add_detail(detail, "STALE_SUPPORTING_REPORT", "V18_38C_R1 CURRENT_REPORT_STALE_WARN_COUNT", stale_supporting_report_count, "STALE_SUPPORTING_REPORT", False, "Supporting report stale warning is fixable but not a daily-run blocker.")
    add_detail(detail, "HISTORICAL_LEGACY_ONLY", "V18_38C_R1 legacy issue counters", historical_legacy, "HISTORICAL_LEGACY_ONLY", False, "Historical/legacy findings never make DAILY_RUN_USABLE false.")
    if not detail:
        add_detail(detail, "CLEAN_OK", "V18_40B", 1, "CLEAN_OK", False, "No blocking, fixable, expected, provider, stale, or legacy warnings found.")

    summary = {
        "status": status,
        "run_id": run_id,
        "blocking_current_failure_count": blocking_current_failure_count,
        "fixable_current_warning_count": fixable_current_warning_count,
        "expected_pending_forward_outcome_count": expected_pending,
        "expected_account_template_no_real_trading_count": expected_account_count,
        "local_cache_ok_provider_warning_count": local_cache_ok_provider_warning_count,
        "stale_supporting_report_count": stale_supporting_report_count,
        "historical_legacy_only_count": historical_legacy,
        "daily_run_usable": daily_run_usable,
        "forward_research_usable": forward_research_usable,
        "buy_candidate_report_usable": buy_candidate_report_usable,
        "trading_execution_allowed": trading_execution_allowed,
        "next_recommended_step": next_step,
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "ranking_modified": "FALSE",
        "factor_weights_modified": "FALSE",
        "broker_api_used": "FALSE",
        "order_execution_used": "FALSE",
    }

    write_csv(root / OUT_SUMMARY, [summary], SUMMARY_FIELDS)
    write_csv(root / OUT_DETAIL, detail, DETAIL_FIELDS)
    write_text(root / OUT_READ_FIRST, render_read_first(summary))
    report = render_report(summary, detail)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_CURRENT_REPORT, report)
    return 1 if status.startswith("FAIL_") else 0


def render_read_first(summary: dict[str, object]) -> str:
    keys = [
        "STATUS",
        "RUN_ID",
        "BLOCKING_CURRENT_FAILURE_COUNT",
        "FIXABLE_CURRENT_WARNING_COUNT",
        "EXPECTED_PENDING_FORWARD_OUTCOME_COUNT",
        "EXPECTED_ACCOUNT_TEMPLATE_NO_REAL_TRADING_COUNT",
        "LOCAL_CACHE_OK_PROVIDER_WARNING_COUNT",
        "STALE_SUPPORTING_REPORT_COUNT",
        "HISTORICAL_LEGACY_ONLY_COUNT",
        "DAILY_RUN_USABLE",
        "FORWARD_RESEARCH_USABLE",
        "BUY_CANDIDATE_REPORT_USABLE",
        "TRADING_EXECUTION_ALLOWED",
        "NEXT_RECOMMENDED_STEP",
    ]
    lines = [f"{key}: {summary.get(key.lower(), '')}" for key in keys]
    lines += [
        "OFFICIAL_DECISION_IMPACT: NONE",
        "AUTO_TRADE: DISABLED",
        "AUTO_SELL: DISABLED",
        "RANKING_MODIFIED: FALSE",
        "FACTOR_WEIGHTS_MODIFIED: FALSE",
        "BROKER_API_USED: FALSE",
        "ORDER_EXECUTION_USED: FALSE",
    ]
    return "\n".join(lines) + "\n"


def render_report(summary: dict[str, object], detail: list[dict[str, object]]) -> str:
    lines = [
        "# V18.40B Current Warning Cleanup Status Contract",
        "",
        "## Operator Status",
        f"- STATUS: {summary.get('status')}",
        f"- DAILY_RUN_USABLE: {summary.get('daily_run_usable')}",
        f"- FORWARD_RESEARCH_USABLE: {summary.get('forward_research_usable')}",
        f"- BUY_CANDIDATE_REPORT_USABLE: {summary.get('buy_candidate_report_usable')}",
        f"- TRADING_EXECUTION_ALLOWED: {summary.get('trading_execution_allowed')}",
        f"- NEXT_RECOMMENDED_STEP: {summary.get('next_recommended_step')}",
        "",
        "## Clean Classification Counts",
        f"- BLOCKING_CURRENT_FAILURE: {summary.get('blocking_current_failure_count')}",
        f"- FIXABLE_CURRENT_WARNING: {summary.get('fixable_current_warning_count')}",
        f"- EXPECTED_PENDING_FORWARD_OUTCOME: {summary.get('expected_pending_forward_outcome_count')}",
        f"- EXPECTED_ACCOUNT_TEMPLATE_NO_REAL_TRADING: {summary.get('expected_account_template_no_real_trading_count')}",
        f"- LOCAL_CACHE_OK_PROVIDER_WARNING: {summary.get('local_cache_ok_provider_warning_count')}",
        f"- STALE_SUPPORTING_REPORT: {summary.get('stale_supporting_report_count')}",
        f"- HISTORICAL_LEGACY_ONLY: {summary.get('historical_legacy_only_count')}",
        "",
        "## Detail",
        "| category | source | count | classification | blocking | notes |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for row in detail:
        lines.append(f"| {row.get('category')} | {row.get('source')} | {row.get('source_count')} | {row.get('operator_classification')} | {row.get('daily_run_blocking')} | {row.get('notes')} |")
    lines += [
        "",
        "## Safety",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- RANKING_MODIFIED: FALSE",
        "- FACTOR_WEIGHTS_MODIFIED: FALSE",
        "- BROKER_API_USED: FALSE",
        "- ORDER_EXECUTION_USED: FALSE",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
