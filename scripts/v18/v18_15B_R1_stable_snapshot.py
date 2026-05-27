from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_15B_R1_STABLE_SNAPSHOT_READY"
STATUS_WARN = "WARN_V18_15B_R1_STABLE_SNAPSHOT_WITH_FAILURES"
SNAPSHOT_PREFIX = "V18_15B_R1_stable_current_daily_forward_tracker_manual_feedback_predev_audited"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
SNAPSHOT_ONLY = "TRUE"

CRITICAL_FILES = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/run_v18_15B_current_daily_with_manual_feedback.ps1",
    "scripts/v18/v18_15B_current_daily_with_manual_feedback.py",
    "scripts/v18/run_v18_15A_manual_position_trade_feedback.ps1",
    "scripts/v18/v18_15A_manual_position_trade_feedback.py",
    "state/v18/manual/V18_MANUAL_POSITIONS.csv",
    "state/v18/manual/V18_MANUAL_TRADE_LOG.csv",
    "scripts/v18/run_v18_14E_current_daily_with_forward_tracker.ps1",
    "scripts/v18/v18_14E_current_daily_with_forward_tracker.py",
    "scripts/v18/run_v18_14C_ranked_candidate_forward_tracker.ps1",
    "scripts/v18/v18_14C_ranked_candidate_forward_tracker.py",
    "scripts/v18/run_v18_14D_ranked_candidate_forward_price_filler.ps1",
    "scripts/v18/v18_14D_ranked_candidate_forward_price_filler.py",
    "scripts/v18/run_v18_15C_predevelopment_program_audit.ps1",
    "scripts/v18/v18_15C_predevelopment_program_audit.py",
    "outputs/v18/ops/V18_15C_READ_FIRST.txt",
    "outputs/v18/ops/V18_15C_CURRENT_PREDEVELOPMENT_PROGRAM_AUDIT_REPORT.md",
    "outputs/v18/ops/V18_15C_CURRENT_SCRIPT_INVENTORY.csv",
    "outputs/v18/ops/V18_15C_CURRENT_OUTPUT_INVENTORY.csv",
    "outputs/v18/ops/V18_15C_CURRENT_STABLE_SNAPSHOT_AUDIT.csv",
    "outputs/v18/ops/V18_15C_CURRENT_CURRENT_ALIAS_AUDIT.csv",
    "outputs/v18/ops/V18_15C_CURRENT_RANKING_FACTOR_LINEAGE_AUDIT.csv",
    "outputs/v18/ops/V18_15C_CURRENT_RUNTIME_VALIDATION_AUDIT.csv",
    "outputs/v18/ops/V18_15C_CURRENT_DANGEROUS_TOKEN_SCAN.csv",
    "outputs/v18/ops/V18_15C_CURRENT_PREDEVELOPMENT_RECOMMENDATIONS.csv",
    "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
    "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv",
    "outputs/v18/positions/V18_CURRENT_MANUAL_POSITION_REVIEW.csv",
    "outputs/v18/positions/V18_CURRENT_MANUAL_TRADE_FEEDBACK.csv",
    "outputs/v18/positions/V18_CURRENT_MANUAL_POSITION_LIFECYCLE_AUDIT.csv",
    "outputs/v18/ops/V18_CURRENT_FORWARD_TRACKER_READ_FIRST.txt",
    "outputs/v18/ops/V18_CURRENT_FORWARD_PRICE_FILLER_READ_FIRST.txt",
    "outputs/v18/ops/V18_CURRENT_MANUAL_FEEDBACK_READ_FIRST.txt",
    "outputs/v18/ops/V18_CURRENT_PREDEVELOPMENT_AUDIT_READ_FIRST.txt",
    "outputs/v18/ops/V18_CURRENT_RANKING_FACTOR_LINEAGE_AUDIT.csv",
    "scripts/v18/run_v18_15B_R1_stable_snapshot.ps1",
    "scripts/v18/v18_15B_R1_stable_snapshot.py",
]

PS_PARSE_FILES = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/run_v18_15B_current_daily_with_manual_feedback.ps1",
    "scripts/v18/run_v18_15A_manual_position_trade_feedback.ps1",
    "scripts/v18/run_v18_14E_current_daily_with_forward_tracker.ps1",
    "scripts/v18/run_v18_14C_ranked_candidate_forward_tracker.ps1",
    "scripts/v18/run_v18_14D_ranked_candidate_forward_price_filler.ps1",
    "scripts/v18/run_v18_15C_predevelopment_program_audit.ps1",
    "scripts/v18/run_v18_15B_R1_stable_snapshot.ps1",
]

