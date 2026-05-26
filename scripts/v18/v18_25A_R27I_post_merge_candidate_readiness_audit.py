from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R27I_CANDIDATE_READINESS_AUDIT_READY"
STATUS_WARN = "WARN_V18_25A_R27I_CANDIDATE_READINESS_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_25A_R27I_FORBIDDEN_MODIFIED"

MODE = "READ_ONLY_POST_MERGE_CANDIDATE_READINESS_AUDIT"

TARGET_TICKERS = ["RDDT", "TLN"]
TARGET_SET = set(TARGET_TICKERS)
EXPECTED_R27H_STATUS = "OK_V18_25A_R27H_OFFICIAL_FACTOR_TECHNICAL_MERGE_READY"

R27H_READ_FIRST = "outputs/v18/ops/V18_25A_R27H_READ_FIRST.txt"
FACTOR_PACK = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_TIMING = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
PRICE_CACHE_DIR = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OUT_DIR = "outputs/v18/candidates"
OUT_AUDIT = f"{OUT_DIR}/V18_25A_R27I_CURRENT_CANDIDATE_READINESS_AUDIT.csv"
OUT_PREVIEW_PLAN = f"{OUT_DIR}/V18_25A_R27I_CURRENT_RANKED_CANDIDATE_PREVIEW_REFRESH_PLAN.csv"
OUT_PRESENCE = f"{OUT_DIR}/V18_25A_R27I_CURRENT_CURRENT_CANDIDATES_PRESENCE_AUDIT.csv"
OUT_SUMMARY = f"{OUT_DIR}/V18_25A_R27I_CURRENT_SUMMARY.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R27I_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R27I_CURRENT_POST_MERGE_CANDIDATE_READINESS_REPORT.md"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R27H_STATUS",
    "TARGET_TICKER_COUNT",
    "TARGET_TICKERS",
    "PRICE_CACHE_PRESENT_COUNT",
    "ROLLING_LEDGER_SUCCESS_COUNT",
    "FACTOR_PRESENT_COUNT",
    "FACTOR_SCORE_PRESENT_COUNT",
    "TECHNICAL_PRESENT_COUNT",
    "TECHNICAL_SCORE_PRESENT_COUNT",
    "CURRENT_RANKED_CANDIDATE_ROW_COUNT",
    "RANKED_CANDIDATE_PRESENT_COUNT",
    "READY_FOR_RANKED_CANDIDATE_PREVIEW_REFRESH_COUNT",
    "BLOCKED_COUNT",
    "RANKED_CANDIDATE_PREVIEW_REFRESH_RECOMMENDED",
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

AUDIT_FIELDS = [
    "ticker",
    "price_cache_present",
    "rolling_ledger_success",
    "factor_present",
    "factor_score_present",
    "technical_present",
    "technical_score_present",
    "ranked_candidate_present",
    "candidate_readiness_status",
    "recommended_next_action",
]

PREVIEW_FIELDS = [
    "ticker",
    "preview_action",
    "candidate_readiness_status",
    "reason",
]

PRESENCE_FIELDS = [
    "ticker",
    "ranked_candidate_present",
    "current_candidate_row_count",
    "current_candidate_rank",
    "current_candidate_reason",
]

SUMMARY_FIELDS = ["metric", "value", "expected", "status", "notes"]


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


def dir_sig(path: Path) -> Dict[str, Tuple[int, int]]:
    if not path.exists():
        return {}
    if path.is_file():
        return {path.name: file_sig(path)}
    return {str(child.relative_to(path)): file_sig(child) for child in path.rglob("*") if child.is_file()}


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def get_field(row: Dict[str, str], *names: str) -> str:
    for name in names:
        value = str(row.get(name, "") or "").strip()
        if value:
            return value
    return ""


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


def build_ticker_map(rows: Sequence[Dict[str, str]], ticker_col: str = "ticker") -> Dict[str, Dict[str, str]]:
    return {norm_ticker(row.get(ticker_col)): row for row in rows if norm_ticker(row.get(ticker_col))}


