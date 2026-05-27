from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")

STATUS_OK_FULL = "OK_V18_13D_DAILY_COMMAND_CENTER_READY"
STATUS_OK_REFRESH = "OK_V18_13D_READ_CENTER_REFRESH_READY"
STATUS_FAIL_A = "FAIL_V18_13D_UNIFIED_DAILY_FAILED"
STATUS_WARN_B = "WARN_V18_13D_RANKED_CANDIDATES_FAILED"
STATUS_WARN_C = "WARN_V18_13D_UNIFIED_RANKED_LINK_FAILED"
STATUS_FAIL_DANGEROUS = "FAIL_V18_13D_DANGEROUS_TOKEN_FOUND"

RUN_MODE_FULL = "FULL_DAILY_COMMAND_CENTER"
RUN_MODE_REFRESH = "READ_CENTER_REFRESH_ONLY"

OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
READ_ONLY = "TRUE"
COMMAND_CENTER_ONLY = "TRUE"

DANGEROUS_TOKENS = (
    "BUY_NOW",
    "SELL_NOW",
    "EXECUTE_ORDER",
    "PLACE_ORDER",
    "AUTO_TRADE: ENABLED",
    "AUTO_SELL: ENABLED",
)

SUMMARY_FIELDS = ["metric", "value"]
AUDIT_FIELDS = [
    "component",
    "source_file",
    "exists",
    "row_count",
    "parse_status",
    "status_value",
    "note",
]

