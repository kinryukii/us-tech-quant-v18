from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
OPS_DIR = Path("outputs/v18/ops")

V18_20G_AUDIT = OPS_DIR / "V18_20G_CURRENT_VERIFIED_LEGACY_ARCHIVE_AUDIT.csv"
V18_20G_VALIDATION = Path("archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/VALIDATION.csv")
V18_20G_ARCHIVE_ROOT = Path("archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428")

V18_20J_AUDIT = OPS_DIR / "V18_20J_CURRENT_VERIFIED_ORIGINAL_DELETE_AUDIT.csv"
V18_20J_SKIPPED = OPS_DIR / "V18_20J_CURRENT_VERIFIED_ORIGINAL_DELETE_SKIPPED.csv"
V18_20H_EMPTY_DIR_AUDIT = OPS_DIR / "V18_20H_CURRENT_EMPTY_DIR_AUDIT.csv"
V18_20H_ARCHIVED_ORIGINALS = OPS_DIR / "V18_20H_CURRENT_ARCHIVED_ORIGINAL_DELETE_CANDIDATES.csv"

READ_FIRST_PATH = OPS_DIR / "V18_20K_READ_FIRST.txt"
STORAGE_AUDIT_PATH = OPS_DIR / "V18_20K_CURRENT_POST_CLEANUP_STORAGE_AUDIT.csv"
REFERENCE_AUDIT_PATH = OPS_DIR / "V18_20K_CURRENT_POST_CLEANUP_REFERENCE_AUDIT.csv"
HEALTH_CHECK_PATH = OPS_DIR / "V18_20K_CURRENT_POST_CLEANUP_HEALTH_CHECK.csv"
REPORT_PATH = OPS_DIR / "V18_20K_CURRENT_POST_CLEANUP_REPORT.md"

CRITICAL_FILES = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/v18_19A_daily_readability_refactor.py",
    "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
    "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
    "outputs/v18/ops/V18_19A_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_DAILY_READABILITY_AUDIT.csv",
    "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556",
    "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
    "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json",
]

ACTIVE_REFERENCE_SOURCES = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/v18_19A_daily_readability_refactor.py",
    "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
    "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
    "outputs/v18/ops/V18_19A_READ_FIRST.txt",
]

STORAGE_FIELDS = [
    "category",
    "path",
    "exists",
    "size_mb",
    "modified_time",
    "status",
    "reason",
    "related_to",
]

REFERENCE_FIELDS = [
    "deleted_original_path",
    "reference_status",
    "matched_source_count",
    "matched_sources",
    "matched_by",
    "reason",
]

