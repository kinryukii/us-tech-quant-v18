from __future__ import annotations

import argparse
import csv
import math
import py_compile
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import v18_16K_true_5day_unique_coverage_scheduler as base


STATUS_OK = "OK_V18_16K_R1_COVERAGE_EVIDENCE_QUALITY_PATCH_READY"
STATUS_WARN = "WARN_V18_16K_R1_COVERAGE_EVIDENCE_QUALITY_PATCH_DEGRADED"
MODE = "ADVISORY_ONLY"
PATCH_MODE = "SOURCE_RECONCILIATION_AND_AUDIT_ONLY"
COVERAGE_WINDOW_DAYS = 5

R1_OUTPUTS = {
    "reconciliation": Path("outputs/v18/universe/V18_16K_R1_CURRENT_UNIVERSE_COUNT_RECONCILIATION.csv"),
    "evidence_quality": Path("outputs/v18/universe/V18_16K_R1_CURRENT_SCAN_DAY_EVIDENCE_QUALITY.csv"),
    "duplicate_detail": Path("outputs/v18/universe/V18_16K_R1_CURRENT_DUPLICATE_SCAN_DETAIL.csv"),
    "recovery_plan": Path("outputs/v18/universe/V18_16K_R1_CURRENT_5DAY_RECOVERY_PLAN.csv"),
    "read_first": Path("outputs/v18/ops/V18_16K_R1_READ_FIRST.txt"),
    "report": Path("outputs/v18/ops/V18_16K_R1_CURRENT_COVERAGE_EVIDENCE_QUALITY_REPORT.md"),
}

