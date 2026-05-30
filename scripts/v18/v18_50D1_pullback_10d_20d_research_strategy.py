from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


PATCH_VERSION = "V18.50D-1-R1"
PATCH_NAME = "PULLBACK_10D_20D_MA10_FIX"
PULLBACK_RULE_VERSION = "V18_50D1_PULLBACK_10D_20D_RULE"

READ50B = "outputs/v18/ops/V18_50B_R2_READ_FIRST.txt"
READ50C = "outputs/v18/ops/V18_50C_READ_FIRST.txt"
READ50A = "outputs/v18/ops/V18_50A_READ_FIRST.txt"
CURRENT_TOP20 = "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"
ACTION_PACKET = "outputs/v18/action_plan/V18_50A_DAILY_OPERATOR_ACTION_PACKET.csv"
STATUS35D = "outputs/v18/candidates/V18_35D_FULL_UNIVERSE_COMPUTATION_STATUS.csv"
TECH35D = "outputs/v18/technical_timing/V18_35D_FULL_UNIVERSE_TECHNICAL_TIMING.csv"
EVENT_RISK = "outputs/v18/event_risk/V18_47C_R2_TOP20_90D_RISK_EVENT_DIAGNOSTICS.csv"
OPTIONS_RISK = "outputs/v18/options/V18_48B_TOP20_OPTIONS_RISK_RADAR_DETAIL.csv"

OUT_MATRIX = "outputs/v18/strategy_research/V18_50D1_SIMULATION_ENTRY_STRATEGY_MATRIX.csv"
OUT_SUMMARY = "outputs/v18/strategy_research/V18_50D1_SIMULATION_ENTRY_STRATEGY_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_50D1_SIMULATION_ENTRY_STRATEGY_MATRIX_REPORT.md"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_SIMULATION_ENTRY_STRATEGY_MATRIX.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_50D1_READ_FIRST.txt"

SAFETY_FIELDS = {
    "RESEARCH_ONLY": "TRUE",
    "OFFICIAL_RANKING_CHANGED": "FALSE",
    "FACTOR_WEIGHTS_CHANGED": "FALSE",
    "OFFICIAL_BUY_PERMISSION_CHANGED": "FALSE",
    "OFFICIAL_SELL_PERMISSION_CHANGED": "FALSE",
    "TRADING_EXECUTION_ALLOWED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "BROKER_API_USED": "FALSE",
    "ORDER_EXECUTION_USED": "FALSE",
}

MATRIX_FIELDS = [
    "signal_date", "strategy_id", "strategy_name", "strategy_family", "strategy_status",
    "ticker", "rank", "composite_candidate_score", "factor_score", "technical_score",
    "latest_price_date", "source_authoritative_ok", "current_top20_rank_match_ok",
    "simulation_action_from_v18_50A", "real_position_action_from_v18_50A",
    "event_risk_level_if_available", "options_risk_level_if_available",
    "latest_close", "ma10", "ma20", "distance_to_ma10_pct", "distance_to_ma20_pct",
    "pullback_reference_ma", "pullback_near_ma_flag", "pullback_rule_version",
    "entry_candidate_flag", "entry_block_reason", "research_only", "trading_allowed", "notes",
]

