import argparse
import csv
import os
import re
from datetime import datetime
from pathlib import Path


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv_rows(path: Path):
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    return []


def write_csv_rows(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def extract_field(text: str, label: str, default: str = "UNKNOWN") -> str:
    if not text:
        return default

    patterns = [
        rf"(?im)^\s*[-*]?\s*{re.escape(label)}\s*[:：]\s*`?([^`\n\r]+)`?\s*$",
        rf"(?im)^\s*{re.escape(label)}\s*$\s*^\s*`?([^`\n\r]+)`?\s*$",
        rf"(?im){re.escape(label)}\s*[:：]\s*`?([A-Z0-9_\-\.]+)`?",
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip().strip("`").strip()

    return default


def normalize_num(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "").replace("$", "").replace("¥", "")
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None


def pick_col(rows, candidates):
    if not rows:
        return None
    cols = list(rows[0].keys())
    lower = {c.lower(): c for c in cols}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    for c in cols:
        cl = c.lower()
        for cand in candidates:
            if cand.lower() in cl:
                return c
    return None


def load_account(account_path: Path, initial_cash_usd: float):
    fields = ["account_id", "cash_usd", "realized_pnl_usd", "created_at", "updated_at"]
    if account_path.exists():
        rows = read_csv_rows(account_path)
        if rows:
            row = rows[0]
            return {
                "account_id": row.get("account_id") or "V18_SIM",
                "cash_usd": normalize_num(row.get("cash_usd")) or 0.0,
                "realized_pnl_usd": normalize_num(row.get("realized_pnl_usd")) or 0.0,
                "created_at": row.get("created_at") or "",
                "updated_at": row.get("updated_at") or "",
            }, fields

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "account_id": "V18_SIM",
        "cash_usd": float(initial_cash_usd),
        "realized_pnl_usd": 0.0,
        "created_at": now,
        "updated_at": now,
    }, fields


def classify_official_permission(final_action: str, buy_permission: str) -> str:
    blob = f"{final_action} {buy_permission}".upper()

    block_words = [
        "NO_BUY",
        "NO_NEW_BUYS",
        "NO_TRADE",
        "BLOCK",
        "LOCKED",
        "WAIT",
        "EVENT",
        "BUDGET_LOCKED",
    ]
    allow_words = [
        "BUY_NOW",
        "EXECUTE",
        "TRIAL",
        "PROBE",
        "ALLOW",
        "YES",
    ]

    if any(w in blob for w in block_words):
        return "OFFICIAL_BLOCKED"

    if any(w in blob for w in allow_words):
        return "OFFICIAL_ALLOWED"

    return "OFFICIAL_UNKNOWN_CONSERVATIVE_BLOCK"


def row_text(row):
    return " ".join(str(v) for v in row.values() if v is not None).upper()


def select_candidates(tech_rows, max_new_positions):
    if not tech_rows:
        return []

    ticker_col = pick_col(tech_rows, ["ticker", "symbol"])
    price_col = pick_col(tech_rows, ["latest_close", "last_close", "close", "price", "adj_close"])

    if not ticker_col:
        return []

    good_terms = [
        "PULLBACK_WATCH",
        "WATCH_POSITIVE",
        "BREAKOUT_CONTINUATION",
        "BB_SQUEEZE",
        "SQUEEZE",
    ]

    bad_terms = [
        "EXHAUSTION",
        "OVERHEAT",
        "STALE",
        "LOW_COVERAGE",
        "FAIL",
    ]

    selected = []
    seen = set()

    for r in tech_rows:
        t = str(r.get(ticker_col, "")).strip().upper()
        if not t or t in seen:
            continue

        txt = row_text(r)
        if not any(g in txt for g in good_terms):
            continue
        if any(b in txt for b in bad_terms):
            continue

        price = normalize_num(r.get(price_col)) if price_col else None
        if price is None or price <= 0:
            continue

        selected.append({
            "ticker": t,
            "price": price,
            "reason": "TECH_SHADOW_ELIGIBLE",
            "raw_status": txt[:300],
        })
        seen.add(t)

        if len(selected) >= max_new_positions:
            break

    return selected


def current_position_tickers(position_rows):
    out = set()
    for r in position_rows:
        qty = normalize_num(r.get("quantity")) or 0
        ticker = str(r.get("ticker", "")).strip().upper()
        if ticker and qty > 0:
            out.add(ticker)
    return out


def update_mark_to_market(position_rows, tech_rows):
    if not position_rows:
        return position_rows, 0.0, 0.0

    ticker_col = pick_col(tech_rows, ["ticker", "symbol"])
    price_col = pick_col(tech_rows, ["latest_close", "last_close", "close", "price", "adj_close"])

    price_map = {}
    if ticker_col and price_col:
        for r in tech_rows:
            t = str(r.get(ticker_col, "")).strip().upper()
            p = normalize_num(r.get(price_col))
            if t and p and p > 0:
                price_map[t] = p

    total_mv = 0.0
    total_unreal = 0.0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for r in position_rows:
        t = str(r.get("ticker", "")).strip().upper()
        qty = normalize_num(r.get("quantity")) or 0.0
        avg = normalize_num(r.get("avg_cost_usd")) or 0.0
        last = price_map.get(t, normalize_num(r.get("last_price_usd")) or avg)

        mv = qty * last
        unreal = qty * (last - avg)

        r["last_price_usd"] = f"{last:.4f}"
        r["market_value_usd"] = f"{mv:.4f}"
        r["unrealized_pnl_usd"] = f"{unreal:.4f}"
        r["updated_at"] = now

        total_mv += mv
        total_unreal += unreal

    return position_rows, total_mv, total_unreal


def append_trade_log_once(trade_path: Path, new_rows):
    fields = [
        "sim_date",
        "timestamp",
        "action",
        "ticker",
        "quantity",
        "price_usd",
        "notional_usd",
        "reason",
        "official_permission",
        "source",
    ]

    old = read_csv_rows(trade_path) if trade_path.exists() else []
    existing_keys = set()
    for r in old:
        existing_keys.add((
            r.get("sim_date", ""),
            r.get("action", ""),
            r.get("ticker", ""),
            r.get("reason", ""),
        ))

    merged = list(old)
    appended = []
    for r in new_rows:
        key = (
            r.get("sim_date", ""),
            r.get("action", ""),
            r.get("ticker", ""),
            r.get("reason", ""),
        )
        if key not in existing_keys:
            merged.append(r)
            appended.append(r)
            existing_keys.add(key)

    write_csv_rows(trade_path, merged, fields)
    return appended, merged, fields


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"D:\us-tech-quant")
    ap.add_argument("--initial-cash-usd", type=float, default=2000.0)
    ap.add_argument("--max-new-positions", type=int, default=3)
    args = ap.parse_args()

    root = Path(args.root)

    out_dir = root / "outputs" / "v18" / "simulation"
    state_dir = root / "state" / "v18" / "simulation"
    out_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    read_first_path = root / "outputs" / "v18" / "read_center" / "V18_6E_READ_FIRST.txt"
    read_center_path = root / "outputs" / "v18" / "read_center" / "V18_6E_CURRENT_FINAL_READ_CENTER_WITH_TECHNICAL.md"
    tech_dash_path = root / "outputs" / "v18" / "technical_timing_read_center" / "V18_6D_CURRENT_TECHNICAL_TIMING_DASHBOARD.csv"

    account_path = state_dir / "V18_CURRENT_SIM_ACCOUNT.csv"
    positions_path = state_dir / "V18_CURRENT_PAPER_POSITIONS.csv"
    trade_log_path = state_dir / "V18_CURRENT_PAPER_TRADE_LOG.csv"

    output_positions_path = out_dir / "V18_CURRENT_PAPER_POSITIONS.csv"
    output_trade_log_path = out_dir / "V18_CURRENT_PAPER_TRADE_LOG.csv"
    output_pnl_path = out_dir / "V18_CURRENT_PAPER_PNL.csv"
    report_path = out_dir / "V18_CURRENT_SIM_CABIN.md"
    read_first_out = out_dir / "V18_8B_READ_FIRST.txt"

    rf_text = read_text(read_first_path)
    rc_text = read_text(read_center_path)
    all_text = rf_text + "\n" + rc_text

    final_action = extract_field(all_text, "FINAL_ACTION")
    buy_permission = extract_field(all_text, "BUY_PERMISSION")
    vix_regime = extract_field(all_text, "VIX_REGIME")
    official_decision_impact = extract_field(all_text, "OFFICIAL_DECISION_IMPACT")

    official_permission = classify_official_permission(final_action, buy_permission)

    tech_rows = read_csv_rows(tech_dash_path)
    account, account_fields = load_account(account_path, args.initial_cash_usd)

    position_fields = [
        "ticker",
        "quantity",
        "avg_cost_usd",
        "last_price_usd",
        "market_value_usd",
        "unrealized_pnl_usd",
        "realized_pnl_usd",
        "opened_at",
        "updated_at",
        "source",
    ]

    position_rows = read_csv_rows(positions_path) if positions_path.exists() else []
    position_rows, total_mv, total_unreal = update_mark_to_market(position_rows, tech_rows)

    sim_date = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_trade_rows = []

    if official_permission != "OFFICIAL_ALLOWED":
        new_trade_rows.append({
            "sim_date": sim_date,
            "timestamp": now,
            "action": "DAILY_NO_TRADE",
            "ticker": "CASH",
            "quantity": "0",
            "price_usd": "0",
            "notional_usd": "0",
            "reason": official_permission,
            "official_permission": official_permission,
            "source": str(read_first_path),
        })
    else:
        held = current_position_tickers(position_rows)
        candidates = select_candidates(tech_rows, args.max_new_positions)
        cash = float(account.get("cash_usd", 0.0))

        for c in candidates:
            if c["ticker"] in held:
                continue

            qty = 1
            notional = c["price"] * qty
            if cash < notional:
                continue

            cash -= notional
            account["cash_usd"] = cash

            position_rows.append({
                "ticker": c["ticker"],
                "quantity": str(qty),
                "avg_cost_usd": f"{c['price']:.4f}",
                "last_price_usd": f"{c['price']:.4f}",
                "market_value_usd": f"{notional:.4f}",
                "unrealized_pnl_usd": "0.0000",
                "realized_pnl_usd": "0.0000",
                "opened_at": now,
                "updated_at": now,
                "source": "V18_8B_TECH_SHADOW",
            })

            new_trade_rows.append({
                "sim_date": sim_date,
                "timestamp": now,
                "action": "PAPER_BUY",
                "ticker": c["ticker"],
                "quantity": str(qty),
                "price_usd": f"{c['price']:.4f}",
                "notional_usd": f"{notional:.4f}",
                "reason": c["reason"],
                "official_permission": official_permission,
                "source": str(tech_dash_path),
            })

        if not new_trade_rows:
            new_trade_rows.append({
                "sim_date": sim_date,
                "timestamp": now,
                "action": "DAILY_NO_TRADE",
                "ticker": "CASH",
                "quantity": "0",
                "price_usd": "0",
                "notional_usd": "0",
                "reason": "OFFICIAL_ALLOWED_BUT_NO_ELIGIBLE_TECH_CANDIDATE_OR_CASH",
                "official_permission": official_permission,
                "source": str(tech_dash_path),
            })

    account["updated_at"] = now

    # Re-mark after possible buys.
    position_rows, total_mv, total_unreal = update_mark_to_market(position_rows, tech_rows)

    appended_rows, all_trade_rows, trade_fields = append_trade_log_once(trade_log_path, new_trade_rows)

    write_csv_rows(account_path, [account], account_fields)
    write_csv_rows(positions_path, position_rows, position_fields)

    # Mirror current state to outputs.
    write_csv_rows(output_positions_path, position_rows, position_fields)
    write_csv_rows(output_trade_log_path, all_trade_rows, trade_fields)

    pnl_fields = [
        "sim_date",
        "cash_usd",
        "market_value_usd",
        "equity_usd",
        "realized_pnl_usd",
        "unrealized_pnl_usd",
        "position_count",
        "official_permission",
        "final_action",
        "buy_permission",
        "vix_regime",
    ]

    cash_usd = float(account.get("cash_usd", 0.0))
    realized = float(account.get("realized_pnl_usd", 0.0))
    equity = cash_usd + total_mv

    pnl_row = {
        "sim_date": sim_date,
        "cash_usd": f"{cash_usd:.4f}",
        "market_value_usd": f"{total_mv:.4f}",
        "equity_usd": f"{equity:.4f}",
        "realized_pnl_usd": f"{realized:.4f}",
        "unrealized_pnl_usd": f"{total_unreal:.4f}",
        "position_count": str(len([r for r in position_rows if (normalize_num(r.get('quantity')) or 0) > 0])),
        "official_permission": official_permission,
        "final_action": final_action,
        "buy_permission": buy_permission,
        "vix_regime": vix_regime,
    }

    old_pnl = read_csv_rows(output_pnl_path) if output_pnl_path.exists() else []
    old_pnl = [r for r in old_pnl if r.get("sim_date") != sim_date]
    old_pnl.append(pnl_row)
    write_csv_rows(output_pnl_path, old_pnl, pnl_fields)

    status = "OK_SIM_CABIN_READY"
    trade_count_today = len(appended_rows)
    position_count = pnl_row["position_count"]

    report = []
    report.append("# V18.8B Current Simulation Cabin")
    report.append("")
    report.append(f"- STATUS: `{status}`")
    report.append("- MODE: `SHADOW_ONLY`")
    report.append(f"- SIM_DATE: `{sim_date}`")
    report.append(f"- GENERATED_AT: `{now}`")
    report.append(f"- OFFICIAL_PERMISSION: `{official_permission}`")
    report.append(f"- FINAL_ACTION: `{final_action}`")
    report.append(f"- BUY_PERMISSION: `{buy_permission}`")
    report.append(f"- VIX_REGIME: `{vix_regime}`")
    report.append(f"- OFFICIAL_DECISION_IMPACT: `{official_decision_impact}`")
    report.append("")
    report.append("## Account")
    report.append("")
    report.append(f"- CASH_USD: `{cash_usd:.4f}`")
    report.append(f"- MARKET_VALUE_USD: `{total_mv:.4f}`")
    report.append(f"- EQUITY_USD: `{equity:.4f}`")
    report.append(f"- REALIZED_PNL_USD: `{realized:.4f}`")
    report.append(f"- UNREALIZED_PNL_USD: `{total_unreal:.4f}`")
    report.append(f"- POSITION_COUNT: `{position_count}`")
    report.append(f"- NEW_TRADE_LOG_ROWS_TODAY: `{trade_count_today}`")
    report.append("")
    report.append("## Today's Simulation Actions")
    report.append("")
    report.append("| action | ticker | quantity | price_usd | notional_usd | reason |")
    report.append("|---|---:|---:|---:|---:|---|")
    for r in appended_rows:
        report.append(
            f"| {r.get('action','')} | {r.get('ticker','')} | {r.get('quantity','')} | "
            f"{r.get('price_usd','')} | {r.get('notional_usd','')} | {r.get('reason','')} |"
        )
    if not appended_rows:
        report.append("| NO_NEW_ROW | CASH | 0 | 0 | 0 | DUPLICATE_DAILY_ENTRY_ALREADY_EXISTS |")

    report.append("")
    report.append("## Current Positions")
    report.append("")
    report.append("| ticker | quantity | avg_cost_usd | last_price_usd | market_value_usd | unrealized_pnl_usd |")
    report.append("|---|---:|---:|---:|---:|---:|")
    active_positions = [r for r in position_rows if (normalize_num(r.get("quantity")) or 0) > 0]
    for r in active_positions:
        report.append(
            f"| {r.get('ticker','')} | {r.get('quantity','')} | {r.get('avg_cost_usd','')} | "
            f"{r.get('last_price_usd','')} | {r.get('market_value_usd','')} | {r.get('unrealized_pnl_usd','')} |"
        )
    if not active_positions:
        report.append("| NONE | 0 | 0 | 0 | 0 | 0 |")

    report.append("")
    report.append("## Files")
    report.append("")
    report.append(f"- REPORT: `{report_path}`")
    report.append(f"- READ_FIRST: `{read_first_out}`")
    report.append(f"- STATE_ACCOUNT: `{account_path}`")
    report.append(f"- STATE_POSITIONS: `{positions_path}`")
    report.append(f"- STATE_TRADE_LOG: `{trade_log_path}`")
    report.append(f"- OUTPUT_POSITIONS: `{output_positions_path}`")
    report.append(f"- OUTPUT_TRADE_LOG: `{output_trade_log_path}`")
    report.append(f"- OUTPUT_PNL: `{output_pnl_path}`")
    report.append("")
    report.append("## Interpretation")
    report.append("")
    report.append("- This module is shadow-only.")
    report.append("- It does not modify the official decision.")
    report.append("- It records whether the official daily system would allow a simulated trade.")
    report.append("- If official risk gates block buying, the simulation cabin also records no trade.")

    write_text(report_path, "\n".join(report))

    rf = []
    rf.append("V18.8B CURRENT SIMULATION CABIN")
    rf.append("")
    rf.append(f"STATUS: {status}")
    rf.append("MODE: SHADOW_ONLY")
    rf.append(f"SIM_DATE: {sim_date}")
    rf.append(f"OFFICIAL_PERMISSION: {official_permission}")
    rf.append(f"FINAL_ACTION: {final_action}")
    rf.append(f"BUY_PERMISSION: {buy_permission}")
    rf.append(f"VIX_REGIME: {vix_regime}")
    rf.append(f"CASH_USD: {cash_usd:.4f}")
    rf.append(f"MARKET_VALUE_USD: {total_mv:.4f}")
    rf.append(f"EQUITY_USD: {equity:.4f}")
    rf.append(f"POSITION_COUNT: {position_count}")
    rf.append(f"NEW_TRADE_LOG_ROWS_TODAY: {trade_count_today}")
    rf.append("")
    rf.append("REPORT:")
    rf.append(str(report_path))
    rf.append("")
    rf.append("STATE_POSITIONS:")
    rf.append(str(positions_path))
    rf.append("")
    rf.append("STATE_TRADE_LOG:")
    rf.append(str(trade_log_path))
    rf.append("")
    rf.append("OUTPUT_PNL:")
    rf.append(str(output_pnl_path))

    write_text(read_first_out, "\n".join(rf))

    print("")
    print("=== V18.8B CURRENT SIMULATION CABIN READY ===")
    print(f"STATUS: {status}")
    print("MODE: SHADOW_ONLY")
    print(f"SIM_DATE: {sim_date}")
    print(f"OFFICIAL_PERMISSION: {official_permission}")
    print(f"FINAL_ACTION: {final_action}")
    print(f"BUY_PERMISSION: {buy_permission}")
    print(f"VIX_REGIME: {vix_regime}")
    print(f"CASH_USD: {cash_usd:.4f}")
    print(f"MARKET_VALUE_USD: {total_mv:.4f}")
    print(f"EQUITY_USD: {equity:.4f}")
    print(f"POSITION_COUNT: {position_count}")
    print(f"NEW_TRADE_LOG_ROWS_TODAY: {trade_count_today}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first_out}")
    print("")


if __name__ == "__main__":
    main()
