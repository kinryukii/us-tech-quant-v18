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
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_DRYRUN = "OK_V18_18A_STORAGE_SLIMMING_AUDIT_READY"
STATUS_APPLY = "OK_V18_18A_STORAGE_SLIMMING_CLEANUP_APPLIED"
STATUS_WARN = "WARN_V18_18A_STORAGE_SLIMMING_VALIDATION_FAILED"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
LATEST_STABLE_NAME = "V18_16G_R1_stable_run_triggered_rolling_universe_scan_20260519_122357"


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
    return any(after.get(k) != v for k, v in before.items())


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


def file_iter(root: Path) -> List[Path]:
    roots = ["scripts", "outputs", "state", "archive", "logs", ".venv", ".git", "configs"]
    files: List[Path] = []
    for name in roots:
        base = root / name
        if not base.exists():
            continue
        for dirpath, _, filenames in os.walk(base):
            for filename in filenames:
                p = Path(dirpath) / filename
                try:
                    if p.is_file():
                        files.append(p)
                except OSError:
                    pass
    return files


def directory_group(relative_path: str) -> str:
    return relative_path.split("/", 1)[0] if "/" in relative_path else relative_path


def is_under(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False


def is_current_alias(path: Path) -> bool:
    name = path.name.upper()
    return "CURRENT" in name or "READ_FIRST" in name


def family_key(path: Path) -> str:
    name = path.name
    key = re.sub(r"\d{8}_\d{6}", "TIMESTAMP", name)
    key = re.sub(r"V18_\d+[A-Z]?(?:_P\d+)?(?:_R\d+)?", "V18_VERSION", key, flags=re.IGNORECASE)
    key = re.sub(r"V18-\d+[A-Z]?", "V18_VERSION", key, flags=re.IGNORECASE)
    key = re.sub(r"\d{4}-\d{2}-\d{2}", "DATE", key)
    return f"{path.parent.as_posix()}::{key}".lower()


def stable_snapshot_root(path: Path, stable_root: Path) -> Path | None:
    try:
        relp = path.resolve().relative_to(stable_root.resolve())
    except Exception:
        return None
    parts = relp.parts
    if not parts:
        return None
    return stable_root / parts[0]


def stable_snapshots(root: Path) -> List[Path]:
    base = root / "archive/stable"
    if not base.exists():
        return []
    return sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)


def classify_file(root: Path, path: Path, latest_stable_keep: set[Path]) -> Dict[str, object]:
    rp = rel(root, path)
    lower = rp.lower()
    name_lower = path.name.lower()
    ext = path.suffix.lower()
    stable_root = root / "archive/stable"
    source = lower.startswith("scripts/") or lower.startswith("configs/") or ext in {".py", ".ps1"} and lower.startswith("scripts/")
    state_file = lower.startswith("state/")
    manual = lower in {
        "state/v18/manual/v18_manual_positions.csv",
        "state/v18/manual/v18_manual_trade_log.csv",
    }
    universe_state = lower in {
        "state/v18/universe/v18_universe_rolling_state.csv",
        "state/v18/universe/v18_manual_universe_additions.csv",
    }
    price_cache = lower.startswith("state/v18/price_cache/")
    provider_cache = lower.startswith("state/v18/provider_cache/")
    stable_file = lower.startswith("archive/stable/")
    temp = (
        ext in {".tmp", ".temp", ".bak"}
        or lower.startswith("state/v18/provider_cache/yfinance/tmp/")
        or "/tmp/" in lower
    )
    log_file = ext in {".log"} or lower.startswith("logs/") or lower.startswith("state/v18/provider_cache/yfinance/logs/")
    pycache = "__pycache__" in lower or ext == ".pyc" or ".pytest_cache" in lower
    current = is_current_alias(path)
    keep_reason = ""
    protected_category = ""
    snap_root = stable_snapshot_root(path, stable_root)
    if lower.startswith(".git/"):
        keep_reason = "PROTECTED_GIT"
        protected_category = ".git"
    elif lower.startswith(".venv/"):
        keep_reason = "PROTECTED_VENV"
        protected_category = ".venv"
    elif source:
        keep_reason = "PROTECTED_SOURCE_CODE"
        protected_category = "SOURCE_CODE"
    elif stable_file:
        keep_reason = "PROTECTED_STABLE_SNAPSHOT"
        protected_category = "STABLE_SNAPSHOT"
        if snap_root and snap_root.resolve() in {p.resolve() for p in latest_stable_keep}:
            keep_reason = "PROTECTED_LATEST_STABLE_SNAPSHOT_SET"
    elif universe_state:
        keep_reason = "PROTECTED_UNIVERSE_STATE"
        protected_category = "UNIVERSE_STATE"
    elif manual:
        keep_reason = "PROTECTED_MANUAL_STATE"
        protected_category = "MANUAL_STATE"
    elif price_cache:
        keep_reason = "PROTECTED_PRICE_CACHE"
        protected_category = "PRICE_CACHE"
    elif current:
        keep_reason = "PROTECTED_CURRENT_ALIAS_OR_READ_FIRST"
        protected_category = "CURRENT_ALIAS"
    elif lower.startswith("state/v18/universe/") or lower.startswith("state/v18/manual/"):
        keep_reason = "PROTECTED_STATE_DIRECTORY"
        protected_category = "STATE"
    return {
        "relative_path": rp,
        "directory_group": directory_group(rp),
        "extension": ext,
        "family_key": family_key(Path(rp)),
        "is_current_alias": current,
        "is_source_code": source,
        "is_state_file": state_file,
        "is_manual_file": manual,
        "is_price_cache_file": price_cache,
        "is_provider_cache_file": provider_cache,
        "is_stable_snapshot_file": stable_file,
        "is_temp_file": temp,
        "is_log_file": log_file,
        "is_pycache_file": pycache,
        "keep_reason": keep_reason,
        "protected_category": protected_category,
    }