READ_FIRST_ORDER = [
    "STATUS", "PATCH_VERSION", "PATCH_NAME", "SOURCE_GATE_V18_50B_R2_OK",
    "READABILITY_GATE_V18_50C_R1_OK", "CURRENT_TOP20_FOUND", "CURRENT_TOP20_ROW_COUNT",
    "ACTION_PACKET_FOUND", "ACTION_PACKET_ROW_COUNT", "STRATEGY_COUNT", "STRATEGY_IDS",
    "BASELINE_TOP20_ROW_COUNT", "PULLBACK_10D_20D_ROW_COUNT", "PULLBACK_10D_20D_CANDIDATE_COUNT",
    "PULLBACK_10D_20D_BLOCKED_COUNT", "PULLBACK_10D_20D_MA10_COMPUTED_COUNT",
    "MATRIX_WRITTEN", "SUMMARY_WRITTEN", "REPORT_WRITTEN",
    "CURRENT_REPORT_WRITTEN", "RESEARCH_ONLY", "OFFICIAL_RANKING_CHANGED",
    "FACTOR_WEIGHTS_CHANGED", "OFFICIAL_BUY_PERMISSION_CHANGED", "OFFICIAL_SELL_PERMISSION_CHANGED",
    "TRADING_EXECUTION_ALLOWED", "AUTO_TRADE", "AUTO_SELL", "BROKER_API_USED", "ORDER_EXECUTION_USED",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def to_int(value: object) -> int:
    try:
        return int(float(clean(value)))
    except Exception:
        return 0


def to_float(value: object) -> float | None:
    text = clean(value)
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def read_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip().upper()] = value.strip()
    return out


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as f:
                reader = csv.DictReader(f)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def sorted_top20(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda r: (to_int(r.get("rank")) or 10**9, clean(r.get("ticker")).upper()))[:20]


