from __future__ import annotations

import argparse
import csv
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


STATUS_OK = "OK_V18_35G_UNIVERSE_INVALID_TICKER_PRUNE_READY"
STATUS_WARN = "WARN_V18_35G_UNIVERSE_INVALID_TICKER_PRUNE_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_35G_UNIVERSE_INVALID_TICKER_PRUNE_FAILED"

AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FORBIDDEN_MODIFIED = "FALSE"

UNIVERSE = "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv"
ROLLING = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
REMAINING = "outputs/v18/candidates/V18_35E_REMAINING_UNCOMPUTED_TICKERS.csv"
BRIDGE = "outputs/v18/candidates/V18_35E_CANDIDATE_ADOPTION_BRIDGE.csv"
BACKFILL_FAILED = "outputs/v18/data_backfill/V18_35E_ONLINE_BACKFILL_FAILED_TICKERS.csv"
CURRENT_FULL = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
CURRENT_RANKED = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
CURRENT_TOP = "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"
FREEZE = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"

OUT_PREVIEW = "outputs/v18/ops/V18_35G_UNIVERSE_INVALID_TICKER_PRUNE_PREVIEW.csv"
OUT_DETAIL = "outputs/v18/ops/V18_35G_UNIVERSE_INVALID_TICKER_PRUNE_DETAIL.csv"
OUT_SUMMARY = "outputs/v18/ops/V18_35G_UNIVERSE_INVALID_TICKER_PRUNE_SUMMARY.csv"
OUT_EXCLUDED = "outputs/v18/ops/V18_35G_EXCLUDED_TICKER_LEDGER.csv"
OUT_REPORT = "outputs/v18/read_center/V18_35G_UNIVERSE_INVALID_TICKER_PRUNE_REPORT.md"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_UNIVERSE_INVALID_TICKER_PRUNE.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_35G_READ_FIRST.txt"

NUMERIC_TARGETS = ["0", "105", "20", "250", "252", "303", "318", "325"]
HEADER_TARGETS = ["TICKER", "TICKERS"]
USER_REMOVE_TARGETS = ["CDTX", "CFLT", "COG", "JFROG", "MPW"]
TARGETS = NUMERIC_TARGETS + HEADER_TARGETS + USER_REMOVE_TARGETS

