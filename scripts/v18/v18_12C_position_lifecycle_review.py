from __future__ import annotations

"""V18.12C Position Lifecycle Review.

Additive SHADOW_ONLY layer on top of V18.12A/V18.12B sell timing outputs.
It reviews the age and lifecycle state of open positions and combines that
context with existing shadow exit actions. It does not trade, sell, modify
official daily scripts, alter factor weights, or affect official decisions.
"""

import argparse
import csv
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
STATUS_OK = "OK_POSITION_LIFECYCLE_REVIEW_READY"
MODE = "SHADOW_ONLY"
OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_SELL = "DISABLED"
AUTO_TRADE = "DISABLED"

OUTPUT_FIELDS = [
    "snapshot_date",
    "ticker",
    "source_file",
    "position_status",
    "shares",
    "entry_date",
    "entry_price",
    "current_price",
    "cost_basis",
    "market_value",
    "unrealized_return_pct",
    "max_return_since_entry_pct",
    "drawdown_from_peak_pct",
    "holding_days",
    "lifecycle_stage",
    "original_buy_reason",
    "current_buy_reason_still_valid",
    "technical_exit_action",
    "combined_shadow_exit_action",
    "lifecycle_exit_score",
    "lifecycle_exit_action",
    "lifecycle_exit_reason",
    "final_shadow_exit_action",
    "final_shadow_exit_reason",
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
    "position_like",
    "open_position_count",
    "used_for_lifecycle_context",
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

OPEN_STATUS_BLOCK_TERMS = {"CLOSED", "SOLD", "EXITED", "FLAT", "NO_POSITION"}
POSITION_NAME_TERMS = ["positions", "current_positions", "paper_positions", "latest_paper_positions"]
DISCOVERY_TERMS = ["positions", "current_positions", "paper_positions", "latest_paper_positions", "account", "paper_pnl", "trade_log", "candidate_tracker"]


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


def as_int(value: object) -> Optional[int]:
    x = as_float(value)
    if x is None:
        return None
    return int(x)


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


def stronger(left: str, right: str) -> str:
    return right if ACTION_PRIORITY.get(right, 0) > ACTION_PRIORITY.get(left, 0) else left


def discover_inputs(root: Path) -> List[Path]:
    search_roots = [
        root / "state/v18/simulation",
        root / "outputs/v18/simulation",
        root / "state/v18",
        root / "outputs/v18",
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
            if any(term in name for term in DISCOVERY_TERMS):
                key = str(path.resolve()).lower()
                if key not in seen:
                    seen.add(key)
                    found.append(path)
    return found


def is_position_like(path: Path, rows: List[Dict[str, str]], fields: List[str]) -> bool:
    name = path.name.lower()
    if any(term in name for term in POSITION_NAME_TERMS):
        return True
    ticker_col = pick_col(fields, ["ticker", "symbol"])
    qty_col = pick_col(fields, ["quantity", "shares", "share_count", "position_qty", "position_size"])
    entry_col = pick_col(fields, ["avg_cost_usd", "avg_cost", "entry_price", "cost_basis_price"])
    return bool(ticker_col and (qty_col or entry_col) and rows)


def open_position_count(rows: List[Dict[str, str]], fields: List[str]) -> int:
    ticker_col = pick_col(fields, ["ticker", "symbol"])
    qty_col = pick_col(fields, ["quantity", "shares", "share_count", "position_qty", "position_size"])
    status_col = pick_col(fields, ["position_status", "status", "state"])
    market_col = pick_col(fields, ["market_value_usd", "market_value"])
    count = 0
    for row in rows:
        ticker = str(row.get(ticker_col or "", "")).strip().upper()
        if not ticker:
            continue
        status = str(row.get(status_col or "", "")).strip().upper()
        if status and any(term in status for term in OPEN_STATUS_BLOCK_TERMS):
            continue
        qty = as_float(row.get(qty_col or ""))
        market_value = as_float(row.get(market_col or ""))
        if (qty is not None and qty > 0) or (qty is None and market_value is not None and market_value > 0):
            count += 1
    return count


def audit_position_sources(root: Path, snapshot_date: str) -> Tuple[List[Dict[str, str]], Dict[str, Dict[str, str]]]:
    audit_rows: List[Dict[str, str]] = []
    context: Dict[str, Dict[str, str]] = {}
    for path in discover_inputs(root):
        rows, fields, parse_status = read_csv(path) if path.suffix.lower() == ".csv" else ([], [], "SKIPPED_NON_CSV")
        position_like = is_position_like(path, rows, fields) if parse_status == "OK" else False
        open_count = open_position_count(rows, fields) if position_like else 0
        ticker_col = pick_col(fields, ["ticker", "symbol"]) if fields else None
        entry_date_col = pick_col(fields, ["opened_at", "entry_date", "open_date", "created_at"]) if fields else None
        reason_col = pick_col(fields, ["original_buy_reason", "buy_reason", "reason", "source_row_text", "technical_tags", "candidate_bucket"]) if fields else None
        if ticker_col:
            for row in rows:
                ticker = str(row.get(ticker_col, "")).strip().upper()
                if ticker and ticker not in context:
                    context[ticker] = {
                        "entry_date": normalize_date(row.get(entry_date_col or "")),
                        "original_buy_reason": str(row.get(reason_col or "", "")).strip()[:300],
                        "source_file": str(path),
                        "raw_blob": row_blob(row),
                    }
        audit_rows.append(
            {
                "snapshot_date": snapshot_date,
                "search_root": str(path.parent),
                "source_file": str(path),
                "exists": "YES",
                "file_type": path.suffix.lower().lstrip("."),
                "row_count": str(len(rows)),
                "column_count": str(len(fields)),
                "parse_status": parse_status,
                "position_like": "YES" if position_like else "NO",
                "open_position_count": str(open_count),
                "used_for_lifecycle_context": "YES" if ticker_col else "NO",
                "note": "POSITION_LIFECYCLE_DISCOVERY",
            }
        )
    return audit_rows, context


def normalize_date(value: object) -> str:
    s = str(value or "").strip()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:19], fmt).date().isoformat()
        except Exception:
            continue
    return s[:10]


