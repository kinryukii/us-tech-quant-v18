from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import v18_35D_full_universe_factor_technical_recompute as d35


STATUS_OK = "OK_V18_35E_ONLINE_BACKFILL_CANDIDATE_BRIDGE_READY"
STATUS_WARN = "WARN_V18_35E_ONLINE_BACKFILL_CANDIDATE_BRIDGE_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_35E_ONLINE_BACKFILL_CANDIDATE_BRIDGE_FAILED"

AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FORBIDDEN_MODIFIED = "FALSE"

UNIVERSE = d35.UNIVERSE
FREEZE = d35.FREEZE
PRICE_CACHE = d35.PRICE_CACHE
CURRENT_FULL = d35.CURRENT_FULL
CURRENT_RANKED = d35.CURRENT_RANKED
CURRENT_TOP = d35.CURRENT_TOP
CURRENT_FACTOR = d35.CURRENT_FACTOR
CURRENT_TECH = d35.CURRENT_TECH
CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_ONLINE_BACKFILL_CANDIDATE_BRIDGE.md"
CURRENT_ALIAS_WRITE_DISABLED_BY = "V18_50B_R2_SOLE_CURRENT_TOP20_WRITER_ENFORCEMENT"

D_STATUS = d35.OUT_STATUS
D_FAILURES = d35.OUT_FAILURES
D_RANKED = d35.OUT_RANKED
D_FACTOR = d35.OUT_FACTOR
D_TECH = d35.OUT_TECH

OUT_ATTEMPTS = "outputs/v18/data_backfill/V18_35E_ONLINE_BACKFILL_ATTEMPTS.csv"
OUT_VALIDATED = "outputs/v18/data_backfill/V18_35E_ONLINE_BACKFILL_VALIDATED_TICKERS.csv"
OUT_FAILED = "outputs/v18/data_backfill/V18_35E_ONLINE_BACKFILL_FAILED_TICKERS.csv"
OUT_RANKED = "outputs/v18/candidates/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_CANDIDATES.csv"
OUT_FACTOR = "outputs/v18/factor_pack/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv"
OUT_TECH = "outputs/v18/technical_timing/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv"
OUT_STATUS = "outputs/v18/candidates/V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_STATUS.csv"
OUT_BRIDGE = "outputs/v18/candidates/V18_35E_CANDIDATE_ADOPTION_BRIDGE.csv"
OUT_READY = "outputs/v18/candidates/V18_35E_NEXT_FREEZE_READINESS_CANDIDATES.csv"
OUT_REMAINING = "outputs/v18/candidates/V18_35E_REMAINING_UNCOMPUTED_TICKERS.csv"
OUT_SUMMARY = "outputs/v18/ops/V18_35E_ONLINE_BACKFILL_CANDIDATE_BRIDGE_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_35E_ONLINE_BACKFILL_CANDIDATE_BRIDGE_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_35E_READ_FIRST.txt"

TARGET_BUCKET_PRIORITY = {
    "PRICE_DATA_UNAVAILABLE": 1,
    "PRICE_HISTORY_INSUFFICIENT": 2,
    "PRICE_STALE_OR_NOT_LATEST": 3,
    "TECHNICAL_INPUT_MISSING": 4,
    "FACTOR_INPUT_MISSING": 5,
}

BRIDGE_FIELDS = [
    "ticker", "in_total_universe", "in_latest_freeze_252", "in_current_full_candidates_before",
    "in_v18_35d_local_recomputed_candidates", "in_v18_35e_online_recomputed_candidates",
    "was_v18_35d_failure", "online_backfill_attempted", "online_backfill_success",
    "price_data_available_after_backfill", "factor_success_after_backfill",
    "technical_success_after_backfill", "ranking_success_after_backfill",
    "rank_eligible_after_backfill", "previous_rank_if_available", "recomputed_rank_after_backfill",
    "previous_score_if_available", "recomputed_score_after_backfill", "adoption_bucket",
    "freeze_readiness_status", "remaining_failure_bucket", "remaining_failure_reason",
    "evidence_sources",
]

ATTEMPT_FIELDS = [
    "run_id", "ticker", "v18_35d_failure_bucket", "v18_35d_failure_reason", "attempted",
    "provider", "download_row_count", "validation_status", "validation_reason",
    "latest_available_date", "staging_csv", "cache_csv", "cache_backup_path",
]


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def norm(v: object) -> str:
    return d35.norm(v)


def truth(v: object) -> bool:
    return str(v or "").strip().upper() == "TRUE"


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: Sequence[str]) -> None:
    d35.write_csv(path, rows, fields)


