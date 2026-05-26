from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_19A_R1_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_19A_R1_STABLE_SNAPSHOT_VALIDATION_FAILED"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
SNAPSHOT_ONLY = "TRUE"
SNAPSHOT_NAME = "V18_19A_R1_stable_daily_readability_refactor"

CRITICAL_FILES = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/v18_19A_daily_readability_refactor.py",
    "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
    "scripts/v18/v18_19A_R1_stable_snapshot.py",
    "scripts/v18/run_v18_19A_R1_stable_snapshot.ps1",
    "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
    "outputs/v18/read_center/V18_CURRENT_DAILY_COMMAND_CENTER.md",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST.md",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
    "outputs/v18/ops/V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt",
    "outputs/v18/ops/V18_CURRENT_RANKING_PROVENANCE_READ_FIRST.txt",
    "outputs/v18/ops/V18_16H_READ_FIRST.txt",
    "outputs/v18/ops/V18_16F_READ_FIRST.txt",
    "outputs/v18/ops/V18_16F_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN_SUMMARY.csv",
    "outputs/v18/ops/V18_16F_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN_INPUT_AUDIT.csv",
    "outputs/v18/ops/V18_17A_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_DAILY_READABILITY_AUDIT.csv",
]

OPTIONAL_DIRS = [
    "outputs/v18/read_center/daily_packet",
    "state/v18/universe",
]

PS_PARSE = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
    "scripts/v18/run_v18_19A_R1_stable_snapshot.ps1",
]

