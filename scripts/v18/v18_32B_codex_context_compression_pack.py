from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import traceback
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_32B_CODEX_CONTEXT_COMPRESSION_READY"
STATUS_WARN = "WARN_V18_32B_CODEX_CONTEXT_COMPRESSION_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_32B_CODEX_CONTEXT_COMPRESSION_FAILED"
MODE_LIVE = "CODEX_CONTEXT_COMPRESSION_PACK"
MODE_DRY = "CODEX_CONTEXT_COMPRESSION_PACK_DRY_RUN"

CURRENT_DAILY = "outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md"
CURRENT_ACCOUNT_GUIDE = "outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md"
CURRENT_ACCOUNT_PLAN = "outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md"
CURRENT_OPERATOR_CENTER = "outputs/v18/read_center/V18_CURRENT_OPERATOR_CONTROL_CENTER.md"
CURRENT_SIGNAL_GUARD = "outputs/v18/read_center/V18_CURRENT_TRADING_DAY_SIGNAL_DATE_GUARD.md"
R32A_READ_FIRST = "outputs/v18/ops/V18_32A_READ_FIRST.txt"
R31F_RUNNER = "scripts/v18/v18_31F_full_daily_trade_readiness_runner.py"
R31F_WRAPPER = "scripts/v18/run_v18_31F_full_daily_trade_readiness_runner.ps1"

RANKED = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
THEMES = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
ACCOUNT_AWARE = "outputs/v18/execution/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.csv"
TRADE_PLAN_SNAPSHOT_REPORT = "outputs/v18/read_center/V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_REPORT.md"
ACCOUNT_AWARE_REPORT = "outputs/v18/read_center/V18_31D_ACCOUNT_AWARE_MANUAL_TRADE_PLAN_REPORT.md"
FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"

OUT_SAFETY_CONTRACT = "docs/v18/V18_CODEX_SAFETY_CONTRACT.md"
OUT_TASK_TEMPLATE = "docs/v18/V18_CODEX_TASK_TEMPLATE.md"
OUT_PROJECT_CONTEXT = "outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md"
OUT_NEXT_TASK_BRIEF = "outputs/v18/ops/V18_CODEX_NEXT_TASK_BRIEF.md"
OUT_SUMMARY = "outputs/v18/ops/V18_32B_CODEX_CONTEXT_COMPRESSION_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_32B_CODEX_CONTEXT_COMPRESSION_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_32B_READ_FIRST.txt"
OUT_ERROR = "outputs/v18/read_center/V18_32B_CODEX_CONTEXT_COMPRESSION_ERROR.md"

OPTIONAL_INPUTS = [
    CURRENT_OPERATOR_CENTER,
    CURRENT_SIGNAL_GUARD,
    R32A_READ_FIRST,
]

REQUIRED_INPUTS = [
    CURRENT_DAILY,
    CURRENT_ACCOUNT_GUIDE,
    CURRENT_ACCOUNT_PLAN,
    R31F_RUNNER,
    R31F_WRAPPER,
]

GENERATED_OUTPUTS = [
    OUT_SAFETY_CONTRACT,
    OUT_TASK_TEMPLATE,
    OUT_PROJECT_CONTEXT,
    OUT_NEXT_TASK_BRIEF,
    OUT_SUMMARY,
    OUT_REPORT,
    OUT_READ_FIRST,
]

SUMMARY_FIELDS = [
    "run_id",
    "status",
    "generated_at",
    "dry_run",
    "expected_candidate_count",
    "current_ranked_candidate_count",
    "recommendation_row_count",
    "theme_classification_row_count",
    "latest_signal_date",
    "latest_relevant_signal_date",
    "latest_full_freeze_status",
    "latest_freeze_ticker_count",
    "latest_freeze_expected_count",
    "latest_freeze_coverage_status",
    "latest_freeze_missing_ticker_count",
    "current_allowed_trade_candidate_count",
    "current_allowed_trade_candidate_tickers",
    "account_state_quality",
    "template_manual_account_warning",
    "forward_return_readiness",
    "current_allowed_trade_candidates",
    "context_extraction_confidence",
    "context_extraction_warning_count",
    "latest_freeze_missing_tickers",
    "freeze_source_paths",
    "allowed_trade_source_paths",
    "auto_trade",
    "auto_sell",
    "official_decision_impact",
    "forbidden_modified",
    "missing_required_inputs",
    "missing_optional_inputs",
    "unknown_fields",
    "generated_output_count",
    "protected_state_modified",
    "ledger_modified",
    "broker_api_code_added",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "DRY_RUN",
    "EXPECTED_CANDIDATE_COUNT",
    "CURRENT_RANKED_CANDIDATE_COUNT",
    "RECOMMENDATION_ROW_COUNT",
    "THEME_CLASSIFICATION_ROW_COUNT",
    "LATEST_SIGNAL_DATE",
    "LATEST_RELEVANT_SIGNAL_DATE",
    "LATEST_FULL_FREEZE_STATUS",
    "LATEST_FREEZE_TICKER_COUNT",
    "LATEST_FREEZE_EXPECTED_COUNT",
    "LATEST_FREEZE_COVERAGE_STATUS",
    "LATEST_FREEZE_MISSING_TICKER_COUNT",
    "CURRENT_ALLOWED_TRADE_CANDIDATE_COUNT",
    "CURRENT_ALLOWED_TRADE_CANDIDATE_TICKERS",
    "ACCOUNT_STATE_QUALITY",
    "TEMPLATE_MANUAL_ACCOUNT_WARNING",
    "FORWARD_RETURN_READINESS",
    "CURRENT_ALLOWED_TRADE_CANDIDATES",
    "CONTEXT_EXTRACTION_CONFIDENCE",
    "CONTEXT_EXTRACTION_WARNING_COUNT",
    "LATEST_FREEZE_MISSING_TICKERS",
    "FREEZE_SOURCE_PATHS",
    "ALLOWED_TRADE_SOURCE_PATHS",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "FORBIDDEN_MODIFIED",
    "UNKNOWN_FIELD_COUNT",
    "MISSING_OPTIONAL_INPUT_COUNT",
    "MISSING_REQUIRED_INPUT_COUNT",
    "PROTECTED_STATE_MODIFIED",
    "LEDGER_MODIFIED",
    "BROKER_API_CODE_ADDED",
    "NEXT_TASK_BRIEF",
    "SAFETY_CONTRACT",
    "TASK_TEMPLATE",
    "PROJECT_CONTEXT_COMPACT",
]


