from __future__ import annotations

"""V18.12E Sell Timing Daily Read Center.

Summarizes the shadow-only V18.12 sell timing chain after the daily wrapper
runs V18.12A, V18.12B, V18.12C, and V18.12D. This script only reads current
sell_timing artifacts and writes V18.12E summary/read-center outputs.
"""

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
STATUS_OK = "OK_V18_12E_SELL_TIMING_DAILY_WRAPPER_READY"
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

READ_FIRST_PATHS = {
    "V18.12A": "outputs/v18/sell_timing/V18_12A_READ_FIRST.txt",
    "V18.12B": "outputs/v18/sell_timing/V18_12B_READ_FIRST.txt",
    "V18.12C": "outputs/v18/sell_timing/V18_12C_READ_FIRST.txt",
    "V18.12D": "outputs/v18/sell_timing/V18_12D_READ_FIRST.txt",
}

CSV_PATHS = {
    "V18.12C_LIFECYCLE": "outputs/v18/sell_timing/V18_12C_CURRENT_POSITION_LIFECYCLE_REVIEW.csv",
    "V18.12D_VALIDATION": "outputs/v18/sell_timing/V18_12D_CURRENT_EXIT_SIGNAL_FORWARD_VALIDATION.csv",
}


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


def build_outputs(root: Path) -> Dict[str, str]:
    out_dir = root / "outputs/v18/sell_timing"
    read_center_path = out_dir / "V18_12E_CURRENT_SELL_TIMING_DAILY_READ_CENTER.md"
    read_first_path = out_dir / "V18_12E_READ_FIRST.txt"
    summary_path = out_dir / "V18_12E_CURRENT_SELL_TIMING_DAILY_SUMMARY.csv"
    audit_path = out_dir / "V18_12E_CURRENT_SELL_TIMING_DAILY_INPUT_AUDIT.csv"

    audit_rows: List[Dict[str, str]] = []
    summary_rows: List[Dict[str, str]] = []

    statuses: Dict[str, str] = {}
    values: Dict[str, str] = {
        "POSITION_COUNT": "0",
        "ACTIONABLE_EXIT_COUNT": "0",
        "TECHNICAL_LABEL_SOURCE_COUNT": "0",
        "LIFECYCLE_STAGE_COUNT": "0",
        "TRACKER_ROWS": "0",
        "FORWARD_COMPLETE_ROWS": "0",
        "PENDING_FORWARD_ROWS": "0",
    }

    for component, rel_path in READ_FIRST_PATHS.items():
        path = root / rel_path
        status_value = read_first_value(path, "STATUS") if path.exists() else "MISSING"
        statuses[component] = status_value
        audit_rows.append(audit_row(component, path, 0, "OK_TEXT" if path.exists() else "MISSING", status_value, "READ_FIRST"))
        summary_rows.append(metric_row("component_status", f"{component}_STATUS", status_value, "OK" if status_value and status_value != "MISSING" else "MISSING", str(path)))

    # Prefer later chain layers for shared counters.
    for key in ["POSITION_COUNT", "ACTIONABLE_EXIT_COUNT"]:
        for component in ["V18.12C", "V18.12B", "V18.12A"]:
            path = root / READ_FIRST_PATHS[component]
            val = read_first_value(path, key)
            if val != "":
                values[key] = val
                break
    values["TECHNICAL_LABEL_SOURCE_COUNT"] = read_first_value(root / READ_FIRST_PATHS["V18.12B"], "TECHNICAL_LABEL_SOURCE_COUNT") or "0"
    values["LIFECYCLE_STAGE_COUNT"] = read_first_value(root / READ_FIRST_PATHS["V18.12C"], "LIFECYCLE_STAGE_COUNT") or "0"
    for key in ["TRACKER_ROWS", "FORWARD_COMPLETE_ROWS", "PENDING_FORWARD_ROWS"]:
        values[key] = read_first_value(root / READ_FIRST_PATHS["V18.12D"], key) or "0"

    lifecycle_rows, _, lifecycle_status = read_csv(root / CSV_PATHS["V18.12C_LIFECYCLE"])
    audit_rows.append(audit_row("V18.12C_LIFECYCLE", root / CSV_PATHS["V18.12C_LIFECYCLE"], len(lifecycle_rows), lifecycle_status, statuses.get("V18.12C", ""), "LIFECYCLE_CSV"))

    validation_rows, _, validation_status = read_csv(root / CSV_PATHS["V18.12D_VALIDATION"])
    audit_rows.append(audit_row("V18.12D_VALIDATION", root / CSV_PATHS["V18.12D_VALIDATION"], len(validation_rows), validation_status, statuses.get("V18.12D", ""), "FORWARD_VALIDATION_CSV"))
    label_counts = Counter(row.get("validation_label", "UNKNOWN") for row in validation_rows)

    for key, value in values.items():
        summary_rows.append(metric_row("daily_summary", key, value, "OK", "V18.12E"))
    for label in ["EXIT_SIGNAL_HELPED", "EXIT_SIGNAL_HURT", "EXIT_SIGNAL_NEUTRAL", "INSUFFICIENT_DATA", "NO_ACTIONABLE_EXIT"]:
        summary_rows.append(metric_row("validation_label_counts", label, str(label_counts.get(label, 0)), "OK", str(root / CSV_PATHS["V18.12D_VALIDATION"])))
    summary_rows.extend(
        [
            metric_row("guardrails", "OFFICIAL_DECISION_IMPACT", OFFICIAL_DECISION_IMPACT, "OK", "V18.12E"),
            metric_row("guardrails", "AUTO_SELL", AUTO_SELL, "OK", "V18.12E"),
            metric_row("guardrails", "AUTO_TRADE", AUTO_TRADE, "OK", "V18.12E"),
        ]
    )

    all_ok = all(statuses.get(c, "").startswith("OK_") for c in READ_FIRST_PATHS)
    status = "OK_V18_12E_SELL_TIMING_DAILY_WRAPPER_READY" if all_ok else "WARN_V18_12E_SELL_TIMING_DAILY_WRAPPER_WITH_MISSING_COMPONENT"

    report = [
        "# V18.12E Sell Timing Daily Read Center",
        "",
        "## Status",
        "",
        f"- STATUS: {status}",
        f"- MODE: {MODE}",
        f"- V18.12A_STATUS: {statuses.get('V18.12A', '')}",
        f"- V18.12B_STATUS: {statuses.get('V18.12B', '')}",
        f"- V18.12C_STATUS: {statuses.get('V18.12C', '')}",
        f"- V18.12D_STATUS: {statuses.get('V18.12D', '')}",
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
        "## Safety Guardrails",
        "",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "- This is a shadow-only sell timing review center, not a sell order.",
        "- It does not affect official decisions, official daily scripts, trading logic, or factor weights.",
        "",
        "## Validation Label Counts",
        "",
    ]
    for label in ["EXIT_SIGNAL_HELPED", "EXIT_SIGNAL_HURT", "EXIT_SIGNAL_NEUTRAL", "INSUFFICIENT_DATA", "NO_ACTIONABLE_EXIT"]:
        report.append(f"- {label}: {label_counts.get(label, 0)}")
    report.extend(
        [
            "",
            "## Inputs",
            "",
            f"- SUMMARY_CSV: {summary_path}",
            f"- INPUT_AUDIT: {audit_path}",
            "",
            "## Note",
            "",
            "- V18.12E only coordinates and summarizes V18.12 shadow sell timing review outputs.",
            "- Immediate live order vocabulary is intentionally excluded from generated outputs.",
        ]
    )

    read_first = "\n".join(
        [
            "V18.12E SELL TIMING DAILY WRAPPER READ FIRST",
            "",
            "STATUS:",
            status,
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
    parser = argparse.ArgumentParser(description="V18.12E sell timing read center.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    result = build_outputs(Path(args.root))
    for key in [
        "STATUS",
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
