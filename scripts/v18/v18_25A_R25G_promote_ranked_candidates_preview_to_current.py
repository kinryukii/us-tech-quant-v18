from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRYRUN_OK = "OK_V18_25A_R25G_DRYRUN_PROMOTION_PLAN_READY"
STATUS_OK = "OK_V18_25A_R25G_RANKED_CANDIDATES_PROMOTED_TO_CURRENT"
STATUS_PREVIEW_MISSING = "WARN_V18_25A_R25G_PREVIEW_MISSING"
STATUS_PREVIEW_FAILED = "WARN_V18_25A_R25G_PREVIEW_VALIDATION_FAILED"
STATUS_SCHEMA = "WARN_V18_25A_R25G_SCHEMA_REVIEW_NEEDED"
STATUS_NOT_AUTH = "WARN_V18_25A_R25G_PROMOTION_NOT_AUTHORIZED"
STATUS_POST_FAILED = "WARN_V18_25A_R25G_POST_PROMOTION_VALIDATION_FAILURE"

MODE_DRYRUN = "DRYRUN_PROMOTE_RANKED_CANDIDATES_PREVIEW_TO_CURRENT"
MODE_APPLY = "APPLY_PROMOTE_RANKED_CANDIDATES_PREVIEW_TO_CURRENT"
EXPECTED_PREVIEW_ROWS = 250
EXPECTED_TARGETS = 93

PREVIEW = "outputs/v18/candidates/V18_25A_R25F_CURRENT_RANKED_CANDIDATES_PREVIEW.csv"
TARGET_IMPACT = "outputs/v18/post_merge_validation/V18_25A_R25F_CURRENT_RANKED_CANDIDATE_TARGET_IMPACT.csv"
TRUST = "outputs/v18/post_merge_validation/V18_25A_R25F_CURRENT_TRUST_CLASSIFICATION_AFTER_REFRESH.csv"
R25F_READ_FIRST = "outputs/v18/ops/V18_25A_R25F_READ_FIRST.txt"
CURRENT = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
PRICE_CACHE = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
FACTOR_CURRENT = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_CURRENT = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"

OUT_PLAN = "outputs/v18/candidates/V18_25A_R25G_CURRENT_PROMOTION_PLAN.csv"
OUT_RESULT = "outputs/v18/candidates/V18_25A_R25G_CURRENT_PROMOTION_RESULT.csv"
OUT_POST = "outputs/v18/candidates/V18_25A_R25G_CURRENT_POST_PROMOTION_VALIDATION.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R25G_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R25G_CURRENT_PROMOTE_RANKED_CANDIDATES_REPORT.md"

PLAN_FIELDS = [
    "plan_item", "status", "expected_value", "actual_value", "promotion_allowed", "reason",
]
RESULT_FIELDS = [
    "result_item", "status", "path", "details",
]
POST_FIELDS = [
    "validation_item", "status", "expected_value", "actual_value", "reason",
]
MANIFEST_FIELDS = [
    "backup_item", "source_path", "backup_path", "required", "created", "size_bytes", "notes",
]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "RUN_ID", "PREVIEW_PATH", "CURRENT_CANDIDATES_PATH", "BACKUP_DIR", "RESTORE_SCRIPT_PATH",
    "PREVIEW_ROW_COUNT", "CURRENT_PRE_ROW_COUNT", "CURRENT_POST_ROW_COUNT", "R25F_TARGET_EXPECTED_COUNT",
    "R25F_TARGET_PRESENT_IN_PREVIEW_COUNT", "R25F_TARGET_PRESENT_IN_CURRENT_AFTER_COUNT",
    "PREVIEW_DUPLICATE_TICKER_COUNT", "CURRENT_DUPLICATE_TICKER_COUNT_AFTER",
    "PREVIEW_SCHEMA_COMPATIBLE_WITH_CURRENT", "PROMOTION_ALLOWED", "PROMOTION_APPLIED", "BACKUP_CREATED",
    "RESTORE_SCRIPT_CREATED", "CURRENT_RANKED_CANDIDATES_MODIFIED", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE",
    "AUTO_SELL", "EXTERNAL_FETCH_EXECUTED", "BACKTEST_EXECUTED", "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED", "FACTOR_PACK_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "TIER_FILES_MODIFIED",
    "OFFICIAL_DECISION_MODIFIED", "VALIDATION_FAIL_COUNT", "FORBIDDEN_MODIFIED", "NEXT_RECOMMENDED_STEP",
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