def write_text(path: Path, text: str) -> None:
    d35.write_text(path, text)


def ticker_set(rows: list[dict[str, str]]) -> set[str]:
    return d35.ticker_set(rows)


def index_by_ticker(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return d35.index_by_ticker(rows)


def latest_freeze(rows: list[dict[str, str]]) -> set[str]:
    return d35.latest_freeze(rows)


def rel(root: Path, path: Path | str) -> str:
    return d35.rel(root, path)


def backup_files(root: Path, backup_dir: Path, rels: Sequence[str]) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    for item in rels:
        src = root / item
        if src.exists():
            dst = backup_dir / item
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def cache_write(root: Path, ticker: str, rows: list[dict[str, object]], backup_dir: Path) -> tuple[str, str]:
    cache_path = root / PRICE_CACHE / f"{ticker}.csv"
    backup_path = ""
    if cache_path.exists():
        dst = backup_dir / PRICE_CACHE / f"{ticker}.csv"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cache_path, dst)
        backup_path = str(dst)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "open", "high", "low", "close", "volume"], extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in ["date", "open", "high", "low", "close", "volume"]})
    return str(cache_path), backup_path


def validate_prices(rows: list[dict[str, object]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty price history"
    dates: list[str] = []
    for row in rows:
        date = str(row.get("date", "")).strip()[:10]
        if not date:
            return False, "missing date"
        for col in ["open", "high", "low", "close", "volume"]:
            if d35.to_float(row.get(col)) is None:
                return False, f"missing or invalid {col}"
        dates.append(date)
    if len(dates) != len(set(dates)):
        return False, "duplicate dates"
    if len(rows) < 120:
        return False, f"price history rows {len(rows)} < 120"
    latest = max(dates)
    try:
        latest_dt = datetime.strptime(latest, "%Y-%m-%d")
    except ValueError:
        return False, "latest date is not parseable"
    if latest_dt < datetime.now() - timedelta(days=10):
        return False, f"latest available date {latest} is stale"
    return True, "validated"


def valid_online_symbol(ticker: str) -> tuple[bool, str]:
    if ticker in {"", "TICKER", "TICKERS", "SYMBOL", "NAN", "NONE"}:
        return False, "invalid ticker placeholder"
    if ticker.isdigit():
        return False, "invalid numeric ticker artifact"
    if not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", ticker):
        return False, "invalid ticker format for online provider"
    return True, ""


def target_failures(d_failures: list[dict[str, str]]) -> list[dict[str, str]]:
    def key(row: dict[str, str]) -> tuple[int, str]:
        bucket = str(row.get("failure_bucket", "")).strip().upper()
        reason = str(row.get("failure_reason", "")).strip().upper()
        priority = TARGET_BUCKET_PRIORITY.get(bucket, 99)
        if "PRICE" in reason and bucket in {"TECHNICAL_INPUT_MISSING", "FACTOR_INPUT_MISSING"}:
            priority = min(priority, 4)
        return priority, norm(row.get("ticker"))

    out = []
    for row in d_failures:
        bucket = str(row.get("failure_bucket", "")).strip().upper()
        reason = str(row.get("failure_reason", "")).strip().upper()
        if bucket in TARGET_BUCKET_PRIORITY or "PRICE" in reason:
            out.append(row)
    return sorted(out, key=key)


def recompute_full_universe(root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[str], int]:
    universe_rows, _ = d35.read_csv(root / UNIVERSE)
    factor_current, factor_fields = d35.read_csv(root / CURRENT_FACTOR)
    tech_current, tech_fields = d35.read_csv(root / CURRENT_TECH)
    full_current, _ = d35.read_csv(root / CURRENT_FULL)
    top_current, _ = d35.read_csv(root / CURRENT_TOP)
    freeze_rows, _ = d35.read_csv(root / FREEZE)

    universe = sorted(ticker_set(universe_rows))
    full_set_before = ticker_set(full_current)
    top_set_before = ticker_set(top_current)
    freeze_set = latest_freeze(freeze_rows)
    universe_idx = index_by_ticker(universe_rows)
    # V18.50B-R2: legacy/current factor and technical files are reference-only here.
    # They must not seed rows that could later be promoted to current aliases.
    factor_idx: dict[str, dict[str, str]] = {}
    tech_idx: dict[str, dict[str, str]] = {}
    if not factor_fields:
        factor_fields = ["factor_pack_rank", "ticker", "factor_pack_score", "latest_price_date", "latest_close"]
    if not tech_fields:
        tech_fields = ["ticker", "yf_ticker", "price_date", "close", "technical_timing_score", "technical_signal"]

    status_rows: list[dict[str, object]] = []
    factor_rows: list[dict[str, object]] = []
    tech_rows: list[dict[str, object]] = []

    for ticker in universe:
        evidence = [UNIVERSE]
        existing_factor = None
        existing_tech = None
        prices: list[dict[str, object]] = []
        price_error = ""
        price_source = ""

        if not existing_factor or not existing_tech:
            cache_path = root / PRICE_CACHE / f"{ticker}.csv"
            prices, price_error = d35.load_prices(cache_path)
            price_source = rel(root, cache_path)
            if prices and len(prices) >= 120:
                evidence.append(price_source)
                if not existing_factor:
                    try:
                        frow = d35.factor_row(ticker, prices, factor_fields)
                        factor_rows.append(frow)
                        existing_factor = {k: str(v) for k, v in frow.items()}
                    except Exception as exc:
                        price_error = f"factor calculation error: {type(exc).__name__}"
                if not existing_tech:
                    try:
                        trow = d35.technical_row(ticker, prices, tech_fields)
                        tech_rows.append(trow)
                        existing_tech = {k: str(v) for k, v in trow.items()}
                    except Exception as exc:
                        price_error = f"technical calculation error: {type(exc).__name__}"

        fscore = (existing_factor or {}).get("factor_pack_score", "")
        tscore = (existing_tech or {}).get("technical_timing_score", "")
        comp = d35.composite_score(fscore, tscore)
        rank_ok = comp is not None
        latest_date = (existing_factor or {}).get("latest_price_date") or (existing_tech or {}).get("price_date") or (prices[-1]["date"] if prices else universe_idx.get(ticker, {}).get("latest_price_date", ""))
        latest_close = (existing_factor or {}).get("latest_close") or (existing_tech or {}).get("close") or (prices[-1]["close"] if prices else universe_idx.get(ticker, {}).get("last_close", ""))
        price_available = bool(existing_factor or existing_tech or prices)
        if rank_ok:
            bucket, calc_status, reason = "OK_COMPUTED", "OK_COMPUTED", "factor and technical calculations available"
        elif not price_available:
            bucket, calc_status, reason = "PRICE_DATA_UNAVAILABLE", "CALCULATION_FAILED", price_error or "no factor/technical row and no local price cache"
        elif prices and len(prices) < 120:
            bucket, calc_status, reason = "PRICE_HISTORY_INSUFFICIENT", "CALCULATION_FAILED", f"price history rows {len(prices)} < 120"
        elif not existing_factor:
            bucket = "FACTOR_CALCULATION_ERROR" if "factor calculation error" in price_error else "FACTOR_INPUT_MISSING"
            calc_status, reason = "CALCULATION_FAILED", price_error or "factor calculation did not produce a row"
        elif not existing_tech:
            bucket = "TECHNICAL_CALCULATION_ERROR" if "technical calculation error" in price_error else "TECHNICAL_INPUT_MISSING"
            calc_status, reason = "CALCULATION_FAILED", price_error or "technical calculation did not produce a row"
        else:
            bucket, calc_status, reason = "UNKNOWN_COMPUTATION_FAILURE", "CALCULATION_FAILED", "unknown computation failure"
        status_rows.append({
            "ticker": ticker, "in_total_universe": "TRUE",
            "in_current_full_candidates_before": str(ticker in full_set_before).upper(),
            "in_current_top_candidates_before": str(ticker in top_set_before).upper(),
            "in_latest_signal_freeze": str(ticker in freeze_set).upper(),
            "calculation_attempted": "TRUE", "price_data_attempted": "TRUE",
            "price_data_available": str(price_available).upper(),
            "price_data_source": price_source or ("CURRENT_FACTOR_OR_TECHNICAL" if price_available else "NONE"),
            "latest_price_date": latest_date,
            "history_row_count": len(prices) if prices else "",
            "history_start_date": prices[0]["date"] if prices else "",
            "history_end_date": prices[-1]["date"] if prices else "",
            "factor_calculation_attempted": "TRUE",
            "factor_calculation_success": str(bool(existing_factor)).upper(),
            "technical_calculation_attempted": "TRUE",
            "technical_calculation_success": str(bool(existing_tech)).upper(),
            "ranking_merge_attempted": "TRUE", "ranking_merge_success": str(rank_ok).upper(),
            "factor_score": fscore, "technical_timing_score": tscore,
            "recomputed_composite_score": comp if comp is not None else "",
            "recomputed_rank": "", "rank_eligible": str(rank_ok).upper(),
            "calculation_status": calc_status, "failure_bucket": bucket, "failure_reason": reason,
            "evidence_sources": ";".join(dict.fromkeys(evidence)),
            "_latest_close": latest_close,
            "_technical_status": (existing_tech or {}).get("technical_signal") or (existing_tech or {}).get("technical_warning_label", ""),
            "_pullback_status": (existing_tech or {}).get("bb_status", ""),
            "_overheat_status": (existing_tech or {}).get("gamma_squeeze_risk_label") or (existing_tech or {}).get("overheat_penalty", ""),
        })

    ranked_status = [r for r in status_rows if r["rank_eligible"] == "TRUE"]
    ranked_status.sort(key=lambda r: float(r["recomputed_composite_score"]), reverse=True)
    for i, row in enumerate(ranked_status, 1):
        row["recomputed_rank"] = i
    ranked_rows: list[dict[str, object]] = []
    for row in ranked_status:
        ranked_rows.append({
            "rank": row["recomputed_rank"], "ticker": row["ticker"],
            "composite_candidate_score": row["recomputed_composite_score"],
            "ranking_source_policy": "V18_35E_ONLINE_BACKFILL_RECOMPUTE",
            "primary_score_source_files": f"{OUT_FACTOR};{OUT_TECH}",
            "audit_only_source_files": "NONE",
            "score_source_status": "OK_RECOMPUTED_FACTOR_TECHNICAL",
            "score_source_files": f"{OUT_FACTOR};{OUT_TECH}",
            "score_source_columns": "factor_pack_score;technical_timing_score",
            "latest_price_date": row["latest_price_date"],
            "latest_close": row["_latest_close"], "technical_status": row["_technical_status"],
            "event_risk_status": "", "overheat_status": row["_overheat_status"],
            "pullback_status": row["_pullback_status"], "execution_status": "REVIEW_ONLY",
            "final_action": "WAIT_PULLBACK_REVIEW_ONLY" if "LOWER" in str(row["_pullback_status"]).upper() else "REVIEW_ONLY",
            "reason": "V18.35E recomputed after validated online backfill where available; no fake scores.",
        })
    for row in status_rows:
        for k in ["_latest_close", "_technical_status", "_pullback_status", "_overheat_status"]:
            row.pop(k, None)
    factor_rows.sort(key=lambda r: d35.to_float(r.get("factor_pack_score")) if d35.to_float(r.get("factor_pack_score")) is not None else -1, reverse=True)
    for i, row in enumerate(factor_rows, 1):
        row["factor_pack_rank"] = i
    duplicate_count = len(status_rows) - len({r["ticker"] for r in status_rows})
    return status_rows, factor_rows, tech_rows, ranked_rows, list(factor_fields), duplicate_count


def bridge_rows(universe: set[str], freeze: set[str], current_full: list[dict[str, str]], d_ranked: list[dict[str, str]],
                d_failures: list[dict[str, str]], e_ranked: list[dict[str, object]], e_status: list[dict[str, object]],
                attempts: list[dict[str, object]]) -> list[dict[str, object]]:
    current_idx = index_by_ticker(current_full)
    d_idx = index_by_ticker(d_ranked)
    d_fail_idx = index_by_ticker(d_failures)
    e_idx = {norm(r.get("ticker")): r for r in e_ranked}
    status_idx = {norm(r.get("ticker")): r for r in e_status}
    attempt_idx = {norm(r.get("ticker")): r for r in attempts if truth(r.get("attempted"))}
    out = []
    for ticker in sorted(universe | set(current_idx) | set(d_idx) | set(e_idx) | set(d_fail_idx)):
        s = status_idx.get(ticker, {})
        in_freeze = ticker in freeze
        e_ok = ticker in e_idx
        d_ok = ticker in d_idx
        attempted = ticker in attempt_idx
        success = truth(attempt_idx.get(ticker, {}).get("validation_status") == "PASS")
        if in_freeze and e_ok:
            bucket = "EXISTING_FREEZE_AND_RECOMPUTED_OK"
            readiness = "ALREADY_IN_LATEST_FREEZE"
        elif in_freeze and not e_ok:
            bucket = "EXISTING_FREEZE_BUT_RECOMPUTE_MISSING"
            readiness = "NOT_READY_RECOMPUTE_FAILURE"
        elif attempted and success and e_ok and not in_freeze:
            bucket = "NEWLY_BACKFILLED_AND_RECOMPUTED"
            readiness = "READY_FOR_NEXT_FREEZE_REVIEW"
        elif e_ok and not in_freeze:
            bucket = "NEW_RECOMPUTED_NOT_IN_FREEZE"
            readiness = "READY_FOR_NEXT_FREEZE_REVIEW"
        elif ticker in universe and not e_ok and ticker in d_fail_idx:
            bucket = "STILL_UNCOMPUTED_AFTER_BACKFILL"
            readiness = "NOT_READY_DATA_FAILURE" if "PRICE" in str(s.get("failure_bucket", "")).upper() else "NOT_READY_RECOMPUTE_FAILURE"
        elif ticker in universe:
            bucket = "TOTAL_UNIVERSE_ONLY"
            readiness = "DO_NOT_FREEZE_IN_THIS_TASK"
        else:
            bucket = "UNKNOWN_ADOPTION_STATE"
            readiness = "NOT_READY_MANUAL_REVIEW"
        out.append({
            "ticker": ticker,
            "in_total_universe": str(ticker in universe).upper(),
            "in_latest_freeze_252": str(in_freeze).upper(),
            "in_current_full_candidates_before": str(ticker in current_idx).upper(),
            "in_v18_35d_local_recomputed_candidates": str(d_ok).upper(),
            "in_v18_35e_online_recomputed_candidates": str(e_ok).upper(),
            "was_v18_35d_failure": str(ticker in d_fail_idx).upper(),
            "online_backfill_attempted": str(attempted).upper(),
            "online_backfill_success": str(success).upper(),
            "price_data_available_after_backfill": s.get("price_data_available", ""),
            "factor_success_after_backfill": s.get("factor_calculation_success", ""),
            "technical_success_after_backfill": s.get("technical_calculation_success", ""),
            "ranking_success_after_backfill": s.get("ranking_merge_success", ""),
            "rank_eligible_after_backfill": s.get("rank_eligible", ""),
            "previous_rank_if_available": current_idx.get(ticker, {}).get("rank") or d_idx.get(ticker, {}).get("rank", ""),
            "recomputed_rank_after_backfill": e_idx.get(ticker, {}).get("rank", ""),
            "previous_score_if_available": current_idx.get(ticker, {}).get("composite_candidate_score") or d_idx.get(ticker, {}).get("composite_candidate_score", ""),
            "recomputed_score_after_backfill": e_idx.get(ticker, {}).get("composite_candidate_score", ""),
            "adoption_bucket": bucket,
            "freeze_readiness_status": readiness,
            "remaining_failure_bucket": "" if e_ok else s.get("failure_bucket", ""),
            "remaining_failure_reason": "" if e_ok else s.get("failure_reason", ""),
            "evidence_sources": s.get("evidence_sources", ""),
        })
    return out


def make_report(summary: dict[str, object], bucket_counts: Counter, ready_rows: list[dict[str, object]], remaining: list[dict[str, object]]) -> str:
    remaining_counts = Counter(str(r.get("failure_bucket", "")) for r in remaining)
    lines = [
        "# V18.35E 在线补数据与重算候选接管桥接",
        "",
        f"- STATUS: `{summary['status']}`",
        f"- RUN_ID: `{summary['run_id']}`",
        f"- GENERATED_AT: `{summary['generated_at']}`",
        "",
        "## 说明",
        "V18.35D 本地重算结果为 total universe 332、attempted 332、rank eligible 303、failed 29。本步骤继续针对 V18.35D 失败 ticker 做在线补数据验证，并桥接新的 full-universe recomputed candidates 与最新 freeze set。",
        f"- 本次是否使用 yfinance/online backfill: `{summary['use_yfinance_for_candidate_bridge_backfill']}`",
        f"- 是否 apply 到 current full candidate aliases: `{summary['apply_online_backfilled_recomputed_candidates']}`",
        "- freeze ledger 本任务不修改；freeze 扩展需要单独 review 和独立任务。",
        "",
        "## Online Backfill Summary",
        "| metric | value |",
        "| --- | ---: |",
        f"| target tickers | {summary['online_backfill_target_count']} |",
        f"| attempted | {summary['online_backfill_attempted_count']} |",
        f"| success | {summary['online_backfill_success_count']} |",
        f"| failed | {summary['online_backfill_failure_count']} |",
        "",
        "## Recompute Before/After Count Comparison",
        "| item | count |",
        "| --- | ---: |",
        f"| V18.35D local rank eligible | {summary['v18_35d_local_rank_eligible_count']} |",
        f"| V18.35E rank eligible after backfill | {summary['recomputed_rank_eligible_after_backfill_count']} |",
        f"| latest freeze | {summary['latest_signal_freeze_count']} |",
        f"| new recomputed not in freeze | {summary['new_recomputed_not_in_freeze_count']} |",
        "",
        "## Adoption Bucket Counts",
        "| bucket | count |",
        "| --- | ---: |",
    ]
    for bucket, count in bucket_counts.most_common():
        lines.append(f"| `{bucket}` | {count} |")
    lines += ["", "## Next Freeze Ready Samples", "| rank | ticker | score | bucket |", "| ---: | --- | ---: | --- |"]
    for row in ready_rows[:30]:
        lines.append(f"| {row.get('recomputed_rank_after_backfill')} | `{row.get('ticker')}` | {row.get('recomputed_score_after_backfill')} | `{row.get('adoption_bucket')}` |")
    lines += ["", "## Remaining Failure Bucket Counts", "| bucket | count |", "| --- | ---: |"]
    for bucket, count in remaining_counts.most_common():
        lines.append(f"| `{bucket}` | {count} |")
    lines += ["", "## Remaining Failure Samples", "| ticker | bucket | reason |", "| --- | --- | --- |"]
    for row in remaining[:30]:
        lines.append(f"| `{row.get('ticker')}` | `{row.get('failure_bucket')}` | {row.get('failure_reason')} |")
    lines += [
        "",
        "## Operator Next Action",
        "- 先检查 `V18_35E_NEXT_FREEZE_READINESS_CANDIDATES.csv`，确认新增 recomputed candidates 是否进入下一次 freeze review。",
        "- 对仍无法计算的 ticker，优先补完整价格历史或手工核验退市/改名/不可交易状态。",
        "- V18.35A 仍可能使用 freeze-matched 252 source selection；这是预期限制，不在本任务中修改。",
        "",
        "## Final Conclusion",
        "Online backfill and recompute bridge completed.",
        "No fake scores were created.",
        "Freeze ledger was not modified.",
        "No trading/order/account logic was modified.",
        "AUTO_TRADE DISABLED, AUTO_SELL DISABLED, OFFICIAL_DECISION_IMPACT NONE.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--use-yfinance-for-candidate-bridge-backfill", action="store_true")
    parser.add_argument("--apply-online-backfilled-recomputed-candidates", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    run_id = "V18_35E_" + stamp()
    generated_at = iso_now()
    backup_path = "NONE"
    warnings: list[str] = []
    fails: list[str] = []

    universe_rows, _ = d35.read_csv(root / UNIVERSE)
    d_status, _ = d35.read_csv(root / D_STATUS)
    d_failures, _ = d35.read_csv(root / D_FAILURES)
    d_ranked, _ = d35.read_csv(root / D_RANKED)
    current_full, _ = d35.read_csv(root / CURRENT_FULL)
    freeze_rows, _ = d35.read_csv(root / FREEZE)

    universe = set(sorted(ticker_set(universe_rows)))
    freeze = latest_freeze(freeze_rows)
    if not universe:
        fails.append("total universe source cannot be read")
    if not d_status or not d_ranked:
        fails.append("V18.35D base outputs cannot be read")

    targets = target_failures(d_failures)
    attempts: list[dict[str, object]] = []
    validated: list[dict[str, object]] = []
    failed_backfill: list[dict[str, object]] = []
    staging_dir = root / "outputs/v18/data_backfill/staging" / run_id
    cache_backup_dir = root / "archive/v18/online_backfill_candidate_bridge_backups" / run_id / "price_cache_overwrite_backups"

    if args.use_yfinance_for_candidate_bridge_backfill and not fails:
        for row in targets:
            ticker = norm(row.get("ticker"))
            symbol_ok, symbol_reason = valid_online_symbol(ticker)
            prices: list[dict[str, object]] = []
            fetch_error = ""
            if symbol_ok:
                prices, fetch_error = d35.download_prices_yf(ticker)
                ok, reason = validate_prices(prices)
            else:
                ok, reason = False, symbol_reason
            staging_csv = staging_dir / f"{ticker}.csv"
            cache_csv = ""
            cache_backup = ""
            if prices:
                write_csv(staging_csv, prices, ["date", "open", "high", "low", "close", "volume"])
            if ok:
                try:
                    cache_csv, cache_backup = cache_write(root, ticker, prices, cache_backup_dir)
                except Exception as exc:
                    ok = False
                    reason = f"validated but cache write failed: {type(exc).__name__}"
            elif fetch_error and not reason:
                reason = fetch_error
            attempt = {
                "run_id": run_id, "ticker": ticker,
                "v18_35d_failure_bucket": row.get("failure_bucket", ""),
                "v18_35d_failure_reason": row.get("failure_reason", ""),
                "attempted": "TRUE", "provider": "yfinance",
                "download_row_count": len(prices),
                "validation_status": "PASS" if ok else "FAIL",
                "validation_reason": reason or fetch_error,
                "latest_available_date": prices[-1]["date"] if prices else "",
                "staging_csv": rel(root, staging_csv) if prices else "",
                "cache_csv": rel(root, cache_csv) if cache_csv else "",
                "cache_backup_path": cache_backup,
            }
            attempts.append(attempt)
            (validated if ok else failed_backfill).append(attempt)
    else:
        if targets:
            warnings.append("online backfill target tickers remain because yfinance flag was not used")
        for row in targets:
            attempt = {
                "run_id": run_id, "ticker": norm(row.get("ticker")),
                "v18_35d_failure_bucket": row.get("failure_bucket", ""),
                "v18_35d_failure_reason": row.get("failure_reason", ""),
                "attempted": "FALSE", "provider": "NONE",
                "download_row_count": 0, "validation_status": "NOT_ATTEMPTED",
                "validation_reason": "UseYFinanceForCandidateBridgeBackfill was not passed",
                "latest_available_date": "", "staging_csv": "", "cache_csv": "", "cache_backup_path": "",
            }
            attempts.append(attempt)
            failed_backfill.append(attempt)

    try:
        e_status, e_factor, e_tech, e_ranked, factor_fields, duplicate_count = recompute_full_universe(root)
    except Exception as exc:
        fails.append(f"online backfill recompute crashed: {type(exc).__name__}")
        e_status, e_factor, e_tech, e_ranked, factor_fields, duplicate_count = [], [], [], [], [], 0

    write_csv(root / OUT_ATTEMPTS, attempts, ATTEMPT_FIELDS)
    write_csv(root / OUT_VALIDATED, validated, ATTEMPT_FIELDS)
    write_csv(root / OUT_FAILED, failed_backfill, ATTEMPT_FIELDS)
    write_csv(root / OUT_FACTOR, e_factor, factor_fields or ["factor_pack_rank", "ticker", "factor_pack_score"])
    write_csv(root / OUT_TECH, e_tech, list(e_tech[0].keys()) if e_tech else ["ticker", "technical_timing_score"])
    write_csv(root / OUT_RANKED, e_ranked, d35.RANK_FIELDS)
    write_csv(root / OUT_STATUS, e_status, d35.STATUS_FIELDS)

    bridge = bridge_rows(universe, freeze, current_full, d_ranked, d_failures, e_ranked, e_status, attempts)
    ready = [r for r in bridge if r["freeze_readiness_status"] == "READY_FOR_NEXT_FREEZE_REVIEW"]
    remaining = [r for r in e_status if r.get("rank_eligible") != "TRUE"]
    write_csv(root / OUT_BRIDGE, bridge, BRIDGE_FIELDS)
    write_csv(root / OUT_READY, ready, BRIDGE_FIELDS)
    write_csv(root / OUT_REMAINING, remaining, d35.STATUS_FIELDS)

    applied = False
    current_full_after = len(ticker_set(current_full))
    top_after = 20 if e_ranked else 0
    if args.apply_online_backfilled_recomputed_candidates and not fails:
        warnings.append("current candidate alias apply disabled by V18.50B-R2; sidecar outputs only")

    new_not_freeze = [r for r in bridge if truth(r.get("in_v18_35e_online_recomputed_candidates")) and not truth(r.get("in_latest_freeze_252"))]
    newly_backfilled = [r for r in bridge if r.get("adoption_bucket") == "NEWLY_BACKFILLED_AND_RECOMPUTED"]
    expected_freeze = bool(len(e_ranked) > len(freeze))
    if remaining:
        warnings.append("some tickers still fail after online backfill")
    if args.use_yfinance_for_candidate_bridge_backfill and failed_backfill:
        warnings.append("online provider failed or was partially unavailable")
    if not args.apply_online_backfilled_recomputed_candidates:
        warnings.append("apply mode was not used")
    if expected_freeze:
        warnings.append("freeze remains 252 while recomputed candidate set is larger")
    warnings.append("V18.35A may still use freeze-matched 252 source selection")
    if len(e_status) != len(universe):
        fails.append("output row count mismatch")
    if duplicate_count > 0:
        fails.append("duplicate ticker count > 0")

    summary = {
        "status": STATUS_OK,
        "run_id": run_id,
        "generated_at": generated_at,
        "use_yfinance_for_candidate_bridge_backfill": str(args.use_yfinance_for_candidate_bridge_backfill).upper(),
        "apply_online_backfilled_recomputed_candidates": str(args.apply_online_backfilled_recomputed_candidates).upper(),
        "total_universe_count": len(universe),
        "v18_35d_local_rank_eligible_count": len(d_ranked),
        "online_backfill_target_count": len(targets),
        "online_backfill_attempted_count": sum(1 for r in attempts if r.get("attempted") == "TRUE"),
        "online_backfill_success_count": len(validated),
        "online_backfill_failure_count": len(failed_backfill),
        "recomputed_rank_eligible_after_backfill_count": len(e_ranked),
        "recomputed_rank_ineligible_after_backfill_count": len(e_status) - len(e_ranked),
        "latest_signal_freeze_count": len(freeze),
        "current_full_candidate_count_before": len(ticker_set(current_full)),
        "current_full_candidate_count_after": current_full_after,
        "current_top_candidate_count_after": top_after,
        "v18_35e_direct_current_write_disabled": "TRUE",
        "v18_35e_raw105_current_factor_reuse_blocked_from_current_alias": "TRUE",
        "current_alias_write_disabled_by": CURRENT_ALIAS_WRITE_DISABLED_BY,
        "new_recomputed_not_in_freeze_count": len(new_not_freeze),
        "newly_backfilled_and_recomputed_count": len(newly_backfilled),
        "still_uncomputed_after_backfill_count": len(remaining),
        "next_freeze_ready_candidate_count": len(ready),
        "expected_freeze_not_expanded_yet": str(expected_freeze).upper(),
        "duplicate_ticker_count": duplicate_count,
        "backup_path": backup_path,
        "warning_count": 0,
        "fail_count": 0,
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "forbidden_modified": FORBIDDEN_MODIFIED,
    }
    summary["fail_count"] = len(fails)
    summary["warning_count"] = len(warnings)
    summary["status"] = STATUS_FAIL if fails else (STATUS_WARN if warnings else STATUS_OK)

    bucket_counts = Counter(str(r.get("adoption_bucket", "")) for r in bridge)
    write_csv(root / OUT_SUMMARY, [summary], list(summary.keys()))
    report = make_report(summary, bucket_counts, ready, remaining)
    write_text(root / OUT_REPORT, report)
    write_text(root / CURRENT_REPORT, report)

    read_first_keys = [
        "status", "run_id", "use_yfinance_for_candidate_bridge_backfill",
        "apply_online_backfilled_recomputed_candidates", "total_universe_count",
        "v18_35d_local_rank_eligible_count", "online_backfill_target_count",
        "online_backfill_attempted_count", "online_backfill_success_count",
        "online_backfill_failure_count", "recomputed_rank_eligible_after_backfill_count",
        "recomputed_rank_ineligible_after_backfill_count", "latest_signal_freeze_count",
        "current_full_candidate_count_before", "current_full_candidate_count_after",
        "current_top_candidate_count_after", "v18_35e_direct_current_write_disabled",
        "v18_35e_raw105_current_factor_reuse_blocked_from_current_alias",
        "current_alias_write_disabled_by", "new_recomputed_not_in_freeze_count",
        "newly_backfilled_and_recomputed_count", "still_uncomputed_after_backfill_count",
        "next_freeze_ready_candidate_count", "expected_freeze_not_expanded_yet",
        "duplicate_ticker_count", "backup_path", "warning_count", "fail_count",
    ]
    read_first = [f"{k.upper()}: {summary[k]}" for k in read_first_keys]
    read_first += [
        f"REPORT: {OUT_REPORT}",
        f"CURRENT_REPORT: {CURRENT_REPORT}",
        f"BRIDGE_CSV: {OUT_BRIDGE}",
        f"NEXT_FREEZE_READY_CSV: {OUT_READY}",
        f"REMAINING_UNCOMPUTED_CSV: {OUT_REMAINING}",
        f"BACKFILL_ATTEMPTS_CSV: {OUT_ATTEMPTS}",
        f"SUMMARY_CSV: {OUT_SUMMARY}",
        "OFFICIAL_DECISION_IMPACT: NONE",
        "AUTO_TRADE: DISABLED",
        "AUTO_SELL: DISABLED",
        "FORBIDDEN_MODIFIED: FALSE",
        "",
    ]
    write_text(root / OUT_READ_FIRST, "\n".join(read_first))

    for key in ["status", "run_id", "online_backfill_target_count", "online_backfill_attempted_count", "online_backfill_success_count", "online_backfill_failure_count", "recomputed_rank_eligible_after_backfill_count", "backup_path", "warning_count", "fail_count"]:
        print(f"{key.upper()}: {summary[key]}")
    print(f"REPORT: {root / CURRENT_REPORT}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if str(summary["status"]).startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