def norm(value: object) -> str:
    return "" if value is None else str(value).strip()


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
        key = key.strip().lstrip("-").strip()
        values[key] = clean_value(value)
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


def row_count(path: Path) -> Optional[int]:
    rows, fields = read_csv_rows(path)
    if rows or fields:
        return len(rows)
    return None


def clean_value(value: object) -> str:
    text = norm(value)
    text = text.strip("`").strip()
    return text


def first_regex(texts: Sequence[str], patterns: Sequence[str]) -> str:
    for text in texts:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
            if match:
                return clean_value(match.group(1))
    return "UNKNOWN"


def first_status_value(values: Sequence[Dict[str, str]], keys: Sequence[str]) -> str:
    for data in values:
        for key in keys:
            if key in data and norm(data[key]):
                return clean_value(data[key])
    return "UNKNOWN"


def infer_forward_return_readiness(texts: Sequence[str]) -> str:
    joined = "\n".join(texts).upper()
    if "FORWARD_RETURN_NOT_READY" in joined or "WAIT_FOR_FUTURE_PRICE_DATA" in joined:
        return "NOT_READY_WAIT_FOR_FUTURE_PRICE_DATA"
    if "FORWARD" in joined and "READY" in joined:
        return "READY"
    return "UNKNOWN"


def infer_latest_full_freeze_status(values: Sequence[Dict[str, str]], texts: Sequence[str], preferred_date: str) -> str:
    freeze_rows = first_regex(texts, [r"Latest full signal freeze rows:\s*`?([^`\r\n]+)`?"])
    if freeze_rows != "UNKNOWN":
        return f"PRESENT date={preferred_date} count={freeze_rows}"
    date_value = first_status_value(values, ["LATEST_FULL_SIGNAL_FREEZE_DATE", "LATEST_FULL_FREEZE_DATE"])
    count_value = first_status_value(
        values,
        ["LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT", "LATEST_FULL_FREEZE_TICKER_COUNT", "LATEST_FULL_SIGNAL_FREEZE_ROWS"],
    )
    if date_value != "UNKNOWN" or count_value != "UNKNOWN":
        return f"PRESENT date={date_value} count={count_value}"
    return "UNKNOWN"


def infer_current_allowed_trade_candidates(account_plan_text: str, account_rows: List[Dict[str, str]]) -> str:
    candidates: List[str] = []
    for row in account_rows:
        joined = " ".join(norm(v).upper() for v in row.values())
        ticker = norm(row.get("ticker") or row.get("TICKER"))
        if ticker and ("ACCOUNT_ELIGIBLE" in joined or "BUY_CANDIDATE" in joined or "ALLOWED" in joined):
            if "BLOCKED" not in joined and "NOT_ALLOWED" not in joined:
                candidates.append(ticker)
    if candidates:
        return ";".join(sorted(set(candidates)))
    if re.search(r"Today's Account-Eligible Manual Buy Candidates\s*\r?\n_None\._", account_plan_text, re.IGNORECASE):
        return "0"
    if re.search(r"Today's Final Account-Aware Candidates\s*\r?\n_None\._", account_plan_text, re.IGNORECASE):
        return "0"
    return "UNKNOWN"


def join_paths(paths: Sequence[str]) -> str:
    cleaned = [p for p in (clean_value(path) for path in paths) if p]
    return ";".join(cleaned) if cleaned else "UNKNOWN"


def extract_ticker_set(rows: Sequence[Dict[str, str]], field: str = "ticker") -> List[str]:
    return sorted({clean_value(row.get(field)) for row in rows if clean_value(row.get(field))})


