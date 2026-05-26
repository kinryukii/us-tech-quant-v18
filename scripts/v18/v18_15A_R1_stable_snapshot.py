from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import py_compile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_15A_R1_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_15A_R1_STABLE_SNAPSHOT_WITH_FAILURES"
STATUS_FAIL = "FAIL_V18_15A_R1_STABLE_SNAPSHOT"

EXPECTED_CURRENT_STATUS = "OK_V18_15A_MANUAL_POSITION_TRADE_FEEDBACK_READY"
EXPECTED_POSITION_COUNT = "0"
EXPECTED_TRADE_LOG_ROWS = "0"
EXPECTED_VALIDATION_FAIL_COUNT = "0"

OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
SNAPSHOT_ONLY = "TRUE"

SNAPSHOT_PREFIX = "V18_15A_R1_stable_manual_position_trade_feedback"

SNAPSHOT_FILES = [
    ("script", "scripts/v18/run_v18_15A_manual_position_trade_feedback.ps1", True),
    ("script", "scripts/v18/v18_15A_manual_position_trade_feedback.py", True),
    ("script", "scripts/v18/run_v18_15A_R1_stable_snapshot.ps1", True),
    ("script", "scripts/v18/v18_15A_R1_stable_snapshot.py", True),
    ("manual_template", "state/v18/manual/V18_MANUAL_POSITIONS.csv", True),
    ("manual_template", "state/v18/manual/V18_MANUAL_TRADE_LOG.csv", True),
    ("v18_15a_output", "outputs/v18/positions/V18_15A_CURRENT_MANUAL_POSITION_REVIEW.csv", True),
    ("v18_15a_output", "outputs/v18/positions/V18_15A_CURRENT_MANUAL_TRADE_FEEDBACK.csv", True),
    ("v18_15a_output", "outputs/v18/positions/V18_15A_CURRENT_MANUAL_POSITION_LIFECYCLE_AUDIT.csv", True),
    ("v18_15a_output", "outputs/v18/ops/V18_15A_READ_FIRST.txt", True),
    ("v18_15a_output", "outputs/v18/ops/V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_REPORT.md", True),
    ("v18_15a_output", "outputs/v18/ops/V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_SUMMARY.csv", True),
    ("v18_15a_output", "outputs/v18/ops/V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_INPUT_AUDIT.csv", True),
    ("upstream", "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv", False),
    ("upstream", "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv", False),
    ("upstream", "outputs/v18/ops/V18_14E_R1_READ_FIRST.txt", False),
    ("upstream", "state/v18/candidate_forward_tracker/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv", False),
]

PS_PARSE_FILES = [
    "scripts/v18/run_v18_15A_manual_position_trade_feedback.ps1",
    "scripts/v18/run_v18_15A_R1_stable_snapshot.ps1",
]

PY_COMPILE_FILES = [
    "scripts/v18/v18_15A_manual_position_trade_feedback.py",
    "scripts/v18/v18_15A_R1_stable_snapshot.py",
]

PROTECTED_SNAPSHOT_CHECKS = [
    ("V18_12F_R2", "V18_12F_R2_stable*", "V18_12F_R2_STABLE_MANIFEST.csv"),
    ("V18_12H_R1", "V18_12H_R1_stable*", "V18_12H_R1_STABLE_MANIFEST.csv"),
    ("V18_13A_R1", "V18_13A_R1_stable*", "V18_13A_R1_STABLE_MANIFEST.csv"),
    ("V18_13B_R1", "V18_13B_R1_stable*", "MANIFEST.csv"),
    ("V18_13C_R1", "V18_13C_R1_stable*", "MANIFEST.csv"),
    ("V18_13D_R1", "V18_13D_R1_stable*", "MANIFEST.csv"),
    ("V18_14A_R1", "V18_14A_R1_stable*", "MANIFEST.csv"),
    ("V18_14B_R1", "V18_14B_R1_stable*", "MANIFEST.csv"),
    ("V18_14C_R1", "V18_14C_R1_stable*", "MANIFEST.csv"),
    ("V18_14D_R1", "V18_14D_R1_stable*", "MANIFEST.csv"),
    ("V18_14E_R1", "V18_14E_R1_stable*", "MANIFEST.csv"),
]

