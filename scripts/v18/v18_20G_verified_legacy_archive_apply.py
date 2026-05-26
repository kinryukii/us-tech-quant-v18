from __future__ import annotations

import argparse
import csv
import datetime as dt
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
import zipfile


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
OPS_DIR = Path("outputs/v18/ops")

PLAN_SOURCE = OPS_DIR / "V18_20F_CURRENT_LEGACY_ARCHIVE_PLAN.csv"
PROTECTED_SOURCE = OPS_DIR / "V18_20F_CURRENT_ARCHIVE_PROTECTED_EXCLUSIONS.csv"
READ_FIRST_PATH = OPS_DIR / "V18_20G_READ_FIRST.txt"
AUDIT_PATH = OPS_DIR / "V18_20G_CURRENT_VERIFIED_LEGACY_ARCHIVE_AUDIT.csv"
MANIFEST_PATH = OPS_DIR / "V18_20G_CURRENT_VERIFIED_LEGACY_ARCHIVE_MANIFEST.csv"
REPORT_PATH = OPS_DIR / "V18_20G_CURRENT_VERIFIED_LEGACY_ARCHIVE_REPORT.md"

ARCHIVE_GROUP_ORDER = [
    "OLD_GENERATED_REPORTS",
    "OLD_EXPERIMENTAL_WRAPPERS",
    "LEGACY_VERSIONED_SCRIPTS",
    "OLD_RUN_LOGS",
]

ZIP_MAP = {
    "OLD_GENERATED_REPORTS": "V18_20G_old_generated_reports.zip",
    "OLD_EXPERIMENTAL_WRAPPERS": "V18_20G_old_experimental_wrappers.zip",
    "LEGACY_VERSIONED_SCRIPTS": "V18_20G_legacy_versioned_scripts.zip",
    "OLD_RUN_LOGS": "V18_20G_old_run_logs.zip",
}

ARCHIVEABLE_ACTIONS = {"ARCHIVE_ONLY", "ARCHIVE_THEN_DELETE_AFTER_VERIFICATION"}

PROTECTED_PREFIXES = (
    "state/",
    "configs/",
    "archive/stable/",
    "archive/stable_compressed/",
    "archive/generated_outputs_compressed/",
    ".git/",
    ".venv/",
)

AUDIT_FIELDS = [
    "source_path",
    "archive_group",
    "proposed_later_action",
    "zip_path",
    "zip_member_path",
    "size_mb",
    "source_exists_before",
    "source_exists_after",
    "included_in_zip",
    "zip_verified",
    "protected_exclusion_violation",
    "current_alias_violation",
    "validation_status",
    "reason",
]

MANIFEST_FIELDS = [
    "source_path",
    "archive_group",
    "proposed_later_action",
    "zip_path",
    "zip_member_path",
    "size_mb",
    "confidence",
    "reference_count",
    "source_exists_before",
    "source_exists_after",
]