PY_COMPILE = [
    "scripts/v18/v18_19A_daily_readability_refactor.py",
    "scripts/v18/v18_19A_R1_stable_snapshot.py",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(base: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def first_value(path: Path, key: str) -> str:
    target = key.upper()
    for raw in read_text(path).splitlines():
        if ":" not in raw:
            continue
        left, right = raw.split(":", 1)
        if left.strip().lstrip("- ").strip().upper() == target:
            return right.strip()
    return ""


def stable_baseline(root: Path) -> Dict[str, Tuple[float, str]]:
    base = root / "archive/stable"
    out: Dict[str, Tuple[float, str]] = {}
    if not base.exists():
        return out
    for folder in base.iterdir():
        if folder.is_dir():
            manifest = folder / "MANIFEST.csv"
            out[str(folder.resolve())] = (folder.stat().st_mtime, sha256(manifest))
    return out


def parse_ps(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    ps_path = str(path.resolve()).replace("'", "''")
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f"$p='{ps_path}'; $t=$null; $e=$null; [System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$e) > $null; if ($e.Count -gt 0) {{ $e | ForEach-Object {{ $_.Message }}; exit 1 }}",
    ]
    proc = subprocess.run(command, text=True, capture_output=True, timeout=60)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def compile_py(path: Path) -> Tuple[bool, str]:
    try:
        ast.parse(read_text(path), filename=str(path))
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def manifest_row(root: Path, snapshot: Path, src: Path, dst: Path, category: str, status: str, error: str = "") -> Dict[str, object]:
    size = ""
    digest = ""
    modified = ""
    if dst.exists() and dst.is_file():
        stat = dst.stat()
        size = stat.st_size
        digest = sha256(dst)
        modified = dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    return {
        "category": category,
        "status": status,
        "required": "YES",
        "source_path": str(src),
        "snapshot_path": str(dst),
        "relative_source_path": rel(root, src),
        "relative_snapshot_path": rel(snapshot, dst),
        "size_bytes": size,
        "last_write_time": modified,
        "sha256": digest,
        "error": error,
    }


def copy_file(root: Path, snapshot: Path, rel_path: str, category: str = "critical") -> Dict[str, object]:
    src = root / rel_path
    dst = snapshot / rel_path
    if not src.exists() or not src.is_file():
        return manifest_row(root, snapshot, src, dst, category, "MISSING_CRITICAL", "Source file missing")
    try:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        return manifest_row(root, snapshot, src, dst, category, "COPIED")
    except Exception as exc:
        return manifest_row(root, snapshot, src, dst, category, "COPY_FAIL", f"{type(exc).__name__}: {exc}")


def copy_dir(root: Path, snapshot: Path, rel_dir: str) -> List[Dict[str, object]]:
    src_dir = root / rel_dir
    rows: List[Dict[str, object]] = []
    if not src_dir.exists():
        return rows
    for src in sorted(p for p in src_dir.rglob("*") if p.is_file()):
        rows.append(copy_file(root, snapshot, rel(root, src), "context_directory"))
    return rows


def build_restore_script(snapshot: Path) -> str:
    files = CRITICAL_FILES + [
        "outputs/v18/read_center/daily_packet/V18_CURRENT_COVERAGE_STATUS.md",
        "outputs/v18/read_center/daily_packet/V18_CURRENT_DATA_FRESHNESS.md",
        "outputs/v18/read_center/daily_packet/V18_CURRENT_RISK_DASHBOARD.md",
        "outputs/v18/read_center/daily_packet/V18_CURRENT_TOP_RANKED_CANDIDATES.md",
        "outputs/v18/read_center/daily_packet/V18_CURRENT_UNIVERSE_CHANGES.md",
    ]
    file_lines = ",\n".join(f'    "{p}"' for p in files)
    return f'''param(
    [string]$Root = "D:\\us-tech-quant",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$Snapshot = "{snapshot}"
Write-Host "=== V18.19A-R1 STABLE SNAPSHOT RESTORE ==="
Write-Host "SNAPSHOT: $Snapshot"
Write-Host "ROOT: $Root"
Write-Host "APPLY: $Apply"
Write-Host "SNAPSHOT_ONLY: TRUE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
if (-not (Test-Path -LiteralPath $Snapshot)) {{ throw "MISSING_SNAPSHOT: $Snapshot" }}
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
}}
if (-not $Apply) {{
    Write-Host "DRYRUN_ONLY. Re-run with -Apply to restore."
}}
'''


def check_current_aliases(root: Path) -> List[str]:
    return [
        "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
        "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
        "outputs/v18/read_center/V18_CURRENT_DAILY_COMMAND_CENTER.md",
        "outputs/v18/ops/V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt",
        "outputs/v18/ops/V18_CURRENT_RANKING_PROVENANCE_READ_FIRST.txt",
    ]


def build(root: Path) -> int:
    root = root.resolve()
    before_stable = stable_baseline(root)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot = root / "archive/stable" / f"{SNAPSHOT_NAME}_{timestamp}"
    ensure_dir(snapshot)

    ops = root / "outputs/v18/ops"
    ensure_dir(ops)
    read_first_path = ops / "V18_19A_R1_READ_FIRST.txt"
    report_path = ops / "V18_19A_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_19A_R1_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_19A_R1.ps1"

    validations: List[Dict[str, object]] = []
    for rel_path in PS_PARSE:
        ok, note = parse_ps(root / rel_path)
        validations.append({
            "check_name": f"POWERSHELL_PARSE_{Path(rel_path).name}",
            "status": "PASS" if ok else "FAIL",
            "path": rel_path,
            "expected": "parse_ok",
            "actual": "parse_ok" if ok else "parse_fail",
            "note": note,
        })
    for rel_path in PY_COMPILE:
        ok, note = compile_py(root / rel_path)
        validations.append({
            "check_name": f"PY_COMPILE_{Path(rel_path).name}",
            "status": "PASS" if ok else "FAIL",
            "path": rel_path,
            "expected": "compile_ok",
            "actual": "compile_ok" if ok else "compile_fail",
            "note": note,
        })

    manifest_rows = [copy_file(root, snapshot, p) for p in CRITICAL_FILES]
    for d in OPTIONAL_DIRS:
        manifest_rows.extend(copy_dir(root, snapshot, d))

    write_text(restore_path, build_restore_script(snapshot))
    manifest_rows.append(manifest_row(root, snapshot, restore_path, restore_path, "snapshot_metadata", "COPIED"))

    summary_source = root / "outputs/v18/ops/V18_19A_READ_FIRST.txt"
    status_value = first_value(summary_source, "STATUS") or STATUS_WARN
    trust_level = first_value(summary_source, "DAILY_TRUST_LEVEL") or "UNKNOWN"
    auto_trade = first_value(summary_source, "AUTO_TRADE") or AUTO_TRADE
    auto_sell = first_value(summary_source, "AUTO_SELL") or AUTO_SELL
    official = first_value(summary_source, "OFFICIAL_DECISION_IMPACT") or OFFICIAL_DECISION_IMPACT
    validation_fail_count = first_value(summary_source, "VALIDATION_FAIL_COUNT") or "0"
    snapshot_path_value = str(snapshot)

    snapshot_file_count = sum(1 for row in manifest_rows if row["status"] == "COPIED")
    copy_fail_count = sum(1 for row in manifest_rows if row["status"] == "COPY_FAIL")
    missing_critical_count = sum(1 for row in manifest_rows if row["status"] == "MISSING_CRITICAL")
    stable_missing = [key for key in before_stable if key not in stable_baseline(root)]
    stable_modified = [
        key for key, value in before_stable.items()
        if key in stable_baseline(root) and stable_baseline(root)[key] != value
    ]
    current_alias_missing = [p for p in check_current_aliases(root) if not (root / p).exists()]
    validation_rows: List[Dict[str, object]] = validations[:]
    validation_rows.extend([
        {
            "check_name": "SNAPSHOT_DIR_EXISTS",
            "status": "PASS" if snapshot.exists() else "FAIL",
            "path": str(snapshot),
            "expected": "exists",
            "actual": "exists" if snapshot.exists() else "missing",
            "note": "",
        },
        {
            "check_name": "MANIFEST_ROWS_PRESENT",
            "status": "PASS" if snapshot_file_count > 0 else "FAIL",
            "path": str(manifest_path),
            "expected": "rows>0",
            "actual": f"rows={snapshot_file_count}",
            "note": "",
        },
        {
            "check_name": "RESTORE_PRESENT",
            "status": "PASS" if restore_path.exists() else "FAIL",
            "path": str(restore_path),
            "expected": "exists",
            "actual": "exists" if restore_path.exists() else "missing",
            "note": "",
        },
        {
            "check_name": "CRITICAL_FILES_PRESENT",
            "status": "PASS" if missing_critical_count == 0 and copy_fail_count == 0 else "FAIL",
            "path": str(snapshot),
            "expected": "all critical copied",
            "actual": f"missing={missing_critical_count};copy_fail={copy_fail_count}",
            "note": "",
        },
        {
            "check_name": "AUTO_TRADE_DISABLED",
            "status": "PASS" if auto_trade.upper() == "DISABLED" else "FAIL",
            "path": str(read_first_path),
            "expected": "DISABLED",
            "actual": auto_trade,
            "note": "",
        },
        {
            "check_name": "AUTO_SELL_DISABLED",
            "status": "PASS" if auto_sell.upper() == "DISABLED" else "FAIL",
            "path": str(read_first_path),
            "expected": "DISABLED",
            "actual": auto_sell,
            "note": "",
        },
        {
            "check_name": "OFFICIAL_DECISION_NONE",
            "status": "PASS" if official.upper() == "NONE" else "FAIL",
            "path": str(read_first_path),
            "expected": "NONE",
            "actual": official,
            "note": "",
        },
        {
            "check_name": "CURRENT_ALIASES_PRESENT",
            "status": "PASS" if not current_alias_missing else "FAIL",
            "path": " ; ".join(check_current_aliases(root)),
            "expected": "present",
            "actual": "present" if not current_alias_missing else f"missing={len(current_alias_missing)}",
            "note": "; ".join(current_alias_missing),
        },
        {
            "check_name": "STABLE_HISTORY_PRESERVED",
            "status": "PASS" if not stable_missing and not stable_modified else "FAIL",
            "path": str(root / "archive/stable"),
            "expected": "no deletions or modifications",
            "actual": f"missing={len(stable_missing)};modified={len(stable_modified)}",
            "note": "",
        },
        {
            "check_name": "NO_ENABLEMENT_TOKENS",
            "status": "PASS" if auto_trade.upper() == "DISABLED" and auto_sell.upper() == "DISABLED" and official.upper() == "NONE" else "FAIL",
            "path": str(read_first_path),
            "expected": "none",
            "actual": f"AUTO_TRADE={auto_trade};AUTO_SELL={auto_sell};OFFICIAL_DECISION_IMPACT={official}",
            "note": "",
        },
    ])

    validation_fail_count_total = sum(1 for row in validation_rows if row["status"] != "PASS")

    read_first_values = {
        "STATUS": STATUS_OK if validation_fail_count_total == 0 else STATUS_WARN,
        "SNAPSHOT_NAME": SNAPSHOT_NAME,
        "SNAPSHOT_PATH": snapshot_path_value,
        "COPIED_FILE_COUNT": str(snapshot_file_count),
        "COPY_FAIL_COUNT": str(copy_fail_count),
        "MISSING_CRITICAL_COUNT": str(missing_critical_count),
        "VALIDATION_FAIL_COUNT": str(validation_fail_count_total),
        "AUTO_TRADE": auto_trade,
        "AUTO_SELL": auto_sell,
        "OFFICIAL_DECISION_IMPACT": official,
        "DAILY_TRUST_LEVEL": trust_level,
        "READ_FIRST": str(read_first_path),
        "SNAPSHOT_REPORT": str(report_path),
        "MANIFEST": str(manifest_path),
        "VALIDATION": str(validation_path),
        "README": str(readme_path),
        "RESTORE_SCRIPT": str(restore_path),
    }
    write_text(read_first_path, "\n".join(f"{k}: {v}" for k, v in read_first_values.items()) + "\n")

    readme_lines = [
        "# V18.19A-R1 Stable Snapshot",
        "",
        f"Created: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Snapshot: {snapshot}",
        "",
        "Stable snapshot for the reviewed V18.19A reporting-only daily readability refactor.",
        "",
        f"AUTO_TRADE: {AUTO_TRADE}",
        f"AUTO_SELL: {AUTO_SELL}",
        f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"SNAPSHOT_ONLY: {SNAPSHOT_ONLY}",
    ]
    write_text(readme_path, "\n".join(readme_lines) + "\n")

    for row in validation_rows:
        if row["check_name"] == "README_PRESENT":
            row["status"] = "PASS" if readme_path.exists() else "FAIL"
            row["path"] = str(readme_path)
            row["expected"] = "exists"
            row["actual"] = "exists" if readme_path.exists() else "missing"
            row["note"] = ""

    write_csv(validation_path, validation_rows, ["check_name", "status", "path", "expected", "actual", "note"])

    manifest_rows.append(manifest_row(root, snapshot, readme_path, readme_path, "snapshot_metadata", "COPIED"))
    manifest_rows.append(manifest_row(root, snapshot, validation_path, validation_path, "snapshot_metadata", "COPIED"))
    manifest_rows.append(manifest_row(root, snapshot, manifest_path, manifest_path, "snapshot_metadata", "COPIED"))
    write_csv(manifest_path, manifest_rows, ["category", "status", "required", "source_path", "snapshot_path", "relative_source_path", "relative_snapshot_path", "size_bytes", "last_write_time", "sha256", "error"])

    report_lines = [
        "# V18.19A-R1 Stable Snapshot Report",
        "",
        f"- STATUS: {read_first_values['STATUS']}",
        f"- SNAPSHOT_PATH: {read_first_values['SNAPSHOT_PATH']}",
        f"- COPIED_FILE_COUNT: {read_first_values['COPIED_FILE_COUNT']}",
        f"- COPY_FAIL_COUNT: {read_first_values['COPY_FAIL_COUNT']}",
        f"- MISSING_CRITICAL_COUNT: {read_first_values['MISSING_CRITICAL_COUNT']}",
        f"- VALIDATION_FAIL_COUNT: {read_first_values['VALIDATION_FAIL_COUNT']}",
        f"- AUTO_TRADE: {read_first_values['AUTO_TRADE']}",
        f"- AUTO_SELL: {read_first_values['AUTO_SELL']}",
        f"- OFFICIAL_DECISION_IMPACT: {read_first_values['OFFICIAL_DECISION_IMPACT']}",
        f"- DAILY_TRUST_LEVEL: {read_first_values['DAILY_TRUST_LEVEL']}",
        f"- MANIFEST: {manifest_path}",
        f"- VALIDATION: {validation_path}",
        f"- README: {readme_path}",
        f"- RESTORE_SCRIPT: {restore_path}",
        "",
        "## Validation",
        "",
    ]
    for row in validation_rows:
        report_lines.append(f"- {row['check_name']}: {row['status']} {row.get('note', '')}".rstrip())
    write_text(report_path, "\n".join(report_lines) + "\n")

    print(f"STATUS: {read_first_values['STATUS']}")
    print(f"SNAPSHOT_PATH: {read_first_values['SNAPSHOT_PATH']}")
    print(f"COPIED_FILE_COUNT: {read_first_values['COPIED_FILE_COUNT']}")
    print(f"COPY_FAIL_COUNT: {read_first_values['COPY_FAIL_COUNT']}")
    print(f"MISSING_CRITICAL_COUNT: {read_first_values['MISSING_CRITICAL_COUNT']}")
    print(f"VALIDATION_FAIL_COUNT: {read_first_values['VALIDATION_FAIL_COUNT']}")
    print(f"AUTO_TRADE: {read_first_values['AUTO_TRADE']}")
    print(f"AUTO_SELL: {read_first_values['AUTO_SELL']}")
    print(f"OFFICIAL_DECISION_IMPACT: {read_first_values['OFFICIAL_DECISION_IMPACT']}")
    print(f"READ_FIRST: {read_first_path}")
    print(f"SNAPSHOT_REPORT: {report_path}")
    return 0 if validation_fail_count_total == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the V18.19A-R1 stable snapshot.")
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
