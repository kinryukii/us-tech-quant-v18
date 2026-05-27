from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_SKIPPED = "OK_V18_14E_CURRENT_DAILY_WITH_FORWARD_TRACKER_SKIPPED_READY"
STATUS_READY = "OK_V18_14E_CURRENT_DAILY_WITH_FORWARD_TRACKER_READY"
STATUS_FAIL = "FAIL_V18_14E_FORWARD_TRACKER_INTEGRATION"

OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
READ_ONLY = "TRUE"
CURRENT_ENTRY_ONLY = "TRUE"
FORWARD_TRACKER_INTEGRATED = "TRUE"

DANGEROUS_TOKENS = (
    "SELL_NOW",
    "BUY_NOW_FORCE",
    "AUTO_EXECUTE",
    "LIVE_ORDER",
    "LIVE_SELL",
    "BROKER_ORDER",
)

SUMMARY_FIELDS = (
    "metric",
    "value",
)
AUDIT_FIELDS = (
    "component",
    "source_file",
    "alias_file",
    "exists",
    "copied",
    "row_count",
    "parse_status",
    "status_value",
    "note",
)


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


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def first_value(path: Path, key: str) -> str:
    target = f"{key}:"
    bullet_target = f"- {target}"
    lines = [line.strip() for line in read_text(path).splitlines()]
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


def copy_alias(src: Path, dst: Path) -> Tuple[bool, str, int, str]:
    if not src.exists() or not src.is_file():
        return False, "MISSING_SOURCE", 0, "MISSING"
    try:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        rows = 0
        parse_status = "OK_TEXT"
        if dst.suffix.lower() == ".csv":
            csv_rows, _, parse_status = read_csv(dst)
            rows = len(csv_rows)
        return True, "COPIED", rows, parse_status
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}", 0, "COPY_FAIL"


def scan_tokens(root: Path, paths: Iterable[Path]) -> List[str]:
    hits: List[str] = []
    for path in paths:
        text = read_text(path)
        for token in DANGEROUS_TOKENS:
            if token in text:
                hits.append(f"{rel(root, path)}::{token}")
    return hits


