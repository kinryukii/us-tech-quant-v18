from __future__ import annotations

import argparse
import csv
import datetime as dt
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_28C_RECOMMENDATION_TIER_CALIBRATION_READY"
STATUS_WARN = "WARN_V18_28C_RECOMMENDATION_TIER_CALIBRATION_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_28C_RECOMMENDATION_TIER_CALIBRATION_ERROR"
MODE = "READ_ONLY_RECOMMENDATION_TIER_CALIBRATION_AUDIT"

CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
THEME_CLASSIFICATION = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
TECHNICAL_TIMING = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"

OUT_CSV = "outputs/v18/recommendations/V18_28C_RECOMMENDATION_TIER_CALIBRATION_AUDIT.csv"
OUT_REPORT = "outputs/v18/read_center/V18_28C_RECOMMENDATION_TIER_CALIBRATION_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_28C_READ_FIRST.txt"

PROTECTED_FILES = [
    CURRENT_CANDIDATES,
    THEME_CLASSIFICATION,
    RECOMMENDATIONS,
    TECHNICAL_TIMING,
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv",
]
PROTECTED_DIRS = [
    "state/v18/price_cache",
    "state/v18/trading",
    "outputs/v18/official_daily",
]

OUTPUT_FIELDS = [
    "ticker",
    "rank",
    "composite_candidate_score",
    "primary_theme",
    "theme_rank",
    "role_bucket",
    "volatility_bucket",
    "technical_timing_score",
    "overheat_penalty",
    "recommendation_tier",
    "recommendation_action",
    "risk_label",
    "reason_codes",
    "audit_flag",
    "audit_comment",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "INPUT_RECOMMENDATION_ROW_COUNT",
    "CURRENT_RANKED_CANDIDATE_ROW_COUNT",
    "MISSING_RECOMMENDATION_TIER_COUNT",
    "MISSING_RECOMMENDATION_ACTION_COUNT",
    "UNKNOWN_PRIMARY_THEME_COUNT",
    "DUPLICATE_TICKER_COUNT",
    "CORE_CANDIDATE_COUNT",
    "WATCHLIST_STRONG_COUNT",
    "TACTICAL_ENTRY_COUNT",
    "OVERHEATED_WAIT_COUNT",
    "SPECULATIVE_SATELLITE_COUNT",
    "DEFENSIVE_HEDGE_COUNT",
    "ETF_OR_MACRO_EXPOSURE_COUNT",
    "DO_NOT_PRIORITIZE_COUNT",
    "TOP_30_SPECULATIVE_SATELLITE_COUNT",
    "TOP_30_OVERHEATED_WAIT_COUNT",
    "TOP_30_CORE_CANDIDATE_COUNT",
    "POSSIBLE_CORE_REVIEW_COUNT",
    "POSSIBLE_WATCHLIST_REVIEW_COUNT",
    "OVERHEAT_RULE_REVIEW_COUNT",
    "VOLATILITY_RULE_REVIEW_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "FORBIDDEN_MODIFIED",
]


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
        except Exception:
            continue
    raise RuntimeError(f"Unable to read CSV: {path}")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def norm(value: object) -> str:
    return str(value or "").strip()


def ticker(value: object) -> str:
    return norm(value).upper()


def to_int(value: object, default: int = 0) -> int:
    try:
        text = norm(value)
        return int(float(text)) if text else default
    except Exception:
        return default


def to_float(value: object, default: float = 0.0) -> float:
    try:
        text = norm(value)
        return float(text) if text else default
    except Exception:
        return default


def bool_true(value: object) -> bool:
    return norm(value).upper() in {"TRUE", "T", "YES", "Y", "1"}


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def protected_sig(root: Path) -> Dict[str, object]:
    sig: Dict[str, object] = {}
    for rel in PROTECTED_FILES:
        sig[rel] = file_sig(root / rel)
    for rel in PROTECTED_DIRS:
        sig[rel] = tree_sig(root / rel)
    return sig


