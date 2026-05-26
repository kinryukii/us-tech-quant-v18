
# -*- coding: utf-8 -*-
"""
V18.3D RAW105 factor pack shadow extension.

Purpose:
- Add price/volume reversal, volume anomaly, cross-sectional rank, and time-series momentum/pullback factors.
- Run as shadow evidence only.
- Do NOT modify V17 official BUY/NO_BUY decision files.
"""

from __future__ import annotations

import math
import os
import re
import sys
import glob
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(os.environ.get("US_TECH_QUANT_ROOT", r"D:\us-tech-quant"))
OUT_DIR = ROOT / "outputs" / "v18" / "factor_pack"
OUT_DIR.mkdir(parents=True, exist_ok=True)

READ_FIRST = OUT_DIR / "V18_3D_READ_FIRST.txt"
VALUES_CSV = OUT_DIR / "V18_3D_RAW105_FACTOR_PACK_VALUES.csv"
RANKING_CSV = OUT_DIR / "V18_3D_RAW105_FACTOR_PACK_RANKING.csv"
TOP30_MD = OUT_DIR / "V18_3D_FACTOR_PACK_TOP30.md"
OVERLAP_MD = OUT_DIR / "V18_3D_FACTOR_PACK_OFFICIAL_OVERLAP.md"

TICKER_RE = re.compile(r"^[A-Z][A-Z0-9]{0,4}(?:[.-][A-Z])?$")
BAD_TOKENS = {
    "OK", "NO", "YES", "BUY", "SELL", "HOLD", "NONE", "NULL", "TRUE", "FALSE",
    "CSV", "TXT", "MD", "READ", "FIRST", "RAW", "RAW105", "DAILY", "V17", "V18",
    "COUNT", "DATE", "PATH", "STATUS", "ACTION", "FINAL", "TOP", "LOCKED",
    "EVENT", "RISK", "PRICE", "FRESH", "STALE", "SOURCE", "OUTPUT",
}


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def safe_read_csv(path: Path) -> pd.DataFrame | None:
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return None


def normalize_ticker(x: object) -> str | None:
    if pd.isna(x):
        return None
    s = str(x).strip().upper()
    s = s.replace("$", "")
    if not s or len(s) > 8:
        return None
    if s in BAD_TOKENS or re.match(r"^F\d+$", s):
        return None
    if TICKER_RE.match(s):
        return s
    return None


def extract_tickers_from_df(df: pd.DataFrame) -> list[str]:
    preferred = []
    for col in df.columns:
        c = str(col).strip().lower()
        if c in {"ticker", "symbol", "name", "code"} or "ticker" in c or "symbol" in c:
            preferred.append(col)

    found: list[str] = []
    cols = preferred or list(df.columns[:4])
    for col in cols:
        for v in df[col].dropna().tolist():
            t = normalize_ticker(v)
            if t:
                found.append(t)

    # Deduplicate preserving order.
    out = []
    seen = set()
    for t in found:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def discover_universe() -> tuple[list[str], str]:
    candidates: list[tuple[int, int, Path, list[str]]] = []

    exact_paths = [
        ROOT / "outputs" / "v17" / "raw105_decision" / "v17_8A_raw105_full_decision_daily.csv",
        ROOT / "outputs" / "v18" / "factor_shadow" / "V18_1B_RAW105_FACTOR_VALUES.csv",
        ROOT / "outputs" / "v18" / "factor_shadow" / "v18_1B_raw105_factor_values.csv",
    ]

    glob_patterns = [
        ROOT / "outputs" / "v17" / "raw105_decision" / "*.csv",
        ROOT / "outputs" / "v18" / "factor_shadow" / "*.csv",
        ROOT / "outputs" / "v18" / "**" / "*raw105*.csv",
        ROOT / "state" / "**" / "*raw105*.csv",
        ROOT / "data" / "**" / "*raw105*.csv",
    ]

    paths: list[Path] = []
    for p in exact_paths:
        if p.exists():
            paths.append(p)
    for pat in glob_patterns:
        paths.extend(Path(x) for x in glob.glob(str(pat), recursive=True))

    # Unique paths preserving order.
    seen_paths = set()
    unique_paths: list[Path] = []
    for p in paths:
        try:
            rp = p.resolve()
        except Exception:
            rp = p
        if rp not in seen_paths and p.exists() and p.is_file():
            seen_paths.add(rp)
            unique_paths.append(p)

    for p in unique_paths:
        df = safe_read_csv(p)
        if df is None or df.empty:
            continue
        tickers = extract_tickers_from_df(df)
        n = len(tickers)
        if n < 50:
            continue

        pl = str(p).lower()
        score = 0
        if "raw105" in pl:
            score += 100
        if "full_decision" in pl or "decision" in pl:
            score += 60
        if "factor_values" in pl or "factor" in pl:
            score += 35
        if 95 <= n <= 115:
            score += 50
        elif 70 <= n <= 150:
            score += 20
        try:
            mtime = int(p.stat().st_mtime)
        except Exception:
            mtime = 0
        candidates.append((score, mtime, p, tickers))

    if not candidates:
        raise RuntimeError(
            "找不到 RAW105 universe。请先运行 V17.8D，确认 raw105_decision CSV 或 V18.1B factor values CSV 已生成。"
        )

    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    score, _mtime, source, tickers = candidates[0]
    return tickers, str(source)


