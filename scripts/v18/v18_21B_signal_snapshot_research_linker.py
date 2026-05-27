import argparse
import csv
import hashlib
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


MODE = "ADVISORY_ONLY"
PATCH_MODE = "SIGNAL_SNAPSHOT_AND_RESEARCH_LINK_ONLY"
STATUS_OK = "OK_V18_21B_SIGNAL_SNAPSHOT_RESEARCH_LINKER_READY"
STATUS_WARN = "WARN_V18_21B_SIGNAL_SNAPSHOT_RESEARCH_LINKER_DEGRADED"
QUALITY_PATCH_COMPATIBILITY = "V18_21B_R1_READY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "PRICE_FACTOR_MODIFIED": "FALSE",
    "SIMULATION_POSITION_MODIFIED": "FALSE",
    "FORWARD_TRACKER_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
}

SNAPSHOT_FIELDS = [
    "snapshot_date",
    "ticker",
    "signal_snapshot_id",
    "source_presence_summary",
    "factor_pack_rank",
    "factor_pack_score",
    "composite_candidate_score",
    "technical_timing_score",
    "technical_label",
    "overheat_penalty",
    "price_derived_total_score",
    "price_derived_status",
    "factor_scope_class",
    "score_scope",
    "full_factor_score_ready",
    "light_factor_score_ready",
    "score_ready",
    "relative_strength_score",
    "trend_structure_score",
    "buy_zone_score",
    "buy_zone_label",
    "nearest_buy_zone_distance",
    "volume_confirmation_score",
    "breakout_volume_confirmed",
    "volatility_risk_score",
    "market_regime_label",
    "market_risk_coefficient",
    "market_regime_confidence",
    "vix_proxy_status",
    "vix_missing_cap_applied",
    "true_5day_unique_coverage_met",
    "coverage_window_complete",
    "daily_trust_level",
    "buy_permission",
    "event_status",
    "simulation_link_key",
    "forward_tracker_link_key",
    "manual_feedback_link_key",
    "signal_research_status",
    "signal_snapshot_quality_status",
]

