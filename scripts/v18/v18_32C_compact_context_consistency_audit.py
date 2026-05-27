from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import subprocess
import traceback
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_32C_CONTEXT_CONSISTENCY_AUDIT_READY"
STATUS_WARN = "WARN_V18_32C_CONTEXT_CONSISTENCY_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_32C_CONTEXT_CONSISTENCY_AUDIT_FAILED"
MODE_LIVE = "V18_32C_CONTEXT_CONSISTENCY_AUDIT"
MODE_DRY = "V18_32C_CONTEXT_CONSISTENCY_AUDIT_DRY_RUN"

CURRENT_DAILY = "outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md"
CURRENT_ACCOUNT_GUIDE = "outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md"
CURRENT_ACCOUNT_PLAN = "outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md"
CURRENT_SIGNAL_GUARD = "outputs/v18/read_center/V18_CURRENT_TRADING_DAY_SIGNAL_DATE_GUARD.md"
CURRENT_OPERATOR_CENTER = "outputs/v18/read_center/V18_CURRENT_OPERATOR_CONTROL_CENTER.md"
CURRENT_TRADE_PLAN_SNAPSHOT_REPORT = "outputs/v18/read_center/V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_REPORT.md"
CURRENT_ACCOUNT_AWARE_REPORT = "outputs/v18/read_center/V18_31D_ACCOUNT_AWARE_MANUAL_TRADE_PLAN_REPORT.md"

RANKED = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
THEMES = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
ACCOUNT_AWARE = "outputs/v18/execution/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.csv"

V32B_READ_FIRST = "outputs/v18/ops/V18_32B_READ_FIRST.txt"
V32B_CONTEXT = "outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md"

OUT_SUMMARY = "outputs/v18/ops/V18_32C_CONTEXT_CONSISTENCY_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_32C_CONTEXT_CONSISTENCY_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_32C_READ_FIRST.txt"
OUT_CONTEXT = "outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md"
OUT_ERROR = "outputs/v18/read_center/V18_32C_CONTEXT_CONSISTENCY_ERROR.md"

SUMMARY_FIELDS = [
    "run_id",
    "status",
    "generated_at",
    "dry_run",
    "patch32b_requested",
    "patch32b_applied",
    "expected_candidate_count",
    "freeze_ticker_count",
    "freeze_unique_ticker_count",
    "freeze_missing_vs_current_count",
    "freeze_extra_vs_current_count",
    "freeze_coverage_status",
    "latest_relevant_signal_date",
    "latest_supported_signal_date",
    "current_allowed_trade_candidate_count",
    "current_allowed_trade_candidate_tickers",
    "compact_expected_candidate_count",
    "compact_latest_relevant_signal_date",
    "compact_latest_full_freeze_status",
    "compact_latest_freeze_ticker_count",
    "compact_latest_freeze_expected_count",
    "compact_latest_freeze_coverage_status",
    "compact_current_allowed_trade_candidate_count",
    "compact_current_allowed_trade_candidate_tickers",
    "mismatch_count",
    "warning_count",
    "source_paths",
    "missing_tickers",
    "extra_tickers",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "DRY_RUN",
    "PATCH32B_REQUESTED",
    "PATCH32B_APPLIED",
    "EXPECTED_CANDIDATE_COUNT",
    "FREEZE_TICKER_COUNT",
    "FREEZE_UNIQUE_TICKER_COUNT",
    "FREEZE_MISSING_VS_CURRENT_COUNT",
    "FREEZE_EXTRA_VS_CURRENT_COUNT",
    "FREEZE_COVERAGE_STATUS",
    "LATEST_RELEVANT_SIGNAL_DATE",
    "LATEST_SUPPORTED_SIGNAL_DATE",
    "CURRENT_ALLOWED_TRADE_CANDIDATE_COUNT",
    "CURRENT_ALLOWED_TRADE_CANDIDATE_TICKERS",
    "COMPACT_EXPECTED_CANDIDATE_COUNT",
    "COMPACT_LATEST_RELEVANT_SIGNAL_DATE",
    "COMPACT_LATEST_FULL_FREEZE_STATUS",
    "COMPACT_LATEST_FREEZE_TICKER_COUNT",
    "COMPACT_LATEST_FREEZE_EXPECTED_COUNT",
    "COMPACT_LATEST_FREEZE_COVERAGE_STATUS",
    "COMPACT_CURRENT_ALLOWED_TRADE_CANDIDATE_COUNT",
    "COMPACT_CURRENT_ALLOWED_TRADE_CANDIDATE_TICKERS",
    "MISMATCH_COUNT",
    "WARNING_COUNT",
    "SOURCE_PATHS",
    "READ_FIRST_PATH",
    "REPORT_PATH",
    "CONTEXT_PATH",
]


