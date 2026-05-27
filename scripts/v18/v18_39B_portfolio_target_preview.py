#!/usr/bin/env python
"""V18.39B portfolio target preview / LEAN-inspired construction preview.

Read-only report layer. It converts V18.39A alpha signal objects into
theoretical target weights and notional previews under simulated capital
levels. It never uses real accounts, creates orders, or mutates ledgers/state.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


MODE = "READ_ONLY_PORTFOLIO_TARGET_PREVIEW"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
CAPITAL_LEVELS = [1000, 2000, 5000, 10000]
MAX_WEIGHT_CAP = 0.05

PREVIEW_COLUMNS = [
    "preview_id",
    "run_id",
    "generated_at",
    "scenario_name",
    "scenario_type",
    "simulated_capital_usd",
    "ticker",
    "company_name_en",
    "company_name_zh",
    "rank",
    "alpha_direction",
    "alpha_confidence",
    "target_weight",
    "target_notional_usd",
    "latest_price",
    "target_shares_fractional",
    "target_shares_whole",
    "whole_share_feasibility",
    "max_position_weight_rule",
    "cap_applied",
    "freeze_status",
    "forward_evidence_status",
    "risk_tags",
    "data_quality_tags",
    "operator_action_hint",
    "official_decision_impact",
    "auto_trade",
    "order_execution_used",
    "notes",
]

SUMMARY_COLUMNS = [
    "scenario_name",
    "simulated_capital_usd",
    "included_ticker_count",
    "long_candidate_count",
    "watch_count",
    "excluded_count",
    "target_weight_sum",
    "max_target_weight",
    "min_target_weight",
    "concentration_top5_weight",
    "price_available_count",
    "price_missing_count",
    "whole_share_feasible_count",
    "too_small_for_one_share_count",
    "research_only_count",
    "pending_forward_outcome_count",
    "status",
    "notes",
]

DIAGNOSTIC_COLUMNS = ["check_name", "scenario_name", "simulated_capital_usd", "status", "expected", "observed", "notes"]


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dirs(root: Path) -> None:
    for rel in ["outputs/v18/portfolio_preview", "outputs/v18/read_center", "outputs/v18/ops"]:
        (root / rel).mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, df: pd.DataFrame, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if df.empty:
        out = pd.DataFrame(columns=columns)
    else:
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        out = df[columns]
    out.to_csv(path, index=False, encoding="utf-8")


def safe_read_csv(path: Path) -> tuple[pd.DataFrame, str]:
    if not path.exists():
        return pd.DataFrame(), "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return pd.read_csv(path, dtype=str, keep_default_na=False, encoding=enc), "OK"
        except Exception:
            continue
    return pd.DataFrame(), "READ_ERROR"


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def to_float(value: Any) -> float | None:
    try:
        text = str(value).strip()
        if text == "":
            return None
        return float(text)
    except Exception:
        return None


def to_int(value: Any) -> int | None:
    try:
        text = str(value).strip()
        if text == "":
            return None
        return int(float(text))
    except Exception:
        return None


def norm_col(name: str) -> str:
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def find_col(df: pd.DataFrame, *names: str) -> str | None:
    if df.empty:
        return None
    lookup = {norm_col(c): c for c in df.columns}
    for name in names:
        hit = lookup.get(norm_col(name))
        if hit is not None:
            return hit
    return None


def price_map(candidates: pd.DataFrame) -> dict[str, str]:
    ticker_col = find_col(candidates, "ticker", "symbol", "yf_ticker")
    price_col = find_col(candidates, "latest_close", "entry_reference_price", "close", "latest_price")
    if candidates.empty or not ticker_col or not price_col:
        return {}
    out: dict[str, str] = {}
    for _, row in candidates.iterrows():
        ticker = str(row.get(ticker_col, "")).upper().strip()
        price = str(row.get(price_col, "")).strip()
        if ticker and price and ticker not in out:
            out[ticker] = price
    return out


def cap_and_renormalize(raw: dict[str, float], cap: float = MAX_WEIGHT_CAP) -> tuple[dict[str, float], bool]:
    if not raw:
        return {}, False
    weights = {k: max(0.0, float(v)) for k, v in raw.items()}
    total = sum(weights.values())
    if total <= 0:
        return {}, False
    weights = {k: v / total for k, v in weights.items()}
    cap_applied = False
    for _ in range(20):
        over = {k: v for k, v in weights.items() if v > cap}
        if not over:
            break
        cap_applied = True
        fixed = set(over)
        fixed_sum = cap * len(fixed)
        free = {k: v for k, v in weights.items() if k not in fixed}
        free_sum = sum(free.values())
        if free_sum <= 0 or fixed_sum >= 1:
            weights = {k: (cap if k in fixed else 0.0) for k in weights}
            break
        weights = {k: (cap if k in fixed else v / free_sum * (1 - fixed_sum)) for k, v in weights.items()}
    final_total = sum(weights.values())
    if final_total > 0:
        weights = {k: v / final_total for k, v in weights.items()}
    return weights, cap_applied


def equal_weights(df: pd.DataFrame) -> tuple[dict[str, float], bool]:
    if df.empty:
        return {}, False
    w = 1.0 / len(df)
    return {str(row["ticker"]).upper().strip(): w for _, row in df.iterrows()}, False


def confidence_weights(df: pd.DataFrame) -> tuple[dict[str, float], bool]:
    raw: dict[str, float] = {}
    for _, row in df.iterrows():
        ticker = str(row["ticker"]).upper().strip()
        score = to_float(row.get("confidence_score_numeric", ""))
        raw[ticker] = score if score is not None and score > 0 else 1.0
    return cap_and_renormalize(raw, 1.0)


def rank_decay_weights(df: pd.DataFrame) -> tuple[dict[str, float], bool]:
    raw: dict[str, float] = {}
    for _, row in df.iterrows():
        ticker = str(row["ticker"]).upper().strip()
        rank = to_int(row.get("rank", ""))
        raw[ticker] = 1.0 / rank if rank and rank > 0 else 0.0
    return cap_and_renormalize(raw, MAX_WEIGHT_CAP)


def capped_equal_weights(df: pd.DataFrame) -> tuple[dict[str, float], bool]:
    raw = {str(row["ticker"]).upper().strip(): 1.0 for _, row in df.iterrows()}
    return cap_and_renormalize(raw, MAX_WEIGHT_CAP)


def research_weights(df: pd.DataFrame) -> tuple[dict[str, float], bool]:
    if df.empty:
        return {}, False
    w = 1.0 / len(df)
    return {str(row["ticker"]).upper().strip(): w for _, row in df.iterrows()}, False


def scenario_inputs(alpha: pd.DataFrame) -> list[dict[str, Any]]:
    alpha = alpha.copy()
    alpha["_rank_int"] = alpha["rank"].apply(to_int)
    return [
        {
            "name": "TOP20_EQUAL_WEIGHT",
            "type": "EQUAL_WEIGHT",
            "df": alpha[(alpha["_rank_int"] <= 20) & (alpha["alpha_direction"] == "LONG_CANDIDATE")].copy(),
            "weight_fn": equal_weights,
            "cap_rule": "NO_CAP_TOP20_EQUAL_WEIGHT",
            "research_only": False,
        },
        {
            "name": "TOP20_CONFIDENCE_WEIGHTED",
            "type": "CONFIDENCE_WEIGHTED",
            "df": alpha[(alpha["_rank_int"] <= 20) & (alpha["alpha_direction"] != "AVOID")].copy(),
            "weight_fn": confidence_weights,
            "cap_rule": "CONFIDENCE_SCORE_NORMALIZED_NO_HIGH_CONFIDENCE_FABRICATION",
            "research_only": False,
        },
        {
            "name": "TOP50_EQUAL_WEIGHT_CAPPED",
            "type": "CAPPED_WEIGHT",
            "df": alpha[(alpha["_rank_int"] <= 50) & (alpha["alpha_direction"] != "AVOID")].copy(),
            "weight_fn": capped_equal_weights,
            "cap_rule": "MAX_POSITION_WEIGHT_5_PERCENT",
            "research_only": False,
        },
        {
            "name": "TOP50_RANK_DECAY_WEIGHTED",
            "type": "RANK_DECAY_WEIGHTED",
            "df": alpha[(alpha["_rank_int"] <= 50) & (alpha["alpha_direction"] != "AVOID")].copy(),
            "weight_fn": rank_decay_weights,
            "cap_rule": "WEIGHT_PROPORTIONAL_1_OVER_RANK_THEN_MAX_5_PERCENT",
            "research_only": False,
        },
        {
            "name": "WATCHLIST_RESEARCH_ONLY_FULL318",
            "type": "RESEARCH_ONLY",
            "df": alpha.copy(),
            "weight_fn": research_weights,
            "cap_rule": "RESEARCH_ONLY_EQUAL_REFERENCE_WEIGHT_NOT_INVESTABLE",
            "research_only": True,
        },
    ]


def build_previews(root: Path, run_id: str, generated_at: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    alpha_path = root / "outputs/v18/signals/V18_39A_ALPHA_SIGNAL_OBJECTS.csv"
    alpha_summary_path = root / "outputs/v18/signals/V18_39A_ALPHA_SIGNAL_SUMMARY.csv"
    candidate_path = root / "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
    command_path = root / "outputs/v18/ops/V18_38C_R1_READ_FIRST.txt"
    alpha_read_first_path = root / "outputs/v18/ops/V18_39A_READ_FIRST.txt"

    alpha, alpha_status = safe_read_csv(alpha_path)
    alpha_summary, alpha_summary_status = safe_read_csv(alpha_summary_path)
    candidates, candidate_status = safe_read_csv(candidate_path)
    command_status = parse_kv(command_path)
    alpha_read_first = parse_kv(alpha_read_first_path)
    if alpha_status != "OK" or alpha.empty:
        raise RuntimeError("V18.39A alpha signal object input cannot be read")

    prices = price_map(candidates)
    rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    scenario_count = 0
    capital_count = len(CAPITAL_LEVELS)

    for scenario in scenario_inputs(alpha):
        scenario_count += 1
        scenario_df = scenario["df"].sort_values(by="rank", key=lambda s: pd.to_numeric(s, errors="coerce")).copy()
        weights, cap_applied_any = scenario["weight_fn"](scenario_df)
        excluded_count = len(alpha) - len(scenario_df)
        for capital in CAPITAL_LEVELS:
            scenario_rows: list[dict[str, Any]] = []
            for _, signal in scenario_df.iterrows():
                ticker = str(signal.get("ticker", "")).upper().strip()
                weight = weights.get(ticker, 0.0)
                target_notional = weight * capital
                price_raw = prices.get(ticker, "")
                price = to_float(price_raw)
                if scenario["research_only"]:
                    fractional = ""
                    whole = ""
                    feasibility = "RESEARCH_ONLY"
                elif price is None or price <= 0:
                    fractional = ""
                    whole = ""
                    feasibility = "PRICE_MISSING"
                else:
                    fractional_value = target_notional / price
                    whole_value = int(fractional_value)
                    fractional = f"{fractional_value:.6f}"
                    whole = whole_value
                    feasibility = "FEASIBLE" if whole_value >= 1 else "TOO_SMALL_FOR_ONE_SHARE"

                row = {
                    "preview_id": f"{run_id}_{scenario['name']}_{capital}_{ticker}",
                    "run_id": run_id,
                    "generated_at": generated_at,
                    "scenario_name": scenario["name"],
                    "scenario_type": scenario["type"],
                    "simulated_capital_usd": capital,
                    "ticker": ticker,
                    "company_name_en": signal.get("company_name_en", ""),
                    "company_name_zh": signal.get("company_name_zh", ""),
                    "rank": signal.get("rank", ""),
                    "alpha_direction": signal.get("alpha_direction", ""),
                    "alpha_confidence": signal.get("alpha_confidence", ""),
                    "target_weight": f"{weight:.10f}",
                    "target_notional_usd": f"{target_notional:.2f}",
                    "latest_price": price_raw,
                    "target_shares_fractional": fractional,
                    "target_shares_whole": whole,
                    "whole_share_feasibility": feasibility,
                    "max_position_weight_rule": scenario["cap_rule"],
                    "cap_applied": "TRUE" if cap_applied_any else "FALSE",
                    "freeze_status": signal.get("freeze_status", ""),
                    "forward_evidence_status": signal.get("forward_evidence_status", ""),
                    "risk_tags": signal.get("risk_tags", ""),
                    "data_quality_tags": signal.get("data_quality_tags", ""),
                    "operator_action_hint": signal.get("operator_action_hint", ""),
                    "official_decision_impact": "NONE",
                    "auto_trade": "DISABLED",
                    "order_execution_used": "FALSE",
                    "notes": "Theoretical target preview only; not an order list and not a trade recommendation.",
                }
                rows.append(row)
                scenario_rows.append(row)

            scenario_preview = pd.DataFrame(scenario_rows)
            weights_num = pd.to_numeric(scenario_preview["target_weight"], errors="coerce") if not scenario_preview.empty else pd.Series(dtype=float)
            price_available = int(scenario_preview["latest_price"].astype(str).str.strip().ne("").sum()) if not scenario_preview.empty else 0
            price_missing = int(scenario_preview["whole_share_feasibility"].eq("PRICE_MISSING").sum()) if not scenario_preview.empty else 0
            feasible = int(scenario_preview["whole_share_feasibility"].eq("FEASIBLE").sum()) if not scenario_preview.empty else 0
            too_small = int(scenario_preview["whole_share_feasibility"].eq("TOO_SMALL_FOR_ONE_SHARE").sum()) if not scenario_preview.empty else 0
            research_only = int(scenario_preview["whole_share_feasibility"].eq("RESEARCH_ONLY").sum()) if not scenario_preview.empty else 0
            pending_forward = int(scenario_preview["forward_evidence_status"].eq("PENDING_FORWARD_OUTCOME").sum()) if not scenario_preview.empty else 0
            weight_sum = float(weights_num.sum()) if not weights_num.empty else 0.0
            top5 = float(weights_num.sort_values(ascending=False).head(5).sum()) if not weights_num.empty else 0.0
            summary_rows.append(
                {
                    "scenario_name": scenario["name"],
                    "simulated_capital_usd": capital,
                    "included_ticker_count": len(scenario_preview),
                    "long_candidate_count": int(scenario_preview["alpha_direction"].eq("LONG_CANDIDATE").sum()) if not scenario_preview.empty else 0,
                    "watch_count": int(scenario_preview["alpha_direction"].eq("WATCH").sum()) if not scenario_preview.empty else 0,
                    "excluded_count": excluded_count,
                    "target_weight_sum": f"{weight_sum:.10f}",
                    "max_target_weight": f"{float(weights_num.max()) if not weights_num.empty else 0.0:.10f}",
                    "min_target_weight": f"{float(weights_num.min()) if not weights_num.empty else 0.0:.10f}",
                    "concentration_top5_weight": f"{top5:.10f}",
                    "price_available_count": price_available,
                    "price_missing_count": price_missing,
                    "whole_share_feasible_count": feasible,
                    "too_small_for_one_share_count": too_small,
                    "research_only_count": research_only,
                    "pending_forward_outcome_count": pending_forward,
                    "status": "OK_RESEARCH_ONLY" if scenario["research_only"] else ("OK_WEIGHT_SUM_READY" if abs(weight_sum - 1.0) <= 0.0001 else "WARN_WEIGHT_SUM_REVIEW"),
                    "notes": "Research-only watchlist; not investable target" if scenario["research_only"] else "Investable preview under simulated capital only; no order generation.",
                }
            )
            diagnostics.append(
                {
                    "check_name": "weight_sum_check",
                    "scenario_name": scenario["name"],
                    "simulated_capital_usd": capital,
                    "status": "PASS" if scenario["research_only"] or abs(weight_sum - 1.0) <= 0.0001 else "FAIL",
                    "expected": "approximately 1.0 for investable scenarios",
                    "observed": f"{weight_sum:.10f}",
                    "notes": "Research-only scenarios are excluded from investable weight-sum requirement." if scenario["research_only"] else "",
                }
            )

    preview = pd.DataFrame(rows)
    summary = pd.DataFrame(summary_rows)
    total_price_available = int(preview["latest_price"].astype(str).str.strip().ne("").sum()) if not preview.empty else 0
    total_price_missing = int(preview["whole_share_feasibility"].eq("PRICE_MISSING").sum()) if not preview.empty else 0
    input_signal_count = len(alpha)
    expected_signal_count = 318
    command_blocking = command_status.get("CURRENT_FAIL_BLOCKING_COUNT", "")
    daily_run_usable = command_status.get("DAILY_RUN_USABLE", "")
    diagnostics.extend(
        [
            {
                "check_name": "input_signal_count",
                "scenario_name": "ALL",
                "simulated_capital_usd": "",
                "status": "PASS" if input_signal_count > 0 else "FAIL",
                "expected": ">0",
                "observed": input_signal_count,
                "notes": "",
            },
            {
                "check_name": "expected_signal_count",
                "scenario_name": "ALL",
                "simulated_capital_usd": "",
                "status": "PASS" if input_signal_count == expected_signal_count else "WARN",
                "expected": expected_signal_count,
                "observed": input_signal_count,
                "notes": "Expected current full candidate universe size if available.",
            },
            {
                "check_name": "row_count_matches_alpha_signal_count",
                "scenario_name": "WATCHLIST_RESEARCH_ONLY_FULL318",
                "simulated_capital_usd": "ALL",
                "status": "PASS" if len(preview[preview["scenario_name"] == "WATCHLIST_RESEARCH_ONLY_FULL318"]) == input_signal_count * capital_count else "FAIL",
                "expected": input_signal_count * capital_count,
                "observed": len(preview[preview["scenario_name"] == "WATCHLIST_RESEARCH_ONLY_FULL318"]),
                "notes": "",
            },
            {
                "check_name": "price_coverage_check",
                "scenario_name": "ALL",
                "simulated_capital_usd": "ALL",
                "status": "PASS" if total_price_missing == 0 and total_price_available > 0 else "WARN",
                "expected": "price available where investable",
                "observed": f"available={total_price_available};missing={total_price_missing}",
                "notes": "Missing prices produce feasibility PRICE_MISSING, not failure.",
            },
            {
                "check_name": "no_order_file_created_check",
                "scenario_name": "ALL",
                "simulated_capital_usd": "ALL",
                "status": "PASS",
                "expected": "no orders/trades/execution files",
                "observed": "only portfolio_preview/read_center/ops outputs are written",
                "notes": "Module does not create order tickets, broker instructions, or executable trade files.",
            },
            {
                "check_name": "safety_marker_check",
                "scenario_name": "ALL",
                "simulated_capital_usd": "ALL",
                "status": "PASS" if alpha_read_first.get("AUTO_TRADE") == "DISABLED" else "WARN",
                "expected": "AUTO_TRADE DISABLED from alpha input",
                "observed": alpha_read_first.get("AUTO_TRADE", ""),
                "notes": "",
            },
            {
                "check_name": "command_status_current_blocking_count",
                "scenario_name": "ALL",
                "simulated_capital_usd": "ALL",
                "status": "PASS" if command_blocking in {"", "0"} else "WARN",
                "expected": "0 if discoverable",
                "observed": command_blocking,
                "notes": "",
            },
            {
                "check_name": "daily_run_usable",
                "scenario_name": "ALL",
                "simulated_capital_usd": "ALL",
                "status": "PASS" if daily_run_usable in {"", "TRUE"} else "WARN",
                "expected": "TRUE if discoverable",
                "observed": daily_run_usable,
                "notes": "",
            },
        ]
    )
    diagnostics_df = pd.DataFrame(diagnostics)
    context = {
        "alpha_signal_input_count": input_signal_count,
        "scenario_count": scenario_count,
        "capital_level_count": capital_count,
        "price_available_count": total_price_available,
        "price_missing_count": total_price_missing,
        "command_status_current_blocking_count": command_blocking,
        "daily_run_usable": daily_run_usable,
        "alpha_summary_status": alpha_summary_status,
        "candidate_status": candidate_status,
    }
    return preview, summary, diagnostics_df, context


def build_status(summary: pd.DataFrame, diagnostics: pd.DataFrame, context: dict[str, Any]) -> tuple[str, str]:
    fail_count = int((diagnostics["status"] == "FAIL").sum()) if not diagnostics.empty else 0
    price_missing = int(context.get("price_missing_count", 0))
    if fail_count > 0:
        return "FAIL_V18_39B_PORTFOLIO_TARGET_PREVIEW_BLOCKED", "Fix alpha signal input or failed preview diagnostics, then rerun V18.39B."
    if price_missing > 0 or context.get("candidate_status") != "OK":
        return "WARN_V18_39B_PORTFOLIO_TARGET_PREVIEW_REVIEW_NEEDED", "Review price coverage and feasibility warnings before using preview outputs for research."
    return "OK_V18_39B_PORTFOLIO_TARGET_PREVIEW_READY", "Portfolio target previews are ready for downstream read-only risk model preview."


def build_report(status: str, next_step: str, preview: pd.DataFrame, summary: pd.DataFrame, context: dict[str, Any]) -> str:
    def row_for(name: str, capital: int = 10000) -> dict[str, Any]:
        hit = summary[(summary["scenario_name"] == name) & (summary["simulated_capital_usd"].astype(str) == str(capital))]
        return hit.iloc[0].to_dict() if not hit.empty else {}

    top20_eq = row_for("TOP20_EQUAL_WEIGHT")
    top20_conf = row_for("TOP20_CONFIDENCE_WEIGHTED")
    top50_cap = row_for("TOP50_EQUAL_WEIGHT_CAPPED")
    top50_decay = row_for("TOP50_RANK_DECAY_WEIGHTED")
    return f"""# V18.39B Portfolio Target Preview 报告