def audit_freeze_coverage(root: Path, latest_signal_date: str, expected_candidate_count: int) -> Dict[str, str]:
    freeze_rows, freeze_fields = read_csv_rows(root / FREEZE_LEDGER)
    freeze_source_paths = [FREEZE_LEDGER]
    if not freeze_rows:
        return {
            "latest_freeze_ticker_count": "UNKNOWN",
            "latest_freeze_expected_count": str(expected_candidate_count),
            "latest_freeze_coverage_status": "MISSING_LEDGER",
            "latest_freeze_missing_ticker_count": "UNKNOWN",
            "latest_freeze_missing_tickers": "UNKNOWN",
            "latest_full_freeze_status": "UNKNOWN",
            "freeze_source_paths": join_paths(freeze_source_paths),
        }

    relevant_rows = [row for row in freeze_rows if clean_value(row.get("signal_date")) == latest_signal_date]
    if not relevant_rows:
        return {
            "latest_freeze_ticker_count": "UNKNOWN",
            "latest_freeze_expected_count": str(expected_candidate_count),
            "latest_freeze_coverage_status": "MISSING_LEDGER",
            "latest_freeze_missing_ticker_count": "UNKNOWN",
            "latest_freeze_missing_tickers": "UNKNOWN",
            "latest_full_freeze_status": f"NO_LEDGER_ROWS_FOR_SIGNAL_DATE date={latest_signal_date}",
            "freeze_source_paths": join_paths(freeze_source_paths),
        }

    freeze_tickers = extract_ticker_set(relevant_rows)
    ranked_rows, _ = read_csv_rows(root / RANKED)
    ranked_tickers = extract_ticker_set(ranked_rows)
    freeze_set = set(freeze_tickers)
    ranked_set = set(ranked_tickers)
    missing = sorted(ranked_set - freeze_set)
    extra = sorted(freeze_set - ranked_set)
    freeze_count = str(len(relevant_rows))
    unique_count = len(freeze_tickers)
    if missing and extra:
        coverage_status = "PARTIAL_MISSING_EXTRA_TICKERS"
    elif missing:
        coverage_status = "PARTIAL_MISSING"
    elif extra:
        coverage_status = "EXTRA_TICKERS"
    elif unique_count == expected_candidate_count:
        coverage_status = "FULL_MATCH"
    else:
        coverage_status = "UNKNOWN"

    if coverage_status == "FULL_MATCH":
        full_status = f"FULL_FREEZE_COVERAGE date={latest_signal_date} count={freeze_count} expected={expected_candidate_count}"
    elif coverage_status in {"PARTIAL_MISSING", "PARTIAL_MISSING_EXTRA_TICKERS"}:
        full_status = (
            f"PARTIAL_FREEZE_COVERAGE date={latest_signal_date} count={freeze_count} "
            f"expected={expected_candidate_count} missing={len(missing)}"
        )
    elif coverage_status == "EXTRA_TICKERS":
        full_status = (
            f"EXTRA_FREEZE_TICKERS date={latest_signal_date} count={freeze_count} "
            f"expected={expected_candidate_count} extra={len(extra)}"
        )
    else:
        full_status = f"FREEZE_COVERAGE_UNKNOWN date={latest_signal_date} count={freeze_count} expected={expected_candidate_count}"

    return {
        "latest_freeze_ticker_count": freeze_count,
        "latest_freeze_expected_count": str(expected_candidate_count),
        "latest_freeze_coverage_status": coverage_status,
        "latest_freeze_missing_ticker_count": str(len(missing)),
        "latest_freeze_missing_tickers": ";".join(missing) if missing else "NONE",
        "latest_full_freeze_status": full_status,
        "freeze_source_paths": join_paths(freeze_source_paths),
    }


def audit_allowed_candidates(root: Path) -> Dict[str, str]:
    source_texts = {
        TRADE_PLAN_SNAPSHOT_REPORT: read_text(root / TRADE_PLAN_SNAPSHOT_REPORT),
        ACCOUNT_AWARE_REPORT: read_text(root / ACCOUNT_AWARE_REPORT),
        CURRENT_ACCOUNT_PLAN: read_text(root / CURRENT_ACCOUNT_PLAN),
    }
    source_paths = [path for path, text in source_texts.items() if text]
    snapshot_text = source_texts[TRADE_PLAN_SNAPSHOT_REPORT]
    account_plan_text = source_texts[CURRENT_ACCOUNT_PLAN]
    account_aware_text = source_texts[ACCOUNT_AWARE_REPORT]

    count = "UNKNOWN"
    tickers = "UNKNOWN"
    if snapshot_text:
        count = first_regex([snapshot_text], [r"ACCOUNT_TRADE_ALLOWED_COUNT:\s*`?([^`\r\n]+)`?", r"Account-Tra[\w-]* Allowed Count:\s*`?([^`\r\n]+)`?"])
        if count == "UNKNOWN":
            count = first_regex([snapshot_text], [r"Today's Account-Eligible Manual Buy Candidates\s*.*?_None\._"])
        if count == "0":
            tickers = "NONE"
    if count == "UNKNOWN" and account_plan_text:
        if re.search(r"Today's Account-Eligible Manual Buy Candidates\s*\r?\n_None\._", account_plan_text, re.IGNORECASE):
            count = "0"
            tickers = "NONE"
    if count == "UNKNOWN" and account_aware_text:
        if re.search(r"\bBLOCKED_BY_OPERATOR_STATE\b", account_aware_text) and not re.search(r"\bACCOUNT_TRADE_ALLOWED\b", account_aware_text):
            # Don't infer zero from blocked status alone.
            count = "UNKNOWN"
    if count == "UNKNOWN":
        tickers = "UNKNOWN"
    return {
        "current_allowed_trade_candidate_count": count,
        "current_allowed_trade_candidate_tickers": tickers,
        "allowed_trade_source_paths": join_paths(source_paths),
    }


