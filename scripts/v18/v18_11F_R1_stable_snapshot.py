from __future__ import annotations

import csv
import datetime as dt
import hashlib
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


MODE = "SNAPSHOT_ONLY"
OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_WEIGHT_CHANGE = "DISABLED"
AUTO_PROMOTION = "DISABLED"
AUTO_TRADE = "DISABLED"
OFFICIAL_POINTER_MODIFIED = "False"
CURRENT_SHADOW_RESEARCH_DAILY_MODIFIED = "False"
STATE_SOURCE_MODIFIED = "False"
CANDIDATE_TRACKER_STATE_MODIFIED = "False"
FACTOR_WEIGHTS_MODIFIED = "False"


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: List[Dict[str, str]], fields: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="utf-8-sig")
        except Exception:
            return ""


def read_first_value(path: Path, key: str) -> str:
    text = read_text(path)
    lines = [line.strip() for line in text.splitlines()]
    target = key.strip()
    if not target.endswith(":"):
        target += ":"
    for i, line in enumerate(lines):
        if line == target:
            for nxt in lines[i + 1 :]:
                if nxt:
                    return nxt
        if line.startswith(target):
            val = line[len(target) :].strip()
            if val:
                return val
    return ""


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_row(root: Path, snapshot: Path, src: Path, dst: Path, category: str, status: str, error: str = "") -> Dict[str, str]:
    size = ""
    modified = ""
    digest = ""
    if src.exists() and src.is_file():
        stat = src.stat()
        size = str(stat.st_size)
        modified = dt.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        if status == "COPIED":
            digest = sha256(dst)
    return {
        "category": category,
        "status": status,
        "source_path": str(src),
        "snapshot_path": str(dst),
        "relative_source_path": rel(root, src),
        "relative_snapshot_path": rel(snapshot, dst),
        "size_bytes": size,
        "last_write_time": modified,
        "sha256": digest,
        "error": error,
    }


def snapshot_metadata_row(snapshot: Path, path: Path, category: str) -> Dict[str, str]:
    size = ""
    modified = ""
    digest = ""
    if path.exists() and path.is_file():
        stat = path.stat()
        size = str(stat.st_size)
        modified = dt.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        digest = sha256(path)
    return {
        "category": category,
        "status": "COPIED",
        "source_path": str(path),
        "snapshot_path": str(path),
        "relative_source_path": rel(snapshot, path),
        "relative_snapshot_path": rel(snapshot, path),
        "size_bytes": size,
        "last_write_time": modified,
        "sha256": digest,
        "error": "",
    }


def copy_file(root: Path, snapshot: Path, src: Path, category: str) -> Dict[str, str]:
    dst = snapshot / rel(root, src)
    try:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        return manifest_row(root, snapshot, src, dst, category, "COPIED")
    except Exception as exc:
        return manifest_row(root, snapshot, src, dst, category, "COPY_FAIL", f"{type(exc).__name__}: {exc}")


def copy_tree(root: Path, snapshot: Path, rel_layer: str, category: str) -> List[Dict[str, str]]:
    src_dir = root / rel_layer
    if not src_dir.exists():
        return [
            {
                "category": category,
                "status": "MISSING_LAYER",
                "source_path": str(src_dir),
                "snapshot_path": "",
                "relative_source_path": rel_layer,
                "relative_snapshot_path": "",
                "size_bytes": "",
                "last_write_time": "",
                "sha256": "",
                "error": "Layer not found",
            }
        ]
    rows = []
    for src in src_dir.rglob("*"):
        if src.is_file():
            rows.append(copy_file(root, snapshot, src, category))
    return rows


def copy_existing_files(root: Path, snapshot: Path, files: Iterable[Path], category: str, critical: bool = False) -> List[Dict[str, str]]:
    rows = []
    for src in files:
        if src.exists() and src.is_file():
            rows.append(copy_file(root, snapshot, src, category))
        elif critical:
            rows.append(
                {
                    "category": category,
                    "status": "MISSING_CRITICAL",
                    "source_path": str(src),
                    "snapshot_path": "",
                    "relative_source_path": rel(root, src),
                    "relative_snapshot_path": "",
                    "size_bytes": "",
                    "last_write_time": "",
                    "sha256": "",
                    "error": "Critical file missing",
                }
            )
    return rows


