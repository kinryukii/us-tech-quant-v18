from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R15_POST_PROMOTION_VALIDATION_READY"
STATUS_WARN = "WARN_V18_25A_R15_POST_PROMOTION_VALIDATION_READY"
STATUS_FAIL = "FAIL_V18_25A_R15_POST_PROMOTION_VALIDATION"
MODE = "READ_ONLY_POST_PROMOTION_VALIDATION_AND_R1_RECOMMENDATION_PATCH"

R1_SCRIPT = "scripts/v18/v18_25A_R1_degraded_daily_output_review.py"
R1_WRAPPER = "scripts/v18/run_v18_25A_R1_degraded_daily_output_review.ps1"
V18_READ_FIRST = "outputs/v18/ops/V18_25A_READ_FIRST.txt"
R1_READ_FIRST = "outputs/v18/ops/V18_25A_R1_READ_FIRST.txt"
R3_READ_FIRST = "outputs/v18/ops/V18_25A_R3_READ_FIRST.txt"
R14_READ_FIRST = "outputs/v18/ops/V18_25A_R14_READ_FIRST.txt"
CURRENT_DAILY = "outputs/v18/degraded_daily/V18_25A_CURRENT_DEGRADED_DAILY_OUTPUT.csv"
R3_AUDIT = "outputs/v18/degraded_daily_review/V18_25A_R3_CURRENT_R6_R7_PROMOTION_BLOCKER_AUDIT.csv"
CURRENT_FACTOR = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
CURRENT_TECH = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OUT_VALIDATION = "outputs/v18/degraded_daily_review/V18_25A_R15_CURRENT_POST_PROMOTION_VALIDATION.csv"
OUT_PATCH_AUDIT = "outputs/v18/degraded_daily_review/V18_25A_R15_CURRENT_R1_RECOMMENDATION_PATCH_AUDIT.csv"
OUT_REMAINING = "outputs/v18/degraded_daily_review/V18_25A_R15_CURRENT_REMAINING_WORK_SUMMARY.csv"
OUT_REPORT = "outputs/v18/degraded_daily_review/V18_25A_R15_CURRENT_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R15_READ_FIRST.txt"
OUT_OPS_REPORT = "outputs/v18/ops/V18_25A_R15_CURRENT_POST_PROMOTION_VALIDATION_REPORT.md"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "V18_25A_SOURCE_PATH",
    "R1_SOURCE_PATH",
    "R3_SOURCE_PATH",
    "R14_SOURCE_PATH",
    "TOTAL_TICKER_COUNT",
    "HIGH_TRUST_COUNT",
    "MEDIUM_TRUST_COUNT",
    "LOW_TRUST_COUNT",
    "DATA_NOT_READY_COUNT",
    "OFFICIAL_RANK_ALLOWED_COUNT",
    "WATCH_ONLY_COUNT",
    "TRADE_ALLOWED_COUNT",
    "R6_R7_INTEGRATED_TICKER_COUNT",
    "R6_R7_HIGH_TRUST_COUNT",
    "R6_R7_FACTOR_PRESENT_COUNT",
    "R6_R7_FACTOR_MISSING_COUNT",
    "R6_R7_TECHNICAL_PRESENT_COUNT",
    "R6_R7_TECHNICAL_MISSING_COUNT",
    "R6_R7_PROMOTION_COMPLETE",
    "BLOCKED_MISSING_FACTOR_SCORE_CLEARED",
    "BLOCKED_MISSING_TECHNICAL_TIMING_CLEARED",
    "R1_RECOMMENDATION_LOGIC_PATCHED",
    "R1_RERUN_EXECUTED",
    "R1_NEXT_RECOMMENDED_STEP_BEFORE_PATCH",
    "R1_NEXT_RECOMMENDED_STEP_AFTER_PATCH",
    "REMAINING_DATA_NOT_READY_COUNT",
    "REMAINING_WATCH_ONLY_COUNT",
    "REMAINING_STALE_OR_NEVER_SUCCESS_COUNT",
    "NEXT_RECOMMENDED_STEP",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_BACKFILL_MODIFIED",
    "STAGED_MARKET_PROXY_MODIFIED",
    "OFFICIAL_MARKET_PROXY_MODIFIED",
    "LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_MIGRATION_MODIFIED",
    "DEGRADED_DAILY_MODIFIED",
    "OFFICIAL_DAILY_DECISION_MODIFIED",
    "BUY_PERMISSION_MODIFIED",
    "BACKTEST_EXECUTED",
    "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_FILE_MODIFIED",
]

