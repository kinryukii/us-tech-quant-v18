from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_DRYRUN = "OK_V18_25A_R27H_DRYRUN_OFFICIAL_FACTOR_TECHNICAL_MERGE_PLAN_READY"
STATUS_APPLY_OK = "OK_V18_25A_R27H_OFFICIAL_FACTOR_TECHNICAL_MERGE_READY"
STATUS_APPLY_BLOCKED = "WARN_V18_25A_R27H_APPLY_BLOCKED"
STATUS_POST_REVIEW = "WARN_V18_25A_R27H_POST_MERGE_VALIDATION_REVIEW_NEEDED"
STATUS_FORBIDDEN = "FAIL_V18_25A_R27H_FORBIDDEN_MODIFIED"

MODE_DRYRUN = "DRYRUN_OFFICIAL_FACTOR_TECHNICAL_MERGE_PLAN_ONLY"
MODE_APPLY = "APPLY_OFFICIAL_FACTOR_TECHNICAL_MERGE_WITH_BACKUP"

EXPECTED_TICKERS = ["RDDT", "TLN"]
EXPECTED_TICKER_SET = set(EXPECTED_TICKERS)
EXPECTED_R27G_STATUS = "OK_V18_25A_R27G_STAGED_VALIDATION_MERGE_PLAN_READY"

R27G_READ_FIRST = "outputs/v18/ops/V18_25A_R27G_READ_FIRST.txt"
R27G_MERGE_PLAN = "outputs/v18/staged_factor_technical/V18_25A_R27G_CURRENT_OFFICIAL_MERGE_PLAN.csv"
R27G_BACKUP_PLAN = "outputs/v18/staged_factor_technical/V18_25A_R27G_CURRENT_REQUIRED_BACKUP_PLAN.csv"
STAGED_FACTOR = "outputs/v18/staged_factor_technical/V18_25A_R27F_CURRENT_STAGED_FACTOR_ROWS.csv"
STAGED_TECH = "outputs/v18/staged_factor_technical/V18_25A_R27F_CURRENT_STAGED_TECHNICAL_ROWS.csv"
OFFICIAL_FACTOR = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
OFFICIAL_TECH = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"

PRICE_CACHE_DIR = "state/v18/price_cache"
ROLLING_LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
CANDIDATES_DIR = "outputs/v18/candidates"
OFFICIAL_DECISIONS_DIR = "outputs/v18/official_decisions"
FACTOR_DIR = "outputs/v18/factor_pack"
TECH_DIR = "outputs/v18/technical_timing"
BACKUP_ROOT = "archive/v18/factor_technical_merge_backups"

OUT_DIR = "outputs/v18/staged_factor_technical"
OUT_PLAN = f"{OUT_DIR}/V18_25A_R27H_CURRENT_DRYRUN_OR_APPLY_PLAN.csv"
OUT_FACTOR_RESULT = f"{OUT_DIR}/V18_25A_R27H_CURRENT_FACTOR_MERGE_RESULT.csv"
OUT_TECH_RESULT = f"{OUT_DIR}/V18_25A_R27H_CURRENT_TECHNICAL_MERGE_RESULT.csv"
OUT_POST_VALIDATE = f"{OUT_DIR}/V18_25A_R27H_CURRENT_POST_MERGE_VALIDATION.csv"
OUT_BACKUP_MANIFEST = f"{OUT_DIR}/V18_25A_R27H_CURRENT_BACKUP_MANIFEST.csv"
OUT_SUMMARY = f"{OUT_DIR}/V18_25A_R27H_CURRENT_SUMMARY.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R27H_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R27H_CURRENT_OFFICIAL_FACTOR_TECHNICAL_MERGE_REPORT.md"