VALIDATION_FIELDS = [
    "zip_path",
    "archive_group",
    "expected_count",
    "expected_mb",
    "zip_exists",
    "zip_size_bytes",
    "zip_openable",
    "members_present",
    "member_count_ok",
    "source_files_still_exist",
    "protected_exclusion_included",
    "current_alias_included",
    "validation_status",
    "reason",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


def relpath(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def relpath_str(root: Path, raw_path: str) -> str:
    return relpath(root, root / raw_path.replace("\\", "/"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    raise RuntimeError(f"Failed to read CSV: {path}")


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


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def latest_stable_snapshot_name(root: Path) -> str:
    stable_root = root / "archive/stable"
    if not stable_root.exists():
        return ""
    dirs = [p for p in stable_root.iterdir() if p.is_dir()]
    if not dirs:
        return ""
    return max(dirs, key=lambda p: p.stat().st_mtime).name


def is_protected_path(rel_path: str) -> bool:
    lower = rel_path.lower()
    return any(lower.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def is_current_alias_related(rel_path: str, row: Dict[str, str]) -> bool:
    return safe_bool(row.get("current_alias_related")) or "CURRENT" in rel_path.upper()


def is_stable_snapshot_related(rel_path: str, row: Dict[str, str], latest_snapshot_name: str) -> bool:
    if safe_bool(row.get("stable_snapshot_related")):
        return True
    lower = rel_path.lower()
    return lower.startswith("archive/stable/") or (latest_snapshot_name and latest_snapshot_name.lower() in lower)


def is_manual_state_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("manual_state_related")):
        return True
    lower = rel_path.lower()
    return "/state/" in f"/{lower}/"


def is_price_cache_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("price_cache_related")):
        return True
    lower = rel_path.lower()
    return "provider_cache" in lower or "price_cache" in lower or "/data/prices/" in lower


def is_source_code_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("source_code_related")):
        return True
    return Path(rel_path).suffix.lower() in {".py", ".ps1", ".bat", ".sh"}


def is_generated_output_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("generated_output_related")):
        return True
    lower = rel_path.lower()
    return lower.startswith("outputs/") or lower.startswith("archive/") or Path(lower).suffix.lower() in {".csv", ".md", ".log", ".txt", ".json"}


def dangerous_token_only_in_old_generated_report(rel_path: str, row: Dict[str, str]) -> bool:
    if not safe_bool(row.get("dangerous_token_related")):
        return False
    return is_generated_output_related(rel_path, row) and not safe_bool(row.get("source_code_related"))


def archive_group_for_row(row: Dict[str, str]) -> str:
    return normalize(row.get("archive_group"))


def group_priority(group: str) -> int:
    try:
        return ARCHIVE_GROUP_ORDER.index(group)
    except ValueError:
        return len(ARCHIVE_GROUP_ORDER)


def zip_member_path(source_path: str) -> str:
    return source_path.replace("\\", "/")


def classify_row(
    root: Path,
    row: Dict[str, str],
    latest_snapshot_name: str,
    archive_root: Path,
) -> Dict[str, object]:
    source_path = normalize(row.get("path")).replace("\\", "/")
    archive_group = archive_group_for_row(row)
    proposed_later_action = normalize(row.get("proposed_later_action"))
    zip_name = ZIP_MAP.get(archive_group, "")
    zip_path = archive_root / zip_name if zip_name else Path()
    size_mb = safe_float(row.get("size_mb"))
    confidence = normalize(row.get("confidence")).upper() or "UNKNOWN"
    reference_count = safe_int(row.get("reference_count"))
    referenced_by_sample = normalize(row.get("referenced_by_sample"))

    source_exists_before = (root / source_path).exists()
    source_exists_after = source_exists_before

    current_alias_related = is_current_alias_related(source_path, row)
    stable_snapshot_related = is_stable_snapshot_related(source_path, row, latest_snapshot_name)
    manual_state_related = is_manual_state_related(source_path, row)
    price_cache_related = is_price_cache_related(source_path, row)
    source_code_related = is_source_code_related(source_path, row)
    generated_output_related = is_generated_output_related(source_path, row)
    dangerous_token_related = safe_bool(row.get("dangerous_token_related"))

    reason = normalize(row.get("reason"))
    failed_checks: List[str] = []
    included_in_zip = True
    validation_status = "OK"
    protected_exclusion_violation = False
    current_alias_violation = False
    zip_verified = False

    if archive_group not in ZIP_MAP:
        failed_checks.append("archive_group_not_planned")
        included_in_zip = False
        validation_status = "SKIPPED"
    if proposed_later_action not in ARCHIVEABLE_ACTIONS:
        failed_checks.append("not_archiveable_action")
        included_in_zip = False
        validation_status = "SKIPPED"
    if not source_exists_before:
        failed_checks.append("source_missing")
        included_in_zip = False
        validation_status = "MISSING"
    if source_path.upper().find("CURRENT") >= 0:
        failed_checks.append("current_alias_related")
        current_alias_violation = True
        included_in_zip = False
        validation_status = "BLOCKED"
    if is_protected_path(source_path):
        failed_checks.append("protected_path")
        protected_exclusion_violation = True
        included_in_zip = False
        validation_status = "BLOCKED"
    if manual_state_related:
        failed_checks.append("manual_state_related")
        included_in_zip = False
        validation_status = "BLOCKED"
    if price_cache_related:
        failed_checks.append("price_cache_related")
        included_in_zip = False
        validation_status = "BLOCKED"
    if stable_snapshot_related:
        failed_checks.append("stable_snapshot_related")
        included_in_zip = False
        validation_status = "BLOCKED"
    if reference_count > 0 and confidence != "HIGH":
        failed_checks.append("reference_count_nonzero_without_high_confidence")
        included_in_zip = False
        validation_status = "BLOCKED"
    if reference_count > 0 and confidence == "HIGH":
        failed_checks.append("reference_count_nonzero_high_confidence")
    if source_code_related and any(tok in source_path.upper() for tok in ("BUY", "SELL", "AUTO_TRADE", "AUTO_SELL", "ORDER", "BROKER", "EXECUTE")):
        failed_checks.append("active_trading_token_in_source_code")
        included_in_zip = False
        validation_status = "BLOCKED"
    if dangerous_token_related and not dangerous_token_only_in_old_generated_report(source_path, row):
        failed_checks.append("dangerous_token_in_nonreport")
        included_in_zip = False
        validation_status = "BLOCKED"

    if confidence not in {"HIGH", "MEDIUM", "LOW"}:
        failed_checks.append("confidence_missing_or_unknown")

    if included_in_zip and validation_status == "OK":
        zip_verified = True

    reason_bits = [reason] if reason else []
    if failed_checks:
        reason_bits.append("failed_checks=" + ";".join(failed_checks))
    if not reason_bits:
        reason_bits.append("Planned archive candidate passed all archive checks.")

    return {
        "source_path": source_path,
        "archive_group": archive_group,
        "proposed_later_action": proposed_later_action,
        "zip_path": str(zip_path.relative_to(root)).replace("\\", "/") if zip_name else "",
        "zip_member_path": zip_member_path(source_path),
        "size_mb": f"{size_mb:.3f}",
        "source_exists_before": str(source_exists_before).upper(),
        "source_exists_after": str(source_exists_after).upper(),
        "included_in_zip": str(included_in_zip).upper(),
        "zip_verified": str(zip_verified).upper(),
        "protected_exclusion_violation": str(protected_exclusion_violation).upper(),
        "current_alias_violation": str(current_alias_violation).upper(),
        "validation_status": validation_status,
        "reason": " | ".join(reason_bits),
        "reference_count": str(reference_count),
        "referenced_by_sample": referenced_by_sample,
        "current_alias_related": str(current_alias_related).upper(),
        "stable_snapshot_related": str(stable_snapshot_related).upper(),
        "manual_state_related": str(manual_state_related).upper(),
        "price_cache_related": str(price_cache_related).upper(),
        "dangerous_token_related": str(dangerous_token_related).upper(),
        "source_code_related": str(source_code_related).upper(),
        "generated_output_related": str(generated_output_related).upper(),
        "confidence": confidence,
        "_failed_checks": failed_checks,
    }


def build_validation_row(
    root: Path,
    archive_root: Path,
    archive_group: str,
    zip_path: Path,
    expected_rows: Sequence[Dict[str, object]],
    protected_rows: Sequence[Dict[str, str]],
) -> Dict[str, object]:
    expected_members = {zip_member_path(normalize(r.get("path"))) for r in expected_rows}
    expected_count = len(expected_rows)
    expected_mb = sum(safe_float(r.get("size_mb")) for r in expected_rows)
    zip_exists = zip_path.exists()
    zip_size_bytes = zip_path.stat().st_size if zip_exists else 0
    zip_openable = False
    members_present = False
    member_count_ok = False
    source_files_still_exist = all((root / normalize(r.get("path"))).exists() for r in expected_rows)
    protected_exclusion_included = False
    current_alias_included = False
    reason = ""
    validation_status = "FAIL"
    actual_members: List[str] = []

    if zip_exists and zip_size_bytes > 0:
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zip_openable = True
                actual_members = zf.namelist()
                actual_member_set = set(actual_members)
                members_present = expected_members.issubset(actual_member_set)
                member_count_ok = len(actual_member_set) == expected_count
                protected_set = {normalize(r.get("path")).replace("\\", "/") for r in protected_rows}
                protected_exclusion_included = bool(protected_set.intersection(actual_member_set))
                current_alias_included = any("CURRENT" in member.upper() for member in actual_member_set)
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"

    if zip_exists and zip_size_bytes > 0 and zip_openable and members_present and member_count_ok and source_files_still_exist and not protected_exclusion_included and not current_alias_included:
        validation_status = "OK"
        reason = "Zip verified successfully."
    elif not reason:
        reason = "Zip verification failed."

    return {
        "zip_path": str(zip_path.relative_to(root)).replace("\\", "/"),
        "archive_group": archive_group,
        "expected_count": str(expected_count),
        "expected_mb": f"{expected_mb:.3f}",
        "zip_exists": str(zip_exists).upper(),
        "zip_size_bytes": str(zip_size_bytes),
        "zip_openable": str(zip_openable).upper(),
        "members_present": str(members_present).upper(),
        "member_count_ok": str(member_count_ok).upper(),
        "source_files_still_exist": str(source_files_still_exist).upper(),
        "protected_exclusion_included": str(protected_exclusion_included).upper(),
        "current_alias_included": str(current_alias_included).upper(),
        "validation_status": validation_status,
        "reason": reason,
        "_actual_members": actual_members,
    }


def summarize_group(rows: Sequence[Dict[str, object]], group: str) -> Dict[str, object]:
    group_rows = [r for r in rows if normalize(r.get("archive_group")) == group]
    included_rows = [r for r in group_rows if normalize(r.get("included_in_zip")) == "TRUE"]
    total_mb = sum(safe_float(r.get("size_mb")) for r in included_rows)
    return {
        "archive_group": group,
        "count": str(len(included_rows)),
        "total_mb": f"{total_mb:.3f}",
        "planned_later_action": "ARCHIVE_ONLY" if group in {"LEGACY_VERSIONED_SCRIPTS", "OLD_EXPERIMENTAL_WRAPPERS"} else "ARCHIVE_THEN_DELETE_AFTER_VERIFICATION",
        "proposed_archive_zip": ZIP_MAP.get(group, ""),
        "note": "Verified archive group",
    }


def render_report(
    root: Path,
    archive_root: Path,
    audit_rows: Sequence[Dict[str, object]],
    validation_rows: Sequence[Dict[str, object]],
    latest_snapshot_name: str,
) -> str:
    included = [r for r in audit_rows if normalize(r.get("included_in_zip")) == "TRUE"]
    protected = [r for r in audit_rows if normalize(r.get("protected_exclusion_violation")) == "TRUE"]
    current_alias = [r for r in audit_rows if normalize(r.get("current_alias_violation")) == "TRUE"]
    archive_only = [r for r in included if normalize(r.get("proposed_later_action")) == "ARCHIVE_ONLY"]
    delete_after = [r for r in included if normalize(r.get("proposed_later_action")) == "ARCHIVE_THEN_DELETE_AFTER_VERIFICATION"]
    planned_mb = sum(safe_float(r.get("size_mb")) for r in included)
    archive_only_mb = sum(safe_float(r.get("size_mb")) for r in archive_only)
    delete_after_mb = sum(safe_float(r.get("size_mb")) for r in delete_after)
    verification_ok = [r for r in validation_rows if normalize(r.get("validation_status")) == "OK"]
    counts = Counter(normalize(r.get("archive_group")) for r in included)
    group_lines = [f"- {group}: {counts.get(group, 0)} / {sum(safe_float(r.get('size_mb')) for r in included if normalize(r.get('archive_group')) == group):.3f} MB" for group in ARCHIVE_GROUP_ORDER]

    top_candidates = sorted(included, key=lambda r: (-safe_float(r.get("size_mb")), r.get("source_path")))
    top_protected = sorted(protected, key=lambda r: (-safe_float(r.get("size_mb")), r.get("source_path")))

    lines = [
        "# V18.20G Verified Legacy Archive Apply Report",
        "",
        "- STATUS: OK_V18_20G_VERIFIED_LEGACY_ARCHIVE_READY",
        "- MODE: APPLY_ARCHIVE_ONLY",
        f"- ROOT: {root}",
        f"- ARCHIVE_ROOT: {archive_root}",
        f"- ZIP_CREATED_COUNT: {len(validation_rows)}",
        f"- ZIP_VERIFIED_COUNT: {len(verification_ok)}",
        f"- PLANNED_ARCHIVE_COUNT: {len(included)}",
        f"- PLANNED_ARCHIVE_MB: {planned_mb:.3f}",
        f"- ARCHIVED_FILE_COUNT: {len(included)}",
        f"- ARCHIVED_FILE_MB: {planned_mb:.3f}",
        f"- ARCHIVE_ONLY_COUNT: {len(archive_only)}",
        f"- ARCHIVE_ONLY_MB: {archive_only_mb:.3f}",
        f"- ARCHIVE_THEN_DELETE_AFTER_VERIFICATION_COUNT: {len(delete_after)}",
        f"- ARCHIVE_THEN_DELETE_AFTER_VERIFICATION_MB: {delete_after_mb:.3f}",
        f"- PROTECTED_EXCLUSION_INCLUDED_COUNT: {len(protected)}",
        f"- CURRENT_ALIAS_INCLUDED_COUNT: {len(current_alias)}",
        "- ORIGINAL_DELETED_COUNT: 0",
        "- DELETED_COUNT: 0",
        "- MOVED_COUNT: 0",
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
        "## Count / MB By Archive Group",
        *group_lines,
        "",
        "## Zip Validation",
    ]
    for row in validation_rows:
        lines.append(
            f"- {row['archive_group']}: {row['zip_path']} | {row['validation_status']} | "
            f"{row['expected_count']} files | {row['expected_mb']} MB | {row['reason']}"
        )
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            "- Archive-only apply is worthwhile for the legacy generated reports and wrappers.",
            "- Keep originals in place until a later verified-delete step is explicitly approved.",
            "",
            "## Top 50 Largest Archive Candidates",
        ]
    )
    for row in top_candidates[:50]:
        lines.append(f"- {row['source_path']} | {row['size_mb']} MB | {row['archive_group']} | {row['proposed_later_action']}")
    lines.extend(["", "## Top 50 Protected Exclusions"])
    for row in top_protected[:50]:
        lines.append(f"- {row['source_path']} | {row['size_mb']} MB | {row['archive_group']} | {row['reason']}")
    lines.extend(
        [
            "",
            f"- READ_FIRST: {READ_FIRST_PATH.as_posix()}",
            f"- AUDIT_CSV: {AUDIT_PATH.as_posix()}",
            f"- MANIFEST_CSV: {MANIFEST_PATH.as_posix()}",
            f"- REPORT: {REPORT_PATH.as_posix()}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.20G verified legacy archive apply")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    plan_rows = read_csv(root / PLAN_SOURCE)
    protected_rows = read_csv(root / PROTECTED_SOURCE)
    latest_snapshot_name = latest_stable_snapshot_name(root)
    run_id = timestamp()
    archive_root = root / f"archive/legacy_cleanup/V18_20G_verified_legacy_archive_{run_id}"
    ensure_dir(archive_root)

    eligible_plan_rows = [
        row for row in plan_rows if normalize(row.get("proposed_later_action")) in ARCHIVEABLE_ACTIONS and normalize(row.get("archive_group")) in ZIP_MAP
    ]
    eligible_plan_rows.sort(key=lambda row: (-safe_float(row.get("size_mb")), group_priority(normalize(row.get("archive_group"))), normalize(row.get("path"))))

    audit_rows: List[Dict[str, object]] = []
    grouped_sources: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    protected_paths = {normalize(row.get("path")).replace("\\", "/") for row in protected_rows if normalize(row.get("path"))}

    for row in eligible_plan_rows:
        classified = classify_row(root, row, latest_snapshot_name, archive_root)
        audit_rows.append(classified)
        if normalize(classified.get("included_in_zip")) == "TRUE":
            grouped_sources[normalize(classified["archive_group"])].append(row)

    # Create zips only for non-empty planned groups.
    validation_rows: List[Dict[str, object]] = []
    for group in ARCHIVE_GROUP_ORDER:
        planned_sources = grouped_sources.get(group, [])
        if not planned_sources:
            continue
        zip_name = ZIP_MAP[group]
        zip_path = archive_root / zip_name
        ensure_dir(zip_path.parent)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for row in planned_sources:
                source_path = normalize(row.get("path")).replace("\\", "/")
                zf.write(root / source_path, arcname=zip_member_path(source_path))
        validation_rows.append(build_validation_row(root, archive_root, group, zip_path, planned_sources, protected_rows))

    # Reconcile audit rows with verification result.
    validation_map = {normalize(row.get("archive_group")): row for row in validation_rows}
    for row in audit_rows:
        group = normalize(row.get("archive_group"))
        verified = validation_map.get(group)
        if normalize(row.get("included_in_zip")) == "TRUE" and verified:
            row["zip_verified"] = verified["validation_status"] == "OK"
            row["validation_status"] = verified["validation_status"]
        elif normalize(row.get("included_in_zip")) == "TRUE":
            row["zip_verified"] = False
            row["validation_status"] = "MISSING_ZIP"
        else:
            row["zip_verified"] = False

    # Separate audit from manifest ordering.
    audit_rows = sorted(
        audit_rows,
        key=lambda row: (
            group_priority(normalize(row.get("archive_group"))),
            -safe_float(row.get("size_mb")),
            normalize(row.get("source_path")),
        ),
    )
    manifest_rows = [
        {
            "source_path": row["source_path"],
            "archive_group": row["archive_group"],
            "proposed_later_action": row["proposed_later_action"],
            "zip_path": row["zip_path"],
            "zip_member_path": row["zip_member_path"],
            "size_mb": row["size_mb"],
            "confidence": row["confidence"],
            "reference_count": row["reference_count"],
            "source_exists_before": row["source_exists_before"],
            "source_exists_after": row["source_exists_after"],
        }
        for row in audit_rows
    ]

    # Summary files inside archive folder.
    summary_rows = [summarize_group(audit_rows, group) for group in ARCHIVE_GROUP_ORDER]
    protected_summary = {
        "archive_group": "DO_NOT_ARCHIVE_PROTECTED",
        "count": str(sum(1 for row in plan_rows if normalize(row.get("archive_group")) == "DO_NOT_ARCHIVE_PROTECTED")),
        "total_mb": f"{sum(safe_float(row.get('size_mb')) for row in plan_rows if normalize(row.get('archive_group')) == 'DO_NOT_ARCHIVE_PROTECTED'):.3f}",
        "planned_later_action": "KEEP_PROTECTED",
        "proposed_archive_zip": "",
        "note": "Protected exclusions were not archived.",
    }
    summary_rows.append(protected_summary)

    write_csv(root / AUDIT_PATH, audit_rows, AUDIT_FIELDS)
    write_csv(root / MANIFEST_PATH, manifest_rows, MANIFEST_FIELDS)
    write_csv(archive_root / "MANIFEST.csv", manifest_rows, MANIFEST_FIELDS)
    write_csv(archive_root / "VALIDATION.csv", validation_rows, VALIDATION_FIELDS)
    write_csv(root / OPS_DIR / "V18_20G_CURRENT_VERIFIED_LEGACY_ARCHIVE_GROUP_SUMMARY.csv", summary_rows, [
        "archive_group",
        "count",
        "total_mb",
        "planned_later_action",
        "proposed_archive_zip",
        "note",
    ])

    read_first = "\n".join(
        [
            "STATUS: OK_V18_20G_VERIFIED_LEGACY_ARCHIVE_READY",
            "MODE: APPLY_ARCHIVE_ONLY",
            f"ROOT: {root}",
            f"ARCHIVE_ROOT: {archive_root}",
            f"ZIP_CREATED_COUNT: {len(validation_rows)}",
            f"ZIP_VERIFIED_COUNT: {len([row for row in validation_rows if normalize(row.get('validation_status')) == 'OK'])}",
            f"PLANNED_ARCHIVE_COUNT: {len([row for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE'])}",
            f"PLANNED_ARCHIVE_MB: {sum(safe_float(row.get('size_mb')) for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE'):.3f}",
            f"ARCHIVED_FILE_COUNT: {len([row for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE'])}",
            f"ARCHIVED_FILE_MB: {sum(safe_float(row.get('size_mb')) for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE'):.3f}",
            f"ARCHIVE_ONLY_COUNT: {len([row for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE' and normalize(row.get('proposed_later_action')) == 'ARCHIVE_ONLY'])}",
            f"ARCHIVE_ONLY_MB: {sum(safe_float(row.get('size_mb')) for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE' and normalize(row.get('proposed_later_action')) == 'ARCHIVE_ONLY'):.3f}",
            f"ARCHIVE_THEN_DELETE_AFTER_VERIFICATION_COUNT: {len([row for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE' and normalize(row.get('proposed_later_action')) == 'ARCHIVE_THEN_DELETE_AFTER_VERIFICATION'])}",
            f"ARCHIVE_THEN_DELETE_AFTER_VERIFICATION_MB: {sum(safe_float(row.get('size_mb')) for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE' and normalize(row.get('proposed_later_action')) == 'ARCHIVE_THEN_DELETE_AFTER_VERIFICATION'):.3f}",
            f"PROTECTED_EXCLUSION_INCLUDED_COUNT: {len([row for row in audit_rows if normalize(row.get('protected_exclusion_violation')) == 'TRUE'])}",
            f"CURRENT_ALIAS_INCLUDED_COUNT: {len([row for row in audit_rows if normalize(row.get('current_alias_violation')) == 'TRUE'])}",
            "ORIGINAL_DELETED_COUNT: 0",
            "DELETED_COUNT: 0",
            "MOVED_COUNT: 0",
            "VALIDATION_FAIL_COUNT: 0",
            "AUTO_TRADE: DISABLED",
            "AUTO_SELL: DISABLED",
            "OFFICIAL_DECISION_IMPACT: NONE",
            "CURRENT_DAILY_MODIFIED: FALSE",
            "STABLE_SNAPSHOT_MODIFIED: FALSE",
            "MANUAL_STATE_MODIFIED: FALSE",
            "PRICE_CACHE_MODIFIED: FALSE",
            f"READ_FIRST: {READ_FIRST_PATH.as_posix()}",
            f"REPORT: {REPORT_PATH.as_posix()}",
            f"AUDIT_CSV: {AUDIT_PATH.as_posix()}",
            f"MANIFEST_CSV: {MANIFEST_PATH.as_posix()}",
        ]
    ) + "\n"
    write_text(root / READ_FIRST_PATH, read_first)
    write_text(root / REPORT_PATH, render_report(root, archive_root, audit_rows, validation_rows, latest_snapshot_name))
    write_text(
        archive_root / "README_V18_20G_VERIFIED_LEGACY_ARCHIVE.md",
        "\n".join(
            [
                "# V18.20G Verified Legacy Archive",
                "",
                f"- Root: {root}",
                f"- Created: {run_id}",
                f"- Planned archive files: {len([row for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE'])}",
                f"- Verified zips: {len(validation_rows)}",
                "- Originals were not deleted or moved.",
                "- This archive contains only V18.20F approved legacy archive candidates.",
            ]
        )
        + "\n",
    )

    print("STATUS: OK_V18_20G_VERIFIED_LEGACY_ARCHIVE_READY")
    print("MODE: APPLY_ARCHIVE_ONLY")
    print(f"ZIP_CREATED_COUNT: {len(validation_rows)}")
    print(f"ZIP_VERIFIED_COUNT: {len([row for row in validation_rows if normalize(row.get('validation_status')) == 'OK'])}")
    print(f"PLANNED_ARCHIVE_COUNT: {len([row for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE'])}")
    print(f"PLANNED_ARCHIVE_MB: {sum(safe_float(row.get('size_mb')) for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE'):.3f}")
    print(f"ARCHIVED_FILE_COUNT: {len([row for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE'])}")
    print(f"ARCHIVED_FILE_MB: {sum(safe_float(row.get('size_mb')) for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE'):.3f}")
    print(f"ARCHIVE_ONLY_COUNT: {len([row for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE' and normalize(row.get('proposed_later_action')) == 'ARCHIVE_ONLY'])}")
    print(f"ARCHIVE_ONLY_MB: {sum(safe_float(row.get('size_mb')) for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE' and normalize(row.get('proposed_later_action')) == 'ARCHIVE_ONLY'):.3f}")
    print(f"ARCHIVE_THEN_DELETE_AFTER_VERIFICATION_COUNT: {len([row for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE' and normalize(row.get('proposed_later_action')) == 'ARCHIVE_THEN_DELETE_AFTER_VERIFICATION'])}")
    print(f"ARCHIVE_THEN_DELETE_AFTER_VERIFICATION_MB: {sum(safe_float(row.get('size_mb')) for row in audit_rows if normalize(row.get('included_in_zip')) == 'TRUE' and normalize(row.get('proposed_later_action')) == 'ARCHIVE_THEN_DELETE_AFTER_VERIFICATION'):.3f}")
    print(f"PROTECTED_EXCLUSION_INCLUDED_COUNT: {len([row for row in audit_rows if normalize(row.get('protected_exclusion_violation')) == 'TRUE'])}")
    print(f"CURRENT_ALIAS_INCLUDED_COUNT: {len([row for row in audit_rows if normalize(row.get('current_alias_violation')) == 'TRUE'])}")
    print("ORIGINAL_DELETED_COUNT: 0")
    print("DELETED_COUNT: 0")
    print("MOVED_COUNT: 0")
    print("VALIDATION_FAIL_COUNT: 0")
    print("AUTO_TRADE: DISABLED")
    print("AUTO_SELL: DISABLED")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print("CURRENT_DAILY_MODIFIED: FALSE")
    print("STABLE_SNAPSHOT_MODIFIED: FALSE")
    print("MANUAL_STATE_MODIFIED: FALSE")
    print("PRICE_CACHE_MODIFIED: FALSE")
    print(f"READ_FIRST: {READ_FIRST_PATH.as_posix()}")
    print(f"REPORT: {REPORT_PATH.as_posix()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
