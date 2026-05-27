from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R27G_STAGED_VALIDATION_MERGE_PLAN_READY"
STATUS_WARN = "WARN_V18_25A_R27G_STAGED_VALIDATION_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_25A_R27G_FORBIDDEN_MODIFIED"

MODE = "READ_ONLY_STAGED_VALIDATION_MERGE_PLAN"

TARGET_TICKERS = ["RDDT", "TLN"]

R27F_READ_FIRST = "outputs/v18/ops/V18_25A_R27F_READ_FIRST.txt"
R27F_EXPECTED_STATUS = "OK_V18_25A_R27F_STAGED_FACTOR_TECHNICAL_ROWS_READY"
R27F_FACTOR = "outputs/v18/staged_factor_technical/V18_25A_R27F_CURRENT_STAGED_FACTOR_ROWS.csv"
R27F_TECH = "outputs/v18/staged_factor_technical/V18_25A_R27F_CURRENT_STAGED_TECHNICAL_ROWS.csv"

PRICE_CACHE_DIR = "state/v18/price_cache"
LEDGER_PATH = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
FACTOR_CURRENT = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_CURRENT = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
CANDIDATES_CURRENT = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"

OUT_DIR = "outputs/v18/staged_factor_technical"
OUT_VALIDATION = f"{OUT_DIR}/V18_25A_R27G_CURRENT_STAGED_VALIDATION.csv"
OUT_MERGE_PLAN = f"{OUT_DIR}/V18_25A_R27G_CURRENT_OFFICIAL_MERGE_PLAN.csv"
OUT_BACKUP_PLAN = f"{OUT_DIR}/V18_25A_R27G_CURRENT_REQUIRED_BACKUP_PLAN.csv"
OUT_RECHECK = f"{OUT_DIR}/V18_25A_R27G_CURRENT_TARGET_READINESS_RECHECK.csv"
OUT_SUMMARY = f"{OUT_DIR}/V18_25A_R27G_CURRENT_SUMMARY.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R27G_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R27G_CURRENT_STAGED_VALIDATION_MERGE_PLAN_REPORT.md"

FACTOR_REQUIRED = [
    "factor_pack_rank",
    "ticker",
    "factor_pack_score",
    "latest_price_date",
    "latest_close",
    "ret_5d",
    "ret_20d",
    "ret_60d",
    "ret_120d",
    "volume_ratio_5_20",
    "F006_SHORT_REV_5D",
    "F007_PULLBACK_IN_UPTREND",
    "F008_VOLUME_ABNORMAL_5_20",
    "F009_VOLUME_PRICE_CONFIRM",
    "F010_XSEC_COMPOSITE_RANK",
    "F011_TS_MOMENTUM_60_120",
    "F012_TS_PULLBACK_REVERSAL",
    "volatility_penalty",
    "overheat_penalty",
    "shadow_side_hint",
]

TECH_REQUIRED = [
    "ticker",
    "yf_ticker",
    "price_date",
    "close",
    "bb_mid_20",
    "bb_upper_20_2",
    "bb_lower_20_2",
    "bb_percent_b",
    "bb_bandwidth",
    "bb_squeeze_flag",
    "bb_status",
    "rsi_14",
    "rsi_status",
    "kdj_k",
    "kdj_d",
    "kdj_j",
    "kdj_status",
    "volume_ratio_5_20",
    "overheat_penalty",
    "pullback_timing_bonus",
    "breakout_confirmation_bonus",
    "technical_timing_score",
    "technical_signal",
    "technical_warning_label",
    "option_data_status",
    "put_call_ratio",
    "iv_rank_proxy",
    "gamma_squeeze_status",
    "gamma_squeeze_risk_label",
    "official_decision_impact",
    "vix_date",
    "vix_close",
    "vix_regime",
]

VALIDATION_FIELDS = [
    "ticker",
    "price_cache_present",
    "price_cache_row_count",
    "rolling_ledger_success",
    "staged_factor_present",
    "staged_technical_present",
    "official_factor_present",
    "official_technical_present",
    "official_ranked_candidate_present",
    "factor_score_present",
    "technical_score_present",
    "validation_status",
    "error_message",
]

MERGE_PLAN_FIELDS = [
    "ticker",
    "factor_merge_action",
    "technical_merge_action",
    "factor_schema_compatible",
    "technical_schema_compatible",
    "merge_allowed",
    "blocker",
]

