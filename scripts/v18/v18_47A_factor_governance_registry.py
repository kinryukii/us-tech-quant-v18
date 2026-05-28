from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PATCH_VERSION = "V18.47A"
PATCH_NAME = "Factor Governance Registry"

REGISTRY_COLUMNS = [
    "factor_id",
    "factor_name",
    "factor_group",
    "factor_type",
    "current_status",
    "official_weight",
    "shadow_weight",
    "max_allowed_weight",
    "data_source",
    "output_source",
    "used_in_official_ranking",
    "used_in_risk_gate",
    "used_in_shadow_report",
    "future_leak_risk",
    "future_leak_reason",
    "economic_rationale",
    "mathematical_or_empirical_basis",
    "historical_evidence_level",
    "asof_backtest_ready",
    "walk_forward_ready",
    "live_forward_ready",
    "live_forward_sample_count",
    "pending_forward_sample_count",
    "drawdown_relevance",
    "benchmark_relevance",
    "promotion_verdict",
    "demotion_rule",
    "notes",
]

ALLOWED_GROUPS = {
    "ALPHA",
    "TECHNICAL_TIMING",
    "EVENT_RISK",
    "OPTIONS_RISK",
    "DATA_QUALITY",
    "PORTFOLIO_RISK",
    "STRATEGY_VALIDATION",
    "ACTION_RESPONSE",
    "MANUAL_FEEDBACK",
    "FORWARD_ATTRIBUTION",
    "UNIVERSE_COVERAGE",
    "BUDGET_PERMISSION",
    "MARKET_REGIME",
}

ALLOWED_STATUSES = {
    "OFFICIAL_ACTIVE",
    "OFFICIAL_SMALL_WEIGHT",
    "RISK_GATE_ONLY",
    "RISK_ADJUSTED_ONLY",
    "SHADOW_ONLY",
    "RESEARCH_ONLY",
    "PROBATION",
    "DEMOTED",
    "REJECTED",
    "PLANNED_NOT_IMPLEMENTED",
}


@dataclass(frozen=True)
class FactorSpec:
    factor_id: str
    factor_name: str
    factor_group: str
    factor_type: str
    current_status: str
    official_weight: str = ""
    shadow_weight: str = ""
    max_allowed_weight: str = ""
    data_source: str = "CURRENT_OUTPUTS"
    output_source: str = "READ_ONLY_GOVERNANCE_REGISTRY"
    used_in_official_ranking: str = "FALSE"
    used_in_risk_gate: str = "FALSE"
    used_in_shadow_report: str = "FALSE"
    future_leak_risk: str = "LOW"
    future_leak_reason: str = "ASOF_AVAILABLE_OR_NON_PREDICTIVE_CONTROL"
    economic_rationale: str = "Governance classification pending additional evidence."
    mathematical_or_empirical_basis: str = "Read-only inventory classification; no formula changes."
    historical_evidence_level: str = "CURRENT_SYSTEM_EVIDENCE"
    asof_backtest_ready: str = "UNKNOWN"
    walk_forward_ready: str = "UNKNOWN"
    live_forward_ready: str = "UNKNOWN"
    live_forward_sample_count: str = "0"
    pending_forward_sample_count: str = "0"
    drawdown_relevance: str = "UNKNOWN"
    benchmark_relevance: str = "UNKNOWN"
    promotion_verdict: str = "NOT_PROMOTION_READY"
    demotion_rule: str = "NO_AUTOMATED_DEMOTION_IN_V18_47A"
    notes: str = "V18.47A is registry-only and does not promote, demote, or reweight factors."

    def to_row(self) -> dict[str, str]:
        row = {column: str(getattr(self, column)) for column in REGISTRY_COLUMNS}
        if row["factor_group"] not in ALLOWED_GROUPS:
            raise ValueError(f"Invalid factor_group for {self.factor_id}: {row['factor_group']}")
        if row["current_status"] not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid current_status for {self.factor_id}: {row['current_status']}")
        return row


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def slug_to_name(factor_id: str) -> str:
    return factor_id.replace("_", " ").title()


