from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
from pathlib import Path
from typing import Dict, List


ROOT = Path(r"D:\us-tech-quant")
AUDIT_CSV = ROOT / "outputs" / "v18" / "ops" / "V18_CLEANUP_AUDIT_CURRENT.csv"
OUT_DIR = ROOT / "outputs" / "v18" / "ops"
PLAN_CSV = OUT_DIR / "V18_CLEANUP_QUARANTINE_PLAN_CURRENT.csv"
PLAN_MD = OUT_DIR / "V18_CLEANUP_QUARANTINE_PLAN_CURRENT.md"
READ_FIRST = OUT_DIR / "V18_CLEANUP_QUARANTINE_READ_FIRST.txt"
DELETE_PLAN_CSV = OUT_DIR / "V18_CLEANUP_DELETE_PLAN_CURRENT.csv"
DELETE_PLAN_MD = OUT_DIR / "V18_CLEANUP_DELETE_PLAN_CURRENT.md"
DELETE_READ_FIRST = OUT_DIR / "V18_CLEANUP_DELETE_READ_FIRST.txt"

MODE_DRY_RUN = "DRY_RUN"
MODE_QUARANTINE = "QUARANTINE"
MODE_DELETE_GENERATED_ONLY = "DELETE_GENERATED_ONLY"
OFFICIAL_DECISION_IMPACT = "NONE"

PROTECTED_NAMES = {
    "run_v18_current_official_daily.ps1",
    "run_v18_current_shadow_research_daily.ps1",
}

CURRENT_REPORT_NAMES = {
    "V18_CURRENT_SHADOW_RESEARCH_DAILY.md",
    "V18_CURRENT_SHADOW_RESEARCH_DAILY_READ_FIRST.txt",
    "V18_10D_CURRENT_OFFICIAL_DAILY_WITH_FACTOR_WEIGHT_RESEARCH.md",
    "V18_10D_READ_FIRST.txt",
    "V18_9C_CURRENT_OFFICIAL_DAILY_WITH_SIM_VALIDATION.md",
    "V18_9C_READ_FIRST.txt",
}

FIELDS = [
    "source_path",
    "destination_path",
    "mode",
    "status",
    "size_bytes",
    "category",
    "risk_level",
    "recommended_action",
    "reason",
    "skip_reason",
]

DELETE_FIELDS = [
    "source_path",
    "mode",
    "status",
    "size_bytes",
    "category",
    "risk_level",
    "recommended_action",
    "reason",
    "skip_reason",
    "delete_error",
]


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def norm_path_text(value: str) -> str:
    return str(value or "").replace("/", "\\").strip().lower()


def protected_by_path(rel_path: str) -> str:
    p = norm_path_text(rel_path)
    name = Path(rel_path).name

    if p.startswith("scripts\\v18\\"):
        return "PROTECTED_SCRIPTS_V18"
    if p.startswith("state\\v18\\"):
        return "PROTECTED_STATE_V18"
    if p.startswith("archive\\stable\\"):
        return "PROTECTED_ARCHIVE_STABLE"
    if p.startswith(".venv\\") or "\\.venv\\" in p:
        return "PROTECTED_VENV"
    if "node_modules" in p:
        return "PROTECTED_NODE_MODULES"
    if name in PROTECTED_NAMES:
        return "PROTECTED_CURRENT_WRAPPER"
    if name in CURRENT_REPORT_NAMES:
        return "PROTECTED_CURRENT_OFFICIAL_OR_SHADOW_REPORT"
    if "read_first" in name.lower() and "current" in p:
        return "PROTECTED_CURRENT_READ_FIRST"
    if name.endswith(".bak") and (
        p.startswith("scripts\\v18\\")
        or p.startswith("state\\v18\\")
        or p.startswith("outputs\\v18\\simulation\\")
    ):
        return "PROTECTED_BAK_IN_CRITICAL_TREE"
    if "stable" in p and "snapshot" in p:
        return "PROTECTED_STABLE_SNAPSHOT"
    return ""


