from __future__ import annotations

import csv
import datetime as dt
import hashlib
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


MODE = "SNAPSHOT_ONLY"
STATUS_OK = "OK_V18_12F_R1_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_12F_R1_STABLE_SNAPSHOT_WITH_FAILURES"
SHADOW_ONLY = "TRUE"
OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_SELL = "DISABLED"
AUTO_TRADE = "DISABLED"
EXPECTED_SHADOW_STATUS = "SKIPPED_USE_EXISTING_OUTPUTS"
EXPECTED_SELL_TIMING_STATUS = "OK_V18_12E_SELL_TIMING_DAILY_WRAPPER_READY"

SNAPSHOT_FILES = [
    ("script", "scripts/v18/run_v18_12F_shadow_research_daily_with_sell_timing.ps1"),
    ("script", "scripts/v18/v18_12F_shadow_research_sell_timing_read_center.py"),
    ("output", "outputs/v18/sell_timing/V18_12F_READ_FIRST.txt"),
    ("output", "outputs/v18/sell_timing/V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_READ_CENTER.md"),
    ("output", "outputs/v18/sell_timing/V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_SUMMARY.csv"),
    ("output", "outputs/v18/sell_timing/V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_INPUT_AUDIT.csv"),
]

PS_PARSE_FILES = [
    "scripts/v18/run_v18_12F_shadow_research_daily_with_sell_timing.ps1",
    "scripts/v18/run_v18_12F_R1_stable_snapshot.ps1",
]

PY_COMPILE_FILES = [
    "scripts/v18/v18_12F_shadow_research_sell_timing_read_center.py",
    "scripts/v18/v18_12F_R1_stable_snapshot.py",
]

PROTECTED_FILES = [
    "scripts/v18/run_v18_current_official_daily.ps1",
    "scripts/v18/run_v18_12A_R1_stable_snapshot.ps1",
    "scripts/v18/v18_12A_R1_stable_snapshot.py",
    "scripts/v18/run_v18_12B_R1_stable_snapshot.ps1",
    "scripts/v18/v18_12B_R1_stable_snapshot.py",
    "scripts/v18/run_v18_12C_R1_stable_snapshot.ps1",
    "scripts/v18/v18_12C_R1_stable_snapshot.py",
    "scripts/v18/run_v18_12D_R1_stable_snapshot.ps1",
    "scripts/v18/v18_12D_R1_stable_snapshot.py",
    "scripts/v18/run_v18_12E_R1_stable_snapshot.ps1",
    "scripts/v18/v18_12E_R1_stable_snapshot.py",
]

SNAPSHOT_CHECKS = [
    ("V18_12A_R1_STABLE_SNAPSHOT_UNCHANGED", "V18_12A_R1_stable*", "V18_12A_R1_STABLE_MANIFEST.csv"),
    ("V18_12B_R1_STABLE_SNAPSHOT_UNCHANGED", "V18_12B_R1_stable*", "V18_12B_R1_STABLE_MANIFEST.csv"),
    ("V18_12C_R1_STABLE_SNAPSHOT_UNCHANGED", "V18_12C_R1_stable*", "V18_12C_R1_STABLE_MANIFEST.csv"),
    ("V18_12D_R1_STABLE_SNAPSHOT_UNCHANGED", "V18_12D_R1_stable*", "V18_12D_R1_STABLE_MANIFEST.csv"),
    ("V18_12E_R1_STABLE_SNAPSHOT_UNCHANGED", "V18_12E_R1_stable*", "V18_12E_R1_STABLE_MANIFEST.csv"),
]

V18_12F_OUTPUTS = [
    "outputs/v18/sell_timing/V18_12F_READ_FIRST.txt",
    "outputs/v18/sell_timing/V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_READ_CENTER.md",
    "outputs/v18/sell_timing/V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_SUMMARY.csv",
    "outputs/v18/sell_timing/V18_12F_CURRENT_SHADOW_RESEARCH_WITH_SELL_TIMING_INPUT_AUDIT.csv",
]

