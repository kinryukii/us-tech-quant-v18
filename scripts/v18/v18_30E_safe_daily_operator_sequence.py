from __future__ import annotations

import argparse
import csv
import datetime as dt
import subprocess
import sys
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


STATUS_DRY = "OK_V18_30E_SAFE_DAILY_SEQUENCE_DRY_RUN_READY"
STATUS_OK = "OK_V18_30E_SAFE_DAILY_OPERATOR_SEQUENCE_READY"
STATUS_WARN = "WARN_V18_30E_SAFE_DAILY_OPERATOR_SEQUENCE_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_30E_SAFE_DAILY_OPERATOR_SEQUENCE_FAILED"

MODE_LIVE = "SAFE_DAILY_OPERATOR_SEQUENCE"
MODE_DRY = "SAFE_DAILY_OPERATOR_SEQUENCE_DRY_RUN"
EXPECTED_ROWS = 252

OUT_READ_FIRST = "outputs/v18/ops/V18_30E_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_30E_SAFE_DAILY_SEQUENCE_SUMMARY.csv"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_SAFE_DAILY_OPERATOR_SEQUENCE.md"
OUT_REPORT = "outputs/v18/read_center/V18_30E_SAFE_DAILY_OPERATOR_SEQUENCE_REPORT.md"
OUT_ERROR_REPORT = "outputs/v18/read_center/V18_30E_SAFE_DAILY_OPERATOR_SEQUENCE_ERROR.md"

R30B_WRAPPER = "scripts/v18/run_v18_30B_daily_command_compatibility_guard.ps1"
R28A_WRAPPER_REQUESTED = "scripts/v18/run_v18_28A_theme_classification_layer.ps1"
R28A_WRAPPER_EXISTING = "scripts/v18/run_v18_28A_sector_theme_classification_audit.ps1"
R28B_WRAPPER = "scripts/v18/run_v18_28B_recommendation_tier_action_layer.ps1"
R21_WRAPPER = "scripts/v18/run_v18_25A_R21_daily_signal_freeze_forward_test_ledger.ps1"
R29C_WRAPPER = "scripts/v18/run_v18_29C_daily_recommendation_tier_snapshot_ledger.ps1"
R30A_WRAPPER = "scripts/v18/run_v18_30A_daily_operator_control_center.ps1"

R30B_READ_FIRST = "outputs/v18/ops/V18_30B_READ_FIRST.txt"
R28A_READ_FIRST = "outputs/v18/ops/V18_28A_READ_FIRST.txt"
R28B_READ_FIRST = "outputs/v18/ops/V18_28B_READ_FIRST.txt"
R21_READ_FIRST = "outputs/v18/ops/V18_25A_R21_READ_FIRST.txt"
R29C_READ_FIRST = "outputs/v18/ops/V18_29C_READ_FIRST.txt"
R30A_READ_FIRST = "outputs/v18/ops/V18_30A_READ_FIRST.txt"

CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
CURRENT_THEMES = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
CURRENT_RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
SIGNAL_FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
SNAPSHOT_LEDGER = "state/v18/recommendation_snapshots/V18_DAILY_RECOMMENDATION_TIER_LEDGER.csv"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "TOP_N_REQUESTED",
    "DRY_RUN",
    "FORCE_SNAPSHOT",
    "SKIP_R21",
    "SKIP_R29C",
    "R30B_STATUS",
    "R28A_STATUS",
    "R28B_STATUS",
    "R21_STATUS",
    "R21_SIGNAL_DATE",
    "R21_RUN_ID",
    "R21_FROZEN_ROW_COUNT",
    "R21_DUPLICATE_SIGNAL_DATE_TICKER_COUNT",
    "R21_MODE",
    "R29C_ACTION",
    "R29C_STATUS",
    "R29C_SNAPSHOT_DATE",
    "R29C_APPENDED_ROWS",
    "R30A_STATUS",
    "FINAL_OPERATOR_ACTION",
    "CURRENT_RANKED_CANDIDATE_ROWS",
    "CURRENT_THEME_CLASSIFICATION_ROWS",
    "CURRENT_RECOMMENDATION_ROWS",
    "LATEST_FULL_FREEZE_TICKER_COUNT",
    "LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
    "FAILED_STEP",
    "FAILED_REASON",
    "FAILED_COMMAND",
    "ERROR_REPORT_PATH",
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
    "action",
    "is_critical",
    "continue_allowed",
    "result",
    "notes",
]


