from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_30D_SAME_DAY_SIGNAL_FREEZE_REPLACE_POLICY_READY"
STATUS_WARN = "WARN_V18_30D_SAME_DAY_SIGNAL_FREEZE_REPLACE_POLICY_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_30D_SAME_DAY_SIGNAL_FREEZE_REPLACE_POLICY_ERROR"
MODE = "SAME_DAY_SIGNAL_FREEZE_REPLACE_POLICY"

FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
R21_SCRIPT = "scripts/v18/v18_25A_R21_daily_signal_freeze_forward_test_ledger.py"
R21_WRAPPER = "scripts/v18/run_v18_25A_R21_daily_signal_freeze_forward_test_ledger.ps1"
R30A_SCRIPT = "scripts/v18/v18_30A_daily_operator_control_center.py"
R30B_SCRIPT = "scripts/v18/v18_30B_daily_command_compatibility_guard.py"
BACKUP_ROOT = "archive/v18/signal_freeze_same_day_replace_backups"

OUT_READ_FIRST = "outputs/v18/ops/V18_30D_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/read_center/V18_30D_SAME_DAY_SIGNAL_FREEZE_REPLACE_POLICY_REPORT.md"
OUT_CSV = "outputs/v18/ops/V18_30D_SAME_DAY_SIGNAL_FREEZE_REPLACE_POLICY.csv"

LEDGER_FIELDS = [
    "signal_date",
    "run_id",
    "run_timestamp",
    "ticker",
    "source_rank",
    "factor_pack_rank",
    "factor_score",
    "technical_timing_score",
    "composite_candidate_score",
    "trust_level",
    "tier",
    "entry_reference_price",
    "price_asof_date",
    "data_freshness_status",
    "event_risk_status",
    "buy_permission",
    "official_decision_impact",
    "auto_trade",
    "auto_sell",
    "source_quality",
    "selected_source_file",
    "selected_source_file_mtime",
    "selected_source_file_size",
    "technical_source_file",
    "technical_source_file_mtime",
    "model_version",
    "pipeline_version",
    "notes",
    "forward_return_1d",
    "forward_return_3d",
    "forward_return_5d",
    "forward_return_10d",
    "forward_return_20d",
    "max_drawdown_after_signal",
    "max_runup_after_signal",
    "forward_fill_status",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "FREEZE_LEDGER_PATH",
    "PRE_LEDGER_ROWS",
    "SIGNAL_DATE_COUNT",
    "DUPLICATE_SIGNAL_DATE_TICKER_COUNT_BEFORE",
    "DUPLICATE_SIGNAL_DATE_TICKER_COUNT_AFTER",
    "R21_PATCH_APPLIED",
    "R21_WRAPPER_PATCH_APPLIED",
    "R30A_PATCH_APPLIED",
    "R30B_PATCH_APPLIED",
    "APPLY_CLEANUP",
    "CLEANUP_APPLIED",
    "BACKUP_PATH",
    "LATEST_SIGNAL_DATE",
    "LATEST_SIGNAL_DATE_ROW_COUNT",
    "LATEST_SIGNAL_DATE_UNIQUE_TICKER_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "FORBIDDEN_MODIFIED",
]

CSV_FIELDS = ["category", "item", "status", "value", "details"]

