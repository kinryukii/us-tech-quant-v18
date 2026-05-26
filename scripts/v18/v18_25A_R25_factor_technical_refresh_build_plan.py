from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R25_FACTOR_TECHNICAL_REFRESH_PLAN_READY"
STATUS_INPUTS_MISSING = "WARN_V18_25A_R25_R24_INPUTS_MISSING"
STATUS_ZERO_TARGETS = "WARN_V18_25A_R25_ZERO_TARGETS"
STATUS_SCHEMA_REVIEW = "WARN_V18_25A_R25_SCHEMA_REVIEW_NEEDED"
STATUS_SCRIPT_REVIEW = "WARN_V18_25A_R25_SOURCE_SCRIPT_REVIEW_NEEDED"
STATUS_PARTIAL = "WARN_V18_25A_R25_PARTIAL_INPUTS_USED"

MODE = "READ_ONLY_FACTOR_TECHNICAL_REFRESH_PLAN"

R24_ACTION = "outputs/v18/readiness/V18_25A_R24_CURRENT_NEXT_ACTION_PLAN.csv"
R24_SUMMARY = "outputs/v18/readiness/V18_25A_R24_CURRENT_REFRESH_READINESS_SUMMARY.csv"
R24_PRICE = "outputs/v18/readiness/V18_25A_R24_CURRENT_PRICE_LEDGER_READINESS.csv"
R24_FACTOR = "outputs/v18/readiness/V18_25A_R24_CURRENT_FACTOR_READINESS.csv"
R24_TECH = "outputs/v18/readiness/V18_25A_R24_CURRENT_TECHNICAL_READINESS.csv"
R24_TIER = "outputs/v18/readiness/V18_25A_R24_CURRENT_TIER_READINESS.csv"
PRICE_CACHE = "state/v18/price_cache"
FACTOR = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECHNICAL = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OUT_FACTOR = "outputs/v18/readiness/V18_25A_R25_CURRENT_FACTOR_BUILD_PLAN.csv"
OUT_TECH = "outputs/v18/readiness/V18_25A_R25_CURRENT_TECHNICAL_REFRESH_PLAN.csv"
OUT_COMBINED = "outputs/v18/readiness/V18_25A_R25_CURRENT_COMBINED_REFRESH_PLAN.csv"
OUT_SCRIPT = "outputs/v18/readiness/V18_25A_R25_CURRENT_SOURCE_SCRIPT_AUDIT.csv"
OUT_SCHEMA = "outputs/v18/readiness/V18_25A_R25_CURRENT_SCHEMA_COMPATIBILITY_AUDIT.csv"
OUT_BLOCKERS = "outputs/v18/readiness/V18_25A_R25_CURRENT_BLOCKERS_AND_HOLDS.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R25_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R25_CURRENT_FACTOR_TECHNICAL_REFRESH_PLAN_REPORT.md"