def norm(value: object) -> str:
    return "" if value is None else str(value).strip()


def clean(value: object) -> str:
    return norm(value).strip("`").strip()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_status_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = clean(value)
    return values


def read_csv_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
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


def parse_csv_line(line: str) -> List[str]:
    values: List[str] = []
    cur = ""
    in_quotes = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            if in_quotes and i + 1 < len(line) and line[i + 1] == '"':
                cur += '"'
                i += 1
            else:
                in_quotes = not in_quotes
        elif ch == "," and not in_quotes:
            values.append(cur)
            cur = ""
        else:
            cur += ch
        i += 1
    values.append(cur)
    return values


def parse_ticker_rows(path: Path, ticker_field: str = "ticker") -> List[Dict[str, str]]:
    rows, _fields = read_csv_rows(path)
    return rows


def unique_tickers(rows: Sequence[Dict[str, str]], field: str = "ticker") -> List[str]:
    return sorted({clean(row.get(field)) for row in rows if clean(row.get(field))})


def first_regex(texts: Sequence[str], patterns: Sequence[str]) -> str:
    for text in texts:
        for pattern in patterns:
            m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
            if m:
                return clean(m.group(1))
    return "UNKNOWN"


def format_list(values: Sequence[str], limit: int = 25) -> str:
    if not values:
        return "NONE"
    if len(values) <= limit:
        return ";".join(values)
    head = ";".join(values[:limit])
    return f"{head};...(+{len(values) - limit})"


def compact_value(read_first: Dict[str, str], key: str) -> str:
    return read_first.get(key, "UNKNOWN")


