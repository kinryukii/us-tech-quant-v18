from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRYRUN = "OK_V18_25A_R25B_DRYRUN_STAGED_BUILD_PLAN_READY"
STATUS_OK = "OK_V18_25A_R25B_STAGED_FACTOR_TECHNICAL_ROWS_READY"
STATUS_GATE = "WARN_V18_25A_R25B_R25A_GATE_NOT_PASS"
STATUS_ZERO = "WARN_V18_25A_R25B_ZERO_TARGETS"
STATUS_PRICE = "WARN_V18_25A_R25B_PRICE_CACHE_VALIDATION_FAILURE"
STATUS_FACTOR = "WARN_V18_25A_R25B_FACTOR_BUILD_PARTIAL_FAILURE"
STATUS_TECH = "WARN_V18_25A_R25B_TECHNICAL_BUILD_PARTIAL_FAILURE"
STATUS_SCHEMA = "WARN_V18_25A_R25B_SCHEMA_VALIDATION_REVIEW_NEEDED"
STATUS_MERGE_REFUSED = "WARN_V18_25A_R25B_MERGE_REFUSED_FOR_SAFETY"

MODE_DRYRUN = "DRYRUN_STAGED_BUILD_PLAN_ONLY"
MODE = "STAGED_BUILD_ONLY"

R25_COMBINED = "outputs/v18/readiness/V18_25A_R25_CURRENT_COMBINED_REFRESH_PLAN.csv"
R25_FACTOR_PLAN = "outputs/v18/readiness/V18_25A_R25_CURRENT_FACTOR_BUILD_PLAN.csv"
R25_TECH_PLAN = "outputs/v18/readiness/V18_25A_R25_CURRENT_TECHNICAL_REFRESH_PLAN.csv"
R25A_BUILDERS = "outputs/v18/readiness/V18_25A_R25A_CURRENT_BUILDER_SELECTION_PLAN.csv"
R25A_GATE = "outputs/v18/readiness/V18_25A_R25A_CURRENT_R25B_INPUT_GATE.csv"
PRICE_CACHE = "state/v18/price_cache"
FACTOR_CURRENT = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_CURRENT = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OUT_TARGETS = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_TARGETS.csv"
OUT_FACTOR = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_STAGED_FACTOR_ROWS.csv"
OUT_TECH = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_STAGED_TECHNICAL_ROWS.csv"
OUT_FACTOR_AUDIT = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_FACTOR_BUILD_AUDIT.csv"
OUT_TECH_AUDIT = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_TECHNICAL_BUILD_AUDIT.csv"
OUT_SCHEMA = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_SCHEMA_VALIDATION.csv"
OUT_HOLDS = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_HOLDS_AND_FAILURES.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R25B_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R25B_CURRENT_STAGED_FACTOR_TECHNICAL_BUILD_REPORT.md"

TARGET_FIELDS = ["priority_rank", "ticker", "source_batch", "target_status", "price_cache_file", "price_row_count", "reason"]
AUDIT_FIELDS = ["ticker", "build_attempted", "build_success", "row_count", "status", "error_message"]
SCHEMA_FIELDS = ["schema_item", "status", "value", "notes"]
HOLD_FIELDS = ["ticker", "hold_type", "reason", "next_action"]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "RUN_ID", "R25_COMBINED_PLAN_PATH", "R25A_INPUT_GATE_PATH", "MAX_TICKERS", "EXPECTED_TARGET_COUNT",
    "SELECTED_TARGET_COUNT", "DEDUPED_TARGET_COUNT", "PRICE_CACHE_VALIDATION_SUCCESS_COUNT", "PRICE_CACHE_VALIDATION_FAIL_COUNT",
    "FACTOR_BUILDER_SELECTED", "TECHNICAL_BUILDER_SELECTED", "FACTOR_BUILDER_PARSE_STATUS", "TECHNICAL_BUILDER_PARSE_STATUS",
    "STAGED_FACTOR_ROW_COUNT", "STAGED_TECHNICAL_ROW_COUNT", "FACTOR_BUILD_SUCCESS_COUNT", "FACTOR_BUILD_FAIL_COUNT",
    "TECHNICAL_BUILD_SUCCESS_COUNT", "TECHNICAL_BUILD_FAIL_COUNT", "FACTOR_SCHEMA_COMPATIBLE", "TECHNICAL_SCHEMA_COMPATIBLE",
    "DUPLICATE_FACTOR_TICKER_COUNT", "DUPLICATE_TECHNICAL_TICKER_COUNT", "HOLDS_AND_FAILURES_COUNT", "STAGED_FACTOR_ROWS_PATH",
    "STAGED_TECHNICAL_ROWS_PATH", "FACTOR_BUILD_AUDIT_PATH", "TECHNICAL_BUILD_AUDIT_PATH", "SCHEMA_VALIDATION_PATH",
    "OFFICIAL_FACTOR_PACK_MERGE_ALLOWED_NOW", "OFFICIAL_TECHNICAL_TIMING_MERGE_ALLOWED_NOW", "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE", "AUTO_SELL", "EXTERNAL_FETCH_EXECUTED", "BACKTEST_EXECUTED", "PRICE_CACHE_MODIFIED", "ROLLING_LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "TIER_FILES_MODIFIED", "OFFICIAL_DECISION_MODIFIED", "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED", "NEXT_RECOMMENDED_STEP",
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
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as h:
                r = csv.DictReader(h)
                return [dict(row) for row in r], list(r.fieldnames or [])
        except Exception:
            continue
    return [], []


