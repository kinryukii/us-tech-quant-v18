from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_34A_STORAGE_INVENTORY_READY"
STATUS_WARN = "WARN_V18_34A_STORAGE_INVENTORY_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_34A_STORAGE_INVENTORY_FAILED"

OUT_SUMMARY = Path("outputs/v18/ops/V18_34A_STORAGE_INVENTORY_SUMMARY.csv")
OUT_CANDIDATES = Path("outputs/v18/ops/V18_34A_STORAGE_DELETE_CANDIDATES.csv")
OUT_PROTECTED = Path("outputs/v18/ops/V18_34A_STORAGE_PROTECTED_ITEMS.csv")
OUT_MANIFEST = Path("outputs/v18/ops/V18_34A_STORAGE_DELETION_MANIFEST.csv")
OUT_REPORT = Path("outputs/v18/read_center/V18_34A_STORAGE_CLEANUP_REPORT.md")
OUT_CURRENT = Path("outputs/v18/read_center/V18_CURRENT_STORAGE_CLEANUP.md")
OUT_READ_FIRST = Path("outputs/v18/ops/V18_34A_READ_FIRST.txt")

PROTECTED_FREEZE_REPAIR_BACKUP = Path(
    "archive/v18/freeze_repair_backups/V18_32D_FREEZE_REPAIR_20260524_235413/"
    "V18_DAILY_SIGNAL_FREEZE_LEDGER_PRE_REPAIR.csv"
)


@dataclass
class Item:
    path: Path
    rel_path: str
    item_type: str
    size_bytes: int
    modified_time: str


@dataclass
class Candidate:
    category: str
    path: Path
    rel_path: str
    item_type: str
    size_bytes: int
    modified_time: str
    reason: str
    protection_check_result: str
    allowed_by_flags: bool = False
    deleted: bool = False
    delete_error: str = ""


def now_iso() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()


def fmt_mb(size_bytes: int) -> str:
    return f"{size_bytes / 1024 / 1024:.2f}"


def safe_rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def is_inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def stat_mtime(path: Path) -> str:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime).replace(microsecond=0).isoformat()
    except OSError:
        return ""


def path_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for name in filenames:
            fp = Path(dirpath) / name
            try:
                total += fp.stat().st_size
            except OSError:
                pass
    return total


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames:
            yield Path(dirpath) / name


def immediate_dirs(root: Path, path: Path) -> List[Item]:
    out: List[Item] = []
    if not path.exists():
        return out
    for child in path.iterdir():
        try:
            item_type = "DIR" if child.is_dir() else "FILE"
            out.append(
                Item(
                    path=child,
                    rel_path=safe_rel(root, child),
                    item_type=item_type,
                    size_bytes=path_size(child),
                    modified_time=stat_mtime(child),
                )
            )
        except OSError:
            continue
    return out


def top_dirs(root: Path, limit: int = 30) -> List[Item]:
    dirs: List[Item] = []
    for dirpath, dirnames, filenames in os.walk(root):
        p = Path(dirpath)
        if p == root:
            continue
        try:
            dirs.append(Item(p, safe_rel(root, p), "DIR", path_size(p), stat_mtime(p)))
        except OSError:
            continue
    return sorted(dirs, key=lambda x: x.size_bytes, reverse=True)[:limit]


def top_files(root: Path, limit: int = 50) -> List[Item]:
    files: List[Item] = []
    for fp in iter_files(root):
        try:
            files.append(Item(fp, safe_rel(root, fp), "FILE", fp.stat().st_size, stat_mtime(fp)))
        except OSError:
            continue
    return sorted(files, key=lambda x: x.size_bytes, reverse=True)[:limit]


def age_days(path: Path) -> float:
    try:
        return (dt.datetime.now() - dt.datetime.fromtimestamp(path.stat().st_mtime)).total_seconds() / 86400
    except OSError:
        return 0


