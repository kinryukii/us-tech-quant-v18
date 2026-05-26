from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def norm(s: str) -> str:
    return str(s or "").strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    return rows, fields


def write_csv(path: Path, rows: List[Dict], fields: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def parse_float(x) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if s == "" or s.lower() in ("nan", "none", "null", "na", "n/a"):
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


def parse_return(x, field_name: str = "") -> Optional[float]:
    v = parse_float(x)
    if v is None:
        return None
    # If the column says pct/percent and value is 3.2, interpret as 3.2%.
    nf = norm(field_name)
    if ("pct" in nf or "percent" in nf) and abs(v) > 1.0:
        return v / 100.0
    # Extremely large forward returns are usually percentage points in CSVs.
    if abs(v) > 2.0:
        return v / 100.0
    return v


def parse_bool_or_float(x) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    if s == "":
        return None
    sl = s.lower()
    if sl in ("true", "t", "yes", "y", "1", "ok", "pass", "passed", "captured"):
        return 1.0
    if sl in ("false", "f", "no", "n", "0", "fail", "failed", "missing"):
        return 0.0
    return parse_float(s)


def fmt_num(x: Optional[float], digits: int = 6) -> str:
    if x is None:
        return ""
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return ""
    return f"{x:.{digits}f}"


def fmt_pct(x: Optional[float], digits: int = 4) -> str:
    if x is None:
        return ""
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return ""
    return f"{x * 100:.{digits}f}%"


def mean(xs: List[float]) -> Optional[float]:
    vals = [x for x in xs if x is not None and not math.isnan(x)]
    if not vals:
        return None
    return sum(vals) / len(vals)


def median(xs: List[float]) -> Optional[float]:
    vals = [x for x in xs if x is not None and not math.isnan(x)]
    if not vals:
        return None
    return statistics.median(vals)


def win_rate(xs: List[float]) -> Optional[float]:
    vals = [x for x in xs if x is not None and not math.isnan(x)]
    if not vals:
        return None
    return sum(1 for x in vals if x > 0) / len(vals)


def pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return None
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return cov / math.sqrt(vx * vy)


def rank_values(vals: List[float]) -> List[float]:
    pairs = sorted(enumerate(vals), key=lambda kv: kv[1])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][1] == pairs[i][1]:
            j += 1
        avg_rank = (i + j) / 2.0
        for k in range(i, j + 1):
            ranks[pairs[k][0]] = avg_rank
        i = j + 1
    return ranks


def spearman(xs: List[float], ys: List[float]) -> Optional[float]:
    if len(xs) < 3:
        return None
    return pearson(rank_values(xs), rank_values(ys))


def percentile_scores(raw_values: List[Optional[float]], lower_is_better: bool) -> List[Optional[float]]:
    valid = [(i, v) for i, v in enumerate(raw_values) if v is not None and not math.isnan(v)]
    out: List[Optional[float]] = [None] * len(raw_values)

    if not valid:
        return out

    if len(valid) == 1:
        out[valid[0][0]] = 50.0
        return out

    sorted_vals = sorted(valid, key=lambda kv: kv[1])
    i = 0
    while i < len(sorted_vals):
        j = i
        while j + 1 < len(sorted_vals) and sorted_vals[j + 1][1] == sorted_vals[i][1]:
            j += 1

        avg_rank = (i + j) / 2.0
        pct = 100.0 * avg_rank / (len(sorted_vals) - 1)
        if lower_is_better:
            pct = 100.0 - pct

        for k in range(i, j + 1):
            out[sorted_vals[k][0]] = pct

        i = j + 1

    return out


def find_existing_columns(fields: List[str], names: List[str]) -> List[str]:
    out: List[str] = []
    nfields = {norm(f): f for f in fields}

    for name in names:
        nn = norm(name)
        if nn in nfields and nfields[nn] not in out:
            out.append(nfields[nn])

    for name in names:
        nn = norm(name)
        if not nn:
            continue
        for f in fields:
            nf = norm(f)
            if len(nn) >= 5 and nn in nf and f not in out:
                out.append(f)

    return out


