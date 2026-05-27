from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R27B_MATURE_PARTIAL_POLICY_REVIEW_READY"
STATUS_WARN = "WARN_V18_25A_R27B_PLAN_WARNINGS"
STATUS_FAIL_INPUTS = "FAIL_V18_25A_R27B_REQUIRED_INPUTS_MISSING_OR_UNREADABLE"
STATUS_FAIL_FORBIDDEN = "FAIL_V18_25A_R27B_FORBIDDEN_PATH_MODIFIED"

MODE = "READ_ONLY_PLAN_ONLY_MATURE_PARTIAL_POLICY_REVIEW_EMPTY_FETCH_SYMBOL_AUDIT"

R27A_READ_FIRST = "outputs/v18/ops/V18_25A_R27A_READ_FIRST.txt"
R27A_STATUS_EXPECTED = "OK_V18_25A_R27A_PARTIAL_HISTORY_MATURITY_RECHECK_READY"

LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
R27A_AUDIT = "outputs/v18/coverage_resolution/V18_25A_R27A_CURRENT_REMAINING_COVERAGE_RESOLUTION_AUDIT.csv"
R27A_MATURE = "outputs/v18/coverage_resolution/V18_25A_R27A_CURRENT_PARTIAL_MATURE_REVIEW_CANDIDATES.csv"
R27A_NEAR = "outputs/v18/coverage_resolution/V18_25A_R27A_CURRENT_PARTIAL_NEAR_MATURE_WATCH.csv"
R27A_CONTINUE = "outputs/v18/coverage_resolution/V18_25A_R27A_CURRENT_PARTIAL_CONTINUE_HOLD.csv"
R27A_EMPTY = "outputs/v18/coverage_resolution/V18_25A_R27A_CURRENT_EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT.csv"

OUT_DIR = "outputs/v18/coverage_resolution"
OUT_MATURE_POLICY = f"{OUT_DIR}/V18_25A_R27B_CURRENT_MATURE_PARTIAL_POLICY_REVIEW.csv"
OUT_R27C_DRYRUN = f"{OUT_DIR}/V18_25A_R27B_CURRENT_R27C_DRYRUN_CANDIDATES.csv"
OUT_NEAR = f"{OUT_DIR}/V18_25A_R27B_CURRENT_NEAR_MATURE_WATCH.csv"
OUT_CONTINUE = f"{OUT_DIR}/V18_25A_R27B_CURRENT_CONTINUE_PARTIAL_HOLD.csv"
OUT_EMPTY_PLAN = f"{OUT_DIR}/V18_25A_R27B_CURRENT_EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT_PLAN.csv"
OUT_SUMMARY = f"{OUT_DIR}/V18_25A_R27B_CURRENT_SUMMARY.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R27B_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R27B_CURRENT_MATURE_PARTIAL_POLICY_REVIEW_REPORT.md"

EXPECTED_TOTAL_LEDGER_ROWS = 323
EXPECTED_ARTIFACT_COUNT = 0
EXPECTED_CURRENT_NEVER_SUCCESS = 22
EXPECTED_MATURE_INPUT_COUNT = 2
EXPECTED_MATURE_PASS_COUNT = 2
EXPECTED_R27C_DRYRUN_COUNT = 2
EXPECTED_NEAR_COUNT = 2
EXPECTED_CONTINUE_COUNT = 13
EXPECTED_EMPTY_COUNT = 5

MATURE_POLICY_FIELDS = [
    "ticker",
    "row_count",
    "min_date",
    "max_date",
    "latest_close",
    "latest_volume",
    "data_quality_pass",
    "maturity_bucket",
    "policy_review_status",
    "recommended_next_action",
]

R27C_FIELDS = [
    "ticker",
    "row_count",
    "min_date",
    "max_date",
    "latest_close",
    "latest_volume",
    "data_quality_pass",
    "maturity_bucket",
    "policy_review_status",
    "recommended_next_action",
]

