from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

HORIZONS = [5, 10, 20, 60]

TRACKING_COLUMNS = [
    "snapshot_date",
    "generated_at",
    "ticker",

    "candidate_rank",
    "system_tier",
    "manual_decision",
    "event_confirmation_status",
    "restriction",

    "trend_score",
    "momentum_score",
    "relative_strength_score",
    "pullback_score",
    "pullback_status",
    "overheat_penalty",
    "overheat_status",
    "volatility_penalty",

    "event_risk_score",
    "event_risk_band",
    "event_risk_status",

    "official_action",
    "budget_action",
    "buy_permission",
    "global_mode",

    "price_anchor_date",
    "price_anchor_close",
    "price_anchor_source",
]

for h in HORIZONS:
    TRACKING_COLUMNS += [
        f"close_t_plus_{h}d",
        f"ret_{h}d",
        f"qqq_ret_{h}d",
        f"rel_qqq_ret_{h}d",
        f"return_fill_status_{h}d",
    ]

TRACKING_COLUMNS += [
    "source_files",
    "notes",
]

ALIASES = {
    "candidate_rank": [
        "rank", "candidate_rank", "review_rank", "score_rank"
    ],
    "system_tier": [
        "system_tier", "candidate_tier", "tier", "bucket", "candidate_bucket",
        "candidate_level", "final_bucket", "stage_bucket"
    ],
    "manual_decision": [
        "manual_decision", "user_review_decision", "candidate_review_decision",
        "review_decision", "manual_review_decision"
    ],
    "event_confirmation_status": [
        "event_confirmation_status", "confirmation_status", "event_status"
    ],
    "restriction": [
        "restriction", "trade_restriction", "buy_restriction", "action_restriction"
    ],

    "trend_score": [
        "trend_score", "trend", "trend_factor", "ma_trend_score"
    ],
    "momentum_score": [
        "momentum_score", "momentum", "momentum_factor"
    ],
    "relative_strength_score": [
        "relative_strength_score", "relative_strength", "rs_score", "rs_factor"
    ],
    "pullback_score": [
        "pullback_score", "pullback_factor"
    ],
    "pullback_status": [
        "pullback_status", "pullback", "trigger_status", "pullback_trigger_status"
    ],
    "overheat_penalty": [
        "overheat_penalty", "overheat_score", "overheat"
    ],
    "overheat_status": [
        "overheat_status", "momentum_extension_status", "extension_status"
    ],
    "volatility_penalty": [
        "volatility_penalty", "vol_penalty", "beta_penalty", "high_beta_penalty"
    ],

    "event_risk_score": [
        "event_risk_score", "max_event_risk_score", "risk_score", "macro_risk_score"
    ],
    "event_risk_band": [
        "event_risk_band", "max_event_risk_band", "risk_band", "band", "macro_risk_band"
    ],
    "event_risk_status": [
        "event_risk_status", "risk_status", "macro_risk_status"
    ],

    "price_anchor_close": [
        "close", "latest_close", "last_close", "price", "latest_price", "current_price"
    ],
    "price_anchor_date": [
        "price_date", "latest_price_date", "max_price_date", "date", "snapshot_price_date"
    ],
}

STATUS_LABELS = {
    "official_action": [
        "OFFICIAL ACTION", "OFFICIAL_ACTION", "FINAL ACTION", "FINAL_DAILY_ACTION_WITH_EVENTS"
    ],
    "budget_action": [
        "BUDGET ACTION", "FINAL_BUDGET_ACTION"
    ],
    "buy_permission": [
        "BUY PERMISSION", "BUY_PERMISSION"
    ],
    "global_mode": [
        "GLOBAL MODE", "GLOBAL_MODE"
    ],
}


