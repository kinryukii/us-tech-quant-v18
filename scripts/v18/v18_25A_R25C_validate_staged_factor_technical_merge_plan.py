from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R25C_STAGED_VALIDATION_MERGE_PLAN_READY"
STATUS_INPUTS_MISSING = "WARN_V18_25A_R25C_INPUTS_MISSING"
STATUS_ROW_COUNT = "WARN_V18_25A_R25C_ROW_COUNT_MISMATCH"
STATUS_TARGET_SET = "WARN_V18_25A_R25C_TARGET_SET_MISMATCH"
STATUS_SCHEMA = "WARN_V18_25A_R25C_SCHEMA_VALIDATION_REVIEW_NEEDED"
STATUS_SCORE = "WARN_V18_25A_R25C_SCORE_VALIDATION_REVIEW_NEEDED"
STATUS_MERGE_BLOCKED = "WARN_V18_25A_R25C_MERGE_BLOCKED"
STATUS_PARTIAL_FAIL = "WARN_V18_25A_R25C_PARTIAL_VALIDATION_FAILURE"
STATUS_MERGE_REFUSED = "WARN_V18_25A_R25C_OFFICIAL_MERGE_REFUSED"

MODE = "READ_ONLY_STAGED_VALIDATION_MERGE_PLAN"
EXPECTED_TARGET_COUNT = 93

IN_TARGETS = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_TARGETS.csv"
IN_FACTOR = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_STAGED_FACTOR_ROWS.csv"
IN_TECH = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_STAGED_TECHNICAL_ROWS.csv"
IN_FACTOR_AUDIT = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_FACTOR_BUILD_AUDIT.csv"
IN_TECH_AUDIT = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_TECHNICAL_BUILD_AUDIT.csv"
IN_SCHEMA = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_SCHEMA_VALIDATION.csv"
FACTOR_CURRENT = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_CURRENT = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
PRICE_CACHE = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OUT_FACTOR_VALIDATION = "outputs/v18/staged_factor_technical/V18_25A_R25C_CURRENT_STAGED_FACTOR_VALIDATION.csv"
OUT_TECH_VALIDATION = "outputs/v18/staged_factor_technical/V18_25A_R25C_CURRENT_STAGED_TECHNICAL_VALIDATION.csv"
OUT_CROSS = "outputs/v18/staged_factor_technical/V18_25A_R25C_CURRENT_CROSS_SOURCE_TARGET_AUDIT.csv"
OUT_MERGE_PLAN = "outputs/v18/staged_factor_technical/V18_25A_R25C_CURRENT_OFFICIAL_MERGE_PLAN.csv"
OUT_BACKUP_PLAN = "outputs/v18/staged_factor_technical/V18_25A_R25C_CURRENT_REQUIRED_BACKUP_PLAN.csv"
OUT_BLOCKERS = "outputs/v18/staged_factor_technical/V18_25A_R25C_CURRENT_BLOCKERS_AND_HOLDS.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R25C_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R25C_CURRENT_STAGED_VALIDATION_MERGE_PLAN_REPORT.md"