def candidate_reason(row: Dict[str, object], args: argparse.Namespace, generated_keep: set[str], log_keep: set[str]) -> Tuple[bool, str, str]:
    rp = str(row["relative_path"])
    if row["keep_reason"]:
        return False, "", "PROTECTED"
    if row["is_pycache_file"] and args.delete_pycache:
        return True, "PYTHON_CACHE", "LOW"
    if row["is_temp_file"] and args.delete_temp_files:
        if str(row["relative_path"]).lower().startswith("state/v18/provider_cache/") and not args.delete_provider_temp_cache:
            return False, "", "PROTECTED"
        return True, "TEMP_FILE", "LOW"
    if row["is_log_file"] and args.delete_old_logs and rp not in log_keep:
        return True, "OLD_LOG_BEYOND_RETENTION", "LOW"
    if args.delete_old_generated_outputs and rp.startswith(("outputs/v18/ops/", "outputs/v18/universe/", "outputs/v18/data/", "outputs/v18/risk/", "outputs/v18/ranking/")):
        if rp not in generated_keep:
            return True, "OLD_GENERATED_OUTPUT_BEYOND_RETENTION", "LOW"
    if row["is_stable_snapshot_file"] and args.delete_old_stable_snapshots:
        return False, "", "PROTECTED"
    return False, "", "PROTECTED"


def delete_file(path: Path) -> Tuple[bool, str]:
    try:
        path.unlink()
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def compress_old_stable_snapshots(root: Path, keep_count: int, apply: bool) -> List[str]:
    notes: List[str] = []
    snapshots = stable_snapshots(root)
    for snap in snapshots[keep_count:]:
        if snap.name == LATEST_STABLE_NAME:
            continue
        zip_path = snap.with_suffix(".zip")
        if zip_path.exists() and zip_path.stat().st_size > 0:
            notes.append(f"EXISTS:{rel(root, zip_path)}")
            continue
        if apply:
            base_name = str(snap)
            shutil.make_archive(base_name, "zip", root_dir=snap.parent, base_dir=snap.name)
            if zip_path.exists() and zip_path.stat().st_size > 0:
                notes.append(f"CREATED:{rel(root, zip_path)}")
            else:
                notes.append(f"FAILED:{rel(root, zip_path)}")
        else:
            notes.append(f"DRYRUN_WOULD_COMPRESS:{rel(root, snap)}")
    return notes