def audit_rows() -> List[Dict[str, str]]:
    if not AUDIT_CSV.exists():
        return []
    with AUDIT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def eligible_or_skip(row: Dict[str, str]) -> str:
    rel_path = row.get("path", "")
    if row.get("recommended_action", "") != "DELETE_DRYRUN_ONLY":
        return "SKIP_RECOMMENDED_ACTION_NOT_DELETE_DRYRUN_ONLY"
    if row.get("category", "") != "SAFE_DELETE_GENERATED":
        return "SKIP_CATEGORY_NOT_SAFE_DELETE_GENERATED"
    if row.get("risk_level", "") not in {"Low", "Medium"}:
        return "SKIP_RISK_NOT_LOW_OR_MEDIUM"

    protected = protected_by_path(rel_path)
    if protected:
        return protected

    source = ROOT / rel_path
    if not source.exists():
        return "SKIP_SOURCE_MISSING"
    if not source.is_file():
        return "SKIP_SOURCE_NOT_FILE"

    return ""


def make_dest(root: Path, rel_path: str) -> Path:
    return root / rel_path


def plan_row(
    source_rel: str,
    dest: str,
    mode: str,
    status: str,
    size_bytes: str,
    category: str,
    risk: str,
    action: str,
    reason: str,
    skip_reason: str,
) -> Dict[str, str]:
    return {
        "source_path": source_rel,
        "destination_path": dest,
        "mode": mode,
        "status": status,
        "size_bytes": str(size_bytes or "0"),
        "category": category,
        "risk_level": risk,
        "recommended_action": action,
        "reason": reason,
        "skip_reason": skip_reason,
    }


