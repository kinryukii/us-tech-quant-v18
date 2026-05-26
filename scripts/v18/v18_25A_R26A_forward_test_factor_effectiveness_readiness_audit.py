from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R26A_FORWARD_TEST_FACTOR_EFFECTIVENESS_READINESS_READY"
STATUS_SIGNAL_REFRESH = "WARN_V18_25A_R26A_SIGNAL_FREEZE_REFRESH_NEEDED"
STATUS_JOIN_GAPS = "WARN_V18_25A_R26A_INPUT_JOIN_GAPS"
STATUS_FORWARD_NOT_FILLABLE = "WARN_V18_25A_R26A_FORWARD_RETURN_NOT_YET_FILLABLE"
STATUS_LEDGER_MISSING = "WARN_V18_25A_R26A_SIGNAL_LEDGER_MISSING"
STATUS_CURRENT_MISSING = "WARN_V18_25A_R26A_CURRENT_CANDIDATES_MISSING"

MODE = "READ_ONLY_FORWARD_TEST_FACTOR_EFFECTIVENESS_READINESS_AUDIT"
EXPECTED_CURRENT_ROWS = 250
EXPECTED_TOPN = 250

CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"
SIGNAL_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
FACTOR_PACK = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECHNICAL_TIMING = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
PRICE_CACHE = "state/v18/price_cache"
ROLLING_LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
R21_READ_FIRST = "outputs/v18/ops/V18_25A_R21_READ_FIRST.txt"
R25G_READ_FIRST = "outputs/v18/ops/V18_25A_R25G_READ_FIRST.txt"

OUT_INPUT_READINESS = "outputs/v18/factor_validation/V18_25A_R26A_CURRENT_INPUT_READINESS.csv"
OUT_SIGNAL_AUDIT = "outputs/v18/factor_validation/V18_25A_R26A_CURRENT_SIGNAL_LEDGER_AUDIT.csv"
OUT_JOIN_AUDIT = "outputs/v18/factor_validation/V18_25A_R26A_CURRENT_RANKED_CANDIDATE_JOIN_AUDIT.csv"
OUT_FORWARD_READINESS = "outputs/v18/factor_validation/V18_25A_R26A_CURRENT_FORWARD_RETURN_FILL_READINESS.csv"
OUT_SUMMARY = "outputs/v18/factor_validation/V18_25A_R26A_CURRENT_FACTOR_EFFECTIVENESS_READINESS_SUMMARY.csv"
OUT_BLOCKERS = "outputs/v18/factor_validation/V18_25A_R26A_CURRENT_BLOCKERS_AND_NEXT_ACTIONS.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R26A_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R26A_CURRENT_FORWARD_TEST_FACTOR_EFFECTIVENESS_READINESS_REPORT.md"