PROTECTED_FILES = [
    "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv",
    "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
    "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv",
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


def norm(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def ticker(value: object) -> str:
    return norm(value).upper()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def parse_date(value: object) -> Optional[dt.date]:
    text = norm(value)
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    try:
        return dt.date.fromisoformat(text[:10])
    except ValueError:
        return None


def parse_dt(value: object) -> dt.datetime:
    text = norm(value)
    if not text:
        return dt.datetime.min
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        parsed = parse_date(text)
        return dt.datetime.combine(parsed, dt.time.min) if parsed else dt.datetime.min


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
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


def duplicate_signal_date_ticker_count(rows: Sequence[Dict[str, str]]) -> int:
    counts = Counter((norm(row.get("signal_date")), ticker(row.get("ticker"))) for row in rows)
    return sum(1 for key, count in counts.items() if key[0] and key[1] and count > 1)


def latest_signal_date_info(rows: Sequence[Dict[str, str]]) -> Tuple[str, int, int]:
    dates = sorted({norm(row.get("signal_date")) for row in rows if norm(row.get("signal_date"))})
    if not dates:
        return "", 0, 0
    latest = dates[-1]
    latest_rows = [row for row in rows if norm(row.get("signal_date")) == latest]
    return latest, len(latest_rows), len({ticker(row.get("ticker")) for row in latest_rows if ticker(row.get("ticker"))})


def cleanup_rows(rows: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    best_by_key: Dict[Tuple[str, str], Dict[str, str]] = {}
    for row in rows:
        key = (norm(row.get("signal_date")), ticker(row.get("ticker")))
        if not key[0] or not key[1]:
            continue
        current = best_by_key.get(key)
        row_key = (parse_dt(row.get("run_timestamp")), norm(row.get("run_id")))
        current_key = (parse_dt(current.get("run_timestamp")), norm(current.get("run_id"))) if current else (dt.datetime.min, "")
        if current is None or row_key >= current_key:
            best_by_key[key] = row
    cleaned = list(best_by_key.values())
    cleaned.sort(key=lambda row: (norm(row.get("signal_date")), parse_dt(row.get("run_timestamp")), norm(row.get("run_id")), ticker(row.get("ticker"))))
    return cleaned


def file_contains(path: Path, patterns: Sequence[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return all(pattern in text for pattern in patterns)


def markdown_table(rows: Sequence[Dict[str, object]]) -> str:
    if not rows:
        return "_None._\n"
    lines = ["| " + " | ".join(CSV_FIELDS) + " |", "| " + " | ".join(["---"] * len(CSV_FIELDS)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in CSV_FIELDS) + " |")
    return "\n".join(lines) + "\n"


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def build_report(values: Dict[str, object], rows: Sequence[Dict[str, object]]) -> str:
    return "\n".join(
        [
            "# V18.30D Same-Day Signal Freeze Replace Policy",
            "",
            "## Read First",
            "```text",
            "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS),
            "```",
            "",
            "## Policy Summary",
            "R21 default mode is same-day replace by signal_date+ticker. Use -AllowSameDayAppend only for intentional intraday archival appends.",
            "",
            "## Checks",
            markdown_table(rows),
        ]
    ) + "\n"


def run(root: Path, apply_cleanup: bool = False) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("V18_30D_%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)
    ledger_path = root / FREEZE_LEDGER
    if not ledger_path.exists():
        raise FileNotFoundError(ledger_path)

    rows = read_csv(ledger_path)
    pre_rows = len(rows)
    dup_before = duplicate_signal_date_ticker_count(rows)
    signal_date_count = len({norm(row.get("signal_date")) for row in rows if norm(row.get("signal_date"))})
    latest_date, latest_date_rows, latest_date_unique = latest_signal_date_info(rows)

    r21_patch = file_contains(root / R21_SCRIPT, ["SAME_DAY_REPLACE_ENABLED", "allow_same_day_append", "DUPLICATE_SIGNAL_DATE_TICKER_COUNT_AFTER"])
    r21_wrapper_patch = file_contains(root / R21_WRAPPER, ["AllowSameDayAppend", "AppendIntradayRun", "--allow-same-day-append"])
    r30a_patch = file_contains(root / R30A_SCRIPT, ["latest_full_freeze_info", "SAME_DAY_MULTIPLE_FREEZE_WARNING"])
    r30b_patch = file_contains(root / R30B_SCRIPT, ["duplicate_signal_date_ticker_count_in_freeze_ledger"])

    backup_path = ""
    cleanup_applied = False
    dup_after = dup_before
    if apply_cleanup and dup_before:
        backup_dir = root / BACKUP_ROOT / run_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / "V18_DAILY_SIGNAL_FREEZE_LEDGER_PRE_CLEANUP.csv"
        write_csv(backup_file, rows, LEDGER_FIELDS)
        backup_path = str(backup_file)
        cleaned = cleanup_rows(rows)
        write_csv(ledger_path, cleaned, LEDGER_FIELDS)
        cleanup_applied = True
        rows = read_csv(ledger_path)
        dup_after = duplicate_signal_date_ticker_count(rows)
        latest_date, latest_date_rows, latest_date_unique = latest_signal_date_info(rows)
        if dup_after:
            raise RuntimeError("Duplicate signal_date+ticker rows remain after cleanup")
    elif apply_cleanup:
        backup_path = ""

    forbidden_modified = protected_sig(root) != protected_before
    status = STATUS_OK
    if forbidden_modified or not all([r21_patch, r21_wrapper_patch, r30a_patch, r30b_patch]):
        status = STATUS_FAIL
    elif dup_after:
        status = STATUS_WARN

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "FREEZE_LEDGER_PATH": str(ledger_path),
        "PRE_LEDGER_ROWS": pre_rows,
        "SIGNAL_DATE_COUNT": signal_date_count,
        "DUPLICATE_SIGNAL_DATE_TICKER_COUNT_BEFORE": dup_before,
        "DUPLICATE_SIGNAL_DATE_TICKER_COUNT_AFTER": dup_after,
        "R21_PATCH_APPLIED": bool_text(r21_patch),
        "R21_WRAPPER_PATCH_APPLIED": bool_text(r21_wrapper_patch),
        "R30A_PATCH_APPLIED": bool_text(r30a_patch),
        "R30B_PATCH_APPLIED": bool_text(r30b_patch),
        "APPLY_CLEANUP": bool_text(apply_cleanup),
        "CLEANUP_APPLIED": bool_text(cleanup_applied),
        "BACKUP_PATH": backup_path,
        "LATEST_SIGNAL_DATE": latest_date,
        "LATEST_SIGNAL_DATE_ROW_COUNT": latest_date_rows,
        "LATEST_SIGNAL_DATE_UNIQUE_TICKER_COUNT": latest_date_unique,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": bool_text(forbidden_modified),
    }
    check_rows = [
        {"category": "check", "item": "r21_patch_applied", "status": "PASS" if r21_patch else "FAIL", "value": bool_text(r21_patch), "details": R21_SCRIPT},
        {"category": "check", "item": "r21_wrapper_patch_applied", "status": "PASS" if r21_wrapper_patch else "FAIL", "value": bool_text(r21_wrapper_patch), "details": R21_WRAPPER},
        {"category": "check", "item": "r30a_patch_applied", "status": "PASS" if r30a_patch else "FAIL", "value": bool_text(r30a_patch), "details": R30A_SCRIPT},
        {"category": "check", "item": "r30b_patch_applied", "status": "PASS" if r30b_patch else "FAIL", "value": bool_text(r30b_patch), "details": R30B_SCRIPT},
        {"category": "ledger", "item": "duplicate_signal_date_ticker_before", "status": "PASS" if dup_before == 0 else "WARN", "value": dup_before, "details": "Apply cleanup if nonzero"},
        {"category": "ledger", "item": "duplicate_signal_date_ticker_after", "status": "PASS" if dup_after == 0 else "WARN", "value": dup_after, "details": "Post-cleanup duplicate count"},
        {"category": "ledger", "item": "latest_signal_date_row_count", "status": "PASS", "value": latest_date_rows, "details": latest_date},
        {"category": "ledger", "item": "latest_signal_date_unique_ticker_count", "status": "PASS" if latest_date_unique == 252 else "WARN", "value": latest_date_unique, "details": latest_date},
    ]
    write_csv(root / OUT_CSV, check_rows, CSV_FIELDS)
    write_text(root / OUT_REPORT, build_report(values, check_rows))
    write_read_first(root / OUT_READ_FIRST, values)
    if status == STATUS_FAIL:
        raise RuntimeError("R30D same-day replace policy validation failed")
    return values


def write_failure(root: Path, error: BaseException) -> None:
    values = {field: "" for field in READ_FIRST_FIELDS}
    values.update({
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("V18_30D_%Y%m%d_%H%M%S"),
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "UNKNOWN",
    })
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, f"# V18.30D Same-Day Signal Freeze Replace Policy Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.30D same-day signal freeze replace policy.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--apply-cleanup", action="store_true", help="Clean duplicate signal_date+ticker rows, keeping latest run_timestamp.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        values = run(root, apply_cleanup=args.apply_cleanup)
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