def norm_col(x: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(x).strip().lower()).strip("_")


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def read_text_safe(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ["utf-8-sig", "utf-8", "cp932", "gbk", "latin-1"]:
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return ""


def read_csv_safe(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []

    raw = None
    for enc in ["utf-8-sig", "utf-8", "cp932", "gbk", "latin-1"]:
        try:
            raw = path.read_text(encoding=enc)
            break
        except Exception:
            continue

    if raw is None:
        return [], []

    lines = raw.splitlines()
    if not lines:
        return [], []

    try:
        reader = csv.DictReader(lines)
        rows = []
        for row in reader:
            clean = {}
            for k, v in row.items():
                if k is None:
                    continue
                clean[str(k).strip()] = "" if v is None else str(v).strip()
            rows.append(clean)
        return rows, list(reader.fieldnames or [])
    except Exception:
        return [], []


def write_csv_safe(path: Path, rows: List[Dict[str, Any]], columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})


def get_by_alias(row: Dict[str, str], aliases: List[str]) -> str:
    if not row:
        return ""
    norm_map = {norm_col(k): v for k, v in row.items()}
    for a in aliases:
        v = norm_map.get(norm_col(a), "")
        if str(v).strip() != "":
            return str(v).strip()
    return ""


def find_ticker_col(columns: List[str]) -> Optional[str]:
    candidates = ["ticker", "symbol", "asset", "code"]
    norm_to_orig = {norm_col(c): c for c in columns}
    for c in candidates:
        if c in norm_to_orig:
            return norm_to_orig[c]
    return None


def clean_ticker(x: str) -> str:
    x = str(x or "").strip().upper()
    x = x.replace("$", "")
    x = x.split()[0] if x else ""
    x = re.sub(r"[^A-Z0-9\.\-]", "", x)
    return x


def safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if s == "" or s.upper() in {"NA", "N/A", "NONE", "NULL", "UNKNOWN"}:
        return None
    if s.endswith("%"):
        try:
            return float(s[:-1]) / 100.0
        except Exception:
            return None
    try:
        return float(s)
    except Exception:
        return None


def fmt_float(x: Optional[float], digits: int = 6) -> str:
    if x is None:
        return ""
    try:
        return f"{float(x):.{digits}f}"
    except Exception:
        return ""


def init_info(ticker: str) -> Dict[str, Any]:
    info = {c: "" for c in TRACKING_COLUMNS}
    info["ticker"] = ticker
    info["_source_files_set"] = set()
    return info


def merge_row_into_info(root: Path, path: Path, row: Dict[str, str], info: Dict[str, Any]) -> None:
    info["_source_files_set"].add(relpath(root, path))

    for out_col, aliases in ALIASES.items():
        v = get_by_alias(row, aliases)
        if v and not str(info.get(out_col, "")).strip():
            info[out_col] = v

    if not str(info.get("manual_decision", "")).strip():
        possible = get_by_alias(row, ["decision", "conclusion"])
        if possible and possible.upper() in {"WATCH", "BLOCK", "PENDING", "PENDING_MANUAL_CHECK"}:
            info["manual_decision"] = possible


def discover_candidate_info(root: Path) -> Dict[str, Dict[str, Any]]:
    info_by_ticker: Dict[str, Dict[str, Any]] = {}

    preferred_files = [
        root / "state" / "v16_manual_review_decisions.csv",
        root / "outputs" / "v16" / "events" / "v16_17_candidate_event_risk_scores.csv",
        root / "outputs" / "v16" / "manual_review" / "v16_20_3_manual_review_helper.csv",
        root / "outputs" / "v16" / "manual_review" / "v16_21_manual_review_decision_updater_report.csv",
    ]

    search_roots = [
        root / "outputs" / "v16",
        root / "state",
    ]

    discovered = []
    for sr in search_roots:
        if sr.exists():
            discovered.extend(list(sr.rglob("*.csv")))

    def is_relevant(path: Path) -> bool:
        s = str(path).lower()
        keys = [
            "candidate", "manual_review", "event_risk", "full_universe",
            "review", "tier", "score", "pullback", "decision"
        ]
        return any(k in s for k in keys)

    all_files = []
    seen = set()
    for p in preferred_files + sorted([p for p in discovered if is_relevant(p)], key=lambda x: str(x).lower()):
        if p.exists():
            key = str(p.resolve()).lower()
            if key not in seen:
                all_files.append(p)
                seen.add(key)

    for path in all_files:
        rows, cols = read_csv_safe(path)
        if not rows or not cols:
            continue
        tcol = find_ticker_col(cols)
        if not tcol:
            continue

        for row in rows:
            ticker = clean_ticker(row.get(tcol, ""))
            if not ticker:
                continue
            if ticker not in info_by_ticker:
                info_by_ticker[ticker] = init_info(ticker)
            merge_row_into_info(root, path, row, info_by_ticker[ticker])

    for ticker, info in info_by_ticker.items():
        src = sorted(list(info.get("_source_files_set", set())))
        info["source_files"] = " | ".join(src)
        info.pop("_source_files_set", None)

    return info_by_ticker


def parse_status_files(root: Path) -> Dict[str, str]:
    status = {
        "official_action": "UNKNOWN",
        "budget_action": "UNKNOWN",
        "buy_permission": "UNKNOWN",
        "global_mode": "UNKNOWN",
    }

    files = [
        root / "outputs" / "v16" / "read_center" / "V16_24_2B_CLASSIC_DAILY_BRIEF.md",
        root / "outputs" / "v16" / "V16_19_UNIFIED_DAILY_EXECUTION_BUDGET_SUMMARY.md",
        root / "outputs" / "v16" / "V16_18_READ_FIRST.txt",
        root / "outputs" / "v16" / "V16_17_0_DAILY_MASTER_WITH_RISK.md",
    ]

    text = "\n".join(read_text_safe(p) for p in files if p.exists())

    for out_col, labels in STATUS_LABELS.items():
        found = ""
        for label in labels:
            patterns = [
                rf"{re.escape(label)}\s*[:：]\s*`?([A-Z0-9_\-]+)`?",
                rf"\*\*{re.escape(label)}\*\*\s*[:：]?\s*`?([A-Z0-9_\-]+)`?",
                rf"{re.escape(label)}\s*\n\s*`?([A-Z0-9_\-]+)`?",
            ]
            for pat in patterns:
                m = re.search(pat, text, flags=re.IGNORECASE)
                if m:
                    found = m.group(1).strip().strip("`")
                    break
            if found:
                break
        if found:
            status[out_col] = found

    return status


def fetch_latest_prices(tickers: List[str]) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    result: Dict[str, Dict[str, str]] = {}
    errors: List[str] = []

    try:
        import yfinance as yf
    except Exception as e:
        return result, [f"yfinance_import_failed: {e}"]

    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period="10d", auto_adjust=False)
            if hist is None or hist.empty or "Close" not in hist.columns:
                errors.append(f"{ticker}: no_history")
                continue
            hist = hist.dropna(subset=["Close"])
            if hist.empty:
                errors.append(f"{ticker}: no_close")
                continue
            last = hist.iloc[-1]
            dt = hist.index[-1]
            try:
                dstr = dt.date().isoformat()
            except Exception:
                dstr = str(dt)[:10]
            close = float(last["Close"])
            result[ticker] = {
                "price_anchor_date": dstr,
                "price_anchor_close": fmt_float(close, 6),
                "price_anchor_source": "yfinance_latest_close",
            }
        except Exception as e:
            errors.append(f"{ticker}: {type(e).__name__}: {e}")

    return result, errors


