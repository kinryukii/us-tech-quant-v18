from __future__ import annotations

import argparse
import csv
import datetime as dt
import subprocess
import traceback
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRY = "OK_V18_31F_FULL_DAILY_TRADE_READINESS_DRY_RUN_READY"
STATUS_OK = "OK_V18_31F_FULL_DAILY_TRADE_READINESS_READY"
STATUS_WARN = "WARN_V18_31F_FULL_DAILY_TRADE_READINESS_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_31F_FULL_DAILY_TRADE_READINESS_FAILED"
STATUS_R1_WARN = "WARN_V18_31F_R1_NON_TRADING_DAY_REUSE_LATEST_READY"
STATUS_R1_STRUCT_FAIL = "FAIL_V18_31F_R1_STRUCTURAL_VALIDATION_FAILED"
STATUS_R1_LEDGER_FAIL = "FAIL_V18_31F_R1_TRADE_PLAN_LEDGER_VALIDATION_FAILED"

FAIL_R30E = "FAIL_V18_31F_CORE_DAILY_SEQUENCE_FAILED"
FAIL_R31A = "FAIL_V18_31F_BUYABILITY_GATE_FAILED"
FAIL_R31B = "FAIL_V18_31F_POSITION_SIZING_FAILED"
FAIL_R31C = "FAIL_V18_31F_COST_CONSTRAINT_FAILED"
FAIL_R31D = "FAIL_V18_31F_ACCOUNT_AWARE_PLAN_FAILED"
FAIL_R31E = "FAIL_V18_31F_TRADE_PLAN_SNAPSHOT_FAILED"

MODE_LIVE = "FULL_DAILY_TRADE_READINESS_RUNNER"
MODE_DRY = "FULL_DAILY_TRADE_READINESS_DRY_RUN"
EXPECTED_ROWS = 252

R30E_WRAPPER = "scripts/v18/run_v18_30E_safe_daily_operator_sequence.ps1"
R31A_WRAPPER = "scripts/v18/run_v18_31A_static_buyability_gate.ps1"
R31B_WRAPPER = "scripts/v18/run_v18_31B_manual_position_sizing_policy_layer.ps1"
R31C_WRAPPER = "scripts/v18/run_v18_31C_moomoo_cost_slippage_constraint_layer.ps1"
R31D_WRAPPER = "scripts/v18/run_v18_31D_account_aware_manual_trade_plan.ps1"
R31E_WRAPPER = "scripts/v18/run_v18_31E_daily_trade_plan_snapshot_ledger.ps1"
R31G_WRAPPER = "scripts/v18/run_v18_31G_trading_day_signal_date_guard.ps1"

R30E_READ_FIRST = "outputs/v18/ops/V18_30E_READ_FIRST.txt"
R30A_READ_FIRST = "outputs/v18/ops/V18_30A_READ_FIRST.txt"
R31A_READ_FIRST = "outputs/v18/ops/V18_31A_READ_FIRST.txt"
R31B_READ_FIRST = "outputs/v18/ops/V18_31B_READ_FIRST.txt"
R31C_READ_FIRST = "outputs/v18/ops/V18_31C_READ_FIRST.txt"
R31C_R1_READ_FIRST = "outputs/v18/ops/V18_31C_R1_READ_FIRST.txt"
R31D_READ_FIRST = "outputs/v18/ops/V18_31D_READ_FIRST.txt"
R31E_READ_FIRST = "outputs/v18/ops/V18_31E_READ_FIRST.txt"
R31G_READ_FIRST = "outputs/v18/ops/V18_31G_READ_FIRST.txt"

ACCOUNT_AWARE = "outputs/v18/execution/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.csv"
COST_ADJUSTED = "outputs/v18/execution/V18_CURRENT_COST_ADJUSTED_TRADE_PLAN.csv"
POSITION_POLICY = "outputs/v18/execution/V18_CURRENT_POSITION_SIZING_POLICY.csv"
BUYABILITY = "outputs/v18/execution/V18_CURRENT_BUYABILITY_GATE.csv"
RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
RANKED = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
THEMES = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"

OUT_CURRENT_HOME = "outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md"
OUT_REPORT = "outputs/v18/read_center/V18_31F_FULL_DAILY_TRADE_READINESS_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_31F_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_31F_FULL_DAILY_TRADE_READINESS_SUMMARY.csv"
OUT_ERROR_REPORT = "outputs/v18/read_center/V18_31F_FULL_DAILY_TRADE_READINESS_ERROR.md"
OUT_R1_REPORT = "outputs/v18/read_center/V18_31F_R1_NON_TRADING_DAY_FALLBACK_REPORT.md"
OUT_R1_READ_FIRST = "outputs/v18/ops/V18_31F_R1_READ_FIRST.txt"
OUT_R1_SUMMARY = "outputs/v18/ops/V18_31F_R1_NON_TRADING_DAY_FALLBACK_SUMMARY.csv"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "DRY_RUN",
    "TOP_N_REQUESTED",
    "ACCOUNT_SIZE_USD",
    "CASH_USD",
    "CASH_RESERVE_PCT",
    "BROKER_PROFILE",
    "MIN_EFFECTIVE_TRADE_NOTIONAL_USD",
    "SAME_DAY_POLICY",
    "R31F_R1_PATCH_APPLIED",
    "R31F_NON_TRADING_MODE",
    "R30E_FAILURE_SOFTENED_BY_STRUCTURAL_VALIDATION",
    "R30E_FAILURE_CLASSIFICATION",
    "INDEPENDENT_STRUCTURAL_VALIDATION_RESULT",
    "REUSED_SIGNAL_DATE",
    "R31E_SIGNAL_DATE_OVERRIDE_USED",
    "STALE_OUTPUT_SUPPRESSED_ON_FAIL",
    "R31G_STATUS",
    "TRADING_DAY_GUARD_NEW_SIGNAL_DATE_ALLOWED",
    "TRADING_DAY_GUARD_RECOMMENDED_SIGNAL_DATE",
    "TRADING_DAY_GUARD_REUSED_LATEST_SIGNAL_DATE",
    "TRADING_DAY_GUARD_CANDIDATE_SIGNAL_DATE",
    "TRADING_DAY_GUARD_LATEST_PRICE_DATE",
    "TRADING_DAY_GUARD_ACTION",
    "NON_TRADING_DATE_GUARD_APPLIED",
    "R30E_STATUS",
    "R31A_STATUS",
    "R31B_STATUS",
    "R31C_STATUS",
    "R31C_R1_STATUS",
    "R31D_STATUS",
    "R31E_STATUS",
    "SIGNAL_DATE",
    "SNAPSHOT_DATE",
    "CURRENT_RANKED_CANDIDATE_ROWS",
    "CURRENT_RECOMMENDATION_ROWS",
    "CURRENT_THEME_CLASSIFICATION_ROWS",
    "LATEST_FULL_FREEZE_TICKER_COUNT",
    "R31A_OUTPUT_ROWS",
    "R31B_OUTPUT_ROWS",
    "R31C_OUTPUT_ROWS",
    "R31D_OUTPUT_ROWS",
    "R31E_APPENDED_ROWS",
    "R31E_POST_LEDGER_ROWS",
    "R31E_DUPLICATE_SIGNAL_DATE_TICKER_COUNT",
    "BUY_NOW_ALLOWED_COUNT",
    "BUY_SMALL_ONLY_COUNT",
    "WATCH_FOR_ENTRY_COUNT",
    "WAIT_FOR_PULLBACK_COUNT",
    "POSITION_ALLOWED_COUNT",
    "POSITION_SMALL_ONLY_COUNT",
    "COST_OK_COUNT",
    "CURRENT_COST_OK_CANDIDATE_COUNT",
    "CURRENT_BLOCKED_MIN_NOTIONAL_COUNT",
    "REVIEW_FIRST_NO_CURRENT_TRADE_COUNT",
    "WATCH_ONLY_NO_CURRENT_TRADE_COUNT",
    "WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT",
    "ACCOUNT_TRADE_ALLOWED_COUNT",
    "ACCOUNT_TRADE_SMALL_ONLY_COUNT",
    "ACCOUNT_WATCH_ONLY_COUNT",
    "ACCOUNT_WAIT_PULLBACK_COUNT",
    "ACCOUNT_REVIEW_FIRST_COUNT",
    "BLOCKED_BY_DAILY_NEW_BUY_LIMIT_COUNT",
    "BLOCKED_BY_COST_PLAN_COUNT",
    "ACCOUNT_STATE_MODE",
    "ACCOUNT_STATE_QUALITY_FLAG",
    "ACCOUNT_TOTAL_VALUE_USD",
    "CASH_USD_EFFECTIVE",
    "AVAILABLE_CASH_AFTER_RESERVE_USD",
    "FORWARD_RETURN_FILLABLE_READY",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "FINAL_OPERATOR_ACTION",
    "DAILY_READ_FILES",
    "NEXT_RECOMMENDED_STEP",
]

SUMMARY_FIELDS = [
    "run_id",
    "step_order",
    "step_name",
    "command",
    "started_at",
    "ended_at",
    "duration_seconds",
    "exit_code",
    "read_first_path",
    "parsed_status",
    "required_status",
    "result",
    "continue_allowed",
    "notes",
]

R1_READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R31F_R1_PATCH_APPLIED",
    "R31F_NON_TRADING_MODE",
    "R31G_STATUS",
    "CANDIDATE_SIGNAL_DATE",
    "LATEST_OBSERVED_PRICE_DATE",
    "RECOMMENDED_SIGNAL_DATE",
    "R30E_STATUS",
    "R30E_FAILURE_CLASSIFICATION",
    "R30E_FAILURE_SOFTENED_BY_STRUCTURAL_VALIDATION",
    "INDEPENDENT_STRUCTURAL_VALIDATION_RESULT",
    "R31A_STATUS",
    "R31B_STATUS",
    "R31C_STATUS",
    "R31D_STATUS",
    "R31E_STATUS",
    "R31E_SIGNAL_DATE_OVERRIDE_USED",
    "R31E_SIGNAL_DATE",
    "R31E_DUPLICATE_SIGNAL_DATE_TICKER_COUNT",
    "CURRENT_RANKED_CANDIDATE_ROWS",
    "CURRENT_RECOMMENDATION_ROWS",
    "CURRENT_THEME_CLASSIFICATION_ROWS",
    "LATEST_FULL_FREEZE_TICKER_COUNT",
    "R31A_OUTPUT_ROWS",
    "R31B_OUTPUT_ROWS",
    "R31C_OUTPUT_ROWS",
    "R31D_OUTPUT_ROWS",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]