def discover_columns(root: Path) -> set[str]:
    candidates = [
        root / "outputs" / "v18" / "current",
        root / "outputs" / "v18" / "ranking",
        root / "outputs" / "v18" / "ranked_candidates",
        root / "outputs" / "v18" / "factor_pack",
        root / "outputs" / "v18" / "technical_timing",
        root / "outputs" / "v18" / "read_center",
    ]
    columns: set[str] = set()
    for folder in candidates:
        if not folder.exists():
            continue
        for path in folder.rglob("*.csv"):
            try:
                with path.open("r", encoding="utf-8-sig", newline="") as handle:
                    reader = csv.reader(handle)
                    header = next(reader, [])
                columns.update(item.strip() for item in header if item and item.strip())
            except (OSError, UnicodeDecodeError, csv.Error):
                continue
    return columns


def matching_files(root: Path, patterns: Iterable[str]) -> list[Path]:
    matches: list[Path] = []
    output_root = root / "outputs" / "v18"
    if not output_root.exists():
        return matches
    for pattern in patterns:
        matches.extend(output_root.rglob(pattern))
    return sorted(set(matches))


def make_factor(
    factor_id: str,
    group: str,
    ftype: str,
    status: str,
    **kwargs: str,
) -> FactorSpec:
    return FactorSpec(
        factor_id=factor_id,
        factor_name=kwargs.pop("factor_name", slug_to_name(factor_id)),
        factor_group=group,
        factor_type=ftype,
        current_status=status,
        **kwargs,
    )


