from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import zipfile


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
OPS_DIR = Path("outputs/v18/ops")

V18_20A_DEPENDENCY_AUDIT = OPS_DIR / "V18_20A_CURRENT_DEPENDENCY_REFERENCE_AUDIT.csv"
V18_20A_PROTECTED_FILES = OPS_DIR / "V18_20A_CURRENT_DEEP_CLEANUP_PROTECTED_FILES.csv"
V18_20F_PLAN = OPS_DIR / "V18_20F_CURRENT_LEGACY_ARCHIVE_PLAN.csv"
V18_20G_AUDIT = OPS_DIR / "V18_20G_CURRENT_VERIFIED_LEGACY_ARCHIVE_AUDIT.csv"
V18_20G_MANIFEST = OPS_DIR / "V18_20G_CURRENT_VERIFIED_LEGACY_ARCHIVE_MANIFEST.csv"

READ_FIRST_PATH = OPS_DIR / "V18_20H_READ_FIRST.txt"
EMPTY_DIR_AUDIT_PATH = OPS_DIR / "V18_20H_CURRENT_EMPTY_DIR_AUDIT.csv"
ORPHAN_OUTPUT_AUDIT_PATH = OPS_DIR / "V18_20H_CURRENT_ORPHAN_OUTPUT_AUDIT.csv"
ARCHIVED_ORIGINAL_CANDIDATES_PATH = OPS_DIR / "V18_20H_CURRENT_ARCHIVED_ORIGINAL_DELETE_CANDIDATES.csv"
PROTECTED_EXCLUSIONS_PATH = OPS_DIR / "V18_20H_CURRENT_PROTECTED_CLEANUP_EXCLUSIONS.csv"
REPORT_PATH = OPS_DIR / "V18_20H_CURRENT_EMPTY_ORPHAN_CLEANUP_REPORT.md"

CURRENT_ACTIVE_DIRS = [
    "outputs/v18/read_center",
    "outputs/v18/read_center/daily_packet",
    "outputs/v18/ops",
    "outputs/v18/universe",
    "outputs/v18/ranking",
    "outputs/v18/factor_pack",
    "outputs/v18/data",
    "outputs/v18/risk",
]

PROTECTED_DIR_PREFIXES = (
    ".git/",
    ".venv/",
    "state/",
    "configs/",
    "archive/stable/",
    "archive/stable_compressed/",
    "archive/generated_outputs_compressed/",
    "provider_cache/",
    "price_cache/",
)

CURRENT_ALIAS_KEYWORDS = ("CURRENT",)
REF_KEYWORDS = ("V18_CURRENT_DAILY_COMMAND_CENTER", "V18_CURRENT_DAILY_BRIEF", "V18_19A", "MANIFEST.CSV", "RESTORE_")

EMPTY_DIR_FIELDS = [
    "path",
    "depth",
    "parent",
    "category",
    "reason",
    "protected_root_related",
    "current_active_dir_related",
    "latest_archive_related",
]

ORPHAN_FIELDS = [
    "path",
    "size_mb",
    "extension",
    "modified_time",
    "orphan_category",
    "proposed_later_action",
    "reason",
    "reference_count",
    "referenced_by_sample",
    "current_alias_related",
    "stable_snapshot_related",
    "archived_by_v18_20G",
    "zip_path",
    "zip_verified",
    "source_exists",
    "dangerous_token_related",
    "confidence",
]

ARCHIVED_ORIGINAL_FIELDS = [
    "source_path",
    "archive_group",
    "proposed_later_action",
    "size_mb",
    "confidence",
    "reason",
    "reference_count",
    "referenced_by_sample",
    "source_exists",
    "zip_path",
    "zip_verified",
]

