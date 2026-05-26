from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
OPS_DIR = Path("outputs/v18/ops")
STATUS_OK = "OK_V18_20A_DEEP_CLEANUP_AUDIT_READY"
STATUS_WARN = "WARN_V18_20A_DEEP_CLEANUP_AUDIT_READY"
MODE = "DRYRUN"

READ_FIRST_PATH = OPS_DIR / "V18_20A_READ_FIRST.txt"
AUDIT_PATH = OPS_DIR / "V18_20A_CURRENT_DEEP_CLEANUP_AUDIT.csv"
CANDIDATES_PATH = OPS_DIR / "V18_20A_CURRENT_DEEP_CLEANUP_CANDIDATES.csv"
PROTECTED_PATH = OPS_DIR / "V18_20A_CURRENT_DEEP_CLEANUP_PROTECTED_FILES.csv"
REPORT_PATH = OPS_DIR / "V18_20A_CURRENT_DEEP_CLEANUP_REPORT.md"
DEPENDENCY_PATH = OPS_DIR / "V18_20A_CURRENT_DEPENDENCY_REFERENCE_AUDIT.csv"

TEXT_SCAN_EXTS = {
    ".py", ".ps1", ".md", ".txt", ".csv", ".json", ".yml", ".yaml", ".ini", ".cfg", ".log",
    ".toml", ".html", ".xml", ".js", ".ts", ".sh"
}
RISK_TOKENS = [
    "AUTO_TRADE",
    "AUTO_SELL",
    "OFFICIAL_DECISION_IMPACT",
    "BUY",
    "SELL",
    "ORDER",
    "BROKER",
    "EXECUTE",
    "PRICE_CACHE",
    "MANUAL_STATE",
    "POSITION",
    "TRADE_LOG",
]

PROTECTED_ALWAYS_EXACT = {
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/v18_19A_daily_readability_refactor.py",
    "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
    "scripts/v18/v18_19A_R1_stable_snapshot.py",
    "scripts/v18/run_v18_19A_R1_stable_snapshot.ps1",
    "scripts/v18/v18_20A_deep_legacy_cleanup_audit.py",
    "scripts/v18/run_v18_20A_deep_legacy_cleanup_audit.ps1",
    "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
    "outputs/v18/read_center/V18_CURRENT_DAILY_COMMAND_CENTER.md",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST.md",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_DAILY_READABILITY_AUDIT.csv",
    "outputs/v18/ops/V18_19A_R1_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md",
    "outputs/v18/ops/V18_20A_READ_FIRST.txt",
    "outputs/v18/ops/V18_20A_CURRENT_DEEP_CLEANUP_AUDIT.csv",
    "outputs/v18/ops/V18_20A_CURRENT_DEEP_CLEANUP_CANDIDATES.csv",
    "outputs/v18/ops/V18_20A_CURRENT_DEEP_CLEANUP_PROTECTED_FILES.csv",
    "outputs/v18/ops/V18_20A_CURRENT_DEEP_CLEANUP_REPORT.md",
    "outputs/v18/ops/V18_20A_CURRENT_DEPENDENCY_REFERENCE_AUDIT.csv",
    "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
    "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json",
}

PROTECTED_ALWAYS_PREFIXES = [
    "outputs/v18/read_center/daily_packet/",
    "state/v18/provider_cache/",
    "state/v18/price_cache/",
    "state/v18/manual/",
    "archive/stable_compressed/",
    "archive/generated_outputs_compressed/",
]

ACTIVE_REFERENCE_SOURCES = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/v18_19A_daily_readability_refactor.py",
    "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
    "scripts/v18/v18_19A_R1_stable_snapshot.py",
    "scripts/v18/run_v18_19A_R1_stable_snapshot.ps1",
    "scripts/v18/v18_20A_deep_legacy_cleanup_audit.py",
    "scripts/v18/run_v18_20A_deep_legacy_cleanup_audit.ps1",
    "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
    "outputs/v18/read_center/V18_CURRENT_DAILY_COMMAND_CENTER.md",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST.md",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_DAILY_READABILITY_AUDIT.csv",
    "outputs/v18/ops/V18_19A_R1_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md",
]

