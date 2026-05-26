from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import csv
import json
import math

import pandas as pd

from qutumn.common.paths import OUTPUTS_V16, ensure_dir
from qutumn.backtest.strategy_lab import collect_strategy_records, StrategyRecord
from qutumn.data.historical_prices import load_backtest_config, load_price_matrix, write_price_audit


@dataclass
class BacktestResult:
    strategy_name: str
    status: str
    ticker_count: int
    data_start: str
    data_end: str
    trading_days: int
    total_return_pct: float | None
    annual_return_pct: float | None
    benchmark_total_return_pct: float | None
    benchmark_annual_return_pct: float | None
    max_drawdown_pct: float | None
    volatility_pct: float | None
    sharpe: float | None
    win_rate_pct: float | None
    trade_count: int
    rebalance_count: int
    turnover_pct: float | None
    estimated_cost_drag_pct: float | None
    avg_exposure_pct: float | None
    avg_position_count: float | None
    latest_positions: str
    cap_constrained_executable_ratio_pct: float | None
    reason: str


def _pct(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value * 100.0, 4)


def _safe_float(value: object, default: float) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: object, default: int) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _max_drawdown(equity: pd.Series) -> float | None:
    if equity.empty:
        return None

    running_max = equity.cummax()
    dd = equity / running_max - 1.0
    return float(dd.min())


def _annual_return(total_return: float, days: int) -> float | None:
    if days <= 0:
        return None

    try:
        return float((1.0 + total_return) ** (252.0 / days) - 1.0)
    except Exception:
        return None


def _clean_weights(weights: dict[str, float]) -> dict[str, float]:
    cleaned: dict[str, float] = {}

    for ticker, weight in weights.items():
        if weight is None:
            continue
        if weight <= 0:
            continue
        cleaned[str(ticker)] = float(weight)

    total = sum(cleaned.values())

    if total > 1.0 and total > 0:
        cleaned = {ticker: weight / total for ticker, weight in cleaned.items()}

    return cleaned


def _series_available(hist: pd.DataFrame, ticker: str, min_rows: int) -> bool:
    if ticker not in hist.columns:
        return False
    return len(hist[ticker].dropna()) >= min_rows


def _latest_value(series: pd.Series) -> float | None:
    s = series.dropna()
    if s.empty:
        return None
    return float(s.iloc[-1])


def _indicator_snapshot(hist: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "latest": hist.ffill().iloc[-1],
        "ret20": hist.pct_change(20).iloc[-1],
        "ret60": hist.pct_change(60).iloc[-1],
        "sma50": hist.rolling(50).mean().iloc[-1],
        "sma100": hist.rolling(100).mean().iloc[-1],
        "sma200": hist.rolling(200).mean().iloc[-1],
        "high60": hist.rolling(60).max().iloc[-1],
    }


