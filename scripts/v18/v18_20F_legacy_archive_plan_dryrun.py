from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
OPS_DIR = Path("outputs/v18/ops")

ARCHIVE_SOURCE = OPS_DIR / "V18_20B_CURRENT_ARCHIVE_THEN_DELETE_LATER.csv"
REVIEW_SOURCE = OPS_DIR / "V18_20B_CURRENT_REVIEW_REQUIRED_TRIAGE.csv"
DEPENDENCY_AUDIT = OPS_DIR / "V18_20A_CURRENT_DEPENDENCY_REFERENCE_AUDIT.csv"
PROTECTED_FILES = OPS_DIR / "V18_20A_CURRENT_DEEP_CLEANUP_PROTECTED_FILES.csv"
MEDIUM_OR_REVIEW = OPS_DIR / "V18_20E_CURRENT_KEEP_MEDIUM_OR_REVIEW.csv"

READ_FIRST_PATH = OPS_DIR / "V18_20F_READ_FIRST.txt"
PLAN_PATH = OPS_DIR / "V18_20F_CURRENT_LEGACY_ARCHIVE_PLAN.csv"
SUMMARY_PATH = OPS_DIR / "V18_20F_CURRENT_ARCHIVE_GROUP_SUMMARY.csv"
PROTECTED_PATH = OPS_DIR / "V18_20F_CURRENT_ARCHIVE_PROTECTED_EXCLUSIONS.csv"
REPORT_PATH = OPS_DIR / "V18_20F_CURRENT_LEGACY_ARCHIVE_PLAN_REPORT.md"

PROTECTED_PREFIXES = (
    "state/",
    "configs/",
    "archive/stable/",
    "archive/stable_compressed/",
    "archive/generated_outputs_compressed/",
    ".git/",
    ".venv/",
)

ZIP_MAP = {
    "LEGACY_VERSIONED_SCRIPTS": "V18_20F_legacy_versioned_scripts.zip",
    "OLD_GENERATED_REPORTS": "V18_20F_old_generated_reports.zip",
    "OLD_RUN_LOGS": "V18_20F_old_run_logs.zip",
    "OLD_EXPERIMENTAL_WRAPPERS": "V18_20F_old_experimental_wrappers.zip",
}

GROUP_SUBDIR = {
    "LEGACY_VERSIONED_SCRIPTS": "legacy_versioned_scripts",
    "OLD_GENERATED_REPORTS": "old_generated_reports",
    "OLD_RUN_LOGS": "old_run_logs",
    "OLD_EXPERIMENTAL_WRAPPERS": "old_experimental_wrappers",
}

OUTPUT_FIELDS = [
    "path",
    "size_mb",
    "extension",
    "archive_group",
    "proposed_archive_zip",
    "proposed_archive_subdir",
    "proposed_later_action",
    "reason",
    "reference_count",
    "referenced_by_sample",
    "current_alias_related",
    "stable_snapshot_related",
    "manual_state_related",
    "price_cache_related",
    "dangerous_token_related",
    "source_code_related",
    "generated_output_related",
    "confidence",
]

