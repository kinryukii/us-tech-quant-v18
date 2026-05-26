from __future__ import annotations

"""V18.12F shadow research daily with sell timing read center.

This script is additive and shadow-only. It summarizes the existing V18 shadow
research daily entry together with the V18.12E sell timing daily wrapper.
"""

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
STATUS_OK = "OK_V18_12F_SHADOW_RESEARCH_DAILY_WITH_SELL_TIMING_READY"
STATUS_WARN = "WARN_V18_12F_SHADOW_RESEARCH_DAILY_WITH_SELL_TIMING_INCOMPLETE"
STATUS_SELL_TIMING_DEPENDENCY_MISSING = "FAIL_V18_12F_SELL_TIMING_DEPENDENCY_MISSING"
MODE = "SHADOW_ONLY"
OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_SELL = "DISABLED"
AUTO_TRADE = "DISABLED"

SUMMARY_FIELDS = [
    "section",
    "metric",
    "value",
    "status",
    "source_file",
    "official_decision_impact",
    "auto_sell",
    "auto_trade",
]

AUDIT_FIELDS = [
    "component",
    "source_file",
    "exists",
    "row_count",
    "parse_status",
    "status_value",
    "note",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp932", "gbk"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: List[Dict[str, str]], fields: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def read_first_value(path: Path, key: str) -> str:
    lines = [line.strip() for line in read_text(path).splitlines()]
    target = key if key.endswith(":") else f"{key}:"
    for i, line in enumerate(lines):
        if line == target:
            for nxt in lines[i + 1 :]:
                if nxt:
                    return nxt
        if line.startswith(target):
            value = line[len(target) :].strip()
            if value:
                return value
    return ""


def metric_row(section: str, metric: str, value: str, status: str, source_file: str) -> Dict[str, str]:
    return {
        "section": section,
        "metric": metric,
        "value": str(value),
        "status": status,
        "source_file": source_file,
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_sell": AUTO_SELL,
        "auto_trade": AUTO_TRADE,
    }


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


def value_or_zero(value: str) -> str:
    return value if value != "" else "0"


def shadow_status_ok(status: str) -> bool:
    return status.startswith("OK_") or status == "SKIPPED_USE_EXISTING_OUTPUTS"


def build_outputs(root: Path, shadow_status: str, shadow_exit_code: int, sell_timing_status: str, sell_timing_exit_code: int) -> Dict[str, str]:
    out_dir = root / "outputs/v18/sell_timing"
    read_center_path = out_dir / "V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_READ_CENTER.md"
    read_first_path = out_dir / "V18_12F_READ_FIRST.txt"
    summary_path = out_dir / "V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_SUMMARY.csv"
    audit_path = out_dir / "V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_INPUT_AUDIT.csv"

    shadow_wrapper = root / "scripts/v18/run_v18_current_shadow_research_daily.ps1"
    sell_timing_wrapper = root / "scripts/v18/run_v18_12E_sell_timing_daily_wrapper.ps1"
    shadow_read_first = root / "outputs/v18/read_center/V18_CURRENT_SHADOW_RESEARCH_DAILY_READ_FIRST.txt"
    sell_timing_read_first = root / "outputs/v18/sell_timing/V18_12E_READ_FIRST.txt"
    sell_timing_summary = root / "outputs/v18/sell_timing/V18_12E_CURRENT_SELL_TIMING_DAILY_SUMMARY.csv"
    sell_timing_audit = root / "outputs/v18/sell_timing/V18_12E_CURRENT_SELL_TIMING_DAILY_INPUT_AUDIT.csv"
    tracker_path = root / "outputs/v18/sell_timing/V18_CURRENT_EXIT_SIGNAL_FORWARD_TRACKER.csv"
    validation_path = root / "outputs/v18/sell_timing/V18_12D_CURRENT_EXIT_SIGNAL_FORWARD_VALIDATION.csv"

    audit_rows: List[Dict[str, str]] = []
    summary_rows: List[Dict[str, str]] = []

    shadow_read_first_status = read_first_value(shadow_read_first, "STATUS") if shadow_read_first.exists() else "MISSING"
    sell_timing_read_first_status = read_first_value(sell_timing_read_first, "STATUS") if sell_timing_read_first.exists() else "MISSING"

    values = {
        "POSITION_COUNT": value_or_zero(read_first_value(sell_timing_read_first, "POSITION_COUNT")),
        "ACTIONABLE_EXIT_COUNT": value_or_zero(read_first_value(sell_timing_read_first, "ACTIONABLE_EXIT_COUNT")),
        "TECHNICAL_LABEL_SOURCE_COUNT": value_or_zero(read_first_value(sell_timing_read_first, "TECHNICAL_LABEL_SOURCE_COUNT")),
        "LIFECYCLE_STAGE_COUNT": value_or_zero(read_first_value(sell_timing_read_first, "LIFECYCLE_STAGE_COUNT")),
        "TRACKER_ROWS": value_or_zero(read_first_value(sell_timing_read_first, "TRACKER_ROWS")),
        "FORWARD_COMPLETE_ROWS": value_or_zero(read_first_value(sell_timing_read_first, "FORWARD_COMPLETE_ROWS")),
        "PENDING_FORWARD_ROWS": value_or_zero(read_first_value(sell_timing_read_first, "PENDING_FORWARD_ROWS")),
    }

    tracker_rows, _, tracker_parse_status = read_csv(tracker_path)
    validation_rows, _, validation_parse_status = read_csv(validation_path)
    summary_rows_e, _, summary_parse_status = read_csv(sell_timing_summary)
    audit_rows_e, _, audit_parse_status = read_csv(sell_timing_audit)

    audit_rows.extend(
        [
            audit_row("SHADOW_RESEARCH_WRAPPER", shadow_wrapper, 0, "SCRIPT" if shadow_wrapper.exists() else "MISSING", shadow_status, f"EXIT_CODE={shadow_exit_code}"),
            audit_row("SHADOW_RESEARCH_READ_FIRST", shadow_read_first, 0, "OK_TEXT" if shadow_read_first.exists() else "MISSING", shadow_read_first_status, "CURRENT_SHADOW_RESEARCH_DAILY_READ_FIRST"),
            audit_row("V18.12E_SELL_TIMING_WRAPPER", sell_timing_wrapper, 0, "SCRIPT" if sell_timing_wrapper.exists() else "MISSING", sell_timing_status, f"EXIT_CODE={sell_timing_exit_code}"),
            audit_row("V18.12E_READ_FIRST", sell_timing_read_first, 0, "OK_TEXT" if sell_timing_read_first.exists() else "MISSING", sell_timing_read_first_status, "SELL_TIMING_DAILY_READ_FIRST"),
            audit_row("V18.12E_SUMMARY", sell_timing_summary, len(summary_rows_e), summary_parse_status, sell_timing_read_first_status, "SELL_TIMING_DAILY_SUMMARY"),
            audit_row("V18.12E_INPUT_AUDIT", sell_timing_audit, len(audit_rows_e), audit_parse_status, sell_timing_read_first_status, "SELL_TIMING_DAILY_INPUT_AUDIT"),
            audit_row("EXIT_SIGNAL_TRACKER", tracker_path, len(tracker_rows), tracker_parse_status, "", "TRACKER_ROWS"),
            audit_row("EXIT_SIGNAL_FORWARD_VALIDATION", validation_path, len(validation_rows), validation_parse_status, "", "FORWARD_VALIDATION_ROWS"),
        ]
    )

    if sell_timing_status.startswith("MISSING_CRITICAL_V18_12E"):
        status = STATUS_SELL_TIMING_DEPENDENCY_MISSING
    else:
        status = STATUS_OK
    if status == STATUS_OK and (
        not shadow_status_ok(shadow_status) or not sell_timing_status.startswith("OK_") or not sell_timing_read_first_status.startswith("OK_")
    ):
        status = STATUS_WARN

    summary_rows.extend(
        [
            metric_row("run_status", "SHADOW_RESEARCH_STATUS", shadow_status, "OK" if shadow_status_ok(shadow_status) else "WARN", str(shadow_wrapper)),
            metric_row("run_status", "SELL_TIMING_STATUS", sell_timing_status, "OK" if sell_timing_status.startswith("OK_") else "WARN", str(sell_timing_wrapper)),
            metric_row("run_status", "SHADOW_RESEARCH_READ_FIRST_STATUS", shadow_read_first_status, "OK" if shadow_read_first_status.startswith("OK_") else "WARN", str(shadow_read_first)),
            metric_row("run_status", "SELL_TIMING_READ_FIRST_STATUS", sell_timing_read_first_status, "OK" if sell_timing_read_first_status.startswith("OK_") else "WARN", str(sell_timing_read_first)),
        ]
    )
    for key, value in values.items():
        summary_rows.append(metric_row("daily_summary", key, value, "OK", str(sell_timing_read_first)))
    summary_rows.extend(
        [
            metric_row("guardrails", "OFFICIAL_DECISION_IMPACT", OFFICIAL_DECISION_IMPACT, "OK", "V18.12F"),
            metric_row("guardrails", "AUTO_SELL", AUTO_SELL, "OK", "V18.12F"),
            metric_row("guardrails", "AUTO_TRADE", AUTO_TRADE, "OK", "V18.12F"),
        ]
    )

    report = [
        "# V18.12F Shadow Research Daily With Sell Timing Read Center",
        "",
        "## Status",
        "",
        f"- STATUS: {status}",
        f"- MODE: {MODE}",
        f"- SHADOW_RESEARCH_STATUS: {shadow_status}",
        f"- SELL_TIMING_STATUS: {sell_timing_status}",
        f"- POSITION_COUNT: {values['POSITION_COUNT']}",
        f"- ACTIONABLE_EXIT_COUNT: {values['ACTIONABLE_EXIT_COUNT']}",
        f"- TECHNICAL_LABEL_SOURCE_COUNT: {values['TECHNICAL_LABEL_SOURCE_COUNT']}",
        f"- LIFECYCLE_STAGE_COUNT: {values['LIFECYCLE_STAGE_COUNT']}",
        f"- TRACKER_ROWS: {values['TRACKER_ROWS']}",
        f"- FORWARD_COMPLETE_ROWS: {values['FORWARD_COMPLETE_ROWS']}",
        f"- PENDING_FORWARD_ROWS: {values['PENDING_FORWARD_ROWS']}",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "",
        "## Guardrails",
        "",
        "- This is shadow-only research integration, not an official sell decision.",
        "- Fast safe mode may reuse existing shadow research outputs without rerunning the full shadow research chain.",
        "- It does not replace the official daily entry and does not affect official decisions.",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "",
        "## Inputs",
        "",
        f"- SHADOW_RESEARCH_READ_FIRST: {shadow_read_first}",
        f"- SELL_TIMING_READ_FIRST: {sell_timing_read_first}",
        f"- SUMMARY_CSV: {summary_path}",
        f"- INPUT_AUDIT: {audit_path}",
    ]

    read_first = "\n".join(
        [
            "V18.12F SHADOW RESEARCH DAILY WITH SELL TIMING READ FIRST",
            "",
            "STATUS:",
            status,
            "",
            "SHADOW_RESEARCH_STATUS:",
            shadow_status,
            "",
            "SELL_TIMING_STATUS:",
            sell_timing_status,
            "",
            "POSITION_COUNT:",
            values["POSITION_COUNT"],
            "",
            "ACTIONABLE_EXIT_COUNT:",
            values["ACTIONABLE_EXIT_COUNT"],
            "",
            "TECHNICAL_LABEL_SOURCE_COUNT:",
            values["TECHNICAL_LABEL_SOURCE_COUNT"],
            "",
            "LIFECYCLE_STAGE_COUNT:",
            values["LIFECYCLE_STAGE_COUNT"],
            "",
            "TRACKER_ROWS:",
            values["TRACKER_ROWS"],
            "",
            "FORWARD_COMPLETE_ROWS:",
            values["FORWARD_COMPLETE_ROWS"],
            "",
            "PENDING_FORWARD_ROWS:",
            values["PENDING_FORWARD_ROWS"],
            "",
            "OFFICIAL_DECISION_IMPACT:",
            OFFICIAL_DECISION_IMPACT,
            "",
            "AUTO_SELL:",
            AUTO_SELL,
            "",
            "AUTO_TRADE:",
            AUTO_TRADE,
            "",
            "READ_CENTER:",
            str(read_center_path),
            "",
            "SUMMARY_CSV:",
            str(summary_path),
            "",
            "INPUT_AUDIT:",
            str(audit_path),
            "",
        ]
    )

    write_csv(summary_path, summary_rows, SUMMARY_FIELDS)
    write_csv(audit_path, audit_rows, AUDIT_FIELDS)
    write_text(read_center_path, "\n".join(report) + "\n")
    write_text(read_first_path, read_first)

    return {
        "STATUS": status,
        "SHADOW_RESEARCH_STATUS": shadow_status,
        "SELL_TIMING_STATUS": sell_timing_status,
        **values,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_SELL": AUTO_SELL,
        "AUTO_TRADE": AUTO_TRADE,
        "READ_CENTER": str(read_center_path),
        "SUMMARY_CSV": str(summary_path),
        "INPUT_AUDIT": str(audit_path),
        "READ_FIRST": str(read_first_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.12F shadow research with sell timing read center.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    parser.add_argument("--shadow-status", default="NOT_RUN")
    parser.add_argument("--shadow-exit-code", type=int, default=0)
    parser.add_argument("--sell-timing-status", default="NOT_RUN")
    parser.add_argument("--sell-timing-exit-code", type=int, default=0)
    args = parser.parse_args()

    result = build_outputs(
        Path(args.root),
        args.shadow_status,
        args.shadow_exit_code,
        args.sell_timing_status,
        args.sell_timing_exit_code,
    )
    for key in [
        "STATUS",
        "SHADOW_RESEARCH_STATUS",
        "SELL_TIMING_STATUS",
        "POSITION_COUNT",
        "ACTIONABLE_EXIT_COUNT",
        "TECHNICAL_LABEL_SOURCE_COUNT",
        "LIFECYCLE_STAGE_COUNT",
        "TRACKER_ROWS",
        "FORWARD_COMPLETE_ROWS",
        "PENDING_FORWARD_ROWS",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_SELL",
        "AUTO_TRADE",
        "READ_CENTER",
        "SUMMARY_CSV",
        "INPUT_AUDIT",
        "READ_FIRST",
    ]:
        print(f"{key}: {result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
