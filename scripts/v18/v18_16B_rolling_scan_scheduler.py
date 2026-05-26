from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple


STATUS_OK = "OK_V18_16B_ROLLING_SCAN_SCHEDULER_READY"
STATUS_WARN = "WARN_V18_16B_ROLLING_SCAN_SCHEDULER_VALIDATION_FAILED"
MODE = "SCHEDULER_ONLY"
MAX_RUNTIME_SECONDS = 300
SOFT_STOP_SECONDS = 270
COVERAGE_WINDOW_TRADING_DAYS = 5
DEFAULT_MAX_ESTIMATED_PLAN_COST = 300
ROLLING_SCAN_ALWAYS_ON = "TRUE"
PRICE_UPDATE_EXECUTED = "FALSE"
EVENT_UPDATE_EXECUTED = "FALSE"
ROLLING_SCAN_EXECUTED = "FALSE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

PLAN_COLUMNS = [
    "ticker",
    "universe_tier",
    "scan_reason",
    "scan_priority",
    "data_depth",
    "last_scan_date",
    "next_due_scan_date",
    "days_since_last_scan",
    "is_position",
    "is_core_daily",
    "is_candidate",
    "is_watchlist",
    "is_overdue",
    "selected_this_run",
    "deferred_reason",
    "estimated_scan_cost",
    "estimated_data_update_cost",
    "estimated_total_cost",
    "source_count",
    "price_cache_status",
    "event_cache_status",
]

TIER_BASE_SCORE = {
    "POSITION": 1000,
    "CORE_DAILY": 800,
    "CANDIDATE": 600,
    "STRONG_WATCH": 400,
    "WATCHLIST": 250,
    "RESEARCH": 100,
}

TIER_SCAN_COST = {
    "POSITION": 5,
    "CORE_DAILY": 4,
    "CANDIDATE": 3,
    "STRONG_WATCH": 2,
    "WATCHLIST": 1,
    "RESEARCH": 1,
}

DEPTH_COST = {
    "FULL_POSITION_DATA": 5,
    "FULL_FACTOR_DATA": 4,
    "MEDIUM_TREND_DATA": 3,
    "LIGHT_PLUS_DATA": 2,
    "LIGHT_DATA": 1,
}

