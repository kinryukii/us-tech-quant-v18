from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")

STATUS_OK = "OK_V18_15A_MANUAL_POSITION_TRADE_FEEDBACK_READY"
STATUS_FAIL = "FAIL_V18_15A_MANUAL_POSITION_TRADE_FEEDBACK"

OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
READ_ONLY = "TRUE"
MANUAL_INPUT_ONLY = "TRUE"
POSITION_FEEDBACK_ONLY = "TRUE"

POSITION_COLUMNS = [
    "position_id",
    "ticker",
    "shares",
    "avg_cost",
    "currency",
    "entry_date",
    "account",
    "position_type",
    "planned_max_jpy",
    "notes",
]

TRADE_COLUMNS = [
    "trade_id",
    "trade_date",
    "ticker",
    "side",
    "shares",
    "price",
    "currency",
    "account",
    "reason",
    "linked_signal_date",
    "manual_override",
    "notes",
]

POSITION_REVIEW_COLUMNS = [
    "position_id",
    "ticker",
    "shares",
    "avg_cost",
    "currency",
    "entry_date",
    "account",
    "position_type",
    "planned_max_jpy",
    "current_price",
    "current_price_date",
    "market_value",
    "unrealized_return",
    "latest_rank",
    "latest_score",
    "latest_signal_date",
    "latest_forward_validation_status",
    "linked_trade_count",
    "lifecycle_stage",
    "review_status",
    "notes",
]

TRADE_FEEDBACK_COLUMNS = [
    "trade_id",
    "trade_date",
    "ticker",
    "side",
    "shares",
    "price",
    "currency",
    "account",
    "reason",
    "linked_signal_date",
    "manual_override",
    "matched_rank",
    "matched_signal_status",
    "feedback_status",
    "notes",
]

LIFECYCLE_AUDIT_COLUMNS = [
    "ticker",
    "position_id",
    "position_rows",
    "trade_rows",
    "signal_rows",
    "current_price_available",
    "lifecycle_stage",
    "notes",
]

SUMMARY_FIELDS = [
    "status",
    "position_count",
    "trade_log_rows",
    "linked_signal_rows",
    "unlinked_position_rows",
    "current_price_available_rows",
    "current_price_missing_rows",
    "validation_fail_count",
    "official_decision_impact",
    "auto_trade",
    "auto_sell",
    "read_only",
    "manual_input_only",
    "position_feedback_only",
    "read_first",
]

INPUT_AUDIT_FIELDS = ["input_name", "path", "exists", "rows", "columns", "last_write_time", "status", "notes"]

DANGEROUS_TOKENS = (
    "SELL_NOW",
    "BUY_NOW_FORCE",
    "AUTO_EXECUTE",
    "LIVE_ORDER",
    "LIVE_SELL",
    "BROKER_ORDER",
)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def ensure_template(path: Path, fields: Sequence[str]) -> bool:
    if path.exists():
        return False
    write_csv(path, [], fields)
    return True


def audit_row(name: str, path: Path, rows: int, fields: Sequence[str], status: str, notes: str) -> Dict[str, str]:
    last_write = ""
    if path.exists():
        last_write = dt.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "input_name": name,
        "path": str(path),
        "exists": "YES" if path.exists() else "NO",
        "rows": str(rows),
        "columns": ";".join(fields),
        "last_write_time": last_write,
        "status": status,
        "notes": notes,
    }


def parse_float(value: str) -> Optional[float]:
    try:
        text = str(value).strip().replace(",", "")
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def fmt_float(value: Optional[float]) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def pick(row: Dict[str, str], names: Sequence[str]) -> str:
    for name in names:
        if name in row and str(row.get(name, "")).strip():
            return str(row.get(name, "")).strip()
    return ""


