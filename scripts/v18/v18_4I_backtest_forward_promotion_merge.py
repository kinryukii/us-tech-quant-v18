from pathlib import Path
from datetime import datetime
import re
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[2]

OUT_DIR = ROOT / "outputs" / "v18" / "promotion_merge"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BACKTEST_INTERP = ROOT / "outputs" / "v18" / "factor_backtest" / "V18_4H_R1A_CURRENT_FACTOR_ROBUSTNESS_INTERPRETATION.csv"

MERGE_OUT = OUT_DIR / "V18_4I_CURRENT_BACKTEST_FORWARD_PROMOTION_MERGE.csv"
CLUSTER_OUT = OUT_DIR / "V18_4I_CURRENT_PROMOTION_CLUSTER.csv"
REPORT_OUT = OUT_DIR / "V18_4I_CURRENT_BACKTEST_FORWARD_PROMOTION_REPORT.md"
CURRENT_OUT = OUT_DIR / "V18_CURRENT_BACKTEST_FORWARD_PROMOTION.md"
READ_FIRST_OUT = OUT_DIR / "V18_4I_READ_FIRST.txt"


def read_csv_safe(path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def read_text_safe(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def fmt_pct(x):
    try:
        if pd.isna(x):
            return "NA"
        return f"{float(x) * 100:.2f}%"
    except Exception:
        return "NA"


def find_existing_files(candidates):
    return [p for p in candidates if p.exists()]


def newest_csv_matching(root_dirs, keywords):
    hits = []
    for root_dir in root_dirs:
        if not root_dir.exists():
            continue
        for p in root_dir.rglob("*.csv"):
            name = p.name.lower()
            if all(k.lower() in name for k in keywords):
                hits.append(p)
    hits = sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)
    return hits


def discover_forward_csv_sources():
    exact_candidates = [
        ROOT / "outputs" / "v18" / "outcome_summary" / "V18_4B_CURRENT_FACTOR_OUTCOME_SUMMARY.csv",
        ROOT / "outputs" / "v18" / "outcome_summary" / "V18_4B_CURRENT_PROMOTION_RULES.csv",
        ROOT / "state" / "v18" / "V18_4A_CURRENT_FACTOR_FORWARD_OUTCOME_TRACKER.csv",
        ROOT / "state" / "v18" / "V18_4A_FACTOR_FORWARD_OUTCOME_TRACKER.csv",
        ROOT / "state" / "v18" / "V18_4F_CURRENT_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT.csv",
    ]

    found = find_existing_files(exact_candidates)

    discovered = []
    discovered += newest_csv_matching([ROOT / "outputs" / "v18", ROOT / "state" / "v18"], ["factor", "outcome"])
    discovered += newest_csv_matching([ROOT / "outputs" / "v18", ROOT / "state" / "v18"], ["factor", "forward"])
    discovered += newest_csv_matching([ROOT / "outputs" / "v18", ROOT / "state" / "v18"], ["promotion"])

    seen = set()
    ordered = []
    for p in found + discovered:
        key = str(p).lower()
        if key not in seen:
            ordered.append(p)
            seen.add(key)

    return ordered


def discover_text_sources():
    candidates = [
        ROOT / "outputs" / "v18" / "outcome_summary" / "V18_CURRENT_FACTOR_OUTCOME_PROMOTION.md",
        ROOT / "outputs" / "v18" / "outcome_summary" / "V18_4B_CURRENT_PROMOTION_RULES.md",
        ROOT / "outputs" / "v18" / "daily_integrated" / "V18_CURRENT_FINAL_DAILY.md",
        ROOT / "outputs" / "v18" / "daily_integrated" / "V18_4B_R1_READ_FIRST.txt",
        ROOT / "outputs" / "v18" / "factor_backtest" / "V18_CURRENT_FACTOR_ROBUSTNESS_INTERPRETATION.md",
    ]
    return find_existing_files(candidates)


def parse_key_values_from_text(text):
    kv = {}
    for raw in text.splitlines():
        line = raw.strip()
        line = line.lstrip("-").strip()
        if ":" not in line:
            continue

        left, right = line.split(":", 1)
        key = left.strip().strip("`").upper()
        value = right.strip().strip("`").strip()

        if key and len(key) <= 80:
            kv[key] = value

    return kv


def collect_global_context():
    text_sources = discover_text_sources()
    combined_text = []
    kv = {}

    for p in text_sources:
        text = read_text_safe(p)
        combined_text.append(f"\n\n--- SOURCE: {p} ---\n{text}")
        kv.update(parse_key_values_from_text(text))

    return {
        "text_sources": text_sources,
        "text": "\n".join(combined_text),
        "kv": kv,
    }


def detect_global_forward_gate(kv):
    promo_rec = str(kv.get("PROMOTION_RECOMMENDATION", "UNKNOWN"))
    promo_action = str(kv.get("PROMOTION_ACTION", "UNKNOWN"))
    official_impact = str(kv.get("OFFICIAL_DECISION_IMPACT", "UNKNOWN"))

    text = f"{promo_rec} {promo_action} {official_impact}".upper()

    if "PROMOTION_ACTION" in text and "NONE" not in text:
        return "FORWARD_PROMOTION_ACTION_PRESENT"

    if "NO_PROMOTION_DATA_INSUFFICIENT" in text:
        return "FORWARD_DATA_INSUFFICIENT"

    if "KEEP_WATCHING" in text:
        return "FORWARD_KEEP_WATCHING_NO_PROMOTION"

    if "NO_PROMOTION" in text:
        return "FORWARD_NO_PROMOTION"

    if "PROMOTION" in text and "NO" not in text:
        return "FORWARD_PROMOTION_CANDIDATE_GLOBAL"

    return "FORWARD_STATUS_UNKNOWN"


def load_best_forward_df():
    sources = discover_forward_csv_sources()

    for p in sources:
        try:
            df = read_csv_safe(p)
            if df is not None and not df.empty:
                return df, p, sources
        except Exception:
            continue

    return pd.DataFrame(), None, sources


def match_forward_row(forward_df: pd.DataFrame, factor: str):
    if forward_df is None or forward_df.empty:
        return None

    factor_upper = str(factor).upper()

    for _, row in forward_df.iterrows():
        joined = " ".join(str(x).upper() for x in row.values)
        if factor_upper in joined:
            return row

    short_id = factor_upper.split("_")[0]
    if short_id.startswith("F") and len(short_id) <= 4:
        for _, row in forward_df.iterrows():
            joined = " ".join(str(x).upper() for x in row.values)
            if short_id in joined:
                return row

    return None


def infer_forward_evidence(forward_df, factor):
    if forward_df is None or forward_df.empty:
        return {
            "forward_factor_row_found": False,
            "forward_status": "FORWARD_SOURCE_EMPTY_OR_MISSING",
            "forward_completed_observation_max": np.nan,
            "forward_text_hit": "",
        }

    row = match_forward_row(forward_df, factor)

    if row is None:
        return {
            "forward_factor_row_found": False,
            "forward_status": "FORWARD_NOT_FACTOR_SPECIFIC",
            "forward_completed_observation_max": np.nan,
            "forward_text_hit": "",
        }

    numeric_values = []
    for col, val in row.items():
        c = str(col).lower()
        if any(k in c for k in ["completed", "observation", "obs", "count", "n_"]):
            try:
                numeric_values.append(float(val))
            except Exception:
                pass

    completed_max = max(numeric_values) if numeric_values else np.nan
    row_text = " ".join(str(x) for x in row.values)
    row_text_upper = row_text.upper()

    if "PROMOTION" in row_text_upper and "NO_PROMOTION" not in row_text_upper:
        status = "FORWARD_ROW_PROMOTION_SIGNAL_PRESENT"
    elif "KEEP_WATCHING" in row_text_upper:
        status = "FORWARD_ROW_KEEP_WATCHING"
    elif "INSUFFICIENT" in row_text_upper:
        status = "FORWARD_ROW_DATA_INSUFFICIENT"
    else:
        status = "FORWARD_ROW_FOUND_UNCLASSIFIED"

    return {
        "forward_factor_row_found": True,
        "forward_status": status,
        "forward_completed_observation_max": completed_max,
        "forward_text_hit": row_text[:300],
    }


def alpha_score(alpha_strength):
    return {
        "STRONG_ALPHA": 5,
        "HIGH_ALPHA": 4,
        "MODERATE_ALPHA": 3,
        "SECONDARY_ALPHA": 2,
        "WEAK_ALPHA": 1,
    }.get(str(alpha_strength), 0)


def drawdown_penalty(drawdown_risk):
    return {
        "EXTREME_DRAWDOWN_RISK": 3.0,
        "VERY_HIGH_DRAWDOWN_RISK": 2.5,
        "HIGH_DRAWDOWN_RISK": 2.0,
        "ELEVATED_DRAWDOWN_RISK": 1.25,
        "NORMAL_FOR_HIGH_BETA_TECH": 0.5,
    }.get(str(drawdown_risk), 1.5)


def assign_cluster_role(factor, alpha_strength, drawdown_risk):
    if factor == "F007_PULLBACK_IN_UPTREND":
        return "CORE_ALPHA_WATCH"
    if factor == "F009_VOLUME_PRICE_CONFIRM":
        return "PRIMARY_CONFIRMATION_WATCH"
    if factor == "F010_XSEC_COMPOSITE_RANK":
        return "AUXILIARY_STABILIZER_ONLY"
    if factor == "F011_TS_MOMENTUM_60_120":
        return "AUXILIARY_TREND_CONFIRMATION"
    if factor == "F008_VOLUME_ABNORMAL_5_20":
        return "AUXILIARY_VOLUME_ABNORMALITY"
    if factor == "F006_SHORT_REV_5D":
        return "AUXILIARY_SHORT_REVERSAL"
    return "UNCLASSIFIED"


def classify_merged_status(row, global_forward_gate):
    factor = row["factor"]
    alpha = row["alpha_strength"]
    dd = row["drawdown_risk"]

    dd_blocked = dd in (
        "EXTREME_DRAWDOWN_RISK",
        "VERY_HIGH_DRAWDOWN_RISK",
        "HIGH_DRAWDOWN_RISK",
    )

    forward_pending = global_forward_gate in (
        "FORWARD_DATA_INSUFFICIENT",
        "FORWARD_KEEP_WATCHING_NO_PROMOTION",
        "FORWARD_NO_PROMOTION",
        "FORWARD_STATUS_UNKNOWN",
    )

    if factor == "F007_PULLBACK_IN_UPTREND":
        return "CORE_WATCH_NOT_PROMOTED_DD_AND_FORWARD_BLOCKED"

    if factor == "F009_VOLUME_PRICE_CONFIRM":
        return "PRIMARY_CONFIRMATION_WATCH_NOT_PROMOTED_DD_AND_FORWARD_BLOCKED"

    if alpha in ("STRONG_ALPHA", "HIGH_ALPHA") and dd_blocked:
        return "WATCH_NOT_PROMOTED_DRAWDOWN_BLOCKED"

    if alpha in ("MODERATE_ALPHA", "SECONDARY_ALPHA"):
        return "AUXILIARY_EVIDENCE_ONLY"

    if forward_pending:
        return "NO_PROMOTION_FORWARD_PENDING"

    return "NO_PROMOTION"


def build_merge():
    if not BACKTEST_INTERP.exists():
        raise FileNotFoundError(f"Missing V18.4H-R1A interpretation file: {BACKTEST_INTERP}")

    interp = read_csv_safe(BACKTEST_INTERP)
    forward_df, forward_source, all_forward_sources = load_best_forward_df()
    global_context = collect_global_context()
    kv = global_context["kv"]
    global_forward_gate = detect_global_forward_gate(kv)

    rows = []

    for _, r in interp.iterrows():
        factor = str(r.get("factor", "")).strip()

        forward_info = infer_forward_evidence(forward_df, factor)

        alpha = str(r.get("alpha_strength", "UNKNOWN"))
        dd = str(r.get("drawdown_risk", "UNKNOWN"))
        promotion_status = str(r.get("promotion_status", "UNKNOWN"))
        final_role = str(r.get("final_role", "UNKNOWN"))

        a_score = alpha_score(alpha)
        dd_pen = drawdown_penalty(dd)
        evidence_score = a_score - dd_pen

        row = {
            "factor": factor,
            "alpha_strength": alpha,
            "drawdown_risk": dd,
            "historical_promotion_status": promotion_status,
            "historical_final_role": final_role,
            "avg_rank": r.get("avg_rank", np.nan),
            "top1_count": r.get("top1_count", np.nan),
            "top3_rate": r.get("top3_rate", np.nan),
            "avg_sharpe": r.get("avg_sharpe", np.nan),
            "avg_cagr": r.get("avg_cagr", np.nan),
            "worst_max_drawdown": r.get("worst_max_drawdown", np.nan),
            "alpha_score": a_score,
            "drawdown_penalty": dd_pen,
            "historical_net_evidence_score": evidence_score,
            "global_forward_gate": global_forward_gate,
            "global_promotion_recommendation": kv.get("PROMOTION_RECOMMENDATION", "UNKNOWN"),
            "global_promotion_action": kv.get("PROMOTION_ACTION", "UNKNOWN"),
            "global_official_decision_impact": kv.get("OFFICIAL_DECISION_IMPACT", "UNKNOWN"),
            "forward_source": str(forward_source) if forward_source else "NONE",
            **forward_info,
        }

        row["cluster_role"] = assign_cluster_role(factor, alpha, dd)
        row["merged_promotion_status"] = classify_merged_status(row, global_forward_gate)
        row["official_decision_impact"] = "NONE"
        row["promotion_action"] = "NONE"

        rows.append(row)

    merge = pd.DataFrame(rows)

    role_priority = {
        "CORE_ALPHA_WATCH": 1,
        "PRIMARY_CONFIRMATION_WATCH": 2,
        "AUXILIARY_STABILIZER_ONLY": 3,
        "AUXILIARY_TREND_CONFIRMATION": 4,
        "AUXILIARY_VOLUME_ABNORMALITY": 5,
        "AUXILIARY_SHORT_REVERSAL": 6,
    }

    merge["_role_priority"] = merge["cluster_role"].map(role_priority).fillna(99)
    merge = merge.sort_values(
        ["_role_priority", "historical_net_evidence_score", "avg_rank"],
        ascending=[True, False, True],
    ).drop(columns=["_role_priority"])

    cluster = merge[
        merge["cluster_role"].isin([
            "CORE_ALPHA_WATCH",
            "PRIMARY_CONFIRMATION_WATCH",
            "AUXILIARY_STABILIZER_ONLY",
            "AUXILIARY_TREND_CONFIRMATION",
            "AUXILIARY_VOLUME_ABNORMALITY",
            "AUXILIARY_SHORT_REVERSAL",
        ])
    ].copy()

    return merge, cluster, {
        "forward_source": forward_source,
        "all_forward_sources": all_forward_sources,
        "global_context": global_context,
        "global_forward_gate": global_forward_gate,
    }


def write_report(merge, cluster, meta):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    forward_source = meta["forward_source"]
    global_forward_gate = meta["global_forward_gate"]
    text_sources = meta["global_context"]["text_sources"]
    kv = meta["global_context"]["kv"]

    core_rows = cluster[cluster["cluster_role"] == "CORE_ALPHA_WATCH"]
    confirm_rows = cluster[cluster["cluster_role"] == "PRIMARY_CONFIRMATION_WATCH"]

    core = ", ".join(core_rows["factor"].tolist()) if not core_rows.empty else "NONE"
    confirm = ", ".join(confirm_rows["factor"].tolist()) if not confirm_rows.empty else "NONE"

    lines = []
    lines.append("# V18.4I Backtest-Forward Promotion Merge")
    lines.append("")
    lines.append(f"生成时间：{now}")
    lines.append("")
    lines.append("## 1. 结论")
    lines.append("")
    lines.append("- V18_4I_STATUS: `OK_BACKTEST_FORWARD_PROMOTION_MERGE_READY`")
    lines.append("- OFFICIAL_DECISION_IMPACT: `NONE`")
    lines.append("- PROMOTION_ACTION: `NONE`")
    lines.append("- DIRECT_PROMOTION: `NO`")
    lines.append(f"- GLOBAL_FORWARD_GATE: `{global_forward_gate}`")
    lines.append(f"- CORE_ALPHA_WATCH: `{core}`")
    lines.append(f"- PRIMARY_CONFIRMATION_WATCH: `{confirm}`")
    lines.append("")
    lines.append("当前结论：")
    lines.append("")
    lines.append("```text")
    lines.append("F007 是历史强 alpha，但被回撤和 forward 成熟度阻挡。")
    lines.append("F009 是主要确认因子，但同样不能单独 promotion。")
    lines.append("F010/F011/F008/F006 只作为辅助证据，不直接触发 official decision。")
    lines.append("```")
    lines.append("")
    lines.append("## 2. 输入来源")
    lines.append("")
    lines.append(f"- BACKTEST_INTERPRETATION: `{BACKTEST_INTERP}`")
    lines.append(f"- FORWARD_SOURCE_USED: `{forward_source if forward_source else 'NONE'}`")
    lines.append("")
    lines.append("文本上下文来源：")
    lines.append("")
    for p in text_sources:
        lines.append(f"- `{p}`")
    lines.append("")
    lines.append("## 3. 全局 promotion context")
    lines.append("")
    lines.append(f"- PROMOTION_RECOMMENDATION: `{kv.get('PROMOTION_RECOMMENDATION', 'UNKNOWN')}`")
    lines.append(f"- PROMOTION_ACTION: `{kv.get('PROMOTION_ACTION', 'UNKNOWN')}`")
    lines.append(f"- OFFICIAL_DECISION_IMPACT: `{kv.get('OFFICIAL_DECISION_IMPACT', 'UNKNOWN')}`")
    lines.append("")
    lines.append("## 4. 合并后因子状态")
    lines.append("")
    lines.append("| rank | factor | cluster_role | alpha | drawdown | merged_status | avg_rank | top3_rate | avg_sharpe | avg_cagr | worst_dd | official_impact |")
    lines.append("|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---|")

    for idx, (_, row) in enumerate(merge.iterrows(), start=1):
        lines.append(
            f"| {idx} | {row['factor']} | {row['cluster_role']} | "
            f"{row['alpha_strength']} | {row['drawdown_risk']} | {row['merged_promotion_status']} | "
            f"{float(row['avg_rank']):.2f} | {fmt_pct(row['top3_rate'])} | "
            f"{float(row['avg_sharpe']):.3f} | {fmt_pct(row['avg_cagr'])} | "
            f"{fmt_pct(row['worst_max_drawdown'])} | {row['official_decision_impact']} |"
        )

    lines.append("")
    lines.append("## 5. Promotion cluster")
    lines.append("")
    lines.append("```text")
    lines.append("CORE:        F007_PULLBACK_IN_UPTREND")
    lines.append("CONFIRM:     F009_VOLUME_PRICE_CONFIRM")
    lines.append("AUXILIARY:   F010 / F011 / F008 / F006")
    lines.append("ACTION:      WATCH_NOT_PROMOTED")
    lines.append("IMPACT:      OFFICIAL_DECISION_IMPACT = NONE")
    lines.append("```")
    lines.append("")
    lines.append("## 6. 下一步")
    lines.append("")
    lines.append("下一步不是直接 promotion，而是做 V18.4I-R1：把本 merge 报告接入 final daily wrapper，使每天自动刷新 promotion evidence。")
    lines.append("接入后仍然不允许绕过 event gate、budget lock、behavior guard 和 official daily decision。")

    text = "\n".join(lines)
    REPORT_OUT.write_text(text, encoding="utf-8")
    CURRENT_OUT.write_text(text, encoding="utf-8")

    read_first = []
    read_first.append("V18_4I_STATUS: OK_BACKTEST_FORWARD_PROMOTION_MERGE_READY")
    read_first.append("DIRECT_PROMOTION: NO")
    read_first.append("OFFICIAL_DECISION_IMPACT: NONE")
    read_first.append("PROMOTION_ACTION: NONE")
    read_first.append(f"GLOBAL_FORWARD_GATE: {global_forward_gate}")
    read_first.append("CORE_ALPHA_WATCH: F007_PULLBACK_IN_UPTREND")
    read_first.append("PRIMARY_CONFIRMATION_WATCH: F009_VOLUME_PRICE_CONFIRM")
    read_first.append(f"REPORT: {REPORT_OUT}")
    read_first.append(f"MERGE_CSV: {MERGE_OUT}")
    read_first.append(f"CLUSTER_CSV: {CLUSTER_OUT}")

    READ_FIRST_OUT.write_text("\n".join(read_first), encoding="utf-8")


def main():
    merge, cluster, meta = build_merge()

    merge.to_csv(MERGE_OUT, index=False, encoding="utf-8-sig")
    cluster.to_csv(CLUSTER_OUT, index=False, encoding="utf-8-sig")

    write_report(merge, cluster, meta)

    print("")
    print("=== V18.4I BACKTEST-FORWARD PROMOTION MERGE READY ===")
    print(f"MERGE_ROWS: {len(merge)}")
    print(f"CLUSTER_ROWS: {len(cluster)}")
    print(f"GLOBAL_FORWARD_GATE: {meta['global_forward_gate']}")
    print(f"FORWARD_SOURCE_USED: {meta['forward_source'] if meta['forward_source'] else 'NONE'}")
    print(f"MERGE: {MERGE_OUT}")
    print(f"CLUSTER: {CLUSTER_OUT}")
    print(f"REPORT: {REPORT_OUT}")
    print(f"CURRENT: {CURRENT_OUT}")
    print(f"READ_FIRST: {READ_FIRST_OUT}")

    print("")
    print("=== V18.4I MERGED PROMOTION STATUS ===")
    for _, row in merge.iterrows():
        print(
            f"{row['factor']}: "
            f"ROLE={row['cluster_role']}, "
            f"ALPHA={row['alpha_strength']}, "
            f"DD={row['drawdown_risk']}, "
            f"MERGED={row['merged_promotion_status']}, "
            f"IMPACT={row['official_decision_impact']}"
        )


if __name__ == "__main__":
    main()