from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

FIELD_ALIASES = {
    "candidate_rank": [
        "rank", "candidate_rank", "review_rank", "score_rank"
    ],
    "system_tier": [
        "system_tier", "candidate_tier", "tier", "bucket", "candidate_bucket",
        "candidate_level", "final_bucket", "stage_bucket", "candidate_group",
        "review_bucket", "daily_bucket"
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
        "event_risk_score", "max_event_risk_score", "risk_score", "macro_risk_score",
        "candidate_event_risk_score"
    ],
    "event_risk_band": [
        "event_risk_band", "max_event_risk_band", "risk_band", "band",
        "macro_risk_band", "candidate_event_risk_band"
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

DECISION_ALIASES = [
    "final_user_review_decision",
    "current_user_review_decision",
    "user_review_decision",
    "new_user_review_decision",
    "manual_review_decision",
    "manual_decision",
    "candidate_review_decision",
    "review_decision",
    "decision",
    "conclusion",
    "status",
]

STATUS_LABELS = {
    "official_action": [
        "OFFICIAL ACTION",
        "OFFICIAL_ACTION",
        "FINAL ACTION",
        "FINAL_DAILY_ACTION_WITH_EVENTS",
        "CURRENT OFFICIAL ACTION",
    ],
    "budget_action": [
        "BUDGET ACTION",
        "BUDGET_ACTION",
        "FINAL_BUDGET_ACTION",
    ],
    "buy_permission": [
        "BUY PERMISSION",
        "BUY_PERMISSION",
    ],
    "global_mode": [
        "GLOBAL MODE",
        "GLOBAL_MODE",
    ],
}


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def norm_col(x: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(x).strip().lower()).strip("_")


def clean_ticker(x: Any) -> str:
    s = str(x or "").strip().upper().replace("$", "")
    if not s:
        return ""
    s = s.split()[0]
    return re.sub(r"[^A-Z0-9.\-]", "", s)


def safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if not s or s.upper() in {"NA", "N/A", "NONE", "NULL", "UNKNOWN"}:
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


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def read_text_safe(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ["utf-8-sig", "utf-8", "cp932", "gbk", "latin-1"]:
        try:
            return path.read_text(encoding=enc)
        except Exception:
            pass
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
            pass

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


def write_csv_safe(path: Path, rows: List[Dict[str, Any]], cols: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in cols})


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def get_by_alias(row: Dict[str, str], aliases: List[str]) -> str:
    nmap = {norm_col(k): v for k, v in row.items()}
    for alias in aliases:
        v = nmap.get(norm_col(alias), "")
        if str(v).strip():
            return str(v).strip()
    return ""


def normalize_decision(x: Any) -> str:
    u = str(x or "").strip().upper()
    if not u:
        return ""
    if "BLOCK" in u:
        return "BLOCK"
    if "WATCH" in u:
        return "WATCH"
    if "PENDING" in u or "MISSING_CONFIRMATION" in u or "MANUAL_CHECK" in u:
        return "PENDING_REVIEW"
    return ""


def extract_manual_decision(row: Dict[str, str]) -> str:
    nmap = {norm_col(k): v for k, v in row.items()}

    for alias in DECISION_ALIASES:
        d = normalize_decision(nmap.get(norm_col(alias), ""))
        if d:
            return d

    found_pending = ""
    for v in row.values():
        d = normalize_decision(v)
        if d in {"BLOCK", "WATCH"}:
            return d
        if d == "PENDING_REVIEW":
            found_pending = d

    return found_pending


def find_ticker_col(cols: List[str]) -> Optional[str]:
    nmap = {norm_col(c): c for c in cols}
    for c in ["ticker", "symbol", "asset", "code"]:
        if c in nmap:
            return nmap[c]
    return None


def source_priority(path: Path) -> int:
    s = str(path).replace("/", "\\").lower()
    if s.endswith("\\state\\v16_manual_review_decisions.csv"):
        return 1000
    if "v16_21_manual_review_decision_updater_report" in s:
        return 950
    if "v16_21_manual_review_update_template" in s:
        return 920
    if "candidate_event_risk_scores" in s:
        return 850
    if "manual_review_helper" in s:
        return 700
    if "manual_review_tasks" in s:
        return 650
    if "candidate" in s:
        return 600
    return 400


def relevant_csv(path: Path) -> bool:
    s = str(path).lower()
    keys = [
        "candidate", "manual_review", "event_risk", "review", "tier",
        "score", "pullback", "decision", "full_universe"
    ]
    return any(k in s for k in keys)


def init_info(ticker: str) -> Dict[str, Any]:
    row = {c: "" for c in TRACKING_COLUMNS}
    row["ticker"] = ticker
    row["_priority"] = {}
    row["_sources"] = set()
    return row


def set_if_better(info: Dict[str, Any], field: str, value: Any, pr: int) -> None:
    v = str(value or "").strip()
    if not v:
        return
    current_pr = int(info.get("_priority", {}).get(field, -1))
    current = str(info.get(field, "") or "").strip()
    if not current or pr >= current_pr:
        info[field] = v
        info["_priority"][field] = pr


def merge_source_row(root: Path, path: Path, row: Dict[str, str], info: Dict[str, Any]) -> None:
    pr = source_priority(path)
    info["_sources"].add(relpath(root, path))

    for field, aliases in FIELD_ALIASES.items():
        v = get_by_alias(row, aliases)
        set_if_better(info, field, v, pr)

    d = extract_manual_decision(row)
    if d:
        old = str(info.get("manual_decision", "") or "").strip().upper()
        old_pr = int(info.get("_priority", {}).get("manual_decision", -1))

        should_set = False
        if not old:
            should_set = True
        elif pr > old_pr:
            should_set = True
        elif old == "PENDING_REVIEW" and d in {"WATCH", "BLOCK"}:
            should_set = True
        elif d == "BLOCK" and old != "BLOCK" and pr >= old_pr:
            should_set = True

        if should_set:
            info["manual_decision"] = d
            info["_priority"]["manual_decision"] = pr


def discover_candidate_info(root: Path) -> Dict[str, Dict[str, Any]]:
    info_by_ticker: Dict[str, Dict[str, Any]] = {}

    scan_roots = [
        root / "state",
        root / "outputs" / "v16",
    ]

    files: List[Path] = []

    preferred = [
        root / "state" / "v16_manual_review_decisions.csv",
        root / "outputs" / "v16" / "manual_review" / "v16_21_manual_review_decision_updater_report.csv",
        root / "state" / "v16_21_manual_review_update_template.csv",
        root / "outputs" / "v16" / "events" / "v16_17_candidate_event_risk_scores.csv",
        root / "outputs" / "v16" / "manual_review" / "v16_20_3_manual_review_helper.csv",
        root / "outputs" / "v16" / "manual_review" / "v16_20_manual_review_tasks.csv",
    ]

    for p in preferred:
        if p.exists():
            files.append(p)

    for sr in scan_roots:
        if sr.exists():
            for p in sr.rglob("*.csv"):
                if relevant_csv(p):
                    files.append(p)

    seen = set()
    ordered = []
    for p in sorted(files, key=lambda x: (-source_priority(x), str(x).lower())):
        k = str(p.resolve()).lower()
        if k not in seen:
            seen.add(k)
            ordered.append(p)

    for path in ordered:
        rows, cols = read_csv_safe(path)
        if not rows or not cols:
            continue
        tcol = find_ticker_col(cols)
        if not tcol:
            continue

        for r in rows:
            ticker = clean_ticker(r.get(tcol, ""))
            if not ticker:
                continue
            info = info_by_ticker.setdefault(ticker, init_info(ticker))
            merge_source_row(root, path, r, info)

    for ticker, info in list(info_by_ticker.items()):
        manual = str(info.get("manual_decision", "") or "").strip().upper()
        restriction = str(info.get("restriction", "") or "").strip().upper()
        risk_band = str(info.get("event_risk_band", "") or "").strip().upper()

        if not manual:
            if "FREEZE" in restriction or "BLOCK" in restriction:
                info["manual_decision"] = "BLOCK"
            else:
                info["manual_decision"] = "UNKNOWN"

        tier = str(info.get("system_tier", "") or "").strip().upper()
        if not tier or tier == "UNKNOWN":
            if info["manual_decision"] == "BLOCK" or "FREEZE" in restriction:
                info["system_tier"] = "D_BLOCKED_OR_EXCLUDED"
            elif info["manual_decision"] == "WATCH" and "EXTREME" in risk_band:
                info["system_tier"] = "C_WATCH_ONLY_EVENT_LOCKED"
            elif info["manual_decision"] == "WATCH":
                info["system_tier"] = "C_WATCH_ONLY_WAIT_PULLBACK"
            elif info["manual_decision"] == "PENDING_REVIEW":
                info["system_tier"] = "B_PENDING_MANUAL_CONFIRMATION"
            else:
                info["system_tier"] = "Z_REVIEW_REQUIRED"

        info["source_files"] = " | ".join(sorted(info.get("_sources", set())))
        info.pop("_sources", None)
        info.pop("_priority", None)

    return info_by_ticker


def parse_status_from_text(text: str, labels: List[str]) -> str:
    for label in labels:
        lab = re.escape(label)

        patterns = [
            rf"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?{lab}(?:\*\*)?\s*[:：]\s*`?([A-Z][A-Z0-9_]+)`?",
            rf"(?is){lab}\s*[:：]?\s*(?:\r?\n\s*)+`?([A-Z][A-Z0-9_]+)`?",
        ]

        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip().strip("`")
    return ""


def parse_status_from_csv(path: Path, status: Dict[str, str]) -> None:
    rows, cols = read_csv_safe(path)
    if not rows or not cols:
        return

    ncols = {norm_col(c): c for c in cols}

    for status_key, labels in STATUS_LABELS.items():
        if status.get(status_key, "UNKNOWN") != "UNKNOWN":
            continue

        for label in labels + [status_key]:
            nc = norm_col(label)
            if nc in ncols:
                for r in rows:
                    v = str(r.get(ncols[nc], "")).strip()
                    if v:
                        status[status_key] = v.strip("`")
                        break

        if status.get(status_key, "UNKNOWN") != "UNKNOWN":
            continue

        # item/value style CSV
        for r in rows:
            values = list(r.values())
            joined_left = " ".join(values[:2]).upper()
            for label in labels:
                if label.upper() in joined_left:
                    for v in values[1:]:
                        vv = str(v).strip().strip("`")
                        if re.match(r"^[A-Z][A-Z0-9_]+$", vv):
                            status[status_key] = vv
                            break
                if status.get(status_key, "UNKNOWN") != "UNKNOWN":
                    break


def parse_global_status(root: Path) -> Dict[str, str]:
    status = {
        "official_action": "UNKNOWN",
        "budget_action": "UNKNOWN",
        "buy_permission": "UNKNOWN",
        "global_mode": "UNKNOWN",
    }

    candidate_files = [
        root / "outputs" / "v16" / "read_center" / "V16_24_2B_CLASSIC_DAILY_BRIEF.md",
        root / "outputs" / "v16" / "read_center" / "V16_22_5_READABLE_DAILY_CONTROL_PANEL.md",
        root / "outputs" / "v16" / "V16_19_UNIFIED_DAILY_EXECUTION_BUDGET_SUMMARY.md",
        root / "outputs" / "v16" / "V16_18_READ_FIRST.txt",
        root / "outputs" / "v16" / "V16_17_0_DAILY_MASTER_WITH_RISK.md",
        root / "state" / "v16_24_classic_brief_status_fallback.csv",
    ]

    # Add recent active V16 text files.
    active_roots = [
        root / "outputs" / "v16",
        root / "outputs" / "v16" / "read_center",
        root / "outputs" / "v16" / "execution_budget",
        root / "outputs" / "v16" / "events",
    ]

    recent_texts: List[Path] = []
    for ar in active_roots:
        if ar.exists():
            for ext in ["*.md", "*.txt", "*.csv"]:
                recent_texts.extend(ar.glob(ext))

    recent_texts = sorted(
        recent_texts,
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True
    )[:80]

    files = []
    seen = set()
    for p in candidate_files + recent_texts:
        if p.exists():
            k = str(p.resolve()).lower()
            if k not in seen:
                seen.add(k)
                files.append(p)

    for p in files:
        if p.suffix.lower() == ".csv":
            parse_status_from_csv(p, status)

        text = read_text_safe(p)
        if not text:
            continue

        for key, labels in STATUS_LABELS.items():
            if status.get(key, "UNKNOWN") != "UNKNOWN":
                continue
            v = parse_status_from_text(text, labels)
            if v:
                status[key] = v

    return status


def fetch_histories(tickers: List[str], period: str = "1y") -> Tuple[Dict[str, List[Tuple[str, float]]], List[str]]:
    histories: Dict[str, List[Tuple[str, float]]] = {}
    errors: List[str] = []

    try:
        import yfinance as yf
    except Exception as e:
        return histories, [f"yfinance_import_failed: {e}"]

    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period=period, auto_adjust=False)
            if hist is None or hist.empty or "Close" not in hist.columns:
                errors.append(f"{ticker}: no_history")
                continue

            hist = hist.dropna(subset=["Close"])
            series: List[Tuple[str, float]] = []
            for idx, row in hist.iterrows():
                try:
                    d = idx.date().isoformat()
                except Exception:
                    d = str(idx)[:10]
                c = safe_float(row["Close"])
                if c is not None:
                    series.append((d, float(c)))

            if series:
                histories[ticker] = series
            else:
                errors.append(f"{ticker}: no_close")
        except Exception as e:
            errors.append(f"{ticker}: {type(e).__name__}: {e}")

    return histories, errors


def returns_by_lag(closes: List[float], lag: int) -> Optional[float]:
    if len(closes) <= lag:
        return None
    base = closes[-lag - 1]
    if base == 0:
        return None
    return closes[-1] / base - 1.0


def sma(closes: List[float], n: int) -> Optional[float]:
    if len(closes) < n:
        return None
    return sum(closes[-n:]) / n


def compute_price_factors(
    ticker: str,
    series: List[Tuple[str, float]],
    qqq_series: List[Tuple[str, float]],
) -> Dict[str, str]:
    out: Dict[str, str] = {}

    if not series:
        return out

    dates = [d for d, _ in series]
    closes = [c for _, c in series]
    close = closes[-1]

    out["price_anchor_date"] = dates[-1]
    out["price_anchor_close"] = fmt_float(close, 6)
    out["price_anchor_source"] = "yfinance_latest_close_v17_1_1"

    s20 = sma(closes, 20)
    s50 = sma(closes, 50)
    s100 = sma(closes, 100)

    trend_points = 0
    trend_total = 0
    for s in [s20, s50, s100]:
        if s is not None:
            trend_total += 1
            if close > s:
                trend_points += 1

    if trend_total > 0:
        trend_score = 100.0 * trend_points / trend_total
        out["trend_score"] = fmt_float(trend_score, 2)

    r20 = returns_by_lag(closes, 20)
    r60 = returns_by_lag(closes, 60)
    r120 = returns_by_lag(closes, 120)

    momentum_raw = 50.0
    if r20 is not None:
        momentum_raw += r20 * 120
    if r60 is not None:
        momentum_raw += r60 * 70
    if r120 is not None:
        momentum_raw += r120 * 40
    out["momentum_score"] = fmt_float(clamp(momentum_raw, 0, 100), 2)

    qqq_closes = [c for _, c in qqq_series]
    qqq_r20 = returns_by_lag(qqq_closes, 20) if qqq_closes else None

    if r20 is not None and qqq_r20 is not None:
        rs = 50 + (r20 - qqq_r20) * 250
        out["relative_strength_score"] = fmt_float(clamp(rs, 0, 100), 2)

    high60 = max(closes[-60:]) if len(closes) >= 60 else max(closes)
    dd60 = close / high60 - 1.0 if high60 else 0.0

    if dd60 > -0.03:
        pullback_status = "NO_PULLBACK"
        pullback_score = 25
    elif dd60 > -0.05:
        pullback_status = "TRIAL_PULLBACK"
        pullback_score = 60
    elif dd60 > -0.10:
        pullback_status = "NORMAL_PULLBACK"
        pullback_score = 85
    elif dd60 > -0.20:
        pullback_status = "DEEP_PULLBACK"
        pullback_score = 70
    else:
        pullback_status = "TREND_DAMAGE_RISK"
        pullback_score = 20

    out["pullback_status"] = pullback_status
    out["pullback_score"] = fmt_float(float(pullback_score), 2)

    overheat_penalty = 0.0
    if r20 is not None and r20 > 0.20:
        overheat_penalty += min(40, (r20 - 0.20) * 200)
    if dd60 > -0.02 and r20 is not None and r20 > 0.10:
        overheat_penalty += 15

    out["overheat_penalty"] = fmt_float(clamp(overheat_penalty, 0, 60), 2)
    if overheat_penalty >= 25:
        out["overheat_status"] = "EXTENDED"
    elif overheat_penalty > 0:
        out["overheat_status"] = "MILD_EXTENSION"
    else:
        out["overheat_status"] = "OK"

    if len(closes) >= 21:
        rets = []
        for i in range(-20, 0):
            prev = closes[i - 1]
            curr = closes[i]
            if prev:
                rets.append(curr / prev - 1.0)
        if len(rets) >= 2:
            vol_ann = statistics.stdev(rets) * math.sqrt(252)
            out["volatility_penalty"] = fmt_float(clamp(vol_ann * 100, 0, 100), 2)

    notes = []
    for name, val in [("r20", r20), ("r60", r60), ("r120", r120), ("dd60", dd60)]:
        if val is not None:
            notes.append(f"{name}={val:.4f}")
    if notes:
        out["notes"] = "V17.1.1 computed price factors; " + "; ".join(notes)

    return out


def find_idx_on_or_before(series: List[Tuple[str, float]], anchor_date: str) -> Optional[int]:
    idx = None
    for i, (d, _) in enumerate(series):
        if d <= anchor_date:
            idx = i
        elif d > anchor_date and idx is None:
            return i
    return idx


def update_forward_returns(rows: List[Dict[str, Any]], histories: Dict[str, List[Tuple[str, float]]]) -> List[str]:
    fill_count = 0
    wait_count = 0
    qqq_series = histories.get("QQQ", [])

    for row in rows:
        ticker = clean_ticker(row.get("ticker", ""))
        series = histories.get(ticker, [])
        if not ticker or not series:
            continue

        anchor_date = str(row.get("price_anchor_date", "") or row.get("snapshot_date", ""))[:10]
        anchor_close = safe_float(row.get("price_anchor_close", ""))
        if not anchor_date or anchor_close is None:
            continue

        anchor_idx = find_idx_on_or_before(series, anchor_date)
        qqq_anchor_idx = find_idx_on_or_before(qqq_series, anchor_date) if qqq_series else None

        if anchor_idx is None:
            continue

        for h in HORIZONS:
            if str(row.get(f"ret_{h}d", "")).strip():
                continue

            target_idx = anchor_idx + h
            if target_idx >= len(series):
                row[f"return_fill_status_{h}d"] = "WAIT_NOT_ENOUGH_TRADING_DAYS"
                wait_count += 1
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

    return [
        f"forward_return_fill_count={fill_count}",
        f"forward_return_wait_count={wait_count}",
    ]


def load_tracking(path: Path) -> List[Dict[str, Any]]:
    rows, _ = read_csv_safe(path)
    out = []
    for r in rows:
        out.append({c: r.get(c, "") for c in TRACKING_COLUMNS})
    return out


def upsert_rows(existing: List[Dict[str, Any]], today_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}
    order: List[Tuple[str, str]] = []

    for r in existing:
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
            base = {c: "" for c in TRACKING_COLUMNS}
        else:
            base = by_key[key]

        merged = {c: base.get(c, "") for c in TRACKING_COLUMNS}

        # Same-day same-ticker: V17.1.1 should repair stale fields.
        repair_fields = {
            "system_tier", "manual_decision", "official_action", "budget_action",
            "buy_permission", "global_mode", "trend_score", "momentum_score",
            "relative_strength_score", "pullback_score", "pullback_status",
            "overheat_penalty", "overheat_status", "volatility_penalty",
            "event_risk_score", "event_risk_band", "event_risk_status",
            "price_anchor_date", "price_anchor_close", "price_anchor_source",
            "source_files", "notes", "restriction", "event_confirmation_status",
            "candidate_rank",
        }

        for c in TRACKING_COLUMNS:
            incoming = str(r.get(c, "") or "").strip()
            if not incoming:
                continue
            if c in repair_fields:
                merged[c] = incoming
            elif not str(merged.get(c, "")).strip():
                merged[c] = incoming

        by_key[key] = merged

    rows = [by_key[k] for k in order]
    rows.sort(key=lambda x: (str(x.get("snapshot_date", "")), str(x.get("ticker", ""))))
    return rows


def build_today_rows(root: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    info = discover_candidate_info(root)
    status = parse_global_status(root)

    tickers = sorted(info.keys())
    price_tickers = sorted(set(tickers + ["QQQ"]))
    histories, price_errors = fetch_histories(price_tickers, period="1y")
    qqq_series = histories.get("QQQ", [])

    today = today_iso()
    generated = now_iso()
    rows = []

    for ticker in tickers:
        row = {c: info[ticker].get(c, "") for c in TRACKING_COLUMNS}
        row["snapshot_date"] = today
        row["generated_at"] = generated
        row["ticker"] = ticker

        for k, v in status.items():
            row[k] = v

        computed = compute_price_factors(ticker, histories.get(ticker, []), qqq_series)
        for k, v in computed.items():
            if str(v).strip():
                # For core computed factors, V17.1.1 overwrites blanks/stale.
                if k in {
                    "price_anchor_date", "price_anchor_close", "price_anchor_source",
                    "trend_score", "momentum_score", "relative_strength_score",
                    "pullback_score", "pullback_status", "overheat_penalty",
                    "overheat_status", "volatility_penalty", "notes"
                }:
                    row[k] = v

        if not str(row.get("manual_decision", "")).strip():
            row["manual_decision"] = "UNKNOWN"

        if not str(row.get("system_tier", "")).strip() or row.get("system_tier") == "UNKNOWN":
            if row["manual_decision"] == "BLOCK":
                row["system_tier"] = "D_BLOCKED_OR_EXCLUDED"
            elif row["manual_decision"] == "WATCH":
                row["system_tier"] = "C_WATCH_ONLY_EVENT_LOCKED"
            elif row["manual_decision"] == "PENDING_REVIEW":
                row["system_tier"] = "B_PENDING_MANUAL_CONFIRMATION"
            else:
                row["system_tier"] = "Z_REVIEW_REQUIRED"

        if not str(row.get("event_risk_status", "")).strip() and str(row.get("event_risk_band", "")).strip():
            row["event_risk_status"] = row["event_risk_band"]

        rows.append(row)

    return rows, price_errors


def validate(rows: List[Dict[str, Any]], today_rows: List[Dict[str, Any]], price_errors: List[str]) -> Tuple[str, List[Dict[str, str]]]:
    checks: List[Dict[str, str]] = []

    def add(level: str, check: str, detail: str) -> None:
        checks.append({"level": level, "check": check, "detail": detail})

    if today_rows:
        add("OK", "today_rows_present", f"today_rows={len(today_rows)}")
    else:
        add("FAIL", "today_rows_present", "today_rows=0")

    keys = [(r.get("snapshot_date", ""), clean_ticker(r.get("ticker", ""))) for r in rows]
    dup = len(keys) - len(set(keys))
    if dup == 0:
        add("OK", "no_duplicate_snapshot_ticker", "duplicate_count=0")
    else:
        add("FAIL", "no_duplicate_snapshot_ticker", f"duplicate_count={dup}")

    price_missing = [r.get("ticker", "") for r in today_rows if not str(r.get("price_anchor_close", "")).strip()]
    if not price_missing:
        add("OK", "today_anchor_prices_present", "missing_price_count=0")
    else:
        add("WARN", "today_anchor_prices_present", f"missing_price_count={len(price_missing)} tickers={','.join(price_missing)}")

    manual_counts = Counter(str(r.get("manual_decision", "") or "UNKNOWN").upper() for r in today_rows)
    add("OK", "today_manual_decision_counts", str(dict(manual_counts)))

    tier_counts = Counter(str(r.get("system_tier", "") or "UNKNOWN").upper() for r in today_rows)
    add("OK", "today_system_tier_counts", str(dict(tier_counts)))

    unknown_tier = tier_counts.get("UNKNOWN", 0)
    if unknown_tier == 0:
        add("OK", "system_tier_resolved", "unknown_tier_count=0")
    else:
        add("WARN", "system_tier_resolved", f"unknown_tier_count={unknown_tier}")

    global_unknown = []
    for f in ["official_action", "budget_action", "buy_permission", "global_mode"]:
        vals = Counter(str(r.get(f, "") or "UNKNOWN").upper() for r in today_rows)
        if vals.get("UNKNOWN", 0) > 0:
            global_unknown.append(f)
    if not global_unknown:
        add("OK", "global_status_resolved", "all_global_status_fields_present")
    else:
        add("WARN", "global_status_resolved", "unknown_fields=" + ",".join(global_unknown))

    factor_missing = []
    for f in ["trend_score", "momentum_score", "relative_strength_score", "pullback_score", "overheat_penalty", "volatility_penalty"]:
        missing = sum(1 for r in today_rows if not str(r.get(f, "")).strip())
        if missing:
            factor_missing.append(f"{f}:{missing}")
    if not factor_missing:
        add("OK", "computed_price_factors_present", "all_core_computed_price_factors_present")
    else:
        add("WARN", "computed_price_factors_present", "missing=" + ",".join(factor_missing))

    if price_errors:
        add("WARN", "price_fetch_messages", " | ".join(price_errors[:20]))
    else:
        add("OK", "price_fetch_messages", "no_price_fetch_errors")

    fail = sum(1 for c in checks if c["level"] == "FAIL")
    warn = sum(1 for c in checks if c["level"] == "WARN")

    if fail:
        status = "FAIL"
    elif warn:
        status = "WARN"
    else:
        status = "OK"

    return status, checks


def write_outputs(
    root: Path,
    tracking_path: Path,
    today_rows: List[Dict[str, Any]],
    all_rows: List[Dict[str, Any]],
    validation_status: str,
    checks: List[Dict[str, str]],
    forward_messages: List[str],
) -> None:
    out_dir = root / "outputs" / "v17" / "factor_effectiveness"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / "V17_1_1_FACTOR_EFFECTIVENESS_TRACKER_SUMMARY.md"
    validation_path = out_dir / "V17_1_1_FACTOR_EFFECTIVENESS_VALIDATION.md"
    validation_csv = out_dir / "v17_1_1_factor_effectiveness_validation.csv"
    read_first = out_dir / "V17_1_1_READ_FIRST.txt"

    manual_counts = Counter(str(r.get("manual_decision", "") or "UNKNOWN").upper() for r in today_rows)
    tier_counts = Counter(str(r.get("system_tier", "") or "UNKNOWN").upper() for r in today_rows)
    official_counts = Counter(str(r.get("official_action", "") or "UNKNOWN").upper() for r in today_rows)
    budget_counts = Counter(str(r.get("budget_action", "") or "UNKNOWN").upper() for r in today_rows)
    buy_counts = Counter(str(r.get("buy_permission", "") or "UNKNOWN").upper() for r in today_rows)
    global_counts = Counter(str(r.get("global_mode", "") or "UNKNOWN").upper() for r in today_rows)

    factor_price_count = sum(1 for r in today_rows if str(r.get("price_anchor_close", "")).strip())

    lines = []
    lines.append("# V17.1.1 Factor Effectiveness Tracker Summary")
    lines.append("")
    lines.append(f"生成时间：{now_iso()}")
    lines.append("")
    lines.append("## 1. 今日结论")
    lines.append("")
    lines.append(f"- TRACKER_STATUS: `{validation_status}`")
    lines.append(f"- TODAY_ROWS: `{len(today_rows)}`")
    lines.append(f"- TOTAL_TRACKING_ROWS: `{len(all_rows)}`")
    lines.append(f"- TODAY_ROWS_WITH_ANCHOR_PRICE: `{factor_price_count}`")
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
    lines.append("## 4. 今日全局执行状态")
    lines.append("")
    lines.append("### OFFICIAL ACTION")
    for k, v in sorted(official_counts.items()):
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("### BUDGET ACTION")
    for k, v in sorted(budget_counts.items()):
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("### BUY PERMISSION")
    for k, v in sorted(buy_counts.items()):
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("### GLOBAL MODE")
    for k, v in sorted(global_counts.items()):
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## 5. V17.1.1 修复内容")
    lines.append("")
    lines.append("1. 优先读取 `state\\v16_manual_review_decisions.csv` 作为人工复核 canonical source。")
    lines.append("2. WATCH / BLOCK 优先覆盖旧的 PENDING_REVIEW。")
    lines.append("3. system_tier 缺失时根据 manual_decision、restriction、event_risk_band 做可解释推断。")
    lines.append("4. official_action / budget_action / buy_permission / global_mode 从 V16 最新报告和 fallback CSV 中宽松解析。")
    lines.append("5. 当原始因子分数缺失时，用 yfinance 历史价格计算 V17.1.1 价格行为因子。")
    lines.append("")
    lines.append("## 6. 文件位置")
    lines.append("")
    lines.append(f"- TRACKING CSV: `{tracking_path}`")
    lines.append(f"- SUMMARY: `{summary_path}`")
    lines.append(f"- VALIDATION: `{validation_path}`")
    lines.append(f"- READ FIRST: `{read_first}`")
    lines.append("")
    lines.append("## 7. Forward Return Fill Messages")
    lines.append("")
    for msg in forward_messages:
        lines.append(f"- {msg}")
    lines.append("")

    summary_path.write_text("\n".join(lines), encoding="utf-8-sig")

    vlines = []
    vlines.append("# V17.1.1 Factor Effectiveness Validation")
    vlines.append("")
    vlines.append(f"生成时间：{now_iso()}")
    vlines.append("")
    vlines.append(f"VALIDATION_STATUS: `{validation_status}`")
    vlines.append("")
    vlines.append("| level | check | detail |")
    vlines.append("|---|---|---|")
    for c in checks:
        detail = str(c["detail"]).replace("|", "/")
        vlines.append(f"| {c['level']} | {c['check']} | {detail} |")
    vlines.append("")
    validation_path.write_text("\n".join(vlines), encoding="utf-8-sig")
    write_csv_safe(validation_csv, checks, ["level", "check", "detail"])

    rlines = []
    rlines.append("=== V17.1.1 FACTOR EFFECTIVENESS TRACKER READ FIRST ===")
    rlines.append("")
    rlines.append("START HERE:")
    rlines.append(str(summary_path))
    rlines.append("")
    rlines.append("TRACKING CSV:")
    rlines.append(str(tracking_path))
    rlines.append("")
    rlines.append("VALIDATION:")
    rlines.append(str(validation_path))
    rlines.append("")
    rlines.append("NORMAL COMMAND:")
    rlines.append('powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\run_v17_1_1_factor_effectiveness_tracker.ps1"')
    rlines.append("")
    read_first.write_text("\n".join(rlines), encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    tracking_path = root / "state" / "v17_factor_effectiveness_tracking.csv"

    today_rows, price_errors = build_today_rows(root)
    existing = load_tracking(tracking_path)

    tickers_for_history = sorted(set([clean_ticker(r.get("ticker", "")) for r in existing + today_rows] + ["QQQ"]))
    histories, hist_errors = fetch_histories([t for t in tickers_for_history if t], period="1y")

    all_rows = upsert_rows(existing, today_rows)
    forward_messages = update_forward_returns(all_rows, histories)

    write_csv_safe(tracking_path, all_rows, TRACKING_COLUMNS)

    validation_status, checks = validate(all_rows, today_rows, price_errors + hist_errors)
    write_outputs(root, tracking_path, today_rows, all_rows, validation_status, checks, forward_messages)

    out_dir = root / "outputs" / "v17" / "factor_effectiveness"

    print("=== V17.1.1 FACTOR EFFECTIVENESS TRACKER READY ===")
    print(f"TRACKER_STATUS: {validation_status}")
    print(f"TODAY_ROWS: {len(today_rows)}")
    print(f"TOTAL_TRACKING_ROWS: {len(all_rows)}")
    print("")
    print("START HERE:")
    print(str(out_dir / "V17_1_1_FACTOR_EFFECTIVENESS_TRACKER_SUMMARY.md"))
    print("")
    print("TRACKING CSV:")
    print(str(tracking_path))
    print("")
    print("VALIDATION:")
    print(str(out_dir / "V17_1_1_FACTOR_EFFECTIVENESS_VALIDATION.md"))
    print("")

    return 0 if validation_status in {"OK", "WARN"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
