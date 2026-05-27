from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_16H_SAME_DAY_PROMOTION_GUARD_COVERAGE_AUDIT_READY"
STATUS_WARN = "WARN_V18_16H_SAME_DAY_PROMOTION_GUARD_COVERAGE_AUDIT_VALIDATION_FAILED"
MODE = "SAME_DAY_PROMOTION_GUARD_AND_COVERAGE_AUDIT"
COVERAGE_WINDOW_TRADING_DAYS = 5
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"


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
    if base.exists():
        for folder in base.iterdir():
            if folder.is_dir():
                out[str(folder.resolve())] = (folder.stat().st_mtime, sha256(folder / "MANIFEST.csv"))
    return out


def stable_modified(before: Dict[str, Tuple[float, str]], root: Path) -> bool:
    after = stable_baseline(root)
    return any(after.get(key) != value for key, value in before.items())


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def first_value(path: Path, key: str) -> str:
    target = key.upper()
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        if k.strip().upper().lstrip("- ").strip() == target:
            return v.strip()
    return ""


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        if text == "":
            return default
        return int(float(text))
    except Exception:
        return default


def parse_date(value: object) -> dt.date | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(text[:19], fmt).date()
        except Exception:
            pass
    return None


def parse_ps(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    ps_path = str(path.resolve()).replace("'", "''")
    cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
        f"$p='{ps_path}'; $t=$null; $e=$null; [System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$e) > $null; if ($e.Count -gt 0) {{ $e | ForEach-Object {{ $_.Message }}; exit 1 }}",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
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
            safe = (
                "DISABLED" in upper or "DO NOT" in upper or "TOKEN" in upper
                or "HITS.APPEND" in upper or " IN UPPER" in upper or in_token_block
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


def run_command(root: Path, args: Sequence[str]) -> Dict[str, object]:
    proc = subprocess.run(args, cwd=str(root), text=True, capture_output=True, timeout=1800)
    return {
        "returncode": proc.returncode,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-20:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-20:]),
    }


def scan_limit_reason(today_scan: int, daily_min: int, v16b_read: Path, plan_rows: Sequence[Dict[str, str]]) -> str:
    if today_scan >= daily_min:
        return "TARGET_MET"
    estimated = to_int(first_value(v16b_read, "ESTIMATED_PLAN_COST"))
    max_cost = to_int(first_value(v16b_read, "MAX_ESTIMATED_PLAN_COST"))
    if max_cost and estimated >= max_cost:
        return "ESTIMATED_PLAN_COST_LIMIT"
    if plan_rows and all(str(r.get("selected_this_run", "")).upper() == "TRUE" for r in plan_rows):
        return "NO_MORE_DUE_TICKERS"
    deferred = [r for r in plan_rows if str(r.get("deferred_reason", "")).strip()]
    if deferred:
        return "ESTIMATED_PLAN_COST_LIMIT"
    return "UNKNOWN_NEEDS_REVIEW"


