#!/usr/bin/env python
"""V18.41A daily clean operator pipeline summary.

Aggregates the standardized safe daily pipeline outputs into one operator
status page. This is a reporting layer only; it does not modify rankings,
factor weights, candidates, ledgers, account state, broker/API state, or
trading logic.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
BROKER_API_USED = "FALSE"
ORDER_EXECUTION_USED = "FALSE"

READS = {
    "35F": "outputs/v18/ops/V18_35F_READ_FIRST.txt",
    "40A": "outputs/v18/ops/V18_40A_READ_FIRST.txt",
    "39A": "outputs/v18/ops/V18_39A_READ_FIRST.txt",
    "39B": "outputs/v18/ops/V18_39B_READ_FIRST.txt",
    "39C": "outputs/v18/ops/V18_39C_READ_FIRST.txt",
    "40B": "outputs/v18/ops/V18_40B_READ_FIRST.txt",
    "40C": "outputs/v18/ops/V18_40C_READ_FIRST.txt",
    "40D": "outputs/v18/ops/V18_40D_READ_FIRST.txt",
}
SIGNALS = "outputs/v18/signals/V18_39A_ALPHA_SIGNAL_OBJECTS.csv"
TOP_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"
FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"

OUT_READ_FIRST = "outputs/v18/ops/V18_41A_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_REPORT.md"
OUT_CURRENT = "outputs/v18/read_center/V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS.md"

SUMMARY_FIELDS = [
    "status",
    "run_id",
    "generated_at",
    "latest_signal_date",
    "latest_signal_freeze_count",
    "current_full_candidate_count",
    "current_top_candidate_count",
    "long_candidate_count",
    "top_full_mismatch_count",
    "expected_remaining_action_required_count",
    "blocking_current_failure_count",
    "daily_run_usable",
    "buy_candidate_report_usable",
    "trading_execution_allowed",
    "auto_trade",
    "auto_sell",
    "broker_api_used",
    "order_execution_used",
    "ranking_modified",
    "factor_weights_modified",
    "signal_freeze_ledger_modified",
    "paper_trading_ledger_modified",
    "shadow_portfolio_ledger_modified",
    "account_state_modified",
    "next_recommended_step",
]


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


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


def latest_freeze_count(root: Path) -> tuple[str, int]:
    rows, _ = read_csv(root / FREEZE_LEDGER)
    by_date: dict[str, set[str]] = {}
    for row in rows:
        date = str(row.get("signal_date", "")).strip()
        ticker = str(row.get("ticker", "")).upper().strip()
        if date and ticker:
            by_date.setdefault(date, set()).add(ticker)
    if not by_date:
        return "", 0
    latest = sorted(by_date)[-1]
    return latest, len(by_date[latest])


def long_candidate_tickers(root: Path) -> list[dict[str, str]]:
    rows, _ = read_csv(root / SIGNALS)
    longs = [row for row in rows if row.get("alpha_direction") == "LONG_CANDIDATE"]
    longs.sort(key=lambda row: to_int(row.get("rank")) or 10**9)
    return longs


def build(root: Path) -> tuple[dict[str, object], list[dict[str, str]]]:
    run_id = f"V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_{stamp()}"
    generated_at = now_iso()
    reads = {name: parse_kv(root / rel) for name, rel in READS.items()}
    freeze_date, freeze_count = latest_freeze_count(root)
    top_rows, _ = read_csv(root / TOP_CANDIDATES)
    longs = long_candidate_tickers(root)

    r35f = reads["35F"]
    r39a = reads["39A"]
    r40a = reads["40A"]
    r40b = reads["40B"]
    r40d = reads["40D"]

    latest_signal_date = r39a.get("LATEST_SIGNAL_DATE") or freeze_date
    latest_signal_freeze_count = to_int(r39a.get("LATEST_SIGNAL_FREEZE_COUNT")) or freeze_count
    current_full_count = to_int(r39a.get("CURRENT_FULL_CANDIDATE_COUNT"))
    current_top_count = to_int(r39a.get("CURRENT_TOP_CANDIDATE_COUNT")) or len(top_rows)
    long_count = to_int(r39a.get("LONG_CANDIDATE_COUNT")) or len(longs)
    mismatch = to_int(r39a.get("TOP_FULL_TICKER_MISMATCH_COUNT") or r40a.get("MISMATCH_COUNT"))
    remaining_action = to_int(r40d.get("EXPECTED_REMAINING_ACTION_REQUIRED_COUNT"))
    blocking = to_int(r40b.get("BLOCKING_CURRENT_FAILURE_COUNT"))
    daily_usable = r40b.get("DAILY_RUN_USABLE", "")
    buy_usable = r40b.get("BUY_CANDIDATE_REPORT_USABLE", "")
    trading_allowed = r40b.get("TRADING_EXECUTION_ALLOWED", "FALSE")

    required_statuses = [r35f.get("STATUS", ""), r40a.get("STATUS", ""), r39a.get("STATUS", ""), r40b.get("STATUS", ""), reads["40C"].get("STATUS", ""), r40d.get("STATUS", "")]
    required_failed = any(not s or s.startswith("FAIL_") for s in required_statuses)
    candidate_usable = (
        latest_signal_date
        and latest_signal_freeze_count == current_full_count
        and mismatch == 0
        and long_count == 20
        and blocking == 0
        and remaining_action == 0
        and daily_usable == "TRUE"
        and buy_usable == "TRUE"
        and trading_allowed == "FALSE"
    )
    clean_operator_ready = (
        blocking == 0
        and daily_usable == "TRUE"
        and buy_usable == "TRUE"
        and remaining_action == 0
        and mismatch == 0
        and current_top_count > 0
        and trading_allowed == "FALSE"
    )
    nonblocking_warn = any(str(s).startswith("WARN_") for s in required_statuses)
    if required_failed:
        status = "FAIL_V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_FAILED"
        next_step = "Review required step READ_FIRST files before using today's candidate report."
    elif clean_operator_ready and (nonblocking_warn or not candidate_usable):
        status = "WARN_V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_REVIEW_NEEDED"
        next_step = "Candidate report is usable; review nonblocking warnings and freshness audit before any buy-timing use."
    elif not candidate_usable:
        status = "FAIL_V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_FAILED"
        next_step = "Review required step READ_FIRST files before using today's candidate report."
    elif nonblocking_warn:
        status = "WARN_V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_REVIEW_NEEDED"
        next_step = "Candidate report is usable; review nonblocking warnings in detail reports if desired."
    else:
        status = "OK_V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_READY"
        next_step = "Use V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS.md as today's read-first operator summary."

    signal_freeze_modified = "TRUE" if r35f.get("APPLY_NEXT_SIGNAL_FREEZE_EXPANSION") == "TRUE" and to_int(r35f.get("POST_APPLY_LATEST_FREEZE_COUNT")) > 0 else "FALSE"
    paper_modified = "FALSE"
    for read in reads.values():
        if read.get("PAPER_TRADING_LEDGER_MODIFIED", "FALSE") == "TRUE":
            paper_modified = "TRUE"

    summary = {
        "status": status,
        "run_id": run_id,
        "generated_at": generated_at,
        "latest_signal_date": latest_signal_date,
        "latest_signal_freeze_count": latest_signal_freeze_count,
        "current_full_candidate_count": current_full_count,
        "current_top_candidate_count": current_top_count,
        "long_candidate_count": long_count,
        "top_full_mismatch_count": mismatch,
        "expected_remaining_action_required_count": remaining_action,
        "blocking_current_failure_count": blocking,
        "daily_run_usable": daily_usable,
        "buy_candidate_report_usable": buy_usable,
        "trading_execution_allowed": trading_allowed,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "broker_api_used": BROKER_API_USED,
        "order_execution_used": ORDER_EXECUTION_USED,
        "ranking_modified": "FALSE",
        "factor_weights_modified": "FALSE",
        "signal_freeze_ledger_modified": signal_freeze_modified,
        "paper_trading_ledger_modified": paper_modified,
        "shadow_portfolio_ledger_modified": "FALSE",
        "account_state_modified": "FALSE",
        "next_recommended_step": next_step,
    }
    return summary, longs


def render_read_first(summary: dict[str, object]) -> str:
    keys = [
        "STATUS",
        "RUN_ID",
        "GENERATED_AT",
        "LATEST_SIGNAL_DATE",
        "LATEST_SIGNAL_FREEZE_COUNT",
        "CURRENT_FULL_CANDIDATE_COUNT",
        "CURRENT_TOP_CANDIDATE_COUNT",
        "LONG_CANDIDATE_COUNT",
        "TOP_FULL_MISMATCH_COUNT",
        "EXPECTED_REMAINING_ACTION_REQUIRED_COUNT",
        "BLOCKING_CURRENT_FAILURE_COUNT",
        "DAILY_RUN_USABLE",
        "BUY_CANDIDATE_REPORT_USABLE",
        "TRADING_EXECUTION_ALLOWED",
        "AUTO_TRADE",
        "AUTO_SELL",
        "BROKER_API_USED",
        "ORDER_EXECUTION_USED",
        "RANKING_MODIFIED",
        "FACTOR_WEIGHTS_MODIFIED",
        "SIGNAL_FREEZE_LEDGER_MODIFIED",
        "PAPER_TRADING_LEDGER_MODIFIED",
        "SHADOW_PORTFOLIO_LEDGER_MODIFIED",
        "ACCOUNT_STATE_MODIFIED",
        "NEXT_RECOMMENDED_STEP",
    ]
    return "\n".join(f"{key}: {summary.get(key.lower(), '')}" for key in keys) + "\n"


def render_report(summary: dict[str, object], longs: list[dict[str, str]]) -> str:
    tickers = ", ".join(row.get("ticker", "") for row in longs)
    table = ["| rank | ticker | confidence | score |", "| ---: | --- | --- | ---: |"]
    for row in longs:
        table.append(f"| {row.get('rank')} | {row.get('ticker')} | {row.get('alpha_confidence')} | {row.get('confidence_score_numeric')} |")
    return "\n".join([
        "# V18.41A 每日 Clean Operator 状态",
        "",
        "## 今日状态",
        f"- 总状态: {summary.get('status')}",
        f"- 今日信号日期: {summary.get('latest_signal_date')}",
        f"- 最新 freeze 数量: {summary.get('latest_signal_freeze_count')}",
        f"- 当前 full candidate 数量: {summary.get('current_full_candidate_count')}",
        f"- 当前 top candidate 数量: {summary.get('current_top_candidate_count')}",
        f"- 今日 LONG_CANDIDATE 数量: {summary.get('long_candidate_count')}",
        f"- Top/Full mismatch: {summary.get('top_full_mismatch_count')}",
        f"- 是否有阻塞失败: {summary.get('blocking_current_failure_count')}",
        f"- 是否还有 action-required warning: {summary.get('expected_remaining_action_required_count')}",
        "",
        "## 交易安全",
        f"- 是否允许自动交易: {summary.get('auto_trade')}",
        f"- 是否允许自动卖出: {summary.get('auto_sell')}",
        f"- Broker API used: {summary.get('broker_api_used')}",
        f"- Order execution used: {summary.get('order_execution_used')}",
        f"- Trading execution allowed: {summary.get('trading_execution_allowed')}",
        "",
        "## 今日应该看的文件",
        "- outputs/v18/read_center/V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS.md",
        "- outputs/v18/read_center/V18_CURRENT_ALPHA_SIGNAL_OBJECTS.md",
        "- outputs/v18/signals/V18_39A_ALPHA_SIGNAL_OBJECTS.csv",
        "- outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        "",
        "## 今日人工候选池 tickers",
        tickers,
        "",
        "## LONG_CANDIDATE 明细",
        *table,
        "",
        "## 下一步",
        str(summary.get("next_recommended_step", "")),
    ]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    summary, longs = build(root)
    write_csv(root / OUT_SUMMARY, [summary], SUMMARY_FIELDS)
    write_text(root / OUT_READ_FIRST, render_read_first(summary))
    report = render_report(summary, longs)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_CURRENT, report)
    return 1 if str(summary["status"]).startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
