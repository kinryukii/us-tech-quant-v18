from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_18E_TECHNICAL_TIMING_ALIAS_EXTERNALIZATION_AUDIT_READY"
STATUS_WARN = "WARN_V18_18E_TECHNICAL_TIMING_ALIAS_EXTERNALIZATION_AUDIT_VALIDATION_FAILED"
MODE = "DRYRUN"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def mb(size: int | float) -> str:
    return f"{float(size) / (1024 * 1024):.3f}"


def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
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


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
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


def stable_baseline(root: Path) -> Dict[str, Tuple[float, str]]:
    base = root / "archive/stable"
    out: Dict[str, Tuple[float, str]] = {}
    if base.exists():
        for folder in base.iterdir():
            if folder.is_dir():
                out[str(folder.resolve())] = (folder.stat().st_mtime, sha256(folder / "MANIFEST.csv"))
    return out


def stable_modified(before: Dict[str, Tuple[float, str]], root: Path) -> bool:
    after = stable_baseline(root)
    return any(after.get(key) != value for key, value in before.items())


def parse_ps(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    ps_path = str(path.resolve()).replace("'", "''")
    cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
        f"$p='{ps_path}'; $t=$null; $e=$null; [System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$e) > $null; if ($e.Count -gt 0) {{ $e | ForEach-Object {{ $_.Message }}; exit 1 }}"
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def compile_py(path: Path) -> Tuple[bool, str]:
    try:
        ast.parse(read_text(path), filename=str(path))
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def dangerous_hits(paths: Iterable[Path]) -> List[str]:
    tokens = ["BUY_NOW", "SELL_NOW", "EXECUTE_LIVE_ORDER", "LIVE_TRADE", "LIVE_SELL"]
    hits: List[str] = []
    for path in paths:
        text = read_text(path)
        in_token_block = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            upper = line.upper()
            stripped = upper.strip()
            if "TOKENS =" in upper or "DANGEROUS" in upper:
                in_token_block = True
            safe = (
                "DISABLED" in upper or "DO NOT" in upper or "TOKEN" in upper
                or "HITS.APPEND" in upper or " IN UPPER" in upper or in_token_block
            )
            for token in tokens:
                if token in upper and not safe:
                    hits.append(f"{path}:{line_no}:{token}")
            if "AUTO_TRADE" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{path}:{line_no}:AUTO_TRADE_ENABLED")
            if "AUTO_SELL" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{path}:{line_no}:AUTO_SELL_ENABLED")
            if in_token_block and (stripped.endswith("]") or stripped.endswith(")")):
                in_token_block = False
    return hits


def file_set(root: Path) -> set[str]:
    out: set[str] = set()
    for name in ["scripts", "outputs", "state", "archive", "logs", ".venv", ".git", "configs"]:
        base = root / name
        if not base.exists():
            continue
        for dirpath, _, filenames in os.walk(base):
            for filename in filenames:
                p = Path(dirpath) / filename
                try:
                    if p.is_file():
                        out.add(str(p.resolve()))
                except OSError:
                    pass
    return out


def references(root: Path, filename: str) -> str:
    refs: List[str] = []
    for base_rel in ["outputs/v18/read_center", "outputs/v18/ops"]:
        base = root / base_rel
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.stat().st_size > 5 * 1024 * 1024:
                continue
            if filename in read_text(p):
                refs.append(rel(root, p))
    return ";".join(sorted(set(refs)))


def classify(path: Path) -> Tuple[str, str]:
    name = path.name.upper()
    suffix = path.suffix.lower()
    if "CURRENT" in name:
        return "CURRENT_ALIAS", "Filename contains CURRENT"
    if "READ_FIRST" in name:
        return "LATEST_READ_FIRST_OR_RUN_SUMMARY", "Read-first output"
    if suffix in {".tmp", ".log"}:
        return "LOG_TEMP_INTERMEDIATE", "Log/temp/intermediate extension"
    return "HISTORICAL_VERSIONED", "Versioned or historical generated output"


def plan_target(root: Path, path: Path, category: str) -> str:
    if category != "CURRENT_ALIAS":
        return ""
    target = root / "outputs/v18/technical_timing_backtest_current" / path.name
    return rel(root, target)


def build(root: Path, apply: bool) -> int:
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    target = root / "outputs/v18/technical_timing_backtest"
    ensure_dir(ops)
    files_before = file_set(root)
    stable_before = stable_baseline(root)
    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)

    audit_rows: List[Dict[str, object]] = []
    plan_rows: List[Dict[str, object]] = []
    size_rows: List[Dict[str, object]] = []
    total_bytes = current_bytes = historical_bytes = intermediate_bytes = 0
    current_count = historical_count = intermediate_count = 0

    for p in sorted(target.rglob("*")) if target.exists() else []:
        if not p.is_file():
            continue
        st = p.stat()
        total_bytes += st.st_size
        category, reason = classify(p)
        ref = references(root, p.name)
        archiveable = category != "CURRENT_ALIAS"
        if category == "CURRENT_ALIAS":
            current_count += 1
            current_bytes += st.st_size
        elif category == "LOG_TEMP_INTERMEDIATE":
            intermediate_count += 1
            intermediate_bytes += st.st_size
        else:
            historical_count += 1
            historical_bytes += st.st_size
        audit_rows.append({
            "path": str(p.resolve()),
            "relative_path": rel(root, p),
            "file_name": p.name,
            "file_size_bytes": st.st_size,
            "file_size_mb": mb(st.st_size),
            "modified_time": dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            "contains_current_in_filename": str("CURRENT" in p.name.upper()).upper(),
            "referenced_by_current_read_center_or_ops": str(bool(ref)).upper(),
            "reference_paths": ref,
            "classification": category,
            "protected": str(category == "CURRENT_ALIAS").upper(),
            "protected_reason": reason if category == "CURRENT_ALIAS" else "",
            "archiveable_after_externalization": str(archiveable).upper(),
            "notes": reason,
        })
        if category == "CURRENT_ALIAS":
            plan_rows.append({
                "source_path": str(p.resolve()),
                "source_relative_path": rel(root, p),
                "target_relative_path": plan_target(root, p, category),
                "action": "COPY_ALIAS_TO_EXTERNAL_CURRENT_FOLDER",
                "apply": str(apply).upper(),
                "copied": "FALSE",
                "moved": "FALSE",
                "deleted": "FALSE",
                "required_before_archive": "TRUE",
                "notes": "DRYRUN only; no copy or move performed.",
            })

    size_rows.extend([
        {"metric": "TOTAL_BACKTEST_DIR_SIZE_MB", "value": mb(total_bytes)},
        {"metric": "TOTAL_BACKTEST_FILE_COUNT", "value": str(len(audit_rows))},
        {"metric": "CURRENT_FILE_COUNT", "value": str(current_count)},
        {"metric": "CURRENT_FILE_MB", "value": mb(current_bytes)},
        {"metric": "HISTORICAL_FILE_COUNT", "value": str(historical_count)},
        {"metric": "HISTORICAL_FILE_MB", "value": mb(historical_bytes)},
        {"metric": "LOG_TEMP_INTERMEDIATE_FILE_COUNT", "value": str(intermediate_count)},
        {"metric": "LOG_TEMP_INTERMEDIATE_FILE_MB", "value": mb(intermediate_bytes)},
        {"metric": "ARCHIVEABLE_AFTER_EXTERNALIZATION_COUNT", "value": str(historical_count + intermediate_count)},
        {"metric": "ARCHIVEABLE_AFTER_EXTERNALIZATION_MB", "value": mb(historical_bytes + intermediate_bytes)},
    ])

    paths = {
        "audit": ops / "V18_18E_CURRENT_TECHNICAL_TIMING_BACKTEST_PROTECTION_AUDIT.csv",
        "plan": ops / "V18_18E_CURRENT_ALIAS_EXTERNALIZATION_PLAN.csv",
        "size": ops / "V18_18E_CURRENT_TECHNICAL_TIMING_BACKTEST_SIZE_AUDIT.csv",
        "report": ops / "V18_18E_CURRENT_EXTERNALIZATION_REPORT.md",
        "read": ops / "V18_18E_READ_FIRST.txt",
    }
    write_csv(paths["audit"], audit_rows, [
        "path", "relative_path", "file_name", "file_size_bytes", "file_size_mb", "modified_time",
        "contains_current_in_filename", "referenced_by_current_read_center_or_ops", "reference_paths",
        "classification", "protected", "protected_reason", "archiveable_after_externalization", "notes",
    ])
    write_csv(paths["plan"], plan_rows, [
        "source_path", "source_relative_path", "target_relative_path", "action", "apply",
        "copied", "moved", "deleted", "required_before_archive", "notes",
    ])
    write_csv(paths["size"], size_rows, ["metric", "value"])

    files_after = file_set(root)
    deleted_count = len(files_before - files_after)
    own_output_paths = {str(p.resolve()) for p in paths.values()}
    copied_count = len((files_after - files_before) - own_output_paths)
    moved_count = 0
    current_daily_modified = sha256(current_daily) != current_daily_before
    snapshots_modified = stable_modified(stable_before, root)
    ps_ok, _ = parse_ps(root / "scripts/v18/run_v18_18E_technical_timing_current_alias_externalization_audit.ps1")
    py_ok, _ = compile_py(root / "scripts/v18/v18_18E_technical_timing_current_alias_externalization_audit.py")
    hits = dangerous_hits([
        root / "scripts/v18/run_v18_18E_technical_timing_current_alias_externalization_audit.ps1",
        root / "scripts/v18/v18_18E_technical_timing_current_alias_externalization_audit.py",
        *paths.values(),
    ])
    validations = [
        ps_ok, py_ok, deleted_count == 0, copied_count == 0, moved_count == 0,
        not current_daily_modified, not snapshots_modified, len(hits) == 0,
    ]
    validation_fail = sum(1 for ok in validations if not ok)
    values = {
        "STATUS": STATUS_OK if validation_fail == 0 else STATUS_WARN,
        "MODE": MODE,
        "TOTAL_BACKTEST_DIR_SIZE_MB": mb(total_bytes),
        "TOTAL_BACKTEST_FILE_COUNT": str(len(audit_rows)),
        "CURRENT_FILE_COUNT": str(current_count),
        "CURRENT_FILE_MB": mb(current_bytes),
        "HISTORICAL_FILE_COUNT": str(historical_count),
        "HISTORICAL_FILE_MB": mb(historical_bytes),
        "ARCHIVEABLE_AFTER_EXTERNALIZATION_COUNT": str(historical_count + intermediate_count),
        "ARCHIVEABLE_AFTER_EXTERNALIZATION_MB": mb(historical_bytes + intermediate_bytes),
        "EXTERNALIZATION_NEEDED": str(current_count > 0 and (historical_count + intermediate_count) > 0).upper(),
        "APPLY": str(apply).upper(),
        "DELETED_COUNT": str(deleted_count),
        "MOVED_COUNT": str(moved_count),
        "COPIED_COUNT": str(copied_count),
        "VALIDATION_FAIL_COUNT": str(validation_fail),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }
    report = [
        "# V18.18E Technical Timing Backtest Current Alias Externalization Audit", "",
        "## Summary", "",
        *[f"- {k}: {v}" for k, v in values.items()],
        "", "## Current Files Protecting Directory", "",
        *[f"- {r['relative_path']}: {r['file_size_mb']} MB" for r in audit_rows if r["classification"] == "CURRENT_ALIAS"],
        "", "## Archiveable After Externalization", "",
        *[f"- {r['relative_path']}: {r['file_size_mb']} MB, class={r['classification']}" for r in audit_rows if r["archiveable_after_externalization"] == "TRUE"],
        "", "## Proposed Externalization Target", "",
        "- outputs/v18/technical_timing_backtest_current/",
        "", "## Notes", "",
        "- DRYRUN only; no files were copied, moved, archived, or deleted.",
        "- The externalization plan mirrors CURRENT aliases to a dedicated current folder before any later archive cleanup.",
        "", "## Guardrails", "",
        f"AUTO_TRADE: {AUTO_TRADE}; AUTO_SELL: {AUTO_SELL}; OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}.",
    ]
    write_text(paths["report"], "\n".join(report) + "\n")
    write_text(paths["read"], "\n".join(f"{k}: {v}" for k, v in values.items()) + "\n")

    for key in [
        "STATUS", "TOTAL_BACKTEST_DIR_SIZE_MB", "CURRENT_FILE_COUNT", "CURRENT_FILE_MB",
        "HISTORICAL_FILE_COUNT", "HISTORICAL_FILE_MB", "ARCHIVEABLE_AFTER_EXTERNALIZATION_MB",
        "VALIDATION_FAIL_COUNT", "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT",
    ]:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    return build(Path(args.root), args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