PROTECTED_FIELDS = [
    "path",
    "item_type",
    "size_mb",
    "reason",
    "reference_count",
    "referenced_by_sample",
    "current_alias_related",
    "stable_snapshot_related",
    "manual_state_related",
    "price_cache_related",
    "source_code_related",
    "generated_output_related",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize(value: object) -> str:
    return str(value or "").strip()


def safe_bool(value: object, default: bool = False) -> bool:
    text = normalize(value).upper()
    if text in {"TRUE", "T", "YES", "Y", "1"}:
        return True
    if text in {"FALSE", "F", "NO", "N", "0"}:
        return False
    return default


def safe_float(value: object, default: float = 0.0) -> float:
    text = normalize(value).replace(",", "")
    if not text:
        return default
    try:
        return float(text)
    except Exception:
        return default


def safe_int(value: object, default: int = 0) -> int:
    text = normalize(value).replace(",", "")
    if not text:
        return default
    try:
        return int(float(text))
    except Exception:
        return default


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    raise RuntimeError(f"Failed to read CSV: {path}")


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_mtime(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def latest_stable_snapshot_name(root: Path) -> str:
    stable_root = root / "archive/stable"
    if not stable_root.exists():
        return ""
    dirs = [p for p in stable_root.iterdir() if p.is_dir()]
    if not dirs:
        return ""
    return max(dirs, key=lambda p: p.stat().st_mtime).name


def latest_v18g_archive_root(root: Path) -> Path:
    base = root / "archive/legacy_cleanup"
    if not base.exists():
        return Path()
    candidates = sorted(
        (p for p in base.iterdir() if p.is_dir() and p.name.startswith("V18_20G_verified_legacy_archive_")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else Path()


def load_reference_index(*paths: Path) -> Dict[str, Dict[str, object]]:
    index: Dict[str, Dict[str, object]] = {}
    for path in paths:
        for row in read_csv(path):
            rel_path = normalize(row.get("path") or row.get("source_path")).replace("\\", "/")
            if not rel_path:
                continue
            entry = index.setdefault(rel_path, {})
            for key, value in row.items():
                if key == "path" or key == "source_path":
                    continue
                if value not in ("", None):
                    entry[key] = value
    return index


def load_archive_index(root: Path) -> Dict[str, Dict[str, object]]:
    audit_rows = read_csv(root / V18_20G_AUDIT)
    manifest_rows = read_csv(root / V18_20G_MANIFEST)
    index: Dict[str, Dict[str, object]] = {}
    for row in audit_rows + manifest_rows:
        rel_path = normalize(row.get("source_path")).replace("\\", "/")
        if not rel_path:
            continue
        entry = index.setdefault(rel_path, {})
        for key, value in row.items():
            if value not in ("", None):
                entry[key] = value
        entry["archived_by_v18_20G"] = True
    return index


def load_plan_index(root: Path) -> Dict[str, Dict[str, object]]:
    index: Dict[str, Dict[str, object]] = {}
    for row in read_csv(root / V18_20F_PLAN):
        rel_path = normalize(row.get("path")).replace("\\", "/")
        if not rel_path:
            continue
        index[rel_path] = row
    return index


def is_protected_prefix(rel_path: str) -> bool:
    lower = rel_path.lower()
    return any(lower.startswith(prefix) for prefix in PROTECTED_DIR_PREFIXES)


def is_current_active_dir(rel_path: str) -> bool:
    lower = rel_path.lower()
    return any(lower == prefix or lower.startswith(prefix + "/") for prefix in CURRENT_ACTIVE_DIRS)


def is_current_alias_related(rel_path: str, meta: Dict[str, object]) -> bool:
    if safe_bool(meta.get("current_alias_related")):
        return True
    return any(keyword in rel_path.upper() for keyword in CURRENT_ALIAS_KEYWORDS)


def is_stable_snapshot_related(rel_path: str, meta: Dict[str, object], latest_snapshot_name: str) -> bool:
    if safe_bool(meta.get("stable_snapshot_related")):
        return True
    lower = rel_path.lower()
    return lower.startswith("archive/stable/") or (latest_snapshot_name and latest_snapshot_name.lower() in lower)


def is_manual_state_related(rel_path: str, meta: Dict[str, object]) -> bool:
    if safe_bool(meta.get("manual_state_related")):
        return True
    lower = rel_path.lower()
    return any(tok in lower for tok in ("manual", "trade", "position", "feedback")) and "/state/" in f"/{lower}/"


def is_price_cache_related(rel_path: str, meta: Dict[str, object]) -> bool:
    if safe_bool(meta.get("price_cache_related")):
        return True
    lower = rel_path.lower()
    return "provider_cache" in lower or "price_cache" in lower or "/data/prices/" in lower


def is_source_code_related(rel_path: str, meta: Dict[str, object]) -> bool:
    if safe_bool(meta.get("source_code_related")):
        return True
    return Path(rel_path).suffix.lower() in {".py", ".ps1", ".bat", ".sh"}


def is_generated_output_related(rel_path: str, meta: Dict[str, object]) -> bool:
    if safe_bool(meta.get("generated_output_related")):
        return True
    lower = rel_path.lower()
    return lower.startswith("outputs/") or lower.startswith("archive/") or Path(lower).suffix.lower() in {".csv", ".md", ".txt", ".log", ".json", ".zip"}


def is_dangerous_token_related(rel_path: str, meta: Dict[str, object]) -> bool:
    if safe_bool(meta.get("dangerous_token_related")):
        return True
    lower = rel_path.lower()
    return any(tok in lower for tok in ("buy", "sell", "order", "broker", "trade", "execute", "auto_trade", "auto_sell"))


def compute_meta(rel_path: str, ref_index: Dict[str, Dict[str, object]], protected_index: Dict[str, Dict[str, object]], archive_index: Dict[str, Dict[str, object]], plan_index: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    meta: Dict[str, object] = {}
    for source in (ref_index.get(rel_path, {}), protected_index.get(rel_path, {}), archive_index.get(rel_path, {}), plan_index.get(rel_path, {})):
        for key, value in source.items():
            if value not in ("", None) and key not in meta:
                meta[key] = value
    return meta


def classify_empty_dir(
    root: Path,
    dir_path: Path,
) -> Dict[str, object]:
    rel_path = rel(root, dir_path)
    protected = is_protected_prefix(rel_path) or rel_path in {"archive/legacy_cleanup/V18_20G_verified_legacy_archive_20260519_200428"}
    active = is_current_active_dir(rel_path)
    latest_archive = rel_path.startswith("archive/legacy_cleanup/")
    if protected or active:
        category = "EMPTY_DIR_PROTECTED"
        reason = "Protected or active directory; keep empty folder."
    elif latest_archive:
        category = "EMPTY_DIR_REVIEW_REQUIRED"
        reason = "Archive-legacy directory; keep under review."
    else:
        category = "EMPTY_DIR_DELETE_CANDIDATE"
        reason = "Empty leaf directory outside protected active paths."
    return {
        "path": rel_path,
        "depth": str(len(Path(rel_path).parts)),
        "parent": rel(root, dir_path.parent),
        "category": category,
        "reason": reason,
        "protected_root_related": str(protected).upper(),
        "current_active_dir_related": str(active).upper(),
        "latest_archive_related": str(latest_archive).upper(),
    }


def scan_empty_dirs(root: Path) -> List[Dict[str, object]]:
    candidate_roots = [
        root / "outputs",
        root / "archive",
        root / "scripts",
        root / "state",
        root / "configs",
        root / "provider_cache",
        root / "price_cache",
    ]
    rows: List[Dict[str, object]] = []
    seen: set[str] = set()
    for scan_root in candidate_roots:
        if not scan_root.exists():
            continue
        for current, dirnames, filenames in os.walk(scan_root, topdown=False):
            if dirnames or filenames:
                continue
            dir_path = Path(current)
            rel_path = rel(root, dir_path)
            if rel_path in seen:
                continue
            seen.add(rel_path)
            rows.append(classify_empty_dir(root, dir_path))
    return sorted(rows, key=lambda r: (r["category"], r["path"]))


def scan_orphan_outputs(
    root: Path,
    ref_index: Dict[str, Dict[str, object]],
    protected_index: Dict[str, Dict[str, object]],
    archive_index: Dict[str, Dict[str, object]],
    plan_index: Dict[str, Dict[str, object]],
    latest_snapshot_name: str,
    latest_archive_root: Path,
) -> List[Dict[str, object]]:
    candidate_roots = [
        root / "outputs/v17",
        root / "outputs/v18",
        root / "archive/deprecated",
        root / "archive/legacy_cleanup",
    ]
    rows: List[Dict[str, object]] = []
    for scan_root in candidate_roots:
        if not scan_root.exists():
            continue
        for current, dirnames, filenames in os.walk(scan_root):
            cur_path = Path(current)
            if latest_archive_root and cur_path.resolve() == latest_archive_root.resolve():
                dirnames[:] = []
                continue
            for name in filenames:
                path = cur_path / name
                rel_path = rel(root, path)
                if rel_path.startswith("archive/legacy_cleanup/V18_20G_verified_legacy_archive_"):
                    continue
                if is_protected_prefix(rel_path) or rel_path.startswith("archive/stable/") or rel_path.startswith("archive/stable_compressed/") or rel_path.startswith("archive/generated_outputs_compressed/"):
                    continue
                if is_current_active_dir(rel_path):
                    continue
                meta = compute_meta(rel_path, ref_index, protected_index, archive_index, plan_index)
                reference_count = safe_int(meta.get("reference_count"))
                referenced_by_sample = normalize(meta.get("referenced_by_sample"))
                current_alias_related = is_current_alias_related(rel_path, meta)
                stable_snapshot_related = is_stable_snapshot_related(rel_path, meta, latest_snapshot_name)
                manual_state_related = is_manual_state_related(rel_path, meta)
                price_cache_related = is_price_cache_related(rel_path, meta)
                source_code_related = is_source_code_related(rel_path, meta)
                generated_output_related = is_generated_output_related(rel_path, meta)
                dangerous_token_related = is_dangerous_token_related(rel_path, meta)
                source_exists = path.exists()
                size_mb = path.stat().st_size / (1024 * 1024) if source_exists else 0.0
                modified_time = iso_mtime(path) if source_exists else ""
                archived_by_v18_20G = safe_bool(meta.get("archived_by_v18_20G"))
                zip_path = normalize(meta.get("zip_path"))
                zip_verified = safe_bool(meta.get("zip_verified"))

                orphan_category = "REVIEW_REQUIRED"
                proposed_later_action = "REVIEW_MANUALLY"
                confidence = "LOW"
                reason = "Unclassified or uncertain cleanup candidate."

                if archived_by_v18_20G and zip_verified and source_exists:
                    orphan_category = "VERIFIED_ARCHIVED_ORIGINAL"
                    if normalize(meta.get("archive_group")) == "OLD_GENERATED_REPORTS":
                        proposed_later_action = "DELETE_AFTER_ARCHIVE_VERIFICATION"
                        reason = "Original was archived in V18.20G and the zip verified successfully."
                        confidence = "HIGH"
                    else:
                        proposed_later_action = "KEEP_PROTECTED"
                        reason = "Archived in V18.20G but not a generated-report original."
                        confidence = "MEDIUM"
                elif current_alias_related:
                    orphan_category = "PROTECTED_CURRENT_ALIAS"
                    proposed_later_action = "KEEP_PROTECTED"
                    reason = "Current alias or active output should be preserved."
                    confidence = "HIGH"
                elif reference_count > 0:
                    orphan_category = "REVIEW_REQUIRED"
                    proposed_later_action = "REVIEW_MANUALLY"
                    reason = "Referenced output is not a cleanup candidate."
                    confidence = "MEDIUM"
                else:
                    lower = rel_path.lower()
                    if lower.startswith("outputs/v17/"):
                        orphan_category = "OLD_V17_OUTPUT"
                    elif lower.startswith("archive/deprecated/"):
                        orphan_category = "OLD_DEPRECATED_ARCHIVE_OUTPUT"
                    elif lower.startswith("outputs/v18/") and "current" not in lower:
                        orphan_category = "OLD_V18_SUPERSEDED_OUTPUT"
                    elif path.suffix.lower() == ".log":
                        orphan_category = "OLD_LOG"
                    elif any(ch.isdigit() for ch in path.name) and "current" not in lower:
                        orphan_category = "OLD_TIMESTAMPED_OUTPUT"
                    else:
                        orphan_category = "REVIEW_REQUIRED"
                    if orphan_category in {"OLD_V17_OUTPUT", "OLD_DEPRECATED_ARCHIVE_OUTPUT", "OLD_V18_SUPERSEDED_OUTPUT", "OLD_LOG", "OLD_TIMESTAMPED_OUTPUT"}:
                        proposed_later_action = "DELETE_AFTER_ARCHIVE_VERIFICATION"
                        reason = "Old unreferenced output/log with no active alias or protected path."
                        confidence = "MEDIUM"
                    else:
                        proposed_later_action = "REVIEW_MANUALLY"
                        reason = "Unclear whether this file is obsolete or still useful."
                        confidence = "LOW"

                rows.append(
                    {
                        "path": rel_path,
                        "size_mb": f"{size_mb:.3f}",
                        "extension": path.suffix.lower() or "",
                        "modified_time": modified_time,
                        "orphan_category": orphan_category,
                        "proposed_later_action": proposed_later_action,
                        "reason": reason,
                        "reference_count": str(reference_count),
                        "referenced_by_sample": referenced_by_sample,
                        "current_alias_related": str(current_alias_related).upper(),
                        "stable_snapshot_related": str(stable_snapshot_related).upper(),
                        "archived_by_v18_20G": str(archived_by_v18_20G).upper(),
                        "zip_path": zip_path,
                        "zip_verified": str(zip_verified).upper(),
                        "source_exists": str(source_exists).upper(),
                        "dangerous_token_related": str(dangerous_token_related).upper(),
                        "confidence": confidence,
                        "source_code_related": str(source_code_related).upper(),
                        "generated_output_related": str(generated_output_related).upper(),
                        "_meta": meta,
                    }
                )
    return sorted(rows, key=lambda r: (-safe_float(r.get("size_mb")), r["path"]))


def archived_original_candidates(root: Path, orphan_rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for row in orphan_rows:
        if normalize(row.get("archived_by_v18_20G")) != "TRUE":
            continue
        if normalize(row.get("zip_verified")) != "TRUE":
            continue
        if normalize(row.get("source_exists")) != "TRUE":
            continue
        if normalize(row.get("current_alias_related")) == "TRUE":
            continue
        if normalize(row.get("source_code_related")) == "TRUE" and normalize(row.get("orphan_category")) != "VERIFIED_ARCHIVED_ORIGINAL":
            continue
        archive_group = normalize(row.get("_meta", {}).get("archive_group"))
        if archive_group == "OLD_GENERATED_REPORTS":
            proposed = "DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE"
            reason = "Verified archived original from OLD_GENERATED_REPORTS; eligible for later delete step."
            confidence = "HIGH"
        else:
            proposed = "KEEP_ARCHIVED_ONLY_DO_NOT_DELETE_ORIGINAL"
            reason = "Archived original is not a generated-report original and should remain archived only."
            confidence = "MEDIUM"
        rows.append(
            {
                "source_path": row["path"],
                "archive_group": archive_group,
                "proposed_later_action": proposed,
                "size_mb": row["size_mb"],
                "confidence": confidence,
                "reason": reason,
                "reference_count": row["reference_count"],
                "referenced_by_sample": row["referenced_by_sample"],
                "source_exists": row["source_exists"],
                "zip_path": row["zip_path"],
                "zip_verified": row["zip_verified"],
            }
        )
    return sorted(rows, key=lambda r: (-safe_float(r.get("size_mb")), r["source_path"]))


def protected_exclusions(
    root: Path,
    empty_dir_rows: Sequence[Dict[str, object]],
    orphan_rows: Sequence[Dict[str, object]],
    archived_candidates: Sequence[Dict[str, object]],
    protected_index: Dict[str, Dict[str, object]],
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    for row in empty_dir_rows:
        if normalize(row.get("category")) == "EMPTY_DIR_DELETE_CANDIDATE":
            continue
        rows.append(
            {
                "path": row["path"],
                "item_type": "DIR",
                "size_mb": "0.000",
                "reason": row["reason"],
                "reference_count": "0",
                "referenced_by_sample": "",
                "current_alias_related": row["current_active_dir_related"],
                "stable_snapshot_related": row["latest_archive_related"],
                "manual_state_related": "FALSE",
                "price_cache_related": "FALSE",
                "source_code_related": "FALSE",
                "generated_output_related": "FALSE",
            }
        )

    for row in orphan_rows:
        if normalize(row.get("orphan_category")) == "REVIEW_REQUIRED":
            continue
        if normalize(row.get("proposed_later_action")) == "DELETE_AFTER_ARCHIVE_VERIFICATION":
            continue
        rows.append(
            {
                "path": row["path"],
                "item_type": "FILE",
                "size_mb": row["size_mb"],
                "reason": row["reason"],
                "reference_count": row["reference_count"],
                "referenced_by_sample": row["referenced_by_sample"],
                "current_alias_related": row["current_alias_related"],
                "stable_snapshot_related": row["stable_snapshot_related"],
                "manual_state_related": "FALSE",
                "price_cache_related": "FALSE",
                "source_code_related": row["source_code_related"],
                "generated_output_related": row["generated_output_related"],
            }
        )

    for path, meta in protected_index.items():
        rows.append(
            {
                "path": path,
                "item_type": "FILE",
                "size_mb": normalize(meta.get("size_mb")),
                "reason": normalize(meta.get("reason")) or "Protected by dependency/reference policy.",
                "reference_count": normalize(meta.get("reference_count")) or "0",
                "referenced_by_sample": normalize(meta.get("referenced_by_sample")),
                "current_alias_related": str(safe_bool(meta.get("current_alias_related"))).upper(),
                "stable_snapshot_related": str(safe_bool(meta.get("stable_snapshot_related"))).upper(),
                "manual_state_related": str(safe_bool(meta.get("manual_state_related"))).upper(),
                "price_cache_related": str(safe_bool(meta.get("price_cache_related"))).upper(),
                "source_code_related": str(safe_bool(meta.get("source_code_related"))).upper(),
                "generated_output_related": str(safe_bool(meta.get("generated_output_related"))).upper(),
            }
        )

    # Deduplicate by path/item_type keeping the first seen row.
    dedup: Dict[Tuple[str, str], Dict[str, object]] = {}
    for row in rows:
        key = (normalize(row.get("path")), normalize(row.get("item_type")))
        dedup.setdefault(key, row)
    return sorted(dedup.values(), key=lambda r: (-safe_float(r.get("size_mb")), r["path"]))


def render_report(
    root: Path,
    archive_root: Path,
    empty_rows: Sequence[Dict[str, object]],
    orphan_rows: Sequence[Dict[str, object]],
    archived_rows: Sequence[Dict[str, object]],
    protected_rows: Sequence[Dict[str, object]],
    latest_snapshot_name: str,
) -> str:
    empty_candidates = [r for r in empty_rows if r["category"] == "EMPTY_DIR_DELETE_CANDIDATE"]
    empty_protected = [r for r in empty_rows if r["category"] == "EMPTY_DIR_PROTECTED"]
    empty_review = [r for r in empty_rows if r["category"] == "EMPTY_DIR_REVIEW_REQUIRED"]
    orphan_counts = Counter(normalize(r.get("orphan_category")) for r in orphan_rows)
    orphan_mb = {
        key: sum(safe_float(r.get("size_mb")) for r in orphan_rows if normalize(r.get("orphan_category")) == key)
        for key in orphan_counts
    }

    lines = [
        "# V18.20H Empty Folder and Orphan Output Cleanup Report",
        "",
        "- STATUS: OK_V18_20H_EMPTY_ORPHAN_CLEANUP_READY",
        "- MODE: DRYRUN",
        f"- ROOT: {root}",
        f"- ARCHIVE_ROOT: {archive_root}",
        f"- EMPTY_DIR_COUNT: {len(empty_rows)}",
        f"- EMPTY_DIR_DELETE_CANDIDATE_COUNT: {len(empty_candidates)}",
        f"- EMPTY_DIR_PROTECTED_COUNT: {len(empty_protected)}",
        f"- EMPTY_DIR_REVIEW_REQUIRED_COUNT: {len(empty_review)}",
        f"- ORPHAN_OUTPUT_COUNT: {len(orphan_rows)}",
        f"- ORPHAN_OUTPUT_MB: {sum(safe_float(r.get('size_mb')) for r in orphan_rows):.3f}",
        f"- VERIFIED_ARCHIVED_ORIGINAL_DELETE_CANDIDATE_COUNT: {len([r for r in archived_rows if normalize(r.get('proposed_later_action')) == 'DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE'])}",
        f"- VERIFIED_ARCHIVED_ORIGINAL_DELETE_CANDIDATE_MB: {sum(safe_float(r.get('size_mb')) for r in archived_rows if normalize(r.get('proposed_later_action')) == 'DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE'):.3f}",
        f"- PROTECTED_EXCLUSION_COUNT: {len(protected_rows)}",
        f"- PROTECTED_EXCLUSION_MB: {sum(safe_float(r.get('size_mb')) for r in protected_rows):.3f}",
        "- DELETED_FILE_COUNT: 0",
        "- DELETED_DIR_COUNT: 0",
        "- MOVED_COUNT: 0",
        "- ARCHIVED_COUNT: 0",
        "- ZIP_CREATED_COUNT: 0",
        "- VALIDATION_FAIL_COUNT: 0",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- CURRENT_DAILY_MODIFIED: FALSE",
        "- STABLE_SNAPSHOT_MODIFIED: FALSE",
        "- MANUAL_STATE_MODIFIED: FALSE",
        "- PRICE_CACHE_MODIFIED: FALSE",
        f"- LATEST_STABLE_SNAPSHOT_NAME: {latest_snapshot_name}",
        "",
        "## Empty Directories By Category",
    ]
    lines.append(f"- EMPTY_DIR_DELETE_CANDIDATE: {len(empty_candidates)}")
    lines.append(f"- EMPTY_DIR_PROTECTED: {len(empty_protected)}")
    lines.append(f"- EMPTY_DIR_REVIEW_REQUIRED: {len(empty_review)}")
    lines.extend(["", "## Orphan Output Categories"])
    for category in [
        "OLD_TIMESTAMPED_OUTPUT",
        "OLD_LOG",
        "OLD_DEPRECATED_ARCHIVE_OUTPUT",
        "OLD_V17_OUTPUT",
        "OLD_V18_SUPERSEDED_OUTPUT",
        "VERIFIED_ARCHIVED_ORIGINAL",
        "PROTECTED_CURRENT_ALIAS",
        "REVIEW_REQUIRED",
    ]:
        lines.append(f"- {category}: {orphan_counts.get(category, 0)} / {orphan_mb.get(category, 0.0):.3f} MB")
    lines.extend(["", "## Recommendation", ""])
    if len(empty_candidates) > 0:
        lines.append("- Empty directory deletion looks worthwhile for leaf folders outside protected active paths.")
    else:
        lines.append("- No safe empty directory deletion candidates were found.")
    if len(archived_rows) > 0:
        lines.append("- Later delete only verified OLD_GENERATED_REPORTS originals after a separate approval step.")
    else:
        lines.append("- No verified archived-original delete candidates were found.")
    lines.append("- Keep source scripts and wrappers archive-only unless they are separately reviewed.")
    lines.extend(["", "## Top 30 Largest Orphan Outputs"])
    for row in sorted(orphan_rows, key=lambda r: (-safe_float(r.get("size_mb")), r["path"]))[:30]:
        lines.append(f"- {row['path']} | {row['size_mb']} MB | {row['orphan_category']} | {row['proposed_later_action']}")
    lines.extend(["", "## Top 30 Verified Archived-Original Candidates"])
    for row in sorted(archived_rows, key=lambda r: (-safe_float(r.get("size_mb")), r["source_path"]))[:30]:
        lines.append(f"- {row['source_path']} | {row['size_mb']} MB | {row['proposed_later_action']} | {row['reason']}")
    lines.extend(["", f"- READ_FIRST: {READ_FIRST_PATH.as_posix()}", f"- REPORT: {REPORT_PATH.as_posix()}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.20H empty folder and orphan output cleanup audit")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    parser.add_argument("--apply-empty-dirs-only", action="store_true", help="Reserved for a later apply step; not used in DRYRUN.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    latest_snapshot_name = latest_stable_snapshot_name(root)
    latest_archive_root = latest_v18g_archive_root(root)

    ref_index = load_reference_index(root / V18_20A_DEPENDENCY_AUDIT, root / V18_20A_PROTECTED_FILES)
    protected_index = load_reference_index(root / V18_20A_PROTECTED_FILES)
    archive_index = load_archive_index(root)
    plan_index = load_plan_index(root)

    empty_rows = scan_empty_dirs(root)
    orphan_rows = scan_orphan_outputs(root, ref_index, protected_index, archive_index, plan_index, latest_snapshot_name, latest_archive_root)
    archived_rows = archived_original_candidates(root, orphan_rows)
    protected_rows = protected_exclusions(root, empty_rows, orphan_rows, archived_rows, protected_index)

    # Empty dir CSV
    write_csv(root / EMPTY_DIR_AUDIT_PATH, empty_rows, EMPTY_DIR_FIELDS)
    # Orphan output CSV
    orphan_csv_rows = [
        {
            k: row[k]
            for k in ORPHAN_FIELDS
        }
        for row in orphan_rows
    ]
    write_csv(root / ORPHAN_OUTPUT_AUDIT_PATH, orphan_csv_rows, ORPHAN_FIELDS)
    # Archived originals CSV
    write_csv(root / ARCHIVED_ORIGINAL_CANDIDATES_PATH, archived_rows, ARCHIVED_ORIGINAL_FIELDS)
    # Protected exclusions CSV
    write_csv(root / PROTECTED_EXCLUSIONS_PATH, protected_rows, PROTECTED_FIELDS)

    read_first = "\n".join(
        [
            "STATUS: OK_V18_20H_EMPTY_ORPHAN_CLEANUP_READY",
            "MODE: DRYRUN",
            f"ROOT: {root}",
            f"EMPTY_DIR_COUNT: {len(empty_rows)}",
            f"EMPTY_DIR_DELETE_CANDIDATE_COUNT: {len([r for r in empty_rows if r['category'] == 'EMPTY_DIR_DELETE_CANDIDATE'])}",
            f"EMPTY_DIR_PROTECTED_COUNT: {len([r for r in empty_rows if r['category'] == 'EMPTY_DIR_PROTECTED'])}",
            f"EMPTY_DIR_REVIEW_REQUIRED_COUNT: {len([r for r in empty_rows if r['category'] == 'EMPTY_DIR_REVIEW_REQUIRED'])}",
            f"ORPHAN_OUTPUT_COUNT: {len(orphan_rows)}",
            f"ORPHAN_OUTPUT_MB: {sum(safe_float(r.get('size_mb')) for r in orphan_rows):.3f}",
            f"VERIFIED_ARCHIVED_ORIGINAL_DELETE_CANDIDATE_COUNT: {len([r for r in archived_rows if normalize(r.get('proposed_later_action')) == 'DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE'])}",
            f"VERIFIED_ARCHIVED_ORIGINAL_DELETE_CANDIDATE_MB: {sum(safe_float(r.get('size_mb')) for r in archived_rows if normalize(r.get('proposed_later_action')) == 'DELETE_AFTER_ARCHIVE_VERIFICATION_CANDIDATE'):.3f}",
            f"PROTECTED_EXCLUSION_COUNT: {len(protected_rows)}",
            f"PROTECTED_EXCLUSION_MB: {sum(safe_float(r.get('size_mb')) for r in protected_rows):.3f}",
            "DELETED_FILE_COUNT: 0",
            "DELETED_DIR_COUNT: 0",
            "MOVED_COUNT: 0",
            "ARCHIVED_COUNT: 0",
            "ZIP_CREATED_COUNT: 0",
            "VALIDATION_FAIL_COUNT: 0",
            "AUTO_TRADE: DISABLED",
            "AUTO_SELL: DISABLED",
            "OFFICIAL_DECISION_IMPACT: NONE",
            "CURRENT_DAILY_MODIFIED: FALSE",
            "STABLE_SNAPSHOT_MODIFIED: FALSE",
            "MANUAL_STATE_MODIFIED: FALSE",
            "PRICE_CACHE_MODIFIED: FALSE",
            f"READ_FIRST: {READ_FIRST_PATH.as_posix()}",
            f"REPORT: {REPORT_PATH.as_posix()}",
        ]
    ) + "\n"
    write_text(root / READ_FIRST_PATH, read_first)
    write_text(root / REPORT_PATH, render_report(root, root, empty_rows, orphan_rows, archived_rows, protected_rows, latest_snapshot_name))

    print("STATUS: OK_V18_20H_EMPTY_ORPHAN_CLEANUP_READY")
    print("MODE: DRYRUN")
    print(f"DELETED_FILE_COUNT: 0")
    print(f"DELETED_DIR_COUNT: 0")
    print("MOVED_COUNT: 0")
    print("ARCHIVED_COUNT: 0")
    print("ZIP_CREATED_COUNT: 0")
    print("VALIDATION_FAIL_COUNT: 0")
    print("AUTO_TRADE: DISABLED")
    print("AUTO_SELL: DISABLED")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print("CURRENT_DAILY_MODIFIED: FALSE")
    print("STABLE_SNAPSHOT_MODIFIED: FALSE")
    print("MANUAL_STATE_MODIFIED: FALSE")
    print("PRICE_CACHE_MODIFIED: FALSE")
    print(f"READ_FIRST: {READ_FIRST_PATH.as_posix()}")
    print(f"REPORT: {REPORT_PATH.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
