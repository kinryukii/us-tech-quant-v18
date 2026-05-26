from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R27L_POST_PROMOTION_VALIDATION_SIGNAL_FREEZE_READY"
STATUS_WARN = "WARN_V18_25A_R27L_POST_PROMOTION_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_25A_R27L_FORBIDDEN_MODIFIED"

MODE = "READ_ONLY_POST_PROMOTION_VALIDATION_SIGNAL_FREEZE_READINESS"

TARGET_TICKERS = ["RDDT", "TLN"]
TARGET_SET = set(TARGET_TICKERS)
EXPECTED_R27K_STATUS = "OK_V18_25A_R27K_RANKED_CANDIDATES_PROMOTION_READY"

R27K_READ_FIRST = "outputs/v18/ops/V18_25A_R27K_READ_FIRST.txt"
CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
FACTOR_PACK = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_TIMING = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
PRICE_CACHE_DIR = "state/v18/price_cache"
ROLLING_LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
SIGNAL_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"

OUT_DIR = "outputs/v18/candidates"
OUT_POST_PROMOTION_VALIDATION = f"{OUT_DIR}/V18_25A_R27L_CURRENT_POST_PROMOTION_VALIDATION.csv"
OUT_FULL_JOIN_AUDIT = f"{OUT_DIR}/V18_25A_R27L_CURRENT_FULL_CANDIDATE_JOIN_AUDIT.csv"
OUT_SIGNAL_AUDIT = f"{OUT_DIR}/V18_25A_R27L_CURRENT_SIGNAL_FREEZE_READINESS_AUDIT.csv"
OUT_SUMMARY = f"{OUT_DIR}/V18_25A_R27L_CURRENT_SUMMARY.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R27L_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R27L_CURRENT_POST_PROMOTION_VALIDATION_SIGNAL_FREEZE_READINESS_REPORT.md"

POST_VALIDATION_FIELDS = [
    "ticker",
    "rank_valid",
    "rank",
    "score_present",
    "current_in_factor_pack",
    "current_in_technical_timing",
    "current_in_price_cache",
    "current_in_rolling_ledger",
    "validation_status",
    "error_message",
]

FULL_JOIN_FIELDS = [
    "ticker",
    "current_in_factor_pack",
    "current_in_technical_timing",
    "current_in_price_cache",
    "current_in_rolling_ledger",
    "join_ready",
    "reason",
]

SIGNAL_AUDIT_FIELDS = [
    "latest_signal_freeze_run_id",
    "latest_signal_freeze_ticker_count",
    "latest_signal_freeze_distinct_ticker_count",
    "latest_signal_freeze_duplicate_ticker_count",
    "latest_signal_freeze_matches_current_candidates",
    "targets_present_in_latest_signal_freeze_count",
    "signal_freeze_refresh_recommended",
    "notes",
]