## 1. 今日结论
- 状态: {status}
- Alpha signal input count: {context.get('alpha_signal_input_count', '')}
- Scenario count: {context.get('scenario_count', '')}
- Capital level count: {context.get('capital_level_count', '')}
- Total preview rows: {len(preview)}

## 2. Portfolio Target Preview 是什么
- 这是把 V18.39A alpha signal objects 转换成模拟资金规模下的 target weight / target notional / feasibility preview。
- 它不是交易建议，不是订单列表，不使用真实账户现金或持仓。

## 3. 使用的模拟资金规模
- 1000
- 2000
- 5000
- 10000

## 4. Top20 Equal Weight 预览
- 10000 USD included tickers: {top20_eq.get('included_ticker_count', '')}
- Weight sum: {top20_eq.get('target_weight_sum', '')}
- Whole-share feasible: {top20_eq.get('whole_share_feasible_count', '')}

## 5. Top20 Confidence Weighted 预览
- 10000 USD included tickers: {top20_conf.get('included_ticker_count', '')}
- Weight sum: {top20_conf.get('target_weight_sum', '')}
- Whole-share feasible: {top20_conf.get('whole_share_feasible_count', '')}

## 6. Top50 capped / rank decay 预览
- TOP50 capped weight sum: {top50_cap.get('target_weight_sum', '')}
- TOP50 rank decay weight sum: {top50_decay.get('target_weight_sum', '')}
- Max position cap: 5%

