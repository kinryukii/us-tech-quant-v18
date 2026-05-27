from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import subprocess
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_30C_OPERATOR_CONTROL_CENTER_LATEST_FREEZE_PATCH_READY"
STATUS_WARN = "WARN_V18_30C_OPERATOR_CONTROL_CENTER_LATEST_FREEZE_PATCH_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_30C_OPERATOR_CONTROL_CENTER_LATEST_FREEZE_PATCH_ERROR"
MODE = "OPERATOR_CONTROL_CENTER_LATEST_FREEZE_SOURCE_PATCH"

SIGNAL_FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
CURRENT_RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
CURRENT_THEME = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
R30A_READ_FIRST = "outputs/v18/ops/V18_30A_READ_FIRST.txt"
R30A_WRAPPER = "scripts/v18/run_v18_30A_daily_operator_control_center.ps1"

OUT_READ_FIRST = "outputs/v18/ops/V18_30C_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/read_center/V18_30C_OPERATOR_CONTROL_CENTER_LATEST_FREEZE_PATCH_REPORT.md"
OUT_CSV = "outputs/v18/ops/V18_30C_OPERATOR_CONTROL_CENTER_LATEST_FREEZE_PATCH.csv"

PROTECTED_FILES = [
    SIGNAL_FREEZE_LEDGER,
    CURRENT_RECOMMENDATIONS,
    CURRENT_CANDIDATES,
    CURRENT_THEME,
    "state/v18/recommendation_snapshots/V18_DAILY_RECOMMENDATION_TIER_LEDGER.csv",
    "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
    "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv",
]
PROTECTED_DIRS = [
    "state/v18/price_cache",
    "state/v18/trading",
    "outputs/v18/official_daily",
    "outputs/v18/factor_pack",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R30A_STATUS_AFTER_PATCH",
    "CURRENT_RECOMMENDATION_ROW_COUNT",
    "CURRENT_RANKED_CANDIDATE_ROW_COUNT",
    "THEME_CLASSIFICATION_ROW_COUNT",
    "LATEST_FULL_SIGNAL_FREEZE_RUN_ID",
    "LATEST_FULL_SIGNAL_FREEZE_DATE",
    "LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT",
    "PREVIOUS_FULL_SIGNAL_FREEZE_RUN_ID",
    "SAME_DAY_FULL_FREEZE_RUN_COUNT",
    "SAME_DAY_MULTIPLE_FREEZE_WARNING",
    "SNAPSHOT_MATCHES_LATEST_FREEZE_DATE",
    "MANUAL_REVIEW_READY",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "FORBIDDEN_MODIFIED",
]

CSV_FIELDS = [
    "category",
    "item",
    "status",
    "value",
    "details",
]


def norm(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def ticker(value: object) -> str:
    return norm(value).upper()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def to_int(value: object, default: int = 0) -> int:
    try:
        text = norm(value)
        return int(float(text)) if text else default
    except Exception:
        return default


def parse_date(value: object) -> Optional[dt.date]:
    text = norm(value)
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%m-%d-%Y", "%Y%m%d"):
        try:
            return dt.datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def parse_dt(value: object) -> dt.datetime:
    text = norm(value)
    if not text:
        return dt.datetime.min
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        parsed = parse_date(text)
        if parsed:
            return dt.datetime.combine(parsed, dt.time.min)
    return dt.datetime.min


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def file_sig(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return "MISSING"
    stat = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"{stat.st_size}:{stat.st_mtime_ns}:{digest.hexdigest()}"


def dir_sig(path: Path) -> str:
    if not path.exists() or not path.is_dir():
        return "MISSING"
    parts: List[str] = []
    for child in sorted(path.rglob("*")):
        if child.is_file():
            stat = child.stat()
            parts.append(f"{child.relative_to(path).as_posix()}:{stat.st_size}:{stat.st_mtime_ns}")
    return "|".join(parts)


def protected_sig(root: Path) -> Dict[str, str]:
    sig: Dict[str, str] = {}
    for rel in PROTECTED_FILES:
        sig[f"file:{rel}"] = file_sig(root / rel)
    for rel in PROTECTED_DIRS:
        sig[f"dir:{rel}"] = dir_sig(root / rel)
    return sig


def read_status_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def latest_full_freeze_info(root: Path) -> Tuple[str, str, int, str, int, bool]:
    path = root / SIGNAL_FREEZE_LEDGER
    if not path.exists():
        raise FileNotFoundError(path)
    rows = read_csv(path)
    if not rows:
        raise RuntimeError("Signal freeze ledger is empty")
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[norm(row.get("run_id"))].append(row)
    full_runs: List[Tuple[str, str, int, dt.datetime, dt.date]] = []
    for run_id, run_rows in grouped.items():
        tickers = {ticker(row.get("ticker")) for row in run_rows if ticker(row.get("ticker"))}
        if len(tickers) == 252:
            latest_ts = max((parse_dt(row.get("run_timestamp")) for row in run_rows), default=dt.datetime.min)
            latest_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in run_rows), default=dt.date.min)
            full_runs.append((run_id, latest_date.isoformat() if latest_date != dt.date.min else "", len(tickers), latest_ts, latest_date))
    if not full_runs:
        raise RuntimeError("No full 252-row signal freeze found")
    full_runs.sort(key=lambda item: (item[3], item[4], item[0]))
    latest_run_id, latest_date, latest_count, _, _ = full_runs[-1]
    previous_run_id = full_runs[-2][0] if len(full_runs) > 1 else ""
    same_day_count = sum(1 for item in full_runs if item[1] == latest_date)
    same_day_warning = same_day_count > 1
    return latest_run_id, latest_date, latest_count, previous_run_id, same_day_count, same_day_warning


