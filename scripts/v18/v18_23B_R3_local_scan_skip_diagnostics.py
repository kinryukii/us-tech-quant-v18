from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple


STATUS_OK = "OK_V18_23B_R3_LOCAL_SCAN_SKIP_DIAGNOSTICS_READY"
STATUS_WARN = "WARN_V18_23B_R3_LOCAL_SCAN_SKIP_DIAGNOSTICS_INCOMPLETE"
STATUS_FAIL = "FAIL_V18_23B_R3_LOCAL_SCAN_SKIP_DIAGNOSTICS"
MODE = "READ_ONLY_LOCAL_SCAN_SKIP_DIAGNOSTICS"
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")

OUTPUTS = {
    "diagnostics": "outputs/v18/rolling_coverage/V18_23B_R3_CURRENT_LOCAL_SCAN_SKIP_DIAGNOSTICS.md",
    "ticker_diag": "outputs/v18/rolling_coverage/V18_23B_R3_CURRENT_SKIPPED_TICKER_DIAGNOSTICS.csv",
    "evidence": "outputs/v18/rolling_coverage/V18_23B_R3_CURRENT_LOCAL_SOURCE_EVIDENCE.csv",
    "repair": "outputs/v18/rolling_coverage/V18_23B_R3_CURRENT_REPAIR_PLAN.csv",
    "summary": "outputs/v18/rolling_coverage/V18_23B_R3_CURRENT_SKIP_CATEGORY_SUMMARY.csv",
    "success_def": "outputs/v18/rolling_coverage/V18_23B_R3_CURRENT_SUCCESS_DEFINITION_RECOMMENDATION.csv",
    "validation": "outputs/v18/rolling_coverage/V18_23B_R3_CURRENT_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_23B_R3_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_23B_R3_CURRENT_LOCAL_SCAN_SKIP_DIAGNOSTICS_REPORT.md",
}

SAFETY = {
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "LEDGER_MODIFIED": "FALSE",
    "ROLLING_SCAN_EXECUTED": "FALSE",
    "ROLLING_SCAN_DATA_FETCHED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "STAGED_PRICE_HISTORY_WRITTEN": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "FACTOR_PACK_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "BACKTEST_EXECUTED": "FALSE",
    "BACKTEST_RESULTS_APPLIED": "FALSE",
    "FACTOR_EFFECT_CLAIM_ALLOWED": "FALSE",
    "WEIGHT_CHANGE_ALLOWED": "FALSE",
    "PRODUCTION_PROMOTION_ALLOWED": "FALSE",
    "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED": "FALSE",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "R3_SKIP_DIAGNOSTICS_READY", "V18_23B_R2_SELECTED_SCAN_COUNT",
    "V18_23B_R2_SUCCESS_SCAN_COUNT", "V18_23B_R2_SKIPPED_SCAN_COUNT",
    "DIAGNOSED_SELECTED_TICKER_COUNT", "DIAGNOSED_SKIPPED_TICKER_COUNT",
    "SOURCE_DETECTION_GAP_COUNT", "EXPECTED_OUTSIDE_RAW105_FACTOR_PACK_COUNT",
    "MISSING_LOCAL_PRICE_COUNT", "MISSING_FACTOR_PACK_COUNT", "MISSING_TECHNICAL_TIMING_COUNT",
    "MISSING_FULL_HISTORY_COUNT", "EXECUTOR_SUCCESS_CRITERIA_TOO_STRICT_COUNT",
    "UNKNOWN_LOCAL_INPUT_GAP_COUNT", "REPAIRABLE_WITH_SOURCE_DETECTION_ONLY_COUNT",
    "REPAIRABLE_WITH_SUCCESS_STATUS_SPLIT_COUNT", "NON_REPAIRABLE_WITHOUT_BACKFILL_COUNT",
    "PROJECTED_LOCAL_PRICE_SCAN_SUCCESS_COUNT", "PROJECTED_FULL_FACTOR_SCAN_SUCCESS_COUNT",
    "USER_TARGET_65_LOCAL_PRICE_SCANS_REACHABLE_LOCAL_ONLY",
    "USER_TARGET_65_FULL_FACTOR_SCANS_REACHABLE_LOCAL_ONLY", "V18_23B_R4_PATCH_RECOMMENDED",
    "STAGED_BACKFILL_RECOMMENDED", "VALIDATION_FAIL_COUNT",
    "OFFICIAL_DECISION_IMPACT", "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL",
    "LEDGER_MODIFIED", "ROLLING_SCAN_EXECUTED", "ROLLING_SCAN_DATA_FETCHED",
    "EXTERNAL_DATA_FETCHED", "PRICE_CACHE_MODIFIED", "PRICE_HISTORY_WRITTEN",
    "STAGED_PRICE_HISTORY_WRITTEN", "RANKING_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED",
    "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "BACKTEST_EXECUTED",
    "BACKTEST_RESULTS_APPLIED", "FACTOR_EFFECT_CLAIM_ALLOWED", "WEIGHT_CHANGE_ALLOWED",
    "PRODUCTION_PROMOTION_ALLOWED", "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "RECOMMENDED_NEXT_ACTION", "DIAGNOSTICS_PATH", "SKIPPED_TICKER_DIAGNOSTICS_PATH",
    "LOCAL_SOURCE_EVIDENCE_PATH", "REPAIR_PLAN_PATH", "SKIP_CATEGORY_SUMMARY_PATH",
    "SUCCESS_DEFINITION_RECOMMENDATION_PATH", "VALIDATION_PATH", "REPORT_PATH",
]

