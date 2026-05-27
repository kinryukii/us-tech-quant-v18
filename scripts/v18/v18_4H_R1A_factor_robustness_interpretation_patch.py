from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs" / "v18" / "factor_backtest"

SUMMARY_IN = OUT_DIR / "V18_4H_R1_CURRENT_FACTOR_ROBUSTNESS_SUMMARY.csv"
MATRIX_IN = OUT_DIR / "V18_4H_R1_CURRENT_ROBUSTNESS_MATRIX.csv"

SUMMARY_OUT = OUT_DIR / "V18_4H_R1A_CURRENT_FACTOR_ROBUSTNESS_INTERPRETATION.csv"
REPORT_OUT = OUT_DIR / "V18_4H_R1A_CURRENT_FACTOR_ROBUSTNESS_INTERPRETATION.md"
CURRENT_OUT = OUT_DIR / "V18_CURRENT_FACTOR_ROBUSTNESS_INTERPRETATION.md"


def read_csv_safe(path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def fmt_pct(x):
    if pd.isna(x):
        return "NA"
    return f"{x * 100:.2f}%"


def classify_alpha_strength(row):
    avg_rank = float(row["avg_rank"])
    top3_rate = float(row["top3_rate"])
    avg_sharpe = float(row["avg_sharpe"])
    avg_cagr = float(row["avg_cagr"])
    top1_count = int(row["top1_count"])

    if avg_rank <= 2.25 and top3_rate >= 0.75 and avg_sharpe >= 1.80 and avg_cagr >= 1.00:
        return "STRONG_ALPHA"

    if avg_rank <= 3.25 and top3_rate >= 0.55 and avg_sharpe >= 1.65 and avg_cagr >= 0.90:
        return "HIGH_ALPHA"

    if avg_rank <= 4.25 and avg_sharpe >= 1.55 and avg_cagr >= 0.75 and top1_count > 0:
        return "MODERATE_ALPHA"

    if avg_sharpe >= 1.35 and avg_cagr >= 0.50:
        return "SECONDARY_ALPHA"

    return "WEAK_ALPHA"


def classify_drawdown_risk(row):
    worst_dd = float(row["worst_max_drawdown"])

    if worst_dd <= -0.65:
        return "EXTREME_DRAWDOWN_RISK"

    if worst_dd <= -0.55:
        return "VERY_HIGH_DRAWDOWN_RISK"

    if worst_dd <= -0.50:
        return "HIGH_DRAWDOWN_RISK"

    if worst_dd <= -0.45:
        return "ELEVATED_DRAWDOWN_RISK"

    return "NORMAL_FOR_HIGH_BETA_TECH"


def classify_promotion_status(row):
    alpha = row["alpha_strength"]
    dd = row["drawdown_risk"]

    if alpha == "STRONG_ALPHA":
        if dd in ("EXTREME_DRAWDOWN_RISK", "VERY_HIGH_DRAWDOWN_RISK", "HIGH_DRAWDOWN_RISK"):
            return "CORE_WATCH_NOT_PROMOTED_DD_BLOCKED"
        return "CORE_CANDIDATE_PENDING_FORWARD_CONFIRMATION"

    if alpha == "HIGH_ALPHA":
        if dd in ("EXTREME_DRAWDOWN_RISK", "VERY_HIGH_DRAWDOWN_RISK", "HIGH_DRAWDOWN_RISK"):
            return "STRONG_CONFIRMATION_WATCH_DD_BLOCKED"
        return "CONFIRMATION_CANDIDATE_PENDING_FORWARD_CONFIRMATION"

    if alpha == "MODERATE_ALPHA":
        return "SECONDARY_EVIDENCE_ONLY"

    if alpha == "SECONDARY_ALPHA":
        return "AUXILIARY_EVIDENCE_ONLY"

    return "NO_PROMOTION_EVIDENCE"


def assign_final_role(factor):
    role_map = {
        "F007_PULLBACK_IN_UPTREND": "CORE_PULLBACK_UPTREND_ALPHA",
        "F009_VOLUME_PRICE_CONFIRM": "PRIMARY_VOLUME_PRICE_CONFIRMATION",
        "F010_XSEC_COMPOSITE_RANK": "COMPOSITE_RANK_STABILIZER",
        "F011_TS_MOMENTUM_60_120": "TREND_CONFIRMATION_ONLY",
        "F008_VOLUME_ABNORMAL_5_20": "VOLUME_ABNORMALITY_AUXILIARY",
        "F006_SHORT_REV_5D": "SHORT_REVERSAL_AUXILIARY",
    }
    return role_map.get(factor, "UNKNOWN")


def make_interpretation(row):
    factor = row["factor"]
    alpha = row["alpha_strength"]
    dd = row["drawdown_risk"]
    promotion = row["promotion_status"]

    if factor == "F007_PULLBACK_IN_UPTREND":
        return (
            "Best historical robustness by average rank and top-3 frequency, "
            "but blocked from promotion because worst drawdown is too deep."
        )

    if factor == "F009_VOLUME_PRICE_CONFIRM":
        return (
            "Strongest confirmation factor; robust enough to be paired with F007, "
            "but still requires forward evidence before promotion."
        )

    if factor == "F010_XSEC_COMPOSITE_RANK":
        return (
            "Useful stabilizer/composite layer. It rarely wins outright, "
            "but frequently remains competitive. Not a standalone trigger."
        )

    if factor == "F011_TS_MOMENTUM_60_120":
        return (
            "Trend confirmation only. Strong in some regimes, but not stable enough "
            "for standalone promotion."
        )

    if factor == "F008_VOLUME_ABNORMAL_5_20":
        return (
            "Volume abnormality is useful as auxiliary evidence, not as the first decision layer."
        )

    if factor == "F006_SHORT_REV_5D":
        return (
            "Short reversal works in selected broader configurations, "
            "but full-matrix robustness is not strong enough for promotion."
        )

    return f"Alpha={alpha}; Drawdown={dd}; Promotion={promotion}"


def write_report(summary: pd.DataFrame, matrix: pd.DataFrame):
    config_count = matrix[["lookback_days", "top_n", "hold_days", "cost_bps"]].drop_duplicates().shape[0]
    matrix_rows = len(matrix)

    lines = []
    lines.append("# V18.4H-R1A 因子稳健性解释修正报告")
    lines.append("")
    lines.append("## 1. 结论")
    lines.append("")
    lines.append("本报告不重新回测，只对 V18.4H-R1 的稳健性审计结果做解释层修正。")
    lines.append("")
    lines.append("核心修正：")
    lines.append("")
    lines.append("```text")
    lines.append("不要把 REC 字段直接理解为因子强弱。")
    lines.append("必须拆成：alpha_strength / drawdown_risk / promotion_status。")
    lines.append("```")
    lines.append("")
    lines.append("## 2. 输入状态")
    lines.append("")
    lines.append(f"- MATRIX_ROWS: `{matrix_rows}`")
    lines.append(f"- CONFIG_COUNT: `{config_count}`")
    lines.append(f"- INPUT_SUMMARY: `{SUMMARY_IN}`")
    lines.append(f"- INPUT_MATRIX: `{MATRIX_IN}`")
    lines.append("")
    lines.append("## 3. 修正后因子解释")
    lines.append("")
    lines.append("| rank | factor | alpha_strength | drawdown_risk | promotion_status | avg_rank | top1 | top3_rate | avg_sharpe | avg_cagr | worst_dd | final_role |")
    lines.append("|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---|")

    for idx, (_, row) in enumerate(summary.iterrows(), start=1):
        lines.append(
            f"| {idx} | {row['factor']} | {row['alpha_strength']} | {row['drawdown_risk']} | "
            f"{row['promotion_status']} | {row['avg_rank']:.2f} | {int(row['top1_count'])} | "
            f"{fmt_pct(row['top3_rate'])} | {row['avg_sharpe']:.3f} | "
            f"{fmt_pct(row['avg_cagr'])} | {fmt_pct(row['worst_max_drawdown'])} | "
            f"{row['final_role']} |"
        )

    lines.append("")
    lines.append("## 4. 当前 promotion 结论")
    lines.append("")
    lines.append("当前不做 official promotion。")
    lines.append("")
    lines.append("原因：")
    lines.append("")
    lines.append("```text")
    lines.append("F007 historical alpha is strong, but drawdown risk is too high.")
    lines.append("F009 is a strong confirmation factor, but still lacks merged forward proof.")
    lines.append("F010 is useful as stabilizer, not standalone trigger.")
    lines.append("Forward tracker evidence has not yet been merged into promotion rules.")
    lines.append("```")
    lines.append("")
    lines.append("## 5. 推荐候选结构")
    lines.append("")
    lines.append("```text")
    lines.append("CORE:        F007_PULLBACK_IN_UPTREND")
    lines.append("CONFIRM:     F009_VOLUME_PRICE_CONFIRM")
    lines.append("STABILIZER:  F010_XSEC_COMPOSITE_RANK")
    lines.append("AUXILIARY:   F011 / F008 / F006")
    lines.append("```")
    lines.append("")
    lines.append("## 6. 下一步")
    lines.append("")
    lines.append("进入 V18.4I：把 V18.4H-R1A 历史稳健性解释结果与 V18.4A/V18.4B forward tracker 合并。")
    lines.append("")
    lines.append("V18.4I 的目标不是直接买入，而是生成：")
    lines.append("")
    lines.append("```text")
    lines.append("BACKTEST_FORWARD_PROMOTION_EVIDENCE")
    lines.append("PROMOTION_CANDIDATE_CLUSTER")
    lines.append("OFFICIAL_DECISION_IMPACT = NONE unless future rules explicitly promote")
    lines.append("```")

    text = "\n".join(lines)
    REPORT_OUT.write_text(text, encoding="utf-8")
    CURRENT_OUT.write_text(text, encoding="utf-8")


def main():
    if not SUMMARY_IN.exists():
        raise FileNotFoundError(f"Missing input summary: {SUMMARY_IN}")

    if not MATRIX_IN.exists():
        raise FileNotFoundError(f"Missing input matrix: {MATRIX_IN}")

    summary = read_csv_safe(SUMMARY_IN)
    matrix = read_csv_safe(MATRIX_IN)

    summary["alpha_strength"] = summary.apply(classify_alpha_strength, axis=1)
    summary["drawdown_risk"] = summary.apply(classify_drawdown_risk, axis=1)
    summary["promotion_status"] = summary.apply(classify_promotion_status, axis=1)
    summary["final_role"] = summary["factor"].apply(assign_final_role)
    summary["interpretation"] = summary.apply(make_interpretation, axis=1)
    summary["official_decision_impact"] = "NONE"

    alpha_order = {
        "STRONG_ALPHA": 5,
        "HIGH_ALPHA": 4,
        "MODERATE_ALPHA": 3,
        "SECONDARY_ALPHA": 2,
        "WEAK_ALPHA": 1,
    }

    summary["_alpha_order"] = summary["alpha_strength"].map(alpha_order).fillna(0)
    summary = summary.sort_values(
        ["_alpha_order", "avg_rank", "top3_rate", "avg_sharpe"],
        ascending=[False, True, False, False],
    ).drop(columns=["_alpha_order"])

    summary.to_csv(SUMMARY_OUT, index=False, encoding="utf-8-sig")
    write_report(summary, matrix)

    print("")
    print("=== V18.4H-R1A FACTOR ROBUSTNESS INTERPRETATION READY ===")
    print(f"INPUT_SUMMARY: {SUMMARY_IN}")
    print(f"INPUT_MATRIX: {MATRIX_IN}")
    print(f"OUTPUT_SUMMARY: {SUMMARY_OUT}")
    print(f"REPORT: {REPORT_OUT}")
    print(f"CURRENT: {CURRENT_OUT}")

    print("")
    print("=== INTERPRETATION SUMMARY ===")

    for _, row in summary.iterrows():
        print(
            f"{row['factor']}: "
            f"ALPHA={row['alpha_strength']}, "
            f"DD={row['drawdown_risk']}, "
            f"PROMOTION={row['promotion_status']}, "
            f"ROLE={row['final_role']}"
        )


if __name__ == "__main__":
    main()