SUMMARY_FIELDS = [
    "archive_group",
    "count",
    "total_mb",
    "planned_later_action",
    "proposed_archive_zip",
    "note",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                return rows, list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def normalize(value: object) -> str:
    return str(value or "").strip()


def safe_float(value: object, default: float = 0.0) -> float:
    text = normalize(value).replace(",", "")
    if not text:
        return default
    try:
        return float(text)
    except Exception:
        return default


def safe_int(value: object, default: int = 0) -> int:
    text = normalize(value).replace(",", "")
    if not text:
        return default
    try:
        return int(float(text))
    except Exception:
        return default


def safe_bool(value: object, default: bool = False) -> bool:
    text = normalize(value).upper()
    if text in {"TRUE", "T", "YES", "Y", "1"}:
        return True
    if text in {"FALSE", "F", "NO", "N", "0"}:
        return False
    return default


def mb(value: float) -> str:
    return f"{value:.3f}"


def parse_map(path: Path, key_field: str = "path") -> Dict[str, Dict[str, str]]:
    rows, _, _ = read_csv_rows(path)
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        key = normalize(row.get(key_field)).replace("\\", "/")
        if key:
            out[key] = row
    return out


def latest_stable_snapshot_name(root: Path) -> str:
    base = root / "archive/stable"
    if not base.exists():
        return ""
    dirs = [p for p in base.iterdir() if p.is_dir()]
    if not dirs:
        return ""
    return max(dirs, key=lambda p: p.stat().st_mtime).name


def in_protected_prefix(rel_path: str) -> bool:
    lower = rel_path.lower()
    return any(lower.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def active_ref_guard(referenced_by_sample: str) -> bool:
    refs = referenced_by_sample.upper()
    return any(tok in refs for tok in ("V18_CURRENT_DAILY_COMMAND_CENTER", "V18_CURRENT_DAILY_BRIEF", "V18_19A", "MANIFEST.CSV", "RESTORE_"))


def is_current_alias_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("current_alias_related")):
        return True
    return "CURRENT" in rel_path.upper()


def is_stable_snapshot_related(rel_path: str, row: Dict[str, str], latest_snapshot_name: str) -> bool:
    if safe_bool(row.get("stable_snapshot_related")):
        return True
    lower = rel_path.lower()
    return lower.startswith("archive/stable/") or (latest_snapshot_name and latest_snapshot_name.lower() in lower)


def is_manual_state_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("manual_state_related")):
        return True
    lower = rel_path.lower()
    return "/state/" in f"/{lower}/" and any(tok in lower for tok in ("manual", "trade", "position", "feedback"))


def is_price_cache_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("price_cache_related")):
        return True
    lower = rel_path.lower()
    return "price_cache" in lower or "provider_cache" in lower or "/data/prices/" in lower


def is_source_code_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("source_code_related")):
        return True
    return Path(rel_path.lower()).suffix in {".py", ".ps1", ".bat", ".sh"}


def is_generated_output_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("generated_output_related")):
        return True
    lower = rel_path.lower()
    return lower.startswith("outputs/") or lower.startswith("archive/") or Path(lower).suffix in {".csv", ".log", ".md", ".txt", ".json"}


def build_archive_dest(group: str) -> Tuple[str, str]:
    if group in ZIP_MAP:
        return f"archive/legacy_cleanup/V18_20F_legacy_archive_plan/{GROUP_SUBDIR[group]}", ZIP_MAP[group]
    return "", ""


def is_operational_filename(rel_path: str) -> bool:
    upper = rel_path.upper()
    return any(tok in upper for tok in ("BUY", "SELL", "ORDER", "BROKER", "EXECUTE", "AUTO_TRADE", "AUTO_SELL"))