def make_safety_contract() -> str:
    return """# V18 Codex Safety Contract

This file is the stable safety contract for future V18 Codex work.

## Hard Safety Rules
- No broker/API/trading/order execution code.
- `AUTO_TRADE` and `AUTO_SELL` must remain `DISABLED`.
- `OFFICIAL_DECISION_IMPACT` must remain `NONE` unless the user explicitly asks otherwise in a future separate task.
- Do not modify ranking, factor, recommendation, buyability, sizing, cost, or account-aware logic unless explicitly scoped.
- Do not modify protected state or ledgers unless explicitly scoped and backed up.
- No external fetch unless explicitly scoped.

## Development Rules
- Always read this safety contract before touching V18 code.
- Always produce parse, compile, and run validation appropriate to the changed files.
- Always create or update `READ_FIRST` for new V18 task steps.
- Prefer small, scoped patches.
- Preserve auditability, stable field names, and clear status codes.
- Do not hide warnings by printing `OK`.
- If a warning is expected, label it as `WARN` with the reason.

## Current Safety Baseline
- Broker connection: `NOT_EXECUTED`
- Order placement: `NOT_EXECUTED`
- External trading integration: `NOT_EXECUTED`
- Manual research guidance only.
"""


def make_task_template() -> str:
    return """# V18 Codex Task Template

## Use model
Use model: gpt-5.5

## Repository
`D:\\us-tech-quant`

## First read
1. `docs/v18/V18_CODEX_SAFETY_CONTRACT.md`
2. `docs/v18/V18_CODEX_TASK_TEMPLATE.md`
3. `outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md`
4. `outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md`
5. `outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`

## Task
Describe the exact V18 task, version step, and intended output.

## Modify only
List the exact scripts, docs, or generated outputs that may be modified.

## Create outputs
List every expected output file.

## Do not
- Do not add broker/API/trading/order execution code.
- Do not enable `AUTO_TRADE` or `AUTO_SELL`.
- Do not change `OFFICIAL_DECISION_IMPACT` from `NONE` unless explicitly scoped.
- Do not modify protected state, ledgers, or core ranking/factor/recommendation/buyability/sizing/cost/account-aware logic unless explicitly scoped.
- Do not run heavy daily pipeline steps unless explicitly scoped.
- Do not infer from archived stale files unless asked.

## Validation
List exact compile, parse, dry-run, live-run, and audit checks to execute.

## Success criteria
List exact status codes, output files, row counts, safety fields, and warning behavior expected.

## Run commands
```powershell
python -m py_compile <script>
powershell -NoProfile -ExecutionPolicy Bypass -File <wrapper> -DryRun
powershell -NoProfile -ExecutionPolicy Bypass -File <wrapper>
```

## Final response requirements
Report files changed, status, key fields, warnings or unknowns, validation results, and confirmation that protected trading/state logic was not modified.
"""


def make_next_task_brief() -> str:
    return """Before changing V18 code, first read:
1. docs/v18/V18_CODEX_SAFETY_CONTRACT.md
2. docs/v18/V18_CODEX_TASK_TEMPLATE.md
3. outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md
4. outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md
5. outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md
"""


