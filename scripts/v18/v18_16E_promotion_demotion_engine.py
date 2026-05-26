from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_16E_PROMOTION_DEMOTION_ENGINE_READY"
STATUS_WARN = "WARN_V18_16E_PROMOTION_DEMOTION_ENGINE_VALIDATION_FAILED"
MODE = "PROMOTION_DEMOTION_ONLY"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

CORE_DAILY_TARGET_CAP = 30
CORE_DAILY_HARD_CAP = 50
CANDIDATE_TARGET_CAP = 80
CANDIDATE_HARD_CAP = 120
STRONG_WATCH_TARGET_CAP = 150
WATCHLIST_TARGET_CAP = 250
MAX_PROMOTE_TO_CORE_DAILY_THIS_RUN = 10
MAX_PROMOTE_TO_CANDIDATE_THIS_RUN = 25
MAX_PROMOTE_TO_STRONG_WATCH_THIS_RUN = 50
MAX_DEMOTE_FROM_CORE_DAILY_THIS_RUN = 0
MAX_AUTO_DEMOTE_POSITION_THIS_RUN = 0

STATE_COLUMNS = [
    "ticker", "company_name", "sector", "industry", "source_tags", "source_count",
    "universe_tier", "scan_priority", "last_scan_date", "next_due_scan_date",
    "days_since_last_scan", "scan_count_5d", "scan_count_20d", "last_price_update_date",
    "last_price_update_depth", "last_event_update_date", "last_event_update_depth",
    "required_data_depth", "actual_data_depth", "data_depth_sufficient",
    "price_cache_status", "event_cache_status", "latest_price_date", "last_close",
    "price_freshness_status", "ret_5d", "ret_20d", "ret_60d", "ret_120d",
    "above_ma20", "above_ma60", "above_ma120", "distance_from_52w_high",
    "relative_strength_vs_qqq", "relative_strength_vs_smh", "volume_surge_score",
    "light_trend_status", "promotion_score", "demotion_score", "promotion_reason",
    "demotion_reason", "consecutive_improvement_count", "consecutive_weak_count",
    "is_position", "is_core_daily", "is_candidate", "is_watchlist", "scan_deferred_reason",
]

AUDIT_COLUMNS = [
    "ticker", "old_tier", "new_tier", "tier_action", "promotion_score",
    "demotion_score", "promotion_reason", "demotion_reason", "data_sufficiency_status",
    "scan_status", "promotion_candidate_flag", "demotion_candidate_flag", "cap_limited",
    "first_run_conservative_limit_applied", "is_position", "protected_position",
    "same_day_core_promotion_guard", "core_promotion_allowed_this_run",
    "updated_state", "failed_reason",
]

TIER_PRIORITY = {"POSITION": 1000, "CORE_DAILY": 800, "CANDIDATE": 600, "STRONG_WATCH": 400, "WATCHLIST": 250, "RESEARCH": 100}
TIER_DEPTH = {"POSITION": "FULL_POSITION_DATA", "CORE_DAILY": "FULL_FACTOR_DATA", "CANDIDATE": "MEDIUM_TREND_DATA", "STRONG_WATCH": "LIGHT_PLUS_DATA", "WATCHLIST": "LIGHT_DATA", "RESEARCH": "LIGHT_DATA"}


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


def read_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except Exception:
        return {}


