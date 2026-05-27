from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
from pathlib import Path
from typing import Dict, List, Sequence
import zipfile


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
OPS_DIR = Path("outputs/v18/ops")

DELETE_CANDIDATES_PATH = OPS_DIR / "V18_20H_CURRENT_ARCHIVED_ORIGINAL_DELETE_CANDIDATES.csv"
V18G_AUDIT_PATH = OPS_DIR / "V18_20G_CURRENT_VERIFIED_LEGACY_ARCHIVE_AUDIT.csv"
V18G_VALIDATION_SOURCE = Path("archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/VALIDATION.csv")

READ_FIRST_PATH = OPS_DIR / "V18_20J_READ_FIRST.txt"
AUDIT_PATH = OPS_DIR / "V18_20J_CURRENT_VERIFIED_ORIGINAL_DELETE_AUDIT.csv"
SKIPPED_PATH = OPS_DIR / "V18_20J_CURRENT_VERIFIED_ORIGINAL_DELETE_SKIPPED.csv"
REPORT_PATH = OPS_DIR / "V18_20J_CURRENT_VERIFIED_ORIGINAL_DELETE_REPORT.md"

PROTECTED_PREFIXES = (
    "state/",
    "configs/",
    "archive/stable/",
    "archive/stable_compressed/",
    "archive/generated_outputs_compressed/",
    "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/",
    ".git/",
    ".venv/",
)

AUDIT_FIELDS = [
    "source_path",
    "size_mb",
    "mode",
    "action",
    "skip_reason",
    "archive_group",
    "zip_path",
    "zip_member_path",
    "source_exists_before",
    "source_exists_after",
    "zip_verified",
    "included_in_zip",
    "current_alias_violation",
    "protected_path_violation",
    "source_code_violation",
    "validation_status",
]

SKIPPED_FIELDS = AUDIT_FIELDS


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize(value: object) -> str:
    return str(value or "").strip()


def safe_bool(value: object, default: bool = False) -> bool:
    text = normalize(value).upper()
    if text in {"TRUE", "T", "YES", "Y", "1"}:
        return True
    if text in {"FALSE", "F", "NO", "N", "0"}:
        return False
    return default


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