def make_project_context(fields: Dict[str, str], unknowns: Sequence[str], missing_optional: Sequence[str]) -> str:
    warning_lines = [
        "- Manual account state is template/manual and not broker data.",
        "- Forward-return extraction is not ready until future price bars exist.",
        "- Non-trading-day signal-date guard may reuse the latest supported signal date.",
    ]
    if unknowns:
        warning_lines.append(f"- UNKNOWN extracted fields: `{';'.join(unknowns)}`.")
    if missing_optional:
        warning_lines.append(f"- Missing optional inputs: `{';'.join(missing_optional)}`.")
    return f"""# V18 Project Context Compact

## Purpose
V18 is the daily quant/trade-readiness pipeline for manual research review. It is not a live-trading system.

## Current Daily Entrypoint
- Primary runner: `scripts/v18/run_v18_31F_full_daily_trade_readiness_runner.ps1`
- Python runner: `scripts/v18/v18_31F_full_daily_trade_readiness_runner.py`

## Current Snapshot
- Expected candidate count: `{fields['expected_candidate_count']}`
- Ranked candidates: `{fields['current_ranked_candidate_count']}`
- Recommendation rows: `{fields['recommendation_row_count']}`
- Theme rows: `{fields['theme_classification_row_count']}`
- Latest signal date: `{fields['latest_signal_date']}`
- Latest relevant signal date: `{fields['latest_relevant_signal_date']}`
- Latest freeze coverage status: `{fields['latest_freeze_coverage_status']}`
- Latest freeze ticker count: `{fields['latest_freeze_ticker_count']}`
- Latest freeze expected count: `{fields['latest_freeze_expected_count']}`
- Latest freeze missing tickers: `{fields['latest_freeze_missing_tickers']}`
- Current allowed trade candidates: `{fields['current_allowed_trade_candidates']}`
- Current allowed trade candidate count: `{fields['current_allowed_trade_candidate_count']}`
- Current allowed trade candidate tickers: `{fields['current_allowed_trade_candidate_tickers']}`
- Account state quality: `{fields['account_state_quality']}`
- Forward-return readiness: `{fields['forward_return_readiness']}`

## Key Reports To Read
- `outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md`
- `outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`
- `outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md`
- `outputs/v18/read_center/V18_31E_DAILY_TRADE_PLAN_SNAPSHOT_REPORT.md`
- `outputs/v18/read_center/V18_CURRENT_OPERATOR_CONTROL_CENTER.md`
- `outputs/v18/read_center/V18_CURRENT_TRADING_DAY_SIGNAL_DATE_GUARD.md`

## Known Warnings
{chr(10).join(warning_lines)}
- Context extraction confidence: `{fields['context_extraction_confidence']}`
- Context extraction warning count: `{fields['context_extraction_warning_count']}`
- Freeze source paths: `{fields['freeze_source_paths']}`
- Allowed-trade source paths: `{fields['allowed_trade_source_paths']}`

## Safety State
- `AUTO_TRADE: {fields['auto_trade']}`
- `AUTO_SELL: {fields['auto_sell']}`
- `OFFICIAL_DECISION_IMPACT: {fields['official_decision_impact']}`
- `FORBIDDEN_MODIFIED: {fields['forbidden_modified']}`
- No broker API, no order placement, no live trading, no account login, no external trading integration.

## Development Rule
Use this compact context, `docs/v18/V18_CODEX_SAFETY_CONTRACT.md`, and `docs/v18/V18_CODEX_TASK_TEMPLATE.md` before touching code.

Do not infer from archived stale files unless asked.

Prefer current files over historical reports.
"""


def make_report(fields: Dict[str, str], unknowns: Sequence[str], missing_required: Sequence[str], missing_optional: Sequence[str], generated_at: str, run_id: str, status: str) -> str:
    def bullet(name: str, value: str) -> str:
        return f"- {name}: `{value}`"

    field_lines = [
        bullet("Expected candidate count", fields["expected_candidate_count"]),
        bullet("Current ranked candidate count", fields["current_ranked_candidate_count"]),
        bullet("Recommendation row count", fields["recommendation_row_count"]),
        bullet("Theme classification row count", fields["theme_classification_row_count"]),
        bullet("Latest signal date", fields["latest_signal_date"]),
        bullet("Latest relevant signal date", fields["latest_relevant_signal_date"]),
        bullet("Latest full freeze status", fields["latest_full_freeze_status"]),
        bullet("Latest freeze coverage status", fields["latest_freeze_coverage_status"]),
        bullet("Latest freeze ticker count", fields["latest_freeze_ticker_count"]),
        bullet("Latest freeze expected count", fields["latest_freeze_expected_count"]),
        bullet("Latest freeze missing tickers", fields["latest_freeze_missing_tickers"]),
        bullet("Account state quality", fields["account_state_quality"]),
        bullet("Template/manual account warning", fields["template_manual_account_warning"]),
        bullet("Forward-return readiness", fields["forward_return_readiness"]),
        bullet("Current allowed trade candidates", fields["current_allowed_trade_candidates"]),
        bullet("Current allowed trade candidate count", fields["current_allowed_trade_candidate_count"]),
        bullet("Current allowed trade candidate tickers", fields["current_allowed_trade_candidate_tickers"]),
        bullet("Context extraction confidence", fields["context_extraction_confidence"]),
        bullet("Context extraction warning count", fields["context_extraction_warning_count"]),
        bullet("AUTO_TRADE", fields["auto_trade"]),
        bullet("AUTO_SELL", fields["auto_sell"]),
        bullet("OFFICIAL_DECISION_IMPACT", fields["official_decision_impact"]),
        bullet("FORBIDDEN_MODIFIED", fields["forbidden_modified"]),
    ]
    return f"""# V18.32B Codex Context Compression Report

## 1. Final Status
STATUS: {status}

## 2. Run
- RUN_ID: `{run_id}`
- GENERATED_AT: `{generated_at}`
- MODE: `{MODE_LIVE}`

## 3. Extracted Fields
{chr(10).join(field_lines)}

## 4. UNKNOWN Fields
{chr(10).join(f'- `{item}`' for item in unknowns) if unknowns else '_None._'}

## 5. Missing Inputs
- Required: `{';'.join(missing_required) if missing_required else 'NONE'}`
- Optional: `{';'.join(missing_optional) if missing_optional else 'NONE'}`

## 6. Source Paths
- Freeze: `{fields['freeze_source_paths']}`
- Allowed trade: `{fields['allowed_trade_source_paths']}`

## 7. Generated Context Files
{chr(10).join(f'- `{item}`' for item in GENERATED_OUTPUTS)}

## 8. Safety Confirmation
- Protected state modified: `FALSE`
- Ledgers modified: `FALSE`
- Broker/API/trading/order code added: `FALSE`
- Heavy daily pipeline steps executed: `FALSE`
"""