def norm(value: object) -> str:
    return "" if value is None else str(value).strip()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def to_int(value: object, default: int = 0) -> int:
    try:
        text = norm(value)
        return int(float(text)) if text else default
    except Exception:
        return default


def parse_date(value: object) -> Optional[dt.date]:
    text = norm(value)
    if not text:
        return None
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


def resolve_root(root_arg: str) -> Path:
    if root_arg:
        return Path(root_arg).resolve()
    return Path(__file__).resolve().parents[2]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
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


def is_ok(status: str) -> bool:
    return norm(status).upper().startswith("OK_")


def is_warn(status: str) -> bool:
    return norm(status).upper().startswith("WARN_")


def r28a_wrapper(root: Path) -> str:
    requested = root / R28A_WRAPPER_REQUESTED
    return R28A_WRAPPER_REQUESTED if requested.exists() else R28A_WRAPPER_EXISTING


def command_for(root: Path, wrapper_rel: str, extra_args: Optional[Sequence[str]] = None) -> List[str]:
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root / wrapper_rel), "-Root", str(root)]
    if extra_args:
        cmd.extend([str(item) for item in extra_args])
    return cmd


def cmd_text(cmd: Sequence[str]) -> str:
    return " ".join(f'"{part}"' if " " in part else str(part) for part in cmd)


def run_step(
    root: Path,
    run_id: str,
    rows: List[Dict[str, object]],
    order: int,
    name: str,
    wrapper_rel: str,
    read_first_rel: str,
    required_status: str = "OK",
    extra_args: Optional[Sequence[str]] = None,
    critical: bool = True,
) -> Tuple[subprocess.CompletedProcess[str], Dict[str, str], Dict[str, object]]:
    cmd = command_for(root, wrapper_rel, extra_args)
    started = dt.datetime.now()
    proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
    ended = dt.datetime.now()
    rf_path = root / read_first_rel
    rf = read_status_file(rf_path)
    status = rf.get("STATUS", "")
    allowed = proc.returncode == 0 and is_ok(status)
    summary = {
        "run_id": run_id,
        "step_order": order,
        "step_name": name,
        "command": cmd_text(cmd),
        "started_at": started.isoformat(timespec="seconds"),
        "ended_at": ended.isoformat(timespec="seconds"),
        "duration_seconds": f"{(ended - started).total_seconds():.3f}",
        "exit_code": proc.returncode,
        "read_first_path": str(rf_path),
        "parsed_status": status,
        "required_status": required_status,
        "action": "EXECUTED",
        "is_critical": bool_text(critical),
        "continue_allowed": bool_text(allowed),
        "result": "PASS" if allowed else "FAIL",
        "notes": "",
    }
    if proc.returncode != 0:
        summary["notes"] = (proc.stderr or proc.stdout or "").strip()[:500]
    rows.append(summary)
    return proc, rf, summary


def add_planned_step(
    root: Path,
    run_id: str,
    rows: List[Dict[str, object]],
    order: int,
    name: str,
    wrapper_rel: str,
    read_first_rel: str,
    extra_args: Optional[Sequence[str]] = None,
) -> None:
    rows.append(
        {
            "run_id": run_id,
            "step_order": order,
            "step_name": name,
            "command": cmd_text(command_for(root, wrapper_rel, extra_args)),
            "started_at": "",
            "ended_at": "",
            "duration_seconds": "",
            "exit_code": "",
            "read_first_path": str(root / read_first_rel),
            "parsed_status": "",
            "required_status": "OK",
            "action": "PLANNED_DRY_RUN",
            "is_critical": "TRUE",
            "continue_allowed": "TRUE",
            "result": "PLANNED",
            "notes": "",
        }
    )


