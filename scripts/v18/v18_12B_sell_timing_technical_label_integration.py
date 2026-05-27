from __future__ import annotations

"""V18.12B Sell Timing Technical Label Integration.

This is an additive SHADOW_ONLY layer on top of V18.12A. It reads the current
V18.12A sell timing shadow CSV, discovers existing technical/factor label
outputs, joins label context by ticker when possible, and writes enhanced
review artifacts. It does not place orders, modify official daily scripts,
change factor weights, or affect official decisions.
"""

import argparse
import csv
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
STATUS_OK = "OK_SELL_TIMING_TECHNICAL_LABEL_READY"
MODE = "SHADOW_ONLY"
OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_SELL = "DISABLED"
AUTO_TRADE = "DISABLED"

BASE_12A_FIELDS = [
    "snapshot_date",
    "ticker",
    "source_file",
    "position_status",
    "shares",
    "entry_price",
    "current_price",
    "cost_basis",
    "market_value",
    "unrealized_return_pct",
    "max_return_since_entry_pct",
    "drawdown_from_peak_pct",
    "holding_days",
    "technical_exit_signal",
    "stop_loss_signal",
    "take_profit_signal",
    "trailing_stop_signal",
    "event_exit_signal",
    "overheat_exit_signal",
    "exit_score",
    "shadow_exit_action",
    "shadow_exit_reason",
    "official_decision_impact",
    "auto_sell",
    "auto_trade",
]

TECH_FIELDS = [
    "technical_label_source_count",
    "technical_labels_found",
    "exhaustion_risk_flag",
    "old_overheat_flag",
    "overheat_unclassified_flag",
    "breakout_continuation_flag",
    "pullback_watch_flag",
    "bb_squeeze_flag",
    "vwap_reclaim_flag",
    "vwap_proxy_deviation_flag",
    "rv_spike_flag",
    "opex_pressure_flag",
    "technical_exit_score",
    "technical_exit_action",
    "technical_exit_reason",
    "combined_shadow_exit_action",
    "combined_shadow_exit_reason",
]

OUTPUT_FIELDS = BASE_12A_FIELDS + TECH_FIELDS

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
    "ticker_count",
    "label_hit_count",
    "used_for_label_join",
    "note",
]

ACTION_PRIORITY = {
    "NO_POSITION": 0,
    "HOLD": 1,
    "WATCH_EXIT": 2,
    "TRIM_REVIEW": 3,
    "TAKE_PROFIT_REVIEW": 4,
    "STOP_LOSS_REVIEW": 5,
    "EXIT_REVIEW": 6,
}