R1_SUMMARY_FIELDS = [
    "run_id",
    "status",
    "generated_at",
    "r31f_non_trading_mode",
    "r31g_status",
    "candidate_signal_date",
    "latest_observed_price_date",
    "recommended_signal_date",
    "r30e_status",
    "r30e_failure_classification",
    "r30e_failure_softened_by_structural_validation",
    "independent_structural_validation_result",
    "r31e_signal_date_override_used",
    "r31e_signal_date",
    "r31e_duplicate_signal_date_ticker_count",
    "validation_fail_count",
    "forbidden_modified",
    "notes",
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


def is_ok(status: str) -> bool:
    return norm(status).startswith("OK_")


def is_warn(status: str) -> bool:
    return norm(status).startswith("WARN_")


def is_fail(status: str) -> bool:
    return norm(status).startswith("FAIL_")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
        except Exception:
            continue
    return []


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_status_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def cmd_text(cmd: Sequence[str]) -> str:
    return " ".join(f'"{part}"' if " " in str(part) else str(part) for part in cmd)


def command_for(root: Path, wrapper_rel: str, extra_args: Optional[Sequence[object]] = None) -> List[str]:
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root / wrapper_rel), "-Root", str(root)]
    if extra_args:
        cmd.extend(str(item) for item in extra_args)
    return cmd


def markdown_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: int = 25) -> str:
    selected = list(rows[:limit])
    if not selected:
        return "_None._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in selected:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def row_count(path: Path) -> int:
    return len(read_csv(path))


def output_rows_from(read_first: Dict[str, str], fields: Sequence[str]) -> int:
    for field in fields:
        value = read_first.get(field)
        if norm(value):
            return to_int(value)
    return "UNKNOWN_FAILURE"


def latest_freeze_count_for_date(root: Path, signal_date: str) -> int:
    if not signal_date:
        return 0
    rows = read_csv(root / "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv")
    return len({upper(row.get("ticker")) for row in rows if norm(row.get("signal_date")) == signal_date and upper(row.get("ticker"))})


def independent_structural_validation(root: Path, recommended_signal_date: str) -> Dict[str, object]:
    ranked_rows = row_count(root / RANKED)
    rec_rows = row_count(root / RECOMMENDATIONS)
    theme_rows = row_count(root / THEMES)
    freeze_rows = latest_freeze_count_for_date(root, recommended_signal_date)
    safety_ok = True
    result = "PASS_CURRENT_ONLY"
    failures: List[str] = []
    if ranked_rows != EXPECTED_ROWS:
        failures.append(f"ranked_rows={ranked_rows}")
    if rec_rows != EXPECTED_ROWS:
        failures.append(f"recommendation_rows={rec_rows}")
    if theme_rows != EXPECTED_ROWS:
        failures.append(f"theme_rows={theme_rows}")
    if not safety_ok:
        failures.append("safety_flags_not_clean")
    if failures:
        result = "FAIL_" + ";".join(failures)
    elif freeze_rows != EXPECTED_ROWS:
        result = f"PASS_CURRENT_ONLY_FREEZE_PARTIAL_{freeze_rows}"
    return {
        "result": result,
        "ranked_rows": ranked_rows,
        "recommendation_rows": rec_rows,
        "theme_rows": theme_rows,
        "latest_full_freeze_ticker_count": freeze_rows,
        "passes": not failures,
    }


def classify_r30e_failure(r30e: Dict[str, str], proc: Optional[subprocess.CompletedProcess[str]], non_trading_mode: bool) -> str:
    status = r30e.get("STATUS", "")
    if not is_fail(status):
        return "NOT_FAILURE"
    if non_trading_mode and r30e.get("SKIP_R21") == "TRUE" and r30e.get("SKIP_R29C") == "TRUE":
        failed_step = r30e.get("FAILED_STEP", "")
        failed_reason = r30e.get("FAILED_REASON", "")
        if "R30B" in failed_step or "PRECHECK" in failed_reason:
            return "NON_TRADING_SKIP_MODE_PRECHECK_FAIL"
        return "NON_TRADING_SKIP_MODE_FAIL"
    if any(to_int(r30e.get(field), -1) not in (EXPECTED_ROWS, 0) for field in ["CURRENT_RANKED_CANDIDATE_ROWS", "CURRENT_RECOMMENDATION_ROWS", "CURRENT_THEME_CLASSIFICATION_ROWS"]):
        return "STRUCTURAL_FAILURE"
    if proc is not None and proc.returncode != 0:
        return "CHILD_PROCESS_FAILURE"
    return "UNKNOWN_FAILURE"


def softenable_current_only_layer(read_first: Dict[str, str], row_fields: Sequence[str]) -> bool:
    rows_ok = any(to_int(read_first.get(field), -1) == EXPECTED_ROWS for field in row_fields)
    safety_ok = (
        read_first.get("AUTO_TRADE", "DISABLED") == "DISABLED"
        and read_first.get("AUTO_SELL", "DISABLED") == "DISABLED"
        and read_first.get("OFFICIAL_DECISION_IMPACT", "NONE") == "NONE"
        and read_first.get("FORBIDDEN_MODIFIED", "FALSE") == "FALSE"
    )
    current_ok = (
        to_int(read_first.get("CURRENT_RANKED_CANDIDATE_ROWS"), EXPECTED_ROWS) == EXPECTED_ROWS
        and to_int(read_first.get("CURRENT_RECOMMENDATION_ROWS"), EXPECTED_ROWS) == EXPECTED_ROWS
        and to_int(read_first.get("CURRENT_THEME_CLASSIFICATION_ROWS"), EXPECTED_ROWS) == EXPECTED_ROWS
    )
    return rows_ok and safety_ok and current_ok


def build_step(
    run_id: str,
    order: int,
    name: str,
    command: str,
    read_first_path: str,
    parsed_status: str,
    required_status: str,
    result: str,
    continue_allowed: bool,
    notes: str = "",
    started: str = "",
    ended: str = "",
    duration: str = "",
    exit_code: object = "",
) -> Dict[str, object]:
    return {
        "run_id": run_id,
        "step_order": order,
        "step_name": name,
        "command": command,
        "started_at": started,
        "ended_at": ended,
        "duration_seconds": duration,
        "exit_code": exit_code,
        "read_first_path": read_first_path,
        "parsed_status": parsed_status,
        "required_status": required_status,
        "result": result,
        "continue_allowed": bool_text(continue_allowed),
        "notes": notes,
    }


def run_step(
    root: Path,
    run_id: str,
    rows: List[Dict[str, object]],
    order: int,
    name: str,
    wrapper_rel: str,
    read_first_rel: str,
    fail_status: str,
    args: argparse.Namespace,
    extra_args: Optional[Sequence[object]] = None,
) -> Tuple[bool, Dict[str, str], Dict[str, object], subprocess.CompletedProcess[str]]:
    cmd = command_for(root, wrapper_rel, extra_args)
    started_dt = dt.datetime.now()
    proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
    ended_dt = dt.datetime.now()
    rf_path = root / read_first_rel
    rf = read_status_file(rf_path)
    status = rf.get("STATUS", "")
    allowed = proc.returncode == 0 and (is_ok(status) or (is_warn(status) and not args.stop_on_warn))
    if proc.returncode != 0:
        notes = (proc.stderr or proc.stdout or "").strip()[:800]
    elif is_warn(status) and allowed:
        notes = "WARN accepted for structural orchestration; final status will remain WARN unless all warnings clear."
    elif args.stop_on_warn and is_warn(status):
        notes = "Stopped because --stop-on-warn was set."
    elif is_fail(status):
        notes = f"Child READ_FIRST status is failure; mapped to {fail_status}."
    else:
        notes = ""
    row = build_step(
        run_id,
        order,
        name,
        cmd_text(cmd),
        str(rf_path),
        status,
        "OK_OR_EXPECTED_WARN",
        "PASS" if is_ok(status) and proc.returncode == 0 else ("WARN_ACCEPTED" if allowed else "FAIL"),
        allowed,
        notes,
        started_dt.isoformat(timespec="seconds"),
        ended_dt.isoformat(timespec="seconds"),
        f"{(ended_dt - started_dt).total_seconds():.3f}",
        proc.returncode,
    )
    rows.append(row)
    return allowed, rf, row, proc


def add_planned_step(root: Path, run_id: str, rows: List[Dict[str, object]], order: int, name: str, wrapper_rel: str, read_first_rel: str, extra_args: Optional[Sequence[object]] = None) -> None:
    rows.append(build_step(
        run_id,
        order,
        name,
        cmd_text(command_for(root, wrapper_rel, extra_args)),
        str(root / read_first_rel),
        "DRY_RUN_NOT_EXECUTED",
        "OK_OR_EXPECTED_WARN",
        "PLANNED",
        True,
        "Dry run only; child wrapper not executed.",
    ))


def validate_wrappers(root: Path, args: argparse.Namespace) -> List[str]:
    wrappers = [R31G_WRAPPER, R31A_WRAPPER, R31B_WRAPPER, R31C_WRAPPER, R31D_WRAPPER]
    if not args.skip_r30e:
        wrappers.insert(0, R30E_WRAPPER)
    if not args.skip_r31e:
        wrappers.append(R31E_WRAPPER)
    return [rel for rel in wrappers if not (root / rel).exists()]