def write_csv(rows: List[Dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with PLAN_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def quarantine_plan_rows() -> List[Dict[str, str]]:
    if not PLAN_CSV.exists():
        return []
    with PLAN_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def delete_enabled(mode: str) -> bool:
    return mode == MODE_DELETE_GENERATED_ONLY


def delete_skip_reason(row: Dict[str, str]) -> str:
    rel_path = row.get("source_path", "")
    if row.get("recommended_action", "") != "DELETE_DRYRUN_ONLY":
        return "SKIP_RECOMMENDED_ACTION_NOT_DELETE_DRYRUN_ONLY"
    if row.get("category", "") != "SAFE_DELETE_GENERATED":
        return "SKIP_CATEGORY_NOT_SAFE_DELETE_GENERATED"
    if row.get("risk_level", "") not in {"Low", "Medium"}:
        return "SKIP_RISK_NOT_LOW_OR_MEDIUM"

    protected = protected_by_path(rel_path)
    if protected:
        return protected

    source = ROOT / rel_path
    if not source.exists():
        return "SKIP_SOURCE_MISSING"
    if not source.is_file():
        return "SKIP_SOURCE_NOT_FILE"

    return ""


def delete_plan_row(
    source_rel: str,
    mode: str,
    status: str,
    size_bytes: str,
    category: str,
    risk: str,
    action: str,
    reason: str,
    skip_reason: str,
    delete_error: str = "",
) -> Dict[str, str]:
    return {
        "source_path": source_rel,
        "mode": mode,
        "status": status,
        "size_bytes": str(size_bytes or "0"),
        "category": category,
        "risk_level": risk,
        "recommended_action": action,
        "reason": reason,
        "skip_reason": skip_reason,
        "delete_error": delete_error,
    }


def write_delete_csv(rows: List[Dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with DELETE_PLAN_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DELETE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def grouped(rows: List[Dict[str, str]], key: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in rows:
        value = r.get(key, "") or "NONE"
        out[value] = out.get(value, 0) + 1
    return out


def write_md(rows: List[Dict[str, str]], mode: str, quarantine_root: Path) -> None:
    candidates = [r for r in rows if r["status"] in {"DRYRUN_WOULD_QUARANTINE", "QUARANTINED"}]
    skipped = [r for r in rows if r["status"] == "SKIPPED"]
    candidate_bytes = sum(int(r["size_bytes"] or 0) for r in candidates)
    top = sorted(candidates, key=lambda r: int(r["size_bytes"] or 0), reverse=True)[:30]

    lines = [
        "# V18 Cleanup Quarantine Plan",
        "",
        f"Generated: `{now_text()}`",
        "",
        "## Status",
        "",
        f"- MODE: `{mode}`",
        f"- QUARANTINE_ENABLED: `{mode == MODE_QUARANTINE}`",
        f"- DELETE_ENABLED: `{delete_enabled(mode)}`",
        f"- OFFICIAL_DECISION_IMPACT: `{OFFICIAL_DECISION_IMPACT}`",
        f"- QUARANTINE_TARGET: `{quarantine_root if mode == MODE_QUARANTINE else 'DRYRUN_NOT_CREATED'}`",
        "",
        "## Summary",
        "",
        f"- CANDIDATE_COUNT: `{len(candidates)}`",
        f"- CANDIDATE_BYTES: `{candidate_bytes}`",
        f"- CANDIDATE_MB: `{candidate_bytes / 1048576:.3f}`",
        f"- SKIPPED_COUNT: `{len(skipped)}`",
        "",
        "## Skipped By Reason",
        "",
        "| skip_reason | count |",
        "|---|---:|",
    ]
    for reason, count in sorted(grouped(skipped, "skip_reason").items()):
        lines.append(f"| {reason} | {count} |")
    if not skipped:
        lines.append("| NONE | 0 |")

    lines += [
        "",
        "## Top 30 Quarantine Candidates",
        "",
        "| source_path | size_bytes | risk | status |",
        "|---|---:|---|---|",
    ]
    for r in top:
        lines.append(f"| {r['source_path']} | {r['size_bytes']} | {r['risk_level']} | {r['status']} |")
    if not top:
        lines.append("| NONE | 0 |  |  |")

    lines += [
        "",
        "## Safety Notes",
        "",
        "- Default mode is DRY_RUN.",
        "- Quarantine requires explicit `-Quarantine` on the wrapper.",
        "- Direct deletion requires explicit `-DeleteGeneratedOnly` on the wrapper.",
        "- Delete targets are read only from `V18_CLEANUP_QUARANTINE_PLAN_CURRENT.csv`.",
        "- Protected paths include `scripts\\v18`, `state\\v18`, `archive\\stable`, `.venv`, and `node_modules`.",
        "- Current wrappers, current read-first files, and current official/shadow reports are protected.",
        "",
        "## Outputs",
        "",
        f"- PLAN_CSV: `{PLAN_CSV}`",
        f"- PLAN_MD: `{PLAN_MD}`",
        f"- READ_FIRST: `{READ_FIRST}`",
    ]
    PLAN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_read_first(rows: List[Dict[str, str]], mode: str, quarantine_root: Path) -> None:
    candidates = [r for r in rows if r["status"] in {"DRYRUN_WOULD_QUARANTINE", "QUARANTINED"}]
    skipped = [r for r in rows if r["status"] == "SKIPPED"]
    candidate_bytes = sum(int(r["size_bytes"] or 0) for r in candidates)
    text = f"""V18 CLEANUP QUARANTINE READ FIRST

STATUS:
OK_CLEANUP_QUARANTINE_PLAN_READY

MODE:
{mode}

QUARANTINE_ENABLED:
{mode == MODE_QUARANTINE}

DELETE_ENABLED:
{delete_enabled(mode)}

OFFICIAL_DECISION_IMPACT:
{OFFICIAL_DECISION_IMPACT}

CANDIDATE_COUNT:
{len(candidates)}

CANDIDATE_BYTES:
{candidate_bytes}

CANDIDATE_MB:
{candidate_bytes / 1048576:.3f}

SKIPPED_COUNT:
{len(skipped)}

QUARANTINE_TARGET:
{quarantine_root if mode == MODE_QUARANTINE else "DRYRUN_NOT_CREATED"}

PLAN_CSV:
{PLAN_CSV}

PLAN_MD:
{PLAN_MD}

READ_FIRST:
{READ_FIRST}

NEXT_STEP:
Review the plan CSV. Run with -Quarantine only after explicit approval.
"""
    READ_FIRST.write_text(text, encoding="utf-8")


def delete_targets(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [r for r in rows if r["status"] in {"DRYRUN_WOULD_DELETE", "DELETED", "FAILED"}]


def write_delete_md(rows: List[Dict[str, str]], mode: str) -> None:
    targets = delete_targets(rows)
    skipped = [r for r in rows if r["status"] == "SKIPPED"]
    deleted = [r for r in rows if r["status"] == "DELETED"]
    failed = [r for r in rows if r["status"] == "FAILED"]
    target_bytes = sum(int(r["size_bytes"] or 0) for r in targets)
    deleted_bytes = sum(int(r["size_bytes"] or 0) for r in deleted)
    top = sorted(targets, key=lambda r: int(r["size_bytes"] or 0), reverse=True)[:30]

    lines = [
        "# V18 Cleanup Delete Plan",
        "",
        f"Generated: `{now_text()}`",
        "",
        "## Status",
        "",
        f"- MODE: `{mode}`",
        f"- DELETE_ENABLED: `{delete_enabled(mode)}`",
        f"- OFFICIAL_DECISION_IMPACT: `{OFFICIAL_DECISION_IMPACT}`",
        "",
        "## Summary",
        "",
        f"- TARGET_COUNT: `{len(targets)}`",
        f"- TARGET_BYTES: `{target_bytes}`",
        f"- TARGET_MB: `{target_bytes / 1048576:.3f}`",
        f"- DELETED_COUNT: `{len(deleted)}`",
        f"- DELETED_BYTES: `{deleted_bytes}`",
        f"- FAILED_COUNT: `{len(failed)}`",
        f"- SKIPPED_COUNT: `{len(skipped)}`",
        "",
        "## Skipped By Reason",
        "",
        "| skip_reason | count |",
        "|---|---:|",
    ]
    for reason, count in sorted(grouped(skipped, "skip_reason").items()):
        lines.append(f"| {reason} | {count} |")
    if not skipped:
        lines.append("| NONE | 0 |")

    lines += [
        "",
        "## Top 30 Delete Targets",
        "",
        "| source_path | size_bytes | risk | status |",
        "|---|---:|---|---|",
    ]
    for r in top:
        lines.append(f"| {r['source_path']} | {r['size_bytes']} | {r['risk_level']} | {r['status']} |")
    if not top:
        lines.append("| NONE | 0 |  |  |")

    lines += [
        "",
        "## Safety Notes",
        "",
        "- Default mode is DRY_RUN.",
        "- Direct deletion requires explicit `-DeleteGeneratedOnly` on the wrapper.",
        "- Delete targets are read only from `V18_CLEANUP_QUARANTINE_PLAN_CURRENT.csv`.",
        "- No broad glob-based delete is used.",
        "- Protected paths include `scripts\\v18`, `state\\v18`, `archive\\stable`, `.venv`, and `node_modules`.",
        "- Current wrappers, current read-first files, current official/shadow reports, protected `.bak` files, and stable snapshots are protected.",
        "",
        "## Outputs",
        "",
        f"- DELETE_PLAN_CSV: `{DELETE_PLAN_CSV}`",
        f"- DELETE_PLAN_MD: `{DELETE_PLAN_MD}`",
        f"- DELETE_READ_FIRST: `{DELETE_READ_FIRST}`",
    ]
    DELETE_PLAN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_delete_read_first(rows: List[Dict[str, str]], mode: str) -> None:
    targets = delete_targets(rows)
    skipped = [r for r in rows if r["status"] == "SKIPPED"]
    deleted = [r for r in rows if r["status"] == "DELETED"]
    failed = [r for r in rows if r["status"] == "FAILED"]
    target_bytes = sum(int(r["size_bytes"] or 0) for r in targets)
    deleted_bytes = sum(int(r["size_bytes"] or 0) for r in deleted)
    text = f"""V18 CLEANUP DELETE READ FIRST

STATUS:
OK_CLEANUP_DELETE_PLAN_READY

MODE:
{mode}

DELETE_ENABLED:
{delete_enabled(mode)}

OFFICIAL_DECISION_IMPACT:
{OFFICIAL_DECISION_IMPACT}

TARGET_COUNT:
{len(targets)}

TARGET_BYTES:
{target_bytes}

TARGET_MB:
{target_bytes / 1048576:.3f}

DELETED_COUNT:
{len(deleted)}

DELETED_BYTES:
{deleted_bytes}

FAILED_COUNT:
{len(failed)}

SKIPPED_COUNT:
{len(skipped)}

DELETE_PLAN_CSV:
{DELETE_PLAN_CSV}

DELETE_PLAN_MD:
{DELETE_PLAN_MD}

DELETE_READ_FIRST:
{DELETE_READ_FIRST}

NEXT_STEP:
Review the delete plan. Run with -DeleteGeneratedOnly only after explicit approval.
"""
    DELETE_READ_FIRST.write_text(text, encoding="utf-8")


def build_delete_plan(mode: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for source_row in quarantine_plan_rows():
        rel_path = source_row.get("source_path", "")
        skip = delete_skip_reason(source_row)
        source = ROOT / rel_path

        if skip:
            rows.append(
                delete_plan_row(
                    rel_path,
                    mode,
                    "SKIPPED",
                    source_row.get("size_bytes", "0"),
                    source_row.get("category", ""),
                    source_row.get("risk_level", ""),
                    source_row.get("recommended_action", ""),
                    source_row.get("reason", ""),
                    skip,
                )
            )
            continue

        if mode == MODE_DELETE_GENERATED_ONLY:
            try:
                source.unlink()
                status = "DELETED"
                delete_error = ""
            except Exception as exc:  # pragma: no cover - operational audit path
                status = "FAILED"
                delete_error = f"{type(exc).__name__}: {exc}"
        else:
            status = "DRYRUN_WOULD_DELETE"
            delete_error = ""

        rows.append(
            delete_plan_row(
                rel_path,
                mode,
                status,
                source_row.get("size_bytes", "0"),
                source_row.get("category", ""),
                source_row.get("risk_level", ""),
                source_row.get("recommended_action", ""),
                source_row.get("reason", ""),
                "",
                delete_error,
            )
        )

    write_delete_csv(rows)
    write_delete_md(rows, mode)
    write_delete_read_first(rows, mode)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quarantine", action="store_true")
    ap.add_argument("--delete-generated-only", action="store_true")
    args = ap.parse_args()

    if args.quarantine and args.delete_generated_only:
        ap.error("--quarantine and --delete-generated-only cannot be used together")

    mode = MODE_DRY_RUN
    if args.quarantine:
        mode = MODE_QUARANTINE
    if args.delete_generated_only:
        mode = MODE_DELETE_GENERATED_ONLY
    quarantine_root = ROOT / "archive" / "cleanup_quarantine" / f"V18_CLEANUP_QUARANTINE_{now_stamp()}"

    rows: List[Dict[str, str]] = []
    if mode != MODE_DELETE_GENERATED_ONLY:
        for source_row in audit_rows():
            rel_path = source_row.get("path", "")
            skip = eligible_or_skip(source_row)
            source = ROOT / rel_path
            dest = make_dest(quarantine_root, rel_path)

            if skip:
                rows.append(
                    plan_row(
                        rel_path,
                        "",
                        mode,
                        "SKIPPED",
                        source_row.get("size_bytes", "0"),
                        source_row.get("category", ""),
                        source_row.get("risk_level", ""),
                        source_row.get("recommended_action", ""),
                        source_row.get("reason", ""),
                        skip,
                    )
                )
                continue

            if mode == MODE_QUARANTINE:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(dest))
                status = "QUARANTINED"
            else:
                status = "DRYRUN_WOULD_QUARANTINE"

            rows.append(
                plan_row(
                    rel_path,
                    rel(dest),
                    mode,
                    status,
                    source_row.get("size_bytes", "0"),
                    source_row.get("category", ""),
                    source_row.get("risk_level", ""),
                    source_row.get("recommended_action", ""),
                    source_row.get("reason", ""),
                    "",
                )
            )

        write_csv(rows)
        write_md(rows, mode, quarantine_root)
        write_read_first(rows, mode, quarantine_root)

    delete_rows = build_delete_plan(mode)

    candidates = [r for r in rows if r["status"] in {"DRYRUN_WOULD_QUARANTINE", "QUARANTINED"}]
    skipped = [r for r in rows if r["status"] == "SKIPPED"]
    candidate_bytes = sum(int(r["size_bytes"] or 0) for r in candidates)
    targets = delete_targets(delete_rows)
    deleted = [r for r in delete_rows if r["status"] == "DELETED"]
    failed = [r for r in delete_rows if r["status"] == "FAILED"]
    target_bytes = sum(int(r["size_bytes"] or 0) for r in targets)
    deleted_bytes = sum(int(r["size_bytes"] or 0) for r in deleted)

    print("STATUS: OK_CLEANUP_QUARANTINE_PLAN_READY")
    print(f"MODE: {mode}")
    print(f"QUARANTINE_ENABLED: {mode == MODE_QUARANTINE}")
    print(f"DELETE_ENABLED: {delete_enabled(mode)}")
    print(f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}")
    print(f"CANDIDATE_COUNT: {len(candidates)}")
    print(f"CANDIDATE_BYTES: {candidate_bytes}")
    print(f"SKIPPED_COUNT: {len(skipped)}")
    print(f"DELETE_TARGET_COUNT: {len(targets)}")
    print(f"DELETE_TARGET_BYTES: {target_bytes}")
    print(f"DELETED_COUNT: {len(deleted)}")
    print(f"DELETED_BYTES: {deleted_bytes}")
    print(f"DELETE_FAILED_COUNT: {len(failed)}")
    print(f"PLAN_CSV: {PLAN_CSV}")
    print(f"PLAN_MD: {PLAN_MD}")
    print(f"READ_FIRST: {READ_FIRST}")
    print(f"DELETE_PLAN_CSV: {DELETE_PLAN_CSV}")
    print(f"DELETE_PLAN_MD: {DELETE_PLAN_MD}")
    print(f"DELETE_READ_FIRST: {DELETE_READ_FIRST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
