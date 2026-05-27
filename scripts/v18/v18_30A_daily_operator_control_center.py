from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_30A_DAILY_OPERATOR_CONTROL_CENTER_READY"
STATUS_WARN = "WARN_V18_30A_DAILY_OPERATOR_CONTROL_CENTER_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_30A_DAILY_OPERATOR_CONTROL_CENTER_ERROR"
MODE = "READ_ONLY_DAILY_OPERATOR_CONTROL_CENTER"

READ_FIRST_PATHS = [
    "outputs/v18/ops/V18_28A_READ_FIRST.txt",
    "outputs/v18/ops/V18_28B_READ_FIRST.txt",
    "outputs/v18/ops/V18_28C_READ_FIRST.txt",
    "outputs/v18/ops/V18_28D_READ_FIRST.txt",
    "outputs/v18/ops/V18_29A_READ_FIRST.txt",
    "outputs/v18/ops/V18_29B_READ_FIRST.txt",
    "outputs/v18/ops/V18_29C_READ_FIRST.txt",
]

CURRENT_RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"
CURRENT_TIER_REPORT = "outputs/v18/read_center/V18_CURRENT_RECOMMENDATION_TIERS.md"
RECOMMENDATION_SNAPSHOT_LEDGER = "state/v18/recommendation_snapshots/V18_DAILY_RECOMMENDATION_TIER_LEDGER.csv"
SIGNAL_FREEZE_LEDGER = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
CURRENT_THEMES = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"

OUT_REPORT = "outputs/v18/read_center/V18_CURRENT_OPERATOR_CONTROL_CENTER.md"
OUT_ERROR_REPORT = "outputs/v18/read_center/V18_30A_OPERATOR_CONTROL_CENTER_ERROR.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_30A_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_30A_OPERATOR_STATUS_SUMMARY.csv"

PROTECTED_FILES = [
    CURRENT_RECOMMENDATIONS,
    CURRENT_CANDIDATES,
    CURRENT_THEMES,
    RECOMMENDATION_SNAPSHOT_LEDGER,
    SIGNAL_FREEZE_LEDGER,
    "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
    "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv",
]
PROTECTED_DIRS = [
    "state/v18/price_cache",
    "state/v18/trading",
    "outputs/v18/official_daily",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "CURRENT_RECOMMENDATION_ROW_COUNT",
    "CURRENT_RANKED_CANDIDATE_ROW_COUNT",
    "THEME_CLASSIFICATION_ROW_COUNT",
    "UNKNOWN_PRIMARY_THEME_COUNT",
    "LATEST_SIGNAL_FREEZE_RUN_ID",
    "LATEST_SIGNAL_FREEZE_DATE",
    "LATEST_SIGNAL_FREEZE_TICKER_COUNT",
    "LATEST_FULL_SIGNAL_FREEZE_RUN_ID",
    "LATEST_FULL_SIGNAL_FREEZE_DATE",
    "LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT",
    "PREVIOUS_FULL_SIGNAL_FREEZE_RUN_ID",
    "SAME_DAY_FULL_FREEZE_RUN_COUNT",
    "SAME_DAY_MULTIPLE_FREEZE_WARNING",
    "LATEST_RECOMMENDATION_SNAPSHOT_DATE",
    "LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT",
    "SNAPSHOT_MATCHES_LATEST_FREEZE_DATE",
    "FORWARD_1D_FILLABLE_COUNT",
    "FORWARD_3D_FILLABLE_COUNT",
    "FORWARD_5D_FILLABLE_COUNT",
    "FORWARD_10D_FILLABLE_COUNT",
    "FORWARD_20D_FILLABLE_COUNT",
    "FULL_RECOMMENDATION_TIER_BACKTEST_READY_NOW",
    "CURRENT_OPERATOR_ACTION",
    "MANUAL_REVIEW_READY",
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "FORBIDDEN_MODIFIED",
]

