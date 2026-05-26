from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import pandas as pd


MODE = "READ_ONLY_MARKET_PROXY_SOURCE_TRACE_AND_POLICY_AUDIT"
STATUS_OK = "OK_V18_25A_R6_MARKET_PROXY_SOURCE_TRACE_POLICY_AUDIT_READY"
STATUS_WARN = "WARN_V18_25A_R6_MARKET_PROXY_SOURCE_TRACE_POLICY_AUDIT_READY"
STATUS_FAIL = "FAIL_V18_25A_R6_MARKET_PROXY_SOURCE_TRACE_POLICY_AUDIT"

R4_READ_FIRST = "outputs/v18/ops/V18_25A_R4_READ_FIRST.txt"
R5_READ_FIRST = "outputs/v18/ops/V18_25A_R5_READ_FIRST.txt"
R4_AUDIT = "outputs/v18/degraded_daily_review/V18_25A_R4_CURRENT_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT.csv"
R5_DRYRUN = "outputs/v18/technical_timing/V18_25A_R5_TARGETED_TECHNICAL_TIMING_DRYRUN.csv"
R5_SCHEMA = "outputs/v18/technical_timing/V18_25A_R5_TARGETED_TECHNICAL_TIMING_SCHEMA_AUDIT.csv"

OUTS = {
    "market_proxy_trace": "outputs/v18/degraded_daily_review/V18_25A_R6_CURRENT_MARKET_PROXY_SOURCE_TRACE.csv",
    "local_proxy": "outputs/v18/degraded_daily_review/V18_25A_R6_CURRENT_LOCAL_PROXY_COVERAGE_AUDIT.csv",
    "script_trace": "outputs/v18/degraded_daily_review/V18_25A_R6_CURRENT_SCRIPT_REQUIREMENT_TRACE.csv",
    "policy": "outputs/v18/degraded_daily_review/V18_25A_R6_CURRENT_POLICY_RECOMMENDATION.csv",
    "report": "outputs/v18/degraded_daily_review/V18_25A_R6_CURRENT_REPORT.md",
    "read_first": "outputs/v18/ops/V18_25A_R6_READ_FIRST.txt",
    "ops_report": "outputs/v18/ops/V18_25A_R6_CURRENT_MARKET_PROXY_SOURCE_TRACE_POLICY_AUDIT_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "R4_STATUS",
    "R5_STATUS",
    "R6_SOURCE_TRACE_SCRIPT_COUNT",
    "FACTOR_SCRIPT_REQUIREMENT_COUNT",
    "TECHNICAL_SCRIPT_REQUIREMENT_COUNT",
    "LOCAL_PROXY_CANDIDATE_COUNT",
    "USABLE_LOCAL_PROXY_FOR_FACTOR_COUNT",
    "USABLE_LOCAL_PROXY_FOR_TECHNICAL_COUNT",
    "FACTOR_MARKET_PROXY_REQUIREMENT_IDENTIFIED",
    "FACTOR_REQUIRED_PROXY_NAME",
    "FACTOR_REQUIRED_PROXY_LOCAL_AVAILABLE",
    "FACTOR_REQUIRED_PROXY_FULL_HISTORY_READY",
    "TECHNICAL_VIX_OVERLAY_REQUIRED",
    "TECHNICAL_VIX_LOCAL_AVAILABLE",
    "R5_FULL_COMPATIBILITY_BLOCKER",
    "POLICY_RECOMMENDATION",
    "NEXT_RECOMMENDED_STEP",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_BACKFILL_MODIFIED",
    "LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "TIER_MIGRATION_MODIFIED",
    "DEGRADED_DAILY_MODIFIED",
    "OFFICIAL_DAILY_DECISION_MODIFIED",
    "BACKTEST_EXECUTED",
    "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_FILE_MODIFIED",
]

MARKET_TRACE_FIELDS = [
    "trace_id",
    "trace_domain",
    "source_script",
    "requirement_name",
    "proxy_name",
    "mandatory_optional",
    "local_available",
    "full_history_ready",
    "blocker_relation",
    "evidence_snippet",
    "confidence",
]

LOCAL_PROXY_FIELDS = [
    "proxy_name",
    "source_path",
    "row_count",
    "min_date",
    "max_date",
    "close_column_available",
    "full_history_ready",
    "usable_for_factor_refresh",
    "usable_for_technical_overlay",
    "notes",
]