def markdown_table(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> List[str]:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |")
    return out


def build(root: Path, mode: str, forward_tracker_run: str) -> Tuple[Dict[str, str], int]:
    ops = root / "outputs/v18/ops"
    candidates = root / "outputs/v18/candidates"
    state_tracker = root / "state/v18/candidate_forward_tracker/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv"

    b_read = ops / "V18_14B_READ_FIRST.txt"
    c_read = ops / "V18_14C_READ_FIRST.txt"
    d_read = ops / "V18_14D_READ_FIRST.txt"

    out_read = ops / "V18_14E_READ_FIRST.txt"
    report_path = ops / "V18_14E_CURRENT_DAILY_WITH_FORWARD_TRACKER_REPORT.md"
    summary_path = ops / "V18_14E_CURRENT_DAILY_WITH_FORWARD_TRACKER_SUMMARY.csv"
    audit_path = ops / "V18_14E_CURRENT_DAILY_WITH_FORWARD_TRACKER_INPUT_AUDIT.csv"

    aliases = [
        ("V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER", state_tracker, candidates / "V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv"),
        ("V18_CURRENT_FORWARD_TRACKER_READ_FIRST", c_read, ops / "V18_CURRENT_FORWARD_TRACKER_READ_FIRST.txt"),
        ("V18_CURRENT_FORWARD_PRICE_FILLER_READ_FIRST", d_read, ops / "V18_CURRENT_FORWARD_PRICE_FILLER_READ_FIRST.txt"),
    ]

    audit_rows: List[Dict[str, str]] = []
    copy_failures: List[str] = []
    for component, src, dst in aliases:
        copied, note, rows, parse_status = copy_alias(src, dst)
        if forward_tracker_run == "RAN" and not copied:
            copy_failures.append(component)
        audit_rows.append(
            {
                "component": component,
                "source_file": str(src),
                "alias_file": str(dst),
                "exists": "YES" if src.exists() else "NO",
                "copied": "YES" if copied else "NO",
                "row_count": str(rows),
                "parse_status": parse_status,
                "status_value": note,
                "note": "CURRENT_FORWARD_ALIAS",
            }
        )

    tracker_rows, _, tracker_parse = read_csv(state_tracker)

    b_status = first_value(b_read, "STATUS") or "UNKNOWN"
    c_status = first_value(c_read, "STATUS") or "UNKNOWN"
    d_status = first_value(d_read, "STATUS") or "UNKNOWN"
    run_mode = first_value(b_read, "RUN_MODE") or mode
    full_daily_mode_status = first_value(b_read, "FULL_DAILY_MODE_STATUS") or "UNKNOWN"
    official_daily_status = first_value(b_read, "OFFICIAL_DAILY_STATUS") or "UNKNOWN"
    tracker_rows_count = first_value(d_read, "TRACKER_ROWS") or first_value(c_read, "TRACKER_ROWS") or str(len(tracker_rows))
    new_signal_rows = first_value(c_read, "NEW_SIGNAL_ROWS_ADDED") or "0"
    updated_forward_rows = first_value(d_read, "UPDATED_FORWARD_ROWS") or "0"
    forward_complete_rows = first_value(d_read, "FORWARD_COMPLETE_ROWS") or first_value(c_read, "FORWARD_COMPLETE_ROWS") or "0"
    partial_forward_rows = first_value(d_read, "PARTIAL_FORWARD_FILLED_ROWS") or "0"
    pending_forward_rows = first_value(d_read, "PENDING_FORWARD_ROWS") or first_value(c_read, "PENDING_FORWARD_ROWS") or "0"
    pending_signal_price_rows = first_value(d_read, "PENDING_SIGNAL_PRICE_ROWS") or "0"
    price_source_count = first_value(d_read, "PRICE_SOURCE_COUNT") or "0"
    price_source_status = first_value(d_read, "PRICE_SOURCE_STATUS") or "NOT_RUN"
    top_5 = first_value(d_read, "TOP_5_TICKERS") or first_value(c_read, "TOP_5_TICKERS") or first_value(b_read, "TOP_5_TICKERS")

    failures: List[str] = []
    if not b_read.exists() or not b_status.startswith("OK_V18_14B_"):
        failures.append("V18_14B_CURRENT_OUTPUT_MISSING_OR_NOT_OK")
    if forward_tracker_run == "RAN":
        if not c_read.exists() or c_status != "OK_V18_14C_RANKED_CANDIDATE_FORWARD_TRACKER_READY":
            failures.append("V18_14C_FORWARD_TRACKER_MISSING_OR_NOT_OK")
        if not d_read.exists() or d_status != "OK_V18_14D_RANKED_CANDIDATE_FORWARD_PRICE_FILLER_READY":
            failures.append("V18_14D_FORWARD_PRICE_FILLER_MISSING_OR_NOT_OK")
        if tracker_parse != "OK" or not tracker_rows:
            failures.append("TRACKER_CSV_MISSING_OR_UNREADABLE")
        if copy_failures:
            failures.append("FORWARD_ALIAS_COPY_FAILED")
    if AUTO_TRADE != "DISABLED":
        failures.append("AUTO_TRADE_NOT_DISABLED")
    if AUTO_SELL != "DISABLED":
        failures.append("AUTO_SELL_NOT_DISABLED")
    if OFFICIAL_DECISION_IMPACT != "NONE":
        failures.append("OFFICIAL_DECISION_IMPACT_NOT_NONE")

    scan_paths = [
        out_read,
        report_path,
        summary_path,
        audit_path,
        candidates / "V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv",
        ops / "V18_CURRENT_FORWARD_TRACKER_READ_FIRST.txt",
        ops / "V18_CURRENT_FORWARD_PRICE_FILLER_READ_FIRST.txt",
    ]
    pre_hits = scan_tokens(root, scan_paths[4:])
    if pre_hits:
        failures.append("DANGEROUS_TOKEN_DETECTED")

    if failures:
        status = STATUS_FAIL
    elif forward_tracker_run == "RAN":
        status = STATUS_READY
    else:
        status = STATUS_SKIPPED

    values = {
        "STATUS": status,
        "RUN_MODE": run_mode,
        "FORWARD_TRACKER_RUN": forward_tracker_run,
        "V18_14B_STATUS": b_status,
        "V18_14C_STATUS": c_status if forward_tracker_run == "RAN" else "SKIPPED",
        "V18_14D_STATUS": d_status if forward_tracker_run == "RAN" else "SKIPPED",
        "FULL_DAILY_MODE_STATUS": full_daily_mode_status,
        "OFFICIAL_DAILY_STATUS": official_daily_status,
        "TRACKER_ROWS": tracker_rows_count,
        "NEW_SIGNAL_ROWS_ADDED": new_signal_rows,
        "UPDATED_FORWARD_ROWS": updated_forward_rows,
        "FORWARD_COMPLETE_ROWS": forward_complete_rows,
        "PARTIAL_FORWARD_FILLED_ROWS": partial_forward_rows,
        "PENDING_FORWARD_ROWS": pending_forward_rows,
        "PENDING_SIGNAL_PRICE_ROWS": pending_signal_price_rows,
        "PRICE_SOURCE_COUNT": price_source_count,
        "PRICE_SOURCE_STATUS": price_source_status,
        "TOP_5_TICKERS": top_5,
        "VALIDATION_FAIL_COUNT": str(len(failures)),
        "FAIL_REASONS": ";".join(failures) if failures else "NONE",
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "READ_ONLY": READ_ONLY,
        "CURRENT_ENTRY_ONLY": CURRENT_ENTRY_ONLY,
        "FORWARD_TRACKER_INTEGRATED": FORWARD_TRACKER_INTEGRATED,
        "DANGEROUS_TOKEN_DETECTED": "YES" if pre_hits else "NO",
    }

    read_keys = (
        "STATUS",
        "RUN_MODE",
        "FORWARD_TRACKER_RUN",
        "V18_14B_STATUS",
        "V18_14C_STATUS",
        "V18_14D_STATUS",
        "FULL_DAILY_MODE_STATUS",
        "OFFICIAL_DAILY_STATUS",
        "TRACKER_ROWS",
        "NEW_SIGNAL_ROWS_ADDED",
        "UPDATED_FORWARD_ROWS",
        "FORWARD_COMPLETE_ROWS",
        "PARTIAL_FORWARD_FILLED_ROWS",
        "PENDING_FORWARD_ROWS",
        "PENDING_SIGNAL_PRICE_ROWS",
        "PRICE_SOURCE_COUNT",
        "PRICE_SOURCE_STATUS",
        "TOP_5_TICKERS",
        "VALIDATION_FAIL_COUNT",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "READ_ONLY",
        "CURRENT_ENTRY_ONLY",
        "FORWARD_TRACKER_INTEGRATED",
    )
    write_text(out_read, "\n".join(f"{key}: {values[key]}" for key in read_keys) + f"\nFAIL_REASONS: {values['FAIL_REASONS']}\nDANGEROUS_TOKEN_DETECTED: {values['DANGEROUS_TOKEN_DETECTED']}\n")
    write_csv(summary_path, [{"metric": key, "value": value} for key, value in values.items()], SUMMARY_FIELDS)
    write_csv(audit_path, audit_rows, AUDIT_FIELDS)

    report = [
        "# V18.14E Current Daily With Forward Tracker",
        "",
        "Current daily command-center integration summary. Forward tracking is research-only.",
        "",
        "## Status",
        "",
    ]
    report.extend(f"- {key}: {values[key]}" for key in read_keys)
    report.extend([
        f"- FAIL_REASONS: {values['FAIL_REASONS']}",
        f"- DANGEROUS_TOKEN_DETECTED: {values['DANGEROUS_TOKEN_DETECTED']}",
        "",
        "## Alias Outputs",
        "",
    ])
    report.extend(markdown_table(audit_rows, AUDIT_FIELDS))
    write_text(report_path, "\n".join(report) + "\n")

    post_hits = scan_tokens(root, scan_paths)
    if post_hits and not pre_hits:
        values["STATUS"] = STATUS_FAIL
        values["VALIDATION_FAIL_COUNT"] = "1"
        values["DANGEROUS_TOKEN_DETECTED"] = "YES"
        write_text(out_read, "\n".join(f"{key}: {values[key]}" for key in read_keys) + "\nFAIL_REASONS: DANGEROUS_TOKEN_DETECTED\nDANGEROUS_TOKEN_DETECTED: YES\n")
        write_csv(summary_path, [{"metric": key, "value": value} for key, value in values.items()], SUMMARY_FIELDS)

    for key in read_keys:
        print(f"{key}: {values[key]}")
    print(f"FAIL_REASONS: {values['FAIL_REASONS']}")
    print(f"DANGEROUS_TOKEN_DETECTED: {values['DANGEROUS_TOKEN_DETECTED']}")
    return values, 0 if values["STATUS"] != STATUS_FAIL else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.14E current daily command center with optional forward tracker integration.")
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--mode", choices=["READ_CENTER_REFRESH_ONLY", "FULL_DAILY", "VALIDATE_ONLY"], default="READ_CENTER_REFRESH_ONLY")
    parser.add_argument("--forward-tracker-run", choices=["SKIPPED", "RAN"], default="SKIPPED")
    args = parser.parse_args()
    _, code = build(Path(args.root), args.mode, args.forward_tracker_run)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
