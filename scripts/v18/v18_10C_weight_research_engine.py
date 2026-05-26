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


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def norm(s: str) -> str:
    return str(s or "").strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")


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
    nf = norm(field_name)
    if ("pct" in nf or "percent" in nf) and abs(v) > 1.0:
        return v / 100.0
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
        if len(nn) < 5:
            continue
        for f in fields:
            nf = norm(f)
            if nn in nf and f not in out:
                out.append(f)

    return out


def split_aliases(s: str) -> List[str]:
    return [x.strip() for x in str(s or "").split("|") if x.strip()]


def candidate_sources(root: Path) -> List[Path]:
    return [
        p for p in [
            root / "state/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
            root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
            root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv",
        ]
        if p.exists()
    ]


def choose_source(root: Path) -> Tuple[Optional[Path], List[Dict[str, str]], List[str], List[Dict[str, str]]]:
    audit = []
    best_path = None
    best_rows: List[Dict[str, str]] = []
    best_fields: List[str] = []
    best_score = (-1, -1)

    for p in candidate_sources(root):
        rows, fields = read_csv(p)
        forward_nonblank = 0
        for f in fields:
            nf = norm(f)
            if "forward" in nf or "fwd" in nf or "return_1d" in nf or "return_5d" in nf or "return_10d" in nf or "return_20d" in nf:
                forward_nonblank += sum(1 for r in rows if str(r.get(f, "")).strip() != "")

        audit.append({
            "path": str(p),
            "rows": str(len(rows)),
            "columns": str(len(fields)),
            "forward_nonblank_cells": str(forward_nonblank),
        })

        score = (len(rows), forward_nonblank)
        if score > best_score:
            best_score = score
            best_path = p
            best_rows = rows
            best_fields = fields

    return best_path, best_rows, best_fields, audit


def detect_label_columns(fields: List[str]) -> Dict[int, Optional[str]]:
    aliases = {
        1: ["forward_return_1d", "fwd_1d", "fwd_return_1d", "return_1d", "return_1d_pct", "forward_1d_return"],
        5: ["forward_return_5d", "fwd_5d", "fwd_return_5d", "return_5d", "return_5d_pct", "forward_5d_return"],
        10: ["forward_return_10d", "fwd_10d", "fwd_return_10d", "return_10d", "return_10d_pct", "forward_10d_return"],
        20: ["forward_return_20d", "fwd_20d", "fwd_return_20d", "return_20d", "return_20d_pct", "forward_20d_return"],
    }
    out: Dict[int, Optional[str]] = {}
    for h, names in aliases.items():
        cols = find_existing_columns(fields, names)
        out[h] = cols[0] if cols else None
    return out


def factor_raw_values(rows: List[Dict[str, str]], columns: List[str]) -> Tuple[List[Optional[float]], str]:
    if not columns:
        return [None] * len(rows), "NO_CAPTURED_COLUMN"

    preferred = None
    for c in columns:
        nc = norm(c)
        if (
            nc.endswith("_score")
            or nc in (
                "relative_strength_score",
                "execution_fit",
                "execution_fit_score",
                "volatility_penalty",
                "overheat_penalty",
                "trend_score",
            )
        ):
            preferred = c
            break

    if preferred:
        return [parse_bool_or_float(r.get(preferred)) for r in rows], f"DIRECT_COLUMN:{preferred}"

    raw = []
    for r in rows:
        vals = []
        for c in columns:
            v = parse_bool_or_float(r.get(c))
            if v is not None:
                vals.append(v)
        raw.append(sum(vals) / len(vals) if vals else None)

    return raw, "AGGREGATED_CAPTURED_COLUMNS:" + ",".join(columns)