def gather_values(root: Path, values: Dict[str, object]) -> Tuple[List[str], Dict[str, str]]:
    r31g = read_status_file(root / R31G_READ_FIRST)
    r30e = read_status_file(root / R30E_READ_FIRST)
    r30a = read_status_file(root / R30A_READ_FIRST)
    r31a = read_status_file(root / R31A_READ_FIRST)
    r31b = read_status_file(root / R31B_READ_FIRST)
    r31c = read_status_file(root / R31C_READ_FIRST)
    r31c_r1 = read_status_file(root / R31C_R1_READ_FIRST)
    r31d = read_status_file(root / R31D_READ_FIRST)
    r31e = read_status_file(root / R31E_READ_FIRST)

    values.update({
        "R31G_STATUS": r31g.get("STATUS", values.get("R31G_STATUS", "")),
        "TRADING_DAY_GUARD_NEW_SIGNAL_DATE_ALLOWED": r31g.get("NEW_SIGNAL_DATE_ALLOWED", values.get("TRADING_DAY_GUARD_NEW_SIGNAL_DATE_ALLOWED", "")),
        "TRADING_DAY_GUARD_RECOMMENDED_SIGNAL_DATE": r31g.get("RECOMMENDED_SIGNAL_DATE", values.get("TRADING_DAY_GUARD_RECOMMENDED_SIGNAL_DATE", "")),
        "TRADING_DAY_GUARD_CANDIDATE_SIGNAL_DATE": r31g.get("CANDIDATE_SIGNAL_DATE", values.get("TRADING_DAY_GUARD_CANDIDATE_SIGNAL_DATE", "")),
        "TRADING_DAY_GUARD_LATEST_PRICE_DATE": r31g.get("LATEST_OBSERVED_PRICE_DATE", values.get("TRADING_DAY_GUARD_LATEST_PRICE_DATE", "")),
        "R30E_STATUS": r30e.get("STATUS", values.get("R30E_STATUS", "")),
        "R31A_STATUS": r31a.get("STATUS", values.get("R31A_STATUS", "")),
        "R31B_STATUS": r31b.get("STATUS", values.get("R31B_STATUS", "")),
        "R31C_STATUS": r31c.get("STATUS", values.get("R31C_STATUS", "")),
        "R31C_R1_STATUS": r31e.get("R31C_R1_STATUS", r31c_r1.get("STATUS", values.get("R31C_R1_STATUS", ""))),
        "R31D_STATUS": r31d.get("STATUS", values.get("R31D_STATUS", "")),
        "R31E_STATUS": r31e.get("STATUS", values.get("R31E_STATUS", "")),
        "SIGNAL_DATE": r31e.get("SIGNAL_DATE", r30e.get("R21_SIGNAL_DATE", r30a.get("LATEST_FULL_FREEZE_SIGNAL_DATE", values.get("SIGNAL_DATE", "")))),
        "SNAPSHOT_DATE": r31e.get("SNAPSHOT_DATE", values.get("SNAPSHOT_DATE", "")),
        "CURRENT_RANKED_CANDIDATE_ROWS": r31e.get("CURRENT_RANKED_CANDIDATE_ROWS", r31d.get("CURRENT_RANKED_CANDIDATE_ROWS", r31c.get("CURRENT_RANKED_CANDIDATE_ROWS", row_count(root / RANKED)))),
        "CURRENT_RECOMMENDATION_ROWS": r31e.get("CURRENT_RECOMMENDATION_ROWS", r31d.get("CURRENT_RECOMMENDATION_ROWS", r31c.get("CURRENT_RECOMMENDATION_ROWS", row_count(root / RECOMMENDATIONS)))),
        "CURRENT_THEME_CLASSIFICATION_ROWS": r31e.get("CURRENT_THEME_CLASSIFICATION_ROWS", r31d.get("CURRENT_THEME_CLASSIFICATION_ROWS", r31c.get("CURRENT_THEME_CLASSIFICATION_ROWS", row_count(root / THEMES)))),
        "LATEST_FULL_FREEZE_TICKER_COUNT": r31e.get("LATEST_FULL_FREEZE_TICKER_COUNT", r31d.get("LATEST_FULL_FREEZE_TICKER_COUNT", r30e.get("LATEST_FULL_FREEZE_TICKER_COUNT", r30a.get("LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT", "")))),
        "R31A_OUTPUT_ROWS": output_rows_from(r31a, ["OUTPUT_BUYABILITY_ROWS", "OUTPUT_ROWS"]),
        "R31B_OUTPUT_ROWS": output_rows_from(r31b, ["OUTPUT_POSITION_POLICY_ROWS", "OUTPUT_ROWS"]),
        "R31C_OUTPUT_ROWS": output_rows_from(r31c, ["OUTPUT_COST_ADJUSTED_ROWS", "OUTPUT_ROWS"]),
        "R31D_OUTPUT_ROWS": output_rows_from(r31d, ["OUTPUT_ACCOUNT_AWARE_ROWS", "OUTPUT_ROWS"]),
        "R31E_APPENDED_ROWS": r31e.get("APPENDED_ROWS", values.get("R31E_APPENDED_ROWS", "")),
        "R31E_POST_LEDGER_ROWS": r31e.get("POST_LEDGER_ROWS", values.get("R31E_POST_LEDGER_ROWS", "")),
        "R31E_DUPLICATE_SIGNAL_DATE_TICKER_COUNT": r31e.get("DUPLICATE_SIGNAL_DATE_TICKER_COUNT", values.get("R31E_DUPLICATE_SIGNAL_DATE_TICKER_COUNT", "")),
        "R31E_SIGNAL_DATE_OVERRIDE_USED": r31e.get("SIGNAL_DATE_OVERRIDE_USED", values.get("R31E_SIGNAL_DATE_OVERRIDE_USED", "")),
        "BUY_NOW_ALLOWED_COUNT": r31a.get("BUY_NOW_ALLOWED_COUNT", ""),
        "BUY_SMALL_ONLY_COUNT": r31a.get("BUY_SMALL_ONLY_COUNT", ""),
        "WATCH_FOR_ENTRY_COUNT": r31a.get("WATCH_FOR_ENTRY_COUNT", ""),
        "WAIT_FOR_PULLBACK_COUNT": r31a.get("WAIT_FOR_PULLBACK_COUNT", ""),
        "POSITION_ALLOWED_COUNT": r31b.get("POSITION_ALLOWED_COUNT", ""),
        "POSITION_SMALL_ONLY_COUNT": r31b.get("POSITION_SMALL_ONLY_COUNT", ""),
        "COST_OK_COUNT": r31e.get("COST_OK_COUNT", r31c.get("COST_OK_COUNT", "")),
        "CURRENT_COST_OK_CANDIDATE_COUNT": r31e.get("CURRENT_COST_OK_CANDIDATE_COUNT", r31c_r1.get("CURRENT_COST_OK_CANDIDATE_COUNT", "")),
        "CURRENT_BLOCKED_MIN_NOTIONAL_COUNT": r31e.get("CURRENT_BLOCKED_MIN_NOTIONAL_COUNT", r31c_r1.get("CURRENT_BLOCKED_MIN_NOTIONAL_COUNT", "")),
        "REVIEW_FIRST_NO_CURRENT_TRADE_COUNT": r31e.get("REVIEW_FIRST_NO_CURRENT_TRADE_COUNT", r31c_r1.get("REVIEW_FIRST_NO_CURRENT_TRADE_COUNT", "")),
        "WATCH_ONLY_NO_CURRENT_TRADE_COUNT": r31e.get("WATCH_ONLY_NO_CURRENT_TRADE_COUNT", r31c_r1.get("WATCH_ONLY_NO_CURRENT_TRADE_COUNT", "")),
        "WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT": r31e.get("WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT", r31c_r1.get("WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT", "")),
        "ACCOUNT_TRADE_ALLOWED_COUNT": r31e.get("ACCOUNT_TRADE_ALLOWED_COUNT", r31d.get("ACCOUNT_TRADE_ALLOWED_COUNT", "")),
        "ACCOUNT_TRADE_SMALL_ONLY_COUNT": r31e.get("ACCOUNT_TRADE_SMALL_ONLY_COUNT", r31d.get("ACCOUNT_TRADE_SMALL_ONLY_COUNT", "")),
        "ACCOUNT_WATCH_ONLY_COUNT": r31e.get("ACCOUNT_WATCH_ONLY_COUNT", r31d.get("ACCOUNT_WATCH_ONLY_COUNT", "")),
        "ACCOUNT_WAIT_PULLBACK_COUNT": r31e.get("ACCOUNT_WAIT_PULLBACK_COUNT", r31d.get("ACCOUNT_WAIT_PULLBACK_COUNT", "")),
        "ACCOUNT_REVIEW_FIRST_COUNT": r31e.get("ACCOUNT_REVIEW_FIRST_COUNT", r31d.get("ACCOUNT_REVIEW_FIRST_COUNT", "")),
        "BLOCKED_BY_DAILY_NEW_BUY_LIMIT_COUNT": r31e.get("BLOCKED_BY_DAILY_NEW_BUY_LIMIT_COUNT", r31d.get("BLOCKED_BY_DAILY_NEW_BUY_LIMIT_COUNT", "")),
        "BLOCKED_BY_COST_PLAN_COUNT": r31e.get("BLOCKED_BY_COST_PLAN_COUNT", r31d.get("BLOCKED_BY_COST_PLAN_COUNT", "")),
        "ACCOUNT_STATE_MODE": r31e.get("ACCOUNT_STATE_MODE", r31d.get("ACCOUNT_STATE_MODE", "")),
        "ACCOUNT_STATE_QUALITY_FLAG": r31e.get("ACCOUNT_STATE_QUALITY_FLAG", r31d.get("ACCOUNT_STATE_QUALITY_FLAG", "")),
        "ACCOUNT_TOTAL_VALUE_USD": r31d.get("ACCOUNT_TOTAL_VALUE_USD", ""),
        "CASH_USD_EFFECTIVE": r31d.get("CASH_USD", ""),
        "AVAILABLE_CASH_AFTER_RESERVE_USD": r31d.get("AVAILABLE_CASH_AFTER_RESERVE_USD", ""),
        "FORWARD_RETURN_FILLABLE_READY": r31e.get("FORWARD_RETURN_FILLABLE_READY", r31d.get("FORWARD_RETURN_FILLABLE_READY", r31c.get("FORWARD_RETURN_FILLABLE_READY", "FALSE"))),
        "AUTO_TRADE": r31e.get("AUTO_TRADE", r31d.get("AUTO_TRADE", r31c.get("AUTO_TRADE", "DISABLED"))),
        "AUTO_SELL": r31e.get("AUTO_SELL", r31d.get("AUTO_SELL", r31c.get("AUTO_SELL", "DISABLED"))),
        "OFFICIAL_DECISION_IMPACT": r31e.get("OFFICIAL_DECISION_IMPACT", r31d.get("OFFICIAL_DECISION_IMPACT", r31c.get("OFFICIAL_DECISION_IMPACT", "NONE"))),
        "FINAL_OPERATOR_ACTION": r30e.get("FINAL_OPERATOR_ACTION", r30a.get("CURRENT_OPERATOR_ACTION", "")),
    })
    values["FORBIDDEN_MODIFIED"] = "TRUE" if any(
        rf.get("FORBIDDEN_MODIFIED") == "TRUE" for rf in [r31g, r30e, r30a, r31a, r31b, r31c, r31c_r1, r31d, r31e]
    ) else "FALSE"

    warnings: List[str] = []
    warning_statuses = [
        ("R31G", r31g),
        ("R30E", r30e),
        ("R31A", r31a),
        ("R31B", r31b),
        ("R31C", r31c),
        ("R31D", r31d),
        ("R31E", r31e),
    ]
    for label, rf in warning_statuses:
        status = rf.get("STATUS", "")
        if is_warn(status):
            warnings.append(f"{label}:{status}")
    r31c_r1_status = norm(values.get("R31C_R1_STATUS"))
    if is_warn(r31c_r1_status):
        warnings.append(f"R31C_R1:{r31c_r1_status}")
    if values.get("FORWARD_RETURN_FILLABLE_READY") == "FALSE":
        warnings.append("FORWARD_RETURN_NOT_READY")
    if norm(values.get("ACCOUNT_STATE_QUALITY_FLAG")).startswith("WARN_"):
        warnings.append(norm(values.get("ACCOUNT_STATE_QUALITY_FLAG")))
    return warnings, r31d