FACTOR_FIELDS = ["priority_rank", "ticker", "price_row_count", "min_price_date", "max_price_date", "latest_close", "latest_volume", "enough_history_for_factor_build", "factor_plan_status", "reason", "source_batch"]
TECH_FIELDS = ["priority_rank", "ticker", "price_row_count", "min_price_date", "max_price_date", "latest_close", "latest_volume", "enough_history_for_technical_refresh", "technical_plan_status", "reason", "source_batch"]
COMBINED_FIELDS = ["priority_rank", "ticker", "source_batch", "price_ledger_ready", "factor_ready", "technical_ready", "factor_plan_status", "technical_plan_status", "combined_action", "reason"]
SCRIPT_FIELDS = ["script_path", "script_type", "exists", "parse_check_status", "likely_usable_for_next_step", "notes"]
SCHEMA_FIELDS = ["audit_item", "value", "notes"]
BLOCKER_FIELDS = ["ticker", "blocker_type", "reason", "next_action"]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "RUN_ID", "MAX_TICKERS", "R24_NEXT_ACTION_PLAN_PATH", "EXPECTED_R24_READY_FOR_FACTOR_BUILD_COUNT",
    "EXPECTED_R24_TECHNICAL_MISSING_COUNT", "SELECTED_TARGET_COUNT", "DEDUPED_TARGET_COUNT", "PRICE_LEDGER_READY_TARGET_COUNT",
    "FACTOR_BUILD_READY_COUNT", "FACTOR_BUILD_HOLD_COUNT", "TECHNICAL_REFRESH_READY_COUNT", "TECHNICAL_REFRESH_HOLD_COUNT",
    "BUILD_FACTOR_AND_TECHNICAL_COUNT", "BUILD_FACTOR_ONLY_COUNT", "REFRESH_TECHNICAL_ONLY_COUNT", "HOLD_REVIEW_NEEDED_COUNT",
    "TECHNICAL_REFRESH_ZERO_READY_EXPLANATION", "SOURCE_SCRIPT_AUDIT_PATH", "SCHEMA_COMPATIBILITY_AUDIT_PATH", "FACTOR_BUILD_PLAN_PATH",
    "TECHNICAL_REFRESH_PLAN_PATH", "COMBINED_REFRESH_PLAN_PATH", "BLOCKERS_AND_HOLDS_PATH", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE",
    "AUTO_SELL", "EXTERNAL_FETCH_EXECUTED", "BACKTEST_EXECUTED", "PRICE_CACHE_MODIFIED", "ROLLING_LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "TIER_FILES_MODIFIED", "OFFICIAL_DECISION_MODIFIED",
    "VALIDATION_FAIL_COUNT", "FORBIDDEN_MODIFIED", "NEXT_RECOMMENDED_STEP",
]


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
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def price_profile(path: Path) -> Dict[str, object]:
    rows, fields = read_csv(path)
    dates = [str(row.get("date", "") or "").strip() for row in rows if str(row.get("date", "") or "").strip()]
    latest = sorted(rows, key=lambda row: str(row.get("date", "")))[-1] if rows else {}
    return {
        "readable": bool(fields),
        "row_count": len(rows),
        "min_date": min(dates) if dates else "",
        "max_date": max(dates) if dates else "",
        "latest_close": latest.get("close", ""),
        "latest_volume": latest.get("volume", ""),
        "required_ok": all(col in {f.lower() for f in fields} for col in ["date", "open", "high", "low", "close", "volume"]),
    }


def action_count(rows: List[Dict[str, str]], action: str) -> int:
    for row in rows:
        if str(row.get("action", "")).strip().upper() == action:
            return to_int(row.get("ticker_count"))
    return 0


