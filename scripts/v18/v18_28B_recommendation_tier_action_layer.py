from __future__ import annotations

import argparse
import csv
import datetime as dt
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_28B_RECOMMENDATION_TIERS_READY"
STATUS_WARN = "WARN_V18_28B_RECOMMENDATION_TIERS_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_28B_RECOMMENDATION_TIERS_ERROR"
MODE = "READ_ONLY_RECOMMENDATION_TIER_ACTION_LAYER"

CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
THEME_CLASSIFICATION = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
TECHNICAL_TIMING = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"

OUT_RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
OUT_REPORT = "outputs/v18/read_center/V18_CURRENT_RECOMMENDATION_TIERS.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_28B_READ_FIRST.txt"
EXPECTED_CURRENT_CANDIDATE_ROWS = 252

PROTECTED_FILES = [
    CURRENT_CANDIDATES,
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    TECHNICAL_TIMING,
    "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv",
]
PROTECTED_DIRS = [
    "state/v18/price_cache",
    "state/v18/trading",
    "outputs/v18/official_daily",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "CURRENT_RANKED_CANDIDATE_ROW_COUNT",
    "THEME_CLASSIFICATION_ROW_COUNT",
    "OUTPUT_RECOMMENDATION_ROW_COUNT",
    "MISSING_THEME_COUNT",
    "UNKNOWN_PRIMARY_THEME_COUNT",
    "DUPLICATE_TICKER_COUNT",
    "TECHNICAL_TIMING_AVAILABLE",
    "TECHNICAL_TIMING_MATCHED_COUNT",
    "RECOMMENDATION_TIER_COUNT",
    "CORE_CANDIDATE_COUNT",
    "WATCHLIST_STRONG_COUNT",
    "TACTICAL_ENTRY_COUNT",
    "OVERHEATED_WAIT_COUNT",
    "SPECULATIVE_SATELLITE_COUNT",
    "DEFENSIVE_HEDGE_COUNT",
    "ETF_OR_MACRO_EXPOSURE_COUNT",
    "DO_NOT_PRIORITIZE_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "FORBIDDEN_MODIFIED",
]