def _strategy_target_weights(record: StrategyRecord, strategy_hist: pd.DataFrame, full_hist: pd.DataFrame) -> dict[str, float]:
    tickers = [ticker for ticker in record.tickers if ticker in strategy_hist.columns]

    if len(strategy_hist) < 60 or not tickers:
        return {}

    snap = _indicator_snapshot(strategy_hist)
    latest = snap["latest"]
    ret20 = snap["ret20"]
    ret60 = snap["ret60"]
    sma50 = snap["sma50"]
    sma100 = snap["sma100"]
    sma200 = snap["sma200"]
    high60 = snap["high60"]
    dd60 = latest / high60 - 1.0

    max_single = record.max_single_position_pct
    if max_single is None:
        max_single = 0.25

    weights: dict[str, float] = {}

    if record.strategy_name == "momentum_core":
        scores: dict[str, float] = {}

        for ticker in tickers:
            if pd.isna(latest.get(ticker)) or pd.isna(sma50.get(ticker)) or pd.isna(ret60.get(ticker)):
                continue

            trend_ok = latest[ticker] > sma50[ticker]
            momentum_ok = ret20.get(ticker, -999) > 0 and ret60.get(ticker, -999) > 0

            if trend_ok and momentum_ok:
                scores[ticker] = float(0.6 * ret60[ticker] + 0.4 * ret20[ticker])

        selected = [x[0] for x in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]]

        for ticker in selected:
            weights[ticker] = min(max_single, 0.60 / max(1, len(selected)))

        return _clean_weights(weights)

    if record.strategy_name == "pullback_balanced":
        scores: dict[str, float] = {}

        for ticker in tickers:
            if pd.isna(latest.get(ticker)) or pd.isna(sma200.get(ticker)) or pd.isna(dd60.get(ticker)):
                continue

            trend_ok = latest[ticker] > sma200[ticker]
            pullback_ok = dd60[ticker] <= -0.025 and dd60[ticker] >= -0.14

            if trend_ok and pullback_ok:
                scores[ticker] = float(0.7 * ret60.get(ticker, 0.0) - 0.3 * abs(dd60.get(ticker, 0.0)))

        selected = [x[0] for x in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]]

        for ticker in selected:
            weights[ticker] = min(max_single, 0.50 / max(1, len(selected)))

        return _clean_weights(weights)

    if record.strategy_name == "defensive_cash":
        if "QQQ" not in full_hist.columns or len(full_hist["QQQ"].dropna()) < 200:
            return {}

        qqq = full_hist["QQQ"].dropna()
        qqq_latest = _latest_value(qqq)
        qqq_sma200 = _latest_value(qqq.rolling(200).mean())

        if qqq_latest is None or qqq_sma200 is None:
            return {}

        market_ok = qqq_latest > qqq_sma200

        if not market_ok:
            return {}

        scores: dict[str, float] = {}

        for ticker in tickers:
            if pd.isna(latest.get(ticker)) or pd.isna(ret60.get(ticker)):
                continue

            if ret60[ticker] > 0 and latest[ticker] > sma100.get(ticker, float("inf")):
                scores[ticker] = float(ret60[ticker])

        selected = [x[0] for x in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]]

        for ticker in selected:
            weights[ticker] = min(max_single, 0.50 / max(1, len(selected)))

        return _clean_weights(weights)

    if record.strategy_name == "leveraged_tactical":
        benchmark_map = {
            "TQQQ": "QQQ",
            "SOXL": "SMH",
        }

        for ticker in tickers:
            benchmark = benchmark_map.get(ticker)

            if benchmark is None:
                continue

            if not _series_available(full_hist, benchmark, 200):
                continue

            if not _series_available(strategy_hist, ticker, 100):
                continue

            bench = full_hist[benchmark].dropna()
            bench_latest = _latest_value(bench)
            bench_sma100 = _latest_value(bench.rolling(100).mean())
            bench_sma200 = _latest_value(bench.rolling(200).mean())
            bench_high60 = _latest_value(bench.rolling(60).max())

            if bench_latest is None or bench_sma100 is None or bench_sma200 is None or bench_high60 is None:
                continue

            bench_dd60 = bench_latest / bench_high60 - 1.0
            bench_ret20 = float(bench.pct_change(20).dropna().iloc[-1]) if len(bench.dropna()) >= 21 else 0.0
            bench_ret60 = float(bench.pct_change(60).dropna().iloc[-1]) if len(bench.dropna()) >= 61 else 0.0

            trend_ok = bench_latest > bench_sma200
            tactical_ok = bench_latest > bench_sma100 and bench_ret20 > 0
            pullback_recovery_ok = bench_dd60 <= -0.02 and bench_ret20 > -0.05
            momentum_ok = bench_ret20 > 0 and bench_ret60 > 0

            if trend_ok and (tactical_ok or pullback_recovery_ok or momentum_ok):
                weights[ticker] = min(max_single, 0.15)

        return _clean_weights(weights)

    if record.strategy_name == "event_locked":
        scores: dict[str, float] = {}

        for ticker in tickers:
            if pd.isna(latest.get(ticker)) or pd.isna(sma100.get(ticker)) or pd.isna(dd60.get(ticker)):
                continue

            trend_ok = latest[ticker] > sma100[ticker]
            pullback_ok = dd60[ticker] <= -0.035 and dd60[ticker] >= -0.16
            momentum_ok = ret60.get(ticker, -999) > 0

            if trend_ok and pullback_ok and momentum_ok:
                scores[ticker] = float(0.5 * ret60.get(ticker, 0.0) + 0.5 * ret20.get(ticker, 0.0))

        selected = [x[0] for x in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:3]]

        for ticker in selected:
            weights[ticker] = min(max_single, 0.60 / max(1, len(selected)))

        return _clean_weights(weights)

    return {}


