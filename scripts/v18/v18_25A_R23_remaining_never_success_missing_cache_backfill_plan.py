from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R23_MISSING_CACHE_BACKFILL_PLAN_READY"
STATUS_VALIDATION_MISSING = "WARN_V18_25A_R23_R22B_VALIDATION_MISSING"
STATUS_NO_CANDIDATES = "WARN_V18_25A_R23_NO_MISSING_CACHE_CANDIDATES"
STATUS_ALL_HELD_OUT = "WARN_V18_25A_R23_ALL_CANDIDATES_HELD_OUT"
STATUS_PARTIAL_INPUTS = "WARN_V18_25A_R23_PARTIAL_INPUTS_USED"
STATUS_REVIEW = "WARN_V18_25A_R23_REVIEW_NEEDED"

MODE = "PLAN_ONLY_MISSING_CACHE_BACKFILL"

R22B_VALIDATION = "outputs/v18/rolling_coverage/V18_25A_R22B_CURRENT_LOCAL_REFRESH_VALIDATION.csv"
R22B_LEDGER_UPDATE = "outputs/v18/rolling_coverage/V18_25A_R22B_CURRENT_LEDGER_UPDATE_RESULT.csv"
R22_STATE = "outputs/v18/rolling_coverage/V18_25A_R22_CURRENT_CONTINUATION_STATE.csv"
R22_PLAN = "outputs/v18/rolling_coverage/V18_25A_R22_CURRENT_MULTI_RUN_REFRESH_PLAN.csv"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
PRICE_CACHE = "state/v18/price_cache"

OUT_CANDIDATES = "outputs/v18/staged_backfill/V18_25A_R23_CURRENT_MISSING_CACHE_CANDIDATES.csv"
OUT_EXCLUDED = "outputs/v18/staged_backfill/V18_25A_R23_CURRENT_EXCLUDED_INVALID_OR_ARTIFACTS.csv"
OUT_PLAN = "outputs/v18/staged_backfill/V18_25A_R23_CURRENT_BACKFILL_PLAN.csv"
OUT_AUDIT = "outputs/v18/staged_backfill/V18_25A_R23_CURRENT_BACKFILL_PLAN_AUDIT.csv"
OUT_HELD_OUT = "outputs/v18/staged_backfill/V18_25A_R23_CURRENT_HELD_OUT_REVIEW.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R23_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R23_CURRENT_MISSING_CACHE_BACKFILL_PLAN_REPORT.md"

CANDIDATE_FIELDS = [
    "ticker",
    "priority_rank",
    "classification",
    "include_reason",
    "r22b_validation_result",
    "r22b_error_message",
    "local_price_path",
    "local_price_available",
    "never_success",
    "continuation_eligible",
    "ledger_row_found",
    "current_ledger_status",
]
EXCLUDED_FIELDS = [
    "ticker",
    "priority_rank",
    "classification",
    "exclude_reason",
    "r22b_validation_result",
    "r22b_error_message",
    "local_price_available",
    "never_success",
    "continuation_eligible",
    "ledger_row_found",
]
PLAN_FIELDS = [
    "batch_id",
    "ticker",
    "priority_rank",
    "reason",
    "source_from_r22b",
    "missing_cache_status",
    "never_success_status",
    "current_ledger_status",
    "proposed_backfill_mode",
    "proposed_provider",
    "expected_output_dir",
    "integration_allowed_now",
    "quality_gate_required",
    "official_price_cache_integration_allowed_now",
    "notes",
]
AUDIT_FIELDS = ["metric", "value", "notes"]
READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R22B_VALIDATION_PATH",
    "R22_CONTINUATION_STATE_PATH",
    "ROLLING_LEDGER_PATH",
    "MAX_TICKERS",
    "R22B_LOCAL_VALIDATION_FAIL_COUNT",
    "NO_LOCAL_PRICE_CACHE_FAIL_COUNT",
    "RAW_CANDIDATE_COUNT",
    "DEDUPED_CANDIDATE_COUNT",
    "APPROVED_FOR_NEXT_STAGED_BACKFILL_COUNT",
    "HELD_OUT_COUNT",
    "INVALID_OR_ARTIFACT_COUNT",
    "ALREADY_HAS_LOCAL_CACHE_COUNT",
    "NOT_NEVER_SUCCESS_COUNT",
    "NOT_IN_LEDGER_COUNT",
    "DUPLICATE_EXCLUDED_COUNT",
    "REVIEW_NEEDED_COUNT",
    "BACKFILL_PLAN_PATH",
    "MISSING_CACHE_CANDIDATES_PATH",
    "EXCLUDED_INVALID_OR_ARTIFACTS_PATH",
    "HELD_OUT_REVIEW_PATH",
    "OFFICIAL_PRICE_CACHE_INTEGRATION_ALLOWED_NOW",
    "QUALITY_GATE_REQUIRED_NEXT",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
    "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_FILES_MODIFIED",
    "STAGED_BACKFILL_RAW_MODIFIED",
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