def latest_freeze(root: Path) -> Dict[str, object]:
    rows = read_csv(root / SIGNAL_FREEZE_LEDGER)
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[norm(row.get("run_id"))].append(row)
    if not grouped:
        return {"run_id": "", "signal_date": "", "ticker_count": 0, "duplicate_signal_date_ticker_count": 0}

    def group_key(item: Tuple[str, List[Dict[str, str]]]) -> Tuple[dt.datetime, dt.date, str]:
        run_id, group = item
        ts = max((parse_dt(row.get("run_timestamp")) for row in group), default=dt.datetime.min)
        signal_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in group), default=dt.date.min)
        return ts, signal_date, run_id

    run_id, group = max(grouped.items(), key=group_key)
    signal_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in group), default=dt.date.min)
    tickers = {norm(row.get("ticker")).upper() for row in group if norm(row.get("ticker"))}
    counts = Counter((norm(row.get("signal_date")), norm(row.get("ticker")).upper()) for row in rows)
    duplicate_count = sum(1 for key, count in counts.items() if key[0] and key[1] and count > 1)
    return {
        "run_id": run_id,
        "signal_date": signal_date.isoformat() if signal_date != dt.date.min else "",
        "ticker_count": len(tickers),
        "duplicate_signal_date_ticker_count": duplicate_count,
    }


def snapshot_count_for_date(root: Path, signal_date: str) -> int:
    if not signal_date:
        return 0
    rows = read_csv(root / SNAPSHOT_LEDGER)
    return sum(1 for row in rows if norm(row.get("snapshot_date")) == signal_date)


def current_row_counts(root: Path) -> Dict[str, int]:
    return {
        "candidates": len(read_csv(root / CURRENT_CANDIDATES)),
        "themes": len(read_csv(root / CURRENT_THEMES)),
        "recommendations": len(read_csv(root / CURRENT_RECOMMENDATIONS)),
    }


def expected_r30a_warn_only(r30a: Dict[str, str]) -> bool:
    structural_ok = (
        to_int(r30a.get("CURRENT_RANKED_CANDIDATE_ROW_COUNT")) == EXPECTED_ROWS
        and to_int(r30a.get("THEME_CLASSIFICATION_ROW_COUNT")) == EXPECTED_ROWS
        and to_int(r30a.get("CURRENT_RECOMMENDATION_ROW_COUNT")) == EXPECTED_ROWS
        and to_int(r30a.get("LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT")) == EXPECTED_ROWS
        and to_int(r30a.get("LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT")) == EXPECTED_ROWS
    )
    safety_ok = (
        r30a.get("AUTO_TRADE") == "DISABLED"
        and r30a.get("AUTO_SELL") == "DISABLED"
        and r30a.get("OFFICIAL_DECISION_IMPACT") == "NONE"
        and r30a.get("FORBIDDEN_MODIFIED") == "FALSE"
    )
    forward_total = sum(
        to_int(r30a.get(field))
        for field in [
            "FORWARD_1D_FILLABLE_COUNT",
            "FORWARD_3D_FILLABLE_COUNT",
            "FORWARD_5D_FILLABLE_COUNT",
            "FORWARD_10D_FILLABLE_COUNT",
            "FORWARD_20D_FILLABLE_COUNT",
        ]
    )
    return structural_ok and safety_ok and forward_total == 0