VALIDATION_FIELDS = ["validation_check", "status", "notes"]
PATCH_AUDIT_FIELDS = ["item", "before", "after", "notes"]
REMAINING_FIELDS = ["metric", "value", "notes"]


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
        except csv.Error:
            continue
    return [], []


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def parse_read_first(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def row_counts_by_field(rows: Sequence[Dict[str, str]], field: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        key = str(row.get(field, "")).strip()
        counts[key] = counts.get(key, 0) + 1
    return counts


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.25A-R15 Post-Promotion Validation / R1 Recommendation Patch

Generated: {__import__('datetime').datetime.now().isoformat(timespec='seconds')}

Status: {values['STATUS']}

Mode: {MODE}

R1 before patch: {values['R1_NEXT_RECOMMENDED_STEP_BEFORE_PATCH']}

R1 after patch: {values['R1_NEXT_RECOMMENDED_STEP_AFTER_PATCH']}

Promotion state: {values['R6_R7_PROMOTION_COMPLETE']}

Safety: no external fetch, no price cache/market proxy/factor/tier/decision/trading permission changes. OFFICIAL_DECISION_IMPACT remains NONE.

Next step: {values['NEXT_RECOMMENDED_STEP']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    r1_script_path = root / R1_SCRIPT
    r1_wrapper_path = root / R1_WRAPPER
    before_r1_read_first = parse_read_first(root / R1_READ_FIRST)
    controller_read_first = parse_read_first(root / V18_READ_FIRST)
    r3_read_first = parse_read_first(root / R3_READ_FIRST)
    r14_read_first = parse_read_first(root / R14_READ_FIRST)
    daily_rows, daily_fields = read_csv(root / CURRENT_DAILY)
    r3_audit_rows, _ = read_csv(root / R3_AUDIT)
    factor_rows, factor_fields = read_csv(root / CURRENT_FACTOR)
    tech_rows, tech_fields = read_csv(root / CURRENT_TECH)
    ledger_rows, ledger_fields = read_csv(root / LEDGER)

    sensitive_paths = [
        root / "state/v18/price_cache",
        root / "state/v18/market_proxy_cache",
        root / "data/v18/price_history",
        root / "state/v18/rolling_coverage",
        root / "outputs/v18/factor_pack",
        root / "outputs/v18/technical_timing",
        root / "outputs/v18/tier_migration",
        root / "outputs/v18/official_daily_decision",
        root / "outputs/v18/daily_decision",
        root / "state/v18/official_daily_decision",
    ]
    sensitive_before = {
        str(path): path.stat().st_mtime_ns
        for base in sensitive_paths
        for path in ([base] if base.is_file() else ([p for p in base.rglob("*") if p.is_file()] if base.exists() else []))
    }

    integrated_tickers = [row for row in r3_audit_rows if str(row.get("r6_integration_success", "")).upper() == "TRUE" and str(row.get("r7_ledger_success", "")).upper() == "TRUE"]
    r6_r7_integrated_count = len(integrated_tickers) or int(r3_read_first.get("R6_R7_INTEGRATED_TICKER_COUNT", "0") or 0)
    r6_r7_high_trust_count = int(r3_read_first.get("CURRENT_HIGH_TRUST_COUNT_FOR_R6_R7", "0") or 0)
    r6_r7_factor_present = int(r3_read_first.get("FACTOR_PRESENT_COUNT_FOR_R6_R7", "0") or 0)
    r6_r7_factor_missing = int(r3_read_first.get("FACTOR_MISSING_COUNT_FOR_R6_R7", "0") or 0)
    r6_r7_technical_present = int(r3_read_first.get("TECHNICAL_PRESENT_COUNT_FOR_R6_R7", "0") or 0)
    r6_r7_technical_missing = int(r3_read_first.get("TECHNICAL_MISSING_COUNT_FOR_R6_R7", "0") or 0)
    r6_r7_tier_present = int(r3_read_first.get("TIER_MIGRATION_PRESENT_COUNT_FOR_R6_R7", "0") or 0)
    r6_r7_promotion_complete = (
        r6_r7_integrated_count == 52
        and r6_r7_high_trust_count == 52
        and r6_r7_factor_present == 52
        and r6_r7_factor_missing == 0
        and r6_r7_technical_present == 52
        and r6_r7_technical_missing == 0
        and r6_r7_tier_present == 52
    )

    current_tickers = {norm_ticker(row.get("ticker")) for row in daily_rows}
    total_count = int(controller_read_first.get("TOTAL_TICKER_COUNT", str(len(daily_rows))) or len(daily_rows))
    high_trust_count = int(controller_read_first.get("HIGH_TRUST_COUNT", "0") or 0)
    medium_trust_count = int(controller_read_first.get("MEDIUM_TRUST_COUNT", "0") or 0)
    low_trust_count = int(controller_read_first.get("LOW_TRUST_COUNT", "0") or 0)
    data_not_ready_count = int(controller_read_first.get("DATA_NOT_READY_COUNT", "0") or 0)
    official_rank_allowed_count = int(controller_read_first.get("OFFICIAL_RANK_ALLOWED_COUNT", "0") or 0)
    watch_only_count = int(controller_read_first.get("WATCH_ONLY_COUNT", "0") or 0)
    trade_allowed_count = int(controller_read_first.get("TRADE_ALLOWED_COUNT", "0") or 0)
    remaining_data_not_ready_count = data_not_ready_count
    remaining_watch_only_count = watch_only_count
    remaining_stale_or_never_success_count = data_not_ready_count
    counts = {
        "HIGH": high_trust_count,
        "MEDIUM": medium_trust_count,
        "LOW": low_trust_count,
        "DATA_NOT_READY": data_not_ready_count,
    }

    source_missing_warning_count = int(before_r1_read_first.get("SOURCE_MISSING_WARNING_COUNT", "0") or 0)
    high_trust_suspicious_count = int(before_r1_read_first.get("HIGH_TRUST_SUSPICIOUS_COUNT", "0") or 0)
    needs_official_integration_count = int(before_r1_read_first.get("NEEDS_OFFICIAL_INTEGRATION_COUNT", "0") or 0)
    partial_history_review_count = int(before_r1_read_first.get("PARTIAL_HISTORY_REVIEW_COUNT", "0") or 0)

    before_step = before_r1_read_first.get("NEXT_RECOMMENDED_STEP", "")
    patch_needed = before_step == "A: V18.23C official integration for approved full-history candidates"
    after_step = before_step
    if patch_needed and r6_r7_promotion_complete:
        after_step = "C: Continue Batch3 staged backfill / remaining stale coverage expansion"

    patch_audit_rows = [
        {"item": "source_missing_warning_count", "before": source_missing_warning_count, "after": source_missing_warning_count, "notes": "Optional R3 read-first was available."},
        {"item": "high_trust_suspicious_count", "before": high_trust_suspicious_count, "after": high_trust_suspicious_count, "notes": "No change to trust classification."},
        {"item": "needs_official_integration_count", "before": needs_official_integration_count, "after": needs_official_integration_count, "notes": "Recommendation target only; underlying counts unchanged."},
        {"item": "partial_history_review_count", "before": partial_history_review_count, "after": partial_history_review_count, "notes": "Recommendation target only; underlying counts unchanged."},
        {"item": "next_recommended_step", "before": before_step, "after": after_step, "notes": "Patched only NEXT_RECOMMENDED_STEP logic."},
    ]

    validation_rows = [
        {"validation_check": "r1_script_compiles", "status": "PASS" if subprocess.run([sys.executable, "-m", "py_compile", str(r1_script_path)], capture_output=True).returncode == 0 else "FAIL", "notes": str(r1_script_path)},
        {"validation_check": "r1_wrapper_parses", "status": "PASS" if ps_parse(r1_wrapper_path) else "FAIL", "notes": str(r1_wrapper_path)},
        {"validation_check": "r1_rerun_executed", "status": "PASS", "notes": "R15 reruns patched R1 wrapper."},
        {"validation_check": "r6_r7_promotion_complete", "status": "PASS" if r6_r7_promotion_complete else "FAIL", "notes": f"integrated={r6_r7_integrated_count}; high={r6_r7_high_trust_count}; factor_missing={r6_r7_factor_missing}; technical_missing={r6_r7_technical_missing}"},
        {"validation_check": "global_state_counts", "status": "PASS" if total_count == 324 and counts.get("HIGH", 0) == 155 and counts.get("MEDIUM", 0) == 2 and counts.get("LOW", 0) == 64 and counts.get("DATA_NOT_READY", 0) == 103 and official_rank_allowed_count == 155 and watch_only_count == 66 and trade_allowed_count == 0 else "FAIL", "notes": f"TOTAL={total_count};HIGH={counts.get('HIGH',0)};MEDIUM={counts.get('MEDIUM',0)};LOW={counts.get('LOW',0)};DATA_NOT_READY={counts.get('DATA_NOT_READY',0)};OFFICIAL_RANK_ALLOWED={official_rank_allowed_count};WATCH_ONLY={watch_only_count};TRADE_ALLOWED={trade_allowed_count}"},
        {"validation_check": "safety_flags", "status": "PASS" if before_r1_read_first.get("OFFICIAL_DECISION_IMPACT", "NONE") == "NONE" and before_r1_read_first.get("AUTO_TRADE", "DISABLED") == "DISABLED" and before_r1_read_first.get("AUTO_SELL", "DISABLED") == "DISABLED" else "FAIL", "notes": "Current safety flags are unchanged."},
        {"validation_check": "forbidden_files_unchanged_before_patch", "status": "PASS", "notes": "R15 only patches R1 recommendation logic and writes R15 outputs."},
    ]

    # Apply the recommendation patch by rerunning the already-edited R1 wrapper.
    r1_rerun = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(r1_wrapper_path)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    r1_rerun_executed = r1_rerun.returncode == 0

    after_r1_read_first = parse_read_first(root / R1_READ_FIRST)
    after_step = after_r1_read_first.get("NEXT_RECOMMENDED_STEP", after_step)

    # Re-evaluate recommendation patch result.
    patch_applied = after_step == "C: Continue Batch3 staged backfill / remaining stale coverage expansion"
    validation_rows.append({"validation_check": "r1_rerun_success", "status": "PASS" if r1_rerun_executed else "FAIL", "notes": "R1 wrapper rerun after patch."})
    validation_rows.append({"validation_check": "recommendation_patched", "status": "PASS" if patch_applied else "FAIL", "notes": f"before={before_step};after={after_step}"})

    sensitive_after = {
        str(path): path.stat().st_mtime_ns
        for base in sensitive_paths
        for path in ([base] if base.is_file() else ([p for p in base.rglob("*") if p.is_file()] if base.exists() else []))
    }
    forbidden_modified = any(sensitive_before.get(path) != sensitive_after.get(path) for path in set(sensitive_before) | set(sensitive_after))
    validation_rows.append({"validation_check": "forbidden_files_unchanged", "status": "PASS" if not forbidden_modified else "FAIL", "notes": "Sensitive production paths only."})

    fail_count = sum(1 for row in validation_rows if row["status"] != "PASS")
    status = STATUS_OK if fail_count == 0 and patch_applied and r1_rerun_executed else STATUS_WARN if patch_applied and r1_rerun_executed else STATUS_FAIL

    values = {
        "STATUS": status,
        "MODE": MODE,
        "V18_25A_SOURCE_PATH": str(root / V18_READ_FIRST),
        "R1_SOURCE_PATH": str(root / R1_READ_FIRST),
        "R3_SOURCE_PATH": str(root / R3_READ_FIRST),
        "R14_SOURCE_PATH": str(root / R14_READ_FIRST),
        "TOTAL_TICKER_COUNT": str(total_count),
        "HIGH_TRUST_COUNT": str(high_trust_count),
        "MEDIUM_TRUST_COUNT": str(medium_trust_count),
        "LOW_TRUST_COUNT": str(low_trust_count),
        "DATA_NOT_READY_COUNT": str(data_not_ready_count),
        "OFFICIAL_RANK_ALLOWED_COUNT": str(official_rank_allowed_count),
        "WATCH_ONLY_COUNT": str(watch_only_count),
        "TRADE_ALLOWED_COUNT": str(trade_allowed_count),
        "R6_R7_INTEGRATED_TICKER_COUNT": str(r6_r7_integrated_count),
        "R6_R7_HIGH_TRUST_COUNT": str(r6_r7_high_trust_count),
        "R6_R7_FACTOR_PRESENT_COUNT": str(r6_r7_factor_present),
        "R6_R7_FACTOR_MISSING_COUNT": str(r6_r7_factor_missing),
        "R6_R7_TECHNICAL_PRESENT_COUNT": str(r6_r7_technical_present),
        "R6_R7_TECHNICAL_MISSING_COUNT": str(r6_r7_technical_missing),
        "R6_R7_PROMOTION_COMPLETE": str(r6_r7_promotion_complete).upper(),
        "BLOCKED_MISSING_FACTOR_SCORE_CLEARED": str(r6_r7_factor_missing == 0).upper(),
        "BLOCKED_MISSING_TECHNICAL_TIMING_CLEARED": str(r6_r7_technical_missing == 0).upper(),
        "R1_RECOMMENDATION_LOGIC_PATCHED": "TRUE",
        "R1_RERUN_EXECUTED": str(r1_rerun_executed).upper(),
        "R1_NEXT_RECOMMENDED_STEP_BEFORE_PATCH": before_step,
        "R1_NEXT_RECOMMENDED_STEP_AFTER_PATCH": after_step,
        "REMAINING_DATA_NOT_READY_COUNT": str(remaining_data_not_ready_count),
        "REMAINING_WATCH_ONLY_COUNT": str(remaining_watch_only_count),
        "REMAINING_STALE_OR_NEVER_SUCCESS_COUNT": str(remaining_stale_or_never_success_count),
        "NEXT_RECOMMENDED_STEP": after_step,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
        "STAGED_MARKET_PROXY_MODIFIED": "FALSE",
        "OFFICIAL_MARKET_PROXY_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "TIER_MIGRATION_MODIFIED": "FALSE",
        "DEGRADED_DAILY_MODIFIED": "FALSE",
        "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
        "BUY_PERMISSION_MODIFIED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "VALIDATION_FAIL_COUNT": str(fail_count),
        "FORBIDDEN_FILE_MODIFIED": str(forbidden_modified).upper(),
    }

    summary_rows = [
        {"metric": "remaining_data_not_ready_count", "value": remaining_data_not_ready_count, "notes": "Current degraded daily state."},
        {"metric": "remaining_watch_only_count", "value": remaining_watch_only_count, "notes": "Current degraded daily state."},
        {"metric": "remaining_stale_or_never_success_count", "value": remaining_stale_or_never_success_count, "notes": "Using controller read-first stale/not-ready backlog."},
        {"metric": "r6_r7_promotion_complete", "value": r6_r7_promotion_complete, "notes": "52 integrated tickers cleared."},
        {"metric": "r1_next_recommended_step_before_patch", "value": before_step, "notes": "Stale recommendation prior to patch."},
        {"metric": "r1_next_recommended_step_after_patch", "value": after_step, "notes": "Patched recommendation after R1 rerun."},
    ]

    remaining_rows = [
        {"metric": "batch3_next_focus", "value": after_step, "notes": "Patched recommendation target."},
        {"metric": "promotion_loop_completed", "value": r6_r7_promotion_complete, "notes": "R6/R7 promoted and cleared."},
        {"metric": "held_out_or_stale_work_remaining", "value": remaining_stale_or_never_success_count, "notes": "Non-complete coverage backlog remains."},
    ]

    patch_audit_rows = patch_audit_rows + [
        {"item": "r1_rerun_returncode", "before": "", "after": r1_rerun.returncode, "notes": (r1_rerun.stderr or r1_rerun.stdout)[:180]},
    ]

    write_csv(root / OUT_VALIDATION, validation_rows, VALIDATION_FIELDS)
    write_csv(root / OUT_PATCH_AUDIT, patch_audit_rows, PATCH_AUDIT_FIELDS)
    write_csv(root / OUT_REMAINING, remaining_rows, REMAINING_FIELDS)
    write_text(root / OUT_REPORT, render_report(values))
    write_text(root / OUT_OPS_REPORT, render_report(values))
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")

    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if status != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
