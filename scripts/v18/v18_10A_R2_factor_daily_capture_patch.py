from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def norm(s: str) -> str:
    return str(s or "").strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def to_float(x) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if s == "" or s.lower() in ("nan", "none", "null"):
        return None
    pct = s.endswith("%")
    if pct:
        s = s[:-1]
    try:
        v = float(s)
        return v / 100.0 if pct else v
    except Exception:
        return None


def fmt_float(x: Optional[float], digits: int = 6) -> str:
    if x is None:
        return ""
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return ""
    return f"{x:.{digits}f}"


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    return rows, fields


def write_csv(path: Path, rows: List[Dict[str, str]], fields: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def find_col(fields: List[str], names: List[str]) -> Optional[str]:
    nmap = {norm(f): f for f in fields}
    for name in names:
        if norm(name) in nmap:
            return nmap[norm(name)]
    for name in names:
        nn = norm(name)
        for f in fields:
            nf = norm(f)
            if nn and nn in nf:
                return f
    return None


def add_fields(fields: List[str], new_fields: List[str]) -> List[str]:
    out = list(fields)
    existing = {norm(f) for f in out}
    for f in new_fields:
        if norm(f) not in existing:
            out.append(f)
            existing.add(norm(f))
    return out


def candidate_tracker_paths(root: Path) -> List[Path]:
    paths = [
        root / "state/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv",
    ]
    return [p for p in paths if p.exists()]


def detect_ticker_col(fields: List[str]) -> Optional[str]:
    return find_col(fields, ["ticker", "symbol", "asset", "name"])


def detect_price_col(fields: List[str]) -> Optional[str]:
    return find_col(fields, [
        "latest_close",
        "close",
        "last_close",
        "price",
        "last_price",
        "snapshot_price",
        "current_price",
        "adj_close",
    ])


def detect_existing_return_cols(fields: List[str]) -> Dict[int, Optional[str]]:
    return {
        20: find_col(fields, ["return_20d", "ret_20d", "ticker_return_20d", "asset_return_20d", "r20d", "pct_change_20d"]),
        60: find_col(fields, ["return_60d", "ret_60d", "ticker_return_60d", "asset_return_60d", "r60d", "pct_change_60d"]),
        120: find_col(fields, ["return_120d", "ret_120d", "ticker_return_120d", "asset_return_120d", "r120d", "pct_change_120d"]),
    }


def detect_existing_benchmark_cols(fields: List[str]) -> Dict[int, Optional[str]]:
    return {
        20: find_col(fields, ["benchmark_return_20d", "bench_return_20d", "benchmark_ret_20d", "qqq_return_20d", "qqq_ret_20d"]),
        60: find_col(fields, ["benchmark_return_60d", "bench_return_60d", "benchmark_ret_60d", "qqq_return_60d", "qqq_ret_60d"]),
        120: find_col(fields, ["benchmark_return_120d", "bench_return_120d", "benchmark_ret_120d", "qqq_return_120d", "qqq_ret_120d"]),
    }


def percentile_scores(values: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    valid = [(k, v) for k, v in values.items() if v is not None and not math.isnan(v)]
    if not valid:
        return {k: None for k in values}
    if len(valid) == 1:
        return {k: (50.0 if values[k] is not None else None) for k in values}

    sorted_vals = sorted(valid, key=lambda kv: kv[1])
    scores: Dict[str, Optional[float]] = {k: None for k in values}

    for i, (k, v) in enumerate(sorted_vals):
        same = [j for j, (_, vv) in enumerate(sorted_vals) if vv == v]
        avg_rank = sum(same) / len(same)
        scores[k] = 100.0 * avg_rank / (len(sorted_vals) - 1)

    return scores


def compute_returns_from_series(series, windows=(20, 60, 120)) -> Dict[int, Optional[float]]:
    out: Dict[int, Optional[float]] = {}
    try:
        s = series.dropna()
        if len(s) < 2:
            return {w: None for w in windows}
        last = float(s.iloc[-1])
        for w in windows:
            if len(s) > w:
                base = float(s.iloc[-(w + 1)])
                out[w] = (last / base - 1.0) if base else None
            else:
                out[w] = None
    except Exception:
        out = {w: None for w in windows}
    return out


def yfinance_return_map(tickers: List[str], benchmark: str = "QQQ") -> Tuple[Dict[str, Dict[int, Optional[float]]], str]:
    try:
        import yfinance as yf
    except Exception as e:
        return {}, f"YFINANCE_IMPORT_FAILED: {e}"

    unique = []
    for t in tickers + [benchmark]:
        tt = str(t or "").strip().upper()
        if tt and tt not in unique:
            unique.append(tt)

    if not unique:
        return {}, "NO_TICKERS"

    try:
        data = yf.download(
            tickers=unique,
            period="9mo",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=True,
        )
    except Exception as e:
        return {}, f"YFINANCE_DOWNLOAD_FAILED: {e}"

    out: Dict[str, Dict[int, Optional[float]]] = {}

    try:
        import pandas as pd  # noqa
        if hasattr(data.columns, "levels") and len(data.columns.levels) >= 2:
            for t in unique:
                close = None
                for close_name in ["Close", "Adj Close"]:
                    if (t, close_name) in data.columns:
                        close = data[(t, close_name)]
                        break
                if close is not None:
                    out[t] = compute_returns_from_series(close)
        else:
            # Single ticker fallback
            close = None
            for close_name in ["Close", "Adj Close"]:
                if close_name in data.columns:
                    close = data[close_name]
                    break
            if close is not None and len(unique) == 1:
                out[unique[0]] = compute_returns_from_series(close)
    except Exception as e:
        return out, f"YFINANCE_PARSE_PARTIAL_OR_FAILED: {e}"

    return out, "YFINANCE_OK"


def existing_relative_raw(row: Dict[str, str], asset_cols: Dict[int, Optional[str]], bench_cols: Dict[int, Optional[str]]) -> Tuple[Optional[float], str]:
    weights = {20: 0.50, 60: 0.30, 120: 0.20}
    total = 0.0
    used = 0.0
    parts = []

    for w, wt in weights.items():
        ac = asset_cols.get(w)
        bc = bench_cols.get(w)
        if not ac or not bc:
            continue
        av = to_float(row.get(ac))
        bv = to_float(row.get(bc))
        if av is None or bv is None:
            continue
        total += wt * (av - bv)
        used += wt
        parts.append(f"{w}d:{ac}-{bc}")

    if used <= 0:
        return None, "NO_EXPLICIT_ASSET_AND_BENCHMARK_RETURN_COLUMNS"

    return total / used, "EXISTING_COLUMNS_" + ",".join(parts)


def find_account_cash_usd(root: Path, fallback: float) -> Tuple[float, str]:
    paths = [
        root / "state/v18/simulation/V18_CURRENT_SIM_ACCOUNT.csv",
        root / "outputs/v18/simulation/V18_CURRENT_SIM_ACCOUNT.csv",
        root / "state/v18/simulation/V18_CURRENT_PAPER_ACCOUNT.csv",
        root / "outputs/v18/simulation/V18_CURRENT_PAPER_ACCOUNT.csv",
    ]
    cash_names = ["cash_usd", "CASH_USD", "cash", "available_cash_usd", "available_cash"]

    for p in paths:
        rows, fields = read_csv(p)
        if not rows:
            continue
        col = find_col(fields, cash_names)
        if not col:
            continue
        v = to_float(rows[0].get(col))
        if v is not None:
            return v, str(p)

    return fallback, "PARAM_OR_DEFAULT_CASH_USD"


def execution_score(price: Optional[float], cash_usd: float, price_buffer_pct: float, max_single_order_cash_pct: float) -> Tuple[Optional[float], str, Optional[float], Optional[float]]:
    if price is None or price <= 0:
        return None, "MISSING_PRICE", None, None

    required = price * (1.0 + price_buffer_pct)
    concentration = required / cash_usd if cash_usd > 0 else None

    if cash_usd <= 0:
        return 0.0, "NO_CASH_INPUT", required, concentration

    if required > cash_usd:
        return 0.0, "NOT_BUYABLE_ONE_SHARE", required, concentration

    if concentration is None:
        return None, "MISSING_CONCENTRATION", required, concentration

    if concentration <= 0.20:
        score = 100.0
    elif concentration <= 0.30:
        score = 80.0
    elif concentration <= max_single_order_cash_pct:
        score = 60.0
    elif concentration <= 0.50:
        score = 40.0
    elif concentration <= 0.75:
        score = 20.0
    else:
        score = 10.0

    return score, "EXECUTION_SCORE_ONE_SHARE_CASH_BUFFER_FORMULA", required, concentration


def patch_file(
    path: Path,
    root: Path,
    use_yfinance: bool,
    cash_usd: float,
    cash_source: str,
    price_buffer_pct: float,
    max_single_order_cash_pct: float,
    default_benchmark: str,
    run_stamp: str,
) -> Dict[str, str]:
    rows, fields = read_csv(path)

    result = {
        "path": str(path),
        "rows": str(len(rows)),
        "status": "SKIPPED_EMPTY",
        "ticker_col": "",
        "price_col": "",
        "relative_strength_populated": "0",
        "execution_fit_populated": "0",
        "backup": "",
        "note": "",
    }

    if not rows:
        return result

    ticker_col = detect_ticker_col(fields)
    price_col = detect_price_col(fields)
    asset_cols = detect_existing_return_cols(fields)
    bench_cols = detect_existing_benchmark_cols(fields)

    result["ticker_col"] = ticker_col or ""
    result["price_col"] = price_col or ""

    new_fields = [
        "relative_strength_score",
        "relative_strength_raw",
        "relative_strength_benchmark",
        "relative_strength_method",
        "relative_strength_status",
        "relative_strength_return_20d",
        "relative_strength_benchmark_return_20d",
        "relative_strength_return_60d",
        "relative_strength_benchmark_return_60d",
        "relative_strength_return_120d",
        "relative_strength_benchmark_return_120d",
        "execution_fit",
        "execution_fit_score",
        "execution_fit_status",
        "execution_cash_usd",
        "execution_cash_source",
        "execution_price_used",
        "execution_required_cash_usd",
        "execution_concentration_pct",
        "execution_price_buffer_pct",
        "execution_max_single_order_cash_pct",
        "factor_capture_version",
        "factor_capture_timestamp",
    ]
    out_fields = add_fields(fields, new_fields)

    tickers: List[str] = []
    for r in rows:
        t = str(r.get(ticker_col, "") if ticker_col else "").strip().upper()
        if t and t not in tickers:
            tickers.append(t)

    yf_map: Dict[str, Dict[int, Optional[float]]] = {}
    yf_status = "YFINANCE_NOT_USED"
    if use_yfinance and tickers:
        yf_map, yf_status = yfinance_return_map(tickers, default_benchmark)

    bench_returns = yf_map.get(default_benchmark.upper(), {})

    raw_by_row_id: Dict[str, Optional[float]] = {}
    tmp_raw: List[Optional[float]] = []
    tmp_method: List[str] = []
    tmp_returns: List[Dict[int, Optional[float]]] = []

    for idx, r in enumerate(rows):
        t = str(r.get(ticker_col, "") if ticker_col else "").strip().upper()
        raw = None
        method = ""

        ret_map: Dict[int, Optional[float]] = {20: None, 60: None, 120: None}

        if use_yfinance and t in yf_map and bench_returns:
            ticker_returns = yf_map.get(t, {})
            weights = {20: 0.50, 60: 0.30, 120: 0.20}
            total = 0.0
            used = 0.0
            for w, wt in weights.items():
                tv = ticker_returns.get(w)
                bv = bench_returns.get(w)
                ret_map[w] = tv
                if tv is not None and bv is not None:
                    total += wt * (tv - bv)
                    used += wt
            if used > 0:
                raw = total / used
                method = f"YFINANCE_WEIGHTED_RELATIVE_RETURN_VS_{default_benchmark.upper()}_20D50_60D30_120D20"
            else:
                method = f"YFINANCE_INSUFFICIENT_RETURN_WINDOW: {yf_status}"
        else:
            raw, method = existing_relative_raw(r, asset_cols, bench_cols)

        raw_by_row_id[str(idx)] = raw
        tmp_raw.append(raw)
        tmp_method.append(method)
        tmp_returns.append(ret_map)

    score_map = percentile_scores(raw_by_row_id)

    rel_count = 0
    exe_count = 0

    for idx, r in enumerate(rows):
        raw = tmp_raw[idx]
        score = score_map.get(str(idx))
        method = tmp_method[idx]
        ret_map = tmp_returns[idx]

        if raw is not None:
            r["relative_strength_raw"] = fmt_float(raw, 8)
            r["relative_strength_score"] = fmt_float(score, 4)
            r["relative_strength_status"] = "OK_CAPTURED"
            rel_count += 1
        else:
            r["relative_strength_raw"] = ""
            r["relative_strength_score"] = ""
            r["relative_strength_status"] = "MISSING_INPUT"

        r["relative_strength_benchmark"] = default_benchmark.upper()
        r["relative_strength_method"] = method
        r["relative_strength_return_20d"] = fmt_float(ret_map.get(20), 8)
        r["relative_strength_benchmark_return_20d"] = fmt_float(bench_returns.get(20), 8)
        r["relative_strength_return_60d"] = fmt_float(ret_map.get(60), 8)
        r["relative_strength_benchmark_return_60d"] = fmt_float(bench_returns.get(60), 8)
        r["relative_strength_return_120d"] = fmt_float(ret_map.get(120), 8)
        r["relative_strength_benchmark_return_120d"] = fmt_float(bench_returns.get(120), 8)

        price = to_float(r.get(price_col)) if price_col else None
        escore, estatus, required, concentration = execution_score(
            price=price,
            cash_usd=cash_usd,
            price_buffer_pct=price_buffer_pct,
            max_single_order_cash_pct=max_single_order_cash_pct,
        )

        if escore is not None:
            r["execution_fit"] = fmt_float(escore, 4)
            r["execution_fit_score"] = fmt_float(escore, 4)
            exe_count += 1
        else:
            r["execution_fit"] = ""
            r["execution_fit_score"] = ""

        r["execution_fit_status"] = estatus
        r["execution_cash_usd"] = fmt_float(cash_usd, 4)
        r["execution_cash_source"] = cash_source
        r["execution_price_used"] = fmt_float(price, 6)
        r["execution_required_cash_usd"] = fmt_float(required, 6)
        r["execution_concentration_pct"] = fmt_float(concentration, 6)
        r["execution_price_buffer_pct"] = fmt_float(price_buffer_pct, 6)
        r["execution_max_single_order_cash_pct"] = fmt_float(max_single_order_cash_pct, 6)
        r["factor_capture_version"] = "V18.10A-R2"
        r["factor_capture_timestamp"] = now_text()

    backup = path.with_suffix(path.suffix + f".before_v18_10A_R2_factor_capture_{run_stamp}.bak")
    shutil.copy2(path, backup)
    write_csv(path, rows, out_fields)

    result["status"] = "OK_PATCHED"
    result["relative_strength_populated"] = str(rel_count)
    result["execution_fit_populated"] = str(exe_count)
    result["backup"] = str(backup)
    result["note"] = yf_status
    return result


def write_audit(path: Path, rows: List[Dict[str, str]]) -> None:
    fields = [
        "path",
        "rows",
        "status",
        "ticker_col",
        "price_col",
        "relative_strength_populated",
        "execution_fit_populated",
        "backup",
        "note",
    ]
    write_csv(path, rows, fields)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"D:\us-tech-quant")
    ap.add_argument("--use-yfinance", action="store_true")
    ap.add_argument("--cash-usd", type=float, default=2000.0)
    ap.add_argument("--price-buffer-pct", type=float, default=0.02)
    ap.add_argument("--max-single-order-cash-pct", type=float, default=0.40)
    ap.add_argument("--default-benchmark", default="QQQ")
    args = ap.parse_args()

    root = Path(args.root)
    run_stamp = stamp()

    out_dir = root / "outputs/v18/factor_registry"
    ensure_dir(out_dir)

    audit_path = out_dir / "V18_10A_R2_CURRENT_FACTOR_DAILY_CAPTURE_PATCH_AUDIT.csv"
    report_path = out_dir / "V18_10A_R2_CURRENT_FACTOR_DAILY_CAPTURE_PATCH_REPORT.md"
    read_first_path = out_dir / "V18_10A_R2_READ_FIRST.txt"

    cash_usd, cash_source = find_account_cash_usd(root, args.cash_usd)

    paths = candidate_tracker_paths(root)
    audit_rows: List[Dict[str, str]] = []

    for p in paths:
        audit_rows.append(
            patch_file(
                path=p,
                root=root,
                use_yfinance=args.use_yfinance,
                cash_usd=cash_usd,
                cash_source=cash_source,
                price_buffer_pct=args.price_buffer_pct,
                max_single_order_cash_pct=args.max_single_order_cash_pct,
                default_benchmark=args.default_benchmark,
                run_stamp=run_stamp,
            )
        )

    write_audit(audit_path, audit_rows)

    patched = sum(1 for r in audit_rows if r["status"] == "OK_PATCHED")
    rel_total = sum(int(r.get("relative_strength_populated", "0") or "0") for r in audit_rows)
    exe_total = sum(int(r.get("execution_fit_populated", "0") or "0") for r in audit_rows)

    report = []
    report.append("# V18.10A-R2 Factor Daily Capture Patch")
    report.append("")
    report.append(f"Generated: `{now_text()}`")
    report.append("")
    report.append("## 1. Status")
    report.append("")
    report.append("- STATUS: `OK_FACTOR_DAILY_CAPTURE_PATCH_READY`")
    report.append("- MODE: `NO_BLACK_BOX_FACTOR_CAPTURE`")
    report.append("- OFFICIAL_DECISION_IMPACT: `NONE`")
    report.append("- AUTO_WEIGHT_CHANGE: `DISABLED`")
    report.append("- AUTO_TRADE: `DISABLED`")
    report.append("")
    report.append("## 2. Formula disclosure")
    report.append("")
    report.append("### relative_strength_score")
    report.append("")
    report.append(f"- Benchmark: `{args.default_benchmark.upper()}`")
    report.append("- Raw score formula when yfinance is enabled:")
    report.append("")
    report.append("```text")
    report.append("relative_strength_raw =")
    report.append("  0.50 * (ticker_return_20d - benchmark_return_20d)")
    report.append("+ 0.30 * (ticker_return_60d - benchmark_return_60d)")
    report.append("+ 0.20 * (ticker_return_120d - benchmark_return_120d)")
    report.append("")
    report.append("relative_strength_score = cross-sectional percentile of relative_strength_raw among current candidates")
    report.append("```")
    report.append("")
    report.append("If yfinance is not used and explicit asset/benchmark return columns are missing, the field is created but marked `MISSING_INPUT`.")
    report.append("")
    report.append("### execution_fit")
    report.append("")
    report.append("```text")
    report.append("required_cash_usd = latest_close * (1 + price_buffer_pct)")
    report.append("concentration_pct = required_cash_usd / cash_usd")
    report.append("")
    report.append("if required_cash_usd > cash_usd: execution_fit = 0")
    report.append("elif concentration_pct <= 20%: execution_fit = 100")
    report.append("elif concentration_pct <= 30%: execution_fit = 80")
    report.append("elif concentration_pct <= max_single_order_cash_pct: execution_fit = 60")
    report.append("elif concentration_pct <= 50%: execution_fit = 40")
    report.append("elif concentration_pct <= 75%: execution_fit = 20")
    report.append("else: execution_fit = 10")
    report.append("```")
    report.append("")
    report.append("## 3. Summary")
    report.append("")
    report.append(f"- FILES_FOUND: `{len(paths)}`")
    report.append(f"- FILES_PATCHED: `{patched}`")
    report.append(f"- RELATIVE_STRENGTH_POPULATED_TOTAL: `{rel_total}`")
    report.append(f"- EXECUTION_FIT_POPULATED_TOTAL: `{exe_total}`")
    report.append(f"- USE_YFINANCE: `{args.use_yfinance}`")
    report.append(f"- CASH_USD: `{cash_usd:.4f}`")
    report.append(f"- CASH_SOURCE: `{cash_source}`")
    report.append(f"- PRICE_BUFFER_PCT: `{args.price_buffer_pct}`")
    report.append(f"- MAX_SINGLE_ORDER_CASH_PCT: `{args.max_single_order_cash_pct}`")
    report.append("")
    report.append("## 4. Patched files")
    report.append("")
    report.append("| path | rows | status | relative_strength_populated | execution_fit_populated |")
    report.append("|---|---:|---|---:|---:|")
    for r in audit_rows:
        report.append(
            f"| {r['path']} | {r['rows']} | {r['status']} | "
            f"{r['relative_strength_populated']} | {r['execution_fit_populated']} |"
        )
    report.append("")
    report.append("## 5. Outputs")
    report.append("")
    report.append(f"- AUDIT: `{audit_path}`")
    report.append(f"- REPORT: `{report_path}`")
    report.append(f"- READ_FIRST: `{read_first_path}`")
    report.append("")
    report.append("## 6. Next step")
    report.append("")
    report.append("Run V18.10A coverage audit again. Expected improvement: official candidate captured count should become `7 / 7` if headers are now present.")
    report.append("")

    report_path.write_text("\n".join(report), encoding="utf-8")

    read_first = f"""V18.10A-R2 FACTOR DAILY CAPTURE PATCH READ FIRST

STATUS:
OK_FACTOR_DAILY_CAPTURE_PATCH_READY

MODE:
NO_BLACK_BOX_FACTOR_CAPTURE

OFFICIAL_DECISION_IMPACT:
NONE

AUTO_WEIGHT_CHANGE:
DISABLED

AUTO_TRADE:
DISABLED

FILES_FOUND:
{len(paths)}

FILES_PATCHED:
{patched}

RELATIVE_STRENGTH_POPULATED_TOTAL:
{rel_total}

EXECUTION_FIT_POPULATED_TOTAL:
{exe_total}

USE_YFINANCE:
{args.use_yfinance}

CASH_USD:
{cash_usd:.4f}

CASH_SOURCE:
{cash_source}

PRICE_BUFFER_PCT:
{args.price_buffer_pct}

MAX_SINGLE_ORDER_CASH_PCT:
{args.max_single_order_cash_pct}

AUDIT:
{audit_path}

REPORT:
{report_path}

READ_FIRST:
{read_first_path}

NEXT_STEP:
Run V18.10A coverage audit again:
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_10A_factor_registry_coverage_audit.ps1"
"""
    read_first_path.write_text(read_first, encoding="utf-8")

    print("")
    print("=== V18.10A-R2 FACTOR DAILY CAPTURE PATCH READY ===")
    print("STATUS: OK_FACTOR_DAILY_CAPTURE_PATCH_READY")
    print("MODE: NO_BLACK_BOX_FACTOR_CAPTURE")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print(f"FILES_FOUND: {len(paths)}")
    print(f"FILES_PATCHED: {patched}")
    print(f"RELATIVE_STRENGTH_POPULATED_TOTAL: {rel_total}")
    print(f"EXECUTION_FIT_POPULATED_TOTAL: {exe_total}")
    print(f"USE_YFINANCE: {args.use_yfinance}")
    print(f"CASH_USD: {cash_usd:.4f}")
    print(f"CASH_SOURCE: {cash_source}")
    print(f"AUDIT: {audit_path}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first_path}")
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