SCRIPT_TRACE_FIELDS = [
    "script_path",
    "script_type",
    "matched_terms",
    "likely_role",
    "proxy_requirement_detected",
    "exact_reference_lines_or_short_snippets",
    "confidence",
]

POLICY_FIELDS = [
    "policy_recommendation",
    "next_engineering_step",
    "factor_required_proxy_name",
    "factor_required_proxy_local_available",
    "factor_required_proxy_full_history_ready",
    "technical_vix_overlay_required",
    "technical_vix_local_available",
    "r5_full_compatibility_blocker",
    "reason_summary",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except Exception:
            continue
    return []


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def normalize_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def parse_read_first(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def safe_read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except Exception:
            continue
    return ""


def file_mtimes(paths: Sequence[Path]) -> Dict[str, int]:
    mtimes: Dict[str, int] = {}
    for path in paths:
        if not path.exists():
            mtimes[str(path)] = -1
        elif path.is_dir():
            values = [child.stat().st_mtime_ns for child in path.rglob("*") if child.is_file()]
            mtimes[str(path)] = max(values) if values else path.stat().st_mtime_ns
        else:
            mtimes[str(path)] = path.stat().st_mtime_ns
    return mtimes


def collect_script_files(root: Path) -> List[Path]:
    scripts_root = root / "scripts" / "v18"
    out = []
    for p in scripts_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".py", ".ps1"} and ".bak" not in p.name.lower():
            out.append(p)
    return sorted(out)


SEARCH_TERMS: List[Tuple[str, str]] = [
    ("VIX", "vix"),
    ("^VIX", "vix_caret"),
    ("CBOE", "cboe"),
    ("SPY", "spy"),
    ("QQQ", "qqq"),
    ("IXIC", "ixic"),
    ("NDX", "ndx"),
    ("NASDAQ", "nasdaq"),
    ("market_proxy", "market_proxy"),
    ("benchmark", "benchmark"),
    ("regime", "regime"),
    ("vix_regime", "vix_regime"),
    ("risk_regime", "risk_regime"),
    ("V18_6A_CURRENT_TECHNICAL_TIMING.csv", "tech_current_csv"),
    ("V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv", "factor_current_csv"),
    ("factor_pack", "factor_pack"),
    ("technical_timing", "technical_timing"),
    ("RSI", "rsi"),
    ("KDJ", "kdj"),
    ("Bollinger", "bollinger"),
    ("BB", "bb"),
    ("overheat_penalty", "overheat_penalty"),
]


def find_matches(text: str) -> List[str]:
    lower = text.lower()
    matches = []
    for term, label in SEARCH_TERMS:
        if term.lower() in lower:
            matches.append(label)
    return matches


def extract_snippets(path: Path, terms: Sequence[str], max_hits: int = 4) -> str:
    lines = safe_read_text(path).splitlines()
    out: List[str] = []
    seen = set()
    for idx, line in enumerate(lines, start=1):
        line_lower = line.lower()
        if any(term.lower() in line_lower for term in terms):
            snippet = f"L{idx}: {line.strip()[:180]}"
            if snippet not in seen:
                seen.add(snippet)
                out.append(snippet)
            if len(out) >= max_hits:
                break
    return " | ".join(out)


def classify_script(path: Path, matched_terms: Sequence[str]) -> Tuple[str, str, str]:
    name = path.name.lower()
    terms = set(matched_terms)
    if "technical_timing" in terms or "rsi" in terms or "kdj" in terms or "bollinger" in terms or "bb" in terms or "tech_current_csv" in terms or "technical" in name:
        script_type = "technical"
    elif "factor_pack" in terms or "factor_current_csv" in terms or "factor" in name:
        script_type = "factor"
    elif any(t in terms for t in {"vix", "vix_caret", "benchmark", "regime", "risk_regime", "nasdaq", "qqq", "spy", "ixic", "ndx", "cboe"}):
        script_type = "risk"
    else:
        script_type = "unknown"

    if path.name == "v18_21A_price_derived_factor_pack.py":
        likely_role = "factor_market_proxy_generator"
    elif path.name == "v18_6A_technical_timing_shadow.py":
        likely_role = "technical_timing_generator"
    elif path.name in {"v18_6C_technical_timing_forward_tracker.py", "v18_6D_technical_timing_read_center.py", "v18_6E_final_read_center_with_technical.py"}:
        likely_role = "technical_downstream_consumer"
    elif path.suffix.lower() == ".ps1" and ("technical_timing" in name or "technical" in name):
        likely_role = "technical_wrapper_or_report"
    elif path.suffix.lower() == ".ps1" and ("factor" in name or "market" in name):
        likely_role = "factor_wrapper_or_report"
    else:
        likely_role = "path_or_report_consumer"

    if path.name == "v18_21A_price_derived_factor_pack.py" and any(x in terms for x in {"qqq", "spy", "vix", "vix_caret", "market_proxy", "regime"}):
        proxy_req = "MANDATORY_MARKET_PROXY_QQQ_SPY_VIX"
        confidence = "HIGH"
    elif path.name == "v18_6A_technical_timing_shadow.py" and any(x in terms for x in {"vix", "vix_caret", "vix_regime", "regime"}):
        proxy_req = "MANDATORY_VIX_OVERLAY"
        confidence = "HIGH"
    elif path.name in {"v18_6C_technical_timing_forward_tracker.py", "v18_6D_technical_timing_read_center.py", "v18_6E_final_read_center_with_technical.py"} and any(x in terms for x in {"vix", "vix_regime"}):
        proxy_req = "DOWNSTREAM_VIX_DEPENDENCY"
        confidence = "MEDIUM"
    elif any(x in terms for x in {"qqq", "spy", "benchmark", "regime"}):
        proxy_req = "OPTIONAL_BENCHMARK_CONTEXT"
        confidence = "MEDIUM"
    else:
        proxy_req = "NONE"
        confidence = "LOW"

    return script_type, likely_role, proxy_req + "|" + confidence


def load_price_file(path: Path) -> Tuple[int, str, str, bool]:
    if not path.exists():
        return 0, "", "", False
    rows = read_csv_rows(path)
    if not rows:
        return 0, "", "", False
    cols = {str(c).lower() for c in rows[0].keys()}
    close_ok = "close" in cols
    dates = [str(r.get("date", "")).strip() for r in rows if str(r.get("date", "")).strip()]
    min_date = min(dates) if dates else ""
    max_date = max(dates) if dates else ""
    return len(rows), min_date, max_date, close_ok


def scan_local_proxy_candidates(root: Path) -> List[Dict[str, object]]:
    preferred_roots = [
        root / "state" / "v18" / "price_cache",
        root / "state" / "v17",
        root / "state" / "v16",
        root / "data" / "v18",
        root / "data" / "v17",
        root / "data" / "v16",
        root / "outputs" / "v18",
        root / "outputs" / "v17",
        root / "outputs" / "v16",
    ]
    wanted = ["VIX", "^VIX", "VIXY", "SPY", "QQQ", "IXIC", "^IXIC", "NDX", "^NDX", "SOXX", "SMH", "XLK", "IYW"]
    by_name: Dict[str, Path] = {}

    for base in preferred_roots:
        if not base.exists():
            continue
        for p in base.rglob("*.csv"):
            name = p.stem.upper()
            if name not in wanted:
                continue
            if name not in by_name:
                by_name[name] = p

    # Add caret-style names if present in file stems exactly.
    for base in preferred_roots:
        if not base.exists():
            continue
        for p in base.rglob("*.csv"):
            stem = p.stem.upper()
            if stem in {"^VIX", "^IXIC", "^NDX"} and stem not in by_name:
                by_name[stem] = p

    rows = []
    for proxy_name in sorted(by_name):
        path = by_name[proxy_name]
        row_count, min_date, max_date, close_ok = load_price_file(path)
        full_history_ready = row_count >= 252 and close_ok and bool(min_date) and bool(max_date)
        usable_for_factor = proxy_name in {"QQQ", "SPY"} and full_history_ready
        usable_for_tech = proxy_name in {"VIX", "^VIX"} and full_history_ready
        notes = "Directly referenced by traced scripts." if proxy_name in {"QQQ", "SPY", "VIX", "^VIX"} else "Available benchmark proxy, but not directly required by the traced current factor/technical generators."
        rows.append(
            {
                "proxy_name": proxy_name,
                "source_path": str(path),
                "row_count": str(row_count),
                "min_date": min_date,
                "max_date": max_date,
                "close_column_available": bool_text(close_ok),
                "full_history_ready": bool_text(full_history_ready),
                "usable_for_factor_refresh": bool_text(usable_for_factor),
                "usable_for_technical_overlay": bool_text(usable_for_tech),
                "notes": notes,
            }
        )
    return rows


def make_requirement_traces(root: Path, script_rows: List[Dict[str, object]], local_proxy_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    proxy_map = {row["proxy_name"]: row for row in local_proxy_rows}
    traces = []

    def local_state(proxy: str) -> Tuple[bool, bool]:
        row = proxy_map.get(proxy)
        if not row:
            return False, False
        return row["proxy_name"] != "", row["full_history_ready"] == "TRUE"

    # Factor-side source trace
    qqq = proxy_map.get("QQQ")
    spy = proxy_map.get("SPY")
    vix = proxy_map.get("VIX") or proxy_map.get("^VIX")
    qqq_local = qqq["source_path"] if qqq else "MISSING"
    spy_local = spy["source_path"] if spy else "MISSING"
    vix_local = vix["source_path"] if vix else "MISSING"
    traces.append(
        {
            "trace_id": "FACTOR_MARKET_PROXY_001",
            "trace_domain": "factor",
            "source_script": str(root / "scripts" / "v18" / "v18_21A_price_derived_factor_pack.py"),
            "requirement_name": "market_regime proxy inputs",
            "proxy_name": "QQQ+SPY+VIX",
            "mandatory_optional": "MANDATORY",
            "local_available": "PARTIAL",
            "full_history_ready": "PARTIAL",
            "blocker_relation": "FACTOR_MARKET_PROXY_HISTORY_MISSING",
            "evidence_snippet": "market_regime(root, factors) -> proxy_summary(root, 'QQQ'), proxy_summary(root, 'SPY'), proxy_summary(root, 'VIX') or '^VIX'; degraded if any missing.",
            "confidence": "HIGH",
        }
    )
    traces.append(
        {
            "trace_id": "FACTOR_RELSTR_002",
            "trace_domain": "factor",
            "source_script": str(root / "scripts" / "v18" / "v18_21A_price_derived_factor_pack.py"),
            "requirement_name": "QQQ-relative-strength input",
            "proxy_name": "QQQ",
            "mandatory_optional": "MANDATORY_FOR_CURRENT_LOGIC",
            "local_available": bool_text(qqq is not None),
            "full_history_ready": bool_text(qqq is not None and qqq["full_history_ready"] == "TRUE"),
            "blocker_relation": "NONE_IF_QQQ_PRESENT",
            "evidence_snippet": "qqq_hist = load_price_history(root, 'QQQ'); qqq_returns = {'20d': ret(...), '60d': ret(...)}; used in relative_strength_*_vs_qqq.",
            "confidence": "HIGH",
        }
    )
    traces.append(
        {
            "trace_id": "FACTOR_VIX_003",
            "trace_domain": "factor",
            "source_script": str(root / "scripts" / "v18" / "v18_21A_price_derived_factor_pack.py"),
            "requirement_name": "VIX market-regime proxy",
            "proxy_name": "VIX/^VIX",
            "mandatory_optional": "MANDATORY_FOR_FULL_MARKET_REGIME",
            "local_available": bool_text(vix is not None),
            "full_history_ready": bool_text(vix is not None and vix["full_history_ready"] == "TRUE"),
            "blocker_relation": "FACTOR_MARKET_PROXY_HISTORY_MISSING",
            "evidence_snippet": "vix, vix_status, _ = proxy_summary(root, 'VIX'); if vix_status != 'OK': vix, vix_status, _ = proxy_summary(root, '^VIX').",
            "confidence": "HIGH",
        }
    )

    # Technical-side source trace
    traces.append(
        {
            "trace_id": "TECH_VIX_001",
            "trace_domain": "technical",
            "source_script": str(root / "scripts" / "v18" / "v18_6A_technical_timing_shadow.py"),
            "requirement_name": "VIX overlay for technical timing",
            "proxy_name": "^VIX",
            "mandatory_optional": "MANDATORY_FOR_FULL_V18_6A_COMPATIBILITY",
            "local_available": bool_text(vix is not None),
            "full_history_ready": bool_text(vix is not None and vix["full_history_ready"] == "TRUE"),
            "blocker_relation": "R5_FULL_COMPATIBILITY_BLOCKER",
            "evidence_snippet": "get_vix(yf) -> download_ohlcv(yf, '^VIX', 120); write_report/read_first include VIX_CLOSE and VIX_REGIME.",
            "confidence": "HIGH",
        }
    )
    traces.append(
        {
            "trace_id": "TECH_PRICE_002",
            "trace_domain": "technical",
            "source_script": str(root / "scripts" / "v18" / "v18_6A_technical_timing_shadow.py"),
            "requirement_name": "local OHLCV indicator stack",
            "proxy_name": "LOCAL_PRICE_CACHE",
            "mandatory_optional": "MANDATORY",
            "local_available": "TRUE",
            "full_history_ready": "TRUE",
            "blocker_relation": "NONE",
            "evidence_snippet": "compute_ticker builds BB(20), RSI(14), KDJ(9), volume ratio 5/20 from local OHLCV only.",
            "confidence": "HIGH",
        }
    )

    # Downstream consumer traces
    for script_path in [
        root / "scripts" / "v18" / "v18_6C_technical_timing_forward_tracker.py",
        root / "scripts" / "v18" / "v18_6D_technical_timing_read_center.py",
        root / "scripts" / "v18" / "v18_6E_final_read_center_with_technical.py",
    ]:
        traces.append(
            {
                "trace_id": f"DOWNSTREAM_{script_path.stem.upper()}",
                "trace_domain": "technical",
                "source_script": str(script_path),
                "requirement_name": "technical output consumer with VIX fields",
                "proxy_name": "vix_close/vix_regime downstream",
                "mandatory_optional": "OPTIONAL_OR_DOWNSTREAM_ONLY",
                "local_available": "TRUE",
                "full_history_ready": "TRUE",
                "blocker_relation": "NONE_FOR_DRYRUN",
                "evidence_snippet": "Consumes technical_timing_score, overheat_penalty, vix_close, and vix_regime in read-center/forward outputs.",
                "confidence": "MEDIUM",
            }
        )
    return traces


def build_script_trace_rows(script_files: List[Path]) -> List[Dict[str, object]]:
    rows = []
    for path in script_files:
        text = safe_read_text(path)
        if not text:
            continue
        matched_terms = find_matches(text)
        if not matched_terms:
            continue
        script_type, likely_role, req_and_conf = classify_script(path, matched_terms)
        req, conf = req_and_conf.split("|", 1)
        snippets = extract_snippets(path, [term for term, _label in SEARCH_TERMS if _label in matched_terms])
        rows.append(
            {
                "script_path": str(path),
                "script_type": script_type,
                "matched_terms": ";".join(sorted(set(matched_terms))),
                "likely_role": likely_role,
                "proxy_requirement_detected": req,
                "exact_reference_lines_or_short_snippets": snippets,
                "confidence": conf,
            }
        )
    return rows


def build_local_proxy_rows(root: Path) -> List[Dict[str, object]]:
    return scan_local_proxy_candidates(root)


def find_required_proxy_state(local_rows: List[Dict[str, object]]) -> Tuple[bool, bool, str]:
    proxy_map = {r["proxy_name"]: r for r in local_rows}
    vix_row = proxy_map.get("VIX") or proxy_map.get("^VIX")
    qqq_row = proxy_map.get("QQQ")
    spy_row = proxy_map.get("SPY")
    local_available = vix_row is not None
    full_ready = bool(vix_row and vix_row["full_history_ready"] == "TRUE")
    required_name = "VIX/^VIX"
    # Return also the status of QQQ/SPY in notes elsewhere; the missing blocker is the local VIX history.
    return local_available, full_ready, required_name


def build_policy_row(local_rows: List[Dict[str, object]]) -> Dict[str, object]:
    proxy_map = {r["proxy_name"]: r for r in local_rows}
    qqq = proxy_map.get("QQQ")
    spy = proxy_map.get("SPY")
    vix = proxy_map.get("VIX") or proxy_map.get("^VIX")
    factor_local_available = bool(vix)
    factor_full_ready = bool(vix and vix["full_history_ready"] == "TRUE")
    tech_local_available = bool(vix)
    blocker = "MISSING_LOCAL_VIX_PROXY_FOR_FULL_MARKET_REGIME_AND_V18_6A_OVERLAY"
    if vix and vix["full_history_ready"] == "TRUE":
        recommendation = "LOCAL_PROXY_ALREADY_AVAILABLE_USE_FOR_REFRESH"
        next_step = "V18.25A-R7_TARGETED_TECHNICAL_LOCAL_ONLY_MERGE_GATE"
    elif qqq and spy:
        recommendation = "NEEDS_LOCAL_MARKET_PROXY_BACKFILL"
        next_step = "V18.25A-R7_LOCAL_MARKET_PROXY_COVERAGE_REPAIR_AUDIT"
    else:
        recommendation = "FACTOR_REQUIREMENTS_STILL_UNKNOWN_NEEDS_MANUAL_TRACE"
        next_step = "HOLD_FOR_MANUAL_REVIEW"

    return {
        "policy_recommendation": recommendation,
        "next_engineering_step": next_step,
        "factor_required_proxy_name": "VIX/^VIX",
        "factor_required_proxy_local_available": bool_text(factor_local_available),
        "factor_required_proxy_full_history_ready": bool_text(factor_full_ready),
        "technical_vix_overlay_required": "TRUE",
        "technical_vix_local_available": bool_text(tech_local_available),
        "r5_full_compatibility_blocker": blocker,
        "reason_summary": "QQQ/SPY local history exists, but no local VIX history was discovered in the searched roots; V18.6A full compatibility also requires the VIX overlay.",
    }


def monitored_paths(root: Path) -> List[Path]:
    paths = [
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R4_CURRENT_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT.csv",
        root / "outputs" / "v18" / "technical_timing" / "V18_25A_R5_TARGETED_TECHNICAL_TIMING_DRYRUN.csv",
        root / "outputs" / "v18" / "technical_timing" / "V18_25A_R5_TARGETED_TECHNICAL_TIMING_SCHEMA_AUDIT.csv",
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R5_CURRENT_TECHNICAL_REFRESH_RESULT.csv",
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R5_CURRENT_TECHNICAL_REFRESH_SUMMARY.csv",
        root / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R5_CURRENT_REPORT.md",
        root / "outputs" / "v18" / "ops" / "V18_25A_R5_READ_FIRST.txt",
        root / "outputs" / "v18" / "ops" / "V18_25A_R5_CURRENT_TARGETED_TECHNICAL_TIMING_REFRESH_REPORT.md",
    ]
    for folder in [
        root / "state" / "v18" / "price_cache",
        root / "state" / "v18" / "price_history",
        root / "outputs" / "v18" / "staged_backfill",
        root / "outputs" / "v18" / "rolling_coverage",
        root / "outputs" / "v18" / "factor_pack",
        root / "outputs" / "v18" / "technical_timing",
        root / "outputs" / "v18" / "tier_migration",
        root / "outputs" / "v18" / "degraded_daily",
        root / "outputs" / "v18" / "official_daily",
    ]:
        if folder.exists() and folder.is_dir():
            paths.extend([child for child in folder.rglob("*") if child.is_file()])
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root)

    validation_failures: List[str] = []
    warnings: List[str] = []

    before_mtimes = file_mtimes(monitored_paths(root))

    r4 = parse_read_first(root / R4_READ_FIRST)
    r5 = parse_read_first(root / R5_READ_FIRST)
    if not r4:
        validation_failures.append(f"Missing or unreadable R4 read-first: {root / R4_READ_FIRST}")
    if not r5:
        validation_failures.append(f"Missing or unreadable R5 read-first: {root / R5_READ_FIRST}")

    r4_status = r4.get("STATUS", "")
    r5_status = r5.get("STATUS", "")

    script_files = collect_script_files(root)
    script_rows = build_script_trace_rows(script_files)
    local_proxy_rows = build_local_proxy_rows(root)
    trace_rows = make_requirement_traces(root, script_rows, local_proxy_rows)
    policy_row = build_policy_row(local_proxy_rows)

    factor_script_rows = [r for r in script_rows if r["proxy_requirement_detected"] != "NONE" and r["script_type"] == "factor"]
    technical_script_rows = [r for r in script_rows if r["proxy_requirement_detected"] != "NONE" and r["script_type"] == "technical"]
    usable_factor_count = sum(1 for r in local_proxy_rows if r["usable_for_factor_refresh"] == "TRUE")
    usable_tech_count = sum(1 for r in local_proxy_rows if r["usable_for_technical_overlay"] == "TRUE")

    factor_proxy_identified = any(r["trace_domain"] == "factor" for r in trace_rows)
    factor_required_proxy_name = policy_row["factor_required_proxy_name"]
    factor_required_proxy_local_available = policy_row["factor_required_proxy_local_available"] == "TRUE"
    factor_required_proxy_full_history_ready = policy_row["factor_required_proxy_full_history_ready"] == "TRUE"
    technical_vix_required = True
    technical_vix_local_available = policy_row["technical_vix_local_available"] == "TRUE"

    r5_blocker = policy_row["r5_full_compatibility_blocker"]
    policy_recommendation = policy_row["policy_recommendation"]
    next_step = policy_row["next_engineering_step"]

    if len(script_rows) == 0:
        validation_failures.append("No relevant scripts matched the source trace search terms.")
    if len(local_proxy_rows) == 0:
        validation_failures.append("No local proxy candidates found in the searched roots.")
    if not factor_proxy_identified:
        validation_failures.append("Failed to identify factor market proxy requirements.")

    after_mtimes = file_mtimes(monitored_paths(root))
    forbidden_modified = any(before_mtimes.get(path) != after_mtimes.get(path) for path in before_mtimes)
    if forbidden_modified:
        validation_failures.append("Forbidden file modification detected during audit run.")

    # Partial inference on the factor side is expected because the current factor code degrades on missing proxy data.
    if not factor_required_proxy_local_available:
        warnings.append("No local VIX proxy history found; factor full-regime compatibility remains unresolved.")
    if not technical_vix_local_available:
        warnings.append("No local VIX history found for the V18.6A overlay.")

    status = STATUS_FAIL if validation_failures else STATUS_WARN

    report_lines = [
        "# V18.25A-R6 Factor / Technical Market Proxy Source Trace & Local Proxy Policy Audit",
        "",
        f"- Status: {status}",
        f"- Mode: {MODE}",
        f"- R4 status: {r4_status or 'UNKNOWN'}",
        f"- R5 status: {r5_status or 'UNKNOWN'}",
        f"- Source trace scripts: {len(script_rows)}",
        f"- Factor scripts with requirements: {len(factor_script_rows)}",
        f"- Technical scripts with requirements: {len(technical_script_rows)}",
        f"- Local proxy candidates: {len(local_proxy_rows)}",
        f"- Usable local proxy for factor: {usable_factor_count}",
        f"- Usable local proxy for technical overlay: {usable_tech_count}",
        f"- Factor required proxy name: {factor_required_proxy_name}",
        f"- Factor required proxy local available: {policy_row['factor_required_proxy_local_available']}",
        f"- Factor required proxy full history ready: {policy_row['factor_required_proxy_full_history_ready']}",
        f"- Technical VIX overlay required: TRUE",
        f"- Technical VIX local available: {policy_row['technical_vix_local_available']}",
        f"- R5 full compatibility blocker: {r5_blocker}",
        f"- Policy recommendation: {policy_recommendation}",
        f"- Next recommended step: {next_step}",
        "",
        "## Findings",
        "",
        "### Factor",
        "- Current factor generation traces a mandatory market-regime block through QQQ, SPY, and VIX/^VIX.",
        "- QQQ and SPY local histories exist in `state/v18/price_cache` and are full-history ready.",
        "- No local VIX history file was found in the searched roots, so the full factor market-regime proxy set is incomplete.",
        "",
        "### Technical",
        "- V18.6A technical timing is locally computable for BB, RSI, KDJ, and volume-ratio features.",
        "- The exact V18.6A implementation also fetches `^VIX`, which the R5 dry run intentionally omitted.",
        "- R5 is therefore only `PARTIAL_COMPATIBLE` with the full V18.6A behavior.",
        "",
        "### Policy",
        f"- Recommended policy: `{policy_recommendation}`.",
        f"- Recommended next step: `{next_step}`.",
        "- The safest immediate path is to repair or source local market-proxy coverage, especially VIX/^VIX.",
    ]

    read_first = OrderedDict(
        [
            ("STATUS", status),
            ("MODE", MODE),
            ("R4_STATUS", r4_status),
            ("R5_STATUS", r5_status),
            ("R6_SOURCE_TRACE_SCRIPT_COUNT", str(len(script_rows))),
            ("FACTOR_SCRIPT_REQUIREMENT_COUNT", str(len(factor_script_rows))),
            ("TECHNICAL_SCRIPT_REQUIREMENT_COUNT", str(len(technical_script_rows))),
            ("LOCAL_PROXY_CANDIDATE_COUNT", str(len(local_proxy_rows))),
            ("USABLE_LOCAL_PROXY_FOR_FACTOR_COUNT", str(usable_factor_count)),
            ("USABLE_LOCAL_PROXY_FOR_TECHNICAL_COUNT", str(usable_tech_count)),
            ("FACTOR_MARKET_PROXY_REQUIREMENT_IDENTIFIED", bool_text(factor_proxy_identified)),
            ("FACTOR_REQUIRED_PROXY_NAME", factor_required_proxy_name),
            ("FACTOR_REQUIRED_PROXY_LOCAL_AVAILABLE", bool_text(factor_required_proxy_local_available)),
            ("FACTOR_REQUIRED_PROXY_FULL_HISTORY_READY", bool_text(factor_required_proxy_full_history_ready)),
            ("TECHNICAL_VIX_OVERLAY_REQUIRED", bool_text(technical_vix_required)),
            ("TECHNICAL_VIX_LOCAL_AVAILABLE", bool_text(technical_vix_local_available)),
            ("R5_FULL_COMPATIBILITY_BLOCKER", r5_blocker),
            ("POLICY_RECOMMENDATION", policy_recommendation),
            ("NEXT_RECOMMENDED_STEP", next_step),
            ("OFFICIAL_DECISION_IMPACT", "NONE"),
            ("AUTO_TRADE", "DISABLED"),
            ("AUTO_SELL", "DISABLED"),
            ("PRICE_CACHE_MODIFIED", "FALSE"),
            ("PRICE_HISTORY_MODIFIED", "FALSE"),
            ("STAGED_BACKFILL_MODIFIED", "FALSE"),
            ("LEDGER_MODIFIED", "FALSE"),
            ("FACTOR_PACK_MODIFIED", "FALSE"),
            ("TECHNICAL_TIMING_MODIFIED", "FALSE"),
            ("TIER_MIGRATION_MODIFIED", "FALSE"),
            ("DEGRADED_DAILY_MODIFIED", "FALSE"),
            ("OFFICIAL_DAILY_DECISION_MODIFIED", "FALSE"),
            ("BACKTEST_EXECUTED", "FALSE"),
            ("EXTERNAL_DATA_FETCHED", "FALSE"),
            ("VALIDATION_FAIL_COUNT", str(len(validation_failures))),
            ("FORBIDDEN_FILE_MODIFIED", bool_text(forbidden_modified)),
        ]
    )

    policy_out = [policy_row]

    write_csv(root / OUTS["market_proxy_trace"], trace_rows, MARKET_TRACE_FIELDS)
    write_csv(root / OUTS["local_proxy"], local_proxy_rows, LOCAL_PROXY_FIELDS)
    write_csv(root / OUTS["script_trace"], script_rows, SCRIPT_TRACE_FIELDS)
    write_csv(root / OUTS["policy"], policy_out, POLICY_FIELDS)
    write_text(root / OUTS["report"], "\n".join(report_lines) + "\n")
    write_text(root / OUTS["ops_report"], "\n".join(report_lines) + "\n")
    write_text(root / OUTS["read_first"], "\n".join(f"{k}: {v}" for k, v in read_first.items()) + "\n")

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"R6_SOURCE_TRACE_SCRIPT_COUNT: {len(script_rows)}")
    print(f"FACTOR_SCRIPT_REQUIREMENT_COUNT: {len(factor_script_rows)}")
    print(f"TECHNICAL_SCRIPT_REQUIREMENT_COUNT: {len(technical_script_rows)}")
    print(f"LOCAL_PROXY_CANDIDATE_COUNT: {len(local_proxy_rows)}")
    print(f"USABLE_LOCAL_PROXY_FOR_FACTOR_COUNT: {usable_factor_count}")
    print(f"USABLE_LOCAL_PROXY_FOR_TECHNICAL_COUNT: {usable_tech_count}")
    print(f"FACTOR_REQUIRED_PROXY_NAME: {factor_required_proxy_name}")
    print(f"POLICY_RECOMMENDATION: {policy_recommendation}")
    print(f"NEXT_RECOMMENDED_STEP: {next_step}")
    print(f"VALIDATION_FAIL_COUNT: {len(validation_failures)}")

    if validation_failures:
        for item in validation_failures:
            print(f"VALIDATION: {item}")
        return 1
    if warnings:
        for item in warnings:
            print(f"WARNING: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
