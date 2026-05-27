from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R25F_SAFE_DOWNSTREAM_REFRESH_READY"
STATUS_PREVIEW_OK = "OK_V18_25A_R25F_PREVIEW_RANKED_CANDIDATES_READY"
STATUS_BLOCKED = "WARN_V18_25A_R25F_TARGETS_STILL_DOWNSTREAM_BLOCKED"
STATUS_WRAPPER_SKIPPED = "WARN_V18_25A_R25F_SAFE_WRAPPER_RERUN_SKIPPED"
STATUS_APPROX = "WARN_V18_25A_R25F_CLASSIFICATION_APPROXIMATION_USED"
STATUS_UPDATE_REFUSED = "WARN_V18_25A_R25F_RANKED_CANDIDATE_UPDATE_REFUSED"
STATUS_INPUTS_MISSING = "WARN_V18_25A_R25F_INPUTS_MISSING"

MODE = "SAFE_DOWNSTREAM_REFRESH_NO_FETCH"
EXPECTED_TARGET_COUNT = 93

R25E_TARGETS = "outputs/v18/post_merge_validation/V18_25A_R25E_CURRENT_TARGETS.csv"
R25E_PRESENCE = "outputs/v18/post_merge_validation/V18_25A_R25E_CURRENT_FACTOR_TECHNICAL_PRESENCE_AUDIT.csv"
FACTOR_CURRENT = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_CURRENT = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
PRICE_CACHE = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"

OUT_TARGETS = "outputs/v18/post_merge_validation/V18_25A_R25F_CURRENT_DOWNSTREAM_REFRESH_TARGETS.csv"
OUT_RANK_AUDIT = "outputs/v18/post_merge_validation/V18_25A_R25F_CURRENT_REGENERATED_RANKING_AUDIT.csv"
OUT_TRUST = "outputs/v18/post_merge_validation/V18_25A_R25F_CURRENT_TRUST_CLASSIFICATION_AFTER_REFRESH.csv"
OUT_IMPACT = "outputs/v18/post_merge_validation/V18_25A_R25F_CURRENT_RANKED_CANDIDATE_TARGET_IMPACT.csv"
OUT_BLOCKERS = "outputs/v18/post_merge_validation/V18_25A_R25F_CURRENT_REMAINING_DOWNSTREAM_BLOCKERS.csv"
OUT_PREVIEW = "outputs/v18/candidates/V18_25A_R25F_CURRENT_RANKED_CANDIDATES_PREVIEW.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R25F_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R25F_CURRENT_SAFE_DOWNSTREAM_REFRESH_REPORT.md"

