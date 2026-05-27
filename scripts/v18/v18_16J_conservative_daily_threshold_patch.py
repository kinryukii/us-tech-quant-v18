from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_16J_CONSERVATIVE_DAILY_THRESHOLD_PATCH_READY"
STATUS_WARN = "WARN_V18_16J_CONSERVATIVE_DAILY_THRESHOLD_PATCH_VALIDATION_FAILED"
MODE = "CONSERVATIVE_DAILY_THRESHOLD_PATCH"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

AUDIT_FIELDS = ["metric", "before_value", "after_value", "status", "source_file", "reason"]
POLICY_FIELDS = ["policy_field", "value", "source_file", "applied", "reason"]
COVERAGE_FIELDS = ["metric", "value", "status", "reason", "source_file"]


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
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
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


def file_hashes(paths: Iterable[Path]) -> Dict[str, str]:
    return {str(path.resolve()): sha256(path) for path in paths if path.exists() and path.is_file()}


def first_value(path: Path, key: str) -> str:
    target = key.upper()
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        if left.strip().upper().lstrip("- ").strip() == target:
            return right.strip()
    return ""


def to_int(value: object, default: int = 0) -> int:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return default
    try:
        return int(float(text))
    except Exception:
        return default


def bool_text(value: bool) -> str:
    return str(bool(value)).upper()


def run_cmd(root: Path, args: Sequence[str]) -> Dict[str, object]:
    proc = subprocess.run(args, cwd=str(root), text=True, capture_output=True, timeout=1800)
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-30:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-30:]),
    }


def ps_parse(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    escaped = str(path).replace("'", "''")
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f"$null = [scriptblock]::Create((Get-Content -Raw '{escaped}')); 'OK_PARSE'",
    ]
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    text = (result.stdout + result.stderr).strip()
    return result.returncode == 0 and "OK_PARSE" in text, text