def split_aliases(s: str) -> List[str]:
    return [x.strip() for x in str(s or "").split("|") if x.strip()]


def split_matched_columns(s: str) -> List[str]:
    return [x.strip() for x in str(s or "").split("|") if x.strip()]


def candidate_sources(root: Path) -> List[Path]:
    paths = [
        root / "state/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv",
    ]
    return [p for p in paths if p.exists()]


def choose_source(root: Path) -> Tuple[Optional[Path], List[Dict[str, str]], List[str], List[Dict[str, str]]]:
    candidates = []
    for p in candidate_sources(root):
        rows, fields = read_csv(p)
        fwd_nonblank = 0
        for field in fields:
            nf = norm(field)
            if "forward" in nf or "fwd" in nf or "return_1d" in nf or "return_5d" in nf or "return_10d" in nf or "return_20d" in nf:
                fwd_nonblank += sum(1 for r in rows if str(r.get(field, "")).strip() != "")
        candidates.append({
            "path": str(p),
            "rows": str(len(rows)),
            "columns": str(len(fields)),
            "forward_nonblank_cells": str(fwd_nonblank),
        })

    best_path = None
    best_rows: List[Dict[str, str]] = []
    best_fields: List[str] = []
    best_score = (-1, -1)

    for p in candidate_sources(root):
        rows, fields = read_csv(p)
        fwd_nonblank = 0
        for field in fields:
            nf = norm(field)
            if "forward" in nf or "fwd" in nf or "return_1d" in nf or "return_5d" in nf or "return_10d" in nf or "return_20d" in nf:
                fwd_nonblank += sum(1 for r in rows if str(r.get(field, "")).strip() != "")
        score = (len(rows), fwd_nonblank)
        if score > best_score:
            best_score = score
            best_path = p
            best_rows = rows
            best_fields = fields

    return best_path, best_rows, best_fields, candidates


def detect_label_columns(fields: List[str]) -> Dict[int, Optional[str]]:
    aliases = {
        1: ["forward_return_1d", "fwd_1d", "return_1d", "forward_1d_return", "return_1d_pct", "fwd_return_1d"],
        5: ["forward_return_5d", "fwd_5d", "return_5d", "forward_5d_return", "return_5d_pct", "fwd_return_5d"],
        10: ["forward_return_10d", "fwd_10d", "return_10d", "forward_10d_return", "return_10d_pct", "fwd_return_10d"],
        20: ["forward_return_20d", "fwd_20d", "return_20d", "forward_20d_return", "return_20d_pct", "fwd_return_20d"],
    }
    out: Dict[int, Optional[str]] = {}
    for h, names in aliases.items():
        cols = find_existing_columns(fields, names)
        out[h] = cols[0] if cols else None
    return out


def factor_raw_values(rows: List[Dict[str, str]], columns: List[str]) -> Tuple[List[Optional[float]], str]:
    raw: List[Optional[float]] = []

    if not columns:
        return [None] * len(rows), "NO_CAPTURED_COLUMN"

    # Prefer exact score-style columns when available.
    preferred = None
    for c in columns:
        nc = norm(c)
        if nc.endswith("_score") or nc in ("execution_fit", "relative_strength_score", "volatility_penalty", "overheat_penalty"):
            preferred = c
            break

    if preferred:
        for r in rows:
            raw.append(parse_bool_or_float(r.get(preferred)))
        return raw, f"DIRECT_COLUMN:{preferred}"

    for r in rows:
        vals = []
        for c in columns:
            v = parse_bool_or_float(r.get(c))
            if v is not None:
                vals.append(v)
        raw.append(sum(vals) / len(vals) if vals else None)

    return raw, "AGGREGATED_CAPTURED_COLUMNS:" + ",".join(columns)


