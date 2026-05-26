from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_DRYRUN = "OK_V18_25A_R27K_DRYRUN_RANKED_CANDIDATES_PROMOTION_PLAN_READY"
STATUS_APPLY_OK = "OK_V18_25A_R27K_RANKED_CANDIDATES_PROMOTION_READY"
STATUS_APPLY_BLOCKED = "WARN_V18_25A_R27K_APPLY_BLOCKED"
STATUS_POST_REVIEW = "WARN_V18_25A_R27K_POST_PROMOTION_VALIDATION_REVIEW_NEEDED"
STATUS_FORBIDDEN = "FAIL_V18_25A_R27K_FORBIDDEN_MODIFIED"

MODE_DRYRUN = "DRYRUN_RANKED_CANDIDATES_PROMOTION_PLAN_ONLY"
MODE_APPLY = "APPLY_RANKED_CANDIDATES_PROMOTION_WITH_BACKUP"

EXPECTED_R27J_STATUS = "OK_V18_25A_R27J_RANKED_CANDIDATES_PREVIEW_READY"
TARGET_TICKERS = ["RDDT", "TLN"]
TARGET_SET = set(TARGET_TICKERS)

R27J_READ_FIRST = "outputs/v18/ops/V18_25A_R27J_READ_FIRST.txt"
R27J_PREVIEW = "outputs/v18/candidates/V18_25A_R27J_CURRENT_RANKED_CANDIDATES_PREVIEW.csv"
R27J_VALIDATION = "outputs/v18/candidates/V18_25A_R27J_CURRENT_RANKED_CANDIDATES_PREVIEW_VALIDATION.csv"
R27J_PROMOTION_PLAN = "outputs/v18/candidates/V18_25A_R27J_CURRENT_PROMOTION_PLAN.csv"
CURRENT = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
FACTOR_PACK = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_TIMING = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
PRICE_CACHE_DIR = "state/v18/price_cache"
ROLLING_LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
OFFICIAL_DECISIONS_DIR = "outputs/v18/official_decisions"
BACKUP_ROOT = "archive/v18/candidate_promotion_backups"

OUT_DIR = "outputs/v18/candidates"
OUT_PLAN = f"{OUT_DIR}/V18_25A_R27K_CURRENT_DRYRUN_OR_APPLY_PLAN.csv"
OUT_RESULT = f"{OUT_DIR}/V18_25A_R27K_CURRENT_PROMOTION_RESULT.csv"
OUT_POST = f"{OUT_DIR}/V18_25A_R27K_CURRENT_POST_PROMOTION_VALIDATION.csv"
OUT_BACKUP = f"{OUT_DIR}/V18_25A_R27K_CURRENT_BACKUP_MANIFEST.csv"
OUT_SUMMARY = f"{OUT_DIR}/V18_25A_R27K_CURRENT_SUMMARY.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R27K_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R27K_CURRENT_RANKED_CANDIDATES_PROMOTION_REPORT.md"