CANDIDATE_FIELDS = [
    "rank", "ticker", "composite_candidate_score", "ranking_source_policy", "primary_score_source_files",
    "audit_only_source_files", "score_source_status", "score_source_files", "score_source_columns",
    "latest_price_date", "latest_close", "technical_status", "event_risk_status", "overheat_status",
    "pullback_status", "execution_status", "final_action", "reason",
]
TARGET_FIELDS = [
    "priority_rank", "ticker", "target_in_factor_pack", "target_in_technical_timing", "price_cache_present",
    "price_cache_readable", "rolling_ledger_present", "ready_for_downstream_refresh", "reason",
]
RANK_AUDIT_FIELDS = [
    "ticker", "factor_score", "technical_timing_score", "factor_rank", "technical_status",
    "overheat_penalty", "volatility_penalty", "composite_candidate_score", "rank_preview_eligible",
    "ranking_logic", "reason",
]
TRUST_FIELDS = [
    "ticker", "trust_level_after_refresh", "classification_logic", "official_rank_allowed_after_refresh",
    "factor_present", "technical_present", "price_cache_readable", "rolling_ledger_present",
    "composite_candidate_score", "remaining_blocker_reason",
]
IMPACT_FIELDS = [
    "ticker", "target_in_factor_pack", "target_in_technical_timing", "target_in_regenerated_rank_preview",
    "regenerated_rank", "factor_score", "technical_timing_score", "composite_candidate_score",
    "trust_level_after_refresh", "official_rank_allowed_after_refresh", "remaining_blocker_reason",
]
BLOCKER_FIELDS = ["ticker", "blocker_type", "reason", "next_action"]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "RUN_ID", "MAX_TICKERS", "TARGET_TICKER_COUNT", "FACTOR_TARGET_PRESENT_COUNT",
    "TECHNICAL_TARGET_PRESENT_COUNT", "PRICE_CACHE_PRESENT_COUNT", "ROLLING_LEDGER_PRESENT_COUNT",
    "REGENERATED_RANK_PREVIEW_ROW_COUNT", "RANKED_CANDIDATE_TARGET_PRESENT_COUNT_AFTER_REFRESH",
    "HIGH_TRUST_COUNT_AFTER_REFRESH", "MEDIUM_COUNT_AFTER_REFRESH", "LOW_COUNT_AFTER_REFRESH",
    "DATA_NOT_READY_COUNT_AFTER_REFRESH", "WATCH_ONLY_COUNT_AFTER_REFRESH",
    "OFFICIAL_RANK_ALLOWED_COUNT_AFTER_REFRESH", "TARGETS_STILL_DOWNSTREAM_BLOCKED_COUNT",
    "MISSING_FACTOR_BLOCKER_COUNT_AFTER_REFRESH", "MISSING_TECHNICAL_BLOCKER_COUNT_AFTER_REFRESH",
    "MISSING_PRICE_BLOCKER_COUNT_AFTER_REFRESH", "MISSING_LEDGER_BLOCKER_COUNT_AFTER_REFRESH",
    "OTHER_BLOCKER_COUNT_AFTER_REFRESH", "EXISTING_SAFE_WRAPPERS_RAN", "EXISTING_SAFE_WRAPPER_STATUS",
    "CURRENT_RANKED_CANDIDATES_UPDATED", "PREVIEW_RANKED_CANDIDATES_PATH", "TRUST_CLASSIFICATION_AUDIT_PATH",
    "RANKED_CANDIDATE_TARGET_IMPACT_PATH", "REMAINING_DOWNSTREAM_BLOCKERS_PATH", "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE", "AUTO_SELL", "EXTERNAL_FETCH_EXECUTED", "BACKTEST_EXECUTED", "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED", "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "TIER_FILES_MODIFIED",
    "OFFICIAL_DECISION_MODIFIED", "VALIDATION_FAIL_COUNT", "FORBIDDEN_MODIFIED", "NEXT_RECOMMENDED_STEP",
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
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def to_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip().replace(",", "")
        return float(text) if text else None
    except Exception:
        return None


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(p.relative_to(root)): file_sig(p) for p in root.rglob("*") if p.is_file()}