NEAR_FIELDS = [
    "ticker",
    "row_count",
    "min_date",
    "max_date",
    "latest_close",
    "latest_volume",
    "recommended_next_action",
]

CONTINUE_FIELDS = [
    "ticker",
    "row_count",
    "min_date",
    "max_date",
    "latest_close",
    "latest_volume",
    "recommended_next_action",
]

EMPTY_PLAN_FIELDS = [
    "ticker",
    "last_known_quality_status",
    "recommended_symbol_audit_status",
    "recommended_next_action",
]

SUMMARY_FIELDS = ["metric", "value", "expected", "status", "notes"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R27A_STATUS",
    "TOTAL_LEDGER_ROWS",
    "ARTIFACT_TICKERS_PRESENT_COUNT",
    "CURRENT_NEVER_SUCCESS_COUNT",
    "MATURE_PARTIAL_REVIEW_INPUT_COUNT",
    "MATURE_PARTIAL_POLICY_REVIEW_PASS_COUNT",
    "R27C_DRYRUN_CANDIDATE_COUNT",
    "NEAR_MATURE_WATCH_COUNT",
    "CONTINUE_PARTIAL_HOLD_COUNT",
    "EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT_COUNT",
    "OFFICIAL_INTEGRATION_ALLOWED_NEXT",
    "R27C_CONTROLLED_DRYRUN_RECOMMENDED",
    "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "CANDIDATES_MODIFIED",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except Exception:
            continue
    return ""


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def norm_bool(value: object) -> bool:
    return str(value or "").strip().upper() == "TRUE"


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def non_null(value: object) -> bool:
    return str(value or "").strip() not in {"", "nan", "NaN", "None", "NULL"}


def parse_date(value: object) -> Optional[dt.date]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return dt.datetime.strptime(text[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def get_field(row: Dict[str, str], *names: str) -> str:
    for name in names:
        if name in row and str(row.get(name, "")).strip() != "":
            return str(row.get(name, ""))
    return ""


def has_clean_data_quality(row: Dict[str, str]) -> bool:
    def optional_true(field: str) -> bool:
        value = get_field(row, field)
        return True if value == "" else norm_bool(value)

    def optional_zero(field: str) -> bool:
        value = get_field(row, field)
        return True if value == "" else to_int(value) == 0

    return (
        optional_true("file_exists")
        and optional_true("readable")
        and optional_true("required_columns_present")
        and optional_true("date_parse_ok")
        and optional_zero("duplicate_date_count")
        and optional_zero("null_close_count")
        and non_null(get_field(row, "latest_close"))
        and non_null(get_field(row, "latest_volume"))
    )


def load_required_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], Optional[str]]:
    rows, fields = read_csv(path)
    if not path.exists():
        return rows, fields, "missing"
    if not fields and path.stat().st_size > 0:
        return rows, fields, "unreadable"
    return rows, fields, None


def load_optional_status(path: Path) -> str:
    text = read_text(path)
    for line in text.splitlines():
        if line.startswith("STATUS:"):
            return line.split(":", 1)[1].strip()
    return ""


def parse_current_ledger(ledger_rows: List[Dict[str, str]], run_date: dt.date) -> Dict[str, object]:
    artifact_count = 0
    never_success = 0
    for row in ledger_rows:
        ticker = norm_ticker(get_field(row, "ticker"))
        if ticker == "TICKERS":
            artifact_count += 1
        success_count = to_int(get_field(row, "success_scan_count"))
        success_date = parse_date(get_field(row, "last_success_scan_date"))
        if success_count <= 0 or success_date is None:
            never_success += 1
    return {
        "total": len(ledger_rows),
        "artifact_count": artifact_count,
        "never_success": never_success,
    }


def row_to_policy_review(row: Dict[str, str]) -> Dict[str, object]:
    ticker = norm_ticker(get_field(row, "ticker"))
    row_count = to_int(get_field(row, "row_count"))
    data_quality_pass = row_count >= 500 and has_clean_data_quality(row)
    policy_review_status = "PARTIAL_MATURE_POLICY_REVIEW_PASS" if data_quality_pass else "PARTIAL_MATURE_POLICY_REVIEW_REVIEW"
    recommended_next_action = (
        "R27C_CONTROLLED_PARTIAL_MATURE_INTEGRATION_DRYRUN_RECOMMENDED"
        if data_quality_pass
        else "CONTINUE_PARTIAL_MATURE_POLICY_REVIEW"
    )
    return {
        "ticker": ticker,
        "row_count": row_count,
        "min_date": get_field(row, "min_date"),
        "max_date": get_field(row, "max_date"),
        "latest_close": get_field(row, "latest_close"),
        "latest_volume": get_field(row, "latest_volume"),
        "data_quality_pass": str(data_quality_pass).upper(),
        "maturity_bucket": get_field(row, "manual_review_tier") or "MATURE_PARTIAL",
        "policy_review_status": policy_review_status,
        "recommended_next_action": recommended_next_action,
    }


def row_to_near_watch(row: Dict[str, str]) -> Dict[str, object]:
    return {
        "ticker": norm_ticker(get_field(row, "ticker")),
        "row_count": to_int(get_field(row, "row_count")),
        "min_date": get_field(row, "min_date"),
        "max_date": get_field(row, "max_date"),
        "latest_close": get_field(row, "latest_close"),
        "latest_volume": get_field(row, "latest_volume"),
        "recommended_next_action": "CONTINUE_NEAR_MATURE_WATCH_RECHECK_LATER",
    }


def row_to_continue_hold(row: Dict[str, str]) -> Dict[str, object]:
    return {
        "ticker": norm_ticker(get_field(row, "ticker")),
        "row_count": to_int(get_field(row, "row_count")),
        "min_date": get_field(row, "min_date"),
        "max_date": get_field(row, "max_date"),
        "latest_close": get_field(row, "latest_close"),
        "latest_volume": get_field(row, "latest_volume"),
        "recommended_next_action": "CONTINUE_PARTIAL_HISTORY_HOLD",
    }


def row_to_empty_plan(row: Dict[str, str]) -> Dict[str, object]:
    return {
        "ticker": norm_ticker(get_field(row, "ticker")),
        "last_known_quality_status": get_field(row, "quality_status"),
        "recommended_symbol_audit_status": "SYMBOL_PROVIDER_AUDIT_REQUIRED_BEFORE_RETRY",
        "recommended_next_action": "SYMBOL_PROVIDER_AUDIT_REQUIRED_BEFORE_RETRY",
    }


def metric_row(metric: str, value: object, expected: object, notes: str = "") -> Dict[str, object]:
    return {
        "metric": metric,
        "value": value,
        "expected": expected,
        "status": "OK" if str(value) == str(expected) else "WARN",
        "notes": notes,
    }


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object], warnings: List[str]) -> str:
    warning_block = "\n".join(f"- {line}" for line in warnings) if warnings else "- None."
    return "\n".join(
        [
            "# V18.25A-R27B Mature Partial Policy Review + Empty-Fetch Symbol Provider Audit Plan",
            "",
            f"- STATUS: {values['STATUS']}",
            f"- MODE: {values['MODE']}",
            f"- RUN_ID: {values['RUN_ID']}",
            f"- R27A_STATUS: {values['R27A_STATUS']}",
            "",
            "## Counts",
            "",
            f"- TOTAL_LEDGER_ROWS: {values['TOTAL_LEDGER_ROWS']}",
            f"- ARTIFACT_TICKERS_PRESENT_COUNT: {values['ARTIFACT_TICKERS_PRESENT_COUNT']}",
            f"- CURRENT_NEVER_SUCCESS_COUNT: {values['CURRENT_NEVER_SUCCESS_COUNT']}",
            f"- MATURE_PARTIAL_REVIEW_INPUT_COUNT: {values['MATURE_PARTIAL_REVIEW_INPUT_COUNT']}",
            f"- MATURE_PARTIAL_POLICY_REVIEW_PASS_COUNT: {values['MATURE_PARTIAL_POLICY_REVIEW_PASS_COUNT']}",
            f"- R27C_DRYRUN_CANDIDATE_COUNT: {values['R27C_DRYRUN_CANDIDATE_COUNT']}",
            f"- NEAR_MATURE_WATCH_COUNT: {values['NEAR_MATURE_WATCH_COUNT']}",
            f"- CONTINUE_PARTIAL_HOLD_COUNT: {values['CONTINUE_PARTIAL_HOLD_COUNT']}",
            f"- EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT_COUNT: {values['EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT_COUNT']}",
            "",
            "## Warnings",
            "",
            warning_block,
            "",
            "## Guardrails",
            "",
            f"- OFFICIAL_INTEGRATION_ALLOWED_NEXT: {values['OFFICIAL_INTEGRATION_ALLOWED_NEXT']}",
            f"- R27C_CONTROLLED_DRYRUN_RECOMMENDED: {values['R27C_CONTROLLED_DRYRUN_RECOMMENDED']}",
            f"- PRICE_CACHE_MODIFIED: {values['PRICE_CACHE_MODIFIED']}",
            f"- ROLLING_LEDGER_MODIFIED: {values['ROLLING_LEDGER_MODIFIED']}",
            f"- FACTOR_PACK_MODIFIED: {values['FACTOR_PACK_MODIFIED']}",
            f"- TECHNICAL_TIMING_MODIFIED: {values['TECHNICAL_TIMING_MODIFIED']}",
            f"- CANDIDATES_MODIFIED: {values['CANDIDATES_MODIFIED']}",
            f"- EXTERNAL_FETCH_EXECUTED: {values['EXTERNAL_FETCH_EXECUTED']}",
            f"- BACKTEST_EXECUTED: {values['BACKTEST_EXECUTED']}",
            f"- OFFICIAL_DECISION_IMPACT: {values['OFFICIAL_DECISION_IMPACT']}",
            f"- AUTO_TRADE: {values['AUTO_TRADE']}",
            f"- AUTO_SELL: {values['AUTO_SELL']}",
            f"- FORBIDDEN_MODIFIED: {values['FORBIDDEN_MODIFIED']}",
            "",
            f"NEXT_RECOMMENDED_STEP: {values['NEXT_RECOMMENDED_STEP']}",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R27B_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_date = dt.date.today()

    price_before = tree_sig(root / "state" / "v18" / "price_cache")
    ledger_before = file_sig(root / LEDGER)
    factor_before = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_before = tree_sig(root / "outputs" / "v18" / "technical_timing")
    candidates_before = tree_sig(root / "outputs" / "v18" / "candidates")

    required_specs = [
        (root / R27A_AUDIT, "R27A audit"),
        (root / R27A_MATURE, "R27A mature"),
        (root / R27A_NEAR, "R27A near"),
        (root / R27A_CONTINUE, "R27A continue"),
        (root / R27A_EMPTY, "R27A empty"),
        (root / LEDGER, "rolling ledger"),
    ]
    required_errors = []
    for path, label in required_specs:
        if not path.exists():
            required_errors.append(f"{label} missing: {path}")

    audit_rows, _, audit_err = load_required_csv(root / R27A_AUDIT)
    mature_rows, _, mature_err = load_required_csv(root / R27A_MATURE)
    near_rows, _, near_err = load_required_csv(root / R27A_NEAR)
    continue_rows, _, continue_err = load_required_csv(root / R27A_CONTINUE)
    empty_rows, _, empty_err = load_required_csv(root / R27A_EMPTY)
    ledger_rows, _, ledger_err = load_required_csv(root / LEDGER)
    r27a_status = load_optional_status(root / R27A_READ_FIRST)

    if audit_err:
        required_errors.append(f"R27A audit {audit_err}")
    if mature_err:
        required_errors.append(f"R27A mature {mature_err}")
    if near_err:
        required_errors.append(f"R27A near {near_err}")
    if continue_err:
        required_errors.append(f"R27A continue {continue_err}")
    if empty_err:
        required_errors.append(f"R27A empty {empty_err}")
    if ledger_err:
        required_errors.append(f"rolling ledger {ledger_err}")

    r27a_audit_by_ticker = {norm_ticker(get_field(row, "ticker")): row for row in audit_rows}
    mature_policy_rows = [row_to_policy_review(row) for row in mature_rows]
    r27c_rows = [row for row in mature_policy_rows if row["policy_review_status"] == "PARTIAL_MATURE_POLICY_REVIEW_PASS"]
    near_plan_rows = [row_to_near_watch(row) for row in near_rows]
    continue_plan_rows = [row_to_continue_hold(row) for row in continue_rows]
    empty_plan_rows = [row_to_empty_plan(row) for row in empty_rows]

    current_counts = parse_current_ledger(ledger_rows, run_date)

    warnings: List[str] = []
    if r27a_status and r27a_status != R27A_STATUS_EXPECTED:
        warnings.append(f"R27A status is {r27a_status}, expected {R27A_STATUS_EXPECTED}.")
    if not r27a_status:
        warnings.append("R27A status line was not available in read_first.")
    if current_counts["total"] != EXPECTED_TOTAL_LEDGER_ROWS:
        warnings.append(
            f"ledger rows changed to {current_counts['total']} from expected {EXPECTED_TOTAL_LEDGER_ROWS}."
        )
    if current_counts["artifact_count"] != EXPECTED_ARTIFACT_COUNT:
        warnings.append(f"artifact ticker count is {current_counts['artifact_count']} not {EXPECTED_ARTIFACT_COUNT}.")
    if current_counts["never_success"] != EXPECTED_CURRENT_NEVER_SUCCESS:
        warnings.append(
            f"current never-success count is {current_counts['never_success']} not {EXPECTED_CURRENT_NEVER_SUCCESS}."
        )
    if len(mature_rows) != EXPECTED_MATURE_INPUT_COUNT:
        warnings.append(f"mature partial input count is {len(mature_rows)} not {EXPECTED_MATURE_INPUT_COUNT}.")
    if len(r27c_rows) != EXPECTED_R27C_DRYRUN_COUNT:
        warnings.append(f"dryrun candidate count is {len(r27c_rows)} not {EXPECTED_R27C_DRYRUN_COUNT}.")
    if len(near_rows) != EXPECTED_NEAR_COUNT:
        warnings.append(f"near mature watch count is {len(near_rows)} not {EXPECTED_NEAR_COUNT}.")
    if len(continue_rows) != EXPECTED_CONTINUE_COUNT:
        warnings.append(f"continue partial hold count is {len(continue_rows)} not {EXPECTED_CONTINUE_COUNT}.")
    if len(empty_rows) != EXPECTED_EMPTY_COUNT:
        warnings.append(
            f"empty-fetch symbol-provider audit count is {len(empty_rows)} not {EXPECTED_EMPTY_COUNT}."
        )

    status = STATUS_OK
    validation_fail_count = 0
    if required_errors:
        status = STATUS_FAIL_INPUTS
        validation_fail_count = 1

    write_csv(root / OUT_MATURE_POLICY, mature_policy_rows, MATURE_POLICY_FIELDS)
    write_csv(root / OUT_R27C_DRYRUN, r27c_rows, R27C_FIELDS)
    write_csv(root / OUT_NEAR, near_plan_rows, NEAR_FIELDS)
    write_csv(root / OUT_CONTINUE, continue_plan_rows, CONTINUE_FIELDS)
    write_csv(root / OUT_EMPTY_PLAN, empty_plan_rows, EMPTY_PLAN_FIELDS)

    summary_rows = [
        metric_row("R27A_STATUS", r27a_status or "MISSING", R27A_STATUS_EXPECTED),
        metric_row("TOTAL_LEDGER_ROWS", current_counts["total"], EXPECTED_TOTAL_LEDGER_ROWS),
        metric_row("ARTIFACT_TICKERS_PRESENT_COUNT", current_counts["artifact_count"], EXPECTED_ARTIFACT_COUNT),
        metric_row("CURRENT_NEVER_SUCCESS_COUNT", current_counts["never_success"], EXPECTED_CURRENT_NEVER_SUCCESS),
        metric_row("MATURE_PARTIAL_REVIEW_INPUT_COUNT", len(mature_rows), EXPECTED_MATURE_INPUT_COUNT),
        metric_row(
            "MATURE_PARTIAL_POLICY_REVIEW_PASS_COUNT",
            len(r27c_rows),
            EXPECTED_MATURE_PASS_COUNT,
        ),
        metric_row("R27C_DRYRUN_CANDIDATE_COUNT", len(r27c_rows), EXPECTED_R27C_DRYRUN_COUNT),
        metric_row("NEAR_MATURE_WATCH_COUNT", len(near_rows), EXPECTED_NEAR_COUNT),
        metric_row("CONTINUE_PARTIAL_HOLD_COUNT", len(continue_rows), EXPECTED_CONTINUE_COUNT),
        metric_row(
            "EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT_COUNT",
            len(empty_rows),
            EXPECTED_EMPTY_COUNT,
        ),
    ]
    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    price_modified = tree_sig(root / "state" / "v18" / "price_cache") != price_before
    ledger_modified = file_sig(root / LEDGER) != ledger_before
    factor_modified = tree_sig(root / "outputs" / "v18" / "factor_pack") != factor_before
    tech_modified = tree_sig(root / "outputs" / "v18" / "technical_timing") != tech_before
    candidates_modified = tree_sig(root / "outputs" / "v18" / "candidates") != candidates_before
    forbidden_modified = price_modified or ledger_modified or factor_modified or tech_modified or candidates_modified
    if forbidden_modified:
        status = STATUS_FAIL_FORBIDDEN
        validation_fail_count = max(validation_fail_count, 1)

    if status == STATUS_OK and warnings:
        status = STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R27A_STATUS": r27a_status or "MISSING",
        "TOTAL_LEDGER_ROWS": current_counts["total"],
        "ARTIFACT_TICKERS_PRESENT_COUNT": current_counts["artifact_count"],
        "CURRENT_NEVER_SUCCESS_COUNT": current_counts["never_success"],
        "MATURE_PARTIAL_REVIEW_INPUT_COUNT": len(mature_rows),
        "MATURE_PARTIAL_POLICY_REVIEW_PASS_COUNT": len(r27c_rows),
        "R27C_DRYRUN_CANDIDATE_COUNT": len(r27c_rows),
        "NEAR_MATURE_WATCH_COUNT": len(near_rows),
        "CONTINUE_PARTIAL_HOLD_COUNT": len(continue_rows),
        "EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT_COUNT": len(empty_rows),
        "OFFICIAL_INTEGRATION_ALLOWED_NEXT": "FALSE",
        "R27C_CONTROLLED_DRYRUN_RECOMMENDED": "TRUE" if len(r27c_rows) > 0 else "FALSE",
        "PRICE_CACHE_MODIFIED": str(price_modified).upper(),
        "ROLLING_LEDGER_MODIFIED": str(ledger_modified).upper(),
        "FACTOR_PACK_MODIFIED": str(factor_modified).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(tech_modified).upper(),
        "CANDIDATES_MODIFIED": str(candidates_modified).upper(),
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": (
            "R27C: prepare controlled partial mature integration dryrun for TLN/RDDT only; "
            "keep near-mature watch and empty-fetch symbol-provider audit plan-only; no official integration."
        ),
    }

    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, warnings))
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if validation_fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
