from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRYRUN_OK = "OK_V18_25A_R25D_DRYRUN_OFFICIAL_MERGE_PLAN_READY"
STATUS_OK = "OK_V18_25A_R25D_OFFICIAL_FACTOR_TECHNICAL_MERGE_READY"
STATUS_INPUTS_MISSING = "WARN_V18_25A_R25D_INPUTS_MISSING"
STATUS_PLAN_NOT_VALIDATED = "WARN_V18_25A_R25D_MERGE_PLAN_NOT_FULLY_VALIDATED"
STATUS_TARGET_COUNT = "WARN_V18_25A_R25D_TARGET_COUNT_MISMATCH"
STATUS_SCHEMA = "WARN_V18_25A_R25D_SCHEMA_REVIEW_NEEDED"
STATUS_BACKUP = "WARN_V18_25A_R25D_BACKUP_INCOMPLETE"
STATUS_FACTOR_FAIL = "WARN_V18_25A_R25D_FACTOR_MERGE_PARTIAL_FAILURE"
STATUS_TECH_FAIL = "WARN_V18_25A_R25D_TECHNICAL_MERGE_PARTIAL_FAILURE"
STATUS_POST_FAIL = "WARN_V18_25A_R25D_POST_MERGE_VALIDATION_FAILURE"
STATUS_RANK_REVIEW = "WARN_V18_25A_R25D_RANK_RECOMPUTE_REVIEW_NEEDED"

EXPECTED_TARGET_COUNT = 93
MODE_DRYRUN = "DRYRUN_OFFICIAL_FACTOR_TECHNICAL_MERGE_PLAN"
MODE_APPLY = "APPLY_OFFICIAL_FACTOR_TECHNICAL_MERGE_WITH_BACKUP"

MERGE_PLAN = "outputs/v18/staged_factor_technical/V18_25A_R25C_CURRENT_OFFICIAL_MERGE_PLAN.csv"
BACKUP_PLAN = "outputs/v18/staged_factor_technical/V18_25A_R25C_CURRENT_REQUIRED_BACKUP_PLAN.csv"
STAGED_FACTOR = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_STAGED_FACTOR_ROWS.csv"
STAGED_TECH = "outputs/v18/staged_factor_technical/V18_25A_R25B_CURRENT_STAGED_TECHNICAL_ROWS.csv"
FACTOR_CURRENT = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_CURRENT = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
PRICE_CACHE = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OUT_FACTOR_PLAN = "outputs/v18/staged_factor_technical/V18_25A_R25D_CURRENT_FACTOR_MERGE_PLAN.csv"
OUT_TECH_PLAN = "outputs/v18/staged_factor_technical/V18_25A_R25D_CURRENT_TECHNICAL_MERGE_PLAN.csv"
OUT_FACTOR_RESULT = "outputs/v18/staged_factor_technical/V18_25A_R25D_CURRENT_FACTOR_MERGE_RESULT.csv"
OUT_TECH_RESULT = "outputs/v18/staged_factor_technical/V18_25A_R25D_CURRENT_TECHNICAL_MERGE_RESULT.csv"
OUT_POST = "outputs/v18/staged_factor_technical/V18_25A_R25D_CURRENT_POST_MERGE_VALIDATION.csv"
OUT_BACKUP_MANIFEST = "outputs/v18/staged_factor_technical/V18_25A_R25D_CURRENT_BACKUP_MANIFEST.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R25D_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R25D_CURRENT_OFFICIAL_FACTOR_TECHNICAL_MERGE_REPORT.md"

