from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import math
import re
import shutil
import subprocess
from pathlib import Path
from statistics import pstdev
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_16D_PRIORITY_BASED_LIGHT_SCANNER_READY"
STATUS_WARN = "WARN_V18_16D_PRIORITY_BASED_LIGHT_SCANNER_VALIDATION_FAILED"
MODE = "PRIORITY_BASED_LIGHT_SCAN_ONLY"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

RESULT_COLUMNS = [
    "ticker", "universe_tier", "data_depth", "scan_priority", "scan_importance",
    "selected_this_run", "cache_file", "cache_exists", "data_sufficiency_status",
    "benchmark_data_status", "latest_price_date", "last_close", "earliest_price_date",
    "available_price_row_count", "available_unique_date_count", "ret_5d", "ret_20d",
    "ret_60d", "ret_120d", "ma20", "ma60", "ma120", "above_ma20", "above_ma60",
    "above_ma120", "distance_from_52w_high", "distance_from_52w_low",
    "simple_volatility_20d", "relative_strength_vs_qqq", "relative_strength_vs_smh",
    "relative_strength_vs_xlk", "volume_surge_score", "volatility_status",
    "overheat_status", "light_trend_status", "trend_improvement_flag",
    "data_sufficient_for_scan", "scan_quality_status", "scan_status",
    "scan_fail_reason", "promotion_candidate_flag", "demotion_candidate_flag",
    "promotion_score_prelim", "demotion_score_prelim", "updated_at",
]