def weight_candidates(baseline: Dict[str, float]) -> List[Dict[str, object]]:
    factors = [
        "trend_score",
        "relative_strength_score",
        "pullback_quality_score",
        "momentum_continuation_score",
        "overheat_penalty",
        "volatility_penalty",
        "execution_fit",
    ]

    def clean(w: Dict[str, float]) -> Dict[str, float]:
        out = {f: float(w.get(f, 0.0)) for f in factors}
        s = sum(v for v in out.values() if v > 0)
        if s <= 0:
            return {f: 1.0 / len(factors) for f in factors}
        return {f: max(out[f], 0.0) / s for f in factors}

    base = clean(baseline)

    return [
        {
            "weight_set": "BASELINE_CURRENT",
            "description": "Current official candidate weights from factor registry.",
            "weights": base,
        },
        {
            "weight_set": "EQUAL_WEIGHT",
            "description": "Equal-weight research control.",
            "weights": clean({f: 1 for f in factors}),
        },
        {
            "weight_set": "DEFENSIVE_CAUTION",
            "description": "Higher pullback, overheat, and volatility control; lower momentum.",
            "weights": clean({
                "trend_score": 0.20,
                "relative_strength_score": 0.18,
                "pullback_quality_score": 0.24,
                "momentum_continuation_score": 0.08,
                "overheat_penalty": 0.18,
                "volatility_penalty": 0.08,
                "execution_fit": 0.04,
            }),
        },
        {
            "weight_set": "MOMENTUM_NORMAL",
            "description": "More aggressive trend, RS, and momentum profile for normal markets.",
            "weights": clean({
                "trend_score": 0.26,
                "relative_strength_score": 0.24,
                "pullback_quality_score": 0.14,
                "momentum_continuation_score": 0.22,
                "overheat_penalty": 0.06,
                "volatility_penalty": 0.04,
                "execution_fit": 0.04,
            }),
        },
        {
            "weight_set": "PULLBACK_QUALITY",
            "description": "Prioritizes strong assets with better entry quality.",
            "weights": clean({
                "trend_score": 0.20,
                "relative_strength_score": 0.18,
                "pullback_quality_score": 0.32,
                "momentum_continuation_score": 0.08,
                "overheat_penalty": 0.14,
                "volatility_penalty": 0.05,
                "execution_fit": 0.03,
            }),
        },
        {
            "weight_set": "LOW_VOL_DEFENSE",
            "description": "Higher volatility penalty and overheat control.",
            "weights": clean({
                "trend_score": 0.20,
                "relative_strength_score": 0.18,
                "pullback_quality_score": 0.20,
                "momentum_continuation_score": 0.08,
                "overheat_penalty": 0.14,
                "volatility_penalty": 0.16,
                "execution_fit": 0.04,
            }),
        },
        {
            "weight_set": "EXECUTION_AWARE_SMALL_ACCOUNT",
            "description": "Higher execution fit for small-account practical tradability.",
            "weights": clean({
                "trend_score": 0.20,
                "relative_strength_score": 0.18,
                "pullback_quality_score": 0.20,
                "momentum_continuation_score": 0.10,
                "overheat_penalty": 0.10,
                "volatility_penalty": 0.07,
                "execution_fit": 0.15,
            }),
        },
    ]


def combined_score_for_weightset(
    factor_scores: Dict[str, List[Optional[float]]],
    weights: Dict[str, float],
    row_count: int,
) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for i in range(row_count):
        total = 0.0
        used = 0.0
        for f, w in weights.items():
            if w <= 0:
                continue
            vals = factor_scores.get(f, [])
            if i >= len(vals):
                continue
            v = vals[i]
            if v is None or math.isnan(v):
                continue
            total += w * v
            used += w
        out.append(total / used if used > 0 else None)
    return out


