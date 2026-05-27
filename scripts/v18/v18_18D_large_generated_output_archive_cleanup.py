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


STATUS_DRYRUN = "OK_V18_18D_LARGE_OUTPUT_ARCHIVE_AUDIT_READY"
STATUS_APPLY = "OK_V18_18D_LARGE_OUTPUT_ARCHIVE_APPLIED"
STATUS_DELETE = "OK_V18_18D_LARGE_OUTPUT_VERIFIED_ORIGINALS_DELETED"
STATUS_WARN = "WARN_V18_18D_LARGE_OUTPUT_ARCHIVE_VALIDATION_FAILED"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
ARCHIVE_ROOT = "archive/generated_outputs_compressed"


def parse_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


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


def all_files(path: Path) -> List[Path]:
    files: List[Path] = []
    if not path.exists():
        return files
    for dirpath, _, filenames in os.walk(path):
        for name in filenames:
            p = Path(dirpath) / name
            try:
                if p.is_file():
                    files.append(p)
            except OSError:
                pass
    return files


def size_count_latest(path: Path) -> Tuple[int, int, float]:
    if path.is_file():
        st = path.stat()
        return st.st_size, 1, st.st_mtime
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
            total += size_count_latest(base)[0]
    return total


def path_size(root: Path, rel_path: str) -> int:
    return size_count_latest(root / rel_path)[0] if (root / rel_path).exists() else 0


def output_roots(root: Path) -> List[Path]:
    return [root / p for p in ["outputs/v18", "outputs/v17", "outputs/v16", "outputs/v15"] if (root / p).exists()]


def file_set(root: Path) -> set[str]:
    out: set[str] = set()
    for name in ["scripts", "outputs", "state", "archive", "logs", ".venv", ".git", "configs"]:
        base = root / name
        if base.exists():
            out.update(str(p.resolve()) for p in all_files(base))
    return out


def is_current_alias(path: Path) -> bool:
    return "CURRENT" in path.name.upper()


def is_read_first(path: Path) -> bool:
    return "READ_FIRST" in path.name.upper()


def family_key(path: Path) -> str:
    rp = path.as_posix()
    key = re.sub(r"\d{8}_\d{6}", "TIMESTAMP", rp)
    key = re.sub(r"V18_\d+[A-Z]?(?:_P\d+)?(?:_R\d+)?", "V18_VERSION", key, flags=re.IGNORECASE)
    key = re.sub(r"\d{4}-\d{2}-\d{2}", "DATE", key)
    return key.lower()


def safe_zip_name(relative_path: str) -> str:
    base = re.sub(r"[^A-Za-z0-9_.-]+", "__", relative_path.strip("/\\"))
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_{stamp}.zip"


def has_protected_file(root: Path, path: Path, args: argparse.Namespace) -> Tuple[bool, str, str]:
    paths = [path] if path.is_file() else all_files(path)
    for p in paths:
        rp = rel(root, p)
        lower = rp.lower()
        name = p.name.upper()
        if lower.startswith(("scripts/", "configs/")):
            return True, "PROTECTED_SOURCE_OR_CONFIG", "SOURCE_CODE"
        if lower.startswith(("state/v18/universe/", "state/v18/manual/", "state/v18/price_cache/")):
            return True, "PROTECTED_STATE_OR_CACHE", "STATE"
        if lower.startswith(("archive/stable/", "archive/stable_compressed/", ".venv/", ".git/")):
            return True, "PROTECTED_NON_OUTPUT_AREA", "NON_OUTPUT"
        if args.keep_current_aliases and "CURRENT" in name:
            return True, "PROTECTED_CURRENT_ALIAS", "CURRENT_ALIAS"
        if args.keep_read_center and lower.startswith("outputs/v18/read_center/"):
            return True, "PROTECTED_READ_CENTER", "READ_CENTER"
        if args.keep_latest_ops and lower in {
            "outputs/v18/ops/v18_16g_r1_read_first.txt",
            "outputs/v18/ops/v18_17a_read_first.txt",
            "outputs/v18/ops/v18_18a_read_first.txt",
            "outputs/v18/ops/v18_18b_read_first.txt",
            "outputs/v18/ops/v18_18c_read_first.txt",
        }:
            return True, "PROTECTED_LATEST_OPS_READ_FIRST", "LATEST_OPS"
        if args.keep_ranking_outputs and lower.startswith("outputs/v18/ranking/") and "current" in name.lower():
            return True, "PROTECTED_CURRENT_RANKING_OUTPUT", "CURRENT_ALIAS"
        if args.keep_universe_state_outputs and lower.startswith("outputs/v18/universe/") and "current" in name.lower():
            return True, "PROTECTED_CURRENT_UNIVERSE_OUTPUT", "CURRENT_ALIAS"
        if any(lower.startswith(f"outputs/v18/{d}/") and "current" in name.lower() for d in ["candidates", "data", "risk", "positions"]):
            return True, "PROTECTED_CURRENT_OUTPUT_ALIAS", "CURRENT_ALIAS"
        if is_read_first(p) and args.keep_latest_ops:
            return True, "PROTECTED_READ_FIRST", "READ_FIRST"
    return False, "", ""