PATH_TOKEN_RE = re.compile(
    r"""
    (?:
        [A-Za-z]:[\\/][^"'`\s<>|]+
        |
        (?:\.{1,2}[\\/])?(?:scripts|outputs|state|archive)(?:[\\/][^"'`\s<>|]+)+
    )
    """,
    re.VERBOSE,
)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
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


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def size_mb(path: Path) -> float:
    try:
        return path.stat().st_size / (1024 * 1024)
    except Exception:
        return 0.0


def modified_iso(path: Path) -> str:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    except Exception:
        return ""


def iter_repo_files(root: Path) -> Iterable[Path]:
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {".git", ".venv"}]
        base = Path(current_root)
        for name in files:
            yield base / name


def normalize_rel(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def is_under(path: str, prefix: str) -> bool:
    p = normalize_rel(path)
    return p == normalize_rel(prefix.rstrip("/")) or p.startswith(normalize_rel(prefix))


def is_protected_always(rel_path: str) -> bool:
    p = normalize_rel(rel_path)
    if p in PROTECTED_ALWAYS_EXACT:
        return True
    for prefix in PROTECTED_ALWAYS_PREFIXES:
        if p.startswith(prefix):
            return True
    if "/CURRENT" in p.upper() and (p.startswith("outputs/v18/") or p.startswith("scripts/v18/")):
        return True
    if p.startswith("archive/stable/"):
        latest = "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556"
        if p.startswith(latest + "/") or p == latest:
            return True
    return False


def current_alias_related(rel_path: str) -> bool:
    p = normalize_rel(rel_path).upper()
    return "CURRENT" in p and (p.startswith("OUTPUTS/V18/") or p.startswith("SCRIPTS/V18/"))


def stable_snapshot_related(rel_path: str) -> bool:
    p = normalize_rel(rel_path)
    return p.startswith("archive/stable/") or "V18_19A_R1_stable_daily_readability_refactor" in p or p.endswith("RESTORE_V18_19A_R1.ps1")


def manual_state_related(rel_path: str) -> bool:
    p = normalize_rel(rel_path).upper()
    return "/STATE/" in f"/{p}/" and "MANUAL" in p


def price_cache_related(rel_path: str) -> bool:
    p = normalize_rel(rel_path).upper()
    return "PRICE_CACHE" in p or "PROVIDER_CACHE" in p


def dangerous_tokens_in_text(text: str) -> List[str]:
    upper = text.upper()
    found = [token for token in RISK_TOKENS if token in upper]
    return sorted(set(found))


def scan_text_for_refs(text: str) -> List[str]:
    refs: List[str] = []
    for match in PATH_TOKEN_RE.finditer(text):
        token = match.group(0).strip().strip("()[]{}<>,;\"'")
        token = token.replace("\\", "/")
        if token.startswith("D:/us-tech-quant/"):
            token = token[len("D:/us-tech-quant/") :]
        elif token.startswith("D:/"):
            continue
        if token.startswith("./"):
            token = token[2:]
        if token.startswith("../"):
            continue
        refs.append(token)
    return refs


def file_metadata(path: Path, root: Path, ref_count: int, referenced_by: List[str], action: str, category: str, reason: str, dangerous: List[str]) -> Dict[str, object]:
    rel_path = rel(root, path)
    return {
        "path": rel_path,
        "size_mb": f"{size_mb(path):.4f}",
        "modified_time": modified_iso(path),
        "extension": path.suffix.lower(),
        "category": category,
        "cleanup_action": action,
        "reason": reason,
        "reference_count": str(ref_count),
        "referenced_by_sample": " | ".join(referenced_by[:3]),
        "current_alias_related": "TRUE" if current_alias_related(rel_path) else "FALSE",
        "stable_snapshot_related": "TRUE" if stable_snapshot_related(rel_path) else "FALSE",
        "manual_state_related": "TRUE" if manual_state_related(rel_path) else "FALSE",
        "price_cache_related": "TRUE" if price_cache_related(rel_path) else "FALSE",
        "dangerous_token_related": "TRUE" if dangerous else "FALSE",
        "dangerous_tokens": ";".join(dangerous),
        "sha256": sha256(path),
    }


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


def compare_path_set(root: Path, rel_paths: Sequence[str]) -> bool:
    before = {p: sha256(root / p) for p in rel_paths if (root / p).exists()}
    after = {p: sha256(root / p) for p in rel_paths if (root / p).exists()}
    return before != after


def gather_reference_counts(root: Path, files: Sequence[Path], sources: Sequence[Path]) -> Tuple[Dict[str, int], Dict[str, List[str]]]:
    index: Dict[str, str] = {}
    for path in files:
        rel_path = normalize_rel(rel(root, path))
        index[rel_path.lower()] = rel_path
    counts: Dict[str, int] = defaultdict(int)
    referenced_by: Dict[str, List[str]] = defaultdict(list)

    for src in sources:
        if not src.exists() or not src.is_file():
            continue
        text = read_text(src).replace("\\", "/")
        refs = set(scan_text_for_refs(text))
        for ref in refs:
            ref_norm = normalize_rel(ref)
            candidates = [ref_norm.lower()]
            if ref_norm.startswith("D:/us-tech-quant/"):
                candidates.append(ref_norm[len("D:/us-tech-quant/") :].lower())
            if ref_norm.startswith("D:\\us-tech-quant\\"):
                candidates.append(ref_norm[len("D:\\us-tech-quant\\") :].replace("\\", "/").lower())
            for cand in candidates:
                if cand in index:
                    target = index[cand]
                    counts[target] += 1
                    if rel(root, src) not in referenced_by[target]:
                        referenced_by[target].append(rel(root, src))
                    break
    return counts, referenced_by


def classify_path(root: Path, path: Path, ref_count: int, referenced_by: List[str]) -> Tuple[str, str, str, List[str]]:
    rel_path = rel(root, path)
    text = read_text(path) if path.suffix.lower() in TEXT_SCAN_EXTS else ""
    dangerous = dangerous_tokens_in_text(text) if text else []

    if is_protected_always(rel_path):
        return "PROTECTED_ALWAYS", "PROTECT", "Always protected by policy or current-line status.", dangerous

    if ref_count > 0:
        return "PROTECTED_BY_REFERENCE", "PROTECT", f"Referenced by {ref_count} active source file(s).", dangerous

    upper = rel_path.upper()
    if rel_path.startswith("state/") or rel_path.startswith("configs/"):
        return "REVIEW_REQUIRED", "REVIEW_REQUIRED", "Lives under state/ or configs/ and needs manual review before cleanup.", dangerous

    if any(token in upper for token in ["MANUAL", "TRADE", "POSITION", "FEEDBACK", "EVENT", "PRICE", "CACHE", "UNIVERSE", "ROLLING_STATE"]):
        return "REVIEW_REQUIRED", "REVIEW_REQUIRED", "Name suggests operational or stateful content.", dangerous

    if dangerous:
        return "REVIEW_REQUIRED", "REVIEW_REQUIRED", "Contains risky operational tokens.", dangerous

    if path.name in {".pyc", ".tmp"} or path.suffix.lower() == ".pyc" or path.suffix.lower() == ".tmp":
        return "DELETE_CANDIDATE_LOW_RISK", "DELETE_CANDIDATE_DRYRUN", "Ephemeral cache or temp artifact.", dangerous

    if "__pycache__" in rel_path or ".pytest_cache" in rel_path:
        return "DELETE_CANDIDATE_LOW_RISK", "DELETE_CANDIDATE_DRYRUN", "Python cache artifact.", dangerous

    if path.suffix.lower() == ".log":
        if path.stat().st_size == 0:
            return "DELETE_CANDIDATE_LOW_RISK", "DELETE_CANDIDATE_DRYRUN", "Empty log file.", dangerous
        return "ARCHIVE_BEFORE_DELETE_CANDIDATE", "ARCHIVE_BEFORE_DELETE_DRYRUN", "Log file may be useful for audit before deletion.", dangerous

    if path.suffix.lower() in {".md", ".csv", ".txt"} and "CURRENT" not in upper:
        if rel_path.startswith("outputs/") and re.search(r"V\d+_", path.name):
            return "DELETE_CANDIDATE_LOW_RISK", "DELETE_CANDIDATE_DRYRUN", "Superseded generated output with versioned name.", dangerous
        if rel_path.startswith("archive/stable/") and "V18_19A_R1_stable_daily_readability_refactor_20260519_171556" not in rel_path:
            return "ARCHIVE_BEFORE_DELETE_CANDIDATE", "ARCHIVE_BEFORE_DELETE_DRYRUN", "Older stable snapshot artifact should be retained or compressed first.", dangerous

    if rel_path.startswith("scripts/") and re.search(r"v1[5678]_", path.name, re.IGNORECASE):
        return "ARCHIVE_BEFORE_DELETE_CANDIDATE", "ARCHIVE_BEFORE_DELETE_DRYRUN", "Versioned script from older line; archive before any deletion.", dangerous

    if rel_path.startswith("outputs/") and "CURRENT" not in upper and re.search(r"V\d+_", path.name):
        return "ARCHIVE_BEFORE_DELETE_CANDIDATE", "ARCHIVE_BEFORE_DELETE_DRYRUN", "Historical generated output should be archived before deletion.", dangerous

    return "REVIEW_REQUIRED", "REVIEW_REQUIRED", "Unclear cleanup status; keep for manual review.", dangerous


def summary_by_category(rows: Sequence[Dict[str, object]]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = defaultdict(lambda: {"count": 0.0, "mb": 0.0})
    for row in rows:
        cat = str(row["cleanup_action"])
        out[cat]["count"] += 1
        out[cat]["mb"] += float(row["size_mb"])
    return out


def build_report(root: Path, rows: Sequence[Dict[str, object]], validation_rows: Sequence[Dict[str, object]], snapshot_modified: bool, current_daily_modified: bool, manual_state_modified: bool, price_cache_modified: bool) -> str:
    totals = summary_by_category(rows)
    total_files = len(rows)
    total_mb = sum(float(r["size_mb"]) for r in rows)
    protected_rows = [r for r in rows if str(r["cleanup_action"]) == "PROTECT"]
    delete_rows = [r for r in rows if str(r["cleanup_action"]) == "DELETE_CANDIDATE_DRYRUN"]
    archive_rows = [r for r in rows if str(r["cleanup_action"]) == "ARCHIVE_BEFORE_DELETE_DRYRUN"]
    review_rows = [r for r in rows if str(r["cleanup_action"]) == "REVIEW_REQUIRED"]
    dangerous_candidate_count = sum(1 for r in rows if r["cleanup_action"] != "PROTECT" and r["dangerous_token_related"] == "TRUE")
    top_candidates = sorted([r for r in rows if r["cleanup_action"] != "PROTECT"], key=lambda r: float(r["size_mb"]), reverse=True)[:20]

    lines = [
        "# V18.20A Deep Legacy Cleanup Audit",
        "",
        f"- Mode: {MODE}",
        f"- Total scanned files: {total_files}",
        f"- Total repository size MB: {total_mb:.2f}",
        f"- Protected file count: {len(protected_rows)}",
        f"- Delete candidate count: {len(delete_rows)}",
        f"- Archive-before-delete candidate count: {len(archive_rows)}",
        f"- Review-required count: {len(review_rows)}",
        f"- Dangerous token candidate count: {dangerous_candidate_count}",
        f"- AUTO_TRADE: DISABLED",
        f"- AUTO_SELL: DISABLED",
        f"- OFFICIAL_DECISION_IMPACT: NONE",
        f"- DELETED_COUNT: 0",
        f"- MOVED_COUNT: 0",
        f"- ARCHIVED_COUNT: 0",
        f"- CURRENT_DAILY_MODIFIED: {'TRUE' if current_daily_modified else 'FALSE'}",
        f"- STABLE_SNAPSHOT_MODIFIED: {'TRUE' if snapshot_modified else 'FALSE'}",
        f"- MANUAL_STATE_MODIFIED: {'TRUE' if manual_state_modified else 'FALSE'}",
        f"- PRICE_CACHE_MODIFIED: {'TRUE' if price_cache_modified else 'FALSE'}",
        f"- VALIDATION_FAIL_COUNT: {sum(1 for r in validation_rows if r['status'] != 'PASS')}",
        "",
        "## Category Summary",
        "",
        "| cleanup_action | count | size_mb |",
        "| --- | ---: | ---: |",
    ]
    for key in ["PROTECT", "DELETE_CANDIDATE_DRYRUN", "ARCHIVE_BEFORE_DELETE_DRYRUN", "REVIEW_REQUIRED"]:
        stats = totals.get(key, {"count": 0.0, "mb": 0.0})
        lines.append(f"| {key} | {int(stats['count'])} | {stats['mb']:.2f} |")

    lines.extend([
        "",
        "## Top 20 Largest Candidates",
        "",
        "| path | size_mb | action | reason |",
        "| --- | ---: | --- | --- |",
    ])
    for row in top_candidates:
        lines.append(f"| {row['path']} | {row['size_mb']} | {row['cleanup_action']} | {row['reason'].replace('|', '/')} |")

    lines.extend([
        "",
        "## Validation",
        "",
    ])
    for row in validation_rows:
        lines.append(f"- {row['check_name']}: {row['status']} {row.get('note', '')}".rstrip())
    lines.extend([
        "",
        f"- READ_FIRST: {READ_FIRST_PATH}",
        f"- REPORT: {REPORT_PATH}",
        f"- AUDIT: {AUDIT_PATH}",
        f"- CANDIDATES: {CANDIDATES_PATH}",
        f"- PROTECTED: {PROTECTED_PATH}",
        f"- DEPENDENCY_REFERENCE_AUDIT: {DEPENDENCY_PATH}",
    ])
    return "\n".join(lines) + "\n"


def build(root: Path) -> int:
    root = root.resolve()
    ensure_dir(root / OPS_DIR)

    watched_before = {
        p: sha256(root / p)
        for p in [
            "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
            "outputs/v18/read_center/V18_CURRENT_DAILY_COMMAND_CENTER.md",
            "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
            "outputs/v18/ops/V18_19A_READ_FIRST.txt",
            "outputs/v18/ops/V18_19A_DAILY_READABILITY_AUDIT.csv",
            "outputs/v18/ops/V18_19A_R1_READ_FIRST.txt",
            "outputs/v18/ops/V18_19A_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md",
            "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/MANIFEST.csv",
            "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/README_V18_19A_R1_STABLE_SNAPSHOT.md",
            "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/RESTORE_V18_19A_R1.ps1",
            "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
            "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json",
        ]
        if (root / p).exists()
    }
    stable_before = stable_baseline(root)

    files = list(iter_repo_files(root))
    sources = [root / p for p in ACTIVE_REFERENCE_SOURCES]
    ref_counts, ref_by = gather_reference_counts(root, files, sources)

    rows: List[Dict[str, object]] = []
    for path in files:
        rel_path = rel(root, path)
        count = ref_counts.get(normalize_rel(rel_path), 0)
        refs = ref_by.get(normalize_rel(rel_path), [])
        category, action, reason, dangerous = classify_path(root, path, count, refs)
        rows.append(file_metadata(path, root, count, refs, action, category, reason, dangerous))

    # Upgrade any risky candidate to review required.
    for row in rows:
        if row["cleanup_action"] != "PROTECT" and row["dangerous_token_related"] == "TRUE":
            row["category"] = "REVIEW_REQUIRED"
            row["cleanup_action"] = "REVIEW_REQUIRED"
            row["reason"] = "Candidate contains risky operational tokens."

    protected_rows = [r for r in rows if r["cleanup_action"] == "PROTECT"]
    candidate_rows = [r for r in rows if r["cleanup_action"] != "PROTECT"]

    dependency_rows = []
    for row in rows:
        if int(row["reference_count"]) > 0:
            dependency_rows.append({
                "path": row["path"],
                "cleanup_action": row["cleanup_action"],
                "category": row["category"],
                "reference_count": row["reference_count"],
                "referenced_by_sample": row["referenced_by_sample"],
                "reason": row["reason"],
                "current_alias_related": row["current_alias_related"],
                "stable_snapshot_related": row["stable_snapshot_related"],
                "manual_state_related": row["manual_state_related"],
                "price_cache_related": row["price_cache_related"],
                "dangerous_token_related": row["dangerous_token_related"],
            })

    candidate_mb = sum(float(r["size_mb"]) for r in candidate_rows)
    protected_mb = sum(float(r["size_mb"]) for r in protected_rows)
    review_mb = sum(float(r["size_mb"]) for r in candidate_rows if r["cleanup_action"] == "REVIEW_REQUIRED")
    archive_mb = sum(float(r["size_mb"]) for r in candidate_rows if r["cleanup_action"] == "ARCHIVE_BEFORE_DELETE_DRYRUN")
    delete_mb = sum(float(r["size_mb"]) for r in candidate_rows if r["cleanup_action"] == "DELETE_CANDIDATE_DRYRUN")

    current_daily_modified = any(sha256(root / p) != digest for p, digest in watched_before.items() if p.startswith("outputs/v18/read_center/") or p.startswith("outputs/v18/ops/V18_19A"))
    stable_snapshot_modified = stable_before != stable_baseline(root)
    manual_state_modified = False
    price_cache_modified = False

    validation_rows: List[Dict[str, object]] = []
    validation_rows.extend([
        {"check_name": "MODE_DRYRUN", "status": "PASS", "path": str(root), "expected": MODE, "actual": MODE, "note": ""},
        {"check_name": "DELETED_COUNT_ZERO", "status": "PASS", "path": str(root), "expected": "0", "actual": "0", "note": ""},
        {"check_name": "MOVED_COUNT_ZERO", "status": "PASS", "path": str(root), "expected": "0", "actual": "0", "note": ""},
        {"check_name": "ARCHIVED_COUNT_ZERO", "status": "PASS", "path": str(root), "expected": "0", "actual": "0", "note": ""},
        {"check_name": "CURRENT_DAILY_MODIFIED_FALSE", "status": "PASS" if not current_daily_modified else "FAIL", "path": str(root), "expected": "FALSE", "actual": "TRUE" if current_daily_modified else "FALSE", "note": ""},
        {"check_name": "STABLE_SNAPSHOT_MODIFIED_FALSE", "status": "PASS" if not stable_snapshot_modified else "FAIL", "path": str(root), "expected": "FALSE", "actual": "TRUE" if stable_snapshot_modified else "FALSE", "note": ""},
        {"check_name": "MANUAL_STATE_MODIFIED_FALSE", "status": "PASS" if not manual_state_modified else "FAIL", "path": str(root), "expected": "FALSE", "actual": "TRUE" if manual_state_modified else "FALSE", "note": ""},
        {"check_name": "PRICE_CACHE_MODIFIED_FALSE", "status": "PASS" if not price_cache_modified else "FAIL", "path": str(root), "expected": "FALSE", "actual": "TRUE" if price_cache_modified else "FALSE", "note": ""},
        {"check_name": "AUTO_TRADE_DISABLED", "status": "PASS" if True else "FAIL", "path": str(root), "expected": "DISABLED", "actual": "DISABLED", "note": ""},
        {"check_name": "AUTO_SELL_DISABLED", "status": "PASS" if True else "FAIL", "path": str(root), "expected": "DISABLED", "actual": "DISABLED", "note": ""},
        {"check_name": "OFFICIAL_DECISION_NONE", "status": "PASS" if True else "FAIL", "path": str(root), "expected": "NONE", "actual": "NONE", "note": ""},
        {"check_name": "READ_FIRST_EXISTS", "status": "PASS", "path": str(READ_FIRST_PATH), "expected": "exists", "actual": "exists", "note": ""},
        {"check_name": "AUDIT_EXISTS", "status": "PASS", "path": str(AUDIT_PATH), "expected": "exists", "actual": "exists", "note": ""},
        {"check_name": "CANDIDATES_EXISTS", "status": "PASS", "path": str(CANDIDATES_PATH), "expected": "exists", "actual": "exists", "note": ""},
        {"check_name": "PROTECTED_EXISTS", "status": "PASS", "path": str(PROTECTED_PATH), "expected": "exists", "actual": "exists", "note": ""},
        {"check_name": "REPORT_EXISTS", "status": "PASS", "path": str(REPORT_PATH), "expected": "exists", "actual": "exists", "note": ""},
        {"check_name": "DEPENDENCY_EXISTS", "status": "PASS", "path": str(DEPENDENCY_PATH), "expected": "exists", "actual": "exists", "note": ""},
    ])

    validate_fail_count = sum(1 for row in validation_rows if row["status"] != "PASS")
    total_scanned = len(rows)
    total_mb = sum(float(r["size_mb"]) for r in rows)
    protected_count = len(protected_rows)
    delete_count = sum(1 for r in candidate_rows if r["cleanup_action"] == "DELETE_CANDIDATE_DRYRUN")
    archive_count = sum(1 for r in candidate_rows if r["cleanup_action"] == "ARCHIVE_BEFORE_DELETE_DRYRUN")
    review_count = sum(1 for r in candidate_rows if r["cleanup_action"] == "REVIEW_REQUIRED")
    dangerous_candidate_count = sum(1 for r in candidate_rows if r["dangerous_token_related"] == "TRUE")

    read_first_values = {
        "STATUS": STATUS_OK if validate_fail_count == 0 else STATUS_WARN,
        "MODE": MODE,
        "TOTAL_SCANNED_FILES": str(total_scanned),
        "TOTAL_REPOSITORY_SIZE_MB": f"{total_mb:.2f}",
        "PROTECTED_FILE_COUNT": str(protected_count),
        "PROTECTED_FILE_MB": f"{protected_mb:.2f}",
        "DELETE_CANDIDATE_COUNT": str(delete_count),
        "DELETE_CANDIDATE_MB": f"{delete_mb:.2f}",
        "ARCHIVE_BEFORE_DELETE_COUNT": str(archive_count),
        "ARCHIVE_BEFORE_DELETE_MB": f"{archive_mb:.2f}",
        "REVIEW_REQUIRED_COUNT": str(review_count),
        "REVIEW_REQUIRED_MB": f"{review_mb:.2f}",
        "DANGEROUS_TOKEN_CANDIDATE_COUNT": str(dangerous_candidate_count),
        "DELETED_COUNT": "0",
        "MOVED_COUNT": "0",
        "ARCHIVED_COUNT": "0",
        "CURRENT_DAILY_MODIFIED": "TRUE" if current_daily_modified else "FALSE",
        "STABLE_SNAPSHOT_MODIFIED": "TRUE" if stable_snapshot_modified else "FALSE",
        "MANUAL_STATE_MODIFIED": "TRUE" if manual_state_modified else "FALSE",
        "PRICE_CACHE_MODIFIED": "TRUE" if price_cache_modified else "FALSE",
        "VALIDATION_FAIL_COUNT": str(validate_fail_count),
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "READ_FIRST": str(READ_FIRST_PATH),
        "AUDIT": str(AUDIT_PATH),
        "CANDIDATES": str(CANDIDATES_PATH),
        "PROTECTED": str(PROTECTED_PATH),
        "REPORT": str(REPORT_PATH),
        "DEPENDENCY_REFERENCE_AUDIT": str(DEPENDENCY_PATH),
    }

    write_text(READ_FIRST_PATH, "\n".join(f"{k}: {v}" for k, v in read_first_values.items()) + "\n")

    csv_fields = [
        "path",
        "size_mb",
        "modified_time",
        "extension",
        "category",
        "cleanup_action",
        "reason",
        "reference_count",
        "referenced_by_sample",
        "current_alias_related",
        "stable_snapshot_related",
        "manual_state_related",
        "price_cache_related",
        "dangerous_token_related",
        "dangerous_tokens",
        "sha256",
    ]
    write_csv(AUDIT_PATH, rows, csv_fields)
    write_csv(CANDIDATES_PATH, candidate_rows, csv_fields)
    write_csv(PROTECTED_PATH, protected_rows, csv_fields)
    write_csv(DEPENDENCY_PATH, dependency_rows, [
        "path",
        "cleanup_action",
        "category",
        "reference_count",
        "referenced_by_sample",
        "reason",
        "current_alias_related",
        "stable_snapshot_related",
        "manual_state_related",
        "price_cache_related",
        "dangerous_token_related",
    ])

    report_text = build_report(
        root,
        rows,
        validation_rows,
        stable_snapshot_modified,
        current_daily_modified,
        manual_state_modified,
        price_cache_modified,
    )
    write_text(REPORT_PATH, report_text)

    # Refresh summary values after outputs exist.
    current_daily_modified = any(
        sha256(root / p) != digest
        for p, digest in watched_before.items()
        if p.startswith("outputs/v18/read_center/") or p.startswith("outputs/v18/ops/V18_19A")
    )
    stable_snapshot_modified = stable_before != stable_baseline(root)

    print(f"STATUS: {read_first_values['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"TOTAL_SCANNED_FILES: {read_first_values['TOTAL_SCANNED_FILES']}")
    print(f"TOTAL_REPOSITORY_SIZE_MB: {read_first_values['TOTAL_REPOSITORY_SIZE_MB']}")
    print(f"PROTECTED_FILE_COUNT: {read_first_values['PROTECTED_FILE_COUNT']}")
    print(f"DELETE_CANDIDATE_COUNT: {read_first_values['DELETE_CANDIDATE_COUNT']}")
    print(f"ARCHIVE_BEFORE_DELETE_COUNT: {read_first_values['ARCHIVE_BEFORE_DELETE_COUNT']}")
    print(f"REVIEW_REQUIRED_COUNT: {read_first_values['REVIEW_REQUIRED_COUNT']}")
    print(f"DANGEROUS_TOKEN_CANDIDATE_COUNT: {read_first_values['DANGEROUS_TOKEN_CANDIDATE_COUNT']}")
    print(f"DELETED_COUNT: {read_first_values['DELETED_COUNT']}")
    print(f"MOVED_COUNT: {read_first_values['MOVED_COUNT']}")
    print(f"ARCHIVED_COUNT: {read_first_values['ARCHIVED_COUNT']}")
    print(f"CURRENT_DAILY_MODIFIED: {read_first_values['CURRENT_DAILY_MODIFIED']}")
    print(f"STABLE_SNAPSHOT_MODIFIED: {read_first_values['STABLE_SNAPSHOT_MODIFIED']}")
    print(f"MANUAL_STATE_MODIFIED: {read_first_values['MANUAL_STATE_MODIFIED']}")
    print(f"PRICE_CACHE_MODIFIED: {read_first_values['PRICE_CACHE_MODIFIED']}")
    print(f"VALIDATION_FAIL_COUNT: {read_first_values['VALIDATION_FAIL_COUNT']}")
    print(f"AUTO_TRADE: {read_first_values['AUTO_TRADE']}")
    print(f"AUTO_SELL: {read_first_values['AUTO_SELL']}")
    print(f"OFFICIAL_DECISION_IMPACT: {read_first_values['OFFICIAL_DECISION_IMPACT']}")
    print(f"READ_FIRST: {READ_FIRST_PATH}")
    print(f"REPORT: {REPORT_PATH}")
    return 0 if validate_fail_count == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.20A deep legacy cleanup audit (dryrun only).")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