def audit_current_state(root: Path) -> Dict[str, str]:
    daily = read_text(root / CURRENT_DAILY)
    guard = read_text(root / CURRENT_SIGNAL_GUARD)
    operator = read_text(root / CURRENT_OPERATOR_CENTER)
    plan_31e = read_text(root / CURRENT_TRADE_PLAN_SNAPSHOT_REPORT)
    plan_31d = read_text(root / CURRENT_ACCOUNT_AWARE_REPORT)
    ranked_rows, _ = read_csv_rows(root / RANKED)
    rec_rows, _ = read_csv_rows(root / RECOMMENDATIONS)
    theme_rows, _ = read_csv_rows(root / THEMES)
    freeze_rows, _ = read_csv_rows(root / FREEZE_LEDGER)
    allowed_rows, _ = read_csv_rows(root / ACCOUNT_AWARE)
    compact = read_status_file(root / V32B_READ_FIRST)
    compact_context = read_text(root / V32B_CONTEXT)

    latest_supported_signal_date = first_regex(
        [daily, guard, operator],
        [
            r"Recommended signal date:\s*`?([^`\r\n]+)`?",
            r"RECOMMENDED_SIGNAL_DATE:\s*([^\r\n]+)",
            r"LATEST_SIGNAL_DATE:\s*([^\r\n]+)",
        ],
    )
    latest_relevant_signal_date = latest_supported_signal_date
    expected_candidate_count = str(len(ranked_rows)) if ranked_rows else "UNKNOWN"
    ranked_tickers = unique_tickers(ranked_rows)

    relevant_freeze_rows = [row for row in freeze_rows if clean(row.get("signal_date")) == latest_relevant_signal_date]
    relevant_freeze_tickers = unique_tickers(relevant_freeze_rows)
    missing = sorted(set(ranked_tickers) - set(relevant_freeze_tickers))
    extra = sorted(set(relevant_freeze_tickers) - set(ranked_tickers))
    freeze_ticker_count = str(len(relevant_freeze_rows)) if relevant_freeze_rows else "UNKNOWN"
    freeze_unique_ticker_count = str(len(relevant_freeze_tickers)) if relevant_freeze_rows else "UNKNOWN"
    if not relevant_freeze_rows:
        freeze_coverage_status = "MISSING_LEDGER"
    elif missing and extra:
        freeze_coverage_status = "PARTIAL_MISSING_EXTRA_TICKERS"
    elif missing:
        freeze_coverage_status = "PARTIAL_MISSING"
    elif extra:
        freeze_coverage_status = "EXTRA_TICKERS"
    elif len(relevant_freeze_tickers) == len(ranked_tickers):
        freeze_coverage_status = "FULL_MATCH"
    else:
        freeze_coverage_status = "UNKNOWN"

    allowed_count = "UNKNOWN"
    allowed_tickers = "UNKNOWN"
    if plan_31e:
        allowed_count = first_regex([plan_31e], [r"ACCOUNT_TRADE_ALLOWED_COUNT:\s*`?([^`\r\n]+)`?"])
        if allowed_count == "UNKNOWN":
            allowed_count = first_regex([plan_31e], [r"ACCOUNT_TRADE_ALLOWED_COUNT,\s*([^\r\n]+)"])
        if allowed_count == "0":
            allowed_tickers = "NONE"
    if allowed_count == "UNKNOWN" and plan_31d:
        if re.search(r"Today's Account-Eligible Manual Buy Candidates\s*\r?\n_None\._", plan_31d, re.IGNORECASE):
            allowed_count = "0"
            allowed_tickers = "NONE"
    if allowed_count == "UNKNOWN" and allowed_rows:
        # Do not guess from blocked statuses.
        allowed_tickers = "UNKNOWN"
    source_paths = [
        CURRENT_DAILY,
        CURRENT_SIGNAL_GUARD,
        CURRENT_ACCOUNT_GUIDE,
        CURRENT_ACCOUNT_PLAN,
        CURRENT_TRADE_PLAN_SNAPSHOT_REPORT,
        CURRENT_ACCOUNT_AWARE_REPORT,
        RANKED,
        RECOMMENDATIONS,
        THEMES,
        FREEZE_LEDGER,
        ACCOUNT_AWARE,
        V32B_READ_FIRST,
        V32B_CONTEXT,
    ]

    compact_expected_candidate_count = compact_value(compact, "EXPECTED_CANDIDATE_COUNT")
    compact_latest_relevant_signal_date = compact_value(compact, "LATEST_RELEVANT_SIGNAL_DATE")
    compact_latest_full_freeze_status = compact_value(compact, "LATEST_FULL_FREEZE_STATUS")
    compact_latest_freeze_ticker_count = compact_value(compact, "LATEST_FREEZE_TICKER_COUNT")
    compact_latest_freeze_expected_count = compact_value(compact, "LATEST_FREEZE_EXPECTED_COUNT")
    compact_latest_freeze_coverage_status = compact_value(compact, "LATEST_FREEZE_COVERAGE_STATUS")
    compact_current_allowed_trade_candidate_count = compact_value(compact, "CURRENT_ALLOWED_TRADE_CANDIDATE_COUNT")
    compact_current_allowed_trade_candidate_tickers = compact_value(compact, "CURRENT_ALLOWED_TRADE_CANDIDATE_TICKERS")

    mismatches: List[str] = []
    warnings: List[str] = []
    if freeze_coverage_status != "FULL_MATCH":
        warnings.append(f"FREEZE_COVERAGE_{freeze_coverage_status}")
    if compact_latest_freeze_coverage_status not in {freeze_coverage_status, "UNKNOWN"}:
        mismatches.append("COMPACT_FREEZE_COVERAGE_STATUS")
    if compact_expected_candidate_count not in {expected_candidate_count, "UNKNOWN"}:
        mismatches.append("COMPACT_EXPECTED_CANDIDATE_COUNT")
    if compact_latest_relevant_signal_date not in {latest_relevant_signal_date, "UNKNOWN"}:
        mismatches.append("COMPACT_LATEST_RELEVANT_SIGNAL_DATE")
    if freeze_coverage_status == "FULL_MATCH":
        if compact_latest_full_freeze_status not in {"UNKNOWN", "", "FULL_FREEZE_COVERAGE"} and "FULL_FREEZE_COVERAGE" not in compact_latest_full_freeze_status:
            mismatches.append("COMPACT_LATEST_FULL_FREEZE_STATUS")
    else:
        if compact_latest_full_freeze_status not in {"UNKNOWN", ""} and "PARTIAL_FREEZE_COVERAGE" not in compact_latest_full_freeze_status:
            mismatches.append("COMPACT_LATEST_FULL_FREEZE_STATUS")
    if compact_latest_freeze_ticker_count not in {freeze_ticker_count, "UNKNOWN"}:
        mismatches.append("COMPACT_LATEST_FREEZE_TICKER_COUNT")
    if compact_latest_freeze_expected_count not in {expected_candidate_count, "UNKNOWN"}:
        mismatches.append("COMPACT_LATEST_FREEZE_EXPECTED_COUNT")
    if compact_current_allowed_trade_candidate_count not in {allowed_count, "UNKNOWN"}:
        mismatches.append("COMPACT_ALLOWED_TRADE_COUNT")
    if compact_current_allowed_trade_candidate_tickers not in {allowed_tickers, "UNKNOWN"}:
        mismatches.append("COMPACT_ALLOWED_TRADE_TICKERS")

    status = STATUS_OK if not mismatches and not warnings else STATUS_WARN
    if expected_candidate_count == "UNKNOWN" or latest_relevant_signal_date == "UNKNOWN":
        status = STATUS_WARN

    return {
        "run_id": f"V18_32C_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "status": status,
        "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "expected_candidate_count": expected_candidate_count,
        "freeze_ticker_count": freeze_ticker_count,
        "freeze_unique_ticker_count": freeze_unique_ticker_count,
        "freeze_missing_vs_current_count": str(len(missing)),
        "freeze_extra_vs_current_count": str(len(extra)),
        "freeze_coverage_status": freeze_coverage_status,
        "latest_relevant_signal_date": latest_relevant_signal_date,
        "latest_supported_signal_date": latest_supported_signal_date,
        "current_allowed_trade_candidate_count": allowed_count,
        "current_allowed_trade_candidate_tickers": allowed_tickers,
        "compact_expected_candidate_count": compact_expected_candidate_count,
        "compact_latest_relevant_signal_date": compact_latest_relevant_signal_date,
        "compact_latest_full_freeze_status": compact_latest_full_freeze_status,
        "compact_latest_freeze_ticker_count": compact_latest_freeze_ticker_count,
        "compact_latest_freeze_expected_count": compact_latest_freeze_expected_count,
        "compact_latest_freeze_coverage_status": compact_latest_freeze_coverage_status,
        "compact_current_allowed_trade_candidate_count": compact_current_allowed_trade_candidate_count,
        "compact_current_allowed_trade_candidate_tickers": compact_current_allowed_trade_candidate_tickers,
        "mismatch_count": str(len(mismatches)),
        "warning_count": str(len(warnings)),
        "source_paths": ";".join(source_paths),
        "missing_tickers": format_list(missing),
        "extra_tickers": format_list(extra),
        "mismatches": ";".join(mismatches) if mismatches else "NONE",
        "warnings": ";".join(warnings) if warnings else "NONE",
        "compact_context_path": V32B_CONTEXT,
        "read_first_path": V32B_READ_FIRST,
        "source_snapshot_paths": f"{CURRENT_DAILY};{CURRENT_SIGNAL_GUARD};{FREEZE_LEDGER};{CURRENT_TRADE_PLAN_SNAPSHOT_REPORT};{CURRENT_ACCOUNT_AWARE_REPORT}",
    }