def download_price_volume(tickers: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    try:
        import yfinance as yf
    except Exception as e:
        raise RuntimeError(
            "当前 Python 环境缺少 yfinance。请先在 .venv 中安装：python -m pip install yfinance"
        ) from e

    data = yf.download(
        tickers=tickers,
        period="260d",
        interval="1d",
        auto_adjust=True,
        group_by="column",
        threads=True,
        progress=False,
    )

    if data is None or len(data) == 0:
        raise RuntimeError("yfinance 未返回价格数据。")

    def field_df(field: str) -> pd.DataFrame:
        if isinstance(data.columns, pd.MultiIndex):
            level0 = list(data.columns.get_level_values(0))
            level1 = list(data.columns.get_level_values(1))
            if field in level0:
                out = data[field].copy()
            elif field in level1:
                out = data.xs(field, axis=1, level=1).copy()
            else:
                raise RuntimeError(f"yfinance 数据缺少字段：{field}")
        else:
            if field not in data.columns:
                raise RuntimeError(f"yfinance 数据缺少字段：{field}")
            out = data[[field]].copy()
            if len(tickers) == 1:
                out.columns = tickers
        out.columns = [str(c).upper() for c in out.columns]
        return out

    close = field_df("Close")
    volume = field_df("Volume")
    return close, volume


def pct_rank_high_good(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    if s.notna().sum() == 0:
        return pd.Series(np.nan, index=s.index)
    return s.rank(method="average", pct=True)


def compute_metrics(tickers: list[str], close: pd.DataFrame, volume: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    failed = []

    for t in tickers:
        if t not in close.columns:
            failed.append(t)
            continue
        c = pd.to_numeric(close[t], errors="coerce").dropna()
        if len(c) < 130:
            failed.append(t)
            continue

        v = None
        if t in volume.columns:
            v = pd.to_numeric(volume[t], errors="coerce").reindex(c.index)
        else:
            v = pd.Series(index=c.index, dtype=float)

        ret = c.pct_change()
        last = c.iloc[-1]

        def pct_change(n: int) -> float:
            if len(c) <= n or c.iloc[-n - 1] == 0:
                return np.nan
            return float(c.iloc[-1] / c.iloc[-n - 1] - 1)

        ret_1d = pct_change(1)
        ret_5d = pct_change(5)
        ret_20d = pct_change(20)
        ret_60d = pct_change(60)
        ret_120d = pct_change(120)

        ma20 = float(c.rolling(20).mean().iloc[-1])
        ma60 = float(c.rolling(60).mean().iloc[-1])
        high20 = float(c.rolling(20).max().iloc[-1])
        high60 = float(c.rolling(60).max().iloc[-1])
        dd20 = float(last / high20 - 1) if high20 else np.nan
        dd60 = float(last / high60 - 1) if high60 else np.nan

        vol5 = float(v.rolling(5).mean().iloc[-1]) if v.notna().sum() >= 5 else np.nan
        vol20 = float(v.rolling(20).mean().iloc[-1]) if v.notna().sum() >= 20 else np.nan
        vol_ratio = float(vol5 / vol20) if vol20 and not math.isnan(vol20) and vol20 > 0 else np.nan

        ann_vol20 = float(ret.tail(20).std() * math.sqrt(252)) if ret.tail(20).notna().sum() >= 10 else np.nan

        rows.append({
            "ticker": t,
            "latest_price_date": str(pd.Timestamp(c.index[-1]).date()),
            "latest_close": float(last),
            "ret_1d": ret_1d,
            "ret_5d": ret_5d,
            "ret_20d": ret_20d,
            "ret_60d": ret_60d,
            "ret_120d": ret_120d,
            "ma20": ma20,
            "ma60": ma60,
            "drawdown_20d_high": dd20,
            "drawdown_60d_high": dd60,
            "volume_avg_5d": vol5,
            "volume_avg_20d": vol20,
            "volume_ratio_5_20": vol_ratio,
            "ann_volatility_20d": ann_vol20,
            "trend_ok_60_120": bool(ret_60d > 0 and ret_120d > 0 and last >= ma60),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("没有足够价格历史可计算 V18.3D 因子。")

    # Raw components.
    df["short_rev_raw"] = -df["ret_5d"]
    df["ts_momentum_raw"] = 0.50 * df["ret_60d"] + 0.50 * df["ret_120d"]
    df["volume_price_confirm_raw"] = df["volume_ratio_5_20"] * df["ret_5d"]

    # Pullback inside uptrend: higher when long trend is positive and short-term drawdown exists.
    trend_mask = (
        (df["ret_60d"] > 0)
        & (df["ret_120d"] > 0)
        & (df["latest_close"] >= df["ma60"])
    )
    pullback_depth = (-df["ret_5d"]).clip(lower=0, upper=0.20) + (-df["drawdown_20d_high"]).clip(lower=0, upper=0.20)
    df["pullback_uptrend_raw"] = np.where(trend_mask, pullback_depth, np.nan)

    # Time-series pullback/reversal: trend is alive, near-term weakness exists, but 20d damage is not too severe.
    ts_reversal_raw = (
        (0.50 * df["ret_60d"].clip(lower=0) + 0.50 * df["ret_120d"].clip(lower=0))
        * (-df["ret_5d"]).clip(lower=0, upper=0.20)
    )
    ts_reversal_raw = np.where(df["ret_20d"] > -0.25, ts_reversal_raw, np.nan)
    df["ts_pullback_reversal_raw"] = ts_reversal_raw

    df["F006_SHORT_REV_5D"] = pct_rank_high_good(df["short_rev_raw"]) * 100
    df["F007_PULLBACK_IN_UPTREND"] = pct_rank_high_good(df["pullback_uptrend_raw"]) * 100
    df["F008_VOLUME_ABNORMAL_5_20"] = pct_rank_high_good(df["volume_ratio_5_20"]) * 100
    df["F009_VOLUME_PRICE_CONFIRM"] = pct_rank_high_good(df["volume_price_confirm_raw"]) * 100
    df["F011_TS_MOMENTUM_60_120"] = pct_rank_high_good(df["ts_momentum_raw"]) * 100
    df["F012_TS_PULLBACK_REVERSAL"] = pct_rank_high_good(df["ts_pullback_reversal_raw"]) * 100

    df["volatility_penalty"] = pct_rank_high_good(df["ann_volatility_20d"]) * 100
    overheat_raw = np.maximum(df["ret_20d"].fillna(-9), 0.5 * df["ret_60d"].fillna(-9))
    df["overheat_penalty"] = pct_rank_high_good(overheat_raw) * 100

    factor_cols = [
        "F006_SHORT_REV_5D",
        "F007_PULLBACK_IN_UPTREND",
        "F008_VOLUME_ABNORMAL_5_20",
        "F009_VOLUME_PRICE_CONFIRM",
        "F011_TS_MOMENTUM_60_120",
        "F012_TS_PULLBACK_REVERSAL",
    ]

    # Fill missing factor scores at neutral 50 for composite only.
    f = df[factor_cols].fillna(50.0)
    comp_raw = (
        0.16 * f["F006_SHORT_REV_5D"]
        + 0.22 * f["F007_PULLBACK_IN_UPTREND"]
        + 0.12 * f["F008_VOLUME_ABNORMAL_5_20"]
        + 0.14 * f["F009_VOLUME_PRICE_CONFIRM"]
        + 0.22 * f["F011_TS_MOMENTUM_60_120"]
        + 0.14 * f["F012_TS_PULLBACK_REVERSAL"]
        - 0.08 * df["volatility_penalty"].fillna(50.0)
        - 0.12 * df["overheat_penalty"].fillna(50.0)
    )
    df["F010_XSEC_COMPOSITE_RANK_RAW"] = comp_raw
    df["F010_XSEC_COMPOSITE_RANK"] = pct_rank_high_good(comp_raw) * 100
    df["factor_pack_score"] = df["F010_XSEC_COMPOSITE_RANK"].round(2)
    df = df.sort_values(["factor_pack_score", "ticker"], ascending=[False, True]).reset_index(drop=True)
    df["factor_pack_rank"] = np.arange(1, len(df) + 1)

    def side_hint(row: pd.Series) -> str:
        if row.get("F007_PULLBACK_IN_UPTREND", 0) >= 75 and row.get("F012_TS_PULLBACK_REVERSAL", 0) >= 75:
            return "PULLBACK_IN_UPTREND"
        if row.get("volume_ratio_5_20", 0) >= 1.8 and row.get("ret_5d", 0) < -0.03:
            return "VOLUME_DOWN_RISK"
        if row.get("F009_VOLUME_PRICE_CONFIRM", 0) >= 75:
            return "VOLUME_UP_CONFIRM"
        if row.get("F011_TS_MOMENTUM_60_120", 0) >= 75 and row.get("F006_SHORT_REV_5D", 50) < 35:
            return "MOMENTUM_STRONG_NOT_PULLBACK"
        return "NEUTRAL_SHADOW"

    df["shadow_side_hint"] = df.apply(side_hint, axis=1)

    numeric_cols = [c for c in df.columns if c not in {"ticker", "latest_price_date", "trend_ok_60_120", "shadow_side_hint"}]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").round(6)

    return df, failed


def discover_official_review(universe: Iterable[str]) -> tuple[list[str], str]:
    universe_set = set(universe)
    decision_dir = ROOT / "outputs" / "v17" / "raw105_decision"
    if not decision_dir.exists():
        return [], "NOT_FOUND"

    text_paths = []
    for pat in [
        "V17_8D_CURRENT_RAW105_DECISION_PANEL*",
        "V17_8C_CURRENT_RAW105_DECISION_PANEL*",
        "V17_8B_RAW105_FULL_DECISION_READABLE_PANEL*",
        "V17_8D_READ_FIRST.txt",
        "V17_8C_READ_FIRST.txt",
        "*.md",
        "*.txt",
    ]:
        text_paths.extend(decision_dir.glob(pat))

    text_paths = sorted(set(text_paths), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)

    keys = [
        "WORTH_REVIEW_BUT_LOCKED",
        "WORTH-REVIEW-BUT-LOCKED",
        "OFFICIAL_REVIEW",
        "SECOND_STAGE",
        "第二阶段候选",
    ]

    for p in text_paths:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        found = []
        for line in text.splitlines():
            u = line.upper()
            if not any(k in u for k in keys):
                continue
            for token in re.findall(r"\b[A-Z][A-Z0-9]{1,4}(?:[.-][A-Z])?\b", line.upper()):
                t = normalize_ticker(token)
                if t and t in universe_set and t not in found:
                    found.append(t)
        if found:
            return found, str(p)

    csv_paths = sorted(decision_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in csv_paths:
        df = safe_read_csv(p)
        if df is None or df.empty:
            continue
        tick_col = None
        for col in df.columns:
            if str(col).lower() in {"ticker", "symbol", "name"} or "ticker" in str(col).lower():
                tick_col = col
                break
        if tick_col is None:
            continue

        text_cols = [c for c in df.columns if df[c].dtype == object]
        if not text_cols:
            continue
        mask = pd.Series(False, index=df.index)
        for col in text_cols:
            s = df[col].astype(str).str.upper()
            mask = mask | s.str.contains("WORTH_REVIEW|LOCKED|SECOND_STAGE|REVIEW", regex=True, na=False)
        found = []
        for v in df.loc[mask, tick_col].tolist():
            t = normalize_ticker(v)
            if t and t in universe_set and t not in found:
                found.append(t)
        if found:
            return found, str(p)

    return [], "NOT_FOUND"


def fmt_pct(x: object) -> str:
    try:
        if pd.isna(x):
            return ""
        return f"{float(x) * 100:.2f}%"
    except Exception:
        return ""


def fmt_num(x: object, nd: int = 2) -> str:
    try:
        if pd.isna(x):
            return ""
        return f"{float(x):.{nd}f}"
    except Exception:
        return ""


def markdown_table(rows: list[dict], cols: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(title for _key, title in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = []
    for row in rows:
        vals = []
        for key, _title in cols:
            vals.append(str(row.get(key, "")).replace("|", "/"))
        body.append("| " + " | ".join(vals) + " |")
    return "\n".join([header, sep] + body)


def write_outputs(df: pd.DataFrame, failed: list[str], universe_source: str) -> None:
    official_review, official_source = discover_official_review(df["ticker"].tolist())
    top30 = df.head(30).copy()
    top10_names = ",".join(df.head(10)["ticker"].tolist())
    top30_names = set(top30["ticker"].tolist())
    official_set = set(official_review)
    overlap = sorted(top30_names & official_set)
    official_not_top30 = sorted(official_set - top30_names)
    top30_only = sorted(top30_names - official_set)

    # CSV outputs.
    df.to_csv(VALUES_CSV, index=False, encoding="utf-8-sig")
    ranking_cols = [
        "factor_pack_rank", "ticker", "factor_pack_score", "latest_price_date", "latest_close",
        "ret_5d", "ret_20d", "ret_60d", "ret_120d", "volume_ratio_5_20",
        "F006_SHORT_REV_5D", "F007_PULLBACK_IN_UPTREND", "F008_VOLUME_ABNORMAL_5_20",
        "F009_VOLUME_PRICE_CONFIRM", "F010_XSEC_COMPOSITE_RANK",
        "F011_TS_MOMENTUM_60_120", "F012_TS_PULLBACK_REVERSAL",
        "volatility_penalty", "overheat_penalty", "shadow_side_hint",
    ]
    df[ranking_cols].to_csv(RANKING_CSV, index=False, encoding="utf-8-sig")

    top_rows = []
    for _, r in top30.iterrows():
        top_rows.append({
            "rank": int(r["factor_pack_rank"]),
            "ticker": r["ticker"],
            "score": fmt_num(r["factor_pack_score"], 2),
            "close": fmt_num(r["latest_close"], 2),
            "5d": fmt_pct(r["ret_5d"]),
            "20d": fmt_pct(r["ret_20d"]),
            "60d": fmt_pct(r["ret_60d"]),
            "vol5_20": fmt_num(r["volume_ratio_5_20"], 2),
            "hint": r["shadow_side_hint"],
        })

    top_md = f"""# V18.3D RAW105 Factor Pack Top30

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. 结论

- V18_3D_STATUS: `OK_FACTOR_PACK_SHADOW_READY`
- OFFICIAL_DECISION_IMPACT: `NONE`
- PROMOTION_ACTION: `NONE`
- RAW105_COUNT: `{len(df) + len(failed)}`
- PRICE_OK_COUNT: `{len(df)}`
- PRICE_FAIL_COUNT: `{len(failed)}`
- FACTOR_COUNT: `7`
- TOP30_COUNT: `{len(top30)}`

## 2. Top30

{markdown_table(top_rows, [
    ("rank", "rank"),
    ("ticker", "ticker"),
    ("score", "score"),
    ("close", "close"),
    ("5d", "5d"),
    ("20d", "20d"),
    ("60d", "60d"),
    ("vol5_20", "vol5/20"),
    ("hint", "shadow_hint"),
])}

## 3. 解释

- `F006_SHORT_REV_5D`：短期 5 日反转/回撤分数，越高代表越偏短期回落。
- `F007_PULLBACK_IN_UPTREND`：中期趋势仍在时的回撤窗口分数，越高越接近你的左侧+右侧混合逻辑。
- `F008_VOLUME_ABNORMAL_5_20`：5 日均量相对 20 日均量的异动分数。
- `F009_VOLUME_PRICE_CONFIRM`：成交量异动是否被价格方向确认。
- `F010_XSEC_COMPOSITE_RANK`：RAW105 内部横截面综合排名。
- `F011_TS_MOMENTUM_60_120`：60/120 日时间序列动量。
- `F012_TS_PULLBACK_REVERSAL`：中期趋势中短期回撤/反转窗口。

注意：本文件只提供 shadow evidence，不改变官方交易结论。
"""
    write_text(TOP30_MD, top_md)

    overlap_rows = [{"ticker": t, "in_top30": "YES"} for t in overlap]
    official_rows = [{"ticker": t, "in_top30": "NO"} for t in official_not_top30]
    overlap_md = f"""# V18.3D Factor Pack vs Official Review Overlap

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. 状态

- V18_3D_STATUS: `OK_FACTOR_PACK_SHADOW_READY`
- OFFICIAL_DECISION_IMPACT: `NONE`
- PROMOTION_ACTION: `NONE`
- OFFICIAL_REVIEW_SOURCE: `{official_source}`
- OFFICIAL_REVIEW_COUNT: `{len(official_review)}`
- SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: `{len(overlap)}`
- SHADOW_TOP30_ONLY_COUNT: `{len(top30_only)}`
- OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: `{len(official_not_top30)}`

## 2. Shadow Top30 且 Official Review

{markdown_table(overlap_rows, [("ticker", "ticker"), ("in_top30", "in_top30")]) if overlap_rows else "无"}

## 3. Official Review 但不在 Shadow Top30

{markdown_table(official_rows, [("ticker", "ticker"), ("in_top30", "in_top30")]) if official_rows else "无"}

## 4. 说明

V18.3D 是新增因子包的影子跟踪层。它只记录价量、成交量、横截面 rank、时间序列动量/反转证据，不直接改变 V17.8D 官方 BUY/NO_BUY。
"""
    write_text(OVERLAP_MD, overlap_md)

    read_first = f"""=== V18.3D RAW105 FACTOR PACK SHADOW EXTENSION ===

V18_3D_STATUS: OK_FACTOR_PACK_SHADOW_READY
RUN_TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

UNIVERSE_SOURCE: {universe_source}
RAW105_COUNT: {len(df) + len(failed)}
PRICE_OK_COUNT: {len(df)}
PRICE_FAIL_COUNT: {len(failed)}
PRICE_FAIL_NAMES: {",".join(failed) if failed else "NONE"}

FACTOR_COUNT: 7
FACTOR_NAMES: F006_SHORT_REV_5D,F007_PULLBACK_IN_UPTREND,F008_VOLUME_ABNORMAL_5_20,F009_VOLUME_PRICE_CONFIRM,F010_XSEC_COMPOSITE_RANK,F011_TS_MOMENTUM_60_120,F012_TS_PULLBACK_REVERSAL

TOP10_NAMES: {top10_names}
TOP30_COUNT: {len(top30)}

OFFICIAL_REVIEW_SOURCE: {official_source}
OFFICIAL_REVIEW_COUNT: {len(official_review)}
SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: {len(overlap)}
SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: {",".join(overlap) if overlap else "NONE"}
SHADOW_TOP30_ONLY_COUNT: {len(top30_only)}
OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: {len(official_not_top30)}

OFFICIAL_DECISION_IMPACT: NONE
PROMOTION_ACTION: NONE

START_HERE:
{TOP30_MD}

COMPARE_REPORT:
{OVERLAP_MD}

VALUES_CSV:
{VALUES_CSV}

RANKING_CSV:
{RANKING_CSV}
"""
    write_text(READ_FIRST, read_first)


def main() -> int:
    try:
        tickers, source = discover_universe()
        close, volume = download_price_volume(tickers)
        df, failed = compute_metrics(tickers, close, volume)
        write_outputs(df, failed, source)
        print(READ_FIRST.read_text(encoding="utf-8"))
        return 0
    except Exception as e:
        msg = f"""=== V18.3D RAW105 FACTOR PACK SHADOW EXTENSION ===

V18_3D_STATUS: FAIL
RUN_TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
ERROR: {type(e).__name__}: {e}

OFFICIAL_DECISION_IMPACT: NONE
PROMOTION_ACTION: NONE
"""
        write_text(READ_FIRST, msg)
        print(msg)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
