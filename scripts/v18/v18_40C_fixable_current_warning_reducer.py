#!/usr/bin/env python
"""V18.40C fixable current warning reducer.

Read-only/apply reporting layer that reduces operator noise from V18.40B by
classifying fixable current warnings into refreshable, noncritical,
local-cache-ok, action-required, and unknown groups.

Apply mode is explicit and only writes V18.40C outputs. It does not modify
rankings, candidates, account state, ledgers, broker/API state, or trading
logic. Existing current reducer report aliases are backed up before overwrite
in apply mode.
"""

from __future__ import annotations

import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

READ40B = "outputs/v18/ops/V18_40B_READ_FIRST.txt"
DETAIL40B = "outputs/v18/ops/V18_40B_CURRENT_WARNING_CLEANUP_DETAIL.csv"
DETAIL38C = "outputs/v18/ops/V18_38C_R1_COMMAND_STATUS_DETAIL.csv"
READ39A = "outputs/v18/ops/V18_39A_READ_FIRST.txt"

OUT_READ_FIRST = "outputs/v18/ops/V18_40C_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_40C_FIXABLE_WARNING_REDUCER_SUMMARY.csv"
OUT_DETAIL = "outputs/v18/ops/V18_40C_FIXABLE_WARNING_REDUCER_DETAIL.csv"
OUT_REPORT = "outputs/v18/read_center/V18_40C_FIXABLE_WARNING_REDUCER_REPORT.md"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_FIXABLE_WARNING_REDUCER.md"

SUMMARY_FIELDS = [
    "status",
    "run_id",
    "apply_fixable_current_warning_reducer",
    "input_fixable_current_warning_count",
    "refreshable_warning_count",
    "noncritical_reclassifiable_count",
    "local_cache_ok_reclassifiable_count",
    "action_required_warning_count",
    "unknown_fixable_warning_count",
    "expected_remaining_fixable_warning_count",
    "daily_run_usable",
    "buy_candidate_report_usable",
    "trading_execution_allowed",
    "next_recommended_step",
    "backup_path",
    "official_decision_impact",
    "auto_trade",
    "auto_sell",
    "ranking_modified",
    "factor_weights_modified",
    "signal_freeze_ledger_modified",
    "paper_trading_ledger_modified",
    "shadow_portfolio_ledger_modified",
    "account_state_modified",
    "broker_api_used",
    "order_execution_used",
]