FACTOR_VALIDATION_FIELDS = [
    "ticker", "target_present", "row_present", "duplicate_count", "schema_compatible", "score_column",
    "score_present", "score_numeric", "price_cache_readable", "rolling_ledger_present", "artifact_or_invalid_symbol",
    "r25b_audit_success", "valid", "reason",
]
TECH_VALIDATION_FIELDS = FACTOR_VALIDATION_FIELDS[:]
CROSS_FIELDS = [
    "audit_item", "status", "expected_value", "actual_value", "reason",
]
MERGE_PLAN_FIELDS = [
    "ticker", "factor_merge_action", "technical_merge_action", "factor_current_row_exists",
    "technical_current_row_exists", "staged_factor_valid", "staged_technical_valid", "merge_allowed_next",
    "reason", "required_backup_group", "source_staged_factor_file", "source_staged_technical_file",
    "target_factor_pack_file", "target_technical_timing_file",
]
BACKUP_PLAN_FIELDS = [
    "plan_item", "required", "path_or_value", "notes",
]
BLOCKER_FIELDS = [
    "ticker", "blocker_type", "source", "reason", "next_action",
]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "RUN_ID", "MAX_TICKERS", "EXPECTED_TARGET_COUNT", "TARGET_ROW_COUNT",
    "STAGED_FACTOR_ROW_COUNT", "STAGED_TECHNICAL_ROW_COUNT", "FACTOR_VALIDATION_PASS_COUNT",
    "FACTOR_VALIDATION_FAIL_COUNT", "TECHNICAL_VALIDATION_PASS_COUNT", "TECHNICAL_VALIDATION_FAIL_COUNT",
    "CROSS_SOURCE_TARGET_MATCH", "STAGED_FACTOR_TICKER_SET_MATCH_TARGETS", "STAGED_TECHNICAL_TICKER_SET_MATCH_TARGETS",
    "FACTOR_TECHNICAL_TICKER_SET_MATCH", "DUPLICATE_FACTOR_TICKER_COUNT", "DUPLICATE_TECHNICAL_TICKER_COUNT",
    "NULL_FACTOR_SCORE_COUNT", "NULL_TECHNICAL_SCORE_COUNT", "PRICE_CACHE_RECHECK_SUCCESS_COUNT",
    "PRICE_CACHE_RECHECK_FAIL_COUNT", "ROLLING_LEDGER_TARGET_PRESENT_COUNT", "ROLLING_LEDGER_TARGET_MISSING_COUNT",
    "FACTOR_SCHEMA_COMPATIBLE", "TECHNICAL_SCHEMA_COMPATIBLE", "MERGE_PLAN_ROW_COUNT", "MERGE_ALLOWED_NEXT_COUNT",
    "MERGE_BLOCKED_COUNT", "FACTOR_APPEND_NEW_COUNT", "FACTOR_UPDATE_EXISTING_COUNT", "TECHNICAL_APPEND_NEW_COUNT",
    "TECHNICAL_UPDATE_EXISTING_COUNT", "BACKUP_PLAN_PATH", "MERGE_PLAN_PATH", "BLOCKERS_AND_HOLDS_PATH",
    "OFFICIAL_FACTOR_PACK_MERGE_ALLOWED_NEXT", "OFFICIAL_TECHNICAL_TIMING_MERGE_ALLOWED_NEXT", "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE", "AUTO_SELL", "EXTERNAL_FETCH_EXECUTED", "BACKTEST_EXECUTED", "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED", "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "TIER_FILES_MODIFIED",
    "OFFICIAL_DECISION_MODIFIED", "VALIDATION_FAIL_COUNT", "FORBIDDEN_MODIFIED", "NEXT_RECOMMENDED_STEP",
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
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def to_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        return float(text) if text else None
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
    return {str(p.relative_to(root)): file_sig(p) for p in root.rglob("*") if p.is_file()}


