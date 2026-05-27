from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
import traceback
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_DRY = "OK_V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_DRY_RUN_READY"
STATUS_OK = "OK_V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_FAILED"
MODE_LIVE = "DAILY_TRADE_PLAN_SNAPSHOT_LEDGER"
MODE_DRY = "DAILY_TRADE_PLAN_SNAPSHOT_DRY_RUN"
EXPECTED_ROWS = 252

ACCOUNT_AWARE = "outputs/v18/execution/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.csv"
COST_ADJUSTED = "outputs/v18/execution/V18_CURRENT_COST_ADJUSTED_TRADE_PLAN.csv"
POSITION_POLICY = "outputs/v18/execution/V18_CURRENT_POSITION_SIZING_POLICY.csv"
BUYABILITY = "outputs/v18/execution/V18_CURRENT_BUYABILITY_GATE.csv"
RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
RANKED = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
THEMES = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
SIGNAL_FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"

R31D_READ_FIRST = "outputs/v18/ops/V18_31D_READ_FIRST.txt"
R31C_READ_FIRST = "outputs/v18/ops/V18_31C_READ_FIRST.txt"
R31C_R1_READ_FIRST = "outputs/v18/ops/V18_31C_R1_READ_FIRST.txt"
R31B_READ_FIRST = "outputs/v18/ops/V18_31B_READ_FIRST.txt"
R31A_READ_FIRST = "outputs/v18/ops/V18_31A_READ_FIRST.txt"
R30E_READ_FIRST = "outputs/v18/ops/V18_30E_READ_FIRST.txt"
R30A_READ_FIRST = "outputs/v18/ops/V18_30A_READ_FIRST.txt"

LEDGER = "state/v18/trade_plan_snapshots/V18_DAILY_TRADE_PLAN_LEDGER.csv"
BACKUP_ROOT = "archive/v18/trade_plan_snapshot_backups"
OUT_RESULT = "outputs/v18/execution/V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_RESULT.csv"
OUT_REPORT = "outputs/v18/read_center/V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_31E_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_SUMMARY.csv"
OUT_ERROR_REPORT = "outputs/v18/read_center/V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_ERROR.md"

LEDGER_FIELDS = [
    "signal_date",
    "snapshot_date",
    "snapshot_run_id",
    "generated_at",
    "source_r31d_run_id",
    "source_r31c_run_id",
    "source_r31b_run_id",
    "source_r31a_run_id",
    "source_r30e_run_id",
    "account_state_mode",
    "account_state_quality_flag",
    "account_total_value_usd",
    "cash_usd",
    "available_cash_after_reserve_usd",
    "ticker",
    "rank",
    "composite_candidate_score",
    "primary_theme",
    "recommendation_tier",
    "buy_now_status",
    "position_policy_status",
    "cost_adjusted_trade_status",
    "account_trade_status",
    "account_trade_action",
    "risk_bucket",
    "suggested_initial_notional_usd",
    "suggested_max_notional_usd",
    "suggested_account_initial_notional_usd",
    "max_additional_notional_usd",
    "estimated_total_roundtrip_cost_pct",
    "minimum_required_expected_return_pct",
    "current_position_notional_usd",
    "current_position_pct",
    "current_theme_exposure_pct",
    "projected_theme_exposure_pct_after_trade",
    "current_high_risk_exposure_pct",
    "projected_high_risk_exposure_pct_after_trade",
    "account_block_reason",
    "account_plan_reason",
    "current_trade_candidate_flag",
    "operator_readability_bucket",
    "manual_account_state_mode",
    "source_account_aware_file",
    "source_cost_adjusted_file",
    "source_position_policy_file",
    "source_buyability_file",
    "auto_trade",
    "auto_sell",
    "official_decision_impact",
    "forward_return_fillable_ready",
    "validation_status",
]