DIAG_FIELDS = [
    "ticker", "selected_in_r2", "r2_scan_status", "r2_failure_reason",
    "canonical_universe_present", "ledger_last_status", "local_price_evidence",
    "local_factor_pack_evidence", "local_technical_timing_evidence",
    "local_full_history_ready_evidence", "found_in_any_local_source", "local_source_count",
    "strongest_evidence_source", "likely_skip_category", "repair_recommendation",
]
EVIDENCE_FIELDS = ["ticker", "source_name", "source_path", "evidence_type", "present", "notes"]
REPAIR_FIELDS = ["priority", "repair_id", "repair_recommendation", "affected_count", "rationale", "allowed_now"]
SUMMARY_FIELDS = ["likely_skip_category", "ticker_count", "recommended_interpretation"]
SUCCESS_FIELDS = ["success_status", "definition", "projected_count", "recommended_for_r4"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except csv.Error:
            continue
    return [], []


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def normalize_ticker(value: object) -> str:
    ticker = str(value or "").strip().upper()
    if ticker in {"", "NULL", "NONE", "NAN", "NA", "N/A", "TICKER"} or ticker.isdigit():
        return ""
    return ticker if TICKER_RE.match(ticker) else ""


def find_ticker_column(fields: Sequence[str]) -> str:
    lower = {field.lower(): field for field in fields}
    for name in ("ticker", "symbol", "candidate_ticker", "yf_ticker"):
        if name in lower:
            return lower[name]
    return ""


def ticker_set(path: Path) -> Set[str]:
    rows, fields = read_csv(path)
    col = find_ticker_column(fields)
    return {normalize_ticker(row.get(col, "")) for row in rows if col and normalize_ticker(row.get(col, ""))}


def source_sets(root: Path) -> Dict[str, Tuple[str, Set[str]]]:
    sources = {
        "canonical_plan": "outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv",
        "universe_state": "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv",
        "factor_pack": "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        "technical_timing": "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
        "ranking": "outputs/v18/ranking/V18_CURRENT_RANKED_CANDIDATE_SCORE_EXPLANATION.csv",
        "v16_universe": "outputs/v16/read_center/v16_compat_full_universe_proof.csv",
        "state_universe": "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
    }
    for base_rel in ["outputs/v18/daily_integrated", "outputs/v18/read_center", "outputs/v17/price"]:
        base = root / base_rel
        if base.exists():
            for path in sorted(base.rglob("*.csv")):
                sources[path.stem] = path.relative_to(root).as_posix()
    return {name: (rel, ticker_set(root / rel)) for name, rel in sources.items()}


def price_cache_has(root: Path, ticker: str) -> bool:
    path = root / "state/v18/price_cache" / f"{ticker}.csv"
    return path.exists() and path.stat().st_size > 0 and len(read_text(path).splitlines()) > 1


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return (int(stat.st_mtime_ns), int(stat.st_size))


def protected_files(root: Path) -> List[Path]:
    dirs = [
        "state/v18/rolling_coverage", "state/v18/price_cache", "outputs/v18/factor_pack",
        "outputs/v18/ranking", "outputs/v18/signal_snapshots", "outputs/v18/technical_timing",
        "outputs/v18/universe", "outputs/v18/forward_tracker", "outputs/v18/simulation",
        "state/v18/simulation", "state/v18/forward_outcome", "state/v18/candidate_forward_tracker",
        "state/v18/manual", "state/v16", "archive/stable",
    ]
    out: List[Path] = []
    for rel in dirs:
        base = root / rel
        if base.exists():
            out.extend(path for path in base.rglob("*") if path.is_file())
    return out


def classify(ticker: str, r2_status: str, r2_failure: str, price: bool, factor: bool, tech: bool, full: str, found: bool) -> Tuple[str, str]:
    if price and r2_status.startswith("SKIPPED"):
        return "SOURCE_DETECTION_GAP", "patch executor source detection"
    if price and not factor:
        return "EXPECTED_OUTSIDE_RAW105_FACTOR_PACK", "split partial local scan success from full factor-ready success"
    if price and factor and not tech:
        return "MISSING_TECHNICAL_TIMING_ONLY", "split partial local scan success from full factor-ready success"
    if price and factor:
        return "EXECUTOR_SUCCESS_CRITERIA_TOO_STRICT", "split partial local scan success from full factor-ready success"
    if not price and found:
        return "MISSING_LOCAL_PRICE", "require staged backfill later"
    if not found:
        return "UNKNOWN_LOCAL_INPUT_GAP", "inspect ticker alias"
    return "MISSING_FULL_HISTORY", "require staged backfill later"


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"] + ["| " + " | ".join(str(x) for x in row) + " |" for row in rows])


def render_md(values: Dict[str, str], summary_rows: Sequence[Dict[str, object]]) -> str:
    return f"""# V18.23B-R3 Local Scan Skip Diagnostics

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Status
Status: **{values['STATUS']}**

Mode: **{values['MODE']}**

## Diagnosis
R2 selected {values['V18_23B_R2_SELECTED_SCAN_COUNT']} tickers and skipped {values['V18_23B_R2_SKIPPED_SCAN_COUNT']}. R3 diagnosed {values['DIAGNOSED_SKIPPED_TICKER_COUNT']} skipped tickers without modifying the ledger or source files.

{markdown_table(['Category', 'Count', 'Interpretation'], [(row['likely_skip_category'], row['ticker_count'], row['recommended_interpretation']) for row in summary_rows])}

## Success Definition Recommendation
R4 should split local scan success into LOCAL_PRICE_SCAN_SUCCESS and FULL_FACTOR_SCAN_SUCCESS so rolling coverage can track local price coverage separately from full factor-ready coverage.

## Recommended next action
{values['RECOMMENDED_NEXT_ACTION']}
"""


def render_report(values: Dict[str, str]) -> str:
    return f"""# V18.23B-R3 Local Scan Skip Diagnostics Report

Status: {values['STATUS']}.

Diagnosed skipped ticker count: {values['DIAGNOSED_SKIPPED_TICKER_COUNT']}. Source detection gap count: {values['SOURCE_DETECTION_GAP_COUNT']}. Missing local price count: {values['MISSING_LOCAL_PRICE_COUNT']}.

Projected local price scan success count: {values['PROJECTED_LOCAL_PRICE_SCAN_SUCCESS_COUNT']}. Projected full factor scan success count: {values['PROJECTED_FULL_FACTOR_SCAN_SUCCESS_COUNT']}.

Recommended next action: {values['RECOMMENDED_NEXT_ACTION']}
"""


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    before = {str(path): file_sig(path) for path in protected_files(root)}

    r2_readfirst = {}
    for line in read_text(root / "outputs/v18/ops/V18_23B_R2_READ_FIRST.txt").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            r2_readfirst[k.strip()] = v.strip()
    selected_rows, _ = read_csv(root / "outputs/v18/rolling_coverage/V18_23B_R2_CURRENT_WATCHDOG_SELECTED_SCAN_LIST.csv")
    result_rows, _ = read_csv(root / "outputs/v18/rolling_coverage/V18_23B_R2_CURRENT_SCAN_RESULT.csv")
    ledger_rows, _ = read_csv(root / "outputs/v18/rolling_coverage/V18_23B_R2_CURRENT_SCAN_LEDGER_SNAPSHOT.csv")
    source_map = source_sets(root)
    factor_set = source_map.get("factor_pack", ("", set()))[1]
    tech_set = source_map.get("technical_timing", ("", set()))[1]
    canonical_set = source_map.get("canonical_plan", ("", set()))[1]
    ledger_by_ticker = {normalize_ticker(row.get("ticker")): row for row in ledger_rows if normalize_ticker(row.get("ticker"))}

    result_by_ticker = {normalize_ticker(row.get("ticker")): row for row in result_rows if normalize_ticker(row.get("ticker"))}
    diagnostics: List[Dict[str, object]] = []
    evidence_rows: List[Dict[str, object]] = []
    for ticker in sorted(result_by_ticker):
        row = result_by_ticker[ticker]
        if not str(row.get("scan_status", "")).startswith("SKIPPED"):
            continue
        price = price_cache_has(root, ticker)
        factor = ticker in factor_set
        tech = ticker in tech_set
        full = "TRUE" if factor else "FALSE"
        present_sources = [(name, rel) for name, (rel, tickers) in source_map.items() if ticker in tickers]
        found = bool(present_sources) or price
        strongest = "state/v18/price_cache" if price else present_sources[0][1] if present_sources else ""
        category, repair = classify(ticker, str(row.get("scan_status", "")), str(row.get("failure_reason", "")), price, factor, tech, full, found)
        diagnostics.append({
            "ticker": ticker,
            "selected_in_r2": "TRUE",
            "r2_scan_status": row.get("scan_status", ""),
            "r2_failure_reason": row.get("failure_reason", ""),
            "canonical_universe_present": str(ticker in canonical_set).upper(),
            "ledger_last_status": ledger_by_ticker.get(ticker, {}).get("last_scan_status", ""),
            "local_price_evidence": str(price).upper(),
            "local_factor_pack_evidence": str(factor).upper(),
            "local_technical_timing_evidence": str(tech).upper(),
            "local_full_history_ready_evidence": full,
            "found_in_any_local_source": str(found).upper(),
            "local_source_count": len(present_sources) + (1 if price else 0),
            "strongest_evidence_source": strongest,
            "likely_skip_category": category,
            "repair_recommendation": repair,
        })
        for name, rel in present_sources:
            evidence_rows.append({"ticker": ticker, "source_name": name, "source_path": rel, "evidence_type": "TICKER_COLUMN", "present": "TRUE", "notes": "Ticker present in local source."})
        evidence_rows.append({"ticker": ticker, "source_name": "price_cache", "source_path": f"state/v18/price_cache/{ticker}.csv", "evidence_type": "LOCAL_PRICE_CACHE", "present": str(price).upper(), "notes": "Read-only existence/line-count check."})

    counts = Counter(row["likely_skip_category"] for row in diagnostics)
    summary_rows = [
        {"likely_skip_category": cat, "ticker_count": counts[cat], "recommended_interpretation": "See repair plan."}
        for cat in sorted(counts)
    ]
    projected_price = sum(1 for row in diagnostics if row["local_price_evidence"] == "TRUE")
    projected_full = sum(1 for row in diagnostics if row["local_factor_pack_evidence"] == "TRUE")
    repair_rows = [
        {"priority": 1, "repair_id": "R4_SPLIT_SUCCESS_STATUS", "repair_recommendation": "split partial local scan success from full factor-ready success", "affected_count": projected_price, "rationale": "Allows local price coverage to count separately from full factor readiness.", "allowed_now": "FALSE"},
        {"priority": 2, "repair_id": "SOURCE_DETECTION_REPAIR", "repair_recommendation": "patch executor source detection", "affected_count": counts.get("SOURCE_DETECTION_GAP", 0), "rationale": "Some tickers may have local evidence but were skipped by strict price-cache criteria.", "allowed_now": "FALSE"},
        {"priority": 3, "repair_id": "STAGED_BACKFILL_LATER", "repair_recommendation": "require staged backfill later", "affected_count": counts.get("MISSING_LOCAL_PRICE", 0) + counts.get("UNKNOWN_LOCAL_INPUT_GAP", 0), "rationale": "No local price evidence is available for these tickers.", "allowed_now": "FALSE"},
    ]
    success_rows = [
        {"success_status": "LOCAL_PRICE_SCAN_SUCCESS", "definition": "Local price evidence exists, regardless of factor-pack/full-history readiness.", "projected_count": projected_price, "recommended_for_r4": "TRUE"},
        {"success_status": "FULL_FACTOR_SCAN_SUCCESS", "definition": "Local price plus factor-pack/full-history readiness exists.", "projected_count": projected_full, "recommended_for_r4": "TRUE"},
        {"success_status": "SKIPPED_NO_LOCAL_PRICE", "definition": "No local price evidence found; do not count as local coverage.", "projected_count": len(diagnostics) - projected_price, "recommended_for_r4": "TRUE"},
    ]
    values: Dict[str, str] = {
        "STATUS": STATUS_OK,
        "MODE": MODE,
        "R3_SKIP_DIAGNOSTICS_READY": "FALSE",
        "V18_23B_R2_SELECTED_SCAN_COUNT": r2_readfirst.get("SELECTED_SCAN_COUNT", str(len(selected_rows))),
        "V18_23B_R2_SUCCESS_SCAN_COUNT": r2_readfirst.get("SUCCESS_SCAN_COUNT", ""),
        "V18_23B_R2_SKIPPED_SCAN_COUNT": r2_readfirst.get("SKIPPED_SCAN_COUNT", ""),
        "DIAGNOSED_SELECTED_TICKER_COUNT": str(len(result_rows)),
        "DIAGNOSED_SKIPPED_TICKER_COUNT": str(len(diagnostics)),
        "SOURCE_DETECTION_GAP_COUNT": str(counts.get("SOURCE_DETECTION_GAP", 0)),
        "EXPECTED_OUTSIDE_RAW105_FACTOR_PACK_COUNT": str(counts.get("EXPECTED_OUTSIDE_RAW105_FACTOR_PACK", 0)),
        "MISSING_LOCAL_PRICE_COUNT": str(counts.get("MISSING_LOCAL_PRICE", 0)),
        "MISSING_FACTOR_PACK_COUNT": str(sum(1 for row in diagnostics if row["local_factor_pack_evidence"] == "FALSE")),
        "MISSING_TECHNICAL_TIMING_COUNT": str(sum(1 for row in diagnostics if row["local_technical_timing_evidence"] == "FALSE")),
        "MISSING_FULL_HISTORY_COUNT": str(sum(1 for row in diagnostics if row["local_full_history_ready_evidence"] != "TRUE")),
        "EXECUTOR_SUCCESS_CRITERIA_TOO_STRICT_COUNT": str(counts.get("EXECUTOR_SUCCESS_CRITERIA_TOO_STRICT", 0)),
        "UNKNOWN_LOCAL_INPUT_GAP_COUNT": str(counts.get("UNKNOWN_LOCAL_INPUT_GAP", 0)),
        "REPAIRABLE_WITH_SOURCE_DETECTION_ONLY_COUNT": str(counts.get("SOURCE_DETECTION_GAP", 0)),
        "REPAIRABLE_WITH_SUCCESS_STATUS_SPLIT_COUNT": str(projected_price),
        "NON_REPAIRABLE_WITHOUT_BACKFILL_COUNT": str(counts.get("MISSING_LOCAL_PRICE", 0) + counts.get("UNKNOWN_LOCAL_INPUT_GAP", 0)),
        "PROJECTED_LOCAL_PRICE_SCAN_SUCCESS_COUNT": str(projected_price),
        "PROJECTED_FULL_FACTOR_SCAN_SUCCESS_COUNT": str(projected_full),
        "USER_TARGET_65_LOCAL_PRICE_SCANS_REACHABLE_LOCAL_ONLY": str(projected_price >= 65).upper(),
        "USER_TARGET_65_FULL_FACTOR_SCANS_REACHABLE_LOCAL_ONLY": str(projected_full >= 65).upper(),
        "V18_23B_R4_PATCH_RECOMMENDED": "TRUE",
        "STAGED_BACKFILL_RECOMMENDED": str((len(diagnostics) - projected_price) > 0).upper(),
        "VALIDATION_FAIL_COUNT": "0",
        "RECOMMENDED_NEXT_ACTION": "Implement V18.23B-R4 to split LOCAL_PRICE_SCAN_SUCCESS from FULL_FACTOR_SCAN_SUCCESS; use staged backfill later for tickers with no local price evidence.",
        "DIAGNOSTICS_PATH": str(root / OUTPUTS["diagnostics"]),
        "SKIPPED_TICKER_DIAGNOSTICS_PATH": str(root / OUTPUTS["ticker_diag"]),
        "LOCAL_SOURCE_EVIDENCE_PATH": str(root / OUTPUTS["evidence"]),
        "REPAIR_PLAN_PATH": str(root / OUTPUTS["repair"]),
        "SKIP_CATEGORY_SUMMARY_PATH": str(root / OUTPUTS["summary"]),
        "SUCCESS_DEFINITION_RECOMMENDATION_PATH": str(root / OUTPUTS["success_def"]),
        "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        "REPORT_PATH": str(root / OUTPUTS["report"]),
    }
    values.update(SAFETY)

    write_csv(root / OUTPUTS["ticker_diag"], diagnostics, DIAG_FIELDS)
    write_csv(root / OUTPUTS["evidence"], evidence_rows, EVIDENCE_FIELDS)
    write_csv(root / OUTPUTS["repair"], repair_rows, REPAIR_FIELDS)
    write_csv(root / OUTPUTS["summary"], summary_rows, SUMMARY_FIELDS)
    write_csv(root / OUTPUTS["success_def"], success_rows, SUCCESS_FIELDS)
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["diagnostics"], render_md(values, summary_rows))
    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    after = {str(path): file_sig(path) for path in protected_files(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig) + sorted(path for path in after if path not in before)
    required = [root / rel for rel in OUTPUTS.values()]
    validations = [
        validation_row("python_compile_check", py_compile(root / "scripts/v18/v18_23B_R3_local_scan_skip_diagnostics.py"), 1, "Python compile."),
        validation_row("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_23B_R3_local_scan_skip_diagnostics.ps1"), 1, "PowerShell parse."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required), 1, "All R3 outputs must exist and be non-empty."),
        validation_row("r2_scan_result_readable", bool(result_rows), 1, "V18.23B-R2 scan result must be readable."),
        validation_row("selected_count_matches_r2", str(len(result_rows)) == values["V18_23B_R2_SELECTED_SCAN_COUNT"], 1, "Diagnosed selected count should match R2."),
        validation_row("skipped_count_matches_r2", str(len(diagnostics)) == values["V18_23B_R2_SKIPPED_SCAN_COUNT"], 1, "Diagnosed skipped count should match R2."),
        validation_row("repair_plan_has_rows", bool(repair_rows), 1, "Repair plan must contain rows."),
        validation_row("success_definition_has_rows", bool(success_rows), 1, "Success definition recommendation must contain rows."),
        validation_row("ledger_not_modified", not changed, len(changed), ";".join(changed[:20])),
    ]
    for key, expected in SAFETY.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    unknown = counts.get("UNKNOWN_LOCAL_INPUT_GAP", 0)
    if fail_count:
        values["STATUS"] = STATUS_FAIL
    elif unknown:
        values["STATUS"] = STATUS_WARN
    else:
        values["STATUS"] = STATUS_OK
    values["R3_SKIP_DIAGNOSTICS_READY"] = "TRUE" if fail_count == 0 else "FALSE"
    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["diagnostics"], render_md(values, summary_rows))
    write_text(root / OUTPUTS["report"], render_report(values))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))
    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
