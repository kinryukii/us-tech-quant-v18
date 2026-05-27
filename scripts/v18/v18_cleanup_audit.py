from __future__ import annotations

import csv
import datetime as dt
import re
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(r"D:\us-tech-quant")
OUT_DIR = ROOT / "outputs" / "v18" / "ops"
CSV_OUT = OUT_DIR / "V18_CLEANUP_AUDIT_CURRENT.csv"
MD_OUT = OUT_DIR / "V18_CLEANUP_AUDIT_CURRENT.md"
READ_FIRST_OUT = OUT_DIR / "V18_CLEANUP_AUDIT_READ_FIRST.txt"

MODE = "DRY_RUN"
OFFICIAL_DECISION_IMPACT = "NONE"

FIELDS = [
    "path",
    "category",
    "size_bytes",
    "last_write_time",
    "reason",
    "risk_level",
    "recommended_action",
]

ACTIVE_SCRIPT_NAMES = {
    "run_v18_current_official_daily.ps1",
    "run_v18_current_shadow_research_daily.ps1",
    "run_v18_9C_official_daily_with_sim_validation.ps1",
    "run_v18_8C_official_daily_fast_with_simulation.ps1",
    "run_v18_8B_current_simulation_cabin.ps1",
    "run_v18_9A_simulation_candidate_tracker.ps1",
    "run_v18_9B_forward_return_filler.ps1",
    "run_v18_7D_official_daily_fast_main_with_technical.ps1",
    "run_v18_7B_main_chain_linear_optimizer.ps1",
    "run_v18_7C_factor_output_forward_tracking_audit_fast.ps1",
    "run_v18_6A_technical_timing_shadow.ps1",
    "run_v18_6C_R1_technical_timing_forward_tracker_freshness_guard.ps1",
    "run_v18_6D_technical_timing_read_center.ps1",
    "run_v18_6E_final_read_center_with_technical.ps1",
    "run_v18_10D_official_daily_with_factor_weight_research.ps1",
    "run_v18_10C_R1_factor_weight_research_daily_chain.ps1",
    "run_v18_10C_weight_research_engine.ps1",
    "run_v18_10B_R1_forward_return_maturity_monitor.ps1",
    "run_v18_10B_factor_effectiveness_backtest.ps1",
    "run_v18_10A_R2_factor_daily_capture_patch.ps1",
    "run_v18_10A_factor_registry_coverage_audit.ps1",
    "v18_8B_current_simulation_cabin.py",
    "v18_9A_simulation_candidate_tracker.py",
    "v18_9B_forward_return_filler.py",
    "v18_6A_technical_timing_shadow.py",
    "v18_6C_R1_technical_timing_forward_tracker_freshness_guard.py",
    "v18_6D_technical_timing_read_center.py",
    "v18_6E_final_read_center_with_technical.py",
    "v18_10C_weight_research_engine.py",
    "v18_10B_R1_forward_return_maturity_monitor.py",
    "v18_10B_factor_effectiveness_backtest.py",
    "v18_10A_R2_factor_daily_capture_patch.py",
    "v18_10A_factor_registry_coverage_audit.py",
}

DANGEROUS_CLEANUP_SCRIPTS = {
    "run_v18_4K_R2_safe_delete_cleanup.ps1",
    "run_v18_4K_workspace_cleanup.ps1",
    "run_v18_5D_generated_output_retention_cleanup.ps1",
    "run_v18_8A_legacy_v15_v16_purge.ps1",
}


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def norm_rel(path: Path) -> str:
    return rel(path).replace("/", "\\").lower()


def fmt_time(path: Path) -> str:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    except OSError:
        return ""


def size_of(path: Path) -> int:
    try:
        if path.is_file():
            return path.stat().st_size
        return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
    except OSError:
        return 0


def newest_v18_10d_r2_snapshot() -> str:
    stable = ROOT / "archive" / "stable"
    matches = [p for p in stable.glob("V18_10D_R2_*") if p.is_dir()]
    if not matches:
        return ""
    return norm_rel(max(matches, key=lambda p: p.stat().st_mtime))


def latest_current_outputs() -> set[str]:
    keep = set()
    for sub in [
        ROOT / "outputs" / "v18" / "read_center",
        ROOT / "outputs" / "v18" / "simulation",
        ROOT / "outputs" / "v18" / "factor_research",
        ROOT / "outputs" / "v18" / "weight_research",
        ROOT / "outputs" / "v18" / "ops",
    ]:
        if not sub.exists():
            continue
        for p in sub.glob("*"):
            if not p.is_file():
                continue
            n = p.name.upper()
            if "CURRENT" in n or "READ_FIRST" in n:
                keep.add(norm_rel(p))
    return keep


def row(path: Path, category: str, reason: str, risk: str, action: str) -> Dict[str, str]:
    return {
        "path": rel(path),
        "category": category,
        "size_bytes": str(size_of(path)),
        "last_write_time": fmt_time(path),
        "reason": reason,
        "risk_level": risk,
        "recommended_action": action,
    }