def latest_signal_by_ticker(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    by_ticker: Dict[str, Dict[str, str]] = {}
    for row in rows:
        ticker = row.get("ticker", "").strip().upper()
        if not ticker:
            continue
        current = by_ticker.get(ticker)
        if current is None or row.get("signal_date", "") >= current.get("signal_date", ""):
            by_ticker[ticker] = row
    return by_ticker


def ranked_by_ticker(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        ticker = row.get("ticker", "").strip().upper()
        if ticker and ticker not in out:
            out[ticker] = row
    return out


def scan_tokens(root: Path, paths: Iterable[Path]) -> List[str]:
    hits: List[str] = []
    for path in paths:
        text = read_text(path)
        for token in DANGEROUS_TOKENS:
            if token in text:
                hits.append(f"{rel(root, path)}::{token}")
    return hits


def markdown_table(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> List[str]:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |")
    return out


def build(root: Path, create_templates_only: bool, allow_empty: bool) -> Tuple[Dict[str, str], int]:
    manual_dir = root / "state/v18/manual"
    positions_path = manual_dir / "V18_MANUAL_POSITIONS.csv"
    trades_path = manual_dir / "V18_MANUAL_TRADE_LOG.csv"
    ensure_dir(manual_dir)
    created_positions = ensure_template(positions_path, POSITION_COLUMNS)
    created_trades = ensure_template(trades_path, TRADE_COLUMNS)

    out_dir = root / "outputs/v18/positions"
    ops_dir = root / "outputs/v18/ops"
    position_review_path = out_dir / "V18_15A_CURRENT_MANUAL_POSITION_REVIEW.csv"
    trade_feedback_path = out_dir / "V18_15A_CURRENT_MANUAL_TRADE_FEEDBACK.csv"
    lifecycle_audit_path = out_dir / "V18_15A_CURRENT_MANUAL_POSITION_LIFECYCLE_AUDIT.csv"
    read_first_path = ops_dir / "V18_15A_READ_FIRST.txt"
    report_path = ops_dir / "V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_REPORT.md"
    summary_path = ops_dir / "V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_SUMMARY.csv"
    input_audit_path = ops_dir / "V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_INPUT_AUDIT.csv"

    positions, position_fields, position_status = read_csv(positions_path)
    trades, trade_fields, trade_status = read_csv(trades_path)
    tracker_path = root / "state/v18/candidate_forward_tracker/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv"
    ranked_path = root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
    tracker_rows, tracker_fields, tracker_status = read_csv(tracker_path)
    ranked_rows, ranked_fields, ranked_status = read_csv(ranked_path)

    input_audit = [
        audit_row("MANUAL_POSITIONS", positions_path, len(positions), position_fields, position_status, "CREATED_TEMPLATE" if created_positions else "MANUAL_INPUT"),
        audit_row("MANUAL_TRADE_LOG", trades_path, len(trades), trade_fields, trade_status, "CREATED_TEMPLATE" if created_trades else "MANUAL_INPUT"),
        audit_row("FORWARD_TRACKER", tracker_path, len(tracker_rows), tracker_fields, tracker_status, "OPTIONAL_SIGNAL_LINK"),
        audit_row("CURRENT_RANKED_CANDIDATES", ranked_path, len(ranked_rows), ranked_fields, ranked_status, "OPTIONAL_RANK_CONTEXT"),
    ]

    latest_signal = latest_signal_by_ticker(tracker_rows)
    latest_ranked = ranked_by_ticker(ranked_rows)
    trades_by_ticker: Dict[str, List[Dict[str, str]]] = {}
    for trade in trades:
        ticker = trade.get("ticker", "").strip().upper()
        if ticker:
            trades_by_ticker.setdefault(ticker, []).append(trade)

    position_reviews: List[Dict[str, str]] = []
    lifecycle_rows: List[Dict[str, str]] = []
    linked_signal_rows = 0
    unlinked_position_rows = 0
    price_available_rows = 0
    price_missing_rows = 0

    for position in positions:
        ticker = position.get("ticker", "").strip().upper()
        signal = latest_signal.get(ticker, {})
        ranked = latest_ranked.get(ticker, {})
        shares = parse_float(position.get("shares", ""))
        avg_cost = parse_float(position.get("avg_cost", ""))
        current_price = parse_float(signal.get("price_at_signal", "")) or parse_float(ranked.get("latest_close", ""))
        current_price_date = signal.get("price_date", "") or ranked.get("latest_price_date", "")
        market_value = shares * current_price if shares is not None and current_price is not None else None
        unrealized = current_price / avg_cost - 1 if current_price is not None and avg_cost not in (None, 0) else None
        linked_trade_count = len(trades_by_ticker.get(ticker, []))
        if signal:
            linked_signal_rows += 1
        else:
            unlinked_position_rows += 1
        if current_price is not None:
            price_available_rows += 1
        else:
            price_missing_rows += 1
        notes = position.get("notes", "")
        if current_price is None:
            notes = f"{notes};CURRENT_PRICE_UNAVAILABLE".strip(";")
        lifecycle_stage = "OPEN_POSITION" if shares and shares > 0 else "WATCHLIST_ONLY"
        if not ticker:
            lifecycle_stage = "NO_POSITION_DATA"
        review_status = "MANUAL_REVIEW_REQUIRED" if not signal or current_price is None else "OK_LINKED_SIGNAL_REVIEW"
        row = {
            "position_id": position.get("position_id", ""),
            "ticker": ticker,
            "shares": position.get("shares", ""),
            "avg_cost": position.get("avg_cost", ""),
            "currency": position.get("currency", ""),
            "entry_date": position.get("entry_date", ""),
            "account": position.get("account", ""),
            "position_type": position.get("position_type", ""),
            "planned_max_jpy": position.get("planned_max_jpy", ""),
            "current_price": fmt_float(current_price),
            "current_price_date": current_price_date,
            "market_value": fmt_float(market_value),
            "unrealized_return": fmt_float(unrealized),
            "latest_rank": signal.get("rank", "") or ranked.get("rank", ""),
            "latest_score": signal.get("score", "") or ranked.get("composite_candidate_score", ""),
            "latest_signal_date": signal.get("signal_date", ""),
            "latest_forward_validation_status": signal.get("validation_status", ""),
            "linked_trade_count": str(linked_trade_count),
            "lifecycle_stage": lifecycle_stage,
            "review_status": review_status,
            "notes": notes,
        }
        position_reviews.append(row)
        lifecycle_rows.append(
            {
                "ticker": ticker,
                "position_id": row["position_id"],
                "position_rows": "1",
                "trade_rows": str(linked_trade_count),
                "signal_rows": "1" if signal else "0",
                "current_price_available": "YES" if current_price is not None else "NO",
                "lifecycle_stage": lifecycle_stage,
                "notes": notes,
            }
        )

    trade_feedback_rows: List[Dict[str, str]] = []
    for trade in trades:
        ticker = trade.get("ticker", "").strip().upper()
        signal = latest_signal.get(ticker, {})
        matched_rank = signal.get("rank", "")
        matched_status = signal.get("validation_status", "")
        feedback_status = "LINKED_TO_SIGNAL" if signal else "UNLINKED_MANUAL_TRADE"
        trade_feedback_rows.append(
            {
                "trade_id": trade.get("trade_id", ""),
                "trade_date": trade.get("trade_date", ""),
                "ticker": ticker,
                "side": trade.get("side", ""),
                "shares": trade.get("shares", ""),
                "price": trade.get("price", ""),
                "currency": trade.get("currency", ""),
                "account": trade.get("account", ""),
                "reason": trade.get("reason", ""),
                "linked_signal_date": trade.get("linked_signal_date", "") or signal.get("signal_date", ""),
                "manual_override": trade.get("manual_override", ""),
                "matched_rank": matched_rank,
                "matched_signal_status": matched_status,
                "feedback_status": feedback_status,
                "notes": trade.get("notes", ""),
            }
        )

    failures: List[str] = []
    if position_status != "OK":
        failures.append("MANUAL_POSITIONS_UNREADABLE")
    if trade_status != "OK":
        failures.append("MANUAL_TRADE_LOG_UNREADABLE")
    if not allow_empty and not create_templates_only and not positions and not trades:
        failures.append("EMPTY_MANUAL_FILES_NOT_ALLOWED")
    if OFFICIAL_DECISION_IMPACT != "NONE":
        failures.append("OFFICIAL_DECISION_IMPACT_NOT_NONE")
    if AUTO_TRADE != "DISABLED":
        failures.append("AUTO_TRADE_NOT_DISABLED")
    if AUTO_SELL != "DISABLED":
        failures.append("AUTO_SELL_NOT_DISABLED")

    write_csv(position_review_path, position_reviews, POSITION_REVIEW_COLUMNS)
    write_csv(trade_feedback_path, trade_feedback_rows, TRADE_FEEDBACK_COLUMNS)
    write_csv(lifecycle_audit_path, lifecycle_rows, LIFECYCLE_AUDIT_COLUMNS)
    write_csv(input_audit_path, input_audit, INPUT_AUDIT_FIELDS)

    scan_paths = [positions_path, trades_path, position_review_path, trade_feedback_path, lifecycle_audit_path, read_first_path, report_path, summary_path, input_audit_path]
    pre_hits = scan_tokens(root, [positions_path, trades_path, position_review_path, trade_feedback_path, lifecycle_audit_path])
    if pre_hits:
        failures.append("DANGEROUS_TOKEN_DETECTED")

    status = STATUS_OK if not failures else STATUS_FAIL
    values = {
        "STATUS": status,
        "POSITION_COUNT": str(len(positions)),
        "TRADE_LOG_ROWS": str(len(trades)),
        "LINKED_SIGNAL_ROWS": str(linked_signal_rows),
        "UNLINKED_POSITION_ROWS": str(unlinked_position_rows),
        "CURRENT_PRICE_AVAILABLE_ROWS": str(price_available_rows),
        "CURRENT_PRICE_MISSING_ROWS": str(price_missing_rows),
        "VALIDATION_FAIL_COUNT": str(len(failures)),
        "FAIL_REASONS": ";".join(failures) if failures else "NONE",
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "READ_ONLY": READ_ONLY,
        "MANUAL_INPUT_ONLY": MANUAL_INPUT_ONLY,
        "POSITION_FEEDBACK_ONLY": POSITION_FEEDBACK_ONLY,
        "DANGEROUS_TOKEN_DETECTED": "YES" if pre_hits else "NO",
        "READ_FIRST": rel(root, read_first_path),
    }

    read_first_keys = [
        "STATUS",
        "POSITION_COUNT",
        "TRADE_LOG_ROWS",
        "LINKED_SIGNAL_ROWS",
        "UNLINKED_POSITION_ROWS",
        "CURRENT_PRICE_AVAILABLE_ROWS",
        "CURRENT_PRICE_MISSING_ROWS",
        "VALIDATION_FAIL_COUNT",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "READ_ONLY",
        "MANUAL_INPUT_ONLY",
        "POSITION_FEEDBACK_ONLY",
    ]
    write_text(read_first_path, "\n".join(f"{key}: {values[key]}" for key in read_first_keys) + f"\nFAIL_REASONS: {values['FAIL_REASONS']}\nDANGEROUS_TOKEN_DETECTED: {values['DANGEROUS_TOKEN_DETECTED']}\n")

    summary_row = {
        "status": values["STATUS"],
        "position_count": values["POSITION_COUNT"],
        "trade_log_rows": values["TRADE_LOG_ROWS"],
        "linked_signal_rows": values["LINKED_SIGNAL_ROWS"],
        "unlinked_position_rows": values["UNLINKED_POSITION_ROWS"],
        "current_price_available_rows": values["CURRENT_PRICE_AVAILABLE_ROWS"],
        "current_price_missing_rows": values["CURRENT_PRICE_MISSING_ROWS"],
        "validation_fail_count": values["VALIDATION_FAIL_COUNT"],
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "read_only": READ_ONLY,
        "manual_input_only": MANUAL_INPUT_ONLY,
        "position_feedback_only": POSITION_FEEDBACK_ONLY,
        "read_first": rel(root, read_first_path),
    }
    write_csv(summary_path, [summary_row], SUMMARY_FIELDS)

    report = [
        "# V18.15A Manual Position And Trade Feedback",
        "",
        "Manual input review only. No trading, selling, broker integration, or official decision impact.",
        "",
        "## Status",
        "",
    ]
    report.extend(f"- {key}: {values[key]}" for key in read_first_keys)
    report.extend([
        f"- FAIL_REASONS: {values['FAIL_REASONS']}",
        f"- DANGEROUS_TOKEN_DETECTED: {values['DANGEROUS_TOKEN_DETECTED']}",
        "",
        "## Position Review",
        "",
    ])
    report.extend(markdown_table(position_reviews[:20], ["position_id", "ticker", "shares", "current_price", "latest_rank", "lifecycle_stage", "review_status"]) if position_reviews else ["No manual positions provided."])
    report.extend(["", "## Trade Feedback", ""])
    report.extend(markdown_table(trade_feedback_rows[:20], ["trade_id", "trade_date", "ticker", "side", "matched_rank", "feedback_status"]) if trade_feedback_rows else ["No manual trades provided."])
    write_text(report_path, "\n".join(report) + "\n")

    post_hits = scan_tokens(root, scan_paths)
    if post_hits and not pre_hits:
        values["STATUS"] = STATUS_FAIL
        values["VALIDATION_FAIL_COUNT"] = "1"
        values["DANGEROUS_TOKEN_DETECTED"] = "YES"
        write_text(read_first_path, "\n".join(f"{key}: {values[key]}" for key in read_first_keys) + "\nFAIL_REASONS: DANGEROUS_TOKEN_DETECTED\nDANGEROUS_TOKEN_DETECTED: YES\n")

    for key in read_first_keys:
        print(f"{key}: {values[key]}")
    print(f"FAIL_REASONS: {values['FAIL_REASONS']}")
    print(f"DANGEROUS_TOKEN_DETECTED: {values['DANGEROUS_TOKEN_DETECTED']}")
    print(f"MANUAL_POSITIONS: {positions_path}")
    print(f"MANUAL_TRADE_LOG: {trades_path}")
    return values, 0 if values["STATUS"] == STATUS_OK else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.15A manual position and trade feedback layer.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    parser.add_argument("--create-templates-only", action="store_true")
    parser.add_argument("--allow-empty-manual-files", action="store_true")
    args = parser.parse_args()
    _, code = build(Path(args.root), args.create_templates_only, args.allow_empty_manual_files)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
