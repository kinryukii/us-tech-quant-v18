from __future__ import annotations

"""V18.12D Exit Signal Forward Validation.

Research-only shadow layer for evaluating V18.12 exit review signals over
future horizons. The module maintains a persistent tracker, copies it to
outputs, and never modifies official daily scripts, stable snapshots, factor
weights, or trading behavior.
"""

import argparse
import csv
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
STATUS_OK = "OK_EXIT_SIGNAL_FORWARD_VALIDATION_READY"
MODE = "SHADOW_ONLY"
OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_SELL = "DISABLED"
AUTO_TRADE = "DISABLED"
HORIZONS = [1, 5, 10, 20]
ACTIONABLE_ACTIONS = {"WATCH_EXIT", "TRIM_REVIEW", "TAKE_PROFIT_REVIEW", "STOP_LOSS_REVIEW", "EXIT_REVIEW"}
PROTECTIVE_ACTIONS = {"TRIM_REVIEW", "STOP_LOSS_REVIEW", "EXIT_REVIEW"}

TRACKER_FIELDS = [
    "signal_snapshot_date",
    "ticker",
    "source_file",
    "position_status",
    "final_shadow_exit_action",
    "final_shadow_exit_reason",
    "combined_shadow_exit_action",
    "technical_exit_action",
    "lifecycle_stage",
    "shares",
    "entry_price",
    "current_price",
    "signal_price",
    "unrealized_return_pct",
    "max_return_since_entry_pct",
    "drawdown_from_peak_pct",
    "holding_days",
    "forward_1d_return_pct",
    "forward_5d_return_pct",
    "forward_10d_return_pct",
    "forward_20d_return_pct",
    "forward_1d_status",
    "forward_5d_status",
    "forward_10d_status",
    "forward_20d_status",
    "validation_label",
    "validation_interpretation",
    "official_decision_impact",
    "auto_sell",
    "auto_trade",
]

AUDIT_FIELDS = [
    "snapshot_date",
    "search_root",
    "source_file",
    "exists",
    "file_type",
    "row_count",
    "column_count",
    "parse_status",
    "ticker_column",
    "price_column",
    "date_column",
    "ticker_count",
    "used_for_price_context",
    "note",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: List[Dict[str, str]], fields: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def as_float(value: object) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip().replace(",", "").replace("$", "").replace("%", "")
    if not s or s.upper() in {"NAN", "NONE", "UNKNOWN", "NULL"}:
        return None
    try:
        return float(s)
    except Exception:
        return None


def fmt_pct(value: Optional[float]) -> str:
    return "" if value is None else f"{value:.6f}"


def parse_date(value: object) -> Optional[date]:
    s = str(value or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:19], fmt).date()
        except Exception:
            continue
    return None