SUMMARY_FIELDS = [
    "category",
    "check_name",
    "status",
    "value",
    "detail",
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


def parse_dt(value: object) -> dt.datetime:
    text = norm(value)
    if not text:
        return dt.datetime.min
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        parsed = parse_date(text)
        if parsed:
            return dt.datetime.combine(parsed, dt.time.min)
    return dt.datetime.min


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


def read_status_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def latest_snapshot_info(root: Path) -> Tuple[str, str, int]:
    path = root / RECOMMENDATION_SNAPSHOT_LEDGER
    if not path.exists():
        return "", "", 0
    rows = read_csv(path)
    if not rows:
        return "", "", 0
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[norm(row.get("snapshot_date"))].append(row)
    if not grouped:
        return "", "", 0
    latest_date = max(grouped.keys())
    latest_rows = grouped[latest_date]
    return latest_date, latest_date, len(latest_rows)


def latest_freeze_info(root: Path) -> Tuple[str, str, int]:
    path = root / SIGNAL_FREEZE_LEDGER
    if not path.exists():
        return "", "", 0
    rows = read_csv(path)
    if not rows:
        return "", "", 0
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[norm(row.get("run_id"))].append(row)
    if not grouped:
        return "", "", 0
    def key(item: Tuple[str, List[Dict[str, str]]]) -> Tuple[dt.datetime, dt.date, str]:
        run_id, run_rows = item
        latest_ts = max((parse_dt(row.get("run_timestamp")) for row in run_rows), default=dt.datetime.min)
        latest_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in run_rows), default=dt.date.min)
        return latest_ts, latest_date, run_id
    run_id, run_rows = max(grouped.items(), key=key)
    signal_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in run_rows), default=dt.date.min)
    return run_id, signal_date.isoformat() if signal_date != dt.date.min else "", len({norm_ticker(row.get("ticker")) for row in run_rows if norm_ticker(row.get("ticker"))})


def latest_full_freeze_info(root: Path) -> Tuple[str, str, int, str, int, bool]:
    path = root / SIGNAL_FREEZE_LEDGER
    if not path.exists():
        return "", "", 0, "", 0, False
    rows = read_csv(path)
    if not rows:
        return "", "", 0, "", 0, False
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[norm(row.get("run_id"))].append(row)
    full_runs: List[Tuple[str, str, int, dt.datetime, dt.date]] = []
    for run_id, run_rows in grouped.items():
        tickers = {norm_ticker(row.get("ticker")) for row in run_rows if norm_ticker(row.get("ticker"))}
        if len(tickers) == 252:
            latest_ts = max((parse_dt(row.get("run_timestamp")) for row in run_rows), default=dt.datetime.min)
            latest_date = max((parse_date(row.get("signal_date")) or dt.date.min for row in run_rows), default=dt.date.min)
            full_runs.append((run_id, latest_date.isoformat() if latest_date != dt.date.min else "", len(tickers), latest_ts, latest_date))
    if not full_runs:
        return "", "", 0, "", 0, False
    full_runs.sort(key=lambda item: (item[3], item[4], item[0]))
    latest_run_id, latest_date, latest_count, _, _ = full_runs[-1]
    previous_run_id = full_runs[-2][0] if len(full_runs) > 1 else ""
    same_day_count = sum(1 for item in full_runs if item[1] == latest_date)
    same_day_warning = same_day_count > 1
    return latest_run_id, latest_date, latest_count, previous_run_id, same_day_count, same_day_warning


def parse_read_first_values(root: Path) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for rel in READ_FIRST_PATHS:
        path = root / rel
        out[path.name] = read_status_file(path)
    return out


def tier_counts(rows: Sequence[Dict[str, str]]) -> Counter:
    return Counter(norm(row.get("recommendation_tier")) for row in rows if norm(row.get("recommendation_tier")))


def top_names_by_tier(rows: Sequence[Dict[str, str]], tier: str, limit: int = 5) -> List[str]:
    filtered = [row for row in rows if norm(row.get("recommendation_tier")) == tier]
    filtered.sort(key=lambda row: (to_int(row.get("rank")) or 999999, norm_ticker(row.get("ticker"))))
    names: List[str] = []
    for row in filtered[:limit]:
        name = norm(row.get("company_name")) or norm_ticker(row.get("ticker"))
        names.append(f"{norm_ticker(row.get('ticker'))} - {name}")
    return names


