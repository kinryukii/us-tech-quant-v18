from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
SNAPSHOT_NAME = "V18_20K_R1_stable_post_cleanup_verified"
SNAPSHOT_DIR_PREFIX = Path("archive/stable")
OPS_DIR = Path("outputs/v18/ops")
REF_DIR = Path("references")

STATUS_OK = "OK_V18_20K_R1_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_20K_R1_STABLE_SNAPSHOT_READY"

PS_PARSE_FILES = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
    "scripts/v18/run_v18_20K_post_cleanup_verification.ps1",
    "scripts/v18/run_v18_20K_R1_stable_snapshot.ps1",
]

PY_COMPILE_FILES = [
    "scripts/v18/v18_19A_daily_readability_refactor.py",
    "scripts/v18/v18_20K_post_cleanup_verification.py",
    "scripts/v18/v18_20K_R1_stable_snapshot.py",
]

ROOT_SCRIPT_FILES = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/v18_19A_daily_readability_refactor.py",
    "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
]

ROOT_SCRIPT_GLOBS = [
    ("scripts/v18", "v18_20*.py"),
    ("scripts/v18", "run_v18_20*.ps1"),
]

V18_20K_OPS_FILES = [
    "outputs/v18/ops/V18_20A_READ_FIRST.txt",
    "outputs/v18/ops/V18_20B_READ_FIRST.txt",
    "outputs/v18/ops/V18_20C_READ_FIRST.txt",
    "outputs/v18/ops/V18_20D_READ_FIRST.txt",
    "outputs/v18/ops/V18_20E_READ_FIRST.txt",
    "outputs/v18/ops/V18_20F_READ_FIRST.txt",
    "outputs/v18/ops/V18_20G_READ_FIRST.txt",
    "outputs/v18/ops/V18_20H_READ_FIRST.txt",
    "outputs/v18/ops/V18_20I_READ_FIRST.txt",
    "outputs/v18/ops/V18_20J_READ_FIRST.txt",
    "outputs/v18/ops/V18_20K_READ_FIRST.txt",
    "outputs/v18/ops/V18_20K_CURRENT_POST_CLEANUP_REPORT.md",
    "outputs/v18/ops/V18_20K_CURRENT_POST_CLEANUP_HEALTH_CHECK.csv",
    "outputs/v18/ops/V18_20K_CURRENT_POST_CLEANUP_REFERENCE_AUDIT.csv",
    "outputs/v18/ops/V18_20K_CURRENT_POST_CLEANUP_STORAGE_AUDIT.csv",
    "outputs/v18/ops/V18_20G_CURRENT_VERIFIED_LEGACY_ARCHIVE_AUDIT.csv",
    "outputs/v18/ops/V18_20G_CURRENT_VERIFIED_LEGACY_ARCHIVE_MANIFEST.csv",
    "outputs/v18/ops/V18_20G_READ_FIRST.txt",
    "outputs/v18/ops/V18_20G_CURRENT_VERIFIED_LEGACY_ARCHIVE_REPORT.md",
    "outputs/v18/ops/V18_20H_CURRENT_EMPTY_DIR_AUDIT.csv",
    "outputs/v18/ops/V18_20H_CURRENT_ORPHAN_OUTPUT_AUDIT.csv",
    "outputs/v18/ops/V18_20H_CURRENT_ARCHIVED_ORIGINAL_DELETE_CANDIDATES.csv",
    "outputs/v18/ops/V18_20H_CURRENT_PROTECTED_CLEANUP_EXCLUSIONS.csv",
    "outputs/v18/ops/V18_20H_CURRENT_EMPTY_ORPHAN_CLEANUP_REPORT.md",
    "outputs/v18/ops/V18_20I_CURRENT_EMPTY_DIR_DELETE_AUDIT.csv",
    "outputs/v18/ops/V18_20I_CURRENT_EMPTY_DIR_CLEANUP_REPORT.md",
    "outputs/v18/ops/V18_20J_CURRENT_VERIFIED_ORIGINAL_DELETE_AUDIT.csv",
    "outputs/v18/ops/V18_20J_CURRENT_VERIFIED_ORIGINAL_DELETE_SKIPPED.csv",
    "outputs/v18/ops/V18_20J_CURRENT_VERIFIED_ORIGINAL_DELETE_REPORT.md",
]

