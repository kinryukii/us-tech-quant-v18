from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
STATUS_OK = "OK_V18_12G_SELL_TIMING_CLEANUP_AUDIT_READY"
MODE = "DRYRUN_ONLY"
DELETE_EXECUTED = "FALSE"
VALIDATION_FAIL_COUNT = "0"
OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_SELL = "DISABLED"
AUTO_TRADE = "DISABLED"

FIELDS = [
    "audit_time",
    "category",
    "version_key",
    "path",
    "exists",
    "size_mb",
    "last_write_time",
    "action",
    "reason",
    "safe_to_delete",
    "delete_command_preview",
]

VERSION_KEYS = [
    "V18_12A_R1",
    "V18_12B_R1",
    "V18_12C_R1",
    "V18_12D_R1",
    "V18_12E_R1",
    "V18_12F_R1",
    "V18_12F_R2",
]

REQUIRED_SELL_TIMING_OUTPUTS = {
    "V18_12A_READ_FIRST.txt",
    "V18_12B_READ_FIRST.txt",
    "V18_12C_READ_FIRST.txt",
    "V18_12D_READ_FIRST.txt",
    "V18_12E_READ_FIRST.txt",
    "V18_12F_READ_FIRST.txt",
    "V18_CURRENT_EXIT_SIGNAL_FORWARD_TRACKER.csv",
}

ALLOWED_ACTIONS = {
    "KEEP_LATEST",
    "KEEP_REQUIRED_CURRENT_OUTPUT",
    "KEEP_PROTECTED_STABLE",
    "DELETE_CANDIDATE_DUPLICATE_OLDER_SNAPSHOT",
    "DELETE_CANDIDATE_TEMP_LOG",
    "REVIEW_MANUALLY",
    "IGNORE",
}


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def size_bytes(path: Path) -> int:
    try:
        if path.is_file():
            return path.stat().st_size
        if path.is_dir():
            return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
    except OSError:
        return 0
    return 0


def size_mb(path: Path) -> str:
    return f"{size_bytes(path) / 1048576:.6f}"


def mtime_text(path: Path) -> str:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    except OSError:
        return ""


def delete_preview(path: Path) -> str:
    if path.is_dir():
        return f'Remove-Item -LiteralPath "{path}" -Recurse -Force'
    return f'Remove-Item -LiteralPath "{path}" -Force'


def row(
    audit_time: str,
    category: str,
    version_key: str,
    path: Path,
    action: str,
    reason: str,
    safe_to_delete: str,
    include_preview: bool = False,
) -> Dict[str, str]:
    if action not in ALLOWED_ACTIONS:
        action = "REVIEW_MANUALLY"
    return {
        "audit_time": audit_time,
        "category": category,
        "version_key": version_key,
        "path": str(path),
        "exists": "YES" if path.exists() else "NO",
        "size_mb": size_mb(path),
        "last_write_time": mtime_text(path),
        "action": action,
        "reason": reason,
        "safe_to_delete": safe_to_delete,
        "delete_command_preview": delete_preview(path) if include_preview else "",
    }


def timestamp_from_name(name: str) -> str:
    match = re.search(r"_(20\d{6}_\d{6})$", name)
    return match.group(1) if match else ""


def version_key_from_snapshot(name: str) -> str:
    for key in VERSION_KEYS:
        if name.startswith(f"{key}_stable_"):
            return key
    return ""


def scan_stable_snapshots(root: Path, audit_time: str) -> List[Dict[str, str]]:
    stable_dir = root / "archive/stable"
    rows: List[Dict[str, str]] = []
    if not stable_dir.exists():
        return rows

    grouped: Dict[str, List[Path]] = {key: [] for key in VERSION_KEYS}
    for path in stable_dir.iterdir():
        if not path.is_dir():
            continue
        key = version_key_from_snapshot(path.name)
        if key:
            grouped[key].append(path)

    for key, paths in grouped.items():
        paths.sort(key=lambda p: (timestamp_from_name(p.name), p.stat().st_mtime), reverse=True)
        for idx, path in enumerate(paths):
            if idx == 0:
                action = "KEEP_LATEST"
                safe = "NO"
                reason = "Newest timestamp stable snapshot for this version key."
                rows.append(row(audit_time, "stable_snapshot", key, path, action, reason, safe))
            else:
                action = "DELETE_CANDIDATE_DUPLICATE_OLDER_SNAPSHOT"
                safe = "YES"
                reason = "Older duplicate stable snapshot superseded by the newest snapshot for this version key."
                rows.append(row(audit_time, "stable_snapshot", key, path, action, reason, safe, include_preview=True))
    return rows