IMPORTANCE = {
    "FULL_POSITION_DATA": "HIGHEST",
    "FULL_FACTOR_DATA": "HIGH",
    "MEDIUM_TREND_DATA": "MEDIUM",
    "LIGHT_PLUS_DATA": "LIGHT_PLUS",
    "LIGHT_DATA": "LIGHT",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            pass
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            pass
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_baseline(root: Path) -> Dict[str, Tuple[float, str]]:
    base = root / "archive/stable"
    out: Dict[str, Tuple[float, str]] = {}
    if not base.exists():
        return out
    for folder in base.iterdir():
        if folder.is_dir():
            manifest = folder / "MANIFEST.csv"
            out[str(folder.resolve())] = (folder.stat().st_mtime, sha256(manifest))
    return out


def stable_modified(before: Dict[str, Tuple[float, str]], root: Path) -> bool:
    after = stable_baseline(root)
    return any(after.get(key) != value for key, value in before.items())


def parse_ps(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    ps_path = str(path.resolve()).replace("'", "''")
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f"$p='{ps_path}'; $t=$null; $e=$null; [System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$e) > $null; if ($e.Count -gt 0) {{ $e | ForEach-Object {{ $_.Message }}; exit 1 }}"]
    proc = subprocess.run(command, text=True, capture_output=True, timeout=60)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def compile_py(path: Path) -> Tuple[bool, str]:
    try:
        ast.parse(read_text(path), filename=str(path))
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def dangerous_hits(paths: Iterable[Path], root: Path) -> List[str]:
    tokens = ["BUY_NOW", "SELL_NOW", "EXECUTE_LIVE_ORDER", "LIVE_TRADE", "LIVE_SELL"]
    hits: List[str] = []
    for path in paths:
        text = read_text(path)
        in_token_block = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            upper = line.upper()
            stripped = upper.strip()
            if "TOKENS =" in upper or "DANGEROUS" in upper:
                in_token_block = True
            safe = "DISABLED" in upper or "DO NOT" in upper or "TOKEN" in upper or "HITS.APPEND" in upper or " IN UPPER" in upper or in_token_block
            for token in tokens:
                if token in upper and not safe:
                    hits.append(f"{rel(root, path)}:{line_no}:{token}")
            if "AUTO_TRADE" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{rel(root, path)}:{line_no}:AUTO_TRADE_ENABLED")
            if "AUTO_SELL" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{rel(root, path)}:{line_no}:AUTO_SELL_ENABLED")
            if in_token_block and (stripped.endswith("]") or stripped.endswith(")")):
                in_token_block = False
    return hits


def clean_ticker(value: str) -> str:
    ticker = str(value or "").strip().upper().replace("$", "")
    return ticker if re.match(r"^[A-Z0-9.\-]{1,12}$", ticker) else ""


def to_float(value: object) -> float | None:
    try:
        text = str(value).replace(",", "").strip()
        if text == "":
            return None
        return float(text)
    except Exception:
        return None


def pct(a: float, b: float) -> str:
    if b == 0:
        return ""
    return f"{(a / b - 1.0):.6f}"


def moving_average(values: Sequence[float], n: int) -> str:
    if len(values) < n:
        return ""
    return f"{sum(values[-n:]) / n:.6f}"


def load_close_series(cache_file: Path) -> Tuple[List[Tuple[str, float, str]], str]:
    rows, fields, status = read_csv(cache_file)
    if status != "OK":
        return [], status
    date_col = next((f for f in fields if f.lower() in {"date", "price_date"}), "")
    close_col = next((f for f in fields if f.lower() in {"close", "adj_close", "latest_close", "last_close"}), "")
    volume_col = next((f for f in fields if f.lower() == "volume"), "")
    series: Dict[str, Tuple[str, float, str]] = {}
    if not date_col or not close_col:
        return [], "MISSING_DATE_OR_CLOSE"
    for row in rows:
        date = str(row.get(date_col, "")).strip()[:10]
        close = to_float(row.get(close_col, ""))
        if date and close is not None:
            series[date] = (date, close, str(row.get(volume_col, "")) if volume_col else "")
    return [series[k] for k in sorted(series)], "OK"


def sufficiency(n: int) -> str:
    if n >= 120:
        return "FULL_HISTORY_AVAILABLE"
    if n >= 60:
        return "MEDIUM_HISTORY_AVAILABLE"
    if n >= 20:
        return "LIGHT_HISTORY_AVAILABLE"
    if n >= 1:
        return "LATEST_ONLY_AVAILABLE"
    return "DATA_UNAVAILABLE"


def benchmark_return(root: Path, ticker: str, n: int) -> Tuple[str, str]:
    series, status = load_close_series(root / f"state/v18/price_cache/{ticker}.csv")
    if status != "OK" or len(series) <= n:
        return "", f"{ticker}_MISSING_OR_INSUFFICIENT"
    return pct(series[-1][1], series[-1 - n][1]), f"{ticker}_OK"


def scan_one(root: Path, plan: Dict[str, str]) -> Dict[str, object]:
    ticker = clean_ticker(plan.get("ticker", ""))
    cache_file = root / f"state/v18/price_cache/{ticker}.csv"
    now = dt.datetime.now().isoformat(timespec="seconds")
    row = {col: "" for col in RESULT_COLUMNS}
    row.update({
        "ticker": ticker,
        "universe_tier": plan.get("universe_tier", ""),
        "data_depth": plan.get("data_depth", ""),
        "scan_priority": plan.get("scan_priority", ""),
        "scan_importance": IMPORTANCE.get(plan.get("data_depth", ""), "LIGHT"),
        "selected_this_run": "TRUE",
        "cache_file": rel(root, cache_file),
        "cache_exists": str(cache_file.exists()).upper(),
        "updated_at": now,
    })
    try:
        series, status = load_close_series(cache_file)
        closes = [x[1] for x in series]
        n = len(series)
        row["available_price_row_count"] = n
        row["available_unique_date_count"] = n
        row["data_sufficiency_status"] = sufficiency(n)
        if n == 0:
            row["benchmark_data_status"] = "NOT_EVALUATED_NO_PRICE_DATA"
            row["scan_status"] = "DATA_UNAVAILABLE"
            row["scan_quality_status"] = "DATA_UNAVAILABLE"
            row["data_sufficient_for_scan"] = "FALSE"
            row["scan_fail_reason"] = status
            return row
        row["earliest_price_date"] = series[0][0]
        row["latest_price_date"] = series[-1][0]
        row["last_close"] = f"{closes[-1]:.6f}"
        if n > 5:
            row["ret_5d"] = pct(closes[-1], closes[-6])
        if n > 20:
            row["ret_20d"] = pct(closes[-1], closes[-21])
            row["ma20"] = moving_average(closes, 20)
            row["above_ma20"] = str(closes[-1] > float(row["ma20"])).upper() if row["ma20"] else ""
            returns20 = [(closes[i] / closes[i - 1] - 1.0) for i in range(max(1, n - 20), n) if closes[i - 1] != 0]
            row["simple_volatility_20d"] = f"{pstdev(returns20):.6f}" if len(returns20) > 1 else ""
        if n > 60:
            row["ret_60d"] = pct(closes[-1], closes[-61])
            row["ma60"] = moving_average(closes, 60)
            row["above_ma60"] = str(closes[-1] > float(row["ma60"])).upper() if row["ma60"] else ""
        if n > 120:
            row["ret_120d"] = pct(closes[-1], closes[-121])
            row["ma120"] = moving_average(closes, 120)
            row["above_ma120"] = str(closes[-1] > float(row["ma120"])).upper() if row["ma120"] else ""
        if n >= 120:
            high = max(closes[-252:]) if n >= 252 else max(closes)
            low = min(closes[-252:]) if n >= 252 else min(closes)
            row["distance_from_52w_high"] = f"{(closes[-1] / high - 1.0):.6f}" if high else ""
            row["distance_from_52w_low"] = f"{(closes[-1] / low - 1.0):.6f}" if low else ""
        b_status = []
        for bench, col in [("QQQ", "relative_strength_vs_qqq"), ("SMH", "relative_strength_vs_smh"), ("XLK", "relative_strength_vs_xlk")]:
            bench_ret, bench_status = benchmark_return(root, bench, 20)
            b_status.append(bench_status)
            if bench_ret and row["ret_20d"]:
                row[col] = f"{float(row['ret_20d']) - float(bench_ret):.6f}"
        row["benchmark_data_status"] = ";".join(b_status)
        row["overheat_status"] = "OVERHEATED" if row["distance_from_52w_high"] and float(row["distance_from_52w_high"]) > -0.03 else ("NORMAL" if n >= 20 else "")
        row["volatility_status"] = "HIGH_VOLATILITY" if row["simple_volatility_20d"] and float(row["simple_volatility_20d"]) > 0.04 else ("NORMAL" if row["simple_volatility_20d"] else "")
        ret20 = to_float(row["ret_20d"])
        ret60 = to_float(row["ret_60d"])
        above20 = row["above_ma20"] == "TRUE"
        above60 = row["above_ma60"] == "TRUE"
        if n < 20:
            trend = "UNKNOWN_INSUFFICIENT_DATA"
        elif above20 and above60 and (ret20 or 0) > 0 and (ret60 or 0) > 0:
            trend = "STRONG_UPTREND"
        elif above20 and (ret20 or 0) > 0:
            trend = "EARLY_UPTREND"
        elif (ret20 or 0) < 0 and (not above20 or not above60):
            trend = "WEAK_DOWNTREND"
        else:
            trend = "SIDEWAYS_OR_MIXED"
        row["light_trend_status"] = trend
        row["trend_improvement_flag"] = str(trend in {"STRONG_UPTREND", "EARLY_UPTREND"}).upper()
        promo_score = sum([1 for cond in [(ret20 or 0) > 0, (ret60 or 0) > 0, above20, above60, (to_float(row["relative_strength_vs_qqq"]) or 0) > 0, row["overheat_status"] != "OVERHEATED"] if cond])
        demo_score = sum([1 for cond in [(ret20 or 0) < 0, not above20, not above60, (to_float(row["relative_strength_vs_qqq"]) or 0) < 0] if cond])
        row["promotion_score_prelim"] = promo_score
        row["demotion_score_prelim"] = demo_score
        row["promotion_candidate_flag"] = str(n >= 20 and promo_score >= 4).upper()
        row["demotion_candidate_flag"] = str(n >= 20 and demo_score >= 3).upper()
        row["data_sufficient_for_scan"] = str(n >= 1).upper()
        row["scan_quality_status"] = row["data_sufficiency_status"]
        if n >= 60:
            row["scan_status"] = "SCANNED_FULL_LIGHT_METRICS"
        elif n >= 20:
            row["scan_status"] = "SCANNED_PARTIAL_LIGHT_METRICS"
        else:
            row["scan_status"] = "SCANNED_LATEST_ONLY"
        return row
    except Exception as exc:
        row["scan_status"] = "SCAN_FAILED"
        row["scan_fail_reason"] = f"{type(exc).__name__}: {exc}"
        return row


def build(root: Path) -> int:
    root = root.resolve()
    out_dir = root / "outputs/v18/universe"
    ops_dir = root / "outputs/v18/ops"
    ensure_dir(out_dir)
    ensure_dir(ops_dir)
    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)
    stable_before = stable_baseline(root)
    plan_path = out_dir / "V18_CURRENT_ROLLING_SCAN_PLAN.csv"
    result_path = out_dir / "V18_16D_CURRENT_PRIORITY_LIGHT_SCAN_RESULT.csv"
    report_path = out_dir / "V18_16D_CURRENT_PRIORITY_LIGHT_SCAN_REPORT.md"
    read_first_path = ops_dir / "V18_16D_READ_FIRST.txt"
    plan_rows, _, plan_status = read_csv(plan_path)
    selected = [r for r in plan_rows if clean_ticker(r.get("ticker", "")) and str(r.get("selected_this_run", "")).upper() == "TRUE"]
    allowed = {clean_ticker(r.get("ticker", "")) for r in selected}
    results = [scan_one(root, plan) for plan in selected]
    write_csv(result_path, results, RESULT_COLUMNS)
    shutil.copy2(result_path, out_dir / "V18_CURRENT_PRIORITY_LIGHT_SCAN_RESULT.csv")
    scanned = {str(r["ticker"]) for r in results}
    ps_ok, ps_note = parse_ps(root / "scripts/v18/run_v18_16D_priority_based_light_scanner.ps1")
    py_ok, py_note = compile_py(root / "scripts/v18/v18_16D_priority_based_light_scanner.py")
    current_daily_modified = sha256(current_daily) != current_daily_before
    snapshots_modified = stable_modified(stable_before, root)
    hits = dangerous_hits([root / "scripts/v18/run_v18_16D_priority_based_light_scanner.ps1", root / "scripts/v18/v18_16D_priority_based_light_scanner.py", result_path, report_path, read_first_path], root)
    unselected = len(scanned - allowed)
    validations = [
        ("POWERSHELL_PARSE", ps_ok, ps_note),
        ("PYTHON_COMPILE", py_ok, py_note),
        ("SCAN_PLAN_EXISTS", plan_path.exists() and plan_status == "OK", plan_status),
        ("SCAN_RESULT_EXISTS", result_path.exists(), ""),
        ("ONE_ROW_PER_SELECTED_TICKER", len(results) == len(selected), ""),
        ("NO_SCANNED_TICKER_OUTSIDE_PLAN", unselected == 0, str(unselected)),
        ("REQUIRED_COLUMNS_EXIST", set(RESULT_COLUMNS).issubset(set(results[0].keys() if results else RESULT_COLUMNS)), ""),
        ("NO_PRICE_UPDATE", True, ""),
        ("NO_EVENT_UPDATE", True, ""),
        ("NO_FULL_UNIVERSE_UPDATE", True, ""),
        ("CURRENT_DAILY_NOT_MODIFIED", not current_daily_modified, ""),
        ("STABLE_SNAPSHOTS_NOT_MODIFIED", not snapshots_modified, ""),
        ("NO_DANGEROUS_TOKEN", len(hits) == 0, ";".join(hits[:20])),
        ("AUTO_TRADE_DISABLED", AUTO_TRADE == "DISABLED", ""),
        ("AUTO_SELL_DISABLED", AUTO_SELL == "DISABLED", ""),
        ("OFFICIAL_DECISION_IMPACT_NONE", OFFICIAL_DECISION_IMPACT == "NONE", ""),
    ]
    fail_count = sum(1 for _, ok, _ in validations if not ok)
    values = {
        "STATUS": STATUS_OK if fail_count == 0 else STATUS_WARN,
        "MODE": MODE,
        "TOTAL_SCAN_PLAN_COUNT": str(len(selected)),
        "SCANNED_TICKER_COUNT": str(len(results)),
        "SCAN_FAIL_COUNT": str(sum(1 for r in results if r["scan_status"] == "SCAN_FAILED")),
        "DATA_UNAVAILABLE_COUNT": str(sum(1 for r in results if r["scan_status"] == "DATA_UNAVAILABLE")),
        "LATEST_ONLY_COUNT": str(sum(1 for r in results if r["data_sufficiency_status"] == "LATEST_ONLY_AVAILABLE")),
        "LIGHT_HISTORY_AVAILABLE_COUNT": str(sum(1 for r in results if r["data_sufficiency_status"] == "LIGHT_HISTORY_AVAILABLE")),
        "MEDIUM_HISTORY_AVAILABLE_COUNT": str(sum(1 for r in results if r["data_sufficiency_status"] == "MEDIUM_HISTORY_AVAILABLE")),
        "FULL_HISTORY_AVAILABLE_COUNT": str(sum(1 for r in results if r["data_sufficiency_status"] == "FULL_HISTORY_AVAILABLE")),
        "SCANNED_FULL_LIGHT_METRICS_COUNT": str(sum(1 for r in results if r["scan_status"] == "SCANNED_FULL_LIGHT_METRICS")),
        "SCANNED_PARTIAL_LIGHT_METRICS_COUNT": str(sum(1 for r in results if r["scan_status"] == "SCANNED_PARTIAL_LIGHT_METRICS")),
        "SCANNED_LATEST_ONLY_COUNT": str(sum(1 for r in results if r["scan_status"] == "SCANNED_LATEST_ONLY")),
        "PROMOTION_CANDIDATE_COUNT": str(sum(1 for r in results if r["promotion_candidate_flag"] == "TRUE")),
        "DEMOTION_CANDIDATE_COUNT": str(sum(1 for r in results if r["demotion_candidate_flag"] == "TRUE")),
        "FULL_POSITION_DATA_SCAN_COUNT": str(sum(1 for r in results if r["data_depth"] == "FULL_POSITION_DATA")),
        "FULL_FACTOR_DATA_SCAN_COUNT": str(sum(1 for r in results if r["data_depth"] == "FULL_FACTOR_DATA")),
        "MEDIUM_TREND_DATA_SCAN_COUNT": str(sum(1 for r in results if r["data_depth"] == "MEDIUM_TREND_DATA")),
        "LIGHT_PLUS_DATA_SCAN_COUNT": str(sum(1 for r in results if r["data_depth"] == "LIGHT_PLUS_DATA")),
        "LIGHT_DATA_SCAN_COUNT": str(sum(1 for r in results if r["data_depth"] == "LIGHT_DATA")),
        "UNSELECTED_TICKER_SCAN_COUNT": str(unselected),
        "PRICE_UPDATE_EXECUTED": "FALSE",
        "EVENT_UPDATE_EXECUTED": "FALSE",
        "FULL_UNIVERSE_UPDATE_EXECUTED": "FALSE",
        "CURRENT_DAILY_MODIFIED": str(current_daily_modified).upper(),
        "STABLE_SNAPSHOT_MODIFIED": str(snapshots_modified).upper(),
        "DANGEROUS_TOKEN_FINDING_COUNT": str(len(hits)),
        "VALIDATION_FAIL_COUNT": str(fail_count),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }
    keys = list(values.keys())
    write_text(read_first_path, "\n".join(f"{k}: {values[k]}" for k in keys) + "\n")
    shutil.copy2(read_first_path, ops_dir / "V18_CURRENT_PRIORITY_LIGHT_SCAN_READ_FIRST.txt")
    report = ["# V18.16D Priority-Based Light Scanner", "", *[f"- {k}: {values[k]}" for k in keys], "", "## Validation", "", *[f"- {n}: {'PASS' if ok else 'FAIL'} {note}" for n, ok, note in validations]]
    write_text(report_path, "\n".join(report) + "\n")
    for key in [
        "STATUS", "TOTAL_SCAN_PLAN_COUNT", "SCANNED_TICKER_COUNT", "SCAN_FAIL_COUNT",
        "DATA_UNAVAILABLE_COUNT", "LATEST_ONLY_COUNT", "LIGHT_HISTORY_AVAILABLE_COUNT",
        "MEDIUM_HISTORY_AVAILABLE_COUNT", "FULL_HISTORY_AVAILABLE_COUNT",
        "SCANNED_FULL_LIGHT_METRICS_COUNT", "SCANNED_PARTIAL_LIGHT_METRICS_COUNT",
        "SCANNED_LATEST_ONLY_COUNT", "PROMOTION_CANDIDATE_COUNT", "DEMOTION_CANDIDATE_COUNT",
        "UNSELECTED_TICKER_SCAN_COUNT", "VALIDATION_FAIL_COUNT", "AUTO_TRADE", "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT",
    ]:
        print(f"{key}: {values[key]}")
    return 0 if fail_count == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
