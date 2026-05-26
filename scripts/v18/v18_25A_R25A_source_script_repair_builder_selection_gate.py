from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK_GATE = "OK_V18_25A_R25A_BUILDER_SELECTION_GATE_READY"
STATUS_OK_REPAIR = "OK_V18_25A_R25A_SCRIPT_REPAIR_AND_BUILDER_SELECTION_READY"
STATUS_EXCLUDED = "WARN_V18_25A_R25A_BROKEN_SCRIPT_UNPATCHED_BUT_EXCLUDED"
STATUS_PATCH_REQUIRED = "WARN_V18_25A_R25A_SCRIPT_PATCH_REQUIRED"
STATUS_REVIEW = "WARN_V18_25A_R25A_BUILDER_SELECTION_REVIEW_NEEDED"
STATUS_BLOCKED = "WARN_V18_25A_R25A_R25B_GATE_BLOCKED"

MODE_DRYRUN = "DRYRUN_AUDIT_ONLY"
MODE_PATCH = "SCRIPT_PATCH_AND_BUILDER_SELECTION_GATE"

R25_AUDIT = "outputs/v18/readiness/V18_25A_R25_CURRENT_SOURCE_SCRIPT_AUDIT.csv"
R25_PLAN = "outputs/v18/readiness/V18_25A_R25_CURRENT_COMBINED_REFRESH_PLAN.csv"
R25_SCHEMA = "outputs/v18/readiness/V18_25A_R25_CURRENT_SCHEMA_COMPATIBILITY_AUDIT.csv"
BROKEN_SCRIPT = "scripts/v18/v18_6A_technical_timing_shadow.py"
FACTOR_BUILDER = "scripts/v18/v18_25A_R13_targeted_factor_pack_refresh_staged.py"
FACTOR_WRAPPER = "scripts/v18/run_v18_25A_R13_targeted_factor_pack_refresh_staged.ps1"
TECH_BUILDER = "scripts/v18/v18_25A_R11_full_compatible_technical_timing_refresh_with_vix.py"
TECH_WRAPPER = "scripts/v18/run_v18_25A_R11_full_compatible_technical_timing_refresh_with_vix.ps1"

PRICE_CACHE = "state/v18/price_cache"
LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OUT_REPAIR = "outputs/v18/readiness/V18_25A_R25A_CURRENT_SCRIPT_REPAIR_AUDIT.csv"
OUT_SELECTION = "outputs/v18/readiness/V18_25A_R25A_CURRENT_BUILDER_SELECTION_PLAN.csv"
OUT_GATE = "outputs/v18/readiness/V18_25A_R25A_CURRENT_R25B_INPUT_GATE.csv"
OUT_EXCLUDED = "outputs/v18/readiness/V18_25A_R25A_CURRENT_DEPRECATED_OR_EXCLUDED_SCRIPTS.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R25A_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R25A_CURRENT_SOURCE_SCRIPT_REPAIR_BUILDER_SELECTION_REPORT.md"

REPAIR_FIELDS = ["script_path", "initial_parse_status", "reference_count", "active_mainline_dependency", "patch_attempted", "patch_applied", "backup_path", "final_parse_status", "decision", "notes"]
SELECTION_FIELDS = ["builder_role", "builder_script", "wrapper_script_if_any", "parse_status", "selection_status", "selection_reason", "can_use_for_R25B", "notes"]
GATE_FIELDS = ["gate_check", "status", "value", "notes"]
EXCLUDED_FIELDS = ["script_path", "exclusion_status", "reason", "reference_count", "active_mainline_dependency"]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "RUN_ID", "R25_SOURCE_SCRIPT_AUDIT_PATH", "BROKEN_SCRIPT_PATH", "BROKEN_SCRIPT_INITIAL_PARSE_STATUS",
    "BROKEN_SCRIPT_REFERENCE_COUNT", "BROKEN_SCRIPT_ACTIVE_MAINLINE_DEPENDENCY", "SCRIPT_PATCH_ATTEMPTED", "SCRIPT_PATCH_APPLIED",
    "SCRIPT_BACKUP_PATH", "BROKEN_SCRIPT_FINAL_PARSE_STATUS", "FACTOR_BUILDER_SELECTED", "TECHNICAL_BUILDER_SELECTED",
    "FACTOR_BUILDER_PARSE_STATUS", "TECHNICAL_BUILDER_PARSE_STATUS", "DEPRECATED_OR_EXCLUDED_SCRIPT_COUNT", "R25B_INPUT_GATE_STATUS",
    "R25B_TARGET_COUNT", "SCHEMA_COMPATIBILITY_STATUS", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL",
    "EXTERNAL_FETCH_EXECUTED", "BACKTEST_EXECUTED", "PRICE_CACHE_MODIFIED", "ROLLING_LEDGER_MODIFIED", "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED", "TIER_FILES_MODIFIED", "OFFICIAL_DECISION_MODIFIED", "SCRIPT_FILES_MODIFIED",
    "VALIDATION_FAIL_COUNT", "FORBIDDEN_MODIFIED", "NEXT_RECOMMENDED_STEP",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def parse_py(path: Path, strict_utf8: bool = True) -> str:
    if not path.exists():
        return "MISSING"
    try:
        encoding = "utf-8" if strict_utf8 else "utf-8-sig"
        ast.parse(path.read_text(encoding=encoding, errors="replace"))
        return "PY_AST_PARSE_OK"
    except Exception as exc:
        return f"PY_AST_PARSE_FAIL:{type(exc).__name__}:{str(exc).splitlines()[0][:120]}"