BACKUP_FIELDS = [
    "backup_item",
    "path",
    "required_for_r27h",
    "backup_status",
    "notes",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R27F_STATUS",
    "TARGET_TICKER_COUNT",
    "TARGET_TICKERS",
    "STAGED_FACTOR_ROW_COUNT",
    "STAGED_TECHNICAL_ROW_COUNT",
    "FACTOR_VALIDATION_PASS_COUNT",
    "FACTOR_VALIDATION_FAIL_COUNT",
    "TECHNICAL_VALIDATION_PASS_COUNT",
    "TECHNICAL_VALIDATION_FAIL_COUNT",
    "TARGET_FACTOR_TICKER_SET_MATCH",
    "TARGET_TECHNICAL_TICKER_SET_MATCH",
    "DUPLICATE_FACTOR_TICKER_COUNT",
    "DUPLICATE_TECHNICAL_TICKER_COUNT",
    "FACTOR_SCORE_MISSING_COUNT",
    "TECHNICAL_SCORE_MISSING_COUNT",
    "PRICE_CACHE_PRESENT_COUNT",
    "ROLLING_LEDGER_SUCCESS_COUNT",
    "OFFICIAL_FACTOR_PRESENT_COUNT",
    "OFFICIAL_TECHNICAL_PRESENT_COUNT",
    "FACTOR_SCHEMA_COMPATIBLE",
    "TECHNICAL_SCHEMA_COMPATIBLE",
    "MERGE_PLAN_ROW_COUNT",
    "MERGE_ALLOWED_COUNT",
    "MERGE_BLOCKED_COUNT",
    "FACTOR_APPEND_COUNT",
    "FACTOR_UPDATE_COUNT",
    "TECHNICAL_APPEND_COUNT",
    "TECHNICAL_UPDATE_COUNT",
    "OFFICIAL_FACTOR_MERGE_ALLOWED_NEXT",
    "OFFICIAL_TECHNICAL_MERGE_ALLOWED_NEXT",
    "R27H_OFFICIAL_MERGE_RECOMMENDED",
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

RECHECK_FIELDS = [
    "ticker",
    "price_cache_present",
    "price_cache_row_count",
    "price_cache_min_date",
    "price_cache_max_date",
    "price_cache_latest_close",
    "price_cache_latest_volume",
    "rolling_ledger_present",
    "rolling_ledger_success",
    "rolling_last_scan_status",
    "rolling_last_success_scan_date",
    "official_factor_present",
    "official_technical_present",
    "official_ranked_candidate_present",
    "readiness_status",
    "recommended_next_action",
]

SUMMARY_FIELDS = [
    "metric",
    "value",
    "expected",
    "status",
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


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def parse_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        return float(text) if text else None
    except Exception:
        return None


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


def read_first_value(path: Path, key: str) -> str:
    prefix = f"{key}:"
    for line in read_text(path).splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def get_field(row: Dict[str, str], *names: str) -> str:
    for name in names:
        value = str(row.get(name, "") or "").strip()
        if value != "":
            return value
    return ""


def load_staged_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    return read_csv(path)


def validate_staged_factor(rows: List[Dict[str, str]], fields: Sequence[str]) -> Tuple[bool, int, int, int, bool, str]:
    tickers = [norm_ticker(row.get("ticker")) for row in rows]
    score_missing = sum(1 for row in rows if not non_null(row.get("factor_pack_score")))
    dupes = len(tickers) - len(set(tickers))
    compatible = set(FACTOR_REQUIRED).issubset(set(fields))
    ok = len(rows) == 2 and set(tickers) == set(TARGET_TICKERS) and dupes == 0 and compatible and score_missing == 0
    return ok, len(rows), dupes, score_missing, compatible, ";".join(sorted(set(tickers)))


def validate_staged_technical(rows: List[Dict[str, str]], fields: Sequence[str]) -> Tuple[bool, int, int, int, bool, str]:
    tickers = [norm_ticker(row.get("ticker")) for row in rows]
    score_missing = sum(1 for row in rows if not non_null(row.get("technical_timing_score")))
    dupes = len(tickers) - len(set(tickers))
    compatible = set(TECH_REQUIRED).issubset(set(fields))
    ok = len(rows) == 2 and set(tickers) == set(TARGET_TICKERS) and dupes == 0 and compatible and score_missing == 0
    return ok, len(rows), dupes, score_missing, compatible, ";".join(sorted(set(tickers)))


def load_price_cache(path: Path) -> Tuple[bool, bool, int, str, str, str, str]:
    rows, fields = read_csv(path)
    required = {"date", "open", "high", "low", "close", "volume"}
    field_set = {str(field).strip().lower() for field in fields}
    present = path.exists()
    readable = bool(fields) and required.issubset(field_set)
    dates: List[dt.date] = []
    for row in rows:
        parsed = parse_date(row.get("date", ""))
        if parsed:
            dates.append(parsed)
    latest = rows[-1] if rows else {}
    return present, readable, len(rows), min(dates).isoformat() if dates else "", max(dates).isoformat() if dates else "", str(latest.get("close", "") or "").strip(), str(latest.get("volume", "") or "").strip()


def coverage_metrics(rows: List[Dict[str, str]], fields: Sequence[str], today: dt.date) -> Dict[str, int]:
    ticker_col = None
    success_date_col = None
    success_count_col = None
    field_map = {str(field).strip().lower(): field for field in fields}
    for alias in ["ticker", "symbol"]:
        if alias in field_map:
            ticker_col = field_map[alias]
            break
    for alias in ["last_success_scan_date", "last_success_date", "latest_success_date"]:
        if alias in field_map:
            success_date_col = field_map[alias]
            break
    for alias in ["success_scan_count"]:
        if alias in field_map:
            success_count_col = field_map[alias]
            break
    covered = never = stale = artifact = 0
    seen: set[str] = set()
    for row in rows:
        ticker = norm_ticker(row.get(ticker_col or ""))
        if ticker == "TICKERS":
            artifact += 1
        if ticker in seen:
            continue
        seen.add(ticker)
        success_date = parse_date(row.get(success_date_col or ""))
        success_count = to_int(row.get(success_count_col or ""))
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


def build_ledger_by_ticker(rows: List[Dict[str, str]], fields: Sequence[str]) -> Dict[str, Dict[str, str]]:
    field_map = {str(field).strip().lower(): field for field in fields}
    ticker_col = field_map.get("ticker") or field_map.get("symbol") or ""
    if not ticker_col:
        return {}
    return {
        norm_ticker(row.get(ticker_col)): row
        for row in rows
        if norm_ticker(row.get(ticker_col))
    }


def scan_presence(path: Path, ticker: str, aliases: Sequence[str]) -> Tuple[bool, int]:
    rows, fields = read_csv(path)
    if not rows or not fields:
        return False, 0
    field_map = {str(field).strip().lower(): field for field in fields}
    ticker_col = None
    for alias in aliases:
        if alias.lower() in field_map:
            ticker_col = field_map[alias.lower()]
            break
    if not ticker_col:
        return False, 0
    count = sum(1 for row in rows if norm_ticker(row.get(ticker_col)) == ticker)
    return count > 0, count


def build_validation_row(ticker: str, price_info: Tuple[bool, bool, int, str, str, str, str], ledger_row: Dict[str, str], staged_factor_row: Dict[str, str], staged_technical_row: Dict[str, str], official_factor_present: bool, official_technical_present: bool, official_candidate_present: bool) -> Dict[str, object]:
    price_present, price_readable, price_count, _, _, _, _ = price_info
    ledger_success = get_field(ledger_row, "last_scan_status", "scan_status", "status") == "SUCCESS_LOCAL_PRICE_FULL_HISTORY" and get_field(ledger_row, "last_success_scan_date")
    factor_score = staged_factor_row.get("factor_pack_score", "")
    technical_score = staged_technical_row.get("technical_timing_score", "")
    return {
        "ticker": ticker,
        "price_cache_present": str(price_present and price_readable).upper(),
        "price_cache_row_count": price_count,
        "rolling_ledger_success": str(bool(ledger_success)).upper(),
        "staged_factor_present": "TRUE" if staged_factor_row else "FALSE",
        "staged_technical_present": "TRUE" if staged_technical_row else "FALSE",
        "official_factor_present": str(official_factor_present).upper(),
        "official_technical_present": str(official_technical_present).upper(),
        "official_ranked_candidate_present": str(official_candidate_present).upper(),
        "factor_score_present": str(non_null(factor_score)).upper(),
        "technical_score_present": str(non_null(technical_score)).upper(),
        "validation_status": "PASS" if price_present and price_readable and bool(ledger_success) and staged_factor_row and staged_technical_row and non_null(factor_score) and non_null(technical_score) else "FAIL",
        "error_message": "" if price_present and price_readable and bool(ledger_success) and staged_factor_row and staged_technical_row and non_null(factor_score) and non_null(technical_score) else "Validation failed.",
    }


def merge_plan_row(ticker: str, factor_present: bool, technical_present: bool, factor_schema: bool, technical_schema: bool, validation_ok: bool) -> Dict[str, object]:
    factor_action = "UPDATE" if factor_present else "APPEND"
    tech_action = "UPDATE" if technical_present else "APPEND"
    allowed = validation_ok and factor_schema and technical_schema
    blocker = ""
    if not validation_ok:
        blocker = "Base validation failed."
    elif not factor_schema:
        blocker = "Factor schema incompatible."
    elif not technical_schema:
        blocker = "Technical schema incompatible."
    return {
        "ticker": ticker,
        "factor_merge_action": factor_action,
        "technical_merge_action": tech_action,
        "factor_schema_compatible": str(factor_schema).upper(),
        "technical_schema_compatible": str(technical_schema).upper(),
        "merge_allowed": str(allowed).upper(),
        "blocker": blocker,
    }


def backup_row(item: str, path: str, required: bool, status: str, notes: str = "") -> Dict[str, object]:
    return {
        "backup_item": item,
        "path": path,
        "required_for_r27h": "TRUE" if required else "FALSE",
        "backup_status": status,
        "notes": notes,
    }


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object], warnings: List[str], validation_rows: List[Dict[str, object]], merge_rows: List[Dict[str, object]]) -> str:
    warnings_text = "\n".join(f"- {w}" for w in warnings) if warnings else "- None."
    validations_text = "\n".join(f"- {row['ticker']}: {row['validation_status']}" for row in validation_rows)
    merge_text = "\n".join(f"- {row['ticker']}: {row['factor_merge_action']}/{row['technical_merge_action']} -> {row['merge_allowed']}" for row in merge_rows)
    return "\n".join(
        [
            "# V18.25A-R27G Staged Validation + Official Merge Plan",
            "",
            f"- STATUS: {values['STATUS']}",
            f"- MODE: {values['MODE']}",
            f"- RUN_ID: {values['RUN_ID']}",
            f"- R27F_STATUS: {values['R27F_STATUS']}",
            "",
            "## Validation",
            "",
            validations_text if validations_text else "- None.",
            "",
            "## Merge Plan",
            "",
            merge_text if merge_text else "- None.",
            "",
            "## Warnings",
            "",
            warnings_text,
            "",
            "## Backup Plan",
            "",
            f"- OFFICIAL_FACTOR_MERGE_ALLOWED_NEXT: {values['OFFICIAL_FACTOR_MERGE_ALLOWED_NEXT']}",
            f"- OFFICIAL_TECHNICAL_MERGE_ALLOWED_NEXT: {values['OFFICIAL_TECHNICAL_MERGE_ALLOWED_NEXT']}",
            f"- R27H_OFFICIAL_MERGE_RECOMMENDED: {values['R27H_OFFICIAL_MERGE_RECOMMENDED']}",
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R27G_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    today = dt.date.today()

    price_before = tree_sig(root / PRICE_CACHE_DIR)
    ledger_before = file_sig(root / LEDGER_PATH)
    factor_before = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_before = tree_sig(root / "outputs" / "v18" / "technical_timing")
    candidates_before = tree_sig(root / "outputs" / "v18" / "candidates")
    official_before = tree_sig(root / "outputs" / "v18" / "official_decisions")

    required_errors: List[str] = []
    if not (root / R27F_READ_FIRST).exists():
        required_errors.append(f"missing required input: {R27F_READ_FIRST}")

    r27f_status = read_first_value(root / R27F_READ_FIRST, "STATUS")
    r27f_factor_row_count = to_int(read_first_value(root / R27F_READ_FIRST, "STAGED_FACTOR_ROW_COUNT"))
    r27f_tech_row_count = to_int(read_first_value(root / R27F_READ_FIRST, "STAGED_TECHNICAL_ROW_COUNT"))
    r27f_factor_schema = read_first_value(root / R27F_READ_FIRST, "FACTOR_SCHEMA_COMPATIBLE")
    r27f_tech_schema = read_first_value(root / R27F_READ_FIRST, "TECHNICAL_SCHEMA_COMPATIBLE")
    r27f_forbidden = read_first_value(root / R27F_READ_FIRST, "FORBIDDEN_MODIFIED")
    if r27f_status != R27F_EXPECTED_STATUS:
        required_errors.append(f"R27F status is {r27f_status or 'MISSING'}")
    if r27f_factor_row_count != 2:
        required_errors.append(f"R27F staged factor row count is {r27f_factor_row_count}")
    if r27f_tech_row_count != 2:
        required_errors.append(f"R27F staged technical row count is {r27f_tech_row_count}")
    if r27f_factor_schema != "TRUE":
        required_errors.append("R27F factor schema incompatible")
    if r27f_tech_schema != "TRUE":
        required_errors.append("R27F technical schema incompatible")
    if r27f_forbidden != "FALSE":
        required_errors.append("R27F forbidden modified flag was not FALSE")

    factor_rows, factor_fields = load_staged_rows(root / R27F_FACTOR)
    tech_rows, tech_fields = load_staged_rows(root / R27F_TECH)
    if not factor_rows or not factor_fields:
        required_errors.append("staged factor rows unreadable")
    if not tech_rows or not tech_fields:
        required_errors.append("staged technical rows unreadable")

    factor_tickers = [norm_ticker(row.get("ticker")) for row in factor_rows]
    tech_tickers = [norm_ticker(row.get("ticker")) for row in tech_rows]
    factor_ticker_set_match = set(factor_tickers) == set(TARGET_TICKERS) and len(factor_rows) == 2
    tech_ticker_set_match = set(tech_tickers) == set(TARGET_TICKERS) and len(tech_rows) == 2
    factor_dup_count = len(factor_tickers) - len(set(factor_tickers))
    tech_dup_count = len(tech_tickers) - len(set(tech_tickers))
    factor_score_missing = sum(1 for row in factor_rows if not non_null(row.get("factor_pack_score")))
    tech_score_missing = sum(1 for row in tech_rows if not non_null(row.get("technical_timing_score")))

    price_present_count = 0
    ledger_success_count = 0
    official_factor_present_count = 0
    official_technical_present_count = 0
    validation_rows: List[Dict[str, object]] = []
    merge_rows: List[Dict[str, object]] = []
    backup_rows: List[Dict[str, object]] = []
    recheck_rows: List[Dict[str, object]] = []
    warnings: List[str] = []
    factor_validation_pass = 0
    factor_validation_fail = 0
    technical_validation_pass = 0
    technical_validation_fail = 0
    merge_allowed_count = 0
    merge_blocked_count = 0
    factor_append_count = 0
    factor_update_count = 0
    technical_append_count = 0
    technical_update_count = 0

    factor_current_rows, factor_current_fields = read_csv(root / FACTOR_CURRENT)
    tech_current_rows, tech_current_fields = read_csv(root / TECH_CURRENT)
    candidate_current_rows, candidate_current_fields = read_csv(root / CANDIDATES_CURRENT)
    official_factor_by_ticker = {norm_ticker(row.get("ticker")): row for row in factor_current_rows}
    official_technical_by_ticker = {norm_ticker(row.get("ticker") or row.get("yf_ticker")): row for row in tech_current_rows}
    official_candidate_by_ticker = {norm_ticker(row.get("ticker")): row for row in candidate_current_rows}

    ledger_rows, ledger_fields = read_csv(root / LEDGER_PATH)
    ledger_counts = coverage_metrics(ledger_rows, ledger_fields, today)
    ledger_by_ticker = build_ledger_by_ticker(ledger_rows, ledger_fields)

    for ticker in TARGET_TICKERS:
        price_present, price_readable, price_count, price_min_date, price_max_date, price_close, price_volume = load_price_cache(root / PRICE_CACHE_DIR / f"{ticker}.csv")
        ledger_row = {}
        if ticker in ledger_by_ticker:
            ledger_row = ledger_by_ticker[ticker]
        ledger_status = get_field(ledger_row, "last_scan_status", "scan_status", "status")
        ledger_success = ledger_status == "SUCCESS_LOCAL_PRICE_FULL_HISTORY" and get_field(ledger_row, "last_success_scan_date") == today.isoformat()
        factor_present = ticker in official_factor_by_ticker
        technical_present = ticker in official_technical_by_ticker
        candidate_present = ticker in official_candidate_by_ticker
        if price_present and price_readable:
            price_present_count += 1
        if ledger_success:
            ledger_success_count += 1
        if factor_present:
            official_factor_present_count += 1
        if technical_present:
            official_technical_present_count += 1

        factor_stage_row = next((row for row in factor_rows if norm_ticker(row.get("ticker")) == ticker), {})
        tech_stage_row = next((row for row in tech_rows if norm_ticker(row.get("ticker")) == ticker), {})
        validation_ok = bool(price_present and price_readable and ledger_success and factor_stage_row and tech_stage_row and non_null(factor_stage_row.get("factor_pack_score")) and non_null(tech_stage_row.get("technical_timing_score")))
        if validation_ok:
            factor_validation_pass += 1
            technical_validation_pass += 1
        else:
            factor_validation_fail += 1
            technical_validation_fail += 1

        validation_rows.append(
            build_validation_row(
                ticker,
                (price_present, price_readable, price_count, price_min_date, price_max_date, price_close, price_volume),
                ledger_row,
                factor_stage_row,
                tech_stage_row,
                factor_present,
                technical_present,
                candidate_present,
            )
        )

        merge_row = merge_plan_row(ticker, factor_present, technical_present, set(FACTOR_REQUIRED).issubset(set(factor_fields)), set(TECH_REQUIRED).issubset(set(tech_fields)), validation_ok and set(factor_tickers) == set(TARGET_TICKERS) and set(tech_tickers) == set(TARGET_TICKERS))
        merge_rows.append(merge_row)
        if merge_row["factor_merge_action"] == "APPEND":
            factor_append_count += 1
        else:
            factor_update_count += 1
        if merge_row["technical_merge_action"] == "APPEND":
            technical_append_count += 1
        else:
            technical_update_count += 1
        if merge_row["merge_allowed"] == "TRUE":
            merge_allowed_count += 1
        else:
            merge_blocked_count += 1
        if merge_row["merge_allowed"] != "TRUE":
            warnings.append(f"{ticker} merge is blocked: {merge_row['blocker']}")

        recheck_rows.append(
            {
                "ticker": ticker,
                "price_cache_present": str(price_present and price_readable).upper(),
                "price_cache_row_count": price_count,
                "price_cache_min_date": price_min_date,
                "price_cache_max_date": price_max_date,
                "price_cache_latest_close": price_close,
                "price_cache_latest_volume": price_volume,
                "rolling_ledger_present": str(bool(ledger_row)).upper(),
                "rolling_ledger_success": str(ledger_success).upper(),
                "rolling_last_scan_status": ledger_status,
                "rolling_last_success_scan_date": get_field(ledger_row, "last_success_scan_date"),
                "official_factor_present": str(factor_present).upper(),
                "official_technical_present": str(technical_present).upper(),
                "official_ranked_candidate_present": str(candidate_present).upper(),
                "readiness_status": "READY_FOR_OFFICIAL_MERGE" if validation_ok and merge_row["merge_allowed"] == "TRUE" else "BLOCKED",
                "recommended_next_action": "R27H_OFFICIAL_MERGE_WITH_BACKUP" if validation_ok and merge_row["merge_allowed"] == "TRUE" else "REVIEW_R27G_VALIDATION_GAPS",
            }
        )

    backup_rows.append(backup_row("OFFICIAL_FACTOR_CURRENT", FACTOR_CURRENT, True, "REQUIRED_FOR_R27H", "Backup before any official factor pack merge."))
    backup_rows.append(backup_row("OFFICIAL_TECHNICAL_CURRENT", TECH_CURRENT, True, "REQUIRED_FOR_R27H", "Backup before any official technical timing merge."))
    backup_rows.append(backup_row("OFFICIAL_RANKED_CANDIDATES_CURRENT", CANDIDATES_CURRENT, False, "NOT_REQUIRED_FOR_R27H", "No official candidate file changes are planned in R27G."))

    factor_schema_compatible = set(FACTOR_REQUIRED).issubset(set(factor_fields)) and len(factor_rows) == 2 and factor_dup_count == 0 and factor_score_missing == 0
    technical_schema_compatible = set(TECH_REQUIRED).issubset(set(tech_fields)) and len(tech_rows) == 2 and tech_dup_count == 0 and tech_score_missing == 0

    if len(factor_rows) != 2:
        warnings.append(f"staged factor row count is {len(factor_rows)} not 2.")
    if len(tech_rows) != 2:
        warnings.append(f"staged technical row count is {len(tech_rows)} not 2.")
    if set(factor_tickers) != set(TARGET_TICKERS):
        warnings.append(f"staged factor ticker set is {','.join(sorted(set(factor_tickers)))} not RDDT,TLN.")
    if set(tech_tickers) != set(TARGET_TICKERS):
        warnings.append(f"staged technical ticker set is {','.join(sorted(set(tech_tickers)))} not RDDT,TLN.")
    if factor_dup_count != 0:
        warnings.append("duplicate staged factor tickers detected.")
    if tech_dup_count != 0:
        warnings.append("duplicate staged technical tickers detected.")
    if factor_score_missing != 0:
        warnings.append("staged factor score missing values detected.")
    if tech_score_missing != 0:
        warnings.append("staged technical score missing values detected.")
    if official_factor_present_count != 0:
        warnings.append(f"official factor current already contains {official_factor_present_count} target rows.")
    if official_technical_present_count != 0:
        warnings.append(f"official technical current already contains {official_technical_present_count} target rows.")
    if ledger_counts["total"] != 323:
        warnings.append(f"ledger total rows are {ledger_counts['total']} not 323.")
    if ledger_counts["covered"] != 303:
        warnings.append(f"ledger covered within 5D is {ledger_counts['covered']} not 303.")
    if ledger_counts["never"] != 20:
        warnings.append(f"ledger never-success count is {ledger_counts['never']} not 20.")
    if ledger_counts["stale"] != 0:
        warnings.append(f"ledger stale count is {ledger_counts['stale']} not 0.")
    if ledger_counts["remaining"] != 20:
        warnings.append(f"ledger remaining count is {ledger_counts['remaining']} not 20.")

    if factor_current_fields and not set(FACTOR_REQUIRED).issubset(set(factor_current_fields)):
        warnings.append("official factor schema compatibility should be reviewed.")
    if tech_current_fields and not set(TECH_REQUIRED).issubset(set(tech_current_fields)):
        warnings.append("official technical schema compatibility should be reviewed.")

    if required_errors:
        status = STATUS_FAIL
        validation_fail_count = 1
    elif warnings:
        status = STATUS_WARN
        validation_fail_count = 0
    else:
        status = STATUS_OK
        validation_fail_count = 0

    if merge_allowed_count != 2 or merge_blocked_count != 0:
        warnings.append("merge plan does not allow both targets cleanly.")
        if status == STATUS_OK:
            status = STATUS_WARN

    write_csv(root / OUT_VALIDATION, validation_rows, VALIDATION_FIELDS)
    write_csv(root / OUT_MERGE_PLAN, merge_rows, MERGE_PLAN_FIELDS)
    write_csv(root / OUT_BACKUP_PLAN, backup_rows, BACKUP_FIELDS)
    write_csv(root / OUT_RECHECK, recheck_rows, RECHECK_FIELDS)

    summary_rows = [
        {"metric": "R27F_STATUS", "value": r27f_status or "MISSING", "expected": R27F_EXPECTED_STATUS, "status": "OK" if r27f_status == R27F_EXPECTED_STATUS else "WARN", "notes": ""},
        {"metric": "STAGED_FACTOR_ROW_COUNT", "value": len(factor_rows), "expected": 2, "status": "OK" if len(factor_rows) == 2 else "WARN", "notes": ""},
        {"metric": "STAGED_TECHNICAL_ROW_COUNT", "value": len(tech_rows), "expected": 2, "status": "OK" if len(tech_rows) == 2 else "WARN", "notes": ""},
        {"metric": "FACTOR_VALIDATION_PASS_COUNT", "value": factor_validation_pass, "expected": 2, "status": "OK" if factor_validation_pass == 2 else "WARN", "notes": ""},
        {"metric": "FACTOR_VALIDATION_FAIL_COUNT", "value": factor_validation_fail, "expected": 0, "status": "OK" if factor_validation_fail == 0 else "WARN", "notes": ""},
        {"metric": "TECHNICAL_VALIDATION_PASS_COUNT", "value": technical_validation_pass, "expected": 2, "status": "OK" if technical_validation_pass == 2 else "WARN", "notes": ""},
        {"metric": "TECHNICAL_VALIDATION_FAIL_COUNT", "value": technical_validation_fail, "expected": 0, "status": "OK" if technical_validation_fail == 0 else "WARN", "notes": ""},
        {"metric": "MERGE_PLAN_ROW_COUNT", "value": len(merge_rows), "expected": 2, "status": "OK" if len(merge_rows) == 2 else "WARN", "notes": ""},
        {"metric": "MERGE_ALLOWED_COUNT", "value": merge_allowed_count, "expected": 2, "status": "OK" if merge_allowed_count == 2 else "WARN", "notes": ""},
        {"metric": "MERGE_BLOCKED_COUNT", "value": merge_blocked_count, "expected": 0, "status": "OK" if merge_blocked_count == 0 else "WARN", "notes": ""},
    ]
    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    price_after = tree_sig(root / PRICE_CACHE_DIR)
    ledger_after = file_sig(root / LEDGER_PATH)
    factor_after = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_after = tree_sig(root / "outputs" / "v18" / "technical_timing")
    candidates_after = tree_sig(root / "outputs" / "v18" / "candidates")
    official_after = tree_sig(root / "outputs" / "v18" / "official_decisions")
    price_modified = price_after != price_before
    ledger_modified = ledger_after != ledger_before
    factor_modified = factor_after != factor_before
    tech_modified = tech_after != tech_before
    candidates_modified = candidates_after != candidates_before
    official_modified = official_after != official_before
    forbidden_modified = price_modified or ledger_modified or factor_modified or tech_modified or candidates_modified or official_modified
    if forbidden_modified:
        status = STATUS_FAIL
        validation_fail_count = 1

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R27F_STATUS": r27f_status or "MISSING",
        "TARGET_TICKER_COUNT": len(TARGET_TICKERS),
        "TARGET_TICKERS": ",".join(TARGET_TICKERS),
        "STAGED_FACTOR_ROW_COUNT": len(factor_rows),
        "STAGED_TECHNICAL_ROW_COUNT": len(tech_rows),
        "FACTOR_VALIDATION_PASS_COUNT": factor_validation_pass,
        "FACTOR_VALIDATION_FAIL_COUNT": factor_validation_fail,
        "TECHNICAL_VALIDATION_PASS_COUNT": technical_validation_pass,
        "TECHNICAL_VALIDATION_FAIL_COUNT": technical_validation_fail,
        "TARGET_FACTOR_TICKER_SET_MATCH": str(set(factor_tickers) == set(TARGET_TICKERS) and len(factor_rows) == 2).upper(),
        "TARGET_TECHNICAL_TICKER_SET_MATCH": str(set(tech_tickers) == set(TARGET_TICKERS) and len(tech_rows) == 2).upper(),
        "DUPLICATE_FACTOR_TICKER_COUNT": factor_dup_count,
        "DUPLICATE_TECHNICAL_TICKER_COUNT": tech_dup_count,
        "FACTOR_SCORE_MISSING_COUNT": factor_score_missing,
        "TECHNICAL_SCORE_MISSING_COUNT": tech_score_missing,
        "PRICE_CACHE_PRESENT_COUNT": price_present_count,
        "ROLLING_LEDGER_SUCCESS_COUNT": ledger_success_count,
        "OFFICIAL_FACTOR_PRESENT_COUNT": official_factor_present_count,
        "OFFICIAL_TECHNICAL_PRESENT_COUNT": official_technical_present_count,
        "FACTOR_SCHEMA_COMPATIBLE": str(factor_schema_compatible).upper(),
        "TECHNICAL_SCHEMA_COMPATIBLE": str(technical_schema_compatible).upper(),
        "MERGE_PLAN_ROW_COUNT": len(merge_rows),
        "MERGE_ALLOWED_COUNT": merge_allowed_count,
        "MERGE_BLOCKED_COUNT": merge_blocked_count,
        "FACTOR_APPEND_COUNT": factor_append_count,
        "FACTOR_UPDATE_COUNT": factor_update_count,
        "TECHNICAL_APPEND_COUNT": technical_append_count,
        "TECHNICAL_UPDATE_COUNT": technical_update_count,
        "OFFICIAL_FACTOR_MERGE_ALLOWED_NEXT": "TRUE" if merge_allowed_count == 2 else "FALSE",
        "OFFICIAL_TECHNICAL_MERGE_ALLOWED_NEXT": "TRUE" if merge_allowed_count == 2 else "FALSE",
        "R27H_OFFICIAL_MERGE_RECOMMENDED": "TRUE" if merge_allowed_count == 2 else "FALSE",
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
        "NEXT_RECOMMENDED_STEP": "R27H: create backups and apply official factor pack and technical timing merge only after final approval; no candidate file changes.",
    }

    # Correct an earlier derived count by using the known ledger success rows directly.
    values["ROLLING_LEDGER_SUCCESS_COUNT"] = ledger_success_count

    if merge_allowed_count != 2 or merge_blocked_count != 0 or not factor_schema_compatible or not technical_schema_compatible:
        if status == STATUS_OK:
            status = STATUS_WARN

    values["STATUS"] = status
    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, warnings, validation_rows, merge_rows))
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if status == STATUS_FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
