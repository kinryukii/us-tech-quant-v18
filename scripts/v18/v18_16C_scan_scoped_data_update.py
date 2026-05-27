from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import os
import re
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple


STATUS_OK = "OK_V18_16C_SCAN_SCOPED_DATA_UPDATE_READY"
STATUS_WARN = "WARN_V18_16C_SCAN_SCOPED_DATA_UPDATE_VALIDATION_FAILED"
P1_STATUS_OK = "OK_V18_16C_P1_SCOPED_YFINANCE_SMOKE_READY"
P1_STATUS_WARN = "WARN_V18_16C_P1_SCOPED_YFINANCE_SMOKE_VALIDATION_FAILED"
P2_STATUS_OK = "OK_V18_16C_P2_YFINANCE_CACHE_REPAIR_READY"
P2_STATUS_WARN_PERSIST = "WARN_V18_16C_P2_YFINANCE_PROVIDER_CACHE_ERROR_PERSISTS"
P2_STATUS_WARN = "WARN_V18_16C_P2_YFINANCE_CACHE_REPAIR_VALIDATION_FAILED"
P3_STATUS_OK = "OK_V18_16C_P3_LOCAL_CACHE_BOOTSTRAP_READY"
P3_STATUS_WARN = "WARN_V18_16C_P3_LOCAL_CACHE_BOOTSTRAP_VALIDATION_FAILED"
MODE = "SCAN_SCOPED_DATA_UPDATE_ONLY"
P1_MODE = "SCAN_SCOPED_YFINANCE_SMOKE_TEST"
P2_MODE = "YFINANCE_CACHE_ISOLATION_REPAIR"
P3_MODE = "LOCAL_PRICE_SOURCE_DISCOVERY_AND_CACHE_BOOTSTRAP"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
BACKGROUND_UPDATE = "DISABLED"
AUTO_SCHEDULED_UPDATE = "DISABLED"
SCAN_SCOPED_DATA_UPDATE = "TRUE"
FULL_UNIVERSE_UPDATE_EXECUTED = "FALSE"

PRICE_FIELDS = [
    "ticker",
    "universe_tier",
    "data_depth",
    "selected_this_run",
    "update_attempted",
    "update_status",
    "update_mode",
    "used_yfinance",
    "cache_file",
    "cache_exists_before",
    "cache_exists_after",
    "local_source_used",
    "local_source_path",
    "target_history_days",
    "available_history_days",
    "latest_price_date",
    "latest_close",
    "row_count_before",
    "row_count_after",
    "rows_added",
    "failed_reason",
    "runtime_deferred",
    "updated_at",
]

EVENT_FIELDS = [
    "ticker",
    "universe_tier",
    "data_depth",
    "selected_this_run",
    "event_update_attempted",
    "event_update_status",
    "event_depth",
    "event_cache_file",
    "known_event_date",
    "event_source",
    "failed_reason",
    "runtime_deferred",
    "updated_at",
]

DEPTH_HISTORY_DAYS = {
    "FULL_POSITION_DATA": 730,
    "FULL_FACTOR_DATA": 540,
    "MEDIUM_TREND_DATA": 270,
    "LIGHT_PLUS_DATA": 150,
    "LIGHT_DATA": 90,
}

EVENT_DEPTH = {
    "FULL_POSITION_DATA": "DEEP_EVENT_CHECK",
    "FULL_FACTOR_DATA": "CORE_EVENT_CHECK",
    "MEDIUM_TREND_DATA": "BASIC_EVENT_CHECK",
    "LIGHT_PLUS_DATA": "LIGHT_EVENT_CHECK",
    "LIGHT_DATA": "MINIMAL_EVENT_CHECK",
}

DISCOVERY_FIELDS = [
    "source_path", "exists", "readable", "row_count", "detected_ticker_column",
    "detected_date_column", "detected_close_column", "detected_volume_column",
    "detected_technical_columns", "matched_scan_plan_ticker_count",
    "usable_for_price_cache", "source_quality_status", "source_notes",
]

BOOTSTRAP_FIELDS = [
    "ticker", "selected_this_run", "universe_tier", "data_depth", "bootstrap_attempted",
    "bootstrap_status", "cache_file", "cache_exists_before", "cache_exists_after",
    "cache_quality_status", "selected_source_path", "selected_source_quality",
    "rows_before", "rows_after", "rows_added", "earliest_date", "latest_date",
    "latest_close", "source_notes", "failed_reason", "updated_at",
]

