from __future__ import annotations

import argparse
import csv
import datetime as dt
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_24B_TIER_MIGRATION_OPERATOR_HOMEPAGE_READY"
STATUS_BASELINE = "WARN_V18_24B_TIER_MIGRATION_OPERATOR_HOMEPAGE_BASELINE_READY"
STATUS_LIMITED = "WARN_V18_24B_TIER_MIGRATION_OPERATOR_HOMEPAGE_LIMITED_SOURCE"
STATUS_FAIL = "FAIL_V18_24B_TIER_MIGRATION_OPERATOR_HOMEPAGE"
MODE = "READ_ONLY_TIER_MIGRATION_OPERATOR_HOMEPAGE"

OUTPUTS = {
    "homepage": "outputs/v18/operator_homepage/V18_24B_CURRENT_TIER_MIGRATION_OPERATOR_HOMEPAGE.md",
    "tier_summary": "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_TIER_SUMMARY.csv",
    "movement_highlights": "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_MOVEMENT_HIGHLIGHTS.csv",
    "top_candidates": "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_TOP_TIER_CANDIDATES.csv",
    "data_not_ready": "outputs/v18/tier_migration/V18_24B_CURRENT_OPERATOR_DATA_NOT_READY_SUMMARY.csv",
    "source": "outputs/v18/tier_migration/V18_24B_CURRENT_SOURCE_AUDIT.csv",
    "validation": "outputs/v18/tier_migration/V18_24B_CURRENT_VALIDATION.csv",
    "read_first": "outputs/v18/ops/V18_24B_READ_FIRST.txt",
    "report": "outputs/v18/ops/V18_24B_CURRENT_TIER_MIGRATION_OPERATOR_HOMEPAGE_REPORT.md",
}

V18_24A = {
    "read_first": "outputs/v18/ops/V18_24A_READ_FIRST.txt",
    "audit": "outputs/v18/tier_migration/V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT.md",
    "snapshot": "outputs/v18/tier_migration/V18_24A_CURRENT_SCORE_TIER_SNAPSHOT.csv",
    "movement": "outputs/v18/tier_migration/V18_24A_CURRENT_TIER_MOVEMENT_REPORT.csv",
    "upgrades": "outputs/v18/tier_migration/V18_24A_CURRENT_UPGRADES.csv",
    "downgrades": "outputs/v18/tier_migration/V18_24A_CURRENT_DOWNGRADES.csv",
    "large": "outputs/v18/tier_migration/V18_24A_CURRENT_LARGE_SCORE_MOVES.csv",
    "new_score": "outputs/v18/tier_migration/V18_24A_CURRENT_NEWLY_SCORE_READY.csv",
    "blocked": "outputs/v18/tier_migration/V18_24A_CURRENT_DATA_NOT_READY_OR_BLOCKED.csv",
    "tier_summary": "outputs/v18/tier_migration/V18_24A_CURRENT_TIER_SUMMARY.csv",
}

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "TIER_MIGRATION_OPERATOR_HOMEPAGE_READY", "READ_ONLY",
    "V18_24A_SOURCE_AVAILABLE", "V18_24A_BASELINE_MODE", "CURRENT_TICKER_COUNT",
    "CURRENT_SCORE_SOURCE", "CURRENT_SCORE_SOURCE_TRUST", "TIER_1_CORE_CANDIDATE_COUNT",
    "TIER_2_STRONG_WATCHLIST_COUNT", "TIER_3_WATCHLIST_COUNT", "TIER_4_REVIEW_ONLY_COUNT",
    "TIER_5_WEAK_OR_BLOCKED_COUNT", "TIER_0_DATA_NOT_READY_COUNT", "MOVEMENT_REPORT_AVAILABLE",
    "TOTAL_MOVEMENT_COUNT", "UPGRADE_COUNT", "DOWNGRADE_COUNT", "LARGE_SCORE_MOVE_COUNT",
    "NEWLY_SCORE_READY_COUNT", "DATA_NOT_READY_OR_BLOCKED_COUNT", "TOP_TIER_CANDIDATE_COUNT",
    "OPERATOR_HOMEPAGE_CREATED", "VALIDATION_FAIL_COUNT", "OFFICIAL_DECISION_IMPACT",
    "BUY_PERMISSION_MODIFIED", "AUTO_TRADE", "AUTO_SELL", "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_WRITTEN", "STAGED_PRICE_HISTORY_WRITTEN", "LEDGER_MODIFIED", "RANKING_MODIFIED",
    "SIGNAL_SNAPSHOT_MODIFIED", "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED",
    "BACKTEST_EXECUTED", "BACKTEST_RESULTS_APPLIED", "FACTOR_EFFECT_CLAIM_ALLOWED",
    "WEIGHT_CHANGE_ALLOWED", "PRODUCTION_PROMOTION_ALLOWED", "DAILY_COMMAND_CENTER_INTEGRATION_ALLOWED",
    "TRUE_5DAY_UNIQUE_COVERAGE_MET", "TRUE_5DAY_UNIQUE_COVERAGE_STATUS", "RECOMMENDED_NEXT_ACTION",
    "OPERATOR_HOMEPAGE_PATH", "OPERATOR_TIER_SUMMARY_PATH", "OPERATOR_MOVEMENT_HIGHLIGHTS_PATH",
    "OPERATOR_TOP_TIER_CANDIDATES_PATH", "OPERATOR_DATA_NOT_READY_SUMMARY_PATH",
    "SOURCE_AUDIT_PATH", "VALIDATION_PATH", "REPORT_PATH",
]