def validation_failures(values: Dict[str, object], args: argparse.Namespace) -> List[str]:
    failures: List[str] = []
    expected_keys = {
        "CURRENT_RANKED_CANDIDATE_ROWS": EXPECTED_ROWS,
        "CURRENT_RECOMMENDATION_ROWS": EXPECTED_ROWS,
        "CURRENT_THEME_CLASSIFICATION_ROWS": EXPECTED_ROWS,
        "R31A_OUTPUT_ROWS": EXPECTED_ROWS,
        "R31B_OUTPUT_ROWS": EXPECTED_ROWS,
        "R31C_OUTPUT_ROWS": EXPECTED_ROWS,
        "R31D_OUTPUT_ROWS": EXPECTED_ROWS,
    }
    if not args.skip_r31e and values.get("R31E_STATUS") != "SKIPPED_BY_TRADING_DAY_GUARD":
        expected_keys["R31E_APPENDED_ROWS"] = EXPECTED_ROWS
        if to_int(values.get("R31E_DUPLICATE_SIGNAL_DATE_TICKER_COUNT"), -1) != 0:
            failures.append("R31E duplicate signal_date+ticker count is not zero")
        if values.get("R31F_NON_TRADING_MODE") == "TRUE":
            if norm(values.get("SIGNAL_DATE")) != norm(values.get("REUSED_SIGNAL_DATE")):
                failures.append("R31E signal_date does not match reused signal date")
            if values.get("R31E_SIGNAL_DATE_OVERRIDE_USED") != "TRUE":
                failures.append("R31E signal-date override not used in non-trading mode")
    latest_freeze = to_int(values.get("LATEST_FULL_FREEZE_TICKER_COUNT"), 0)
    if latest_freeze not in (0, EXPECTED_ROWS) and values.get("R31F_NON_TRADING_MODE") != "TRUE":
        failures.append("Latest full freeze ticker count is not 252")
    for key, expected in expected_keys.items():
        if to_int(values.get(key), -1) != expected:
            failures.append(f"{key} != {expected}")
    if values.get("AUTO_TRADE") != "DISABLED":
        failures.append("AUTO_TRADE not disabled")
    if values.get("AUTO_SELL") != "DISABLED":
        failures.append("AUTO_SELL not disabled")
    if values.get("OFFICIAL_DECISION_IMPACT") != "NONE":
        failures.append("OFFICIAL_DECISION_IMPACT not NONE")
    if values.get("FORBIDDEN_MODIFIED") != "FALSE":
        failures.append("FORBIDDEN_MODIFIED not FALSE")
    return failures


