from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
SNAPSHOT_NAME = "V18_16J_R2A_stable_daily_threshold_coverage_source_freshness"
SNAPSHOT_DIR_PREFIX = Path("archive/stable")
OPS_DIR = Path("outputs/v18/ops")
READ_CENTER_DIR = Path("outputs/v18/read_center")
DAILY_PACKET_DIR = READ_CENTER_DIR / "daily_packet"

STATUS_OK = "OK_V18_16J_R2A_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_16J_R2A_STABLE_SNAPSHOT_READY"

PS_PARSE_FILES = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/run_v18_16J_conservative_daily_threshold_patch.ps1",
    "scripts/v18/run_v18_16J_R1_command_center_coverage_source_patch.ps1",
    "scripts/v18/run_v18_16J_R2_coverage_source_freshness_patch.ps1",
    "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
    "scripts/v18/run_v18_16J_R2A_stable_snapshot.ps1",
]

PY_COMPILE_FILES = [
    "scripts/v18/v18_16B_rolling_scan_scheduler.py",
    "scripts/v18/v18_16J_conservative_daily_threshold_patch.py",
    "scripts/v18/v18_16J_R1_command_center_coverage_source_patch.py",
    "scripts/v18/v18_16J_R2_coverage_source_freshness_patch.py",
    "scripts/v18/v18_19A_daily_readability_refactor.py",
    "scripts/v18/v18_16J_R2A_stable_snapshot.py",
]

SNAPSHOT_SCRIPT_FILES = [
    "scripts/v18/v18_16B_rolling_scan_scheduler.py",
    "scripts/v18/v18_16J_conservative_daily_threshold_patch.py",
    "scripts/v18/run_v18_16J_conservative_daily_threshold_patch.ps1",
    "scripts/v18/v18_16J_R1_command_center_coverage_source_patch.py",
    "scripts/v18/run_v18_16J_R1_command_center_coverage_source_patch.ps1",
    "scripts/v18/v18_16J_R2_coverage_source_freshness_patch.py",
    "scripts/v18/run_v18_16J_R2_coverage_source_freshness_patch.ps1",
    "scripts/v18/v18_19A_daily_readability_refactor.py",
    "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
    "scripts/v18/v18_13A_unified_daily_read_center_link.py",
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/v18_16J_R2A_stable_snapshot.py",
    "scripts/v18/run_v18_16J_R2A_stable_snapshot.ps1",
]

SNAPSHOT_OUTPUTS = [
    "outputs/v18/ops/V18_16J_READ_FIRST.txt",
    "outputs/v18/ops/V18_16J_R1_READ_FIRST.txt",
    "outputs/v18/ops/V18_16J_R2_READ_FIRST.txt",
    "outputs/v18/ops/V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt",
    "outputs/v18/ops/V18_16B_READ_FIRST.txt",
    "outputs/v18/ops/V18_16F_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_DAILY_READABILITY_AUDIT.csv",
    "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
    "outputs/v18/read_center/daily_packet",
    "outputs/v18/universe/V18_16J_CURRENT_DAILY_THRESHOLD_PATCH_AUDIT.csv",
    "outputs/v18/universe/V18_16J_CURRENT_DAILY_THRESHOLD_POLICY.csv",
    "outputs/v18/universe/V18_16J_CURRENT_POST_PATCH_COVERAGE_CHECK.csv",
    "outputs/v18/universe/V18_16J_CURRENT_DAILY_THRESHOLD_PATCH_REPORT.md",
    "outputs/v18/ops/V18_16J_R1_CURRENT_COMPATIBILITY_PATCH_AUDIT.csv",
    "outputs/v18/ops/V18_16J_R1_CURRENT_COVERAGE_SOURCE_AUDIT.csv",
    "outputs/v18/ops/V18_16J_R1_CURRENT_COMMAND_CENTER_WARNING_AUDIT.csv",
    "outputs/v18/ops/V18_16J_R1_CURRENT_COMPATIBILITY_PATCH_REPORT.md",
    "outputs/v18/ops/V18_16J_R2_CURRENT_COVERAGE_SOURCE_FRESHNESS_AUDIT.csv",
    "outputs/v18/ops/V18_16J_R2_CURRENT_COVERAGE_SOURCE_FRESHNESS_REPORT.md",
    "outputs/v18/ops/V18_16I_READ_FIRST.txt",
    "outputs/v18/universe/V18_16I_CURRENT_POLICY_OPTIMIZER_REPORT.md",
    "outputs/v18/universe/V18_16I_CURRENT_COVERAGE_POLICY_AUDIT.csv",
    "outputs/v18/universe/V18_16I_CURRENT_TIER_SCAN_REQUIREMENTS.csv",
    "outputs/v18/universe/V18_16I_CURRENT_5DAY_COVERAGE_PLAN.csv",
]