TIER_ORDER = [
    "TIER_1_CORE_CANDIDATE",
    "TIER_2_STRONG_WATCHLIST",
    "TIER_3_WATCHLIST",
    "TIER_4_REVIEW_ONLY",
    "TIER_5_WEAK_OR_BLOCKED",
    "TIER_0_DATA_NOT_READY",
]

TIER_SUMMARY_FIELDS = ["tier", "count", "operator_note", "detail_path"]
HIGHLIGHT_FIELDS = ["section", "ticker", "movement_type", "previous_tier", "current_tier", "previous_score", "current_score", "score_delta", "movement_reason", "detail_path"]
TOP_FIELDS = ["ticker", "current_tier", "current_score", "current_rank", "factor_pack_score", "technical_timing_score", "latest_success_scan_date", "current_tier_reason", "detail_path"]
BLOCKED_FIELDS = ["summary_type", "ticker", "current_tier", "current_score", "data_readiness_status", "held_out_status", "current_tier_reason", "count", "detail_path"]
SOURCE_FIELDS = ["source_name", "source_path", "exists", "row_count", "required", "notes"]
VALIDATION_FIELDS = ["validation_check", "status", "fail_count", "notes"]

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


def parse_read_first(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    out: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def to_float(value: object) -> float:
    try:
        return float(str(value or "").replace(",", ""))
    except ValueError:
        return -1.0


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


def non_empty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def py_compile(path: Path) -> bool:
    return subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True).returncode == 0


def ps_parse(path: Path) -> bool:
    escaped = str(path).replace("'", "''")
    cmd = f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw '{escaped}'), [ref]$null) | Out-Null; 'OK'"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return result.returncode == 0 and "OK" in result.stdout


def validation_row(name: str, ok: bool, fail_count: int, notes: str) -> Dict[str, object]:
    return {"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": 0 if ok else fail_count, "notes": notes}


def render_read_first(values: Dict[str, str]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def top_rows(rows: Sequence[Dict[str, str]], tier: str, limit: int) -> List[Dict[str, str]]:
    selected = [row for row in rows if row.get("current_tier") == tier]
    return sorted(selected, key=lambda row: to_float(row.get("current_score")), reverse=True)[:limit]


def render_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: int = 10) -> str:
    if not rows:
        return "_None currently._"
    selected = list(rows)[:limit]
    header = "| " + " | ".join(fields) + " |"
    sep = "| " + " | ".join("---" for _ in fields) + " |"
    body = ["| " + " | ".join(str(row.get(field, "")) for field in fields) + " |" for row in selected]
    return "\n".join([header, sep] + body)