RESULT_FIELDS = [
    "run_id",
    "status",
    "signal_date",
    "snapshot_date",
    "same_day_policy",
    "ledger_path",
    "pre_ledger_rows",
    "removed_same_day_rows",
    "appended_rows",
    "post_ledger_rows",
    "duplicate_signal_date_ticker_count",
    "account_trade_allowed_count",
    "account_trade_small_only_count",
    "cost_ok_count",
    "blocked_by_min_notional_count",
    "review_first_no_current_trade_count",
    "watch_only_no_current_trade_count",
    "wait_pullback_no_current_trade_count",
    "backup_path",
    "validation_fail_count",
    "forbidden_modified",
    "notes",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "DRY_RUN",
    "TOP_N_REQUESTED",
    "SIGNAL_DATE_OVERRIDE_USED",
    "SIGNAL_DATE_OVERRIDE",
    "SIGNAL_DATE",
    "SNAPSHOT_DATE",
    "SAME_DAY_POLICY",
    "LEDGER_PATH",
    "PRE_LEDGER_ROWS",
    "REMOVED_SAME_DAY_ROWS",
    "APPENDED_ROWS",
    "POST_LEDGER_ROWS",
    "DUPLICATE_SIGNAL_DATE_TICKER_COUNT",
    "SOURCE_ACCOUNT_AWARE_FILE",
    "SOURCE_ACCOUNT_AWARE_ROWS",
    "SOURCE_COST_ADJUSTED_FILE",
    "SOURCE_COST_ADJUSTED_ROWS",
    "SOURCE_POSITION_POLICY_FILE",
    "SOURCE_POSITION_POLICY_ROWS",
    "SOURCE_BUYABILITY_FILE",
    "SOURCE_BUYABILITY_ROWS",
    "CURRENT_RANKED_CANDIDATE_ROWS",
    "CURRENT_RECOMMENDATION_ROWS",
    "CURRENT_THEME_CLASSIFICATION_ROWS",
    "LATEST_FULL_FREEZE_TICKER_COUNT",
    "ACCOUNT_TRADE_ALLOWED_COUNT",
    "ACCOUNT_TRADE_SMALL_ONLY_COUNT",
    "ACCOUNT_WATCH_ONLY_COUNT",
    "ACCOUNT_WAIT_PULLBACK_COUNT",
    "ACCOUNT_REVIEW_FIRST_COUNT",
    "BLOCKED_BY_COST_PLAN_COUNT",
    "BLOCKED_BY_DAILY_NEW_BUY_LIMIT_COUNT",
    "COST_OK_COUNT",
    "CURRENT_COST_OK_CANDIDATE_COUNT",
    "CURRENT_BLOCKED_MIN_NOTIONAL_COUNT",
    "REVIEW_FIRST_NO_CURRENT_TRADE_COUNT",
    "WATCH_ONLY_NO_CURRENT_TRADE_COUNT",
    "WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT",
    "ACCOUNT_STATE_MODE",
    "ACCOUNT_STATE_QUALITY_FLAG",
    "R31D_STATUS",
    "R31C_STATUS",
    "R31C_R1_STATUS",
    "R31B_STATUS",
    "R31A_STATUS",
    "R30E_STATUS",
    "R30A_STATUS",
    "FORWARD_RETURN_FILLABLE_READY",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "BACKUP_PATH",
    "NEXT_RECOMMENDED_STEP",
]

SUMMARY_FIELDS = [
    "run_id",
    "status",
    "generated_at",
    "signal_date",
    "snapshot_date",
    "same_day_policy",
    "pre_ledger_rows",
    "removed_same_day_rows",
    "appended_rows",
    "post_ledger_rows",
    "duplicate_signal_date_ticker_count",
    "source_account_aware_rows",
    "source_cost_adjusted_rows",
    "account_trade_allowed_count",
    "account_trade_small_only_count",
    "cost_ok_count",
    "blocked_by_min_notional_count",
    "account_state_mode",
    "account_state_quality_flag",
    "validation_fail_count",
    "forbidden_modified",
    "notes",
]

PROTECTED_INPUTS = [
    ACCOUNT_AWARE,
    COST_ADJUSTED,
    POSITION_POLICY,
    BUYABILITY,
    RECOMMENDATIONS,
    RANKED,
    THEMES,
    SIGNAL_FREEZE_LEDGER,
]


def norm(value: object) -> str:
    return "" if value is None else str(value).strip()


def upper(value: object) -> str:
    return norm(value).upper()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def to_int(value: object, default: int = 0) -> int:
    try:
        text = norm(value)
        return int(float(text)) if text else default
    except Exception:
        return default


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    raise RuntimeError(f"Unable to read CSV: {path}")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_status_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def protected_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    return {rel: file_sig(root / rel) for rel in PROTECTED_INPUTS}


def parse_date(value: object) -> str:
    text = norm(value)
    if not text:
        return ""
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%m-%d-%Y"):
        try:
            return dt.datetime.strptime(text[:10], fmt).date().isoformat()
        except Exception:
            continue
    return ""


def latest_full_freeze_signal_date(root: Path) -> Tuple[str, int]:
    rows, _fields = read_csv(root / SIGNAL_FREEZE_LEDGER)
    by_date: Dict[str, set[str]] = {}
    for row in rows:
        signal_date = parse_date(row.get("signal_date"))
        ticker = upper(row.get("ticker"))
        if signal_date and ticker:
            by_date.setdefault(signal_date, set()).add(ticker)
    full_dates = [(date, len(tickers)) for date, tickers in by_date.items() if len(tickers) == EXPECTED_ROWS]
    if not full_dates:
        latest = max(by_date.items(), default=("", set()), key=lambda item: item[0])
        return latest[0], len(latest[1]) if latest[0] else 0
    latest_date, count = max(full_dates, key=lambda item: item[0])
    return latest_date, count


def determine_signal_date(root: Path) -> Tuple[str, str, int]:
    r30e = read_status_file(root / R30E_READ_FIRST)
    for field in ("SIGNAL_DATE", "R21_SIGNAL_DATE"):
        value = parse_date(r30e.get(field))
        if value:
            return value, "R30E_READ_FIRST", to_int(r30e.get("LATEST_FULL_FREEZE_TICKER_COUNT"), EXPECTED_ROWS)
    r30a = read_status_file(root / R30A_READ_FIRST)
    for field in ("LATEST_FULL_FREEZE_SIGNAL_DATE", "LATEST_FULL_SIGNAL_FREEZE_DATE", "SIGNAL_DATE"):
        value = parse_date(r30a.get(field))
        if value:
            return value, "R30A_READ_FIRST", to_int(r30a.get("LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT"), EXPECTED_ROWS)
    freeze_date, count = latest_full_freeze_signal_date(root)
    if freeze_date:
        return freeze_date, "LATEST_FULL_SIGNAL_FREEZE_LEDGER", count
    return dt.date.today().isoformat(), "CURRENT_DATE_FALLBACK", 0