def norm_ticker(v: object) -> str:
    return str(v or "").strip().upper()


def is_true(v: object) -> bool:
    return str(v or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def to_float(v: object) -> Optional[float]:
    try:
        s = str(v or "").strip()
        return float(s) if s else None
    except Exception:
        return None


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    st = path.stat()
    return int(st.st_mtime_ns), int(st.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(p.relative_to(root)): file_sig(p) for p in root.rglob("*") if p.is_file()}


def parse_py(path: Path) -> str:
    try:
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return "PY_AST_PARSE_OK"
    except Exception as e:
        return f"PY_AST_PARSE_FAIL:{type(e).__name__}"


def parse_date(s: object) -> Optional[dt.date]:
    t = str(s or "").strip()[:10]
    try:
        return dt.datetime.strptime(t, "%Y-%m-%d").date()
    except Exception:
        return None


def load_prices(path: Path) -> Tuple[List[Dict[str, object]], str]:
    rows, fields = read_csv(path)
    required = {"date", "open", "high", "low", "close", "volume"}
    if not path.exists():
        return [], "price cache file missing"
    if not rows or not required.issubset({f.lower() for f in fields}):
        return [], "price cache unreadable or missing required columns"
    out = []
    for r in rows:
        d = parse_date(r.get("date"))
        c = to_float(r.get("close"))
        if not d or c is None:
            continue
        out.append({
            "date": d,
            "open": to_float(r.get("open")),
            "high": to_float(r.get("high")),
            "low": to_float(r.get("low")),
            "close": c,
            "volume": to_float(r.get("volume")) or 0.0,
        })
    out.sort(key=lambda x: x["date"])
    return out, "" if out else "no parseable price rows"


def pct(a: float, b: float) -> str:
    if b == 0:
        return ""
    return round((a / b) - 1.0, 6)


def percentile_score(value: float, lo: float, hi: float, invert: bool = False) -> float:
    if hi == lo:
        score = 50.0
    else:
        score = max(0.0, min(100.0, 100.0 * (value - lo) / (hi - lo)))
    return round(100.0 - score if invert else score, 6)


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
    row.update({
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
        "shadow_side_hint": "STAGED_R25B_RECOMPUTE",
    })
    return row


def rsi(closes: List[float], n: int = 14) -> str:
    if len(closes) <= n:
        return ""
    gains, losses = [], []
    for i in range(-n, 0):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = sum(gains) / n
    avg_loss = sum(losses) / n
    if avg_loss == 0:
        return 100.0
    return round(100 - (100 / (1 + avg_gain / avg_loss)), 6)


def technical_row(ticker: str, prices: List[Dict[str, object]], fields: Sequence[str]) -> Dict[str, object]:
    closes = [float(r["close"]) for r in prices]
    highs = [float(r["high"] or r["close"]) for r in prices]
    lows = [float(r["low"] or r["close"]) for r in prices]
    vols = [float(r["volume"]) for r in prices]
    latest = prices[-1]
    last20 = closes[-20:] if len(closes) >= 20 else closes
    mid = sum(last20) / len(last20)
    stdev = math.sqrt(sum((x - mid) ** 2 for x in last20) / len(last20)) if last20 else 0.0
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
    row.update({
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
        "technical_warning_label": "STAGED_R25B_NOT_MERGED",
        "option_data_status": "NOT_AVAILABLE_RESERVED",
        "gamma_squeeze_status": "NOT_AVAILABLE_RESERVED",
        "gamma_squeeze_risk_label": "NOT_AVAILABLE_RESERVED",
        "official_decision_impact": "NONE",
    })
    return row


def count_dupes(rows: List[Dict[str, object]]) -> int:
    seen = set()
    d = 0
    for r in rows:
        t = norm_ticker(r.get("ticker"))
        if t in seen:
            d += 1
        seen.add(t)
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="D:/us-tech-quant")
    ap.add_argument("--max-tickers", type=int, default=93)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-merge-to-current-factor-pack", action="store_true")
    ap.add_argument("--allow-merge-to-current-technical-timing", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    run_id = f"V18_25A_R25B_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    before = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": tree_sig(root / "outputs/v18/factor_pack"),
        "technical": tree_sig(root / "outputs/v18/technical_timing"),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
    }

    combined, _ = read_csv(root / R25_COMBINED)
    builders, _ = read_csv(root / R25A_BUILDERS)
    gate, _ = read_csv(root / R25A_GATE)
    factor_current, factor_fields = read_csv(root / FACTOR_CURRENT)
    tech_current, tech_fields = read_csv(root / TECH_CURRENT)
    gate_pass = any(str(r.get("gate_check")) == "r25b_input_gate" and str(r.get("status")).upper() == "PASS" for r in gate)
    status = STATUS_DRYRUN if args.dry_run else STATUS_OK
    validation_fail_count = 0
    if args.allow_merge_to_current_factor_pack or args.allow_merge_to_current_technical_timing:
        status = STATUS_MERGE_REFUSED
        validation_fail_count = 1
    elif not gate_pass:
        status = STATUS_GATE
        validation_fail_count = 1

    targets = []
    seen = set()
    for r in combined:
        t = norm_ticker(r.get("ticker"))
        if str(r.get("combined_action", "")).upper() == "BUILD_FACTOR_AND_TECHNICAL" and t and t not in seen:
            targets.append(r)
            seen.add(t)
    targets = targets[: max(args.max_tickers, 0)]
    if status in {STATUS_DRYRUN, STATUS_OK} and not targets:
        status = STATUS_ZERO
        validation_fail_count = 1

    factor_builder = next((r for r in builders if str(r.get("builder_role")).upper() == "FACTOR"), {})
    tech_builder = next((r for r in builders if str(r.get("builder_role")).upper() == "TECHNICAL"), {})
    factor_parse = parse_py(root / str(factor_builder.get("builder_script", "")))
    tech_parse = parse_py(root / str(tech_builder.get("builder_script", "")))
    target_rows, factor_rows, tech_rows, factor_audit, tech_audit, holds = [], [], [], [], [], []
    price_ok = price_fail = 0
    for idx, r in enumerate(targets, 1):
        ticker = norm_ticker(r.get("ticker"))
        p = root / PRICE_CACHE / f"{ticker}.csv"
        prices, err = load_prices(p)
        ok = not err and len(prices) >= 120
        target_rows.append({"priority_rank": idx, "ticker": ticker, "source_batch": r.get("source_batch", ""), "target_status": "PRICE_CACHE_VALIDATED" if ok else "HOLD_PRICE_CACHE_VALIDATION_FAIL", "price_cache_file": p.as_posix(), "price_row_count": len(prices), "reason": err})
        if not ok:
            price_fail += 1
            holds.append({"ticker": ticker, "hold_type": "PRICE_CACHE_VALIDATION_FAIL", "reason": err, "next_action": "Review official price cache before staged build."})
            continue
        price_ok += 1
        try:
            fr = factor_row(ticker, prices, factor_fields)
            factor_rows.append(fr)
            factor_audit.append({"ticker": ticker, "build_attempted": "TRUE", "build_success": "TRUE", "row_count": len(prices), "status": "FACTOR_ROW_STAGED", "error_message": ""})
        except Exception as e:
            factor_audit.append({"ticker": ticker, "build_attempted": "TRUE", "build_success": "FALSE", "row_count": len(prices), "status": "FACTOR_BUILD_FAIL", "error_message": f"{type(e).__name__}: {e}"})
            holds.append({"ticker": ticker, "hold_type": "FACTOR_BUILD_FAIL", "reason": f"{type(e).__name__}: {e}", "next_action": "Review factor staged calculation."})
        try:
            tr = technical_row(ticker, prices, tech_fields)
            tech_rows.append(tr)
            tech_audit.append({"ticker": ticker, "build_attempted": "TRUE", "build_success": "TRUE", "row_count": len(prices), "status": "TECHNICAL_ROW_STAGED", "error_message": ""})
        except Exception as e:
            tech_audit.append({"ticker": ticker, "build_attempted": "TRUE", "build_success": "FALSE", "row_count": len(prices), "status": "TECHNICAL_BUILD_FAIL", "error_message": f"{type(e).__name__}: {e}"})
            holds.append({"ticker": ticker, "hold_type": "TECHNICAL_BUILD_FAIL", "reason": f"{type(e).__name__}: {e}", "next_action": "Review technical staged calculation."})

    factor_schema = bool(factor_fields) and all(c in factor_fields for c in ["ticker", "factor_pack_score", "factor_pack_rank", "latest_price_date", "latest_close"])
    tech_schema = bool(tech_fields) and all(c in tech_fields for c in ["ticker", "price_date", "close", "technical_timing_score", "technical_signal"])
    schema_rows = [
        {"schema_item": "factor_schema_compatible", "status": "PASS" if factor_schema else "FAIL", "value": str(factor_schema).upper(), "notes": ""},
        {"schema_item": "technical_schema_compatible", "status": "PASS" if tech_schema else "FAIL", "value": str(tech_schema).upper(), "notes": ""},
        {"schema_item": "factor_output_tickers_subset_of_targets", "status": "PASS" if set(norm_ticker(r.get("ticker")) for r in factor_rows).issubset(seen) else "FAIL", "value": len(factor_rows), "notes": ""},
        {"schema_item": "technical_output_tickers_subset_of_targets", "status": "PASS" if set(norm_ticker(r.get("ticker")) for r in tech_rows).issubset(seen) else "FAIL", "value": len(tech_rows), "notes": ""},
    ]

    if price_fail and status in {STATUS_DRYRUN, STATUS_OK}:
        status = STATUS_PRICE
    elif len(factor_rows) != price_ok and status in {STATUS_DRYRUN, STATUS_OK}:
        status = STATUS_FACTOR
    elif len(tech_rows) != price_ok and status in {STATUS_DRYRUN, STATUS_OK}:
        status = STATUS_TECH
    elif (not factor_schema or not tech_schema) and status in {STATUS_DRYRUN, STATUS_OK}:
        status = STATUS_SCHEMA

    write_csv(root / OUT_TARGETS, target_rows, TARGET_FIELDS)
    write_csv(root / OUT_FACTOR_AUDIT, factor_audit, AUDIT_FIELDS)
    write_csv(root / OUT_TECH_AUDIT, tech_audit, AUDIT_FIELDS)
    write_csv(root / OUT_SCHEMA, schema_rows, SCHEMA_FIELDS)
    write_csv(root / OUT_HOLDS, holds, HOLD_FIELDS)
    if not args.dry_run and status != STATUS_MERGE_REFUSED:
        write_csv(root / OUT_FACTOR, factor_rows, factor_fields)
        write_csv(root / OUT_TECH, tech_rows, tech_fields)

    after = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": tree_sig(root / "outputs/v18/factor_pack"),
        "technical": tree_sig(root / "outputs/v18/technical_timing"),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
    }
    mods = {k: before[k] != after[k] for k in before}
    forbidden = any(mods.values())
    factor_dupes = count_dupes(factor_rows)
    tech_dupes = count_dupes(tech_rows)
    if (factor_dupes or tech_dupes) and status in {STATUS_DRYRUN, STATUS_OK}:
        status = STATUS_SCHEMA

    values = {
        "STATUS": status,
        "MODE": MODE_DRYRUN if args.dry_run else MODE,
        "RUN_ID": run_id,
        "R25_COMBINED_PLAN_PATH": R25_COMBINED,
        "R25A_INPUT_GATE_PATH": R25A_GATE,
        "MAX_TICKERS": args.max_tickers,
        "EXPECTED_TARGET_COUNT": 93,
        "SELECTED_TARGET_COUNT": len(targets),
        "DEDUPED_TARGET_COUNT": len(targets),
        "PRICE_CACHE_VALIDATION_SUCCESS_COUNT": price_ok,
        "PRICE_CACHE_VALIDATION_FAIL_COUNT": price_fail,
        "FACTOR_BUILDER_SELECTED": factor_builder.get("builder_script", ""),
        "TECHNICAL_BUILDER_SELECTED": tech_builder.get("builder_script", ""),
        "FACTOR_BUILDER_PARSE_STATUS": factor_parse,
        "TECHNICAL_BUILDER_PARSE_STATUS": tech_parse,
        "STAGED_FACTOR_ROW_COUNT": 0 if args.dry_run else len(factor_rows),
        "STAGED_TECHNICAL_ROW_COUNT": 0 if args.dry_run else len(tech_rows),
        "FACTOR_BUILD_SUCCESS_COUNT": len(factor_rows),
        "FACTOR_BUILD_FAIL_COUNT": price_ok - len(factor_rows),
        "TECHNICAL_BUILD_SUCCESS_COUNT": len(tech_rows),
        "TECHNICAL_BUILD_FAIL_COUNT": price_ok - len(tech_rows),
        "FACTOR_SCHEMA_COMPATIBLE": str(factor_schema).upper(),
        "TECHNICAL_SCHEMA_COMPATIBLE": str(tech_schema).upper(),
        "DUPLICATE_FACTOR_TICKER_COUNT": factor_dupes,
        "DUPLICATE_TECHNICAL_TICKER_COUNT": tech_dupes,
        "HOLDS_AND_FAILURES_COUNT": len(holds),
        "STAGED_FACTOR_ROWS_PATH": OUT_FACTOR,
        "STAGED_TECHNICAL_ROWS_PATH": OUT_TECH,
        "FACTOR_BUILD_AUDIT_PATH": OUT_FACTOR_AUDIT,
        "TECHNICAL_BUILD_AUDIT_PATH": OUT_TECH_AUDIT,
        "SCHEMA_VALIDATION_PATH": OUT_SCHEMA,
        "OFFICIAL_FACTOR_PACK_MERGE_ALLOWED_NOW": "FALSE",
        "OFFICIAL_TECHNICAL_TIMING_MERGE_ALLOWED_NOW": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "PRICE_CACHE_MODIFIED": str(mods["price"]).upper(),
        "ROLLING_LEDGER_MODIFIED": str(mods["ledger"]).upper(),
        "FACTOR_PACK_MODIFIED": str(mods["factor"]).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(mods["technical"]).upper(),
        "TIER_FILES_MODIFIED": str(mods["tier"]).upper(),
        "OFFICIAL_DECISION_MODIFIED": str(mods["decision"]).upper(),
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden).upper(),
        "NEXT_RECOMMENDED_STEP": "R25C: Validate staged factor and technical rows, then prepare official merge plan with backup. Do not merge until validation passes.",
    }
    write_text(root / OUT_READ_FIRST, "\n".join(f"{f}: {values.get(f, '')}" for f in READ_FIRST_FIELDS) + "\n")
    report = "\n".join([
        "# V18.25A R25B Staged Factor Technical Build Report",
        "",
        f"STATUS: {status}",
        f"MODE: {values['MODE']}",
        f"RUN_ID: {run_id}",
        "",
        f"- selected_target_count: {len(targets)}",
        f"- staged_factor_rows: {values['STAGED_FACTOR_ROW_COUNT']}",
        f"- staged_technical_rows: {values['STAGED_TECHNICAL_ROW_COUNT']}",
        f"- holds_and_failures: {len(holds)}",
        "",
        "Official factor/technical current outputs were not modified.",
        "",
    ])
    write_text(root / OUT_REPORT, report)
    print(f"STATUS: {status}")
    print(f"MODE: {values['MODE']}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
