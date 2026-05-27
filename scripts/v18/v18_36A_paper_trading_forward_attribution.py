#!/usr/bin/env python
"""V18.36A paper trading and forward attribution baseline.

This module is paper-trading only. It reads the latest 318 freeze and current
ranked candidates, builds equal-weight simulated portfolios, and reports
forward outcomes from local price cache when available.
"""

from __future__ import annotations

import argparse
import csv
import math
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path


OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
HORIZONS = [1, 3, 5, 10, 20]
PORTFOLIOS = [
    ("TOP20_EQUAL_WEIGHT", 20),
    ("TOP50_EQUAL_WEIGHT", 50),
    ("TOP100_EQUAL_WEIGHT", 100),
    ("FULL318_EQUAL_WEIGHT_OBSERVATION", 318),
]


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dirs(root: Path) -> None:
    for rel in ["outputs/v18/paper_trading", "outputs/v18/ops", "outputs/v18/read_center"]:
        (root / rel).mkdir(parents=True, exist_ok=True)


def read_csv(path: Path, required: bool = True) -> list[dict[str, str]]:
    if not path.exists():
        if required:
            raise FileNotFoundError(str(path))
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def as_float(value: object, default: float | None = None) -> float | None:
    if value is None:
        return default
    text = str(value).strip()
    if text == "":
        return default
    try:
        v = float(text)
    except ValueError:
        return default
    if math.isnan(v) or math.isinf(v):
        return default
    return v


def as_int(value: object, default: int = 0) -> int:
    f = as_float(value)
    return default if f is None else int(f)


def fmt_num(value: object, digits: int = 6) -> str:
    f = as_float(value)
    if f is None:
        return ""
    return f"{f:.{digits}f}".rstrip("0").rstrip(".")


def get_col(row: dict[str, str], *names: str) -> str:
    lower = {k.lower(): v for k, v in row.items()}
    for name in names:
        if name in row:
            return row.get(name, "")
        if name.lower() in lower:
            return lower[name.lower()]
    return ""