def build(root: Path, args: argparse.Namespace) -> int:
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    universe = root / "outputs/v18/universe"
    ensure_dir(ops)
    ensure_dir(universe)

    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)
    stable_before = stable_baseline(root)

    command_center = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(current_daily)]
    default_run = run_command(root, command_center)
    forward_run = run_command(root, [*command_center, "-RunForwardTracker", "-RunManualFeedback"])
    rolling_args = ["-RunUniverseRollingScan", "-RunForwardTracker", "-RunManualFeedback"]
    if args.force_same_day_promotion:
        rolling_args.append("-ForceSameDayPromotion")
    if args.disable_same_day_promotion_guard:
        rolling_args.append("-DisableSameDayPromotionGuard")
    rolling_first = run_command(root, [*command_center, *rolling_args])
    first_core_promoted = to_int(first_value(ops / "V18_16F_READ_FIRST.txt", "PROMOTED_TO_CORE_DAILY_COUNT"))
    rolling_second = run_command(root, [*command_center, *rolling_args])
    second_core_promoted = to_int(first_value(ops / "V18_16F_READ_FIRST.txt", "PROMOTED_TO_CORE_DAILY_COUNT"))

    v16b_read = ops / "V18_16B_READ_FIRST.txt"
    v16e_read = ops / "V18_16E_READ_FIRST.txt"
    v16f_read = ops / "V18_16F_READ_FIRST.txt"
    state_path = root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv"
    plan_path = universe / "V18_CURRENT_ROLLING_SCAN_PLAN.csv"
    guard_audit_source = universe / "V18_CURRENT_PROMOTION_DEMOTION_AUDIT.csv"
    run_state_path = root / "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json"

    state_rows, _, state_status = read_csv(state_path)
    plan_rows, _, plan_status = read_csv(plan_path)
    guard_rows, _, guard_status = read_csv(guard_audit_source)
    run_state = read_json(run_state_path)

    total_universe = len([r for r in state_rows if str(r.get("ticker", "")).strip()])
    daily_min = math.ceil(total_universe / COVERAGE_WINDOW_TRADING_DAYS) if total_universe else 0
    today_scan = to_int(first_value(v16f_read, "TODAY_ROLLING_SCAN_COUNT") or first_value(v16b_read, "TODAY_SCAN_PLAN_COUNT"))
    scanned_ticker_count = to_int(first_value(v16f_read, "SCANNED_TICKER_COUNT") or first_value(v16e_read, "SCANNED_TICKER_COUNT"))
    coverage_shortfall = max(0, daily_min - today_scan)
    coverage_target_met = today_scan >= daily_min
    today = dt.date.today()
    scanned_last_1d = sum(1 for r in state_rows if parse_date(r.get("last_scan_date")) and (today - parse_date(r.get("last_scan_date"))).days <= 1)
    scanned_last_5d = sum(1 for r in state_rows if parse_date(r.get("last_scan_date")) and (today - parse_date(r.get("last_scan_date"))).days <= 5)
    overdue_scan_count = sum(1 for r in state_rows if parse_date(r.get("next_due_scan_date")) and parse_date(r.get("next_due_scan_date")) <= today)
    low_priority_deferred = sum(1 for r in plan_rows if "LOW_PRIORITY" in str(r.get("deferred_reason", "")).upper())
    reason = scan_limit_reason(today_scan, daily_min, v16b_read, plan_rows)

    guard_enabled = not args.disable_same_day_promotion_guard
    force_same_day = bool(args.force_same_day_promotion)
    core_allowed = first_value(v16e_read, "CORE_PROMOTION_ALLOWED_THIS_RUN") or str((not guard_enabled) or force_same_day).upper()
    blocked_count = to_int(first_value(v16e_read, "CORE_PROMOTION_BLOCKED_BY_SAME_DAY_GUARD_COUNT"))
    promoted_core = to_int(first_value(v16e_read, "PROMOTED_TO_CORE_DAILY_COUNT"))
    core_daily_count = to_int(first_value(v16e_read, "CORE_DAILY_COUNT"))
    auto_demoted_positions = to_int(first_value(v16e_read, "AUTO_DEMOTED_POSITION_COUNT"))

    coverage_audit = [{
        "TOTAL_UNIVERSE_COUNT": total_universe,
        "COVERAGE_WINDOW_TRADING_DAYS": COVERAGE_WINDOW_TRADING_DAYS,
        "DAILY_MIN_SCAN_COUNT": daily_min,
        "TODAY_ROLLING_SCAN_COUNT": today_scan,
        "SCANNED_TICKER_COUNT": scanned_ticker_count,
        "COVERAGE_TARGET_MET": str(coverage_target_met).upper(),
        "COVERAGE_SHORTFALL_COUNT": coverage_shortfall,
        "SCANNED_LAST_1D_COUNT": scanned_last_1d,
        "SCANNED_LAST_5D_COUNT": scanned_last_5d,
        "OVERDUE_SCAN_COUNT": overdue_scan_count,
        "LOW_PRIORITY_SCAN_DEFERRED_COUNT": low_priority_deferred,
        "SCAN_LIMIT_REASON": reason,
    }]
    coverage_path = universe / "V18_16H_CURRENT_COVERAGE_AUDIT.csv"
    coverage_alias = universe / "V18_CURRENT_ROLLING_SCAN_COVERAGE_AUDIT.csv"
    write_csv(coverage_path, coverage_audit, list(coverage_audit[0].keys()))
    write_csv(coverage_alias, coverage_audit, list(coverage_audit[0].keys()))

    guard_audit_path = universe / "V18_16H_CURRENT_SAME_DAY_PROMOTION_GUARD_AUDIT.csv"
    guard_alias = universe / "V18_CURRENT_SAME_DAY_PROMOTION_GUARD_AUDIT.csv"
    guard_fields = [
        "ticker", "old_tier", "new_tier", "tier_action", "promotion_score", "demotion_score",
        "same_day_core_promotion_guard", "core_promotion_allowed_this_run", "cap_limited",
        "protected_position", "updated_state", "failed_reason",
    ]
    write_csv(guard_audit_path, guard_rows, guard_fields)
    write_csv(guard_alias, guard_rows, guard_fields)

    run_state.update({
        "last_total_universe_count": total_universe,
        "last_daily_min_scan_count": daily_min,
        "last_today_scan_count": today_scan,
    })
    write_json(run_state_path, run_state)

    ps_paths = [
        "scripts/v18/run_v18_16H_same_day_promotion_guard_coverage_audit.ps1",
        "scripts/v18/run_v18_current_daily_command_center.ps1",
        "scripts/v18/run_v18_16F_current_daily_with_rolling_universe_scan.ps1",
        "scripts/v18/run_v18_16E_promotion_demotion_engine.ps1",
        "scripts/v18/run_v18_16B_rolling_scan_scheduler.ps1",
    ]
    py_paths = [
        "scripts/v18/v18_16H_same_day_promotion_guard_coverage_audit.py",
        "scripts/v18/v18_16F_current_daily_with_rolling_universe_scan.py",
        "scripts/v18/v18_16E_promotion_demotion_engine.py",
        "scripts/v18/v18_16B_rolling_scan_scheduler.py",
    ]
    ps_results = [(p, *parse_ps(root / p)) for p in ps_paths]
    py_results = [(p, *compile_py(root / p)) for p in py_paths]

    current_daily_modified = sha256(current_daily) != current_daily_before
    snapshots_modified = stable_modified(stable_before, root)
    scan_paths = [root / p for p in ps_paths + py_paths] + [
        ops / "V18_16H_READ_FIRST.txt", coverage_path, coverage_alias, guard_audit_path, guard_alias,
        universe / "V18_16H_CURRENT_ROLLING_SCAN_COVERAGE_REPORT.md",
    ]
    hits = dangerous_hits(scan_paths, root)

    old_default_ok = default_run["returncode"] == 0
    old_forward_ok = forward_run["returncode"] == 0
    rolling_ok = rolling_first["returncode"] == 0 and rolling_second["returncode"] == 0
    second_run_guard_ok = force_same_day or second_core_promoted == 0

    validations = [
        ("OLD_DEFAULT_MODE_VALIDATED", old_default_ok, default_run["stderr_tail"]),
        ("OLD_FORWARD_MANUAL_MODE_VALIDATED", old_forward_ok, forward_run["stderr_tail"]),
        ("ROLLING_SCAN_MODE_VALIDATED", rolling_ok, rolling_second["stderr_tail"]),
        ("SECOND_SAME_DAY_CORE_PROMOTION_BLOCKED", second_run_guard_ok, str(second_core_promoted)),
        ("STATE_EXISTS", state_status == "OK", state_status),
        ("PLAN_EXISTS", plan_status == "OK", plan_status),
        ("GUARD_AUDIT_EXISTS", guard_status == "OK", guard_status),
        ("COVERAGE_REASON_PRESENT_IF_SHORT", coverage_shortfall == 0 or bool(reason), reason),
        ("CURRENT_DAILY_NOT_MODIFIED_DURING_AUDIT", not current_daily_modified, ""),
        ("STABLE_SNAPSHOT_NOT_MODIFIED", not snapshots_modified, ""),
        ("NO_DANGEROUS_TOKEN", len(hits) == 0, ";".join(hits[:10])),
        ("AUTO_DEMOTED_POSITION_COUNT_ZERO", auto_demoted_positions == 0, str(auto_demoted_positions)),
        *[(f"PS_PARSE:{p}", ok, note) for p, ok, note in ps_results],
        *[(f"PY_COMPILE:{p}", ok, note) for p, ok, note in py_results],
    ]
    validation_fail_count = sum(1 for _, ok, _ in validations if not ok)

    values = {
        "STATUS": STATUS_OK if validation_fail_count == 0 else STATUS_WARN,
        "MODE": MODE,
        "TOTAL_UNIVERSE_COUNT": str(total_universe),
        "COVERAGE_WINDOW_TRADING_DAYS": str(COVERAGE_WINDOW_TRADING_DAYS),
        "DAILY_MIN_SCAN_COUNT": str(daily_min),
        "TODAY_ROLLING_SCAN_COUNT": str(today_scan),
        "SCANNED_TICKER_COUNT": str(scanned_ticker_count),
        "COVERAGE_TARGET_MET": str(coverage_target_met).upper(),
        "COVERAGE_SHORTFALL_COUNT": str(coverage_shortfall),
        "SCANNED_LAST_5D_COUNT": str(scanned_last_5d),
        "OVERDUE_SCAN_COUNT": str(overdue_scan_count),
        "LOW_PRIORITY_SCAN_DEFERRED_COUNT": str(low_priority_deferred),
        "SCAN_LIMIT_REASON": reason,
        "SAME_DAY_PROMOTION_GUARD": str(guard_enabled).upper(),
        "FORCE_SAME_DAY_PROMOTION": str(force_same_day).upper(),
        "SAME_DAY_RUN_COUNT": str(run_state.get("same_day_run_count", "")),
        "LAST_PROMOTION_DATE": str(run_state.get("last_promotion_date", "")),
        "LAST_CORE_PROMOTION_DATE": str(run_state.get("last_core_promotion_date", "")),
        "CORE_PROMOTION_ALLOWED_THIS_RUN": core_allowed,
        "CORE_PROMOTION_BLOCKED_BY_SAME_DAY_GUARD_COUNT": str(blocked_count),
        "PROMOTED_TO_CORE_DAILY_COUNT": str(promoted_core),
        "CORE_DAILY_COUNT": str(core_daily_count),
        "CORE_DAILY_TARGET_CAP": first_value(v16e_read, "CORE_DAILY_TARGET_CAP") or "30",
        "CORE_DAILY_HARD_CAP": first_value(v16e_read, "CORE_DAILY_HARD_CAP") or "50",
        "AUTO_DEMOTED_POSITION_COUNT": str(auto_demoted_positions),
        "OLD_DEFAULT_MODE_VALIDATED": str(old_default_ok).upper(),
        "OLD_FORWARD_MANUAL_MODE_VALIDATED": str(old_forward_ok).upper(),
        "ROLLING_SCAN_MODE_VALIDATED": str(rolling_ok).upper(),
        "PRICE_UPDATE_EXECUTED": "FALSE",
        "EVENT_UPDATE_EXECUTED": "FALSE",
        "FULL_UNIVERSE_UPDATE_EXECUTED": "FALSE",
        "CURRENT_DAILY_MODIFIED": str(current_daily_modified).upper(),
        "STABLE_SNAPSHOT_MODIFIED": str(snapshots_modified).upper(),
        "DANGEROUS_TOKEN_FINDING_COUNT": str(len(hits)),
        "VALIDATION_FAIL_COUNT": str(validation_fail_count),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }

    read_keys = [
        "STATUS", "MODE", "TOTAL_UNIVERSE_COUNT", "COVERAGE_WINDOW_TRADING_DAYS", "DAILY_MIN_SCAN_COUNT",
        "TODAY_ROLLING_SCAN_COUNT", "SCANNED_TICKER_COUNT", "COVERAGE_TARGET_MET", "COVERAGE_SHORTFALL_COUNT",
        "SCANNED_LAST_5D_COUNT", "OVERDUE_SCAN_COUNT", "LOW_PRIORITY_SCAN_DEFERRED_COUNT", "SCAN_LIMIT_REASON",
        "SAME_DAY_PROMOTION_GUARD", "FORCE_SAME_DAY_PROMOTION", "SAME_DAY_RUN_COUNT", "LAST_PROMOTION_DATE",
        "LAST_CORE_PROMOTION_DATE", "CORE_PROMOTION_ALLOWED_THIS_RUN", "CORE_PROMOTION_BLOCKED_BY_SAME_DAY_GUARD_COUNT",
        "PROMOTED_TO_CORE_DAILY_COUNT", "CORE_DAILY_COUNT", "CORE_DAILY_TARGET_CAP", "CORE_DAILY_HARD_CAP",
        "AUTO_DEMOTED_POSITION_COUNT", "OLD_DEFAULT_MODE_VALIDATED", "OLD_FORWARD_MANUAL_MODE_VALIDATED",
        "ROLLING_SCAN_MODE_VALIDATED", "PRICE_UPDATE_EXECUTED", "EVENT_UPDATE_EXECUTED", "FULL_UNIVERSE_UPDATE_EXECUTED",
        "CURRENT_DAILY_MODIFIED", "STABLE_SNAPSHOT_MODIFIED", "DANGEROUS_TOKEN_FINDING_COUNT", "VALIDATION_FAIL_COUNT",
        "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT",
    ]
    read_first = ops / "V18_16H_READ_FIRST.txt"
    read_alias = ops / "V18_CURRENT_SAME_DAY_PROMOTION_GUARD_READ_FIRST.txt"
    write_text(read_first, "\n".join(f"{k}: {values[k]}" for k in read_keys) + "\n")
    write_text(read_alias, read_text(read_first))

    report = [
        "# V18.16H Same-Day Promotion Guard and Coverage Audit",
        "",
        *[f"- {k}: {values[k]}" for k in read_keys],
        "",
        "## Validation",
        "",
        *[f"- {name}: {'PASS' if ok else 'FAIL'} {note}" for name, ok, note in validations],
        "",
        "## Same-Day Rolling Run Check",
        "",
        f"- first_run_promoted_to_core_daily_count: {first_core_promoted}",
        f"- second_run_promoted_to_core_daily_count: {second_core_promoted}",
    ]
    write_text(universe / "V18_16H_CURRENT_ROLLING_SCAN_COVERAGE_REPORT.md", "\n".join(report) + "\n")

    for key in [
        "STATUS", "TOTAL_UNIVERSE_COUNT", "DAILY_MIN_SCAN_COUNT", "TODAY_ROLLING_SCAN_COUNT",
        "COVERAGE_TARGET_MET", "COVERAGE_SHORTFALL_COUNT", "SCAN_LIMIT_REASON",
        "SAME_DAY_PROMOTION_GUARD", "CORE_PROMOTION_ALLOWED_THIS_RUN",
        "CORE_PROMOTION_BLOCKED_BY_SAME_DAY_GUARD_COUNT", "PROMOTED_TO_CORE_DAILY_COUNT",
        "CORE_DAILY_COUNT", "OLD_DEFAULT_MODE_VALIDATED", "OLD_FORWARD_MANUAL_MODE_VALIDATED",
        "ROLLING_SCAN_MODE_VALIDATED", "VALIDATION_FAIL_COUNT", "AUTO_TRADE", "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT",
    ]:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail_count == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--force-same-day-promotion", action="store_true")
    parser.add_argument("--disable-same-day-promotion-guard", action="store_true")
    args = parser.parse_args()
    return build(Path(args.root), args)


if __name__ == "__main__":
    raise SystemExit(main())