SOURCE_DEFS = [
    {
        "name": "factor_pack",
        "path": "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        "component": "factor_pack",
        "fields": ["factor_pack_rank", "ticker", "factor_pack_score", "overheat_penalty"],
    },
    {
        "name": "technical_timing",
        "path": "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
        "component": "technical_timing",
        "fields": ["ticker", "technical_timing_score", "technical_signal", "overheat_penalty"],
    },
    {
        "name": "price_derived_scores",
        "path": "outputs/v18/price_factors/V18_21A_R2_CURRENT_PRICE_DERIVED_FACTOR_SCORES.csv",
        "component": "price_derived_factors",
        "fields": [
            "ticker",
            "price_derived_total_score",
            "price_derived_status",
            "relative_strength_score",
            "trend_structure_score",
            "buy_zone_score",
            "volume_confirmation_score",
            "volatility_risk_score",
            "score_ready",
            "score_scope",
        ],
    },
    {
        "name": "price_derived_factor_details",
        "path": "outputs/v18/price_factors/V18_21A_CURRENT_PRICE_DERIVED_FACTORS.csv",
        "component": "price_derived_factors",
        "fields": ["ticker", "buy_zone_label", "nearest_buy_zone_distance", "breakout_volume_confirmed"],
    },
    {
        "name": "price_factor_scope",
        "path": "outputs/v18/price_factors/V18_21A_R3_CURRENT_FACTOR_SCOPE_SUMMARY.csv",
        "component": "price_derived_factors",
        "fields": ["ticker", "factor_scope_class", "score_scope", "full_factor_score_ready", "light_factor_score_ready"],
    },
    {
        "name": "backfill_priority_plan",
        "path": "outputs/v18/price_factors/V18_21A_R4_CURRENT_BACKFILL_PRIORITY_PLAN.csv",
        "component": "price_derived_factors",
        "fields": ["ticker", "planned_batch_index", "priority_tier", "priority_score"],
    },
    {
        "name": "backfill_coverage_projection",
        "path": "outputs/v18/price_factors/V18_21A_R4_CURRENT_COVERAGE_PROJECTION.csv",
        "component": "price_derived_factors",
        "fields": ["scenario_name", "projected_score_ready_ratio"],
        "tickerless": True,
    },
    {
        "name": "market_regime",
        "path": "outputs/v18/market_regime/V18_21A_R2_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv",
        "component": "market_regime",
        "fields": ["market_regime_label", "market_risk_coefficient", "market_regime_confidence", "vix_proxy_status"],
        "tickerless": True,
    },
    {
        "name": "price_backfill_read_first",
        "path": "outputs/v18/ops/V18_21A_R4_READ_FIRST.txt",
        "component": "market_regime",
        "fields": ["MARKET_REGIME_STATUS", "MARKET_RISK_COEFFICIENT"],
        "read_first": True,
    },
    {
        "name": "coverage_stable_read_first",
        "path": "outputs/v18/ops/V18_16K_R2_STABLE_READ_FIRST.txt",
        "component": "coverage_trust",
        "fields": ["TRUE_5DAY_UNIQUE_COVERAGE_MET", "COVERAGE_WINDOW_COMPLETE"],
        "read_first": True,
    },
    {
        "name": "coverage_current_read_first",
        "path": "outputs/v18/ops/V18_16K_R2_READ_FIRST.txt",
        "component": "coverage_trust",
        "fields": ["TRUE_5DAY_UNIQUE_COVERAGE_MET", "COVERAGE_WINDOW_COMPLETE"],
        "read_first": True,
    },
    {
        "name": "daily_trust_read_first",
        "path": "outputs/v18/ops/V18_19A_READ_FIRST.txt",
        "component": "coverage_trust",
        "fields": ["DAILY_TRUST_LEVEL", "TRUE_5DAY_UNIQUE_COVERAGE_MET"],
        "read_first": True,
    },
    {
        "name": "current_daily_read_first",
        "path": "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
        "component": "coverage_trust",
        "fields": ["BUY_PERMISSION", "EVENT_STATUS"],
        "read_first": True,
    },
    {
        "name": "simulation_tracker",
        "path": "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        "component": "simulation_reference",
        "fields": ["ticker", "snapshot_date", "buy_permission", "candidate_bucket", "forward_status"],
    },
    {
        "name": "simulation_tracker_today",
        "path": "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER_TODAY.csv",
        "component": "simulation_reference",
        "fields": ["ticker", "snapshot_date", "buy_permission", "candidate_bucket", "forward_status"],
    },
    {
        "name": "forward_tracker",
        "path": "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv",
        "component": "forward_tracker_reference",
        "fields": ["ticker"],
    },
    {
        "name": "manual_trade_feedback",
        "path": "outputs/v18/positions/V18_CURRENT_MANUAL_TRADE_FEEDBACK.csv",
        "component": "manual_feedback_reference",
        "fields": ["ticker"],
    },
]


def norm_ticker(value):
    return str(value or "").strip().upper().replace(".", "-")


def now_stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def file_time(path):
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def read_first(path):
    data = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in raw:
            key, value = raw.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def read_csv_rows(path):
    if not path.exists():
        return [], []
    try:
        with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
            reader = csv.DictReader(handle)
            rows = [dict(row) for row in reader]
            return rows, list(reader.fieldnames or [])
    except Exception:
        return [], []


def first_nonblank(row, names):
    for name in names:
        value = row.get(name, "")
        if str(value).strip() != "":
            return value
    return ""


def index_by_ticker(rows):
    indexed = {}
    for row in rows:
        ticker = norm_ticker(first_nonblank(row, ["ticker", "Ticker", "symbol", "Symbol", "yf_ticker"]))
        if ticker and ticker not in indexed:
            indexed[ticker] = row
    return indexed


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run_command(command):
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
        return completed.returncode == 0, (completed.stdout + completed.stderr).strip()
    except Exception as exc:
        return False, str(exc)


