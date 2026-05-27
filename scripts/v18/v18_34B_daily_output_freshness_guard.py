from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
REPORT_PATH = ROOT_DEFAULT / "outputs/v18/read_center/V18_34B_DAILY_OUTPUT_FRESHNESS_REPORT.md"
CURRENT_PATH = ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_DAILY_OUTPUT_FRESHNESS.md"
SUMMARY_PATH = ROOT_DEFAULT / "outputs/v18/ops/V18_34B_DAILY_OUTPUT_FRESHNESS_SUMMARY.csv"
READ_FIRST_PATH = ROOT_DEFAULT / "outputs/v18/ops/V18_34B_READ_FIRST.txt"

REQUIRED_FILES = [
    ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md",
    ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_RUNBOOK_CN.md",
    ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md",
    ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md",
    ROOT_DEFAULT / "outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md",
]

OPTIONAL_FILES = [
    ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_STORAGE_CLEANUP.md",
    ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_FREEZE_COVERAGE_REPAIR.md",
    ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md",
    ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md",
]

STATUS_OK = "OK_V18_34B_DAILY_OUTPUT_FRESHNESS_READY"
STATUS_WARN = "WARN_V18_34B_DAILY_OUTPUT_FRESHNESS_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_34B_DAILY_OUTPUT_FRESHNESS_FAILED"


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\ufeff", "").strip()
    if text.lower() == "null":
        return ""
    return text


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def modified_time(path: Path) -> Optional[dt.datetime]:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime).replace(microsecond=0)
    except OSError:
        return None


def age_hours(path: Path, now: dt.datetime) -> Optional[float]:
    mt = modified_time(path)
    if mt is None:
        return None
    return max(0.0, (now - mt).total_seconds() / 3600.0)


