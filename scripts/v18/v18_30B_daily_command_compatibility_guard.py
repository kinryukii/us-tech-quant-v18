from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import shutil
import subprocess
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_30B_DAILY_COMMAND_COMPATIBILITY_GUARD_READY"
STATUS_WARN = "WARN_V18_30B_DAILY_COMMAND_COMPATIBILITY_GUARD_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_30B_DAILY_COMMAND_COMPATIBILITY_GUARD_ERROR"
MODE = "DAILY_COMMAND_COMPATIBILITY_GUARD"

EXPECTED_ROWS = 252
LEGACY_ROWS = 20

CURRENT_RANKED = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
CURRENT_THEME = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
CURRENT_RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
SNAPSHOT_LEDGER = "state/v18/recommendation_snapshots/V18_DAILY_RECOMMENDATION_TIER_LEDGER.csv"
SIGNAL_FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
R30A_READ_FIRST = "outputs/v18/ops/V18_30A_READ_FIRST.txt"
CORRECT_R21_WRAPPER = "scripts/v18/run_v18_25A_R21_daily_signal_freeze_forward_test_ledger.ps1"
R28A_WRAPPER = "scripts/v18/run_v18_28A_sector_theme_classification_audit.ps1"
R28B_WRAPPER = "scripts/v18/run_v18_28B_recommendation_tier_action_layer.ps1"

OUT_CSV = "outputs/v18/ops/V18_30B_DAILY_COMMAND_COMPATIBILITY_GUARD.csv"
OUT_REPORT = "outputs/v18/read_center/V18_30B_DAILY_COMMAND_COMPATIBILITY_GUARD_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_30B_READ_FIRST.txt"

BACKUP_ROOT = "archive/v18/compatibility_guard_backups"

PROTECTED_FILES = [
    SNAPSHOT_LEDGER,
    SIGNAL_FREEZE_LEDGER,
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
    "CURRENT_RANKED_CANDIDATE_ROW_COUNT",
    "CURRENT_THEME_CLASSIFICATION_ROW_COUNT",
    "CURRENT_RECOMMENDATION_ROW_COUNT",
    "CURRENT_RANKED_RDDT_COUNT",
    "CURRENT_RANKED_TLN_COUNT",
    "LATEST_RECOMMENDATION_SNAPSHOT_DATE",
    "LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT",
    "LATEST_SIGNAL_FREEZE_RUN_ID",
    "LATEST_SIGNAL_FREEZE_DATE",
    "LATEST_SIGNAL_FREEZE_TICKER_COUNT",
    "LEGACY_DAILY_OVERWRITE_DETECTED",
    "CURRENT_RECOMMENDATION_CORRUPTED_BY_LEGACY_CHAIN",
    "RECOVERY_CANDIDATE_COUNT",
    "BEST_RECOVERY_SOURCE_TYPE",
    "BEST_RECOVERY_CANDIDATE_PATH_OR_GROUP",
    "APPLY_RESTORE",
    "RESTORE_APPLIED",
    "R28A_RERUN",
    "R28B_RERUN",
    "R29C_RERUN_BLOCKED_TO_AVOID_DUPLICATE_SNAPSHOT",
    "CORRECT_R21_WRAPPER_FOUND",
    "CORRECT_R21_WRAPPER_PATH",
    "SAFE_DAILY_COMMAND_RECOMMENDATION",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "FORBIDDEN_MODIFIED",
]

CSV_FIELDS = [
    "category",
    "item",
    "status",
    "value",
    "details",
]

