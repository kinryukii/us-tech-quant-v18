#!/usr/bin/env python
"""V18.37C shadow portfolio daily snapshot / forward attribution bridge.

Research-only snapshot writer for V18.37B shadow portfolios. Preview mode is
default. Apply mode only updates the dedicated shadow portfolio research ledger.
"""

from __future__ import annotations

import argparse
import csv
import shutil
from datetime import date, datetime
from pathlib import Path


AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FACTOR_WEIGHTS_MODIFIED = "FALSE"
OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED = "FALSE"
PAPER_TRADING_LEDGER_MODIFIED = "FALSE"
FORBIDDEN_MODIFIED = "FALSE"
SNAPSHOT_LAYER = "V18_37C_SHADOW_PORTFOLIO"
HORIZONS = (1, 3, 5, 10, 20)


DETAIL_FIELDS = [
    "snapshot_run_id",
    "snapshot_layer",
    "signal_date",
    "signal_date_source",
    "portfolio_id",
    "ticker",
    "final_weight",
    "source_rank",
    "motif_id",
    "composite_candidate_score",
    "technical_timing_score",
    "factor_pack_score",
    "entry_price",
    "entry_price_source",
    "entry_price_date",
    "forward_1d_return",
    "forward_3d_return",
    "forward_5d_return",
    "forward_10d_return",
    "forward_20d_return",
    "forward_fill_status",
    "official_decision_impact",
    "research_only",
]


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def run_id() -> str:
    return "V18_37C_" + datetime.now().strftime("%Y%m%d_%H%M%S")


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


def to_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text[:19]).date()
    except ValueError:
        return None


def fmt_date(value: date | None) -> str:
    return value.isoformat() if value else ""


def candidate_source_paths(root: Path) -> list[Path]:
    return [
        root / "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
        root / "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
        root / "outputs/v18/candidates/V18_14D_CURRENT_RANKED_CANDIDATE_FORWARD_PRICE_FILLER.csv",
    ]


def load_candidate_context(root: Path) -> tuple[dict[str, dict[str, str]], str, str]:
    by_ticker: dict[str, dict[str, str]] = {}
    signal_dates: list[tuple[date, str]] = []
    for path in candidate_source_paths(root):
        rows = read_csv(path)
        if not rows:
            continue
        for row in rows:
            ticker = str(row.get("ticker", "")).strip().upper()
            if ticker and ticker not in by_ticker:
                by_ticker[ticker] = row
            for field in ("latest_price_date", "price_date", "signal_date", "latest_date"):
                parsed = parse_date(row.get(field))
                if parsed:
                    signal_dates.append((parsed, f"{path.name}:{field}"))
    if signal_dates:
        signal_dates.sort(key=lambda item: item[0], reverse=True)
        return by_ticker, fmt_date(signal_dates[0][0]), signal_dates[0][1]
    return by_ticker, date.today().isoformat(), "LOCAL_CURRENT_DATE_FALLBACK"


def price_history_paths(root: Path) -> list[Path]:
    return [
        root / "data/v18/staged_backfill/V18_23C_BATCH1/V18_23C_BATCH1_STAGED_PRICE_HISTORY.csv",
        root / "data/v18/staged_backfill/V18_23C_BATCH2/V18_23C_BATCH2_STAGED_PRICE_HISTORY.csv",
    ]


def load_price_history(root: Path, tickers: set[str]) -> dict[str, list[tuple[date, float, str]]]:
    history: dict[str, list[tuple[date, float, str]]] = {ticker: [] for ticker in tickers}
    for path in price_history_paths(root):
        if not path.exists():
            continue
        with path.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = str(row.get("ticker", "")).strip().upper()
                if ticker not in tickers:
                    continue
                dt = parse_date(row.get("Date") or row.get("date"))
                close = to_float(row.get("Close") or row.get("Adj Close") or row.get("close") or row.get("adj_close"))
                if dt and close and close > 0:
                    history.setdefault(ticker, []).append((dt, close, path.name))
    for ticker in history:
        dedup: dict[date, tuple[date, float, str]] = {}
        for item in history[ticker]:
            dedup[item[0]] = item
        history[ticker] = sorted(dedup.values(), key=lambda item: item[0])
    return history