def norm_key(value: str) -> str:
    return "".join(ch for ch in str(value or "").strip().lower() if ch.isalnum())


def find_col(fields: Sequence[str], aliases: Sequence[str]) -> Optional[str]:
    by_norm = {norm_key(field): field for field in fields}
    for alias in aliases:
        hit = by_norm.get(norm_key(alias))
        if hit:
            return hit
    return None


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def valid_symbol(ticker: str) -> bool:
    invalid_literals = {"", "TICKER", "TICKERS", "HEADER", "NULL", "NONE", "NAN", "SYMBOL"}
    if ticker in invalid_literals:
        return False
    if any(ch in ticker for ch in '<>:"/\\|?*'):
        return False
    return bool(re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", ticker))


def ledger_maps(rows: List[Dict[str, str]], fields: Sequence[str]) -> Dict[str, Dict[str, str]]:
    ticker_col = find_col(fields, ["ticker", "symbol"])
    if not ticker_col:
        return {}
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        ticker = norm_ticker(row.get(ticker_col))
        if ticker and ticker not in out:
            out[ticker] = row
    return out


def infer_never_success(ticker: str, state_row: Optional[Dict[str, str]], ledger_row: Optional[Dict[str, str]], ledger_fields: Sequence[str]) -> bool:
    if state_row and str(state_row.get("never_success", "")).strip():
        return is_true(state_row.get("never_success"))
    if not ledger_row:
        return False
    success_col = find_col(ledger_fields, ["last_success_scan_date", "last_success_date", "latest_success_date"])
    return not str(ledger_row.get(success_col, "") or "").strip() if success_col else False


def infer_continuation_eligible(state_row: Optional[Dict[str, str]]) -> bool:
    if not state_row:
        return False
    value = str(state_row.get("continuation_eligible", "")).strip()
    return is_true(value) if value else False


def local_cache_exists(root: Path, ticker: str) -> bool:
    return (root / PRICE_CACHE / f"{ticker}.csv").exists()


def is_missing_cache_failure(row: Dict[str, str]) -> bool:
    error = str(row.get("error_message", "") or "").lower()
    result = str(row.get("validation_result", "") or "").upper()
    local_available = is_true(row.get("local_price_available"))
    return result != "PASS_LOCAL_PRICE_AVAILABLE" and (not local_available or "missing" in error or "local price cache" in error)


def classify_candidates(
    root: Path,
    validation_rows: List[Dict[str, str]],
    state_rows: List[Dict[str, str]],
    ledger_rows: List[Dict[str, str]],
    ledger_fields: Sequence[str],
    max_tickers: int,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]], Dict[str, int]]:
    state_by_ticker = {norm_ticker(row.get("ticker")): row for row in state_rows if norm_ticker(row.get("ticker"))}
    ledger_by_ticker = ledger_maps(ledger_rows, ledger_fields)
    status_col = find_col(ledger_fields, ["last_scan_status", "scan_status", "status"])

    raw_rows = [row for row in validation_rows if is_missing_cache_failure(row)]
    raw_rows.sort(key=lambda row: (to_int(row.get("priority_rank"), 999999), norm_ticker(row.get("ticker"))))

    seen: set[str] = set()
    candidates: List[Dict[str, object]] = []
    held_out: List[Dict[str, object]] = []
    counts = {
        "raw": len(raw_rows),
        "deduped": 0,
        "approved": 0,
        "held_out": 0,
        "invalid": 0,
        "already_cache": 0,
        "not_never": 0,
        "not_in_ledger": 0,
        "duplicate": 0,
        "review": 0,
    }

    for row in raw_rows:
        ticker = norm_ticker(row.get("ticker"))
        state_row = state_by_ticker.get(ticker)
        ledger_row = ledger_by_ticker.get(ticker)
        never_success = infer_never_success(ticker, state_row, ledger_row, ledger_fields)
        continuation_eligible = infer_continuation_eligible(state_row)
        ledger_status = str(ledger_row.get(status_col, "") or "") if ledger_row and status_col else ""
        base = {
            "ticker": ticker,
            "priority_rank": row.get("priority_rank", ""),
            "r22b_validation_result": row.get("validation_result", ""),
            "r22b_error_message": row.get("error_message", ""),
            "local_price_path": row.get("local_price_path", ""),
            "local_price_available": local_cache_exists(root, ticker),
            "never_success": never_success,
            "continuation_eligible": continuation_eligible,
            "ledger_row_found": bool(ledger_row),
            "current_ledger_status": ledger_status,
        }
        if ticker in seen:
            counts["duplicate"] += 1
            held_out.append({**base, "classification": "HELD_OUT_DUPLICATE", "exclude_reason": "Duplicate ticker in raw R22B missing-cache candidates."})
            continue
        seen.add(ticker)
        counts["deduped"] += 1

        if not valid_symbol(ticker):
            counts["invalid"] += 1
            held_out.append({**base, "classification": "HELD_OUT_INVALID_OR_ARTIFACT", "exclude_reason": "Ticker is empty, an artifact literal, contains invalid path characters, or is not ticker-like."})
        elif base["local_price_available"]:
            counts["already_cache"] += 1
            held_out.append({**base, "classification": "HELD_OUT_ALREADY_HAS_LOCAL_CACHE", "exclude_reason": "Local price cache now exists; staged backfill is not needed."})
        elif not ledger_row:
            counts["not_in_ledger"] += 1
            held_out.append({**base, "classification": "HELD_OUT_NOT_IN_LEDGER", "exclude_reason": "Ticker is absent from rolling ledger; universe extension is not part of R23."})
        elif not never_success:
            counts["not_never"] += 1
            held_out.append({**base, "classification": "HELD_OUT_NOT_NEVER_SUCCESS", "exclude_reason": "Ticker is not never-success in continuation state or ledger."})
        elif not continuation_eligible:
            counts["review"] += 1
            held_out.append({**base, "classification": "HELD_OUT_REVIEW_NEEDED", "exclude_reason": "Ticker is not continuation eligible in R22 state."})
        else:
            candidates.append({**base, "classification": "APPROVED_FOR_NEXT_STAGED_BACKFILL", "include_reason": "R22B local validation failed due to missing local price cache; ticker is valid, in ledger, never-success, and continuation eligible."})

    approved_limited = candidates[: max(max_tickers, 0)]
    for extra in candidates[max(max_tickers, 0) :]:
        counts["review"] += 1
        held_out.append({**extra, "classification": "HELD_OUT_REVIEW_NEEDED", "exclude_reason": "Beyond MaxTickers limit for this R23 plan."})
    candidates = approved_limited
    counts["approved"] = len(candidates)
    counts["held_out"] = len(held_out)

    plan_rows: List[Dict[str, object]] = []
    batch_id = f"V18_25A_R23_MISSING_CACHE_BATCH_{dt.datetime.now().strftime('%Y%m%d')}"
    for idx, candidate in enumerate(candidates, 1):
        plan_rows.append(
            {
                "batch_id": batch_id,
                "ticker": candidate["ticker"],
                "priority_rank": idx,
                "reason": candidate["include_reason"],
                "source_from_r22b": "V18_25A_R22B_CURRENT_LOCAL_REFRESH_VALIDATION",
                "missing_cache_status": "MISSING_LOCAL_PRICE_CACHE",
                "never_success_status": "TRUE",
                "current_ledger_status": candidate.get("current_ledger_status", ""),
                "proposed_backfill_mode": "CONTROLLED_STAGED_BACKFILL_REQUIRED",
                "proposed_provider": "yfinance",
                "expected_output_dir": "data/v18/staged_backfill/V18_25A_R23B",
                "integration_allowed_now": "FALSE",
                "quality_gate_required": "TRUE",
                "official_price_cache_integration_allowed_now": "FALSE",
                "notes": "Provider label only; R23 performs no external fetch.",
            }
        )
    return candidates, held_out, plan_rows, counts


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object]) -> str:
    return "\n".join(
        [
            "# V18.25A R23 Missing-Cache Backfill Plan Report",
            "",
            f"STATUS: {values['STATUS']}",
            f"MODE: {values['MODE']}",
            f"RUN_ID: {values['RUN_ID']}",
            "",
            "## Candidates",
            f"- raw_missing_cache_candidate_count: {values['RAW_CANDIDATE_COUNT']}",
            f"- approved_for_next_staged_backfill_count: {values['APPROVED_FOR_NEXT_STAGED_BACKFILL_COUNT']}",
            f"- held_out_count: {values['HELD_OUT_COUNT']}",
            f"- invalid_or_artifact_count: {values['INVALID_OR_ARTIFACT_COUNT']}",
            "",
            "## Safety",
            "- external_fetch_executed: FALSE",
            "- price_cache_modified: FALSE",
            "- rolling_ledger_modified: FALSE",
            "- staged_backfill_raw_modified: FALSE",
            "- official_price_cache_integration_allowed_now: FALSE",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--max-tickers", type=int, default=65)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R23_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    validation_path = root / R22B_VALIDATION
    state_path = root / R22_STATE
    ledger_path = root / LEDGER
    price_before = tree_sig(root / PRICE_CACHE)
    ledger_before = file_sig(ledger_path)
    raw_backfill_before = tree_sig(root / "data" / "v18" / "staged_backfill")

    validation_rows, _ = read_csv(validation_path)
    state_rows, _ = read_csv(state_path)
    ledger_rows, ledger_fields = read_csv(ledger_path)
    _ledger_update_rows, _ = read_csv(root / R22B_LEDGER_UPDATE)
    _r22_plan_rows, _ = read_csv(root / R22_PLAN)

    status = STATUS_OK
    validation_fail_count = 0
    partial_inputs = False
    if not validation_path.exists() or not validation_rows:
        status = STATUS_VALIDATION_MISSING
        validation_fail_count = 1
    if not state_rows or not ledger_rows:
        partial_inputs = True
        if status == STATUS_OK:
            status = STATUS_PARTIAL_INPUTS

    candidates: List[Dict[str, object]] = []
    held_out: List[Dict[str, object]] = []
    plan_rows: List[Dict[str, object]] = []
    counts = {"raw": 0, "deduped": 0, "approved": 0, "held_out": 0, "invalid": 0, "already_cache": 0, "not_never": 0, "not_in_ledger": 0, "duplicate": 0, "review": 0}
    if validation_rows:
        candidates, held_out, plan_rows, counts = classify_candidates(root, validation_rows, state_rows, ledger_rows, ledger_fields, args.max_tickers)
        if counts["raw"] == 0:
            status = STATUS_NO_CANDIDATES
        elif counts["approved"] == 0:
            status = STATUS_ALL_HELD_OUT
        elif counts["review"] > 0 and status == STATUS_OK:
            status = STATUS_REVIEW
        elif partial_inputs and status == STATUS_OK:
            status = STATUS_PARTIAL_INPUTS

    excluded_invalid = [row for row in held_out if row.get("classification") == "HELD_OUT_INVALID_OR_ARTIFACT"]
    r22b_fail_count = sum(1 for row in validation_rows if str(row.get("validation_result", "")).upper() != "PASS_LOCAL_PRICE_AVAILABLE")
    no_cache_fail_count = sum(1 for row in validation_rows if is_missing_cache_failure(row))

    audit_rows = [
        {"metric": "status", "value": status, "notes": ""},
        {"metric": "r22b_local_validation_fail_count", "value": r22b_fail_count, "notes": ""},
        {"metric": "no_local_price_cache_fail_count", "value": no_cache_fail_count, "notes": ""},
        {"metric": "raw_candidate_count", "value": counts["raw"], "notes": ""},
        {"metric": "deduped_candidate_count", "value": counts["deduped"], "notes": ""},
        {"metric": "approved_for_next_staged_backfill_count", "value": counts["approved"], "notes": ""},
        {"metric": "held_out_count", "value": counts["held_out"], "notes": ""},
        {"metric": "invalid_or_artifact_count", "value": counts["invalid"], "notes": ""},
        {"metric": "already_has_local_cache_count", "value": counts["already_cache"], "notes": ""},
        {"metric": "not_never_success_count", "value": counts["not_never"], "notes": ""},
        {"metric": "not_in_ledger_count", "value": counts["not_in_ledger"], "notes": ""},
        {"metric": "duplicate_excluded_count", "value": counts["duplicate"], "notes": ""},
        {"metric": "review_needed_count", "value": counts["review"], "notes": ""},
        {"metric": "external_fetch_executed", "value": "FALSE", "notes": ""},
        {"metric": "official_price_cache_integration_allowed_now", "value": "FALSE", "notes": ""},
    ]

    write_csv(root / OUT_CANDIDATES, candidates, CANDIDATE_FIELDS)
    write_csv(root / OUT_EXCLUDED, excluded_invalid, EXCLUDED_FIELDS)
    write_csv(root / OUT_PLAN, plan_rows, PLAN_FIELDS)
    write_csv(root / OUT_AUDIT, audit_rows, AUDIT_FIELDS)
    write_csv(root / OUT_HELD_OUT, held_out, EXCLUDED_FIELDS)

    price_modified = tree_sig(root / PRICE_CACHE) != price_before
    ledger_modified = file_sig(ledger_path) != ledger_before
    raw_backfill_modified = tree_sig(root / "data" / "v18" / "staged_backfill") != raw_backfill_before
    forbidden_modified = price_modified or ledger_modified or raw_backfill_modified

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R22B_VALIDATION_PATH": R22B_VALIDATION,
        "R22_CONTINUATION_STATE_PATH": R22_STATE,
        "ROLLING_LEDGER_PATH": LEDGER,
        "MAX_TICKERS": args.max_tickers,
        "R22B_LOCAL_VALIDATION_FAIL_COUNT": r22b_fail_count,
        "NO_LOCAL_PRICE_CACHE_FAIL_COUNT": no_cache_fail_count,
        "RAW_CANDIDATE_COUNT": counts["raw"],
        "DEDUPED_CANDIDATE_COUNT": counts["deduped"],
        "APPROVED_FOR_NEXT_STAGED_BACKFILL_COUNT": counts["approved"],
        "HELD_OUT_COUNT": counts["held_out"],
        "INVALID_OR_ARTIFACT_COUNT": counts["invalid"],
        "ALREADY_HAS_LOCAL_CACHE_COUNT": counts["already_cache"],
        "NOT_NEVER_SUCCESS_COUNT": counts["not_never"],
        "NOT_IN_LEDGER_COUNT": counts["not_in_ledger"],
        "DUPLICATE_EXCLUDED_COUNT": counts["duplicate"],
        "REVIEW_NEEDED_COUNT": counts["review"],
        "BACKFILL_PLAN_PATH": OUT_PLAN,
        "MISSING_CACHE_CANDIDATES_PATH": OUT_CANDIDATES,
        "EXCLUDED_INVALID_OR_ARTIFACTS_PATH": OUT_EXCLUDED,
        "HELD_OUT_REVIEW_PATH": OUT_HELD_OUT,
        "OFFICIAL_PRICE_CACHE_INTEGRATION_ALLOWED_NOW": "FALSE",
        "QUALITY_GATE_REQUIRED_NEXT": "TRUE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "PRICE_CACHE_MODIFIED": "TRUE" if price_modified else "FALSE",
        "ROLLING_LEDGER_MODIFIED": "TRUE" if ledger_modified else "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "TIER_FILES_MODIFIED": "FALSE",
        "STAGED_BACKFILL_RAW_MODIFIED": "TRUE" if raw_backfill_modified else "FALSE",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": "TRUE" if forbidden_modified else "FALSE",
        "NEXT_RECOMMENDED_STEP": "R23B: Controlled staged backfill execution for approved missing-cache tickers, followed by staged quality gate.",
    }
    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values))

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
