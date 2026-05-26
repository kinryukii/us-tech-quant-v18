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


STATUS_OK = "OK_V18_13B_R1_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_13B_R1_STABLE_SNAPSHOT_WITH_FAILURES"
STATUS_FAIL_DANGEROUS = "FAIL_V18_13B_R1_DANGEROUS_TOKEN_FOUND"
EXPECTED_13B_STATUS = "OK_V18_13B_RANKED_CANDIDATE_READ_CENTER_READY"
EXPECTED_RANK_SOURCE_STATUS = "OK_SCORE_SOURCE_FOUND"
OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
READ_ONLY = "TRUE"
SNAPSHOT_ONLY = "TRUE"
RANKING_SOURCE_POLICY = "PRIMARY_CURRENT_ONLY"
FALLBACK_USED = "FALSE"

SNAPSHOT_NAME_PREFIX = "V18_13B_R1_stable_ranked_candidate_read_center_source_dedup"

PRIMARY_SCORE_SOURCE_FILES = [
    "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
]

AUDIT_ONLY_SOURCE_FILES = [
    "outputs/v18/factor_pack/V18_3D_R2_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    "outputs/v18/factor_pack/V18_3D_R2_CURRENT_RAW105_FACTOR_PACK_VALUES.csv",
    "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_VALUES.csv",
    "outputs/v18/technical_timing_backtest/V18_6B_CURRENT_TECHNICAL_TIMING_BACKTEST_DETAIL.csv",
    "outputs/v18/technical_timing_backtest/V18_6B_R1_CURRENT_TECHNICAL_TIMING_DIAGNOSTIC_DETAIL.csv",
]

SNAPSHOT_FILES = [
    ("script", "scripts/v18/v18_13B_ranked_candidate_read_center.py"),
    ("script", "scripts/v18/run_v18_13B_ranked_candidate_read_center.ps1"),
    ("script", "scripts/v18/v18_13B_R1_stable_snapshot.py"),
    ("script", "scripts/v18/run_v18_13B_R1_stable_snapshot.ps1"),
    ("output", "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv"),
    ("output", "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES_INPUT_AUDIT.csv"),
    ("output", "outputs/v18/read_center/V18_13B_CURRENT_RANKED_CANDIDATE_READ_CENTER.md"),
    ("output", "outputs/v18/read_center/V18_13B_READ_FIRST.txt"),
    ("output", "outputs/v18/read_center/V18_13B_CURRENT_RANKED_CANDIDATE_SUMMARY.csv"),
]

PS_PARSE_FILES = [
    "scripts/v18/run_v18_13B_ranked_candidate_read_center.ps1",
    "scripts/v18/run_v18_13B_R1_stable_snapshot.ps1",
]

PY_COMPILE_FILES = [
    "scripts/v18/v18_13B_ranked_candidate_read_center.py",
    "scripts/v18/v18_13B_R1_stable_snapshot.py",
]

PROTECTED_FILES = ["scripts/v18/run_v18_current_official_daily.ps1"]

SNAPSHOT_CHECKS = [
    ("V18_12F_R2_STABLE_SNAPSHOT_UNCHANGED", "V18_12F_R2_stable*", "V18_12F_R2_STABLE_MANIFEST.csv"),
    ("V18_12H_R1_STABLE_SNAPSHOT_UNCHANGED", "V18_12H_R1_stable*", "V18_12H_R1_STABLE_MANIFEST.csv"),
    ("V18_13A_R1_STABLE_SNAPSHOT_UNCHANGED", "V18_13A_R1_stable*", "V18_13A_R1_STABLE_MANIFEST.csv"),
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
    "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv",
    "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES_INPUT_AUDIT.csv",
    "outputs/v18/read_center/V18_13B_CURRENT_RANKED_CANDIDATE_READ_CENTER.md",
    "outputs/v18/read_center/V18_13B_READ_FIRST.txt",
    "outputs/v18/read_center/V18_13B_CURRENT_RANKED_CANDIDATE_SUMMARY.csv",
    "outputs/v18/ops/V18_13B_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md",
    "outputs/v18/ops/V18_13B_R1_READ_FIRST.txt",
]


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def rel(base: Path, path: Path) -> str:
    try:
        return str(path.relative_to(base)).replace("\\", "/")
    except Exception:
        return str(path)


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


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


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
            return line[len(target) :].strip()
    return ""


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