def classify_row(
    root: Path,
    row: Dict[str, str],
    dep_row: Dict[str, str],
    protected_row: Dict[str, str],
    latest_snapshot_name: str,
) -> Dict[str, object]:
    rel_path = normalize(row.get("path")).replace("\\", "/")
    size = safe_float(row.get("size_mb"))
    ext = Path(rel_path).suffix.lower()
    ref_count_text = normalize(dep_row.get("reference_count") or protected_row.get("reference_count") or row.get("reference_count"))
    referenced_by_sample = normalize(dep_row.get("referenced_by_sample") or protected_row.get("referenced_by_sample") or row.get("referenced_by_sample"))
    ref_count = safe_int(ref_count_text, default=-1) if ref_count_text else -1

    source_row = protected_row or row
    current_alias = is_current_alias_related(rel_path, source_row)
    stable_related = is_stable_snapshot_related(rel_path, source_row, latest_snapshot_name)
    manual_related = is_manual_state_related(rel_path, source_row)
    price_related = is_price_cache_related(rel_path, source_row)
    dangerous = safe_bool(dep_row.get("dangerous_token_related") or protected_row.get("dangerous_token_related") or row.get("dangerous_token_related"))
    source_related = is_source_code_related(rel_path, source_row)
    generated_related = is_generated_output_related(rel_path, source_row)
    in_protected_prefixes = in_protected_prefix(rel_path)
    root_reason = normalize(row.get("reason") or dep_row.get("reason") or protected_row.get("reason"))

    failed_checks: List[str] = []
    if ref_count_text == "":
        failed_checks.append("missing_reference_count")
    elif ref_count > 0:
        failed_checks.append("reference_count_nonzero")
    if current_alias:
        failed_checks.append("current_alias_related")
    if stable_related:
        failed_checks.append("stable_snapshot_related")
    if manual_related:
        failed_checks.append("manual_state_related")
    if price_related:
        failed_checks.append("price_cache_related")
    if source_related:
        failed_checks.append("source_code_related")
    if in_protected_prefixes:
        failed_checks.append("protected_directory")
    if active_ref_guard(referenced_by_sample):
        failed_checks.append("referenced_by_active_source")
    if "CURRENT" in rel_path.upper():
        failed_checks.append("path_contains_current")

    protected = (
        in_protected_prefixes
        or current_alias
        or stable_related
        or manual_related
        or price_related
        or ref_count > 0
        or active_ref_guard(referenced_by_sample)
    )

    if protected:
        archive_group = "DO_NOT_ARCHIVE_PROTECTED"
        action = "KEEP_PROTECTED"
        zip_name = ""
        subdir = ""
        reason = root_reason or "Protected by path/reference policy."
        confidence = "HIGH"
    else:
        if source_related:
            if ext == ".py":
                archive_group = "LEGACY_VERSIONED_SCRIPTS"
                if is_operational_filename(rel_path):
                    action = "REVIEW_REQUIRED"
                    reason = "Historical source script has operational filename signals; keep for manual confirmation."
                    confidence = "LOW"
                else:
                    action = "ARCHIVE_ONLY"
                    reason = "Unreferenced legacy script is safe to archive without delete."
                    confidence = "MEDIUM"
            elif ext == ".ps1":
                archive_group = "OLD_EXPERIMENTAL_WRAPPERS"
                if is_operational_filename(rel_path):
                    action = "REVIEW_REQUIRED"
                    reason = "Historical wrapper still carries operational filename signals."
                    confidence = "LOW"
                else:
                    action = "ARCHIVE_ONLY"
                    reason = "Old wrapper is superseded by current command center."
                    confidence = "MEDIUM"
            else:
                archive_group = "DO_NOT_ARCHIVE_PROTECTED"
                action = "REVIEW_REQUIRED"
                reason = "Source-code role is unclear."
                confidence = "LOW"
        elif generated_related:
            if ext == ".log":
                archive_group = "OLD_RUN_LOGS"
            else:
                archive_group = "OLD_GENERATED_REPORTS"
            action = "ARCHIVE_THEN_DELETE_AFTER_VERIFICATION"
            if dangerous and not rel_path.lower().endswith((".log", ".md", ".txt", ".csv", ".json")):
                action = "REVIEW_REQUIRED"
                reason = "Dangerous token appears outside a clearly historical generated report."
                confidence = "LOW"
            else:
                if dangerous:
                    reason = "Historical generated report/log contains tokens but remains unreferenced and old."
                else:
                    reason = "Historical generated output is unreferenced and safe to archive first."
                confidence = "MEDIUM"
        else:
            archive_group = "DO_NOT_ARCHIVE_PROTECTED"
            action = "REVIEW_REQUIRED"
            reason = "Cleanup role is unclear."
            confidence = "LOW"
        zip_name = ZIP_MAP.get(archive_group, "")
        subdir = f"archive/legacy_cleanup/V18_20F_legacy_archive_plan/{GROUP_SUBDIR.get(archive_group, 'review_required')}"

    if action == "REVIEW_REQUIRED":
        archive_group = "DO_NOT_ARCHIVE_PROTECTED"
        zip_name = ""
        subdir = ""
        confidence = "LOW"

    return {
        "path": rel_path,
        "size_mb": f"{size:.3f}",
        "extension": ext,
        "archive_group": archive_group,
        "proposed_archive_zip": zip_name,
        "proposed_archive_subdir": subdir,
        "proposed_later_action": action,
        "reason": reason,
        "reference_count": ref_count_text or "0",
        "referenced_by_sample": referenced_by_sample,
        "current_alias_related": str(current_alias).upper(),
        "stable_snapshot_related": str(stable_related).upper(),
        "manual_state_related": str(manual_related).upper(),
        "price_cache_related": str(price_related).upper(),
        "dangerous_token_related": str(dangerous).upper(),
        "source_code_related": str(source_related).upper(),
        "generated_output_related": str(generated_related).upper(),
        "confidence": confidence,
    }