DETAIL_FIELDS = [
    "source_name",
    "source_path",
    "source_scope",
    "input_normalized_status",
    "input_category",
    "v18_40c_group",
    "source_count",
    "reducer_action",
    "expected_remaining_fixable",
    "daily_run_blocking",
    "notes",
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


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as f:
                reader = csv.DictReader(f)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


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


def to_int(value: object) -> int:
    try:
        text = str(value or "").strip()
        if not text:
            return 0
        return int(float(text))
    except Exception:
        return 0


def local_cache_ok(read39a: dict[str, str], read40b: dict[str, str]) -> bool:
    return (
        to_int(read39a.get("DATA_QUALITY_WARNING_COUNT")) == 0
        and read40b.get("DAILY_RUN_USABLE", "") == "TRUE"
        and bool(read39a.get("LATEST_SIGNAL_DATE", ""))
        and to_int(read39a.get("LATEST_SIGNAL_FREEZE_COUNT")) > 0
        and to_int(read39a.get("LATEST_SIGNAL_FREEZE_COUNT")) == to_int(read39a.get("CURRENT_FULL_CANDIDATE_COUNT"))
    )


def backup_current_report(root: Path, run_id: str) -> str:
    current = root / OUT_CURRENT_REPORT
    if not current.exists():
        return ""
    backup_dir = root / "archive/v18/fixable_warning_reducer_backups" / run_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(current, backup_dir / current.name)
    return backup_dir.as_posix()


def classify_38c_rows(rows38c: list[dict[str, str]], cache_ok: bool) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in rows38c:
        scope = row.get("source_scope", "")
        severity = row.get("severity", "")
        expected = row.get("is_expected_pending", "")
        status = row.get("normalized_status", "")
        if not scope.startswith("CURRENT") or severity != "WARN" or expected == "TRUE":
            continue
        if status == "ACCOUNT_TEMPLATE_WARN":
            continue

        group = "UNKNOWN_FIXABLE_WARNING"
        action = "MANUAL_REVIEW_REQUIRED"
        remaining = 1
        notes = row.get("notes", "")
        if status == "REPORT_STALE_WARN":
            group = "STALE_CURRENT_SUPPORTING_REPORT_NONCRITICAL"
            action = "RECLASSIFY_NONCRITICAL_IN_V18_40C_ONLY"
            remaining = 0
            notes = "Current supporting report is stale, but daily run and buy-candidate report remain usable. Source report is not deleted or suppressed."
        elif status == "DATA_PROVIDER_WARN":
            if cache_ok:
                group = "CURRENT_PROVIDER_WARNING_LOCAL_CACHE_OK"
                action = "RECLASSIFY_LOCAL_CACHE_OK_IN_V18_40C_ONLY"
                remaining = 0
                notes = "Latest V18.39A signals/freeze are complete with zero data-quality warnings; provider warning is nonblocking."
            else:
                group = "CURRENT_PROVIDER_WARNING_ACTION_REQUIRED"
                action = "ACTION_REQUIRED_REVIEW_PROVIDER_OR_PRICE_COVERAGE"
                remaining = 1
        elif status == "REVIEW_NEEDED_NON_BLOCKING":
            source = row.get("source_name", "")
            if source in {"V18_34B_READ_FIRST.txt", "V18_34C_READ_FIRST.txt", "V18_35B_READ_FIRST.txt", "V18_35C_READ_FIRST.txt", "V18_35F_READ_FIRST.txt"}:
                group = "COMMAND_STATUS_RESIDUAL_WARN"
                action = "ACTION_REQUIRED_REVIEW_SOURCE_WARN_STATUS"
                remaining = 1
                notes = "Residual current WARN status requires source-specific review; V18.40C does not rewrite the source report."
        out.append({
            "source_name": row.get("source_name", ""),
            "source_path": row.get("source_path", ""),
            "source_scope": scope,
            "input_normalized_status": status,
            "input_category": "V18_38C_R1_CURRENT_WARNING",
            "v18_40c_group": group,
            "source_count": 1,
            "reducer_action": action,
            "expected_remaining_fixable": remaining,
            "daily_run_blocking": "FALSE",
            "notes": notes,
        })
    return out


def ensure_40b_aggregate_rows(detail_rows: list[dict[str, object]], rows40b: list[dict[str, str]]) -> list[dict[str, object]]:
    """Fallback when 38C detail is unavailable."""
    if detail_rows:
        return detail_rows
    out: list[dict[str, object]] = []
    for row in rows40b:
        if row.get("category") != "FIXABLE_CURRENT_WARNING" and row.get("category") != "STALE_SUPPORTING_REPORT":
            continue
        count = to_int(row.get("source_count"))
        category = "UNKNOWN_FIXABLE_WARNING"
        remaining = count
        action = "MANUAL_REVIEW_REQUIRED"
        if row.get("category") == "STALE_SUPPORTING_REPORT":
            category = "STALE_CURRENT_SUPPORTING_REPORT_NONCRITICAL"
            remaining = 0
            action = "RECLASSIFY_NONCRITICAL_IN_V18_40C_ONLY"
        out.append({
            "source_name": row.get("source", ""),
            "source_path": "",
            "source_scope": "",
            "input_normalized_status": row.get("operator_classification", ""),
            "input_category": row.get("category", ""),
            "v18_40c_group": category,
            "source_count": count,
            "reducer_action": action,
            "expected_remaining_fixable": remaining,
            "daily_run_blocking": "FALSE",
            "notes": row.get("notes", ""),
        })
    return out


def run(root: Path, apply: bool) -> int:
    run_id = f"V18_40C_FIXABLE_CURRENT_WARNING_REDUCER_{stamp()}"
    try:
        read40b = parse_kv(root / READ40B)
        read39a = parse_kv(root / READ39A)
        rows40b, _ = read_csv(root / DETAIL40B)
        rows38c, _ = read_csv(root / DETAIL38C)
        if not read40b:
            raise RuntimeError("missing V18_40B_READ_FIRST")
    except Exception as exc:
        summary = failure_summary(run_id, apply, f"{type(exc).__name__}: {exc}")
        write_outputs(root, run_id, apply, summary, [])
        return 1

    cache_ok = local_cache_ok(read39a, read40b)
    detail = classify_38c_rows(rows38c, cache_ok)
    detail = ensure_40b_aggregate_rows(detail, rows40b)

    input_fixable = to_int(read40b.get("FIXABLE_CURRENT_WARNING_COUNT"))
    refreshable = sum(to_int(r.get("source_count")) for r in detail if r.get("v18_40c_group") == "STALE_CURRENT_SUPPORTING_REPORT_REFRESHABLE")
    noncritical = sum(to_int(r.get("source_count")) for r in detail if r.get("v18_40c_group") == "STALE_CURRENT_SUPPORTING_REPORT_NONCRITICAL")
    local_cache = sum(to_int(r.get("source_count")) for r in detail if r.get("v18_40c_group") == "CURRENT_PROVIDER_WARNING_LOCAL_CACHE_OK")
    action_required = sum(to_int(r.get("source_count")) for r in detail if r.get("v18_40c_group") in {"CURRENT_PROVIDER_WARNING_ACTION_REQUIRED", "COMMAND_STATUS_RESIDUAL_WARN"})
    unknown = sum(to_int(r.get("source_count")) for r in detail if r.get("v18_40c_group") == "UNKNOWN_FIXABLE_WARNING")
    expected_remaining = sum(to_int(r.get("expected_remaining_fixable")) for r in detail)

    if expected_remaining == 0:
        status = "OK_V18_40C_FIXABLE_CURRENT_WARNING_REDUCER_CLEAN"
        next_step = "No remaining fixable current warnings after V18.40C reducer classification."
    else:
        status = "WARN_V18_40C_FIXABLE_CURRENT_WARNING_REDUCER_PARTIAL_REVIEW_NEEDED"
        next_step = "Daily run remains usable; review residual command-status and unknown current warnings at their source reports."

    backup_path = backup_current_report(root, run_id) if apply else ""
    summary = {
        "status": status,
        "run_id": run_id,
        "apply_fixable_current_warning_reducer": str(bool(apply)).upper(),
        "input_fixable_current_warning_count": input_fixable,
        "refreshable_warning_count": refreshable,
        "noncritical_reclassifiable_count": noncritical,
        "local_cache_ok_reclassifiable_count": local_cache,
        "action_required_warning_count": action_required,
        "unknown_fixable_warning_count": unknown,
        "expected_remaining_fixable_warning_count": expected_remaining,
        "daily_run_usable": read40b.get("DAILY_RUN_USABLE", ""),
        "buy_candidate_report_usable": read40b.get("BUY_CANDIDATE_REPORT_USABLE", ""),
        "trading_execution_allowed": "FALSE",
        "next_recommended_step": next_step,
        "backup_path": backup_path,
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "ranking_modified": "FALSE",
        "factor_weights_modified": "FALSE",
        "signal_freeze_ledger_modified": "FALSE",
        "paper_trading_ledger_modified": "FALSE",
        "shadow_portfolio_ledger_modified": "FALSE",
        "account_state_modified": "FALSE",
        "broker_api_used": "FALSE",
        "order_execution_used": "FALSE",
    }
    write_outputs(root, run_id, apply, summary, detail)
    return 0


def failure_summary(run_id: str, apply: bool, reason: str) -> dict[str, object]:
    return {
        "status": "FAIL_V18_40C_FIXABLE_CURRENT_WARNING_REDUCER_FAILED",
        "run_id": run_id,
        "apply_fixable_current_warning_reducer": str(bool(apply)).upper(),
        "input_fixable_current_warning_count": 0,
        "refreshable_warning_count": 0,
        "noncritical_reclassifiable_count": 0,
        "local_cache_ok_reclassifiable_count": 0,
        "action_required_warning_count": 0,
        "unknown_fixable_warning_count": 0,
        "expected_remaining_fixable_warning_count": 0,
        "daily_run_usable": "",
        "buy_candidate_report_usable": "",
        "trading_execution_allowed": "FALSE",
        "next_recommended_step": f"Fix V18.40C input/read failure: {reason}",
        "backup_path": "",
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "ranking_modified": "FALSE",
        "factor_weights_modified": "FALSE",
        "signal_freeze_ledger_modified": "FALSE",
        "paper_trading_ledger_modified": "FALSE",
        "shadow_portfolio_ledger_modified": "FALSE",
        "account_state_modified": "FALSE",
        "broker_api_used": "FALSE",
        "order_execution_used": "FALSE",
    }


def write_outputs(root: Path, run_id: str, apply: bool, summary: dict[str, object], detail: list[dict[str, object]]) -> None:
    write_csv(root / OUT_SUMMARY, [summary], SUMMARY_FIELDS)
    write_csv(root / OUT_DETAIL, detail, DETAIL_FIELDS)
    write_text(root / OUT_READ_FIRST, render_read_first(summary))
    report = render_report(summary, detail)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_CURRENT_REPORT, report)