def fetch_history(tickers: List[str], start_date: str, end_date: str) -> Dict[str, List[Tuple[str, float]]]:
    histories: Dict[str, List[Tuple[str, float]]] = {}
    try:
        import yfinance as yf
    except Exception:
        return histories

    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(start=start_date, end=end_date, auto_adjust=False)
            if hist is None or hist.empty or "Close" not in hist.columns:
                continue
            hist = hist.dropna(subset=["Close"])
            series = []
            for idx, row in hist.iterrows():
                try:
                    d = idx.date().isoformat()
                except Exception:
                    d = str(idx)[:10]
                series.append((d, float(row["Close"])))
            if series:
                histories[ticker] = series
        except Exception:
            continue

    return histories


def find_index_on_or_before(series: List[Tuple[str, float]], anchor_date: str) -> Optional[int]:
    if not series:
        return None
    idx = None
    for i, (d, _) in enumerate(series):
        if d <= anchor_date:
            idx = i
        elif d > anchor_date and idx is None:
            return i
    return idx


def update_forward_returns(rows: List[Dict[str, Any]]) -> List[str]:
    messages = []
    needed_rows = []
    tickers = set()

    for row in rows:
        ticker = clean_ticker(row.get("ticker", ""))
        anchor_date = str(row.get("price_anchor_date", "") or row.get("snapshot_date", "")).strip()
        anchor_close = safe_float(row.get("price_anchor_close", ""))
        if not ticker or not anchor_date or anchor_close is None:
            continue

        need = False
        for h in HORIZONS:
            if not str(row.get(f"ret_{h}d", "")).strip():
                need = True
                break
        if need:
            needed_rows.append(row)
            tickers.add(ticker)

    if not needed_rows:
        return ["no_forward_return_rows_due_or_missing"]

    tickers.add("QQQ")

    min_date = min(str(r.get("price_anchor_date", "") or r.get("snapshot_date", "")) for r in needed_rows)
    try:
        start = (datetime.strptime(min_date[:10], "%Y-%m-%d") - timedelta(days=5)).date().isoformat()
    except Exception:
        start = (datetime.now() - timedelta(days=90)).date().isoformat()

    end = (datetime.now() + timedelta(days=3)).date().isoformat()
    histories = fetch_history(sorted(tickers), start, end)

    if not histories:
        return ["history_fetch_unavailable"]

    qqq_series = histories.get("QQQ", [])

    fill_count = 0

    for row in needed_rows:
        ticker = clean_ticker(row.get("ticker", ""))
        series = histories.get(ticker, [])
        if not series:
            continue

        anchor_date = str(row.get("price_anchor_date", "") or row.get("snapshot_date", "")).strip()[:10]
        anchor_close = safe_float(row.get("price_anchor_close", ""))
        if anchor_close is None:
            continue

        anchor_idx = find_index_on_or_before(series, anchor_date)
        qqq_anchor_idx = find_index_on_or_before(qqq_series, anchor_date) if qqq_series else None
        if anchor_idx is None:
            continue

        for h in HORIZONS:
            ret_col = f"ret_{h}d"
            if str(row.get(ret_col, "")).strip():
                continue

            target_idx = anchor_idx + h
            if target_idx >= len(series):
                row[f"return_fill_status_{h}d"] = "WAIT_NOT_ENOUGH_TRADING_DAYS"
                continue

            target_close = series[target_idx][1]
            ticker_ret = target_close / anchor_close - 1.0
            row[f"close_t_plus_{h}d"] = fmt_float(target_close, 6)
            row[f"ret_{h}d"] = fmt_float(ticker_ret, 6)

            if qqq_series and qqq_anchor_idx is not None and qqq_anchor_idx + h < len(qqq_series):
                qqq_anchor_close = qqq_series[qqq_anchor_idx][1]
                qqq_target_close = qqq_series[qqq_anchor_idx + h][1]
                qqq_ret = qqq_target_close / qqq_anchor_close - 1.0
                row[f"qqq_ret_{h}d"] = fmt_float(qqq_ret, 6)
                row[f"rel_qqq_ret_{h}d"] = fmt_float(ticker_ret - qqq_ret, 6)
                row[f"return_fill_status_{h}d"] = "FILLED"
            else:
                row[f"return_fill_status_{h}d"] = "FILLED_NO_QQQ"

            fill_count += 1

    messages.append(f"forward_return_fill_count={fill_count}")
    return messages