def build_operator_action(snapshot_exists: bool, snapshot_matches_freeze: bool, forward_fillable_total: int, full_backtest_ready: bool) -> str:
    actions: List[str] = []
    if not snapshot_exists:
        actions.append("RUN_DAILY_RECOMMENDATION_SNAPSHOT")
    if forward_fillable_total == 0:
        actions.append("WAIT_FOR_FUTURE_PRICE_DATA")
    elif forward_fillable_total > 0 and not full_backtest_ready:
        actions.append("RUN_R26C_FORWARD_RETURN_FILLER")
    if forward_fillable_total > 0:
        actions.append("RERUN_R29B_LIMITED_BACKTEST")
    if snapshot_exists and snapshot_matches_freeze:
        actions.append("READY_FOR_MANUAL_REVIEW")
    else:
        actions.append("RUN_DAILY_RECOMMENDATION_SNAPSHOT")
    actions.append("DO_NOT_AUTO_TRADE")
    return ";".join(dict.fromkeys(actions))


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


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def build_report(values: Dict[str, object], rows: Sequence[Dict[str, str]], summary_rows: Sequence[Dict[str, object]]) -> str:
    report = [
        "# V18.30A Daily Operator Control Center",
        "",
        "## Read First",
        "```text",
        "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS),
        "```",
        "",
        "## Today's Operator Action",
        f"- `{values.get('CURRENT_OPERATOR_ACTION')}`",
        f"- `MANUAL_REVIEW_READY: {values.get('MANUAL_REVIEW_READY')}`",
        f"- `AUTO_TRADE: {values.get('AUTO_TRADE')}`",
        "",
        "## Current Recommendation Tier Counts",
        markdown_table(
            [{"recommendation_tier": k, "count": v} for k, v in tier_counts(rows).most_common()],
            ["recommendation_tier", "count"],
        ),
        "## Top CORE_CANDIDATE Names",
        "\n".join(f"- {name}" for name in top_names_by_tier(rows, "CORE_CANDIDATE")) or "_None._",
        "",
        "## Top WATCHLIST_STRONG Names",
        "\n".join(f"- {name}" for name in top_names_by_tier(rows, "WATCHLIST_STRONG")) or "_None._",
        "",
        "## Top OVERHEATED_WAIT Names",
        "\n".join(f"- {name}" for name in top_names_by_tier(rows, "OVERHEATED_WAIT")) or "_None._",
        "",
        "## Top SPECULATIVE_SATELLITE Names",
        "\n".join(f"- {name}" for name in top_names_by_tier(rows, "SPECULATIVE_SATELLITE")) or "_None._",
        "",
        "## Signal Freeze And Snapshot Alignment",
        markdown_table(
            [row for row in summary_rows if row.get("category") == "alignment"],
            SUMMARY_FIELDS,
        ),
        "## Forward-Return And Backtest Readiness",
        markdown_table(
            [row for row in summary_rows if row.get("category") in {"backtest", "forward"}],
            SUMMARY_FIELDS,
        ),
        "## Safety Status",
        markdown_table(
            [row for row in summary_rows if row.get("category") == "safety"],
            SUMMARY_FIELDS,
        ),
        "## Exact Next Commands To Run",
        "- `./scripts/v18/run_v18_29C_daily_recommendation_tier_snapshot_ledger.ps1 -Root D:\\us-tech-quant`",
        "- `./scripts/v18/run_v18_29B_limited_signal_freeze_backtest.ps1 -Root D:\\us-tech-quant`",
        "- Re-run the control center after any new daily snapshot or price-data update.",
    ]
    return "\n".join(report) + "\n"


