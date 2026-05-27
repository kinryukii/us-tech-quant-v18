from __future__ import annotations

import csv
import datetime as dt
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set


def norm(s: str) -> str:
    return (
        str(s or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_float(x):
    if x is None or x == "":
        return ""
    return x


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: List[Dict], fieldnames: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def read_csv_header(path: Path) -> Tuple[List[str], int]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            row_count = sum(1 for _ in reader)
        return header, row_count
    except Exception:
        return [], 0


def collect_csv_files(root: Path) -> List[Path]:
    exact = [
        root / "state/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv",
        root / "state/v18/V18_6C_CURRENT_TECHNICAL_TIMING_FORWARD_TRACKER.csv",
        root / "outputs/v18/technical_timing_forward/V18_6C_R1_CURRENT_STALE_PRICE_AUDIT.csv",
        root / "outputs/v18/simulation/V18_9B_CURRENT_FORWARD_RETURN_FILLER_AUDIT.csv",
        root / "outputs/v18/ops/V18_9C_CURRENT_OFFICIAL_DAILY_WITH_SIM_VALIDATION_PROFILE.csv",
        root / "outputs/v18/ops/V18_9C_CURRENT_OFFICIAL_DAILY_WITH_SIM_VALIDATION_STEPS.csv",
    ]

    patterns = [
        "state/v18/simulation/*.csv",
        "outputs/v18/simulation/*.csv",
        "outputs/v18/technical_timing/*.csv",
        "outputs/v18/technical_timing_forward/*.csv",
        "outputs/v18/daily_integrated/*.csv",
        "outputs/v18/factor_audit/*.csv",
        "outputs/v18/factor_pack/*.csv",
        "outputs/v18/promotion_merge/*.csv",
        "outputs/v18/read_center/*.csv",
        "outputs/v18/ops/*PROFILE.csv",
        "outputs/v18/ops/*STEPS.csv",
    ]

    files: List[Path] = []
    seen: Set[str] = set()

    for p in exact:
        if p.exists():
            rp = str(p.resolve()).lower()
            if rp not in seen:
                seen.add(rp)
                files.append(p)

    for pat in patterns:
        for p in root.glob(pat):
            if p.exists() and p.is_file():
                rp = str(p.resolve()).lower()
                if rp not in seen:
                    seen.add(rp)
                    files.append(p)

    return files


def factor_registry() -> List[Dict]:
    rows = [
        {
            "factor_name": "trend_score",
            "factor_group": "alpha",
            "factor_role": "ranking",
            "direction": "higher_is_better",
            "current_weight": 0.25,
            "min_weight": 0.15,
            "max_weight": 0.35,
            "official_status": "official_candidate",
            "decision_impact": "ranking_only",
            "data_source": "price_history / daily_factor_snapshot",
            "formula_note": "Measures medium-term price trend strength using multi-window returns or trend features.",
            "principle": "Trend persistence: strong assets often continue outperforming for a period.",
            "black_box_guard": "Formula and source must be visible. Cannot be optimized without factor effectiveness report.",
            "aliases": "trend_score|trend_strength_score|trend|trend_strength|trend_rank",
        },
        {
            "factor_name": "relative_strength_score",
            "factor_group": "alpha",
            "factor_role": "ranking",
            "direction": "higher_is_better",
            "current_weight": 0.20,
            "min_weight": 0.10,
            "max_weight": 0.30,
            "official_status": "official_candidate",
            "decision_impact": "ranking_only",
            "data_source": "asset_return vs benchmark_return",
            "formula_note": "Compares ticker performance against QQQ/XLK/SMH/SOXX or peer group.",
            "principle": "Leaders tend to outperform benchmarks and sector peers during durable themes.",
            "black_box_guard": "Benchmark must be named. Relative window must be recorded.",
            "aliases": "relative_strength_score|relative_strength|rs_score|rs_rank|relative_strength_rank",
        },
        {
            "factor_name": "pullback_quality_score",
            "factor_group": "alpha",
            "factor_role": "ranking",
            "direction": "higher_is_better",
            "current_weight": 0.20,
            "min_weight": 0.10,
            "max_weight": 0.30,
            "official_status": "official_candidate",
            "decision_impact": "ranking_only",
            "data_source": "price drawdown from recent high / pullback trigger table",
            "formula_note": "Rewards strong assets that have pulled back into a better risk-reward area.",
            "principle": "Improves entry quality. Strong asset plus better entry is preferable to chasing highs.",
            "black_box_guard": "Pullback anchor and trigger distance must be auditable.",
            "aliases": "pullback_quality_score|pullback_score|pullback_quality|pullback_watch|drawdown_from_high",
        },
        {
            "factor_name": "momentum_continuation_score",
            "factor_group": "alpha",
            "factor_role": "ranking",
            "direction": "higher_is_better",
            "current_weight": 0.15,
            "min_weight": 0.05,
            "max_weight": 0.25,
            "official_status": "official_candidate",
            "decision_impact": "ranking_only",
            "data_source": "recent returns / breakout continuation features",
            "formula_note": "Measures whether recent strength is continuing rather than fading.",
            "principle": "Information and institutional flows are often incorporated gradually.",
            "black_box_guard": "Cannot dominate trend and pullback weights. Max weight capped.",
            "aliases": "momentum_continuation_score|momentum_score|momentum|breakout_continuation|short_momentum",
        },
        {
            "factor_name": "overheat_penalty",
            "factor_group": "risk",
            "factor_role": "penalty",
            "direction": "lower_is_better",
            "current_weight": 0.10,
            "min_weight": 0.05,
            "max_weight": 0.20,
            "official_status": "official_candidate",
            "decision_impact": "ranking_penalty",
            "data_source": "multi-window returns / RSI / Bollinger extension / technical timing labels",
            "formula_note": "Penalizes excessive recent rise or stretched technical condition.",
            "principle": "Mean reversion and crowding risk after extreme short-term moves.",
            "black_box_guard": "Penalty thresholds must be explicit. It cannot silently become a buy/sell model.",
            "aliases": "overheat_penalty|overheat_score|overheat|old_overheat|overheat_unclassified|exhaustion_risk",
        },
        {
            "factor_name": "volatility_penalty",
            "factor_group": "risk",
            "factor_role": "penalty",
            "direction": "lower_is_better",
            "current_weight": 0.05,
            "min_weight": 0.00,
            "max_weight": 0.15,
            "official_status": "official_candidate",
            "decision_impact": "ranking_penalty_or_position_control",
            "data_source": "realized volatility / beta / leveraged ETF flag",
            "formula_note": "Penalizes unstable names, high beta, or leveraged instruments.",
            "principle": "High volatility increases drawdown and behavioral execution risk.",
            "black_box_guard": "Volatility window and beta source must be visible.",
            "aliases": "volatility_penalty|volatility_score|volatility|beta|risk_score|high_beta",
        },
        {
            "factor_name": "execution_fit",
            "factor_group": "execution",
            "factor_role": "ranking_auxiliary",
            "direction": "higher_is_better",
            "current_weight": 0.05,
            "min_weight": 0.00,
            "max_weight": 0.10,
            "official_status": "official_candidate",
            "decision_impact": "ranking_auxiliary_or_post_filter",
            "data_source": "cash / share price / broker constraints / FX buffer",
            "formula_note": "Measures whether the ticker can be realistically bought under current account constraints.",
            "principle": "Executable strategy must respect one-share minimum, cash, buffer, and broker constraints.",
            "black_box_guard": "Execution fit is not alpha. It must remain small or post-filter only.",
            "aliases": "execution_fit|execution_score|execution_penalty|buyable|shares_to_buy|cash_required|order_value",
        },

        {
            "factor_name": "data_freshness",
            "factor_group": "gate",
            "factor_role": "hard_gate",
            "direction": "must_pass",
            "current_weight": "",
            "min_weight": "",
            "max_weight": "",
            "official_status": "official_gate",
            "decision_impact": "hard_gate_no_weight",
            "data_source": "latest_price_date / freshness_status / stale audit",
            "formula_note": "Blocks execution when price or factor snapshot is stale.",
            "principle": "Stale data makes all downstream scores unreliable.",
            "black_box_guard": "Never allow high score to override stale data.",
            "aliases": "data_freshness|freshness_status|latest_price_date|price_date|stale_rows|fresh_rows",
        },
        {
            "factor_name": "event_risk",
            "factor_group": "gate",
            "factor_role": "hard_gate_or_downgrade_gate",
            "direction": "lower_is_better",
            "current_weight": "",
            "min_weight": "",
            "max_weight": "",
            "official_status": "official_gate",
            "decision_impact": "hard_gate_or_downgrade_no_weight",
            "data_source": "event calendar / macro calendar / earnings calendar",
            "formula_note": "Freezes or downgrades new buys around CPI, NFP, FOMC, earnings, or major geopolitical events.",
            "principle": "Event gaps can invalidate normal technical and factor signals.",
            "black_box_guard": "Event rule must show event name, date, severity, and action.",
            "aliases": "event_risk|event_risk_status|event_gate|event_calendar|macro_event|earnings_event",
        },
        {
            "factor_name": "vix_regime",
            "factor_group": "regime",
            "factor_role": "market_regime",
            "direction": "regime_based",
            "current_weight": "",
            "min_weight": "",
            "max_weight": "",
            "official_status": "official_context",
            "decision_impact": "regime_switch_or_gate_context",
            "data_source": "VIX close / VIX regime classifier",
            "formula_note": "Classifies market into VIX_NORMAL, VIX_CAUTION, or VIX_STRESS.",
            "principle": "Same signal has different reliability under different volatility regimes.",
            "black_box_guard": "Regime thresholds must be explicit before weight switching.",
            "aliases": "vix_regime|vix_close|vix|market_regime",
        },
        {
            "factor_name": "behavior_guard",
            "factor_group": "gate",
            "factor_role": "hard_gate",
            "direction": "must_pass",
            "current_weight": "",
            "min_weight": "",
            "max_weight": "",
            "official_status": "official_gate",
            "decision_impact": "hard_gate_no_weight",
            "data_source": "behavior guard report / decision state",
            "formula_note": "Blocks FOMO, chase-buying, stale-trigger execution, or impulse trades.",
            "principle": "Most real losses come from poor timing, overtrading, and emotional execution.",
            "black_box_guard": "Behavior block reason must be written in report.",
            "aliases": "behavior_guard|behavior_status|hard_block|fomo|discipline_status",
        },
        {
            "factor_name": "budget_constraint",
            "factor_group": "gate",
            "factor_role": "hard_gate",
            "direction": "must_pass",
            "current_weight": "",
            "min_weight": "",
            "max_weight": "",
            "official_status": "official_gate",
            "decision_impact": "hard_gate_no_weight",
            "data_source": "cash / FX / order buffer / minimum share rule",
            "formula_note": "Checks whether the account can execute a proposed order.",
            "principle": "Unexecutable signals must not become official buy actions.",
            "black_box_guard": "Cash, FX, buffer, and share count must be auditable.",
            "aliases": "budget_constraint|cash_usd|cash_jpy|cash|budget|buy_permission|official_permission",
        },
        {
            "factor_name": "position_cap",
            "factor_group": "gate",
            "factor_role": "risk_constraint",
            "direction": "must_pass",
            "current_weight": "",
            "min_weight": "",
            "max_weight": "",
            "official_status": "official_gate",
            "decision_impact": "risk_cap_no_weight",
            "data_source": "position state / proposed order / portfolio limits",
            "formula_note": "Prevents single-name, theme, high-beta, or daily cash usage from exceeding limits.",
            "principle": "Portfolio survival requires concentration control.",
            "black_box_guard": "Cap rule must state current exposure and limit.",
            "aliases": "position_cap|position_count|max_position|single_name_cap|daily_cash_cap|portfolio_cap",
        },
        {
            "factor_name": "leveraged_etf_constraint",
            "factor_group": "gate",
            "factor_role": "risk_constraint",
            "direction": "must_pass",
            "current_weight": "",
            "min_weight": "",
            "max_weight": "",
            "official_status": "official_gate",
            "decision_impact": "risk_cap_no_weight",
            "data_source": "ticker class / ETF leverage flag / VIX regime",
            "formula_note": "Controls SOXL, TQQQ, and other leveraged ETF exposure.",
            "principle": "Daily-reset leveraged ETFs have volatility decay and path dependency.",
            "black_box_guard": "Leveraged ETF permission must be explicit, especially under VIX_CAUTION/STRESS.",
            "aliases": "leveraged_etf_constraint|leveraged|is_leveraged|leverage_flag|soxl|tqqq",
        },

        {
            "factor_name": "watch_positive",
            "factor_group": "technical",
            "factor_role": "shadow_signal",
            "direction": "higher_is_better",
            "current_weight": 0,
            "min_weight": 0,
            "max_weight": 0,
            "official_status": "shadow_only",
            "decision_impact": "none",
            "data_source": "technical timing dashboard",
            "formula_note": "Positive watch state. Worth tracking but not an official buy.",
            "principle": "Separates observable strength from executable signal.",
            "black_box_guard": "Must remain shadow-only until forward return validates it.",
            "aliases": "watch_positive|technical_bucket|watch_state",
        },
        {
            "factor_name": "pullback_watch",
            "factor_group": "technical",
            "factor_role": "shadow_signal",
            "direction": "higher_is_better",
            "current_weight": 0,
            "min_weight": 0,
            "max_weight": 0,
            "official_status": "shadow_only",
            "decision_impact": "none",
            "data_source": "technical timing dashboard",
            "formula_note": "Ticker is near or entering a pullback-watch zone.",
            "principle": "Strong assets may become attractive after controlled pullbacks.",
            "black_box_guard": "Cannot become official buy without trigger and event/risk gates.",
            "aliases": "pullback_watch|technical_bucket|pullback_state",
        },
        {
            "factor_name": "bb_squeeze",
            "factor_group": "technical",
            "factor_role": "shadow_signal",
            "direction": "event_label",
            "current_weight": 0,
            "min_weight": 0,
            "max_weight": 0,
            "official_status": "shadow_only",
            "decision_impact": "none",
            "data_source": "Bollinger Band width / technical timing dashboard",
            "formula_note": "Bollinger Band compression indicates low-volatility compression.",
            "principle": "Volatility contraction can precede volatility expansion, but direction is unknown.",
            "black_box_guard": "Must not be used as standalone buy signal.",
            "aliases": "bb_squeeze|bollinger_squeeze|bb_width|squeeze",
        },
        {
            "factor_name": "breakout_continuation",
            "factor_group": "technical",
            "factor_role": "shadow_signal",
            "direction": "higher_is_better",
            "current_weight": 0,
            "min_weight": 0,
            "max_weight": 0,
            "official_status": "shadow_only",
            "decision_impact": "none",
            "data_source": "technical timing dashboard / breakout labels",
            "formula_note": "Breakout appears to be continuing rather than failing.",
            "principle": "Breakout follow-through can indicate demand absorbing supply.",
            "black_box_guard": "Needs false-breakout audit under VIX_CAUTION.",
            "aliases": "breakout_continuation|breakout|continuation",
        },
        {
            "factor_name": "exhaustion_risk",
            "factor_group": "technical",
            "factor_role": "shadow_risk_signal",
            "direction": "lower_is_better",
            "current_weight": 0,
            "min_weight": 0,
            "max_weight": 0,
            "official_status": "shadow_only",
            "decision_impact": "none",
            "data_source": "technical timing dashboard / overextension labels",
            "formula_note": "Flags potential short-term upside exhaustion.",
            "principle": "Late-stage momentum can reverse when marginal buyers are exhausted.",
            "black_box_guard": "Use as no-chase warning, not automatic sell.",
            "aliases": "exhaustion_risk|exhaustion|overextension",
        },
        {
            "factor_name": "old_overheat",
            "factor_group": "technical",
            "factor_role": "shadow_risk_signal",
            "direction": "lower_is_better",
            "current_weight": 0,
            "min_weight": 0,
            "max_weight": 0,
            "official_status": "shadow_only",
            "decision_impact": "none",
            "data_source": "technical timing dashboard",
            "formula_note": "Ticker has prior overheat condition that may still need digestion.",
            "principle": "Old overheat can indicate crowded or already-consumed upside.",
            "black_box_guard": "Must be validated with later forward returns.",
            "aliases": "old_overheat|overheat_history",
        },
        {
            "factor_name": "rsi",
            "factor_group": "technical",
            "factor_role": "shadow_indicator",
            "direction": "contextual",
            "current_weight": 0,
            "min_weight": 0,
            "max_weight": 0,
            "official_status": "shadow_only",
            "decision_impact": "none",
            "data_source": "technical indicator calculation",
            "formula_note": "Relative Strength Index. Measures recent up/down force balance.",
            "principle": "Useful for overbought/oversold context but noisy in strong trends.",
            "black_box_guard": "Cannot be standalone signal.",
            "aliases": "rsi|rsi_14|relative_strength_index",
        },
        {
            "factor_name": "kdj",
            "factor_group": "technical",
            "factor_role": "shadow_indicator",
            "direction": "contextual",
            "current_weight": 0,
            "min_weight": 0,
            "max_weight": 0,
            "official_status": "shadow_only",
            "decision_impact": "none",
            "data_source": "technical indicator calculation",
            "formula_note": "Stochastic oscillator variant measuring close location within recent range.",
            "principle": "Useful for short-term overbought/oversold but noisy.",
            "black_box_guard": "Cannot be standalone signal.",
            "aliases": "kdj|k_value|d_value|j_value|stochastic",
        },
        {
            "factor_name": "gamma_squeeze",
            "factor_group": "technical_derivatives",
            "factor_role": "research_only",
            "direction": "contextual",
            "current_weight": 0,
            "min_weight": 0,
            "max_weight": 0,
            "official_status": "research_only",
            "decision_impact": "none",
            "data_source": "options open interest / option volume / dealer gamma estimate",
            "formula_note": "Potential options-driven forced buying pressure.",
            "principle": "Dealer hedging can amplify short-term moves when call exposure is concentrated.",
            "black_box_guard": "Do not activate without real options data.",
            "aliases": "gamma_squeeze|dealer_gamma|option_gamma|call_oi|option_volume",
        },

        {
            "factor_name": "forward_return_1d",
            "factor_group": "validation",
            "factor_role": "label",
            "direction": "higher_is_better",
            "current_weight": "",
            "min_weight": "",
            "max_weight": "",
            "official_status": "validation_label",
            "decision_impact": "none",
            "data_source": "forward return filler",
            "formula_note": "One-trading-day forward return after signal snapshot.",
            "principle": "Validates short-term signal quality.",
            "black_box_guard": "Label only. Must never be available at decision time.",
            "aliases": "forward_return_1d|fwd_1d|return_1d|forward_1d_return|return_1d_pct",
        },
        {
            "factor_name": "forward_return_5d",
            "factor_group": "validation",
            "factor_role": "label",
            "direction": "higher_is_better",
            "current_weight": "",
            "min_weight": "",
            "max_weight": "",
            "official_status": "validation_label",
            "decision_impact": "none",
            "data_source": "forward return filler",
            "formula_note": "Five-trading-day forward return after signal snapshot.",
            "principle": "Validates one-week signal quality.",
            "black_box_guard": "Label only. Must never be available at decision time.",
            "aliases": "forward_return_5d|fwd_5d|return_5d|forward_5d_return|return_5d_pct",
        },
        {
            "factor_name": "forward_return_10d",
            "factor_group": "validation",
            "factor_role": "label",
            "direction": "higher_is_better",
            "current_weight": "",
            "min_weight": "",
            "max_weight": "",
            "official_status": "validation_label",
            "decision_impact": "none",
            "data_source": "forward return filler",
            "formula_note": "Ten-trading-day forward return after signal snapshot.",
            "principle": "Validates short-swing signal quality.",
            "black_box_guard": "Label only. Must never be available at decision time.",
            "aliases": "forward_return_10d|fwd_10d|return_10d|forward_10d_return|return_10d_pct",
        },
        {
            "factor_name": "forward_return_20d",
            "factor_group": "validation",
            "factor_role": "label",
            "direction": "higher_is_better",
            "current_weight": "",
            "min_weight": "",
            "max_weight": "",
            "official_status": "validation_label",
            "decision_impact": "none",
            "data_source": "forward return filler",
            "formula_note": "Twenty-trading-day forward return after signal snapshot.",
            "principle": "Validates one-month factor alpha.",
            "black_box_guard": "Label only. Must never be available at decision time.",
            "aliases": "forward_return_20d|fwd_20d|return_20d|forward_20d_return|return_20d_pct",
        },

        {
            "factor_name": "earnings_quality",
            "factor_group": "fundamental",
            "factor_role": "future_extension",
            "direction": "higher_is_better",
            "current_weight": 0,
            "min_weight": 0,
            "max_weight": 0,
            "official_status": "not_official_yet",
            "decision_impact": "none",
            "data_source": "earnings data / guidance / revenue / margin",
            "formula_note": "Assesses whether earnings support price strength.",
            "principle": "Long-term price needs business confirmation.",
            "black_box_guard": "Requires stable data source before official scoring.",
            "aliases": "earnings_quality|eps_growth|revenue_growth|guidance|margin",
        },
        {
            "factor_name": "valuation_pressure",
            "factor_group": "fundamental",
            "factor_role": "future_extension",
            "direction": "lower_is_better",
            "current_weight": 0,
            "min_weight": 0,
            "max_weight": 0,
            "official_status": "not_official_yet",
            "decision_impact": "none",
            "data_source": "valuation data",
            "formula_note": "Flags whether price already discounts too much future growth.",
            "principle": "Good company can be a bad trade if expectations are extreme.",
            "black_box_guard": "Requires transparent valuation metric and source.",
            "aliases": "valuation_pressure|pe|ps|ev_sales|peg|valuation",
        },
        {
            "factor_name": "sector_theme_exposure",
            "factor_group": "classification",
            "factor_role": "portfolio_context",
            "direction": "contextual",
            "current_weight": "",
            "min_weight": "",
            "max_weight": "",
            "official_status": "context_only",
            "decision_impact": "portfolio_control",
            "data_source": "manual ticker map / sector map",
            "formula_note": "Classifies ticker into AI, semiconductor, CPO, cloud, storage, ETF, leverage, etc.",
            "principle": "Prevents fake diversification from concentrated theme exposure.",
            "black_box_guard": "Theme map must be explicit and manually auditable.",
            "aliases": "sector_theme_exposure|sector|theme|industry|asset_class|ticker_class",
        },
    ]

    return rows


def find_matches(headers_by_file: Dict[Path, List[str]], aliases: List[str]) -> Tuple[Set[str], Set[str]]:
    alias_set = {norm(a) for a in aliases if a}
    matched_cols: Set[str] = set()
    matched_files: Set[str] = set()

    for f, headers in headers_by_file.items():
        nheaders = [norm(h) for h in headers]
        for h_raw, h_norm in zip(headers, nheaders):
            exact = h_norm in alias_set
            contains = any(a and a in h_norm for a in alias_set if len(a) >= 5)
            if exact or contains:
                matched_cols.add(h_raw)
                matched_files.add(str(f))
    return matched_cols, matched_files


def coverage_status(row: Dict, matched_cols: Set[str]) -> str:
    group = row["factor_group"]
    role = row["factor_role"]
    official = row["official_status"]

    if group == "gate":
        return "GATE_SOURCE_CAPTURED" if matched_cols else "GATE_DECLARED_SOURCE_NOT_FOUND"
    if group == "regime":
        return "REGIME_SOURCE_CAPTURED" if matched_cols else "REGIME_SOURCE_NOT_FOUND"
    if group == "validation":
        return "VALIDATION_LABEL_CAPTURED" if matched_cols else "VALIDATION_LABEL_PENDING_OR_NOT_FOUND"
    if official == "shadow_only":
        return "SHADOW_SIGNAL_CAPTURED" if matched_cols else "SHADOW_SIGNAL_NEEDS_CAPTURE"
    if official == "research_only":
        return "RESEARCH_SOURCE_CAPTURED" if matched_cols else "RESEARCH_SOURCE_NOT_FOUND"
    if official == "not_official_yet":
        return "FUTURE_EXTENSION_SOURCE_CAPTURED" if matched_cols else "FUTURE_EXTENSION_NOT_READY"
    if role in ("ranking", "penalty", "ranking_auxiliary"):
        return "OFFICIAL_CANDIDATE_CAPTURED" if matched_cols else "OFFICIAL_CANDIDATE_NEEDS_DAILY_CAPTURE"

    return "UNKNOWN"


def make_report(
    root: Path,
    stamp: str,
    registry_rows: List[Dict],
    coverage_rows: List[Dict],
    files: List[Path],
    file_meta: List[Dict],
    out_registry: Path,
    out_coverage: Path,
    out_report: Path,
    out_read_first: Path,
) -> str:
    total = len(registry_rows)
    captured = sum(1 for r in coverage_rows if str(r["coverage_status"]).endswith("CAPTURED"))
    official_candidates = [r for r in registry_rows if r["official_status"] == "official_candidate"]
    official_candidate_coverage = [
        r for r in coverage_rows
        if r["official_status"] == "official_candidate"
    ]
    official_candidate_captured = sum(
        1 for r in official_candidate_coverage
        if r["coverage_status"] == "OFFICIAL_CANDIDATE_CAPTURED"
    )
    gates = [r for r in coverage_rows if r["factor_group"] == "gate"]
    gates_found = sum(1 for r in gates if r["coverage_status"] == "GATE_SOURCE_CAPTURED")
    labels = [r for r in coverage_rows if r["factor_group"] == "validation"]
    labels_found = sum(1 for r in labels if r["coverage_status"] == "VALIDATION_LABEL_CAPTURED")

    missing_critical = [
        r for r in official_candidate_coverage
        if r["coverage_status"] != "OFFICIAL_CANDIDATE_CAPTURED"
    ]

    lines = []
    lines.append("# V18.10A Factor Registry + Coverage Audit")
    lines.append("")
    lines.append(f"Generated: `{stamp}`")
    lines.append("")
    lines.append("## 1. Status")
    lines.append("")
    lines.append("- STATUS: `OK_FACTOR_REGISTRY_COVERAGE_AUDIT_READY`")
    lines.append("- MODE: `NO_BLACK_BOX_FACTOR_GOVERNANCE`")
    lines.append("- OFFICIAL_DECISION_IMPACT: `NONE`")
    lines.append("- AUTO_WEIGHT_CHANGE: `DISABLED`")
    lines.append("- AUTO_PROMOTION: `DISABLED`")
    lines.append("- AUTO_TRADE: `DISABLED`")
    lines.append("")
    lines.append("## 2. Summary")
    lines.append("")
    lines.append(f"- TOTAL_FACTOR_COUNT: `{total}`")
    lines.append(f"- CAPTURED_FACTOR_OR_LABEL_COUNT: `{captured}`")
    lines.append(f"- OFFICIAL_CANDIDATE_COUNT: `{len(official_candidates)}`")
    lines.append(f"- OFFICIAL_CANDIDATE_CAPTURED_COUNT: `{official_candidate_captured}`")
    lines.append(f"- GATE_FACTOR_COUNT: `{len(gates)}`")
    lines.append(f"- GATE_SOURCE_CAPTURED_COUNT: `{gates_found}`")
    lines.append(f"- VALIDATION_LABEL_COUNT: `{len(labels)}`")
    lines.append(f"- VALIDATION_LABEL_CAPTURED_COUNT: `{labels_found}`")
    lines.append(f"- CSV_FILES_SCANNED: `{len(files)}`")
    lines.append("")
    lines.append("## 3. No-black-box rules")
    lines.append("")
    lines.append("1. Hard gates are not weights.")
    lines.append("2. Forward returns are validation labels, never decision-time inputs.")
    lines.append("3. Every official candidate factor needs explicit name, direction, weight range, source, and principle.")
    lines.append("4. Missing factor fields are not silently inferred.")
    lines.append("5. This module cannot change official decisions.")
    lines.append("")
    lines.append("## 4. Official candidate factor coverage")
    lines.append("")
    lines.append("| factor_name | current_weight | range | coverage_status | matched_columns |")
    lines.append("|---|---:|---:|---|---|")
    for r in official_candidate_coverage:
        rng = f"{r.get('min_weight','')} - {r.get('max_weight','')}"
        lines.append(
            f"| {r['factor_name']} | {r.get('current_weight','')} | {rng} | "
            f"{r['coverage_status']} | {r.get('matched_columns','')} |"
        )
    lines.append("")

    lines.append("## 5. Hard gates")
    lines.append("")
    lines.append("| factor_name | role | coverage_status | matched_columns |")
    lines.append("|---|---|---|---|")
    for r in gates:
        lines.append(
            f"| {r['factor_name']} | {r['factor_role']} | {r['coverage_status']} | {r.get('matched_columns','')} |"
        )
    lines.append("")

    lines.append("## 6. Validation labels")
    lines.append("")
    lines.append("| label | coverage_status | matched_columns |")
    lines.append("|---|---|---|")
    for r in labels:
        lines.append(
            f"| {r['factor_name']} | {r['coverage_status']} | {r.get('matched_columns','')} |"
        )
    lines.append("")

    lines.append("## 7. Missing official candidate fields")
    lines.append("")
    if missing_critical:
        for r in missing_critical:
            lines.append(f"- `{r['factor_name']}`: {r['coverage_status']}")
    else:
        lines.append("- None.")
    lines.append("")

    lines.append("## 8. Files scanned")
    lines.append("")
    lines.append("| rel_path | rows | columns |")
    lines.append("|---|---:|---:|")
    for fm in file_meta:
        lines.append(f"| {fm['rel_path']} | {fm['rows']} | {fm['columns']} |")
    lines.append("")

    lines.append("## 9. Outputs")
    lines.append("")
    lines.append(f"- FACTOR_REGISTRY: `{out_registry}`")
    lines.append(f"- COVERAGE_AUDIT: `{out_coverage}`")
    lines.append(f"- REPORT: `{out_report}`")
    lines.append(f"- READ_FIRST: `{out_read_first}`")
    lines.append("")
    lines.append("## 10. Next step")
    lines.append("")
    lines.append("Next recommended module: `V18.10B Factor Effectiveness Backtest`.")
    lines.append("")
    lines.append("V18.10B should only start after confirming that the required factor columns and forward-return labels are being captured.")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) >= 2 else Path(r"D:\us-tech-quant")
    stamp = now_stamp()

    state_dir = root / "state/v18/factor_registry"
    out_dir = root / "outputs/v18/factor_registry"
    ensure_dir(state_dir)
    ensure_dir(out_dir)

    out_registry = state_dir / "V18_CURRENT_FACTOR_REGISTRY.csv"
    out_coverage = out_dir / "V18_10A_CURRENT_FACTOR_COVERAGE_AUDIT.csv"
    out_report = out_dir / "V18_10A_CURRENT_FACTOR_REGISTRY_REPORT.md"
    out_read_first = out_dir / "V18_10A_READ_FIRST.txt"

    files = collect_csv_files(root)
    headers_by_file: Dict[Path, List[str]] = {}
    file_meta: List[Dict] = []

    for f in files:
        header, row_count = read_csv_header(f)
        if header:
            headers_by_file[f] = header
            try:
                rel = str(f.relative_to(root))
            except Exception:
                rel = str(f)
            file_meta.append(
                {
                    "rel_path": rel,
                    "rows": row_count,
                    "columns": len(header),
                    "headers_preview": ", ".join(header[:12]),
                }
            )

    registry_rows = factor_registry()

    registry_fields = [
        "factor_name",
        "factor_group",
        "factor_role",
        "direction",
        "current_weight",
        "min_weight",
        "max_weight",
        "official_status",
        "decision_impact",
        "data_source",
        "formula_note",
        "principle",
        "black_box_guard",
        "aliases",
    ]
    write_csv(out_registry, registry_rows, registry_fields)

    coverage_rows: List[Dict] = []
    for r in registry_rows:
        aliases = [x.strip() for x in str(r.get("aliases", "")).split("|") if x.strip()]
        matched_cols, matched_files = find_matches(headers_by_file, aliases)
        cr = dict(r)
        cr["coverage_status"] = coverage_status(r, matched_cols)
        cr["matched_columns"] = " | ".join(sorted(matched_cols))
        cr["matched_file_count"] = len(matched_files)
        cr["matched_files"] = " | ".join(sorted(matched_files))
        cr["scanned_file_count"] = len(files)
        coverage_rows.append(cr)

    coverage_fields = registry_fields + [
        "coverage_status",
        "matched_columns",
        "matched_file_count",
        "matched_files",
        "scanned_file_count",
    ]
    write_csv(out_coverage, coverage_rows, coverage_fields)

    report = make_report(
        root=root,
        stamp=stamp,
        registry_rows=registry_rows,
        coverage_rows=coverage_rows,
        files=files,
        file_meta=file_meta,
        out_registry=out_registry,
        out_coverage=out_coverage,
        out_report=out_report,
        out_read_first=out_read_first,
    )

    out_report.write_text(report, encoding="utf-8")

    total = len(registry_rows)
    captured = sum(1 for r in coverage_rows if str(r["coverage_status"]).endswith("CAPTURED"))
    official_candidate_count = sum(1 for r in registry_rows if r["official_status"] == "official_candidate")
    official_candidate_captured = sum(
        1
        for r in coverage_rows
        if r["official_status"] == "official_candidate"
        and r["coverage_status"] == "OFFICIAL_CANDIDATE_CAPTURED"
    )
    validation_label_count = sum(1 for r in coverage_rows if r["factor_group"] == "validation")
    validation_label_captured = sum(
        1
        for r in coverage_rows
        if r["factor_group"] == "validation"
        and r["coverage_status"] == "VALIDATION_LABEL_CAPTURED"
    )

    read_first = f"""V18.10A FACTOR REGISTRY + COVERAGE AUDIT READ FIRST

STATUS:
OK_FACTOR_REGISTRY_COVERAGE_AUDIT_READY

MODE:
NO_BLACK_BOX_FACTOR_GOVERNANCE

OFFICIAL_DECISION_IMPACT:
NONE

AUTO_WEIGHT_CHANGE:
DISABLED

AUTO_PROMOTION:
DISABLED

AUTO_TRADE:
DISABLED

TOTAL_FACTOR_COUNT:
{total}

CAPTURED_FACTOR_OR_LABEL_COUNT:
{captured}

OFFICIAL_CANDIDATE_COUNT:
{official_candidate_count}

OFFICIAL_CANDIDATE_CAPTURED_COUNT:
{official_candidate_captured}

VALIDATION_LABEL_COUNT:
{validation_label_count}

VALIDATION_LABEL_CAPTURED_COUNT:
{validation_label_captured}

CSV_FILES_SCANNED:
{len(files)}

FACTOR_REGISTRY:
{out_registry}

COVERAGE_AUDIT:
{out_coverage}

REPORT:
{out_report}

READ_FIRST:
{out_read_first}

NEXT_STEP:
Review missing official candidate fields first. Then build V18.10B Factor Effectiveness Backtest.
"""
    out_read_first.write_text(read_first, encoding="utf-8")

    print("")
    print("=== V18.10A FACTOR REGISTRY + COVERAGE AUDIT READY ===")
    print("STATUS: OK_FACTOR_REGISTRY_COVERAGE_AUDIT_READY")
    print("MODE: NO_BLACK_BOX_FACTOR_GOVERNANCE")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print(f"TOTAL_FACTOR_COUNT: {total}")
    print(f"OFFICIAL_CANDIDATE_COUNT: {official_candidate_count}")
    print(f"OFFICIAL_CANDIDATE_CAPTURED_COUNT: {official_candidate_captured}")
    print(f"VALIDATION_LABEL_COUNT: {validation_label_count}")
    print(f"VALIDATION_LABEL_CAPTURED_COUNT: {validation_label_captured}")
    print(f"CSV_FILES_SCANNED: {len(files)}")
    print(f"FACTOR_REGISTRY: {out_registry}")
    print(f"COVERAGE_AUDIT: {out_coverage}")
    print(f"REPORT: {out_report}")
    print(f"READ_FIRST: {out_read_first}")
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
