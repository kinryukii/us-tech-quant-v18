#!/usr/bin/env python
"""V18.36C factor implementation audit.

Read-only audit that maps discussed factors/indicators/meta-factors to
IMPLEMENTED, SHADOW_ONLY, DISCUSSED_ONLY, or MISSING.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FACTOR_WEIGHTS_MODIFIED = "FALSE"
AUTO_WEIGHT_CHANGE = "DISABLED"
FORBIDDEN_MODIFIED = "FALSE"

STATUSES = {"IMPLEMENTED", "SHADOW_ONLY", "DISCUSSED_ONLY", "MISSING"}
RANKING_TERMS = [
    "composite_candidate_score",
    "factor_pack_score",
    "factor_pack_rank",
    "current_full_ranked_candidates",
    "current_ranked_candidates",
    "current_top_ranked_candidates",
    "rank eligible",
    "ranking",
]
GATE_TERMS = [
    "final_action",
    "event_risk_status",
    "buy_permission",
    "buyability",
    "execution_status",
    "daily_trust_level",
    "trade_readiness",
    "no-buy",
    "no_trade",
    "AUTO_TRADE: DISABLED".lower(),
]
SHADOW_TERMS = ["shadow", "backtest", "research", "attribution", "paper_trading", "audit", "read_center", "report"]
READ_CENTER_TERMS = ["read_center", "homepage", "daily_brief", "report.md", "read_first"]
OFFICIAL_OUTPUT_HINTS = [
    "V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
    "V18_CURRENT_RANKED_CANDIDATES.csv",
    "V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
    "V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv",
    "V18_35D_FULL_UNIVERSE_TECHNICAL_TIMING.csv",
    "V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv",
    "V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv",
    "V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
]


@dataclass(frozen=True)
class Factor:
    factor_id: str
    factor_name: str
    factor_group: str
    aliases: tuple[str, ...]
    expected_data_type: str
    extra_data_required: bool
    preferred_status_if_detected: str
    notes: str


def inventory() -> list[Factor]:
    rows = [
        ("F001", "WorldQuant / Factor Pack", "Factor Pack", ("worldquant", "factor pack", "factor_pack"), "derived price/volume factor pack", False, "IMPLEMENTED", "Current recompute and candidate scoring source."),
        ("F002", "F002", "Factor Pack", ("F002", "factor_002"), "legacy factor field", False, "SHADOW_ONLY", "Referenced in factor lab/research lineage."),
        ("F003", "factor_pack_score", "Factor Pack", ("factor_pack_score",), "numeric score", False, "IMPLEMENTED", "Current full-universe factor score field."),
        ("F004", "factor_pack_rank", "Factor Pack", ("factor_pack_rank",), "numeric rank", False, "IMPLEMENTED", "Current full-universe factor rank field."),
        ("F005", "composite_candidate_score", "Ranking", ("composite_candidate_score", "candidate_score"), "numeric score", False, "IMPLEMENTED", "Current candidate ranking score."),
        ("T001", "Bollinger Bands / BB", "Technical", ("bollinger", "bb_", "bb_status", "bb_percent_b", "bb_band"), "price technical", False, "IMPLEMENTED", "Technical timing indicator."),
        ("T002", "RSI", "Technical", ("rsi", "rsi_14", "rsi_status"), "price technical", False, "IMPLEMENTED", "Technical timing indicator."),
        ("T003", "KDJ", "Technical", ("kdj", "kdj_k", "kdj_d", "kdj_j"), "price technical", False, "IMPLEMENTED", "Technical timing indicator."),
        ("T004", "technical_timing_score", "Technical", ("technical_timing_score",), "numeric score", False, "IMPLEMENTED", "Current technical timing score."),
        ("T005", "overheat_penalty", "Technical", ("overheat_penalty", "overheat_status"), "numeric/status", False, "IMPLEMENTED", "Current technical/factor overheat field."),
        ("G001", "event risk gating", "Gate", ("event_risk_status", "event risk", "event_risk"), "status/gate", True, "IMPLEMENTED", "Current gate/status field."),
        ("G002", "earnings / cloud earnings event risk", "Gate", ("earnings", "cloud earnings", "earnings event"), "event calendar", True, "SHADOW_ONLY", "May appear in event risk reports/gates."),
        ("G003", "data freshness", "Gate", ("data_freshness_status", "freshness", "daily output freshness"), "status", False, "IMPLEMENTED", "Current daily freshness guard."),
        ("G004", "price freshness", "Gate", ("price_freshness", "price freshness", "price_asof_date", "latest_price_date"), "status/date", False, "IMPLEMENTED", "Current price data status."),
        ("G005", "coverage status", "Gate", ("coverage_status", "coverage", "scan_coverage"), "status", False, "IMPLEMENTED", "Rolling scan / universe coverage."),
        ("G006", "Daily Trust Level", "Gate", ("daily_trust_level", "trust level", "DAILY_TRUST_LEVEL"), "status", False, "IMPLEMENTED", "Read-center trust level."),
        ("P001", "forward attribution / paper trading", "Paper Trading", ("forward attribution", "paper_trading", "paper trading", "forward_return"), "paper outcome", False, "IMPLEMENTED", "Paper-only attribution and forward return layer."),
        ("M001", "Relative Strength vs QQQ", "Relative Strength", ("relative strength", "rs_vs_qqq", "relative_strength_vs_qqq", "qqq relative"), "benchmark price", False, "SHADOW_ONLY", "Can be derived from local prices and QQQ."),
        ("M002", "Distance to 20DMA", "Moving Average", ("distance_20dma", "20dma", "ma20", "20d ma", "sma_20"), "price technical", False, "DISCUSSED_ONLY", "Low-data-cost technical candidate."),
        ("M003", "Distance to 50DMA", "Moving Average", ("distance_50dma", "50dma", "ma50", "50d ma", "sma_50"), "price technical", False, "DISCUSSED_ONLY", "Low-data-cost technical candidate."),
        ("M004", "Distance to 200DMA", "Moving Average", ("distance_200dma", "200dma", "ma200", "200d ma", "sma_200"), "price technical", False, "DISCUSSED_ONLY", "Low-data-cost technical candidate."),
        ("M005", "Drawdown from 20D High", "Drawdown", ("drawdown_20d", "20d high", "from_20d_high"), "price technical", False, "DISCUSSED_ONLY", "Low-data-cost technical candidate."),
        ("M006", "Drawdown from 52W High", "Drawdown", ("drawdown_52w", "52w high", "52-week high", "from_52w_high"), "price technical", False, "DISCUSSED_ONLY", "Low-data-cost technical candidate."),
        ("M007", "Buy-Zone Distance", "Entry Quality", ("buy-zone", "buy_zone", "buy zone distance", "buy_zone_distance"), "price technical", False, "DISCUSSED_ONLY", "Low-data-cost entry quality candidate."),
        ("M008", "MA Alignment", "Moving Average", ("ma_alignment", "moving average alignment", "ma stack", "ma_alignment_score"), "price technical", False, "DISCUSSED_ONLY", "Low-data-cost trend quality candidate."),
        ("M009", "MA Slope", "Moving Average", ("ma_slope", "moving average slope", "slope_20", "slope_50"), "price technical", False, "DISCUSSED_ONLY", "Low-data-cost trend quality candidate."),
        ("M010", "Trend Stability", "Trend", ("trend_stability", "trend stability", "trend_quality"), "price technical", False, "DISCUSSED_ONLY", "Low-data-cost trend quality candidate."),
        ("V001", "20D Realized Volatility", "Volatility", ("realized_vol_20", "20d realized volatility", "rv20", "volatility_20"), "price volatility", False, "SHADOW_ONLY", "Likely appears in shadow volatility research."),
        ("V002", "60D Realized Volatility", "Volatility", ("realized_vol_60", "60d realized volatility", "rv60", "volatility_60"), "price volatility", False, "SHADOW_ONLY", "Likely appears in shadow volatility research."),
        ("V003", "Volatility Expansion / Compression", "Volatility", ("volatility expansion", "volatility compression", "vol expansion", "vol compression", "bb_squeeze"), "price volatility", False, "SHADOW_ONLY", "Can be inferred from BB squeeze/shadow vol work."),
        ("V004", "Return / Volatility Ratio", "Volatility", ("return volatility ratio", "return_volatility", "ret_vol_ratio", "sharpe"), "price volatility", False, "SHADOW_ONLY", "Research metric unless wired to ranking."),
        ("VOL001", "Volume Surge", "Volume", ("volume surge", "volume_ratio", "volume_ratio_5_20", "volume abnormal"), "volume technical", False, "IMPLEMENTED", "Current factor/technical volume ratio fields."),
        ("VOL002", "Up Volume Ratio", "Volume", ("up volume ratio", "up_volume", "upvolume"), "volume technical", False, "DISCUSSED_ONLY", "Requires directional volume derivation."),
        ("VOL003", "Breakout Volume Confirmation", "Volume", ("breakout volume", "breakout_confirmation", "volume_price_confirm"), "volume technical", False, "IMPLEMENTED", "Current factor pack includes volume/price confirmation."),
        ("VOL004", "Dry-Up Pullback", "Volume", ("dry-up", "dry_up_pullback", "volume dry", "pullback low volume"), "volume technical", False, "DISCUSSED_ONLY", "Low-data-cost pullback volume candidate."),
        ("GAP001", "Gap Up / Gap Down / Gap Size", "Gap", ("gap up", "gap down", "gap_size", "gap_pct"), "OHLC price", False, "DISCUSSED_ONLY", "Requires open/prev close logic."),
        ("BETA001", "Beta vs QQQ", "Beta", ("beta vs qqq", "beta_qqq", "qqq_beta"), "benchmark price", False, "DISCUSSED_ONLY", "Can be derived from local benchmark prices."),
        ("BETA002", "Beta vs SPY", "Beta", ("beta vs spy", "beta_spy", "spy_beta"), "benchmark price", False, "DISCUSSED_ONLY", "Can be derived from local benchmark prices."),
        ("BETA003", "BAB / Low Beta quality", "Beta", ("BAB", "betting against beta", "low beta"), "benchmark price/fundamental", False, "MISSING", "Research factor, not current official chain."),
        ("Q001", "QMJ", "Quality", ("QMJ", "quality minus junk", "quality_minus_junk"), "fundamental", True, "MISSING", "Requires fundamental data."),
        ("Q002", "ROE", "Quality", ("ROE", "return on equity"), "fundamental", True, "MISSING", "Requires fundamental data."),
        ("Q003", "ROIC", "Quality", ("ROIC", "return on invested capital"), "fundamental", True, "MISSING", "Requires fundamental data."),
        ("Q004", "Gross Margin", "Quality", ("gross margin", "gross_margin"), "fundamental", True, "MISSING", "Requires fundamental data."),
        ("Q005", "Operating Margin", "Quality", ("operating margin", "operating_margin"), "fundamental", True, "MISSING", "Requires fundamental data."),
        ("Q006", "FCF Margin", "Quality", ("fcf margin", "free cash flow margin", "fcf_margin"), "fundamental", True, "MISSING", "Requires fundamental data."),
        ("Q007", "Debt / EBITDA", "Quality", ("debt ebitda", "debt/ebitda", "debt_to_ebitda"), "fundamental", True, "MISSING", "Requires fundamental data."),
        ("GROW001", "Revenue Growth", "Growth", ("revenue growth", "revenue_growth"), "fundamental", True, "MISSING", "Requires fundamental data."),
        ("GROW002", "EPS Growth", "Growth", ("eps growth", "eps_growth"), "fundamental", True, "MISSING", "Requires fundamental data."),
        ("VAL001", "Valuation / Growth Match", "Valuation", ("valuation growth", "valuation/growth", "valuation_growth_match", "peg"), "fundamental", True, "MISSING", "Requires valuation/fundamental data."),
        ("OPT001", "Max Pain", "Options", ("max pain", "max_pain"), "options chain", True, "MISSING", "Requires options chain data."),
        ("OPT002", "Gamma Exposure / GEX", "Options", ("gamma exposure", "GEX", "gamma_squeeze", "gamma_squeeze_status"), "options chain", True, "SHADOW_ONLY", "Technical report reserves gamma fields; not official ranking."),
        ("OPT003", "Call / Put Ratio", "Options", ("call put ratio", "put_call_ratio", "call/put"), "options chain", True, "SHADOW_ONLY", "Technical report reserves put/call field; not official ranking."),
        ("OPT004", "IV Rank / IV Percentile", "Options", ("iv rank", "iv percentile", "iv_rank_proxy"), "options/volatility", True, "SHADOW_ONLY", "Reserved proxy field in technical timing."),
        ("OPT005", "IV-RV Spread", "Options", ("iv-rv", "iv rv spread", "iv_rv_spread"), "options/volatility", True, "MISSING", "Requires options IV plus realized volatility."),
        ("OPT006", "IV Crush Risk", "Options", ("iv crush", "iv_crush"), "options/events", True, "MISSING", "Requires IV and event calendar."),
        ("MACRO001", "High Yield Spread", "Macro", ("high yield spread", "hy spread", "high_yield_spread"), "macro credit", True, "MISSING", "Requires macro/credit data."),
        ("MACRO002", "Credit Spread", "Macro", ("credit spread", "credit_spread"), "macro credit", True, "MISSING", "Requires macro/credit data."),
        ("MACRO003", "Treasury Yield Regime", "Macro", ("treasury yield", "yield regime", "treasury_yield_regime"), "macro rates", True, "MISSING", "Requires rates data."),
        ("MACRO004", "DXY", "Macro", ("DXY", "dollar index", "dxy_regime"), "macro FX", True, "MISSING", "Requires macro FX data."),
        ("MACRO005", "FOMC / CPI / PCE proximity", "Macro Event", ("FOMC", "CPI", "PCE", "macro event proximity"), "macro calendar", True, "MISSING", "Requires macro calendar."),
        ("EV001", "continuous Event Risk Coefficient", "Event Risk", ("event risk coefficient", "event_risk_coefficient", "continuous_event_risk"), "event score", True, "MISSING", "Requires continuous event risk model."),
    ]
    return [Factor(a, b, c, tuple(d), e, f, g, h) for a, b, c, d, e, f, g, h in rows]


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def read_small_text(path: Path) -> str:
    try:
        if path.suffix.lower() == ".csv":
            with path.open("r", encoding="utf-8-sig", errors="ignore") as f:
                return f.readline().strip()
        data = path.read_text(encoding="utf-8-sig", errors="ignore")
        return data[:600000]
    except Exception:
        return ""


def collect_files(root: Path) -> list[dict[str, str]]:
    scan_roots = [root / "scripts/v18", root / "outputs/v18", root / "state/v18", root / "configs/v18"]
    allowed = {".py", ".ps1", ".csv", ".md", ".txt", ".json", ".yaml", ".yml"}
    files: list[dict[str, str]] = []
    for base in scan_roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in allowed:
                continue
            rel = path.relative_to(root).as_posix()
            rel_l = rel.lower()
            if "v18_36c_factor_implementation_audit" in rel_l or "v18_current_factor_implementation_audit" in rel_l or "v18_36c_read_first" in rel_l:
                continue
            body = read_small_text(path)
            files.append(
                {
                    "path": rel,
                    "path_l": rel_l,
                    "body": body,
                    "body_l": norm(body),
                    "kind": "script" if rel.startswith("scripts/") else "output" if rel.startswith("outputs/") else "state_config",
                    "headers": body if path.suffix.lower() == ".csv" else "",
                }
            )
    return files


def contains_term(text: str, term: str) -> bool:
    t = term.lower()
    if len(t) <= 4 and t.isalnum():
        return re.search(rf"(?<![a-z0-9_]){re.escape(t)}(?![a-z0-9_])", text) is not None
    return t in text


def match_factor(factor: Factor, files: list[dict[str, str]]) -> dict[str, object]:
    matched_scripts: list[str] = []
    matched_outputs: list[str] = []
    matched_state: list[str] = []
    fields: set[str] = set()
    ranking_evidence = False
    gate_evidence = False
    shadow_evidence = False
    read_center_only = False
    official_field_evidence = False
    official_current_chain_evidence = False
    evidence_bits: list[str] = []

    for item in files:
        hay_path = item["path_l"]
        hay_body = item["body_l"]
        hay = f"{hay_path} {hay_body}"
        term_hits = [term for term in factor.aliases if contains_term(hay, term)]
        if not term_hits:
            continue
        path = item["path"]
        if item["kind"] == "script":
            matched_scripts.append(path)
        elif item["kind"] == "output":
            matched_outputs.append(path)
        else:
            matched_state.append(path)
        if item["headers"]:
            header_cols = [c.strip() for c in item["headers"].split(",") if c.strip()]
            for col in header_cols:
                if any(contains_term(col.lower(), term) for term in factor.aliases):
                    fields.add(col)
        path_or_body = f"{hay_path} {hay_body[:4000]}"
        if any(term in path_or_body for term in RANKING_TERMS):
            ranking_evidence = True
        if any(term in path_or_body for term in GATE_TERMS):
            gate_evidence = True
        if any(term in path_or_body for term in SHADOW_TERMS):
            shadow_evidence = True
        if any(term in path_or_body for term in READ_CENTER_TERMS):
            read_center_only = True
        if item["headers"] and any(hint.lower() in hay_path for hint in OFFICIAL_OUTPUT_HINTS):
            official_field_evidence = True
        if item["kind"] == "script" and any(
            hint in hay_path
            for hint in [
                "v18_35d_full_universe_factor_technical_recompute",
                "v18_35e_online_backfill_candidate_adoption_bridge",
                "v18_35f_next_signal_freeze_expansion",
                "v18_34b_daily_output_freshness_guard",
                "v18_34c_trade_readiness_current_refresh",
                "v18_36a_paper_trading_forward_attribution",
                "v18_36b_paper_trading_forward_return_filler",
            ]
        ):
            official_current_chain_evidence = True
        evidence_bits.append(f"{path}: {', '.join(term_hits[:4])}")

    matched_scripts = sorted(set(matched_scripts))[:12]
    matched_outputs = sorted(set(matched_outputs))[:12]
    matched_state = sorted(set(matched_state))[:12]
    meaningful_evidence = bool(matched_scripts or matched_outputs or matched_state)

    affects_ranking = bool(meaningful_evidence and ranking_evidence and official_field_evidence and fields)
    affects_gate = bool(meaningful_evidence and gate_evidence and (official_field_evidence or official_current_chain_evidence or matched_state) and (fields or factor.factor_group == "Gate"))
    affects_shadow = bool(meaningful_evidence and shadow_evidence and not affects_ranking)
    affects_read_center_only = bool(read_center_only and not affects_ranking and not affects_gate)

    status = "MISSING"
    confidence = "LOW"
    missing_reason = ""
    if affects_ranking or affects_gate:
        status = "IMPLEMENTED"
        confidence = "HIGH" if official_field_evidence else "MEDIUM"
    elif meaningful_evidence and (affects_shadow or affects_read_center_only or factor.preferred_status_if_detected == "SHADOW_ONLY"):
        status = "SHADOW_ONLY"
        confidence = "MEDIUM"
    elif meaningful_evidence:
        status = "SHADOW_ONLY" if factor.preferred_status_if_detected == "SHADOW_ONLY" else factor.preferred_status_if_detected
        if status not in STATUSES:
            status = "SHADOW_ONLY"
        confidence = "MEDIUM"
    elif factor.preferred_status_if_detected == "DISCUSSED_ONLY" or not factor.extra_data_required:
        status = "DISCUSSED_ONLY"
        confidence = "MEDIUM"
        missing_reason = "Canonical inventory item; no current script/output/state field evidence found."
    else:
        status = "MISSING"
        confidence = "HIGH"
        missing_reason = "No meaningful implementation evidence found; extra data source likely required."

    if status == "IMPLEMENTED":
        action = "Keep monitored; no factor addition needed in this audit."
    elif status == "SHADOW_ONLY":
        action = "Review research evidence before considering any explicit ranking/gate proposal."
    elif status == "DISCUSSED_ONLY":
        action = "Prototype as shadow metric first; do not change official weights."
    else:
        action = "Defer until required data source and validation plan exist."

    return {
        "implementation_status": status,
        "confidence": confidence,
        "affects_current_ranking": str(affects_ranking).upper(),
        "affects_official_gate": str(affects_gate).upper(),
        "affects_shadow_research": str(affects_shadow).upper(),
        "affects_read_center_only": str(affects_read_center_only).upper(),
        "current_field_names": ";".join(sorted(fields)),
        "matched_scripts": ";".join(matched_scripts),
        "matched_outputs": ";".join(matched_outputs),
        "matched_state_or_config": ";".join(matched_state),
        "evidence_summary": " | ".join(evidence_bits[:8]) if evidence_bits else "No repo evidence found by V18.36C scanner.",
        "missing_reason": missing_reason,
        "recommended_next_action": action,
        "safety_note": "READ_ONLY_AUDIT; no ranking weights, candidates, freeze ledger, paper ledger, account state, broker/API/order logic modified.",
    }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def table(rows: list[dict[str, object]], cols: list[str], limit: int = 20) -> str:
    if not rows:
        return "| none |\n|---|"
    head = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|"
    body = []
    for row in rows[:limit]:
        vals = [str(row.get(c, "")).replace("\n", " ")[:120] for c in cols]
        body.append("| " + " | ".join(vals) + " |")
    return head + "\n" + "\n".join(body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()

    root = Path(args.root)
    ops = root / "outputs/v18/ops"
    read_center = root / "outputs/v18/read_center"
    audit_csv = ops / "V18_36C_FACTOR_IMPLEMENTATION_AUDIT.csv"
    summary_csv = ops / "V18_36C_FACTOR_IMPLEMENTATION_AUDIT_SUMMARY.csv"
    report_path = read_center / "V18_36C_FACTOR_IMPLEMENTATION_AUDIT_REPORT.md"
    current_report_path = read_center / "V18_CURRENT_FACTOR_IMPLEMENTATION_AUDIT.md"
    read_first_path = ops / "V18_36C_READ_FIRST.txt"
    warnings: list[str] = []
    fails: list[str] = []

    try:
        files = collect_files(root)
        factors = inventory()
        rows: list[dict[str, object]] = []
        for factor in factors:
            result = match_factor(factor, files)
            row = {
                "factor_id": factor.factor_id,
                "factor_name": factor.factor_name,
                "factor_group": factor.factor_group,
                "extra_data_required": str(factor.extra_data_required).upper(),
            }
            row.update(result)
            rows.append(row)
        if any(r["confidence"] == "LOW" for r in rows):
            warnings.append("LOW_CONFIDENCE_CLASSIFICATIONS_PRESENT")
    except Exception as exc:
        files = []
        factors = []
        rows = []
        fails.append(f"AUDIT_SCAN_FAILED: {exc}")

    fields = [
        "factor_id",
        "factor_name",
        "factor_group",
        "implementation_status",
        "confidence",
        "affects_current_ranking",
        "affects_official_gate",
        "affects_shadow_research",
        "affects_read_center_only",
        "extra_data_required",
        "current_field_names",
        "matched_scripts",
        "matched_outputs",
        "matched_state_or_config",
        "evidence_summary",
        "missing_reason",
        "recommended_next_action",
        "safety_note",
    ]

    try:
        write_csv(audit_csv, rows, fields)
        counts = {s: sum(1 for r in rows if r.get("implementation_status") == s) for s in STATUSES}
        summary = {
            "STATUS": "PENDING",
            "MODE": "READ_ONLY_AUDIT",
            "FACTOR_COUNT": len(rows),
            "IMPLEMENTED_COUNT": counts["IMPLEMENTED"],
            "SHADOW_ONLY_COUNT": counts["SHADOW_ONLY"],
            "DISCUSSED_ONLY_COUNT": counts["DISCUSSED_ONLY"],
            "MISSING_COUNT": counts["MISSING"],
            "AFFECTS_CURRENT_RANKING_COUNT": sum(1 for r in rows if r.get("affects_current_ranking") == "TRUE"),
            "AFFECTS_OFFICIAL_GATE_COUNT": sum(1 for r in rows if r.get("affects_official_gate") == "TRUE"),
            "EXTRA_DATA_REQUIRED_COUNT": sum(1 for r in rows if r.get("extra_data_required") == "TRUE"),
            "AUTO_TRADE": AUTO_TRADE,
            "AUTO_SELL": AUTO_SELL,
            "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
            "FACTOR_WEIGHTS_MODIFIED": FACTOR_WEIGHTS_MODIFIED,
            "AUTO_WEIGHT_CHANGE": AUTO_WEIGHT_CHANGE,
            "FORBIDDEN_MODIFIED": FORBIDDEN_MODIFIED,
            "WARNING_COUNT": len(warnings),
            "REPORT_PATH": str(report_path),
            "CURRENT_REPORT_PATH": str(current_report_path),
            "AUDIT_CSV_PATH": str(audit_csv),
        }
        if fails:
            status = "FAIL_V18_36C_FACTOR_IMPLEMENTATION_AUDIT_FAILED"
        elif warnings:
            status = "WARN_V18_36C_FACTOR_IMPLEMENTATION_AUDIT_REVIEW_NEEDED"
        else:
            status = "OK_V18_36C_FACTOR_IMPLEMENTATION_AUDIT_READY"
        summary["STATUS"] = status

        implemented = [r for r in rows if r.get("implementation_status") == "IMPLEMENTED"]
        ranking = [r for r in rows if r.get("affects_current_ranking") == "TRUE"]
        gates = [r for r in rows if r.get("affects_official_gate") == "TRUE" and r.get("affects_current_ranking") != "TRUE"]
        shadow = [r for r in rows if r.get("implementation_status") == "SHADOW_ONLY"]
        low_cost_missing = [r for r in rows if r.get("implementation_status") in {"MISSING", "DISCUSSED_ONLY"} and r.get("extra_data_required") == "FALSE"]
        high_cost_missing = [r for r in rows if r.get("implementation_status") in {"MISSING", "DISCUSSED_ONLY"} and r.get("extra_data_required") == "TRUE"]
        distribution = [
            {"status": k, "count": counts[k]}
            for k in ["IMPLEMENTED", "SHADOW_ONLY", "DISCUSSED_ONLY", "MISSING"]
        ]
        recommended = low_cost_missing[:8] + high_cost_missing[:5]
        report = f"""# V18.36C Factor Implementation Audit

