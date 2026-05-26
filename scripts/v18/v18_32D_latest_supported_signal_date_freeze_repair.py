from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
import traceback
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_32D_FREEZE_REPAIR_READY"
STATUS_WARN = "WARN_V18_32D_FREEZE_REPAIR_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_32D_FREEZE_REPAIR_FAILED"
MODE_AUDIT = "LATEST_SUPPORTED_SIGNAL_DATE_FREEZE_REPAIR_AUDIT"
MODE_DRY = "LATEST_SUPPORTED_SIGNAL_DATE_FREEZE_REPAIR_DRY_RUN"
MODE_APPLY = "LATEST_SUPPORTED_SIGNAL_DATE_FREEZE_REPAIR_APPLY"

RANKED = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
FACTOR = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECHNICAL = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
CONTEXT_CONSISTENCY = "outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md"
V32C_READ_FIRST = "outputs/v18/ops/V18_32C_READ_FIRST.txt"
V32C_SUMMARY = "outputs/v18/ops/V18_32C_CONTEXT_CONSISTENCY_SUMMARY.csv"
TRADING_DAY_GUARD = "outputs/v18/read_center/V18_CURRENT_TRADING_DAY_SIGNAL_DATE_GUARD.md"
DAILY_READINESS = "outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md"

BACKUP_ROOT = "archive/v18/freeze_repair_backups"
OUT_SUMMARY = "outputs/v18/ops/V18_32D_FREEZE_REPAIR_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_32D_FREEZE_REPAIR_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_32D_READ_FIRST.txt"
OUT_CURRENT = "outputs/v18/read_center/V18_CURRENT_FREEZE_COVERAGE_REPAIR.md"
OUT_ERROR = "outputs/v18/read_center/V18_32D_FREEZE_REPAIR_ERROR.md"

LEDGER_FIELDS = [
    "signal_date",
    "run_id",
    "run_timestamp",
    "ticker",
    "source_rank",
    "factor_pack_rank",
    "factor_score",
    "technical_timing_score",
    "composite_candidate_score",
    "trust_level",
    "tier",
    "entry_reference_price",
    "price_asof_date",
    "data_freshness_status",
    "event_risk_status",
    "buy_permission",
    "official_decision_impact",
    "auto_trade",
    "auto_sell",
    "source_quality",
    "selected_source_file",
    "selected_source_file_mtime",
    "selected_source_file_size",
    "technical_source_file",
    "technical_source_file_mtime",
    "model_version",
    "pipeline_version",
    "notes",
    "forward_return_1d",
    "forward_return_3d",
    "forward_return_5d",
    "forward_return_10d",
    "forward_return_20d",
    "max_drawdown_after_signal",
    "max_runup_after_signal",
    "forward_fill_status",
]

SUMMARY_FIELDS = [
    "run_id",
    "status",
    "mode",
    "generated_at",
    "dry_run",
    "apply_repair",
    "signal_date",
    "signal_date_source",
    "expected_candidate_count",
    "pre_existing_freeze_row_count",
    "pre_existing_freeze_unique_ticker_count",
    "pre_missing_ticker_count",
    "pre_missing_tickers",
    "pre_extra_ticker_count",
    "pre_coverage_status",
    "repair_applied",
    "backup_path",
    "removed_rows",
    "replacement_rows",
    "post_freeze_row_count",
    "post_freeze_unique_ticker_count",
    "post_missing_ticker_count",
    "post_missing_tickers",
    "post_extra_ticker_count",
    "post_coverage_status",
    "duplicate_signal_date_ticker_count",
    "rddt_present",
    "tln_present",
    "auto_trade",
    "auto_sell",
    "official_decision_impact",
    "forbidden_modified",
    "validation_fail_count",
    "notes",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "DRY_RUN",
    "APPLY_REPAIR",
    "SIGNAL_DATE",
    "SIGNAL_DATE_SOURCE",
    "EXPECTED_CANDIDATE_COUNT",
    "PRE_EXISTING_FREEZE_ROW_COUNT",
    "PRE_EXISTING_FREEZE_UNIQUE_TICKER_COUNT",
    "PRE_MISSING_TICKER_COUNT",
    "PRE_MISSING_TICKERS",
    "PRE_EXTRA_TICKER_COUNT",
    "PRE_COVERAGE_STATUS",
    "REPAIR_APPLIED",
    "BACKUP_PATH",
    "REMOVED_ROWS",
    "REPLACEMENT_ROWS",
    "POST_FREEZE_ROW_COUNT",
    "POST_FREEZE_UNIQUE_TICKER_COUNT",
    "POST_MISSING_TICKER_COUNT",
    "POST_MISSING_TICKERS",
    "POST_EXTRA_TICKER_COUNT",
    "POST_COVERAGE_STATUS",
    "DUPLICATE_SIGNAL_DATE_TICKER_COUNT",
    "RDDT_PRESENT",
    "TLN_PRESENT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "FORBIDDEN_MODIFIED",
    "VALIDATION_FAIL_COUNT",
    "NEXT_RECOMMENDED_STEP",
]


