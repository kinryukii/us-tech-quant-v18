from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R27F_STAGED_FACTOR_TECHNICAL_ROWS_READY"
STATUS_WARN = "WARN_V18_25A_R27F_STAGED_BUILD_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_25A_R27F_FORBIDDEN_MODIFIED"

MODE = "STAGED_BUILD_ONLY"
EXPECTED_TICKERS = ["RDDT", "TLN"]

R27E_READ_FIRST = "outputs/v18/ops/V18_25A_R27E_READ_FIRST.txt"
R27E_EXPECTED_STATUS = "OK_V18_25A_R27E_POST_INTEGRATION_DOWNSTREAM_READINESS_READY"

PRICE_CACHE_DIR = "state/v18/price_cache"
LEDGER_PATH = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
FACTOR_CURRENT = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_CURRENT = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
CANDIDATES_CURRENT = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"

OUT_DIR = "outputs/v18/staged_factor_technical"
OUT_FACTOR = f"{OUT_DIR}/V18_25A_R27F_CURRENT_STAGED_FACTOR_ROWS.csv"
OUT_TECH = f"{OUT_DIR}/V18_25A_R27F_CURRENT_STAGED_TECHNICAL_ROWS.csv"
OUT_VALIDATION = f"{OUT_DIR}/V18_25A_R27F_CURRENT_STAGED_BUILD_VALIDATION.csv"
OUT_RECHECK = f"{OUT_DIR}/V18_25A_R27F_CURRENT_TARGET_READINESS_RECHECK.csv"
OUT_SUMMARY = f"{OUT_DIR}/V18_25A_R27F_CURRENT_SUMMARY.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R27F_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R27F_CURRENT_STAGED_FACTOR_TECHNICAL_BUILD_REPORT.md"

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R27E_STATUS",
    "TARGET_TICKER_COUNT",
    "TARGET_TICKERS",
    "PRICE_CACHE_PRESENT_COUNT",
    "ROLLING_LEDGER_SUCCESS_COUNT",
    "OFFICIAL_FACTOR_PRESENT_COUNT",
    "OFFICIAL_TECHNICAL_PRESENT_COUNT",
    "STAGED_FACTOR_ROW_COUNT",
    "STAGED_TECHNICAL_ROW_COUNT",
    "FACTOR_BUILD_SUCCESS_COUNT",
    "FACTOR_BUILD_FAIL_COUNT",
    "TECHNICAL_BUILD_SUCCESS_COUNT",
    "TECHNICAL_BUILD_FAIL_COUNT",
    "FACTOR_SCHEMA_COMPATIBLE",
    "TECHNICAL_SCHEMA_COMPATIBLE",
    "DUPLICATE_FACTOR_TICKER_COUNT",
    "DUPLICATE_TECHNICAL_TICKER_COUNT",
    "FACTOR_SCORE_MISSING_COUNT",
    "TECHNICAL_SCORE_MISSING_COUNT",
    "OFFICIAL_MERGE_ALLOWED_NEXT",
    "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "CANDIDATES_MODIFIED",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]

SUMMARY_FIELDS = ["metric", "value", "expected", "status", "notes"]

VALIDATION_FIELDS = [
    "ticker",
    "price_cache_present",
    "price_cache_row_count",
    "rolling_ledger_success",
    "official_factor_present",
    "official_technical_present",
    "ranked_candidate_present",
    "factor_stage_success",
    "technical_stage_success",
    "factor_score_present",
    "technical_score_present",
    "validation_status",
    "error_message",
]

RECHECK_FIELDS = [
    "ticker",
    "price_cache_present",
    "price_cache_row_count",
    "price_cache_min_date",
    "price_cache_max_date",
    "price_cache_latest_close",
    "price_cache_latest_volume",
    "rolling_ledger_present",
    "rolling_ledger_success",
    "rolling_last_scan_status",
    "rolling_last_success_scan_date",
    "official_factor_present",
    "official_technical_present",
    "official_ranked_candidate_present",
    "readiness_status",
    "recommended_next_action",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except Exception:
            continue
    return ""


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def parse_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        return float(text) if text else None
    except Exception:
        return None


def parse_date(value: object) -> Optional[dt.date]:
    text = str(value or "").strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt).date()
        except Exception:
            continue
    return None


def non_null(value: object) -> bool:
    return str(value or "").strip() not in {"", "nan", "NaN", "None", "NULL"}


def get_field(row: Dict[str, str], *names: str) -> str:
    for name in names:
        value = str(row.get(name, "") or "").strip()
        if value != "":
            return value
    return ""


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def read_first_value(path: Path, key: str) -> str:
    prefix = f"{key}:"
    for line in read_text(path).splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def pct(a: float, b: float) -> object:
    if b == 0:
        return ""
    return round((a / b) - 1.0, 6)