def make_report(result: Dict[str, str], patch32b_requested: bool, patch32b_applied: bool, dry_run: bool) -> str:
    return f"""# V18.32C Compact Context Consistency Audit

## 1. Final Status
STATUS: {result['status']}

## 2. Snapshot
- EXPECTED_CANDIDATE_COUNT: `{result['expected_candidate_count']}`
- FREEZE_TICKER_COUNT: `{result['freeze_ticker_count']}`
- FREEZE_UNIQUE_TICKER_COUNT: `{result['freeze_unique_ticker_count']}`
- FREEZE_MISSING_VS_CURRENT_COUNT: `{result['freeze_missing_vs_current_count']}`
- FREEZE_EXTRA_VS_CURRENT_COUNT: `{result['freeze_extra_vs_current_count']}`
- FREEZE_COVERAGE_STATUS: `{result['freeze_coverage_status']}`
- LATEST_RELEVANT_SIGNAL_DATE: `{result['latest_relevant_signal_date']}`
- CURRENT_ALLOWED_TRADE_CANDIDATE_COUNT: `{result['current_allowed_trade_candidate_count']}`
- CURRENT_ALLOWED_TRADE_CANDIDATE_TICKERS: `{result['current_allowed_trade_candidate_tickers']}`

## 3. Compact Context Comparison
- COMPACT_EXPECTED_CANDIDATE_COUNT: `{result['compact_expected_candidate_count']}`
- COMPACT_LATEST_FREEZE_TICKER_COUNT: `{result['compact_latest_freeze_ticker_count']}`
- COMPACT_LATEST_FREEZE_EXPECTED_COUNT: `{result['compact_latest_freeze_expected_count']}`
- COMPACT_LATEST_FREEZE_COVERAGE_STATUS: `{result['compact_latest_freeze_coverage_status']}`
- COMPACT_ALLOWED_TRADE_COUNT: `{result['compact_current_allowed_trade_candidate_count']}`
- COMPACT_ALLOWED_TRADE_TICKERS: `{result['compact_current_allowed_trade_candidate_tickers']}`

## 4. Mismatches
- MISMATCH_COUNT: `{result['mismatch_count']}`
- MISMATCHES: `{result['mismatches']}`
- WARNING_COUNT: `{result['warning_count']}`
- WARNINGS: `{result['warnings']}`

## 5. Source Paths
- `{result['source_snapshot_paths']}`

## 6. Patch32B
- REQUESTED: `{bool_text(patch32b_requested)}`
- APPLIED: `{bool_text(patch32b_applied)}`
- DRY_RUN: `{bool_text(dry_run)}`

## 7. Safety
- AUTO_TRADE: `DISABLED`
- AUTO_SELL: `DISABLED`
- OFFICIAL_DECISION_IMPACT: `NONE`
- FORBIDDEN_MODIFIED: `FALSE`
- No broker/API/trading/order code added.
- No ledgers modified.
"""