def evaluate_factor_horizon(
    factor_name: str,
    factor_direction: str,
    factor_raw: List[Optional[float]],
    factor_score: List[Optional[float]],
    labels: List[Optional[float]],
    horizon: int,
    min_count: int,
    top_fraction: float,
) -> Dict[str, str]:
    pairs = []
    for s, y in zip(factor_score, labels):
        if s is None or y is None:
            continue
        if math.isnan(s) or math.isnan(y):
            continue
        pairs.append((s, y))

    n = len(pairs)

    if n == 0:
        return {
            "factor_name": factor_name,
            "horizon": f"{horizon}D",
            "n_pairs": "0",
            "status": "NO_MATURE_FORWARD_RETURNS_OR_FACTOR_VALUES",
            "recommendation": "WAIT_FOR_FORWARD_RETURNS",
        }

    scores = [p[0] for p in pairs]
    rets = [p[1] for p in pairs]
    sorted_pairs = sorted(pairs, key=lambda p: p[0], reverse=True)

    k = max(1, int(math.ceil(n * top_fraction)))
    if n < 4:
        k = 1

    top = [y for _, y in sorted_pairs[:k]]
    bottom = [y for _, y in sorted_pairs[-k:]]

    top_mean = mean(top)
    bottom_mean = mean(bottom)
    spread = None
    if top_mean is not None and bottom_mean is not None:
        spread = top_mean - bottom_mean

    corr_p = pearson(scores, rets)
    corr_s = spearman(scores, rets)

    if n < min_count:
        status = "INSUFFICIENT_SAMPLE"
        recommendation = "DO_NOT_ADJUST_WEIGHT"
    else:
        status = "OK_EVALUATED"
        if spread is not None and spread > 0 and (corr_s is None or corr_s >= -0.05):
            recommendation = "FACTOR_SUPPORTS_CURRENT_OR_UPWEIGHT_RESEARCH"
        elif spread is not None and spread < 0:
            recommendation = "FACTOR_NEEDS_REVIEW_OR_DOWNWEIGHT_RESEARCH"
        else:
            recommendation = "NEUTRAL_OR_WEAK_SIGNAL"

    return {
        "factor_name": factor_name,
        "horizon": f"{horizon}D",
        "n_pairs": str(n),
        "status": status,
        "recommendation": recommendation,
        "factor_direction": factor_direction,
        "top_fraction": fmt_num(top_fraction, 4),
        "top_count": str(len(top)),
        "bottom_count": str(len(bottom)),
        "all_mean_return": fmt_pct(mean(rets)),
        "all_median_return": fmt_pct(median(rets)),
        "all_win_rate": fmt_pct(win_rate(rets)),
        "top_mean_return": fmt_pct(top_mean),
        "top_median_return": fmt_pct(median(top)),
        "top_win_rate": fmt_pct(win_rate(top)),
        "bottom_mean_return": fmt_pct(bottom_mean),
        "bottom_median_return": fmt_pct(median(bottom)),
        "bottom_win_rate": fmt_pct(win_rate(bottom)),
        "top_minus_bottom_mean": fmt_pct(spread),
        "pearson_corr": fmt_num(corr_p, 6),
        "spearman_corr": fmt_num(corr_s, 6),
    }


