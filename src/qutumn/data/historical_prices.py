from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv
import json
from typing import Iterable

import pandas as pd

from qutumn.common.paths import ROOT, CONFIGS_V16, OUTPUTS_V16, ensure_dir
from qutumn.common.config_io import load_yaml_like


@dataclass
class PriceLoadRecord:
    ticker: str
    status: str
    rows: int
    first_date: str
    last_date: str
    source: str
    reason: str = ""


@dataclass
class PriceMatrixResult:
    prices: pd.DataFrame
    records: list[PriceLoadRecord]


def _safe_int(value: object, default: int) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return default


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    cfg = load_yaml_like(path)
    return cfg if isinstance(cfg, dict) else {}


def load_backtest_config() -> dict:
    return _load_yaml(CONFIGS_V16 / "backtest" / "backtest_config.yaml")


def load_price_refresh_config() -> dict:
    return _load_yaml(CONFIGS_V16 / "data" / "price_refresh.yaml")


def _candidate_price_paths(ticker: str) -> list[Path]:
    t = ticker.upper()
    return [
        ROOT / "data" / "v16" / "prices" / f"{t}.csv",
        ROOT / "data" / "prices" / f"{t}.csv",
    ]


def _standardize_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["close"])

    df = df.copy()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [str(col[0]) for col in df.columns]

    lower_map = {str(c).strip().lower(): c for c in df.columns}

    date_col = None
    for c in ["date", "datetime", "time"]:
        if c in lower_map:
            date_col = lower_map[c]
            break

    if date_col is None:
        first_col = df.columns[0]
        if "unnamed" in str(first_col).lower() or str(first_col).lower() in {"index", ""}:
            date_col = first_col

    if date_col is not None:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])
        df = df.set_index(date_col)
    else:
        df.index = pd.to_datetime(df.index, errors="coerce")
        df = df[~df.index.isna()]

    close_col = None
    for c in ["close", "adj close", "adj_close", "Close", "Adj Close"]:
        key = str(c).strip().lower()
        if key in lower_map:
            close_col = lower_map[key]
            break

    if close_col is None:
        for col in df.columns:
            if str(col).strip().lower() == "close":
                close_col = col
                break

    if close_col is None:
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not numeric_cols:
            return pd.DataFrame(columns=["close"])
        close_col = numeric_cols[0]

    out = pd.DataFrame(index=df.index)
    out["close"] = pd.to_numeric(df[close_col], errors="coerce")

    for src, dst in [
        ("open", "open"),
        ("high", "high"),
        ("low", "low"),
        ("volume", "volume"),
        ("adj close", "adj_close"),
        ("adj_close", "adj_close"),
    ]:
        for col in df.columns:
            if str(col).strip().lower() == src:
                out[dst] = pd.to_numeric(df[col], errors="coerce")

    out = out.dropna(subset=["close"])
    out = out[~out.index.duplicated(keep="last")]
    out = out.sort_index()

    return out


def _read_local_price_file(path: Path) -> pd.DataFrame:
    try:
        raw = pd.read_csv(path)
        return _standardize_price_frame(raw)
    except Exception:
        return pd.DataFrame(columns=["close"])


def _record_from_frame(ticker: str, df: pd.DataFrame, source: str, status: str = "OK", reason: str = "") -> PriceLoadRecord:
    if df.empty:
        return PriceLoadRecord(
            ticker=ticker.upper(),
            status=status if status != "OK" else "NO_DATA",
            rows=0,
            first_date="",
            last_date="",
            source=source,
            reason=reason,
        )

    return PriceLoadRecord(
        ticker=ticker.upper(),
        status=status,
        rows=int(len(df)),
        first_date=str(df.index.min().date()),
        last_date=str(df.index.max().date()),
        source=source,
        reason=reason,
    )


def _choose_best_local(ticker: str) -> tuple[pd.DataFrame, PriceLoadRecord]:
    best_df = pd.DataFrame(columns=["close"])
    best_record = PriceLoadRecord(ticker=ticker.upper(), status="NO_DATA", rows=0, first_date="", last_date="", source="", reason="No local file found.")

    for path in _candidate_price_paths(ticker):
        if not path.exists():
            continue

        df = _read_local_price_file(path)
        record = _record_from_frame(ticker, df, str(path.relative_to(ROOT)))

        if df.empty:
            continue

        if best_df.empty or df.index.max() > best_df.index.max():
            best_df = df
            best_record = record

    return best_df, best_record


def _download_yfinance(ticker: str, period: str, interval: str, auto_adjust: bool) -> tuple[pd.DataFrame, str]:
    try:
        import yfinance as yf
    except Exception as exc:
        return pd.DataFrame(columns=["close"]), f"yfinance import failed: {exc}"

    try:
        raw = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            progress=False,
            threads=False,
        )
    except Exception as exc:
        return pd.DataFrame(columns=["close"]), f"yfinance download failed: {exc}"

    if raw is None or raw.empty:
        return pd.DataFrame(columns=["close"]), "yfinance returned empty data."

    df = _standardize_price_frame(raw.reset_index())
    return df, ""