INPUT_FIELDS = [
    "input_name", "exists", "row_count", "ticker_column", "score_column", "status", "notes",
]
SIGNAL_FIELDS = [
    "ticker", "signal_date", "signal_row_present", "ledger_row_count_for_date", "forward_fill_status",
    "current_universe_match", "needs_refresh_after_r25g", "notes",
]
JOIN_FIELDS = [
    "ticker", "current_in_factor_pack", "current_in_technical_timing", "current_in_price_cache",
    "current_in_rolling_ledger", "join_ready", "reason",
]
FORWARD_FIELDS = [
    "ticker", "forward_return_pending", "fillable_1d", "fillable_3d", "fillable_5d", "fillable_10d",
    "fillable_20d", "reason",
]
SUMMARY_FIELDS = ["metric", "value"]
BLOCKER_FIELDS = ["blocker_type", "count", "reason", "next_action"]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "RUN_ID", "TOP_N", "SIGNAL_LOOKBACK_DAYS", "CURRENT_RANKED_CANDIDATES_PATH",
    "CURRENT_RANKED_CANDIDATES_ROW_COUNT", "CURRENT_RANKED_CANDIDATES_DUPLICATE_TICKER_COUNT",
    "FACTOR_PACK_ROW_COUNT", "TECHNICAL_TIMING_ROW_COUNT", "SIGNAL_FREEZE_LEDGER_PATH", "SIGNAL_FREEZE_LEDGER_EXISTS",
    "SIGNAL_FREEZE_LEDGER_ROW_COUNT", "SIGNAL_FREEZE_LATEST_SIGNAL_DATE", "SIGNAL_FREEZE_LATEST_RUN_ID",
    "SIGNAL_FREEZE_LATEST_RUN_ROW_COUNT", "SIGNAL_FREEZE_LATEST_RUN_DISTINCT_TICKER_COUNT",
    "SIGNAL_FREEZE_LATEST_RUN_DUPLICATE_TICKER_COUNT", "SIGNAL_FREEZE_LATEST_RUN_TICKER_MATCH_CURRENT",
    "SIGNAL_FREEZE_LATEST_RUN_MISSING_CURRENT_TICKER_COUNT", "SIGNAL_FREEZE_LATEST_RUN_EXTRA_TICKER_COUNT",
    "SIGNAL_FREEZE_CURRENT_UNIVERSE_MATCH", "SIGNAL_FREEZE_NEEDS_REFRESH_AFTER_R25G",
    "CURRENT_CANDIDATE_FACTOR_JOIN_COUNT", "CURRENT_CANDIDATE_TECHNICAL_JOIN_COUNT",
    "CURRENT_CANDIDATE_PRICE_CACHE_JOIN_COUNT", "CURRENT_CANDIDATE_ROLLING_LEDGER_JOIN_COUNT",
    "FORWARD_RETURN_PENDING_COUNT", "FORWARD_RETURN_FILLABLE_1D_COUNT", "FORWARD_RETURN_FILLABLE_3D_COUNT",
    "FORWARD_RETURN_FILLABLE_5D_COUNT", "FORWARD_RETURN_FILLABLE_10D_COUNT", "FORWARD_RETURN_FILLABLE_20D_COUNT",
    "FACTOR_EFFECTIVENESS_READY_NOW", "FORWARD_RETURN_FILLER_READY_NOW", "RECOMMENDED_NEXT_SIGNAL_FREEZE",
    "RECOMMENDED_NEXT_FORWARD_RETURN_FILL", "INPUT_READINESS_PATH", "SIGNAL_LEDGER_AUDIT_PATH",
    "RANKED_CANDIDATE_JOIN_AUDIT_PATH", "FORWARD_RETURN_FILL_READINESS_PATH", "BLOCKERS_AND_NEXT_ACTIONS_PATH",
    "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL", "EXTERNAL_FETCH_EXECUTED", "BACKTEST_EXECUTED",
    "PRICE_CACHE_MODIFIED", "ROLLING_LEDGER_MODIFIED", "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "TIER_FILES_MODIFIED", "OFFICIAL_DECISION_MODIFIED", "CURRENT_RANKED_CANDIDATES_MODIFIED",
    "SIGNAL_LEDGER_MODIFIED", "VALIDATION_FAIL_COUNT", "FORBIDDEN_MODIFIED", "NEXT_RECOMMENDED_STEP",
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