def scan_files() -> Iterable[Path]:
    roots = [
        ROOT / "scripts" / "v18",
        ROOT / "outputs" / "v18",
        ROOT / "state" / "v18",
        ROOT / "archive" / "stable",
    ]
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file():
                yield p


def classify(path: Path, latest_10d_r2: str, current_keep: set[str]) -> Dict[str, str]:
    nr = norm_rel(path)
    name = path.name
    upper = name.upper()

    if nr.startswith(".venv\\") or "\\.venv\\" in nr or "node_modules" in nr:
        return row(path, "MUST_KEEP_ACTIVE", "Excluded environment or dependency directory.", "High", "KEEP")

    if nr.startswith("state\\v18\\"):
        if path.suffix.lower() == ".bak":
            return row(path, "KEEP_BUT_REVIEW", "State backup; never delete directly from this audit.", "High", "QUARANTINE_FIRST")
        return row(path, "MUST_KEEP_ACTIVE", "Active V18 state is excluded from cleanup.", "High", "KEEP")

    if nr.startswith("scripts\\v18\\"):
        if name in ACTIVE_SCRIPT_NAMES:
            return row(path, "MUST_KEEP_ACTIVE", "Active V18 official/shadow chain script dependency.", "High", "KEEP")
        if name in DANGEROUS_CLEANUP_SCRIPTS:
            return row(path, "BUG_OR_RISK_TO_FIX", "Cleanup script has an -Apply path; use only with explicit approval.", "High", "DO_NOT_DELETE")
        if "__pycache__" in nr or path.suffix.lower() == ".pyc":
            return row(path, "SAFE_DELETE_GENERATED", "Python bytecode cache, reproducible.", "Low", "DELETE_DRYRUN_ONLY")
        if path.suffix.lower() == ".bak":
            return row(path, "KEEP_BUT_REVIEW", "Script backup from prior patch; keep until rollback window is closed.", "Medium", "KEEP")
        if path.stat().st_size == 0:
            return row(path, "BUG_OR_RISK_TO_FIX", "Empty script placeholder; classify dependencies before cleanup.", "Medium", "DO_NOT_DELETE")
        return row(path, "KEEP_BUT_REVIEW", "Non-active V18 script; may be legacy or dependency.", "Medium", "DO_NOT_DELETE")

    if nr.startswith("archive\\stable\\"):
        if latest_10d_r2 and nr.startswith(latest_10d_r2 + "\\"):
            return row(path, "MUST_KEEP_ACTIVE", "Latest V18_10D_R2 stable snapshot is explicitly protected.", "High", "KEEP")
        if "\\v18_" in nr:
            return row(path, "KEEP_BUT_REVIEW", "Older V18 stable snapshot; apply retention policy before action.", "Medium", "KEEP")
        return row(path, "KEEP_BUT_REVIEW", "Legacy stable snapshot; keep unless retention policy is approved.", "Medium", "KEEP")

    if nr in current_keep:
        return row(path, "MUST_KEEP_ACTIVE", "Current or read-first output is protected.", "High", "KEEP")

    if nr.startswith("outputs\\v18\\"):
        if path.suffix.lower() == ".bak":
            return row(path, "QUARANTINE_CANDIDATE", "Generated output backup; review before removal.", "Medium", "QUARANTINE_FIRST")
        if path.suffix.lower() == ".log":
            return row(path, "SAFE_DELETE_GENERATED", "Generated log; reproducible from future runs.", "Low", "DELETE_DRYRUN_ONLY")
        if re.search(r"_20\d{6}_\d{6}", name) and "CURRENT" not in upper and "READ_FIRST" not in upper:
            return row(path, "SAFE_DELETE_GENERATED", "Timestamped generated report/audit superseded by current outputs.", "Medium", "DELETE_DRYRUN_ONLY")
        if "DELETE" in upper or "CLEANUP" in upper:
            return row(path, "KEEP_BUT_REVIEW", "Cleanup/delete audit report; retain for traceability.", "Medium", "KEEP")
        return row(path, "KEEP_BUT_REVIEW", "Generated V18 output not proven safe to remove.", "Medium", "KEEP")

    return row(path, "KEEP_BUT_REVIEW", "Unclassified file in scanned roots.", "Medium", "KEEP")