def find_entry_from_candidate(ticker: str, candidates: dict[str, dict[str, str]]) -> tuple[float | None, str, str]:
    row = candidates.get(ticker, {})
    price = to_float(row.get("latest_close") or row.get("price_at_signal") or row.get("close"))
    dt = row.get("latest_price_date") or row.get("price_date") or row.get("signal_date") or row.get("latest_date") or ""
    if price and price > 0:
        return price, "CURRENT_CANDIDATE_PRICE_FIELD", str(dt)
    return None, "", ""


def find_entry_from_history(signal_dt: date | None, ticker: str, history: dict[str, list[tuple[date, float, str]]]) -> tuple[float | None, str, str]:
    rows = history.get(ticker, [])
    if not signal_dt or not rows:
        return None, "", ""
    prior = [item for item in rows if item[0] <= signal_dt]
    if not prior:
        return None, "", ""
    dt, price, source = prior[-1]
    return price, f"LOCAL_PRICE_HISTORY:{source}", fmt_date(dt)


def nth_forward_price(entry_dt: date | None, ticker: str, horizon: int, history: dict[str, list[tuple[date, float, str]]]) -> tuple[float | None, str]:
    if not entry_dt:
        return None, ""
    future = [item for item in history.get(ticker, []) if item[0] > entry_dt]
    if len(future) < horizon:
        return None, ""
    dt, price, source = future[horizon - 1]
    return price, f"{fmt_date(dt)}:{source}"


def build_snapshot_rows(root: Path, run: str) -> tuple[list[dict[str, object]], str, str, str]:
    holdings_path = root / "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_HOLDINGS.csv"
    registry_path = root / "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_REGISTRY.csv"
    weights_path = root / "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_WEIGHTS.csv"
    if not holdings_path.exists() or not registry_path.exists() or not weights_path.exists():
        return [], "", "NOT_READY_MISSING_V18_37B_OUTPUT", "MISSING_V18_37B_HOLDINGS_OR_REGISTRY_OR_WEIGHTS"

    holdings = read_csv(holdings_path)
    candidates, signal_date, signal_source = load_candidate_context(root)
    signal_dt = parse_date(signal_date)
    tickers = {str(row.get("ticker", "")).strip().upper() for row in holdings if str(row.get("ticker", "")).strip()}
    history = load_price_history(root, tickers)

    rows: list[dict[str, object]] = []
    for row in holdings:
        ticker = str(row.get("ticker", "")).strip().upper()
        if not ticker:
            continue
        entry_price, entry_source, entry_date = find_entry_from_candidate(ticker, candidates)
        if entry_price is None:
            entry_price, entry_source, entry_date = find_entry_from_history(signal_dt, ticker, history)
        entry_dt = parse_date(entry_date) or signal_dt
        forward_values: dict[int, str] = {}
        fillable = 0
        for horizon in HORIZONS:
            future_price, _future_source = nth_forward_price(entry_dt, ticker, horizon, history)
            if entry_price and future_price:
                forward_values[horizon] = str(round((future_price / entry_price) - 1.0, 8))
                fillable += 1
            else:
                forward_values[horizon] = ""
        if entry_price is None:
            fill_status = "ENTRY_PRICE_MISSING"
        elif fillable == len(HORIZONS):
            fill_status = "ALL_FORWARD_HORIZONS_FILLABLE_LOCAL_CACHE"
        elif fillable > 0:
            fill_status = "PARTIAL_FORWARD_HORIZONS_FILLABLE_LOCAL_CACHE"
        else:
            fill_status = "WAITING_FOR_FUTURE_LOCAL_PRICES"

        rows.append(
            {
                "snapshot_run_id": run,
                "snapshot_layer": SNAPSHOT_LAYER,
                "signal_date": signal_date,
                "signal_date_source": signal_source,
                "portfolio_id": row.get("portfolio_id", ""),
                "ticker": ticker,
                "final_weight": row.get("final_weight", ""),
                "source_rank": row.get("source_rank", ""),
                "motif_id": row.get("motif_id", ""),
                "composite_candidate_score": row.get("composite_candidate_score", ""),
                "technical_timing_score": row.get("technical_timing_score", ""),
                "factor_pack_score": row.get("factor_pack_score", ""),
                "entry_price": entry_price if entry_price is not None else "",
                "entry_price_source": entry_source or "NOT_AVAILABLE",
                "entry_price_date": entry_date,
                "forward_1d_return": forward_values[1],
                "forward_3d_return": forward_values[3],
                "forward_5d_return": forward_values[5],
                "forward_10d_return": forward_values[10],
                "forward_20d_return": forward_values[20],
                "forward_fill_status": fill_status,
                "official_decision_impact": OFFICIAL_DECISION_IMPACT,
                "research_only": "TRUE",
            }
        )
    return rows, signal_date, "OK", signal_source