def parse_sources(root):
    parsed = {}
    audits = []
    missing_count = 0
    for src in SOURCE_DEFS:
        path = root / src["path"]
        exists = path.exists()
        rows, fields = ([], [])
        rf = {}
        notes = ""
        if exists and src.get("read_first"):
            rf = read_first(path)
        elif exists:
            rows, fields = read_csv_rows(path)
            if not rows and path.suffix.lower() == ".csv":
                notes = "CSV had no parsed rows or was unreadable."
        else:
            missing_count += 1
            notes = "Missing input source; component will degrade if no alternate exists."
        tickers = set()
        if rows:
            tickers = {norm_ticker(first_nonblank(row, ["ticker", "Ticker", "symbol", "Symbol", "yf_ticker"])) for row in rows}
            tickers.discard("")
        parsed[src["name"]] = {"def": src, "path": path, "rows": rows, "fields": fields, "read_first": rf, "tickers": tickers}
        if exists and src.get("read_first"):
            status = "OK_READ_FIRST_PARSED" if rf else "WARN_READ_FIRST_EMPTY"
        elif exists:
            status = "OK_PARSED" if rows or src.get("tickerless") else "WARN_NO_ROWS"
        else:
            status = "MISSING"
        audits.append(
            {
                "source_name": src["name"],
                "source_path": str(path),
                "source_exists": str(exists).upper(),
                "modified_time": file_time(path),
                "parsed_row_count": len(rows) if rows else (len(rf) if rf else 0),
                "parsed_ticker_count": len(tickers),
                "fields_used": ";".join(src.get("fields", [])),
                "source_status": status,
                "notes": notes,
            }
        )
    return parsed, audits, missing_count


def market_values(parsed):
    rows = parsed.get("market_regime", {}).get("rows", [])
    row = rows[0] if rows else {}
    rf = parsed.get("price_backfill_read_first", {}).get("read_first", {})
    return {
        "market_regime_label": row.get("market_regime_label", ""),
        "market_risk_coefficient": row.get("market_risk_coefficient", rf.get("MARKET_RISK_COEFFICIENT", "")),
        "market_regime_confidence": row.get("market_regime_confidence", ""),
        "vix_proxy_status": row.get("vix_proxy_status", ""),
        "vix_missing_cap_applied": row.get("vix_missing_cap_applied", ""),
        "market_regime_status": row.get("market_regime_data_status", rf.get("MARKET_REGIME_STATUS", "")),
    }


def coverage_values(parsed):
    stable = parsed.get("coverage_stable_read_first", {}).get("read_first", {})
    current = parsed.get("coverage_current_read_first", {}).get("read_first", {})
    trust = parsed.get("daily_trust_read_first", {}).get("read_first", {})
    daily = parsed.get("current_daily_read_first", {}).get("read_first", {})
    return {
        "true_5day_unique_coverage_met": stable.get("TRUE_5DAY_UNIQUE_COVERAGE_MET", current.get("TRUE_5DAY_UNIQUE_COVERAGE_MET", "")),
        "coverage_window_complete": stable.get("COVERAGE_WINDOW_COMPLETE", current.get("COVERAGE_WINDOW_COMPLETE", "")),
        "daily_trust_level": trust.get("DAILY_TRUST_LEVEL", ""),
        "buy_permission": daily.get("BUY_PERMISSION", ""),
        "event_status": daily.get("EVENT_STATUS", ""),
    }


def make_id(snapshot_date, ticker):
    digest = hashlib.sha1(f"V18_21B|{snapshot_date}|{ticker}".encode("utf-8")).hexdigest()[:12].upper()
    return f"V18_21B-{snapshot_date}-{ticker}-{digest}"