def _cap_constrained_executable_ratio(
    record: StrategyRecord,
    prices: pd.DataFrame,
    initial_capital_jpy: float,
    fx_rate_jpy_per_usd: float,
) -> float | None:
    tickers = [ticker for ticker in record.tickers if ticker in prices.columns]

    if not tickers or prices.empty:
        return None

    latest = prices.ffill().iloc[-1]

    max_single = record.max_single_position_pct
    if max_single is None:
        max_single = 0.25

    per_position_budget_usd = initial_capital_jpy * max_single / fx_rate_jpy_per_usd

    valid = 0
    checked = 0

    for ticker in tickers:
        price = latest.get(ticker)

        if pd.isna(price):
            continue

        checked += 1

        if float(price) <= per_position_budget_usd:
            valid += 1

    if checked == 0:
        return None

    return valid / checked


def run_single_backtest(
    record: StrategyRecord,
    all_prices: pd.DataFrame,
    rebalance_frequency_days: int,
    initial_capital_jpy: float,
    fx_rate_jpy_per_usd: float,
    commission_bps: float,
    slippage_bps: float,
) -> BacktestResult:
    tickers = [ticker for ticker in record.tickers if ticker in all_prices.columns]

    if not tickers:
        return BacktestResult(
            strategy_name=record.strategy_name,
            status="NO_DATA",
            ticker_count=0,
            data_start="",
            data_end="",
            trading_days=0,
            total_return_pct=None,
            annual_return_pct=None,
            benchmark_total_return_pct=None,
            benchmark_annual_return_pct=None,
            max_drawdown_pct=None,
            volatility_pct=None,
            sharpe=None,
            win_rate_pct=None,
            trade_count=0,
            rebalance_count=0,
            turnover_pct=None,
            estimated_cost_drag_pct=None,
            avg_exposure_pct=None,
            avg_position_count=None,
            latest_positions="",
            cap_constrained_executable_ratio_pct=None,
            reason="No usable price data for this strategy.",
        )

    strategy_prices = all_prices[tickers].copy()
    strategy_prices = strategy_prices.dropna(how="all").ffill()

    if len(strategy_prices) < 260:
        return BacktestResult(
            strategy_name=record.strategy_name,
            status="WAIT_MORE_DATA",
            ticker_count=len(tickers),
            data_start=str(strategy_prices.index.min().date()) if not strategy_prices.empty else "",
            data_end=str(strategy_prices.index.max().date()) if not strategy_prices.empty else "",
            trading_days=len(strategy_prices),
            total_return_pct=None,
            annual_return_pct=None,
            benchmark_total_return_pct=None,
            benchmark_annual_return_pct=None,
            max_drawdown_pct=None,
            volatility_pct=None,
            sharpe=None,
            win_rate_pct=None,
            trade_count=0,
            rebalance_count=0,
            turnover_pct=None,
            estimated_cost_drag_pct=None,
            avg_exposure_pct=None,
            avg_position_count=None,
            latest_positions="",
            cap_constrained_executable_ratio_pct=_pct(_cap_constrained_executable_ratio(record, strategy_prices, initial_capital_jpy, fx_rate_jpy_per_usd)),
            reason="Fewer than 260 trading days. Metrics are not reliable.",
        )

    returns = strategy_prices.pct_change().fillna(0.0)

    weights: dict[str, float] = {}
    previous_weights: dict[str, float] = {}

    transaction_cost_rate = (commission_bps + slippage_bps) / 10000.0

    net_returns: list[float] = []
    cost_returns: list[float] = []
    equity_values: list[float] = [1.0]
    equity_dates: list[pd.Timestamp] = [strategy_prices.index[0]]

    exposure_values: list[float] = []
    position_counts: list[int] = []

    trade_count = 0
    rebalance_count = 0
    turnover_sum = 0.0

    for i in range(1, len(strategy_prices)):
        cost = 0.0

        if (i - 1) % max(1, rebalance_frequency_days) == 0:
            strategy_hist = strategy_prices.iloc[:i]
            full_hist = all_prices.loc[:strategy_prices.index[i - 1]].copy().ffill()

            new_weights = _strategy_target_weights(record, strategy_hist, full_hist)

            changed = set(previous_weights.keys()).union(new_weights.keys())
            turnover = sum(abs(new_weights.get(ticker, 0.0) - previous_weights.get(ticker, 0.0)) for ticker in changed)

            if turnover > 0.000001:
                trade_count += sum(1 for ticker in changed if abs(new_weights.get(ticker, 0.0) - previous_weights.get(ticker, 0.0)) > 0.000001)
                rebalance_count += 1
                turnover_sum += turnover
                cost = turnover * transaction_cost_rate

            previous_weights = dict(new_weights)
            weights = dict(new_weights)

        gross_daily_ret = 0.0

        for ticker, weight in weights.items():
            if ticker in returns.columns:
                ticker_ret = returns[ticker].iloc[i]
                if not pd.isna(ticker_ret):
                    gross_daily_ret += weight * float(ticker_ret)

        net_daily_ret = gross_daily_ret - cost

        net_returns.append(net_daily_ret)
        cost_returns.append(cost)
        equity_values.append(equity_values[-1] * (1.0 + net_daily_ret))
        equity_dates.append(strategy_prices.index[i])
        exposure_values.append(sum(weights.values()))
        position_counts.append(len(weights))

    equity = pd.Series(equity_values, index=equity_dates)
    port_ret = pd.Series(net_returns, index=strategy_prices.index[1:])

    total_return = float(equity.iloc[-1] - 1.0)
    annual_return = _annual_return(total_return, len(port_ret))
    max_dd = _max_drawdown(equity)

    vol = float(port_ret.std() * math.sqrt(252.0)) if len(port_ret) > 1 else None

    sharpe = None
    if vol is not None and vol > 0:
        sharpe = float((port_ret.mean() * 252.0) / vol)

    win_rate = float((port_ret > 0).mean()) if len(port_ret) > 0 else None

    if "QQQ" in all_prices.columns:
        benchmark_prices = all_prices["QQQ"].reindex(strategy_prices.index).ffill()
    else:
        benchmark_prices = strategy_prices.mean(axis=1)

    benchmark_returns = benchmark_prices.pct_change().fillna(0.0)
    benchmark_equity = (1.0 + benchmark_returns).cumprod()
    benchmark_total = float(benchmark_equity.iloc[-1] - 1.0)
    benchmark_annual = _annual_return(benchmark_total, len(benchmark_returns))

    latest_positions = ";".join([f"{ticker}:{weight:.3f}" for ticker, weight in weights.items()])
    estimated_cost_drag = sum(cost_returns)

    return BacktestResult(
        strategy_name=record.strategy_name,
        status="METRICS_AVAILABLE",
        ticker_count=len(tickers),
        data_start=str(strategy_prices.index.min().date()),
        data_end=str(strategy_prices.index.max().date()),
        trading_days=len(strategy_prices),
        total_return_pct=_pct(total_return),
        annual_return_pct=_pct(annual_return),
        benchmark_total_return_pct=_pct(benchmark_total),
        benchmark_annual_return_pct=_pct(benchmark_annual),
        max_drawdown_pct=_pct(max_dd),
        volatility_pct=_pct(vol),
        sharpe=round(sharpe, 4) if sharpe is not None else None,
        win_rate_pct=_pct(win_rate),
        trade_count=trade_count,
        rebalance_count=rebalance_count,
        turnover_pct=_pct(turnover_sum),
        estimated_cost_drag_pct=_pct(estimated_cost_drag),
        avg_exposure_pct=_pct(sum(exposure_values) / len(exposure_values)) if exposure_values else None,
        avg_position_count=round(sum(position_counts) / len(position_counts), 4) if position_counts else None,
        latest_positions=latest_positions,
        cap_constrained_executable_ratio_pct=_pct(_cap_constrained_executable_ratio(record, strategy_prices, initial_capital_jpy, fx_rate_jpy_per_usd)),
        reason="Cost-aware backtest skeleton metrics generated. Not yet approved for execution.",
    )


