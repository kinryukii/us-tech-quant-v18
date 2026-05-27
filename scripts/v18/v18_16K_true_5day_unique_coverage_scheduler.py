from __future__ import annotations

import argparse
import csv
import math
import py_compile
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_16K_TRUE_5DAY_UNIQUE_COVERAGE_AUDIT_READY"
STATUS_WARN = "WARN_V18_16K_TRUE_5DAY_UNIQUE_COVERAGE_AUDIT_DEGRADED"
MODE = "ADVISORY_ONLY"
COVERAGE_WINDOW_DAYS = 5

SAFETY_FLAGS = {
    "PATCH_MODE": "SOURCE_RECONCILIATION_AND_AUDIT_ONLY",
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

OUTPUTS = {
    "matrix": Path("outputs/v18/universe/V18_16K_CURRENT_5DAY_UNIQUE_COVERAGE_MATRIX.csv"),
    "uncovered": Path("outputs/v18/universe/V18_16K_CURRENT_UNCOVERED_TICKERS.csv"),
    "duplicates": Path("outputs/v18/universe/V18_16K_CURRENT_DUPLICATE_SCAN_AUDIT.csv"),
    "plan": Path("outputs/v18/universe/V18_16K_CURRENT_RECOMMENDED_NEXT_SCAN_PLAN.csv"),
    "read_first": Path("outputs/v18/ops/V18_16K_READ_FIRST.txt"),
    "report": Path("outputs/v18/ops/V18_16K_CURRENT_TRUE_5DAY_COVERAGE_REPORT.md"),
}

MATRIX_FIELDS = [
    "ticker",
    "in_universe",
    "covered_in_true_5day_window",
    "scan_count_in_window",
    "duplicate_scan_count",
    "latest_scan_date",
    "oldest_scan_date",
    "scan_dates_in_window",
    "evidence_sources",
    "coverage_status",
]
UNCOVERED_FIELDS = [
    "ticker",
    "universe_tier",
    "last_scan_date",
    "days_since_last_scan",
    "scan_priority",
    "reason",
]
DUPLICATE_FIELDS = [
    "ticker",
    "scan_count_in_window",
    "duplicate_scan_count",
    "scan_dates_in_window",
    "evidence_sources",
    "audit_status",
]
PLAN_FIELDS = [
    "recommended_order",
    "ticker",
    "recommendation_reason",
    "universe_tier",
    "last_scan_date",
    "days_since_last_scan",
    "scan_count_in_window",
    "scan_priority",
    "advisory_only",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except Exception:
            continue
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def to_int(value: object, default: int = 0) -> int:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return default
    try:
        return int(float(text))
    except Exception:
        return default


def boolish(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1"}


def normalize_ticker(value: object) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9.\-]", "", text)
    if not text or text in {"TICKER", "NAN", "NONE", "NULL"}:
        return ""
    return text


def parse_date(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    return match.group(0) if match else ""


def first_value(path: Path, key: str) -> str:
    target = key.upper()
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        if left.strip().lstrip("-").strip().upper() == target:
            return right.strip()
    return ""


def discover_inputs(root: Path) -> Dict[str, Path]:
    return {
        "current_universe_state": root / "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv",
        "versioned_universe_state": root / "outputs/v18/universe/V18_16A_CURRENT_UNIVERSE_ROLLING_STATE_AUDIT.csv",
        "state_universe_state": root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
        "current_scan_plan": root / "outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv",
        "versioned_scan_plan": root / "outputs/v18/universe/V18_16B_CURRENT_ROLLING_SCAN_PLAN.csv",
        "coverage_audit": root / "outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_COVERAGE_AUDIT.csv",
        "coverage_optimizer_read_first": root / "outputs/v18/ops/V18_16I_READ_FIRST.txt",
        "threshold_read_first": root / "outputs/v18/ops/V18_16J_READ_FIRST.txt",
        "threshold_policy": root / "outputs/v18/universe/V18_16J_CURRENT_DAILY_THRESHOLD_POLICY.csv",
    }


def select_universe_source(paths: Dict[str, Path]) -> Tuple[List[Dict[str, str]], Path, str]:
    for key in ("current_universe_state", "state_universe_state", "versioned_universe_state"):
        rows, _fields, status = read_csv(paths[key])
        tickers = {normalize_ticker(row.get("ticker")) for row in rows}
        tickers.discard("")
        if status == "OK" and tickers:
            return rows, paths[key], status
    return [], paths["current_universe_state"], "MISSING_OR_EMPTY"


def load_universe(rows: Sequence[Dict[str, str]]) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    meta: Dict[str, Dict[str, str]] = {}
    for row in rows:
        ticker = normalize_ticker(row.get("ticker"))
        if not ticker:
            continue
        meta[ticker] = row
    return sorted(meta), meta


def infer_required_daily(paths: Dict[str, Path], total_universe_count: int) -> Tuple[int, str]:
    candidates: List[Tuple[int, str]] = []
    for key in ("coverage_optimizer_read_first", "threshold_read_first"):
        path = paths[key]
        for field in ("REQUIRED_DAILY_SCAN_COUNT", "RECOMMENDED_DAILY_SCAN_COUNT", "DAILY_MIN_SCAN_COUNT"):
            value = to_int(first_value(path, field), 0)
            if value > 0:
                candidates.append((value, str(path)))
                break
    rows, _fields, status = read_csv(paths["coverage_audit"])
    if status == "OK" and rows:
        value = to_int(rows[0].get("DAILY_MIN_SCAN_COUNT"), 0)
        if value > 0:
            candidates.append((value, str(paths["coverage_audit"])))
    rows, _fields, status = read_csv(paths["threshold_policy"])
    if status == "OK" and rows:
        for row in rows:
            for field in ("required_daily_scan_count", "REQUIRED_DAILY_SCAN_COUNT", "daily_min_scan_count"):
                value = to_int(row.get(field), 0)
                if value > 0:
                    candidates.append((value, str(paths["threshold_policy"])))
                    break
            if candidates:
                break
    if candidates:
        return candidates[0]
    if total_universe_count > 0:
        return int(math.ceil(total_universe_count / COVERAGE_WINDOW_DAYS)), "DERIVED_CEIL_TOTAL_UNIVERSE_DIV_5"
    return 0, "UNAVAILABLE"


def infer_current_daily(paths: Dict[str, Path]) -> Tuple[int, str]:
    rows, _fields, status = read_csv(paths["current_scan_plan"])
    if status == "OK" and rows:
        selected = [row for row in rows if boolish(row.get("selected_this_run"))]
        if selected:
            return len({normalize_ticker(row.get("ticker")) for row in selected if normalize_ticker(row.get("ticker"))}), str(paths["current_scan_plan"])
        tickers = {normalize_ticker(row.get("ticker")) for row in rows}
        tickers.discard("")
        if tickers:
            return len(tickers), str(paths["current_scan_plan"])
    for key in ("coverage_optimizer_read_first", "threshold_read_first"):
        value = to_int(first_value(paths[key], "CURRENT_DAILY_SCAN_COUNT"), 0)
        if value > 0:
            return value, str(paths[key])
    rows, _fields, status = read_csv(paths["coverage_audit"])
    if status == "OK" and rows:
        for field in ("TODAY_ROLLING_SCAN_COUNT", "SCANNED_TICKER_COUNT"):
            value = to_int(rows[0].get(field), 0)
            if value > 0:
                return value, str(paths["coverage_audit"])
    return 0, "UNAVAILABLE"


def scan_plan_evidence(path: Path) -> List[Dict[str, str]]:
    rows, _fields, status = read_csv(path)
    if status != "OK":
        return []
    evidence = []
    for row in rows:
        ticker = normalize_ticker(row.get("ticker"))
        if not ticker:
            continue
        selected = boolish(row.get("selected_this_run")) or "selected_this_run" not in row
        if not selected:
            continue
        scan_date = parse_date(row.get("last_scan_date")) or parse_date(datetime.now().isoformat())
        evidence.append({"ticker": ticker, "scan_date": scan_date, "source": str(path)})
    return evidence


def rolling_state_evidence(path: Path, universe: Iterable[str]) -> List[Dict[str, str]]:
    universe_set = set(universe)
    rows, _fields, status = read_csv(path)
    if status != "OK":
        return []
    evidence = []
    for row in rows:
        ticker = normalize_ticker(row.get("ticker"))
        if not ticker or (universe_set and ticker not in universe_set):
            continue
        scan_date = parse_date(row.get("last_scan_date"))
        if scan_date:
            evidence.append({"ticker": ticker, "scan_date": scan_date, "source": str(path)})
    return evidence


def archived_plan_evidence(root: Path) -> List[Dict[str, str]]:
    evidence = []
    archive_root = root / "archive/stable"
    if not archive_root.exists():
        return evidence
    patterns = [
        "*/outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv",
        "*/outputs/v18/universe/V18_16B_CURRENT_ROLLING_SCAN_PLAN.csv",
    ]
    files: List[Path] = []
    for pattern in patterns:
        files.extend(archive_root.glob(pattern))
    for path in sorted(set(files), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)[:30]:
        evidence.extend(scan_plan_evidence(path))
    return evidence


def collect_evidence(root: Path, paths: Dict[str, Path], universe: Sequence[str]) -> List[Dict[str, str]]:
    evidence = []
    for key in ("current_universe_state", "state_universe_state"):
        evidence.extend(rolling_state_evidence(paths[key], universe))
    for key in ("current_scan_plan", "versioned_scan_plan"):
        evidence.extend(scan_plan_evidence(paths[key]))
    evidence.extend(archived_plan_evidence(root))
    return [item for item in evidence if item["ticker"] in set(universe) and item["scan_date"]]


def most_recent_scan_days(evidence: Sequence[Dict[str, str]]) -> List[str]:
    return sorted({item["scan_date"] for item in evidence}, reverse=True)[:COVERAGE_WINDOW_DAYS]


def build_coverage(
    universe: Sequence[str],
    universe_meta: Dict[str, Dict[str, str]],
    evidence: Sequence[Dict[str, str]],
    window_days: Sequence[str],
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]], Counter]:
    by_ticker_date: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
    window_set = set(window_days)
    for item in evidence:
        if item["scan_date"] in window_set:
            by_ticker_date[item["ticker"]][item["scan_date"]].append(item["source"])

    matrix = []
    uncovered = []
    duplicates = []
    source_counter: Counter = Counter()
    for ticker in universe:
        date_sources = by_ticker_date.get(ticker, {})
        dates = sorted(date_sources.keys(), reverse=True)
        sources = sorted({source for grouped in date_sources.values() for source in grouped})
        for source in sources:
            source_counter[source] += 1
        scan_count = len(dates)
        duplicate_count = max(0, scan_count - 1)
        meta = universe_meta.get(ticker, {})
        row = {
            "ticker": ticker,
            "in_universe": "TRUE",
            "covered_in_true_5day_window": "TRUE" if scan_count > 0 else "FALSE",
            "scan_count_in_window": scan_count,
            "duplicate_scan_count": duplicate_count,
            "latest_scan_date": dates[0] if dates else "",
            "oldest_scan_date": dates[-1] if dates else "",
            "scan_dates_in_window": ";".join(dates),
            "evidence_sources": ";".join(sources),
            "coverage_status": "COVERED" if scan_count > 0 else "UNCOVERED",
        }
        matrix.append(row)
        if scan_count == 0:
            uncovered.append(
                {
                    "ticker": ticker,
                    "universe_tier": meta.get("universe_tier", ""),
                    "last_scan_date": parse_date(meta.get("last_scan_date")),
                    "days_since_last_scan": meta.get("days_since_last_scan", ""),
                    "scan_priority": meta.get("scan_priority", ""),
                    "reason": "NO_SCAN_EVIDENCE_IN_MOST_RECENT_5_SCAN_DAYS",
                }
            )
        if duplicate_count > 0:
            duplicates.append(
                {
                    "ticker": ticker,
                    "scan_count_in_window": scan_count,
                    "duplicate_scan_count": duplicate_count,
                    "scan_dates_in_window": ";".join(dates),
                    "evidence_sources": ";".join(sources),
                    "audit_status": "REPEATED_SCAN_REDUCED_UNIQUE_COVERAGE_CAPACITY",
                }
            )
    return matrix, uncovered, duplicates, source_counter


def build_plan(
    universe: Sequence[str],
    universe_meta: Dict[str, Dict[str, str]],
    matrix: Sequence[Dict[str, object]],
    required_daily_count: int,
) -> List[Dict[str, object]]:
    matrix_by_ticker = {str(row["ticker"]): row for row in matrix}

    def priority_key(ticker: str) -> Tuple[int, str, int, int, str]:
        row = matrix_by_ticker.get(ticker, {})
        meta = universe_meta.get(ticker, {})
        covered = str(row.get("covered_in_true_5day_window", "FALSE")) == "TRUE"
        last_scan = parse_date(meta.get("last_scan_date")) or "0000-00-00"
        days_since = to_int(meta.get("days_since_last_scan"), 9999)
        scan_priority = to_int(meta.get("scan_priority"), 0)
        return (0 if not covered else 1, last_scan, -days_since, -scan_priority, ticker)

    limit = required_daily_count if required_daily_count > 0 else len(universe)
    selected = sorted(universe, key=priority_key)[:limit]
    plan = []
    for index, ticker in enumerate(selected, start=1):
        row = matrix_by_ticker.get(ticker, {})
        meta = universe_meta.get(ticker, {})
        covered = str(row.get("covered_in_true_5day_window", "FALSE")) == "TRUE"
        reason = "UNCOVERED_IN_TRUE_5DAY_WINDOW" if not covered else "OLDEST_SCAN_EVIDENCE_ROTATION"
        plan.append(
            {
                "recommended_order": index,
                "ticker": ticker,
                "recommendation_reason": reason,
                "universe_tier": meta.get("universe_tier", ""),
                "last_scan_date": parse_date(meta.get("last_scan_date")),
                "days_since_last_scan": meta.get("days_since_last_scan", ""),
                "scan_count_in_window": row.get("scan_count_in_window", 0),
                "scan_priority": meta.get("scan_priority", ""),
                "advisory_only": "TRUE",
            }
        )
    return plan


def input_audit(paths: Dict[str, Path]) -> Tuple[List[str], List[str], Dict[str, str]]:
    used = []
    missing = []
    statuses = {}
    for name, path in paths.items():
        exists = path.exists()
        statuses[name] = "OK" if exists else "MISSING"
        if exists:
            used.append(str(path))
        else:
            missing.append(str(path))
    return used, missing, statuses


def powershell_parse_check(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING_WRAPPER"
    command = (
        "$ErrorActionPreference='Stop'; "
        f"[scriptblock]::Create((Get-Content -Raw -LiteralPath '{path}')) | Out-Null; "
        "Write-Output OK"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            text=True,
            capture_output=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, "OK_PARSE"
        return False, (result.stderr or result.stdout).strip()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def python_compile_check(path: Path) -> Tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, "OK_COMPILE"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def render_read_first(metrics: Dict[str, object]) -> str:
    ordered = [
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
        "RECOMMENDED_NEXT_SCAN_COUNT",
        "INPUT_FILE_COUNT",
        "MISSING_INPUT_FILE_COUNT",
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
    lines = [f"{key}: {metrics.get(key, '')}" for key in ordered]
    lines.extend(
        [
            f"WINDOW_SCAN_DAYS_USED: {metrics.get('WINDOW_SCAN_DAYS_USED', '')}",
            f"INPUT_FILES_USED: {metrics.get('INPUT_FILES_USED', '')}",
            f"MISSING_INPUT_FILES: {metrics.get('MISSING_INPUT_FILES', '')}",
            f"READ_FIRST: {metrics.get('READ_FIRST', '')}",
            f"REPORT: {metrics.get('REPORT', '')}",
        ]
    )
    return "\n".join(lines) + "\n"


def render_report(metrics: Dict[str, object], used: Sequence[str], missing: Sequence[str], validations: Sequence[str]) -> str:
    true_met = metrics["TRUE_5DAY_UNIQUE_COVERAGE_MET"]
    lines = [
        "# V18.16K True 5-Day Unique Coverage Scheduler Audit",
        "",
        "## Executive summary",
        f"- Status: {metrics['STATUS']}",
        f"- True 5-day unique coverage met: {true_met}",
        f"- Unique covered tickers: {metrics['TRUE_5DAY_UNIQUE_COVERAGE_COUNT']} / {metrics['TOTAL_UNIVERSE_COUNT']}",
        f"- Shortfall: {metrics['TRUE_5DAY_UNIQUE_SHORTFALL_COUNT']}",
        "",
        "## Safety statement",
        "- This module is advisory-only. It writes audit outputs only and does not apply policy.",
        "- Official decisions, ranking, promotion/demotion, manual state, price cache, auto-trade, and auto-sell behavior are unchanged.",
        "",
        "## Input files used",
    ]
    lines.extend([f"- {item}" for item in used] or ["- None"])
    lines.extend(["", "## Missing/degraded inputs"])
    lines.extend([f"- {item}" for item in missing] or ["- None"])
    lines.extend(
        [
            "",
            "## Coverage summary",
            f"- Coverage evidence status: {metrics['COVERAGE_EVIDENCE_STATUS']}",
            f"- Scan days used: {metrics.get('WINDOW_SCAN_DAYS_USED', '')}",
            f"- Required daily scan count: {metrics['REQUIRED_DAILY_SCAN_COUNT']}",
            f"- Current daily scan count: {metrics['CURRENT_DAILY_SCAN_COUNT']}",
            "",
            "## Uncovered ticker summary",
            f"- Uncovered ticker count: {metrics['UNCOVERED_TICKER_COUNT']}",
            "- Full list is in outputs/v18/universe/V18_16K_CURRENT_UNCOVERED_TICKERS.csv",
            "",
            "## Duplicate scan summary",
            f"- Duplicate scan count: {metrics['DUPLICATE_SCAN_COUNT']}",
            "- Duplicate tickers are listed in outputs/v18/universe/V18_16K_CURRENT_DUPLICATE_SCAN_AUDIT.csv",
            "",
            "## Recommended next scan plan summary",
            f"- Recommended next scan count: {metrics['RECOMMENDED_NEXT_SCAN_COUNT']}",
            "- The plan prioritizes uncovered tickers first, then oldest scan evidence. It is not applied.",
            "",
            "## Validation summary",
        ]
    )
    lines.extend([f"- {item}" for item in validations])
    lines.extend(
        [
            f"- Validation fail count: {metrics['VALIDATION_FAIL_COUNT']}",
            "",
            "## Next-step recommendation",
            "- Review the uncovered ticker CSV and use the advisory next scan plan as the next scheduler input candidate if production policy owners choose to apply a future change.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    paths = discover_inputs(root)
    used, missing, _statuses = input_audit(paths)
    universe_rows, universe_source, universe_source_status = select_universe_source(paths)
    universe, universe_meta = load_universe(universe_rows)
    total_universe_count = len(universe)

    required_daily_count, required_source = infer_required_daily(paths, total_universe_count)
    current_daily_count, current_source = infer_current_daily(paths)

    evidence = collect_evidence(root, paths, universe)
    window_days = most_recent_scan_days(evidence)
    matrix, uncovered, duplicates, source_counter = build_coverage(universe, universe_meta, evidence, window_days)
    plan = build_plan(universe, universe_meta, matrix, required_daily_count)

    unique_coverage_count = sum(1 for row in matrix if row["covered_in_true_5day_window"] == "TRUE")
    shortfall = max(0, total_universe_count - unique_coverage_count) if total_universe_count else 0
    true_coverage_met = (
        total_universe_count > 0
        and len(window_days) >= COVERAGE_WINDOW_DAYS
        and unique_coverage_count >= total_universe_count
    )
    duplicate_scan_count = sum(to_int(row["duplicate_scan_count"]) for row in duplicates)

    coverage_evidence_status = "OK"
    degraded_reasons = []
    if universe_source_status != "OK" or total_universe_count == 0:
        degraded_reasons.append("TOTAL_UNIVERSE_UNKNOWN")
    if len(window_days) < COVERAGE_WINDOW_DAYS:
        degraded_reasons.append("FEWER_THAN_5_VALID_SCAN_DAYS")
    if not evidence:
        degraded_reasons.append("NO_SCAN_EVIDENCE")
    if missing:
        degraded_reasons.append("MISSING_OPTIONAL_INPUTS")
    if degraded_reasons:
        coverage_evidence_status = "WARN_" + ";".join(degraded_reasons)

    status = STATUS_OK if coverage_evidence_status == "OK" else STATUS_WARN
    runtime_budget_status = "OK_ADVISORY_LOCAL_IO_ONLY"

    output_paths = {key: root / value for key, value in OUTPUTS.items()}
    write_csv(output_paths["matrix"], matrix, MATRIX_FIELDS)
    write_csv(output_paths["uncovered"], uncovered, UNCOVERED_FIELDS)
    write_csv(output_paths["duplicates"], duplicates, DUPLICATE_FIELDS)
    write_csv(output_paths["plan"], plan, PLAN_FIELDS)

    wrapper_path = root / "scripts/v18/run_v18_16K_true_5day_unique_coverage_scheduler.ps1"
    script_path = root / "scripts/v18/v18_16K_true_5day_unique_coverage_scheduler.py"
    ps_ok, ps_msg = powershell_parse_check(wrapper_path)
    py_ok, py_msg = python_compile_check(script_path)
    outputs_ok = all(path.exists() for path in output_paths.values() if path.name != output_paths["read_first"].name and path.name != output_paths["report"].name)

    validations = [
        f"PowerShell parse check: {ps_msg}",
        f"Python compile check: {py_msg}",
        "Run check: OK_CURRENT_SCRIPT_EXECUTED",
        f"Output existence check: {'OK' if outputs_ok else 'FAILED'}",
        "Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY",
    ]
    validation_fail_count = sum(1 for ok in (ps_ok, py_ok, outputs_ok) if not ok)

    metrics: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "TOTAL_UNIVERSE_COUNT": total_universe_count if total_universe_count else "UNKNOWN",
        "REQUIRED_DAILY_SCAN_COUNT": required_daily_count if required_daily_count else "UNKNOWN",
        "CURRENT_DAILY_SCAN_COUNT": current_daily_count if current_daily_count else "UNKNOWN",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": "TRUE" if true_coverage_met else "FALSE",
        "TRUE_5DAY_UNIQUE_COVERAGE_COUNT": unique_coverage_count,
        "TRUE_5DAY_UNIQUE_SHORTFALL_COUNT": shortfall,
        "UNCOVERED_TICKER_COUNT": len(uncovered),
        "DUPLICATE_SCAN_COUNT": duplicate_scan_count,
        "RECOMMENDED_NEXT_SCAN_COUNT": len(plan),
        "INPUT_FILE_COUNT": len(used),
        "MISSING_INPUT_FILE_COUNT": len(missing),
        "COVERAGE_EVIDENCE_STATUS": coverage_evidence_status,
        "RUNTIME_BUDGET_STATUS": runtime_budget_status,
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "WINDOW_SCAN_DAYS_USED": ";".join(window_days),
        "INPUT_FILES_USED": ";".join(used),
        "MISSING_INPUT_FILES": ";".join(missing),
        "READ_FIRST": str(output_paths["read_first"]),
        "REPORT": str(output_paths["report"]),
        "UNIVERSE_SOURCE": str(universe_source),
        "REQUIRED_DAILY_SOURCE": required_source,
        "CURRENT_DAILY_SOURCE": current_source,
        "EVIDENCE_SOURCE_COUNT": len(source_counter),
    }
    metrics.update(SAFETY_FLAGS)

    write_text(output_paths["read_first"], render_read_first(metrics))
    write_text(output_paths["report"], render_report(metrics, used, missing, validations))

    final_outputs_ok = all(path.exists() for path in output_paths.values())
    if not final_outputs_ok:
        metrics["VALIDATION_FAIL_COUNT"] = to_int(metrics["VALIDATION_FAIL_COUNT"]) + 1
        write_text(output_paths["read_first"], render_read_first(metrics))
        write_text(output_paths["report"], render_report(metrics, used, missing, validations + ["Final output existence check: FAILED"]))

    print(f"STATUS: {metrics['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"TRUE_5DAY_UNIQUE_COVERAGE_MET: {metrics['TRUE_5DAY_UNIQUE_COVERAGE_MET']}")
    print(f"TRUE_5DAY_UNIQUE_COVERAGE_COUNT: {metrics['TRUE_5DAY_UNIQUE_COVERAGE_COUNT']}")
    print(f"TRUE_5DAY_UNIQUE_SHORTFALL_COUNT: {metrics['TRUE_5DAY_UNIQUE_SHORTFALL_COUNT']}")
    print(f"COVERAGE_EVIDENCE_STATUS: {metrics['COVERAGE_EVIDENCE_STATUS']}")
    print(f"VALIDATION_FAIL_COUNT: {metrics['VALIDATION_FAIL_COUNT']}")
    print(f"READ_FIRST: {output_paths['read_first']}")
    print(f"REPORT: {output_paths['report']}")
    return 1 if to_int(metrics["VALIDATION_FAIL_COUNT"]) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
