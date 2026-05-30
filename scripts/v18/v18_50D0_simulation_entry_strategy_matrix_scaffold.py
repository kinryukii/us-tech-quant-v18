from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


PATCH_VERSION = "V18.50D-0"
PATCH_NAME = "SIMULATION_ENTRY_STRATEGY_MATRIX_SCAFFOLD"

READ50B = "outputs/v18/ops/V18_50B_R2_READ_FIRST.txt"
READ50C = "outputs/v18/ops/V18_50C_READ_FIRST.txt"
CURRENT_TOP20 = "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"
ACTION_PACKET = "outputs/v18/action_plan/V18_50A_DAILY_OPERATOR_ACTION_PACKET.csv"
STATUS35D = "outputs/v18/candidates/V18_35D_FULL_UNIVERSE_COMPUTATION_STATUS.csv"
EVENT_RISK = "outputs/v18/event_risk/V18_47C_R2_TOP20_90D_RISK_EVENT_DIAGNOSTICS.csv"
OPTIONS_RISK = "outputs/v18/options/V18_48B_TOP20_OPTIONS_RISK_RADAR_DETAIL.csv"

OUT_MATRIX = "outputs/v18/strategy_research/V18_50D0_SIMULATION_ENTRY_STRATEGY_MATRIX.csv"
OUT_SUMMARY = "outputs/v18/strategy_research/V18_50D0_SIMULATION_ENTRY_STRATEGY_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_50D0_SIMULATION_ENTRY_STRATEGY_MATRIX_REPORT.md"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_SIMULATION_ENTRY_STRATEGY_MATRIX.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_50D0_READ_FIRST.txt"

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
    "entry_candidate_flag", "entry_block_reason", "research_only", "trading_allowed", "notes",
]

