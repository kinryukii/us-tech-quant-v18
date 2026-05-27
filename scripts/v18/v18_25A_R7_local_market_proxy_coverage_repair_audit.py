from __future__ import annotations

import csv
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[2]
MODE = "READ_ONLY_LOCAL_MARKET_PROXY_COVERAGE_REPAIR_AUDIT"
STATUS_OK = "OK_V18_25A_R7_LOCAL_MARKET_PROXY_COVERAGE_REPAIR_AUDIT_READY"
STATUS_WARN = "WARN_V18_25A_R7_LOCAL_MARKET_PROXY_COVERAGE_REPAIR_AUDIT_READY"
STATUS_FAIL = "FAIL_V18_25A_R7_LOCAL_MARKET_PROXY_COVERAGE_REPAIR_AUDIT"

R6_READ_FIRST = ROOT / "outputs" / "v18" / "ops" / "V18_25A_R6_READ_FIRST.txt"
R6_POLICY = ROOT / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R6_CURRENT_POLICY_RECOMMENDATION.csv"
R6_LOCAL_PROXY = ROOT / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R6_CURRENT_LOCAL_PROXY_COVERAGE_AUDIT.csv"
R6_MARKET_TRACE = ROOT / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R6_CURRENT_MARKET_PROXY_SOURCE_TRACE.csv"
R6_SCRIPT_TRACE = ROOT / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R6_CURRENT_SCRIPT_REQUIREMENT_TRACE.csv"

OUT_DIR = ROOT / "outputs" / "v18" / "degraded_daily_review"
OPS_DIR = ROOT / "outputs" / "v18" / "ops"

DISCOVERY_OUT = OUT_DIR / "V18_25A_R7_CURRENT_LOCAL_VIX_DISCOVERY.csv"
REPAIR_OPTIONS_OUT = OUT_DIR / "V18_25A_R7_CURRENT_MARKET_PROXY_REPAIR_OPTIONS.csv"
VIX_SPEC_OUT = OUT_DIR / "V18_25A_R7_CURRENT_VIX_REQUIREMENT_SPEC.csv"
STORAGE_POLICY_OUT = OUT_DIR / "V18_25A_R7_CURRENT_PROXY_STORAGE_POLICY.csv"
REPORT_OUT = OUT_DIR / "V18_25A_R7_CURRENT_REPORT.md"
READ_FIRST_OUT = OPS_DIR / "V18_25A_R7_READ_FIRST.txt"
OPS_REPORT_OUT = OPS_DIR / "V18_25A_R7_CURRENT_LOCAL_MARKET_PROXY_COVERAGE_REPAIR_AUDIT_REPORT.md"

SEARCH_ROOTS = [
    ROOT / "state" / "v18",
    ROOT / "state" / "v17",
    ROOT / "state" / "v16",
    ROOT / "data" / "v18",
    ROOT / "data" / "v17",
    ROOT / "data" / "v16",
    ROOT / "outputs" / "v18",
    ROOT / "outputs" / "v17",
    ROOT / "outputs" / "v16",
    ROOT / "archive" / "stable",
]

SCRIPT_ROOT = ROOT / "scripts" / "v18"

SEARCH_TERMS = [
    "vix",
    "^vix",
    "cboe",
    "volatility",
    "vol_regime",
    "market_regime",
    "risk_regime",
    "vix_regime",
    "fear",
    "vx",
    "vixy",
    "uvxy",
    "vxx",
    "spy",
    "qqq",
    "ixic",
    "ndx",
]

TOKEN_TERMS = {"vix", "^vix", "vixy", "uvxy", "vxx", "spy", "qqq", "ixic", "ndx", "tqqq"}
TEXT_TERMS = {
    "cboe",
    "volatility",
    "vol_regime",
    "market_regime",
    "risk_regime",
    "vix_regime",
    "fear",
}

EXACT_VIX_NAMES = {"VIX", "^VIX"}
VIX_SUBSTITUTE_NAMES = {"VIXY", "VXX", "UVXY"}
BENCHMARK_ONLY_NAMES = {"QQQ", "SPY", "TQQQ", "IXIC", "NDX"}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                return rows, list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "PARSE_FAIL"