def duplicate_signal_date_ticker_count(rows: Sequence[Dict[str, object]]) -> int:
    counts = Counter((norm(row.get("signal_date")), upper(row.get("ticker"))) for row in rows)
    return sum(1 for (signal_date, ticker), count in counts.items() if signal_date and ticker and count > 1)


def md_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: int = 25) -> str:
    selected = list(rows[:limit])
    if not selected:
        return "_None._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in selected:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def build_snapshot_rows(root: Path, account_rows: Sequence[Dict[str, str]], cost_rows: Sequence[Dict[str, str]], values: Dict[str, object], signal_date: str, snapshot_date: str, run_id: str, generated_at: str) -> List[Dict[str, object]]:
    cost_by_ticker = {upper(row.get("ticker")): row for row in cost_rows}
    out: List[Dict[str, object]] = []
    for row in account_rows:
        ticker = upper(row.get("ticker"))
        cost = cost_by_ticker.get(ticker, {})
        out.append({
            "signal_date": signal_date,
            "snapshot_date": snapshot_date,
            "snapshot_run_id": run_id,
            "generated_at": generated_at,
            "source_r31d_run_id": values.get("SOURCE_R31D_RUN_ID", ""),
            "source_r31c_run_id": values.get("SOURCE_R31C_RUN_ID", ""),
            "source_r31b_run_id": values.get("SOURCE_R31B_RUN_ID", ""),
            "source_r31a_run_id": values.get("SOURCE_R31A_RUN_ID", ""),
            "source_r30e_run_id": values.get("SOURCE_R30E_RUN_ID", ""),
            "account_state_mode": values.get("ACCOUNT_STATE_MODE", ""),
            "account_state_quality_flag": values.get("ACCOUNT_STATE_QUALITY_FLAG", ""),
            "account_total_value_usd": values.get("ACCOUNT_TOTAL_VALUE_USD", ""),
            "cash_usd": values.get("CASH_USD", ""),
            "available_cash_after_reserve_usd": values.get("AVAILABLE_CASH_AFTER_RESERVE_USD", ""),
            "ticker": ticker,
            "rank": row.get("rank", ""),
            "composite_candidate_score": row.get("composite_candidate_score", ""),
            "primary_theme": row.get("primary_theme", ""),
            "recommendation_tier": row.get("recommendation_tier", ""),
            "buy_now_status": row.get("buy_now_status", ""),
            "position_policy_status": row.get("position_policy_status", ""),
            "cost_adjusted_trade_status": row.get("cost_adjusted_trade_status", ""),
            "account_trade_status": row.get("account_trade_status", ""),
            "account_trade_action": row.get("account_trade_action", ""),
            "risk_bucket": row.get("risk_bucket", ""),
            "suggested_initial_notional_usd": row.get("suggested_initial_notional_usd", ""),
            "suggested_max_notional_usd": row.get("suggested_max_notional_usd", ""),
            "suggested_account_initial_notional_usd": row.get("suggested_account_initial_notional_usd", ""),
            "max_additional_notional_usd": row.get("max_additional_notional_usd", ""),
            "estimated_total_roundtrip_cost_pct": row.get("estimated_total_roundtrip_cost_pct", ""),
            "minimum_required_expected_return_pct": row.get("minimum_required_expected_return_pct", ""),
            "current_position_notional_usd": row.get("current_position_notional_usd", ""),
            "current_position_pct": row.get("current_position_pct", ""),
            "current_theme_exposure_pct": row.get("current_theme_exposure_pct", ""),
            "projected_theme_exposure_pct_after_trade": row.get("projected_theme_exposure_pct_after_trade", ""),
            "current_high_risk_exposure_pct": row.get("current_high_risk_exposure_pct", ""),
            "projected_high_risk_exposure_pct_after_trade": row.get("projected_high_risk_exposure_pct_after_trade", ""),
            "account_block_reason": row.get("account_block_reason", ""),
            "account_plan_reason": row.get("account_plan_reason", ""),
            "current_trade_candidate_flag": cost.get("current_trade_candidate_flag", ""),
            "operator_readability_bucket": cost.get("operator_readability_bucket", ""),
            "manual_account_state_mode": row.get("manual_account_state_mode", ""),
            "source_account_aware_file": str(root / ACCOUNT_AWARE),
            "source_cost_adjusted_file": str(root / COST_ADJUSTED),
            "source_position_policy_file": str(root / POSITION_POLICY),
            "source_buyability_file": str(root / BUYABILITY),
            "auto_trade": values.get("AUTO_TRADE", "DISABLED"),
            "auto_sell": values.get("AUTO_SELL", "DISABLED"),
            "official_decision_impact": values.get("OFFICIAL_DECISION_IMPACT", "NONE"),
            "forward_return_fillable_ready": values.get("FORWARD_RETURN_FILLABLE_READY", "FALSE"),
            "validation_status": values.get("STATUS", ""),
        })
    return out


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def build_summary(values: Dict[str, object], notes: str) -> List[Dict[str, object]]:
    return [{
        "run_id": values.get("RUN_ID", ""),
        "status": values.get("STATUS", ""),
        "generated_at": values.get("_GENERATED_AT", ""),
        "signal_date": values.get("SIGNAL_DATE", ""),
        "snapshot_date": values.get("SNAPSHOT_DATE", ""),
        "same_day_policy": values.get("SAME_DAY_POLICY", ""),
        "pre_ledger_rows": values.get("PRE_LEDGER_ROWS", ""),
        "removed_same_day_rows": values.get("REMOVED_SAME_DAY_ROWS", ""),
        "appended_rows": values.get("APPENDED_ROWS", ""),
        "post_ledger_rows": values.get("POST_LEDGER_ROWS", ""),
        "duplicate_signal_date_ticker_count": values.get("DUPLICATE_SIGNAL_DATE_TICKER_COUNT", ""),
        "source_account_aware_rows": values.get("SOURCE_ACCOUNT_AWARE_ROWS", ""),
        "source_cost_adjusted_rows": values.get("SOURCE_COST_ADJUSTED_ROWS", ""),
        "account_trade_allowed_count": values.get("ACCOUNT_TRADE_ALLOWED_COUNT", ""),
        "account_trade_small_only_count": values.get("ACCOUNT_TRADE_SMALL_ONLY_COUNT", ""),
        "cost_ok_count": values.get("COST_OK_COUNT", ""),
        "blocked_by_min_notional_count": values.get("CURRENT_BLOCKED_MIN_NOTIONAL_COUNT", ""),
        "account_state_mode": values.get("ACCOUNT_STATE_MODE", ""),
        "account_state_quality_flag": values.get("ACCOUNT_STATE_QUALITY_FLAG", ""),
        "validation_fail_count": values.get("VALIDATION_FAIL_COUNT", ""),
        "forbidden_modified": values.get("FORBIDDEN_MODIFIED", ""),
        "notes": notes,
    }]


