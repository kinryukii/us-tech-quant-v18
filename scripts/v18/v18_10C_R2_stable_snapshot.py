from __future__ import annotations

import csv
import datetime as dt
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: List[Dict], fields: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def copy_file(src: Path, dst: Path) -> Tuple[bool, str]:
    try:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        return True, ""
    except Exception as e:
        return False, str(e)


def copy_tree_layer(root: Path, snapshot: Path, rel_layer: str) -> List[Dict]:
    src_dir = root / rel_layer
    rows: List[Dict] = []

    if not src_dir.exists():
        rows.append({
            "source": str(src_dir),
            "dest": "",
            "rel_path": rel_layer,
            "status": "MISSING_LAYER",
            "size_bytes": "",
            "error": "Layer not found",
        })
        return rows

    for src in src_dir.rglob("*"):
        if not src.is_file():
            continue

        rel = src.relative_to(root)
        dst = snapshot / rel
        ok, err = copy_file(src, dst)

        rows.append({
            "source": str(src),
            "dest": str(dst),
            "rel_path": str(rel),
            "status": "COPIED" if ok else "COPY_FAIL",
            "size_bytes": src.stat().st_size if src.exists() else "",
            "error": err,
        })

    return rows


def parse_check_ps1(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"

    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        f"[scriptblock]::Create((Get-Content -Raw '{str(path)}')) | Out-Null",
    ]

    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if p.returncode == 0:
            return True, ""
        return False, (p.stderr or p.stdout or "").strip()
    except Exception as e:
        return False, str(e)


def compile_check_py(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"

    try:
        py_compile.compile(str(path), doraise=True)
        return True, ""
    except Exception as e:
        return False, str(e)


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="utf-8-sig")
        except Exception:
            return ""