def expected_r21_replace_warn(r21: Dict[str, str], top_n: int) -> bool:
    return (
        r21.get("STATUS") == "WARN_V18_25A_R21_SAME_DAY_FREEZE_REPLACED"
        and to_int(r21.get("FROZEN_ROW_COUNT")) == top_n
        and to_int(r21.get("DUPLICATE_SIGNAL_DATE_TICKER_COUNT_AFTER")) == 0
        and r21.get("AUTO_TRADE") == "DISABLED"
        and r21.get("AUTO_SELL") == "DISABLED"
        and r21.get("OFFICIAL_DECISION_IMPACT") == "NONE"
        and r21.get("FORBIDDEN_MODIFIED") == "FALSE"
        and to_int(r21.get("VALIDATION_FAIL_COUNT")) == 0
    )


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
    for key in [
        "CURRENT_RANKED_CANDIDATE_ROWS",
        "CURRENT_THEME_CLASSIFICATION_ROWS",
        "CURRENT_RECOMMENDATION_ROWS",
        "LATEST_FULL_FREEZE_TICKER_COUNT",
    ]:
        if to_int(values.get(key)) not in (0, EXPECTED_ROWS):
            fails += 1
    return fails


def read_first_text(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def markdown_table(rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> str:
    if not rows:
        return "_None._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def build_report(values: Dict[str, object], summary_rows: Sequence[Dict[str, object]]) -> str:
    status = norm(values.get("STATUS"))
    if status.startswith("FAIL_"):
        next_step = "Inspect the R30E error report and do not trade from the incomplete run."
    elif status.startswith("WARN_"):
        next_step = "Read V18_CURRENT_OPERATOR_CONTROL_CENTER.md, continue manual review, and do not run performance extraction until forward-return fillability is available."
    else:
        next_step = "Read V18_CURRENT_OPERATOR_CONTROL_CENTER.md for the current operator control center."
    return "\n".join(
        [
            "# V18.30E Safe Daily Operator Sequence",
            "",
            f"STATUS: {status}",
            f"RUN_ID: {values.get('RUN_ID', '')}",
            "",
            "## Sequence Result",
            markdown_table(summary_rows, ["step_order", "step_name", "parsed_status", "action", "result", "notes"]),
            "## Latest Signal Freeze",
            f"- R21 status: `{values.get('R21_STATUS', '')}`",
            f"- Signal date: `{values.get('R21_SIGNAL_DATE', '')}`",
            f"- R21 run id: `{values.get('R21_RUN_ID', '')}`",
            f"- Frozen rows: `{values.get('R21_FROZEN_ROW_COUNT', '')}`",
            f"- Latest full freeze ticker count: `{values.get('LATEST_FULL_FREEZE_TICKER_COUNT', '')}`",
            "",
            "## Recommendation Snapshot",
            f"- Action: `{values.get('R29C_ACTION', '')}`",
            f"- Status: `{values.get('R29C_STATUS', '')}`",
            f"- Snapshot date: `{values.get('R29C_SNAPSHOT_DATE', '')}`",
            f"- Appended rows: `{values.get('R29C_APPENDED_ROWS', '')}`",
            f"- Latest snapshot row count: `{values.get('LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT', '')}`",
            "",
            "## Operator Status",
            f"- R30A status: `{values.get('R30A_STATUS', '')}`",
            f"- Final operator action: `{values.get('FINAL_OPERATOR_ACTION', '')}`",
            "",
            "## Safety",
            "- AUTO_TRADE: `DISABLED`",
            "- AUTO_SELL: `DISABLED`",
            "- OFFICIAL_DECISION_IMPACT: `NONE`",
            "- Broker/API calls: `NOT_EXECUTED`",
            "",
            "## What To Do Next",
            next_step,
        ]
    ) + "\n"


def write_outputs(root: Path, values: Dict[str, object], summary_rows: Sequence[Dict[str, object]]) -> None:
    values["VALIDATION_FAIL_COUNT"] = validation_fail_count(values)
    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_text(root / OUT_READ_FIRST, read_first_text(values))
    report = build_report(values, summary_rows)
    write_text(root / OUT_CURRENT_REPORT, report)
    write_text(root / OUT_REPORT, report)


def fail_values(
    values: Dict[str, object],
    step: str,
    reason: str,
    command: str,
) -> Dict[str, object]:
    values["STATUS"] = STATUS_FAIL
    values["FAILED_STEP"] = step
    values["FAILED_REASON"] = reason
    values["FAILED_COMMAND"] = command
    values["ERROR_REPORT_PATH"] = OUT_ERROR_REPORT
    values["NEXT_RECOMMENDED_STEP"] = "Inspect error report and do not trade from incomplete run."
    return values


def validate_wrappers(root: Path) -> List[str]:
    wrappers = [R30B_WRAPPER, r28a_wrapper(root), R28B_WRAPPER, R21_WRAPPER, R29C_WRAPPER, R30A_WRAPPER]
    return [rel for rel in wrappers if not (root / rel).exists()]


def run(root: Path, args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    run_id = dt.datetime.now().strftime("V18_30E_%Y%m%d_%H%M%S")
    summary_rows: List[Dict[str, object]] = []
    counts = current_row_counts(root)
    freeze = latest_freeze(root)
    values: Dict[str, object] = {
        "STATUS": STATUS_DRY if args.dry_run else STATUS_FAIL,
        "MODE": MODE_DRY if args.dry_run else MODE_LIVE,
        "RUN_ID": run_id,
        "TOP_N_REQUESTED": args.top_n,
        "DRY_RUN": bool_text(args.dry_run),
        "FORCE_SNAPSHOT": bool_text(args.force_snapshot),
        "SKIP_R21": bool_text(args.skip_r21),
        "SKIP_R29C": bool_text(args.skip_r29c),
        "R30B_STATUS": "",
        "R28A_STATUS": "",
        "R28B_STATUS": "",
        "R21_STATUS": "",
        "R21_SIGNAL_DATE": norm(freeze.get("signal_date")),
        "R21_RUN_ID": norm(freeze.get("run_id")),
        "R21_FROZEN_ROW_COUNT": norm(freeze.get("ticker_count")),
        "R21_DUPLICATE_SIGNAL_DATE_TICKER_COUNT": norm(freeze.get("duplicate_signal_date_ticker_count")),
        "R21_MODE": "",
        "R29C_ACTION": "",
        "R29C_STATUS": "",
        "R29C_SNAPSHOT_DATE": "",
        "R29C_APPENDED_ROWS": "",
        "R30A_STATUS": "",
        "FINAL_OPERATOR_ACTION": "",
        "CURRENT_RANKED_CANDIDATE_ROWS": counts["candidates"],
        "CURRENT_THEME_CLASSIFICATION_ROWS": counts["themes"],
        "CURRENT_RECOMMENDATION_ROWS": counts["recommendations"],
        "LATEST_FULL_FREEZE_TICKER_COUNT": freeze.get("ticker_count", 0),
        "LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT": snapshot_count_for_date(root, norm(freeze.get("signal_date"))),
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "VALIDATION_FAIL_COUNT": 0,
        "FORBIDDEN_MODIFIED": "FALSE",
        "NEXT_RECOMMENDED_STEP": "",
        "FAILED_STEP": "",
        "FAILED_REASON": "",
        "FAILED_COMMAND": "",
        "ERROR_REPORT_PATH": "",
    }

    missing = validate_wrappers(root)
    if missing:
        reason = "Missing required wrappers: " + "; ".join(missing)
        fail_values(values, "VALIDATE_WRAPPERS", reason, "")
        write_outputs(root, values, summary_rows)
        write_text(root / OUT_ERROR_REPORT, f"# V18.30E Safe Daily Operator Sequence Error\n\n```text\n{reason}\n```\n")
        return 1, values

    r28a_rel = r28a_wrapper(root)
    if args.dry_run:
        add_planned_step(root, run_id, summary_rows, 1, "R30B guard", R30B_WRAPPER, R30B_READ_FIRST)
        add_planned_step(root, run_id, summary_rows, 2, "R28A theme classification", r28a_rel, R28A_READ_FIRST)
        add_planned_step(root, run_id, summary_rows, 3, "R28B recommendation tier refresh", R28B_WRAPPER, R28B_READ_FIRST)
        if not args.skip_r21:
            add_planned_step(root, run_id, summary_rows, 4, "R21 daily signal freeze", R21_WRAPPER, R21_READ_FIRST, ["-TopN", str(args.top_n)])
        if not args.skip_r29c:
            add_planned_step(root, run_id, summary_rows, 5, "R29C daily recommendation snapshot", R29C_WRAPPER, R29C_READ_FIRST)
        add_planned_step(root, run_id, summary_rows, 6, "R30A operator control center", R30A_WRAPPER, R30A_READ_FIRST)
        values["STATUS"] = STATUS_DRY
        values["R29C_ACTION"] = "PLANNED_DECIDE_AT_RUNTIME"
        values["FINAL_OPERATOR_ACTION"] = "DRY_RUN_NO_CHILD_SCRIPTS_EXECUTED"
        values["NEXT_RECOMMENDED_STEP"] = "Run live R30E after reviewing planned sequence."
        write_outputs(root, values, summary_rows)
        return 0, values

    failure: Optional[Tuple[str, str, str]] = None
    try:
        proc, rf, step = run_step(root, run_id, summary_rows, 1, "R30B guard", R30B_WRAPPER, R30B_READ_FIRST)
        values["R30B_STATUS"] = rf.get("STATUS", "")
        if proc.returncode != 0 or not is_ok(values["R30B_STATUS"]):
            failure = ("R30B guard", "FAIL_V18_30E_PRECHECK_GUARD_FAILED", step["command"])
            raise RuntimeError(failure[1])

        proc, rf, step = run_step(root, run_id, summary_rows, 2, "R28A theme classification", r28a_rel, R28A_READ_FIRST)
        values["R28A_STATUS"] = rf.get("STATUS", "")
        if proc.returncode != 0 or not is_ok(values["R28A_STATUS"]):
            failure = ("R28A theme classification", "FAIL_V18_30E_THEME_CLASSIFICATION_FAILED", step["command"])
            raise RuntimeError(failure[1])

        proc, rf, step = run_step(root, run_id, summary_rows, 3, "R28B recommendation tier refresh", R28B_WRAPPER, R28B_READ_FIRST)
        values["R28B_STATUS"] = rf.get("STATUS", "")
        if proc.returncode != 0 or not is_ok(values["R28B_STATUS"]):
            failure = ("R28B recommendation tier refresh", "FAIL_V18_30E_RECOMMENDATION_TIER_FAILED", step["command"])
            raise RuntimeError(failure[1])

        if args.skip_r21:
            values["R21_STATUS"] = "SKIPPED_BY_OPERATOR_FLAG"
            summary_rows.append({
                "run_id": run_id, "step_order": 4, "step_name": "R21 daily signal freeze",
                "command": "", "started_at": "", "ended_at": "", "duration_seconds": "", "exit_code": "",
                "read_first_path": str(root / R21_READ_FIRST), "parsed_status": values["R21_STATUS"],
                "required_status": "OK", "action": "SKIPPED_BY_OPERATOR_FLAG", "is_critical": "TRUE",
                "continue_allowed": "TRUE", "result": "SKIPPED", "notes": "",
            })
            freeze = latest_freeze(root)
        else:
            proc, rf, step = run_step(root, run_id, summary_rows, 4, "R21 daily signal freeze", R21_WRAPPER, R21_READ_FIRST, extra_args=["-TopN", str(args.top_n)])
            values["R21_STATUS"] = rf.get("STATUS", "")
            values["R21_SIGNAL_DATE"] = rf.get("SIGNAL_DATE", "")
            values["R21_RUN_ID"] = rf.get("RUN_ID", "")
            values["R21_FROZEN_ROW_COUNT"] = rf.get("FROZEN_ROW_COUNT", "")
            values["R21_DUPLICATE_SIGNAL_DATE_TICKER_COUNT"] = rf.get("DUPLICATE_SIGNAL_DATE_TICKER_COUNT_AFTER", "")
            values["R21_MODE"] = rf.get("MODE", "")
            if proc.returncode != 0 or (not is_ok(values["R21_STATUS"]) and not expected_r21_replace_warn(rf, args.top_n)):
                failure = ("R21 daily signal freeze", "FAIL_V18_30E_SIGNAL_FREEZE_FAILED", step["command"])
                raise RuntimeError(failure[1])
            if expected_r21_replace_warn(rf, args.top_n):
                step["continue_allowed"] = "TRUE"
                step["result"] = "WARN_ACCEPTED"
                step["notes"] = "Expected R21 same-day replace WARN; 252 rows frozen and duplicate signal_date+ticker count is zero."
            freeze = latest_freeze(root)

        signal_date = norm(values.get("R21_SIGNAL_DATE")) or norm(freeze.get("signal_date"))
        if not signal_date:
            signal_date = dt.date.today().isoformat()
        values["R21_SIGNAL_DATE"] = signal_date
        values["LATEST_FULL_FREEZE_TICKER_COUNT"] = freeze.get("ticker_count", 0)

        if args.skip_r29c:
            values["R29C_ACTION"] = "SKIPPED_BY_OPERATOR_FLAG"
            values["R29C_STATUS"] = "SKIPPED_BY_OPERATOR_FLAG"
            summary_rows.append({
                "run_id": run_id, "step_order": 5, "step_name": "R29C daily recommendation snapshot",
                "command": "", "started_at": "", "ended_at": "", "duration_seconds": "", "exit_code": "",
                "read_first_path": str(root / R29C_READ_FIRST), "parsed_status": values["R29C_STATUS"],
                "required_status": "OK", "action": values["R29C_ACTION"], "is_critical": "TRUE",
                "continue_allowed": "TRUE", "result": "SKIPPED", "notes": "",
            })
        else:
            existing_snapshot_rows = snapshot_count_for_date(root, signal_date)
            if existing_snapshot_rows == EXPECTED_ROWS and not args.force_snapshot:
                values["R29C_ACTION"] = "SKIPPED_EXISTING_SIGNAL_DATE_SNAPSHOT"
                values["R29C_STATUS"] = "SKIPPED_EXISTING_SIGNAL_DATE_SNAPSHOT"
                values["R29C_SNAPSHOT_DATE"] = signal_date
                values["R29C_APPENDED_ROWS"] = "0"
                summary_rows.append({
                    "run_id": run_id, "step_order": 5, "step_name": "R29C daily recommendation snapshot",
                    "command": cmd_text(command_for(root, R29C_WRAPPER)), "started_at": "", "ended_at": "",
                    "duration_seconds": "", "exit_code": "", "read_first_path": str(root / R29C_READ_FIRST),
                    "parsed_status": values["R29C_STATUS"], "required_status": "OK",
                    "action": values["R29C_ACTION"], "is_critical": "TRUE", "continue_allowed": "TRUE",
                    "result": "SKIPPED", "notes": f"{signal_date} already has {existing_snapshot_rows} rows",
                })
            else:
                values["R29C_ACTION"] = "EXECUTED"
                proc, rf, step = run_step(root, run_id, summary_rows, 5, "R29C daily recommendation snapshot", R29C_WRAPPER, R29C_READ_FIRST)
                values["R29C_STATUS"] = rf.get("STATUS", "")
                values["R29C_SNAPSHOT_DATE"] = rf.get("SNAPSHOT_DATE", "")
                values["R29C_APPENDED_ROWS"] = rf.get("APPENDED_ROWS", "")
                if proc.returncode != 0 or not is_ok(values["R29C_STATUS"]):
                    failure = ("R29C daily recommendation snapshot", "FAIL_V18_30E_RECOMMENDATION_SNAPSHOT_FAILED", step["command"])
                    raise RuntimeError(failure[1])

        proc, rf, step = run_step(root, run_id, summary_rows, 6, "R30A operator control center", R30A_WRAPPER, R30A_READ_FIRST, required_status="OK_OR_EXPECTED_WARN")
        values["R30A_STATUS"] = rf.get("STATUS", "")
        values["FINAL_OPERATOR_ACTION"] = rf.get("CURRENT_OPERATOR_ACTION", "")
        values["CURRENT_RANKED_CANDIDATE_ROWS"] = to_int(rf.get("CURRENT_RANKED_CANDIDATE_ROW_COUNT"))
        values["CURRENT_THEME_CLASSIFICATION_ROWS"] = to_int(rf.get("THEME_CLASSIFICATION_ROW_COUNT"))
        values["CURRENT_RECOMMENDATION_ROWS"] = to_int(rf.get("CURRENT_RECOMMENDATION_ROW_COUNT"))
        values["LATEST_FULL_FREEZE_TICKER_COUNT"] = to_int(rf.get("LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT"))
        values["LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT"] = to_int(rf.get("LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT"))
        values["AUTO_TRADE"] = rf.get("AUTO_TRADE", "DISABLED")
        values["AUTO_SELL"] = rf.get("AUTO_SELL", "DISABLED")
        values["OFFICIAL_DECISION_IMPACT"] = rf.get("OFFICIAL_DECISION_IMPACT", "NONE")
        values["FORBIDDEN_MODIFIED"] = rf.get("FORBIDDEN_MODIFIED", "FALSE")

        if proc.returncode != 0 or values["R30A_STATUS"].startswith("FAIL_"):
            failure = ("R30A operator control center", "FAIL_V18_30E_OPERATOR_CONTROL_CENTER_FAILED", step["command"])
            raise RuntimeError(failure[1])
        if is_warn(values["R30A_STATUS"]):
            if not args.allow_r30a_warn or args.stop_on_warn or not expected_r30a_warn_only(rf):
                failure = ("R30A operator control center", "FAIL_V18_30E_OPERATOR_CONTROL_CENTER_FAILED", step["command"])
                raise RuntimeError(failure[1])
            values["STATUS"] = STATUS_WARN
            values["NEXT_RECOMMENDED_STEP"] = "Read V18_CURRENT_OPERATOR_CONTROL_CENTER.md; manual review only until forward-return fillability is available."
            step["continue_allowed"] = "TRUE"
            step["result"] = "WARN_ACCEPTED"
            step["notes"] = "Expected R30A WARN: forward return fillable counts remain zero."
        else:
            values["STATUS"] = STATUS_OK
            values["NEXT_RECOMMENDED_STEP"] = "Read V18_CURRENT_OPERATOR_CONTROL_CENTER.md."

        write_outputs(root, values, summary_rows)
        return (0 if values["STATUS"] in {STATUS_OK, STATUS_WARN} else 1), values
    except Exception as exc:
        if failure is None:
            failure = ("R30E sequence", str(exc), "")
        fail_values(values, failure[0], failure[1], failure[2])
        write_outputs(root, values, summary_rows)
        write_text(root / OUT_ERROR_REPORT, f"# V18.30E Safe Daily Operator Sequence Error\n\n```text\n{failure[0]}\n{failure[1]}\n\n{traceback.format_exc()}\n```\n")
        return 1, values


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.30E safe daily operator sequence.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--top-n", type=int, default=252)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force-snapshot", action="store_true")
    parser.add_argument("--skip-r21", action="store_true")
    parser.add_argument("--skip-r29c", action="store_true")
    parser.add_argument("--allow-r30a-warn", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--stop-on-warn", action="store_true")
    parser.add_argument("--no-open", action="store_true", help="Compatibility flag; no files are opened by this script.")
    args = parser.parse_args()
    root = resolve_root(args.root)
    code, values = run(root, args)
    print(f"STATUS: {values.get('STATUS', '')}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
