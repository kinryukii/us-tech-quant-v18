#!/usr/bin/env python
"""V18.37B shadow portfolio construction comparison.

Read-only research bridge inspired by LEAN-style portfolio construction. It
does not place orders, fetch data, mutate official ranking, mutate factor
weights, mutate candidate aliases, or touch trading/account ledgers.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FACTOR_WEIGHTS_MODIFIED = "FALSE"
FORBIDDEN_MODIFIED = "FALSE"

READY = "READY"
READY_WITH_FALLBACK = "READY_WITH_WEIGHTING_FALLBACK"
NOT_READY_NO_CANDIDATES = "NOT_READY_NO_CANDIDATES"
NOT_READY_MISSING_VOLATILITY_EVIDENCE = "NOT_READY_MISSING_VOLATILITY_EVIDENCE"
NOT_READY_MISSING_V18_37A_OUTPUT = "NOT_READY_MISSING_V18_37A_OUTPUT"
NOT_READY_NO_READY_MOTIFS = "NOT_READY_NO_READY_MOTIFS"


@dataclass(frozen=True)
class PortfolioSpec:
    portfolio_id: str
    portfolio_name_cn: str
    construction_method: str
    source_scope: str
    target_count: int | None
    weighting_method: str
    notes: str


BASE_SPECS: tuple[PortfolioSpec, ...] = (
    PortfolioSpec("TOP20_EQUAL_WEIGHT", "Top20 等权篮子", "TOP_N_EQUAL_WEIGHT", "CURRENT_RANKED_CANDIDATES", 20, "EQUAL_WEIGHT", "当前排名前 20 的等权研究篮子。"),
    PortfolioSpec("TOP50_EQUAL_WEIGHT", "Top50 等权篮子", "TOP_N_EQUAL_WEIGHT", "CURRENT_RANKED_CANDIDATES", 50, "EQUAL_WEIGHT", "当前排名前 50 的等权研究篮子。"),
    PortfolioSpec("TOP100_EQUAL_WEIGHT", "Top100 等权篮子", "TOP_N_EQUAL_WEIGHT", "CURRENT_RANKED_CANDIDATES", 100, "EQUAL_WEIGHT", "当前排名前 100 的等权研究篮子。"),
    PortfolioSpec("TOP20_SCORE_WEIGHTED", "Top20 分数加权篮子", "TOP_N_SCORE_WEIGHTED", "CURRENT_RANKED_CANDIDATES", 20, "SCORE_WEIGHTED", "优先使用 composite_candidate_score 的分数加权研究篮子。"),
    PortfolioSpec("TOP50_SCORE_WEIGHTED", "Top50 分数加权篮子", "TOP_N_SCORE_WEIGHTED", "CURRENT_RANKED_CANDIDATES", 50, "SCORE_WEIGHTED", "优先使用 composite_candidate_score 的分数加权研究篮子。"),
    PortfolioSpec("TOP100_SCORE_WEIGHTED", "Top100 分数加权篮子", "TOP_N_SCORE_WEIGHTED", "CURRENT_RANKED_CANDIDATES", 100, "SCORE_WEIGHTED", "优先使用 composite_candidate_score 的分数加权研究篮子。"),
    PortfolioSpec("LOW_VOL_ADJUSTED_TOP50", "低波动调整 Top50", "LOW_VOL_ADJUSTED_TOP_N", "CURRENT_RANKED_CANDIDATES_WITH_RISK_PROXY", 50, "SCORE_X_RISK_PROXY", "仅在存在可用波动或风险代理字段时生成权重。"),
    PortfolioSpec("MOTIF_READY_EQUAL_WEIGHT", "Ready Motif 等权篮子", "READY_MOTIF_EQUAL_WEIGHT", "V18_37A_READY_MOTIFS", None, "EQUAL_WEIGHT", "只使用 V18.37A 标记为 READY/READY_REAL_EVIDENCE 的 motif 候选。"),
    PortfolioSpec("MOTIF_READY_TOPN_BLEND", "Ready Motif TopN 混合篮子", "READY_MOTIF_TOPN_BLEND", "V18_37A_READY_MOTIFS", None, "EQUAL_MOTIF_THEN_EQUAL_NAME", "每个 ready motif 先等权，再聚合到股票层面。"),
)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def to_float(value: object, default: float | None = None) -> float | None:
    if value is None:
        return default
    text = str(value).strip()
    if text == "":
        return default
    try:
        return float(text)
    except ValueError:
        return default


def round_weight(value: float) -> float:
    return round(value, 10)


def choose_candidate_rows(root: Path) -> tuple[list[dict[str, str]], str]:
    paths = [
        root / "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
        root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
        root / "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        root / "outputs/v18/factor_pack/V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv",
    ]
    for path in paths:
        rows = read_csv(path)
        if rows:
            return rows, path.name
    return [], "NONE"


def index_by_ticker(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        ticker = str(row.get("ticker", "")).strip().upper()
        if ticker and ticker not in indexed:
            indexed[ticker] = row
    return indexed


def load_candidate_universe(root: Path) -> tuple[list[dict[str, object]], str, dict[str, int]]:
    candidate_rows, source = choose_candidate_rows(root)
    factor_rows = read_csv(root / "outputs/v18/factor_pack/V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv")
    timing_rows = read_csv(root / "outputs/v18/technical_timing/V18_35D_FULL_UNIVERSE_TECHNICAL_TIMING.csv")
    if not timing_rows:
        timing_rows = read_csv(root / "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv")

    factor_by_ticker = index_by_ticker(factor_rows)
    timing_by_ticker = index_by_ticker(timing_rows)
    joined: list[dict[str, object]] = []
    for pos, row in enumerate(candidate_rows, start=1):
        ticker = str(row.get("ticker", "")).strip().upper()
        if not ticker:
            continue
        merged: dict[str, object] = {"_source_position": pos, "_rank_source": source}
        merged.update(factor_by_ticker.get(ticker, {}))
        merged.update(timing_by_ticker.get(ticker, {}))
        merged.update(row)
        merged["ticker"] = ticker
        joined.append(merged)
    return joined, source, {"candidate_universe_count": len(joined), "factor_pack_count": len(factor_rows), "technical_timing_count": len(timing_rows)}


def source_rank(row: dict[str, object]) -> str:
    return str(row.get("rank") or row.get("factor_pack_rank") or row.get("_source_position") or "")


def score_value(row: dict[str, object]) -> float | None:
    for field in ("composite_candidate_score", "factor_pack_score", "technical_timing_score"):
        value = to_float(row.get(field))
        if value is not None and value > 0:
            return value
    return None


def risk_proxy_value(row: dict[str, object]) -> float | None:
    for field in ("volatility_penalty", "overheat_penalty", "technical_timing_score"):
        value = to_float(row.get(field))
        if value is not None and value > 0:
            return value
    return None


def has_usable_risk_proxy(rows: list[dict[str, object]]) -> bool:
    return any(risk_proxy_value(row) is not None for row in rows)


def select_top(rows: list[dict[str, object]], count: int | None) -> list[dict[str, object]]:
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            to_float(row.get("rank"), to_float(row.get("factor_pack_rank"), float(row.get("_source_position", 999999)))) or 999999,
            -(score_value(row) or 0.0),
            str(row.get("ticker", "")),
        ),
    )
    selected: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in sorted_rows:
        ticker = str(row.get("ticker", "")).strip().upper()
        if not ticker or ticker in seen:
            continue
        selected.append(row)
        seen.add(ticker)
        if count is not None and len(selected) >= count:
            break
    return selected


def normalize_weights(raw: dict[str, float]) -> dict[str, float]:
    total = sum(v for v in raw.values() if v > 0)
    if total <= 0:
        return {}
    positive = [(ticker, weight) for ticker, weight in raw.items() if weight > 0]
    weights: dict[str, float] = {}
    for idx, (ticker, weight) in enumerate(positive):
        if idx == len(positive) - 1:
            weights[ticker] = round_weight(1.0 - sum(weights.values()))
        else:
            weights[ticker] = round_weight(weight / total)
    return weights


def equal_weights(rows: list[dict[str, object]]) -> tuple[dict[str, float], bool, int]:
    if not rows:
        return {}, False, 0
    weight = round_weight(1.0 / len(rows))
    weights: dict[str, float] = {}
    for idx, row in enumerate(rows):
        ticker = str(row["ticker"])
        if idx == len(rows) - 1:
            weights[ticker] = round_weight(1.0 - sum(weights.values()))
        else:
            weights[ticker] = weight
    return weights, False, 0


def score_weights(rows: list[dict[str, object]]) -> tuple[dict[str, float], bool, int]:
    missing = sum(1 for row in rows if score_value(row) is None)
    if not rows or missing:
        weights, _, _ = equal_weights(rows)
        return weights, True, missing
    return normalize_weights({str(row["ticker"]): score_value(row) or 0.0 for row in rows}), False, 0


def low_vol_weights(rows: list[dict[str, object]]) -> tuple[dict[str, float], bool, int]:
    missing = sum(1 for row in rows if score_value(row) is None or risk_proxy_value(row) is None)
    if not rows or missing == len(rows):
        return {}, False, missing
    raw = {str(row["ticker"]): (score_value(row) or 1.0) * (risk_proxy_value(row) or 0.0) for row in rows}
    return normalize_weights(raw), False, missing


def row_for_holding(portfolio_id: str, row: dict[str, object], raw_weight: float, final_weight: float, weight_sum: float, readiness: str, motif_id: str = "") -> dict[str, object]:
    return {
        "portfolio_id": portfolio_id,
        "ticker": row.get("ticker", ""),
        "source_rank": source_rank(row),
        "motif_id": motif_id,
        "composite_candidate_score": row.get("composite_candidate_score", ""),
        "technical_timing_score": row.get("technical_timing_score", ""),
        "factor_pack_score": row.get("factor_pack_score", ""),
        "raw_weight": raw_weight,
        "final_weight": final_weight,
        "weight_sum_check": round_weight(weight_sum),
        "readiness_status": readiness,
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
    }


def build_standard_portfolio(spec: PortfolioSpec, universe: list[dict[str, object]]) -> tuple[list[dict[str, object]], str, bool, int]:
    selected = select_top(universe, spec.target_count)
    if not selected:
        return [], NOT_READY_NO_CANDIDATES, False, 0

    if spec.construction_method in {"TOP_N_EQUAL_WEIGHT", "FULL_CURRENT_EQUAL_WEIGHT"}:
        weights, fallback, missing_score = equal_weights(selected)
    elif spec.construction_method == "TOP_N_SCORE_WEIGHTED":
        weights, fallback, missing_score = score_weights(selected)
    elif spec.construction_method == "LOW_VOL_ADJUSTED_TOP_N":
        if not has_usable_risk_proxy(selected):
            return [], NOT_READY_MISSING_VOLATILITY_EVIDENCE, False, len(selected)
        weights, fallback, missing_score = low_vol_weights(selected)
    else:
        weights, fallback, missing_score = {}, False, 0

    readiness = READY_WITH_FALLBACK if fallback else READY
    weight_sum = sum(weights.values())
    rows = [row_for_holding(spec.portfolio_id, row, weights.get(str(row["ticker"]), 0.0), weights.get(str(row["ticker"]), 0.0), weight_sum, readiness) for row in selected if str(row["ticker"]) in weights]
    return rows, readiness, fallback, missing_score


def load_ready_motif_data(root: Path) -> tuple[list[dict[str, str]], set[str], int, int, bool]:
    registry_path = root / "outputs/v18/ops/V18_37A_STRATEGY_MOTIF_REGISTRY.csv"
    candidates_path = root / "outputs/v18/ops/V18_37A_SHADOW_STRATEGY_CANDIDATES.csv"
    registry = read_csv(registry_path)
    candidates = read_csv(candidates_path)
    if not registry or not candidates:
        return [], set(), 0, 0, False
    ready_ids = {
        row.get("motif_id", "")
        for row in registry
        if row.get("evidence_status") == "READY_REAL_EVIDENCE" or row.get("research_readiness") == "READY_FOR_PAPER_OBSERVATION"
    }
    proxy_count = sum(1 for row in registry if row.get("evidence_status") == "PROXY_RESEARCH_ONLY" or row.get("research_readiness") == "PROXY_ONLY")
    missing_count = sum(1 for row in registry if row.get("evidence_status") == "MISSING_REQUIRED_FACTOR" or row.get("research_readiness") == "NOT_READY")
    ready_candidates = [row for row in candidates if row.get("motif_id") in ready_ids]
    return ready_candidates, ready_ids, proxy_count, missing_count, True


def build_motif_equal(spec: PortfolioSpec, motif_rows: list[dict[str, str]], ready_ids: set[str], v37a_available: bool) -> tuple[list[dict[str, object]], str, bool, int]:
    if not v37a_available:
        return [], NOT_READY_MISSING_V18_37A_OUTPUT, False, 0
    if not ready_ids or not motif_rows:
        return [], NOT_READY_NO_READY_MOTIFS, False, 0
    by_ticker: dict[str, dict[str, object]] = {}
    motif_labels: dict[str, list[str]] = {}
    for row in motif_rows:
        ticker = str(row.get("ticker", "")).strip().upper()
        if not ticker or ticker in by_ticker:
            continue
        by_ticker[ticker] = dict(row)
        motif_labels[ticker] = [str(row.get("motif_id", ""))]
    selected = list(by_ticker.values())
    weights, fallback, missing_score = equal_weights(selected)
    weight_sum = sum(weights.values())
    rows = [
        row_for_holding(spec.portfolio_id, row, weights.get(str(row["ticker"]), 0.0), weights.get(str(row["ticker"]), 0.0), weight_sum, READY, ";".join(motif_labels.get(str(row["ticker"]), [])))
        for row in selected
    ]
    return rows, READY, fallback, missing_score


def build_motif_blend(spec: PortfolioSpec, motif_rows: list[dict[str, str]], ready_ids: set[str], v37a_available: bool, per_motif_limit: int = 10) -> tuple[list[dict[str, object]], str, bool, int]:
    if not v37a_available:
        return [], NOT_READY_MISSING_V18_37A_OUTPUT, False, 0
    if not ready_ids or not motif_rows:
        return [], NOT_READY_NO_READY_MOTIFS, False, 0
    rows_by_motif: dict[str, list[dict[str, str]]] = {}
    for row in motif_rows:
        motif_id = str(row.get("motif_id", ""))
        rows_by_motif.setdefault(motif_id, []).append(row)

    raw: dict[str, float] = {}
    representative: dict[str, dict[str, object]] = {}
    labels: dict[str, list[str]] = {}
    motif_weight = 1.0 / len(rows_by_motif)
    for motif_id, rows in rows_by_motif.items():
        selected = sorted(rows, key=lambda row: to_float(row.get("shadow_rank"), 999999) or 999999)[:per_motif_limit]
        if not selected:
            continue
        name_weight = motif_weight / len(selected)
        for row in selected:
            ticker = str(row.get("ticker", "")).strip().upper()
            if not ticker:
                continue
            raw[ticker] = raw.get(ticker, 0.0) + name_weight
            representative.setdefault(ticker, dict(row))
            labels.setdefault(ticker, []).append(motif_id)

    weights = normalize_weights(raw)
    weight_sum = sum(weights.values())
    holdings = [
        row_for_holding(spec.portfolio_id, representative[ticker], round_weight(raw[ticker]), weights[ticker], weight_sum, READY, ";".join(sorted(set(labels.get(ticker, [])))))
        for ticker in sorted(weights, key=lambda t: (-weights[t], t))
    ]
    return holdings, READY, False, 0


def diagnostics_for(portfolio_id: str, holdings: list[dict[str, object]], readiness: str, missing_score_count: int, proxy_excluded: int, missing_factor_excluded: int, candidate_count: int) -> dict[str, object]:
    tickers = [str(row.get("ticker", "")) for row in holdings]
    weights = [to_float(row.get("final_weight"), 0.0) or 0.0 for row in holdings]
    warning_count = 0
    if readiness != READY:
        warning_count += 1
    if weights and abs(sum(weights) - 1.0) > 0.0001:
        warning_count += 1
    return {
        "portfolio_id": portfolio_id,
        "duplicate_ticker_count": len(tickers) - len(set(tickers)),
        "weight_sum": round_weight(sum(weights)),
        "max_single_name_weight": round_weight(max(weights) if weights else 0.0),
        "min_single_name_weight": round_weight(min(weights) if weights else 0.0),
        "missing_score_count": missing_score_count,
        "missing_technical_count": sum(1 for row in holdings if str(row.get("technical_timing_score", "")).strip() == ""),
        "missing_factor_count": sum(1 for row in holdings if str(row.get("factor_pack_score", "")).strip() == ""),
        "proxy_motif_excluded_count": proxy_excluded,
        "missing_factor_motif_excluded_count": missing_factor_excluded,
        "candidate_universe_count": candidate_count,
        "portfolio_construction_warning_count": warning_count,
        "readiness_status": readiness,
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
    }


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("|", "/") for item in row) + " |")
    return "\n".join(lines)


def build_report(registry_rows: list[dict[str, object]], holdings: list[dict[str, object]], diagnostics: list[dict[str, object]], candidate_count: int) -> str:
    ready_count = sum(1 for row in registry_rows if str(row.get("readiness_status", "")).startswith("READY"))
    warning_count = sum(int(row.get("portfolio_construction_warning_count", 0) or 0) for row in diagnostics)
    by_portfolio: dict[str, list[dict[str, object]]] = {}
    for row in holdings:
        by_portfolio.setdefault(str(row.get("portfolio_id", "")), []).append(row)

    summary = md_table(
        ["指标", "数值"],
        [
            ["组合数量", len(registry_rows)],
            ["Ready 组合数量", ready_count],
            ["警告数量", warning_count],
            ["候选宇宙数量", candidate_count],
            ["持仓行数", len(holdings)],
        ],
    )
    registry_table = md_table(
        ["Portfolio", "中文名", "方法", "状态", "持仓数", "备注"],
        [[row["portfolio_id"], row["portfolio_name_cn"], row["construction_method"], row["readiness_status"], row["actual_holding_count"], row["notes"]] for row in registry_rows],
    )
    top_sections: list[str] = []
    for row in registry_rows:
        pid = str(row["portfolio_id"])
        if not str(row.get("readiness_status", "")).startswith("READY"):
            continue
        top = sorted(by_portfolio.get(pid, []), key=lambda item: -(to_float(item.get("final_weight"), 0.0) or 0.0))[:8]
        top_sections.append(f"### {pid}")
        top_sections.append(md_table(["Ticker", "Weight", "Rank", "Motif"], [[item.get("ticker", ""), item.get("final_weight", ""), item.get("source_rank", ""), item.get("motif_id", "")] for item in top]))
        top_sections.append("")

    return "\n".join(
        [
            "# V18.37B Shadow Portfolio Construction Comparison",
            "",
            f"生成时间：{now_iso()}",
            "",
            "本报告是受 LEAN/QuantConnect 组合构建思想启发的研究层，用当前 V18 候选排名和 V18.37A strategy motif 影子候选构造透明的影子组合。这里没有复制 LEAN 策略代码，也没有 broker、API、订单、账户或执行逻辑。",
            "",
            "明确边界：官方排名、因子权重、候选冻结、纸交易账本、账户状态和交易决策均未改变。本层只服务研究比较和未来纸交易归因观察。",
            "",
            "## 安全状态",
            "",
            "- AUTO_TRADE: DISABLED",
            "- AUTO_SELL: DISABLED",
            "- OFFICIAL_DECISION_IMPACT: NONE",
            "- FACTOR_WEIGHTS_MODIFIED: FALSE",
            "- FORBIDDEN_MODIFIED: FALSE",
            "",
            "## 总览",
            "",
            summary,
            "",
            "## 组合说明",
            "",
            "等权组合让每只股票权重相同，便于作为最朴素的基线。分数加权组合优先使用 composite_candidate_score，缺失时回退等权并标记 fallback。低波动调整组合只在存在 volatility_penalty、overheat_penalty 或技术风险代理时生成。Motif blend 只使用 V18.37A 中 READY/READY_REAL_EVIDENCE 的 motif，代理和缺失因子 motif 只进入诊断排除计数。",
            "",
            registry_table,
            "",
            "## Ready 组合 Top Holdings",
            "",
            "\n".join(top_sections).strip() or "无 Ready 组合。",
            "",
            "## 操作员结论",
            "",
            "这些组合都是影子组合，不是订单建议，不会改变官方候选、权重、冻结、纸交易或账户记录。可用于后续研究比较：等权 vs 分数加权 vs 风险代理调整 vs ready motif 混合。",
            "",
        ]
    )


def build_read_first(status: str, registry_rows: list[dict[str, object]], diagnostics: list[dict[str, object]], candidate_count: int, holding_count: int) -> str:
    ready_count = sum(1 for row in registry_rows if str(row.get("readiness_status", "")).startswith("READY"))
    warning_count = sum(1 for row in registry_rows if not str(row.get("readiness_status", "")).startswith("READY"))
    diagnostic_warning_count = sum(int(row.get("portfolio_construction_warning_count", 0) or 0) for row in diagnostics)
    return "\n".join(
        [
            f"STATUS: {status}",
            "MODE: READ_ONLY_SHADOW_PORTFOLIO_CONSTRUCTION",
            f"GENERATED_AT: {now_iso()}",
            f"TOTAL_PORTFOLIO_COUNT: {len(registry_rows)}",
            f"READY_PORTFOLIO_COUNT: {ready_count}",
            f"WARNING_PORTFOLIO_COUNT: {warning_count}",
            f"PORTFOLIO_CONSTRUCTION_WARNING_COUNT: {diagnostic_warning_count}",
            f"CANDIDATE_UNIVERSE_COUNT: {candidate_count}",
            f"TOTAL_HOLDING_ROWS: {holding_count}",
            f"AUTO_TRADE: {AUTO_TRADE}",
            f"AUTO_SELL: {AUTO_SELL}",
            f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
            f"FACTOR_WEIGHTS_MODIFIED: {FACTOR_WEIGHTS_MODIFIED}",
            f"FORBIDDEN_MODIFIED: {FORBIDDEN_MODIFIED}",
            "CANDIDATE_ALIAS_MUTATION: FALSE",
            "FREEZE_LEDGER_MUTATION: FALSE",
            "PAPER_TRADING_LEDGER_MUTATION: FALSE",
            "ACCOUNT_STATE_MUTATION: FALSE",
            "BROKER_API_ORDER_CODE: DISABLED",
            "",
        ]
    )


def run(root: Path) -> int:
    ops_dir = root / "outputs/v18/ops"
    read_center_dir = root / "outputs/v18/read_center"
    universe, rank_source, counts = load_candidate_universe(root)
    candidate_count = counts["candidate_universe_count"]

    full_id = f"FULL{candidate_count}_EQUAL_WEIGHT" if candidate_count else "FULL_CURRENT_EQUAL_WEIGHT"
    full_spec = PortfolioSpec(full_id, "全当前候选等权篮子", "FULL_CURRENT_EQUAL_WEIGHT", rank_source, None, "EQUAL_WEIGHT", "当前可用完整候选宇宙的等权研究篮子。")
    specs = list(BASE_SPECS[:3]) + [full_spec] + list(BASE_SPECS[3:])

    motif_rows, ready_motif_ids, proxy_excluded, missing_factor_excluded, v37a_available = load_ready_motif_data(root)
    holding_rows: list[dict[str, object]] = []
    registry_rows: list[dict[str, object]] = []
    diagnostics_rows: list[dict[str, object]] = []

    for spec in specs:
        fallback = False
        missing_score_count = 0
        if spec.construction_method.startswith("READY_MOTIF"):
            if spec.construction_method == "READY_MOTIF_EQUAL_WEIGHT":
                rows, readiness, fallback, missing_score_count = build_motif_equal(spec, motif_rows, ready_motif_ids, v37a_available)
            else:
                rows, readiness, fallback, missing_score_count = build_motif_blend(spec, motif_rows, ready_motif_ids, v37a_available)
        else:
            rows, readiness, fallback, missing_score_count = build_standard_portfolio(spec, universe)

        holding_rows.extend(rows)
        registry_rows.append(
            {
                "portfolio_id": spec.portfolio_id,
                "portfolio_name_cn": spec.portfolio_name_cn,
                "construction_method": spec.construction_method,
                "source_scope": spec.source_scope,
                "target_count": spec.target_count if spec.target_count is not None else "FULL_OR_MOTIF",
                "actual_holding_count": len(rows),
                "readiness_status": readiness,
                "weighting_method": spec.weighting_method,
                "weighting_fallback_used": str(fallback).upper(),
                "official_decision_impact": OFFICIAL_DECISION_IMPACT,
                "notes": spec.notes,
            }
        )
        diagnostics_rows.append(diagnostics_for(spec.portfolio_id, rows, readiness, missing_score_count, proxy_excluded if spec.construction_method.startswith("READY_MOTIF") else 0, missing_factor_excluded if spec.construction_method.startswith("READY_MOTIF") else 0, candidate_count))

    summary_rows = [
        {
            "portfolio_id": row["portfolio_id"],
            "portfolio_name_cn": row["portfolio_name_cn"],
            "construction_method": row["construction_method"],
            "readiness_status": row["readiness_status"],
            "actual_holding_count": row["actual_holding_count"],
            "weighting_method": row["weighting_method"],
            "weighting_fallback_used": row["weighting_fallback_used"],
            "candidate_universe_count": candidate_count,
            "official_decision_impact": OFFICIAL_DECISION_IMPACT,
            "factor_weights_modified": FACTOR_WEIGHTS_MODIFIED,
            "forbidden_modified": FORBIDDEN_MODIFIED,
        }
        for row in registry_rows
    ]

    registry_fields = ["portfolio_id", "portfolio_name_cn", "construction_method", "source_scope", "target_count", "actual_holding_count", "readiness_status", "weighting_method", "weighting_fallback_used", "official_decision_impact", "notes"]
    holding_fields = ["portfolio_id", "ticker", "source_rank", "motif_id", "composite_candidate_score", "technical_timing_score", "factor_pack_score", "raw_weight", "final_weight", "weight_sum_check", "readiness_status", "official_decision_impact"]
    diagnostic_fields = ["portfolio_id", "duplicate_ticker_count", "weight_sum", "max_single_name_weight", "min_single_name_weight", "missing_score_count", "missing_technical_count", "missing_factor_count", "proxy_motif_excluded_count", "missing_factor_motif_excluded_count", "candidate_universe_count", "portfolio_construction_warning_count", "readiness_status", "official_decision_impact"]
    summary_fields = ["portfolio_id", "portfolio_name_cn", "construction_method", "readiness_status", "actual_holding_count", "weighting_method", "weighting_fallback_used", "candidate_universe_count", "official_decision_impact", "factor_weights_modified", "forbidden_modified"]

    write_csv(ops_dir / "V18_37B_SHADOW_PORTFOLIO_CONSTRUCTION_SUMMARY.csv", summary_rows, summary_fields)
    write_csv(ops_dir / "V18_37B_SHADOW_PORTFOLIO_REGISTRY.csv", registry_rows, registry_fields)
    write_csv(ops_dir / "V18_37B_SHADOW_PORTFOLIO_HOLDINGS.csv", holding_rows, holding_fields)
    write_csv(ops_dir / "V18_37B_SHADOW_PORTFOLIO_WEIGHTS.csv", holding_rows, holding_fields)
    write_csv(ops_dir / "V18_37B_SHADOW_PORTFOLIO_DIAGNOSTICS.csv", diagnostics_rows, diagnostic_fields)

    report = build_report(registry_rows, holding_rows, diagnostics_rows, candidate_count)
    write_text(read_center_dir / "V18_37B_SHADOW_PORTFOLIO_CONSTRUCTION_REPORT.md", report)
    write_text(read_center_dir / "V18_CURRENT_SHADOW_PORTFOLIO_CONSTRUCTION.md", report)

    status = "OK" if candidate_count else "WARN_NO_CANDIDATE_UNIVERSE"
    read_first = build_read_first(status, registry_rows, diagnostics_rows, candidate_count, len(holding_rows))
    write_text(ops_dir / "V18_37B_READ_FIRST.txt", read_first)
    print(read_first, end="")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.37B read-only shadow portfolio construction comparison")
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
