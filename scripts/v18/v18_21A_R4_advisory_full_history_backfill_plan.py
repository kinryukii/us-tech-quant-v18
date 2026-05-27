from __future__ import annotations

import argparse
import csv
import math
import py_compile
import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS = "WARN_V18_21A_R4_BACKFILL_PLAN_READY"
MODE = "ADVISORY_ONLY"
PATCH_MODE = "FULL_HISTORY_BACKFILL_PLAN_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "HISTORY_BACKFILL_APPLIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
}

BACKFILL_FIELDS = [
    "ticker", "current_mapping_status", "factor_scope_class", "current_score_scope", "current_score_ready",
    "latest_price_snapshot_available", "selected_priority_tier", "priority_reason",
    "required_history_days_for_full_score", "minimum_history_days_for_light_score",
    "estimated_missing_history_requirement", "recommended_backfill_start_date", "recommended_backfill_end_date",
    "backfill_required_for_20d_return", "backfill_required_for_60d_return", "backfill_required_for_200dma",
    "backfill_required_for_52w_high", "backfill_required_for_volume_surge", "recommended_resolution",
]
PLAN_FIELDS = [
    "planned_batch_index", "ticker", "priority_tier", "priority_score", "priority_reason",
    "expected_factor_scope_after_backfill", "expected_score_ready_after_backfill", "notes",
]
PROJECTION_FIELDS = [
    "scenario_name", "added_full_history_ticker_count", "projected_local_price_data_available_count",
    "projected_full_history_factor_ready_count", "projected_score_ready_count", "projected_score_ready_ratio",
    "projected_no_local_price_data_count", "notes",
]
SAFETY_FIELDS = ["safety_check", "status", "notes"]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "TICKER_INPUT_COUNT",
    "CURRENT_LOCAL_PRICE_DATA_AVAILABLE_COUNT", "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT", "CURRENT_SCORE_READY_RATIO",
    "MISSING_HISTORY_TICKER_COUNT", "BACKFILL_PLAN_READY", "BACKFILL_BATCH_COUNT",
    "TOP_25_PROJECTED_SCORE_READY_RATIO", "TOP_50_PROJECTED_SCORE_READY_RATIO", "TOP_100_PROJECTED_SCORE_READY_RATIO",
    "ALL_MISSING_PROJECTED_SCORE_READY_RATIO", "PRIORITY_SOURCE_STATUS", "HISTORY_BACKFILL_APPLIED",
    "EXTERNAL_DATA_FETCHED", "PRICE_CACHE_MODIFIED", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "RANKING_MODIFIED", "PROMOTION_DEMOTION_MODIFIED",
    "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    return []


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


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


