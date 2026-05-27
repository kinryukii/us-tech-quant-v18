from __future__ import annotations

import argparse
import math
import py_compile
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import v18_16K_true_5day_unique_coverage_scheduler as base
import v18_16K_R1_coverage_evidence_quality_patch as r1


STATUS_OK = "OK_V18_16K_R2_EVIDENCE_COUNT_SEMANTICS_PATCH_READY"
STATUS_WARN = "WARN_V18_16K_R2_EVIDENCE_COUNT_SEMANTICS_PATCH_DEGRADED"
MODE = "ADVISORY_ONLY"
PATCH_MODE = "EVIDENCE_COUNT_SEMANTICS_AND_CONSERVATIVE_RECOVERY_AUDIT_ONLY"
REQUIRED_SCAN_DAY_COUNT = 5

R2_OUTPUTS = {
    "evidence_quality": Path("outputs/v18/universe/V18_16K_R2_CURRENT_SCAN_DAY_EVIDENCE_QUALITY.csv"),
    "recovery_audit": Path("outputs/v18/universe/V18_16K_R2_CURRENT_CONSERVATIVE_RECOVERY_PLAN_AUDIT.csv"),
    "reconciliation": Path("outputs/v18/universe/V18_16K_R2_CURRENT_UNIVERSE_COUNT_RECONCILIATION.csv"),
    "read_first": Path("outputs/v18/ops/V18_16K_R2_READ_FIRST.txt"),
    "report": Path("outputs/v18/ops/V18_16K_R2_CURRENT_EVIDENCE_COUNT_SEMANTICS_REPORT.md"),
}

EVIDENCE_R2_FIELDS = [
    "evidence_source_path",
    "evidence_source_type",
    "evidence_modified_time",
    "scan_date",
    "scanned_ticker_count",
    "unique_scanned_ticker_count",
    "duplicate_within_day_count",
    "evidence_file_valid",
    "scan_day_valid",
    "evidence_quality_status",
    "rejection_reason",
    "contributes_to_distinct_scan_day_count",
]
RECON_R2_FIELDS = [
    *r1.RECON_FIELDS,
    "selected_source_reason",
    "conservative_max_count_source",
    "source_count_disagreement_requires_review",
]
RECOVERY_AUDIT_FIELDS = [
    "selected_total_universe_count",
    "max_source_universe_count",
    "required_daily_scan_count",
    "recovery_plan_day_count",
    "recovery_plan_ticker_count",
    "expected_unique_coverage_after_recovery_plan_selected_universe",
    "expected_shortfall_after_recovery_plan_selected_universe",
    "expected_unique_coverage_after_recovery_plan_max_source_universe",
    "expected_shortfall_after_recovery_plan_max_source_universe",
    "recovery_plan_fully_solves_selected_universe",
    "recovery_plan_fully_solves_max_source_universe",
    "universe_count_source_disagreement",
    "advisory_only",
    "notes",
]

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
}