def parse_script(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.suffix.lower() == ".py":
        try:
            ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            return "PY_AST_PARSE_OK"
        except Exception as exc:
            return f"PY_AST_PARSE_FAIL:{type(exc).__name__}"
    if path.suffix.lower() == ".ps1":
        return "PS_PARSE_NOT_CHECKED_IN_R25"
    return "NOT_APPLICABLE"


def audit_scripts(root: Path) -> List[Dict[str, object]]:
    preferred = [
        "scripts/v18/v18_25A_R13_targeted_factor_pack_refresh_staged.py",
        "scripts/v18/run_v18_25A_R13_targeted_factor_pack_refresh_staged.ps1",
        "scripts/v18/v18_25A_R11_full_compatible_technical_timing_refresh_with_vix.py",
        "scripts/v18/run_v18_25A_R11_full_compatible_technical_timing_refresh_with_vix.ps1",
        "scripts/v18/v18_21A_price_derived_factor_pack.py",
        "scripts/v18/v18_6A_technical_timing_shadow.py",
    ]
    rows = []
    for rel in preferred:
        path = root / rel
        script_type = "FACTOR" if "factor" in rel.lower() or "21a" in rel.lower() or "r13" in rel.lower() else "TECHNICAL"
        exists = path.exists()
        rows.append({
            "script_path": rel,
            "script_type": script_type,
            "exists": str(exists).upper(),
            "parse_check_status": parse_script(path),
            "likely_usable_for_next_step": str(exists and path.suffix.lower() in {".py", ".ps1"}).upper(),
            "notes": "Candidate source for R25B staged build planning; not executed by R25.",
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--max-tickers", type=int, default=100)
    parser.add_argument("--include-technical-plan", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R25_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    before = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": tree_sig(root / "outputs/v18/factor_pack"),
        "technical": tree_sig(root / "outputs/v18/technical_timing"),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
    }

    action_rows, _ = read_csv(root / R24_ACTION)
    summary_rows, _ = read_csv(root / R24_SUMMARY)
    price_rows, _ = read_csv(root / R24_PRICE)
    factor_rows, _ = read_csv(root / R24_FACTOR)
    tech_rows, _ = read_csv(root / R24_TECH)
    tier_rows, _ = read_csv(root / R24_TIER)
    factor_current, factor_fields = read_csv(root / FACTOR)
    tech_current, tech_fields = read_csv(root / TECHNICAL)

    status = STATUS_OK
    validation_fail_count = 0
    if not action_rows or not summary_rows or not price_rows or not factor_rows or not tech_rows:
        status = STATUS_INPUTS_MISSING
        validation_fail_count = 1

    price_by = {norm_ticker(r.get("ticker")): r for r in price_rows}
    factor_by = {norm_ticker(r.get("ticker")): r for r in factor_rows}
    tech_by = {norm_ticker(r.get("ticker")): r for r in tech_rows}
    candidates = []
    for row in summary_rows:
        ticker = norm_ticker(row.get("ticker"))
        if not ticker:
            continue
        price_ready = is_true(row.get("price_ledger_ready")) and is_true(price_by.get(ticker, {}).get("price_ledger_ready"))
        factor_ready = is_true(row.get("factor_ready"))
        tech_ready = is_true(row.get("technical_ready"))
        hold = str(row.get("overall_classification", "")).upper().startswith("HOLD")
        if price_ready and not hold and (not factor_ready or not tech_ready):
            candidates.append(ticker)
    seen = []
    for ticker in candidates:
        if ticker not in seen:
            seen.append(ticker)
    targets = seen[: max(args.max_tickers, 0)]
    if status == STATUS_OK and not targets:
        status = STATUS_ZERO_TARGETS
        validation_fail_count = 1

    factor_plan = []
    tech_plan = []
    combined = []
    blockers = []
    for idx, ticker in enumerate(targets, 1):
        srow = next((r for r in summary_rows if norm_ticker(r.get("ticker")) == ticker), {})
        prof = price_profile(root / PRICE_CACHE / f"{ticker}.csv")
        source_batch = srow.get("source_batch", "")
        enough_factor = bool(prof["readable"] and prof["required_ok"] and to_int(prof["row_count"]) >= 500)
        enough_tech = bool(prof["readable"] and prof["required_ok"] and to_int(prof["row_count"]) >= 120)
        factor_ready_current = is_true(factor_by.get(ticker, {}).get("factor_ready"))
        tech_ready_current = is_true(tech_by.get(ticker, {}).get("technical_ready"))
        if factor_ready_current:
            f_status = "NO_ACTION_ALREADY_READY"
            f_reason = "Factor row already ready."
        elif enough_factor:
            f_status = "READY_FOR_FACTOR_ROW_BUILD"
            f_reason = "Price cache has sufficient local history and required OHLCV schema."
        elif prof["readable"]:
            f_status = "HOLD_INSUFFICIENT_PRICE_HISTORY"
            f_reason = "Price history below factor minimum."
        else:
            f_status = "HOLD_PRICE_CACHE_UNREADABLE"
            f_reason = "Official price cache is unreadable or missing."
        if tech_ready_current:
            t_status = "NO_ACTION_ALREADY_READY"
            t_reason = "Technical timing row already ready."
        elif enough_tech and args.include_technical_plan:
            t_status = "READY_FOR_TECHNICAL_TIMING_REFRESH"
            t_reason = "Price cache has sufficient local history and required OHLCV schema."
        elif not args.include_technical_plan:
            t_status = "HOLD_SCHEMA_REVIEW_NEEDED"
            t_reason = "Technical plan disabled by wrapper option."
        elif prof["readable"]:
            t_status = "HOLD_INSUFFICIENT_PRICE_HISTORY"
            t_reason = "Price history below technical minimum."
        else:
            t_status = "HOLD_PRICE_CACHE_UNREADABLE"
            t_reason = "Official price cache is unreadable or missing."
        factor_plan.append({"priority_rank": idx, "ticker": ticker, "price_row_count": prof["row_count"], "min_price_date": prof["min_date"], "max_price_date": prof["max_date"], "latest_close": prof["latest_close"], "latest_volume": prof["latest_volume"], "enough_history_for_factor_build": str(enough_factor).upper(), "factor_plan_status": f_status, "reason": f_reason, "source_batch": source_batch})
        tech_plan.append({"priority_rank": idx, "ticker": ticker, "price_row_count": prof["row_count"], "min_price_date": prof["min_date"], "max_price_date": prof["max_date"], "latest_close": prof["latest_close"], "latest_volume": prof["latest_volume"], "enough_history_for_technical_refresh": str(enough_tech).upper(), "technical_plan_status": t_status, "reason": t_reason, "source_batch": source_batch})
        f_build = f_status == "READY_FOR_FACTOR_ROW_BUILD"
        t_build = t_status == "READY_FOR_TECHNICAL_TIMING_REFRESH"
        if f_build and t_build:
            action = "BUILD_FACTOR_AND_TECHNICAL"
        elif f_build:
            action = "BUILD_FACTOR_ONLY"
        elif t_build:
            action = "REFRESH_TECHNICAL_ONLY"
        elif f_status == "NO_ACTION_ALREADY_READY" and t_status == "NO_ACTION_ALREADY_READY":
            action = "NO_ACTION_ALREADY_READY"
        else:
            action = "HOLD_REVIEW_NEEDED"
            blockers.append({"ticker": ticker, "blocker_type": "REFRESH_PLAN_HOLD", "reason": f"{f_status};{t_status}", "next_action": "Review price/schema readiness before R25B."})
        combined.append({"priority_rank": idx, "ticker": ticker, "source_batch": source_batch, "price_ledger_ready": "TRUE", "factor_ready": str(factor_ready_current).upper(), "technical_ready": str(tech_ready_current).upper(), "factor_plan_status": f_status, "technical_plan_status": t_status, "combined_action": action, "reason": f"{f_reason} {t_reason}"})

    script_rows = audit_scripts(root)
    source_review_needed = any(r["exists"] != "TRUE" or "FAIL" in str(r["parse_check_status"]) for r in script_rows)
    factor_required = ["ticker", "factor_pack_score", "factor_pack_rank", "latest_price_date", "latest_close"]
    tech_required = ["ticker", "price_date", "close", "technical_timing_score", "technical_signal"]
    factor_missing = [c for c in factor_required if c not in factor_fields]
    tech_missing = [c for c in tech_required if c not in tech_fields]
    schema_ok = not factor_missing and not tech_missing
    schema_rows = [
        {"audit_item": "factor_pack_schema_available", "value": str(bool(factor_fields)).upper(), "notes": FACTOR},
        {"audit_item": "factor_pack_required_columns", "value": ";".join(factor_required), "notes": ""},
        {"audit_item": "factor_pack_missing_required_columns", "value": ";".join(factor_missing), "notes": ""},
        {"audit_item": "technical_schema_available", "value": str(bool(tech_fields)).upper(), "notes": TECHNICAL},
        {"audit_item": "technical_required_columns", "value": ";".join(tech_required), "notes": ""},
        {"audit_item": "technical_missing_required_columns", "value": ";".join(tech_missing), "notes": ""},
        {"audit_item": "compatible_for_next_build_step", "value": str(schema_ok).upper(), "notes": ""},
    ]
    if status == STATUS_OK and not schema_ok:
        status = STATUS_SCHEMA_REVIEW
    elif status == STATUS_OK and source_review_needed:
        status = STATUS_SCRIPT_REVIEW
    elif status == STATUS_OK and (not tier_rows or not factor_current or not tech_current):
        status = STATUS_PARTIAL

    write_csv(root / OUT_FACTOR, factor_plan, FACTOR_FIELDS)
    write_csv(root / OUT_TECH, tech_plan, TECH_FIELDS)
    write_csv(root / OUT_COMBINED, combined, COMBINED_FIELDS)
    write_csv(root / OUT_SCRIPT, script_rows, SCRIPT_FIELDS)
    write_csv(root / OUT_SCHEMA, schema_rows, SCHEMA_FIELDS)
    write_csv(root / OUT_BLOCKERS, blockers, BLOCKER_FIELDS)

    after = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": tree_sig(root / "outputs/v18/factor_pack"),
        "technical": tree_sig(root / "outputs/v18/technical_timing"),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
    }
    mods = {k: before[k] != after[k] for k in before}
    forbidden = any(mods.values())

    build_both = sum(1 for r in combined if r["combined_action"] == "BUILD_FACTOR_AND_TECHNICAL")
    build_factor_only = sum(1 for r in combined if r["combined_action"] == "BUILD_FACTOR_ONLY")
    tech_only = sum(1 for r in combined if r["combined_action"] == "REFRESH_TECHNICAL_ONLY")
    hold = sum(1 for r in combined if r["combined_action"] == "HOLD_REVIEW_NEEDED")
    tech_explanation = "R24 reported zero ready-for-technical-refresh because its overall classification prioritized missing factor rows first; R25 plans technical refresh in parallel for price/ledger-ready tickers with missing technical rows."
    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "MAX_TICKERS": args.max_tickers,
        "R24_NEXT_ACTION_PLAN_PATH": R24_ACTION,
        "EXPECTED_R24_READY_FOR_FACTOR_BUILD_COUNT": action_count(action_rows, "BUILD_FACTOR_ROWS"),
        "EXPECTED_R24_TECHNICAL_MISSING_COUNT": sum(1 for r in tech_rows if not is_true(r.get("technical_ready"))),
        "SELECTED_TARGET_COUNT": len(targets),
        "DEDUPED_TARGET_COUNT": len(targets),
        "PRICE_LEDGER_READY_TARGET_COUNT": len(targets),
        "FACTOR_BUILD_READY_COUNT": sum(1 for r in factor_plan if r["factor_plan_status"] == "READY_FOR_FACTOR_ROW_BUILD"),
        "FACTOR_BUILD_HOLD_COUNT": sum(1 for r in factor_plan if str(r["factor_plan_status"]).startswith("HOLD")),
        "TECHNICAL_REFRESH_READY_COUNT": sum(1 for r in tech_plan if r["technical_plan_status"] == "READY_FOR_TECHNICAL_TIMING_REFRESH"),
        "TECHNICAL_REFRESH_HOLD_COUNT": sum(1 for r in tech_plan if str(r["technical_plan_status"]).startswith("HOLD")),
        "BUILD_FACTOR_AND_TECHNICAL_COUNT": build_both,
        "BUILD_FACTOR_ONLY_COUNT": build_factor_only,
        "REFRESH_TECHNICAL_ONLY_COUNT": tech_only,
        "HOLD_REVIEW_NEEDED_COUNT": hold,
        "TECHNICAL_REFRESH_ZERO_READY_EXPLANATION": tech_explanation,
        "SOURCE_SCRIPT_AUDIT_PATH": OUT_SCRIPT,
        "SCHEMA_COMPATIBILITY_AUDIT_PATH": OUT_SCHEMA,
        "FACTOR_BUILD_PLAN_PATH": OUT_FACTOR,
        "TECHNICAL_REFRESH_PLAN_PATH": OUT_TECH,
        "COMBINED_REFRESH_PLAN_PATH": OUT_COMBINED,
        "BLOCKERS_AND_HOLDS_PATH": OUT_BLOCKERS,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "PRICE_CACHE_MODIFIED": str(mods["price"]).upper(),
        "ROLLING_LEDGER_MODIFIED": str(mods["ledger"]).upper(),
        "FACTOR_PACK_MODIFIED": str(mods["factor"]).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(mods["technical"]).upper(),
        "TIER_FILES_MODIFIED": str(mods["tier"]).upper(),
        "OFFICIAL_DECISION_MODIFIED": str(mods["decision"]).upper(),
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden).upper(),
        "NEXT_RECOMMENDED_STEP": "R25B: Build staged factor and technical rows for approved targets, without merging into current official ranking until validation passes.",
    }
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    report = "\n".join([
        "# V18.25A R25 Factor Technical Refresh Plan Report",
        "",
        f"STATUS: {status}",
        f"MODE: {MODE}",
        f"RUN_ID: {run_id}",
        "",
        "## Plan",
        f"- selected_targets: {len(targets)}",
        f"- factor_build_ready: {values['FACTOR_BUILD_READY_COUNT']}",
        f"- technical_refresh_ready: {values['TECHNICAL_REFRESH_READY_COUNT']}",
        f"- build_factor_and_technical: {build_both}",
        "",
        "## Explanation",
        tech_explanation,
        "",
        "## Safety",
        "- protected artifacts modified: FALSE",
        "",
    ])
    write_text(root / OUT_REPORT, report)
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
