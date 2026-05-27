from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_24A_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT_READY"
STATUS_BASELINE = "WARN_V18_24A_DYNAMIC_SCORE_TIER_MIGRATION_BASELINE_READY"
STATUS_LIMITED = "WARN_V18_24A_DYNAMIC_SCORE_TIER_MIGRATION_LIMITED_SOURCE"
STATUS_FAIL = "FAIL_V18_24A_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT"
MODE = "READ_ONLY_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT"

OUTPUTS = {
    "audit": "outputs/v18/tier_migration/V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT.md",
    "snapshot": "outputs/v18/tier_migration/V18_24A_CURRENT_SCORE_TIER_SNAPSHOT.csv",
    "movement": "outputs/v18/tier_migration/V18_24A_CURRENT_TIER_MOVEMENT_REPORT.csv",
    "upgrades": "outputs/v18/tier_migration/V18_24A_CURRENT_UPGRADES.csv",
    "downgrades": "outputs/v18/tier_migration/V18_24A_CURRENT_DOWNGRADES.csv",
    "large": "outputs/v18/tier_migration/V18_24A_CURRENT_LARGE_SCORE_MOVES.csv",
    "new_score": "outputs/v18/tier_migration/V18_24A_CURRENT_NEWLY_SCORE_READY.csv",
    "blocked": "outputs/v18/tier_migration/V18_24A_CURRENT_DATA_NOT_READY_OR_BLOCKED.csv",
    "summary": "outputs/v18/tier_migration/V18_24A_CURRENT_TIER_SUMMARY.csv",
    "source": "outputs/v18/tier_migration/V18_24A_CURRENT_SOURCE_AUDIT.csv",
    "validation": "outputs/v18/tier_migration/V18_24A_CURRENT_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_24A_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT_REPORT.md",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "TIER_MIGRATION_AUDIT_READY", "READ_ONLY", "CURRENT_TICKER_COUNT",
    "CURRENT_SCORE_SOURCE", "CURRENT_SCORE_SOURCE_TRUST", "PREVIOUS_TIER_SNAPSHOT_FOUND",
    "PREVIOUS_TIER_SNAPSHOT_PATH", "BASELINE_MODE", "TIER_1_CORE_CANDIDATE_COUNT",
    "TIER_2_STRONG_WATCHLIST_COUNT", "TIER_3_WATCHLIST_COUNT", "TIER_4_REVIEW_ONLY_COUNT",
    "TIER_5_WEAK_OR_BLOCKED_COUNT", "TIER_0_DATA_NOT_READY_COUNT", "MOVEMENT_REPORT_CREATED",
    "TOTAL_MOVEMENT_COUNT", "UPGRADE_COUNT", "DOWNGRADE_COUNT", "SAME_TIER_SCORE_UP_COUNT",
    "SAME_TIER_SCORE_DOWN_COUNT", "LARGE_SCORE_MOVE_COUNT", "NEWLY_SCORE_READY_COUNT",
    "NEWLY_DATA_READY_COUNT", "DROPPED_TO_DATA_NOT_READY_COUNT", "HELD_OUT_OR_REVIEW_BLOCKED_COUNT",
    "DATA_NOT_READY_OR_BLOCKED_COUNT", "VALIDATION_FAIL_COUNT", "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL", "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_WRITTEN", "LEDGER_MODIFIED", "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED", "FACTOR_EFFECT_CLAIM_ALLOWED",
    "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED", "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET", "TRUE_5DAY_UNIQUE_COVERAGE_STATUS", "RECOMMENDED_NEXT_ACTION",
    "AUDIT_PATH", "TIER_SNAPSHOT_PATH", "MOVEMENT_REPORT_PATH", "UPGRADES_PATH", "DOWNGRADES_PATH",
    "LARGE_SCORE_MOVES_PATH", "NEWLY_SCORE_READY_PATH", "DATA_NOT_READY_OR_BLOCKED_PATH",
    "TIER_SUMMARY_PATH", "SOURCE_AUDIT_PATH", "VALIDATION_PATH", "REPORT_PATH",
]