def pick_col(fields: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    field_list = list(fields)
    exact = {f.lower(): f for f in field_list}
    for cand in candidates:
        if cand.lower() in exact:
            return exact[cand.lower()]
    for field in field_list:
        fl = field.lower()
        for cand in candidates:
            if cand.lower() in fl:
                return field
    return None


def load_signal_rows(root: Path) -> Tuple[List[Dict[str, str]], str, str]:
    candidates = [
        ("V18.12C", root / "outputs/v18/sell_timing/V18_12C_CURRENT_POSITION_LIFECYCLE_REVIEW.csv"),
        ("V18.12B", root / "outputs/v18/sell_timing/V18_12B_CURRENT_SELL_TIMING_TECHNICAL_LABEL.csv"),
        ("V18.12A", root / "outputs/v18/sell_timing/V18_12A_CURRENT_SELL_TIMING_SHADOW.csv"),
    ]
    for label, path in candidates:
        rows, _, status = read_csv(path)
        if status == "OK" and rows:
            return rows, str(path), label
    return [], str(candidates[-1][1]), "NONE"


def discover_inputs(root: Path) -> List[Path]:
    roots = [
        root / "state/v18/simulation",
        root / "outputs/v18/simulation",
        root / "outputs/v18/technical_timing",
        root / "outputs/v18/factor_research",
        root / "outputs/v18/weight_research",
    ]
    found: List[Path] = []
    seen = set()
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if ".bak" in path.name.lower():
                continue
            if path.suffix.lower() not in {".csv", ".md", ".txt"}:
                continue
            key = str(path.resolve()).lower()
            if key not in seen:
                seen.add(key)
                found.append(path)
    return found


def build_price_map(root: Path, snapshot_date: str) -> Tuple[Dict[str, List[Tuple[date, float]]], List[Dict[str, str]]]:
    price_map: Dict[str, List[Tuple[date, float]]] = {}
    audit: List[Dict[str, str]] = []
    for path in discover_inputs(root):
        rows: List[Dict[str, str]] = []
        fields: List[str] = []
        parse_status = "SKIPPED_NON_CSV"
        ticker_col = ""
        price_col = ""
        date_col = ""
        tickers = set()
        used = "NO"
        if path.suffix.lower() == ".csv":
            rows, fields, parse_status = read_csv(path)
            ticker_col = pick_col(fields, ["ticker", "symbol", "yf_ticker"]) or ""
            price_col = pick_col(fields, ["close", "latest_price_usd", "last_price_usd", "current_price", "price", "latest_close", "last_close", "adj_close"]) or ""
            date_col = pick_col(fields, ["price_date", "date", "snapshot_date", "base_date", "latest_date", "asof_date"]) or ""
            if parse_status == "OK" and ticker_col and price_col:
                for row in rows:
                    ticker = str(row.get(ticker_col, "")).strip().upper()
                    price = as_float(row.get(price_col))
                    d = parse_date(row.get(date_col)) if date_col else None
                    if ticker and price is not None and price > 0 and d:
                        price_map.setdefault(ticker, []).append((d, price))
                        tickers.add(ticker)
                        used = "YES"
        audit.append(
            {
                "snapshot_date": snapshot_date,
                "search_root": str(path.parent),
                "source_file": str(path),
                "exists": "YES",
                "file_type": path.suffix.lower().lstrip("."),
                "row_count": str(len(rows)),
                "column_count": str(len(fields)),
                "parse_status": parse_status,
                "ticker_column": ticker_col,
                "price_column": price_col,
                "date_column": date_col,
                "ticker_count": str(len(tickers)),
                "used_for_price_context": used,
                "note": "FORWARD_VALIDATION_INPUT_DISCOVERY",
            }
        )
    for ticker in list(price_map.keys()):
        dedup = {}
        for d, p in price_map[ticker]:
            dedup[d] = p
        price_map[ticker] = sorted(dedup.items(), key=lambda x: x[0])
    return price_map, audit


def tracker_key(row: Dict[str, str]) -> Tuple[str, str, str]:
    return (
        str(row.get("signal_snapshot_date", "")).strip(),
        str(row.get("ticker", "")).strip().upper(),
        str(row.get("final_shadow_exit_action", "")).strip().upper(),
    )


def signal_key_from_source(row: Dict[str, str], snapshot_date: str) -> Tuple[str, str, str]:
    action = row.get("final_shadow_exit_action") or row.get("combined_shadow_exit_action") or row.get("shadow_exit_action") or "HOLD"
    return (
        str(row.get("snapshot_date", snapshot_date)).strip() or snapshot_date,
        str(row.get("ticker", "")).strip().upper(),
        str(action).strip().upper(),
    )


def normalize_signal_row(row: Dict[str, str], input_path: str, snapshot_date: str) -> Dict[str, str]:
    action = row.get("final_shadow_exit_action") or row.get("combined_shadow_exit_action") or row.get("shadow_exit_action") or "HOLD"
    reason = row.get("final_shadow_exit_reason") or row.get("combined_shadow_exit_reason") or row.get("shadow_exit_reason") or ""
    signal_price = row.get("current_price") or row.get("signal_price") or ""
    status = "NO_SIGNAL" if action in {"HOLD", "NO_POSITION"} else "PENDING"
    out = {field: "" for field in TRACKER_FIELDS}
    out.update(
        {
            "signal_snapshot_date": str(row.get("snapshot_date", snapshot_date)).strip() or snapshot_date,
            "ticker": str(row.get("ticker", "")).strip().upper(),
            "source_file": input_path,
            "position_status": row.get("position_status", ""),
            "final_shadow_exit_action": action,
            "final_shadow_exit_reason": reason,
            "combined_shadow_exit_action": row.get("combined_shadow_exit_action") or row.get("shadow_exit_action") or action,
            "technical_exit_action": row.get("technical_exit_action") or row.get("technical_exit_signal") or "",
            "lifecycle_stage": row.get("lifecycle_stage", ""),
            "shares": row.get("shares", ""),
            "entry_price": row.get("entry_price", ""),
            "current_price": row.get("current_price", ""),
            "signal_price": signal_price,
            "unrealized_return_pct": row.get("unrealized_return_pct", ""),
            "max_return_since_entry_pct": row.get("max_return_since_entry_pct", ""),
            "drawdown_from_peak_pct": row.get("drawdown_from_peak_pct", ""),
            "holding_days": row.get("holding_days", ""),
            "forward_1d_status": status,
            "forward_5d_status": status,
            "forward_10d_status": status,
            "forward_20d_status": status,
            "validation_label": "NO_ACTIONABLE_EXIT" if action in {"HOLD", "NO_POSITION"} else "INSUFFICIENT_DATA",
            "validation_interpretation": "No actionable exit review signal." if action in {"HOLD", "NO_POSITION"} else "Forward returns pending.",
            "official_decision_impact": OFFICIAL_DECISION_IMPACT,
            "auto_sell": AUTO_SELL,
            "auto_trade": AUTO_TRADE,
        }
    )
    return out


def fill_forward_returns(row: Dict[str, str], price_map: Dict[str, List[Tuple[date, float]]]) -> None:
    action = str(row.get("final_shadow_exit_action", "")).upper()
    if action not in ACTIONABLE_ACTIONS:
        for h in HORIZONS:
            row[f"forward_{h}d_status"] = "NO_SIGNAL"
        return
    ticker = str(row.get("ticker", "")).strip().upper()
    series = price_map.get(ticker) or []
    signal_date = parse_date(row.get("signal_snapshot_date"))
    signal_price = as_float(row.get("signal_price")) or as_float(row.get("current_price"))
    if not ticker or not signal_date or not signal_price:
        for h in HORIZONS:
            if row.get(f"forward_{h}d_status") in {"", "PENDING"}:
                row[f"forward_{h}d_status"] = "NO_PRICE_DATA"
        return
    future = [(d, p) for d, p in series if d > signal_date]
    if not future:
        for h in HORIZONS:
            if row.get(f"forward_{h}d_status") in {"", "PENDING"}:
                row[f"forward_{h}d_status"] = "NOT_MATURED"
        return
    for h in HORIZONS:
        ret_field = f"forward_{h}d_return_pct"
        status_field = f"forward_{h}d_status"
        if row.get(status_field) == "FILLED" and row.get(ret_field):
            continue
        if len(future) >= h:
            target_price = future[h - 1][1]
            row[ret_field] = fmt_pct((target_price / signal_price - 1.0) * 100.0)
            row[status_field] = "FILLED"
        else:
            row[status_field] = "NOT_MATURED"


def validation_label(row: Dict[str, str]) -> Tuple[str, str]:
    action = str(row.get("final_shadow_exit_action", "")).upper()
    if action not in ACTIONABLE_ACTIONS:
        return "NO_ACTIONABLE_EXIT", "No actionable exit review signal."
    returns = []
    for h in HORIZONS:
        if row.get(f"forward_{h}d_status") == "FILLED":
            val = as_float(row.get(f"forward_{h}d_return_pct"))
            if val is not None:
                returns.append(val)
    if not returns:
        return "INSUFFICIENT_DATA", "No matured forward returns available."
    avg_ret = sum(returns) / len(returns)
    min_ret = min(returns)
    max_ret = max(returns)
    if action in PROTECTIVE_ACTIONS and (avg_ret <= -3.0 or min_ret <= -5.0):
        return "EXIT_SIGNAL_HELPED", f"Forward returns were negative after signal; avg={avg_ret:.4f}."
    if action in PROTECTIVE_ACTIONS and (avg_ret >= 3.0 or max_ret >= 5.0):
        return "EXIT_SIGNAL_HURT", f"Forward returns were positive after signal; avg={avg_ret:.4f}."
    if avg_ret <= -3.0:
        return "EXIT_SIGNAL_HELPED", f"Watch signal preceded downside; avg={avg_ret:.4f}."
    if avg_ret >= 3.0:
        return "EXIT_SIGNAL_HURT", f"Watch signal preceded upside; avg={avg_ret:.4f}."
    return "EXIT_SIGNAL_NEUTRAL", f"Forward returns were small or mixed; avg={avg_ret:.4f}."


def update_tracker(root: Path, signal_rows: List[Dict[str, str]], input_path: str, snapshot_date: str, price_map: Dict[str, List[Tuple[date, float]]]) -> Tuple[List[Dict[str, str]], int]:
    tracker_path = root / "state/v18/sell_timing/V18_CURRENT_EXIT_SIGNAL_FORWARD_TRACKER.csv"
    existing, _, _ = read_csv(tracker_path)
    normalized_existing = [{field: row.get(field, "") for field in TRACKER_FIELDS} for row in existing]
    seen = {tracker_key(row) for row in normalized_existing}
    new_rows: List[Dict[str, str]] = []
    for src in signal_rows:
        normalized = normalize_signal_row(src, input_path, snapshot_date)
        key = tracker_key(normalized)
        if key in seen:
            continue
        seen.add(key)
        new_rows.append(normalized)
    rows = normalized_existing + new_rows
    for row in rows:
        fill_forward_returns(row, price_map)
        label, interpretation = validation_label(row)
        row["validation_label"] = label
        row["validation_interpretation"] = interpretation
        row["official_decision_impact"] = OFFICIAL_DECISION_IMPACT
        row["auto_sell"] = AUTO_SELL
        row["auto_trade"] = AUTO_TRADE
    write_csv(tracker_path, rows, TRACKER_FIELDS)
    return rows, len(new_rows)


def make_report(
    report_path: Path,
    csv_path: Path,
    tracker_path: Path,
    audit_path: Path,
    input_path: str,
    input_label: str,
    rows: List[Dict[str, str]],
    audit_rows: List[Dict[str, str]],
    new_count: int,
) -> str:
    actionable = [r for r in rows if r.get("final_shadow_exit_action") in ACTIONABLE_ACTIONS]
    forward_complete = [r for r in rows if any(r.get(f"forward_{h}d_status") == "FILLED" for h in HORIZONS)]
    pending = [r for r in rows if any(r.get(f"forward_{h}d_status") in {"PENDING", "NOT_MATURED"} for h in HORIZONS)]
    labels = Counter(r.get("validation_label", "UNKNOWN") for r in rows)
    source_used = sum(1 for r in audit_rows if r.get("used_for_price_context") == "YES")
    lines = [
        "# V18.12D Exit Signal Forward Validation",
        "",
        "## Status",
        "",
        f"- STATUS: {STATUS_OK}",
        f"- MODE: {MODE}",
        f"- TRACKER_ROWS: {len(rows)}",
        f"- NEW_SIGNAL_ROWS_ADDED: {new_count}",
        f"- ACTIONABLE_EXIT_SIGNAL_COUNT: {len(actionable)}",
        f"- FORWARD_COMPLETE_ROWS: {len(forward_complete)}",
        f"- PENDING_FORWARD_ROWS: {len(pending)}",
        f"- VALIDATION_LABEL_COUNT: {len(labels)}",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "",
        "## Safety Guardrails",
        "",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "- SHADOW_ONLY: research validation only.",
        "- This is not a sell order and does not affect official decisions, official daily scripts, trading logic, or factor weights.",
        "",
        "## Input Source Summary",
        "",
        f"- SELL_TIMING_INPUT: {input_path}",
        f"- SELL_TIMING_INPUT_LAYER: {input_label}",
        f"- PRICE_CONTEXT_SOURCE_COUNT: {source_used}",
        f"- INPUT_AUDIT: {audit_path}",
        "",
        "## Tracker Summary",
        "",
        f"- TRACKER: {tracker_path}",
        f"- OUTPUT_CSV: {csv_path}",
        f"- TRACKER_ROWS: {len(rows)}",
        f"- NEW_SIGNAL_ROWS_ADDED: {new_count}",
        "",
        "## Actionable Exit Signal Count",
        "",
        f"- ACTIONABLE_EXIT_SIGNAL_COUNT: {len(actionable)}",
        "",
        "## Forward Label Maturity Summary",
        "",
        f"- FORWARD_COMPLETE_ROWS: {len(forward_complete)}",
        f"- PENDING_FORWARD_ROWS: {len(pending)}",
        "",
        "## Validation Label Counts",
        "",
    ]
    for label in ["EXIT_SIGNAL_HELPED", "EXIT_SIGNAL_HURT", "EXIT_SIGNAL_NEUTRAL", "INSUFFICIENT_DATA", "NO_ACTIONABLE_EXIT"]:
        lines.append(f"- {label}: {labels.get(label, 0)}")
    lines.extend(["", "## Pending Forward Rows", ""])
    pending_rows = [r for r in rows if r.get("validation_label") == "INSUFFICIENT_DATA"][:15]
    if pending_rows:
        lines.append("| signal_snapshot_date | ticker | action | label |")
        lines.append("|---|---|---|---|")
        for row in pending_rows:
            lines.append(f"| {row.get('signal_snapshot_date', '')} | {row.get('ticker', '')} | {row.get('final_shadow_exit_action', '')} | {row.get('validation_label', '')} |")
    else:
        lines.append("No pending actionable forward validation rows.")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- V18.12D is shadow-only research validation for V18.12 exit review signals.",
            "- It updates only the V18.12D forward tracker and generated sell_timing outputs.",
            "- Immediate live-sell vocabulary is intentionally excluded from generated outputs.",
            f"- REPORT: {report_path}",
        ]
    )
    return "\n".join(lines) + "\n"