def has_compressed_copy(root: Path, stable_folder: Path) -> bool:
    compressed = root / "archive/stable_compressed"
    if not compressed.exists():
        return False
    folder_name = stable_folder.name
    token_match = re.match(r"(.+?)_\d{8}_\d{6}$", folder_name)
    prefix = token_match.group(1) if token_match else folder_name
    return any(zip_path.name.startswith(prefix) and zip_path.suffix.lower() == ".zip" for zip_path in compressed.glob("*.zip"))


def protected_prefixes() -> Tuple[str, ...]:
    return (
        "scripts/",
        "configs/",
        "state/",
        "docs/v18/V18_CODEX_SAFETY_CONTRACT.md",
        "docs/v18/V18_CODEX_TASK_TEMPLATE.md",
        "outputs/v18/read_center/V18_CURRENT_",
        "outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md",
        "outputs/v18/ops/V18_CODEX_NEXT_TASK_BRIEF.md",
        "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
        "outputs/v18/recommendations/V18_CURRENT_",
        "outputs/v18/themes/V18_CURRENT_",
        str(PROTECTED_FREEZE_REPAIR_BACKUP).replace("\\", "/"),
    )


def is_read_first_protected(rel_path: str) -> bool:
    if not rel_path.startswith("outputs/v18/ops/") or not rel_path.endswith("_READ_FIRST.txt"):
        return False
    m = re.search(r"V18_(\d+)([A-Z])", rel_path)
    if not m:
        return True
    major = int(m.group(1))
    return major >= 30


def protection_reason(root: Path, path: Path) -> Optional[str]:
    rel = safe_rel(root, path)
    rel_norm = rel.replace("\\", "/")
    if not is_inside(root, path):
        return "OUTSIDE_REPO"
    for prefix in protected_prefixes():
        if rel_norm == prefix or rel_norm.startswith(prefix):
            return f"PROTECTED_PREFIX:{prefix}"
    if is_read_first_protected(rel_norm):
        return "PROTECTED_RECENT_READ_FIRST"
    if rel_norm.startswith(".venv/"):
        return "PROTECTED_VENV"
    if rel_norm.startswith("outputs/v18/ops/V18_34A_") or rel_norm == str(OUT_READ_FIRST).replace("\\", "/"):
        return "PROTECTED_CURRENT_34A_OUTPUT"
    return None


def add_candidate(
    root: Path,
    candidates: List[Candidate],
    category: str,
    path: Path,
    reason: str,
) -> None:
    prot = protection_reason(root, path)
    item_type = "DIR" if path.is_dir() else "FILE"
    candidates.append(
        Candidate(
            category=category,
            path=path,
            rel_path=safe_rel(root, path),
            item_type=item_type,
            size_bytes=path_size(path),
            modified_time=stat_mtime(path),
            reason=reason,
            protection_check_result=prot or "UNPROTECTED",
        )
    )


def collect_cache_candidates(root: Path, min_age_days: int) -> List[Candidate]:
    candidates: List[Candidate] = []
    for dirpath, dirnames, filenames in os.walk(root):
        p = Path(dirpath)
        if protection_reason(root, p):
            continue
        if p.name in {"__pycache__", ".pytest_cache"} and age_days(p) >= min_age_days:
            add_candidate(root, candidates, "LOW_RISK_GENERATED_CACHE", p, f"{p.name} generated cache")
            dirnames[:] = []
            continue
        for name in filenames:
            fp = p / name
            if protection_reason(root, fp):
                continue
            suffix = fp.suffix.lower()
            if fp.stat().st_size == 0 and age_days(fp) >= min_age_days:
                add_candidate(root, candidates, "LOW_RISK_GENERATED_CACHE", fp, "empty generated file")
            elif suffix in {".log", ".tmp"} and age_days(fp) >= min_age_days:
                add_candidate(root, candidates, "LOW_RISK_GENERATED_CACHE", fp, "temporary log/tmp file")
    return candidates


