from __future__ import annotations

import argparse
import csv
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


STATUS_OK = "OK_V18_35F_NEXT_SIGNAL_FREEZE_EXPANSION_READY"
STATUS_WARN = "WARN_V18_35F_NEXT_SIGNAL_FREEZE_EXPANSION_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_35F_NEXT_SIGNAL_FREEZE_EXPANSION_FAILED"

AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FORBIDDEN_MODIFIED = "FALSE"

CURRENT_FULL = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
CURRENT_RANKED = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
CURRENT_TOP = "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"
E_BRIDGE = "outputs/v18/candidates/V18_35E_CANDIDATE_ADOPTION_BRIDGE.csv"
E_READY = "outputs/v18/candidates/V18_35E_NEXT_FREEZE_READINESS_CANDIDATES.csv"
E_REMAINING = "outputs/v18/candidates/V18_35E_REMAINING_UNCOMPUTED_TICKERS.csv"
E_FACTOR = "outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv"
E_TECH = "outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv"
FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
UNIVERSE = "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv"

OUT_PREVIEW = "outputs/v18/forward_test/V18_35F_NEXT_SIGNAL_FREEZE_EXPANSION_PREVIEW.csv"
OUT_ROWS = "outputs/v18/forward_test/V18_35F_NEXT_SIGNAL_FREEZE_EXPANSION_ROWS.csv"
OUT_DIFF = "outputs/v18/forward_test/V18_35F_FREEZE_EXPANSION_DIFF.csv"
OUT_SUMMARY = "outputs/v18/ops/V18_35F_NEXT_SIGNAL_FREEZE_EXPANSION_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_35F_NEXT_SIGNAL_FREEZE_EXPANSION_REPORT.md"
OUT_CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_NEXT_SIGNAL_FREEZE_EXPANSION.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_35F_READ_FIRST.txt"

LEDGER_FIELDS = [
    "signal_date", "run_id", "run_timestamp", "ticker", "source_rank", "factor_pack_rank",
    "factor_score", "technical_timing_score", "composite_candidate_score", "trust_level", "tier",
    "entry_reference_price", "price_asof_date", "data_freshness_status", "event_risk_status",
    "buy_permission", "official_decision_impact", "auto_trade", "auto_sell", "source_quality",
    "selected_source_file", "selected_source_file_mtime", "selected_source_file_size",
    "technical_source_file", "technical_source_file_mtime", "model_version", "pipeline_version",
    "notes", "forward_return_1d", "forward_return_3d", "forward_return_5d", "forward_return_10d",
    "forward_return_20d", "max_drawdown_after_signal", "max_runup_after_signal", "forward_fill_status",
]

DIFF_FIELDS = [
    "ticker", "in_latest_freeze", "in_current_full_candidates", "in_next_freeze_ready",
    "freeze_action", "previous_rank", "new_rank", "previous_score", "new_score", "score_source",
    "rank_source", "readiness_status", "validation_status", "evidence_sources",
]

REQUIRED_ROW_FIELDS = [
    "run_id", "signal_date", "ticker", "freeze_rank", "freeze_score", "source_candidate_file",
    "source_ranked_candidate_count", "freeze_expansion_mode", "readiness_status",
    "official_decision_impact", "auto_trade", "auto_sell", "generated_at",
]


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def norm(v: object) -> str:
    return str(v or "").strip().upper()


def truth(v: object) -> bool:
    return norm(v) == "TRUE"


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