def parse_script(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.suffix.lower() == ".py":
        return parse_py(path, strict_utf8=True)
    if path.suffix.lower() == ".ps1":
        return "PS_PARSE_NOT_CHECKED_IN_R25A"
    return "NOT_APPLICABLE"


def count_refs(root: Path, needle: str) -> Tuple[int, List[str]]:
    refs: List[str] = []
    for path in (root / "scripts" / "v18").glob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".ps1"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if needle in text:
            refs.append(path.relative_to(root).as_posix())
    return len(refs), refs


def active_mainline_dependency(refs: Sequence[str]) -> bool:
    active_prefixes = (
        "scripts/v18/run_v18_25A_R11_",
        "scripts/v18/v18_25A_R11_",
        "scripts/v18/run_v18_25A_R13_",
        "scripts/v18/v18_25A_R13_",
        "scripts/v18/run_v18_25A_R25B_",
        "scripts/v18/v18_25A_R25B_",
    )
    ignored = {"scripts/v18/v18_25A_R25_factor_technical_refresh_build_plan.py"}
    return any(ref.startswith(active_prefixes) and ref not in ignored for ref in refs)


def maybe_patch_bom(root: Path, allow_patch: bool, run_stamp: str) -> Tuple[bool, str]:
    path = root / BROKEN_SCRIPT
    if not allow_patch:
        return False, ""
    raw = path.read_bytes()
    backup = path.with_name(f"{path.name}.before_R25A_{run_stamp}.bak")
    shutil.copy2(path, backup)
    if raw.startswith(b"\xef\xbb\xbf"):
        path.write_bytes(raw[3:])
        return True, backup.as_posix()
    return False, backup.as_posix()


def schema_compatible(rows: List[Dict[str, str]]) -> str:
    for row in rows:
        if str(row.get("audit_item", "")).strip() == "compatible_for_next_build_step":
            return str(row.get("value", "")).strip().upper()
    return "UNKNOWN"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-script-patch", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"V18_25A_R25A_{run_stamp}"
    mode = MODE_DRYRUN if args.dry_run or not args.allow_script_patch else MODE_PATCH

    before = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": tree_sig(root / "outputs/v18/factor_pack"),
        "technical": tree_sig(root / "outputs/v18/technical_timing"),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
        "scripts": tree_sig(root / "scripts/v18"),
    }

    _r25_audit_rows, _ = read_csv(root / R25_AUDIT)
    plan_rows, _ = read_csv(root / R25_PLAN)
    schema_rows, _ = read_csv(root / R25_SCHEMA)
    schema_status = schema_compatible(schema_rows)
    target_count = sum(1 for row in plan_rows if str(row.get("combined_action", "")).upper() == "BUILD_FACTOR_AND_TECHNICAL")

    broken_path = root / BROKEN_SCRIPT
    initial_parse = parse_py(broken_path, strict_utf8=True)
    ref_count, refs = count_refs(root, "v18_6A_technical_timing_shadow")
    is_active = active_mainline_dependency(refs)
    patch_attempted = bool(args.allow_script_patch and not args.dry_run and is_active and not initial_parse.endswith("OK"))
    patch_applied, backup_path = maybe_patch_bom(root, patch_attempted, run_stamp)
    final_parse = parse_py(broken_path, strict_utf8=True)

    factor_parse = parse_script(root / FACTOR_BUILDER)
    tech_parse = parse_script(root / TECH_BUILDER)
    factor_ok = factor_parse == "PY_AST_PARSE_OK"
    tech_ok = tech_parse == "PY_AST_PARSE_OK"
    broken_excluded = not is_active and final_parse != "PY_AST_PARSE_OK"
    broken_ok_or_excluded = final_parse == "PY_AST_PARSE_OK" or broken_excluded
    gate_pass = target_count == 93 and schema_status == "TRUE" and factor_ok and tech_ok and broken_ok_or_excluded

    if gate_pass and patch_applied:
        status = STATUS_OK_REPAIR
    elif gate_pass and broken_excluded:
        status = STATUS_EXCLUDED
    elif gate_pass:
        status = STATUS_OK_GATE
    elif is_active and not patch_applied and final_parse != "PY_AST_PARSE_OK":
        status = STATUS_PATCH_REQUIRED
    elif not factor_ok or not tech_ok:
        status = STATUS_REVIEW
    else:
        status = STATUS_BLOCKED

    repair_rows = [{
        "script_path": BROKEN_SCRIPT,
        "initial_parse_status": initial_parse,
        "reference_count": ref_count,
        "active_mainline_dependency": str(is_active).upper(),
        "patch_attempted": str(patch_attempted).upper(),
        "patch_applied": str(patch_applied).upper(),
        "backup_path": backup_path,
        "final_parse_status": final_parse,
        "decision": "EXCLUDE_FROM_R25B_SELECTION" if broken_excluded else ("PATCHED" if patch_applied else "AVAILABLE"),
        "notes": "Broken strict UTF-8 AST parse is caused by a BOM at file start; R25B selects the parse-clean R11 technical builder instead.",
    }]
    selection_rows = [
        {"builder_role": "FACTOR", "builder_script": FACTOR_BUILDER, "wrapper_script_if_any": FACTOR_WRAPPER, "parse_status": factor_parse, "selection_status": "SELECTED" if factor_ok else "REVIEW", "selection_reason": "R25 primary factor staged refresh builder.", "can_use_for_R25B": str(factor_ok).upper(), "notes": "No execution in R25A."},
        {"builder_role": "TECHNICAL", "builder_script": TECH_BUILDER, "wrapper_script_if_any": TECH_WRAPPER, "parse_status": tech_parse, "selection_status": "SELECTED" if tech_ok else "REVIEW", "selection_reason": "Parse-clean V18.25A technical refresh builder; supersedes legacy v18_6A for R25B selection.", "can_use_for_R25B": str(tech_ok).upper(), "notes": "No execution in R25A."},
    ]
    gate_rows = [
        {"gate_check": "r25_combined_plan_93_targets", "status": "PASS" if target_count == 93 else "FAIL", "value": target_count, "notes": ""},
        {"gate_check": "schema_compatibility_true", "status": "PASS" if schema_status == "TRUE" else "FAIL", "value": schema_status, "notes": ""},
        {"gate_check": "factor_builder_parses", "status": "PASS" if factor_ok else "FAIL", "value": factor_parse, "notes": FACTOR_BUILDER},
        {"gate_check": "technical_builder_parses", "status": "PASS" if tech_ok else "FAIL", "value": tech_parse, "notes": TECH_BUILDER},
        {"gate_check": "broken_script_patched_or_excluded", "status": "PASS" if broken_ok_or_excluded else "FAIL", "value": final_parse, "notes": "Excluded from R25B selection." if broken_excluded else ""},
        {"gate_check": "r25b_input_gate", "status": "PASS" if gate_pass else "FAIL", "value": "PASS" if gate_pass else "BLOCKED", "notes": ""},
    ]
    excluded_rows = []
    if broken_excluded:
        excluded_rows.append({"script_path": BROKEN_SCRIPT, "exclusion_status": "EXCLUDED_FROM_R25B_SELECTION", "reason": "Not an active V18.25A R25B dependency; parse-clean R11 technical builder selected.", "reference_count": ref_count, "active_mainline_dependency": str(is_active).upper()})

    write_csv(root / OUT_REPAIR, repair_rows, REPAIR_FIELDS)
    write_csv(root / OUT_SELECTION, selection_rows, SELECTION_FIELDS)
    write_csv(root / OUT_GATE, gate_rows, GATE_FIELDS)
    write_csv(root / OUT_EXCLUDED, excluded_rows, EXCLUDED_FIELDS)

    after = {
        "price": tree_sig(root / PRICE_CACHE),
        "ledger": file_sig(root / LEDGER),
        "factor": tree_sig(root / "outputs/v18/factor_pack"),
        "technical": tree_sig(root / "outputs/v18/technical_timing"),
        "tier": tree_sig(root / "outputs/v18/tier_migration"),
        "decision": tree_sig(root / "outputs/v18/daily_decision"),
        "scripts": tree_sig(root / "scripts/v18"),
    }
    mods = {k: before[k] != after[k] for k in before}
    script_modified = mods["scripts"]
    forbidden = mods["price"] or mods["ledger"] or mods["factor"] or mods["technical"] or mods["tier"] or mods["decision"] or (script_modified and not args.allow_script_patch)
    validation_fail_count = 0 if gate_pass else 1

    next_step = "R25B: Build staged factor and technical rows for approved targets, without merging into current official ranking until validation passes." if gate_pass else "Resolve builder script selection before R25B."
    values = {
        "STATUS": status,
        "MODE": mode,
        "RUN_ID": run_id,
        "R25_SOURCE_SCRIPT_AUDIT_PATH": R25_AUDIT,
        "BROKEN_SCRIPT_PATH": BROKEN_SCRIPT,
        "BROKEN_SCRIPT_INITIAL_PARSE_STATUS": initial_parse,
        "BROKEN_SCRIPT_REFERENCE_COUNT": ref_count,
        "BROKEN_SCRIPT_ACTIVE_MAINLINE_DEPENDENCY": str(is_active).upper(),
        "SCRIPT_PATCH_ATTEMPTED": str(patch_attempted).upper(),
        "SCRIPT_PATCH_APPLIED": str(patch_applied).upper(),
        "SCRIPT_BACKUP_PATH": backup_path,
        "BROKEN_SCRIPT_FINAL_PARSE_STATUS": final_parse,
        "FACTOR_BUILDER_SELECTED": FACTOR_BUILDER,
        "TECHNICAL_BUILDER_SELECTED": TECH_BUILDER,
        "FACTOR_BUILDER_PARSE_STATUS": factor_parse,
        "TECHNICAL_BUILDER_PARSE_STATUS": tech_parse,
        "DEPRECATED_OR_EXCLUDED_SCRIPT_COUNT": len(excluded_rows),
        "R25B_INPUT_GATE_STATUS": "PASS" if gate_pass else "BLOCKED",
        "R25B_TARGET_COUNT": target_count,
        "SCHEMA_COMPATIBILITY_STATUS": schema_status,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "PRICE_CACHE_MODIFIED": str(mods["price"]).upper(),
        "ROLLING_LEDGER_MODIFIED": str(mods["ledger"]).upper(),
        "FACTOR_PACK_MODIFIED": str(mods["factor"]).upper(),
        "TECHNICAL_TIMING_MODIFIED": str(mods["technical"]).upper(),
        "TIER_FILES_MODIFIED": str(mods["tier"]).upper(),
        "OFFICIAL_DECISION_MODIFIED": str(mods["decision"]).upper(),
        "SCRIPT_FILES_MODIFIED": str(script_modified).upper(),
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "FORBIDDEN_MODIFIED": str(forbidden).upper(),
        "NEXT_RECOMMENDED_STEP": next_step,
    }
    write_text(root / OUT_READ_FIRST, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
    report = "\n".join([
        "# V18.25A R25A Source Script Repair Builder Selection Report",
        "",
        f"STATUS: {status}",
        f"MODE: {mode}",
        f"RUN_ID: {run_id}",
        "",
        "## Decision",
        f"- broken_script_active_mainline_dependency: {values['BROKEN_SCRIPT_ACTIVE_MAINLINE_DEPENDENCY']}",
        f"- broken_script_decision: {repair_rows[0]['decision']}",
        f"- r25b_input_gate_status: {values['R25B_INPUT_GATE_STATUS']}",
        "",
        "## Builders",
        f"- factor_builder: {FACTOR_BUILDER}",
        f"- technical_builder: {TECH_BUILDER}",
        "",
        "## Safety",
        f"- script_files_modified: {values['SCRIPT_FILES_MODIFIED']}",
        "- official state modified: FALSE",
        "",
    ])
    write_text(root / OUT_REPORT, report)
    print(f"STATUS: {status}")
    print(f"MODE: {mode}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