def collect_stable_snapshot_candidates(root: Path, keep_latest: int, min_age_days: int) -> List[Candidate]:
    stable = root / "archive/stable"
    folders = [p for p in stable.iterdir() if p.is_dir()] if stable.exists() else []
    folders = sorted(folders, key=lambda p: p.stat().st_mtime, reverse=True)
    candidates: List[Candidate] = []
    for p in folders[keep_latest:]:
        if age_days(p) < min_age_days:
            continue
        if not has_compressed_copy(root, p):
            add_candidate(root, candidates, "OLD_STABLE_SNAPSHOT_FOLDERS", p, "old stable snapshot folder; no compressed copy detected, protected unless explicitly allowed and reviewed")
        else:
            add_candidate(root, candidates, "OLD_STABLE_SNAPSHOT_FOLDERS", p, f"old stable snapshot folder beyond latest {keep_latest}; compressed copy exists")
    return candidates


def collect_compressed_archive_candidates(root: Path, keep_latest: int, min_age_days: int) -> List[Candidate]:
    compressed = root / "archive/stable_compressed"
    zips = [p for p in compressed.glob("*.zip") if p.is_file()] if compressed.exists() else []
    zips = sorted(zips, key=lambda p: p.stat().st_mtime, reverse=True)
    candidates: List[Candidate] = []
    for p in zips[keep_latest:]:
        if age_days(p) >= min_age_days:
            add_candidate(root, candidates, "OLD_COMPRESSED_STABLE_ARCHIVES", p, f"old compressed stable archive beyond latest {keep_latest}")
    return candidates


def collect_v18_backup_candidates(root: Path, keep_latest: int, min_age_days: int) -> List[Candidate]:
    base = root / "archive/v18"
    candidates: List[Candidate] = []
    if not base.exists():
        return candidates
    for category_dir in [p for p in base.iterdir() if p.is_dir()]:
        backups = [p for p in category_dir.iterdir() if p.is_dir()] if category_dir.is_dir() else []
        backups = sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True)
        for p in backups[keep_latest:]:
            if age_days(p) >= min_age_days:
                add_candidate(root, candidates, "OLD_V18_BACKUPS", p, f"old V18 backup under {category_dir.name} beyond latest {keep_latest}")
    # Some older backup folders are directly under archive/v18.
    direct = [p for p in base.iterdir() if p.is_dir() and not any((p / child).is_dir() for child in [])]
    for p in direct:
        if p.name.endswith("_backups") or p.name == "freeze_repair_backups":
            continue
        if age_days(p) >= min_age_days:
            add_candidate(root, candidates, "OLD_V18_BACKUPS", p, "old direct V18 backup folder")
    return candidates


def output_group_key(path: Path) -> str:
    name = path.name
    m = re.match(r"(V18_\d+[A-Z](?:_R\d+)?)_", name)
    if m:
        return m.group(1)
    return path.stem


def collect_old_output_candidates(root: Path, keep_latest: int, min_age_days: int) -> List[Candidate]:
    bases = [root / "outputs/v18/read_center", root / "outputs/v18/ops"]
    groups: Dict[str, List[Path]] = {}
    for base in bases:
        if not base.exists():
            continue
        for p in base.iterdir():
            if not p.is_file():
                continue
            rel = safe_rel(root, p)
            if protection_reason(root, p):
                continue
            if not (p.suffix.lower() in {".md", ".csv", ".txt"} and p.name.startswith("V18_")):
                continue
            groups.setdefault(output_group_key(p), []).append(p)
    candidates: List[Candidate] = []
    for key, paths in groups.items():
        paths = sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)
        for p in paths[keep_latest:]:
            if age_days(p) >= min_age_days:
                add_candidate(root, candidates, "OLD_OUTPUT_HISTORY", p, f"old generated output history for {key} beyond latest {keep_latest}")
    return candidates


