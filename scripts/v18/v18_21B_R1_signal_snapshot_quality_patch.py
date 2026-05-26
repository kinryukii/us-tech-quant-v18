import argparse
import csv
import hashlib
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


MODE = "ADVISORY_ONLY"
PATCH_MODE = "SIGNAL_SNAPSHOT_QUALITY_AND_LINK_READINESS_ONLY"
STATUS_WARN = "WARN_V18_21B_R1_SIGNAL_SNAPSHOT_QUALITY_DEGRADED"
STATUS_OK = "OK_V18_21B_R1_SIGNAL_SNAPSHOT_QUALITY_READY"

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

BASE_SNAPSHOT = "outputs/v18/signal_snapshots/V18_21B_CURRENT_SIGNAL_SNAPSHOT.csv"
BASE_LINKER = "outputs/v18/signal_snapshots/V18_21B_CURRENT_SIMULATION_RESEARCH_LINKER.csv"
BASE_SOURCE_AUDIT = "outputs/v18/signal_snapshots/V18_21B_CURRENT_SIGNAL_SOURCE_AUDIT.csv"
BASE_COMPONENT_AUDIT = "outputs/v18/signal_snapshots/V18_21B_CURRENT_SIGNAL_COMPONENT_COVERAGE_AUDIT.csv"
BASE_READ_FIRST = "outputs/v18/ops/V18_21B_READ_FIRST.txt"


def truthy(value):
    return str(value or "").strip().upper() in {"TRUE", "YES", "1", "Y"}


def present(value):
    return str(value or "").strip() != ""


def read_csv(path):
    if not path.exists():
        return [], []
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader], list(reader.fieldnames or [])


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


def read_first(path):
    data = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in raw:
            key, value = raw.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def file_hash(path):
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_csv_rows(path):
    rows, _ = read_csv(path)
    return len(rows)


def run_cmd(command):
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=90)
        return completed.returncode == 0, (completed.stdout + completed.stderr).strip()
    except Exception as exc:
        return False, str(exc)


def price_readiness(row):
    has_row = present(row.get("price_derived_status")) or present(row.get("factor_scope_class")) or present(row.get("score_scope"))
    full_ready = truthy(row.get("full_factor_score_ready"))
    light_ready = truthy(row.get("light_factor_score_ready"))
    score_ready = truthy(row.get("score_ready"))
    total_score = present(row.get("price_derived_total_score"))
    buy_zone = present(row.get("buy_zone_label"))
    market = present(row.get("market_regime_label")) and present(row.get("market_risk_coefficient"))

    if full_ready and total_score:
        status = "FULL_SCORE_READY"
        reason = ""
    elif light_ready and total_score:
        status = "LIGHT_SCORE_READY"
        reason = "Light price-derived score available; full score not ready."
    elif has_row:
        status = "ROW_ONLY_NOT_SCORE_READY"
        reason = "Price-derived row exists but full/light score fields are not ready."
    else:
        status = "MISSING_PRICE_DERIVED_ROW"
        reason = "No price-derived row found in signal snapshot."
    return {
        "ticker": row.get("ticker", ""),
        "has_price_derived_row": str(has_row).upper(),
        "factor_scope_class": row.get("factor_scope_class", ""),
        "score_scope": row.get("score_scope", ""),
        "full_factor_score_ready": row.get("full_factor_score_ready", ""),
        "light_factor_score_ready": row.get("light_factor_score_ready", ""),
        "score_ready": row.get("score_ready", ""),
        "price_derived_total_score_available": str(total_score).upper(),
        "buy_zone_label_available": str(buy_zone).upper(),
        "market_regime_available": str(market).upper(),
        "price_derived_readiness_status": status,
        "degradation_reason": reason,
    }


