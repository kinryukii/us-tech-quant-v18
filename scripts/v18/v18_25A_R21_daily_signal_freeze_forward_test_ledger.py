from __future__ import annotations

import argparse
import csv
import datetime as dt
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R21_DAILY_SIGNAL_FREEZE_LEDGER_READY"
STATUS_NO_SOURCE = "WARN_V18_25A_R21_NO_USABLE_SIGNAL_SOURCE"
STATUS_PARTIAL = "WARN_V18_25A_R21_SIGNAL_FREEZE_PARTIAL_FIELDS"
STATUS_DUPLICATE = "WARN_V18_25A_R21_APPEND_SKIPPED_DUPLICATE_RUN"
STATUS_REPLACED = "WARN_V18_25A_R21_SAME_DAY_FREEZE_REPLACED"
STATUS_FAIL = "FAIL_V18_25A_R21_DAILY_SIGNAL_FREEZE_LEDGER_ERROR"
MODE_LIVE = "LIVE_SAME_DAY_REPLACE_SIGNAL_FREEZE"
MODE_APPEND = "LIVE_APPEND_INTRADAY_SIGNAL_FREEZE"
MODE_DRY = "DRY_RUN_SIGNAL_FREEZE_NO_LEDGER_APPEND"
MODEL_VERSION = "V18.25A-R21"
PIPELINE_VERSION = "V18.25A"
NEXT_STEP = "R22: Rolling Multi-Run Continuation Scheduler"

LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
OUT_ROWS = "outputs/v18/forward_test/V18_25A_R21_CURRENT_SIGNAL_FREEZE_ROWS.csv"
OUT_MANIFEST = "outputs/v18/forward_test/V18_25A_R21_CURRENT_SIGNAL_FREEZE_RUN_MANIFEST.csv"
OUT_SOURCE_AUDIT = "outputs/v18/forward_test/V18_25A_R21_CURRENT_SOURCE_AUDIT.csv"
OUT_APPEND_RESULT = "outputs/v18/forward_test/V18_25A_R21_CURRENT_LEDGER_APPEND_RESULT.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R21_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R21_CURRENT_DAILY_SIGNAL_FREEZE_REPORT.md"
SAME_DAY_BACKUP_ROOT = "archive/v18/signal_freeze_same_day_replace_backups"

TECHNICAL_SOURCE = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
FACTOR_SOURCE = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
CURRENT_CANDIDATE_SOURCE = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"

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

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "SIGNAL_DATE",
    "TOP_N_REQUESTED",
    "SELECTED_SOURCE_FILE",
    "SELECTED_SOURCE_ROW_COUNT",
    "FROZEN_ROW_COUNT",
    "LEDGER_PATH",
    "PRE_LEDGER_ROWS",
    "SAME_DAY_REPLACE_ENABLED",
    "SAME_DAY_EXISTING_ROWS_BEFORE",
    "SAME_DAY_REPLACED_ROWS",
    "SAME_DAY_BACKUP_PATH",
    "APPENDED_ROWS",
    "POST_LEDGER_ROWS",
    "DUPLICATE_SIGNAL_DATE_TICKER_COUNT_AFTER",
    "ALLOW_SAME_DAY_APPEND",
    "DUPLICATE_RUN_TICKER_SKIPPED",
    "TECHNICAL_MERGE_STATUS",
    "MISSING_TICKER_COUNT",
    "MISSING_SCORE_COUNT",
    "MISSING_PRICE_COUNT",
    "SOURCE_QUALITY",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]

SOURCE_AUDIT_FIELDS = [
    "priority",
    "source_role",
    "path",
    "exists",
    "usable",
    "row_count",
    "ticker_column",
    "rank_column",
    "score_columns",
    "mtime",
    "size",
    "selected",
    "notes",
]