def write_backtest_outputs(results: list[BacktestResult]) -> tuple:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out_dir = ensure_dir(OUTPUTS_V16 / "backtest")

    csv_path = out_dir / "V16_BACKTEST_METRICS.csv"
    md_path = out_dir / "V16_BACKTEST_REPORT.md"
    json_path = out_dir / "V16_BACKTEST_METRICS.json"

    fieldnames = list(BacktestResult.__dataclass_fields__.keys())

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow(result.__dict__)

    lines: list[str] = []
    lines.append("# V16 Backtest Report")
    lines.append("")
    lines.append(f"生成时间：`{generated_at}`")
    lines.append("")
    lines.append("## 1. 当前结论")
    lines.append("")
    lines.append("V16.2C 已经修正 leveraged_tactical 的基准上下文，并加入初版交易成本和滑点。")
    lines.append("")
    lines.append("重要限制：这仍然是研究骨架回测，不能直接用于实盘。")
    lines.append("")
    lines.append("## 2. 策略回测指标")
    lines.append("")
    lines.append("| 策略 | 状态 | 年化收益% | QQQ年化% | 最大回撤% | Sharpe | 交易次数 | 换手% | 成本拖累% | 平均暴露% | 真实可执行率% |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for result in results:
        lines.append(
            f"| `{result.strategy_name}` | `{result.status}` | `{result.annual_return_pct}` | "
            f"`{result.benchmark_annual_return_pct}` | `{result.max_drawdown_pct}` | `{result.sharpe}` | "
            f"`{result.trade_count}` | `{result.turnover_pct}` | `{result.estimated_cost_drag_pct}` | "
            f"`{result.avg_exposure_pct}` | `{result.cap_constrained_executable_ratio_pct}` |"
        )

    lines.append("")
    lines.append("## 3. 解释")
    lines.append("")
    lines.append("- 年化收益是扣除初版交易成本后的净值结果。")
    lines.append("- 成本拖累按 commission_bps + slippage_bps 估算。")
    lines.append("- 真实可执行率按 200,000 JPY、单仓上限、155 USDJPY 估算，只代表价格可负担性。")
    lines.append("- leveraged_tactical 现在可以读取 QQQ/SMH 作为 TQQQ/SOXL 的基准上下文。")
    lines.append("- 当前仍未纳入真实成交反馈、事件日历、税务、真实券商导出文件。")
    lines.append("")
    lines.append("## 4. 下一步")
    lines.append("")
    lines.append("下一步进入 V16.3：Execution Plan，开始把回测候选策略转化为乐天真实可执行计划。")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "generated_at": generated_at,
        "results": [result.__dict__ for result in results],
    }

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return md_path, csv_path, json_path


