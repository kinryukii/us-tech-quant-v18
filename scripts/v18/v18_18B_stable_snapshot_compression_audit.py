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
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_DRYRUN = "OK_V18_18B_COMPRESSION_AUDIT_READY"
STATUS_APPLY = "OK_V18_18B_COMPRESSION_APPLIED"
STATUS_WARN = "WARN_V18_18B_COMPRESSION_AUDIT_VALIDATION_FAILED"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
LATEST_STABLE_NAME = "V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357"


def parse_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def mb(size: int | float) -> float:
    return float(size) / (1024 * 1024)


def fmt_mb(size: int | float) -> str:
    return f"{mb(size):.3f}"


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


def dir_size_and_count(path: Path) -> Tuple[int, int, float]:
    total = 0
    count = 0
    latest = path.stat().st_mtime if path.exists() else 0.0
    for p in all_files(path):
        try:
            st = p.stat()
        except OSError:
            continue
        total += st.st_size
        count += 1
        latest = max(latest, st.st_mtime)
    return total, count, latest


def repo_size(root: Path) -> int:
    total = 0
    for name in ["scripts", "outputs", "state", "archive", "logs", ".venv", ".git", "configs"]:
        base = root / name
        if base.exists():
            total += dir_size_and_count(base)[0]
    return total


def stable_snapshots(root: Path) -> List[Path]:
    base = root / "archive/stable"
    if not base.exists():
        return []
    return sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)


def infer_version(name: str) -> str:
    match = re.search(r"V18[_-]\d+[A-Z]?(?:[_-]P\d+)?(?:[_-]R\d+)?", name, flags=re.IGNORECASE)
    return match.group(0).replace("-", "_").upper() if match else ""


def estimate_zip_size(size_bytes: int) -> int:
    # Stable snapshots are mostly CSV/text with some repeated payloads; use a conservative estimate for planning only.
    return int(size_bytes * 0.55)


def zip_directory(src: Path, dst: Path) -> Tuple[bool, str, int]:
    ensure_dir(dst.parent)
    try:
        with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            for p in all_files(src):
                zf.write(p, arcname=str(Path(src.name) / p.relative_to(src)))
        if not dst.exists() or dst.stat().st_size <= 0:
            return False, "ZIP_NOT_CREATED_OR_EMPTY", 0
        with zipfile.ZipFile(dst, "r") as zf:
            bad = zf.testzip()
            if bad:
                return False, f"ZIP_TEST_FAILED:{bad}", dst.stat().st_size
            if len(zf.namelist()) == 0:
                return False, "ZIP_EMPTY_LISTING", dst.stat().st_size
        return True, "ZIP_VERIFIED", dst.stat().st_size
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}", 0


def is_current_alias(path: Path) -> bool:
    name = path.name.upper()
    return "CURRENT" in name or "READ_FIRST" in name


def has_current_alias(path: Path) -> bool:
    if path.is_file():
        return is_current_alias(path)
    for p in all_files(path):
        if is_current_alias(p):
            return True
    return False


def output_scan_roots(root: Path) -> List[Path]:
    return [root / p for p in ["outputs/v18", "outputs/v17", "outputs/v16", "outputs/v15"] if (root / p).exists()]