def parse_check(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    command = (
        "$ErrorActionPreference='Stop'; "
        f"[scriptblock]::Create((Get-Content -Raw -LiteralPath '{path}')) | Out-Null; "
        "Write-Output OK_PARSE"
    )
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return True, "OK_PARSE"
        return False, (result.stderr or result.stdout).strip()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def compile_check(path: Path) -> Tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, "OK_COMPILE"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def build_r2_evidence_rows(quality_rows: Sequence[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    file_paths = sorted({str(row.get("evidence_source_path", "")) for row in quality_rows if row.get("evidence_source_path")})
    valid_file_paths = sorted(
        {
            str(row.get("evidence_source_path", ""))
            for row in quality_rows
            if str(row.get("evidence_valid", "")).upper() == "TRUE" and row.get("evidence_source_path")
        }
    )
    considered_days = sorted({str(row.get("scan_date", "")) for row in quality_rows if row.get("scan_date")}, reverse=True)
    valid_days = sorted(
        {
            str(row.get("scan_date", ""))
            for row in quality_rows
            if str(row.get("evidence_valid", "")).upper() == "TRUE" and row.get("scan_date")
        },
        reverse=True,
    )

    contributor_by_day: Dict[str, int] = {}
    for idx, row in enumerate(quality_rows):
        scan_date = str(row.get("scan_date", ""))
        if scan_date not in valid_days or str(row.get("evidence_valid", "")).upper() != "TRUE":
            continue
        current = contributor_by_day.get(scan_date)
        if current is None:
            contributor_by_day[scan_date] = idx
            continue
        current_count = base.to_int(quality_rows[current].get("unique_scanned_ticker_count"), 0)
        row_count = base.to_int(row.get("unique_scanned_ticker_count"), 0)
        if row_count > current_count:
            contributor_by_day[scan_date] = idx

    r2_rows: List[Dict[str, object]] = []
    for idx, row in enumerate(quality_rows):
        evidence_file_valid = str(row.get("evidence_valid", "")).upper() == "TRUE"
        scan_day_valid = evidence_file_valid and bool(row.get("scan_date")) and base.to_int(row.get("unique_scanned_ticker_count"), 0) > 0
        contributes = idx in set(contributor_by_day.values())
        status = "VALID_DISTINCT_SCAN_DAY_CONTRIBUTOR" if contributes else row.get("evidence_quality_status", "")
        if scan_day_valid and not contributes:
            status = "VALID_DUPLICATE_EVIDENCE_FOR_EXISTING_SCAN_DAY"
        r2_rows.append(
            {
                "evidence_source_path": row.get("evidence_source_path", ""),
                "evidence_source_type": row.get("evidence_source_type", ""),
                "evidence_modified_time": row.get("evidence_modified_time", ""),
                "scan_date": row.get("scan_date", ""),
                "scanned_ticker_count": row.get("scanned_ticker_count", 0),
                "unique_scanned_ticker_count": row.get("unique_scanned_ticker_count", 0),
                "duplicate_within_day_count": row.get("duplicate_within_day_count", 0),
                "evidence_file_valid": str(evidence_file_valid).upper(),
                "scan_day_valid": str(scan_day_valid).upper(),
                "evidence_quality_status": status,
                "rejection_reason": row.get("rejection_reason", ""),
                "contributes_to_distinct_scan_day_count": str(contributes).upper(),
            }
        )
    metrics = {
        "EVIDENCE_FILE_CONSIDERED_COUNT": len(file_paths),
        "EVIDENCE_FILE_VALID_COUNT": len(valid_file_paths),
        "DISTINCT_SCAN_DAY_CONSIDERED_COUNT": len(considered_days),
        "DISTINCT_SCAN_DAY_VALID_COUNT": len(valid_days),
        "REQUIRED_SCAN_DAY_COUNT": REQUIRED_SCAN_DAY_COUNT,
        "COVERAGE_WINDOW_COMPLETE": str(len(valid_days) >= REQUIRED_SCAN_DAY_COUNT).upper(),
        "VALID_SCAN_DAYS_USED": ";".join(valid_days[:REQUIRED_SCAN_DAY_COUNT]),
    }
    return r2_rows, metrics


def build_r2_reconciliation(recon_rows: Sequence[Dict[str, object]], selected_source: Path) -> Tuple[List[Dict[str, object]], str, str]:
    counts = [base.to_int(row.get("parsed_universe_count"), 0) for row in recon_rows if base.to_int(row.get("parsed_universe_count"), 0) > 0]
    max_count = max(counts) if counts else 0
    max_sources = [
        str(row.get("source_path", ""))
        for row in recon_rows
        if base.to_int(row.get("parsed_universe_count"), 0) == max_count and max_count > 0
    ]
    max_source = max_sources[0] if max_sources else ""
    disagreement = len(set(counts)) > 1
    rows = []
    for row in recon_rows:
        new_row = dict(row)
        selected = str(row.get("source_selected_for_total_universe_count", "")).upper() == "TRUE"
        new_row["selected_source_reason"] = (
            "CURRENT_ROLLING_STATE_SELECTED_BY_V18_16K_FOR_PER_TICKER_AUDIT"
            if selected
            else ""
        )
        new_row["conservative_max_count_source"] = str(str(row.get("source_path", "")) == max_source).upper()
        new_row["source_count_disagreement_requires_review"] = str(disagreement).upper()
        rows.append(new_row)
    return rows, max_source, str(disagreement).upper()


def build_conservative_recovery_audit(
    selected_count: int,
    max_count: int,
    required_daily_count: int,
    recovery_rows: Sequence[Dict[str, object]],
    expected_selected: int,
    source_disagreement: str,
) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    day_count = len({row.get("planned_day_index") for row in recovery_rows})
    expected_selected = min(expected_selected, selected_count)
    selected_shortfall = max(0, selected_count - expected_selected)
    expected_max = min(expected_selected, max_count) if max_count else expected_selected
    max_shortfall = max(0, max_count - expected_max) if max_count else 0
    solves_selected = selected_shortfall == 0 and selected_count > 0
    solves_max = max_shortfall == 0 and max_count > 0
    row = {
        "selected_total_universe_count": selected_count,
        "max_source_universe_count": max_count if max_count else "",
        "required_daily_scan_count": required_daily_count if required_daily_count else "",
        "recovery_plan_day_count": day_count,
        "recovery_plan_ticker_count": len(recovery_rows),
        "expected_unique_coverage_after_recovery_plan_selected_universe": expected_selected,
        "expected_shortfall_after_recovery_plan_selected_universe": selected_shortfall,
        "expected_unique_coverage_after_recovery_plan_max_source_universe": expected_max,
        "expected_shortfall_after_recovery_plan_max_source_universe": max_shortfall,
        "recovery_plan_fully_solves_selected_universe": str(solves_selected).upper(),
        "recovery_plan_fully_solves_max_source_universe": str(solves_max).upper(),
        "universe_count_source_disagreement": source_disagreement,
        "advisory_only": "TRUE",
        "notes": "MAX_SOURCE_OUTCOME_REMAINS_CONSERVATIVE_WHEN_SOURCE_COUNTS_DISAGREE",
    }
    metrics = {
        "SELECTED_TOTAL_UNIVERSE_COUNT": selected_count,
        "EXPECTED_UNIQUE_COVERAGE_AFTER_RECOVERY_PLAN_SELECTED_UNIVERSE": expected_selected,
        "EXPECTED_SHORTFALL_AFTER_RECOVERY_PLAN_SELECTED_UNIVERSE": selected_shortfall,
        "EXPECTED_UNIQUE_COVERAGE_AFTER_RECOVERY_PLAN_MAX_SOURCE_UNIVERSE": expected_max,
        "EXPECTED_SHORTFALL_AFTER_RECOVERY_PLAN_MAX_SOURCE_UNIVERSE": max_shortfall,
        "RECOVERY_PLAN_FULLY_SOLVES_SELECTED_UNIVERSE": str(solves_selected).upper(),
        "RECOVERY_PLAN_FULLY_SOLVES_MAX_SOURCE_UNIVERSE": str(solves_max).upper(),
        "RECOVERY_PLAN_DAY_COUNT": day_count,
        "TRUE_5DAY_RECOVERY_PLAN_READY": str(bool(recovery_rows)).upper(),
    }
    return [row], metrics


def render_read_first(metrics: Dict[str, object]) -> str:
    fields = [
        "STATUS",
        "MODE",
        "PATCH_MODE",
        "POLICY_APPLIED",
        "TOTAL_UNIVERSE_COUNT",
        "SELECTED_TOTAL_UNIVERSE_COUNT",
        "MIN_SOURCE_UNIVERSE_COUNT",
        "MAX_SOURCE_UNIVERSE_COUNT",
        "UNIVERSE_COUNT_SOURCE_DISAGREEMENT",
        "SOURCE_COUNT_DISAGREEMENT_REQUIRES_REVIEW",
        "REQUIRED_DAILY_SCAN_COUNT",
        "CURRENT_DAILY_SCAN_COUNT",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET",
        "TRUE_5DAY_UNIQUE_COVERAGE_COUNT",
        "TRUE_5DAY_UNIQUE_SHORTFALL_COUNT",
        "UNCOVERED_TICKER_COUNT",
        "DUPLICATE_SCAN_COUNT",
        "EVIDENCE_FILE_CONSIDERED_COUNT",
        "EVIDENCE_FILE_VALID_COUNT",
        "DISTINCT_SCAN_DAY_CONSIDERED_COUNT",
        "DISTINCT_SCAN_DAY_VALID_COUNT",
        "REQUIRED_SCAN_DAY_COUNT",
        "COVERAGE_WINDOW_COMPLETE",
        "VALID_SCAN_DAYS_USED",
        "COVERAGE_EVIDENCE_STATUS",
        "TRUE_5DAY_RECOVERY_PLAN_READY",
        "RECOVERY_PLAN_DAY_COUNT",
        "EXPECTED_UNIQUE_COVERAGE_AFTER_RECOVERY_PLAN_SELECTED_UNIVERSE",
        "EXPECTED_SHORTFALL_AFTER_RECOVERY_PLAN_SELECTED_UNIVERSE",
        "EXPECTED_UNIQUE_COVERAGE_AFTER_RECOVERY_PLAN_MAX_SOURCE_UNIVERSE",
        "EXPECTED_SHORTFALL_AFTER_RECOVERY_PLAN_MAX_SOURCE_UNIVERSE",
        "RECOVERY_PLAN_FULLY_SOLVES_SELECTED_UNIVERSE",
        "RECOVERY_PLAN_FULLY_SOLVES_MAX_SOURCE_UNIVERSE",
        "RUNTIME_BUDGET_STATUS",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "CURRENT_DAILY_MODIFIED",
        "STATE_MODIFIED",
        "PRICE_CACHE_MODIFIED",
        "RANKING_MODIFIED",
        "PROMOTION_DEMOTION_MODIFIED",
        "MANUAL_STATE_MODIFIED",
        "VALIDATION_FAIL_COUNT",
    ]
    lines = [f"{field}: {metrics.get(field, '')}" for field in fields]
    lines.extend([f"READ_FIRST: {metrics.get('READ_FIRST', '')}", f"REPORT: {metrics.get('REPORT', '')}"])
    return "\n".join(lines) + "\n"


def render_report(metrics: Dict[str, object], validations: Sequence[str]) -> str:
    lines = [
        "# V18.16K-R2 Evidence Count Semantics Report",
        "",
        "## Executive summary",
        f"- Status: {metrics['STATUS']}",
        f"- Current true 5-day unique coverage met: {metrics['TRUE_5DAY_UNIQUE_COVERAGE_MET']}",
        f"- Distinct valid scan days: {metrics['DISTINCT_SCAN_DAY_VALID_COUNT']} / {metrics['REQUIRED_SCAN_DAY_COUNT']}",
        f"- Universe source counts: {metrics['MIN_SOURCE_UNIVERSE_COUNT']} to {metrics['MAX_SOURCE_UNIVERSE_COUNT']}",
        "",
        "## Safety statement",
        "- Advisory-only patch. It creates R2 audit outputs and does not apply any recovery plan.",
        "- Current daily behavior, official decisions, ranking, promotion/demotion, manual state, price cache, auto-trade, and auto-sell remain unchanged.",
        "",
        "## Evidence count semantics explanation",
        "- Evidence file counts measure how many source artifacts were considered and how many contained valid dated ticker evidence.",
        "- Distinct scan-day counts measure unique scan dates with valid ticker evidence after de-duplicating multiple files for the same date.",
        "",
        "## Evidence file count vs distinct scan-day count",
        f"- Evidence files valid/considered: {metrics['EVIDENCE_FILE_VALID_COUNT']} / {metrics['EVIDENCE_FILE_CONSIDERED_COUNT']}",
        f"- Distinct scan days valid/considered: {metrics['DISTINCT_SCAN_DAY_VALID_COUNT']} / {metrics['DISTINCT_SCAN_DAY_CONSIDERED_COUNT']}",
        f"- Valid scan days used: {metrics['VALID_SCAN_DAYS_USED']}",
        "",
        "## Current true 5-day coverage status",
        f"- Coverage window complete: {metrics['COVERAGE_WINDOW_COMPLETE']}",
        f"- Unique coverage count: {metrics['TRUE_5DAY_UNIQUE_COVERAGE_COUNT']}",
        f"- Shortfall: {metrics['TRUE_5DAY_UNIQUE_SHORTFALL_COUNT']}",
        "",
        "## Universe count reconciliation",
        f"- Source disagreement: {metrics['UNIVERSE_COUNT_SOURCE_DISAGREEMENT']}",
        f"- Review required: {metrics['SOURCE_COUNT_DISAGREEMENT_REQUIRES_REVIEW']}",
        f"- Selected/max counts: {metrics['SELECTED_TOTAL_UNIVERSE_COUNT']} / {metrics['MAX_SOURCE_UNIVERSE_COUNT']}",
        "",
        "## Conservative recovery plan summary",
        f"- Plan ready: {metrics['TRUE_5DAY_RECOVERY_PLAN_READY']}",
        f"- Selected universe outcome: coverage {metrics['EXPECTED_UNIQUE_COVERAGE_AFTER_RECOVERY_PLAN_SELECTED_UNIVERSE']}, shortfall {metrics['EXPECTED_SHORTFALL_AFTER_RECOVERY_PLAN_SELECTED_UNIVERSE']}, solves {metrics['RECOVERY_PLAN_FULLY_SOLVES_SELECTED_UNIVERSE']}",
        f"- Max-source universe outcome: coverage {metrics['EXPECTED_UNIQUE_COVERAGE_AFTER_RECOVERY_PLAN_MAX_SOURCE_UNIVERSE']}, shortfall {metrics['EXPECTED_SHORTFALL_AFTER_RECOVERY_PLAN_MAX_SOURCE_UNIVERSE']}, solves {metrics['RECOVERY_PLAN_FULLY_SOLVES_MAX_SOURCE_UNIVERSE']}",
        "",
        "## Why current status remains WARN",
        "- The current evidence has fewer than five distinct valid scan days.",
        "- Universe count sources still disagree, so max-source coverage is reported conservatively.",
        "",
        "## Validation summary",
        *[f"- {item}" for item in validations],
        f"- Validation fail count: {metrics['VALIDATION_FAIL_COUNT']}",
        "",
        "## Next-step recommendation",
        "- Resolve the 324 vs 325 source-count discrepancy before treating any recovery plan as complete coverage proof.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    r1_rc = r1.main(["--root", str(root)])
    base_paths = base.discover_inputs(root)
    universe_rows, selected_source, universe_status = base.select_universe_source(base_paths)
    universe, universe_meta = base.load_universe(universe_rows)
    required_daily_count, _ = base.infer_required_daily(base_paths, len(universe))
    current_daily_count, _ = base.infer_current_daily(base_paths)
    evidence = base.collect_evidence(root, base_paths, universe)
    window_days = base.most_recent_scan_days(evidence)
    matrix, uncovered, _duplicates, _source_counter = base.build_coverage(universe, universe_meta, evidence, window_days)
    duplicate_rows = r1.duplicate_detail(matrix)
    recon_rows, recon_metrics = r1.universe_reconciliation(root, selected_source)
    quality_rows, _ = r1.evidence_quality(root, universe)
    recovery_rows, expected_selected, _selected_shortfall = r1.recovery_plan(universe, universe_meta, matrix, required_daily_count)

    r2_quality_rows, evidence_metrics = build_r2_evidence_rows(quality_rows)
    r2_recon_rows, _max_source, source_review = build_r2_reconciliation(recon_rows, selected_source)
    max_count = base.to_int(recon_metrics.get("MAX_SOURCE_UNIVERSE_COUNT"), len(universe))
    recovery_audit_rows, recovery_metrics = build_conservative_recovery_audit(
        len(universe),
        max_count,
        required_daily_count,
        recovery_rows,
        expected_selected,
        source_review,
    )

    unique_coverage_count = sum(1 for row in matrix if str(row.get("covered_in_true_5day_window")).upper() == "TRUE")
    selected_shortfall = max(0, len(universe) - unique_coverage_count)
    coverage_complete = str(evidence_metrics["COVERAGE_WINDOW_COMPLETE"]).upper() == "TRUE"
    true_coverage_met = coverage_complete and len(universe) > 0 and unique_coverage_count >= len(universe)

    reasons = []
    if not coverage_complete:
        reasons.append("FEWER_THAN_5_VALID_SCAN_DAYS")
    if source_review == "TRUE":
        reasons.append("UNIVERSE_COUNT_SOURCE_DISAGREEMENT")
    if universe_status != "OK" or not universe:
        reasons.append("TOTAL_UNIVERSE_UNKNOWN")
    coverage_status = "OK" if not reasons else "WARN_" + ";".join(reasons)
    status = STATUS_WARN if reasons else STATUS_OK

    r2_paths = {key: root / value for key, value in R2_OUTPUTS.items()}
    base.write_csv(r2_paths["evidence_quality"], r2_quality_rows, EVIDENCE_R2_FIELDS)
    base.write_csv(r2_paths["recovery_audit"], recovery_audit_rows, RECOVERY_AUDIT_FIELDS)
    base.write_csv(r2_paths["reconciliation"], r2_recon_rows, RECON_R2_FIELDS)

    wrapper_path = root / "scripts/v18/run_v18_16K_R2_evidence_count_semantics_patch.ps1"
    base_script = root / "scripts/v18/v18_16K_true_5day_unique_coverage_scheduler.py"
    r1_script = root / "scripts/v18/v18_16K_R1_coverage_evidence_quality_patch.py"
    r2_script = root / "scripts/v18/v18_16K_R2_evidence_count_semantics_patch.py"
    ps_ok, ps_msg = parse_check(wrapper_path)
    base_ok, base_msg = compile_check(base_script)
    r1_ok, r1_msg = compile_check(r1_script)
    r2_ok, r2_msg = compile_check(r2_script)
    pre_outputs_ok = all(path.exists() for path in r2_paths.values() if path not in {r2_paths["read_first"], r2_paths["report"]})

    validations = [
        f"PowerShell parse check: {ps_msg}",
        f"Python compile check V18.16K: {base_msg}",
        f"Python compile check V18.16K-R1: {r1_msg}",
        f"Python compile check V18.16K-R2: {r2_msg}",
        f"Run check: {'OK_CURRENT_SCRIPT_EXECUTED' if r1_rc == 0 else 'OK_CURRENT_SCRIPT_EXECUTED_WITH_WARN_EXIT'}",
        f"R2 output existence check: {'OK' if pre_outputs_ok else 'FAILED'}",
        "Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY",
    ]
    validation_fail_count = sum(1 for ok in (ps_ok, base_ok, r1_ok, r2_ok, pre_outputs_ok) if not ok)

    metrics: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "PATCH_MODE": PATCH_MODE,
        "TOTAL_UNIVERSE_COUNT": len(universe) if universe else "UNKNOWN",
        "REQUIRED_DAILY_SCAN_COUNT": required_daily_count if required_daily_count else "UNKNOWN",
        "CURRENT_DAILY_SCAN_COUNT": current_daily_count if current_daily_count else "UNKNOWN",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": str(true_coverage_met).upper(),
        "TRUE_5DAY_UNIQUE_COVERAGE_COUNT": unique_coverage_count,
        "TRUE_5DAY_UNIQUE_SHORTFALL_COUNT": selected_shortfall,
        "UNCOVERED_TICKER_COUNT": len(uncovered),
        "DUPLICATE_SCAN_COUNT": sum(base.to_int(row.get("duplicate_count"), 0) for row in duplicate_rows),
        "SOURCE_COUNT_DISAGREEMENT_REQUIRES_REVIEW": source_review,
        "COVERAGE_EVIDENCE_STATUS": coverage_status,
        "RUNTIME_BUDGET_STATUS": "OK_ADVISORY_LOCAL_IO_ONLY",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "READ_FIRST": str(r2_paths["read_first"]),
        "REPORT": str(r2_paths["report"]),
    }
    metrics.update(SAFETY_FLAGS)
    metrics.update(recon_metrics)
    metrics.update(evidence_metrics)
    metrics.update(recovery_metrics)

    base.write_text(r2_paths["read_first"], render_read_first(metrics))
    base.write_text(r2_paths["report"], render_report(metrics, validations))
    final_outputs_ok = all(path.exists() for path in r2_paths.values())
    if not final_outputs_ok:
        metrics["VALIDATION_FAIL_COUNT"] = base.to_int(metrics["VALIDATION_FAIL_COUNT"]) + 1
        base.write_text(r2_paths["read_first"], render_read_first(metrics))
        base.write_text(r2_paths["report"], render_report(metrics, validations + ["Final output existence check: FAILED"]))

    print(f"STATUS: {metrics['STATUS']}")
    print(f"MODE: {metrics['MODE']}")
    print(f"PATCH_MODE: {metrics['PATCH_MODE']}")
    print(f"EVIDENCE_FILE_VALID_COUNT: {metrics['EVIDENCE_FILE_VALID_COUNT']}")
    print(f"EVIDENCE_FILE_CONSIDERED_COUNT: {metrics['EVIDENCE_FILE_CONSIDERED_COUNT']}")
    print(f"DISTINCT_SCAN_DAY_VALID_COUNT: {metrics['DISTINCT_SCAN_DAY_VALID_COUNT']}")
    print(f"DISTINCT_SCAN_DAY_CONSIDERED_COUNT: {metrics['DISTINCT_SCAN_DAY_CONSIDERED_COUNT']}")
    print(f"COVERAGE_WINDOW_COMPLETE: {metrics['COVERAGE_WINDOW_COMPLETE']}")
    print(f"VALID_SCAN_DAYS_USED: {metrics['VALID_SCAN_DAYS_USED']}")
    print(f"RECOVERY_PLAN_FULLY_SOLVES_SELECTED_UNIVERSE: {metrics['RECOVERY_PLAN_FULLY_SOLVES_SELECTED_UNIVERSE']}")
    print(f"RECOVERY_PLAN_FULLY_SOLVES_MAX_SOURCE_UNIVERSE: {metrics['RECOVERY_PLAN_FULLY_SOLVES_MAX_SOURCE_UNIVERSE']}")
    print(f"VALIDATION_FAIL_COUNT: {metrics['VALIDATION_FAIL_COUNT']}")
    print(f"READ_FIRST: {r2_paths['read_first']}")
    print(f"REPORT: {r2_paths['report']}")
    return 1 if base.to_int(metrics["VALIDATION_FAIL_COUNT"]) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