def infer_holding_days(row: Dict[str, str], entry_date: str) -> str:
    existing = str(row.get("holding_days", "")).strip()
    if existing:
        return existing
    if not entry_date:
        return ""
    try:
        opened = datetime.strptime(entry_date[:10], "%Y-%m-%d").date()
        return str((date.today() - opened).days)
    except Exception:
        return ""


def lifecycle_stage(holding_days: Optional[int]) -> str:
    if holding_days is None:
        return "UNKNOWN"
    if holding_days <= 3:
        return "NEW_POSITION"
    if holding_days <= 20:
        return "EARLY_HOLD"
    if holding_days <= 60:
        return "TREND_HOLD"
    return "MATURE_POSITION"


def technical_risk_high(row: Dict[str, str]) -> bool:
    action = str(row.get("technical_exit_action", "")).upper()
    combined = str(row.get("combined_shadow_exit_action", row.get("shadow_exit_action", ""))).upper()
    labels = str(row.get("technical_labels_found", "")).upper()
    risk_terms = ["EXHAUSTION_RISK", "OLD_OVERHEAT", "OVERHEAT_UNCLASSIFIED", "RV_SPIKE", "OPEX_PRESSURE", "VWAP_PROXY_DEVIATION"]
    return action in {"TRIM_REVIEW", "EXIT_REVIEW", "STOP_LOSS_REVIEW"} or combined in {"TRIM_REVIEW", "EXIT_REVIEW", "STOP_LOSS_REVIEW"} or any(term in labels for term in risk_terms)


def current_buy_reason_valid(row: Dict[str, str], ctx: Dict[str, str]) -> str:
    labels = str(row.get("technical_labels_found", "")).upper()
    combined = str(row.get("combined_shadow_exit_action", row.get("shadow_exit_action", ""))).upper()
    blob = str(ctx.get("raw_blob", "")).upper()
    if combined in {"EXIT_REVIEW", "STOP_LOSS_REVIEW"}:
        return "NO"
    if "BREAKOUT_CONTINUATION" in labels or "PULLBACK_WATCH" in labels or "WATCH_POSITIVE" in blob:
        return "YES"
    if technical_risk_high(row):
        return "REVIEW"
    return "UNKNOWN"