def render_homepage(values: Dict[str, str], tier_summary: Sequence[Dict[str, object]], highlights: Sequence[Dict[str, object]], top_candidates: Sequence[Dict[str, object]], blocked_rows: Sequence[Dict[str, object]], reason_counts: Counter[str]) -> str:
    tier_table = render_table(tier_summary, ["tier", "count", "operator_note"], 10)
    upgrades = [row for row in highlights if row.get("section") == "UPGRADE"]
    downgrades = [row for row in highlights if row.get("section") == "DOWNGRADE"]
    large = [row for row in highlights if row.get("section") == "LARGE_SCORE_MOVE"]
    new_ready = [row for row in highlights if row.get("section") == "NEWLY_READY"]
    reason_table = render_table([{"reason": k, "count": v} for k, v in reason_counts.most_common(12)], ["reason", "count"], 12)
    return f"""# V18.24B Tier Migration Operator Homepage

Generated: {dt.datetime.now().isoformat(timespec='seconds')}

## Overall Status
Status: {values['STATUS']}

## Tier Migration Status
V18.24A source available: {values['V18_24A_SOURCE_AVAILABLE']}. Current tickers: {values['CURRENT_TICKER_COUNT']}. Score source trust: {values['CURRENT_SCORE_SOURCE_TRUST']}.

## Baseline Vs Comparison Mode
Baseline mode: {values['V18_24A_BASELINE_MODE']}. If TRUE, upgrade/downgrade counts are expected to be zero until a later run compares against this baseline.

## Current Tier Distribution
{tier_table}

## Today's Upgrades
{render_table(upgrades, ['ticker', 'previous_tier', 'current_tier', 'score_delta', 'movement_reason'], 12)}

## Today's Downgrades
{render_table(downgrades, ['ticker', 'previous_tier', 'current_tier', 'score_delta', 'movement_reason'], 12)}

## Large Score Movers
{render_table(large, ['ticker', 'movement_type', 'score_delta', 'movement_reason'], 12)}

## Newly Score-Ready / Data-Ready
{render_table(new_ready, ['ticker', 'movement_type', 'current_tier', 'movement_reason'], 12)}

## Data-Not-Ready Or Blocked Summary
Data-not-ready/blocked count: {values['DATA_NOT_READY_OR_BLOCKED_COUNT']}.
{render_table(blocked_rows, ['summary_type', 'ticker', 'current_tier', 'data_readiness_status', 'held_out_status'], 12)}

## Top Tier 1 / Tier 2 Candidates
{render_table(top_candidates, ['ticker', 'current_tier', 'current_score', 'current_rank', 'latest_success_scan_date'], 20)}

## Movement Reason Summary
{reason_table}

## Coverage / Trust Notes
TRUE_5DAY_UNIQUE_COVERAGE_MET remains {values['TRUE_5DAY_UNIQUE_COVERAGE_MET']}: {values['TRUE_5DAY_UNIQUE_COVERAGE_STATUS']}.

## What Remains Blocked
Official ranking changes, factor effect claims, weight changes, production promotion, daily command center integration, backtests, auto-trade, and auto-sell remain blocked.

## Exact Files To Read Next
- {values['OPERATOR_HOMEPAGE_PATH']}
- {values['OPERATOR_TIER_SUMMARY_PATH']}
- {values['OPERATOR_MOVEMENT_HIGHLIGHTS_PATH']}
- {values['OPERATOR_TOP_TIER_CANDIDATES_PATH']}
- {values['OPERATOR_DATA_NOT_READY_SUMMARY_PATH']}

## Safety Invariants
Official decision impact: NONE. Ranking, factor pack, technical timing, signal snapshot, ledger, price cache, backtest, and trading state were not modified.

## Recommended Next Action
{values['RECOMMENDED_NEXT_ACTION']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    before = {str(path): file_sig(path) for path in collect_forbidden(root)}

    read_first = parse_read_first(root / V18_24A["read_first"])
    snapshot_rows, _ = read_csv(root / V18_24A["snapshot"])
    movement_rows, _ = read_csv(root / V18_24A["movement"])
    upgrades, _ = read_csv(root / V18_24A["upgrades"])
    downgrades, _ = read_csv(root / V18_24A["downgrades"])
    large_moves, _ = read_csv(root / V18_24A["large"])
    newly_ready, _ = read_csv(root / V18_24A["new_score"])
    blocked_snapshot, _ = read_csv(root / V18_24A["blocked"])
    tier_summary_in, _ = read_csv(root / V18_24A["tier_summary"])
    r3 = parse_read_first(root / "outputs/v18/ops/V18_23C_R3_READ_FIRST.txt")

    source_available = bool(read_first) and bool(snapshot_rows)
    baseline = read_first.get("BASELINE_MODE", "FALSE")
    tier_counts = {row.get("tier", ""): row.get("count", "0") for row in tier_summary_in}
    tier_summary = [
        {
            "tier": tier,
            "count": tier_counts.get(tier, "0"),
            "operator_note": "Read-only tier migration category.",
            "detail_path": str(root / V18_24A["snapshot"]),
        }
        for tier in TIER_ORDER
    ]

    highlight_rows: List[Dict[str, object]] = []
    def add_highlights(section: str, rows: Sequence[Dict[str, str]], limit: int = 25) -> None:
        for row in rows[:limit]:
            highlight_rows.append({
                "section": section,
                "ticker": row.get("ticker", ""),
                "movement_type": row.get("movement_type", ""),
                "previous_tier": row.get("previous_tier", ""),
                "current_tier": row.get("current_tier", ""),
                "previous_score": row.get("previous_score", ""),
                "current_score": row.get("current_score", ""),
                "score_delta": row.get("score_delta", ""),
                "movement_reason": row.get("movement_reason", ""),
                "detail_path": str(root / V18_24A["movement"]),
            })
    add_highlights("UPGRADE", upgrades)
    add_highlights("DOWNGRADE", downgrades)
    add_highlights("LARGE_SCORE_MOVE", large_moves)
    add_highlights("NEWLY_READY", newly_ready)
    if not highlight_rows:
        highlight_rows.append({
            "section": "BASELINE",
            "ticker": "",
            "movement_type": "BASELINE_NO_PRIOR_TIER",
            "previous_tier": "",
            "current_tier": "",
            "previous_score": "",
            "current_score": "",
            "score_delta": "",
            "movement_reason": "V18.24A baseline mode; no prior snapshot.",
            "detail_path": str(root / V18_24A["movement"]),
        })

    top_candidates: List[Dict[str, object]] = []
    for row in top_rows(snapshot_rows, "TIER_1_CORE_CANDIDATE", 25) + top_rows(snapshot_rows, "TIER_2_STRONG_WATCHLIST", 25):
        top_candidates.append({
            "ticker": row.get("ticker", ""),
            "current_tier": row.get("current_tier", ""),
            "current_score": row.get("current_score", ""),
            "current_rank": row.get("current_rank", ""),
            "factor_pack_score": row.get("factor_pack_score", ""),
            "technical_timing_score": row.get("technical_timing_score", ""),
            "latest_success_scan_date": row.get("latest_success_scan_date", ""),
            "current_tier_reason": row.get("current_tier_reason", ""),
            "detail_path": str(root / V18_24A["snapshot"]),
        })

    blocked_rows: List[Dict[str, object]] = [{
        "summary_type": "TOTAL_DATA_NOT_READY_OR_BLOCKED",
        "ticker": "",
        "current_tier": "",
        "current_score": "",
        "data_readiness_status": "",
        "held_out_status": "",
        "current_tier_reason": "",
        "count": len(blocked_snapshot),
        "detail_path": str(root / V18_24A["blocked"]),
    }]
    for row in blocked_snapshot[:50]:
        blocked_rows.append({
            "summary_type": "SAMPLE",
            "ticker": row.get("ticker", ""),
            "current_tier": row.get("current_tier", ""),
            "current_score": row.get("current_score", ""),
            "data_readiness_status": row.get("data_readiness_status", ""),
            "held_out_status": row.get("held_out_status", ""),
            "current_tier_reason": row.get("current_tier_reason", ""),
            "count": "",
            "detail_path": str(root / V18_24A["blocked"]),
        })

    reason_counts = Counter(reason for row in movement_rows for reason in str(row.get("movement_reason", "")).split(";") if reason)
    source_rows = []
    for key, rel in V18_24A.items():
        rows, _ = read_csv(root / rel) if rel.endswith(".csv") else ([], [])
        source_rows.append({
            "source_name": f"v18_24a_{key}",
            "source_path": rel,
            "exists": str((root / rel).exists()).upper(),
            "row_count": len(rows) if rel.endswith(".csv") else (1 if (root / rel).exists() else 0),
            "required": "TRUE" if key in {"read_first", "snapshot", "movement", "tier_summary"} else "FALSE",
            "notes": "V18.24A source consumed read-only.",
        })
    source_rows.append({
        "source_name": "v18_23c_r3_read_first",
        "source_path": "outputs/v18/ops/V18_23C_R3_READ_FIRST.txt",
        "exists": str(bool(r3)).upper(),
        "row_count": 1 if r3 else 0,
        "required": "FALSE",
        "notes": "Coverage/trust context.",
    })

    values: Dict[str, str] = {
        "STATUS": STATUS_OK,
        "MODE": MODE,
        "TIER_MIGRATION_OPERATOR_HOMEPAGE_READY": "TRUE",
        "READ_ONLY": "TRUE",
        "V18_24A_SOURCE_AVAILABLE": str(source_available).upper(),
        "V18_24A_BASELINE_MODE": baseline,
        "CURRENT_TICKER_COUNT": read_first.get("CURRENT_TICKER_COUNT", str(len(snapshot_rows))),
        "CURRENT_SCORE_SOURCE": read_first.get("CURRENT_SCORE_SOURCE", ""),
        "CURRENT_SCORE_SOURCE_TRUST": read_first.get("CURRENT_SCORE_SOURCE_TRUST", ""),
        "TIER_1_CORE_CANDIDATE_COUNT": read_first.get("TIER_1_CORE_CANDIDATE_COUNT", tier_counts.get("TIER_1_CORE_CANDIDATE", "0")),
        "TIER_2_STRONG_WATCHLIST_COUNT": read_first.get("TIER_2_STRONG_WATCHLIST_COUNT", tier_counts.get("TIER_2_STRONG_WATCHLIST", "0")),
        "TIER_3_WATCHLIST_COUNT": read_first.get("TIER_3_WATCHLIST_COUNT", tier_counts.get("TIER_3_WATCHLIST", "0")),
        "TIER_4_REVIEW_ONLY_COUNT": read_first.get("TIER_4_REVIEW_ONLY_COUNT", tier_counts.get("TIER_4_REVIEW_ONLY", "0")),
        "TIER_5_WEAK_OR_BLOCKED_COUNT": read_first.get("TIER_5_WEAK_OR_BLOCKED_COUNT", tier_counts.get("TIER_5_WEAK_OR_BLOCKED", "0")),
        "TIER_0_DATA_NOT_READY_COUNT": read_first.get("TIER_0_DATA_NOT_READY_COUNT", tier_counts.get("TIER_0_DATA_NOT_READY", "0")),
        "MOVEMENT_REPORT_AVAILABLE": str(bool(movement_rows)).upper(),
        "TOTAL_MOVEMENT_COUNT": read_first.get("TOTAL_MOVEMENT_COUNT", str(len(movement_rows))),
        "UPGRADE_COUNT": read_first.get("UPGRADE_COUNT", str(len(upgrades))),
        "DOWNGRADE_COUNT": read_first.get("DOWNGRADE_COUNT", str(len(downgrades))),
        "LARGE_SCORE_MOVE_COUNT": read_first.get("LARGE_SCORE_MOVE_COUNT", str(len(large_moves))),
        "NEWLY_SCORE_READY_COUNT": read_first.get("NEWLY_SCORE_READY_COUNT", str(len(newly_ready))),
        "DATA_NOT_READY_OR_BLOCKED_COUNT": read_first.get("DATA_NOT_READY_OR_BLOCKED_COUNT", str(len(blocked_snapshot))),
        "TOP_TIER_CANDIDATE_COUNT": str(len(top_candidates)),
        "OPERATOR_HOMEPAGE_CREATED": "TRUE",
        "VALIDATION_FAIL_COUNT": "0",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": r3.get("TRUE_5DAY_UNIQUE_COVERAGE_MET", read_first.get("TRUE_5DAY_UNIQUE_COVERAGE_MET", "FALSE")),
        "TRUE_5DAY_UNIQUE_COVERAGE_STATUS": r3.get("TRUE_5DAY_UNIQUE_COVERAGE_STATUS", read_first.get("TRUE_5DAY_UNIQUE_COVERAGE_STATUS", "")),
        "RECOMMENDED_NEXT_ACTION": "Read the V18.24B homepage first each day; rerun V18.24A after score/readiness changes to produce real upgrade/downgrade movement against this baseline.",
        "OPERATOR_HOMEPAGE_PATH": str(root / OUTPUTS["homepage"]),
        "OPERATOR_TIER_SUMMARY_PATH": str(root / OUTPUTS["tier_summary"]),
        "OPERATOR_MOVEMENT_HIGHLIGHTS_PATH": str(root / OUTPUTS["movement_highlights"]),
        "OPERATOR_TOP_TIER_CANDIDATES_PATH": str(root / OUTPUTS["top_candidates"]),
        "OPERATOR_DATA_NOT_READY_SUMMARY_PATH": str(root / OUTPUTS["data_not_ready"]),
        "SOURCE_AUDIT_PATH": str(root / OUTPUTS["source"]),
        "VALIDATION_PATH": str(root / OUTPUTS["validation"]),
        "REPORT_PATH": str(root / OUTPUTS["report"]),
    }
    values.update(SAFETY)
    if baseline == "TRUE":
        values["STATUS"] = STATUS_BASELINE

    write_csv(root / OUTPUTS["tier_summary"], tier_summary, TIER_SUMMARY_FIELDS)
    write_csv(root / OUTPUTS["movement_highlights"], highlight_rows, HIGHLIGHT_FIELDS)
    write_csv(root / OUTPUTS["top_candidates"], top_candidates, TOP_FIELDS)
    write_csv(root / OUTPUTS["data_not_ready"], blocked_rows, BLOCKED_FIELDS)
    write_csv(root / OUTPUTS["source"], source_rows, SOURCE_FIELDS)
    write_text(root / OUTPUTS["homepage"], render_homepage(values, tier_summary, highlight_rows, top_candidates, blocked_rows, reason_counts))
    write_text(root / OUTPUTS["report"], render_homepage(values, tier_summary, highlight_rows, top_candidates, blocked_rows, reason_counts))
    write_csv(root / OUTPUTS["validation"], [validation_row("validation_initialized", True, 0, "Validation initialized.")], VALIDATION_FIELDS)
    write_text(root / OUTPUTS["read_first"], render_read_first(values))

    after = {str(path): file_sig(path) for path in collect_forbidden(root)}
    changed = sorted(path for path, sig in before.items() if after.get(path) != sig) + sorted(path for path in after if path not in before)
    required_outputs = [root / rel for rel in OUTPUTS.values()]
    tier_names = {row["tier"] for row in tier_summary}
    validations = [
        validation_row("python_compile_check", py_compile(root / "scripts/v18/v18_24B_tier_migration_operator_homepage.py"), 1, "Python compile."),
        validation_row("powershell_parse_check", ps_parse(root / "scripts/v18/run_v18_24B_tier_migration_operator_homepage.ps1"), 1, "PowerShell parse."),
        validation_row("required_outputs_exist_non_empty", all(non_empty(path) for path in required_outputs), 1, "All V18.24B outputs must exist and be non-empty."),
        validation_row("v18_24a_snapshot_readable", bool(snapshot_rows), 1, "V18.24A tier snapshot must be readable."),
        validation_row("tier_summary_all_tiers", set(TIER_ORDER).issubset(tier_names), 1, "Operator tier summary must include all tiers."),
        validation_row("movement_highlights_exists", non_empty(root / OUTPUTS["movement_highlights"]), 1, "Movement highlights must exist even in baseline mode."),
        validation_row("top_tier_candidates_available", bool(top_candidates), 1, "Top tier candidates should contain Tier 1/Tier 2 rows if available."),
        validation_row("data_not_ready_summary_available", bool(blocked_rows), 1, "Data-not-ready summary must contain count/sample rows."),
        validation_row("no_forbidden_files_modified", not changed, len(changed), ";".join(changed[:20])),
    ]
    for key, expected in SAFETY.items():
        validations.append(validation_row(f"safety_{key.lower()}", values.get(key) == expected, 1, f"Expected {key}={expected}; actual {values.get(key)}."))
    fail_count = sum(int(row["fail_count"]) for row in validations)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count or not source_available:
        values["STATUS"] = STATUS_FAIL
        values["TIER_MIGRATION_OPERATOR_HOMEPAGE_READY"] = "FALSE"
    elif baseline == "TRUE":
        values["STATUS"] = STATUS_BASELINE
    elif any(row["required"] == "FALSE" and row["exists"] == "FALSE" for row in source_rows):
        values["STATUS"] = STATUS_LIMITED
    else:
        values["STATUS"] = STATUS_OK
    write_csv(root / OUTPUTS["validation"], validations, VALIDATION_FIELDS)
    write_text(root / OUTPUTS["homepage"], render_homepage(values, tier_summary, highlight_rows, top_candidates, blocked_rows, reason_counts))
    write_text(root / OUTPUTS["report"], render_homepage(values, tier_summary, highlight_rows, top_candidates, blocked_rows, reason_counts))
    write_text(root / OUTPUTS["read_first"], render_read_first(values))
    for field in READ_FIRST_FIELDS:
        print(f"{field}: {values.get(field, '')}")
    return 0 if values["STATUS"] != STATUS_FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
