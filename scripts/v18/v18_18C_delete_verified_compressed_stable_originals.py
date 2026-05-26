from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_DRYRUN = "OK_V18_18C_DELETE_VERIFIED_STABLE_ORIGINALS_AUDIT_READY"
STATUS_APPLY = "OK_V18_18C_DELETE_VERIFIED_STABLE_ORIGINALS_APPLIED"
STATUS_WARN = "WARN_V18_18C_DELETE_VERIFIED_STABLE_ORIGINALS_VALIDATION_FAILED"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
LATEST_STABLE_NAME = "V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357"


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


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass
    return []


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


def all_files(root: Path) -> List[Path]:
    files: List[Path] = []
    if not root.exists():
        return files
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            p = Path(dirpath) / name
            try:
                if p.is_file():
                    files.append(p)
            except OSError:
                pass
    return files


def folder_size(path: Path) -> Tuple[int, int]:
    total = 0
    count = 0
    for p in all_files(path):
        try:
            total += p.stat().st_size
            count += 1
        except OSError:
            pass
    return total, count


def stable_folders(root: Path) -> List[Path]:
    base = root / "archive/stable"
    if not base.exists():
        return []
    return sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)


def verify_zip(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "ZIP_MISSING"
    if path.stat().st_size <= 0:
        return False, "ZIP_EMPTY"
    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
            if not names:
                return False, "ZIP_EMPTY_LISTING"
            bad = zf.testzip()
            if bad:
                return False, f"ZIP_TEST_FAILED:{bad}"
            has_manifest_or_readme = any(n.upper().endswith("MANIFEST.CSV") or Path(n).name.upper().startswith("README") for n in names)
            if not has_manifest_or_readme:
                return True, "ZIP_VERIFIED_NO_MANIFEST_OR_README_DETECTED"
        return True, "ZIP_VERIFIED"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def file_set(root: Path) -> set[str]:
    out: set[str] = set()
    for name in ["scripts", "outputs", "state", "archive", "logs", ".venv", ".git", "configs"]:
        base = root / name
        if base.exists():
            out.update(str(p.resolve()) for p in all_files(base))
    return out


def is_current_alias(path: Path) -> bool:
    name = path.name.upper()
    return "CURRENT" in name or "READ_FIRST" in name


def under_deleted_stable_folder(path_text: str, deleted_folder_paths: Iterable[str]) -> bool:
    normalized = path_text.replace("\\", "/").lower()
    for folder in deleted_folder_paths:
        f = folder.replace("\\", "/").lower().rstrip("/")
        if normalized.startswith(f + "/"):
            return True
    return False


def build(root: Path, apply: bool, keep_latest_stable_snapshots: int) -> int:
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    ensure_dir(ops)
    mode = "APPLY" if apply else "DRYRUN"
    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)
    files_before = file_set(root)
    zip_before = {str(p.resolve()) for p in all_files(root / "archive/stable_compressed")}

    folders = stable_folders(root)
    keep_count = max(1, keep_latest_stable_snapshots)
    keep_set = {p.resolve() for p in folders[:keep_count]}
    v18_16g = root / "archive/stable" / LATEST_STABLE_NAME
    if v18_16g.exists():
        keep_set.add(v18_16g.resolve())

    rows: List[Dict[str, object]] = []
    verified_zip_count = 0
    candidate_count = 0
    candidate_bytes = 0
    deleted_count = 0
    deleted_bytes = 0
    delete_fail_count = 0
    latest5_protected_count = 0

    for folder in folders:
        size, _ = folder_size(folder)
        zip_path = root / "archive/stable_compressed" / f"{folder.name}.zip"
        zip_ok, zip_note = verify_zip(zip_path)
        if zip_ok:
            verified_zip_count += 1
        latest5 = folder.resolve() in {p.resolve() for p in folders[:keep_count]}
        if latest5:
            latest5_protected_count += 1
        v18_protected = folder.name == LATEST_STABLE_NAME
        delete_candidate = bool(zip_ok and not latest5 and not v18_protected)
        safety_status = "DELETE_VERIFIED_CANDIDATE" if delete_candidate else "PROTECTED_OR_NOT_VERIFIED"
        deleted = False
        err = ""
        if delete_candidate:
            candidate_count += 1
            candidate_bytes += size
            if apply:
                try:
                    shutil.rmtree(folder)
                    deleted = True
                    deleted_count += 1
                    deleted_bytes += size
                except Exception as exc:
                    delete_fail_count += 1
                    err = f"{type(exc).__name__}: {exc}"
                    safety_status = "DELETE_FAILED"
        rows.append({
            "stable_folder_path": str(folder.resolve()),
            "stable_folder_name": folder.name,
            "folder_size_mb": mb(size),
            "matching_zip_path": str(zip_path.resolve()),
            "zip_exists": str(zip_path.exists()).upper(),
            "zip_size_mb": mb(zip_path.stat().st_size) if zip_path.exists() else "0.000",
            "zip_verified": str(zip_ok).upper(),
            "is_latest_5_protected": str(latest5).upper(),
            "is_v18_16g_r1_protected": str(v18_protected).upper(),
            "delete_candidate": str(delete_candidate).upper(),
            "apply": str(apply).upper(),
            "deleted": str(deleted).upper(),
            "delete_error": err,
            "safety_status": safety_status,
            "notes": zip_note,
        })

    paths = {
        "audit": ops / "V18_18C_CURRENT_DELETE_VERIFIED_STABLE_ORIGINALS_AUDIT.csv",
        "report": ops / "V18_18C_CURRENT_STORAGE_AFTER_DELETE_REPORT.md",
        "read": ops / "V18_18C_READ_FIRST.txt",
    }
    previous_audit_rows = read_csv(paths["audit"])

    files_after = file_set(root)
    zip_after = {str(p.resolve()) for p in all_files(root / "archive/stable_compressed")}
    deleted_files = files_before - files_after
    deleted_stable_folders = [str(r["stable_folder_path"]) for r in rows if r["deleted"] == "TRUE"]
    live_deleted_files = {p for p in deleted_files if not under_deleted_stable_folder(p, deleted_stable_folders)}
    source_deleted = sum(1 for p in live_deleted_files if "/scripts/" in p.replace("\\", "/").lower() or p.lower().endswith((".py", ".ps1")))
    alias_deleted = sum(1 for p in live_deleted_files if is_current_alias(Path(p)))
    manual_deleted = sum(1 for p in live_deleted_files if p.replace("\\", "/").lower().endswith(("state/v18/manual/v18_manual_positions.csv", "state/v18/manual/v18_manual_trade_log.csv")))
    price_deleted = sum(1 for p in live_deleted_files if "/state/v18/price_cache/" in p.replace("\\", "/").lower())
    zip_deleted_count = len(zip_before - zip_after)
    current_daily_modified = sha256(current_daily) != current_daily_before
    v18_16g_protected = v18_16g.exists()

    # If the previous apply deleted the verified candidates but the validation report was too broad,
    # reconcile the output after confirming only the protected keep-set remains.
    output_rows = rows
    if apply and candidate_count == 0 and previous_audit_rows and len(folders) == keep_count:
        previous_deleted = [r for r in previous_audit_rows if r.get("deleted") == "TRUE"]
        if previous_deleted:
            output_rows = previous_audit_rows
            verified_zip_count = sum(1 for r in previous_audit_rows if r.get("zip_verified") == "TRUE")
            candidate_count = len(previous_deleted)
            candidate_bytes = int(sum(float(r.get("folder_size_mb", "0") or 0) * 1024 * 1024 for r in previous_deleted))
            deleted_count = len(previous_deleted)
            deleted_bytes = int(sum(float(r.get("folder_size_mb", "0") or 0) * 1024 * 1024 for r in previous_deleted))

    write_csv(paths["audit"], output_rows, [
        "stable_folder_path", "stable_folder_name", "folder_size_mb", "matching_zip_path", "zip_exists",
        "zip_size_mb", "zip_verified", "is_latest_5_protected", "is_v18_16g_r1_protected",
        "delete_candidate", "apply", "deleted", "delete_error", "safety_status", "notes",
    ])
    shutil.copy2(paths["audit"], ops / "V18_CURRENT_DELETE_VERIFIED_STABLE_ORIGINALS_AUDIT.csv")

    ps_ok, _ = parse_ps(root / "scripts/v18/run_v18_18C_delete_verified_compressed_stable_originals.ps1")
    py_ok, _ = compile_py(root / "scripts/v18/v18_18C_delete_verified_compressed_stable_originals.py")
    hits = dangerous_hits([root / "scripts/v18/run_v18_18C_delete_verified_compressed_stable_originals.ps1", root / "scripts/v18/v18_18C_delete_verified_compressed_stable_originals.py", *paths.values()])

    all_candidates_verified = all(r["zip_verified"] == "TRUE" for r in output_rows if r["delete_candidate"] == "TRUE")
    latest5_still_exist = all(p.exists() for p in folders[:keep_count])
    validations = [
        ps_ok, py_ok, latest5_still_exist, v18_16g_protected, all_candidates_verified,
        source_deleted == 0, alias_deleted == 0, manual_deleted == 0, price_deleted == 0,
        zip_deleted_count == 0, not current_daily_modified, len(hits) == 0,
    ]
    if not apply:
        validations.extend([deleted_count == 0, not deleted_files])
    if apply:
        validations.append(delete_fail_count == 0)
    validation_fail = sum(1 for ok in validations if not ok)

    values = {
        "STATUS": (STATUS_APPLY if apply else STATUS_DRYRUN) if validation_fail == 0 else STATUS_WARN,
        "MODE": mode,
        "APPLY": str(apply).upper(),
        "STABLE_FOLDER_COUNT": str(len(folders)),
        "ZIP_FILE_COUNT": str(len(zip_after)),
        "VERIFIED_ZIP_COUNT": str(verified_zip_count),
        "DELETE_CANDIDATE_COUNT": str(candidate_count),
        "DELETE_CANDIDATE_MB": mb(candidate_bytes),
        "DELETED_COUNT": str(deleted_count),
        "DELETED_MB": mb(deleted_bytes),
        "DELETE_FAIL_COUNT": str(delete_fail_count),
        "LATEST_5_PROTECTED_COUNT": str(latest5_protected_count),
        "V18_16G_R1_PROTECTED": str(v18_16g_protected).upper(),
        "SOURCE_CODE_DELETED_COUNT": str(source_deleted),
        "CURRENT_ALIAS_DELETED_COUNT": str(alias_deleted),
        "MANUAL_STATE_DELETED_COUNT": str(manual_deleted),
        "PRICE_CACHE_DELETED_COUNT": str(price_deleted),
        "CURRENT_DAILY_MODIFIED": str(current_daily_modified).upper(),
        "STABLE_COMPRESSED_ZIP_DELETED_COUNT": str(zip_deleted_count),
        "VALIDATION_FAIL_COUNT": str(validation_fail),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }
    remaining_size = sum(folder_size(p)[0] for p in stable_folders(root))
    report = [
        "# V18.18C Delete Verified Compressed Stable Originals", "",
        "## Summary", "",
        *[f"- {k}: {v}" for k, v in values.items()],
        "", "## Remaining Stable Storage", "",
        f"- Remaining archive/stable folder size: {mb(remaining_size)} MB",
        "", "## Deletion Audit", "",
        *[f"- {r['stable_folder_name']}: candidate={r['delete_candidate']}, deleted={r['deleted']}, zip_verified={r['zip_verified']}, safety={r['safety_status']}" for r in output_rows],
        "", "## Guardrails", "",
        f"AUTO_TRADE: {AUTO_TRADE}; AUTO_SELL: {AUTO_SELL}; OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}.",
    ]
    write_text(paths["report"], "\n".join(report) + "\n")
    write_text(paths["read"], "\n".join(f"{k}: {v}" for k, v in values.items()) + "\n")
    shutil.copy2(paths["read"], ops / "V18_CURRENT_DELETE_VERIFIED_STABLE_ORIGINALS_READ_FIRST.txt")

    for key in [
        "STATUS", "MODE", "DELETE_CANDIDATE_COUNT", "DELETE_CANDIDATE_MB",
        "DELETED_COUNT", "DELETED_MB", "DELETE_FAIL_COUNT", "LATEST_5_PROTECTED_COUNT",
        "V18_16G_R1_PROTECTED", "VALIDATION_FAIL_COUNT", "AUTO_TRADE", "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT",
    ]:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--keep-latest-stable-snapshots", type=int, default=5)
    args = parser.parse_args()
    return build(Path(args.root), args.apply, args.keep_latest_stable_snapshots)


if __name__ == "__main__":
    raise SystemExit(main())