def make_context_page(result: Dict[str, str]) -> str:
    return f"""# V18 Current Context Consistency

## Status
STATUS: {result['status']}

## Core Facts
- Expected candidates: `{result['expected_candidate_count']}`
- Freeze coverage: `{result['freeze_coverage_status']}`
- Freeze counts: `{result['freeze_ticker_count']}/{result['expected_candidate_count']}`
- Missing tickers: `{result['missing_tickers']}`
- Allowed trade candidates: `{result['current_allowed_trade_candidate_count']}`
- Allowed trade tickers: `{result['current_allowed_trade_candidate_tickers']}`
- Signal date: `{result['latest_relevant_signal_date']}`

## Read First
- `outputs/v18/ops/V18_32C_READ_FIRST.txt`
- `outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md`
- `outputs/v18/ops/V18_32B_READ_FIRST.txt`
- `outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md`
- `outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`

## Notes
- Compact context is now date-aware and marks partial freeze coverage explicitly.
- Use the audited source paths, not archived stale reports, unless a task explicitly asks otherwise.
"""


def make_read_first(result: Dict[str, str], patch32b_requested: bool, patch32b_applied: bool, dry_run: bool) -> str:
    values = {
        "STATUS": result["status"],
        "MODE": MODE_DRY if dry_run else MODE_LIVE,
        "RUN_ID": result["run_id"],
        "DRY_RUN": bool_text(dry_run),
        "PATCH32B_REQUESTED": bool_text(patch32b_requested),
        "PATCH32B_APPLIED": bool_text(patch32b_applied),
        "EXPECTED_CANDIDATE_COUNT": result["expected_candidate_count"],
        "FREEZE_TICKER_COUNT": result["freeze_ticker_count"],
        "FREEZE_UNIQUE_TICKER_COUNT": result["freeze_unique_ticker_count"],
        "FREEZE_MISSING_VS_CURRENT_COUNT": result["freeze_missing_vs_current_count"],
        "FREEZE_EXTRA_VS_CURRENT_COUNT": result["freeze_extra_vs_current_count"],
        "FREEZE_COVERAGE_STATUS": result["freeze_coverage_status"],
        "LATEST_RELEVANT_SIGNAL_DATE": result["latest_relevant_signal_date"],
        "LATEST_SUPPORTED_SIGNAL_DATE": result["latest_supported_signal_date"],
        "CURRENT_ALLOWED_TRADE_CANDIDATE_COUNT": result["current_allowed_trade_candidate_count"],
        "CURRENT_ALLOWED_TRADE_CANDIDATE_TICKERS": result["current_allowed_trade_candidate_tickers"],
        "COMPACT_EXPECTED_CANDIDATE_COUNT": result["compact_expected_candidate_count"],
        "COMPACT_LATEST_RELEVANT_SIGNAL_DATE": result["compact_latest_relevant_signal_date"],
        "COMPACT_LATEST_FULL_FREEZE_STATUS": result["compact_latest_full_freeze_status"],
        "COMPACT_LATEST_FREEZE_TICKER_COUNT": result["compact_latest_freeze_ticker_count"],
        "COMPACT_LATEST_FREEZE_EXPECTED_COUNT": result["compact_latest_freeze_expected_count"],
        "COMPACT_LATEST_FREEZE_COVERAGE_STATUS": result["compact_latest_freeze_coverage_status"],
        "COMPACT_CURRENT_ALLOWED_TRADE_CANDIDATE_COUNT": result["compact_current_allowed_trade_candidate_count"],
        "COMPACT_CURRENT_ALLOWED_TRADE_CANDIDATE_TICKERS": result["compact_current_allowed_trade_candidate_tickers"],
        "MISMATCH_COUNT": result["mismatch_count"],
        "WARNING_COUNT": result["warning_count"],
        "SOURCE_PATHS": result["source_paths"],
        "READ_FIRST_PATH": V32B_READ_FIRST,
        "REPORT_PATH": OUT_REPORT,
        "CONTEXT_PATH": OUT_CONTEXT,
    }
    lines = [f"{key}: {values.get(key, '')}" for key in READ_FIRST_FIELDS]
    lines.append(f"MISMATCHES: {result['mismatches']}")
    lines.append(f"WARNINGS: {result['warnings']}")
    lines.append(f"SOURCE_SNAPSHOT_PATHS: {result['source_snapshot_paths']}")
    return "\n".join(lines) + "\n"