def build_result(values: Dict[str, object], notes: str) -> List[Dict[str, object]]:
    return [{
        "run_id": values.get("RUN_ID", ""),
        "status": values.get("STATUS", ""),
        "signal_date": values.get("SIGNAL_DATE", ""),
        "snapshot_date": values.get("SNAPSHOT_DATE", ""),
        "same_day_policy": values.get("SAME_DAY_POLICY", ""),
        "ledger_path": values.get("LEDGER_PATH", ""),
        "pre_ledger_rows": values.get("PRE_LEDGER_ROWS", ""),
        "removed_same_day_rows": values.get("REMOVED_SAME_DAY_ROWS", ""),
        "appended_rows": values.get("APPENDED_ROWS", ""),
        "post_ledger_rows": values.get("POST_LEDGER_ROWS", ""),
        "duplicate_signal_date_ticker_count": values.get("DUPLICATE_SIGNAL_DATE_TICKER_COUNT", ""),
        "account_trade_allowed_count": values.get("ACCOUNT_TRADE_ALLOWED_COUNT", ""),
        "account_trade_small_only_count": values.get("ACCOUNT_TRADE_SMALL_ONLY_COUNT", ""),
        "cost_ok_count": values.get("COST_OK_COUNT", ""),
        "blocked_by_min_notional_count": values.get("CURRENT_BLOCKED_MIN_NOTIONAL_COUNT", ""),
        "review_first_no_current_trade_count": values.get("REVIEW_FIRST_NO_CURRENT_TRADE_COUNT", ""),
        "watch_only_no_current_trade_count": values.get("WATCH_ONLY_NO_CURRENT_TRADE_COUNT", ""),
        "wait_pullback_no_current_trade_count": values.get("WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT", ""),
        "backup_path": values.get("BACKUP_PATH", ""),
        "validation_fail_count": values.get("VALIDATION_FAIL_COUNT", ""),
        "forbidden_modified": values.get("FORBIDDEN_MODIFIED", ""),
        "notes": notes,
    }]