def percentile_score(value: float, lo: float, hi: float, invert: bool = False) -> float:
    if hi == lo:
        score = 50.0
    else:
        score = max(0.0, min(100.0, 100.0 * (value - lo) / (hi - lo)))
    return round(100.0 - score if invert else score, 6)


def load_price_rows(path: Path) -> Tuple[List[Dict[str, object]], str]:
    rows, fields = read_csv(path)
    required = {"date", "open", "high", "low", "close", "volume"}
    if not path.exists():
        return [], "price cache file missing"
    if not rows or not required.issubset({field.lower() for field in fields}):
        return [], "price cache unreadable or missing required columns"
    out: List[Dict[str, object]] = []
    for row in rows:
        date_value = parse_date(row.get("date", ""))
        close_value = parse_float(row.get("close"))
        high_value = parse_float(row.get("high"))
        low_value = parse_float(row.get("low"))
        volume_value = parse_float(row.get("volume"))
        open_value = parse_float(row.get("open"))
        if not date_value or close_value is None or high_value is None or low_value is None or volume_value is None:
            continue
        out.append(
            {
                "date": date_value,
                "open": open_value if open_value is not None else close_value,
                "high": high_value,
                "low": low_value,
                "close": close_value,
                "volume": volume_value,
            }
        )
    out.sort(key=lambda item: item["date"])
    return out, "" if out else "no parseable price rows"


def rsi(closes: List[float], n: int = 14) -> object:
    if len(closes) <= n:
        return ""
    gains: List[float] = []
    losses: List[float] = []
    for i in range(-n, 0):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = sum(gains) / n
    avg_loss = sum(losses) / n
    if avg_loss == 0:
        return 100.0
    return round(100 - (100 / (1 + avg_gain / avg_loss)), 6)


def factor_row(ticker: str, prices: List[Dict[str, object]], fields: Sequence[str]) -> Dict[str, object]:
    closes = [float(r["close"]) for r in prices]
    vols = [float(r["volume"]) for r in prices]
    latest = prices[-1]

    def ret(n: int) -> object:
        return pct(closes[-1], closes[-1 - n]) if len(closes) > n else ""

    ret5, ret20, ret60, ret120 = ret(5), ret(20), ret(60), ret(120)
    avg5 = sum(vols[-5:]) / min(5, len(vols))
    avg20 = sum(vols[-20:]) / min(20, len(vols))
    vol_ratio = round(avg5 / avg20, 6) if avg20 else ""
    mom60 = float(ret60) if ret60 != "" else 0.0
    mom120 = float(ret120) if ret120 != "" else 0.0
    pullback = -float(ret5) if ret5 != "" and mom60 > 0 else 0.0
    composite = 0.45 * percentile_score(mom60, -0.5, 0.8) + 0.35 * percentile_score(mom120, -0.8, 1.5) + 0.20 * percentile_score(pullback, -0.1, 0.2)
    row = {f: "" for f in fields}
    row.update(
        {
            "factor_pack_rank": "",
            "ticker": ticker,
            "factor_pack_score": round(composite, 6),
            "latest_price_date": latest["date"].isoformat(),
            "latest_close": latest["close"],
            "ret_5d": ret5,
            "ret_20d": ret20,
            "ret_60d": ret60,
            "ret_120d": ret120,
            "volume_ratio_5_20": vol_ratio,
            "F006_SHORT_REV_5D": percentile_score(-float(ret5), -0.2, 0.2) if ret5 != "" else "",
            "F007_PULLBACK_IN_UPTREND": percentile_score(pullback, -0.1, 0.2),
            "F008_VOLUME_ABNORMAL_5_20": percentile_score(float(vol_ratio), 0.5, 2.0) if vol_ratio != "" else "",
            "F009_VOLUME_PRICE_CONFIRM": percentile_score((float(ret20) if ret20 != "" else 0.0) * (float(vol_ratio) if vol_ratio != "" else 1.0), -0.2, 0.4),
            "F010_XSEC_COMPOSITE_RANK": round(composite, 6),
            "F011_TS_MOMENTUM_60_120": percentile_score((mom60 + mom120) / 2.0, -0.5, 1.0),
            "F012_TS_PULLBACK_REVERSAL": percentile_score(pullback, -0.1, 0.2),
            "volatility_penalty": "",
            "overheat_penalty": "",
            "shadow_side_hint": "STAGED_R27F_RECOMPUTE",
        }
    )
    return row