FORBIDDEN_RELS = [
    "state/v18/price_cache",
    "state/v18/rolling_coverage",
    "state/v18/tier",
    "outputs/v18/factor_pack",
    "outputs/v18/technical_timing",
    "outputs/v18/rolling_coverage",
    "outputs/v18/tier",
    "outputs/v18/tier_migration",
    "outputs/v18/official_daily",
    "outputs/v18/daily_decision",
    "outputs/v18/market_proxy",
    "outputs/v18/staged_backfill",
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
    if not path.exists() or not path.is_file():
        return [], []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def file_info(path: Path) -> Tuple[str, str, str]:
    if not path.exists() or not path.is_file():
        return "", "", ""
    stat = path.stat()
    mtime = dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    return str(path), mtime, str(stat.st_size)


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def snapshot_forbidden(root: Path) -> Dict[str, Tuple[int, int]]:
    out: Dict[str, Tuple[int, int]] = {}
    for rel in FORBIDDEN_RELS:
        base = root / rel
        if not base.exists():
            continue
        files = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
        for path in files:
            try:
                out[path.resolve().relative_to(root.resolve()).as_posix()] = file_sig(path)
            except ValueError:
                out[str(path.resolve())] = file_sig(path)
    return out


def changed_paths(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    return [key for key in sorted(set(before) | set(after)) if before.get(key) != after.get(key)]


def alias_map(fields: Sequence[str]) -> Dict[str, str]:
    return {field.strip().lower(): field for field in fields}


def first_col(fields: Sequence[str], aliases: Sequence[str]) -> Optional[str]:
    lower = alias_map(fields)
    for alias in aliases:
        if alias.lower() in lower:
            return lower[alias.lower()]
    return None


def first_value(row: Dict[str, str], fields: Sequence[str], aliases: Sequence[str]) -> str:
    col = first_col(fields, aliases)
    return str(row.get(col, "") if col else "").strip()


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def source_candidates(root: Path) -> List[Tuple[int, str, Path]]:
    candidates: List[Tuple[int, str, Path]] = [
        (10, "current_ranked_candidates", root / CURRENT_CANDIDATE_SOURCE),
        (20, "raw105_factor_pack_ranking", root / FACTOR_SOURCE),
    ]
    outputs = root / "outputs/v18"
    if outputs.exists():
        discovered: List[Path] = []
        for pattern in ("*CURRENT*RANK* CANDIDATE*.csv",):
            discovered.extend(outputs.rglob(pattern))
        for path in outputs.rglob("*.csv"):
            name = path.name.upper()
            if path in {root / CURRENT_CANDIDATE_SOURCE, root / FACTOR_SOURCE}:
                continue
            if "CURRENT" in name and (("RANK" in name and "CANDIDATE" in name) or "DAILY_CANDIDATE" in name):
                discovered.append(path)
        for offset, path in enumerate(sorted(set(discovered), key=lambda p: p.as_posix().lower())):
            candidates.append((30 + offset, "discovered_current_ranked_or_daily_candidate", path))
    candidates.append((900, "technical_timing_fallback", root / TECHNICAL_SOURCE))
    return candidates


def assess_source(priority: int, role: str, path: Path) -> Dict[str, object]:
    rows, fields = read_csv(path)
    ticker_col = first_col(fields, ["ticker", "TICKER", "symbol", "SYMBOL"])
    rank_col = first_col(fields, ["rank", "source_rank", "factor_pack_rank", "candidate_rank"])
    score_cols = [
        col for col in [
            first_col(fields, ["composite_candidate_score", "candidate_score", "score"]),
            first_col(fields, ["factor_score", "factor_pack_score"]),
            first_col(fields, ["technical_timing_score", "technical_score"]),
        ] if col
    ]
    exists = path.exists()
    usable = bool(rows and ticker_col)
    _, mtime, size = file_info(path)
    notes = "OK_USABLE_SOURCE" if usable else ("MISSING_TICKER_COLUMN_OR_EMPTY" if exists else "MISSING_FILE")
    return {
        "priority": priority,
        "source_role": role,
        "path": str(path),
        "exists": str(exists).upper(),
        "usable": str(usable).upper(),
        "row_count": len(rows),
        "ticker_column": ticker_col or "",
        "rank_column": rank_col or "",
        "score_columns": ";".join(score_cols),
        "mtime": mtime,
        "size": size,
        "selected": "FALSE",
        "notes": notes,
        "_rows": rows,
        "_fields": fields,
        "_path": path,
    }


def build_lookup(rows: List[Dict[str, str]], fields: Sequence[str]) -> Dict[str, Dict[str, str]]:
    ticker_col = first_col(fields, ["ticker", "TICKER", "symbol", "SYMBOL"])
    if not ticker_col:
        return {}
    return {norm_ticker(row.get(ticker_col, "")): row for row in rows if norm_ticker(row.get(ticker_col, ""))}


def rank_sort_key(row: Dict[str, str], fields: Sequence[str], fallback_index: int) -> Tuple[float, int]:
    rank = first_value(row, fields, ["rank", "source_rank", "factor_pack_rank", "candidate_rank"])
    try:
        return float(rank), fallback_index
    except Exception:
        return float(fallback_index + 1), fallback_index


def build_freeze_rows(
    selected: Dict[str, object],
    top_n: int,
    signal_date: str,
    run_id: str,
    run_timestamp: str,
    factor_lookup: Dict[str, Dict[str, str]],
    factor_fields: Sequence[str],
    technical_lookup: Dict[str, Dict[str, str]],
    technical_fields: Sequence[str],
    technical_path: Path,
) -> Tuple[List[Dict[str, object]], Dict[str, int], str]:
    rows: List[Dict[str, str]] = list(selected["_rows"])  # type: ignore[index]
    fields: Sequence[str] = list(selected["_fields"])  # type: ignore[index]
    source_path: Path = selected["_path"]  # type: ignore[assignment]
    selected_file, selected_mtime, selected_size = file_info(source_path)
    technical_file, technical_mtime, _ = file_info(technical_path)
    sorted_rows = sorted(enumerate(rows), key=lambda pair: rank_sort_key(pair[1], fields, pair[0]))
    selected_rows = [row for _, row in sorted_rows[: max(top_n, 0)]]
    source_quality = "OK_USABLE_SIGNAL_SOURCE"
    technical_merge_status = "TECHNICAL_SOURCE_NOT_AVAILABLE"
    if technical_lookup:
        technical_merge_status = "TECHNICAL_MERGE_AVAILABLE"

    out: List[Dict[str, object]] = []
    missing_ticker = 0
    missing_score = 0
    missing_price = 0
    technical_matches = 0

    for index, row in enumerate(selected_rows, start=1):
        ticker = norm_ticker(first_value(row, fields, ["ticker", "TICKER", "symbol", "SYMBOL"]))
        if not ticker:
            missing_ticker += 1
        factor_row = factor_lookup.get(ticker, {})
        tech_row = technical_lookup.get(ticker, {})
        if tech_row:
            technical_matches += 1

        source_rank = first_value(row, fields, ["rank", "source_rank", "candidate_rank"]) or str(index)
        factor_pack_rank = first_value(row, fields, ["factor_pack_rank", "factor_rank", "rank"])
        if not factor_pack_rank and factor_row:
            factor_pack_rank = first_value(factor_row, factor_fields, ["factor_pack_rank", "factor_rank", "rank"])
        factor_score = first_value(row, fields, ["factor_score", "factor_pack_score"])
        if not factor_score and factor_row:
            factor_score = first_value(factor_row, factor_fields, ["factor_score", "factor_pack_score"])
        technical_score = first_value(row, fields, ["technical_timing_score", "technical_score"])
        if not technical_score and tech_row:
            technical_score = first_value(tech_row, technical_fields, ["technical_timing_score", "technical_score"])
        composite_score = first_value(row, fields, ["composite_candidate_score", "candidate_score", "score"])
        entry_price = first_value(row, fields, ["entry_reference_price", "reference_price", "latest_close", "close", "price"])
        if not entry_price and tech_row:
            entry_price = first_value(tech_row, technical_fields, ["entry_reference_price", "reference_price", "latest_close", "close", "price"])
        if not entry_price and factor_row:
            entry_price = first_value(factor_row, factor_fields, ["entry_reference_price", "reference_price", "latest_close", "close", "price"])
        price_date = first_value(row, fields, ["price_asof_date", "latest_price_date", "price_date", "date"])
        if not price_date and tech_row:
            price_date = first_value(tech_row, technical_fields, ["price_asof_date", "latest_price_date", "price_date", "date"])
        if not price_date and factor_row:
            price_date = first_value(factor_row, factor_fields, ["price_asof_date", "latest_price_date", "price_date", "date"])
        trust_level = first_value(row, fields, ["trust_level", "coverage_trust_level", "data_trust_level"])
        tier = first_value(row, fields, ["tier", "candidate_tier", "trust_tier"])
        freshness = first_value(row, fields, ["data_freshness_status", "freshness_status", "score_source_status"])
        event_risk = first_value(row, fields, ["event_risk_status", "event_risk", "risk_status"])
        buy_permission = first_value(row, fields, ["buy_permission", "buy_permission_status", "final_action", "execution_status"])

        if not (factor_score or technical_score or composite_score):
            missing_score += 1
        if not entry_price:
            missing_price += 1

        out.append({
            "signal_date": signal_date,
            "run_id": run_id,
            "run_timestamp": run_timestamp,
            "ticker": ticker,
            "source_rank": source_rank,
            "factor_pack_rank": factor_pack_rank,
            "factor_score": factor_score,
            "technical_timing_score": technical_score,
            "composite_candidate_score": composite_score,
            "trust_level": trust_level,
            "tier": tier,
            "entry_reference_price": entry_price,
            "price_asof_date": price_date,
            "data_freshness_status": freshness,
            "event_risk_status": event_risk,
            "buy_permission": buy_permission,
            "official_decision_impact": "NONE",
            "auto_trade": "DISABLED",
            "auto_sell": "DISABLED",
            "source_quality": source_quality,
            "selected_source_file": selected_file,
            "selected_source_file_mtime": selected_mtime,
            "selected_source_file_size": selected_size,
            "technical_source_file": technical_file,
            "technical_source_file_mtime": technical_mtime,
            "model_version": MODEL_VERSION,
            "pipeline_version": PIPELINE_VERSION,
            "notes": "R21 signal freeze only; forward return fields intentionally pending.",
            "forward_return_1d": "",
            "forward_return_3d": "",
            "forward_return_5d": "",
            "forward_return_10d": "",
            "forward_return_20d": "",
            "max_drawdown_after_signal": "",
            "max_runup_after_signal": "",
            "forward_fill_status": "PENDING_FORWARD_RETURN_FILL",
        })

    if technical_lookup:
        technical_merge_status = f"TECHNICAL_MERGE_MATCHED_{technical_matches}_OF_{len(out)}"
    counts = {
        "missing_ticker": missing_ticker,
        "missing_score": missing_score,
        "missing_price": missing_price,
    }
    return out, counts, technical_merge_status


def ledger_count(path: Path) -> int:
    rows, _ = read_csv(path)
    return len(rows)


def duplicate_signal_date_ticker_count(rows: Sequence[Dict[str, object]]) -> int:
    counts = Counter((str(row.get("signal_date", "")), norm_ticker(row.get("ticker", ""))) for row in rows)
    return sum(1 for key, count in counts.items() if key[0] and key[1] and count > 1)


def append_ledger(
    path: Path,
    rows: List[Dict[str, object]],
    dry_run: bool,
    allow_same_day_append: bool,
    backup_root: Path,
    run_id: str,
) -> Tuple[int, int, int, int, int, int, str, int]:
    pre_rows, fields = read_csv(path)
    pre_count = len(pre_rows)
    signal_date = str(rows[0].get("signal_date", "")) if rows else ""
    same_day_existing = [row for row in pre_rows if str(row.get("signal_date", "")) == signal_date]
    same_day_backup_path = ""
    same_day_replaced = 0
    working_pre_rows = list(pre_rows)
    if signal_date and same_day_existing and not allow_same_day_append:
        same_day_replaced = len(same_day_existing)
        if not dry_run:
            backup_dir = backup_root / run_id
            ensure_dir(backup_dir)
            backup_file = backup_dir / f"V18_25A_R21_REPLACED_{signal_date}.csv"
            write_csv(backup_file, same_day_existing, LEDGER_FIELDS)
            same_day_backup_path = str(backup_file)
        working_pre_rows = [row for row in pre_rows if str(row.get("signal_date", "")) != signal_date]

    existing = {(str(row.get("run_id", "")), norm_ticker(row.get("ticker", ""))) for row in working_pre_rows}
    append_rows: List[Dict[str, object]] = []
    skipped = 0
    seen_in_batch = set()
    for row in rows:
        key = (str(row.get("run_id", "")), norm_ticker(row.get("ticker", "")))
        if key in existing or key in seen_in_batch:
            skipped += 1
            continue
        seen_in_batch.add(key)
        append_rows.append(row)
    if not dry_run:
        if signal_date and same_day_existing and not allow_same_day_append:
            write_csv(path, working_pre_rows + append_rows, LEDGER_FIELDS)
        else:
            ensure_dir(path.parent)
            new_file = not path.exists()
            with path.open("a", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS, extrasaction="ignore")
                if new_file:
                    writer.writeheader()
                for row in append_rows:
                    writer.writerow({field: row.get(field, "") for field in LEDGER_FIELDS})
    post_count = pre_count if dry_run else ledger_count(path)
    post_rows, _ = read_csv(path)
    duplicate_after = duplicate_signal_date_ticker_count(post_rows if not dry_run else pre_rows)
    return pre_count, len(append_rows) if not dry_run else 0, post_count, skipped, len(same_day_existing), same_day_replaced if not dry_run else 0, same_day_backup_path, duplicate_after


def validation_fail_count(read_values: Dict[str, object], forbidden_modified: bool) -> int:
    fails = 0
    if read_values.get("OFFICIAL_DECISION_IMPACT") != "NONE":
        fails += 1
    if read_values.get("AUTO_TRADE") != "DISABLED":
        fails += 1
    if read_values.get("AUTO_SELL") != "DISABLED":
        fails += 1
    if read_values.get("EXTERNAL_FETCH_EXECUTED") != "FALSE":
        fails += 1
    if read_values.get("BACKTEST_EXECUTED") != "FALSE":
        fails += 1
    if forbidden_modified:
        fails += 1
    return fails


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    lines = [f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS]
    write_text(path, "\n".join(lines) + "\n")


def write_report(path: Path, values: Dict[str, object], changed: Sequence[str]) -> None:
    changed_text = "None" if not changed else ", ".join(changed[:20])
    text = f"""# V18.25A-R21 Daily Signal Freeze / Forward Test Ledger

STATUS: {values.get("STATUS", "")}
MODE: {values.get("MODE", "")}
RUN_ID: {values.get("RUN_ID", "")}
SIGNAL_DATE: {values.get("SIGNAL_DATE", "")}

## Freeze Summary
- TOP_N_REQUESTED: {values.get("TOP_N_REQUESTED", "")}
- SELECTED_SOURCE_FILE: {values.get("SELECTED_SOURCE_FILE", "")}
- SELECTED_SOURCE_ROW_COUNT: {values.get("SELECTED_SOURCE_ROW_COUNT", "")}
- FROZEN_ROW_COUNT: {values.get("FROZEN_ROW_COUNT", "")}
- SOURCE_QUALITY: {values.get("SOURCE_QUALITY", "")}
- TECHNICAL_MERGE_STATUS: {values.get("TECHNICAL_MERGE_STATUS", "")}

## Ledger Summary
- LEDGER_PATH: {values.get("LEDGER_PATH", "")}
- PRE_LEDGER_ROWS: {values.get("PRE_LEDGER_ROWS", "")}
- APPENDED_ROWS: {values.get("APPENDED_ROWS", "")}
- POST_LEDGER_ROWS: {values.get("POST_LEDGER_ROWS", "")}
- DUPLICATE_RUN_TICKER_SKIPPED: {values.get("DUPLICATE_RUN_TICKER_SKIPPED", "")}

## Missing Field Counts
- MISSING_TICKER_COUNT: {values.get("MISSING_TICKER_COUNT", "")}
- MISSING_SCORE_COUNT: {values.get("MISSING_SCORE_COUNT", "")}
- MISSING_PRICE_COUNT: {values.get("MISSING_PRICE_COUNT", "")}

## Safety
- OFFICIAL_DECISION_IMPACT: {values.get("OFFICIAL_DECISION_IMPACT", "")}
- AUTO_TRADE: {values.get("AUTO_TRADE", "")}
- AUTO_SELL: {values.get("AUTO_SELL", "")}
- EXTERNAL_FETCH_EXECUTED: {values.get("EXTERNAL_FETCH_EXECUTED", "")}
- BACKTEST_EXECUTED: {values.get("BACKTEST_EXECUTED", "")}
- FORBIDDEN_MODIFIED: {values.get("FORBIDDEN_MODIFIED", "")}
- FORBIDDEN_CHANGED_PATHS: {changed_text}

## Next
{values.get("NEXT_RECOMMENDED_STEP", "")}
"""
    write_text(path, text)


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.25A-R21 daily signal freeze forward test ledger.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--top-n", type=int, default=100, help="Number of candidates to freeze.")
    parser.add_argument("--dry-run", action="store_true", help="Write current outputs without appending ledger.")
    parser.add_argument("--allow-same-day-append", action="store_true", help="Preserve legacy behavior and append another same-day run.")
    parser.add_argument("--append-intraday-run", action="store_true", help="Alias for --allow-same-day-append.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    now = dt.datetime.now()
    run_id = now.strftime("V18_25A_R21_%Y%m%d_%H%M%S")
    run_timestamp = now.isoformat(timespec="seconds")
    signal_date = now.date().isoformat()
    allow_same_day_append = bool(args.allow_same_day_append or args.append_intraday_run)
    mode = MODE_DRY if args.dry_run else (MODE_APPEND if allow_same_day_append else MODE_LIVE)
    before_forbidden = snapshot_forbidden(root)

    audited = [assess_source(priority, role, path) for priority, role, path in source_candidates(root)]
    selected = next((item for item in audited if item["usable"] == "TRUE"), None)
    for item in audited:
        item["selected"] = "TRUE" if selected is item else "FALSE"

    ledger_path = root / LEDGER
    current_rows: List[Dict[str, object]] = []
    missing_counts = {"missing_ticker": 0, "missing_score": 0, "missing_price": 0}
    technical_merge_status = "TECHNICAL_SOURCE_NOT_AVAILABLE"
    pre_ledger_rows = ledger_count(ledger_path)
    appended_rows = 0
    post_ledger_rows = pre_ledger_rows
    duplicate_skipped = 0
    same_day_existing_rows_before = 0
    same_day_replaced_rows = 0
    same_day_backup_path = ""
    duplicate_signal_date_ticker_after = 0
    source_quality = "NO_USABLE_SIGNAL_SOURCE"

    factor_rows, factor_fields = read_csv(root / FACTOR_SOURCE)
    factor_lookup = build_lookup(factor_rows, factor_fields)
    technical_rows, technical_fields = read_csv(root / TECHNICAL_SOURCE)
    technical_lookup = build_lookup(technical_rows, technical_fields)

    if selected:
        current_rows, missing_counts, technical_merge_status = build_freeze_rows(
            selected=selected,
            top_n=args.top_n,
            signal_date=signal_date,
            run_id=run_id,
            run_timestamp=run_timestamp,
            factor_lookup=factor_lookup,
            factor_fields=factor_fields,
            technical_lookup=technical_lookup,
            technical_fields=technical_fields,
            technical_path=root / TECHNICAL_SOURCE,
        )
        source_quality = "OK_USABLE_SIGNAL_SOURCE"
        if any(missing_counts.values()):
            source_quality = "PARTIAL_FIELDS_PRESENT"
        (
            pre_ledger_rows,
            appended_rows,
            post_ledger_rows,
            duplicate_skipped,
            same_day_existing_rows_before,
            same_day_replaced_rows,
            same_day_backup_path,
            duplicate_signal_date_ticker_after,
        ) = append_ledger(
            ledger_path,
            current_rows,
            args.dry_run,
            allow_same_day_append,
            root / SAME_DAY_BACKUP_ROOT,
            run_id,
        )

    write_csv(root / OUT_ROWS, current_rows, LEDGER_FIELDS)
    source_audit_rows = [{key: value for key, value in item.items() if not key.startswith("_")} for item in audited]
    write_csv(root / OUT_SOURCE_AUDIT, source_audit_rows, SOURCE_AUDIT_FIELDS)

    selected_path = str(selected["_path"]) if selected else ""  # type: ignore[index]
    selected_row_count = int(selected["row_count"]) if selected else 0
    status = STATUS_OK
    if not selected:
        status = STATUS_NO_SOURCE
    elif duplicate_skipped and appended_rows == 0 and not args.dry_run:
        status = STATUS_DUPLICATE
    elif same_day_replaced_rows and same_day_backup_path and not args.dry_run:
        status = STATUS_REPLACED
    elif any(missing_counts.values()):
        status = STATUS_PARTIAL
    if selected and len(current_rows) != args.top_n:
        status = STATUS_FAIL
    if duplicate_signal_date_ticker_after:
        status = STATUS_FAIL

    after_forbidden = snapshot_forbidden(root)
    forbidden_changed = changed_paths(before_forbidden, after_forbidden)
    forbidden_modified = bool(forbidden_changed)

    read_values: Dict[str, object] = {
        "STATUS": status,
        "MODE": mode,
        "RUN_ID": run_id,
        "SIGNAL_DATE": signal_date,
        "TOP_N_REQUESTED": args.top_n,
        "SELECTED_SOURCE_FILE": selected_path,
        "SELECTED_SOURCE_ROW_COUNT": selected_row_count,
        "FROZEN_ROW_COUNT": len(current_rows),
        "LEDGER_PATH": str(ledger_path),
        "PRE_LEDGER_ROWS": pre_ledger_rows,
        "SAME_DAY_REPLACE_ENABLED": str((not allow_same_day_append and not args.dry_run)).upper(),
        "SAME_DAY_EXISTING_ROWS_BEFORE": same_day_existing_rows_before,
        "SAME_DAY_REPLACED_ROWS": same_day_replaced_rows,
        "SAME_DAY_BACKUP_PATH": same_day_backup_path,
        "APPENDED_ROWS": appended_rows,
        "POST_LEDGER_ROWS": post_ledger_rows,
        "DUPLICATE_SIGNAL_DATE_TICKER_COUNT_AFTER": duplicate_signal_date_ticker_after,
        "ALLOW_SAME_DAY_APPEND": str(allow_same_day_append).upper(),
        "DUPLICATE_RUN_TICKER_SKIPPED": duplicate_skipped,
        "TECHNICAL_MERGE_STATUS": technical_merge_status,
        "MISSING_TICKER_COUNT": missing_counts["missing_ticker"],
        "MISSING_SCORE_COUNT": missing_counts["missing_score"],
        "MISSING_PRICE_COUNT": missing_counts["missing_price"],
        "SOURCE_QUALITY": source_quality,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "VALIDATION_FAIL_COUNT": 0,
        "FORBIDDEN_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": NEXT_STEP,
    }
    read_values["VALIDATION_FAIL_COUNT"] = validation_fail_count(read_values, forbidden_modified)

    manifest_rows = [{"key": key, "value": value} for key, value in read_values.items()]
    append_rows = [
        {"metric": "ledger_path", "value": str(ledger_path)},
        {"metric": "dry_run", "value": str(args.dry_run).upper()},
        {"metric": "pre_ledger_rows", "value": pre_ledger_rows},
        {"metric": "current_rows", "value": len(current_rows)},
        {"metric": "appended_rows", "value": appended_rows},
        {"metric": "post_ledger_rows", "value": post_ledger_rows},
        {"metric": "duplicate_run_ticker_skipped", "value": duplicate_skipped},
        {"metric": "status", "value": status},
    ]
    write_csv(root / OUT_MANIFEST, manifest_rows, ["key", "value"])
    write_csv(root / OUT_APPEND_RESULT, append_rows, ["metric", "value"])
    write_read_first(root / OUT_READ_FIRST, read_values)
    write_report(root / OUT_REPORT, read_values, forbidden_changed)

    print(f"STATUS: {status}")
    print(f"RUN_ID: {run_id}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
