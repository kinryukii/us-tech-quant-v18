from __future__ import annotations

import argparse
import csv
import subprocess
from datetime import datetime
from pathlib import Path


PATCH_VERSION = "V18.50A"
PATCH_NAME = "DAILY_OPERATOR_ACTION_ENTRY"

PACKET_COLUMNS = [
    "run_date", "rank", "ticker", "latest_price_date", "source_policy_id",
    "source_chain", "simulation_action", "real_position_action", "section",
    "item", "value", "details",
]
SUMMARY_COLUMNS = [
    "run_date", "status", "v18_49d_status", "v18_49a_status", "v18_49b_status",
    "v18_49c_status", "real_trade_upload_checked", "real_position_book_found",
    "real_position_book_written_to_state", "write_real_position_book_requested",
    "source_policy_id", "source_policy_confidence", "simulation_decision",
    "paper_buy_candidate_count", "paper_add_candidate_count",
    "paper_reduce_candidate_count", "paper_exit_candidate_count",
    "real_advice_available", "real_advice_unavailable_reason",
    "official_ranking_changed", "factor_weights_changed",
    "real_trade_execution_allowed", "broker_api_used", "order_execution_used",
]

SAFETY_EXPECTED = {
    "OFFICIAL_RANKING_CHANGED": "FALSE",
    "FACTOR_WEIGHTS_CHANGED": "FALSE",
    "OFFICIAL_BUY_PERMISSION_CHANGED": "FALSE",
    "OFFICIAL_SELL_PERMISSION_CHANGED": "FALSE",
    "REAL_TRADE_EXECUTION_ALLOWED": "FALSE",
    "OPTIONS_TRADE_EXECUTION_ALLOWED": "FALSE",
    "TRADING_EXECUTION_ALLOWED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "BROKER_API_USED": "FALSE",
    "ORDER_EXECUTION_USED": "FALSE",
}


def clean(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def read_key_values(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                out[key.strip()] = value.strip()
    except OSError:
        pass
    return out


def read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except (OSError, UnicodeDecodeError, csv.Error):
        return []


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: clean(row.get(column)) for column in fieldnames})


def powershell() -> str:
    return "powershell"


