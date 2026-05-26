from __future__ import annotations

"""V18.12A Sell Timing Shadow Engine.

Purpose:
    Build a transparent CSV/Markdown review layer for position exit timing.
    The engine reads current position-like files, evaluates simple review
    signals, and writes shadow-only artifacts for human inspection.

Safety:
    This module does not sell, trade, promote factors, change weights, or
    modify official daily decision scripts. OFFICIAL_DECISION_IMPACT is always
    NONE, while AUTO_SELL and AUTO_TRADE are always DISABLED.
"""

import argparse
import csv
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
STATUS_OK = "OK_SELL_TIMING_SHADOW_READY"

# Hard guardrails for this shadow layer. These constants are written into every
# output row and status artifact so the output cannot be mistaken for an order.
MODE = "SHADOW_ONLY"
OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_SELL = "DISABLED"
AUTO_TRADE = "DISABLED"

# Review-only action vocabulary. V18.12A intentionally never emits SELL_NOW.
OUTPUT_FIELDS = [
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

AUDIT_FIELDS = [
    "snapshot_date",
    "search_root",
    "source_file",
    "candidate_reason",
    "exists",
    "file_type",
    "row_count",
    "column_count",
    "parse_status",
    "position_like",
    "open_position_count",
    "selected_for_positions",
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

# Input discovery is intentionally broad and read-only. The audit output records
# what was found or missing; missing files are normal and do not fail the run.
POSITION_NAME_TERMS = [
    "positions",
    "current_positions",
    "paper_positions",
    "latest_paper_positions",
]

DISCOVERY_TERMS = [
    "positions",
    "current_positions",
    "paper_positions",
    "latest_paper_positions",
    "account",
    "paper_pnl",
    "sim_cabin",
    "candidate_tracker",
]

OPEN_STATUS_BLOCK_TERMS = {"CLOSED", "SOLD", "EXITED", "FLAT", "NO_POSITION"}


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


def fmt_num(value: Optional[float], digits: int = 4) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def pick_col(fields: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    field_list = list(fields)
    exact = {f.lower(): f for f in field_list}
    for cand in candidates:
        if cand.lower() in exact:
            return exact[cand.lower()]
    for f in field_list:
        fl = f.lower()
        for cand in candidates:
            if cand.lower() in fl:
                return f
    return None


def row_blob(row: Dict[str, str]) -> str:
    return " ".join(str(v) for v in row.values() if v is not None).upper()


def candidate_reason(path: Path) -> str:
    name = path.name.lower()
    hits = [term for term in DISCOVERY_TERMS if term in name]
    return "|".join(hits) if hits else "DISCOVERED"


def discover_inputs(root: Path) -> List[Path]:
    """Find likely position, account, PnL, cabin, and tracker files.

    Discovery searches the current V18 state/output areas and records likely
    inputs for the audit CSV. It does not mutate any discovered source.
    """
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


def source_rank(path: Path) -> Tuple[int, str]:
    """Prefer real/simulation current position files over tracker-like inputs."""
    s = str(path).replace("\\", "/").lower()
    name = path.name.lower()
    if "state/v18/simulation" in s and "positions" in name:
        return (0, s)
    if "outputs/v18/simulation" in s and "positions" in name:
        return (1, s)
    if "state/v18" in s and "positions" in name:
        return (2, s)
    if "outputs/v18" in s and "positions" in name:
        return (3, s)
    return (9, s)


def is_position_like(path: Path, rows: List[Dict[str, str]], fields: List[str]) -> bool:
    """Classify files that can plausibly contain open positions."""
    name = path.name.lower()
    if any(term in name for term in POSITION_NAME_TERMS):
        return True
    ticker_col = pick_col(fields, ["ticker", "symbol"])
    qty_col = pick_col(fields, ["quantity", "shares", "share_count", "position_qty", "position_size"])
    entry_col = pick_col(fields, ["avg_cost_usd", "avg_cost", "entry_price", "cost_basis_price"])
    return bool(ticker_col and (qty_col or entry_col) and rows)


def open_position_count(rows: List[Dict[str, str]], fields: List[str]) -> int:
    """Count open positions without treating closed, sold, or flat rows as open."""
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


def load_technical_map(root: Path) -> Dict[str, str]:
    """Load optional technical labels used only as shadow exit context."""
    paths = [
        root / "state/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv",
    ]
    out: Dict[str, str] = {}
    for path in paths:
        rows, fields, status = read_csv(path)
        if status != "OK":
            continue
        ticker_col = pick_col(fields, ["ticker", "symbol"])
        if not ticker_col:
            continue
        for row in rows:
            ticker = str(row.get(ticker_col, "")).strip().upper()
            if ticker and ticker not in out:
                out[ticker] = row_blob(row)
    return out


def parse_open_positions(path: Path, rows: List[Dict[str, str]], fields: List[str]) -> List[Dict[str, object]]:
    """Normalize open position rows into the fields expected by the review CSV."""
    ticker_col = pick_col(fields, ["ticker", "symbol"])
    qty_col = pick_col(fields, ["quantity", "shares", "share_count", "position_qty", "position_size"])
    entry_col = pick_col(fields, ["avg_cost_usd", "avg_cost", "entry_price", "cost_basis_price", "cost_price"])
    current_col = pick_col(fields, ["last_price_usd", "current_price", "latest_price_usd", "last_price", "price"])
    cost_col = pick_col(fields, ["cost_basis", "cost_basis_usd", "book_value", "total_cost"])
    market_col = pick_col(fields, ["market_value_usd", "market_value"])
    ret_col = pick_col(fields, ["unrealized_return_pct", "return_pct", "pnl_pct"])
    max_ret_col = pick_col(fields, ["max_return_since_entry_pct", "peak_return_pct", "max_unrealized_return_pct"])
    drawdown_col = pick_col(fields, ["drawdown_from_peak_pct", "peak_drawdown_pct"])
    status_col = pick_col(fields, ["position_status", "status", "state"])
    opened_col = pick_col(fields, ["opened_at", "entry_date", "open_date", "created_at"])

    out: List[Dict[str, object]] = []
    for row in rows:
        ticker = str(row.get(ticker_col or "", "")).strip().upper()
        if not ticker:
            continue
        status = str(row.get(status_col or "", "")).strip().upper()
        if status and any(term in status for term in OPEN_STATUS_BLOCK_TERMS):
            continue

        shares = as_float(row.get(qty_col or ""))
        entry_price = as_float(row.get(entry_col or ""))
        current_price = as_float(row.get(current_col or ""))
        cost_basis = as_float(row.get(cost_col or ""))
        market_value = as_float(row.get(market_col or ""))
        unrealized_return = as_float(row.get(ret_col or ""))
        max_return = as_float(row.get(max_ret_col or ""))
        drawdown = as_float(row.get(drawdown_col or ""))

        if shares is None and market_value is not None and market_value > 0:
            status = status or "OPEN_UNKNOWN_SIZE"
        elif shares is None or shares <= 0:
            continue
        else:
            status = status or "OPEN"

        if cost_basis is None and shares is not None and entry_price is not None:
            cost_basis = shares * entry_price
        if market_value is None and shares is not None and current_price is not None:
            market_value = shares * current_price
        if unrealized_return is None and entry_price and current_price:
            unrealized_return = (current_price / entry_price - 1.0) * 100.0
        if drawdown is None and max_return is not None and unrealized_return is not None:
            drawdown = unrealized_return - max_return

        holding_days = compute_holding_days(row.get(opened_col or ""))

        out.append(
            {
                "ticker": ticker,
                "source_file": str(path),
                "position_status": status,
                "shares": shares,
                "entry_price": entry_price,
                "current_price": current_price,
                "cost_basis": cost_basis,
                "market_value": market_value,
                "unrealized_return_pct": unrealized_return,
                "max_return_since_entry_pct": max_return,
                "drawdown_from_peak_pct": drawdown,
                "holding_days": holding_days,
                "raw_blob": row_blob(row),
            }
        )
    return out


def compute_holding_days(value: object) -> str:
    s = str(value or "").strip()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            opened = datetime.strptime(s[:19], fmt).date()
            return str((date.today() - opened).days)
        except Exception:
            continue
    return ""


def stronger(current: str, candidate: str) -> str:
    return candidate if ACTION_PRIORITY[candidate] > ACTION_PRIORITY[current] else current


def evaluate_position(pos: Dict[str, object], technical_blob: str, snapshot_date: str) -> Dict[str, str]:
    """Apply simple transparent exit-review rules to one open position.

    The result is a review action only. It never places an order and always
    preserves OFFICIAL_DECISION_IMPACT/NONE and AUTO_* disabled guardrails.
    """
    unrealized = pos.get("unrealized_return_pct")
    max_return = pos.get("max_return_since_entry_pct")
    drawdown = pos.get("drawdown_from_peak_pct")
    action = "HOLD"
    reasons: List[str] = []
    score = 0

    stop_loss_signal = ""
    take_profit_signal = ""
    trailing_stop_signal = ""
    overheat_exit_signal = ""
    event_exit_signal = ""
    technical_exit_signal = "NONE"

    if isinstance(unrealized, float):
        if unrealized <= -10:
            stop_loss_signal = "HARD_STOP_LOSS_REVIEW"
            action = stronger(action, "STOP_LOSS_REVIEW")
            reasons.append(stop_loss_signal)
            score += 50
        elif unrealized <= -6:
            stop_loss_signal = "SOFT_STOP_LOSS_REVIEW"
            action = stronger(action, "WATCH_EXIT")
            reasons.append(stop_loss_signal)
            score += 20

        if unrealized >= 20:
            take_profit_signal = "TAKE_PROFIT_REVIEW"
            action = stronger(action, "TAKE_PROFIT_REVIEW")
            reasons.append(take_profit_signal)
            score += 35
        elif unrealized >= 12:
            take_profit_signal = "PARTIAL_TRIM_REVIEW"
            action = stronger(action, "TRIM_REVIEW")
            reasons.append(take_profit_signal)
            score += 25

    if isinstance(max_return, float) and isinstance(drawdown, float):
        if max_return >= 15 and drawdown <= -6:
            trailing_stop_signal = "TRAILING_PROFIT_PROTECTION_REVIEW"
            trail_action = "EXIT_REVIEW" if drawdown <= -10 else "TRIM_REVIEW"
            action = stronger(action, trail_action)
            reasons.append(trailing_stop_signal)
            score += 30 if trail_action == "TRIM_REVIEW" else 45

    if any(label in technical_blob for label in ("EXHAUSTION_RISK", "OLD_OVERHEAT")):
        overheat_exit_signal = "OVERHEAT_TRIM_REVIEW"
        technical_exit_signal = "TECHNICAL_OVERHEAT_REVIEW"
        action = stronger(action, "TRIM_REVIEW")
        reasons.append(overheat_exit_signal)
        score += 25
    elif any(label in technical_blob for label in ("OVERHEAT_UNCLASSIFIED", "BB_ABOVE_UPPER", "RSI_OVERHEAT", "KDJ_OVERHEAT")):
        technical_exit_signal = "TECHNICAL_WATCH"
        score += 5

    return {
        "snapshot_date": snapshot_date,
        "ticker": str(pos.get("ticker", "")),
        "source_file": str(pos.get("source_file", "")),
        "position_status": str(pos.get("position_status", "")),
        "shares": fmt_num(pos.get("shares") if isinstance(pos.get("shares"), float) else None),
        "entry_price": fmt_num(pos.get("entry_price") if isinstance(pos.get("entry_price"), float) else None),
        "current_price": fmt_num(pos.get("current_price") if isinstance(pos.get("current_price"), float) else None),
        "cost_basis": fmt_num(pos.get("cost_basis") if isinstance(pos.get("cost_basis"), float) else None),
        "market_value": fmt_num(pos.get("market_value") if isinstance(pos.get("market_value"), float) else None),
        "unrealized_return_pct": fmt_num(unrealized if isinstance(unrealized, float) else None),
        "max_return_since_entry_pct": fmt_num(max_return if isinstance(max_return, float) else None),
        "drawdown_from_peak_pct": fmt_num(drawdown if isinstance(drawdown, float) else None),
        "holding_days": str(pos.get("holding_days", "")),
        "technical_exit_signal": technical_exit_signal,
        "stop_loss_signal": stop_loss_signal,
        "take_profit_signal": take_profit_signal,
        "trailing_stop_signal": trailing_stop_signal,
        "event_exit_signal": event_exit_signal,
        "overheat_exit_signal": overheat_exit_signal,
        "exit_score": str(score),
        "shadow_exit_action": action,
        "shadow_exit_reason": "; ".join(reasons) if reasons else "NO_EXIT_SIGNAL",
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_sell": AUTO_SELL,
        "auto_trade": AUTO_TRADE,
    }


def no_position_row(snapshot_date: str) -> Dict[str, str]:
    """Emit a successful no-position row when no open positions are available."""
    row = {field: "" for field in OUTPUT_FIELDS}
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


def make_report(
    report_path: Path,
    csv_path: Path,
    audit_path: Path,
    snapshot_date: str,
    status: str,
    audit_rows: List[Dict[str, str]],
    output_rows: List[Dict[str, str]],
    position_count: int,
    actionable_count: int,
) -> str:
    action_counts = Counter(row.get("shadow_exit_action", "UNKNOWN") for row in output_rows)
    available = [r for r in audit_rows if r.get("exists") == "YES"]
    selected = [r for r in audit_rows if r.get("selected_for_positions") == "YES"]
    top_rows = [
        r
        for r in output_rows
        if r.get("shadow_exit_action") not in {"HOLD", "NO_POSITION"}
    ]
    top_rows.sort(key=lambda r: as_float(r.get("exit_score")) or 0.0, reverse=True)

    lines = [
        "# V18.12A Sell Timing Shadow Engine",
        "",
        "## Status",
        "",
        f"- STATUS: {status}",
        f"- SNAPSHOT_DATE: {snapshot_date}",
        f"- MODE: {MODE}",
        f"- POSITION_COUNT: {position_count}",
        f"- ACTIONABLE_EXIT_COUNT: {actionable_count}",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "",
        "## Purpose",
        "",
        "- V18.12A is a shadow-only sell/trim/hold review layer for current positions.",
        "- It is designed to make exit timing inputs visible without changing official decisions.",
        "- The logic is intentionally simple, transparent, and CSV/Markdown based.",
        "",
        "## Safety Guardrails",
        "",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        "- This is shadow-only review output. It is not a sell order and does not modify official daily decisions.",
        "- Official daily runners and pointers are not modified by this module.",
        "",
        "## Input Discovery",
        "",
        "- Search roots: state/v18/simulation, outputs/v18/simulation, state/v18, outputs/v18.",
        "- Candidate names include positions, current_positions, paper_positions, account, paper_pnl, sim_cabin, and candidate_tracker.",
        "- Position-like sources are audited first, then the highest-priority open-position source is selected for review.",
        "- Missing or non-position files are recorded in the audit CSV and do not fail the shadow run.",
        "",
        "## No-Position Behavior",
        "",
        "- If no open positions are found, the run still exits OK with POSITION_COUNT 0.",
        "- The shadow CSV contains a NO_POSITION row and ACTIONABLE_EXIT_COUNT remains 0.",
        "",
        "## Action Vocabulary",
        "",
        "- HOLD: no current exit review signal.",
        "- WATCH_EXIT: soft risk review.",
        "- TRIM_REVIEW: partial trim review candidate.",
        "- TAKE_PROFIT_REVIEW: profit-taking review candidate.",
        "- STOP_LOSS_REVIEW: stop-loss review candidate.",
        "- EXIT_REVIEW: highest-severity shadow exit review.",
        "- NO_POSITION: no open position was available for review.",
        "- SELL_NOW is intentionally not part of V18.12A output vocabulary.",
        "",
        "## Output Files",
        "",
        f"- REPORT: {report_path}",
        f"- CSV: {csv_path}",
        f"- INPUT_AUDIT: {audit_path}",
        "",
        "## Input Source Summary",
        "",
        f"- AVAILABLE_SOURCE_COUNT: {len(available)}",
        f"- SELECTED_POSITION_SOURCE_COUNT: {len(selected)}",
    ]
    if selected:
        for row in selected[:10]:
            lines.append(f"- SELECTED: {row.get('source_file')} (open_positions={row.get('open_position_count')})")
    else:
        lines.append("- SELECTED: NONE")

    lines.extend(
        [
            "",
            "## Position Summary",
            "",
            f"- POSITION_COUNT: {position_count}",
            f"- OUTPUT_CSV: {csv_path}",
            f"- INPUT_AUDIT_CSV: {audit_path}",
            "",
            "## Exit Action Counts",
            "",
        ]
    )
    for action in ["EXIT_REVIEW", "STOP_LOSS_REVIEW", "TAKE_PROFIT_REVIEW", "TRIM_REVIEW", "WATCH_EXIT", "HOLD", "NO_POSITION"]:
        lines.append(f"- {action}: {action_counts.get(action, 0)}")

    lines.extend(["", "## Top Exit Review Rows", ""])
    if top_rows:
        lines.append("| ticker | action | score | unrealized_return_pct | reason |")
        lines.append("|---|---:|---:|---:|---|")
        for row in top_rows[:15]:
            lines.append(
                f"| {row.get('ticker', '')} | {row.get('shadow_exit_action', '')} | {row.get('exit_score', '')} | "
                f"{row.get('unrealized_return_pct', '')} | {row.get('shadow_exit_reason', '')} |"
            )
    else:
        lines.append("No actionable exit review rows.")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- V18.12A only creates CSV/MD review artifacts for sell, trim, watch, and hold review.",
            "- It does not output SELL_NOW.",
            "- It does not auto-sell, auto-trade, auto-promote, change weights, or modify official daily decision files.",
            "- All rows keep OFFICIAL_DECISION_IMPACT as NONE, AUTO_SELL as DISABLED, and AUTO_TRADE as DISABLED.",
            f"- REPORT: {report_path}",
        ]
    )
    return "\n".join(lines) + "\n"


def make_read_first(
    status: str,
    position_count: int,
    actionable_count: int,
    report_path: Path,
    csv_path: Path,
    audit_path: Path,
) -> str:
    return "\n".join(
        [
            "V18.12A SELL TIMING SHADOW READ FIRST",
            "",
            "PURPOSE:",
            "Shadow-only position exit timing review. Produces sell/trim/hold review artifacts; does not place orders.",
            "",
            "SAFETY_GUARDRAILS:",
            "OFFICIAL_DECISION_IMPACT remains NONE; AUTO_SELL and AUTO_TRADE remain DISABLED.",
            "",
            "INPUT_DISCOVERY:",
            "Reads likely position/account/PnL/candidate tracker files under state/v18 and outputs/v18; missing files are audited, not fatal.",
            "",
            "NO_POSITION_BEHAVIOR:",
            "If no open positions exist, run still exits OK with POSITION_COUNT 0 and shadow action NO_POSITION.",
            "",
            "ACTION_VOCABULARY:",
            "HOLD, WATCH_EXIT, TRIM_REVIEW, TAKE_PROFIT_REVIEW, STOP_LOSS_REVIEW, EXIT_REVIEW, NO_POSITION. SELL_NOW is not emitted.",
            "",
            "OUTPUT_FILES:",
            "Report, shadow CSV, input audit CSV, and this READ_FIRST file under outputs/v18/sell_timing.",
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
    """Generate V18.12A shadow outputs.

    The current outputs intentionally overwrite prior current files, matching
    the V18 current-output convention. Source position/tracker files and
    official daily scripts are read-only from this module's perspective.
    """
    snapshot_date = date.today().isoformat()
    out_dir = root / "outputs/v18/sell_timing"
    report_path = out_dir / "V18_12A_CURRENT_SELL_TIMING_SHADOW_REPORT.md"
    csv_path = out_dir / "V18_12A_CURRENT_SELL_TIMING_SHADOW.csv"
    audit_path = out_dir / "V18_12A_CURRENT_SELL_TIMING_INPUT_AUDIT.csv"
    read_first_path = out_dir / "V18_12A_READ_FIRST.txt"

    discovered = discover_inputs(root)
    audit_rows: List[Dict[str, str]] = []
    parsed_sources = []

    for path in discovered:
        rows, fields, parse_status = read_csv(path) if path.suffix.lower() == ".csv" else ([], [], "SKIPPED_NON_CSV")
        position_like = is_position_like(path, rows, fields) if parse_status == "OK" else False
        open_count = open_position_count(rows, fields) if position_like else 0
        parsed_sources.append((path, rows, fields, position_like, open_count))
        audit_rows.append(
            {
                "snapshot_date": snapshot_date,
                "search_root": str(path.parent),
                "source_file": str(path),
                "candidate_reason": candidate_reason(path),
                "exists": "YES",
                "file_type": path.suffix.lower().lstrip("."),
                "row_count": str(len(rows)),
                "column_count": str(len(fields)),
                "parse_status": parse_status,
                "position_like": "YES" if position_like else "NO",
                "open_position_count": str(open_count),
                "selected_for_positions": "NO",
                "note": "CURRENT_DISCOVERED_INPUT",
            }
        )

    search_roots = [
        root / "state/v18/simulation",
        root / "outputs/v18/simulation",
        root / "state/v18",
        root / "outputs/v18",
    ]
    existing_names = {p.name.lower() for p in discovered}
    for base in search_roots:
        for expected in ["V18_CURRENT_PAPER_POSITIONS.csv", "V18_CURRENT_SIM_CANDIDATE_TRACKER.csv", "V18_CURRENT_SIM_ACCOUNT.csv"]:
            if expected.lower() in existing_names:
                continue
            audit_rows.append(
                {
                    "snapshot_date": snapshot_date,
                    "search_root": str(base),
                    "source_file": str(base / expected),
                    "candidate_reason": candidate_reason(base / expected),
                    "exists": "NO",
                    "file_type": "csv",
                    "row_count": "0",
                    "column_count": "0",
                    "parse_status": "MISSING",
                    "position_like": "NO",
                    "open_position_count": "0",
                    "selected_for_positions": "NO",
                    "note": "EXPECTED_CANDIDATE_NAME_NOT_FOUND_AT_THIS_ROOT",
                }
            )

    selected_positions: List[Dict[str, object]] = []
    for path, rows, fields, position_like, open_count in sorted(parsed_sources, key=lambda x: source_rank(x[0])):
        if not position_like or open_count <= 0:
            continue
        selected_positions = parse_open_positions(path, rows, fields)
        if selected_positions:
            for audit in audit_rows:
                if audit.get("source_file") == str(path):
                    audit["selected_for_positions"] = "YES"
                    audit["note"] = "SELECTED_POSITION_SOURCE_BY_PRIORITY"
            break

    tech_map = load_technical_map(root)
    if selected_positions:
        output_rows = []
        for pos in selected_positions:
            technical_blob = f"{pos.get('raw_blob', '')} {tech_map.get(str(pos.get('ticker', '')).upper(), '')}".upper()
            output_rows.append(evaluate_position(pos, technical_blob, snapshot_date))
    else:
        output_rows = [no_position_row(snapshot_date)]

    position_count = len(selected_positions)
    actionable_count = sum(1 for row in output_rows if row.get("shadow_exit_action") not in {"HOLD", "NO_POSITION"})
    status = STATUS_OK

    write_csv(csv_path, output_rows, OUTPUT_FIELDS)
    write_csv(audit_path, audit_rows, AUDIT_FIELDS)
    write_text(report_path, make_report(report_path, csv_path, audit_path, snapshot_date, status, audit_rows, output_rows, position_count, actionable_count))
    write_text(read_first_path, make_read_first(status, position_count, actionable_count, report_path, csv_path, audit_path))

    return {
        "STATUS": status,
        "POSITION_COUNT": str(position_count),
        "ACTIONABLE_EXIT_COUNT": str(actionable_count),
        "REPORT": str(report_path),
        "CSV": str(csv_path),
        "INPUT_AUDIT": str(audit_path),
        "READ_FIRST": str(read_first_path),
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_SELL": AUTO_SELL,
        "AUTO_TRADE": AUTO_TRADE,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.12A sell timing shadow engine.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()

    result = generate(Path(args.root))
    for key in ["STATUS", "POSITION_COUNT", "ACTIONABLE_EXIT_COUNT", "OFFICIAL_DECISION_IMPACT", "AUTO_SELL", "AUTO_TRADE", "REPORT", "CSV", "INPUT_AUDIT", "READ_FIRST"]:
        print(f"{key}: {result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