def read_first_text(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def daily_files(root: Path) -> str:
    files = [
        root / OUT_READ_FIRST,
        root / OUT_CURRENT_HOME,
        root / "outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md",
        root / "outputs/v18/read_center/V18_CURRENT_OPERATOR_CONTROL_CENTER.md",
    ]
    return "; ".join(str(path) for path in files)


def operator_conclusion(values: Dict[str, object], warnings: Sequence[str]) -> str:
    if norm(values.get("STATUS")).startswith("FAIL_"):
        return "Daily trade-readiness run failed; do not use the incomplete trade-readiness output."
    parts = ["Manual review ready", "no auto-trading"]
    if norm(values.get("ACCOUNT_STATE_QUALITY_FLAG")).startswith("WARN_"):
        parts.append("account file is template/manual-warning")
    if values.get("FORWARD_RETURN_FILLABLE_READY") == "FALSE":
        parts.append("forward-return validation not ready")
    if not warnings and values.get("STATUS") == STATUS_OK:
        parts.append("structural checks passed")
    return "; ".join(parts) + "."


def cost_ok_not_account_allowed(rows: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    selected = []
    for row in rows:
        if upper(row.get("cost_adjusted_trade_status")) in {"COST_OK", "COST_OK_SMALL_ONLY"} and upper(row.get("account_trade_status")) not in {"ACCOUNT_TRADE_ALLOWED", "ACCOUNT_TRADE_SMALL_ONLY"}:
            selected.append(row)
    return selected


def build_homepage(values: Dict[str, object], warnings: Sequence[str]) -> str:
    if norm(values.get("STATUS")).startswith("FAIL_"):
        return "\n".join([
            "# V18 Current Daily Trade Readiness",
            "",
            "## 1. Final Status",
            f"STATUS: {values.get('STATUS', '')}",
            "",
            "## 2. Operator Conclusion",
            "Daily trade-readiness run failed; current trade candidates below are not refreshed and must not be used.",
            "",
            "## 3. Trading-Day / Signal-Date Guard",
            f"- Candidate signal date: `{values.get('TRADING_DAY_GUARD_CANDIDATE_SIGNAL_DATE', '')}`",
            f"- Latest observed price date: `{values.get('TRADING_DAY_GUARD_LATEST_PRICE_DATE', '')}`",
            f"- New signal date allowed: `{values.get('TRADING_DAY_GUARD_NEW_SIGNAL_DATE_ALLOWED', '')}`",
            f"- Recommended signal date: `{values.get('TRADING_DAY_GUARD_RECOMMENDED_SIGNAL_DATE', '')}`",
            f"- Guard action: `{values.get('TRADING_DAY_GUARD_ACTION', '')}`",
            "",
            "## 4. Failure Context",
            f"- R30E status: `{values.get('R30E_STATUS', '')}`",
            f"- R30E failure classification: `{values.get('R30E_FAILURE_CLASSIFICATION', '')}`",
            f"- Independent structural validation: `{values.get('INDEPENDENT_STRUCTURAL_VALIDATION_RESULT', '')}`",
            "- Normal candidate tables are intentionally suppressed on FAIL to avoid stale-output misuse.",
            "",
            "## 5. Safety",
            "- AUTO_TRADE: `DISABLED`",
            "- AUTO_SELL: `DISABLED`",
            "- Broker connection: `NOT_EXECUTED`",
            "- Order placement: `NOT_EXECUTED`",
            "- This is manual research guidance only.",
            "",
            "## 6. Next Step",
            values.get("NEXT_RECOMMENDED_STEP", "Inspect R31F READ_FIRST and error report."),
        ]) + "\n"
    account_rows = read_csv(Path(values["_ROOT"]) / ACCOUNT_AWARE)
    cost_rows = read_csv(Path(values["_ROOT"]) / COST_ADJUSTED)
    allowed = [row for row in account_rows if upper(row.get("account_trade_status")) in {"ACCOUNT_TRADE_ALLOWED", "ACCOUNT_TRADE_SMALL_ONLY"}]
    cost_not_account = cost_ok_not_account_allowed(account_rows)
    min_notional = [row for row in cost_rows if upper(row.get("cost_adjusted_trade_status")) == "BLOCKED_BY_MIN_NOTIONAL"]
    review_first = [row for row in cost_rows if upper(row.get("cost_review_substatus")) == "REVIEW_FIRST_NO_CURRENT_TRADE"]
    watch_wait_counts = Counter(upper(row.get("cost_review_substatus")) for row in cost_rows)
    warning_lines = warnings or ["NONE"]
    return "\n".join([
        "# V18 Current Daily Trade Readiness",
        "",
        "## 1. Final Status",
        f"STATUS: {values.get('STATUS', '')}",
        "",
        "## 2. Operator Conclusion",
        operator_conclusion(values, warnings),
        ("Current reports refreshed using latest supported signal date "
         f"`{values.get('REUSED_SIGNAL_DATE', '')}`; no new signal_date was created."
         if values.get("R31F_NON_TRADING_MODE") == "TRUE" else ""),
        "",
        "## 3. System Integrity Snapshot",
        f"- Ranked rows: `{values.get('CURRENT_RANKED_CANDIDATE_ROWS', '')}`",
        f"- Recommendation rows: `{values.get('CURRENT_RECOMMENDATION_ROWS', '')}`",
        f"- Theme rows: `{values.get('CURRENT_THEME_CLASSIFICATION_ROWS', '')}`",
        f"- Latest full signal freeze rows: `{values.get('LATEST_FULL_FREEZE_TICKER_COUNT', '')}`",
        f"- Trade plan ledger rows: `{values.get('R31E_POST_LEDGER_ROWS', '')}`",
        f"- Ledger duplicate signal_date+ticker count: `{values.get('R31E_DUPLICATE_SIGNAL_DATE_TICKER_COUNT', '')}`",
        "",
        "## Trading-Day / Signal-Date Guard",
        f"- Candidate signal date: `{values.get('TRADING_DAY_GUARD_CANDIDATE_SIGNAL_DATE', '')}`",
        f"- Latest observed price date: `{values.get('TRADING_DAY_GUARD_LATEST_PRICE_DATE', '')}`",
        f"- New signal date allowed: `{values.get('TRADING_DAY_GUARD_NEW_SIGNAL_DATE_ALLOWED', '')}`",
        f"- Reused latest signal date: `{values.get('TRADING_DAY_GUARD_REUSED_LATEST_SIGNAL_DATE', '')}`",
        f"- Recommended signal date: `{values.get('TRADING_DAY_GUARD_RECOMMENDED_SIGNAL_DATE', '')}`",
        f"- Guard action: `{values.get('TRADING_DAY_GUARD_ACTION', '')}`",
        f"- Prevented new R31E date: `{values.get('NON_TRADING_DATE_GUARD_APPLIED', '')}`",
        "- Weekend or no-new-price-data runs must not create a new validation signal date unless explicitly overridden.",
        "",
        "## 4. Today's Final Account-Aware Candidates",
        markdown_table(allowed, ["ticker", "rank", "recommendation_tier", "account_trade_status", "suggested_account_initial_notional_usd", "account_plan_reason"]),
        "## 5. Cost-OK But Not Account-Allowed",
        markdown_table(cost_not_account, ["ticker", "rank", "cost_adjusted_trade_status", "account_trade_status", "suggested_initial_notional_usd", "account_block_reason"]),
        "## 6. Blocked By Min Notional",
        markdown_table(min_notional, ["ticker", "rank", "recommendation_tier", "primary_theme", "suggested_initial_notional_usd", "cost_block_reason"]),
        "## 7. Review-First / No Current Trade",
        markdown_table(review_first, ["ticker", "rank", "recommendation_tier", "primary_theme", "suggested_initial_notional_usd", "cost_block_reason"]),
        "## 8. Watch-Only / Wait-Pullback Summary",
        f"- Watch-only / no current trade: `{watch_wait_counts.get('WATCH_ONLY_NO_CURRENT_TRADE', 0)}`",
        f"- Wait-pullback / no current trade: `{watch_wait_counts.get('WAIT_PULLBACK_NO_CURRENT_TRADE', 0)}`",
        f"- Account watch-only: `{values.get('ACCOUNT_WATCH_ONLY_COUNT', '')}`",
        f"- Account wait-pullback: `{values.get('ACCOUNT_WAIT_PULLBACK_COUNT', '')}`",
        "",
        "## 9. Account State Warning",
        f"- Account state mode: `{values.get('ACCOUNT_STATE_MODE', '')}`",
        f"- Account state quality: `{values.get('ACCOUNT_STATE_QUALITY_FLAG', '')}`",
        "- Manual account state is operator-maintained and must be updated before relying on account-aware constraints.",
        "",
        "## 10. Safety",
        "- AUTO_TRADE: `DISABLED`",
        "- AUTO_SELL: `DISABLED`",
        "- Broker connection: `NOT_EXECUTED`",
        "- Order placement: `NOT_EXECUTED`",
        "- This is manual research guidance only.",
        "",
        "## 11. Daily Files To Read",
        "- `outputs/v18/ops/V18_31F_READ_FIRST.txt`",
        "- `outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md`",
        "- `outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md`",
        "- `outputs/v18/read_center/V18_CURRENT_OPERATOR_CONTROL_CENTER.md`",
        "",
        "## 12. Next Step",
        "- Update `state/v18/manual_account/V18_MANUAL_ACCOUNT_STATE.csv` if real positions or cash changed.",
        "- Run forward validation only after future prices exist.",
        "",
        "## Warnings",
        "\n".join(f"- `{item}`" for item in warning_lines),
    ]) + "\n"


def build_report(values: Dict[str, object], steps: Sequence[Dict[str, object]], warnings: Sequence[str], failures: Sequence[str]) -> str:
    return "\n".join([
        "# V18.31F Full Daily Trade-Readiness Runner",
        "",
        f"STATUS: {values.get('STATUS', '')}",
        f"RUN_ID: {values.get('RUN_ID', '')}",
        "",
        "## Step Results",
        markdown_table(steps, ["step_order", "step_name", "parsed_status", "exit_code", "result", "continue_allowed", "notes"], limit=20),
        "## Child Statuses",
        f"- R31G: `{values.get('R31G_STATUS', '')}`",
        f"- R30E: `{values.get('R30E_STATUS', '')}`",
        f"- R31A: `{values.get('R31A_STATUS', '')}`",
        f"- R31B: `{values.get('R31B_STATUS', '')}`",
        f"- R31C: `{values.get('R31C_STATUS', '')}`",
        f"- R31C-R1: `{values.get('R31C_R1_STATUS', '')}`",
        f"- R31D: `{values.get('R31D_STATUS', '')}`",
        f"- R31E: `{values.get('R31E_STATUS', '')}`",
        "",
        "## Key Counts",
        f"- Ranked rows: `{values.get('CURRENT_RANKED_CANDIDATE_ROWS', '')}`",
        f"- Recommendation rows: `{values.get('CURRENT_RECOMMENDATION_ROWS', '')}`",
        f"- Theme rows: `{values.get('CURRENT_THEME_CLASSIFICATION_ROWS', '')}`",
        f"- R31A rows: `{values.get('R31A_OUTPUT_ROWS', '')}`",
        f"- R31B rows: `{values.get('R31B_OUTPUT_ROWS', '')}`",
        f"- R31C rows: `{values.get('R31C_OUTPUT_ROWS', '')}`",
        f"- R31D rows: `{values.get('R31D_OUTPUT_ROWS', '')}`",
        f"- R31E appended rows: `{values.get('R31E_APPENDED_ROWS', '')}`",
        f"- R31E post-ledger rows: `{values.get('R31E_POST_LEDGER_ROWS', '')}`",
        f"- R31E duplicate keys: `{values.get('R31E_DUPLICATE_SIGNAL_DATE_TICKER_COUNT', '')}`",
        "",
        "## Trade Readiness Counts",
        f"- Account trade allowed: `{values.get('ACCOUNT_TRADE_ALLOWED_COUNT', '')}`",
        f"- Account trade small-only: `{values.get('ACCOUNT_TRADE_SMALL_ONLY_COUNT', '')}`",
        f"- Cost OK: `{values.get('COST_OK_COUNT', '')}`",
        f"- Blocked by min notional: `{values.get('CURRENT_BLOCKED_MIN_NOTIONAL_COUNT', '')}`",
        f"- Review-first/no-current-trade: `{values.get('REVIEW_FIRST_NO_CURRENT_TRADE_COUNT', '')}`",
        f"- Watch-only/no-current-trade: `{values.get('WATCH_ONLY_NO_CURRENT_TRADE_COUNT', '')}`",
        f"- Wait-pullback/no-current-trade: `{values.get('WAIT_PULLBACK_NO_CURRENT_TRADE_COUNT', '')}`",
        "",
        "## Ledger Action",
        f"- Signal date: `{values.get('SIGNAL_DATE', '')}`",
        f"- Snapshot date: `{values.get('SNAPSHOT_DATE', '')}`",
        f"- Same-day policy: `{values.get('SAME_DAY_POLICY', '')}`",
        f"- Trading-day guard action: `{values.get('TRADING_DAY_GUARD_ACTION', '')}`",
        f"- Guard recommended signal date: `{values.get('TRADING_DAY_GUARD_RECOMMENDED_SIGNAL_DATE', '')}`",
        "",
        "## Warnings",
        "\n".join(f"- `{item}`" for item in (warnings or ["NONE"])),
        "",
        "## Validation Failures",
        "\n".join(f"- `{item}`" for item in (failures or ["NONE"])),
        "",
        "## Safety",
        "- AUTO_TRADE: `DISABLED`",
        "- AUTO_SELL: `DISABLED`",
        "- OFFICIAL_DECISION_IMPACT: `NONE`",
        "- Broker/API calls: `NOT_EXECUTED`",
        "- Order placement: `NOT_EXECUTED`",
    ]) + "\n"


def r1_read_first_text(values: Dict[str, object]) -> str:
    mapped = {
        "STATUS": values.get("STATUS", ""),
        "MODE": values.get("MODE", ""),
        "RUN_ID": values.get("RUN_ID", ""),
        "R31F_R1_PATCH_APPLIED": values.get("R31F_R1_PATCH_APPLIED", ""),
        "R31F_NON_TRADING_MODE": values.get("R31F_NON_TRADING_MODE", ""),
        "R31G_STATUS": values.get("R31G_STATUS", ""),
        "CANDIDATE_SIGNAL_DATE": values.get("TRADING_DAY_GUARD_CANDIDATE_SIGNAL_DATE", ""),
        "LATEST_OBSERVED_PRICE_DATE": values.get("TRADING_DAY_GUARD_LATEST_PRICE_DATE", ""),
        "RECOMMENDED_SIGNAL_DATE": values.get("TRADING_DAY_GUARD_RECOMMENDED_SIGNAL_DATE", ""),
        "R30E_STATUS": values.get("R30E_STATUS", ""),
        "R30E_FAILURE_CLASSIFICATION": values.get("R30E_FAILURE_CLASSIFICATION", ""),
        "R30E_FAILURE_SOFTENED_BY_STRUCTURAL_VALIDATION": values.get("R30E_FAILURE_SOFTENED_BY_STRUCTURAL_VALIDATION", ""),
        "INDEPENDENT_STRUCTURAL_VALIDATION_RESULT": values.get("INDEPENDENT_STRUCTURAL_VALIDATION_RESULT", ""),
        "R31A_STATUS": values.get("R31A_STATUS", ""),
        "R31B_STATUS": values.get("R31B_STATUS", ""),
        "R31C_STATUS": values.get("R31C_STATUS", ""),
        "R31D_STATUS": values.get("R31D_STATUS", ""),
        "R31E_STATUS": values.get("R31E_STATUS", ""),
        "R31E_SIGNAL_DATE_OVERRIDE_USED": values.get("R31E_SIGNAL_DATE_OVERRIDE_USED", ""),
        "R31E_SIGNAL_DATE": values.get("SIGNAL_DATE", ""),
        "R31E_DUPLICATE_SIGNAL_DATE_TICKER_COUNT": values.get("R31E_DUPLICATE_SIGNAL_DATE_TICKER_COUNT", ""),
        "CURRENT_RANKED_CANDIDATE_ROWS": values.get("CURRENT_RANKED_CANDIDATE_ROWS", ""),
        "CURRENT_RECOMMENDATION_ROWS": values.get("CURRENT_RECOMMENDATION_ROWS", ""),
        "CURRENT_THEME_CLASSIFICATION_ROWS": values.get("CURRENT_THEME_CLASSIFICATION_ROWS", ""),
        "LATEST_FULL_FREEZE_TICKER_COUNT": values.get("LATEST_FULL_FREEZE_TICKER_COUNT", ""),
        "R31A_OUTPUT_ROWS": values.get("R31A_OUTPUT_ROWS", ""),
        "R31B_OUTPUT_ROWS": values.get("R31B_OUTPUT_ROWS", ""),
        "R31C_OUTPUT_ROWS": values.get("R31C_OUTPUT_ROWS", ""),
        "R31D_OUTPUT_ROWS": values.get("R31D_OUTPUT_ROWS", ""),
        "AUTO_TRADE": values.get("AUTO_TRADE", ""),
        "AUTO_SELL": values.get("AUTO_SELL", ""),
        "OFFICIAL_DECISION_IMPACT": values.get("OFFICIAL_DECISION_IMPACT", ""),
        "VALIDATION_FAIL_COUNT": values.get("VALIDATION_FAIL_COUNT", ""),
        "FORBIDDEN_MODIFIED": values.get("FORBIDDEN_MODIFIED", ""),
        "NEXT_RECOMMENDED_STEP": values.get("NEXT_RECOMMENDED_STEP", ""),
    }
    return "\n".join(f"{field}: {mapped.get(field, '')}" for field in R1_READ_FIRST_FIELDS) + "\n"


def build_r1_summary(values: Dict[str, object], notes: str) -> List[Dict[str, object]]:
    return [{
        "run_id": values.get("RUN_ID", ""),
        "status": values.get("STATUS", ""),
        "generated_at": values.get("_GENERATED_AT", ""),
        "r31f_non_trading_mode": values.get("R31F_NON_TRADING_MODE", ""),
        "r31g_status": values.get("R31G_STATUS", ""),
        "candidate_signal_date": values.get("TRADING_DAY_GUARD_CANDIDATE_SIGNAL_DATE", ""),
        "latest_observed_price_date": values.get("TRADING_DAY_GUARD_LATEST_PRICE_DATE", ""),
        "recommended_signal_date": values.get("TRADING_DAY_GUARD_RECOMMENDED_SIGNAL_DATE", ""),
        "r30e_status": values.get("R30E_STATUS", ""),
        "r30e_failure_classification": values.get("R30E_FAILURE_CLASSIFICATION", ""),
        "r30e_failure_softened_by_structural_validation": values.get("R30E_FAILURE_SOFTENED_BY_STRUCTURAL_VALIDATION", ""),
        "independent_structural_validation_result": values.get("INDEPENDENT_STRUCTURAL_VALIDATION_RESULT", ""),
        "r31e_signal_date_override_used": values.get("R31E_SIGNAL_DATE_OVERRIDE_USED", ""),
        "r31e_signal_date": values.get("SIGNAL_DATE", ""),
        "r31e_duplicate_signal_date_ticker_count": values.get("R31E_DUPLICATE_SIGNAL_DATE_TICKER_COUNT", ""),
        "validation_fail_count": values.get("VALIDATION_FAIL_COUNT", ""),
        "forbidden_modified": values.get("FORBIDDEN_MODIFIED", ""),
        "notes": notes,
    }]


def build_r1_report(values: Dict[str, object], steps: Sequence[Dict[str, object]], warnings: Sequence[str], failures: Sequence[str]) -> str:
    return "\n".join([
        "# V18.31F-R1 Non-Trading-Day Current-Only Fallback",
        "",
        "## 1. Final Status",
        f"STATUS: {values.get('STATUS', '')}",
        "",
        "## 2. Non-Trading Fallback",
        f"- Active: `{values.get('R31F_NON_TRADING_MODE', '')}`",
        f"- Reused signal date: `{values.get('REUSED_SIGNAL_DATE', '')}`",
        "",
        "## 3. R31G Guard Decision",
        f"- R31G status: `{values.get('R31G_STATUS', '')}`",
        f"- Candidate signal date: `{values.get('TRADING_DAY_GUARD_CANDIDATE_SIGNAL_DATE', '')}`",
        f"- Latest observed price date: `{values.get('TRADING_DAY_GUARD_LATEST_PRICE_DATE', '')}`",
        f"- Recommended signal date: `{values.get('TRADING_DAY_GUARD_RECOMMENDED_SIGNAL_DATE', '')}`",
        "",
        "## 4. R30E Result",
        f"- R30E status: `{values.get('R30E_STATUS', '')}`",
        f"- Failure classification: `{values.get('R30E_FAILURE_CLASSIFICATION', '')}`",
        f"- Softened by structural validation: `{values.get('R30E_FAILURE_SOFTENED_BY_STRUCTURAL_VALIDATION', '')}`",
        "",
        "## 5. Independent Structural Validation",
        f"- Result: `{values.get('INDEPENDENT_STRUCTURAL_VALIDATION_RESULT', '')}`",
        f"- Ranked rows: `{values.get('CURRENT_RANKED_CANDIDATE_ROWS', '')}`",
        f"- Recommendation rows: `{values.get('CURRENT_RECOMMENDATION_ROWS', '')}`",
        f"- Theme rows: `{values.get('CURRENT_THEME_CLASSIFICATION_ROWS', '')}`",
        f"- Latest freeze ticker count: `{values.get('LATEST_FULL_FREEZE_TICKER_COUNT', '')}`",
        "",
        "## 6. R31A/B/C/D/E Execution",
        markdown_table(steps, ["step_order", "step_name", "parsed_status", "result", "continue_allowed", "notes"], limit=20),
        "## 7. R31E Signal-Date Override",
        f"- Override used: `{values.get('R31E_SIGNAL_DATE_OVERRIDE_USED', '')}`",
        f"- R31E signal date: `{values.get('SIGNAL_DATE', '')}`",
        f"- Duplicate signal_date+ticker count: `{values.get('R31E_DUPLICATE_SIGNAL_DATE_TICKER_COUNT', '')}`",
        "",
        "## 8. Unsupported Date Prevention",
        f"- Guard action: `{values.get('TRADING_DAY_GUARD_ACTION', '')}`",
        "- R31E must not create unsupported weekend dates in fallback mode.",
        "",
        "## 9. Safety",
        "- AUTO_TRADE: `DISABLED`",
        "- AUTO_SELL: `DISABLED`",
        "- OFFICIAL_DECISION_IMPACT: `NONE`",
        "- Broker/API calls: `NOT_EXECUTED`",
        "- Order placement: `NOT_EXECUTED`",
        "",
        "## 10. Warnings",
        "\n".join(f"- `{item}`" for item in (warnings or ["NONE"])),
        "",
        "## 11. Validation Failures",
        "\n".join(f"- `{item}`" for item in (failures or ["NONE"])),
        "",
        "## 12. Next Step",
        values.get("NEXT_RECOMMENDED_STEP", ""),
    ]) + "\n"


def write_outputs(root: Path, values: Dict[str, object], steps: Sequence[Dict[str, object]], warnings: Sequence[str], failures: Sequence[str]) -> None:
    values["_ROOT"] = str(root)
    values["DAILY_READ_FILES"] = daily_files(root)
    values.setdefault("_GENERATED_AT", dt.datetime.now().isoformat(timespec="seconds"))
    values["STALE_OUTPUT_SUPPRESSED_ON_FAIL"] = bool_text(norm(values.get("STATUS")).startswith("FAIL_"))
    write_csv(root / OUT_SUMMARY, steps, SUMMARY_FIELDS)
    write_text(root / OUT_READ_FIRST, read_first_text(values))
    home = build_homepage(values, warnings)
    write_text(root / OUT_CURRENT_HOME, home)
    write_text(root / OUT_REPORT, build_report(values, steps, warnings, failures))
    r1_notes = "; ".join(failures) if failures else ("; ".join(warnings) if warnings else "OK")
    write_text(root / OUT_R1_READ_FIRST, r1_read_first_text(values))
    write_csv(root / OUT_R1_SUMMARY, build_r1_summary(values, r1_notes), R1_SUMMARY_FIELDS)
    write_text(root / OUT_R1_REPORT, build_r1_report(values, steps, warnings, failures))


def fail_error_report(root: Path, values: Dict[str, object], step: Dict[str, object], proc: Optional[subprocess.CompletedProcess[str]], message: str) -> None:
    stderr = ""
    if proc is not None:
        stderr = (proc.stderr or proc.stdout or "").strip()[:2000]
    write_text(root / OUT_ERROR_REPORT, "\n".join([
        "# V18.31F Full Daily Trade-Readiness Error",
        "",
        f"STATUS: {values.get('STATUS', '')}",
        f"FAILED_STEP: {step.get('step_name', '')}",
        f"COMMAND: {step.get('command', '')}",
        f"REASON: {message}",
        "",
        "```text",
        stderr,
        "```",
        "",
    ]))


def initial_values(args: argparse.Namespace, run_id: str) -> Dict[str, object]:
    return {
        "STATUS": STATUS_DRY if args.dry_run else STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": run_id,
        "DRY_RUN": bool_text(args.dry_run),
        "TOP_N_REQUESTED": args.top_n,
        "ACCOUNT_SIZE_USD": args.account_size_usd,
        "CASH_USD": "" if args.cash_usd is None else args.cash_usd,
        "CASH_RESERVE_PCT": args.cash_reserve_pct,
        "BROKER_PROFILE": args.broker_profile,
        "MIN_EFFECTIVE_TRADE_NOTIONAL_USD": args.min_effective_trade_notional_usd,
        "SAME_DAY_POLICY": args.same_day_policy,
        "R31F_R1_PATCH_APPLIED": "TRUE",
        "R31F_NON_TRADING_MODE": "FALSE",
        "R30E_FAILURE_SOFTENED_BY_STRUCTURAL_VALIDATION": "FALSE",
        "R30E_FAILURE_CLASSIFICATION": "",
        "INDEPENDENT_STRUCTURAL_VALIDATION_RESULT": "",
        "REUSED_SIGNAL_DATE": "",
        "R31E_SIGNAL_DATE_OVERRIDE_USED": "FALSE",
        "STALE_OUTPUT_SUPPRESSED_ON_FAIL": "FALSE",
        "R31G_STATUS": "",
        "TRADING_DAY_GUARD_NEW_SIGNAL_DATE_ALLOWED": "",
        "TRADING_DAY_GUARD_RECOMMENDED_SIGNAL_DATE": "",
        "TRADING_DAY_GUARD_REUSED_LATEST_SIGNAL_DATE": "FALSE",
        "TRADING_DAY_GUARD_CANDIDATE_SIGNAL_DATE": "",
        "TRADING_DAY_GUARD_LATEST_PRICE_DATE": "",
        "TRADING_DAY_GUARD_ACTION": "",
        "NON_TRADING_DATE_GUARD_APPLIED": "FALSE",
        "R30E_STATUS": "SKIPPED_BY_OPERATOR_FLAG" if args.skip_r30e else "",
        "R31A_STATUS": "",
        "R31B_STATUS": "",
        "R31C_STATUS": "",
        "R31C_R1_STATUS": "",
        "R31D_STATUS": "",
        "R31E_STATUS": "SKIPPED_BY_OPERATOR_FLAG" if args.skip_r31e else "",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "VALIDATION_FAIL_COUNT": 0,
        "FORBIDDEN_MODIFIED": "FALSE",
        "FINAL_OPERATOR_ACTION": "",
        "DAILY_READ_FILES": "",
        "NEXT_RECOMMENDED_STEP": "",
    }


def run(root: Path, args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    now = dt.datetime.now()
    run_id = now.strftime("V18_31F_%Y%m%d_%H%M%S")
    steps: List[Dict[str, object]] = []
    values = initial_values(args, run_id)
    values["_GENERATED_AT"] = now.isoformat(timespec="seconds")
    root.joinpath("outputs/v18/read_center").mkdir(parents=True, exist_ok=True)
    root.joinpath("outputs/v18/ops").mkdir(parents=True, exist_ok=True)

    missing = validate_wrappers(root, args)
    if missing:
        values["STATUS"] = STATUS_FAIL
        values["VALIDATION_FAIL_COUNT"] = len(missing)
        values["NEXT_RECOMMENDED_STEP"] = "Restore missing wrappers before running the full daily trade-readiness runner."
        failures = [f"Missing wrapper: {rel}" for rel in missing]
        write_outputs(root, values, steps, [], failures)
        write_text(root / OUT_ERROR_REPORT, "# V18.31F Full Daily Trade-Readiness Error\n\n" + "\n".join(f"- {item}" for item in failures) + "\n")
        return 1, values

    if args.dry_run:
        order = 1
        add_planned_step(root, run_id, steps, order, "R31G trading-day signal-date guard", R31G_WRAPPER, R31G_READ_FIRST)
        order += 1
        if not args.skip_r30e:
            add_planned_step(root, run_id, steps, order, "R30E safe daily operator sequence", R30E_WRAPPER, R30E_READ_FIRST, ["-TopN", args.top_n])
            order += 1
        add_planned_step(root, run_id, steps, order, "R31A static buyability gate", R31A_WRAPPER, R31A_READ_FIRST, ["-TopN", args.top_n])
        order += 1
        add_planned_step(root, run_id, steps, order, "R31B manual position sizing policy", R31B_WRAPPER, R31B_READ_FIRST, ["-TopN", args.top_n])
        order += 1
        add_planned_step(root, run_id, steps, order, "R31C cost/slippage constraints", R31C_WRAPPER, R31C_READ_FIRST, ["-TopN", args.top_n])
        order += 1
        add_planned_step(root, run_id, steps, order, "R31D account-aware manual trade plan", R31D_WRAPPER, R31D_READ_FIRST, ["-TopN", args.top_n])
        order += 1
        if not args.skip_r31e:
            add_planned_step(root, run_id, steps, order, "R31E daily trade plan snapshot ledger", R31E_WRAPPER, R31E_READ_FIRST, ["-TopN", args.top_n, "-SameDayPolicy", args.same_day_policy])
        values["STATUS"] = STATUS_DRY
        values["NEXT_RECOMMENDED_STEP"] = "Run R31F live after reviewing the planned sequence."
        write_outputs(root, values, steps, [], [])
        return 0, values

    try:
        order = 1
        ok, rf, step, proc = run_step(root, run_id, steps, order, "R31G trading-day signal-date guard", R31G_WRAPPER, R31G_READ_FIRST, STATUS_FAIL, args)
        values["R31G_STATUS"] = rf.get("STATUS", "")
        guard_allowed = rf.get("NEW_SIGNAL_DATE_ALLOWED") == "TRUE"
        guard_reuse = rf.get("REUSE_LATEST_SIGNAL_DATE_RECOMMENDED") == "TRUE"
        guard_recommended_signal_date = rf.get("RECOMMENDED_SIGNAL_DATE", "")
        values["TRADING_DAY_GUARD_NEW_SIGNAL_DATE_ALLOWED"] = rf.get("NEW_SIGNAL_DATE_ALLOWED", "")
        values["TRADING_DAY_GUARD_RECOMMENDED_SIGNAL_DATE"] = guard_recommended_signal_date
        values["TRADING_DAY_GUARD_REUSED_LATEST_SIGNAL_DATE"] = bool_text((not guard_allowed) and guard_reuse)
        values["TRADING_DAY_GUARD_CANDIDATE_SIGNAL_DATE"] = rf.get("CANDIDATE_SIGNAL_DATE", "")
        values["TRADING_DAY_GUARD_LATEST_PRICE_DATE"] = rf.get("LATEST_OBSERVED_PRICE_DATE", "")
        values["TRADING_DAY_GUARD_ACTION"] = "NORMAL_DAILY_RUN" if guard_allowed else ("REUSE_LATEST_SIGNAL_DATE_SKIP_NEW_LEDGER_DATE" if guard_reuse else "BLOCK_NEW_SIGNAL_DATE_REQUIRES_OVERRIDE")
        values["NON_TRADING_DATE_GUARD_APPLIED"] = bool_text(not guard_allowed)
        non_trading_mode = (not guard_allowed) and guard_reuse and bool(guard_recommended_signal_date)
        values["R31F_NON_TRADING_MODE"] = bool_text(non_trading_mode)
        values["REUSED_SIGNAL_DATE"] = guard_recommended_signal_date if non_trading_mode else ""
        independent = independent_structural_validation(root, guard_recommended_signal_date)
        values["INDEPENDENT_STRUCTURAL_VALIDATION_RESULT"] = independent["result"]
        values["CURRENT_RANKED_CANDIDATE_ROWS"] = independent["ranked_rows"]
        values["CURRENT_RECOMMENDATION_ROWS"] = independent["recommendation_rows"]
        values["CURRENT_THEME_CLASSIFICATION_ROWS"] = independent["theme_rows"]
        values["LATEST_FULL_FREEZE_TICKER_COUNT"] = independent["latest_full_freeze_ticker_count"]
        order += 1
        if not ok:
            values["STATUS"] = STATUS_FAIL
            values["NEXT_RECOMMENDED_STEP"] = "Inspect R31G guard output before continuing daily trade-readiness orchestration."
            fail_error_report(root, values, step, proc, STATUS_FAIL)
            write_outputs(root, values, steps, [], [STATUS_FAIL])
            return 1, values

        if not args.skip_r30e:
            r30e_args: List[object] = ["-TopN", args.top_n]
            if not guard_allowed and guard_reuse:
                r30e_args.extend(["-SkipR21", "-SkipR29C"])
            ok, rf, step, proc = run_step(root, run_id, steps, order, "R30E safe daily operator sequence", R30E_WRAPPER, R30E_READ_FIRST, FAIL_R30E, args, r30e_args)
            values["R30E_STATUS"] = rf.get("STATUS", "")
            order += 1
            if not ok:
                classification = classify_r30e_failure(rf, proc, non_trading_mode)
                values["R30E_FAILURE_CLASSIFICATION"] = classification
                if non_trading_mode and independent["passes"]:
                    values["R30E_FAILURE_SOFTENED_BY_STRUCTURAL_VALIDATION"] = "TRUE"
                    step["continue_allowed"] = "TRUE"
                    step["result"] = "WARN_ACCEPTED"
                    step["notes"] = f"R30E failed in non-trading reuse mode; softened because independent structural validation passed: {independent['result']}."
                else:
                    values["STATUS"] = STATUS_R1_STRUCT_FAIL if not independent["passes"] else FAIL_R30E
                    values["NEXT_RECOMMENDED_STEP"] = "Inspect R30E outputs and independent structural validation before continuing."
                    fail_error_report(root, values, step, proc, values["STATUS"])
                    write_outputs(root, values, steps, [], [values["STATUS"]])
                    return 1, values
            else:
                values["R30E_FAILURE_CLASSIFICATION"] = "NOT_FAILURE"

        ok, rf, step, proc = run_step(root, run_id, steps, order, "R31A static buyability gate", R31A_WRAPPER, R31A_READ_FIRST, FAIL_R31A, args, ["-TopN", args.top_n])
        values["R31A_STATUS"] = rf.get("STATUS", "")
        order += 1
        if not ok:
            values["STATUS"] = FAIL_R31A
            fail_error_report(root, values, step, proc, FAIL_R31A)
            write_outputs(root, values, steps, [], [FAIL_R31A])
            return 1, values

        r31b_args = ["-TopN", args.top_n, "-AccountSizeUsd", args.account_size_usd, "-CashReservePct", args.cash_reserve_pct, "-MaxActivePositions", args.max_active_positions, "-MaxSpeculativePositions", args.max_speculative_positions]
        ok, rf, step, proc = run_step(root, run_id, steps, order, "R31B manual position sizing policy", R31B_WRAPPER, R31B_READ_FIRST, FAIL_R31B, args, r31b_args)
        values["R31B_STATUS"] = rf.get("STATUS", "")
        order += 1
        if not ok:
            values["STATUS"] = FAIL_R31B
            fail_error_report(root, values, step, proc, FAIL_R31B)
            write_outputs(root, values, steps, [], [FAIL_R31B])
            return 1, values

        r31c_args = [
            "-TopN", args.top_n,
            "-BrokerProfile", args.broker_profile,
            "-CommissionRatePct", args.commission_rate_pct,
            "-CommissionMinUsd", args.commission_min_usd,
            "-CommissionCapUsd", args.commission_cap_usd,
            "-FxFeeJpyPerUsd", args.fx_fee_jpy_per_usd,
            "-ConservativeFxFeeJpyPerUsd", args.conservative_fx_fee_jpy_per_usd,
            "-MinEffectiveTradeNotionalUsd", args.min_effective_trade_notional_usd,
            "-CostSafetyMultiple", args.cost_safety_multiple,
        ]
        ok, rf, step, proc = run_step(root, run_id, steps, order, "R31C cost/slippage constraints", R31C_WRAPPER, R31C_READ_FIRST, FAIL_R31C, args, r31c_args)
        values["R31C_STATUS"] = rf.get("STATUS", "")
        order += 1
        if not ok:
            if non_trading_mode and softenable_current_only_layer(rf, ["OUTPUT_COST_ADJUSTED_ROWS", "OUTPUT_ROWS"]):
                step["continue_allowed"] = "TRUE"
                step["result"] = "WARN_ACCEPTED"
                step["notes"] = "R31C failed from propagated non-trading operator state, but produced structurally valid 252-row current-only cost output."
            else:
                values["STATUS"] = FAIL_R31C
                fail_error_report(root, values, step, proc, FAIL_R31C)
                write_outputs(root, values, steps, [], [FAIL_R31C])
                return 1, values

        r31d_args = [
            "-TopN", args.top_n,
            "-AccountSizeUsd", args.account_size_usd,
            "-CashReservePct", args.cash_reserve_pct,
            "-MaxActivePositions", args.max_active_positions,
            "-MaxSpeculativePositions", args.max_speculative_positions,
            "-MaxSinglePositionPct", args.max_single_position_pct,
            "-MaxThemeExposurePct", args.max_theme_exposure_pct,
            "-MaxHighRiskTotalExposurePct", args.max_high_risk_total_exposure_pct,
            "-MaxNewBuysPerDay", args.max_new_buys_per_day,
            "-MinCashAfterTradeUsd", args.min_cash_after_trade_usd,
        ]
        if args.cash_usd is not None:
            r31d_args.extend(["-CashUsd", args.cash_usd])
        ok, rf, step, proc = run_step(root, run_id, steps, order, "R31D account-aware manual trade plan", R31D_WRAPPER, R31D_READ_FIRST, FAIL_R31D, args, r31d_args)
        values["R31D_STATUS"] = rf.get("STATUS", "")
        order += 1
        if not ok:
            if non_trading_mode and softenable_current_only_layer(rf, ["OUTPUT_ACCOUNT_AWARE_ROWS", "OUTPUT_ROWS"]):
                step["continue_allowed"] = "TRUE"
                step["result"] = "WARN_ACCEPTED"
                step["notes"] = "R31D failed from propagated non-trading operator state, but produced structurally valid 252-row current-only account-aware output."
            else:
                values["STATUS"] = FAIL_R31D
                fail_error_report(root, values, step, proc, FAIL_R31D)
                write_outputs(root, values, steps, [], [FAIL_R31D])
                return 1, values

        should_run_r31e = not args.skip_r31e and (guard_allowed or (guard_reuse and bool(guard_recommended_signal_date)))
        if should_run_r31e:
            r31e_args: List[object] = ["-TopN", args.top_n, "-SameDayPolicy", args.same_day_policy]
            if not guard_allowed and guard_reuse and guard_recommended_signal_date:
                r31e_args.extend(["-SignalDateOverride", guard_recommended_signal_date])
            ok, rf, step, proc = run_step(root, run_id, steps, order, "R31E daily trade plan snapshot ledger", R31E_WRAPPER, R31E_READ_FIRST, FAIL_R31E, args, r31e_args)
            values["R31E_STATUS"] = rf.get("STATUS", "")
            values["R31E_SIGNAL_DATE_OVERRIDE_USED"] = rf.get("SIGNAL_DATE_OVERRIDE_USED", values.get("R31E_SIGNAL_DATE_OVERRIDE_USED", ""))
            if not ok:
                r31e_soft_ok = (
                    non_trading_mode
                    and rf.get("SIGNAL_DATE_OVERRIDE_USED") == "TRUE"
                    and rf.get("SIGNAL_DATE") == guard_recommended_signal_date
                    and to_int(rf.get("APPENDED_ROWS"), -1) == EXPECTED_ROWS
                    and to_int(rf.get("DUPLICATE_SIGNAL_DATE_TICKER_COUNT"), -1) == 0
                    and rf.get("AUTO_TRADE", "DISABLED") == "DISABLED"
                    and rf.get("AUTO_SELL", "DISABLED") == "DISABLED"
                    and rf.get("OFFICIAL_DECISION_IMPACT", "NONE") == "NONE"
                    and rf.get("FORBIDDEN_MODIFIED", "FALSE") == "FALSE"
                )
                if r31e_soft_ok:
                    step["continue_allowed"] = "TRUE"
                    step["result"] = "WARN_ACCEPTED"
                    step["notes"] = "R31E returned FAIL from inherited non-trading/partial-freeze validation, but signal-date override, 252-row replace, and duplicate checks passed."
                else:
                    values["STATUS"] = FAIL_R31E
                    fail_error_report(root, values, step, proc, FAIL_R31E)
                    write_outputs(root, values, steps, [], [FAIL_R31E])
                    return 1, values
        else:
            reason = "--skip-r31e set" if args.skip_r31e else "Guard blocked new signal date and no reusable signal date was available."
            values["R31E_STATUS"] = "SKIPPED_BY_TRADING_DAY_GUARD" if not args.skip_r31e else "SKIPPED_BY_OPERATOR_FLAG"
            steps.append(build_step(run_id, order, "R31E daily trade plan snapshot ledger", "", str(root / R31E_READ_FIRST), values["R31E_STATUS"], "SKIPPED", "SKIPPED", True, reason))

        warnings, _r31d = gather_values(root, values)
        failures = validation_failures(values, args)
        values["VALIDATION_FAIL_COUNT"] = len(failures)
        if failures:
            values["STATUS"] = STATUS_R1_LEDGER_FAIL if any("R31E" in item for item in failures) else STATUS_FAIL
            values["NEXT_RECOMMENDED_STEP"] = "Inspect R31F validation failures before using daily trade-readiness outputs."
        elif non_trading_mode:
            values["STATUS"] = STATUS_R1_WARN
            values["NEXT_RECOMMENDED_STEP"] = "Manual review only; current reports reused latest supported signal date and no new signal_date was created."
        elif warnings:
            values["STATUS"] = STATUS_WARN
            values["NEXT_RECOMMENDED_STEP"] = "Manual review only; update account state if needed and wait for forward-return validation data."
        else:
            values["STATUS"] = STATUS_OK
            values["NEXT_RECOMMENDED_STEP"] = "Review V18_CURRENT_DAILY_TRADE_READINESS.md and account-aware plan manually."
        write_outputs(root, values, steps, warnings, failures)
        return (1 if failures else 0), values
    except Exception:
        values["STATUS"] = STATUS_FAIL
        values["VALIDATION_FAIL_COUNT"] = 1
        failures = [traceback.format_exc()]
        write_outputs(root, values, steps, [], failures)
        write_text(root / OUT_ERROR_REPORT, "# V18.31F Full Daily Trade-Readiness Error\n\n```text\n" + traceback.format_exc() + "\n```\n")
        return 1, values


def resolve_root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.31F full daily trade-readiness runner.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--top-n", type=int, default=252)
    parser.add_argument("--account-size-usd", type=float, default=2000)
    parser.add_argument("--cash-usd", type=float, default=None)
    parser.add_argument("--cash-reserve-pct", type=float, default=15)
    parser.add_argument("--max-active-positions", type=int, default=8)
    parser.add_argument("--max-speculative-positions", type=int, default=2)
    parser.add_argument("--max-single-position-pct", type=float, default=12)
    parser.add_argument("--max-theme-exposure-pct", type=float, default=35)
    parser.add_argument("--max-high-risk-total-exposure-pct", type=float, default=25)
    parser.add_argument("--max-new-buys-per-day", type=int, default=3)
    parser.add_argument("--min-cash-after-trade-usd", type=float, default=100)
    parser.add_argument("--broker-profile", default="MOOMOO_JP_US_STOCK_BASIC")
    parser.add_argument("--commission-rate-pct", type=float, default=0.132)
    parser.add_argument("--commission-min-usd", type=float, default=0.00)
    parser.add_argument("--commission-cap-usd", type=float, default=22.00)
    parser.add_argument("--fx-fee-jpy-per-usd", type=float, default=0.00)
    parser.add_argument("--conservative-fx-fee-jpy-per-usd", type=float, default=0.25)
    parser.add_argument("--min-effective-trade-notional-usd", type=float, default=50)
    parser.add_argument("--cost-safety-multiple", type=float, default=2.0)
    parser.add_argument("--same-day-policy", choices=["REPLACE", "SKIP", "APPEND_EXPLICIT"], default="REPLACE")
    parser.add_argument("--skip-r30e", action="store_true")
    parser.add_argument("--skip-r31e", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--stop-on-warn", action="store_true")
    parser.add_argument("--no-open", action="store_true", help="Compatibility flag; no files are opened by this script.")
    args = parser.parse_args()
    root = resolve_root(args.root)
    code, values = run(root, args)
    print(f"STATUS: {values.get('STATUS', '')}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    print(f"DAILY_HOME: {root / OUT_CURRENT_HOME}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