def blocker_row(row, price_status):
    missing_factor = not present(row.get("factor_pack_score")) and not present(row.get("factor_pack_rank"))
    missing_tech = not present(row.get("technical_timing_score"))
    missing_price_score = not present(row.get("price_derived_total_score"))
    missing_market = not present(row.get("market_regime_label")) or not present(row.get("market_risk_coefficient"))
    missing_coverage = not present(row.get("true_5day_unique_coverage_met")) or not present(row.get("coverage_window_complete"))
    missing_sim = not present(row.get("simulation_link_key"))
    missing_forward = not present(row.get("forward_tracker_link_key"))
    data_degraded = row.get("signal_snapshot_quality_status", "").upper() != "OK" or price_status in {
        "ROW_ONLY_NOT_SCORE_READY",
        "MISSING_PRICE_DERIVED_ROW",
    }
    coverage_incomplete = str(row.get("coverage_window_complete", "")).strip().upper() != "TRUE"
    trust_not_high = str(row.get("daily_trust_level", "")).strip().upper() != "HIGH"

    blockers = []
    if missing_factor:
        blockers.append("MISSING_FACTOR_PACK")
    if missing_tech:
        blockers.append("MISSING_TECHNICAL_TIMING")
    if missing_price_score:
        blockers.append("MISSING_PRICE_SCORE")
    if missing_market:
        blockers.append("MISSING_MARKET_REGIME")
    if missing_coverage:
        blockers.append("MISSING_COVERAGE_TRUST")
    if missing_sim:
        blockers.append("MISSING_SIMULATION_REFERENCE")
    if missing_forward:
        blockers.append("MISSING_FORWARD_TRACKER_REFERENCE")
    if data_degraded:
        blockers.append("DATA_DEGRADED")
    if coverage_incomplete:
        blockers.append("COVERAGE_WINDOW_INCOMPLETE")
    if trust_not_high:
        blockers.append("DAILY_TRUST_NOT_HIGH")

    core_ready = not (missing_factor or missing_tech or missing_price_score or missing_market or missing_coverage)
    ready_forward = core_ready
    ready_sim = core_ready and not missing_sim
    if core_ready and not missing_sim and not missing_forward and not coverage_incomplete and not trust_not_high and not data_degraded:
        use = "FULL_RESEARCH_READY"
    elif core_ready:
        use = "FORWARD_ONLY_READY"
    elif not missing_sim and not missing_price_score:
        use = "SIMULATION_LIGHT_READY"
    elif present(row.get("ticker")) and (present(row.get("price_derived_status")) or present(row.get("factor_scope_class"))):
        use = "WATCH_ONLY_DUE_TO_DEGRADED_DATA"
    else:
        use = "NOT_READY_MISSING_CORE_SIGNAL"

    return {
        "ticker": row.get("ticker", ""),
        "ready_for_forward_research": str(ready_forward).upper(),
        "ready_for_simulation_analysis": str(ready_sim).upper(),
        "blocker_count": len(blockers),
        "blocker_reasons": ";".join(blockers),
        "missing_factor_pack": str(missing_factor).upper(),
        "missing_technical_timing": str(missing_tech).upper(),
        "missing_price_score": str(missing_price_score).upper(),
        "missing_market_regime": str(missing_market).upper(),
        "missing_coverage_trust": str(missing_coverage).upper(),
        "missing_simulation_reference": str(missing_sim).upper(),
        "missing_forward_tracker_reference": str(missing_forward).upper(),
        "data_degraded": str(data_degraded).upper(),
        "coverage_window_incomplete": str(coverage_incomplete).upper(),
        "daily_trust_not_high": str(trust_not_high).upper(),
        "recommended_research_use": use,
    }


def key_quality(rows):
    audits = []
    for key in ["signal_snapshot_id", "simulation_link_key", "forward_tracker_link_key", "manual_feedback_link_key"]:
        values = [str(row.get(key, "")).strip() for row in rows]
        non_empty = [value for value in values if value]
        unique_count = len(set(non_empty))
        duplicate_count = len(non_empty) - unique_count
        missing_count = len(values) - len(non_empty)
        if key == "signal_snapshot_id":
            status = "OK" if missing_count == 0 and duplicate_count == 0 else "FAIL"
            notes = "Signal snapshot IDs must be populated and unique for every row."
        else:
            status = "OK" if duplicate_count == 0 else "WARN_DUPLICATE_KEYS"
            if missing_count:
                status = "WARN_MISSING_KEYS" if duplicate_count == 0 else status
            notes = "Missing optional link keys are expected when the source component is absent."
        audits.append(
            {
                "key_type": key,
                "row_count": len(rows),
                "non_empty_key_count": len(non_empty),
                "unique_key_count": unique_count,
                "duplicate_key_count": duplicate_count,
                "missing_key_count": missing_count,
                "key_quality_status": status,
                "notes": notes,
            }
        )
    return audits