def patch_v32b(root: Path, dry_run: bool) -> bool:
    if dry_run:
        return False
    wrapper = root / "scripts/v18/run_v18_32B_codex_context_compression_pack.ps1"
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(wrapper),
    ]
    completed = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"V18.32B refresh failed: {completed.stderr or completed.stdout}")
    return True


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    result = audit_current_state(root)
    patch_applied = False
    if args.patch32b and not args.dry_run:
        patch_applied = patch_v32b(root, args.dry_run)
        result = audit_current_state(root)
        result["status"] = STATUS_WARN if result["freeze_coverage_status"] != "FULL_MATCH" or result["mismatch_count"] != "0" else STATUS_OK

    status = result["status"]
    if not result["expected_candidate_count"] or result["expected_candidate_count"] == "UNKNOWN":
        status = STATUS_WARN
        result["status"] = status

    summary_row = {
        "run_id": result["run_id"],
        "status": result["status"],
        "generated_at": result["generated_at"],
        "dry_run": bool_text(args.dry_run),
        "patch32b_requested": bool_text(args.patch32b),
        "patch32b_applied": bool_text(patch_applied),
        "expected_candidate_count": result["expected_candidate_count"],
        "freeze_ticker_count": result["freeze_ticker_count"],
        "freeze_unique_ticker_count": result["freeze_unique_ticker_count"],
        "freeze_missing_vs_current_count": result["freeze_missing_vs_current_count"],
        "freeze_extra_vs_current_count": result["freeze_extra_vs_current_count"],
        "freeze_coverage_status": result["freeze_coverage_status"],
        "latest_relevant_signal_date": result["latest_relevant_signal_date"],
        "latest_supported_signal_date": result["latest_supported_signal_date"],
        "current_allowed_trade_candidate_count": result["current_allowed_trade_candidate_count"],
        "current_allowed_trade_candidate_tickers": result["current_allowed_trade_candidate_tickers"],
        "compact_expected_candidate_count": result["compact_expected_candidate_count"],
        "compact_latest_relevant_signal_date": result["compact_latest_relevant_signal_date"],
        "compact_latest_full_freeze_status": result["compact_latest_full_freeze_status"],
        "compact_latest_freeze_ticker_count": result["compact_latest_freeze_ticker_count"],
        "compact_latest_freeze_expected_count": result["compact_latest_freeze_expected_count"],
        "compact_latest_freeze_coverage_status": result["compact_latest_freeze_coverage_status"],
        "compact_current_allowed_trade_candidate_count": result["compact_current_allowed_trade_candidate_count"],
        "compact_current_allowed_trade_candidate_tickers": result["compact_current_allowed_trade_candidate_tickers"],
        "mismatch_count": result["mismatch_count"],
        "warning_count": result["warning_count"],
        "source_paths": result["source_paths"],
        "missing_tickers": result["missing_tickers"],
        "extra_tickers": result["extra_tickers"],
    }
    write_csv(root / OUT_SUMMARY, [summary_row], SUMMARY_FIELDS)
    write_text(root / OUT_REPORT, make_report(result, args.patch32b, patch_applied, args.dry_run))
    write_text(root / OUT_CONTEXT, make_context_page(result))
    write_text(root / OUT_READ_FIRST, make_read_first(result, args.patch32b, patch_applied, args.dry_run))

    print(f"STATUS: {result['status']}")
    print(f"RUN_ID: {result['run_id']}")
    print(f"DRY_RUN: {bool_text(args.dry_run)}")
    print(f"PATCH32B_REQUESTED: {bool_text(args.patch32b)}")
    print(f"PATCH32B_APPLIED: {bool_text(patch_applied)}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    print(f"FREEZE_COVERAGE_STATUS: {result['freeze_coverage_status']}")
    print(f"CURRENT_ALLOWED_TRADE_CANDIDATE_COUNT: {result['current_allowed_trade_candidate_count']}")
    print(f"MISMATCH_COUNT: {result['mismatch_count']}")
    print(f"WARNING_COUNT: {result['warning_count']}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit V18.32B compact context consistency.")
    parser.add_argument("--root", default="D:\\us-tech-quant")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--patch32b", action="store_true")
    return parser.parse_args()


def main() -> int:
    try:
        return run(parse_args())
    except Exception as exc:
        root = Path("D:\\us-tech-quant")
        try:
            args = parse_args()
            root = Path(args.root).resolve()
        except Exception:
            pass
        now = dt.datetime.now().replace(microsecond=0).isoformat()
        write_text(
            root / OUT_ERROR,
            "# V18.32C Compact Context Consistency Audit Error\n\n"
            f"STATUS: {STATUS_FAIL}\n\n"
            f"GENERATED_AT: `{now}`\n\n"
            "```text\n"
            f"{exc}\n\n{traceback.format_exc()}"
            "```\n",
        )
        print(f"STATUS: {STATUS_FAIL}")
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
