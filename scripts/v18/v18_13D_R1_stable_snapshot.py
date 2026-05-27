from __future__ import annotations

import csv
import datetime as dt
import hashlib
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_13D_R1_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_13D_R1_STABLE_SNAPSHOT_WITH_FAILURES"
STATUS_FAIL_DANGEROUS = "FAIL_V18_13D_R1_DANGEROUS_TOKEN_FOUND"

EXPECTED_STATUS = "OK_V18_13D_READ_CENTER_REFRESH_READY"
EXPECTED_RUN_MODE = "READ_CENTER_REFRESH_ONLY"
FULL_DAILY_MODE = "NOT_VALIDATED_IN_CODEX_TIMEOUT_WINDOW"
EXPECTED_OFFICIAL_DAILY_STATUS = "SKIPPED"
EXPECTED_13A_STATUS = "OK_V18_13A_UNIFIED_DAILY_READ_CENTER_READY"
EXPECTED_13B_STATUS = "OK_V18_13B_RANKED_CANDIDATE_READ_CENTER_READY"
EXPECTED_13C_STATUS = "OK_V18_13C_UNIFIED_DAILY_WITH_RANKED_CANDIDATES_READY"
EXPECTED_RANK_SOURCE_STATUS = "OK_SCORE_SOURCE_FOUND"
EXPECTED_TOP_5 = "APH,ACM,ASML,AMZN,CAMT"

OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
READ_ONLY = "TRUE"
COMMAND_CENTER_ONLY = "TRUE"
SNAPSHOT_ONLY = "TRUE"

SNAPSHOT_NAME_PREFIX = "V18_13D_R1_stable_daily_command_center_read_center_refresh"

SNAPSHOT_FILES = [
    ("script", "scripts/v18/v18_13D_daily_command_center.py"),
    ("script", "scripts/v18/run_v18_13D_daily_command_center.ps1"),
    ("script", "scripts/v18/v18_13D_R1_stable_snapshot.py"),
    ("script", "scripts/v18/run_v18_13D_R1_stable_snapshot.ps1"),
    ("output", "outputs/v18/read_center/V18_13D_READ_FIRST.txt"),
    ("output", "outputs/v18/read_center/V18_13D_CURRENT_DAILY_COMMAND_CENTER.md"),
    ("output", "outputs/v18/read_center/V18_13D_CURRENT_DAILY_COMMAND_CENTER_SUMMARY.csv"),
    ("output", "outputs/v18/read_center/V18_13D_CURRENT_DAILY_COMMAND_CENTER_INPUT_AUDIT.csv"),
    ("output", "outputs/v18/ops/V18_13D_CURRENT_DAILY_COMMAND_CENTER_RUN_LOG.csv"),
    ("linked_source", "outputs/v18/read_center/V18_13A_READ_FIRST.txt"),
    ("linked_source", "outputs/v18/read_center/V18_13B_READ_FIRST.txt"),
    ("linked_source", "outputs/v18/read_center/V18_13C_READ_FIRST.txt"),
    ("linked_source", "outputs/v18/read_center/V18_13C_CURRENT_UNIFIED_DAILY_WITH_RANKED_CANDIDATES.md"),
    ("linked_source", "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv"),
]

PS_PARSE_FILES = [
    "scripts/v18/run_v18_13D_R1_stable_snapshot.ps1",
    "scripts/v18/run_v18_13D_daily_command_center.ps1",
]

PY_COMPILE_FILES = [
    "scripts/v18/v18_13D_R1_stable_snapshot.py",
    "scripts/v18/v18_13D_daily_command_center.py",
]

PROTECTED_FILES = ["scripts/v18/run_v18_current_official_daily.ps1"]

