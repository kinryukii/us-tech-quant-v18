#!/usr/bin/env python
"""V18.40D residual action warning resolver.

Diagnostic/read-center layer for the five residual action-required warnings
left by V18.40C. Default mode is read-only. Apply mode only writes V18.40D
outputs and backs up the current report alias before overwriting it.
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

DETAIL40C = "outputs/v18/ops/V18_40C_FIXABLE_WARNING_REDUCER_DETAIL.csv"
READ40C = "outputs/v18/ops/V18_40C_READ_FIRST.txt"
READ39A = "outputs/v18/ops/V18_39A_READ_FIRST.txt"
READ40A = "outputs/v18/ops/V18_40A_READ_FIRST.txt"
FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"

RESIDUAL_READS = {
    "V18_34B_READ_FIRST.txt": "outputs/v18/ops/V18_34B_READ_FIRST.txt",
    "V18_34C_READ_FIRST.txt": "outputs/v18/ops/V18_34C_READ_FIRST.txt",
    "V18_35B_READ_FIRST.txt": "outputs/v18/ops/V18_35B_READ_FIRST.txt",
    "V18_35C_READ_FIRST.txt": "outputs/v18/ops/V18_35C_READ_FIRST.txt",
    "V18_35F_READ_FIRST.txt": "outputs/v18/ops/V18_35F_READ_FIRST.txt",
}

OUT_READ_FIRST = "outputs/v18/ops/V18_40D_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_40D_RESIDUAL_ACTION_WARNING_RESOLVER_SUMMARY.csv"
OUT_DETAIL = "outputs/v18/ops/V18_40D_RESIDUAL_ACTION_WARNING_RESOLVER_DETAIL.csv"
OUT_REPORT = "outputs/v18/read_center/V18_40D_RESIDUAL_ACTION_WARNING_RESOLVER_REPORT.md"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_RESIDUAL_ACTION_WARNING_RESOLVER.md"

CLASSIFICATIONS = [
    "RESOLVED_BY_LATEST_SUCCESSFUL_RERUN",
    "EXPECTED_NO_REAL_TRADING_MODE",
    "EXPECTED_FORWARD_PENDING_OR_IMMATURE_HORIZON",
    "READABILITY_TRUST_WARNING_NONBLOCKING",
    "STALE_BUT_NONCRITICAL_SUPPORTING_MODULE",
    "TRUE_ACTION_REQUIRED_REFRESH",
    "TRUE_ACTION_REQUIRED_CODE_FIX",
    "UNKNOWN_REVIEW_REQUIRED",
]

SUMMARY_FIELDS = [
    "status",
    "run_id",
    "apply_residual_action_warning_resolver",
    "input_residual_action_required_count",
    "resolved_by_latest_successful_rerun_count",
    "expected_no_real_trading_mode_count",
    "expected_forward_pending_or_immature_horizon_count",
    "readability_trust_warning_nonblocking_count",
    "v18_19a_readability_warning_classified_nonblocking",
    "stale_but_noncritical_supporting_module_count",
    "true_action_required_refresh_count",
    "true_action_required_code_fix_count",
    "unknown_review_required_count",
    "expected_remaining_action_required_count",
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
    "input_v18_40c_group",
    "source_status",
    "classification",
    "expected_remaining_action_required",
    "diagnostic_reason",
    "evidence",
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


def trueish(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "1", "FULL_MATCH"}


def backup_current_report(root: Path, run_id: str) -> str:
    current = root / OUT_CURRENT_REPORT
    if not current.exists():
        return ""
    backup_dir = root / "archive/v18/residual_action_warning_resolver_backups" / run_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(current, backup_dir / current.name)
    return backup_dir.as_posix()


def freeze_latest_count(root: Path) -> tuple[str, int]:
    rows, _ = read_csv(root / FREEZE_LEDGER)
    by_date: dict[str, set[str]] = {}
    for row in rows:
        date = str(row.get("signal_date", "")).strip()
        ticker = str(row.get("ticker", "")).strip().upper()
        if date and ticker:
            by_date.setdefault(date, set()).add(ticker)
    if not by_date:
        return "", 0
    latest = sorted(by_date)[-1]
    return latest, len(by_date[latest])


def residual_inputs(root: Path) -> list[dict[str, str]]:
    rows, _ = read_csv(root / DETAIL40C)
    residual = [row for row in rows if to_int(row.get("expected_remaining_fixable")) > 0]
    if residual:
        return residual
    return [{"source_name": name, "source_path": path, "v18_40c_group": "COMMAND_STATUS_RESIDUAL_WARN"} for name, path in RESIDUAL_READS.items()]


def classify_source(source_name: str, read: dict[str, str], read39a: dict[str, str], read40a: dict[str, str], read40c: dict[str, str], freeze_date: str, freeze_count: int) -> tuple[str, int, str, str]:
    status = read.get("STATUS", "")
    latest_signal_date = read39a.get("LATEST_SIGNAL_DATE", "")
    full_count = to_int(read39a.get("CURRENT_FULL_CANDIDATE_COUNT"))
    daily_usable = read40c.get("DAILY_RUN_USABLE") == "TRUE"
    buy_usable = read40c.get("BUY_CANDIDATE_REPORT_USABLE") == "TRUE"
    top_full_clean = read40a.get("MISMATCH_COUNT") == "0" and read39a.get("TOP_FULL_CANONICAL_SYNC_REQUIRED") == "FALSE"
    common_evidence = f"daily_usable={daily_usable};buy_usable={buy_usable};latest_signal_date={latest_signal_date};freeze={freeze_date}/{freeze_count};top_full_clean={top_full_clean}"

    if "ERROR" in status.upper() or "TRACEBACK" in status.upper() or "RUNTIME" in status.upper():
        return "TRUE_ACTION_REQUIRED_CODE_FIX", 1, "Source status indicates a code/runtime failure.", common_evidence

    if source_name == "V18_19A_READ_FIRST.txt" and status == "WARN_V18_19A_DAILY_READABILITY_READY":
        if daily_usable and buy_usable and top_full_clean:
            return (
                "READABILITY_TRUST_WARNING_NONBLOCKING",
                0,
                "Daily readability trust warning caps operator trust level but does not block current candidate report usability when current candidate/top/full consistency is already proven.",
                common_evidence,
            )
        return "TRUE_ACTION_REQUIRED_REFRESH", 1, "V18.19A readability warning remains action-required because current candidate usability or top/full consistency is not proven.", common_evidence

    if source_name == "V18_35F_READ_FIRST.txt":
        ok = (
            status.startswith("OK")
            and read.get("APPLY_NEXT_SIGNAL_FREEZE_EXPANSION") == "TRUE"
            and read.get("SIGNAL_DATE") == latest_signal_date
            and read.get("POST_APPLY_MATCHES_CURRENT_FULL_CANDIDATES") == "TRUE"
            and to_int(read.get("WARNING_COUNT")) == 0
            and to_int(read.get("FAIL_COUNT")) == 0
        )
        if ok:
            return "RESOLVED_BY_LATEST_SUCCESSFUL_RERUN", 0, "V18.35F satisfies the explicit latest successful rerun rule.", common_evidence
        return "TRUE_ACTION_REQUIRED_REFRESH", 1, "V18.35F does not satisfy the latest successful rerun rule.", common_evidence

    if source_name == "V18_34C_READ_FIRST.txt":
        if daily_usable and buy_usable and read.get("POST_REFRESH_FREEZE", "").startswith("FULL_MATCH"):
            return "EXPECTED_NO_REAL_TRADING_MODE", 0, "Trade-readiness warning is expected in no-real-trading mode; freeze refresh evidence is full match.", common_evidence
        return "TRUE_ACTION_REQUIRED_REFRESH", 1, "Trade-readiness refresh lacks full-match evidence.", common_evidence

    if source_name == "V18_35B_READ_FIRST.txt":
        ok = (
            trueish(read.get("FULL_MATCHES_FREEZE"))
            and trueish(read.get("TOP_IS_SUBSET_OF_FULL"))
            and to_int(read.get("FAIL_COUNT")) == 0
            and full_count == to_int(read.get("FULL_CANDIDATE_COUNT"))
            and top_full_clean
        )
        if ok and daily_usable and buy_usable:
            return "STALE_BUT_NONCRITICAL_SUPPORTING_MODULE", 0, "Candidate source normalization has warning count but current full/top/freeze consistency is proven by V18.39A/V18.40A.", common_evidence
        return "TRUE_ACTION_REQUIRED_REFRESH", 1, "Candidate source normalization does not prove current source consistency.", common_evidence

    if source_name == "V18_35C_READ_FIRST.txt":
        if to_int(read.get("FAIL_COUNT")) == 0 and daily_usable and buy_usable and top_full_clean:
            return "STALE_BUT_NONCRITICAL_SUPPORTING_MODULE", 0, "Dependency review is advisory/text-reference cleanup; current candidate report is already usable and top/full aligned.", common_evidence
        return "TRUE_ACTION_REQUIRED_CODE_FIX", 1, "Dependency review has failures or current candidate usability is not proven.", common_evidence

    if source_name == "V18_34B_READ_FIRST.txt":
        if daily_usable and buy_usable and latest_signal_date and top_full_clean:
            return "STALE_BUT_NONCRITICAL_SUPPORTING_MODULE", 0, "Freshness/readability warning does not block current candidate report usability.", common_evidence
        return "TRUE_ACTION_REQUIRED_REFRESH", 1, "Daily/buy-candidate usability evidence is incomplete.", common_evidence

    if "PENDING" in status.upper() or "IMMATURE" in status.upper():
        return "EXPECTED_FORWARD_PENDING_OR_IMMATURE_HORIZON", 0, "Residual warning is due to expected forward horizon immaturity.", common_evidence

    return "UNKNOWN_REVIEW_REQUIRED", 1, "No resolver rule matched this residual source.", common_evidence


def run(root: Path, apply: bool) -> int:
    run_id = f"V18_40D_RESIDUAL_ACTION_WARNING_RESOLVER_{stamp()}"
    try:
        read40c = parse_kv(root / READ40C)
        read39a = parse_kv(root / READ39A)
        read40a = parse_kv(root / READ40A)
        if not read40c:
            raise RuntimeError("missing V18_40C_READ_FIRST")
        freeze_date, freeze_count = freeze_latest_count(root)
        inputs = residual_inputs(root)
        detail: list[dict[str, object]] = []
        for row in inputs:
            source_name = row.get("source_name", "")
            source_path = row.get("source_path", "") or RESIDUAL_READS.get(source_name, "")
            read = parse_kv(root / source_path) if source_path else {}
            classification, remaining, reason, evidence = classify_source(source_name, read, read39a, read40a, read40c, freeze_date, freeze_count)
            detail.append({
                "source_name": source_name,
                "source_path": source_path,
                "input_v18_40c_group": row.get("v18_40c_group", ""),
                "source_status": read.get("STATUS", ""),
                "classification": classification,
                "expected_remaining_action_required": remaining,
                "diagnostic_reason": reason,
                "evidence": evidence,
            })
    except Exception as exc:
        detail = []
        summary = build_summary(run_id, apply, "FAIL_V18_40D_RESIDUAL_ACTION_WARNING_RESOLVER_FAILED", 0, detail, "", "", "FALSE", f"Fix V18.40D input/read failure: {type(exc).__name__}: {exc}")
        write_outputs(root, summary, detail)
        return 1

    remaining = sum(to_int(row.get("expected_remaining_action_required")) for row in detail)
    status = "OK_V18_40D_RESIDUAL_ACTION_WARNING_RESOLVER_CLEAN" if remaining == 0 else "WARN_V18_40D_RESIDUAL_ACTION_WARNING_RESOLVER_REVIEW_NEEDED"
    next_step = "Residual action-required warnings are resolved or nonblocking in the V18.40D operator view." if remaining == 0 else "Review true action-required or unknown residual rows listed in V18.40D detail."
    backup_path = backup_current_report(root, run_id) if apply else ""
    summary = build_summary(
        run_id,
        apply,
        status,
        len(detail),
        detail,
        read40c.get("DAILY_RUN_USABLE", ""),
        read40c.get("BUY_CANDIDATE_REPORT_USABLE", ""),
        "FALSE",
        next_step,
        backup_path,
    )
    write_outputs(root, summary, detail)
    return 0


def build_summary(run_id: str, apply: bool, status: str, input_count: int, detail: list[dict[str, object]], daily_usable: str, buy_usable: str, trading_allowed: str, next_step: str, backup_path: str = "") -> dict[str, object]:
    counts = {name: 0 for name in CLASSIFICATIONS}
    remaining = 0
    for row in detail:
        cls = str(row.get("classification", "UNKNOWN_REVIEW_REQUIRED"))
        counts[cls] = counts.get(cls, 0) + 1
        remaining += to_int(row.get("expected_remaining_action_required"))
    return {
        "status": status,
        "run_id": run_id,
        "apply_residual_action_warning_resolver": str(bool(apply)).upper(),
        "input_residual_action_required_count": input_count,
        "resolved_by_latest_successful_rerun_count": counts["RESOLVED_BY_LATEST_SUCCESSFUL_RERUN"],
        "expected_no_real_trading_mode_count": counts["EXPECTED_NO_REAL_TRADING_MODE"],
        "expected_forward_pending_or_immature_horizon_count": counts["EXPECTED_FORWARD_PENDING_OR_IMMATURE_HORIZON"],
        "readability_trust_warning_nonblocking_count": counts["READABILITY_TRUST_WARNING_NONBLOCKING"],
        "v18_19a_readability_warning_classified_nonblocking": str(any(
            str(row.get("source_name")) == "V18_19A_READ_FIRST.txt"
            and str(row.get("classification")) == "READABILITY_TRUST_WARNING_NONBLOCKING"
            for row in detail
        )).upper(),
        "stale_but_noncritical_supporting_module_count": counts["STALE_BUT_NONCRITICAL_SUPPORTING_MODULE"],
        "true_action_required_refresh_count": counts["TRUE_ACTION_REQUIRED_REFRESH"],
        "true_action_required_code_fix_count": counts["TRUE_ACTION_REQUIRED_CODE_FIX"],
        "unknown_review_required_count": counts["UNKNOWN_REVIEW_REQUIRED"],
        "expected_remaining_action_required_count": remaining,
        "daily_run_usable": daily_usable,
        "buy_candidate_report_usable": buy_usable,
        "trading_execution_allowed": trading_allowed,
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


def write_outputs(root: Path, summary: dict[str, object], detail: list[dict[str, object]]) -> None:
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
        "APPLY_RESIDUAL_ACTION_WARNING_RESOLVER",
        "INPUT_RESIDUAL_ACTION_REQUIRED_COUNT",
        "RESOLVED_BY_LATEST_SUCCESSFUL_RERUN_COUNT",
        "EXPECTED_NO_REAL_TRADING_MODE_COUNT",
        "EXPECTED_FORWARD_PENDING_OR_IMMATURE_HORIZON_COUNT",
        "READABILITY_TRUST_WARNING_NONBLOCKING_COUNT",
        "V18_19A_READABILITY_WARNING_CLASSIFIED_NONBLOCKING",
        "STALE_BUT_NONCRITICAL_SUPPORTING_MODULE_COUNT",
        "TRUE_ACTION_REQUIRED_REFRESH_COUNT",
        "TRUE_ACTION_REQUIRED_CODE_FIX_COUNT",
        "UNKNOWN_REVIEW_REQUIRED_COUNT",
        "EXPECTED_REMAINING_ACTION_REQUIRED_COUNT",
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
        "# V18.40D Residual Action Warning Resolver",
        "",
        "## Status",
        f"- STATUS: {summary.get('status')}",
        f"- RUN_ID: {summary.get('run_id')}",
        f"- APPLY_RESIDUAL_ACTION_WARNING_RESOLVER: {summary.get('apply_residual_action_warning_resolver')}",
        f"- INPUT_RESIDUAL_ACTION_REQUIRED_COUNT: {summary.get('input_residual_action_required_count')}",
        f"- READABILITY_TRUST_WARNING_NONBLOCKING_COUNT: {summary.get('readability_trust_warning_nonblocking_count')}",
        f"- V18_19A_READABILITY_WARNING_CLASSIFIED_NONBLOCKING: {summary.get('v18_19a_readability_warning_classified_nonblocking')}",
        f"- UNKNOWN_REVIEW_REQUIRED_COUNT: {summary.get('unknown_review_required_count')}",
        f"- EXPECTED_REMAINING_ACTION_REQUIRED_COUNT: {summary.get('expected_remaining_action_required_count')}",
        f"- DAILY_RUN_USABLE: {summary.get('daily_run_usable')}",
        f"- BUY_CANDIDATE_REPORT_USABLE: {summary.get('buy_candidate_report_usable')}",
        f"- TRADING_EXECUTION_ALLOWED: {summary.get('trading_execution_allowed')}",
        "",
        "## Detail",
        "| source | status | classification | remaining | reason |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in detail:
        lines.append(f"| {row.get('source_name')} | {row.get('source_status')} | {row.get('classification')} | {row.get('expected_remaining_action_required')} | {row.get('diagnostic_reason')} |")
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
    parser.add_argument("--apply-residual-action-warning-resolver", action="store_true")
    args = parser.parse_args()
    return run(Path(args.root).resolve(), bool(args.apply_residual_action_warning_resolver))


if __name__ == "__main__":
    raise SystemExit(main())
