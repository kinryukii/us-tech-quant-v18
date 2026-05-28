from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path


PATCH_VERSION = "V18.49B-R1"
PATCH_NAME = "OPTIONS_PROMOTION_GATE_AND_HISTORY_NORMALIZATION_REPAIR"
OPTIONS_HISTORY_COVERAGE_MIN = 0.70
OPTIONS_MATCHED_COMPLETED_MIN = 20

DECISION_COLUMNS = [
    "run_date", "source_patch_version", "source_status", "source_best_policy_id",
    "source_recommendation_label", "source_recommended_sim_style", "source_evidence_quality",
    "source_comparison_basis_status", "primary_policy_id", "secondary_policy_id",
    "simulation_policy_style", "entry_aggressiveness", "exit_aggressiveness",
    "max_paper_buy_count", "max_paper_add_count", "max_paper_reduce_count",
    "allow_new_paper_buys", "allow_paper_adds", "allow_paper_reduces",
    "allow_paper_exit_review", "options_risk_filter_mode", "event_risk_filter_mode",
    "technical_exit_validation_mode", "pullback_entry_mode", "policy_confidence",
    "policy_reason", "official_ranking_changed", "factor_weights_changed",
    "real_trade_execution_allowed", "broker_api_used", "order_execution_used",
]