def build_report(values: Dict[str, object]) -> str:
    warnings: List[str] = []
    if values.get("FORWARD_RETURN_FILLABLE_READY") == "FALSE":
        warnings.append("FORWARD_RETURN_NOT_READY_TRADE_PLAN_SNAPSHOT_ONLY")
    if str(values.get("ACCOUNT_STATE_QUALITY_FLAG", "")).startswith("WARN_"):
        warnings.append(str(values.get("ACCOUNT_STATE_QUALITY_FLAG")))
    if values.get("_SIGNAL_DATE_SOURCE") == "CURRENT_DATE_FALLBACK":
        warnings.append("WEAK_SIGNAL_DATE_INFERENCE_CURRENT_DATE_FALLBACK")
    if values.get("SIGNAL_DATE_OVERRIDE_USED") == "TRUE":
        warnings.append("SIGNAL_DATE_OVERRIDE_USED")
    if values.get("SAME_DAY_POLICY") == "APPEND_EXPLICIT":
        warnings.append("APPEND_EXPLICIT_CAN_CREATE_SAME_DAY_DUPLICATES")
    if not warnings:
        warnings.append("NONE")
    return "\n".join([
        "# V18.31E Daily Trade Plan Snapshot Ledger",
        "",
        "## 1. Final Status",
        f"STATUS: {values.get('STATUS', '')}",
        "",
        "## 2. Run Id / Signal Date / Snapshot Date",
        f"- RUN_ID: `{values.get('RUN_ID', '')}`",
        f"- SIGNAL_DATE: `{values.get('SIGNAL_DATE', '')}`",
        f"- SNAPSHOT_DATE: `{values.get('SNAPSHOT_DATE', '')}`",
        "",
        "## 3. Same-Day Policy Result",
        f"- SAME_DAY_POLICY: `{values.get('SAME_DAY_POLICY', '')}`",
        f"- REMOVED_SAME_DAY_ROWS: `{values.get('REMOVED_SAME_DAY_ROWS', '')}`",
        f"- APPENDED_ROWS: `{values.get('APPENDED_ROWS', '')}`",
        f"- BACKUP_PATH: `{values.get('BACKUP_PATH', '')}`",
        "",
        "## 4. Ledger Row Counts Before/After",
        f"- PRE_LEDGER_ROWS: `{values.get('PRE_LEDGER_ROWS', '')}`",
        f"- POST_LEDGER_ROWS: `{values.get('POST_LEDGER_ROWS', '')}`",
        "",
        "## 5. Duplicate Key Check",
        f"- DUPLICATE_SIGNAL_DATE_TICKER_COUNT: `{values.get('DUPLICATE_SIGNAL_DATE_TICKER_COUNT', '')}`",
        "",
        "## 6. Account-Aware Allowed Candidates Snapshot Count",
        f"- ACCOUNT_TRADE_ALLOWED_COUNT: `{values.get('ACCOUNT_TRADE_ALLOWED_COUNT', '')}`",
        f"- ACCOUNT_TRADE_SMALL_ONLY_COUNT: `{values.get('ACCOUNT_TRADE_SMALL_ONLY_COUNT', '')}`",
        "",
        "## 7. Cost-Ok / Min-Notional / Review-First Snapshot Count",
        f"- COST_OK_COUNT: `{values.get('COST_OK_COUNT', '')}`",
        f"- CURRENT_COST_OK_CANDIDATE_COUNT: `{values.get('CURRENT_COST_OK_CANDIDATE_COUNT', '')}`",
        f"- CURRENT_BLOCKED_MIN_NOTIONAL_COUNT: `{values.get('CURRENT_BLOCKED_MIN_NOTIONAL_COUNT', '')}`",
        f"- REVIEW_FIRST_NO_CURRENT_TRADE_COUNT: `{values.get('REVIEW_FIRST_NO_CURRENT_TRADE_COUNT', '')}`",
        f"- WATCH_ONLY_NO_CURRENT_TRADE_COUNT: `{values.get('WATCH_ONLY_NO_CURRENT_TRADE_COUNT', '')}`",
        f"- WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT: `{values.get('WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT', '')}`",
        "",
        "## 8. Account State Mode And Warning",
        f"- ACCOUNT_STATE_MODE: `{values.get('ACCOUNT_STATE_MODE', '')}`",
        f"- ACCOUNT_STATE_QUALITY_FLAG: `{values.get('ACCOUNT_STATE_QUALITY_FLAG', '')}`",
        "",
        "## 9. Safety",
        "- Manual research ledger only.",
        "- No broker connection.",
        "- No order placement.",
        "- `AUTO_TRADE: DISABLED`",
        "- `AUTO_SELL: DISABLED`",
        "- `OFFICIAL_DECISION_IMPACT: NONE`",
        "",
        "## 10. What This Ledger Enables",
        "- Future validation of ACCOUNT_TRADE_ALLOWED.",
        "- Future validation of COST_OK.",
        "- Future validation of min-notional blocks.",
        "- Future validation of watch-only/wait-pullback.",
        "",
        "## 11. Warnings",
        "\n".join(f"- `{warning}`" for warning in warnings),
        "",
        "## 12. Next Step",
        "- Integrate R31A-D/E into daily trade-readiness runner.",
        "- Run forward validation after future price data exists.",
    ]) + "\n"


def validation_fail_count(values: Dict[str, object]) -> int:
    fails = 0
    if values.get("AUTO_TRADE") != "DISABLED":
        fails += 1
    if values.get("AUTO_SELL") != "DISABLED":
        fails += 1
    if values.get("OFFICIAL_DECISION_IMPACT") != "NONE":
        fails += 1
    if values.get("FORBIDDEN_MODIFIED") != "FALSE":
        fails += 1
    if to_int(values.get("SOURCE_ACCOUNT_AWARE_ROWS")) != EXPECTED_ROWS:
        fails += 1
    if to_int(values.get("SOURCE_COST_ADJUSTED_ROWS")) != EXPECTED_ROWS:
        fails += 1
    if to_int(values.get("SOURCE_POSITION_POLICY_ROWS")) != EXPECTED_ROWS:
        fails += 1
    if to_int(values.get("SOURCE_BUYABILITY_ROWS")) != EXPECTED_ROWS:
        fails += 1
    if to_int(values.get("CURRENT_RANKED_CANDIDATE_ROWS")) != EXPECTED_ROWS:
        fails += 1
    if to_int(values.get("CURRENT_RECOMMENDATION_ROWS")) != EXPECTED_ROWS:
        fails += 1
    if to_int(values.get("CURRENT_THEME_CLASSIFICATION_ROWS")) != EXPECTED_ROWS:
        fails += 1
    latest_freeze = to_int(values.get("LATEST_FULL_FREEZE_TICKER_COUNT"))
    if latest_freeze not in (0, EXPECTED_ROWS):
        fails += 1
    if values.get("SAME_DAY_POLICY") != "APPEND_EXPLICIT" and to_int(values.get("DUPLICATE_SIGNAL_DATE_TICKER_COUNT")) != 0:
        fails += 1
    return fails


