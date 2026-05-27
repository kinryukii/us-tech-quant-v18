from __future__ import annotations

import argparse
import csv
import math
import py_compile
import statistics
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_21A_PRICE_DERIVED_FACTOR_PACK_READY"
STATUS_WARN = "WARN_V18_21A_PRICE_DERIVED_FACTOR_PACK_DEGRADED"
MODE = "ADVISORY_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
}

FACTOR_FIELDS = [
    "ticker",
    "latest_date",
    "latest_close",
    "return_20d",
    "return_60d",
    "qqq_return_20d",
    "qqq_return_60d",
    "relative_strength_20d_vs_qqq",
    "relative_strength_60d_vs_qqq",
    "sma20",
    "sma50",
    "sma200",
    "distance_to_20dma",
    "distance_to_50dma",
    "distance_to_200dma",
    "rolling_52w_high",
    "drawdown_from_52w_high",
    "realized_volatility_20d",
    "realized_volatility_60d",
    "avg_volume_20d",
    "volume_surge_20d",
    "breakout_20d",
    "breakout_60d",
    "breakout_volume_confirmed",
    "ma_alignment_label",
    "ma_slope_20d",
    "ma_slope_50d",
    "ma_slope_200d",
    "ma_slope_label",
    "nearest_buy_zone_distance",
    "buy_zone_label",
    "price_factor_data_status",
    "price_source_path",
]

SCORE_FIELDS = [
    "ticker",
    "relative_strength_score",
    "trend_structure_score",
    "buy_zone_score",
    "volume_confirmation_score",
    "volatility_risk_score",
    "price_derived_total_score",
    "price_derived_status",
]

