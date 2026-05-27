#!/usr/bin/env python
"""V18.36B paper trading forward return filler.

Reads existing V18.36A paper entries and fills paper-only forward outcomes from
validated local price cache when available. It never creates real orders.
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
PORTFOLIOS = ["TOP20_EQUAL_WEIGHT", "TOP50_EQUAL_WEIGHT", "TOP100_EQUAL_WEIGHT", "FULL318_EQUAL_WEIGHT_OBSERVATION"]


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
    if not text:
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


def load_price_history(root: Path, ticker: str) -> list[dict[str, object]]:
    path = root / "state/v18/price_cache" / f"{ticker}.csv"
    rows = read_csv(path, required=False)
    out: list[dict[str, object]] = []
    seen_dates: set[str] = set()
    for r in rows:
        date = get_col(r, "date", "price_date")[:10]
        close = as_float(get_col(r, "close", "adj_close", "latest_close"))
        if not date or date in seen_dates:
            continue
        seen_dates.add(date)
        if close is None or close <= 0:
            continue
        out.append({"date": date, "close": close, "source": str(path)})
    out.sort(key=lambda x: str(x["date"]))
    return out


def maybe_online_prices(ticker: str) -> list[dict[str, object]]:
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
    seen_dates: set[str] = set()
    for idx, row in df.iterrows():
        date = str(idx.date())
        close = as_float(row.get(close_col))
        if date not in seen_dates and close is not None and close > 0:
            seen_dates.add(date)
            out.append({"date": date, "close": close, "source": "TRANSIENT_YFINANCE_NO_CACHE_WRITE"})
    out.sort(key=lambda x: str(x["date"]))
    return out


def pick_entries(root: Path) -> tuple[list[dict[str, str]], str]:
    state_ledger = root / "state/v18/paper_trading/V18_PAPER_TRADING_LEDGER.csv"
    rows = read_csv(state_ledger, required=False)
    if rows:
        return rows, str(state_ledger)
    entry_plan = root / "outputs/v18/paper_trading/V18_36A_PAPER_ENTRY_PLAN.csv"
    rows = read_csv(entry_plan)
    return rows, str(entry_plan)


def latest_run_entries(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    run_ids = sorted({r.get("paper_run_id", "") for r in rows if r.get("paper_run_id", "")})
    if not run_ids:
        return rows
    latest = run_ids[-1]
    return [r for r in rows if r.get("paper_run_id") == latest]


def forward_for_entry(
    entry: dict[str, str],
    history: list[dict[str, object]],
    horizon: int,
    cost_return: float,
) -> dict[str, object]:
    entry_price = as_float(entry.get("entry_price"))
    entry_date = entry.get("entry_price_date", "")
    if entry_price is None or entry_price <= 0 or not entry_date:
        status = "ENTRY_PRICE_MISSING"
        return {"target_exit_date": "", "exit_price": "", "exit_price_date": "", "exit_price_source": "", "gross_return": "", "estimated_cost_return": fmt_num(cost_return, 8), "net_return_after_cost": "", "outcome_status": status, "failure_reason": status}
    if not history:
        return {"target_exit_date": "", "exit_price": "", "exit_price_date": "", "exit_price_source": "", "gross_return": "", "estimated_cost_return": fmt_num(cost_return, 8), "net_return_after_cost": "", "outcome_status": "PRICE_DATA_UNAVAILABLE", "failure_reason": "PRICE_CACHE_MISSING_OR_EMPTY"}
    after = [r for r in history if str(r["date"]) > entry_date]
    if len(after) < horizon:
        target = after[-1]["date"] if after else ""
        return {"target_exit_date": target, "exit_price": "", "exit_price_date": "", "exit_price_source": history[-1]["source"], "gross_return": "", "estimated_cost_return": fmt_num(cost_return, 8), "net_return_after_cost": "", "outcome_status": "PENDING_FUTURE_PRICE", "failure_reason": f"HORIZON_{horizon}D_NOT_AVAILABLE_IN_PRICE_CACHE"}
    exit_row = after[horizon - 1]
    exit_price = as_float(exit_row["close"])
    if exit_price is None or exit_price <= 0:
        return {"target_exit_date": exit_row["date"], "exit_price": "", "exit_price_date": "", "exit_price_source": exit_row["source"], "gross_return": "", "estimated_cost_return": fmt_num(cost_return, 8), "net_return_after_cost": "", "outcome_status": "INVALID_PRICE_DATA", "failure_reason": "EXIT_PRICE_INVALID"}
    gross = (exit_price / entry_price) - 1.0
    return {
        "target_exit_date": exit_row["date"],
        "exit_price": fmt_num(exit_price),
        "exit_price_date": exit_row["date"],
        "exit_price_source": exit_row["source"],
        "gross_return": fmt_num(gross, 8),
        "estimated_cost_return": fmt_num(cost_return, 8),
        "net_return_after_cost": fmt_num(gross - cost_return, 8),
        "outcome_status": "FILLED",
        "failure_reason": "",
    }


def avg(values: list[float]) -> str:
    return "" if not values else fmt_num(sum(values) / len(values), 8)


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


def rank_group(value: object) -> str:
    rank = as_int(value)
    if rank <= 20:
        return "TOP20"
    if rank <= 50:
        return "TOP50_EX_TOP20"
    if rank <= 100:
        return "TOP100_EX_TOP50"
    return "FULL318_EX_TOP100"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="D:/us-tech-quant")
    ap.add_argument("--update-paper-trading-forward-returns", action="store_true")
    ap.add_argument("--use-yfinance-for-paper-forward-prices", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    ensure_dirs(root)
    run_id = f"V18_36B_PAPER_FORWARD_RETURN_FILLER_{now_ts()}"
    generated_at = now_iso()
    warnings: list[str] = []
    fails: list[str] = []
    backup_path = ""
    paper_state_updated = False

    out_dir = root / "outputs/v18/paper_trading"
    ops_dir = root / "outputs/v18/ops"
    read_dir = root / "outputs/v18/read_center"
    paths = {
        "forward": out_dir / "V18_36B_PAPER_FORWARD_RETURNS_FILLED.csv",
        "performance": out_dir / "V18_36B_PAPER_PORTFOLIO_PERFORMANCE_UPDATED.csv",
        "attrib": out_dir / "V18_36B_FORWARD_ATTRIBUTION_BY_BUCKET_UPDATED.csv",
        "benchmark": out_dir / "V18_36B_BENCHMARK_COMPARISON_UPDATED.csv",
        "fill_status": out_dir / "V18_36B_FORWARD_FILL_STATUS.csv",
        "summary": ops_dir / "V18_36B_PAPER_FORWARD_RETURN_FILLER_SUMMARY.csv",
        "report": read_dir / "V18_36B_PAPER_FORWARD_RETURN_FILLER_REPORT.md",
        "current_report": read_dir / "V18_CURRENT_PAPER_FORWARD_RETURN_FILLER.md",
        "read_first": ops_dir / "V18_36B_READ_FIRST.txt",
    }

    try:
        all_entries, entry_source = pick_entries(root)
        entries = latest_run_entries(all_entries)
    except Exception as exc:
        fails.append(f"PAPER_ENTRY_SOURCE_READ_FAILED: {exc}")
        entries = []
        entry_source = ""
    if not entries:
        fails.append("NO_PAPER_ENTRIES_FOUND")

    duplicate_keys = 0
    seen_keys: set[tuple[str, str, str, str]] = set()
    for r in entries:
        key = (r.get("paper_run_id", ""), r.get("signal_date", ""), r.get("portfolio_name", ""), r.get("ticker", ""))
        if key in seen_keys:
            duplicate_keys += 1
        seen_keys.add(key)
    if duplicate_keys:
        fails.append(f"DUPLICATE_PAPER_ENTRY_KEYS={duplicate_keys}")

    latest_signal_date = entries[0].get("signal_date", "") if entries else ""
    paper_run_id = entries[0].get("paper_run_id", "") if entries else ""
    portfolio_count = len({r.get("portfolio_name", "") for r in entries if r.get("portfolio_name", "")})

    history_cache: dict[str, list[dict[str, object]]] = {}

    def history(ticker: str) -> list[dict[str, object]]:
        if ticker not in history_cache:
            hist = load_price_history(root, ticker)
            if not hist and args.use_yfinance_for_paper_forward_prices:
                hist = maybe_online_prices(ticker)
                if hist:
                    warnings.append(f"USED_TRANSIENT_YFINANCE_FOR_{ticker}")
            history_cache[ticker] = hist
        return history_cache[ticker]

    forward_rows: list[dict[str, object]] = []
    for e in entries:
        ticker = e.get("ticker", "").strip().upper()
        cost_bps = (as_float(e.get("estimated_commission_bps"), 0.0) or 0.0) + (as_float(e.get("estimated_slippage_bps"), 0.0) or 0.0)
        cost_return = cost_bps / 10000.0
        hist = history(ticker)
        for h in HORIZONS:
            f = forward_for_entry(e, hist, h, cost_return)
            forward_rows.append(
                {
                    "paper_run_id": e.get("paper_run_id", ""),
                    "signal_date": e.get("signal_date", ""),
                    "portfolio_name": e.get("portfolio_name", ""),
                    "ticker": ticker,
                    "candidate_rank": e.get("candidate_rank", ""),
                    "entry_price": e.get("entry_price", ""),
                    "entry_price_date": e.get("entry_price_date", ""),
                    "horizon": f"{h}D",
                    "target_exit_date": f["target_exit_date"],
                    "exit_price": f["exit_price"],
                    "exit_price_date": f["exit_price_date"],
                    "exit_price_source": f["exit_price_source"],
                    "gross_return": f["gross_return"],
                    "estimated_cost_return": f["estimated_cost_return"],
                    "net_return_after_cost": f["net_return_after_cost"],
                    "outcome_status": f["outcome_status"],
                    "failure_reason": f["failure_reason"],
                    "evidence_sources": f"{entry_source};{f['exit_price_source']}",
                }
            )

    def bench_return(ticker: str, signal_date: str, horizon: int) -> tuple[str, bool]:
        hist = history(ticker)
        if not hist:
            return "", False
        on_before = [r for r in hist if str(r["date"]) <= signal_date]
        entry = on_before[-1] if on_before else None
        if entry is None:
            return "", False
        after = [r for r in hist if str(r["date"]) > str(entry["date"])]
        if len(after) < horizon:
            return "", True
        return fmt_num((float(after[horizon - 1]["close"]) / float(entry["close"])) - 1.0, 8), True

    spy_available = bool(history("SPY"))
    qqq_available = bool(history("QQQ"))
    if not spy_available:
        warnings.append("SPY_BENCHMARK_MISSING")
    if not qqq_available:
        warnings.append("QQQ_BENCHMARK_MISSING")

    perf_rows: list[dict[str, object]] = []
    benchmark_rows: list[dict[str, object]] = []
    fill_status_rows: list[dict[str, object]] = []
    for portfolio in sorted({r.get("portfolio_name", "") for r in entries if r.get("portfolio_name", "")}):
        for h in HORIZONS:
            htext = f"{h}D"
            rows = [r for r in forward_rows if r["portfolio_name"] == portfolio and r["horizon"] == htext]
            filled = [r for r in rows if r["outcome_status"] == "FILLED"]
            pending = [r for r in rows if r["outcome_status"] == "PENDING_FUTURE_PRICE"]
            unavailable = [r for r in rows if r["outcome_status"] in {"PRICE_DATA_UNAVAILABLE", "ENTRY_PRICE_MISSING", "INVALID_PRICE_DATA"}]
            gross_vals = [as_float(r["gross_return"]) for r in filled if as_float(r["gross_return"]) is not None]
            net_vals = [as_float(r["net_return_after_cost"]) for r in filled if as_float(r["net_return_after_cost"]) is not None]
            best = max(filled, key=lambda r: as_float(r["net_return_after_cost"], -999.0) or -999.0)["ticker"] if filled else ""
            worst = min(filled, key=lambda r: as_float(r["net_return_after_cost"], 999.0) or 999.0)["ticker"] if filled else ""
            spy_ret, _ = bench_return("SPY", latest_signal_date, h)
            qqq_ret, _ = bench_return("QQQ", latest_signal_date, h)
            net_avg = as_float(avg([v for v in net_vals if v is not None]))
            spy_f = as_float(spy_ret)
            qqq_f = as_float(qqq_ret)
            perf_rows.append(
                {
                    "paper_run_id": paper_run_id,
                    "signal_date": latest_signal_date,
                    "portfolio_name": portfolio,
                    "horizon": htext,
                    "ticker_count": len(rows),
                    "filled_count": len(filled),
                    "pending_count": len(pending),
                    "gross_equal_weight_return": avg([v for v in gross_vals if v is not None]),
                    "net_equal_weight_return": fmt_num(net_avg, 8),
                    "win_rate": avg([1.0 if (as_float(r["gross_return"], 0.0) or 0.0) > 0 else 0.0 for r in filled]),
                    "best_ticker": best,
                    "worst_ticker": worst,
                    "benchmark_spy_return": spy_ret,
                    "benchmark_qqq_return": qqq_ret,
                    "excess_return_vs_spy": fmt_num("" if net_avg is None or spy_f is None else net_avg - spy_f, 8),
                    "excess_return_vs_qqq": fmt_num("" if net_avg is None or qqq_f is None else net_avg - qqq_f, 8),
                    "performance_status": "FILLED" if filled else "PENDING_FUTURE_PRICE",
                }
            )
            fill_status_rows.append(
                {
                    "paper_run_id": paper_run_id,
                    "signal_date": latest_signal_date,
                    "portfolio_name": portfolio,
                    "horizon": htext,
                    "total_entries": len(rows),
                    "fillable_count": len(filled),
                    "pending_count": len(pending),
                    "unavailable_count": len(unavailable),
                    "fill_rate": fmt_num((len(filled) / len(rows)) if rows else 0.0, 8),
                    "status": "FILLED" if filled and not pending and not unavailable else "PENDING_OR_PARTIAL",
                }
            )
            for bench, bret in [("SPY", spy_ret), ("QQQ", qqq_ret)]:
                bf = as_float(bret)
                benchmark_rows.append(
                    {
                        "paper_run_id": paper_run_id,
                        "signal_date": latest_signal_date,
                        "portfolio_name": portfolio,
                        "horizon": htext,
                        "benchmark": bench,
                        "portfolio_net_return_after_cost": fmt_num(net_avg, 8),
                        "benchmark_return": bret,
                        "excess_return_after_cost": fmt_num("" if net_avg is None or bf is None else net_avg - bf, 8),
                        "comparison_status": "FILLED" if net_avg is not None and bf is not None else "PENDING_OR_MISSING_PRICE",
                    }
                )

    full_entries = [e for e in entries if e.get("portfolio_name") == "FULL318_EQUAL_WEIGHT_OBSERVATION"] or entries
    full_forward = [r for r in forward_rows if r["portfolio_name"] == "FULL318_EQUAL_WEIGHT_OBSERVATION"] or forward_rows
    forward_index = {(r["ticker"], r["horizon"]): r for r in full_forward}
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for e in full_entries:
        groups[("RANK_BUCKET", rank_group(e.get("candidate_rank")))].append(e)
        groups[("FACTOR_SCORE_BUCKET", score_bucket(e.get("factor_score"), "FACTOR_SCORE"))].append(e)
        groups[("TECHNICAL_TIMING_BUCKET", score_bucket(e.get("technical_timing_score"), "TECHNICAL_TIMING"))].append(e)
        groups[("TOP_CANDIDATE_GROUP", rank_group(e.get("candidate_rank")))].append(e)
    attrib_rows: list[dict[str, object]] = []
    for (bucket_type, bucket_name), members in sorted(groups.items()):
        row: dict[str, object] = {
            "paper_run_id": paper_run_id,
            "signal_date": latest_signal_date,
            "bucket_type": bucket_type,
            "bucket_name": bucket_name,
            "ticker_count": len(members),
            "average_rank": avg([as_float(m.get("candidate_rank"), 0.0) or 0.0 for m in members]),
            "average_score": avg([as_float(m.get("candidate_score"), 0.0) or 0.0 for m in members]),
        }
        total_filled = 0
        total_pending = 0
        wins: list[float] = []
        for h in HORIZONS:
            htext = f"{h}D"
            vals = []
            net_vals = []
            pending = 0
            for m in members:
                fr = forward_index.get((m.get("ticker", ""), htext))
                if fr and fr.get("outcome_status") == "FILLED":
                    g = as_float(fr.get("gross_return"))
                    n = as_float(fr.get("net_return_after_cost"))
                    if g is not None:
                        vals.append(g)
                        wins.append(1.0 if g > 0 else 0.0)
                    if n is not None:
                        net_vals.append(n)
                else:
                    pending += 1
            total_filled += len(vals)
            total_pending += pending
            row[f"average_gross_return_{h}d"] = avg(vals)
            row[f"average_net_return_{h}d"] = avg(net_vals)
        row["fillable_count"] = total_filled
        row["pending_count"] = total_pending
        row["win_rate"] = avg(wins)
        row["attribution_status"] = "FILLED_OR_PARTIAL" if total_filled else "PENDING_FUTURE_PRICE"
        attrib_rows.append(row)

    horizon_summary: dict[int, dict[str, int]] = {}
    for h in HORIZONS:
        htext = f"{h}D"
        rows = [r for r in forward_rows if r["horizon"] == htext]
        filled = sum(1 for r in rows if r["outcome_status"] == "FILLED")
        pending = len(rows) - filled
        horizon_summary[h] = {"total": len(rows), "filled": filled, "pending": pending}
        if pending:
            warnings.append(f"FORWARD_{h}D_PENDING_COUNT={pending}")
    if not args.update_paper_trading_forward_returns:
        warnings.append("PAPER_FORWARD_STATE_UPDATE_NOT_REQUESTED")

    if args.update_paper_trading_forward_returns and not fails:
        try:
            state_dir = root / "state/v18/paper_trading"
            state_dir.mkdir(parents=True, exist_ok=True)
            backup_dir = root / "archive/v18/paper_trading_forward_return_backups" / f"V18_36B_{now_ts()}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = str(backup_dir)
            for name in ["V18_PAPER_TRADING_LEDGER.csv", "V18_PAPER_POSITIONS.csv", "V18_PAPER_PORTFOLIO_STATE.csv"]:
                src = state_dir / name
                if src.exists():
                    shutil.copy2(src, backup_dir / name)
            by_entry: dict[tuple[str, str, str, str], dict[str, object]] = defaultdict(dict)
            for fr in forward_rows:
                key = (str(fr["paper_run_id"]), str(fr["signal_date"]), str(fr["portfolio_name"]), str(fr["ticker"]))
                h = str(fr["horizon"]).lower()
                by_entry[key][f"forward_{h}_status"] = fr["outcome_status"]
                by_entry[key][f"forward_{h}_gross_return"] = fr["gross_return"]
                by_entry[key][f"forward_{h}_net_return_after_cost"] = fr["net_return_after_cost"]
                by_entry[key][f"forward_{h}_exit_date"] = fr["exit_price_date"]
            updated_entries: list[dict[str, object]] = []
            for e in entries:
                row = dict(e)
                key = (e.get("paper_run_id", ""), e.get("signal_date", ""), e.get("portfolio_name", ""), e.get("ticker", ""))
                row.update(by_entry.get(key, {}))
                row["official_decision_impact"] = OFFICIAL_DECISION_IMPACT
                row["auto_trade"] = AUTO_TRADE
                row["auto_sell"] = AUTO_SELL
                updated_entries.append(row)
            ledger_fields = list(updated_entries[0].keys()) if updated_entries else []
            write_csv(state_dir / "V18_PAPER_TRADING_LEDGER.csv", updated_entries, ledger_fields)
            write_csv(state_dir / "V18_PAPER_POSITIONS.csv", updated_entries, ledger_fields)
            write_csv(state_dir / "V18_PAPER_PORTFOLIO_STATE.csv", perf_rows, list(perf_rows[0].keys()) if perf_rows else ["paper_run_id"])
            paper_state_updated = True
        except Exception as exc:
            fails.append(f"PAPER_FORWARD_STATE_UPDATE_FAILED: {exc}")

    status = "OK_V18_36B_PAPER_FORWARD_RETURN_FILLER_READY"
    if fails:
        status = "FAIL_V18_36B_PAPER_FORWARD_RETURN_FILLER_FAILED"
    elif warnings:
        status = "WARN_V18_36B_PAPER_FORWARD_RETURN_FILLER_REVIEW_NEEDED"

    summary = {
        "status": status,
        "run_id": run_id,
        "generated_at": generated_at,
        "update_paper_trading_forward_returns": str(bool(args.update_paper_trading_forward_returns)).upper(),
        "use_yfinance_for_paper_forward_prices": str(bool(args.use_yfinance_for_paper_forward_prices)).upper(),
        "latest_signal_date": latest_signal_date,
        "paper_entry_count": len(entries),
        "portfolio_count": portfolio_count,
        "forward_1d_total_count": horizon_summary.get(1, {}).get("total", 0),
        "forward_1d_filled_count": horizon_summary.get(1, {}).get("filled", 0),
        "forward_1d_pending_count": horizon_summary.get(1, {}).get("pending", 0),
        "forward_3d_total_count": horizon_summary.get(3, {}).get("total", 0),
        "forward_3d_filled_count": horizon_summary.get(3, {}).get("filled", 0),
        "forward_3d_pending_count": horizon_summary.get(3, {}).get("pending", 0),
        "forward_5d_total_count": horizon_summary.get(5, {}).get("total", 0),
        "forward_5d_filled_count": horizon_summary.get(5, {}).get("filled", 0),
        "forward_5d_pending_count": horizon_summary.get(5, {}).get("pending", 0),
        "forward_10d_total_count": horizon_summary.get(10, {}).get("total", 0),
        "forward_10d_filled_count": horizon_summary.get(10, {}).get("filled", 0),
        "forward_10d_pending_count": horizon_summary.get(10, {}).get("pending", 0),
        "forward_20d_total_count": horizon_summary.get(20, {}).get("total", 0),
        "forward_20d_filled_count": horizon_summary.get(20, {}).get("filled", 0),
        "forward_20d_pending_count": horizon_summary.get(20, {}).get("pending", 0),
        "benchmark_spy_available": str(spy_available).upper(),
        "benchmark_qqq_available": str(qqq_available).upper(),
        "paper_state_updated": str(paper_state_updated).upper(),
        "backup_path": backup_path,
        "warning_count": len(warnings),
        "fail_count": len(fails),
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "forbidden_modified": "FALSE",
    }

    forward_fields = [
        "paper_run_id", "signal_date", "portfolio_name", "ticker", "candidate_rank", "entry_price",
        "entry_price_date", "horizon", "target_exit_date", "exit_price", "exit_price_date", "exit_price_source",
        "gross_return", "estimated_cost_return", "net_return_after_cost", "outcome_status", "failure_reason",
        "evidence_sources",
    ]
    perf_fields = [
        "paper_run_id", "signal_date", "portfolio_name", "horizon", "ticker_count", "filled_count",
        "pending_count", "gross_equal_weight_return", "net_equal_weight_return", "win_rate", "best_ticker",
        "worst_ticker", "benchmark_spy_return", "benchmark_qqq_return", "excess_return_vs_spy",
        "excess_return_vs_qqq", "performance_status",
    ]
    attrib_fields = [
        "paper_run_id", "signal_date", "bucket_type", "bucket_name", "ticker_count", "fillable_count",
        "pending_count", "average_gross_return_1d", "average_net_return_1d", "average_gross_return_3d",
        "average_net_return_3d", "average_gross_return_5d", "average_net_return_5d",
        "average_gross_return_10d", "average_net_return_10d", "average_gross_return_20d",
        "average_net_return_20d", "win_rate", "average_rank", "average_score", "attribution_status",
    ]
    write_csv(paths["forward"], forward_rows, forward_fields)
    write_csv(paths["performance"], perf_rows, perf_fields)
    write_csv(paths["attrib"], attrib_rows, attrib_fields)
    write_csv(paths["benchmark"], benchmark_rows, list(benchmark_rows[0].keys()) if benchmark_rows else ["paper_run_id"])
    write_csv(paths["fill_status"], fill_status_rows, list(fill_status_rows[0].keys()) if fill_status_rows else ["paper_run_id"])
    write_csv(paths["summary"], [summary], list(summary.keys()))

    horizon_table = "\n".join(
        f"| {h}D | {horizon_summary.get(h, {}).get('total', 0)} | {horizon_summary.get(h, {}).get('filled', 0)} | {horizon_summary.get(h, {}).get('pending', 0)} |"
        for h in HORIZONS
    )
    perf_sample = "\n".join(
        f"| {r['portfolio_name']} | {r['horizon']} | {r['filled_count']} | {r['pending_count']} | {r['net_equal_weight_return']} | {r['performance_status']} |"
        for r in perf_rows[:20]
    )
    bench_sample = "\n".join(
        f"| {r['portfolio_name']} | {r['horizon']} | {r['benchmark']} | {r['benchmark_return']} | {r['comparison_status']} |"
        for r in benchmark_rows[:20]
    )
    attrib_sample = "\n".join(
        f"| {r['bucket_type']} | {r['bucket_name']} | {r['fillable_count']} | {r['pending_count']} | {r['attribution_status']} |"
        for r in attrib_rows[:20]
    )
    report = f"""# V18.36B 模拟交易前向收益填充