def build_snapshot(parsed, snapshot_date):
    factor = index_by_ticker(parsed["factor_pack"]["rows"])
    tech = index_by_ticker(parsed["technical_timing"]["rows"])
    price_scores = index_by_ticker(parsed["price_derived_scores"]["rows"])
    price_details = index_by_ticker(parsed["price_derived_factor_details"]["rows"])
    scope = index_by_ticker(parsed["price_factor_scope"]["rows"])
    backfill = index_by_ticker(parsed["backfill_priority_plan"]["rows"])
    sim = index_by_ticker(parsed["simulation_tracker"]["rows"])
    sim_today = index_by_ticker(parsed["simulation_tracker_today"]["rows"])
    forward = index_by_ticker(parsed["forward_tracker"]["rows"])
    manual = index_by_ticker(parsed["manual_trade_feedback"]["rows"])

    tickers = set()
    for index in [factor, tech, price_scores, price_details, scope, backfill, sim, sim_today, forward, manual]:
        tickers.update(index.keys())

    market = market_values(parsed)
    coverage = coverage_values(parsed)
    rows = []
    degraded_count = 0
    for ticker in sorted(tickers):
        frow = factor.get(ticker, {})
        trow = tech.get(ticker, {})
        psrow = price_scores.get(ticker, {})
        pdrow = price_details.get(ticker, {})
        scrow = scope.get(ticker, {})
        simrow = sim_today.get(ticker) or sim.get(ticker, {})
        components = []
        for name, index in [
            ("factor_pack", factor),
            ("technical_timing", tech),
            ("price_derived_factors", price_scores),
            ("factor_scope", scope),
            ("backfill_plan", backfill),
            ("simulation", sim if ticker not in sim_today else sim_today),
            ("forward_tracker", forward),
            ("manual_feedback", manual),
        ]:
            if ticker in index:
                components.append(name)
        missing_core = []
        if ticker not in factor:
            missing_core.append("factor_pack")
        if ticker not in tech:
            missing_core.append("technical_timing")
        if ticker not in price_scores:
            missing_core.append("price_derived_factors")
        if missing_core:
            degraded_count += 1
        snapshot_id = make_id(snapshot_date, ticker)
        sim_key = f"simulation|{snapshot_date}|{ticker}" if ticker in sim or ticker in sim_today else ""
        forward_key = f"forward_tracker|{snapshot_date}|{ticker}" if ticker in forward else ""
        manual_key = f"manual_feedback|{snapshot_date}|{ticker}" if ticker in manual else ""
        ready_research = "TRUE" if ticker in price_scores and (ticker in factor or ticker in tech) else "FALSE"
        row = {
            "snapshot_date": snapshot_date,
            "ticker": ticker,
            "signal_snapshot_id": snapshot_id,
            "source_presence_summary": ";".join(components) if components else "NO_COMPONENT_SOURCE",
            "factor_pack_rank": frow.get("factor_pack_rank", ""),
            "factor_pack_score": frow.get("factor_pack_score", ""),
            "composite_candidate_score": first_nonblank(frow, ["composite_candidate_score", "candidate_score", "factor_pack_score"]),
            "technical_timing_score": trow.get("technical_timing_score", ""),
            "technical_label": first_nonblank(trow, ["technical_label", "technical_signal", "technical_warning_label"]),
            "overheat_penalty": first_nonblank(trow, ["overheat_penalty"]) or frow.get("overheat_penalty", ""),
            "price_derived_total_score": psrow.get("price_derived_total_score", ""),
            "price_derived_status": psrow.get("price_derived_status", ""),
            "factor_scope_class": first_nonblank(scrow, ["factor_scope_class"]) or psrow.get("factor_scope_class", ""),
            "score_scope": first_nonblank(scrow, ["score_scope"]) or psrow.get("score_scope", ""),
            "full_factor_score_ready": first_nonblank(scrow, ["full_factor_score_ready"]) or psrow.get("full_factor_score_ready", ""),
            "light_factor_score_ready": first_nonblank(scrow, ["light_factor_score_ready"]) or psrow.get("light_factor_score_ready", ""),
            "score_ready": psrow.get("score_ready", ""),
            "relative_strength_score": psrow.get("relative_strength_score", ""),
            "trend_structure_score": psrow.get("trend_structure_score", ""),
            "buy_zone_score": psrow.get("buy_zone_score", ""),
            "buy_zone_label": pdrow.get("buy_zone_label", ""),
            "nearest_buy_zone_distance": pdrow.get("nearest_buy_zone_distance", ""),
            "volume_confirmation_score": psrow.get("volume_confirmation_score", ""),
            "breakout_volume_confirmed": pdrow.get("breakout_volume_confirmed", ""),
            "volatility_risk_score": psrow.get("volatility_risk_score", ""),
            "market_regime_label": market["market_regime_label"],
            "market_risk_coefficient": market["market_risk_coefficient"],
            "market_regime_confidence": market["market_regime_confidence"],
            "vix_proxy_status": market["vix_proxy_status"],
            "vix_missing_cap_applied": market["vix_missing_cap_applied"],
            "true_5day_unique_coverage_met": coverage["true_5day_unique_coverage_met"],
            "coverage_window_complete": coverage["coverage_window_complete"],
            "daily_trust_level": coverage["daily_trust_level"],
            "buy_permission": first_nonblank(simrow, ["buy_permission", "official_permission"]) or coverage["buy_permission"],
            "event_status": first_nonblank(simrow, ["blocked_or_observe_reason", "event_status"]) or coverage["event_status"],
            "simulation_link_key": sim_key,
            "forward_tracker_link_key": forward_key,
            "manual_feedback_link_key": manual_key,
            "signal_research_status": "READY_FOR_SNAPSHOT_RESEARCH" if ready_research == "TRUE" else "DEGRADED_COMPONENT_MISSING",
            "signal_snapshot_quality_status": "OK" if not missing_core else "DEGRADED_MISSING_" + "_".join(missing_core).upper(),
        }
        rows.append(row)
    return rows, degraded_count