PLAN_FIELDS = [
    "ticker", "merge_action", "current_row_exists", "staged_row_present", "schema_compatible",
    "eligible", "reason", "source_staged_file", "target_official_file",
]
RESULT_FIELDS = [
    "ticker", "merge_action", "attempted", "success", "pre_row_exists", "post_row_exists", "reason",
]
POST_FIELDS = [
    "validation_item", "status", "expected_value", "actual_value", "reason",
]
MANIFEST_FIELDS = [
    "backup_item", "source_path", "backup_path", "required", "created", "size_bytes", "notes",
]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "RUN_ID", "MAX_TICKERS", "MERGE_PLAN_PATH", "STAGED_FACTOR_ROWS_PATH",
    "STAGED_TECHNICAL_ROWS_PATH", "OFFICIAL_FACTOR_PACK_PATH", "OFFICIAL_TECHNICAL_TIMING_PATH",
    "BACKUP_DIR", "RESTORE_SCRIPT_PATH", "EXPECTED_TARGET_COUNT", "SELECTED_MERGE_TARGET_COUNT",
    "FACTOR_PRE_ROW_COUNT", "FACTOR_POST_ROW_COUNT", "TECHNICAL_PRE_ROW_COUNT", "TECHNICAL_POST_ROW_COUNT",
    "FACTOR_APPEND_ATTEMPT_COUNT", "FACTOR_APPEND_SUCCESS_COUNT", "FACTOR_UPDATE_ATTEMPT_COUNT",
    "FACTOR_UPDATE_SUCCESS_COUNT", "FACTOR_MERGE_FAIL_COUNT", "TECHNICAL_APPEND_ATTEMPT_COUNT",
    "TECHNICAL_APPEND_SUCCESS_COUNT", "TECHNICAL_UPDATE_ATTEMPT_COUNT", "TECHNICAL_UPDATE_SUCCESS_COUNT",
    "TECHNICAL_MERGE_FAIL_COUNT", "POST_FACTOR_TARGET_PRESENT_COUNT", "POST_TECHNICAL_TARGET_PRESENT_COUNT",
    "POST_FACTOR_TARGET_MISSING_COUNT", "POST_TECHNICAL_TARGET_MISSING_COUNT", "POST_FACTOR_DUPLICATE_TARGET_COUNT",
    "POST_TECHNICAL_DUPLICATE_TARGET_COUNT", "POST_FACTOR_SCORE_MISSING_COUNT", "POST_TECHNICAL_SCORE_MISSING_COUNT",
    "FACTOR_RANK_RECOMPUTE_STATUS", "NON_TARGET_FACTOR_ROWS_PRESERVED", "NON_TARGET_TECHNICAL_ROWS_PRESERVED",
    "BACKUP_CREATED", "RESTORE_SCRIPT_CREATED", "OFFICIAL_FACTOR_PACK_MERGE_APPLIED",
    "OFFICIAL_TECHNICAL_TIMING_MERGE_APPLIED", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL",
    "EXTERNAL_FETCH_EXECUTED", "BACKTEST_EXECUTED", "PRICE_CACHE_MODIFIED", "ROLLING_LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "TIER_FILES_MODIFIED", "OFFICIAL_DECISION_MODIFIED",
    "VALIDATION_FAIL_COUNT", "FORBIDDEN_MODIFIED", "NEXT_RECOMMENDED_STEP",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def to_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip()
        return float(text) if text else None
    except Exception:
        return None


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(p.relative_to(root)): file_sig(p) for p in root.rglob("*") if p.is_file()}