def summarize(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    totals: Dict[str, Tuple[int, float, str, str]] = {
        "LEGACY_VERSIONED_SCRIPTS": (0, 0.0, "ARCHIVE_ONLY", ZIP_MAP["LEGACY_VERSIONED_SCRIPTS"]),
        "OLD_GENERATED_REPORTS": (0, 0.0, "ARCHIVE_THEN_DELETE_AFTER_VERIFICATION", ZIP_MAP["OLD_GENERATED_REPORTS"]),
        "OLD_RUN_LOGS": (0, 0.0, "ARCHIVE_THEN_DELETE_AFTER_VERIFICATION", ZIP_MAP["OLD_RUN_LOGS"]),
        "OLD_EXPERIMENTAL_WRAPPERS": (0, 0.0, "ARCHIVE_ONLY", ZIP_MAP["OLD_EXPERIMENTAL_WRAPPERS"]),
        "DO_NOT_ARCHIVE_PROTECTED": (0, 0.0, "KEEP_PROTECTED", ""),
    }
    notes = {
        "LEGACY_VERSIONED_SCRIPTS": "Archive-only source code; do not delete after first archive pass.",
        "OLD_GENERATED_REPORTS": "Historical generated output can be archived and later deleted after verification.",
        "OLD_RUN_LOGS": "Logs are safe to archive first, then delete after verification.",
        "OLD_EXPERIMENTAL_WRAPPERS": "Archive-only wrappers are superseded by current entrypoints.",
        "DO_NOT_ARCHIVE_PROTECTED": "Protected by path, reference, or role policy.",
    }
    for row in rows:
        group = normalize(row.get("archive_group")) or "DO_NOT_ARCHIVE_PROTECTED"
        action = normalize(row.get("proposed_later_action"))
        zip_name = normalize(row.get("proposed_archive_zip"))
        count, total, _, _ = totals.get(group, (0, 0.0, action, zip_name))
        totals[group] = (count + 1, total + safe_float(row.get("size_mb")), action or totals.get(group, ("", "", "", ""))[2], zip_name or totals.get(group, ("", "", "", ""))[3])
    out = []
    for group, (count, total, action, zip_name) in sorted(totals.items(), key=lambda kv: (-kv[1][1], kv[0])):
        out.append(
            {
                "archive_group": group,
                "count": count,
                "total_mb": f"{total:.3f}",
                "planned_later_action": action,
                "proposed_archive_zip": zip_name,
                "note": notes.get(group, ""),
            }
        )
    return out


def render_report(
    root: Path,
    plan_rows: Sequence[Dict[str, object]],
    summary_rows: Sequence[Dict[str, object]],
    protected_rows: Sequence[Dict[str, object]],
    latest_snapshot_name: str,
) -> str:
    planned_rows = [r for r in plan_rows if normalize(r.get("proposed_later_action")) in {"ARCHIVE_ONLY", "ARCHIVE_THEN_DELETE_AFTER_VERIFICATION"}]
    archive_only_rows = [r for r in plan_rows if normalize(r.get("proposed_later_action")) == "ARCHIVE_ONLY"]
    archive_then_delete_rows = [r for r in plan_rows if normalize(r.get("proposed_later_action")) == "ARCHIVE_THEN_DELETE_AFTER_VERIFICATION"]
    review_rows = [r for r in plan_rows if normalize(r.get("proposed_later_action")) == "REVIEW_REQUIRED"]
    protected_mb = sum(safe_float(r.get("size_mb")) for r in protected_rows)
    planned_mb = sum(safe_float(r.get("size_mb")) for r in planned_rows)
    archive_only_mb = sum(safe_float(r.get("size_mb")) for r in archive_only_rows)
    delete_after_mb = sum(safe_float(r.get("size_mb")) for r in archive_then_delete_rows)
    review_mb = sum(safe_float(r.get("size_mb")) for r in review_rows)
    lines = [
        "# V18.20F Legacy Archive Plan Dryrun",
        "",
        "- STATUS: OK_V18_20F_LEGACY_ARCHIVE_PLAN_READY",
        "- MODE: DRYRUN",
        f"- ROOT: {root}",
        f"- INPUT_ARCHIVE_CANDIDATE_COUNT: {len(plan_rows)}",
        f"- INPUT_ARCHIVE_CANDIDATE_MB: {mb(sum(safe_float(r.get('size_mb')) for r in plan_rows))}",
        f"- PLANNED_ARCHIVE_COUNT: {len(planned_rows)}",
        f"- PLANNED_ARCHIVE_MB: {mb(planned_mb)}",
        f"- ARCHIVE_THEN_DELETE_AFTER_VERIFICATION_COUNT: {len(archive_then_delete_rows)}",
        f"- ARCHIVE_THEN_DELETE_AFTER_VERIFICATION_MB: {mb(delete_after_mb)}",
        f"- ARCHIVE_ONLY_COUNT: {len(archive_only_rows)}",
        f"- ARCHIVE_ONLY_MB: {mb(archive_only_mb)}",
        f"- PROTECTED_EXCLUSIONS_COUNT: {len(protected_rows)}",
        f"- PROTECTED_EXCLUSIONS_MB: {mb(protected_mb)}",
        f"- REVIEW_REQUIRED_COUNT: {len(review_rows)}",
        f"- REVIEW_REQUIRED_MB: {mb(review_mb)}",
        "- ARCHIVED_COUNT: 0",
        "- DELETED_COUNT: 0",
        "- MOVED_COUNT: 0",
        "- ZIP_CREATED_COUNT: 0",
        "- VALIDATION_FAIL_COUNT: 0",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- CURRENT_DAILY_MODIFIED: FALSE",
        "- STABLE_SNAPSHOT_MODIFIED: FALSE",
        "- MANUAL_STATE_MODIFIED: FALSE",
        "- PRICE_CACHE_MODIFIED: FALSE",
        f"- LATEST_STABLE_SNAPSHOT_NAME: {latest_snapshot_name}",
        "",
        "## Count By Archive Group",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['archive_group']}: {row['count']} / {row['total_mb']} MB")
    lines.extend(["", "## Top 50 Largest Archive Candidates", ""])
    for row in sorted(planned_rows, key=lambda r: (-safe_float(r.get("size_mb")), normalize(r.get("path"))))[:50]:
        lines.append(f"- {row['path']} | {row['size_mb']} MB | {row['archive_group']} | {row['proposed_later_action']}")
    lines.extend(["", "## Top 50 Protected Exclusions", ""])
    for row in sorted(protected_rows, key=lambda r: (-safe_float(r.get("size_mb")), normalize(r.get("path"))))[:50]:
        lines.append(f"- {row['path']} | {row['size_mb']} MB | {row['reason']}")
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            "- An archive-only apply step is worthwhile for the legacy scripts/wrappers and historical reports.",
            "- Keep the protected price-data and reference-tied material untouched.",
            "- Do not delete originals yet; archive verification should happen first for the generated reports.",
            "",
            f"- READ_FIRST: {rel(root, READ_FIRST_PATH)}",
            f"- REPORT: {rel(root, REPORT_PATH)}",
            f"- PLAN_CSV: {rel(root, PLAN_PATH)}",
            f"- SUMMARY_CSV: {rel(root, SUMMARY_PATH)}",
            f"- PROTECTED_EXCLUSIONS_CSV: {rel(root, PROTECTED_PATH)}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.20F legacy archive plan dryrun")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    archive_rows, _, _ = read_csv_rows(root / ARCHIVE_SOURCE)
    dep_map = parse_map(root / DEPENDENCY_AUDIT)
    protected_map = parse_map(root / PROTECTED_FILES)
    _review_map = parse_map(root / REVIEW_SOURCE)
    _medium_or_review_map = parse_map(root / MEDIUM_OR_REVIEW) if (root / MEDIUM_OR_REVIEW).exists() else {}
    latest_snapshot_name = latest_stable_snapshot_name(root)

    plan_rows: List[Dict[str, object]] = []
    protected_rows: List[Dict[str, object]] = []

    for row in archive_rows:
        rel_path = normalize(row.get("path")).replace("\\", "/")
        dep_row = dep_map.get(rel_path, {})
        protected_row = protected_map.get(rel_path, {})
        classified = classify_row(root, row, dep_row, protected_row, latest_snapshot_name)
        plan_rows.append(classified)
        if normalize(classified.get("proposed_later_action")) == "KEEP_PROTECTED":
            protected_rows.append(classified)

    summary_rows = summarize(plan_rows)
    plan_rows = sorted(plan_rows, key=lambda r: (-safe_float(r.get("size_mb")), normalize(r.get("path"))))
    protected_rows = sorted(protected_rows, key=lambda r: (-safe_float(r.get("size_mb")), normalize(r.get("path"))))

    write_csv(root / PLAN_PATH, plan_rows, OUTPUT_FIELDS)
    write_csv(root / SUMMARY_PATH, summary_rows, SUMMARY_FIELDS)
    write_csv(root / PROTECTED_PATH, protected_rows, OUTPUT_FIELDS)

    input_count = len(archive_rows)
    input_mb = sum(safe_float(r.get("size_mb")) for r in archive_rows)
    planned_rows = [r for r in plan_rows if normalize(r.get("proposed_later_action")) in {"ARCHIVE_ONLY", "ARCHIVE_THEN_DELETE_AFTER_VERIFICATION"}]
    archive_only_rows = [r for r in plan_rows if normalize(r.get("proposed_later_action")) == "ARCHIVE_ONLY"]
    delete_after_rows = [r for r in plan_rows if normalize(r.get("proposed_later_action")) == "ARCHIVE_THEN_DELETE_AFTER_VERIFICATION"]
    review_rows = [r for r in plan_rows if normalize(r.get("proposed_later_action")) == "REVIEW_REQUIRED"]

    planned_mb = sum(safe_float(r.get("size_mb")) for r in planned_rows)
    archive_only_mb = sum(safe_float(r.get("size_mb")) for r in archive_only_rows)
    delete_after_mb = sum(safe_float(r.get("size_mb")) for r in delete_after_rows)
    protected_mb = sum(safe_float(r.get("size_mb")) for r in protected_rows)
    review_mb = sum(safe_float(r.get("size_mb")) for r in review_rows)

    read_first = "\n".join(
        [
            "STATUS: OK_V18_20F_LEGACY_ARCHIVE_PLAN_READY",
            "MODE: DRYRUN",
            f"ROOT: {root}",
            f"INPUT_ARCHIVE_CANDIDATE_COUNT: {input_count}",
            f"INPUT_ARCHIVE_CANDIDATE_MB: {mb(input_mb)}",
            f"PLANNED_ARCHIVE_COUNT: {len(planned_rows)}",
            f"PLANNED_ARCHIVE_MB: {mb(planned_mb)}",
            f"ARCHIVE_THEN_DELETE_AFTER_VERIFICATION_COUNT: {len(delete_after_rows)}",
            f"ARCHIVE_THEN_DELETE_AFTER_VERIFICATION_MB: {mb(delete_after_mb)}",
            f"ARCHIVE_ONLY_COUNT: {len(archive_only_rows)}",
            f"ARCHIVE_ONLY_MB: {mb(archive_only_mb)}",
            f"PROTECTED_EXCLUSIONS_COUNT: {len(protected_rows)}",
            f"PROTECTED_EXCLUSIONS_MB: {mb(protected_mb)}",
            f"REVIEW_REQUIRED_COUNT: {len(review_rows)}",
            f"REVIEW_REQUIRED_MB: {mb(review_mb)}",
            "ARCHIVED_COUNT: 0",
            "DELETED_COUNT: 0",
            "MOVED_COUNT: 0",
            "ZIP_CREATED_COUNT: 0",
            "VALIDATION_FAIL_COUNT: 0",
            "AUTO_TRADE: DISABLED",
            "AUTO_SELL: DISABLED",
            "OFFICIAL_DECISION_IMPACT: NONE",
            "CURRENT_DAILY_MODIFIED: FALSE",
            "STABLE_SNAPSHOT_MODIFIED: FALSE",
            "MANUAL_STATE_MODIFIED: FALSE",
            "PRICE_CACHE_MODIFIED: FALSE",
            f"READ_FIRST: {rel(root, READ_FIRST_PATH)}",
            f"REPORT: {rel(root, REPORT_PATH)}",
            f"PLAN_CSV: {rel(root, PLAN_PATH)}",
            f"SUMMARY_CSV: {rel(root, SUMMARY_PATH)}",
            f"PROTECTED_EXCLUSIONS_CSV: {rel(root, PROTECTED_PATH)}",
        ]
    ) + "\n"
    write_text(root / READ_FIRST_PATH, read_first)
    write_text(root / REPORT_PATH, render_report(root, plan_rows, summary_rows, protected_rows, latest_snapshot_name))

    print("STATUS: OK_V18_20F_LEGACY_ARCHIVE_PLAN_READY")
    print("MODE: DRYRUN")
    print(f"INPUT_ARCHIVE_CANDIDATE_COUNT: {input_count}")
    print(f"INPUT_ARCHIVE_CANDIDATE_MB: {mb(input_mb)}")
    print(f"PLANNED_ARCHIVE_COUNT: {len(planned_rows)}")
    print(f"PLANNED_ARCHIVE_MB: {mb(planned_mb)}")
    print(f"ARCHIVE_THEN_DELETE_AFTER_VERIFICATION_COUNT: {len(delete_after_rows)}")
    print(f"ARCHIVE_THEN_DELETE_AFTER_VERIFICATION_MB: {mb(delete_after_mb)}")
    print(f"ARCHIVE_ONLY_COUNT: {len(archive_only_rows)}")
    print(f"ARCHIVE_ONLY_MB: {mb(archive_only_mb)}")
    print(f"PROTECTED_EXCLUSIONS_COUNT: {len(protected_rows)}")
    print(f"PROTECTED_EXCLUSIONS_MB: {mb(protected_mb)}")
    print(f"REVIEW_REQUIRED_COUNT: {len(review_rows)}")
    print(f"REVIEW_REQUIRED_MB: {mb(review_mb)}")
    print("ARCHIVED_COUNT: 0")
    print("DELETED_COUNT: 0")
    print("MOVED_COUNT: 0")
    print("ZIP_CREATED_COUNT: 0")
    print("VALIDATION_FAIL_COUNT: 0")
    print("AUTO_TRADE: DISABLED")
    print("AUTO_SELL: DISABLED")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print("CURRENT_DAILY_MODIFIED: FALSE")
    print("STABLE_SNAPSHOT_MODIFIED: FALSE")
    print("MANUAL_STATE_MODIFIED: FALSE")
    print("PRICE_CACHE_MODIFIED: FALSE")
    print(f"READ_FIRST: {rel(root, READ_FIRST_PATH)}")
    print(f"REPORT: {rel(root, REPORT_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