def summarize_factor(effect_rows: List[Dict[str, str]], factor_name: str, min_count: int) -> Dict[str, str]:
    rows = [r for r in effect_rows if r.get("factor_name") == factor_name]
    valid = [r for r in rows if r.get("status") == "OK_EVALUATED"]

    def pct_to_float(s: str) -> Optional[float]:
        return parse_return(s)

    spreads = []
    corrs = []
    for r in valid:
        sp = pct_to_float(r.get("top_minus_bottom_mean", ""))
        co = parse_float(r.get("spearman_corr", ""))
        if sp is not None:
            spreads.append(sp)
        if co is not None:
            corrs.append(co)

    if not valid:
        total_pairs = sum(int(r.get("n_pairs", "0") or "0") for r in rows)
        return {
            "factor_name": factor_name,
            "evaluated_horizon_count": "0",
            "total_pairs_across_horizons": str(total_pairs),
            "avg_top_minus_bottom": "",
            "avg_spearman_corr": "",
            "summary_status": "INSUFFICIENT_MATURE_DATA",
            "weight_action": "HOLD_CURRENT_WEIGHT",
        }

    avg_spread = mean(spreads)
    avg_corr = mean(corrs)
    positive_spreads = sum(1 for x in spreads if x > 0)
    negative_spreads = sum(1 for x in spreads if x < 0)

    if positive_spreads >= 2 and (avg_corr is None or avg_corr >= -0.05):
        action = "RESEARCH_UPWEIGHT_OR_KEEP"
        status = "POSITIVE_EVIDENCE"
    elif negative_spreads >= 2:
        action = "RESEARCH_DOWNWEIGHT"
        status = "NEGATIVE_EVIDENCE"
    else:
        action = "HOLD_CURRENT_WEIGHT"
        status = "MIXED_OR_WEAK_EVIDENCE"

    return {
        "factor_name": factor_name,
        "evaluated_horizon_count": str(len(valid)),
        "total_pairs_across_horizons": str(sum(int(r.get("n_pairs", "0") or "0") for r in rows)),
        "avg_top_minus_bottom": fmt_pct(avg_spread),
        "avg_spearman_corr": fmt_num(avg_corr, 6),
        "summary_status": status,
        "weight_action": action,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"D:\us-tech-quant")
    ap.add_argument("--min-count", type=int, default=20)
    ap.add_argument("--top-fraction", type=float, default=0.30)
    args = ap.parse_args()

    root = Path(args.root)
    out_dir = root / "outputs/v18/factor_research"
    ensure_dir(out_dir)

    registry_path = root / "state/v18/factor_registry/V18_CURRENT_FACTOR_REGISTRY.csv"
    coverage_path = root / "outputs/v18/factor_registry/V18_10A_CURRENT_FACTOR_COVERAGE_AUDIT.csv"

    registry_rows, registry_fields = read_csv(registry_path)
    coverage_rows, coverage_fields = read_csv(coverage_path)

    coverage_by_factor = {r.get("factor_name", ""): r for r in coverage_rows}

    source_path, data_rows, data_fields, source_candidates = choose_source(root)

    effect_path = out_dir / "V18_10B_CURRENT_FACTOR_EFFECTIVENESS.csv"
    summary_path = out_dir / "V18_10B_CURRENT_FACTOR_EFFECTIVENESS_SUMMARY.csv"
    audit_path = out_dir / "V18_10B_CURRENT_FACTOR_EFFECTIVENESS_AUDIT.csv"
    report_path = out_dir / "V18_10B_CURRENT_FACTOR_EFFECTIVENESS_REPORT.md"
    read_first_path = out_dir / "V18_10B_READ_FIRST.txt"

    official_factors = [
        r for r in registry_rows
        if r.get("official_status") == "official_candidate"
    ]

    label_cols = detect_label_columns(data_fields)
    label_values: Dict[int, List[Optional[float]]] = {}
    label_counts: Dict[int, int] = {}

    for h, c in label_cols.items():
        vals = []
        if c:
            for r in data_rows:
                vals.append(parse_return(r.get(c), c))
        else:
            vals = [None] * len(data_rows)
        label_values[h] = vals
        label_counts[h] = sum(1 for v in vals if v is not None)

    factor_audit_rows: List[Dict[str, str]] = []
    effect_rows: List[Dict[str, str]] = []

    for f in official_factors:
        fname = f.get("factor_name", "")
        direction = f.get("direction", "")
        lower_is_better = direction == "lower_is_better"

        coverage = coverage_by_factor.get(fname, {})
        names = [fname] + split_aliases(f.get("aliases", "")) + split_matched_columns(coverage.get("matched_columns", ""))
        cols = find_existing_columns(data_fields, names)

        raw, method = factor_raw_values(data_rows, cols)
        score = percentile_scores(raw, lower_is_better=lower_is_better)

        factor_nonnull = sum(1 for v in raw if v is not None)
        score_nonnull = sum(1 for v in score if v is not None)

        factor_audit_rows.append({
            "factor_name": fname,
            "direction": direction,
            "current_weight": f.get("current_weight", ""),
            "min_weight": f.get("min_weight", ""),
            "max_weight": f.get("max_weight", ""),
            "captured_columns_used": " | ".join(cols),
            "factor_method": method,
            "factor_nonnull_count": str(factor_nonnull),
            "factor_score_nonnull_count": str(score_nonnull),
            "coverage_status": coverage.get("coverage_status", ""),
            "note": "favorable_score = cross_sectional_percentile(raw); inverted for lower_is_better",
        })

        for h in [1, 5, 10, 20]:
            row = evaluate_factor_horizon(
                factor_name=fname,
                factor_direction=direction,
                factor_raw=raw,
                factor_score=score,
                labels=label_values[h],
                horizon=h,
                min_count=args.min_count,
                top_fraction=args.top_fraction,
            )
            row["label_column"] = label_cols.get(h) or ""
            row["captured_columns_used"] = " | ".join(cols)
            row["factor_method"] = method
            row["current_weight"] = f.get("current_weight", "")
            effect_rows.append(row)

    summary_rows = [
        summarize_factor(effect_rows, f.get("factor_name", ""), args.min_count)
        for f in official_factors
    ]

    effect_fields = [
        "factor_name",
        "horizon",
        "n_pairs",
        "status",
        "recommendation",
        "current_weight",
        "factor_direction",
        "label_column",
        "captured_columns_used",
        "factor_method",
        "top_fraction",
        "top_count",
        "bottom_count",
        "all_mean_return",
        "all_median_return",
        "all_win_rate",
        "top_mean_return",
        "top_median_return",
        "top_win_rate",
        "bottom_mean_return",
        "bottom_median_return",
        "bottom_win_rate",
        "top_minus_bottom_mean",
        "pearson_corr",
        "spearman_corr",
    ]

    summary_fields = [
        "factor_name",
        "evaluated_horizon_count",
        "total_pairs_across_horizons",
        "avg_top_minus_bottom",
        "avg_spearman_corr",
        "summary_status",
        "weight_action",
    ]

    audit_fields = [
        "factor_name",
        "direction",
        "current_weight",
        "min_weight",
        "max_weight",
        "captured_columns_used",
        "factor_method",
        "factor_nonnull_count",
        "factor_score_nonnull_count",
        "coverage_status",
        "note",
    ]

    source_audit_path = out_dir / "V18_10B_CURRENT_SOURCE_AUDIT.csv"
    write_csv(effect_path, effect_rows, effect_fields)
    write_csv(summary_path, summary_rows, summary_fields)
    write_csv(audit_path, factor_audit_rows, audit_fields)
    write_csv(source_audit_path, source_candidates, ["path", "rows", "columns", "forward_nonblank_cells"])

    mature_label_min = min(label_counts.values()) if label_counts else 0
    ok_eval_count = sum(1 for r in effect_rows if r.get("status") == "OK_EVALUATED")
    insufficient_count = sum(1 for r in effect_rows if r.get("status") == "INSUFFICIENT_SAMPLE")
    no_data_count = sum(1 for r in effect_rows if r.get("status") == "NO_MATURE_FORWARD_RETURNS_OR_FACTOR_VALUES")

    report = []
    report.append("# V18.10B Factor Effectiveness Backtest")
    report.append("")
    report.append(f"Generated: `{now_text()}`")
    report.append("")
    report.append("## 1. Status")
    report.append("")
    report.append("- STATUS: `OK_FACTOR_EFFECTIVENESS_BACKTEST_READY`")
    report.append("- MODE: `SHADOW_ONLY_NO_BLACK_BOX_FACTOR_RESEARCH`")
    report.append("- OFFICIAL_DECISION_IMPACT: `NONE`")
    report.append("- AUTO_WEIGHT_CHANGE: `DISABLED`")
    report.append("- AUTO_PROMOTION: `DISABLED`")
    report.append("- AUTO_TRADE: `DISABLED`")
    report.append("")
    report.append("## 2. Source")
    report.append("")
    report.append(f"- SELECTED_SOURCE: `{source_path}`")
    report.append(f"- SOURCE_ROWS: `{len(data_rows)}`")
    report.append(f"- SOURCE_COLUMNS: `{len(data_fields)}`")
    report.append(f"- MIN_COUNT_FOR_EVALUATION: `{args.min_count}`")
    report.append(f"- TOP_FRACTION: `{args.top_fraction}`")
    report.append("")
    report.append("## 3. Forward return maturity")
    report.append("")
    report.append("| horizon | label_column | nonblank_count |")
    report.append("|---|---|---:|")
    for h in [1, 5, 10, 20]:
        report.append(f"| {h}D | {label_cols.get(h) or ''} | {label_counts.get(h, 0)} |")
    report.append("")
    report.append("## 4. Factor audit")
    report.append("")
    report.append("| factor | current_weight | columns_used | method | nonnull |")
    report.append("|---|---:|---|---|---:|")
    for r in factor_audit_rows:
        report.append(
            f"| {r['factor_name']} | {r['current_weight']} | {r['captured_columns_used']} | "
            f"{r['factor_method']} | {r['factor_nonnull_count']} |"
        )
    report.append("")
    report.append("## 5. Summary")
    report.append("")
    report.append("| factor | evaluated_horizons | avg_top_minus_bottom | avg_spearman | status | action |")
    report.append("|---|---:|---:|---:|---|---|")
    for r in summary_rows:
        report.append(
            f"| {r['factor_name']} | {r['evaluated_horizon_count']} | {r['avg_top_minus_bottom']} | "
            f"{r['avg_spearman_corr']} | {r['summary_status']} | {r['weight_action']} |"
        )
    report.append("")
    report.append("## 6. Interpretation rules")
    report.append("")
    report.append("1. `top_minus_bottom_mean > 0` means the favorable factor group outperformed the unfavorable group for that horizon.")
    report.append("2. `spearman_corr > 0` means higher favorable factor score is generally associated with higher forward return.")
    report.append("3. `INSUFFICIENT_SAMPLE` means the factor should not be used for weight changes yet.")
    report.append("4. This report does not change official weights. It only produces evidence.")
    report.append("")
    report.append("## 7. Outputs")
    report.append("")
    report.append(f"- EFFECTIVENESS: `{effect_path}`")
    report.append(f"- SUMMARY: `{summary_path}`")
    report.append(f"- FACTOR_AUDIT: `{audit_path}`")
    report.append(f"- SOURCE_AUDIT: `{source_audit_path}`")
    report.append(f"- REPORT: `{report_path}`")
    report.append(f"- READ_FIRST: `{read_first_path}`")
    report.append("")
    report.append("## 8. Next step")
    report.append("")
    if mature_label_min < args.min_count:
        report.append("Forward-return sample is still immature. Keep running daily tracker + forward return filler until enough horizons mature.")
    else:
        report.append("Proceed to V18.10C Weight Research Engine after reviewing factor effectiveness.")
    report.append("")

    report_path.write_text("\n".join(report), encoding="utf-8")

    read_first = f"""V18.10B FACTOR EFFECTIVENESS BACKTEST READ FIRST

STATUS:
OK_FACTOR_EFFECTIVENESS_BACKTEST_READY

MODE:
SHADOW_ONLY_NO_BLACK_BOX_FACTOR_RESEARCH

OFFICIAL_DECISION_IMPACT:
NONE

AUTO_WEIGHT_CHANGE:
DISABLED

AUTO_PROMOTION:
DISABLED

AUTO_TRADE:
DISABLED

SELECTED_SOURCE:
{source_path}

SOURCE_ROWS:
{len(data_rows)}

OFFICIAL_FACTOR_COUNT:
{len(official_factors)}

LABEL_1D_COLUMN:
{label_cols.get(1) or ""}

LABEL_1D_NONBLANK_COUNT:
{label_counts.get(1, 0)}

LABEL_5D_COLUMN:
{label_cols.get(5) or ""}

LABEL_5D_NONBLANK_COUNT:
{label_counts.get(5, 0)}

LABEL_10D_COLUMN:
{label_cols.get(10) or ""}

LABEL_10D_NONBLANK_COUNT:
{label_counts.get(10, 0)}

LABEL_20D_COLUMN:
{label_cols.get(20) or ""}

LABEL_20D_NONBLANK_COUNT:
{label_counts.get(20, 0)}

MIN_COUNT_FOR_EVALUATION:
{args.min_count}

OK_EVALUATED_ROWS:
{ok_eval_count}

INSUFFICIENT_SAMPLE_ROWS:
{insufficient_count}

NO_DATA_ROWS:
{no_data_count}

EFFECTIVENESS:
{effect_path}

SUMMARY:
{summary_path}

FACTOR_AUDIT:
{audit_path}

SOURCE_AUDIT:
{source_audit_path}

REPORT:
{report_path}

READ_FIRST:
{read_first_path}

NEXT_STEP:
If most rows are INSUFFICIENT_SAMPLE, continue daily forward-return filling first.
If enough rows are OK_EVALUATED, review V18_10B_CURRENT_FACTOR_EFFECTIVENESS_SUMMARY.csv before V18.10C.
"""
    read_first_path.write_text(read_first, encoding="utf-8")

    print("")
    print("=== V18.10B FACTOR EFFECTIVENESS BACKTEST READY ===")
    print("STATUS: OK_FACTOR_EFFECTIVENESS_BACKTEST_READY")
    print("MODE: SHADOW_ONLY_NO_BLACK_BOX_FACTOR_RESEARCH")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print("AUTO_WEIGHT_CHANGE: DISABLED")
    print("AUTO_PROMOTION: DISABLED")
    print("AUTO_TRADE: DISABLED")
    print(f"SELECTED_SOURCE: {source_path}")
    print(f"SOURCE_ROWS: {len(data_rows)}")
    print(f"OFFICIAL_FACTOR_COUNT: {len(official_factors)}")
    print(f"LABEL_1D_NONBLANK_COUNT: {label_counts.get(1, 0)}")
    print(f"LABEL_5D_NONBLANK_COUNT: {label_counts.get(5, 0)}")
    print(f"LABEL_10D_NONBLANK_COUNT: {label_counts.get(10, 0)}")
    print(f"LABEL_20D_NONBLANK_COUNT: {label_counts.get(20, 0)}")
    print(f"MIN_COUNT_FOR_EVALUATION: {args.min_count}")
    print(f"OK_EVALUATED_ROWS: {ok_eval_count}")
    print(f"INSUFFICIENT_SAMPLE_ROWS: {insufficient_count}")
    print(f"NO_DATA_ROWS: {no_data_count}")
    print(f"EFFECTIVENESS: {effect_path}")
    print(f"SUMMARY: {summary_path}")
    print(f"FACTOR_AUDIT: {audit_path}")
    print(f"SOURCE_AUDIT: {source_audit_path}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first_path}")
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
