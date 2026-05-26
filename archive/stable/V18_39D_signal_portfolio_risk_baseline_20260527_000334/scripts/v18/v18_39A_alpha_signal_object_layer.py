#!/usr/bin/env python
"""V18.39A alpha signal object layer / LEAN-inspired signal normalization.

Read-only reporting layer. It converts current ranked candidate evidence into
normalized alpha signal objects for operator review and downstream research.
It does not modify ranking, candidates, factors, ledgers, account state,
broker/API logic, or order/trading logic.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


MODE = "READ_ONLY_ALPHA_SIGNAL_OBJECT_LAYER"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

OBJECT_COLUMNS = [
    "signal_id",
    "signal_date",
    "ticker",
    "company_name_en",
    "company_name_zh",
    "rank",
    "rank_bucket",
    "alpha_direction",
    "alpha_confidence",
    "confidence_score_numeric",
    "expected_horizon",
    "composite_candidate_score",
    "factor_score",
    "technical_timing_score",
    "overheat_status",
    "technical_tags",
    "factor_tags",
    "risk_tags",
    "data_quality_tags",
    "research_tags",
    "freeze_status",
    "latest_signal_freeze_count",
    "paper_tracking_status",
    "shadow_portfolio_membership_count",
    "benchmark_context",
    "forward_evidence_status",
    "operator_action_hint",
    "official_decision_impact",
    "auto_trade",
    "notes",
]

SUMMARY_COLUMNS = [
    "total_signal_count",
    "latest_signal_date",
    "latest_signal_freeze_count",
    "current_full_candidate_count",
    "current_top_candidate_count",
    "top20_signal_count",
    "top50_signal_count",
    "top100_signal_count",
    "long_candidate_count",
    "watch_count",
    "avoid_count",
    "unknown_count",
    "high_confidence_count",
    "medium_confidence_count",
    "low_confidence_count",
    "pending_forward_outcome_count",
    "in_latest_freeze_count",
    "missing_freeze_status_count",
    "severe_overheat_count",
    "data_quality_warning_count",
    "status",
    "next_recommended_step",
]

TAG_COLUMNS = ["signal_id", "ticker", "tag_type", "tag_value", "tag_source", "notes"]


PATHS = {
    "full_candidates": "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
    "top_candidates": "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
    "source_map": "outputs/v18/candidates/V18_CURRENT_CANDIDATE_SOURCE_MAP.csv",
    "freeze": "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "technical": "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
    "factor": "outputs/v18/factor_pack/V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv",
    "forward_detail": "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_DETAIL.csv",
    "experiment_registry": "outputs/v18/ops/V18_38B_RESEARCH_EXPERIMENT_REGISTRY.csv",
    "command_status": "outputs/v18/ops/V18_38C_R1_READ_FIRST.txt",
    "homepage": "outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md",
    "factor_audit": "outputs/v18/ops/V18_36C_R1_STRICT_FACTOR_IMPLEMENTATION_AUDIT.csv",
    "shadow_holdings": "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_HOLDINGS.csv",
    "shadow_snapshot": "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_DETAIL.csv",
}


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dirs(root: Path) -> None:
    for rel in ["outputs/v18/signals", "outputs/v18/read_center", "outputs/v18/ops"]:
        (root / rel).mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, df: pd.DataFrame, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if df.empty:
        out = pd.DataFrame(columns=columns)
    else:
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        out = df[columns]
    out.to_csv(path, index=False, encoding="utf-8")


def safe_read_csv(path: Path) -> tuple[pd.DataFrame, str]:
    if not path.exists():
        return pd.DataFrame(), "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return pd.read_csv(path, dtype=str, keep_default_na=False, encoding=enc), "OK"
        except Exception:
            continue
    return pd.DataFrame(), "READ_ERROR"


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            out[key.strip()] = val.strip()
    return out


def norm_col(name: str) -> str:
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def find_col(df: pd.DataFrame, *names: str) -> str | None:
    if df.empty:
        return None
    lookup = {norm_col(c): c for c in df.columns}
    for name in names:
        hit = lookup.get(norm_col(name))
        if hit is not None:
            return hit
    return None


def value(row: pd.Series, *names: str) -> str:
    lookup = {norm_col(k): k for k in row.index}
    for name in names:
        key = lookup.get(norm_col(name))
        if key is not None:
            return str(row.get(key, "")).strip()
    return ""


def to_float(raw: Any) -> float | None:
    try:
        text = str(raw).strip()
        if text == "":
            return None
        return float(text)
    except Exception:
        return None


def to_int(raw: Any) -> int | None:
    try:
        text = str(raw).strip()
        if text == "":
            return None
        return int(float(text))
    except Exception:
        return None


def latest_freeze(freeze: pd.DataFrame) -> tuple[str, set[str], int, dict[str, pd.Series]]:
    if freeze.empty:
        return "", set(), 0, {}
    date_col = find_col(freeze, "signal_date")
    ticker_col = find_col(freeze, "ticker")
    if not date_col or not ticker_col:
        return "", set(), 0, {}
    latest_date = sorted([d for d in freeze[date_col].astype(str).str.strip().unique() if d])[-1]
    latest = freeze[freeze[date_col].astype(str).str.strip() == latest_date].copy()
    latest["_ticker_norm"] = latest[ticker_col].astype(str).str.upper().str.strip()
    by_ticker = {str(row["_ticker_norm"]): row for _, row in latest.iterrows()}
    tickers = set(by_ticker)
    return latest_date, tickers, len(tickers), by_ticker


def dataframe_by_ticker(df: pd.DataFrame) -> dict[str, pd.Series]:
    col = find_col(df, "ticker", "yf_ticker", "symbol")
    if df.empty or not col:
        return {}
    out: dict[str, pd.Series] = {}
    for _, row in df.iterrows():
        ticker = str(row.get(col, "")).upper().strip()
        if ticker and ticker not in out:
            out[ticker] = row
    return out


def shadow_membership_counts(*dfs: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, set[str]] = {}
    for df in dfs:
        if df.empty:
            continue
        ticker_col = find_col(df, "ticker")
        portfolio_col = find_col(df, "portfolio_id", "motif_id", "snapshot_layer")
        if not ticker_col:
            continue
        for _, row in df.iterrows():
            ticker = str(row.get(ticker_col, "")).upper().strip()
            if not ticker:
                continue
            portfolio = str(row.get(portfolio_col, "shadow") if portfolio_col else "shadow").strip() or "shadow"
            counts.setdefault(ticker, set()).add(portfolio)
    return {ticker: len(items) for ticker, items in counts.items()}


def rank_bucket(rank: int | None) -> str:
    if rank is None:
        return "UNKNOWN"
    if rank <= 20:
        return "TOP20"
    if rank <= 50:
        return "TOP50"
    if rank <= 100:
        return "TOP100"
    if rank <= 318:
        return "FULL318"
    return "UNKNOWN"


def severe_overheat(text: str) -> bool:
    t = text.upper()
    return any(token in t for token in ["EXTREME", "SEVERE", "OVERHEAT_AVOID", "AVOID_CHASE"])


def add_tag(tags: list[dict[str, str]], signal_id: str, ticker: str, tag_type: str, tag_value: str, tag_source: str, notes: str = "") -> None:
    if not tag_value:
        return
    tags.append(
        {
            "signal_id": signal_id,
            "ticker": ticker,
            "tag_type": tag_type,
            "tag_value": tag_value,
            "tag_source": tag_source,
            "notes": notes,
        }
    )


def join_tags(tags: list[str]) -> str:
    cleaned = []
    for tag in tags:
        tag = str(tag).strip()
        if tag and tag not in cleaned:
            cleaned.append(tag)
    return ";".join(cleaned)


def forward_status(forward_detail: pd.DataFrame, command: dict[str, str]) -> str:
    if command.get("CURRENT_FAIL_BLOCKING_COUNT", "") not in {"", "0"}:
        return "UNKNOWN"
    text = " ".join(str(v) for v in command.values()).upper()
    if "PENDING" in text or command.get("EXPECTED_PENDING_COUNT", "0") not in {"", "0"}:
        return "PENDING_FORWARD_OUTCOME"
    if forward_detail.empty:
        return "UNKNOWN"
    status_col = find_col(forward_detail, "comparison_ready_status", "usability_status", "readiness_status")
    if not status_col:
        return "UNKNOWN"
    statuses = " ".join(forward_detail[status_col].astype(str).str.upper().tolist())
    if "READY" in statuses and "PENDING" not in statuses:
        return "READY"
    if "PARTIAL" in statuses:
        return "PARTIAL_READY"
    if "PENDING" in statuses:
        return "PENDING_FORWARD_OUTCOME"
    return "UNKNOWN"


def classify_signal(rank: int | None, freeze_status: str, overheat: str, score: float | None, data_quality_tags: list[str]) -> tuple[str, str, str, str]:
    if data_quality_tags or freeze_status != "IN_LATEST_FREEZE":
        return "UNKNOWN", "LOW", "", "RESEARCH_ONLY"
    if severe_overheat(overheat):
        return "AVOID", "LOW", "" if score is None else f"{score:.4f}", "DO_NOT_TRADE_SYSTEM_NOT_READY"
    if rank is not None and rank <= 20:
        return "LONG_CANDIDATE", "MEDIUM", "" if score is None else f"{score:.4f}", "REVIEW_TOP_CANDIDATE"
    if rank is not None and rank <= 100:
        return "WATCH", "LOW", "" if score is None else f"{score:.4f}", "WATCHLIST_ONLY"
    if rank is not None:
        return "WATCH", "LOW", "" if score is None else f"{score:.4f}", "RESEARCH_ONLY"
    return "UNKNOWN", "UNKNOWN", "", "RESEARCH_ONLY"


def build_objects(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], list[str]]:
    loaded: dict[str, tuple[pd.DataFrame, str]] = {name: safe_read_csv(root / rel) for name, rel in PATHS.items() if rel.endswith(".csv")}
    command_status = parse_kv(root / PATHS["command_status"])
    full, full_status = loaded["full_candidates"]
    top, top_status = loaded["top_candidates"]
    freeze, freeze_status_load = loaded["freeze"]
    technical, technical_status = loaded["technical"]
    factor, factor_status = loaded["factor"]
    forward_detail, _ = loaded["forward_detail"]
    experiment, experiment_status = loaded["experiment_registry"]
    shadow_holdings, shadow_holdings_status = loaded["shadow_holdings"]
    shadow_snapshot, shadow_snapshot_status = loaded["shadow_snapshot"]

    warnings: list[str] = []
    if full_status != "OK" or full.empty:
        raise RuntimeError("Current full ranked candidates cannot be read")
    for name, (_, status) in loaded.items():
        if name != "full_candidates" and status != "OK":
            warnings.append(f"{name}:{status}")

    tech_by_ticker = dataframe_by_ticker(technical)
    factor_by_ticker = dataframe_by_ticker(factor)
    latest_signal_date, freeze_tickers, latest_freeze_count, freeze_by_ticker = latest_freeze(freeze)
    shadow_counts = shadow_membership_counts(shadow_holdings, shadow_snapshot)
    global_forward_status = forward_status(forward_detail, command_status)
    benchmark_context = "SPY_QQQ_AVAILABLE" if latest_signal_date and {"SPY", "QQQ"}.issubset(freeze_tickers) else "UNKNOWN"

    rows: list[dict[str, Any]] = []
    tag_rows: list[dict[str, str]] = []
    top_count = len(top) if top_status == "OK" else 0
    rank_col = find_col(full, "rank", "source_rank")
    ticker_col = find_col(full, "ticker", "yf_ticker", "symbol")
    if not ticker_col:
        raise RuntimeError("Current full ranked candidates missing ticker column")

    for _, row in full.iterrows():
        ticker = str(row.get(ticker_col, "")).upper().strip()
        if not ticker:
            continue
        rank = to_int(row.get(rank_col, "")) if rank_col else None
        signal_date = latest_signal_date or str(row.get("latest_price_date", "")).strip()
        signal_id = f"V18_39A_{signal_date or 'UNKNOWN'}_{rank or 'NA'}_{ticker}"
        candidate_score = value(row, "composite_candidate_score")
        score_float = to_float(candidate_score)
        tech_row = tech_by_ticker.get(ticker)
        factor_row = factor_by_ticker.get(ticker)
        freeze_row = freeze_by_ticker.get(ticker)

        factor_score = ""
        if factor_row is not None:
            factor_score = value(factor_row, "factor_pack_score", "factor_score")
        elif freeze_row is not None:
            factor_score = value(freeze_row, "factor_score", "factor_pack_score")

        technical_score = ""
        if tech_row is not None:
            technical_score = value(tech_row, "technical_timing_score")
        elif freeze_row is not None:
            technical_score = value(freeze_row, "technical_timing_score")

        overheat = value(row, "overheat_status") or (value(tech_row, "technical_warning_label", "gamma_squeeze_risk_label") if tech_row is not None else "")
        freeze_membership = "IN_LATEST_FREEZE" if ticker in freeze_tickers else ("NOT_IN_LATEST_FREEZE" if latest_signal_date else "UNKNOWN")

        technical_tags = [
            value(row, "technical_status"),
            value(row, "pullback_status"),
            value(tech_row, "technical_signal") if tech_row is not None else "",
            value(tech_row, "rsi_status") if tech_row is not None else "",
            value(tech_row, "bb_status") if tech_row is not None else "",
        ]
        factor_tags = [
            value(row, "score_source_status"),
            value(factor_row, "shadow_side_hint") if factor_row is not None else "",
        ]
        risk_tags = [
            value(row, "event_risk_status"),
            overheat if severe_overheat(overheat) else "",
            value(tech_row, "gamma_squeeze_risk_label") if tech_row is not None else "",
            value(row, "execution_status"),
            value(row, "final_action"),
        ]
        research_tags = [
            global_forward_status,
            "V18_38B_EXPERIMENTS_REGISTERED" if experiment_status == "OK" and not experiment.empty else "",
            "SHADOW_PORTFOLIO_MEMBER" if shadow_counts.get(ticker, 0) > 0 else "",
        ]
        data_quality_tags: list[str] = []
        if candidate_score == "":
            data_quality_tags.append("MISSING_COMPOSITE_SCORE")
        if factor_score == "":
            data_quality_tags.append("MISSING_FACTOR_SCORE")
        if technical_score == "":
            data_quality_tags.append("MISSING_TECHNICAL_TIMING_SCORE")
        if freeze_membership == "UNKNOWN":
            data_quality_tags.append("MISSING_FREEZE_STATUS")
        if technical_status != "OK":
            data_quality_tags.append("TECHNICAL_SOURCE_NOT_AVAILABLE")
        if factor_status != "OK":
            data_quality_tags.append("FACTOR_SOURCE_NOT_AVAILABLE")

        direction, confidence, confidence_numeric, action_hint = classify_signal(rank, freeze_membership, overheat, score_float, data_quality_tags)
        if global_forward_status == "PENDING_FORWARD_OUTCOME" and action_hint == "REVIEW_TOP_CANDIDATE":
            action_hint = "REVIEW_TOP_CANDIDATE"

        row_out = {
            "signal_id": signal_id,
            "signal_date": signal_date,
            "ticker": ticker,
            "company_name_en": value(row, "company_name_en", "company_name"),
            "company_name_zh": value(row, "company_name_zh"),
            "rank": rank if rank is not None else "",
            "rank_bucket": rank_bucket(rank),
            "alpha_direction": direction,
            "alpha_confidence": confidence,
            "confidence_score_numeric": confidence_numeric,
            "expected_horizon": "1D_5D" if rank is not None and rank <= 20 else ("5D_20D" if rank is not None else "UNKNOWN"),
            "composite_candidate_score": candidate_score,
            "factor_score": factor_score,
            "technical_timing_score": technical_score,
            "overheat_status": overheat,
            "technical_tags": join_tags(technical_tags),
            "factor_tags": join_tags(factor_tags),
            "risk_tags": join_tags(risk_tags),
            "data_quality_tags": join_tags(data_quality_tags),
            "research_tags": join_tags(research_tags),
            "freeze_status": freeze_membership,
            "latest_signal_freeze_count": latest_freeze_count if latest_freeze_count else "",
            "paper_tracking_status": value(freeze_row, "forward_fill_status") if freeze_row is not None else "",
            "shadow_portfolio_membership_count": shadow_counts.get(ticker, 0),
            "benchmark_context": benchmark_context,
            "forward_evidence_status": global_forward_status,
            "operator_action_hint": action_hint,
            "official_decision_impact": "NONE",
            "auto_trade": "DISABLED",
            "notes": "Signal object normalization only; not a buy recommendation.",
        }
        rows.append(row_out)

        for tag in row_out["technical_tags"].split(";"):
            add_tag(tag_rows, signal_id, ticker, "TECHNICAL", tag, "candidate/technical_timing")
        for tag in row_out["factor_tags"].split(";"):
            add_tag(tag_rows, signal_id, ticker, "FACTOR", tag, "candidate/factor_pack")
        for tag in row_out["risk_tags"].split(";"):
            add_tag(tag_rows, signal_id, ticker, "RISK", tag, "candidate/technical_timing")
        for tag in row_out["data_quality_tags"].split(";"):
            add_tag(tag_rows, signal_id, ticker, "DATA_QUALITY", tag, "v18_39A_loader")
        for tag in row_out["research_tags"].split(";"):
            add_tag(tag_rows, signal_id, ticker, "RESEARCH", tag, "v18_38_research_stack")
        add_tag(tag_rows, signal_id, ticker, "FREEZE", freeze_membership, "signal_freeze_ledger")

    summary_context = {
        "latest_signal_date": latest_signal_date,
        "latest_signal_freeze_count": latest_freeze_count,
        "current_full_candidate_count": len(full),
        "current_top_candidate_count": top_count,
        "command_current_blocking_count": command_status.get("CURRENT_FAIL_BLOCKING_COUNT", ""),
        "daily_run_usable": command_status.get("DAILY_RUN_USABLE", ""),
        "forward_research_usable": command_status.get("FORWARD_RESEARCH_USABLE", ""),
        "load_warnings": warnings,
    }
    return pd.DataFrame(rows), pd.DataFrame(tag_rows), summary_context, warnings


def build_summary(objects: pd.DataFrame, context: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    total = len(objects)
    data_quality_warning_count = int(objects["data_quality_tags"].astype(str).str.strip().ne("").sum()) if not objects.empty else 0
    generated = total > 0
    if not generated:
        status = "FAIL_V18_39A_ALPHA_SIGNAL_OBJECT_LAYER_BLOCKED"
        next_step = "Fix current full ranked candidate source, then rerun V18.39A."
    elif warnings or data_quality_warning_count > 0:
        status = "WARN_V18_39A_ALPHA_SIGNAL_OBJECT_LAYER_REVIEW_NEEDED"
        next_step = "Review missing optional score/tag sources and use signal objects for research-only operator review."
    else:
        status = "OK_V18_39A_ALPHA_SIGNAL_OBJECT_LAYER_READY"
        next_step = "Signal objects are ready for downstream read-only portfolio/risk preview modules."

    return {
        "total_signal_count": total,
        "latest_signal_date": context.get("latest_signal_date", ""),
        "latest_signal_freeze_count": context.get("latest_signal_freeze_count", ""),
        "current_full_candidate_count": context.get("current_full_candidate_count", ""),
        "current_top_candidate_count": context.get("current_top_candidate_count", ""),
        "top20_signal_count": int((objects["rank_bucket"] == "TOP20").sum()) if not objects.empty else 0,
        "top50_signal_count": int(objects["rank"].apply(lambda x: to_int(x) is not None and to_int(x) <= 50).sum()) if not objects.empty else 0,
        "top100_signal_count": int(objects["rank"].apply(lambda x: to_int(x) is not None and to_int(x) <= 100).sum()) if not objects.empty else 0,
        "long_candidate_count": int((objects["alpha_direction"] == "LONG_CANDIDATE").sum()) if not objects.empty else 0,
        "watch_count": int((objects["alpha_direction"] == "WATCH").sum()) if not objects.empty else 0,
        "avoid_count": int((objects["alpha_direction"] == "AVOID").sum()) if not objects.empty else 0,
        "unknown_count": int((objects["alpha_direction"] == "UNKNOWN").sum()) if not objects.empty else 0,
        "high_confidence_count": int((objects["alpha_confidence"] == "HIGH").sum()) if not objects.empty else 0,
        "medium_confidence_count": int((objects["alpha_confidence"] == "MEDIUM").sum()) if not objects.empty else 0,
        "low_confidence_count": int((objects["alpha_confidence"] == "LOW").sum()) if not objects.empty else 0,
        "pending_forward_outcome_count": int((objects["forward_evidence_status"] == "PENDING_FORWARD_OUTCOME").sum()) if not objects.empty else 0,
        "in_latest_freeze_count": int((objects["freeze_status"] == "IN_LATEST_FREEZE").sum()) if not objects.empty else 0,
        "missing_freeze_status_count": int((objects["freeze_status"] == "UNKNOWN").sum()) if not objects.empty else 0,
        "severe_overheat_count": int(objects["overheat_status"].astype(str).apply(severe_overheat).sum()) if not objects.empty else 0,
        "data_quality_warning_count": data_quality_warning_count,
        "status": status,
        "next_recommended_step": next_step,
    }


def build_report(summary: dict[str, Any], context: dict[str, Any]) -> str:
    return f"""# V18.39A Alpha Signal Object Layer 报告