PY_COMPILE_FILES = [
    "scripts/v18/v18_15B_current_daily_with_manual_feedback.py",
    "scripts/v18/v18_15A_manual_position_trade_feedback.py",
    "scripts/v18/v18_14E_current_daily_with_forward_tracker.py",
    "scripts/v18/v18_14C_ranked_candidate_forward_tracker.py",
    "scripts/v18/v18_14D_ranked_candidate_forward_price_filler.py",
    "scripts/v18/v18_15C_predevelopment_program_audit.py",
    "scripts/v18/v18_15B_R1_stable_snapshot.py",
]

RUNTIME_COMMANDS = [
    ("CURRENT_DEFAULT_SAFE_MODE", ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", r"D:\us-tech-quant\scripts\v18\run_v18_current_daily_command_center.ps1"]),
    ("CURRENT_FORWARD_TRACKER_AND_MANUAL_FEEDBACK", ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", r"D:\us-tech-quant\scripts\v18\run_v18_current_daily_command_center.ps1", "-RunForwardTracker", "-RunManualFeedback"]),
]


def stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            pass
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            pass
    return [], [], "CSV_PARSE_FAILED"


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
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def first_value(path: Path, key: str) -> str:
    target = key.upper()
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        if k.strip().upper().lstrip("- ").strip() == target:
            return v.strip()
    return ""


def ticker_value(row: Dict[str, str]) -> str:
    for key in row:
        if key.lower() in {"ticker", "symbol"}:
            return row.get(key, "").strip()
    return ""


def validation_row(name: str, status: str, path: str, expected: str, actual: str, note: str = "") -> Dict[str, str]:
    return {"check_name": name, "status": status, "path": path, "expected": expected, "actual": actual, "note": note}


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
    if not path.exists():
        return False, "MISSING"
    try:
        ast.parse(read_text(path), filename=str(path))
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def manifest_row(root: Path, snapshot: Path, src: Path, dst: Path, category: str, status: str, error: str = "") -> Dict[str, str]:
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


def copy_critical(root: Path, snapshot: Path, rel_path: str) -> Dict[str, str]:
    src = root / rel_path
    dst = snapshot / rel_path
    category = rel_path.split("/", 1)[0]
    if not src.exists() or not src.is_file():
        return manifest_row(root, snapshot, src, dst, category, "MISSING_CRITICAL", "Source file missing")
    try:
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        return manifest_row(root, snapshot, src, dst, category, "COPIED")
    except Exception as exc:
        return manifest_row(root, snapshot, src, dst, category, "COPY_FAIL", f"{type(exc).__name__}: {exc}")


def stable_baseline(root: Path) -> Dict[str, Tuple[float, str]]:
    base = root / "archive/stable"
    out: Dict[str, Tuple[float, str]] = {}
    if not base.exists():
        return out
    for folder in base.iterdir():
        if not folder.is_dir():
            continue
        manifest = folder / "MANIFEST.csv"
        digest = sha256(manifest) if manifest.exists() else ""
        out[str(folder.resolve())] = (folder.stat().st_mtime, digest)
    return out


def check_stable_protection(before: Dict[str, Tuple[float, str]], root: Path, new_snapshot: Path) -> Tuple[str, str]:
    after = stable_baseline(root)
    changed = []
    new_key = str(new_snapshot.resolve())
    for key, prior in before.items():
        if key == new_key:
            continue
        if key not in after:
            changed.append(f"missing:{key}")
        elif after[key] != prior:
            changed.append(f"modified:{key}")
    return ("PASS" if not changed else "FAIL", ";".join(changed[:10]) if changed else "existing stable snapshots unchanged")


def run_runtime(root: Path) -> List[Dict[str, str]]:
    rows = []
    for mode, args in RUNTIME_COMMANDS:
        proc = subprocess.run(args, cwd=str(root), text=True, capture_output=True, timeout=600)
        out = proc.stdout + "\n" + proc.stderr
        auto_trade = "DISABLED" if re.search(r"AUTO_TRADE:\s*DISABLED", out, re.I) else "UNKNOWN"
        auto_sell = "DISABLED" if re.search(r"AUTO_SELL:\s*DISABLED", out, re.I) else "UNKNOWN"
        impact = "NONE" if re.search(r"OFFICIAL_DECISION_IMPACT:\s*NONE", out, re.I) else "UNKNOWN"
        status = "PASS" if proc.returncode == 0 and auto_trade == "DISABLED" and auto_sell == "DISABLED" and impact == "NONE" else "FAIL"
        rows.append(validation_row(f"RUNTIME_{mode}", status, " ".join(args), "exit0_safe_guards", f"exit={proc.returncode};AUTO_TRADE={auto_trade};AUTO_SELL={auto_sell};OFFICIAL_DECISION_IMPACT={impact}", "\n".join(out.splitlines()[-12:])))
    return rows


def dangerous_hits(root: Path, paths: Sequence[Path]) -> List[str]:
    tokens = ["BUY_NOW", "SELL_NOW", "EXECUTE_LIVE_ORDER", "LIVE_TRADE", "LIVE_SELL"]
    hits = []
    for path in paths:
        text = read_text(path)
        token_definition_block = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            upper = line.upper()
            stripped = upper.strip()
            if "DANGEROUS_TOKENS" in upper or "TOKENS =" in upper or "TOKEN_PARTS" in upper or "GUARDED_PATTERNS" in upper:
                token_definition_block = True
            safe = (
                "DISABLED" in upper
                or "DO NOT" in upper
                or "DANGEROUS" in upper
                or "TOKEN" in upper
                or "GUARDED_PATTERNS" in upper
                or "EXACT_TOKENS" in upper
                or "TOKEN_PARTS" in upper
                or "TOKENS =" in upper
                or "SCAN" in upper
                or "HITS.APPEND" in upper
                or " IN UPPER" in upper
                or " AND NOT SAFE" in upper
                or token_definition_block
            )
            for token in tokens:
                if token in upper and not safe:
                    hits.append(f"{rel(root, path)}:{line_no}:{token}")
            if "AUTO_TRADE" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{rel(root, path)}:{line_no}:AUTO_TRADE_ENABLED")
            if "AUTO_SELL" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{rel(root, path)}:{line_no}:AUTO_SELL_ENABLED")
            if token_definition_block and (stripped.endswith(")") or stripped.endswith("]")):
                token_definition_block = False
    return hits


def build_restore(snapshot: Path) -> str:
    files = ",\n".join(f'    "{p}"' for p in CRITICAL_FILES if not p.startswith("outputs/v18/ops/V18_15C_CURRENT") and not p.startswith("outputs/v18/candidates") and not p.startswith("outputs/v18/positions"))
    return f'''param(
    [string]$Root = "D:\\us-tech-quant",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$Snapshot = "{snapshot}"

Write-Host "=== V18.15B-R1 STABLE SNAPSHOT RESTORE ==="
Write-Host "SNAPSHOT: $Snapshot"
Write-Host "ROOT: $Root"
Write-Host "APPLY: $Apply"
Write-Host "SNAPSHOT_ONLY: TRUE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

if (-not (Test-Path -LiteralPath $Snapshot)) {{
    throw "MISSING_SNAPSHOT: $Snapshot"
}}

$Files = @(
{files}
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
    Write-Host "DRYRUN_ONLY. Re-run with -Apply to restore V18.15B-R1 files."
}}
else {{
    Write-Host "RESTORE_APPLIED."
}}
'''


def build(root: Path) -> int:
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    ensure_dir(ops)
    before_stable = stable_baseline(root)
    snapshot = root / "archive/stable" / f"{SNAPSHOT_PREFIX}_{stamp()}"
    ensure_dir(snapshot)

    read_first_path = ops / "V18_15B_R1_READ_FIRST.txt"
    report_path = ops / "V18_15B_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md"
    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_15B_R1_STABLE_SNAPSHOT.md"
    restore_path = snapshot / "RESTORE_V18_15B_R1.ps1"

    validations: List[Dict[str, str]] = []
    v15c_read = root / "outputs/v18/ops/V18_15C_READ_FIRST.txt"
    validations.append(validation_row("V18_15C_READY_FOR_V18_16", "PASS" if first_value(v15c_read, "READY_FOR_V18_16") == "TRUE" else "FAIL", str(v15c_read), "TRUE", first_value(v15c_read, "READY_FOR_V18_16")))
    validations.extend(run_runtime(root))

    for rel_path in PS_PARSE_FILES:
        ok, note = parse_ps(root / rel_path)
        validations.append(validation_row(f"POWERSHELL_PARSE_{Path(rel_path).name}", "PASS" if ok else "FAIL", rel_path, "parse_ok", "parse_ok" if ok else "parse_fail", note))
    for rel_path in PY_COMPILE_FILES:
        ok, note = compile_py(root / rel_path)
        validations.append(validation_row(f"PY_COMPILE_{Path(rel_path).name}", "PASS" if ok else "FAIL", rel_path, "compile_ok", "compile_ok" if ok else "compile_fail", note))

    manifest_rows = [copy_critical(root, snapshot, rel_path) for rel_path in CRITICAL_FILES]

    write_text(restore_path, build_restore(snapshot))
    write_text(
        readme_path,
        f"""# V18.15B-R1 Stable Snapshot

Created: {now_text()}

Snapshot: {snapshot}

Purpose: Stable restore point for the V18 current daily command center with forward tracker integration, manual feedback integration, and V18.15C pre-development audit evidence.

Safety:
AUTO_TRADE: {AUTO_TRADE}
AUTO_SELL: {AUTO_SELL}
OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}
SNAPSHOT_ONLY: {SNAPSHOT_ONLY}
FULL_DAILY: NOT_RUN
YFINANCE: NOT_USED
""",
    )
    for metadata in (readme_path, restore_path):
        manifest_rows.append(manifest_row(root, snapshot, metadata, metadata, "snapshot_metadata", "COPIED"))

    protection_status, protection_note = check_stable_protection(before_stable, root, snapshot)
    validations.append(validation_row("EXISTING_STABLE_SNAPSHOTS_NOT_MODIFIED", protection_status, str(root / "archive/stable"), "unchanged", protection_status, protection_note))
    for metadata_name, metadata_path in [("README_PRESENT", readme_path), ("RESTORE_PRESENT", restore_path)]:
        validations.append(validation_row(metadata_name, "PASS" if metadata_path.exists() else "FAIL", str(metadata_path), "present", "present" if metadata_path.exists() else "missing"))

    scan_paths = [root / p for p in PS_PARSE_FILES] + [read_first_path, report_path, readme_path, restore_path]
    scan_paths += [snapshot / p for p in CRITICAL_FILES]
    hits = dangerous_hits(root, scan_paths)
    validations.append(validation_row("DANGEROUS_TOKEN_SCAN", "PASS" if not hits else "FAIL", "new outputs and relevant scripts", "0", str(len(hits)), ";".join(hits[:20])))

    validation_fields = ["check_name", "status", "path", "expected", "actual", "note"]
    manifest_fields = ["category", "status", "required", "source_path", "snapshot_path", "relative_source_path", "relative_snapshot_path", "size_bytes", "last_write_time", "sha256", "error"]
    write_csv(validation_path, validations, validation_fields)
    manifest_rows.append(manifest_row(root, snapshot, validation_path, validation_path, "snapshot_metadata", "COPIED"))
    write_csv(manifest_path, manifest_rows, manifest_fields)
    manifest_rows.append(manifest_row(root, snapshot, manifest_path, manifest_path, "snapshot_metadata", "COPIED"))
    write_csv(manifest_path, manifest_rows, manifest_fields)
    validations.append(validation_row("MANIFEST_PRESENT", "PASS" if manifest_path.exists() else "FAIL", str(manifest_path), "present", "present" if manifest_path.exists() else "missing"))
    validations.append(validation_row("VALIDATION_PRESENT", "PASS" if validation_path.exists() else "FAIL", str(validation_path), "present", "present" if validation_path.exists() else "missing"))
    write_csv(validation_path, validations, validation_fields)

    ranked_rows, _, _ = read_csv(root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv")
    top5 = ",".join(ticker_value(r) for r in ranked_rows[:5] if ticker_value(r))
    copied = sum(1 for r in manifest_rows if r["status"] == "COPIED")
    copy_fail = sum(1 for r in manifest_rows if r["status"] == "COPY_FAIL")
    missing = sum(1 for r in manifest_rows if r["status"] == "MISSING_CRITICAL")
    ps_pass = sum(1 for r in validations if r["check_name"].startswith("POWERSHELL_PARSE_") and r["status"] == "PASS")
    ps_fail = sum(1 for r in validations if r["check_name"].startswith("POWERSHELL_PARSE_") and r["status"] != "PASS")
    py_pass = sum(1 for r in validations if r["check_name"].startswith("PY_COMPILE_") and r["status"] == "PASS")
    py_fail = sum(1 for r in validations if r["check_name"].startswith("PY_COMPILE_") and r["status"] != "PASS")
    runtime_rows = [r for r in validations if r["check_name"].startswith("RUNTIME_")]
    runtime_fail = sum(1 for r in runtime_rows if r["status"] != "PASS")
    dangerous_count = len(hits)
    v15c_ready = first_value(v15c_read, "READY_FOR_V18_16") or "FALSE"
    rank_source = first_value(v15c_read, "RANK_SOURCE_STATUS") or "UNKNOWN"
    validation_fail = copy_fail + missing + ps_fail + py_fail + runtime_fail + dangerous_count
    if v15c_ready != "TRUE":
        validation_fail += 1
    if protection_status != "PASS":
        validation_fail += 1
    status = STATUS_OK if validation_fail == 0 else STATUS_WARN

    values = {
        "STATUS": status,
        "SNAPSHOT_PATH": str(snapshot),
        "COPIED_FILE_COUNT": str(copied),
        "COPY_FAIL_COUNT": str(copy_fail),
        "MISSING_CRITICAL_COUNT": str(missing),
        "POWERSHELL_PARSE_PASS_COUNT": str(ps_pass),
        "POWERSHELL_PARSE_FAIL_COUNT": str(ps_fail),
        "PYTHON_COMPILE_PASS_COUNT": str(py_pass),
        "PYTHON_COMPILE_FAIL_COUNT": str(py_fail),
        "RUNTIME_VALIDATION_RUN_COUNT": str(len(runtime_rows)),
        "RUNTIME_VALIDATION_FAIL_COUNT": str(runtime_fail),
        "V18_15C_READY_FOR_V18_16": v15c_ready,
        "RANK_SOURCE_STATUS": rank_source,
        "TOP_5_TICKERS": top5,
        "DANGEROUS_TOKEN_FINDING_COUNT": str(dangerous_count),
        "STABLE_SNAPSHOT_PROTECTION_STATUS": protection_status,
        "VALIDATION_FAIL_COUNT": str(validation_fail),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "SNAPSHOT_ONLY": SNAPSHOT_ONLY,
    }
    read_keys = [
        "STATUS", "SNAPSHOT_PATH", "COPIED_FILE_COUNT", "COPY_FAIL_COUNT", "MISSING_CRITICAL_COUNT",
        "POWERSHELL_PARSE_PASS_COUNT", "POWERSHELL_PARSE_FAIL_COUNT", "PYTHON_COMPILE_PASS_COUNT",
        "PYTHON_COMPILE_FAIL_COUNT", "RUNTIME_VALIDATION_RUN_COUNT", "RUNTIME_VALIDATION_FAIL_COUNT",
        "V18_15C_READY_FOR_V18_16", "RANK_SOURCE_STATUS", "TOP_5_TICKERS",
        "DANGEROUS_TOKEN_FINDING_COUNT", "STABLE_SNAPSHOT_PROTECTION_STATUS", "VALIDATION_FAIL_COUNT",
        "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT", "SNAPSHOT_ONLY",
    ]
    write_text(read_first_path, "\n".join(f"{k}: {values[k]}" for k in read_keys) + "\n")
    write_text(
        report_path,
        "# V18.15B-R1 Current Stable Snapshot Report\n\n"
        + "\n".join(f"- {k}: {values[k]}" for k in read_keys)
        + f"\n\n- MANIFEST: {manifest_path}\n- VALIDATION: {validation_path}\n- RESTORE_SCRIPT: {restore_path}\n",
    )

    for key in [
        "STATUS", "SNAPSHOT_PATH", "COPIED_FILE_COUNT", "COPY_FAIL_COUNT", "MISSING_CRITICAL_COUNT",
        "VALIDATION_FAIL_COUNT", "V18_15C_READY_FOR_V18_16", "RANK_SOURCE_STATUS", "TOP_5_TICKERS",
        "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT",
    ]:
        print(f"{key}: {values[key]}")
    return 0 if status == STATUS_OK else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