def scan_ops(root: Path, audit_time: str) -> List[Dict[str, str]]:
    ops_dir = root / "outputs/v18/ops"
    rows: List[Dict[str, str]] = []
    if not ops_dir.exists():
        return rows

    for path in sorted(ops_dir.iterdir(), key=lambda p: p.name):
        if not path.is_file():
            continue
        name = path.name
        if re.match(r"V18_12[A-Z]?_?R\d+_CURRENT_STABLE_SNAPSHOT_REPORT\.md$", name) or re.match(r"V18_12[A-Z]?_?R\d+_READ_FIRST\.txt$", name):
            match = re.match(r"(V18_12[A-Z]_R\d+)", name)
            key = match.group(1) if match else ""
            rows.append(
                row(
                    audit_time,
                    "ops_stable_snapshot_current_output",
                    key,
                    path,
                    "KEEP_REQUIRED_CURRENT_OUTPUT",
                    "Current stable snapshot report/read-first output retained for traceability.",
                    "NO",
                )
            )
            continue

        if re.match(r"V18_7[BD]_STEP_.*_20\d{6}_\d{6}\.log$", name):
            rows.append(
                row(
                    audit_time,
                    "ops_temp_log",
                    "",
                    path,
                    "DELETE_CANDIDATE_TEMP_LOG",
                    "Repeated V18.7B/V18.7D timestamped step log from heavy/interrupted V18.12F attempts.",
                    "YES",
                    include_preview=True,
                )
            )
            continue

        if name in {
            "V18_7B_CURRENT_MAIN_CHAIN_LINEAR_PROFILE.csv",
            "V18_7B_CURRENT_MAIN_CHAIN_LINEAR_REPORT.md",
            "V18_7B_READ_FIRST.txt",
            "V18_7D_CURRENT_OFFICIAL_DAILY_FAST_MAIN_WITH_TECHNICAL_PROFILE.csv",
            "V18_7D_CURRENT_OFFICIAL_DAILY_FAST_MAIN_WITH_TECHNICAL_REPORT.md",
            "V18_7D_READ_FIRST.txt",
        }:
            rows.append(
                row(
                    audit_time,
                    "ops_required_current_output",
                    "",
                    path,
                    "KEEP_REQUIRED_CURRENT_OUTPUT",
                    "Latest current output/read-first is not a cleanup candidate.",
                    "NO",
                )
            )
            continue
    return rows


def scan_sell_timing_outputs(root: Path, audit_time: str) -> List[Dict[str, str]]:
    out_dir = root / "outputs/v18/sell_timing"
    rows: List[Dict[str, str]] = []
    if not out_dir.exists():
        return rows

    for path in sorted(out_dir.iterdir(), key=lambda p: p.name):
        if not path.is_file():
            continue
        name = path.name
        if name in REQUIRED_SELL_TIMING_OUTPUTS or name.startswith("V18_12F_CURRENT_"):
            rows.append(
                row(
                    audit_time,
                    "sell_timing_required_current_output",
                    "",
                    path,
                    "KEEP_REQUIRED_CURRENT_OUTPUT",
                    "Required current V18.12 sell timing output explicitly preserved.",
                    "NO",
                )
            )
        elif name.startswith("V18_12") or name.startswith("V18_CURRENT_EXIT_SIGNAL"):
            rows.append(
                row(
                    audit_time,
                    "sell_timing_generated_output",
                    "",
                    path,
                    "REVIEW_MANUALLY",
                    "Generated sell timing output not in required-current preserve list; review manually before any cleanup.",
                    "NO",
                )
            )
    return rows


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def table_rows(rows: Iterable[Dict[str, str]], limit: int = 80) -> List[str]:
    out = ["| action | category | version_key | size_mb | path |", "|---|---|---|---:|---|"]
    count = 0
    for item in rows:
        count += 1
        if count > limit:
            out.append(f"| ... | ... | ... | ... | {count - limit} more rows omitted |")
            break
        path_text = item["path"].replace("|", "/")
        out.append(f"| {item['action']} | {item['category']} | {item['version_key']} | {item['size_mb']} | `{path_text}` |")
    if count == 0:
        out.append("| none |  |  | 0 |  |")
    return out


def summarize(rows: List[Dict[str, str]]) -> Dict[str, str]:
    delete_rows = [r for r in rows if r["action"].startswith("DELETE_CANDIDATE")]
    protected_rows = [r for r in rows if r["action"].startswith("KEEP_")]
    manual_rows = [r for r in rows if r["action"] == "REVIEW_MANUALLY"]
    delete_mb = sum(float(r["size_mb"] or "0") for r in delete_rows)
    return {
        "TOTAL_ITEMS_SCANNED": str(len(rows)),
        "DELETE_CANDIDATE_COUNT": str(len(delete_rows)),
        "DELETE_CANDIDATE_MB": f"{delete_mb:.6f}",
        "PROTECTED_KEEP_COUNT": str(len(protected_rows)),
        "MANUAL_REVIEW_COUNT": str(len(manual_rows)),
    }