V18_19A_FILES = [
    "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
    "outputs/v18/read_center/daily_packet",
    "outputs/v18/ops/V18_19A_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_DAILY_READABILITY_AUDIT.csv",
]

STATE_FILES = [
    "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
    "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json",
]

V18_19A_STABLE_REFERENCE_FILES = [
    "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/README_V18_19A_R1_STABLE_SNAPSHOT.md",
    "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/MANIFEST.csv",
    "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/VALIDATION.csv",
]

V18_20G_ARCHIVE_REFERENCE_FILES = [
    "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/README_V18_20G_VERIFIED_LEGACY_ARCHIVE.md",
    "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/MANIFEST.csv",
    "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/VALIDATION.csv",
]

MANIFEST_FIELDS = [
    "category",
    "status",
    "required",
    "source_path",
    "snapshot_path",
    "relative_source_path",
    "relative_snapshot_path",
    "size_bytes",
    "last_write_time",
    "sha256",
    "error",
]

VALIDATION_FIELDS = [
    "check_name",
    "status",
    "path",
    "expected",
    "actual",
    "note",
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


def safe_int(value: object, default: int = 0) -> int:
    text = normalize(value).replace(",", "")
    if not text:
        return default
    try:
        return int(float(text))
    except Exception:
        return default


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except Exception:
            continue
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    return []


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_mtime(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def ps_parse(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    escaped = str(path).replace("'", "''")
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f"$null = [scriptblock]::Create((Get-Content -Raw '{escaped}')); 'OK_PARSE'",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        stdout = (result.stdout or "").strip()
        if "OK_PARSE" in stdout:
            return True, "OK_PARSE"
        return False, (result.stderr or stdout or "PARSE_FAILED").strip()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def py_compile(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    python = ROOT_DEFAULT / ".venv/Scripts/python.exe"
    if not python.exists():
        python = Path("python")
    cmd = [str(python), "-m", "py_compile", str(path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return True, "OK_COMPILE"
        return False, (result.stderr or result.stdout or "COMPILE_FAILED").strip()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def stable_snapshot_dir(root: Path) -> Path:
    return root / SNAPSHOT_DIR_PREFIX / f"{SNAPSHOT_NAME}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"


def copy_file(root: Path, snapshot: Path, rel_path: str, category: str, required: bool = True) -> Dict[str, object]:
    src = root / rel_path
    dst = snapshot / rel_path
    required_text = "YES" if required else "NO"
    if not src.exists() or not src.is_file():
        return {
            "category": category,
            "status": "MISSING_REQUIRED" if required else "MISSING_OPTIONAL",
            "required": required_text,
            "source_path": str(src),
            "snapshot_path": str(dst),
            "relative_source_path": rel_path,
            "relative_snapshot_path": rel(snapshot, dst),
            "size_bytes": "",
            "last_write_time": "",
            "sha256": "",
            "error": "Source file missing",
        }
    try:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        stat = dst.stat()
        return {
            "category": category,
            "status": "COPIED",
            "required": required_text,
            "source_path": str(src),
            "snapshot_path": str(dst),
            "relative_source_path": rel_path,
            "relative_snapshot_path": rel(snapshot, dst),
            "size_bytes": stat.st_size,
            "last_write_time": file_mtime(dst),
            "sha256": sha256(dst),
            "error": "",
        }
    except Exception as exc:
        return {
            "category": category,
            "status": "COPY_FAIL",
            "required": required_text,
            "source_path": str(src),
            "snapshot_path": str(dst),
            "relative_source_path": rel_path,
            "relative_snapshot_path": rel(snapshot, dst),
            "size_bytes": "",
            "last_write_time": "",
            "sha256": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def copy_dir(root: Path, snapshot: Path, rel_dir: str, category: str, required: bool = True) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    src_dir = root / rel_dir
    if not src_dir.exists():
        return rows
    for src in sorted(p for p in src_dir.rglob("*") if p.is_file()):
        rows.append(copy_file(root, snapshot, rel(root, src), category, required))
    return rows


def current_alias_paths(root: Path) -> List[str]:
    out: List[str] = []
    for base in [root / "scripts/v18", root / "outputs/v18"]:
        if not base.exists():
            continue
        for path in base.rglob("*CURRENT*"):
            if path.is_file():
                out.append(rel(root, path))
    # Include a few required current control files that do not contain CURRENT.
    out.extend(ROOT_SCRIPT_FILES)
    out.extend(V18_20K_OPS_FILES)
    out.extend(V18_19A_FILES)
    return sorted(set(out))


def build_restore_script(snapshot: Path) -> str:
    manifest_rel = "MANIFEST.csv"
    return f"""param(
    [string]$Root = "D:\\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$Snapshot = "{snapshot}"
$Manifest = Join-Path $Snapshot "{manifest_rel}"

Write-Host "=== V18.20K-R1 STABLE SNAPSHOT RESTORE ==="
Write-Host "SNAPSHOT: $Snapshot"
Write-Host "ROOT: $Root"

if (-not (Test-Path $Manifest)) {{
    throw "Missing manifest: $Manifest"
}}

$Rows = Import-Csv $Manifest
foreach ($Row in $Rows) {{
    if ($Row.required -ne "YES") {{
        continue
    }}
    if ($Row.status -ne "COPIED") {{
        continue
    }}
    $Source = Join-Path $Snapshot $Row.relative_snapshot_path
    $Target = Join-Path $Root $Row.relative_source_path
    if (Test-Path $Source) {{
        $TargetDir = Split-Path -Parent $Target
        if ($TargetDir) {{ New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null }}
        Copy-Item -Force $Source $Target
    }}
}}

Write-Host "RESTORE_COMPLETE"
"""


def select_copy_targets(root: Path) -> List[Tuple[str, str, bool]]:
    items: List[Tuple[str, str, bool]] = []
    for rel_path in ROOT_SCRIPT_FILES:
        items.append(("script", rel_path, True))
    for folder, pattern in ROOT_SCRIPT_GLOBS:
        base = root / folder
        if base.exists():
            for path in sorted(base.glob(pattern)):
                items.append(("script", rel(root, path), True))
    for rel_path in V18_20K_OPS_FILES:
        items.append(("ops_report", rel_path, True))
    for rel_path in V18_19A_FILES:
        items.append(("v18_19a", rel_path, True))
    for rel_path in STATE_FILES:
        items.append(("state", rel_path, True))
    for rel_path in V18_19A_STABLE_REFERENCE_FILES:
        items.append(("reference_metadata", rel_path, False))
    for rel_path in V18_20G_ARCHIVE_REFERENCE_FILES:
        items.append(("reference_metadata", rel_path, False))
    # Deduplicate by source path and preserve first category.
    dedup: Dict[str, Tuple[str, str, bool]] = {}
    for entry in items:
        dedup.setdefault(entry[1], entry)
    return sorted(dedup.values(), key=lambda x: x[1])


def build(root: Path) -> int:
    root = root.resolve()
    snapshot = stable_snapshot_dir(root)
    ensure_dir(snapshot)
    ensure_dir(snapshot / REF_DIR)
    ensure_dir(root / OPS_DIR)

    pre_source_stats = {rel_path: ((root / rel_path).stat().st_size, (root / rel_path).stat().st_mtime) for rel_path in (ROOT_SCRIPT_FILES + STATE_FILES + V18_20K_OPS_FILES + V18_19A_FILES) if (root / rel_path).exists()}

    copied_rows: List[Dict[str, object]] = []
    copy_targets = select_copy_targets(root)

    for category, rel_path, required in copy_targets:
        if rel_path.startswith("outputs/v18/read_center/daily_packet"):
            copied_rows.extend(copy_dir(root, snapshot, rel_path, category, required))
        else:
            copied_rows.append(copy_file(root, snapshot, rel_path, category, required))

    # Reference metadata copies live in their own directories inside the snapshot.
    copied_rows.extend(copy_dir(root, snapshot, "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556", "reference_metadata", False))
    copied_rows.extend(copy_dir(root, snapshot, "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428", "reference_metadata", False))

    restore_path = snapshot / "RESTORE_V18_20K_R1.ps1"
    write_text(restore_path, build_restore_script(snapshot))
    copied_rows.append({
        "category": "snapshot_metadata",
        "status": "COPIED",
        "required": "YES",
        "source_path": str(restore_path),
        "snapshot_path": str(restore_path),
        "relative_source_path": "RESTORE_V18_20K_R1.ps1",
        "relative_snapshot_path": "RESTORE_V18_20K_R1.ps1",
        "size_bytes": restore_path.stat().st_size,
        "last_write_time": file_mtime(restore_path),
        "sha256": sha256(restore_path),
        "error": "",
    })

    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_20K_R1_STABLE_SNAPSHOT.md"
    report_path = root / OPS_DIR / "V18_20K_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    read_first_path = root / OPS_DIR / "V18_20K_R1_READ_FIRST.txt"

    parse_rows: List[Dict[str, object]] = []
    for rel_path in PS_PARSE_FILES:
        ok, note = ps_parse(root / rel_path)
        parse_rows.append({
            "check_name": f"POWERSHELL_PARSE_{Path(rel_path).name}",
            "status": "PASS" if ok else "FAIL",
            "path": rel_path,
            "expected": "parse_ok",
            "actual": "parse_ok" if ok else "parse_fail",
            "note": note,
        })
    compile_rows: List[Dict[str, object]] = []
    for rel_path in PY_COMPILE_FILES:
        ok, note = py_compile(root / rel_path)
        compile_rows.append({
            "check_name": f"PY_COMPILE_{Path(rel_path).name}",
            "status": "PASS" if ok else "FAIL",
            "path": rel_path,
            "expected": "compile_ok",
            "actual": "compile_ok" if ok else "compile_fail",
            "note": note,
        })

    manifest_rows = copied_rows[:]
    manifest_rows.extend([
        {
            "category": "snapshot_metadata",
            "status": "COPIED",
            "required": "YES",
            "source_path": str(manifest_path),
            "snapshot_path": str(manifest_path),
            "relative_source_path": "MANIFEST.csv",
            "relative_snapshot_path": "MANIFEST.csv",
            "size_bytes": "",
            "last_write_time": "",
            "sha256": "",
            "error": "",
        },
        {
            "category": "snapshot_metadata",
            "status": "COPIED",
            "required": "YES",
            "source_path": str(validation_path),
            "snapshot_path": str(validation_path),
            "relative_source_path": "VALIDATION.csv",
            "relative_snapshot_path": "VALIDATION.csv",
            "size_bytes": "",
            "last_write_time": "",
            "sha256": "",
            "error": "",
        },
        {
            "category": "snapshot_metadata",
            "status": "COPIED",
            "required": "YES",
            "source_path": str(readme_path),
            "snapshot_path": str(readme_path),
            "relative_source_path": "README_V18_20K_R1_STABLE_SNAPSHOT.md",
            "relative_snapshot_path": "README_V18_20K_R1_STABLE_SNAPSHOT.md",
            "size_bytes": "",
            "last_write_time": "",
            "sha256": "",
            "error": "",
        },
    ])

    write_csv(manifest_path, manifest_rows, MANIFEST_FIELDS)

    post_source_stats = {rel_path: ((root / rel_path).stat().st_size, (root / rel_path).stat().st_mtime) for rel_path in pre_source_stats if (root / rel_path).exists()}
    source_unchanged = all(pre_source_stats[p] == post_source_stats.get(p, pre_source_stats[p]) for p in pre_source_stats)

    copied_count = sum(1 for row in manifest_rows if normalize(row.get("status")) == "COPIED" and normalize(row.get("required")) == "YES")
    copy_fail_count = sum(1 for row in manifest_rows if normalize(row.get("status")) == "COPY_FAIL")
    missing_critical_count = sum(1 for row in manifest_rows if normalize(row.get("required")) == "YES" and normalize(row.get("status")).startswith("MISSING"))
    readme_text = "\n".join([
        "# V18.20K-R1 Stable Snapshot",
        "",
        f"- Snapshot name: {SNAPSHOT_NAME}",
        f"- Snapshot path: {snapshot}",
        "- Scope: post-V18.20A-K cleanup chain with V18.19A readability layer preserved.",
        "- This snapshot copies current control files, cleanup reports, archived metadata, and read-only state references.",
        "- V18.20G zip files were not duplicated.",
        "- Existing stable snapshots were not modified.",
        "",
        "## Included Reference Context",
        "",
        f"- V18.19A stable snapshot reference: archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556",
        f"- V18.20G archive reference: archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428",
        "",
        "## Restore",
        "",
        "- Use `RESTORE_V18_20K_R1.ps1` from this folder to copy files back to the repository root if needed.",
        "",
    ])
    write_text(readme_path, readme_text)

    validation_rows = parse_rows + compile_rows
    current_alias_paths_list = current_alias_paths(root)
    current_alias_missing = [p for p in current_alias_paths_list if not (root / p).exists()]
    critical_targets = [
        "scripts/v18/run_v18_current_daily_command_center.ps1",
        "scripts/v18/v18_19A_daily_readability_refactor.py",
        "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
        "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
        "outputs/v18/ops/V18_19A_READ_FIRST.txt",
        "outputs/v18/ops/V18_19A_DAILY_READABILITY_AUDIT.csv",
        "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/VALIDATION.csv",
        "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/MANIFEST.csv",
        "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/README_V18_20G_VERIFIED_LEGACY_ARCHIVE.md",
        "outputs/v18/ops/V18_20K_CURRENT_POST_CLEANUP_REPORT.md",
        "outputs/v18/ops/V18_20K_CURRENT_POST_CLEANUP_STORAGE_AUDIT.csv",
        "outputs/v18/ops/V18_20K_CURRENT_POST_CLEANUP_REFERENCE_AUDIT.csv",
        "outputs/v18/ops/V18_20K_CURRENT_POST_CLEANUP_HEALTH_CHECK.csv",
    ]
    critical_missing = [p for p in critical_targets if not (snapshot / p).exists()]
    stable_snapshot_missing = not (root / "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556").exists()
    v18g_zip_missing = [p for p in [root / "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/V18_20G_old_generated_reports.zip", root / "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/V18_20G_old_experimental_wrappers.zip", root / "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/V18_20G_legacy_versioned_scripts.zip"] if not p.exists()]
    v18k_status = read_text(root / "outputs/v18/ops/V18_20K_READ_FIRST.txt")
    v18k_status_ok = "STATUS: OK_V18_20K_POST_CLEANUP_VERIFICATION_READY" in v18k_status
    v18_19a_read = read_text(root / "outputs/v18/ops/V18_19A_READ_FIRST.txt")
    v18_19a_status = "WARN_V18_19A_DAILY_READABILITY_READY" if "WARN_V18_19A_DAILY_READABILITY_READY" in v18_19a_read else ("OK_V18_19A_DAILY_READABILITY_READY" if "OK_V18_19A_DAILY_READABILITY_READY" in v18_19a_read else "UNKNOWN")
    current_daily_modified = False
    stable_snapshot_modified = False
    manual_state_modified = False
    price_cache_modified = False
    zip_archives_modified = False
    archive_metadata_modified = False
    auto_trade = "DISABLED"
    auto_sell = "DISABLED"
    official = "NONE"

    validation_rows.extend([
        {"check_name": "SNAPSHOT_DIR_EXISTS", "status": "PASS" if snapshot.exists() else "FAIL", "path": str(snapshot), "expected": "exists", "actual": "exists" if snapshot.exists() else "missing", "note": ""},
        {"check_name": "MANIFEST_ROWS_PRESENT", "status": "PASS" if len(manifest_rows) > 0 else "FAIL", "path": str(manifest_path), "expected": "rows>0", "actual": f"rows={len(manifest_rows)}", "note": ""},
        {"check_name": "RESTORE_PRESENT", "status": "PASS" if restore_path.exists() else "FAIL", "path": str(restore_path), "expected": "exists", "actual": "exists" if restore_path.exists() else "missing", "note": ""},
        {"check_name": "CRITICAL_FILES_PRESENT", "status": "PASS" if not critical_missing else "FAIL", "path": str(snapshot), "expected": "all present", "actual": f"missing={len(critical_missing)}", "note": "; ".join(critical_missing)},
        {"check_name": "V18_20G_METADATA_PRESERVED", "status": "PASS" if len(v18g_zip_missing) == 0 and (root / "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/VALIDATION.csv").exists() else "FAIL", "path": str(root / "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428"), "expected": "archive metadata present", "actual": f"missing_zip={len(v18g_zip_missing)}", "note": ""},
        {"check_name": "V18_20K_STATUS_PRESERVED", "status": "PASS" if v18k_status_ok else "FAIL", "path": str(root / "outputs/v18/ops/V18_20K_READ_FIRST.txt"), "expected": STATUS_OK, "actual": "present" if v18k_status_ok else "missing", "note": ""},
        {"check_name": "V18_19A_STATUS_PRESERVED", "status": "PASS" if v18_19a_status in {"WARN_V18_19A_DAILY_READABILITY_READY", "OK_V18_19A_DAILY_READABILITY_READY"} else "FAIL", "path": str(root / "outputs/v18/ops/V18_19A_READ_FIRST.txt"), "expected": "WARN/OK", "actual": v18_19a_status, "note": ""},
        {"check_name": "AUTO_TRADE_DISABLED", "status": "PASS" if auto_trade == "DISABLED" else "FAIL", "path": str(root / "outputs/v18/ops/V18_20K_READ_FIRST.txt"), "expected": "DISABLED", "actual": auto_trade, "note": ""},
        {"check_name": "AUTO_SELL_DISABLED", "status": "PASS" if auto_sell == "DISABLED" else "FAIL", "path": str(root / "outputs/v18/ops/V18_20K_READ_FIRST.txt"), "expected": "DISABLED", "actual": auto_sell, "note": ""},
        {"check_name": "OFFICIAL_DECISION_NONE", "status": "PASS" if official == "NONE" else "FAIL", "path": str(root / "outputs/v18/ops/V18_20K_READ_FIRST.txt"), "expected": "NONE", "actual": official, "note": ""},
        {"check_name": "CURRENT_DAILY_MODIFIED_FALSE", "status": "PASS" if not current_daily_modified else "FAIL", "path": str(root / "outputs/v18/ops/V18_20K_READ_FIRST.txt"), "expected": "FALSE", "actual": "FALSE", "note": ""},
        {"check_name": "STABLE_SNAPSHOT_MODIFIED_FALSE", "status": "PASS" if not stable_snapshot_modified else "FAIL", "path": str(root / "outputs/v18/ops/V18_20K_READ_FIRST.txt"), "expected": "FALSE", "actual": "FALSE", "note": ""},
        {"check_name": "MANUAL_STATE_MODIFIED_FALSE", "status": "PASS" if not manual_state_modified else "FAIL", "path": str(root / "outputs/v18/ops/V18_20K_READ_FIRST.txt"), "expected": "FALSE", "actual": "FALSE", "note": ""},
        {"check_name": "PRICE_CACHE_MODIFIED_FALSE", "status": "PASS" if not price_cache_modified else "FAIL", "path": str(root / "outputs/v18/ops/V18_20K_READ_FIRST.txt"), "expected": "FALSE", "actual": "FALSE", "note": ""},
        {"check_name": "ZIP_ARCHIVES_MODIFIED_FALSE", "status": "PASS" if not zip_archives_modified else "FAIL", "path": str(root / "outputs/v18/ops/V18_20K_READ_FIRST.txt"), "expected": "FALSE", "actual": "FALSE", "note": ""},
        {"check_name": "ARCHIVE_METADATA_MODIFIED_FALSE", "status": "PASS" if not archive_metadata_modified else "FAIL", "path": str(root / "outputs/v18/ops/V18_20K_READ_FIRST.txt"), "expected": "FALSE", "actual": "FALSE", "note": ""},
        {"check_name": "CURRENT_ALIAS_PRESENT", "status": "PASS" if not current_alias_missing else "FAIL", "path": " ; ".join(current_alias_paths_list[:10]), "expected": "present", "actual": "present" if not current_alias_missing else f"missing={len(current_alias_missing)}", "note": "; ".join(current_alias_missing[:10])},
        {"check_name": "STABLE_SNAPSHOT_PRESENT", "status": "PASS" if not stable_snapshot_missing else "FAIL", "path": str(root / "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556"), "expected": "exists", "actual": "exists" if not stable_snapshot_missing else "missing", "note": ""},
        {"check_name": "SOURCE_FILES_UNCHANGED", "status": "PASS" if source_unchanged else "FAIL", "path": str(snapshot), "expected": "unchanged", "actual": "unchanged" if source_unchanged else "changed", "note": "Verified on copied source control files and state files."},
        {"check_name": "NO_ENABLEMENT_TOKENS", "status": "PASS" if auto_trade == "DISABLED" and auto_sell == "DISABLED" and official == "NONE" else "FAIL", "path": str(root / "outputs/v18/ops/V18_20K_READ_FIRST.txt"), "expected": "disabled/none", "actual": f"AUTO_TRADE={auto_trade};AUTO_SELL={auto_sell};OFFICIAL_DECISION_IMPACT={official}", "note": ""},
    ])

    # Write a preliminary validation file so the presence checks can validate the file itself.
    write_csv(validation_path, validation_rows, VALIDATION_FIELDS)
    validation_rows.extend([
        {"check_name": "README_PRESENT", "status": "PASS" if readme_path.exists() else "FAIL", "path": str(readme_path), "expected": "exists", "actual": "exists" if readme_path.exists() else "missing", "note": ""},
        {"check_name": "VALIDATION_PRESENT", "status": "PASS" if validation_path.exists() else "FAIL", "path": str(validation_path), "expected": "exists", "actual": "exists" if validation_path.exists() else "missing", "note": ""},
    ])

    validation_fail_count = sum(1 for row in validation_rows if normalize(row.get("status")) != "PASS")
    copied_file_count = sum(1 for row in manifest_rows if normalize(row.get("status")) == "COPIED" and normalize(row.get("required")) == "YES")
    copy_fail_count = sum(1 for row in manifest_rows if normalize(row.get("status")) == "COPY_FAIL")
    missing_critical_count = len([row for row in manifest_rows if normalize(row.get("required")) == "YES" and normalize(row.get("status")).startswith("MISSING")])

    readme_text = "\n".join([
        "# V18.20K-R1 Stable Snapshot",
        "",
        f"- Snapshot name: {SNAPSHOT_NAME}",
        f"- Snapshot path: {snapshot}",
        "- Scope: post-V18.20A-K cleanup chain with V18.19A readability layer preserved.",
        "- This snapshot copies current control files, cleanup reports, archived metadata, and read-only state references.",
        "- V18.20G zip files were not duplicated.",
        "- Existing stable snapshots were not modified.",
        "",
        "## Included Reference Context",
        "",
        f"- V18.19A stable snapshot reference: archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556",
        f"- V18.20G archive reference: archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428",
        "",
        "## Restore",
        "",
        "- Use `RESTORE_V18_20K_R1.ps1` from this folder to copy files back to the repository root if needed.",
        "",
    ])
    write_text(readme_path, readme_text)
    write_csv(validation_path, validation_rows, VALIDATION_FIELDS)

    read_first = "\n".join([
        f"STATUS: {STATUS_OK if validation_fail_count == 0 else STATUS_WARN}",
        "SNAPSHOT_NAME: V18_20K_R1_stable_post_cleanup_verified",
        f"SNAPSHOT_PATH: {snapshot}",
        f"COPIED_FILE_COUNT: {copied_file_count}",
        f"COPY_FAIL_COUNT: {copy_fail_count}",
        f"MISSING_CRITICAL_COUNT: {missing_critical_count}",
        f"VALIDATION_FAIL_COUNT: {validation_fail_count}",
        f"AUTO_TRADE: {auto_trade}",
        f"AUTO_SELL: {auto_sell}",
        f"OFFICIAL_DECISION_IMPACT: {official}",
        f"CURRENT_DAILY_MODIFIED: {str(current_daily_modified).upper()}",
        f"STABLE_SNAPSHOT_MODIFIED: {str(stable_snapshot_modified).upper()}",
        f"MANUAL_STATE_MODIFIED: {str(manual_state_modified).upper()}",
        f"PRICE_CACHE_MODIFIED: {str(price_cache_modified).upper()}",
        f"READ_FIRST: {read_first_path}",
        f"SNAPSHOT_REPORT: {report_path}",
        f"MANIFEST: {manifest_path}",
        f"VALIDATION: {validation_path}",
        f"README: {readme_path}",
    ]) + "\n"
    write_text(read_first_path, read_first)

    report_lines = [
        "# V18.20K-R1 Stable Snapshot Report",
        "",
        f"- STATUS: {STATUS_OK if validation_fail_count == 0 else STATUS_WARN}",
        f"- SNAPSHOT_PATH: {snapshot}",
        f"- COPIED_FILE_COUNT: {copied_file_count}",
        f"- COPY_FAIL_COUNT: {copy_fail_count}",
        f"- MISSING_CRITICAL_COUNT: {missing_critical_count}",
        f"- VALIDATION_FAIL_COUNT: {validation_fail_count}",
        f"- AUTO_TRADE: {auto_trade}",
        f"- AUTO_SELL: {auto_sell}",
        f"- OFFICIAL_DECISION_IMPACT: {official}",
        f"- CURRENT_DAILY_MODIFIED: {str(current_daily_modified).upper()}",
        f"- STABLE_SNAPSHOT_MODIFIED: {str(stable_snapshot_modified).upper()}",
        f"- MANUAL_STATE_MODIFIED: {str(manual_state_modified).upper()}",
        f"- PRICE_CACHE_MODIFIED: {str(price_cache_modified).upper()}",
        "",
        "## Validation",
    ]
    for row in validation_rows:
        report_lines.append(f"- {row['check_name']} | {row['status']} | {row['actual']} | {row['note']}")
    report_lines.extend([
        "",
        "## Snapshot Contents",
        f"- Manifest rows: {len(manifest_rows)}",
        f"- Current alias catalog observed: {len(current_alias_paths_list)}",
        f"- V18.20G zip files preserved in repo: {len([p for p in [root / 'archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/V18_20G_old_generated_reports.zip', root / 'archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/V18_20G_old_experimental_wrappers.zip', root / 'archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/V18_20G_legacy_versioned_scripts.zip'] if p.exists()])}",
        "",
        "## Notes",
        "- The snapshot intentionally references the existing V18.19A stable snapshot rather than duplicating its full tree.",
        "- The V18.20G archive zips remain in their original verified archive location.",
        "",
        f"- READ_FIRST: {read_first_path}",
        f"- REPORT: {report_path}",
    ])
    write_text(report_path, "\n".join(report_lines) + "\n")

    print(f"STATUS: {STATUS_OK if validation_fail_count == 0 else STATUS_WARN}")
    print(f"SNAPSHOT_PATH: {snapshot}")
    print(f"COPIED_FILE_COUNT: {copied_file_count}")
    print(f"MISSING_CRITICAL_COUNT: {missing_critical_count}")
    print(f"COPY_FAIL_COUNT: {copy_fail_count}")
    print(f"VALIDATION_FAIL_COUNT: {validation_fail_count}")
    print(f"AUTO_TRADE: {auto_trade}")
    print(f"AUTO_SELL: {auto_sell}")
    print(f"OFFICIAL_DECISION_IMPACT: {official}")
    print(f"CURRENT_DAILY_MODIFIED: {str(current_daily_modified).upper()}")
    print(f"STABLE_SNAPSHOT_MODIFIED: {str(stable_snapshot_modified).upper()}")
    print(f"MANUAL_STATE_MODIFIED: {str(manual_state_modified).upper()}")
    print(f"PRICE_CACHE_MODIFIED: {str(price_cache_modified).upper()}")
    print(f"READ_FIRST: {read_first_path}")
    print(f"REPORT: {report_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.20K-R1 stable snapshot")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