def build_restore_script(snapshot: Path, restore_path: Path) -> None:
    layers = [
        "scripts\\v18",
        "state\\v18\\factor_registry",
        "state\\v18\\simulation",
        "outputs\\v18\\factor_registry",
        "outputs\\v18\\factor_research",
        "outputs\\v18\\weight_research",
        "outputs\\v18\\simulation",
        "outputs\\v18\\read_center",
        "outputs\\v18\\ops",
    ]

    lines = []
    lines.append('param(')
    lines.append('    [string]$Root = "D:\\us-tech-quant",')
    lines.append('    [switch]$Apply')
    lines.append(')')
    lines.append('')
    lines.append('$ErrorActionPreference = "Stop"')
    lines.append('')
    lines.append(f'$Snapshot = "{str(snapshot)}"')
    lines.append('Write-Host ""')
    lines.append('Write-Host "=== V18.10C-R2 STABLE SNAPSHOT RESTORE ==="')
    lines.append('Write-Host "SNAPSHOT: $Snapshot"')
    lines.append('Write-Host "ROOT: $Root"')
    lines.append('')
    lines.append('if (-not (Test-Path $Snapshot)) { throw "Snapshot not found: $Snapshot" }')
    lines.append('')
    lines.append('$Layers = @(')
    for layer in layers:
        lines.append(f'    "{layer}",')
    lines.append(')')
    lines.append('')
    lines.append('foreach ($Layer in $Layers) {')
    lines.append('    $Src = Join-Path $Snapshot $Layer')
    lines.append('    $Dst = Join-Path $Root $Layer')
    lines.append('    if (Test-Path $Src) {')
    lines.append('        Write-Host "RESTORE_LAYER: $Layer"')
    lines.append('        if ($Apply) {')
    lines.append('            New-Item -ItemType Directory -Force -Path $Dst | Out-Null')
    lines.append('            Copy-Item -Path (Join-Path $Src "*") -Destination $Dst -Recurse -Force')
    lines.append('        }')
    lines.append('    }')
    lines.append('}')
    lines.append('')
    lines.append('if (-not $Apply) {')
    lines.append('    Write-Host ""')
    lines.append('    Write-Host "DRYRUN_ONLY. Re-run with -Apply to restore."')
    lines.append('}')
    lines.append('else {')
    lines.append('    Write-Host ""')
    lines.append('    Write-Host "RESTORE_APPLIED."')
    lines.append('}')
    lines.append('')

    restore_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) >= 2 else Path(r"D:\us-tech-quant")

    stamp = now_stamp()
    snapshot_name = f"V18_10C_R2_stable_factor_weight_research_chain_{stamp}"
    snapshot = root / "archive" / "stable" / snapshot_name
    ensure_dir(snapshot)

    out_dir = root / "outputs" / "v18" / "ops"
    ensure_dir(out_dir)

    manifest_path = snapshot / "V18_10C_R2_STABLE_MANIFEST.csv"
    readme_path = snapshot / "V18_10C_R2_STABLE_SNAPSHOT_README.txt"
    restore_path = snapshot / "restore_v18_10C_R2_stable_snapshot.ps1"
    check_path = snapshot / "V18_10C_R2_STABLE_VALIDATION_CHECKS.csv"
    combined_rf_path = snapshot / "V18_10C_R2_COMBINED_READ_FIRST_CAPTURE.txt"

    report_path = out_dir / "V18_10C_R2_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    read_first_path = out_dir / "V18_10C_R2_READ_FIRST.txt"

    layers = [
        "scripts/v18",
        "state/v18/factor_registry",
        "state/v18/simulation",
        "outputs/v18/factor_registry",
        "outputs/v18/factor_research",
        "outputs/v18/weight_research",
        "outputs/v18/simulation",
        "outputs/v18/read_center",
        "outputs/v18/ops",
    ]

    manifest_rows: List[Dict] = []

    for layer in layers:
        print(f"COPY_LAYER: {layer}")
        manifest_rows.extend(copy_tree_layer(root, snapshot, layer))

    write_csv(manifest_path, manifest_rows, [
        "source",
        "dest",
        "rel_path",
        "status",
        "size_bytes",
        "error",
    ])

    copied_count = sum(1 for r in manifest_rows if r["status"] == "COPIED")
    missing_layer_count = sum(1 for r in manifest_rows if r["status"] == "MISSING_LAYER")
    copy_fail_count = sum(1 for r in manifest_rows if r["status"] == "COPY_FAIL")

    critical_ps1 = [
        "scripts/v18/run_v18_current_official_daily.ps1",
        "scripts/v18/run_v18_9B_forward_return_filler.ps1",
        "scripts/v18/run_v18_10A_factor_registry_coverage_audit.ps1",
        "scripts/v18/run_v18_10A_R2_factor_daily_capture_patch.ps1",
        "scripts/v18/run_v18_10B_factor_effectiveness_backtest.ps1",
        "scripts/v18/run_v18_10B_R1_forward_return_maturity_monitor.ps1",
        "scripts/v18/run_v18_10B_R2_factor_research_daily_chain.ps1",
        "scripts/v18/run_v18_10B_R3_stable_snapshot.ps1",
        "scripts/v18/run_v18_10C_weight_research_engine.ps1",
        "scripts/v18/run_v18_10C_R1_factor_weight_research_daily_chain.ps1",
    ]

    critical_py = [
        "scripts/v18/v18_9B_forward_return_filler.py",
        "scripts/v18/v18_10A_factor_registry_coverage_audit.py",
        "scripts/v18/v18_10A_R2_factor_daily_capture_patch.py",
        "scripts/v18/v18_10B_factor_effectiveness_backtest.py",
        "scripts/v18/v18_10B_R1_forward_return_maturity_monitor.py",
        "scripts/v18/v18_10B_R3_stable_snapshot.py",
        "scripts/v18/v18_10C_weight_research_engine.py",
        "scripts/v18/v18_10C_R2_stable_snapshot.py",
    ]

    check_rows: List[Dict] = []

    for rel in critical_ps1:
        p = root / rel
        ok, err = parse_check_ps1(p)
        check_rows.append({
            "type": "ps1_parse",
            "path": str(p),
            "rel_path": rel,
            "status": "OK_PARSE" if ok else "PARSE_FAIL",
            "error": err,
        })

    for rel in critical_py:
        p = root / rel
        ok, err = compile_check_py(p)
        check_rows.append({
            "type": "py_compile",
            "path": str(p),
            "rel_path": rel,
            "status": "OK_PY_COMPILE" if ok else "PY_COMPILE_FAIL",
            "error": err,
        })

    write_csv(check_path, check_rows, [
        "type",
        "path",
        "rel_path",
        "status",
        "error",
    ])

    parse_fail_count = sum(1 for r in check_rows if r["status"] == "PARSE_FAIL")
    py_compile_fail_count = sum(1 for r in check_rows if r["status"] == "PY_COMPILE_FAIL")
    missing_critical_count = sum(1 for r in check_rows if r["error"] == "MISSING")

    build_restore_script(snapshot=snapshot, restore_path=restore_path)

    key_readfirsts = [
        root / "outputs/v18/weight_research/V18_10C_R1_READ_FIRST.txt",
        root / "outputs/v18/weight_research/V18_10C_READ_FIRST.txt",
        root / "outputs/v18/factor_research/V18_10B_R2_READ_FIRST.txt",
        root / "outputs/v18/factor_research/V18_10B_R1_READ_FIRST.txt",
        root / "outputs/v18/factor_research/V18_10B_READ_FIRST.txt",
        root / "outputs/v18/factor_registry/V18_10A_READ_FIRST.txt",
        root / "outputs/v18/simulation/V18_9B_READ_FIRST.txt",
    ]

    combined_rf = []
    for p in key_readfirsts:
        combined_rf.append("")
        combined_rf.append("=" * 88)
        combined_rf.append(str(p))
        combined_rf.append("=" * 88)
        combined_rf.append(read_text_safe(p))

    combined_rf_path.write_text("\n".join(combined_rf), encoding="utf-8")

    status = "OK_STABLE_SNAPSHOT_READY"
    if copy_fail_count > 0 or parse_fail_count > 0 or py_compile_fail_count > 0 or missing_critical_count > 0:
        status = "WARN_STABLE_SNAPSHOT_HAS_ISSUES"

    readme_lines = []
    readme_lines.append("V18.10C-R2 STABLE SNAPSHOT README")
    readme_lines.append("")
    readme_lines.append(f"STATUS: {status}")
    readme_lines.append(f"GENERATED: {now_text()}")
    readme_lines.append(f"ROOT: {root}")
    readme_lines.append(f"SNAPSHOT: {snapshot}")
    readme_lines.append("")
    readme_lines.append("PURPOSE:")
    readme_lines.append("Stable restore point after V18.10C-R1 integrated factor + weight research daily chain became clean.")
    readme_lines.append("")
    readme_lines.append("OFFICIAL_DECISION_IMPACT:")
    readme_lines.append("NONE")
    readme_lines.append("")
    readme_lines.append("AUTO_WEIGHT_CHANGE:")
    readme_lines.append("DISABLED")
    readme_lines.append("")
    readme_lines.append("AUTO_PROMOTION:")
    readme_lines.append("DISABLED")
    readme_lines.append("")
    readme_lines.append("AUTO_TRADE:")
    readme_lines.append("DISABLED")
    readme_lines.append("")
    readme_lines.append("SNAPSHOT CONTENT:")
    for layer in layers:
        readme_lines.append(f"- {layer}")
    readme_lines.append("")
    readme_lines.append("RESTORE:")
    readme_lines.append(f"powershell -NoProfile -ExecutionPolicy Bypass -File \"{restore_path}\"")
    readme_lines.append("Add -Apply only after reviewing dryrun output.")
    readme_lines.append("")
    readme_lines.append("MANIFEST:")
    readme_lines.append(str(manifest_path))
    readme_lines.append("")
    readme_lines.append("VALIDATION_CHECKS:")
    readme_lines.append(str(check_path))
    readme_lines.append("")
    readme_lines.append("COMBINED_READ_FIRST:")
    readme_lines.append(str(combined_rf_path))
    readme_lines.append("")

    readme_path.write_text("\n".join(readme_lines), encoding="utf-8")

    report_lines = []
    report_lines.append("# V18.10C-R2 Stable Snapshot")
    report_lines.append("")
    report_lines.append(f"Generated: `{now_text()}`")
    report_lines.append("")
    report_lines.append("## 1. Status")
    report_lines.append("")
    report_lines.append(f"- STATUS: `{status}`")
    report_lines.append("- MODE: `STABLE_RESTORE_POINT_FOR_FACTOR_WEIGHT_RESEARCH_CHAIN`")
    report_lines.append("- OFFICIAL_DECISION_IMPACT: `NONE`")
    report_lines.append("- AUTO_WEIGHT_CHANGE: `DISABLED`")
    report_lines.append("- AUTO_PROMOTION: `DISABLED`")
    report_lines.append("- AUTO_TRADE: `DISABLED`")
    report_lines.append("")
    report_lines.append("## 2. Snapshot")
    report_lines.append("")
    report_lines.append(f"- SNAPSHOT: `{snapshot}`")
    report_lines.append(f"- COPIED_FILE_COUNT: `{copied_count}`")
    report_lines.append(f"- MISSING_LAYER_COUNT: `{missing_layer_count}`")
    report_lines.append(f"- COPY_FAIL_COUNT: `{copy_fail_count}`")
    report_lines.append(f"- MISSING_CRITICAL_COUNT: `{missing_critical_count}`")
    report_lines.append(f"- PARSE_FAIL_COUNT: `{parse_fail_count}`")
    report_lines.append(f"- PY_COMPILE_FAIL_COUNT: `{py_compile_fail_count}`")
    report_lines.append("")
    report_lines.append("## 3. Critical validation")
    report_lines.append("")
    report_lines.append("| type | rel_path | status |")
    report_lines.append("|---|---|---|")
    for r in check_rows:
        report_lines.append(f"| {r['type']} | {r['rel_path']} | {r['status']} |")
    report_lines.append("")
    report_lines.append("## 4. Outputs")
    report_lines.append("")
    report_lines.append(f"- README: `{readme_path}`")
    report_lines.append(f"- MANIFEST: `{manifest_path}`")
    report_lines.append(f"- VALIDATION_CHECKS: `{check_path}`")
    report_lines.append(f"- RESTORE_SCRIPT: `{restore_path}`")
    report_lines.append(f"- COMBINED_READ_FIRST: `{combined_rf_path}`")
    report_lines.append(f"- REPORT: `{report_path}`")
    report_lines.append(f"- READ_FIRST: `{read_first_path}`")
    report_lines.append("")

    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    read_first = f"""V18.10C-R2 STABLE SNAPSHOT READ FIRST

STATUS:
{status}

MODE:
STABLE_RESTORE_POINT_FOR_FACTOR_WEIGHT_RESEARCH_CHAIN

OFFICIAL_DECISION_IMPACT:
NONE

AUTO_WEIGHT_CHANGE:
DISABLED

AUTO_PROMOTION:
DISABLED

AUTO_TRADE:
DISABLED

SNAPSHOT:
{snapshot}

COPIED_FILE_COUNT:
{copied_count}

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

README:
{readme_path}

MANIFEST:
{manifest_path}

VALIDATION_CHECKS:
{check_path}

RESTORE_SCRIPT:
{restore_path}

COMBINED_READ_FIRST:
{combined_rf_path}

REPORT:
{report_path}

READ_FIRST:
{read_first_path}

NEXT_STEP:
If STATUS is OK_STABLE_SNAPSHOT_READY, use V18.10C-R1 as the daily factor + weight research chain.
Do not promote or adjust weights until forward-return labels mature and evaluation rows become OK_EVALUATED.
"""
    read_first_path.write_text(read_first, encoding="utf-8")

    print("")
    print("=== V18.10C-R2 STABLE SNAPSHOT READY ===")
    print(f"STATUS: {status}")
    print("MODE: STABLE_RESTORE_POINT_FOR_FACTOR_WEIGHT_RESEARCH_CHAIN")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print("AUTO_WEIGHT_CHANGE: DISABLED")
    print("AUTO_PROMOTION: DISABLED")
    print("AUTO_TRADE: DISABLED")
    print(f"SNAPSHOT: {snapshot}")
    print(f"COPIED_FILE_COUNT: {copied_count}")
    print(f"MISSING_LAYER_COUNT: {missing_layer_count}")
    print(f"COPY_FAIL_COUNT: {copy_fail_count}")
    print(f"MISSING_CRITICAL_COUNT: {missing_critical_count}")
    print(f"PARSE_FAIL_COUNT: {parse_fail_count}")
    print(f"PY_COMPILE_FAIL_COUNT: {py_compile_fail_count}")
    print(f"README: {readme_path}")
    print(f"MANIFEST: {manifest_path}")
    print(f"VALIDATION_CHECKS: {check_path}")
    print(f"RESTORE_SCRIPT: {restore_path}")
    print(f"REPORT: {report_path}")
    print(f"READ_FIRST: {read_first_path}")
    print("")

    return 0 if status == "OK_STABLE_SNAPSHOT_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
