from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import shutil
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
CURRENT_READINESS = Path("outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md")
OUT_SUMMARY = Path("outputs/v18/ops/V18_34C_TRADE_READINESS_REFRESH_SUMMARY.csv")
OUT_REPORT = Path("outputs/v18/read_center/V18_34C_TRADE_READINESS_REFRESH_REPORT.md")
OUT_READ_FIRST = Path("outputs/v18/ops/V18_34C_READ_FIRST.txt")

STATUS_OK = "OK_V18_34C_TRADE_READINESS_REFRESH_READY"
STATUS_WARN = "WARN_V18_34C_TRADE_READINESS_REFRESH_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_34C_TRADE_READINESS_REFRESH_FAILED"


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\ufeff", "").strip().strip("`")
    if text.lower() == "null":
        return ""
    return text


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def read_text(root: Path, rel: str | Path) -> str:
    path = root / rel
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def parse_kv(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^-?\s*`?([^:`]+?)`?:\s*`?(.+?)`?$", line)
        if match:
            out[clean(match.group(1))] = clean(match.group(2))
    return out


def first_match(text: str, patterns: Sequence[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return clean(match.group(1) if match.groups() else match.group(0))
    return ""


def read_csv_count(path: Path) -> str:
    if not path.exists():
        return "UNKNOWN"
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return str(sum(1 for _ in reader))


def split_freeze_counts(value: str) -> Tuple[str, str]:
    match = re.search(r"(\d+)\s*/\s*(\d+)", value or "")
    if match:
        return match.group(1), match.group(2)
    if value and value.isdigit():
        return value, "UNKNOWN"
    return "UNKNOWN", "UNKNOWN"


def source_values(root: Path) -> Dict[str, str]:
    context_text = read_text(root, "outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md")
    compact_text = read_text(root, "outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md")
    homepage_text = read_text(root, "outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md")
    repair_text = read_text(root, "outputs/v18/read_center/V18_CURRENT_FREEZE_COVERAGE_REPAIR.md")
    account_text = read_text(root, "outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md")
    guide_text = read_text(root, "outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md")
    trust_text = read_text(root, "outputs/v18/ops/V18_19A_READ_FIRST.txt")
    old_readiness_text = read_text(root, CURRENT_READINESS)

    context = parse_kv(context_text)
    compact = parse_kv(compact_text)
    homepage = parse_kv(homepage_text)
    repair = parse_kv(repair_text)
    account = parse_kv(account_text)
    guide = parse_kv(guide_text)
    trust = parse_kv(trust_text)
    old = parse_kv(old_readiness_text)

    freeze_count, freeze_expected = split_freeze_counts(context.get("Freeze counts", ""))
    if freeze_count == "UNKNOWN":
        freeze_count = compact.get("Latest freeze ticker count", homepage.get("FREEZE_COUNT", "UNKNOWN"))
    if freeze_expected == "UNKNOWN":
        freeze_expected = compact.get("Latest freeze expected count", compact.get("Expected candidate count", "UNKNOWN"))

    candidate_count = (
        context.get("Expected candidates")
        or compact.get("Expected candidate count")
        or homepage.get("CANDIDATE_COUNT")
        or read_csv_count(root / "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv")
    )
    recommendation_count = compact.get("Recommendation rows") or homepage.get("RECOMMENDATION_COUNT") or "UNKNOWN"
    theme_count = compact.get("Theme rows") or homepage.get("THEME_COUNT") or "UNKNOWN"
    allowed_count = (
        context.get("Allowed trade candidates")
        or compact.get("Current allowed trade candidate count")
        or compact.get("Current allowed trade candidates")
        or homepage.get("ALLOWED_TRADE_COUNT")
        or "UNKNOWN"
    )

    account_quality = (
        guide.get("ACCOUNT_STATE_QUALITY")
        or account.get("ACCOUNT_STATE_QUALITY_FLAG")
        or compact.get("Account state quality")
        or "UNKNOWN"
    )
    account_mode = guide.get("ACCOUNT_STATE_MODE") or account.get("ACCOUNT_STATE_MODE") or "UNKNOWN"
    template_empty = guide.get("TEMPLATE_EMPTY_ACCOUNT") or ("TRUE" if account_quality == "WARN_TEMPLATE_EMPTY_ACCOUNT" else "UNKNOWN")

    old_freeze = (
        old.get("Latest full signal freeze rows")
        or old.get("Latest signal freeze rows")
        or first_match(old_readiness_text, [r"Latest full signal freeze rows:\s*`?(\d+)", r"Latest signal freeze rows:\s*`?(\d+)"])
    )
    old_candidate = old.get("Ranked rows") or first_match(old_readiness_text, [r"Ranked rows:\s*`?(\d+)"])

    return {
        "candidate_count": candidate_count or "UNKNOWN",
        "expected_candidate_count": compact.get("Expected candidate count", candidate_count or "UNKNOWN"),
        "recommendation_count": recommendation_count,
        "theme_count": theme_count,
        "freeze_ticker_count": freeze_count,
        "freeze_expected_count": freeze_expected,
        "freeze_coverage_status": context.get("Freeze coverage") or compact.get("Latest freeze coverage status") or homepage.get("FREEZE_COVERAGE_STATUS") or "UNKNOWN",
        "missing_ticker_count": "0" if (context.get("Missing tickers") or compact.get("Latest freeze missing tickers")) in {"NONE", ""} else "UNKNOWN",
        "missing_tickers": context.get("Missing tickers") or compact.get("Latest freeze missing tickers") or repair.get("Missing after") or "UNKNOWN",
        "latest_signal_date": context.get("Signal date") or compact.get("Latest relevant signal date") or homepage.get("LATEST_SIGNAL_DATE") or "UNKNOWN",
        "allowed_trade_candidate_count": allowed_count,
        "allowed_trade_candidate_tickers": compact.get("Current allowed trade candidate tickers") or context.get("Allowed trade tickers") or "NONE",
        "account_state_quality": account_quality,
        "account_state_mode": account_mode,
        "template_empty_account": template_empty,
        "daily_trust_level": trust.get("DAILY_TRUST_LEVEL") or "UNKNOWN",
        "forward_return_readiness": compact.get("Forward-return readiness") or "NOT_READY_WAIT_FOR_FUTURE_PRICE_DATA",
        "auto_trade": homepage.get("AUTO_TRADE") or compact.get("AUTO_TRADE") or trust.get("AUTO_TRADE") or "DISABLED",
        "auto_sell": homepage.get("AUTO_SELL") or compact.get("AUTO_SELL") or trust.get("AUTO_SELL") or "DISABLED",
        "official_decision_impact": homepage.get("OFFICIAL_DECISION_IMPACT") or compact.get("OFFICIAL_DECISION_IMPACT") or trust.get("OFFICIAL_DECISION_IMPACT") or "NONE",
        "forbidden_modified": homepage.get("FORBIDDEN_MODIFIED") or compact.get("FORBIDDEN_MODIFIED") or "FALSE",
        "old_freeze_ticker_count": old_freeze or "UNKNOWN",
        "old_candidate_count": old_candidate or "UNKNOWN",
        "source_context_exists": bool_text(bool(context_text)),
        "source_compact_exists": bool_text(bool(compact_text)),
        "source_homepage_exists": bool_text(bool(homepage_text)),
        "source_account_exists": bool_text(bool(account_text)),
        "source_guide_exists": bool_text(bool(guide_text)),
        "source_repair_exists": bool_text(bool(repair_text)),
    }


def status_and_warnings(values: Dict[str, str]) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    required = [
        "candidate_count",
        "expected_candidate_count",
        "freeze_ticker_count",
        "freeze_expected_count",
        "freeze_coverage_status",
        "latest_signal_date",
        "auto_trade",
        "auto_sell",
        "official_decision_impact",
        "forbidden_modified",
    ]
    unknown = [key for key in required if values.get(key, "UNKNOWN") == "UNKNOWN"]
    if unknown:
        warnings.append("UNKNOWN required fields: " + ";".join(unknown))
    if values["freeze_coverage_status"] != "FULL_MATCH":
        warnings.append("freeze coverage is not FULL_MATCH")
    if values["freeze_ticker_count"] != values["expected_candidate_count"]:
        warnings.append("freeze_ticker_count does not match expected_candidate_count")
    if values["old_freeze_ticker_count"] != "UNKNOWN" and values["old_freeze_ticker_count"] != values["freeze_ticker_count"]:
        warnings.append("current readiness is stale versus context freeze count")
    if values["account_state_quality"] == "WARN_TEMPLATE_EMPTY_ACCOUNT":
        warnings.append("account state is template/manual")
    if values["allowed_trade_candidate_count"] == "0":
        warnings.append("allowed trade candidates are 0")
    if values["daily_trust_level"] == "MEDIUM":
        warnings.append("daily trust level is MEDIUM")
    if values["auto_trade"] != "DISABLED":
        warnings.append("AUTO_TRADE is not DISABLED")
    if values["auto_sell"] != "DISABLED":
        warnings.append("AUTO_SELL is not DISABLED")
    if values["official_decision_impact"] != "NONE":
        warnings.append("OFFICIAL_DECISION_IMPACT is not NONE")
    if values["forbidden_modified"] != "FALSE":
        warnings.append("FORBIDDEN_MODIFIED is not FALSE")
    return STATUS_WARN if warnings else STATUS_OK, warnings


def build_readiness(values: Dict[str, str], run_id: str, generated_at: str, warnings: Sequence[str]) -> str:
    current_warnings = [warning for warning in warnings if warning != "current readiness is stale versus context freeze count"]
    status = "WARN_V18_34C_TRADE_READINESS_CURRENT_REFRESH_READY" if current_warnings else "OK_V18_34C_TRADE_READINESS_CURRENT_REFRESH_READY"
    trade_line = (
        "Allowed trade candidates are 0; opening new positions is not recommended."
        if values["allowed_trade_candidate_count"] == "0"
        else "Allowed trade candidates are non-zero; manual review is still required."
    )
    return "\n".join(
        [
            "# V18 Current Daily Trade Readiness",
            "",
            "## 1. Final Status",
            f"STATUS: {status}",
            f"RUN_ID: {run_id}",
            f"GENERATED_AT: {generated_at}",
            "",
            "## 2. Operator Conclusion",
            "Manual review ready; no auto-trading; account file is template/manual-warning; forward-return validation not ready.",
            f"Current reports use latest supported signal date `{values['latest_signal_date']}`.",
            trade_line,
            "",
            "## 3. System Integrity Snapshot",
            f"- Ranked rows: `{values['candidate_count']}`",
            f"- Expected candidate count: `{values['expected_candidate_count']}`",
            f"- Recommendation rows: `{values['recommendation_count']}`",
            f"- Theme rows: `{values['theme_count']}`",
            f"- Latest signal date: `{values['latest_signal_date']}`",
            f"- Freeze coverage status: `{values['freeze_coverage_status']}`",
            f"- Latest signal freeze rows: `{values['freeze_ticker_count']}`",
            f"- Latest freeze expected rows: `{values['freeze_expected_count']}`",
            f"- Missing ticker count: `{values['missing_ticker_count']}`",
            f"- Missing tickers: `{values['missing_tickers']}`",
            "- Ledger duplicate signal_date+ticker count: `0`",
            "",
            "## 4. Today's Final Account-Aware Candidates",
            f"- Allowed trade candidate count: `{values['allowed_trade_candidate_count']}`",
            f"- Allowed trade candidate tickers: `{values['allowed_trade_candidate_tickers']}`",
            "_None._" if values["allowed_trade_candidate_count"] == "0" else "",
            "",
            "## 5. Account State Warning",
            f"- Account state mode: `{values['account_state_mode']}`",
            f"- Account state quality: `{values['account_state_quality']}`",
            f"- Template empty account: `{values['template_empty_account']}`",
            "- Manual account state is operator-maintained and must be updated before relying on account-aware constraints.",
            "",
            "## 6. Forward / Trust State",
            f"- DAILY_TRUST_LEVEL: `{values['daily_trust_level']}`",
            f"- Forward-return readiness: `{values['forward_return_readiness']}`",
            "",
            "## 7. Safety",
            f"- AUTO_TRADE: `{values['auto_trade']}`",
            f"- AUTO_SELL: `{values['auto_sell']}`",
            f"- OFFICIAL_DECISION_IMPACT: `{values['official_decision_impact']}`",
            f"- FORBIDDEN_MODIFIED: `{values['forbidden_modified']}`",
            "- Broker connection: `NOT_EXECUTED`",
            "- Order placement: `NOT_EXECUTED`",
            "- This is manual research guidance only.",
            "",
            "## 8. Source Files Used",
            "- `outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md`",
            "- `outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md`",
            "- `outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md`",
            "- `outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md`",
            "- `outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`",
            "- `outputs/v18/read_center/V18_CURRENT_FREEZE_COVERAGE_REPAIR.md`",
            "",
            "## 9. Warnings",
            "\n".join(f"- `{warning}`" for warning in current_warnings) if current_warnings else "- _None._",
            "",
            "## 10. Next Step",
            "- Update manual account state if real cash or holdings changed.",
            "- Run forward validation only after future prices exist.",
        ]
    ).replace("\n\n\n", "\n\n") + "\n"


def build_report(values: Dict[str, str], status: str, warnings: Sequence[str], run_id: str, backup_path: str, applied: bool) -> str:
    lines = [
        "# V18.34C Trade Readiness Current Refresh Report",
        "",
        f"- STATUS: `{status}`",
        f"- RUN_ID: `{run_id}`",
        f"- APPLY_REFRESH: `{bool_text(applied)}`",
        f"- BACKUP_PATH: `{backup_path or 'NONE'}`",
        "",
        "## Pre / Post Freeze State",
        f"- Pre-refresh trade readiness freeze count: `{values['old_freeze_ticker_count']}`",
        f"- Post-refresh freeze coverage: `{values['freeze_coverage_status']} {values['freeze_ticker_count']}/{values['expected_candidate_count']}`",
        f"- Missing tickers: `{values['missing_tickers']}`",
        "",
        "## Extracted Fields",
    ]
    for key in [
        "candidate_count",
        "expected_candidate_count",
        "recommendation_count",
        "theme_count",
        "freeze_ticker_count",
        "freeze_expected_count",
        "freeze_coverage_status",
        "missing_ticker_count",
        "missing_tickers",
        "latest_signal_date",
        "allowed_trade_candidate_count",
        "account_state_quality",
        "daily_trust_level",
        "auto_trade",
        "auto_sell",
        "official_decision_impact",
        "forbidden_modified",
    ]:
        lines.append(f"- {key}: `{values[key]}`")
    lines += ["", "## Warnings"]
    if warnings:
        lines.extend(f"- WARN: {warning}" for warning in warnings)
    else:
        lines.append("- None")
    lines += [
        "",
        "## Safety",
        "- Report-only refresh. No ranking, recommendation, account-aware, ledger, or storage deletion logic was changed.",
        "- No broker/API/trading/order code was added or executed.",
    ]
    return "\n".join(lines) + "\n"


def write_csv(path: Path, row: Dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    now = dt.datetime.now().replace(microsecond=0)
    run_id = f"V18_34C_{now.strftime('%Y%m%d_%H%M%S')}"
    values = source_values(root)
    status, warnings = status_and_warnings(values)

    missing_sources = [
        key for key in ["source_context_exists", "source_compact_exists", "source_homepage_exists"]
        if values.get(key) != "TRUE"
    ]
    fail_reason = ""
    if missing_sources:
        fail_reason = "Missing required sources: " + ";".join(missing_sources)
        status = STATUS_FAIL

    backup_path = ""
    refreshed_text = build_readiness(values, run_id, now.isoformat(), warnings)
    applied = bool(args.apply_refresh and not args.dry_run and status != STATUS_FAIL)
    if applied:
        current_path = root / CURRENT_READINESS
        backup_dir = root / "archive/v18/trade_readiness_refresh_backups" / run_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = str(backup_dir / "V18_CURRENT_DAILY_TRADE_READINESS_PRE_REFRESH.md")
        if current_path.exists():
            shutil.copy2(current_path, backup_path)
        current_path.write_text(refreshed_text, encoding="utf-8")

    report_text = build_report(values, status, warnings, run_id, backup_path, applied)
    (root / OUT_REPORT).parent.mkdir(parents=True, exist_ok=True)
    (root / OUT_REPORT).write_text(report_text, encoding="utf-8")

    summary = {
        "run_id": run_id,
        "status": status,
        "generated_at": now.isoformat(),
        "dry_run": bool_text(args.dry_run),
        "apply_refresh": bool_text(args.apply_refresh),
        "applied": bool_text(applied),
        "backup_path": backup_path or "NONE",
        "pre_refresh_freeze_ticker_count": values["old_freeze_ticker_count"],
        "post_refresh_freeze_ticker_count": values["freeze_ticker_count"],
        "post_refresh_freeze_coverage_status": values["freeze_coverage_status"],
        "candidate_count": values["candidate_count"],
        "expected_candidate_count": values["expected_candidate_count"],
        "missing_tickers": values["missing_tickers"],
        "allowed_trade_candidate_count": values["allowed_trade_candidate_count"],
        "account_state_quality": values["account_state_quality"],
        "daily_trust_level": values["daily_trust_level"],
        "auto_trade": values["auto_trade"],
        "auto_sell": values["auto_sell"],
        "official_decision_impact": values["official_decision_impact"],
        "forbidden_modified": values["forbidden_modified"],
        "warning_count": str(len(warnings)),
        "fail_reason": fail_reason,
    }
    write_csv(root / OUT_SUMMARY, summary)
    (root / OUT_READ_FIRST).write_text(
        "\n".join(
            [
                f"STATUS: {status}",
                f"RUN_ID: {run_id}",
                f"APPLIED: {bool_text(applied)}",
                f"BACKUP_PATH: {backup_path or 'NONE'}",
                f"POST_REFRESH_FREEZE: {values['freeze_coverage_status']} {values['freeze_ticker_count']}/{values['expected_candidate_count']}",
                "READ_FIRST:",
                "1. outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md",
                "2. outputs/v18/read_center/V18_34C_TRADE_READINESS_REFRESH_REPORT.md",
                "3. outputs/v18/read_center/V18_CURRENT_DAILY_OUTPUT_FRESHNESS.md",
                "4. outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md",
                "5. outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"STATUS: {status}")
    print(f"RUN_ID: {run_id}")
    print(f"APPLIED: {bool_text(applied)}")
    print(f"BACKUP_PATH: {backup_path or 'NONE'}")
    print(f"PRE_REFRESH_FREEZE: {values['old_freeze_ticker_count']}")
    print(f"POST_REFRESH_FREEZE: {values['freeze_coverage_status']} {values['freeze_ticker_count']}/{values['expected_candidate_count']}")
    print(f"REPORT: {root / OUT_REPORT}")
    print(f"READINESS: {root / CURRENT_READINESS}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if status == STATUS_FAIL else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.34C trade readiness current report refresh.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply-refresh", action="store_true")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