## 运行结论

V18.36A 已经建好 paper entry；本任务不重复建仓，只读取既有 paper ledger / entry plan，并在未来价格进入本地缓存后填充 forward returns。当前状态为 `{status}`。

| 项目 | 数值 |
|---|---:|
| paper entry count | {len(entries)} |
| portfolio count | {portfolio_count} |
| signal date | {latest_signal_date} |
| paper state updated | {str(paper_state_updated).upper()} |
| backup path | {backup_path} |

## Horizon Fillability

| horizon | total | filled | pending |
|---|---:|---:|---:|
{horizon_table}

如果全部或部分 pending，表示未来价格尚未进入缓存，或对应 horizon 尚不可计算；这不是收益计算失败，也不会伪造价格。

## Portfolio Performance

| portfolio | horizon | filled | pending | net equal weight return | status |
|---|---:|---:|---:|---:|---|
{perf_sample}

## Benchmark Comparison

| portfolio | horizon | benchmark | benchmark return | status |
|---|---:|---|---:|---|
{bench_sample}

SPY benchmark available: {str(spy_available).upper()}  
QQQ benchmark available: {str(qqq_available).upper()}

## Attribution Summary

| bucket type | bucket | fillable | pending | status |
|---|---|---:|---:|---|
{attrib_sample}