def portfolio_preview(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_portfolio: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_portfolio.setdefault(str(row.get("portfolio_id", "")), []).append(row)
    previews: list[dict[str, object]] = []
    for portfolio_id, items in sorted(by_portfolio.items()):
        weights = [to_float(row.get("final_weight")) or 0.0 for row in items]
        previews.append(
            {
                "portfolio_id": portfolio_id,
                "holding_count": len(items),
                "weight_sum": round(sum(weights), 10),
                "entry_price_available_count": sum(1 for row in items if to_float(row.get("entry_price")) is not None),
                "entry_price_missing_count": sum(1 for row in items if to_float(row.get("entry_price")) is None),
                "forward_1d_fillable_count": sum(1 for row in items if str(row.get("forward_1d_return", "")).strip()),
                "forward_3d_fillable_count": sum(1 for row in items if str(row.get("forward_3d_return", "")).strip()),
                "forward_5d_fillable_count": sum(1 for row in items if str(row.get("forward_5d_return", "")).strip()),
                "forward_10d_fillable_count": sum(1 for row in items if str(row.get("forward_10d_return", "")).strip()),
                "forward_20d_fillable_count": sum(1 for row in items if str(row.get("forward_20d_return", "")).strip()),
                "max_single_name_weight": round(max(weights), 10) if weights else 0,
                "min_single_name_weight": round(min(weights), 10) if weights else 0,
                "official_decision_impact": OFFICIAL_DECISION_IMPACT,
                "research_only": "TRUE",
            }
        )
    return previews


def readiness_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    total = len(rows)
    return [
        {
            "metric": "entry_price_available_count",
            "count": sum(1 for row in rows if to_float(row.get("entry_price")) is not None),
            "total_snapshot_rows": total,
            "status": "OK" if total and any(to_float(row.get("entry_price")) is not None for row in rows) else "WARN",
        },
        *[
            {
                "metric": f"forward_{horizon}d_fillable_count",
                "count": sum(1 for row in rows if str(row.get(f"forward_{horizon}d_return", "")).strip()),
                "total_snapshot_rows": total,
                "status": "OK" if any(str(row.get(f"forward_{horizon}d_return", "")).strip() for row in rows) else "WARN_WAITING_FOR_FUTURE_LOCAL_PRICES",
            }
            for horizon in HORIZONS
        ],
    ]


def summary_rows(rows: list[dict[str, object]], signal_date: str, signal_source: str, apply_snapshot: bool, status: str, ledger_path: Path, backup_path: str) -> list[dict[str, object]]:
    portfolios = sorted({str(row.get("portfolio_id", "")) for row in rows if row.get("portfolio_id")})
    entry_available = sum(1 for row in rows if to_float(row.get("entry_price")) is not None)
    return [
        {
            "status": status,
            "signal_date": signal_date,
            "signal_date_source": signal_source,
            "total_portfolio_count": len(portfolios),
            "total_snapshot_rows": len(rows),
            "entry_price_available_count": entry_available,
            "entry_price_missing_count": len(rows) - entry_available,
            "apply_snapshot": str(apply_snapshot).upper(),
            "ledger_path": str(ledger_path),
            "backup_path": backup_path,
            "official_decision_impact": OFFICIAL_DECISION_IMPACT,
            "official_signal_freeze_ledger_modified": OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED,
            "paper_trading_ledger_modified": PAPER_TRADING_LEDGER_MODIFIED,
            "forbidden_modified": FORBIDDEN_MODIFIED,
        }
    ]


def apply_snapshot_to_ledger(root: Path, rows: list[dict[str, object]], signal_date: str, run: str) -> tuple[Path, str]:
    ledger_path = root / "state/v18/shadow_portfolios/V18_SHADOW_PORTFOLIO_DAILY_SNAPSHOT_LEDGER.csv"
    backup_dir = root / "archive/v18/shadow_portfolio_snapshot_backups" / run
    backup_dir.mkdir(parents=True, exist_ok=True)
    if ledger_path.exists():
        shutil.copy2(ledger_path, backup_dir / ledger_path.name)
        existing = read_csv(ledger_path)
    else:
        write_text(backup_dir / "NO_EXISTING_LEDGER.txt", "No existing dedicated shadow portfolio ledger before apply.\n")
        existing = []
    kept = [row for row in existing if not (row.get("signal_date") == signal_date and row.get("snapshot_layer") == SNAPSHOT_LAYER)]
    write_csv(ledger_path, kept + rows, DETAIL_FIELDS)
    return ledger_path, str(backup_dir)


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("|", "/") for item in row) + " |")
    return "\n".join(lines)