def candidate_objects(root: Path, threshold_mb: float, args: argparse.Namespace) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    threshold = int(threshold_mb * 1024 * 1024)
    raw: List[Path] = []
    # Prefer whole generated-output directories. Files are included when a parent directory is protected.
    for base in output_roots(root):
        for child in base.rglob("*"):
            try:
                if child.is_dir():
                    size, _, _ = size_count_latest(child)
                    if size >= threshold:
                        raw.append(child)
                elif child.is_file() and child.stat().st_size >= threshold:
                    raw.append(child)
            except OSError:
                pass
    # Keep only top-level candidates: if parent is also a candidate, avoid duplicate archiving.
    raw_sorted = sorted(set(raw), key=lambda p: (len(p.parts), str(p)))
    selected: List[Path] = []
    for p in raw_sorted:
        if any(str(p.resolve()).startswith(str(s.resolve()) + os.sep) for s in selected if s.is_dir()):
            continue
        selected.append(p)

    archive_rows: List[Dict[str, object]] = []
    protected_rows: List[Dict[str, object]] = []
    for p in selected:
        size, count, latest = size_count_latest(p)
        protected, reason, category = has_protected_file(root, p, args)
        rp = rel(root, p)
        proposed = root / ARCHIVE_ROOT / safe_zip_name(rp)
        archive_candidate = not protected
        row = {
            "path": str(p.resolve()),
            "relative_path": rp,
            "candidate_type": "FILE" if p.is_file() else "DIRECTORY",
            "size_mb": mb(size),
            "file_count": count,
            "latest_modified_time": dt.datetime.fromtimestamp(latest).isoformat(timespec="seconds"),
            "protected_status": "PROTECTED" if protected else "UNPROTECTED",
            "protected_reason": reason,
            "archive_candidate": str(archive_candidate).upper(),
            "proposed_zip_path": str(proposed.resolve()),
            "zip_exists_before": str(proposed.exists()).upper(),
            "zip_created": "FALSE",
            "zip_verified": "FALSE",
            "delete_original_allowed": "FALSE",
            "deleted_original": "FALSE",
            "delete_error": "",
            "estimated_savings_mb": mb(size if archive_candidate else 0),
            "notes": "Large generated output candidate." if archive_candidate else "Protected output; not eligible.",
        }
        archive_rows.append(row)
        if protected:
            protected_rows.append({
                "path": str(p.resolve()),
                "relative_path": rp,
                "size_mb": mb(size),
                "protected_reason": reason,
                "protected_category": category,
            })
    return archive_rows, protected_rows


def zip_path(src: Path, dst: Path) -> Tuple[bool, str, int]:
    ensure_dir(dst.parent)
    try:
        with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            if src.is_file():
                zf.write(src, arcname=src.name)
            else:
                for p in all_files(src):
                    zf.write(p, arcname=str(src.name / p.relative_to(src)) if isinstance(src.name, Path) else str(Path(src.name) / p.relative_to(src)))
        if not dst.exists() or dst.stat().st_size <= 0:
            return False, "ZIP_NOT_CREATED_OR_EMPTY", 0
        with zipfile.ZipFile(dst, "r") as zf:
            bad = zf.testzip()
            if bad:
                return False, f"ZIP_TEST_FAILED:{bad}", dst.stat().st_size
            if not zf.namelist():
                return False, "ZIP_EMPTY_LISTING", dst.stat().st_size
        return True, "ZIP_VERIFIED", dst.stat().st_size
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}", 0