def evaluate_weightset_horizon(
    weight_set: str,
    scores: List[Optional[float]],
    labels: List[Optional[float]],
    horizon: int,
    min_count: int,
    top_fraction: float,
) -> Dict[str, str]:
    pairs = []
    for s, y in zip(scores, labels):
        if s is None or y is None:
            continue
        if math.isnan(s) or math.isnan(y):
            continue
        pairs.append((s, y))

    n = len(pairs)

    if n == 0:
        return {
            "weight_set": weight_set,
            "horizon": f"{horizon}D",
            "n_pairs": "0",
            "status": "NO_MATURE_FORWARD_RETURNS",
            "promotion_action": "HOLD_NO_WEIGHT_ACTION",
        }

    sorted_pairs = sorted(pairs, key=lambda p: p[0], reverse=True)
    k = max(1, int(math.ceil(n * top_fraction)))
    if n < 4:
        k = 1

    top = [y for _, y in sorted_pairs[:k]]
    bottom = [y for _, y in sorted_pairs[-k:]]

    spread = None
    top_m = mean(top)
    bottom_m = mean(bottom)
    if top_m is not None and bottom_m is not None:
        spread = top_m - bottom_m

    if n < min_count:
        status = "INSUFFICIENT_SAMPLE"
        action = "HOLD_NO_WEIGHT_ACTION"
    else:
        status = "OK_EVALUATED"
        action = "RESEARCH_REVIEW_ALLOWED_NO_AUTO_PROMOTION"

    return {
        "weight_set": weight_set,
        "horizon": f"{horizon}D",
        "n_pairs": str(n),
        "status": status,
        "promotion_action": action,
        "top_fraction": fmt_num(top_fraction, 4),
        "top_count": str(len(top)),
        "bottom_count": str(len(bottom)),
        "all_mean_return": fmt_pct(mean([y for _, y in pairs])),
        "all_median_return": fmt_pct(median([y for _, y in pairs])),
        "all_win_rate": fmt_pct(win_rate([y for _, y in pairs])),
        "top_mean_return": fmt_pct(top_m),
        "top_median_return": fmt_pct(median(top)),
        "top_win_rate": fmt_pct(win_rate(top)),
        "bottom_mean_return": fmt_pct(bottom_m),
        "bottom_median_return": fmt_pct(median(bottom)),
        "bottom_win_rate": fmt_pct(win_rate(bottom)),
        "top_minus_bottom_mean": fmt_pct(spread),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"D:\us-tech-quant")
    ap.add_argument("--min-count", type=int, default=20)
    ap.add_argument("--top-fraction", type=float, default=0.30)
    args = ap.parse_args()

    root = Path(args.root)
    out_dir = root / "outputs/v18/weight_research"
    ensure_dir(out_dir)

    registry_path = root / "state/v18/factor_registry/V18_CURRENT_FACTOR_REGISTRY.csv"
    source_path, data_rows, data_fields, source_audit = choose_source(root)

    registry_rows, _ = read_csv(registry_path)

    official_factors = [
        r for r in registry_rows
        if r.get("official_status") == "official_candidate"
    ]

    baseline = {}
    for r in official_factors:
        baseline[r.get("factor_name", "")] = parse_float(r.get("current_weight")) or 0.0

    label_cols = detect_label_columns(data_fields)
    label_values: Dict[int, List[Optional[float]]] = {}
    label_counts: Dict[int, int] = {}
    for h, c in label_cols.items():
        vals = []
        if c:
            vals = [parse_return(r.get(c), c) for r in data_rows]
        else:
            vals = [None] * len(data_rows)
        label_values[h] = vals
        label_counts[h] = sum(1 for v in vals if v is not None)

    factor_scores: Dict[str, List[Optional[float]]] = {}
    factor_audit_rows = []

    for f in official_factors:
        fname = f.get("factor_name", "")
        direction = f.get("direction", "")
        lower_is_better = direction == "lower_is_better"
        aliases = [fname] + split_aliases(f.get("aliases", ""))
        cols = find_existing_columns(data_fields, aliases)
        raw, method = factor_raw_values(data_rows, cols)
        score = percentile_scores(raw, lower_is_better=lower_is_better)
        factor_scores[fname] = score

        factor_audit_rows.append({
            "factor_name": fname,
            "direction": direction,
            "current_weight": f.get("current_weight", ""),
            "columns_used": " | ".join(cols),
            "method": method,
            "nonnull_raw_count": str(sum(1 for x in raw if x is not None)),
            "nonnull_score_count": str(sum(1 for x in score if x is not None)),
        })

    weight_sets = weight_candidates(baseline)

    candidate_rows = []
    eval_rows = []

    for ws in weight_sets:
        name = str(ws["weight_set"])
        description = str(ws["description"])
        weights = ws["weights"]

        row = {
            "weight_set": name,
            "description": description,
        }
        for f, w in weights.items():
            row[f] = fmt_num(w, 6)
        candidate_rows.append(row)

        combined = combined_score_for_weightset(
            factor_scores=factor_scores,
            weights=weights,
            row_count=len(data_rows),
        )

        for h in [1, 5, 10, 20]:
            e = evaluate_weightset_horizon(
                weight_set=name,
                scores=combined,
                labels=label_values[h],
                horizon=h,
                min_count=args.min_count,
                top_fraction=args.top_fraction,
            )
            e["label_column"] = label_cols.get(h) or ""
            eval_rows.append(e)

    ready_horizons = sum(1 for h in [1, 5, 10, 20] if label_counts.get(h, 0) >= args.min_count)
    ok_eval_rows = sum(1 for r in eval_rows if r.get("status") == "OK_EVALUATED")
    insufficient_rows = sum(1 for r in eval_rows if r.get("status") == "INSUFFICIENT_SAMPLE")
    no_data_rows = sum(1 for r in eval_rows if r.get("status") == "NO_MATURE_FORWARD_RETURNS")

    if ready_horizons > 0 and ok_eval_rows > 0:
        promotion_permission = "RESEARCH_REVIEW_ALLOWED_BUT_NO_AUTO_PROMOTION"
    else:
        promotion_permission = "HOLD_NO_WEIGHT_ACTION"

    status = "OK_WEIGHT_RESEARCH_ENGINE_READY"

    candidates_path = out_dir / "V18_10C_CURRENT_WEIGHT_CANDIDATES.csv"
    eval_path = out_dir / "V18_10C_CURRENT_WEIGHT_RESEARCH_EVALUATION.csv"
    factor_audit_path = out_dir / "V18_10C_CURRENT_WEIGHT_RESEARCH_FACTOR_AUDIT.csv"
    source_audit_path = out_dir / "V18_10C_CURRENT_WEIGHT_RESEARCH_SOURCE_AUDIT.csv"
    report_path = out_dir / "V18_10C_CURRENT_WEIGHT_RESEARCH_REPORT.md"
    read_first_path = out_dir / "V18_10C_READ_FIRST.txt"

    factor_names = [
        "trend_score",
        "relative_strength_score",
        "pullback_quality_score",
        "momentum_continuation_score",
        "overheat_penalty",
        "volatility_penalty",
        "execution_fit",
    ]

    write_csv(candidates_path, candidate_rows, ["weight_set", "description"] + factor_names)

    write_csv(eval_path, eval_rows, [
        "weight_set",
        "horizon",
        "label_column",
        "n_pairs",
        "status",
        "promotion_action",
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
    ])

    write_csv(factor_audit_path, factor_audit_rows, [
        "factor_name",
        "direction",
        "current_weight",
        "columns_used",
        "method",
        "nonnull_raw_count",
        "nonnull_score_count",
    ])

    write_csv(source_audit_path, source_audit, [
        "path",
        "rows",
        "columns",
        "forward_nonblank_cells",
    ])

    report = []
    report.append("# V18.10C Weight Research Engine")
    report.append("")
    report.append(f"Generated: `{now_text()}`")
    report.append("")
    report.append("## 1. Status")
    report.append("")
    report.append(f"- STATUS: `{status}`")
    report.append("- MODE: `SHADOW_ONLY_NO_BLACK_BOX_WEIGHT_RESEARCH`")
    report.append("- OFFICIAL_DECISION_IMPACT: `NONE`")
    report.append("- AUTO_WEIGHT_CHANGE: `DISABLED`")
    report.append("- AUTO_PROMOTION: `DISABLED`")
    report.append("- AUTO_TRADE: `DISABLED`")
    report.append("")
    report.append("## 2. Source")
    report.append("")
    report.append(f"- SELECTED_SOURCE: `{source_path}`")
    report.append(f"- SOURCE_ROWS: `{len(data_rows)}`")
    report.append(f"- OFFICIAL_FACTOR_COUNT: `{len(official_factors)}`")
    report.append(f"- WEIGHT_CANDIDATE_COUNT: `{len(weight_sets)}`")
    report.append(f"- MIN_COUNT_REQUIRED: `{args.min_count}`")
    report.append(f"- TOP_FRACTION: `{args.top_fraction}`")
    report.append("")
    report.append("## 3. Forward label maturity")
    report.append("")
    report.append("| horizon | label_column | nonblank_count |")
    report.append("|---|---|---:|")
    for h in [1, 5, 10, 20]:
        report.append(f"| {h}D | {label_cols.get(h) or ''} | {label_counts.get(h, 0)} |")
    report.append("")
    report.append("## 4. Weight candidates")
    report.append("")
    report.append("| weight_set | trend | rs | pullback | momentum | overheat | volatility | execution |")
    report.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in candidate_rows:
        report.append(
            f"| {row['weight_set']} | {row.get('trend_score','')} | {row.get('relative_strength_score','')} | "
            f"{row.get('pullback_quality_score','')} | {row.get('momentum_continuation_score','')} | "
            f"{row.get('overheat_penalty','')} | {row.get('volatility_penalty','')} | {row.get('execution_fit','')} |"
        )
    report.append("")
    report.append("## 5. Guardrail conclusion")
    report.append("")
    report.append(f"- READY_HORIZON_COUNT: `{ready_horizons}`")
    report.append(f"- OK_EVALUATED_ROWS: `{ok_eval_rows}`")
    report.append(f"- INSUFFICIENT_SAMPLE_ROWS: `{insufficient_rows}`")
    report.append(f"- NO_DATA_ROWS: `{no_data_rows}`")
    report.append(f"- PROMOTION_PERMISSION: `{promotion_permission}`")
    report.append("")
    report.append("No automatic weight changes are allowed. If forward labels are immature, the only valid action is HOLD_NO_WEIGHT_ACTION.")
    report.append("")
    report.append("## 6. Outputs")
    report.append("")
    report.append(f"- WEIGHT_CANDIDATES: `{candidates_path}`")
    report.append(f"- EVALUATION: `{eval_path}`")
    report.append(f"- FACTOR_AUDIT: `{factor_audit_path}`")
    report.append(f"- SOURCE_AUDIT: `{source_audit_path}`")
    report.append(f"- REPORT: `{report_path}`")
    report.append(f"- READ_FIRST: `{read_first_path}`")
    report.append("")

    report_path.write_text("\n".join(report), encoding="utf-8")

    read_first = f"""V18.10C WEIGHT RESEARCH ENGINE READ FIRST

STATUS:
{status}

MODE:
SHADOW_ONLY_NO_BLACK_BOX_WEIGHT_RESEARCH

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

WEIGHT_CANDIDATE_COUNT:
{len(weight_sets)}

LABEL_1D_NONBLANK_COUNT:
{label_counts.get(1, 0)}

LABEL_5D_NONBLANK_COUNT:
{label_counts.get(5, 0)}

LABEL_10D_NONBLANK_COUNT:
{label_counts.get(10, 0)}

LABEL_20D_NONBLANK_COUNT:
{label_counts.get(20, 0)}

READY_HORIZON_COUNT:
{ready_horizons}

OK_EVALUATED_ROWS:
{ok_eval_rows}

INSUFFICIENT_SAMPLE_ROWS:
{insufficient_rows}

NO_DATA_ROWS:
{no_data_rows}

PROMOTION_PERMISSION:
{promotion_permission}

WEIGHT_CANDIDATES:
{candidates_path}

EVALUATION:
{eval_path}

FACTOR_AUDIT:
{factor_audit_path}

SOURCE_AUDIT:
{source_audit_path}

REPORT:
{report_path}

READ_FIRST:
{read_first_path}

NEXT_STEP:
If PROMOTION_PERMISSION is HOLD_NO_WEIGHT_ACTION, do not adjust weights.
Keep running V18.10B-R2 daily factor research chain until forward-return labels mature.
"""
    read_first_path.write_text(read_first, encoding="utf-8")

    print("")
    print("=== V18.10C WEIGHT RESEARCH ENGINE READY ===")
    print(f"STATUS: {status}")
    print("MODE: SHADOW_ONLY_NO_BLACK_BOX_WEIGHT_RESEARCH")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print("AUTO_WEIGHT_CHANGE: DISABLED")
    print("AUTO_PROMOTION: DISABLED")
    print("AUTO_TRADE: DISABLED")
    print(f"SELECTED_SOURCE: {source_path}")
    print(f"SOURCE_ROWS: {len(data_rows)}")
    print(f"OFFICIAL_FACTOR_COUNT: {len(official_factors)}")
    print(f"WEIGHT_CANDIDATE_COUNT: {len(weight_sets)}")
    print(f"LABEL_1D_NONBLANK_COUNT: {label_counts.get(1, 0)}")
    print(f"LABEL_5D_NONBLANK_COUNT: {label_counts.get(5, 0)}")
    print(f"LABEL_10D_NONBLANK_COUNT: {label_counts.get(10, 0)}")
    print(f"LABEL_20D_NONBLANK_COUNT: {label_counts.get(20, 0)}")
    print(f"READY_HORIZON_COUNT: {ready_horizons}")
    print(f"OK_EVALUATED_ROWS: {ok_eval_rows}")
    print(f"INSUFFICIENT_SAMPLE_ROWS: {insufficient_rows}")
    print(f"NO_DATA_ROWS: {no_data_rows}")
    print(f"PROMOTION_PERMISSION: {promotion_permission}")
    print(f"WEIGHT_CANDIDATES: {candidates_path}")
    print(f"EVALUATION: {eval_path}")
    print(f"FACTOR_AUDIT: {factor_audit_path}")
    print(f"SOURCE_AUDIT: {source_audit_path}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first_path}")
    print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