DISALLOWED_ORDER_TOKENS = [
    "SELL_NOW",
    "LIVE_SELL",
    "AUTO_SELL_NOW",
    "MARKET_SELL",
    "SELL_ORDER",
    "EXECUTE_SELL",
    "PLACE_SELL",
    "IMMEDIATE_LIVE_SELL",
]


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp932", "gbk"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def write_csv(path: Path, rows: List[Dict[str, str]], fields: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rel(base: Path, path: Path) -> str:
    try:
        return str(path.relative_to(base))
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


def read_first_value(path: Path, key: str) -> str:
    lines = [line.strip() for line in read_text(path).splitlines()]
    target = key if key.endswith(":") else f"{key}:"
    for i, line in enumerate(lines):
        if line == target:
            for nxt in lines[i + 1 :]:
                if nxt:
                    return nxt
        if line.startswith(target):
            value = line[len(target) :].strip()
            if value:
                return value
    return ""


def validation_row(check_name: str, status: str, path: Path | str, expected: str, actual: str, note: str = "") -> Dict[str, str]:
    return {
        "check_name": check_name,
        "status": status,
        "path": str(path),
        "expected": expected,
        "actual": actual,
        "note": note,
    }


def manifest_row(root: Path, snapshot: Path, category: str, src: Path, dst: Path, status: str, error: str = "") -> Dict[str, str]:
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
        "source_path": str(src),
        "snapshot_path": str(dst),
        "relative_source_path": rel(root, src),
        "relative_snapshot_path": rel(snapshot, dst),
        "size_bytes": size,
        "last_write_time": modified,
        "sha256": digest,
        "error": error,
    }


def metadata_manifest_row(snapshot: Path, path: Path, category: str) -> Dict[str, str]:
    return manifest_row(snapshot, snapshot, category, path, path, "COPIED")


def copy_critical_file(root: Path, snapshot: Path, category: str, rel_path: str) -> Dict[str, str]:
    src = root / rel_path
    dst = snapshot / rel_path
    if not src.exists() or not src.is_file():
        return manifest_row(root, snapshot, category, src, dst, "MISSING_CRITICAL", "Critical file missing")
    try:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        return manifest_row(root, snapshot, category, src, dst, "COPIED")
    except Exception as exc:
        return manifest_row(root, snapshot, category, src, dst, "COPY_FAIL", f"{type(exc).__name__}: {exc}")


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


def run_v18_12f_fast_mode(root: Path) -> Tuple[bool, str]:
    wrapper = root / "scripts/v18/run_v18_12F_shadow_research_daily_with_sell_timing.ps1"
    try:
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(wrapper),
                "-SkipShadowResearch",
                "-UseExistingShadowResearchOutputs",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = "\n".join(x for x in [proc.stdout.strip(), proc.stderr.strip()] if x)
        return proc.returncode == 0, output[-4000:]
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def stable_snapshot_manifest_hashes(snapshot_root: Path, manifest_name: str) -> Tuple[bool, str, int]:
    manifest_path = snapshot_root / manifest_name
    checked = 0
    if not manifest_path.exists():
        return False, f"Manifest missing: {manifest_path}", checked
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    problems: List[str] = []
    for row in rows:
        if row.get("status") != "COPIED":
            continue
        rel_snapshot_path = str(row.get("relative_snapshot_path", ""))
        if rel_snapshot_path == manifest_name:
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


def all_snapshots_unchanged(root: Path, pattern: str, manifest_name: str) -> Tuple[bool, str, int]:
    checked = 0
    problems: List[str] = []
    matches = list((root / "archive/stable").glob(pattern))
    if not matches:
        return False, f"No snapshots matched pattern: {pattern}", checked
    for snapshot_root in matches:
        ok, note, count = stable_snapshot_manifest_hashes(snapshot_root, manifest_name)
        checked += count
        if not ok:
            problems.append(note)
    if problems:
        return False, "; ".join(problems[:5]), checked
    return True, "", checked


def no_order_tokens_in_outputs(root: Path) -> Tuple[bool, str]:
    hits: List[str] = []
    for rel_path in V18_12F_OUTPUTS:
        path = root / rel_path
        text = read_text(path).upper()
        for token in DISALLOWED_ORDER_TOKENS:
            if token in text:
                hits.append(f"{token}:{path}")
    return len(hits) == 0, "; ".join(hits)