def load_existing_tracking(path: Path) -> List[Dict[str, Any]]:
    rows, _ = read_csv_safe(path)
    clean_rows = []
    for r in rows:
        row = {c: r.get(c, "") for c in TRACKING_COLUMNS}
        clean_rows.append(row)
    return clean_rows


def build_today_rows(root: Path, info_by_ticker: Dict[str, Dict[str, Any]], status: Dict[str, str]) -> Tuple[List[Dict[str, Any]], List[str]]:
    tickers = sorted(info_by_ticker.keys())
    price_map, price_errors = fetch_latest_prices(tickers)

    rows = []
    snap_date = today_iso()
    gen_at = now_iso()

    for ticker in tickers:
        info = {c: info_by_ticker[ticker].get(c, "") for c in TRACKING_COLUMNS}
        info["snapshot_date"] = snap_date
        info["generated_at"] = gen_at
        info["ticker"] = ticker

        for k, v in status.items():
            info[k] = v

        if ticker in price_map:
            for k, v in price_map[ticker].items():
                info[k] = v
        else:
            if not str(info.get("price_anchor_source", "")).strip():
                if str(info.get("price_anchor_close", "")).strip():
                    info["price_anchor_source"] = "candidate_file_price"
                else:
                    info["price_anchor_source"] = "MISSING_PRICE"

        if not str(info.get("manual_decision", "")).strip():
            info["manual_decision"] = "UNKNOWN"

        if not str(info.get("system_tier", "")).strip():
            info["system_tier"] = "UNKNOWN"

        rows.append(info)

    return rows, price_errors