def parse_key_values(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not text:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^-?\s*`?([^:`]+?)`?:\s*`?(.+?)`?$", line)
        if m:
            out[clean(m.group(1))] = clean(m.group(2))
    return out


def first_match(text: str, patterns: Sequence[str]) -> str:
    if not text:
        return ""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            if m.groups():
                return clean(m.group(1))
            return clean(m.group(0))
    return ""


def extract_int(text: str, patterns: Sequence[str]) -> str:
    value = first_match(text, patterns)
    return value if value else "UNKNOWN"


def extract_float(text: str, patterns: Sequence[str]) -> str:
    value = first_match(text, patterns)
    return value if value else "UNKNOWN"


def parse_report_fields(root: Path) -> Dict[str, str]:
    homepage = read_text(REQUIRED_FILES[0])
    runbook = read_text(REQUIRED_FILES[1])
    context = read_text(REQUIRED_FILES[2])
    readiness = read_text(REQUIRED_FILES[3])
    compact = read_text(REQUIRED_FILES[4])
    storage = read_text(ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_STORAGE_CLEANUP.md")
    fresh_33a = read_text(ROOT_DEFAULT / "outputs/v18/ops/V18_33A_READ_FIRST.txt")
    fresh_33b = read_text(ROOT_DEFAULT / "outputs/v18/ops/V18_33B_READ_FIRST.txt")
    trust = read_text(ROOT_DEFAULT / "outputs/v18/ops/V18_19A_READ_FIRST.txt")

    homepage_kv = parse_key_values(homepage)
    runbook_kv = parse_key_values(runbook)
    context_kv = parse_key_values(context)
    readiness_kv = parse_key_values(readiness)
    compact_kv = parse_key_values(compact)
    storage_kv = parse_key_values(storage)
    trust_kv = parse_key_values(trust)
    read_first_33a = parse_key_values(fresh_33a)
    read_first_33b = parse_key_values(fresh_33b)

    latest_signal_date = (
        homepage_kv.get("LATEST_SIGNAL_DATE")
        or runbook_kv.get("LATEST_SIGNAL_DATE")
        or context_kv.get("Signal date")
        or context_kv.get("Signal Date")
        or readiness_kv.get("Recommended signal date")
        or "UNKNOWN"
    )
    candidate_count = (
        homepage_kv.get("CANDIDATE_COUNT")
        or runbook_kv.get("候选数")
        or context_kv.get("Expected candidates")
        or readiness_kv.get("Ranked rows")
        or "UNKNOWN"
    )
    expected_candidate_count = (
        homepage_kv.get("CANDIDATE_COUNT")
        or runbook_kv.get("候选数")
        or context_kv.get("Expected candidates")
        or "UNKNOWN"
    )
    freeze_ticker_count = (
        homepage_kv.get("FREEZE_TICKER_COUNT")
        or runbook_kv.get("冻结 ticker 数")
        or context_kv.get("Freeze counts")
        or readiness_kv.get("Latest full signal freeze rows")
        or compact_kv.get("Latest freeze ticker count")
        or "UNKNOWN"
    )
    freeze_coverage_status = (
        homepage_kv.get("FREEZE_COVERAGE_STATUS")
        or runbook_kv.get("冻结覆盖状态")
        or context_kv.get("Freeze coverage")
        or compact_kv.get("Latest freeze coverage status")
        or "UNKNOWN"
    )
    allowed_trade_candidate_count = (
        homepage_kv.get("ALLOWED_TRADE_COUNT")
        or runbook_kv.get("当前允许交易候选数")
        or readiness_kv.get("Allowed trade candidates")
        or context_kv.get("Allowed trade candidates")
        or compact_kv.get("Current allowed trade candidates")
        or "UNKNOWN"
    )
    account_state_quality = (
        homepage_kv.get("ACCOUNT_STATE_QUALITY")
        or runbook_kv.get("账户状态质量")
        or readiness_kv.get("Account state quality")
        or compact_kv.get("Account state quality")
        or "UNKNOWN"
    )
    auto_trade = (
        homepage_kv.get("AUTO_TRADE")
        or runbook_kv.get("AUTO_TRADE")
        or readiness_kv.get("AUTO_TRADE")
        or compact_kv.get("AUTO_TRADE")
        or trust_kv.get("AUTO_TRADE")
        or "UNKNOWN"
    )
    auto_sell = (
        homepage_kv.get("AUTO_SELL")
        or runbook_kv.get("AUTO_SELL")
        or readiness_kv.get("AUTO_SELL")
        or compact_kv.get("AUTO_SELL")
        or trust_kv.get("AUTO_SELL")
        or "UNKNOWN"
    )
    official_decision_impact = (
        homepage_kv.get("OFFICIAL_DECISION_IMPACT")
        or runbook_kv.get("OFFICIAL_DECISION_IMPACT")
        or readiness_kv.get("OFFICIAL_DECISION_IMPACT")
        or compact_kv.get("OFFICIAL_DECISION_IMPACT")
        or trust_kv.get("OFFICIAL_DECISION_IMPACT")
        or "UNKNOWN"
    )
    forbidden_modified = (
        homepage_kv.get("FORBIDDEN_MODIFIED")
        or runbook_kv.get("FORBIDDEN_MODIFIED")
        or readiness_kv.get("FORBIDDEN_MODIFIED")
        or compact_kv.get("FORBIDDEN_MODIFIED")
        or "UNKNOWN"
    )
    daily_trust_level = (
        trust_kv.get("DAILY_TRUST_LEVEL")
        or first_match(trust, [r"DAILY_TRUST_LEVEL:\s*([A-Z_]+)"])
        or "UNKNOWN"
    )
    v18_33a_run_id = (
        read_first_33a.get("RUN_ID")
        or homepage_kv.get("RUN_ID")
        or "UNKNOWN"
    )
    v18_33b_run_id = read_first_33b.get("RUN_ID") or "UNKNOWN"
    storage_repo_size_mb = (
        storage_kv.get("TOTAL_REPO_SIZE_MB_BEFORE")
        or storage_kv.get("TOTAL_REPO_SIZE_MB_AFTER")
        or "UNKNOWN"
    )

    return {
        "latest_signal_date": latest_signal_date,
        "candidate_count": candidate_count,
        "expected_candidate_count": expected_candidate_count,
        "freeze_ticker_count": freeze_ticker_count,
        "freeze_coverage_status": freeze_coverage_status,
        "allowed_trade_candidate_count": allowed_trade_candidate_count,
        "account_state_quality": account_state_quality,
        "auto_trade": auto_trade,
        "auto_sell": auto_sell,
        "official_decision_impact": official_decision_impact,
        "forbidden_modified": forbidden_modified,
        "daily_trust_level": daily_trust_level,
        "v18_33a_run_id": v18_33a_run_id,
        "v18_33b_run_id": v18_33b_run_id,
        "storage_repo_size_mb": storage_repo_size_mb,
    }


def build_report(
    fields: Dict[str, str],
    required_meta: List[Dict[str, object]],
    optional_meta: List[Dict[str, object]],
    warnings: List[str],
    status: str,
    max_gap_hours: str,
    freshness_round_consistent: str,
) -> str:
    lines = [
        "# V18.34B Daily Output Freshness Guard",
        "",
        f"- STATUS: `{status}`",
        f"- GENERATED_AT: `{dt.datetime.now().replace(microsecond=0).isoformat()}`",
        f"- FRESHNESS_ROUND_CONSISTENT: `{freshness_round_consistent}`",
        f"- MAX_KEY_FILE_GAP_HOURS: `{max_gap_hours}`",
        "",
        "## Required Files",
        "| file | exists | modified | age_hours |",
        "| --- | --- | --- | ---: |",
    ]
    for row in required_meta:
        lines.append(
            f"| `{row['path']}` | {row['exists']} | {row['modified'] or 'UNKNOWN'} | {row['age_hours']} |"
        )
    lines += [
        "",
        "## Optional Files",
        "| file | exists | modified | age_hours |",
        "| --- | --- | --- | ---: |",
    ]
    for row in optional_meta:
        lines.append(
            f"| `{row['path']}` | {row['exists']} | {row['modified'] or 'UNKNOWN'} | {row['age_hours']} |"
        )
    lines += [
        "",
        "## Extracted Fields",
        f"- candidate_count: `{fields['candidate_count']}`",
        f"- expected_candidate_count: `{fields['expected_candidate_count']}`",
        f"- freeze_ticker_count: `{fields['freeze_ticker_count']}`",
        f"- freeze_coverage_status: `{fields['freeze_coverage_status']}`",
        f"- latest_signal_date: `{fields['latest_signal_date']}`",
        f"- allowed_trade_candidate_count: `{fields['allowed_trade_candidate_count']}`",
        f"- account_state_quality: `{fields['account_state_quality']}`",
        f"- `AUTO_TRADE`: `{fields['auto_trade']}`",
        f"- `AUTO_SELL`: `{fields['auto_sell']}`",
        f"- `OFFICIAL_DECISION_IMPACT`: `{fields['official_decision_impact']}`",
        f"- `FORBIDDEN_MODIFIED`: `{fields['forbidden_modified']}`",
        f"- `DAILY_TRUST_LEVEL`: `{fields['daily_trust_level']}`",
        f"- `V18_33A_RUN_ID`: `{fields['v18_33a_run_id']}`",
        f"- `V18_33B_RUN_ID`: `{fields['v18_33b_run_id']}`",
        f"- storage_repo_size_mb: `{fields['storage_repo_size_mb']}`",
        "",
        "## Consistency Check",
        f"- homepage vs context candidate/freeze: {'OK' if 'candidate_mismatch' not in warnings and 'freeze_mismatch' not in warnings else 'WARN'}",
        f"- runbook vs homepage freshness: {'OK' if 'runbook_stale_vs_homepage' not in warnings else 'WARN'}",
        f"- compact vs context consistency: {'OK' if 'compact_vs_context_mismatch' not in warnings else 'WARN'}",
        f"- daily readiness vs homepage/context: {'OK' if 'daily_readiness_mismatch' not in warnings else 'WARN'}",
        f"- storage state: {'OK' if fields['storage_repo_size_mb'] != 'UNKNOWN' and float(fields['storage_repo_size_mb']) < 900 else 'WARN'}",
        "",
        "## Warnings",
    ]
    if warnings:
        for warn in warnings:
            lines.append(f"- WARN: {warn}")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Notes",
        "- This guard is audit-only and does not modify ledgers or trading logic.",
        "- `WARN` is expected for template account state, zero allowed candidates, and medium daily trust level.",
    ]
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    now = dt.datetime.now().replace(microsecond=0)
    warnings: List[str] = []

    required_meta: List[Dict[str, object]] = []
    optional_meta: List[Dict[str, object]] = []
    missing_required = False
    for path in REQUIRED_FILES:
        exists = path.exists()
        if not exists:
            missing_required = True
        modified = modified_time(path)
        age = age_hours(path, now)
        required_meta.append(
            {
                "path": str(path),
                "exists": bool_text(exists),
                "modified": modified.isoformat() if modified else "",
                "age_hours": f"{age:.2f}" if age is not None else "UNKNOWN",
            }
        )
    for path in OPTIONAL_FILES:
        exists = path.exists()
        modified = modified_time(path)
        age = age_hours(path, now)
        optional_meta.append(
            {
                "path": str(path),
                "exists": bool_text(exists),
                "modified": modified.isoformat() if modified else "",
                "age_hours": f"{age:.2f}" if age is not None else "UNKNOWN",
            }
        )

    if missing_required:
        fields = parse_report_fields(root)
        status = STATUS_FAIL
        fail_reason = "Missing one or more required current report files."
    else:
        fields = parse_report_fields(root)
        fail_reason = ""
        # freshness warnings
        key_ages = [age_hours(p, now) for p in REQUIRED_FILES if age_hours(p, now) is not None]
        max_age = max(key_ages) if key_ages else 0.0
        min_age = min(key_ages) if key_ages else 0.0
        max_gap = max_age - min_age
        freshness_round_consistent = bool_text(max_gap <= 36.0)
        max_gap_hours = f"{max_gap:.2f}"
        for row in required_meta:
            try:
                if row["age_hours"] != "UNKNOWN" and float(row["age_hours"]) > 36.0:
                    warnings.append(f"{Path(row['path']).name} older than 36h")
            except Exception:
                warnings.append(f"{Path(row['path']).name} age could not be parsed")
        if max_gap > 36.0:
            warnings.append(f"max modified-time gap among key files is {max_gap:.2f}h")

        # field consistency warnings
        if fields["freeze_coverage_status"] != "FULL_MATCH":
            warnings.append("freeze coverage is not FULL_MATCH")
        if fields["candidate_count"] != "UNKNOWN" and fields["expected_candidate_count"] != "UNKNOWN" and fields["candidate_count"] != fields["expected_candidate_count"]:
            warnings.append("candidate_count and expected_candidate_count differ")
        if fields["freeze_ticker_count"] != "UNKNOWN" and fields["expected_candidate_count"] != "UNKNOWN" and fields["freeze_ticker_count"] != fields["expected_candidate_count"]:
            warnings.append("freeze_ticker_count does not match expected_candidate_count")
        if fields["auto_trade"] != "DISABLED":
            warnings.append("AUTO_TRADE is not DISABLED")
        if fields["auto_sell"] != "DISABLED":
            warnings.append("AUTO_SELL is not DISABLED")
        if fields["official_decision_impact"] != "NONE":
            warnings.append("OFFICIAL_DECISION_IMPACT is not NONE")
        if fields["forbidden_modified"] != "FALSE":
            warnings.append("FORBIDDEN_MODIFIED is not FALSE")
        if fields["daily_trust_level"] == "MEDIUM":
            warnings.append("daily trust level is MEDIUM")
        if fields["account_state_quality"] == "WARN_TEMPLATE_EMPTY_ACCOUNT":
            warnings.append("account state is template/manual")
        if fields["allowed_trade_candidate_count"] == "0":
            warnings.append("allowed trade candidates are 0")

        # cross-file stale report checks
        home = parse_key_values(read_text(REQUIRED_FILES[0]))
        runbook = parse_key_values(read_text(REQUIRED_FILES[1]))
        context = parse_key_values(read_text(REQUIRED_FILES[2]))
        readiness = parse_key_values(read_text(REQUIRED_FILES[3]))
        compact = parse_key_values(read_text(REQUIRED_FILES[4]))
        home_candidate = home.get("CANDIDATE_COUNT", "UNKNOWN")
        home_freeze = home.get("FREEZE_COVERAGE_STATUS", "UNKNOWN")
        context_candidate = context.get("Expected candidates", "UNKNOWN")
        context_freeze = context.get("Freeze coverage", "UNKNOWN")
        readiness_candidate = readiness.get("Ranked rows", "UNKNOWN")
        readiness_freeze = readiness.get("Latest full signal freeze rows", "UNKNOWN")
        compact_candidate = compact.get("Expected candidate count", "UNKNOWN")
        compact_freeze = compact.get("Latest freeze coverage status", "UNKNOWN")

        if home_candidate != "UNKNOWN" and context_candidate != "UNKNOWN" and home_candidate != context_candidate:
            warnings.append("homepage candidate count differs from context consistency")
            warnings.append("candidate_mismatch")
        if home_freeze != "UNKNOWN" and context_freeze != "UNKNOWN" and home_freeze != context_freeze:
            warnings.append("homepage freeze state differs from context consistency")
            warnings.append("freeze_mismatch")
        if compact_freeze != "UNKNOWN" and context_freeze != "UNKNOWN" and compact_freeze != context_freeze:
            warnings.append("compact context freeze state differs from context consistency")
            warnings.append("compact_vs_context_mismatch")
        if readiness_freeze != "UNKNOWN" and context_freeze != "UNKNOWN" and readiness_freeze != context_freeze:
            warnings.append("daily readiness freeze state differs from context/homepage")
            warnings.append("daily_readiness_mismatch")

        # specific stale-file relationship checks
        if modified_time(REQUIRED_FILES[1]) and modified_time(REQUIRED_FILES[2]):
            if modified_time(REQUIRED_FILES[2]) and modified_time(REQUIRED_FILES[1]) and modified_time(REQUIRED_FILES[1]) < modified_time(REQUIRED_FILES[2]) and age_hours(REQUIRED_FILES[1], now) and age_hours(REQUIRED_FILES[1], now) > 36.0:
                warnings.append("runbook is older than context consistency by more than 36h")
                warnings.append("runbook_stale_vs_homepage")
        # storage cleanup state
        storage_text = read_text(ROOT_DEFAULT / "outputs/v18/read_center/V18_CURRENT_STORAGE_CLEANUP.md")
        storage_kv = parse_key_values(storage_text)
        storage_size = storage_kv.get("TOTAL_REPO_SIZE_MB_BEFORE") or storage_kv.get("TOTAL_REPO_SIZE_MB_AFTER") or "UNKNOWN"
        if storage_size != "UNKNOWN":
            try:
                if float(storage_size) > 1000.0:
                    warnings.append("repo size is still above 1GB")
                elif float(storage_size) < 900.0:
                    pass
            except ValueError:
                warnings.append("storage repo size could not be parsed")
        else:
            warnings.append("storage repo size is UNKNOWN")

        status = STATUS_OK if not warnings else STATUS_WARN

    if missing_required:
        status = STATUS_FAIL
        max_gap_hours = "UNKNOWN"
        freshness_round_consistent = "FALSE"
    else:
        key_ages = [age_hours(p, now) for p in REQUIRED_FILES if age_hours(p, now) is not None]
        max_gap = max(key_ages) - min(key_ages) if key_ages else 0.0
        max_gap_hours = f"{max_gap:.2f}"
        freshness_round_consistent = bool_text(max_gap <= 36.0)

    summary_row = {
        "run_id": f"V18_34B_{now.strftime('%Y%m%d_%H%M%S')}",
        "status": status,
        "generated_at": now.isoformat(),
        "required_files_present": bool_text(not missing_required),
        "homepage_exists": bool_text(REQUIRED_FILES[0].exists()),
        "runbook_exists": bool_text(REQUIRED_FILES[1].exists()),
        "context_consistency_exists": bool_text(REQUIRED_FILES[2].exists()),
        "daily_readiness_exists": bool_text(REQUIRED_FILES[3].exists()),
        "compact_context_exists": bool_text(REQUIRED_FILES[4].exists()),
        "candidate_count": fields["candidate_count"],
        "expected_candidate_count": fields["expected_candidate_count"],
        "freeze_ticker_count": fields["freeze_ticker_count"],
        "freeze_coverage_status": fields["freeze_coverage_status"],
        "latest_signal_date": fields["latest_signal_date"],
        "allowed_trade_candidate_count": fields["allowed_trade_candidate_count"],
        "account_state_quality": fields["account_state_quality"],
        "auto_trade": fields["auto_trade"],
        "auto_sell": fields["auto_sell"],
        "official_decision_impact": fields["official_decision_impact"],
        "forbidden_modified": fields["forbidden_modified"],
        "daily_trust_level": fields["daily_trust_level"],
        "v18_33a_run_id": fields["v18_33a_run_id"],
        "storage_repo_size_mb": fields["storage_repo_size_mb"],
        "max_key_file_gap_hours": max_gap_hours,
        "freshness_round_consistent": freshness_round_consistent,
        "warning_count": str(len(warnings)),
        "fail_reason": fail_reason,
    }

    report_text = build_report(fields, required_meta, optional_meta, warnings, status, max_gap_hours, freshness_round_consistent)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    CURRENT_PATH.write_text(report_text, encoding="utf-8")
    write_csv(SUMMARY_PATH, [summary_row], list(summary_row.keys()))
    READ_FIRST_PATH.write_text(
        "\n".join(
            [
                f"STATUS: {status}",
                "1. outputs/v18/read_center/V18_CURRENT_DAILY_OUTPUT_FRESHNESS.md",
                "2. outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md",
                "3. outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_RUNBOOK_CN.md",
                "4. outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md",
                "5. outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md",
                "6. outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"STATUS: {status}")
    print(f"RUN_ID: {summary_row['run_id']}")
    print(f"MAX_KEY_FILE_GAP_HOURS: {max_gap_hours}")
    print(f"FRESHNESS_ROUND_CONSISTENT: {freshness_round_consistent}")
    print(f"CANDIDATE_COUNT: {fields['candidate_count']}")
    print(f"FREEZE_COVERAGE_STATUS: {fields['freeze_coverage_status']}")
    print(f"ALLOWED_TRADE_COUNT: {fields['allowed_trade_candidate_count']}")
    print(f"DAILY_TRUST_LEVEL: {fields['daily_trust_level']}")
    print(f"STORAGE_REPO_SIZE_MB: {fields['storage_repo_size_mb']}")
    print(f"REPORT: {REPORT_PATH}")
    print(f"READ_FIRST: {READ_FIRST_PATH}")
    if status == STATUS_FAIL:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.34B daily output freshness guard.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