def evaluate_lifecycle(row: Dict[str, str], stage: str) -> Tuple[str, str, int]:
    if row.get("combined_shadow_exit_action") == "NO_POSITION" or row.get("position_status") == "NO_OPEN_POSITION":
        return "NO_POSITION", "NO_OPEN_POSITIONS_FOUND", 0

    combined = row.get("combined_shadow_exit_action") or row.get("shadow_exit_action") or "HOLD"
    technical = row.get("technical_exit_action") or ""
    unrealized = as_float(row.get("unrealized_return_pct"))
    max_return = as_float(row.get("max_return_since_entry_pct"))
    drawdown = as_float(row.get("drawdown_from_peak_pct"))
    action = "HOLD"
    reasons: List[str] = []
    score = 0
    high_risk = technical_risk_high(row)

    if stage == "UNKNOWN":
        if combined in {"TRIM_REVIEW", "TAKE_PROFIT_REVIEW", "STOP_LOSS_REVIEW", "EXIT_REVIEW"}:
            action = stronger(action, combined)
            reasons.append("existing shadow action retained with unknown holding age")
            score += 10
        else:
            reasons.append("holding age unknown")
    elif stage == "NEW_POSITION":
        if combined in {"STOP_LOSS_REVIEW", "EXIT_REVIEW"}:
            action = stronger(action, combined)
            reasons.append("new position but severe existing risk retained")
            score += 35
        elif high_risk or technical in {"WATCH_EXIT", "TRIM_REVIEW"}:
            action = stronger(action, "WATCH_EXIT")
            reasons.append("new position technical risk watch")
            score += 10
        else:
            reasons.append("new position protected from aggressive lifecycle exit")
    elif stage == "EARLY_HOLD":
        if unrealized is not None and unrealized <= -10:
            action = stronger(action, "STOP_LOSS_REVIEW")
            reasons.append("early hold hard loss review")
            score += 45
        elif unrealized is not None and unrealized <= -6:
            action = stronger(action, "WATCH_EXIT")
            reasons.append("early hold soft loss watch")
            score += 20
        if high_risk:
            action = stronger(action, "TRIM_REVIEW")
            reasons.append("early hold high technical risk")
            score += 25
    elif stage == "TREND_HOLD":
        if max_return is not None and drawdown is not None and max_return >= 15 and drawdown <= -6:
            action = stronger(action, "TRIM_REVIEW")
            reasons.append("trend hold trailing profit protection")
            score += 30
        if ACTION_PRIORITY.get(combined, 0) >= ACTION_PRIORITY["TRIM_REVIEW"]:
            action = stronger(action, combined)
            reasons.append("existing combined shadow review retained")
            score += 20
    elif stage == "MATURE_POSITION":
        if high_risk:
            action = stronger(action, "TRIM_REVIEW")
            reasons.append("mature position high technical risk")
            score += 30
        if max_return is not None and drawdown is not None and max_return >= 15 and drawdown <= -10:
            action = stronger(action, "EXIT_REVIEW")
            reasons.append("mature position large profit drawdown review")
            score += 45
        if ACTION_PRIORITY.get(combined, 0) >= ACTION_PRIORITY["TRIM_REVIEW"]:
            action = stronger(action, combined)
            reasons.append("existing combined shadow review retained")
            score += 15

    if not reasons:
        reasons.append("no lifecycle exit signal")
    return action, "; ".join(reasons), score


def no_position_row(snapshot_date: str) -> Dict[str, str]:
    row = {field: "" for field in OUTPUT_FIELDS}
    row.update(
        {
            "snapshot_date": snapshot_date,
            "position_status": "NO_OPEN_POSITION",
            "lifecycle_stage": "UNKNOWN",
            "current_buy_reason_still_valid": "UNKNOWN",
            "technical_exit_action": "NO_POSITION",
            "combined_shadow_exit_action": "NO_POSITION",
            "lifecycle_exit_score": "0",
            "lifecycle_exit_action": "NO_POSITION",
            "lifecycle_exit_reason": "NO_OPEN_POSITIONS_FOUND",
            "final_shadow_exit_action": "NO_POSITION",
            "final_shadow_exit_reason": "NO_OPEN_POSITIONS_FOUND",
            "official_decision_impact": OFFICIAL_DECISION_IMPACT,
            "auto_sell": AUTO_SELL,
            "auto_trade": AUTO_TRADE,
        }
    )
    return row


def load_sell_timing_rows(root: Path) -> Tuple[List[Dict[str, str]], str]:
    candidates = [
        root / "outputs/v18/sell_timing/V18_12B_CURRENT_SELL_TIMING_TECHNICAL_LABEL.csv",
        root / "outputs/v18/sell_timing/V18_12A_CURRENT_SELL_TIMING_SHADOW.csv",
    ]
    for path in candidates:
        rows, _, status = read_csv(path)
        if status == "OK" and rows:
            return rows, str(path)
    return [], str(candidates[-1])