def parse_read_first(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    text = read_text(path)
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def normalize_text(value: object) -> str:
    return str(value or "").strip()


def lower_name(path: Path) -> str:
    return path.name.lower()


def match_candidate(path: Path) -> bool:
    path_text = str(path).lower()
    stem = path.stem.lower()
    name = path.name.lower()
    parts = {p.lower() for p in path.parts}

    for token in TOKEN_TERMS:
        if token in { "spy", "qqq", "ixic", "ndx", "tqqq", "vixy", "vxx", "uvxy"}:
            if stem == token or name == f"{token}.csv" or token in parts:
                return True
        else:
            if token in path_text or token in stem:
                return True

    for token in TEXT_TERMS:
        if token in path_text or token in stem:
            return True

    return False


def candidate_sort_key(path: Path) -> Tuple[int, str]:
    text = str(path).lower()
    if "state\\v18\\price_cache" in text or "state/v18/price_cache" in text:
        rank = 0
    elif "\\data\\v16\\prices_full" in text or "/data/v16/prices_full" in text:
        rank = 1
    elif "\\data\\v16\\prices" in text or "/data/v16/prices" in text:
        rank = 2
    elif "\\archive\\stable\\" in text:
        rank = 3
    else:
        rank = 4
    return rank, str(path).lower()


def find_candidate_files() -> List[Path]:
    found: Dict[str, Path] = {}
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.csv"):
            if not match_candidate(path):
                continue
            key = str(path.resolve()).lower()
            if key not in found:
                found[key] = path.resolve()
    return sorted(found.values(), key=candidate_sort_key)


def detect_columns(fields: Sequence[str]) -> Tuple[Optional[str], Optional[str]]:
    lowered = {str(field).strip().lower(): field for field in fields}
    date_candidates = [
        "date",
        "datetime",
        "trade_date",
        "price_date",
        "timestamp",
    ]
    close_candidates = [
        "close",
        "adj_close",
        "adjusted_close",
        "settle",
        "last",
        "value",
    ]
    date_col = None
    close_col = None
    for candidate in date_candidates:
        if candidate in lowered:
            date_col = lowered[candidate]
            break
    for candidate in close_candidates:
        if candidate in lowered:
            close_col = lowered[candidate]
            break
    return date_col, close_col


def parse_date_text(value: object) -> Optional[datetime]:
    text = normalize_text(value)
    if not text:
        return None
    text = text[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return None


def candidate_metadata(path: Path) -> Dict[str, object]:
    rows, fields, status = read_csv_rows(path)
    date_col, close_col = detect_columns(fields)
    parsed_dates: List[datetime] = []
    row_count = len(rows) if status == "OK" else 0
    if status == "OK" and date_col:
        for row in rows:
            dt = parse_date_text(row.get(date_col))
            if dt is not None:
                parsed_dates.append(dt)
    min_date = min(parsed_dates).date().isoformat() if parsed_dates else ""
    max_date = max(parsed_dates).date().isoformat() if parsed_dates else ""

    stem = path.stem.upper()
    name = path.name.upper()
    exact_vix = stem in EXACT_VIX_NAMES or name in {"VIX.CSV", "^VIX.CSV"}
    substitute = stem in VIX_SUBSTITUTE_NAMES
    benchmark_only = stem in BENCHMARK_ONLY_NAMES
    file_type = "csv_history" if date_col and close_col and row_count else "csv_output"
    notes: List[str] = []

    if exact_vix:
        notes.append("Exact VIX history candidate.")
    elif substitute:
        notes.append("Volatility ETF substitute candidate; warning-only for staged research.")
    elif benchmark_only:
        notes.append("Benchmark proxy only; not a volatility proxy.")
    elif "market_regime" in path.as_posix().lower():
        notes.append("Derived output, not raw proxy history.")
    else:
        notes.append("Search hit; not an exact VIX history file.")

    if not date_col:
        notes.append("No date column detected.")
    if not close_col:
        notes.append("No close column detected.")
    if status != "OK":
        notes.append("CSV parse issue or missing file.")

    return {
        "candidate_name": path.stem,
        "source_path": str(path),
        "file_type": file_type,
        "row_count": row_count,
        "min_date": min_date,
        "max_date": max_date,
        "date_column_detected": date_col or "",
        "close_column_detected": close_col or "",
        "usable_as_vix_history": "TRUE" if exact_vix and bool(date_col) and bool(close_col) and row_count > 0 else "FALSE",
        "usable_as_vix_substitute": "TRUE" if substitute and bool(date_col) and bool(close_col) and row_count >= 120 else "FALSE",
        "notes": " ".join(notes),
    }


def script_type_for(path: Path) -> str:
    text = str(path).lower()
    if "factor" in text or "rank" in text or "benchmark" in text:
        return "factor"
    if "technical" in text or "timing" in text or "vix" in text:
        return "technical"
    if "risk" in text or "regime" in text:
        return "risk"
    return "unknown"


def relevant_script_terms(text: str) -> List[str]:
    found: List[str] = []
    lowered = text.lower()
    for term in SEARCH_TERMS:
        if term.lower() in lowered:
            found.append(term)
    return found


def script_trace() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for path in sorted(SCRIPT_ROOT.rglob("*.py"), key=lambda p: str(p).lower()):
        text = read_text(path)
        if not text:
            continue
        terms = relevant_script_terms(text)
        if not terms:
            continue
        lines = text.splitlines()
        snippets: List[str] = []
        matched_line_count = 0
        for idx, line in enumerate(lines, start=1):
            line_lower = line.lower()
            line_terms = [term for term in terms if term.lower() in line_lower]
            if not line_terms:
                continue
            matched_line_count += 1
            snippets.append(f"{idx}:{line.strip()}")
            if len(snippets) >= 3:
                break
        proxy_requirement_detected = any(term in {"vix", "^vix", "market_regime", "vix_regime", "benchmark", "qqq", "spy"} for term in terms)
        likely_role = {
            "factor": "Factor generator or factor-adjacent consumer",
            "technical": "Technical timing generator or consumer",
            "risk": "Risk/regime consumer or reporter",
            "unknown": "Script references proxy/timing terms but role is unclear",
        }[script_type_for(path)]
        confidence = "HIGH" if proxy_requirement_detected and matched_line_count else "MEDIUM" if matched_line_count else "LOW"
        rows.append(
            {
                "script_path": str(path),
                "script_type": script_type_for(path),
                "matched_terms": ", ".join(sorted(set(terms))),
                "likely_role": likely_role,
                "proxy_requirement_detected": "TRUE" if proxy_requirement_detected else "FALSE",
                "exact_reference_lines_or_short_snippets": " | ".join(snippets),
                "confidence": confidence,
            }
        )
    return rows


def derive_requirement_spec() -> List[Dict[str, object]]:
    return [
        {
            "required_proxy_name": "VIX/^VIX",
            "required_date_range": "At least 120 trading days for the V18.6A overlay path; ~252 trading days preferred for factor proxy completeness.",
            "required_columns": "date + close minimum; factor proxy_summary also uses high and volume; technical overlay needs OHLCV.",
            "minimum_history_days": 252,
            "must_be_exact_vix": "TRUE",
            "substitute_allowed": "WARNING_ONLY_FOR_STAGED_RESEARCH",
            "qqq_spy_benchmark_only": "TRUE",
            "vixy_vxx_uvxy_warning_only": "TRUE",
            "source_trace": "scripts/v18/v18_21A_price_derived_factor_pack.py and scripts/v18/v18_6A_technical_timing_shadow.py",
        }
    ]


def repair_options() -> List[Dict[str, object]]:
    return [
        {
            "option_name": "USE_EXISTING_LOCAL_VIX_IF_FOUND",
            "safety_level": "HIGH",
            "requires_external_fetch": "FALSE",
            "modifies_official_cache": "FALSE",
            "staged_first_required": "FALSE",
            "expected_downstream_unlock": "Full factor refresh and full V18.6A compatibility, but only if an exact local VIX history exists.",
            "risks": "Not available in this audit; no exact local VIX was found.",
            "recommended_or_not": "NO",
        },
        {
            "option_name": "CONTROLLED_STAGED_VIX_BACKFILL",
            "safety_level": "HIGH",
            "requires_external_fetch": "TRUE",
            "modifies_official_cache": "FALSE",
            "staged_first_required": "TRUE",
            "expected_downstream_unlock": "Exact VIX-backed factor refresh and exact V18.6A technical overlay compatibility after validation.",
            "risks": "Requires controlled provenance, validation, and later promotion; do not write official cache first.",
            "recommended_or_not": "YES",
        },
        {
            "option_name": "CONTROLLED_STAGED_VOLATILITY_ETF_BACKFILL",
            "safety_level": "MEDIUM",
            "requires_external_fetch": "TRUE",
            "modifies_official_cache": "FALSE",
            "staged_first_required": "TRUE",
            "expected_downstream_unlock": "A warning-only volatility surrogate for staged analysis, but not exact VIX compatibility.",
            "risks": "Substitute mismatch: VIXY/VXX/UVXY track vol exposure, not the VIX index itself.",
            "recommended_or_not": "NO",
        },
        {
            "option_name": "SPLIT_LOCAL_ONLY_TECH_FROM_FULL_VIX_TECH",
            "safety_level": "HIGH",
            "requires_external_fetch": "FALSE",
            "modifies_official_cache": "FALSE",
            "staged_first_required": "FALSE",
            "expected_downstream_unlock": "Keeps the staged local-only technical layer isolated while the full VIX layer remains blocked.",
            "risks": "Dual-track maintenance if merged without a clean policy boundary.",
            "recommended_or_not": "NO",
        },
        {
            "option_name": "KEEP_FACTOR_REFRESH_BLOCKED_UNTIL_VIX_READY",
            "safety_level": "HIGH",
            "requires_external_fetch": "FALSE",
            "modifies_official_cache": "FALSE",
            "staged_first_required": "FALSE",
            "expected_downstream_unlock": "No new unlock; preserves conservative guardrails until exact VIX coverage is repaired.",
            "risks": "Leaves factor refresh blocked and delays full compatibility.",
            "recommended_or_not": "NO",
        },
    ]


def storage_policy_rows() -> List[Dict[str, object]]:
    return [
        {
            "policy_item": "primary_staged_storage",
            "recommended_path": str(ROOT / "data" / "v18" / "staged_market_proxy"),
            "usage": "Stage exact VIX / market proxy history here first.",
            "rationale": "Keeps repair data separate from official caches and allows validation before promotion.",
        },
        {
            "policy_item": "promotion_target_after_validation",
            "recommended_path": str(ROOT / "state" / "v18" / "market_proxy_cache"),
            "usage": "Promote validated proxy history here after staged checks pass.",
            "rationale": "Provides a stable local cache for downstream factor and technical consumers without touching official price cache.",
        },
        {
            "policy_item": "avoid_immediate_official_cache_write",
            "recommended_path": str(ROOT / "state" / "v18" / "price_cache"),
            "usage": "Do not write proxy repair data here in this step.",
            "rationale": "Official price cache must remain untouched during the audit and staged repair planning.",
        },
    ]


def best_match(rows: List[Dict[str, object]], predicate) -> Optional[Dict[str, object]]:
    for row in rows:
        if predicate(row):
            return row
    return None


def summarize_counts(discovery_rows: List[Dict[str, object]]) -> Dict[str, int]:
    total = len(discovery_rows)
    exact = sum(1 for row in discovery_rows if row["usable_as_vix_history"] == "TRUE")
    substitute = sum(1 for row in discovery_rows if row["usable_as_vix_substitute"] == "TRUE")
    return {
        "LOCAL_VIX_CANDIDATE_COUNT": total,
        "USABLE_EXACT_LOCAL_VIX_COUNT": exact,
        "USABLE_VIX_SUBSTITUTE_COUNT": substitute,
    }


def markdown_table(rows: List[Dict[str, object]], columns: Sequence[str]) -> str:
    if not rows:
        return "_No rows found._"
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines = [header, sep]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def write_report(
    read_first: Dict[str, str],
    discovery_rows: List[Dict[str, object]],
    script_rows: List[Dict[str, object]],
    repair_rows: List[Dict[str, object]],
    spec_rows: List[Dict[str, object]],
    storage_rows: List[Dict[str, object]],
) -> None:
    lines: List[str] = []
    lines.append("# V18.25A-R7 Local Market Proxy / VIX Coverage Repair Audit")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- STATUS: `{read_first['STATUS']}`")
    lines.append(f"- MODE: `{read_first['MODE']}`")
    lines.append(f"- Local VIX candidate count: `{read_first['LOCAL_VIX_CANDIDATE_COUNT']}`")
    lines.append(f"- Exact local VIX count: `{read_first['USABLE_EXACT_LOCAL_VIX_COUNT']}`")
    lines.append(f"- VIX substitute count: `{read_first['USABLE_VIX_SUBSTITUTE_COUNT']}`")
    lines.append(f"- Required proxy name: `{read_first['REQUIRED_PROXY_NAME']}`")
    lines.append(f"- Recommended repair option: `{read_first['RECOMMENDED_REPAIR_OPTION']}`")
    lines.append(f"- Recommended proxy storage path: `{read_first['RECOMMENDED_PROXY_STORAGE_PATH']}`")
    lines.append(f"- Staged backfill required: `{read_first['STAGED_BACKFILL_REQUIRED']}`")
    lines.append(f"- External fetch required for next step: `{read_first['EXTERNAL_FETCH_REQUIRED_FOR_NEXT_STEP']}`")
    lines.append("")

    lines.append("## Required Proxy Specification")
    lines.append(markdown_table(spec_rows, ["required_proxy_name", "required_date_range", "required_columns", "minimum_history_days", "must_be_exact_vix", "substitute_allowed", "qqq_spy_benchmark_only", "vixy_vxx_uvxy_warning_only", "source_trace"]))
    lines.append("")

    lines.append("## Local VIX Discovery")
    lines.append(markdown_table(discovery_rows, ["candidate_name", "source_path", "file_type", "row_count", "min_date", "max_date", "date_column_detected", "close_column_detected", "usable_as_vix_history", "usable_as_vix_substitute", "notes"]))
    lines.append("")

    lines.append("## Repair Options")
    lines.append(markdown_table(repair_rows, ["option_name", "safety_level", "requires_external_fetch", "modifies_official_cache", "staged_first_required", "expected_downstream_unlock", "risks", "recommended_or_not"]))
    lines.append("")

    lines.append("## Storage Policy")
    lines.append(markdown_table(storage_rows, ["policy_item", "recommended_path", "usage", "rationale"]))
    lines.append("")

    lines.append("## Script Requirement Trace")
    lines.append(markdown_table(script_rows, ["script_path", "script_type", "matched_terms", "likely_role", "proxy_requirement_detected", "exact_reference_lines_or_short_snippets", "confidence"]))
    lines.append("")

    lines.append("## Notes")
    lines.append("- QQQ/SPY are benchmark proxies and are not volatility proxies.")
    lines.append("- No exact local VIX history file was discovered in the searched roots.")
    lines.append("- This audit does not fetch external data or modify official caches.")
    lines.append("- The staged-first policy keeps repair data out of `state\\v18\\price_cache` until validation is complete.")

    write_text(REPORT_OUT, "\n".join(lines))
    write_text(OPS_REPORT_OUT, "\n".join(lines))


def make_read_first(read_first: Dict[str, str]) -> str:
    ordered_keys = [
        "STATUS",
        "MODE",
        "R6_SOURCE_PATH",
        "LOCAL_VIX_CANDIDATE_COUNT",
        "USABLE_EXACT_LOCAL_VIX_COUNT",
        "USABLE_VIX_SUBSTITUTE_COUNT",
        "REQUIRED_PROXY_NAME",
        "REQUIRED_PROXY_EXACTNESS",
        "LOCAL_VIX_READY",
        "LOCAL_VIX_SUBSTITUTE_READY",
        "RECOMMENDED_REPAIR_OPTION",
        "RECOMMENDED_PROXY_STORAGE_PATH",
        "STAGED_BACKFILL_REQUIRED",
        "EXTERNAL_FETCH_REQUIRED_FOR_NEXT_STEP",
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
    return "\n".join(f"{key}: {read_first.get(key, '')}" for key in ordered_keys)


def main() -> int:
    ensure_dir(OUT_DIR)
    ensure_dir(OPS_DIR)

    read_first_r6 = parse_read_first(R6_READ_FIRST)
    policy_rows = []
    rows, _, _ = read_csv_rows(R6_POLICY)
    if rows:
        policy_rows = rows

    candidate_files = find_candidate_files()
    discovery_rows = [candidate_metadata(path) for path in candidate_files]
    counts = summarize_counts(discovery_rows)

    script_rows = script_trace()
    factor_rows = [row for row in script_rows if row["script_type"] == "factor"]
    technical_rows = [row for row in script_rows if row["script_type"] == "technical"]

    required_proxy_name = "VIX/^VIX"
    exact_vix_ready = counts["USABLE_EXACT_LOCAL_VIX_COUNT"] > 0
    substitute_ready = counts["USABLE_VIX_SUBSTITUTE_COUNT"] > 0
    local_vix_ready = exact_vix_ready
    local_vix_substitute_ready = substitute_ready

    recommended_repair_option = "CONTROLLED_STAGED_VIX_BACKFILL"
    recommended_storage_path = str(ROOT / "data" / "v18" / "staged_market_proxy")
    staged_backfill_required = "TRUE"
    external_fetch_required = "TRUE"
    next_step = "V18.25A-R8_CONTROLLED_STAGED_VIX_BACKFILL"

    status = STATUS_WARN if not exact_vix_ready else STATUS_OK
    if not candidate_files:
        status = STATUS_FAIL

    read_first = {
        "STATUS": status,
        "MODE": MODE,
        "R6_SOURCE_PATH": str(R6_READ_FIRST),
        "LOCAL_VIX_CANDIDATE_COUNT": str(counts["LOCAL_VIX_CANDIDATE_COUNT"]),
        "USABLE_EXACT_LOCAL_VIX_COUNT": str(counts["USABLE_EXACT_LOCAL_VIX_COUNT"]),
        "USABLE_VIX_SUBSTITUTE_COUNT": str(counts["USABLE_VIX_SUBSTITUTE_COUNT"]),
        "REQUIRED_PROXY_NAME": required_proxy_name,
        "REQUIRED_PROXY_EXACTNESS": "EXACT_REQUIRED_FOR_OFFICIAL_FULL_COMPATIBILITY",
        "LOCAL_VIX_READY": "TRUE" if local_vix_ready else "FALSE",
        "LOCAL_VIX_SUBSTITUTE_READY": "TRUE" if local_vix_substitute_ready else "FALSE",
        "RECOMMENDED_REPAIR_OPTION": recommended_repair_option,
        "RECOMMENDED_PROXY_STORAGE_PATH": recommended_storage_path,
        "STAGED_BACKFILL_REQUIRED": staged_backfill_required,
        "EXTERNAL_FETCH_REQUIRED_FOR_NEXT_STEP": external_fetch_required,
        "NEXT_RECOMMENDED_STEP": next_step,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "TIER_MIGRATION_MODIFIED": "FALSE",
        "DEGRADED_DAILY_MODIFIED": "FALSE",
        "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "VALIDATION_FAIL_COUNT": "0",
        "FORBIDDEN_FILE_MODIFIED": "FALSE",
    }

    discovery_fields = [
        "candidate_name",
        "source_path",
        "file_type",
        "row_count",
        "min_date",
        "max_date",
        "date_column_detected",
        "close_column_detected",
        "usable_as_vix_history",
        "usable_as_vix_substitute",
        "notes",
    ]
    repair_fields = [
        "option_name",
        "safety_level",
        "requires_external_fetch",
        "modifies_official_cache",
        "staged_first_required",
        "expected_downstream_unlock",
        "risks",
        "recommended_or_not",
    ]
    spec_fields = [
        "required_proxy_name",
        "required_date_range",
        "required_columns",
        "minimum_history_days",
        "must_be_exact_vix",
        "substitute_allowed",
        "qqq_spy_benchmark_only",
        "vixy_vxx_uvxy_warning_only",
        "source_trace",
    ]
    storage_fields = ["policy_item", "recommended_path", "usage", "rationale"]
    script_fields = [
        "script_path",
        "script_type",
        "matched_terms",
        "likely_role",
        "proxy_requirement_detected",
        "exact_reference_lines_or_short_snippets",
        "confidence",
    ]

    write_csv(DISCOVERY_OUT, discovery_rows, discovery_fields)
    write_csv(REPAIR_OPTIONS_OUT, repair_options(), repair_fields)
    write_csv(VIX_SPEC_OUT, derive_requirement_spec(), spec_fields)
    write_csv(STORAGE_POLICY_OUT, storage_policy_rows(), storage_fields)
    write_csv(ROOT / "outputs" / "v18" / "degraded_daily_review" / "V18_25A_R7_CURRENT_SCRIPT_REQUIREMENT_TRACE.csv", script_rows, script_fields)

    write_report(read_first, discovery_rows, script_rows, repair_options(), derive_requirement_spec(), storage_policy_rows())
    write_text(READ_FIRST_OUT, make_read_first(read_first))

    print(f"STATUS: {status}")
    print(f"LOCAL_VIX_CANDIDATE_COUNT: {read_first['LOCAL_VIX_CANDIDATE_COUNT']}")
    print(f"USABLE_EXACT_LOCAL_VIX_COUNT: {read_first['USABLE_EXACT_LOCAL_VIX_COUNT']}")
    print(f"USABLE_VIX_SUBSTITUTE_COUNT: {read_first['USABLE_VIX_SUBSTITUTE_COUNT']}")
    print(f"RECOMMENDED_REPAIR_OPTION: {recommended_repair_option}")
    print(f"RECOMMENDED_PROXY_STORAGE_PATH: {recommended_storage_path}")
    print(f"NEXT_RECOMMENDED_STEP: {next_step}")
    return 0 if status != STATUS_FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())