def technical_row(ticker: str, prices: List[Dict[str, object]], fields: Sequence[str]) -> Dict[str, object]:
    closes = [float(r["close"]) for r in prices]
    highs = [float(r["high"] or r["close"]) for r in prices]
    lows = [float(r["low"] or r["close"]) for r in prices]
    vols = [float(r["volume"]) for r in prices]
    latest = prices[-1]
    last20 = closes[-20:] if len(closes) >= 20 else closes
    mid = sum(last20) / len(last20)
    stdev = (sum((x - mid) ** 2 for x in last20) / len(last20)) ** 0.5 if last20 else 0.0
    upper = mid + 2 * stdev
    lower = mid - 2 * stdev
    pct_b = (closes[-1] - lower) / (upper - lower) if upper != lower else 0.5
    bandwidth = (upper - lower) / mid if mid else ""
    rsi14 = rsi(closes)
    low14 = min(lows[-14:]) if len(lows) >= 14 else min(lows)
    high14 = max(highs[-14:]) if len(highs) >= 14 else max(highs)
    k = 100 * (closes[-1] - low14) / (high14 - low14) if high14 != low14 else 50.0
    d = k
    j = 3 * k - 2 * d
    avg5 = sum(vols[-5:]) / min(5, len(vols))
    avg20 = sum(vols[-20:]) / min(20, len(vols))
    vol_ratio = avg5 / avg20 if avg20 else ""
    score = 50.0
    if rsi14 != "":
        score += 10 if float(rsi14) < 40 else (-10 if float(rsi14) > 70 else 0)
    score += 10 if pct_b < 0.35 else (-10 if pct_b > 0.9 else 0)
    score = round(max(0, min(100, score)), 6)
    row = {f: "" for f in fields}
    row.update(
        {
            "ticker": ticker,
            "yf_ticker": ticker,
            "price_date": latest["date"].isoformat(),
            "close": latest["close"],
            "bb_mid_20": round(mid, 6),
            "bb_upper_20_2": round(upper, 6),
            "bb_lower_20_2": round(lower, 6),
            "bb_percent_b": round(pct_b, 6),
            "bb_bandwidth": round(bandwidth, 6) if bandwidth != "" else "",
            "bb_squeeze_flag": "False",
            "bb_status": "BB_LOWER_HALF" if pct_b < 0.5 else "BB_UPPER_HALF",
            "rsi_14": rsi14,
            "rsi_status": "RSI_OVERSOLD" if rsi14 != "" and float(rsi14) < 30 else ("RSI_WEAK" if rsi14 != "" and float(rsi14) < 45 else "RSI_NEUTRAL"),
            "kdj_k": round(k, 6),
            "kdj_d": round(d, 6),
            "kdj_j": round(j, 6),
            "kdj_status": "KDJ_OVERSOLD" if k < 20 else "KDJ_NEUTRAL",
            "volume_ratio_5_20": round(vol_ratio, 6) if vol_ratio != "" else "",
            "overheat_penalty": 0,
            "pullback_timing_bonus": 10 if pct_b < 0.35 else 0,
            "breakout_confirmation_bonus": 10 if pct_b > 0.85 else 0,
            "technical_timing_score": score,
            "technical_signal": "TECH_TIMING_STAGED_REFRESH",
            "technical_warning_label": "STAGED_R27F_NOT_MERGED",
            "option_data_status": "NOT_AVAILABLE_RESERVED",
            "put_call_ratio": "",
            "iv_rank_proxy": "",
            "gamma_squeeze_status": "NOT_AVAILABLE_RESERVED",
            "gamma_squeeze_risk_label": "NOT_AVAILABLE_RESERVED",
            "official_decision_impact": "NONE",
            "vix_date": "",
            "vix_close": "",
            "vix_regime": "",
        }
    )
    return row


def count_dupes(rows: List[Dict[str, object]]) -> int:
    seen = set()
    dupes = 0
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker in seen:
            dupes += 1
        seen.add(ticker)
    return dupes


def scan_presence(path: Path, ticker: str, alias_fields: Sequence[str]) -> Tuple[bool, int]:
    rows, fields = read_csv(path)
    if not rows or not fields:
        return False, 0
    ticker_col = None
    field_norm = {str(field).strip().lower(): field for field in fields}
    for alias in alias_fields:
        if alias.lower() in field_norm:
            ticker_col = field_norm[alias.lower()]
            break
    if not ticker_col:
        return False, 0
    count = sum(1 for row in rows if norm_ticker(row.get(ticker_col)) == ticker)
    return count > 0, count