## 1. 今日结论
- 状态: {summary['status']}
- Signal object 数量: {summary['total_signal_count']}
- 最新 signal date: {summary['latest_signal_date']}
- 最新 freeze 数量: {summary['latest_signal_freeze_count']}
- 当前候选池数量: {summary['current_full_candidate_count']}

## 2. Alpha signal object 是什么
- 这是把 ranked candidates、factor score、technical timing、risk/data tags、freeze 和研究状态整理成统一信号对象的只读层。
- 它不是买入建议，不下单，不连接账户，不改变排名或权重。

## 3. 总体信号分布
- LONG_CANDIDATE: {summary['long_candidate_count']}
- WATCH: {summary['watch_count']}
- AVOID: {summary['avoid_count']}
- UNKNOWN: {summary['unknown_count']}

## 4. Top20 / Top50 / Top100 信号概览
- TOP20: {summary['top20_signal_count']}
- TOP50: {summary['top50_signal_count']}
- TOP100: {summary['top100_signal_count']}
- 当前 top candidate 数量: {summary['current_top_candidate_count']}

## 5. 置信度分布
- HIGH: {summary['high_confidence_count']}
- MEDIUM: {summary['medium_confidence_count']}
- LOW: {summary['low_confidence_count']}

## 6. 风险与过热标签
- Severe overheat 数量: {summary['severe_overheat_count']}
- Data quality warning 数量: {summary['data_quality_warning_count']}