def build_lifecycle_rows(base_rows: List[Dict[str, str]], context: Dict[str, Dict[str, str]], snapshot_date: str) -> List[Dict[str, str]]:
    if not base_rows:
        return [no_position_row(snapshot_date)]
    out: List[Dict[str, str]] = []
    for base in base_rows:
        if base.get("combined_shadow_exit_action") == "NO_POSITION" or base.get("shadow_exit_action") == "NO_POSITION" or base.get("position_status") == "NO_OPEN_POSITION":
            out.append(no_position_row(snapshot_date))
            continue
        ticker = str(base.get("ticker", "")).strip().upper()
        ctx = context.get(ticker, {})
        entry_date = normalize_date(ctx.get("entry_date", ""))
        holding_days = infer_holding_days(base, entry_date)
        stage = lifecycle_stage(as_int(holding_days))
        technical_action = base.get("technical_exit_action") or base.get("technical_exit_signal") or "HOLD"
        combined_action = base.get("combined_shadow_exit_action") or base.get("shadow_exit_action") or "HOLD"
        lifecycle_action, lifecycle_reason, lifecycle_score = evaluate_lifecycle({**base, "technical_exit_action": technical_action, "combined_shadow_exit_action": combined_action}, stage)
        final_action = stronger(combined_action, lifecycle_action)
        row = {
            "snapshot_date": snapshot_date,
            "ticker": ticker,
            "source_file": base.get("source_file") or ctx.get("source_file", ""),
            "position_status": base.get("position_status", ""),
            "shares": base.get("shares", ""),
            "entry_date": entry_date,
            "entry_price": base.get("entry_price", ""),
            "current_price": base.get("current_price", ""),
            "cost_basis": base.get("cost_basis", ""),
            "market_value": base.get("market_value", ""),
            "unrealized_return_pct": base.get("unrealized_return_pct", ""),
            "max_return_since_entry_pct": base.get("max_return_since_entry_pct", ""),
            "drawdown_from_peak_pct": base.get("drawdown_from_peak_pct", ""),
            "holding_days": holding_days,
            "lifecycle_stage": stage,
            "original_buy_reason": ctx.get("original_buy_reason", ""),
            "current_buy_reason_still_valid": current_buy_reason_valid(base, ctx),
            "technical_exit_action": technical_action,
            "combined_shadow_exit_action": combined_action,
            "lifecycle_exit_score": str(lifecycle_score),
            "lifecycle_exit_action": lifecycle_action,
            "lifecycle_exit_reason": lifecycle_reason,
            "final_shadow_exit_action": final_action,
            "final_shadow_exit_reason": f"combined={combined_action}; lifecycle={lifecycle_action}; {lifecycle_reason}",
            "official_decision_impact": OFFICIAL_DECISION_IMPACT,
            "auto_sell": AUTO_SELL,
            "auto_trade": AUTO_TRADE,
        }
        out.append(row)
    return out or [no_position_row(snapshot_date)]


def make_report(
    report_path: Path,
    csv_path: Path,
    audit_path: Path,
    input_path: str,
    rows: List[Dict[str, str]],
    audit_rows: List[Dict[str, str]],
    position_count: int,
    actionable_count: int,
    stage_count: int,
) -> str:
    stage_counts = Counter(row.get("lifecycle_stage", "UNKNOWN") for row in rows)
    action_counts = Counter(row.get("final_shadow_exit_action", "UNKNOWN") for row in rows)
    top_rows = [r for r in rows if r.get("final_shadow_exit_action") not in {"HOLD", "NO_POSITION"}]
    top_rows.sort(key=lambda r: as_float(r.get("lifecycle_exit_score")) or 0.0, reverse=True)
    position_sources = [r for r in audit_rows if r.get("position_like") == "YES"]

    lines = [
        "# V18.12C Position Lifecycle Review",
        "",
        "## Status",
        "",
        f"- STATUS: {STATUS_OK}",
        f"- MODE: {MODE}",
        f"- POSITION_COUNT: {position_count}",
        f"- ACTIONABLE_EXIT_COUNT: {actionable_count}",
        f"- LIFECYCLE_STAGE_COUNT: {stage_count}",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "",
        "## Safety Guardrails",
        "",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "- SHADOW_ONLY: lifecycle review creates review context only.",
        "- This is not a sell order and does not affect official decisions, official daily scripts, trading logic, or factor weights.",
        "",
        "## Input Source Summary",
        "",
        f"- SELL_TIMING_INPUT: {input_path}",
        f"- POSITION_LIKE_SOURCE_COUNT: {len(position_sources)}",
        f"- INPUT_AUDIT: {audit_path}",
        "",
        "## Position Lifecycle Summary",
        "",
        f"- POSITION_COUNT: {position_count}",
        f"- OUTPUT_CSV: {csv_path}",
        "",
        "## Lifecycle Stage Counts",
        "",
    ]
    for stage in ["UNKNOWN", "NEW_POSITION", "EARLY_HOLD", "TREND_HOLD", "MATURE_POSITION"]:
        lines.append(f"- {stage}: {stage_counts.get(stage, 0)}")
    lines.extend(["", "## Final Shadow Exit Action Counts", ""])
    for action in ["EXIT_REVIEW", "STOP_LOSS_REVIEW", "TAKE_PROFIT_REVIEW", "TRIM_REVIEW", "WATCH_EXIT", "HOLD", "NO_POSITION"]:
        lines.append(f"- {action}: {action_counts.get(action, 0)}")
    lines.extend(["", "## Top Lifecycle Review Rows", ""])
    if top_rows:
        lines.append("| ticker | stage | final_action | score | reason |")
        lines.append("|---|---|---:|---:|---|")
        for row in top_rows[:15]:
            lines.append(f"| {row.get('ticker', '')} | {row.get('lifecycle_stage', '')} | {row.get('final_shadow_exit_action', '')} | {row.get('lifecycle_exit_score', '')} | {row.get('final_shadow_exit_reason', '')} |")
    else:
        lines.append("No actionable lifecycle review rows.")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- V18.12C is additive to V18.12A and V18.12B.",
            "- Final action uses the stronger of combined sell timing action and lifecycle review action.",
            "- Immediate sell action vocabulary is intentionally excluded.",
            "- Outputs are review-only shadow artifacts.",
            f"- REPORT: {report_path}",
        ]
    )
    return "\n".join(lines) + "\n"