def build_report(run: str, status: str, signal_date: str, signal_source: str, apply_snapshot: bool, preview: list[dict[str, object]], backup_path: str) -> str:
    total_rows = sum(int(row.get("holding_count", 0) or 0) for row in preview)
    entry_available = sum(int(row.get("entry_price_available_count", 0) or 0) for row in preview)
    table = md_table(
        ["Portfolio", "持仓数", "权重和", "Entry 可用", "1D", "3D", "5D", "10D", "20D"],
        [
            [
                row.get("portfolio_id", ""),
                row.get("holding_count", ""),
                row.get("weight_sum", ""),
                row.get("entry_price_available_count", ""),
                row.get("forward_1d_fillable_count", ""),
                row.get("forward_3d_fillable_count", ""),
                row.get("forward_5d_fillable_count", ""),
                row.get("forward_10d_fillable_count", ""),
                row.get("forward_20d_fillable_count", ""),
            ]
            for row in preview
        ],
    )
    return "\n".join(
        [
            "# V18.37C Shadow Portfolio Forward Bridge",
            "",
            f"生成时间：{now_iso()}",
            f"RUN_ID：{run}",
            f"状态：{status}",
            f"信号日期：{signal_date}",
            f"日期来源：{signal_source}",
            f"ApplySnapshot：{str(apply_snapshot).upper()}",
            f"Backup：{backup_path or 'N/A'}",
            "",
            "本层是 V18.37B 影子组合的研究快照与未来归因桥。它只冻结影子组合持仓和权重到专用 research ledger，用于未来 1D/3D/5D/10D/20D 组合级 forward return 比较。",
            "",
            "它不是实盘交易，不是官方决策逻辑，也不修改官方排名、因子权重、候选别名、官方 signal freeze ledger、纸交易账本、账户状态、broker/API 或订单逻辑。",
            "",
            "## 总览",
            "",
            md_table([ "指标", "数值" ], [["Portfolio 数", len(preview)], ["Snapshot 行数", total_rows], ["Entry price 可用", entry_available], ["Entry price 缺失", total_rows - entry_available]]),
            "",
            "## Forward Readiness",
            "",
            table if preview else "V18.37B 输出缺失或没有可快照持仓。",
            "",
            "## 安全状态",
            "",
            "- AUTO_TRADE: DISABLED",
            "- AUTO_SELL: DISABLED",
            "- OFFICIAL_DECISION_IMPACT: NONE",
            "- FACTOR_WEIGHTS_MODIFIED: FALSE",
            "- OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE",
            "- PAPER_TRADING_LEDGER_MODIFIED: FALSE",
            "- FORBIDDEN_MODIFIED: FALSE",
            "",
        ]
    )


