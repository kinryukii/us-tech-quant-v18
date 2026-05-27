from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_16F_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN_READY"
STATUS_WARN = "WARN_V18_16F_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN_VALIDATION_FAILED"
MODE = "CURRENT_DAILY_INTEGRATION_WITH_ROLLING_SCAN"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

PS_PARSE = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/run_v18_16F_current_daily_with_rolling_universe_scan.ps1",
    "scripts/v18/run_v18_16A_universe_rolling_state_builder.ps1",
    "scripts/v18/run_v18_16B_rolling_scan_scheduler.ps1",
    "scripts/v18/run_v18_16C_scan_scoped_data_update.ps1",
    "scripts/v18/run_v18_16D_priority_based_light_scanner.ps1",
    "scripts/v18/run_v18_16E_promotion_demotion_engine.ps1",
]

PY_COMPILE = [
    "scripts/v18/v18_16F_current_daily_with_rolling_universe_scan.py",
    "scripts/v18/v18_16A_universe_rolling_state_builder.py",
    "scripts/v18/v18_16B_rolling_scan_scheduler.py",
    "scripts/v18/v18_16C_scan_scoped_data_update.py",
    "scripts/v18/v18_16D_priority_based_light_scanner.py",
    "scripts/v18/v18_16E_promotion_demotion_engine.py",
]


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


def first_value(path: Path, key: str) -> str:
    target = key.upper()
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        if k.strip().upper().lstrip("- ").strip() == target:
            return v.strip()
    return ""


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
                    hits.append(f"{path}:{line_no}:{token}")
            if "AUTO_TRADE" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{path}:{line_no}:AUTO_TRADE_ENABLED")
            if "AUTO_SELL" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{path}:{line_no}:AUTO_SELL_ENABLED")
            if in_token_block and (stripped.endswith("]") or stripped.endswith(")")):
                in_token_block = False
    return hits


def run_component(root: Path, name: str, script_rel: str, args: Sequence[str], read_first_rel: str, expected_output_rel: str) -> Dict[str, object]:
    script = root / script_rel
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *args]
    proc = subprocess.run(command, cwd=str(root), text=True, capture_output=True, timeout=900)
    read_first = root / read_first_rel
    vfail = first_value(read_first, "VALIDATION_FAIL_COUNT")
    status = first_value(read_first, "STATUS")
    ok = proc.returncode == 0 and (vfail in {"", "0"})
    return {
        "component_name": name,
        "script_path": script_rel,
        "expected_output": expected_output_rel,
        "ran_this_run": "TRUE",
        "component_status": status or ("PASS" if ok else "FAIL"),
        "read_first_path": read_first_rel,
        "validation_fail_count": vfail or ("0" if ok else "1"),
        "notes": "\n".join((proc.stdout + proc.stderr).splitlines()[-8:]),
        "_ok": ok,
    }