def by_ticker(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {norm_ticker(row.get("ticker")): row for row in rows if norm_ticker(row.get("ticker"))}


def score_col(fields: Sequence[str], candidates: Sequence[str]) -> str:
    lower = {field.lower(): field for field in fields}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return ""


def price_cache_readable(path: Path) -> bool:
    rows, fields = read_csv(path)
    return bool(rows) and {"date", "close"}.issubset({field.lower() for field in fields})


def composite_score(factor_score: float, technical_score: float, overheat: Optional[float], volatility: Optional[float]) -> float:
    score = factor_score * 0.40 + technical_score * 0.30
    if overheat is not None:
        score -= abs(overheat)
    if volatility is not None:
        score -= abs(volatility)
    return round(score, 6)


def final_action(technical_status: str, overheat_status: str, pullback_status: str) -> str:
    status_text = " ".join([technical_status, overheat_status, pullback_status]).upper()
    if any(token in status_text for token in ("AVOID", "RISK", "EXIT", "OVERHEAT", "NO_TRADE")):
        return "NO_TRADE_REVIEW_ONLY"
    if any(token in status_text for token in ("PULLBACK", "LOWER", "WATCH")):
        return "WAIT_PULLBACK_REVIEW_ONLY"
    return "REVIEW_ONLY"


def classify_target(
    factor_present: bool,
    technical_present: bool,
    price_ok: bool,
    ledger_present: bool,
    composite: Optional[float],
    in_preview: bool,
) -> Tuple[str, bool, str]:
    blockers: List[str] = []
    if not factor_present:
        blockers.append("BLOCKED_MISSING_FACTOR_SCORE")
    if not technical_present:
        blockers.append("BLOCKED_MISSING_TECHNICAL_TIMING")
    if not price_ok:
        blockers.append("BLOCKED_MISSING_PRICE_CACHE")
    if not ledger_present:
        blockers.append("BLOCKED_NOT_IN_ROLLING_LEDGER")
    if composite is None or not in_preview:
        blockers.append("BLOCKED_NOT_IN_REGENERATED_RANK_PREVIEW")
    if blockers:
        if not factor_present or not technical_present or not price_ok or not ledger_present:
            return "DATA_NOT_READY", False, "|".join(blockers)
        return "WATCH_ONLY", False, "|".join(blockers)
    if composite >= 50:
        return "HIGH_TRUST", True, ""
    if composite >= 30:
        return "MEDIUM", True, ""
    return "LOW", True, "LOW_COMPOSITE_SCORE_REVIEW_ONLY"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--max-tickers", type=int, default=93)
    parser.add_argument("--run-existing-safe-wrappers", action="store_true")
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--update-current-candidates", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R25F_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    before = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": file_sig(root / FACTOR_CURRENT),
        "technical": file_sig(root / TECH_CURRENT),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
    }

    required = [R25E_TARGETS, R25E_PRESENCE, FACTOR_CURRENT, TECH_CURRENT, LEDGER]
    missing_inputs = [path for path in required if not (root / path).exists()]
    targets_in, _ = read_csv(root / R25E_TARGETS)
    factor_rows, factor_fields = read_csv(root / FACTOR_CURRENT)
    tech_rows, tech_fields = read_csv(root / TECH_CURRENT)
    ledger_rows, _ = read_csv(root / LEDGER)

    target_tickers = [norm_ticker(row.get("ticker")) for row in targets_in if norm_ticker(row.get("ticker"))][: max(args.max_tickers, 0)]
    target_set = set(target_tickers)
    factor_by = by_ticker(factor_rows)
    tech_by = by_ticker(tech_rows)
    ledger_set = set(by_ticker(ledger_rows))
    factor_score_col = score_col(factor_fields, ["factor_score", "factor_pack_score", "F010_XSEC_COMPOSITE_RANK"])
    factor_rank_col = score_col(factor_fields, ["factor_pack_rank", "rank"])
    tech_score_col = score_col(tech_fields, ["technical_timing_score", "technical_score"])

    common_tickers = sorted(set(factor_by) & set(tech_by))
    preview_raw: List[Tuple[str, float, float, Dict[str, object]]] = []
    rank_audit_rows: List[Dict[str, object]] = []
    for ticker in common_tickers:
        frow = factor_by[ticker]
        trow = tech_by[ticker]
        fscore = to_float(frow.get(factor_score_col))
        tscore = to_float(trow.get(tech_score_col))
        if fscore is None or tscore is None:
            continue
        overheat = to_float(frow.get("overheat_penalty"))
        volatility = to_float(frow.get("volatility_penalty"))
        comp = composite_score(fscore, tscore, overheat, volatility)
        frank = to_float(frow.get(factor_rank_col)) or 999999.0
        technical_status = str(trow.get("technical_signal") or trow.get("technical_status") or trow.get("technical_warning_label") or "")
        overheat_status = str(trow.get("gamma_squeeze_risk_label") or frow.get("overheat_penalty") or "")
        pullback_status = str(trow.get("bb_status") or "")
        latest_date = str(frow.get("latest_price_date") or trow.get("price_date") or "")
        latest_close = str(frow.get("latest_close") or trow.get("close") or "")
        row = {
            "ticker": ticker,
            "composite_candidate_score": f"{comp:.6f}",
            "ranking_source_policy": "PRIMARY_CURRENT_ONLY_R25F_PREVIEW",
            "primary_score_source_files": f"{FACTOR_CURRENT};{TECH_CURRENT}",
            "audit_only_source_files": "",
            "score_source_status": "OK_SCORE_SOURCE_FOUND",
            "score_source_files": f"{FACTOR_CURRENT};{TECH_CURRENT}",
            "score_source_columns": f"{factor_score_col};{tech_score_col};factor_pack_rank;overheat_penalty;volatility_penalty",
            "latest_price_date": latest_date,
            "latest_close": latest_close,
            "technical_status": technical_status,
            "event_risk_status": "",
            "overheat_status": overheat_status,
            "pullback_status": pullback_status,
            "execution_status": "",
            "final_action": final_action(technical_status, overheat_status, pullback_status),
            "reason": "R25F preview regenerated from current official factor pack and technical timing only; no external fetch.",
        }
        preview_raw.append((ticker, comp, frank, row))
        rank_audit_rows.append({
            "ticker": ticker,
            "factor_score": fscore,
            "technical_timing_score": tscore,
            "factor_rank": frow.get(factor_rank_col, ""),
            "technical_status": technical_status,
            "overheat_penalty": "" if overheat is None else overheat,
            "volatility_penalty": "" if volatility is None else volatility,
            "composite_candidate_score": f"{comp:.6f}",
            "rank_preview_eligible": "TRUE",
            "ranking_logic": "factor_score*0.40 + technical_timing_score*0.30 - abs(overheat_penalty) - abs(volatility_penalty)",
            "reason": "",
        })

    preview_rows: List[Dict[str, object]] = []
    preview_by_ticker: Dict[str, Dict[str, object]] = {}
    for idx, (_, _, _, row) in enumerate(sorted(preview_raw, key=lambda item: (-item[1], item[2], item[0])), 1):
        out = dict(row)
        out["rank"] = idx
        preview_rows.append(out)
        preview_by_ticker[str(out["ticker"])] = out

    target_rows: List[Dict[str, object]] = []
    trust_rows: List[Dict[str, object]] = []
    impact_rows: List[Dict[str, object]] = []
    blockers: List[Dict[str, object]] = []
    for idx, ticker in enumerate(target_tickers, 1):
        factor_present = ticker in factor_by and to_float(factor_by[ticker].get(factor_score_col)) is not None
        technical_present = ticker in tech_by and to_float(tech_by[ticker].get(tech_score_col)) is not None
        price_path = root / PRICE_CACHE / f"{ticker}.csv"
        price_present = price_path.exists()
        price_ok = price_cache_readable(price_path)
        ledger_present = ticker in ledger_set
        preview = preview_by_ticker.get(ticker)
        comp = to_float(preview.get("composite_candidate_score")) if preview else None
        trust, official_allowed, reason = classify_target(factor_present, technical_present, price_ok, ledger_present, comp, bool(preview))
        target_rows.append({
            "priority_rank": idx,
            "ticker": ticker,
            "target_in_factor_pack": str(factor_present).upper(),
            "target_in_technical_timing": str(technical_present).upper(),
            "price_cache_present": str(price_present).upper(),
            "price_cache_readable": str(price_ok).upper(),
            "rolling_ledger_present": str(ledger_present).upper(),
            "ready_for_downstream_refresh": str(not reason or reason == "LOW_COMPOSITE_SCORE_REVIEW_ONLY").upper(),
            "reason": reason,
        })
        trust_rows.append({
            "ticker": ticker,
            "trust_level_after_refresh": trust,
            "classification_logic": "SIMPLIFIED_R25F_AUDIT_CLASSIFICATION",
            "official_rank_allowed_after_refresh": str(official_allowed).upper(),
            "factor_present": str(factor_present).upper(),
            "technical_present": str(technical_present).upper(),
            "price_cache_readable": str(price_ok).upper(),
            "rolling_ledger_present": str(ledger_present).upper(),
            "composite_candidate_score": "" if comp is None else f"{comp:.6f}",
            "remaining_blocker_reason": reason,
        })
        impact_rows.append({
            "ticker": ticker,
            "target_in_factor_pack": str(factor_present).upper(),
            "target_in_technical_timing": str(technical_present).upper(),
            "target_in_regenerated_rank_preview": str(bool(preview)).upper(),
            "regenerated_rank": preview.get("rank", "") if preview else "",
            "factor_score": factor_by.get(ticker, {}).get(factor_score_col, ""),
            "technical_timing_score": tech_by.get(ticker, {}).get(tech_score_col, ""),
            "composite_candidate_score": "" if comp is None else f"{comp:.6f}",
            "trust_level_after_refresh": trust,
            "official_rank_allowed_after_refresh": str(official_allowed).upper(),
            "remaining_blocker_reason": reason,
        })
        for token in [part for part in reason.split("|") if part.startswith("BLOCKED_")]:
            blockers.append({"ticker": ticker, "blocker_type": token, "reason": reason, "next_action": "Resolve downstream blocker logic before R26."})

    write_csv(root / OUT_TARGETS, target_rows, TARGET_FIELDS)
    write_csv(root / OUT_RANK_AUDIT, rank_audit_rows, RANK_AUDIT_FIELDS)
    write_csv(root / OUT_TRUST, trust_rows, TRUST_FIELDS)
    write_csv(root / OUT_IMPACT, impact_rows, IMPACT_FIELDS)
    write_csv(root / OUT_BLOCKERS, blockers, BLOCKER_FIELDS)
    write_csv(root / OUT_PREVIEW, preview_rows, CANDIDATE_FIELDS)

    current_updated = False
    update_refused = False
    if args.update_current_candidates and not args.preview_only:
        shutil.copy2(root / OUT_PREVIEW, root / CURRENT_CANDIDATES)
        current_updated = True
    elif args.update_current_candidates and args.preview_only:
        update_refused = True

    wrappers_ran = False
    wrapper_status = "SKIPPED_NO_RERUN_REQUESTED"
    if args.run_existing_safe_wrappers:
        wrapper_status = "SKIPPED_NO_SAFE_READ_ONLY_WRAPPER_PROVEN"

    factor_present_count = sum(1 for row in target_rows if row["target_in_factor_pack"] == "TRUE")
    tech_present_count = sum(1 for row in target_rows if row["target_in_technical_timing"] == "TRUE")
    price_present_count = sum(1 for row in target_rows if row["price_cache_readable"] == "TRUE")
    ledger_present_count = sum(1 for row in target_rows if row["rolling_ledger_present"] == "TRUE")
    preview_target_present = sum(1 for row in impact_rows if row["target_in_regenerated_rank_preview"] == "TRUE")
    high_count = sum(1 for row in trust_rows if row["trust_level_after_refresh"] == "HIGH_TRUST")
    medium_count = sum(1 for row in trust_rows if row["trust_level_after_refresh"] == "MEDIUM")
    low_count = sum(1 for row in trust_rows if row["trust_level_after_refresh"] == "LOW")
    data_not_ready_count = sum(1 for row in trust_rows if row["trust_level_after_refresh"] == "DATA_NOT_READY")
    watch_count = sum(1 for row in trust_rows if row["trust_level_after_refresh"] == "WATCH_ONLY")
    official_allowed_count = sum(1 for row in trust_rows if row["official_rank_allowed_after_refresh"] == "TRUE")
    missing_factor = len(target_rows) - factor_present_count
    missing_tech = len(target_rows) - tech_present_count
    missing_price = len(target_rows) - price_present_count
    missing_ledger = len(target_rows) - ledger_present_count
    other_blockers = sum(1 for row in trust_rows if "BLOCKED_NOT_IN_REGENERATED_RANK_PREVIEW" in str(row["remaining_blocker_reason"]))
    still_blocked = sum(1 for row in trust_rows if str(row["remaining_blocker_reason"]).startswith("BLOCKED_"))

    after = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": file_sig(root / FACTOR_CURRENT),
        "technical": file_sig(root / TECH_CURRENT),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
    }
    mods = {key: before[key] != after[key] for key in before}
    forbidden = any(mods.values())

    status = STATUS_PREVIEW_OK if not current_updated else STATUS_OK
    if missing_inputs:
        status = STATUS_INPUTS_MISSING
    elif update_refused:
        status = STATUS_UPDATE_REFUSED
    elif still_blocked:
        status = STATUS_BLOCKED
    elif args.run_existing_safe_wrappers and not wrappers_ran:
        status = STATUS_WRAPPER_SKIPPED
    elif any(row["classification_logic"] == "SIMPLIFIED_R25F_AUDIT_CLASSIFICATION" for row in trust_rows):
        status = STATUS_APPROX

    validation_fail_count = int(status in {STATUS_INPUTS_MISSING, STATUS_BLOCKED, STATUS_UPDATE_REFUSED} or forbidden)
    next_step = (
        "R26: Factor effectiveness validation / forward-test integration readiness."
        if preview_target_present == len(target_rows) and still_blocked == 0
        else "Resolve downstream blocker logic before factor effectiveness validation."
    )
    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "MAX_TICKERS": args.max_tickers,
        "TARGET_TICKER_COUNT": len(target_rows),
        "FACTOR_TARGET_PRESENT_COUNT": factor_present_count,
        "TECHNICAL_TARGET_PRESENT_COUNT": tech_present_count,
        "PRICE_CACHE_PRESENT_COUNT": price_present_count,
        "ROLLING_LEDGER_PRESENT_COUNT": ledger_present_count,
        "REGENERATED_RANK_PREVIEW_ROW_COUNT": len(preview_rows),
        "RANKED_CANDIDATE_TARGET_PRESENT_COUNT_AFTER_REFRESH": preview_target_present,
        "HIGH_TRUST_COUNT_AFTER_REFRESH": high_count,
        "MEDIUM_COUNT_AFTER_REFRESH": medium_count,
        "LOW_COUNT_AFTER_REFRESH": low_count,
        "DATA_NOT_READY_COUNT_AFTER_REFRESH": data_not_ready_count,
        "WATCH_ONLY_COUNT_AFTER_REFRESH": watch_count,
        "OFFICIAL_RANK_ALLOWED_COUNT_AFTER_REFRESH": official_allowed_count,
        "TARGETS_STILL_DOWNSTREAM_BLOCKED_COUNT": still_blocked,
        "MISSING_FACTOR_BLOCKER_COUNT_AFTER_REFRESH": missing_factor,
        "MISSING_TECHNICAL_BLOCKER_COUNT_AFTER_REFRESH": missing_tech,
        "MISSING_PRICE_BLOCKER_COUNT_AFTER_REFRESH": missing_price,
        "MISSING_LEDGER_BLOCKER_COUNT_AFTER_REFRESH": missing_ledger,
        "OTHER_BLOCKER_COUNT_AFTER_REFRESH": other_blockers,
        "EXISTING_SAFE_WRAPPERS_RAN": str(wrappers_ran).upper(),
        "EXISTING_SAFE_WRAPPER_STATUS": wrapper_status,
        "CURRENT_RANKED_CANDIDATES_UPDATED": str(current_updated).upper(),
        "PREVIEW_RANKED_CANDIDATES_PATH": OUT_PREVIEW,
        "TRUST_CLASSIFICATION_AUDIT_PATH": OUT_TRUST,
        "RANKED_CANDIDATE_TARGET_IMPACT_PATH": OUT_IMPACT,
        "REMAINING_DOWNSTREAM_BLOCKERS_PATH": OUT_BLOCKERS,
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
        "NEXT_RECOMMENDED_STEP": next_step,
    }
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    report = "\n".join([
        "# V18.25A R25F Safe Downstream Refresh Report",
        "",
        f"STATUS: {status}",
        f"MODE: {MODE}",
        f"RUN_ID: {run_id}",
        "",
        f"- target_ticker_count: {len(target_rows)}",
        f"- regenerated_rank_preview_row_count: {len(preview_rows)}",
        f"- ranked_candidate_target_present_after_refresh: {preview_target_present}",
        f"- high/medium/low/data_not_ready/watch_only: {high_count}/{medium_count}/{low_count}/{data_not_ready_count}/{watch_count}",
        f"- targets_still_downstream_blocked: {still_blocked}",
        f"- current_ranked_candidates_updated: {str(current_updated).upper()}",
        "",
        "R25F used current official factor and technical timing files only. No external fetch, broker access, backtest, or official decision update was executed.",
        "",
    ])
    write_text(root / OUT_REPORT, report)
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