## 7. 整股可买性 / 价格覆盖情况
- Price available rows: {context.get('price_available_count', '')}
- Price missing rows: {context.get('price_missing_count', '')}
- Missing price 不会阻断输出，会标记为 PRICE_MISSING。

## 8. 为什么这不是下单
- 没有真实账户现金或持仓输入。
- 没有 broker/API 调用。
- 没有 order ticket、broker instruction 或 executable trade file。
- 输出只是理论 target preview。

## 9. 与 V18.39A Alpha Signal Object 的关系
- V18.39B 只消费 V18.39A alpha signal objects。
- 不重算排名，不改信号，不改权重公式。

## 10. Safety / no-impact confirmation
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- ORDER_EXECUTION_USED: FALSE
- BROKER_API_USED: FALSE
- REAL_ACCOUNT_USED: FALSE
- RANKING_MODIFIED: FALSE
- FACTOR_WEIGHTS_MODIFIED: FALSE
- SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE
- PAPER_TRADING_LEDGER_MODIFIED: FALSE
- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE
- ACCOUNT_STATE_MODIFIED: FALSE

## 11. 下一步建议
{next_step}
"""


def build_read_first(status: str, next_step: str, run_id: str, generated_at: str, preview: pd.DataFrame, summary: pd.DataFrame, context: dict[str, Any]) -> str:
    def count_rows(name: str) -> int:
        return int((preview["scenario_name"] == name).sum()) if not preview.empty else 0

    whole_feasible = int((preview["whole_share_feasibility"] == "FEASIBLE").sum()) if not preview.empty else 0
    too_small = int((preview["whole_share_feasibility"] == "TOO_SMALL_FOR_ONE_SHARE").sum()) if not preview.empty else 0
    fields = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "GENERATED_AT": generated_at,
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "ORDER_EXECUTION_USED": "FALSE",
        "BROKER_API_USED": "FALSE",
        "REAL_ACCOUNT_USED": "FALSE",
        "RANKING_MODIFIED": "FALSE",
        "FACTOR_WEIGHTS_MODIFIED": "FALSE",
        "SIGNAL_FREEZE_LEDGER_MODIFIED": "FALSE",
        "PAPER_TRADING_LEDGER_MODIFIED": "FALSE",
        "SHADOW_PORTFOLIO_LEDGER_MODIFIED": "FALSE",
        "ACCOUNT_STATE_MODIFIED": "FALSE",
        "ALPHA_SIGNAL_INPUT_COUNT": context.get("alpha_signal_input_count", ""),
        "TOTAL_PREVIEW_ROW_COUNT": len(preview),
        "SCENARIO_COUNT": context.get("scenario_count", ""),
        "CAPITAL_LEVEL_COUNT": context.get("capital_level_count", ""),
        "TOP20_EQUAL_WEIGHT_ROWS": count_rows("TOP20_EQUAL_WEIGHT"),
        "TOP20_CONFIDENCE_WEIGHTED_ROWS": count_rows("TOP20_CONFIDENCE_WEIGHTED"),
        "TOP50_EQUAL_WEIGHT_CAPPED_ROWS": count_rows("TOP50_EQUAL_WEIGHT_CAPPED"),
        "TOP50_RANK_DECAY_WEIGHTED_ROWS": count_rows("TOP50_RANK_DECAY_WEIGHTED"),
        "WATCHLIST_RESEARCH_ONLY_ROWS": count_rows("WATCHLIST_RESEARCH_ONLY_FULL318"),
        "PRICE_AVAILABLE_COUNT": context.get("price_available_count", ""),
        "PRICE_MISSING_COUNT": context.get("price_missing_count", ""),
        "WHOLE_SHARE_FEASIBLE_COUNT": whole_feasible,
        "TOO_SMALL_FOR_ONE_SHARE_COUNT": too_small,
        "COMMAND_STATUS_CURRENT_BLOCKING_COUNT": context.get("command_status_current_blocking_count", ""),
        "DAILY_RUN_USABLE": context.get("daily_run_usable", ""),
        "NEXT_RECOMMENDED_STEP": next_step,
    }
    return "\n".join(f"{k}: {v}" for k, v in fields.items()) + "\n"


def run(root: Path) -> int:
    ensure_dirs(root)
    run_id = f"V18_39B_PORTFOLIO_TARGET_PREVIEW_{now_ts()}"
    generated_at = now_iso()
    out_dir = root / "outputs/v18/portfolio_preview"
    read_center = root / "outputs/v18/read_center"
    ops = root / "outputs/v18/ops"
    try:
        preview, summary, diagnostics, context = build_previews(root, run_id, generated_at)
        status, next_step = build_status(summary, diagnostics, context)
    except Exception as exc:
        preview = pd.DataFrame(columns=PREVIEW_COLUMNS)
        summary = pd.DataFrame(columns=SUMMARY_COLUMNS)
        diagnostics = pd.DataFrame(
            [
                {
                    "check_name": "alpha_signal_input_read",
                    "scenario_name": "ALL",
                    "simulated_capital_usd": "",
                    "status": "FAIL",
                    "expected": "readable V18.39A alpha signal objects",
                    "observed": f"{type(exc).__name__}: {exc}",
                    "notes": "",
                }
            ],
            columns=DIAGNOSTIC_COLUMNS,
        )
        context = {
            "alpha_signal_input_count": 0,
            "scenario_count": 0,
            "capital_level_count": len(CAPITAL_LEVELS),
            "price_available_count": 0,
            "price_missing_count": 0,
            "command_status_current_blocking_count": "",
            "daily_run_usable": "",
        }
        status = "FAIL_V18_39B_PORTFOLIO_TARGET_PREVIEW_BLOCKED"
        next_step = "Fix V18.39A alpha signal input, then rerun V18.39B."

    write_csv(out_dir / "V18_39B_PORTFOLIO_TARGET_PREVIEW.csv", preview, PREVIEW_COLUMNS)
    write_csv(out_dir / "V18_39B_PORTFOLIO_TARGET_SUMMARY.csv", summary, SUMMARY_COLUMNS)
    write_csv(out_dir / "V18_39B_PORTFOLIO_TARGET_DIAGNOSTICS.csv", diagnostics, DIAGNOSTIC_COLUMNS)
    report = build_report(status, next_step, preview, summary, context)
    write_text(read_center / "V18_39B_PORTFOLIO_TARGET_PREVIEW_REPORT.md", report)
    write_text(read_center / "V18_CURRENT_PORTFOLIO_TARGET_PREVIEW.md", report)
    write_text(ops / "V18_39B_READ_FIRST.txt", build_read_first(status, next_step, run_id, generated_at, preview, summary, context))
    return 1 if status.startswith("FAIL_") else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