def run_backtest_runner() -> int:
    cfg = load_backtest_config()

    lookback_days = _safe_int(cfg.get("lookback_days"), 756)
    rebalance_days = _safe_int(cfg.get("rebalance_frequency_days"), 5)

    capital = cfg.get("capital", {})
    if not isinstance(capital, dict):
        capital = {}

    assumptions = cfg.get("assumptions", {})
    if not isinstance(assumptions, dict):
        assumptions = {}

    data_cfg = cfg.get("data", {})
    if not isinstance(data_cfg, dict):
        data_cfg = {}

    initial_capital_jpy = _safe_float(capital.get("initial_capital_jpy"), 200000.0)
    fx_rate_jpy_per_usd = _safe_float(capital.get("fx_rate_jpy_per_usd"), 155.0)
    commission_bps = _safe_float(assumptions.get("commission_bps"), 5.0)
    slippage_bps = _safe_float(assumptions.get("slippage_bps"), 10.0)
    allow_yfinance_download = bool(data_cfg.get("allow_yfinance_download", True))

    records = collect_strategy_records()

    all_tickers: list[str] = []
    for record in records:
        all_tickers.extend(record.tickers)

    extra_context_tickers = ["QQQ", "SMH", "SPY"]
    all_tickers.extend(extra_context_tickers)
    all_tickers = list(dict.fromkeys([ticker.upper() for ticker in all_tickers]))

    price_result = load_price_matrix(
        tickers=all_tickers,
        lookback_days=lookback_days,
        allow_yfinance_download=allow_yfinance_download,
    )

    price_audit_md, price_audit_csv = write_price_audit(price_result.records)

    results: list[BacktestResult] = []

    for record in records:
        result = run_single_backtest(
            record=record,
            all_prices=price_result.prices,
            rebalance_frequency_days=rebalance_days,
            initial_capital_jpy=initial_capital_jpy,
            fx_rate_jpy_per_usd=fx_rate_jpy_per_usd,
            commission_bps=commission_bps,
            slippage_bps=slippage_bps,
        )
        results.append(result)

    md_path, csv_path, json_path = write_backtest_outputs(results)

    print("")
    print("V16 cost-aware backtest runner completed.")
    print(f"- strategies: {len(results)}")
    print(f"- price_audit: {price_audit_md}")
    print(f"- backtest_report: {md_path}")
    print(f"- backtest_csv: {csv_path}")
    print(f"- backtest_json: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run_backtest_runner())