def component_coverage(parsed, snapshot_rows):
    all_tickers = {row["ticker"] for row in snapshot_rows}
    total = len(all_tickers)
    source_by_component = {}
    component_tickers = {
        "factor_pack": set(parsed["factor_pack"]["tickers"]),
        "technical_timing": set(parsed["technical_timing"]["tickers"]),
        "price_derived_factors": set(parsed["price_derived_scores"]["tickers"]) | set(parsed["price_factor_scope"]["tickers"]),
        "market_regime": set(all_tickers) if parsed["market_regime"]["rows"] else set(),
        "coverage_trust": set(all_tickers)
        if parsed["coverage_stable_read_first"]["read_first"] or parsed["coverage_current_read_first"]["read_first"]
        else set(),
        "simulation_reference": set(parsed["simulation_tracker"]["tickers"]) | set(parsed["simulation_tracker_today"]["tickers"]),
        "forward_tracker_reference": set(parsed["forward_tracker"]["tickers"]),
        "manual_feedback_reference": set(parsed["manual_trade_feedback"]["tickers"]),
    }
    for name, src in parsed.items():
        component = src["def"].get("component")
        if component and component not in source_by_component and src["path"].exists():
            source_by_component[component] = str(src["path"])
    rows = []
    for component, tickers in component_tickers.items():
        available = len(tickers & all_tickers)
        missing = max(total - available, 0)
        ratio = (available / total) if total else 0.0
        rows.append(
            {
                "component_name": component,
                "available_ticker_count": available,
                "missing_ticker_count": missing,
                "coverage_ratio": f"{ratio:.6f}",
                "source_path": source_by_component.get(component, ""),
                "component_status": "OK" if available == total else ("MISSING" if available == 0 else "PARTIAL"),
                "notes": "Global source applied to all snapshot rows." if component in {"market_regime", "coverage_trust"} and available else "",
            }
        )
    return rows


def linker_rows(snapshot_rows):
    rows = []
    for row in snapshot_rows:
        ready_forward = "TRUE" if row["price_derived_total_score"] or row["factor_pack_score"] or row["technical_timing_score"] else "FALSE"
        ready_sim = "TRUE" if row["simulation_link_key"] else "FALSE"
        blocking = []
        if ready_forward != "TRUE":
            blocking.append("NO_SIGNAL_COMPONENT_SCORE_AVAILABLE")
        if ready_sim != "TRUE":
            blocking.append("NO_SIMULATION_TRACKER_ROW")
        rows.append(
            {
                "snapshot_date": row["snapshot_date"],
                "ticker": row["ticker"],
                "signal_snapshot_id": row["signal_snapshot_id"],
                "simulation_link_key": row["simulation_link_key"],
                "forward_tracker_link_key": row["forward_tracker_link_key"],
                "manual_feedback_link_key": row["manual_feedback_link_key"],
                "recommended_research_use": "FORWARD_RETURN_SIGNAL_EFFECTIVENESS" if ready_forward == "TRUE" else "REFERENCE_ONLY_PENDING_SIGNAL_COMPONENTS",
                "ready_for_forward_return_research": ready_forward,
                "ready_for_simulation_analysis": ready_sim,
                "blocking_reason": ";".join(blocking),
            }
        )
    return rows