SUMMARY_FIELDS = ["metric", "value", "expected", "status", "notes"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R27K_STATUS",
    "CURRENT_RANKED_CANDIDATE_ROW_COUNT",
    "TARGET_TICKER_COUNT",
    "TARGET_TICKERS",
    "TARGETS_PRESENT_COUNT",
    "DUPLICATE_TICKER_COUNT",
    "TARGET_SCORE_PRESENT_COUNT",
    "FACTOR_PRESENT_COUNT_FOR_TARGETS",
    "TECHNICAL_PRESENT_COUNT_FOR_TARGETS",
    "PRICE_CACHE_PRESENT_COUNT_FOR_TARGETS",
    "ROLLING_LEDGER_SUCCESS_COUNT_FOR_TARGETS",
    "FULL_CANDIDATE_FACTOR_JOIN_MISSING_COUNT",
    "FULL_CANDIDATE_TECHNICAL_JOIN_MISSING_COUNT",
    "FULL_CANDIDATE_PRICE_CACHE_MISSING_COUNT",
    "FULL_CANDIDATE_ROLLING_LEDGER_MISSING_COUNT",
    "LATEST_SIGNAL_FREEZE_RUN_ID",
    "LATEST_SIGNAL_FREEZE_TICKER_COUNT",
    "LATEST_SIGNAL_FREEZE_MATCHES_CURRENT_CANDIDATES",
    "TARGETS_PRESENT_IN_LATEST_SIGNAL_FREEZE_COUNT",
    "SIGNAL_FREEZE_REFRESH_RECOMMENDED",
    "CANDIDATES_CURRENT_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED",
    "SIGNAL_FREEZE_EXECUTED",
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
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def read_first_value(path: Path, key: str) -> str:
    prefix = f"{key}:"
    for line in read_text(path).splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def non_null(value: object) -> bool:
    return str(value or "").strip() not in {"", "nan", "NaN", "None", "NULL"}


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


def build_ticker_map(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {norm_ticker(row.get("ticker")): row for row in rows if norm_ticker(row.get("ticker"))}


def ticker_counts(rows: Sequence[Dict[str, str]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker:
            counts[ticker] = counts.get(ticker, 0) + 1
    return counts


def duplicate_ticker_count(rows: Sequence[Dict[str, str]]) -> int:
    return sum(max(0, count - 1) for count in ticker_counts(rows).values())


def parse_run_timestamp(value: str) -> dt.datetime:
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d_%H%M%S", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(text, fmt)
        except Exception:
            continue
    return dt.datetime.min


def parse_date(value: object) -> Optional[dt.date]:
    text = str(value or "").strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt).date()
        except Exception:
            continue
    return None


def latest_signal_slice(rows: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
    if not rows:
        return "", []
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("run_id") or "").strip(), []).append(row)
    latest_run_id = max(grouped.keys(), key=lambda run_id: (
        parse_run_timestamp(grouped[run_id][0].get("run_timestamp", "")),
        run_id,
    ))
    return latest_run_id, grouped[latest_run_id]


def price_cache_present(root: Path, ticker: str) -> bool:
    path = root / PRICE_CACHE_DIR / f"{ticker}.csv"
    return path.exists() and path.is_file()


def rank_valid(rows: Sequence[Dict[str, str]]) -> bool:
    ranks = [to_int(row.get("rank"), -1) for row in rows]
    return len(ranks) == len(set(ranks)) and sorted(ranks) == list(range(1, len(rows) + 1))


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object], validation_rows: Sequence[Dict[str, object]], join_rows: Sequence[Dict[str, object]], signal_rows: Sequence[Dict[str, object]]) -> str:
    validation_text = "\n".join(f"- {row['ticker']}: {row['validation_status']}" for row in validation_rows)
    join_text = "\n".join(f"- {row['ticker']}: {row['join_ready']}" for row in join_rows[:10])
    signal_text = "\n".join(
        f"- run {row['latest_signal_freeze_run_id']}: match={row['latest_signal_freeze_matches_current_candidates']}, refresh={row['signal_freeze_refresh_recommended']}"
        for row in signal_rows
    )
    return "\n".join(
        [
            "# V18.25A-R27L Post-Promotion Validation + Signal-Freeze Readiness",
            "",
            f"- STATUS: {values['STATUS']}",
            f"- MODE: {values['MODE']}",
            f"- RUN_ID: {values['RUN_ID']}",
            f"- R27K_STATUS: {values['R27K_STATUS']}",
            "",
            "## Validation",
            "",
            validation_text if validation_text else "- None.",
            "",
            "## Join Audit",
            "",
            join_text if join_text else "- None.",
            "",
            "## Signal Freeze",
            "",
            signal_text if signal_text else "- None.",
            "",
            "## Guardrails",
            "",
            f"- CANDIDATES_CURRENT_MODIFIED: {values['CANDIDATES_CURRENT_MODIFIED']}",
            f"- FACTOR_PACK_MODIFIED: {values['FACTOR_PACK_MODIFIED']}",
            f"- TECHNICAL_TIMING_MODIFIED: {values['TECHNICAL_TIMING_MODIFIED']}",
            f"- PRICE_CACHE_MODIFIED: {values['PRICE_CACHE_MODIFIED']}",
            f"- ROLLING_LEDGER_MODIFIED: {values['ROLLING_LEDGER_MODIFIED']}",
            f"- SIGNAL_FREEZE_EXECUTED: {values['SIGNAL_FREEZE_EXECUTED']}",
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
    run_id = f"V18_25A_R27L_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    today = dt.date.today()

    current_before = file_sig(root / CURRENT_CANDIDATES)
    factor_before = file_sig(root / FACTOR_PACK)
    tech_before = file_sig(root / TECH_TIMING)
    price_before = tree_sig(root / PRICE_CACHE_DIR)
    ledger_before = file_sig(root / ROLLING_LEDGER)
    signal_before = file_sig(root / SIGNAL_LEDGER)

    blockers: List[str] = []
    r27k_status = read_first_value(root / R27K_READ_FIRST, "STATUS")
    if not (root / R27K_READ_FIRST).exists():
        blockers.append(f"missing required input: {R27K_READ_FIRST}")
    if r27k_status != EXPECTED_R27K_STATUS:
        blockers.append(f"R27K status is {r27k_status or 'MISSING'}")
    if read_first_value(root / R27K_READ_FIRST, "CURRENT_ROW_COUNT_AFTER") != "252":
        blockers.append("R27K current row count after promotion is not 252")
    if read_first_value(root / R27K_READ_FIRST, "TARGETS_PRESENT_AFTER_COUNT") != "2":
        blockers.append("R27K target presence count after promotion is not 2")
    if read_first_value(root / R27K_READ_FIRST, "DUPLICATE_TICKER_COUNT_AFTER") != "0":
        blockers.append("R27K duplicate ticker count after promotion is not 0")
    if read_first_value(root / R27K_READ_FIRST, "FORBIDDEN_MODIFIED") != "FALSE":
        blockers.append("R27K forbidden modified flag was not FALSE")

    current_rows, current_fields = read_csv(root / CURRENT_CANDIDATES)
    factor_rows, factor_fields = read_csv(root / FACTOR_PACK)
    tech_rows, tech_fields = read_csv(root / TECH_TIMING)
    ledger_rows, ledger_fields = read_csv(root / ROLLING_LEDGER)
    signal_rows, signal_fields = read_csv(root / SIGNAL_LEDGER)

    current_count = len(current_rows)
    current_dupes = duplicate_ticker_count(current_rows)
    current_by = build_ticker_map(current_rows)
    factor_by = build_ticker_map(factor_rows)
    tech_by = build_ticker_map(tech_rows)
    ledger_by = build_ticker_map(ledger_rows)
    signal_latest_run_id, signal_latest_rows = latest_signal_slice(signal_rows)
    signal_latest_set = {norm_ticker(row.get("ticker")) for row in signal_latest_rows if norm_ticker(row.get("ticker"))}
    current_set = {norm_ticker(row.get("ticker")) for row in current_rows if norm_ticker(row.get("ticker"))}
    signal_latest_distinct = len(signal_latest_set)
    signal_latest_dupes = duplicate_ticker_count(signal_latest_rows)
    signal_matches_current = signal_latest_set == current_set and bool(signal_latest_run_id)
    targets_present_in_latest = sum(1 for ticker in TARGET_TICKERS if ticker in signal_latest_set)
    signal_freeze_refresh_recommended = not signal_matches_current

    rank_ok = rank_valid(current_rows)
    score_present_count = sum(1 for row in current_rows if non_null(row.get("composite_candidate_score")))
    factor_present_targets = sum(1 for ticker in TARGET_TICKERS if ticker in factor_by)
    technical_present_targets = sum(1 for ticker in TARGET_TICKERS if ticker in tech_by)
    price_present_targets = sum(1 for ticker in TARGET_TICKERS if price_cache_present(root, ticker))
    ledger_success_targets = 0
    for ticker in TARGET_TICKERS:
        row = ledger_by.get(ticker, {})
        status = str(row.get("last_scan_status") or row.get("scan_status") or row.get("status") or "").strip().upper()
        success_date = str(row.get("last_success_scan_date") or "").strip()
        if status in {"SUCCESS_LOCAL_PRICE_FULL_HISTORY", "LOCAL_PRICE_SCAN_SUCCESS"} and success_date == today.isoformat():
            ledger_success_targets += 1

    join_rows: List[Dict[str, object]] = []
    validation_rows: List[Dict[str, object]] = []
    factor_join_missing = 0
    tech_join_missing = 0
    price_join_missing = 0
    ledger_join_missing = 0
    for row in current_rows:
        ticker = norm_ticker(row.get("ticker"))
        factor_present = ticker in factor_by
        tech_present = ticker in tech_by
        price_present = price_cache_present(root, ticker)
        ledger_present = ticker in ledger_by
        factor_join_missing += 0 if factor_present else 1
        tech_join_missing += 0 if tech_present else 1
        price_join_missing += 0 if price_present else 1
        ledger_join_missing += 0 if ledger_present else 1
        reason_bits = []
        if not factor_present:
            reason_bits.append("MISSING_FACTOR")
        if not tech_present:
            reason_bits.append("MISSING_TECHNICAL")
        if not price_present:
            reason_bits.append("MISSING_PRICE_CACHE")
        if not ledger_present:
            reason_bits.append("MISSING_ROLLING_LEDGER")
        join_ready = not reason_bits
        join_rows.append(
            {
                "ticker": ticker,
                "current_in_factor_pack": str(factor_present).upper(),
                "current_in_technical_timing": str(tech_present).upper(),
                "current_in_price_cache": str(price_present).upper(),
                "current_in_rolling_ledger": str(ledger_present).upper(),
                "join_ready": str(join_ready).upper(),
                "reason": "|".join(reason_bits),
            }
        )
        validation_rows.append(
            {
                "ticker": ticker,
                "rank_valid": str(rank_ok).upper(),
                "rank": row.get("rank", ""),
                "score_present": str(non_null(row.get("composite_candidate_score"))).upper(),
                "current_in_factor_pack": str(factor_present).upper(),
                "current_in_technical_timing": str(tech_present).upper(),
                "current_in_price_cache": str(price_present).upper(),
                "current_in_rolling_ledger": str(ledger_present).upper(),
                "validation_status": "PASS" if join_ready and rank_ok and non_null(row.get("composite_candidate_score")) else "FAIL",
                "error_message": "|".join(reason_bits) if reason_bits else "",
            }
        )

    full_join_ok = (
        factor_join_missing == 0
        and tech_join_missing == 0
        and price_join_missing == 0
        and ledger_join_missing == 0
    )

    signal_audit_rows = [
        {
            "latest_signal_freeze_run_id": signal_latest_run_id,
            "latest_signal_freeze_ticker_count": len(signal_latest_rows),
            "latest_signal_freeze_distinct_ticker_count": signal_latest_distinct,
            "latest_signal_freeze_duplicate_ticker_count": signal_latest_dupes,
            "latest_signal_freeze_matches_current_candidates": str(signal_matches_current).upper(),
            "targets_present_in_latest_signal_freeze_count": targets_present_in_latest,
            "signal_freeze_refresh_recommended": str(signal_freeze_refresh_recommended).upper(),
            "notes": "Latest R21 freeze slice compared to current ranked candidates.",
        }
    ]

    write_csv(root / OUT_POST_PROMOTION_VALIDATION, validation_rows, POST_VALIDATION_FIELDS)
    write_csv(root / OUT_FULL_JOIN_AUDIT, join_rows, FULL_JOIN_FIELDS)
    write_csv(root / OUT_SIGNAL_AUDIT, signal_audit_rows, SIGNAL_AUDIT_FIELDS)

    status = STATUS_OK
    if blockers:
        status = STATUS_WARN
    if not full_join_ok or not rank_ok or current_dupes != 0 or score_present_count != current_count:
        status = STATUS_WARN
    if signal_freeze_refresh_recommended:
        status = STATUS_WARN if status == STATUS_OK else status

    validation_fail_count = 0
    if current_count != 252:
        validation_fail_count += 1
    if current_dupes != 0:
        validation_fail_count += 1
    if not rank_ok:
        validation_fail_count += 1
    if score_present_count != current_count:
        validation_fail_count += 1
    if not full_join_ok:
        validation_fail_count += 1
    if signal_latest_run_id == "":
        validation_fail_count += 1
    if signal_latest_distinct != signal_latest_distinct or signal_latest_dupes != 0:
        validation_fail_count += 1
    if blockers:
        validation_fail_count += 1
    if status == STATUS_FAIL:
        validation_fail_count += 1

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R27K_STATUS": r27k_status or "MISSING",
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": current_count,
        "TARGET_TICKER_COUNT": len(TARGET_TICKERS),
        "TARGET_TICKERS": ",".join(TARGET_TICKERS),
        "TARGETS_PRESENT_COUNT": sum(1 for ticker in TARGET_TICKERS if ticker in current_by),
        "DUPLICATE_TICKER_COUNT": current_dupes,
        "TARGET_SCORE_PRESENT_COUNT": sum(1 for ticker in TARGET_TICKERS if non_null(current_by.get(ticker, {}).get("composite_candidate_score"))),
        "FACTOR_PRESENT_COUNT_FOR_TARGETS": factor_present_targets,
        "TECHNICAL_PRESENT_COUNT_FOR_TARGETS": technical_present_targets,
        "PRICE_CACHE_PRESENT_COUNT_FOR_TARGETS": price_present_targets,
        "ROLLING_LEDGER_SUCCESS_COUNT_FOR_TARGETS": ledger_success_targets,
        "FULL_CANDIDATE_FACTOR_JOIN_MISSING_COUNT": factor_join_missing,
        "FULL_CANDIDATE_TECHNICAL_JOIN_MISSING_COUNT": tech_join_missing,
        "FULL_CANDIDATE_PRICE_CACHE_MISSING_COUNT": price_join_missing,
        "FULL_CANDIDATE_ROLLING_LEDGER_MISSING_COUNT": ledger_join_missing,
        "LATEST_SIGNAL_FREEZE_RUN_ID": signal_latest_run_id,
        "LATEST_SIGNAL_FREEZE_TICKER_COUNT": len(signal_latest_rows),
        "LATEST_SIGNAL_FREEZE_MATCHES_CURRENT_CANDIDATES": str(signal_matches_current).upper(),
        "TARGETS_PRESENT_IN_LATEST_SIGNAL_FREEZE_COUNT": targets_present_in_latest,
        "SIGNAL_FREEZE_REFRESH_RECOMMENDED": str(signal_freeze_refresh_recommended).upper(),
        "CANDIDATES_CURRENT_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "ROLLING_LEDGER_MODIFIED": "FALSE",
        "SIGNAL_FREEZE_EXECUTED": "FALSE",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": "FALSE" if not blockers else "FALSE",
        "NEXT_RECOMMENDED_STEP": "R21_SIGNAL_FREEZE_REFRESH_AFTER_CURRENT_CANDIDATE_UPDATE" if signal_freeze_refresh_recommended else "R26B_FORWARD_RETURN_FILLER_READINESS_AUDIT",
    }

    summary_rows = [
        summary_row("CURRENT_RANKED_CANDIDATE_ROW_COUNT", current_count, 252, current_count == 252),
        summary_row("TARGETS_PRESENT_COUNT", values["TARGETS_PRESENT_COUNT"], 2, values["TARGETS_PRESENT_COUNT"] == 2),
        summary_row("DUPLICATE_TICKER_COUNT", current_dupes, 0, current_dupes == 0),
        summary_row("TARGET_SCORE_PRESENT_COUNT", values["TARGET_SCORE_PRESENT_COUNT"], 2, values["TARGET_SCORE_PRESENT_COUNT"] == 2),
        summary_row("FULL_CANDIDATE_FACTOR_JOIN_MISSING_COUNT", factor_join_missing, 0, factor_join_missing == 0),
        summary_row("FULL_CANDIDATE_TECHNICAL_JOIN_MISSING_COUNT", tech_join_missing, 0, tech_join_missing == 0),
        summary_row("FULL_CANDIDATE_PRICE_CACHE_MISSING_COUNT", price_join_missing, 0, price_join_missing == 0),
        summary_row("FULL_CANDIDATE_ROLLING_LEDGER_MISSING_COUNT", ledger_join_missing, 0, ledger_join_missing == 0),
        summary_row("LATEST_SIGNAL_FREEZE_RUN_ID", signal_latest_run_id or "MISSING", signal_latest_run_id or "MISSING", bool(signal_latest_run_id)),
        summary_row("LATEST_SIGNAL_FREEZE_TICKER_COUNT", len(signal_latest_rows), len(signal_latest_rows), True),
        summary_row("LATEST_SIGNAL_FREEZE_MATCHES_CURRENT_CANDIDATES", str(signal_matches_current).upper(), "FALSE" if signal_freeze_refresh_recommended else "TRUE", True),
        summary_row("TARGETS_PRESENT_IN_LATEST_SIGNAL_FREEZE_COUNT", targets_present_in_latest, targets_present_in_latest, True),
        summary_row("SIGNAL_FREEZE_REFRESH_RECOMMENDED", str(signal_freeze_refresh_recommended).upper(), str(signal_freeze_refresh_recommended).upper(), True),
    ]
    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, validation_rows, join_rows, signal_audit_rows))

    current_modified = file_sig(root / CURRENT_CANDIDATES) != current_before
    factor_modified = file_sig(root / FACTOR_PACK) != factor_before
    tech_modified = file_sig(root / TECH_TIMING) != tech_before
    price_modified = tree_sig(root / PRICE_CACHE_DIR) != price_before
    ledger_modified = file_sig(root / ROLLING_LEDGER) != ledger_before
    signal_modified = file_sig(root / SIGNAL_LEDGER) != signal_before
    forbidden_modified = current_modified or factor_modified or tech_modified or price_modified or ledger_modified or signal_modified
    if forbidden_modified:
        values["STATUS"] = STATUS_FAIL
        values["FORBIDDEN_MODIFIED"] = "TRUE"
        values["VALIDATION_FAIL_COUNT"] = validation_fail_count + 1
        write_text(root / OUT_READ_FIRST, render_read_first(values))
        write_text(root / OUT_REPORT, render_report(values, validation_rows, join_rows, signal_audit_rows))

    print(f"STATUS: {values['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if values["STATUS"] == STATUS_FAIL else 0


def summary_row(metric: str, value: object, expected: object, ok: bool, notes: str = "") -> Dict[str, object]:
    return {"metric": metric, "value": value, "expected": expected, "status": "OK" if ok else "WARN", "notes": notes}


if __name__ == "__main__":
    raise SystemExit(main())