def by_ticker(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {norm_ticker(row.get("ticker")): row for row in rows if norm_ticker(row.get("ticker"))}


def duplicate_count(rows: List[Dict[str, str]], tickers: Optional[set[str]] = None) -> int:
    counts: Dict[str, int] = {}
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker and (tickers is None or ticker in tickers):
            counts[ticker] = counts.get(ticker, 0) + 1
    return sum(1 for count in counts.values() if count > 1)


def score_col(fields: Sequence[str], candidates: Sequence[str]) -> str:
    by_lower = {field.lower(): field for field in fields}
    for candidate in candidates:
        if candidate.lower() in by_lower:
            return by_lower[candidate.lower()]
    return ""


def merge_rows(
    current_rows: List[Dict[str, str]],
    staged_by_ticker: Dict[str, Dict[str, str]],
    selected_plan: List[Dict[str, str]],
    action_field: str,
    fields: Sequence[str],
) -> Tuple[List[Dict[str, str]], List[Dict[str, object]]]:
    rows_by_ticker = by_ticker(current_rows)
    ordered = [dict(row) for row in current_rows]
    results: List[Dict[str, object]] = []
    for plan_row in selected_plan:
        ticker = norm_ticker(plan_row.get("ticker"))
        action = str(plan_row.get(action_field, "")).strip().upper()
        staged = staged_by_ticker.get(ticker)
        pre_exists = ticker in rows_by_ticker
        attempted = action in {"APPEND_NEW_ROW", "UPDATE_EXISTING_ROW"}
        success = False
        reason = ""
        if not staged:
            reason = "staged row missing"
        elif action == "APPEND_NEW_ROW":
            if pre_exists:
                reason = "append refused because official row already exists"
            else:
                new_row = {field: staged.get(field, "") for field in fields}
                ordered.append(new_row)
                rows_by_ticker[ticker] = new_row
                success = True
        elif action == "UPDATE_EXISTING_ROW":
            if not pre_exists:
                reason = "update refused because official row is missing"
            else:
                replacement = {field: staged.get(field, "") for field in fields}
                for idx, row in enumerate(ordered):
                    if norm_ticker(row.get("ticker")) == ticker:
                        ordered[idx] = replacement
                        rows_by_ticker[ticker] = replacement
                        success = True
                        break
        else:
            reason = f"merge action not applied: {action or 'BLANK'}"
        if success:
            reason = "merged"
        results.append({
            "ticker": ticker,
            "merge_action": action,
            "attempted": str(attempted).upper(),
            "success": str(success).upper(),
            "pre_row_exists": str(pre_exists).upper(),
            "post_row_exists": str(ticker in rows_by_ticker).upper(),
            "reason": reason,
        })
    return ordered, results


def recompute_factor_rank(rows: List[Dict[str, str]], fields: Sequence[str]) -> str:
    if "factor_pack_rank" not in fields or "factor_pack_score" not in fields:
        return "RANK_RECOMPUTE_REVIEW_NEEDED"
    if any(to_float(row.get("factor_pack_score")) is None for row in rows):
        return "RANK_RECOMPUTE_REVIEW_NEEDED"
    rows.sort(key=lambda row: (-float(row.get("factor_pack_score", "0")), norm_ticker(row.get("ticker"))))
    for idx, row in enumerate(rows, 1):
        row["factor_pack_rank"] = str(idx)
    return "RANK_RECOMPUTED_BY_FACTOR_PACK_SCORE_DESC_TICKER_ASC"


def non_target_rows_preserved(
    before_rows: List[Dict[str, str]],
    after_rows: List[Dict[str, str]],
    target_tickers: set[str],
    ignore_fields: Optional[set[str]] = None,
) -> bool:
    ignore_fields = ignore_fields or set()
    before = {norm_ticker(row.get("ticker")): row for row in before_rows if norm_ticker(row.get("ticker")) not in target_tickers}
    after = {norm_ticker(row.get("ticker")): row for row in after_rows if norm_ticker(row.get("ticker")) not in target_tickers}
    if set(before) != set(after):
        return False
    for ticker, before_row in before.items():
        after_row = after[ticker]
        keys = set(before_row) | set(after_row)
        for key in keys:
            if key in ignore_fields:
                continue
            if str(before_row.get(key, "")) != str(after_row.get(key, "")):
                return False
    return True


def create_backup(root: Path, backup_dir: Path) -> Tuple[bool, bool, List[Dict[str, object]], Path]:
    ensure_dir(backup_dir)
    factor_src = root / FACTOR_CURRENT
    tech_src = root / TECH_CURRENT
    factor_backup = backup_dir / factor_src.name
    tech_backup = backup_dir / tech_src.name
    shutil.copy2(factor_src, factor_backup)
    shutil.copy2(tech_src, tech_backup)
    restore = backup_dir / "RESTORE_V18_25A_R25D_FACTOR_TECHNICAL.ps1"
    restore_text = f"""[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$backupDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Copy-Item -LiteralPath (Join-Path $backupDir "{factor_src.name}") -Destination (Join-Path $Root "{FACTOR_CURRENT.replace('/', '\\')}") -Force
Copy-Item -LiteralPath (Join-Path $backupDir "{tech_src.name}") -Destination (Join-Path $Root "{TECH_CURRENT.replace('/', '\\')}") -Force
Write-Host "Restored V18.25A-R25D factor pack and technical timing backups."
"""
    write_text(restore, restore_text)
    readme = backup_dir / "README_RESTORE_V18_25A_R25D.txt"
    write_text(readme, "\n".join([
        "V18.25A-R25D restore package",
        "",
        "Run RESTORE_V18_25A_R25D_FACTOR_TECHNICAL.ps1 from PowerShell to restore:",
        f"- {FACTOR_CURRENT}",
        f"- {TECH_CURRENT}",
        "",
    ]))
    rows = [
        {"backup_item": "official_factor_pack", "source_path": FACTOR_CURRENT, "backup_path": str(factor_backup), "required": "TRUE", "created": str(factor_backup.exists()).upper(), "size_bytes": factor_backup.stat().st_size if factor_backup.exists() else 0, "notes": ""},
        {"backup_item": "official_technical_timing", "source_path": TECH_CURRENT, "backup_path": str(tech_backup), "required": "TRUE", "created": str(tech_backup.exists()).upper(), "size_bytes": tech_backup.stat().st_size if tech_backup.exists() else 0, "notes": ""},
        {"backup_item": "restore_script", "source_path": "", "backup_path": str(restore), "required": "TRUE", "created": str(restore.exists()).upper(), "size_bytes": restore.stat().st_size if restore.exists() else 0, "notes": ""},
        {"backup_item": "restore_readme", "source_path": "", "backup_path": str(readme), "required": "TRUE", "created": str(readme.exists()).upper(), "size_bytes": readme.stat().st_size if readme.exists() else 0, "notes": ""},
    ]
    manifest = backup_dir / "MANIFEST.csv"
    write_csv(manifest, rows, MANIFEST_FIELDS)
    rows.append({"backup_item": "manifest", "source_path": "", "backup_path": str(manifest), "required": "TRUE", "created": str(manifest.exists()).upper(), "size_bytes": manifest.stat().st_size if manifest.exists() else 0, "notes": ""})
    backup_ok = factor_backup.exists() and tech_backup.exists() and manifest.exists()
    restore_ok = restore.exists()
    return backup_ok, restore_ok, rows, restore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--max-tickers", type=int, default=93)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--require-validated-merge-plan", action="store_true", default=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R25D_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    mode = MODE_DRYRUN if args.dry_run else MODE_APPLY
    backup_dir = root / "archive/v18/factor_technical_backups" / run_id
    restore_script = backup_dir / "RESTORE_V18_25A_R25D_FACTOR_TECHNICAL.ps1"
    before = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor_target": file_sig(root / FACTOR_CURRENT),
        "tech_target": file_sig(root / TECH_CURRENT),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
    }

    required = [MERGE_PLAN, BACKUP_PLAN, STAGED_FACTOR, STAGED_TECH, FACTOR_CURRENT, TECH_CURRENT]
    missing = [path for path in required if not (root / path).exists()]
    merge_plan, _ = read_csv(root / MERGE_PLAN)
    staged_factor, factor_fields = read_csv(root / STAGED_FACTOR)
    staged_tech, tech_fields = read_csv(root / STAGED_TECH)
    factor_current, factor_current_fields = read_csv(root / FACTOR_CURRENT)
    tech_current, tech_current_fields = read_csv(root / TECH_CURRENT)

    selected = [row for row in merge_plan if is_true(row.get("merge_allowed_next"))][: max(args.max_tickers, 0)]
    selected_tickers = [norm_ticker(row.get("ticker")) for row in selected if norm_ticker(row.get("ticker"))]
    selected_set = set(selected_tickers)
    plan_fully_validated = len(selected) == min(len(merge_plan), max(args.max_tickers, 0)) and all(is_true(row.get("merge_allowed_next")) for row in selected)
    staged_factor_by_ticker = by_ticker(staged_factor)
    staged_tech_by_ticker = by_ticker(staged_tech)
    factor_current_by_ticker = by_ticker(factor_current)
    tech_current_by_ticker = by_ticker(tech_current)
    factor_schema_ok = bool(factor_fields) and list(factor_fields) == list(factor_current_fields)
    tech_schema_ok = bool(tech_fields) and list(tech_fields) == list(tech_current_fields)
    staged_factor_set = set(staged_factor_by_ticker) & selected_set
    staged_tech_set = set(staged_tech_by_ticker) & selected_set
    target_sets_ok = selected_set == staged_factor_set == staged_tech_set
    duplicate_inputs = duplicate_count(staged_factor, selected_set) or duplicate_count(staged_tech, selected_set)

    factor_plan_rows = []
    tech_plan_rows = []
    for row in selected:
        ticker = norm_ticker(row.get("ticker"))
        factor_plan_rows.append({
            "ticker": ticker,
            "merge_action": row.get("factor_merge_action", ""),
            "current_row_exists": str(ticker in factor_current_by_ticker).upper(),
            "staged_row_present": str(ticker in staged_factor_by_ticker).upper(),
            "schema_compatible": str(factor_schema_ok).upper(),
            "eligible": str(factor_schema_ok and ticker in staged_factor_by_ticker and is_true(row.get("merge_allowed_next"))).upper(),
            "reason": row.get("reason", ""),
            "source_staged_file": STAGED_FACTOR,
            "target_official_file": FACTOR_CURRENT,
        })
        tech_plan_rows.append({
            "ticker": ticker,
            "merge_action": row.get("technical_merge_action", ""),
            "current_row_exists": str(ticker in tech_current_by_ticker).upper(),
            "staged_row_present": str(ticker in staged_tech_by_ticker).upper(),
            "schema_compatible": str(tech_schema_ok).upper(),
            "eligible": str(tech_schema_ok and ticker in staged_tech_by_ticker and is_true(row.get("merge_allowed_next"))).upper(),
            "reason": row.get("reason", ""),
            "source_staged_file": STAGED_TECH,
            "target_official_file": TECH_CURRENT,
        })

    merged_factor, factor_results = merge_rows(factor_current, staged_factor_by_ticker, selected, "factor_merge_action", factor_current_fields)
    merged_tech, tech_results = merge_rows(tech_current, staged_tech_by_ticker, selected, "technical_merge_action", tech_current_fields)
    rank_status = recompute_factor_rank(merged_factor, factor_current_fields)
    non_target_factor_preserved = non_target_rows_preserved(factor_current, merged_factor, selected_set, {"factor_pack_rank"})
    non_target_tech_preserved = non_target_rows_preserved(tech_current, merged_tech, selected_set)

    backup_created = False
    restore_created = False
    backup_manifest_rows: List[Dict[str, object]] = []
    if not args.dry_run and not missing and plan_fully_validated and len(selected_set) == EXPECTED_TARGET_COUNT and target_sets_ok and not duplicate_inputs and factor_schema_ok and tech_schema_ok:
        backup_created, restore_created, backup_manifest_rows, restore_script = create_backup(root, backup_dir)
        if backup_created and restore_created:
            write_csv(root / FACTOR_CURRENT, merged_factor, factor_current_fields)
            write_csv(root / TECH_CURRENT, merged_tech, tech_current_fields)
    elif args.dry_run:
        backup_manifest_rows = [{
            "backup_item": "dryrun_backup_not_created",
            "source_path": "",
            "backup_path": str(backup_dir),
            "required": "FALSE",
            "created": "FALSE",
            "size_bytes": 0,
            "notes": "DryRun does not create backup or modify official files.",
        }]

    post_factor_rows, _ = read_csv(root / FACTOR_CURRENT) if not args.dry_run else (merged_factor, factor_current_fields)
    post_tech_rows, _ = read_csv(root / TECH_CURRENT) if not args.dry_run else (merged_tech, tech_current_fields)
    post_factor_by_ticker = by_ticker(post_factor_rows)
    post_tech_by_ticker = by_ticker(post_tech_rows)
    factor_score = score_col(factor_current_fields, ["factor_score", "factor_pack_score", "F010_XSEC_COMPOSITE_RANK"])
    tech_score = score_col(tech_current_fields, ["technical_timing_score", "technical_score"])
    post_factor_present = sum(1 for ticker in selected_set if ticker in post_factor_by_ticker)
    post_tech_present = sum(1 for ticker in selected_set if ticker in post_tech_by_ticker)
    post_factor_missing = len(selected_set) - post_factor_present
    post_tech_missing = len(selected_set) - post_tech_present
    post_factor_dup_targets = duplicate_count(post_factor_rows, selected_set)
    post_tech_dup_targets = duplicate_count(post_tech_rows, selected_set)
    post_factor_score_missing = sum(1 for ticker in selected_set if ticker not in post_factor_by_ticker or to_float(post_factor_by_ticker[ticker].get(factor_score)) is None)
    post_tech_score_missing = sum(1 for ticker in selected_set if ticker not in post_tech_by_ticker or to_float(post_tech_by_ticker[ticker].get(tech_score)) is None)

    factor_append_attempt = sum(1 for row in factor_results if row["merge_action"] == "APPEND_NEW_ROW" and row["attempted"] == "TRUE")
    factor_append_success = sum(1 for row in factor_results if row["merge_action"] == "APPEND_NEW_ROW" and row["success"] == "TRUE")
    factor_update_attempt = sum(1 for row in factor_results if row["merge_action"] == "UPDATE_EXISTING_ROW" and row["attempted"] == "TRUE")
    factor_update_success = sum(1 for row in factor_results if row["merge_action"] == "UPDATE_EXISTING_ROW" and row["success"] == "TRUE")
    factor_fail = sum(1 for row in factor_results if row["attempted"] == "TRUE" and row["success"] != "TRUE")
    tech_append_attempt = sum(1 for row in tech_results if row["merge_action"] == "APPEND_NEW_ROW" and row["attempted"] == "TRUE")
    tech_append_success = sum(1 for row in tech_results if row["merge_action"] == "APPEND_NEW_ROW" and row["success"] == "TRUE")
    tech_update_attempt = sum(1 for row in tech_results if row["merge_action"] == "UPDATE_EXISTING_ROW" and row["attempted"] == "TRUE")
    tech_update_success = sum(1 for row in tech_results if row["merge_action"] == "UPDATE_EXISTING_ROW" and row["success"] == "TRUE")
    tech_fail = sum(1 for row in tech_results if row["attempted"] == "TRUE" and row["success"] != "TRUE")

    write_csv(root / OUT_FACTOR_PLAN, factor_plan_rows, PLAN_FIELDS)
    write_csv(root / OUT_TECH_PLAN, tech_plan_rows, PLAN_FIELDS)
    write_csv(root / OUT_FACTOR_RESULT, factor_results, RESULT_FIELDS)
    write_csv(root / OUT_TECH_RESULT, tech_results, RESULT_FIELDS)
    write_csv(root / OUT_BACKUP_MANIFEST, backup_manifest_rows, MANIFEST_FIELDS)

    post_rows = [
        {"validation_item": "selected_target_count", "status": "PASS" if len(selected_set) == EXPECTED_TARGET_COUNT else "FAIL", "expected_value": EXPECTED_TARGET_COUNT, "actual_value": len(selected_set), "reason": ""},
        {"validation_item": "post_factor_target_present", "status": "PASS" if post_factor_present == len(selected_set) else "FAIL", "expected_value": len(selected_set), "actual_value": post_factor_present, "reason": ""},
        {"validation_item": "post_technical_target_present", "status": "PASS" if post_tech_present == len(selected_set) else "FAIL", "expected_value": len(selected_set), "actual_value": post_tech_present, "reason": ""},
        {"validation_item": "post_factor_duplicate_targets", "status": "PASS" if post_factor_dup_targets == 0 else "FAIL", "expected_value": 0, "actual_value": post_factor_dup_targets, "reason": ""},
        {"validation_item": "post_technical_duplicate_targets", "status": "PASS" if post_tech_dup_targets == 0 else "FAIL", "expected_value": 0, "actual_value": post_tech_dup_targets, "reason": ""},
        {"validation_item": "post_factor_score_missing", "status": "PASS" if post_factor_score_missing == 0 else "FAIL", "expected_value": 0, "actual_value": post_factor_score_missing, "reason": ""},
        {"validation_item": "post_technical_score_missing", "status": "PASS" if post_tech_score_missing == 0 else "FAIL", "expected_value": 0, "actual_value": post_tech_score_missing, "reason": ""},
        {"validation_item": "restore_script_exists", "status": "PASS" if args.dry_run or restore_script.exists() else "FAIL", "expected_value": "TRUE", "actual_value": str(args.dry_run or restore_script.exists()).upper(), "reason": ""},
        {"validation_item": "non_target_factor_rows_preserved_except_rank", "status": "PASS" if non_target_factor_preserved else "FAIL", "expected_value": "TRUE", "actual_value": str(non_target_factor_preserved).upper(), "reason": ""},
        {"validation_item": "non_target_technical_rows_preserved", "status": "PASS" if non_target_tech_preserved else "FAIL", "expected_value": "TRUE", "actual_value": str(non_target_tech_preserved).upper(), "reason": ""},
    ]
    write_csv(root / OUT_POST, post_rows, POST_FIELDS)

    after = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor_target": file_sig(root / FACTOR_CURRENT),
        "tech_target": file_sig(root / TECH_CURRENT),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
    }
    mods = {key: before[key] != after[key] for key in before}
    official_factor_applied = mods["factor_target"] and not args.dry_run
    official_tech_applied = mods["tech_target"] and not args.dry_run
    forbidden = mods["price"] or mods["ledger"] or mods["tier"] or mods["decision"] or (mods["factor_target"] and args.dry_run) or (mods["tech_target"] and args.dry_run)

    status = STATUS_DRYRUN_OK if args.dry_run else STATUS_OK
    if missing:
        status = STATUS_INPUTS_MISSING
    elif args.require_validated_merge_plan and not plan_fully_validated:
        status = STATUS_PLAN_NOT_VALIDATED
    elif len(selected_set) != EXPECTED_TARGET_COUNT or not target_sets_ok:
        status = STATUS_TARGET_COUNT
    elif duplicate_inputs or not factor_schema_ok or not tech_schema_ok:
        status = STATUS_SCHEMA
    elif not args.dry_run and (not backup_created or not restore_created):
        status = STATUS_BACKUP
    elif factor_fail:
        status = STATUS_FACTOR_FAIL
    elif tech_fail:
        status = STATUS_TECH_FAIL
    elif post_factor_missing or post_tech_missing or post_factor_dup_targets or post_tech_dup_targets or post_factor_score_missing or post_tech_score_missing or not non_target_factor_preserved or not non_target_tech_preserved:
        status = STATUS_POST_FAIL
    elif rank_status == "RANK_RECOMPUTE_REVIEW_NEEDED":
        status = STATUS_RANK_REVIEW

    validation_fail_count = int(status not in {STATUS_DRYRUN_OK, STATUS_OK} or forbidden)
    values = {
        "STATUS": status,
        "MODE": mode,
        "RUN_ID": run_id,
        "MAX_TICKERS": args.max_tickers,
        "MERGE_PLAN_PATH": MERGE_PLAN,
        "STAGED_FACTOR_ROWS_PATH": STAGED_FACTOR,
        "STAGED_TECHNICAL_ROWS_PATH": STAGED_TECH,
        "OFFICIAL_FACTOR_PACK_PATH": FACTOR_CURRENT,
        "OFFICIAL_TECHNICAL_TIMING_PATH": TECH_CURRENT,
        "BACKUP_DIR": str(backup_dir),
        "RESTORE_SCRIPT_PATH": str(restore_script),
        "EXPECTED_TARGET_COUNT": EXPECTED_TARGET_COUNT,
        "SELECTED_MERGE_TARGET_COUNT": len(selected_set),
        "FACTOR_PRE_ROW_COUNT": len(factor_current),
        "FACTOR_POST_ROW_COUNT": len(post_factor_rows),
        "TECHNICAL_PRE_ROW_COUNT": len(tech_current),
        "TECHNICAL_POST_ROW_COUNT": len(post_tech_rows),
        "FACTOR_APPEND_ATTEMPT_COUNT": factor_append_attempt,
        "FACTOR_APPEND_SUCCESS_COUNT": factor_append_success,
        "FACTOR_UPDATE_ATTEMPT_COUNT": factor_update_attempt,
        "FACTOR_UPDATE_SUCCESS_COUNT": factor_update_success,
        "FACTOR_MERGE_FAIL_COUNT": factor_fail,
        "TECHNICAL_APPEND_ATTEMPT_COUNT": tech_append_attempt,
        "TECHNICAL_APPEND_SUCCESS_COUNT": tech_append_success,
        "TECHNICAL_UPDATE_ATTEMPT_COUNT": tech_update_attempt,
        "TECHNICAL_UPDATE_SUCCESS_COUNT": tech_update_success,
        "TECHNICAL_MERGE_FAIL_COUNT": tech_fail,
        "POST_FACTOR_TARGET_PRESENT_COUNT": post_factor_present,
        "POST_TECHNICAL_TARGET_PRESENT_COUNT": post_tech_present,
        "POST_FACTOR_TARGET_MISSING_COUNT": post_factor_missing,
        "POST_TECHNICAL_TARGET_MISSING_COUNT": post_tech_missing,
        "POST_FACTOR_DUPLICATE_TARGET_COUNT": post_factor_dup_targets,
        "POST_TECHNICAL_DUPLICATE_TARGET_COUNT": post_tech_dup_targets,
        "POST_FACTOR_SCORE_MISSING_COUNT": post_factor_score_missing,
        "POST_TECHNICAL_SCORE_MISSING_COUNT": post_tech_score_missing,
        "FACTOR_RANK_RECOMPUTE_STATUS": rank_status,
        "NON_TARGET_FACTOR_ROWS_PRESERVED": str(non_target_factor_preserved).upper(),
        "NON_TARGET_TECHNICAL_ROWS_PRESERVED": str(non_target_tech_preserved).upper(),
        "BACKUP_CREATED": str(backup_created).upper(),
        "RESTORE_SCRIPT_CREATED": str(restore_created).upper(),
        "OFFICIAL_FACTOR_PACK_MERGE_APPLIED": str(official_factor_applied).upper(),
        "OFFICIAL_TECHNICAL_TIMING_MERGE_APPLIED": str(official_tech_applied).upper(),
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "PRICE_CACHE_MODIFIED": str(mods["price"]).upper(),
        "ROLLING_LEDGER_MODIFIED": str(mods["ledger"]).upper(),
        "FACTOR_PACK_MODIFIED": str(mods["factor_target"]).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(mods["tech_target"]).upper(),
        "TIER_FILES_MODIFIED": str(mods["tier"]).upper(),
        "OFFICIAL_DECISION_MODIFIED": str(mods["decision"]).upper(),
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden).upper(),
        "NEXT_RECOMMENDED_STEP": "R25E: Post-merge validation rerun of V18.25A / ranked candidates / trust classification to confirm the 93 tickers are no longer blocked by missing factor or technical rows.",
    }
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    report = "\n".join([
        "# V18.25A R25D Official Factor Technical Merge Report",
        "",
        f"STATUS: {status}",
        f"MODE: {mode}",
        f"RUN_ID: {run_id}",
        "",
        f"- selected_merge_target_count: {len(selected_set)}",
        f"- factor_rows_pre_post: {len(factor_current)} -> {len(post_factor_rows)}",
        f"- technical_rows_pre_post: {len(tech_current)} -> {len(post_tech_rows)}",
        f"- factor_append_update_fail: {factor_append_success}/{factor_update_success}/{factor_fail}",
        f"- technical_append_update_fail: {tech_append_success}/{tech_update_success}/{tech_fail}",
        f"- backup_dir: {backup_dir}",
        f"- restore_script: {restore_script}",
        "",
        "R25D modified only the official factor pack and technical timing targets in apply mode.",
        "",
    ])
    write_text(root / OUT_REPORT, report)
    print(f"STATUS: {status}")
    print(f"MODE: {mode}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