def build_registry(root: Path) -> list[FactorSpec]:
    columns = discover_columns(root)
    has_options = bool(
        matching_files(
            root,
            [
                "*options_risk*.csv",
                "*options_chain*.csv",
                "*option_volume*.csv",
                "*iv_rank*.csv",
                "*put_call*.csv",
                "*skew_score*.csv",
            ],
        )
    )
    has_event_outputs = bool(
        matching_files(root, ["*event*risk*.csv", "*event*risk*.md", "*earnings*.csv", "*earnings*.md"])
    )

    factors: list[FactorSpec] = []

    def add(factor_id: str, group: str, ftype: str, status: str, **kwargs: str) -> None:
        factors.append(make_factor(factor_id, group, ftype, status, **kwargs))

    official_note = "Official current ranking input inventory; V18.47A records status only."
    add("factor_pack_score", "ALPHA", "OFFICIAL_SCORE", "OFFICIAL_ACTIVE", official_weight="CURRENT_SYSTEM_WEIGHT", used_in_official_ranking="TRUE", economic_rationale="Aggregates approved factor-pack signals into the official candidate score.", mathematical_or_empirical_basis="Existing official ranking chain field.", notes=official_note)
    add("factor_pack_rank", "ALPHA", "OFFICIAL_RANK", "OFFICIAL_ACTIVE", used_in_official_ranking="TRUE", economic_rationale="Orders candidates after official score computation.", mathematical_or_empirical_basis="Existing official ranked-candidate ordering field.", notes=official_note)
    add("technical_timing_score", "TECHNICAL_TIMING", "OFFICIAL_SCORE", "OFFICIAL_ACTIVE", official_weight="CURRENT_SYSTEM_WEIGHT", used_in_official_ranking="TRUE", economic_rationale="Captures as-of technical setup quality.", mathematical_or_empirical_basis="Existing technical timing field in current chain.", notes=official_note)
    add("technical_status", "TECHNICAL_TIMING", "OFFICIAL_LABEL", "OFFICIAL_SMALL_WEIGHT", official_weight="CURRENT_SYSTEM_WEIGHT_OR_LABEL", used_in_official_ranking=bool_text("technical_status" in columns), economic_rationale="Summarizes technical condition for candidate interpretation.", mathematical_or_empirical_basis="Current technical timing label.", notes="Small-weight or label-style technical input; no V18.47A weight change.")
    add("pullback_status", "TECHNICAL_TIMING", "OFFICIAL_LABEL", "OFFICIAL_SMALL_WEIGHT", official_weight="CURRENT_SYSTEM_WEIGHT_OR_LABEL", used_in_official_ranking=bool_text("pullback_status" in columns), economic_rationale="Identifies whether the entry setup is pullback-sensitive.", mathematical_or_empirical_basis="Current technical timing label.", notes="Classified as current official/small-weight only when present in current fields.")
    add("overheat_penalty", "TECHNICAL_TIMING", "RISK_ADJUSTMENT", "RISK_ADJUSTED_ONLY", official_weight="CURRENT_SYSTEM_PENALTY_IF_PRESENT", used_in_official_ranking=bool_text("overheat_penalty" in columns), used_in_risk_gate="TRUE", economic_rationale="Reduces enthusiasm for extended or overheated entries.", mathematical_or_empirical_basis="Current overheat control field if available.", notes="Risk adjustment only; no promotion or demotion in V18.47A.")

    for factor_id in ["price_freshness", "freshness_eligibility", "stale_price_data_flag", "actionable_allowed_by_freshness"]:
        add(factor_id, "DATA_QUALITY", "CURRENT_FRESHNESS_GATE", "RISK_GATE_ONLY", used_in_risk_gate="TRUE", future_leak_risk="LOW", economic_rationale="Prevents stale or non-actionable data from being treated as current.", mathematical_or_empirical_basis="Current freshness/readiness controls.", historical_evidence_level="OPERATIONAL_CONTROL", notes="Freshness is a gate/control, not an alpha factor.")

    for factor_id in ["kdj_shadow_signal", "macd_shadow_signal", "bb_status", "rsi_status", "sell_timing_shadow_label", "exit_signal_forward_validation"]:
        leak = "HIGH" if "forward_validation" in factor_id else "LOW"
        reason = "Forward validation must not be used for same-day ranking." if leak == "HIGH" else "As-of shadow technical signal."
        add(factor_id, "TECHNICAL_TIMING", "SHADOW_TECHNICAL_SIGNAL", "SHADOW_ONLY", used_in_shadow_report="TRUE", future_leak_risk=leak, future_leak_reason=reason, economic_rationale="Research-only technical timing evidence.", mathematical_or_empirical_basis="Shadow technical report field or planned shadow field.", historical_evidence_level="SHADOW_RESEARCH", notes="Shadow-only unless separately promoted by evidence outside V18.47A.")

    event_status = "RISK_GATE_ONLY" if has_event_outputs else "RESEARCH_ONLY"
    for factor_id in ["earnings_event_risk", "days_to_earnings", "earnings_window_flag", "macro_event_risk", "manual_event_override", "sector_event_exposure"]:
        group = "EVENT_RISK" if factor_id != "manual_event_override" else "MANUAL_FEEDBACK"
        add(factor_id, group, "EVENT_OR_OVERRIDE_CONTROL", event_status, used_in_risk_gate=bool_text(event_status == "RISK_GATE_ONLY"), economic_rationale="Controls event-window or discretionary risk not captured by alpha score.", mathematical_or_empirical_basis="Event calendar or manual override availability.", historical_evidence_level="CURRENT_FILE_AVAILABLE" if has_event_outputs else "RESEARCH_CONCEPT", notes="Event risk is conservative gate/research inventory only.")

    option_status = "RESEARCH_ONLY" if has_options else "PLANNED_NOT_IMPLEMENTED"
    for factor_id in ["atm_iv", "iv_rank", "expected_move_pct", "put_call_ratio", "skew_score", "option_volume_abnormal_flag", "option_liquidity_status", "options_risk_level"]:
        add(factor_id, "OPTIONS_RISK", "OPTIONS_RISK_CONTROL", option_status, used_in_risk_gate=bool_text(has_options), economic_rationale="Options market state may identify volatility, liquidity, and positioning risk.", mathematical_or_empirical_basis="Options chain or options summary data required.", historical_evidence_level="CURRENT_FILE_AVAILABLE" if has_options else "PLANNED", notes="Options factors remain non-ranking controls in V18.47A.")

    forward_ids = ["return_5d", "return_10d", "return_20d", "return_60d", "max_drawdown_20d", "max_drawdown_60d", "maturity_5d", "maturity_10d", "maturity_20d", "maturity_60d", "benchmark_excess_return", "beta_to_qqq", "alpha_after_beta_adjustment"]
    for factor_id in forward_ids:
        group = "STRATEGY_VALIDATION" if factor_id.startswith(("return_", "max_drawdown_", "maturity_")) else "FORWARD_ATTRIBUTION"
        add(factor_id, group, "FORWARD_VALIDATION_FIELD", "RESEARCH_ONLY", future_leak_risk="HIGH", future_leak_reason="Requires future returns or post-signal outcomes; prohibited from official ranking.", economic_rationale="Measures realized post-signal quality for validation, not prediction at decision time.", mathematical_or_empirical_basis="Forward return, drawdown, maturity, or beta-adjusted attribution calculation.", historical_evidence_level="FORWARD_VALIDATION_ONLY", asof_backtest_ready="FALSE", walk_forward_ready="UNKNOWN", live_forward_ready="UNKNOWN", drawdown_relevance=bool_text("drawdown" in factor_id), benchmark_relevance=bool_text(factor_id in {"benchmark_excess_return", "beta_to_qqq", "alpha_after_beta_adjustment"}), notes="High future-leak risk if used in ranking; V18.47A marks official ranking usage FALSE.")

    for factor_id in ["spy_return", "qqq_return", "qld_return", "tqqq_return", "upro_return", "qqq_spy_cash_rotation_return", "tqqq_cash_200ma_rotation_return", "market_regime", "vix_risk_flag"]:
        status = "RISK_GATE_ONLY" if factor_id in {"market_regime", "vix_risk_flag"} else "RESEARCH_ONLY"
        add(factor_id, "MARKET_REGIME", "MARKET_BENCHMARK_OR_REGIME", status, used_in_risk_gate=bool_text(status == "RISK_GATE_ONLY"), economic_rationale="Benchmarks and regime indicators contextualize factor performance and market risk.", mathematical_or_empirical_basis="Market proxy return or regime calculation.", benchmark_relevance="TRUE", notes="Market/regime inventory only; no official ranking formula change.")

    for factor_id in ["sector_exposure", "theme_exposure", "single_name_position_limit", "high_beta_exposure", "portfolio_concentration_risk_score"]:
        add(factor_id, "PORTFOLIO_RISK", "PORTFOLIO_RISK_CONTROL", "RISK_GATE_ONLY", used_in_risk_gate="TRUE", economic_rationale="Prevents concentration or exposure risks from overwhelming alpha selection.", mathematical_or_empirical_basis="Portfolio exposure and risk limit controls.", drawdown_relevance="TRUE", notes="Risk governance only; does not alter official candidate scoring in V18.47A.")

    for factor_id in ["buy_risk_score", "hold_risk_score", "sell_risk_score", "entry_strategy", "exit_strategy", "exit_plan_present"]:
        add(factor_id, "ACTION_RESPONSE", "ACTION_RESPONSE_CONTROL", "RESEARCH_ONLY", economic_rationale="Structures human-readable action response and execution preparedness.", mathematical_or_empirical_basis="Action layer or trade-plan fields.", notes="Action response remains advisory/read-center only.")

    trust_ids = ["current_authoritative_chain_ready", "validation_fail_count", "blocking_current_failure_count", "top_full_mismatch_count", "daily_trust_level", "candidate_report_trust", "invalid_pseudo_ticker_filter", "unavailable_ticker_quarantine"]
    for factor_id in trust_ids:
        group = "UNIVERSE_COVERAGE" if factor_id in {"invalid_pseudo_ticker_filter", "unavailable_ticker_quarantine"} else "DATA_QUALITY"
        add(factor_id, group, "SYSTEM_TRUST_CONTROL", "RISK_GATE_ONLY", used_in_risk_gate="TRUE", economic_rationale="Protects current outputs from known data, chain, or universe-quality failures.", mathematical_or_empirical_basis="Operational readiness and trust checks.", historical_evidence_level="OPERATIONAL_CONTROL", notes="Trust and quality controls are not alpha factors.")

    return factors


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(row.get(column, "") for column in columns) + " |")
    return "\n".join(lines)