def run_wrapper(script: Path, root: Path, write_current: bool, extra_args: list[str]) -> tuple[int, str]:
    args = [
        powershell(), "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(script), "-ProjectRoot", str(root),
    ]
    if write_current:
        args.append("-WriteCurrent")
    args.extend(extra_args)
    completed = subprocess.run(args, cwd=str(root), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return completed.returncode, completed.stdout


def status_of(read_first: dict[str, str], exit_code: int) -> str:
    if exit_code != 0:
        return f"FAIL_EXIT_{exit_code}"
    return clean(read_first.get("STATUS"), "MISSING_READ_FIRST")


def count_action(rows: list[dict[str, str]], column: str, value: str) -> int:
    return sum(1 for row in rows if row.get(column) == value)


def by_ticker(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {clean(row.get("ticker")).upper(): row for row in rows if clean(row.get("ticker"))}


def safety_ok(*maps: dict[str, str]) -> bool:
    for data in maps:
        for key, expected in SAFETY_EXPECTED.items():
            actual = data.get(key)
            if actual is not None and actual != expected:
                return False
    return True


def determine_status(exit_codes: dict[str, int], required_paths: list[Path], safety_pass: bool) -> str:
    if any(code != 0 for code in exit_codes.values()):
        return "FAIL_V18_50A_REQUIRED_WRAPPER_NONZERO"
    if any(not path.exists() for path in required_paths):
        return "FAIL_V18_50A_REQUIRED_OUTPUT_MISSING"
    if not safety_pass:
        return "FAIL_V18_50A_SAFETY_FLAG_VIOLATION"
    return "PASS"


def top20_signature(rows: list[dict[str, str]]) -> list[tuple[str, str, str]]:
    out = []
    for row in rows[:20]:
        out.append((clean(row.get("rank")), clean(row.get("ticker")).upper(), clean(row.get("latest_price_date"))))
    return out


def sorted_by_rank(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    def key(row: dict[str, str]) -> tuple[int, str]:
        try:
            rank = int(float(clean(row.get("rank"))))
        except Exception:
            rank = 10**9
        return rank, clean(row.get("ticker")).upper()
    return sorted([dict(row) for row in rows if clean(row.get("ticker"))], key=key)


def current_source_ok(read50b: dict[str, str], current_top_rows: list[dict[str, str]], auth_rows: list[dict[str, str]]) -> bool:
    if not current_top_rows:
        return False
    auth_top20 = sorted_by_rank(auth_rows)[:20]
    if top20_signature(current_top_rows) != top20_signature(auth_top20):
        return False
    return (
        read50b.get("STATUS") == "PASS"
        and read50b.get("PATCH_VERSION") == "V18.50B-R2"
        and read50b.get("SOLE_WRITER_AUDIT_OK") == "TRUE"
        and read50b.get("CURRENT_TOP20_ALIAS_WRITTEN") == "TRUE"
        and read50b.get("CURRENT_TOP20_WRITE_ALLOWED") == "TRUE"
        and read50b.get("TRUE_PROVENANCE_REPAIRED") == "TRUE"
        and read50b.get("RECONCILIATION_OK") == "TRUE"
        and read50b.get("V18_35D_TOP20_MATCH_CURRENT_TOP20") == "TRUE"
        and read50b.get("DAILY_OPERATOR_ACTION_ENTRY_SOURCE_OK") == "TRUE"
    )


def packet_row(run_ts: str, section: str, item: str, value: str, details: str = "") -> dict[str, str]:
    return {
        "run_date": run_ts, "rank": "", "ticker": "", "latest_price_date": "",
        "source_policy_id": "", "source_chain": "", "simulation_action": "",
        "real_position_action": "", "section": section, "item": item,
        "value": value, "details": details,
    }


def build_top20_packet_rows(
    run_ts: str,
    current_top_rows: list[dict[str, str]],
    paper_rows: list[dict[str, str]],
    real_rows: list[dict[str, str]],
    source_policy_id: str,
) -> list[dict[str, str]]:
    paper_by_ticker = by_ticker(paper_rows)
    real_by_ticker = by_ticker(real_rows)
    rows: list[dict[str, str]] = []
    for top in current_top_rows[:20]:
        ticker = clean(top.get("ticker")).upper()
        paper = paper_by_ticker.get(ticker, {})
        real = real_by_ticker.get(ticker, {})
        rows.append({
            "run_date": run_ts,
            "rank": clean(top.get("rank")),
            "ticker": ticker,
            "latest_price_date": clean(top.get("latest_price_date")),
            "source_policy_id": source_policy_id,
            "source_chain": clean(top.get("current_top20_authoritative_source") or top.get("ranking_source_policy")),
            "simulation_action": clean(paper.get("simulation_action"), "NO_SIMULATION_ACTION"),
            "real_position_action": clean(real.get("real_position_advice"), "NO_REAL_POSITION_ACTION"),
            "section": "current_top20_action",
            "item": "Top20 candidate action row",
            "value": ticker,
            "details": clean(paper.get("reason") or real.get("reason"), ""),
        })
    return rows


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def build_report(values: dict[str, str], packet_rows: list[dict[str, str]], paper_rows: list[dict[str, str]], real_rows: list[dict[str, str]]) -> str:
    buy_tickers = [row["ticker"] for row in paper_rows if row.get("simulation_action") == "PAPER_BUY_CANDIDATE"]
    add_rows = [row for row in paper_rows if row.get("simulation_action") == "PAPER_ADD_REVIEW"]
    reduce_rows = [row for row in paper_rows if row.get("simulation_action") == "PAPER_REDUCE_REVIEW"]
    exit_rows = [row for row in paper_rows if row.get("simulation_action") == "PAPER_EXIT_REVIEW"]
    return "\n".join([
        "# V18.50A Daily Operator Action Entry",
        "",
        "## Operator Answers",
        f"1. Usable today: {values['DAILY_ACTION_ENTRY_USABLE']}",
        f"2. Real trade upload ledger checked: {values['REAL_TRADE_UPLOAD_CHECKED']}",
        f"3. Real position book found or rebuilt: found={values['REAL_POSITION_BOOK_FOUND']}; rebuilt={values['REAL_POSITION_BOOK_REBUILT']}",
        f"4. Real position book state write: {values['REAL_POSITION_BOOK_WRITTEN_TO_STATE']} (write requested: {values['WRITE_REAL_POSITION_BOOK_REQUESTED']})",
        f"5. Current simulation policy: {values['SIMULATION_DECISION']}",
        f"6. Policy confidence: {values['SOURCE_POLICY_CONFIDENCE']}",
        f"7. Paper buy candidates allowed today: {values['PAPER_BUY_CANDIDATE_COUNT']}",
        f"8. Paper buy candidate tickers: {', '.join(buy_tickers) if buy_tickers else 'NONE'}",
        f"9. Paper add/reduce/exit candidates: add={len(add_rows)}; reduce={len(reduce_rows)}; exit={len(exit_rows)}",
        f"10. Real-position advice available: {values['REAL_ADVICE_AVAILABLE']}",
        f"11. Real-position advice unavailable reason: {values['REAL_ADVICE_UNAVAILABLE_REASON']}",
        "12. Execution safety: no real trade execution, broker API, order generation, auto-buy, or auto-sell occurred.",
        "",
        "## Status Summary",
        markdown_table(packet_rows, ["section", "item", "value", "details"]),
        "",
        "## Paper Buy Candidates",
        markdown_table([row for row in paper_rows if row.get("simulation_action") == "PAPER_BUY_CANDIDATE"], ["ticker", "rank", "simulation_action", "event_risk", "options_risk", "reason"]) if buy_tickers else "No paper buy candidates.",
        "",
        "## Real Advice Preview",
        markdown_table(real_rows[:10], ["ticker", "rank", "real_position_advice", "reason"]) if real_rows else "No real advice rows available.",
        "",
        "## Safety Confirmation",
        "This is an orchestration/read-center layer only. It does not alter ranking logic, factor weights, Top20 selection, candidate scoring, buy/sell permission logic, broker behavior, order execution, or real/options trade execution.",
        "",
    ]) + "\n"


def write_read_first(path: Path, values: dict[str, str]) -> None:
    order = [
        "STATUS", "PATCH_VERSION", "PATCH_NAME", "V18_49D_STATUS", "V18_49A_STATUS",
        "V18_49B_STATUS", "V18_49C_STATUS", "REAL_TRADE_UPLOAD_CHECKED",
        "REAL_POSITION_BOOK_FOUND", "REAL_POSITION_BOOK_WRITTEN_TO_STATE",
        "WRITE_REAL_POSITION_BOOK_REQUESTED", "SOURCE_POLICY_ID",
        "SOURCE_POLICY_CONFIDENCE", "SIMULATION_DECISION", "PAPER_BUY_CANDIDATE_COUNT",
        "PAPER_ADD_CANDIDATE_COUNT", "PAPER_REDUCE_CANDIDATE_COUNT",
        "PAPER_EXIT_CANDIDATE_COUNT", "REAL_ADVICE_AVAILABLE",
        "REAL_ADVICE_UNAVAILABLE_REASON", "CURRENT_ALIAS_WRITTEN",
        "DAILY_OPERATOR_ACTION_ENTRY_SOURCE_OK", "DAILY_OPERATOR_ACTION_ENTRY_SOURCE_BLOCKED_REASON",
        "OFFICIAL_RANKING_CHANGED", "FACTOR_WEIGHTS_CHANGED", "OFFICIAL_BUY_PERMISSION_CHANGED",
        "OFFICIAL_SELL_PERMISSION_CHANGED", "REAL_TRADE_EXECUTION_ALLOWED",
        "OPTIONS_TRADE_EXECUTION_ALLOWED", "TRADING_EXECUTION_ALLOWED", "AUTO_TRADE",
        "AUTO_SELL", "BROKER_API_USED", "ORDER_EXECUTION_USED",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{key}: {values.get(key, '')}" for key in order) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.50A daily operator action entry.")
    parser.add_argument("--root", "--project-root", dest="root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write-current", action="store_true")
    parser.add_argument("--write-real-position-book-from-uploads", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_ts = datetime.now().astimezone().isoformat(timespec="seconds")
    wrappers = {
        "49D": root / "scripts/v18/run_v18_49D_real_trade_upload_ledger.ps1",
        "49A": root / "scripts/v18/run_v18_49A_factor_weight_buy_sell_policy_backtest.ps1",
        "49B": root / "scripts/v18/run_v18_49B_simulation_policy_weight_engine.ps1",
        "49C": root / "scripts/v18/run_v18_49C_dual_book_buy_sell_action_planner.ps1",
    }
    exit_codes: dict[str, int] = {}
    logs: dict[str, str] = {}

    d_args = ["-CreateTemplate"]
    if args.write_real_position_book_from_uploads:
        d_args.append("-WriteRealPositionBook")
    exit_codes["49D"], logs["49D"] = run_wrapper(wrappers["49D"], root, args.write_current, d_args)
    exit_codes["49A"], logs["49A"] = run_wrapper(wrappers["49A"], root, args.write_current, [])
    exit_codes["49B"], logs["49B"] = run_wrapper(wrappers["49B"], root, args.write_current, [])
    exit_codes["49C"], logs["49C"] = run_wrapper(wrappers["49C"], root, args.write_current, [])

    read49d = read_key_values(root / "outputs/v18/ops/V18_49D_READ_FIRST.txt")
    read49a = read_key_values(root / "outputs/v18/ops/V18_49A_READ_FIRST.txt")
    read49b = read_key_values(root / "outputs/v18/ops/V18_49B_READ_FIRST.txt")
    read49c = read_key_values(root / "outputs/v18/ops/V18_49C_READ_FIRST.txt")
    read50b = read_key_values(root / "outputs/v18/ops/V18_50B_R2_READ_FIRST.txt")
    current_top_rows = read_csv(root / "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv")
    auth_rows = read_csv(root / "outputs/v18/candidates/V18_35D_FULL_UNIVERSE_RECOMPUTED_RANKED_CANDIDATES.csv")
    paper_rows = read_csv(root / "outputs/v18/action_plan/V18_49C_SIMULATION_ACTION_PLAN.csv")
    real_rows = read_csv(root / "outputs/v18/action_plan/V18_49C_REAL_POSITION_ADVICE_PLAN.csv")

    required_paths = [
        root / "outputs/v18/ops/V18_49D_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_49A_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_49B_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_49C_READ_FIRST.txt",
        root / "outputs/v18/action_plan/V18_49C_SIMULATION_ACTION_PLAN.csv",
        root / "outputs/v18/action_plan/V18_49C_REAL_POSITION_ADVICE_PLAN.csv",
    ]
    safety_pass = safety_ok(read49d, read49a, read49b, read49c, read50b)
    status = determine_status(exit_codes, required_paths, safety_pass)
    source_ok = current_source_ok(read50b, current_top_rows, auth_rows)
    if not source_ok and status == "PASS":
        status = "FAIL_V18_50A_CURRENT_TOP20_SOURCE_NOT_AUTHORITATIVE"

    real_advice_available = read49c.get("REAL_POSITION_BOOK_FOUND") == "TRUE" and bool(real_rows)
    unavailable_reason = "NONE" if real_advice_available else "REAL_POSITION_BOOK_MISSING" if read49c.get("REAL_POSITION_BOOK_FOUND") != "TRUE" else "REAL_ADVICE_ROWS_MISSING"
    simulation_decision = clean(read49b.get("SOURCE_SIMULATION_POLICY_STYLE") or read49c.get("SOURCE_SIMULATION_POLICY_STYLE"))
    source_policy_id = clean(read49b.get("PRIMARY_POLICY_ID") or read49c.get("SOURCE_PRIMARY_POLICY_ID"))
    source_confidence = clean(read49b.get("POLICY_CONFIDENCE") or read49c.get("SOURCE_POLICY_CONFIDENCE"))

    values = {
        "STATUS": status,
        "PATCH_VERSION": PATCH_VERSION,
        "PATCH_NAME": PATCH_NAME,
        "V18_49D_STATUS": status_of(read49d, exit_codes["49D"]),
        "V18_49A_STATUS": status_of(read49a, exit_codes["49A"]),
        "V18_49B_STATUS": status_of(read49b, exit_codes["49B"]),
        "V18_49C_STATUS": status_of(read49c, exit_codes["49C"]),
        "REAL_TRADE_UPLOAD_CHECKED": "TRUE" if read49d else "FALSE",
        "REAL_POSITION_BOOK_FOUND": clean(read49c.get("REAL_POSITION_BOOK_FOUND"), "FALSE"),
        "REAL_POSITION_BOOK_REBUILT": clean(read49d.get("REAL_POSITION_BOOK_REBUILT"), "FALSE"),
        "REAL_POSITION_BOOK_WRITTEN_TO_STATE": clean(read49d.get("REAL_POSITION_BOOK_STATE_WRITTEN"), "FALSE"),
        "WRITE_REAL_POSITION_BOOK_REQUESTED": "TRUE" if args.write_real_position_book_from_uploads else "FALSE",
        "SOURCE_POLICY_ID": source_policy_id,
        "SOURCE_POLICY_CONFIDENCE": source_confidence,
        "SIMULATION_DECISION": simulation_decision,
        "PAPER_BUY_CANDIDATE_COUNT": str(count_action(paper_rows, "simulation_action", "PAPER_BUY_CANDIDATE")),
        "PAPER_ADD_CANDIDATE_COUNT": str(count_action(paper_rows, "simulation_action", "PAPER_ADD_REVIEW")),
        "PAPER_REDUCE_CANDIDATE_COUNT": str(count_action(paper_rows, "simulation_action", "PAPER_REDUCE_REVIEW")),
        "PAPER_EXIT_CANDIDATE_COUNT": str(count_action(paper_rows, "simulation_action", "PAPER_EXIT_REVIEW")),
        "REAL_ADVICE_AVAILABLE": "TRUE" if real_advice_available else "FALSE",
        "REAL_ADVICE_UNAVAILABLE_REASON": unavailable_reason,
        "CURRENT_ALIAS_WRITTEN": "FALSE",
        "DAILY_OPERATOR_ACTION_ENTRY_SOURCE_OK": "TRUE" if source_ok else "FALSE",
        "DAILY_OPERATOR_ACTION_ENTRY_SOURCE_BLOCKED_REASON": "NONE" if source_ok else clean(read50b.get("CURRENT_TOP20_WRITE_BLOCKED_REASON"), "CURRENT_TOP20_AUTH_MATCH_OR_R1_GATE_FAILED"),
        "DAILY_ACTION_ENTRY_USABLE": "TRUE" if not status.startswith("FAIL_") else "FALSE",
        **SAFETY_EXPECTED,
    }

    packet_rows = build_top20_packet_rows(run_ts, current_top_rows, paper_rows, real_rows, source_policy_id)
    packet_rows.extend([
        packet_row(run_ts, "status", "Daily action entry usable today", values["DAILY_ACTION_ENTRY_USABLE"], values["STATUS"]),
        packet_row(run_ts, "source", "Current Top20 source authoritative", values["DAILY_OPERATOR_ACTION_ENTRY_SOURCE_OK"], values["DAILY_OPERATOR_ACTION_ENTRY_SOURCE_BLOCKED_REASON"]),
        packet_row(run_ts, "real_upload", "Real trade upload ledger checked", values["REAL_TRADE_UPLOAD_CHECKED"], values["V18_49D_STATUS"]),
        packet_row(run_ts, "real_upload", "Real position book found", values["REAL_POSITION_BOOK_FOUND"], ""),
        packet_row(run_ts, "real_upload", "Real position book written to state", values["REAL_POSITION_BOOK_WRITTEN_TO_STATE"], f"write_requested={values['WRITE_REAL_POSITION_BOOK_REQUESTED']}"),
        packet_row(run_ts, "policy", "Current simulation policy", values["SIMULATION_DECISION"], values["SOURCE_POLICY_ID"]),
        packet_row(run_ts, "policy", "Policy confidence", values["SOURCE_POLICY_CONFIDENCE"], values["V18_49B_STATUS"]),
        packet_row(run_ts, "simulation", "Paper buy candidates allowed today", values["PAPER_BUY_CANDIDATE_COUNT"], ""),
        packet_row(run_ts, "simulation", "Paper add/reduce/exit counts", f"{values['PAPER_ADD_CANDIDATE_COUNT']}/{values['PAPER_REDUCE_CANDIDATE_COUNT']}/{values['PAPER_EXIT_CANDIDATE_COUNT']}", "add/reduce/exit"),
        packet_row(run_ts, "real_advice", "Real-position advice available", values["REAL_ADVICE_AVAILABLE"], values["REAL_ADVICE_UNAVAILABLE_REASON"]),
        packet_row(run_ts, "safety", "No execution/broker/order/autotrade", "TRUE", "broker_api=FALSE;order_execution=FALSE;auto_trade=DISABLED;auto_sell=DISABLED"),
    ])
    summary = {
        "run_date": run_ts,
        "status": values["STATUS"],
        "v18_49d_status": values["V18_49D_STATUS"],
        "v18_49a_status": values["V18_49A_STATUS"],
        "v18_49b_status": values["V18_49B_STATUS"],
        "v18_49c_status": values["V18_49C_STATUS"],
        "real_trade_upload_checked": values["REAL_TRADE_UPLOAD_CHECKED"],
        "real_position_book_found": values["REAL_POSITION_BOOK_FOUND"],
        "real_position_book_written_to_state": values["REAL_POSITION_BOOK_WRITTEN_TO_STATE"],
        "write_real_position_book_requested": values["WRITE_REAL_POSITION_BOOK_REQUESTED"],
        "source_policy_id": values["SOURCE_POLICY_ID"],
        "source_policy_confidence": values["SOURCE_POLICY_CONFIDENCE"],
        "simulation_decision": values["SIMULATION_DECISION"],
        "paper_buy_candidate_count": values["PAPER_BUY_CANDIDATE_COUNT"],
        "paper_add_candidate_count": values["PAPER_ADD_CANDIDATE_COUNT"],
        "paper_reduce_candidate_count": values["PAPER_REDUCE_CANDIDATE_COUNT"],
        "paper_exit_candidate_count": values["PAPER_EXIT_CANDIDATE_COUNT"],
        "real_advice_available": values["REAL_ADVICE_AVAILABLE"],
        "real_advice_unavailable_reason": values["REAL_ADVICE_UNAVAILABLE_REASON"],
        "official_ranking_changed": "FALSE",
        "factor_weights_changed": "FALSE",
        "real_trade_execution_allowed": "FALSE",
        "broker_api_used": "FALSE",
        "order_execution_used": "FALSE",
    }

    out_dir = root / "outputs/v18/action_plan"
    write_csv(out_dir / "V18_50A_DAILY_OPERATOR_ACTION_PACKET.csv", packet_rows, PACKET_COLUMNS)
    write_csv(out_dir / "V18_50A_DAILY_OPERATOR_ACTION_SUMMARY.csv", [summary], SUMMARY_COLUMNS)
    report = build_report(values, packet_rows, paper_rows, real_rows)
    report_path = root / "outputs/v18/read_center/V18_50A_DAILY_OPERATOR_ACTION_ENTRY_REPORT.md"
    current_path = root / "outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_ACTION_ENTRY.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    if args.write_current:
        current_path.write_text(report, encoding="utf-8")
        values["CURRENT_ALIAS_WRITTEN"] = "TRUE"
    write_read_first(root / "outputs/v18/ops/V18_50A_READ_FIRST.txt", values)

    print(f"STATUS: {status}")
    print(f"V18_49D_STATUS: {values['V18_49D_STATUS']}")
    print(f"V18_49A_STATUS: {values['V18_49A_STATUS']}")
    print(f"V18_49B_STATUS: {values['V18_49B_STATUS']}")
    print(f"V18_49C_STATUS: {values['V18_49C_STATUS']}")
    print(f"PAPER_BUY_CANDIDATE_COUNT: {values['PAPER_BUY_CANDIDATE_COUNT']}")
    print(f"REAL_ADVICE_AVAILABLE: {values['REAL_ADVICE_AVAILABLE']}")
    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