def build_restore_script(snapshot: Path) -> str:
    files = [rel_path.replace("/", "\\") for _, rel_path in SNAPSHOT_FILES]
    file_lines = "\n".join(f'    "{path}"' for path in files)
    return f'''param(
    [string]$Root = "D:\\us-tech-quant",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$Snapshot = "{snapshot}"

Write-Host ""
Write-Host "=== V18.12F-R1 STABLE SNAPSHOT RESTORE ==="
Write-Host "SNAPSHOT: $Snapshot"
Write-Host "ROOT: $Root"
Write-Host "APPLY: $Apply"
Write-Host "NOTE: Restore covers only V18.12F shadow research sell timing integration files and outputs."

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
    Write-Host "DRYRUN_ONLY. Re-run with -Apply to restore."
}}
else {{
    Write-Host "RESTORE_APPLIED."
}}
'''


def build_readme(snapshot: Path, manifest_path: Path, validation_path: Path, restore_path: Path) -> str:
    return f"""V18.12F-R1 STABLE SNAPSHOT README

Created:
{now_text()}

Snapshot:
{snapshot}

Purpose:
Stable restore point for V18.12F Shadow Research Daily With Sell Timing Integration after fast safe mode was added.

Scope:
Copies the V18.12F wrapper, V18.12F read center, READ_FIRST, read center Markdown, summary CSV, and input audit CSV.

Safety:
MODE={MODE}
SHADOW_ONLY={SHADOW_ONLY}
OFFICIAL_DECISION_IMPACT={OFFICIAL_DECISION_IMPACT}
AUTO_SELL={AUTO_SELL}
AUTO_TRADE={AUTO_TRADE}
SHADOW_RESEARCH_STATUS={EXPECTED_SHADOW_STATUS}
SELL_TIMING_STATUS={EXPECTED_SELL_TIMING_STATUS}

Restore:
The restore script is generated but not executed by snapshot creation. It restores only V18.12F files and generated V18.12F outputs.

Files:
MANIFEST={manifest_path}
VALIDATION_CHECKS={validation_path}
RESTORE_SCRIPT={restore_path}
"""


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"D:\us-tech-quant")
    stamp = now_stamp()
    snapshot = root / "archive/stable" / f"V18_12F_R1_stable_shadow_research_daily_with_sell_timing_fast_safe_{stamp}"
    out_dir = root / "outputs/v18/ops"
    ensure_dir(snapshot)
    ensure_dir(out_dir)

    protected_before = {rel_path: sha256(root / rel_path) for rel_path in PROTECTED_FILES}

    manifest_path = snapshot / "V18_12F_R1_STABLE_MANIFEST.csv"
    validation_path = snapshot / "V18_12F_R1_STABLE_VALIDATION_CHECKS.csv"
    readme_path = snapshot / "V18_12F_R1_STABLE_SNAPSHOT_README.txt"
    restore_path = snapshot / "restore_v18_12F_R1_stable_snapshot.ps1"
    report_path = out_dir / "V18_12F_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    read_first_path = out_dir / "V18_12F_R1_READ_FIRST.txt"
    f_read_first = root / "outputs/v18/sell_timing/V18_12F_READ_FIRST.txt"

    validations: List[Dict[str, str]] = []
    wrapper_ok, wrapper_output = run_v18_12f_fast_mode(root)
    validations.append(validation_row("RUN_V18_12F_FAST_SAFE_MODE", "PASS" if wrapper_ok else "FAIL", root / "scripts/v18/run_v18_12F_shadow_research_daily_with_sell_timing.ps1", "exit_0", "exit_0" if wrapper_ok else "nonzero", wrapper_output))

    for rel_path in PS_PARSE_FILES:
        path = root / rel_path
        ok, err = parse_check_ps1(path)
        validations.append(validation_row(f"POWERSHELL_PARSE_{Path(rel_path).name}", "PASS" if ok else "FAIL", path, "parse_ok", "parse_ok" if ok else "parse_fail", err))

    for rel_path in PY_COMPILE_FILES:
        path = root / rel_path
        ok, err = compile_check_py(path)
        validations.append(validation_row(f"PY_COMPILE_{Path(rel_path).name}", "PASS" if ok else "FAIL", path, "compile_ok", "compile_ok" if ok else "compile_fail", err))

    read_first_expectations = [
        ("STATUS", STATUS_OK),
        ("SHADOW_RESEARCH_STATUS", EXPECTED_SHADOW_STATUS),
        ("SELL_TIMING_STATUS", EXPECTED_SELL_TIMING_STATUS),
        ("OFFICIAL_DECISION_IMPACT", OFFICIAL_DECISION_IMPACT),
        ("AUTO_SELL", AUTO_SELL),
        ("AUTO_TRADE", AUTO_TRADE),
    ]

    f_values: Dict[str, str] = {}
    expected_read_first_status = "OK_V18_12F_SHADOW_RESEARCH_DAILY_WITH_SELL_TIMING_READY"
    for key, expected in read_first_expectations:
        compare_expected = expected_read_first_status if key == "STATUS" else expected
        actual = read_first_value(f_read_first, key)
        f_values[key] = actual
        validations.append(validation_row(f"V18_12F_{key}", "PASS" if actual == compare_expected else "FAIL", f_read_first, compare_expected, actual))

    no_token_ok, token_note = no_order_tokens_in_outputs(root)
    validations.append(validation_row("NO_ORDER_TOKEN_IN_V18_12F_OUTPUTS", "PASS" if no_token_ok else "FAIL", "outputs/v18/sell_timing/V18_12F*", "no immediate live sell tokens", "clean" if no_token_ok else "found", token_note))

    manifest_rows: List[Dict[str, str]] = []
    for category, rel_path in SNAPSHOT_FILES:
        manifest_rows.append(copy_critical_file(root, snapshot, category, rel_path))

    for _, rel_path in SNAPSHOT_FILES:
        copied = snapshot / rel_path
        ok = copied.exists() and copied.is_file()
        validations.append(validation_row(f"CRITICAL_FILE_COPIED_{Path(rel_path).name}", "PASS" if ok else "FAIL", copied, "exists", "exists" if ok else "missing"))

    protected_after = {rel_path: sha256(root / rel_path) for rel_path in PROTECTED_FILES}
    for rel_path in PROTECTED_FILES:
        ok = bool(protected_before[rel_path]) and protected_before[rel_path] == protected_after[rel_path]
        validations.append(validation_row(f"PROTECTED_UNCHANGED_{Path(rel_path).name}", "PASS" if ok else "FAIL", root / rel_path, protected_before[rel_path], protected_after[rel_path]))

    for check_name, pattern, manifest_name in SNAPSHOT_CHECKS:
        ok, note, checked = all_snapshots_unchanged(root, pattern, manifest_name)
        validations.append(validation_row(check_name, "PASS" if ok else "FAIL", root / "archive/stable", "manifest_hashes_match", f"checked={checked}" if ok else "mismatch", note))

    restore_path.write_text(build_restore_script(snapshot), encoding="utf-8")
    readme_path.write_text(build_readme(snapshot, manifest_path, validation_path, restore_path), encoding="utf-8")
    manifest_rows.append(metadata_manifest_row(snapshot, restore_path, "snapshot_metadata"))
    manifest_rows.append(metadata_manifest_row(snapshot, readme_path, "snapshot_metadata"))

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

    write_csv(validation_path, validations, validation_fields)
    manifest_rows.append(metadata_manifest_row(snapshot, validation_path, "snapshot_metadata"))
    write_csv(manifest_path, manifest_rows, manifest_fields)
    manifest_rows.append(metadata_manifest_row(snapshot, manifest_path, "snapshot_metadata"))
    write_csv(manifest_path, manifest_rows, manifest_fields)

    copied_file_count = sum(1 for row in manifest_rows if row["status"] == "COPIED")
    copy_fail_count = sum(1 for row in manifest_rows if row["status"] == "COPY_FAIL")
    missing_critical_count = sum(1 for row in manifest_rows if row["status"] == "MISSING_CRITICAL")
    validation_fail_count = sum(1 for row in validations if row["status"] != "PASS")
    fail_count = copy_fail_count + missing_critical_count + validation_fail_count
    status = STATUS_OK if fail_count == 0 else STATUS_WARN

    report = f"""# V18.12F-R1 Stable Snapshot

- STATUS: `{status}`
- MODE: `{MODE}`
- SNAPSHOT_PATH: `{snapshot}`
- COPIED_FILE_COUNT: `{copied_file_count}`
- COPY_FAIL_COUNT: `{copy_fail_count}`
- MISSING_CRITICAL_COUNT: `{missing_critical_count}`
- VALIDATION_FAIL_COUNT: `{validation_fail_count}`
- SHADOW_RESEARCH_STATUS: `{f_values.get('SHADOW_RESEARCH_STATUS', '')}`
- SELL_TIMING_STATUS: `{f_values.get('SELL_TIMING_STATUS', '')}`
- OFFICIAL_DECISION_IMPACT: `{OFFICIAL_DECISION_IMPACT}`
- AUTO_SELL: `{AUTO_SELL}`
- AUTO_TRADE: `{AUTO_TRADE}`
- SHADOW_ONLY: `{SHADOW_ONLY}`

## Snapshot Scope

The snapshot contains only V18.12F shadow research sell timing integration files, generated V18.12F outputs, README, manifest, validation checks, and restore tooling.

## Files

- MANIFEST: `{manifest_path}`
- VALIDATION_CHECKS: `{validation_path}`
- RESTORE_SCRIPT: `{restore_path}`
- README: `{readme_path}`

## Validation

The V18.12F wrapper was run in fast safe mode before copying. PowerShell parse checks, Python compile checks, critical file copy checks, protected-file hash checks, V18.12A/B/C/D/E stable snapshot manifest hash checks, and generated output token checks were recorded.
"""
    report_path.write_text(report, encoding="utf-8")

    read_first_out = f"""V18.12F-R1 STABLE SNAPSHOT READ FIRST

STATUS:
{status}

MODE:
{MODE}

SNAPSHOT_PATH:
{snapshot}

SHADOW_RESEARCH_STATUS:
{f_values.get('SHADOW_RESEARCH_STATUS', '')}

SELL_TIMING_STATUS:
{f_values.get('SELL_TIMING_STATUS', '')}

COPIED_FILE_COUNT:
{copied_file_count}

COPY_FAIL_COUNT:
{copy_fail_count}

MISSING_CRITICAL_COUNT:
{missing_critical_count}

VALIDATION_FAIL_COUNT:
{validation_fail_count}

OFFICIAL_DECISION_IMPACT:
{OFFICIAL_DECISION_IMPACT}

AUTO_SELL:
{AUTO_SELL}

AUTO_TRADE:
{AUTO_TRADE}

SHADOW_ONLY:
{SHADOW_ONLY}

MANIFEST:
{manifest_path}

VALIDATION_CHECKS:
{validation_path}

RESTORE_SCRIPT:
{restore_path}

REPORT:
{report_path}
"""
    read_first_path.write_text(read_first_out, encoding="utf-8")

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"SNAPSHOT_PATH: {snapshot}")
    print(f"SHADOW_RESEARCH_STATUS: {f_values.get('SHADOW_RESEARCH_STATUS', '')}")
    print(f"SELL_TIMING_STATUS: {f_values.get('SELL_TIMING_STATUS', '')}")
    print(f"COPIED_FILE_COUNT: {copied_file_count}")
    print(f"COPY_FAIL_COUNT: {copy_fail_count}")
    print(f"MISSING_CRITICAL_COUNT: {missing_critical_count}")
    print(f"VALIDATION_FAIL_COUNT: {validation_fail_count}")
    print(f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}")
    print(f"AUTO_SELL: {AUTO_SELL}")
    print(f"AUTO_TRADE: {AUTO_TRADE}")
    print(f"SHADOW_ONLY: {SHADOW_ONLY}")
    print(f"MANIFEST: {manifest_path}")
    print(f"VALIDATION_CHECKS: {validation_path}")
    print(f"RESTORE_SCRIPT: {restore_path}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first_path}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