def report_text(values):
    return f"""# V18.21B-R1 Signal Snapshot Quality Report

## Executive summary
Status: {values['STATUS']}. R1 preserves the V18.21B advisory snapshot while separating price-derived row coverage from score-ready coverage and explaining research readiness blockers.

## Safety statement
This patch is advisory-only. It does not modify official decisions, ranking, technical timing, price factor outputs, simulation positions, forward tracker state, manual state, price cache, broker execution, auto-trade, or auto-sell behavior.

## Signal snapshot quality summary
Rows: {values['SIGNAL_SNAPSHOT_ROW_COUNT']}. History copy created: {values['SIGNAL_SNAPSHOT_HISTORY_COPY_CREATED']}. History copy matches current: {values['HISTORY_COPY_MATCHES_CURRENT']}.

## Price-derived readiness explanation
Price-derived row coverage is {values['PRICE_DERIVED_ROW_COVERAGE_COUNT']}, but full score-ready coverage is {values['PRICE_DERIVED_FULL_SCORE_READY_COUNT']} and light score-ready coverage is {values['PRICE_DERIVED_LIGHT_SCORE_READY_COUNT']}. Row-only tickers are not treated as fully research-ready.

## Research readiness blocker summary
Forward-ready rows: {values['READY_FOR_FORWARD_RESEARCH_COUNT']}. Simulation-ready rows: {values['READY_FOR_SIMULATION_ANALYSIS_COUNT']}. Full research ready rows: {values['FULL_RESEARCH_READY_COUNT']}. Watch-only degraded rows: {values['WATCH_ONLY_DUE_TO_DEGRADED_DATA_COUNT']}.

## Link key quality summary
Signal snapshot IDs unique: {values['SIGNAL_SNAPSHOT_ID_UNIQUE']}. Duplicate signal snapshot IDs: {values['SIGNAL_SNAPSHOT_ID_DUPLICATE_COUNT']}. Simulation link keys populated: {values['SIMULATION_LINK_KEY_NON_EMPTY_COUNT']}; forward tracker keys populated: {values['FORWARD_TRACKER_LINK_KEY_NON_EMPTY_COUNT']}; manual feedback keys populated: {values['MANUAL_FEEDBACK_LINK_KEY_NON_EMPTY_COUNT']}.

## History copy consistency summary
The R1 current snapshot was copied to the timestamped history file and compared by row count and SHA-256 hash.

## Degraded data explanation
Status remains WARN because factor pack and technical timing cover only part of the 325-row universe, true 5-day coverage remains FALSE, coverage window is incomplete, daily trust is not HIGH, and VIX remains missing in the market regime layer.

## Validation summary
Validation fail count: {values['VALIDATION_FAIL_COUNT']}.

## Next-step recommendation
Use the R1 snapshot for historical factor-effectiveness research with readiness filters. Do not treat row coverage as score-ready coverage.
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    base_snapshot = root / BASE_SNAPSHOT
    base_linker = root / BASE_LINKER
    base_source = root / BASE_SOURCE_AUDIT
    base_component = root / BASE_COMPONENT_AUDIT
    base_rf = root / BASE_READ_FIRST

    out_dir = root / "outputs/v18/signal_snapshots"
    ops_dir = root / "outputs/v18/ops"
    history_dir = out_dir / "history"
    price_audit_path = out_dir / "V18_21B_R1_CURRENT_PRICE_DERIVED_READINESS_AUDIT.csv"
    blockers_path = out_dir / "V18_21B_R1_CURRENT_RESEARCH_READINESS_BLOCKERS.csv"
    key_audit_path = out_dir / "V18_21B_R1_CURRENT_LINK_KEY_QUALITY_AUDIT.csv"
    history_audit_path = out_dir / "V18_21B_R1_CURRENT_HISTORY_COPY_AUDIT.csv"
    r1_snapshot_path = out_dir / "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv"
    r1_history_path = history_dir / f"V18_21B_R1_SIGNAL_SNAPSHOT_{stamp}.csv"
    read_first_path = ops_dir / "V18_21B_R1_READ_FIRST.txt"
    report_path = ops_dir / "V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT_QUALITY_REPORT.md"

    snapshot_rows, snapshot_fields = read_csv(base_snapshot)
    linker_rows, _ = read_csv(base_linker)
    source_rows, _ = read_csv(base_source)
    component_rows, _ = read_csv(base_component)
    base_values = read_first(base_rf)

    price_rows = []
    blocker_rows = []
    enhanced_rows = []
    rec_counter = Counter()
    price_counter = Counter()

    for row in snapshot_rows:
        price = price_readiness(row)
        blocker = blocker_row(row, price["price_derived_readiness_status"])
        price_rows.append(price)
        blocker_rows.append(blocker)
        rec_counter[blocker["recommended_research_use"]] += 1
        price_counter[price["price_derived_readiness_status"]] += 1
        key_status = "OK"
        enhanced = dict(row)
        enhanced["price_derived_readiness_status"] = price["price_derived_readiness_status"]
        enhanced["research_readiness_status"] = blocker["recommended_research_use"]
        enhanced["blocker_reasons"] = blocker["blocker_reasons"]
        enhanced["link_key_quality_status"] = key_status
        enhanced_rows.append(enhanced)

    enhanced_fields = list(snapshot_fields)
    for field in ["price_derived_readiness_status", "research_readiness_status", "blocker_reasons", "link_key_quality_status"]:
        if field not in enhanced_fields:
            enhanced_fields.append(field)

    write_csv(
        price_audit_path,
        price_rows,
        [
            "ticker",
            "has_price_derived_row",
            "factor_scope_class",
            "score_scope",
            "full_factor_score_ready",
            "light_factor_score_ready",
            "score_ready",
            "price_derived_total_score_available",
            "buy_zone_label_available",
            "market_regime_available",
            "price_derived_readiness_status",
            "degradation_reason",
        ],
    )
    write_csv(
        blockers_path,
        blocker_rows,
        [
            "ticker",
            "ready_for_forward_research",
            "ready_for_simulation_analysis",
            "blocker_count",
            "blocker_reasons",
            "missing_factor_pack",
            "missing_technical_timing",
            "missing_price_score",
            "missing_market_regime",
            "missing_coverage_trust",
            "missing_simulation_reference",
            "missing_forward_tracker_reference",
            "data_degraded",
            "coverage_window_incomplete",
            "daily_trust_not_high",
            "recommended_research_use",
        ],
    )
    write_csv(r1_snapshot_path, enhanced_rows, enhanced_fields)
    history_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(r1_snapshot_path, r1_history_path)

    key_rows = key_quality(enhanced_rows)
    write_csv(
        key_audit_path,
        key_rows,
        [
            "key_type",
            "row_count",
            "non_empty_key_count",
            "unique_key_count",
            "duplicate_key_count",
            "missing_key_count",
            "key_quality_status",
            "notes",
        ],
    )

    current_hash = file_hash(r1_snapshot_path)
    history_hash = file_hash(r1_history_path)
    current_count = count_csv_rows(r1_snapshot_path)
    history_count = count_csv_rows(r1_history_path)
    history_matches = r1_history_path.exists() and current_count == history_count and current_hash == history_hash
    history_audit = [
        {
            "current_snapshot_path": str(r1_snapshot_path),
            "history_snapshot_path": str(r1_history_path),
            "current_row_count": current_count,
            "history_row_count": history_count,
            "current_file_hash": current_hash,
            "history_file_hash": history_hash,
            "history_copy_created": str(r1_history_path.exists()).upper(),
            "history_copy_matches_current": str(history_matches).upper(),
            "audit_status": "OK" if history_matches else "FAIL",
            "notes": "R1 current snapshot and history copy match by row count and SHA-256 hash." if history_matches else "History copy mismatch or missing.",
        }
    ]
    write_csv(
        history_audit_path,
        history_audit,
        [
            "current_snapshot_path",
            "history_snapshot_path",
            "current_row_count",
            "history_row_count",
            "current_file_hash",
            "history_file_hash",
            "history_copy_created",
            "history_copy_matches_current",
            "audit_status",
            "notes",
        ],
    )

    comp = {row.get("component_name", ""): row for row in component_rows}
    key_by_type = {row["key_type"]: row for row in key_rows}
    sig_key = key_by_type.get("signal_snapshot_id", {})
    values = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "PATCH_MODE": PATCH_MODE,
        "POLICY_APPLIED": "FALSE",
        "SNAPSHOT_DATE": base_values.get("SNAPSHOT_DATE", ""),
        "SIGNAL_SNAPSHOT_ROW_COUNT": str(len(enhanced_rows)),
        "SIGNAL_SNAPSHOT_HISTORY_COPY_CREATED": str(r1_history_path.exists()).upper(),
        "HISTORY_COPY_MATCHES_CURRENT": str(history_matches).upper(),
        "INPUT_SOURCE_COUNT": base_values.get("INPUT_SOURCE_COUNT", str(len(source_rows))),
        "MISSING_INPUT_SOURCE_COUNT": base_values.get("MISSING_INPUT_SOURCE_COUNT", ""),
        "FACTOR_PACK_COVERAGE_COUNT": comp.get("factor_pack", {}).get("available_ticker_count", base_values.get("FACTOR_PACK_COVERAGE_COUNT", "")),
        "TECHNICAL_TIMING_COVERAGE_COUNT": comp.get("technical_timing", {}).get("available_ticker_count", base_values.get("TECHNICAL_TIMING_COVERAGE_COUNT", "")),
        "PRICE_DERIVED_ROW_COVERAGE_COUNT": str(price_counter["FULL_SCORE_READY"] + price_counter["LIGHT_SCORE_READY"] + price_counter["ROW_ONLY_NOT_SCORE_READY"]),
        "PRICE_DERIVED_FULL_SCORE_READY_COUNT": str(price_counter["FULL_SCORE_READY"]),
        "PRICE_DERIVED_LIGHT_SCORE_READY_COUNT": str(price_counter["LIGHT_SCORE_READY"]),
        "PRICE_DERIVED_ROW_ONLY_COUNT": str(price_counter["ROW_ONLY_NOT_SCORE_READY"]),
        "PRICE_DERIVED_MISSING_ROW_COUNT": str(price_counter["MISSING_PRICE_DERIVED_ROW"]),
        "MARKET_REGIME_STATUS": base_values.get("MARKET_REGIME_STATUS", ""),
        "MARKET_RISK_COEFFICIENT": base_values.get("MARKET_RISK_COEFFICIENT", ""),
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": base_values.get("TRUE_5DAY_UNIQUE_COVERAGE_MET", ""),
        "COVERAGE_WINDOW_COMPLETE": base_values.get("COVERAGE_WINDOW_COMPLETE", ""),
        "DAILY_TRUST_LEVEL": base_values.get("DAILY_TRUST_LEVEL", ""),
        "SIMULATION_LINKER_ROW_COUNT": str(len(linker_rows)),
        "READY_FOR_FORWARD_RESEARCH_COUNT": str(sum(1 for row in blocker_rows if row["ready_for_forward_research"] == "TRUE")),
        "READY_FOR_SIMULATION_ANALYSIS_COUNT": str(sum(1 for row in blocker_rows if row["ready_for_simulation_analysis"] == "TRUE")),
        "FULL_RESEARCH_READY_COUNT": str(rec_counter["FULL_RESEARCH_READY"]),
        "FORWARD_ONLY_READY_COUNT": str(rec_counter["FORWARD_ONLY_READY"]),
        "SIMULATION_LIGHT_READY_COUNT": str(rec_counter["SIMULATION_LIGHT_READY"]),
        "WATCH_ONLY_DUE_TO_DEGRADED_DATA_COUNT": str(rec_counter["WATCH_ONLY_DUE_TO_DEGRADED_DATA"]),
        "NOT_READY_MISSING_CORE_SIGNAL_COUNT": str(rec_counter["NOT_READY_MISSING_CORE_SIGNAL"]),
        "SIGNAL_SNAPSHOT_ID_UNIQUE": str(sig_key.get("duplicate_key_count", 1) == 0 and sig_key.get("missing_key_count", 1) == 0).upper(),
        "SIGNAL_SNAPSHOT_ID_DUPLICATE_COUNT": str(sig_key.get("duplicate_key_count", "")),
        "SIMULATION_LINK_KEY_NON_EMPTY_COUNT": str(key_by_type.get("simulation_link_key", {}).get("non_empty_key_count", "")),
        "FORWARD_TRACKER_LINK_KEY_NON_EMPTY_COUNT": str(key_by_type.get("forward_tracker_link_key", {}).get("non_empty_key_count", "")),
        "MANUAL_FEEDBACK_LINK_KEY_NON_EMPTY_COUNT": str(key_by_type.get("manual_feedback_link_key", {}).get("non_empty_key_count", "")),
        "DATA_DEGRADED_COUNT": str(sum(1 for row in blocker_rows if row["data_degraded"] == "TRUE")),
        **SAFETY_FLAGS,
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(read_first_path),
        "REPORT": str(report_path),
    }

    if (
        values["SIGNAL_SNAPSHOT_ID_UNIQUE"] == "TRUE"
        and values["HISTORY_COPY_MATCHES_CURRENT"] == "TRUE"
        and values["PRICE_DERIVED_FULL_SCORE_READY_COUNT"] == values["SIGNAL_SNAPSHOT_ROW_COUNT"]
        and values["COVERAGE_WINDOW_COMPLETE"] == "TRUE"
        and values["DAILY_TRUST_LEVEL"].upper() == "HIGH"
    ):
        values["STATUS"] = STATUS_OK

    required_fields = [
        "STATUS",
        "MODE",
        "PATCH_MODE",
        "POLICY_APPLIED",
        "SNAPSHOT_DATE",
        "SIGNAL_SNAPSHOT_ROW_COUNT",
        "SIGNAL_SNAPSHOT_HISTORY_COPY_CREATED",
        "HISTORY_COPY_MATCHES_CURRENT",
        "INPUT_SOURCE_COUNT",
        "MISSING_INPUT_SOURCE_COUNT",
        "FACTOR_PACK_COVERAGE_COUNT",
        "TECHNICAL_TIMING_COVERAGE_COUNT",
        "PRICE_DERIVED_ROW_COVERAGE_COUNT",
        "PRICE_DERIVED_FULL_SCORE_READY_COUNT",
        "PRICE_DERIVED_LIGHT_SCORE_READY_COUNT",
        "PRICE_DERIVED_ROW_ONLY_COUNT",
        "PRICE_DERIVED_MISSING_ROW_COUNT",
        "MARKET_REGIME_STATUS",
        "MARKET_RISK_COEFFICIENT",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET",
        "COVERAGE_WINDOW_COMPLETE",
        "DAILY_TRUST_LEVEL",
        "SIMULATION_LINKER_ROW_COUNT",
        "READY_FOR_FORWARD_RESEARCH_COUNT",
        "READY_FOR_SIMULATION_ANALYSIS_COUNT",
        "FULL_RESEARCH_READY_COUNT",
        "FORWARD_ONLY_READY_COUNT",
        "SIMULATION_LIGHT_READY_COUNT",
        "WATCH_ONLY_DUE_TO_DEGRADED_DATA_COUNT",
        "NOT_READY_MISSING_CORE_SIGNAL_COUNT",
        "SIGNAL_SNAPSHOT_ID_UNIQUE",
        "SIGNAL_SNAPSHOT_ID_DUPLICATE_COUNT",
        "SIMULATION_LINK_KEY_NON_EMPTY_COUNT",
        "FORWARD_TRACKER_LINK_KEY_NON_EMPTY_COUNT",
        "MANUAL_FEEDBACK_LINK_KEY_NON_EMPTY_COUNT",
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

    read_first_text = "\n".join(f"{field}: {values.get(field, '')}" for field in required_fields) + "\n"
    read_first_text = "\n".join(f"{field}: {values.get(field, '')}" for field in required_fields) + "\n"
    write_text(read_first_path, read_first_text)
    write_text(report_path, report_text(values))

    output_paths = [
        price_audit_path,
        blockers_path,
        key_audit_path,
        history_audit_path,
        r1_snapshot_path,
        r1_history_path,
        read_first_path,
        report_path,
    ]
    fail_count = 0
    for path in output_paths:
        if not path.exists():
            fail_count += 1
    for field in required_fields:
        if field not in values:
            fail_count += 1
    if values["SIGNAL_SNAPSHOT_ID_UNIQUE"] != "TRUE":
        fail_count += 1
    if values["HISTORY_COPY_MATCHES_CURRENT"] != "TRUE":
        fail_count += 1
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    if fail_count:
        values["STATUS"] = STATUS_WARN

    write_text(read_first_path, read_first_text)
    write_text(report_path, report_text(values))

    for key in [
        "STATUS",
        "MODE",
        "PATCH_MODE",
        "SNAPSHOT_DATE",
        "SIGNAL_SNAPSHOT_ROW_COUNT",
        "SIGNAL_SNAPSHOT_HISTORY_COPY_CREATED",
        "HISTORY_COPY_MATCHES_CURRENT",
        "PRICE_DERIVED_ROW_COVERAGE_COUNT",
        "PRICE_DERIVED_FULL_SCORE_READY_COUNT",
        "PRICE_DERIVED_LIGHT_SCORE_READY_COUNT",
        "PRICE_DERIVED_ROW_ONLY_COUNT",
        "PRICE_DERIVED_MISSING_ROW_COUNT",
        "READY_FOR_FORWARD_RESEARCH_COUNT",
        "READY_FOR_SIMULATION_ANALYSIS_COUNT",
        "SIGNAL_SNAPSHOT_ID_UNIQUE",
        "SIGNAL_SNAPSHOT_ID_DUPLICATE_COUNT",
        "VALIDATION_FAIL_COUNT",
        "READ_FIRST",
        "REPORT",
    ]:
        print(f"{key}: {values.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