def run(root: Path, args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    now = dt.datetime.now()
    run_id = now.strftime("V18_31E_%Y%m%d_%H%M%S")
    generated_at = now.isoformat(timespec="seconds")
    snapshot_date = now.date().isoformat()
    before = protected_sig(root)
    ledger_path = root / LEDGER
    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    account_rows, _account_fields = read_csv(root / ACCOUNT_AWARE)
    cost_rows, _cost_fields = read_csv(root / COST_ADJUSTED)
    pos_rows, _pos_fields = read_csv(root / POSITION_POLICY)
    buy_rows, _buy_fields = read_csv(root / BUYABILITY)
    rec_rows, _rec_fields = read_csv(root / RECOMMENDATIONS)
    ranked_rows, _ranked_fields = read_csv(root / RANKED)
    theme_rows, _theme_fields = read_csv(root / THEMES)
    ledger_rows, _ledger_fields = read_csv(ledger_path)
    required_missing = [rel for rel in [ACCOUNT_AWARE, COST_ADJUSTED, POSITION_POLICY, BUYABILITY, RECOMMENDATIONS, RANKED, THEMES] if not (root / rel).exists()]

    r31d = read_status_file(root / R31D_READ_FIRST)
    r31c = read_status_file(root / R31C_READ_FIRST)
    r31c_r1 = read_status_file(root / R31C_R1_READ_FIRST)
    r31b = read_status_file(root / R31B_READ_FIRST)
    r31a = read_status_file(root / R31A_READ_FIRST)
    r30e = read_status_file(root / R30E_READ_FIRST)
    r30a = read_status_file(root / R30A_READ_FIRST)
    signal_date, signal_source, latest_freeze_count = determine_signal_date(root)
    signal_date_override = parse_date(getattr(args, "signal_date_override", ""))
    if signal_date_override:
        signal_date = signal_date_override
        signal_source = "CLI_SIGNAL_DATE_OVERRIDE"
    if to_int(r31d.get("LATEST_FULL_FREEZE_TICKER_COUNT")):
        latest_freeze_count = to_int(r31d.get("LATEST_FULL_FREEZE_TICKER_COUNT"))

    account_counts = Counter(upper(row.get("account_trade_status")) for row in account_rows)
    cost_counts = Counter(upper(row.get("cost_adjusted_trade_status")) for row in cost_rows)
    cost_substatus_counts = Counter(upper(row.get("cost_review_substatus")) for row in cost_rows)
    current_cost_ok = sum(1 for row in cost_rows if upper(row.get("current_trade_candidate_flag")) == "TRUE")
    same_day_rows = [row for row in ledger_rows if norm(row.get("signal_date")) == signal_date]
    pre_ledger_rows = len(ledger_rows)
    removed_same_day_rows = 0
    appended_rows = 0
    backup_path = ""
    working_ledger = list(ledger_rows)

    values: Dict[str, object] = {
        "STATUS": STATUS_DRY if args.dry_run else STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": run_id,
        "DRY_RUN": bool_text(args.dry_run),
        "TOP_N_REQUESTED": args.top_n,
        "SIGNAL_DATE_OVERRIDE_USED": bool_text(bool(signal_date_override)),
        "SIGNAL_DATE_OVERRIDE": signal_date_override,
        "SIGNAL_DATE": signal_date,
        "SNAPSHOT_DATE": snapshot_date,
        "SAME_DAY_POLICY": args.same_day_policy,
        "LEDGER_PATH": str(ledger_path),
        "PRE_LEDGER_ROWS": pre_ledger_rows,
        "REMOVED_SAME_DAY_ROWS": 0,
        "APPENDED_ROWS": 0,
        "POST_LEDGER_ROWS": pre_ledger_rows,
        "DUPLICATE_SIGNAL_DATE_TICKER_COUNT": duplicate_signal_date_ticker_count(ledger_rows),
        "SOURCE_ACCOUNT_AWARE_FILE": str(root / ACCOUNT_AWARE),
        "SOURCE_ACCOUNT_AWARE_ROWS": len(account_rows),
        "SOURCE_COST_ADJUSTED_FILE": str(root / COST_ADJUSTED),
        "SOURCE_COST_ADJUSTED_ROWS": len(cost_rows),
        "SOURCE_POSITION_POLICY_FILE": str(root / POSITION_POLICY),
        "SOURCE_POSITION_POLICY_ROWS": len(pos_rows),
        "SOURCE_BUYABILITY_FILE": str(root / BUYABILITY),
        "SOURCE_BUYABILITY_ROWS": len(buy_rows),
        "CURRENT_RANKED_CANDIDATE_ROWS": len(ranked_rows),
        "CURRENT_RECOMMENDATION_ROWS": len(rec_rows),
        "CURRENT_THEME_CLASSIFICATION_ROWS": len(theme_rows),
        "LATEST_FULL_FREEZE_TICKER_COUNT": latest_freeze_count,
        "ACCOUNT_TRADE_ALLOWED_COUNT": account_counts.get("ACCOUNT_TRADE_ALLOWED", 0),
        "ACCOUNT_TRADE_SMALL_ONLY_COUNT": account_counts.get("ACCOUNT_TRADE_SMALL_ONLY", 0),
        "ACCOUNT_WATCH_ONLY_COUNT": account_counts.get("ACCOUNT_WATCH_ONLY", 0),
        "ACCOUNT_WAIT_PULLBACK_COUNT": account_counts.get("ACCOUNT_WAIT_PULLBACK", 0),
        "ACCOUNT_REVIEW_FIRST_COUNT": account_counts.get("ACCOUNT_REVIEW_FIRST", 0),
        "BLOCKED_BY_COST_PLAN_COUNT": account_counts.get("BLOCKED_BY_COST_PLAN", 0),
        "BLOCKED_BY_DAILY_NEW_BUY_LIMIT_COUNT": account_counts.get("BLOCKED_BY_DAILY_NEW_BUY_LIMIT", 0),
        "COST_OK_COUNT": cost_counts.get("COST_OK", 0),
        "CURRENT_COST_OK_CANDIDATE_COUNT": current_cost_ok,
        "CURRENT_BLOCKED_MIN_NOTIONAL_COUNT": cost_counts.get("BLOCKED_BY_MIN_NOTIONAL", 0),
        "REVIEW_FIRST_NO_CURRENT_TRADE_COUNT": cost_substatus_counts.get("REVIEW_FIRST_NO_CURRENT_TRADE", 0),
        "WATCH_ONLY_NO_CURRENT_TRADE_COUNT": cost_substatus_counts.get("WATCH_ONLY_NO_CURRENT_TRADE", 0),
        "WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT": cost_substatus_counts.get("WAIT_PULLBACK_NO_CURRENT_TRADE", 0),
        "ACCOUNT_STATE_MODE": r31d.get("ACCOUNT_STATE_MODE", ""),
        "ACCOUNT_STATE_QUALITY_FLAG": r31d.get("ACCOUNT_STATE_QUALITY_FLAG", ""),
        "R31D_STATUS": r31d.get("STATUS", ""),
        "R31C_STATUS": r31c.get("STATUS", ""),
        "R31C_R1_STATUS": r31c.get("R31C_R1_STATUS") or r31c_r1.get("STATUS", ""),
        "R31B_STATUS": r31b.get("STATUS", ""),
        "R31A_STATUS": r31a.get("STATUS", ""),
        "R30E_STATUS": r30e.get("STATUS", ""),
        "R30A_STATUS": r30a.get("STATUS", ""),
        "FORWARD_RETURN_FILLABLE_READY": r31d.get("FORWARD_RETURN_FILLABLE_READY") or r31c.get("FORWARD_RETURN_FILLABLE_READY") or "FALSE",
        "AUTO_TRADE": r31d.get("AUTO_TRADE") or r31c.get("AUTO_TRADE") or "DISABLED",
        "AUTO_SELL": r31d.get("AUTO_SELL") or r31c.get("AUTO_SELL") or "DISABLED",
        "OFFICIAL_DECISION_IMPACT": r31d.get("OFFICIAL_DECISION_IMPACT") or r31c.get("OFFICIAL_DECISION_IMPACT") or "NONE",
        "VALIDATION_FAIL_COUNT": 0,
        "FORBIDDEN_MODIFIED": "FALSE",
        "BACKUP_PATH": "",
        "NEXT_RECOMMENDED_STEP": "",
        "SOURCE_R31D_RUN_ID": r31d.get("RUN_ID", ""),
        "SOURCE_R31C_RUN_ID": r31c.get("RUN_ID", ""),
        "SOURCE_R31B_RUN_ID": r31b.get("RUN_ID", ""),
        "SOURCE_R31A_RUN_ID": r31a.get("RUN_ID", ""),
        "SOURCE_R30E_RUN_ID": r30e.get("RUN_ID", ""),
        "ACCOUNT_TOTAL_VALUE_USD": r31d.get("ACCOUNT_TOTAL_VALUE_USD", ""),
        "CASH_USD": r31d.get("CASH_USD", ""),
        "AVAILABLE_CASH_AFTER_RESERVE_USD": r31d.get("AVAILABLE_CASH_AFTER_RESERVE_USD", ""),
        "_GENERATED_AT": generated_at,
        "_SIGNAL_DATE_SOURCE": signal_source,
    }

    snapshot_rows = [] if required_missing else build_snapshot_rows(root, account_rows[: max(args.top_n, 0)], cost_rows, values, signal_date, snapshot_date, run_id, generated_at)
    notes = ""
    if args.dry_run:
        notes = "Dry run only; trade plan ledger not modified."
        values["STATUS"] = STATUS_DRY
        values["NEXT_RECOMMENDED_STEP"] = "Run live R31E to write or replace the daily trade plan snapshot."
    elif required_missing:
        notes = "Missing required inputs: " + "; ".join(required_missing)
        values["STATUS"] = STATUS_FAIL
        values["NEXT_RECOMMENDED_STEP"] = "Restore required R31D/R31C/R31B/R31A inputs before snapshotting."
    elif len(account_rows) != EXPECTED_ROWS or len(cost_rows) != EXPECTED_ROWS or len(pos_rows) != EXPECTED_ROWS or len(buy_rows) != EXPECTED_ROWS or len(snapshot_rows) != args.top_n:
        notes = "Structural row count mismatch."
        values["STATUS"] = STATUS_FAIL
        values["NEXT_RECOMMENDED_STEP"] = "Rerun R31A/R31B/R31C/R31D before snapshotting."
    else:
        if same_day_rows and args.same_day_policy == "REPLACE":
            backup_dir = root / BACKUP_ROOT / run_id
            backup_file = backup_dir / "V18_DAILY_TRADE_PLAN_LEDGER_PRE_REPLACE.csv"
            backup_dir.mkdir(parents=True, exist_ok=True)
            if ledger_path.exists():
                shutil.copy2(ledger_path, backup_file)
            else:
                write_csv(backup_file, [], LEDGER_FIELDS)
            backup_path = str(backup_file)
            working_ledger = [row for row in ledger_rows if norm(row.get("signal_date")) != signal_date]
            removed_same_day_rows = len(same_day_rows)
        elif same_day_rows and args.same_day_policy == "SKIP":
            snapshot_rows = []
            notes = "Existing same-day snapshot skipped by same-day policy."
        elif same_day_rows and args.same_day_policy == "APPEND_EXPLICIT":
            notes = "APPEND_EXPLICIT used; same-day duplicate warning allowed."
        if args.same_day_policy != "SKIP" or not same_day_rows:
            write_csv(ledger_path, working_ledger + snapshot_rows, LEDGER_FIELDS)
            appended_rows = len(snapshot_rows)
        post_rows, _post_fields = read_csv(ledger_path)
        duplicate_count = duplicate_signal_date_ticker_count(post_rows)
        values["REMOVED_SAME_DAY_ROWS"] = removed_same_day_rows
        values["APPENDED_ROWS"] = appended_rows
        values["POST_LEDGER_ROWS"] = len(post_rows)
        values["DUPLICATE_SIGNAL_DATE_TICKER_COUNT"] = duplicate_count
        values["BACKUP_PATH"] = backup_path
        if args.same_day_policy != "APPEND_EXPLICIT" and duplicate_count:
            values["STATUS"] = STATUS_FAIL
            notes = "Duplicate signal_date+ticker keys remain after snapshot write."
            values["NEXT_RECOMMENDED_STEP"] = "Inspect trade plan snapshot ledger before using it for validation."
        elif str(values.get("ACCOUNT_STATE_QUALITY_FLAG", "")).startswith("WARN_") or values["FORWARD_RETURN_FILLABLE_READY"] == "FALSE" or signal_source == "CURRENT_DATE_FALLBACK" or args.same_day_policy == "APPEND_EXPLICIT":
            values["STATUS"] = STATUS_WARN
            notes = notes or "WARN_TEMPLATE_OR_FORWARD_RETURN_NOT_READY"
            values["NEXT_RECOMMENDED_STEP"] = "Use ledger for manual research only; update account state and run forward validation later."
        else:
            values["STATUS"] = STATUS_OK
            notes = notes or "Daily trade plan snapshot ledger ready."
            values["NEXT_RECOMMENDED_STEP"] = "Integrate R31A-D/E into the daily trade-readiness runner."

    after = protected_sig(root)
    values["FORBIDDEN_MODIFIED"] = bool_text(after != before)
    if values["FORBIDDEN_MODIFIED"] != "FALSE":
        values["STATUS"] = STATUS_FAIL
        notes = "Forbidden input modification detected."
        values["NEXT_RECOMMENDED_STEP"] = "Inspect R31E error report; do not use this snapshot."
    values["VALIDATION_FAIL_COUNT"] = validation_fail_count(values)
    if values["VALIDATION_FAIL_COUNT"] and values["STATUS"] != STATUS_DRY:
        values["STATUS"] = STATUS_FAIL

    write_csv(root / OUT_RESULT, build_result(values, notes), RESULT_FIELDS)
    write_csv(root / OUT_SUMMARY, build_summary(values, notes), SUMMARY_FIELDS)
    write_text(root / OUT_REPORT, build_report(values))
    write_read_first(root / OUT_READ_FIRST, values)
    if values["STATUS"] == STATUS_FAIL:
        write_text(root / OUT_ERROR_REPORT, f"# V18.31E Daily Trade Plan Snapshot Error\n\n```text\n{notes}\n```\n")
        return 1, values
    return 0, values


def write_failure(root: Path, error: BaseException, args: argparse.Namespace) -> Dict[str, object]:
    now = dt.datetime.now()
    values: Dict[str, object] = {field: "" for field in READ_FIRST_FIELDS}
    values.update({
        "STATUS": STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": now.strftime("V18_31E_%Y%m%d_%H%M%S"),
        "DRY_RUN": bool_text(args.dry_run),
        "TOP_N_REQUESTED": args.top_n,
        "SIGNAL_DATE_OVERRIDE_USED": bool_text(bool(getattr(args, "signal_date_override", ""))),
        "SIGNAL_DATE_OVERRIDE": getattr(args, "signal_date_override", ""),
        "SAME_DAY_POLICY": args.same_day_policy,
        "LEDGER_PATH": str(root / LEDGER),
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "VALIDATION_FAIL_COUNT": 1,
        "FORBIDDEN_MODIFIED": "UNKNOWN",
        "NEXT_RECOMMENDED_STEP": "Inspect R31E error report.",
        "_GENERATED_AT": now.isoformat(timespec="seconds"),
    })
    write_read_first(root / OUT_READ_FIRST, values)
    write_csv(root / OUT_SUMMARY, build_summary(values, str(error)), SUMMARY_FIELDS)
    write_csv(root / OUT_RESULT, build_result(values, str(error)), RESULT_FIELDS)
    write_text(root / OUT_ERROR_REPORT, f"# V18.31E Daily Trade Plan Snapshot Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.31E daily trade plan snapshot ledger.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--top-n", type=int, default=252)
    parser.add_argument("--same-day-policy", choices=["REPLACE", "SKIP", "APPEND_EXPLICIT"], default="REPLACE")
    parser.add_argument("--signal-date-override", default="")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-open", action="store_true", help="Compatibility flag; no files are opened by this script.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        code, values = run(root, args)
        print(f"STATUS: {values.get('STATUS', '')}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return code
    except Exception as exc:
        values = write_failure(root, exc, args)
        print(f"STATUS: {values.get('STATUS', STATUS_FAIL)}")
        print(f"ERROR: {exc}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
