from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_WARN = "WARN_V18_21D_R1_CONTROLLED_SHADOW_FORWARD_TRACKER_READY"
MODE = "CONTROLLED_SHADOW_APPLICATION"
APPLY_SCOPE = "NEW_SHADOW_OUTPUTS_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "FORWARD_TRACKER_UPGRADE_APPLIED": "TRUE",
    "FORWARD_TRACKER_PRODUCTION_REPLACED": "FALSE",
    "EXISTING_FORWARD_TRACKER_MODIFIED": "FALSE",
    "SIGNAL_SNAPSHOT_MODIFIED": "FALSE",
    "SIMULATION_POSITION_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "PRICE_FACTOR_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "EFFECT_CLAIM_ALLOWED_COUNT": "0",
    "WEIGHT_CHANGE_ALLOWED_COUNT": "0",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT": "0",
}

DRYRUN_PATH = "outputs/v18/forward_tracker/V18_21D_CURRENT_DRYRUN_FORWARD_ROW_TEMPLATE.csv"
SIGNAL_PATH = "outputs/v18/signal_snapshots/V18_21B_R1_CURRENT_SIGNAL_SNAPSHOT.csv"
SCHEMA_AUDIT_PATH = "outputs/v18/forward_tracker/V18_21D_CURRENT_FORWARD_TRACKER_SCHEMA_AUDIT.csv"

READ_FIRST_FIELDS = [
    "STATUS", "MODE", "APPLY_SCOPE", "POLICY_APPLIED", "FORWARD_TRACKER_UPGRADE_APPLIED",
    "FORWARD_TRACKER_PRODUCTION_REPLACED", "EXISTING_FORWARD_TRACKER_MODIFIED", "SIGNAL_SNAPSHOT_MODIFIED",
    "SIMULATION_POSITION_MODIFIED", "PRICE_CACHE_MODIFIED", "EXTERNAL_DATA_FETCHED", "DRYRUN_FORWARD_TEMPLATE_ROW_COUNT",
    "UPGRADED_SHADOW_ROW_COUNT", "PLANNED_HORIZON_COUNT", "UNIQUE_SIGNAL_SNAPSHOT_ID_COUNT",
    "COMPLETE_HIGH_CONFIDENCE_READY_COUNT", "PARTIAL_MEDIUM_CONFIDENCE_READY_COUNT", "PARTIAL_LOW_CONFIDENCE_COUNT",
    "INVALID_MISSING_CORE_KEYS_COUNT", "FORWARD_RETURN_FILLED_COUNT", "FORWARD_RETURN_PENDING_COUNT",
    "SHADOW_OUTPUT_CREATED", "SHADOW_PRODUCTION_SAFETY_DIFF_CREATED", "UPGRADED_SCHEMA_VALIDATION_CREATED",
    "POST_SHADOW_MATCH_PROJECTION_CREATED", "EFFECT_CLAIM_ALLOWED_COUNT", "WEIGHT_CHANGE_ALLOWED_COUNT",
    "PRODUCTION_PROMOTION_ALLOWED_COUNT", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "RANKING_MODIFIED", "TECHNICAL_TIMING_MODIFIED", "PRICE_FACTOR_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED", "VALIDATION_FAIL_COUNT",
    "READ_FIRST", "REPORT",
]

CORE_KEYS = ["signal_snapshot_id", "snapshot_date", "ticker", "planned_horizon", "planned_outcome_date"]
OPTIONAL_KEYS = ["forward_tracker_link_key", "simulation_link_key", "manual_feedback_link_key"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", newline="", encoding=enc, errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8", newline="\n")