def refresh_prices(tickers: Iterable[str] | None = None) -> tuple[list[PriceLoadRecord], dict]:
    cfg = load_price_refresh_config()

    cfg_tickers = cfg.get("tickers", [])
    if tickers is None:
        tickers = cfg_tickers

    tickers = [str(t).upper().strip() for t in tickers if str(t).strip()]
    tickers = list(dict.fromkeys(tickers))

    download_cfg = cfg.get("download", {})
    if not isinstance(download_cfg, dict):
        download_cfg = {}

    period = str(download_cfg.get("period", "7y"))
    interval = str(download_cfg.get("interval", "1d"))
    auto_adjust = _safe_bool(download_cfg.get("auto_adjust"), False)
    force_refresh = _safe_bool(download_cfg.get("force_refresh"), True)

    cache_dir_raw = str(cfg.get("cache_dir", "data/v16/prices"))
    cache_dir = ensure_dir(ROOT / cache_dir_raw)

    records: list[PriceLoadRecord] = []

    for ticker in tickers:
        if not force_refresh:
            local_df, local_record = _choose_best_local(ticker)
            if not local_df.empty:
                records.append(local_record)
                continue

        downloaded, reason = _download_yfinance(ticker, period=period, interval=interval, auto_adjust=auto_adjust)

        if downloaded.empty:
            local_df, local_record = _choose_best_local(ticker)
            if local_df.empty:
                records.append(
                    PriceLoadRecord(
                        ticker=ticker,
                        status="DOWNLOAD_FAILED",
                        rows=0,
                        first_date="",
                        last_date="",
                        source="",
                        reason=reason,
                    )
                )
            else:
                local_record.status = "LOCAL_FALLBACK"
                local_record.reason = reason
                records.append(local_record)
            continue

        out_path = cache_dir / f"{ticker}.csv"
        to_save = downloaded.copy()
        to_save.index.name = "date"
        to_save.reset_index().to_csv(out_path, index=False, encoding="utf-8-sig")

        records.append(_record_from_frame(ticker, downloaded, str(out_path.relative_to(ROOT)), status="REFRESHED", reason="Downloaded by yfinance."))

    freshness_cfg = cfg.get("freshness", {})
    if not isinstance(freshness_cfg, dict):
        freshness_cfg = {}

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker_count": len(tickers),
        "refreshed_count": sum(1 for r in records if r.status == "REFRESHED"),
        "fallback_count": sum(1 for r in records if r.status == "LOCAL_FALLBACK"),
        "failed_count": sum(1 for r in records if r.status == "DOWNLOAD_FAILED"),
        "fresh_max_age_days": _safe_int(freshness_cfg.get("fresh_max_age_days"), 2),
        "stale_review_max_age_days": _safe_int(freshness_cfg.get("stale_review_max_age_days"), 5),
    }

    write_price_refresh_audit(records, summary)
    return records, summary


def load_price_matrix(
    tickers: Iterable[str],
    lookback_days: int = 756,
    allow_yfinance_download: bool = True,
) -> PriceMatrixResult:
    prices: dict[str, pd.Series] = {}
    records: list[PriceLoadRecord] = []

    for raw_ticker in tickers:
        ticker = str(raw_ticker).upper().strip()
        if not ticker:
            continue

        df, record = _choose_best_local(ticker)

        if df.empty and allow_yfinance_download:
            downloaded, reason = _download_yfinance(ticker, period="7y", interval="1d", auto_adjust=False)
            if not downloaded.empty:
                cache_dir = ensure_dir(ROOT / "data" / "v16" / "prices")
                out_path = cache_dir / f"{ticker}.csv"
                tmp = downloaded.copy()
                tmp.index.name = "date"
                tmp.reset_index().to_csv(out_path, index=False, encoding="utf-8-sig")
                df = downloaded
                record = _record_from_frame(ticker, df, str(out_path.relative_to(ROOT)), status="DOWNLOADED_ON_DEMAND", reason="Downloaded on demand.")
            else:
                record = PriceLoadRecord(ticker=ticker, status="NO_DATA", rows=0, first_date="", last_date="", source="", reason=reason)

        if not df.empty:
            if lookback_days and lookback_days > 0:
                df = df.tail(lookback_days)
            prices[ticker] = df["close"].copy()
            records.append(_record_from_frame(ticker, df, record.source, status=record.status, reason=record.reason))
        else:
            records.append(record)

    if prices:
        matrix = pd.DataFrame(prices).sort_index()
        matrix = matrix.ffill()
    else:
        matrix = pd.DataFrame()

    return PriceMatrixResult(prices=matrix, records=records)


