#!/usr/bin/env python
"""V18.38B research experiment registry / Qlib-style tracking layer.

Read-only experiment registration and status reporting. This module consumes
existing V18 outputs/state only and does not modify ranking, weights, ledgers,
account state, broker/API, or order execution logic.
"""

from __future__ import annotations

import argparse
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


MODE = "READ_ONLY_RESEARCH_EXPERIMENT_REGISTRY"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
EXPECTED_HORIZONS = "1D;3D;5D;10D;20D"


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dirs(root: Path) -> None:
    for rel in ["outputs/v18/ops", "outputs/v18/read_center"]:
        (root / rel).mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, df: pd.DataFrame, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if df.empty:
        df = pd.DataFrame(columns=columns)
    else:
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        df = df[columns]
    df.to_csv(path, index=False, encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def mtime(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def safe_read_csv(path: Path) -> tuple[pd.DataFrame, str]:
    if not path.exists():
        return pd.DataFrame(), "MISSING"
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig"), "OK"
    except Exception as exc:
        return pd.DataFrame(), f"READ_ERROR: {type(exc).__name__}: {exc}"


def norm(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def find_col(df: pd.DataFrame, *names: str) -> str | None:
    if df.empty:
        return None
    lookup = {norm(c): c for c in df.columns}
    for name in names:
        hit = lookup.get(norm(name))
        if hit is not None:
            return hit
    return None


def val(row: pd.Series | dict[str, Any], *names: str, default: str = "") -> str:
    if isinstance(row, pd.Series):
        data = row.to_dict()
    else:
        data = row
    lookup = {norm(k): k for k in data.keys()}
    for name in names:
        key = lookup.get(norm(name))
        if key is not None:
            return str(data.get(key, "")).strip()
    return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value)))
    except Exception:
        return default


def bool_text(value: bool | None) -> str:
    if value is None:
        return "UNKNOWN"
    return "TRUE" if value else "FALSE"


def dependency_row(root: Path, name: str, path: Path, df: pd.DataFrame, load_status: str, important: bool) -> dict[str, Any]:
    exists = path.exists()
    if not exists:
        status = "WARN_MISSING_IMPORTANT_INPUT" if important else "WARN_MISSING_OPTIONAL_INPUT"
        notes = "missing; registry continues defensively"
    elif load_status != "OK":
        status = "WARN_READ_ERROR"
        notes = load_status
    elif path.suffix.lower() == ".csv" and df.empty:
        status = "WARN_EMPTY_CSV"
        notes = "CSV exists but has zero rows"
    else:
        status = "OK_USABLE"
        notes = "usable dependency"
    return {
        "dependency_name": name,
        "dependency_path": rel(root, path),
        "exists": bool_text(exists),
        "row_count": "" if path.suffix.lower() != ".csv" or not exists or load_status != "OK" else len(df),
        "modified_time": mtime(path),
        "dependency_status": status,
        "notes": notes,
    }