DANGEROUS_TOKENS = [
    "SELL_NOW",
    "BUY_NOW_FORCE",
    "AUTO_EXECUTE",
    "LIVE_ORDER",
    "LIVE_SELL",
    "BROKER_ORDER",
]


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8", "utf-8-sig", "cp932", "gbk"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    return []


def csv_fields(path: Path) -> List[str]:
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader.fieldnames or [])
        except Exception:
            continue
    return []


def write_csv(path: Path, rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rel(base: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def first_value(path: Path, key: str) -> str:
    target = f"{key}:"
    bullet_target = f"- {target}"
    lines = [line.strip() for line in read_text(path).splitlines()]
    for i, line in enumerate(lines):
        if line == target:
            for nxt in lines[i + 1 :]:
                if nxt:
                    return nxt.strip("` ")
        if line.startswith(target):
            value = line[len(target) :].strip()
            if value:
                return value.strip("` ")
        if line.startswith(bullet_target):
            value = line[len(bullet_target) :].strip()
            if value:
                return value.strip("` ")
    return ""


def validation_row(name: str, status: str, path: Path | str, expected: str, actual: str, note: str = "") -> Dict[str, str]:
    return {
        "check_name": name,
        "status": status,
        "path": str(path),
        "expected": expected,
        "actual": actual,
        "note": note,
    }


def manifest_row(root: Path, snapshot: Path, category: str, src: Path, dst: Path, status: str, required: bool, error: str = "") -> Dict[str, str]:
    size = ""
    modified = ""
    digest = ""
    if dst.exists() and dst.is_file():
        stat = dst.stat()
        size = str(stat.st_size)
        modified = dt.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        digest = sha256(dst)
    return {
        "category": category,
        "status": status,
        "required": "YES" if required else "NO",
        "source_path": str(src),
        "snapshot_path": str(dst),
        "relative_source_path": rel(root, src),
        "relative_snapshot_path": rel(snapshot, dst),
        "size_bytes": size,
        "last_write_time": modified,
        "sha256": digest,
        "error": error,
    }


def copy_file(root: Path, snapshot: Path, category: str, rel_path: str, required: bool) -> Dict[str, str]:
    src = root / rel_path
    dst = snapshot / rel_path
    if not src.exists() or not src.is_file():
        status = "MISSING_CRITICAL" if required else "MISSING_OPTIONAL"
        return manifest_row(root, snapshot, category, src, dst, status, required, "Source file missing")
    try:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        return manifest_row(root, snapshot, category, src, dst, "COPIED", required)
    except Exception as exc:
        return manifest_row(root, snapshot, category, src, dst, "COPY_FAIL", required, f"{type(exc).__name__}: {exc}")


def metadata_manifest_row(snapshot: Path, path: Path, category: str) -> Dict[str, str]:
    return manifest_row(snapshot, snapshot, category, path, path, "COPIED", True)


def parse_check_ps1(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    escaped = str(path).replace("'", "''")
    command = (
        "$tokens=$null; $errors=$null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{escaped}',[ref]$tokens,[ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { $_.Message }; exit 1 }"
    )
    try:
        proc = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True, timeout=60)
        return proc.returncode == 0, (proc.stderr or proc.stdout or "").strip()
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


def stable_manifest_hashes(snapshot_root: Path, manifest_name: str) -> Tuple[bool, str, int]:
    manifest = snapshot_root / manifest_name
    checked = 0
    if not manifest.exists():
        return False, f"Manifest missing: {manifest}", checked
    problems: List[str] = []
    for row in read_csv_rows(manifest):
        if row.get("status") != "COPIED":
            continue
        rel_snapshot_path = str(row.get("relative_snapshot_path", ""))
        if not rel_snapshot_path or rel_snapshot_path == manifest_name:
            continue
        path = snapshot_root / rel_snapshot_path
        expected = str(row.get("sha256", "")).lower()
        actual = sha256(path).lower()
        checked += 1
        if not path.exists():
            problems.append(f"MISSING {path}")
        elif expected and actual != expected:
            problems.append(f"HASH_MISMATCH {path}")
    if problems:
        return False, "; ".join(problems[:5]), checked
    return True, "", checked


def protected_snapshots_unchanged(root: Path, pattern: str, manifest_name: str) -> Tuple[bool, str, int]:
    matches = list((root / "archive/stable").glob(pattern))
    if not matches:
        return False, f"No snapshot matched {pattern}", 0
    checked = 0
    problems: List[str] = []
    for snapshot_root in matches:
        ok, note, count = stable_manifest_hashes(snapshot_root, manifest_name)
        checked += count
        if not ok:
            problems.append(note)
    if problems:
        return False, "; ".join(problems[:5]), checked
    return True, "", checked


def dangerous_hits(root: Path, paths: Sequence[Path]) -> List[str]:
    hits = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        text = read_text(path)
        for token in DANGEROUS_TOKENS:
            if token in text:
                hits.append(f"{rel(root, path)}::{token}")
    return hits


def build_restore_script(snapshot: Path) -> str:
    restore_files = [
        rel_path.replace("/", "\\")
        for category, rel_path, required in SNAPSHOT_FILES
        if category in {"script", "manual_template", "v18_15a_output"} and required
    ]
    file_lines = "\n".join(f'    "{path}"' for path in restore_files)
    return f'''param(
    [string]$Root = "D:\\us-tech-quant",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$Snapshot = "{snapshot}"

Write-Host "=== V18.15A-R1 STABLE SNAPSHOT RESTORE ==="
Write-Host "SNAPSHOT: $Snapshot"
Write-Host "ROOT: $Root"
Write-Host "APPLY: $Apply"
Write-Host "SNAPSHOT_ONLY: TRUE"

if (-not (Test-Path -LiteralPath $Snapshot)) {{
    throw "MISSING_SNAPSHOT: $Snapshot"
}}

$Files = @(
{file_lines}
)

foreach ($File in $Files) {{
    $Src = Join-Path $Snapshot $File
    $Dst = Join-Path $Root $File
    if (Test-Path -LiteralPath $Src) {{
        Write-Host "RESTORE_FILE: $File"
        if ($Apply) {{
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dst) | Out-Null
            Copy-Item -LiteralPath $Src -Destination $Dst -Force
        }}
    }}
    else {{
        Write-Host "MISSING_IN_SNAPSHOT: $File"
    }}
}}

if (-not $Apply) {{
    Write-Host "DRYRUN_ONLY. Re-run with -Apply to restore V18.15A-R1 manual feedback files."
}}
else {{
    Write-Host "RESTORE_APPLIED."
}}
'''


def build(root: Path) -> Tuple[Dict[str, str], int]:
    stamp = now_stamp()
    snapshot = root / "archive/stable" / f"{SNAPSHOT_PREFIX}_{stamp}"
    ops_dir = root / "outputs/v18/ops"
    ensure_dir(snapshot)
    ensure_dir(ops_dir)

    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_15A_R1_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_15A_R1.ps1"
    report_path = ops_dir / "V18_15A_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    read_first_path = ops_dir / "V18_15A_R1_READ_FIRST.txt"

    current_read_first = root / "outputs/v18/ops/V18_15A_READ_FIRST.txt"
    positions_path = root / "state/v18/manual/V18_MANUAL_POSITIONS.csv"
    trades_path = root / "state/v18/manual/V18_MANUAL_TRADE_LOG.csv"
    positions_rows = read_csv_rows(positions_path)
    trades_rows = read_csv_rows(trades_path)

    current_values = {
        "STATUS": first_value(current_read_first, "STATUS"),
        "POSITION_COUNT": first_value(current_read_first, "POSITION_COUNT"),
        "TRADE_LOG_ROWS": first_value(current_read_first, "TRADE_LOG_ROWS"),
        "LINKED_SIGNAL_ROWS": first_value(current_read_first, "LINKED_SIGNAL_ROWS"),
        "UNLINKED_POSITION_ROWS": first_value(current_read_first, "UNLINKED_POSITION_ROWS"),
        "CURRENT_PRICE_AVAILABLE_ROWS": first_value(current_read_first, "CURRENT_PRICE_AVAILABLE_ROWS"),
        "CURRENT_PRICE_MISSING_ROWS": first_value(current_read_first, "CURRENT_PRICE_MISSING_ROWS"),
        "VALIDATION_FAIL_COUNT": first_value(current_read_first, "VALIDATION_FAIL_COUNT"),
        "OFFICIAL_DECISION_IMPACT": first_value(current_read_first, "OFFICIAL_DECISION_IMPACT"),
        "AUTO_TRADE": first_value(current_read_first, "AUTO_TRADE"),
        "AUTO_SELL": first_value(current_read_first, "AUTO_SELL"),
    }

    validations: List[Dict[str, str]] = []
    expected = {
        "STATUS": EXPECTED_CURRENT_STATUS,
        "POSITION_COUNT": EXPECTED_POSITION_COUNT,
        "TRADE_LOG_ROWS": EXPECTED_TRADE_LOG_ROWS,
        "VALIDATION_FAIL_COUNT": EXPECTED_VALIDATION_FAIL_COUNT,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
    }
    for key, expected_value in expected.items():
        actual = current_values.get(key, "")
        validations.append(validation_row(f"CURRENT_V18_15A_{key}", "PASS" if actual == expected_value else "FAIL", current_read_first, expected_value, actual))

    position_fields = csv_fields(positions_path)
    trade_fields = csv_fields(trades_path)
    validations.append(validation_row("MANUAL_POSITIONS_TEMPLATE_READABLE", "PASS" if positions_path.exists() and position_fields else "FAIL", positions_path, "readable_template", f"fields={len(position_fields)} rows={len(positions_rows)}"))
    validations.append(validation_row("MANUAL_TRADE_LOG_TEMPLATE_READABLE", "PASS" if trades_path.exists() and trade_fields else "FAIL", trades_path, "readable_template", f"fields={len(trade_fields)} rows={len(trades_rows)}"))

    for rel_path in PS_PARSE_FILES:
        path = root / rel_path
        ok, err = parse_check_ps1(path)
        validations.append(validation_row(f"POWERSHELL_PARSE_{Path(rel_path).name}", "PASS" if ok else "FAIL", path, "parse_ok", "parse_ok" if ok else "parse_fail", err))

    for rel_path in PY_COMPILE_FILES:
        path = root / rel_path
        ok, err = compile_check_py(path)
        validations.append(validation_row(f"PY_COMPILE_{Path(rel_path).name}", "PASS" if ok else "FAIL", path, "compile_ok", "compile_ok" if ok else "compile_fail", err))

    for label, pattern, manifest_name in PROTECTED_SNAPSHOT_CHECKS:
        ok, note, checked = protected_snapshots_unchanged(root, pattern, manifest_name)
        validations.append(validation_row(f"{label}_PROTECTED_STABLE_SNAPSHOT_UNCHANGED", "PASS" if ok else "FAIL", root / "archive/stable", "manifest_hashes_match", f"checked={checked}" if ok else "mismatch", note))

    manifest_rows: List[Dict[str, str]] = []
    for category, rel_path, required in SNAPSHOT_FILES:
        manifest_rows.append(copy_file(root, snapshot, category, rel_path, required))

    restore_path.write_text(build_restore_script(snapshot), encoding="utf-8")
    readme = f"""# V18.15A-R1 Stable Snapshot

Created: {now_text()}

Snapshot: {snapshot}

Purpose: Stable restore point for the V18.15A manual position and trade feedback layer.

Accepted state:
STATUS: {current_values['STATUS']}
POSITION_COUNT: {current_values['POSITION_COUNT']}
TRADE_LOG_ROWS: {current_values['TRADE_LOG_ROWS']}
LINKED_SIGNAL_ROWS: {current_values['LINKED_SIGNAL_ROWS']}
UNLINKED_POSITION_ROWS: {current_values['UNLINKED_POSITION_ROWS']}
CURRENT_PRICE_AVAILABLE_ROWS: {current_values['CURRENT_PRICE_AVAILABLE_ROWS']}
CURRENT_PRICE_MISSING_ROWS: {current_values['CURRENT_PRICE_MISSING_ROWS']}
VALIDATION_FAIL_COUNT: {current_values['VALIDATION_FAIL_COUNT']}

Interpretation: Empty manual templates are expected and valid for R1.

Safety:
OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}
AUTO_TRADE: {AUTO_TRADE}
AUTO_SELL: {AUTO_SELL}
SNAPSHOT_ONLY: {SNAPSHOT_ONLY}
"""
    readme_path.write_text(readme, encoding="utf-8")
    manifest_rows.append(metadata_manifest_row(snapshot, restore_path, "snapshot_metadata"))
    manifest_rows.append(metadata_manifest_row(snapshot, readme_path, "snapshot_metadata"))

    scan_paths = [
        root / "state/v18/manual/V18_MANUAL_POSITIONS.csv",
        root / "state/v18/manual/V18_MANUAL_TRADE_LOG.csv",
        root / "outputs/v18/positions/V18_15A_CURRENT_MANUAL_POSITION_REVIEW.csv",
        root / "outputs/v18/positions/V18_15A_CURRENT_MANUAL_TRADE_FEEDBACK.csv",
        root / "outputs/v18/positions/V18_15A_CURRENT_MANUAL_POSITION_LIFECYCLE_AUDIT.csv",
        root / "outputs/v18/ops/V18_15A_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_REPORT.md",
        root / "outputs/v18/ops/V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_SUMMARY.csv",
        root / "outputs/v18/ops/V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_INPUT_AUDIT.csv",
        snapshot / "state/v18/manual/V18_MANUAL_POSITIONS.csv",
        snapshot / "state/v18/manual/V18_MANUAL_TRADE_LOG.csv",
        snapshot / "outputs/v18/positions/V18_15A_CURRENT_MANUAL_POSITION_REVIEW.csv",
        snapshot / "outputs/v18/positions/V18_15A_CURRENT_MANUAL_TRADE_FEEDBACK.csv",
        snapshot / "outputs/v18/positions/V18_15A_CURRENT_MANUAL_POSITION_LIFECYCLE_AUDIT.csv",
        snapshot / "outputs/v18/ops/V18_15A_READ_FIRST.txt",
        snapshot / "outputs/v18/ops/V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_REPORT.md",
        snapshot / "outputs/v18/ops/V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_SUMMARY.csv",
        snapshot / "outputs/v18/ops/V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_INPUT_AUDIT.csv",
        readme_path,
        restore_path,
    ]
    hits = dangerous_hits(root, scan_paths)
    validations.append(validation_row("NO_DANGEROUS_TOKEN_IN_V18_15A_OUTPUTS_AND_SNAPSHOT", "PASS" if not hits else "FAIL", "V18.15A outputs and snapshot artifacts", "clean", "clean" if not hits else "found", "NONE" if not hits else ";".join(hits[:10])))

    validation_fields = ["check_name", "status", "path", "expected", "actual", "note"]
    manifest_fields = ["category", "status", "required", "source_path", "snapshot_path", "relative_source_path", "relative_snapshot_path", "size_bytes", "last_write_time", "sha256", "error"]
    write_csv(validation_path, validations, validation_fields)
    manifest_rows.append(metadata_manifest_row(snapshot, validation_path, "snapshot_metadata"))
    write_csv(manifest_path, manifest_rows, manifest_fields)
    manifest_rows.append(metadata_manifest_row(snapshot, manifest_path, "snapshot_metadata"))
    write_csv(manifest_path, manifest_rows, manifest_fields)

    copied_file_count = sum(1 for row in manifest_rows if row["status"] == "COPIED")
    copy_fail_count = sum(1 for row in manifest_rows if row["status"] == "COPY_FAIL")
    missing_critical_count = sum(1 for row in manifest_rows if row["status"] == "MISSING_CRITICAL")
    validation_fail_count = sum(1 for row in validations if row["status"] != "PASS")
    status = STATUS_OK if copy_fail_count == 0 and missing_critical_count == 0 and validation_fail_count == 0 else STATUS_WARN
    if current_values["STATUS"] != EXPECTED_CURRENT_STATUS:
        status = STATUS_FAIL

    values = {
        "STATUS": status,
        "SNAPSHOT_PATH": str(snapshot),
        "COPIED_FILE_COUNT": str(copied_file_count),
        "COPY_FAIL_COUNT": str(copy_fail_count),
        "MISSING_CRITICAL_COUNT": str(missing_critical_count),
        "VALIDATION_FAIL_COUNT": str(validation_fail_count),
        "POSITION_COUNT": current_values["POSITION_COUNT"],
        "TRADE_LOG_ROWS": current_values["TRADE_LOG_ROWS"],
        "LINKED_SIGNAL_ROWS": current_values["LINKED_SIGNAL_ROWS"],
        "UNLINKED_POSITION_ROWS": current_values["UNLINKED_POSITION_ROWS"],
        "CURRENT_PRICE_AVAILABLE_ROWS": current_values["CURRENT_PRICE_AVAILABLE_ROWS"],
        "CURRENT_PRICE_MISSING_ROWS": current_values["CURRENT_PRICE_MISSING_ROWS"],
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "SNAPSHOT_ONLY": SNAPSHOT_ONLY,
        "DANGEROUS_TOKEN_DETECTED": "YES" if hits else "NO",
        "MANUAL_TEMPLATES_INCLUDED": "YES" if positions_path.exists() and trades_path.exists() else "NO",
        "PROTECTED_STABLE_SNAPSHOTS_UNCHANGED": "YES" if all(row["status"] == "PASS" for row in validations if "PROTECTED_STABLE_SNAPSHOT" in row["check_name"]) else "NO",
    }

    read_first_keys = [
        "STATUS", "SNAPSHOT_PATH", "COPIED_FILE_COUNT", "COPY_FAIL_COUNT", "MISSING_CRITICAL_COUNT",
        "VALIDATION_FAIL_COUNT", "POSITION_COUNT", "TRADE_LOG_ROWS", "LINKED_SIGNAL_ROWS",
        "UNLINKED_POSITION_ROWS", "CURRENT_PRICE_AVAILABLE_ROWS", "CURRENT_PRICE_MISSING_ROWS",
        "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL", "SNAPSHOT_ONLY",
        "DANGEROUS_TOKEN_DETECTED", "MANUAL_TEMPLATES_INCLUDED", "PROTECTED_STABLE_SNAPSHOTS_UNCHANGED",
    ]
    write_text(read_first_path, "\n".join(f"{key}: {values[key]}" for key in read_first_keys) + "\n")

    report = [
        "# V18.15A-R1 Stable Snapshot",
        "",
        *[f"- {key}: {values[key]}" for key in read_first_keys],
        "",
        "## Validation",
        "",
        f"- VALIDATION: {validation_path}",
        f"- MANIFEST: {manifest_path}",
        f"- RESTORE_SCRIPT: {restore_path}",
        "",
        "Snapshot only. No trading impact.",
    ]
    write_text(report_path, "\n".join(report) + "\n")

    for key in [
        "STATUS", "SNAPSHOT_PATH", "COPIED_FILE_COUNT", "COPY_FAIL_COUNT", "MISSING_CRITICAL_COUNT",
        "VALIDATION_FAIL_COUNT", "POSITION_COUNT", "TRADE_LOG_ROWS", "LINKED_SIGNAL_ROWS",
        "UNLINKED_POSITION_ROWS", "CURRENT_PRICE_AVAILABLE_ROWS", "CURRENT_PRICE_MISSING_ROWS",
        "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL", "SNAPSHOT_ONLY",
    ]:
        print(f"{key}: {values[key]}")
    print(f"DANGEROUS_TOKEN_DETECTED: {values['DANGEROUS_TOKEN_DETECTED']}")
    print(f"MANUAL_TEMPLATES_INCLUDED: {values['MANUAL_TEMPLATES_INCLUDED']}")
    print(f"PROTECTED_STABLE_SNAPSHOTS_UNCHANGED: {values['PROTECTED_STABLE_SNAPSHOTS_UNCHANGED']}")
    print(f"READ_FIRST: {read_first_path}")
    print(f"REPORT: {report_path}")
    print(f"MANIFEST: {manifest_path}")
    print(f"VALIDATION: {validation_path}")
    return values, 0 if status == STATUS_OK else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Create V18.15A-R1 manual position trade feedback stable snapshot.")
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    _, code = build(Path(args.root))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