def make_read_first(fields: Dict[str, str], unknowns: Sequence[str], missing_required: Sequence[str], missing_optional: Sequence[str], run_id: str, generated_at: str, status: str, dry_run: bool) -> str:
    values = {
        "STATUS": status,
        "MODE": MODE_DRY if dry_run else MODE_LIVE,
        "RUN_ID": run_id,
        "DRY_RUN": bool_text(dry_run),
        "EXPECTED_CANDIDATE_COUNT": fields["expected_candidate_count"],
        "CURRENT_RANKED_CANDIDATE_COUNT": fields["current_ranked_candidate_count"],
        "RECOMMENDATION_ROW_COUNT": fields["recommendation_row_count"],
        "THEME_CLASSIFICATION_ROW_COUNT": fields["theme_classification_row_count"],
        "LATEST_SIGNAL_DATE": fields["latest_signal_date"],
        "LATEST_RELEVANT_SIGNAL_DATE": fields["latest_relevant_signal_date"],
        "LATEST_FULL_FREEZE_STATUS": fields["latest_full_freeze_status"],
        "LATEST_FREEZE_TICKER_COUNT": fields["latest_freeze_ticker_count"],
        "LATEST_FREEZE_EXPECTED_COUNT": fields["latest_freeze_expected_count"],
        "LATEST_FREEZE_COVERAGE_STATUS": fields["latest_freeze_coverage_status"],
        "LATEST_FREEZE_MISSING_TICKER_COUNT": fields["latest_freeze_missing_ticker_count"],
        "CURRENT_ALLOWED_TRADE_CANDIDATE_COUNT": fields["current_allowed_trade_candidate_count"],
        "CURRENT_ALLOWED_TRADE_CANDIDATE_TICKERS": fields["current_allowed_trade_candidate_tickers"],
        "ACCOUNT_STATE_QUALITY": fields["account_state_quality"],
        "TEMPLATE_MANUAL_ACCOUNT_WARNING": fields["template_manual_account_warning"],
        "FORWARD_RETURN_READINESS": fields["forward_return_readiness"],
        "CURRENT_ALLOWED_TRADE_CANDIDATES": fields["current_allowed_trade_candidates"],
        "CONTEXT_EXTRACTION_CONFIDENCE": fields["context_extraction_confidence"],
        "CONTEXT_EXTRACTION_WARNING_COUNT": fields["context_extraction_warning_count"],
        "LATEST_FREEZE_MISSING_TICKERS": fields["latest_freeze_missing_tickers"],
        "FREEZE_SOURCE_PATHS": fields["freeze_source_paths"],
        "ALLOWED_TRADE_SOURCE_PATHS": fields["allowed_trade_source_paths"],
        "AUTO_TRADE": fields["auto_trade"],
        "AUTO_SELL": fields["auto_sell"],
        "OFFICIAL_DECISION_IMPACT": fields["official_decision_impact"],
        "FORBIDDEN_MODIFIED": fields["forbidden_modified"],
        "UNKNOWN_FIELD_COUNT": str(len(unknowns)),
        "MISSING_OPTIONAL_INPUT_COUNT": str(len(missing_optional)),
        "MISSING_REQUIRED_INPUT_COUNT": str(len(missing_required)),
        "PROTECTED_STATE_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "BROKER_API_CODE_ADDED": "FALSE",
        "NEXT_TASK_BRIEF": OUT_NEXT_TASK_BRIEF,
        "SAFETY_CONTRACT": OUT_SAFETY_CONTRACT,
        "TASK_TEMPLATE": OUT_TASK_TEMPLATE,
        "PROJECT_CONTEXT_COMPACT": OUT_PROJECT_CONTEXT,
    }
    lines = [f"{key}: {values.get(key, '')}" for key in READ_FIRST_FIELDS]
    lines.append(f"GENERATED_AT: {generated_at}")
    if unknowns:
        lines.append(f"UNKNOWN_FIELDS: {';'.join(unknowns)}")
    if missing_optional:
        lines.append(f"MISSING_OPTIONAL_INPUTS: {';'.join(missing_optional)}")
    if missing_required:
        lines.append(f"MISSING_REQUIRED_INPUTS: {';'.join(missing_required)}")
    lines.append(f"CONTEXT_EXTRACTION_WARNINGS: {fields['context_extraction_warnings']}")
    return "\n".join(lines) + "\n"