INPUTS = {
    "V18_13A_READ_FIRST": "outputs/v18/read_center/V18_13A_READ_FIRST.txt",
    "V18_13B_READ_FIRST": "outputs/v18/read_center/V18_13B_READ_FIRST.txt",
    "V18_13C_READ_FIRST": "outputs/v18/read_center/V18_13C_READ_FIRST.txt",
    "V18_13C_MAIN_READ": "outputs/v18/read_center/V18_13C_CURRENT_UNIFIED_DAILY_WITH_RANKED_CANDIDATES.md",
    "V18_13B_CANDIDATES": "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv",
    "RUN_LOG": "outputs/v18/ops/V18_13D_CURRENT_DAILY_COMMAND_CENTER_RUN_LOG.csv",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def rel_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def first_value(path: Path, key: str) -> str:
    lines = [line.strip() for line in read_text(path).splitlines()]
    target = key if key.endswith(":") else f"{key}:"
    bullet_target = f"- {target}"
    for i, line in enumerate(lines):
        if line == target:
            for nxt in lines[i + 1 :]:
                if nxt:
                    return nxt.strip("` ")
        if line.startswith(target):
            value = line[len(target) :].strip()
            if value:
                return value.strip("` ")
        if line.startswith(bullet_target):
            value = line[len(bullet_target) :].strip()
            if value:
                return value.strip("` ")
    return ""


def step_status(rows: Sequence[Dict[str, str]], step: str) -> str:
    for row in rows:
        if row.get("step") == step:
            return row.get("status", "")
    return ""


def step_note(rows: Sequence[Dict[str, str]], step: str) -> str:
    for row in rows:
        if row.get("step") == step:
            return row.get("note", "")
    return ""


def audit_row(component: str, path: Path, row_count: int, parse_status: str, status_value: str, note: str) -> Dict[str, str]:
    return {
        "component": component,
        "source_file": str(path),
        "exists": "YES" if path.exists() else "NO",
        "row_count": str(row_count),
        "parse_status": parse_status,
        "status_value": status_value,
        "note": note,
    }


def markdown_table(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> List[str]:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        vals = [str(row.get(field, "")).replace("|", "/") for field in fields]
        out.append("| " + " | ".join(vals) + " |")
    return out


def dangerous_token_hits(paths: Sequence[Path]) -> List[str]:
    hits: List[str] = []
    for path in paths:
        text = read_text(path)
        for token in DANGEROUS_TOKENS:
            if token in text:
                hits.append(f"{path}:{token}")
    return hits


def build_outputs(root: Path) -> Dict[str, str]:
    out_dir = root / "outputs/v18/read_center"
    ops_dir = root / "outputs/v18/ops"
    read_first_path = out_dir / "V18_13D_READ_FIRST.txt"
    read_center_path = out_dir / "V18_13D_CURRENT_DAILY_COMMAND_CENTER.md"
    summary_path = out_dir / "V18_13D_CURRENT_DAILY_COMMAND_CENTER_SUMMARY.csv"
    audit_path = out_dir / "V18_13D_CURRENT_DAILY_COMMAND_CENTER_INPUT_AUDIT.csv"
    run_log_path = ops_dir / "V18_13D_CURRENT_DAILY_COMMAND_CENTER_RUN_LOG.csv"

    a_read_first = root / INPUTS["V18_13A_READ_FIRST"]
    b_read_first = root / INPUTS["V18_13B_READ_FIRST"]
    c_read_first = root / INPUTS["V18_13C_READ_FIRST"]
    c_main_read = root / INPUTS["V18_13C_MAIN_READ"]
    b_candidates = root / INPUTS["V18_13B_CANDIDATES"]

    run_log_rows, _, run_log_parse = read_csv(run_log_path)
    candidate_rows, _, candidate_parse = read_csv(b_candidates)

    official_step = step_status(run_log_rows, "OFFICIAL_DAILY")
    a_step = step_status(run_log_rows, "V18_13A")
    b_step = step_status(run_log_rows, "V18_13B")
    c_step = step_status(run_log_rows, "V18_13C")
    official_skipped = official_step == "SKIPPED"

    run_mode = RUN_MODE_REFRESH if official_skipped else RUN_MODE_FULL
    official_status = "SKIPPED" if official_skipped else (first_value(a_read_first, "OFFICIAL_DAILY_STATUS") or step_note(run_log_rows, "OFFICIAL_DAILY") or "UNKNOWN")
    v18_13a_status = first_value(a_read_first, "STATUS") or ("FAILED" if a_step == "FAIL" else "MISSING")
    v18_13b_status = first_value(b_read_first, "STATUS") or ("FAILED" if b_step == "FAIL" else "MISSING")
    v18_13c_status = first_value(c_read_first, "STATUS") or ("FAILED" if c_step == "FAIL" else "MISSING")

    rank_source_status = first_value(c_read_first, "RANK_SOURCE_STATUS") or first_value(b_read_first, "RANK_SOURCE_STATUS") or "MISSING"
    second_stage_count = first_value(c_read_first, "SECOND_STAGE_COUNT") or first_value(b_read_first, "SECOND_STAGE_COUNT") or "0"
    scored_ticker_count = first_value(c_read_first, "SCORED_TICKER_COUNT") or "0"
    unscored_ticker_count = first_value(c_read_first, "UNSCORED_TICKER_COUNT") or "0"
    top_5 = first_value(c_read_first, "TOP_5_TICKERS") or first_value(b_read_first, "TOP_5_TICKERS")

    a_failed = a_step == "FAIL" or not v18_13a_status.startswith("OK_")
    b_failed = b_step == "FAIL" or b_step == "SKIPPED" or not v18_13b_status.startswith("OK_")
    c_failed = c_step == "FAIL" or c_step == "SKIPPED" or not v18_13c_status.startswith("OK_")

    if a_failed:
        status = STATUS_FAIL_A
    elif b_failed:
        status = STATUS_WARN_B
    elif c_failed:
        status = STATUS_WARN_C
    elif official_skipped:
        status = STATUS_OK_REFRESH
    else:
        status = STATUS_OK_FULL

    today_main_read = rel_path(root, c_main_read) if not c_failed and c_main_read.exists() else rel_path(root, a_read_first)
    today_ranked_candidates_csv = rel_path(root, b_candidates) if not b_failed and b_candidates.exists() else "UNAVAILABLE"

    values = {
        "STATUS": status,
        "RUN_MODE": run_mode,
        "OFFICIAL_DAILY_STATUS": official_status,
        "V18_13A_STATUS": v18_13a_status,
        "V18_13B_STATUS": v18_13b_status,
        "V18_13C_STATUS": v18_13c_status,
        "RANK_SOURCE_STATUS": rank_source_status,
        "SECOND_STAGE_COUNT": second_stage_count,
        "SCORED_TICKER_COUNT": scored_ticker_count,
        "UNSCORED_TICKER_COUNT": unscored_ticker_count,
        "TOP_5_TICKERS": top_5,
        "TODAY_MAIN_READ": today_main_read,
        "TODAY_RANKED_CANDIDATES_CSV": today_ranked_candidates_csv,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "READ_ONLY": READ_ONLY,
        "COMMAND_CENTER_ONLY": COMMAND_CENTER_ONLY,
        "READ_FIRST": rel_path(root, read_first_path),
        "MAIN_READ": rel_path(root, read_center_path),
    }

    audit_rows = [
        audit_row("V18_13A_READ_FIRST", a_read_first, 0, "OK_TEXT" if a_read_first.exists() else "MISSING", v18_13a_status, "REQUIRED_INPUT"),
        audit_row("V18_13B_READ_FIRST", b_read_first, 0, "OK_TEXT" if b_read_first.exists() else "MISSING", v18_13b_status, "RANKED_INPUT"),
        audit_row("V18_13C_READ_FIRST", c_read_first, 0, "OK_TEXT" if c_read_first.exists() else "MISSING", v18_13c_status, "LINK_INPUT"),
        audit_row("V18_13C_MAIN_READ", c_main_read, 0, "OK_TEXT" if c_main_read.exists() else "MISSING", v18_13c_status, "MAIN_READ_INPUT"),
        audit_row("V18_13B_CANDIDATES", b_candidates, len(candidate_rows), candidate_parse, rank_source_status, "RANKED_CANDIDATE_INPUT"),
        audit_row("RUN_LOG", run_log_path, len(run_log_rows), run_log_parse, status, "COMMAND_CENTER_RUN_LOG"),
    ]
    for key in ("OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL", "READ_ONLY", "COMMAND_CENTER_ONLY"):
        audit_rows.append(
            {
                "component": key,
                "source_file": "V18.13D",
                "exists": "YES",
                "row_count": "0",
                "parse_status": "OK_GUARDRAIL",
                "status_value": values[key],
                "note": "OUTPUT_GUARDRAIL",
            }
        )

    top_fields = ["rank", "ticker", "composite_candidate_score", "final_action", "technical_status", "latest_price_date", "latest_close"]
    run_fields = ["timestamp", "step", "status", "exit_code", "script", "note"]
    report = [
        "# V18.13D Daily Command Center",
        "",
        "## Status",
        "",
        *[f"- {key}: {values[key]}" for key in (
            "STATUS",
            "RUN_MODE",
            "OFFICIAL_DAILY_STATUS",
            "V18_13A_STATUS",
            "V18_13B_STATUS",
            "V18_13C_STATUS",
            "RANK_SOURCE_STATUS",
            "SECOND_STAGE_COUNT",
            "SCORED_TICKER_COUNT",
            "UNSCORED_TICKER_COUNT",
            "TOP_5_TICKERS",
            "TODAY_MAIN_READ",
            "TODAY_RANKED_CANDIDATES_CSV",
            "OFFICIAL_DECISION_IMPACT",
            "AUTO_TRADE",
            "AUTO_SELL",
            "READ_ONLY",
            "COMMAND_CENTER_ONLY",
        )],
        "",
        "## Run Log",
    ]
    report.extend(markdown_table(run_log_rows, run_fields) if run_log_rows else ["No run log rows available."])
    report.extend(["", "## Top Ranked Candidates"])
    if not b_failed and candidate_rows:
        report.extend(markdown_table(candidate_rows[:10], top_fields))
    else:
        report.append("Ranked candidates are unavailable for this run.")
    report.extend(
        [
            "",
            "## Read Paths",
            f"- Main read: {values['TODAY_MAIN_READ']}",
            f"- Ranked candidates CSV: {values['TODAY_RANKED_CANDIDATES_CSV']}",
            "",
            "## Limitations",
            "- The command center orchestrates local daily read-center refresh steps only.",
            "- Ranked candidates are research priority only and are not official trade actions.",
            "- Official decision logic is owned by the existing official daily chain and is not changed here.",
        ]
    )

    read_first = "\n".join([f"{key}: {values[key]}" for key in (
        "STATUS",
        "RUN_MODE",
        "OFFICIAL_DAILY_STATUS",
        "V18_13A_STATUS",
        "V18_13B_STATUS",
        "V18_13C_STATUS",
        "RANK_SOURCE_STATUS",
        "SECOND_STAGE_COUNT",
        "SCORED_TICKER_COUNT",
        "UNSCORED_TICKER_COUNT",
        "TOP_5_TICKERS",
        "TODAY_MAIN_READ",
        "TODAY_RANKED_CANDIDATES_CSV",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "READ_ONLY",
        "COMMAND_CENTER_ONLY",
        "MAIN_READ",
    )]) + "\n"

    summary_rows = [{"metric": key, "value": value} for key, value in values.items()]
    write_text(read_center_path, "\n".join(report) + "\n")
    write_text(read_first_path, read_first)
    write_csv(summary_path, summary_rows, SUMMARY_FIELDS)
    write_csv(audit_path, audit_rows, AUDIT_FIELDS)

    output_paths = [read_first_path, read_center_path, summary_path, audit_path]
    hits = dangerous_token_hits(output_paths)
    if hits:
        values["STATUS"] = STATUS_FAIL_DANGEROUS
        summary_rows = [{"metric": key, "value": value} for key, value in values.items()]
        write_csv(summary_path, summary_rows, SUMMARY_FIELDS)
        write_text(read_first_path, read_first.replace(f"STATUS: {status}", f"STATUS: {STATUS_FAIL_DANGEROUS}"))
        raise RuntimeError(STATUS_FAIL_DANGEROUS)

    for key in (
        "STATUS",
        "RUN_MODE",
        "OFFICIAL_DAILY_STATUS",
        "V18_13A_STATUS",
        "V18_13B_STATUS",
        "V18_13C_STATUS",
        "RANK_SOURCE_STATUS",
        "SECOND_STAGE_COUNT",
        "SCORED_TICKER_COUNT",
        "UNSCORED_TICKER_COUNT",
        "TOP_5_TICKERS",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "READ_ONLY",
        "COMMAND_CENTER_ONLY",
        "READ_FIRST",
        "MAIN_READ",
    ):
        print(f"{key}: {values.get(key, '')}")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.13D daily command center summary")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    try:
        values = build_outputs(Path(args.root))
        return 0 if values["STATUS"] not in {STATUS_FAIL_A, STATUS_FAIL_DANGEROUS} else 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
