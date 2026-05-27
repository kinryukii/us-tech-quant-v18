from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_29C_DAILY_RECOMMENDATION_TIER_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_29C_DAILY_RECOMMENDATION_TIER_SNAPSHOT_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_29C_DAILY_RECOMMENDATION_TIER_SNAPSHOT_ERROR"
MODE = "DAILY_RECOMMENDATION_TIER_SNAPSHOT_LEDGER"

CURRENT_RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
READ_FIRST_R28B = "outputs/v18/ops/V18_28B_READ_FIRST.txt"
READ_FIRST_R28D = "outputs/v18/ops/V18_28D_READ_FIRST.txt"
SIGNAL_FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"

LEDGER_PATH = "state/v18/recommendation_snapshots/V18_DAILY_RECOMMENDATION_TIER_LEDGER.csv"
OUT_RESULT = "outputs/v18/recommendations/V18_29C_DAILY_RECOMMENDATION_TIER_SNAPSHOT_RESULT.csv"
OUT_REPORT = "outputs/v18/read_center/V18_29C_DAILY_RECOMMENDATION_TIER_SNAPSHOT_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_29C_READ_FIRST.txt"

PROTECTED_FILES = [
    CURRENT_RECOMMENDATIONS,
    "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
    "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv",
    "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
    SIGNAL_FREEZE_LEDGER,
    "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv",
]
PROTECTED_DIRS = [
    "state/v18/price_cache",
    "state/v18/trading",
    "outputs/v18/official_daily",
    "outputs/v18/factor_pack",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "SNAPSHOT_DATE",
    "SOURCE_RECOMMENDATION_ROW_COUNT",
    "LEDGER_PATH",
    "LEDGER_EXISTS_BEFORE",
    "PRE_LEDGER_ROWS",
    "APPENDED_ROWS",
    "POST_LEDGER_ROWS",
    "DUPLICATE_SNAPSHOT_ROWS_SKIPPED",
    "DUPLICATE_TICKER_COUNT_SOURCE",
    "MISSING_RECOMMENDATION_TIER_COUNT",
    "MISSING_RECOMMENDATION_ACTION_COUNT",
    "UNKNOWN_PRIMARY_THEME_COUNT",
    "SOURCE_R28B_STATUS",
    "SOURCE_R28D_STATUS",
    "LATEST_SIGNAL_FREEZE_RUN_ID",
    "LATEST_SIGNAL_FREEZE_DATE",
    "RECOMMENDATION_TIER_SNAPSHOT_COUNT_BY_DATE",
    "FULL_RECOMMENDATION_TIER_BACKTEST_READY_NOW",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "FORBIDDEN_MODIFIED",
]

REPORT_FIELDS = [
    "snapshot_run_id",
    "snapshot_date",
    "ticker",
    "rank",
    "company_name",
    "composite_candidate_score",
    "primary_theme",
    "secondary_theme",
    "industry_group",
    "role_bucket",
    "cyclicality_bucket",
    "volatility_bucket",
    "liquidity_bucket",
    "theme_rank",
    "theme_percentile",
    "technical_timing_score",
    "overheat_penalty",
    "bb_status",
    "rsi_status",
    "kdj_status",
    "technical_signal",
    "technical_warning_label",
    "recommendation_tier",
    "recommendation_action",
    "position_role",
    "risk_label",
    "reason_codes",
    "operator_notes",
    "source_recommendation_run_id",
    "source_r28b_status",
    "source_r28d_status",
    "latest_signal_freeze_run_id",
    "latest_signal_freeze_date",
    "append_timestamp",
    "snapshot_action",
]

LEDGER_FIELDS = [
    "snapshot_run_id",
    "snapshot_date",
    "ticker",
    "rank",
    "company_name",
    "composite_candidate_score",
    "primary_theme",
    "secondary_theme",
    "industry_group",
    "role_bucket",
    "cyclicality_bucket",
    "volatility_bucket",
    "liquidity_bucket",
    "theme_rank",
    "theme_percentile",
    "technical_timing_score",
    "overheat_penalty",
    "bb_status",
    "rsi_status",
    "kdj_status",
    "technical_signal",
    "technical_warning_label",
    "recommendation_tier",
    "recommendation_action",
    "position_role",
    "risk_label",
    "reason_codes",
    "operator_notes",
    "source_recommendation_run_id",
    "source_r28b_status",
    "source_r28d_status",
    "latest_signal_freeze_run_id",
    "latest_signal_freeze_date",
    "append_timestamp",
]