def clean(value: object, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except (OSError, UnicodeDecodeError, csv.Error):
        return []


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_key_values(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                out[key.strip()] = value.strip()
    except OSError:
        pass
    return out


def normalize_decision_row(row: dict[str, str]) -> dict[str, str]:
    return {column: clean(row.get(column), "") for column in DECISION_COLUMNS}


def append_history(path: Path, row: dict[str, str]) -> dict[str, int]:
    rows = read_csv(path) if path.exists() else []
    current = normalize_decision_row(row)
    current_key = current.get("run_date", "")
    by_run_date: dict[str, dict[str, str]] = {}
    stats = {
        "rows_normalized": 0,
        "malformed_rows_dropped": 0,
        "duplicate_run_date_rows_collapsed": 0,
    }
    for old in rows:
        key = clean(old.get("run_date"), "")
        if not key:
            stats["malformed_rows_dropped"] += 1
            continue
        normalized = normalize_decision_row(old)
        stats["rows_normalized"] += 1
        if key in by_run_date:
            stats["duplicate_run_date_rows_collapsed"] += 1
        by_run_date[key] = normalized
    if current_key in by_run_date:
        stats["duplicate_run_date_rows_collapsed"] += 1
    by_run_date[current_key] = current
    write_csv(path, list(by_run_date.values()), DECISION_COLUMNS)
    return stats


def policy_available(summary_rows: list[dict[str, str]], policy_id: str) -> bool:
    for row in summary_rows:
        if row.get("policy_id") == policy_id:
            label = clean(row.get("recommendation_label"))
            return label not in {"DO_NOT_USE", "INSUFFICIENT_EVIDENCE", "UNKNOWN"}
    return False


def policy_label(summary_rows: list[dict[str, str]], policy_id: str) -> str:
    for row in summary_rows:
        if row.get("policy_id") == policy_id:
            return clean(row.get("recommendation_label"))
    return "UNKNOWN"


def policy_row(summary_rows: list[dict[str, str]], policy_id: str) -> dict[str, str] | None:
    for row in summary_rows:
        if row.get("policy_id") == policy_id:
            return row
    return None


def parse_float(value: object) -> float | None:
    try:
        return float(clean(value, ""))
    except ValueError:
        return None


def parse_int(value: object) -> int:
    try:
        return int(float(clean(value, "0")))
    except ValueError:
        return 0


def is_true(value: object) -> bool:
    return clean(value, "").upper() == "TRUE"


def options_risk_filtered_promotion(summary_rows: list[dict[str, str]]) -> tuple[bool, str]:
    row = policy_row(summary_rows, "OPTIONS_RISK_FILTERED")
    if row is None:
        return False, "OPTIONS_RISK_FILTERED_SOURCE_ROW_MISSING"
    label = clean(row.get("recommendation_label"))
    if label in {"DO_NOT_USE", "UNKNOWN"}:
        return False, f"OPTIONS_RISK_FILTERED_RECOMMENDATION_{label}"
    evidence = clean(row.get("evidence_quality"))
    if evidence in {"LOW", "INSUFFICIENT", "INSUFFICIENT_EVIDENCE", "UNKNOWN"}:
        return False, f"OPTIONS_RISK_FILTERED_EVIDENCE_{evidence}"
    comparison = clean(row.get("comparison_basis_status"))
    if comparison != "MATCHED_BASIS_OK":
        return False, f"OPTIONS_RISK_FILTERED_COMPARISON_{comparison}"
    coverage = parse_float(row.get("event_options_history_coverage_pct"))
    if coverage is None:
        return False, "OPTIONS_RISK_FILTERED_HISTORY_COVERAGE_MISSING"
    if coverage < OPTIONS_HISTORY_COVERAGE_MIN:
        return False, f"OPTIONS_RISK_FILTERED_HISTORY_COVERAGE_LT_{OPTIONS_HISTORY_COVERAGE_MIN:.2f}"
    completed = max(
        parse_int(row.get("matched_completed_5d_count")),
        parse_int(row.get("matched_completed_10d_count")),
        parse_int(row.get("matched_completed_20d_count")),
    )
    if completed < OPTIONS_MATCHED_COMPLETED_MIN:
        return False, f"OPTIONS_RISK_FILTERED_MATCHED_COMPLETED_LT_{OPTIONS_MATCHED_COMPLETED_MIN}"
    if "min_completed_threshold_met" in row and not is_true(row.get("min_completed_threshold_met")):
        return False, "OPTIONS_RISK_FILTERED_MIN_COMPLETED_THRESHOLD_NOT_MET"
    return True, "PROMOTED"


def low_event_options_coverage(summary_rows: list[dict[str, str]]) -> bool:
    for row in summary_rows:
        if row.get("policy_id") in {"EVENT_FILTERED", "OPTIONS_RISK_FILTERED", "DEFENSIVE"}:
            try:
                if float(clean(row.get("event_options_history_coverage_pct"), "0")) < 0.5:
                    return True
            except ValueError:
                return True
    return False


def build_decision(run_ts: str, read_first: dict[str, str], rec_rows: list[dict[str, str]], summary_rows: list[dict[str, str]]) -> tuple[dict[str, str], str, dict[str, str]]:
    options_promoted, options_blocked_reason = options_risk_filtered_promotion(summary_rows)
    source_found = bool(read_first) and bool(rec_rows) and bool(summary_rows)
    if not source_found:
        row = {
            "run_date": run_ts,
            "source_patch_version": "MISSING",
            "source_status": "SOURCE_BACKTEST_MISSING_OR_INVALID",
            "source_best_policy_id": "NONE",
            "source_recommendation_label": "UNKNOWN",
            "source_recommended_sim_style": "SIM_DEFENSIVE",
            "source_evidence_quality": "UNKNOWN",
            "source_comparison_basis_status": "UNKNOWN",
            "primary_policy_id": "NONE",
            "secondary_policy_id": "NONE",
            "simulation_policy_style": "SIM_DEFENSIVE",
            "entry_aggressiveness": "BLOCKED",
            "exit_aggressiveness": "ACTIVE_REVIEW",
            "max_paper_buy_count": "0",
            "max_paper_add_count": "0",
            "max_paper_reduce_count": "1",
            "allow_new_paper_buys": "FALSE",
            "allow_paper_adds": "FALSE",
            "allow_paper_reduces": "TRUE",
            "allow_paper_exit_review": "TRUE",
            "options_risk_filter_mode": "CURRENT_CONTEXT_ONLY_OR_LIMITED_HISTORY",
            "event_risk_filter_mode": "CURRENT_CONTEXT_ONLY_OR_LIMITED_HISTORY",
            "technical_exit_validation_mode": "ENABLED",
            "pullback_entry_mode": "REFERENCE_ONLY",
            "policy_confidence": "LOW",
            "policy_reason": "SOURCE_BACKTEST_MISSING_OR_INVALID",
            "official_ranking_changed": "FALSE",
            "factor_weights_changed": "FALSE",
            "real_trade_execution_allowed": "FALSE",
            "broker_api_used": "FALSE",
            "order_execution_used": "FALSE",
        }
        meta = {
            "options_risk_filtered_promoted": "FALSE",
            "options_risk_filtered_blocked_reason": "SOURCE_BACKTEST_MISSING_OR_INVALID",
        }
        return row, "WARN_V18_49B_SOURCE_BACKTEST_MISSING", meta

    rec = rec_rows[0]
    source_status = clean(read_first.get("STATUS"))
    evidence = clean(read_first.get("EVIDENCE_QUALITY") or rec.get("evidence_quality"))
    comparison = clean(read_first.get("COMPARISON_BASIS_STATUS"))
    best_policy = clean(read_first.get("BEST_POLICY_ID") or rec.get("recommended_policy_id"))
    rec_label = clean(read_first.get("BEST_POLICY_RECOMMENDATION_LABEL"))
    rec_style = clean(read_first.get("RECOMMENDED_SIM_STYLE") or rec.get("recommended_sim_style"))
    reasons = []
    confidence = "LOW" if evidence == "LOW" or "LOW_EVIDENCE" in rec_label else clean(rec.get("confidence_level"), "LOW")

    style = rec_style if rec_style in {"SIM_DEFENSIVE", "SIM_BALANCED", "SIM_AGGRESSIVE_TEST", "SIM_EXIT_VALIDATION", "SIM_EVENT_LOCK_TEST"} else "SIM_DEFENSIVE"
    entry = "LIMITED"
    exit_aggr = "ACTIVE_REVIEW"
    max_buy = 1
    max_add = 0
    max_reduce = 1
    allow_buys = "FALSE"
    allow_adds = "FALSE"
    allow_reduces = "TRUE"
    allow_exit_review = "TRUE"
    primary = best_policy
    secondary = "NONE"
    technical_mode = "DISABLED"
    pullback_mode = "REFERENCE_ONLY"

    if evidence == "LOW":
        if style == "SIM_AGGRESSIVE_TEST":
            style = "SIM_BALANCED"
        confidence = "LOW"
        reasons.append("LOW_EVIDENCE_NOT_READY_FOR_POLICY_WEIGHTING")
        if best_policy == "BASELINE_TOP20":
            style = "SIM_BALANCED"
            entry = "LIMITED_NORMAL"
            exit_aggr = "ACTIVE_REVIEW"
            primary = "BASELINE_TOP20"
            secondary = "OPTIONS_RISK_FILTERED" if options_promoted else "NONE"
            max_buy = 3
            max_add = 1
            max_reduce = 1
            allow_buys = "TRUE"
            allow_adds = "TRUE" if max_add > 0 else "FALSE"
            reasons.append("LOW_EVIDENCE_BASELINE_ONLY")
    if comparison == "COMPARISON_BASIS_LIMITED":
        if style == "SIM_AGGRESSIVE_TEST":
            style = "SIM_BALANCED"
        reasons.append("COMPARISON_BASIS_LIMITED_NOT_READY_FOR_POLICY_WEIGHTING")
        confidence = "LOW"
    if "LOW_EVIDENCE" in rec_label:
        confidence = "LOW"
        if style == "SIM_AGGRESSIVE_TEST":
            style = "SIM_BALANCED"

    tech_label = policy_label(summary_rows, "TECHNICAL_HEAVY")
    pull_label = policy_label(summary_rows, "PULLBACK_ENTRY")
    if tech_label == "SIMULATION_EXIT_VALIDATION_ONLY" or pull_label == "SIMULATION_EXIT_VALIDATION_ONLY":
        technical_mode = "ENABLED"
        pullback_mode = "REFERENCE_ONLY"
    if options_promoted:
        if secondary == "NONE":
            secondary = "OPTIONS_RISK_FILTERED"
        options_mode = "SMALL_SIZE_OR_SKIP_HIGH_RISK"
    else:
        options_mode = "LIMITED_HISTORY_NOT_PROMOTED"
        reasons.append("OPTIONS_RISK_FILTERED_NOT_PROMOTED_LIMITED_HISTORY")
    event_mode = "CURRENT_CONTEXT_ONLY_OR_LIMITED_HISTORY" if low_event_options_coverage(summary_rows) or comparison != "MATCHED_BASIS_OK" else "POINT_IN_TIME_FILTER_ENABLED"
    if low_event_options_coverage(summary_rows) and options_mode != "SMALL_SIZE_OR_SKIP_HIGH_RISK":
        options_mode = "CURRENT_CONTEXT_ONLY_OR_LIMITED_HISTORY"
    if style == "SIM_DEFENSIVE":
        entry = "LIMITED" if allow_buys == "TRUE" else "BLOCKED"
        max_buy = min(max_buy, 1)
        max_add = 0
        allow_adds = "FALSE"
    if style == "SIM_EXIT_VALIDATION":
        entry = "LIMITED"
        exit_aggr = "EXIT_VALIDATION_ONLY"
        max_buy = min(max_buy, 1)
        max_add = 0

    row = {
        "run_date": run_ts,
        "source_patch_version": clean(read_first.get("PATCH_VERSION")),
        "source_status": source_status,
        "source_best_policy_id": best_policy,
        "source_recommendation_label": rec_label,
        "source_recommended_sim_style": rec_style,
        "source_evidence_quality": evidence,
        "source_comparison_basis_status": comparison,
        "primary_policy_id": primary,
        "secondary_policy_id": secondary,
        "simulation_policy_style": style,
        "entry_aggressiveness": entry,
        "exit_aggressiveness": exit_aggr,
        "max_paper_buy_count": str(max_buy),
        "max_paper_add_count": str(max_add),
        "max_paper_reduce_count": str(max_reduce),
        "allow_new_paper_buys": allow_buys,
        "allow_paper_adds": allow_adds,
        "allow_paper_reduces": allow_reduces,
        "allow_paper_exit_review": allow_exit_review,
        "options_risk_filter_mode": options_mode,
        "event_risk_filter_mode": event_mode,
        "technical_exit_validation_mode": technical_mode,
        "pullback_entry_mode": pullback_mode,
        "policy_confidence": confidence,
        "policy_reason": ";".join(dict.fromkeys(reasons)) if reasons else "SOURCE_BACKTEST_VALID_SIMULATION_ONLY",
        "official_ranking_changed": "FALSE",
        "factor_weights_changed": "FALSE",
        "real_trade_execution_allowed": "FALSE",
        "broker_api_used": "FALSE",
        "order_execution_used": "FALSE",
    }
    status = "WARN_V18_49B_SOURCE_BACKTEST_LOW_EVIDENCE" if evidence == "LOW" else "PASS"
    meta = {
        "options_risk_filtered_promoted": "TRUE" if options_promoted else "FALSE",
        "options_risk_filtered_blocked_reason": "NONE" if options_promoted else options_blocked_reason,
    }
    return row, status, meta


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(column), "") for column in columns) + " |")
    return "\n".join(lines)


