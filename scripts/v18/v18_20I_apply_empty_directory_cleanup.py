from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Dict, List


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
OPS_DIR = Path("outputs/v18/ops")

EMPTY_DIR_AUDIT_SOURCE = OPS_DIR / "V18_20H_CURRENT_EMPTY_DIR_AUDIT.csv"
READ_FIRST_PATH = OPS_DIR / "V18_20I_READ_FIRST.txt"
DELETE_AUDIT_PATH = OPS_DIR / "V18_20I_CURRENT_EMPTY_DIR_DELETE_AUDIT.csv"
REPORT_PATH = OPS_DIR / "V18_20I_CURRENT_EMPTY_DIR_CLEANUP_REPORT.md"

PROTECTED_PREFIXES = (
    ".git/",
    ".venv/",
    "state/",
    "configs/",
    "archive/stable/",
    "archive/stable_compressed/",
    "archive/generated_outputs_compressed/",
    "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428",
    "provider_cache/",
    "price_cache/",
)

ACTIVE_DIRS = {
    "outputs/v18/read_center",
    "outputs/v18/read_center/daily_packet",
    "outputs/v18/ops",
    "outputs/v18/universe",
    "outputs/v18/ranking",
    "outputs/v18/factor_pack",
    "outputs/v18/data",
    "outputs/v18/risk",
}

DELETE_FIELDS = [
    "path",
    "parent",
    "category",
    "mode",
    "action",
    "skip_reason",
    "existed_before",
    "exists_after",
    "validation_status",
]


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


def write_csv(path: Path, rows: List[Dict[str, object]], fields: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def is_protected(rel_path: str) -> bool:
    lower = rel_path.lower()
    return any(lower.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def is_active_dir(rel_path: str) -> bool:
    lower = rel_path.lower()
    return any(lower == d or lower.startswith(d + "/") for d in ACTIVE_DIRS)


def is_empty_dir(path: Path) -> bool:
    try:
        return path.is_dir() and not any(path.iterdir())
    except Exception:
        return False


def validate_candidate(root: Path, row: Dict[str, str]) -> Dict[str, object]:
    rel_path = normalize(row.get("path")).replace("\\", "/")
    path = root / rel_path
    category = normalize(row.get("category"))
    existed_before = path.exists()
    exists_after = existed_before
    skip_reason = ""
    action = "WOULD_DELETE"
    validation_status = "OK"

    if not existed_before:
        action = "SKIPPED"
        validation_status = "MISSING"
        skip_reason = "Directory does not exist."
    elif not path.is_dir():
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "Path is not a directory."
    elif not rel_path.startswith("archive/deprecated/") and is_protected(rel_path):
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "Protected path."
    elif is_active_dir(rel_path):
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "Active current output directory."
    elif not category == "EMPTY_DIR_DELETE_CANDIDATE":
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "Not classified as delete candidate in V18.20H."
    elif not is_empty_dir(path):
        action = "SKIPPED"
        validation_status = "BLOCKED"
        skip_reason = "Directory is not empty at apply time."

    return {
        "path": rel_path,
        "parent": rel(root, path.parent) if existed_before else str(Path(rel_path).parent).replace("\\", "/"),
        "category": category,
        "mode": "APPLY" if action == "DELETED" else "DRYRUN",
        "action": action,
        "skip_reason": skip_reason,
        "existed_before": str(existed_before).upper(),
        "exists_after": str(exists_after).upper(),
        "validation_status": validation_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.20I apply empty directory cleanup")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    parser.add_argument("--apply", action="store_true", help="Delete empty directories that pass safety checks.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    source_rows = read_csv(root / EMPTY_DIR_AUDIT_SOURCE)
    candidate_rows = [row for row in source_rows if normalize(row.get("category")) == "EMPTY_DIR_DELETE_CANDIDATE"]

    audit_rows: List[Dict[str, object]] = []
    deleted_count = 0
    skipped_count = 0
    fail_count = 0

    for row in candidate_rows:
        result = validate_candidate(root, row)
        if args.apply and result["action"] == "WOULD_DELETE":
            try:
                os.rmdir(root / result["path"])
                result["action"] = "DELETED"
                result["mode"] = "APPLY"
                result["exists_after"] = str((root / result["path"]).exists()).upper()
                deleted_count += 1
            except Exception as exc:
                result["action"] = "SKIPPED"
                result["validation_status"] = "FAIL"
                result["skip_reason"] = f"{type(exc).__name__}: {exc}"
                result["mode"] = "APPLY"
                fail_count += 1
        if result["action"] == "DELETED":
            deleted_count += 0
        elif result["action"] == "SKIPPED":
            skipped_count += 1
        audit_rows.append(result)

    mode = "APPLY" if args.apply else "DRYRUN"
    would_delete_count = sum(1 for row in audit_rows if row["action"] == "WOULD_DELETE")
    delete_fail_count = fail_count

    write_csv(root / DELETE_AUDIT_PATH, audit_rows, DELETE_FIELDS)

    read_first = "\n".join(
        [
            "STATUS: OK_V18_20I_EMPTY_DIRECTORY_CLEANUP_READY",
            f"MODE: {mode}",
            f"DELETED_FILE_COUNT: 0",
            f"DELETED_DIR_COUNT: {deleted_count}",
            f"MOVED_COUNT: 0",
            f"ARCHIVED_COUNT: 0",
            f"WOULD_DELETE_DIR_COUNT: {would_delete_count}",
            f"DELETE_FAIL_COUNT: {delete_fail_count}",
            f"VALIDATION_FAIL_COUNT: {delete_fail_count}",
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

    report_lines = [
        "# V18.20I Empty Directory Cleanup Report",
        "",
        f"- STATUS: OK_V18_20I_EMPTY_DIRECTORY_CLEANUP_READY",
        f"- MODE: {mode}",
        f"- INPUT_DELETE_CANDIDATE_COUNT: {len(candidate_rows)}",
        f"- WOULD_DELETE_DIR_COUNT: {would_delete_count}",
        f"- DELETED_DIR_COUNT: {deleted_count}",
        f"- SKIPPED_DIR_COUNT: {skipped_count}",
        f"- DELETE_FAIL_COUNT: {delete_fail_count}",
        f"- DELETED_FILE_COUNT: 0",
        f"- VALIDATION_FAIL_COUNT: {delete_fail_count}",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- CURRENT_DAILY_MODIFIED: FALSE",
        "- STABLE_SNAPSHOT_MODIFIED: FALSE",
        "- MANUAL_STATE_MODIFIED: FALSE",
        "- PRICE_CACHE_MODIFIED: FALSE",
        "",
        "## Candidate Rows",
    ]
    for row in audit_rows:
        report_lines.append(
            f"- {row['path']} | {row['action']} | {row['validation_status']} | {row['skip_reason']}"
        )
    report_lines.extend(
        [
            "",
            f"- READ_FIRST: {READ_FIRST_PATH.as_posix()}",
            f"- REPORT: {REPORT_PATH.as_posix()}",
        ]
    )
    write_text(root / REPORT_PATH, "\n".join(report_lines) + "\n")

    print("STATUS: OK_V18_20I_EMPTY_DIRECTORY_CLEANUP_READY")
    print(f"MODE: {mode}")
    print("DELETED_FILE_COUNT: 0")
    print(f"DELETED_DIR_COUNT: {deleted_count}")
    print("MOVED_COUNT: 0")
    print("ARCHIVED_COUNT: 0")
    print(f"DELETE_FAIL_COUNT: {delete_fail_count}")
    print(f"VALIDATION_FAIL_COUNT: {delete_fail_count}")
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