def build(root: Path, args: argparse.Namespace) -> int:
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    ensure_dir(ops)
    apply = bool(args.apply)
    mode = "APPLY" if apply else "DRYRUN"
    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)
    stable_before = stable_baseline(root)
    before_files = {str(p.resolve()) for p in file_iter(root)}

    stable_keep = set(stable_snapshots(root)[: max(1, args.keep_latest_stable_snapshots)])
    latest_stable = root / "archive/stable" / LATEST_STABLE_NAME
    if latest_stable.exists():
        stable_keep.add(latest_stable)

    files = file_iter(root)
    generated_groups: Dict[str, List[Path]] = defaultdict(list)
    logs: List[Path] = []
    for p in files:
        rp = rel(root, p)
        if rp.startswith(("outputs/v18/ops/", "outputs/v18/universe/", "outputs/v18/data/", "outputs/v18/risk/", "outputs/v18/ranking/")):
            generated_groups[family_key(Path(rp))].append(p)
        if p.suffix.lower() == ".log" or rp.startswith("logs/") or rp.startswith("state/v18/provider_cache/yfinance/logs/"):
            logs.append(p)

    generated_keep: set[str] = set()
    for group_files in generated_groups.values():
        sorted_group = sorted(group_files, key=lambda x: x.stat().st_mtime, reverse=True)
        for p in sorted_group[: max(0, args.keep_latest_outputs)]:
            generated_keep.add(rel(root, p))
    log_keep = {rel(root, p) for p in sorted(logs, key=lambda x: x.stat().st_mtime, reverse=True)[: max(0, args.keep_latest_logs)]}

    audit_rows: List[Dict[str, object]] = []
    delete_rows: List[Dict[str, object]] = []
    protected_rows: List[Dict[str, object]] = []
    top_sizes: Dict[str, int] = defaultdict(int)
    dir_sizes: Dict[str, int] = defaultdict(int)
    total_size = 0
    for p in files:
        try:
            stat = p.stat()
        except OSError:
            continue
        size = stat.st_size
        total_size += size
        rp = rel(root, p)
        top_sizes[directory_group(rp)] += size
        parts = Path(rp).parts
        for depth in range(1, min(len(parts), 4)):
            dir_sizes["/".join(parts[:depth])] += size
        cls = classify_file(root, p, stable_keep)
        candidate, reason, risk = candidate_reason(cls, args, generated_keep, log_keep)
        row = {
            "path": str(p.resolve()),
            "relative_path": rp,
            "directory_group": cls["directory_group"],
            "file_size_bytes": size,
            "file_size_mb": mb(size),
            "modified_time": dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "extension": cls["extension"],
            "family_key": cls["family_key"],
            "is_current_alias": str(cls["is_current_alias"]).upper(),
            "is_source_code": str(cls["is_source_code"]).upper(),
            "is_state_file": str(cls["is_state_file"]).upper(),
            "is_manual_file": str(cls["is_manual_file"]).upper(),
            "is_price_cache_file": str(cls["is_price_cache_file"]).upper(),
            "is_provider_cache_file": str(cls["is_provider_cache_file"]).upper(),
            "is_stable_snapshot_file": str(cls["is_stable_snapshot_file"]).upper(),
            "is_temp_file": str(cls["is_temp_file"]).upper(),
            "is_log_file": str(cls["is_log_file"]).upper(),
            "is_pycache_file": str(cls["is_pycache_file"]).upper(),
            "keep_reason": cls["keep_reason"],
            "delete_candidate": str(candidate).upper(),
            "delete_reason": reason,
            "delete_risk_level": risk,
        }
        audit_rows.append(row)
        if cls["keep_reason"]:
            protected_rows.append({
                "path": row["path"],
                "relative_path": rp,
                "file_size_mb": row["file_size_mb"],
                "keep_reason": cls["keep_reason"],
                "protected_category": cls["protected_category"],
            })
        if candidate:
            delete_rows.append({
                "path": row["path"],
                "relative_path": rp,
                "file_size_bytes": size,
                "file_size_mb": row["file_size_mb"],
                "modified_time": row["modified_time"],
                "delete_reason": reason,
                "delete_risk_level": risk,
                "protected_status": "UNPROTECTED",
                "will_delete_in_apply": str(apply).upper(),
                "deleted": "FALSE",
                "delete_error": "",
            })

    compress_notes: List[str] = []
    if args.compress_old_stable_snapshots:
        compress_notes = compress_old_stable_snapshots(root, args.keep_latest_stable_snapshots, apply)

    deleted_count = 0
    deleted_bytes = 0
    delete_fail_count = 0
    if apply:
        for row in delete_rows:
            path = Path(str(row["path"]))
            ok, err = delete_file(path)
            row["deleted"] = str(ok).upper()
            row["delete_error"] = err
            if ok:
                deleted_count += 1
                deleted_bytes += int(row["file_size_bytes"])
            else:
                delete_fail_count += 1

    paths = {
        "audit": ops / "V18_18A_CURRENT_STORAGE_AUDIT.csv",
        "delete": ops / "V18_18A_CURRENT_DELETE_CANDIDATES.csv",
        "keep": ops / "V18_18A_CURRENT_KEEP_PROTECTED_FILES.csv",
        "report": ops / "V18_18A_CURRENT_STORAGE_CLEANUP_REPORT.md",
        "read": ops / "V18_18A_READ_FIRST.txt",
    }
    write_csv(paths["audit"], audit_rows, [
        "path", "relative_path", "directory_group", "file_size_bytes", "file_size_mb", "modified_time",
        "extension", "family_key", "is_current_alias", "is_source_code", "is_state_file", "is_manual_file",
        "is_price_cache_file", "is_provider_cache_file", "is_stable_snapshot_file", "is_temp_file", "is_log_file", "is_pycache_file",
        "keep_reason", "delete_candidate", "delete_reason", "delete_risk_level",
    ])
    write_csv(paths["delete"], delete_rows, [
        "path", "relative_path", "file_size_bytes", "file_size_mb", "modified_time", "delete_reason",
        "delete_risk_level", "protected_status", "will_delete_in_apply", "deleted", "delete_error",
    ])
    write_csv(paths["keep"], protected_rows, ["path", "relative_path", "file_size_mb", "keep_reason", "protected_category"])
    shutil.copy2(paths["audit"], ops / "V18_CURRENT_STORAGE_AUDIT.csv")
    shutil.copy2(paths["delete"], ops / "V18_CURRENT_DELETE_CANDIDATES.csv")

    after_files = {str(p.resolve()) for p in file_iter(root)}
    actually_deleted = before_files - after_files
    current_daily_modified = sha256(current_daily) != current_daily_before
    snapshots_modified = stable_modified(stable_before, root)

    source_deleted = sum(1 for p in actually_deleted if "/scripts/" in p.replace("\\", "/").lower() or p.lower().endswith((".py", ".ps1")))
    alias_deleted = sum(1 for p in actually_deleted if is_current_alias(Path(p)))
    manual_deleted = sum(1 for p in actually_deleted if p.replace("\\", "/").lower().endswith(("state/v18/manual/v18_manual_positions.csv", "state/v18/manual/v18_manual_trade_log.csv")))
    price_deleted = sum(1 for p in actually_deleted if "/state/v18/price_cache/" in p.replace("\\", "/").lower())

    ps_ok, _ = parse_ps(root / "scripts/v18/run_v18_18A_storage_slimming_cleanup.ps1")
    py_ok, _ = compile_py(root / "scripts/v18/v18_18A_storage_slimming_cleanup.py")
    hits = dangerous_hits([root / "scripts/v18/run_v18_18A_storage_slimming_cleanup.ps1", root / "scripts/v18/v18_18A_storage_slimming_cleanup.py", *paths.values()])

    delete_candidate_paths = {str(r["relative_path"]).lower() for r in delete_rows}
    validation_checks = [
        ps_ok,
        py_ok,
        not current_daily_modified,
        not any(p.startswith("scripts/") for p in delete_candidate_paths),
        not any("current" in Path(p).name.lower() or "read_first" in Path(p).name.lower() for p in delete_candidate_paths),
        "state/v18/manual/v18_manual_positions.csv" not in delete_candidate_paths,
        "state/v18/manual/v18_manual_trade_log.csv" not in delete_candidate_paths,
        not any(p.startswith("state/v18/price_cache/") for p in delete_candidate_paths),
        not any(p.startswith(f"archive/stable/{LATEST_STABLE_NAME.lower()}/") for p in delete_candidate_paths),
        args.delete_old_stable_snapshots or not any(p.startswith("archive/stable/") for p in delete_candidate_paths),
        source_deleted == 0,
        alias_deleted == 0,
        manual_deleted == 0,
        price_deleted == 0,
        len(hits) == 0,
    ]
    if not apply:
        validation_checks.extend([deleted_count == 0, len(actually_deleted) == 0, not snapshots_modified])
    validation_fail = sum(1 for ok in validation_checks if not ok)

    def size_group(name: str) -> int:
        return top_sizes.get(name, 0)

    price_cache_size = sum(r["file_size_bytes"] for r in audit_rows if r["is_price_cache_file"] == "TRUE")
    provider_cache_size = sum(r["file_size_bytes"] for r in audit_rows if r["is_provider_cache_file"] == "TRUE")
    delete_bytes = sum(int(r["file_size_bytes"]) for r in delete_rows)
    protected_bytes = sum(int(float(r["file_size_mb"]) * 1024 * 1024) for r in protected_rows)
    stable_size = sum(r["file_size_bytes"] for r in audit_rows if r["is_stable_snapshot_file"] == "TRUE")

    values = {
        "STATUS": (STATUS_APPLY if apply else STATUS_DRYRUN) if validation_fail == 0 else STATUS_WARN,
        "MODE": mode,
        "ROOT": str(root),
        "TOTAL_FILE_COUNT": str(len(audit_rows)),
        "TOTAL_SIZE_MB": mb(total_size),
        "SCRIPTS_SIZE_MB": mb(size_group("scripts")),
        "OUTPUTS_SIZE_MB": mb(size_group("outputs")),
        "STATE_SIZE_MB": mb(size_group("state")),
        "ARCHIVE_STABLE_SIZE_MB": mb(stable_size),
        "VENV_SIZE_MB": mb(size_group(".venv")),
        "GIT_SIZE_MB": mb(size_group(".git")),
        "PRICE_CACHE_SIZE_MB": mb(price_cache_size),
        "PROVIDER_CACHE_SIZE_MB": mb(provider_cache_size),
        "DELETE_CANDIDATE_COUNT": str(len(delete_rows)),
        "DELETE_CANDIDATE_MB": mb(delete_bytes),
        "PROTECTED_FILE_COUNT": str(len(protected_rows)),
        "PROTECTED_FILE_MB": mb(protected_bytes),
        "DELETED_COUNT": str(deleted_count),
        "DELETED_MB": mb(deleted_bytes),
        "DELETE_FAIL_COUNT": str(delete_fail_count),
        "KEEP_LATEST_OUTPUTS": str(args.keep_latest_outputs),
        "KEEP_LATEST_LOGS": str(args.keep_latest_logs),
        "KEEP_LATEST_STABLE_SNAPSHOTS": str(args.keep_latest_stable_snapshots),
        "APPLY": str(apply).upper(),
        "COMPRESS_OLD_STABLE_SNAPSHOTS": str(args.compress_old_stable_snapshots).upper(),
        "DELETE_OLD_STABLE_SNAPSHOTS": str(args.delete_old_stable_snapshots).upper(),
        "CURRENT_DAILY_MODIFIED": str(current_daily_modified).upper(),
        "STABLE_SNAPSHOT_MODIFIED": str(snapshots_modified).upper(),
        "SOURCE_CODE_DELETED_COUNT": str(source_deleted),
        "CURRENT_ALIAS_DELETED_COUNT": str(alias_deleted),
        "MANUAL_STATE_DELETED_COUNT": str(manual_deleted),
        "PRICE_CACHE_DELETED_COUNT": str(price_deleted),
        "VALIDATION_FAIL_COUNT": str(validation_fail),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }

    largest_files = sorted(audit_rows, key=lambda r: int(r["file_size_bytes"]), reverse=True)[:30]
    largest_dirs = sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)[:20]
    stable_summary = []
    for snap in stable_snapshots(root):
        snap_size = sum(p.stat().st_size for p in snap.rglob("*") if p.is_file())
        stable_summary.append(f"- {snap.name}: {mb(snap_size)} MB")
    report = [
        "# V18.18A Storage Slimming Audit and Safe Retention Cleanup", "",
        "## Summary", "",
        *[f"- {k}: {v}" for k, v in values.items()],
        "", "## Size by Top-Level Directory", "",
        *[f"- {k}: {mb(v)} MB" for k, v in sorted(top_sizes.items(), key=lambda x: x[1], reverse=True)],
        "", "## Largest 30 Files", "",
        *[f"- {r['relative_path']}: {r['file_size_mb']} MB" for r in largest_files],
        "", "## Largest 20 Directories", "",
        *[f"- {k}: {mb(v)} MB" for k, v in largest_dirs],
        "", "## Stable Snapshot Size Summary", "",
        *(stable_summary or ["No stable snapshots found."]),
        "", "## Generated Output Summary", "",
        f"- outputs/v18 generated files audited: {sum(1 for r in audit_rows if str(r['relative_path']).startswith('outputs/v18/'))}",
        f"- Delete candidates: {values['DELETE_CANDIDATE_COUNT']} files / {values['DELETE_CANDIDATE_MB']} MB",
        "", "## State Summary", "",
        f"- state/v18 size: {values['STATE_SIZE_MB']} MB",
        f"- price cache size: {values['PRICE_CACHE_SIZE_MB']} MB",
        f"- provider cache size: {values['PROVIDER_CACHE_SIZE_MB']} MB",
        "", "## Provider Cache Temp/Log Summary", "",
        f"- temp/log candidates are included only when unprotected and matching configured retention flags.",
        "", "## Mode", "",
        f"- Current mode: {mode}",
        "- Apply command: powershell -NoProfile -ExecutionPolicy Bypass -File \"D:\\us-tech-quant\\scripts\\v18\\run_v18_18A_storage_slimming_cleanup.ps1\" -Apply",
        "", "## Stable Compression Notes", "",
        *(compress_notes or ["Compression not requested."]),
        "", "## Guardrails", "",
        f"AUTO_TRADE: {AUTO_TRADE}; AUTO_SELL: {AUTO_SELL}; OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}.",
    ]
    write_text(paths["report"], "\n".join(report) + "\n")
    write_text(paths["read"], "\n".join(f"{k}: {v}" for k, v in values.items()) + "\n")
    shutil.copy2(paths["read"], ops / "V18_CURRENT_STORAGE_CLEANUP_READ_FIRST.txt")

    for key in [
        "STATUS", "MODE", "TOTAL_SIZE_MB", "OUTPUTS_SIZE_MB", "STATE_SIZE_MB", "ARCHIVE_STABLE_SIZE_MB",
        "VENV_SIZE_MB", "DELETE_CANDIDATE_COUNT", "DELETE_CANDIDATE_MB", "PROTECTED_FILE_COUNT",
        "PROTECTED_FILE_MB", "DELETED_COUNT", "DELETED_MB", "VALIDATION_FAIL_COUNT",
        "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT",
    ]:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--keep-latest-outputs", type=int, default=3)
    parser.add_argument("--keep-latest-logs", type=int, default=10)
    parser.add_argument("--keep-latest-stable-snapshots", type=int, default=5)
    parser.add_argument("--compress-old-stable-snapshots", type=parse_bool, default=False)
    parser.add_argument("--delete-pycache", type=parse_bool, default=True)
    parser.add_argument("--delete-temp-files", type=parse_bool, default=True)
    parser.add_argument("--delete-old-generated-outputs", type=parse_bool, default=True)
    parser.add_argument("--delete-provider-temp-cache", type=parse_bool, default=True)
    parser.add_argument("--delete-old-logs", type=parse_bool, default=True)
    parser.add_argument("--delete-old-stable-snapshots", type=parse_bool, default=False)
    args = parser.parse_args()
    return build(Path(args.root), args)


if __name__ == "__main__":
    raise SystemExit(main())