def latest_freeze_rows(rows: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
    dates = sorted({r.get("signal_date", "") for r in rows if r.get("signal_date", "")})
    if not dates:
        raise ValueError("freeze ledger has no signal_date")
    latest = dates[-1]
    return latest, [r for r in rows if r.get("signal_date") == latest]


def load_price_history(root: Path, ticker: str) -> list[dict[str, object]]:
    path = root / "state/v18/price_cache" / f"{ticker}.csv"
    rows = read_csv(path, required=False)
    out: list[dict[str, object]] = []
    for r in rows:
        date = get_col(r, "date", "price_date")
        close = as_float(get_col(r, "close", "adj_close", "latest_close"))
        if date and close is not None:
            out.append({"date": date[:10], "close": close, "source": str(path)})
    out.sort(key=lambda x: str(x["date"]))
    return out


def maybe_online_prices(ticker: str) -> list[dict[str, object]]:
    """Optional transient online lookup. It never writes cache and failure is nonfatal."""
    try:
        import yfinance as yf  # type: ignore
    except Exception:
        return []
    try:
        df = yf.download(ticker, period="3mo", progress=False, auto_adjust=False)
    except Exception:
        return []
    if df is None or df.empty:
        return []
    close_col = "Close" if "Close" in df.columns else "Adj Close" if "Adj Close" in df.columns else None
    if close_col is None:
        return []
    out: list[dict[str, object]] = []
    for idx, row in df.iterrows():
        close = as_float(row.get(close_col))
        if close is not None:
            out.append({"date": str(idx.date()), "close": close, "source": "TRANSIENT_YFINANCE_NO_CACHE_WRITE"})
    out.sort(key=lambda x: str(x["date"]))
    return out


def entry_price(history: list[dict[str, object]], signal_date: str) -> dict[str, object]:
    if not history:
        return {"price": "", "date": "", "source": "", "status": "ENTRY_PRICE_MISSING", "warning": "LOCAL_PRICE_CACHE_MISSING_OR_EMPTY"}
    on_after = [r for r in history if str(r["date"]) >= signal_date]
    if on_after:
        r = on_after[0]
        return {"price": r["close"], "date": r["date"], "source": r["source"], "status": "ENTRY_PRICE_AVAILABLE", "warning": ""}
    before = [r for r in history if str(r["date"]) < signal_date]
    if before:
        r = before[-1]
        return {"price": r["close"], "date": r["date"], "source": r["source"], "status": "ENTRY_PRICE_STALE_WARNING", "warning": "ENTRY_PRICE_BEFORE_SIGNAL_DATE"}
    return {"price": "", "date": "", "source": "", "status": "ENTRY_PRICE_MISSING", "warning": "NO_CLOSE_ON_OR_BEFORE_SIGNAL_DATE"}


def forward_exit(history: list[dict[str, object]], entry_date: str, horizon: int) -> dict[str, object]:
    if not history or not entry_date:
        return {"price": "", "date": "", "status": "PENDING_FUTURE_PRICE", "reason": "ENTRY_PRICE_MISSING"}
    after = [r for r in history if str(r["date"]) > entry_date]
    if len(after) >= horizon:
        r = after[horizon - 1]
        return {"price": r["close"], "date": r["date"], "status": "FILLED_FORWARD_PRICE", "reason": ""}
    return {"price": "", "date": "", "status": "PENDING_FUTURE_PRICE", "reason": f"HORIZON_{horizon}D_NOT_AVAILABLE_IN_LOCAL_CACHE"}


def score_bucket(value: object, prefix: str) -> str:
    v = as_float(value)
    if v is None:
        return f"{prefix}_MISSING"
    if v >= 80:
        return f"{prefix}_80_PLUS"
    if v >= 60:
        return f"{prefix}_60_TO_80"
    if v >= 40:
        return f"{prefix}_40_TO_60"
    return f"{prefix}_BELOW_40"


def rank_group(rank: int) -> str:
    if rank <= 20:
        return "TOP20"
    if rank <= 50:
        return "TOP50_EX_TOP20"
    if rank <= 100:
        return "TOP100_EX_TOP50"
    return "FULL318_EX_TOP100"


def average(values: list[float]) -> str:
    return "" if not values else fmt_num(sum(values) / len(values), 8)


def build_attribution(
    paper_run_id: str,
    signal_date: str,
    candidates: list[dict[str, object]],
    forward_rows: list[dict[str, object]],
    addition_map: dict[str, str],
) -> list[dict[str, object]]:
    by_ticker_horizon: dict[tuple[str, int], dict[str, object]] = {}
    for row in forward_rows:
        if row.get("portfolio_name") == "FULL318_EQUAL_WEIGHT_OBSERVATION":
            horizon_text = str(row.get("horizon", "")).upper().replace("D", "")
            by_ticker_horizon[(str(row["ticker"]), as_int(horizon_text))] = row

    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for c in candidates:
        ticker = str(c["ticker"])
        rank = as_int(c.get("rank"))
        groups[("RANK_BUCKET", rank_group(rank))].append(c)
        groups[("FACTOR_SCORE_BUCKET", score_bucket(c.get("factor_score"), "FACTOR_SCORE"))].append(c)
        groups[("TECHNICAL_TIMING_BUCKET", score_bucket(c.get("technical_timing_score"), "TECHNICAL_TIMING"))].append(c)
        groups[("TOP_CANDIDATE_GROUP", rank_group(rank))].append(c)
        groups[("V18_35F_ADDITION_STATUS", addition_map.get(ticker, "UNKNOWN_V18_35F_STATUS"))].append(c)

    rows: list[dict[str, object]] = []
    for (bucket_type, bucket_name), members in sorted(groups.items()):
        data: dict[str, object] = {
            "paper_run_id": paper_run_id,
            "signal_date": signal_date,
            "bucket_type": bucket_type,
            "bucket_name": bucket_name,
            "ticker_count": len(members),
            "average_rank": average([as_float(m.get("rank"), 0.0) or 0.0 for m in members]),
            "average_score": average([as_float(m.get("candidate_score"), 0.0) or 0.0 for m in members]),
            "attribution_status": "PENDING_FUTURE_PRICE",
        }
        fillable_any = 0
        pending_any = 0
        wins: list[float] = []
        for h in HORIZONS:
            gross: list[float] = []
            net: list[float] = []
            pending = 0
            for m in members:
                fr = by_ticker_horizon.get((str(m["ticker"]), h))
                if fr and fr.get("outcome_status") == "FILLED_FORWARD_PRICE":
                    g = as_float(fr.get("gross_return"))
                    n = as_float(fr.get("net_return_after_cost"))
                    if g is not None:
                        gross.append(g)
                        wins.append(1.0 if g > 0 else 0.0)
                    if n is not None:
                        net.append(n)
                else:
                    pending += 1
            if gross:
                fillable_any += len(gross)
                data["attribution_status"] = "PARTIAL_OR_FILLED_FORWARD_ATTRIBUTION"
            pending_any += pending
            data[f"average_gross_return_{h}d"] = average(gross)
            data[f"average_net_return_{h}d"] = average(net)
        data["fillable_count"] = fillable_any
        data["pending_count"] = pending_any
        data["win_rate"] = average(wins)
        rows.append(data)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="D:/us-tech-quant")
    ap.add_argument("--update-paper-trading-ledger", action="store_true")
    ap.add_argument("--use-yfinance-for-paper-trading-prices", action="store_true")
    ap.add_argument("--paper-capital", type=float, default=100000.0)
    ap.add_argument("--commission-bps", type=float, default=1.0)
    ap.add_argument("--slippage-bps", type=float, default=5.0)
    args = ap.parse_args()

    root = Path(args.root)
    ensure_dirs(root)
    run_id = f"V18_36A_PAPER_TRADING_FORWARD_ATTRIBUTION_{now_ts()}"
    generated_at = now_iso()
    warnings: list[str] = []
    fails: list[str] = []
    backup_path = ""
    paper_ledger_updated = False

    out_dir = root / "outputs/v18/paper_trading"
    ops_dir = root / "outputs/v18/ops"
    read_dir = root / "outputs/v18/read_center"
    paths = {
        "config": out_dir / "V18_36A_PAPER_PORTFOLIO_CONFIG.csv",
        "entry": out_dir / "V18_36A_PAPER_ENTRY_PLAN.csv",
        "positions": out_dir / "V18_36A_PAPER_POSITIONS_PREVIEW.csv",
        "forward": out_dir / "V18_36A_PAPER_FORWARD_RETURNS.csv",
        "daily": out_dir / "V18_36A_PAPER_PORTFOLIO_DAILY_SNAPSHOT.csv",
        "performance": out_dir / "V18_36A_PAPER_PORTFOLIO_PERFORMANCE.csv",
        "attrib": out_dir / "V18_36A_FORWARD_ATTRIBUTION_BY_BUCKET.csv",
        "benchmark": out_dir / "V18_36A_BENCHMARK_COMPARISON.csv",
        "ledger_preview": out_dir / "V18_36A_PAPER_TRADING_LEDGER_PREVIEW.csv",
        "summary": ops_dir / "V18_36A_PAPER_TRADING_FORWARD_ATTRIBUTION_SUMMARY.csv",
        "report": read_dir / "V18_36A_PAPER_TRADING_FORWARD_ATTRIBUTION_REPORT.md",
        "current_report": read_dir / "V18_CURRENT_PAPER_TRADING_FORWARD_ATTRIBUTION.md",
        "read_first": ops_dir / "V18_36A_READ_FIRST.txt",
    }

    try:
        freeze_rows = read_csv(root / "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv")
        signal_date, latest_freeze = latest_freeze_rows(freeze_rows)
        full_candidates_raw = read_csv(root / "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv")
        ranked_candidates_raw = read_csv(root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv", required=False)
        top_candidates_raw = read_csv(root / "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv", required=False)
    except Exception as exc:
        fails.append(f"REQUIRED_INPUT_READ_FAILED: {exc}")
        signal_date = ""
        latest_freeze = []
        full_candidates_raw = []
        ranked_candidates_raw = []
        top_candidates_raw = []

    factor_rows = read_csv(root / "outputs/v18/factor_pack/V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv", required=False)
    tech_rows = read_csv(root / "outputs/v18/technical_timing/V18_35D_FULL_UNIVERSE_TECHNICAL_TIMING.csv", required=False)
    factor_map = {r.get("ticker", ""): r for r in factor_rows}
    tech_map = {r.get("ticker", ""): r for r in tech_rows}

    seen: set[str] = set()
    duplicate_candidate_count = 0
    candidates: list[dict[str, object]] = []
    for row in full_candidates_raw:
        ticker = row.get("ticker", "").strip().upper()
        if not ticker:
            continue
        if ticker in seen:
            duplicate_candidate_count += 1
        seen.add(ticker)
        frow = factor_map.get(ticker, {})
        trow = tech_map.get(ticker, {})
        candidates.append(
            {
                "ticker": ticker,
                "rank": as_int(row.get("rank")),
                "candidate_score": fmt_num(row.get("composite_candidate_score")),
                "factor_score": fmt_num(frow.get("factor_pack_score")),
                "technical_timing_score": fmt_num(trow.get("technical_timing_score")),
                "source_files": "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv;outputs/v18/factor_pack/V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv;outputs/v18/technical_timing/V18_35D_FULL_UNIVERSE_TECHNICAL_TIMING.csv",
            }
        )
    candidates.sort(key=lambda x: as_int(x.get("rank")))
    if duplicate_candidate_count:
        fails.append(f"DUPLICATE_CANDIDATE_TICKERS: {duplicate_candidate_count}")
    if not candidates:
        fails.append("NO_PAPER_PORTFOLIOS_CAN_BE_BUILT")

    cost_return = (args.commission_bps + args.slippage_bps) / 10000.0
    history_cache: dict[str, list[dict[str, object]]] = {}

    def get_history(ticker: str) -> list[dict[str, object]]:
        if ticker not in history_cache:
            hist = load_price_history(root, ticker)
            if not hist and args.use_yfinance_for_paper_trading_prices:
                hist = maybe_online_prices(ticker)
                if hist:
                    warnings.append(f"USED_TRANSIENT_YFINANCE_FOR_{ticker}")
            history_cache[ticker] = hist
        return history_cache[ticker]

    config_rows: list[dict[str, object]] = []
    entry_rows: list[dict[str, object]] = []
    forward_rows: list[dict[str, object]] = []
    for name, size in PORTFOLIOS:
        members = candidates[: min(size, len(candidates))]
        if not members:
            continue
        weight = 1.0 / len(members)
        config_rows.append(
            {
                "paper_run_id": run_id,
                "signal_date": signal_date,
                "portfolio_name": name,
                "target_weight_method": "EQUAL_WEIGHT",
                "paper_capital": fmt_num(args.paper_capital, 2),
                "max_position_count": len(members),
                "commission_bps": args.commission_bps,
                "slippage_bps": args.slippage_bps,
                "leverage": "NONE",
                "shorting": "DISABLED",
                "fractional_shares": "TRUE",
                "official_decision_impact": OFFICIAL_DECISION_IMPACT,
                "auto_trade": AUTO_TRADE,
                "auto_sell": AUTO_SELL,
            }
        )
        for c in members:
            ticker = str(c["ticker"])
            hist = get_history(ticker)
            ent = entry_price(hist, signal_date)
            price = as_float(ent["price"])
            notional = args.paper_capital * weight
            shares = "" if price is None else notional / price
            entry_rows.append(
                {
                    "paper_run_id": run_id,
                    "signal_date": signal_date,
                    "portfolio_name": name,
                    "ticker": ticker,
                    "candidate_rank": c["rank"],
                    "candidate_score": c["candidate_score"],
                    "factor_score": c["factor_score"],
                    "technical_timing_score": c["technical_timing_score"],
                    "entry_price": fmt_num(price),
                    "entry_price_date": ent["date"],
                    "entry_price_source": ent["source"],
                    "target_weight": fmt_num(weight, 8),
                    "paper_capital": fmt_num(args.paper_capital, 2),
                    "paper_notional": fmt_num(notional, 4),
                    "paper_shares": fmt_num(shares, 8),
                    "estimated_commission_bps": args.commission_bps,
                    "estimated_slippage_bps": args.slippage_bps,
                    "estimated_total_cost_usd": fmt_num(notional * cost_return, 4),
                    "entry_status": ent["status"],
                    "warning_reason": ent["warning"],
                    "evidence_sources": c["source_files"],
                }
            )
            for h in HORIZONS:
                exit_info = forward_exit(hist, str(ent["date"]), h)
                exit_price = as_float(exit_info["price"])
                gross = "" if price is None or exit_price is None else (exit_price / price) - 1.0
                net = "" if gross == "" else (as_float(gross) or 0.0) - cost_return
                forward_rows.append(
                    {
                        "paper_run_id": run_id,
                        "signal_date": signal_date,
                        "portfolio_name": name,
                        "ticker": ticker,
                        "candidate_rank": c["rank"],
                        "entry_price": fmt_num(price),
                        "entry_price_date": ent["date"],
                        "horizon": f"{h}D",
                        "exit_price": fmt_num(exit_price),
                        "exit_price_date": exit_info["date"],
                        "gross_return": fmt_num(gross, 8),
                        "estimated_cost_return": fmt_num(cost_return, 8),
                        "net_return_after_cost": fmt_num(net, 8),
                        "outcome_status": exit_info["status"],
                        "failure_reason": exit_info["reason"],
                        "evidence_sources": ent["source"],
                    }
                )

    entry_available = sum(1 for r in entry_rows if r["entry_status"] in {"ENTRY_PRICE_AVAILABLE", "ENTRY_PRICE_STALE_WARNING"})
    entry_missing = sum(1 for r in entry_rows if r["entry_status"] == "ENTRY_PRICE_MISSING")
    stale_entries = sum(1 for r in entry_rows if r["entry_status"] == "ENTRY_PRICE_STALE_WARNING")
    if entry_missing:
        warnings.append(f"ENTRY_PRICE_MISSING_COUNT={entry_missing}")
    if stale_entries:
        warnings.append(f"ENTRY_PRICE_STALE_WARNING_COUNT={stale_entries}")

    horizon_counts = {}
    for h in HORIZONS:
        horizon_counts[h] = sum(1 for r in forward_rows if r["horizon"] == f"{h}D" and r["outcome_status"] == "FILLED_FORWARD_PRICE")
        if horizon_counts[h] < sum(1 for r in forward_rows if r["horizon"] == f"{h}D"):
            warnings.append(f"FORWARD_{h}D_PENDING")
    if not args.update_paper_trading_ledger:
        warnings.append("PAPER_LEDGER_UPDATE_NOT_REQUESTED")

    daily_rows: list[dict[str, object]] = []
    perf_rows: list[dict[str, object]] = []
    for name, _size in PORTFOLIOS:
        erows = [r for r in entry_rows if r["portfolio_name"] == name]
        if not erows:
            continue
        daily_rows.append(
            {
                "paper_run_id": run_id,
                "signal_date": signal_date,
                "portfolio_name": name,
                "entry_count": len(erows),
                "entry_price_available_count": sum(1 for r in erows if r["entry_status"] != "ENTRY_PRICE_MISSING"),
                "entry_price_missing_count": sum(1 for r in erows if r["entry_status"] == "ENTRY_PRICE_MISSING"),
                "paper_capital": fmt_num(args.paper_capital, 2),
                "snapshot_status": "PAPER_ENTRY_PREVIEW_READY",
                "official_decision_impact": OFFICIAL_DECISION_IMPACT,
            }
        )
        for h in HORIZONS:
            frows = [r for r in forward_rows if r["portfolio_name"] == name and r["horizon"] == f"{h}D"]
            gross = [as_float(r["gross_return"]) for r in frows if r["outcome_status"] == "FILLED_FORWARD_PRICE" and as_float(r["gross_return"]) is not None]
            net = [as_float(r["net_return_after_cost"]) for r in frows if r["outcome_status"] == "FILLED_FORWARD_PRICE" and as_float(r["net_return_after_cost"]) is not None]
            perf_rows.append(
                {
                    "paper_run_id": run_id,
                    "signal_date": signal_date,
                    "portfolio_name": name,
                    "horizon": f"{h}D",
                    "ticker_count": len(frows),
                    "fillable_count": len(gross),
                    "pending_count": len(frows) - len(gross),
                    "equal_weight_gross_return": average([g for g in gross if g is not None]),
                    "equal_weight_net_return_after_cost": average([n for n in net if n is not None]),
                    "win_rate": average([1.0 if (g or 0.0) > 0 else 0.0 for g in gross if g is not None]),
                    "performance_status": "FILLED_FORWARD_PRICE" if gross else "PENDING_FUTURE_PRICE",
                }
            )

    diff_rows = read_csv(root / "outputs/v18/forward_test/V18_35F_FREEZE_EXPANSION_DIFF.csv", required=False)
    addition_map = {r.get("ticker", ""): r.get("freeze_action", "UNKNOWN") for r in diff_rows if r.get("ticker")}
    attribution_rows = build_attribution(run_id, signal_date, candidates, forward_rows, addition_map)

    benchmark_rows: list[dict[str, object]] = []
    benchmark_available = 0
    for bench in ["SPY", "QQQ"]:
        hist = get_history(bench)
        ent = entry_price(hist, signal_date)
        if ent["status"] != "ENTRY_PRICE_MISSING":
            benchmark_available += 1
        price = as_float(ent["price"])
        for h in HORIZONS:
            ex = forward_exit(hist, str(ent["date"]), h)
            exit_price = as_float(ex["price"])
            bench_ret = "" if price is None or exit_price is None else (exit_price / price) - 1.0
            for name, _size in PORTFOLIOS:
                prow = next((p for p in perf_rows if p["portfolio_name"] == name and p["horizon"] == f"{h}D"), None)
                pnet = as_float(prow.get("equal_weight_net_return_after_cost")) if prow else None
                bret = as_float(bench_ret)
                benchmark_rows.append(
                    {
                        "paper_run_id": run_id,
                        "signal_date": signal_date,
                        "portfolio_name": name,
                        "benchmark": bench,
                        "horizon": f"{h}D",
                        "benchmark_entry_price": fmt_num(price),
                        "benchmark_entry_date": ent["date"],
                        "benchmark_exit_price": fmt_num(exit_price),
                        "benchmark_exit_date": ex["date"],
                        "benchmark_return": fmt_num(bench_ret, 8),
                        "portfolio_net_return_after_cost": fmt_num(pnet, 8),
                        "excess_return_after_cost": fmt_num("" if pnet is None or bret is None else pnet - bret, 8),
                        "comparison_status": "FILLED_BENCHMARK_COMPARISON" if bret is not None and pnet is not None else "PENDING_OR_MISSING_BENCHMARK_PRICE",
                    }
                )
    benchmark_missing = 2 - benchmark_available
    if benchmark_missing:
        warnings.append(f"BENCHMARK_MISSING_COUNT={benchmark_missing}")

    ledger_preview_rows = []
    for r in entry_rows:
        row = dict(r)
        row["ledger_action"] = "PREVIEW_ONLY" if not args.update_paper_trading_ledger else "PAPER_LEDGER_UPDATE"
        row["official_decision_impact"] = OFFICIAL_DECISION_IMPACT
        row["auto_trade"] = AUTO_TRADE
        row["auto_sell"] = AUTO_SELL
        ledger_preview_rows.append(row)

    if args.update_paper_trading_ledger and not fails:
        try:
            state_dir = root / "state/v18/paper_trading"
            state_dir.mkdir(parents=True, exist_ok=True)
            backup_dir = root / "archive/v18/paper_trading_backups" / f"V18_36A_{now_ts()}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = str(backup_dir)
            for name in ["V18_PAPER_TRADING_LEDGER.csv", "V18_PAPER_POSITIONS.csv", "V18_PAPER_PORTFOLIO_STATE.csv"]:
                src = state_dir / name
                if src.exists():
                    shutil.copy2(src, backup_dir / name)
            ledger_path = state_dir / "V18_PAPER_TRADING_LEDGER.csv"
            existing = read_csv(ledger_path, required=False)
            ledger_fields = list(ledger_preview_rows[0].keys()) if ledger_preview_rows else []
            write_csv(ledger_path, existing + ledger_preview_rows, ledger_fields)
            write_csv(state_dir / "V18_PAPER_POSITIONS.csv", entry_rows, list(entry_rows[0].keys()) if entry_rows else [])
            write_csv(state_dir / "V18_PAPER_PORTFOLIO_STATE.csv", daily_rows, list(daily_rows[0].keys()) if daily_rows else [])
            paper_ledger_updated = True
        except Exception as exc:
            fails.append(f"PAPER_LEDGER_WRITE_FAILED: {exc}")

    status = "OK_V18_36A_PAPER_TRADING_FORWARD_ATTRIBUTION_READY"
    if fails:
        status = "FAIL_V18_36A_PAPER_TRADING_FORWARD_ATTRIBUTION_FAILED"
    elif warnings:
        status = "WARN_V18_36A_PAPER_TRADING_FORWARD_ATTRIBUTION_REVIEW_NEEDED"

    summary = {
        "status": status,
        "run_id": run_id,
        "generated_at": generated_at,
        "update_paper_trading_ledger": str(bool(args.update_paper_trading_ledger)).upper(),
        "use_yfinance_for_paper_trading_prices": str(bool(args.use_yfinance_for_paper_trading_prices)).upper(),
        "latest_signal_date": signal_date,
        "latest_freeze_count": len(latest_freeze),
        "current_full_candidate_count": len(candidates),
        "current_top_candidate_count": len(top_candidates_raw),
        "paper_portfolio_count": len(config_rows),
        "paper_entry_count": len(entry_rows),
        "top20_entry_count": sum(1 for r in entry_rows if r["portfolio_name"] == "TOP20_EQUAL_WEIGHT"),
        "top50_entry_count": sum(1 for r in entry_rows if r["portfolio_name"] == "TOP50_EQUAL_WEIGHT"),
        "top100_entry_count": sum(1 for r in entry_rows if r["portfolio_name"] == "TOP100_EQUAL_WEIGHT"),
        "full318_observation_count": sum(1 for r in entry_rows if r["portfolio_name"] == "FULL318_EQUAL_WEIGHT_OBSERVATION"),
        "entry_price_available_count": entry_available,
        "entry_price_missing_count": entry_missing,
        "forward_1d_fillable_count": horizon_counts.get(1, 0),
        "forward_3d_fillable_count": horizon_counts.get(3, 0),
        "forward_5d_fillable_count": horizon_counts.get(5, 0),
        "forward_10d_fillable_count": horizon_counts.get(10, 0),
        "forward_20d_fillable_count": horizon_counts.get(20, 0),
        "benchmark_available_count": benchmark_available,
        "benchmark_missing_count": benchmark_missing,
        "paper_ledger_updated": str(paper_ledger_updated).upper(),
        "backup_path": backup_path,
        "warning_count": len(warnings),
        "fail_count": len(fails),
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "forbidden_modified": "FALSE",
    }

    entry_fields = [
        "paper_run_id", "signal_date", "portfolio_name", "ticker", "candidate_rank", "candidate_score",
        "factor_score", "technical_timing_score", "entry_price", "entry_price_date", "entry_price_source",
        "target_weight", "paper_capital", "paper_notional", "paper_shares", "estimated_commission_bps",
        "estimated_slippage_bps", "estimated_total_cost_usd", "entry_status", "warning_reason", "evidence_sources",
    ]
    forward_fields = [
        "paper_run_id", "signal_date", "portfolio_name", "ticker", "candidate_rank", "entry_price",
        "entry_price_date", "horizon", "exit_price", "exit_price_date", "gross_return", "estimated_cost_return",
        "net_return_after_cost", "outcome_status", "failure_reason", "evidence_sources",
    ]
    attrib_fields = [
        "paper_run_id", "signal_date", "bucket_type", "bucket_name", "ticker_count", "fillable_count",
        "pending_count", "average_gross_return_1d", "average_net_return_1d", "average_gross_return_3d",
        "average_net_return_3d", "average_gross_return_5d", "average_net_return_5d",
        "average_gross_return_10d", "average_net_return_10d", "average_gross_return_20d",
        "average_net_return_20d", "win_rate", "average_rank", "average_score", "attribution_status",
    ]

    write_csv(paths["config"], config_rows, list(config_rows[0].keys()) if config_rows else ["paper_run_id"])
    write_csv(paths["entry"], entry_rows, entry_fields)
    write_csv(paths["positions"], entry_rows, entry_fields)
    write_csv(paths["forward"], forward_rows, forward_fields)
    write_csv(paths["daily"], daily_rows, list(daily_rows[0].keys()) if daily_rows else ["paper_run_id"])
    write_csv(paths["performance"], perf_rows, list(perf_rows[0].keys()) if perf_rows else ["paper_run_id"])
    write_csv(paths["attrib"], attribution_rows, attrib_fields)
    write_csv(paths["benchmark"], benchmark_rows, list(benchmark_rows[0].keys()) if benchmark_rows else ["paper_run_id"])
    write_csv(paths["ledger_preview"], ledger_preview_rows, list(ledger_preview_rows[0].keys()) if ledger_preview_rows else ["paper_run_id"])
    write_csv(paths["summary"], [summary], list(summary.keys()))

    portfolio_table = "\n".join(
        f"| {r['portfolio_name']} | {r['max_position_count']} | {r['paper_capital']} | {r['commission_bps']} | {r['slippage_bps']} |"
        for r in config_rows
    )
    horizon_table = "\n".join(
        f"| {h}D | {horizon_counts.get(h, 0)} | {sum(1 for r in forward_rows if r['horizon'] == f'{h}D') - horizon_counts.get(h, 0)} |"
        for h in HORIZONS
    )
    sample_table = "\n".join(
        f"| {r['ticker']} | {r['candidate_rank']} | {r['candidate_score']} | {r['entry_price']} | {r['entry_status']} |"
        for r in entry_rows
        if r["portfolio_name"] == "TOP20_EQUAL_WEIGHT"
    )
    report = f"""# V18.36A 模拟交易与前向归因基线

## 运行结论

V18.35H 之后，系统已经形成 318 对齐基线；本步骤开始建立 paper trading 和 forward attribution 的观察层。这里不是实盘交易，不创建真实买卖建议，不发送订单，也不修改 broker/API/account/trading execution 逻辑。

| 项目 | 数值 |
|---|---:|
| latest signal date | {signal_date} |
| latest freeze count | {len(latest_freeze)} |
| current full candidates | {len(candidates)} |
| current top candidates | {len(top_candidates_raw)} |
| paper entries | {len(entry_rows)} |
| entry price available | {entry_available} |
| entry price missing | {entry_missing} |
| paper ledger updated | {str(paper_ledger_updated).upper()} |

## Paper Portfolio

| portfolio | entries | capital | commission bps | slippage bps |
|---|---:|---:|---:|---:|
{portfolio_table}

组合按 Top20 / Top50 / Top100 / Full318 observation 等权构建；不加杠杆，不做空，模拟层允许 fractional shares。默认资金为 {fmt_num(args.paper_capital, 2)} USD，成本假设为 commission {args.commission_bps} bps + slippage {args.slippage_bps} bps。

## Forward Horizon 可填充状态

| horizon | fillable rows | pending rows |
|---|---:|---:|
{horizon_table}

如果本地未来价格还没有覆盖对应 horizon，状态会保持 PENDING_FUTURE_PRICE，不会伪造价格或收益。

## Benchmark

| benchmark | availability |
|---|---|
| SPY | {'AVAILABLE' if get_history('SPY') else 'MISSING'} |
| QQQ | {'AVAILABLE' if get_history('QQQ') else 'MISSING'} |

## Top 20 Entry Sample

| ticker | rank | score | entry price | entry status |
|---|---:|---:|---:|---|
{sample_table}

## Operator Next Action

若仅需要观察，继续使用 preview/report 模式。若要让后续 paper tracking 读取 state/v18/paper_trading/，再显式运行 -UpdatePaperTradingLedger；该模式只写 paper ledger，并会先创建备份。

## Final Conclusion

This is paper trading only. No real orders were created. No broker/API/account/trading execution logic was modified. AUTO_TRADE DISABLED, AUTO_SELL DISABLED, OFFICIAL_DECISION_IMPACT NONE.
"""
    write_text(paths["report"], report)
    write_text(paths["current_report"], report)

    read_first_lines = [
        f"STATUS: {status}",
        f"RUN_ID: {run_id}",
        f"UPDATE_PAPER_TRADING_LEDGER: {str(bool(args.update_paper_trading_ledger)).upper()}",
        f"USE_YFINANCE_FOR_PAPER_TRADING_PRICES: {str(bool(args.use_yfinance_for_paper_trading_prices)).upper()}",
        f"LATEST_SIGNAL_DATE: {signal_date}",
        f"LATEST_FREEZE_COUNT: {len(latest_freeze)}",
        f"CURRENT_FULL_CANDIDATE_COUNT: {len(candidates)}",
        f"CURRENT_TOP_CANDIDATE_COUNT: {len(top_candidates_raw)}",
        f"PAPER_PORTFOLIO_COUNT: {len(config_rows)}",
        f"PAPER_ENTRY_COUNT: {len(entry_rows)}",
        f"TOP20_ENTRY_COUNT: {summary['top20_entry_count']}",
        f"TOP50_ENTRY_COUNT: {summary['top50_entry_count']}",
        f"TOP100_ENTRY_COUNT: {summary['top100_entry_count']}",
        f"FULL318_OBSERVATION_COUNT: {summary['full318_observation_count']}",
        f"ENTRY_PRICE_AVAILABLE_COUNT: {entry_available}",
        f"ENTRY_PRICE_MISSING_COUNT: {entry_missing}",
        f"FORWARD_1D_FILLABLE_COUNT: {horizon_counts.get(1, 0)}",
        f"FORWARD_3D_FILLABLE_COUNT: {horizon_counts.get(3, 0)}",
        f"FORWARD_5D_FILLABLE_COUNT: {horizon_counts.get(5, 0)}",
        f"FORWARD_10D_FILLABLE_COUNT: {horizon_counts.get(10, 0)}",
        f"FORWARD_20D_FILLABLE_COUNT: {horizon_counts.get(20, 0)}",
        f"PAPER_LEDGER_UPDATED: {str(paper_ledger_updated).upper()}",
        f"BACKUP_PATH: {backup_path}",
        f"WARNING_COUNT: {len(warnings)}",
        f"FAIL_COUNT: {len(fails)}",
        f"REPORT: {paths['report']}",
        f"CURRENT_REPORT: {paths['current_report']}",
        f"ENTRY_PLAN_CSV: {paths['entry']}",
        f"FORWARD_RETURNS_CSV: {paths['forward']}",
        f"PORTFOLIO_PERFORMANCE_CSV: {paths['performance']}",
        f"ATTRIBUTION_CSV: {paths['attrib']}",
        f"BENCHMARK_COMPARISON_CSV: {paths['benchmark']}",
        f"SUMMARY_CSV: {paths['summary']}",
        f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"AUTO_TRADE: {AUTO_TRADE}",
        f"AUTO_SELL: {AUTO_SELL}",
        "FORBIDDEN_MODIFIED: FALSE",
    ]
    write_text(paths["read_first"], "\n".join(read_first_lines) + "\n")

    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