def run_v18_13b(root: Path) -> Tuple[bool, str]:
    wrapper = root / "scripts/v18/run_v18_13B_ranked_candidate_read_center.ps1"
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(wrapper)],
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
    rows = read_csv_rows(manifest_path)
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


def dangerous_token_hits(root: Path) -> List[str]:
    hits: List[str] = []
    for rel_path in TOKEN_SCAN_OUTPUTS:
        path = root / rel_path
        text = read_text(path)
        for token in DANGEROUS_TOKENS:
            if token in text:
                hits.append(f"{rel_path}:{token}")
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
Write-Host "=== V18.13B-R1 STABLE SNAPSHOT RESTORE ==="
Write-Host "SNAPSHOT: $Snapshot"
Write-Host "ROOT: $Root"
Write-Host "APPLY: $Apply"
Write-Host "NOTE: Restore covers only V18.13B ranked candidate read center scripts and outputs."

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
    return f"""# V18.13B-R1 Stable Snapshot

Created: {now_text()}

Snapshot: {snapshot}

Purpose: Stable restore point for the source-deduplicated V18.13B Ranked Candidate Read Center.

Scope: Copies the V18.13B ranked candidate read center scripts and current outputs plus this snapshot's manifest, validation, README, and restore tooling.

Safety:
OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}
AUTO_TRADE: {AUTO_TRADE}
AUTO_SELL: {AUTO_SELL}
READ_ONLY: {READ_ONLY}
SNAPSHOT_ONLY: {SNAPSHOT_ONLY}
ranking_source_policy: {RANKING_SOURCE_POLICY}
fallback_used: {FALLBACK_USED}

Restore: RESTORE_V18_13B_R1.ps1 is generated but not executed by snapshot creation. It restores only the files listed in MANIFEST.csv.

Files:
MANIFEST: {manifest_path}
VALIDATION: {validation_path}
RESTORE_SCRIPT: {restore_path}
"""