PLAN_FIELDS = [
    "ticker",
    "factor_merge_action",
    "technical_merge_action",
    "factor_schema_compatible",
    "technical_schema_compatible",
    "factor_score_present",
    "technical_score_present",
    "merge_allowed",
    "blocker",
]
RESULT_FIELDS = [
    "ticker",
    "merge_attempted",
    "merge_success",
    "merge_action",
    "rows_before",
    "rows_after",
    "error_message",
]
POST_FIELDS = [
    "ticker",
    "factor_present",
    "technical_present",
    "factor_score_present",
    "technical_score_present",
    "factor_duplicate_count",
    "technical_duplicate_count",
    "factor_row_count_delta_ok",
    "technical_row_count_delta_ok",
    "post_validate_status",
    "error_message",
]
BACKUP_FIELDS = ["backup_item", "source_path", "backup_path", "backup_status", "notes"]
SUMMARY_FIELDS = ["metric", "value", "expected", "status", "notes"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R27G_STATUS",
    "APPLY_REQUESTED",
    "TARGET_TICKER_COUNT",
    "TARGET_TICKERS",
    "EXPECTED_TICKER_MATCH",
    "BACKUP_CREATED",
    "BACKUP_DIR",
    "RESTORE_SCRIPT_CREATED",
    "FACTOR_MERGE_ATTEMPT_COUNT",
    "FACTOR_MERGE_SUCCESS_COUNT",
    "FACTOR_MERGE_FAIL_COUNT",
    "TECHNICAL_MERGE_ATTEMPT_COUNT",
    "TECHNICAL_MERGE_SUCCESS_COUNT",
    "TECHNICAL_MERGE_FAIL_COUNT",
    "FACTOR_APPEND_COUNT",
    "FACTOR_UPDATE_COUNT",
    "TECHNICAL_APPEND_COUNT",
    "TECHNICAL_UPDATE_COUNT",
    "POST_VALIDATE_FACTOR_PRESENT_COUNT",
    "POST_VALIDATE_TECHNICAL_PRESENT_COUNT",
    "POST_VALIDATE_FACTOR_SCORE_PRESENT_COUNT",
    "POST_VALIDATE_TECHNICAL_SCORE_PRESENT_COUNT",
    "POST_VALIDATE_FAIL_COUNT",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "CANDIDATES_MODIFIED",
    "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
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
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
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


def changed_keys(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    return [key for key in sorted(set(before) | set(after)) if before.get(key) != after.get(key)]


def rows_by_ticker(rows: Sequence[Dict[str, str]], ticker_col: str = "ticker") -> Dict[str, Dict[str, str]]:
    return {norm_ticker(row.get(ticker_col)): row for row in rows if norm_ticker(row.get(ticker_col))}


def duplicate_count(rows: Sequence[Dict[str, str]], tickers: Sequence[str], ticker_col: str = "ticker") -> int:
    counts = {ticker: 0 for ticker in tickers}
    for row in rows:
        ticker = norm_ticker(row.get(ticker_col))
        if ticker in counts:
            counts[ticker] += 1
    return sum(max(0, count - 1) for count in counts.values())


def target_presence_count(rows: Sequence[Dict[str, str]], tickers: Sequence[str], ticker_col: str = "ticker") -> int:
    present = {norm_ticker(row.get(ticker_col)) for row in rows}
    return sum(1 for ticker in tickers if ticker in present)


def project_row(row: Dict[str, str], fields: Sequence[str]) -> Dict[str, str]:
    return {field: str(row.get(field, "") or "") for field in fields}


def validate_inputs(root: Path) -> Tuple[List[str], Dict[str, object]]:
    blockers: List[str] = []
    r27g_path = root / R27G_READ_FIRST
    r27g_status = read_first_value(r27g_path, "STATUS")
    values = {
        "R27G_STATUS": r27g_status or "MISSING",
        "EXPECTED_TICKER_MATCH": "FALSE",
    }
    if not r27g_path.exists():
        blockers.append(f"missing required input: {R27G_READ_FIRST}")
    if r27g_status != EXPECTED_R27G_STATUS:
        blockers.append(f"R27G status is {r27g_status or 'MISSING'}")
    if read_first_value(r27g_path, "R27H_OFFICIAL_MERGE_RECOMMENDED") != "TRUE":
        blockers.append("R27G did not recommend R27H official merge")
    if to_int(read_first_value(r27g_path, "MERGE_ALLOWED_COUNT")) != 2:
        blockers.append("R27G MERGE_ALLOWED_COUNT is not 2")
    if to_int(read_first_value(r27g_path, "MERGE_BLOCKED_COUNT")) != 0:
        blockers.append("R27G MERGE_BLOCKED_COUNT is not 0")
    if read_first_value(r27g_path, "FORBIDDEN_MODIFIED") != "FALSE":
        blockers.append("R27G FORBIDDEN_MODIFIED is not FALSE")

    for rel_path in [R27G_MERGE_PLAN, R27G_BACKUP_PLAN, STAGED_FACTOR, STAGED_TECH, OFFICIAL_FACTOR, OFFICIAL_TECH]:
        if not (root / rel_path).exists():
            blockers.append(f"missing required input: {rel_path}")
    return blockers, values


def build_plan(
    staged_factor_rows: List[Dict[str, str]],
    staged_factor_fields: Sequence[str],
    staged_tech_rows: List[Dict[str, str]],
    staged_tech_fields: Sequence[str],
    official_factor_rows: List[Dict[str, str]],
    official_factor_fields: Sequence[str],
    official_tech_rows: List[Dict[str, str]],
    official_tech_fields: Sequence[str],
) -> Tuple[List[Dict[str, object]], List[str]]:
    blockers: List[str] = []
    factor_tickers = [norm_ticker(row.get("ticker")) for row in staged_factor_rows]
    tech_tickers = [norm_ticker(row.get("ticker")) for row in staged_tech_rows]

    if len(staged_factor_rows) != 2:
        blockers.append(f"staged factor row count is {len(staged_factor_rows)}")
    if len(staged_tech_rows) != 2:
        blockers.append(f"staged technical row count is {len(staged_tech_rows)}")
    if set(factor_tickers) != EXPECTED_TICKER_SET:
        blockers.append(f"staged factor tickers are {','.join(sorted(set(factor_tickers)))}")
    if set(tech_tickers) != EXPECTED_TICKER_SET:
        blockers.append(f"staged technical tickers are {','.join(sorted(set(tech_tickers)))}")
    if len(factor_tickers) != len(set(factor_tickers)):
        blockers.append("duplicate staged factor ticker rows")
    if len(tech_tickers) != len(set(tech_tickers)):
        blockers.append("duplicate staged technical ticker rows")
    if not set(official_factor_fields).issubset(set(staged_factor_fields)) and not set(staged_factor_fields).issubset(set(official_factor_fields)):
        blockers.append("staged factor schema is not compatible with official factor schema")
    if not set(official_tech_fields).issubset(set(staged_tech_fields)) and not set(staged_tech_fields).issubset(set(official_tech_fields)):
        blockers.append("staged technical schema is not compatible with official technical schema")

    factor_by_ticker = rows_by_ticker(staged_factor_rows)
    tech_by_ticker = rows_by_ticker(staged_tech_rows)
    official_factor_tickers = {norm_ticker(row.get("ticker")) for row in official_factor_rows}
    official_tech_tickers = {norm_ticker(row.get("ticker")) for row in official_tech_rows}

    rows: List[Dict[str, object]] = []
    for ticker in EXPECTED_TICKERS:
        factor_row = factor_by_ticker.get(ticker, {})
        tech_row = tech_by_ticker.get(ticker, {})
        factor_score_present = non_null(factor_row.get("factor_pack_score"))
        tech_score_present = non_null(tech_row.get("technical_timing_score"))
        factor_schema_compatible = set(official_factor_fields).issubset(set(staged_factor_fields))
        tech_schema_compatible = set(official_tech_fields).issubset(set(staged_tech_fields))
        row_blockers: List[str] = []
        if not factor_row:
            row_blockers.append("missing staged factor row")
        if not tech_row:
            row_blockers.append("missing staged technical row")
        if not factor_score_present:
            row_blockers.append("missing factor score")
        if not tech_score_present:
            row_blockers.append("missing technical score")
        if not factor_schema_compatible:
            row_blockers.append("factor schema incompatible")
        if not tech_schema_compatible:
            row_blockers.append("technical schema incompatible")
        rows.append(
            {
                "ticker": ticker,
                "factor_merge_action": "UPDATE" if ticker in official_factor_tickers else "APPEND",
                "technical_merge_action": "UPDATE" if ticker in official_tech_tickers else "APPEND",
                "factor_schema_compatible": str(factor_schema_compatible).upper(),
                "technical_schema_compatible": str(tech_schema_compatible).upper(),
                "factor_score_present": str(factor_score_present).upper(),
                "technical_score_present": str(tech_score_present).upper(),
                "merge_allowed": str(not row_blockers).upper(),
                "blocker": "; ".join(row_blockers),
            }
        )
    return rows, blockers


def create_backup(root: Path, run_stamp: str) -> Tuple[Path, List[Dict[str, object]], bool]:
    backup_dir = root / BACKUP_ROOT / f"V18_25A_R27H_{run_stamp}"
    ensure_dir(backup_dir)
    rows: List[Dict[str, object]] = []
    for item, rel_path in [
        ("OFFICIAL_FACTOR_PACK", OFFICIAL_FACTOR),
        ("OFFICIAL_TECHNICAL_TIMING", OFFICIAL_TECH),
    ]:
        source = root / rel_path
        backup = backup_dir / source.name
        shutil.copy2(source, backup)
        rows.append(
            {
                "backup_item": item,
                "source_path": source.as_posix(),
                "backup_path": backup.as_posix(),
                "backup_status": "BACKED_UP",
                "notes": "Restore before any downstream candidate rebuild if rollback is needed.",
            }
        )
    write_csv(backup_dir / "MANIFEST.csv", rows, BACKUP_FIELDS)
    restore_script = backup_dir / "RESTORE_V18_25A_R27H_FACTOR_TECHNICAL_MERGE.ps1"
    restore_text = """[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$manifestPath = Join-Path $PSScriptRoot "MANIFEST.csv"
$manifest = Import-Csv $manifestPath
foreach ($row in $manifest) {
    if ($row.backup_status -eq "BACKED_UP") {
        Copy-Item -Path $row.backup_path -Destination $row.source_path -Force
        Write-Host "Restored $($row.backup_item): $($row.source_path)"
    }
}
"""
    write_text(restore_script, restore_text)
    write_text(
        backup_dir / "README_V18_25A_R27H_RESTORE.txt",
        "Run RESTORE_V18_25A_R27H_FACTOR_TECHNICAL_MERGE.ps1 to restore the official factor pack and technical timing files to their pre-R27H state.\n",
    )
    return backup_dir, rows, restore_script.exists()


def merge_rows(
    official_rows: List[Dict[str, str]],
    official_fields: Sequence[str],
    staged_by_ticker: Dict[str, Dict[str, str]],
    tickers: Sequence[str],
) -> List[Dict[str, str]]:
    target_set = set(tickers)
    kept = [row for row in official_rows if norm_ticker(row.get("ticker")) not in target_set]
    for ticker in tickers:
        kept.append(project_row(staged_by_ticker[ticker], official_fields))
    return kept


def post_validate(
    root: Path,
    expected_factor_delta: int,
    expected_tech_delta: int,
    factor_before_count: int,
    tech_before_count: int,
) -> Tuple[List[Dict[str, object]], Dict[str, int]]:
    factor_rows, _ = read_csv(root / OFFICIAL_FACTOR)
    tech_rows, _ = read_csv(root / OFFICIAL_TECH)
    factor_by_ticker = rows_by_ticker(factor_rows)
    tech_by_ticker = rows_by_ticker(tech_rows)
    factor_delta_ok = len(factor_rows) == factor_before_count + expected_factor_delta
    tech_delta_ok = len(tech_rows) == tech_before_count + expected_tech_delta
    rows: List[Dict[str, object]] = []
    counts = {
        "factor_present": 0,
        "technical_present": 0,
        "factor_score": 0,
        "technical_score": 0,
        "fail": 0,
    }
    for ticker in EXPECTED_TICKERS:
        factor_present = ticker in factor_by_ticker
        technical_present = ticker in tech_by_ticker
        factor_score = factor_present and non_null(factor_by_ticker[ticker].get("factor_pack_score"))
        tech_score = technical_present and non_null(tech_by_ticker[ticker].get("technical_timing_score"))
        factor_dupes = duplicate_count(factor_rows, [ticker])
        tech_dupes = duplicate_count(tech_rows, [ticker])
        ok = factor_present and technical_present and factor_score and tech_score and factor_dupes == 0 and tech_dupes == 0 and factor_delta_ok and tech_delta_ok
        if factor_present:
            counts["factor_present"] += 1
        if technical_present:
            counts["technical_present"] += 1
        if factor_score:
            counts["factor_score"] += 1
        if tech_score:
            counts["technical_score"] += 1
        if not ok:
            counts["fail"] += 1
        errors: List[str] = []
        if not factor_present:
            errors.append("factor row missing")
        if not technical_present:
            errors.append("technical row missing")
        if not factor_score:
            errors.append("factor score missing")
        if not tech_score:
            errors.append("technical score missing")
        if factor_dupes:
            errors.append("duplicate factor target rows")
        if tech_dupes:
            errors.append("duplicate technical target rows")
        if not factor_delta_ok:
            errors.append("factor row count delta mismatch")
        if not tech_delta_ok:
            errors.append("technical row count delta mismatch")
        rows.append(
            {
                "ticker": ticker,
                "factor_present": str(factor_present).upper(),
                "technical_present": str(technical_present).upper(),
                "factor_score_present": str(factor_score).upper(),
                "technical_score_present": str(tech_score).upper(),
                "factor_duplicate_count": factor_dupes,
                "technical_duplicate_count": tech_dupes,
                "factor_row_count_delta_ok": str(factor_delta_ok).upper(),
                "technical_row_count_delta_ok": str(tech_delta_ok).upper(),
                "post_validate_status": "PASS" if ok else "FAIL",
                "error_message": "; ".join(errors),
            }
        )
    return rows, counts


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object], blockers: Sequence[str], plan_rows: Sequence[Dict[str, object]]) -> str:
    blockers_text = "\n".join(f"- {item}" for item in blockers) if blockers else "- None."
    plan_text = "\n".join(
        f"- {row['ticker']}: factor {row['factor_merge_action']}, technical {row['technical_merge_action']}, allowed {row['merge_allowed']}"
        for row in plan_rows
    )
    return "\n".join(
        [
            "# V18.25A-R27H Official Factor + Technical Merge",
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
            "## Backup",
            "",
            f"- BACKUP_CREATED: {values['BACKUP_CREATED']}",
            f"- BACKUP_DIR: {values['BACKUP_DIR']}",
            f"- RESTORE_SCRIPT_CREATED: {values['RESTORE_SCRIPT_CREATED']}",
            "",
            "## Guardrails",
            "",
            f"- FACTOR_PACK_MODIFIED: {values['FACTOR_PACK_MODIFIED']}",
            f"- TECHNICAL_TIMING_MODIFIED: {values['TECHNICAL_TIMING_MODIFIED']}",
            f"- CANDIDATES_MODIFIED: {values['CANDIDATES_MODIFIED']}",
            f"- PRICE_CACHE_MODIFIED: {values['PRICE_CACHE_MODIFIED']}",
            f"- ROLLING_LEDGER_MODIFIED: {values['ROLLING_LEDGER_MODIFIED']}",
            f"- FORBIDDEN_MODIFIED: {values['FORBIDDEN_MODIFIED']}",
            "",
            "## Blockers",
            "",
            blockers_text,
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
    now = dt.datetime.now()
    run_stamp = now.strftime("%Y%m%d_%H%M%S")
    run_id = f"V18_25A_R27H_{run_stamp}"
    mode = MODE_APPLY if args.apply else MODE_DRYRUN

    factor_before_tree = tree_sig(root / FACTOR_DIR)
    tech_before_tree = tree_sig(root / TECH_DIR)
    candidates_before_tree = tree_sig(root / CANDIDATES_DIR)
    price_before_tree = tree_sig(root / PRICE_CACHE_DIR)
    ledger_before_sig = file_sig(root / ROLLING_LEDGER)
    official_decisions_before_tree = tree_sig(root / OFFICIAL_DECISIONS_DIR)

    input_blockers, input_values = validate_inputs(root)

    staged_factor_rows, staged_factor_fields = read_csv(root / STAGED_FACTOR)
    staged_tech_rows, staged_tech_fields = read_csv(root / STAGED_TECH)
    official_factor_rows, official_factor_fields = read_csv(root / OFFICIAL_FACTOR)
    official_tech_rows, official_tech_fields = read_csv(root / OFFICIAL_TECH)
    merge_plan_rows, plan_blockers = build_plan(
        staged_factor_rows,
        staged_factor_fields,
        staged_tech_rows,
        staged_tech_fields,
        official_factor_rows,
        official_factor_fields,
        official_tech_rows,
        official_tech_fields,
    )
    blockers = input_blockers + plan_blockers

    merge_allowed_count = sum(1 for row in merge_plan_rows if row["merge_allowed"] == "TRUE")
    factor_append_count = sum(1 for row in merge_plan_rows if row["factor_merge_action"] == "APPEND")
    factor_update_count = sum(1 for row in merge_plan_rows if row["factor_merge_action"] == "UPDATE")
    tech_append_count = sum(1 for row in merge_plan_rows if row["technical_merge_action"] == "APPEND")
    tech_update_count = sum(1 for row in merge_plan_rows if row["technical_merge_action"] == "UPDATE")
    expected_match = (
        set(norm_ticker(row.get("ticker")) for row in merge_plan_rows) == EXPECTED_TICKER_SET
        and len(merge_plan_rows) == 2
    )
    if not expected_match:
        blockers.append("merge plan target tickers are not exactly RDDT/TLN")
    if merge_allowed_count != 2:
        blockers.append("merge plan does not allow both targets")

    write_csv(root / OUT_PLAN, merge_plan_rows, PLAN_FIELDS)

    backup_dir = Path("")
    backup_rows: List[Dict[str, object]] = []
    backup_created = False
    restore_created = False
    factor_results: List[Dict[str, object]] = []
    tech_results: List[Dict[str, object]] = []
    post_rows: List[Dict[str, object]] = []
    post_counts = {"factor_present": 0, "technical_present": 0, "factor_score": 0, "technical_score": 0, "fail": 0}

    if not args.apply:
        status = STATUS_DRYRUN if not blockers else STATUS_APPLY_BLOCKED
    elif blockers:
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
                factor_by_ticker = rows_by_ticker(staged_factor_rows)
                tech_by_ticker = rows_by_ticker(staged_tech_rows)
                new_factor_rows = merge_rows(official_factor_rows, official_factor_fields, factor_by_ticker, EXPECTED_TICKERS)
                new_tech_rows = merge_rows(official_tech_rows, official_tech_fields, tech_by_ticker, EXPECTED_TICKERS)
                write_csv(root / OFFICIAL_FACTOR, new_factor_rows, official_factor_fields)
                write_csv(root / OFFICIAL_TECH, new_tech_rows, official_tech_fields)
                for row in merge_plan_rows:
                    ticker = str(row["ticker"])
                    factor_results.append(
                        {
                            "ticker": ticker,
                            "merge_attempted": "TRUE",
                            "merge_success": "TRUE",
                            "merge_action": row["factor_merge_action"],
                            "rows_before": len(official_factor_rows),
                            "rows_after": len(new_factor_rows),
                            "error_message": "",
                        }
                    )
                    tech_results.append(
                        {
                            "ticker": ticker,
                            "merge_attempted": "TRUE",
                            "merge_success": "TRUE",
                            "merge_action": row["technical_merge_action"],
                            "rows_before": len(official_tech_rows),
                            "rows_after": len(new_tech_rows),
                            "error_message": "",
                        }
                    )
                post_rows, post_counts = post_validate(
                    root,
                    factor_append_count,
                    tech_append_count,
                    len(official_factor_rows),
                    len(official_tech_rows),
                )
                status = STATUS_APPLY_OK if post_counts["fail"] == 0 else STATUS_POST_REVIEW
            except Exception as exc:
                blockers.append(f"apply_failed: {type(exc).__name__}: {exc}")
                status = STATUS_POST_REVIEW

    if not args.apply:
        for row in merge_plan_rows:
            factor_results.append(
                {
                    "ticker": row["ticker"],
                    "merge_attempted": "FALSE",
                    "merge_success": "FALSE",
                    "merge_action": row["factor_merge_action"],
                    "rows_before": len(official_factor_rows),
                    "rows_after": len(official_factor_rows),
                    "error_message": "DRYRUN_ONLY",
                }
            )
            tech_results.append(
                {
                    "ticker": row["ticker"],
                    "merge_attempted": "FALSE",
                    "merge_success": "FALSE",
                    "merge_action": row["technical_merge_action"],
                    "rows_before": len(official_tech_rows),
                    "rows_after": len(official_tech_rows),
                    "error_message": "DRYRUN_ONLY",
                }
            )

    write_csv(root / OUT_FACTOR_RESULT, factor_results, RESULT_FIELDS)
    write_csv(root / OUT_TECH_RESULT, tech_results, RESULT_FIELDS)
    write_csv(root / OUT_POST_VALIDATE, post_rows, POST_FIELDS)
    write_csv(root / OUT_BACKUP_MANIFEST, backup_rows, BACKUP_FIELDS)

    factor_attempts = sum(1 for row in factor_results if row["merge_attempted"] == "TRUE")
    factor_success = sum(1 for row in factor_results if row["merge_success"] == "TRUE")
    tech_attempts = sum(1 for row in tech_results if row["merge_attempted"] == "TRUE")
    tech_success = sum(1 for row in tech_results if row["merge_success"] == "TRUE")

    summary_rows = [
        summary_row("R27G_STATUS", input_values["R27G_STATUS"], EXPECTED_R27G_STATUS, input_values["R27G_STATUS"] == EXPECTED_R27G_STATUS),
        summary_row("EXPECTED_TICKER_MATCH", str(expected_match).upper(), "TRUE", expected_match),
        summary_row("MERGE_ALLOWED_COUNT", merge_allowed_count, 2, merge_allowed_count == 2),
        summary_row("FACTOR_APPEND_COUNT", factor_append_count, 2, factor_append_count == 2),
        summary_row("FACTOR_UPDATE_COUNT", factor_update_count, 0, factor_update_count == 0),
        summary_row("TECHNICAL_APPEND_COUNT", tech_append_count, 2, tech_append_count == 2),
        summary_row("TECHNICAL_UPDATE_COUNT", tech_update_count, 0, tech_update_count == 0),
        summary_row("POST_VALIDATE_FAIL_COUNT", post_counts["fail"], 0 if args.apply else "N/A", post_counts["fail"] == 0),
    ]
    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    factor_after_tree = tree_sig(root / FACTOR_DIR)
    tech_after_tree = tree_sig(root / TECH_DIR)
    candidates_after_tree = tree_sig(root / CANDIDATES_DIR)
    price_after_tree = tree_sig(root / PRICE_CACHE_DIR)
    ledger_after_sig = file_sig(root / ROLLING_LEDGER)
    official_decisions_after_tree = tree_sig(root / OFFICIAL_DECISIONS_DIR)

    factor_changed = changed_keys(factor_before_tree, factor_after_tree)
    tech_changed = changed_keys(tech_before_tree, tech_after_tree)
    allowed_factor_changed = factor_changed in ([], [Path(OFFICIAL_FACTOR).name])
    allowed_tech_changed = tech_changed in ([], [Path(OFFICIAL_TECH).name])
    factor_modified = bool(factor_changed)
    tech_modified = bool(tech_changed)
    candidates_modified = candidates_before_tree != candidates_after_tree
    price_modified = price_before_tree != price_after_tree
    ledger_modified = ledger_before_sig != ledger_after_sig
    official_decisions_modified = official_decisions_before_tree != official_decisions_after_tree
    forbidden_modified = (
        not allowed_factor_changed
        or not allowed_tech_changed
        or candidates_modified
        or price_modified
        or ledger_modified
        or official_decisions_modified
    )
    if forbidden_modified:
        status = STATUS_FORBIDDEN

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": mode,
        "RUN_ID": run_id,
        "R27G_STATUS": input_values["R27G_STATUS"],
        "APPLY_REQUESTED": str(args.apply).upper(),
        "TARGET_TICKER_COUNT": len(EXPECTED_TICKERS),
        "TARGET_TICKERS": ",".join(EXPECTED_TICKERS),
        "EXPECTED_TICKER_MATCH": str(expected_match).upper(),
        "BACKUP_CREATED": str(backup_created).upper(),
        "BACKUP_DIR": backup_dir.as_posix() if backup_created else "",
        "RESTORE_SCRIPT_CREATED": str(restore_created).upper(),
        "FACTOR_MERGE_ATTEMPT_COUNT": factor_attempts,
        "FACTOR_MERGE_SUCCESS_COUNT": factor_success,
        "FACTOR_MERGE_FAIL_COUNT": factor_attempts - factor_success,
        "TECHNICAL_MERGE_ATTEMPT_COUNT": tech_attempts,
        "TECHNICAL_MERGE_SUCCESS_COUNT": tech_success,
        "TECHNICAL_MERGE_FAIL_COUNT": tech_attempts - tech_success,
        "FACTOR_APPEND_COUNT": factor_append_count,
        "FACTOR_UPDATE_COUNT": factor_update_count,
        "TECHNICAL_APPEND_COUNT": tech_append_count,
        "TECHNICAL_UPDATE_COUNT": tech_update_count,
        "POST_VALIDATE_FACTOR_PRESENT_COUNT": post_counts["factor_present"],
        "POST_VALIDATE_TECHNICAL_PRESENT_COUNT": post_counts["technical_present"],
        "POST_VALIDATE_FACTOR_SCORE_PRESENT_COUNT": post_counts["factor_score"],
        "POST_VALIDATE_TECHNICAL_SCORE_PRESENT_COUNT": post_counts["technical_score"],
        "POST_VALIDATE_FAIL_COUNT": post_counts["fail"],
        "FACTOR_PACK_MODIFIED": str(factor_modified).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(tech_modified).upper(),
        "CANDIDATES_MODIFIED": str(candidates_modified).upper(),
        "PRICE_CACHE_MODIFIED": str(price_modified).upper(),
        "ROLLING_LEDGER_MODIFIED": str(ledger_modified).upper(),
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "VALIDATION_FAIL_COUNT": 1 if status in {STATUS_FORBIDDEN, STATUS_POST_REVIEW} else 0,
        "FORBIDDEN_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": "R27I: post-merge candidate-readiness audit for RDDT/TLN only; keep auto trade and auto sell disabled.",
    }

    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, blockers, merge_plan_rows))

    print(f"STATUS: {status}")
    print(f"MODE: {mode}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if status == STATUS_FORBIDDEN else 0


if __name__ == "__main__":
    raise SystemExit(main())