def norm(value: object) -> str:
    return "" if value is None else str(value).strip()


def upper(value: object) -> str:
    return norm(value).upper()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def clean(value: object) -> str:
    return norm(value).strip("`").strip()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    return path.read_text(encoding="utf-8", errors="replace")


def read_status(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = clean(value)
    return out


def first_col(fields: Sequence[str], aliases: Sequence[str]) -> Optional[str]:
    lookup = {field.lower(): field for field in fields}
    for alias in aliases:
        if alias.lower() in lookup:
            return lookup[alias.lower()]
    return None


def first_value(row: Dict[str, str], fields: Sequence[str], aliases: Sequence[str]) -> str:
    for alias in aliases:
        col = first_col(fields, [alias])
        if col and norm(row.get(col)):
            return norm(row.get(col))
    return ""


def file_info(path: Path) -> Tuple[str, str, str]:
    if not path.exists() or not path.is_file():
        return "", "", ""
    stat = path.stat()
    return str(path), dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"), str(stat.st_size)


def ticker_set(rows: Sequence[Dict[str, str]]) -> List[str]:
    return sorted({upper(row.get("ticker")) for row in rows if upper(row.get("ticker"))})


def rows_for_date(rows: Sequence[Dict[str, str]], signal_date: str) -> List[Dict[str, str]]:
    return [row for row in rows if norm(row.get("signal_date")) == signal_date]


def coverage(ranked_rows: Sequence[Dict[str, str]], freeze_rows: Sequence[Dict[str, str]]) -> Dict[str, object]:
    expected = ticker_set(ranked_rows)
    frozen = ticker_set(freeze_rows)
    missing = sorted(set(expected) - set(frozen))
    extra = sorted(set(frozen) - set(expected))
    if not freeze_rows:
        status = "MISSING_LEDGER"
    elif missing and extra:
        status = "PARTIAL_MISSING_EXTRA_TICKERS"
    elif missing:
        status = "PARTIAL_MISSING"
    elif extra:
        status = "EXTRA_TICKERS"
    elif len(frozen) == len(expected):
        status = "FULL_MATCH"
    else:
        status = "UNKNOWN"
    return {
        "expected_count": len(expected),
        "row_count": len(freeze_rows),
        "unique_count": len(frozen),
        "missing": missing,
        "extra": extra,
        "status": status,
    }


def duplicate_signal_ticker_count(rows: Sequence[Dict[str, str]]) -> int:
    counts = Counter((norm(row.get("signal_date")), upper(row.get("ticker"))) for row in rows)
    return sum(1 for (signal_date, ticker), count in counts.items() if signal_date and ticker and count > 1)


def determine_signal_date(root: Path, override: str) -> Tuple[str, str]:
    if norm(override):
        return norm(override), "SIGNAL_DATE_OVERRIDE"
    v32c = read_status(root / V32C_READ_FIRST)
    for key in ("LATEST_SUPPORTED_SIGNAL_DATE", "LATEST_RELEVANT_SIGNAL_DATE", "SIGNAL_DATE"):
        if norm(v32c.get(key)):
            return norm(v32c[key]), f"{V32C_READ_FIRST}:{key}"
    rows, _ = read_csv(root / V32C_SUMMARY)
    if rows:
        for key in ("latest_supported_signal_date", "latest_relevant_signal_date"):
            if norm(rows[-1].get(key)):
                return norm(rows[-1][key]), f"{V32C_SUMMARY}:{key}"
    guard_text = read_text(root / TRADING_DAY_GUARD)
    for marker in ("RECOMMENDED_SIGNAL_DATE:", "Recommended signal date:", "Latest observed local price date:"):
        for line in guard_text.splitlines():
            if marker.lower() in line.lower() and ":" in line:
                return clean(line.split(":", 1)[1]), f"{TRADING_DAY_GUARD}:{marker.rstrip(':')}"
    daily_text = read_text(root / DAILY_READINESS)
    for line in daily_text.splitlines():
        if "latest supported signal date" in line.lower() and "`" in line:
            parts = line.split("`")
            if len(parts) >= 2:
                return clean(parts[1]), f"{DAILY_READINESS}:latest supported signal date"
    ledger_rows, _ = read_csv(root / FREEZE_LEDGER)
    dates = sorted({norm(row.get("signal_date")) for row in ledger_rows if norm(row.get("signal_date"))})
    if dates:
        return dates[-1], f"{FREEZE_LEDGER}:latest signal_date fallback"
    return "", "UNKNOWN"


def build_lookup(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> Dict[str, Dict[str, str]]:
    ticker_col = first_col(fields, ["ticker", "TICKER", "symbol", "SYMBOL"])
    if not ticker_col:
        return {}
    return {upper(row.get(ticker_col)): row for row in rows if upper(row.get(ticker_col))}


def rank_key(row: Dict[str, str], fields: Sequence[str], index: int) -> Tuple[float, int]:
    value = first_value(row, fields, ["rank", "source_rank", "candidate_rank"])
    try:
        return float(value), index
    except Exception:
        return float(index + 1), index


def build_replacement_rows(root: Path, ranked_rows: Sequence[Dict[str, str]], ranked_fields: Sequence[str], signal_date: str, run_id: str, run_ts: str) -> List[Dict[str, object]]:
    factor_rows, factor_fields = read_csv(root / FACTOR)
    technical_rows, technical_fields = read_csv(root / TECHNICAL)
    factor_lookup = build_lookup(factor_rows, factor_fields)
    technical_lookup = build_lookup(technical_rows, technical_fields)
    selected_file, selected_mtime, selected_size = file_info(root / RANKED)
    technical_file, technical_mtime, _ = file_info(root / TECHNICAL)

    out: List[Dict[str, object]] = []
    sorted_rows = [row for _, row in sorted(enumerate(ranked_rows), key=lambda pair: rank_key(pair[1], ranked_fields, pair[0]))]
    for index, row in enumerate(sorted_rows, start=1):
        ticker = upper(first_value(row, ranked_fields, ["ticker", "TICKER", "symbol", "SYMBOL"]))
        factor_row = factor_lookup.get(ticker, {})
        tech_row = technical_lookup.get(ticker, {})
        factor_pack_rank = first_value(row, ranked_fields, ["factor_pack_rank", "factor_rank", "rank"])
        if not factor_pack_rank:
            factor_pack_rank = first_value(factor_row, factor_fields, ["factor_pack_rank", "factor_rank", "rank"])
        factor_score = first_value(row, ranked_fields, ["factor_score", "factor_pack_score"])
        if not factor_score:
            factor_score = first_value(factor_row, factor_fields, ["factor_score", "factor_pack_score"])
        technical_score = first_value(row, ranked_fields, ["technical_timing_score", "technical_score"])
        if not technical_score:
            technical_score = first_value(tech_row, technical_fields, ["technical_timing_score", "technical_score"])
        entry_price = first_value(row, ranked_fields, ["entry_reference_price", "reference_price", "latest_close", "close", "price"])
        if not entry_price:
            entry_price = first_value(tech_row, technical_fields, ["entry_reference_price", "reference_price", "latest_close", "close", "price"])
        if not entry_price:
            entry_price = first_value(factor_row, factor_fields, ["entry_reference_price", "reference_price", "latest_close", "close", "price"])
        price_date = first_value(row, ranked_fields, ["price_asof_date", "latest_price_date", "price_date", "date"])
        if not price_date:
            price_date = first_value(tech_row, technical_fields, ["price_asof_date", "latest_price_date", "price_date", "date"])
        if not price_date:
            price_date = first_value(factor_row, factor_fields, ["price_asof_date", "latest_price_date", "price_date", "date"])
        out.append({
            "signal_date": signal_date,
            "run_id": run_id,
            "run_timestamp": run_ts,
            "ticker": ticker,
            "source_rank": first_value(row, ranked_fields, ["rank", "source_rank", "candidate_rank"]) or str(index),
            "factor_pack_rank": factor_pack_rank,
            "factor_score": factor_score,
            "technical_timing_score": technical_score,
            "composite_candidate_score": first_value(row, ranked_fields, ["composite_candidate_score", "candidate_score", "score"]),
            "trust_level": first_value(row, ranked_fields, ["trust_level", "coverage_trust_level", "data_trust_level"]),
            "tier": first_value(row, ranked_fields, ["tier", "candidate_tier", "trust_tier"]),
            "entry_reference_price": entry_price,
            "price_asof_date": price_date,
            "data_freshness_status": first_value(row, ranked_fields, ["data_freshness_status", "freshness_status", "score_source_status"]),
            "event_risk_status": first_value(row, ranked_fields, ["event_risk_status", "event_risk", "risk_status"]),
            "buy_permission": first_value(row, ranked_fields, ["buy_permission", "buy_permission_status", "final_action", "execution_status"]),
            "official_decision_impact": "NONE",
            "auto_trade": "DISABLED",
            "auto_sell": "DISABLED",
            "source_quality": "OK_USABLE_SIGNAL_SOURCE",
            "selected_source_file": selected_file,
            "selected_source_file_mtime": selected_mtime,
            "selected_source_file_size": selected_size,
            "technical_source_file": technical_file,
            "technical_source_file_mtime": technical_mtime,
            "model_version": "V18.32D-FREEZE-REPAIR",
            "pipeline_version": "V18.32D",
            "notes": "V18.32D latest supported signal-date freeze repair; forward return fields intentionally pending.",
            "forward_return_1d": "",
            "forward_return_3d": "",
            "forward_return_5d": "",
            "forward_return_10d": "",
            "forward_return_20d": "",
            "max_drawdown_after_signal": "",
            "max_runup_after_signal": "",
            "forward_fill_status": "PENDING_FORWARD_RETURN_FILL",
        })
    return out


def make_report(values: Dict[str, object]) -> str:
    return f"""# V18.32D Latest Supported Signal-Date Freeze Repair

## 1. Final Status
STATUS: {values['STATUS']}

## 2. Coverage
- SIGNAL_DATE: `{values['SIGNAL_DATE']}`
- SIGNAL_DATE_SOURCE: `{values['SIGNAL_DATE_SOURCE']}`
- EXPECTED_CANDIDATE_COUNT: `{values['EXPECTED_CANDIDATE_COUNT']}`
- PRE_COVERAGE_STATUS: `{values['PRE_COVERAGE_STATUS']}`
- PRE_EXISTING_FREEZE_ROW_COUNT: `{values['PRE_EXISTING_FREEZE_ROW_COUNT']}`
- PRE_MISSING_TICKERS: `{values['PRE_MISSING_TICKERS']}`
- POST_COVERAGE_STATUS: `{values['POST_COVERAGE_STATUS']}`
- POST_FREEZE_ROW_COUNT: `{values['POST_FREEZE_ROW_COUNT']}`
- POST_MISSING_TICKERS: `{values['POST_MISSING_TICKERS']}`

## 3. Repair
- REPAIR_APPLIED: `{values['REPAIR_APPLIED']}`
- BACKUP_PATH: `{values['BACKUP_PATH']}`
- REMOVED_ROWS: `{values['REMOVED_ROWS']}`
- REPLACEMENT_ROWS: `{values['REPLACEMENT_ROWS']}`
- DUPLICATE_SIGNAL_DATE_TICKER_COUNT: `{values['DUPLICATE_SIGNAL_DATE_TICKER_COUNT']}`
- RDDT_PRESENT: `{values['RDDT_PRESENT']}`
- TLN_PRESENT: `{values['TLN_PRESENT']}`

## 4. Safety
- AUTO_TRADE: `DISABLED`
- AUTO_SELL: `DISABLED`
- OFFICIAL_DECISION_IMPACT: `NONE`
- FORBIDDEN_MODIFIED: `FALSE`
- No external fetch, backtest, broker/API, trading, or order code executed.
"""


def make_current(values: Dict[str, object]) -> str:
    return f"""# V18 Current Freeze Coverage Repair

STATUS: {values['STATUS']}

- Signal date: `{values['SIGNAL_DATE']}`
- Coverage before: `{values['PRE_COVERAGE_STATUS']} {values['PRE_EXISTING_FREEZE_UNIQUE_TICKER_COUNT']}/{values['EXPECTED_CANDIDATE_COUNT']}`
- Coverage after: `{values['POST_COVERAGE_STATUS']} {values['POST_FREEZE_UNIQUE_TICKER_COUNT']}/{values['EXPECTED_CANDIDATE_COUNT']}`
- Missing before: `{values['PRE_MISSING_TICKERS']}`
- Missing after: `{values['POST_MISSING_TICKERS']}`
- Backup path: `{values['BACKUP_PATH']}`
- RDDT present: `{values['RDDT_PRESENT']}`
- TLN present: `{values['TLN_PRESENT']}`
"""


def validation_fail_count(values: Dict[str, object]) -> int:
    fail = 0
    if values["FORBIDDEN_MODIFIED"] != "FALSE":
        fail += 1
    if values["AUTO_TRADE"] != "DISABLED" or values["AUTO_SELL"] != "DISABLED":
        fail += 1
    if values["OFFICIAL_DECISION_IMPACT"] != "NONE":
        fail += 1
    if values["REPAIR_APPLIED"] == "TRUE":
        if values["POST_COVERAGE_STATUS"] != "FULL_MATCH":
            fail += 1
        if values["DUPLICATE_SIGNAL_DATE_TICKER_COUNT"] != 0:
            fail += 1
        if values["RDDT_PRESENT"] != "TRUE" or values["TLN_PRESENT"] != "TRUE":
            fail += 1
    return fail


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    now = dt.datetime.now().replace(microsecond=0)
    run_id = f"V18_32D_FREEZE_REPAIR_{now.strftime('%Y%m%d_%H%M%S')}"
    run_ts = now.isoformat()
    signal_date, signal_source = determine_signal_date(root, args.signal_date_override)
    mode = MODE_DRY if args.dry_run else (MODE_APPLY if args.apply_repair else MODE_AUDIT)

    ranked_rows, ranked_fields = read_csv(root / RANKED)
    ledger_rows, ledger_fields = read_csv(root / FREEZE_LEDGER)
    if ledger_fields and ledger_fields != LEDGER_FIELDS:
        raise RuntimeError(f"Signal freeze ledger schema mismatch. Expected R21-compatible fields, got: {ledger_fields}")
    if not signal_date:
        raise RuntimeError("Unable to determine latest supported signal date.")

    pre_rows = rows_for_date(ledger_rows, signal_date)
    pre = coverage(ranked_rows, pre_rows)
    backup_path = ""
    removed_rows = 0
    replacement_rows = 0
    repair_applied = False
    notes = "AUDIT_ONLY"

    post_rows = list(pre_rows)
    post_ledger_rows = list(ledger_rows)
    if args.apply_repair and not args.dry_run:
        if pre["status"] == "FULL_MATCH":
            notes = "COVERAGE_ALREADY_FULL_NO_REPAIR"
        elif pre["status"] in {"PARTIAL_MISSING", "PARTIAL_MISSING_EXTRA_TICKERS", "EXTRA_TICKERS", "MISSING_LEDGER"}:
            backup_dir = root / BACKUP_ROOT / run_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_file = backup_dir / "V18_DAILY_SIGNAL_FREEZE_LEDGER_PRE_REPAIR.csv"
            shutil.copy2(root / FREEZE_LEDGER, backup_file)
            backup_path = str(backup_file)
            replacement = build_replacement_rows(root, ranked_rows, ranked_fields, signal_date, run_id, run_ts)
            kept = [row for row in ledger_rows if norm(row.get("signal_date")) != signal_date]
            removed_rows = len(ledger_rows) - len(kept)
            replacement_rows = len(replacement)
            write_csv(root / FREEZE_LEDGER, kept + replacement, LEDGER_FIELDS)
            repair_applied = True
            notes = "REPLACED_SIGNAL_DATE_FREEZE_WITH_CURRENT_252_RANKED_CANDIDATES"
            post_ledger_rows, _ = read_csv(root / FREEZE_LEDGER)
            post_rows = rows_for_date(post_ledger_rows, signal_date)
        else:
            raise RuntimeError(f"Unsafe coverage status for repair: {pre['status']}")

    post = coverage(ranked_rows, post_rows)
    post_tickers = set(ticker_set(post_rows))
    duplicate_count = duplicate_signal_ticker_count(post_ledger_rows)
    status = STATUS_OK if post["status"] == "FULL_MATCH" else STATUS_WARN
    if args.apply_repair and not args.dry_run and post["status"] != "FULL_MATCH":
        status = STATUS_FAIL

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": mode,
        "RUN_ID": run_id,
        "DRY_RUN": bool_text(args.dry_run),
        "APPLY_REPAIR": bool_text(args.apply_repair),
        "SIGNAL_DATE": signal_date,
        "SIGNAL_DATE_SOURCE": signal_source,
        "EXPECTED_CANDIDATE_COUNT": pre["expected_count"],
        "PRE_EXISTING_FREEZE_ROW_COUNT": pre["row_count"],
        "PRE_EXISTING_FREEZE_UNIQUE_TICKER_COUNT": pre["unique_count"],
        "PRE_MISSING_TICKER_COUNT": len(pre["missing"]),
        "PRE_MISSING_TICKERS": ";".join(pre["missing"]) if pre["missing"] else "NONE",
        "PRE_EXTRA_TICKER_COUNT": len(pre["extra"]),
        "PRE_COVERAGE_STATUS": pre["status"],
        "REPAIR_APPLIED": bool_text(repair_applied),
        "BACKUP_PATH": backup_path,
        "REMOVED_ROWS": removed_rows,
        "REPLACEMENT_ROWS": replacement_rows,
        "POST_FREEZE_ROW_COUNT": post["row_count"],
        "POST_FREEZE_UNIQUE_TICKER_COUNT": post["unique_count"],
        "POST_MISSING_TICKER_COUNT": len(post["missing"]),
        "POST_MISSING_TICKERS": ";".join(post["missing"]) if post["missing"] else "NONE",
        "POST_EXTRA_TICKER_COUNT": len(post["extra"]),
        "POST_COVERAGE_STATUS": post["status"],
        "DUPLICATE_SIGNAL_DATE_TICKER_COUNT": duplicate_count,
        "RDDT_PRESENT": bool_text("RDDT" in post_tickers),
        "TLN_PRESENT": bool_text("TLN" in post_tickers),
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "FORBIDDEN_MODIFIED": "FALSE",
        "NEXT_RECOMMENDED_STEP": "Run V18.32C with -Patch32B after repair.",
        "notes": notes,
    }
    values["VALIDATION_FAIL_COUNT"] = validation_fail_count(values)
    if values["VALIDATION_FAIL_COUNT"]:
        values["STATUS"] = STATUS_FAIL

    write_csv(root / OUT_SUMMARY, [{
        "run_id": values["RUN_ID"],
        "status": values["STATUS"],
        "mode": values["MODE"],
        "generated_at": run_ts,
        "dry_run": values["DRY_RUN"],
        "apply_repair": values["APPLY_REPAIR"],
        "signal_date": values["SIGNAL_DATE"],
        "signal_date_source": values["SIGNAL_DATE_SOURCE"],
        "expected_candidate_count": values["EXPECTED_CANDIDATE_COUNT"],
        "pre_existing_freeze_row_count": values["PRE_EXISTING_FREEZE_ROW_COUNT"],
        "pre_existing_freeze_unique_ticker_count": values["PRE_EXISTING_FREEZE_UNIQUE_TICKER_COUNT"],
        "pre_missing_ticker_count": values["PRE_MISSING_TICKER_COUNT"],
        "pre_missing_tickers": values["PRE_MISSING_TICKERS"],
        "pre_extra_ticker_count": values["PRE_EXTRA_TICKER_COUNT"],
        "pre_coverage_status": values["PRE_COVERAGE_STATUS"],
        "repair_applied": values["REPAIR_APPLIED"],
        "backup_path": values["BACKUP_PATH"],
        "removed_rows": values["REMOVED_ROWS"],
        "replacement_rows": values["REPLACEMENT_ROWS"],
        "post_freeze_row_count": values["POST_FREEZE_ROW_COUNT"],
        "post_freeze_unique_ticker_count": values["POST_FREEZE_UNIQUE_TICKER_COUNT"],
        "post_missing_ticker_count": values["POST_MISSING_TICKER_COUNT"],
        "post_missing_tickers": values["POST_MISSING_TICKERS"],
        "post_extra_ticker_count": values["POST_EXTRA_TICKER_COUNT"],
        "post_coverage_status": values["POST_COVERAGE_STATUS"],
        "duplicate_signal_date_ticker_count": values["DUPLICATE_SIGNAL_DATE_TICKER_COUNT"],
        "rddt_present": values["RDDT_PRESENT"],
        "tln_present": values["TLN_PRESENT"],
        "auto_trade": values["AUTO_TRADE"],
        "auto_sell": values["AUTO_SELL"],
        "official_decision_impact": values["OFFICIAL_DECISION_IMPACT"],
        "forbidden_modified": values["FORBIDDEN_MODIFIED"],
        "validation_fail_count": values["VALIDATION_FAIL_COUNT"],
        "notes": values["notes"],
    }], SUMMARY_FIELDS)
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    write_text(root / OUT_REPORT, make_report(values))
    write_text(root / OUT_CURRENT, make_current(values))

    print(f"STATUS: {values['STATUS']}")
    print(f"RUN_ID: {run_id}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    print(f"PRE_COVERAGE_STATUS: {values['PRE_COVERAGE_STATUS']}")
    print(f"POST_COVERAGE_STATUS: {values['POST_COVERAGE_STATUS']}")
    print(f"BACKUP_PATH: {values['BACKUP_PATH']}")
    return 1 if str(values["STATUS"]).startswith("FAIL") else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repair latest supported signal-date freeze coverage.")
    parser.add_argument("--root", default="D:\\us-tech-quant")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply-repair", action="store_true")
    parser.add_argument("--signal-date-override", default="")
    return parser.parse_args()


def main() -> int:
    try:
        return run(parse_args())
    except Exception as exc:
        root = Path("D:\\us-tech-quant")
        try:
            args = parse_args()
            root = Path(args.root).resolve()
        except Exception:
            pass
        write_text(
            root / OUT_ERROR,
            "# V18.32D Freeze Repair Error\n\n"
            f"STATUS: {STATUS_FAIL}\n\n"
            "```text\n"
            f"{exc}\n\n{traceback.format_exc()}"
            "```\n",
        )
        print(f"STATUS: {STATUS_FAIL}")
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
