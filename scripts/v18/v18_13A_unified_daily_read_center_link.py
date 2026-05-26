from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
STATUS_OK = "OK_V18_13A_UNIFIED_DAILY_READ_CENTER_READY"
UNIFIED_STATUS_OK = "OK_LINKED_CURRENT_READ_FILES"
UNIFIED_STATUS_WARN = "WARN_LINKED_WITH_MISSING_INPUTS"
MODE = "READ_LINK_ONLY"
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

DISCOVERY_DIRS = [
    "outputs/v18/read_center",
    "outputs/v18/sell_timing",
    "outputs/v18/ops",
    "outputs/v18/daily_integrated",
    "outputs/v18/promotion_merge",
    "outputs/v18/factor_audit",
    "outputs/v18/factor_research",
    "outputs/v18/weight_research",
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


def discover_read_first_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for rel_dir in DISCOVERY_DIRS:
        path = root / rel_dir
        if not path.exists():
            continue
        for candidate in path.glob("*READ_FIRST*"):
            if candidate.is_file():
                files.append(candidate)
    return sorted(set(files), key=lambda p: str(p).lower())


def latest_stable_read_first(root: Path, name: str) -> Path:
    return root / f"outputs/v18/ops/{name}"


def first_existing_path(paths: List[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


def build_outputs(root: Path) -> Dict[str, str]:
    out_dir = root / "outputs/v18/read_center"
    read_center_path = out_dir / "V18_13A_CURRENT_UNIFIED_DAILY_READ_CENTER.md"
    read_first_path = out_dir / "V18_13A_READ_FIRST.txt"
    summary_path = out_dir / "V18_13A_CURRENT_UNIFIED_DAILY_SUMMARY.csv"
    audit_path = out_dir / "V18_13A_CURRENT_UNIFIED_DAILY_INPUT_AUDIT.csv"

    paths = {
        "official_current_read_first": root / "outputs/v18/read_center/V18_CURRENT_READ_FIRST.md",
        "official_9c_read_first": root / "outputs/v18/read_center/V18_9C_READ_FIRST.txt",
        "shadow_research_read_first": root / "outputs/v18/read_center/V18_CURRENT_SHADOW_RESEARCH_DAILY_READ_FIRST.txt",
        "v18_12h_read_first": root / "outputs/v18/read_center/V18_12H_READ_FIRST.txt",
        "v18_12h_read_link": root / "outputs/v18/read_center/V18_12H_CURRENT_SELL_TIMING_READ_LINK.md",
        "v18_12f_read_first": first_existing_path([
            root / "outputs/v18/sell_timing/V18_12F_READ_FIRST.txt",
            root / "outputs/v18/ops/V18_12F_R2_READ_FIRST.txt",
            root / "outputs/v18/ops/V18_12F_R1_READ_FIRST.txt",
        ]),
        "v18_12e_read_first": first_existing_path([
            root / "outputs/v18/sell_timing/V18_12E_READ_FIRST.txt",
            root / "outputs/v18/ops/V18_12E_R1_READ_FIRST.txt",
        ]),
        "v18_12g_read_first": root / "outputs/v18/ops/V18_12G_READ_FIRST.txt",
        "v18_12h_r1_read_first": latest_stable_read_first(root, "V18_12H_R1_READ_FIRST.txt"),
        "v18_12f_r2_read_first": latest_stable_read_first(root, "V18_12F_R2_READ_FIRST.txt"),
    }

    values = {
        "OFFICIAL_DAILY_STATUS": read_first_value(paths["official_9c_read_first"], "STATUS") or read_first_value(paths["official_current_read_first"], "STATUS") or "UNKNOWN",
        "SHADOW_RESEARCH_STATUS": read_first_value(paths["shadow_research_read_first"], "RESEARCH_STATUS") or read_first_value(paths["shadow_research_read_first"], "STATUS") or "UNKNOWN",
        "SELL_TIMING_LINK_STATUS": read_first_value(paths["v18_12h_read_first"], "SELL_TIMING_LINK_STATUS") or "MISSING",
        "SELL_TIMING_STATUS": read_first_value(paths["v18_12f_read_first"], "SELL_TIMING_STATUS") or "MISSING",
        "SELL_TIMING_READ_FIRST_STATUS": "OK_CURRENT_FALLBACK_READ_FIRST_FOUND" if paths["v18_12f_read_first"].exists() else "WARN_MISSING_OPTIONAL_SHADOW_READ_FIRST",
        "V18_12F_STATUS": read_first_value(paths["v18_12f_read_first"], "STATUS") or "MISSING",
        "POSITION_COUNT": value_or_zero(read_first_value(paths["v18_12f_read_first"], "POSITION_COUNT")),
        "ACTIONABLE_EXIT_COUNT": value_or_zero(read_first_value(paths["v18_12f_read_first"], "ACTIONABLE_EXIT_COUNT")),
        "TECHNICAL_LABEL_SOURCE_COUNT": value_or_zero(read_first_value(paths["v18_12f_read_first"], "TECHNICAL_LABEL_SOURCE_COUNT")),
        "LIFECYCLE_STAGE_COUNT": value_or_zero(read_first_value(paths["v18_12f_read_first"], "LIFECYCLE_STAGE_COUNT")),
        "TRACKER_ROWS": value_or_zero(read_first_value(paths["v18_12f_read_first"], "TRACKER_ROWS")),
        "CLEANUP_AUDIT_STATUS": read_first_value(paths["v18_12g_read_first"], "STATUS") or "MISSING",
        "V18_12F_R2_STATUS": read_first_value(paths["v18_12f_r2_read_first"], "STATUS") or "MISSING",
        "V18_12H_R1_STATUS": read_first_value(paths["v18_12h_r1_read_first"], "STATUS") or "MISSING",
    }

    discovered = discover_read_first_files(root)
    audit_rows: List[Dict[str, str]] = []
    for component, path in paths.items():
        status_value = read_first_value(path, "STATUS") if path.exists() else "MISSING"
        audit_rows.append(audit_row(component, path, 0, "OK_TEXT" if path.exists() else "MISSING", status_value, "IMPORTANT_INPUT"))
    for path in discovered:
        status_value = read_first_value(path, "STATUS") if path.exists() else ""
        audit_rows.append(audit_row("discovered_read_first", path, 0, "OK_TEXT", status_value, "DISCOVERED_READ_FIRST"))

    missing_important = [
        row for row in audit_rows
        if row["note"] == "IMPORTANT_INPUT" and row["exists"] != "YES" and row["component"] not in {"official_current_read_first", "official_9c_read_first"}
    ]
    unified_status = UNIFIED_STATUS_OK if not missing_important and values["SELL_TIMING_LINK_STATUS"].startswith("OK_") else UNIFIED_STATUS_WARN
    status = STATUS_OK if unified_status == UNIFIED_STATUS_OK else "WARN_V18_13A_UNIFIED_DAILY_READ_CENTER_WITH_MISSING_INPUTS"

    summary_rows: List[Dict[str, str]] = [
        metric_row("unified_status", "UNIFIED_READ_CENTER_STATUS", unified_status, "OK" if unified_status.startswith("OK_") else "WARN", "V18.13A"),
        metric_row("official", "OFFICIAL_DAILY_STATUS", values["OFFICIAL_DAILY_STATUS"], "OK" if values["OFFICIAL_DAILY_STATUS"].startswith("OK_") else "INFO", str(paths["official_9c_read_first"])),
        metric_row("shadow_research", "SHADOW_RESEARCH_STATUS", values["SHADOW_RESEARCH_STATUS"], "OK" if values["SHADOW_RESEARCH_STATUS"].startswith("OK_") else "INFO", str(paths["shadow_research_read_first"])),
        metric_row("sell_timing", "SELL_TIMING_LINK_STATUS", values["SELL_TIMING_LINK_STATUS"], "OK" if values["SELL_TIMING_LINK_STATUS"].startswith("OK_") else "WARN", str(paths["v18_12h_read_first"])),
        metric_row("sell_timing", "SELL_TIMING_STATUS", values["SELL_TIMING_STATUS"], "OK" if values["SELL_TIMING_STATUS"].startswith("OK_") else "WARN", str(paths["v18_12f_read_first"])),
        metric_row("sell_timing", "SELL_TIMING_READ_FIRST_STATUS", values["SELL_TIMING_READ_FIRST_STATUS"], "OK" if values["SELL_TIMING_READ_FIRST_STATUS"].startswith("OK_") else "WARN", str(paths["v18_12f_read_first"])),
        metric_row("cleanup", "CLEANUP_AUDIT_STATUS", values["CLEANUP_AUDIT_STATUS"], "OK" if values["CLEANUP_AUDIT_STATUS"].startswith("OK_") else "WARN", str(paths["v18_12g_read_first"])),
        metric_row("stable_baseline", "V18_12F_R2_STATUS", values["V18_12F_R2_STATUS"], "OK" if values["V18_12F_R2_STATUS"].startswith("OK_") else "WARN", str(paths["v18_12f_r2_read_first"])),
        metric_row("stable_baseline", "V18_12H_R1_STATUS", values["V18_12H_R1_STATUS"], "OK" if values["V18_12H_R1_STATUS"].startswith("OK_") else "WARN", str(paths["v18_12h_r1_read_first"])),
    ]
    for key in ["POSITION_COUNT", "ACTIONABLE_EXIT_COUNT", "TECHNICAL_LABEL_SOURCE_COUNT", "LIFECYCLE_STAGE_COUNT", "TRACKER_ROWS"]:
        summary_rows.append(metric_row("sell_timing_metrics", key, values[key], "OK", str(paths["v18_12f_read_first"])))
    summary_rows.extend(
        [
            metric_row("guardrails", "OFFICIAL_DECISION_IMPACT", OFFICIAL_DECISION_IMPACT, "OK", "V18.13A"),
            metric_row("guardrails", "AUTO_SELL", AUTO_SELL, "OK", "V18.13A"),
            metric_row("guardrails", "AUTO_TRADE", AUTO_TRADE, "OK", "V18.13A"),
        ]
    )

    report = [
        "# V18.13A Unified Daily Read Center",
        "",
        "## Status",
        "",
        f"- STATUS: {status}",
        f"- UNIFIED_READ_CENTER_STATUS: {unified_status}",
        f"- MODE: {MODE}",
        "",
        "## Daily Status",
        "",
        f"- OFFICIAL_DAILY_STATUS: {values['OFFICIAL_DAILY_STATUS']}",
        f"- SHADOW_RESEARCH_STATUS: {values['SHADOW_RESEARCH_STATUS']}",
        f"- SELL_TIMING_LINK_STATUS: {values['SELL_TIMING_LINK_STATUS']}",
        f"- SELL_TIMING_STATUS: {values['SELL_TIMING_STATUS']}",
        f"- SELL_TIMING_READ_FIRST_STATUS: {values['SELL_TIMING_READ_FIRST_STATUS']}",
        "",
        "## Sell Timing Metrics",
        "",
        f"- POSITION_COUNT: {values['POSITION_COUNT']}",
        f"- ACTIONABLE_EXIT_COUNT: {values['ACTIONABLE_EXIT_COUNT']}",
        f"- TECHNICAL_LABEL_SOURCE_COUNT: {values['TECHNICAL_LABEL_SOURCE_COUNT']}",
        f"- LIFECYCLE_STAGE_COUNT: {values['LIFECYCLE_STAGE_COUNT']}",
        f"- EXIT_SIGNAL_TRACKER_ROWS: {values['TRACKER_ROWS']}",
        "",
        "## Cleanup And Stable Baselines",
        "",
        f"- CLEANUP_AUDIT_STATUS: {values['CLEANUP_AUDIT_STATUS']}",
        f"- LATEST_PROTECTED_STABLE_BASELINE_V18_12F_R2: {values['V18_12F_R2_STATUS']}",
        f"- LATEST_PROTECTED_STABLE_BASELINE_V18_12H_R1: {values['V18_12H_R1_STATUS']}",
        "",
        "## Safety Guardrails",
        "",
        "- This is display/read-center linking only.",
        "- It does not modify official daily logic or sell timing logic.",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "",
        "## Links",
        "",
        f"- OFFICIAL_READ_FIRST: {paths['official_9c_read_first']}",
        f"- SHADOW_RESEARCH_READ_FIRST: {paths['shadow_research_read_first']}",
        f"- V18.12H_READ_FIRST: {paths['v18_12h_read_first']}",
        f"- V18.12H_READ_LINK: {paths['v18_12h_read_link']}",
        f"- V18.12F_READ_FIRST: {paths['v18_12f_read_first']}",
        f"- V18.12E_READ_FIRST: {paths['v18_12e_read_first']}",
        f"- V18.12G_CLEANUP_READ_FIRST: {paths['v18_12g_read_first']}",
        f"- V18.12F_R2_STABLE_READ_FIRST: {paths['v18_12f_r2_read_first']}",
        f"- V18.12H_R1_STABLE_READ_FIRST: {paths['v18_12h_r1_read_first']}",
        "",
        "## Outputs",
        "",
        f"- SUMMARY_CSV: {summary_path}",
        f"- INPUT_AUDIT: {audit_path}",
    ]

    read_first = "\n".join(
        [
            "V18.13A UNIFIED DAILY READ CENTER READ FIRST",
            "",
            "STATUS:",
            status,
            "",
            "UNIFIED_READ_CENTER_STATUS:",
            unified_status,
            "",
            "OFFICIAL_DAILY_STATUS:",
            values["OFFICIAL_DAILY_STATUS"],
            "",
            "SHADOW_RESEARCH_STATUS:",
            values["SHADOW_RESEARCH_STATUS"],
            "",
            "SELL_TIMING_LINK_STATUS:",
            values["SELL_TIMING_LINK_STATUS"],
            "",
            "SELL_TIMING_STATUS:",
            values["SELL_TIMING_STATUS"],
            "",
            "SELL_TIMING_READ_FIRST_STATUS:",
            values["SELL_TIMING_READ_FIRST_STATUS"],
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
        "UNIFIED_READ_CENTER_STATUS": unified_status,
        "OFFICIAL_DAILY_STATUS": values["OFFICIAL_DAILY_STATUS"],
        "SHADOW_RESEARCH_STATUS": values["SHADOW_RESEARCH_STATUS"],
        "SELL_TIMING_LINK_STATUS": values["SELL_TIMING_LINK_STATUS"],
        "SELL_TIMING_STATUS": values["SELL_TIMING_STATUS"],
        "SELL_TIMING_READ_FIRST_STATUS": values["SELL_TIMING_READ_FIRST_STATUS"],
        "POSITION_COUNT": values["POSITION_COUNT"],
        "ACTIONABLE_EXIT_COUNT": values["ACTIONABLE_EXIT_COUNT"],
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_SELL": AUTO_SELL,
        "AUTO_TRADE": AUTO_TRADE,
        "READ_CENTER": str(read_center_path),
        "SUMMARY_CSV": str(summary_path),
        "INPUT_AUDIT": str(audit_path),
        "READ_FIRST": str(read_first_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.13A unified daily read center link.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    result = build_outputs(Path(args.root))
    for key in [
        "STATUS",
        "UNIFIED_READ_CENTER_STATUS",
        "OFFICIAL_DAILY_STATUS",
        "SHADOW_RESEARCH_STATUS",
        "SELL_TIMING_LINK_STATUS",
        "SELL_TIMING_STATUS",
        "SELL_TIMING_READ_FIRST_STATUS",
        "POSITION_COUNT",
        "ACTIONABLE_EXIT_COUNT",
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