RANKED_RESTORE_FIELDS = [
    "rank",
    "ticker",
    "company_name",
    "composite_candidate_score",
    "primary_theme",
    "secondary_theme",
    "industry_group",
    "role_bucket",
    "cyclicality_bucket",
    "volatility_bucket",
    "liquidity_bucket",
    "theme_rank",
    "theme_percentile",
    "technical_timing_score",
    "overheat_penalty",
    "bb_status",
    "rsi_status",
    "kdj_status",
    "technical_signal",
    "technical_warning_label",
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


def latest_snapshot_group(rows: Sequence[Dict[str, str]]) -> Tuple[str, str, List[Dict[str, str]]]:
    groups: Dict[Tuple[str, str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (
            norm(row.get("snapshot_date")),
            norm(row.get("source_recommendation_run_id")),
            norm(row.get("snapshot_run_id")),
        )
        groups[key].append(row)
    candidates = [(key, group) for key, group in groups.items() if len(group) == EXPECTED_ROWS]
    if not candidates:
        return "", "", []
    key, group = max(
        candidates,
        key=lambda item: (
            parse_date(item[0][0]) or dt.date.min,
            max((parse_dt(row.get("append_timestamp")) for row in item[1]), default=dt.datetime.min),
            item[0][2],
        ),
    )
    return key[0], "|".join(part for part in key if part), group


def latest_freeze_group(rows: Sequence[Dict[str, str]]) -> Tuple[str, str, List[Dict[str, str]]]:
    groups: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[norm(row.get("run_id"))].append(row)
    if not groups:
        return "", "", []
    run_id, group = max(
        groups.items(),
        key=lambda item: (
            max((parse_dt(row.get("run_timestamp")) for row in item[1]), default=dt.datetime.min),
            max((parse_date(row.get("signal_date")) or dt.date.min for row in item[1]), default=dt.date.min),
            item[0],
        ),
    )
    signal_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in group), default=dt.date.min)
    return run_id, signal_date.isoformat() if signal_date != dt.date.min else "", group


def count_ticker(rows: Sequence[Dict[str, str]], symbol: str) -> int:
    return sum(1 for row in rows if ticker(row.get("ticker")) == symbol)


def duplicate_signal_date_ticker_count(rows: Sequence[Dict[str, str]]) -> int:
    counts = Counter((norm(row.get("signal_date")), ticker(row.get("ticker"))) for row in rows)
    return sum(1 for key, count in counts.items() if key[0] and key[1] and count > 1)


def recovery_candidates(snapshot_rows: Sequence[Dict[str, str]], freeze_rows: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    snap_groups: Dict[Tuple[str, str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in snapshot_rows:
        snap_groups[(norm(row.get("snapshot_date")), norm(row.get("source_recommendation_run_id")), norm(row.get("snapshot_run_id")))].append(row)
    for key, rows in snap_groups.items():
        if len(rows) == EXPECTED_ROWS:
            out.append(
                {
                    "source_type": "RECOMMENDATION_SNAPSHOT",
                    "path_or_group": f"{SNAPSHOT_LEDGER}::{key[0]}::{key[1]}::{key[2]}",
                    "row_count": len(rows),
                    "date": key[0],
                    "priority": 1,
                }
            )
    freeze_groups: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in freeze_rows:
        freeze_groups[norm(row.get("run_id"))].append(row)
    for run_id, rows in freeze_groups.items():
        tickers = {ticker(row.get("ticker")) for row in rows if ticker(row.get("ticker"))}
        if len(tickers) == EXPECTED_ROWS:
            signal_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in rows), default=dt.date.min)
            out.append(
                {
                    "source_type": "SIGNAL_FREEZE",
                    "path_or_group": f"{SIGNAL_FREEZE_LEDGER}::{run_id}",
                    "row_count": len(tickers),
                    "date": signal_date.isoformat() if signal_date != dt.date.min else "",
                    "priority": 2,
                }
            )
    return sorted(out, key=lambda row: (row["priority"], row["date"], row["path_or_group"]), reverse=False)


def ranked_rows_from_snapshot(rows: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    out = [{field: norm(row.get(field)) for field in RANKED_RESTORE_FIELDS} for row in rows]
    out.sort(key=lambda row: (to_int(row.get("rank"), 999999), ticker(row.get("ticker"))))
    return out


def ranked_rows_from_freeze(rows: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for row in rows:
        out.append(
            {
                "rank": norm(row.get("source_rank")) or norm(row.get("factor_pack_rank")),
                "ticker": ticker(row.get("ticker")),
                "company_name": "",
                "composite_candidate_score": norm(row.get("composite_candidate_score")),
                "primary_theme": "",
                "secondary_theme": "",
                "industry_group": "",
                "role_bucket": "",
                "cyclicality_bucket": "",
                "volatility_bucket": "",
                "liquidity_bucket": "",
                "theme_rank": "",
                "theme_percentile": "",
                "technical_timing_score": norm(row.get("technical_timing_score")),
                "overheat_penalty": "",
                "bb_status": "",
                "rsi_status": "",
                "kdj_status": "",
                "technical_signal": "",
                "technical_warning_label": "",
            }
        )
    out.sort(key=lambda row: (to_int(row.get("rank"), 999999), ticker(row.get("ticker"))))
    return out


def backup_current_files(root: Path, backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    for rel in [CURRENT_RANKED, CURRENT_THEME, CURRENT_RECOMMENDATIONS]:
        src = root / rel
        if src.exists():
            dest = backup_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def run_wrapper(root: Path, wrapper_rel: str) -> None:
    wrapper = root / wrapper_rel
    if not wrapper.exists():
        raise FileNotFoundError(wrapper)
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(wrapper), "-Root", str(root)],
        check=True,
        cwd=str(root),
    )


def markdown_table(rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> str:
    if not rows:
        return "_None._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def build_report(values: Dict[str, object], csv_rows: Sequence[Dict[str, object]], candidates: Sequence[Dict[str, object]]) -> str:
    recovery_rows = [row for row in csv_rows if row.get("category") == "recovery_candidate"]
    check_rows = [row for row in csv_rows if row.get("category") == "check"]
    return "\n".join(
        [
            "# V18.30B Daily Command Compatibility Guard",
            "",
            "## Read First",
            "```text",
            "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS),
            "```",
            "",
            "## Compatibility Warning",
            "Do not run `scripts/v18/run_v18_current_daily_command_center.ps1` before the V18.28+ layer until compatibility is fixed. Use the R21 wrapper recorded below for the 252-row flow.",
            "",
            "## Recovery Candidate List",
            markdown_table(recovery_rows, CSV_FIELDS),
            "## Anchor Checks",
            markdown_table(check_rows, CSV_FIELDS),
            "## Safe Daily Command Recommendation",
            f"`{values.get('SAFE_DAILY_COMMAND_RECOMMENDATION')}`",
        ]
    ) + "\n"


def run(root: Path, apply_restore: bool = False, refresh_derived: bool = False) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("V18_30B_%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)

    ranked = read_csv(root / CURRENT_RANKED)
    theme = read_csv(root / CURRENT_THEME)
    recs = read_csv(root / CURRENT_RECOMMENDATIONS)
    snapshots = read_csv(root / SNAPSHOT_LEDGER)
    freezes = read_csv(root / SIGNAL_FREEZE_LEDGER)

    latest_snapshot_date, latest_snapshot_group_id, latest_snapshot_rows = latest_snapshot_group(snapshots)
    latest_freeze_run_id, latest_freeze_date, latest_freeze_rows = latest_freeze_group(freezes)
    latest_freeze_ticker_count = len({ticker(row.get("ticker")) for row in latest_freeze_rows if ticker(row.get("ticker"))})
    recovery = recovery_candidates(snapshots, freezes)
    best = recovery[0] if recovery else {}

    rddt_count = count_ticker(ranked, "RDDT")
    tln_count = count_ticker(ranked, "TLN")
    legacy_detected = (
        (len(ranked) == LEGACY_ROWS or len(theme) == LEGACY_ROWS or len(recs) == LEGACY_ROWS)
        and len(latest_snapshot_rows) == EXPECTED_ROWS
    )
    rec_corrupted = len(recs) == LEGACY_ROWS and len(latest_snapshot_rows) == EXPECTED_ROWS
    correct_wrapper_found = (root / CORRECT_R21_WRAPPER).exists()
    freeze_duplicate_count = duplicate_signal_date_ticker_count(freezes)

    csv_rows: List[Dict[str, object]] = [
        {"category": "check", "item": "current_ranked_candidate_row_count", "status": "PASS" if len(ranked) == EXPECTED_ROWS else "WARN", "value": len(ranked), "details": f"expected {EXPECTED_ROWS}"},
        {"category": "check", "item": "current_theme_classification_row_count", "status": "PASS" if len(theme) == EXPECTED_ROWS else "WARN", "value": len(theme), "details": f"expected {EXPECTED_ROWS}"},
        {"category": "check", "item": "current_recommendation_row_count", "status": "PASS" if len(recs) == EXPECTED_ROWS else "WARN", "value": len(recs), "details": f"expected {EXPECTED_ROWS}"},
        {"category": "check", "item": "rddt_present", "status": "PASS" if rddt_count == 1 else "WARN", "value": rddt_count, "details": "RDDT should be present once in ranked candidates"},
        {"category": "check", "item": "tln_present", "status": "PASS" if tln_count == 1 else "WARN", "value": tln_count, "details": "TLN should be present once in ranked candidates"},
        {"category": "check", "item": "latest_snapshot_row_count", "status": "PASS" if len(latest_snapshot_rows) == EXPECTED_ROWS else "WARN", "value": len(latest_snapshot_rows), "details": latest_snapshot_group_id},
        {"category": "check", "item": "latest_signal_freeze_ticker_count", "status": "PASS" if latest_freeze_ticker_count == EXPECTED_ROWS else "WARN", "value": latest_freeze_ticker_count, "details": latest_freeze_run_id},
        {"category": "check", "item": "duplicate_signal_date_ticker_count_in_freeze_ledger", "status": "PASS" if freeze_duplicate_count == 0 else "WARN", "value": freeze_duplicate_count, "details": "Run V18.30D cleanup if nonzero"},
        {"category": "check", "item": "legacy_daily_overwrite_detected", "status": "WARN" if legacy_detected else "PASS", "value": bool_text(legacy_detected), "details": "20-row current files with 252-row snapshot available"},
        {"category": "check", "item": "correct_r21_wrapper_found", "status": "PASS" if correct_wrapper_found else "WARN", "value": bool_text(correct_wrapper_found), "details": CORRECT_R21_WRAPPER},
    ]
    for candidate in recovery:
        csv_rows.append(
            {
                "category": "recovery_candidate",
                "item": candidate["source_type"],
                "status": "PASS",
                "value": candidate["row_count"],
                "details": candidate["path_or_group"],
            }
        )

    restore_applied = False
    r28a_rerun = False
    r28b_rerun = False
    r29c_blocked = latest_snapshot_date == latest_freeze_date and len(latest_snapshot_rows) == EXPECTED_ROWS
    if apply_restore:
        if not recovery:
            raise RuntimeError("Apply restore requested but no 252-row recovery candidate was found")
        backup_dir = root / BACKUP_ROOT / run_id
        backup_current_files(root, backup_dir)
        if len(ranked) != EXPECTED_ROWS:
            if len(latest_snapshot_rows) == EXPECTED_ROWS:
                restored = ranked_rows_from_snapshot(latest_snapshot_rows)
            elif latest_freeze_ticker_count == EXPECTED_ROWS:
                restored = ranked_rows_from_freeze(latest_freeze_rows)
            else:
                raise RuntimeError("No valid 252-row restore source available")
            write_csv(root / CURRENT_RANKED, restored, RANKED_RESTORE_FIELDS)
            restore_applied = True
            restored_check = read_csv(root / CURRENT_RANKED)
            if len(restored_check) != EXPECTED_ROWS or count_ticker(restored_check, "RDDT") != 1 or count_ticker(restored_check, "TLN") != 1:
                raise RuntimeError("Restore row count or RDDT/TLN validation failed")
        if refresh_derived and restore_applied:
            run_wrapper(root, R28A_WRAPPER)
            r28a_rerun = True
            run_wrapper(root, R28B_WRAPPER)
            r28b_rerun = True

    post_ranked = read_csv(root / CURRENT_RANKED)
    post_theme = read_csv(root / CURRENT_THEME)
    post_recs = read_csv(root / CURRENT_RECOMMENDATIONS)
    post_rddt_count = count_ticker(post_ranked, "RDDT")
    post_tln_count = count_ticker(post_ranked, "TLN")

    forbidden_modified = protected_sig(root) != protected_before
    current_valid = (
        len(post_ranked) == EXPECTED_ROWS
        and len(post_theme) == EXPECTED_ROWS
        and len(post_recs) == EXPECTED_ROWS
        and post_rddt_count == 1
        and post_tln_count == 1
    )
    status = STATUS_OK
    if forbidden_modified:
        status = STATUS_FAIL
    elif apply_restore and not recovery:
        status = STATUS_FAIL
    elif legacy_detected or not current_valid:
        status = STATUS_WARN
    elif len(latest_snapshot_rows) != EXPECTED_ROWS or latest_freeze_ticker_count != EXPECTED_ROWS or not correct_wrapper_found:
        status = STATUS_WARN

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": len(post_ranked),
        "CURRENT_THEME_CLASSIFICATION_ROW_COUNT": len(post_theme),
        "CURRENT_RECOMMENDATION_ROW_COUNT": len(post_recs),
        "CURRENT_RANKED_RDDT_COUNT": post_rddt_count,
        "CURRENT_RANKED_TLN_COUNT": post_tln_count,
        "LATEST_RECOMMENDATION_SNAPSHOT_DATE": latest_snapshot_date,
        "LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT": len(latest_snapshot_rows),
        "LATEST_SIGNAL_FREEZE_RUN_ID": latest_freeze_run_id,
        "LATEST_SIGNAL_FREEZE_DATE": latest_freeze_date,
        "LATEST_SIGNAL_FREEZE_TICKER_COUNT": latest_freeze_ticker_count,
        "LEGACY_DAILY_OVERWRITE_DETECTED": bool_text(legacy_detected),
        "CURRENT_RECOMMENDATION_CORRUPTED_BY_LEGACY_CHAIN": bool_text(rec_corrupted),
        "RECOVERY_CANDIDATE_COUNT": len(recovery),
        "BEST_RECOVERY_SOURCE_TYPE": best.get("source_type", ""),
        "BEST_RECOVERY_CANDIDATE_PATH_OR_GROUP": best.get("path_or_group", ""),
        "APPLY_RESTORE": bool_text(apply_restore),
        "RESTORE_APPLIED": bool_text(restore_applied),
        "R28A_RERUN": bool_text(r28a_rerun),
        "R28B_RERUN": bool_text(r28b_rerun),
        "R29C_RERUN_BLOCKED_TO_AVOID_DUPLICATE_SNAPSHOT": bool_text(r29c_blocked),
        "CORRECT_R21_WRAPPER_FOUND": bool_text(correct_wrapper_found),
        "CORRECT_R21_WRAPPER_PATH": CORRECT_R21_WRAPPER if correct_wrapper_found else "",
        "SAFE_DAILY_COMMAND_RECOMMENDATION": f"Use {CORRECT_R21_WRAPPER}; do not run scripts/v18/run_v18_current_daily_command_center.ps1 before V18.28+ compatibility is fixed.",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": bool_text(forbidden_modified),
    }

    write_csv(root / OUT_CSV, csv_rows, CSV_FIELDS)
    write_text(root / OUT_REPORT, build_report(values, csv_rows, recovery))
    write_read_first(root / OUT_READ_FIRST, values)

    if status == STATUS_FAIL:
        raise RuntimeError("Daily command compatibility guard failed validation checks")
    return values


def write_failure(root: Path, error: BaseException) -> None:
    values = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("V18_30B_%Y%m%d_%H%M%S"),
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": 0,
        "CURRENT_THEME_CLASSIFICATION_ROW_COUNT": 0,
        "CURRENT_RECOMMENDATION_ROW_COUNT": 0,
        "CURRENT_RANKED_RDDT_COUNT": 0,
        "CURRENT_RANKED_TLN_COUNT": 0,
        "LATEST_RECOMMENDATION_SNAPSHOT_DATE": "",
        "LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT": 0,
        "LATEST_SIGNAL_FREEZE_RUN_ID": "",
        "LATEST_SIGNAL_FREEZE_DATE": "",
        "LATEST_SIGNAL_FREEZE_TICKER_COUNT": 0,
        "LEGACY_DAILY_OVERWRITE_DETECTED": "UNKNOWN",
        "CURRENT_RECOMMENDATION_CORRUPTED_BY_LEGACY_CHAIN": "UNKNOWN",
        "RECOVERY_CANDIDATE_COUNT": 0,
        "BEST_RECOVERY_SOURCE_TYPE": "",
        "BEST_RECOVERY_CANDIDATE_PATH_OR_GROUP": "",
        "APPLY_RESTORE": "UNKNOWN",
        "RESTORE_APPLIED": "FALSE",
        "R28A_RERUN": "FALSE",
        "R28B_RERUN": "FALSE",
        "R29C_RERUN_BLOCKED_TO_AVOID_DUPLICATE_SNAPSHOT": "UNKNOWN",
        "CORRECT_R21_WRAPPER_FOUND": "UNKNOWN",
        "CORRECT_R21_WRAPPER_PATH": "",
        "SAFE_DAILY_COMMAND_RECOMMENDATION": "ERROR",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "UNKNOWN",
    }
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, f"# V18.30B Daily Command Compatibility Guard Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.30B daily command compatibility guard.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--apply-restore", action="store_true", help="Restore current ranked candidates from the best 252-row recovery source.")
    parser.add_argument("--refresh-derived", action="store_true", help="After restore, rerun R28A and R28B wrappers.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        values = run(root, apply_restore=args.apply_restore, refresh_derived=args.refresh_derived)
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
