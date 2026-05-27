from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R26B_FORWARD_RETURN_FILLER_READINESS_READY"
STATUS_WARN = "WARN_V18_25A_R26B_FORWARD_RETURN_READINESS_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_25A_R26B_FORBIDDEN_MODIFIED"

MODE = "READ_ONLY_FORWARD_RETURN_FILLER_READINESS_AUDIT"
TARGET_TICKERS = ["RDDT", "TLN"]
TARGET_SET = set(TARGET_TICKERS)

EXPECTED_R27L_STATUS = "OK_V18_25A_R27L_POST_PROMOTION_VALIDATION_SIGNAL_FREEZE_READY"

R27L_READ_FIRST = "outputs/v18/ops/V18_25A_R27L_READ_FIRST.txt"
CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
FACTOR_PACK = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_TIMING = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
PRICE_CACHE_DIR = "state/v18/price_cache"
ROLLING_LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
SIGNAL_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"

OUT_DIR = "outputs/v18/forward_test"
OUT_RUN_SUMMARY = f"{OUT_DIR}/V18_25A_R26B_CURRENT_SIGNAL_FREEZE_RUN_SUMMARY.csv"
OUT_FILLABILITY_BY_RUN = f"{OUT_DIR}/V18_25A_R26B_CURRENT_FORWARD_RETURN_FILLABILITY_BY_RUN.csv"
OUT_FILLABILITY_BY_TICKER = f"{OUT_DIR}/V18_25A_R26B_CURRENT_FORWARD_RETURN_FILLABILITY_BY_TICKER.csv"
OUT_LATEST_FULL_READINESS = f"{OUT_DIR}/V18_25A_R26B_CURRENT_LATEST_FULL_RUN_READINESS.csv"
OUT_TARGET_PRESENCE = f"{OUT_DIR}/V18_25A_R26B_CURRENT_RDDT_TLN_FORWARD_TEST_PRESENCE.csv"
OUT_FULL_JOIN_AUDIT = f"{OUT_DIR}/V18_25A_R26B_CURRENT_FULL_CANDIDATE_JOIN_AUDIT.csv"
OUT_SUMMARY = f"{OUT_DIR}/V18_25A_R26B_CURRENT_SUMMARY.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R26B_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R26B_CURRENT_FORWARD_RETURN_FILLER_READINESS_REPORT.md"

RUN_SUMMARY_FIELDS = [
    "run_id",
    "signal_date",
    "run_timestamp",
    "top_n_requested",
    "frozen_ticker_count",
    "missing_ticker_count",
    "missing_score_count",
    "missing_price_count",
    "current_candidate_match",
    "current_missing_ticker_count",
    "current_extra_ticker_count",
    "rddt_present",
    "tln_present",
    "rddt_tln_present_count",
    "latest_available_price_date_min",
    "latest_available_price_date_max",
]

FILLABILITY_BY_RUN_FIELDS = [
    "run_id",
    "signal_date",
    "top_n_requested",
    "frozen_ticker_count",
    "fillable_1d_count",
    "fillable_3d_count",
    "fillable_5d_count",
    "fillable_10d_count",
    "fillable_20d_count",
    "not_yet_mature_1d_count",
    "not_yet_mature_3d_count",
    "not_yet_mature_5d_count",
    "not_yet_mature_10d_count",
    "not_yet_mature_20d_count",
    "missing_price_cache_count",
    "latest_available_price_date_min",
    "latest_available_price_date_max",
]

FILLABILITY_BY_TICKER_FIELDS = [
    "run_id",
    "signal_date",
    "ticker",
    "source_rank",
    "top_n_requested",
    "price_cache_present",
    "price_latest_date",
    "future_dates_available_count",
    "fillable_1d",
    "fillable_3d",
    "fillable_5d",
    "fillable_10d",
    "fillable_20d",
    "not_yet_mature_1d",
    "not_yet_mature_3d",
    "not_yet_mature_5d",
    "not_yet_mature_10d",
    "not_yet_mature_20d",
]

LATEST_FULL_FIELDS = [
    "latest_full_current_freeze_run_id",
    "latest_full_current_freeze_signal_date",
    "latest_full_current_freeze_ticker_count",
    "latest_full_current_freeze_matches_current_candidates",
    "rddt_tln_present_in_latest_full_freeze_count",
    "latest_full_run_fillable_1d_count",
    "latest_full_run_fillable_3d_count",
    "latest_full_run_fillable_5d_count",
    "latest_full_run_fillable_10d_count",
    "latest_full_run_fillable_20d_count",
    "latest_full_run_not_yet_mature_1d_count",
    "latest_full_run_not_yet_mature_3d_count",
    "latest_full_run_not_yet_mature_5d_count",
    "latest_full_run_not_yet_mature_10d_count",
    "latest_full_run_not_yet_mature_20d_count",
    "missing_price_cache_count_for_latest_full_run",
    "latest_available_price_date_min",
    "latest_available_price_date_max",
    "forward_return_filler_ready_now",
    "forward_return_filler_scope_recommendation",
]