READ_FIRST_ORDER = [
    "STATUS", "PATCH_VERSION", "PATCH_NAME", "SOURCE_GATE_V18_50B_R2_OK",
    "READABILITY_GATE_V18_50C_R1_OK", "CURRENT_TOP20_FOUND", "CURRENT_TOP20_ROW_COUNT",
    "ACTION_PACKET_FOUND", "ACTION_PACKET_ROW_COUNT", "STRATEGY_COUNT", "STRATEGY_IDS",
    "BASELINE_TOP20_ROW_COUNT", "MATRIX_WRITTEN", "SUMMARY_WRITTEN", "REPORT_WRITTEN",
    "CURRENT_REPORT_WRITTEN", "RESEARCH_ONLY", "OFFICIAL_RANKING_CHANGED",
    "FACTOR_WEIGHTS_CHANGED", "OFFICIAL_BUY_PERMISSION_CHANGED", "OFFICIAL_SELL_PERMISSION_CHANGED",
    "TRADING_EXECUTION_ALLOWED", "AUTO_TRADE", "AUTO_SELL", "BROKER_API_USED", "ORDER_EXECUTION_USED",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


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


def to_int(value: object) -> int:
    try:
        return int(float(clean(value)))
    except Exception:
        return 0


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


def build_matrix(
    top20: list[dict[str, str]],
    action_rows: list[dict[str, str]],
    status_rows: list[dict[str, str]],
    event_rows: list[dict[str, str]],
    options_rows: list[dict[str, str]],
    gates_ok: bool,
) -> list[dict[str, str]]:
    actions = index_by_ticker(action_rows)
    status = index_by_ticker(status_rows)
    events = index_by_ticker(event_rows)
    options = index_by_ticker(options_rows)
    signal_date = max([clean(row.get("latest_price_date")) for row in top20 if clean(row.get("latest_price_date"))] or [""])
    out: list[dict[str, str]] = []
    for expected_rank, row in enumerate(sorted_top20(top20), 1):
        ticker = clean(row.get("ticker")).upper()
        srow = status.get(ticker, {})
        arow = actions.get(ticker, {})
        erow = events.get(ticker, {})
        orow = options.get(ticker, {})
        authoritative = clean(row.get("authoritative_row_ok")).upper() == "TRUE"
        rank_match = to_int(row.get("rank")) == expected_rank
        entry_ok = gates_ok and authoritative and rank_match
        out.append({
            "signal_date": signal_date,
            "strategy_id": "BASELINE_TOP20",
            "strategy_name": "Baseline current Top20 research cohort",
            "strategy_family": "BASELINE",
            "strategy_status": "RESEARCH_ONLY",
            "ticker": ticker,
            "rank": clean(row.get("rank")),
            "composite_candidate_score": clean(row.get("composite_candidate_score")),
            "factor_score": clean(srow.get("factor_score")),
            "technical_score": clean(srow.get("technical_timing_score")),
            "latest_price_date": clean(row.get("latest_price_date")),
            "source_authoritative_ok": bool_text(authoritative),
            "current_top20_rank_match_ok": bool_text(rank_match),
            "simulation_action_from_v18_50A": clean(arow.get("simulation_action")),
            "real_position_action_from_v18_50A": clean(arow.get("real_position_action")),
            "event_risk_level_if_available": clean(erow.get("final_event_risk_level")),
            "options_risk_level_if_available": clean(orow.get("dte_bucket_options_risk_level")),
            "entry_candidate_flag": bool_text(entry_ok),
            "entry_block_reason": "NONE" if entry_ok else "SOURCE_GATE_OR_AUTHORITATIVE_ROW_NOT_READY",
            "research_only": "TRUE",
            "trading_allowed": "FALSE",
            "notes": "Research baseline only; not a buy signal and does not override V18.50A actions.",
        })
    return out


def render_report(values: dict[str, str], matrix: list[dict[str, str]]) -> str:
    lines = [
        "# V18.50D-0 模拟入场策略矩阵脚手架",
        "",
        f"- STATUS: `{values['STATUS']}`",
        f"- PATCH_VERSION: `{PATCH_VERSION}`",
        f"- SOURCE_GATE_V18_50B_R2_OK: `{values['SOURCE_GATE_V18_50B_R2_OK']}`",
        f"- READABILITY_GATE_V18_50C_R1_OK: `{values['READABILITY_GATE_V18_50C_R1_OK']}`",
        "",
        "## 重要说明",
        "",
        "- BASELINE_TOP20 是研究基准组，不是买入信号。",
        "- V18.50D-0 不改变 V18.50A 的 simulation_action。",
        "- 如果 V18.50A 仍显示 PAPER_SKIP_POLICY_LIMIT，本补丁不会覆盖它。",
        "- 真实交易继续禁用，broker/order/trading 均为 FALSE/DISABLED。",
        "",
        "## BASELINE_TOP20",
        "",
        "| rank | ticker | score | sim_action | real_action | entry_candidate_flag |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in matrix:
        lines.append(
            f"| {row['rank']} | {row['ticker']} | {row['composite_candidate_score']} | "
            f"{row['simulation_action_from_v18_50A']} | {row['real_position_action_from_v18_50A']} | "
            f"{row['entry_candidate_flag']} |"
        )
    return "\n".join(lines) + "\n"


def run(root: Path) -> int:
    read50b = read_kv(root / READ50B)
    read50c = read_kv(root / READ50C)
    top20, _ = read_csv(root / CURRENT_TOP20)
    actions, _ = read_csv(root / ACTION_PACKET)
    gate_b = gate50b_ok(read50b)
    gate_c = gate50c_ok(read50c)
    gates_ok = gate_b and gate_c

    matrix_written = summary_written = report_written = current_report_written = "FALSE"
    matrix: list[dict[str, str]] = []
    status = "PASS" if gates_ok and top20 and actions else "WARN_V18_50D0_SOURCE_GATES_NOT_READY"

    if gates_ok:
        status_rows, _ = read_csv(root / STATUS35D)
        event_rows, _ = read_csv(root / EVENT_RISK)
        options_rows, _ = read_csv(root / OPTIONS_RISK)
        matrix = build_matrix(top20, actions, status_rows, event_rows, options_rows, gates_ok)
        write_csv(root / OUT_MATRIX, matrix, MATRIX_FIELDS)
        matrix_written = "TRUE"
        values_preview = {"STATUS": status, "SOURCE_GATE_V18_50B_R2_OK": bool_text(gate_b), "READABILITY_GATE_V18_50C_R1_OK": bool_text(gate_c)}
        report = render_report(values_preview, matrix)
        write_text(root / OUT_REPORT, report)
        write_text(root / OUT_CURRENT_REPORT, report)
        report_written = current_report_written = "TRUE"

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
        "STRATEGY_COUNT": "1" if matrix else "0",
        "STRATEGY_IDS": "BASELINE_TOP20" if matrix else "NONE",
        "BASELINE_TOP20_ROW_COUNT": str(len(matrix)),
        "MATRIX_WRITTEN": matrix_written,
        "SUMMARY_WRITTEN": "TRUE",
        "REPORT_WRITTEN": report_written,
        "CURRENT_REPORT_WRITTEN": current_report_written,
        **SAFETY_FIELDS,
    }
    write_csv(root / OUT_SUMMARY, [values], READ_FIRST_ORDER)
    summary_written = "TRUE"
    values["SUMMARY_WRITTEN"] = summary_written
    write_csv(root / OUT_SUMMARY, [values], READ_FIRST_ORDER)
    write_text(root / OUT_READ_FIRST, "\n".join(f"{key}: {values.get(key, '')}" for key in READ_FIRST_ORDER) + "\n")

    print(f"STATUS: {values['STATUS']}")
    print(f"BASELINE_TOP20_ROW_COUNT: {values['BASELINE_TOP20_ROW_COUNT']}")
    print(f"MATRIX_WRITTEN: {values['MATRIX_WRITTEN']}")
    print(f"RESEARCH_ONLY: {values['RESEARCH_ONLY']}")
    return 0 if values["STATUS"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.50D-0 simulation entry strategy matrix scaffold.")
    parser.add_argument("--root", "--project-root", dest="root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