def write_report(path: Path, rows: List[Dict[str, str]], summary: Dict[str, str], csv_path: Path, read_first_path: Path) -> None:
    delete_rows = [r for r in rows if r["action"].startswith("DELETE_CANDIDATE")]
    keep_rows = [r for r in rows if r["action"].startswith("KEEP_")]
    manual_rows = [r for r in rows if r["action"] == "REVIEW_MANUALLY"]
    lines = [
        "# V18.12G Sell Timing Cleanup Audit",
        "",
        f"Generated: `{now_text()}`",
        "",
        "## Status",
        "",
        f"- STATUS: `{STATUS_OK}`",
        f"- MODE: `{MODE}`",
        f"- DELETE_EXECUTED: `{DELETE_EXECUTED}`",
        f"- VALIDATION_FAIL_COUNT: `{VALIDATION_FAIL_COUNT}`",
        f"- OFFICIAL_DECISION_IMPACT: `{OFFICIAL_DECISION_IMPACT}`",
        f"- AUTO_SELL: `{AUTO_SELL}`",
        f"- AUTO_TRADE: `{AUTO_TRADE}`",
        "",
        "## Summary",
        "",
        f"- TOTAL_ITEMS_SCANNED: `{summary['TOTAL_ITEMS_SCANNED']}`",
        f"- DELETE_CANDIDATE_COUNT: `{summary['DELETE_CANDIDATE_COUNT']}`",
        f"- DELETE_CANDIDATE_MB: `{summary['DELETE_CANDIDATE_MB']}`",
        f"- PROTECTED_KEEP_COUNT: `{summary['PROTECTED_KEEP_COUNT']}`",
        f"- MANUAL_REVIEW_COUNT: `{summary['MANUAL_REVIEW_COUNT']}`",
        "",
        "## Delete Candidates",
        "",
        *table_rows(delete_rows, 120),
        "",
        "## Protected Keeps",
        "",
        *table_rows(keep_rows, 80),
        "",
        "## Manual Review",
        "",
        *table_rows(manual_rows, 80),
        "",
        "## Outputs",
        "",
        f"- CSV: `{csv_path}`",
        f"- READ_FIRST: `{read_first_path}`",
        "",
        "## Guardrail",
        "",
        "This is cleanup audit only. It does not delete, move, rename, or modify stable snapshots.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_read_first(path: Path, summary: Dict[str, str], report_path: Path, csv_path: Path) -> None:
    text = f"""V18.12G SELL TIMING CLEANUP AUDIT READ FIRST

STATUS:
{STATUS_OK}

MODE:
{MODE}

TOTAL_ITEMS_SCANNED:
{summary['TOTAL_ITEMS_SCANNED']}

DELETE_CANDIDATE_COUNT:
{summary['DELETE_CANDIDATE_COUNT']}

DELETE_CANDIDATE_MB:
{summary['DELETE_CANDIDATE_MB']}

PROTECTED_KEEP_COUNT:
{summary['PROTECTED_KEEP_COUNT']}

MANUAL_REVIEW_COUNT:
{summary['MANUAL_REVIEW_COUNT']}

OFFICIAL_DECISION_IMPACT:
{OFFICIAL_DECISION_IMPACT}

AUTO_SELL:
{AUTO_SELL}

AUTO_TRADE:
{AUTO_TRADE}

DELETE_EXECUTED:
{DELETE_EXECUTED}

VALIDATION_FAIL_COUNT:
{VALIDATION_FAIL_COUNT}

REPORT:
{report_path}

CSV:
{csv_path}
"""
    path.write_text(text, encoding="utf-8")


def build_outputs(root: Path) -> Dict[str, str]:
    audit_time = now_text()
    out_dir = root / "outputs/v18/ops"
    csv_path = out_dir / "V18_12G_CURRENT_SELL_TIMING_CLEANUP_AUDIT.csv"
    report_path = out_dir / "V18_12G_CURRENT_SELL_TIMING_CLEANUP_AUDIT_REPORT.md"
    read_first_path = out_dir / "V18_12G_READ_FIRST.txt"

    rows: List[Dict[str, str]] = []
    rows.extend(scan_stable_snapshots(root, audit_time))
    rows.extend(scan_ops(root, audit_time))
    rows.extend(scan_sell_timing_outputs(root, audit_time))
    rows.sort(key=lambda r: (r["category"], r["version_key"], r["action"], r["path"].lower()))

    summary = summarize(rows)
    write_csv(csv_path, rows)
    write_report(report_path, rows, summary, csv_path, read_first_path)
    write_read_first(read_first_path, summary, report_path, csv_path)

    return {
        "STATUS": STATUS_OK,
        "MODE": MODE,
        "DELETE_EXECUTED": DELETE_EXECUTED,
        "VALIDATION_FAIL_COUNT": VALIDATION_FAIL_COUNT,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_SELL": AUTO_SELL,
        "AUTO_TRADE": AUTO_TRADE,
        **summary,
        "REPORT": str(report_path),
        "CSV": str(csv_path),
        "READ_FIRST": str(read_first_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.12G sell timing cleanup audit.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    result = build_outputs(Path(args.root))
    for key in [
        "STATUS",
        "MODE",
        "DELETE_EXECUTED",
        "VALIDATION_FAIL_COUNT",
        "TOTAL_ITEMS_SCANNED",
        "DELETE_CANDIDATE_COUNT",
        "DELETE_CANDIDATE_MB",
        "PROTECTED_KEEP_COUNT",
        "MANUAL_REVIEW_COUNT",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_SELL",
        "AUTO_TRADE",
        "REPORT",
        "CSV",
        "READ_FIRST",
    ]:
        print(f"{key}: {result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