def run(root: Path) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("V18_30A_%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)

    recs = read_csv(root / CURRENT_RECOMMENDATIONS)
    if not recs:
        raise RuntimeError("Missing current recommendation file")
    if len(recs) != 252:
        raise RuntimeError(f"Invalid recommendation row count: {len(recs)}")
    rec_dup = sum(1 for count in Counter(norm_ticker(row.get("ticker")) for row in recs if norm_ticker(row.get("ticker"))).values() if count > 1)
    if rec_dup:
        raise RuntimeError(f"Duplicate recommendation tickers detected: {rec_dup}")
    missing_tier = sum(1 for row in recs if not norm(row.get("recommendation_tier")))
    missing_action = sum(1 for row in recs if not norm(row.get("recommendation_action")))
    unknown_theme = sum(1 for row in recs if norm(row.get("primary_theme")).upper() in {"", "UNKNOWN"})
    if missing_tier or missing_action or unknown_theme:
        raise RuntimeError("Invalid current recommendation file contents")

    candidates = read_csv(root / CURRENT_CANDIDATES)
    themes = read_csv(root / CURRENT_THEMES)
    if len(candidates) != 252:
        raise RuntimeError(f"Invalid ranked candidate row count: {len(candidates)}")
    if len(themes) != 252:
        raise RuntimeError(f"Invalid theme classification row count: {len(themes)}")
    theme_unknown = sum(1 for row in themes if norm(row.get("primary_theme")).upper() in {"", "UNKNOWN"})
    if theme_unknown:
        raise RuntimeError("Unknown themes detected in theme classification")

    read_firsts = parse_read_first_values(root)
    r28a = read_firsts.get("V18_28A_READ_FIRST.txt", {})
    r28b = read_firsts.get("V18_28B_READ_FIRST.txt", {})
    r28c = read_firsts.get("V18_28C_READ_FIRST.txt", {})
    r28d = read_firsts.get("V18_28D_READ_FIRST.txt", {})
    r29a = read_firsts.get("V18_29A_READ_FIRST.txt", {})
    r29b = read_firsts.get("V18_29B_READ_FIRST.txt", {})
    r29c = read_firsts.get("V18_29C_READ_FIRST.txt", {})

    snapshot_date, snapshot_date_match, snapshot_row_count = latest_snapshot_info(root)
    latest_snapshot_exists = bool(snapshot_date)

    freeze_run_id = r29a.get("LATEST_SIGNAL_FREEZE_RUN_ID") or r29b.get("LATEST_FREEZE_RUN_ID") or ""
    freeze_date = r29a.get("LATEST_SIGNAL_FREEZE_DATE") or r29b.get("LATEST_FREEZE_SIGNAL_DATE") or ""
    freeze_count = to_int(r29a.get("LATEST_SIGNAL_FREEZE_TICKER_COUNT")) or to_int(r29b.get("UNIQUE_TICKER_COUNT")) or 0
    latest_full_freeze_run_id, latest_full_freeze_date, latest_full_freeze_count, previous_full_freeze_run_id, same_day_full_freeze_run_count, same_day_multiple_freeze_warning = latest_full_freeze_info(root)
    if latest_full_freeze_run_id:
        freeze_run_id = latest_full_freeze_run_id
        freeze_date = latest_full_freeze_date
        freeze_count = latest_full_freeze_count

    current_rows = len(recs)
    current_candidates_rows = len(candidates)
    current_themes_rows = len(themes)
    unknown_count = theme_unknown
    current_recommendation_rows_valid = current_rows == 252 and missing_tier == 0 and missing_action == 0 and unknown_theme == 0
    snapshot_matches_freeze = bool(snapshot_date and freeze_date and snapshot_date == freeze_date)
    latest_freeze_matches_current = (r29a.get("LATEST_SIGNAL_FREEZE_MATCHES_CURRENT_RECOMMENDATIONS") == "TRUE")

    forward_1d = to_int(r29a.get("FORWARD_1D_FILLABLE_COUNT")) or 0
    forward_3d = to_int(r29a.get("FORWARD_3D_FILLABLE_COUNT")) or 0
    forward_5d = to_int(r29a.get("FORWARD_5D_FILLABLE_COUNT")) or 0
    forward_10d = to_int(r29a.get("FORWARD_10D_FILLABLE_COUNT")) or 0
    forward_20d = to_int(r29a.get("FORWARD_20D_FILLABLE_COUNT")) or 0
    forward_total = forward_1d + forward_3d + forward_5d + forward_10d + forward_20d
    full_backtest_ready = r29a.get("FULL_RECOMMENDATION_TIER_BACKTEST_READY") == "TRUE" or r29b.get("FULL_RECOMMENDATION_TIER_BACKTEST_READY") == "TRUE" or snapshot_date != ""

    operator_action = build_operator_action(latest_snapshot_exists, snapshot_matches_freeze, forward_total, full_backtest_ready)
    manual_review_ready = bool(current_recommendation_rows_valid)

    summary_rows = [
        {"category": "alignment", "check_name": "latest_recommendation_snapshot_date", "status": "PASS" if latest_snapshot_exists else "WARN", "value": snapshot_date, "detail": "Latest snapshot from recommendation snapshot ledger"},
        {"category": "alignment", "check_name": "snapshot_matches_latest_freeze_date", "status": "PASS" if snapshot_matches_freeze else "WARN", "value": bool_text(snapshot_matches_freeze), "detail": f"snapshot={snapshot_date} freeze={freeze_date}"},
        {"category": "alignment", "check_name": "latest_freeze_run_id", "status": "PASS" if freeze_run_id else "WARN", "value": freeze_run_id, "detail": "from R29A/R29B if available"},
        {"category": "alignment", "check_name": "latest_full_freeze_run_id", "status": "PASS" if latest_full_freeze_run_id else "WARN", "value": latest_full_freeze_run_id, "detail": "directly selected from signal freeze ledger"},
        {"category": "alignment", "check_name": "same_day_multiple_freeze_warning", "status": "WARN" if same_day_multiple_freeze_warning else "PASS", "value": bool_text(same_day_multiple_freeze_warning), "detail": "multiple full freezes on the same signal date"},
        {"category": "backtest", "check_name": "forward_fillable_total", "status": "PASS" if forward_total > 0 else "WARN", "value": forward_total, "detail": "R29A/R29B forward-return fillability"},
        {"category": "backtest", "check_name": "full_recommendation_tier_backtest_ready_now", "status": "PASS" if full_backtest_ready else "WARN", "value": bool_text(full_backtest_ready), "detail": "current system readiness"},
        {"category": "forward", "check_name": "forward_1d_fillable_count", "status": "PASS" if forward_1d > 0 else "WARN", "value": forward_1d, "detail": "R29A"},
        {"category": "forward", "check_name": "forward_3d_fillable_count", "status": "PASS" if forward_3d > 0 else "WARN", "value": forward_3d, "detail": "R29A"},
        {"category": "forward", "check_name": "forward_5d_fillable_count", "status": "PASS" if forward_5d > 0 else "WARN", "value": forward_5d, "detail": "R29A"},
        {"category": "forward", "check_name": "forward_10d_fillable_count", "status": "PASS" if forward_10d > 0 else "WARN", "value": forward_10d, "detail": "R29A"},
        {"category": "forward", "check_name": "forward_20d_fillable_count", "status": "PASS" if forward_20d > 0 else "WARN", "value": forward_20d, "detail": "R29A"},
        {"category": "safety", "check_name": "auto_trade", "status": "PASS", "value": "DISABLED", "detail": "No trading actions are enabled."},
        {"category": "safety", "check_name": "auto_sell", "status": "PASS", "value": "DISABLED", "detail": "No trading actions are enabled."},
        {"category": "safety", "check_name": "official_decision_impact", "status": "PASS", "value": "NONE", "detail": "Read-only control center."},
    ]

    status = STATUS_OK
    if not current_recommendation_rows_valid:
        status = STATUS_FAIL
    elif not latest_snapshot_exists or not snapshot_matches_freeze or forward_total == 0:
        status = STATUS_WARN

    protected_after = protected_sig(root)
    forbidden_modified = protected_after != protected_before
    if forbidden_modified:
        status = STATUS_FAIL

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "CURRENT_RECOMMENDATION_ROW_COUNT": current_rows,
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": current_candidates_rows,
        "THEME_CLASSIFICATION_ROW_COUNT": current_themes_rows,
        "UNKNOWN_PRIMARY_THEME_COUNT": unknown_count,
        "LATEST_SIGNAL_FREEZE_RUN_ID": freeze_run_id,
        "LATEST_SIGNAL_FREEZE_DATE": freeze_date,
        "LATEST_SIGNAL_FREEZE_TICKER_COUNT": freeze_count,
        "LATEST_FULL_SIGNAL_FREEZE_RUN_ID": latest_full_freeze_run_id,
        "LATEST_FULL_SIGNAL_FREEZE_DATE": latest_full_freeze_date,
        "LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT": latest_full_freeze_count,
        "PREVIOUS_FULL_SIGNAL_FREEZE_RUN_ID": previous_full_freeze_run_id,
        "SAME_DAY_FULL_FREEZE_RUN_COUNT": same_day_full_freeze_run_count,
        "SAME_DAY_MULTIPLE_FREEZE_WARNING": bool_text(same_day_multiple_freeze_warning),
        "LATEST_RECOMMENDATION_SNAPSHOT_DATE": snapshot_date,
        "LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT": snapshot_row_count,
        "SNAPSHOT_MATCHES_LATEST_FREEZE_DATE": bool_text(snapshot_matches_freeze),
        "FORWARD_1D_FILLABLE_COUNT": forward_1d,
        "FORWARD_3D_FILLABLE_COUNT": forward_3d,
        "FORWARD_5D_FILLABLE_COUNT": forward_5d,
        "FORWARD_10D_FILLABLE_COUNT": forward_10d,
        "FORWARD_20D_FILLABLE_COUNT": forward_20d,
        "FULL_RECOMMENDATION_TIER_BACKTEST_READY_NOW": bool_text(full_backtest_ready),
        "CURRENT_OPERATOR_ACTION": operator_action,
        "MANUAL_REVIEW_READY": bool_text(manual_review_ready),
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "FORBIDDEN_MODIFIED": bool_text(forbidden_modified),
    }

    write_text(root / OUT_REPORT, build_report(values, recs, summary_rows))
    write_read_first(root / OUT_READ_FIRST, values)
    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    if status == STATUS_FAIL:
        raise RuntimeError("Daily operator control center failed validation checks")
    return values