def norm(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def norm_ticker(value: object) -> str:
    return norm(value).upper()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def to_int(value: object) -> Optional[int]:
    try:
        text = norm(value)
        if not text:
            return None
        return int(float(text))
    except Exception:
        return None


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_dt(value: object) -> dt.datetime:
    text = norm(value)
    if not text:
        return dt.datetime.min
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return dt.datetime.min


def parse_date(value: object) -> Optional[dt.date]:
    text = norm(value)
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%m-%d-%Y", "%Y%m%d"):
        try:
            return dt.datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def file_sig(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return "MISSING"
    stat = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"{stat.st_size}:{stat.st_mtime_ns}:{digest.hexdigest()}"


def dir_sig(path: Path) -> str:
    if not path.exists() or not path.is_dir():
        return "MISSING"
    parts: List[str] = []
    for child in sorted(path.rglob("*")):
        if child.is_file():
            stat = child.stat()
            parts.append(f"{child.relative_to(path).as_posix()}:{stat.st_size}:{stat.st_mtime_ns}")
    return "|".join(parts)


def protected_sig(root: Path) -> Dict[str, str]:
    sig: Dict[str, str] = {}
    for rel in PROTECTED_FILES:
        sig[f"file:{rel}"] = file_sig(root / rel)
    for rel in PROTECTED_DIRS:
        sig[f"dir:{rel}"] = dir_sig(root / rel)
    return sig


def read_status_field(path: Path, field: str) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return ""


def latest_freeze_group(rows: Sequence[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[norm(row.get("run_id"))].append(row)
    if not grouped:
        return "", []

    def key(item: Tuple[str, List[Dict[str, str]]]) -> Tuple[dt.datetime, dt.date, str]:
        run_id, run_rows = item
        latest_ts = max((parse_dt(row.get("run_timestamp")) for row in run_rows), default=dt.datetime.min)
        latest_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in run_rows), default=dt.date.min)
        return latest_ts, latest_date, run_id

    run_id, run_rows = max(grouped.items(), key=key)
    return run_id, run_rows


def markdown_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: Optional[int] = None) -> str:
    selected = list(rows[:limit] if limit is not None else rows)
    if not selected:
        return "_None._\n"
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in selected:
        lines.append("| " + " | ".join(norm(row.get(field)).replace("|", "/") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def build_report(values: Dict[str, object], snapshot_rows: Sequence[Dict[str, object]], ledger_before: int, ledger_after: int) -> str:
    tier_counts = Counter(norm(row.get("recommendation_tier")) for row in snapshot_rows)
    theme_counts = Counter(norm(row.get("primary_theme")) for row in snapshot_rows)
    report = [
        "# V18.29C Daily Recommendation Tier Snapshot Ledger",
        "",
        "## Read First",
        "```text",
        "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS),
        "```",
        "",
        "## Snapshot Append Summary",
        f"- Snapshot run id: `{values.get('RUN_ID')}`",
        f"- Snapshot date: `{values.get('SNAPSHOT_DATE')}`",
        f"- Rows appended this run: `{values.get('APPENDED_ROWS')}`",
        f"- Duplicate rows skipped: `{values.get('DUPLICATE_SNAPSHOT_ROWS_SKIPPED')}`",
        f"- Ledger rows before: `{ledger_before}`",
        f"- Ledger rows after: `{ledger_after}`",
        "",
        "## Recommendation Tier Counts For This Snapshot",
        markdown_table(
            [{"recommendation_tier": k, "count": v} for k, v in tier_counts.most_common()],
            ["recommendation_tier", "count"],
        ),
        "## Theme Counts For This Snapshot",
        markdown_table(
            [{"primary_theme": k, "count": v} for k, v in theme_counts.most_common()],
            ["primary_theme", "count"],
        ),
        "## Top 30 Snapshot Rows",
        markdown_table(sorted(snapshot_rows, key=lambda row: to_int(row.get("rank")) or 999999), REPORT_FIELDS, limit=30),
        "## Ledger Growth Summary",
        f"- Pre-ledger rows: `{ledger_before}`",
        f"- Post-ledger rows: `{ledger_after}`",
        f"- Growth this run: `{ledger_after - ledger_before}`",
        f"- Snapshot count by date: `{values.get('RECOMMENDATION_TIER_SNAPSHOT_COUNT_BY_DATE')}`",
        "",
        "## Next-Step Recommendation",
        "- Continue appending one dated snapshot per day before the next limited historical backtest run.",
        "- Once multiple dated snapshots exist, the recommendation-tier backtest can use dated tier snapshots instead of the current-only tier file.",
        "- Keep the current recommendation file unchanged; the ledger is the historical source of record.",
    ]
    return "\n".join(report) + "\n"


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def run(root: Path) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("V18_29C_%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)

    recs = read_csv(root / CURRENT_RECOMMENDATIONS)
    if not recs:
        raise RuntimeError("Current recommendation file is empty")

    duplicate_tickers = sum(1 for count in Counter(norm_ticker(row.get("ticker")) for row in recs if norm_ticker(row.get("ticker"))).values() if count > 1)
    missing_tier = sum(1 for row in recs if not norm(row.get("recommendation_tier")))
    missing_action = sum(1 for row in recs if not norm(row.get("recommendation_action")))
    unknown_theme = sum(1 for row in recs if norm(row.get("primary_theme")).upper() in {"", "UNKNOWN"})
    valid_source = len(recs) == 252 and duplicate_tickers == 0 and missing_tier == 0 and missing_action == 0 and unknown_theme == 0
    if not valid_source:
        raise RuntimeError("Invalid current recommendation source file")

    ledger_path = root / LEDGER_PATH
    ledger_exists_before = ledger_path.exists()
    pre_ledger_rows = len(read_csv(ledger_path)) if ledger_exists_before else 0
    existing_rows = read_csv(ledger_path) if ledger_exists_before else []
    existing_keys = {
        (
            norm(row.get("snapshot_date")),
            norm_ticker(row.get("ticker")),
            norm(row.get("source_recommendation_run_id")),
        )
        for row in existing_rows
    }

    r28b_status = read_status_field(root / READ_FIRST_R28B, "STATUS")
    r28b_run_id = read_status_field(root / READ_FIRST_R28B, "RUN_ID")
    r28d_status = read_status_field(root / READ_FIRST_R28D, "STATUS")
    latest_run_id, latest_run_rows = latest_freeze_group(read_csv(root / SIGNAL_FREEZE_LEDGER))
    latest_signal_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in latest_run_rows), default=dt.date.min)
    latest_signal_date_text = latest_signal_date.isoformat() if latest_signal_date != dt.date.min else ""
    latest_freeze_tickers = {norm_ticker(row.get("ticker")) for row in latest_run_rows if norm_ticker(row.get("ticker"))}
    current_tickers = {norm_ticker(row.get("ticker")) for row in recs if norm_ticker(row.get("ticker"))}
    freeze_matches_current = latest_freeze_tickers == current_tickers and len(latest_freeze_tickers) == len(current_tickers)
    snapshot_date = latest_signal_date if freeze_matches_current and latest_signal_date_text else dt.date.today()
    snapshot_date_text = snapshot_date.isoformat()

    source_rows: List[Dict[str, object]] = []
    appended_rows: List[Dict[str, object]] = []
    skipped_count = 0
    append_timestamp = dt.datetime.now().isoformat(timespec="seconds")
    for row in recs:
        ticker = norm_ticker(row.get("ticker"))
        key = (snapshot_date_text, ticker, r28b_run_id)
        action = "APPEND"
        if key in existing_keys:
            action = "SKIP_DUPLICATE"
            skipped_count += 1
        else:
            source_rows.append(
                {
                    "snapshot_run_id": run_id,
                    "snapshot_date": snapshot_date_text,
                    "ticker": ticker,
                    "rank": norm(row.get("rank")),
                    "company_name": norm(row.get("company_name")),
                    "composite_candidate_score": norm(row.get("composite_candidate_score")),
                    "primary_theme": norm(row.get("primary_theme")),
                    "secondary_theme": norm(row.get("secondary_theme")),
                    "industry_group": norm(row.get("industry_group")),
                    "role_bucket": norm(row.get("role_bucket")),
                    "cyclicality_bucket": norm(row.get("cyclicality_bucket")),
                    "volatility_bucket": norm(row.get("volatility_bucket")),
                    "liquidity_bucket": norm(row.get("liquidity_bucket")),
                    "theme_rank": norm(row.get("theme_rank")),
                    "theme_percentile": norm(row.get("theme_percentile")),
                    "technical_timing_score": norm(row.get("technical_timing_score")),
                    "overheat_penalty": norm(row.get("overheat_penalty")),
                    "bb_status": norm(row.get("bb_status")),
                    "rsi_status": norm(row.get("rsi_status")),
                    "kdj_status": norm(row.get("kdj_status")),
                    "technical_signal": norm(row.get("technical_signal")),
                    "technical_warning_label": norm(row.get("technical_warning_label")),
                    "recommendation_tier": norm(row.get("recommendation_tier")),
                    "recommendation_action": norm(row.get("recommendation_action")),
                    "position_role": norm(row.get("position_role")),
                    "risk_label": norm(row.get("risk_label")),
                    "reason_codes": norm(row.get("reason_codes")),
                    "operator_notes": norm(row.get("operator_notes")),
                    "source_recommendation_run_id": r28b_run_id,
                    "source_r28b_status": r28b_status,
                    "source_r28d_status": r28d_status,
                    "latest_signal_freeze_run_id": latest_run_id,
                    "latest_signal_freeze_date": latest_signal_date_text,
                    "append_timestamp": append_timestamp,
                    "snapshot_action": action,
                }
            )
        appended_rows.append(
            {
                "snapshot_run_id": run_id,
                "snapshot_date": snapshot_date_text,
                "ticker": ticker,
                "rank": norm(row.get("rank")),
                "company_name": norm(row.get("company_name")),
                "composite_candidate_score": norm(row.get("composite_candidate_score")),
                "primary_theme": norm(row.get("primary_theme")),
                "secondary_theme": norm(row.get("secondary_theme")),
                "industry_group": norm(row.get("industry_group")),
                "role_bucket": norm(row.get("role_bucket")),
                "cyclicality_bucket": norm(row.get("cyclicality_bucket")),
                "volatility_bucket": norm(row.get("volatility_bucket")),
                "liquidity_bucket": norm(row.get("liquidity_bucket")),
                "theme_rank": norm(row.get("theme_rank")),
                "theme_percentile": norm(row.get("theme_percentile")),
                "technical_timing_score": norm(row.get("technical_timing_score")),
                "overheat_penalty": norm(row.get("overheat_penalty")),
                "bb_status": norm(row.get("bb_status")),
                "rsi_status": norm(row.get("rsi_status")),
                "kdj_status": norm(row.get("kdj_status")),
                "technical_signal": norm(row.get("technical_signal")),
                "technical_warning_label": norm(row.get("technical_warning_label")),
                "recommendation_tier": norm(row.get("recommendation_tier")),
                "recommendation_action": norm(row.get("recommendation_action")),
                "position_role": norm(row.get("position_role")),
                "risk_label": norm(row.get("risk_label")),
                "reason_codes": norm(row.get("reason_codes")),
                "operator_notes": norm(row.get("operator_notes")),
                "source_recommendation_run_id": r28b_run_id,
                "source_r28b_status": r28b_status,
                "source_r28d_status": r28d_status,
                "latest_signal_freeze_run_id": latest_run_id,
                "latest_signal_freeze_date": latest_signal_date_text,
                "append_timestamp": append_timestamp,
                "snapshot_action": action,
            }
        )

    if not ledger_exists_before:
        write_csv(ledger_path, source_rows, LEDGER_FIELDS)
    elif source_rows:
        write_csv(ledger_path, existing_rows + source_rows, LEDGER_FIELDS)

    post_ledger_rows = len(existing_rows) + len(source_rows)
    snapshot_count_by_date = sum(1 for row in (existing_rows + source_rows) if norm(row.get("snapshot_date")) == snapshot_date_text)
    full_backtest_ready_now = "FALSE"
    status = STATUS_OK if (valid_source and (source_rows or skipped_count == len(recs))) else STATUS_WARN
    if not freeze_matches_current:
        status = STATUS_WARN

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "SNAPSHOT_DATE": snapshot_date_text,
        "SOURCE_RECOMMENDATION_ROW_COUNT": len(recs),
        "LEDGER_PATH": str(ledger_path),
        "LEDGER_EXISTS_BEFORE": bool_text(ledger_exists_before),
        "PRE_LEDGER_ROWS": pre_ledger_rows,
        "APPENDED_ROWS": len(source_rows),
        "POST_LEDGER_ROWS": post_ledger_rows,
        "DUPLICATE_SNAPSHOT_ROWS_SKIPPED": skipped_count,
        "DUPLICATE_TICKER_COUNT_SOURCE": duplicate_tickers,
        "MISSING_RECOMMENDATION_TIER_COUNT": missing_tier,
        "MISSING_RECOMMENDATION_ACTION_COUNT": missing_action,
        "UNKNOWN_PRIMARY_THEME_COUNT": unknown_theme,
        "SOURCE_R28B_STATUS": r28b_status,
        "SOURCE_R28D_STATUS": r28d_status,
        "LATEST_SIGNAL_FREEZE_RUN_ID": latest_run_id,
        "LATEST_SIGNAL_FREEZE_DATE": latest_signal_date_text,
        "RECOMMENDATION_TIER_SNAPSHOT_COUNT_BY_DATE": f"{snapshot_date_text}={snapshot_count_by_date}",
        "FULL_RECOMMENDATION_TIER_BACKTEST_READY_NOW": full_backtest_ready_now,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": bool_text(protected_sig(root) != protected_before),
    }

    write_csv(root / OUT_RESULT, appended_rows, REPORT_FIELDS)
    write_text(root / OUT_REPORT, build_report(values, appended_rows, pre_ledger_rows, post_ledger_rows))
    write_read_first(root / OUT_READ_FIRST, values)

    if protected_sig(root) != protected_before:
        raise RuntimeError("Protected state modified during snapshot ledger update")
    return values


def write_failure(root: Path, error: BaseException) -> None:
    values: Dict[str, object] = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("V18_29C_%Y%m%d_%H%M%S"),
        "SNAPSHOT_DATE": "",
        "SOURCE_RECOMMENDATION_ROW_COUNT": 0,
        "LEDGER_PATH": str(root / LEDGER_PATH),
        "LEDGER_EXISTS_BEFORE": "UNKNOWN",
        "PRE_LEDGER_ROWS": 0,
        "APPENDED_ROWS": 0,
        "POST_LEDGER_ROWS": 0,
        "DUPLICATE_SNAPSHOT_ROWS_SKIPPED": 0,
        "DUPLICATE_TICKER_COUNT_SOURCE": 0,
        "MISSING_RECOMMENDATION_TIER_COUNT": 0,
        "MISSING_RECOMMENDATION_ACTION_COUNT": 0,
        "UNKNOWN_PRIMARY_THEME_COUNT": 0,
        "SOURCE_R28B_STATUS": "",
        "SOURCE_R28D_STATUS": "",
        "LATEST_SIGNAL_FREEZE_RUN_ID": "",
        "LATEST_SIGNAL_FREEZE_DATE": "",
        "RECOMMENDATION_TIER_SNAPSHOT_COUNT_BY_DATE": "",
        "FULL_RECOMMENDATION_TIER_BACKTEST_READY_NOW": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "UNKNOWN",
    }
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, f"# V18.29C Daily Recommendation Tier Snapshot Ledger Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.29C daily recommendation tier snapshot ledger.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        values = run(root)
        print(f"STATUS: {values['STATUS']}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return 0
    except Exception as exc:
        write_failure(root, exc)
        print(f"STATUS: {STATUS_FAIL}")
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