def read_first(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    out: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def is_true(value: object) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "Y", "1", "PASS", "SUCCESS"}


def to_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip().replace(",", "")
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


def ticker_counts(rows: List[Dict[str, str]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker:
            counts[ticker] = counts.get(ticker, 0) + 1
    return counts


def duplicate_ticker_count(rows: List[Dict[str, str]]) -> int:
    return sum(1 for count in ticker_counts(rows).values() if count > 1)


def invalid_ticker_count(rows: List[Dict[str, str]]) -> int:
    invalid = 0
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker in {"", "TICKER", "TICKERS", "SYMBOL", "SYMBOLS", "NAN", "NULL"}:
            invalid += 1
        elif re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,14}", ticker) is None:
            invalid += 1
    return invalid


def score_column(fields: Sequence[str]) -> str:
    lower = {field.lower(): field for field in fields}
    for candidate in ["composite_candidate_score", "candidate_score", "score"]:
        if candidate in lower:
            return lower[candidate]
    return ""


def create_backup(root: Path, backup_dir: Path, current_exists: bool) -> Tuple[bool, bool, List[Dict[str, object]], Path]:
    ensure_dir(backup_dir)
    current_src = root / CURRENT
    backup_file = backup_dir / current_src.name
    rows: List[Dict[str, object]] = []
    if current_exists:
        shutil.copy2(current_src, backup_file)
        rows.append({
            "backup_item": "current_ranked_candidates",
            "source_path": CURRENT,
            "backup_path": str(backup_file),
            "required": "TRUE",
            "created": str(backup_file.exists()).upper(),
            "size_bytes": backup_file.stat().st_size if backup_file.exists() else 0,
            "notes": "",
        })
    else:
        rows.append({
            "backup_item": "NEW_TARGET_FILE",
            "source_path": CURRENT,
            "backup_path": "",
            "required": "TRUE",
            "created": "TRUE",
            "size_bytes": 0,
            "notes": "Current ranked candidates did not exist before R25G.",
        })
    restore = backup_dir / "RESTORE_V18_25A_R25G_RANKED_CANDIDATES.ps1"
    current_win = CURRENT.replace("/", "\\")
    if current_exists:
        restore_body = f"""[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$backupDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Copy-Item -LiteralPath (Join-Path $backupDir "{current_src.name}") -Destination (Join-Path $Root "{current_win}") -Force
Write-Host "Restored V18.25A-R25G ranked candidates backup."
"""
    else:
        restore_body = f"""[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$target = Join-Path $Root "{current_win}"
if (Test-Path $target) {{ Remove-Item -LiteralPath $target -Force }}
Write-Host "Removed V18.25A-R25G new ranked candidates target file."
"""
    write_text(restore, restore_body)
    readme = backup_dir / "README_RESTORE_V18_25A_R25G.txt"
    write_text(readme, "\n".join([
        "V18.25A-R25G restore package",
        "",
        f"Target: {CURRENT}",
        "Run RESTORE_V18_25A_R25G_RANKED_CANDIDATES.ps1 from PowerShell to restore the pre-promotion state.",
        "",
    ]))
    rows.extend([
        {"backup_item": "restore_script", "source_path": "", "backup_path": str(restore), "required": "TRUE", "created": str(restore.exists()).upper(), "size_bytes": restore.stat().st_size if restore.exists() else 0, "notes": ""},
        {"backup_item": "restore_readme", "source_path": "", "backup_path": str(readme), "required": "TRUE", "created": str(readme.exists()).upper(), "size_bytes": readme.stat().st_size if readme.exists() else 0, "notes": ""},
    ])
    manifest = backup_dir / "MANIFEST.csv"
    write_csv(manifest, rows, MANIFEST_FIELDS)
    rows.append({"backup_item": "manifest", "source_path": "", "backup_path": str(manifest), "required": "TRUE", "created": str(manifest.exists()).upper(), "size_bytes": manifest.stat().st_size if manifest.exists() else 0, "notes": ""})
    backup_ok = (backup_file.exists() if current_exists else True) and manifest.exists()
    restore_ok = restore.exists()
    return backup_ok, restore_ok, rows, restore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--require-r25f-preview-valid", action="store_true", default=True)
    parser.add_argument("--allow-promotion", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R25G_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    mode = MODE_DRYRUN if args.dry_run else MODE_APPLY
    backup_dir = root / "archive/v18/candidate_backups" / run_id
    restore_script = backup_dir / "RESTORE_V18_25A_R25G_RANKED_CANDIDATES.ps1"
    before = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": file_sig(root / FACTOR_CURRENT),
        "technical": file_sig(root / TECH_CURRENT),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
        "current_candidates": file_sig(root / CURRENT),
    }

    preview_rows, preview_fields = read_csv(root / PREVIEW)
    impact_rows, _ = read_csv(root / TARGET_IMPACT)
    trust_rows, _ = read_csv(root / TRUST)
    current_rows, current_fields = read_csv(root / CURRENT)
    r25f = read_first(root / R25F_READ_FIRST)
    current_exists = (root / CURRENT).exists()

    preview_missing = not (root / PREVIEW).exists()
    preview_row_count = len(preview_rows)
    current_pre_count = len(current_rows)
    target_present_preview = sum(1 for row in impact_rows if is_true(row.get("target_in_regenerated_rank_preview")))
    official_allowed = sum(1 for row in trust_rows if is_true(row.get("official_rank_allowed_after_refresh")))
    blockers = int(r25f.get("TARGETS_STILL_DOWNSTREAM_BLOCKED_COUNT", "0") or "0") if r25f else 0
    preview_dupes = duplicate_ticker_count(preview_rows)
    invalid_tickers = invalid_ticker_count(preview_rows)
    score_col = score_column(preview_fields)
    score_missing = sum(1 for row in preview_rows if to_float(row.get(score_col)) is None) if score_col else len(preview_rows)
    has_rank = "rank" in preview_fields
    has_ticker = "ticker" in preview_fields
    schema_compatible = (not current_exists) or (list(preview_fields) == list(current_fields))
    preview_valid = (
        not preview_missing
        and preview_row_count == EXPECTED_PREVIEW_ROWS
        and target_present_preview == EXPECTED_TARGETS
        and blockers == 0
        and official_allowed == EXPECTED_TARGETS
        and has_ticker
        and has_rank
        and bool(score_col)
        and preview_dupes == 0
        and invalid_tickers == 0
        and score_missing == 0
    )
    promotion_allowed = preview_valid and schema_compatible and (args.dry_run or args.allow_promotion)

    plan_rows = [
        {"plan_item": "preview_file_exists", "status": "PASS" if not preview_missing else "FAIL", "expected_value": "TRUE", "actual_value": str(not preview_missing).upper(), "promotion_allowed": str(promotion_allowed).upper(), "reason": ""},
        {"plan_item": "preview_row_count", "status": "PASS" if preview_row_count == EXPECTED_PREVIEW_ROWS else "FAIL", "expected_value": EXPECTED_PREVIEW_ROWS, "actual_value": preview_row_count, "promotion_allowed": str(promotion_allowed).upper(), "reason": ""},
        {"plan_item": "r25f_targets_present_in_preview", "status": "PASS" if target_present_preview == EXPECTED_TARGETS else "FAIL", "expected_value": EXPECTED_TARGETS, "actual_value": target_present_preview, "promotion_allowed": str(promotion_allowed).upper(), "reason": ""},
        {"plan_item": "r25f_downstream_blockers", "status": "PASS" if blockers == 0 else "FAIL", "expected_value": 0, "actual_value": blockers, "promotion_allowed": str(promotion_allowed).upper(), "reason": ""},
        {"plan_item": "r25f_official_rank_allowed", "status": "PASS" if official_allowed == EXPECTED_TARGETS else "FAIL", "expected_value": EXPECTED_TARGETS, "actual_value": official_allowed, "promotion_allowed": str(promotion_allowed).upper(), "reason": ""},
        {"plan_item": "preview_schema_compatible_with_current", "status": "PASS" if schema_compatible else "FAIL", "expected_value": "TRUE", "actual_value": str(schema_compatible).upper(), "promotion_allowed": str(promotion_allowed).upper(), "reason": ""},
        {"plan_item": "preview_duplicate_tickers", "status": "PASS" if preview_dupes == 0 else "FAIL", "expected_value": 0, "actual_value": preview_dupes, "promotion_allowed": str(promotion_allowed).upper(), "reason": ""},
        {"plan_item": "preview_score_numeric", "status": "PASS" if score_missing == 0 else "FAIL", "expected_value": 0, "actual_value": score_missing, "promotion_allowed": str(promotion_allowed).upper(), "reason": ""},
    ]

    backup_created = False
    restore_created = False
    promotion_applied = False
    result_rows: List[Dict[str, object]] = []
    backup_manifest_rows: List[Dict[str, object]] = []
    if not args.dry_run and promotion_allowed:
        backup_created, restore_created, backup_manifest_rows, restore_script = create_backup(root, backup_dir, current_exists)
        if backup_created and restore_created:
            shutil.copy2(root / PREVIEW, root / CURRENT)
            promotion_applied = True
            result_rows.append({"result_item": "promote_preview_to_current", "status": "PASS", "path": CURRENT, "details": "Preview copied to current ranked candidates."})
        else:
            result_rows.append({"result_item": "backup_before_promotion", "status": "FAIL", "path": str(backup_dir), "details": "Backup or restore script incomplete."})
    elif args.dry_run:
        result_rows.append({"result_item": "dryrun_no_promotion", "status": "PASS", "path": CURRENT, "details": "DryRun did not modify current ranked candidates."})
    else:
        result_rows.append({"result_item": "promotion_not_applied", "status": "FAIL", "path": CURRENT, "details": "Promotion not authorized or validation failed."})

    write_csv(root / OUT_PLAN, plan_rows, PLAN_FIELDS)
    write_csv(root / OUT_RESULT, result_rows, RESULT_FIELDS)

    post_rows, post_fields = read_csv(root / CURRENT)
    post_count = len(post_rows)
    current_counts_after = ticker_counts(post_rows)
    target_tickers = {norm_ticker(row.get("ticker")) for row in impact_rows if norm_ticker(row.get("ticker"))}
    targets_in_current_after = sum(1 for ticker in target_tickers if ticker in current_counts_after)
    current_dupes_after = duplicate_ticker_count(post_rows)
    post_score_col = score_column(post_fields)
    post_valid = (
        (root / CURRENT).exists()
        and post_count == preview_row_count
        and targets_in_current_after == EXPECTED_TARGETS
        and current_dupes_after == 0
        and "ticker" in post_fields
        and "rank" in post_fields
        and bool(post_score_col)
    )
    post_validation_rows = [
        {"validation_item": "current_ranked_candidates_exists", "status": "PASS" if (root / CURRENT).exists() else "FAIL", "expected_value": "TRUE", "actual_value": str((root / CURRENT).exists()).upper(), "reason": ""},
        {"validation_item": "current_row_count_equals_preview", "status": "PASS" if post_count == preview_row_count else "FAIL", "expected_value": preview_row_count, "actual_value": post_count, "reason": ""},
        {"validation_item": "r25f_targets_present_after", "status": "PASS" if targets_in_current_after == EXPECTED_TARGETS else "FAIL", "expected_value": EXPECTED_TARGETS, "actual_value": targets_in_current_after, "reason": ""},
        {"validation_item": "current_duplicate_tickers_after", "status": "PASS" if current_dupes_after == 0 else "FAIL", "expected_value": 0, "actual_value": current_dupes_after, "reason": ""},
        {"validation_item": "current_rank_score_columns_after", "status": "PASS" if "rank" in post_fields and bool(post_score_col) else "FAIL", "expected_value": "rank+score", "actual_value": f"rank={'rank' in post_fields};score={post_score_col}", "reason": ""},
    ]
    write_csv(root / OUT_POST, post_validation_rows, POST_FIELDS)

    after = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": file_sig(root / FACTOR_CURRENT),
        "technical": file_sig(root / TECH_CURRENT),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
        "current_candidates": file_sig(root / CURRENT),
    }
    mods = {key: before[key] != after[key] for key in before}
    current_modified = mods["current_candidates"]
    forbidden = mods["price"] or mods["ledger"] or mods["factor"] or mods["technical"] or mods["tier"] or mods["decision"] or (current_modified and args.dry_run) or (current_modified and not promotion_applied)

    status = STATUS_DRYRUN_OK if args.dry_run else STATUS_OK
    if preview_missing:
        status = STATUS_PREVIEW_MISSING
    elif not preview_valid and args.require_r25f_preview_valid:
        status = STATUS_PREVIEW_FAILED
    elif not schema_compatible:
        status = STATUS_SCHEMA
    elif not args.dry_run and not args.allow_promotion:
        status = STATUS_NOT_AUTH
    elif not args.dry_run and not post_valid:
        status = STATUS_POST_FAILED

    validation_fail_count = int(status not in {STATUS_DRYRUN_OK, STATUS_OK} or forbidden)
    values = {
        "STATUS": status,
        "MODE": mode,
        "RUN_ID": run_id,
        "PREVIEW_PATH": PREVIEW,
        "CURRENT_CANDIDATES_PATH": CURRENT,
        "BACKUP_DIR": str(backup_dir),
        "RESTORE_SCRIPT_PATH": str(restore_script),
        "PREVIEW_ROW_COUNT": preview_row_count,
        "CURRENT_PRE_ROW_COUNT": current_pre_count,
        "CURRENT_POST_ROW_COUNT": post_count,
        "R25F_TARGET_EXPECTED_COUNT": EXPECTED_TARGETS,
        "R25F_TARGET_PRESENT_IN_PREVIEW_COUNT": target_present_preview,
        "R25F_TARGET_PRESENT_IN_CURRENT_AFTER_COUNT": targets_in_current_after,
        "PREVIEW_DUPLICATE_TICKER_COUNT": preview_dupes,
        "CURRENT_DUPLICATE_TICKER_COUNT_AFTER": current_dupes_after,
        "PREVIEW_SCHEMA_COMPATIBLE_WITH_CURRENT": str(schema_compatible).upper(),
        "PROMOTION_ALLOWED": str(promotion_allowed).upper(),
        "PROMOTION_APPLIED": str(promotion_applied).upper(),
        "BACKUP_CREATED": str(backup_created).upper(),
        "RESTORE_SCRIPT_CREATED": str(restore_created).upper(),
        "CURRENT_RANKED_CANDIDATES_MODIFIED": str(current_modified).upper(),
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "PRICE_CACHE_MODIFIED": str(mods["price"]).upper(),
        "ROLLING_LEDGER_MODIFIED": str(mods["ledger"]).upper(),
        "FACTOR_PACK_MODIFIED": str(mods["factor"]).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(mods["technical"]).upper(),
        "TIER_FILES_MODIFIED": str(mods["tier"]).upper(),
        "OFFICIAL_DECISION_MODIFIED": str(mods["decision"]).upper(),
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden).upper(),
        "NEXT_RECOMMENDED_STEP": "R26: Factor effectiveness validation / forward-test integration readiness, using the updated current ranked candidates and R21 signal freeze ledger.",
    }
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    report = "\n".join([
        "# V18.25A R25G Promote Ranked Candidates Preview Report",
        "",
        f"STATUS: {status}",
        f"MODE: {mode}",
        f"RUN_ID: {run_id}",
        "",
        f"- preview_row_count: {preview_row_count}",
        f"- current_rows_pre_post: {current_pre_count} -> {post_count}",
        f"- r25f_targets_present_in_preview: {target_present_preview}",
        f"- r25f_targets_present_after: {targets_in_current_after}",
        f"- backup_dir: {backup_dir}",
        f"- restore_script: {restore_script}",
        "",
        "R25G promotes only the validated ranked candidates preview to the current ranked candidates file when explicitly authorized.",
        "",
    ])
    write_text(root / OUT_REPORT, report)
    print(f"STATUS: {status}")
    print(f"MODE: {mode}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