def duplicate_counts(rows: List[Dict[str, str]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker:
            counts[ticker] = counts.get(ticker, 0) + 1
    return {ticker: count for ticker, count in counts.items() if count > 1}


def ticker_set(rows: List[Dict[str, str]]) -> set[str]:
    return {norm_ticker(row.get("ticker")) for row in rows if norm_ticker(row.get("ticker"))}


def is_invalid_symbol(ticker: str) -> bool:
    if ticker in {"", "TICKER", "TICKERS", "SYMBOL", "SYMBOLS", "NULL", "NAN"}:
        return True
    return re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,14}", ticker) is None


def score_column(fields: Sequence[str], candidates: Sequence[str]) -> str:
    by_lower = {field.lower(): field for field in fields}
    for candidate in candidates:
        if candidate.lower() in by_lower:
            return by_lower[candidate.lower()]
    return ""


def price_cache_readable(path: Path) -> bool:
    rows, fields = read_csv(path)
    field_set = {field.lower() for field in fields}
    return bool(rows) and {"date", "close"}.issubset(field_set)


def audit_success(rows: List[Dict[str, str]], ticker: str, success_field: str) -> bool:
    for row in rows:
        if norm_ticker(row.get("ticker")) == ticker:
            return is_true(row.get(success_field)) or str(row.get("status", "")).upper().endswith("_ROW_STAGED")
    return False


def schema_pass_from_r25b(schema_rows: List[Dict[str, str]], item: str) -> bool:
    for row in schema_rows:
        if str(row.get("schema_item", "")).strip().lower() == item.lower():
            return is_true(row.get("value")) or str(row.get("status", "")).upper() == "PASS"
    return False


def validation_row(
    ticker: str,
    staged_rows_by_ticker: Dict[str, Dict[str, str]],
    dupes: Dict[str, int],
    target_tickers: set[str],
    score_col: str,
    schema_compatible: bool,
    price_cache_ok: bool,
    ledger_present: bool,
    audit_ok: bool,
) -> Dict[str, object]:
    row = staged_rows_by_ticker.get(ticker, {})
    score = to_float(row.get(score_col)) if score_col else None
    score_raw = str(row.get(score_col, "")).strip() if score_col else ""
    reasons: List[str] = []
    checks = {
        "target_present": ticker in target_tickers,
        "row_present": bool(row),
        "duplicate_count": dupes.get(ticker, 0),
        "schema_compatible": schema_compatible,
        "score_column": score_col,
        "score_present": bool(score_raw),
        "score_numeric": score is not None,
        "price_cache_readable": price_cache_ok,
        "rolling_ledger_present": ledger_present,
        "artifact_or_invalid_symbol": is_invalid_symbol(ticker),
        "r25b_audit_success": audit_ok,
    }
    if not checks["target_present"]:
        reasons.append("ticker not in approved R25B target list")
    if not checks["row_present"]:
        reasons.append("staged row missing")
    if checks["duplicate_count"]:
        reasons.append("duplicate staged ticker")
    if not checks["schema_compatible"]:
        reasons.append("staged schema is not compatible with current official schema")
    if not checks["score_column"]:
        reasons.append("score column missing")
    elif not checks["score_present"]:
        reasons.append("score is null")
    elif not checks["score_numeric"]:
        reasons.append("score is non-numeric")
    if not checks["price_cache_readable"]:
        reasons.append("price cache unreadable")
    if not checks["rolling_ledger_present"]:
        reasons.append("target missing from rolling ledger")
    if checks["artifact_or_invalid_symbol"]:
        reasons.append("invalid or artifact ticker symbol")
    if not checks["r25b_audit_success"]:
        reasons.append("R25B audit did not confirm successful staged build")

    checks["valid"] = not reasons
    checks["reason"] = "; ".join(reasons)
    checks["ticker"] = ticker
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--max-tickers", type=int, default=93)
    parser.add_argument("--plan-only", action="store_true", default=True)
    parser.add_argument("--allow-official-merge", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R25C_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    before = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": tree_sig(root / "outputs/v18/factor_pack"),
        "technical": tree_sig(root / "outputs/v18/technical_timing"),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
    }

    input_paths = [IN_TARGETS, IN_FACTOR, IN_TECH, IN_FACTOR_AUDIT, IN_TECH_AUDIT, IN_SCHEMA, FACTOR_CURRENT, TECH_CURRENT, LEDGER]
    missing_inputs = [path for path in input_paths if not (root / path).exists()]

    targets, target_fields = read_csv(root / IN_TARGETS)
    factor_rows, factor_fields = read_csv(root / IN_FACTOR)
    tech_rows, tech_fields = read_csv(root / IN_TECH)
    factor_audit, _ = read_csv(root / IN_FACTOR_AUDIT)
    tech_audit, _ = read_csv(root / IN_TECH_AUDIT)
    schema_rows, _ = read_csv(root / IN_SCHEMA)
    factor_current, factor_current_fields = read_csv(root / FACTOR_CURRENT)
    tech_current, tech_current_fields = read_csv(root / TECH_CURRENT)
    ledger_rows, _ = read_csv(root / LEDGER)

    target_tickers = [norm_ticker(row.get("ticker")) for row in targets if norm_ticker(row.get("ticker"))]
    target_ticker_set = set(target_tickers)
    target_tickers = target_tickers[: max(args.max_tickers, 0)]
    target_ticker_set = set(target_tickers)
    factor_tickers = ticker_set(factor_rows)
    tech_tickers = ticker_set(tech_rows)
    ledger_tickers = ticker_set(ledger_rows)
    factor_current_tickers = ticker_set(factor_current)
    tech_current_tickers = ticker_set(tech_current)

    factor_dupes = duplicate_counts(factor_rows)
    tech_dupes = duplicate_counts(tech_rows)
    factor_score_col = score_column(factor_fields, ["factor_score", "factor_pack_score", "F010_XSEC_COMPOSITE_RANK"])
    tech_score_col = score_column(tech_fields, ["technical_timing_score", "technical_score"])
    factor_schema_compatible = (
        bool(factor_fields)
        and bool(factor_current_fields)
        and list(factor_fields) == list(factor_current_fields)
        and schema_pass_from_r25b(schema_rows, "factor_schema_compatible")
    )
    tech_schema_compatible = (
        bool(tech_fields)
        and bool(tech_current_fields)
        and list(tech_fields) == list(tech_current_fields)
        and schema_pass_from_r25b(schema_rows, "technical_schema_compatible")
    )

    price_cache_ok_by_ticker = {
        ticker: price_cache_readable(root / PRICE_CACHE / f"{ticker}.csv") for ticker in target_tickers
    }
    ledger_present_by_ticker = {ticker: ticker in ledger_tickers for ticker in target_tickers}

    factor_by_ticker = {norm_ticker(row.get("ticker")): row for row in factor_rows if norm_ticker(row.get("ticker"))}
    tech_by_ticker = {norm_ticker(row.get("ticker")): row for row in tech_rows if norm_ticker(row.get("ticker"))}
    factor_validation = [
        validation_row(
            ticker,
            factor_by_ticker,
            factor_dupes,
            target_ticker_set,
            factor_score_col,
            factor_schema_compatible,
            price_cache_ok_by_ticker.get(ticker, False),
            ledger_present_by_ticker.get(ticker, False),
            audit_success(factor_audit, ticker, "build_success"),
        )
        for ticker in target_tickers
    ]
    tech_validation = [
        validation_row(
            ticker,
            tech_by_ticker,
            tech_dupes,
            target_ticker_set,
            tech_score_col,
            tech_schema_compatible,
            price_cache_ok_by_ticker.get(ticker, False),
            ledger_present_by_ticker.get(ticker, False),
            audit_success(tech_audit, ticker, "build_success"),
        )
        for ticker in target_tickers
    ]

    factor_valid_by_ticker = {str(row["ticker"]): bool(row["valid"]) for row in factor_validation}
    tech_valid_by_ticker = {str(row["ticker"]): bool(row["valid"]) for row in tech_validation}
    factor_fail_by_ticker = {str(row["ticker"]): str(row["reason"]) for row in factor_validation if not row["valid"]}
    tech_fail_by_ticker = {str(row["ticker"]): str(row["reason"]) for row in tech_validation if not row["valid"]}

    staged_factor_match_targets = factor_tickers == target_ticker_set
    staged_tech_match_targets = tech_tickers == target_ticker_set
    factor_tech_match = factor_tickers == tech_tickers
    cross_source_target_match = staged_factor_match_targets and staged_tech_match_targets and factor_tech_match
    null_factor_scores = sum(1 for row in factor_rows if not str(row.get(factor_score_col, "")).strip()) if factor_score_col else len(factor_rows)
    null_tech_scores = sum(1 for row in tech_rows if not str(row.get(tech_score_col, "")).strip()) if tech_score_col else len(tech_rows)

    cross_rows = [
        {"audit_item": "expected_target_count", "status": "PASS" if len(target_tickers) == EXPECTED_TARGET_COUNT else "FAIL", "expected_value": EXPECTED_TARGET_COUNT, "actual_value": len(target_tickers), "reason": ""},
        {"audit_item": "staged_factor_row_count", "status": "PASS" if len(factor_rows) == len(target_tickers) else "FAIL", "expected_value": len(target_tickers), "actual_value": len(factor_rows), "reason": ""},
        {"audit_item": "staged_technical_row_count", "status": "PASS" if len(tech_rows) == len(target_tickers) else "FAIL", "expected_value": len(target_tickers), "actual_value": len(tech_rows), "reason": ""},
        {"audit_item": "staged_factor_ticker_set_match_targets", "status": "PASS" if staged_factor_match_targets else "FAIL", "expected_value": "TARGET_SET", "actual_value": str(staged_factor_match_targets).upper(), "reason": ""},
        {"audit_item": "staged_technical_ticker_set_match_targets", "status": "PASS" if staged_tech_match_targets else "FAIL", "expected_value": "TARGET_SET", "actual_value": str(staged_tech_match_targets).upper(), "reason": ""},
        {"audit_item": "factor_technical_ticker_set_match", "status": "PASS" if factor_tech_match else "FAIL", "expected_value": "MATCH", "actual_value": str(factor_tech_match).upper(), "reason": ""},
        {"audit_item": "factor_schema_compatible", "status": "PASS" if factor_schema_compatible else "FAIL", "expected_value": "TRUE", "actual_value": str(factor_schema_compatible).upper(), "reason": ""},
        {"audit_item": "technical_schema_compatible", "status": "PASS" if tech_schema_compatible else "FAIL", "expected_value": "TRUE", "actual_value": str(tech_schema_compatible).upper(), "reason": ""},
    ]

    merge_rows: List[Dict[str, object]] = []
    blockers: List[Dict[str, object]] = []
    for ticker in target_tickers:
        factor_valid = factor_valid_by_ticker.get(ticker, False)
        tech_valid = tech_valid_by_ticker.get(ticker, False)
        allowed = factor_valid and tech_valid
        reason = "validated for R25D official merge" if allowed else "; ".join(
            part for part in [factor_fail_by_ticker.get(ticker, ""), tech_fail_by_ticker.get(ticker, "")] if part
        )
        factor_exists = ticker in factor_current_tickers
        tech_exists = ticker in tech_current_tickers
        merge_rows.append({
            "ticker": ticker,
            "factor_merge_action": ("UPDATE_EXISTING_ROW" if factor_exists else "APPEND_NEW_ROW") if factor_valid else "BLOCKED",
            "technical_merge_action": ("UPDATE_EXISTING_ROW" if tech_exists else "APPEND_NEW_ROW") if tech_valid else "BLOCKED",
            "factor_current_row_exists": str(factor_exists).upper(),
            "technical_current_row_exists": str(tech_exists).upper(),
            "staged_factor_valid": str(factor_valid).upper(),
            "staged_technical_valid": str(tech_valid).upper(),
            "merge_allowed_next": str(allowed).upper(),
            "reason": reason,
            "required_backup_group": "V18_25A_R25D_FACTOR_TECHNICAL_BACKUP",
            "source_staged_factor_file": IN_FACTOR,
            "source_staged_technical_file": IN_TECH,
            "target_factor_pack_file": FACTOR_CURRENT,
            "target_technical_timing_file": TECH_CURRENT,
        })
        if not allowed:
            blockers.append({
                "ticker": ticker,
                "blocker_type": "MERGE_BLOCKED",
                "source": "R25C_VALIDATION",
                "reason": reason,
                "next_action": "Fix staged rows or builder logic before R25D.",
            })

    for source_name, rows, success_field in [
        ("R25B_FACTOR_BUILD_AUDIT", factor_audit, "build_success"),
        ("R25B_TECHNICAL_BUILD_AUDIT", tech_audit, "build_success"),
    ]:
        for row in rows:
            ticker = norm_ticker(row.get("ticker"))
            if ticker and not audit_success(rows, ticker, success_field):
                blockers.append({
                    "ticker": ticker,
                    "blocker_type": "R25B_AUDIT_HOLD",
                    "source": source_name,
                    "reason": row.get("error_message") or row.get("status") or "R25B audit did not pass",
                    "next_action": "Review R25B build audit before R25D.",
                })

    backup_dir = "archive/v18/factor_technical_backups/V18_25A_R25D_YYYYMMDD_HHMMSS"
    backup_rows = [
        {"plan_item": "factor pack current file backup required", "required": "TRUE", "path_or_value": FACTOR_CURRENT, "notes": "R25D must copy before modifying."},
        {"plan_item": "technical timing current file backup required", "required": "TRUE", "path_or_value": TECH_CURRENT, "notes": "R25D must copy before modifying."},
        {"plan_item": "restore script required", "required": "TRUE", "path_or_value": f"{backup_dir}/restore_v18_25A_R25D_factor_technical.ps1", "notes": "R25D must generate restore instructions before merge."},
        {"plan_item": "expected backup directory", "required": "TRUE", "path_or_value": backup_dir, "notes": "Timestamp must be resolved by R25D at execution time."},
        {"plan_item": "R25D would modify", "required": "TRUE", "path_or_value": FACTOR_CURRENT, "notes": ""},
        {"plan_item": "R25D would modify", "required": "TRUE", "path_or_value": TECH_CURRENT, "notes": ""},
        {"plan_item": "R25D must not modify", "required": "TRUE", "path_or_value": PRICE_CACHE, "notes": "Official price cache remains read-only."},
        {"plan_item": "R25D must not modify", "required": "TRUE", "path_or_value": LEDGER, "notes": "Rolling ledger remains read-only."},
        {"plan_item": "R25D must not modify", "required": "TRUE", "path_or_value": "outputs/v18/tier_migration", "notes": ""},
        {"plan_item": "R25D must not modify", "required": "TRUE", "path_or_value": "outputs/v18/daily_decision", "notes": ""},
        {"plan_item": "R25D must not modify", "required": "TRUE", "path_or_value": "outputs/v18/market_regime", "notes": "No official market proxy changes."},
        {"plan_item": "R25D must not modify", "required": "TRUE", "path_or_value": "outputs/v18/staged_backfill", "notes": "No staged backfill price changes."},
    ]

    write_csv(root / OUT_FACTOR_VALIDATION, factor_validation, FACTOR_VALIDATION_FIELDS)
    write_csv(root / OUT_TECH_VALIDATION, tech_validation, TECH_VALIDATION_FIELDS)
    write_csv(root / OUT_CROSS, cross_rows, CROSS_FIELDS)
    write_csv(root / OUT_MERGE_PLAN, merge_rows, MERGE_PLAN_FIELDS)
    write_csv(root / OUT_BACKUP_PLAN, backup_rows, BACKUP_PLAN_FIELDS)
    write_csv(root / OUT_BLOCKERS, blockers, BLOCKER_FIELDS)

    after = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": tree_sig(root / "outputs/v18/factor_pack"),
        "technical": tree_sig(root / "outputs/v18/technical_timing"),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
    }
    mods = {key: before[key] != after[key] for key in before}
    forbidden = any(mods.values())

    factor_pass = sum(1 for row in factor_validation if row["valid"])
    tech_pass = sum(1 for row in tech_validation if row["valid"])
    factor_fail = len(factor_validation) - factor_pass
    tech_fail = len(tech_validation) - tech_pass
    merge_allowed = sum(1 for row in merge_rows if row["merge_allowed_next"] == "TRUE")
    merge_blocked = len(merge_rows) - merge_allowed
    factor_append = sum(1 for row in merge_rows if row["factor_merge_action"] == "APPEND_NEW_ROW")
    factor_update = sum(1 for row in merge_rows if row["factor_merge_action"] == "UPDATE_EXISTING_ROW")
    tech_append = sum(1 for row in merge_rows if row["technical_merge_action"] == "APPEND_NEW_ROW")
    tech_update = sum(1 for row in merge_rows if row["technical_merge_action"] == "UPDATE_EXISTING_ROW")
    price_ok = sum(1 for value in price_cache_ok_by_ticker.values() if value)
    price_fail = len(target_tickers) - price_ok
    ledger_present = sum(1 for value in ledger_present_by_ticker.values() if value)
    ledger_missing = len(target_tickers) - ledger_present

    status = STATUS_OK
    if args.allow_official_merge:
        status = STATUS_MERGE_REFUSED
    elif missing_inputs:
        status = STATUS_INPUTS_MISSING
    elif len(target_tickers) != EXPECTED_TARGET_COUNT or len(factor_rows) != len(target_tickers) or len(tech_rows) != len(target_tickers):
        status = STATUS_ROW_COUNT
    elif not cross_source_target_match:
        status = STATUS_TARGET_SET
    elif not factor_schema_compatible or not tech_schema_compatible:
        status = STATUS_SCHEMA
    elif null_factor_scores or null_tech_scores or not factor_score_col or not tech_score_col:
        status = STATUS_SCORE
    elif merge_blocked:
        status = STATUS_MERGE_BLOCKED
    elif factor_fail or tech_fail:
        status = STATUS_PARTIAL_FAIL

    validation_fail_count = int(
        bool(missing_inputs)
        or len(target_tickers) != EXPECTED_TARGET_COUNT
        or len(factor_rows) != len(target_tickers)
        or len(tech_rows) != len(target_tickers)
        or not cross_source_target_match
        or not factor_schema_compatible
        or not tech_schema_compatible
        or bool(null_factor_scores)
        or bool(null_tech_scores)
        or bool(merge_blocked)
        or forbidden
        or args.allow_official_merge
    )
    next_step = (
        "R25D: Official factor pack and technical timing merge with backup for validated staged rows only."
        if status == STATUS_OK
        else "Fix staged rows or builder logic before R25D."
    )
    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "MAX_TICKERS": args.max_tickers,
        "EXPECTED_TARGET_COUNT": EXPECTED_TARGET_COUNT,
        "TARGET_ROW_COUNT": len(target_tickers),
        "STAGED_FACTOR_ROW_COUNT": len(factor_rows),
        "STAGED_TECHNICAL_ROW_COUNT": len(tech_rows),
        "FACTOR_VALIDATION_PASS_COUNT": factor_pass,
        "FACTOR_VALIDATION_FAIL_COUNT": factor_fail,
        "TECHNICAL_VALIDATION_PASS_COUNT": tech_pass,
        "TECHNICAL_VALIDATION_FAIL_COUNT": tech_fail,
        "CROSS_SOURCE_TARGET_MATCH": str(cross_source_target_match).upper(),
        "STAGED_FACTOR_TICKER_SET_MATCH_TARGETS": str(staged_factor_match_targets).upper(),
        "STAGED_TECHNICAL_TICKER_SET_MATCH_TARGETS": str(staged_tech_match_targets).upper(),
        "FACTOR_TECHNICAL_TICKER_SET_MATCH": str(factor_tech_match).upper(),
        "DUPLICATE_FACTOR_TICKER_COUNT": len(factor_dupes),
        "DUPLICATE_TECHNICAL_TICKER_COUNT": len(tech_dupes),
        "NULL_FACTOR_SCORE_COUNT": null_factor_scores,
        "NULL_TECHNICAL_SCORE_COUNT": null_tech_scores,
        "PRICE_CACHE_RECHECK_SUCCESS_COUNT": price_ok,
        "PRICE_CACHE_RECHECK_FAIL_COUNT": price_fail,
        "ROLLING_LEDGER_TARGET_PRESENT_COUNT": ledger_present,
        "ROLLING_LEDGER_TARGET_MISSING_COUNT": ledger_missing,
        "FACTOR_SCHEMA_COMPATIBLE": str(factor_schema_compatible).upper(),
        "TECHNICAL_SCHEMA_COMPATIBLE": str(tech_schema_compatible).upper(),
        "MERGE_PLAN_ROW_COUNT": len(merge_rows),
        "MERGE_ALLOWED_NEXT_COUNT": merge_allowed,
        "MERGE_BLOCKED_COUNT": merge_blocked,
        "FACTOR_APPEND_NEW_COUNT": factor_append,
        "FACTOR_UPDATE_EXISTING_COUNT": factor_update,
        "TECHNICAL_APPEND_NEW_COUNT": tech_append,
        "TECHNICAL_UPDATE_EXISTING_COUNT": tech_update,
        "BACKUP_PLAN_PATH": OUT_BACKUP_PLAN,
        "MERGE_PLAN_PATH": OUT_MERGE_PLAN,
        "BLOCKERS_AND_HOLDS_PATH": OUT_BLOCKERS,
        "OFFICIAL_FACTOR_PACK_MERGE_ALLOWED_NEXT": str(status == STATUS_OK).upper(),
        "OFFICIAL_TECHNICAL_TIMING_MERGE_ALLOWED_NEXT": str(status == STATUS_OK).upper(),
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "PRICE_CACHE_MODIFIED": str(mods["price"]).upper(),
        "ROLLING_LEDGER_MODIFIED": str(mods["ledger"]).upper(),
        "FACTOR_PACK_MODIFIED": str(mods["factor"]).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(mods["technical"]).upper(),
        "TIER_FILES_MODIFIED": str(mods["tier"]).upper(),
        "OFFICIAL_DECISION_MODIFIED": str(mods["decision"]).upper(),
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden).upper(),
        "NEXT_RECOMMENDED_STEP": next_step,
    }
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    report = "\n".join([
        "# V18.25A R25C Staged Validation Merge Plan Report",
        "",
        f"STATUS: {status}",
        f"MODE: {MODE}",
        f"RUN_ID: {run_id}",
        "",
        f"- target_row_count: {len(target_tickers)}",
        f"- staged_factor_row_count: {len(factor_rows)}",
        f"- staged_technical_row_count: {len(tech_rows)}",
        f"- factor_validation_pass/fail: {factor_pass}/{factor_fail}",
        f"- technical_validation_pass/fail: {tech_pass}/{tech_fail}",
        f"- merge_allowed_next_count: {merge_allowed}",
        f"- merge_blocked_count: {merge_blocked}",
        "",
        "R25C generated an official merge plan only. It did not merge staged rows into official factor or technical files.",
        "",
    ])
    write_text(root / OUT_REPORT, report)
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