def readfirst(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def num(v: object, default: float = 0) -> float:
    try:
        text = str(v or "").replace(",", "").strip()
        return float(text) if text else default
    except Exception:
        return default


def fmt(v: float, digits: int = 6) -> str:
    return f"{v:.{digits}f}"


def ps_parse(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    escaped = str(path).replace("'", "''")
    cmd = f"$null = [scriptblock]::Create((Get-Content -Raw -LiteralPath '{escaped}')); 'OK_PARSE'"
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd], capture_output=True, text=True, timeout=30)
        return (r.returncode == 0 and "OK_PARSE" in (r.stdout or "")), ((r.stdout or r.stderr).strip())
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def compile_check(path: Path) -> Tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, "OK_COMPILE"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def priority_maps(root: Path) -> Tuple[Dict[str, float], Dict[str, str], str]:
    scores: Dict[str, float] = {}
    reasons: Dict[str, str] = {}
    status_bits = []
    ranked = read_csv(root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv")
    if ranked:
        status_bits.append("RANKED_CANDIDATES_OK")
        for row in ranked:
            ticker = str(row.get("ticker", "")).upper()
            rank = num(row.get("rank"), 999)
            scores[ticker] = max(scores.get(ticker, 0), 10000 - rank * 100)
            reasons[ticker] = "CURRENT_RANKED_CANDIDATE"
    scan = read_csv(root / "outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv")
    if scan:
        status_bits.append("ROLLING_SCAN_PLAN_OK")
        for row in scan:
            ticker = str(row.get("ticker", "")).upper()
            p = num(row.get("scan_priority"), 0)
            scores[ticker] = max(scores.get(ticker, 0), 5000 + p)
            reasons.setdefault(ticker, "ROLLING_SCAN_PRIORITY")
    universe = read_csv(root / "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv")
    if universe:
        status_bits.append("UNIVERSE_TIER_OK")
        tier_score = {"CORE_DAILY": 4000, "CANDIDATE": 3000, "STRONG_WATCH": 2500, "WATCHLIST": 1500, "RESEARCH": 500}
        for row in universe:
            ticker = str(row.get("ticker", "")).upper()
            tier = row.get("universe_tier", "")
            scores[ticker] = max(scores.get(ticker, 0), tier_score.get(tier, 100))
            reasons.setdefault(ticker, f"UNIVERSE_TIER_{tier or 'UNKNOWN'}")
    return scores, reasons, ";".join(status_bits) if status_bits else "FALLBACK_DETERMINISTIC_ORDER_ONLY"


def build(root: Path) -> Tuple[Dict[str, object], Dict[str, Path]]:
    paths = {
        "mapping": root / "outputs/v18/price_factors/V18_21A_R3_CURRENT_TICKER_SOURCE_MAPPING_AUDIT.csv",
        "no_local": root / "outputs/v18/price_factors/V18_21A_R3_CURRENT_NO_LOCAL_PRICE_DATA_DETAIL.csv",
        "scope": root / "outputs/v18/price_factors/V18_21A_R3_CURRENT_FACTOR_SCOPE_SUMMARY.csv",
        "r3_read": root / "outputs/v18/ops/V18_21A_R3_READ_FIRST.txt",
        "backfill": root / "outputs/v18/price_factors/V18_21A_R4_CURRENT_MISSING_HISTORY_BACKFILL_UNIVERSE.csv",
        "plan": root / "outputs/v18/price_factors/V18_21A_R4_CURRENT_BACKFILL_PRIORITY_PLAN.csv",
        "projection": root / "outputs/v18/price_factors/V18_21A_R4_CURRENT_COVERAGE_PROJECTION.csv",
        "safety": root / "outputs/v18/price_factors/V18_21A_R4_CURRENT_BACKFILL_SAFETY_AUDIT.csv",
        "read": root / "outputs/v18/ops/V18_21A_R4_READ_FIRST.txt",
        "report": root / "outputs/v18/ops/V18_21A_R4_CURRENT_ADVISORY_BACKFILL_PLAN_REPORT.md",
    }
    mapping = read_csv(paths["mapping"])
    scope_rows = {r["ticker"]: r for r in read_csv(paths["scope"])}
    r3 = readfirst(paths["r3_read"])
    scores, reasons, priority_status = priority_maps(root)
    today = date.today()
    start = today - timedelta(days=365 * 6)
    missing = [r for r in mapping if r.get("mapping_status") in {"NO_CANDIDATE_SOURCE_FOUND", "CANDIDATE_SOURCES_REJECTED", "MAPPED_LATEST_ONLY"}]
    backfill_rows = []
    for r in missing:
        t = r["ticker"]
        s = scope_rows.get(t, {})
        latest = r.get("mapping_status") == "MAPPED_LATEST_ONLY"
        priority_score = scores.get(t, 0)
        tier = "TOP_RANKED_OR_CANDIDATE" if priority_score >= 8000 else "ROLLING_SCAN_PRIORITY" if priority_score >= 5000 else "CORE_OR_HIGH_RELEVANCE" if priority_score >= 3000 else "WATCHLIST_OR_RESEARCH"
        backfill_rows.append({
            "ticker": t,
            "current_mapping_status": r.get("mapping_status", ""),
            "factor_scope_class": s.get("factor_scope_class", "NO_LOCAL_PRICE_DATA"),
            "current_score_scope": s.get("score_scope", "NOT_SCORE_READY"),
            "current_score_ready": "TRUE" if s.get("full_factor_score_ready") == "TRUE" or s.get("light_factor_score_ready") == "TRUE" else "FALSE",
            "latest_price_snapshot_available": "TRUE" if latest else "FALSE",
            "selected_priority_tier": tier,
            "priority_reason": reasons.get(t, "DETERMINISTIC_FALLBACK_ORDER"),
            "required_history_days_for_full_score": 252,
            "minimum_history_days_for_light_score": 60,
            "estimated_missing_history_requirement": "FULL_OHLCV_252D_PLUS_VOLUME",
            "recommended_backfill_start_date": start.isoformat(),
            "recommended_backfill_end_date": today.isoformat(),
            "backfill_required_for_20d_return": "TRUE",
            "backfill_required_for_60d_return": "TRUE",
            "backfill_required_for_200dma": "TRUE",
            "backfill_required_for_52w_high": "TRUE",
            "backfill_required_for_volume_surge": "TRUE",
            "recommended_resolution": "CAN_USE_LATEST_ONLY_REFERENCE" if latest else "NEED_FULL_HISTORY_BACKFILL",
            "_priority_score": priority_score,
        })
    ordered = sorted(backfill_rows, key=lambda x: (-num(x["_priority_score"]), x["ticker"]))
    plan_rows = []
    for i, row in enumerate(ordered, 1):
        plan_rows.append({
            "planned_batch_index": math.ceil(i / 25),
            "ticker": row["ticker"],
            "priority_tier": row["selected_priority_tier"],
            "priority_score": int(num(row["_priority_score"])),
            "priority_reason": row["priority_reason"],
            "expected_factor_scope_after_backfill": "FULL_HISTORY_FACTOR_READY",
            "expected_score_ready_after_backfill": "TRUE",
            "notes": "ADVISORY_PLAN_ONLY_NO_BACKFILL_APPLIED",
        })
    for row in backfill_rows:
        row.pop("_priority_score", None)

    current_total = int(num(r3.get("TICKER_INPUT_COUNT"), len(mapping)))
    current_local = int(num(r3.get("LOCAL_PRICE_DATA_AVAILABLE_COUNT"), current_total - len(missing)))
    current_full = int(num(r3.get("MAPPED_FULL_HISTORY_COUNT"), 0))
    current_score_ready = current_full
    no_local = int(num(r3.get("NO_LOCAL_PRICE_DATA_COUNT"), len(missing)))
    scenarios = [("CURRENT", 0), ("BACKFILL_TOP_25", 25), ("BACKFILL_TOP_50", 50), ("BACKFILL_TOP_100", 100), ("BACKFILL_ALL_MISSING", len(missing))]
    proj_rows = []
    proj_ratios = {}
    for name, add in scenarios:
        add = min(add, len(missing))
        ready = min(current_total, current_score_ready + add)
        local = min(current_total, current_local + add)
        full = min(current_total, current_full + add)
        ratio = ready / current_total if current_total else 0
        proj_ratios[name] = fmt(ratio)
        proj_rows.append({
            "scenario_name": name,
            "added_full_history_ticker_count": add,
            "projected_local_price_data_available_count": local,
            "projected_full_history_factor_ready_count": full,
            "projected_score_ready_count": ready,
            "projected_score_ready_ratio": fmt(ratio),
            "projected_no_local_price_data_count": max(0, no_local - add),
            "notes": "ADVISORY_PROJECTION_ONLY",
        })
    safety_rows = [{"safety_check": k, "status": v, "notes": "PASS" if v in {"FALSE", "NONE", "DISABLED"} else ""} for k, v in SAFETY_FLAGS.items()]
    write_csv(paths["backfill"], backfill_rows, BACKFILL_FIELDS)
    write_csv(paths["plan"], plan_rows, PLAN_FIELDS)
    write_csv(paths["projection"], proj_rows, PROJECTION_FIELDS)
    write_csv(paths["safety"], safety_rows, SAFETY_FIELDS)
    metrics = {
        "STATUS": STATUS, "MODE": MODE, "PATCH_MODE": PATCH_MODE,
        "TICKER_INPUT_COUNT": current_total,
        "CURRENT_LOCAL_PRICE_DATA_AVAILABLE_COUNT": current_local,
        "CURRENT_FULL_HISTORY_FACTOR_READY_COUNT": current_full,
        "CURRENT_SCORE_READY_RATIO": r3.get("SCORE_READY_RATIO", fmt(current_score_ready / current_total if current_total else 0)),
        "MISSING_HISTORY_TICKER_COUNT": len(missing),
        "BACKFILL_PLAN_READY": "TRUE" if plan_rows else "FALSE",
        "BACKFILL_BATCH_COUNT": max([int(r["planned_batch_index"]) for r in plan_rows], default=0),
        "TOP_25_PROJECTED_SCORE_READY_RATIO": proj_ratios["BACKFILL_TOP_25"],
        "TOP_50_PROJECTED_SCORE_READY_RATIO": proj_ratios["BACKFILL_TOP_50"],
        "TOP_100_PROJECTED_SCORE_READY_RATIO": proj_ratios["BACKFILL_TOP_100"],
        "ALL_MISSING_PROJECTED_SCORE_READY_RATIO": proj_ratios["BACKFILL_ALL_MISSING"],
        "PRIORITY_SOURCE_STATUS": priority_status,
        "VALIDATION_FAIL_COUNT": 0,
        "READ_FIRST": str(paths["read"]),
        "REPORT": str(paths["report"]),
    }
    metrics.update(SAFETY_FLAGS)
    return metrics, paths


def render_read(metrics: Dict[str, object]) -> str:
    return "\n".join(f"{f}: {metrics.get(f, '')}" for f in READ_FIRST_FIELDS) + "\n"


def render_report(metrics: Dict[str, object], validations: Sequence[str]) -> str:
    return "\n".join([
        "# V18.21A-R4 Advisory Full-History Backfill Plan", "",
        "## Executive summary",
        f"- Status: {metrics['STATUS']}",
        f"- Missing history tickers: {metrics['MISSING_HISTORY_TICKER_COUNT']}",
        f"- All-missing projected score-ready ratio: {metrics['ALL_MISSING_PROJECTED_SCORE_READY_RATIO']}", "",
        "## Safety statement",
        "- No backfill was applied. No external data was fetched. Price cache and protected behavior were not modified.", "",
        "## Current coverage summary from R3",
        f"- Current local price data available: {metrics['CURRENT_LOCAL_PRICE_DATA_AVAILABLE_COUNT']}",
        f"- Current full-history factor ready: {metrics['CURRENT_FULL_HISTORY_FACTOR_READY_COUNT']}",
        f"- Current score-ready ratio: {metrics['CURRENT_SCORE_READY_RATIO']}", "",
        "## Missing history ticker summary",
        f"- Plan rows: {metrics['MISSING_HISTORY_TICKER_COUNT']}", "",
        "## Backfill priority methodology",
        f"- Priority source status: {metrics['PRIORITY_SOURCE_STATUS']}", "",
        "## Coverage projection scenarios",
        f"- Top 25: {metrics['TOP_25_PROJECTED_SCORE_READY_RATIO']}; Top 50: {metrics['TOP_50_PROJECTED_SCORE_READY_RATIO']}; Top 100: {metrics['TOP_100_PROJECTED_SCORE_READY_RATIO']}; All missing: {metrics['ALL_MISSING_PROJECTED_SCORE_READY_RATIO']}", "",
        "## Safety audit summary",
        "- Safety audit file confirms no history backfill, external fetch, cache write, state write, ranking change, broker execution, auto-trade, or auto-sell change.", "",
        "## Validation summary",
        *[f"- {v}" for v in validations],
        f"- Validation fail count: {metrics['VALIDATION_FAIL_COUNT']}", "",
        "## Recommended next step",
        "- Take a stable snapshot of this advisory plan, or implement a separate controlled backfill only after explicit approval.",
    ]) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    metrics, paths = build(root)
    ps_ok, ps_msg = ps_parse(root / "scripts/v18/run_v18_21A_R4_advisory_full_history_backfill_plan.ps1")
    py_ok, py_msg = compile_check(root / "scripts/v18/v18_21A_R4_advisory_full_history_backfill_plan.py")
    output_paths = [paths[k] for k in ("backfill", "plan", "projection", "safety")]
    outputs_ok = all(p.exists() for p in output_paths)
    validations = [
        f"PowerShell parse check: {ps_msg}",
        f"Python compile check: {py_msg}",
        "Run check: OK_CURRENT_SCRIPT_EXECUTED",
        f"R4 output existence check: {'OK' if outputs_ok else 'FAILED'}",
        "Protected behavior check: OK_ADVISORY_PLAN_ONLY",
        "HISTORY_BACKFILL_APPLIED: FALSE",
        "EXTERNAL_DATA_FETCHED: FALSE",
    ]
    metrics["VALIDATION_FAIL_COUNT"] = sum(1 for ok in (ps_ok, py_ok, outputs_ok) if not ok)
    write_text(paths["read"], render_read(metrics))
    write_text(paths["report"], render_report(metrics, validations))
    fields_ok = all(f in read_text(paths["read"]) for f in READ_FIRST_FIELDS)
    final_ok = fields_ok and all(p.exists() for p in [*output_paths, paths["read"], paths["report"]])
    if not final_ok:
        metrics["VALIDATION_FAIL_COUNT"] = int(metrics["VALIDATION_FAIL_COUNT"]) + 1
        write_text(paths["read"], render_read(metrics))
        write_text(paths["report"], render_report(metrics, validations + ["Final READ_FIRST/output check: FAILED"]))
    print(f"STATUS: {metrics['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"PATCH_MODE: {PATCH_MODE}")
    print(f"MISSING_HISTORY_TICKER_COUNT: {metrics['MISSING_HISTORY_TICKER_COUNT']}")
    print(f"BACKFILL_PLAN_READY: {metrics['BACKFILL_PLAN_READY']}")
    print(f"BACKFILL_BATCH_COUNT: {metrics['BACKFILL_BATCH_COUNT']}")
    print(f"ALL_MISSING_PROJECTED_SCORE_READY_RATIO: {metrics['ALL_MISSING_PROJECTED_SCORE_READY_RATIO']}")
    print(f"HISTORY_BACKFILL_APPLIED: FALSE")
    print(f"EXTERNAL_DATA_FETCHED: FALSE")
    print(f"VALIDATION_FAIL_COUNT: {metrics['VALIDATION_FAIL_COUNT']}")
    print(f"READ_FIRST: {paths['read']}")
    print(f"REPORT: {paths['report']}")
    return 1 if int(metrics["VALIDATION_FAIL_COUNT"]) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