def ledger_metrics(root: Path, today: dt.date) -> Tuple[Dict[str, int], Dict[str, Dict[str, str]]]:
    rows, fields = read_csv(root / LEDGER_PATH)
    ticker_col = None
    success_count_col = None
    success_date_col = None
    status_col = None
    field_map = {str(field).strip().lower(): field for field in fields}
    for alias in ["ticker", "symbol"]:
        if alias in field_map:
            ticker_col = field_map[alias]
            break
    for alias in ["success_scan_count"]:
        if alias in field_map:
            success_count_col = field_map[alias]
            break
    for alias in ["last_success_scan_date", "last_success_date", "latest_success_date"]:
        if alias in field_map:
            success_date_col = field_map[alias]
            break
    for alias in ["last_scan_status", "scan_status", "status"]:
        if alias in field_map:
            status_col = field_map[alias]
            break
    by_ticker: Dict[str, Dict[str, str]] = {}
    covered = never = stale = artifact = 0
    seen: set[str] = set()
    for row in rows:
        ticker = norm_ticker(row.get(ticker_col or ""))
        if ticker == "TICKERS":
            artifact += 1
        by_ticker[ticker] = row
        if ticker in seen:
            continue
        seen.add(ticker)
        success_count = to_int(row.get(success_count_col or ""))
        success_date = parse_date(row.get(success_date_col or ""))
        if success_count <= 0 or success_date is None:
            never += 1
        elif 0 <= (today - success_date).days <= 5:
            covered += 1
        else:
            stale += 1
    counts = {
        "total": len(rows),
        "covered": covered,
        "never": never,
        "stale": stale,
        "remaining": never + stale,
        "artifact": artifact,
    }
    return counts, by_ticker


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object], warnings: List[str], recheck_rows: List[Dict[str, object]], validation_rows: List[Dict[str, object]]) -> str:
    audit_lines = "\n".join(f"- {row['ticker']}: {row['readiness_status']} -> {row['recommended_next_action']}" for row in recheck_rows)
    warning_lines = "\n".join(f"- {line}" for line in warnings) if warnings else "- None."
    validation_lines = "\n".join(f"- {row['ticker']}: {row['validation_status']}" for row in validation_rows)
    return "\n".join(
        [
            "# V18.25A-R27F Staged Factor + Technical Build for TLN/RDDT Only",
            "",
            f"- STATUS: {values['STATUS']}",
            f"- MODE: {values['MODE']}",
            f"- RUN_ID: {values['RUN_ID']}",
            f"- R27E_STATUS: {values['R27E_STATUS']}",
            "",
            "## Readiness",
            "",
            audit_lines if audit_lines else "- None.",
            "",
            "## Validation",
            "",
            validation_lines if validation_lines else "- None.",
            "",
            "## Warnings",
            "",
            warning_lines,
            "",
            "## Summary",
            "",
            f"- STAGED_FACTOR_ROW_COUNT: {values['STAGED_FACTOR_ROW_COUNT']}",
            f"- STAGED_TECHNICAL_ROW_COUNT: {values['STAGED_TECHNICAL_ROW_COUNT']}",
            f"- FACTOR_BUILD_SUCCESS_COUNT: {values['FACTOR_BUILD_SUCCESS_COUNT']}",
            f"- TECHNICAL_BUILD_SUCCESS_COUNT: {values['TECHNICAL_BUILD_SUCCESS_COUNT']}",
            f"- FACTOR_SCHEMA_COMPATIBLE: {values['FACTOR_SCHEMA_COMPATIBLE']}",
            f"- TECHNICAL_SCHEMA_COMPATIBLE: {values['TECHNICAL_SCHEMA_COMPATIBLE']}",
            "",
            "## Guardrails",
            "",
            f"- OFFICIAL_MERGE_ALLOWED_NEXT: {values['OFFICIAL_MERGE_ALLOWED_NEXT']}",
            f"- PRICE_CACHE_MODIFIED: {values['PRICE_CACHE_MODIFIED']}",
            f"- ROLLING_LEDGER_MODIFIED: {values['ROLLING_LEDGER_MODIFIED']}",
            f"- FACTOR_PACK_MODIFIED: {values['FACTOR_PACK_MODIFIED']}",
            f"- TECHNICAL_TIMING_MODIFIED: {values['TECHNICAL_TIMING_MODIFIED']}",
            f"- CANDIDATES_MODIFIED: {values['CANDIDATES_MODIFIED']}",
            f"- EXTERNAL_FETCH_EXECUTED: {values['EXTERNAL_FETCH_EXECUTED']}",
            f"- BACKTEST_EXECUTED: {values['BACKTEST_EXECUTED']}",
            f"- OFFICIAL_DECISION_IMPACT: {values['OFFICIAL_DECISION_IMPACT']}",
            f"- AUTO_TRADE: {values['AUTO_TRADE']}",
            f"- AUTO_SELL: {values['AUTO_SELL']}",
            f"- FORBIDDEN_MODIFIED: {values['FORBIDDEN_MODIFIED']}",
            "",
            f"NEXT_RECOMMENDED_STEP: {values['NEXT_RECOMMENDED_STEP']}",
            "",
        ]
    )