def report_text(values, source_audit, coverage_rows):
    missing = [row for row in source_audit if row["source_status"] == "MISSING"]
    degraded_components = [row for row in coverage_rows if row["component_status"] != "OK"]
    return f"""# V18.21B Signal Snapshot + Simulation Research Linker

## Executive summary
Status: {values['STATUS']}. The module created an advisory-only signal snapshot with {values['SIGNAL_SNAPSHOT_ROW_COUNT']} ticker rows and a timestamped history copy.

## Safety statement
This is a snapshot/linking layer only. It does not modify official decisions, ranking logic, technical timing logic, price factors, simulation positions, forward tracker state, manual state, price cache, broker execution, auto-trade, or auto-sell behavior.

## Input source summary
Input sources considered: {values['INPUT_SOURCE_COUNT']}. Missing sources: {values['MISSING_INPUT_SOURCE_COUNT']}. Missing or degraded inputs are recorded in `V18_21B_CURRENT_SIGNAL_SOURCE_AUDIT.csv`.

## Signal snapshot field summary
Rows include ranking, technical timing, price-derived factor, factor scope, market regime, coverage/trust, simulation link, forward tracker link, and manual feedback link fields when available. Missing components are marked in `signal_snapshot_quality_status`.

## Component coverage summary
Factor pack coverage: {values['FACTOR_PACK_COVERAGE_COUNT']}. Technical timing coverage: {values['TECHNICAL_TIMING_COVERAGE_COUNT']}. Price-derived coverage: {values['PRICE_DERIVED_COVERAGE_COUNT']}.

## Simulation/forward/manual link keys
Link keys are deterministic references generated from the snapshot date and ticker when a local source row exists. They do not create or modify simulation, forward tracker, or manual feedback state.

## Degraded/missing data summary
Market regime status: {values['MARKET_REGIME_STATUS']}. True 5-day unique coverage met: {values['TRUE_5DAY_UNIQUE_COVERAGE_MET']}. Coverage window complete: {values['COVERAGE_WINDOW_COMPLETE']}. Degraded snapshot rows: {values['DATA_DEGRADED_COUNT']}.

Missing sources:
{os.linesep.join('- ' + row['source_name'] + ': ' + row['source_path'] for row in missing) if missing else '- None'}

Degraded components:
{os.linesep.join('- ' + row['component_name'] + ': ' + row['component_status'] for row in degraded_components) if degraded_components else '- None'}

## Validation summary
Validation fail count: {values['VALIDATION_FAIL_COUNT']}. Required outputs and READ_FIRST fields were checked during the run.

## Next-step recommendation
Use the history snapshot as the immutable as-of signal state for future forward-return research and simulation analysis. Keep this advisory layer separate from official trading and ranking systems.
"""