def render_read_first(summary: dict[str, object]) -> str:
    keys = [
        "STATUS",
        "RUN_ID",
        "APPLY_FIXABLE_CURRENT_WARNING_REDUCER",
        "INPUT_FIXABLE_CURRENT_WARNING_COUNT",
        "REFRESHABLE_WARNING_COUNT",
        "NONCRITICAL_RECLASSIFIABLE_COUNT",
        "LOCAL_CACHE_OK_RECLASSIFIABLE_COUNT",
        "ACTION_REQUIRED_WARNING_COUNT",
        "UNKNOWN_FIXABLE_WARNING_COUNT",
        "EXPECTED_REMAINING_FIXABLE_WARNING_COUNT",
        "DAILY_RUN_USABLE",
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
        "SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE",
        "PAPER_TRADING_LEDGER_MODIFIED: FALSE",
        "SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE",
        "ACCOUNT_STATE_MODIFIED: FALSE",
        "BROKER_API_USED: FALSE",
        "ORDER_EXECUTION_USED: FALSE",
    ]
    return "\n".join(lines) + "\n"


def render_report(summary: dict[str, object], detail: list[dict[str, object]]) -> str:
    lines = [
        "# V18.40C Fixable Current Warning Reducer",
        "",
        "## Status",
        f"- STATUS: {summary.get('status')}",
        f"- RUN_ID: {summary.get('run_id')}",
        f"- APPLY_FIXABLE_CURRENT_WARNING_REDUCER: {summary.get('apply_fixable_current_warning_reducer')}",
        f"- INPUT_FIXABLE_CURRENT_WARNING_COUNT: {summary.get('input_fixable_current_warning_count')}",
        f"- EXPECTED_REMAINING_FIXABLE_WARNING_COUNT: {summary.get('expected_remaining_fixable_warning_count')}",
        f"- DAILY_RUN_USABLE: {summary.get('daily_run_usable')}",
        f"- BUY_CANDIDATE_REPORT_USABLE: {summary.get('buy_candidate_report_usable')}",
        f"- TRADING_EXECUTION_ALLOWED: {summary.get('trading_execution_allowed')}",
        "",
        "## Reducer Counts",
        f"- REFRESHABLE_WARNING_COUNT: {summary.get('refreshable_warning_count')}",
        f"- NONCRITICAL_RECLASSIFIABLE_COUNT: {summary.get('noncritical_reclassifiable_count')}",
        f"- LOCAL_CACHE_OK_RECLASSIFIABLE_COUNT: {summary.get('local_cache_ok_reclassifiable_count')}",
        f"- ACTION_REQUIRED_WARNING_COUNT: {summary.get('action_required_warning_count')}",
        f"- UNKNOWN_FIXABLE_WARNING_COUNT: {summary.get('unknown_fixable_warning_count')}",
        "",
        "## Detail",
        "| source | status | group | count | action | remaining | notes |",
        "| --- | --- | --- | ---: | --- | ---: | --- |",
    ]
    for row in detail:
        lines.append(
            f"| {row.get('source_name')} | {row.get('input_normalized_status')} | {row.get('v18_40c_group')} | "
            f"{row.get('source_count')} | {row.get('reducer_action')} | {row.get('expected_remaining_fixable')} | {row.get('notes')} |"
        )
    lines += [
        "",
        "## Safety",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- RANKING_MODIFIED: FALSE",
        "- FACTOR_WEIGHTS_MODIFIED: FALSE",
        "- SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE",
        "- PAPER_TRADING_LEDGER_MODIFIED: FALSE",
        "- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE",
        "- ACCOUNT_STATE_MODIFIED: FALSE",
        "- BROKER_API_USED: FALSE",
        "- ORDER_EXECUTION_USED: FALSE",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--apply-fixable-current-warning-reducer", action="store_true")
    args = parser.parse_args()
    return run(Path(args.root).resolve(), bool(args.apply_fixable_current_warning_reducer))


if __name__ == "__main__":
    raise SystemExit(main())