def protected_items(root: Path, keep_latest_stable: int, keep_latest_backups: int) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    explicit = [
        "scripts",
        "configs",
        "state",
        "docs/v18/V18_CODEX_SAFETY_CONTRACT.md",
        "docs/v18/V18_CODEX_TASK_TEMPLATE.md",
        "outputs/v18/read_center/V18_CURRENT_*.md",
        "outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md",
        "outputs/v18/ops/V18_CODEX_NEXT_TASK_BRIEF.md",
        "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
        "outputs/v18/recommendations/V18_CURRENT_*",
        "outputs/v18/themes/V18_CURRENT_*",
        str(PROTECTED_FREEZE_REPAIR_BACKUP).replace("\\", "/"),
        ".venv",
    ]
    for rel in explicit:
        rows.append({"path": rel, "reason": "HARD_PROTECTED", "exists": str((root / rel.replace("*", "")).exists()).upper() if "*" not in rel else "GLOB"})
    stable = root / "archive/stable"
    if stable.exists():
        latest = sorted([p for p in stable.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)[:keep_latest_stable]
        for p in latest:
            rows.append({"path": safe_rel(root, p), "reason": f"LATEST_{keep_latest_stable}_STABLE_SNAPSHOT", "exists": "TRUE"})
    compressed = root / "archive/stable_compressed"
    if compressed.exists():
        latest = sorted(compressed.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)[:keep_latest_stable]
        for p in latest:
            rows.append({"path": safe_rel(root, p), "reason": f"LATEST_{keep_latest_stable}_COMPRESSED_STABLE_ARCHIVE", "exists": "TRUE"})
    v18 = root / "archive/v18"
    if v18.exists():
        for category_dir in [p for p in v18.iterdir() if p.is_dir()]:
            backups = [p for p in category_dir.iterdir() if p.is_dir()] if category_dir.is_dir() else []
            for p in sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True)[:keep_latest_backups]:
                rows.append({"path": safe_rel(root, p), "reason": f"LATEST_{keep_latest_backups}_BACKUP_IN_{category_dir.name}", "exists": "TRUE"})
    return rows


def allowed_for_candidate(args: argparse.Namespace, c: Candidate) -> bool:
    if c.protection_check_result != "UNPROTECTED":
        return False
    if c.category == "LOW_RISK_GENERATED_CACHE":
        return bool(args.allow_delete_caches)
    if c.category == "OLD_STABLE_SNAPSHOT_FOLDERS":
        # A compressed copy check is part of the candidate reason; the explicit flag is still required.
        return bool(args.allow_delete_uncompressed_snapshots)
    if c.category == "OLD_COMPRESSED_STABLE_ARCHIVES":
        return bool(args.allow_delete_compressed_archives)
    if c.category == "OLD_V18_BACKUPS":
        return bool(args.allow_delete_old_backups)
    if c.category == "OLD_OUTPUT_HISTORY":
        return bool(args.allow_delete_old_outputs)
    return False