PLAN_FIELDS = [
    "plan_item",
    "status",
    "expected_value",
    "actual_value",
    "promotion_allowed",
    "reason",
]
RESULT_FIELDS = [
    "result_item",
    "status",
    "path",
    "details",
]
POST_FIELDS = [
    "validation_item",
    "status",
    "expected_value",
    "actual_value",
    "reason",
]
BACKUP_FIELDS = [
    "backup_item",
    "source_path",
    "backup_path",
    "backup_status",
    "notes",
]
SUMMARY_FIELDS = ["metric", "value", "expected", "status", "notes"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R27J_STATUS",
    "APPLY_REQUESTED",
    "TARGET_TICKER_COUNT",
    "TARGET_TICKERS",
    "EXPECTED_TICKER_MATCH",
    "CURRENT_ROW_COUNT_BEFORE",
    "PREVIEW_ROW_COUNT",
    "BACKUP_CREATED",
    "BACKUP_DIR",
    "RESTORE_SCRIPT_CREATED",
    "PROMOTION_ATTEMPT_COUNT",
    "PROMOTION_SUCCESS",
    "PROMOTION_FAIL_COUNT",
    "CURRENT_ROW_COUNT_AFTER",
    "TARGETS_PRESENT_AFTER_COUNT",
    "DUPLICATE_TICKER_COUNT_AFTER",
    "EXISTING_CURRENT_TICKERS_PRESERVED",
    "TARGET_SCORE_PRESENT_COUNT_AFTER",
    "CANDIDATES_CURRENT_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
    "SIGNAL_FREEZE_EXECUTED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def read_first_value(path: Path, key: str) -> str:
    prefix = f"{key}:"
    for line in read_text(path).splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def non_null(value: object) -> bool:
    return str(value or "").strip() not in {"", "nan", "NaN", "None", "NULL"}


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def ticker_counts(rows: Sequence[Dict[str, str]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker:
            counts[ticker] = counts.get(ticker, 0) + 1
    return counts


def duplicate_ticker_count(rows: Sequence[Dict[str, str]]) -> int:
    return sum(max(0, count - 1) for count in ticker_counts(rows).values())


def target_present_count(rows: Sequence[Dict[str, str]], tickers: Sequence[str]) -> int:
    counts = ticker_counts(rows)
    return sum(1 for ticker in tickers if counts.get(ticker, 0) == 1)


def target_score_count(rows: Sequence[Dict[str, str]], tickers: Sequence[str]) -> int:
    counts = 0
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker in tickers and non_null(row.get("composite_candidate_score")):
            counts += 1
    return counts


def row_without_rank(row: Dict[str, str]) -> Dict[str, str]:
    return {key: value for key, value in row.items() if key != "rank"}


def current_preserved(current_rows: Sequence[Dict[str, str]], preview_rows: Sequence[Dict[str, str]]) -> bool:
    preview_by = {norm_ticker(row.get("ticker")): row for row in preview_rows}
    for row in current_rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker not in preview_by:
            return False
        if row_without_rank(row) != row_without_rank(preview_by[ticker]):
            return False
    return True


def validate_preconditions(root: Path, current_rows: List[Dict[str, str]], current_fields: Sequence[str], preview_rows: List[Dict[str, str]], preview_fields: Sequence[str]) -> Tuple[List[str], List[Dict[str, object]], Dict[str, object]]:
    blockers: List[str] = []
    plan_rows: List[Dict[str, object]] = []
    r27j_status = read_first_value(root / R27J_READ_FIRST, "STATUS")
    target_match = read_first_value(root / R27J_READ_FIRST, "TARGET_TICKERS") == "RDDT,TLN"
    current_count = len(current_rows)
    preview_count = len(preview_rows)
    current_counts = ticker_counts(current_rows)
    preview_counts = ticker_counts(preview_rows)
    preview_dupes = duplicate_ticker_count(preview_rows)
    schema_match = list(current_fields) == list(preview_fields)
    preserved = current_preserved(current_rows, preview_rows)
    target_scores = target_score_count(preview_rows, TARGET_TICKERS)
    targets_absent_current = all(current_counts.get(ticker, 0) == 0 for ticker in TARGET_TICKERS)
    targets_once_preview = all(preview_counts.get(ticker, 0) == 1 for ticker in TARGET_TICKERS)

    checks = [
        ("r27j_status", r27j_status, EXPECTED_R27J_STATUS, r27j_status == EXPECTED_R27J_STATUS, "R27J status must be OK."),
        ("r27j_promotion_recommended", read_first_value(root / R27J_READ_FIRST, "PROMOTION_TO_CURRENT_RECOMMENDED"), "TRUE", read_first_value(root / R27J_READ_FIRST, "PROMOTION_TO_CURRENT_RECOMMENDED") == "TRUE", "R27J must recommend promotion."),
        ("target_ticker_match", str(target_match).upper(), "TRUE", target_match, "Targets must be exactly RDDT/TLN."),
        ("current_row_count_before", current_count, 250, current_count == 250, "Current count changed from expected baseline; preview preservation is still validated."),
        ("preview_row_count", preview_count, 252, preview_count == 252, "Preview must have 252 rows."),
        ("targets_absent_current", str(targets_absent_current).upper(), "TRUE", targets_absent_current, "Targets must be absent before promotion."),
        ("targets_once_preview", str(targets_once_preview).upper(), "TRUE", targets_once_preview, "Targets must be present exactly once in preview."),
        ("preview_schema_match", str(schema_match).upper(), "TRUE", schema_match, "Preview schema must match current schema."),
        ("preview_preserves_current_tickers", str(preserved).upper(), "TRUE", preserved, "Preview must preserve existing current tickers."),
        ("preview_duplicate_ticker_count", preview_dupes, 0, preview_dupes == 0, "Preview must have no duplicate tickers."),
        ("target_score_present_count", target_scores, 2, target_scores == 2, "Both targets must have scores."),
        ("rank_recomputed", read_first_value(root / R27J_READ_FIRST, "RANK_RECOMPUTED"), "TRUE", read_first_value(root / R27J_READ_FIRST, "RANK_RECOMPUTED") == "TRUE", "Preview ranks must be recomputed."),
        ("r27j_forbidden_modified", read_first_value(root / R27J_READ_FIRST, "FORBIDDEN_MODIFIED"), "FALSE", read_first_value(root / R27J_READ_FIRST, "FORBIDDEN_MODIFIED") == "FALSE", "R27J guardrail must be clean."),
    ]
    for item, actual, expected, ok, reason in checks:
        plan_rows.append(
            {
                "plan_item": item,
                "status": "PASS" if ok else "WARN",
                "expected_value": expected,
                "actual_value": actual,
                "promotion_allowed": str(ok).upper(),
                "reason": "" if ok else reason,
            }
        )
        if not ok and item != "current_row_count_before":
            blockers.append(reason)
    metrics = {
        "R27J_STATUS": r27j_status or "MISSING",
        "EXPECTED_TICKER_MATCH": target_match,
        "CURRENT_ROW_COUNT_BEFORE": current_count,
        "PREVIEW_ROW_COUNT": preview_count,
        "PREVIEW_DUPLICATE_COUNT": preview_dupes,
        "EXISTING_PRESERVED": preserved,
        "TARGET_SCORE_COUNT": target_scores,
    }
    return blockers, plan_rows, metrics


def create_backup(root: Path, run_stamp: str) -> Tuple[Path, List[Dict[str, object]], bool]:
    backup_dir = root / BACKUP_ROOT / f"V18_25A_R27K_{run_stamp}"
    ensure_dir(backup_dir)
    source = root / CURRENT
    backup = backup_dir / source.name
    shutil.copy2(source, backup)
    rows = [
        {
            "backup_item": "CURRENT_RANKED_CANDIDATES",
            "source_path": source.as_posix(),
            "backup_path": backup.as_posix(),
            "backup_status": "BACKED_UP",
            "notes": "Pre-R27K current ranked candidates.",
        }
    ]
    write_csv(backup_dir / "MANIFEST.csv", rows, BACKUP_FIELDS)
    restore = backup_dir / "RESTORE_V18_25A_R27K_RANKED_CANDIDATES_PROMOTION.ps1"
    restore_text = """[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$manifestPath = Join-Path $PSScriptRoot "MANIFEST.csv"
$manifest = Import-Csv $manifestPath
foreach ($row in $manifest) {
    if ($row.backup_item -eq "CURRENT_RANKED_CANDIDATES" -and $row.backup_status -eq "BACKED_UP") {
        Copy-Item -Path $row.backup_path -Destination $row.source_path -Force
        Write-Host "Restored current ranked candidates: $($row.source_path)"
    }
}
"""
    write_text(restore, restore_text)
    write_text(
        backup_dir / "README_V18_25A_R27K_RESTORE.txt",
        "Run RESTORE_V18_25A_R27K_RANKED_CANDIDATES_PROMOTION.ps1 to restore V18_CURRENT_RANKED_CANDIDATES.csv to its pre-R27K state.\n",
    )
    return backup_dir, rows, restore.exists()


def post_validate(root: Path, pre_fields: Sequence[str], pre_current_rows: Sequence[Dict[str, str]]) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    rows, fields = read_csv(root / CURRENT)
    row_count = len(rows)
    target_count = target_present_count(rows, TARGET_TICKERS)
    dupe_count = duplicate_ticker_count(rows)
    schema_ok = list(fields) == list(pre_fields)
    preserved = current_preserved(pre_current_rows, rows)
    target_scores = target_score_count(rows, TARGET_TICKERS)
    checks = [
        ("current_row_count_after", row_count, 252, row_count == 252, ""),
        ("targets_present_after_count", target_count, 2, target_count == 2, ""),
        ("duplicate_ticker_count_after", dupe_count, 0, dupe_count == 0, ""),
        ("schema_still_matches_pre_apply", str(schema_ok).upper(), "TRUE", schema_ok, ""),
        ("existing_current_tickers_preserved", str(preserved).upper(), "TRUE", preserved, ""),
        ("target_score_present_count_after", target_scores, 2, target_scores == 2, ""),
    ]
    out_rows = [
        {
            "validation_item": item,
            "status": "PASS" if ok else "FAIL",
            "expected_value": expected,
            "actual_value": actual,
            "reason": reason,
        }
        for item, actual, expected, ok, reason in checks
    ]
    metrics = {
        "CURRENT_ROW_COUNT_AFTER": row_count,
        "TARGETS_PRESENT_AFTER_COUNT": target_count,
        "DUPLICATE_TICKER_COUNT_AFTER": dupe_count,
        "EXISTING_CURRENT_TICKERS_PRESERVED": preserved,
        "TARGET_SCORE_PRESENT_COUNT_AFTER": target_scores,
        "POST_FAIL_COUNT": sum(1 for _, _, _, ok, _ in checks if not ok),
    }
    return out_rows, metrics


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object], plan_rows: Sequence[Dict[str, object]], post_rows: Sequence[Dict[str, object]]) -> str:
    plan_text = "\n".join(f"- {row['plan_item']}: {row['status']}" for row in plan_rows)
    post_text = "\n".join(f"- {row['validation_item']}: {row['status']}" for row in post_rows)
    return "\n".join(
        [
            "# V18.25A-R27K Ranked Candidates Promotion",
            "",
            f"- STATUS: {values['STATUS']}",
            f"- MODE: {values['MODE']}",
            f"- RUN_ID: {values['RUN_ID']}",
            f"- APPLY_REQUESTED: {values['APPLY_REQUESTED']}",
            "",
            "## Plan",
            "",
            plan_text if plan_text else "- None.",
            "",
            "## Post-Promotion Validation",
            "",
            post_text if post_text else "- Not run in dry-run mode.",
            "",
            "## Backup",
            "",
            f"- BACKUP_CREATED: {values['BACKUP_CREATED']}",
            f"- BACKUP_DIR: {values['BACKUP_DIR']}",
            f"- RESTORE_SCRIPT_CREATED: {values['RESTORE_SCRIPT_CREATED']}",
            "",
            "## Guardrails",
            "",
            f"- CANDIDATES_CURRENT_MODIFIED: {values['CANDIDATES_CURRENT_MODIFIED']}",
            f"- FACTOR_PACK_MODIFIED: {values['FACTOR_PACK_MODIFIED']}",
            f"- TECHNICAL_TIMING_MODIFIED: {values['TECHNICAL_TIMING_MODIFIED']}",
            f"- PRICE_CACHE_MODIFIED: {values['PRICE_CACHE_MODIFIED']}",
            f"- ROLLING_LEDGER_MODIFIED: {values['ROLLING_LEDGER_MODIFIED']}",
            f"- FORBIDDEN_MODIFIED: {values['FORBIDDEN_MODIFIED']}",
            "",
            f"NEXT_RECOMMENDED_STEP: {values['NEXT_RECOMMENDED_STEP']}",
            "",
        ]
    )


def summary_row(metric: str, value: object, expected: object, ok: bool, notes: str = "") -> Dict[str, object]:
    return {"metric": metric, "value": value, "expected": expected, "status": "OK" if ok else "WARN", "notes": notes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"V18_25A_R27K_{run_stamp}"
    mode = MODE_APPLY if args.apply else MODE_DRYRUN

    current_before_sig = file_sig(root / CURRENT)
    factor_before = file_sig(root / FACTOR_PACK)
    tech_before = file_sig(root / TECH_TIMING)
    price_before = tree_sig(root / PRICE_CACHE_DIR)
    ledger_before = file_sig(root / ROLLING_LEDGER)
    official_before = tree_sig(root / OFFICIAL_DECISIONS_DIR)

    current_rows, current_fields = read_csv(root / CURRENT)
    preview_rows, preview_fields = read_csv(root / R27J_PREVIEW)
    if not current_rows or not current_fields:
        preview_fields_for_plan = preview_fields
    else:
        preview_fields_for_plan = preview_fields
    blockers, plan_rows, metrics = validate_preconditions(root, current_rows, current_fields, preview_rows, preview_fields_for_plan)

    backup_dir = Path("")
    backup_rows: List[Dict[str, object]] = []
    backup_created = False
    restore_created = False
    result_rows: List[Dict[str, object]] = []
    post_rows: List[Dict[str, object]] = []
    post_metrics: Dict[str, object] = {
        "CURRENT_ROW_COUNT_AFTER": len(current_rows),
        "TARGETS_PRESENT_AFTER_COUNT": target_present_count(current_rows, TARGET_TICKERS),
        "DUPLICATE_TICKER_COUNT_AFTER": duplicate_ticker_count(current_rows),
        "EXISTING_CURRENT_TICKERS_PRESERVED": True,
        "TARGET_SCORE_PRESENT_COUNT_AFTER": target_score_count(current_rows, TARGET_TICKERS),
        "POST_FAIL_COUNT": 0,
    }

    status = STATUS_DRYRUN if not blockers else STATUS_APPLY_BLOCKED
    if args.apply:
        if blockers:
            status = STATUS_APPLY_BLOCKED
        else:
            try:
                backup_dir, backup_rows, restore_created = create_backup(root, run_stamp)
                backup_created = True
            except Exception as exc:
                blockers.append(f"backup_creation_failed: {type(exc).__name__}: {exc}")
                status = STATUS_APPLY_BLOCKED
            else:
                try:
                    shutil.copy2(root / R27J_PREVIEW, root / CURRENT)
                    result_rows.append(
                        {
                            "result_item": "promote_preview_to_current",
                            "status": "PASS",
                            "path": CURRENT,
                            "details": "R27J preview copied to current ranked candidates.",
                        }
                    )
                    post_rows, post_metrics = post_validate(root, current_fields, current_rows)
                    status = STATUS_APPLY_OK if post_metrics["POST_FAIL_COUNT"] == 0 else STATUS_POST_REVIEW
                except Exception as exc:
                    result_rows.append(
                        {
                            "result_item": "promote_preview_to_current",
                            "status": "FAIL",
                            "path": CURRENT,
                            "details": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    status = STATUS_POST_REVIEW
    else:
        result_rows.append(
            {
                "result_item": "dryrun_no_promotion",
                "status": "PASS" if not blockers else "WARN",
                "path": CURRENT,
                "details": "Dry-run did not modify current ranked candidates.",
            }
        )

    write_csv(root / OUT_PLAN, plan_rows, PLAN_FIELDS)
    write_csv(root / OUT_RESULT, result_rows, RESULT_FIELDS)
    write_csv(root / OUT_POST, post_rows, POST_FIELDS)
    write_csv(root / OUT_BACKUP, backup_rows, BACKUP_FIELDS)

    current_after_sig = file_sig(root / CURRENT)
    factor_modified = file_sig(root / FACTOR_PACK) != factor_before
    tech_modified = file_sig(root / TECH_TIMING) != tech_before
    price_modified = tree_sig(root / PRICE_CACHE_DIR) != price_before
    ledger_modified = file_sig(root / ROLLING_LEDGER) != ledger_before
    official_modified = tree_sig(root / OFFICIAL_DECISIONS_DIR) != official_before
    current_modified = current_after_sig != current_before_sig
    forbidden_modified = factor_modified or tech_modified or price_modified or ledger_modified or official_modified
    if args.apply:
        forbidden_modified = forbidden_modified or not current_modified
    else:
        forbidden_modified = forbidden_modified or current_modified
    if forbidden_modified:
        status = STATUS_FORBIDDEN

    promotion_attempt_count = 1 if args.apply and not blockers else 0
    promotion_success = args.apply and status == STATUS_APPLY_OK
    promotion_fail_count = 0 if (not args.apply or promotion_success) else 1
    validation_fail_count = 1 if status in {STATUS_FORBIDDEN, STATUS_POST_REVIEW} else 0

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": mode,
        "RUN_ID": run_id,
        "R27J_STATUS": metrics["R27J_STATUS"],
        "APPLY_REQUESTED": str(args.apply).upper(),
        "TARGET_TICKER_COUNT": len(TARGET_TICKERS),
        "TARGET_TICKERS": ",".join(TARGET_TICKERS),
        "EXPECTED_TICKER_MATCH": str(metrics["EXPECTED_TICKER_MATCH"]).upper(),
        "CURRENT_ROW_COUNT_BEFORE": metrics["CURRENT_ROW_COUNT_BEFORE"],
        "PREVIEW_ROW_COUNT": metrics["PREVIEW_ROW_COUNT"],
        "BACKUP_CREATED": str(backup_created).upper(),
        "BACKUP_DIR": backup_dir.as_posix() if backup_created else "",
        "RESTORE_SCRIPT_CREATED": str(restore_created).upper(),
        "PROMOTION_ATTEMPT_COUNT": promotion_attempt_count,
        "PROMOTION_SUCCESS": str(promotion_success).upper(),
        "PROMOTION_FAIL_COUNT": promotion_fail_count,
        "CURRENT_ROW_COUNT_AFTER": post_metrics["CURRENT_ROW_COUNT_AFTER"],
        "TARGETS_PRESENT_AFTER_COUNT": post_metrics["TARGETS_PRESENT_AFTER_COUNT"],
        "DUPLICATE_TICKER_COUNT_AFTER": post_metrics["DUPLICATE_TICKER_COUNT_AFTER"],
        "EXISTING_CURRENT_TICKERS_PRESERVED": str(post_metrics["EXISTING_CURRENT_TICKERS_PRESERVED"]).upper(),
        "TARGET_SCORE_PRESENT_COUNT_AFTER": post_metrics["TARGET_SCORE_PRESENT_COUNT_AFTER"],
        "CANDIDATES_CURRENT_MODIFIED": str(current_modified).upper(),
        "FACTOR_PACK_MODIFIED": str(factor_modified).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(tech_modified).upper(),
        "PRICE_CACHE_MODIFIED": str(price_modified).upper(),
        "ROLLING_LEDGER_MODIFIED": str(ledger_modified).upper(),
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "SIGNAL_FREEZE_EXECUTED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": "R27L_POST_PROMOTION_VALIDATION_AND_SIGNAL_FREEZE_READINESS_AUDIT",
    }

    summary_rows = [
        summary_row("R27J_STATUS", metrics["R27J_STATUS"], EXPECTED_R27J_STATUS, metrics["R27J_STATUS"] == EXPECTED_R27J_STATUS),
        summary_row("CURRENT_ROW_COUNT_BEFORE", metrics["CURRENT_ROW_COUNT_BEFORE"], 250, metrics["CURRENT_ROW_COUNT_BEFORE"] == 250),
        summary_row("PREVIEW_ROW_COUNT", metrics["PREVIEW_ROW_COUNT"], 252, metrics["PREVIEW_ROW_COUNT"] == 252),
        summary_row("CURRENT_ROW_COUNT_AFTER", post_metrics["CURRENT_ROW_COUNT_AFTER"], 252 if args.apply else metrics["CURRENT_ROW_COUNT_BEFORE"], True),
        summary_row("TARGETS_PRESENT_AFTER_COUNT", post_metrics["TARGETS_PRESENT_AFTER_COUNT"], 2 if args.apply else 0, True),
        summary_row("DUPLICATE_TICKER_COUNT_AFTER", post_metrics["DUPLICATE_TICKER_COUNT_AFTER"], 0, post_metrics["DUPLICATE_TICKER_COUNT_AFTER"] == 0),
        summary_row("FORBIDDEN_MODIFIED", str(forbidden_modified).upper(), "FALSE", not forbidden_modified),
    ]
    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, plan_rows, post_rows))

    print(f"STATUS: {status}")
    print(f"MODE: {mode}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if status == STATUS_FORBIDDEN else 0


if __name__ == "__main__":
    raise SystemExit(main())
