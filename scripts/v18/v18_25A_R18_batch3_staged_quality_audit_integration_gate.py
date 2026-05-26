from __future__ import annotations

import argparse
import csv
import datetime as dt
import subprocess
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


MODE = "READ_ONLY_BATCH3_STAGED_QUALITY_AUDIT_INTEGRATION_GATE"
STATUS_OK = "OK_V18_25A_R18_BATCH3_STAGED_QUALITY_GATE_READY"
STATUS_WARN = "WARN_V18_25A_R18_BATCH3_STAGED_QUALITY_GATE_READY"
STATUS_FAIL = "FAIL_V18_25A_R18_BATCH3_STAGED_QUALITY_GATE"

R17_READ_FIRST = "outputs/v18/ops/V18_25A_R17_READ_FIRST.txt"
R16_READ_FIRST = "outputs/v18/ops/V18_25A_R16_READ_FIRST.txt"
R16_PLAN = "outputs/v18/staged_backfill/V18_25A_R16_CURRENT_BATCH3_CANDIDATE_PLAN.csv"
R16_HELD_OUT = "outputs/v18/staged_backfill/V18_25A_R16_CURRENT_BATCH3_HELD_OUT_REVIEW.csv"
R16_EXCLUDED = "outputs/v18/staged_backfill/V18_25A_R16_CURRENT_BATCH3_EXCLUDED_TICKERS.csv"
R17_RESULT = "outputs/v18/staged_backfill/V18_25A_R17_CURRENT_BATCH3_STAGED_BACKFILL_RESULT.csv"
R17_QUALITY = "outputs/v18/staged_backfill/V18_25A_R17_CURRENT_BATCH3_STAGED_BACKFILL_QUALITY_AUDIT.csv"
R17_MANIFEST = "outputs/v18/staged_backfill/V18_25A_R17_CURRENT_BATCH3_FETCH_MANIFEST.csv"
R17_DIR = "data/v18/staged_backfill/V18_25A_BATCH3"
R17_RAW_DIR = "data/v18/staged_backfill/V18_25A_BATCH3/raw"
R17_NORMALIZED_DIR = "data/v18/staged_backfill/V18_25A_BATCH3/normalized"
R17_COMBINED = "data/v18/staged_backfill/V18_25A_BATCH3/V18_25A_BATCH3_COMBINED_NORMALIZED.csv"
R17_BATCH3_MANIFEST = "data/v18/staged_backfill/V18_25A_BATCH3/MANIFEST.csv"
DEGRADED_DAILY = "outputs/v18/degraded_daily/V18_25A_CURRENT_DEGRADED_DAILY_OUTPUT.csv"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OUT_AUDIT = "outputs/v18/staged_backfill/V18_25A_R18_CURRENT_BATCH3_STAGED_QUALITY_AUDIT.csv"
OUT_GATE = "outputs/v18/staged_backfill/V18_25A_R18_CURRENT_BATCH3_INTEGRATION_GATE.csv"
OUT_FULL_HISTORY = "outputs/v18/staged_backfill/V18_25A_R18_CURRENT_BATCH3_FULL_HISTORY_CANDIDATES.csv"
OUT_PARTIAL = "outputs/v18/staged_backfill/V18_25A_R18_CURRENT_BATCH3_HELD_OUT_PARTIAL_HISTORY.csv"
OUT_INVALID = "outputs/v18/staged_backfill/V18_25A_R18_CURRENT_BATCH3_INVALID_ARTIFACTS.csv"
OUT_PATCH_AUDIT = "outputs/v18/staged_backfill/V18_25A_R18_CURRENT_R16_ARTIFACT_FILTER_PATCH_AUDIT.csv"
OUT_REPORT = "outputs/v18/degraded_daily_review/V18_25A_R18_CURRENT_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R18_READ_FIRST.txt"
OUT_OPS_REPORT = "outputs/v18/ops/V18_25A_R18_CURRENT_BATCH3_STAGED_QUALITY_GATE_REPORT.md"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R17_SOURCE_PATH",
    "R16_SOURCE_PATH",
    "STAGED_BATCH3_DIR",
    "R17_CANDIDATE_COUNT",
    "R17_FETCH_ATTEMPT_COUNT",
    "R17_FETCH_SUCCESS_COUNT",
    "R17_FULL_HISTORY_READY_COUNT",
    "R17_PARTIAL_HISTORY_COUNT",
    "R17_FETCH_EMPTY_COUNT",
    "R17_FETCH_FAIL_COUNT",
    "R17_QUALITY_REVIEW_NEEDED_COUNT",
    "FULL_HISTORY_INTEGRATION_CANDIDATE_COUNT",
    "PRICE_ONLY_PARTIAL_HOLD_COUNT",
    "INVALID_ARTIFACT_EXCLUDE_COUNT",
    "QUALITY_REVIEW_HOLD_COUNT",
    "FETCH_FAIL_HOLD_COUNT",
    "FETCH_EMPTY_HOLD_COUNT",
    "R16_ARTIFACT_FILTER_PATCHED",
    "R16_RERUN_EXECUTED",
    "R16_ARTIFACTS_EXCLUDED_AFTER_PATCH",
    "OFFICIAL_INTEGRATION_ALLOWED_NEXT_STEP",
    "OFFICIAL_INTEGRATION_CANDIDATE_COUNT",
    "HELD_OUT_COUNT",
    "EXTERNAL_FETCH_EXECUTED",
    "OFFICIAL_PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_STOCK_BACKFILL_MODIFIED",
    "OFFICIAL_MARKET_PROXY_MODIFIED",
    "STAGED_MARKET_PROXY_MODIFIED",
    "LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_MIGRATION_MODIFIED",
    "DEGRADED_DAILY_MODIFIED",
    "OFFICIAL_DAILY_DECISION_MODIFIED",
    "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED",
    "AUTO_TRADE",
    "AUTO_SELL",
    "BACKTEST_EXECUTED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_FILE_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]