def build_report(rows: list[dict[str, str]]) -> str:
    by_status = Counter(row["current_status"] for row in rows)
    official = [row for row in rows if row["used_in_official_ranking"] == "TRUE"]
    shadow = [row for row in rows if row["current_status"] == "SHADOW_ONLY"]
    gates = [row for row in rows if row["used_in_risk_gate"] == "TRUE"]
    data_quality = [row for row in rows if row["factor_group"] in {"DATA_QUALITY", "UNIVERSE_COVERAGE"}]
    planned = [row for row in rows if row["current_status"] == "PLANNED_NOT_IMPLEMENTED" or row["factor_group"] in {"OPTIONS_RISK", "ACTION_RESPONSE", "EVENT_RISK"}]
    high_leak = [row for row in rows if row["future_leak_risk"] == "HIGH"]

    sections = [
        f"# {PATCH_VERSION} Factor Governance Registry Report",
        "",
        "V18.47A is a read-only governance registry. It does not modify official ranking logic, factor weights, Top20 selection, freshness eligibility, trading execution, broker behavior, order behavior, or signal freeze ledgers.",
        "",
        "## Counts",
        markdown_table(
            [{"metric": key, "value": str(value)} for key, value in sorted(by_status.items())],
            ["metric", "value"],
        ),
        "",
        "## Official factors currently affecting ranking",
        markdown_table(official, ["factor_id", "factor_group", "current_status", "official_weight", "notes"]),
        "",
        "## Shadow factors currently not affecting ranking",
        markdown_table(shadow, ["factor_id", "factor_group", "future_leak_risk", "notes"]),
        "",
        "## Risk-gate factors",
        markdown_table(gates, ["factor_id", "factor_group", "current_status", "notes"]),
        "",
        "## Data-quality and system trust factors",
        markdown_table(data_quality, ["factor_id", "factor_group", "current_status", "notes"]),
        "",
        "## Planned options, event, and action-response factors",
        markdown_table(planned, ["factor_id", "factor_group", "current_status", "notes"]),
        "",
        "## High future-leak-risk factors",
        markdown_table(high_leak, ["factor_id", "factor_group", "future_leak_reason", "used_in_official_ranking"]),
        "",
        "## Promotion and demotion governance principles",
        "- Promotion requires as-of availability, reproducible backtest evidence, walk-forward evidence, live-forward samples, and explicit approval outside this patch.",
        "- Forward returns, realized drawdowns, maturity flags, and benchmark attribution are validation fields only and must not enter same-day ranking.",
        "- Demotion requires documented underperformance or operational risk evidence; V18.47A performs no demotion.",
        "- Uncertain factors stay RESEARCH_ONLY or SHADOW_ONLY.",
    ]
    return "\n".join(sections) + "\n"