def large_output_candidates(root: Path, threshold_mb: float, archive_root: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    seen: set[str] = set()
    threshold_bytes = int(threshold_mb * 1024 * 1024)
    for base in output_scan_roots(root):
        for child in base.rglob("*"):
            try:
                if child.is_dir():
                    size, count, latest = dir_size_and_count(child)
                    if size >= threshold_bytes:
                        key = str(child.resolve())
                        if key not in seen:
                            seen.add(key)
                            rows.append({
                                "path": str(child.resolve()),
                                "relative_path": rel(root, child),
                                "size_mb": f"{mb(size):.3f}",
                                "file_count": count,
                                "latest_modified_time": dt.datetime.fromtimestamp(latest).isoformat(timespec="seconds"),
                                "current_alias_present": str(has_current_alias(child)).upper(),
                                "protected_status": "PROTECTED_CURRENT_ALIAS_PRESENT" if has_current_alias(child) else "UNPROTECTED_ARCHIVE_CANDIDATE",
                                "archive_candidate": "TRUE",
                                "proposed_archive_path": rel(root, archive_root / (rel(root, child).replace("/", "__") + ".zip")),
                                "notes": "Large generated output directory; archive-only candidate, no original deletion implemented.",
                            })
                elif child.is_file() and child.stat().st_size >= threshold_bytes:
                    rows.append({
                        "path": str(child.resolve()),
                        "relative_path": rel(root, child),
                        "size_mb": f"{mb(child.stat().st_size):.3f}",
                        "file_count": 1,
                        "latest_modified_time": dt.datetime.fromtimestamp(child.stat().st_mtime).isoformat(timespec="seconds"),
                        "current_alias_present": str(is_current_alias(child)).upper(),
                        "protected_status": "PROTECTED_CURRENT_ALIAS" if is_current_alias(child) else "UNPROTECTED_ARCHIVE_CANDIDATE",
                        "archive_candidate": "TRUE",
                        "proposed_archive_path": rel(root, archive_root / (rel(root, child).replace("/", "__") + ".zip")),
                        "notes": "Large generated output file; archive-only candidate, no original deletion implemented.",
                    })
            except OSError:
                pass
    rows.sort(key=lambda r: float(r["size_mb"]), reverse=True)
    return rows


def file_set(root: Path) -> set[str]:
    out: set[str] = set()
    for name in ["scripts", "outputs", "state", "archive", "logs", ".venv", ".git", "configs"]:
        base = root / name
        if base.exists():
            out.update(str(p.resolve()) for p in all_files(base))
    return out


def build(root: Path, args: argparse.Namespace) -> int:
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    ensure_dir(ops)
    apply = bool(args.apply)
    mode = "APPLY" if apply else "DRYRUN"
    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)
    stable_before = stable_baseline(root)
    files_before = file_set(root)

    stable_zip_root = root / args.stable_zip_root
    output_archive_root = root / args.output_archive_root
    snapshots = stable_snapshots(root)
    keep_count = max(1, args.keep_latest_stable_snapshots)
    keep_set = {p.resolve() for p in snapshots[:keep_count]}
    latest_stable = root / "archive/stable" / LATEST_STABLE_NAME
    if latest_stable.exists():
        keep_set.add(latest_stable.resolve())

    stable_rows: List[Dict[str, object]] = []
    compression_rows: List[Dict[str, object]] = []
    stable_zip_created_count = 0
    stable_zip_created_bytes = 0
    stable_original_deleted_count = 0
    stable_original_deleted_bytes = 0

    for snap in snapshots:
        size, count, latest = dir_size_and_count(snap)
        is_latest = snap.resolve() == snapshots[0].resolve() if snapshots else False
        keep = snap.resolve() in keep_set
        candidate = bool(args.compress_old_stable_snapshots and not keep)
        zip_path = stable_zip_root / f"{snap.name}.zip"
        estimated_zip = estimate_zip_size(size)
        row = {
            "folder_path": str(snap.resolve()),
            "folder_name": snap.name,
            "inferred_version": infer_version(snap.name),
            "created_or_modified_time": dt.datetime.fromtimestamp(latest).isoformat(timespec="seconds"),
            "total_size_mb": f"{mb(size):.3f}",
            "file_count": count,
            "has_manifest": str((snap / "MANIFEST.csv").exists()).upper(),
            "has_validation": str((snap / "VALIDATION.csv").exists()).upper(),
            "has_readme": str(any(p.name.upper().startswith("README") for p in snap.glob("*"))).upper(),
            "has_restore_script": str(any(p.name.upper().startswith("RESTORE") and p.suffix.lower() == ".ps1" for p in snap.glob("*"))).upper(),
            "is_latest_snapshot": str(is_latest).upper(),
            "keep_uncompressed": str(keep).upper(),
            "compression_candidate": str(candidate).upper(),
            "proposed_zip_path": str(zip_path.resolve()),
            "proposed_action": "COMPRESS_TO_ZIP" if candidate else "KEEP_UNCOMPRESSED",
            "estimated_zip_size_mb": f"{mb(estimated_zip):.3f}",
            "estimated_savings_mb": f"{mb(max(0, size - estimated_zip)):.3f}",
            "safety_status": "PROTECTED_KEEP_SET" if keep else "SAFE_COMPRESSION_CANDIDATE",
            "notes": "",
        }
        if candidate:
            comp = {
                "candidate_type": "STABLE_SNAPSHOT",
                "source_path": str(snap.resolve()),
                "relative_path": rel(root, snap),
                "source_size_mb": row["total_size_mb"],
                "file_count": count,
                "proposed_zip_path": str(zip_path.resolve()),
                "estimated_zip_size_mb": row["estimated_zip_size_mb"],
                "estimated_savings_mb": row["estimated_savings_mb"],
                "apply": str(apply).upper(),
                "zip_created": "FALSE",
                "zip_verified": "FALSE",
                "original_deleted": "FALSE",
                "delete_original_requested": str(args.delete_original_after_verified_zip).upper(),
                "error": "",
            }
            if apply:
                ok, note, zip_size = zip_directory(snap, zip_path)
                comp["zip_created"] = str(ok).upper()
                comp["zip_verified"] = str(ok).upper()
                comp["error"] = "" if ok else note
                if ok:
                    stable_zip_created_count += 1
                    stable_zip_created_bytes += zip_size
                    comp["estimated_zip_size_mb"] = f"{mb(zip_size):.3f}"
                    if args.delete_original_after_verified_zip and snap.resolve() not in keep_set:
                        try:
                            shutil.rmtree(snap)
                            stable_original_deleted_count += 1
                            stable_original_deleted_bytes += size
                            comp["original_deleted"] = "TRUE"
                        except Exception as exc:
                            comp["error"] = f"DELETE_FAILED:{type(exc).__name__}: {exc}"
            compression_rows.append(comp)
        stable_rows.append(row)

    large_rows = large_output_candidates(root, args.large_output_threshold_mb, output_archive_root)
    output_zip_created_count = 0
    output_zip_created_bytes = 0
    if apply and args.archive_large_outputs:
        for row in large_rows:
            src = Path(str(row["path"]))
            dst = root / str(row["proposed_archive_path"]).replace("/", os.sep)
            if src.is_dir():
                ok, note, zip_size = zip_directory(src, dst)
            else:
                ensure_dir(dst.parent)
                try:
                    with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
                        zf.write(src, arcname=src.name)
                    with zipfile.ZipFile(dst, "r") as zf:
                        bad = zf.testzip()
                    ok = dst.exists() and dst.stat().st_size > 0 and bad is None
                    note = "ZIP_VERIFIED" if ok else "ZIP_TEST_FAILED"
                    zip_size = dst.stat().st_size if dst.exists() else 0
                except Exception as exc:
                    ok, note, zip_size = False, f"{type(exc).__name__}: {exc}", 0
            row["notes"] = f"{row['notes']} {note}".strip()
            if ok:
                output_zip_created_count += 1
                output_zip_created_bytes += zip_size

    paths = {
        "stable": ops / "V18_18B_CURRENT_STABLE_SNAPSHOT_SIZE_AUDIT.csv",
        "candidates": ops / "V18_18B_CURRENT_COMPRESSION_CANDIDATES.csv",
        "large": ops / "V18_18B_CURRENT_LARGE_OUTPUT_SIZE_AUDIT.csv",
        "report": ops / "V18_18B_CURRENT_COMPRESSION_REPORT.md",
        "read": ops / "V18_18B_READ_FIRST.txt",
    }
    write_csv(paths["stable"], stable_rows, [
        "folder_path", "folder_name", "inferred_version", "created_or_modified_time", "total_size_mb", "file_count",
        "has_manifest", "has_validation", "has_readme", "has_restore_script", "is_latest_snapshot",
        "keep_uncompressed", "compression_candidate", "proposed_zip_path", "proposed_action",
        "estimated_zip_size_mb", "estimated_savings_mb", "safety_status", "notes",
    ])
    write_csv(paths["candidates"], compression_rows, [
        "candidate_type", "source_path", "relative_path", "source_size_mb", "file_count", "proposed_zip_path",
        "estimated_zip_size_mb", "estimated_savings_mb", "apply", "zip_created", "zip_verified",
        "original_deleted", "delete_original_requested", "error",
    ])
    write_csv(paths["large"], large_rows, [
        "path", "relative_path", "size_mb", "file_count", "latest_modified_time", "current_alias_present",
        "protected_status", "archive_candidate", "proposed_archive_path", "notes",
    ])
    shutil.copy2(paths["stable"], ops / "V18_CURRENT_STABLE_SNAPSHOT_SIZE_AUDIT.csv")
    shutil.copy2(paths["candidates"], ops / "V18_CURRENT_COMPRESSION_CANDIDATES.csv")

    current_daily_modified = sha256(current_daily) != current_daily_before
    snapshots_modified = stable_modified(stable_before, root)
    files_after = file_set(root)
    deleted_files = files_before - files_after
    source_deleted = sum(1 for p in deleted_files if "/scripts/" in p.replace("\\", "/").lower() or p.lower().endswith((".py", ".ps1")))
    alias_deleted = sum(1 for p in deleted_files if is_current_alias(Path(p)))
    manual_deleted = sum(1 for p in deleted_files if p.replace("\\", "/").lower().endswith(("state/v18/manual/v18_manual_positions.csv", "state/v18/manual/v18_manual_trade_log.csv")))
    price_deleted = sum(1 for p in deleted_files if "/state/v18/price_cache/" in p.replace("\\", "/").lower())

    ps_ok, _ = parse_ps(root / "scripts/v18/run_v18_18B_stable_snapshot_compression_audit.ps1")
    py_ok, _ = compile_py(root / "scripts/v18/v18_18B_stable_snapshot_compression_audit.py")
    hits = dangerous_hits([root / "scripts/v18/run_v18_18B_stable_snapshot_compression_audit.ps1", root / "scripts/v18/v18_18B_stable_snapshot_compression_audit.py", *paths.values()])

    latest_protected = bool(snapshots and snapshots[0].resolve() in keep_set)
    v18_16g_protected = latest_stable.exists() and latest_stable.resolve() in keep_set
    stable_candidate_mb = sum(float(r["source_size_mb"]) for r in compression_rows)
    est_zip_mb = sum(float(r["estimated_zip_size_mb"]) for r in compression_rows)
    large_candidate_mb = sum(float(r["size_mb"]) for r in large_rows)
    stable_size_mb = sum(float(r["total_size_mb"]) for r in stable_rows)

    validation_checks = [
        ps_ok, py_ok, latest_protected, v18_16g_protected,
        source_deleted == 0, alias_deleted == 0, manual_deleted == 0, price_deleted == 0,
        not current_daily_modified, len(hits) == 0,
    ]
    if not apply:
        validation_checks.extend([
            stable_zip_created_count == 0,
            stable_original_deleted_count == 0,
            output_zip_created_count == 0,
            len(deleted_files) == 0,
            not snapshots_modified,
        ])
    validation_fail = sum(1 for ok in validation_checks if not ok)

    values = {
        "STATUS": (STATUS_APPLY if apply else STATUS_DRYRUN) if validation_fail == 0 else STATUS_WARN,
        "MODE": mode,
        "APPLY": str(apply).upper(),
        "KEEP_LATEST_STABLE_SNAPSHOTS": str(keep_count),
        "DELETE_ORIGINAL_AFTER_VERIFIED_ZIP": str(args.delete_original_after_verified_zip).upper(),
        "ARCHIVE_LARGE_OUTPUTS": str(args.archive_large_outputs).upper(),
        "TOTAL_SIZE_MB_BEFORE": fmt_mb(repo_size(root)),
        "ARCHIVE_STABLE_SIZE_MB": f"{stable_size_mb:.3f}",
        "STABLE_SNAPSHOT_FOLDER_COUNT": str(len(stable_rows)),
        "STABLE_COMPRESSION_CANDIDATE_COUNT": str(len(compression_rows)),
        "STABLE_COMPRESSION_CANDIDATE_MB": f"{stable_candidate_mb:.3f}",
        "ESTIMATED_STABLE_ZIP_SIZE_MB": f"{est_zip_mb:.3f}",
        "ESTIMATED_STABLE_SAVINGS_MB": f"{max(0.0, stable_candidate_mb - est_zip_mb):.3f}",
        "STABLE_ZIP_CREATED_COUNT": str(stable_zip_created_count),
        "STABLE_ZIP_CREATED_MB": fmt_mb(stable_zip_created_bytes),
        "STABLE_ORIGINAL_DELETED_COUNT": str(stable_original_deleted_count),
        "STABLE_ORIGINAL_DELETED_MB": fmt_mb(stable_original_deleted_bytes),
        "LARGE_OUTPUT_CANDIDATE_COUNT": str(len(large_rows)),
        "LARGE_OUTPUT_CANDIDATE_MB": f"{large_candidate_mb:.3f}",
        "OUTPUT_ZIP_CREATED_COUNT": str(output_zip_created_count),
        "OUTPUT_ZIP_CREATED_MB": fmt_mb(output_zip_created_bytes),
        "OUTPUT_ORIGINAL_DELETED_COUNT": "0",
        "OUTPUT_ORIGINAL_DELETED_MB": "0.000",
        "SOURCE_CODE_DELETED_COUNT": str(source_deleted),
        "CURRENT_ALIAS_DELETED_COUNT": str(alias_deleted),
        "MANUAL_STATE_DELETED_COUNT": str(manual_deleted),
        "PRICE_CACHE_DELETED_COUNT": str(price_deleted),
        "LATEST_STABLE_SNAPSHOT_PROTECTED": str(latest_protected).upper(),
        "V18_16G_R1_PROTECTED": str(v18_16g_protected).upper(),
        "CURRENT_DAILY_MODIFIED": str(current_daily_modified).upper(),
        "STABLE_SNAPSHOT_MODIFIED": str(snapshots_modified).upper(),
        "VALIDATION_FAIL_COUNT": str(validation_fail),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }

    largest_stable = sorted(stable_rows, key=lambda r: float(r["total_size_mb"]), reverse=True)[:20]
    largest_outputs = large_rows[:30]
    report = [
        "# V18.18B Stable Snapshot Compression and Large Output Archive Audit", "",
        "## Summary", "",
        *[f"- {k}: {v}" for k, v in values.items()],
        "", "## Stable Snapshot Candidates", "",
        *[f"- {r['folder_name']}: {r['total_size_mb']} MB, candidate={r['compression_candidate']}, action={r['proposed_action']}" for r in largest_stable],
        "", "## Large Output Candidates", "",
        *[f"- {r['relative_path']}: {r['size_mb']} MB, protected={r['protected_status']}" for r in largest_outputs],
        "", "## Safety Notes", "",
        "- DRYRUN creates no zip files and deletes nothing.",
        "- Stable snapshot originals are never deleted unless both -Apply and -DeleteOriginalAfterVerifiedZip are passed.",
        "- Output originals are not deleted by this first V18.18B version.",
        "", "## Apply Commands", "",
        "- Compression only: powershell -NoProfile -ExecutionPolicy Bypass -File \"D:\\us-tech-quant\\scripts\\v18\\run_v18_18B_stable_snapshot_compression_audit.ps1\" -Apply",
        "- Compression with old stable original deletion after verified zip: powershell -NoProfile -ExecutionPolicy Bypass -File \"D:\\us-tech-quant\\scripts\\v18\\run_v18_18B_stable_snapshot_compression_audit.ps1\" -Apply -DeleteOriginalAfterVerifiedZip",
        "", "## Guardrails", "",
        f"AUTO_TRADE: {AUTO_TRADE}; AUTO_SELL: {AUTO_SELL}; OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}.",
    ]
    write_text(paths["report"], "\n".join(report) + "\n")
    write_text(paths["read"], "\n".join(f"{k}: {v}" for k, v in values.items()) + "\n")
    shutil.copy2(paths["read"], ops / "V18_CURRENT_COMPRESSION_AUDIT_READ_FIRST.txt")

    for key in [
        "STATUS", "MODE", "ARCHIVE_STABLE_SIZE_MB", "STABLE_SNAPSHOT_FOLDER_COUNT",
        "STABLE_COMPRESSION_CANDIDATE_COUNT", "STABLE_COMPRESSION_CANDIDATE_MB",
        "ESTIMATED_STABLE_ZIP_SIZE_MB", "ESTIMATED_STABLE_SAVINGS_MB",
        "LARGE_OUTPUT_CANDIDATE_COUNT", "LARGE_OUTPUT_CANDIDATE_MB",
        "VALIDATION_FAIL_COUNT", "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT",
    ]:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--keep-latest-stable-snapshots", type=int, default=5)
    parser.add_argument("--compress-old-stable-snapshots", type=parse_bool, default=True)
    parser.add_argument("--delete-original-after-verified-zip", action="store_true")
    parser.add_argument("--archive-large-outputs", type=parse_bool, default=False)
    parser.add_argument("--large-output-threshold-mb", type=float, default=25.0)
    parser.add_argument("--output-archive-root", default="archive/generated_outputs_compressed")
    parser.add_argument("--stable-zip-root", default="archive/stable_compressed")
    args = parser.parse_args()
    return build(Path(args.root), args)


if __name__ == "__main__":
    raise SystemExit(main())