def build_lookup(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}
    for row in rows:
        t = ticker(row.get("ticker"))
        if t and t not in lookup:
            lookup[t] = row
    return lookup


def duplicate_ticker_count(rows: Sequence[Dict[str, str]]) -> int:
    counts = Counter(ticker(row.get("ticker")) for row in rows if ticker(row.get("ticker")))
    return sum(1 for count in counts.values() if count > 1)


def tier_for_top(row: Dict[str, object], top_n: int) -> bool:
    return to_int(row.get("rank"), 999999) <= top_n


def technical_overheat_evidence(row: Dict[str, object]) -> Tuple[bool, str]:
    overheat_penalty = to_float(row.get("overheat_penalty"))
    signal = norm(row.get("technical_signal")).upper()
    warning = norm(row.get("technical_warning_label")).upper()
    bb_status = norm(row.get("bb_status")).upper()
    rsi_status = norm(row.get("rsi_status")).upper()
    kdj_status = norm(row.get("kdj_status")).upper()
    reason_codes = {token for token in norm(row.get("reason_codes")).split(";") if token}

    if "STRONG_TECHNICAL_OVERHEAT" in reason_codes:
        return True, "Strong technical overheat reason code present."
    strong_markers = [
        token
        for token in [signal, warning, bb_status, rsi_status, kdj_status]
        if any(x in token for x in ["EXTREME_OVERHEAT", "BREAKOUT_OVERHEAT", "ABOVE_UPPER"])
    ]
    if overheat_penalty > 0 or strong_markers:
        return True, "Strong technical overheat evidence present."
    if any(x in token for token in [signal, warning, bb_status, rsi_status, kdj_status] for x in ["STAGED_R25B_NOT_MERGED", "NONE"]):
        return False, "Overheat wait appears weakly supported by staging / non-overheat labels."
    return False, "No strong technical overheat evidence found; wait signal likely inferred."


def current_top_distribution(rows: Sequence[Dict[str, object]], top_n: int) -> Dict[str, int]:
    subset = [row for row in rows if tier_for_top(row, top_n)]
    return Counter(norm(row.get("recommendation_tier")) for row in subset)


def grouped_tier_counts(rows: Sequence[Dict[str, object]], group_field: str) -> List[Dict[str, object]]:
    grouped: Dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        key = norm(row.get(group_field)) or "BLANK"
        grouped[key][norm(row.get("recommendation_tier")) or "BLANK"] += 1
    out = []
    for group in sorted(grouped):
        entry = {"group": group}
        entry.update(grouped[group])
        out.append(entry)
    return out


def make_flag(row: Dict[str, object]) -> Tuple[str, str]:
    rank = to_int(row.get("rank"), 999999)
    theme_rank = to_int(row.get("theme_rank"), 999999)
    tier = norm(row.get("recommendation_tier")).upper()
    role = norm(row.get("role_bucket")).upper()
    vol = norm(row.get("volatility_bucket")).upper()
    reason_codes = {token for token in norm(row.get("reason_codes")).split(";") if token}
    overheat_evidence, overheat_comment = technical_overheat_evidence(row)

    flags: List[str] = []
    comments: List[str] = []

    has_strong_overheat = "TECHNICAL_OVERHEAT" in reason_codes or "STRONG_TECHNICAL_OVERHEAT" in reason_codes

    if rank <= 30 and role in {"CORE_GROWTH", "CYCLICAL_GROWTH"} and vol == "HIGH" and vol != "EXTREME" and not has_strong_overheat and tier != "CORE_CANDIDATE":
        flags.append("POSSIBLE_CORE_REVIEW")
        comments.append("High-priority growth name remains below CORE_CANDIDATE despite acceptable high-volatility profile.")

    if (rank <= 75 or theme_rank <= 3) and tier == "SPECULATIVE_SATELLITE" and vol == "HIGH" and vol != "EXTREME" and not has_strong_overheat:
        flags.append("POSSIBLE_WATCHLIST_REVIEW")
        comments.append("Top-ranked / top-theme candidate is speculative despite only high volatility and no technical overheat flag.")

    if tier == "OVERHEATED_WAIT" and (not overheat_evidence or (vol in {"HIGH", "EXTREME"} and not has_strong_overheat)):
        flags.append("OVERHEAT_RULE_REVIEW")
        comments.append(overheat_comment)

    if tier == "SPECULATIVE_SATELLITE" and vol == "HIGH" and rank <= 30 and ({"HIGH_VOLATILITY"} <= reason_codes or reason_codes == {"TOP_30_RANK", "TOP_75_RANK", "TOP_3_THEME_RANK", "HIGH_VOLATILITY"} or not has_strong_overheat):
        flags.append("VOLATILITY_RULE_REVIEW")
        comments.append("Only high-volatility downgrade is visible in the current reason set for a top-ranked candidate.")

    if not flags:
        return "NONE", ""
    return ";".join(flags), " ".join(comments)