def write_price_audit(records: list[PriceLoadRecord]) -> tuple[Path, Path]:
    out_dir = ensure_dir(OUTPUTS_V16 / "backtest")
    md_path = out_dir / "V16_PRICE_LOAD_AUDIT.md"
    csv_path = out_dir / "V16_PRICE_LOAD_AUDIT.csv"

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        fieldnames = list(PriceLoadRecord.__dataclass_fields__.keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r.__dict__)

    lines: list[str] = []
    lines.append("# V16 Price Load Audit")
    lines.append("")
    lines.append("## 价格读取结果")
    lines.append("")
    lines.append("| ticker | status | rows | first_date | last_date | source | reason |")
    lines.append("|---|---|---:|---|---|---|---|")
    for r in records:
        lines.append(f"| `{r.ticker}` | `{r.status}` | `{r.rows}` | `{r.first_date}` | `{r.last_date}` | `{r.source}` | {r.reason} |")
    lines.append("")
    lines.append("## 说明")
    lines.append("")
    lines.append("V16.9 会优先选择 data/v16/prices 和 data/prices 中 last_date 最新的本地数据。")
    lines.append("如果本地没有数据且允许下载，则使用 yfinance on-demand 下载。")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path, csv_path


def _freshness_label(last_date: str, fresh_max_age: int, stale_review_max_age: int) -> str:
    if not last_date:
        return "NO_PRICE"
    try:
        d = pd.to_datetime(last_date).date()
        age = (datetime.now().date() - d).days
        if age <= fresh_max_age:
            return "FRESH"
        if age <= stale_review_max_age:
            return "STALE_REVIEW"
        return "STALE_BLOCK"
    except Exception:
        return "UNKNOWN"


def write_price_refresh_audit(records: list[PriceLoadRecord], summary: dict) -> tuple[Path, Path, Path]:
    out_dir = ensure_dir(OUTPUTS_V16 / "data")
    md_path = out_dir / "V16_PRICE_REFRESH_AUDIT.md"
    csv_path = out_dir / "V16_PRICE_REFRESH_AUDIT.csv"
    json_path = out_dir / "V16_PRICE_REFRESH_AUDIT.json"

    fresh_max_age = int(summary.get("fresh_max_age_days", 2))
    stale_review_max_age = int(summary.get("stale_review_max_age_days", 5))

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        fieldnames = list(PriceLoadRecord.__dataclass_fields__.keys()) + ["freshness"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            row = r.__dict__.copy()
            row["freshness"] = _freshness_label(r.last_date, fresh_max_age, stale_review_max_age)
            writer.writerow(row)

    freshness_counts: dict[str, int] = {}
    for r in records:
        label = _freshness_label(r.last_date, fresh_max_age, stale_review_max_age)
        freshness_counts[label] = freshness_counts.get(label, 0) + 1

    lines: list[str] = []
    lines.append("# V16 Price Refresh Audit")
    lines.append("")
    lines.append(f"生成时间：`{summary.get('generated_at')}`")
    lines.append("")
    lines.append("## 1. 当前结论")
    lines.append("")
    if summary.get("refreshed_count", 0) > 0:
        lines.append("V16.9 已尝试刷新价格数据，并写入 data/v16/prices。")
    else:
        lines.append("V16.9 未成功刷新价格数据，当前仍依赖本地 fallback。")
    lines.append("")
    lines.append("## 2. Summary")
    lines.append("")
    lines.append("| item | value |")
    lines.append("|---|---:|")
    for key in ["ticker_count", "refreshed_count", "fallback_count", "failed_count"]:
        lines.append(f"| {key} | `{summary.get(key, 0)}` |")

    lines.append("")
    lines.append("## 3. Freshness Summary")
    lines.append("")
    lines.append("| freshness | count |")
    lines.append("|---|---:|")
    for key in sorted(freshness_counts):
        lines.append(f"| `{key}` | `{freshness_counts[key]}` |")

    lines.append("")
    lines.append("## 4. Ticker Details")
    lines.append("")
    lines.append("| ticker | status | freshness | rows | first_date | last_date | source | reason |")
    lines.append("|---|---|---|---:|---|---|---|---|")
    for r in records:
        label = _freshness_label(r.last_date, fresh_max_age, stale_review_max_age)
        lines.append(f"| `{r.ticker}` | `{r.status}` | `{label}` | `{r.rows}` | `{r.first_date}` | `{r.last_date}` | `{r.source}` | {r.reason} |")

    lines.append("")
    lines.append("## 5. 下一步")
    lines.append("")
    lines.append("刷新后重新运行 Execution Plan / Position Review / Event Gate / Behavior Guard。")
    lines.append("如果全部仍为 STALE_REVIEW，说明 yfinance 没有拿到新数据或当前不是可用交易日。")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "summary": summary,
        "freshness_counts": freshness_counts,
        "records": [r.__dict__ for r in records],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return md_path, csv_path, json_path