def build_report(decision: dict[str, str], source_rows: list[dict[str, str]]) -> str:
    summary_columns = ["policy_id", "evidence_quality", "comparison_basis_status", "recommendation_label", "avg_return_5d"]
    return "\n".join([
        "# V18.49B-R1 Simulation Policy Weight Engine",
        "",
        "V18.49B-R1 reads V18.49A-R1 evidence and converts it into simulation-cabin policy settings only.",
        "",
        "## Source V18.49A-R1 Evidence",
        markdown_table(source_rows, summary_columns) if source_rows else "SOURCE_BACKTEST_MISSING_OR_INVALID",
        "",
        "## Simulation Policy Decision",
        markdown_table([decision], ["simulation_policy_style", "primary_policy_id", "secondary_policy_id", "policy_confidence", "policy_reason"]),
        "",
        "## Entry / Exit Aggressiveness",
        markdown_table([decision], ["entry_aggressiveness", "exit_aggressiveness", "max_paper_buy_count", "max_paper_add_count", "max_paper_reduce_count"]),
        "",
        "## Risk Filter Modes",
        markdown_table([decision], ["options_risk_filter_mode", "event_risk_filter_mode", "technical_exit_validation_mode", "pullback_entry_mode"]),
        "",
        "## Simulation Only",
        "This output is not real trade advice and creates no executable orders. It is only eligible for cautious simulation-cabin testing.",
        "",
        "## Official Ranking And Weights",
        "V18.49B-R1 does not change official ranking, factor weights, Top20 selection, buy/sell permissions, final_action, real positions, broker behavior, or order execution.",
        "",
        "## Next Step",
        "V18.49C Dual-Book Action Planner.",
        "",
    ]) + "\n"