OUTPUT_FIELDS = [
    "rank",
    "ticker",
    "company_name",
    "composite_candidate_score",
    "primary_theme",
    "secondary_theme",
    "industry_group",
    "role_bucket",
    "cyclicality_bucket",
    "volatility_bucket",
    "liquidity_bucket",
    "theme_rank",
    "theme_percentile",
    "technical_timing_score",
    "overheat_penalty",
    "bb_status",
    "rsi_status",
    "kdj_status",
    "technical_signal",
    "technical_warning_label",
    "recommendation_tier",
    "recommendation_action",
    "position_role",
    "risk_label",
    "reason_codes",
    "operator_notes",
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


def duplicate_ticker_count(rows: Sequence[Dict[str, str]]) -> int:
    counts = Counter(ticker(row.get("ticker")) for row in rows if ticker(row.get("ticker")))
    return sum(1 for count in counts.values() if count > 1)


def build_lookup(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}
    for row in rows:
        t = ticker(row.get("ticker"))
        if t and t not in lookup:
            lookup[t] = row
    return lookup


def is_technical_overheat(row: Dict[str, object]) -> bool:
    rsi_status = norm(row.get("rsi_status")).upper()
    bb_status = norm(row.get("bb_status")).upper()
    technical_warning_label = norm(row.get("technical_warning_label")).upper()
    technical_score = to_float(row.get("technical_timing_score"), 999.0)
    if to_float(row.get("overheat_penalty")) > 0:
        return True
    if "EXTREME_OVERHEAT" in rsi_status or "OVERHEAT" in rsi_status:
        return True
    if "ABOVE_UPPER" in bb_status or "BREAKOUT_OVERHEAT" in bb_status:
        return True
    if "OVERHEAT" in technical_warning_label and technical_score <= 40:
        return True
    return False


def is_technical_caution(row: Dict[str, object]) -> bool:
    if is_technical_overheat(row):
        return False
    warning = norm(row.get("technical_warning_label")).upper()
    score = to_float(row.get("technical_timing_score"), 999.0)
    bb_status = norm(row.get("bb_status")).upper()
    if score <= 40:
        return True
    if warning and warning not in {"NONE", "NOT_AVAILABLE_RESERVED"}:
        return True
    if "UPPER_HALF" in bb_status:
        return True
    return False


def risk_label(role_bucket: str, cyclicality_bucket: str, volatility_bucket: str, tier: str) -> str:
    vol = volatility_bucket.upper()
    cyc = cyclicality_bucket.upper()
    role = role_bucket.upper()
    if tier == "ETF_OR_MACRO_EXPOSURE":
        return "MACRO_OR_ETF_REVIEW"
    if vol == "EXTREME":
        return "EXTREME_RISK"
    if vol == "HIGH" or role == "SPECULATIVE_SATELLITE":
        return "HIGH_RISK"
    if role == "DEFENSIVE_HEDGE" or cyc == "DEFENSIVE":
        return "DEFENSIVE_RISK"
    if vol == "LOW":
        return "LOW_RISK"
    return "MEDIUM_RISK"


def classify(row: Dict[str, object]) -> Tuple[str, str, str, str, List[str], str]:
    rank = to_int(row.get("rank"), 999999)
    theme_rank = to_int(row.get("theme_rank"), 999999)
    primary_theme = norm(row.get("primary_theme")).upper()
    industry_group = norm(row.get("industry_group")).upper()
    role = norm(row.get("role_bucket")).upper()
    vol = norm(row.get("volatility_bucket")).upper()
    reasons: List[str] = []
    strong_overheat = is_technical_overheat(row)
    technical_caution = is_technical_caution(row)
    is_etf_macro = primary_theme == "OTHER" and industry_group == "ETF"
    core_eligible = (
        rank <= 30
        and role in {"CORE_GROWTH", "CYCLICAL_GROWTH"}
        and vol in {"LOW", "MEDIUM", "HIGH"}
        and not strong_overheat
        and not is_etf_macro
        and role != "DEFENSIVE_HEDGE"
    )
    watchlist_eligible = (
        (rank <= 75 or theme_rank <= 3)
        and role in {"CORE_GROWTH", "CYCLICAL_GROWTH", "TACTICAL_BETA"}
        and vol in {"LOW", "MEDIUM", "HIGH"}
        and not strong_overheat
        and not is_etf_macro
    )

    if rank <= 30:
        reasons.append("TOP_30_RANK")
    if rank <= 75:
        reasons.append("TOP_75_RANK")
    if theme_rank <= 3:
        reasons.append("TOP_3_THEME_RANK")
    if role == "CORE_GROWTH":
        reasons.append("CORE_GROWTH_ROLE")
    if role == "CYCLICAL_GROWTH":
        reasons.append("CYCLICAL_GROWTH_ROLE")
    if role == "SPECULATIVE_SATELLITE":
        reasons.append("SPECULATIVE_ROLE")
    if vol == "HIGH":
        reasons.append("HIGH_VOLATILITY")
        reasons.append("HIGH_VOLATILITY_NOT_AUTO_DOWNGRADE")
    if vol == "EXTREME":
        reasons.append("EXTREME_VOLATILITY")
        reasons.append("EXTREME_VOLATILITY_LIMIT")
    if role == "DEFENSIVE_HEDGE":
        reasons.append("DEFENSIVE_ROLE")
    if is_etf_macro:
        reasons.append("ETF_OR_MACRO")
    if strong_overheat:
        reasons.append("STRONG_TECHNICAL_OVERHEAT")
    elif technical_caution:
        reasons.append("TECHNICAL_CAUTION")
    if core_eligible:
        reasons.append("CALIBRATED_CORE_ELIGIBLE")
    if watchlist_eligible:
        reasons.append("CALIBRATED_WATCHLIST_ELIGIBLE")
    if rank > 125:
        reasons.append("LOW_PRIORITY_RANK")

    if is_etf_macro:
        tier, action, position = "ETF_OR_MACRO_EXPOSURE", "MACRO_OR_ETF_SEPARATE_REVIEW", "MACRO_ETF"
    elif role == "DEFENSIVE_HEDGE":
        tier, action, position = "DEFENSIVE_HEDGE", "DEFENSIVE_HOLD_CANDIDATE", "DEFENSIVE"
    elif strong_overheat:
        tier, action, position = "OVERHEATED_WAIT", "WAIT_FOR_PULLBACK", "TACTICAL"
    elif core_eligible:
        tier, action, position = "CORE_CANDIDATE", "REVIEW_FIRST", "CORE"
    elif watchlist_eligible:
        tier, action, position = "WATCHLIST_STRONG", "WATCH_FOR_ENTRY", "TACTICAL"
    elif role == "SPECULATIVE_SATELLITE":
        if rank <= 75 or theme_rank <= 3:
            tier, action, position = "SPECULATIVE_SATELLITE", "HIGH_RISK_SMALL_SIZE_ONLY", "SATELLITE"
        else:
            tier, action, position = "DO_NOT_PRIORITIZE", "LOW_PRIORITY", "AVOID_OR_LOW_PRIORITY"
    elif vol == "EXTREME":
        if rank <= 75 or theme_rank <= 3:
            tier, action, position = "SPECULATIVE_SATELLITE", "HIGH_RISK_SMALL_SIZE_ONLY", "SATELLITE"
        else:
            tier, action, position = "DO_NOT_PRIORITIZE", "LOW_PRIORITY", "AVOID_OR_LOW_PRIORITY"
    elif rank <= 75 or theme_rank <= 3:
        tier, action, position = "WATCHLIST_STRONG", "WATCH_FOR_ENTRY", "TACTICAL"
    elif rank <= 125:
        tier, action, position = "TACTICAL_ENTRY", "WATCH_FOR_ENTRY", "TACTICAL"
    else:
        tier, action, position = "DO_NOT_PRIORITIZE", "LOW_PRIORITY", "AVOID_OR_LOW_PRIORITY"

    risk = risk_label(role, norm(row.get("cyclicality_bucket")).upper(), vol, tier)
    notes = (
        f"Advisory tier only. Rank {rank}; theme {primary_theme}; role {role or 'UNKNOWN'}; "
        f"volatility {vol or 'UNKNOWN'}; action {action}. No official decision or trade instruction."
    )
    return tier, action, position, risk, reasons, notes


def build_rows(
    candidates: Sequence[Dict[str, str]],
    theme_lookup: Dict[str, Dict[str, str]],
    technical_lookup: Dict[str, Dict[str, str]],
) -> Tuple[List[Dict[str, object]], int, int]:
    rows: List[Dict[str, object]] = []
    missing_theme = 0
    technical_matched = 0
    for candidate in candidates:
        t = ticker(candidate.get("ticker"))
        theme = theme_lookup.get(t, {})
        tech = technical_lookup.get(t, {})
        if not theme:
            missing_theme += 1
        if tech:
            technical_matched += 1
        row: Dict[str, object] = {
            "rank": candidate.get("rank", ""),
            "ticker": t,
            "company_name": theme.get("company_name", ""),
            "composite_candidate_score": candidate.get("composite_candidate_score", ""),
            "primary_theme": theme.get("primary_theme", ""),
            "secondary_theme": theme.get("secondary_theme", ""),
            "industry_group": theme.get("industry_group", ""),
            "role_bucket": theme.get("role_bucket", ""),
            "cyclicality_bucket": theme.get("cyclicality_bucket", ""),
            "volatility_bucket": theme.get("volatility_bucket", ""),
            "liquidity_bucket": theme.get("liquidity_bucket", ""),
            "theme_rank": theme.get("theme_rank", ""),
            "theme_percentile": theme.get("theme_percentile", ""),
            "technical_timing_score": tech.get("technical_timing_score", ""),
            "overheat_penalty": tech.get("overheat_penalty", candidate.get("overheat_penalty", "")),
            "bb_status": tech.get("bb_status", candidate.get("pullback_status", "")),
            "rsi_status": tech.get("rsi_status", ""),
            "kdj_status": tech.get("kdj_status", ""),
            "technical_signal": tech.get("technical_signal", candidate.get("technical_status", "")),
            "technical_warning_label": tech.get("technical_warning_label", ""),
            "overheat_status": candidate.get("overheat_status", ""),
            "rsi_14": tech.get("rsi_14", ""),
            "bb_percent_b": tech.get("bb_percent_b", ""),
        }
        tier, action, position, risk, reasons, notes = classify(row)
        row.update(
            {
                "recommendation_tier": tier,
                "recommendation_action": action,
                "position_role": position,
                "risk_label": risk,
                "reason_codes": ";".join(reasons),
                "operator_notes": notes,
            }
        )
        rows.append(row)
    rows.sort(key=lambda row: to_int(row.get("rank"), 999999))
    return rows, missing_theme, technical_matched


def count_rows(rows: Sequence[Dict[str, object]], field: str) -> List[Dict[str, object]]:
    counts = Counter(norm(row.get(field)) or "BLANK" for row in rows)
    return [{"key": key, "count": count} for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def md_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: int = 30) -> str:
    selected = list(rows[:limit])
    if not selected:
        return "_None._"
    header = "| " + " | ".join(fields) + " |"
    sep = "| " + " | ".join(["---"] * len(fields)) + " |"
    body = ["| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |" for row in selected]
    return "\n".join([header, sep] + body)


def theme_summary(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[norm(row.get("primary_theme"))].append(row)
    out = []
    for theme, theme_rows in grouped.items():
        tiers = Counter(row.get("recommendation_tier") for row in theme_rows)
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


def top_by_theme(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[norm(row.get("primary_theme"))].append(row)
    out = []
    for theme in sorted(grouped):
        for row in sorted(grouped[theme], key=lambda item: to_int(item.get("rank"), 999999))[:3]:
            out.append(row)
    return out


def build_report(run_id: str, values: Dict[str, object], rows: Sequence[Dict[str, object]]) -> str:
    compact_fields = [
        "rank",
        "ticker",
        "company_name",
        "primary_theme",
        "role_bucket",
        "volatility_bucket",
        "theme_rank",
        "recommendation_action",
        "risk_label",
        "reason_codes",
    ]
    lines = [
        "# V18 Current Recommendation Tiers",
        "",
        "## Read First",
        "",
    ]
    lines.extend([f"- {field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS])
    lines.extend(
        [
            "",
            "## Recommendation Tier Counts",
            "",
            md_table(count_rows(rows, "recommendation_tier"), ["key", "count"], 20),
            "",
            "## Recommendation Action Counts",
            "",
            md_table(count_rows(rows, "recommendation_action"), ["key", "count"], 20),
            "",
            "## Top CORE_CANDIDATE",
            "",
            md_table([row for row in rows if row.get("recommendation_tier") == "CORE_CANDIDATE"], compact_fields, 30),
            "",
            "## Top WATCHLIST_STRONG",
            "",
            md_table([row for row in rows if row.get("recommendation_tier") == "WATCHLIST_STRONG"], compact_fields, 30),
            "",
            "## OVERHEATED_WAIT",
            "",
            md_table([row for row in rows if row.get("recommendation_tier") == "OVERHEATED_WAIT"], compact_fields, 50),
            "",
            "## SPECULATIVE_SATELLITE",
            "",
            md_table([row for row in rows if row.get("recommendation_tier") == "SPECULATIVE_SATELLITE"], compact_fields, 50),
            "",
            "## ETF_OR_MACRO_EXPOSURE",
            "",
            md_table([row for row in rows if row.get("recommendation_tier") == "ETF_OR_MACRO_EXPOSURE"], compact_fields, 50),
            "",
            "## Theme Summary",
            "",
            md_table(theme_summary(rows), ["primary_theme", "candidate_count", "core_count", "watchlist_count", "speculative_count", "do_not_prioritize_count"], 40),
            "",
            "## Top Candidates By Primary Theme",
            "",
            md_table(top_by_theme(rows), ["primary_theme", "rank", "ticker", "company_name", "recommendation_tier", "recommendation_action", "reason_codes"], 80),
            "",
            "## Safety",
            "",
            "- Advisory read-center layer only.",
            "- No official buy/sell orders, no auto-trade, no auto-sell.",
            "- No external fetch, yfinance, or backtest.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def run(root: Path, allow_non_252_current_candidates: bool = False) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)

    candidates, candidate_fields = read_csv(root / CURRENT_CANDIDATES)
    themes, _theme_fields = read_csv(root / THEME_CLASSIFICATION)
    if not candidates:
        raise RuntimeError(f"No current ranked candidate rows found: {root / CURRENT_CANDIDATES}")
    if not themes:
        raise RuntimeError(f"Missing theme classification rows: {root / THEME_CLASSIFICATION}")
    if "ticker" not in candidate_fields:
        raise RuntimeError("Current ranked candidates missing ticker column")
    if len(candidates) != EXPECTED_CURRENT_CANDIDATE_ROWS and not allow_non_252_current_candidates:
        raise RuntimeError(
            "Refusing to overwrite V18_CURRENT_RECOMMENDATION_TIERS.csv because "
            f"current ranked candidates row count is {len(candidates)}, expected {EXPECTED_CURRENT_CANDIDATE_ROWS}. "
            "Use --allow-non-252-current-candidates only for an intentional compatibility override."
        )

    tech_path = root / TECHNICAL_TIMING
    technical_available = tech_path.exists()
    technical_rows, _technical_fields = read_csv(tech_path) if technical_available else ([], [])

    theme_lookup = build_lookup(themes)
    technical_lookup = build_lookup(technical_rows)
    rows, missing_theme_count, technical_matched = build_rows(candidates, theme_lookup, technical_lookup)
    unknown_theme_count = sum(1 for row in rows if norm(row.get("primary_theme")).upper() in {"", "UNKNOWN"})
    duplicate_count = duplicate_ticker_count(candidates)
    tier_counts = Counter(row.get("recommendation_tier") for row in rows)
    missing_recs = sum(1 for row in rows if not row.get("recommendation_tier") or not row.get("recommendation_action"))

    forbidden_modified = protected_sig(root) != protected_before
    output_count = len(rows)
    if output_count != len(candidates) or missing_theme_count or unknown_theme_count or duplicate_count or missing_recs or forbidden_modified:
        status = STATUS_FAIL
    elif not technical_available or technical_matched != len(candidates):
        status = STATUS_WARN
    else:
        status = STATUS_OK

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": len(candidates),
        "THEME_CLASSIFICATION_ROW_COUNT": len(themes),
        "OUTPUT_RECOMMENDATION_ROW_COUNT": output_count,
        "MISSING_THEME_COUNT": missing_theme_count,
        "UNKNOWN_PRIMARY_THEME_COUNT": unknown_theme_count,
        "DUPLICATE_TICKER_COUNT": duplicate_count,
        "TECHNICAL_TIMING_AVAILABLE": "TRUE" if technical_available else "FALSE",
        "TECHNICAL_TIMING_MATCHED_COUNT": technical_matched,
        "RECOMMENDATION_TIER_COUNT": len(set(row.get("recommendation_tier") for row in rows if row.get("recommendation_tier"))),
        "CORE_CANDIDATE_COUNT": tier_counts.get("CORE_CANDIDATE", 0),
        "WATCHLIST_STRONG_COUNT": tier_counts.get("WATCHLIST_STRONG", 0),
        "TACTICAL_ENTRY_COUNT": tier_counts.get("TACTICAL_ENTRY", 0),
        "OVERHEATED_WAIT_COUNT": tier_counts.get("OVERHEATED_WAIT", 0),
        "SPECULATIVE_SATELLITE_COUNT": tier_counts.get("SPECULATIVE_SATELLITE", 0),
        "DEFENSIVE_HEDGE_COUNT": tier_counts.get("DEFENSIVE_HEDGE", 0),
        "ETF_OR_MACRO_EXPOSURE_COUNT": tier_counts.get("ETF_OR_MACRO_EXPOSURE", 0),
        "DO_NOT_PRIORITIZE_COUNT": tier_counts.get("DO_NOT_PRIORITIZE", 0),
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "TRUE" if forbidden_modified else "FALSE",
    }

    write_csv(root / OUT_RECOMMENDATIONS, rows, OUTPUT_FIELDS)
    write_text(root / OUT_REPORT, build_report(run_id, values, rows))
    write_read_first(root / OUT_READ_FIRST, values)

    if status == STATUS_FAIL:
        raise RuntimeError(f"V18.28B failed status checks: {values}")
    return values


def write_failure(root: Path, error: BaseException) -> None:
    values = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": 0,
        "THEME_CLASSIFICATION_ROW_COUNT": 0,
        "OUTPUT_RECOMMENDATION_ROW_COUNT": 0,
        "MISSING_THEME_COUNT": 0,
        "UNKNOWN_PRIMARY_THEME_COUNT": 0,
        "DUPLICATE_TICKER_COUNT": 0,
        "TECHNICAL_TIMING_AVAILABLE": "FALSE",
        "TECHNICAL_TIMING_MATCHED_COUNT": 0,
        "RECOMMENDATION_TIER_COUNT": 0,
        "CORE_CANDIDATE_COUNT": 0,
        "WATCHLIST_STRONG_COUNT": 0,
        "TACTICAL_ENTRY_COUNT": 0,
        "OVERHEATED_WAIT_COUNT": 0,
        "SPECULATIVE_SATELLITE_COUNT": 0,
        "DEFENSIVE_HEDGE_COUNT": 0,
        "ETF_OR_MACRO_EXPOSURE_COUNT": 0,
        "DO_NOT_PRIORITIZE_COUNT": 0,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "FALSE",
    }
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, f"# V18.28B Recommendation Tier Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.28B recommendation tier/action layer.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument(
        "--allow-non-252-current-candidates",
        action="store_true",
        help="Explicit compatibility override for non-252 current candidate universes.",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        values = run(root, allow_non_252_current_candidates=args.allow_non_252_current_candidates)
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