def make_read_first(rows: List[Dict[str, str]], new_count: int, report_path: Path, csv_path: Path, tracker_path: Path, audit_path: Path) -> str:
    actionable_count = sum(1 for r in rows if r.get("final_shadow_exit_action") in ACTIONABLE_ACTIONS)
    complete_count = sum(1 for r in rows if any(r.get(f"forward_{h}d_status") == "FILLED" for h in HORIZONS))
    pending_count = sum(1 for r in rows if any(r.get(f"forward_{h}d_status") in {"PENDING", "NOT_MATURED"} for h in HORIZONS))
    label_count = len(Counter(r.get("validation_label", "UNKNOWN") for r in rows))
    return "\n".join(
        [
            "V18.12D EXIT SIGNAL FORWARD VALIDATION READ FIRST",
            "",
            "STATUS:",
            STATUS_OK,
            "",
            "TRACKER_ROWS:",
            str(len(rows)),
            "",
            "NEW_SIGNAL_ROWS_ADDED:",
            str(new_count),
            "",
            "ACTIONABLE_EXIT_SIGNAL_COUNT:",
            str(actionable_count),
            "",
            "FORWARD_COMPLETE_ROWS:",
            str(complete_count),
            "",
            "PENDING_FORWARD_ROWS:",
            str(pending_count),
            "",
            "VALIDATION_LABEL_COUNT:",
            str(label_count),
            "",
            "OFFICIAL_DECISION_IMPACT:",
            OFFICIAL_DECISION_IMPACT,
            "",
            "AUTO_SELL:",
            AUTO_SELL,
            "",
            "AUTO_TRADE:",
            AUTO_TRADE,
            "",
            "REPORT:",
            str(report_path),
            "",
            "CSV:",
            str(csv_path),
            "",
            "TRACKER:",
            str(tracker_path),
            "",
            "INPUT_AUDIT:",
            str(audit_path),
            "",
        ]
    )