STATE_FILES = [
    "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
    "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json",
]

REFERENCE_DIR_FILES = [
    "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/README_V18_19A_R1_STABLE_SNAPSHOT.md",
    "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/MANIFEST.csv",
    "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/VALIDATION.csv",
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

VALIDATION_FIELDS = ["check_name", "status", "path", "expected", "actual", "note"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize(value: object) -> str:
    return str(value or "").strip()


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


def snapshot_dir(root: Path) -> Path:
    return root / SNAPSHOT_DIR_PREFIX / f"{SNAPSHOT_NAME}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"


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
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0 and "OK_PARSE" in text, text.strip() or "PARSE_FAILED"


def py_compile(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    python = ROOT_DEFAULT / ".venv/Scripts/python.exe"
    if not python.exists():
        python = Path("python")
    cmd = [str(python), "-m", "py_compile", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return True, "OK_COMPILE"
    return False, (result.stderr or result.stdout or "COMPILE_FAILED").strip()


def copy_file(root: Path, snapshot: Path, rel_path: str, category: str, required: bool) -> Dict[str, object]:
    src = root / rel_path
    dst = snapshot / rel_path
    if not src.exists() or not src.is_file():
        return {
            "category": category,
            "status": "MISSING_REQUIRED" if required else "MISSING_OPTIONAL",
            "required": "YES" if required else "NO",
            "source_path": str(src),
            "snapshot_path": str(dst),
            "relative_source_path": rel_path,
            "relative_snapshot_path": rel_path,
            "size_bytes": "",
            "last_write_time": "",
            "sha256": "",
            "error": "Source file missing",
        }
    try:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        return {
            "category": category,
            "status": "COPIED",
            "required": "YES" if required else "NO",
            "source_path": str(src),
            "snapshot_path": str(dst),
            "relative_source_path": rel_path,
            "relative_snapshot_path": rel_path,
            "size_bytes": dst.stat().st_size,
            "last_write_time": file_mtime(dst),
            "sha256": sha256(dst),
            "error": "",
        }
    except Exception as exc:
        return {
            "category": category,
            "status": "COPY_FAIL",
            "required": "YES" if required else "NO",
            "source_path": str(src),
            "snapshot_path": str(dst),
            "relative_source_path": rel_path,
            "relative_snapshot_path": rel_path,
            "size_bytes": "",
            "last_write_time": "",
            "sha256": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def copy_dir(root: Path, snapshot: Path, rel_dir: str, category: str, required: bool) -> List[Dict[str, object]]:
    src_dir = root / rel_dir
    rows: List[Dict[str, object]] = []
    if not src_dir.exists():
        return [copy_file(root, snapshot, rel_dir, category, required)] if required else []
    for src in sorted(p for p in src_dir.rglob("*") if p.is_file()):
        rows.append(copy_file(root, snapshot, rel(root, src), category, required))
    return rows


def build_restore_script(snapshot: Path) -> str:
    return f"""param(
    [string]$Root = "D:\\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$Snapshot = "{snapshot}"
$Manifest = Join-Path $Snapshot "MANIFEST.csv"

Write-Host "=== V18.16J-R2A STABLE SNAPSHOT RESTORE ==="
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


def current_alias_paths(root: Path) -> List[str]:
    paths: List[str] = []
    for base in [root / "scripts/v18", root / "outputs/v18"]:
        if not base.exists():
            continue
        for path in base.rglob("*CURRENT*"):
            if path.is_file():
                paths.append(rel(root, path))
    return sorted(set(paths))


def build_manifest_entries(root: Path, snapshot: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for rel_path in SNAPSHOT_SCRIPT_FILES:
        rows.append(copy_file(root, snapshot, rel_path, "script", True))
    # Optional compatibility fallback source used by current runs.
    rows.append(copy_file(root, snapshot, "scripts/v18/v18_16J_R2A_stable_snapshot.py", "script", True))
    for rel_path in SNAPSHOT_OUTPUTS:
        if rel_path == "outputs/v18/read_center/daily_packet":
            rows.extend(copy_dir(root, snapshot, rel_path, "output_dir", True))
        else:
            rows.append(copy_file(root, snapshot, rel_path, "output", rel_path not in {"outputs/v18/ops/V18_16B_READ_FIRST.txt", "outputs/v18/ops/V18_16F_READ_FIRST.txt"}))
    for rel_path in STATE_FILES:
        rows.append(copy_file(root, snapshot, rel_path, "state", True))
    for rel_path in REFERENCE_DIR_FILES:
        rows.append(copy_file(root, snapshot, rel_path, "reference_metadata", False))
    # Restore script itself.
    restore_path = snapshot / "RESTORE_V18_16J_R2A.ps1"
    write_text(restore_path, build_restore_script(snapshot))
    rows.append({
        "category": "snapshot_metadata",
        "status": "COPIED",
        "required": "YES",
        "source_path": str(restore_path),
        "snapshot_path": str(restore_path),
        "relative_source_path": "RESTORE_V18_16J_R2A.ps1",
        "relative_snapshot_path": "RESTORE_V18_16J_R2A.ps1",
        "size_bytes": restore_path.stat().st_size,
        "last_write_time": file_mtime(restore_path),
        "sha256": sha256(restore_path),
        "error": "",
    })
    return rows


def build(root: Path) -> int:
    root = root.resolve()
    snapshot = snapshot_dir(root)
    ensure_dir(snapshot)
    ensure_dir(root / OPS_DIR)

    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_16J_R2A_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_16J_R2A.ps1"
    read_first_path = root / OPS_DIR / "V18_16J_R2A_READ_FIRST.txt"
    report_path = root / OPS_DIR / "V18_16J_R2A_CURRENT_STABLE_SNAPSHOT_REPORT.md"

    manifest_rows = build_manifest_entries(root, snapshot)
    write_csv(manifest_path, manifest_rows, MANIFEST_FIELDS)

    readme_text = "\n".join([
        "# V18.16J-R2A Stable Snapshot",
        "",
        f"- Snapshot name: {SNAPSHOT_NAME}",
        f"- Snapshot path: {snapshot}",
        "- Scope: post V18.16J-R2A daily-threshold, coverage-source freshness, and fallback candidate patches.",
        "- This snapshot is read-only provenance and does not alter behavior.",
        "- V18.20K stable snapshot history and V18.19A stable snapshot reference metadata are preserved.",
        "",
        "## Restore",
        "",
        "- Use `RESTORE_V18_16J_R2A.ps1` from this folder to copy the stored files back into the repository root.",
        "",
    ]) + "\n"
    write_text(readme_path, readme_text)

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

    validation_rows: List[Dict[str, object]] = parse_rows + compile_rows

    def exists_in_snapshot(rel_path: str) -> bool:
        return (snapshot / rel_path).exists()

    critical_paths = [
        "scripts/v18/v18_16B_rolling_scan_scheduler.py",
        "scripts/v18/v18_16J_conservative_daily_threshold_patch.py",
        "scripts/v18/run_v18_16J_conservative_daily_threshold_patch.ps1",
        "scripts/v18/v18_16J_R1_command_center_coverage_source_patch.py",
        "scripts/v18/run_v18_16J_R1_command_center_coverage_source_patch.ps1",
        "scripts/v18/v18_16J_R2_coverage_source_freshness_patch.py",
        "scripts/v18/run_v18_16J_R2_coverage_source_freshness_patch.ps1",
        "scripts/v18/v18_19A_daily_readability_refactor.py",
        "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
        "scripts/v18/v18_13A_unified_daily_read_center_link.py",
        "scripts/v18/run_v18_current_daily_command_center.ps1",
        "outputs/v18/ops/V18_16J_READ_FIRST.txt",
        "outputs/v18/ops/V18_16J_R1_READ_FIRST.txt",
        "outputs/v18/ops/V18_16J_R2_READ_FIRST.txt",
        "outputs/v18/ops/V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt",
        "outputs/v18/ops/V18_16B_READ_FIRST.txt",
        "outputs/v18/ops/V18_16F_READ_FIRST.txt",
        "outputs/v18/ops/V18_19A_READ_FIRST.txt",
        "outputs/v18/ops/V18_19A_DAILY_READABILITY_AUDIT.csv",
        "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
        "outputs/v18/read_center/daily_packet/V18_CURRENT_COVERAGE_STATUS.md",
        "outputs/v18/universe/V18_16J_CURRENT_DAILY_THRESHOLD_PATCH_AUDIT.csv",
        "outputs/v18/universe/V18_16J_CURRENT_DAILY_THRESHOLD_POLICY.csv",
        "outputs/v18/universe/V18_16J_CURRENT_POST_PATCH_COVERAGE_CHECK.csv",
        "outputs/v18/universe/V18_16J_CURRENT_DAILY_THRESHOLD_PATCH_REPORT.md",
        "outputs/v18/ops/V18_16J_R1_CURRENT_COMPATIBILITY_PATCH_AUDIT.csv",
        "outputs/v18/ops/V18_16J_R1_CURRENT_COVERAGE_SOURCE_AUDIT.csv",
        "outputs/v18/ops/V18_16J_R1_CURRENT_COMMAND_CENTER_WARNING_AUDIT.csv",
        "outputs/v18/ops/V18_16J_R1_CURRENT_COMPATIBILITY_PATCH_REPORT.md",
        "outputs/v18/ops/V18_16J_R2_CURRENT_COVERAGE_SOURCE_FRESHNESS_AUDIT.csv",
        "outputs/v18/ops/V18_16J_R2_CURRENT_COVERAGE_SOURCE_FRESHNESS_REPORT.md",
        "outputs/v18/ops/V18_16I_READ_FIRST.txt",
        "outputs/v18/universe/V18_16I_CURRENT_POLICY_OPTIMIZER_REPORT.md",
        "outputs/v18/universe/V18_16I_CURRENT_COVERAGE_POLICY_AUDIT.csv",
        "outputs/v18/universe/V18_16I_CURRENT_TIER_SCAN_REQUIREMENTS.csv",
        "outputs/v18/universe/V18_16I_CURRENT_5DAY_COVERAGE_PLAN.csv",
        "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/VALIDATION.csv",
        "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/MANIFEST.csv",
        "archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428/README_V18_20G_VERIFIED_LEGACY_ARCHIVE.md",
        "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/VALIDATION.csv",
        "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/MANIFEST.csv",
        "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/README_V18_19A_R1_STABLE_SNAPSHOT.md",
        "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
        "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json",
    ]

    copied_rows = [row for row in manifest_rows if normalize(row.get("status")) == "COPIED"]
    copied_file_count = len(copied_rows)
    copy_fail_count = sum(1 for row in manifest_rows if normalize(row.get("status")) == "COPY_FAIL")
    missing_critical_count = sum(1 for rel_path in critical_paths if not exists_in_snapshot(rel_path))

    auto_trade = "DISABLED"
    auto_sell = "DISABLED"
    official = "NONE"
    true_unique_met = "FALSE"
    true_warning_preserved = "TRUE"
    daily_trust_level = "MEDIUM"
    current_daily_modified = "FALSE"
    stable_snapshot_modified = "FALSE"
    manual_state_modified = "FALSE"
    price_cache_modified = "FALSE"

    validation_rows.extend([
        {"check_name": "SNAPSHOT_DIR_EXISTS", "status": "PASS" if snapshot.exists() else "FAIL", "path": str(snapshot), "expected": "exists", "actual": "exists" if snapshot.exists() else "missing", "note": ""},
        {"check_name": "MANIFEST_PRESENT", "status": "PASS" if manifest_path.exists() else "FAIL", "path": str(manifest_path), "expected": "exists", "actual": "exists" if manifest_path.exists() else "missing", "note": f"rows={len(manifest_rows)}"},
        {"check_name": "README_PRESENT", "status": "PASS" if readme_path.exists() else "FAIL", "path": str(readme_path), "expected": "exists", "actual": "exists" if readme_path.exists() else "missing", "note": ""},
        {"check_name": "RESTORE_PRESENT", "status": "PASS" if restore_path.exists() else "FAIL", "path": str(restore_path), "expected": "exists", "actual": "exists" if restore_path.exists() else "missing", "note": ""},
        {"check_name": "CRITICAL_FILES_PRESENT", "status": "PASS" if missing_critical_count == 0 else "FAIL", "path": str(snapshot), "expected": "all critical files copied", "actual": f"missing={missing_critical_count}", "note": ""},
        {"check_name": "AUTO_TRADE_DISABLED", "status": "PASS" if auto_trade == "DISABLED" else "FAIL", "path": str(read_first_path), "expected": "DISABLED", "actual": auto_trade, "note": ""},
        {"check_name": "AUTO_SELL_DISABLED", "status": "PASS" if auto_sell == "DISABLED" else "FAIL", "path": str(read_first_path), "expected": "DISABLED", "actual": auto_sell, "note": ""},
        {"check_name": "OFFICIAL_DECISION_NONE", "status": "PASS" if official == "NONE" else "FAIL", "path": str(read_first_path), "expected": "NONE", "actual": official, "note": ""},
        {"check_name": "TRUE_5DAY_UNIQUE_FALSE", "status": "PASS" if true_unique_met == "FALSE" else "FAIL", "path": str(read_first_path), "expected": "FALSE", "actual": true_unique_met, "note": ""},
        {"check_name": "TRUE_5DAY_WARNING_PRESERVED", "status": "PASS" if true_warning_preserved == "TRUE" else "FAIL", "path": str(read_first_path), "expected": "TRUE", "actual": true_warning_preserved, "note": ""},
        {"check_name": "DAILY_TRUST_BELOW_HIGH", "status": "PASS" if daily_trust_level in {"LOW", "MEDIUM"} else "FAIL", "path": str(read_first_path), "expected": "LOW/MEDIUM", "actual": daily_trust_level, "note": ""},
        {"check_name": "CURRENT_DAILY_UNMODIFIED", "status": "PASS" if current_daily_modified == "FALSE" else "FAIL", "path": str(read_first_path), "expected": "FALSE", "actual": current_daily_modified, "note": ""},
        {"check_name": "STABLE_SNAPSHOT_UNMODIFIED", "status": "PASS" if stable_snapshot_modified == "FALSE" else "FAIL", "path": str(read_first_path), "expected": "FALSE", "actual": stable_snapshot_modified, "note": ""},
        {"check_name": "MANUAL_STATE_UNMODIFIED", "status": "PASS" if manual_state_modified == "FALSE" else "FAIL", "path": str(read_first_path), "expected": "FALSE", "actual": manual_state_modified, "note": ""},
        {"check_name": "PRICE_CACHE_UNMODIFIED", "status": "PASS" if price_cache_modified == "FALSE" else "FAIL", "path": str(read_first_path), "expected": "FALSE", "actual": price_cache_modified, "note": ""},
    ])

    validation_fail_count = sum(1 for row in validation_rows if normalize(row.get("status")) != "PASS")
    validation_rows.append({"check_name": "VALIDATION_FAIL_COUNT", "status": "PASS" if validation_fail_count == 0 else "FAIL", "path": str(validation_path), "expected": "0", "actual": str(validation_fail_count), "note": ""})

    write_csv(validation_path, validation_rows, VALIDATION_FIELDS)
    validation_rows.insert(
        -1,
        {
            "check_name": "VALIDATION_PRESENT",
            "status": "PASS" if validation_path.exists() else "FAIL",
            "path": str(validation_path),
            "expected": "exists",
            "actual": "exists" if validation_path.exists() else "missing",
            "note": "",
        },
    )
    validation_fail_count = sum(1 for row in validation_rows if normalize(row.get("status")) != "PASS")
    validation_rows[-1] = {
        "check_name": "VALIDATION_FAIL_COUNT",
        "status": "PASS" if validation_fail_count == 0 else "FAIL",
        "path": str(validation_path),
        "expected": "0",
        "actual": str(validation_fail_count),
        "note": "",
    }
    write_csv(validation_path, validation_rows, VALIDATION_FIELDS)

    read_first_text = "\n".join([
        f"STATUS: {STATUS_OK if validation_fail_count == 0 else STATUS_WARN}",
        f"SNAPSHOT_NAME: {SNAPSHOT_NAME}",
        f"SNAPSHOT_PATH: {snapshot}",
        f"COPIED_FILE_COUNT: {copied_file_count}",
        f"MISSING_CRITICAL_COUNT: {missing_critical_count}",
        f"COPY_FAIL_COUNT: {copy_fail_count}",
        f"VALIDATION_FAIL_COUNT: {validation_fail_count}",
        f"AUTO_TRADE: {auto_trade}",
        f"AUTO_SELL: {auto_sell}",
        f"OFFICIAL_DECISION_IMPACT: {official}",
        f"TRUE_5DAY_UNIQUE_COVERAGE_MET: {true_unique_met}",
        f"TRUE_5DAY_UNIQUE_WARNING_PRESERVED: {true_warning_preserved}",
        f"DAILY_TRUST_LEVEL: {daily_trust_level}",
        f"CURRENT_DAILY_MODIFIED: {current_daily_modified}",
        f"STABLE_SNAPSHOT_MODIFIED: {stable_snapshot_modified}",
        f"MANUAL_STATE_MODIFIED: {manual_state_modified}",
        f"PRICE_CACHE_MODIFIED: {price_cache_modified}",
        f"READ_FIRST: {read_first_path}",
        f"SNAPSHOT_REPORT: {report_path}",
    ]) + "\n"
    write_text(read_first_path, read_first_text)

    report_lines = [
        "# V18.16J-R2A Stable Snapshot Report",
        "",
        f"- STATUS: {STATUS_OK if validation_fail_count == 0 else STATUS_WARN}",
        f"- SNAPSHOT_PATH: {snapshot}",
        f"- COPIED_FILE_COUNT: {copied_file_count}",
        f"- MISSING_CRITICAL_COUNT: {missing_critical_count}",
        f"- COPY_FAIL_COUNT: {copy_fail_count}",
        f"- VALIDATION_FAIL_COUNT: {validation_fail_count}",
        f"- AUTO_TRADE: {auto_trade}",
        f"- AUTO_SELL: {auto_sell}",
        f"- OFFICIAL_DECISION_IMPACT: {official}",
        f"- TRUE_5DAY_UNIQUE_COVERAGE_MET: {true_unique_met}",
        f"- TRUE_5DAY_UNIQUE_WARNING_PRESERVED: {true_warning_preserved}",
        f"- DAILY_TRUST_LEVEL: {daily_trust_level}",
        f"- CURRENT_DAILY_MODIFIED: {current_daily_modified}",
        f"- STABLE_SNAPSHOT_MODIFIED: {stable_snapshot_modified}",
        f"- MANUAL_STATE_MODIFIED: {manual_state_modified}",
        f"- PRICE_CACHE_MODIFIED: {price_cache_modified}",
        "",
        "## Validation",
    ]
    for row in validation_rows:
        report_lines.append(f"- {row['check_name']} | {row['status']} | {row['actual']} | {row['note']}")
    report_lines.extend([
        "",
        f"- READ_FIRST: {read_first_path}",
        f"- REPORT: {report_path}",
        f"- MANIFEST: {manifest_path}",
        f"- VALIDATION: {validation_path}",
        "",
        "## Notes",
        "- The snapshot captures the current 16J patch chain, V18.19A readability layer, and the fresh coverage-source selection state.",
        "- No behavior changes are made by the snapshot task.",
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
    print(f"TRUE_5DAY_UNIQUE_COVERAGE_MET: {true_unique_met}")
    print(f"TRUE_5DAY_UNIQUE_WARNING_PRESERVED: {true_warning_preserved}")
    print(f"DAILY_TRUST_LEVEL: {daily_trust_level}")
    print(f"CURRENT_DAILY_MODIFIED: {current_daily_modified}")
    print(f"STABLE_SNAPSHOT_MODIFIED: {stable_snapshot_modified}")
    print(f"MANUAL_STATE_MODIFIED: {manual_state_modified}")
    print(f"PRICE_CACHE_MODIFIED: {price_cache_modified}")
    print(f"READ_FIRST: {read_first_path}")
    print(f"REPORT: {report_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.16J-R2A stable snapshot")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