LABEL_TERMS = [
    "EXHAUSTION_RISK",
    "OLD_OVERHEAT",
    "OVERHEAT_UNCLASSIFIED",
    "BREAKOUT_CONTINUATION",
    "PULLBACK_WATCH",
    "BB_SQUEEZE",
    "VWAP_RECLAIM",
    "VWAP_RECLAIM_CANDIDATE",
    "VWAP_PROXY_DEVIATION",
    "RV_SPIKE",
    "OPEX_PRESSURE",
    "MONTH_END_REBALANCE",
    "QUARTER_END_REBALANCE",
    "POST_OPEX_RELIEF",
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
                rows = list(reader)
                return rows, list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "CSV_PARSE_FAILED"


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp932", "gbk"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


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


def row_blob(row: Dict[str, str]) -> str:
    return " ".join(str(v) for v in row.values() if v is not None).upper()


def discover_label_inputs(root: Path) -> List[Path]:
    search_roots = [
        root / "outputs/v18/technical_timing",
        root / "outputs/v18/factor_research",
        root / "outputs/v18/weight_research",
        root / "outputs/v18/sell_timing",
        root / "state/v18/simulation",
        root / "outputs/v18/simulation",
    ]
    found: List[Path] = []
    seen = set()
    for base in search_roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            name = path.name.lower()
            if path.suffix.lower() not in {".csv", ".md", ".txt"}:
                continue
            if ".bak" in name:
                continue
            if name.startswith("v18_12b_current_") or name == "v18_12b_read_first.txt":
                continue
            key = str(path.resolve()).lower()
            if key not in seen:
                seen.add(key)
                found.append(path)
    return found


def extract_labels_from_blob(blob: str) -> List[str]:
    labels = {term for term in LABEL_TERMS if term in blob}
    if "VWAP_RECLAIM_CANDIDATE" in blob:
        labels.add("VWAP_RECLAIM")
    if "VWAP_PROXY" in blob or "VWAP_DEVIATION" in blob:
        labels.add("VWAP_PROXY_DEVIATION")
    if "REALIZED_VOLATILITY" in blob and ("SPIKE" in blob or "HIGH" in blob):
        labels.add("RV_SPIKE")
    if "MONTHLY_OPEX" in blob or "OPEX_PRESSURE" in blob:
        labels.add("OPEX_PRESSURE")
    if "BB_SQUEEZE" in blob or "SQUEEZE" in blob:
        labels.add("BB_SQUEEZE")
    if "WATCH_POSITIVE" in blob or "PULLBACK_TIMING" in blob:
        labels.add("PULLBACK_WATCH")
    return sorted(labels)


def add_numeric_factor_labels(row: Dict[str, str], labels: set[str]) -> None:
    vwap_dev = as_float(row.get("vwap_deviation_factor"))
    if vwap_dev is not None and vwap_dev < 0:
        labels.add("VWAP_PROXY_DEVIATION")
    reclaim = as_float(row.get("vwap_reclaim_support_factor"))
    if reclaim is not None and reclaim > 0:
        labels.add("VWAP_RECLAIM")
    rv = as_float(row.get("realized_volatility_factor"))
    if rv is not None and rv >= 0.50:
        labels.add("RV_SPIKE")
    opex = str(row.get("options_expiry_pressure_status", "")).upper()
    if opex and opex not in {"OUT_OF_WINDOW", "NONE", "UNKNOWN"}:
        labels.add("OPEX_PRESSURE")
    if str(row.get("month_end_window_status", "")).upper() not in {"", "OUT_OF_WINDOW", "NONE", "UNKNOWN"}:
        labels.add("MONTH_END_REBALANCE")
    if str(row.get("quarter_end_window_status", "")).upper() not in {"", "OUT_OF_WINDOW", "NONE", "UNKNOWN"}:
        labels.add("QUARTER_END_REBALANCE")
    if str(row.get("opex_relief_status", "")).upper() not in {"", "OUT_OF_WINDOW", "NONE", "UNKNOWN"}:
        labels.add("POST_OPEX_RELIEF")


def collect_label_context(root: Path, snapshot_date: str) -> Tuple[Dict[str, Dict[str, object]], List[Dict[str, str]], int]:
    paths = discover_label_inputs(root)
    by_ticker: Dict[str, Dict[str, object]] = defaultdict(lambda: {"labels": set(), "sources": set(), "blobs": [], "rows": []})
    audit_rows: List[Dict[str, str]] = []
    used_sources = set()

    for path in paths:
        suffix = path.suffix.lower()
        rows: List[Dict[str, str]] = []
        fields: List[str] = []
        parse_status = "OK"
        ticker_col = ""
        tickers = set()
        label_hit_count = 0

        if suffix == ".csv":
            rows, fields, parse_status = read_csv(path)
            ticker_col = pick_col(fields, ["ticker", "symbol", "yf_ticker"]) or ""
            if parse_status == "OK" and ticker_col:
                for row in rows:
                    ticker = str(row.get(ticker_col, "")).strip().upper()
                    if not ticker:
                        continue
                    labels = set(extract_labels_from_blob(row_blob(row)))
                    add_numeric_factor_labels(row, labels)
                    if labels:
                        ctx = by_ticker[ticker]
                        ctx["labels"].update(labels)
                        ctx["sources"].add(str(path))
                        ctx["blobs"].append(row_blob(row)[:500])
                        ctx["rows"].append(row)
                        tickers.add(ticker)
                        label_hit_count += len(labels)
                        used_sources.add(str(path))
        else:
            text = read_text(path).upper()
            labels = set(extract_labels_from_blob(text))
            label_hit_count = len(labels)
            if labels:
                for ticker in sorted(set(re.findall(r"\b[A-Z]{1,5}\b", text))):
                    if ticker in LABEL_TERMS or ticker in {"VIX", "CSV", "READ", "FIRST", "NONE", "TRUE", "FALSE"}:
                        continue
                    ctx = by_ticker[ticker]
                    ctx["labels"].update(labels)
                    ctx["sources"].add(str(path))
                    ctx["blobs"].append(text[:500])
                    tickers.add(ticker)
                used_sources.add(str(path))
            parse_status = "OK_TEXT"

        audit_rows.append(
            {
                "snapshot_date": snapshot_date,
                "search_root": str(path.parent),
                "source_file": str(path),
                "exists": "YES",
                "file_type": suffix.lstrip("."),
                "row_count": str(len(rows)),
                "column_count": str(len(fields)),
                "parse_status": parse_status,
                "ticker_column": ticker_col,
                "ticker_count": str(len(tickers)),
                "label_hit_count": str(label_hit_count),
                "used_for_label_join": "YES" if str(path) in used_sources else "NO",
                "note": "TECHNICAL_LABEL_DISCOVERY",
            }
        )

    return by_ticker, audit_rows, len(used_sources)


def stronger(left: str, right: str) -> str:
    return right if ACTION_PRIORITY.get(right, 0) > ACTION_PRIORITY.get(left, 0) else left


def flag(labels: set[str], name: str) -> str:
    return "YES" if name in labels else "NO"


def evaluate_technical(row: Dict[str, str], labels: set[str], ctx: Dict[str, object]) -> Tuple[str, str, int]:
    if row.get("shadow_exit_action") == "NO_POSITION" or row.get("position_status") == "NO_OPEN_POSITION":
        return "NO_POSITION", "NO_OPEN_POSITIONS_FOUND", 0

    action = "HOLD"
    reasons: List[str] = []
    score = 0

    if "EXHAUSTION_RISK" in labels:
        action = stronger(action, "TRIM_REVIEW")
        reasons.append("exhaustion risk")
        score += 35
    if "OLD_OVERHEAT" in labels:
        action = stronger(action, "TRIM_REVIEW")
        reasons.append("old overheat")
        score += 30
    if "OVERHEAT_UNCLASSIFIED" in labels:
        action = stronger(action, "WATCH_EXIT")
        reasons.append("unclassified overheat")
        score += 15

    vwap_min = None
    for raw_row in ctx.get("rows", []):
        if isinstance(raw_row, dict):
            value = as_float(raw_row.get("vwap_deviation_factor"))
            if value is not None:
                vwap_min = value if vwap_min is None else min(vwap_min, value)
    if "VWAP_PROXY_DEVIATION" in labels:
        if vwap_min is not None and vwap_min <= -0.08:
            action = stronger(action, "TRIM_REVIEW")
            reasons.append(f"strong negative VWAP proxy deviation {vwap_min:.4f}")
            score += 25
        elif vwap_min is not None and vwap_min <= -0.04:
            action = stronger(action, "WATCH_EXIT")
            reasons.append(f"negative VWAP proxy deviation {vwap_min:.4f}")
            score += 15
        else:
            action = stronger(action, "WATCH_EXIT")
            reasons.append("VWAP proxy deviation")
            score += 10
    if "RV_SPIKE" in labels:
        action = stronger(action, "WATCH_EXIT")
        reasons.append("realized volatility spike")
        score += 10
    if "OPEX_PRESSURE" in labels:
        action = stronger(action, "WATCH_EXIT")
        reasons.append("OPEX pressure")
        score += 10

    if "PULLBACK_WATCH" in labels:
        reasons.append("pullback watch context")
    if "BB_SQUEEZE" in labels:
        reasons.append("BB squeeze context")
    if "VWAP_RECLAIM" in labels:
        reasons.append("VWAP reclaim context")

    if "BREAKOUT_CONTINUATION" in labels:
        if not ({"EXHAUSTION_RISK", "OLD_OVERHEAT", "OVERHEAT_UNCLASSIFIED"} & labels):
            if action == "TRIM_REVIEW":
                action = "WATCH_EXIT"
            elif action == "WATCH_EXIT":
                action = "HOLD"
            reasons.append("breakout continuation reduced exit urgency")
            score = max(0, score - 10)
        else:
            reasons.append("breakout continuation present but paired with overheat/exhaustion")

    if not reasons:
        reasons.append("no technical exit label")
    return action, "; ".join(reasons), score


def no_position_base_row(snapshot_date: str) -> Dict[str, str]:
    row = {field: "" for field in BASE_12A_FIELDS}
    row.update(
        {
            "snapshot_date": snapshot_date,
            "position_status": "NO_OPEN_POSITION",
            "technical_exit_signal": "NONE",
            "exit_score": "0",
            "shadow_exit_action": "NO_POSITION",
            "shadow_exit_reason": "NO_OPEN_POSITIONS_FOUND",
            "official_decision_impact": OFFICIAL_DECISION_IMPACT,
            "auto_sell": AUTO_SELL,
            "auto_trade": AUTO_TRADE,
        }
    )
    return row


def load_12a_rows(root: Path, snapshot_date: str) -> Tuple[List[Dict[str, str]], str]:
    path = root / "outputs/v18/sell_timing/V18_12A_CURRENT_SELL_TIMING_SHADOW.csv"
    rows, fields, status = read_csv(path)
    if status == "OK" and rows:
        return rows, str(path)
    return [no_position_base_row(snapshot_date)], str(path)


def enhance_rows(base_rows: List[Dict[str, str]], label_map: Dict[str, Dict[str, object]], snapshot_date: str) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for base in base_rows:
        row = {field: base.get(field, "") for field in BASE_12A_FIELDS}
        row["snapshot_date"] = row.get("snapshot_date") or snapshot_date
        row["official_decision_impact"] = OFFICIAL_DECISION_IMPACT
        row["auto_sell"] = AUTO_SELL
        row["auto_trade"] = AUTO_TRADE

        ticker = str(row.get("ticker", "")).strip().upper()
        ctx = label_map.get(ticker, {"labels": set(), "sources": set(), "rows": []})
        labels = set(ctx.get("labels", set()))
        technical_action, technical_reason, technical_score = evaluate_technical(row, labels, ctx)
        base_action = row.get("shadow_exit_action") or "HOLD"
        combined = stronger(base_action, technical_action)
        if base_action == "NO_POSITION" or technical_action == "NO_POSITION":
            combined = "NO_POSITION"

        source_count = len(ctx.get("sources", set()))
        row.update(
            {
                "technical_label_source_count": str(source_count),
                "technical_labels_found": ";".join(sorted(labels)) if labels else "NONE",
                "exhaustion_risk_flag": flag(labels, "EXHAUSTION_RISK"),
                "old_overheat_flag": flag(labels, "OLD_OVERHEAT"),
                "overheat_unclassified_flag": flag(labels, "OVERHEAT_UNCLASSIFIED"),
                "breakout_continuation_flag": flag(labels, "BREAKOUT_CONTINUATION"),
                "pullback_watch_flag": flag(labels, "PULLBACK_WATCH"),
                "bb_squeeze_flag": flag(labels, "BB_SQUEEZE"),
                "vwap_reclaim_flag": "YES" if {"VWAP_RECLAIM", "VWAP_RECLAIM_CANDIDATE"} & labels else "NO",
                "vwap_proxy_deviation_flag": flag(labels, "VWAP_PROXY_DEVIATION"),
                "rv_spike_flag": flag(labels, "RV_SPIKE"),
                "opex_pressure_flag": flag(labels, "OPEX_PRESSURE"),
                "technical_exit_score": str(technical_score),
                "technical_exit_action": technical_action,
                "technical_exit_reason": technical_reason,
                "combined_shadow_exit_action": combined,
                "combined_shadow_exit_reason": f"V18.12A={base_action}; V18.12B={technical_action}; {technical_reason}",
            }
        )
        out.append(row)
    return out


def make_report(
    report_path: Path,
    csv_path: Path,
    audit_path: Path,
    status: str,
    rows: List[Dict[str, str]],
    audit_rows: List[Dict[str, str]],
    source_count: int,
    position_count: int,
    actionable_count: int,
) -> str:
    action_counts = Counter(row.get("combined_shadow_exit_action", "UNKNOWN") for row in rows)
    top_rows = [r for r in rows if r.get("technical_exit_action") not in {"HOLD", "NO_POSITION"}]
    top_rows.sort(key=lambda r: as_float(r.get("technical_exit_score")) or 0.0, reverse=True)
    available = [r for r in audit_rows if r.get("exists") == "YES"]
    used = [r for r in audit_rows if r.get("used_for_label_join") == "YES"]

    lines = [
        "# V18.12B Sell Timing Technical Label Integration",
        "",
        "## Status",
        "",
        f"- STATUS: {status}",
        f"- MODE: {MODE}",
        f"- POSITION_COUNT: {position_count}",
        f"- ACTIONABLE_EXIT_COUNT: {actionable_count}",
        f"- TECHNICAL_LABEL_SOURCE_COUNT: {source_count}",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "",
        "## Safety Guardrails",
        "",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "- SHADOW_ONLY: technical labels create review context only.",
        "- This is not a sell order and does not affect official decisions, trading logic, or factor weights.",
        "",
        "## Input Source Summary",
        "",
        f"- V18_12A_INPUT: {csv_path.parent / 'V18_12A_CURRENT_SELL_TIMING_SHADOW.csv'}",
        f"- INPUT_AUDIT: {audit_path}",
        "",
        "## Technical Label Source Summary",
        "",
        f"- AVAILABLE_SOURCE_COUNT: {len(available)}",
        f"- USED_LABEL_SOURCE_COUNT: {len(used)}",
    ]
    for audit in used[:15]:
        lines.append(f"- USED: {audit.get('source_file')} (label_hits={audit.get('label_hit_count')})")

    lines.extend(
        [
            "",
            "## Position Summary",
            "",
            f"- POSITION_COUNT: {position_count}",
            f"- OUTPUT_CSV: {csv_path}",
            "",
            "## Exit Action Counts",
            "",
        ]
    )
    for action in ["EXIT_REVIEW", "STOP_LOSS_REVIEW", "TAKE_PROFIT_REVIEW", "TRIM_REVIEW", "WATCH_EXIT", "HOLD", "NO_POSITION"]:
        lines.append(f"- {action}: {action_counts.get(action, 0)}")

    lines.extend(["", "## Top Technical Exit Review Rows", ""])
    if top_rows:
        lines.append("| ticker | technical_action | combined_action | technical_score | labels | reason |")
        lines.append("|---|---:|---:|---:|---|---|")
        for row in top_rows[:15]:
            lines.append(
                f"| {row.get('ticker', '')} | {row.get('technical_exit_action', '')} | {row.get('combined_shadow_exit_action', '')} | "
                f"{row.get('technical_exit_score', '')} | {row.get('technical_labels_found', '')} | {row.get('technical_exit_reason', '')} |"
            )
    else:
        lines.append("No actionable technical exit review rows.")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- V18.12B is additive to V18.12A and preserves V18.12A stable files.",
            "- Combined action uses the stronger of V18.12A shadow_exit_action and V18.12B technical_exit_action.",
            "- Immediate sell action vocabulary is intentionally excluded.",
            "- Outputs are review-only shadow artifacts.",
            f"- REPORT: {report_path}",
        ]
    )
    return "\n".join(lines) + "\n"