def write_read_first(path: Path, rows: list[dict[str, str]], registry_path: Path, current_report_path: Path, current_alias_written: bool) -> None:
    by_status = Counter(row["current_status"] for row in rows)
    high_leak_count = sum(1 for row in rows if row["future_leak_risk"] == "HIGH")
    lines = [
        "STATUS: PASS",
        f"PATCH_VERSION: {PATCH_VERSION}",
        f"PATCH_NAME: {PATCH_NAME}",
        f"REGISTRY_ROW_COUNT: {len(rows)}",
        f"OFFICIAL_ACTIVE_COUNT: {by_status.get('OFFICIAL_ACTIVE', 0)}",
        f"SHADOW_ONLY_COUNT: {by_status.get('SHADOW_ONLY', 0)}",
        f"RISK_GATE_ONLY_COUNT: {by_status.get('RISK_GATE_ONLY', 0)}",
        f"PLANNED_NOT_IMPLEMENTED_COUNT: {by_status.get('PLANNED_NOT_IMPLEMENTED', 0)}",
        f"HIGH_FUTURE_LEAK_RISK_COUNT: {high_leak_count}",
        "OFFICIAL_RANKING_CHANGED: FALSE",
        "FACTOR_WEIGHTS_CHANGED: FALSE",
        "TRADING_EXECUTION_ALLOWED: FALSE",
        "AUTO_TRADE: DISABLED",
        "AUTO_SELL: DISABLED",
        "BROKER_API_USED: FALSE",
        "ORDER_EXECUTION_USED: FALSE",
        f"CURRENT_ALIAS_WRITTEN: {bool_text(current_alias_written)}",
        f"REGISTRY_PATH: {registry_path}",
        f"CURRENT_REPORT_PATH: {current_report_path}",
        "VALIDATION_NOTES: READ_ONLY_GOVERNANCE_REGISTRY_NO_RANKING_WEIGHT_TRADING_OR_BROKER_CHANGES",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V18.47A factor governance registry.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write-current", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rows = [factor.to_row() for factor in build_registry(root)]
    rows.sort(key=lambda row: (row["factor_group"], row["factor_id"]))

    registry_path = root / "outputs" / "v18" / "factor_governance" / "V18_47A_FACTOR_GOVERNANCE_REGISTRY.csv"
    summary_path = root / "outputs" / "v18" / "factor_governance" / "V18_47A_FACTOR_GOVERNANCE_SUMMARY.csv"
    report_path = root / "outputs" / "v18" / "read_center" / "V18_47A_FACTOR_GOVERNANCE_REGISTRY_REPORT.md"
    current_report_path = root / "outputs" / "v18" / "read_center" / "V18_CURRENT_FACTOR_GOVERNANCE_REGISTRY.md"
    read_first_path = root / "outputs" / "v18" / "ops" / "V18_47A_READ_FIRST.txt"

    write_csv(registry_path, rows, REGISTRY_COLUMNS)
    by_status = Counter(row["current_status"] for row in rows)
    by_group = Counter(row["factor_group"] for row in rows)
    summary_rows = (
        [{"summary_type": "STATUS", "summary_key": key, "summary_value": str(value)} for key, value in sorted(by_status.items())]
        + [{"summary_type": "GROUP", "summary_key": key, "summary_value": str(value)} for key, value in sorted(by_group.items())]
        + [{"summary_type": "SAFETY", "summary_key": "OFFICIAL_RANKING_CHANGED", "summary_value": "FALSE"}]
        + [{"summary_type": "SAFETY", "summary_key": "FACTOR_WEIGHTS_CHANGED", "summary_value": "FALSE"}]
        + [{"summary_type": "SAFETY", "summary_key": "TRADING_EXECUTION_ALLOWED", "summary_value": "FALSE"}]
    )
    write_csv(summary_path, summary_rows, ["summary_type", "summary_key", "summary_value"])

    report = build_report(rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    if args.write_current:
        current_report_path.write_text(report, encoding="utf-8")

    write_read_first(read_first_path, rows, registry_path, current_report_path, args.write_current)
    print(f"STATUS: PASS")
    print(f"REGISTRY_ROW_COUNT: {len(rows)}")
    print(f"REGISTRY_PATH: {registry_path}")
    print(f"REPORT_PATH: {report_path}")
    print(f"CURRENT_ALIAS_WRITTEN: {bool_text(args.write_current)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