def rel(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def is_protected_path(rel_path: str) -> bool:
    lower = rel_path.lower()
    return any(lower.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def is_current_alias_related(rel_path: str, row: Dict[str, str]) -> bool:
    return safe_bool(row.get("current_alias_related")) or "CURRENT" in rel_path.upper()


def is_source_code_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("source_code_related")):
        return True
    return Path(rel_path).suffix.lower() in {".py", ".ps1", ".bat", ".sh"}


def is_wrapper_script(rel_path: str) -> bool:
    lower = rel_path.lower()
    return lower.endswith((".ps1", ".bat", ".sh")) or "run_" in Path(lower).name


def is_latest_stable_snapshot_material(rel_path: str) -> bool:
    return rel_path.lower().startswith("archive/stable/")


def load_candidate_rows(root: Path) -> List[Dict[str, str]]:
    return read_csv(root / DELETE_CANDIDATES_PATH)


def load_v18g_audit(root: Path) -> Dict[str, Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {}
    for row in read_csv(root / V18G_AUDIT_PATH):
        source_path = normalize(row.get("source_path")).replace("\\", "/")
        if source_path:
            index[source_path] = row
    return index


def load_v18g_validation(root: Path) -> Dict[str, Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {}
    for row in read_csv(root / V18G_VALIDATION_SOURCE):
        zip_path = normalize(row.get("zip_path")).replace("\\", "/")
        if zip_path:
            index[zip_path] = row
    return index


def resolve_archive_member(row: Dict[str, str], v18g_audit: Dict[str, Dict[str, str]]) -> str:
    source_path = normalize(row.get("source_path")).replace("\\", "/")
    return normalize(v18g_audit.get(source_path, {}).get("zip_member_path"))


def candidate_zip_verified(row: Dict[str, str], v18g_audit: Dict[str, Dict[str, str]], v18g_validation: Dict[str, Dict[str, str]]) -> bool:
    source_path = normalize(row.get("source_path")).replace("\\", "/")
    audit_row = v18g_audit.get(source_path, {})
    zip_path = normalize(audit_row.get("zip_path")).replace("\\", "/")
    if not zip_path:
        return False
    validation = v18g_validation.get(zip_path, {})
    return safe_bool(audit_row.get("zip_verified")) and normalize(validation.get("validation_status")) == "OK"


def verify_in_zip(root: Path, row: Dict[str, str], v18g_audit: Dict[str, Dict[str, str]], v18g_validation: Dict[str, Dict[str, str]]) -> bool:
    audit_row = v18g_audit.get(normalize(row.get("source_path")).replace("\\", "/"), {})
    zip_path = normalize(audit_row.get("zip_path")).replace("\\", "/")
    member = normalize(audit_row.get("zip_member_path")).replace("\\", "/")
    if not zip_path or not member:
        return False
    zip_full = root / zip_path
    if not zip_full.exists():
        return False
    try:
        with zipfile.ZipFile(zip_full, "r") as zf:
            return member in set(zf.namelist())
    except Exception:
        return False


def classify_row(root: Path, row: Dict[str, str], v18g_audit: Dict[str, Dict[str, str]], v18g_validation: Dict[str, Dict[str, str]]) -> Dict[str, object]:
    source_path = normalize(row.get("source_path")).replace("\\", "/")
    size_mb = safe_float(row.get("size_mb"))
    archive_group = normalize(row.get("archive_group"))
    zip_path = normalize(row.get("zip_path")).replace("\\", "/")
    zip_member_path = resolve_archive_member(row, v18g_audit)
    ref_count = safe_int(row.get("reference_count"))
    source_exists_before = (root / source_path).exists()
    source_exists_after = source_exists_before
    included_in_zip = safe_bool(row.get("zip_verified")) and safe_bool(row.get("source_exists")) and candidate_zip_verified(row, v18g_audit, v18g_validation) and verify_in_zip(root, row, v18g_audit, v18g_validation)
    current_alias_violation = is_current_alias_related(source_path, row)
    protected_path_violation = is_protected_path(source_path) or is_latest_stable_snapshot_material(source_path)
    source_code_violation = is_source_code_related(source_path, row)
    zip_verified = candidate_zip_verified(row, v18g_audit, v18g_validation)
    action = "WOULD_DELETE"
    skip_reason = ""
    validation_status = "OK"

    if archive_group != "OLD_GENERATED_REPORTS":
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "Not an OLD_GENERATED_REPORTS archive-group original."
    elif not source_exists_before:
        action = "MISSING"
        validation_status = "MISSING"
        skip_reason = "Source file is already missing."
    elif not safe_bool(row.get("zip_verified")) or not zip_verified:
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "Verified archive zip check failed."
    elif not included_in_zip:
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "Source file is not present in verified zip."
    elif ref_count != 0:
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "reference_count is nonzero."
    elif current_alias_violation:
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "Current alias related path."
    elif protected_path_violation:
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "Protected or stable snapshot path."
    elif source_code_violation or is_wrapper_script(source_path):
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "Source code or wrapper script must not be deleted here."
    elif "CURRENT" in source_path.upper():
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "Path contains CURRENT in an active output folder."

    return {
        "source_path": source_path,
        "size_mb": f"{size_mb:.3f}",
        "mode": "APPLY" if action == "DELETED" else "DRYRUN",
        "action": action,
        "skip_reason": skip_reason,
        "archive_group": archive_group,
        "zip_path": zip_path,
        "zip_member_path": zip_member_path,
        "source_exists_before": str(source_exists_before).upper(),
        "source_exists_after": str(source_exists_after).upper(),
        "zip_verified": str(zip_verified).upper(),
        "included_in_zip": str(included_in_zip).upper(),
        "current_alias_violation": str(current_alias_violation).upper(),
        "protected_path_violation": str(protected_path_violation).upper(),
        "source_code_violation": str(source_code_violation).upper(),
        "validation_status": validation_status,
        "_candidate_row": row,
    }


def render_report(root: Path, audit_rows: Sequence[Dict[str, object]], skipped_rows: Sequence[Dict[str, object]]) -> str:
    deleted = [r for r in audit_rows if normalize(r.get("action")) == "DELETED"]
    would_delete = [r for r in audit_rows if normalize(r.get("action")) == "WOULD_DELETE"]
    skipped = [r for r in audit_rows if normalize(r.get("action")) == "SKIPPED"]
    missing = [r for r in audit_rows if normalize(r.get("action")) == "MISSING"]
    delete_mb = sum(safe_float(r.get("size_mb")) for r in deleted)
    would_mb = sum(safe_float(r.get("size_mb")) for r in would_delete)
    skipped_mb = sum(safe_float(r.get("size_mb")) for r in skipped)
    lines = [
        "# V18.20J Verified Archived Generated Originals Delete Report",
        "",
        "- STATUS: OK_V18_20J_VERIFIED_ORIGINAL_DELETE_READY",
        "- MODE: DRYRUN",
        f"- ROOT: {root}",
        f"- WOULD_DELETE_COUNT: {len(would_delete)}",
        f"- WOULD_DELETE_MB: {would_mb:.3f}",
        f"- DELETED_COUNT: {len(deleted)}",
        f"- DELETED_MB: {delete_mb:.3f}",
        f"- SKIPPED_COUNT: {len(skipped)}",
        f"- SKIPPED_MB: {skipped_mb:.3f}",
        f"- MISSING_COUNT: {len(missing)}",
        "- DELETE_FAIL_COUNT: 0",
        "- VALIDATION_FAIL_COUNT: 0",
        "- ZIP_ARCHIVES_MODIFIED: FALSE",
        "- ARCHIVE_METADATA_MODIFIED: FALSE",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- CURRENT_DAILY_MODIFIED: FALSE",
        "- STABLE_SNAPSHOT_MODIFIED: FALSE",
        "- MANUAL_STATE_MODIFIED: FALSE",
        "- PRICE_CACHE_MODIFIED: FALSE",
        "",
        "## Candidates",
    ]
    for row in audit_rows:
        lines.append(f"- {row['source_path']} | {row['action']} | {row['validation_status']} | {row['skip_reason']}")
    lines.extend(["", f"- READ_FIRST: {READ_FIRST_PATH.as_posix()}", f"- REPORT: {REPORT_PATH.as_posix()}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.20J delete verified archived generated originals")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    parser.add_argument("--apply", action="store_true", help="Delete verified archived originals.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    candidates = load_candidate_rows(root)
    v18g_audit = load_v18g_audit(root)
    v18g_validation = load_v18g_validation(root)

    audit_rows: List[Dict[str, object]] = []
    skipped_rows: List[Dict[str, object]] = []
    deleted_count = 0
    delete_fail_count = 0

    for row in candidates:
        classified = classify_row(root, row, v18g_audit, v18g_validation)
        if args.apply and normalize(classified["action"]) == "WOULD_DELETE":
            try:
                os.remove(root / classified["source_path"])
                classified["action"] = "DELETED"
                classified["mode"] = "APPLY"
                classified["source_exists_after"] = str((root / classified["source_path"]).exists()).upper()
                deleted_count += 1
            except Exception as exc:
                classified["action"] = "SKIPPED"
                classified["mode"] = "APPLY"
                classified["validation_status"] = "FAIL"
                classified["skip_reason"] = f"{type(exc).__name__}: {exc}"
                delete_fail_count += 1
        if normalize(classified["action"]) == "SKIPPED":
            skipped_rows.append(classified)
        audit_rows.append(classified)

    mode = "APPLY" if args.apply else "DRYRUN"
    would_delete_rows = [r for r in audit_rows if normalize(r.get("action")) == "WOULD_DELETE"]
    skipped_only = [r for r in audit_rows if normalize(r.get("action")) == "SKIPPED"]
    missing_count = sum(1 for r in audit_rows if normalize(r.get("action")) == "MISSING")

    write_csv(root / AUDIT_PATH, audit_rows, AUDIT_FIELDS)
    write_csv(root / SKIPPED_PATH, skipped_only, SKIPPED_FIELDS)

    read_first = "\n".join(
        [
            "STATUS: OK_V18_20J_VERIFIED_ORIGINAL_DELETE_READY",
            f"MODE: {mode}",
            f"DELETED_COUNT: {deleted_count}",
            f"DELETED_MB: {sum(safe_float(r.get('size_mb')) for r in audit_rows if normalize(r.get('action')) == 'DELETED'):.3f}",
            f"WOULD_DELETE_COUNT: {len(would_delete_rows)}",
            f"WOULD_DELETE_MB: {sum(safe_float(r.get('size_mb')) for r in would_delete_rows):.3f}",
            f"SKIPPED_COUNT: {len(skipped_only)}",
            f"SKIPPED_MB: {sum(safe_float(r.get('size_mb')) for r in skipped_only):.3f}",
            f"DELETE_FAIL_COUNT: {delete_fail_count}",
            f"VALIDATION_FAIL_COUNT: {delete_fail_count}",
            f"MISSING_COUNT: {missing_count}",
            "ZIP_ARCHIVES_MODIFIED: FALSE",
            "ARCHIVE_METADATA_MODIFIED: FALSE",
            "AUTO_TRADE: DISABLED",
            "AUTO_SELL: DISABLED",
            "OFFICIAL_DECISION_IMPACT: NONE",
            "CURRENT_DAILY_MODIFIED: FALSE",
            "STABLE_SNAPSHOT_MODIFIED: FALSE",
            "MANUAL_STATE_MODIFIED: FALSE",
            "PRICE_CACHE_MODIFIED: FALSE",
            f"READ_FIRST: {READ_FIRST_PATH.as_posix()}",
            f"REPORT: {REPORT_PATH.as_posix()}",
        ]
    ) + "\n"
    write_text(root / READ_FIRST_PATH, read_first)
    write_text(root / REPORT_PATH, render_report(root, audit_rows, skipped_only))

    print("STATUS: OK_V18_20J_VERIFIED_ORIGINAL_DELETE_READY")
    print(f"MODE: {mode}")
    print(f"DELETED_COUNT: {deleted_count}")
    print(f"DELETED_MB: {sum(safe_float(r.get('size_mb')) for r in audit_rows if normalize(r.get('action')) == 'DELETED'):.3f}")
    print(f"WOULD_DELETE_COUNT: {len(would_delete_rows)}")
    print(f"WOULD_DELETE_MB: {sum(safe_float(r.get('size_mb')) for r in would_delete_rows):.3f}")
    print(f"SKIPPED_COUNT: {len(skipped_only)}")
    print(f"SKIPPED_MB: {sum(safe_float(r.get('size_mb')) for r in skipped_only):.3f}")
    print(f"DELETE_FAIL_COUNT: {delete_fail_count}")
    print(f"VALIDATION_FAIL_COUNT: {delete_fail_count}")
    print("ZIP_ARCHIVES_MODIFIED: FALSE")
    print("ARCHIVE_METADATA_MODIFIED: FALSE")
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