def write_read_first(path: Path, values: dict[str, str]) -> None:
    order = [
        "STATUS", "PATCH_VERSION", "PATCH_NAME", "SOURCE_V18_49A_FOUND",
        "SOURCE_V18_49A_PATCH_VERSION", "SOURCE_V18_49A_STATUS", "SOURCE_EVIDENCE_QUALITY",
        "SOURCE_COMPARISON_BASIS_STATUS", "SOURCE_BEST_POLICY_ID", "SOURCE_RECOMMENDATION_LABEL",
        "SIMULATION_POLICY_STYLE", "PRIMARY_POLICY_ID", "SECONDARY_POLICY_ID",
        "ENTRY_AGGRESSIVENESS", "EXIT_AGGRESSIVENESS", "MAX_PAPER_BUY_COUNT",
        "MAX_PAPER_ADD_COUNT", "MAX_PAPER_REDUCE_COUNT", "ALLOW_NEW_PAPER_BUYS",
        "ALLOW_PAPER_ADDS", "ALLOW_PAPER_REDUCES", "ALLOW_PAPER_EXIT_REVIEW",
        "POLICY_CONFIDENCE", "CURRENT_ALIAS_WRITTEN", "OFFICIAL_RANKING_CHANGED",
        "OPTIONS_RISK_FILTERED_PROMOTED", "OPTIONS_RISK_FILTERED_BLOCKED_REASON",
        "HISTORY_ROWS_NORMALIZED", "HISTORY_MALFORMED_ROWS_DROPPED",
        "HISTORY_DUPLICATE_RUN_DATE_ROWS_COLLAPSED", "HISTORY_APPEND_SAFE",
        "FACTOR_WEIGHTS_CHANGED", "OFFICIAL_BUY_PERMISSION_CHANGED", "OFFICIAL_SELL_PERMISSION_CHANGED",
        "REAL_TRADE_EXECUTION_ALLOWED", "OPTIONS_TRADE_EXECUTION_ALLOWED", "TRADING_EXECUTION_ALLOWED",
        "AUTO_TRADE", "AUTO_SELL", "BROKER_API_USED", "ORDER_EXECUTION_USED", "VALIDATION_NOTES",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{key}: {values.get(key, '')}" for key in order) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only V18.49B simulation policy weight engine.")
    parser.add_argument("--root", "--project-root", dest="root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write-current", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_ts = datetime.now().astimezone().isoformat(timespec="seconds")
    fb_dir = root / "outputs/v18/factor_backtest"
    read_first_49a = root / "outputs/v18/ops/V18_49A_READ_FIRST.txt"
    summary_path = fb_dir / "V18_49A_POLICY_PERFORMANCE_SUMMARY.csv"
    rec_path = fb_dir / "V18_49A_POLICY_RECOMMENDATION.csv"
    diag_path = fb_dir / "V18_49A_SOURCE_DIAGNOSTICS.csv"

    read_first = read_key_values(read_first_49a)
    summary_rows = read_csv(summary_path)
    rec_rows = read_csv(rec_path)
    _ = read_csv(diag_path)
    decision, status, decision_meta = build_decision(run_ts, read_first, rec_rows, summary_rows)

    out_dir = root / "outputs/v18/action_plan"
    snapshot_path = out_dir / "V18_49B_SIMULATION_POLICY_WEIGHT_SNAPSHOT.csv"
    history_path = out_dir / "V18_49B_SIMULATION_POLICY_WEIGHT_HISTORY.csv"
    decision_path = out_dir / "V18_49B_SIMULATION_POLICY_DECISION.csv"
    report_path = root / "outputs/v18/read_center/V18_49B_SIMULATION_POLICY_WEIGHT_ENGINE_REPORT.md"
    current_path = root / "outputs/v18/read_center/V18_CURRENT_SIMULATION_POLICY_WEIGHT.md"
    read_first_path = root / "outputs/v18/ops/V18_49B_READ_FIRST.txt"

    write_csv(snapshot_path, [decision], DECISION_COLUMNS)
    write_csv(decision_path, [decision], DECISION_COLUMNS)
    history_stats = append_history(history_path, decision)
    report = build_report(decision, summary_rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    current_written = False
    if args.write_current:
        current_path.write_text(report, encoding="utf-8")
        current_written = True

    source_found = bool(read_first) and bool(summary_rows) and bool(rec_rows)
    values = {
        "STATUS": status,
        "PATCH_VERSION": PATCH_VERSION,
        "PATCH_NAME": PATCH_NAME,
        "SOURCE_V18_49A_FOUND": "TRUE" if source_found else "FALSE",
        "SOURCE_V18_49A_PATCH_VERSION": decision["source_patch_version"],
        "SOURCE_V18_49A_STATUS": decision["source_status"],
        "SOURCE_EVIDENCE_QUALITY": decision["source_evidence_quality"],
        "SOURCE_COMPARISON_BASIS_STATUS": decision["source_comparison_basis_status"],
        "SOURCE_BEST_POLICY_ID": decision["source_best_policy_id"],
        "SOURCE_RECOMMENDATION_LABEL": decision["source_recommendation_label"],
        "SIMULATION_POLICY_STYLE": decision["simulation_policy_style"],
        "PRIMARY_POLICY_ID": decision["primary_policy_id"],
        "SECONDARY_POLICY_ID": decision["secondary_policy_id"],
        "ENTRY_AGGRESSIVENESS": decision["entry_aggressiveness"],
        "EXIT_AGGRESSIVENESS": decision["exit_aggressiveness"],
        "MAX_PAPER_BUY_COUNT": decision["max_paper_buy_count"],
        "MAX_PAPER_ADD_COUNT": decision["max_paper_add_count"],
        "MAX_PAPER_REDUCE_COUNT": decision["max_paper_reduce_count"],
        "ALLOW_NEW_PAPER_BUYS": decision["allow_new_paper_buys"],
        "ALLOW_PAPER_ADDS": decision["allow_paper_adds"],
        "ALLOW_PAPER_REDUCES": decision["allow_paper_reduces"],
        "ALLOW_PAPER_EXIT_REVIEW": decision["allow_paper_exit_review"],
        "POLICY_CONFIDENCE": decision["policy_confidence"],
        "CURRENT_ALIAS_WRITTEN": "TRUE" if current_written else "FALSE",
        "OPTIONS_RISK_FILTERED_PROMOTED": decision_meta["options_risk_filtered_promoted"],
        "OPTIONS_RISK_FILTERED_BLOCKED_REASON": decision_meta["options_risk_filtered_blocked_reason"],
        "HISTORY_ROWS_NORMALIZED": str(history_stats["rows_normalized"]),
        "HISTORY_MALFORMED_ROWS_DROPPED": str(history_stats["malformed_rows_dropped"]),
        "HISTORY_DUPLICATE_RUN_DATE_ROWS_COLLAPSED": str(history_stats["duplicate_run_date_rows_collapsed"]),
        "HISTORY_APPEND_SAFE": "TRUE",
        "OFFICIAL_RANKING_CHANGED": "FALSE",
        "FACTOR_WEIGHTS_CHANGED": "FALSE",
        "OFFICIAL_BUY_PERMISSION_CHANGED": "FALSE",
        "OFFICIAL_SELL_PERMISSION_CHANGED": "FALSE",
        "REAL_TRADE_EXECUTION_ALLOWED": "FALSE",
        "OPTIONS_TRADE_EXECUTION_ALLOWED": "FALSE",
        "TRADING_EXECUTION_ALLOWED": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "BROKER_API_USED": "FALSE",
        "ORDER_EXECUTION_USED": "FALSE",
        "VALIDATION_NOTES": "READ_ONLY_SIMULATION_POLICY_ENGINE_NO_BACKTEST_NO_RANKING_WEIGHT_PERMISSION_POSITION_BROKER_ORDER_OR_TRADING_CHANGES",
    }
    write_read_first(read_first_path, values)
    print(f"STATUS: {status}")
    print(f"SIMULATION_POLICY_STYLE: {decision['simulation_policy_style']}")
    print(f"PRIMARY_POLICY_ID: {decision['primary_policy_id']}")
    print(f"SECONDARY_POLICY_ID: {decision['secondary_policy_id']}")
    print(f"OPTIONS_RISK_FILTERED_PROMOTED: {decision_meta['options_risk_filtered_promoted']}")
    print(f"POLICY_CONFIDENCE: {decision['policy_confidence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
