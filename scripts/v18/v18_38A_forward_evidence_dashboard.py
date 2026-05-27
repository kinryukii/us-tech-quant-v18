#!/usr/bin/env python
"""V18.38A forward evidence dashboard / outcome readiness center.

Read-only reporting layer. It summarizes available forward outcome evidence
from paper trading, shadow portfolio, signal freeze, candidates, and benchmark
outputs. It never modifies ranking, ledgers, account state, or trading logic.
"""

from __future__ import annotations

import argparse
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


HORIZONS = [1, 3, 5, 10, 20]
HORIZON_LABELS = [f"{h}D" for h in HORIZONS]

AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
MODE = "READ_ONLY_FORWARD_EVIDENCE_DASHBOARD"


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


def modified_time(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def safe_read_csv(path: Path) -> tuple[pd.DataFrame, str]:
    if not path.exists():
        return pd.DataFrame(), "MISSING"
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig"), "OK"
    except Exception as exc:  # defensive report layer: never crash on one bad optional input
        return pd.DataFrame(), f"READ_ERROR: {type(exc).__name__}: {exc}"


def norm_col(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def find_col(df: pd.DataFrame, *names: str) -> str | None:
    if df.empty:
        return None
    lookup = {norm_col(c): c for c in df.columns}
    for name in names:
        hit = lookup.get(norm_col(name))
        if hit is not None:
            return hit
    return None


def numeric_series(df: pd.DataFrame, col: str | None) -> pd.Series:
    if col is None or col not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[col].replace("", pd.NA), errors="coerce").dropna()


def nonempty_count(df: pd.DataFrame, col: str | None) -> int:
    if col is None or col not in df.columns:
        return 0
    return int(df[col].astype(str).str.strip().ne("").sum())


def pct(num: int, den: int) -> str:
    if den <= 0:
        return ""
    return f"{(num / den) * 100:.2f}"


def bool_text(value: bool | None) -> str:
    if value is None:
        return "UNKNOWN"
    return "TRUE" if value else "FALSE"


def readiness_status(total: int, fillable: int, source_exists: bool) -> str:
    if not source_exists or total <= 0:
        return "MISSING_INPUT"
    if fillable >= total:
        return "READY"
    if fillable > 0:
        return "PARTIAL_READY"
    return "PENDING_NOT_ENOUGH_FUTURE_PRICES"


def comparison_status(entry_count: int, entry_available: int, matured_count: int) -> str:
    if entry_count <= 0:
        return "MISSING_INPUT"
    if matured_count > 0 and entry_available >= entry_count:
        return "READY"
    if matured_count > 0 or entry_available > 0:
        return "PARTIAL_READY"
    return "PENDING_NOT_ENOUGH_FUTURE_PRICES"


def inventory_row(root: Path, source_name: str, path: Path, df: pd.DataFrame, load_status: str, core: bool) -> dict[str, Any]:
    exists = path.exists()
    if not exists:
        usability = "WARN_MISSING_CORE_INPUT" if core else "WARN_MISSING_OPTIONAL_INPUT"
        notes = "missing file; dashboard continues defensively"
    elif load_status != "OK":
        usability = "WARN_READ_ERROR"
        notes = load_status
    elif path.suffix.lower() == ".csv" and df.empty:
        usability = "WARN_EMPTY_CSV"
        notes = "CSV exists but has zero rows"
    else:
        usability = "OK_USABLE"
        notes = "usable evidence source"
    return {
        "source_name": source_name,
        "expected_path": rel(root, path),
        "exists": bool_text(exists),
        "row_count": "" if path.suffix.lower() != ".csv" or not exists or load_status != "OK" else len(df),
        "modified_time": modified_time(path),
        "usability_status": usability,
        "notes": notes,
    }


def horizon_from_text(value: str) -> str:
    text = str(value).upper().strip()
    if text.endswith("D"):
        return text
    if text in {str(h) for h in HORIZONS}:
        return f"{text}D"
    return text


def paper_counts(paper_forward: pd.DataFrame, horizon: int) -> tuple[int, int]:
    if paper_forward.empty:
        return 0, 0
    h_col = find_col(paper_forward, "horizon")
    if h_col is None:
        return 0, 0
    sub = paper_forward[paper_forward[h_col].map(horizon_from_text).eq(f"{horizon}D")]
    ret_col = find_col(sub, "net_return_after_cost", "gross_return", f"forward_{horizon}d_return", f"forward_return_{horizon}d")
    status_col = find_col(sub, "outcome_status", "forward_fill_status")
    filled_by_return = numeric_series(sub, ret_col).index
    fillable = len(filled_by_return)
    if status_col is not None:
        fillable = max(fillable, int(sub[status_col].astype(str).str.upper().str.contains("FILLED|READY|AVAILABLE", regex=True).sum()))
    return int(fillable), int(len(sub))


def shadow_counts(shadow_detail: pd.DataFrame, horizon: int) -> tuple[int, int]:
    if shadow_detail.empty:
        return 0, 0
    col = find_col(shadow_detail, f"forward_{horizon}d_return", f"forward_return_{horizon}d")
    return nonempty_count(shadow_detail, col), int(len(shadow_detail))


def benchmark_available(benchmark: pd.DataFrame, horizon: int) -> bool | None:
    if benchmark.empty:
        return None
    h_col = find_col(benchmark, "horizon")
    if h_col is None:
        return None
    sub = benchmark[benchmark[h_col].map(horizon_from_text).eq(f"{horizon}D")]
    if sub.empty:
        return None
    ret_col = find_col(sub, "benchmark_return", "excess_return_after_cost", "benchmark_excess_return")
    return nonempty_count(sub, ret_col) > 0


def group_rows_from_paper(paper_forward: pd.DataFrame, benchmark: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if paper_forward.empty:
        return rows
    p_col = find_col(paper_forward, "portfolio_name", "group_name")
    if p_col is None:
        return rows
    h_col = find_col(paper_forward, "horizon")
    entry_col = find_col(paper_forward, "entry_price")
    rank_col = find_col(paper_forward, "candidate_rank", "rank", "source_rank")
    ret_col = find_col(paper_forward, "net_return_after_cost", "gross_return")
    for name, sub in paper_forward.groupby(p_col, dropna=False):
        name_text = str(name)
        if "TOP20" in name_text:
            label = "Top20"
        elif "TOP50" in name_text:
            label = "Top50"
        elif "TOP100" in name_text:
            label = "Top100"
        elif "FULL318" in name_text or "318" in name_text:
            label = "Full318"
        else:
            label = name_text
        entry_count = int(sub[rank_col].nunique()) if rank_col else int(len(sub))
        entry_avail = nonempty_count(sub.drop_duplicates(rank_col) if rank_col else sub, entry_col)
        horizons = sorted({horizon_from_text(x) for x in sub[h_col].tolist() if horizon_from_text(x) in HORIZON_LABELS}) if h_col else []
        matured = 0
        if h_col and ret_col:
            for h in HORIZON_LABELS:
                hsub = sub[sub[h_col].map(horizon_from_text).eq(h)]
                if numeric_series(hsub, ret_col).shape[0] > 0:
                    matured += 1
        rows.append({
            "group_name": label,
            "group_type": "PAPER_TOPN",
            "entry_count": entry_count,
            "entry_price_available_count": entry_avail,
            "entry_price_missing_count": max(entry_count - entry_avail, 0),
            "available_forward_horizons": ";".join(horizons),
            "matured_forward_horizon_count": matured,
            "comparison_ready_status": comparison_status(entry_count, entry_avail, matured),
            "notes": f"paper source portfolio_name={name_text}",
        })
    if not benchmark.empty:
        for bench in ["SPY", "QQQ"]:
            b_col = find_col(benchmark, "benchmark", "symbol", "ticker")
            sub = benchmark[benchmark[b_col].astype(str).str.upper().eq(bench)] if b_col else pd.DataFrame()
            h_col = find_col(sub, "horizon")
            ret_col = find_col(sub, "benchmark_return")
            entry_col = find_col(sub, "benchmark_entry_price", "entry_price")
            horizons = sorted({horizon_from_text(x) for x in sub[h_col].tolist() if horizon_from_text(x) in HORIZON_LABELS}) if h_col else []
            matured = 0
            if h_col and ret_col:
                for h in HORIZON_LABELS:
                    hsub = sub[sub[h_col].map(horizon_from_text).eq(h)]
                    if numeric_series(hsub, ret_col).shape[0] > 0:
                        matured += 1
            entry_available = 1 if nonempty_count(sub, entry_col) > 0 else 0
            rows.append({
                "group_name": bench,
                "group_type": "BENCHMARK",
                "entry_count": 1 if not sub.empty else 0,
                "entry_price_available_count": entry_available,
                "entry_price_missing_count": 0 if entry_available else 1,
                "available_forward_horizons": ";".join(horizons),
                "matured_forward_horizon_count": matured,
                "comparison_ready_status": comparison_status(1 if not sub.empty else 0, entry_available, matured),
                "notes": "benchmark evidence from paper/shadow outputs if available",
            })
    return rows


def group_rows_from_shadow(shadow_detail: pd.DataFrame) -> list[dict[str, Any]]:
    if shadow_detail.empty:
        return []
    p_col = find_col(shadow_detail, "portfolio_id", "portfolio_name", "group_name")
    entry_col = find_col(shadow_detail, "entry_price")
    if p_col is None:
        return []
    rows: list[dict[str, Any]] = []
    for name, sub in shadow_detail.groupby(p_col, dropna=False):
        entry_count = int(len(sub))
        entry_avail = nonempty_count(sub, entry_col)
        horizons: list[str] = []
        matured = 0
        for h in HORIZONS:
            col = find_col(sub, f"forward_{h}d_return", f"forward_return_{h}d")
            if col is not None:
                horizons.append(f"{h}D")
                if nonempty_count(sub, col) > 0:
                    matured += 1
        rows.append({
            "group_name": str(name),
            "group_type": "SHADOW_PORTFOLIO",
            "entry_count": entry_count,
            "entry_price_available_count": entry_avail,
            "entry_price_missing_count": max(entry_count - entry_avail, 0),
            "available_forward_horizons": ";".join(horizons),
            "matured_forward_horizon_count": matured,
            "comparison_ready_status": comparison_status(entry_count, entry_avail, matured),
            "notes": "shadow portfolio snapshot evidence",
        })
    return rows


def outcome_metrics_from_paper(paper_forward: pd.DataFrame, benchmark: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not paper_forward.empty:
        p_col = find_col(paper_forward, "portfolio_name", "group_name")
        h_col = find_col(paper_forward, "horizon")
        ret_col = find_col(paper_forward, "net_return_after_cost", "gross_return")
        if p_col and h_col and ret_col:
            for (group, horizon), sub in paper_forward.groupby([p_col, h_col], dropna=False):
                vals = numeric_series(sub, ret_col)
                if vals.empty:
                    continue
                rows.append(metric_row("PAPER_TOPN", str(group), horizon_from_text(str(horizon)), vals, None))
    if not benchmark.empty:
        b_col = find_col(benchmark, "benchmark")
        h_col = find_col(benchmark, "horizon")
        ret_col = find_col(benchmark, "benchmark_return")
        excess_col = find_col(benchmark, "excess_return_after_cost", "benchmark_excess_return")
        if b_col and h_col and ret_col:
            for (bench, horizon), sub in benchmark.groupby([b_col, h_col], dropna=False):
                vals = numeric_series(sub, ret_col)
                if vals.empty:
                    continue
                excess = numeric_series(sub, excess_col)
                rows.append(metric_row("BENCHMARK", str(bench), horizon_from_text(str(horizon)), vals, excess))
    return rows


def outcome_metrics_from_shadow(shadow_detail: pd.DataFrame) -> list[dict[str, Any]]:
    if shadow_detail.empty:
        return []
    p_col = find_col(shadow_detail, "portfolio_id", "portfolio_name")
    if p_col is None:
        return []
    rows: list[dict[str, Any]] = []
    for group, sub in shadow_detail.groupby(p_col, dropna=False):
        for h in HORIZONS:
            col = find_col(sub, f"forward_{h}d_return", f"forward_return_{h}d")
            vals = numeric_series(sub, col)
            if vals.empty:
                continue
            rows.append(metric_row("SHADOW_PORTFOLIO", str(group), f"{h}D", vals, None))
    return rows


def metric_row(group_type: str, group_name: str, horizon: str, vals: pd.Series, excess_vals: pd.Series | None) -> dict[str, Any]:
    win_rate = float((vals > 0).sum()) / float(len(vals)) if len(vals) else math.nan
    return {
        "record_type": "OUTCOME_METRIC",
        "source_name": "",
        "expected_path": "",
        "exists": "",
        "row_count": "",
        "modified_time": "",
        "usability_status": "",
        "group_name": group_name,
        "group_type": group_type,
        "entry_count": "",
        "entry_price_available_count": "",
        "entry_price_missing_count": "",
        "available_forward_horizons": horizon,
        "matured_forward_horizon_count": 1,
        "comparison_ready_status": "READY",
        "horizon": horizon,
        "avg_forward_return": f"{vals.mean():.8f}",
        "median_forward_return": f"{vals.median():.8f}",
        "win_rate": f"{win_rate:.6f}",
        "benchmark_excess_return": "" if excess_vals is None or excess_vals.empty else f"{excess_vals.mean():.8f}",
        "count_used": int(len(vals)),
        "notes": "computed only from existing non-empty forward return columns",
    }


def latest_signal_info(freeze: pd.DataFrame) -> tuple[str, int]:
    if freeze.empty:
        return "", 0
    date_col = find_col(freeze, "signal_date")
    if date_col is None:
        return "", len(freeze)
    dates = [x for x in freeze[date_col].astype(str).tolist() if x.strip()]
    if not dates:
        return "", len(freeze)
    latest = sorted(dates)[-1]
    return latest, int(freeze[freeze[date_col].astype(str).eq(latest)].shape[0])


def source_status(inventory: list[dict[str, Any]], names: list[str]) -> str:
    matched = [r for r in inventory if r["source_name"] in names]
    if not matched:
        return "MISSING_INPUT"
    if any(str(r["usability_status"]).startswith("OK") for r in matched):
        return "OK_USABLE"
    if any(r["exists"] == "TRUE" for r in matched):
        return "WARN_PRESENT_BUT_NOT_USABLE"
    return "MISSING_INPUT"


def build_report(
    read_first: dict[str, Any],
    inventory: pd.DataFrame,
    readiness: pd.DataFrame,
    groups: pd.DataFrame,
    metrics: pd.DataFrame,
) -> str:
    def table(df: pd.DataFrame, cols: list[str], max_rows: int = 40) -> str:
        if df.empty:
            return "_无可用记录。_"
        return df[cols].head(max_rows).to_markdown(index=False)

    paper_groups = groups[groups["group_type"].eq("PAPER_TOPN")] if not groups.empty else pd.DataFrame()
    shadow_groups = groups[groups["group_type"].eq("SHADOW_PORTFOLIO")] if not groups.empty else pd.DataFrame()
    bench_groups = groups[groups["group_type"].eq("BENCHMARK")] if not groups.empty else pd.DataFrame()

    conclusion = "当前看板已生成；forward horizon 未成熟属于预期等待，不是系统失败。"
    if read_first["ANY_FORWARD_OUTCOME_AVAILABLE"] == "TRUE":
        conclusion = "已有部分 forward outcome 可读，可开始做有限范围的证据复核。"
    if str(read_first["STATUS"]).startswith("WARN"):
        conclusion = "看板可用，但部分证据源缺失或不可读，需要人工复核。"
    if str(read_first["STATUS"]).startswith("FAIL"):
        conclusion = "看板被阻塞，无法形成有效报告。"

    metric_note = "_目前没有可聚合的 forward return 数值；状态为 PENDING_NOT_ENOUGH_FUTURE_PRICES。_"
    if not metrics.empty:
        metric_note = table(metrics, ["group_type", "group_name", "horizon", "avg_forward_return", "median_forward_return", "win_rate", "count_used"], 30)

    lines = [
        "# V18.38A Forward Evidence Dashboard / Outcome Readiness Center",
        "",
        "## 1. 今日结论",
        f"- STATUS: {read_first['STATUS']}",
        f"- RUN_ID: {read_first['RUN_ID']}",
        f"- 结论: {conclusion}",
        f"- ANY_FORWARD_OUTCOME_AVAILABLE: {read_first['ANY_FORWARD_OUTCOME_AVAILABLE']}",
        f"- READY_FOR_FACTOR_FORWARD_ATTRIBUTION: {read_first['READY_FOR_FACTOR_FORWARD_ATTRIBUTION']}",
        f"- READY_FOR_SHADOW_PORTFOLIO_LEAGUE_TABLE: {read_first['READY_FOR_SHADOW_PORTFOLIO_LEAGUE_TABLE']}",
        "",
        "## 2. 证据源检查",
        table(inventory, ["source_name", "exists", "row_count", "modified_time", "usability_status", "notes"], 60),
        "",
        "## 3. Forward horizon 成熟度",
        table(readiness, ["horizon", "paper_trading_fillable_count", "paper_trading_total_count", "paper_trading_fillable_pct", "shadow_portfolio_fillable_count", "shadow_portfolio_total_count", "shadow_portfolio_fillable_pct", "benchmark_available", "readiness_status"], 20),
        "",
        "## 4. Paper trading 证据状态",
        table(paper_groups, ["group_name", "entry_count", "entry_price_available_count", "available_forward_horizons", "matured_forward_horizon_count", "comparison_ready_status", "notes"], 20),
        "",
        "## 5. Shadow portfolio 证据状态",
        table(shadow_groups, ["group_name", "entry_count", "entry_price_available_count", "available_forward_horizons", "matured_forward_horizon_count", "comparison_ready_status", "notes"], 30),
        "",
        "## 6. TopN / Full318 比较准备度",
        table(groups[groups["group_name"].astype(str).isin(["Top20", "Top50", "Top100", "Full318"])] if not groups.empty else pd.DataFrame(), ["group_name", "group_type", "entry_count", "entry_price_available_count", "matured_forward_horizon_count", "comparison_ready_status"], 20),
        "",
        "## 7. Benchmark 状态",
        table(bench_groups, ["group_name", "entry_count", "entry_price_available_count", "available_forward_horizons", "matured_forward_horizon_count", "comparison_ready_status", "notes"], 20),
        "",
        "## 8. 当前是否足够做因子归因",
        f"- READY_FOR_FACTOR_FORWARD_ATTRIBUTION: {read_first['READY_FOR_FACTOR_FORWARD_ATTRIBUTION']}",
        f"- 可用 outcome metrics: {metric_note}",
        "",
        "## 9. 当前是否足够做影子组合联赛表",
        f"- READY_FOR_SHADOW_PORTFOLIO_LEAGUE_TABLE: {read_first['READY_FOR_SHADOW_PORTFOLIO_LEAGUE_TABLE']}",
        "- 如果 shadow portfolio 的所有 forward horizon 仍为等待未来价格，则只能展示构造/入场证据，不能排名真实收益表现。",
        "",
        "## 10. 下一步建议",
        f"- {read_first['NEXT_RECOMMENDED_STEP']}",
        "",
        "## 11. Safety / no-impact confirmation",
        f"- MODE: {read_first['MODE']}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        "- RANKING_MODIFIED: FALSE",
        "- FACTOR_WEIGHTS_MODIFIED: FALSE",
        "- SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE",
        "- PAPER_TRADING_LEDGER_MODIFIED: FALSE",
        "- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE",
        "- ACCOUNT_STATE_MODIFIED: FALSE",
        "- BROKER_API_USED: FALSE",
        "- ORDER_EXECUTION_USED: FALSE",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ensure_dirs(root)
    run_id = f"V18_38A_FORWARD_EVIDENCE_DASHBOARD_{now_ts()}"
    generated_at = now_iso()

    paths = {
        "paper_forward": root / "outputs/v18/paper_trading/V18_36A_PAPER_FORWARD_RETURNS.csv",
        "paper_forward_filled": root / "outputs/v18/paper_trading/V18_36B_PAPER_FORWARD_RETURNS_FILLED.csv",
        "paper_benchmark": root / "outputs/v18/paper_trading/V18_36A_BENCHMARK_COMPARISON.csv",
        "paper_benchmark_filled": root / "outputs/v18/paper_trading/V18_36B_BENCHMARK_COMPARISON_UPDATED.csv",
        "paper_ledger": root / "state/v18/paper_trading/V18_PAPER_TRADING_LEDGER.csv",
        "paper_state": root / "state/v18/paper_trading/V18_PAPER_PORTFOLIO_STATE.csv",
        "paper_read_first": root / "outputs/v18/ops/V18_36A_READ_FIRST.txt",
        "paper_report": root / "outputs/v18/read_center/V18_CURRENT_PAPER_TRADING_FORWARD_ATTRIBUTION.md",
        "shadow_summary": root / "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_SUMMARY.csv",
        "shadow_detail": root / "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_DETAIL.csv",
        "shadow_readiness": root / "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_FORWARD_READINESS.csv",
        "shadow_ledger": root / "state/v18/shadow_portfolios/V18_SHADOW_PORTFOLIO_DAILY_SNAPSHOT_LEDGER.csv",
        "full_candidates": root / "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
        "top_candidates": root / "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        "signal_freeze": root / "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    }

    data: dict[str, pd.DataFrame] = {}
    load_status: dict[str, str] = {}
    for key, path in paths.items():
        if path.suffix.lower() == ".csv":
            data[key], load_status[key] = safe_read_csv(path)
        else:
            data[key], load_status[key] = pd.DataFrame(), "OK" if path.exists() else "MISSING"

    # Prefer filled V18.36B evidence when present, otherwise use V18.36A baseline.
    paper_forward_key = "paper_forward_filled" if not data["paper_forward_filled"].empty else "paper_forward"
    paper_benchmark_key = "paper_benchmark_filled" if not data["paper_benchmark_filled"].empty else "paper_benchmark"
    paper_forward = data[paper_forward_key]
    paper_benchmark = data[paper_benchmark_key]
    shadow_detail = data["shadow_detail"]
    signal_freeze = data["signal_freeze"]

    core_names = {"paper_forward", "shadow_detail", "full_candidates", "top_candidates", "signal_freeze"}
    source_labels = {
        "paper_forward": "V18.36A paper forward returns",
        "paper_forward_filled": "V18.36B paper forward returns filled",
        "paper_benchmark": "V18.36A benchmark comparison",
        "paper_benchmark_filled": "V18.36B benchmark comparison updated",
        "paper_ledger": "paper trading ledger",
        "paper_state": "paper portfolio state",
        "paper_read_first": "V18.36A READ_FIRST",
        "paper_report": "current paper trading forward attribution report",
        "shadow_summary": "V18.37C shadow snapshot summary",
        "shadow_detail": "V18.37C shadow snapshot detail",
        "shadow_readiness": "V18.37C shadow forward readiness",
        "shadow_ledger": "shadow portfolio snapshot ledger",
        "full_candidates": "current Full318 candidates",
        "top_candidates": "current top candidates",
        "signal_freeze": "signal freeze ledger",
    }
    inventory = [
        inventory_row(root, source_labels[key], path, data[key], load_status[key], key in core_names)
        for key, path in paths.items()
    ]

    readiness_rows: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        p_fill, p_total = paper_counts(paper_forward, horizon)
        s_fill, s_total = shadow_counts(shadow_detail, horizon)
        b_avail = benchmark_available(paper_benchmark, horizon)
        statuses = [
            readiness_status(p_total, p_fill, not paper_forward.empty),
            readiness_status(s_total, s_fill, not shadow_detail.empty),
        ]
        if "READY" in statuses or "PARTIAL_READY" in statuses:
            status = "READY" if all(x == "READY" for x in statuses if x != "MISSING_INPUT") else "PARTIAL_READY"
        elif all(x == "MISSING_INPUT" for x in statuses):
            status = "MISSING_INPUT"
        elif all(x in {"MISSING_INPUT", "PENDING_NOT_ENOUGH_FUTURE_PRICES"} for x in statuses):
            status = "PENDING_NOT_ENOUGH_FUTURE_PRICES"
        else:
            status = "UNKNOWN"
        readiness_rows.append({
            "horizon": f"{horizon}D",
            "paper_trading_fillable_count": p_fill,
            "paper_trading_total_count": p_total,
            "paper_trading_fillable_pct": pct(p_fill, p_total),
            "shadow_portfolio_fillable_count": s_fill,
            "shadow_portfolio_total_count": s_total,
            "shadow_portfolio_fillable_pct": pct(s_fill, s_total),
            "benchmark_available": bool_text(b_avail),
            "readiness_status": status,
            "notes": "EXPECTED_PENDING_FORWARD_HORIZON if fillable counts are zero before enough future prices exist",
        })
    readiness_df = pd.DataFrame(readiness_rows)

    group_records = group_rows_from_paper(paper_forward, paper_benchmark) + group_rows_from_shadow(shadow_detail)
    group_df = pd.DataFrame(group_records)
    group_columns = [
        "group_name",
        "group_type",
        "entry_count",
        "entry_price_available_count",
        "entry_price_missing_count",
        "available_forward_horizons",
        "matured_forward_horizon_count",
        "comparison_ready_status",
        "notes",
    ]
    if group_df.empty:
        group_df = pd.DataFrame(columns=group_columns)

    metric_records = outcome_metrics_from_paper(paper_forward, paper_benchmark) + outcome_metrics_from_shadow(shadow_detail)
    metrics_df = pd.DataFrame(metric_records)
    any_forward_outcome = not metrics_df.empty

    latest_signal_date, latest_freeze_count = latest_signal_info(signal_freeze)
    full_count = int(len(data["full_candidates"])) if not data["full_candidates"].empty else 0
    top_count = int(len(data["top_candidates"])) if not data["top_candidates"].empty else 0
    usable_sources = sum(1 for r in inventory if str(r["usability_status"]).startswith("OK"))
    missing_sources = sum(1 for r in inventory if r["exists"] == "FALSE")
    total_sources = len(inventory)
    core_usable = any(str(r["usability_status"]).startswith("OK") for r in inventory if r["source_name"] in {
        source_labels["paper_forward"],
        source_labels["paper_forward_filled"],
        source_labels["shadow_detail"],
        source_labels["signal_freeze"],
        source_labels["full_candidates"],
    })

    if not core_usable:
        status = "FAIL_V18_38A_FORWARD_EVIDENCE_DASHBOARD_BLOCKED"
    elif missing_sources > 0 or any(str(r["usability_status"]).startswith("WARN_READ_ERROR") for r in inventory):
        status = "WARN_V18_38A_FORWARD_EVIDENCE_DASHBOARD_REVIEW_NEEDED"
    else:
        status = "OK_V18_38A_FORWARD_EVIDENCE_DASHBOARD_READY"

    factor_ready = "TRUE" if any_forward_outcome and any(group_df["group_type"].eq("PAPER_TOPN")) else "FALSE"
    shadow_ready = "TRUE" if any_forward_outcome and any(group_df["group_type"].eq("SHADOW_PORTFOLIO")) and int(group_df.loc[group_df["group_type"].eq("SHADOW_PORTFOLIO"), "matured_forward_horizon_count"].astype(int).sum()) > 0 else "FALSE"
    if any_forward_outcome:
        next_step = "Review available forward outcome metrics and decide whether a limited attribution memo is warranted."
    else:
        next_step = "Wait for future-price horizons to mature, then rerun V18.36B/V18.37C and this dashboard."

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
        "TOTAL_EVIDENCE_SOURCE_COUNT": total_sources,
        "USABLE_EVIDENCE_SOURCE_COUNT": usable_sources,
        "MISSING_EVIDENCE_SOURCE_COUNT": missing_sources,
        "PAPER_TRADING_SOURCE_STATUS": source_status(inventory, [source_labels["paper_forward"], source_labels["paper_forward_filled"], source_labels["paper_ledger"]]),
        "SHADOW_PORTFOLIO_SOURCE_STATUS": source_status(inventory, [source_labels["shadow_detail"], source_labels["shadow_ledger"]]),
        "SIGNAL_FREEZE_SOURCE_STATUS": source_status(inventory, [source_labels["signal_freeze"]]),
        "LATEST_SIGNAL_DATE": latest_signal_date,
        "LATEST_SIGNAL_FREEZE_COUNT": latest_freeze_count,
        "CURRENT_FULL_CANDIDATE_COUNT": full_count,
        "CURRENT_TOP_CANDIDATE_COUNT": top_count,
        "HORIZON_1D_STATUS": readiness_df.loc[readiness_df["horizon"].eq("1D"), "readiness_status"].iloc[0],
        "HORIZON_3D_STATUS": readiness_df.loc[readiness_df["horizon"].eq("3D"), "readiness_status"].iloc[0],
        "HORIZON_5D_STATUS": readiness_df.loc[readiness_df["horizon"].eq("5D"), "readiness_status"].iloc[0],
        "HORIZON_10D_STATUS": readiness_df.loc[readiness_df["horizon"].eq("10D"), "readiness_status"].iloc[0],
        "HORIZON_20D_STATUS": readiness_df.loc[readiness_df["horizon"].eq("20D"), "readiness_status"].iloc[0],
        "ANY_FORWARD_OUTCOME_AVAILABLE": "TRUE" if any_forward_outcome else "FALSE",
        "READY_FOR_FACTOR_FORWARD_ATTRIBUTION": factor_ready,
        "READY_FOR_SHADOW_PORTFOLIO_LEAGUE_TABLE": shadow_ready,
        "NEXT_RECOMMENDED_STEP": next_step,
    }

    inv_df = pd.DataFrame(inventory)
    summary_df = pd.DataFrame([read_first])
    detail_rows: list[dict[str, Any]] = []
    for row in inventory:
        rec = {"record_type": "EVIDENCE_SOURCE", **row}
        detail_rows.append(rec)
    for row in group_df.to_dict("records"):
        rec = {"record_type": "COMPARISON_GROUP", **row}
        detail_rows.append(rec)
    for row in metric_records:
        detail_rows.append(row)
    detail_df = pd.DataFrame(detail_rows)

    summary_path = root / "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_SUMMARY.csv"
    detail_path = root / "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_DETAIL.csv"
    readiness_path = root / "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_READINESS.csv"
    report_path = root / "outputs/v18/read_center/V18_38A_FORWARD_EVIDENCE_DASHBOARD_REPORT.md"
    current_report_path = root / "outputs/v18/read_center/V18_CURRENT_FORWARD_EVIDENCE_DASHBOARD.md"
    read_first_path = root / "outputs/v18/ops/V18_38A_READ_FIRST.txt"

    write_csv(summary_path, summary_df, list(read_first.keys()))
    write_csv(detail_path, detail_df, [
        "record_type",
        "source_name",
        "expected_path",
        "exists",
        "row_count",
        "modified_time",
        "usability_status",
        "group_name",
        "group_type",
        "entry_count",
        "entry_price_available_count",
        "entry_price_missing_count",
        "available_forward_horizons",
        "matured_forward_horizon_count",
        "comparison_ready_status",
        "horizon",
        "avg_forward_return",
        "median_forward_return",
        "win_rate",
        "benchmark_excess_return",
        "count_used",
        "notes",
    ])
    write_csv(readiness_path, readiness_df, [
        "horizon",
        "paper_trading_fillable_count",
        "paper_trading_total_count",
        "paper_trading_fillable_pct",
        "shadow_portfolio_fillable_count",
        "shadow_portfolio_total_count",
        "shadow_portfolio_fillable_pct",
        "benchmark_available",
        "readiness_status",
        "notes",
    ])

    report = build_report(read_first, inv_df, readiness_df, group_df, metrics_df)
    write_text(report_path, report)
    shutil.copyfile(report_path, current_report_path)

    read_first_text = "\n".join(f"{k}: {v}" for k, v in read_first.items()) + "\n"
    write_text(read_first_path, read_first_text)
    print(read_first_text, end="")
    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