def parse_check_ps1(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "$tokens=$null; $errors=$null; "
            f"[System.Management.Automation.Language.Parser]::ParseFile('{str(path)}',[ref]$tokens,[ref]$errors) | Out-Null; "
            "if ($errors.Count -gt 0) { $errors | ForEach-Object { $_.Message }; exit 1 }"
        ),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode == 0:
            return True, ""
        return False, (proc.stderr or proc.stdout or "").strip()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def compile_check_py(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    try:
        py_compile.compile(str(path), doraise=True)
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def validation_row(name: str, status: str, path: Path | str, expected: str, actual: str, note: str = "") -> Dict[str, str]:
    return {
        "check_name": name,
        "status": status,
        "path": str(path),
        "expected": expected,
        "actual": actual,
        "note": note,
    }


def build_validations(root: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    ps_scripts = [
        root / "scripts/v18/run_v18_11F_shadow_factor_research_chain.ps1",
        root / "scripts/v18/run_v18_11D_shadow_factor_daily.ps1",
        root / "scripts/v18/run_v18_11E_shadow_factor_summary.ps1",
    ]
    for p in ps_scripts:
        ok, err = parse_check_ps1(p)
        rows.append(validation_row(f"POWERSHELL_PARSE_{p.name}", "PASS" if ok else "FAIL", p, "parse_ok", "parse_ok" if ok else "parse_fail", err))

    py_scripts = [
        root / "scripts/v18/v18_11_calendar_vwap_rv_shadow_factors.py",
        root / "scripts/v18/v18_11E_shadow_factor_summary.py",
    ]
    for p in py_scripts:
        ok, err = compile_check_py(p)
        rows.append(validation_row(f"PY_COMPILE_{p.name}", "PASS" if ok else "FAIL", p, "compile_ok", "compile_ok" if ok else "compile_fail", err))

    official = root / "scripts/v18/run_v18_current_official_daily.ps1"
    official_text = read_text(official)
    official_expected = "run_v18_9C_official_daily_with_sim_validation.ps1"
    official_ok = official_expected in official_text
    rows.append(validation_row("OFFICIAL_POINTER_UNCHANGED", "PASS" if official_ok else "FAIL", official, official_expected, "present" if official_ok else "missing"))

    shadow = root / "scripts/v18/run_v18_current_shadow_research_daily.ps1"
    shadow_text = read_text(shadow)
    shadow_expected = "run_v18_10D_official_daily_with_factor_weight_research.ps1"
    shadow_ok = shadow_expected in shadow_text
    rows.append(validation_row("CURRENT_SHADOW_RESEARCH_DAILY_UNCHANGED", "PASS" if shadow_ok else "FAIL", shadow, shadow_expected, "present" if shadow_ok else "missing"))

    read_first = root / "outputs/v18/factor_research/V18_11F_READ_FIRST.txt"
    for key, expected in [
        ("MODE", "SHADOW_ONLY"),
        ("OFFICIAL_DECISION_IMPACT", OFFICIAL_DECISION_IMPACT),
        ("AUTO_WEIGHT_CHANGE", AUTO_WEIGHT_CHANGE),
        ("AUTO_PROMOTION", AUTO_PROMOTION),
        ("AUTO_TRADE", AUTO_TRADE),
    ]:
        actual = read_first_value(read_first, key)
        rows.append(validation_row(f"V18_11F_{key}", "PASS" if actual == expected else "FAIL", read_first, expected, actual))

    return rows


def restore_script_text(snapshot: Path) -> str:
    return f'''param(
    [string]$Root = "D:\\us-tech-quant",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$Snapshot = "{snapshot}"

Write-Host ""
Write-Host "=== V18.11F-R1 STABLE SNAPSHOT RESTORE ==="
Write-Host "SNAPSHOT: $Snapshot"
Write-Host "ROOT: $Root"
Write-Host "APPLY: $Apply"

if (-not (Test-Path -LiteralPath $Snapshot)) {{
    throw "MISSING_SNAPSHOT: $Snapshot"
}}

$Layers = @(
    "scripts\\v18",
    "outputs\\v18\\factor_research",
    "outputs\\v18\\factor_registry",
    "outputs\\v18\\ops",
    "outputs\\v18\\read_center",
    "state\\v18"
)

foreach ($Layer in $Layers) {{
    $Src = Join-Path $Snapshot $Layer
    $Dst = Join-Path $Root $Layer
    if (Test-Path -LiteralPath $Src) {{
        Write-Host "RESTORE_LAYER: $Layer"
        if ($Apply) {{
            New-Item -ItemType Directory -Force -Path $Dst | Out-Null
            Copy-Item -LiteralPath $Src -Destination (Split-Path -Parent $Dst) -Recurse -Force
        }}
    }}
}}

if (-not $Apply) {{
    Write-Host "DRYRUN_ONLY. Re-run with -Apply to restore."
}}
else {{
    Write-Host "RESTORE_APPLIED."
}}
'''


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"D:\us-tech-quant")
    stamp = now_stamp()
    snapshot = root / "archive/stable" / f"V18_11F_R1_stable_shadow_factor_research_chain_{stamp}"
    ensure_dir(snapshot)
    out_dir = root / "outputs/v18/ops"
    ensure_dir(out_dir)

    manifest_path = snapshot / "V18_11F_R1_STABLE_MANIFEST.csv"
    validation_path = snapshot / "V18_11F_R1_STABLE_VALIDATION_CHECKS.csv"
    readme_path = snapshot / "V18_11F_R1_STABLE_SNAPSHOT_README.txt"
    restore_path = snapshot / "restore_v18_11F_R1_stable_snapshot.ps1"
    report_path = out_dir / "V18_11F_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    read_first_path = out_dir / "V18_11F_R1_READ_FIRST.txt"

    validations = build_validations(root)
    parse_fail_count = sum(1 for r in validations if r["check_name"].startswith("POWERSHELL_PARSE_") and r["status"] != "PASS")
    py_compile_fail_count = sum(1 for r in validations if r["check_name"].startswith("PY_COMPILE_") and r["status"] != "PASS")

    manifest_rows: List[Dict[str, str]] = []
    manifest_rows.extend(copy_tree(root, snapshot, "scripts/v18", "scripts_v18"))
    manifest_rows.extend(copy_tree(root, snapshot, "outputs/v18/factor_research", "outputs_factor_research"))
    manifest_rows.extend(copy_tree(root, snapshot, "outputs/v18/factor_registry", "outputs_factor_registry"))

    ops_files = [
        root / "outputs/v18/ops/V18_11F_CURRENT_SHADOW_FACTOR_RESEARCH_CHAIN_STEPS.csv",
        root / "outputs/v18/ops/V18_11D_CURRENT_SHADOW_FACTOR_DAILY_STEPS.csv",
        root / "outputs/v18/ops/V18_CLEANUP_AUDIT_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_CLEANUP_AUDIT_CURRENT.md",
        root / "outputs/v18/ops/V18_CLEANUP_AUDIT_CURRENT.csv",
    ]
    manifest_rows.extend(copy_existing_files(root, snapshot, ops_files, "outputs_ops_context", critical=False))

    state_files = [
        root / "state/v18/factor_registry/V18_CURRENT_FACTOR_REGISTRY.csv",
        root / "state/v18/simulation/V18_CURRENT_SIM_CANDIDATE_TRACKER.csv",
        root / "state/v18/V18_6C_CURRENT_TECHNICAL_TIMING_FORWARD_TRACKER.csv",
    ]
    manifest_rows.extend(copy_existing_files(root, snapshot, state_files, "state_required_active", critical=True))

    manifest_rows.extend(copy_tree(root, snapshot, "outputs/v18/read_center", "outputs_read_center_context"))

    restore_path.write_text(restore_script_text(snapshot), encoding="utf-8")
    readme_path.write_text(
        f"""V18.11F-R1 STABLE SNAPSHOT README

Created:
{now_text()}

Mode:
{MODE}

Snapshot:
{snapshot}

Purpose:
Stable snapshot for the independent V18.11F shadow factor research chain.

Safety:
OFFICIAL_DECISION_IMPACT={OFFICIAL_DECISION_IMPACT}
AUTO_WEIGHT_CHANGE={AUTO_WEIGHT_CHANGE}
AUTO_PROMOTION={AUTO_PROMOTION}
AUTO_TRADE={AUTO_TRADE}
OFFICIAL_POINTER_MODIFIED={OFFICIAL_POINTER_MODIFIED}
CURRENT_SHADOW_RESEARCH_DAILY_MODIFIED={CURRENT_SHADOW_RESEARCH_DAILY_MODIFIED}
STATE_SOURCE_MODIFIED={STATE_SOURCE_MODIFIED}
CANDIDATE_TRACKER_STATE_MODIFIED={CANDIDATE_TRACKER_STATE_MODIFIED}
FACTOR_WEIGHTS_MODIFIED={FACTOR_WEIGHTS_MODIFIED}

Restore:
The restore script is generated but was not executed by snapshot creation.
""",
        encoding="utf-8",
    )
    manifest_rows.append(snapshot_metadata_row(snapshot, restore_path, "snapshot_metadata"))
    manifest_rows.append(snapshot_metadata_row(snapshot, readme_path, "snapshot_metadata"))

    manifest_fields = [
        "category",
        "status",
        "source_path",
        "snapshot_path",
        "relative_source_path",
        "relative_snapshot_path",
        "size_bytes",
        "last_write_time",
        "sha256",
        "error",
    ]
    validation_fields = ["check_name", "status", "path", "expected", "actual", "note"]
    write_csv(manifest_path, manifest_rows, manifest_fields)
    write_csv(validation_path, validations, validation_fields)
    manifest_rows.append(snapshot_metadata_row(snapshot, validation_path, "snapshot_metadata"))

    # Add the manifest itself after the first write, then rewrite with the self-entry included.
    manifest_rows.append(snapshot_metadata_row(snapshot, manifest_path, "snapshot_metadata"))
    write_csv(manifest_path, manifest_rows, manifest_fields)

    copied_file_count = sum(1 for r in manifest_rows if r["status"] == "COPIED")
    missing_layer_count = sum(1 for r in manifest_rows if r["status"] == "MISSING_LAYER")
    copy_fail_count = sum(1 for r in manifest_rows if r["status"] == "COPY_FAIL")
    missing_critical_count = sum(1 for r in manifest_rows if r["status"] == "MISSING_CRITICAL")
    fail_count = copy_fail_count + missing_critical_count + parse_fail_count + py_compile_fail_count
    status = "OK_V18_11F_R1_STABLE_SNAPSHOT_READY" if fail_count == 0 else "WARN_V18_11F_R1_STABLE_SNAPSHOT_WITH_FAILURES"

    report = f"""# V18.11F-R1 Stable Snapshot

- STATUS: `{status}`
- MODE: `{MODE}`
- SNAPSHOT_PATH: `{snapshot}`
- COPIED_FILE_COUNT: `{copied_file_count}`
- MISSING_LAYER_COUNT: `{missing_layer_count}`
- COPY_FAIL_COUNT: `{copy_fail_count}`
- MISSING_CRITICAL_COUNT: `{missing_critical_count}`
- PARSE_FAIL_COUNT: `{parse_fail_count}`
- PY_COMPILE_FAIL_COUNT: `{py_compile_fail_count}`
- OFFICIAL_DECISION_IMPACT: `{OFFICIAL_DECISION_IMPACT}`
- AUTO_WEIGHT_CHANGE: `{AUTO_WEIGHT_CHANGE}`
- AUTO_PROMOTION: `{AUTO_PROMOTION}`
- AUTO_TRADE: `{AUTO_TRADE}`
- OFFICIAL_POINTER_MODIFIED: `{OFFICIAL_POINTER_MODIFIED}`
- CURRENT_SHADOW_RESEARCH_DAILY_MODIFIED: `{CURRENT_SHADOW_RESEARCH_DAILY_MODIFIED}`
- STATE_SOURCE_MODIFIED: `{STATE_SOURCE_MODIFIED}`
- CANDIDATE_TRACKER_STATE_MODIFIED: `{CANDIDATE_TRACKER_STATE_MODIFIED}`
- FACTOR_WEIGHTS_MODIFIED: `{FACTOR_WEIGHTS_MODIFIED}`

## Files

- MANIFEST: `{manifest_path}`
- VALIDATION_CHECKS: `{validation_path}`
- RESTORE_SCRIPT: `{restore_path}`
- README: `{readme_path}`

## Note

The restore script was generated but not executed.
"""
    report_path.write_text(report, encoding="utf-8")

    read_first = f"""V18.11F-R1 STABLE SNAPSHOT READ FIRST

STATUS:
{status}

MODE:
{MODE}

SNAPSHOT_PATH:
{snapshot}

COPIED_FILE_COUNT:
{copied_file_count}

MISSING_LAYER_COUNT:
{missing_layer_count}

COPY_FAIL_COUNT:
{copy_fail_count}

MISSING_CRITICAL_COUNT:
{missing_critical_count}

PARSE_FAIL_COUNT:
{parse_fail_count}

PY_COMPILE_FAIL_COUNT:
{py_compile_fail_count}

OFFICIAL_DECISION_IMPACT:
{OFFICIAL_DECISION_IMPACT}

AUTO_WEIGHT_CHANGE:
{AUTO_WEIGHT_CHANGE}

AUTO_PROMOTION:
{AUTO_PROMOTION}

AUTO_TRADE:
{AUTO_TRADE}

OFFICIAL_POINTER_MODIFIED:
{OFFICIAL_POINTER_MODIFIED}

CURRENT_SHADOW_RESEARCH_DAILY_MODIFIED:
{CURRENT_SHADOW_RESEARCH_DAILY_MODIFIED}

STATE_SOURCE_MODIFIED:
{STATE_SOURCE_MODIFIED}

CANDIDATE_TRACKER_STATE_MODIFIED:
{CANDIDATE_TRACKER_STATE_MODIFIED}

FACTOR_WEIGHTS_MODIFIED:
{FACTOR_WEIGHTS_MODIFIED}

MANIFEST:
{manifest_path}

VALIDATION_CHECKS:
{validation_path}

RESTORE_SCRIPT:
{restore_path}

REPORT:
{report_path}
"""
    read_first_path.write_text(read_first, encoding="utf-8")

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"SNAPSHOT_PATH: {snapshot}")
    print(f"COPIED_FILE_COUNT: {copied_file_count}")
    print(f"MISSING_LAYER_COUNT: {missing_layer_count}")
    print(f"COPY_FAIL_COUNT: {copy_fail_count}")
    print(f"MISSING_CRITICAL_COUNT: {missing_critical_count}")
    print(f"PARSE_FAIL_COUNT: {parse_fail_count}")
    print(f"PY_COMPILE_FAIL_COUNT: {py_compile_fail_count}")
    print(f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}")
    print(f"AUTO_WEIGHT_CHANGE: {AUTO_WEIGHT_CHANGE}")
    print(f"AUTO_PROMOTION: {AUTO_PROMOTION}")
    print(f"AUTO_TRADE: {AUTO_TRADE}")
    print(f"OFFICIAL_POINTER_MODIFIED: {OFFICIAL_POINTER_MODIFIED}")
    print(f"CURRENT_SHADOW_RESEARCH_DAILY_MODIFIED: {CURRENT_SHADOW_RESEARCH_DAILY_MODIFIED}")
    print(f"STATE_SOURCE_MODIFIED: {STATE_SOURCE_MODIFIED}")
    print(f"CANDIDATE_TRACKER_STATE_MODIFIED: {CANDIDATE_TRACKER_STATE_MODIFIED}")
    print(f"FACTOR_WEIGHTS_MODIFIED: {FACTOR_WEIGHTS_MODIFIED}")
    print(f"MANIFEST: {manifest_path}")
    print(f"VALIDATION_CHECKS: {validation_path}")
    print(f"RESTORE_SCRIPT: {restore_path}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first_path}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