def read_first(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    out: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def to_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip().replace(",", "")
        return float(text) if text else None
    except Exception:
        return None


def ticker_counts(rows: List[Dict[str, str]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker:
            counts[ticker] = counts.get(ticker, 0) + 1
    return counts


def duplicate_ticker_count(rows: List[Dict[str, str]]) -> int:
    return sum(1 for count in ticker_counts(rows).values() if count > 1)


def score_column(fields: Sequence[str], candidates: Sequence[str]) -> str:
    lower = {field.lower(): field for field in fields}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return ""


def signal_ledger_rows_for_date(rows: List[Dict[str, str]], signal_date: str) -> List[Dict[str, str]]:
    return [row for row in rows if str(row.get("signal_date", "")).strip() == signal_date]


def latest_signal_date(rows: List[Dict[str, str]]) -> str:
    dates = sorted({str(row.get("signal_date", "")).strip() for row in rows if str(row.get("signal_date", "")).strip()})
    return dates[-1] if dates else ""


def parse_dt(value: object) -> Optional[dt.datetime]:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d_%H%M%S"):
        try:
            return dt.datetime.strptime(text, fmt)
        except Exception:
            continue
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def run_sort_key(row: Dict[str, str]) -> Tuple[int, dt.datetime, str, str]:
    ts = parse_dt(row.get("run_timestamp"))
    if ts is not None:
        return (3, ts, str(row.get("signal_date", "")).strip(), str(row.get("run_id", "")).strip())
    ts = parse_dt(row.get("run_id"))
    if ts is not None:
        return (2, ts, str(row.get("signal_date", "")).strip(), str(row.get("run_id", "")).strip())
    sig = str(row.get("signal_date", "")).strip()
    sig_dt = parse_dt(sig + "T00:00:00") or dt.datetime.min
    return (1, sig_dt, sig, str(row.get("run_id", "")).strip())


def latest_run_rows(rows: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
    if not rows:
        return "", []
    latest = max(rows, key=run_sort_key)
    latest_id = str(latest.get("run_id", "")).strip()
    if not latest_id:
        latest_id = str(latest.get("run_timestamp", "")).strip() or str(latest.get("signal_date", "")).strip()
    filtered = [row for row in rows if str(row.get("run_id", "")).strip() == latest_id]
    if not filtered:
        filtered = [latest]
    return latest_id, filtered


def get_price_dates(price_root: Path, tickers: List[str]) -> Dict[str, List[str]]:
    dates: Dict[str, List[str]] = {}
    for ticker in tickers:
        path = price_root / f"{ticker}.csv"
        rows, fields = read_csv(path)
        if not rows or "date" not in {f.lower() for f in fields}:
            continue
        date_col = next((f for f in fields if f.lower() == "date"), "")
        series = sorted({str(row.get(date_col, "")).strip()[:10] for row in rows if str(row.get(date_col, "")).strip()})
        dates[ticker] = series
    return dates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--top-n", type=int, default=250)
    parser.add_argument("--signal-lookback-days", type=int, default=30)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R26A_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    today = dt.date.today().isoformat()
    before = {
        "price": None,
        "ledger": file_sig(root / ROLLING_LEDGER),
        "factor": file_sig(root / FACTOR_PACK),
        "technical": file_sig(root / TECHNICAL_TIMING),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
        "current": file_sig(root / CURRENT_CANDIDATES),
        "signal": file_sig(root / SIGNAL_LEDGER),
    }

    current_rows, current_fields = read_csv(root / CURRENT_CANDIDATES)
    signal_rows, signal_fields = read_csv(root / SIGNAL_LEDGER)
    factor_rows, factor_fields = read_csv(root / FACTOR_PACK)
    tech_rows, tech_fields = read_csv(root / TECHNICAL_TIMING)
    ledger_rows, ledger_fields = read_csv(root / ROLLING_LEDGER)
    r25g = read_first(root / R25G_READ_FIRST)
    r21 = read_first(root / R21_READ_FIRST)

    current_count = len(current_rows)
    current_dupes = duplicate_ticker_count(current_rows)
    current_tickers = [norm_ticker(row.get("ticker")) for row in current_rows if norm_ticker(row.get("ticker"))][: max(args.top_n, 0)]
    current_set = set(current_tickers)
    current_factor_score_col = score_column(current_fields, ["composite_candidate_score", "candidate_score", "score"])
    current_rank_col = score_column(current_fields, ["rank", "priority_rank", "candidate_rank"])
    factor_score_col = score_column(factor_fields, ["factor_pack_score", "factor_score"])
    tech_score_col = score_column(tech_fields, ["technical_timing_score", "technical_score"])
    factor_by = {norm_ticker(row.get("ticker")): row for row in factor_rows if norm_ticker(row.get("ticker"))}
    tech_by = {norm_ticker(row.get("ticker")): row for row in tech_rows if norm_ticker(row.get("ticker"))}
    ledger_by = {norm_ticker(row.get("ticker")): row for row in ledger_rows if norm_ticker(row.get("ticker"))}
    price_dates = get_price_dates(root / PRICE_CACHE, current_tickers)

    signal_exists = (root / SIGNAL_LEDGER).exists()
    signal_row_count = len(signal_rows)
    signal_latest_run_id, signal_latest_rows = latest_run_rows(signal_rows)
    signal_latest_signal_date = latest_signal_date(signal_latest_rows)
    signal_latest_run_distinct = len({norm_ticker(row.get("ticker")) for row in signal_latest_rows if norm_ticker(row.get("ticker"))})
    signal_latest_run_dupes = duplicate_ticker_count(signal_latest_rows)
    signal_latest_run_set = {norm_ticker(row.get("ticker")) for row in signal_latest_rows if norm_ticker(row.get("ticker"))}
    signal_latest_run_match = signal_exists and bool(signal_latest_run_id) and signal_latest_run_set == current_set
    signal_latest_run_missing = len(current_set - signal_latest_run_set)
    signal_latest_run_extra = len(signal_latest_run_set - current_set)
    signal_current_universe_match = signal_latest_run_match
    signal_needs_refresh = not signal_exists or not signal_latest_run_id or signal_latest_run_distinct != len(current_set) or not signal_latest_run_match

    input_rows = []
    input_rows.append({"input_name": "current_ranked_candidates", "exists": str((root / CURRENT_CANDIDATES).exists()).upper(), "row_count": current_count, "ticker_column": "ticker" if "ticker" in current_fields else "", "score_column": current_factor_score_col, "status": "PASS" if current_count == EXPECTED_CURRENT_ROWS and current_dupes == 0 and current_rank_col and current_factor_score_col else "FAIL", "notes": "Current ranked candidates after R25G."})
    input_rows.append({"input_name": "signal_freeze_ledger", "exists": str(signal_exists).upper(), "row_count": signal_row_count, "ticker_column": "ticker" if "ticker" in signal_fields else "", "score_column": "composite_candidate_score" if "composite_candidate_score" in signal_fields else "", "status": "PASS" if signal_exists else "FAIL", "notes": "R21 freeze ledger should be refreshed after R25G."})
    input_rows.append({"input_name": "factor_pack", "exists": str((root / FACTOR_PACK).exists()).upper(), "row_count": len(factor_rows), "ticker_column": "ticker" if "ticker" in factor_fields else "", "score_column": factor_score_col, "status": "PASS" if factor_score_col else "FAIL", "notes": "Current official factor pack."})
    input_rows.append({"input_name": "technical_timing", "exists": str((root / TECHNICAL_TIMING).exists()).upper(), "row_count": len(tech_rows), "ticker_column": "ticker" if "ticker" in tech_fields else "", "score_column": tech_score_col, "status": "PASS" if tech_score_col else "FAIL", "notes": "Current official technical timing."})
    input_rows.append({"input_name": "rolling_ledger", "exists": str((root / ROLLING_LEDGER).exists()).upper(), "row_count": len(ledger_rows), "ticker_column": "ticker" if "ticker" in ledger_fields else "", "score_column": "", "status": "PASS" if ledger_rows else "FAIL", "notes": "Rolling coverage ledger."})
    input_rows.append({"input_name": "price_cache", "exists": str((root / PRICE_CACHE).exists()).upper(), "row_count": len(list((root / PRICE_CACHE).glob("*.csv"))) if (root / PRICE_CACHE).exists() else 0, "ticker_column": "filename", "score_column": "", "status": "PASS" if (root / PRICE_CACHE).exists() else "FAIL", "notes": "Local price cache directory."})

    signal_audit_rows = [
        {
            "ticker": row.get("ticker", ""),
            "signal_date": row.get("signal_date", ""),
            "signal_row_present": "TRUE",
            "ledger_row_count_for_date": len(signal_latest_rows),
            "forward_fill_status": row.get("forward_fill_status", ""),
            "current_universe_match": str(signal_current_universe_match).upper(),
            "needs_refresh_after_r25g": str(signal_needs_refresh).upper(),
            "notes": "Latest R21 freeze slice compared against current candidates." if signal_current_universe_match else "Latest R21 freeze slice does not match current candidates.",
        }
        for row in signal_latest_rows[: min(len(signal_latest_rows), args.top_n)]
    ]

    current_join_rows: List[Dict[str, object]] = []
    forward_rows: List[Dict[str, object]] = []
    blockers: List[Dict[str, object]] = []
    factor_join_count = tech_join_count = price_join_count = ledger_join_count = 0
    forward_pending_count = 0
    fill_1d = fill_3d = fill_5d = fill_10d = fill_20d = 0
    for ticker in current_tickers:
        factor_present = ticker in factor_by
        tech_present = ticker in tech_by
        price_present = (root / PRICE_CACHE / f"{ticker}.csv").exists()
        ledger_present = ticker in ledger_by
        if factor_present:
            factor_join_count += 1
        if tech_present:
            tech_join_count += 1
        if price_present:
            price_join_count += 1
        if ledger_present:
            ledger_join_count += 1
        join_ready = factor_present and tech_present and price_present and ledger_present
        reasons = []
        if not factor_present:
            reasons.append("MISSING_FACTOR")
        if not tech_present:
            reasons.append("MISSING_TECHNICAL")
        if not price_present:
            reasons.append("MISSING_PRICE_CACHE")
        if not ledger_present:
            reasons.append("MISSING_ROLLING_LEDGER")
        if reasons:
            blockers.append({
                "blocker_type": "JOIN_GAP",
                "count": 1,
                "reason": "|".join(reasons),
                "next_action": "Refresh R21 signal freeze after R25G and re-run join audit.",
            })
        current_join_rows.append({
            "ticker": ticker,
            "current_in_factor_pack": str(factor_present).upper(),
            "current_in_technical_timing": str(tech_present).upper(),
            "current_in_price_cache": str(price_present).upper(),
            "current_in_rolling_ledger": str(ledger_present).upper(),
            "join_ready": str(join_ready).upper(),
            "reason": "|".join(reasons),
        })

        # Forward returns remain pending until future bars exist; this audit only checks readiness.
        pending = True
        forward_rows.append({
            "ticker": ticker,
            "forward_return_pending": str(pending).upper(),
            "fillable_1d": "FALSE",
            "fillable_3d": "FALSE",
            "fillable_5d": "FALSE",
            "fillable_10d": "FALSE",
            "fillable_20d": "FALSE",
            "reason": "No future-day buffer is available in the local cache for forward-return fill.",
        })
        forward_pending_count += 1

    current_join_count = sum(1 for row in current_join_rows if row["join_ready"] == "TRUE")
    full_ready = current_join_count == len(current_join_rows) and signal_current_universe_match
    forward_ready = False

    summary_rows = [
        {"metric": "current_ranked_candidates_row_count", "value": current_count},
        {"metric": "signal_freeze_ledger_row_count", "value": signal_row_count},
        {"metric": "signal_freeze_latest_run_row_count", "value": len(signal_latest_rows)},
        {"metric": "signal_freeze_latest_run_distinct_ticker_count", "value": signal_latest_run_distinct},
        {"metric": "signal_freeze_latest_run_duplicate_ticker_count", "value": signal_latest_run_dupes},
        {"metric": "signal_freeze_latest_run_ticker_match_current", "value": str(signal_latest_run_match).upper()},
        {"metric": "signal_freeze_latest_run_missing_current_ticker_count", "value": signal_latest_run_missing},
        {"metric": "signal_freeze_latest_run_extra_ticker_count", "value": signal_latest_run_extra},
        {"metric": "signal_freeze_needs_refresh_after_r25g", "value": str(signal_needs_refresh).upper()},
        {"metric": "factor_join_count", "value": factor_join_count},
        {"metric": "technical_join_count", "value": tech_join_count},
        {"metric": "price_cache_join_count", "value": price_join_count},
        {"metric": "rolling_ledger_join_count", "value": ledger_join_count},
        {"metric": "forward_return_pending_count", "value": forward_pending_count},
        {"metric": "forward_return_fillable_1d_count", "value": fill_1d},
        {"metric": "forward_return_fillable_3d_count", "value": fill_3d},
        {"metric": "forward_return_fillable_5d_count", "value": fill_5d},
        {"metric": "forward_return_fillable_10d_count", "value": fill_10d},
        {"metric": "forward_return_fillable_20d_count", "value": fill_20d},
        {"metric": "factor_effectiveness_ready_now", "value": str(False if signal_needs_refresh else full_ready).upper()},
        {"metric": "forward_return_filler_ready_now", "value": str(forward_ready).upper()},
    ]

    blocker_rows = [
        {"blocker_type": "SIGNAL_FREEZE_REFRESH_NEEDED" if signal_needs_refresh else "NONE", "count": 1 if signal_needs_refresh else 0, "reason": "Latest R21 signal freeze slice does not match the current ranked candidates." if signal_needs_refresh else "Latest R21 signal freeze slice matches the current ranked candidates.", "next_action": "Run R21 signal freeze again using the updated current ranked candidates." if signal_needs_refresh else "No signal freeze refresh needed; latest R21 signal freeze matches the current ranked candidate universe."},
        {"blocker_type": "FORWARD_RETURN_NOT_YET_FILLABLE", "count": forward_pending_count, "reason": "Future-day bars are not yet available locally for 1D/3D/5D/10D/20D fills.", "next_action": "Wait until sufficient future trading days/bars exist, then run R26B forward return filler."},
    ]

    write_csv(root / OUT_INPUT_READINESS, input_rows, INPUT_FIELDS)
    write_csv(root / OUT_SIGNAL_AUDIT, signal_audit_rows, SIGNAL_FIELDS)
    write_csv(root / OUT_JOIN_AUDIT, current_join_rows, JOIN_FIELDS)
    write_csv(root / OUT_FORWARD_READINESS, forward_rows, FORWARD_FIELDS)
    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_csv(root / OUT_BLOCKERS, blocker_rows, BLOCKER_FIELDS)

    after = {
        "price": None,
        "ledger": file_sig(root / ROLLING_LEDGER),
        "factor": file_sig(root / FACTOR_PACK),
        "technical": file_sig(root / TECHNICAL_TIMING),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
        "current": file_sig(root / CURRENT_CANDIDATES),
        "signal": file_sig(root / SIGNAL_LEDGER),
    }
    mods = {key: before[key] != after[key] for key in before if key != "price"}
    forbidden = any(mods.values())

    status = STATUS_OK
    if not (root / CURRENT_CANDIDATES).exists():
        status = STATUS_CURRENT_MISSING
    elif not signal_exists:
        status = STATUS_LEDGER_MISSING
    elif factor_join_count != current_count or tech_join_count != current_count or price_join_count != current_count or ledger_join_count != current_count:
        status = STATUS_JOIN_GAPS
    elif fill_1d == fill_3d == fill_5d == fill_10d == fill_20d == 0:
        status = STATUS_FORWARD_NOT_FILLABLE

    validation_fail_count = int(status != STATUS_OK or forbidden)
    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "TOP_N": args.top_n,
        "SIGNAL_LOOKBACK_DAYS": args.signal_lookback_days,
        "CURRENT_RANKED_CANDIDATES_PATH": CURRENT_CANDIDATES,
        "CURRENT_RANKED_CANDIDATES_ROW_COUNT": current_count,
        "CURRENT_RANKED_CANDIDATES_DUPLICATE_TICKER_COUNT": current_dupes,
        "FACTOR_PACK_ROW_COUNT": len(factor_rows),
        "TECHNICAL_TIMING_ROW_COUNT": len(tech_rows),
        "SIGNAL_FREEZE_LEDGER_PATH": SIGNAL_LEDGER,
        "SIGNAL_FREEZE_LEDGER_EXISTS": str(signal_exists).upper(),
        "SIGNAL_FREEZE_LEDGER_ROW_COUNT": signal_row_count,
        "SIGNAL_FREEZE_LATEST_SIGNAL_DATE": signal_latest_signal_date,
        "SIGNAL_FREEZE_LATEST_RUN_ID": signal_latest_run_id,
        "SIGNAL_FREEZE_LATEST_RUN_ROW_COUNT": len(signal_latest_rows),
        "SIGNAL_FREEZE_LATEST_RUN_DISTINCT_TICKER_COUNT": signal_latest_run_distinct,
        "SIGNAL_FREEZE_LATEST_RUN_DUPLICATE_TICKER_COUNT": signal_latest_run_dupes,
        "SIGNAL_FREEZE_LATEST_RUN_TICKER_MATCH_CURRENT": str(signal_latest_run_match).upper(),
        "SIGNAL_FREEZE_LATEST_RUN_MISSING_CURRENT_TICKER_COUNT": signal_latest_run_missing,
        "SIGNAL_FREEZE_LATEST_RUN_EXTRA_TICKER_COUNT": signal_latest_run_extra,
        "SIGNAL_FREEZE_CURRENT_UNIVERSE_MATCH": str(signal_latest_run_match).upper(),
        "SIGNAL_FREEZE_NEEDS_REFRESH_AFTER_R25G": str(signal_needs_refresh).upper(),
        "CURRENT_CANDIDATE_FACTOR_JOIN_COUNT": factor_join_count,
        "CURRENT_CANDIDATE_TECHNICAL_JOIN_COUNT": tech_join_count,
        "CURRENT_CANDIDATE_PRICE_CACHE_JOIN_COUNT": price_join_count,
        "CURRENT_CANDIDATE_ROLLING_LEDGER_JOIN_COUNT": ledger_join_count,
        "FORWARD_RETURN_PENDING_COUNT": forward_pending_count,
        "FORWARD_RETURN_FILLABLE_1D_COUNT": fill_1d,
        "FORWARD_RETURN_FILLABLE_3D_COUNT": fill_3d,
        "FORWARD_RETURN_FILLABLE_5D_COUNT": fill_5d,
        "FORWARD_RETURN_FILLABLE_10D_COUNT": fill_10d,
        "FORWARD_RETURN_FILLABLE_20D_COUNT": fill_20d,
        "FACTOR_EFFECTIVENESS_READY_NOW": str(full_ready and not signal_needs_refresh).upper(),
        "FORWARD_RETURN_FILLER_READY_NOW": str(forward_ready).upper(),
        "RECOMMENDED_NEXT_SIGNAL_FREEZE": "No signal freeze refresh needed. Latest R21 signal freeze matches the current ranked candidate universe." if signal_current_universe_match and not signal_needs_refresh else "Run R21 signal freeze again using updated current ranked candidates, then proceed to R26B forward return filler readiness.",
        "RECOMMENDED_NEXT_FORWARD_RETURN_FILL": "Wait until sufficient future trading days/bars exist, then run R26B forward return filler.",
        "INPUT_READINESS_PATH": OUT_INPUT_READINESS,
        "SIGNAL_LEDGER_AUDIT_PATH": OUT_SIGNAL_AUDIT,
        "RANKED_CANDIDATE_JOIN_AUDIT_PATH": OUT_JOIN_AUDIT,
        "FORWARD_RETURN_FILL_READINESS_PATH": OUT_FORWARD_READINESS,
        "BLOCKERS_AND_NEXT_ACTIONS_PATH": OUT_BLOCKERS,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "ROLLING_LEDGER_MODIFIED": str(mods["ledger"]).upper(),
        "FACTOR_PACK_MODIFIED": str(mods["factor"]).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(mods["technical"]).upper(),
        "TIER_FILES_MODIFIED": str(mods["tier"]).upper(),
        "OFFICIAL_DECISION_MODIFIED": str(mods["decision"]).upper(),
        "CURRENT_RANKED_CANDIDATES_MODIFIED": str(mods["current"]).upper(),
        "SIGNAL_LEDGER_MODIFIED": str(mods["signal"]).upper(),
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden).upper(),
        "NEXT_RECOMMENDED_STEP": "Wait for future bars, then run R26B forward return filler / initial factor effectiveness report. Continue daily R21 signal freeze for new daily signals.",
    }
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    report = "\n".join([
        "# V18.25A R26A Forward-Test Factor Effectiveness Readiness Audit",
        "",
        f"STATUS: {status}",
        f"MODE: {MODE}",
        f"RUN_ID: {run_id}",
        "",
        f"- current_ranked_candidates_row_count: {current_count}",
        f"- signal_freeze_ledger_row_count: {signal_row_count}",
        f"- signal_freeze_latest_run_row_count: {len(signal_latest_rows)}",
        f"- signal_freeze_latest_run_distinct_ticker_count: {signal_latest_run_distinct}",
        f"- signal_freeze_latest_run_ticker_match_current: {str(signal_latest_run_match).upper()}",
        f"- signal_freeze_needs_refresh_after_r25g: {str(signal_needs_refresh).upper()}",
        f"- recommended_next_signal_freeze: {values['RECOMMENDED_NEXT_SIGNAL_FREEZE']}",
        f"- recommended_next_forward_return_fill: {values['RECOMMENDED_NEXT_FORWARD_RETURN_FILL']}",
        f"- current_candidate_join_ready: {current_join_count}/{len(current_join_rows)}",
        f"- forward_returns_fillable: {fill_1d}/{fill_3d}/{fill_5d}/{fill_10d}/{fill_20d}",
        "",
        "R26A is read-only readiness audit only. It does not compute factor effectiveness statistics, backtests, or future returns.",
        "",
    ])
    write_text(root / OUT_REPORT, report)
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(p.relative_to(root)): file_sig(p) for p in root.rglob("*") if p.is_file()}


if __name__ == "__main__":
    raise SystemExit(main())