def write_failure(root: Path, error: BaseException) -> None:
    values: Dict[str, object] = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("V18_30A_%Y%m%d_%H%M%S"),
        "CURRENT_RECOMMENDATION_ROW_COUNT": 0,
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": 0,
        "THEME_CLASSIFICATION_ROW_COUNT": 0,
        "UNKNOWN_PRIMARY_THEME_COUNT": 0,
        "LATEST_SIGNAL_FREEZE_RUN_ID": "",
        "LATEST_SIGNAL_FREEZE_DATE": "",
        "LATEST_SIGNAL_FREEZE_TICKER_COUNT": 0,
        "LATEST_FULL_SIGNAL_FREEZE_RUN_ID": "",
        "LATEST_FULL_SIGNAL_FREEZE_DATE": "",
        "LATEST_FULL_SIGNAL_FREEZE_TICKER_COUNT": 0,
        "PREVIOUS_FULL_SIGNAL_FREEZE_RUN_ID": "",
        "SAME_DAY_FULL_FREEZE_RUN_COUNT": 0,
        "SAME_DAY_MULTIPLE_FREEZE_WARNING": "FALSE",
        "LATEST_RECOMMENDATION_SNAPSHOT_DATE": "",
        "LATEST_RECOMMENDATION_SNAPSHOT_ROW_COUNT": 0,
        "SNAPSHOT_MATCHES_LATEST_FREEZE_DATE": "FALSE",
        "FORWARD_1D_FILLABLE_COUNT": 0,
        "FORWARD_3D_FILLABLE_COUNT": 0,
        "FORWARD_5D_FILLABLE_COUNT": 0,
        "FORWARD_10D_FILLABLE_COUNT": 0,
        "FORWARD_20D_FILLABLE_COUNT": 0,
        "FULL_RECOMMENDATION_TIER_BACKTEST_READY_NOW": "FALSE",
        "CURRENT_OPERATOR_ACTION": "ERROR",
        "MANUAL_REVIEW_READY": "FALSE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "FORBIDDEN_MODIFIED": "UNKNOWN",
    }
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_ERROR_REPORT, f"# V18.30A Daily Operator Control Center Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.30A daily operator control center.")
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
