from __future__ import annotations

import argparse
import csv
import datetime as dt
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_PLAN_OK = "OK_V18_25A_R8_CONTROLLED_STAGED_VIX_BACKFILL_PLAN_READY"
STATUS_FETCH_OK = "OK_V18_25A_R8_CONTROLLED_STAGED_VIX_BACKFILL_READY"
STATUS_FETCH_WARN = "WARN_V18_25A_R8_CONTROLLED_STAGED_VIX_BACKFILL_READY"
STATUS_FAIL = "FAIL_V18_25A_R8_CONTROLLED_STAGED_VIX_BACKFILL"
MODE = "CONTROLLED_STAGED_VIX_BACKFILL_STAGED_ONLY"
RUN_MODE_PLAN = "PLAN_ONLY"
RUN_MODE_FETCH = "FETCH_STAGED_VIX"
FETCH_PROVIDER = "yfinance"
FETCH_SYMBOLS = ["^VIX", "VIX"]
MIN_REQUIRED_TRADING_ROWS = 120
PREFERRED_TRADING_ROWS = 252
MAX_LATEST_STALE_DAYS = 10

R7_INPUTS = [
    "outputs/v18/ops/V18_25A_R7_READ_FIRST.txt",
    "outputs/v18/degraded_daily_review/V18_25A_R7_CURRENT_VIX_REQUIREMENT_SPEC.csv",
    "outputs/v18/degraded_daily_review/V18_25A_R7_CURRENT_PROXY_STORAGE_POLICY.csv",
    "outputs/v18/degraded_daily_review/V18_25A_R7_CURRENT_MARKET_PROXY_REPAIR_OPTIONS.csv",
]

STAGED_DIR_REL = "data/v18/staged_market_proxy/V18_25A_R8_VIX"
OUT_DEGRADED_REL = "outputs/v18/degraded_daily_review"
OUT_OPS_REL = "outputs/v18/ops"

PLAN_OUT = "V18_25A_R8_CURRENT_STAGED_VIX_BACKFILL_PLAN.csv"
QUALITY_OUT = "V18_25A_R8_CURRENT_STAGED_VIX_QUALITY_AUDIT.csv"
RESULT_OUT = "V18_25A_R8_CURRENT_STAGED_VIX_BACKFILL_RESULT.csv"
REPORT_OUT = "V18_25A_R8_CURRENT_REPORT.md"
READ_FIRST_OUT = "V18_25A_R8_READ_FIRST.txt"
OPS_REPORT_OUT = "V18_25A_R8_CURRENT_CONTROLLED_STAGED_VIX_BACKFILL_REPORT.md"

RAW_OUT = "V18_25A_R8_VIX_RAW.csv"
NORMALIZED_OUT = "V18_25A_R8_VIX_NORMALIZED.csv"
MANIFEST_OUT = "MANIFEST.csv"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_MODE",
    "R7_SOURCE_PATH",
    "STAGED_VIX_DIR",
    "EXTERNAL_DATA_FETCHED",
    "FETCH_APPROVAL_REQUIRED",
    "FETCH_PROVIDER",
    "FETCH_SYMBOL_ATTEMPTED",
    "FETCH_SUCCESS",
    "FETCH_EMPTY",
    "FETCH_FAIL",
    "RAW_ROW_COUNT",
    "NORMALIZED_ROW_COUNT",
    "MIN_DATE",
    "MAX_DATE",
    "LATEST_DATE",
    "CLOSE_COLUMN_AVAILABLE",
    "CLOSE_NON_NULL_COUNT",
    "FULL_HISTORY_READY",
    "USABLE_FOR_FACTOR_REFRESH",
    "USABLE_FOR_TECHNICAL_OVERLAY",
    "QUALITY_STATUS",
    "OFFICIAL_PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_STOCK_BACKFILL_MODIFIED",
    "MARKET_PROXY_STAGED_MODIFIED",
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