## Executive Conclusion

V18.36C completed a read-only factor implementation audit across `scripts/v18`, `outputs/v18`, `state/v18`, and `configs/v18`. It maps every canonical factor to exactly one status: IMPLEMENTED, SHADOW_ONLY, DISCUSSED_ONLY, or MISSING. The audit did not change ranking formulas, factor weights, candidates, freeze ledgers, universe state, paper trading ledgers, account state, or trading logic.

## Status Distribution

{table(distribution, ["status", "count"], 10)}

## Factors That Affect Current Ranking

{table(ranking, ["factor_id", "factor_name", "factor_group", "current_field_names", "confidence"], 30)}

## Factors That Affect Official Gates But Not Ranking

{table(gates, ["factor_id", "factor_name", "factor_group", "current_field_names", "confidence"], 30)}

## Shadow-Only / Research-Only Factors

{table(shadow, ["factor_id", "factor_name", "factor_group", "matched_scripts", "matched_outputs"], 35)}

## Missing But Low-Data-Cost Candidates

{table(low_cost_missing, ["factor_id", "factor_name", "factor_group", "implementation_status", "recommended_next_action"], 35)}

## Missing And High-Data-Cost Candidates

{table(high_cost_missing, ["factor_id", "factor_name", "factor_group", "implementation_status", "recommended_next_action"], 35)}