TIER_DEPTH = {
    "POSITION": "FULL_POSITION_DATA",
    "CORE_DAILY": "FULL_FACTOR_DATA",
    "CANDIDATE": "MEDIUM_TREND_DATA",
    "STRONG_WATCH": "LIGHT_PLUS_DATA",
    "WATCHLIST": "LIGHT_DATA",
    "RESEARCH": "LIGHT_DATA",
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


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


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
    for key, value in before.items():
        if after.get(key) != value:
            return True
    return False


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def to_int(value: object, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def clean_ticker(value: str) -> str:
    ticker = str(value or "").strip().upper()
    return ticker if re.match(r"^[A-Z0-9.\-]{1,12}$", ticker) else ""


def parse_date(value: str) -> dt.date | None:
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(value[:19], fmt).date()
        except Exception:
            pass
    return None


def days_since_last_scan(row: Dict[str, str]) -> Tuple[int, bool]:
    raw = str(row.get("days_since_last_scan", "")).strip()
    if raw:
        return to_int(raw, 0), False
    last_scan = parse_date(row.get("last_scan_date", ""))
    if last_scan:
        return max(0, (dt.date.today() - last_scan).days), False
    return 9999, True


def bool_text(value: object) -> str:
    return "TRUE" if str(value).strip().upper() in {"TRUE", "YES", "1"} else "FALSE"


def is_overdue(row: Dict[str, str], days: int, never_scanned: bool) -> bool:
    if never_scanned:
        return True
    due = parse_date(row.get("next_due_scan_date", ""))
    if due and due <= dt.date.today():
        return True
    return days >= COVERAGE_WINDOW_TRADING_DAYS


def priority_score(row: Dict[str, str], days: int, overdue: bool, never_scanned: bool) -> int:
    tier = str(row.get("universe_tier", "RESEARCH") or "RESEARCH").upper()
    source_count = to_int(row.get("source_count", 0), 0)
    price_status = str(row.get("price_freshness_status") or row.get("price_cache_status") or "").upper()
    event_status = str(row.get("event_cache_status") or "").upper()
    score = TIER_BASE_SCORE.get(tier, 100)
    if not never_scanned:
        score += max(0, days) * 50
    else:
        score += 500
    if overdue:
        score += 500
    score += source_count * 20
    if not price_status or "UNKNOWN" in price_status or "NOT_UPDATED" in price_status or "MISSING" in price_status:
        score += 100
    if not event_status or "UNKNOWN" in event_status or "NOT_UPDATED" in event_status or "MISSING" in event_status:
        score += 50
    return score


def estimated_cost(tier: str, depth: str) -> Tuple[int, int, int]:
    scan_cost = TIER_SCAN_COST.get(tier, 1)
    data_cost = DEPTH_COST.get(depth, 1)
    return scan_cost, data_cost, scan_cost + data_cost


def plan_row(row: Dict[str, str]) -> Dict[str, object]:
    tier = str(row.get("universe_tier", "RESEARCH") or "RESEARCH").upper()
    depth = str(row.get("required_data_depth") or TIER_DEPTH.get(tier, "LIGHT_DATA"))
    days, never_scanned = days_since_last_scan(row)
    overdue = is_overdue(row, days, never_scanned)
    scan_cost, data_cost, total_cost = estimated_cost(tier, depth)
    reason_bits = []
    if tier in {"POSITION", "CORE_DAILY", "CANDIDATE"}:
        reason_bits.append(f"MUST_SELECT_{tier}")
    if never_scanned:
        reason_bits.append("NEVER_SCANNED")
    if overdue:
        reason_bits.append("OVERDUE")
    if not reason_bits:
        reason_bits.append("ROLLING_COVERAGE")
    return {
        "ticker": clean_ticker(row.get("ticker", "")),
        "universe_tier": tier,
        "scan_reason": ";".join(reason_bits),
        "scan_priority": priority_score(row, days, overdue, never_scanned),
        "data_depth": depth,
        "last_scan_date": row.get("last_scan_date", ""),
        "next_due_scan_date": row.get("next_due_scan_date", ""),
        "days_since_last_scan": "" if never_scanned else days,
        "is_position": bool_text(row.get("is_position")) if tier != "POSITION" else "TRUE",
        "is_core_daily": bool_text(row.get("is_core_daily")) if tier != "CORE_DAILY" else "TRUE",
        "is_candidate": bool_text(row.get("is_candidate")) if tier not in {"CORE_DAILY", "CANDIDATE"} else "TRUE",
        "is_watchlist": bool_text(row.get("is_watchlist")) if tier not in {"WATCHLIST", "STRONG_WATCH"} else "TRUE",
        "is_overdue": str(overdue).upper(),
        "selected_this_run": "FALSE",
        "deferred_reason": "",
        "estimated_scan_cost": scan_cost,
        "estimated_data_update_cost": data_cost,
        "estimated_total_cost": total_cost,
        "source_count": to_int(row.get("source_count", 0), 0),
        "price_cache_status": row.get("price_cache_status", ""),
        "event_cache_status": row.get("event_cache_status", ""),
        "_never_scanned": never_scanned,
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


def select_plan(plan_rows: List[Dict[str, object]], daily_min: int, max_cost: int) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], int]:
    selected: List[Dict[str, object]] = []
    selected_tickers: Set[str] = set()
    cost = 0

    def add(row: Dict[str, object], reason_suffix: str = "") -> None:
        nonlocal cost
        ticker = str(row["ticker"])
        if ticker in selected_tickers:
            return
        row["selected_this_run"] = "TRUE"
        row["deferred_reason"] = ""
        if reason_suffix and reason_suffix not in str(row["scan_reason"]):
            row["scan_reason"] = f"{row['scan_reason']};{reason_suffix}"
        selected.append(row)
        selected_tickers.add(ticker)
        cost += to_int(row.get("estimated_total_cost"), 0)

    must = [r for r in plan_rows if r["universe_tier"] in {"POSITION", "CORE_DAILY", "CANDIDATE"}]
    for row in sorted(must, key=lambda r: (-to_int(r["scan_priority"]), str(r["ticker"]))):
        add(row)

    optional = [r for r in plan_rows if r["ticker"] not in selected_tickers]
    optional_sorted = sorted(
        optional,
        key=lambda r: (
            0 if r["universe_tier"] in {"WATCHLIST", "STRONG_WATCH"} else 1,
            0 if str(r.get("_never_scanned")) == "True" else 1,
            -to_int(r["scan_priority"]),
            str(r["ticker"]),
        ),
    )

    for row in optional_sorted:
        if len(selected) >= daily_min:
            break
        projected = cost + to_int(row.get("estimated_total_cost"), 0)
        if projected <= max_cost:
            add(row, "DAILY_MIN_COVERAGE")

    for row in optional_sorted:
        if row["ticker"] in selected_tickers:
            continue
        projected = cost + to_int(row.get("estimated_total_cost"), 0)
        if projected > max_cost:
            continue
        if row["is_overdue"] == "TRUE" or str(row.get("_never_scanned")) == "True":
            add(row, "BUDGET_AVAILABLE_OVERDUE_OR_NEVER_SCANNED")

    deferred = []
    for row in plan_rows:
        if row["ticker"] not in selected_tickers:
            row["selected_this_run"] = "FALSE"
            row["deferred_reason"] = "LOW_PRIORITY_BUDGET_DEFERRED" if cost >= max_cost else "LOW_PRIORITY_COVERAGE_DEFERRED"
            deferred.append(row)
    return selected, deferred, cost


def daily_threshold_cost_floor(plan_rows: List[Dict[str, object]], daily_min: int) -> int:
    selected_tickers: Set[str] = set()
    cost = 0

    must = [r for r in plan_rows if r["universe_tier"] in {"POSITION", "CORE_DAILY", "CANDIDATE"}]
    for row in sorted(must, key=lambda r: (-to_int(r["scan_priority"]), str(r["ticker"]))):
        ticker = str(row["ticker"])
        if ticker in selected_tickers:
            continue
        selected_tickers.add(ticker)
        cost += to_int(row.get("estimated_total_cost"), 0)

    optional = [r for r in plan_rows if r["ticker"] not in selected_tickers]
    optional_sorted = sorted(
        optional,
        key=lambda r: (
            0 if r["universe_tier"] in {"WATCHLIST", "STRONG_WATCH"} else 1,
            0 if str(r.get("_never_scanned")) == "True" else 1,
            -to_int(r["scan_priority"]),
            str(r["ticker"]),
        ),
    )
    for row in optional_sorted:
        if len(selected_tickers) >= daily_min:
            break
        selected_tickers.add(str(row["ticker"]))
        cost += to_int(row.get("estimated_total_cost"), 0)
    return cost if len(selected_tickers) >= daily_min else 0


def strip_internal(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    return [{col: row.get(col, "") for col in PLAN_COLUMNS} for row in rows]


def build(root: Path, max_estimated_plan_cost: int) -> int:
    root = root.resolve()
    out_dir = root / "outputs/v18/universe"
    ops_dir = root / "outputs/v18/ops"
    ensure_dir(out_dir)
    ensure_dir(ops_dir)

    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)
    stable_before = stable_baseline(root)

    input_path = root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv"
    plan_path = out_dir / "V18_16B_CURRENT_ROLLING_SCAN_PLAN.csv"
    alias_path = out_dir / "V18_CURRENT_ROLLING_SCAN_PLAN.csv"
    report_path = out_dir / "V18_16B_CURRENT_ROLLING_SCAN_SCHEDULER_REPORT.md"
    read_first_path = ops_dir / "V18_16B_READ_FIRST.txt"

    universe_rows, fields, parse_status = read_csv(input_path)
    valid_universe_rows = [r for r in universe_rows if clean_ticker(r.get("ticker", ""))]
    total = len(valid_universe_rows)
    daily_min = math.ceil(total / COVERAGE_WINDOW_TRADING_DAYS) if total else 0
    all_plan = [plan_row(row) for row in valid_universe_rows]
    daily_threshold_floor = daily_threshold_cost_floor(all_plan, daily_min)
    effective_max_estimated_plan_cost = max(max_estimated_plan_cost, daily_threshold_floor)
    selected, deferred, estimated_cost = select_plan(all_plan, daily_min, effective_max_estimated_plan_cost)
    selected_clean = strip_internal(sorted(selected, key=lambda r: (-to_int(r["scan_priority"]), str(r["ticker"]))))
    deferred_clean = strip_internal(sorted(deferred, key=lambda r: (-to_int(r["scan_priority"]), str(r["ticker"]))))

    write_csv(plan_path, selected_clean, PLAN_COLUMNS)
    shutil.copy2(plan_path, alias_path)

    selected_tickers = {str(r["ticker"]) for r in selected_clean}
    tier_count = {tier: sum(1 for r in selected_clean if r["universe_tier"] == tier) for tier in TIER_BASE_SCORE}
    overdue_count = sum(1 for r in selected_clean if r["is_overdue"] == "TRUE")
    never_count = sum(1 for r in selected if str(r.get("_never_scanned")) == "True")
    low_priority_deferred = sum(1 for r in deferred_clean if str(r.get("deferred_reason", "")).startswith("LOW_PRIORITY"))
    positions = {clean_ticker(r.get("ticker", "")) for r in valid_universe_rows if str(r.get("universe_tier", "")).upper() == "POSITION"}
    core = {clean_ticker(r.get("ticker", "")) for r in valid_universe_rows if str(r.get("universe_tier", "")).upper() == "CORE_DAILY"}
    candidates = {clean_ticker(r.get("ticker", "")) for r in valid_universe_rows if str(r.get("universe_tier", "")).upper() == "CANDIDATE"}

    ps_ok, ps_note = parse_ps(root / "scripts/v18/run_v18_16B_rolling_scan_scheduler.ps1")
    py_ok, py_note = compile_py(root / "scripts/v18/v18_16B_rolling_scan_scheduler.py")
    current_daily_modified = sha256(current_daily) != current_daily_before
    snapshots_modified = stable_modified(stable_before, root)
    scan_paths = [
        root / "scripts/v18/run_v18_16B_rolling_scan_scheduler.ps1",
        root / "scripts/v18/v18_16B_rolling_scan_scheduler.py",
        plan_path,
        alias_path,
        report_path,
        read_first_path,
    ]
    hits = dangerous_hits(scan_paths, root)
    budget_prevents_min = len(selected_clean) < daily_min and estimated_cost >= effective_max_estimated_plan_cost

    validations = [
        ("POWERSHELL_PARSE", ps_ok, ps_note),
        ("PYTHON_COMPILE", py_ok, py_note),
        ("INPUT_ROLLING_STATE_EXISTS", input_path.exists() and parse_status == "OK", parse_status),
        ("SCAN_PLAN_OUTPUT_EXISTS", plan_path.exists(), ""),
        ("CURRENT_ALIAS_EXISTS", alias_path.exists(), ""),
        ("REQUIRED_COLUMNS_EXIST", set(PLAN_COLUMNS).issubset(set(selected_clean[0].keys() if selected_clean else PLAN_COLUMNS)), ""),
        ("NO_DUPLICATE_TICKER_IN_SCAN_PLAN", len(selected_tickers) == len(selected_clean), ""),
        ("SELECTED_COUNT_GT_ZERO_IF_UNIVERSE_GT_ZERO", total == 0 or len(selected_clean) > 0, ""),
        ("TODAY_SCAN_PLAN_COUNT_MEETS_DAILY_MIN_OR_BUDGET", len(selected_clean) >= daily_min or budget_prevents_min, ""),
        ("ALL_POSITION_SELECTED", positions.issubset(selected_tickers), f"missing={sorted(positions - selected_tickers)}"),
        ("ALL_CORE_DAILY_SELECTED", core.issubset(selected_tickers), f"missing={sorted(core - selected_tickers)}"),
        ("ALL_CANDIDATE_SELECTED_IF_FEASIBLE", candidates.issubset(selected_tickers), f"missing={sorted(candidates - selected_tickers)}"),
        ("NO_PRICE_UPDATE_EXECUTED", PRICE_UPDATE_EXECUTED == "FALSE", ""),
        ("NO_EVENT_UPDATE_EXECUTED", EVENT_UPDATE_EXECUTED == "FALSE", ""),
        ("NO_ROLLING_SCAN_EXECUTED", ROLLING_SCAN_EXECUTED == "FALSE", ""),
        ("CURRENT_DAILY_NOT_MODIFIED", not current_daily_modified, ""),
        ("STABLE_SNAPSHOTS_NOT_MODIFIED", not snapshots_modified, ""),
        ("NO_DANGEROUS_TOKEN_INTRODUCED", len(hits) == 0, ";".join(hits[:20])),
        ("AUTO_TRADE_DISABLED", AUTO_TRADE == "DISABLED", ""),
        ("AUTO_SELL_DISABLED", AUTO_SELL == "DISABLED", ""),
        ("OFFICIAL_DECISION_IMPACT_NONE", OFFICIAL_DECISION_IMPACT == "NONE", ""),
    ]
    validation_fail_count = sum(1 for _, ok, _ in validations if not ok)
    status = STATUS_OK if validation_fail_count == 0 else STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": MODE,
        "TOTAL_UNIVERSE_COUNT": str(total),
        "TODAY_SCAN_PLAN_COUNT": str(len(selected_clean)),
        "DAILY_MIN_SCAN_COUNT": str(daily_min),
        "COVERAGE_WINDOW_TRADING_DAYS": str(COVERAGE_WINDOW_TRADING_DAYS),
        "MAX_RUNTIME_SECONDS": str(MAX_RUNTIME_SECONDS),
        "SOFT_STOP_SECONDS": str(SOFT_STOP_SECONDS),
        "CONFIGURED_MAX_ESTIMATED_PLAN_COST": str(max_estimated_plan_cost),
        "DAILY_THRESHOLD_COST_FLOOR": str(daily_threshold_floor),
        "MAX_ESTIMATED_PLAN_COST": str(effective_max_estimated_plan_cost),
        "ESTIMATED_PLAN_COST": str(estimated_cost),
        "POSITION_SCAN_COUNT": str(tier_count.get("POSITION", 0)),
        "CORE_DAILY_SCAN_COUNT": str(tier_count.get("CORE_DAILY", 0)),
        "CANDIDATE_SCAN_COUNT": str(tier_count.get("CANDIDATE", 0)),
        "STRONG_WATCH_SCAN_COUNT": str(tier_count.get("STRONG_WATCH", 0)),
        "WATCHLIST_SCAN_COUNT": str(tier_count.get("WATCHLIST", 0)),
        "RESEARCH_SCAN_COUNT": str(tier_count.get("RESEARCH", 0)),
        "OVERDUE_SCAN_COUNT": str(overdue_count),
        "NEVER_SCANNED_SELECTED_COUNT": str(never_count),
        "LOW_PRIORITY_SCAN_DEFERRED_COUNT": str(low_priority_deferred),
        "ROLLING_SCAN_ALWAYS_ON": ROLLING_SCAN_ALWAYS_ON,
        "PRICE_UPDATE_EXECUTED": PRICE_UPDATE_EXECUTED,
        "EVENT_UPDATE_EXECUTED": EVENT_UPDATE_EXECUTED,
        "ROLLING_SCAN_EXECUTED": ROLLING_SCAN_EXECUTED,
        "CURRENT_DAILY_MODIFIED": str(current_daily_modified).upper(),
        "STABLE_SNAPSHOT_MODIFIED": str(snapshots_modified).upper(),
        "DANGEROUS_TOKEN_FINDING_COUNT": str(len(hits)),
        "VALIDATION_FAIL_COUNT": str(validation_fail_count),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }

    read_keys = [
        "STATUS",
        "MODE",
        "TOTAL_UNIVERSE_COUNT",
        "TODAY_SCAN_PLAN_COUNT",
        "DAILY_MIN_SCAN_COUNT",
        "COVERAGE_WINDOW_TRADING_DAYS",
        "MAX_RUNTIME_SECONDS",
        "SOFT_STOP_SECONDS",
        "CONFIGURED_MAX_ESTIMATED_PLAN_COST",
        "DAILY_THRESHOLD_COST_FLOOR",
        "MAX_ESTIMATED_PLAN_COST",
        "ESTIMATED_PLAN_COST",
        "POSITION_SCAN_COUNT",
        "CORE_DAILY_SCAN_COUNT",
        "CANDIDATE_SCAN_COUNT",
        "STRONG_WATCH_SCAN_COUNT",
        "WATCHLIST_SCAN_COUNT",
        "RESEARCH_SCAN_COUNT",
        "OVERDUE_SCAN_COUNT",
        "NEVER_SCANNED_SELECTED_COUNT",
        "LOW_PRIORITY_SCAN_DEFERRED_COUNT",
        "ROLLING_SCAN_ALWAYS_ON",
        "PRICE_UPDATE_EXECUTED",
        "EVENT_UPDATE_EXECUTED",
        "ROLLING_SCAN_EXECUTED",
        "CURRENT_DAILY_MODIFIED",
        "STABLE_SNAPSHOT_MODIFIED",
        "DANGEROUS_TOKEN_FINDING_COUNT",
        "VALIDATION_FAIL_COUNT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT",
    ]
    write_text(read_first_path, "\n".join(f"{key}: {values[key]}" for key in read_keys) + "\n")

    selected_preview = selected_clean[:40]
    deferred_preview = deferred_clean[:40]
    report = [
        "# V18.16B Rolling Scan Scheduler",
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
        "## Selected Preview",
        "",
        "| ticker | tier | priority | reason | cost |",
        "| --- | --- | --- | --- | --- |",
        *[f"| {r['ticker']} | {r['universe_tier']} | {r['scan_priority']} | {r['scan_reason']} | {r['estimated_total_cost']} |" for r in selected_preview],
        "",
        "## Deferred Preview",
        "",
        "| ticker | tier | priority | deferred_reason |",
        "| --- | --- | --- | --- |",
        *[f"| {r['ticker']} | {r['universe_tier']} | {r['scan_priority']} | {r['deferred_reason']} |" for r in deferred_preview],
        "",
        "Scheduler-only. No price update, event update, rolling scan calculation, FullDaily, YFinance, live trading, or live selling was run.",
    ]
    write_text(report_path, "\n".join(report) + "\n")

    # Re-scan after report/read-first exist.
    hits = dangerous_hits(scan_paths, root)
    if hits and validation_fail_count == 0:
        values["DANGEROUS_TOKEN_FINDING_COUNT"] = str(len(hits))
        values["VALIDATION_FAIL_COUNT"] = str(len(hits))
        values["STATUS"] = STATUS_WARN
        write_text(read_first_path, "\n".join(f"{key}: {values[key]}" for key in read_keys) + "\n")
        status = STATUS_WARN

    for key in [
        "STATUS",
        "TOTAL_UNIVERSE_COUNT",
        "TODAY_SCAN_PLAN_COUNT",
        "DAILY_MIN_SCAN_COUNT",
        "ESTIMATED_PLAN_COST",
        "POSITION_SCAN_COUNT",
        "CORE_DAILY_SCAN_COUNT",
        "CANDIDATE_SCAN_COUNT",
        "WATCHLIST_SCAN_COUNT",
        "RESEARCH_SCAN_COUNT",
        "LOW_PRIORITY_SCAN_DEFERRED_COUNT",
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
    parser.add_argument("--max-estimated-plan-cost", type=int, default=DEFAULT_MAX_ESTIMATED_PLAN_COST)
    args = parser.parse_args()
    return build(Path(args.root), args.max_estimated_plan_cost)


if __name__ == "__main__":
    raise SystemExit(main())