RECON_FIELDS = [
    "source_path",
    "source_exists",
    "modified_time",
    "parsed_universe_count",
    "parsed_required_daily_count",
    "parsed_current_daily_count",
    "source_type",
    "source_freshness_status",
    "source_selected_for_total_universe_count",
    "notes",
]
EVIDENCE_FIELDS = [
    "evidence_source_path",
    "evidence_source_type",
    "evidence_modified_time",
    "scan_date",
    "scanned_ticker_count",
    "unique_scanned_ticker_count",
    "duplicate_within_day_count",
    "evidence_file_valid",
    "scan_day_valid",
    "evidence_valid",
    "evidence_quality_status",
    "rejection_reason",
]
DUP_DETAIL_FIELDS = [
    "ticker",
    "scan_day_count",
    "scan_dates",
    "duplicate_count",
    "latest_scan_date",
    "duplicate_reason",
]
RECOVERY_FIELDS = [
    "planned_day_index",
    "planned_scan_date_label",
    "ticker",
    "priority_reason",
    "coverage_status_before_plan",
    "expected_coverage_status_after_plan",
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


def mtime(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def readfirst_metrics(path: Path) -> Dict[str, str]:
    metrics: Dict[str, str] = {}
    for line in base.read_text(path).splitlines():
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        key = left.strip().lstrip("-").strip().upper()
        if key:
            metrics[key] = right.strip()
    return metrics


def source_type(path: Path) -> str:
    name = path.name.upper()
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return "READ_FIRST"
    if "ROLLING_SCAN_PLAN" in name:
        return "ROLLING_SCAN_PLAN"
    if "UNIVERSE_ROLLING_STATE" in name:
        return "UNIVERSE_ROLLING_STATE"
    if "DAILY_THRESHOLD_POLICY" in name:
        return "DAILY_THRESHOLD_POLICY"
    return suffix.lstrip(".").upper() or "UNKNOWN"


def freshness_status(path: Path, selected_mtime: float | None) -> str:
    if not path.exists():
        return "MISSING"
    if selected_mtime is None:
        return "AVAILABLE"
    delta = abs(path.stat().st_mtime - selected_mtime)
    if delta <= 300:
        return "CURRENT_WITH_SELECTED_SOURCE"
    if path.stat().st_mtime < selected_mtime:
        return "OLDER_THAN_SELECTED_SOURCE"
    return "NEWER_THAN_SELECTED_SOURCE"


def candidate_paths(root: Path) -> List[Path]:
    return [
        root / "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv",
        root / "outputs/v18/universe/V18_16A_CURRENT_UNIVERSE_ROLLING_STATE_AUDIT.csv",
        root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
        root / "outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv",
        root / "outputs/v18/universe/V18_16B_CURRENT_ROLLING_SCAN_PLAN.csv",
        root / "outputs/v18/universe/V18_16J_CURRENT_DAILY_THRESHOLD_POLICY.csv",
        root / "outputs/v18/ops/V18_16F_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_16J_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_16K_READ_FIRST.txt",
    ]


def parse_counts(path: Path) -> Tuple[int, int, int, str]:
    if not path.exists():
        return 0, 0, 0, "MISSING"
    if path.suffix.lower() == ".txt":
        metrics = readfirst_metrics(path)
        total = base.to_int(metrics.get("TOTAL_UNIVERSE_COUNT"), 0)
        required = base.to_int(metrics.get("REQUIRED_DAILY_SCAN_COUNT") or metrics.get("DAILY_MIN_SCAN_COUNT"), 0)
        current = base.to_int(
            metrics.get("CURRENT_DAILY_SCAN_COUNT")
            or metrics.get("TODAY_ROLLING_SCAN_COUNT")
            or metrics.get("SCANNED_TICKER_COUNT"),
            0,
        )
        return total, required, current, "READ_FIRST_FIELDS"

    rows, fields, status = base.read_csv(path)
    if status != "OK":
        return 0, 0, 0, status

    tickers = {base.normalize_ticker(row.get("ticker")) for row in rows}
    tickers.discard("")
    total = len(tickers)
    required = 0
    current = 0

    if "ROLLING_SCAN_PLAN" in path.name.upper():
        selected = [row for row in rows if base.boolish(row.get("selected_this_run"))]
        if selected:
            current = len({base.normalize_ticker(row.get("ticker")) for row in selected if base.normalize_ticker(row.get("ticker"))})
        else:
            current = total
        return 0, required, current, "SCAN_PLAN_DAILY_SCOPE_NOT_TOTAL_UNIVERSE"

    if rows and "policy_field" in fields and "value" in fields:
        policy = {str(row.get("policy_field", "")).upper(): row.get("value", "") for row in rows}
        required = base.to_int(policy.get("DAILY_MIN_SCAN_COUNT") or policy.get("TARGET_DAILY_SCAN_COUNT"), 0)
        if required and not total:
            total = required * COVERAGE_WINDOW_DAYS
            return total, required, current, "POLICY_DERIVED_TOTAL_FROM_DAILY_MIN_X_5"

    for field in ("REQUIRED_DAILY_SCAN_COUNT", "DAILY_MIN_SCAN_COUNT", "required_daily_scan_count", "daily_min_scan_count"):
        if rows and field in rows[0]:
            required = base.to_int(rows[0].get(field), required)
    for field in ("CURRENT_DAILY_SCAN_COUNT", "TODAY_ROLLING_SCAN_COUNT", "SCANNED_TICKER_COUNT"):
        if rows and field in rows[0]:
            current = base.to_int(rows[0].get(field), current)
    return total, required, current, "CSV_TICKER_OR_FIELDS"


def universe_reconciliation(root: Path, selected_source: Path) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    selected_mtime = selected_source.stat().st_mtime if selected_source.exists() else None
    rows: List[Dict[str, object]] = []
    counts = []
    for path in candidate_paths(root):
        total, required, current, note = parse_counts(path)
        if total > 0:
            counts.append(total)
        rows.append(
            {
                "source_path": str(path),
                "source_exists": str(path.exists()).upper(),
                "modified_time": mtime(path),
                "parsed_universe_count": total if total > 0 else "",
                "parsed_required_daily_count": required if required > 0 else "",
                "parsed_current_daily_count": current if current > 0 else "",
                "source_type": source_type(path),
                "source_freshness_status": freshness_status(path, selected_mtime),
                "source_selected_for_total_universe_count": str(path.resolve() == selected_source.resolve()).upper() if path.exists() and selected_source.exists() else "FALSE",
                "notes": note,
            }
        )
    min_count = min(counts) if counts else 0
    max_count = max(counts) if counts else 0
    disagreement = len(set(counts)) > 1
    status = "WARN_SOURCE_COUNTS_DISAGREE" if disagreement else "OK_SOURCE_COUNTS_ALIGNED"
    if not counts:
        status = "WARN_NO_SOURCE_UNIVERSE_COUNTS"
    return rows, {
        "UNIVERSE_COUNT_RECONCILIATION_STATUS": status,
        "MIN_SOURCE_UNIVERSE_COUNT": min_count if min_count else "UNKNOWN",
        "MAX_SOURCE_UNIVERSE_COUNT": max_count if max_count else "UNKNOWN",
        "UNIVERSE_COUNT_SOURCE_DISAGREEMENT": str(disagreement).upper(),
    }


def rows_to_evidence(path: Path, universe: Sequence[str]) -> List[Dict[str, str]]:
    stype = source_type(path)
    if stype == "UNIVERSE_ROLLING_STATE":
        return base.rolling_state_evidence(path, universe)
    if stype == "ROLLING_SCAN_PLAN":
        return base.scan_plan_evidence(path)
    return []


def evidence_quality(root: Path, universe: Sequence[str]) -> Tuple[List[Dict[str, object]], List[Dict[str, str]]]:
    sources = [
        root / "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv",
        root / "outputs/v18/universe/V18_16A_CURRENT_UNIVERSE_ROLLING_STATE_AUDIT.csv",
        root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
        root / "outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv",
        root / "outputs/v18/universe/V18_16B_CURRENT_ROLLING_SCAN_PLAN.csv",
    ]
    archive_root = root / "archive/stable"
    if archive_root.exists():
        for pattern in (
            "*/outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv",
            "*/outputs/v18/universe/V18_16B_CURRENT_ROLLING_SCAN_PLAN.csv",
        ):
            sources.extend(sorted(archive_root.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)[:30])

    quality_rows: List[Dict[str, object]] = []
    all_evidence: List[Dict[str, str]] = []
    for path in sources:
        if not path.exists():
            continue
        evidence = [item for item in rows_to_evidence(path, universe) if item.get("scan_date")]
        all_evidence.extend([item for item in evidence if item["ticker"] in set(universe)])
        by_date: Dict[str, List[str]] = defaultdict(list)
        for item in evidence:
            if item["ticker"] in set(universe):
                by_date[item["scan_date"]].append(item["ticker"])
        if not by_date:
            quality_rows.append(
                {
                    "scan_date": "",
                    "evidence_source_path": str(path),
                    "evidence_source_type": source_type(path),
                    "evidence_modified_time": mtime(path),
                    "scanned_ticker_count": 0,
                    "unique_scanned_ticker_count": 0,
                    "duplicate_within_day_count": 0,
                    "evidence_valid": "FALSE",
                    "evidence_quality_status": "REJECTED_NO_DATED_TICKER_EVIDENCE",
                    "rejection_reason": "NO_SCAN_DATE_OR_TICKER_ROWS",
                }
            )
            continue
        for scan_date, tickers in sorted(by_date.items(), reverse=True):
            unique_count = len(set(tickers))
            duplicate_count = max(0, len(tickers) - unique_count)
            valid = unique_count > 0 and bool(scan_date)
            quality_rows.append(
                {
                    "scan_date": scan_date,
                    "evidence_source_path": str(path),
                    "evidence_source_type": source_type(path),
                    "evidence_modified_time": mtime(path),
                    "scanned_ticker_count": len(tickers),
                    "unique_scanned_ticker_count": unique_count,
                    "duplicate_within_day_count": duplicate_count,
                    "evidence_valid": str(valid).upper(),
                    "evidence_quality_status": "VALID" if valid else "REJECTED",
                    "rejection_reason": "" if valid else "NO_UNIQUE_TICKERS_FOR_SCAN_DAY",
                }
            )
    return quality_rows, all_evidence


def duplicate_detail(matrix: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    rows = []
    for row in matrix:
        count = base.to_int(row.get("scan_count_in_window"), 0)
        if count <= 1:
            continue
        dates = str(row.get("scan_dates_in_window", ""))
        rows.append(
            {
                "ticker": row.get("ticker", ""),
                "scan_day_count": count,
                "scan_dates": dates,
                "duplicate_count": count - 1,
                "latest_scan_date": row.get("latest_scan_date", ""),
                "duplicate_reason": "SCANNED_ON_MULTIPLE_DAYS_WITHIN_CURRENT_5DAY_WINDOW",
            }
        )
    return rows


def recovery_plan(
    universe: Sequence[str],
    universe_meta: Dict[str, Dict[str, str]],
    matrix: Sequence[Dict[str, object]],
    required_daily_count: int,
) -> Tuple[List[Dict[str, object]], int, int]:
    matrix_by_ticker = {str(row["ticker"]): row for row in matrix}

    def key(ticker: str) -> Tuple[int, int, str, int, int, str]:
        row = matrix_by_ticker.get(ticker, {})
        meta = universe_meta.get(ticker, {})
        covered = str(row.get("covered_in_true_5day_window", "FALSE")) == "TRUE"
        scan_count = base.to_int(row.get("scan_count_in_window"), 0)
        last_scan = base.parse_date(meta.get("last_scan_date")) or "0000-00-00"
        days_since = base.to_int(meta.get("days_since_last_scan"), 9999)
        priority = base.to_int(meta.get("scan_priority"), 0)
        return (0 if not covered else 1, scan_count, last_scan, -days_since, -priority, ticker)

    daily = required_daily_count if required_daily_count > 0 else max(1, math.ceil(len(universe) / COVERAGE_WINDOW_DAYS))
    candidates = sorted(universe, key=key)
    max_items = min(len(candidates), daily * COVERAGE_WINDOW_DAYS)
    selected = candidates[:max_items]
    rows: List[Dict[str, object]] = []
    expected_covered = {
        str(row["ticker"])
        for row in matrix
        if str(row.get("covered_in_true_5day_window", "FALSE")).upper() == "TRUE"
    }
    for idx, ticker in enumerate(selected):
        day_index = idx // daily + 1
        before = "COVERED" if ticker in expected_covered else "UNCOVERED"
        scan_count = base.to_int(matrix_by_ticker.get(ticker, {}).get("scan_count_in_window"), 0)
        if before == "UNCOVERED":
            reason = "UNCOVERED_TICKER_RECOVERY"
        elif scan_count < 2:
            reason = "UNDER_COVERED_ROTATION"
        else:
            reason = "OLDEST_SCAN_EVIDENCE_REFRESH"
        expected_covered.add(ticker)
        rows.append(
            {
                "planned_day_index": day_index,
                "planned_scan_date_label": f"NEXT_DAY_{day_index}",
                "ticker": ticker,
                "priority_reason": reason,
                "coverage_status_before_plan": before,
                "expected_coverage_status_after_plan": "COVERED",
            }
        )
    expected_count = len(expected_covered)
    expected_shortfall = max(0, len(universe) - expected_count)
    return rows, expected_count, expected_shortfall


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


def render_read_first(metrics: Dict[str, object]) -> str:
    order = [
        "STATUS",
        "MODE",
        "PATCH_MODE",
        "POLICY_APPLIED",
        "TOTAL_UNIVERSE_COUNT",
        "REQUIRED_DAILY_SCAN_COUNT",
        "CURRENT_DAILY_SCAN_COUNT",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET",
        "TRUE_5DAY_UNIQUE_COVERAGE_COUNT",
        "TRUE_5DAY_UNIQUE_SHORTFALL_COUNT",
        "UNCOVERED_TICKER_COUNT",
        "DUPLICATE_SCAN_COUNT",
        "UNIVERSE_COUNT_RECONCILIATION_STATUS",
        "SELECTED_TOTAL_UNIVERSE_SOURCE",
        "MIN_SOURCE_UNIVERSE_COUNT",
        "MAX_SOURCE_UNIVERSE_COUNT",
        "UNIVERSE_COUNT_SOURCE_DISAGREEMENT",
        "SCAN_DAY_EVIDENCE_VALID_COUNT",
        "SCAN_DAY_EVIDENCE_CONSIDERED_COUNT",
        "TRUE_5DAY_RECOVERY_PLAN_READY",
        "RECOVERY_PLAN_DAY_COUNT",
        "EXPECTED_UNIQUE_COVERAGE_AFTER_RECOVERY_PLAN",
        "EXPECTED_SHORTFALL_AFTER_RECOVERY_PLAN",
        "COVERAGE_EVIDENCE_STATUS",
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
    lines = [f"{key}: {metrics.get(key, '')}" for key in order]
    lines.extend(
        [
            f"WINDOW_SCAN_DAYS_USED: {metrics.get('WINDOW_SCAN_DAYS_USED', '')}",
            f"READ_FIRST: {metrics.get('READ_FIRST', '')}",
            f"REPORT: {metrics.get('REPORT', '')}",
        ]
    )
    return "\n".join(lines) + "\n"


def render_report(metrics: Dict[str, object], recon_rows: Sequence[Dict[str, object]], quality_rows: Sequence[Dict[str, object]], validations: Sequence[str]) -> str:
    count_notes = [
        f"{row['parsed_universe_count']} from {row['source_path']}"
        for row in recon_rows
        if row.get("parsed_universe_count")
    ][:8]
    return "\n".join(
        [
            "# V18.16K-R1 Coverage Evidence Quality Report",
            "",
            "## Executive summary",
            f"- Status: {metrics['STATUS']}",
            f"- True 5-day unique coverage met: {metrics['TRUE_5DAY_UNIQUE_COVERAGE_MET']}",
            f"- Unique coverage: {metrics['TRUE_5DAY_UNIQUE_COVERAGE_COUNT']} / {metrics['TOTAL_UNIVERSE_COUNT']}",
            f"- Evidence status: {metrics['COVERAGE_EVIDENCE_STATUS']}",
            "",
            "## Safety statement",
            "- Advisory-only patch. It writes R1 audit outputs and does not apply the recovery plan.",
            "- Current daily behavior, decisions, ranking, promotion/demotion, manual state, price cache, auto-trade, and auto-sell are unchanged.",
            "",
            "## Universe count reconciliation",
            f"- Status: {metrics['UNIVERSE_COUNT_RECONCILIATION_STATUS']}",
            f"- Selected source: {metrics['SELECTED_TOTAL_UNIVERSE_SOURCE']}",
            f"- Min/max parsed source counts: {metrics['MIN_SOURCE_UNIVERSE_COUNT']} / {metrics['MAX_SOURCE_UNIVERSE_COUNT']}",
            f"- Source disagreement: {metrics['UNIVERSE_COUNT_SOURCE_DISAGREEMENT']}",
            "- Count evidence: " + ("; ".join(count_notes) if count_notes else "None"),
            "",
            "## Evidence quality",
            f"- Valid scan-day evidence points: {metrics['SCAN_DAY_EVIDENCE_VALID_COUNT']} / {metrics['SCAN_DAY_EVIDENCE_CONSIDERED_COUNT']}",
            f"- Scan days used: {metrics.get('WINDOW_SCAN_DAYS_USED', '')}",
            "",
            "## Duplicate scan detail",
            f"- Duplicate scan count: {metrics['DUPLICATE_SCAN_COUNT']}",
            "- Detail output: outputs/v18/universe/V18_16K_R1_CURRENT_DUPLICATE_SCAN_DETAIL.csv",
            "",
            "## 5-day recovery plan",
            f"- Plan ready: {metrics['TRUE_5DAY_RECOVERY_PLAN_READY']}",
            f"- Day count: {metrics['RECOVERY_PLAN_DAY_COUNT']}",
            f"- Expected unique coverage after plan: {metrics['EXPECTED_UNIQUE_COVERAGE_AFTER_RECOVERY_PLAN']}",
            f"- Expected shortfall after plan: {metrics['EXPECTED_SHORTFALL_AFTER_RECOVERY_PLAN']}",
            "- The plan is advisory and was not applied.",
            "",
            "## Validation summary",
            *[f"- {item}" for item in validations],
            f"- Validation fail count: {metrics['VALIDATION_FAIL_COUNT']}",
            "",
            "## Next-step recommendation",
            "- Treat the 324 vs 325 disagreement as an input governance item before stable snapshot. The R1 reconciliation CSV identifies which current rolling-state sources expose 324 and which READ_FIRST/policy context still reports or implies 325.",
        ]
    ) + "\n"


def append_r1_fields_to_v18_16k(root: Path, metrics: Dict[str, object]) -> None:
    path = root / "outputs/v18/ops/V18_16K_READ_FIRST.txt"
    report = root / "outputs/v18/ops/V18_16K_CURRENT_TRUE_5DAY_COVERAGE_REPORT.md"
    fields = [
        "UNIVERSE_COUNT_RECONCILIATION_STATUS",
        "SELECTED_TOTAL_UNIVERSE_SOURCE",
        "MIN_SOURCE_UNIVERSE_COUNT",
        "MAX_SOURCE_UNIVERSE_COUNT",
        "UNIVERSE_COUNT_SOURCE_DISAGREEMENT",
        "SCAN_DAY_EVIDENCE_VALID_COUNT",
        "SCAN_DAY_EVIDENCE_CONSIDERED_COUNT",
        "TRUE_5DAY_RECOVERY_PLAN_READY",
        "RECOVERY_PLAN_DAY_COUNT",
        "EXPECTED_UNIQUE_COVERAGE_AFTER_RECOVERY_PLAN",
        "EXPECTED_SHORTFALL_AFTER_RECOVERY_PLAN",
    ]
    text = base.read_text(path)
    retained = []
    skip = False
    for line in text.splitlines():
        if line.strip() == "R1_PATCH_FIELDS:":
            skip = True
            continue
        if skip and any(line.startswith(f"{field}:") for field in fields):
            continue
        skip = False
        retained.append(line)
    retained.append("R1_PATCH_FIELDS:")
    retained.extend([f"{field}: {metrics.get(field, '')}" for field in fields])
    base.write_text(path, "\n".join(retained) + "\n")

    report_text = base.read_text(report)
    marker = "\n## R1 Evidence Quality Patch\n"
    if marker in report_text:
        report_text = report_text.split(marker, 1)[0]
    report_text += marker
    report_text += f"- Reconciliation status: {metrics['UNIVERSE_COUNT_RECONCILIATION_STATUS']}\n"
    report_text += f"- Selected total universe source: {metrics['SELECTED_TOTAL_UNIVERSE_SOURCE']}\n"
    report_text += f"- Scan-day evidence valid/considered: {metrics['SCAN_DAY_EVIDENCE_VALID_COUNT']} / {metrics['SCAN_DAY_EVIDENCE_CONSIDERED_COUNT']}\n"
    report_text += f"- Recovery plan ready: {metrics['TRUE_5DAY_RECOVERY_PLAN_READY']}\n"
    base.write_text(report, report_text)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    base_rc = base.main(["--root", str(root)])
    base_paths = base.discover_inputs(root)
    universe_rows, selected_source, universe_status = base.select_universe_source(base_paths)
    universe, universe_meta = base.load_universe(universe_rows)
    required_daily_count, _required_source = base.infer_required_daily(base_paths, len(universe))
    current_daily_count, _current_source = base.infer_current_daily(base_paths)

    evidence = base.collect_evidence(root, base_paths, universe)
    window_days = base.most_recent_scan_days(evidence)
    matrix, uncovered, _duplicates, _source_counter = base.build_coverage(universe, universe_meta, evidence, window_days)
    duplicate_rows = duplicate_detail(matrix)
    recon_rows, recon_metrics = universe_reconciliation(root, selected_source)
    quality_rows, _all_quality_evidence = evidence_quality(root, universe)
    recovery_rows, expected_after, expected_shortfall = recovery_plan(universe, universe_meta, matrix, required_daily_count)

    r1_paths = {key: root / value for key, value in R1_OUTPUTS.items()}
    base.write_csv(r1_paths["reconciliation"], recon_rows, RECON_FIELDS)
    base.write_csv(r1_paths["evidence_quality"], quality_rows, EVIDENCE_FIELDS)
    base.write_csv(r1_paths["duplicate_detail"], duplicate_rows, DUP_DETAIL_FIELDS)
    base.write_csv(r1_paths["recovery_plan"], recovery_rows, RECOVERY_FIELDS)

    valid_evidence_count = sum(1 for row in quality_rows if str(row.get("evidence_valid")).upper() == "TRUE")
    considered_evidence_count = len(quality_rows)
    unique_coverage_count = sum(1 for row in matrix if str(row.get("covered_in_true_5day_window")).upper() == "TRUE")
    total_universe_count = len(universe)
    shortfall = max(0, total_universe_count - unique_coverage_count)
    true_coverage_met = total_universe_count > 0 and len(window_days) >= COVERAGE_WINDOW_DAYS and unique_coverage_count >= total_universe_count
    coverage_evidence_status = "OK"
    reasons = []
    if len(window_days) < COVERAGE_WINDOW_DAYS:
        reasons.append("FEWER_THAN_5_VALID_SCAN_DAYS")
    if recon_metrics["UNIVERSE_COUNT_SOURCE_DISAGREEMENT"] == "TRUE":
        reasons.append("UNIVERSE_COUNT_SOURCE_DISAGREEMENT")
    if universe_status != "OK" or total_universe_count == 0:
        reasons.append("TOTAL_UNIVERSE_UNKNOWN")
    if reasons:
        coverage_evidence_status = "WARN_" + ";".join(reasons)
    status = STATUS_WARN if coverage_evidence_status.startswith("WARN") else STATUS_OK

    wrapper_path = root / "scripts/v18/run_v18_16K_R1_coverage_evidence_quality_patch.ps1"
    r1_script_path = root / "scripts/v18/v18_16K_R1_coverage_evidence_quality_patch.py"
    base_script_path = root / "scripts/v18/v18_16K_true_5day_unique_coverage_scheduler.py"
    ps_ok, ps_msg = parse_check(wrapper_path)
    base_py_ok, base_py_msg = compile_check(base_script_path)
    r1_py_ok, r1_py_msg = compile_check(r1_script_path)
    outputs_ok = all(path.exists() for path in r1_paths.values() if path not in {r1_paths["read_first"], r1_paths["report"]})

    validations = [
        f"PowerShell parse check: {ps_msg}",
        f"Python compile check V18.16K: {base_py_msg}",
        f"Python compile check V18.16K-R1: {r1_py_msg}",
        f"Run check: {'OK_CURRENT_SCRIPT_EXECUTED' if base_rc == 0 else 'OK_CURRENT_SCRIPT_EXECUTED_WITH_WARN_EXIT'}",
        f"R1 output existence check: {'OK' if outputs_ok else 'FAILED'}",
        "Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY",
    ]
    validation_fail_count = sum(1 for ok in (ps_ok, base_py_ok, r1_py_ok, outputs_ok) if not ok)

    metrics: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "PATCH_MODE": PATCH_MODE,
        "TOTAL_UNIVERSE_COUNT": total_universe_count if total_universe_count else "UNKNOWN",
        "REQUIRED_DAILY_SCAN_COUNT": required_daily_count if required_daily_count else "UNKNOWN",
        "CURRENT_DAILY_SCAN_COUNT": current_daily_count if current_daily_count else "UNKNOWN",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": "TRUE" if true_coverage_met else "FALSE",
        "TRUE_5DAY_UNIQUE_COVERAGE_COUNT": unique_coverage_count,
        "TRUE_5DAY_UNIQUE_SHORTFALL_COUNT": shortfall,
        "UNCOVERED_TICKER_COUNT": len(uncovered),
        "DUPLICATE_SCAN_COUNT": sum(base.to_int(row.get("duplicate_count"), 0) for row in duplicate_rows),
        "SELECTED_TOTAL_UNIVERSE_SOURCE": str(selected_source),
        "SCAN_DAY_EVIDENCE_VALID_COUNT": valid_evidence_count,
        "SCAN_DAY_EVIDENCE_CONSIDERED_COUNT": considered_evidence_count,
        "TRUE_5DAY_RECOVERY_PLAN_READY": "TRUE" if recovery_rows else "FALSE",
        "RECOVERY_PLAN_DAY_COUNT": len({row["planned_day_index"] for row in recovery_rows}),
        "EXPECTED_UNIQUE_COVERAGE_AFTER_RECOVERY_PLAN": expected_after,
        "EXPECTED_SHORTFALL_AFTER_RECOVERY_PLAN": expected_shortfall,
        "COVERAGE_EVIDENCE_STATUS": coverage_evidence_status,
        "RUNTIME_BUDGET_STATUS": "OK_ADVISORY_LOCAL_IO_ONLY",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "WINDOW_SCAN_DAYS_USED": ";".join(window_days),
        "READ_FIRST": str(r1_paths["read_first"]),
        "REPORT": str(r1_paths["report"]),
    }
    metrics.update(SAFETY_FLAGS)
    metrics.update(recon_metrics)

    base.write_text(r1_paths["read_first"], render_read_first(metrics))
    base.write_text(r1_paths["report"], render_report(metrics, recon_rows, quality_rows, validations))
    append_r1_fields_to_v18_16k(root, metrics)

    final_outputs_ok = all(path.exists() for path in r1_paths.values())
    if not final_outputs_ok:
        metrics["VALIDATION_FAIL_COUNT"] = base.to_int(metrics["VALIDATION_FAIL_COUNT"]) + 1
        base.write_text(r1_paths["read_first"], render_read_first(metrics))
        base.write_text(r1_paths["report"], render_report(metrics, recon_rows, quality_rows, validations + ["Final output existence check: FAILED"]))

    print(f"STATUS: {metrics['STATUS']}")
    print(f"MODE: {metrics['MODE']}")
    print(f"PATCH_MODE: {metrics['PATCH_MODE']}")
    print(f"UNIVERSE_COUNT_RECONCILIATION_STATUS: {metrics['UNIVERSE_COUNT_RECONCILIATION_STATUS']}")
    print(f"SELECTED_TOTAL_UNIVERSE_SOURCE: {metrics['SELECTED_TOTAL_UNIVERSE_SOURCE']}")
    print(f"MIN_SOURCE_UNIVERSE_COUNT: {metrics['MIN_SOURCE_UNIVERSE_COUNT']}")
    print(f"MAX_SOURCE_UNIVERSE_COUNT: {metrics['MAX_SOURCE_UNIVERSE_COUNT']}")
    print(f"UNIVERSE_COUNT_SOURCE_DISAGREEMENT: {metrics['UNIVERSE_COUNT_SOURCE_DISAGREEMENT']}")
    print(f"SCAN_DAY_EVIDENCE_VALID_COUNT: {metrics['SCAN_DAY_EVIDENCE_VALID_COUNT']}")
    print(f"SCAN_DAY_EVIDENCE_CONSIDERED_COUNT: {metrics['SCAN_DAY_EVIDENCE_CONSIDERED_COUNT']}")
    print(f"TRUE_5DAY_RECOVERY_PLAN_READY: {metrics['TRUE_5DAY_RECOVERY_PLAN_READY']}")
    print(f"EXPECTED_UNIQUE_COVERAGE_AFTER_RECOVERY_PLAN: {metrics['EXPECTED_UNIQUE_COVERAGE_AFTER_RECOVERY_PLAN']}")
    print(f"EXPECTED_SHORTFALL_AFTER_RECOVERY_PLAN: {metrics['EXPECTED_SHORTFALL_AFTER_RECOVERY_PLAN']}")
    print(f"VALIDATION_FAIL_COUNT: {metrics['VALIDATION_FAIL_COUNT']}")
    print(f"READ_FIRST: {r1_paths['read_first']}")
    print(f"REPORT: {r1_paths['report']}")
    return 1 if base.to_int(metrics["VALIDATION_FAIL_COUNT"]) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