def delete_candidate(root: Path, c: Candidate) -> None:
    if not is_inside(root, c.path):
        c.delete_error = "OUTSIDE_REPO"
        return
    try:
        if c.path.is_dir():
            shutil.rmtree(c.path)
        elif c.path.exists():
            c.path.unlink()
        c.deleted = True
    except Exception as exc:  # noqa: BLE001
        c.delete_error = str(exc)


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_report(
    status: str,
    root: Path,
    before_size: int,
    after_size: int,
    top_level: List[Item],
    key_sizes: Dict[str, int],
    top_file_rows: List[Item],
    top_dir_rows: List[Item],
    candidates: List[Candidate],
    protected_count: int,
    applied: bool,
    warnings: List[str],
) -> str:
    reclaim_by_cat: Dict[str, int] = {}
    for c in candidates:
        if c.protection_check_result == "UNPROTECTED":
            reclaim_by_cat[c.category] = reclaim_by_cat.get(c.category, 0) + c.size_bytes
    deleted_bytes = before_size - after_size if applied else 0
    lines = [
        "# V18.34A Storage Inventory / Safe Cleanup Report",
        "",
        f"- STATUS: `{status}`",
        f"- GENERATED_AT: `{now_iso()}`",
        f"- ROOT: `{root}`",
        f"- APPLY_CLEAN: `{str(applied).upper()}`",
        f"- TOTAL_REPO_SIZE_MB_BEFORE: `{fmt_mb(before_size)}`",
        f"- TOTAL_REPO_SIZE_MB_AFTER: `{fmt_mb(after_size)}`",
        f"- ACTUAL_RECLAIMED_MB: `{fmt_mb(max(0, deleted_bytes))}`",
        f"- DELETE_CANDIDATE_COUNT: `{len(candidates)}`",
        f"- PROTECTED_ITEM_COUNT: `{protected_count}`",
        "",
        "## Top-Level Directory Size",
        "| path | size_mb |",
        "| --- | ---: |",
    ]
    for item in top_level:
        lines.append(f"| `{item.rel_path}` | {fmt_mb(item.size_bytes)} |")
    lines += ["", "## Key Directory Size", "| path | size_mb |", "| --- | ---: |"]
    for rel, size in key_sizes.items():
        lines.append(f"| `{rel}` | {fmt_mb(size)} |")
    lines += ["", "## Estimated Reclaimable By Category", "| category | estimated_mb |", "| --- | ---: |"]
    for category, size in sorted(reclaim_by_cat.items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"| `{category}` | {fmt_mb(size)} |")
    lines += ["", "## Top 20 Largest Files", "| path | size_mb | modified |", "| --- | ---: | --- |"]
    for item in top_file_rows[:20]:
        lines.append(f"| `{item.rel_path}` | {fmt_mb(item.size_bytes)} | {item.modified_time} |")
    lines += ["", "## Top 20 Largest Directories", "| path | size_mb | modified |", "| --- | ---: | --- |"]
    for item in top_dir_rows[:20]:
        lines.append(f"| `{item.rel_path}` | {fmt_mb(item.size_bytes)} | {item.modified_time} |")
    lines += [
        "",
        "## Apply Examples",
        "Review `outputs/v18/ops/V18_34A_STORAGE_DELETE_CANDIDATES.csv` before using any apply command.",
        "",
        "```powershell",
        'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_34A_storage_inventory_safe_cleanup.ps1" -ApplyClean -AllowDeleteCaches',
        "```",
        "```powershell",
        'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_34A_storage_inventory_safe_cleanup.ps1" -ApplyClean -AllowDeleteOldOutputs -KeepLatestOutputs 3 -MinAgeDays 3',
        "```",
        "```powershell",
        'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_34A_storage_inventory_safe_cleanup.ps1" -ApplyClean -AllowDeleteOldBackups -KeepLatestBackups 5 -MinAgeDays 7',
        "```",
        "```powershell",
        'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_34A_storage_inventory_safe_cleanup.ps1" -ApplyClean -AllowDeleteUncompressedSnapshots -KeepLatestStable 5 -MinAgeDays 7',
        "```",
        "```powershell",
        'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_34A_storage_inventory_safe_cleanup.ps1" -ApplyClean -AllowDeleteCompressedArchives -KeepLatestStable 5 -MinAgeDays 14',
        "```",
        "",
        "## Warnings",
    ]
    if warnings:
        for warn in warnings:
            lines.append(f"- WARN: {warn}")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Safety",
        "- Default mode deletes nothing.",
        "- `-ApplyClean` requires category-specific allow flags.",
        "- `scripts/`, `configs/`, `state/`, current reports, active ledgers, current candidates, current recommendations, and current themes are protected.",
        "- No broker/API/trading/order code is added or executed.",
    ]
    return "\n".join(lines) + "\n"


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    warnings: List[str] = []
    if root != Path(r"D:\us-tech-quant").resolve():
        warnings.append(f"non-default root used: {root}")
    if not root.exists():
        print(f"STATUS: {STATUS_FAIL}")
        print(f"FAIL_REASON: root missing: {root}")
        return 1

    before_size = path_size(root)
    top_level = sorted(immediate_dirs(root, root), key=lambda x: x.size_bytes, reverse=True)
    key_dirs = [
        "archive/stable",
        "archive/stable_compressed",
        "archive/v18",
        "outputs/v18",
        "outputs/v17",
        "outputs/v16",
        "logs",
        ".venv",
    ]
    key_sizes = {rel: path_size(root / rel) for rel in key_dirs}
    top_file_rows = top_files(root, 50)
    top_dir_rows = top_dirs(root, 30)

    candidates: List[Candidate] = []
    candidates.extend(collect_cache_candidates(root, args.min_age_days))
    candidates.extend(collect_stable_snapshot_candidates(root, args.keep_latest_stable, args.min_age_days))
    candidates.extend(collect_compressed_archive_candidates(root, args.keep_latest_stable, args.min_age_days))
    candidates.extend(collect_v18_backup_candidates(root, args.keep_latest_backups, args.min_age_days))
    candidates.extend(collect_old_output_candidates(root, args.keep_latest_outputs, args.min_age_days))

    # De-duplicate by path/category while preserving first reason.
    seen = set()
    uniq_candidates: List[Candidate] = []
    for c in candidates:
        key = (c.category, c.rel_path)
        if key not in seen:
            seen.add(key)
            uniq_candidates.append(c)
    candidates = uniq_candidates

    for c in candidates:
        c.allowed_by_flags = allowed_for_candidate(args, c)

    protected_rows = protected_items(root, args.keep_latest_stable, args.keep_latest_backups)
    ambiguous_count = sum(1 for c in candidates if c.protection_check_result != "UNPROTECTED")
    if ambiguous_count:
        warnings.append(f"{ambiguous_count} candidates were protected by safety checks")

    applied = bool(args.apply_clean and not args.dry_run)
    if args.apply_clean and not any(
        [
            args.allow_delete_caches,
            args.allow_delete_uncompressed_snapshots,
            args.allow_delete_compressed_archives,
            args.allow_delete_old_backups,
            args.allow_delete_old_outputs,
        ]
    ):
        warnings.append("ApplyClean was supplied without any category allow flag; no deletion allowed")

    if applied:
        for c in candidates:
            if c.allowed_by_flags:
                delete_candidate(root, c)

    after_size = path_size(root)
    deleted_bytes = before_size - after_size if applied else 0
    fail_count = sum(1 for c in candidates if c.delete_error)
    if fail_count:
        status = STATUS_FAIL
    else:
        status = STATUS_WARN if warnings else STATUS_OK

    reclaim_by_cat: Dict[str, int] = {}
    for c in candidates:
        if c.protection_check_result == "UNPROTECTED":
            reclaim_by_cat[c.category] = reclaim_by_cat.get(c.category, 0) + c.size_bytes

    summary_rows = [
        {
            "status": status,
            "generated_at": now_iso(),
            "root": str(root),
            "dry_run": str(bool(args.dry_run)).upper(),
            "apply_clean": str(bool(args.apply_clean)).upper(),
            "total_repo_size_mb_before": fmt_mb(before_size),
            "total_repo_size_mb_after": fmt_mb(after_size),
            "delete_candidate_count": len(candidates),
            "protected_item_count": len(protected_rows),
            "estimated_reclaimable_mb": fmt_mb(sum(reclaim_by_cat.values())),
            "actual_reclaimed_mb": fmt_mb(max(0, deleted_bytes)),
            "warning_count": len(warnings),
            "fail_count": fail_count,
            "auto_trade": "DISABLED",
            "auto_sell": "DISABLED",
            "official_decision_impact": "NONE",
            "forbidden_modified": "FALSE",
        }
    ]

    candidate_rows = [
        {
            "category": c.category,
            "path": c.rel_path,
            "item_type": c.item_type,
            "size_bytes": c.size_bytes,
            "size_mb": fmt_mb(c.size_bytes),
            "modified_time": c.modified_time,
            "reason": c.reason,
            "protection_check_result": c.protection_check_result,
            "allowed_by_flags": str(c.allowed_by_flags).upper(),
        }
        for c in sorted(candidates, key=lambda x: x.size_bytes, reverse=True)
    ]
    manifest_rows = [
        {
            "timestamp": now_iso(),
            "category": c.category,
            "path": c.rel_path,
            "item_type": c.item_type,
            "size_bytes": c.size_bytes,
            "modified_time": c.modified_time,
            "reason": c.reason,
            "protection_check_result": c.protection_check_result,
            "allowed_by_flags": str(c.allowed_by_flags).upper(),
            "deleted": str(c.deleted).upper(),
            "delete_error": c.delete_error,
        }
        for c in sorted(candidates, key=lambda x: x.size_bytes, reverse=True)
    ]

    write_csv(root / OUT_SUMMARY, summary_rows, list(summary_rows[0].keys()))
    write_csv(root / OUT_CANDIDATES, candidate_rows, list(candidate_rows[0].keys()) if candidate_rows else ["category", "path", "item_type", "size_bytes", "size_mb", "modified_time", "reason", "protection_check_result", "allowed_by_flags"])
    write_csv(root / OUT_PROTECTED, protected_rows, ["path", "reason", "exists"])
    write_csv(root / OUT_MANIFEST, manifest_rows, list(manifest_rows[0].keys()) if manifest_rows else ["timestamp", "category", "path", "item_type", "size_bytes", "modified_time", "reason", "protection_check_result", "allowed_by_flags", "deleted", "delete_error"])

    report_text = build_report(
        status,
        root,
        before_size,
        after_size,
        top_level,
        key_sizes,
        top_file_rows,
        top_dir_rows,
        candidates,
        len(protected_rows),
        applied,
        warnings,
    )
    (root / OUT_REPORT).parent.mkdir(parents=True, exist_ok=True)
    (root / OUT_REPORT).write_text(report_text, encoding="utf-8")
    (root / OUT_CURRENT).write_text(report_text, encoding="utf-8")
    (root / OUT_READ_FIRST).write_text(
        "\n".join(
            [
                f"STATUS: {status}",
                f"TOTAL_REPO_SIZE_MB_BEFORE: {fmt_mb(before_size)}",
                f"DELETE_CANDIDATE_COUNT: {len(candidates)}",
                f"ESTIMATED_RECLAIMABLE_MB: {fmt_mb(sum(reclaim_by_cat.values()))}",
                f"ACTUAL_RECLAIMED_MB: {fmt_mb(max(0, deleted_bytes))}",
                "READ_FIRST:",
                "1. outputs/v18/read_center/V18_CURRENT_STORAGE_CLEANUP.md",
                "2. outputs/v18/ops/V18_34A_STORAGE_DELETE_CANDIDATES.csv",
                "3. outputs/v18/ops/V18_34A_STORAGE_PROTECTED_ITEMS.csv",
                "4. outputs/v18/ops/V18_34A_STORAGE_DELETION_MANIFEST.csv",
                "5. docs/v18/V18_CODEX_SAFETY_CONTRACT.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"STATUS: {status}")
    print(f"TOTAL_REPO_SIZE_MB_BEFORE: {fmt_mb(before_size)}")
    print(f"DELETE_CANDIDATE_COUNT: {len(candidates)}")
    print(f"ESTIMATED_RECLAIMABLE_MB: {fmt_mb(sum(reclaim_by_cat.values()))}")
    print(f"ACTUAL_RECLAIMED_MB: {fmt_mb(max(0, deleted_bytes))}")
    print(f"REPORT: {root / OUT_REPORT}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    if fail_count:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.34A storage inventory and safe cleanup.")
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply-clean", action="store_true")
    parser.add_argument("--keep-latest-stable", type=int, default=5)
    parser.add_argument("--keep-latest-backups", type=int, default=5)
    parser.add_argument("--keep-latest-outputs", type=int, default=3)
    parser.add_argument("--min-age-days", type=int, default=0)
    parser.add_argument("--allow-delete-uncompressed-snapshots", action="store_true")
    parser.add_argument("--allow-delete-compressed-archives", action="store_true")
    parser.add_argument("--allow-delete-old-backups", action="store_true")
    parser.add_argument("--allow-delete-old-outputs", action="store_true")
    parser.add_argument("--allow-delete-caches", action="store_true")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