def count_target_presence(rows: Sequence[Dict[str, str]], tickers: Sequence[str], ticker_col: str = "ticker") -> int:
    present = {norm_ticker(row.get(ticker_col)) for row in rows}
    return sum(1 for ticker in tickers if ticker in present)


def latest_row_for_ticker(rows: Sequence[Dict[str, str]], ticker: str, ticker_col: str = "ticker", date_col: str = "latest_price_date") -> Dict[str, str]:
    matches = [row for row in rows if norm_ticker(row.get(ticker_col)) == ticker]
    if not matches:
        return {}
    def sort_key(row: Dict[str, str]) -> Tuple[dt.date, int]:
        parsed = parse_date(row.get(date_col)) or dt.date.min
        return (parsed, 0)
    return sorted(matches, key=sort_key)[-1]


def ledger_metrics(rows: List[Dict[str, str]], fields: Sequence[str], today: dt.date) -> Dict[str, int]:
    field_map = {str(field).strip().lower(): field for field in fields}
    ticker_col = field_map.get("ticker") or field_map.get("symbol") or ""
    success_date_col = field_map.get("last_success_scan_date") or field_map.get("last_success_date") or ""
    success_count_col = field_map.get("success_scan_count") or ""
    covered = never = stale = artifact = 0
    seen: set[str] = set()
    for row in rows:
        ticker = norm_ticker(row.get(ticker_col))
        if ticker == "TICKERS":
            artifact += 1
        if ticker in seen:
            continue
        seen.add(ticker)
        success_date = parse_date(row.get(success_date_col))
        success_count = to_int(row.get(success_count_col))
        if success_count <= 0 or success_date is None:
            never += 1
        elif 0 <= (today - success_date).days <= 5:
            covered += 1
        else:
            stale += 1
    return {
        "total": len(rows),
        "covered": covered,
        "never": never,
        "stale": stale,
        "remaining": never + stale,
        "artifact": artifact,
    }


def price_cache_present(root: Path, ticker: str) -> Tuple[bool, int, str, str, str]:
    rows, fields = read_csv(root / PRICE_CACHE_DIR / f"{ticker}.csv")
    field_set = {str(field).strip().lower() for field in fields}
    required = {"date", "open", "high", "low", "close", "volume"}
    present = bool(rows) and required.issubset(field_set)
    latest = rows[-1] if rows else {}
    dates = [parse_date(row.get("date")) for row in rows]
    dates = [date for date in dates if date]
    return present, len(rows), min(dates).isoformat() if dates else "", max(dates).isoformat() if dates else "", str(latest.get("close", "") or "").strip()


def ledger_success_for_ticker(ledger_rows: List[Dict[str, str]], ledger_fields: Sequence[str], ticker: str, today: dt.date) -> Tuple[bool, Dict[str, str]]:
    field_map = {str(field).strip().lower(): field for field in ledger_fields}
    ticker_col = field_map.get("ticker") or field_map.get("symbol") or ""
    row = {}
    for candidate in ledger_rows:
        if ticker_col and norm_ticker(candidate.get(ticker_col)) == ticker:
            row = candidate
            break
    status = get_field(row, "last_scan_status", "scan_status", "status")
    success_date = get_field(row, "last_success_scan_date")
    success = status in {"SUCCESS_LOCAL_PRICE_FULL_HISTORY", "LOCAL_PRICE_SCAN_SUCCESS"} and success_date == today.isoformat()
    return success, row


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object], audit_rows: Sequence[Dict[str, object]], preview_rows: Sequence[Dict[str, object]]) -> str:
    audit_text = "\n".join(
        f"- {row['ticker']}: {row['candidate_readiness_status']} ({row['recommended_next_action']})" for row in audit_rows
    )
    preview_text = "\n".join(f"- {row['ticker']}: {row['preview_action']}" for row in preview_rows)
    return "\n".join(
        [
            "# V18.25A-R27I Post-Merge Candidate Readiness Audit",
            "",
            f"- STATUS: {values['STATUS']}",
            f"- MODE: {values['MODE']}",
            f"- RUN_ID: {values['RUN_ID']}",
            f"- R27H_STATUS: {values['R27H_STATUS']}",
            "",
            "## Audit",
            "",
            audit_text if audit_text else "- None.",
            "",
            "## Preview Refresh Plan",
            "",
            preview_text if preview_text else "- None.",
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
            f"- OFFICIAL_DECISION_IMPACT: {values['OFFICIAL_DECISION_IMPACT']}",
            f"- AUTO_TRADE: {values['AUTO_TRADE']}",
            f"- AUTO_SELL: {values['AUTO_SELL']}",
            f"- FORBIDDEN_MODIFIED: {values['FORBIDDEN_MODIFIED']}",
            "",
            f"NEXT_RECOMMENDED_STEP: {values['NEXT_RECOMMENDED_STEP']}",
            "",
        ]
    )