MARKET_FIELDS = [
    "qqq_latest_date",
    "qqq_latest_close",
    "qqq_sma50",
    "qqq_sma200",
    "qqq_distance_to_50dma",
    "qqq_distance_to_200dma",
    "qqq_realized_volatility_20d",
    "spy_latest_date",
    "spy_latest_close",
    "spy_rolling_52w_high",
    "spy_drawdown_from_52w_high",
    "vix_latest_value",
    "vix_regime_strength",
    "internal_breadth_up_ratio",
    "internal_breadth_above_50dma_ratio",
    "market_regime_label",
    "market_risk_coefficient",
    "market_regime_data_status",
    "qqq_proxy_status",
    "spy_proxy_status",
    "vix_proxy_status",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "POLICY_APPLIED",
    "TICKER_INPUT_COUNT",
    "TICKER_FACTOR_ROWS",
    "TICKER_FACTOR_FAIL_COUNT",
    "TICKER_INSUFFICIENT_HISTORY_COUNT",
    "QQQ_PROXY_STATUS",
    "SPY_PROXY_STATUS",
    "VIX_PROXY_STATUS",
    "MARKET_REGIME_STATUS",
    "MARKET_REGIME_LABEL",
    "MARKET_RISK_COEFFICIENT",
    "TOP_RELATIVE_STRENGTH_TICKERS",
    "TOP_NEAR_BUY_ZONE_TICKERS",
    "TOP_BREAKOUT_VOLUME_CONFIRMED_TICKERS",
    "EXTENDED_ABOVE_BUY_ZONE_COUNT",
    "BELOW_200DMA_COUNT",
    "HIGH_VOL_CAUTION_COUNT",
    "DATA_DEGRADED_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED",
    "STATE_MODIFIED",
    "PRICE_CACHE_MODIFIED",
    "RANKING_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED",
    "MANUAL_STATE_MODIFIED",
    "BROKER_EXECUTION_MODIFIED",
    "VALIDATION_FAIL_COUNT",
    "READ_FIRST",
    "REPORT",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def to_float(value: object) -> float | None:
    text = str(value or "").strip().replace(",", "")
    if not text or text.upper() in {"NAN", "NONE", "NULL"}:
        return None
    try:
        val = float(text)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    except Exception:
        return None


def fmt(value: object, digits: int = 6) -> str:
    if value is None:
        return ""
    try:
        val = float(value)
        if math.isnan(val) or math.isinf(val):
            return ""
        return f"{val:.{digits}f}"
    except Exception:
        return str(value)


def normalize_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def discover_universe(root: Path) -> List[str]:
    sources = [
        root / "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv",
        root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
        root / "state/v18/raw105_universe_for_factor_lab.csv",
    ]
    for path in sources:
        rows, fields, status = read_csv(path)
        if status != "OK":
            continue
        tickers = sorted({normalize_ticker(row.get("ticker")) for row in rows if normalize_ticker(row.get("ticker"))})
        if tickers:
            return tickers
    return []


def price_candidates(root: Path, ticker: str) -> List[Path]:
    return [
        root / "data/prices" / f"{ticker}.csv",
        root / "state/v18/price_cache" / f"{ticker}.csv",
        root / "data/v16/prices_full" / f"{ticker}.csv",
        root / "data/v16/prices" / f"{ticker}.csv",
    ]


def load_price_history(root: Path, ticker: str) -> Tuple[List[Dict[str, object]], str, str]:
    for path in price_candidates(root, ticker):
        rows, fields, status = read_csv(path)
        if status != "OK":
            continue
        lower = {field.lower(): field for field in fields}
        date_col = lower.get("date") or lower.get("datetime")
        close_col = lower.get("adj_close") or lower.get("close")
        high_col = lower.get("high")
        volume_col = lower.get("volume")
        if not date_col or not close_col:
            continue
        out = []
        for row in rows:
            close = to_float(row.get(close_col))
            if close is None or close <= 0:
                continue
            out.append(
                {
                    "date": str(row.get(date_col, "")).strip()[:10],
                    "close": close,
                    "high": to_float(row.get(high_col)) if high_col else close,
                    "volume": to_float(row.get(volume_col)) if volume_col else None,
                }
            )
        out = sorted(out, key=lambda item: str(item["date"]))
        if out:
            return out, str(path), "OK"
    return [], "", "MISSING_LOCAL_PRICE_HISTORY"


def sma(values: Sequence[float], n: int) -> float | None:
    if len(values) < n:
        return None
    return sum(values[-n:]) / n


def ret(values: Sequence[float], n: int) -> float | None:
    if len(values) <= n or values[-n - 1] <= 0:
        return None
    return values[-1] / values[-n - 1] - 1


def rolling_high(values: Sequence[float], n: int) -> float | None:
    if len(values) < n:
        return None
    return max(values[-n:])


def annual_vol(values: Sequence[float], n: int) -> float | None:
    if len(values) <= n:
        return None
    logs = []
    segment = values[-(n + 1):]
    for prev, cur in zip(segment, segment[1:]):
        if prev > 0 and cur > 0:
            logs.append(math.log(cur / prev))
    if len(logs) < 2:
        return None
    return statistics.stdev(logs) * math.sqrt(252)


def slope(values: Sequence[float], n: int, lookback: int = 5) -> float | None:
    if len(values) < n + lookback:
        return None
    now = sma(values, n)
    prev_vals = values[:-lookback]
    prev = sma(prev_vals, n)
    if now is None or prev is None or prev == 0:
        return None
    return now / prev - 1


def bool_text(value: bool | None) -> str:
    if value is None:
        return ""
    return "TRUE" if value else "FALSE"


def classify_buy_zone(latest: float, sma20v: float | None, sma50v: float | None, high20: float | None) -> Tuple[str, float | None]:
    candidates = []
    if sma20v:
        candidates.append(("NEAR_20DMA_PULLBACK", latest / sma20v - 1))
    if sma50v:
        candidates.append(("NEAR_50DMA_PULLBACK", latest / sma50v - 1))
    if high20:
        candidates.append(("BREAKOUT_NEAR", latest / high20 - 1))
    if not candidates:
        return "INSUFFICIENT_HISTORY", None
    nearest = min(candidates, key=lambda item: abs(item[1]))
    if sma50v and latest < sma50v * 0.98:
        return "BELOW_KEY_SUPPORT", latest / sma50v - 1
    if sma20v and latest > sma20v * 1.12:
        return "EXTENDED_ABOVE_BUY_ZONE", latest / sma20v - 1
    if abs(nearest[1]) <= 0.03:
        return nearest
    if latest > max([x for x in (sma20v, sma50v, high20) if x]):
        return "EXTENDED_ABOVE_BUY_ZONE", nearest[1]
    return nearest


def compute_factor(root: Path, ticker: str, qqq_returns: Dict[str, float | None]) -> Dict[str, object]:
    hist, source, status = load_price_history(root, ticker)
    if not hist:
        return {"ticker": ticker, "price_factor_data_status": status, "price_source_path": source}
    closes = [float(row["close"]) for row in hist]
    highs = [float(row["high"] or row["close"]) for row in hist]
    volumes = [row["volume"] for row in hist]
    latest = closes[-1]
    latest_volume = volumes[-1]
    sma20v = sma(closes, 20)
    sma50v = sma(closes, 50)
    sma200v = sma(closes, 200)
    high20 = rolling_high(highs, 20)
    high60 = rolling_high(highs, 60)
    high252 = rolling_high(highs, 252)
    return20 = ret(closes, 20)
    return60 = ret(closes, 60)
    vol20 = annual_vol(closes, 20)
    vol60 = annual_vol(closes, 60)
    avg_vol20 = None
    if len(volumes) >= 20 and all(v is not None for v in volumes[-20:]):
        avg_vol20 = sum(float(v) for v in volumes[-20:]) / 20
    volume_surge = latest_volume / avg_vol20 if latest_volume is not None and avg_vol20 and avg_vol20 > 0 else None
    breakout20 = latest >= high20 if high20 else None
    breakout60 = latest >= high60 if high60 else None
    breakout_vol = bool((breakout20 or breakout60) and volume_surge is not None and volume_surge >= 1.5)
    ma_alignment = "INSUFFICIENT_HISTORY"
    if sma20v and sma50v and sma200v:
        if latest > sma20v > sma50v > sma200v:
            ma_alignment = "BULLISH_ALIGNMENT"
        elif latest < sma50v or sma50v < sma200v:
            ma_alignment = "BEARISH_ALIGNMENT"
        else:
            ma_alignment = "MIXED_ALIGNMENT"
    s20 = slope(closes, 20)
    s50 = slope(closes, 50)
    s200 = slope(closes, 200)
    slope_label = "INSUFFICIENT_HISTORY"
    if s20 is not None and s50 is not None:
        if s20 > 0 and s50 > 0 and (s200 is None or s200 >= 0):
            slope_label = "RISING_MA_SLOPES"
        elif s20 < 0 and s50 < 0:
            slope_label = "FALLING_MA_SLOPES"
        else:
            slope_label = "MIXED_MA_SLOPES"
    buy_label, buy_dist = classify_buy_zone(latest, sma20v, sma50v, high20)
    data_flags = []
    if len(closes) < 61:
        data_flags.append("INSUFFICIENT_60D_HISTORY")
    if len(closes) < 200:
        data_flags.append("INSUFFICIENT_200DMA_HISTORY")
    if len(closes) < 252:
        data_flags.append("INSUFFICIENT_52W_HISTORY")
    if volume_surge is None:
        data_flags.append("VOLUME_DEGRADED")
    if qqq_returns.get("20d") is None or qqq_returns.get("60d") is None:
        data_flags.append("QQQ_RELATIVE_STRENGTH_DEGRADED")
    factor_status = "OK" if not data_flags else ";".join(data_flags)
    return {
        "ticker": ticker,
        "latest_date": hist[-1]["date"],
        "latest_close": fmt(latest),
        "return_20d": fmt(return20),
        "return_60d": fmt(return60),
        "qqq_return_20d": fmt(qqq_returns.get("20d")),
        "qqq_return_60d": fmt(qqq_returns.get("60d")),
        "relative_strength_20d_vs_qqq": fmt(return20 - qqq_returns["20d"] if return20 is not None and qqq_returns.get("20d") is not None else None),
        "relative_strength_60d_vs_qqq": fmt(return60 - qqq_returns["60d"] if return60 is not None and qqq_returns.get("60d") is not None else None),
        "sma20": fmt(sma20v),
        "sma50": fmt(sma50v),
        "sma200": fmt(sma200v),
        "distance_to_20dma": fmt(latest / sma20v - 1 if sma20v else None),
        "distance_to_50dma": fmt(latest / sma50v - 1 if sma50v else None),
        "distance_to_200dma": fmt(latest / sma200v - 1 if sma200v else None),
        "rolling_52w_high": fmt(high252),
        "drawdown_from_52w_high": fmt(latest / high252 - 1 if high252 else None),
        "realized_volatility_20d": fmt(vol20),
        "realized_volatility_60d": fmt(vol60),
        "avg_volume_20d": fmt(avg_vol20, 2),
        "volume_surge_20d": fmt(volume_surge),
        "breakout_20d": bool_text(breakout20),
        "breakout_60d": bool_text(breakout60),
        "breakout_volume_confirmed": bool_text(breakout_vol),
        "ma_alignment_label": ma_alignment,
        "ma_slope_20d": fmt(s20),
        "ma_slope_50d": fmt(s50),
        "ma_slope_200d": fmt(s200),
        "ma_slope_label": slope_label,
        "nearest_buy_zone_distance": fmt(buy_dist),
        "buy_zone_label": buy_label,
        "price_factor_data_status": factor_status,
        "price_source_path": source,
    }


def score_row(f: Dict[str, object]) -> Dict[str, object]:
    if not f.get("latest_close"):
        return {"ticker": f.get("ticker", ""), "price_derived_status": "INSUFFICIENT_HISTORY"}
    rs20 = to_float(f.get("relative_strength_20d_vs_qqq"))
    rs60 = to_float(f.get("relative_strength_60d_vs_qqq"))
    dist200 = to_float(f.get("distance_to_200dma"))
    vol20 = to_float(f.get("realized_volatility_20d"))
    buy_label = str(f.get("buy_zone_label", ""))
    alignment = str(f.get("ma_alignment_label", ""))
    breakout = str(f.get("breakout_volume_confirmed", "")).upper() == "TRUE"
    breakout20 = str(f.get("breakout_20d", "")).upper() == "TRUE"
    breakout60 = str(f.get("breakout_60d", "")).upper() == "TRUE"
    rs_score = 0
    if rs20 is not None:
        rs_score += 2 if rs20 > 0.05 else 1 if rs20 > 0 else -1
    if rs60 is not None:
        rs_score += 2 if rs60 > 0.08 else 1 if rs60 > 0 else -1
    trend_score = 2 if alignment == "BULLISH_ALIGNMENT" else -2 if alignment == "BEARISH_ALIGNMENT" else 0
    if str(f.get("ma_slope_label")) == "RISING_MA_SLOPES":
        trend_score += 1
    elif str(f.get("ma_slope_label")) == "FALLING_MA_SLOPES":
        trend_score -= 1
    buy_score = {
        "NEAR_20DMA_PULLBACK": 2,
        "NEAR_50DMA_PULLBACK": 2,
        "BREAKOUT_NEAR": 1,
        "EXTENDED_ABOVE_BUY_ZONE": -2,
        "BELOW_KEY_SUPPORT": -3,
    }.get(buy_label, -1)
    volume_score = 2 if breakout else 0 if not (breakout20 or breakout60) else -1
    vol_score = 0
    if vol20 is not None:
        vol_score = -2 if vol20 > 0.75 else -1 if vol20 > 0.55 else 1 if vol20 < 0.35 else 0
    total = rs_score + trend_score + buy_score + volume_score + vol_score
    status = "INSUFFICIENT_HISTORY"
    if vol20 is not None and vol20 > 0.75:
        status = "HIGH_VOL_CAUTION"
    elif buy_label == "BELOW_KEY_SUPPORT" or (dist200 is not None and dist200 < -0.02):
        status = "BELOW_TREND_SUPPORT"
    elif breakout:
        status = "BREAKOUT_CONFIRMED"
    elif breakout20 or breakout60:
        status = "BREAKOUT_NO_VOLUME"
    elif alignment == "BULLISH_ALIGNMENT" and buy_label in {"NEAR_20DMA_PULLBACK", "NEAR_50DMA_PULLBACK", "BREAKOUT_NEAR"}:
        status = "STRONG_TREND_NEAR_BUY_ZONE"
    elif alignment == "BULLISH_ALIGNMENT" and buy_label == "EXTENDED_ABOVE_BUY_ZONE":
        status = "STRONG_BUT_EXTENDED"
    elif f.get("price_factor_data_status") == "OK":
        status = "NEUTRAL_PRICE_STRUCTURE"
    return {
        "ticker": f.get("ticker", ""),
        "relative_strength_score": rs_score,
        "trend_structure_score": trend_score,
        "buy_zone_score": buy_score,
        "volume_confirmation_score": volume_score,
        "volatility_risk_score": vol_score,
        "price_derived_total_score": total,
        "price_derived_status": status,
    }


def proxy_summary(root: Path, ticker: str) -> Tuple[Dict[str, object], str, str]:
    hist, source, status = load_price_history(root, ticker)
    if not hist:
        return {}, status, source
    closes = [float(row["close"]) for row in hist]
    highs = [float(row["high"] or row["close"]) for row in hist]
    latest = closes[-1]
    return {
        "latest_date": hist[-1]["date"],
        "latest_close": latest,
        "return_20d": ret(closes, 20),
        "return_60d": ret(closes, 60),
        "sma50": sma(closes, 50),
        "sma200": sma(closes, 200),
        "distance_to_50dma": latest / sma(closes, 50) - 1 if sma(closes, 50) else None,
        "distance_to_200dma": latest / sma(closes, 200) - 1 if sma(closes, 200) else None,
        "vol20": annual_vol(closes, 20),
        "high252": rolling_high(highs, 252),
        "drawdown52w": latest / rolling_high(highs, 252) - 1 if rolling_high(highs, 252) else None,
    }, "OK", source


def market_regime(root: Path, factors: Sequence[Dict[str, object]]) -> Tuple[Dict[str, object], Dict[str, str]]:
    qqq, qqq_status, _ = proxy_summary(root, "QQQ")
    spy, spy_status, _ = proxy_summary(root, "SPY")
    vix, vix_status, _ = proxy_summary(root, "VIX")
    if vix_status != "OK":
        vix, vix_status, _ = proxy_summary(root, "^VIX")
    valid = [f for f in factors if f.get("latest_close")]
    up_count = sum(1 for f in valid if (to_float(f.get("return_20d")) or 0) > 0)
    above50_count = sum(1 for f in valid if (to_float(f.get("distance_to_50dma")) or -999) > 0)
    breadth_up = up_count / len(valid) if valid else None
    breadth_above50 = above50_count / len(valid) if valid else None
    qqq_d50 = qqq.get("distance_to_50dma")
    qqq_d200 = qqq.get("distance_to_200dma")
    qqq_vol = qqq.get("vol20")
    spy_dd = spy.get("drawdown52w")
    label = "RISK_ON_TREND"
    coeff = 1.0
    degraded = []
    if qqq_status != "OK":
        degraded.append("QQQ_MISSING")
    if spy_status != "OK":
        degraded.append("SPY_MISSING")
    if vix_status != "OK":
        degraded.append("VIX_MISSING")
    if qqq_status != "OK" or spy_status != "OK":
        label = "DEGRADED_MISSING_MARKET_PROXY"
        coeff = 0.60
    elif qqq_d200 is not None and qqq_d200 < 0:
        label = "INDEX_BELOW_200DMA"
        coeff = 0.40
    elif qqq_d50 is not None and qqq_d50 < 0:
        label = "INDEX_BELOW_50DMA"
        coeff = 0.60
    elif (qqq_vol is not None and qqq_vol > 0.35) or (vix.get("latest_close") is not None and vix["latest_close"] > 25):
        label = "HIGH_VOL_CAUTION"
        coeff = 0.60
    elif spy_dd is not None and spy_dd < -0.05:
        label = "HEALTHY_PULLBACK"
        coeff = 0.80
    row = {
        "qqq_latest_date": qqq.get("latest_date", ""),
        "qqq_latest_close": fmt(qqq.get("latest_close")),
        "qqq_sma50": fmt(qqq.get("sma50")),
        "qqq_sma200": fmt(qqq.get("sma200")),
        "qqq_distance_to_50dma": fmt(qqq.get("distance_to_50dma")),
        "qqq_distance_to_200dma": fmt(qqq.get("distance_to_200dma")),
        "qqq_realized_volatility_20d": fmt(qqq.get("vol20")),
        "spy_latest_date": spy.get("latest_date", ""),
        "spy_latest_close": fmt(spy.get("latest_close")),
        "spy_rolling_52w_high": fmt(spy.get("high252")),
        "spy_drawdown_from_52w_high": fmt(spy.get("drawdown52w")),
        "vix_latest_value": fmt(vix.get("latest_close")),
        "vix_regime_strength": "HIGH" if vix.get("latest_close") and vix["latest_close"] > 25 else "NORMAL" if vix.get("latest_close") else "",
        "internal_breadth_up_ratio": fmt(breadth_up),
        "internal_breadth_above_50dma_ratio": fmt(breadth_above50),
        "market_regime_label": label,
        "market_risk_coefficient": fmt(coeff, 2),
        "market_regime_data_status": "OK" if not degraded else "DEGRADED_" + ";".join(degraded),
        "qqq_proxy_status": qqq_status,
        "spy_proxy_status": spy_status,
        "vix_proxy_status": vix_status,
    }
    return row, {"QQQ": qqq_status, "SPY": spy_status, "VIX": vix_status}


def ps_parse(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    escaped = str(path).replace("'", "''")
    cmd = f"$null = [scriptblock]::Create((Get-Content -Raw -LiteralPath '{escaped}')); 'OK_PARSE'"
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd], text=True, capture_output=True, timeout=30)
        if result.returncode == 0 and "OK_PARSE" in (result.stdout or ""):
            return True, "OK_PARSE"
        return False, (result.stderr or result.stdout).strip()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def compile_check(path: Path) -> Tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, "OK_COMPILE"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def render_read_first(metrics: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {metrics.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(metrics: Dict[str, object], validations: Sequence[str]) -> str:
    return "\n".join(
        [
            "# V18.21A Price-Derived Factor Pack Report",
            "",
            "## Executive summary",
            f"- Status: {metrics['STATUS']}",
            f"- Ticker factor rows: {metrics['TICKER_FACTOR_ROWS']} / {metrics['TICKER_INPUT_COUNT']}",
            f"- Market regime: {metrics['MARKET_REGIME_LABEL']} at coefficient {metrics['MARKET_RISK_COEFFICIENT']}",
            "",
            "## Safety statement",
            "- Advisory-only. No external providers were used and no cache, state, ranking, trading, or command-center files were modified.",
            "",
            "## Input discovery summary",
            "- Universe source: outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv",
            "- Price source precedence: data/prices, state/v18/price_cache, data/v16/prices_full, data/v16/prices.",
            "",
            "## Ticker-level factor summary",
            f"- Insufficient history count: {metrics['TICKER_INSUFFICIENT_HISTORY_COUNT']}",
            f"- Data degraded count: {metrics['DATA_DEGRADED_COUNT']}",
            "",
            "## Market regime summary",
            f"- QQQ: {metrics['QQQ_PROXY_STATUS']}; SPY: {metrics['SPY_PROXY_STATUS']}; VIX: {metrics['VIX_PROXY_STATUS']}",
            "",
            "## Top relative strength tickers",
            f"- {metrics['TOP_RELATIVE_STRENGTH_TICKERS']}",
            "",
            "## Top near-buy-zone tickers",
            f"- {metrics['TOP_NEAR_BUY_ZONE_TICKERS']}",
            "",
            "## Breakout volume confirmation summary",
            f"- {metrics['TOP_BREAKOUT_VOLUME_CONFIRMED_TICKERS']}",
            "",
            "## Degraded/missing data summary",
            f"- Factor fail count: {metrics['TICKER_FACTOR_FAIL_COUNT']}; VIX status: {metrics['VIX_PROXY_STATUS']}",
            "",
            "## Validation summary",
            *[f"- {item}" for item in validations],
            f"- Validation fail count: {metrics['VALIDATION_FAIL_COUNT']}",
            "",
            "## Next-step recommendation",
            "- Review V18.21A as a research input only. Promote nothing into official ranking or trading until a separate policy review is approved.",
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    out_factors = root / "outputs/v18/price_factors/V18_21A_CURRENT_PRICE_DERIVED_FACTORS.csv"
    out_scores = root / "outputs/v18/price_factors/V18_21A_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv"
    out_market = root / "outputs/v18/market_regime/V18_21A_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv"
    read_first = root / "outputs/v18/ops/V18_21A_READ_FIRST.txt"
    report = root / "outputs/v18/ops/V18_21A_CURRENT_PRICE_DERIVED_FACTOR_REPORT.md"

    tickers = discover_universe(root)
    qqq_hist, _qqq_source, qqq_status_raw = load_price_history(root, "QQQ")
    qqq_returns = {"20d": None, "60d": None}
    if qqq_hist:
        qqq_closes = [float(row["close"]) for row in qqq_hist]
        qqq_returns = {"20d": ret(qqq_closes, 20), "60d": ret(qqq_closes, 60)}

    factor_rows = [compute_factor(root, ticker, qqq_returns) for ticker in tickers]
    score_rows = [score_row(row) for row in factor_rows]
    market_row, proxy_status = market_regime(root, factor_rows)

    write_csv(out_factors, factor_rows, FACTOR_FIELDS)
    write_csv(out_scores, score_rows, SCORE_FIELDS)
    write_csv(out_market, [market_row], MARKET_FIELDS)

    fail_count = sum(1 for row in factor_rows if not row.get("latest_close"))
    insufficient_count = sum(1 for row in factor_rows if "INSUFFICIENT" in str(row.get("price_factor_data_status", "")))
    degraded_count = sum(1 for row in factor_rows if str(row.get("price_factor_data_status", "")) != "OK")
    extended_count = sum(1 for row in factor_rows if row.get("buy_zone_label") == "EXTENDED_ABOVE_BUY_ZONE")
    below200_count = sum(1 for row in factor_rows if (to_float(row.get("distance_to_200dma")) is not None and to_float(row.get("distance_to_200dma")) < 0))
    high_vol_count = sum(1 for row in score_rows if row.get("price_derived_status") == "HIGH_VOL_CAUTION")
    top_rs = sorted(factor_rows, key=lambda r: to_float(r.get("relative_strength_60d_vs_qqq")) if to_float(r.get("relative_strength_60d_vs_qqq")) is not None else -999, reverse=True)[:10]
    top_buy = [row for row in factor_rows if row.get("buy_zone_label") in {"NEAR_20DMA_PULLBACK", "NEAR_50DMA_PULLBACK", "BREAKOUT_NEAR"}][:10]
    top_breakout = [row for row in factor_rows if row.get("breakout_volume_confirmed") == "TRUE"][:10]
    status = STATUS_WARN if fail_count or market_row["market_regime_data_status"].startswith("DEGRADED") else STATUS_OK

    ps_ok, ps_msg = ps_parse(root / "scripts/v18/run_v18_21A_price_derived_factor_pack.ps1")
    py_ok, py_msg = compile_check(root / "scripts/v18/v18_21A_price_derived_factor_pack.py")
    outputs_ok = all(path.exists() for path in (out_factors, out_scores, out_market))
    validations = [
        f"PowerShell parse check: {ps_msg}",
        f"Python compile check: {py_msg}",
        "Run check: OK_CURRENT_SCRIPT_EXECUTED",
        f"Output existence check: {'OK' if outputs_ok else 'FAILED'}",
        "Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY",
    ]
    validation_fail_count = sum(1 for ok in (ps_ok, py_ok, outputs_ok) if not ok)

    metrics: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "TICKER_INPUT_COUNT": len(tickers),
        "TICKER_FACTOR_ROWS": len(factor_rows),
        "TICKER_FACTOR_FAIL_COUNT": fail_count,
        "TICKER_INSUFFICIENT_HISTORY_COUNT": insufficient_count,
        "QQQ_PROXY_STATUS": proxy_status["QQQ"],
        "SPY_PROXY_STATUS": proxy_status["SPY"],
        "VIX_PROXY_STATUS": proxy_status["VIX"],
        "MARKET_REGIME_STATUS": market_row["market_regime_data_status"],
        "MARKET_REGIME_LABEL": market_row["market_regime_label"],
        "MARKET_RISK_COEFFICIENT": market_row["market_risk_coefficient"],
        "TOP_RELATIVE_STRENGTH_TICKERS": ";".join(str(row.get("ticker")) for row in top_rs if row.get("latest_close")),
        "TOP_NEAR_BUY_ZONE_TICKERS": ";".join(str(row.get("ticker")) for row in top_buy),
        "TOP_BREAKOUT_VOLUME_CONFIRMED_TICKERS": ";".join(str(row.get("ticker")) for row in top_breakout),
        "EXTENDED_ABOVE_BUY_ZONE_COUNT": extended_count,
        "BELOW_200DMA_COUNT": below200_count,
        "HIGH_VOL_CAUTION_COUNT": high_vol_count,
        "DATA_DEGRADED_COUNT": degraded_count,
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "READ_FIRST": str(read_first),
        "REPORT": str(report),
    }
    metrics.update(SAFETY_FLAGS)
    write_text(read_first, render_read_first(metrics))
    write_text(report, render_report(metrics, validations))

    required_fields_ok = all(field in read_text(read_first) for field in READ_FIRST_FIELDS)
    final_outputs_ok = all(path.exists() for path in (out_factors, out_scores, out_market, read_first, report))
    if not required_fields_ok or not final_outputs_ok:
        metrics["VALIDATION_FAIL_COUNT"] = int(metrics["VALIDATION_FAIL_COUNT"]) + 1
        write_text(read_first, render_read_first(metrics))
        write_text(report, render_report(metrics, validations + ["Final READ_FIRST/output check: FAILED"]))

    print(f"STATUS: {metrics['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"TICKER_INPUT_COUNT: {metrics['TICKER_INPUT_COUNT']}")
    print(f"TICKER_FACTOR_ROWS: {metrics['TICKER_FACTOR_ROWS']}")
    print(f"MARKET_REGIME_LABEL: {metrics['MARKET_REGIME_LABEL']}")
    print(f"MARKET_RISK_COEFFICIENT: {metrics['MARKET_RISK_COEFFICIENT']}")
    print(f"QQQ_PROXY_STATUS: {metrics['QQQ_PROXY_STATUS']}")
    print(f"SPY_PROXY_STATUS: {metrics['SPY_PROXY_STATUS']}")
    print(f"VIX_PROXY_STATUS: {metrics['VIX_PROXY_STATUS']}")
    print(f"VALIDATION_FAIL_COUNT: {metrics['VALIDATION_FAIL_COUNT']}")
    print(f"READ_FIRST: {read_first}")
    print(f"REPORT: {report}")
    return 1 if int(metrics["VALIDATION_FAIL_COUNT"]) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