def upsert_today(existing_rows: List[Dict[str, Any]], today_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}
    order = []

    for r in existing_rows:
        key = (str(r.get("snapshot_date", "")), clean_ticker(r.get("ticker", "")))
        if not key[0] or not key[1]:
            continue
        if key not in by_key:
            order.append(key)
        by_key[key] = {c: r.get(c, "") for c in TRACKING_COLUMNS}

    for r in today_rows:
        key = (str(r.get("snapshot_date", "")), clean_ticker(r.get("ticker", "")))
        if not key[0] or not key[1]:
            continue
        if key not in by_key:
            order.append(key)

        old = by_key.get(key, {c: "" for c in TRACKING_COLUMNS})
        new = {c: old.get(c, "") for c in TRACKING_COLUMNS}

        for c in TRACKING_COLUMNS:
            incoming = r.get(c, "")
            if str(incoming).strip() != "":
                new[c] = incoming

        by_key[key] = new

    rows = [by_key[k] for k in order]
    rows.sort(key=lambda x: (str(x.get("snapshot_date", "")), str(x.get("ticker", ""))))
    return rows


def validate(rows: List[Dict[str, Any]], today_rows: List[Dict[str, Any]], price_errors: List[str]) -> Tuple[str, List[Dict[str, str]]]:
    checks = []

    def add(level: str, check: str, detail: str) -> None:
        checks.append({"level": level, "check": check, "detail": detail})

    if rows:
        add("OK", "tracking_rows_present", f"rows={len(rows)}")
    else:
        add("FAIL", "tracking_rows_present", "rows=0")

    if today_rows:
        add("OK", "today_rows_present", f"today_rows={len(today_rows)}")
    else:
        add("FAIL", "today_rows_present", "today_rows=0")

    keys = [(r.get("snapshot_date", ""), clean_ticker(r.get("ticker", ""))) for r in rows]
    dup_count = len(keys) - len(set(keys))
    if dup_count == 0:
        add("OK", "no_duplicate_snapshot_ticker", "duplicate_count=0")
    else:
        add("FAIL", "no_duplicate_snapshot_ticker", f"duplicate_count={dup_count}")

    missing_price_today = [
        clean_ticker(r.get("ticker", ""))
        for r in today_rows
        if not str(r.get("price_anchor_close", "")).strip()
    ]
    if not missing_price_today:
        add("OK", "today_anchor_prices_present", "missing_price_count=0")
    else:
        add("WARN", "today_anchor_prices_present", "missing_price_count=" + str(len(missing_price_today)) + " tickers=" + ",".join(missing_price_today[:20]))

    if price_errors:
        add("WARN", "price_fetch_messages", " | ".join(price_errors[:20]))
    else:
        add("OK", "price_fetch_messages", "no_price_fetch_errors")

    today_manual = Counter(str(r.get("manual_decision", "") or "UNKNOWN").upper() for r in today_rows)
    add("OK", "today_manual_decision_counts", dict(today_manual).__repr__())

    fail_count = sum(1 for c in checks if c["level"] == "FAIL")
    warn_count = sum(1 for c in checks if c["level"] == "WARN")

    if fail_count > 0:
        status = "FAIL"
    elif warn_count > 0:
        status = "WARN"
    else:
        status = "OK"

    return status, checks


