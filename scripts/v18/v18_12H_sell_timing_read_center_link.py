from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
STATUS_OK = "OK_V18_12H_SELL_TIMING_READ_CENTER_LINK_READY"
STATUS_WARN = "WARN_V18_12H_SELL_TIMING_READ_CENTER_LINK_WITH_MISSING_INPUTS"
SELL_TIMING_LINK_STATUS_OK = "OK_LINKED_TO_V18_12F_SELL_TIMING_READ_CENTER"
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


def value_or_zero(value: str) -> str:
    return value if value != "" else "0"


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


def build_outputs(root: Path) -> Dict[str, str]:
    out_dir = root / "outputs/v18/read_center"
    read_link_path = out_dir / "V18_12H_CURRENT_SELL_TIMING_READ_LINK.md"
    read_first_path = out_dir / "V18_12H_READ_FIRST.txt"
    summary_path = out_dir / "V18_12H_CURRENT_SELL_TIMING_READ_LINK_SUMMARY.csv"
    audit_path = out_dir / "V18_12H_CURRENT_SELL_TIMING_READ_LINK_INPUT_AUDIT.csv"

    f_read_first = root / "outputs/v18/sell_timing/V18_12F_READ_FIRST.txt"
    f_read_center = root / "outputs/v18/sell_timing/V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_READ_CENTER.md"
    f_summary = root / "outputs/v18/sell_timing/V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_SUMMARY.csv"
    e_read_first = root / "outputs/v18/sell_timing/V18_12E_READ_FIRST.txt"
    g_read_first = root / "outputs/v18/ops/V18_12G_READ_FIRST.txt"

    f_summary_rows, _, f_summary_parse = read_csv(f_summary)

    values = {
        "V18_12F_STATUS": read_first_value(f_read_first, "STATUS") if f_read_first.exists() else "MISSING",
        "SHADOW_RESEARCH_STATUS": read_first_value(f_read_first, "SHADOW_RESEARCH_STATUS") if f_read_first.exists() else "MISSING",
        "SELL_TIMING_STATUS": read_first_value(f_read_first, "SELL_TIMING_STATUS") if f_read_first.exists() else "MISSING",
        "POSITION_COUNT": value_or_zero(read_first_value(f_read_first, "POSITION_COUNT")),
        "ACTIONABLE_EXIT_COUNT": value_or_zero(read_first_value(f_read_first, "ACTIONABLE_EXIT_COUNT")),
        "TECHNICAL_LABEL_SOURCE_COUNT": value_or_zero(read_first_value(f_read_first, "TECHNICAL_LABEL_SOURCE_COUNT")),
        "LIFECYCLE_STAGE_COUNT": value_or_zero(read_first_value(f_read_first, "LIFECYCLE_STAGE_COUNT")),
        "TRACKER_ROWS": value_or_zero(read_first_value(f_read_first, "TRACKER_ROWS")),
        "FORWARD_COMPLETE_ROWS": value_or_zero(read_first_value(f_read_first, "FORWARD_COMPLETE_ROWS")),
        "PENDING_FORWARD_ROWS": value_or_zero(read_first_value(f_read_first, "PENDING_FORWARD_ROWS")),
        "CLEANUP_AUDIT_STATUS": read_first_value(g_read_first, "STATUS") if g_read_first.exists() else "MISSING",
    }

    required_inputs = [
        ("V18.12F_READ_FIRST", f_read_first, "OK_TEXT" if f_read_first.exists() else "MISSING", values["V18_12F_STATUS"], "PRIMARY_STATUS_SOURCE"),
        ("V18.12F_READ_CENTER", f_read_center, "OK_TEXT" if f_read_center.exists() else "MISSING", "", "PRIMARY_READ_CENTER_LINK"),
        ("V18.12F_SUMMARY", f_summary, f_summary_parse, values["V18_12F_STATUS"], "SUMMARY_CSV"),
        ("V18.12E_READ_FIRST", e_read_first, "OK_TEXT" if e_read_first.exists() else "MISSING", read_first_value(e_read_first, "STATUS") if e_read_first.exists() else "MISSING", "SELL_TIMING_DAILY_READ_FIRST"),
        ("V18.12G_READ_FIRST", g_read_first, "OK_TEXT" if g_read_first.exists() else "MISSING", values["CLEANUP_AUDIT_STATUS"], "CLEANUP_AUDIT_READ_FIRST"),
    ]

    audit_rows = [
        audit_row(component, path, len(f_summary_rows) if component == "V18.12F_SUMMARY" else 0, parse_status, status_value, note)
        for component, path, parse_status, status_value, note in required_inputs
    ]

    missing_inputs = [row for row in audit_rows if row["exists"] != "YES" or row["parse_status"] in {"MISSING", "CSV_PARSE_FAILED"}]
    link_status = SELL_TIMING_LINK_STATUS_OK if not missing_inputs and values["V18_12F_STATUS"].startswith("OK_") else "WARN_LINK_WITH_MISSING_OR_NON_OK_INPUTS"
    status = STATUS_OK if link_status == SELL_TIMING_LINK_STATUS_OK else STATUS_WARN

    summary_rows: List[Dict[str, str]] = [
        metric_row("link_status", "SELL_TIMING_LINK_STATUS", link_status, "OK" if link_status.startswith("OK_") else "WARN", str(f_read_first)),
        metric_row("source_status", "V18_12F_STATUS", values["V18_12F_STATUS"], "OK" if values["V18_12F_STATUS"].startswith("OK_") else "WARN", str(f_read_first)),
        metric_row("source_status", "SHADOW_RESEARCH_STATUS", values["SHADOW_RESEARCH_STATUS"], "OK", str(f_read_first)),
        metric_row("source_status", "SELL_TIMING_STATUS", values["SELL_TIMING_STATUS"], "OK" if values["SELL_TIMING_STATUS"].startswith("OK_") else "WARN", str(f_read_first)),
        metric_row("source_status", "CLEANUP_AUDIT_STATUS", values["CLEANUP_AUDIT_STATUS"], "OK" if values["CLEANUP_AUDIT_STATUS"].startswith("OK_") else "WARN", str(g_read_first)),
    ]
    for key in [
        "POSITION_COUNT",
        "ACTIONABLE_EXIT_COUNT",
        "TECHNICAL_LABEL_SOURCE_COUNT",
        "LIFECYCLE_STAGE_COUNT",
        "TRACKER_ROWS",
        "FORWARD_COMPLETE_ROWS",
        "PENDING_FORWARD_ROWS",
    ]:
        summary_rows.append(metric_row("sell_timing_metrics", key, values[key], "OK", str(f_read_first)))
    summary_rows.extend(
        [
            metric_row("guardrails", "OFFICIAL_DECISION_IMPACT", OFFICIAL_DECISION_IMPACT, "OK", "V18.12H"),
            metric_row("guardrails", "AUTO_SELL", AUTO_SELL, "OK", "V18.12H"),
            metric_row("guardrails", "AUTO_TRADE", AUTO_TRADE, "OK", "V18.12H"),
        ]
    )

    report = [
        "# V18.12H Sell Timing Read Center Link",
        "",
        "## Status",
        "",
        f"- STATUS: {status}",
        f"- SELL_TIMING_LINK_STATUS: {link_status}",
        f"- MODE: {MODE}",
        f"- V18_12F_STATUS: {values['V18_12F_STATUS']}",
        f"- SHADOW_RESEARCH_STATUS: {values['SHADOW_RESEARCH_STATUS']}",
        f"- SELL_TIMING_STATUS: {values['SELL_TIMING_STATUS']}",
        f"- CLEANUP_AUDIT_STATUS: {values['CLEANUP_AUDIT_STATUS']}",
        "",
        "## Sell Timing Summary",
        "",
        f"- POSITION_COUNT: {values['POSITION_COUNT']}",
        f"- ACTIONABLE_EXIT_COUNT: {values['ACTIONABLE_EXIT_COUNT']}",
        f"- TECHNICAL_LABEL_SOURCE_COUNT: {values['TECHNICAL_LABEL_SOURCE_COUNT']}",
        f"- LIFECYCLE_STAGE_COUNT: {values['LIFECYCLE_STAGE_COUNT']}",
        f"- TRACKER_ROWS: {values['TRACKER_ROWS']}",
        f"- FORWARD_COMPLETE_ROWS: {values['FORWARD_COMPLETE_ROWS']}",
        f"- PENDING_FORWARD_ROWS: {values['PENDING_FORWARD_ROWS']}",
        "",
        "## Safety Guardrails",
        "",
        "- This is display/read-center linking only.",
        "- It does not modify official daily decision logic.",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "",
        "## Links",
        "",
        f"- V18.12F_READ_FIRST: {f_read_first}",
        f"- V18.12F_READ_CENTER: {f_read_center}",
        f"- V18.12E_READ_FIRST: {e_read_first}",
        f"- V18.12G_CLEANUP_AUDIT_READ_FIRST: {g_read_first}",
        "",
        "## Outputs",
        "",
        f"- SUMMARY_CSV: {summary_path}",
        f"- INPUT_AUDIT: {audit_path}",
    ]

    read_first = "\n".join(
        [
            "V18.12H SELL TIMING READ CENTER LINK READ FIRST",
            "",
            "STATUS:",
            status,
            "",
            "SELL_TIMING_LINK_STATUS:",
            link_status,
            "",
            "V18_12F_STATUS:",
            values["V18_12F_STATUS"],
            "",
            "POSITION_COUNT:",
            values["POSITION_COUNT"],
            "",
            "ACTIONABLE_EXIT_COUNT:",
            values["ACTIONABLE_EXIT_COUNT"],
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
            "READ_LINK:",
            str(read_link_path),
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
    write_text(read_link_path, "\n".join(report) + "\n")
    write_text(read_first_path, read_first)

    return {
        "STATUS": status,
        "SELL_TIMING_LINK_STATUS": link_status,
        "V18_12F_STATUS": values["V18_12F_STATUS"],
        "POSITION_COUNT": values["POSITION_COUNT"],
        "ACTIONABLE_EXIT_COUNT": values["ACTIONABLE_EXIT_COUNT"],
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_SELL": AUTO_SELL,
        "AUTO_TRADE": AUTO_TRADE,
        "READ_LINK": str(read_link_path),
        "SUMMARY_CSV": str(summary_path),
        "INPUT_AUDIT": str(audit_path),
        "READ_FIRST": str(read_first_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.12H sell timing read center link.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    result = build_outputs(Path(args.root))
    for key in [
        "STATUS",
        "SELL_TIMING_LINK_STATUS",
        "V18_12F_STATUS",
        "POSITION_COUNT",
        "ACTIONABLE_EXIT_COUNT",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_SELL",
        "AUTO_TRADE",
        "READ_LINK",
        "SUMMARY_CSV",
        "INPUT_AUDIT",
        "READ_FIRST",
    ]:
        print(f"{key}: {result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