def append_expectation(validations: List[Dict[str, str]], name: str, path: Path | str, expected: str, actual: str) -> None:
    validations.append(validation_row(name, "PASS" if actual == expected else "FAIL", path, expected, actual))


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
    readme_path = snapshot / "README_V18_13B_R1_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_13B_R1.ps1"
    report_path = out_dir / "V18_13B_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    read_first_path = out_dir / "V18_13B_R1_READ_FIRST.txt"

    v18_read_first = root / "outputs/v18/read_center/V18_13B_READ_FIRST.txt"
    summary_path = root / "outputs/v18/read_center/V18_13B_CURRENT_RANKED_CANDIDATE_SUMMARY.csv"
    audit_path = root / "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES_INPUT_AUDIT.csv"

    validations: List[Dict[str, str]] = []
    wrapper_ok, wrapper_output = run_v18_13b(root)
    validations.append(validation_row("RUN_V18_13B_RANKED_CANDIDATE_READ_CENTER", "PASS" if wrapper_ok else "FAIL", root / "scripts/v18/run_v18_13B_ranked_candidate_read_center.ps1", "exit_0", "exit_0" if wrapper_ok else "nonzero", wrapper_output))

    summary = summary_values(summary_path)
    audit_rows = read_csv_rows(audit_path)
    selected_sources = [row.get("input_path", "") for row in audit_rows if row.get("selected_for_ranking") == "TRUE"]
    audit_only_selected = [path for path in AUDIT_ONLY_SOURCE_FILES if path in selected_sources]

    selected_for_ranking_count = str(len(selected_sources))
    top5 = summary.get("TOP_5_TICKERS", read_first_value(v18_read_first, "TOP_5_TICKERS"))
    values = {
        "STATUS": summary.get("STATUS", read_first_value(v18_read_first, "STATUS")),
        "RANK_SOURCE_STATUS": summary.get("RANK_SOURCE_STATUS", read_first_value(v18_read_first, "RANK_SOURCE_STATUS")),
        "SECOND_STAGE_COUNT": summary.get("SECOND_STAGE_COUNT", read_first_value(v18_read_first, "SECOND_STAGE_COUNT")),
        "SCORED_TICKER_COUNT": summary.get("SCORED_TICKER_COUNT", ""),
        "UNSCORED_TICKER_COUNT": summary.get("UNSCORED_TICKER_COUNT", ""),
        "TOP_5_TICKERS": top5,
        "ranking_source_policy": summary.get("RANKING_SOURCE_POLICY", ""),
        "fallback_used": "TRUE" if "FALLBACK" in summary.get("RANKING_SOURCE_POLICY", "") else FALLBACK_USED,
        "selected_for_ranking_count": selected_for_ranking_count,
        "PRIMARY_SCORE_SOURCE_FILES": summary.get("PRIMARY_SCORE_SOURCE_FILES", ""),
        "AUDIT_ONLY_SOURCE_FILES": summary.get("AUDIT_ONLY_SOURCE_FILES", ""),
        "OFFICIAL_DECISION_IMPACT": summary.get("OFFICIAL_DECISION_IMPACT", read_first_value(v18_read_first, "OFFICIAL_DECISION_IMPACT")),
        "AUTO_TRADE": summary.get("AUTO_TRADE", read_first_value(v18_read_first, "AUTO_TRADE")),
        "AUTO_SELL": summary.get("AUTO_SELL", read_first_value(v18_read_first, "AUTO_SELL")),
        "READ_ONLY": summary.get("READ_ONLY", read_first_value(v18_read_first, "READ_ONLY")),
        "SNAPSHOT_ONLY": SNAPSHOT_ONLY,
    }

    expected_values = {
        "STATUS": EXPECTED_13B_STATUS,
        "RANK_SOURCE_STATUS": EXPECTED_RANK_SOURCE_STATUS,
        "SECOND_STAGE_COUNT": "20",
        "SCORED_TICKER_COUNT": "20",
        "UNSCORED_TICKER_COUNT": "0",
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "READ_ONLY": READ_ONLY,
        "ranking_source_policy": RANKING_SOURCE_POLICY,
        "fallback_used": FALLBACK_USED,
        "selected_for_ranking_count": "2",
    }
    for key, expected in expected_values.items():
        append_expectation(validations, f"V18_13B_{key}", summary_path if key not in {"STATUS", "RANK_SOURCE_STATUS", "SECOND_STAGE_COUNT"} else v18_read_first, expected, values.get(key, ""))

    primary_actual = values["PRIMARY_SCORE_SOURCE_FILES"].split(";") if values["PRIMARY_SCORE_SOURCE_FILES"] else []
    append_expectation(validations, "PRIMARY_SCORE_SOURCE_FILES_EXACT", summary_path, ";".join(PRIMARY_SCORE_SOURCE_FILES), ";".join(primary_actual))
    append_expectation(validations, "SELECTED_SOURCES_EXACT", audit_path, ";".join(PRIMARY_SCORE_SOURCE_FILES), ";".join(selected_sources))
    append_expectation(validations, "AUDIT_ONLY_FILES_NOT_SELECTED", audit_path, "none_selected", "none_selected" if not audit_only_selected else ";".join(audit_only_selected))

    for audit_only_path in AUDIT_ONLY_SOURCE_FILES:
        audit_row = next((row for row in audit_rows if row.get("input_path") == audit_only_path), {})
        append_expectation(validations, f"AUDIT_ONLY_NOT_SELECTED_{Path(audit_only_path).name}", audit_path, "FALSE", audit_row.get("selected_for_ranking", ""))

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
    preliminary_fail_count = copy_fail_count + missing_critical_count + validation_fail_count
    status = STATUS_OK if preliminary_fail_count == 0 else STATUS_WARN

    report = f"""# V18.13B-R1 Stable Snapshot

- STATUS: `{status}`
- SNAPSHOT_PATH: `{snapshot}`
- COPIED_FILE_COUNT: `PENDING`
- COPY_FAIL_COUNT: `{copy_fail_count}`
- MISSING_CRITICAL_COUNT: `{missing_critical_count}`
- VALIDATION_FAIL_COUNT: `{validation_fail_count}`
- RANK_SOURCE_STATUS: `{values['RANK_SOURCE_STATUS']}`
- SECOND_STAGE_COUNT: `{values['SECOND_STAGE_COUNT']}`
- SCORED_TICKER_COUNT: `{values['SCORED_TICKER_COUNT']}`
- UNSCORED_TICKER_COUNT: `{values['UNSCORED_TICKER_COUNT']}`
- TOP_5_TICKERS: `{values['TOP_5_TICKERS']}`
- selected_for_ranking_count: `{values['selected_for_ranking_count']}`
- ranking_source_policy: `{values['ranking_source_policy']}`
- fallback_used: `{values['fallback_used']}`
- OFFICIAL_DECISION_IMPACT: `{OFFICIAL_DECISION_IMPACT}`
- AUTO_TRADE: `{AUTO_TRADE}`
- AUTO_SELL: `{AUTO_SELL}`
- READ_ONLY: `{READ_ONLY}`
- SNAPSHOT_ONLY: `{SNAPSHOT_ONLY}`

## Source Selection

Ranking uses exactly the two primary current score sources. Audit-only source files are retained as evidence and excluded from ranking.

## Snapshot Scope

The snapshot contains the required V18.13B scripts, current ranked-candidate outputs, README, manifest, validation file, and restore tooling.
"""
    report_path.write_text(report, encoding="utf-8")

    read_first_out = f"""V18.13B-R1 STABLE SNAPSHOT READ FIRST

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

selected_for_ranking_count:
{values['selected_for_ranking_count']}

ranking_source_policy:
{values['ranking_source_policy']}

fallback_used:
{values['fallback_used']}

OFFICIAL_DECISION_IMPACT:
{OFFICIAL_DECISION_IMPACT}

AUTO_TRADE:
{AUTO_TRADE}

AUTO_SELL:
{AUTO_SELL}

READ_ONLY:
{READ_ONLY}

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

    hits = dangerous_token_hits(root)
    validations.append(validation_row("NO_DANGEROUS_TOKEN_IN_V18_13B_R1_OUTPUTS", "PASS" if not hits else "FAIL", "outputs/v18", "clean", "clean" if not hits else "found", "clean" if not hits else "redacted_hits_present"))
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

    report = report.replace("`PENDING`", f"`{copied_file_count}`").replace(f"- STATUS: `{STATUS_OK if preliminary_fail_count == 0 else STATUS_WARN}`", f"- STATUS: `{status}`").replace(f"- VALIDATION_FAIL_COUNT: `{validation_fail_count - (1 if hits else 0)}`", f"- VALIDATION_FAIL_COUNT: `{validation_fail_count}`")
    report_path.write_text(report, encoding="utf-8")
    read_first_out = read_first_out.replace("PENDING", str(copied_file_count)).replace(f"STATUS:\n{STATUS_OK if preliminary_fail_count == 0 else STATUS_WARN}", f"STATUS:\n{status}").replace(f"VALIDATION_FAIL_COUNT:\n{validation_fail_count - (1 if hits else 0)}", f"VALIDATION_FAIL_COUNT:\n{validation_fail_count}")
    read_first_path.write_text(read_first_out, encoding="utf-8")

    print(f"STATUS: {status}")
    print(f"SNAPSHOT_PATH: {snapshot}")
    print(f"COPIED_FILE_COUNT: {copied_file_count}")
    print(f"COPY_FAIL_COUNT: {copy_fail_count}")
    print(f"MISSING_CRITICAL_COUNT: {missing_critical_count}")
    print(f"VALIDATION_FAIL_COUNT: {validation_fail_count}")
    print(f"RANK_SOURCE_STATUS: {values['RANK_SOURCE_STATUS']}")
    print(f"SECOND_STAGE_COUNT: {values['SECOND_STAGE_COUNT']}")
    print(f"SCORED_TICKER_COUNT: {values['SCORED_TICKER_COUNT']}")
    print(f"UNSCORED_TICKER_COUNT: {values['UNSCORED_TICKER_COUNT']}")
    print(f"TOP_5_TICKERS: {values['TOP_5_TICKERS']}")
    print(f"selected_for_ranking_count: {values['selected_for_ranking_count']}")
    print(f"ranking_source_policy: {values['ranking_source_policy']}")
    print(f"fallback_used: {values['fallback_used']}")
    print(f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}")
    print(f"AUTO_TRADE: {AUTO_TRADE}")
    print(f"AUTO_SELL: {AUTO_SELL}")
    print(f"READ_ONLY: {READ_ONLY}")
    print(f"SNAPSHOT_ONLY: {SNAPSHOT_ONLY}")
    print(f"MANIFEST: {manifest_path}")
    print(f"VALIDATION: {validation_path}")
    print(f"RESTORE_SCRIPT: {restore_path}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first_path}")
    return 0 if status == STATUS_OK else 1


if __name__ == "__main__":
    raise SystemExit(main())
