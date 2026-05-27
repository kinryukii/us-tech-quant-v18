from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R27A_PARTIAL_HISTORY_MATURITY_RECHECK_READY"
STATUS_WARN_ARTIFACT = "WARN_V18_25A_R27A_ARTIFACT_STILL_PRESENT"
STATUS_WARN_COUNT = "WARN_V18_25A_R27A_COUNT_DISCREPANCY"
STATUS_FAIL_INPUTS = "FAIL_V18_25A_R27A_REQUIRED_INPUTS_MISSING"
STATUS_FAIL_FORBIDDEN = "FAIL_V18_25A_R27A_FORBIDDEN_PATH_MODIFIED"

MODE = "READ_ONLY_PARTIAL_HISTORY_MATURITY_RECHECK_EMPTY_FETCH_AUDIT"

QUALITY_GATE = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_STAGED_QUALITY_GATE.csv"
PARTIAL_HOLDS = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_PARTIAL_HISTORY_HOLDS.csv"
EMPTY_HOLDS = "outputs/v18/staged_backfill/V18_25A_R23C_CURRENT_EMPTY_OR_FAILED_HOLDS.csv"
MANUAL_REVIEW = "outputs/v18/staged_backfill/V18_25A_R27A_MANUAL_PARTIAL_MATURITY_REVIEW_CANDIDATES.csv"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OUT_DIR = "outputs/v18/coverage_resolution"
OUT_AUDIT = f"{OUT_DIR}/V18_25A_R27A_CURRENT_REMAINING_COVERAGE_RESOLUTION_AUDIT.csv"
OUT_MATURE = f"{OUT_DIR}/V18_25A_R27A_CURRENT_PARTIAL_MATURE_REVIEW_CANDIDATES.csv"
OUT_NEAR = f"{OUT_DIR}/V18_25A_R27A_CURRENT_PARTIAL_NEAR_MATURE_WATCH.csv"
OUT_CONTINUE = f"{OUT_DIR}/V18_25A_R27A_CURRENT_PARTIAL_CONTINUE_HOLD.csv"
OUT_EMPTY = f"{OUT_DIR}/V18_25A_R27A_CURRENT_EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT.csv"
OUT_STATUS = f"{OUT_DIR}/V18_25A_R27A_CURRENT_COVERAGE_STATUS_AFTER_ARTIFACT_CLEANUP.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R27A_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R27A_CURRENT_PARTIAL_HISTORY_MATURITY_RECHECK_REPORT.md"

EXPECTED_TOTAL_LEDGER_ROWS = 323
EXPECTED_COVERED_WITHIN_5D = 301
EXPECTED_NEVER_SUCCESS_COUNT = 22
EXPECTED_STALE_COUNT = 0
EXPECTED_REMAINING_COUNT = 22
EXPECTED_PARTIAL_HOLD_COUNT = 17
EXPECTED_EMPTY_HOLD_COUNT = 5
EXPECTED_MATURE = {"TLN", "RDDT"}
EXPECTED_NEAR = {"LINE", "PONY"}
EXPECTED_EMPTY = {"CDTX", "CFLT", "COG", "JFROG", "MPW"}

OUTPUT_FIELDS = [
    "ticker",
    "resolution_bucket",
    "row_count",
    "min_date",
    "max_date",
    "latest_close",
    "latest_volume",
    "r23b_quality_status",
    "quality_status",
    "integration_candidate_status",
    "reason",
    "provider",
    "fetch_run_id",
    "rolling_last_scan_status",
    "rolling_last_attempt_scan_timestamp",
    "rolling_last_success_scan_date",
    "recommended_next_action",
]