def audit_comment(row: Dict[str, object], audit_flag: str, audit_comment: str) -> str:
    if audit_flag == "NONE":
        return "No calibration issue identified under current audit rules."
    tier = norm(row.get("recommendation_tier"))
    rank = norm(row.get("rank"))
    theme = norm(row.get("primary_theme"))
    vol = norm(row.get("volatility_bucket"))
    return f"{audit_flag}: rank {rank}, tier {tier}, theme {theme}, volatility {vol}. {audit_comment}".strip()


def sort_key(row: Dict[str, object]) -> Tuple[int, int, str]:
    return (to_int(row.get("rank"), 999999), 0, ticker(row.get("ticker")))


def table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: int = 30) -> str:
    selected = list(rows[:limit])
    if not selected:
        return "_None._"
    header = "| " + " | ".join(fields) + " |"
    sep = "| " + " | ".join(["---"] * len(fields)) + " |"
    body = ["| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |" for row in selected]
    return "\n".join([header, sep] + body)


def count_rows(rows: Sequence[Dict[str, object]], field: str) -> List[Dict[str, object]]:
    counts = Counter(norm(row.get(field)) or "BLANK" for row in rows)
    return [{"key": key, "count": count} for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def distribution_table(rows: Sequence[Dict[str, object]], top_n: int) -> List[Dict[str, object]]:
    subset = [row for row in rows if to_int(row.get("rank"), 999999) <= top_n]
    counts = Counter(norm(row.get("recommendation_tier")) or "BLANK" for row in subset)
    return [{"tier": tier, "count": count} for tier, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def top_candidate_flags(rows: Sequence[Dict[str, object]], tier: str) -> List[Dict[str, object]]:
    return [row for row in rows if norm(row.get("recommendation_tier")).upper() == tier]


def tier_by_primary_theme(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        theme = norm(row.get("primary_theme")) or "BLANK"
        grouped[theme][norm(row.get("recommendation_tier")) or "BLANK"] += 1
    out = []
    for theme in sorted(grouped):
        item = {"primary_theme": theme}
        item.update(grouped[theme])
        out.append(item)
    return out


def summarize_theme_primary(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[norm(row.get("primary_theme"))].append(row)
    out = []
    for theme in sorted(grouped):
        theme_rows = grouped[theme]
        tiers = Counter(norm(row.get("recommendation_tier")) for row in theme_rows)
        out.append(
            {
                "primary_theme": theme,
                "candidate_count": len(theme_rows),
                "core_count": tiers.get("CORE_CANDIDATE", 0),
                "watchlist_count": tiers.get("WATCHLIST_STRONG", 0),
                "speculative_count": tiers.get("SPECULATIVE_SATELLITE", 0),
                "do_not_prioritize_count": tiers.get("DO_NOT_PRIORITIZE", 0),
            }
        )
    return sorted(out, key=lambda row: (-int(row["candidate_count"]), row["primary_theme"]))


def candidate_rows_for_review(rows: Sequence[Dict[str, object]], flag: str) -> List[Dict[str, object]]:
    return [row for row in rows if flag in norm(row.get("audit_flag")).split(";")]


def build_report(values: Dict[str, object], rows: Sequence[Dict[str, object]]) -> str:
    flags = {
        "POSSIBLE_CORE_REVIEW": candidate_rows_for_review(rows, "POSSIBLE_CORE_REVIEW"),
        "POSSIBLE_WATCHLIST_REVIEW": candidate_rows_for_review(rows, "POSSIBLE_WATCHLIST_REVIEW"),
        "OVERHEAT_RULE_REVIEW": candidate_rows_for_review(rows, "OVERHEAT_RULE_REVIEW"),
        "VOLATILITY_RULE_REVIEW": candidate_rows_for_review(rows, "VOLATILITY_RULE_REVIEW"),
    }
    all_flags = [row for row in rows if norm(row.get("audit_flag")) != "NONE"]

    lines = [
        "# V18.28C Recommendation Tier Calibration Audit",
        "",
        "## Read First",
        "",
    ]
    lines.extend([f"- {field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS])
    lines.extend(
        [
            "",
            "## Current Recommendation Tier Counts",
            "",
            table(count_rows(rows, "recommendation_tier"), ["key", "count"], 20),
            "",
            "## Top 30 Tier Distribution",
            "",
            table(distribution_table(rows, 30), ["tier", "count"], 20),
            "",
            "## Top 75 Tier Distribution",
            "",
            table(distribution_table(rows, 75), ["tier", "count"], 20),
            "",
            "## Tier by Primary Theme",
            "",
            table(tier_by_primary_theme(rows), ["primary_theme", "CORE_CANDIDATE", "WATCHLIST_STRONG", "TACTICAL_ENTRY", "OVERHEATED_WAIT", "SPECULATIVE_SATELLITE", "DEFENSIVE_HEDGE", "ETF_OR_MACRO_EXPOSURE", "DO_NOT_PRIORITIZE"], 40),
            "",
            "## Tier by Volatility Bucket",
            "",
            table(grouped_tier_counts(rows, "volatility_bucket"), ["group", "CORE_CANDIDATE", "WATCHLIST_STRONG", "TACTICAL_ENTRY", "OVERHEATED_WAIT", "SPECULATIVE_SATELLITE", "DEFENSIVE_HEDGE", "ETF_OR_MACRO_EXPOSURE", "DO_NOT_PRIORITIZE"], 20),
            "",
            "## Tier by Role Bucket",
            "",
            table(grouped_tier_counts(rows, "role_bucket"), ["group", "CORE_CANDIDATE", "WATCHLIST_STRONG", "TACTICAL_ENTRY", "OVERHEATED_WAIT", "SPECULATIVE_SATELLITE", "DEFENSIVE_HEDGE", "ETF_OR_MACRO_EXPOSURE", "DO_NOT_PRIORITIZE"], 20),
            "",
            "## Possible CORE Review Candidates",
            "",
            table(flags["POSSIBLE_CORE_REVIEW"], ["rank", "ticker", "primary_theme", "role_bucket", "volatility_bucket", "recommendation_tier", "reason_codes", "audit_comment"], 50),
            "",
            "## Possible WATCHLIST Review Candidates",
            "",
            table(flags["POSSIBLE_WATCHLIST_REVIEW"], ["rank", "ticker", "primary_theme", "role_bucket", "volatility_bucket", "recommendation_tier", "reason_codes", "audit_comment"], 50),
            "",
            "## Overheated Wait Review Candidates",
            "",
            table(flags["OVERHEAT_RULE_REVIEW"], ["rank", "ticker", "primary_theme", "role_bucket", "volatility_bucket", "technical_timing_score", "overheat_penalty", "recommendation_tier", "reason_codes", "audit_comment"], 50),
            "",
            "## Volatility Rule Review Candidates",
            "",
            table(flags["VOLATILITY_RULE_REVIEW"], ["rank", "ticker", "primary_theme", "role_bucket", "volatility_bucket", "recommendation_tier", "reason_codes", "audit_comment"], 50),
            "",
            "## Calibration Recommendations",
            "",
            f"- `POSSIBLE_CORE_REVIEW` count is {len(flags['POSSIBLE_CORE_REVIEW'])}; this suggests the current priority order may be over-penalizing top-30 cyclical growth names with only high volatility.",
            f"- `POSSIBLE_WATCHLIST_REVIEW` count is {len(flags['POSSIBLE_WATCHLIST_REVIEW'])}; consider whether top-75 / top-theme speculative names should be WATCHLIST_STRONG instead of SPECULATIVE_SATELLITE when technicals are not overheated.",
            f"- `OVERHEAT_RULE_REVIEW` count is {len(flags['OVERHEAT_RULE_REVIEW'])}; review whether `OVERHEATED_WAIT` should require stronger evidence than staging labels or high-volatility inference alone.",
            f"- `VOLATILITY_RULE_REVIEW` count is {len(flags['VOLATILITY_RULE_REVIEW'])}; review whether the volatility fallback is too aggressive for top-ranked candidates.",
            "",
            "## Next-Step Recommendation For R29A / R29B",
            "",
            "- `R29A`: calibrate rule priority and volatility thresholds on a copy of the advisory layer, focusing on top-30 and top-75 names that are currently speculative or waiting on pullbacks.",
            "- `R29B`: if the calibration is accepted, rerun the tier layer with revised thresholds before any historical backtest or recommendation-policy promotion.",
            "",
            "## Audit Details",
            "",
            f"- Rows with any audit flag: {len(all_flags)}",
            f"- Strongly reviewed top-30 names: {sum(1 for row in flags['POSSIBLE_CORE_REVIEW'] if to_int(row.get('rank'), 999999) <= 30)}",
        ]
    )
    return "\n".join(lines) + "\n"


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def run(root: Path) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)

    candidates, _candidate_fields = read_csv(root / CURRENT_CANDIDATES)
    themes, _theme_fields = read_csv(root / THEME_CLASSIFICATION)
    recs, rec_fields = read_csv(root / RECOMMENDATIONS)
    tech_path = root / TECHNICAL_TIMING
    tech_available = tech_path.exists()
    tech_rows, _tech_fields = read_csv(tech_path) if tech_available else ([], [])

    if not candidates:
        raise RuntimeError(f"Missing current ranked candidates: {root / CURRENT_CANDIDATES}")
    if not themes:
        raise RuntimeError(f"Missing theme classification: {root / THEME_CLASSIFICATION}")
    if not recs:
        raise RuntimeError(f"Missing recommendations: {root / RECOMMENDATIONS}")
    if "ticker" not in rec_fields:
        raise RuntimeError("Recommendation file missing ticker column")

    candidate_lookup = build_lookup(candidates)
    theme_lookup = build_lookup(themes)
    tech_lookup = build_lookup(tech_rows)

    if len(candidates) != 252 or len(recs) != 252 or len(themes) != 252:
        raise RuntimeError("Row count mismatch detected; expected 252 rows across inputs")

    duplicate_count = duplicate_ticker_count(recs)
    if duplicate_count:
        raise RuntimeError("Duplicate ticker rows detected in recommendations")

    rows: List[Dict[str, object]] = []
    missing_tier = 0
    missing_action = 0
    unknown_theme_count = 0
    technical_matched = 0
    possible_core = 0
    possible_watchlist = 0
    overheat_review = 0
    volatility_review = 0

    for rec in recs:
        t = ticker(rec.get("ticker"))
        candidate = candidate_lookup.get(t, {})
        theme = theme_lookup.get(t, {})
        tech = tech_lookup.get(t, {})
        if tech:
            technical_matched += 1

        row: Dict[str, object] = {
            "ticker": t,
            "rank": rec.get("rank", candidate.get("rank", "")),
            "composite_candidate_score": rec.get("composite_candidate_score", candidate.get("composite_candidate_score", "")),
            "primary_theme": rec.get("primary_theme", theme.get("primary_theme", "")),
            "theme_rank": rec.get("theme_rank", theme.get("theme_rank", "")),
            "role_bucket": rec.get("role_bucket", theme.get("role_bucket", "")),
            "volatility_bucket": rec.get("volatility_bucket", theme.get("volatility_bucket", "")),
            "technical_timing_score": rec.get("technical_timing_score", tech.get("technical_timing_score", "")),
            "overheat_penalty": rec.get("overheat_penalty", tech.get("overheat_penalty", "")),
            "recommendation_tier": rec.get("recommendation_tier", ""),
            "recommendation_action": rec.get("recommendation_action", ""),
            "risk_label": rec.get("risk_label", ""),
            "reason_codes": rec.get("reason_codes", ""),
            "bb_status": rec.get("bb_status", tech.get("bb_status", "")),
            "rsi_status": rec.get("rsi_status", tech.get("rsi_status", "")),
            "kdj_status": rec.get("kdj_status", tech.get("kdj_status", "")),
            "technical_signal": rec.get("technical_signal", tech.get("technical_signal", "")),
            "technical_warning_label": rec.get("technical_warning_label", tech.get("technical_warning_label", "")),
        }

        if not norm(row["recommendation_tier"]):
            missing_tier += 1
        if not norm(row["recommendation_action"]):
            missing_action += 1
        if norm(row["primary_theme"]).upper() in {"", "UNKNOWN"}:
            unknown_theme_count += 1

        audit_flag, audit_comment_raw = make_flag(row)
        audit_comment_text = audit_comment(row, audit_flag, audit_comment_raw)

        if audit_flag != "NONE":
            if "POSSIBLE_CORE_REVIEW" in audit_flag:
                possible_core += 1
            if "POSSIBLE_WATCHLIST_REVIEW" in audit_flag:
                possible_watchlist += 1
            if "OVERHEAT_RULE_REVIEW" in audit_flag:
                overheat_review += 1
            if "VOLATILITY_RULE_REVIEW" in audit_flag:
                volatility_review += 1

        row["audit_flag"] = audit_flag
        row["audit_comment"] = audit_comment_text
        rows.append(row)

    rows.sort(key=sort_key)
    output_count = len(rows)
    top30 = [row for row in rows if to_int(row.get("rank"), 999999) <= 30]

    tier_counts = Counter(norm(row.get("recommendation_tier")) for row in rows)
    top30_counts = Counter(norm(row.get("recommendation_tier")) for row in top30)
    all_flags = [row for row in rows if norm(row.get("audit_flag")) != "NONE"]
    calibration_action_required = "YES" if all_flags else "NO"

    forbidden_modified = protected_sig(root) != protected_before
    if forbidden_modified:
        raise RuntimeError("Protected state modified during calibration audit")

    status = STATUS_OK
    if any([possible_core, possible_watchlist, overheat_review, volatility_review]):
        status = STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "INPUT_RECOMMENDATION_ROW_COUNT": len(recs),
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": len(candidates),
        "MISSING_RECOMMENDATION_TIER_COUNT": missing_tier,
        "MISSING_RECOMMENDATION_ACTION_COUNT": missing_action,
        "UNKNOWN_PRIMARY_THEME_COUNT": unknown_theme_count,
        "DUPLICATE_TICKER_COUNT": duplicate_count,
        "CORE_CANDIDATE_COUNT": tier_counts.get("CORE_CANDIDATE", 0),
        "WATCHLIST_STRONG_COUNT": tier_counts.get("WATCHLIST_STRONG", 0),
        "TACTICAL_ENTRY_COUNT": tier_counts.get("TACTICAL_ENTRY", 0),
        "OVERHEATED_WAIT_COUNT": tier_counts.get("OVERHEATED_WAIT", 0),
        "SPECULATIVE_SATELLITE_COUNT": tier_counts.get("SPECULATIVE_SATELLITE", 0),
        "DEFENSIVE_HEDGE_COUNT": tier_counts.get("DEFENSIVE_HEDGE", 0),
        "ETF_OR_MACRO_EXPOSURE_COUNT": tier_counts.get("ETF_OR_MACRO_EXPOSURE", 0),
        "DO_NOT_PRIORITIZE_COUNT": tier_counts.get("DO_NOT_PRIORITIZE", 0),
        "TOP_30_SPECULATIVE_SATELLITE_COUNT": top30_counts.get("SPECULATIVE_SATELLITE", 0),
        "TOP_30_OVERHEATED_WAIT_COUNT": top30_counts.get("OVERHEATED_WAIT", 0),
        "TOP_30_CORE_CANDIDATE_COUNT": top30_counts.get("CORE_CANDIDATE", 0),
        "POSSIBLE_CORE_REVIEW_COUNT": possible_core,
        "POSSIBLE_WATCHLIST_REVIEW_COUNT": possible_watchlist,
        "OVERHEAT_RULE_REVIEW_COUNT": overheat_review,
        "VOLATILITY_RULE_REVIEW_COUNT": volatility_review,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "FALSE",
    }

    write_csv(root / OUT_CSV, rows, OUTPUT_FIELDS)
    write_text(root / OUT_REPORT, build_report(values, rows))
    write_read_first(root / OUT_READ_FIRST, values)

    if output_count != len(candidates) or missing_tier or missing_action or unknown_theme_count or duplicate_count:
        status = STATUS_FAIL
    values["STATUS"] = status
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, build_report(values, rows))
    write_csv(root / OUT_CSV, rows, OUTPUT_FIELDS)

    if status == STATUS_FAIL:
        raise RuntimeError("Recommendation calibration audit failed validation checks")
    return values


def write_failure(root: Path, error: BaseException) -> None:
    values = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "INPUT_RECOMMENDATION_ROW_COUNT": 0,
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": 0,
        "MISSING_RECOMMENDATION_TIER_COUNT": 0,
        "MISSING_RECOMMENDATION_ACTION_COUNT": 0,
        "UNKNOWN_PRIMARY_THEME_COUNT": 0,
        "DUPLICATE_TICKER_COUNT": 0,
        "CORE_CANDIDATE_COUNT": 0,
        "WATCHLIST_STRONG_COUNT": 0,
        "TACTICAL_ENTRY_COUNT": 0,
        "OVERHEATED_WAIT_COUNT": 0,
        "SPECULATIVE_SATELLITE_COUNT": 0,
        "DEFENSIVE_HEDGE_COUNT": 0,
        "ETF_OR_MACRO_EXPOSURE_COUNT": 0,
        "DO_NOT_PRIORITIZE_COUNT": 0,
        "TOP_30_SPECULATIVE_SATELLITE_COUNT": 0,
        "TOP_30_OVERHEATED_WAIT_COUNT": 0,
        "TOP_30_CORE_CANDIDATE_COUNT": 0,
        "POSSIBLE_CORE_REVIEW_COUNT": 0,
        "POSSIBLE_WATCHLIST_REVIEW_COUNT": 0,
        "OVERHEAT_RULE_REVIEW_COUNT": 0,
        "VOLATILITY_RULE_REVIEW_COUNT": 0,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "FALSE",
    }
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, f"# V18.28C Recommendation Tier Calibration Audit Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.28C recommendation tier calibration audit.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        values = run(root)
        print(f"STATUS: {values['STATUS']}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return 0
    except Exception as exc:
        write_failure(root, exc)
        print(f"STATUS: {STATUS_FAIL}")
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