def index_by_ticker(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        ticker = clean(row.get("ticker")).upper()
        if ticker and ticker not in out:
            out[ticker] = row
    return out


def gate50b_ok(read50b: dict[str, str]) -> bool:
    return (
        read50b.get("PATCH_VERSION") == "V18.50B-R2"
        and read50b.get("STATUS") == "PASS"
        and read50b.get("SOLE_WRITER_AUDIT_OK") == "TRUE"
        and read50b.get("CURRENT_TOP20_WRITE_ALLOWED") == "TRUE"
        and read50b.get("V18_35D_TOP20_MATCH_CURRENT_TOP20") == "TRUE"
    )


def gate50c_ok(read50c: dict[str, str]) -> bool:
    return (
        read50c.get("PATCH_VERSION") == "V18.50C-R1"
        and read50c.get("STATUS") == "PASS"
        and read50c.get("DAILY_OPERATOR_REPORT_USABLE") == "TRUE"
        and read50c.get("COMMAND_CENTER_SEQUENCE_OK") == "TRUE"
    )


def gate50a_ok(read50a: dict[str, str]) -> bool:
    return (
        read50a.get("PATCH_VERSION") == "V18.50A"
        and read50a.get("STATUS") == "PASS"
        and read50a.get("DAILY_OPERATOR_ACTION_ENTRY_SOURCE_OK") == "TRUE"
    )


def pct_distance(close_value: float | None, ma_value: float | None) -> float | None:
    if close_value is None or ma_value is None or ma_value == 0:
        return None
    return ((close_value / ma_value) - 1.0) * 100.0


def fmt_num(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def in_pullback_band(distance: float | None) -> bool:
    return distance is not None and -2.0 <= distance <= 5.0


def resolve_price_source(root: Path, source_text: str, ticker: str) -> Path | None:
    source = clean(source_text)
    if not source:
        return None
    source_path = Path(source)
    if source_path.exists():
        return source_path
    alt = root / source
    if alt.exists():
        return alt
    fallback = root / "state" / "v18" / "price_cache" / f"{ticker.upper()}.csv"
    if fallback.exists():
        return fallback
    return None


def compute_ma_values(root: Path, source_text: str, ticker: str, latest_price_date: str) -> tuple[float | None, float | None]:
    source_path = resolve_price_source(root, source_text, ticker)
    if source_path is None:
        return None, None
    history_rows, _ = read_csv(source_path)
    if not history_rows:
        return None, None
    closes: list[float] = []
    for hrow in history_rows:
        d = clean(hrow.get("date") or hrow.get("price_date"))
        if not d:
            continue
        if latest_price_date and d > latest_price_date:
            continue
        c = to_float(hrow.get("close") or hrow.get("adj_close") or hrow.get("manual_latest_close"))
        if c is not None:
            closes.append(c)
    if len(closes) < 20:
        return None, None
    ma20 = sum(closes[-20:]) / 20.0
    ma10 = sum(closes[-10:]) / 10.0 if len(closes) >= 10 else None
    return ma10, ma20


def build_rows(
    root: Path,
    top20: list[dict[str, str]],
    action_rows: list[dict[str, str]],
    status_rows: list[dict[str, str]],
    event_rows: list[dict[str, str]],
    options_rows: list[dict[str, str]],
    tech_rows: list[dict[str, str]],
    gates_ok: bool,
) -> list[dict[str, str]]:
    actions = index_by_ticker(action_rows)
    status = index_by_ticker(status_rows)
    events = index_by_ticker(event_rows)
    options = index_by_ticker(options_rows)
    tech = index_by_ticker(tech_rows)
    signal_date = max([clean(row.get("latest_price_date")) for row in top20 if clean(row.get("latest_price_date"))] or [""])
    output: list[dict[str, str]] = []

    for expected_rank, row in enumerate(sorted_top20(top20), 1):
        ticker = clean(row.get("ticker")).upper()
        srow = status.get(ticker, {})
        arow = actions.get(ticker, {})
        erow = events.get(ticker, {})
        orow = options.get(ticker, {})
        trow = tech.get(ticker, {})

        authoritative = clean(row.get("authoritative_row_ok")).upper() == "TRUE"
        rank_match = to_int(row.get("rank")) == expected_rank
        latest_date = clean(row.get("latest_price_date"))
        latest_close = to_float(row.get("latest_close"))
        ma10_hist, ma20_hist = compute_ma_values(root, srow.get("price_data_source", ""), ticker, latest_date)
        ma10 = ma10_hist
        ma20 = ma20_hist if ma20_hist is not None else to_float(trow.get("bb_mid_20"))
        history_rows = to_int(srow.get("history_row_count"))
        enough_history = history_rows >= 20
        dist10 = pct_distance(latest_close, ma10)
        dist20 = pct_distance(latest_close, ma20)
        qual10 = in_pullback_band(dist10)
        qual20 = in_pullback_band(dist20)
        near_ma = qual10 or qual20

        ref_ma = ""
        if qual10 and qual20:
            ref_ma = "MA10" if abs(dist10 or 0.0) <= abs(dist20 or 0.0) else "MA20"
        elif qual10:
            ref_ma = "MA10"
        elif qual20:
            ref_ma = "MA20"

        base_entry_ok = gates_ok and authoritative and rank_match
        base_block = "NONE" if base_entry_ok else "SOURCE_GATE_OR_AUTHORITATIVE_ROW_NOT_READY"

        base_common = {
            "signal_date": signal_date,
            "ticker": ticker,
            "rank": clean(row.get("rank")),
            "composite_candidate_score": clean(row.get("composite_candidate_score")),
            "factor_score": clean(srow.get("factor_score")),
            "technical_score": clean(srow.get("technical_timing_score")),
            "latest_price_date": latest_date,
            "source_authoritative_ok": bool_text(authoritative),
            "current_top20_rank_match_ok": bool_text(rank_match),
            "simulation_action_from_v18_50A": clean(arow.get("simulation_action")),
            "real_position_action_from_v18_50A": clean(arow.get("real_position_action")),
            "event_risk_level_if_available": clean(erow.get("final_event_risk_level")),
            "options_risk_level_if_available": clean(orow.get("dte_bucket_options_risk_level")),
            "latest_close": fmt_num(latest_close),
            "ma10": fmt_num(ma10),
            "ma20": fmt_num(ma20),
            "distance_to_ma10_pct": fmt_num(dist10),
            "distance_to_ma20_pct": fmt_num(dist20),
            "pullback_reference_ma": "",
            "pullback_near_ma_flag": "FALSE",
            "pullback_rule_version": PULLBACK_RULE_VERSION,
            "research_only": "TRUE",
            "trading_allowed": "FALSE",
        }

        output.append({
            **base_common,
            "strategy_id": "BASELINE_TOP20",
            "strategy_name": "Baseline current Top20 research cohort",
            "strategy_family": "BASELINE",
            "strategy_status": "RESEARCH_ONLY",
            "entry_candidate_flag": bool_text(base_entry_ok),
            "entry_block_reason": base_block,
            "notes": "Research baseline only; not a buy signal and does not override V18.50A actions.",
        })

        pullback_ok = False
        pullback_block = "NONE"
        if not base_entry_ok:
            pullback_block = "SOURCE_GATE_OR_AUTHORITATIVE_ROW_NOT_READY"
        elif latest_close is None or not enough_history or ma20 is None:
            pullback_block = "PRICE_HISTORY_OR_MA_UNAVAILABLE"
        elif not near_ma:
            pullback_block = "NOT_NEAR_10D_OR_20D_MA"
        else:
            pullback_ok = True

        output.append({
            **base_common,
            "strategy_id": "PULLBACK_10D_20D",
            "strategy_name": "Pullback near MA10/MA20 research cohort",
            "strategy_family": "PULLBACK",
            "strategy_status": "RESEARCH_ONLY",
            "pullback_reference_ma": ref_ma,
            "pullback_near_ma_flag": bool_text(near_ma),
            "entry_candidate_flag": bool_text(pullback_ok),
            "entry_block_reason": "NONE" if pullback_ok else pullback_block,
            "notes": "Research-only pullback screen; not a buy signal and does not override V18.50A actions.",
        })
    return output


def render_report(values: dict[str, str], matrix_rows: list[dict[str, str]]) -> str:
    baseline = [r for r in matrix_rows if r.get("strategy_id") == "BASELINE_TOP20"]
    pullback = [r for r in matrix_rows if r.get("strategy_id") == "PULLBACK_10D_20D"]
    lines = [
        "# V18.50D-1 模拟入场策略矩阵（研究层）",
        "",
        f"- STATUS: `{values['STATUS']}`",
        f"- PATCH_VERSION: `{PATCH_VERSION}`",
        f"- SOURCE_GATE_V18_50B_R2_OK: `{values['SOURCE_GATE_V18_50B_R2_OK']}`",
        f"- READABILITY_GATE_V18_50C_R1_OK: `{values['READABILITY_GATE_V18_50C_R1_OK']}`",
        "",
        "## 重要说明",
        "",
        "- PULLBACK_10D_20D 是研究用策略，不是买入信号。",
        "- 本补丁不会改写 V18.50A 的 simulation_action。",
        "- 若 V18.50A 为 PAPER_SKIP_POLICY_LIMIT，本补丁不会覆盖。",
        "- 真实交易保持禁用（trading/broker/order 均为 FALSE 或 DISABLED）。",
        "",
        "## BASELINE_TOP20（研究基准）",
        "",
        "| rank | ticker | score | sim_action | real_action | entry_candidate_flag |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in baseline:
        lines.append(
            f"| {row['rank']} | {row['ticker']} | {row['composite_candidate_score']} | "
            f"{row['simulation_action_from_v18_50A']} | {row['real_position_action_from_v18_50A']} | {row['entry_candidate_flag']} |"
        )
    lines.extend([
        "",
        "## PULLBACK_10D_20D（研究筛选）",
        "",
        "| rank | ticker | close | ma20 | dist_ma20_pct | ref_ma | near_ma | entry_candidate_flag | block_reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ])
    for row in pullback:
        lines.append(
            f"| {row['rank']} | {row['ticker']} | {row['latest_close']} | {row['ma20']} | "
            f"{row['distance_to_ma20_pct']} | {row['pullback_reference_ma']} | {row['pullback_near_ma_flag']} | "
            f"{row['entry_candidate_flag']} | {row['entry_block_reason']} |"
        )
    return "\n".join(lines) + "\n"


def run(root: Path) -> int:
    read50b = read_kv(root / READ50B)
    read50c = read_kv(root / READ50C)
    read50a = read_kv(root / READ50A)
    top20, _ = read_csv(root / CURRENT_TOP20)
    actions, _ = read_csv(root / ACTION_PACKET)
    gate_b = gate50b_ok(read50b)
    gate_c = gate50c_ok(read50c)
    gate_a = gate50a_ok(read50a)
    gates_ok = gate_b and gate_c and gate_a and bool(top20) and bool(actions)

    matrix_written = report_written = current_report_written = "FALSE"
    matrix_rows: list[dict[str, str]] = []
    status = "PASS" if gates_ok else "WARN_V18_50D1_SOURCE_GATES_NOT_READY"

    if gates_ok:
        status_rows, _ = read_csv(root / STATUS35D)
        event_rows, _ = read_csv(root / EVENT_RISK)
        options_rows, _ = read_csv(root / OPTIONS_RISK)
        tech_rows, _ = read_csv(root / TECH35D)
        matrix_rows = build_rows(root, top20, actions, status_rows, event_rows, options_rows, tech_rows, gates_ok)
        write_csv(root / OUT_MATRIX, matrix_rows, MATRIX_FIELDS)
        matrix_written = "TRUE"
        preview = {
            "STATUS": status,
            "SOURCE_GATE_V18_50B_R2_OK": bool_text(gate_b),
            "READABILITY_GATE_V18_50C_R1_OK": bool_text(gate_c),
        }
        report = render_report(preview, matrix_rows)
        write_text(root / OUT_REPORT, report)
        write_text(root / OUT_CURRENT_REPORT, report)
        report_written = current_report_written = "TRUE"

    baseline_rows = [r for r in matrix_rows if r.get("strategy_id") == "BASELINE_TOP20"]
    pullback_rows = [r for r in matrix_rows if r.get("strategy_id") == "PULLBACK_10D_20D"]
    pullback_candidates = [r for r in pullback_rows if clean(r.get("entry_candidate_flag")).upper() == "TRUE"]
    ma10_computed_rows = [r for r in pullback_rows if clean(r.get("ma10")) != ""]

    values = {
        "STATUS": status,
        "PATCH_VERSION": PATCH_VERSION,
        "PATCH_NAME": PATCH_NAME,
        "SOURCE_GATE_V18_50B_R2_OK": bool_text(gate_b),
        "READABILITY_GATE_V18_50C_R1_OK": bool_text(gate_c),
        "CURRENT_TOP20_FOUND": bool_text(bool(top20)),
        "CURRENT_TOP20_ROW_COUNT": str(len(sorted_top20(top20))),
        "ACTION_PACKET_FOUND": bool_text(bool(actions)),
        "ACTION_PACKET_ROW_COUNT": str(len(actions)),
        "STRATEGY_COUNT": "2" if matrix_rows else "0",
        "STRATEGY_IDS": "BASELINE_TOP20;PULLBACK_10D_20D" if matrix_rows else "NONE",
        "BASELINE_TOP20_ROW_COUNT": str(len(baseline_rows)),
        "PULLBACK_10D_20D_ROW_COUNT": str(len(pullback_rows)),
        "PULLBACK_10D_20D_CANDIDATE_COUNT": str(len(pullback_candidates)),
        "PULLBACK_10D_20D_BLOCKED_COUNT": str(max(0, len(pullback_rows) - len(pullback_candidates))),
        "PULLBACK_10D_20D_MA10_COMPUTED_COUNT": str(len(ma10_computed_rows)),
        "MATRIX_WRITTEN": matrix_written,
        "SUMMARY_WRITTEN": "TRUE",
        "REPORT_WRITTEN": report_written,
        "CURRENT_REPORT_WRITTEN": current_report_written,
        **SAFETY_FIELDS,
    }
    write_csv(root / OUT_SUMMARY, [values], READ_FIRST_ORDER)
    write_text(root / OUT_READ_FIRST, "\n".join(f"{k}: {values.get(k, '')}" for k in READ_FIRST_ORDER) + "\n")

    print(f"STATUS: {values['STATUS']}")
    print(f"BASELINE_TOP20_ROW_COUNT: {values['BASELINE_TOP20_ROW_COUNT']}")
    print(f"PULLBACK_10D_20D_ROW_COUNT: {values['PULLBACK_10D_20D_ROW_COUNT']}")
    print(f"PULLBACK_10D_20D_CANDIDATE_COUNT: {values['PULLBACK_10D_20D_CANDIDATE_COUNT']}")
    print(f"MATRIX_WRITTEN: {values['MATRIX_WRITTEN']}")
    return 0 if values["STATUS"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.50D-1 pullback 10d/20d research strategy matrix.")
    parser.add_argument("--root", "--project-root", dest="root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