STATUS_FIELDS = [
    "metric",
    "value",
    "expected",
    "status",
    "notes",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "TOTAL_LEDGER_ROWS",
    "COVERED_WITHIN_5D",
    "NEVER_SUCCESS_COUNT",
    "STALE_COUNT",
    "REMAINING_COUNT",
    "ARTIFACT_TICKERS_PRESENT_COUNT",
    "QUALITY_GATE_TOTAL_COUNT",
    "PARTIAL_HISTORY_HOLD_COUNT",
    "EMPTY_FETCH_HOLD_COUNT",
    "MATURE_REVIEW_PRIORITY_COUNT",
    "NEAR_MATURE_WATCH_COUNT",
    "CONTINUE_PARTIAL_HOLD_COUNT",
    "EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT_COUNT",
    "OFFICIAL_INTEGRATION_ALLOWED_NEXT",
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


def parse_date(value: object) -> Optional[dt.date]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return dt.datetime.strptime(text[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def non_null(value: object) -> bool:
    return str(value or "").strip() not in {"", "nan", "NaN", "None", "NULL"}


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def has_clean_partial_quality(row: Dict[str, str]) -> bool:
    return (
        norm_bool(row.get("file_exists"))
        and norm_bool(row.get("readable"))
        and norm_bool(row.get("required_columns_present"))
        and norm_bool(row.get("date_parse_ok"))
        and to_int(row.get("duplicate_date_count")) == 0
        and to_int(row.get("null_close_count")) == 0
        and non_null(row.get("latest_close"))
        and non_null(row.get("latest_volume"))
    )


def coverage_counts(ledger_rows: List[Dict[str, str]], run_date: dt.date) -> Dict[str, object]:
    artifact_count = sum(1 for row in ledger_rows if norm_ticker(row.get("ticker")) == "TICKERS")
    never_success = []
    stale = []
    covered = []
    for row in ledger_rows:
        ticker = norm_ticker(row.get("ticker"))
        success_count = to_int(row.get("success_scan_count"))
        success_date = parse_date(row.get("last_success_scan_date"))
        if success_count <= 0 or success_date is None:
            never_success.append(ticker)
            continue
        age_days = (run_date - success_date).days
        if 0 <= age_days <= 5:
            covered.append(ticker)
        else:
            stale.append(ticker)
    remaining = never_success + stale
    return {
        "total": len(ledger_rows),
        "covered": len(covered),
        "never_success": len(never_success),
        "stale": len(stale),
        "remaining": len(remaining),
        "artifact_count": artifact_count,
        "remaining_tickers": sorted(set(remaining)),
    }


def classify_row(row: Dict[str, str], empty_hold_tickers: set[str]) -> Tuple[str, str]:
    ticker = norm_ticker(row.get("ticker"))
    quality_status = str(row.get("quality_status") or "").strip()
    row_count = to_int(row.get("row_count"))
    clean = has_clean_partial_quality(row)

    if quality_status == "HELD_OUT_EMPTY_FETCH" or ticker in empty_hold_tickers:
        return (
            "EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT",
            "SYMBOL_PROVIDER_AUDIT_R27B_OR_PROVIDER_FALLBACK_RETRY",
        )
    if quality_status == "HELD_OUT_PARTIAL_HISTORY" and row_count >= 500 and clean:
        return (
            "PARTIAL_HISTORY_MATURE_REVIEW_PRIORITY",
            "REVIEW_FOR_PARTIAL_HISTORY_MATURE_POLICY_R27B_NO_AUTO_INTEGRATION",
        )
    if quality_status == "HELD_OUT_PARTIAL_HISTORY" and 300 <= row_count < 500 and clean:
        return (
            "PARTIAL_HISTORY_NEAR_MATURE_WATCH",
            "CONTINUE_NEAR_MATURE_WATCH_RECHECK_LATER",
        )
    if quality_status == "HELD_OUT_PARTIAL_HISTORY":
        return ("PARTIAL_HISTORY_CONTINUE_HOLD", "CONTINUE_PARTIAL_HISTORY_HOLD")
    return ("UNCLASSIFIED_REMAINING_COVERAGE_HOLD", "REVIEW_R27A_UNCLASSIFIED_REMAINING_TICKER")


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object], status_rows: List[Dict[str, object]], bucket_counts: Dict[str, int]) -> str:
    warnings = [row for row in status_rows if row.get("status") == "WARN"]
    warning_lines = "\n".join(
        f"- {row['metric']}: actual {row['value']} vs expected {row['expected']}."
        for row in warnings
    )
    if not warning_lines:
        warning_lines = "- None."
    return "\n".join(
        [
            "# V18.25A-R27A Partial-History Maturity Recheck + Empty-Fetch Audit",
            "",
            f"- STATUS: {values['STATUS']}",
            f"- MODE: {values['MODE']}",
            f"- RUN_ID: {values['RUN_ID']}",
            f"- OFFICIAL_DECISION_IMPACT: {values['OFFICIAL_DECISION_IMPACT']}",
            f"- OFFICIAL_INTEGRATION_ALLOWED_NEXT: {values['OFFICIAL_INTEGRATION_ALLOWED_NEXT']}",
            f"- AUTO_TRADE: {values['AUTO_TRADE']}",
            f"- AUTO_SELL: {values['AUTO_SELL']}",
            "",
            "## Coverage Snapshot",
            "",
            f"- TOTAL_LEDGER_ROWS: {values['TOTAL_LEDGER_ROWS']}",
            f"- COVERED_WITHIN_5D: {values['COVERED_WITHIN_5D']}",
            f"- NEVER_SUCCESS_COUNT: {values['NEVER_SUCCESS_COUNT']}",
            f"- STALE_COUNT: {values['STALE_COUNT']}",
            f"- REMAINING_COUNT: {values['REMAINING_COUNT']}",
            f"- ARTIFACT_TICKERS_PRESENT_COUNT: {values['ARTIFACT_TICKERS_PRESENT_COUNT']}",
            "",
            "## Resolution Buckets",
            "",
            f"- PARTIAL_HISTORY_MATURE_REVIEW_PRIORITY: {bucket_counts.get('PARTIAL_HISTORY_MATURE_REVIEW_PRIORITY', 0)}",
            f"- PARTIAL_HISTORY_NEAR_MATURE_WATCH: {bucket_counts.get('PARTIAL_HISTORY_NEAR_MATURE_WATCH', 0)}",
            f"- PARTIAL_HISTORY_CONTINUE_HOLD: {bucket_counts.get('PARTIAL_HISTORY_CONTINUE_HOLD', 0)}",
            f"- EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT: {bucket_counts.get('EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT', 0)}",
            "",
            "## Warnings",
            "",
            warning_lines,
            "",
            "## Guardrails",
            "",
            f"- PRICE_CACHE_MODIFIED: {values['PRICE_CACHE_MODIFIED']}",
            f"- ROLLING_LEDGER_MODIFIED: {values['ROLLING_LEDGER_MODIFIED']}",
            f"- FACTOR_PACK_MODIFIED: {values['FACTOR_PACK_MODIFIED']}",
            f"- TECHNICAL_TIMING_MODIFIED: {values['TECHNICAL_TIMING_MODIFIED']}",
            f"- CANDIDATES_MODIFIED: {values['CANDIDATES_MODIFIED']}",
            f"- EXTERNAL_FETCH_EXECUTED: {values['EXTERNAL_FETCH_EXECUTED']}",
            f"- BACKTEST_EXECUTED: {values['BACKTEST_EXECUTED']}",
            f"- FORBIDDEN_MODIFIED: {values['FORBIDDEN_MODIFIED']}",
            "",
            f"NEXT_RECOMMENDED_STEP: {values['NEXT_RECOMMENDED_STEP']}",
            "",
        ]
    )


def metric_row(metric: str, value: object, expected: object, notes: str = "") -> Dict[str, object]:
    return {
        "metric": metric,
        "value": value,
        "expected": expected,
        "status": "OK" if str(value) == str(expected) else "WARN",
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--run-date", default="")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R27A_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_date = parse_date(args.run_date) if args.run_date else dt.date.today()
    if run_date is None:
        run_date = dt.date.today()

    price_before = tree_sig(root / "state" / "v18" / "price_cache")
    ledger_before = file_sig(root / LEDGER)
    factor_before = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_before = tree_sig(root / "outputs" / "v18" / "technical_timing")
    candidates_before = tree_sig(root / "outputs" / "v18" / "candidates")

    required_paths = [root / QUALITY_GATE, root / PARTIAL_HOLDS, root / EMPTY_HOLDS, root / LEDGER]
    missing = [str(path) for path in required_paths if not path.exists()]
    gate_rows, _ = read_csv(root / QUALITY_GATE)
    partial_rows, _ = read_csv(root / PARTIAL_HOLDS)
    empty_rows, _ = read_csv(root / EMPTY_HOLDS)
    ledger_rows, _ = read_csv(root / LEDGER)
    manual_rows, _ = read_csv(root / MANUAL_REVIEW)

    counts = coverage_counts(ledger_rows, run_date)
    quality_by_ticker = {norm_ticker(row.get("ticker")): row for row in gate_rows}
    ledger_by_ticker = {norm_ticker(row.get("ticker")): row for row in ledger_rows}
    empty_hold_tickers = {norm_ticker(row.get("ticker")) for row in empty_rows}

    audit_rows: List[Dict[str, object]] = []
    for ticker in counts["remaining_tickers"]:
        gate = quality_by_ticker.get(ticker, {"ticker": ticker})
        ledger = ledger_by_ticker.get(ticker, {})
        bucket, action = classify_row(gate, empty_hold_tickers)
        audit_rows.append(
            {
                "ticker": ticker,
                "resolution_bucket": bucket,
                "row_count": gate.get("row_count", ""),
                "min_date": gate.get("min_date", ""),
                "max_date": gate.get("max_date", ""),
                "latest_close": gate.get("latest_close", ""),
                "latest_volume": gate.get("latest_volume", ""),
                "r23b_quality_status": gate.get("r23b_quality_status", ""),
                "quality_status": gate.get("quality_status", ""),
                "integration_candidate_status": gate.get("integration_candidate_status", ""),
                "reason": gate.get("reason", ""),
                "provider": gate.get("provider", ""),
                "fetch_run_id": gate.get("fetch_run_id", ""),
                "rolling_last_scan_status": ledger.get("last_scan_status", ""),
                "rolling_last_attempt_scan_timestamp": ledger.get("last_attempt_scan_timestamp", ""),
                "rolling_last_success_scan_date": ledger.get("last_success_scan_date", ""),
                "recommended_next_action": action,
            }
        )

    mature = [row for row in audit_rows if row["resolution_bucket"] == "PARTIAL_HISTORY_MATURE_REVIEW_PRIORITY"]
    near = [row for row in audit_rows if row["resolution_bucket"] == "PARTIAL_HISTORY_NEAR_MATURE_WATCH"]
    continue_hold = [row for row in audit_rows if row["resolution_bucket"] == "PARTIAL_HISTORY_CONTINUE_HOLD"]
    empty_audit = [row for row in audit_rows if row["resolution_bucket"] == "EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT"]
    bucket_counts: Dict[str, int] = {}
    for row in audit_rows:
        bucket_counts[str(row["resolution_bucket"])] = bucket_counts.get(str(row["resolution_bucket"]), 0) + 1

    status_rows = [
        metric_row("TOTAL_LEDGER_ROWS", counts["total"], EXPECTED_TOTAL_LEDGER_ROWS),
        metric_row("COVERED_WITHIN_5D", counts["covered"], EXPECTED_COVERED_WITHIN_5D),
        metric_row("NEVER_SUCCESS_COUNT", counts["never_success"], EXPECTED_NEVER_SUCCESS_COUNT),
        metric_row("STALE_COUNT", counts["stale"], EXPECTED_STALE_COUNT),
        metric_row("REMAINING_COUNT", counts["remaining"], EXPECTED_REMAINING_COUNT),
        metric_row("ARTIFACT_TICKERS_PRESENT_COUNT", counts["artifact_count"], 0),
        metric_row("PARTIAL_HISTORY_HOLD_COUNT", len(partial_rows), EXPECTED_PARTIAL_HOLD_COUNT),
        metric_row("EMPTY_FETCH_HOLD_COUNT", len(empty_rows), EXPECTED_EMPTY_HOLD_COUNT),
        metric_row("MATURE_REVIEW_PRIORITY_TICKERS", ",".join(sorted(row["ticker"] for row in mature)), ",".join(sorted(EXPECTED_MATURE))),
        metric_row("NEAR_MATURE_WATCH_TICKERS", ",".join(sorted(row["ticker"] for row in near)), ",".join(sorted(EXPECTED_NEAR))),
        metric_row("EMPTY_FETCH_AUDIT_TICKERS", ",".join(sorted(row["ticker"] for row in empty_audit)), ",".join(sorted(EXPECTED_EMPTY))),
        metric_row("MANUAL_REVIEW_OPTIONAL_ROWS", len(manual_rows), "0_OR_MORE", "Optional input; informational only."),
    ]
    status_rows[-1]["status"] = "OK"

    status = STATUS_OK
    validation_fail_count = 0
    if missing or not gate_rows or not ledger_rows:
        status = STATUS_FAIL_INPUTS
        validation_fail_count = 1
    elif int(counts["artifact_count"]) > 0:
        status = STATUS_WARN_ARTIFACT
    elif any(row["status"] == "WARN" for row in status_rows):
        status = STATUS_WARN_COUNT

    write_csv(root / OUT_AUDIT, audit_rows, OUTPUT_FIELDS)
    write_csv(root / OUT_MATURE, mature, OUTPUT_FIELDS)
    write_csv(root / OUT_NEAR, near, OUTPUT_FIELDS)
    write_csv(root / OUT_CONTINUE, continue_hold, OUTPUT_FIELDS)
    write_csv(root / OUT_EMPTY, empty_audit, OUTPUT_FIELDS)
    write_csv(root / OUT_STATUS, status_rows, STATUS_FIELDS)

    price_modified = tree_sig(root / "state" / "v18" / "price_cache") != price_before
    ledger_modified = file_sig(root / LEDGER) != ledger_before
    factor_modified = tree_sig(root / "outputs" / "v18" / "factor_pack") != factor_before
    tech_modified = tree_sig(root / "outputs" / "v18" / "technical_timing") != tech_before
    candidates_modified = tree_sig(root / "outputs" / "v18" / "candidates") != candidates_before
    forbidden_modified = price_modified or ledger_modified or factor_modified or tech_modified or candidates_modified
    if forbidden_modified:
        status = STATUS_FAIL_FORBIDDEN
        validation_fail_count = max(validation_fail_count, 1)

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "TOTAL_LEDGER_ROWS": counts["total"],
        "COVERED_WITHIN_5D": counts["covered"],
        "NEVER_SUCCESS_COUNT": counts["never_success"],
        "STALE_COUNT": counts["stale"],
        "REMAINING_COUNT": counts["remaining"],
        "ARTIFACT_TICKERS_PRESENT_COUNT": counts["artifact_count"],
        "QUALITY_GATE_TOTAL_COUNT": len(gate_rows),
        "PARTIAL_HISTORY_HOLD_COUNT": len(partial_rows),
        "EMPTY_FETCH_HOLD_COUNT": len(empty_rows),
        "MATURE_REVIEW_PRIORITY_COUNT": len(mature),
        "NEAR_MATURE_WATCH_COUNT": len(near),
        "CONTINUE_PARTIAL_HOLD_COUNT": len(continue_hold),
        "EMPTY_FETCH_SYMBOL_PROVIDER_AUDIT_COUNT": len(empty_audit),
        "OFFICIAL_INTEGRATION_ALLOWED_NEXT": "FALSE",
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
        "NEXT_RECOMMENDED_STEP": "R27B: manual policy review for TLN/RDDT and symbol-provider audit or provider-fallback retry for empty-fetch holds; no automatic official integration.",
    }

    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, status_rows, bucket_counts))
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if validation_fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