def run_r30a(root: Path) -> Dict[str, str]:
    wrapper = root / R30A_WRAPPER
    if not wrapper.exists():
        raise FileNotFoundError(wrapper)
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(wrapper), "-Root", str(root)],
        check=True,
        cwd=str(root),
    )
    return read_status_file(root / R30A_READ_FIRST)


def markdown_table(rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> str:
    if not rows:
        return "_None._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def build_report(values: Dict[str, object], rows: Sequence[Dict[str, object]]) -> str:
    return "\n".join(
        [
            "# V18.30C Operator Control Center Latest Freeze Patch",
            "",
            "## Read First",
            "```text",
            "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS),
            "```",
            "",
            "## Patch Summary",
            f"- Direct latest full freeze from ledger: `{values.get('LATEST_FULL_SIGNAL_FREEZE_RUN_ID')}`",
            f"- Same-day full freeze count: `{values.get('SAME_DAY_FULL_FREEZE_RUN_COUNT')}`",
            f"- Same-day warning: `{values.get('SAME_DAY_MULTIPLE_FREEZE_WARNING')}`",
            "",
            "## Validation Checks",
            markdown_table(rows, CSV_FIELDS),
            "## Operator Note",
            "Multiple full signal freezes exist for the same signal date. Treat later run as intraday refresh; avoid rerunning R21 again unless intentionally refreshing.",
        ]
    ) + "\n"


def run(root: Path) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("V18_30C_%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)

    r30a_before = read_status_file(root / R30A_READ_FIRST)
    r30a_after = run_r30a(root)
    latest_full_run_id, latest_full_date, latest_full_count, previous_full_run_id, same_day_count, same_day_warning = latest_full_freeze_info(root)

    current_rows = to_int(r30a_after.get("CURRENT_RECOMMENDATION_ROW_COUNT"))
    current_ranked_rows = to_int(r30a_after.get("CURRENT_RANKED_CANDIDATE_ROW_COUNT"))
    theme_rows = to_int(r30a_after.get("THEME_CLASSIFICATION_ROW_COUNT"))
    snapshot_matches = r30a_after.get("SNAPSHOT_MATCHES_LATEST_FREEZE_DATE") == "TRUE"
    manual_review_ready = r30a_after.get("MANUAL_REVIEW_READY") == "TRUE"
    r30a_status_after = r30a_after.get("STATUS") or r30a_before.get("STATUS") or ""
    current_valid = current_rows == 252 and current_ranked_rows == 252 and theme_rows == 252 and latest_full_count == 252

    csv_rows = [
        {"category": "check", "item": "current_recommendation_row_count", "status": "PASS" if current_rows == 252 else "FAIL", "value": current_rows, "details": "Expected 252"},
        {"category": "check", "item": "current_ranked_candidate_row_count", "status": "PASS" if current_ranked_rows == 252 else "FAIL", "value": current_ranked_rows, "details": "Expected 252"},
        {"category": "check", "item": "theme_classification_row_count", "status": "PASS" if theme_rows == 252 else "FAIL", "value": theme_rows, "details": "Expected 252"},
        {"category": "check", "item": "latest_full_signal_freeze_run_id", "status": "PASS" if latest_full_run_id else "FAIL", "value": latest_full_run_id, "details": "Directly selected from signal freeze ledger"},
        {"category": "check", "item": "same_day_full_freeze_run_count", "status": "WARN" if same_day_warning else "PASS", "value": same_day_count, "details": "Count of full 252-row freezes for latest signal date"},
        {"category": "check", "item": "same_day_multiple_freeze_warning", "status": "WARN" if same_day_warning else "PASS", "value": bool_text(same_day_warning), "details": "Later run should be treated as intraday refresh"},
        {"category": "check", "item": "snapshot_matches_latest_freeze_date", "status": "PASS" if snapshot_matches else "WARN", "value": bool_text(snapshot_matches), "details": "R30A alignment flag"},
        {"category": "check", "item": "manual_review_ready", "status": "PASS" if manual_review_ready else "WARN", "value": bool_text(manual_review_ready), "details": "R30A operator readiness"},
    ]

    forbidden_modified = protected_sig(root) != protected_before
    status = STATUS_OK
    if forbidden_modified or current_rows != 252 or current_ranked_rows != 252 or theme_rows != 252 or latest_full_count != 252:
        status = STATUS_FAIL
    elif same_day_warning:
        status = STATUS_WARN

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R30A_STATUS_AFTER_PATCH": r30a_status_after,
        "CURRENT_RECOMMENDATION_ROW_COUNT": current_rows,
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": current_ranked_rows,
        "THEME_CLASSIFICATION_ROW_COUNT": theme_rows,
        "LATEST_FULL_SIGNAL_FREEZE_RUN_ID": latest_full_run_id,
        "LATEST_FULL_SIGNAL_FREEZE_DATE": latest_full_date,
        "LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT": latest_full_count,
        "PREVIOUS_FULL_SIGNAL_FREEZE_RUN_ID": previous_full_run_id,
        "SAME_DAY_FULL_FREEZE_RUN_COUNT": same_day_count,
        "SAME_DAY_MULTIPLE_FREEZE_WARNING": bool_text(same_day_warning),
        "SNAPSHOT_MATCHES_LATEST_FREEZE_DATE": bool_text(snapshot_matches),
        "MANUAL_REVIEW_READY": bool_text(manual_review_ready),
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "FORBIDDEN_MODIFIED": bool_text(forbidden_modified),
    }

    write_csv(root / OUT_CSV, csv_rows, CSV_FIELDS)
    write_text(root / OUT_REPORT, build_report(values, csv_rows))
    write_read_first(root / OUT_READ_FIRST, values)

    if status == STATUS_FAIL:
        raise RuntimeError("V18.30C latest freeze patch validation failed")
    return values


def write_failure(root: Path, error: BaseException) -> None:
    values: Dict[str, object] = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("V18_30C_%Y%m%d_%H%M%S"),
        "R30A_STATUS_AFTER_PATCH": "",
        "CURRENT_RECOMMENDATION_ROW_COUNT": 0,
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": 0,
        "THEME_CLASSIFICATION_ROW_COUNT": 0,
        "LATEST_FULL_SIGNAL_FREEZE_RUN_ID": "",
        "LATEST_FULL_SIGNAL_FREEZE_DATE": "",
        "LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT": 0,
        "PREVIOUS_FULL_SIGNAL_FREEZE_RUN_ID": "",
        "SAME_DAY_FULL_FREEZE_RUN_COUNT": 0,
        "SAME_DAY_MULTIPLE_FREEZE_WARNING": "UNKNOWN",
        "SNAPSHOT_MATCHES_LATEST_FREEZE_DATE": "UNKNOWN",
        "MANUAL_REVIEW_READY": "UNKNOWN",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "FORBIDDEN_MODIFIED": "UNKNOWN",
    }
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, f"# V18.30C Operator Control Center Latest Freeze Patch Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.30C operator control center latest freeze patch.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        values = run(root)
        print(f"STATUS: {values['STATUS']}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return 0
    except Exception as exc:
        write_failure(root, exc)
        print(f"STATUS: {STATUS_FAIL}")
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