## Recommended Next Development Order

{table(recommended, ["factor_id", "factor_name", "factor_group", "extra_data_required", "recommended_next_action"], 20)}

## Safety

- READ ONLY audit mode.
- No ranking formulas changed.
- No factor weights changed.
- No candidate files changed.
- No freeze ledgers changed.
- No universe state changed.
- No paper trading ledgers changed.
- No account state changed.
- No broker/API/order/auto-trade/auto-sell logic added.
- AUTO_TRADE DISABLED.
- AUTO_SELL DISABLED.
- OFFICIAL_DECISION_IMPACT NONE.
- FACTOR_WEIGHTS_MODIFIED FALSE.
- AUTO_WEIGHT_CHANGE DISABLED.
"""
        write_text(report_path, report)
        write_text(current_report_path, report)
        write_csv(summary_csv, [summary], list(summary.keys()))

        recommended_next_step = "Prototype low-data-cost DISCUSSED_ONLY factors in shadow-only outputs before any ranking proposal."
        read_first_lines = [
            f"STATUS: {status}",
            "MODE: READ_ONLY_AUDIT",
            f"FACTOR_COUNT: {len(rows)}",
            f"IMPLEMENTED_COUNT: {counts['IMPLEMENTED']}",
            f"SHADOW_ONLY_COUNT: {counts['SHADOW_ONLY']}",
            f"DISCUSSED_ONLY_COUNT: {counts['DISCUSSED_ONLY']}",
            f"MISSING_COUNT: {counts['MISSING']}",
            f"AFFECTS_CURRENT_RANKING_COUNT: {summary['AFFECTS_CURRENT_RANKING_COUNT']}",
            f"AFFECTS_OFFICIAL_GATE_COUNT: {summary['AFFECTS_OFFICIAL_GATE_COUNT']}",
            f"AUTO_TRADE: {AUTO_TRADE}",
            f"AUTO_SELL: {AUTO_SELL}",
            f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
            f"FACTOR_WEIGHTS_MODIFIED: {FACTOR_WEIGHTS_MODIFIED}",
            f"AUTO_WEIGHT_CHANGE: {AUTO_WEIGHT_CHANGE}",
            f"FORBIDDEN_MODIFIED: {FORBIDDEN_MODIFIED}",
            f"REPORT_PATH: {report_path}",
            f"CURRENT_REPORT_PATH: {current_report_path}",
            f"AUDIT_CSV_PATH: {audit_csv}",
            f"RECOMMENDED_NEXT_STEP: {recommended_next_step}",
        ]
        write_text(read_first_path, "\n".join(read_first_lines) + "\n")
    except Exception as exc:
        fails.append(f"OUTPUT_WRITE_FAILED: {exc}")
        status = "FAIL_V18_36C_FACTOR_IMPLEMENTATION_AUDIT_FAILED"
        try:
            write_text(
                read_first_path,
                "\n".join(
                    [
                        f"STATUS: {status}",
                        "MODE: READ_ONLY_AUDIT",
                        "FACTOR_COUNT: 0",
                        "IMPLEMENTED_COUNT: 0",
                        "SHADOW_ONLY_COUNT: 0",
                        "DISCUSSED_ONLY_COUNT: 0",
                        "MISSING_COUNT: 0",
                        "AFFECTS_CURRENT_RANKING_COUNT: 0",
                        "AFFECTS_OFFICIAL_GATE_COUNT: 0",
                        f"AUTO_TRADE: {AUTO_TRADE}",
                        f"AUTO_SELL: {AUTO_SELL}",
                        f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
                        f"FACTOR_WEIGHTS_MODIFIED: {FACTOR_WEIGHTS_MODIFIED}",
                        f"AUTO_WEIGHT_CHANGE: {AUTO_WEIGHT_CHANGE}",
                        f"FORBIDDEN_MODIFIED: {FORBIDDEN_MODIFIED}",
                        f"REPORT_PATH: {report_path}",
                        f"CURRENT_REPORT_PATH: {current_report_path}",
                        f"AUDIT_CSV_PATH: {audit_csv}",
                        "RECOMMENDED_NEXT_STEP: Fix audit output write failure before using this report.",
                    ]
                )
                + "\n",
            )
        except Exception:
            pass

    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