def extract_fields(root: Path) -> Tuple[Dict[str, str], List[str], List[str], List[str]]:
    input_paths = {
        "daily": root / CURRENT_DAILY,
        "account_guide": root / CURRENT_ACCOUNT_GUIDE,
        "account_plan": root / CURRENT_ACCOUNT_PLAN,
        "operator_center": root / CURRENT_OPERATOR_CENTER,
        "signal_guard": root / CURRENT_SIGNAL_GUARD,
        "r32a_read_first": root / R32A_READ_FIRST,
        "r31f_runner": root / R31F_RUNNER,
        "r31f_wrapper": root / R31F_WRAPPER,
    }
    texts = {name: read_text(path) for name, path in input_paths.items()}
    status_values = [
        read_status_file(root / R32A_READ_FIRST),
        read_status_file(root / CURRENT_OPERATOR_CENTER),
    ]
    missing_required = [item for item in REQUIRED_INPUTS if not (root / item).exists()]
    missing_optional = [item for item in OPTIONAL_INPUTS if not (root / item).exists()]

    ranked_count = row_count(root / RANKED)
    recommendation_count = row_count(root / RECOMMENDATIONS)
    theme_count = row_count(root / THEMES)
    account_rows, _account_fields = read_csv_rows(root / ACCOUNT_AWARE)

    all_texts = [texts[name] for name in texts]
    latest_signal_date = first_regex(all_texts, [r"Recommended signal date:\s*`?([^`\r\n]+)`?", r"RECOMMENDED_SIGNAL_DATE:\s*([^\r\n]+)", r"LATEST_FULL_SIGNAL_FREEZE_DATE:\s*([^\r\n]+)", r"Latest full freeze signal date:\s*`?([^`\r\n]+)`?"])
    expected_candidate_count = ranked_count if ranked_count is not None else 0
    freeze_audit = audit_freeze_coverage(root, latest_signal_date, expected_candidate_count)
    allowed_audit = audit_allowed_candidates(root)
    fields = {
        "expected_candidate_count": str(expected_candidate_count) if ranked_count is not None else "UNKNOWN",
        "current_ranked_candidate_count": str(ranked_count) if ranked_count is not None else first_regex(all_texts, [r"Ranked rows:\s*`?([^`\r\n]+)`?", r"CURRENT_RANKED_CANDIDATE_ROW_COUNT:\s*([^\r\n]+)"]),
        "recommendation_row_count": str(recommendation_count) if recommendation_count is not None else first_regex(all_texts, [r"Recommendation rows:\s*`?([^`\r\n]+)`?", r"CURRENT_RECOMMENDATION_ROW_COUNT:\s*([^\r\n]+)"]),
        "theme_classification_row_count": str(theme_count) if theme_count is not None else first_regex(all_texts, [r"Theme rows:\s*`?([^`\r\n]+)`?", r"THEME_CLASSIFICATION_ROW_COUNT:\s*([^\r\n]+)"]),
        "latest_signal_date": latest_signal_date,
        "latest_relevant_signal_date": latest_signal_date,
        "latest_full_freeze_status": freeze_audit["latest_full_freeze_status"],
        "latest_freeze_ticker_count": freeze_audit["latest_freeze_ticker_count"],
        "latest_freeze_expected_count": freeze_audit["latest_freeze_expected_count"],
        "latest_freeze_coverage_status": freeze_audit["latest_freeze_coverage_status"],
        "latest_freeze_missing_ticker_count": freeze_audit["latest_freeze_missing_ticker_count"],
        "latest_freeze_missing_tickers": freeze_audit["latest_freeze_missing_tickers"],
        "freeze_source_paths": freeze_audit["freeze_source_paths"],
        "current_allowed_trade_candidate_count": allowed_audit["current_allowed_trade_candidate_count"],
        "current_allowed_trade_candidate_tickers": allowed_audit["current_allowed_trade_candidate_tickers"],
        "allowed_trade_source_paths": allowed_audit["allowed_trade_source_paths"],
        "account_state_quality": first_status_value(status_values, ["ACCOUNT_STATE_QUALITY", "ACCOUNT_STATE_QUALITY_FLAG"]),
        "template_manual_account_warning": first_status_value(status_values, ["TEMPLATE_EMPTY_ACCOUNT"]),
        "forward_return_readiness": infer_forward_return_readiness(all_texts),
        "current_allowed_trade_candidates": infer_current_allowed_trade_candidates(texts["account_plan"] + "\n" + texts["daily"], account_rows),
        "auto_trade": first_status_value(status_values, ["AUTO_TRADE"]),
        "auto_sell": first_status_value(status_values, ["AUTO_SELL"]),
        "official_decision_impact": first_status_value(status_values, ["OFFICIAL_DECISION_IMPACT"]),
        "forbidden_modified": first_status_value(status_values, ["FORBIDDEN_MODIFIED"]),
    }
    for key in ("auto_trade", "auto_sell", "official_decision_impact", "forbidden_modified"):
        if fields[key] == "UNKNOWN":
            fields[key] = first_regex(all_texts, [rf"{key.replace('_', r'[_\\s-]*')}:\s*`?([^`\r\n]+)`?"])
    warning_count = 0
    warnings: List[str] = []
    if freeze_audit["latest_freeze_coverage_status"] != "FULL_MATCH":
        warning_count += 1
        warnings.append(f"FREEZE_COVERAGE_{freeze_audit['latest_freeze_coverage_status']}")
    if fields["current_allowed_trade_candidate_count"] == "UNKNOWN":
        warning_count += 1
        warnings.append("ALLOWED_CANDIDATE_COUNT_UNKNOWN")
    unknowns = [key for key, value in fields.items() if not norm(value) or value == "UNKNOWN"]
    fields["context_extraction_warning_count"] = str(warning_count)
    fields["context_extraction_confidence"] = "MEDIUM" if warning_count else "HIGH"
    fields["context_extraction_warnings"] = ";".join(warnings) if warnings else "NONE"
    return fields, unknowns, missing_required, missing_optional


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    now = dt.datetime.now().replace(microsecond=0)
    generated_at = now.isoformat()
    run_id = f"V18_32B_{now.strftime('%Y%m%d_%H%M%S')}"

    fields, unknowns, missing_required, missing_optional = extract_fields(root)
    status = STATUS_WARN if unknowns or missing_optional or fields.get("context_extraction_warning_count", "0") != "0" else STATUS_OK
    if missing_required:
        status = STATUS_WARN

    summary_row = {
        "run_id": run_id,
        "status": status,
        "generated_at": generated_at,
        "dry_run": bool_text(args.dry_run),
        "expected_candidate_count": fields["expected_candidate_count"],
        "current_ranked_candidate_count": fields["current_ranked_candidate_count"],
        "recommendation_row_count": fields["recommendation_row_count"],
        "theme_classification_row_count": fields["theme_classification_row_count"],
        "latest_signal_date": fields["latest_signal_date"],
        "latest_relevant_signal_date": fields["latest_relevant_signal_date"],
        "latest_full_freeze_status": fields["latest_full_freeze_status"],
        "latest_freeze_ticker_count": fields["latest_freeze_ticker_count"],
        "latest_freeze_expected_count": fields["latest_freeze_expected_count"],
        "latest_freeze_coverage_status": fields["latest_freeze_coverage_status"],
        "latest_freeze_missing_ticker_count": fields["latest_freeze_missing_ticker_count"],
        "current_allowed_trade_candidate_count": fields["current_allowed_trade_candidate_count"],
        "current_allowed_trade_candidate_tickers": fields["current_allowed_trade_candidate_tickers"],
        "account_state_quality": fields["account_state_quality"],
        "template_manual_account_warning": fields["template_manual_account_warning"],
        "forward_return_readiness": fields["forward_return_readiness"],
        "current_allowed_trade_candidates": fields["current_allowed_trade_candidates"],
        "context_extraction_confidence": fields["context_extraction_confidence"],
        "context_extraction_warning_count": fields["context_extraction_warning_count"],
        "latest_freeze_missing_tickers": fields["latest_freeze_missing_tickers"],
        "freeze_source_paths": fields["freeze_source_paths"],
        "allowed_trade_source_paths": fields["allowed_trade_source_paths"],
        "auto_trade": fields["auto_trade"],
        "auto_sell": fields["auto_sell"],
        "official_decision_impact": fields["official_decision_impact"],
        "forbidden_modified": fields["forbidden_modified"],
        "missing_required_inputs": ";".join(missing_required),
        "missing_optional_inputs": ";".join(missing_optional),
        "unknown_fields": ";".join(unknowns),
        "generated_output_count": str(len(GENERATED_OUTPUTS)),
        "protected_state_modified": "FALSE",
        "ledger_modified": "FALSE",
        "broker_api_code_added": "FALSE",
    }

    write_text(root / OUT_SAFETY_CONTRACT, make_safety_contract())
    write_text(root / OUT_TASK_TEMPLATE, make_task_template())
    write_text(root / OUT_PROJECT_CONTEXT, make_project_context(fields, unknowns, missing_optional))
    write_text(root / OUT_NEXT_TASK_BRIEF, make_next_task_brief())
    write_csv(root / OUT_SUMMARY, [summary_row], SUMMARY_FIELDS)
    write_text(root / OUT_REPORT, make_report(fields, unknowns, missing_required, missing_optional, generated_at, run_id, status))
    write_text(root / OUT_READ_FIRST, make_read_first(fields, unknowns, missing_required, missing_optional, run_id, generated_at, status, args.dry_run))

    print(f"STATUS: {status}")
    print(f"RUN_ID: {run_id}")
    print(f"DRY_RUN: {bool_text(args.dry_run)}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    print(f"UNKNOWN_FIELD_COUNT: {len(unknowns)}")
    print(f"MISSING_OPTIONAL_INPUT_COUNT: {len(missing_optional)}")
    print("AUTO_TRADE: " + fields["auto_trade"])
    print("AUTO_SELL: " + fields["auto_sell"])
    print("OFFICIAL_DECISION_IMPACT: " + fields["official_decision_impact"])
    print("FORBIDDEN_MODIFIED: " + fields["forbidden_modified"])
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build V18.32B Codex context compression pack.")
    parser.add_argument("--root", default="D:\\us-tech-quant")
    parser.add_argument("--dry-run", action="store_true")
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
            "# V18.32B Codex Context Compression Error\n\n"
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