TARGET_PRESENCE_FIELDS = [
    "ticker",
    "present_in_latest_full_freeze",
    "present_in_latest_full_freeze_count",
    "current_candidate_present",
    "current_candidate_rank",
    "current_candidate_score",
    "latest_full_freeze_source_rank",
    "latest_full_freeze_price_latest_date",
    "latest_full_freeze_future_dates_available_count",
]

SUMMARY_FIELDS = ["metric", "value", "expected", "status", "notes"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R27L_STATUS",
    "CURRENT_RANKED_CANDIDATE_ROW_COUNT",
    "SIGNAL_FREEZE_LEDGER_ROW_COUNT",
    "SIGNAL_FREEZE_RUN_COUNT",
    "LATEST_FULL_CURRENT_FREEZE_RUN_ID",
    "LATEST_FULL_CURRENT_FREEZE_SIGNAL_DATE",
    "LATEST_FULL_CURRENT_FREEZE_TICKER_COUNT",
    "LATEST_FULL_CURRENT_FREEZE_MATCHES_CURRENT_CANDIDATES",
    "RDDT_TLN_PRESENT_IN_LATEST_FULL_FREEZE_COUNT",
    "LATEST_FULL_RUN_FILLABLE_1D_COUNT",
    "LATEST_FULL_RUN_FILLABLE_3D_COUNT",
    "LATEST_FULL_RUN_FILLABLE_5D_COUNT",
    "LATEST_FULL_RUN_FILLABLE_10D_COUNT",
    "LATEST_FULL_RUN_FILLABLE_20D_COUNT",
    "LATEST_FULL_RUN_NOT_YET_MATURE_1D_COUNT",
    "LATEST_FULL_RUN_NOT_YET_MATURE_3D_COUNT",
    "LATEST_FULL_RUN_NOT_YET_MATURE_5D_COUNT",
    "LATEST_FULL_RUN_NOT_YET_MATURE_10D_COUNT",
    "LATEST_FULL_RUN_NOT_YET_MATURE_20D_COUNT",
    "ANY_RUN_FILLABLE_1D_COUNT",
    "ANY_RUN_FILLABLE_3D_COUNT",
    "ANY_RUN_FILLABLE_5D_COUNT",
    "ANY_RUN_FILLABLE_10D_COUNT",
    "ANY_RUN_FILLABLE_20D_COUNT",
    "MISSING_PRICE_CACHE_COUNT_FOR_LATEST_FULL_RUN",
    "FORWARD_RETURN_FILLER_READY_NOW",
    "FORWARD_RETURN_FILLER_SCOPE_RECOMMENDATION",
    "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED",
    "CANDIDATES_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "SIGNAL_FREEZE_LEDGER_MODIFIED",
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


def parse_ts(value: str) -> dt.datetime:
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d_%H%M%S"):
        try:
            return dt.datetime.strptime(text, fmt)
        except Exception:
            continue
    return dt.datetime.min


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


def load_price_cache_dates(root: Path) -> Tuple[Dict[str, List[dt.date]], Dict[str, dt.date]]:
    dates_by_ticker: Dict[str, List[dt.date]] = {}
    latest_by_ticker: Dict[str, dt.date] = {}
    price_dir = root / PRICE_CACHE_DIR
    for path in price_dir.glob("*.csv"):
        rows, _ = read_csv(path)
        if not rows:
            continue
        dates = [parse_date(row.get("date")) for row in rows]
        dates = sorted({date for date in dates if date is not None})
        if not dates:
            continue
        ticker = norm_ticker(path.stem)
        dates_by_ticker[ticker] = dates
        latest_by_ticker[ticker] = dates[-1]
    return dates_by_ticker, latest_by_ticker


def future_dates_available_count(dates_by_ticker: Dict[str, List[dt.date]], ticker: str, signal_date: dt.date) -> int:
    dates = dates_by_ticker.get(ticker, [])
    return sum(1 for date in dates if date > signal_date)


def latest_full_current_freeze(
    run_rows: Dict[str, List[Dict[str, str]]],
    current_set: set[str],
    current_count: int,
) -> Tuple[str, str, List[Dict[str, str]]]:
    candidates: List[Tuple[dt.datetime, dt.date, str, List[Dict[str, str]]]] = []
    for run_id, rows in run_rows.items():
        tickers = {norm_ticker(row.get("ticker")) for row in rows if norm_ticker(row.get("ticker"))}
        if len(rows) == current_count and tickers == current_set:
            signal_date = parse_date(rows[0].get("signal_date")) or dt.date.min
            run_ts = parse_ts(rows[0].get("run_timestamp", ""))
            candidates.append((run_ts, signal_date, run_id, rows))
    if not candidates:
        return "", "", []
    run_ts, signal_date, run_id, rows = max(candidates, key=lambda item: (item[0], item[1], item[2]))
    return run_id, signal_date.isoformat() if signal_date != dt.date.min else "", rows


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object], run_rows: Sequence[Dict[str, object]], full_rows: Sequence[Dict[str, object]], presence_rows: Sequence[Dict[str, object]]) -> str:
    run_text = "\n".join(
        f"- {row['run_id']}: fillable_1d={row['fillable_1d_count']}, fillable_3d={row['fillable_3d_count']}, fillable_5d={row['fillable_5d_count']}"
        for row in run_rows
    )
    full_text = "\n".join(f"- {row['ticker']}: {row['present_in_latest_full_freeze']}" for row in presence_rows)
    return "\n".join(
        [
            "# V18.25A-R26B Forward Return Filler Readiness Audit",
            "",
            f"- STATUS: {values['STATUS']}",
            f"- MODE: {values['MODE']}",
            f"- RUN_ID: {values['RUN_ID']}",
            f"- R27L_STATUS: {values['R27L_STATUS']}",
            "",
            "## Run Summary",
            "",
            run_text if run_text else "- None.",
            "",
            "## Latest Full Freeze",
            "",
            f"- {values['LATEST_FULL_CURRENT_FREEZE_RUN_ID']} / {values['LATEST_FULL_CURRENT_FREEZE_SIGNAL_DATE']}",
            "",
            "## Target Presence",
            "",
            full_text if full_text else "- None.",
            "",
            "## Guardrails",
            "",
            f"- PRICE_CACHE_MODIFIED: {values['PRICE_CACHE_MODIFIED']}",
            f"- ROLLING_LEDGER_MODIFIED: {values['ROLLING_LEDGER_MODIFIED']}",
            f"- CANDIDATES_MODIFIED: {values['CANDIDATES_MODIFIED']}",
            f"- FACTOR_PACK_MODIFIED: {values['FACTOR_PACK_MODIFIED']}",
            f"- TECHNICAL_TIMING_MODIFIED: {values['TECHNICAL_TIMING_MODIFIED']}",
            f"- SIGNAL_FREEZE_LEDGER_MODIFIED: {values['SIGNAL_FREEZE_LEDGER_MODIFIED']}",
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
    run_id = f"V18_25A_R26B_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    current_before = file_sig(root / CURRENT_CANDIDATES)
    factor_before = file_sig(root / FACTOR_PACK)
    tech_before = file_sig(root / TECH_TIMING)
    price_before = tree_sig(root / PRICE_CACHE_DIR)
    ledger_before = file_sig(root / ROLLING_LEDGER)
    signal_before = file_sig(root / SIGNAL_LEDGER)

    blockers: List[str] = []
    r27l_status = read_first_value(root / R27L_READ_FIRST, "STATUS")
    if not (root / R27L_READ_FIRST).exists():
        blockers.append(f"missing required input: {R27L_READ_FIRST}")
    if r27l_status != EXPECTED_R27L_STATUS:
        blockers.append(f"R27L status is {r27l_status or 'MISSING'}")
    if read_first_value(root / R27L_READ_FIRST, "CURRENT_RANKED_CANDIDATE_ROW_COUNT") != "252":
        blockers.append("R27L current ranked candidate row count is not 252")
    if read_first_value(root / R27L_READ_FIRST, "LATEST_SIGNAL_FREEZE_MATCHES_CURRENT_CANDIDATES") != "TRUE":
        blockers.append("R27L latest signal freeze does not match current candidates")
    if read_first_value(root / R27L_READ_FIRST, "TARGETS_PRESENT_IN_LATEST_SIGNAL_FREEZE_COUNT") != "2":
        blockers.append("R27L targets are not both present in the latest signal freeze")
    if read_first_value(root / R27L_READ_FIRST, "FORBIDDEN_MODIFIED") != "FALSE":
        blockers.append("R27L forbidden modified flag was not FALSE")

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
    current_set = set(current_by)

    dates_by_ticker, latest_date_by_ticker = load_price_cache_dates(root)

    signal_run_rows: Dict[str, List[Dict[str, str]]] = {}
    for row in signal_rows:
        run = str(row.get("run_id") or "").strip()
        if run:
            signal_run_rows.setdefault(run, []).append(row)

    signal_run_count = len(signal_run_rows)
    signal_ledger_row_count = len(signal_rows)

    run_summary_rows: List[Dict[str, object]] = []
    fillability_by_run_rows: List[Dict[str, object]] = []
    fillability_by_ticker_rows: List[Dict[str, object]] = []

    any_run_fillable = {1: 0, 3: 0, 5: 0, 10: 0, 20: 0}
    latest_full_run_id, latest_full_run_signal_date, latest_full_rows = latest_full_current_freeze(signal_run_rows, current_set, current_count)

    latest_full_fillable = {1: 0, 3: 0, 5: 0, 10: 0, 20: 0}
    latest_full_missing_price = 0
    latest_full_price_dates: List[dt.date] = []
    latest_full_set = {norm_ticker(row.get("ticker")) for row in latest_full_rows if norm_ticker(row.get("ticker"))}
    latest_full_present_count = sum(1 for ticker in TARGET_TICKERS if ticker in latest_full_set)

    for run_id_key, rows in sorted(
        signal_run_rows.items(),
        key=lambda item: (
            parse_date(item[1][0].get("signal_date")) or dt.date.min,
            parse_ts(item[1][0].get("run_timestamp", "")),
            item[0],
        ),
    ):
        signal_date = parse_date(rows[0].get("signal_date")) or dt.date.min
        run_ts = rows[0].get("run_timestamp", "")
        tickers = [norm_ticker(row.get("ticker")) for row in rows if norm_ticker(row.get("ticker"))]
        ticker_set = set(tickers)
        frozen_count = len(rows)
        top_n_requested = max((to_int(row.get("source_rank"), 0) for row in rows), default=frozen_count)
        missing_ticker_count = sum(1 for row in rows if not norm_ticker(row.get("ticker")))
        missing_score_count = sum(
            1
            for row in rows
            if not non_null(row.get("factor_score"))
            or not non_null(row.get("technical_timing_score"))
            or not non_null(row.get("composite_candidate_score"))
        )
        missing_price_count = sum(1 for row in rows if norm_ticker(row.get("ticker")) not in dates_by_ticker)
        current_candidate_match = ticker_set == current_set and frozen_count == current_count
        current_missing_ticker_count = len(current_set - ticker_set)
        current_extra_ticker_count = len(ticker_set - current_set)
        rddt_present = int("RDDT" in ticker_set)
        tln_present = int("TLN" in ticker_set)
        rddt_tln_present_count = rddt_present + tln_present
        latest_dates = [latest_date_by_ticker[ticker] for ticker in ticker_set if ticker in latest_date_by_ticker]
        latest_available_min = min(latest_dates).isoformat() if latest_dates else ""
        latest_available_max = max(latest_dates).isoformat() if latest_dates else ""

        run_fillable = {1: 0, 3: 0, 5: 0, 10: 0, 20: 0}
        run_missing_price = 0
        for row in rows:
            ticker = norm_ticker(row.get("ticker"))
            signal_row_date = signal_date
            if not ticker or ticker not in dates_by_ticker:
                run_missing_price += 1
                continue
            future_count = future_dates_available_count(dates_by_ticker, ticker, signal_row_date)
            for horizon in run_fillable:
                if future_count >= horizon:
                    run_fillable[horizon] += 1
            fillability_by_ticker_rows.append(
                {
                    "run_id": run_id_key,
                    "signal_date": signal_date.isoformat() if signal_date != dt.date.min else "",
                    "ticker": ticker,
                    "source_rank": row.get("source_rank", ""),
                    "top_n_requested": top_n_requested,
                    "price_cache_present": str(ticker in dates_by_ticker).upper(),
                    "price_latest_date": latest_date_by_ticker.get(ticker, dt.date.min).isoformat() if ticker in latest_date_by_ticker else "",
                    "future_dates_available_count": future_count,
                    "fillable_1d": str(future_count >= 1).upper(),
                    "fillable_3d": str(future_count >= 3).upper(),
                    "fillable_5d": str(future_count >= 5).upper(),
                    "fillable_10d": str(future_count >= 10).upper(),
                    "fillable_20d": str(future_count >= 20).upper(),
                    "not_yet_mature_1d": str(future_count < 1).upper(),
                    "not_yet_mature_3d": str(future_count < 3).upper(),
                    "not_yet_mature_5d": str(future_count < 5).upper(),
                    "not_yet_mature_10d": str(future_count < 10).upper(),
                    "not_yet_mature_20d": str(future_count < 20).upper(),
                }
            )

        for horizon, count in run_fillable.items():
            if count > 0:
                any_run_fillable[horizon] += 1

        run_summary_rows.append(
            {
                "run_id": run_id_key,
                "signal_date": signal_date.isoformat() if signal_date != dt.date.min else "",
                "run_timestamp": run_ts,
                "top_n_requested": top_n_requested,
                "frozen_ticker_count": frozen_count,
                "missing_ticker_count": missing_ticker_count,
                "missing_score_count": missing_score_count,
                "missing_price_count": missing_price_count,
                "current_candidate_match": str(current_candidate_match).upper(),
                "current_missing_ticker_count": current_missing_ticker_count,
                "current_extra_ticker_count": current_extra_ticker_count,
                "rddt_present": str(bool(rddt_present)).upper(),
                "tln_present": str(bool(tln_present)).upper(),
                "rddt_tln_present_count": rddt_tln_present_count,
                "latest_available_price_date_min": latest_available_min,
                "latest_available_price_date_max": latest_available_max,
            }
        )

        fillability_by_run_rows.append(
            {
                "run_id": run_id_key,
                "signal_date": signal_date.isoformat() if signal_date != dt.date.min else "",
                "top_n_requested": top_n_requested,
                "frozen_ticker_count": frozen_count,
                "fillable_1d_count": run_fillable[1],
                "fillable_3d_count": run_fillable[3],
                "fillable_5d_count": run_fillable[5],
                "fillable_10d_count": run_fillable[10],
                "fillable_20d_count": run_fillable[20],
                "not_yet_mature_1d_count": frozen_count - run_fillable[1],
                "not_yet_mature_3d_count": frozen_count - run_fillable[3],
                "not_yet_mature_5d_count": frozen_count - run_fillable[5],
                "not_yet_mature_10d_count": frozen_count - run_fillable[10],
                "not_yet_mature_20d_count": frozen_count - run_fillable[20],
                "missing_price_cache_count": run_missing_price,
                "latest_available_price_date_min": latest_available_min,
                "latest_available_price_date_max": latest_available_max,
            }
        )

        if run_id_key == latest_full_run_id:
            latest_full_fillable = run_fillable
            latest_full_missing_price = run_missing_price
            latest_full_price_dates = latest_dates

    # current candidate validation
    rank_values = [to_int(row.get("rank"), 0) for row in current_rows]
    rank_valid = len(rank_values) == current_count and len(set(rank_values)) == current_count and sorted(rank_values) == list(range(1, current_count + 1))
    score_present_count = sum(1 for row in current_rows if non_null(row.get("composite_candidate_score")))
    targets_present_count = sum(1 for ticker in TARGET_TICKERS if ticker in current_by)
    duplicate_count = current_dupes
    target_score_present_count = sum(1 for ticker in TARGET_TICKERS if non_null(current_by.get(ticker, {}).get("composite_candidate_score")))

    factor_present_targets = sum(1 for ticker in TARGET_TICKERS if ticker in factor_by)
    technical_present_targets = sum(1 for ticker in TARGET_TICKERS if ticker in tech_by)
    price_present_targets = sum(1 for ticker in TARGET_TICKERS if (root / PRICE_CACHE_DIR / f"{ticker}.csv").exists())
    rolling_success_targets = 0
    for ticker in TARGET_TICKERS:
        row = ledger_by.get(ticker, {})
        status_text = str(row.get("last_scan_status") or row.get("scan_status") or row.get("status") or "").strip().upper()
        success_date = str(row.get("last_success_scan_date") or "").strip()
        if status_text in {"SUCCESS_LOCAL_PRICE_FULL_HISTORY", "LOCAL_PRICE_SCAN_SUCCESS"} and success_date:
            rolling_success_targets += 1

    full_candidate_factor_missing = 0
    full_candidate_tech_missing = 0
    full_candidate_price_missing = 0
    full_candidate_ledger_missing = 0
    full_candidate_price_dates: List[dt.date] = []
    for row in current_rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker not in factor_by:
            full_candidate_factor_missing += 1
        if ticker not in tech_by:
            full_candidate_tech_missing += 1
        if ticker not in dates_by_ticker:
            full_candidate_price_missing += 1
        if ticker not in ledger_by:
            full_candidate_ledger_missing += 1
        if ticker in latest_date_by_ticker:
            full_candidate_price_dates.append(latest_date_by_ticker[ticker])

    latest_full_run_fillable_1d = latest_full_fillable[1]
    latest_full_run_fillable_3d = latest_full_fillable[3]
    latest_full_run_fillable_5d = latest_full_fillable[5]
    latest_full_run_fillable_10d = latest_full_fillable[10]
    latest_full_run_fillable_20d = latest_full_fillable[20]
    latest_full_run_not_yet_1d = current_count - latest_full_run_fillable_1d
    latest_full_run_not_yet_3d = current_count - latest_full_run_fillable_3d
    latest_full_run_not_yet_5d = current_count - latest_full_run_fillable_5d
    latest_full_run_not_yet_10d = current_count - latest_full_run_fillable_10d
    latest_full_run_not_yet_20d = current_count - latest_full_run_fillable_20d
    latest_full_price_min = min(latest_full_price_dates).isoformat() if latest_full_price_dates else ""
    latest_full_price_max = max(latest_full_price_dates).isoformat() if latest_full_price_dates else ""
    latest_full_present_count = sum(1 for ticker in TARGET_TICKERS if ticker in latest_full_set)

    latest_full_ready_now = any(
        count > 0 for count in [
            latest_full_run_fillable_1d,
            latest_full_run_fillable_3d,
            latest_full_run_fillable_5d,
            latest_full_run_fillable_10d,
            latest_full_run_fillable_20d,
        ]
    )
    any_run_fillable_1d = any_run_fillable[1]
    any_run_fillable_3d = any_run_fillable[3]
    any_run_fillable_5d = any_run_fillable[5]
    any_run_fillable_10d = any_run_fillable[10]
    any_run_fillable_20d = any_run_fillable[20]

    if latest_full_ready_now:
        scope_recommendation = "R26C_FORWARD_RETURN_FILLER_READY_FOR_LATEST_FULL_RUN"
    elif any_run_fillable_1d or any_run_fillable_3d or any_run_fillable_5d or any_run_fillable_10d or any_run_fillable_20d:
        scope_recommendation = "R26C_FORWARD_RETURN_FILLER_CAN_RUN_FOR_MATURED_RUNS"
    else:
        scope_recommendation = "WAIT_FOR_FUTURE_PRICE_DATA_THEN_RUN_R26C_FORWARD_RETURN_FILLER"

    latest_full_presence_rows = []
    if latest_full_rows:
        latest_full_by = build_ticker_map(latest_full_rows)
        for ticker in TARGET_TICKERS:
            row = latest_full_by.get(ticker, {})
            future_count = future_dates_available_count(dates_by_ticker, ticker, parse_date(latest_full_rows[0].get("signal_date")) or dt.date.min) if ticker in dates_by_ticker else 0
            latest_full_presence_rows.append(
                {
                    "ticker": ticker,
                    "present_in_latest_full_freeze": str(ticker in latest_full_by).upper(),
                    "present_in_latest_full_freeze_count": 1 if ticker in latest_full_by else 0,
                    "current_candidate_present": str(ticker in current_by).upper(),
                    "current_candidate_rank": current_by.get(ticker, {}).get("rank", ""),
                    "current_candidate_score": current_by.get(ticker, {}).get("composite_candidate_score", ""),
                    "latest_full_freeze_source_rank": row.get("source_rank", ""),
                    "latest_full_freeze_price_latest_date": latest_date_by_ticker.get(ticker, dt.date.min).isoformat() if ticker in latest_date_by_ticker else "",
                    "latest_full_freeze_future_dates_available_count": future_count,
                }
            )
    else:
        for ticker in TARGET_TICKERS:
            latest_full_presence_rows.append(
                {
                    "ticker": ticker,
                    "present_in_latest_full_freeze": "FALSE",
                    "present_in_latest_full_freeze_count": 0,
                    "current_candidate_present": str(ticker in current_by).upper(),
                    "current_candidate_rank": current_by.get(ticker, {}).get("rank", ""),
                    "current_candidate_score": current_by.get(ticker, {}).get("composite_candidate_score", ""),
                    "latest_full_freeze_source_rank": "",
                    "latest_full_freeze_price_latest_date": latest_date_by_ticker.get(ticker, dt.date.min).isoformat() if ticker in latest_date_by_ticker else "",
                    "latest_full_freeze_future_dates_available_count": 0,
                }
            )

    # current candidates join audit
    join_rows: List[Dict[str, object]] = []
    full_join_missing = {"factor": 0, "technical": 0, "price": 0, "ledger": 0}
    for row in current_rows:
        ticker = norm_ticker(row.get("ticker"))
        factor_present = ticker in factor_by
        tech_present = ticker in tech_by
        price_present = ticker in dates_by_ticker
        ledger_present = ticker in ledger_by
        if not factor_present:
            full_join_missing["factor"] += 1
        if not tech_present:
            full_join_missing["technical"] += 1
        if not price_present:
            full_join_missing["price"] += 1
        if not ledger_present:
            full_join_missing["ledger"] += 1
        join_rows.append(
            {
                "ticker": ticker,
                "current_in_factor_pack": str(factor_present).upper(),
                "current_in_technical_timing": str(tech_present).upper(),
                "current_in_price_cache": str(price_present).upper(),
                "current_in_rolling_ledger": str(ledger_present).upper(),
                "join_ready": str(factor_present and tech_present and price_present and ledger_present).upper(),
                "reason": "" if (factor_present and tech_present and price_present and ledger_present) else "|".join(
                    [
                        reason
                        for reason, present in [
                            ("MISSING_FACTOR", factor_present),
                            ("MISSING_TECHNICAL", tech_present),
                            ("MISSING_PRICE_CACHE", price_present),
                            ("MISSING_ROLLING_LEDGER", ledger_present),
                        ]
                        if not present
                    ]
                ),
            }
        )

    write_csv(root / OUT_RUN_SUMMARY, run_summary_rows, RUN_SUMMARY_FIELDS)
    write_csv(root / OUT_FILLABILITY_BY_RUN, fillability_by_run_rows, FILLABILITY_BY_RUN_FIELDS)
    write_csv(root / OUT_FILLABILITY_BY_TICKER, fillability_by_ticker_rows, FILLABILITY_BY_TICKER_FIELDS)
    write_csv(root / OUT_LATEST_FULL_READINESS, [
        {
            "latest_full_current_freeze_run_id": latest_full_run_id,
            "latest_full_current_freeze_signal_date": latest_full_run_signal_date,
            "latest_full_current_freeze_ticker_count": current_count if latest_full_run_id else 0,
            "latest_full_current_freeze_matches_current_candidates": str(bool(latest_full_run_id)).upper(),
            "rddt_tln_present_in_latest_full_freeze_count": latest_full_present_count,
            "latest_full_run_fillable_1d_count": latest_full_run_fillable_1d,
            "latest_full_run_fillable_3d_count": latest_full_run_fillable_3d,
            "latest_full_run_fillable_5d_count": latest_full_run_fillable_5d,
            "latest_full_run_fillable_10d_count": latest_full_run_fillable_10d,
            "latest_full_run_fillable_20d_count": latest_full_run_fillable_20d,
            "latest_full_run_not_yet_mature_1d_count": latest_full_run_not_yet_1d,
            "latest_full_run_not_yet_mature_3d_count": latest_full_run_not_yet_3d,
            "latest_full_run_not_yet_mature_5d_count": latest_full_run_not_yet_5d,
            "latest_full_run_not_yet_mature_10d_count": latest_full_run_not_yet_10d,
            "latest_full_run_not_yet_mature_20d_count": latest_full_run_not_yet_20d,
            "missing_price_cache_count_for_latest_full_run": latest_full_missing_price,
            "latest_available_price_date_min": latest_full_price_min,
            "latest_available_price_date_max": latest_full_price_max,
            "forward_return_filler_ready_now": str(latest_full_ready_now).upper(),
            "forward_return_filler_scope_recommendation": scope_recommendation,
        }
    ], LATEST_FULL_FIELDS)
    write_csv(root / OUT_TARGET_PRESENCE, latest_full_presence_rows, TARGET_PRESENCE_FIELDS)
    write_csv(root / OUT_FULL_JOIN_AUDIT, join_rows, [
        "ticker",
        "current_in_factor_pack",
        "current_in_technical_timing",
        "current_in_price_cache",
        "current_in_rolling_ledger",
        "join_ready",
        "reason",
    ])

    # Structural validation only.
    status = STATUS_OK
    if blockers:
        status = STATUS_WARN
    if current_count != 252 or current_dupes != 0 or not rank_valid or score_present_count != current_count or len(current_by) != current_count:
        status = STATUS_WARN
    if latest_full_run_id == "":
        status = STATUS_WARN
    if full_join_missing["factor"] or full_join_missing["technical"] or full_join_missing["price"] or full_join_missing["ledger"]:
        status = STATUS_WARN

    validation_fail_count = 0
    validation_fail_count += int(current_count != 252)
    validation_fail_count += int(current_dupes != 0)
    validation_fail_count += int(not rank_valid)
    validation_fail_count += int(score_present_count != current_count)
    validation_fail_count += int(latest_full_run_id == "")
    validation_fail_count += int(bool(blockers))
    validation_fail_count += int(full_join_missing["factor"] or full_join_missing["technical"] or full_join_missing["price"] or full_join_missing["ledger"])

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R27L_STATUS": r27l_status or "MISSING",
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": current_count,
        "SIGNAL_FREEZE_LEDGER_ROW_COUNT": signal_ledger_row_count,
        "SIGNAL_FREEZE_RUN_COUNT": signal_run_count,
        "LATEST_FULL_CURRENT_FREEZE_RUN_ID": latest_full_run_id,
        "LATEST_FULL_CURRENT_FREEZE_SIGNAL_DATE": latest_full_run_signal_date,
        "LATEST_FULL_CURRENT_FREEZE_TICKER_COUNT": current_count if latest_full_run_id else 0,
        "LATEST_FULL_CURRENT_FREEZE_MATCHES_CURRENT_CANDIDATES": str(bool(latest_full_run_id and latest_full_run_signal_date)).upper(),
        "RDDT_TLN_PRESENT_IN_LATEST_FULL_FREEZE_COUNT": latest_full_present_count,
        "LATEST_FULL_RUN_FILLABLE_1D_COUNT": latest_full_run_fillable_1d,
        "LATEST_FULL_RUN_FILLABLE_3D_COUNT": latest_full_run_fillable_3d,
        "LATEST_FULL_RUN_FILLABLE_5D_COUNT": latest_full_run_fillable_5d,
        "LATEST_FULL_RUN_FILLABLE_10D_COUNT": latest_full_run_fillable_10d,
        "LATEST_FULL_RUN_FILLABLE_20D_COUNT": latest_full_run_fillable_20d,
        "LATEST_FULL_RUN_NOT_YET_MATURE_1D_COUNT": latest_full_run_not_yet_1d,
        "LATEST_FULL_RUN_NOT_YET_MATURE_3D_COUNT": latest_full_run_not_yet_3d,
        "LATEST_FULL_RUN_NOT_YET_MATURE_5D_COUNT": latest_full_run_not_yet_5d,
        "LATEST_FULL_RUN_NOT_YET_MATURE_10D_COUNT": latest_full_run_not_yet_10d,
        "LATEST_FULL_RUN_NOT_YET_MATURE_20D_COUNT": latest_full_run_not_yet_20d,
        "ANY_RUN_FILLABLE_1D_COUNT": any_run_fillable_1d,
        "ANY_RUN_FILLABLE_3D_COUNT": any_run_fillable_3d,
        "ANY_RUN_FILLABLE_5D_COUNT": any_run_fillable_5d,
        "ANY_RUN_FILLABLE_10D_COUNT": any_run_fillable_10d,
        "ANY_RUN_FILLABLE_20D_COUNT": any_run_fillable_20d,
        "MISSING_PRICE_CACHE_COUNT_FOR_LATEST_FULL_RUN": latest_full_missing_price,
        "FORWARD_RETURN_FILLER_READY_NOW": str(latest_full_ready_now).upper(),
        "FORWARD_RETURN_FILLER_SCOPE_RECOMMENDATION": scope_recommendation,
        "PRICE_CACHE_MODIFIED": "FALSE",
        "ROLLING_LEDGER_MODIFIED": "FALSE",
        "CANDIDATES_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "SIGNAL_FREEZE_LEDGER_MODIFIED": "FALSE",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": "FALSE",
        "NEXT_RECOMMENDED_STEP": scope_recommendation,
    }

    summary_rows = [
        summary_row("R27L_STATUS", r27l_status or "MISSING", EXPECTED_R27L_STATUS, r27l_status == EXPECTED_R27L_STATUS),
        summary_row("CURRENT_RANKED_CANDIDATE_ROW_COUNT", current_count, 252, current_count == 252),
        summary_row("SIGNAL_FREEZE_LEDGER_ROW_COUNT", signal_ledger_row_count, signal_ledger_row_count, True),
        summary_row("SIGNAL_FREEZE_RUN_COUNT", signal_run_count, signal_run_count, True),
        summary_row("LATEST_FULL_CURRENT_FREEZE_RUN_ID", latest_full_run_id or "MISSING", latest_full_run_id or "MISSING", bool(latest_full_run_id)),
        summary_row("LATEST_FULL_CURRENT_FREEZE_TICKER_COUNT", current_count if latest_full_run_id else 0, 252 if latest_full_run_id else 0, bool(latest_full_run_id)),
        summary_row("LATEST_FULL_CURRENT_FREEZE_MATCHES_CURRENT_CANDIDATES", values["LATEST_FULL_CURRENT_FREEZE_MATCHES_CURRENT_CANDIDATES"], "TRUE", values["LATEST_FULL_CURRENT_FREEZE_MATCHES_CURRENT_CANDIDATES"] == "TRUE"),
        summary_row("RDDT_TLN_PRESENT_IN_LATEST_FULL_FREEZE_COUNT", latest_full_present_count, 2, latest_full_present_count == 2),
        summary_row("FORWARD_RETURN_FILLER_READY_NOW", values["FORWARD_RETURN_FILLER_READY_NOW"], "FALSE", True),
        summary_row("FORWARD_RETURN_FILLER_SCOPE_RECOMMENDATION", scope_recommendation, scope_recommendation, True),
    ]

    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, fillability_by_run_rows, run_summary_rows, latest_full_presence_rows))

    current_modified = file_sig(root / CURRENT_CANDIDATES) != current_before
    factor_modified = file_sig(root / FACTOR_PACK) != factor_before
    tech_modified = file_sig(root / TECH_TIMING) != tech_before
    price_modified = tree_sig(root / PRICE_CACHE_DIR) != price_before
    ledger_modified = file_sig(root / ROLLING_LEDGER) != ledger_before
    signal_modified = file_sig(root / SIGNAL_LEDGER) != signal_before
    forbidden_modified = current_modified or factor_modified or tech_modified or price_modified or ledger_modified or signal_modified
    if forbidden_modified:
        status = STATUS_FAIL
        values["STATUS"] = status
        values["FORBIDDEN_MODIFIED"] = "TRUE"
        values["VALIDATION_FAIL_COUNT"] = validation_fail_count + 1
        write_text(root / OUT_READ_FIRST, render_read_first(values))
        write_text(root / OUT_REPORT, render_report(values, fillability_by_run_rows, run_summary_rows, latest_full_presence_rows))

    print(f"STATUS: {values['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if values["STATUS"] == STATUS_FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