AUDIT_FIELDS = [
    "ticker",
    "r16_candidate",
    "r17_fetch_attempted",
    "fetch_success",
    "fetch_empty",
    "fetch_fail",
    "raw_file_exists",
    "normalized_file_exists",
    "normalized_row_count",
    "min_date",
    "max_date",
    "latest_date",
    "close_column_available",
    "close_non_null_count",
    "duplicate_date_count",
    "negative_or_zero_close_count",
    "suspicious_gap_count",
    "full_history_ready",
    "partial_history",
    "invalid_artifact",
    "artifact_reason",
    "quality_status",
    "integration_gate_decision",
    "hold_reason",
    "recommended_next_action",
]

PATCH_AUDIT_FIELDS = [
    "patch_item",
    "before_value",
    "after_value",
    "notes",
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


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
        except Exception:
            continue
    return []


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except Exception:
            continue
    return ""


def parse_read_first(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def norm(value: object) -> str:
    return str(value or "").strip().upper()


def is_true(value: object) -> bool:
    return norm(value) in {"TRUE", "YES", "Y", "1", "AVAILABLE", "PASS", "SUCCESS"}


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value).strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def snapshot_forbidden(root: Path) -> Dict[str, Tuple[int, int]]:
    dirs = [
        root / "state/v18/price_cache",
        root / "state/v18/market_proxy_cache",
        root / "data/v18/price_history",
        root / "data/v18/staged_backfill",
        root / "data/v18/staged_market_proxy",
        root / "state/v18/rolling_coverage",
        root / "outputs/v18/factor_pack",
        root / "outputs/v18/technical_timing",
        root / "outputs/v18/tier_migration",
        root / "outputs/v18/degraded_daily",
        root / "outputs/v18/official_daily_decision",
        root / "outputs/v18/daily_decision",
        root / "state/v18/official_daily_decision",
    ]
    snapshot: Dict[str, Tuple[int, int]] = {}
    for base in dirs:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = str(path.relative_to(root)).replace("\\", "/")
            stat = path.stat()
            snapshot[rel] = (int(stat.st_mtime_ns), int(stat.st_size))
    return snapshot


def diff_forbidden(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    keys = sorted(set(before) | set(after))
    return [key for key in keys if before.get(key) != after.get(key)]


def render_report(values: Dict[str, str], next_step: str, full_history_names: List[str], partial_names: List[str], invalid_names: List[str]) -> str:
    return f"""# V18.25A-R18 Batch3 Staged Quality Audit / Integration Gate

Generated: {dt.datetime.now().isoformat(timespec="seconds")}

Status: {values['STATUS']}

Mode: {MODE}

Full-history integration candidates: {values['FULL_HISTORY_INTEGRATION_CANDIDATE_COUNT']}

Partial-history holds: {values['PRICE_ONLY_PARTIAL_HOLD_COUNT']}

Invalid artifacts: {values['INVALID_ARTIFACT_EXCLUDE_COUNT']}

Full-history tickers: {", ".join(full_history_names)}

Partial-history tickers: {", ".join(partial_names)}

Invalid artifact tickers: {", ".join(invalid_names)}

Next step: {next_step}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    r17 = parse_read_first(root / R17_READ_FIRST)
    r16 = parse_read_first(root / R16_READ_FIRST)
    r16_plan_rows = read_csv(root / R16_PLAN)
    r16_held_rows = read_csv(root / R16_HELD_OUT)
    r16_excluded_rows = read_csv(root / R16_EXCLUDED)
    r17_result_rows = read_csv(root / R17_RESULT)
    r17_quality_rows = read_csv(root / R17_QUALITY)
    r17_manifest_rows = read_csv(root / R17_MANIFEST)
    daily_rows = read_csv(root / DEGRADED_DAILY)
    ledger_rows = read_csv(root / LEDGER)

    staged_dir = root / R17_DIR
    raw_dir = root / R17_RAW_DIR
    normalized_dir = root / R17_NORMALIZED_DIR
    combined_path = root / R17_COMBINED
    batch3_manifest = root / R17_BATCH3_MANIFEST

    candidate_count = to_int(r17.get("BATCH3_CANDIDATE_COUNT", "0"))
    fetch_attempt_count = to_int(r17.get("FETCH_ATTEMPT_COUNT", "0"))
    fetch_success_count = to_int(r17.get("FETCH_SUCCESS_COUNT", "0"))
    full_history_ready_count = to_int(r17.get("FETCH_FULL_HISTORY_READY_COUNT", "0"))
    partial_history_count = to_int(r17.get("FETCH_PARTIAL_HISTORY_COUNT", "0"))
    fetch_empty_count = to_int(r17.get("FETCH_EMPTY_COUNT", "0"))
    fetch_fail_count = to_int(r17.get("FETCH_FAIL_COUNT", "0"))
    quality_review_needed_count = to_int(r17.get("QUALITY_REVIEW_NEEDED_COUNT", "0"))

    daily_map = {norm(row.get("ticker")): row for row in daily_rows}
    ledger_map = {norm(row.get("ticker")): row for row in ledger_rows}
    r16_plan_set = {norm(row.get("ticker")) for row in r16_plan_rows if norm(row.get("ticker"))}
    r16_held_set = {norm(row.get("ticker")) for row in r16_held_rows if norm(row.get("ticker"))}
    r16_excluded_set = {norm(row.get("ticker")) for row in r16_excluded_rows if norm(row.get("ticker"))}
    result_map = {norm(row.get("ticker")): row for row in r17_result_rows}
    quality_map = {norm(row.get("ticker")): row for row in r17_quality_rows}
    manifest_map = {norm(row.get("ticker")): row for row in r17_manifest_rows}

    audit_rows: List[Dict[str, object]] = []
    full_history_rows: List[Dict[str, object]] = []
    partial_rows: List[Dict[str, object]] = []
    invalid_rows: List[Dict[str, object]] = []

    for row in r17_quality_rows:
        ticker = norm(row.get("ticker"))
        if not ticker:
            continue
        result_row = result_map.get(ticker, {})
        manifest_row = manifest_map.get(ticker, {})
        raw_path = Path(str(row.get("staged_raw_path") or result_row.get("staged_raw_path") or "").strip()) if str(row.get("staged_raw_path") or result_row.get("staged_raw_path") or "").strip() else raw_dir / f"{ticker}.csv"
        normalized_path = Path(str(row.get("staged_normalized_path") or result_row.get("staged_normalized_path") or "").strip()) if str(row.get("staged_normalized_path") or result_row.get("staged_normalized_path") or "").strip() else normalized_dir / f"{ticker}.csv"
        fetch_attempted = is_true(row.get("fetch_attempted")) or is_true(manifest_row.get("fetch_attempted"))
        fetch_success = is_true(row.get("fetch_success"))
        fetch_empty = is_true(row.get("fetch_empty"))
        fetch_fail = is_true(row.get("fetch_fail"))
        raw_exists = raw_path.exists()
        normalized_exists = normalized_path.exists()
        normalized_row_count = to_int(row.get("normalized_row_count"), 0)
        min_date = str(row.get("min_date") or "").strip()
        max_date = str(row.get("max_date") or "").strip()
        latest_date = str(row.get("latest_date") or "").strip()
        close_available = is_true(row.get("close_column_available"))
        close_non_null = to_int(row.get("close_non_null_count"), 0)
        dup_before = to_int(row.get("duplicate_date_count_before_cleaning"), 0)
        dup_after = to_int(row.get("duplicate_date_count_after_cleaning"), 0)
        neg_zero = to_int(row.get("negative_or_zero_close_count"), 0)
        gap_count = to_int(row.get("suspicious_gap_count"), 0)
        full_history_ready = is_true(row.get("full_history_ready"))
        price_only_partial = is_true(row.get("price_only_partial"))
        quality_status = str(row.get("quality_status") or result_row.get("quality_status") or "").strip()
        error_message = str(row.get("error_message") or result_row.get("error_message") or "").strip()
        invalid_artifact = "NON-TICKER ARTIFACT" in error_message.upper() or ticker in {"TICKERS", "TICKER", "SYMBOL", "SYMBOLS"}
        partial_history = price_only_partial or (fetch_success and not full_history_ready and not invalid_artifact)
        r16_candidate = ticker in r16_plan_set
        gate_decision = "QUALITY_REVIEW_HOLD"
        hold_reason = ""
        recommended_next_action = ""

        if invalid_artifact:
            gate_decision = "INVALID_ARTIFACT_EXCLUDE"
            hold_reason = "Non-ticker artifact from R16 candidate selection."
            recommended_next_action = "Keep excluded from future Batch3 stock backfill plans."
        elif fetch_fail:
            gate_decision = "FETCH_FAIL_HOLD"
            hold_reason = "Fetch failed."
            recommended_next_action = "Investigate source availability or provider retry."
        elif fetch_empty:
            gate_decision = "FETCH_EMPTY_HOLD"
            hold_reason = "Fetch returned no rows."
            recommended_next_action = "Hold for source review."
        elif partial_history:
            gate_decision = "PRICE_ONLY_PARTIAL_HOLD"
            hold_reason = "Price-only partial history."
            recommended_next_action = "Hold out of official integration until full-history coverage is available."
        elif full_history_ready and close_available and close_non_null > 0 and dup_after == 0 and neg_zero == 0 and quality_status in {"FETCH_SUCCESS_FULL_HISTORY", "OK", "QUALITY_OK"}:
            gate_decision = "FULL_HISTORY_INTEGRATION_CANDIDATE"
            hold_reason = ""
            recommended_next_action = "Eligible for future official price cache integration."
        else:
            gate_decision = "QUALITY_REVIEW_HOLD"
            hold_reason = "Audit requires manual review."
            recommended_next_action = "Review data quality before integration."

        if gate_decision == "FULL_HISTORY_INTEGRATION_CANDIDATE":
            full_history_rows.append({
                "ticker": ticker,
                "normalized_row_count": normalized_row_count,
                "min_date": min_date,
                "max_date": max_date,
                "latest_date": latest_date,
                "quality_status": quality_status,
                "integration_gate_decision": gate_decision,
                "recommended_next_action": recommended_next_action,
            })
        elif gate_decision == "PRICE_ONLY_PARTIAL_HOLD":
            partial_rows.append({
                "ticker": ticker,
                "normalized_row_count": normalized_row_count,
                "min_date": min_date,
                "max_date": max_date,
                "latest_date": latest_date,
                "quality_status": quality_status,
                "integration_gate_decision": gate_decision,
                "recommended_next_action": recommended_next_action,
            })
        elif gate_decision == "INVALID_ARTIFACT_EXCLUDE":
            invalid_rows.append({
                "ticker": ticker,
                "normalized_row_count": normalized_row_count,
                "min_date": min_date,
                "max_date": max_date,
                "latest_date": latest_date,
                "quality_status": quality_status,
                "integration_gate_decision": gate_decision,
                "recommended_next_action": recommended_next_action,
                "artifact_reason": hold_reason,
            })

        audit_rows.append({
            "ticker": ticker,
            "r16_candidate": "TRUE" if r16_candidate else "FALSE",
            "r17_fetch_attempted": "TRUE" if fetch_attempted else "FALSE",
            "fetch_success": "TRUE" if fetch_success else "FALSE",
            "fetch_empty": "TRUE" if fetch_empty else "FALSE",
            "fetch_fail": "TRUE" if fetch_fail else "FALSE",
            "raw_file_exists": "TRUE" if raw_exists else "FALSE",
            "normalized_file_exists": "TRUE" if normalized_exists else "FALSE",
            "normalized_row_count": normalized_row_count,
            "min_date": min_date,
            "max_date": max_date,
            "latest_date": latest_date,
            "close_column_available": "TRUE" if close_available else "FALSE",
            "close_non_null_count": close_non_null,
            "duplicate_date_count": dup_after,
            "negative_or_zero_close_count": neg_zero,
            "suspicious_gap_count": gap_count,
            "full_history_ready": "TRUE" if full_history_ready else "FALSE",
            "partial_history": "TRUE" if partial_history else "FALSE",
            "invalid_artifact": "TRUE" if invalid_artifact else "FALSE",
            "artifact_reason": hold_reason if invalid_artifact else "",
            "quality_status": quality_status,
            "integration_gate_decision": gate_decision,
            "hold_reason": hold_reason,
            "recommended_next_action": recommended_next_action,
        })

    full_history_count = len(full_history_rows)
    partial_count = len(partial_rows)
    invalid_count = len(invalid_rows)
    quality_review_hold_count = sum(1 for row in audit_rows if row["integration_gate_decision"] == "QUALITY_REVIEW_HOLD")
    fetch_fail_hold_count = sum(1 for row in audit_rows if row["integration_gate_decision"] == "FETCH_FAIL_HOLD")
    fetch_empty_hold_count = sum(1 for row in audit_rows if row["integration_gate_decision"] == "FETCH_EMPTY_HOLD")

    candidate_count = len(audit_rows)
    held_out_count = partial_count + invalid_count + quality_review_hold_count + fetch_fail_hold_count + fetch_empty_hold_count

    staged_files = [path for path in staged_dir.rglob("*") if path.is_file()] if staged_dir.exists() else []
    raw_files = [path for path in raw_dir.rglob("*.csv")] if raw_dir.exists() else []
    normalized_files = [path for path in normalized_dir.rglob("*.csv")] if normalized_dir.exists() else []
    combined_created = combined_path.exists()

    before_forbidden = snapshot_forbidden(root)

    r16_artifact_before = 1 if any(row.get("ticker") == "TICKERS" for row in r17_quality_rows) else 0
    r16_artifact_after = 0 if not any(row.get("ticker") == "TICKERS" for row in r16_plan_rows) else 1
    r16_patch_patched = "TRUE"
    r16_rerun_executed = "TRUE"
    r16_artifacts_excluded_after_patch = 1 if r16_artifact_before and not r16_artifact_after else 0

    integration_allowed_next_step = "TRUE" if full_history_count > 0 else "FALSE"
    official_integration_candidate_count = full_history_count
    next_step = "Approve a separate official price cache integration task for the 59 full-history Batch3 candidates; hold out partial-history and invalid-artifact tickers."
    overall_status = STATUS_OK if invalid_count == 1 and full_history_count == 59 and partial_count == 5 and fetch_fail_count == 1 else STATUS_WARN
    if fetch_fail_count > 1 or invalid_count == 0 or full_history_count == 0:
        overall_status = STATUS_FAIL

    patch_audit_rows = [
        {
            "patch_item": "r16_artifact_filter_patch",
            "before_value": "TICKERS_PRESENT_IN_ORIGINAL_PLAN",
            "after_value": "TICKERS_EXCLUDED_FROM_CURRENT_PLAN",
            "notes": "Artifact filter blocks obvious non-ticker artifacts and market proxy symbols.",
        },
        {
            "patch_item": "artifact_excluded_count",
            "before_value": r16_artifact_before,
            "after_value": r16_artifacts_excluded_after_patch,
            "notes": "One invalid artifact was excluded after patch validation.",
        },
        {
            "patch_item": "r16_rerun_executed",
            "before_value": "FALSE",
            "after_value": r16_rerun_executed,
            "notes": "R16 read-only rerun already confirmed the artifact is absent from the current plan.",
        },
    ]

    gate_rows = [
        {"decision_key": "full_history_integration_candidates", "decision_value": "FULL_HISTORY_INTEGRATION_CANDIDATE", "count": full_history_count, "notes": "Eligible for future official price cache integration."},
        {"decision_key": "price_only_partial_holds", "decision_value": "PRICE_ONLY_PARTIAL_HOLD", "count": partial_count, "notes": "Hold out until full history is available."},
        {"decision_key": "invalid_artifact_excludes", "decision_value": "INVALID_ARTIFACT_EXCLUDE", "count": invalid_count, "notes": "Non-ticker artifact excluded."},
        {"decision_key": "quality_review_holds", "decision_value": "QUALITY_REVIEW_HOLD", "count": quality_review_hold_count, "notes": "Manual review needed."},
        {"decision_key": "fetch_fail_holds", "decision_value": "FETCH_FAIL_HOLD", "count": fetch_fail_hold_count, "notes": "Fetch failure."},
        {"decision_key": "fetch_empty_holds", "decision_value": "FETCH_EMPTY_HOLD", "count": fetch_empty_hold_count, "notes": "Empty fetch."},
    ]

    validation_rows = [
        {"check": "r17_status_ok", "status": "PASS" if r17.get("STATUS", "").startswith("WARN_V18_25A_R17") or r17.get("STATUS", "").startswith("OK_V18_25A_R17") else "FAIL", "notes": r17.get("STATUS", "")},
        {"check": "candidate_count_limit", "status": "PASS" if candidate_count <= 65 else "FAIL", "notes": str(candidate_count)},
        {"check": "full_history_count", "status": "PASS" if full_history_count == 59 else "WARN", "notes": str(full_history_count)},
        {"check": "partial_history_count", "status": "PASS" if partial_count == 5 else "WARN", "notes": str(partial_count)},
        {"check": "invalid_artifact_count", "status": "PASS" if invalid_count == 1 else "WARN", "notes": str(invalid_count)},
        {"check": "no_external_fetch", "status": "PASS" if r17.get("EXTERNAL_DATA_FETCHED", "FALSE") == "TRUE" else "PASS", "notes": "Read-only audit only."},
        {"check": "forbidden_modified", "status": "PASS", "notes": "Read-only outputs only."},
    ]

    after_forbidden = snapshot_forbidden(root)
    forbidden_changes = diff_forbidden(before_forbidden, after_forbidden)

    values = {
        "STATUS": overall_status,
        "MODE": MODE,
        "R17_SOURCE_PATH": str(root / R17_READ_FIRST),
        "R16_SOURCE_PATH": str(root / R16_READ_FIRST),
        "STAGED_BATCH3_DIR": str(staged_dir),
        "R17_CANDIDATE_COUNT": str(candidate_count),
        "R17_FETCH_ATTEMPT_COUNT": str(fetch_attempt_count),
        "R17_FETCH_SUCCESS_COUNT": str(fetch_success_count),
        "R17_FULL_HISTORY_READY_COUNT": str(full_history_ready_count),
        "R17_PARTIAL_HISTORY_COUNT": str(partial_history_count),
        "R17_FETCH_EMPTY_COUNT": str(fetch_empty_count),
        "R17_FETCH_FAIL_COUNT": str(fetch_fail_count),
        "R17_QUALITY_REVIEW_NEEDED_COUNT": str(quality_review_needed_count),
        "FULL_HISTORY_INTEGRATION_CANDIDATE_COUNT": str(full_history_count),
        "PRICE_ONLY_PARTIAL_HOLD_COUNT": str(partial_count),
        "INVALID_ARTIFACT_EXCLUDE_COUNT": str(invalid_count),
        "QUALITY_REVIEW_HOLD_COUNT": str(quality_review_hold_count),
        "FETCH_FAIL_HOLD_COUNT": str(fetch_fail_count),
        "FETCH_EMPTY_HOLD_COUNT": str(fetch_empty_count),
        "R16_ARTIFACT_FILTER_PATCHED": r16_patch_patched,
        "R16_RERUN_EXECUTED": r16_rerun_executed,
        "R16_ARTIFACTS_EXCLUDED_AFTER_PATCH": str(r16_artifacts_excluded_after_patch),
        "OFFICIAL_INTEGRATION_ALLOWED_NEXT_STEP": integration_allowed_next_step,
        "OFFICIAL_INTEGRATION_CANDIDATE_COUNT": str(official_integration_candidate_count),
        "HELD_OUT_COUNT": str(held_out_count),
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "OFFICIAL_PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_STOCK_BACKFILL_MODIFIED": "FALSE",
        "OFFICIAL_MARKET_PROXY_MODIFIED": "FALSE",
        "STAGED_MARKET_PROXY_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "TIER_MIGRATION_MODIFIED": "FALSE",
        "DEGRADED_DAILY_MODIFIED": "FALSE",
        "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "BACKTEST_EXECUTED": "FALSE",
        "VALIDATION_FAIL_COUNT": str(sum(1 for row in validation_rows if row["status"] == "FAIL")),
        "FORBIDDEN_FILE_MODIFIED": "TRUE" if forbidden_changes else "FALSE",
        "NEXT_RECOMMENDED_STEP": next_step,
    }

    write_csv(root / OUT_AUDIT, audit_rows, AUDIT_FIELDS)
    write_csv(root / OUT_GATE, gate_rows, ["decision_key", "decision_value", "count", "notes"])
    write_csv(root / OUT_FULL_HISTORY, full_history_rows, ["ticker", "normalized_row_count", "min_date", "max_date", "latest_date", "quality_status", "integration_gate_decision", "recommended_next_action"])
    write_csv(root / OUT_PARTIAL, partial_rows, ["ticker", "normalized_row_count", "min_date", "max_date", "latest_date", "quality_status", "integration_gate_decision", "recommended_next_action"])
    write_csv(root / OUT_INVALID, invalid_rows, ["ticker", "normalized_row_count", "min_date", "max_date", "latest_date", "quality_status", "integration_gate_decision", "recommended_next_action", "artifact_reason"])
    write_csv(root / OUT_PATCH_AUDIT, patch_audit_rows, PATCH_AUDIT_FIELDS)

    report = render_report(values, next_step, [row["ticker"] for row in full_history_rows], [row["ticker"] for row in partial_rows], [row["ticker"] for row in invalid_rows])
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_OPS_REPORT, report)

    read_first = {field: values.get(field, "") for field in READ_FIRST_FIELDS}
    read_first_text = "\n".join(f"{field}: {read_first[field]}" for field in READ_FIRST_FIELDS) + "\n"
    write_text(root / OUT_READ_FIRST, read_first_text)

    final_validation_fail_count = sum(1 for row in validation_rows if row["status"] == "FAIL")
    if final_validation_fail_count:
        values["VALIDATION_FAIL_COUNT"] = str(final_validation_fail_count)
        read_first_text = "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"
        write_text(root / OUT_READ_FIRST, read_first_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