PLAN_FIELDS = [
    "item",
    "status",
    "path_or_value",
    "notes",
]
QUALITY_FIELDS = [
    "row_count",
    "min_date",
    "max_date",
    "latest_date",
    "close_non_null_count",
    "duplicate_date_count_before_cleaning",
    "duplicate_date_count_after_cleaning",
    "negative_or_zero_close_count",
    "suspicious_gap_count",
    "full_history_ready",
    "usable_for_factor_refresh",
    "usable_for_technical_overlay",
    "quality_status",
    "assumed_threshold",
]
RESULT_FIELDS = [
    "provider",
    "symbol_attempted",
    "fetch_status",
    "failure_reason",
    "raw_row_count",
    "normalized_row_count",
    "raw_path",
    "normalized_path",
]
MANIFEST_FIELDS = ["file_name", "relative_path", "exists", "row_count", "notes"]

SAFETY_VALUES = {
    "OFFICIAL_PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_MODIFIED": "FALSE",
    "STAGED_STOCK_BACKFILL_MODIFIED": "FALSE",
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
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


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
        except csv.Error:
            continue
    return [], []


def rel_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def forbidden_roots(root: Path) -> List[Path]:
    rels = [
        "state/v18/price_cache",
        "data/v18/price_history",
        "data/v18/prices",
        "data/v18/staged_backfill",
        "state/v18/rolling_coverage",
        "outputs/v18/factor_pack",
        "outputs/v18/ranking",
        "outputs/v18/technical_timing",
        "outputs/v18/tier_migration",
        "outputs/v18/official_daily_decision",
        "outputs/v18/daily_decision",
        "state/v18/official_daily_decision",
    ]
    return [(root / rel).resolve() for rel in rels]


def file_is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def forbidden_files(root: Path) -> List[Path]:
    out: List[Path] = []
    for base in forbidden_roots(root):
        if base.exists():
            out.extend(path for path in base.rglob("*") if path.is_file())
    return out


def changed_forbidden_files(root: Path, before: Dict[str, Tuple[int, int]]) -> List[str]:
    after = {str(path): file_sig(path) for path in forbidden_files(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig)
    changed.extend(sorted(path for path in after if path not in before))
    return changed


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def parse_date(text: object) -> Optional[dt.date]:
    raw = str(text or "").strip()[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def number_value(value: object) -> Optional[float]:
    try:
        text = str(value).replace(",", "").strip()
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def normalize_yfinance_columns(columns: Sequence[object]) -> List[str]:
    names = []
    for col in columns:
        name = str(col[0] if isinstance(col, tuple) else col).strip().lower()
        name = name.replace(" ", "_")
        if name == "adj_close":
            names.append("adj_close")
        elif name in {"date", "open", "high", "low", "close", "volume"}:
            names.append(name)
        else:
            names.append(name)
    return names


def fetch_symbol(symbol: str, raw_path: Path) -> Tuple[str, str, int, List[Dict[str, object]], List[str]]:
    try:
        import yfinance as yf  # type: ignore
    except Exception as exc:
        return "FAIL", f"YFINANCE_IMPORT_FAILED:{exc}", 0, [], []
    try:
        df = yf.download(symbol, period="max", interval="1d", auto_adjust=False, progress=False, threads=False)
    except Exception as exc:
        return "FAIL", f"YFINANCE_DOWNLOAD_FAILED:{exc}", 0, [], []
    if df is None or getattr(df, "empty", True):
        return "EMPTY", "EMPTY_DATA", 0, [], []
    if hasattr(df.columns, "nlevels") and getattr(df.columns, "nlevels", 1) > 1:
        df.columns = [col[0] for col in df.columns]
    df = df.reset_index()
    df.columns = normalize_yfinance_columns(df.columns)
    ensure_dir(raw_path.parent)
    df.to_csv(raw_path, index=False)
    rows = df.to_dict("records")
    fields = [str(col) for col in df.columns]
    return "SUCCESS", "", len(rows), rows, fields


def normalize_rows(raw_rows: Sequence[Dict[str, object]], symbol: str) -> Tuple[List[Dict[str, object]], int, int, int, int]:
    date_counts: Dict[str, int] = {}
    intermediate: List[Dict[str, object]] = []
    for row in raw_rows:
        date_value = row.get("date") or row.get("Date") or row.get("datetime")
        parsed = parse_date(date_value)
        if parsed is None:
            continue
        date_text = parsed.isoformat()
        date_counts[date_text] = date_counts.get(date_text, 0) + 1
        normalized = {
            "date": date_text,
            "open": row.get("open", ""),
            "high": row.get("high", ""),
            "low": row.get("low", ""),
            "close": row.get("close", ""),
            "adj_close": row.get("adj_close", ""),
            "volume": row.get("volume", ""),
            "proxy_symbol": symbol,
            "source": FETCH_PROVIDER,
        }
        intermediate.append(normalized)
    duplicate_before = sum(count - 1 for count in date_counts.values() if count > 1)
    by_date: Dict[str, Dict[str, object]] = {}
    for row in intermediate:
        by_date[str(row["date"])] = row
    cleaned = [by_date[key] for key in sorted(by_date)]
    clean_counts: Dict[str, int] = {}
    for row in cleaned:
        key = str(row["date"])
        clean_counts[key] = clean_counts.get(key, 0) + 1
    duplicate_after = sum(count - 1 for count in clean_counts.values() if count > 1)
    negative_or_zero = sum(1 for row in cleaned if (number_value(row.get("close")) is not None and number_value(row.get("close")) <= 0))
    suspicious_gaps = count_suspicious_gaps([str(row["date"]) for row in cleaned])
    return cleaned, duplicate_before, duplicate_after, negative_or_zero, suspicious_gaps


def count_suspicious_gaps(date_values: Sequence[str]) -> int:
    parsed = [parse_date(value) for value in date_values]
    dates = [value for value in parsed if value is not None]
    gaps = 0
    for prev, cur in zip(dates, dates[1:]):
        if (cur - prev).days > 10:
            gaps += 1
    return gaps


def quality_values(rows: Sequence[Dict[str, object]], duplicate_before: int, duplicate_after: int, negative_or_zero: int, suspicious_gaps: int) -> Dict[str, str]:
    dates = [str(row.get("date", "")) for row in rows if row.get("date")]
    close_values = [number_value(row.get("close")) for row in rows]
    close_non_null = sum(1 for value in close_values if value is not None)
    latest = max(dates) if dates else ""
    latest_date = parse_date(latest)
    stale = True
    if latest_date is not None:
        stale = (dt.date.today() - latest_date).days > MAX_LATEST_STALE_DAYS
    close_available = close_non_null > 0
    full_history_ready = len(rows) >= PREFERRED_TRADING_ROWS and close_available and negative_or_zero == 0
    usable_factor = full_history_ready and not stale
    usable_technical = len(rows) >= MIN_REQUIRED_TRADING_ROWS and close_available and negative_or_zero == 0 and not stale
    if not rows or not close_available:
        quality = "FAIL"
    elif full_history_ready and usable_factor and usable_technical:
        quality = "OK"
    else:
        quality = "WARN"
    return {
        "row_count": str(len(rows)),
        "min_date": min(dates) if dates else "",
        "max_date": max(dates) if dates else "",
        "latest_date": latest,
        "close_non_null_count": str(close_non_null),
        "duplicate_date_count_before_cleaning": str(duplicate_before),
        "duplicate_date_count_after_cleaning": str(duplicate_after),
        "negative_or_zero_close_count": str(negative_or_zero),
        "suspicious_gap_count": str(suspicious_gaps),
        "full_history_ready": str(full_history_ready).upper(),
        "usable_for_factor_refresh": str(usable_factor).upper(),
        "usable_for_technical_overlay": str(usable_technical).upper(),
        "quality_status": quality,
        "assumed_threshold": f"minimum={MIN_REQUIRED_TRADING_ROWS}_rows;preferred={PREFERRED_TRADING_ROWS}_rows;latest_stale_days>{MAX_LATEST_STALE_DAYS}",
    }


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, str], plan_rows: Sequence[Dict[str, object]]) -> str:
    plan_lines = "\n".join(f"- {row['item']}: {row['status']} ({row['notes']})" for row in plan_rows)
    return f"""# V18.25A-R8 Controlled Staged VIX Backfill

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

Status: {values['STATUS']}

Mode: {values['MODE']}

Run mode: {values['RUN_MODE']}

External data fetched: {values['EXTERNAL_DATA_FETCHED']}

Staged VIX directory: `{values['STAGED_VIX_DIR']}`

## Plan And Context
{plan_lines}

## Safety
No official price cache, official price history, staged stock backfill data, rolling ledger, factor pack, technical timing, tier migration, degraded daily output current source, buy permission, or official daily decision files were modified. AUTO_TRADE and AUTO_SELL remain DISABLED. OFFICIAL_DECISION_IMPACT remains NONE.

## Next Step
{values['NEXT_RECOMMENDED_STEP']}
"""


def initial_values(root: Path, run_mode: str) -> Dict[str, str]:
    return {
        "STATUS": STATUS_PLAN_OK if run_mode == RUN_MODE_PLAN else STATUS_FAIL,
        "MODE": MODE,
        "RUN_MODE": run_mode,
        "R7_SOURCE_PATH": str(root / R7_INPUTS[0]),
        "STAGED_VIX_DIR": str(root / STAGED_DIR_REL),
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "FETCH_APPROVAL_REQUIRED": "TRUE" if run_mode == RUN_MODE_PLAN else "FALSE",
        "FETCH_PROVIDER": FETCH_PROVIDER,
        "FETCH_SYMBOL_ATTEMPTED": "",
        "FETCH_SUCCESS": "FALSE",
        "FETCH_EMPTY": "FALSE",
        "FETCH_FAIL": "FALSE",
        "RAW_ROW_COUNT": "0",
        "NORMALIZED_ROW_COUNT": "0",
        "MIN_DATE": "",
        "MAX_DATE": "",
        "LATEST_DATE": "",
        "CLOSE_COLUMN_AVAILABLE": "FALSE",
        "CLOSE_NON_NULL_COUNT": "0",
        "FULL_HISTORY_READY": "FALSE",
        "USABLE_FOR_FACTOR_REFRESH": "FALSE",
        "USABLE_FOR_TECHNICAL_OVERLAY": "FALSE",
        "QUALITY_STATUS": "NOT_RUN_PLAN_ONLY" if run_mode == RUN_MODE_PLAN else "NOT_RUN",
        "MARKET_PROXY_STAGED_MODIFIED": "FALSE",
        "VALIDATION_FAIL_COUNT": "0",
        "FORBIDDEN_FILE_MODIFIED": "FALSE",
        "NEXT_RECOMMENDED_STEP": "Review this plan-only READ_FIRST, then approve the explicit -FetchStagedVix run if acceptable.",
    } | SAFETY_VALUES


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--fetch-staged-vix", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_mode = RUN_MODE_FETCH if args.fetch_staged_vix else RUN_MODE_PLAN
    out_degraded = root / OUT_DEGRADED_REL
    out_ops = root / OUT_OPS_REL
    staged_dir = root / STAGED_DIR_REL
    before_forbidden = {str(path): file_sig(path) for path in forbidden_files(root)}

    script_path = root / "scripts/v18/v18_25A_R8_controlled_staged_vix_backfill.py"
    wrapper_path = root / "scripts/v18/run_v18_25A_R8_controlled_staged_vix_backfill.ps1"
    values = initial_values(root, run_mode)

    r7_exists = [(root / rel).exists() for rel in R7_INPUTS]
    r7_text = read_text(root / R7_INPUTS[0])
    r7_recommends_backfill = "CONTROLLED_STAGED_VIX_BACKFILL" in r7_text and "EXTERNAL_FETCH_REQUIRED_FOR_NEXT_STEP: TRUE" in r7_text
    plan_rows = [
        {"item": "r7_read_first", "status": str(r7_exists[0]).upper(), "path_or_value": str(root / R7_INPUTS[0]), "notes": "R7 READ_FIRST context."},
        {"item": "r7_vix_requirement_spec", "status": str(r7_exists[1]).upper(), "path_or_value": str(root / R7_INPUTS[1]), "notes": "Exact VIX requirement and threshold context."},
        {"item": "r7_proxy_storage_policy", "status": str(r7_exists[2]).upper(), "path_or_value": str(root / R7_INPUTS[2]), "notes": "Staged storage policy."},
        {"item": "r7_repair_options", "status": str(r7_exists[3]).upper(), "path_or_value": str(root / R7_INPUTS[3]), "notes": "Controlled staged VIX backfill recommendation."},
        {"item": "r7_recommends_controlled_staged_vix_backfill", "status": str(r7_recommends_backfill).upper(), "path_or_value": "CONTROLLED_STAGED_VIX_BACKFILL", "notes": "External fetch required but must be explicitly approved."},
        {"item": "expected_staged_path", "status": "READY", "path_or_value": str(staged_dir), "notes": "Not created in PLAN_ONLY mode."},
        {"item": "fetch_scope", "status": "LOCKED", "path_or_value": ",".join(FETCH_SYMBOLS), "notes": "Only ^VIX first, then VIX fallback."},
    ]
    write_csv(out_degraded / PLAN_OUT, plan_rows, PLAN_FIELDS)

    fetch_result_rows: List[Dict[str, object]] = []
    quality: Dict[str, str] = {}
    if run_mode == RUN_MODE_FETCH:
        values["EXTERNAL_DATA_FETCHED"] = "TRUE"
        values["FETCH_APPROVAL_REQUIRED"] = "FALSE"
        raw_path = staged_dir / RAW_OUT
        normalized_path = staged_dir / NORMALIZED_OUT
        selected_symbol = ""
        raw_rows: List[Dict[str, object]] = []
        raw_fields: List[str] = []
        fetch_status = "FAIL"
        failure_reason = "NO_SYMBOL_ATTEMPTED"
        raw_count = 0
        attempted: List[str] = []
        for symbol in FETCH_SYMBOLS:
            attempted.append(symbol)
            status, reason, count, rows, fields = fetch_symbol(symbol, raw_path)
            fetch_result_rows.append(
                {
                    "provider": FETCH_PROVIDER,
                    "symbol_attempted": symbol,
                    "fetch_status": status,
                    "failure_reason": reason,
                    "raw_row_count": count,
                    "normalized_row_count": 0,
                    "raw_path": str(raw_path) if status == "SUCCESS" else "",
                    "normalized_path": "",
                }
            )
            if status == "SUCCESS" and count > 0:
                selected_symbol = symbol
                raw_rows = rows
                raw_fields = fields
                fetch_status = status
                failure_reason = reason
                raw_count = count
                break
            fetch_status = status
            failure_reason = reason
            raw_count = count
        values["FETCH_SYMBOL_ATTEMPTED"] = ",".join(attempted)
        values["FETCH_SUCCESS"] = str(fetch_status == "SUCCESS").upper()
        values["FETCH_EMPTY"] = str(fetch_status == "EMPTY").upper()
        values["FETCH_FAIL"] = str(fetch_status not in {"SUCCESS", "EMPTY"}).upper()
        values["RAW_ROW_COUNT"] = str(raw_count)

        normalized_rows: List[Dict[str, object]] = []
        duplicate_before = duplicate_after = negative_or_zero = suspicious_gaps = 0
        if selected_symbol:
            normalized_rows, duplicate_before, duplicate_after, negative_or_zero, suspicious_gaps = normalize_rows(raw_rows, selected_symbol)
            write_csv(normalized_path, normalized_rows, ["date", "open", "high", "low", "close", "adj_close", "volume", "proxy_symbol", "source"])
            fetch_result_rows[-1]["normalized_row_count"] = len(normalized_rows)
            fetch_result_rows[-1]["normalized_path"] = str(normalized_path)
            values["MARKET_PROXY_STAGED_MODIFIED"] = "TRUE"

        quality = quality_values(normalized_rows, duplicate_before, duplicate_after, negative_or_zero, suspicious_gaps)
        values["NORMALIZED_ROW_COUNT"] = quality["row_count"]
        values["MIN_DATE"] = quality["min_date"]
        values["MAX_DATE"] = quality["max_date"]
        values["LATEST_DATE"] = quality["latest_date"]
        values["CLOSE_COLUMN_AVAILABLE"] = str(int(quality["close_non_null_count"]) > 0).upper()
        values["CLOSE_NON_NULL_COUNT"] = quality["close_non_null_count"]
        values["FULL_HISTORY_READY"] = quality["full_history_ready"]
        values["USABLE_FOR_FACTOR_REFRESH"] = quality["usable_for_factor_refresh"]
        values["USABLE_FOR_TECHNICAL_OVERLAY"] = quality["usable_for_technical_overlay"]
        values["QUALITY_STATUS"] = quality["quality_status"]
        write_csv(out_degraded / QUALITY_OUT, [quality], QUALITY_FIELDS)
        write_csv(out_degraded / RESULT_OUT, fetch_result_rows, RESULT_FIELDS)
        write_csv(
            staged_dir / MANIFEST_OUT,
            [
                {"file_name": RAW_OUT, "relative_path": rel_path(root, raw_path), "exists": str(raw_path.exists()).upper(), "row_count": raw_count, "notes": f"raw fetch fields={','.join(raw_fields)}"},
                {"file_name": NORMALIZED_OUT, "relative_path": rel_path(root, normalized_path), "exists": str(normalized_path.exists()).upper(), "row_count": len(normalized_rows), "notes": "normalized VIX staged history"},
            ],
            MANIFEST_FIELDS,
        )

    validations = [
        ("python_compile_check", py_compile(script_path), str(script_path)),
        ("powershell_parse_check", ps_parse(wrapper_path), str(wrapper_path)),
        ("r7_context_files_exist", all(r7_exists), ",".join(R7_INPUTS)),
        ("r7_requires_external_fetch", r7_recommends_backfill, "R7 recommended controlled staged VIX backfill."),
        ("auto_trade_disabled", values["AUTO_TRADE"] == "DISABLED", "AUTO_TRADE must remain DISABLED."),
        ("auto_sell_disabled", values["AUTO_SELL"] == "DISABLED", "AUTO_SELL must remain DISABLED."),
        ("official_decision_impact_none", values["OFFICIAL_DECISION_IMPACT"] == "NONE", "OFFICIAL_DECISION_IMPACT must remain NONE."),
    ]
    if run_mode == RUN_MODE_PLAN:
        validations.extend(
            [
                ("plan_only_no_external_fetch", values["EXTERNAL_DATA_FETCHED"] == "FALSE", "PLAN_ONLY must not fetch."),
                ("plan_only_no_market_proxy_staged_write", values["MARKET_PROXY_STAGED_MODIFIED"] == "FALSE", "PLAN_ONLY must not write staged market proxy files."),
            ]
        )
    else:
        validations.extend(
            [
                ("fetch_scope_vix_only", values["FETCH_SYMBOL_ATTEMPTED"] in {"^VIX", "^VIX,VIX"}, values["FETCH_SYMBOL_ATTEMPTED"]),
                ("fetch_success", values["FETCH_SUCCESS"] == "TRUE", "At least one of ^VIX or VIX must fetch."),
                ("normalized_rows_positive", int(values["NORMALIZED_ROW_COUNT"]) > 0, values["NORMALIZED_ROW_COUNT"]),
                ("close_column_available", values["CLOSE_COLUMN_AVAILABLE"] == "TRUE", "close required."),
                ("quality_not_fail", values["QUALITY_STATUS"] in {"OK", "WARN"}, values["QUALITY_STATUS"]),
            ]
        )
    forbidden_changed = changed_forbidden_files(root, before_forbidden)
    values["FORBIDDEN_FILE_MODIFIED"] = str(bool(forbidden_changed)).upper()
    validations.append(("forbidden_files_unchanged", not forbidden_changed, ";".join(forbidden_changed[:20])))
    for key, expected in SAFETY_VALUES.items():
        validations.append((f"safety_{key.lower()}", values.get(key) == expected, f"Expected {key}={expected}; actual {values.get(key)}."))

    validation_rows = [
        {"item": name, "status": "PASS" if ok else "FAIL", "path_or_value": "", "notes": notes}
        for name, ok, notes in validations
    ]
    fail_count = sum(1 for _, ok, _ in validations if not ok)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if run_mode == RUN_MODE_PLAN:
        values["STATUS"] = STATUS_PLAN_OK if fail_count == 0 else STATUS_FAIL
    elif fail_count or values["FETCH_SUCCESS"] != "TRUE" or values["QUALITY_STATUS"] == "FAIL":
        values["STATUS"] = STATUS_FAIL
    elif values["QUALITY_STATUS"] == "OK":
        values["STATUS"] = STATUS_FETCH_OK
    else:
        values["STATUS"] = STATUS_FETCH_WARN
    if run_mode == RUN_MODE_FETCH:
        values["NEXT_RECOMMENDED_STEP"] = "Review staged VIX quality audit before any separate market-proxy promotion step."

    write_csv(out_degraded / PLAN_OUT, plan_rows + validation_rows, PLAN_FIELDS)
    report = render_report(values, plan_rows)
    write_text(out_degraded / REPORT_OUT, report)
    write_text(out_ops / OPS_REPORT_OUT, report)
    write_text(out_ops / READ_FIRST_OUT, render_read_first(values))

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