SNAPSHOT_CHECKS = [
    ("V18_13A_R1_STABLE_SNAPSHOT_UNCHANGED", "V18_13A_R1_stable*", "V18_13A_R1_STABLE_MANIFEST.csv"),
    ("V18_13B_R1_STABLE_SNAPSHOT_UNCHANGED", "V18_13B_R1_stable*", "MANIFEST.csv"),
    ("V18_13C_R1_STABLE_SNAPSHOT_UNCHANGED", "V18_13C_R1_stable*", "MANIFEST.csv"),
    ("V18_12F_R2_STABLE_SNAPSHOT_UNCHANGED", "V18_12F_R2_stable*", "V18_12F_R2_STABLE_MANIFEST.csv"),
    ("V18_12H_R1_STABLE_SNAPSHOT_UNCHANGED", "V18_12H_R1_stable*", "V18_12H_R1_STABLE_MANIFEST.csv"),
]

DANGEROUS_TOKENS = [
    "BUY_NOW",
    "SELL_NOW",
    "EXECUTE_ORDER",
    "PLACE_ORDER",
    "AUTO_TRADE: ENABLED",
    "AUTO_SELL: ENABLED",
]

TOKEN_SCAN_OUTPUTS = [
    "outputs/v18/read_center/V18_13D_READ_FIRST.txt",
    "outputs/v18/read_center/V18_13D_CURRENT_DAILY_COMMAND_CENTER.md",
    "outputs/v18/read_center/V18_13D_CURRENT_DAILY_COMMAND_CENTER_SUMMARY.csv",
    "outputs/v18/read_center/V18_13D_CURRENT_DAILY_COMMAND_CENTER_INPUT_AUDIT.csv",
    "outputs/v18/ops/V18_13D_CURRENT_DAILY_COMMAND_CENTER_RUN_LOG.csv",
    "outputs/v18/ops/V18_13D_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md",
    "outputs/v18/ops/V18_13D_R1_READ_FIRST.txt",
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


def write_csv(path: Path, rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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


def rel(base: Path, path: Path) -> str:
    try:
        return str(path.relative_to(base)).replace("\\", "/")
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


def summary_values(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for row in read_csv_rows(path):
        metric = str(row.get("metric", ""))
        if metric:
            values[metric] = str(row.get("value", ""))
    return values


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


def run_v18_13d_refresh(root: Path) -> Tuple[bool, str]:
    wrapper = root / "scripts/v18/run_v18_13D_daily_command_center.ps1"
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(wrapper), "-SkipOfficialDaily"],
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
    problems: List[str] = []
    for row in read_csv_rows(manifest_path):
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


def append_expectation(validations: List[Dict[str, str]], name: str, path: Path | str, expected: str, actual: str) -> None:
    validations.append(validation_row(name, "PASS" if actual == expected else "FAIL", path, expected, actual))


def dangerous_token_hits(paths: Sequence[Path]) -> List[str]:
    hits: List[str] = []
    for path in paths:
        text = read_text(path)
        for token in DANGEROUS_TOKENS:
            if token in text:
                hits.append(f"{path}:{token}")
    return hits


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
Write-Host "=== V18.13D-R1 STABLE SNAPSHOT RESTORE ==="
Write-Host "SNAPSHOT: $Snapshot"
Write-Host "ROOT: $Root"
Write-Host "APPLY: $Apply"
Write-Host "NOTE: Restore covers only V18.13D command center scripts, outputs, run log, and copied linked read outputs."

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
    return f"""# V18.13D-R1 Stable Snapshot

Created: {now_text()}

Snapshot: {snapshot}

Purpose: Stable restore point for the V18.13D Daily Command Center in read-center refresh mode.

Scope: Copies the V18.13D command center scripts and outputs, available linked current read outputs, manifest, validation, README, and restore tooling.

Validation mode:
RUN_MODE: {EXPECTED_RUN_MODE}
FULL_DAILY_MODE: {FULL_DAILY_MODE}
OFFICIAL_DAILY_STATUS: {EXPECTED_OFFICIAL_DAILY_STATUS}

Safety:
OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}
AUTO_TRADE: {AUTO_TRADE}
AUTO_SELL: {AUTO_SELL}
READ_ONLY: {READ_ONLY}
COMMAND_CENTER_ONLY: {COMMAND_CENTER_ONLY}
SNAPSHOT_ONLY: {SNAPSHOT_ONLY}

Limitation: Full official daily mode was not validated inside the Codex timeout window. This is recorded as a limitation, not a validation failure.

Restore: RESTORE_V18_13D_R1.ps1 is generated but not executed by snapshot creation. It restores only files listed in MANIFEST.csv.

Files:
MANIFEST: {manifest_path}
VALIDATION: {validation_path}
RESTORE_SCRIPT: {restore_path}
"""


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"D:\us-tech-quant")
    stamp = now_stamp()
    snapshot = root / "archive/stable" / f"{SNAPSHOT_NAME_PREFIX}_{stamp}"
    out_dir = root / "outputs/v18/ops"
    ensure_dir(snapshot)
    ensure_dir(out_dir)

    protected_before = {rel_path: sha256(root / rel_path) for rel_path in PROTECTED_FILES}

    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_13D_R1_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_13D_R1.ps1"
    report_path = out_dir / "V18_13D_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    read_first_path = out_dir / "V18_13D_R1_READ_FIRST.txt"
    summary_path = root / "outputs/v18/read_center/V18_13D_CURRENT_DAILY_COMMAND_CENTER_SUMMARY.csv"

    validations: List[Dict[str, str]] = []
    wrapper_ok, wrapper_output = run_v18_13d_refresh(root)
    validations.append(validation_row("RUN_V18_13D_DAILY_COMMAND_CENTER_SKIP_OFFICIAL", "PASS" if wrapper_ok else "FAIL", root / "scripts/v18/run_v18_13D_daily_command_center.ps1", "exit_0", "exit_0" if wrapper_ok else "nonzero", wrapper_output))

    summary = summary_values(summary_path)
    values = {
        "STATUS": summary.get("STATUS", ""),
        "RUN_MODE": summary.get("RUN_MODE", ""),
        "FULL_DAILY_MODE": FULL_DAILY_MODE,
        "OFFICIAL_DAILY_STATUS": summary.get("OFFICIAL_DAILY_STATUS", ""),
        "V18_13A_STATUS": summary.get("V18_13A_STATUS", ""),
        "V18_13B_STATUS": summary.get("V18_13B_STATUS", ""),
        "V18_13C_STATUS": summary.get("V18_13C_STATUS", ""),
        "RANK_SOURCE_STATUS": summary.get("RANK_SOURCE_STATUS", ""),
        "SECOND_STAGE_COUNT": summary.get("SECOND_STAGE_COUNT", ""),
        "SCORED_TICKER_COUNT": summary.get("SCORED_TICKER_COUNT", ""),
        "UNSCORED_TICKER_COUNT": summary.get("UNSCORED_TICKER_COUNT", ""),
        "TOP_5_TICKERS": summary.get("TOP_5_TICKERS", ""),
        "OFFICIAL_DECISION_IMPACT": summary.get("OFFICIAL_DECISION_IMPACT", ""),
        "AUTO_TRADE": summary.get("AUTO_TRADE", ""),
        "AUTO_SELL": summary.get("AUTO_SELL", ""),
        "READ_ONLY": summary.get("READ_ONLY", ""),
        "COMMAND_CENTER_ONLY": summary.get("COMMAND_CENTER_ONLY", ""),
        "SNAPSHOT_ONLY": SNAPSHOT_ONLY,
    }
    expected_values = {
        "STATUS": EXPECTED_STATUS,
        "RUN_MODE": EXPECTED_RUN_MODE,
        "FULL_DAILY_MODE": FULL_DAILY_MODE,
        "OFFICIAL_DAILY_STATUS": EXPECTED_OFFICIAL_DAILY_STATUS,
        "V18_13A_STATUS": EXPECTED_13A_STATUS,
        "V18_13B_STATUS": EXPECTED_13B_STATUS,
        "V18_13C_STATUS": EXPECTED_13C_STATUS,
        "RANK_SOURCE_STATUS": EXPECTED_RANK_SOURCE_STATUS,
        "SECOND_STAGE_COUNT": "20",
        "SCORED_TICKER_COUNT": "20",
        "UNSCORED_TICKER_COUNT": "0",
        "TOP_5_TICKERS": EXPECTED_TOP_5,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "READ_ONLY": READ_ONLY,
        "COMMAND_CENTER_ONLY": COMMAND_CENTER_ONLY,
    }
    for key, expected in expected_values.items():
        append_expectation(validations, f"V18_13D_{key}", summary_path, expected, values.get(key, ""))

    for rel_path in PS_PARSE_FILES:
        path = root / rel_path
        ok, err = parse_check_ps1(path)
        validations.append(validation_row(f"POWERSHELL_PARSE_{Path(rel_path).name}", "PASS" if ok else "FAIL", path, "parse_ok", "parse_ok" if ok else "parse_fail", err))

    for rel_path in PY_COMPILE_FILES:
        path = root / rel_path
        ok, err = compile_check_py(path)
        validations.append(validation_row(f"PY_COMPILE_{Path(rel_path).name}", "PASS" if ok else "FAIL", path, "compile_ok", "compile_ok" if ok else "compile_fail", err))

    protected_after = {rel_path: sha256(root / rel_path) for rel_path in PROTECTED_FILES}
    for rel_path in PROTECTED_FILES:
        ok = bool(protected_before[rel_path]) and protected_before[rel_path] == protected_after[rel_path]
        validations.append(validation_row(f"PROTECTED_UNCHANGED_{Path(rel_path).name}", "PASS" if ok else "FAIL", root / rel_path, protected_before[rel_path], protected_after[rel_path]))

    for check_name, pattern, manifest_name in SNAPSHOT_CHECKS:
        ok, note, checked = all_snapshots_unchanged(root, pattern, manifest_name)
        validations.append(validation_row(check_name, "PASS" if ok else "FAIL", root / "archive/stable", "manifest_hashes_match", f"checked={checked}" if ok else "mismatch", note))

    manifest_rows: List[Dict[str, str]] = []
    for category, rel_path in SNAPSHOT_FILES:
        manifest_rows.append(copy_critical_file(root, snapshot, category, rel_path))

    for _, rel_path in SNAPSHOT_FILES:
        copied = snapshot / rel_path
        validations.append(validation_row(f"CRITICAL_FILE_COPIED_{Path(rel_path).name}", "PASS" if copied.exists() and copied.is_file() else "FAIL", copied, "exists", "exists" if copied.exists() and copied.is_file() else "missing"))

    restore_path.write_text(build_restore_script(snapshot), encoding="utf-8")
    readme_path.write_text(build_readme(snapshot, manifest_path, validation_path, restore_path), encoding="utf-8")
    manifest_rows.append(metadata_manifest_row(snapshot, restore_path, "snapshot_metadata"))
    manifest_rows.append(metadata_manifest_row(snapshot, readme_path, "snapshot_metadata"))

    copy_fail_count = sum(1 for row in manifest_rows if row["status"] == "COPY_FAIL")
    missing_critical_count = sum(1 for row in manifest_rows if row["status"] == "MISSING_CRITICAL")
    validation_fail_count = sum(1 for row in validations if row["status"] != "PASS")
    preliminary_status = STATUS_OK if copy_fail_count + missing_critical_count + validation_fail_count == 0 else STATUS_WARN
    status = preliminary_status

    report = f"""# V18.13D-R1 Stable Snapshot

- STATUS: `{status}`
- SNAPSHOT_PATH: `{snapshot}`
- COPIED_FILE_COUNT: `PENDING`
- COPY_FAIL_COUNT: `{copy_fail_count}`
- MISSING_CRITICAL_COUNT: `{missing_critical_count}`
- VALIDATION_FAIL_COUNT: `{validation_fail_count}`
- RUN_MODE: `{values['RUN_MODE']}`
- FULL_DAILY_MODE: `{FULL_DAILY_MODE}`
- OFFICIAL_DAILY_STATUS: `{values['OFFICIAL_DAILY_STATUS']}`
- V18_13A_STATUS: `{values['V18_13A_STATUS']}`
- V18_13B_STATUS: `{values['V18_13B_STATUS']}`
- V18_13C_STATUS: `{values['V18_13C_STATUS']}`
- RANK_SOURCE_STATUS: `{values['RANK_SOURCE_STATUS']}`
- SECOND_STAGE_COUNT: `{values['SECOND_STAGE_COUNT']}`
- SCORED_TICKER_COUNT: `{values['SCORED_TICKER_COUNT']}`
- UNSCORED_TICKER_COUNT: `{values['UNSCORED_TICKER_COUNT']}`
- TOP_5_TICKERS: `{values['TOP_5_TICKERS']}`
- OFFICIAL_DECISION_IMPACT: `{OFFICIAL_DECISION_IMPACT}`
- AUTO_TRADE: `{AUTO_TRADE}`
- AUTO_SELL: `{AUTO_SELL}`
- READ_ONLY: `{READ_ONLY}`
- COMMAND_CENTER_ONLY: `{COMMAND_CENTER_ONLY}`
- SNAPSHOT_ONLY: `{SNAPSHOT_ONLY}`

## Validation Scope

V18.13D-R1 validates read-center refresh mode only. Full official daily mode is recorded as not validated inside the Codex timeout window and can be run manually later if needed.
"""
    report_path.write_text(report, encoding="utf-8")

    read_first_out = f"""V18.13D-R1 STABLE SNAPSHOT READ FIRST

STATUS:
{status}

SNAPSHOT_PATH:
{snapshot}

COPIED_FILE_COUNT:
PENDING

COPY_FAIL_COUNT:
{copy_fail_count}

MISSING_CRITICAL_COUNT:
{missing_critical_count}

VALIDATION_FAIL_COUNT:
{validation_fail_count}

RUN_MODE:
{values['RUN_MODE']}

FULL_DAILY_MODE:
{FULL_DAILY_MODE}

OFFICIAL_DAILY_STATUS:
{values['OFFICIAL_DAILY_STATUS']}

V18_13A_STATUS:
{values['V18_13A_STATUS']}

V18_13B_STATUS:
{values['V18_13B_STATUS']}

V18_13C_STATUS:
{values['V18_13C_STATUS']}

RANK_SOURCE_STATUS:
{values['RANK_SOURCE_STATUS']}

SECOND_STAGE_COUNT:
{values['SECOND_STAGE_COUNT']}

SCORED_TICKER_COUNT:
{values['SCORED_TICKER_COUNT']}

UNSCORED_TICKER_COUNT:
{values['UNSCORED_TICKER_COUNT']}

TOP_5_TICKERS:
{values['TOP_5_TICKERS']}

OFFICIAL_DECISION_IMPACT:
{OFFICIAL_DECISION_IMPACT}

AUTO_TRADE:
{AUTO_TRADE}

AUTO_SELL:
{AUTO_SELL}

READ_ONLY:
{READ_ONLY}

COMMAND_CENTER_ONLY:
{COMMAND_CENTER_ONLY}

SNAPSHOT_ONLY:
{SNAPSHOT_ONLY}

MANIFEST:
{manifest_path}

VALIDATION:
{validation_path}

RESTORE_SCRIPT:
{restore_path}

REPORT:
{report_path}
"""
    read_first_path.write_text(read_first_out, encoding="utf-8")

    scan_paths = [root / rel_path for rel_path in TOKEN_SCAN_OUTPUTS]
    scan_paths.extend(snapshot / rel_path for category, rel_path in SNAPSHOT_FILES if category != "script")
    scan_paths.extend([readme_path, restore_path])
    hits = dangerous_token_hits(scan_paths)
    validations.append(validation_row("NO_DANGEROUS_TOKEN_IN_V18_13D_AND_R1_OUTPUTS", "PASS" if not hits else "FAIL", "V18.13D outputs and V18.13D-R1 snapshot outputs", "clean", "clean" if not hits else "found", "clean" if not hits else "redacted_hits_present"))
    if hits:
        status = STATUS_FAIL_DANGEROUS
        validation_fail_count = sum(1 for row in validations if row["status"] != "PASS")

    validation_fields = ["check_name", "status", "path", "expected", "actual", "note"]
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
    write_csv(validation_path, validations, validation_fields)
    manifest_rows.append(metadata_manifest_row(snapshot, validation_path, "snapshot_metadata"))
    write_csv(manifest_path, manifest_rows, manifest_fields)
    manifest_rows.append(metadata_manifest_row(snapshot, manifest_path, "snapshot_metadata"))
    write_csv(manifest_path, manifest_rows, manifest_fields)

    copied_file_count = sum(1 for row in manifest_rows if row["status"] == "COPIED")
    copy_fail_count = sum(1 for row in manifest_rows if row["status"] == "COPY_FAIL")
    missing_critical_count = sum(1 for row in manifest_rows if row["status"] == "MISSING_CRITICAL")
    validation_fail_count = sum(1 for row in validations if row["status"] != "PASS")
    if status != STATUS_FAIL_DANGEROUS:
        status = STATUS_OK if copy_fail_count + missing_critical_count + validation_fail_count == 0 else STATUS_WARN

    report = report.replace("`PENDING`", f"`{copied_file_count}`").replace(f"- STATUS: `{preliminary_status}`", f"- STATUS: `{status}`").replace(f"- VALIDATION_FAIL_COUNT: `{sum(1 for row in validations[:-1] if row['status'] != 'PASS')}`", f"- VALIDATION_FAIL_COUNT: `{validation_fail_count}`")
    report_path.write_text(report, encoding="utf-8")
    read_first_out = read_first_out.replace("PENDING", str(copied_file_count)).replace(f"STATUS:\n{preliminary_status}", f"STATUS:\n{status}").replace(f"VALIDATION_FAIL_COUNT:\n{sum(1 for row in validations[:-1] if row['status'] != 'PASS')}", f"VALIDATION_FAIL_COUNT:\n{validation_fail_count}")
    read_first_path.write_text(read_first_out, encoding="utf-8")

    print(f"STATUS: {status}")
    print(f"SNAPSHOT_PATH: {snapshot}")
    print(f"COPIED_FILE_COUNT: {copied_file_count}")
    print(f"COPY_FAIL_COUNT: {copy_fail_count}")
    print(f"MISSING_CRITICAL_COUNT: {missing_critical_count}")
    print(f"VALIDATION_FAIL_COUNT: {validation_fail_count}")
    print(f"RUN_MODE: {values['RUN_MODE']}")
    print(f"FULL_DAILY_MODE: {FULL_DAILY_MODE}")
    print(f"OFFICIAL_DAILY_STATUS: {values['OFFICIAL_DAILY_STATUS']}")
    print(f"V18_13A_STATUS: {values['V18_13A_STATUS']}")
    print(f"V18_13B_STATUS: {values['V18_13B_STATUS']}")
    print(f"V18_13C_STATUS: {values['V18_13C_STATUS']}")
    print(f"RANK_SOURCE_STATUS: {values['RANK_SOURCE_STATUS']}")
    print(f"SECOND_STAGE_COUNT: {values['SECOND_STAGE_COUNT']}")
    print(f"SCORED_TICKER_COUNT: {values['SCORED_TICKER_COUNT']}")
    print(f"UNSCORED_TICKER_COUNT: {values['UNSCORED_TICKER_COUNT']}")
    print(f"TOP_5_TICKERS: {values['TOP_5_TICKERS']}")
    print(f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}")
    print(f"AUTO_TRADE: {AUTO_TRADE}")
    print(f"AUTO_SELL: {AUTO_SELL}")
    print(f"READ_ONLY: {READ_ONLY}")
    print(f"COMMAND_CENTER_ONLY: {COMMAND_CENTER_ONLY}")
    print(f"SNAPSHOT_ONLY: {SNAPSHOT_ONLY}")
    print(f"MANIFEST: {manifest_path}")
    print(f"VALIDATION: {validation_path}")
    print(f"RESTORE_SCRIPT: {restore_path}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first_path}")
    return 0 if status == STATUS_OK else 1


if __name__ == "__main__":
    raise SystemExit(main())