def exp_id(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text.upper()).strip("_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned


def readiness_from_comparison(status: str, matured: int, entry_count: int) -> str:
    s = str(status).upper()
    if entry_count <= 0:
        return "MISSING_INPUT"
    if matured > 0 and "READY" in s and "PARTIAL" not in s:
        return "READY"
    if matured > 0 or "PARTIAL" in s:
        return "PARTIAL_READY" if matured > 0 else "PENDING_FORWARD_OUTCOME"
    if "PENDING" in s:
        return "PENDING_FORWARD_OUTCOME"
    return "REGISTERED_NOT_YET_MEASURABLE"


def base_experiment(
    experiment_id: str,
    experiment_name: str,
    experiment_family: str,
    experiment_type: str,
    signal_source: str,
    candidate_scope: str,
    portfolio_construction_method: str,
    benchmark: str,
    entry_count: int | str,
    matured_horizon_count: int | str,
    any_forward_outcome_available: str,
    readiness_status: str,
    upstream_files: list[str],
    downstream_recommended_next_step: str,
    notes: str,
    current_forward_readiness: str = "",
    expected_horizons: str = EXPECTED_HORIZONS,
) -> dict[str, Any]:
    return {
        "experiment_id": experiment_id,
        "experiment_name": experiment_name,
        "experiment_family": experiment_family,
        "experiment_type": experiment_type,
        "signal_source": signal_source,
        "candidate_scope": candidate_scope,
        "portfolio_construction_method": portfolio_construction_method,
        "benchmark": benchmark,
        "expected_horizons": expected_horizons,
        "current_forward_readiness": current_forward_readiness,
        "entry_count": entry_count,
        "matured_horizon_count": matured_horizon_count,
        "any_forward_outcome_available": any_forward_outcome_available,
        "readiness_status": readiness_status,
        "upstream_files": ";".join(upstream_files),
        "downstream_recommended_next_step": downstream_recommended_next_step,
        "notes": notes,
    }


def comparison_lookup(detail: pd.DataFrame) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    if detail.empty:
        return out
    rtype = find_col(detail, "record_type")
    gtype = find_col(detail, "group_type")
    gname = find_col(detail, "group_name")
    if not rtype or not gtype or not gname:
        return out
    sub = detail[detail[rtype].astype(str).eq("COMPARISON_GROUP")]
    for _, row in sub.iterrows():
        out[(val(row, "group_type"), val(row, "group_name").upper())] = row.to_dict()
    return out


def add_paper_experiments(rows: list[dict[str, Any]], comp: dict[tuple[str, str], dict[str, Any]], root: Path) -> None:
    specs = [
        ("PAPER_TOP20", "Paper Top20 equal-weight", "Top20", "Top20", "TOP20_EQUAL_WEIGHT"),
        ("PAPER_TOP50", "Paper Top50 equal-weight", "Top50", "Top50", "TOP50_EQUAL_WEIGHT"),
        ("PAPER_TOP100", "Paper Top100 equal-weight", "Top100", "Top100", "TOP100_EQUAL_WEIGHT"),
        ("PAPER_FULL318", "Paper Full318 equal-weight observation", "Full318", "Full318", "FULL318_EQUAL_WEIGHT_OBSERVATION"),
    ]
    for eid, name, family, scope, method in specs:
        rec = comp.get(("PAPER_TOPN", scope.upper()), {})
        entry_count = as_int(rec.get("entry_count", 0))
        matured = as_int(rec.get("matured_forward_horizon_count", 0))
        readiness = readiness_from_comparison(str(rec.get("comparison_ready_status", "")), matured, entry_count)
        rows.append(base_experiment(
            eid,
            name,
            family,
            "PAPER_TRADING",
            "V18_DAILY_SIGNAL_FREEZE_LEDGER / V18_CURRENT_FULL_RANKED_CANDIDATES",
            scope,
            method,
            "SPY;QQQ",
            entry_count,
            matured,
            "TRUE" if matured > 0 else "FALSE",
            readiness,
            [
                "outputs/v18/paper_trading/V18_36A_PAPER_FORWARD_RETURNS.csv",
                "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_DETAIL.csv",
            ],
            "Wait for forward returns to mature, then compare net return and benchmark excess return.",
            "Registered from paper trading forward attribution evidence.",
            str(rec.get("comparison_ready_status", "")),
        ))


def add_benchmark_experiments(rows: list[dict[str, Any]], comp: dict[tuple[str, str], dict[str, Any]]) -> None:
    for bench in ["SPY", "QQQ"]:
        rec = comp.get(("BENCHMARK", bench), {})
        entry_count = as_int(rec.get("entry_count", 0), 1 if rec else 0)
        matured = as_int(rec.get("matured_forward_horizon_count", 0))
        readiness = readiness_from_comparison(str(rec.get("comparison_ready_status", "")), matured, entry_count)
        rows.append(base_experiment(
            f"BENCHMARK_{bench}",
            f"Benchmark {bench}",
            f"BENCHMARK_{bench}",
            "BENCHMARK",
            "benchmark evidence from paper/shadow output if available",
            bench,
            "BENCHMARK_BUY_AND_HOLD_REFERENCE",
            bench,
            entry_count,
            matured,
            "TRUE" if matured > 0 else "FALSE",
            readiness,
            [
                "outputs/v18/paper_trading/V18_36A_BENCHMARK_COMPARISON.csv",
                "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_DETAIL.csv",
            ],
            "Use only as reference once benchmark forward returns are filled.",
            "Benchmark experiment row; no trading action implied.",
            str(rec.get("comparison_ready_status", "")),
        ))


def add_shadow_experiments(rows: list[dict[str, Any]], registry: pd.DataFrame, comp: dict[tuple[str, str], dict[str, Any]]) -> None:
    if registry.empty:
        for key, rec in comp.items():
            if key[0] != "SHADOW_PORTFOLIO":
                continue
            name = key[1]
            entry_count = as_int(rec.get("entry_count", 0))
            matured = as_int(rec.get("matured_forward_horizon_count", 0))
            rows.append(base_experiment(
                f"SHADOW_PORTFOLIO_{exp_id(name)}",
                f"Shadow portfolio {name}",
                f"SHADOW_PORTFOLIO_{exp_id(name)}",
                "SHADOW_PORTFOLIO",
                "V18.37C snapshot detail",
                str(rec.get("group_name", name)),
                "UNKNOWN",
                "SPY;QQQ",
                entry_count,
                matured,
                "TRUE" if matured > 0 else "FALSE",
                readiness_from_comparison(str(rec.get("comparison_ready_status", "")), matured, entry_count),
                ["outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_DETAIL.csv"],
                "Wait for forward outcomes before league-table ranking.",
                "Discovered from V18.38A shadow comparison evidence.",
                str(rec.get("comparison_ready_status", "")),
            ))
        return

    for _, row in registry.iterrows():
        pid = val(row, "portfolio_id", "portfolio_name", default="UNKNOWN_PORTFOLIO")
        rec = comp.get(("SHADOW_PORTFOLIO", pid.upper()), {})
        entry_count = as_int(rec.get("entry_count", val(row, "actual_holding_count", default="0")))
        matured = as_int(rec.get("matured_forward_horizon_count", 0))
        readiness = readiness_from_comparison(str(rec.get("comparison_ready_status", "")), matured, entry_count)
        rows.append(base_experiment(
            f"SHADOW_PORTFOLIO_{exp_id(pid)}",
            val(row, "portfolio_name_cn", default=f"Shadow portfolio {pid}"),
            f"SHADOW_PORTFOLIO_{exp_id(pid)}",
            "SHADOW_PORTFOLIO",
            val(row, "source_scope", default="V18_CURRENT_FULL_RANKED_CANDIDATES"),
            val(row, "source_scope", default="UNKNOWN"),
            val(row, "construction_method", default="UNKNOWN"),
            "SPY;QQQ",
            entry_count,
            matured,
            "TRUE" if matured > 0 else "FALSE",
            readiness,
            [
                "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_REGISTRY.csv",
                "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_DETAIL.csv",
            ],
            "Wait for forward outcomes before shadow portfolio league table.",
            val(row, "notes", default="Registered from V18.37B/V18.37C shadow portfolio evidence."),
            str(rec.get("comparison_ready_status", val(row, "readiness_status", default=""))),
        ))


def add_motif_experiments(rows: list[dict[str, Any]], motif_registry: pd.DataFrame, motif_summary: pd.DataFrame) -> None:
    if motif_registry.empty and motif_summary.empty:
        return
    source = motif_registry if not motif_registry.empty else motif_summary
    summary_by_id: dict[str, dict[str, Any]] = {}
    if not motif_summary.empty:
        id_col = find_col(motif_summary, "motif_id")
        if id_col:
            for _, srow in motif_summary.iterrows():
                summary_by_id[val(srow, "motif_id")] = srow.to_dict()
    for _, row in source.iterrows():
        mid = val(row, "motif_id", default="UNKNOWN_MOTIF")
        srow = summary_by_id.get(mid, {})
        entry_count = as_int(val(srow, "shadow_candidate_count", default=val(row, "shadow_candidate_count", default="0")))
        readiness_raw = val(row, "research_readiness", default=val(srow, "research_readiness", default="UNKNOWN"))
        if "READY" in readiness_raw.upper() and "NOT_READY" not in readiness_raw.upper():
            readiness = "REGISTERED_NOT_YET_MEASURABLE"
        elif "PROXY" in readiness_raw.upper():
            readiness = "REGISTERED_NOT_YET_MEASURABLE"
        else:
            readiness = "MISSING_INPUT" if "NOT_READY" in readiness_raw.upper() else "UNKNOWN"
        rows.append(base_experiment(
            f"LEAN_MOTIF_{exp_id(mid)}",
            val(row, "motif_name_cn", "motif_name_en", default=mid),
            f"LEAN_MOTIF_{exp_id(mid)}",
            "STRATEGY_MOTIF",
            val(srow, "rank_source", default="V18_CURRENT_FULL_RANKED_CANDIDATES.csv"),
            "MOTIF_SHADOW_CANDIDATES",
            f"LEAN_INSPIRED_MOTIF:{mid}",
            "",
            entry_count,
            0,
            "FALSE",
            readiness,
            [
                "outputs/v18/ops/V18_37A_STRATEGY_MOTIF_REGISTRY.csv",
                "outputs/v18/ops/V18_37A_LEAN_INSPIRED_STRATEGY_MOTIF_SUMMARY.csv",
            ],
            "Use as research grouping; connect to forward outcomes only after motif-level performance evidence exists.",
            f"evidence_status={val(row, 'evidence_status', default=val(srow, 'evidence_status', default='UNKNOWN'))}; research_readiness={readiness_raw}",
            readiness_raw,
            expected_horizons="",
        ))


def add_pending_research(rows: list[dict[str, Any]], any_forward: str, factor_ready: str, shadow_ready: str) -> None:
    rows.append(base_experiment(
        "FACTOR_FORWARD_ATTRIBUTION_PENDING",
        "Factor forward attribution pending",
        "FACTOR_FORWARD_ATTRIBUTION_PENDING",
        "FACTOR_RESEARCH_PENDING",
        "V18.38A forward evidence dashboard",
        "PAPER_TOPN;FULL318",
        "ATTRIBUTION_ANALYSIS_PENDING",
        "SPY;QQQ",
        "",
        "",
        any_forward,
        "READY" if factor_ready == "TRUE" else "PENDING_FORWARD_OUTCOME",
        ["outputs/v18/ops/V18_38A_READ_FIRST.txt", "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_DETAIL.csv"],
        "Run factor attribution only after forward outcomes exist.",
        "Registry placeholder; no attribution computed here.",
    ))
    rows.append(base_experiment(
        "SHADOW_PORTFOLIO_LEAGUE_TABLE_PENDING",
        "Shadow portfolio league table pending",
        "SHADOW_PORTFOLIO_LEAGUE_TABLE_PENDING",
        "FACTOR_RESEARCH_PENDING",
        "V18.37C / V18.38A",
        "SHADOW_PORTFOLIO_*",
        "LEAGUE_TABLE_PENDING",
        "SPY;QQQ",
        "",
        "",
        any_forward,
        "READY" if shadow_ready == "TRUE" else "PENDING_FORWARD_OUTCOME",
        ["outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_FORWARD_READINESS.csv", "outputs/v18/ops/V18_38A_READ_FIRST.txt"],
        "Build league table only after shadow portfolio horizons mature.",
        "Registry placeholder; no league table ranking computed here.",
    ))
    rows.append(base_experiment(
        "TURNOVER_COST_SIMULATION_PENDING",
        "Turnover cost simulation pending",
        "TURNOVER_COST_SIMULATION_PENDING",
        "COST_RESEARCH_PENDING",
        "paper/shadow ledgers",
        "PAPER_TOPN;SHADOW_PORTFOLIO_*",
        "TURNOVER_COST_SIMULATION_PENDING",
        "",
        "",
        "",
        "UNKNOWN",
        "REGISTERED_NOT_YET_MEASURABLE",
        ["state/v18/paper_trading/V18_PAPER_TRADING_LEDGER.csv", "state/v18/shadow_portfolios/V18_SHADOW_PORTFOLIO_DAILY_SNAPSHOT_LEDGER.csv"],
        "Define cost model after enough forward snapshots and turnover events exist.",
        "Pending research family registered for future cost/slippage analysis.",
        expected_horizons="",
    ))


def parse_read_first(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def md_table(df: pd.DataFrame, cols: list[str], max_rows: int = 30) -> str:
    if df.empty:
        return "_无可用记录。_"
    small = df.copy()
    for col in cols:
        if col not in small.columns:
            small[col] = ""
    small = small[cols].head(max_rows).astype(str)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in small.iterrows():
        vals = [str(row[c]).replace("|", "/") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def build_report(read_first: dict[str, Any], registry: pd.DataFrame, deps: pd.DataFrame, summary: dict[str, Any]) -> str:
    paper = registry[registry["experiment_type"].eq("PAPER_TRADING")]
    shadow = registry[registry["experiment_type"].eq("SHADOW_PORTFOLIO")]
    motif = registry[registry["experiment_type"].eq("STRATEGY_MOTIF")]
    bench = registry[registry["experiment_type"].eq("BENCHMARK")]
    pending = registry[registry["experiment_type"].isin(["FACTOR_RESEARCH_PENDING", "COST_RESEARCH_PENDING"])]
    comparable = registry[registry["readiness_status"].isin(["READY", "PARTIAL_READY"])]
    waiting = registry[registry["readiness_status"].eq("PENDING_FORWARD_OUTCOME")]
    conclusion = "实验总账已生成；当前主要状态是等待 forward outcome 成熟。"
    if read_first["ANY_FORWARD_OUTCOME_AVAILABLE"] == "TRUE":
        conclusion = "已有部分 forward outcome，可开始做受限范围的实验比较。"
    if str(read_first["STATUS"]).startswith("WARN"):
        conclusion = "实验总账可用，但存在重要输入缺失或待复核项。"

    cols = ["experiment_id", "experiment_type", "entry_count", "matured_horizon_count", "readiness_status", "downstream_recommended_next_step"]
    lines = [
        "# V18.38B Research Experiment Registry / Qlib-Style Experiment Tracking Layer",
        "",
        "## 1. 今日结论",
        f"- STATUS: {read_first['STATUS']}",
        f"- RUN_ID: {read_first['RUN_ID']}",
        f"- 结论: {conclusion}",
        f"- TOTAL_EXPERIMENT_COUNT: {read_first['TOTAL_EXPERIMENT_COUNT']}",
        f"- ANY_FORWARD_OUTCOME_AVAILABLE: {read_first['ANY_FORWARD_OUTCOME_AVAILABLE']}",
        f"- READY_FOR_FACTOR_FORWARD_ATTRIBUTION: {read_first['READY_FOR_FACTOR_FORWARD_ATTRIBUTION']}",
        f"- READY_FOR_SHADOW_PORTFOLIO_LEAGUE_TABLE: {read_first['READY_FOR_SHADOW_PORTFOLIO_LEAGUE_TABLE']}",
        "",
        "## 2. 实验总览",
        md_table(pd.DataFrame([summary]), list(summary.keys()), 1),
        "",
        "## 3. Paper trading 实验",
        md_table(paper, cols, 20),
        "",
        "## 4. Shadow portfolio 实验",
        md_table(shadow, cols, 40),
        "",
        "## 5. LEAN-inspired motif 实验",
        md_table(motif, ["experiment_id", "experiment_name", "entry_count", "current_forward_readiness", "readiness_status", "notes"], 40),
        "",
        "## 6. Benchmark 实验",
        md_table(bench, cols, 20),
        "",
        "## 7. 当前 pending 的研究任务",
        md_table(pending, ["experiment_id", "experiment_type", "readiness_status", "upstream_files", "downstream_recommended_next_step"], 20),
        "",
        "## 8. 哪些实验已经可以比较",
        md_table(comparable, cols, 40),
        "",
        "## 9. 哪些实验还需要等待 forward outcome",
        md_table(waiting, cols, 40),
        "",
        "## 10. 下一步建议",
        f"- {read_first['NEXT_RECOMMENDED_STEP']}",
        "",
        "## 11. Safety / no-impact confirmation",
        f"- MODE: {read_first['MODE']}",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- RANKING_MODIFIED: FALSE",
        "- FACTOR_WEIGHTS_MODIFIED: FALSE",
        "- SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE",
        "- PAPER_TRADING_LEDGER_MODIFIED: FALSE",
        "- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE",
        "- ACCOUNT_STATE_MODIFIED: FALSE",
        "- BROKER_API_USED: FALSE",
        "- ORDER_EXECUTION_USED: FALSE",
        "",
        "### Dependency Snapshot",
        md_table(deps, ["dependency_name", "exists", "row_count", "dependency_status", "modified_time", "notes"], 50),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ensure_dirs(root)
    run_id = f"V18_38B_RESEARCH_EXPERIMENT_REGISTRY_{now_ts()}"
    generated_at = now_iso()

    paths = {
        "v38a_read_first": root / "outputs/v18/ops/V18_38A_READ_FIRST.txt",
        "v38a_summary": root / "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_SUMMARY.csv",
        "v38a_detail": root / "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_DETAIL.csv",
        "v38a_readiness": root / "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_READINESS.csv",
        "v36a_read_first": root / "outputs/v18/ops/V18_36A_READ_FIRST.txt",
        "paper_report": root / "outputs/v18/read_center/V18_CURRENT_PAPER_TRADING_FORWARD_ATTRIBUTION.md",
        "motif_summary": root / "outputs/v18/ops/V18_37A_LEAN_INSPIRED_STRATEGY_MOTIF_SUMMARY.csv",
        "motif_registry": root / "outputs/v18/ops/V18_37A_STRATEGY_MOTIF_REGISTRY.csv",
        "shadow_registry": root / "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_REGISTRY.csv",
        "shadow_holdings": root / "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_HOLDINGS.csv",
        "shadow_diagnostics": root / "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_DIAGNOSTICS.csv",
        "shadow_snapshot_summary": root / "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_SUMMARY.csv",
        "shadow_forward_readiness": root / "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_FORWARD_READINESS.csv",
        "full_candidates": root / "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
        "top_candidates": root / "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        "signal_freeze": root / "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
        "paper_ledger": root / "state/v18/paper_trading/V18_PAPER_TRADING_LEDGER.csv",
        "paper_positions": root / "state/v18/paper_trading/V18_PAPER_POSITIONS.csv",
        "paper_state": root / "state/v18/paper_trading/V18_PAPER_PORTFOLIO_STATE.csv",
        "shadow_ledger": root / "state/v18/shadow_portfolios/V18_SHADOW_PORTFOLIO_DAILY_SNAPSHOT_LEDGER.csv",
    }
    labels = {
        "v38a_read_first": "V18.38A READ_FIRST",
        "v38a_summary": "V18.38A forward evidence summary",
        "v38a_detail": "V18.38A forward evidence detail",
        "v38a_readiness": "V18.38A forward evidence readiness",
        "v36a_read_first": "V18.36A READ_FIRST",
        "paper_report": "current paper trading forward attribution report",
        "motif_summary": "V18.37A LEAN motif summary",
        "motif_registry": "V18.37A strategy motif registry",
        "shadow_registry": "V18.37B shadow portfolio registry",
        "shadow_holdings": "V18.37B shadow portfolio holdings",
        "shadow_diagnostics": "V18.37B shadow portfolio diagnostics",
        "shadow_snapshot_summary": "V18.37C shadow snapshot summary",
        "shadow_forward_readiness": "V18.37C shadow forward readiness",
        "full_candidates": "current Full318 candidates",
        "top_candidates": "current top candidates",
        "signal_freeze": "signal freeze ledger",
        "paper_ledger": "paper trading ledger",
        "paper_positions": "paper positions",
        "paper_state": "paper portfolio state",
        "shadow_ledger": "shadow portfolio snapshot ledger",
    }
    important = {
        "v38a_read_first",
        "v38a_detail",
        "motif_registry",
        "shadow_registry",
        "full_candidates",
        "top_candidates",
        "signal_freeze",
    }

    data: dict[str, pd.DataFrame] = {}
    load_status: dict[str, str] = {}
    dep_records: list[dict[str, Any]] = []
    for key, path in paths.items():
        if path.suffix.lower() == ".csv":
            data[key], load_status[key] = safe_read_csv(path)
        else:
            data[key], load_status[key] = pd.DataFrame(), "OK" if path.exists() else "MISSING"
        dep_records.append(dependency_row(root, labels[key], path, data[key], load_status[key], key in important))

    comp = comparison_lookup(data["v38a_detail"])
    v38a_rf = parse_read_first(paths["v38a_read_first"])
    any_forward = v38a_rf.get("ANY_FORWARD_OUTCOME_AVAILABLE", "UNKNOWN")
    factor_ready = v38a_rf.get("READY_FOR_FACTOR_FORWARD_ATTRIBUTION", "FALSE")
    shadow_ready = v38a_rf.get("READY_FOR_SHADOW_PORTFOLIO_LEAGUE_TABLE", "FALSE")

    rows: list[dict[str, Any]] = []
    add_paper_experiments(rows, comp, root)
    add_shadow_experiments(rows, data["shadow_registry"], comp)
    add_motif_experiments(rows, data["motif_registry"], data["motif_summary"])
    add_benchmark_experiments(rows, comp)
    add_pending_research(rows, any_forward, factor_ready, shadow_ready)

    registry_cols = [
        "experiment_id",
        "experiment_name",
        "experiment_family",
        "experiment_type",
        "signal_source",
        "candidate_scope",
        "portfolio_construction_method",
        "benchmark",
        "expected_horizons",
        "current_forward_readiness",
        "entry_count",
        "matured_horizon_count",
        "any_forward_outcome_available",
        "readiness_status",
        "upstream_files",
        "downstream_recommended_next_step",
        "notes",
    ]
    registry = pd.DataFrame(rows, columns=registry_cols)

    total = len(registry)
    paper_count = int(registry["experiment_type"].eq("PAPER_TRADING").sum()) if total else 0
    shadow_count = int(registry["experiment_type"].eq("SHADOW_PORTFOLIO").sum()) if total else 0
    motif_count = int(registry["experiment_type"].eq("STRATEGY_MOTIF").sum()) if total else 0
    benchmark_count = int(registry["experiment_type"].eq("BENCHMARK").sum()) if total else 0
    pending_count = int(registry["experiment_type"].isin(["FACTOR_RESEARCH_PENDING", "COST_RESEARCH_PENDING"]).sum()) if total else 0
    ready_count = int(registry["readiness_status"].eq("READY").sum()) if total else 0
    partial_count = int(registry["readiness_status"].eq("PARTIAL_READY").sum()) if total else 0
    pending_forward_count = int(registry["readiness_status"].eq("PENDING_FORWARD_OUTCOME").sum()) if total else 0
    missing_count = int(registry["readiness_status"].eq("MISSING_INPUT").sum()) if total else 0

    deps = pd.DataFrame(dep_records)
    missing_important = int(deps[deps["dependency_status"].astype(str).str.contains("WARN_MISSING_IMPORTANT_INPUT", regex=False)].shape[0]) if not deps.empty else 0
    unknown_or_missing = missing_count + int(registry["readiness_status"].eq("UNKNOWN").sum()) if total else 0
    if total <= 0:
        status = "FAIL_V18_38B_RESEARCH_EXPERIMENT_REGISTRY_BLOCKED"
    elif missing_important > 0 or unknown_or_missing > max(3, total // 2):
        status = "WARN_V18_38B_RESEARCH_EXPERIMENT_REGISTRY_REVIEW_NEEDED"
    else:
        status = "OK_V18_38B_RESEARCH_EXPERIMENT_REGISTRY_READY"

    if any_forward == "TRUE":
        next_step = "Review ready/partial experiments and produce a constrained comparison memo."
    else:
        next_step = "Wait for forward outcome maturity, then rerun V18.38A and V18.38B."

    summary = {
        "total_experiment_count": total,
        "paper_experiment_count": paper_count,
        "shadow_portfolio_experiment_count": shadow_count,
        "motif_experiment_count": motif_count,
        "benchmark_experiment_count": benchmark_count,
        "pending_research_experiment_count": pending_count,
        "ready_experiment_count": ready_count,
        "partial_ready_experiment_count": partial_count,
        "pending_forward_outcome_count": pending_forward_count,
        "missing_input_experiment_count": missing_count,
        "any_forward_outcome_available": any_forward,
        "ready_for_factor_forward_attribution": factor_ready,
        "ready_for_shadow_portfolio_league_table": shadow_ready,
        "recommended_next_development_step": next_step,
    }

    read_first = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "GENERATED_AT": generated_at,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "RANKING_MODIFIED": "FALSE",
        "FACTOR_WEIGHTS_MODIFIED": "FALSE",
        "SIGNAL_FREEZE_LEDGER_MODIFIED": "FALSE",
        "PAPER_TRADING_LEDGER_MODIFIED": "FALSE",
        "SHADOW_PORTFOLIO_LEDGER_MODIFIED": "FALSE",
        "ACCOUNT_STATE_MODIFIED": "FALSE",
        "BROKER_API_USED": "FALSE",
        "ORDER_EXECUTION_USED": "FALSE",
        "TOTAL_EXPERIMENT_COUNT": total,
        "PAPER_EXPERIMENT_COUNT": paper_count,
        "SHADOW_PORTFOLIO_EXPERIMENT_COUNT": shadow_count,
        "MOTIF_EXPERIMENT_COUNT": motif_count,
        "BENCHMARK_EXPERIMENT_COUNT": benchmark_count,
        "PENDING_RESEARCH_EXPERIMENT_COUNT": pending_count,
        "READY_EXPERIMENT_COUNT": ready_count,
        "PARTIAL_READY_EXPERIMENT_COUNT": partial_count,
        "PENDING_FORWARD_OUTCOME_COUNT": pending_forward_count,
        "MISSING_INPUT_EXPERIMENT_COUNT": missing_count,
        "ANY_FORWARD_OUTCOME_AVAILABLE": any_forward,
        "READY_FOR_FACTOR_FORWARD_ATTRIBUTION": factor_ready,
        "READY_FOR_SHADOW_PORTFOLIO_LEAGUE_TABLE": shadow_ready,
        "NEXT_RECOMMENDED_STEP": next_step,
    }

    registry_path = root / "outputs/v18/ops/V18_38B_RESEARCH_EXPERIMENT_REGISTRY.csv"
    summary_path = root / "outputs/v18/ops/V18_38B_RESEARCH_EXPERIMENT_SUMMARY.csv"
    deps_path = root / "outputs/v18/ops/V18_38B_RESEARCH_EXPERIMENT_DEPENDENCIES.csv"
    report_path = root / "outputs/v18/read_center/V18_38B_RESEARCH_EXPERIMENT_REGISTRY_REPORT.md"
    current_report_path = root / "outputs/v18/read_center/V18_CURRENT_RESEARCH_EXPERIMENT_REGISTRY.md"
    read_first_path = root / "outputs/v18/ops/V18_38B_READ_FIRST.txt"

    dep_cols = ["experiment_id", "dependency_name", "dependency_path", "exists", "row_count", "modified_time", "dependency_status", "notes"]
    exp_ids = ";".join(registry["experiment_id"].astype(str).tolist()) if not registry.empty else ""
    deps["experiment_id"] = exp_ids

    write_csv(registry_path, registry, registry_cols)
    write_csv(summary_path, pd.DataFrame([summary]), list(summary.keys()))
    write_csv(deps_path, deps, dep_cols)
    report = build_report(read_first, registry, deps, summary)
    write_text(report_path, report)
    shutil.copyfile(report_path, current_report_path)
    read_first_text = "\n".join(f"{k}: {v}" for k, v in read_first.items()) + "\n"
    write_text(read_first_path, read_first_text)
    print(read_first_text, end="")
    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