def validate_outputs(paths, read_first_values, required_fields):
    rows = []
    fail_count = 0
    for name, path in paths.items():
        ok = path.exists()
        if not ok:
            fail_count += 1
        rows.append({"validation_check": f"output_exists:{name}", "status": "PASS" if ok else "FAIL", "notes": str(path)})
    for field in required_fields:
        ok = field in read_first_values
        if not ok:
            fail_count += 1
        rows.append({"validation_check": f"read_first_field:{field}", "status": "PASS" if ok else "FAIL", "notes": ""})
    return rows, fail_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    snapshot_date = datetime.now().strftime("%Y-%m-%d")
    stamp = now_stamp()

    out_dir = root / "outputs/v18/signal_snapshots"
    ops_dir = root / "outputs/v18/ops"
    history_dir = out_dir / "history"
    snapshot_path = out_dir / "V18_21B_CURRENT_SIGNAL_SNAPSHOT.csv"
    history_path = history_dir / f"V18_21B_SIGNAL_SNAPSHOT_{stamp}.csv"
    source_audit_path = out_dir / "V18_21B_CURRENT_SIGNAL_SOURCE_AUDIT.csv"
    coverage_audit_path = out_dir / "V18_21B_CURRENT_SIGNAL_COMPONENT_COVERAGE_AUDIT.csv"
    linker_path = out_dir / "V18_21B_CURRENT_SIMULATION_RESEARCH_LINKER.csv"
    read_first_path = ops_dir / "V18_21B_READ_FIRST.txt"
    report_path = ops_dir / "V18_21B_CURRENT_SIGNAL_SNAPSHOT_RESEARCH_LINKER_REPORT.md"

    parsed, source_audit, missing_source_count = parse_sources(root)
    snapshot_rows, degraded_count = build_snapshot(parsed, snapshot_date)
    coverage_rows = component_coverage(parsed, snapshot_rows)
    linker = linker_rows(snapshot_rows)

    write_csv(snapshot_path, snapshot_rows, SNAPSHOT_FIELDS)
    history_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(snapshot_path, history_path)
    write_csv(
        source_audit_path,
        source_audit,
        ["source_name", "source_path", "source_exists", "modified_time", "parsed_row_count", "parsed_ticker_count", "fields_used", "source_status", "notes"],
    )
    write_csv(
        coverage_audit_path,
        coverage_rows,
        ["component_name", "available_ticker_count", "missing_ticker_count", "coverage_ratio", "source_path", "component_status", "notes"],
    )
    write_csv(
        linker_path,
        linker,
        [
            "snapshot_date",
            "ticker",
            "signal_snapshot_id",
            "simulation_link_key",
            "forward_tracker_link_key",
            "manual_feedback_link_key",
            "recommended_research_use",
            "ready_for_forward_return_research",
            "ready_for_simulation_analysis",
            "blocking_reason",
        ],
    )

    market = market_values(parsed)
    coverage = coverage_values(parsed)
    comp = {row["component_name"]: row for row in coverage_rows}
    ready_forward_count = sum(1 for row in linker if row["ready_for_forward_return_research"] == "TRUE")
    ready_sim_count = sum(1 for row in linker if row["ready_for_simulation_analysis"] == "TRUE")
    core_ok = all(
        parsed[name]["path"].exists()
        for name in ["factor_pack", "technical_timing", "price_derived_scores", "market_regime", "coverage_stable_read_first"]
    )
    component_ok = all(comp.get(name, {}).get("component_status") in {"OK", "PARTIAL"} for name in ["factor_pack", "technical_timing", "price_derived_factors"])
    status = STATUS_OK if core_ok and component_ok and missing_source_count == 0 and degraded_count == 0 else STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": MODE,
        "PATCH_MODE": PATCH_MODE,
        "POLICY_APPLIED": "FALSE",
        "SNAPSHOT_DATE": snapshot_date,
        "SIGNAL_SNAPSHOT_ROW_COUNT": str(len(snapshot_rows)),
        "SIGNAL_SNAPSHOT_HISTORY_COPY_CREATED": str(history_path.exists()).upper(),
        "INPUT_SOURCE_COUNT": str(len(SOURCE_DEFS)),
        "MISSING_INPUT_SOURCE_COUNT": str(missing_source_count),
        "FACTOR_PACK_COVERAGE_COUNT": str(comp.get("factor_pack", {}).get("available_ticker_count", 0)),
        "TECHNICAL_TIMING_COVERAGE_COUNT": str(comp.get("technical_timing", {}).get("available_ticker_count", 0)),
        "PRICE_DERIVED_COVERAGE_COUNT": str(comp.get("price_derived_factors", {}).get("available_ticker_count", 0)),
        "MARKET_REGIME_STATUS": market["market_regime_status"],
        "MARKET_RISK_COEFFICIENT": market["market_risk_coefficient"],
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": coverage["true_5day_unique_coverage_met"],
        "COVERAGE_WINDOW_COMPLETE": coverage["coverage_window_complete"],
        "DAILY_TRUST_LEVEL": coverage["daily_trust_level"],
        "SIMULATION_LINKER_ROW_COUNT": str(len(linker)),
        "READY_FOR_FORWARD_RESEARCH_COUNT": str(ready_forward_count),
        "READY_FOR_SIMULATION_ANALYSIS_COUNT": str(ready_sim_count),
        "DATA_DEGRADED_COUNT": str(degraded_count),
        **SAFETY_FLAGS,
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(read_first_path),
        "REPORT": str(report_path),
    }

    required_fields = [
        "STATUS",
        "MODE",
        "PATCH_MODE",
        "POLICY_APPLIED",
        "SNAPSHOT_DATE",
        "SIGNAL_SNAPSHOT_ROW_COUNT",
        "SIGNAL_SNAPSHOT_HISTORY_COPY_CREATED",
        "INPUT_SOURCE_COUNT",
        "MISSING_INPUT_SOURCE_COUNT",
        "FACTOR_PACK_COVERAGE_COUNT",
        "TECHNICAL_TIMING_COVERAGE_COUNT",
        "PRICE_DERIVED_COVERAGE_COUNT",
        "MARKET_REGIME_STATUS",
        "MARKET_RISK_COEFFICIENT",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET",
        "COVERAGE_WINDOW_COMPLETE",
        "DAILY_TRUST_LEVEL",
        "SIMULATION_LINKER_ROW_COUNT",
        "READY_FOR_FORWARD_RESEARCH_COUNT",
        "READY_FOR_SIMULATION_ANALYSIS_COUNT",
        "DATA_DEGRADED_COUNT",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "CURRENT_DAILY_MODIFIED",
        "STATE_MODIFIED",
        "PRICE_CACHE_MODIFIED",
        "RANKING_MODIFIED",
        "TECHNICAL_TIMING_MODIFIED",
        "PRICE_FACTOR_MODIFIED",
        "SIMULATION_POSITION_MODIFIED",
        "FORWARD_TRACKER_MODIFIED",
        "PROMOTION_DEMOTION_MODIFIED",
        "MANUAL_STATE_MODIFIED",
        "BROKER_EXECUTION_MODIFIED",
        "VALIDATION_FAIL_COUNT",
        "READ_FIRST",
        "REPORT",
    ]

    outputs = {
        "signal_snapshot": snapshot_path,
        "history_snapshot": history_path,
        "source_audit": source_audit_path,
        "component_coverage": coverage_audit_path,
        "simulation_research_linker": linker_path,
        "read_first": read_first_path,
        "report": report_path,
    }
    read_first_text = "\n".join(f"{field}: {values.get(field, '')}" for field in required_fields) + "\n"
    write_text(read_first_path, read_first_text)
    write_text(report_path, report_text(values, source_audit, coverage_rows))

    validation_rows, fail_count = validate_outputs(outputs, values, required_fields)
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        values["STATUS"] = STATUS_WARN

    read_first_text = "\n".join(f"{field}: {values.get(field, '')}" for field in required_fields) + "\n"
    write_text(read_first_path, read_first_text)
    write_text(report_path, report_text(values, source_audit, coverage_rows))

    # Keep validation internal to this run; the requested output set does not include a validation CSV.
    for row in validation_rows:
        if row["status"] != "PASS":
            print(f"VALIDATION_WARNING: {row['validation_check']} {row['notes']}")

    for key in [
        "STATUS",
        "MODE",
        "PATCH_MODE",
        "SNAPSHOT_DATE",
        "SIGNAL_SNAPSHOT_ROW_COUNT",
        "SIGNAL_SNAPSHOT_HISTORY_COPY_CREATED",
        "INPUT_SOURCE_COUNT",
        "MISSING_INPUT_SOURCE_COUNT",
        "FACTOR_PACK_COVERAGE_COUNT",
        "TECHNICAL_TIMING_COVERAGE_COUNT",
        "PRICE_DERIVED_COVERAGE_COUNT",
        "MARKET_REGIME_STATUS",
        "MARKET_RISK_COEFFICIENT",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET",
        "COVERAGE_WINDOW_COMPLETE",
        "SIMULATION_LINKER_ROW_COUNT",
        "READY_FOR_FORWARD_RESEARCH_COUNT",
        "READY_FOR_SIMULATION_ANALYSIS_COUNT",
        "DATA_DEGRADED_COUNT",
        "VALIDATION_FAIL_COUNT",
        "READ_FIRST",
        "REPORT",
    ]:
        print(f"{key}: {values.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