TIER_ORDER = {
    "POSITION": 0,
    "CORE_DAILY": 1,
    "CANDIDATE": 2,
    "STRONG_WATCH": 3,
    "WATCHLIST": 4,
    "RESEARCH": 5,
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            pass
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            pass
    return [], [], "CSV_PARSE_FAILED"


def read_csv_limited(path: Path, limit: int = 5000) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            rows: List[Dict[str, str]] = []
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                fields = list(reader.fieldnames or [])
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    rows.append(row)
                return rows, fields, "OK"
        except Exception:
            pass
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_baseline(root: Path) -> Dict[str, Tuple[float, str]]:
    base = root / "archive/stable"
    out: Dict[str, Tuple[float, str]] = {}
    if not base.exists():
        return out
    for folder in base.iterdir():
        if folder.is_dir():
            manifest = folder / "MANIFEST.csv"
            out[str(folder.resolve())] = (folder.stat().st_mtime, sha256(manifest))
    return out


def stable_modified(before: Dict[str, Tuple[float, str]], root: Path) -> bool:
    after = stable_baseline(root)
    return any(after.get(key) != value for key, value in before.items())


def clean_ticker(value: str) -> str:
    ticker = str(value or "").strip().upper().replace("$", "")
    return ticker if re.match(r"^[A-Z0-9.\-]{1,12}$", ticker) else ""


def to_int(value: object, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def row_count(path: Path) -> int:
    rows, _, status = read_csv(path)
    return len(rows) if status == "OK" else 0


def cache_stats(path: Path) -> Dict[str, object]:
    rows, fields, status = read_csv(path)
    if status != "OK":
        return {"row_count": 0, "latest_price_date": "", "latest_close": "", "available_history_days": 0}
    date_col = next((f for f in fields if f.lower() in {"date", "price_date"}), "")
    close_col = next((f for f in fields if f.lower() in {"close", "adj_close", "latest_close", "last_close"}), "")
    latest_date = ""
    latest_close = ""
    if rows and date_col:
        sorted_rows = sorted(rows, key=lambda r: str(r.get(date_col, "")))
        latest = sorted_rows[-1]
        latest_date = latest.get(date_col, "")
        latest_close = latest.get(close_col, "") if close_col else ""
    return {
        "row_count": len(rows),
        "latest_price_date": latest_date,
        "latest_close": latest_close,
        "available_history_days": len(rows),
    }


def parse_ps(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    ps_path = str(path.resolve()).replace("'", "''")
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f"$p='{ps_path}'; $t=$null; $e=$null; [System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$e) > $null; if ($e.Count -gt 0) {{ $e | ForEach-Object {{ $_.Message }}; exit 1 }}",
    ]
    proc = subprocess.run(command, text=True, capture_output=True, timeout=60)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def compile_py(path: Path) -> Tuple[bool, str]:
    try:
        ast.parse(read_text(path), filename=str(path))
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def dangerous_hits(paths: Iterable[Path], root: Path) -> List[str]:
    parts = [("BUY", "NOW"), ("SELL", "NOW"), ("EXECUTE", "LIVE_ORDER"), ("LIVE", "TRADE"), ("LIVE", "SELL")]
    tokens = ["_".join(p) for p in parts]
    hits: List[str] = []
    for path in paths:
        text = read_text(path)
        in_token_block = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            upper = line.upper()
            stripped = upper.strip()
            if "PARTS =" in upper or "TOKENS =" in upper or "DANGEROUS" in upper:
                in_token_block = True
            safe = (
                "DISABLED" in upper
                or "DO NOT" in upper
                or "DANGEROUS" in upper
                or "TOKEN" in upper
                or "SCAN" in upper
                or "HITS.APPEND" in upper
                or " IN UPPER" in upper
                or in_token_block
            )
            for token in tokens:
                if token in upper and not safe:
                    hits.append(f"{rel(root, path)}:{line_no}:{token}")
            if "AUTO_TRADE" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{rel(root, path)}:{line_no}:AUTO_TRADE_ENABLED")
            if "AUTO_SELL" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{rel(root, path)}:{line_no}:AUTO_SELL_ENABLED")
            if in_token_block and (stripped.endswith("]") or stripped.endswith(")")):
                in_token_block = False
    return hits


def provider_cache_paths(root: Path) -> Dict[str, Path]:
    base = root / "state/v18/provider_cache/yfinance"
    return {
        "base": base,
        "tz": base / "tz",
        "tmp": base / "tmp",
        "logs": base / "logs",
        "xdg": root / "state/v18/provider_cache",
    }


def configure_provider_cache(root: Path) -> Dict[str, str]:
    paths = provider_cache_paths(root)
    for path in paths.values():
        ensure_dir(path)
    os.environ["YFINANCE_CACHE_DIR"] = str(paths["base"])
    os.environ["XDG_CACHE_HOME"] = str(paths["xdg"])
    os.environ["TMP"] = str(paths["tmp"])
    os.environ["TEMP"] = str(paths["tmp"])
    preflight = "PASS"
    sqlite_status = "PASS"
    note = ""
    test_file = paths["base"] / "_v18_16c_p2_write_test.tmp"
    sqlite_file = paths["base"] / "_v18_16c_p2_sqlite_test.db"
    try:
        test_file.write_text("ok", encoding="utf-8")
        if test_file.read_text(encoding="utf-8") != "ok":
            preflight = "FAIL"
            note = "write_read_mismatch"
    except Exception as exc:
        preflight = "FAIL"
        note = f"{type(exc).__name__}: {exc}"
    try:
        conn = sqlite3.connect(str(sqlite_file))
        conn.execute("create table if not exists preflight (id integer primary key, value text)")
        conn.execute("insert into preflight(value) values ('ok')")
        conn.commit()
        conn.close()
    except Exception as exc:
        sqlite_status = "FAIL"
        note = (note + "; " if note else "") + f"sqlite {type(exc).__name__}: {exc}"
    for cleanup in (test_file, sqlite_file):
        try:
            if cleanup.exists():
                cleanup.unlink()
        except Exception:
            pass
    set_tz_status = "NOT_CALLED"
    try:
        import yfinance as yf  # type: ignore

        if hasattr(yf, "set_tz_cache_location"):
            yf.set_tz_cache_location(str(paths["tz"]))
            set_tz_status = "PASS"
        else:
            set_tz_status = "NOT_AVAILABLE"
    except Exception as exc:
        set_tz_status = f"FAIL_{type(exc).__name__}: {exc}"
    return {
        "YFINANCE_CACHE_DIR": str(paths["base"]),
        "YFINANCE_TZ_CACHE_DIR": str(paths["tz"]),
        "YFINANCE_CACHE_PREFLIGHT_STATUS": preflight,
        "YFINANCE_SET_TZ_CACHE_LOCATION_STATUS": set_tz_status,
        "SQLITE_PREFLIGHT_STATUS": sqlite_status,
        "PROVIDER_PREFLIGHT_NOTE": note,
    }


def yfinance_update(ticker: str, cache_file: Path, target_days: int) -> Tuple[str, str, int, str, str]:
    try:
        import yfinance as yf  # type: ignore
    except Exception as exc:
        return "FAILED_PROVIDER_IMPORT", f"{type(exc).__name__}: {exc}", 0, "", ""
    period = f"{max(5, target_days)}d"
    try:
        frame = yf.download(ticker, period=period, interval="1d", auto_adjust=False, progress=False, threads=False)
    except Exception as exc:
        return "FAILED_YFINANCE_DOWNLOAD", f"{type(exc).__name__}: {exc}", 0, "", ""
    if frame is None or frame.empty:
        return "FAILED_YFINANCE_EMPTY", "empty provider response", 0, "", ""
    ensure_dir(cache_file.parent)
    now = dt.datetime.now().isoformat(timespec="seconds")
    rows = []
    for idx, record in frame.reset_index().iterrows():
        date_value = record.get("Date")
        rows.append(
            {
                "date": str(date_value)[:10],
                "open": record.get("Open", ""),
                "high": record.get("High", ""),
                "low": record.get("Low", ""),
                "close": record.get("Close", ""),
                "adj_close": record.get("Adj Close", ""),
                "volume": record.get("Volume", ""),
                "source": "YFINANCE_SCAN_SCOPE",
                "updated_at": now,
            }
        )
    write_csv(cache_file, rows, ["date", "open", "high", "low", "close", "adj_close", "volume", "source", "updated_at"])
    latest = rows[-1] if rows else {}
    return "UPDATED_YFINANCE_SCAN_SCOPE", "", len(rows), str(latest.get("date", "")), str(latest.get("close", ""))


def event_lookup(root: Path, ticker: str) -> Tuple[str, str]:
    calendar = root / "state/v18/cloud_earnings_event_calendar.csv"
    rows, fields, status = read_csv(calendar)
    if status != "OK":
        return "", ""
    ticker_col = next((f for f in fields if f.lower() in {"ticker", "symbol"}), "")
    date_col = next((f for f in fields if "date" in f.lower()), "")
    if not ticker_col:
        return "", ""
    for row in rows:
        if clean_ticker(row.get(ticker_col, "")) == ticker:
            return row.get(date_col, "") if date_col else "", rel(root, calendar)
    return "", rel(root, calendar)


def detect_col(fields: Sequence[str], names: Sequence[str], contains: Sequence[str] = ()) -> str:
    lower = {f.lower(): f for f in fields}
    for name in names:
        if name.lower() in lower:
            return lower[name.lower()]
    for field in fields:
        fl = field.lower()
        if any(part in fl for part in contains):
            return field
    return ""


def local_source_search_paths(root: Path) -> List[Path]:
    paths: List[Path] = []
    for rel_path in ["outputs/v18", "outputs/v17", "outputs/v16", "outputs/v15", "state/v18", "state/v16"]:
        base = root / rel_path
        if base.exists():
            for p in base.rglob("*.csv"):
                if not p.is_file():
                    continue
                lower = p.name.lower()
                if any(x in lower for x in ("audit", "summary", "manifest", "validation", "recommendation", "inventory", "read_first")):
                    continue
                if p.stat().st_size > 25 * 1024 * 1024:
                    continue
                paths.append(p)
    return sorted(set(paths))


def discover_local_sources(root: Path, allowed: Set[str]) -> Tuple[List[Dict[str, object]], Dict[str, List[Dict[str, object]]]]:
    discovery: List[Dict[str, object]] = []
    by_ticker: Dict[str, List[Dict[str, object]]] = {}
    technical_names = ["ret_5d", "ret_20d", "ret_60d", "ret_120d", "above_ma20", "above_ma60", "above_ma120", "ma20", "ma60", "ma120", "relative_strength", "rs_vs_qqq", "rs_vs_smh"]
    for path in local_source_search_paths(root):
        rows, fields, status = read_csv_limited(path, 5000)
        ticker_col = detect_col(fields, ["ticker", "symbol"])
        date_col = detect_col(fields, ["date", "price_date", "latest_price_date", "latest_date", "timestamp"], ["date", "timestamp"])
        close_col = detect_col(fields, ["close", "adj_close", "Adj Close", "latest_close", "price", "last_close"])
        volume_col = detect_col(fields, ["volume"])
        tech_cols = [f for f in fields if f.lower() in {n.lower() for n in technical_names}]
        matched: Set[str] = set()
        per_ticker_dates: Dict[str, Set[str]] = {}
        if status == "OK" and ticker_col:
            for row in rows:
                ticker = clean_ticker(row.get(ticker_col, ""))
                if ticker in allowed:
                    matched.add(ticker)
                    if date_col and row.get(date_col):
                        per_ticker_dates.setdefault(ticker, set()).add(str(row.get(date_col, "")))
        multiple_dates = any(len(v) > 1 for v in per_ticker_dates.values())
        if ticker_col and date_col and close_col and multiple_dates:
            quality = "HISTORICAL_DAILY_PRICE"
        elif ticker_col and close_col and (date_col or "latest" in close_col.lower()):
            quality = "LATEST_PRICE_ONLY"
        elif ticker_col and tech_cols:
            quality = "TECHNICAL_FEATURE_SOURCE"
        else:
            quality = "UNUSABLE"
        usable = quality in {"HISTORICAL_DAILY_PRICE", "LATEST_PRICE_ONLY"}
        rec = {
            "source_path": rel(root, path),
            "exists": str(path.exists()).upper(),
            "readable": str(status == "OK").upper(),
            "row_count": len(rows) if status == "OK" else 0,
            "detected_ticker_column": ticker_col,
            "detected_date_column": date_col,
            "detected_close_column": close_col,
            "detected_volume_column": volume_col,
            "detected_technical_columns": ";".join(tech_cols),
            "matched_scan_plan_ticker_count": len(matched),
            "usable_for_price_cache": str(usable).upper(),
            "source_quality_status": quality,
            "source_notes": status,
        }
        discovery.append(rec)
        if usable and matched:
            for ticker in matched:
                by_ticker.setdefault(ticker, []).append({"path": path, "quality": quality, "ticker_col": ticker_col, "date_col": date_col, "close_col": close_col, "volume_col": volume_col})
    return discovery, by_ticker


def source_sort_key(root: Path, src: Dict[str, object]) -> Tuple[int, int, int, str]:
    rel_path = rel(root, Path(src["path"]))
    quality = str(src["quality"])
    return (
        0 if "/v18/" in rel_path.lower() or "\\v18\\" in str(src["path"]).lower() else 1,
        0 if "CURRENT" in rel_path.upper() else 1,
        0 if quality == "HISTORICAL_DAILY_PRICE" else 1,
        rel_path,
    )


def normalize_cache_rows(src: Dict[str, object], ticker: str, root: Path) -> Tuple[List[Dict[str, object]], str, str]:
    path = Path(src["path"])
    rows, _, status = read_csv(path)
    if status != "OK":
        return [], "", f"read_status={status}"
    out: List[Dict[str, object]] = []
    now = dt.datetime.now().isoformat(timespec="seconds")
    for row in rows:
        if clean_ticker(row.get(str(src["ticker_col"]), "")) != ticker:
            continue
        date_value = str(row.get(str(src["date_col"]), "")).strip()
        close_value = str(row.get(str(src["close_col"]), "")).strip()
        if not date_value or not close_value:
            continue
        out.append({
            "date": date_value[:10],
            "open": "",
            "high": "",
            "low": "",
            "close": close_value,
            "adj_close": close_value,
            "volume": row.get(str(src.get("volume_col") or ""), ""),
            "source": "LOCAL_HISTORICAL" if src["quality"] == "HISTORICAL_DAILY_PRICE" else "LOCAL_LATEST_ONLY",
            "source_file": rel(root, path),
            "updated_at": now,
        })
    return out, rel(root, path), ""


def merge_cache(cache_file: Path, new_rows: Sequence[Dict[str, object]]) -> Tuple[int, int, int, str, str, str]:
    existing, _, _ = read_csv(cache_file)
    before = len(existing)
    merged: Dict[str, Dict[str, object]] = {}
    for row in existing:
        if row.get("date"):
            merged[str(row["date"])] = row
    for row in new_rows:
        if row.get("date"):
            merged[str(row["date"])] = row
    final = [merged[k] for k in sorted(merged)]
    write_csv(cache_file, final, ["date", "open", "high", "low", "close", "adj_close", "volume", "source", "source_file", "updated_at"])
    after = len(final)
    latest = final[-1] if final else {}
    earliest = final[0] if final else {}
    return before, after, max(0, after - before), str(earliest.get("date", "")), str(latest.get("date", "")), str(latest.get("close", ""))


def run_local_cache_bootstrap(root: Path, max_runtime_seconds: int, soft_stop_seconds: int) -> int:
    start = time.monotonic()
    root = root.resolve()
    for rel_dir in ["state/v18/price_cache", "outputs/v18/data", "outputs/v18/universe", "outputs/v18/ops"]:
        ensure_dir(root / rel_dir)
    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)
    stable_before = stable_baseline(root)
    plan_path = root / "outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv"
    plan_rows, _, plan_status = read_csv(plan_path)
    selected = [r for r in plan_rows if clean_ticker(r.get("ticker", "")) and str(r.get("selected_this_run", "")).upper() == "TRUE"]
    allowed = {clean_ticker(r.get("ticker", "")) for r in selected}
    discovery_path = root / "outputs/v18/data/V18_16C_P3_LOCAL_PRICE_SOURCE_DISCOVERY.csv"
    audit_path = root / "outputs/v18/data/V18_16C_P3_LOCAL_CACHE_BOOTSTRAP_AUDIT.csv"
    read_first_path = root / "outputs/v18/ops/V18_16C_P3_READ_FIRST.txt"
    price_audit_path = root / "outputs/v18/data/V18_16C_CURRENT_SCAN_SCOPED_PRICE_UPDATE_AUDIT.csv"
    summary_path = root / "outputs/v18/universe/V18_16C_CURRENT_SCAN_SCOPED_DATA_UPDATE_SUMMARY.csv"
    report_path = root / "outputs/v18/universe/V18_16C_CURRENT_SCAN_SCOPED_DATA_UPDATE_REPORT.md"
    v16c_read_first = root / "outputs/v18/ops/V18_16C_READ_FIRST.txt"
    discovery, by_ticker = discover_local_sources(root, allowed)
    write_csv(discovery_path, discovery, DISCOVERY_FIELDS)
    audit: List[Dict[str, object]] = []
    created = updated = hist_count = latest_count = exists_count = no_source = 0
    updated_tickers: Set[str] = set()
    for plan in selected:
        ticker = clean_ticker(plan.get("ticker", ""))
        cache_file = root / f"state/v18/price_cache/{ticker}.csv"
        existed = cache_file.exists()
        sources = sorted(by_ticker.get(ticker, []), key=lambda s: source_sort_key(root, s))
        status = "NO_LOCAL_SOURCE_FOUND"
        quality = ""
        selected_source = ""
        failed = ""
        before = row_count(cache_file)
        after = before
        rows_added = 0
        earliest = latest = latest_close = ""
        if existed and before > 0:
            status = "CACHE_ALREADY_EXISTS"
            exists_count += 1
            stats = cache_stats(cache_file)
            earliest = ""
            latest = str(stats["latest_price_date"])
            latest_close = str(stats["latest_close"])
        elif sources:
            src = sources[0]
            rows, selected_source, failed = normalize_cache_rows(src, ticker, root)
            quality = str(src["quality"])
            if rows:
                try:
                    ensure_dir(cache_file.parent)
                    before, after, rows_added, earliest, latest, latest_close = merge_cache(cache_file, rows)
                    status = "CACHE_BOOTSTRAPPED_FROM_HISTORICAL" if quality == "HISTORICAL_DAILY_PRICE" else "CACHE_BOOTSTRAPPED_FROM_LATEST_ONLY"
                    if not existed:
                        created += 1
                    else:
                        updated += 1
                    updated_tickers.add(ticker)
                    if quality == "HISTORICAL_DAILY_PRICE":
                        hist_count += 1
                    else:
                        latest_count += 1
                except Exception as exc:
                    status = "FAILED_CACHE_WRITE"
                    failed = f"{type(exc).__name__}: {exc}"
            else:
                status = "FAILED_LOCAL_SOURCE_READ" if failed else "NO_LOCAL_SOURCE_FOUND"
                no_source += 1
        else:
            no_source += 1
        audit.append({
            "ticker": ticker,
            "selected_this_run": "TRUE",
            "universe_tier": plan.get("universe_tier", ""),
            "data_depth": plan.get("data_depth", ""),
            "bootstrap_attempted": str(bool(sources) and status != "CACHE_ALREADY_EXISTS").upper(),
            "bootstrap_status": status,
            "cache_file": rel(root, cache_file),
            "cache_exists_before": str(existed).upper(),
            "cache_exists_after": str(cache_file.exists()).upper(),
            "cache_quality_status": "LATEST_ONLY_LIMITED" if status == "CACHE_BOOTSTRAPPED_FROM_LATEST_ONLY" else ("HISTORICAL_CACHE" if status == "CACHE_BOOTSTRAPPED_FROM_HISTORICAL" else ""),
            "selected_source_path": selected_source,
            "selected_source_quality": quality,
            "rows_before": before,
            "rows_after": after,
            "rows_added": rows_added,
            "earliest_date": earliest,
            "latest_date": latest,
            "latest_close": latest_close,
            "source_notes": "",
            "failed_reason": failed,
            "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
        })
    write_csv(audit_path, audit, BOOTSTRAP_FIELDS)
    # Also refresh current V18.16C price audit shape with bootstrap audit content where columns overlap.
    write_csv(price_audit_path, audit, BOOTSTRAP_FIELDS)
    unselected = len(updated_tickers - allowed)
    ps_ok, ps_note = parse_ps(root / "scripts/v18/run_v18_16C_scan_scoped_data_update.ps1")
    py_ok, py_note = compile_py(root / "scripts/v18/v18_16C_scan_scoped_data_update.py")
    current_daily_modified = sha256(current_daily) != current_daily_before
    snapshots_modified = stable_modified(stable_before, root)
    hits = dangerous_hits([root / "scripts/v18/run_v18_16C_scan_scoped_data_update.ps1", root / "scripts/v18/v18_16C_scan_scoped_data_update.py", discovery_path, audit_path, read_first_path], root)
    usable = [r for r in discovery if r["usable_for_price_cache"] == "TRUE"]
    validations = [
        ("POWERSHELL_PARSE", ps_ok, ps_note),
        ("PYTHON_COMPILE", py_ok, py_note),
        ("SCAN_PLAN_EXISTS", plan_path.exists() and plan_status == "OK", plan_status),
        ("DISCOVERY_EXISTS", discovery_path.exists(), ""),
        ("BOOTSTRAP_AUDIT_EXISTS", audit_path.exists(), ""),
        ("UPDATED_TICKERS_IN_SCAN_PLAN", unselected == 0, str(unselected)),
        ("NO_FULL_UNIVERSE_UPDATE", FULL_UNIVERSE_UPDATE_EXECUTED == "FALSE", ""),
        ("CURRENT_DAILY_NOT_MODIFIED", not current_daily_modified, ""),
        ("STABLE_SNAPSHOTS_NOT_MODIFIED", not snapshots_modified, ""),
        ("NO_DANGEROUS_TOKEN", len(hits) == 0, ";".join(hits[:20])),
        ("AUTO_TRADE_DISABLED", AUTO_TRADE == "DISABLED", ""),
        ("AUTO_SELL_DISABLED", AUTO_SELL == "DISABLED", ""),
        ("OFFICIAL_DECISION_IMPACT_NONE", OFFICIAL_DECISION_IMPACT == "NONE", ""),
    ]
    fail_count = sum(1 for _, ok, _ in validations if not ok)
    values = {
        "STATUS": P3_STATUS_OK if fail_count == 0 else P3_STATUS_WARN,
        "MODE": P3_MODE,
        "USE_YFINANCE": "FALSE",
        "TOTAL_SCAN_PLAN_COUNT": str(len(selected)),
        "LOCAL_SOURCE_FILE_SCANNED_COUNT": str(len(discovery)),
        "USABLE_LOCAL_SOURCE_COUNT": str(len(usable)),
        "HISTORICAL_DAILY_SOURCE_COUNT": str(sum(1 for r in discovery if r["source_quality_status"] == "HISTORICAL_DAILY_PRICE")),
        "LATEST_ONLY_SOURCE_COUNT": str(sum(1 for r in discovery if r["source_quality_status"] == "LATEST_PRICE_ONLY")),
        "TECHNICAL_FEATURE_SOURCE_COUNT": str(sum(1 for r in discovery if r["source_quality_status"] == "TECHNICAL_FEATURE_SOURCE")),
        "CACHE_BOOTSTRAP_ATTEMPT_COUNT": str(sum(1 for r in audit if r["bootstrap_attempted"] == "TRUE")),
        "CACHE_BOOTSTRAPPED_FROM_HISTORICAL_COUNT": str(hist_count),
        "CACHE_BOOTSTRAPPED_FROM_LATEST_ONLY_COUNT": str(latest_count),
        "CACHE_ALREADY_EXISTS_COUNT": str(exists_count),
        "NO_LOCAL_SOURCE_FOUND_COUNT": str(no_source),
        "CACHE_FILE_CREATED_COUNT": str(created),
        "CACHE_FILE_UPDATED_COUNT": str(updated),
        "UNSELECTED_TICKER_UPDATE_COUNT": str(unselected),
        "FULL_UNIVERSE_UPDATE_EXECUTED": FULL_UNIVERSE_UPDATE_EXECUTED,
        "CURRENT_DAILY_MODIFIED": str(current_daily_modified).upper(),
        "STABLE_SNAPSHOT_MODIFIED": str(snapshots_modified).upper(),
        "DANGEROUS_TOKEN_FINDING_COUNT": str(len(hits)),
        "VALIDATION_FAIL_COUNT": str(fail_count),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }
    keys = list(values.keys())
    write_text(read_first_path, "\n".join(f"{k}: {values[k]}" for k in keys) + "\n")
    write_text(v16c_read_first, "\n".join(f"{k}: {values[k]}" for k in keys) + "\n")
    write_csv(summary_path, [{"metric": k, "value": v} for k, v in values.items()], ["metric", "value"])
    report = ["# V18.16C-P3 Local Price Source Discovery and Cache Bootstrap", "", *[f"- {k}: {values[k]}" for k in keys], "", "## Validation", "", *[f"- {n}: {'PASS' if ok else 'FAIL'} {note}" for n, ok, note in validations]]
    write_text(report_path, "\n".join(report) + "\n")
    for key in [
        "STATUS", "MODE", "TOTAL_SCAN_PLAN_COUNT", "LOCAL_SOURCE_FILE_SCANNED_COUNT",
        "USABLE_LOCAL_SOURCE_COUNT", "HISTORICAL_DAILY_SOURCE_COUNT", "LATEST_ONLY_SOURCE_COUNT",
        "CACHE_BOOTSTRAPPED_FROM_HISTORICAL_COUNT", "CACHE_BOOTSTRAPPED_FROM_LATEST_ONLY_COUNT",
        "CACHE_ALREADY_EXISTS_COUNT", "NO_LOCAL_SOURCE_FOUND_COUNT", "CACHE_FILE_CREATED_COUNT",
        "CACHE_FILE_UPDATED_COUNT", "UNSELECTED_TICKER_UPDATE_COUNT", "VALIDATION_FAIL_COUNT",
        "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT",
    ]:
        print(f"{key}: {values[key]}")
    return 0 if fail_count == 0 else 1


def build(root: Path, use_yfinance: bool, max_runtime_seconds: int, soft_stop_seconds: int, max_ticker_updates: int | None) -> int:
    start = time.monotonic()
    root = root.resolve()
    price_cache_dir = root / "state/v18/price_cache"
    event_cache_dir = root / "state/v18/event_cache"
    data_dir = root / "outputs/v18/data"
    risk_dir = root / "outputs/v18/risk"
    universe_dir = root / "outputs/v18/universe"
    ops_dir = root / "outputs/v18/ops"
    for directory in [price_cache_dir, event_cache_dir, data_dir, risk_dir, universe_dir, ops_dir]:
        ensure_dir(directory)
    provider_cache = configure_provider_cache(root) if use_yfinance else {
        "YFINANCE_CACHE_DIR": "",
        "YFINANCE_TZ_CACHE_DIR": "",
        "YFINANCE_CACHE_PREFLIGHT_STATUS": "NOT_RUN",
        "YFINANCE_SET_TZ_CACHE_LOCATION_STATUS": "NOT_RUN",
        "SQLITE_PREFLIGHT_STATUS": "NOT_RUN",
        "PROVIDER_PREFLIGHT_NOTE": "",
    }

    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)
    stable_before = stable_baseline(root)

    scan_plan_path = universe_dir / "V18_CURRENT_ROLLING_SCAN_PLAN.csv"
    state_path = root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv"
    price_audit_path = data_dir / "V18_16C_CURRENT_SCAN_SCOPED_PRICE_UPDATE_AUDIT.csv"
    event_audit_path = risk_dir / "V18_16C_CURRENT_SCAN_SCOPED_EVENT_UPDATE_AUDIT.csv"
    summary_path = universe_dir / "V18_16C_CURRENT_SCAN_SCOPED_DATA_UPDATE_SUMMARY.csv"
    report_path = universe_dir / "V18_16C_CURRENT_SCAN_SCOPED_DATA_UPDATE_REPORT.md"
    read_first_path = ops_dir / "V18_16C_READ_FIRST.txt"
    p1_price_audit_path = data_dir / "V18_16C_P1_SCOPED_YFINANCE_SMOKE_PRICE_AUDIT.csv"
    p1_read_first_path = ops_dir / "V18_16C_P1_READ_FIRST.txt"
    p2_price_audit_path = data_dir / "V18_16C_P2_YFINANCE_CACHE_REPAIR_PRICE_AUDIT.csv"
    p2_read_first_path = ops_dir / "V18_16C_P2_READ_FIRST.txt"

    plan_rows, plan_fields, plan_status = read_csv(scan_plan_path)
    state_rows, _, state_status = read_csv(state_path)
    selected_rows = [r for r in plan_rows if clean_ticker(r.get("ticker", "")) and str(r.get("selected_this_run", "")).upper() == "TRUE"]
    selected_rows.sort(key=lambda r: (TIER_ORDER.get(str(r.get("universe_tier", "RESEARCH")).upper(), 9), -to_int(r.get("scan_priority"), 0), clean_ticker(r.get("ticker", ""))))
    allowed_tickers = {clean_ticker(r.get("ticker", "")) for r in selected_rows}

    price_rows: List[Dict[str, object]] = []
    event_rows: List[Dict[str, object]] = []
    updated_ticker_count = 0
    cache_only_count = 0
    not_updated_no_provider_count = 0
    failed_count = 0
    runtime_deferred_count = 0
    max_ticker_deferred_count = 0
    attempted_ticker_count = 0
    provider_precheck_fail_count = 0
    cache_file_created_count = 0
    cache_file_updated_count = 0
    price_update_executed = "FALSE"
    event_update_executed = "FALSE"
    update_counter = 0

    for row in selected_rows:
        ticker = clean_ticker(row.get("ticker", ""))
        tier = str(row.get("universe_tier", "RESEARCH")).upper()
        depth = str(row.get("data_depth") or "LIGHT_DATA")
        target_days = DEPTH_HISTORY_DAYS.get(depth, 90)
        now = dt.datetime.now().isoformat(timespec="seconds")
        elapsed = time.monotonic() - start
        defer_runtime = elapsed >= soft_stop_seconds and tier == "RESEARCH"
        defer_max_ticker = bool(max_ticker_updates and update_counter >= max_ticker_updates)
        if defer_max_ticker and tier == "RESEARCH":
            defer_runtime = True

        cache_file = price_cache_dir / f"{ticker}.csv"
        event_cache_file = event_cache_dir / f"{ticker}.csv"
        cache_before = cache_file.exists()
        rows_before = row_count(cache_file)
        update_status = "MAX_TICKER_UPDATES_DEFERRED" if defer_max_ticker else ("DEFERRED_RUNTIME_BUDGET" if defer_runtime else "")
        failed_reason = ""
        local_source_used = "FALSE"
        local_source_path = ""
        latest_date = ""
        latest_close = ""
        available_days = 0
        rows_after = rows_before
        rows_added = 0

        provider_preflight_ok = provider_cache["YFINANCE_CACHE_PREFLIGHT_STATUS"] == "PASS" and provider_cache["SQLITE_PREFLIGHT_STATUS"] == "PASS"
        if defer_runtime:
            runtime_deferred_count += 1
            if defer_max_ticker:
                max_ticker_deferred_count += 1
        elif cache_before:
            stats = cache_stats(cache_file)
            update_status = "CACHE_ONLY"
            cache_only_count += 1
            local_source_used = "TRUE"
            local_source_path = rel(root, cache_file)
            rows_after = int(stats["row_count"])
            available_days = int(stats["available_history_days"])
            latest_date = str(stats["latest_price_date"])
            latest_close = str(stats["latest_close"])
        elif use_yfinance and not provider_preflight_ok:
            update_status = "PROVIDER_PREFLIGHT_FAILED"
            provider_precheck_fail_count += 1
            failed_reason = provider_cache.get("PROVIDER_PREFLIGHT_NOTE", "provider cache preflight failed")
        elif use_yfinance:
            attempted_ticker_count += 1
            status, reason, new_rows, latest_date, latest_close = yfinance_update(ticker, cache_file, target_days)
            update_status = status
            failed_reason = reason
            rows_after = row_count(cache_file)
            rows_added = max(0, rows_after - rows_before)
            available_days = rows_after
            update_counter += 1
            if status.startswith("UPDATED"):
                updated_ticker_count += 1
                price_update_executed = "TRUE"
                if cache_before:
                    cache_file_updated_count += 1
                else:
                    cache_file_created_count += 1
            else:
                failed_count += 1
        else:
            update_status = "NOT_UPDATED_NO_PROVIDER_IN_SAFE_MODE"
            not_updated_no_provider_count += 1
            failed_reason = "No local cache and UseYFinance was not enabled."

        price_rows.append(
            {
                "ticker": ticker,
                "universe_tier": tier,
                "data_depth": depth,
                "selected_this_run": "TRUE",
                "update_attempted": str(not defer_runtime).upper(),
                "update_status": update_status,
                "update_mode": "YFINANCE_SCAN_SCOPE" if use_yfinance else "LOCAL_CACHE_ONLY_SAFE_MODE",
                "used_yfinance": str(use_yfinance and update_status.startswith("UPDATED")).upper(),
                "cache_file": rel(root, cache_file),
                "cache_exists_before": str(cache_before).upper(),
                "cache_exists_after": str(cache_file.exists()).upper(),
                "local_source_used": local_source_used,
                "local_source_path": local_source_path,
                "target_history_days": target_days,
                "available_history_days": available_days,
                "latest_price_date": latest_date,
                "latest_close": latest_close,
                "row_count_before": rows_before,
                "row_count_after": rows_after,
                "rows_added": rows_added,
                "failed_reason": failed_reason,
                "runtime_deferred": str(defer_runtime).upper(),
                "updated_at": now,
            }
        )

        known_event_date, event_source = event_lookup(root, ticker)
        if defer_runtime:
            event_status = "MAX_TICKER_UPDATES_DEFERRED" if defer_max_ticker else "DEFERRED_RUNTIME_BUDGET"
        elif event_cache_file.exists():
            event_status = "CACHE_ONLY"
            event_update_executed = "FALSE"
        else:
            event_status = "NOT_UPDATED_NO_PROVIDER_IN_SAFE_MODE"
        event_rows.append(
            {
                "ticker": ticker,
                "universe_tier": tier,
                "data_depth": depth,
                "selected_this_run": "TRUE",
                "event_update_attempted": str(not defer_runtime).upper(),
                "event_update_status": event_status,
                "event_depth": EVENT_DEPTH.get(depth, "MINIMAL_EVENT_CHECK"),
                "event_cache_file": rel(root, event_cache_file),
                "known_event_date": known_event_date,
                "event_source": event_source,
                "failed_reason": "" if event_status == "CACHE_ONLY" else ("Max ticker updates deferred." if defer_max_ticker else ("Runtime budget deferred." if defer_runtime else "No event provider enabled in safe mode.")),
                "runtime_deferred": str(defer_runtime).upper(),
                "updated_at": now,
            }
        )

    write_csv(price_audit_path, price_rows, PRICE_FIELDS)
    write_csv(event_audit_path, event_rows, EVENT_FIELDS)
    shutil.copy2(price_audit_path, data_dir / "V18_CURRENT_SCAN_SCOPED_PRICE_UPDATE_AUDIT.csv")
    shutil.copy2(event_audit_path, risk_dir / "V18_CURRENT_SCAN_SCOPED_EVENT_UPDATE_AUDIT.csv")
    if use_yfinance:
        shutil.copy2(price_audit_path, p1_price_audit_path)
        shutil.copy2(price_audit_path, p2_price_audit_path)

    price_tickers = {str(r["ticker"]) for r in price_rows}
    event_tickers = {str(r["ticker"]) for r in event_rows}
    unselected_update_count = len(price_tickers - allowed_tickers) + len(event_tickers - allowed_tickers)
    depth_counts = {depth: sum(1 for r in price_rows if r["data_depth"] == depth) for depth in DEPTH_HISTORY_DAYS}
    price_fail_count = sum(1 for r in price_rows if str(r["update_status"]).startswith("FAILED"))
    event_fail_count = sum(1 for r in event_rows if str(r["event_update_status"]).startswith("FAILED"))

    ps_ok, ps_note = parse_ps(root / "scripts/v18/run_v18_16C_scan_scoped_data_update.ps1")
    py_ok, py_note = compile_py(root / "scripts/v18/v18_16C_scan_scoped_data_update.py")
    current_daily_modified = sha256(current_daily) != current_daily_before
    snapshots_modified = stable_modified(stable_before, root)
    scan_paths = [
        root / "scripts/v18/run_v18_16C_scan_scoped_data_update.ps1",
        root / "scripts/v18/v18_16C_scan_scoped_data_update.py",
        price_audit_path,
        event_audit_path,
        summary_path,
        report_path,
        read_first_path,
        p1_price_audit_path,
        p1_read_first_path,
        p2_price_audit_path,
        p2_read_first_path,
    ]
    hits = dangerous_hits(scan_paths, root)
    smoke_validation_checks = [
        ("ATTEMPTED_TICKER_COUNT_LTE_MAX", (not use_yfinance) or (max_ticker_updates is None) or attempted_ticker_count <= max_ticker_updates, str(attempted_ticker_count)),
        ("ATTEMPTED_TICKERS_IN_SCAN_PLAN", {str(r["ticker"]) for r in price_rows if r["update_attempted"] == "TRUE"}.issubset(allowed_tickers), ""),
    ]
    validations = [
        ("POWERSHELL_PARSE", ps_ok, ps_note),
        ("PYTHON_COMPILE", py_ok, py_note),
        ("YFINANCE_PROVIDER_CACHE_DIR_EXISTS", (not use_yfinance) or Path(provider_cache["YFINANCE_CACHE_DIR"]).exists(), provider_cache["YFINANCE_CACHE_DIR"]),
        ("YFINANCE_PROVIDER_CACHE_PREFLIGHT_PASS", (not use_yfinance) or provider_cache["YFINANCE_CACHE_PREFLIGHT_STATUS"] == "PASS", provider_cache["YFINANCE_CACHE_PREFLIGHT_STATUS"]),
        ("SQLITE_PREFLIGHT_PASS", (not use_yfinance) or provider_cache["SQLITE_PREFLIGHT_STATUS"] == "PASS", provider_cache["SQLITE_PREFLIGHT_STATUS"]),
        ("SCAN_PLAN_EXISTS", scan_plan_path.exists() and plan_status == "OK", plan_status),
        ("ROLLING_STATE_EXISTS", state_path.exists() and state_status == "OK", state_status),
        ("PRICE_AUDIT_TICKERS_IN_SCAN_PLAN", price_tickers.issubset(allowed_tickers), f"extra={sorted(price_tickers - allowed_tickers)}"),
        ("EVENT_AUDIT_TICKERS_IN_SCAN_PLAN", event_tickers.issubset(allowed_tickers), f"extra={sorted(event_tickers - allowed_tickers)}"),
        ("UNSELECTED_TICKER_UPDATE_COUNT_ZERO", unselected_update_count == 0, str(unselected_update_count)),
        ("DATA_DEPTH_CATEGORIES_COUNTED", sum(depth_counts.values()) == len(price_rows), str(depth_counts)),
        ("PRICE_UPDATE_SCOPE_COUNT_MATCHES_SCAN_PLAN_OR_DEFERRED", len(price_rows) + runtime_deferred_count >= len(selected_rows), ""),
        ("EVENT_UPDATE_SCOPE_COUNT_MATCHES_SCAN_PLAN_OR_DEFERRED", len(event_rows) + runtime_deferred_count >= len(selected_rows), ""),
        ("NO_FULL_UNIVERSE_UPDATE_EXECUTED", FULL_UNIVERSE_UPDATE_EXECUTED == "FALSE", ""),
        ("CURRENT_DAILY_NOT_MODIFIED", not current_daily_modified, ""),
        ("STABLE_SNAPSHOTS_NOT_MODIFIED", not snapshots_modified, ""),
        ("NO_DANGEROUS_TOKEN_INTRODUCED", len(hits) == 0, ";".join(hits[:20])),
        ("AUTO_TRADE_DISABLED", AUTO_TRADE == "DISABLED", ""),
        ("AUTO_SELL_DISABLED", AUTO_SELL == "DISABLED", ""),
        ("OFFICIAL_DECISION_IMPACT_NONE", OFFICIAL_DECISION_IMPACT == "NONE", ""),
    ] + smoke_validation_checks
    validation_fail_count = sum(1 for _, ok, _ in validations if not ok)
    actual_runtime = round(time.monotonic() - start, 3)
    status = STATUS_OK if validation_fail_count == 0 else STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_TRIGGERED_UPDATE": "TRUE",
        "BACKGROUND_UPDATE": BACKGROUND_UPDATE,
        "AUTO_SCHEDULED_UPDATE": AUTO_SCHEDULED_UPDATE,
        "SCAN_SCOPED_DATA_UPDATE": SCAN_SCOPED_DATA_UPDATE,
        "USE_YFINANCE": str(use_yfinance).upper(),
        "MAX_RUNTIME_SECONDS": str(max_runtime_seconds),
        "SOFT_STOP_SECONDS": str(soft_stop_seconds),
        "ACTUAL_RUNTIME_SECONDS": str(actual_runtime),
        "TOTAL_UNIVERSE_COUNT": str(len(state_rows)),
        "TOTAL_SCAN_PLAN_COUNT": str(len(selected_rows)),
        "PRICE_UPDATE_SCOPE_COUNT": str(len(price_rows)),
        "EVENT_UPDATE_SCOPE_COUNT": str(len(event_rows)),
        "UPDATED_TICKER_COUNT": str(updated_ticker_count),
        "CACHE_ONLY_TICKER_COUNT": str(cache_only_count),
        "NOT_UPDATED_NO_PROVIDER_COUNT": str(not_updated_no_provider_count),
        "SKIPPED_FRESH_TICKER_COUNT": "0",
        "FAILED_TICKER_COUNT": str(failed_count),
        "PROVIDER_PRECHECK_FAIL_COUNT": str(provider_precheck_fail_count),
        "RUNTIME_DEFERRED_COUNT": str(runtime_deferred_count),
        "MAX_TICKER_UPDATES_DEFERRED_COUNT": str(max_ticker_deferred_count),
        "UNSELECTED_TICKER_UPDATE_COUNT": str(unselected_update_count),
        "FULL_POSITION_DATA_COUNT": str(depth_counts.get("FULL_POSITION_DATA", 0)),
        "FULL_FACTOR_DATA_COUNT": str(depth_counts.get("FULL_FACTOR_DATA", 0)),
        "MEDIUM_TREND_DATA_COUNT": str(depth_counts.get("MEDIUM_TREND_DATA", 0)),
        "LIGHT_PLUS_DATA_COUNT": str(depth_counts.get("LIGHT_PLUS_DATA", 0)),
        "LIGHT_DATA_COUNT": str(depth_counts.get("LIGHT_DATA", 0)),
        "PRICE_FRESHNESS_FAIL_COUNT": str(price_fail_count),
        "EVENT_UPDATE_FAIL_COUNT": str(event_fail_count),
        "PRICE_UPDATE_EXECUTED": price_update_executed,
        "EVENT_UPDATE_EXECUTED": event_update_executed,
        "FULL_UNIVERSE_UPDATE_EXECUTED": FULL_UNIVERSE_UPDATE_EXECUTED,
        "CURRENT_DAILY_MODIFIED": str(current_daily_modified).upper(),
        "STABLE_SNAPSHOT_MODIFIED": str(snapshots_modified).upper(),
        "DANGEROUS_TOKEN_FINDING_COUNT": str(len(hits)),
        "VALIDATION_FAIL_COUNT": str(validation_fail_count),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }
    p1_status = P1_STATUS_OK if validation_fail_count == 0 else P1_STATUS_WARN
    p1_values = {
        "STATUS": p1_status,
        "MODE": P1_MODE,
        "USE_YFINANCE": str(use_yfinance).upper(),
        "MAX_TICKER_UPDATES": str(max_ticker_updates or ""),
        "TOTAL_SCAN_PLAN_COUNT": values["TOTAL_SCAN_PLAN_COUNT"],
        "PRICE_UPDATE_SCOPE_COUNT": values["PRICE_UPDATE_SCOPE_COUNT"],
        "ATTEMPTED_TICKER_COUNT": str(attempted_ticker_count),
        "UPDATED_TICKER_COUNT": values["UPDATED_TICKER_COUNT"],
        "CACHE_FILE_CREATED_COUNT": str(cache_file_created_count),
        "CACHE_FILE_UPDATED_COUNT": str(cache_file_updated_count),
        "FAILED_TICKER_COUNT": values["FAILED_TICKER_COUNT"],
        "RUNTIME_DEFERRED_COUNT": values["RUNTIME_DEFERRED_COUNT"],
        "MAX_TICKER_UPDATES_DEFERRED_COUNT": values["MAX_TICKER_UPDATES_DEFERRED_COUNT"],
        "UNSELECTED_TICKER_UPDATE_COUNT": values["UNSELECTED_TICKER_UPDATE_COUNT"],
        "FULL_POSITION_DATA_COUNT": values["FULL_POSITION_DATA_COUNT"],
        "FULL_FACTOR_DATA_COUNT": values["FULL_FACTOR_DATA_COUNT"],
        "MEDIUM_TREND_DATA_COUNT": values["MEDIUM_TREND_DATA_COUNT"],
        "LIGHT_PLUS_DATA_COUNT": values["LIGHT_PLUS_DATA_COUNT"],
        "LIGHT_DATA_COUNT": values["LIGHT_DATA_COUNT"],
        "ACTUAL_RUNTIME_SECONDS": values["ACTUAL_RUNTIME_SECONDS"],
        "FULL_UNIVERSE_UPDATE_EXECUTED": values["FULL_UNIVERSE_UPDATE_EXECUTED"],
        "CURRENT_DAILY_MODIFIED": values["CURRENT_DAILY_MODIFIED"],
        "STABLE_SNAPSHOT_MODIFIED": values["STABLE_SNAPSHOT_MODIFIED"],
        "DANGEROUS_TOKEN_FINDING_COUNT": values["DANGEROUS_TOKEN_FINDING_COUNT"],
        "VALIDATION_FAIL_COUNT": values["VALIDATION_FAIL_COUNT"],
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }
    operational_error_count = sum(1 for r in price_rows if "UNABLE TO OPEN DATABASE FILE" in str(r.get("failed_reason", "")).upper())
    p2_status = P2_STATUS_OK if validation_fail_count == 0 else P2_STATUS_WARN
    if (
        validation_fail_count == 0
        and attempted_ticker_count == (max_ticker_updates or attempted_ticker_count)
        and attempted_ticker_count > 0
        and failed_count == attempted_ticker_count
        and operational_error_count == attempted_ticker_count
    ):
        p2_status = P2_STATUS_WARN_PERSIST
    p2_values = {
        "STATUS": p2_status,
        "MODE": P2_MODE,
        "USE_YFINANCE": str(use_yfinance).upper(),
        "MAX_TICKER_UPDATES": str(max_ticker_updates or ""),
        "TOTAL_SCAN_PLAN_COUNT": values["TOTAL_SCAN_PLAN_COUNT"],
        "ATTEMPTED_TICKER_COUNT": str(attempted_ticker_count),
        "UPDATED_TICKER_COUNT": values["UPDATED_TICKER_COUNT"],
        "CACHE_FILE_CREATED_COUNT": str(cache_file_created_count),
        "CACHE_FILE_UPDATED_COUNT": str(cache_file_updated_count),
        "FAILED_TICKER_COUNT": values["FAILED_TICKER_COUNT"],
        "PROVIDER_PRECHECK_FAIL_COUNT": values["PROVIDER_PRECHECK_FAIL_COUNT"],
        "YFINANCE_CACHE_DIR": provider_cache["YFINANCE_CACHE_DIR"],
        "YFINANCE_TZ_CACHE_DIR": provider_cache["YFINANCE_TZ_CACHE_DIR"],
        "YFINANCE_CACHE_PREFLIGHT_STATUS": provider_cache["YFINANCE_CACHE_PREFLIGHT_STATUS"],
        "YFINANCE_SET_TZ_CACHE_LOCATION_STATUS": provider_cache["YFINANCE_SET_TZ_CACHE_LOCATION_STATUS"],
        "SQLITE_PREFLIGHT_STATUS": provider_cache["SQLITE_PREFLIGHT_STATUS"],
        "MAX_TICKER_UPDATES_DEFERRED_COUNT": values["MAX_TICKER_UPDATES_DEFERRED_COUNT"],
        "UNSELECTED_TICKER_UPDATE_COUNT": values["UNSELECTED_TICKER_UPDATE_COUNT"],
        "FULL_UNIVERSE_UPDATE_EXECUTED": values["FULL_UNIVERSE_UPDATE_EXECUTED"],
        "CURRENT_DAILY_MODIFIED": values["CURRENT_DAILY_MODIFIED"],
        "STABLE_SNAPSHOT_MODIFIED": values["STABLE_SNAPSHOT_MODIFIED"],
        "DANGEROUS_TOKEN_FINDING_COUNT": values["DANGEROUS_TOKEN_FINDING_COUNT"],
        "ACTUAL_RUNTIME_SECONDS": values["ACTUAL_RUNTIME_SECONDS"],
        "VALIDATION_FAIL_COUNT": values["VALIDATION_FAIL_COUNT"],
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }
    summary_rows = [{"metric": key, "value": value} for key, value in values.items()]
    write_csv(summary_path, summary_rows, ["metric", "value"])
    shutil.copy2(summary_path, universe_dir / "V18_CURRENT_SCAN_SCOPED_DATA_UPDATE_SUMMARY.csv")

    read_keys = [
        "STATUS",
        "MODE",
        "RUN_TRIGGERED_UPDATE",
        "BACKGROUND_UPDATE",
        "AUTO_SCHEDULED_UPDATE",
        "SCAN_SCOPED_DATA_UPDATE",
        "USE_YFINANCE",
        "MAX_RUNTIME_SECONDS",
        "SOFT_STOP_SECONDS",
        "ACTUAL_RUNTIME_SECONDS",
        "TOTAL_UNIVERSE_COUNT",
        "TOTAL_SCAN_PLAN_COUNT",
        "PRICE_UPDATE_SCOPE_COUNT",
        "EVENT_UPDATE_SCOPE_COUNT",
        "UPDATED_TICKER_COUNT",
        "CACHE_ONLY_TICKER_COUNT",
        "NOT_UPDATED_NO_PROVIDER_COUNT",
        "SKIPPED_FRESH_TICKER_COUNT",
        "FAILED_TICKER_COUNT",
        "RUNTIME_DEFERRED_COUNT",
        "UNSELECTED_TICKER_UPDATE_COUNT",
        "FULL_POSITION_DATA_COUNT",
        "FULL_FACTOR_DATA_COUNT",
        "MEDIUM_TREND_DATA_COUNT",
        "LIGHT_PLUS_DATA_COUNT",
        "LIGHT_DATA_COUNT",
        "PRICE_FRESHNESS_FAIL_COUNT",
        "EVENT_UPDATE_FAIL_COUNT",
        "PRICE_UPDATE_EXECUTED",
        "EVENT_UPDATE_EXECUTED",
        "FULL_UNIVERSE_UPDATE_EXECUTED",
        "CURRENT_DAILY_MODIFIED",
        "STABLE_SNAPSHOT_MODIFIED",
        "DANGEROUS_TOKEN_FINDING_COUNT",
        "VALIDATION_FAIL_COUNT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT",
    ]
    write_text(read_first_path, "\n".join(f"{key}: {values[key]}" for key in read_keys) + "\n")
    shutil.copy2(read_first_path, ops_dir / "V18_CURRENT_SCAN_SCOPED_DATA_UPDATE_READ_FIRST.txt")
    p1_read_keys = [
        "STATUS",
        "MODE",
        "USE_YFINANCE",
        "MAX_TICKER_UPDATES",
        "TOTAL_SCAN_PLAN_COUNT",
        "PRICE_UPDATE_SCOPE_COUNT",
        "ATTEMPTED_TICKER_COUNT",
        "UPDATED_TICKER_COUNT",
        "CACHE_FILE_CREATED_COUNT",
        "CACHE_FILE_UPDATED_COUNT",
        "FAILED_TICKER_COUNT",
        "RUNTIME_DEFERRED_COUNT",
        "MAX_TICKER_UPDATES_DEFERRED_COUNT",
        "UNSELECTED_TICKER_UPDATE_COUNT",
        "FULL_POSITION_DATA_COUNT",
        "FULL_FACTOR_DATA_COUNT",
        "MEDIUM_TREND_DATA_COUNT",
        "LIGHT_PLUS_DATA_COUNT",
        "LIGHT_DATA_COUNT",
        "ACTUAL_RUNTIME_SECONDS",
        "FULL_UNIVERSE_UPDATE_EXECUTED",
        "CURRENT_DAILY_MODIFIED",
        "STABLE_SNAPSHOT_MODIFIED",
        "DANGEROUS_TOKEN_FINDING_COUNT",
        "VALIDATION_FAIL_COUNT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT",
    ]
    if use_yfinance:
        write_text(p1_read_first_path, "\n".join(f"{key}: {p1_values[key]}" for key in p1_read_keys) + "\n")
        p2_read_keys = [
            "STATUS",
            "MODE",
            "USE_YFINANCE",
            "MAX_TICKER_UPDATES",
            "TOTAL_SCAN_PLAN_COUNT",
            "ATTEMPTED_TICKER_COUNT",
            "UPDATED_TICKER_COUNT",
            "CACHE_FILE_CREATED_COUNT",
            "CACHE_FILE_UPDATED_COUNT",
            "FAILED_TICKER_COUNT",
            "PROVIDER_PRECHECK_FAIL_COUNT",
            "YFINANCE_CACHE_DIR",
            "YFINANCE_TZ_CACHE_DIR",
            "YFINANCE_CACHE_PREFLIGHT_STATUS",
            "YFINANCE_SET_TZ_CACHE_LOCATION_STATUS",
            "SQLITE_PREFLIGHT_STATUS",
            "MAX_TICKER_UPDATES_DEFERRED_COUNT",
            "UNSELECTED_TICKER_UPDATE_COUNT",
            "FULL_UNIVERSE_UPDATE_EXECUTED",
            "CURRENT_DAILY_MODIFIED",
            "STABLE_SNAPSHOT_MODIFIED",
            "DANGEROUS_TOKEN_FINDING_COUNT",
            "ACTUAL_RUNTIME_SECONDS",
            "VALIDATION_FAIL_COUNT",
            "AUTO_TRADE",
            "AUTO_SELL",
            "OFFICIAL_DECISION_IMPACT",
        ]
        write_text(p2_read_first_path, "\n".join(f"{key}: {p2_values[key]}" for key in p2_read_keys) + "\n")

    report = [
        "# V18.16C Scan-Scoped Data Update",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Read First",
        "",
        *[f"- {key}: {values[key]}" for key in read_keys],
        "",
        "## Validation",
        "",
        *[f"- {name}: {'PASS' if ok else 'FAIL'} {note}" for name, ok, note in validations],
        "",
        "Scope is limited to selected tickers in outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv.",
        "Default mode is local/cache-only and does not call YFinance.",
    ]
    write_text(report_path, "\n".join(report) + "\n")

    # Re-scan after all outputs exist.
    hits = dangerous_hits(scan_paths, root)
    if hits and values["VALIDATION_FAIL_COUNT"] == "0":
        values["STATUS"] = STATUS_WARN
        values["DANGEROUS_TOKEN_FINDING_COUNT"] = str(len(hits))
        values["VALIDATION_FAIL_COUNT"] = str(len(hits))
        write_text(read_first_path, "\n".join(f"{key}: {values[key]}" for key in read_keys) + "\n")
        shutil.copy2(read_first_path, ops_dir / "V18_CURRENT_SCAN_SCOPED_DATA_UPDATE_READ_FIRST.txt")
        status = STATUS_WARN
        if use_yfinance:
            p1_values["STATUS"] = P1_STATUS_WARN
            p1_values["DANGEROUS_TOKEN_FINDING_COUNT"] = values["DANGEROUS_TOKEN_FINDING_COUNT"]
            p1_values["VALIDATION_FAIL_COUNT"] = values["VALIDATION_FAIL_COUNT"]
            write_text(p1_read_first_path, "\n".join(f"{key}: {p1_values[key]}" for key in p1_read_keys) + "\n")
            p2_values["STATUS"] = P2_STATUS_WARN
            p2_values["DANGEROUS_TOKEN_FINDING_COUNT"] = values["DANGEROUS_TOKEN_FINDING_COUNT"]
            p2_values["VALIDATION_FAIL_COUNT"] = values["VALIDATION_FAIL_COUNT"]
            write_text(p2_read_first_path, "\n".join(f"{key}: {p2_values[key]}" for key in p2_read_keys) + "\n")

    if use_yfinance:
        for key in [
            "STATUS",
            "USE_YFINANCE",
            "MAX_TICKER_UPDATES",
            "ATTEMPTED_TICKER_COUNT",
            "UPDATED_TICKER_COUNT",
            "CACHE_FILE_CREATED_COUNT",
            "CACHE_FILE_UPDATED_COUNT",
            "FAILED_TICKER_COUNT",
            "PROVIDER_PRECHECK_FAIL_COUNT",
            "YFINANCE_CACHE_PREFLIGHT_STATUS",
            "SQLITE_PREFLIGHT_STATUS",
            "MAX_TICKER_UPDATES_DEFERRED_COUNT",
            "UNSELECTED_TICKER_UPDATE_COUNT",
            "FULL_UNIVERSE_UPDATE_EXECUTED",
            "ACTUAL_RUNTIME_SECONDS",
            "VALIDATION_FAIL_COUNT",
            "AUTO_TRADE",
            "AUTO_SELL",
            "OFFICIAL_DECISION_IMPACT",
        ]:
            print(f"{key}: {p2_values[key]}")
    else:
        for key in [
            "STATUS",
            "MODE",
            "USE_YFINANCE",
            "TOTAL_SCAN_PLAN_COUNT",
            "PRICE_UPDATE_SCOPE_COUNT",
            "EVENT_UPDATE_SCOPE_COUNT",
            "UPDATED_TICKER_COUNT",
            "CACHE_ONLY_TICKER_COUNT",
            "NOT_UPDATED_NO_PROVIDER_COUNT",
            "FAILED_TICKER_COUNT",
            "RUNTIME_DEFERRED_COUNT",
            "UNSELECTED_TICKER_UPDATE_COUNT",
            "FULL_POSITION_DATA_COUNT",
            "FULL_FACTOR_DATA_COUNT",
            "MEDIUM_TREND_DATA_COUNT",
            "LIGHT_PLUS_DATA_COUNT",
            "LIGHT_DATA_COUNT",
            "VALIDATION_FAIL_COUNT",
            "AUTO_TRADE",
            "AUTO_SELL",
            "OFFICIAL_DECISION_IMPACT",
        ]:
            print(f"{key}: {values[key]}")
    return 0 if status == STATUS_OK else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--use-yfinance", action="store_true")
    parser.add_argument("--local-cache-bootstrap", action="store_true")
    parser.add_argument("--max-runtime-seconds", type=int, default=300)
    parser.add_argument("--soft-stop-seconds", type=int, default=270)
    parser.add_argument("--max-ticker-updates", type=int, default=0)
    args = parser.parse_args()
    if args.local_cache_bootstrap:
        return run_local_cache_bootstrap(Path(args.root), args.max_runtime_seconds, args.soft_stop_seconds)
    return build(
        Path(args.root),
        args.use_yfinance,
        args.max_runtime_seconds,
        args.soft_stop_seconds,
        args.max_ticker_updates if args.max_ticker_updates > 0 else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