def coverage_summary(root: Path, today: dt.date) -> Dict[str, int]:
    return ledger_metrics(root, today)[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R27F_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    today = dt.date.today()

    price_before = tree_sig(root / PRICE_CACHE_DIR)
    ledger_before = file_sig(root / LEDGER_PATH)
    factor_before = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_before = tree_sig(root / "outputs" / "v18" / "technical_timing")
    candidates_before = tree_sig(root / "outputs" / "v18" / "candidates")
    official_before = tree_sig(root / "outputs" / "v18" / "official_decisions")

    r27e_status = read_first_value(root / R27E_READ_FIRST, "STATUS")
    ready_count = to_int(read_first_value(root / R27E_READ_FIRST, "READY_FOR_STAGED_FACTOR_TECHNICAL_BUILD_COUNT"))
    blocked_count = to_int(read_first_value(root / R27E_READ_FIRST, "BLOCKED_COUNT"))

    required_errors: List[str] = []
    if not (root / R27E_READ_FIRST).exists():
        required_errors.append(f"missing required input: {R27E_READ_FIRST}")
    if r27e_status != R27E_EXPECTED_STATUS:
        required_errors.append(f"R27E status is {r27e_status or 'MISSING'}")
    if ready_count != 2:
        required_errors.append(f"R27E ready count is {ready_count}, expected 2")
    if blocked_count != 0:
        required_errors.append(f"R27E blocked count is {blocked_count}, expected 0")

    factor_current_rows, factor_current_fields = read_csv(root / FACTOR_CURRENT)
    tech_current_rows, tech_current_fields = read_csv(root / TECH_CURRENT)
    candidate_current_rows, candidate_current_fields = read_csv(root / CANDIDATES_CURRENT)
    if not factor_current_fields:
        required_errors.append("official factor current file unreadable")
    if not tech_current_fields:
        required_errors.append("official technical current file unreadable")
    if not candidate_current_fields:
        required_errors.append("official ranked candidates file unreadable")

    price_present_count = 0
    ledger_success_count = 0
    official_factor_present_count = 0
    official_technical_present_count = 0
    ranked_candidate_present_count = 0
    warnings: List[str] = []
    recheck_rows: List[Dict[str, object]] = []
    validation_rows: List[Dict[str, object]] = []
    staged_factor_rows: List[Dict[str, object]] = []
    staged_technical_rows: List[Dict[str, object]] = []
    staged_price_info: Dict[str, Tuple[List[Dict[str, object]], str]] = {}
    factor_score_missing_count = 0
    technical_score_missing_count = 0
    validation_fail_count = 0

    coverage_counts, ledger_by_ticker = ledger_metrics(root, today)
    official_factor_by_ticker = {norm_ticker(row.get("ticker")): row for row in factor_current_rows}
    official_technical_by_ticker = {norm_ticker(row.get("ticker") or row.get("yf_ticker")): row for row in tech_current_rows}
    official_candidate_by_ticker = {norm_ticker(row.get("ticker")): row for row in candidate_current_rows}

    for ticker in EXPECTED_TICKERS:
        price_info, price_err = load_price_rows(root / PRICE_CACHE_DIR / f"{ticker}.csv")
        staged_price_info[ticker] = (price_info, price_err)
        price_present = bool(price_info)
        price_row_count = len(price_info)
        price_min_date = price_info[0]["date"].isoformat() if price_info else ""
        price_max_date = price_info[-1]["date"].isoformat() if price_info else ""
        latest_close = price_info[-1]["close"] if price_info else ""
        latest_volume = price_info[-1]["volume"] if price_info else ""
        ledger_row = ledger_by_ticker.get(ticker, {})
        ledger_present = bool(ledger_row)
        ledger_status = get_field(ledger_row, "last_scan_status", "scan_status", "status")
        ledger_success = ledger_status == "SUCCESS_LOCAL_PRICE_FULL_HISTORY" and get_field(ledger_row, "last_success_scan_date") == today.isoformat()
        factor_present = ticker in official_factor_by_ticker
        technical_present = ticker in official_technical_by_ticker
        ranked_candidate_present = ticker in official_candidate_by_ticker

        if price_present:
            price_present_count += 1
        if ledger_success:
            ledger_success_count += 1
        if factor_present:
            official_factor_present_count += 1
        if technical_present:
            official_technical_present_count += 1
        if ranked_candidate_present:
            ranked_candidate_present_count += 1

        readiness_status = "BLOCKED"
        recommended_next_action = "REVIEW_R27F_STAGED_BUILD_VALIDATION"
        if price_present and ledger_success:
            if factor_present and technical_present:
                readiness_status = "ALREADY_DOWNSTREAM_READY"
                recommended_next_action = "R27G_REVIEW_STAGED_FACTOR_TECHNICAL_ROWS_FOR_OFFICIAL_MERGE_PLAN"
            else:
                readiness_status = "READY_FOR_STAGED_FACTOR_TECHNICAL_BUILD"
                recommended_next_action = "R27G_REVIEW_STAGED_FACTOR_TECHNICAL_ROWS_FOR_OFFICIAL_MERGE_PLAN"

        if not price_present or not ledger_success:
            warnings.append(f"{ticker} failed base price cache or ledger success readiness checks.")
        if factor_present or technical_present or ranked_candidate_present:
            warnings.append(f"{ticker} already appears in downstream current outputs.")

        recheck_rows.append(
            {
                "ticker": ticker,
                "price_cache_present": str(price_present).upper(),
                "price_cache_row_count": price_row_count,
                "price_cache_min_date": price_min_date,
                "price_cache_max_date": price_max_date,
                "price_cache_latest_close": latest_close,
                "price_cache_latest_volume": latest_volume,
                "rolling_ledger_present": str(ledger_present).upper(),
                "rolling_ledger_success": str(ledger_success).upper(),
                "rolling_last_scan_status": ledger_status,
                "rolling_last_success_scan_date": get_field(ledger_row, "last_success_scan_date"),
                "official_factor_present": str(factor_present).upper(),
                "official_technical_present": str(technical_present).upper(),
                "official_ranked_candidate_present": str(ranked_candidate_present).upper(),
                "readiness_status": readiness_status,
                "recommended_next_action": recommended_next_action,
            }
        )

        if not price_present or not ledger_success:
            validation_rows.append(
                {
                    "ticker": ticker,
                    "price_cache_present": str(price_present).upper(),
                    "price_cache_row_count": price_row_count,
                    "rolling_ledger_success": str(ledger_success).upper(),
                    "official_factor_present": str(factor_present).upper(),
                    "official_technical_present": str(technical_present).upper(),
                    "ranked_candidate_present": str(ranked_candidate_present).upper(),
                    "factor_stage_success": "FALSE",
                    "technical_stage_success": "FALSE",
                    "factor_score_present": "FALSE",
                    "technical_score_present": "FALSE",
                    "validation_status": "FAIL",
                    "error_message": "Base readiness failed before staged build.",
                }
            )
            continue

        fr = factor_row(ticker, price_info, factor_current_fields)
        tr = technical_row(ticker, price_info, tech_current_fields)
        staged_factor_rows.append(fr)
        staged_technical_rows.append(tr)
        factor_score_present = non_null(fr.get("factor_pack_score"))
        technical_score_present = non_null(tr.get("technical_timing_score"))
        if not factor_score_present:
            factor_score_missing_count += 1
        if not technical_score_present:
            technical_score_missing_count += 1
        validation_status = "PASS" if factor_score_present and technical_score_present else "FAIL"
        validation_rows.append(
            {
                "ticker": ticker,
                "price_cache_present": str(price_present).upper(),
                "price_cache_row_count": price_row_count,
                "rolling_ledger_success": str(ledger_success).upper(),
                "official_factor_present": str(factor_present).upper(),
                "official_technical_present": str(technical_present).upper(),
                "ranked_candidate_present": str(ranked_candidate_present).upper(),
                "factor_stage_success": "TRUE",
                "technical_stage_success": "TRUE",
                "factor_score_present": str(factor_score_present).upper(),
                "technical_score_present": str(technical_score_present).upper(),
                "validation_status": validation_status,
                "error_message": "" if validation_status == "PASS" else "Missing factor or technical score.",
            }
        )

    staged_factor_rows.sort(key=lambda row: (-float(row.get("factor_pack_score") or 0.0), norm_ticker(row.get("ticker"))))
    for idx, row in enumerate(staged_factor_rows, 1):
        row["factor_pack_rank"] = idx

    factor_schema_compatible = bool(staged_factor_rows) and set(factor_current_fields).issubset(set(staged_factor_rows[0].keys()))
    technical_schema_compatible = bool(staged_technical_rows) and set(tech_current_fields).issubset(set(staged_technical_rows[0].keys()))
    duplicate_factor_ticker_count = count_dupes(staged_factor_rows)
    duplicate_technical_ticker_count = count_dupes(staged_technical_rows)

    if official_factor_present_count != 0:
        warnings.append(f"official factor current contains {official_factor_present_count} target rows.")
    if official_technical_present_count != 0:
        warnings.append(f"official technical current contains {official_technical_present_count} target rows.")
    if ranked_candidate_present_count != 0:
        warnings.append(f"official ranked candidates current contains {ranked_candidate_present_count} target rows.")
    if coverage_counts["total"] != 323:
        warnings.append(f"ledger total rows are {coverage_counts['total']} not 323.")
    if coverage_counts["covered"] != 303:
        warnings.append(f"covered within 5D is {coverage_counts['covered']} not 303.")
    if coverage_counts["never"] != 20:
        warnings.append(f"never-success count is {coverage_counts['never']} not 20.")
    if coverage_counts["stale"] != 0:
        warnings.append(f"stale count is {coverage_counts['stale']} not 0.")
    if coverage_counts["remaining"] != 20:
        warnings.append(f"remaining count is {coverage_counts['remaining']} not 20.")
    if duplicate_factor_ticker_count != 0:
        warnings.append("duplicate factor staged ticker rows detected.")
    if duplicate_technical_ticker_count != 0:
        warnings.append("duplicate technical staged ticker rows detected.")
    if factor_score_missing_count != 0 or technical_score_missing_count != 0:
        warnings.append("one or more staged score values were missing.")

    if required_errors:
        status = STATUS_FAIL
        validation_fail_count = 1
    elif any("failed base price cache or ledger success" in warning for warning in warnings):
        status = STATUS_WARN
        validation_fail_count = 0
    elif factor_schema_compatible and technical_schema_compatible and duplicate_factor_ticker_count == 0 and duplicate_technical_ticker_count == 0 and factor_score_missing_count == 0 and technical_score_missing_count == 0 and not warnings:
        status = STATUS_OK
        validation_fail_count = 0
    elif warnings:
        status = STATUS_WARN
        validation_fail_count = 0
    else:
        status = STATUS_OK
        validation_fail_count = 0

    if status == STATUS_OK and (not factor_schema_compatible or not technical_schema_compatible or factor_score_missing_count or technical_score_missing_count):
        status = STATUS_WARN

    write_csv(root / OUT_FACTOR, staged_factor_rows, factor_current_fields)
    write_csv(root / OUT_TECH, staged_technical_rows, tech_current_fields)
    write_csv(root / OUT_VALIDATION, validation_rows, VALIDATION_FIELDS)
    write_csv(root / OUT_RECHECK, recheck_rows, RECHECK_FIELDS)

    summary_rows = [
        {"metric": "R27E_STATUS", "value": r27e_status or "MISSING", "expected": R27E_EXPECTED_STATUS, "status": "OK" if r27e_status == R27E_EXPECTED_STATUS else "WARN", "notes": ""},
        {"metric": "TARGET_TICKER_COUNT", "value": len(EXPECTED_TICKERS), "expected": 2, "status": "OK", "notes": ""},
        {"metric": "PRICE_CACHE_PRESENT_COUNT", "value": price_present_count, "expected": 2, "status": "OK" if price_present_count == 2 else "WARN", "notes": ""},
        {"metric": "ROLLING_LEDGER_SUCCESS_COUNT", "value": ledger_success_count, "expected": 2, "status": "OK" if ledger_success_count == 2 else "WARN", "notes": ""},
        {"metric": "OFFICIAL_FACTOR_PRESENT_COUNT", "value": official_factor_present_count, "expected": 0, "status": "OK" if official_factor_present_count == 0 else "WARN", "notes": ""},
        {"metric": "OFFICIAL_TECHNICAL_PRESENT_COUNT", "value": official_technical_present_count, "expected": 0, "status": "OK" if official_technical_present_count == 0 else "WARN", "notes": ""},
        {"metric": "RANKED_CANDIDATE_PRESENT_COUNT", "value": ranked_candidate_present_count, "expected": 0, "status": "OK" if ranked_candidate_present_count == 0 else "WARN", "notes": ""},
        {"metric": "STAGED_FACTOR_ROW_COUNT", "value": len(staged_factor_rows), "expected": 2, "status": "OK" if len(staged_factor_rows) == 2 else "WARN", "notes": ""},
        {"metric": "STAGED_TECHNICAL_ROW_COUNT", "value": len(staged_technical_rows), "expected": 2, "status": "OK" if len(staged_technical_rows) == 2 else "WARN", "notes": ""},
        {"metric": "FACTOR_BUILD_SUCCESS_COUNT", "value": len(staged_factor_rows), "expected": 2, "status": "OK" if len(staged_factor_rows) == 2 else "WARN", "notes": ""},
        {"metric": "FACTOR_BUILD_FAIL_COUNT", "value": 0, "expected": 0, "status": "OK", "notes": ""},
        {"metric": "TECHNICAL_BUILD_SUCCESS_COUNT", "value": len(staged_technical_rows), "expected": 2, "status": "OK" if len(staged_technical_rows) == 2 else "WARN", "notes": ""},
        {"metric": "TECHNICAL_BUILD_FAIL_COUNT", "value": 0, "expected": 0, "status": "OK", "notes": ""},
        {"metric": "FACTOR_SCHEMA_COMPATIBLE", "value": str(factor_schema_compatible).upper(), "expected": "TRUE", "status": "OK" if factor_schema_compatible else "WARN", "notes": ""},
        {"metric": "TECHNICAL_SCHEMA_COMPATIBLE", "value": str(technical_schema_compatible).upper(), "expected": "TRUE", "status": "OK" if technical_schema_compatible else "WARN", "notes": ""},
        {"metric": "DUPLICATE_FACTOR_TICKER_COUNT", "value": duplicate_factor_ticker_count, "expected": 0, "status": "OK" if duplicate_factor_ticker_count == 0 else "WARN", "notes": ""},
        {"metric": "DUPLICATE_TECHNICAL_TICKER_COUNT", "value": duplicate_technical_ticker_count, "expected": 0, "status": "OK" if duplicate_technical_ticker_count == 0 else "WARN", "notes": ""},
        {"metric": "FACTOR_SCORE_MISSING_COUNT", "value": factor_score_missing_count, "expected": 0, "status": "OK" if factor_score_missing_count == 0 else "WARN", "notes": ""},
        {"metric": "TECHNICAL_SCORE_MISSING_COUNT", "value": technical_score_missing_count, "expected": 0, "status": "OK" if technical_score_missing_count == 0 else "WARN", "notes": ""},
        {"metric": "TOTAL_LEDGER_ROWS", "value": coverage_counts["total"], "expected": 323, "status": "OK" if coverage_counts["total"] == 323 else "WARN", "notes": ""},
        {"metric": "COVERED_WITHIN_5D", "value": coverage_counts["covered"], "expected": 303, "status": "OK" if coverage_counts["covered"] == 303 else "WARN", "notes": ""},
        {"metric": "NEVER_SUCCESS_COUNT", "value": coverage_counts["never"], "expected": 20, "status": "OK" if coverage_counts["never"] == 20 else "WARN", "notes": ""},
        {"metric": "STALE_COUNT", "value": coverage_counts["stale"], "expected": 0, "status": "OK" if coverage_counts["stale"] == 0 else "WARN", "notes": ""},
        {"metric": "REMAINING_COUNT", "value": coverage_counts["remaining"], "expected": 20, "status": "OK" if coverage_counts["remaining"] == 20 else "WARN", "notes": ""},
    ]
    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    price_after = tree_sig(root / PRICE_CACHE_DIR)
    ledger_after = file_sig(root / LEDGER_PATH)
    factor_after = tree_sig(root / "outputs" / "v18" / "factor_pack")
    tech_after = tree_sig(root / "outputs" / "v18" / "technical_timing")
    candidates_after = tree_sig(root / "outputs" / "v18" / "candidates")
    official_after = tree_sig(root / "outputs" / "v18" / "official_decisions")
    price_modified = price_after != price_before
    ledger_modified = ledger_after != ledger_before
    factor_modified = factor_after != factor_before
    tech_modified = tech_after != tech_before
    candidates_modified = candidates_after != candidates_before
    official_modified = official_after != official_before
    forbidden_modified = price_modified or ledger_modified or factor_modified or tech_modified or candidates_modified or official_modified
    if forbidden_modified:
        status = STATUS_FAIL
        validation_fail_count = 1

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R27E_STATUS": r27e_status or "MISSING",
        "TARGET_TICKER_COUNT": len(EXPECTED_TICKERS),
        "TARGET_TICKERS": ",".join(EXPECTED_TICKERS),
        "PRICE_CACHE_PRESENT_COUNT": price_present_count,
        "ROLLING_LEDGER_SUCCESS_COUNT": ledger_success_count,
        "OFFICIAL_FACTOR_PRESENT_COUNT": official_factor_present_count,
        "OFFICIAL_TECHNICAL_PRESENT_COUNT": official_technical_present_count,
        "STAGED_FACTOR_ROW_COUNT": len(staged_factor_rows),
        "STAGED_TECHNICAL_ROW_COUNT": len(staged_technical_rows),
        "FACTOR_BUILD_SUCCESS_COUNT": len(staged_factor_rows),
        "FACTOR_BUILD_FAIL_COUNT": 0,
        "TECHNICAL_BUILD_SUCCESS_COUNT": len(staged_technical_rows),
        "TECHNICAL_BUILD_FAIL_COUNT": 0,
        "FACTOR_SCHEMA_COMPATIBLE": str(factor_schema_compatible).upper(),
        "TECHNICAL_SCHEMA_COMPATIBLE": str(technical_schema_compatible).upper(),
        "DUPLICATE_FACTOR_TICKER_COUNT": duplicate_factor_ticker_count,
        "DUPLICATE_TECHNICAL_TICKER_COUNT": duplicate_technical_ticker_count,
        "FACTOR_SCORE_MISSING_COUNT": factor_score_missing_count,
        "TECHNICAL_SCORE_MISSING_COUNT": technical_score_missing_count,
        "OFFICIAL_MERGE_ALLOWED_NEXT": "FALSE",
        "PRICE_CACHE_MODIFIED": str(price_modified).upper(),
        "ROLLING_LEDGER_MODIFIED": str(ledger_modified).upper(),
        "FACTOR_PACK_MODIFIED": str(factor_modified).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(tech_modified).upper(),
        "CANDIDATES_MODIFIED": str(candidates_modified).upper(),
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": "R27G_REVIEW_STAGED_FACTOR_TECHNICAL_ROWS_FOR_OFFICIAL_MERGE_PLAN",
    }

    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, warnings, recheck_rows, validation_rows))
    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if status == STATUS_FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