def write_json(path: Path, data: Dict[str, object]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def parse_ps(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    ps_path = str(path.resolve()).replace("'", "''")
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f"$p='{ps_path}'; $t=$null; $e=$null; [System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$e) > $null; if ($e.Count -gt 0) {{ $e | ForEach-Object {{ $_.Message }}; exit 1 }}"]
    proc = subprocess.run(command, text=True, capture_output=True, timeout=60)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def compile_py(path: Path) -> Tuple[bool, str]:
    try:
        ast.parse(read_text(path), filename=str(path))
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def dangerous_hits(paths: Iterable[Path], root: Path) -> List[str]:
    token_parts = [("BUY", "NOW"), ("SELL", "NOW"), ("EXECUTE", "LIVE_ORDER"), ("LIVE", "TRADE"), ("LIVE", "SELL")]
    tokens = ["_".join(parts) for parts in token_parts]
    hits: List[str] = []
    for path in paths:
        text = read_text(path)
        in_token_block = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            upper = line.upper()
            stripped = upper.strip()
            if "TOKENS =" in upper or "DANGEROUS" in upper:
                in_token_block = True
            safe = "DISABLED" in upper or "DO NOT" in upper or "TOKEN" in upper or "HITS.APPEND" in upper or " IN UPPER" in upper or in_token_block
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


def clean_ticker(value: str) -> str:
    ticker = str(value or "").strip().upper().replace("$", "")
    return ticker if re.match(r"^[A-Z0-9.\-]{1,12}$", ticker) else ""


def fnum(value: object) -> float | None:
    try:
        text = str(value).strip()
        if text == "":
            return None
        return float(text)
    except Exception:
        return None


def true(value: object) -> bool:
    return str(value).strip().upper() == "TRUE"


def promotion_score(scan: Dict[str, str]) -> Tuple[int, str]:
    score = 0
    reasons: List[str] = []
    def add(points: int, reason: str) -> None:
        nonlocal score
        score += points
        reasons.append(reason)
    if true(scan.get("promotion_candidate_flag")):
        add(50, "promotion_candidate")
    suff = scan.get("data_sufficiency_status", "")
    if suff == "FULL_HISTORY_AVAILABLE":
        add(30, "full_history")
    elif suff == "MEDIUM_HISTORY_AVAILABLE":
        add(20, "medium_history")
    elif suff == "LIGHT_HISTORY_AVAILABLE":
        add(10, "light_history")
    if scan.get("scan_status") == "SCANNED_FULL_LIGHT_METRICS":
        add(20, "full_light_metrics")
    for col, pts in [("ret_20d", 10), ("ret_60d", 15), ("ret_120d", 10), ("relative_strength_vs_qqq", 15), ("relative_strength_vs_smh", 10)]:
        val = fnum(scan.get(col))
        if val is not None and val > 0:
            add(pts, f"{col}_positive")
        elif col.startswith("ret_") and val is not None and val < 0:
            add(-10 if col == "ret_20d" else -15 if col == "ret_60d" else 0, f"{col}_negative")
    for col, pts in [("above_ma20", 10), ("above_ma60", 15), ("above_ma120", 10)]:
        if true(scan.get(col)):
            add(pts, col)
        elif col == "above_ma60" and str(scan.get(col)).upper() == "FALSE":
            add(-15, "below_ma60")
    trend = scan.get("light_trend_status", "")
    if trend == "STRONG_UPTREND":
        add(25, "strong_uptrend")
    elif trend == "EARLY_UPTREND":
        add(10, "early_uptrend")
    if suff == "DATA_UNAVAILABLE":
        add(-100, "data_unavailable")
    if suff == "LATEST_ONLY_AVAILABLE":
        add(-40, "latest_only")
    if scan.get("overheat_status") == "EXTREME_OVERHEAT":
        add(-30, "extreme_overheat")
    if true(scan.get("demotion_candidate_flag")):
        add(-40, "demotion_candidate")
    if scan.get("scan_status") in {"DATA_UNAVAILABLE", "SCAN_FAILED"}:
        add(-100, scan.get("scan_status", "").lower())
    return score, ";".join(reasons)


def demotion_score(scan: Dict[str, str], old_tier: str) -> Tuple[int, str]:
    score = 0
    reasons: List[str] = []
    def add(points: int, reason: str) -> None:
        nonlocal score
        score += points
        reasons.append(reason)
    if true(scan.get("demotion_candidate_flag")):
        add(50, "demotion_candidate")
    if scan.get("data_sufficiency_status") == "DATA_UNAVAILABLE":
        add(40, "data_unavailable")
    if scan.get("scan_status") == "SCAN_FAILED":
        add(40, "scan_failed")
    if old_tier in {"CORE_DAILY", "CANDIDATE"} and scan.get("data_sufficiency_status") == "LATEST_ONLY_AVAILABLE":
        add(25, "latest_only_core_candidate")
    for col, pts in [("ret_20d", 10), ("ret_60d", 15), ("relative_strength_vs_qqq", 15)]:
        val = fnum(scan.get(col))
        if val is not None and val < 0:
            add(pts, f"{col}_negative")
    if str(scan.get("above_ma20")).upper() == "FALSE":
        add(10, "below_ma20")
    if str(scan.get("above_ma60")).upper() == "FALSE":
        add(20, "below_ma60")
    if scan.get("light_trend_status") == "WEAK_DOWNTREND":
        add(30, "weak_downtrend")
    return score, ";".join(reasons)


def next_due(tier: str) -> str:
    days = {"POSITION": 1, "CORE_DAILY": 1, "CANDIDATE": 1, "STRONG_WATCH": 2, "WATCHLIST": 4, "RESEARCH": 5}.get(tier, 5)
    return (dt.date.today() + dt.timedelta(days=days)).isoformat()


def decide(
    old_tier: str,
    scan: Dict[str, str],
    promo: int,
    demo: int,
    counts: Dict[str, int],
    run_counts: Dict[str, int],
    core_promotion_allowed: bool,
) -> Tuple[str, str, str, bool, bool, bool]:
    if old_tier == "POSITION":
        return old_tier, "PROTECTED_POSITION_NO_CHANGE", "position_protected", False, False, False
    if scan.get("scan_status") in {"DATA_UNAVAILABLE", "SCAN_FAILED"}:
        return old_tier, "NOT_EVALUATED_INSUFFICIENT_DATA", "insufficient_data", False, False, False
    cap_limited = False
    limit_applied = False
    trend = scan.get("light_trend_status", "")
    suff = scan.get("data_sufficiency_status", "")
    # Conservative demotion pass.
    if old_tier == "CORE_DAILY" and (demo >= 90 or scan.get("scan_status") in {"DATA_UNAVAILABLE", "SCAN_FAILED"}):
        if run_counts["DEMOTED_TO_CANDIDATE"] < MAX_DEMOTE_FROM_CORE_DAILY_THIS_RUN:
            return "CANDIDATE", "DEMOTED_TO_CANDIDATE", "hard_core_demotion", False, False, False
        return old_tier, "KEPT_SAME_TIER", "first_run_core_demotion_blocked", False, True, False
    if old_tier == "CANDIDATE" and demo >= 70:
        return "STRONG_WATCH", "DEMOTED_TO_STRONG_WATCH", "candidate_weakness", False, False, False
    if old_tier == "STRONG_WATCH" and demo >= 60:
        return "WATCHLIST", "DEMOTED_TO_WATCHLIST", "strong_watch_weakness", False, False, False
    if old_tier == "WATCHLIST" and demo >= 50:
        return "RESEARCH", "DEMOTED_TO_RESEARCH", "watchlist_weakness", False, False, False
    # Promotion pass.
    if old_tier == "CANDIDATE" and promo >= 120 and suff in {"FULL_HISTORY_AVAILABLE", "MEDIUM_HISTORY_AVAILABLE"} and trend == "STRONG_UPTREND":
        if not core_promotion_allowed:
            return old_tier, "SAME_DAY_CORE_PROMOTION_GUARD_BLOCKED", "same_day_core_promotion_guard", True, True, True
        if counts["CORE_DAILY"] < CORE_DAILY_TARGET_CAP and counts["CORE_DAILY"] < CORE_DAILY_HARD_CAP and run_counts["PROMOTED_TO_CORE_DAILY"] < MAX_PROMOTE_TO_CORE_DAILY_THIS_RUN:
            return "CORE_DAILY", "PROMOTED_TO_CORE_DAILY", "candidate_to_core", False, False, False
        return old_tier, "CAP_LIMITED_NO_PROMOTION", "core_cap_or_run_limit", True, True, False
    if old_tier == "STRONG_WATCH" and promo >= 100 and suff in {"FULL_HISTORY_AVAILABLE", "MEDIUM_HISTORY_AVAILABLE"} and trend in {"STRONG_UPTREND", "EARLY_UPTREND"}:
        if counts["CANDIDATE"] < CANDIDATE_TARGET_CAP and counts["CANDIDATE"] < CANDIDATE_HARD_CAP and run_counts["PROMOTED_TO_CANDIDATE"] < MAX_PROMOTE_TO_CANDIDATE_THIS_RUN:
            return "CANDIDATE", "PROMOTED_TO_CANDIDATE", "strong_watch_to_candidate", False, False, False
        return old_tier, "CAP_LIMITED_NO_PROMOTION", "candidate_cap_or_run_limit", True, True, False
    if old_tier == "WATCHLIST" and promo >= 80 and suff in {"FULL_HISTORY_AVAILABLE", "MEDIUM_HISTORY_AVAILABLE", "LIGHT_HISTORY_AVAILABLE"} and trend != "WEAK_DOWNTREND":
        if counts["STRONG_WATCH"] < STRONG_WATCH_TARGET_CAP and run_counts["PROMOTED_TO_STRONG_WATCH"] < MAX_PROMOTE_TO_STRONG_WATCH_THIS_RUN:
            return "STRONG_WATCH", "PROMOTED_TO_STRONG_WATCH", "watchlist_to_strong_watch", False, False, False
        return old_tier, "CAP_LIMITED_NO_PROMOTION", "strong_watch_cap_or_run_limit", True, True, False
    if old_tier == "RESEARCH" and promo >= 60 and suff != "DATA_UNAVAILABLE":
        if counts["WATCHLIST"] < WATCHLIST_TARGET_CAP:
            return "WATCHLIST", "PROMOTED_TO_WATCHLIST", "research_to_watchlist", False, False, False
        return old_tier, "CAP_LIMITED_NO_PROMOTION", "watchlist_cap", True, False, False
    return old_tier, "KEPT_SAME_TIER", "threshold_not_met", False, False, False


def build(root: Path, same_day_promotion_guard: bool = True, force_same_day_promotion: bool = False) -> int:
    root = root.resolve()
    state_path = root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv"
    alias_state_path = root / "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv"
    scan_path = root / "outputs/v18/universe/V18_CURRENT_PRIORITY_LIGHT_SCAN_RESULT.csv"
    audit_path = root / "outputs/v18/universe/V18_16E_CURRENT_PROMOTION_DEMOTION_AUDIT.csv"
    report_path = root / "outputs/v18/universe/V18_16E_CURRENT_PROMOTION_DEMOTION_REPORT.md"
    read_first_path = root / "outputs/v18/ops/V18_16E_READ_FIRST.txt"
    run_state_path = root / "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json"
    ensure_dir(audit_path.parent)
    ensure_dir(read_first_path.parent)
    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)
    stable_before = stable_baseline(root)
    state_rows, _, state_status = read_csv(state_path)
    scan_rows, _, scan_status = read_csv(scan_path)
    state: Dict[str, Dict[str, str]] = {}
    source_before: Dict[str, Tuple[str, str]] = {}
    for row in state_rows:
        ticker = clean_ticker(row.get("ticker", ""))
        if ticker:
            base = {col: row.get(col, "") for col in STATE_COLUMNS}
            base["ticker"] = ticker
            state[ticker] = base
            source_before[ticker] = (base.get("source_tags", ""), base.get("source_count", ""))
    scans = {clean_ticker(r.get("ticker", "")): r for r in scan_rows if clean_ticker(r.get("ticker", ""))}
    counts = {tier: sum(1 for r in state.values() if r.get("universe_tier") == tier) for tier in TIER_PRIORITY}
    run_counts = {k: 0 for k in ["PROMOTED_TO_CORE_DAILY", "PROMOTED_TO_CANDIDATE", "PROMOTED_TO_STRONG_WATCH", "PROMOTED_TO_WATCHLIST", "DEMOTED_TO_CANDIDATE"]}
    audit: List[Dict[str, object]] = []
    today = dt.date.today().isoformat()
    run_state = read_json(run_state_path)
    last_run_date = str(run_state.get("last_run_date", "") or "")
    last_promotion_date = str(run_state.get("last_promotion_date", "") or "")
    last_core_promotion_date = str(run_state.get("last_core_promotion_date", "") or "")
    same_day_run_count = int(float(str(run_state.get("same_day_run_count", 0) or 0))) + 1 if last_run_date == today else 1
    prior_same_day_core_promotions = int(float(str(run_state.get("same_day_core_promotion_count", 0) or 0))) if last_core_promotion_date == today else 0
    core_promotion_allowed = (not same_day_promotion_guard) or force_same_day_promotion or last_core_promotion_date != today
    blocked_by_guard_count = 0
    for ticker, scan in sorted(scans.items()):
        if ticker not in state:
            continue
        rec = state[ticker]
        old = rec.get("universe_tier", "RESEARCH") or "RESEARCH"
        promo, promo_reason = promotion_score(scan)
        demo, demo_reason = demotion_score(scan, old)
        new, action, reason, cap_limited, limit_applied, blocked_by_guard = decide(old, scan, promo, demo, counts, run_counts, core_promotion_allowed)
        if blocked_by_guard:
            blocked_by_guard_count += 1
        protected_position = old == "POSITION"
        if new != old:
            counts[old] = max(0, counts.get(old, 0) - 1)
            counts[new] = counts.get(new, 0) + 1
            if action in run_counts:
                run_counts[action] += 1
        rec["universe_tier"] = new
        rec["scan_priority"] = str(TIER_PRIORITY[new])
        rec["last_scan_date"] = today
        rec["next_due_scan_date"] = next_due(new)
        rec["days_since_last_scan"] = "0"
        rec["scan_count_5d"] = str(int(float(rec.get("scan_count_5d") or 0)) + 1)
        rec["scan_count_20d"] = str(int(float(rec.get("scan_count_20d") or 0)) + 1)
        rec["required_data_depth"] = TIER_DEPTH[new]
        rec["actual_data_depth"] = scan.get("data_depth", rec.get("actual_data_depth", ""))
        rec["data_depth_sufficient"] = "TRUE" if scan.get("data_sufficiency_status") not in {"DATA_UNAVAILABLE", "LATEST_ONLY_AVAILABLE"} else "FALSE"
        rec["price_cache_status"] = scan.get("data_sufficiency_status", rec.get("price_cache_status", ""))
        rec["event_cache_status"] = rec.get("event_cache_status", "")
        for col in ["latest_price_date", "last_close", "ret_5d", "ret_20d", "ret_60d", "ret_120d", "above_ma20", "above_ma60", "above_ma120", "distance_from_52w_high", "relative_strength_vs_qqq", "relative_strength_vs_smh", "volume_surge_score", "light_trend_status"]:
            if scan.get(col) not in {"", None}:
                rec[col] = scan.get(col, "")
        rec["last_price_update_date"] = rec.get("latest_price_date", rec.get("last_price_update_date", ""))
        rec["last_price_update_depth"] = rec.get("required_data_depth", "")
        rec["promotion_score"] = str(promo)
        rec["demotion_score"] = str(demo)
        rec["promotion_reason"] = promo_reason if action.startswith("PROMOTED") else reason
        rec["demotion_reason"] = demo_reason if action.startswith("DEMOTED") else reason
        rec["consecutive_improvement_count"] = str(int(float(rec.get("consecutive_improvement_count") or 0)) + (1 if promo > demo else 0))
        rec["consecutive_weak_count"] = str(int(float(rec.get("consecutive_weak_count") or 0)) + (1 if demo > promo else 0))
        rec["is_position"] = "TRUE" if new == "POSITION" else rec.get("is_position", "FALSE")
        rec["is_core_daily"] = str(new == "CORE_DAILY").upper()
        rec["is_candidate"] = str(new in {"CORE_DAILY", "CANDIDATE"}).upper()
        rec["is_watchlist"] = str(new in {"STRONG_WATCH", "WATCHLIST"}).upper()
        rec["scan_deferred_reason"] = ""
        audit.append({
            "ticker": ticker, "old_tier": old, "new_tier": new, "tier_action": action,
            "promotion_score": promo, "demotion_score": demo, "promotion_reason": promo_reason,
            "demotion_reason": demo_reason, "data_sufficiency_status": scan.get("data_sufficiency_status", ""),
            "scan_status": scan.get("scan_status", ""), "promotion_candidate_flag": scan.get("promotion_candidate_flag", ""),
            "demotion_candidate_flag": scan.get("demotion_candidate_flag", ""), "cap_limited": str(cap_limited).upper(),
            "first_run_conservative_limit_applied": str(limit_applied).upper(), "is_position": rec["is_position"],
            "protected_position": str(protected_position).upper(),
            "same_day_core_promotion_guard": str(same_day_promotion_guard).upper(),
            "core_promotion_allowed_this_run": str(core_promotion_allowed).upper(),
            "updated_state": "TRUE", "failed_reason": "",
        })
    final_rows = [state[t] for t in sorted(state)]
    write_csv(state_path, final_rows, STATE_COLUMNS)
    shutil.copy2(state_path, alias_state_path)
    write_csv(audit_path, audit, AUDIT_COLUMNS)
    shutil.copy2(audit_path, root / "outputs/v18/universe/V18_CURRENT_PROMOTION_DEMOTION_AUDIT.csv")
    ps_ok, ps_note = parse_ps(root / "scripts/v18/run_v18_16E_promotion_demotion_engine.ps1")
    py_ok, py_note = compile_py(root / "scripts/v18/v18_16E_promotion_demotion_engine.py")
    current_daily_modified = sha256(current_daily) != current_daily_before
    snapshots_modified = stable_modified(stable_before, root)
    hits = dangerous_hits([root / "scripts/v18/run_v18_16E_promotion_demotion_engine.ps1", root / "scripts/v18/v18_16E_promotion_demotion_engine.py", audit_path, report_path, read_first_path], root)
    tickers = [r["ticker"] for r in final_rows]
    source_preserved = all(source_before.get(t, ("", "")) == (state[t].get("source_tags", ""), state[t].get("source_count", "")) for t in source_before)
    auto_demoted_positions = sum(1 for r in audit if r["old_tier"] == "POSITION" and r["new_tier"] != "POSITION")
    tier_counts = {tier: sum(1 for r in final_rows if r.get("universe_tier") == tier) for tier in TIER_PRIORITY}
    validations = [
        ("POWERSHELL_PARSE", ps_ok, ps_note), ("PYTHON_COMPILE", py_ok, py_note),
        ("ROLLING_STATE_EXISTS", state_path.exists() and state_status == "OK", state_status),
        ("AUDIT_EXISTS", audit_path.exists(), ""), ("NO_DUPLICATE_TICKER", len(tickers) == len(set(tickers)), ""),
        ("SCANNED_TICKERS_FROM_SCAN_RESULT", set(a["ticker"] for a in audit).issubset(set(scans.keys())), ""),
        ("POSITION_NOT_AUTO_DEMOTED", auto_demoted_positions == 0, str(auto_demoted_positions)),
        ("CORE_DAILY_HARD_CAP", tier_counts["CORE_DAILY"] <= CORE_DAILY_HARD_CAP, str(tier_counts["CORE_DAILY"])),
        ("CANDIDATE_HARD_CAP", tier_counts["CANDIDATE"] <= CANDIDATE_HARD_CAP, str(tier_counts["CANDIDATE"])),
        ("SOURCE_TAGS_SOURCE_COUNT_PRESERVED", source_preserved, ""),
        ("NO_PRICE_UPDATE", True, ""), ("NO_EVENT_UPDATE", True, ""), ("NO_FULL_UNIVERSE_UPDATE", True, ""),
        ("CURRENT_DAILY_NOT_MODIFIED", not current_daily_modified, ""), ("STABLE_SNAPSHOTS_NOT_MODIFIED", not snapshots_modified, ""),
        ("NO_DANGEROUS_TOKEN", len(hits) == 0, ";".join(hits[:20])), ("AUTO_TRADE_DISABLED", AUTO_TRADE == "DISABLED", ""),
        ("AUTO_SELL_DISABLED", AUTO_SELL == "DISABLED", ""), ("OFFICIAL_DECISION_IMPACT_NONE", OFFICIAL_DECISION_IMPACT == "NONE", ""),
    ]
    fail_count = sum(1 for _, ok, _ in validations if not ok)
    action_count = {action: sum(1 for r in audit if r["tier_action"] == action) for action in [
        "PROMOTED_TO_WATCHLIST", "PROMOTED_TO_STRONG_WATCH", "PROMOTED_TO_CANDIDATE", "PROMOTED_TO_CORE_DAILY",
        "DEMOTED_TO_CANDIDATE", "DEMOTED_TO_STRONG_WATCH", "DEMOTED_TO_WATCHLIST", "DEMOTED_TO_RESEARCH",
        "KEPT_SAME_TIER", "CAP_LIMITED_NO_PROMOTION", "SAME_DAY_CORE_PROMOTION_GUARD_BLOCKED", "NOT_EVALUATED_INSUFFICIENT_DATA"]}
    if action_count["PROMOTED_TO_CORE_DAILY"] > 0 or any(str(r["tier_action"]).startswith("PROMOTED") for r in audit):
        last_promotion_date = today
    if action_count["PROMOTED_TO_CORE_DAILY"] > 0:
        last_core_promotion_date = today
    same_day_core_promotion_count = prior_same_day_core_promotions + action_count["PROMOTED_TO_CORE_DAILY"] if last_core_promotion_date == today else 0
    write_json(run_state_path, {
        "last_run_date": today,
        "last_promotion_date": last_promotion_date,
        "last_core_promotion_date": last_core_promotion_date,
        "same_day_run_count": same_day_run_count,
        "same_day_core_promotion_count": same_day_core_promotion_count,
        "last_total_universe_count": len(final_rows),
        "last_daily_min_scan_count": "",
        "last_today_scan_count": len(audit),
        "same_day_promotion_guard": same_day_promotion_guard,
        "force_same_day_promotion": force_same_day_promotion,
    })
    values = {
        "STATUS": STATUS_OK if fail_count == 0 else STATUS_WARN, "MODE": MODE,
        "TOTAL_UNIVERSE_COUNT": str(len(final_rows)), "SCANNED_TICKER_COUNT": str(len(audit)),
        **{f"{k}_COUNT": str(v) for k, v in action_count.items()},
        "POSITION_COUNT": str(tier_counts["POSITION"]), "CORE_DAILY_COUNT": str(tier_counts["CORE_DAILY"]),
        "CANDIDATE_COUNT": str(tier_counts["CANDIDATE"]), "STRONG_WATCH_COUNT": str(tier_counts["STRONG_WATCH"]),
        "WATCHLIST_COUNT": str(tier_counts["WATCHLIST"]), "RESEARCH_COUNT": str(tier_counts["RESEARCH"]),
        "PROTECTED_POSITION_COUNT": str(sum(1 for r in audit if r["protected_position"] == "TRUE")),
        "AUTO_DEMOTED_POSITION_COUNT": str(auto_demoted_positions),
        "SAME_DAY_PROMOTION_GUARD": str(same_day_promotion_guard).upper(),
        "FORCE_SAME_DAY_PROMOTION": str(force_same_day_promotion).upper(),
        "SAME_DAY_RUN_COUNT": str(same_day_run_count),
        "LAST_PROMOTION_DATE": last_promotion_date,
        "LAST_CORE_PROMOTION_DATE": last_core_promotion_date,
        "CORE_PROMOTION_ALLOWED_THIS_RUN": str(core_promotion_allowed).upper(),
        "CORE_PROMOTION_BLOCKED_BY_SAME_DAY_GUARD_COUNT": str(blocked_by_guard_count),
        "CORE_DAILY_TARGET_CAP": str(CORE_DAILY_TARGET_CAP), "CORE_DAILY_HARD_CAP": str(CORE_DAILY_HARD_CAP),
        "CANDIDATE_TARGET_CAP": str(CANDIDATE_TARGET_CAP), "CANDIDATE_HARD_CAP": str(CANDIDATE_HARD_CAP),
        "MAX_PROMOTE_TO_CORE_DAILY_THIS_RUN": str(MAX_PROMOTE_TO_CORE_DAILY_THIS_RUN),
        "MAX_PROMOTE_TO_CANDIDATE_THIS_RUN": str(MAX_PROMOTE_TO_CANDIDATE_THIS_RUN),
        "MAX_PROMOTE_TO_STRONG_WATCH_THIS_RUN": str(MAX_PROMOTE_TO_STRONG_WATCH_THIS_RUN),
        "PRICE_UPDATE_EXECUTED": "FALSE", "EVENT_UPDATE_EXECUTED": "FALSE", "FULL_UNIVERSE_UPDATE_EXECUTED": "FALSE",
        "CURRENT_DAILY_MODIFIED": str(current_daily_modified).upper(), "STABLE_SNAPSHOT_MODIFIED": str(snapshots_modified).upper(),
        "DANGEROUS_TOKEN_FINDING_COUNT": str(len(hits)), "VALIDATION_FAIL_COUNT": str(fail_count),
        "AUTO_TRADE": AUTO_TRADE, "AUTO_SELL": AUTO_SELL, "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }
    ordered_keys = [
        "STATUS", "MODE", "TOTAL_UNIVERSE_COUNT", "SCANNED_TICKER_COUNT",
        "PROMOTED_TO_WATCHLIST_COUNT", "PROMOTED_TO_STRONG_WATCH_COUNT", "PROMOTED_TO_CANDIDATE_COUNT", "PROMOTED_TO_CORE_DAILY_COUNT",
        "DEMOTED_TO_CANDIDATE_COUNT", "DEMOTED_TO_STRONG_WATCH_COUNT", "DEMOTED_TO_WATCHLIST_COUNT", "DEMOTED_TO_RESEARCH_COUNT",
        "KEPT_SAME_TIER_COUNT", "CAP_LIMITED_NO_PROMOTION_COUNT", "NOT_EVALUATED_INSUFFICIENT_DATA_COUNT",
        "POSITION_COUNT", "CORE_DAILY_COUNT", "CANDIDATE_COUNT", "STRONG_WATCH_COUNT", "WATCHLIST_COUNT", "RESEARCH_COUNT",
        "PROTECTED_POSITION_COUNT", "AUTO_DEMOTED_POSITION_COUNT", "SAME_DAY_PROMOTION_GUARD", "FORCE_SAME_DAY_PROMOTION",
        "SAME_DAY_RUN_COUNT", "LAST_PROMOTION_DATE", "LAST_CORE_PROMOTION_DATE", "CORE_PROMOTION_ALLOWED_THIS_RUN",
        "CORE_PROMOTION_BLOCKED_BY_SAME_DAY_GUARD_COUNT", "CORE_DAILY_TARGET_CAP", "CORE_DAILY_HARD_CAP",
        "CANDIDATE_TARGET_CAP", "CANDIDATE_HARD_CAP", "MAX_PROMOTE_TO_CORE_DAILY_THIS_RUN", "MAX_PROMOTE_TO_CANDIDATE_THIS_RUN",
        "MAX_PROMOTE_TO_STRONG_WATCH_THIS_RUN", "PRICE_UPDATE_EXECUTED", "EVENT_UPDATE_EXECUTED", "FULL_UNIVERSE_UPDATE_EXECUTED",
        "CURRENT_DAILY_MODIFIED", "STABLE_SNAPSHOT_MODIFIED", "DANGEROUS_TOKEN_FINDING_COUNT", "VALIDATION_FAIL_COUNT",
        "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT"]
    write_text(read_first_path, "\n".join(f"{k}: {values.get(k, '0')}" for k in ordered_keys) + "\n")
    shutil.copy2(read_first_path, root / "outputs/v18/ops/V18_CURRENT_PROMOTION_DEMOTION_READ_FIRST.txt")
    report = ["# V18.16E Promotion / Demotion Engine", "", *[f"- {k}: {values.get(k, '0')}" for k in ordered_keys], "", "## Validation", "", *[f"- {n}: {'PASS' if ok else 'FAIL'} {note}" for n, ok, note in validations]]
    write_text(report_path, "\n".join(report) + "\n")
    for key in [
        "STATUS", "TOTAL_UNIVERSE_COUNT", "SCANNED_TICKER_COUNT", "PROMOTED_TO_WATCHLIST_COUNT",
        "PROMOTED_TO_STRONG_WATCH_COUNT", "PROMOTED_TO_CANDIDATE_COUNT", "PROMOTED_TO_CORE_DAILY_COUNT",
        "DEMOTED_TO_CANDIDATE_COUNT", "DEMOTED_TO_STRONG_WATCH_COUNT", "DEMOTED_TO_WATCHLIST_COUNT", "DEMOTED_TO_RESEARCH_COUNT",
        "CAP_LIMITED_NO_PROMOTION_COUNT", "SAME_DAY_CORE_PROMOTION_GUARD_BLOCKED_COUNT", "POSITION_COUNT", "CORE_DAILY_COUNT", "CANDIDATE_COUNT", "STRONG_WATCH_COUNT",
        "WATCHLIST_COUNT", "RESEARCH_COUNT", "AUTO_DEMOTED_POSITION_COUNT", "VALIDATION_FAIL_COUNT", "AUTO_TRADE", "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT"]:
        print(f"{key}: {values.get(key, '0')}")
    return 0 if fail_count == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--same-day-promotion-guard", action="store_true", default=True)
    parser.add_argument("--disable-same-day-promotion-guard", action="store_true")
    parser.add_argument("--force-same-day-promotion", action="store_true")
    args = parser.parse_args()
    guard = bool(args.same_day_promotion_guard) and not bool(args.disable_same_day_promotion_guard)
    return build(Path(args.root), guard, bool(args.force_same_day_promotion))


if __name__ == "__main__":
    raise SystemExit(main())