## 7. Forward evidence 状态
- Pending forward outcome 数量: {summary['pending_forward_outcome_count']}
- Forward research usable: {context.get('forward_research_usable', '')}

## 8. 与 V18.38A/B/C 的关系
- V18.38A 提供 forward evidence readiness。
- V18.38B 提供 experiment registry / research context。
- V18.38C-R1 提供 current-vs-legacy command status scope。
- COMMAND_STATUS_CURRENT_BLOCKING_COUNT: {context.get('command_current_blocking_count', '')}
- DAILY_RUN_USABLE: {context.get('daily_run_usable', '')}

## 9. Safety / no-impact confirmation
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- RANKING_MODIFIED: FALSE
- FACTOR_WEIGHTS_MODIFIED: FALSE
- SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE
- PAPER_TRADING_LEDGER_MODIFIED: FALSE
- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE
- ACCOUNT_STATE_MODIFIED: FALSE
- BROKER_API_USED: FALSE
- ORDER_EXECUTION_USED: FALSE

## 10. 下一步建议
{summary['next_recommended_step']}
"""


def build_read_first(summary: dict[str, Any], context: dict[str, Any], run_id: str, generated_at: str) -> str:
    fields = {
        "STATUS": summary["status"],
        "MODE": MODE,
        "RUN_ID": run_id,
        "GENERATED_AT": generated_at,
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "RANKING_MODIFIED": "FALSE",
        "FACTOR_WEIGHTS_MODIFIED": "FALSE",
        "SIGNAL_FREEZE_LEDGER_MODIFIED": "FALSE",
        "PAPER_TRADING_LEDGER_MODIFIED": "FALSE",
        "SHADOW_PORTFOLIO_LEDGER_MODIFIED": "FALSE",
        "ACCOUNT_STATE_MODIFIED": "FALSE",
        "BROKER_API_USED": "FALSE",
        "ORDER_EXECUTION_USED": "FALSE",
        "TOTAL_SIGNAL_COUNT": summary["total_signal_count"],
        "LATEST_SIGNAL_DATE": summary["latest_signal_date"],
        "LATEST_SIGNAL_FREEZE_COUNT": summary["latest_signal_freeze_count"],
        "CURRENT_FULL_CANDIDATE_COUNT": summary["current_full_candidate_count"],
        "CURRENT_TOP_CANDIDATE_COUNT": summary["current_top_candidate_count"],
        "TOP20_SIGNAL_COUNT": summary["top20_signal_count"],
        "TOP50_SIGNAL_COUNT": summary["top50_signal_count"],
        "TOP100_SIGNAL_COUNT": summary["top100_signal_count"],
        "LONG_CANDIDATE_COUNT": summary["long_candidate_count"],
        "WATCH_COUNT": summary["watch_count"],
        "AVOID_COUNT": summary["avoid_count"],
        "UNKNOWN_COUNT": summary["unknown_count"],
        "HIGH_CONFIDENCE_COUNT": summary["high_confidence_count"],
        "MEDIUM_CONFIDENCE_COUNT": summary["medium_confidence_count"],
        "LOW_CONFIDENCE_COUNT": summary["low_confidence_count"],
        "PENDING_FORWARD_OUTCOME_COUNT": summary["pending_forward_outcome_count"],
        "IN_LATEST_FREEZE_COUNT": summary["in_latest_freeze_count"],
        "DATA_QUALITY_WARNING_COUNT": summary["data_quality_warning_count"],
        "COMMAND_STATUS_CURRENT_BLOCKING_COUNT": context.get("command_current_blocking_count", ""),
        "DAILY_RUN_USABLE": context.get("daily_run_usable", ""),
        "FORWARD_RESEARCH_USABLE": context.get("forward_research_usable", ""),
        "NEXT_RECOMMENDED_STEP": summary["next_recommended_step"],
    }
    return "\n".join(f"{key}: {value}" for key, value in fields.items()) + "\n"


def run(root: Path) -> int:
    ensure_dirs(root)
    run_id = f"V18_39A_ALPHA_SIGNAL_OBJECT_LAYER_{now_ts()}"
    generated_at = now_iso()
    try:
        objects, tags, context, warnings = build_objects(root)
        summary = build_summary(objects, context, warnings)
    except Exception as exc:
        context = {
            "latest_signal_date": "",
            "latest_signal_freeze_count": "",
            "current_full_candidate_count": "",
            "current_top_candidate_count": "",
            "command_current_blocking_count": "",
            "daily_run_usable": "",
            "forward_research_usable": "",
        }
        objects = pd.DataFrame(columns=OBJECT_COLUMNS)
        tags = pd.DataFrame(columns=TAG_COLUMNS)
        summary = {
            "total_signal_count": 0,
            "latest_signal_date": "",
            "latest_signal_freeze_count": "",
            "current_full_candidate_count": "",
            "current_top_candidate_count": "",
            "top20_signal_count": 0,
            "top50_signal_count": 0,
            "top100_signal_count": 0,
            "long_candidate_count": 0,
            "watch_count": 0,
            "avoid_count": 0,
            "unknown_count": 0,
            "high_confidence_count": 0,
            "medium_confidence_count": 0,
            "low_confidence_count": 0,
            "pending_forward_outcome_count": 0,
            "in_latest_freeze_count": 0,
            "missing_freeze_status_count": 0,
            "severe_overheat_count": 0,
            "data_quality_warning_count": 0,
            "status": "FAIL_V18_39A_ALPHA_SIGNAL_OBJECT_LAYER_BLOCKED",
            "next_recommended_step": f"Fix current candidate source/read error, then rerun V18.39A. Error: {type(exc).__name__}: {exc}",
        }

    signals_dir = root / "outputs/v18/signals"
    read_center = root / "outputs/v18/read_center"
    ops = root / "outputs/v18/ops"

    write_csv(signals_dir / "V18_39A_ALPHA_SIGNAL_OBJECTS.csv", objects, OBJECT_COLUMNS)
    write_csv(signals_dir / "V18_39A_ALPHA_SIGNAL_SUMMARY.csv", pd.DataFrame([summary]), SUMMARY_COLUMNS)
    write_csv(signals_dir / "V18_39A_ALPHA_SIGNAL_TAGS.csv", tags, TAG_COLUMNS)
    report = build_report(summary, context)
    write_text(read_center / "V18_39A_ALPHA_SIGNAL_OBJECT_LAYER_REPORT.md", report)
    write_text(read_center / "V18_CURRENT_ALPHA_SIGNAL_OBJECTS.md", report)
    write_text(ops / "V18_39A_READ_FIRST.txt", build_read_first(summary, context, run_id, generated_at))

    return 1 if str(summary["status"]).startswith("FAIL_") else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