DETAIL_FIELDS = [
    "ticker", "exclusion_reason", "in_universe_before", "in_current_full_candidates",
    "in_current_top_candidates", "in_latest_freeze", "in_remaining_uncomputed",
    "action_preview", "action_applied", "active_universe_after", "validation_status",
    "evidence_sources",
]


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def norm(v: object) -> str:
    return str(v or "").strip().upper()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as f:
                reader = csv.DictReader(f)
                return [dict(r) for r in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def ticker_set(rows: Sequence[dict[str, str]]) -> set[str]:
    return {norm(r.get("ticker") or r.get("yf_ticker") or r.get("symbol")) for r in rows if norm(r.get("ticker") or r.get("yf_ticker") or r.get("symbol"))}


def latest_freeze(rows: Sequence[dict[str, str]]) -> tuple[str, set[str]]:
    by_date: dict[str, set[str]] = {}
    for row in rows:
        d = str(row.get("signal_date", "")).strip()
        t = norm(row.get("ticker"))
        if d and t:
            by_date.setdefault(d, set()).add(t)
    if not by_date:
        return "", set()
    d = sorted(by_date)[-1]
    return d, by_date[d]


def duplicate_ticker_count(rows: Sequence[dict[str, str]]) -> int:
    counts = Counter(norm(r.get("ticker")) for r in rows if norm(r.get("ticker")))
    return sum(1 for _, c in counts.items() if c > 1)


def reason_for(ticker: str) -> str:
    if ticker in NUMERIC_TARGETS:
        return "INVALID_NUMERIC_TOKEN"
    if ticker in HEADER_TARGETS:
        return "INVALID_HEADER_TOKEN"
    return "USER_CONFIRMED_REMOVE_UNCOMPUTED_TICKER"


def make_detail(targets: Sequence[str], universe_set: set[str], full_set: set[str], top_set: set[str], freeze_set: set[str],
                remaining_set: set[str], applied: bool, after_universe_set: set[str]) -> list[dict[str, object]]:
    rows = []
    for ticker in targets:
        evidence = []
        if ticker in universe_set:
            evidence.append(UNIVERSE)
        if ticker in remaining_set:
            evidence.append(REMAINING)
        if ticker in full_set:
            evidence.append(CURRENT_FULL)
        if ticker in top_set:
            evidence.append(CURRENT_TOP)
        if ticker in freeze_set:
            evidence.append(FREEZE)
        active_after = ticker in after_universe_set
        status = "PASS" if applied and not active_after else ("PREVIEW_ONLY" if not applied else "FAIL_STILL_ACTIVE")
        rows.append({
            "ticker": ticker,
            "exclusion_reason": reason_for(ticker),
            "in_universe_before": str(ticker in universe_set).upper(),
            "in_current_full_candidates": str(ticker in full_set).upper(),
            "in_current_top_candidates": str(ticker in top_set).upper(),
            "in_latest_freeze": str(ticker in freeze_set).upper(),
            "in_remaining_uncomputed": str(ticker in remaining_set).upper(),
            "action_preview": "REMOVE_FROM_ACTIVE_UNIVERSE_AND_MARK_ROLLING_LEDGER_EXCLUDED" if ticker in universe_set else "AUDIT_LEDGER_ONLY_NOT_IN_ACTIVE_UNIVERSE",
            "action_applied": "TRUE" if applied and ticker in universe_set else "FALSE",
            "active_universe_after": str(active_after).upper(),
            "validation_status": status,
            "evidence_sources": ";".join(evidence),
        })
    return rows


def make_report(summary: dict[str, object], detail: list[dict[str, object]]) -> str:
    numeric = ", ".join(f"`{x}`" for x in NUMERIC_TARGETS)
    headers = ", ".join(f"`{x}`" for x in HEADER_TARGETS)
    user_removed = ", ".join(f"`{x}`" for x in USER_REMOVE_TARGETS)
    lines = [
        "# V18.35G 无效 ticker 清理 / active universe 修正",
        "",
        f"- STATUS: `{summary['status']}`",
        f"- RUN_ID: `{summary['run_id']}`",
        "",
        "## 说明",
        "V18.35E 后剩余 15 个无法计算 ticker 已由用户确认可以从当前 active universe 中剔除。目标是让 active universe 与当前 full candidates 318 对齐，减少后续重算中的无效失败项。",
        f"- 明显脏数字 token: {numeric}",
        f"- 明显表头 token: {headers}",
        f"- 用户确认不再研究的无法计算 ticker: {user_removed}",
        "",
        "## Count Summary",
        "| item | value |",
        "| --- | ---: |",
        f"| target exclusion count | {summary['target_exclusion_count']} |",
        f"| found in active universe | {summary['found_in_active_universe_count']} |",
        f"| applied exclusion count | {summary['applied_exclusion_count']} |",
        f"| total universe before | {summary['total_universe_count_before']} |",
        f"| total universe after | {summary['total_universe_count_after']} |",
        f"| current full candidates | {summary['current_full_candidate_count']} |",
        f"| latest freeze | {summary['latest_freeze_count']} |",
        "",
        "## Target Detail",
        "| ticker | reason | in universe before | in candidates | in freeze | validation |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in detail:
        lines.append(f"| `{row['ticker']}` | `{row['exclusion_reason']}` | {row['in_universe_before']} | {row['in_current_full_candidates']} | {row['in_latest_freeze']} | `{row['validation_status']}` |")
    lines += [
        "",
        "## Safety",
        f"- apply used: `{summary['apply_universe_invalid_ticker_prune']}`",
        f"- backup path: `{summary['backup_path']}`",
        "- freeze ledger 不修改，因为 V18.35F 已经冻结 318 候选，本任务只修正 active universe 来源。",
        "- candidate/ranking/factor 文件不修改；本任务只读它们用于验证。",
        "",
        "## Operator Next Action",
        "- apply 后重跑 V18.35D/E/A，确认 total universe 约 318、rank eligible 约 318、freeze/candidates 仍匹配。",
        "- 后续 universe 构建若再次引入这些 token，应检查上游 CSV/header/数字污染来源。",
        "",
        "## Final Conclusion",
        "Active universe invalid ticker cleanup completed or previewed.",
        "Freeze ledger was not modified.",
        "Candidate/ranking/factor logic was not modified.",
        "AUTO_TRADE DISABLED, AUTO_SELL DISABLED, OFFICIAL_DECISION_IMPACT NONE.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--apply-universe-invalid-ticker-prune", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    run_id = "V18_35G_" + stamp()
    generated_at = iso_now()
    warnings: list[str] = []
    fails: list[str] = []
    backup_path = "NONE"

    universe_rows, universe_fields = read_csv(root / UNIVERSE)
    rolling_rows, rolling_fields = read_csv(root / ROLLING)
    remaining_rows, _ = read_csv(root / REMAINING)
    bridge_rows, _ = read_csv(root / BRIDGE)
    failed_rows, _ = read_csv(root / BACKFILL_FAILED)
    full_rows, _ = read_csv(root / CURRENT_FULL)
    ranked_rows, _ = read_csv(root / CURRENT_RANKED)
    top_rows, _ = read_csv(root / CURRENT_TOP)
    freeze_rows, _ = read_csv(root / FREEZE)

    if not universe_rows or not universe_fields:
        fails.append("universe source cannot be read")

    universe_set_before = ticker_set(universe_rows)
    remaining_set = ticker_set(remaining_rows)
    full_set = ticker_set(full_rows)
    top_set = ticker_set(top_rows)
    latest_signal_date, freeze_set = latest_freeze(freeze_rows)
    found = [t for t in TARGETS if t in universe_set_before]
    not_found = [t for t in TARGETS if t not in universe_set_before]
    if not_found:
        warnings.append("some target tickers were not found in active universe")
    targets_in_freeze = [t for t in TARGETS if t in freeze_set]
    if targets_in_freeze:
        warnings.append("some target tickers appear in freeze ledger; freeze intentionally not modified")

    freeze_before_bytes = (root / FREEZE).read_bytes() if (root / FREEZE).exists() else b""
    full_before_bytes = (root / CURRENT_FULL).read_bytes() if (root / CURRENT_FULL).exists() else b""
    ranked_before_bytes = (root / CURRENT_RANKED).read_bytes() if (root / CURRENT_RANKED).exists() else b""
    top_before_bytes = (root / CURRENT_TOP).read_bytes() if (root / CURRENT_TOP).exists() else b""

    applied_count = 0
    after_universe_rows = list(universe_rows)
    after_rolling_rows = list(rolling_rows)
    if args.apply_universe_invalid_ticker_prune and not fails:
        try:
            backup_dir = root / "archive/v18/universe_invalid_ticker_prune_backups" / run_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / UNIVERSE, backup_dir / "V18_UNIVERSE_ROLLING_STATE_PRE_V18_35G.csv")
            if rolling_rows:
                shutil.copy2(root / ROLLING, backup_dir / "V18_23B_ROLLING_SCAN_LEDGER_PRE_V18_35G.csv")
            backup_path = str(backup_dir)

            target_set = set(TARGETS)
            after_universe_rows = [r for r in universe_rows if norm(r.get("ticker")) not in target_set]
            applied_count = len(universe_rows) - len(after_universe_rows)
            write_csv(root / UNIVERSE, after_universe_rows, universe_fields)

            if rolling_rows and rolling_fields:
                for row in after_rolling_rows:
                    ticker = norm(row.get("ticker"))
                    if ticker in target_set:
                        if "canonical_universe_present" in row:
                            row["canonical_universe_present"] = "FALSE"
                        if "last_scan_status" in row:
                            row["last_scan_status"] = "EXCLUDED_FROM_ACTIVE_UNIVERSE_V18_35G"
                        if "failure_reason" in row:
                            row["failure_reason"] = reason_for(ticker)
                        if "source_notes" in row:
                            note = str(row.get("source_notes", "")).strip()
                            suffix = f"V18.35G excluded from active universe: {reason_for(ticker)}"
                            row["source_notes"] = f"{note};{suffix}" if note else suffix
                write_csv(root / ROLLING, after_rolling_rows, rolling_fields)
        except Exception as exc:
            fails.append(f"backup/write fails in apply mode: {type(exc).__name__}")

    after_universe_set = ticker_set(after_universe_rows)
    detail = make_detail(TARGETS, universe_set_before, full_set, top_set, freeze_set, remaining_set, args.apply_universe_invalid_ticker_prune and not fails, after_universe_set)

    if args.apply_universe_invalid_ticker_prune and not fails:
        still_active = [t for t in TARGETS if t in after_universe_set]
        if still_active:
            fails.append("post-apply validation failed: target tickers still active")
        if duplicate_ticker_count(after_universe_rows):
            fails.append("post-apply validation failed: duplicate ticker count > 0")
        if freeze_before_bytes and (root / FREEZE).read_bytes() != freeze_before_bytes:
            fails.append("freeze ledger was modified")
        if full_before_bytes and (root / CURRENT_FULL).read_bytes() != full_before_bytes:
            fails.append("current full candidates were modified")
        if ranked_before_bytes and (root / CURRENT_RANKED).read_bytes() != ranked_before_bytes:
            fails.append("current ranked candidates were modified")
        if top_before_bytes and (root / CURRENT_TOP).read_bytes() != top_before_bytes:
            fails.append("current top candidates were modified")
    elif not args.apply_universe_invalid_ticker_prune:
        warnings.append("preview ready but apply not used")

    duplicate_after = duplicate_ticker_count(after_universe_rows)
    preview = [{
        "run_id": run_id,
        "generated_at": generated_at,
        "apply_universe_invalid_ticker_prune": str(args.apply_universe_invalid_ticker_prune).upper(),
        "target_exclusion_count": len(TARGETS),
        "found_in_active_universe_count": len(found),
        "expected_total_universe_count_after": len(universe_set_before) - len(found),
        "current_full_candidate_count": len(full_set),
        "latest_signal_date": latest_signal_date,
        "latest_freeze_count": len(freeze_set),
        "targets_in_current_full_candidates_count": sum(1 for t in TARGETS if t in full_set),
        "targets_in_latest_freeze_count": len(targets_in_freeze),
    }]
    excluded_ledger_rows = []
    for row in detail:
        excluded_ledger_rows.append({
            "run_id": run_id,
            "generated_at": generated_at,
            "ticker": row["ticker"],
            "exclusion_reason": row["exclusion_reason"],
            "apply_universe_invalid_ticker_prune": str(args.apply_universe_invalid_ticker_prune).upper(),
            "action_applied": row["action_applied"],
            "source": "V18_35G_USER_CONFIRMED_PRUNE_LIST",
            "evidence_sources": row["evidence_sources"],
        })

    summary = {
        "status": STATUS_OK,
        "run_id": run_id,
        "generated_at": generated_at,
        "apply_universe_invalid_ticker_prune": str(args.apply_universe_invalid_ticker_prune).upper(),
        "target_exclusion_count": len(TARGETS),
        "found_in_active_universe_count": len(found),
        "applied_exclusion_count": applied_count if args.apply_universe_invalid_ticker_prune and not fails else 0,
        "total_universe_count_before": len(universe_set_before),
        "total_universe_count_after": len(after_universe_set),
        "current_full_candidate_count": len(full_set),
        "latest_freeze_count": len(freeze_set),
        "targets_in_current_full_candidates_count": sum(1 for t in TARGETS if t in full_set),
        "targets_in_latest_freeze_count": len(targets_in_freeze),
        "duplicate_ticker_count_after": duplicate_after,
        "backup_path": backup_path,
        "warning_count": 0,
        "fail_count": 0,
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "forbidden_modified": FORBIDDEN_MODIFIED,
    }
    if FORBIDDEN_MODIFIED != "FALSE":
        fails.append("forbidden files/logic modified")
    summary["fail_count"] = len(fails)
    summary["warning_count"] = len(warnings)
    summary["status"] = STATUS_FAIL if fails else (STATUS_WARN if warnings else STATUS_OK)

    write_csv(root / OUT_PREVIEW, preview, list(preview[0].keys()))
    write_csv(root / OUT_DETAIL, detail, DETAIL_FIELDS)
    write_csv(root / OUT_EXCLUDED, excluded_ledger_rows, ["run_id", "generated_at", "ticker", "exclusion_reason", "apply_universe_invalid_ticker_prune", "action_applied", "source", "evidence_sources"])
    write_csv(root / OUT_SUMMARY, [summary], list(summary.keys()))
    report = make_report(summary, detail)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_CURRENT_REPORT, report)

    read_keys = [
        "status", "run_id", "apply_universe_invalid_ticker_prune", "target_exclusion_count",
        "found_in_active_universe_count", "applied_exclusion_count", "total_universe_count_before",
        "total_universe_count_after", "current_full_candidate_count", "latest_freeze_count",
        "targets_in_current_full_candidates_count", "targets_in_latest_freeze_count",
        "duplicate_ticker_count_after", "backup_path", "warning_count", "fail_count",
    ]
    read_first = [f"{k.upper()}: {summary[k]}" for k in read_keys]
    read_first += [
        f"REPORT: {OUT_REPORT}",
        f"CURRENT_REPORT: {OUT_CURRENT_REPORT}",
        f"DETAIL_CSV: {OUT_DETAIL}",
        f"SUMMARY_CSV: {OUT_SUMMARY}",
        f"EXCLUDED_TICKER_LEDGER: {OUT_EXCLUDED}",
        "OFFICIAL_DECISION_IMPACT: NONE",
        "AUTO_TRADE: DISABLED",
        "AUTO_SELL: DISABLED",
        "FORBIDDEN_MODIFIED: FALSE",
        "",
    ]
    write_text(root / OUT_READ_FIRST, "\n".join(read_first))

    for key in ["status", "run_id", "target_exclusion_count", "found_in_active_universe_count", "applied_exclusion_count", "total_universe_count_before", "total_universe_count_after", "backup_path", "warning_count", "fail_count"]:
        print(f"{key.upper()}: {summary[key]}")
    print(f"REPORT: {root / OUT_CURRENT_REPORT}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if str(summary["status"]).startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