def make_read_first(position_count: int, actionable_count: int, stage_count: int, report_path: Path, csv_path: Path, audit_path: Path) -> str:
    return "\n".join(
        [
            "V18.12C POSITION LIFECYCLE REVIEW READ FIRST",
            "",
            "STATUS:",
            STATUS_OK,
            "",
            "POSITION_COUNT:",
            str(position_count),
            "",
            "ACTIONABLE_EXIT_COUNT:",
            str(actionable_count),
            "",
            "LIFECYCLE_STAGE_COUNT:",
            str(stage_count),
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
    report_path = out_dir / "V18_12C_CURRENT_POSITION_LIFECYCLE_REVIEW_REPORT.md"
    csv_path = out_dir / "V18_12C_CURRENT_POSITION_LIFECYCLE_REVIEW.csv"
    audit_path = out_dir / "V18_12C_CURRENT_POSITION_LIFECYCLE_INPUT_AUDIT.csv"
    read_first_path = out_dir / "V18_12C_READ_FIRST.txt"

    base_rows, input_path = load_sell_timing_rows(root)
    audit_rows, context = audit_position_sources(root, snapshot_date)
    output_rows = build_lifecycle_rows(base_rows, context, snapshot_date)
    position_count = sum(1 for row in output_rows if row.get("final_shadow_exit_action") != "NO_POSITION")
    actionable_count = sum(1 for row in output_rows if row.get("final_shadow_exit_action") not in {"HOLD", "NO_POSITION"})
    if position_count == 0:
        actionable_count = 0
        output_rows = [no_position_row(snapshot_date)]
    stage_count = len({row.get("lifecycle_stage", "UNKNOWN") for row in output_rows})

    write_csv(csv_path, output_rows, OUTPUT_FIELDS)
    write_csv(audit_path, audit_rows, AUDIT_FIELDS)
    write_text(report_path, make_report(report_path, csv_path, audit_path, input_path, output_rows, audit_rows, position_count, actionable_count, stage_count))
    write_text(read_first_path, make_read_first(position_count, actionable_count, stage_count, report_path, csv_path, audit_path))

    return {
        "STATUS": STATUS_OK,
        "POSITION_COUNT": str(position_count),
        "ACTIONABLE_EXIT_COUNT": str(actionable_count),
        "LIFECYCLE_STAGE_COUNT": str(stage_count),
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_SELL": AUTO_SELL,
        "AUTO_TRADE": AUTO_TRADE,
        "REPORT": str(report_path),
        "CSV": str(csv_path),
        "INPUT_AUDIT": str(audit_path),
        "READ_FIRST": str(read_first_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.12C position lifecycle review.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    result = generate(Path(args.root))
    for key in ["STATUS", "POSITION_COUNT", "ACTIONABLE_EXIT_COUNT", "LIFECYCLE_STAGE_COUNT", "OFFICIAL_DECISION_IMPACT", "AUTO_SELL", "AUTO_TRADE", "REPORT", "CSV", "INPUT_AUDIT", "READ_FIRST"]:
        print(f"{key}: {result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
