from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_16I_ROLLING_SCAN_COVERAGE_POLICY_OPTIMIZER_READY"
STATUS_WARN = "WARN_V18_16I_ROLLING_SCAN_COVERAGE_POLICY_OPTIMIZER_VALIDATION_FAILED"
MODE = "DRYRUN_POLICY_OPTIMIZER"
COVERAGE_WINDOW_TRADING_DAYS = 5
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

TIER_ORDER = ["CORE_DAILY", "CANDIDATE", "STRONG_WATCH", "WATCHLIST", "RESEARCH"]
TIER_TARGET_FREQUENCY = {
    "CORE_DAILY": "EVERY_TRADING_DAY",
    "CANDIDATE": "EVERY_TRADING_DAY_OR_NEAR_DAILY",
    "STRONG_WATCH": "EVERY_2_TRADING_DAYS",
    "WATCHLIST": "EVERY_3_TRADING_DAYS",
    "RESEARCH": "EVERY_5_TRADING_DAYS_ROTATION",
}
TIER_INTERVAL_DAYS = {
    "CORE_DAILY": 1,
    "CANDIDATE": 1,
    "STRONG_WATCH": 2,
    "WATCHLIST": 3,
    "RESEARCH": 5,
}

AUDIT_FIELDS = ["metric", "current_value", "recommended_value", "status", "reason", "source_file", "confidence"]
TIER_FIELDS = [
    "tier",
    "current_count",
    "current_scan_frequency",
    "recommended_scan_frequency",
    "recommended_daily_quota",
    "five_day_target_count",
    "reason",
    "confidence",
]
PLAN_FIELDS = [
    "ticker",
    "tier",
    "last_scan_date",
    "current_priority",
    "recommended_scan_day",
    "recommended_reason",
    "stale_risk_level",
    "confidence",
]
FIVE_DAY_FIELDS = [
    "plan_day",
    "planned_total_scan_count",
    "core_daily_count",
    "candidate_count",
    "strong_watch_count",
    "watchlist_count",
    "research_count",
    "cumulative_expected_coverage",
    "expected_uncovered_remaining",
    "meets_target",
    "notes",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            pass
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            pass
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except Exception:
        return {}


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_py(path: Path) -> Tuple[bool, str]:
    try:
        ast.parse(read_text(path), filename=str(path))
        return True, "OK_COMPILE"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def first_value(path: Path, key: str) -> str:
    target = key.upper()
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        if left.strip().upper().lstrip("- ").strip() == target:
            return right.strip()
    return ""


def to_int(value: object, default: int = 0) -> int:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return default
    try:
        return int(float(text))
    except Exception:
        return default


def to_float(value: object, default: float = 0.0) -> float:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return default
    try:
        return float(text)
    except Exception:
        return default


def parse_date(value: object) -> dt.date | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(text[:19], fmt).date()
        except Exception:
            pass
    return None


def bool_text(value: bool) -> str:
    return str(bool(value)).upper()


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def file_hashes(paths: Iterable[Path]) -> Dict[str, str]:
    return {str(path.resolve()): sha256(path) for path in paths if path.exists() and path.is_file()}


def tier_of(row: Dict[str, str]) -> str:
    tier = str(row.get("universe_tier") or "").strip().upper()
    if tier in TIER_ORDER:
        return tier
    if str(row.get("is_core_daily", "")).upper() == "TRUE":
        return "CORE_DAILY"
    if str(row.get("is_candidate", "")).upper() == "TRUE":
        return "CANDIDATE"
    if str(row.get("is_watchlist", "")).upper() == "TRUE":
        return "WATCHLIST"
    return "RESEARCH"


def selected_counts_by_tier(plan_rows: Sequence[Dict[str, str]]) -> Counter:
    counts: Counter = Counter()
    for row in plan_rows:
        if str(row.get("selected_this_run", "")).upper() == "TRUE":
            counts[tier_of(row)] += 1
    return counts


def runtime_confidence(v16f_read: Path) -> Tuple[str, str]:
    max_runtime = to_float(first_value(v16f_read, "MAX_RUNTIME_SECONDS"))
    soft_stop = to_float(first_value(v16f_read, "SOFT_STOP_SECONDS"))
    actual = to_float(first_value(v16f_read, "ACTUAL_RUNTIME_SECONDS"))
    if max_runtime and soft_stop and actual:
        if actual <= soft_stop:
            return "HIGH", f"ACTUAL_RUNTIME_SECONDS={actual}; SOFT_STOP_SECONDS={soft_stop}; MAX_RUNTIME_SECONDS={max_runtime}"
        return "MEDIUM", f"runtime exceeded soft stop: ACTUAL_RUNTIME_SECONDS={actual}; SOFT_STOP_SECONDS={soft_stop}"
    return "LOW", "Runtime fields are incomplete; optimizer cannot prove runtime headroom."


def stale_risk(row: Dict[str, str], today: dt.date) -> str:
    tier = tier_of(row)
    last = parse_date(row.get("last_scan_date"))
    days = to_int(row.get("days_since_last_scan"), -1)
    if last:
        days = (today - last).days
    if tier in {"CORE_DAILY", "CANDIDATE"} and days > 1:
        return "HIGH"
    if tier == "STRONG_WATCH" and days > 2:
        return "HIGH"
    if tier == "WATCHLIST" and days > 5:
        return "MEDIUM"
    if tier == "RESEARCH" and days > 10:
        return "MEDIUM"
    return "LOW"


def allocate_quota(total_required: int, tier_counts: Dict[str, int]) -> Dict[str, int]:
    quotas = {tier: 0 for tier in TIER_ORDER}
    quotas["CORE_DAILY"] = tier_counts.get("CORE_DAILY", 0)
    quotas["CANDIDATE"] = tier_counts.get("CANDIDATE", 0)
    remaining = max(0, total_required - quotas["CORE_DAILY"] - quotas["CANDIDATE"])
    strong_target = min(tier_counts.get("STRONG_WATCH", 0), math.ceil(tier_counts.get("STRONG_WATCH", 0) / 2))
    watch_target = min(tier_counts.get("WATCHLIST", 0), math.ceil(tier_counts.get("WATCHLIST", 0) / 3))
    research_target = min(tier_counts.get("RESEARCH", 0), max(0, remaining - strong_target - watch_target))
    for tier, target in [("STRONG_WATCH", strong_target), ("WATCHLIST", watch_target), ("RESEARCH", research_target)]:
        take = min(remaining, target)
        quotas[tier] = take
        remaining -= take
    if remaining > 0:
        for tier in ["RESEARCH", "WATCHLIST", "STRONG_WATCH"]:
            cap = tier_counts.get(tier, 0)
            take = min(remaining, max(0, cap - quotas[tier]))
            quotas[tier] += take
            remaining -= take
            if remaining <= 0:
                break
    return quotas


def build_rotation(
    rows_by_tier: Dict[str, List[Dict[str, str]]],
    quotas: Dict[str, int],
    daily_target: int,
    today: dt.date,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    plan_rows: List[Dict[str, object]] = []
    five_day_rows: List[Dict[str, object]] = []
    per_day_counts: Dict[int, Counter] = {day: Counter() for day in range(1, 6)}
    scheduled_by_ticker: Dict[str, str] = {}

    daily_fixed = len(rows_by_tier.get("CORE_DAILY", [])) + len(rows_by_tier.get("CANDIDATE", []))
    variable_capacity = max(0, daily_target - daily_fixed)
    remaining_capacity = {day: variable_capacity for day in range(1, 6)}

    for tier in ["CORE_DAILY", "CANDIDATE"]:
        for row in rows_by_tier.get(tier, []):
            ticker = str(row.get("ticker", "")).strip().upper()
            if not ticker:
                continue
            scheduled_by_ticker[ticker] = "EVERY_DAY"
            for day in range(1, 6):
                per_day_counts[day][tier] += 1

    for tier in ["STRONG_WATCH", "WATCHLIST", "RESEARCH"]:
        sorted_rows = sorted(
            rows_by_tier.get(tier, []),
            key=lambda r: (
                parse_date(r.get("last_scan_date")) or dt.date(1900, 1, 1),
                -to_int(r.get("scan_priority")),
                str(r.get("ticker", "")),
            ),
        )
        max_daily_for_tier = max(0, quotas.get(tier, 0))
        day = 1
        used_by_day = Counter()
        for row in sorted_rows:
            ticker = str(row.get("ticker", "")).strip().upper()
            if not ticker:
                continue
            assigned = ""
            for _ in range(5):
                if remaining_capacity[day] > 0 and (tier == "RESEARCH" or used_by_day[(tier, day)] < max_daily_for_tier):
                    assigned = f"DAY_{day}"
                    per_day_counts[day][tier] += 1
                    remaining_capacity[day] -= 1
                    used_by_day[(tier, day)] += 1
                    day = 1 if day == 5 else day + 1
                    break
                day = 1 if day == 5 else day + 1
            if not assigned:
                assigned = "UNSCHEDULED_REQUIRES_POLICY_REVIEW"
            scheduled_by_ticker[ticker] = assigned

    for tier in TIER_ORDER:
        sorted_rows = sorted(
            rows_by_tier.get(tier, []),
            key=lambda r: (
                parse_date(r.get("last_scan_date")) or dt.date(1900, 1, 1),
                -to_int(r.get("scan_priority")),
                str(r.get("ticker", "")),
            ),
        )
        for row in sorted_rows:
            ticker = str(row.get("ticker", "")).strip().upper()
            if not ticker:
                continue
            day = scheduled_by_ticker.get(ticker, "UNSCHEDULED_REQUIRES_POLICY_REVIEW")
            if day == "EVERY_DAY":
                reason = f"{tier} receives daily/near-daily coverage before lower tiers."
            elif day.startswith("DAY_"):
                reason = f"{tier} rotated by stale date and priority within available daily quota."
            else:
                reason = f"{tier} remains outside the 5-day advisory plan because the dry-run target preserves the daily cap."
            plan_rows.append({
                "ticker": ticker,
                "tier": tier,
                "last_scan_date": row.get("last_scan_date", ""),
                "current_priority": row.get("scan_priority", ""),
                "recommended_scan_day": day,
                "recommended_reason": reason,
                "stale_risk_level": stale_risk(row, today),
                "confidence": "HIGH" if tier in {"CORE_DAILY", "CANDIDATE"} else "MEDIUM",
            })

    cumulative: set[str] = set()
    total_universe = sum(len(v) for v in rows_by_tier.values())
    for day in range(1, 6):
        day_tickers: set[str] = set()
        for row in plan_rows:
            scan_day = str(row["recommended_scan_day"])
            if scan_day == "EVERY_DAY" or scan_day == f"DAY_{day}":
                day_tickers.add(str(row["ticker"]))
        cumulative |= day_tickers
        counts = per_day_counts[day]
        planned_total = sum(counts.values())
        five_day_rows.append({
            "plan_day": f"DAY_{day}",
            "planned_total_scan_count": planned_total,
            "core_daily_count": counts["CORE_DAILY"],
            "candidate_count": counts["CANDIDATE"],
            "strong_watch_count": counts["STRONG_WATCH"],
            "watchlist_count": counts["WATCHLIST"],
            "research_count": counts["RESEARCH"],
            "cumulative_expected_coverage": len(cumulative),
            "expected_uncovered_remaining": max(0, total_universe - len(cumulative)),
            "meets_target": bool_text(planned_total >= math.ceil(total_universe / COVERAGE_WINDOW_TRADING_DAYS)),
            "notes": "Meets current daily scan-count threshold; full unique coverage remains constrained by repeated high-tier scans." if planned_total >= daily_target else "Below current daily scan-count threshold.",
        })
    return plan_rows, five_day_rows


def add_audit(rows: List[Dict[str, object]], metric: str, current: object, recommended: object, status: str, reason: str, source: Path, confidence: str) -> None:
    rows.append({
        "metric": metric,
        "current_value": current,
        "recommended_value": recommended,
        "status": status,
        "reason": reason,
        "source_file": str(source),
        "confidence": confidence,
    })


def build(root: Path) -> int:
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    universe = root / "outputs/v18/universe"
    ensure_dir(ops)
    ensure_dir(universe)

    state_path = root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv"
    run_state_path = root / "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json"
    coverage_path = universe / "V18_16H_CURRENT_COVERAGE_AUDIT.csv"
    v16h_report_path = universe / "V18_16H_CURRENT_ROLLING_SCAN_COVERAGE_REPORT.md"
    v16h_read = ops / "V18_16H_READ_FIRST.txt"
    v16f_read = ops / "V18_16F_READ_FIRST.txt"
    v16b_read = ops / "V18_16B_READ_FIRST.txt"
    scan_result_path = universe / "V18_CURRENT_PRIORITY_LIGHT_SCAN_RESULT.csv"
    promotion_path = universe / "V18_CURRENT_PROMOTION_DEMOTION_AUDIT.csv"
    daily_brief_path = root / "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md"
    v19a_read = ops / "V18_19A_READ_FIRST.txt"
    v19a_audit = ops / "V18_19A_DAILY_READABILITY_AUDIT.csv"
    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    new_script = root / "scripts/v18/v18_16I_rolling_scan_coverage_policy_optimizer.py"
    new_wrapper = root / "scripts/v18/run_v18_16I_rolling_scan_coverage_policy_optimizer.ps1"

    protected_paths = [
        state_path,
        run_state_path,
        current_daily,
        promotion_path,
        scan_result_path,
    ]
    before_hashes = file_hashes(protected_paths)

    state_rows, _, state_status = read_csv(state_path)
    coverage_rows, _, coverage_status = read_csv(coverage_path)
    scan_rows, _, scan_status = read_csv(scan_result_path)
    promotion_rows, _, promotion_status = read_csv(promotion_path)
    run_state = read_json(run_state_path)

    total_universe = len([r for r in state_rows if str(r.get("ticker", "")).strip()])
    coverage = coverage_rows[0] if coverage_rows else {}
    daily_min = to_int(coverage.get("DAILY_MIN_SCAN_COUNT")) or math.ceil(total_universe / COVERAGE_WINDOW_TRADING_DAYS)
    today_scan = to_int(coverage.get("TODAY_ROLLING_SCAN_COUNT")) or to_int(first_value(v16f_read, "TODAY_ROLLING_SCAN_COUNT")) or to_int(run_state.get("last_today_scan_count"))
    coverage_target_met = str(coverage.get("COVERAGE_TARGET_MET", "")).upper() == "TRUE"
    coverage_shortfall = to_int(coverage.get("COVERAGE_SHORTFALL_COUNT"), max(0, daily_min - today_scan))
    scanned_last_5d = to_int(coverage.get("SCANNED_LAST_5D_COUNT"))
    scan_limit_reason = coverage.get("SCAN_LIMIT_REASON") or first_value(v16h_read, "SCAN_LIMIT_REASON") or "UNKNOWN"

    tiers = Counter(tier_of(row) for row in state_rows if str(row.get("ticker", "")).strip())
    rows_by_tier: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in state_rows:
        if str(row.get("ticker", "")).strip():
            rows_by_tier[tier_of(row)].append(row)

    selected_counts = selected_counts_by_tier(read_csv(root / "outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_PLAN.csv")[0])
    runtime_conf, runtime_reason = runtime_confidence(v16f_read)
    max_cost = to_int(first_value(v16b_read, "MAX_ESTIMATED_PLAN_COST"))
    current_cost = to_int(first_value(v16b_read, "ESTIMATED_PLAN_COST"))
    actual_runtime = to_float(first_value(v16f_read, "ACTUAL_RUNTIME_SECONDS"))

    tier_weighted_full = sum(math.ceil(tiers.get(tier, 0) / TIER_INTERVAL_DAYS[tier]) for tier in TIER_ORDER)
    recommended_daily = max(daily_min, today_scan)
    recommended_quotas = allocate_quota(recommended_daily, dict(tiers))
    projected_daily_threshold_shortfall = max(0, daily_min - sum(recommended_quotas.values()))
    projected_daily_threshold_met = projected_daily_threshold_shortfall == 0
    unique_5day_expected = 0
    unique_5day_shortfall = total_universe

    current_frequency = {}
    for tier in TIER_ORDER:
        count = tiers.get(tier, 0)
        selected = selected_counts.get(tier, 0)
        current_frequency[tier] = "NONE_SELECTED" if selected == 0 else f"{selected}/{count}_SELECTED_THIS_RUN"

    today = dt.date.today()
    recommended_plan, five_day_plan = build_rotation(rows_by_tier, recommended_quotas, recommended_daily, today)
    if five_day_plan:
        unique_5day_expected = to_int(five_day_plan[-1].get("cumulative_expected_coverage"))
        unique_5day_shortfall = to_int(five_day_plan[-1].get("expected_uncovered_remaining"))

    scheduled_unique_by_tier = Counter()
    day1_counts = Counter()
    if five_day_plan:
        first = five_day_plan[0]
        day1_counts.update({
            "CORE_DAILY": to_int(first.get("core_daily_count")),
            "CANDIDATE": to_int(first.get("candidate_count")),
            "STRONG_WATCH": to_int(first.get("strong_watch_count")),
            "WATCHLIST": to_int(first.get("watchlist_count")),
            "RESEARCH": to_int(first.get("research_count")),
        })
    for row in recommended_plan:
        if str(row.get("recommended_scan_day")) != "UNSCHEDULED_REQUIRES_POLICY_REVIEW":
            scheduled_unique_by_tier[str(row.get("tier"))] += 1

    tier_rows: List[Dict[str, object]] = []
    for tier in TIER_ORDER:
        count = tiers.get(tier, 0)
        quota = day1_counts.get(tier, recommended_quotas.get(tier, 0))
        constrained = tier not in {"CORE_DAILY", "CANDIDATE"} and scheduled_unique_by_tier.get(tier, 0) < count
        tier_rows.append({
            "tier": tier,
            "current_count": count,
            "current_scan_frequency": current_frequency.get(tier, "UNKNOWN"),
            "recommended_scan_frequency": TIER_TARGET_FREQUENCY[tier],
            "recommended_daily_quota": quota,
            "five_day_target_count": scheduled_unique_by_tier.get(tier, 0),
            "reason": "High-trust tier receives daily coverage." if tier in {"CORE_DAILY", "CANDIDATE"} else ("Constrained rotation after high-trust daily tiers; full tier target needs higher capacity." if constrained else "Rotated after high-trust daily tiers to reduce permanent staleness."),
            "confidence": "HIGH" if count > 0 and not constrained else "MEDIUM",
        })

    audit_rows: List[Dict[str, object]] = []
    add_audit(audit_rows, "total_universe_count", total_universe, total_universe, "INFO", "Universe size read from rolling state.", state_path, "HIGH" if state_status == "OK" else "LOW")
    add_audit(audit_rows, "current_daily_scan_count", today_scan, recommended_daily, "IMPROVE", "Current scan count is below the daily 5-day coverage threshold.", coverage_path, "HIGH" if coverage_status == "OK" else "MEDIUM")
    add_audit(audit_rows, "required_daily_scan_count", daily_min, daily_min, "INFO", "ceil(total universe / 5 trading days).", coverage_path, "HIGH")
    add_audit(audit_rows, "tier_weighted_full_coverage_daily_count", today_scan, tier_weighted_full, "REVIEW_REQUIRED", "Full tier-aware unique coverage requires higher daily capacity because CORE/CANDIDATE repeat.", state_path, "MEDIUM")
    add_audit(audit_rows, "recommended_daily_scan_count", today_scan, recommended_daily, "ADVISORY_ONLY", "Closest next-step target to satisfy current daily trust threshold; no policy applied.", coverage_path, "MEDIUM")
    add_audit(audit_rows, "projected_daily_threshold_met", bool_text(coverage_target_met), bool_text(projected_daily_threshold_met), "IMPROVE" if projected_daily_threshold_met and not coverage_target_met else "INFO", "Daily threshold only; this does not imply full unique five-day universe coverage.", coverage_path, "MEDIUM")
    add_audit(audit_rows, "projected_daily_threshold_shortfall_after", coverage_shortfall, projected_daily_threshold_shortfall, "IMPROVE", "Daily threshold shortfall closes if future policy reaches recommended daily quota.", coverage_path, "MEDIUM")
    add_audit(audit_rows, "projected_true_5day_unique_coverage_met", "FALSE", bool_text(unique_5day_shortfall == 0), "REVIEW_REQUIRED", f"True unique five-day coverage remains insufficient under the {recommended_daily}/day advisory plan.", state_path, "MEDIUM")
    add_audit(audit_rows, "projected_true_5day_unique_coverage_count", scanned_last_5d, unique_5day_expected, "PARTIAL_IMPROVE", "Daily threshold can improve while full unique tier coverage remains short.", state_path, "MEDIUM")
    add_audit(audit_rows, "projected_true_5day_unique_shortfall_count", max(0, total_universe - scanned_last_5d), unique_5day_shortfall, "REVIEW_REQUIRED", "Full unique coverage likely needs a separate budget/runtime policy decision.", state_path, "MEDIUM")
    add_audit(audit_rows, "projected_coverage_target_met_legacy_daily_threshold", bool_text(coverage_target_met), bool_text(projected_daily_threshold_met), "LEGACY_DAILY_THRESHOLD_ONLY", "Backward-compatible daily-threshold metric; not true full coverage.", coverage_path, "MEDIUM")
    add_audit(audit_rows, "scan_limit_reason", scan_limit_reason, "REVIEW_COST_LIMIT_BEFORE_APPLY", "REVIEW_REQUIRED", "Existing scheduler reported cost limit pressure.", v16b_read, "HIGH")
    add_audit(audit_rows, "runtime_confidence", runtime_conf, runtime_conf, "INFO", runtime_reason, v16f_read, runtime_conf)
    add_audit(audit_rows, "estimated_plan_cost", current_cost, "NEEDS_RECALC_IN_APPLY_DESIGN", "REVIEW_REQUIRED" if max_cost and current_cost > max_cost else "INFO", f"MAX_ESTIMATED_PLAN_COST={max_cost}; current scheduler estimate={current_cost}.", v16b_read, "HIGH" if max_cost else "LOW")
    add_audit(audit_rows, "daily_trust_degrader", "coverage_shortfall_active", "daily_threshold_reduced_but_keep_warn_until_true_unique_coverage_improves", "ADVISORY_ONLY", "V18.19A trust logic was not modified and should not infer HIGH trust solely from daily-threshold coverage.", v19a_read, "MEDIUM")
    add_audit(audit_rows, "policy_applied", "FALSE", "FALSE", "PASS", "Dry-run optimizer only.", new_script, "HIGH")
    add_audit(audit_rows, "state_modified", "FALSE", "FALSE", "PASS", "State hashes are checked after output generation.", state_path, "HIGH")

    output_policy = universe / "V18_16I_CURRENT_COVERAGE_POLICY_AUDIT.csv"
    output_tiers = universe / "V18_16I_CURRENT_TIER_SCAN_REQUIREMENTS.csv"
    output_plan = universe / "V18_16I_CURRENT_RECOMMENDED_SCAN_PLAN.csv"
    output_5day = universe / "V18_16I_CURRENT_5DAY_COVERAGE_PLAN.csv"
    output_report = universe / "V18_16I_CURRENT_POLICY_OPTIMIZER_REPORT.md"
    read_first_path = ops / "V18_16I_READ_FIRST.txt"

    write_csv(output_policy, audit_rows, AUDIT_FIELDS)
    write_csv(output_tiers, tier_rows, TIER_FIELDS)
    write_csv(output_plan, recommended_plan, PLAN_FIELDS)
    write_csv(output_5day, five_day_plan, FIVE_DAY_FIELDS)

    after_hashes = file_hashes(protected_paths)
    state_modified = before_hashes.get(str(state_path.resolve())) != after_hashes.get(str(state_path.resolve()))
    current_daily_modified = before_hashes.get(str(current_daily.resolve())) != after_hashes.get(str(current_daily.resolve()))
    promotion_modified = before_hashes.get(str(promotion_path.resolve())) != after_hashes.get(str(promotion_path.resolve()))
    scan_result_modified = before_hashes.get(str(scan_result_path.resolve())) != after_hashes.get(str(scan_result_path.resolve()))
    price_update_modified = False
    ranking_modified = False
    policy_applied = False

    validations = [
        ("ROLLING_STATE_INPUT_OK", state_status == "OK", state_status),
        ("COVERAGE_INPUT_OK", coverage_status == "OK", coverage_status),
        ("SCAN_RESULT_INPUT_OK", scan_status == "OK", scan_status),
        ("PROMOTION_INPUT_OK", promotion_status == "OK", promotion_status),
        ("OUTPUT_POLICY_AUDIT_EXISTS", output_policy.exists(), str(output_policy)),
        ("OUTPUT_TIER_REQUIREMENTS_EXISTS", output_tiers.exists(), str(output_tiers)),
        ("OUTPUT_RECOMMENDED_PLAN_EXISTS", output_plan.exists(), str(output_plan)),
        ("OUTPUT_5DAY_PLAN_EXISTS", output_5day.exists(), str(output_5day)),
        ("TOTAL_UNIVERSE_GT_ZERO", total_universe > 0, str(total_universe)),
        ("POLICY_APPLIED_FALSE", not policy_applied, ""),
        ("STATE_NOT_MODIFIED", not state_modified, ""),
        ("CURRENT_DAILY_NOT_MODIFIED", not current_daily_modified, ""),
        ("PROMOTION_DEMOTION_NOT_MODIFIED", not promotion_modified, ""),
        ("RANKING_NOT_MODIFIED", not ranking_modified, ""),
        ("PRICE_UPDATE_NOT_MODIFIED", not price_update_modified, ""),
        ("AUTO_TRADE_DISABLED", AUTO_TRADE == "DISABLED", AUTO_TRADE),
        ("AUTO_SELL_DISABLED", AUTO_SELL == "DISABLED", AUTO_SELL),
        ("OFFICIAL_DECISION_IMPACT_NONE", OFFICIAL_DECISION_IMPACT == "NONE", OFFICIAL_DECISION_IMPACT),
        ("PYTHON_PARSE_SELF", parse_py(new_script)[0], parse_py(new_script)[1]),
    ]
    validation_fail_count = sum(1 for _, ok, _ in validations if not ok)

    status = STATUS_OK if validation_fail_count == 0 else STATUS_WARN
    read_first_lines = [
        f"STATUS: {status}",
        f"MODE: {MODE}",
        f"TOTAL_UNIVERSE_COUNT: {total_universe}",
        f"CURRENT_DAILY_SCAN_COUNT: {today_scan}",
        f"REQUIRED_DAILY_SCAN_COUNT: {daily_min}",
        f"RECOMMENDED_DAILY_SCAN_COUNT: {recommended_daily}",
        f"TIER_WEIGHTED_FULL_COVERAGE_DAILY_COUNT: {tier_weighted_full}",
        f"CURRENT_COVERAGE_TARGET_MET: {bool_text(coverage_target_met)}",
        f"PROJECTED_DAILY_THRESHOLD_MET: {bool_text(projected_daily_threshold_met)}",
        f"PROJECTED_DAILY_THRESHOLD_SHORTFALL_AFTER: {projected_daily_threshold_shortfall}",
        f"PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_MET: {bool_text(unique_5day_shortfall == 0)}",
        f"PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_COUNT: {unique_5day_expected}",
        f"PROJECTED_TRUE_5DAY_UNIQUE_SHORTFALL_COUNT: {unique_5day_shortfall}",
        f"PROJECTED_COVERAGE_TARGET_MET_LEGACY_DAILY_THRESHOLD: {bool_text(projected_daily_threshold_met)}",
        f"COVERAGE_SHORTFALL_BEFORE: {coverage_shortfall}",
        f"SCAN_LIMIT_REASON: {scan_limit_reason}",
        f"RUNTIME_CONFIDENCE: {runtime_conf}",
        f"POLICY_APPLIED: {bool_text(policy_applied)}",
        f"STATE_MODIFIED: {bool_text(state_modified)}",
        f"CURRENT_DAILY_MODIFIED: {bool_text(current_daily_modified)}",
        f"PROMOTION_DEMOTION_MODIFIED: {bool_text(promotion_modified)}",
        f"RANKING_MODIFIED: {bool_text(ranking_modified)}",
        f"PRICE_UPDATE_MODIFIED: {bool_text(price_update_modified)}",
        f"AUTO_TRADE: {AUTO_TRADE}",
        f"AUTO_SELL: {AUTO_SELL}",
        f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"VALIDATION_FAIL_COUNT: {validation_fail_count}",
        f"READ_FIRST: {read_first_path}",
        f"REPORT: {output_report}",
    ]
    write_text(read_first_path, "\n".join(read_first_lines) + "\n")

    quota_by_tier = {str(row["tier"]): row["recommended_daily_quota"] for row in tier_rows}
    quota_text = ", ".join(f"{tier}={quota_by_tier.get(tier, 0)}" for tier in TIER_ORDER)
    report_lines = [
        "# V18.16I Rolling Scan Coverage Policy Optimizer",
        "",
        f"- STATUS: {status}",
        f"- MODE: {MODE}",
        f"- TOTAL_UNIVERSE_COUNT: {total_universe}",
        f"- CURRENT_DAILY_SCAN_COUNT: {today_scan}",
        f"- REQUIRED_DAILY_SCAN_COUNT: {daily_min}",
        f"- RECOMMENDED_DAILY_SCAN_COUNT: {recommended_daily}",
        f"- TIER_WEIGHTED_FULL_COVERAGE_DAILY_COUNT: {tier_weighted_full}",
        f"- CURRENT_COVERAGE_TARGET_MET: {bool_text(coverage_target_met)}",
        f"- PROJECTED_DAILY_THRESHOLD_MET: {bool_text(projected_daily_threshold_met)}",
        f"- PROJECTED_DAILY_THRESHOLD_SHORTFALL_AFTER: {projected_daily_threshold_shortfall}",
        f"- PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_MET: {bool_text(unique_5day_shortfall == 0)}",
        f"- PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_COUNT: {unique_5day_expected}",
        f"- PROJECTED_TRUE_5DAY_UNIQUE_SHORTFALL_COUNT: {unique_5day_shortfall}",
        f"- PROJECTED_COVERAGE_TARGET_MET_LEGACY_DAILY_THRESHOLD: {bool_text(projected_daily_threshold_met)}",
        f"- COVERAGE_SHORTFALL_BEFORE: {coverage_shortfall}",
        f"- RECOMMENDED_QUOTAS: {quota_text}",
        f"- POLICY_APPLIED: {bool_text(policy_applied)}",
        f"- VALIDATION_FAIL_COUNT: {validation_fail_count}",
        "",
        "## Current Problem Summary",
        "",
        f"The current rolling scan count is {today_scan}, below the existing {daily_min} per-day threshold derived from {total_universe} names over {COVERAGE_WINDOW_TRADING_DAYS} trading days. The recent shortfall is {coverage_shortfall}, with scan limit reason `{scan_limit_reason}`.",
        "",
        "## Tier Breakdown",
        "",
        "| tier | count | current selected | recommended quota | recommended frequency |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for tier in TIER_ORDER:
        report_lines.append(f"| {tier} | {tiers.get(tier, 0)} | {selected_counts.get(tier, 0)} | {quota_by_tier.get(tier, 0)} | {TIER_TARGET_FREQUENCY[tier]} |")
    report_lines.extend([
        "",
        "## Proposed Policy",
        "",
        f"The advisory next-step policy targets {recommended_daily} scans/day to close the current daily-threshold shortfall while preserving daily CORE_DAILY and CANDIDATE coverage first. This is not a true full-universe coverage fix. A stricter tier-aware full-coverage policy estimates {tier_weighted_full} scans/day, which should be reviewed separately because it may exceed current estimated cost limits.",
        "",
        "## 5-Day Plan",
        "",
        "| day | total | core | candidate | strong | watchlist | research | cumulative unique | remaining | target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ])
    for row in five_day_plan:
        report_lines.append(
            f"| {row['plan_day']} | {row['planned_total_scan_count']} | {row['core_daily_count']} | {row['candidate_count']} | {row['strong_watch_count']} | {row['watchlist_count']} | {row['research_count']} | {row['cumulative_expected_coverage']} | {row['expected_uncovered_remaining']} | {row['meets_target']} |"
        )
    report_lines.extend([
        "",
        "## Expected Improvement",
        "",
        f"- PROJECTED_DAILY_THRESHOLD_MET would likely move from {bool_text(coverage_target_met)} to {bool_text(projected_daily_threshold_met)} if a future scheduler policy can safely run the recommended quota.",
        f"- PROJECTED_DAILY_THRESHOLD_SHORTFALL_AFTER would move from {coverage_shortfall} to {projected_daily_threshold_shortfall}.",
        f"- PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_MET remains {bool_text(unique_5day_shortfall == 0)} with {unique_5day_expected}/{total_universe} unique names covered and {unique_5day_shortfall} uncovered.",
        f"- Daily threshold blocker may be reduced if {recommended_daily}/day is applied, but coverage trust should remain WARN/degraded until true five-day unique coverage improves.",
        "- V18.19A should not infer HIGH trust solely from daily-threshold coverage.",
        "",
        "## Risks / Unknowns",
        "",
        f"- Runtime confidence: {runtime_conf}. {runtime_reason}",
        f"- Estimated cost confidence: {'HIGH' if max_cost else 'LOW'}. Current scheduler estimate is {current_cost} against max {max_cost}.",
        "- True full unique five-day coverage remains constrained by high-tier daily repeats unless cost/runtime policy is revised.",
        "",
        "## Future APPLY Requirements",
        "",
        "- V18.16J may address the conservative daily threshold gap.",
        "- V18.16K is required for true five-day unique coverage scheduling.",
        "- Update the scheduler policy explicitly if adopting the recommended quota.",
        "- Recalculate estimated plan cost before applying any higher scan count.",
        "- Keep yfinance disabled unless a separate approved task changes provider behavior.",
        "- Re-run V18.19A and V18.20K verification after any future policy apply.",
        "",
        "## Dryrun Statement",
        "",
        "No rolling scan policy was applied. No state file, current daily command center, promotion/demotion engine, ranking output, price update behavior, yfinance behavior, auto trading, auto selling, or official decision logic was modified.",
        "",
        "## Validation",
        "",
    ])
    for name, ok, note in validations:
        report_lines.append(f"- {name}: {'PASS' if ok else 'FAIL'} {note}")
    write_text(output_report, "\n".join(report_lines) + "\n")

    for key, value in [
        ("STATUS", status),
        ("MODE", MODE),
        ("TOTAL_UNIVERSE_COUNT", total_universe),
        ("CURRENT_DAILY_SCAN_COUNT", today_scan),
        ("REQUIRED_DAILY_SCAN_COUNT", daily_min),
        ("RECOMMENDED_DAILY_SCAN_COUNT", recommended_daily),
        ("CURRENT_COVERAGE_TARGET_MET", bool_text(coverage_target_met)),
        ("PROJECTED_DAILY_THRESHOLD_MET", bool_text(projected_daily_threshold_met)),
        ("PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_MET", bool_text(unique_5day_shortfall == 0)),
        ("PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_COUNT", unique_5day_expected),
        ("PROJECTED_TRUE_5DAY_UNIQUE_SHORTFALL_COUNT", unique_5day_shortfall),
        ("OFFICIAL_DECISION_IMPACT", OFFICIAL_DECISION_IMPACT),
        ("AUTO_TRADE", AUTO_TRADE),
        ("AUTO_SELL", AUTO_SELL),
        ("POLICY_APPLIED", bool_text(policy_applied)),
        ("STATE_MODIFIED", bool_text(state_modified)),
        ("CURRENT_DAILY_MODIFIED", bool_text(current_daily_modified)),
        ("VALIDATION_FAIL_COUNT", validation_fail_count),
        ("READ_FIRST", read_first_path),
        ("REPORT", output_report),
    ]:
        print(f"{key}: {value}")
    return 0 if validation_fail_count == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.16I rolling scan coverage policy optimizer dryrun")
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