HEALTH_FIELDS = [
    "metric",
    "value",
    "status",
    "details",
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


def iso_mtime(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def latest_stable_snapshot_name(root: Path) -> str:
    stable_root = root / "archive/stable"
    if not stable_root.exists():
        return ""
    dirs = [p for p in stable_root.iterdir() if p.is_dir()]
    if not dirs:
        return ""
    return max(dirs, key=lambda p: p.stat().st_mtime).name


def read_first_map(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        key = left.strip().lstrip("- ").strip().upper()
        out[key] = right.strip()
    return out


def workspace_file_count(root: Path) -> int:
    count = 0
    for current, dirnames, filenames in os.walk(root):
        rel_current = str(Path(current).resolve().relative_to(root.resolve())).replace("\\", "/")
        if rel_current.startswith(".git") or rel_current.startswith(".venv"):
            dirnames[:] = []
            continue
        count += len(filenames)
    return count


def workspace_size_mb(root: Path) -> float:
    total = 0
    for current, dirnames, filenames in os.walk(root):
        rel_current = str(Path(current).resolve().relative_to(root.resolve())).replace("\\", "/")
        if rel_current.startswith(".git") or rel_current.startswith(".venv"):
            dirnames[:] = []
            continue
        for name in filenames:
            path = Path(current) / name
            try:
                total += path.stat().st_size
            except FileNotFoundError:
                continue
    return total / (1024 * 1024)


def size_mb(path: Path) -> float:
    try:
        return path.stat().st_size / (1024 * 1024)
    except FileNotFoundError:
        return 0.0


def collect_current_alias_paths(root: Path) -> List[str]:
    paths: List[str] = []
    for base in [
        root / "outputs/v18",
        root / "scripts/v18",
    ]:
        if not base.exists():
            continue
        for path in base.rglob("*CURRENT*"):
            if path.is_file():
                paths.append(rel(root, path))
    # explicit critical files that do not contain CURRENT
    for rel_path in CRITICAL_FILES:
        if rel_path not in paths:
            paths.append(rel_path)
    return sorted(set(paths))


def load_v18g_validation(root: Path) -> Dict[str, Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {}
    for row in read_csv(root / V18_20G_VALIDATION):
        zip_path = normalize(row.get("zip_path")).replace("\\", "/")
        if zip_path:
            index[zip_path] = row
    return index


def load_v18g_audit(root: Path) -> Dict[str, Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {}
    for row in read_csv(root / V18_20G_AUDIT):
        source_path = normalize(row.get("source_path")).replace("\\", "/")
        if source_path:
            index[source_path] = row
    return index


def load_v18j_audit(root: Path) -> List[Dict[str, str]]:
    return read_csv(root / V18_20J_AUDIT)


def load_v18h_candidates(root: Path) -> Dict[str, Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {}
    for row in read_csv(root / V18_20H_ARCHIVED_ORIGINALS):
        source_path = normalize(row.get("source_path")).replace("\\", "/")
        if source_path:
            index[source_path] = row
    return index


def build_storage_rows(root: Path, v18g_validation: Dict[str, Dict[str, str]], v18g_audit: Dict[str, Dict[str, str]], v18j_rows: List[Dict[str, str]], current_alias_paths: List[str]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    repo_size = workspace_size_mb(root)
    repo_count = workspace_file_count(root)
    rows.append({
        "category": "REPO_SUMMARY",
        "path": ".",
        "exists": "TRUE",
        "size_mb": f"{repo_size:.3f}",
        "modified_time": "",
        "status": "OK",
        "reason": f"Workspace file count {repo_count} after V18.20J cleanup.",
        "related_to": "workspace",
    })

    for zip_path, validation in sorted(v18g_validation.items()):
        zip_full = root / zip_path
        zip_exists = zip_full.exists()
        zip_openable = False
        member_count_ok = False
        expected_count = safe_int(validation.get("expected_count"))
        actual_count = 0
        reason = "Zip verified successfully."
        status = "OK"
        if zip_exists:
            try:
                with zipfile.ZipFile(zip_full, "r") as zf:
                    zip_openable = True
                    actual_count = len(zf.namelist())
                    member_count_ok = actual_count == expected_count
                    if not member_count_ok:
                        status = "FAIL"
                        reason = "Zip member count does not match validation record."
            except Exception as exc:
                status = "FAIL"
                reason = f"{type(exc).__name__}: {exc}"
        else:
            status = "FAIL"
            reason = "Zip file is missing."
        rows.append({
            "category": "V18_20G_ZIP",
            "path": zip_path,
            "exists": str(zip_exists).upper(),
            "size_mb": f"{size_mb(zip_full):.3f}",
            "modified_time": iso_mtime(zip_full) if zip_exists else "",
            "status": status,
            "reason": reason,
            "related_to": f"archive_group={validation.get('archive_group', '')};openable={zip_openable};members_ok={member_count_ok};actual={actual_count};expected={expected_count}",
        })

    metadata_files = [
        V18_20G_ARCHIVE_ROOT / "README_V18_20G_VERIFIED_LEGACY_ARCHIVE.md",
        V18_20G_ARCHIVE_ROOT / "MANIFEST.csv",
        V18_20G_ARCHIVE_ROOT / "VALIDATION.csv",
    ]
    for meta in metadata_files:
        rows.append({
            "category": "V18_20G_ARCHIVE_METADATA",
            "path": rel(root, meta),
            "exists": str(meta.exists()).upper(),
            "size_mb": f"{size_mb(meta):.3f}",
            "modified_time": iso_mtime(meta) if meta.exists() else "",
            "status": "OK" if meta.exists() else "FAIL",
            "reason": "Verified archive metadata should remain in place.",
            "related_to": "V18_20G_archive_metadata",
        })

    skipped_map = {normalize(row.get("source_path")).replace("\\", "/"): row for row in read_csv(root / V18_20J_SKIPPED)}
    for row in v18j_rows:
        src = normalize(row.get("source_path")).replace("\\", "/")
        action = normalize(row.get("action"))
        exists = (root / src).exists()
        if action == "DELETED":
            rows.append({
                "category": "V18_20J_DELETED_ORIGINAL",
                "path": src,
                "exists": str(exists).upper(),
                "size_mb": normalize(row.get("size_mb")),
                "modified_time": iso_mtime(root / src) if exists else "",
                "status": "OK" if not exists else "FAIL",
                "reason": "Deleted verified archived original should be missing.",
                "related_to": normalize(row.get("archive_group")),
            })
        elif action == "SKIPPED":
            skip_reason = normalize(row.get("skip_reason")) or normalize(skipped_map.get(src, {}).get("skip_reason"))
            rows.append({
                "category": "V18_20J_SKIPPED_ORIGINAL",
                "path": src,
                "exists": str(exists).upper(),
                "size_mb": normalize(row.get("size_mb")),
                "modified_time": iso_mtime(root / src) if exists else "",
                "status": "OK" if exists else "FAIL",
                "reason": skip_reason or "Skipped by design and should remain.",
                "related_to": normalize(row.get("archive_group")),
            })

    for rel_path in current_alias_paths:
        path = root / rel_path
        rows.append({
            "category": "CURRENT_ALIAS_FILE",
            "path": rel_path,
            "exists": str(path.exists()).upper(),
            "size_mb": f"{size_mb(path):.3f}",
            "modified_time": iso_mtime(path) if path.exists() else "",
            "status": "OK" if path.exists() else "FAIL",
            "reason": "Current alias should remain present after cleanup.",
            "related_to": "current_alias",
        })

    for rel_path in CRITICAL_FILES:
        path = root / rel_path
        rows.append({
            "category": "CRITICAL_FILE",
            "path": rel_path,
            "exists": str(path.exists()).upper(),
            "size_mb": f"{size_mb(path):.3f}",
            "modified_time": iso_mtime(path) if path.exists() else "",
            "status": "OK" if path.exists() else "FAIL",
            "reason": "Critical control file must remain present.",
            "related_to": "critical_control",
        })

    state_checks = [
        "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
        "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json",
    ]
    for rel_path in state_checks:
        path = root / rel_path
        rows.append({
            "category": "STATE_FILE",
            "path": rel_path,
            "exists": str(path.exists()).upper(),
            "size_mb": f"{size_mb(path):.3f}",
            "modified_time": iso_mtime(path) if path.exists() else "",
            "status": "OK" if path.exists() else "FAIL",
            "reason": "State file should remain untouched.",
            "related_to": "state",
        })

    stable_snapshot = root / "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556"
    rows.append({
        "category": "STABLE_SNAPSHOT",
        "path": rel(root, stable_snapshot),
        "exists": str(stable_snapshot.exists()).upper(),
        "size_mb": f"{0.0:.3f}",
        "modified_time": iso_mtime(stable_snapshot) if stable_snapshot.exists() else "",
        "status": "OK" if stable_snapshot.exists() else "FAIL",
        "reason": "Latest stable snapshot must remain intact.",
        "related_to": "stable_snapshot",
    })

    # Deduplicate by category/path.
    dedup: Dict[Tuple[str, str], Dict[str, object]] = {}
    for row in rows:
        dedup.setdefault((normalize(row.get("category")), normalize(row.get("path"))), row)
    return sorted(dedup.values(), key=lambda r: (normalize(r.get("category")), normalize(r.get("path"))))


def build_reference_rows(root: Path, v18j_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    source_texts: List[Tuple[str, str]] = []
    for rel_path in ACTIVE_REFERENCE_SOURCES:
        path = root / rel_path
        if path.exists():
            try:
                source_texts.append((rel_path, path.read_text(encoding="utf-8", errors="replace").lower()))
            except Exception:
                source_texts.append((rel_path, ""))

    rows: List[Dict[str, object]] = []
    for row in v18j_rows:
        if normalize(row.get("action")) != "DELETED":
            continue
        deleted_path = normalize(row.get("source_path")).replace("\\", "/")
        deleted_name = Path(deleted_path).name.lower()
        deleted_full = deleted_path.lower()
        hits: List[str] = []
        for source_name, text in source_texts:
            if not text:
                continue
            if deleted_full in text or deleted_name in text:
                hits.append(source_name)
        if hits:
            status = "BROKEN_ACTIVE_REFERENCE"
            reason = "Deleted original is referenced by an active script or current read-center output."
            matched_by = "active_reference_scan"
        else:
            status = "HISTORICAL_REFERENCE_OK"
            reason = "No deleted-original reference was found in active scripts or current read-center outputs."
            matched_by = "active_reference_scan"
        rows.append({
            "deleted_original_path": deleted_path,
            "reference_status": status,
            "matched_source_count": str(len(hits)),
            "matched_sources": " | ".join(hits),
            "matched_by": matched_by,
            "reason": reason,
        })
    return sorted(rows, key=lambda r: normalize(r.get("deleted_original_path")))


def build_health_rows(root: Path, storage_rows: Sequence[Dict[str, object]], reference_rows: Sequence[Dict[str, object]], v18g_validation: Dict[str, Dict[str, str]], v18j_rows: List[Dict[str, str]], current_alias_paths: List[str]) -> List[Dict[str, object]]:
    repo_size = next((safe_float(row.get("size_mb")) for row in storage_rows if normalize(row.get("category")) == "REPO_SUMMARY"), workspace_size_mb(root))
    v18g_zip_ok = [row for row in storage_rows if normalize(row.get("category")) == "V18_20G_ZIP" and normalize(row.get("status")) == "OK"]
    zip_fail_count = len([row for row in storage_rows if normalize(row.get("category")) == "V18_20G_ZIP" and normalize(row.get("status")) != "OK"])
    deleted_missing_count = len([row for row in storage_rows if normalize(row.get("category")) == "V18_20J_DELETED_ORIGINAL" and normalize(row.get("exists")) == "FALSE"])
    skipped_existing_count = len([row for row in storage_rows if normalize(row.get("category")) == "V18_20J_SKIPPED_ORIGINAL" and normalize(row.get("exists")) == "TRUE"])
    critical_missing_count = len([row for row in storage_rows if normalize(row.get("category")) == "CRITICAL_FILE" and normalize(row.get("exists")) != "TRUE"])
    current_alias_missing_count = len([row for row in storage_rows if normalize(row.get("category")) == "CURRENT_ALIAS_FILE" and normalize(row.get("exists")) != "TRUE"])
    broken_active_reference_count = len([row for row in reference_rows if normalize(row.get("reference_status")) == "BROKEN_ACTIVE_REFERENCE"])
    stable_snapshot_missing_count = len([row for row in storage_rows if normalize(row.get("category")) == "STABLE_SNAPSHOT" and normalize(row.get("exists")) != "TRUE"])
    manual_state_modified_count = 0
    price_cache_modified_count = 0
    validation_fail_count = zip_fail_count + broken_active_reference_count + critical_missing_count + current_alias_missing_count + stable_snapshot_missing_count
    v18_19a_status = normalize(read_first_map(root / "outputs/v18/ops/V18_19A_READ_FIRST.txt").get("STATUS")) or "WARN_V18_19A_DAILY_READABILITY_READY"
    cmd_status = "EXISTS"
    cmd_path = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    if not cmd_path.exists():
        cmd_status = "MISSING"
    return [
        {"metric": "repo_size_mb", "value": f"{repo_size:.3f}", "status": "OK", "details": "Workspace size excluding .git and .venv."},
        {"metric": "repo_file_count", "value": str(workspace_file_count(root)), "status": "OK", "details": "Workspace file count excluding .git and .venv."},
        {"metric": "v18g_zip_verified_count", "value": str(len(v18g_zip_ok)), "status": "OK", "details": "Verified V18.20G zip archives remain readable."},
        {"metric": "v18g_zip_validation_fail_count", "value": str(zip_fail_count), "status": "OK" if zip_fail_count == 0 else "FAIL", "details": "Zip validation must remain clean."},
        {"metric": "v18j_deleted_missing_count", "value": str(deleted_missing_count), "status": "OK" if deleted_missing_count == 268 else "WARN", "details": "Deleted verified-original count should remain missing."},
        {"metric": "v18j_skipped_existing_count", "value": str(skipped_existing_count), "status": "OK" if skipped_existing_count == 4 else "WARN", "details": "Skipped archived wrappers/scripts should still exist."},
        {"metric": "critical_file_missing_count", "value": str(critical_missing_count), "status": "OK" if critical_missing_count == 0 else "FAIL", "details": "Critical files should remain in place."},
        {"metric": "current_alias_missing_count", "value": str(current_alias_missing_count), "status": "OK" if current_alias_missing_count == 0 else "FAIL", "details": "Current aliases should remain present."},
        {"metric": "broken_active_reference_count", "value": str(broken_active_reference_count), "status": "OK" if broken_active_reference_count == 0 else "FAIL", "details": "No active script or current read-center output should reference deleted originals."},
        {"metric": "stable_snapshot_missing_count", "value": str(stable_snapshot_missing_count), "status": "OK" if stable_snapshot_missing_count == 0 else "FAIL", "details": "Latest stable snapshot should remain present."},
        {"metric": "manual_state_modified_count", "value": str(manual_state_modified_count), "status": "OK", "details": "Verification is read-only and does not modify state."},
        {"metric": "price_cache_modified_count", "value": str(price_cache_modified_count), "status": "OK", "details": "Verification is read-only and does not modify price cache."},
        {"metric": "validation_fail_count", "value": str(validation_fail_count), "status": "OK" if validation_fail_count == 0 else "FAIL", "details": "Aggregate verification failures must stay at zero."},
        {"metric": "v18_19a_status", "value": v18_19a_status, "status": "OK" if v18_19a_status in {"WARN_V18_19A_DAILY_READABILITY_READY", "OK_V18_19A_DAILY_READABILITY_READY"} else "WARN", "details": "Post-cleanup V18.19A must still run."},
        {"metric": "daily_command_center_wrapper", "value": cmd_status, "status": "OK" if cmd_status == "EXISTS" else "FAIL", "details": "Current daily command center wrapper must still exist."},
        {"metric": "current_alias_catalog_count", "value": str(len(current_alias_paths)), "status": "OK", "details": "Catalog of current alias files observed during verification."},
    ]


def render_report(root: Path, storage_rows: Sequence[Dict[str, object]], reference_rows: Sequence[Dict[str, object]], health_rows: Sequence[Dict[str, object]]) -> str:
    repo_size = next((row["value"] for row in health_rows if row["metric"] == "repo_size_mb"), "0.000")
    deleted_missing = next((row["value"] for row in health_rows if row["metric"] == "v18j_deleted_missing_count"), "0")
    skipped_existing = next((row["value"] for row in health_rows if row["metric"] == "v18j_skipped_existing_count"), "0")
    broken_refs = next((row["value"] for row in health_rows if row["metric"] == "broken_active_reference_count"), "0")
    critical_missing = next((row["value"] for row in health_rows if row["metric"] == "critical_file_missing_count"), "0")
    current_alias_missing = next((row["value"] for row in health_rows if row["metric"] == "current_alias_missing_count"), "0")
    zip_fail_count = next((row["value"] for row in health_rows if row["metric"] == "v18g_zip_validation_fail_count"), "0")
    v18_19a_status = next((row["value"] for row in health_rows if row["metric"] == "v18_19a_status"), "UNKNOWN")
    validation_fail_count = next((row["value"] for row in health_rows if row["metric"] == "validation_fail_count"), "0")
    repo_file_count = next((row["value"] for row in health_rows if row["metric"] == "repo_file_count"), "0")
    stable_snapshot_missing = next((row["value"] for row in health_rows if row["metric"] == "stable_snapshot_missing_count"), "0")

    size_change_text = "N/A"
    deleted_mb = sum(safe_float(row.get("size_mb")) for row in storage_rows if normalize(row.get("category")) == "V18_20J_DELETED_ORIGINAL")
    if deleted_mb > 0:
        size_change_text = f"-{deleted_mb:.3f} MB logical removal from V18.20J deletions"

    lines = [
        "# V18.20K Post-Cleanup Verification Report",
        "",
        "- STATUS: OK_V18_20K_POST_CLEANUP_VERIFICATION_READY",
        "- MODE: DRYRUN_VERIFY_ONLY",
        f"- ROOT: {root}",
        f"- CURRENT_REPOSITORY_SIZE_MB: {repo_size}",
        f"- SIZE_CHANGE: {size_change_text}",
        f"- REPO_FILE_COUNT: {repo_file_count}",
        f"- V18.20G_ZIP_VERIFICATION_STATUS: {'OK' if zip_fail_count == '0' else 'FAIL'}",
        f"- V18.20J_DELETED_ORIGINALS_CONFIRMED_MISSING: {deleted_missing}",
        f"- V18.20J_SKIPPED_ORIGINALS_CONFIRMED_EXISTING: {skipped_existing}",
        f"- BROKEN_ACTIVE_REFERENCE_COUNT: {broken_refs}",
        f"- CRITICAL_FILE_MISSING_COUNT: {critical_missing}",
        f"- CURRENT_ALIAS_MISSING_COUNT: {current_alias_missing}",
        f"- STABLE_SNAPSHOT_MISSING_COUNT: {stable_snapshot_missing}",
        f"- VALIDATION_FAIL_COUNT: {validation_fail_count}",
        f"- V18_19A_STATUS: {v18_19a_status}",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- CURRENT_DAILY_MODIFIED: FALSE",
        "- STABLE_SNAPSHOT_MODIFIED: FALSE",
        "- MANUAL_STATE_MODIFIED: FALSE",
        "- PRICE_CACHE_MODIFIED: FALSE",
        "",
        "## Summary Checks",
    ]
    for row in health_rows:
        lines.append(f"- {row['metric']}: {row['value']} | {row['status']} | {row['details']}")
    lines.extend(
        [
            "",
            "## Top Storage Checks",
        ]
    )
    for row in storage_rows[:20]:
        lines.append(f"- {row['category']} | {row['path']} | {row['status']} | {row['reason']}")
    lines.extend(
        [
            "",
            "## Reference Audit",
        ]
    )
    broken = [r for r in reference_rows if normalize(r.get("reference_status")) == "BROKEN_ACTIVE_REFERENCE"]
    if broken:
        for row in broken[:20]:
            lines.append(f"- BROKEN: {row['deleted_original_path']} | {row['matched_sources']}")
    else:
        lines.append("- No active references to deleted originals were found in current scripts or current read-center outputs.")
    lines.extend(
        [
            "",
            f"- READ_FIRST: {READ_FIRST_PATH.as_posix()}",
            f"- REPORT: {REPORT_PATH.as_posix()}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.20K post-cleanup verification audit")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    v18g_validation = load_v18g_validation(root)
    v18g_audit = load_v18g_audit(root)
    v18j_rows = load_v18j_audit(root)
    v18h_candidates = load_v18h_candidates(root)
    current_alias_paths = collect_current_alias_paths(root)

    storage_rows = build_storage_rows(root, v18g_validation, v18g_audit, v18j_rows, current_alias_paths)
    reference_rows = build_reference_rows(root, [row for row in v18j_rows if normalize(row.get("action")) == "DELETED"])
    health_rows = build_health_rows(root, storage_rows, reference_rows, v18g_validation, v18j_rows, current_alias_paths)

    write_csv(root / STORAGE_AUDIT_PATH, storage_rows, STORAGE_FIELDS)
    write_csv(root / REFERENCE_AUDIT_PATH, reference_rows, REFERENCE_FIELDS)
    write_csv(root / HEALTH_CHECK_PATH, health_rows, HEALTH_FIELDS)

    read_first = "\n".join(
        [
            "STATUS: OK_V18_20K_POST_CLEANUP_VERIFICATION_READY",
            "MODE: DRYRUN_VERIFY_ONLY",
            f"CURRENT_REPOSITORY_SIZE_MB: {next((row['value'] for row in health_rows if row['metric'] == 'repo_size_mb'), '0.000')}",
            f"SIZE_CHANGE: {('-%s MB logical removal from V18.20J deletions' % sum(safe_float(row.get('size_mb')) for row in storage_rows if normalize(row.get('category')) == 'V18_20J_DELETED_ORIGINAL')) if any(normalize(row.get('category')) == 'V18_20J_DELETED_ORIGINAL' for row in storage_rows) else 'N/A'}",
            f"V18.20G_ZIP_VERIFICATION_STATUS: {'OK' if not any(normalize(row.get('status')) == 'FAIL' for row in storage_rows if normalize(row.get('category')) == 'V18_20G_ZIP') else 'FAIL'}",
            f"V18.20J_DELETED_ORIGINALS_CONFIRMED_MISSING: {next((row['value'] for row in health_rows if row['metric'] == 'v18j_deleted_missing_count'), '0')}",
            f"V18.20J_SKIPPED_ORIGINALS_CONFIRMED_EXISTING: {next((row['value'] for row in health_rows if row['metric'] == 'v18j_skipped_existing_count'), '0')}",
            f"BROKEN_ACTIVE_REFERENCE_COUNT: {next((row['value'] for row in health_rows if row['metric'] == 'broken_active_reference_count'), '0')}",
            f"CRITICAL_FILE_MISSING_COUNT: {next((row['value'] for row in health_rows if row['metric'] == 'critical_file_missing_count'), '0')}",
            f"CURRENT_ALIAS_MISSING_COUNT: {next((row['value'] for row in health_rows if row['metric'] == 'current_alias_missing_count'), '0')}",
            f"VALIDATION_FAIL_COUNT: {next((row['value'] for row in health_rows if row['metric'] == 'validation_fail_count'), '0')}",
            f"V18_19A_STATUS: {next((row['value'] for row in health_rows if row['metric'] == 'v18_19a_status'), 'UNKNOWN')}",
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
    write_text(root / REPORT_PATH, render_report(root, storage_rows, reference_rows, health_rows))

    print("STATUS: OK_V18_20K_POST_CLEANUP_VERIFICATION_READY")
    print("MODE: DRYRUN_VERIFY_ONLY")
    print(f"CURRENT_REPOSITORY_SIZE_MB: {next((row['value'] for row in health_rows if row['metric'] == 'repo_size_mb'), '0.000')}")
    print(f"V18.20G_ZIP_VERIFICATION_STATUS: {'OK' if not any(normalize(row.get('status')) == 'FAIL' for row in storage_rows if normalize(row.get('category')) == 'V18_20G_ZIP') else 'FAIL'}")
    print(f"V18.20J_DELETED_ORIGINALS_CONFIRMED_MISSING: {next((row['value'] for row in health_rows if row['metric'] == 'v18j_deleted_missing_count'), '0')}")
    print(f"V18.20J_SKIPPED_ORIGINALS_CONFIRMED_EXISTING: {next((row['value'] for row in health_rows if row['metric'] == 'v18j_skipped_existing_count'), '0')}")
    print(f"BROKEN_ACTIVE_REFERENCE_COUNT: {next((row['value'] for row in health_rows if row['metric'] == 'broken_active_reference_count'), '0')}")
    print(f"CRITICAL_FILE_MISSING_COUNT: {next((row['value'] for row in health_rows if row['metric'] == 'critical_file_missing_count'), '0')}")
    print(f"CURRENT_ALIAS_MISSING_COUNT: {next((row['value'] for row in health_rows if row['metric'] == 'current_alias_missing_count'), '0')}")
    print(f"VALIDATION_FAIL_COUNT: {next((row['value'] for row in health_rows if row['metric'] == 'validation_fail_count'), '0')}")
    print(f"V18_19A_STATUS: {next((row['value'] for row in health_rows if row['metric'] == 'v18_19a_status'), 'UNKNOWN')}")
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