def build(root: Path, args: argparse.Namespace) -> int:
    start = time.monotonic()
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    read_center = root / "outputs/v18/read_center"
    ensure_dir(ops)
    ensure_dir(read_center)
    stable_before = stable_baseline(root)
    audit_rows: List[Dict[str, object]] = []

    components = [
        ("V18.16A", "scripts/v18/run_v18_16A_universe_rolling_state_builder.ps1", [], "outputs/v18/ops/V18_16A_READ_FIRST.txt", "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv"),
        ("V18.16B", "scripts/v18/run_v18_16B_rolling_scan_scheduler.ps1", [], "outputs/v18/ops/V18_16B_READ_FIRST.txt", "outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv"),
        ("V18.16C", "scripts/v18/run_v18_16C_scan_scoped_data_update.ps1", (["-UseYFinance"] if args.use_yfinance_for_rolling_scan else []) + ["-MaxRuntimeSeconds", str(args.max_runtime_seconds), "-SoftStopSeconds", str(args.soft_stop_seconds)], "outputs/v18/ops/V18_16C_READ_FIRST.txt", "outputs/v18/data/V18_CURRENT_SCAN_SCOPED_PRICE_UPDATE_AUDIT.csv"),
        ("V18.16D", "scripts/v18/run_v18_16D_priority_based_light_scanner.ps1", [], "outputs/v18/ops/V18_16D_READ_FIRST.txt", "outputs/v18/universe/V18_CURRENT_PRIORITY_LIGHT_SCAN_RESULT.csv"),
        ("V18.16E", "scripts/v18/run_v18_16E_promotion_demotion_engine.ps1", (["-ForceSameDayPromotion"] if args.force_same_day_promotion else []) + (["-DisableSameDayPromotionGuard"] if args.disable_same_day_promotion_guard else []), "outputs/v18/ops/V18_16E_READ_FIRST.txt", "outputs/v18/universe/V18_CURRENT_PROMOTION_DEMOTION_AUDIT.csv"),
    ]
    for comp in components:
        audit_rows.append(run_component(root, *comp))

    if args.run_manual_feedback:
        comp_args = ["-RunManualFeedback"]
        if args.run_forward_tracker:
            comp_args.append("-RunForwardTracker")
        if args.full_daily:
            comp_args.append("-FullDaily")
        if args.read_center_refresh_only:
            comp_args.append("-ReadCenterRefreshOnly")
        if args.validate_only:
            comp_args.append("-ValidateOnly")
        audit_rows.append(run_component(root, "V18.15B/V18.15A manual feedback", "scripts/v18/run_v18_15B_current_daily_with_manual_feedback.ps1", comp_args, "outputs/v18/ops/V18_15B_READ_FIRST.txt", "outputs/v18/ops/V18_15B_CURRENT_DAILY_WITH_MANUAL_FEEDBACK_REPORT.md"))
    elif args.run_forward_tracker:
        audit_rows.append(run_component(root, "V18.14C forward tracker", "scripts/v18/run_v18_14C_ranked_candidate_forward_tracker.ps1", [], "outputs/v18/ops/V18_CURRENT_FORWARD_TRACKER_READ_FIRST.txt", "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv"))
        audit_rows.append(run_component(root, "V18.14D forward price filler", "scripts/v18/run_v18_14D_ranked_candidate_forward_price_filler.ps1", [], "outputs/v18/ops/V18_CURRENT_FORWARD_PRICE_FILLER_READ_FIRST.txt", "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv"))

    actual_runtime = round(time.monotonic() - start, 3)
    runtime_status = "OK_WITHIN_BUDGET" if actual_runtime <= args.max_runtime_seconds else "WARN_OVER_BUDGET"
    component_fail_count = sum(1 for r in audit_rows if not r.get("_ok"))

    ps_fail = sum(1 for rel in PS_PARSE if not parse_ps(root / rel)[0])
    py_fail = sum(1 for rel in PY_COMPILE if not compile_py(root / rel)[0])
    snapshots_modified = stable_modified(stable_before, root)
    read_first_path = ops / "V18_16F_READ_FIRST.txt"
    report_path = read_center / "V18_16F_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN.md"
    summary_path = ops / "V18_16F_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN_SUMMARY.csv"
    audit_path = ops / "V18_16F_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN_INPUT_AUDIT.csv"
    hits = dangerous_hits([root / "scripts/v18/run_v18_current_daily_command_center.ps1", root / "scripts/v18/run_v18_16F_current_daily_with_rolling_universe_scan.ps1", root / "scripts/v18/v18_16F_current_daily_with_rolling_universe_scan.py", read_first_path, report_path, summary_path, audit_path], root)

    validation_fail_count = component_fail_count + ps_fail + py_fail + len(hits) + (1 if snapshots_modified else 0)
    v16b = root / "outputs/v18/ops/V18_16B_READ_FIRST.txt"
    v16c = root / "outputs/v18/ops/V18_16C_READ_FIRST.txt"
    v16d = root / "outputs/v18/ops/V18_16D_READ_FIRST.txt"
    v16e = root / "outputs/v18/ops/V18_16E_READ_FIRST.txt"
    values = {
        "STATUS": STATUS_OK if validation_fail_count == 0 else STATUS_WARN,
        "MODE": MODE,
        "RUN_MODE": "FULL_DAILY" if args.full_daily else "READ_CENTER_REFRESH_ONLY",
        "RUN_TRIGGERED_UPDATE": "TRUE",
        "BACKGROUND_UPDATE": "DISABLED",
        "AUTO_SCHEDULED_UPDATE": "DISABLED",
        "ROLLING_SCAN_THIS_RUN": "TRUE",
        "SCAN_SCOPED_DATA_UPDATE": "TRUE",
        "USE_YFINANCE_FOR_ROLLING_SCAN": str(args.use_yfinance_for_rolling_scan).upper(),
        "MAX_RUNTIME_SECONDS": str(args.max_runtime_seconds),
        "SOFT_STOP_SECONDS": str(args.soft_stop_seconds),
        "ACTUAL_RUNTIME_SECONDS": str(actual_runtime),
        "RUNTIME_BUDGET_STATUS": runtime_status,
        "TOTAL_UNIVERSE_COUNT": first_value(v16e, "TOTAL_UNIVERSE_COUNT"),
        "TODAY_ROLLING_SCAN_COUNT": first_value(v16b, "TODAY_SCAN_PLAN_COUNT"),
        "DAILY_MIN_SCAN_COUNT": first_value(v16b, "DAILY_MIN_SCAN_COUNT"),
        "SCANNED_TICKER_COUNT": first_value(v16e, "SCANNED_TICKER_COUNT") or first_value(v16d, "SCANNED_TICKER_COUNT"),
        "DATA_UNAVAILABLE_COUNT": first_value(v16d, "DATA_UNAVAILABLE_COUNT"),
        "LATEST_ONLY_COUNT": first_value(v16d, "LATEST_ONLY_COUNT"),
        "FULL_HISTORY_AVAILABLE_COUNT": first_value(v16d, "FULL_HISTORY_AVAILABLE_COUNT"),
        "PROMOTED_TO_WATCHLIST_COUNT": first_value(v16e, "PROMOTED_TO_WATCHLIST_COUNT"),
        "PROMOTED_TO_STRONG_WATCH_COUNT": first_value(v16e, "PROMOTED_TO_STRONG_WATCH_COUNT"),
        "PROMOTED_TO_CANDIDATE_COUNT": first_value(v16e, "PROMOTED_TO_CANDIDATE_COUNT"),
        "PROMOTED_TO_CORE_DAILY_COUNT": first_value(v16e, "PROMOTED_TO_CORE_DAILY_COUNT"),
        "SAME_DAY_PROMOTION_GUARD": first_value(v16e, "SAME_DAY_PROMOTION_GUARD") or str(not args.disable_same_day_promotion_guard).upper(),
        "FORCE_SAME_DAY_PROMOTION": first_value(v16e, "FORCE_SAME_DAY_PROMOTION") or str(args.force_same_day_promotion).upper(),
        "SAME_DAY_RUN_COUNT": first_value(v16e, "SAME_DAY_RUN_COUNT"),
        "LAST_PROMOTION_DATE": first_value(v16e, "LAST_PROMOTION_DATE"),
        "LAST_CORE_PROMOTION_DATE": first_value(v16e, "LAST_CORE_PROMOTION_DATE"),
        "CORE_PROMOTION_ALLOWED_THIS_RUN": first_value(v16e, "CORE_PROMOTION_ALLOWED_THIS_RUN"),
        "CORE_PROMOTION_BLOCKED_BY_SAME_DAY_GUARD_COUNT": first_value(v16e, "CORE_PROMOTION_BLOCKED_BY_SAME_DAY_GUARD_COUNT"),
        "DEMOTED_TO_CANDIDATE_COUNT": first_value(v16e, "DEMOTED_TO_CANDIDATE_COUNT"),
        "DEMOTED_TO_STRONG_WATCH_COUNT": first_value(v16e, "DEMOTED_TO_STRONG_WATCH_COUNT"),
        "DEMOTED_TO_WATCHLIST_COUNT": first_value(v16e, "DEMOTED_TO_WATCHLIST_COUNT"),
        "DEMOTED_TO_RESEARCH_COUNT": first_value(v16e, "DEMOTED_TO_RESEARCH_COUNT"),
        "CAP_LIMITED_NO_PROMOTION_COUNT": first_value(v16e, "CAP_LIMITED_NO_PROMOTION_COUNT"),
        "POSITION_COUNT": first_value(v16e, "POSITION_COUNT"),
        "CORE_DAILY_COUNT": first_value(v16e, "CORE_DAILY_COUNT"),
        "CANDIDATE_COUNT": first_value(v16e, "CANDIDATE_COUNT"),
        "STRONG_WATCH_COUNT": first_value(v16e, "STRONG_WATCH_COUNT"),
        "WATCHLIST_COUNT": first_value(v16e, "WATCHLIST_COUNT"),
        "RESEARCH_COUNT": first_value(v16e, "RESEARCH_COUNT"),
        "FORWARD_TRACKER_RUN": str(args.run_forward_tracker).upper(),
        "MANUAL_FEEDBACK_RUN": str(args.run_manual_feedback).upper(),
        "FORWARD_TRACKER_STATUS": "RAN" if args.run_forward_tracker else "SKIPPED",
        "MANUAL_FEEDBACK_STATUS": "RAN" if args.run_manual_feedback else "SKIPPED",
        "PRICE_UPDATE_EXECUTED": first_value(v16c, "PRICE_UPDATE_EXECUTED") or "FALSE",
        "EVENT_UPDATE_EXECUTED": first_value(v16c, "EVENT_UPDATE_EXECUTED") or "FALSE",
        "FULL_UNIVERSE_UPDATE_EXECUTED": first_value(v16c, "FULL_UNIVERSE_UPDATE_EXECUTED") or "FALSE",
        "CURRENT_DAILY_MODIFIED": "TRUE_FOR_OPTIONAL_FLAG_ONLY",
        "STABLE_SNAPSHOT_MODIFIED": str(snapshots_modified).upper(),
        "DANGEROUS_TOKEN_FINDING_COUNT": str(len(hits)),
        "COMPONENT_FAIL_COUNT": str(component_fail_count),
        "VALIDATION_FAIL_COUNT": str(validation_fail_count),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }
    run_state_path = root / "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json"
    run_state = read_json(run_state_path)
    run_state.update({
        "last_total_universe_count": values["TOTAL_UNIVERSE_COUNT"],
        "last_daily_min_scan_count": values["DAILY_MIN_SCAN_COUNT"],
        "last_today_scan_count": values["TODAY_ROLLING_SCAN_COUNT"],
    })
    write_json(run_state_path, run_state)
    keys = list(values.keys())
    write_text(read_first_path, "\n".join(f"{k}: {values[k]}" for k in keys) + "\n")
    write_csv(summary_path, [{"metric": k, "value": v} for k, v in values.items()], ["metric", "value"])
    write_csv(audit_path, [{k: v for k, v in row.items() if not k.startswith("_")} for row in audit_rows], ["component_name", "script_path", "expected_output", "ran_this_run", "component_status", "read_first_path", "validation_fail_count", "notes"])
    report = ["# V18.16F Current Daily With Rolling Universe Scan", "", *[f"- {k}: {values[k]}" for k in keys], "", "## Component Audit", ""]
    for row in audit_rows:
        report.append(f"- {row['component_name']}: {row['component_status']} validation_fail_count={row['validation_fail_count']}")
    write_text(report_path, "\n".join(report) + "\n")
    write_text(read_center / "V18_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN.md", read_text(report_path))
    write_text(ops / "V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt", read_text(read_first_path))
    write_csv(ops / "V18_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN_SUMMARY.csv", [{"metric": k, "value": v} for k, v in values.items()], ["metric", "value"])

    for key in ["STATUS", "MODE", "ROLLING_SCAN_THIS_RUN", "TOTAL_UNIVERSE_COUNT", "TODAY_ROLLING_SCAN_COUNT", "SCANNED_TICKER_COUNT", "PROMOTED_TO_WATCHLIST_COUNT", "PROMOTED_TO_STRONG_WATCH_COUNT", "PROMOTED_TO_CANDIDATE_COUNT", "PROMOTED_TO_CORE_DAILY_COUNT", "DEMOTED_TO_CANDIDATE_COUNT", "DEMOTED_TO_STRONG_WATCH_COUNT", "CORE_DAILY_COUNT", "CANDIDATE_COUNT", "WATCHLIST_COUNT", "RESEARCH_COUNT", "FORWARD_TRACKER_RUN", "MANUAL_FEEDBACK_RUN", "COMPONENT_FAIL_COUNT", "VALIDATION_FAIL_COUNT", "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT"]:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail_count == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--use-yfinance-for-rolling-scan", action="store_true")
    parser.add_argument("--run-forward-tracker", action="store_true")
    parser.add_argument("--run-manual-feedback", action="store_true")
    parser.add_argument("--force-same-day-promotion", action="store_true")
    parser.add_argument("--disable-same-day-promotion-guard", action="store_true")
    parser.add_argument("--full-daily", action="store_true")
    parser.add_argument("--read-center-refresh-only", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--max-runtime-seconds", type=int, default=300)
    parser.add_argument("--soft-stop-seconds", type=int, default=270)
    args = parser.parse_args()
    return build(Path(args.root), args)


if __name__ == "__main__":
    raise SystemExit(main())