## Operator Next Action

继续按日运行本 filler。若本地 price cache 更新后出现 post-entry 价格，V18.36B 会自动把可填 horizon 标记为 FILLED；需要写入 paper state 时显式使用 -UpdatePaperTradingForwardReturns。

## Final Conclusion

This is paper trading only. No real orders were created. No broker/API/account/trading execution logic was modified. AUTO_TRADE DISABLED, AUTO_SELL DISABLED, OFFICIAL_DECISION_IMPACT NONE.
"""
    write_text(paths["report"], report)
    write_text(paths["current_report"], report)

    read_first = [
        f"STATUS: {status}",
        f"RUN_ID: {run_id}",
        f"UPDATE_PAPER_TRADING_FORWARD_RETURNS: {str(bool(args.update_paper_trading_forward_returns)).upper()}",
        f"USE_YFINANCE_FOR_PAPER_FORWARD_PRICES: {str(bool(args.use_yfinance_for_paper_forward_prices)).upper()}",
        f"LATEST_SIGNAL_DATE: {latest_signal_date}",
        f"PAPER_ENTRY_COUNT: {len(entries)}",
        f"PORTFOLIO_COUNT: {portfolio_count}",
        f"FORWARD_1D_FILLED_COUNT: {horizon_summary.get(1, {}).get('filled', 0)}",
        f"FORWARD_1D_PENDING_COUNT: {horizon_summary.get(1, {}).get('pending', 0)}",
        f"FORWARD_3D_FILLED_COUNT: {horizon_summary.get(3, {}).get('filled', 0)}",
        f"FORWARD_3D_PENDING_COUNT: {horizon_summary.get(3, {}).get('pending', 0)}",
        f"FORWARD_5D_FILLED_COUNT: {horizon_summary.get(5, {}).get('filled', 0)}",
        f"FORWARD_5D_PENDING_COUNT: {horizon_summary.get(5, {}).get('pending', 0)}",
        f"FORWARD_10D_FILLED_COUNT: {horizon_summary.get(10, {}).get('filled', 0)}",
        f"FORWARD_10D_PENDING_COUNT: {horizon_summary.get(10, {}).get('pending', 0)}",
        f"FORWARD_20D_FILLED_COUNT: {horizon_summary.get(20, {}).get('filled', 0)}",
        f"FORWARD_20D_PENDING_COUNT: {horizon_summary.get(20, {}).get('pending', 0)}",
        f"SPY_BENCHMARK_AVAILABLE: {str(spy_available).upper()}",
        f"QQQ_BENCHMARK_AVAILABLE: {str(qqq_available).upper()}",
        f"PAPER_STATE_UPDATED: {str(paper_state_updated).upper()}",
        f"BACKUP_PATH: {backup_path}",
        f"WARNING_COUNT: {len(warnings)}",
        f"FAIL_COUNT: {len(fails)}",
        f"REPORT: {paths['report']}",
        f"CURRENT_REPORT: {paths['current_report']}",
        f"FORWARD_RETURNS_CSV: {paths['forward']}",
        f"PORTFOLIO_PERFORMANCE_CSV: {paths['performance']}",
        f"ATTRIBUTION_CSV: {paths['attrib']}",
        f"BENCHMARK_COMPARISON_CSV: {paths['benchmark']}",
        f"FILL_STATUS_CSV: {paths['fill_status']}",
        f"SUMMARY_CSV: {paths['summary']}",
        f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"AUTO_TRADE: {AUTO_TRADE}",
        f"AUTO_SELL: {AUTO_SELL}",
        "FORBIDDEN_MODIFIED: FALSE",
    ]
    write_text(paths["read_first"], "\n".join(read_first) + "\n")

    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