def delete_original(path: Path) -> Tuple[bool, str]:
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        else:
            return False, "PATH_MISSING"
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def build(root: Path, args: argparse.Namespace) -> int:
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    ensure_dir(ops)
    apply = bool(args.apply)
    delete_after = bool(args.delete_original_after_verified_zip)
    mode = "APPLY_DELETE_VERIFIED_ORIGINALS" if apply and delete_after else ("APPLY" if apply else "DRYRUN")
    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)
    files_before = file_set(root)
    total_before = repo_size(root)
    outputs_before = path_size(root, "outputs")
    archive_generated_before = path_size(root, ARCHIVE_ROOT)

    archive_rows, protected_rows = candidate_objects(root, args.large_output_threshold_mb, args)
    zip_created_count = 0
    zip_created_bytes = 0
    zip_verified_count = 0
    deleted_count = 0
    deleted_bytes = 0
    delete_candidates: List[Dict[str, object]] = []

    if apply:
        for row in archive_rows:
            if row["archive_candidate"] != "TRUE":
                continue
            src = Path(str(row["path"]))
            dst = Path(str(row["proposed_zip_path"]))
            ok, note, zsize = zip_path(src, dst)
            row["zip_created"] = str(ok).upper()
            row["zip_verified"] = str(ok).upper()
            row["notes"] = note
            if ok:
                zip_created_count += 1
                zip_created_bytes += zsize
                zip_verified_count += 1
            if ok and delete_after:
                protected, reason, _ = has_protected_file(root, src, args)
                row["delete_original_allowed"] = str(not protected).upper()
                if not protected:
                    deleted, err = delete_original(src)
                    row["deleted_original"] = str(deleted).upper()
                    row["delete_error"] = err
                    if deleted:
                        deleted_count += 1
                        deleted_bytes += int(float(row["size_mb"]) * 1024 * 1024)
                    else:
                        row["notes"] = f"{note}; DELETE_FAILED"
                else:
                    row["delete_error"] = f"PROTECTED:{reason}"

    for row in archive_rows:
        if row["archive_candidate"] == "TRUE":
            delete_candidates.append({
                "path": row["path"],
                "relative_path": row["relative_path"],
                "size_mb": row["size_mb"],
                "proposed_zip_path": row["proposed_zip_path"],
                "zip_verified": row["zip_verified"],
                "delete_candidate": "TRUE",
                "will_delete_in_apply": str(apply and delete_after).upper(),
                "deleted": row["deleted_original"],
                "delete_error": row["delete_error"],
                "safety_status": "VERIFIED_DELETE_ALLOWED" if row["zip_verified"] == "TRUE" and delete_after else "ARCHIVE_ONLY_OR_DRYRUN",
            })

    paths = {
        "audit": ops / "V18_18D_CURRENT_LARGE_OUTPUT_ARCHIVE_AUDIT.csv",
        "delete": ops / "V18_18D_CURRENT_LARGE_OUTPUT_DELETE_CANDIDATES.csv",
        "protected": ops / "V18_18D_CURRENT_LARGE_OUTPUT_PROTECTED_FILES.csv",
        "storage": ops / "V18_18D_CURRENT_STORAGE_AFTER_LARGE_OUTPUT_AUDIT.csv",
        "report": ops / "V18_18D_CURRENT_LARGE_OUTPUT_ARCHIVE_REPORT.md",
        "read": ops / "V18_18D_READ_FIRST.txt",
    }

    write_csv(paths["audit"], archive_rows, [
        "path", "relative_path", "candidate_type", "size_mb", "file_count", "latest_modified_time",
        "protected_status", "protected_reason", "archive_candidate", "proposed_zip_path",
        "zip_exists_before", "zip_created", "zip_verified", "delete_original_allowed",
        "deleted_original", "delete_error", "estimated_savings_mb", "notes",
    ])
    write_csv(paths["delete"], delete_candidates, [
        "path", "relative_path", "size_mb", "proposed_zip_path", "zip_verified", "delete_candidate",
        "will_delete_in_apply", "deleted", "delete_error", "safety_status",
    ])
    write_csv(paths["protected"], protected_rows, ["path", "relative_path", "size_mb", "protected_reason", "protected_category"])
    shutil.copy2(paths["audit"], ops / "V18_CURRENT_LARGE_OUTPUT_ARCHIVE_AUDIT.csv")

    files_after = file_set(root)
    deleted_files = files_before - files_after
    current_daily_modified = sha256(current_daily) != current_daily_before
    total_after = repo_size(root)
    outputs_after = path_size(root, "outputs")
    archive_generated_after = path_size(root, ARCHIVE_ROOT)

    def count_deleted(prefix: str) -> int:
        return sum(1 for p in deleted_files if f"/{prefix.lower().strip('/')}/" in p.replace("\\", "/").lower())

    source_deleted = sum(1 for p in deleted_files if "/scripts/" in p.replace("\\", "/").lower() or "/configs/" in p.replace("\\", "/").lower())
    alias_deleted = sum(1 for p in deleted_files if is_current_alias(Path(p)))
    read_center_deleted = count_deleted("outputs/v18/read_center")
    manual_deleted = count_deleted("state/v18/manual")
    price_deleted = count_deleted("state/v18/price_cache")
    stable_deleted = count_deleted("archive/stable")
    stable_zip_deleted = count_deleted("archive/stable_compressed")
    venv_deleted = count_deleted(".venv")
    git_deleted = count_deleted(".git")

    ps_ok, _ = parse_ps(root / "scripts/v18/run_v18_18D_large_generated_output_archive_cleanup.ps1")
    py_ok, _ = compile_py(root / "scripts/v18/v18_18D_large_generated_output_archive_cleanup.py")
    hits = dangerous_hits([root / "scripts/v18/run_v18_18D_large_generated_output_archive_cleanup.ps1", root / "scripts/v18/v18_18D_large_generated_output_archive_cleanup.py", *paths.values()])

    candidate_count = sum(1 for r in archive_rows if r["archive_candidate"] == "TRUE")
    candidate_mb = sum(float(r["size_mb"]) for r in archive_rows if r["archive_candidate"] == "TRUE")
    estimated_savings = candidate_mb if delete_after else 0.0
    validations = [
        ps_ok, py_ok, source_deleted == 0, alias_deleted == 0, read_center_deleted == 0,
        manual_deleted == 0, price_deleted == 0, stable_deleted == 0, stable_zip_deleted == 0,
        venv_deleted == 0, git_deleted == 0, not current_daily_modified, len(hits) == 0,
    ]
    if not apply:
        validations.extend([zip_created_count == 0, deleted_count == 0, not deleted_files])
    if apply and delete_after:
        validations.append(zip_verified_count == deleted_count)
    validation_fail = sum(1 for ok in validations if not ok)

    status = STATUS_DRYRUN
    if apply and delete_after:
        status = STATUS_DELETE
    elif apply:
        status = STATUS_APPLY
    if validation_fail:
        status = STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": mode,
        "APPLY": str(apply).upper(),
        "DELETE_ORIGINAL_AFTER_VERIFIED_ZIP": str(delete_after).upper(),
        "TOTAL_SIZE_MB_BEFORE": mb(total_before),
        "OUTPUTS_SIZE_MB_BEFORE": mb(outputs_before),
        "ARCHIVE_GENERATED_OUTPUTS_SIZE_MB_BEFORE": mb(archive_generated_before),
        "LARGE_OUTPUT_CANDIDATE_COUNT": str(candidate_count),
        "LARGE_OUTPUT_CANDIDATE_MB": f"{candidate_mb:.3f}",
        "OUTPUT_ZIP_CREATED_COUNT": str(zip_created_count),
        "OUTPUT_ZIP_CREATED_MB": mb(zip_created_bytes),
        "OUTPUT_ZIP_VERIFIED_COUNT": str(zip_verified_count),
        "OUTPUT_ORIGINAL_DELETED_COUNT": str(deleted_count),
        "OUTPUT_ORIGINAL_DELETED_MB": mb(deleted_bytes),
        "ESTIMATED_SAVINGS_MB": f"{estimated_savings:.3f}",
        "TOTAL_SIZE_MB_AFTER": mb(total_after),
        "OUTPUTS_SIZE_MB_AFTER": mb(outputs_after),
        "ARCHIVE_GENERATED_OUTPUTS_SIZE_MB_AFTER": mb(archive_generated_after),
        "SOURCE_CODE_DELETED_COUNT": str(source_deleted),
        "CURRENT_ALIAS_DELETED_COUNT": str(alias_deleted),
        "READ_CENTER_DELETED_COUNT": str(read_center_deleted),
        "MANUAL_STATE_DELETED_COUNT": str(manual_deleted),
        "PRICE_CACHE_DELETED_COUNT": str(price_deleted),
        "STABLE_SNAPSHOT_DELETED_COUNT": str(stable_deleted),
        "STABLE_COMPRESSED_ZIP_DELETED_COUNT": str(stable_zip_deleted),
        "VENV_DELETED_COUNT": str(venv_deleted),
        "GIT_DELETED_COUNT": str(git_deleted),
        "CURRENT_DAILY_MODIFIED": str(current_daily_modified).upper(),
        "DANGEROUS_TOKEN_FINDING_COUNT": str(len(hits)),
        "VALIDATION_FAIL_COUNT": str(validation_fail),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }
    storage_rows = [{"metric": k, "value": v} for k, v in values.items()]
    write_csv(paths["storage"], storage_rows, ["metric", "value"])
    report = [
        "# V18.18D Large Generated Output Archive and Verified Cleanup", "",
        "## Summary", "",
        *[f"- {k}: {v}" for k, v in values.items()],
        "", "## Archive Candidates", "",
        *[f"- {r['relative_path']}: {r['size_mb']} MB, type={r['candidate_type']}, zip={r['proposed_zip_path']}" for r in archive_rows if r["archive_candidate"] == "TRUE"],
        "", "## Protected Large Outputs", "",
        *[f"- {r['relative_path']}: {r['size_mb']} MB, reason={r['protected_reason']}" for r in archive_rows if r["archive_candidate"] != "TRUE"],
        "", "## Safety", "",
        "- DRYRUN creates no zip files and deletes nothing.",
        "- Original generated outputs are deleted only when both -Apply and -DeleteOriginalAfterVerifiedZip are passed.",
        "- Protected current aliases, read center files, state, price cache, stable snapshots, .venv, and .git are never eligible.",
        "", "## Guardrails", "",
        f"AUTO_TRADE: {AUTO_TRADE}; AUTO_SELL: {AUTO_SELL}; OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}.",
    ]
    write_text(paths["report"], "\n".join(report) + "\n")
    write_text(paths["read"], "\n".join(f"{k}: {v}" for k, v in values.items()) + "\n")
    shutil.copy2(paths["read"], ops / "V18_CURRENT_LARGE_OUTPUT_CLEANUP_READ_FIRST.txt")

    for key in [
        "STATUS", "MODE", "TOTAL_SIZE_MB_BEFORE", "OUTPUTS_SIZE_MB_BEFORE",
        "LARGE_OUTPUT_CANDIDATE_COUNT", "LARGE_OUTPUT_CANDIDATE_MB", "ESTIMATED_SAVINGS_MB",
        "OUTPUT_ZIP_CREATED_COUNT", "OUTPUT_ORIGINAL_DELETED_COUNT", "SOURCE_CODE_DELETED_COUNT",
        "CURRENT_ALIAS_DELETED_COUNT", "READ_CENTER_DELETED_COUNT", "MANUAL_STATE_DELETED_COUNT",
        "PRICE_CACHE_DELETED_COUNT", "VALIDATION_FAIL_COUNT", "AUTO_TRADE", "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT",
    ]:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--delete-original-after-verified-zip", action="store_true")
    parser.add_argument("--large-output-threshold-mb", type=float, default=25.0)
    parser.add_argument("--keep-latest-per-family", type=int, default=3)
    parser.add_argument("--keep-current-aliases", type=parse_bool, default=True)
    parser.add_argument("--keep-read-center", type=parse_bool, default=True)
    parser.add_argument("--keep-latest-ops", type=parse_bool, default=True)
    parser.add_argument("--keep-ranking-outputs", type=parse_bool, default=True)
    parser.add_argument("--keep-universe-state-outputs", type=parse_bool, default=True)
    parser.add_argument("--keep-price-cache", type=parse_bool, default=True)
    parser.add_argument("--keep-manual-state", type=parse_bool, default=True)
    args = parser.parse_args()
    return build(Path(args.root), args)


if __name__ == "__main__":
    raise SystemExit(main())