def build_read_first(
    status: str,
    mode: str,
    run: str,
    signal_date: str,
    signal_source: str,
    rows: list[dict[str, object]],
    preview: list[dict[str, object]],
    ledger_path: Path,
    apply_snapshot: bool,
    backup_path: str,
) -> str:
    def fill_count(field: str) -> int:
        return sum(1 for row in rows if str(row.get(field, "")).strip())

    entry_available = sum(1 for row in rows if to_float(row.get("entry_price")) is not None)
    lines = [
        f"STATUS: {status}",
        f"MODE: {mode}",
        f"RUN_ID: {run}",
        f"SIGNAL_DATE: {signal_date}",
        f"SIGNAL_DATE_SOURCE: {signal_source}",
        f"TOTAL_PORTFOLIO_COUNT: {len(preview)}",
        f"TOTAL_SNAPSHOT_ROWS: {len(rows)}",
        f"ENTRY_PRICE_AVAILABLE_COUNT: {entry_available}",
        f"ENTRY_PRICE_MISSING_COUNT: {len(rows) - entry_available}",
        f"FORWARD_1D_FILLABLE_COUNT: {fill_count('forward_1d_return')}",
        f"FORWARD_3D_FILLABLE_COUNT: {fill_count('forward_3d_return')}",
        f"FORWARD_5D_FILLABLE_COUNT: {fill_count('forward_5d_return')}",
        f"FORWARD_10D_FILLABLE_COUNT: {fill_count('forward_10d_return')}",
        f"FORWARD_20D_FILLABLE_COUNT: {fill_count('forward_20d_return')}",
        f"LEDGER_PATH: {ledger_path}",
        f"APPLY_SNAPSHOT: {str(apply_snapshot).upper()}",
    ]
    if apply_snapshot:
        lines.append(f"BACKUP_PATH: {backup_path}")
    lines.extend(
        [
            f"AUTO_TRADE: {AUTO_TRADE}",
            f"AUTO_SELL: {AUTO_SELL}",
            f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
            f"FACTOR_WEIGHTS_MODIFIED: {FACTOR_WEIGHTS_MODIFIED}",
            f"OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED: {OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED}",
            f"PAPER_TRADING_LEDGER_MODIFIED: {PAPER_TRADING_LEDGER_MODIFIED}",
            f"FORBIDDEN_MODIFIED: {FORBIDDEN_MODIFIED}",
            "",
        ]
    )
    return "\n".join(lines)


def run(root: Path, apply_snapshot: bool) -> int:
    ops_dir = root / "outputs/v18/ops"
    read_center_dir = root / "outputs/v18/read_center"
    ledger_path = root / "state/v18/shadow_portfolios/V18_SHADOW_PORTFOLIO_DAILY_SNAPSHOT_LEDGER.csv"
    run = run_id()
    mode = "APPLY_SHADOW_PORTFOLIO_SNAPSHOT" if apply_snapshot else "PREVIEW_ONLY_SHADOW_PORTFOLIO_SNAPSHOT"

    rows, signal_date, status, signal_source = build_snapshot_rows(root, run)
    backup_path = ""
    if rows and status == "OK" and apply_snapshot:
        ledger_path, backup_path = apply_snapshot_to_ledger(root, rows, signal_date, run)

    preview = portfolio_preview(rows)
    readiness = readiness_rows(rows)
    summary = summary_rows(rows, signal_date, signal_source, apply_snapshot, status, ledger_path, backup_path)

    write_csv(ops_dir / "V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_SUMMARY.csv", summary, list(summary[0].keys()))
    write_csv(ops_dir / "V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_DETAIL.csv", rows, DETAIL_FIELDS)
    write_csv(ops_dir / "V18_37C_SHADOW_PORTFOLIO_FORWARD_READINESS.csv", readiness, ["metric", "count", "total_snapshot_rows", "status"])
    write_csv(
        ops_dir / "V18_37C_SHADOW_PORTFOLIO_ATTRIBUTION_PREVIEW.csv",
        preview,
        [
            "portfolio_id",
            "holding_count",
            "weight_sum",
            "entry_price_available_count",
            "entry_price_missing_count",
            "forward_1d_fillable_count",
            "forward_3d_fillable_count",
            "forward_5d_fillable_count",
            "forward_10d_fillable_count",
            "forward_20d_fillable_count",
            "max_single_name_weight",
            "min_single_name_weight",
            "official_decision_impact",
            "research_only",
        ],
    )

    report = build_report(run, status, signal_date, signal_source, apply_snapshot, preview, backup_path)
    write_text(read_center_dir / "V18_37C_SHADOW_PORTFOLIO_FORWARD_BRIDGE_REPORT.md", report)
    write_text(read_center_dir / "V18_CURRENT_SHADOW_PORTFOLIO_FORWARD_BRIDGE.md", report)
    read_first = build_read_first(status, mode, run, signal_date, signal_source, rows, preview, ledger_path, apply_snapshot, backup_path)
    write_text(ops_dir / "V18_37C_READ_FIRST.txt", read_first)
    print(read_first, end="")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.37C shadow portfolio daily snapshot forward bridge")
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--apply-snapshot", action="store_true")
    args = parser.parse_args()
    return run(Path(args.root).resolve(), args.apply_snapshot)


if __name__ == "__main__":
    raise SystemExit(main())