def summary_row(metric: str, value: object, expected: object, ok: bool, notes: str = "") -> Dict[str, object]:
    return {"metric": metric, "value": value, "expected": expected, "status": "OK" if ok else "WARN", "notes": notes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    today = dt.date.today()
    run_id = f"V18_25A_R27I_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    factor_before = file_sig(root / FACTOR_PACK)
    tech_before = file_sig(root / TECH_TIMING)
    candidates_before = file_sig(root / CANDIDATES)
    price_before = tree_sig(root / PRICE_CACHE_DIR)
    ledger_before_sig = file_sig(root / LEDGER)

    blockers: List[str] = []
    r27h_status = read_first_value(root / R27H_READ_FIRST, "STATUS")
    if not (root / R27H_READ_FIRST).exists():
        blockers.append(f"missing required input: {R27H_READ_FIRST}")
    if r27h_status != EXPECTED_R27H_STATUS:
        blockers.append(f"R27H status is {r27h_status or 'MISSING'}")
    if read_first_value(root / R27H_READ_FIRST, "FACTOR_MERGE_SUCCESS_COUNT") != "2":
        blockers.append("R27H factor merge success count is not 2")
    if read_first_value(root / R27H_READ_FIRST, "TECHNICAL_MERGE_SUCCESS_COUNT") != "2":
        blockers.append("R27H technical merge success count is not 2")
    if read_first_value(root / R27H_READ_FIRST, "POST_VALIDATE_FAIL_COUNT") != "0":
        blockers.append("R27H post-merge validation did not pass")
    if read_first_value(root / R27H_READ_FIRST, "FORBIDDEN_MODIFIED") != "FALSE":
        blockers.append("R27H forbidden modified flag was not FALSE")

    factor_rows, factor_fields = read_csv(root / FACTOR_PACK)
    tech_rows, tech_fields = read_csv(root / TECH_TIMING)
    candidate_rows, candidate_fields = read_csv(root / CANDIDATES)
    ledger_rows, ledger_fields = read_csv(root / LEDGER)

    factor_by_ticker = build_ticker_map(factor_rows)
    tech_by_ticker = build_ticker_map(tech_rows)
    candidate_by_ticker = build_ticker_map(candidate_rows)

    current_candidate_count = len(candidate_rows)
    current_candidate_present_count = count_target_presence(candidate_rows, TARGET_TICKERS)
    factor_present_count = 0
    factor_score_present_count = 0
    technical_present_count = 0
    technical_score_present_count = 0
    price_present_count = 0
    ledger_success_count = 0

    audit_rows: List[Dict[str, object]] = []
    preview_rows: List[Dict[str, object]] = []
    presence_rows: List[Dict[str, object]] = []
    ready_count = 0
    blocked_count = 0

    ledger_metrics_map = ledger_metrics(ledger_rows, ledger_fields, today)

    for ticker in TARGET_TICKERS:
        price_present, _, _, _, _ = price_cache_present(root, ticker)
        ledger_success, ledger_row = ledger_success_for_ticker(ledger_rows, ledger_fields, ticker, today)
        factor_row = factor_by_ticker.get(ticker, {})
        tech_row = tech_by_ticker.get(ticker, {})
        factor_present = bool(factor_row)
        tech_present = bool(tech_row)
        factor_score_present = non_null(factor_row.get("factor_pack_score"))
        tech_score_present = non_null(tech_row.get("technical_timing_score"))
        ranked_candidate_present = ticker in candidate_by_ticker

        if price_present:
            price_present_count += 1
        if ledger_success:
            ledger_success_count += 1
        if factor_present:
            factor_present_count += 1
        if factor_score_present:
            factor_score_present_count += 1
        if tech_present:
            technical_present_count += 1
        if tech_score_present:
            technical_score_present_count += 1

        if price_present and ledger_success and factor_present and factor_score_present and tech_present and tech_score_present:
            if ranked_candidate_present:
                readiness = "ALREADY_IN_CURRENT_RANKED_CANDIDATES"
                next_action = "R27K_POST_REFRESH_VALIDATION"
            else:
                readiness = "READY_FOR_RANKED_CANDIDATE_PREVIEW_REFRESH"
                next_action = "R27J_RANKED_CANDIDATES_PREVIEW_REFRESH_FOR_RDDT_TLN"
            ready_count += 1
        else:
            readiness = "BLOCKED"
            next_action = "REVIEW_R27H_POST_MERGE_VALIDATION"
            blocked_count += 1

        if not ranked_candidate_present:
            preview_action = "WOULD_PREVIEW_REFRESH"
            preview_reason = "Official factor pack and technical timing are present; candidate file left unchanged in R27I."
        else:
            preview_action = "NO_CHANGE_NEEDED"
            preview_reason = "Ticker already present in current ranked candidates."

        audit_rows.append(
            {
                "ticker": ticker,
                "price_cache_present": str(price_present).upper(),
                "rolling_ledger_success": str(ledger_success).upper(),
                "factor_present": str(factor_present).upper(),
                "factor_score_present": str(factor_score_present).upper(),
                "technical_present": str(tech_present).upper(),
                "technical_score_present": str(tech_score_present).upper(),
                "ranked_candidate_present": str(ranked_candidate_present).upper(),
                "candidate_readiness_status": readiness,
                "recommended_next_action": next_action,
            }
        )
        preview_rows.append(
            {
                "ticker": ticker,
                "preview_action": preview_action,
                "candidate_readiness_status": readiness,
                "reason": preview_reason,
            }
        )
        presence_rows.append(
            {
                "ticker": ticker,
                "ranked_candidate_present": str(ranked_candidate_present).upper(),
                "current_candidate_row_count": current_candidate_count,
                "current_candidate_rank": get_field(candidate_by_ticker.get(ticker, {}), "rank"),
                "current_candidate_reason": get_field(candidate_by_ticker.get(ticker, {}), "reason"),
            }
        )

    write_csv(root / OUT_AUDIT, audit_rows, AUDIT_FIELDS)
    write_csv(root / OUT_PREVIEW_PLAN, preview_rows, PREVIEW_FIELDS)
    write_csv(root / OUT_PRESENCE, presence_rows, PRESENCE_FIELDS)

    if blocked_count > 0 or len(TARGET_TICKERS) != 2:
        status = STATUS_WARN
    elif blockers:
        status = STATUS_WARN
    else:
        status = STATUS_OK

    target_present_ok = current_candidate_present_count == 0 or current_candidate_present_count == 2 or current_candidate_present_count == len([row for row in audit_rows if row["candidate_readiness_status"] == "ALREADY_IN_CURRENT_RANKED_CANDIDATES"])
    if not target_present_ok:
        blockers.append("candidate presence count is inconsistent with readiness classification")
        if status == STATUS_OK:
            status = STATUS_WARN

    preview_recommended = ready_count == 2
    next_step = (
        "R27J_RANKED_CANDIDATES_PREVIEW_REFRESH_FOR_RDDT_TLN"
        if ready_count == 2
        else "R27K_POST_REFRESH_VALIDATION"
        if blocked_count == 0 and ready_count == 0
        else "REVIEW_R27H_POST_MERGE_VALIDATION"
    )

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R27H_STATUS": r27h_status or "MISSING",
        "TARGET_TICKER_COUNT": len(TARGET_TICKERS),
        "TARGET_TICKERS": ",".join(TARGET_TICKERS),
        "PRICE_CACHE_PRESENT_COUNT": price_present_count,
        "ROLLING_LEDGER_SUCCESS_COUNT": ledger_success_count,
        "FACTOR_PRESENT_COUNT": factor_present_count,
        "FACTOR_SCORE_PRESENT_COUNT": factor_score_present_count,
        "TECHNICAL_PRESENT_COUNT": technical_present_count,
        "TECHNICAL_SCORE_PRESENT_COUNT": technical_score_present_count,
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": current_candidate_count,
        "RANKED_CANDIDATE_PRESENT_COUNT": current_candidate_present_count,
        "READY_FOR_RANKED_CANDIDATE_PREVIEW_REFRESH_COUNT": ready_count,
        "BLOCKED_COUNT": blocked_count,
        "RANKED_CANDIDATE_PREVIEW_REFRESH_RECOMMENDED": str(preview_recommended).upper(),
        "PRICE_CACHE_MODIFIED": "FALSE",
        "ROLLING_LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "CANDIDATES_MODIFIED": "FALSE",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "VALIDATION_FAIL_COUNT": 1 if status == STATUS_FAIL else 0,
        "FORBIDDEN_MODIFIED": "FALSE",
        "NEXT_RECOMMENDED_STEP": next_step,
    }

    summary_rows = [
        summary_row("R27H_STATUS", r27h_status or "MISSING", EXPECTED_R27H_STATUS, r27h_status == EXPECTED_R27H_STATUS),
        summary_row("TARGET_TICKERS", ",".join(TARGET_TICKERS), "RDDT,TLN", True),
        summary_row("PRICE_CACHE_PRESENT_COUNT", price_present_count, 2, price_present_count == 2),
        summary_row("ROLLING_LEDGER_SUCCESS_COUNT", ledger_success_count, 2, ledger_success_count == 2),
        summary_row("FACTOR_PRESENT_COUNT", factor_present_count, 2, factor_present_count == 2),
        summary_row("TECHNICAL_PRESENT_COUNT", technical_present_count, 2, technical_present_count == 2),
        summary_row("CURRENT_RANKED_CANDIDATE_ROW_COUNT", current_candidate_count, current_candidate_count, True),
        summary_row("RANKED_CANDIDATE_PRESENT_COUNT", current_candidate_present_count, 0, current_candidate_present_count == 0),
        summary_row("READY_FOR_RANKED_CANDIDATE_PREVIEW_REFRESH_COUNT", ready_count, 2, ready_count == 2),
        summary_row("BLOCKED_COUNT", blocked_count, 0, blocked_count == 0),
    ]
    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, audit_rows, preview_rows))

    factor_modified = file_sig(root / FACTOR_PACK) != factor_before
    tech_modified = file_sig(root / TECH_TIMING) != tech_before
    candidates_modified = file_sig(root / CANDIDATES) != candidates_before
    price_modified = tree_sig(root / PRICE_CACHE_DIR) != price_before
    ledger_modified = file_sig(root / LEDGER) != ledger_before_sig
    forbidden_modified = factor_modified or tech_modified or candidates_modified or price_modified or ledger_modified
    if forbidden_modified:
        values["STATUS"] = STATUS_FAIL
        values["FORBIDDEN_MODIFIED"] = "TRUE"
        values["VALIDATION_FAIL_COUNT"] = 1
        write_text(root / OUT_READ_FIRST, render_read_first(values))
        write_text(root / OUT_REPORT, render_report(values, audit_rows, preview_rows))

    print(f"STATUS: {values['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if values["STATUS"] == STATUS_FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