def generate(root: Path) -> Dict[str, str]:
    snapshot_date = date.today().isoformat()
    out_dir = root / "outputs/v18/sell_timing"
    state_dir = root / "state/v18/sell_timing"
    report_path = out_dir / "V18_12D_CURRENT_EXIT_SIGNAL_FORWARD_VALIDATION_REPORT.md"
    csv_path = out_dir / "V18_12D_CURRENT_EXIT_SIGNAL_FORWARD_VALIDATION.csv"
    audit_path = out_dir / "V18_12D_CURRENT_EXIT_SIGNAL_FORWARD_VALIDATION_INPUT_AUDIT.csv"
    read_first_path = out_dir / "V18_12D_READ_FIRST.txt"
    tracker_path = state_dir / "V18_CURRENT_EXIT_SIGNAL_FORWARD_TRACKER.csv"
    tracker_output_path = out_dir / "V18_CURRENT_EXIT_SIGNAL_FORWARD_TRACKER.csv"

    signal_rows, input_path, input_label = load_signal_rows(root)
    price_map, audit_rows = build_price_map(root, snapshot_date)
    tracker_rows, new_count = update_tracker(root, signal_rows, input_path, snapshot_date, price_map)
    write_csv(csv_path, tracker_rows, TRACKER_FIELDS)
    write_csv(tracker_output_path, tracker_rows, TRACKER_FIELDS)
    write_csv(audit_path, audit_rows, AUDIT_FIELDS)
    write_text(report_path, make_report(report_path, csv_path, tracker_path, audit_path, input_path, input_label, tracker_rows, audit_rows, new_count))
    write_text(read_first_path, make_read_first(tracker_rows, new_count, report_path, csv_path, tracker_path, audit_path))

    actionable_count = sum(1 for r in tracker_rows if r.get("final_shadow_exit_action") in ACTIONABLE_ACTIONS)
    complete_count = sum(1 for r in tracker_rows if any(r.get(f"forward_{h}d_status") == "FILLED" for h in HORIZONS))
    pending_count = sum(1 for r in tracker_rows if any(r.get(f"forward_{h}d_status") in {"PENDING", "NOT_MATURED"} for h in HORIZONS))
    label_count = len(Counter(r.get("validation_label", "UNKNOWN") for r in tracker_rows))
    return {
        "STATUS": STATUS_OK,
        "TRACKER_ROWS": str(len(tracker_rows)),
        "NEW_SIGNAL_ROWS_ADDED": str(new_count),
        "ACTIONABLE_EXIT_SIGNAL_COUNT": str(actionable_count),
        "FORWARD_COMPLETE_ROWS": str(complete_count),
        "PENDING_FORWARD_ROWS": str(pending_count),
        "VALIDATION_LABEL_COUNT": str(label_count),
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_SELL": AUTO_SELL,
        "AUTO_TRADE": AUTO_TRADE,
        "REPORT": str(report_path),
        "CSV": str(csv_path),
        "TRACKER": str(tracker_path),
        "INPUT_AUDIT": str(audit_path),
        "READ_FIRST": str(read_first_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.12D exit signal forward validation.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    result = generate(Path(args.root))
    for key in [
        "STATUS",
        "TRACKER_ROWS",
        "NEW_SIGNAL_ROWS_ADDED",
        "ACTIONABLE_EXIT_SIGNAL_COUNT",
        "FORWARD_COMPLETE_ROWS",
        "PENDING_FORWARD_ROWS",
        "VALIDATION_LABEL_COUNT",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_SELL",
        "AUTO_TRADE",
        "REPORT",
        "CSV",
        "TRACKER",
        "INPUT_AUDIT",
        "READ_FIRST",
    ]:
        print(f"{key}: {result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