def write_csv(rows: List[Dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def reclaimable(rows: List[Dict[str, str]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in rows:
        if r["recommended_action"] not in {"DELETE_DRYRUN_ONLY", "QUARANTINE_FIRST"}:
            continue
        out[r["category"]] = out.get(r["category"], 0) + int(r["size_bytes"] or 0)
    return out


def write_md(rows: List[Dict[str, str]], latest_10d_r2: str, totals: Dict[str, int]) -> None:
    top = sorted(
        [r for r in rows if r["recommended_action"] in {"DELETE_DRYRUN_ONLY", "QUARANTINE_FIRST"}],
        key=lambda r: int(r["size_bytes"] or 0),
        reverse=True,
    )[:30]

    counts: Dict[str, int] = {}
    for r in rows:
        counts[r["category"]] = counts.get(r["category"], 0) + 1

    lines = [
        "# V18 Cleanup Audit",
        "",
        f"Generated: `{now_text()}`",
        "",
        "## Status",
        "",
        f"- MODE: `{MODE}`",
        f"- OFFICIAL_DECISION_IMPACT: `{OFFICIAL_DECISION_IMPACT}`",
        "- DELETE_ENABLED: `False`",
        "- MOVE_ENABLED: `False`",
        "",
        "## Total Reclaimable Size By Category",
        "",
        "| category | bytes | mb |",
        "|---|---:|---:|",
    ]
    for category, bytes_value in sorted(totals.items()):
        lines.append(f"| {category} | {bytes_value} | {bytes_value / 1048576:.3f} |")
    if not totals:
        lines.append("| NONE | 0 | 0.000 |")

    lines += [
        "",
        "## Row Counts",
        "",
        "| category | count |",
        "|---|---:|",
    ]
    for category, count in sorted(counts.items()):
        lines.append(f"| {category} | {count} |")

    lines += [
        "",
        "## Top 30 Cleanup Candidates",
        "",
        "| path | category | size_bytes | reason | risk | action |",
        "|---|---|---:|---|---|---|",
    ]
    for r in top:
        lines.append(
            f"| {r['path']} | {r['category']} | {r['size_bytes']} | "
            f"{r['reason']} | {r['risk_level']} | {r['recommended_action']} |"
        )
    if not top:
        lines.append("| NONE |  | 0 |  |  |  |")

    lines += [
        "",
        "## Active-Chain Exclusions",
        "",
        "- `run_v18_current_official_daily.ps1` is protected and remains outside cleanup.",
        "- `run_v18_current_shadow_research_daily.ps1` is protected and remains outside cleanup.",
        "- Active V18.9C official chain and V18.10B/10C/10D shadow research chain scripts are protected.",
        "- `state\\v18` is protected from delete actions by this audit.",
        "- Current read-first/current report outputs are protected.",
        "",
        "## Stable Snapshot Retention Notes",
        "",
        f"- Latest protected V18_10D_R2 snapshot: `{latest_10d_r2 or 'NOT_FOUND'}`",
        "- Older stable snapshots are classified `KEEP_BUT_REVIEW`, not delete candidates.",
        "- Stable snapshot deletion requires a separate retention policy and approval.",
        "",
        "## Dangerous Cleanup Script Warnings",
        "",
    ]
    for script in sorted(DANGEROUS_CLEANUP_SCRIPTS):
        lines.append(f"- `{script}` has an `-Apply` path or delete/move behavior. Do not run with `-Apply` without explicit approval.")

    lines += [
        "",
        "## Outputs",
        "",
        f"- CSV: `{CSV_OUT}`",
        f"- MD: `{MD_OUT}`",
        f"- READ_FIRST: `{READ_FIRST_OUT}`",
    ]

    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_read_first(rows: List[Dict[str, str]], totals: Dict[str, int]) -> None:
    total_reclaim = sum(totals.values())
    delete_count = sum(1 for r in rows if r["recommended_action"] == "DELETE_DRYRUN_ONLY")
    quarantine_count = sum(1 for r in rows if r["recommended_action"] == "QUARANTINE_FIRST")
    text = f"""V18 CLEANUP AUDIT READ FIRST

STATUS:
OK_CLEANUP_AUDIT_READY

MODE:
{MODE}

OFFICIAL_DECISION_IMPACT:
{OFFICIAL_DECISION_IMPACT}

DELETE_ENABLED:
False

MOVE_ENABLED:
False

TOTAL_ROWS:
{len(rows)}

DELETE_DRYRUN_ONLY_COUNT:
{delete_count}

QUARANTINE_FIRST_COUNT:
{quarantine_count}

TOTAL_RECLAIMABLE_BYTES:
{total_reclaim}

TOTAL_RECLAIMABLE_MB:
{total_reclaim / 1048576:.3f}

CSV:
{CSV_OUT}

REPORT:
{MD_OUT}

READ_FIRST:
{READ_FIRST_OUT}

NEXT_STEP:
Review the CSV and approve a separate dry-run cleanup/quarantine plan before any file operation.
"""
    READ_FIRST_OUT.write_text(text, encoding="utf-8")


def main() -> int:
    latest_10d_r2 = newest_v18_10d_r2_snapshot()
    current_keep = latest_current_outputs()
    rows = [classify(p, latest_10d_r2, current_keep) for p in scan_files()]
    rows.sort(key=lambda r: (r["category"], r["recommended_action"], r["path"].lower()))

    totals = reclaimable(rows)
    write_csv(rows)
    write_md(rows, latest_10d_r2, totals)
    write_read_first(rows, totals)

    print("STATUS: OK_CLEANUP_AUDIT_READY")
    print(f"MODE: {MODE}")
    print(f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}")
    print("DELETE_ENABLED: False")
    print("MOVE_ENABLED: False")
    print(f"TOTAL_ROWS: {len(rows)}")
    print(f"TOTAL_RECLAIMABLE_BYTES: {sum(totals.values())}")
    print(f"CSV: {CSV_OUT}")
    print(f"REPORT: {MD_OUT}")
    print(f"READ_FIRST: {READ_FIRST_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