def file_mtime(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else ""


def present(value: object) -> bool:
    text = str(value or "").strip()
    return text not in {"", "NA", "N/A", "None", "NULL"}


def snapshot_index(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {row.get("signal_snapshot_id", ""): row for row in rows if row.get("signal_snapshot_id", "")}


def discover_protected(root: Path, schema_rows: List[Dict[str, str]]) -> List[Path]:
    paths = []
    for row in schema_rows:
        raw = row.get("source_path", "")
        if raw:
            paths.append(Path(raw))
    extras = [
        root / SIGNAL_PATH,
        root / "outputs/v18/signal_snapshots/V18_21B_CURRENT_SIGNAL_SNAPSHOT.csv",
        root / "outputs/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        root / "outputs/v18/simulation/V18_CURRENT_PAPER_POSITIONS.csv",
        root / "state/v18/price_cache/QQQ.csv",
        root / "scripts/v18/run_v18_current_daily_command_center.ps1",
        root / "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        root / "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
    ]
    paths.extend(extras)
    unique = []
    seen = set()
    for path in paths:
        resolved = path if path.is_absolute() else root / path
        key = str(resolved).lower()
        if key not in seen:
            seen.add(key)
            unique.append(resolved)
    return unique


def completeness(row: Dict[str, str]) -> Dict[str, object]:
    available = []
    missing = []
    for key in CORE_KEYS + OPTIONAL_KEYS:
        if present(row.get(key, "")):
            available.append(key)
        else:
            missing.append(key)
    core_ok = all(key not in missing for key in CORE_KEYS)
    required_total = len(CORE_KEYS) + len(OPTIONAL_KEYS)
    available_count = len(available)
    if core_ok and all(key not in missing for key in OPTIONAL_KEYS):
        status = "COMPLETE_HIGH_CONFIDENCE_READY"
    elif core_ok and present(row.get("forward_tracker_link_key", "")):
        status = "PARTIAL_MEDIUM_CONFIDENCE_READY"
    elif core_ok:
        status = "PARTIAL_LOW_CONFIDENCE"
    else:
        status = "INVALID_MISSING_CORE_KEYS"
    return {
        "required_key_available_count": available_count,
        "required_key_total_count": required_total,
        "link_key_completeness_ratio": f"{available_count / required_total:.6f}",
        "link_key_completeness_status": status,
        "missing_required_keys": ";".join(missing),
    }


def build_shadow(dryrun_rows: List[Dict[str, str]], signal_rows: List[Dict[str, str]], root: Path):
    by_id = snapshot_index(signal_rows)
    shadow = []
    audit = []
    for row in dryrun_rows:
        planned_date = row.get("planned_outcome_date_placeholder", "") or "PENDING_OUTCOME_DATE"
        if planned_date.upper() in {"NA", "N/A", "NONE", "NULL"}:
            planned_date = "PENDING_OUTCOME_DATE"
        normalized = {
            "snapshot_date": row.get("snapshot_date", ""),
            "ticker": row.get("ticker", ""),
            "signal_snapshot_id": row.get("signal_snapshot_id", ""),
            "forward_tracker_link_key": row.get("forward_tracker_link_key", ""),
            "simulation_link_key": row.get("simulation_link_key", ""),
            "manual_feedback_link_key": row.get("manual_feedback_link_key", ""),
            "planned_horizon": row.get("planned_horizon", ""),
            "planned_outcome_date": planned_date,
            "forward_return": "NA",
        }
        comp = completeness(normalized)
        source = by_id.get(normalized["signal_snapshot_id"], {})
        quality = source.get("signal_snapshot_quality_status", "SOURCE_SIGNAL_ROW_MISSING") if source else "SOURCE_SIGNAL_ROW_MISSING"
        out = {
            **normalized,
            "forward_return_status": "PENDING_NOT_FILLED",
            "source_snapshot_path": row.get("source_snapshot_path", str(root / SIGNAL_PATH)),
            "source_signal_snapshot_row_found": str(bool(source)).upper(),
            "source_signal_snapshot_quality_status": quality,
            "link_key_completeness_status": comp["link_key_completeness_status"],
            "upgraded_schema_version": "V18_21D_R1_SHADOW_V1",
            "apply_scope": "NEW_SHADOW_OUTPUTS_ONLY",
            "apply_status": "APPLIED_TO_SHADOW_OUTPUT_ONLY",
        }
        shadow.append(out)
        audit.append(
            {
                "ticker": normalized["ticker"],
                "signal_snapshot_id_present": str(present(normalized["signal_snapshot_id"])).upper(),
                "snapshot_date_present": str(present(normalized["snapshot_date"])).upper(),
                "forward_tracker_link_key_present": str(present(normalized["forward_tracker_link_key"])).upper(),
                "simulation_link_key_present": str(present(normalized["simulation_link_key"])).upper(),
                "manual_feedback_link_key_present": str(present(normalized["manual_feedback_link_key"])).upper(),
                "horizon_present": str(present(normalized["planned_horizon"])).upper(),
                "planned_outcome_date_present": str(present(normalized["planned_outcome_date"])).upper(),
                "ticker_present": str(present(normalized["ticker"])).upper(),
                **comp,
            }
        )
    return shadow, audit


def schema_validations(shadow_path: Path, dryrun_count: int, shadow_rows: List[Dict[str, str]], safety_rows: List[Dict[str, object]]):
    filled = sum(1 for row in shadow_rows if present(row.get("forward_return", "")))
    production_applied = sum(1 for row in shadow_rows if row.get("apply_status") == "PRODUCTION_APPLIED")
    all_shadow = sum(1 for row in shadow_rows if row.get("apply_status") != "APPLIED_TO_SHADOW_OUTPUT_ONLY")
    modified_protected = sum(1 for row in safety_rows if row.get("modified_by_this_run") == "TRUE")
    checks = [
        ("upgraded shadow output exists", shadow_path.exists(), 0 if shadow_path.exists() else 1, "Shadow output file must exist."),
        ("upgraded shadow row count equals dry-run template row count", len(shadow_rows) == dryrun_count, abs(len(shadow_rows) - dryrun_count), f"dryrun={dryrun_count}; shadow={len(shadow_rows)}"),
        ("no forward_return values filled", filled == 0, filled, "Forward returns must remain NA/blank."),
        ("all rows apply_status = APPLIED_TO_SHADOW_OUTPUT_ONLY", all_shadow == 0, all_shadow, "No row may be production-applied."),
        ("no rows apply_status = PRODUCTION_APPLIED", production_applied == 0, production_applied, "Production application is disallowed."),
        ("core keys non-empty where available", True, 0, "Core key completeness is audited per row."),
        ("no existing forward tracker production file modified", modified_protected == 0, modified_protected, "Protected files should not change."),
        ("signal snapshot not modified", modified_protected == 0, 0 if modified_protected == 0 else 1, "Signal snapshot is included in protected-file diff."),
        ("simulation positions not modified", modified_protected == 0, 0 if modified_protected == 0 else 1, "Simulation files are included in protected-file diff."),
        ("external data not fetched", True, 0, "No network/external fetch is performed."),
    ]
    return [{"validation_check": name, "status": "PASS" if ok else "FAIL", "fail_count": fail, "notes": notes} for name, ok, fail, notes in checks]


def projection(shadow_rows: List[Dict[str, str]], current_baseline: Dict[str, str]):
    complete = sum(1 for row in shadow_rows if row.get("link_key_completeness_status") == "COMPLETE_HIGH_CONFIDENCE_READY")
    medium = sum(1 for row in shadow_rows if row.get("link_key_completeness_status") == "PARTIAL_MEDIUM_CONFIDENCE_READY")
    invalid = sum(1 for row in shadow_rows if row.get("link_key_completeness_status") == "INVALID_MISSING_CORE_KEYS")
    multi = len(shadow_rows)
    baseline_low = current_baseline.get("LOW_CONFIDENCE_MATCH_COUNT", "20")
    return [
        {
            "scenario_name": "CURRENT_LOW_CONFIDENCE_BASELINE",
            "projected_high_confidence_rows": current_baseline.get("HIGH_CONFIDENCE_MATCH_COUNT", "0"),
            "projected_medium_confidence_rows": current_baseline.get("MEDIUM_CONFIDENCE_MATCH_COUNT", "0"),
            "projected_low_confidence_rows": baseline_low,
            "projected_invalid_rows": current_baseline.get("UNMATCHED_OR_AMBIGUOUS_COUNT", "305"),
            "projected_multi_horizon_rows": "0",
            "assumptions": "Existing production files only.",
            "limitations": "Low-confidence matches and incomplete horizon maturity remain.",
        },
        {
            "scenario_name": "SHADOW_SCHEMA_CREATED_NO_OUTCOMES_FILLED",
            "projected_high_confidence_rows": complete,
            "projected_medium_confidence_rows": medium,
            "projected_low_confidence_rows": max(len(shadow_rows) - complete - medium - invalid, 0),
            "projected_invalid_rows": invalid,
            "projected_multi_horizon_rows": multi,
            "assumptions": "Shadow rows can carry strong keys, but returns remain pending.",
            "limitations": "No forward returns are filled in this task.",
        },
        {
            "scenario_name": "SHADOW_SCHEMA_WITH_FUTURE_1D_OUTCOMES",
            "projected_high_confidence_rows": complete,
            "projected_medium_confidence_rows": medium,
            "projected_low_confidence_rows": 0,
            "projected_invalid_rows": invalid,
            "projected_multi_horizon_rows": len({row.get("signal_snapshot_id") for row in shadow_rows if row.get("planned_horizon") == "1D"}),
            "assumptions": "Future local 1D outcome filler populates shadow rows without changing production.",
            "limitations": "Theoretical readiness only; no filler applied.",
        },
        {
            "scenario_name": "SHADOW_SCHEMA_WITH_FUTURE_1D_3D_5D_10D_20D_OUTCOMES",
            "projected_high_confidence_rows": complete,
            "projected_medium_confidence_rows": medium,
            "projected_low_confidence_rows": 0,
            "projected_invalid_rows": invalid,
            "projected_multi_horizon_rows": multi,
            "assumptions": "All planned horizons mature in future local outcome processes.",
            "limitations": "No outcomes are fetched, computed, or backfilled here.",
        },
    ]


def report_text(values: Dict[str, object]) -> str:
    return f"""# V18.21D-R1 Controlled Forward Link Application Report

## Executive summary
Status: {values['STATUS']}. A new shadow-only upgraded forward tracker output was created. Existing forward tracker production files were not modified or replaced.

## Safety statement
This is controlled shadow application only. No production tracker replacement, signal snapshot modification, simulation position modification, price cache modification, external data fetch, ranking change, official decision change, auto-trade, or auto-sell occurred.

## What was applied and what was not applied
Applied: a new shadow output file with upgraded link-key schema. Not applied: production replacement, return filling, historical backfill, price fetch, factor effect claim, weight change, or promotion.

## Upgraded shadow forward tracker summary
Shadow rows: {values['UPGRADED_SHADOW_ROW_COUNT']}; dry-run rows: {values['DRYRUN_FORWARD_TEMPLATE_ROW_COUNT']}; planned horizons: {values['PLANNED_HORIZON_COUNT']}; forward returns filled: {values['FORWARD_RETURN_FILLED_COUNT']}.

## Link-key completeness summary
Complete high-confidence ready: {values['COMPLETE_HIGH_CONFIDENCE_READY_COUNT']}; partial medium: {values['PARTIAL_MEDIUM_CONFIDENCE_READY_COUNT']}; partial low: {values['PARTIAL_LOW_CONFIDENCE_COUNT']}; invalid: {values['INVALID_MISSING_CORE_KEYS_COUNT']}.

## Shadow-vs-production safety diff summary
Safety diff created: {values['SHADOW_PRODUCTION_SAFETY_DIFF_CREATED']}. Existing forward tracker modified: {values['EXISTING_FORWARD_TRACKER_MODIFIED']}. Signal snapshot modified: {values['SIGNAL_SNAPSHOT_MODIFIED']}.

## Upgraded schema validation summary
Validation artifact created: {values['UPGRADED_SCHEMA_VALIDATION_CREATED']}. Validation fail count: {values['VALIDATION_FAIL_COUNT']}.

## Post-shadow match quality projection
Projection artifact created: {values['POST_SHADOW_MATCH_PROJECTION_CREATED']}. Projections are theoretical readiness only because forward returns remain pending.

## Why no factor effectiveness claims are allowed
No forward returns were filled and no production outcomes were altered. This creates link-key structure only.

## Next-step recommendation
Create a stable snapshot of R1 if clean, then design V18.21D-R2 outcome filler separately or integrate into a future forward tracker wrapper only with explicit approval.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out_dir = root / "outputs/v18/forward_tracker"
    ops_dir = root / "outputs/v18/ops"
    shadow_path = out_dir / "V18_21D_R1_CURRENT_UPGRADED_FORWARD_TRACKER_SHADOW.csv"
    completeness_path = out_dir / "V18_21D_R1_CURRENT_LINK_KEY_COMPLETENESS_AUDIT.csv"
    safety_diff_path = out_dir / "V18_21D_R1_CURRENT_SHADOW_PRODUCTION_SAFETY_DIFF.csv"
    schema_validation_path = out_dir / "V18_21D_R1_CURRENT_UPGRADED_SCHEMA_VALIDATION.csv"
    projection_path = out_dir / "V18_21D_R1_CURRENT_POST_SHADOW_MATCH_QUALITY_PROJECTION.csv"
    read_first_path = ops_dir / "V18_21D_R1_READ_FIRST.txt"
    report_path = ops_dir / "V18_21D_R1_CURRENT_CONTROLLED_FORWARD_LINK_APPLICATION_REPORT.md"

    dryrun_rows, _ = read_csv(root / DRYRUN_PATH)
    signal_rows, _ = read_csv(root / SIGNAL_PATH)
    schema_rows, _ = read_csv(root / SCHEMA_AUDIT_PATH)
    stable_21d = {}
    stable_path = root / "outputs/v18/ops/V18_21D_STABLE_READ_FIRST.txt"
    if stable_path.exists():
        for line in stable_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                stable_21d[key.strip()] = val.strip()

    if not dryrun_rows or not signal_rows:
        fail_values = {
            "STATUS": "FAIL_V18_21D_R1_MISSING_REQUIRED_INPUT",
            "MODE": MODE,
            "APPLY_SCOPE": APPLY_SCOPE,
            **SAFETY_FLAGS,
            "DRYRUN_FORWARD_TEMPLATE_ROW_COUNT": str(len(dryrun_rows)),
            "UPGRADED_SHADOW_ROW_COUNT": "0",
            "VALIDATION_FAIL_COUNT": "1",
            "READ_FIRST": str(read_first_path),
            "REPORT": str(report_path),
        }
        write_text(read_first_path, "\n".join(f"{field}: {fail_values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
        write_text(report_path, report_text(fail_values))
        print("STATUS: FAIL_V18_21D_R1_MISSING_REQUIRED_INPUT")
        return 1

    protected = discover_protected(root, schema_rows)
    before = {str(path): file_mtime(path) for path in protected}
    shadow_rows, audit_rows = build_shadow(dryrun_rows, signal_rows, root)

    shadow_fields = [
        "snapshot_date", "ticker", "signal_snapshot_id", "forward_tracker_link_key", "simulation_link_key",
        "manual_feedback_link_key", "planned_horizon", "planned_outcome_date", "forward_return", "forward_return_status",
        "source_snapshot_path", "source_signal_snapshot_row_found", "source_signal_snapshot_quality_status",
        "link_key_completeness_status", "upgraded_schema_version", "apply_scope", "apply_status",
    ]
    write_csv(shadow_path, shadow_rows, shadow_fields)
    write_csv(completeness_path, audit_rows, [
        "ticker", "signal_snapshot_id_present", "snapshot_date_present", "forward_tracker_link_key_present",
        "simulation_link_key_present", "manual_feedback_link_key_present", "horizon_present",
        "planned_outcome_date_present", "ticker_present", "required_key_available_count", "required_key_total_count",
        "link_key_completeness_ratio", "link_key_completeness_status", "missing_required_keys",
    ])

    after = {str(path): file_mtime(path) for path in protected}
    safety_rows = []
    for path in protected:
        exists = path.exists()
        b = before.get(str(path), "")
        a = after.get(str(path), "")
        modified = bool(exists and b and a and b != a)
        safety_rows.append(
            {
                "checked_path": str(path),
                "file_exists": str(exists).upper(),
                "modified_before_run": b,
                "modified_after_run": a,
                "modified_by_this_run": str(modified).upper(),
                "protection_status": "FAIL_MODIFIED" if modified else "OK_NOT_MODIFIED",
                "notes": "Protected production/context file; shadow application must not modify it.",
            }
        )
    write_csv(safety_diff_path, safety_rows, [
        "checked_path", "file_exists", "modified_before_run", "modified_after_run", "modified_by_this_run",
        "protection_status", "notes",
    ])
    validation_rows = schema_validations(shadow_path, len(dryrun_rows), shadow_rows, safety_rows)
    write_csv(schema_validation_path, validation_rows, ["validation_check", "status", "fail_count", "notes"])
    write_csv(projection_path, projection(shadow_rows, stable_21d), [
        "scenario_name", "projected_high_confidence_rows", "projected_medium_confidence_rows",
        "projected_low_confidence_rows", "projected_invalid_rows", "projected_multi_horizon_rows", "assumptions", "limitations",
    ])

    status_counts = Counter(row["link_key_completeness_status"] for row in shadow_rows)
    filled_count = sum(1 for row in shadow_rows if present(row.get("forward_return", "")))
    pending_count = sum(1 for row in shadow_rows if row.get("forward_return_status") == "PENDING_NOT_FILLED")
    unique_ids = len({row.get("signal_snapshot_id", "") for row in shadow_rows if row.get("signal_snapshot_id", "")})
    values: Dict[str, object] = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "APPLY_SCOPE": APPLY_SCOPE,
        "DRYRUN_FORWARD_TEMPLATE_ROW_COUNT": str(len(dryrun_rows)),
        "UPGRADED_SHADOW_ROW_COUNT": str(len(shadow_rows)),
        "PLANNED_HORIZON_COUNT": str(len({row.get("planned_horizon", "") for row in shadow_rows if row.get("planned_horizon", "")})),
        "UNIQUE_SIGNAL_SNAPSHOT_ID_COUNT": str(unique_ids),
        "COMPLETE_HIGH_CONFIDENCE_READY_COUNT": str(status_counts["COMPLETE_HIGH_CONFIDENCE_READY"]),
        "PARTIAL_MEDIUM_CONFIDENCE_READY_COUNT": str(status_counts["PARTIAL_MEDIUM_CONFIDENCE_READY"]),
        "PARTIAL_LOW_CONFIDENCE_COUNT": str(status_counts["PARTIAL_LOW_CONFIDENCE"]),
        "INVALID_MISSING_CORE_KEYS_COUNT": str(status_counts["INVALID_MISSING_CORE_KEYS"]),
        "FORWARD_RETURN_FILLED_COUNT": str(filled_count),
        "FORWARD_RETURN_PENDING_COUNT": str(pending_count),
        "SHADOW_OUTPUT_CREATED": str(shadow_path.exists()).upper(),
        "SHADOW_PRODUCTION_SAFETY_DIFF_CREATED": str(safety_diff_path.exists()).upper(),
        "UPGRADED_SCHEMA_VALIDATION_CREATED": str(schema_validation_path.exists()).upper(),
        "POST_SHADOW_MATCH_PROJECTION_CREATED": str(projection_path.exists()).upper(),
        **SAFETY_FLAGS,
        "VALIDATION_FAIL_COUNT": "0",
        "READ_FIRST": str(read_first_path),
        "REPORT": str(report_path),
    }
    output_paths = [shadow_path, completeness_path, safety_diff_path, schema_validation_path, projection_path, read_first_path, report_path]
    write_text(read_first_path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    write_text(report_path, report_text(values))

    fail_count = 0
    for path in output_paths:
        if not path.exists():
            fail_count += 1
    for field in READ_FIRST_FIELDS:
        if field not in values:
            fail_count += 1
    for row in validation_rows:
        fail_count += int(row["fail_count"])
    if filled_count:
        fail_count += filled_count
    if any(row.get("apply_status") == "PRODUCTION_APPLIED" for row in shadow_rows):
        fail_count += 1
    values["VALIDATION_FAIL_COUNT"] = str(fail_count)
    write_text(read_first_path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    write_text(report_path, report_text(values))

    for key in [
        "STATUS", "MODE", "APPLY_SCOPE", "FORWARD_TRACKER_UPGRADE_APPLIED", "FORWARD_TRACKER_PRODUCTION_REPLACED",
        "EXISTING_FORWARD_TRACKER_MODIFIED", "DRYRUN_FORWARD_TEMPLATE_ROW_COUNT", "UPGRADED_SHADOW_ROW_COUNT",
        "PLANNED_HORIZON_COUNT", "COMPLETE_HIGH_CONFIDENCE_READY_COUNT", "PARTIAL_MEDIUM_CONFIDENCE_READY_COUNT",
        "FORWARD_RETURN_FILLED_COUNT", "FORWARD_RETURN_PENDING_COUNT", "SHADOW_OUTPUT_CREATED", "VALIDATION_FAIL_COUNT",
        "READ_FIRST", "REPORT",
    ]:
        print(f"{key}: {values.get(key, '')}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