def write_summary(
    root: Path,
    out_dir: Path,
    tracking_path: Path,
    today_rows: List[Dict[str, Any]],
    all_rows: List[Dict[str, Any]],
    validation_status: str,
    validation_checks: List[Dict[str, str]],
    forward_messages: List[str],
) -> None:
    manual_counts = Counter(str(r.get("manual_decision", "") or "UNKNOWN").upper() for r in today_rows)
    tier_counts = Counter(str(r.get("system_tier", "") or "UNKNOWN").upper() for r in today_rows)
    price_ok = sum(1 for r in today_rows if str(r.get("price_anchor_close", "")).strip())

    summary_path = out_dir / "V17_1_FACTOR_EFFECTIVENESS_TRACKER_SUMMARY.md"
    read_first_path = out_dir / "V17_1_READ_FIRST.txt"
    validation_path = out_dir / "V17_1_FACTOR_EFFECTIVENESS_VALIDATION.md"

    lines = []
    lines.append("# V17.1 Factor Effectiveness Tracker Summary")
    lines.append("")
    lines.append(f"生成时间：{now_iso()}")
    lines.append("")
    lines.append("## 1. 今日结论")
    lines.append("")
    lines.append(f"- TRACKER_STATUS: `{validation_status}`")
    lines.append(f"- TODAY_ROWS: `{len(today_rows)}`")
    lines.append(f"- TOTAL_TRACKING_ROWS: `{len(all_rows)}`")
    lines.append(f"- TODAY_ROWS_WITH_ANCHOR_PRICE: `{price_ok}`")
    lines.append("")
    lines.append("## 2. 今日人工复核状态")
    lines.append("")
    for k, v in sorted(manual_counts.items()):
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## 3. 今日系统分层状态")
    lines.append("")
    for k, v in sorted(tier_counts.items()):
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## 4. 本表追踪的核心字段")
    lines.append("")
    lines.append("- 趋势：trend_score")
    lines.append("- 动量：momentum_score")
    lines.append("- 相对强度：relative_strength_score")
    lines.append("- 回撤：pullback_score / pullback_status")
    lines.append("- 过热：overheat_penalty / overheat_status")
    lines.append("- 波动：volatility_penalty")
    lines.append("- 事件风险：event_risk_score / event_risk_band / event_risk_status")
    lines.append("- 执行状态：official_action / budget_action / buy_permission / global_mode")
    lines.append("- 人工决策：manual_decision")
    lines.append("- 价格锚点：price_anchor_date / price_anchor_close")
    lines.append("- 后验表现：5 / 10 / 20 / 60 个交易日收益与相对 QQQ 收益")
    lines.append("")
    lines.append("## 5. 后续如何使用")
    lines.append("")
    lines.append("每天跑一次本脚本。它会：")
    lines.append("")
    lines.append("1. 记录当天候选池和因子状态；")
    lines.append("2. 不重复写入同一天同一 ticker；")
    lines.append("3. 当未来交易日足够时，自动回填 5 / 10 / 20 / 60 日收益；")
    lines.append("4. 让我们回答：WATCH / BLOCK / WAIT / 候选分层到底有没有预测力。")
    lines.append("")
    lines.append("## 6. 文件位置")
    lines.append("")
    lines.append(f"- TRACKING CSV: `{tracking_path}`")
    lines.append(f"- SUMMARY: `{summary_path}`")
    lines.append(f"- VALIDATION: `{validation_path}`")
    lines.append(f"- READ FIRST: `{read_first_path}`")
    lines.append("")
    lines.append("## 7. Forward Return Fill Messages")
    lines.append("")
    for msg in forward_messages:
        lines.append(f"- {msg}")
    lines.append("")

    summary_path.write_text("\n".join(lines), encoding="utf-8-sig")

    vlines = []
    vlines.append("# V17.1 Factor Effectiveness Validation")
    vlines.append("")
    vlines.append(f"生成时间：{now_iso()}")
    vlines.append("")
    vlines.append(f"VALIDATION_STATUS: `{validation_status}`")
    vlines.append("")
    vlines.append("| level | check | detail |")
    vlines.append("|---|---|---|")
    for c in validation_checks:
        detail = str(c["detail"]).replace("|", "/")
        vlines.append(f"| {c['level']} | {c['check']} | {detail} |")
    vlines.append("")
    validation_path.write_text("\n".join(vlines), encoding="utf-8-sig")

    read_lines = []
    read_lines.append("=== V17.1 FACTOR EFFECTIVENESS TRACKER READ FIRST ===")
    read_lines.append("")
    read_lines.append("START HERE:")
    read_lines.append(str(summary_path))
    read_lines.append("")
    read_lines.append("TRACKING CSV:")
    read_lines.append(str(tracking_path))
    read_lines.append("")
    read_lines.append("VALIDATION:")
    read_lines.append(str(validation_path))
    read_lines.append("")
    read_lines.append("NORMAL COMMAND:")
    read_lines.append('powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\run_v17_1_factor_effectiveness_tracker.ps1"')
    read_lines.append("")
    read_first_path.write_text("\n".join(read_lines), encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="project root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = root / "outputs" / "v17" / "factor_effectiveness"
    out_dir.mkdir(parents=True, exist_ok=True)

    tracking_path = root / "state" / "v17_factor_effectiveness_tracking.csv"
    validation_csv_path = out_dir / "v17_1_factor_effectiveness_validation.csv"

    info_by_ticker = discover_candidate_info(root)
    status = parse_status_files(root)

    today_rows, price_errors = build_today_rows(root, info_by_ticker, status)

    existing_rows = load_existing_tracking(tracking_path)
    all_rows = upsert_today(existing_rows, today_rows)

    forward_messages = update_forward_returns(all_rows)

    write_csv_safe(tracking_path, all_rows, TRACKING_COLUMNS)

    validation_status, validation_checks = validate(all_rows, today_rows, price_errors)
    write_csv_safe(validation_csv_path, validation_checks, ["level", "check", "detail"])

    write_summary(
        root=root,
        out_dir=out_dir,
        tracking_path=tracking_path,
        today_rows=today_rows,
        all_rows=all_rows,
        validation_status=validation_status,
        validation_checks=validation_checks,
        forward_messages=forward_messages,
    )

    print("=== V17.1 FACTOR EFFECTIVENESS TRACKER READY ===")
    print(f"TRACKER_STATUS: {validation_status}")
    print(f"TODAY_ROWS: {len(today_rows)}")
    print(f"TOTAL_TRACKING_ROWS: {len(all_rows)}")
    print("")
    print("START HERE:")
    print(str(out_dir / "V17_1_FACTOR_EFFECTIVENESS_TRACKER_SUMMARY.md"))
    print("")
    print("TRACKING CSV:")
    print(str(tracking_path))
    print("")
    print("VALIDATION:")
    print(str(out_dir / "V17_1_FACTOR_EFFECTIVENESS_VALIDATION.md"))
    print("")
    return 0 if validation_status in {"OK", "WARN"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