def make_read_first(
    status: str,
    position_count: int,
    actionable_count: int,
    source_count: int,
    report_path: Path,
    csv_path: Path,
    audit_path: Path,
) -> str:
    return "\n".join(
        [
            "V18.12B SELL TIMING TECHNICAL LABEL READ FIRST",
            "",
            "STATUS:",
            status,
            "",
            "POSITION_COUNT:",
            str(position_count),
            "",
            "ACTIONABLE_EXIT_COUNT:",
            str(actionable_count),
            "",
            "TECHNICAL_LABEL_SOURCE_COUNT:",
            str(source_count),
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
            "INPUT_AUDIT:",
            str(audit_path),
            "",
        ]
    )


def generate(root: Path) -> Dict[str, str]:
    snapshot_date = date.today().isoformat()
    out_dir = root / "outputs/v18/sell_timing"
    report_path = out_dir / "V18_12B_CURRENT_SELL_TIMING_TECHNICAL_LABEL_REPORT.md"
    csv_path = out_dir / "V18_12B_CURRENT_SELL_TIMING_TECHNICAL_LABEL.csv"
    audit_path = out_dir / "V18_12B_CURRENT_TECHNICAL_LABEL_INPUT_AUDIT.csv"
    read_first_path = out_dir / "V18_12B_READ_FIRST.txt"

    base_rows, _ = load_12a_rows(root, snapshot_date)
    label_map, audit_rows, technical_source_count = collect_label_context(root, snapshot_date)
    output_rows = enhance_rows(base_rows, label_map, snapshot_date)

    position_count = sum(1 for row in output_rows if row.get("combined_shadow_exit_action") != "NO_POSITION")
    actionable_count = sum(1 for row in output_rows if row.get("combined_shadow_exit_action") not in {"HOLD", "NO_POSITION"})
    if position_count == 0:
        actionable_count = 0
        for row in output_rows:
            row["combined_shadow_exit_action"] = "NO_POSITION"

    write_csv(csv_path, output_rows, OUTPUT_FIELDS)
    write_csv(audit_path, audit_rows, AUDIT_FIELDS)
    write_text(report_path, make_report(report_path, csv_path, audit_path, STATUS_OK, output_rows, audit_rows, technical_source_count, position_count, actionable_count))
    write_text(read_first_path, make_read_first(STATUS_OK, position_count, actionable_count, technical_source_count, report_path, csv_path, audit_path))

    return {
        "STATUS": STATUS_OK,
        "POSITION_COUNT": str(position_count),
        "ACTIONABLE_EXIT_COUNT": str(actionable_count),
        "TECHNICAL_LABEL_SOURCE_COUNT": str(technical_source_count),
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_SELL": AUTO_SELL,
        "AUTO_TRADE": AUTO_TRADE,
        "REPORT": str(report_path),
        "CSV": str(csv_path),
        "INPUT_AUDIT": str(audit_path),
        "READ_FIRST": str(read_first_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.12B sell timing technical label integration.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()

    result = generate(Path(args.root))
    for key in [
        "STATUS",
        "POSITION_COUNT",
        "ACTIONABLE_EXIT_COUNT",
        "TECHNICAL_LABEL_SOURCE_COUNT",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_SELL",
        "AUTO_TRADE",
        "REPORT",
        "CSV",
        "INPUT_AUDIT",
        "READ_FIRST",
    ]:
        print(f"{key}: {result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
