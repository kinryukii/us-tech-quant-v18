#!/usr/bin/env python
"""V18.37A LEAN-inspired strategy motif lab.

Read-only research layer. This script does not copy LEAN strategy code, place
orders, fetch data, mutate ranking weights, mutate candidates, or touch trading
state. It maps reusable strategy motifs to existing V18 evidence only.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Callable


AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FACTOR_WEIGHTS_MODIFIED = "FALSE"
FORBIDDEN_MODIFIED = "FALSE"

READY_REAL_EVIDENCE = "READY_REAL_EVIDENCE"
PROXY_RESEARCH_ONLY = "PROXY_RESEARCH_ONLY"
SHADOW_ONLY = "SHADOW_ONLY"
MISSING_REQUIRED_FACTOR = "MISSING_REQUIRED_FACTOR"

REAL_STATUS = "REAL_IMPLEMENTED"
PROXY_STATUS = "PROXY_IMPLEMENTED"
SHADOW_STATUSES = {"SHADOW_ONLY", "REPORT_ONLY", "DISCUSSED_ONLY"}
MISSING_STATUSES = {"MISSING", ""}


@dataclass(frozen=True)
class Motif:
    motif_id: str
    motif_name_cn: str
    motif_name_en: str
    description_cn: str
    lean_inspiration_cn: str
    required_factors: tuple[str, ...]
    optional_factors: tuple[str, ...]
    missing_concepts_cn: str
    candidate_selector: str
    target_count: int = 10


MOTIFS: tuple[Motif, ...] = (
    Motif(
        "VALUE_MOMENTUM",
        "价值动量",
        "Value + Momentum",
        "寻找已有动量证据支持、但仍需要估值因子确认的候选。",
        "借鉴 LEAN 示例中常见的基本面筛选叠加价格动量框架，只抽象研究主题，不复用代码逻辑。",
        ("VAL001", "F003", "F005"),
        ("F001", "VOL001"),
        "缺少真实估值/价值成长匹配因子，当前只能观察动量和现有综合排名。",
        "momentum",
    ),
    Motif(
        "QUALITY_MOMENTUM",
        "质量动量",
        "Quality + Momentum",
        "寻找已有动量证据支持、但仍需要质量因子确认的候选。",
        "借鉴质量筛选加趋势确认的策略设计母题，只映射到 V18 现有证据。",
        ("Q001", "F003", "F005"),
        ("Q002", "Q003", "Q004", "Q005", "Q006", "F001", "VOL001"),
        "缺少 QMJ、ROE、ROIC、利润率、自由现金流等真实质量因子。",
        "momentum",
    ),
    Motif(
        "LOW_VOL_MOMENTUM",
        "低波动动量",
        "Low Volatility + Momentum",
        "优先观察动量仍在、且波动惩罚较低或技术风险较低的候选。",
        "借鉴风险调整趋势策略的母题，用现有波动/过热代理证据做影子观察。",
        ("F003", "F005", "T005", "V003"),
        ("V001", "V002", "V004"),
        "真实 20D/60D 波动率与收益波动比仍是影子或代理证据。",
        "low_vol_momentum",
    ),
    Motif(
        "BREAKOUT_CONTINUATION",
        "突破延续",
        "Breakout Continuation",
        "观察布林、成交量、价格确认共同支持的突破延续候选。",
        "借鉴技术突破策略的设计母题，只使用 V18 已计算的技术计时和成交量确认字段。",
        ("T001", "T004", "VOL001", "VOL003"),
        ("F011", "V003"),
        "无需新增交易逻辑；若要实盘化仍需单独风控和订单层设计。",
        "breakout",
    ),
    Motif(
        "MEAN_REVERSION_CANDIDATE",
        "均值回归候选",
        "Mean Reversion Candidate",
        "观察短期回撤、布林下半区或下轨附近但中期趋势仍可接受的候选。",
        "借鉴回撤/均值回归策略母题，当前仅作为等待观察组。",
        ("T001", "T004", "F001"),
        ("VOL004",),
        "干缩回撤等更细成交量结构仍未实现。",
        "mean_reversion",
    ),
    Motif(
        "TECHNICAL_OVERHEAT_AVOIDANCE",
        "技术过热回避",
        "Technical Overheat Avoidance",
        "观察综合排名靠前且未出现明显过热惩罚或技术警告的候选。",
        "借鉴趋势策略中的过热过滤母题，只生成研究提示，不改变买卖判断。",
        ("T002", "T003", "T005", "T004"),
        ("OPT002", "OPT003", "OPT004"),
        "期权拥挤和隐波证据仍是代理，不作为官方交易门控。",
        "overheat_avoidance",
    ),
    Motif(
        "RISK_ADJUSTED_TOP_RANK",
        "风险调整高排名",
        "Risk Adjusted Top Rank",
        "从当前官方候选中观察综合分靠前、技术风险相对温和的研究组。",
        "借鉴风险调整排序母题，但不重算官方排名、不改权重。",
        ("F005", "T004", "T005"),
        ("V001", "V002", "V004"),
        "真实风险调整收益因子仍未进入官方排序。",
        "risk_adjusted_top_rank",
    ),
    Motif(
        "SECTOR_BALANCED_TOP_RANK",
        "行业均衡高排名",
        "Sector Balanced Top Rank",
        "理论上应按行业控制集中度，但当前候选文件没有可靠行业字段。",
        "借鉴组合构建中的行业均衡母题；本步骤只标记缺口。",
        ("F005", "SECTOR001"),
        (),
        "缺少行业/板块分类字段，不能构造真实行业均衡影子组。",
        "top_rank",
    ),
    Motif(
        "EQUAL_WEIGHT_TOP_N_BASELINE",
        "等权 Top N 基线",
        "Equal Weight Top N Baseline",
        "以当前候选排名前 N 作为等权观察基线；不生成订单、不改仓位。",
        "借鉴组合基线对照思想，仅用于研究观察。",
        ("F005",),
        (),
        "等权只是观察标签，不是账户或交易指令。",
        "top_rank",
    ),
    Motif(
        "SCORE_WEIGHTED_TOP_N_BASELINE",
        "分数加权 Top N 基线",
        "Score Weighted Top N Baseline",
        "以当前候选综合分前 N 作为分数加权观察基线；不改变任何官方权重。",
        "借鉴分数加权组合基线思想，只保留研究解释。",
        ("F005",),
        ("F003", "T004"),
        "分数加权只是观察标签，不是账户或交易指令。",
        "top_rank",
    ),
)

FIELD_EVIDENCE_BY_MOTIF: dict[str, tuple[str, ...]] = {
    "VALUE_MOMENTUM": ("F011_TS_MOMENTUM_60_120", "ret_60d", "ret_120d"),
    "QUALITY_MOMENTUM": ("F011_TS_MOMENTUM_60_120", "ret_60d", "ret_120d"),
    "LOW_VOL_MOMENTUM": ("volatility_penalty", "overheat_penalty", "F011_TS_MOMENTUM_60_120"),
    "BREAKOUT_CONTINUATION": ("breakout_confirmation_bonus", "F009_VOLUME_PRICE_CONFIRM", "volume_ratio_5_20"),
    "MEAN_REVERSION_CANDIDATE": ("F006_SHORT_REV_5D", "F007_PULLBACK_IN_UPTREND", "F012_TS_PULLBACK_REVERSAL", "pullback_status"),
    "TECHNICAL_OVERHEAT_AVOIDANCE": ("overheat_penalty", "technical_warning_label", "rsi_14", "kdj_status"),
    "RISK_ADJUSTED_TOP_RANK": ("composite_candidate_score", "technical_timing_score", "overheat_penalty"),
    "SECTOR_BALANCED_TOP_RANK": ("composite_candidate_score",),
    "EQUAL_WEIGHT_TOP_N_BASELINE": ("rank", "composite_candidate_score"),
    "SCORE_WEIGHTED_TOP_N_BASELINE": ("rank", "composite_candidate_score"),
}


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


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def first_present(row: dict[str, object], names: tuple[str, ...]) -> str:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return str(value)
    return ""


def semicolon(items: list[str] | tuple[str, ...]) -> str:
    return ";".join([str(item) for item in items if str(item).strip()]) or "NONE"


def choose_candidate_rows(root: Path) -> tuple[list[dict[str, str]], str, Path | None]:
    candidates = [
        root / "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
        root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
        root / "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        root / "outputs/v18/factor_pack/V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv",
    ]
    for path in candidates:
        rows = read_csv(path)
        if rows:
            return rows, path.name, path
    return [], "NONE", None


def index_by_ticker(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        ticker = str(row.get("ticker", "")).strip().upper()
        if ticker and ticker not in indexed:
            indexed[ticker] = row
    return indexed


def load_joined_universe(root: Path) -> tuple[list[dict[str, object]], str, Path | None, dict[str, int]]:
    candidate_rows, rank_source, rank_path = choose_candidate_rows(root)
    factor_rows = read_csv(root / "outputs/v18/factor_pack/V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv")
    timing_rows = read_csv(root / "outputs/v18/technical_timing/V18_35D_FULL_UNIVERSE_TECHNICAL_TIMING.csv")
    if not timing_rows:
        timing_rows = read_csv(root / "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv")

    factor_by_ticker = index_by_ticker(factor_rows)
    timing_by_ticker = index_by_ticker(timing_rows)
    joined: list[dict[str, object]] = []
    seen: set[str] = set()

    for position, row in enumerate(candidate_rows, start=1):
        ticker = str(row.get("ticker", "")).strip().upper()
        if not ticker:
            continue
        seen.add(ticker)
        merged: dict[str, object] = {"_rank_source": rank_source, "_rank_path": str(rank_path or ""), "_source_position": position}
        merged.update(factor_by_ticker.get(ticker, {}))
        merged.update(timing_by_ticker.get(ticker, {}))
        merged.update(row)
        merged["ticker"] = ticker
        joined.append(merged)

    if not joined:
        for position, row in enumerate(factor_rows, start=1):
            ticker = str(row.get("ticker", "")).strip().upper()
            if not ticker:
                continue
            merged = {"_rank_source": "V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv", "_rank_path": "", "_source_position": position}
            merged.update(row)
            merged.update(timing_by_ticker.get(ticker, {}))
            merged["ticker"] = ticker
            joined.append(merged)
            seen.add(ticker)

    counts = {
        "candidate_count": len(candidate_rows),
        "factor_pack_count": len(factor_rows),
        "technical_timing_count": len(timing_rows),
        "joined_count": len(joined),
    }
    return joined, rank_source, rank_path, counts


def load_audit(root: Path) -> dict[str, dict[str, str]]:
    rows = read_csv(root / "outputs/v18/ops/V18_36C_R1_STRICT_FACTOR_IMPLEMENTATION_AUDIT.csv")
    by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        factor_id = str(row.get("factor_id", "")).strip()
        if factor_id:
            by_id[factor_id] = row
    return by_id


def factor_label(factor_id: str, audit: dict[str, dict[str, str]]) -> str:
    row = audit.get(factor_id, {})
    name = row.get("factor_name", "") or factor_id
    status = row.get("strict_implementation_status", "") or "NOT_IN_STRICT_AUDIT"
    return f"{factor_id}:{name}:{status}"


def evidence_status_for(
    motif: Motif,
    audit: dict[str, dict[str, str]],
    available_fields: set[str],
) -> tuple[str, str, str, str]:
    required_statuses = []
    missing = []
    supporting = []
    optional = []
    for factor_id in motif.required_factors:
        row = audit.get(factor_id)
        status = (row or {}).get("strict_implementation_status", "")
        required_statuses.append(status)
        if status == REAL_STATUS:
            supporting.append(factor_label(factor_id, audit))
        elif status == PROXY_STATUS:
            optional.append(factor_label(factor_id, audit))
        else:
            missing.append(factor_label(factor_id, audit))
    for factor_id in motif.optional_factors:
        row = audit.get(factor_id)
        status = (row or {}).get("strict_implementation_status", "")
        if status in {REAL_STATUS, PROXY_STATUS} | SHADOW_STATUSES:
            optional.append(factor_label(factor_id, audit))

    field_evidence = [
        f"FIELD:{field}:CURRENT_OUTPUT"
        for field in FIELD_EVIDENCE_BY_MOTIF.get(motif.motif_id, ())
        if field in available_fields
    ]

    if missing:
        status = MISSING_REQUIRED_FACTOR
        readiness = "NOT_READY"
    elif any(item == PROXY_STATUS for item in required_statuses):
        status = PROXY_RESEARCH_ONLY
        readiness = "PROXY_ONLY"
    elif all(item == REAL_STATUS for item in required_statuses):
        status = READY_REAL_EVIDENCE
        readiness = "READY_FOR_PAPER_OBSERVATION"
    else:
        status = SHADOW_ONLY
        readiness = "SHADOW_OBSERVATION_ONLY"

    return status, readiness, semicolon(supporting + optional + field_evidence), semicolon(missing)


def numeric_values(rows: list[dict[str, object]], field: str) -> list[float]:
    vals = [to_float(row.get(field)) for row in rows]
    return [v for v in vals if v is not None]


def threshold(rows: list[dict[str, object]], field: str, default: float) -> float:
    vals = numeric_values(rows, field)
    if not vals:
        return default
    return median(vals)


def rank_sort_key(row: dict[str, object]) -> tuple[float, float, float]:
    rank = to_float(row.get("rank"))
    factor_rank = to_float(row.get("factor_pack_rank"))
    score = to_float(first_present(row, ("composite_candidate_score", "factor_pack_score", "technical_timing_score")), 0.0) or 0.0
    best_rank = rank if rank is not None else factor_rank if factor_rank is not None else 999999.0
    return (best_rank, -score, float(row.get("_source_position", 999999)))


def select_rows(selector: str, rows: list[dict[str, object]], target_count: int) -> list[dict[str, object]]:
    if not rows:
        return []

    f011_med = threshold(rows, "F011_TS_MOMENTUM_60_120", 50.0)
    vol_pen_med = threshold(rows, "volatility_penalty", 50.0)
    overheat_med = threshold(rows, "overheat_penalty", 50.0)
    volume_med = threshold(rows, "volume_ratio_5_20", 1.0)
    confirm_med = threshold(rows, "F009_VOLUME_PRICE_CONFIRM", 0.0)

    def momentum(row: dict[str, object]) -> bool:
        f011 = to_float(row.get("F011_TS_MOMENTUM_60_120"), 0.0) or 0.0
        ret60 = to_float(row.get("ret_60d"), 0.0) or 0.0
        ret120 = to_float(row.get("ret_120d"), 0.0) or 0.0
        return f011 >= f011_med or ret60 > 0 or ret120 > 0

    def low_vol_momentum(row: dict[str, object]) -> bool:
        vol_pen = to_float(row.get("volatility_penalty"), 0.0) or 0.0
        overheat = to_float(row.get("overheat_penalty"), 0.0) or 0.0
        return momentum(row) and vol_pen >= vol_pen_med and overheat >= overheat_med

    def breakout(row: dict[str, object]) -> bool:
        bonus = to_float(row.get("breakout_confirmation_bonus"), 0.0) or 0.0
        bb_status = str(row.get("bb_status", "") or row.get("technical_status", "")).upper()
        volume = to_float(row.get("volume_ratio_5_20"), 0.0) or 0.0
        confirm = to_float(row.get("F009_VOLUME_PRICE_CONFIRM"), 0.0) or 0.0
        return bonus > 0 or ("UPPER" in bb_status and volume >= volume_med) or confirm >= confirm_med

    def mean_reversion(row: dict[str, object]) -> bool:
        pullback = str(row.get("pullback_status", "") or row.get("shadow_side_hint", "") or row.get("bb_status", "")).upper()
        f007 = to_float(row.get("F007_PULLBACK_IN_UPTREND"), 0.0) or 0.0
        f012 = to_float(row.get("F012_TS_PULLBACK_REVERSAL"), 0.0) or 0.0
        return "PULLBACK" in pullback or "LOWER" in pullback or f007 >= 50.0 or f012 >= 50.0

    def overheat_avoidance(row: dict[str, object]) -> bool:
        warning = str(row.get("technical_warning_label", "") or row.get("overheat_status", "")).upper()
        rsi = to_float(row.get("rsi_14"), 50.0) or 50.0
        overheat = to_float(row.get("overheat_penalty"), 0.0) or 0.0
        return rsi < 70.0 and "OVERHEAT" not in warning and overheat >= overheat_med

    def risk_adjusted(row: dict[str, object]) -> bool:
        score = to_float(row.get("composite_candidate_score"), to_float(row.get("factor_pack_score"), 0.0)) or 0.0
        tech = to_float(row.get("technical_timing_score"), 50.0) or 50.0
        overheat = to_float(row.get("overheat_penalty"), 0.0) or 0.0
        return score > 0 and tech >= 50.0 and overheat >= overheat_med

    selectors: dict[str, Callable[[dict[str, object]], bool]] = {
        "momentum": momentum,
        "low_vol_momentum": low_vol_momentum,
        "breakout": breakout,
        "mean_reversion": mean_reversion,
        "overheat_avoidance": overheat_avoidance,
        "risk_adjusted_top_rank": risk_adjusted,
        "top_rank": lambda row: True,
    }
    predicate = selectors.get(selector, lambda row: True)
    selected = [row for row in rows if predicate(row)]
    if not selected:
        selected = list(rows)
    return sorted(selected, key=rank_sort_key)[:target_count]


def build_registry_rows(motif_evidence: dict[str, tuple[str, str, str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for motif in MOTIFS:
        evidence_status, readiness, supporting, missing = motif_evidence[motif.motif_id]
        rows.append(
            {
                "motif_id": motif.motif_id,
                "motif_name_cn": motif.motif_name_cn,
                "motif_name_en": motif.motif_name_en,
                "description_cn": motif.description_cn,
                "lean_inspiration_cn": motif.lean_inspiration_cn,
                "required_factors": semicolon(motif.required_factors),
                "optional_factors": semicolon(motif.optional_factors),
                "supporting_factors": supporting,
                "missing_factors": missing,
                "evidence_status": evidence_status,
                "research_readiness": readiness,
                "official_decision_impact": OFFICIAL_DECISION_IMPACT,
                "auto_trade": AUTO_TRADE,
                "auto_sell": AUTO_SELL,
            }
        )
    return rows


def build_factor_map_rows(motif_evidence: dict[str, tuple[str, str, str, str]], audit: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for motif in MOTIFS:
        evidence_status, readiness, _, _ = motif_evidence[motif.motif_id]
        for role, factors in [("REQUIRED", motif.required_factors), ("OPTIONAL", motif.optional_factors)]:
            for factor_id in factors:
                audit_row = audit.get(factor_id, {})
                rows.append(
                    {
                        "motif_id": motif.motif_id,
                        "motif_name_cn": motif.motif_name_cn,
                        "factor_role": role,
                        "factor_id": factor_id,
                        "factor_name": audit_row.get("factor_name", factor_id),
                        "strict_implementation_status": audit_row.get("strict_implementation_status", "NOT_IN_STRICT_AUDIT"),
                        "strict_affects_current_ranking": audit_row.get("strict_affects_current_ranking", "FALSE"),
                        "current_field_names": audit_row.get("current_field_names", ""),
                        "motif_evidence_status": evidence_status,
                        "motif_research_readiness": readiness,
                        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
                    }
                )
    return rows


def build_shadow_candidate_rows(
    motifs: tuple[Motif, ...],
    motif_evidence: dict[str, tuple[str, str, str, str]],
    joined_rows: list[dict[str, object]],
    rank_source: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for motif in motifs:
        evidence_status, readiness, supporting, missing = motif_evidence[motif.motif_id]
        selected = select_rows(motif.candidate_selector, joined_rows, motif.target_count)
        for shadow_rank, row in enumerate(selected, start=1):
            rows.append(
                {
                    "motif_id": motif.motif_id,
                    "motif_name_cn": motif.motif_name_cn,
                    "ticker": row.get("ticker", ""),
                    "shadow_rank": shadow_rank,
                    "rank_source": rank_source,
                    "official_rank": row.get("rank", row.get("factor_pack_rank", "")),
                    "composite_candidate_score": row.get("composite_candidate_score", ""),
                    "factor_pack_score": row.get("factor_pack_score", ""),
                    "technical_timing_score": row.get("technical_timing_score", ""),
                    "technical_status": row.get("technical_status", row.get("technical_signal", "")),
                    "bb_status": row.get("bb_status", ""),
                    "rsi_14": row.get("rsi_14", ""),
                    "kdj_status": row.get("kdj_status", ""),
                    "volume_ratio_5_20": row.get("volume_ratio_5_20", ""),
                    "overheat_penalty": row.get("overheat_penalty", ""),
                    "volatility_penalty": row.get("volatility_penalty", ""),
                    "supporting_factors": supporting,
                    "missing_factors": missing,
                    "evidence_status": evidence_status,
                    "research_readiness": readiness,
                    "official_decision_impact": OFFICIAL_DECISION_IMPACT,
                    "auto_trade": AUTO_TRADE,
                    "auto_sell": AUTO_SELL,
                    "notes": "RESEARCH_ONLY_SHADOW_GROUP_NO_ORDER_NO_RANKING_CHANGE",
                }
            )
    return rows


def build_summary_rows(
    registry_rows: list[dict[str, object]],
    shadow_rows: list[dict[str, object]],
    counts: dict[str, int],
    rank_source: str,
) -> list[dict[str, object]]:
    by_motif_count: dict[str, int] = {}
    for row in shadow_rows:
        motif_id = str(row.get("motif_id", ""))
        by_motif_count[motif_id] = by_motif_count.get(motif_id, 0) + 1
    rows: list[dict[str, object]] = []
    for row in registry_rows:
        rows.append(
            {
                "motif_id": row["motif_id"],
                "motif_name_cn": row["motif_name_cn"],
                "evidence_status": row["evidence_status"],
                "research_readiness": row["research_readiness"],
                "shadow_candidate_count": by_motif_count.get(str(row["motif_id"]), 0),
                "rank_source": rank_source,
                "current_full_candidate_count": counts["candidate_count"],
                "joined_research_universe_count": counts["joined_count"],
                "official_decision_impact": OFFICIAL_DECISION_IMPACT,
                "factor_weights_modified": FACTOR_WEIGHTS_MODIFIED,
                "forbidden_modified": FORBIDDEN_MODIFIED,
            }
        )
    return rows


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(item).replace("|", "/") for item in row) + " |")
    return "\n".join(out)


def top_tickers_for(shadow_rows: list[dict[str, object]], motif_id: str, limit: int = 5) -> str:
    tickers = [str(row.get("ticker", "")) for row in shadow_rows if row.get("motif_id") == motif_id]
    return ", ".join([t for t in tickers if t][:limit]) or "无"


def build_report(
    registry_rows: list[dict[str, object]],
    shadow_rows: list[dict[str, object]],
    counts: dict[str, int],
    rank_source: str,
) -> str:
    ready = [r for r in registry_rows if r["evidence_status"] == READY_REAL_EVIDENCE]
    proxy = [r for r in registry_rows if r["evidence_status"] == PROXY_RESEARCH_ONLY]
    missing = [r for r in registry_rows if r["evidence_status"] == MISSING_REQUIRED_FACTOR]
    shadow = [r for r in registry_rows if r["evidence_status"] == SHADOW_ONLY]

    summary_table = md_table(
        ["分组", "数量"],
        [
            ["可用真实证据", len(ready)],
            ["仅代理研究", len(proxy)],
            ["仅影子观察", len(shadow)],
            ["缺少必需因子", len(missing)],
            ["候选输入数量", counts["candidate_count"]],
            ["研究合并宇宙数量", counts["joined_count"]],
        ],
    )
    motif_table = md_table(
        ["Motif", "中文名", "证据状态", "研究可用性", "Top tickers"],
        [
            [
                row["motif_id"],
                row["motif_name_cn"],
                row["evidence_status"],
                row["research_readiness"],
                top_tickers_for(shadow_rows, str(row["motif_id"])),
            ]
            for row in registry_rows
        ],
    )

    details: list[str] = []
    by_id = {motif.motif_id: motif for motif in MOTIFS}
    for row in registry_rows:
        motif = by_id[str(row["motif_id"])]
        details.append(f"### {motif.motif_id}：{motif.motif_name_cn}")
        details.append(f"- 含义：{motif.description_cn}")
        details.append(f"- LEAN 启发：{motif.lean_inspiration_cn}")
        details.append(f"- 当前支持因子：{row['supporting_factors']}")
        details.append(f"- 缺失/不足：{row['missing_factors'] if row['missing_factors'] != 'NONE' else motif.missing_concepts_cn}")
        details.append(f"- 研究状态：{row['evidence_status']} / {row['research_readiness']}")
        details.append(f"- 影子候选前列：{top_tickers_for(shadow_rows, motif.motif_id)}")
        details.append("")

    return "\n".join(
        [
            "# V18.37A LEAN-Inspired Strategy Motif Lab",
            "",
            f"生成时间：{now_iso()}",
            "",
            "本报告是受 LEAN/QuantConnect 常见策略设计方式启发的研究层：提炼“价值+动量、质量+动量、突破延续、均值回归、风险调整”等策略母题，并映射到当前 V18 已有因子、技术计时和候选排名证据。它不是 LEAN 策略代码复刻，也不包含 broker、API、订单或账户逻辑。",
            "",
            "明确边界：官方排名、交易决策、候选冻结、因子权重、纸交易账本、账户状态和执行逻辑均未改变。本步骤只生成研究/观察输出。",
            "",
            "## 安全状态",
            "",
            "- AUTO_TRADE: DISABLED",
            "- AUTO_SELL: DISABLED",
            "- OFFICIAL_DECISION_IMPACT: NONE",
            "- FACTOR_WEIGHTS_MODIFIED: FALSE",
            "- FORBIDDEN_MODIFIED: FALSE",
            f"- 候选来源：{rank_source}",
            "",
            "## 总览",
            "",
            summary_table,
            "",
            "## Motif 状态与候选",
            "",
            motif_table,
            "",
            "## 逐项解释",
            "",
            "\n".join(details).strip(),
            "",
            "## 操作员结论",
            "",
            "READY_REAL_EVIDENCE 可进入纸交易观察视角，但仍不代表自动买卖。PROXY_RESEARCH_ONLY 和 SHADOW_ONLY 只能作为研究提示。MISSING_REQUIRED_FACTOR 表示缺少关键因子，不能伪造分数或推断实盘可用性。",
            "",
        ]
    )


def build_read_first(
    status: str,
    registry_rows: list[dict[str, object]],
    counts: dict[str, int],
    warnings: list[str],
) -> str:
    def count_status(status_name: str) -> int:
        return sum(1 for row in registry_rows if row.get("evidence_status") == status_name)

    lines = [
        f"STATUS: {status}",
        "MODE: READ_ONLY_RESEARCH_MOTIF_LAB",
        f"GENERATED_AT: {now_iso()}",
        f"TOTAL_MOTIF_COUNT: {len(registry_rows)}",
        f"READY_MOTIF_COUNT: {count_status(READY_REAL_EVIDENCE)}",
        f"PROXY_ONLY_MOTIF_COUNT: {count_status(PROXY_RESEARCH_ONLY)}",
        f"SHADOW_ONLY_MOTIF_COUNT: {count_status(SHADOW_ONLY)}",
        f"MISSING_FACTOR_MOTIF_COUNT: {count_status(MISSING_REQUIRED_FACTOR)}",
        f"CURRENT_FULL_CANDIDATE_COUNT: {counts['candidate_count']}",
        f"JOINED_RESEARCH_UNIVERSE_COUNT: {counts['joined_count']}",
        f"AUTO_TRADE: {AUTO_TRADE}",
        f"AUTO_SELL: {AUTO_SELL}",
        f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"FACTOR_WEIGHTS_MODIFIED: {FACTOR_WEIGHTS_MODIFIED}",
        f"FORBIDDEN_MODIFIED: {FORBIDDEN_MODIFIED}",
        "CANDIDATE_ALIAS_MUTATION: FALSE",
        "FREEZE_LEDGER_MUTATION: FALSE",
        "PAPER_TRADING_LEDGER_MUTATION: FALSE",
        "BROKER_API_ORDER_CODE: DISABLED",
        f"WARNING_COUNT: {len(warnings)}",
    ]
    for warning in warnings:
        lines.append(f"WARNING: {warning}")
    return "\n".join(lines) + "\n"


def run(root: Path) -> int:
    ops_dir = root / "outputs/v18/ops"
    read_center_dir = root / "outputs/v18/read_center"
    warnings: list[str] = []

    joined_rows, rank_source, rank_path, counts = load_joined_universe(root)
    if not joined_rows:
        warnings.append("NO_CANDIDATE_OR_FACTOR_PACK_ROWS_AVAILABLE")
    if rank_path is None:
        warnings.append("NO_RANK_SOURCE_AVAILABLE")

    audit = load_audit(root)
    if not audit:
        warnings.append("STRICT_FACTOR_IMPLEMENTATION_AUDIT_NOT_FOUND_OR_EMPTY")

    available_fields = {field for row in joined_rows for field in row.keys()}
    motif_evidence = {motif.motif_id: evidence_status_for(motif, audit, available_fields) for motif in MOTIFS}
    registry_rows = build_registry_rows(motif_evidence)
    factor_map_rows = build_factor_map_rows(motif_evidence, audit)
    shadow_rows = build_shadow_candidate_rows(MOTIFS, motif_evidence, joined_rows, rank_source)
    summary_rows = build_summary_rows(registry_rows, shadow_rows, counts, rank_source)

    write_csv(
        ops_dir / "V18_37A_STRATEGY_MOTIF_REGISTRY.csv",
        registry_rows,
        [
            "motif_id",
            "motif_name_cn",
            "motif_name_en",
            "description_cn",
            "lean_inspiration_cn",
            "required_factors",
            "optional_factors",
            "supporting_factors",
            "missing_factors",
            "evidence_status",
            "research_readiness",
            "official_decision_impact",
            "auto_trade",
            "auto_sell",
        ],
    )
    write_csv(
        ops_dir / "V18_37A_STRATEGY_MOTIF_TO_FACTOR_MAP.csv",
        factor_map_rows,
        [
            "motif_id",
            "motif_name_cn",
            "factor_role",
            "factor_id",
            "factor_name",
            "strict_implementation_status",
            "strict_affects_current_ranking",
            "current_field_names",
            "motif_evidence_status",
            "motif_research_readiness",
            "official_decision_impact",
        ],
    )
    write_csv(
        ops_dir / "V18_37A_SHADOW_STRATEGY_CANDIDATES.csv",
        shadow_rows,
        [
            "motif_id",
            "motif_name_cn",
            "ticker",
            "shadow_rank",
            "rank_source",
            "official_rank",
            "composite_candidate_score",
            "factor_pack_score",
            "technical_timing_score",
            "technical_status",
            "bb_status",
            "rsi_14",
            "kdj_status",
            "volume_ratio_5_20",
            "overheat_penalty",
            "volatility_penalty",
            "supporting_factors",
            "missing_factors",
            "evidence_status",
            "research_readiness",
            "official_decision_impact",
            "auto_trade",
            "auto_sell",
            "notes",
        ],
    )
    write_csv(
        ops_dir / "V18_37A_LEAN_INSPIRED_STRATEGY_MOTIF_SUMMARY.csv",
        summary_rows,
        [
            "motif_id",
            "motif_name_cn",
            "evidence_status",
            "research_readiness",
            "shadow_candidate_count",
            "rank_source",
            "current_full_candidate_count",
            "joined_research_universe_count",
            "official_decision_impact",
            "factor_weights_modified",
            "forbidden_modified",
        ],
    )

    report = build_report(registry_rows, shadow_rows, counts, rank_source)
    write_text(read_center_dir / "V18_37A_LEAN_INSPIRED_STRATEGY_MOTIF_LAB_REPORT.md", report)
    write_text(read_center_dir / "V18_CURRENT_LEAN_INSPIRED_STRATEGY_LAB.md", report)

    status = "OK" if joined_rows else "WARN_NO_RESEARCH_UNIVERSE"
    read_first = build_read_first(status, registry_rows, counts, warnings)
    write_text(ops_dir / "V18_37A_READ_FIRST.txt", read_first)

    print(read_first, end="")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.37A read-only LEAN-inspired strategy motif lab")
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