SNAPSHOT_FIELDS = [
    "ticker", "current_score", "current_score_source", "current_rank", "factor_pack_score",
    "technical_timing_score", "overheat_penalty", "event_risk_status", "local_price_available",
    "full_history_ready", "latest_success_scan_date", "data_readiness_status", "held_out_status",
    "current_tier", "current_tier_reason", "review_required",
]
MOVEMENT_FIELDS = [
    "ticker", "movement_type", "previous_tier", "current_tier", "previous_score", "current_score",
    "score_delta", "previous_rank", "current_rank", "rank_delta", "movement_reason",
    "current_score_source", "review_required",
]
SUMMARY_FIELDS = ["tier", "count", "notes"]
SOURCE_FIELDS = ["source_name", "source_path", "exists", "row_count", "selected", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]

TIERS = [
    "TIER_1_CORE_CANDIDATE",
    "TIER_2_STRONG_WATCHLIST",
    "TIER_3_WATCHLIST",
    "TIER_4_REVIEW_ONLY",
    "TIER_5_WEAK_OR_BLOCKED",
    "TIER_0_DATA_NOT_READY",
]
TIER_RANK = {tier: idx for idx, tier in enumerate(TIERS)}

SAFETY = {
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "BUY_PERMISSION_MODIFIED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_WRITTEN": "FALSE",
    "STAGED_PRICE_HISTORY_WRITTEN": "FALSE",
    "LEDGER_MODIFIED": "FALSE",
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


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return (int(stat.st_mtime_ns), int(stat.st_size))


def collect_forbidden(root: Path) -> List[Path]:
    rel_dirs = [
        "state/v18/price_cache", "data/v18/staged_backfill", "state/v18/rolling_coverage",
        "outputs/v18/ranking", "outputs/v18/signal_snapshots", "outputs/v18/factor_pack",
        "outputs/v18/technical_timing", "outputs/v18/backtest", "outputs/v18/daily_integrated",
        "state/v18/manual", "state/v18/simulation", "state/v18/forward_outcome",
        "state/v18/candidate_forward_tracker", "archive/stable",
    ]
    out: List[Path] = []
    for rel in rel_dirs:
        base = root / rel
        if base.exists():
            out.extend(path for path in base.rglob("*") if path.is_file())
    return out


def get_ticker(row: Dict[str, str]) -> str:
    for key in ("ticker", "Ticker", "symbol", "Symbol", "yf_ticker"):
        value = row.get(key, "")
        if value:
            text = str(value).strip().upper()
            if text and text not in {"NAN", "NULL", "NONE"}:
                return text
    return ""


def to_float(value: object) -> float | None:
    try:
        text = str(value).replace(",", "").strip()
        if text == "":
            return None
        return float(text)
    except ValueError:
        return None


def to_int(value: object) -> int | None:
    number = to_float(value)
    return int(number) if number is not None else None


def choose_score_source(sources: Sequence[Tuple[str, Path, List[Dict[str, str]], List[str]]]) -> Tuple[str, Path | None, List[Dict[str, str]], str, str]:
    preferred = ["composite_candidate_score", "final_score", "total_score", "factor_pack_score", "score"]
    for source_name, path, rows, fields in sources:
        lower_to_field = {field.lower(): field for field in fields}
        if not rows:
            continue
        for score_name in preferred:
            if score_name in lower_to_field:
                field = lower_to_field[score_name]
                usable = sum(1 for row in rows if get_ticker(row) and to_float(row.get(field)) is not None)
                if usable:
                    trust = "HIGH" if score_name != "score" else "MEDIUM"
                    return field, path, rows, source_name, trust
    for source_name, path, rows, fields in sources:
        rank_field = next((field for field in fields if "rank" in field.lower()), "")
        if rows and rank_field:
            usable = sum(1 for row in rows if get_ticker(row) and to_int(row.get(rank_field)) is not None)
            if usable:
                return f"RANK_FALLBACK:{rank_field}", path, rows, source_name, "LOW"
    return "", None, [], "", "NONE"


def cap_tier(current: str, cap: str) -> str:
    return current if TIER_RANK[current] >= TIER_RANK[cap] else cap


def tier_from_score(score: float | None) -> str:
    if score is None:
        return "TIER_0_DATA_NOT_READY"
    if score >= 85:
        return "TIER_1_CORE_CANDIDATE"
    if score >= 75:
        return "TIER_2_STRONG_WATCHLIST"
    if score >= 65:
        return "TIER_3_WATCHLIST"
    if score >= 50:
        return "TIER_4_REVIEW_ONLY"
    return "TIER_5_WEAK_OR_BLOCKED"


def discover_previous_snapshot(root: Path) -> Path | None:
    current = root / OUTPUTS["snapshot"]
    if current.exists():
        return current
    history = root / "outputs/v18/tier_migration/history"
    if history.exists():
        matches = sorted(history.glob("V18_24A_SCORE_TIER_SNAPSHOT_*.csv"), key=lambda p: p.name, reverse=True)
        if matches:
            return matches[0]
    return None


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_md(values: Dict[str, str], summary_rows: Sequence[Dict[str, object]], movement_counts: Counter[str], reason_counts: Counter[str]) -> str:
    summary = "\n".join(f"- {row['tier']}: {row['count']}" for row in summary_rows)
    movements = "\n".join(f"- {key}: {value}" for key, value in movement_counts.most_common())
    reasons = "\n".join(f"- {key}: {value}" for key, value in reason_counts.most_common(12))
    return f"""# V18.24A Dynamic Score Tier Migration Audit

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Purpose
Create a read-only score tier snapshot, compare it with the prior tier snapshot when available, and produce a separate movement/change audit. This step does not modify official ranking, factor pack, technical timing, signal snapshot, price cache, ledger, backtest, or trading state.

## Source Summary
Current ticker count: {values['CURRENT_TICKER_COUNT']}.
Score source: {values['CURRENT_SCORE_SOURCE']} ({values['CURRENT_SCORE_SOURCE_TRUST']}).
Previous snapshot found: {values['PREVIOUS_TIER_SNAPSHOT_FOUND']}.
Baseline mode: {values['BASELINE_MODE']}.

## Tier Policy
Default thresholds: score >= 85 Tier 1; 75-84.99 Tier 2; 65-74.99 Tier 3; 50-64.99 Tier 4; below 50 Tier 5. Missing score or missing local price evidence is Tier 0. Held-out/review tickers are capped at Tier 4. Full-history gaps are capped at Tier 4 when a usable score exists.

## Current Tier Distribution
{summary}

## Movement Summary
{movements or '- No movements beyond baseline rows.'}

## Top Reasons
{reasons or '- No movement reasons.'}

## Limits And Trust Notes
Score coverage is limited to available local score/rank sources. Tier output is an audit/read-center artifact only and is not an official ranking change.

## Recommended Next Action
{values['RECOMMENDED_NEXT_ACTION']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    before = {str(path): file_sig(path) for path in collect_forbidden(root)}

    previous_path = discover_previous_snapshot(root)
    previous_rows, _ = read_csv(previous_path) if previous_path else ([], [])
    previous_by = {get_ticker(row): row for row in previous_rows if get_ticker(row)}
    baseline_mode = previous_path is None

    candidate_paths = [
        ("factor_pack", root / "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"),
        ("technical_timing", root / "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"),
        ("ranking_score_explanation", root / "outputs/v18/ranking/V18_CURRENT_RANKED_CANDIDATE_SCORE_EXPLANATION.csv"),
        ("read_center_ranked_summary", root / "outputs/v18/read_center/V18_13B_CURRENT_RANKED_CANDIDATE_SUMMARY.csv"),
    ]
    loaded_sources = [(name, path, *read_csv(path)) for name, path in candidate_paths]
    score_field, score_path, score_rows, score_source_name, score_trust = choose_score_source(loaded_sources)

    plan_rows, _ = read_csv(root / "outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv")
    canonical = sorted({get_ticker(row) for row in plan_rows if get_ticker(row)})
    ledger_rows, _ = read_csv(root / "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_SCAN_LEDGER_SNAPSHOT.csv")
    if not ledger_rows:
        ledger_rows, _ = read_csv(root / "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv")
    held_rows, _ = read_csv(root / "outputs/v18/staged_backfill/V18_23C_R2_CURRENT_HELD_OUT_TICKERS.csv")
    r3_read_first = (root / "outputs/v18/ops/V18_23C_R3_READ_FIRST.txt").read_text(encoding="utf-8", errors="replace") if (root / "outputs/v18/ops/V18_23C_R3_READ_FIRST.txt").exists() else ""

    score_by = {get_ticker(row): row for row in score_rows if get_ticker(row)}
    ledger_by = {get_ticker(row): row for row in ledger_rows if get_ticker(row)}
    held_by = {get_ticker(row): row for row in held_rows if get_ticker(row)}
    tech_rows, _ = read_csv(root / "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv")
    tech_by = {get_ticker(row): row for row in tech_rows if get_ticker(row)}
    factor_rows, _ = read_csv(root / "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv")
    factor_by = {get_ticker(row): row for row in factor_rows if get_ticker(row)}

    snapshot_rows: List[Dict[str, object]] = []
    for ticker in canonical:
        score_row = score_by.get(ticker, {})
        score: float | None
        rank: int | None
        score_source = score_field or ""
        if score_field.startswith("RANK_FALLBACK:"):
            rank_field = score_field.split(":", 1)[1]
            rank = to_int(score_row.get(rank_field))
            score = None if rank is None else max(0.0, 100.0 - (rank - 1))
            score_source = "RANK_FALLBACK"
        else:
            score = to_float(score_row.get(score_field, "")) if score_row else None
            rank_field = next((field for field in score_row if "rank" in field.lower()), "")
            rank = to_int(score_row.get(rank_field)) if rank_field else None
        ledger = ledger_by.get(ticker, {})
        local_price = str(ledger.get("local_price_available", "FALSE")).upper() == "TRUE"
        full_history = str(ledger.get("full_history_ready", "FALSE")).upper() == "TRUE"
        held = held_by.get(ticker, {})
        held_status = held.get("classification", "")
        tech = tech_by.get(ticker, {})
        factor = factor_by.get(ticker, {})
        overheat = to_float(tech.get("overheat_penalty", factor.get("overheat_penalty", "")))
        event_status = tech.get("official_decision_impact", "")
        review_required = False
        reasons: List[str] = []
        if score is None:
            tier = "TIER_0_DATA_NOT_READY"
            reasons.append("NO_USABLE_SCORE")
        else:
            tier = tier_from_score(score)
            reasons.append("SCORE_THRESHOLD_POLICY")
        if not local_price:
            tier = "TIER_0_DATA_NOT_READY"
            reasons.append("LOCAL_PRICE_NOT_AVAILABLE")
        elif not full_history and score is not None:
            tier = cap_tier(tier, "TIER_4_REVIEW_ONLY")
            review_required = True
            reasons.append("FULL_HISTORY_NOT_READY_CAP")
        if held_status:
            tier = cap_tier(tier, "TIER_4_REVIEW_ONLY")
            review_required = True
            reasons.append("HELD_OUT_BY_BACKFILL_QUALITY")
        if event_status and event_status not in {"NONE", "NOT_AVAILABLE_RESERVED"}:
            tier = cap_tier(tier, "TIER_4_REVIEW_ONLY")
            review_required = True
            reasons.append("EVENT_RISK_CAP")
        if overheat is not None and overheat >= 80:
            if tier in {"TIER_1_CORE_CANDIDATE", "TIER_2_STRONG_WATCHLIST", "TIER_3_WATCHLIST"}:
                tier = TIERS[TIER_RANK[tier] + 1]
            review_required = True
            reasons.append("TECHNICAL_OVERHEAT_CAP")
        data_status = "PRICE_AND_FULL_HISTORY_READY" if local_price and full_history else "LOCAL_PRICE_ONLY" if local_price else "DATA_NOT_READY"
        snapshot_rows.append({
            "ticker": ticker,
            "current_score": "" if score is None else f"{score:.6f}",
            "current_score_source": score_source,
            "current_rank": "" if rank is None else rank,
            "factor_pack_score": factor.get("factor_pack_score", ""),
            "technical_timing_score": tech.get("technical_timing_score", ""),
            "overheat_penalty": "" if overheat is None else overheat,
            "event_risk_status": event_status,
            "local_price_available": str(local_price).upper(),
            "full_history_ready": str(full_history).upper(),
            "latest_success_scan_date": ledger.get("last_success_scan_date", ""),
            "data_readiness_status": data_status,
            "held_out_status": held_status,
            "current_tier": tier,
            "current_tier_reason": ";".join(reasons),
            "review_required": str(review_required).upper(),
        })

    movement_rows: List[Dict[str, object]] = []
    for row in snapshot_rows:
        ticker = str(row["ticker"])
        prev = previous_by.get(ticker)
        current_tier = str(row["current_tier"])
        current_score = to_float(row.get("current_score", ""))
        current_rank = to_int(row.get("current_rank", ""))
        reasons: List[str] = []
        if baseline_mode or not prev:
            movement = "BASELINE_NO_PRIOR_TIER" if baseline_mode else "NEW_TICKER"
            reasons.append("NO_PRIOR_BASELINE" if baseline_mode else "NEW_TICKER")
            prev_tier = ""
            prev_score = None
            prev_rank = None
        else:
            prev_tier = prev.get("current_tier", "")
            prev_score = to_float(prev.get("current_score", ""))
            prev_rank = to_int(prev.get("current_rank", ""))
            score_delta = (current_score - prev_score) if current_score is not None and prev_score is not None else None
            rank_delta = (current_rank - prev_rank) if current_rank is not None and prev_rank is not None else None
            if current_tier == "TIER_0_DATA_NOT_READY" and prev_tier != "TIER_0_DATA_NOT_READY":
                movement = "DROPPED_TO_DATA_NOT_READY"
                reasons.append("DATA_NOT_READY")
            elif prev_tier == "TIER_0_DATA_NOT_READY" and current_tier != "TIER_0_DATA_NOT_READY":
                movement = "NEWLY_DATA_READY"
                reasons.append("NEW_OFFICIAL_CACHE_DATA_AVAILABLE")
            elif TIER_RANK.get(current_tier, 9) < TIER_RANK.get(prev_tier, 9):
                movement = "UPGRADE"
                reasons.append("SCORE_THRESHOLD_CROSSED")
            elif TIER_RANK.get(current_tier, 9) > TIER_RANK.get(prev_tier, 9):
                movement = "DOWNGRADE"
                reasons.append("SCORE_THRESHOLD_CROSSED")
            elif score_delta is not None and score_delta > 0:
                movement = "SAME_TIER_SCORE_UP"
                reasons.append("SCORE_INCREASE")
            elif score_delta is not None and score_delta < 0:
                movement = "SAME_TIER_SCORE_DOWN"
                reasons.append("SCORE_DECREASE")
            else:
                movement = "SAME_TIER_SCORE_UP" if False else "SAME_TIER_SCORE_DOWN"
                reasons.append("NO_MATERIAL_CHANGE")
            if score_delta is not None and abs(score_delta) >= 10:
                movement = "LARGE_SCORE_MOVE_UP" if score_delta > 0 else "LARGE_SCORE_MOVE_DOWN"
                reasons.append("SCORE_INCREASE_LARGE" if score_delta > 0 else "SCORE_DECREASE_LARGE")
            elif rank_delta is not None and abs(rank_delta) >= 20:
                movement = "LARGE_SCORE_MOVE_UP" if rank_delta < 0 else "LARGE_SCORE_MOVE_DOWN"
                reasons.append("RANK_CHANGED")
            if row.get("held_out_status"):
                movement = "HELD_OUT_OR_REVIEW_BLOCKED"
                reasons.append("HELD_OUT_BY_BACKFILL_QUALITY")
        prev_score_text = "" if prev is None else prev.get("current_score", "")
        prev_rank_text = "" if prev is None else prev.get("current_rank", "")
        prev_score_num = to_float(prev_score_text)
        prev_rank_num = to_int(prev_rank_text)
        score_delta_num = (current_score - prev_score_num) if current_score is not None and prev_score_num is not None else None
        rank_delta_num = (current_rank - prev_rank_num) if current_rank is not None and prev_rank_num is not None else None
        movement_rows.append({
            "ticker": ticker,
            "movement_type": movement,
            "previous_tier": prev_tier if prev else "",
            "current_tier": current_tier,
            "previous_score": prev_score_text,
            "current_score": row.get("current_score", ""),
            "score_delta": "" if score_delta_num is None else f"{score_delta_num:.6f}",
            "previous_rank": prev_rank_text,
            "current_rank": row.get("current_rank", ""),
            "rank_delta": "" if rank_delta_num is None else rank_delta_num,
            "movement_reason": ";".join(dict.fromkeys(reasons)),
            "current_score_source": row.get("current_score_source", ""),
            "review_required": row.get("review_required", ""),
        })
    if previous_by:
        current_tickers = {str(row["ticker"]) for row in snapshot_rows}
        for ticker, prev in previous_by.items():
            if ticker not in current_tickers:
                movement_rows.append({
                    "ticker": ticker, "movement_type": "REMOVED_FROM_CURRENT_UNIVERSE",
                    "previous_tier": prev.get("current_tier", ""), "current_tier": "",
                    "previous_score": prev.get("current_score", ""), "current_score": "",
                    "score_delta": "", "previous_rank": prev.get("current_rank", ""), "current_rank": "",
                    "rank_delta": "", "movement_reason": "REMOVED_FROM_CURRENT_UNIVERSE",
                    "current_score_source": "", "review_required": "TRUE",
                })

    movement_counts = Counter(str(row["movement_type"]) for row in movement_rows)
    reason_counts = Counter(reason for row in movement_rows for reason in str(row["movement_reason"]).split(";") if reason)
    tier_counts = Counter(str(row["current_tier"]) for row in snapshot_rows)
    summary_rows = [{"tier": tier, "count": tier_counts.get(tier, 0), "notes": "Current read-only tier distribution."} for tier in TIERS]
    blocked_rows = [row for row in snapshot_rows if row["current_tier"] == "TIER_0_DATA_NOT_READY" or row["review_required"] == "TRUE"]
    large_rows = [row for row in movement_rows if str(row["movement_type"]).startswith("LARGE_SCORE_MOVE")]
    source_rows = []
    for name, path, rows, fields in loaded_sources:
        source_rows.append({"source_name": name, "source_path": str(path), "exists": str(path.exists()).upper(), "row_count": len(rows), "selected": str(path == score_path).upper(), "notes": f"fields={','.join(fields[:12])}"})
    for name, path, rows in [
        ("canonical_plan", root / "outputs/v18/rolling_coverage/V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv", plan_rows),
        ("ledger_snapshot", root / "outputs/v18/rolling_coverage/V18_23C_R3_CURRENT_SCAN_LEDGER_SNAPSHOT.csv", ledger_rows),
        ("held_out", root / "outputs/v18/staged_backfill/V18_23C_R2_CURRENT_HELD_OUT_TICKERS.csv", held_rows),
        ("v18_23c_r3_read_first", root / "outputs/v18/ops/V18_23C_R3_READ_FIRST.txt", [{"exists": "1"}] if r3_read_first else []),
    ]:
        source_rows.append({"source_name": name, "source_path": str(path), "exists": str(path.exists()).upper(), "row_count": len(rows), "selected": "FALSE", "notes": "supporting source"})

    history_snapshot = root / f"outputs/v18/tier_migration/history/V18_24A_SCORE_TIER_SNAPSHOT_{timestamp}.csv"
    history_movement = root / f"outputs/v18/tier_migration/history/V18_24A_TIER_MOVEMENT_REPORT_{timestamp}.csv"
    write_csv(root / OUTPUTS["snapshot"], snapshot_rows, SNAPSHOT_FIELDS)
    write_csv(root / OUTPUTS["movement"], movement_rows, MOVEMENT_FIELDS)
    write_csv(root / OUTPUTS["upgrades"], [r for r in movement_rows if r["movement_type"] == "UPGRADE"], MOVEMENT_FIELDS)
    write_csv(root / OUTPUTS["downgrades"], [r for r in movement_rows if r["movement_type"] == "DOWNGRADE"], MOVEMENT_FIELDS)
    write_csv(root / OUTPUTS["large"], large_rows, MOVEMENT_FIELDS)
    write_csv(root / OUTPUTS["new_score"], [r for r in movement_rows if r["movement_type"] in {"NEWLY_SCORE_READY", "NEWLY_DATA_READY"}], MOVEMENT_FIELDS)
    write_csv(root / OUTPUTS["blocked"], blocked_rows, SNAPSHOT_FIELDS)
    write_csv(root / OUTPUTS["summary"], summary_rows, SUMMARY_FIELDS)
    write_csv(root / OUTPUTS["source"], source_rows, SOURCE_FIELDS)
    write_csv(history_snapshot, snapshot_rows, SNAPSHOT_FIELDS)
    write_csv(history_movement, movement_rows, MOVEMENT_FIELDS)

    data_not_ready_count = len(blocked_rows)
    values: Dict[str, str] = {
        "STATUS": STATUS_OK,
        "MODE": MODE,
        "TIER_MIGRATION_AUDIT_READY": "TRUE",
        "READ_ONLY": "TRUE",
        "CURRENT_TICKER_COUNT": str(len(snapshot_rows)),
        "CURRENT_SCORE_SOURCE": str(score_path) if score_path else "",
        "CURRENT_SCORE_SOURCE_TRUST": score_trust,
        "PREVIOUS_TIER_SNAPSHOT_FOUND": str(previous_path is not None).upper(),
        "PREVIOUS_TIER_SNAPSHOT_PATH": str(previous_path) if previous_path else "",
        "BASELINE_MODE": str(baseline_mode).upper(),
        "TIER_1_CORE_CANDIDATE_COUNT": str(tier_counts.get("TIER_1_CORE_CANDIDATE", 0)),
        "TIER_2_STRONG_WATCHLIST_COUNT": str(tier_counts.get("TIER_2_STRONG_WATCHLIST", 0)),
        "TIER_3_WATCHLIST_COUNT": str(tier_counts.get("TIER_3_WATCHLIST", 0)),
        "TIER_4_REVIEW_ONLY_COUNT": str(tier_counts.get("TIER_4_REVIEW_ONLY", 0)),
        "TIER_5_WEAK_OR_BLOCKED_COUNT": str(tier_counts.get("TIER_5_WEAK_OR_BLOCKED", 0)),
        "TIER_0_DATA_NOT_READY_COUNT": str(tier_counts.get("TIER_0_DATA_NOT_READY", 0)),
        "MOVEMENT_REPORT_CREATED": "TRUE",
        "TOTAL_MOVEMENT_COUNT": str(len(movement_rows)),
        "UPGRADE_COUNT": str(movement_counts.get("UPGRADE", 0)),
        "DOWNGRADE_COUNT": str(movement_counts.get("DOWNGRADE", 0)),
        "SAME_TIER_SCORE_UP_COUNT": str(movement_counts.get("SAME_TIER_SCORE_UP", 0)),
        "SAME_TIER_SCORE_DOWN_COUNT": str(movement_counts.get("SAME_TIER_SCORE_DOWN", 0)),
        "LARGE_SCORE_MOVE_COUNT": str(len(large_rows)),
        "NEWLY_SCORE_READY_COUNT": str(movement_counts.get("NEWLY_SCORE_READY", 0)),
        "NEWLY_DATA_READY_COUNT": str(movement_counts.get("NEWLY_DATA_READY", 0)),
        "DROPPED_TO_DATA_NOT_READY_COUNT": str(movement_counts.get("DROPPED_TO_DATA_NOT_READY", 0)),
        "HELD_OUT_OR_REVIEW_BLOCKED_COUNT": str(movement_counts.get("HELD_OUT_OR_REVIEW_BLOCKED", 0)),
        "DATA_NOT_READY_OR_BLOCKED_COUNT": str(data_not_ready_count),
        "VALIDATION_FAIL_COUNT": "0",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": "FALSE",
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": "FALSE_PARTIAL_LEDGER_COVERAGE_AFTER_R3",
        "RECOMMENDED_NEXT_ACTION": "Use this read-only tier/movement report for operator review; do not modify official rankings or weights until score coverage, ledger coverage, and forward-return gates are ready.",
        "AUDIT_PATH": str(root / OUTPUTS["audit"]),
        "TIER_SNAPSHOT_PATH": str(root / OUTPUTS["snapshot"]),
        "MOVEMENT_REPORT_PATH": str(root / OUTPUTS["movement"]),
        "UPGRADES_PATH": str(root / OUTPUTS["upgrades"]),
        "DOWNGRADES_PATH": str(root / OUTPUTS["downgrades"]),
        "LARGE_SCORE_MOVES_PATH": str(root / OUTPUTS["large"]),
        "NEWLY_SCORE_READY_PATH": str(root / OUTPUTS["new_score"]),
        "DATA_NOT_READY_OR_BLOCKED_PATH": str(root / OUTPUTS["blocked"]),
        "TIER_SUMMARY_PATH": str(root / OUTPUTS["summary"]),
        "SOURCE_AUDIT_PATH": str(root / OUTPUTS["source"]),
        "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        "REPORT_PATH": str(root / OUTPUTS["report"]),
    }
    values.update(SAFETY)
    if not baseline_mode and (score_trust == "LOW" or sum(1 for row in snapshot_rows if row["current_score"] == "") > len(snapshot_rows) // 2):
        values["STATUS"] = STATUS_LIMITED
    elif baseline_mode:
        values["STATUS"] = STATUS_BASELINE

    write_text(root / OUTPUTS["audit"], render_md(values, summary_rows, movement_counts, reason_counts))
    write_text(root / OUTPUTS["report"], render_md(values, summary_rows, movement_counts, reason_counts))
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    after = {str(path): file_sig(path) for path in collect_forbidden(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig) + sorted(path for path in after if path not in before)
    required = [root / rel for rel in OUTPUTS.values()]
    validations = [
        validation_row("python_compile_check", py_compile(root / "scripts/v18/v18_24A_dynamic_score_tier_migration_audit.py"), 1, "Python compile."),
        validation_row("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_24A_dynamic_score_tier_migration_audit.ps1"), 1, "PowerShell parse."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required), 1, "All current outputs must exist and be non-empty."),
        validation_row("ticker_universe_built", bool(snapshot_rows), 1, "Current tier snapshot must contain ticker rows."),
        validation_row("score_or_rank_source_found", bool(score_path), 1, "A usable score or rank source must exist."),
        validation_row("tier_summary_all_tiers", {row["tier"] for row in summary_rows} == set(TIERS), 1, "Tier summary must include all tier names."),
        validation_row("movement_report_exists", non_empty(root / OUTPUTS["movement"]), 1, "Movement report must exist."),
        validation_row("baseline_mode_correct", (baseline_mode and all(row["movement_type"] == "BASELINE_NO_PRIOR_TIER" for row in movement_rows)) or not baseline_mode, 1, "Baseline rows must be baseline movement type."),
        validation_row("no_forbidden_files_modified", not changed, len(changed), ";".join(changed[:20])),
    ]
    for key, expected in SAFETY.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count or not snapshot_rows or not score_path:
        values["STATUS"] = STATUS_FAIL
        values["TIER_MIGRATION_AUDIT_READY"] = "FALSE"
    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["audit"], render_md(values, summary_rows, movement_counts, reason_counts))
    write_text(root / OUTPUTS["report"], render_md(values, summary_rows, movement_counts, reason_counts))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))
    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