def py_compile(path: Path) -> Tuple[bool, str]:
    python = Path(r"D:\us-tech-quant\.venv\Scripts\python.exe")
    cmd = [str(python if python.exists() else "python"), "-m", "py_compile", str(path)]
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def main_build(root: Path) -> int:
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    universe = root / "outputs/v18/universe"
    ensure_dir(ops)
    ensure_dir(universe)

    scheduler_py = root / "scripts/v18/v18_16B_rolling_scan_scheduler.py"
    scheduler_ps = root / "scripts/v18/run_v18_16B_rolling_scan_scheduler.ps1"
    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    state_csv = root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv"
    run_state_json = root / "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json"
    promotion = universe / "V18_CURRENT_PROMOTION_DEMOTION_AUDIT.csv"
    ranking = root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
    price_update = root / "outputs/v18/data/V18_CURRENT_SCAN_SCOPED_PRICE_UPDATE_AUDIT.csv"
    v16b_read = ops / "V18_16B_READ_FIRST.txt"
    v16i_read = ops / "V18_16I_READ_FIRST.txt"

    read_first_path = ops / "V18_16J_READ_FIRST.txt"
    audit_path = universe / "V18_16J_CURRENT_DAILY_THRESHOLD_PATCH_AUDIT.csv"
    policy_path = universe / "V18_16J_CURRENT_DAILY_THRESHOLD_POLICY.csv"
    coverage_path = universe / "V18_16J_CURRENT_POST_PATCH_COVERAGE_CHECK.csv"
    report_path = universe / "V18_16J_CURRENT_DAILY_THRESHOLD_PATCH_REPORT.md"

    prior_audit_rows, _, _ = read_csv(audit_path)
    original_old_daily_target = 0
    for row in prior_audit_rows:
        if str(row.get("metric", "")).strip() == "daily_scan_target":
            original_old_daily_target = to_int(row.get("before_value"))
            break

    protected = [current_daily, state_csv, run_state_json, promotion, ranking, price_update]
    before_hashes = file_hashes(protected)

    state_rows, _, state_status = read_csv(state_csv)
    total_universe = len([r for r in state_rows if str(r.get("ticker", "")).strip()])
    required_daily = math.ceil(total_universe / 5) if total_universe else 0

    old_daily_target = to_int(first_value(v16b_read, "TODAY_SCAN_PLAN_COUNT"))
    baseline_old_daily_target = original_old_daily_target or old_daily_target
    old_daily_min = to_int(first_value(v16b_read, "DAILY_MIN_SCAN_COUNT"))
    old_configured_cost = to_int(first_value(v16b_read, "CONFIGURED_MAX_ESTIMATED_PLAN_COST") or first_value(v16b_read, "MAX_ESTIMATED_PLAN_COST"))
    old_effective_cost = to_int(first_value(v16b_read, "MAX_ESTIMATED_PLAN_COST"))
    old_coverage_met = str(first_value(ops / "V18_16H_READ_FIRST.txt", "COVERAGE_TARGET_MET") or "FALSE").upper()
    old_shortfall = to_int(first_value(ops / "V18_16H_READ_FIRST.txt", "COVERAGE_SHORTFALL_COUNT"), max(0, required_daily - old_daily_target))

    scheduler_run = run_cmd(root, ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(scheduler_ps)])

    new_daily_target = to_int(first_value(v16b_read, "TODAY_SCAN_PLAN_COUNT"))
    new_daily_min = to_int(first_value(v16b_read, "DAILY_MIN_SCAN_COUNT"))
    configured_cost = to_int(first_value(v16b_read, "CONFIGURED_MAX_ESTIMATED_PLAN_COST"))
    cost_floor = to_int(first_value(v16b_read, "DAILY_THRESHOLD_COST_FLOOR"))
    effective_cost = to_int(first_value(v16b_read, "MAX_ESTIMATED_PLAN_COST"))
    estimated_cost = to_int(first_value(v16b_read, "ESTIMATED_PLAN_COST"))

    true_unique_met = str(first_value(v16i_read, "PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_MET") or "FALSE").upper()
    true_unique_count = to_int(first_value(v16i_read, "PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_COUNT"))
    true_unique_shortfall = to_int(first_value(v16i_read, "PROJECTED_TRUE_5DAY_UNIQUE_SHORTFALL_COUNT"))
    true_warning_preserved = true_unique_met == "FALSE" and true_unique_shortfall > 0

    after_hashes = file_hashes(protected)
    state_modified = before_hashes.get(str(state_csv.resolve())) != after_hashes.get(str(state_csv.resolve()))
    run_state_modified = before_hashes.get(str(run_state_json.resolve())) != after_hashes.get(str(run_state_json.resolve()))
    current_daily_modified = before_hashes.get(str(current_daily.resolve())) != after_hashes.get(str(current_daily.resolve()))
    promotion_modified = before_hashes.get(str(promotion.resolve())) != after_hashes.get(str(promotion.resolve()))
    ranking_modified = before_hashes.get(str(ranking.resolve())) != after_hashes.get(str(ranking.resolve()))
    price_update_modified = before_hashes.get(str(price_update.resolve())) != after_hashes.get(str(price_update.resolve()))

    policy_applied = scheduler_run["returncode"] == 0 and new_daily_target >= required_daily and required_daily > baseline_old_daily_target
    daily_threshold_met_expected = new_daily_target >= required_daily

    audit_rows = [
        {"metric": "total_universe_count", "before_value": total_universe, "after_value": total_universe, "status": "INFO", "source_file": str(state_csv), "reason": state_status},
        {"metric": "daily_scan_target", "before_value": baseline_old_daily_target, "after_value": new_daily_target, "status": "PATCHED" if new_daily_target >= required_daily and required_daily > baseline_old_daily_target else "ALREADY_PATCHED", "source_file": str(v16b_read), "reason": "Scheduler plan count after conservative threshold patch."},
        {"metric": "daily_min_scan_count", "before_value": old_daily_min, "after_value": new_daily_min, "status": "COMPUTED", "source_file": str(scheduler_py), "reason": "ceil(total_universe_count / 5)."},
        {"metric": "coverage_target_met", "before_value": old_coverage_met, "after_value": bool_text(daily_threshold_met_expected), "status": "EXPECTED_IMPROVE", "source_file": str(v16b_read), "reason": "Daily threshold expectation only; true unique coverage remains separate."},
        {"metric": "coverage_shortfall", "before_value": old_shortfall, "after_value": max(0, required_daily - new_daily_target), "status": "EXPECTED_IMPROVE", "source_file": str(v16b_read), "reason": "Daily threshold shortfall after scheduler patch."},
        {"metric": "quota_source", "before_value": f"configured_max_estimated_plan_cost={old_effective_cost}", "after_value": f"effective_max_estimated_plan_cost=max({configured_cost},{cost_floor})", "status": "PATCHED", "source_file": str(scheduler_py), "reason": "Cost cap now floors to the computed daily threshold budget."},
    ]

    policy_rows = [
        {"policy_field": "DAILY_MIN_SCAN_COUNT", "value": new_daily_min, "source_file": str(scheduler_py), "applied": bool_text(policy_applied), "reason": "Computed as ceil(total_universe_count / 5)."},
        {"policy_field": "TARGET_DAILY_SCAN_COUNT", "value": new_daily_target, "source_file": str(v16b_read), "applied": bool_text(policy_applied), "reason": "Generated scheduler target after patch."},
        {"policy_field": "CONFIGURED_MAX_ESTIMATED_PLAN_COST", "value": configured_cost, "source_file": str(scheduler_py), "applied": bool_text(policy_applied), "reason": "Legacy configured cap retained for traceability."},
        {"policy_field": "DAILY_THRESHOLD_COST_FLOOR", "value": cost_floor, "source_file": str(scheduler_py), "applied": bool_text(policy_applied), "reason": "Computed budget floor required to reach daily threshold."},
        {"policy_field": "EFFECTIVE_MAX_ESTIMATED_PLAN_COST", "value": effective_cost, "source_file": str(scheduler_py), "applied": bool_text(policy_applied), "reason": "max(configured cap, daily threshold cost floor)."},
    ]

    coverage_rows = [
        {"metric": "TOTAL_UNIVERSE_COUNT", "value": total_universe, "status": "INFO", "reason": "Read from rolling universe state.", "source_file": str(state_csv)},
        {"metric": "REQUIRED_DAILY_SCAN_COUNT", "value": required_daily, "status": "PASS" if required_daily > 0 else "FAIL", "reason": "ceil(total universe / 5).", "source_file": str(scheduler_py)},
        {"metric": "TARGET_DAILY_SCAN_COUNT", "value": new_daily_target, "status": "PASS" if new_daily_target >= required_daily else "FAIL", "reason": "Scheduler output after patch.", "source_file": str(v16b_read)},
        {"metric": "EXPECTED_DAILY_SCAN_COUNT", "value": new_daily_target, "status": "PASS" if new_daily_target >= required_daily else "FAIL", "reason": "Expected daily threshold target.", "source_file": str(v16b_read)},
        {"metric": "DAILY_THRESHOLD_TARGET_MET_EXPECTED", "value": bool_text(daily_threshold_met_expected), "status": "PASS" if daily_threshold_met_expected else "FAIL", "reason": "Daily threshold only.", "source_file": str(v16b_read)},
        {"metric": "TRUE_5DAY_UNIQUE_COVERAGE_MET", "value": true_unique_met, "status": "PASS" if true_unique_met == "FALSE" else "FAIL", "reason": "True unique coverage was not fixed by V18.16J.", "source_file": str(v16i_read)},
        {"metric": "TRUE_5DAY_UNIQUE_COVERAGE_COUNT", "value": true_unique_count, "status": "INFO", "reason": "Preserved from V18.16I optimizer.", "source_file": str(v16i_read)},
        {"metric": "TRUE_5DAY_UNIQUE_SHORTFALL_COUNT", "value": true_unique_shortfall, "status": "PASS" if true_unique_shortfall > 0 else "FAIL", "reason": "Warning must remain until V18.16K.", "source_file": str(v16i_read)},
        {"metric": "TRUE_5DAY_UNIQUE_WARNING_PRESERVED", "value": bool_text(true_warning_preserved), "status": "PASS" if true_warning_preserved else "FAIL", "reason": "Daily Trust must not become HIGH solely from daily threshold.", "source_file": str(v16i_read)},
    ]

    write_csv(audit_path, audit_rows, AUDIT_FIELDS)
    write_csv(policy_path, policy_rows, POLICY_FIELDS)
    write_csv(coverage_path, coverage_rows, COVERAGE_FIELDS)

    ps_ok, ps_note = ps_parse(root / "scripts/v18/run_v18_16J_conservative_daily_threshold_patch.ps1")
    py_ok, py_note = py_compile(root / "scripts/v18/v18_16J_conservative_daily_threshold_patch.py")

    validations = [
        ("POWERSHELL_PARSE", ps_ok, ps_note),
        ("PYTHON_COMPILE", py_ok, py_note),
        ("SCHEDULER_RUN_OK", scheduler_run["returncode"] == 0, scheduler_run["stderr_tail"]),
        ("NEW_DAILY_SCAN_TARGET_MATCHES_REQUIRED_DAILY", new_daily_target == required_daily and required_daily > 0, f"new={new_daily_target};required={required_daily}"),
        ("DAILY_THRESHOLD_PATCH_APPLIED", policy_applied, f"baseline_old={baseline_old_daily_target};new={new_daily_target};required={required_daily}"),
        ("TRUE_5DAY_UNIQUE_COVERAGE_FALSE", true_unique_met == "FALSE", true_unique_met),
        ("TRUE_5DAY_UNIQUE_WARNING_PRESERVED", true_warning_preserved, str(true_unique_shortfall)),
        ("STATE_NOT_MODIFIED", not state_modified and not run_state_modified, ""),
        ("CURRENT_DAILY_NOT_MODIFIED", not current_daily_modified, ""),
        ("PROMOTION_DEMOTION_NOT_MODIFIED", not promotion_modified, ""),
        ("RANKING_NOT_MODIFIED", not ranking_modified, ""),
        ("PRICE_UPDATE_NOT_MODIFIED", not price_update_modified, ""),
        ("AUTO_TRADE_DISABLED", AUTO_TRADE == "DISABLED", AUTO_TRADE),
        ("AUTO_SELL_DISABLED", AUTO_SELL == "DISABLED", AUTO_SELL),
        ("OFFICIAL_DECISION_IMPACT_NONE", OFFICIAL_DECISION_IMPACT == "NONE", OFFICIAL_DECISION_IMPACT),
    ]
    validation_fail_count = sum(1 for _, ok, _ in validations if not ok)
    status = STATUS_OK if validation_fail_count == 0 else STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": MODE,
        "OLD_DAILY_SCAN_TARGET": str(baseline_old_daily_target),
        "NEW_DAILY_SCAN_TARGET": str(new_daily_target),
        "TOTAL_UNIVERSE_COUNT": str(total_universe),
        "REQUIRED_DAILY_SCAN_COUNT": str(required_daily),
        "DAILY_THRESHOLD_PATCH_APPLIED": bool_text(policy_applied),
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": true_unique_met,
        "TRUE_5DAY_UNIQUE_WARNING_PRESERVED": bool_text(true_warning_preserved),
        "POLICY_APPLIED": bool_text(policy_applied),
        "STATE_MODIFIED": bool_text(state_modified or run_state_modified),
        "CURRENT_DAILY_MODIFIED": bool_text(current_daily_modified),
        "PROMOTION_DEMOTION_MODIFIED": bool_text(promotion_modified),
        "RANKING_MODIFIED": bool_text(ranking_modified),
        "PRICE_UPDATE_MODIFIED": bool_text(price_update_modified),
        "VALIDATION_FAIL_COUNT": str(validation_fail_count),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "READ_FIRST": str(read_first_path),
        "REPORT": str(report_path),
    }

    read_keys = [
        "STATUS", "MODE", "OLD_DAILY_SCAN_TARGET", "NEW_DAILY_SCAN_TARGET",
        "TOTAL_UNIVERSE_COUNT", "REQUIRED_DAILY_SCAN_COUNT",
        "DAILY_THRESHOLD_PATCH_APPLIED", "TRUE_5DAY_UNIQUE_COVERAGE_MET",
        "TRUE_5DAY_UNIQUE_WARNING_PRESERVED", "POLICY_APPLIED", "STATE_MODIFIED",
        "CURRENT_DAILY_MODIFIED", "PROMOTION_DEMOTION_MODIFIED", "RANKING_MODIFIED",
        "PRICE_UPDATE_MODIFIED", "VALIDATION_FAIL_COUNT", "AUTO_TRADE", "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT", "READ_FIRST", "REPORT",
    ]
    write_text(read_first_path, "\n".join(f"{key}: {values[key]}" for key in read_keys) + "\n")

    report_lines = [
        "# V18.16J Conservative Daily Threshold Patch",
        "",
        *[f"- {key}: {values[key]}" for key in read_keys],
        "",
        "## Exact Patch",
        "",
        "- File: scripts/v18/v18_16B_rolling_scan_scheduler.py",
        "- Field/logic: MAX_ESTIMATED_PLAN_COST now uses an effective computed floor: max(configured cap, DAILY_THRESHOLD_COST_FLOOR).",
        "- DAILY_THRESHOLD_COST_FLOOR is computed from the current universe plan needed to satisfy ceil(TOTAL_UNIVERSE_COUNT / 5).",
        "",
        "## Daily Threshold",
        "",
        f"- Old daily scan target: {baseline_old_daily_target}",
        f"- New daily scan target: {new_daily_target}",
        f"- Required daily scan count: {required_daily}",
        f"- Estimated plan cost: {estimated_cost}",
        f"- Configured cost cap: {configured_cost}",
        f"- Daily threshold cost floor: {cost_floor}",
        f"- Effective cost cap: {effective_cost}",
        "",
        "## Trust Guard",
        "",
        f"- TRUE_5DAY_UNIQUE_COVERAGE_MET: {true_unique_met}",
        f"- TRUE_5DAY_UNIQUE_COVERAGE_COUNT: {true_unique_count}",
        f"- TRUE_5DAY_UNIQUE_SHORTFALL_COUNT: {true_unique_shortfall}",
        "- Coverage trust should remain WARN/degraded until V18.16K addresses true unique five-day scheduling.",
        "- V18.19A must not infer HIGH trust solely from this daily-threshold patch.",
        "",
        "## Validation",
        "",
        *[f"- {name}: {'PASS' if ok else 'FAIL'} {note}" for name, ok, note in validations],
    ]
    write_text(report_path, "\n".join(report_lines) + "\n")

    for key in [
        "STATUS", "MODE", "OLD_DAILY_SCAN_TARGET", "NEW_DAILY_SCAN_TARGET",
        "TOTAL_UNIVERSE_COUNT", "REQUIRED_DAILY_SCAN_COUNT",
        "DAILY_THRESHOLD_PATCH_APPLIED", "TRUE_5DAY_UNIQUE_COVERAGE_MET",
        "TRUE_5DAY_UNIQUE_WARNING_PRESERVED", "POLICY_APPLIED", "STATE_MODIFIED",
        "CURRENT_DAILY_MODIFIED", "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT",
        "READ_FIRST", "REPORT",
    ]:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail_count == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    return main_build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