def index_by_ticker(rows: Sequence[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {norm(r.get("ticker") or r.get("yf_ticker") or r.get("symbol")): r for r in rows if norm(r.get("ticker") or r.get("yf_ticker") or r.get("symbol"))}


def latest_freeze(rows: Sequence[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
    dates = sorted({str(r.get("signal_date", "")).strip() for r in rows if str(r.get("signal_date", "")).strip()})
    if not dates:
        return "", []
    date = dates[-1]
    return date, [r for r in rows if str(r.get("signal_date", "")).strip() == date]


def duplicate_ticker_count(rows: Sequence[dict[str, object]]) -> int:
    counts = Counter(norm(r.get("ticker")) for r in rows if norm(r.get("ticker")))
    return sum(1 for _, c in counts.items() if c > 1)


def duplicate_signal_ticker_count(rows: Sequence[dict[str, object]]) -> int:
    counts = Counter((str(r.get("signal_date", "")).strip(), norm(r.get("ticker"))) for r in rows)
    return sum(1 for key, c in counts.items() if key[0] and key[1] and c > 1)


def file_info(path: Path) -> tuple[str, str, str]:
    if not path.exists():
        return str(path), "", ""
    stat = path.stat()
    return str(path), datetime.fromtimestamp(stat.st_mtime).replace(microsecond=0).isoformat(), str(stat.st_size)


def first(row: dict[str, str], names: Sequence[str]) -> str:
    lower = {k.lower(): k for k in row}
    for name in names:
        key = lower.get(name.lower())
        if key and str(row.get(key, "")).strip():
            return str(row.get(key, "")).strip()
    return ""


def sort_candidates(rows: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    def key(pair: tuple[int, dict[str, str]]) -> tuple[float, int]:
        idx, row = pair
        try:
            return float(first(row, ["rank", "source_rank", "candidate_rank"])), idx
        except Exception:
            return float(idx + 1), idx
    return [r for _, r in sorted(enumerate(rows), key=key)]


def score_ok(row: dict[str, str]) -> bool:
    return bool(first(row, ["rank", "source_rank"]) and first(row, ["composite_candidate_score", "candidate_score", "score"]))


def build_freeze_rows(root: Path, candidates: list[dict[str, str]], signal_date: str, run_id: str, generated_at: str, mode: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    factor_rows, _ = read_csv(root / E_FACTOR)
    tech_rows, _ = read_csv(root / E_TECH)
    factor_idx = index_by_ticker(factor_rows)
    tech_idx = index_by_ticker(tech_rows)
    selected_file, selected_mtime, selected_size = file_info(root / CURRENT_FULL)
    technical_file, technical_mtime, _ = file_info(root / E_TECH)
    out: list[dict[str, object]] = []
    expansion_rows: list[dict[str, object]] = []
    for index, row in enumerate(sort_candidates(candidates), 1):
        ticker = norm(row.get("ticker"))
        factor = factor_idx.get(ticker, {})
        tech = tech_idx.get(ticker, {})
        source_rank = first(row, ["rank", "source_rank", "candidate_rank"]) or str(index)
        factor_rank = first(row, ["factor_pack_rank", "factor_rank"]) or first(factor, ["factor_pack_rank", "factor_rank", "rank"])
        factor_score = first(row, ["factor_score", "factor_pack_score"]) or first(factor, ["factor_score", "factor_pack_score"])
        tech_score = first(row, ["technical_timing_score", "technical_score"]) or first(tech, ["technical_timing_score", "technical_score"])
        composite = first(row, ["composite_candidate_score", "candidate_score", "score"])
        entry_price = first(row, ["entry_reference_price", "reference_price", "latest_close", "close", "price"]) or first(tech, ["entry_reference_price", "reference_price", "latest_close", "close", "price"]) or first(factor, ["entry_reference_price", "reference_price", "latest_close", "close", "price"])
        price_date = first(row, ["price_asof_date", "latest_price_date", "price_date", "date"]) or first(tech, ["price_asof_date", "latest_price_date", "price_date", "date"]) or first(factor, ["price_asof_date", "latest_price_date", "price_date", "date"])
        ledger_row = {
            "signal_date": signal_date, "run_id": run_id, "run_timestamp": generated_at,
            "ticker": ticker, "source_rank": source_rank, "factor_pack_rank": factor_rank,
            "factor_score": factor_score, "technical_timing_score": tech_score,
            "composite_candidate_score": composite, "trust_level": first(row, ["trust_level"]),
            "tier": first(row, ["tier"]), "entry_reference_price": entry_price,
            "price_asof_date": price_date,
            "data_freshness_status": first(row, ["data_freshness_status", "freshness_status", "score_source_status"]) or first(row, ["score_source_status"]),
            "event_risk_status": first(row, ["event_risk_status", "event_risk", "risk_status"]),
            "buy_permission": first(row, ["buy_permission", "buy_permission_status", "final_action", "execution_status"]),
            "official_decision_impact": OFFICIAL_DECISION_IMPACT, "auto_trade": AUTO_TRADE, "auto_sell": AUTO_SELL,
            "source_quality": "OK_V18_35F_RECOMPUTED_CANDIDATE_FREEZE_SOURCE",
            "selected_source_file": selected_file, "selected_source_file_mtime": selected_mtime,
            "selected_source_file_size": selected_size, "technical_source_file": technical_file,
            "technical_source_file_mtime": technical_mtime, "model_version": "V18.35F-FREEZE-EXPANSION",
            "pipeline_version": "V18.35F",
            "notes": "V18.35F next signal freeze expansion from recomputed full candidates; forward return fields intentionally pending.",
            "forward_return_1d": "", "forward_return_3d": "", "forward_return_5d": "", "forward_return_10d": "",
            "forward_return_20d": "", "max_drawdown_after_signal": "", "max_runup_after_signal": "",
            "forward_fill_status": "PENDING_FORWARD_RETURN_FILL",
        }
        out.append(ledger_row)
        expansion_rows.append({
            **ledger_row,
            "freeze_rank": source_rank,
            "freeze_score": composite,
            "source_candidate_file": CURRENT_FULL,
            "source_ranked_candidate_count": len(candidates),
            "freeze_expansion_mode": mode,
            "readiness_status": "READY_FOR_NEXT_FREEZE_REVIEW",
            "generated_at": generated_at,
        })
    return out, expansion_rows


def build_diff(latest_rows: list[dict[str, str]], candidates: list[dict[str, str]], ready_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    latest_idx = index_by_ticker(latest_rows)
    cand_idx = index_by_ticker(candidates)
    ready_idx = index_by_ticker(ready_rows)
    out = []
    for ticker in sorted(set(latest_idx) | set(cand_idx) | set(ready_idx)):
        in_latest = ticker in latest_idx
        in_current = ticker in cand_idx
        in_ready = ticker in ready_idx
        if in_latest and in_current:
            action = "KEEP_EXISTING_FREEZE"
            validation = "OK"
        elif in_current and in_ready:
            action = "ADD_NEW_READY_CANDIDATE"
            validation = "OK"
        elif in_latest and not in_current:
            action = "EXCLUDE_NOT_IN_CURRENT_FULL_CANDIDATES"
            validation = "REVIEW"
        elif in_current and not in_ready:
            action = "REVIEW_NOT_READY"
            validation = "OK_EXISTING_OR_CURRENT_FULL"
        else:
            action = "UNKNOWN"
            validation = "REVIEW"
        prev = latest_idx.get(ticker, {})
        cur = cand_idx.get(ticker, {})
        ready = ready_idx.get(ticker, {})
        out.append({
            "ticker": ticker,
            "in_latest_freeze": str(in_latest).upper(),
            "in_current_full_candidates": str(in_current).upper(),
            "in_next_freeze_ready": str(in_ready).upper(),
            "freeze_action": action,
            "previous_rank": first(prev, ["source_rank", "rank"]),
            "new_rank": first(cur, ["rank", "source_rank"]),
            "previous_score": first(prev, ["composite_candidate_score", "score"]),
            "new_score": first(cur, ["composite_candidate_score", "score"]),
            "score_source": first(cur, ["score_source_files", "primary_score_source_files"]) or CURRENT_FULL,
            "rank_source": first(cur, ["ranking_source_policy"]) or CURRENT_FULL,
            "readiness_status": first(ready, ["freeze_readiness_status"]) or ("ALREADY_IN_LATEST_FREEZE" if in_latest else "CURRENT_FULL_CANDIDATE"),
            "validation_status": validation,
            "evidence_sources": ";".join(x for x in [FREEZE_LEDGER if in_latest else "", CURRENT_FULL if in_current else "", E_READY if in_ready else ""] if x),
        })
    return out


def make_report(summary: dict[str, object], diff_rows: list[dict[str, object]], checks: list[dict[str, object]]) -> str:
    add_rows = [r for r in diff_rows if r.get("freeze_action") == "ADD_NEW_READY_CANDIDATE"]
    lines = [
        "# V18.35F 下一次信号冻结扩展",
        "",
        f"- STATUS: `{summary['status']}`",
        f"- RUN_ID: `{summary['run_id']}`",
        f"- SIGNAL_DATE: `{summary['signal_date']}`",
        "",
        "## 说明",
        "V18.35E 已经把 recomputed full candidates 接管到 318，但 latest signal freeze 仍是 252。V18.35F 的作用是把新的 318 候选写成下一次 signal freeze 批次，让后续 V18.35A、forward tracker 和日报使用 318 freeze 口径。",
        "这不是篡改历史账本；apply 时会先备份，然后对同一 signal_date 做安全替换，或对新 signal_date 追加新批次。",
        "",
        "## Freeze Before/After Count Table",
        "| item | count/status |",
        "| --- | ---: |",
        f"| latest freeze before | {summary['latest_freeze_count_before']} |",
        f"| current full candidates | {summary['current_full_candidate_count']} |",
        f"| new ready candidates | {summary['new_ready_candidate_count']} |",
        f"| planned freeze rows | {summary['planned_new_freeze_count']} |",
        f"| post-apply latest freeze | {summary['post_apply_latest_freeze_count']} |",
        f"| post-apply matches current full | {summary['post_apply_matches_current_full_candidates']} |",
        "",
        "## Add New Ready Candidate Samples",
        "| ticker | new_rank | new_score |",
        "| --- | ---: | ---: |",
    ]
    for row in add_rows[:30]:
        lines.append(f"| `{row.get('ticker')}` | {row.get('new_rank')} | {row.get('new_score')} |")
    lines += ["", "## Validation Checks", "| check | status | detail |", "| --- | --- | --- |"]
    for row in checks:
        lines.append(f"| {row.get('check')} | `{row.get('status')}` | {row.get('detail')} |")
    lines += [
        "",
        "## Operator Next Action",
        "- 如果 apply 尚未执行，先人工检查 preview/diff 后再用 `-ApplyNextSignalFreezeExpansion`。",
        "- apply 后运行 V18.35A，确认 latest freeze 与 current candidates 已进入 318 口径。",
        "- AUTO_TRADE/AUTO_SELL 仍然禁用，因为本步骤只冻结观察/验证候选，不下单、不调用券商、不改变账户逻辑。",
        "",
        "## Final Conclusion",
        "Signal freeze expansion preview/apply completed.",
        "Freeze ledger backup created if apply was used.",
        "No trading/order/account logic was modified.",
        "AUTO_TRADE DISABLED, AUTO_SELL DISABLED, OFFICIAL_DECISION_IMPACT NONE.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--apply-next-signal-freeze-expansion", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    run_id = "V18_35F_" + stamp()
    generated_at = iso_now()
    signal_date = datetime.now().date().isoformat()
    warnings: list[str] = []
    fails: list[str] = []
    backup_path = "NONE"

    candidates, candidate_fields = read_csv(root / CURRENT_FULL)
    ledger_rows, ledger_fields = read_csv(root / FREEZE_LEDGER)
    ready_rows, _ = read_csv(root / E_READY)
    bridge_rows, _ = read_csv(root / E_BRIDGE)
    if not candidates:
        fails.append("current full candidates cannot be read")
    if not ledger_rows or not ledger_fields:
        fails.append("freeze ledger cannot be read")
    if ledger_fields and ledger_fields != LEDGER_FIELDS:
        fails.append("freeze ledger schema is not R21-compatible")

    latest_signal_date, latest_rows = latest_freeze(ledger_rows)
    latest_set = ticker_set(latest_rows)
    current_set = ticker_set(candidates)
    ready_set = ticker_set(ready_rows)
    duplicate_candidate = duplicate_ticker_count(candidates)
    duplicate_latest = duplicate_ticker_count(latest_rows)
    same_day_existing = [r for r in ledger_rows if str(r.get("signal_date", "")).strip() == signal_date]
    mode = "SAME_DAY_REPLACE_252_TO_318" if same_day_existing else "APPEND_NEW_SIGNAL_DATE_318"
    freeze_rows, expansion_rows = build_freeze_rows(root, candidates, signal_date, run_id, generated_at, mode)
    planned_dup = duplicate_signal_ticker_count(freeze_rows)
    diff_rows = build_diff(latest_rows, candidates, ready_rows)

    add_count = sum(1 for r in diff_rows if r["freeze_action"] == "ADD_NEW_READY_CANDIDATE")
    keep_count = sum(1 for r in diff_rows if r["freeze_action"] == "KEEP_EXISTING_FREEZE")
    missing_ready = sorted((current_set - latest_set) - ready_set)
    blank_score_rows = [r for r in candidates if not score_ok(r)]

    checks = [
        {"check": "current_full_readable", "status": "PASS" if candidates else "FAIL", "detail": len(candidates)},
        {"check": "candidate_count_ge_latest_freeze", "status": "PASS" if len(candidates) >= len(latest_set) else "FAIL", "detail": f"{len(candidates)} >= {len(latest_set)}"},
        {"check": "new_additions_in_v18_35e_ready", "status": "PASS" if not missing_ready else "WARN", "detail": len(missing_ready)},
        {"check": "duplicate_candidate_ticker_count", "status": "PASS" if duplicate_candidate == 0 else "FAIL", "detail": duplicate_candidate},
        {"check": "duplicate_latest_freeze_ticker_count", "status": "PASS" if duplicate_latest == 0 else "FAIL", "detail": duplicate_latest},
        {"check": "all_candidates_have_rank_and_score", "status": "PASS" if not blank_score_rows else "FAIL", "detail": len(blank_score_rows)},
        {"check": "planned_rows_match_current_full", "status": "PASS" if len(freeze_rows) == len(candidates) else "FAIL", "detail": f"{len(freeze_rows)} vs {len(candidates)}"},
        {"check": "planned_signal_date_ticker_duplicates", "status": "PASS" if planned_dup == 0 else "FAIL", "detail": planned_dup},
    ]
    for c in checks:
        if c["status"] == "FAIL":
            fails.append(str(c["check"]))
        elif c["status"] == "WARN":
            warnings.append(str(c["check"]))

    write_csv(root / OUT_PREVIEW, [{
        "run_id": run_id, "generated_at": generated_at, "signal_date": signal_date,
        "latest_signal_date_before": latest_signal_date, "freeze_expansion_mode": mode,
        "apply_next_signal_freeze_expansion": str(args.apply_next_signal_freeze_expansion).upper(),
        "latest_freeze_count_before": len(latest_set), "current_full_candidate_count": len(candidates),
        "planned_new_freeze_count": len(freeze_rows), "new_ready_candidate_count": len(ready_set),
        "add_new_ready_candidate_count": add_count, "keep_existing_freeze_count": keep_count,
    }], ["run_id", "generated_at", "signal_date", "latest_signal_date_before", "freeze_expansion_mode", "apply_next_signal_freeze_expansion", "latest_freeze_count_before", "current_full_candidate_count", "planned_new_freeze_count", "new_ready_candidate_count", "add_new_ready_candidate_count", "keep_existing_freeze_count"])
    row_fields = list(dict.fromkeys(REQUIRED_ROW_FIELDS + LEDGER_FIELDS))
    write_csv(root / OUT_ROWS, expansion_rows, row_fields)
    write_csv(root / OUT_DIFF, diff_rows, DIFF_FIELDS)

    applied = False
    post_latest_count = len(latest_set)
    post_match = "FALSE"
    post_dup = duplicate_signal_ticker_count(ledger_rows)
    if args.apply_next_signal_freeze_expansion and not fails:
        try:
            backup_dir = root / "archive/v18/next_signal_freeze_expansion_backups" / run_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_file = backup_dir / "V18_DAILY_SIGNAL_FREEZE_LEDGER_PRE_V18_35F.csv"
            shutil.copy2(root / FREEZE_LEDGER, backup_file)
            backup_path = str(backup_dir)
            kept = [r for r in ledger_rows if str(r.get("signal_date", "")).strip() != signal_date]
            write_csv(root / FREEZE_LEDGER, kept + freeze_rows, LEDGER_FIELDS)
            applied = True
            post_rows, _ = read_csv(root / FREEZE_LEDGER)
            post_signal, post_latest_rows = latest_freeze(post_rows)
            post_set = ticker_set(post_latest_rows)
            post_latest_count = len(post_set)
            post_match = str(post_signal == signal_date and post_set == current_set).upper()
            post_dup = duplicate_signal_ticker_count(post_rows)
            if post_latest_count != len(candidates):
                fails.append("post-apply latest freeze count does not equal current full candidate count")
            if post_match != "TRUE":
                fails.append("post-apply latest freeze does not match current full candidates")
            if post_dup:
                fails.append("post-apply duplicate signal_date+ticker count is nonzero")
        except Exception as exc:
            fails.append(f"backup/write operation fails in apply mode: {type(exc).__name__}")
    elif not args.apply_next_signal_freeze_expansion:
        warnings.append("preview is ready but apply mode not used")
        if len(latest_set) < len(candidates):
            warnings.append("freeze remains smaller than current full candidates")

    if FORBIDDEN_MODIFIED != "FALSE":
        fails.append("forbidden files/logic modified")

    summary = {
        "status": STATUS_OK,
        "run_id": run_id,
        "generated_at": generated_at,
        "apply_next_signal_freeze_expansion": str(args.apply_next_signal_freeze_expansion).upper(),
        "signal_date": signal_date,
        "freeze_expansion_mode": mode,
        "latest_freeze_count_before": len(latest_set),
        "current_full_candidate_count": len(candidates),
        "planned_new_freeze_count": len(freeze_rows),
        "new_ready_candidate_count": len(ready_set),
        "add_new_ready_candidate_count": add_count,
        "keep_existing_freeze_count": keep_count,
        "post_apply_latest_freeze_count": post_latest_count,
        "post_apply_matches_current_full_candidates": post_match,
        "duplicate_candidate_ticker_count": duplicate_candidate,
        "duplicate_planned_signal_date_ticker_count": planned_dup,
        "duplicate_post_apply_signal_date_ticker_count": post_dup,
        "backup_path": backup_path,
        "warning_count": 0,
        "fail_count": 0,
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "forbidden_modified": FORBIDDEN_MODIFIED,
    }
    if applied and len(latest_set) < len(candidates):
        warnings.append("V18.35A should now recognize expanded latest freeze after rerun")
    summary["fail_count"] = len(fails)
    summary["warning_count"] = len(warnings)
    summary["status"] = STATUS_FAIL if fails else (STATUS_WARN if warnings else STATUS_OK)

    write_csv(root / OUT_SUMMARY, [summary], list(summary.keys()))
    report = make_report(summary, diff_rows, checks)
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_CURRENT_REPORT, report)

    read_keys = [
        "status", "run_id", "apply_next_signal_freeze_expansion", "signal_date", "freeze_expansion_mode",
        "latest_freeze_count_before", "current_full_candidate_count", "planned_new_freeze_count",
        "new_ready_candidate_count", "add_new_ready_candidate_count", "keep_existing_freeze_count",
        "post_apply_latest_freeze_count", "post_apply_matches_current_full_candidates",
        "duplicate_candidate_ticker_count", "duplicate_planned_signal_date_ticker_count",
        "duplicate_post_apply_signal_date_ticker_count", "backup_path", "warning_count", "fail_count",
    ]
    read_first = [f"{k.upper()}: {summary[k]}" for k in read_keys]
    read_first += [
        f"REPORT: {OUT_REPORT}",
        f"CURRENT_REPORT: {OUT_CURRENT_REPORT}",
        f"PREVIEW_CSV: {OUT_PREVIEW}",
        f"FREEZE_ROWS_CSV: {OUT_ROWS}",
        f"DIFF_CSV: {OUT_DIFF}",
        f"SUMMARY_CSV: {OUT_SUMMARY}",
        f"LEDGER_PATH: {FREEZE_LEDGER}",
        "OFFICIAL_DECISION_IMPACT: NONE",
        "AUTO_TRADE: DISABLED",
        "AUTO_SELL: DISABLED",
        "FORBIDDEN_MODIFIED: FALSE",
        "",
    ]
    write_text(root / OUT_READ_FIRST, "\n".join(read_first))

    for key in ["status", "run_id", "signal_date", "freeze_expansion_mode", "latest_freeze_count_before", "current_full_candidate_count", "planned_new_freeze_count", "post_apply_latest_freeze_count", "backup_path", "warning_count", "fail_count"]:
        print(f"{key.upper()}: {summary[key]}")
    print(f"REPORT: {root / OUT_CURRENT_REPORT}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if str(summary["status"]).startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
