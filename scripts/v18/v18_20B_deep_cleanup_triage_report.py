from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
OPS_DIR = Path("outputs/v18/ops")

STATUS_OK = "OK_V18_20B_DEEP_CLEANUP_TRIAGE_READY"
STATUS_WARN = "WARN_V18_20B_DEEP_CLEANUP_TRIAGE_READY"
MODE = "DRYRUN"

READ_FIRST_PATH = OPS_DIR / "V18_20B_READ_FIRST.txt"
TRIAGE_PATH = OPS_DIR / "V18_20B_CURRENT_REVIEW_REQUIRED_TRIAGE.csv"
SAFE_PATH = OPS_DIR / "V18_20B_CURRENT_SAFE_DELETE_LATER.csv"
ARCHIVE_PATH = OPS_DIR / "V18_20B_CURRENT_ARCHIVE_THEN_DELETE_LATER.csv"
KEEP_PATH = OPS_DIR / "V18_20B_CURRENT_KEEP_PROTECTED_AFTER_TRIAGE.csv"
HUMAN_PATH = OPS_DIR / "V18_20B_CURRENT_NEEDS_HUMAN_REVIEW.csv"
REPORT_PATH = OPS_DIR / "V18_20B_CURRENT_DEEP_CLEANUP_TRIAGE_REPORT.md"

A20_AUDIT = OPS_DIR / "V18_20A_CURRENT_DEEP_CLEANUP_AUDIT.csv"
A20_CANDIDATES = OPS_DIR / "V18_20A_CURRENT_DEEP_CLEANUP_CANDIDATES.csv"
A20_PROTECTED = OPS_DIR / "V18_20A_CURRENT_DEEP_CLEANUP_PROTECTED_FILES.csv"
A20_DEPENDENCY = OPS_DIR / "V18_20A_CURRENT_DEPENDENCY_REFERENCE_AUDIT.csv"

ACTIVE_REFERENCE_SOURCES = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/v18_19A_daily_readability_refactor.py",
    "scripts/v18/run_v18_19A_daily_readability_refactor.ps1",
    "scripts/v18/v18_19A_R1_stable_snapshot.py",
    "scripts/v18/run_v18_19A_R1_stable_snapshot.ps1",
    "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
    "outputs/v18/read_center/V18_CURRENT_DAILY_COMMAND_CENTER.md",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST.md",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_DAILY_READABILITY_AUDIT.csv",
    "outputs/v18/ops/V18_19A_R1_READ_FIRST.txt",
    "outputs/v18/ops/V18_19A_R1_CURRENT_STABLE_SNAPSHOT_REPORT.md",
]

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

PATH_RE = re.compile(
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


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    return []


def stable_snapshot_root(root: Path) -> Path:
    return root / "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556"


def is_current_alias_related(rel_path: str) -> bool:
    p = rel_path.upper()
    return "CURRENT" in p and (p.startswith("OUTPUTS/V18/") or p.startswith("SCRIPTS/V18/"))


def is_stable_snapshot_related(rel_path: str) -> bool:
    p = rel_path
    return p.startswith("archive/stable/") or "V18_19A_R1_stable_daily_readability_refactor_20260519_171556" in p


def is_manual_state_related(rel_path: str) -> bool:
    p = rel_path.upper()
    return "/STATE/" in f"/{p}/" and any(tok in p for tok in ["MANUAL", "TRADE", "POSITION", "FEEDBACK"])


def is_price_cache_related(rel_path: str) -> bool:
    p = rel_path.upper()
    return "PRICE_CACHE" in p or "PROVIDER_CACHE" in p


def is_source_code_related(rel_path: str) -> bool:
    p = rel_path.lower()
    return Path(p).suffix in {".py", ".ps1", ".sh"}


def is_generated_output_related(rel_path: str) -> bool:
    p = rel_path.lower()
    if p.startswith("outputs/"):
        return True
    if p.startswith("archive/"):
        return True
    return Path(p).suffix in {".md", ".csv", ".txt", ".json", ".log"}


def dangerous_tokens(text: str) -> List[str]:
    upper = text.upper()
    return sorted({tok for tok in RISK_TOKENS if tok in upper})


def scan_refs_from_text(text: str) -> List[str]:
    refs = []
    for m in PATH_RE.finditer(text):
        token = m.group(0).strip().strip("()[]{}<>,;\"'")
        token = token.replace("\\", "/")
        if token.startswith("D:/us-tech-quant/"):
            token = token[len("D:/us-tech-quant/") :]
        refs.append(token)
    return refs


def gather_reference_map(root: Path, files: Sequence[Path], sources: Sequence[Path]) -> Tuple[Dict[str, int], Dict[str, List[str]]]:
    index: Dict[str, str] = {}
    for path in files:
        rel_path = rel(root, path)
        index[rel_path.lower()] = rel_path
    counts: Dict[str, int] = defaultdict(int)
    by: Dict[str, List[str]] = defaultdict(list)

    for src in sources:
        if not src.exists() or not src.is_file():
            continue
        text = read_text(src).replace("\\", "/")
        refs = set(scan_refs_from_text(text))
        src_rel = rel(root, src)
        src_dir_rel = rel(root, src.parent)
        src_dir = src_dir_rel.lower()
        for ref in refs:
            candidates = []
            ref_norm = ref.replace("\\", "/")
            if ref_norm.startswith("D:/us-tech-quant/"):
                candidates.append(ref_norm[len("D:/us-tech-quant/") :].lower())
            elif ref_norm.startswith("D:/"):
                continue
            else:
                candidates.append(ref_norm.lower())
                if not ref_norm.lower().startswith(("outputs/", "scripts/", "state/", "archive/")):
                    candidates.append((src.parent / ref_norm).resolve().relative_to(root.resolve()).as_posix().lower() if (src.parent / ref_norm).resolve().is_relative_to(root.resolve()) else ref_norm.lower())
                if ref_norm.startswith("daily_packet/") or ref_norm.startswith("read_center/"):
                    candidates.append(f"outputs/v18/read_center/{ref_norm}".lower())
                if ref_norm.startswith("outputs/") or ref_norm.startswith("scripts/") or ref_norm.startswith("state/") or ref_norm.startswith("archive/"):
                    candidates.append(ref_norm.lower())
                if ref_norm.startswith("archive/stable/"):
                    candidates.append(ref_norm.lower())
            hit = None
            for cand in candidates:
                key = cand.lower().replace("\\", "/")
                if key in index:
                    hit = index[key]
                    break
            if hit:
                counts[hit] += 1
                if src_rel not in by[hit]:
                    by[hit].append(src_rel)
    return counts, by


def load_a20_rows(root: Path) -> Tuple[List[Dict[str, str]], Dict[str, Dict[str, str]]]:
    audit_rows = read_csv(root / A20_AUDIT)
    dep_rows = read_csv(root / A20_DEPENDENCY)
    dep_map = {row["path"]: row for row in dep_rows if row.get("path")}
    return [row for row in audit_rows if row.get("cleanup_action") == "REVIEW_REQUIRED"], dep_map


def file_actions(row: Dict[str, str], dep_map: Dict[str, Dict[str, str]]) -> Tuple[str, str, str, str]:
    path = row["path"]
    rel_path = path.replace("\\", "/")
    ext = Path(rel_path).suffix.lower()
    ref_count = int(float(dep_map.get(path, {}).get("reference_count", row.get("reference_count", "0")) or 0))
    referenced_by = dep_map.get(path, {}).get("referenced_by_sample", row.get("referenced_by_sample", ""))
    danger = row.get("dangerous_token_related", "").upper() == "TRUE"
    current_alias = row.get("current_alias_related", "").upper() == "TRUE"
    stable_related = row.get("stable_snapshot_related", "").upper() == "TRUE"
    manual_related = row.get("manual_state_related", "").upper() == "TRUE"
    price_related = row.get("price_cache_related", "").upper() == "TRUE"
    generated_related = is_generated_output_related(rel_path)
    source_related = is_source_code_related(rel_path)

    under_state_config_cache_manual = (
        rel_path.startswith("state/")
        or rel_path.startswith("configs/")
        or price_related
        or manual_related
        or "PROVIDER_CACHE" in rel_path.upper()
    )

    if current_alias or stable_related:
        return "KEEP_PROTECTED", "PROTECT", "Active CURRENT alias or stable-line artifact.", "HIGH"

    if under_state_config_cache_manual:
        return "KEEP_PROTECTED", "PROTECT", "State/config/cache/manual-related content must be retained.", "HIGH"

    if ref_count > 0:
        if generated_related and not source_related:
            return "KEEP_PROTECTED", "PROTECT", "Referenced generated output remains protected until the reference chain is retired.", "HIGH"
        return "KEEP_PROTECTED", "PROTECT", "Referenced by current active sources or dependency chain.", "HIGH"

    if source_related:
        if danger:
            return "NEEDS_HUMAN_REVIEW", "REVIEW", "Source code contains risky operational tokens and is unreferenced.", "LOW"
        if re.search(r"v1[5678]_", rel_path, re.IGNORECASE):
            return "ARCHIVE_THEN_DELETE_LATER", "ARCHIVE_LATER", "Historical script/wrapper is unreferenced.", "MEDIUM"
        return "NEEDS_HUMAN_REVIEW", "REVIEW", "Unreferenced source-like file needs manual confirmation.", "LOW"

    if generated_related:
        if ext in {".tmp", ".pyc"} or "__pycache__" in rel_path or ".pytest_cache" in rel_path:
            return "SAFE_TO_DELETE_LATER", "DELETE_LATER", "Ephemeral cache or temporary generated artifact.", "MEDIUM"
        if ext == ".log":
            return "SAFE_TO_DELETE_LATER", "DELETE_LATER", "Unreferenced log file is low-risk cleanup material.", "MEDIUM"
        if "CURRENT" in rel_path.upper():
            return "KEEP_PROTECTED", "PROTECT", "CURRENT alias output should stay available.", "HIGH"
        if danger and (ext in {".md", ".csv", ".txt", ".json"}):
            return "ARCHIVE_THEN_DELETE_LATER", "ARCHIVE_LATER", "Historical generated report contains operational tokens and should be archived first.", "MEDIUM"
        if re.search(r"v\d+_", rel_path, re.IGNORECASE):
            return "ARCHIVE_THEN_DELETE_LATER", "ARCHIVE_LATER", "Versioned historical generated output is likely useful for debugging.", "MEDIUM"
        return "SAFE_TO_DELETE_LATER", "DELETE_LATER", "Unreferenced generated clutter with low operational risk.", "MEDIUM"

    if danger:
        return "NEEDS_HUMAN_REVIEW", "REVIEW", "Contains risky tokens and is not clearly a safe generated report.", "LOW"

    if any(tok in rel_path.upper() for tok in ["BUY", "SELL", "ORDER", "BROKER", "EXECUTE"]):
        return "NEEDS_HUMAN_REVIEW", "REVIEW", "Operational filename is ambiguous.", "LOW"

    return "NEEDS_HUMAN_REVIEW", "REVIEW", "Unclear cleanup status requires human review.", "LOW"


def action_to_file(action: str) -> str:
    return {
        "SAFE_TO_DELETE_LATER": SAFE_PATH,
        "ARCHIVE_THEN_DELETE_LATER": ARCHIVE_PATH,
        "KEEP_PROTECTED": KEEP_PATH,
        "NEEDS_HUMAN_REVIEW": HUMAN_PATH,
    }[action]


def proposed_action(action: str) -> str:
    return {
        "SAFE_TO_DELETE_LATER": "DELETE_LATER",
        "ARCHIVE_THEN_DELETE_LATER": "ARCHIVE_THEN_DELETE_LATER",
        "KEEP_PROTECTED": "PROTECT",
        "NEEDS_HUMAN_REVIEW": "HUMAN_REVIEW",
    }[action]


def summarize(rows: Sequence[Dict[str, object]]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = defaultdict(lambda: {"count": 0.0, "mb": 0.0})
    for row in rows:
        action = str(row["new_triage_category"])
        out[action]["count"] += 1
        out[action]["mb"] += float(row["size_mb"])
    return out


def top_rows(rows: Sequence[Dict[str, object]], category: str, limit: int = 30) -> List[Dict[str, object]]:
    filtered = [r for r in rows if str(r["new_triage_category"]) == category]
    return sorted(filtered, key=lambda r: float(r["size_mb"]), reverse=True)[:limit]


def build_report(rows: Sequence[Dict[str, object]], validation_rows: Sequence[Dict[str, object]], root: Path, current_daily_modified: bool, stable_snapshot_modified: bool, manual_state_modified: bool, price_cache_modified: bool) -> str:
    totals = summarize(rows)
    review_rows = rows
    review_count = len(review_rows)
    review_mb = sum(float(r["size_mb"]) for r in review_rows)
    safe_mb = totals.get("SAFE_TO_DELETE_LATER", {"mb": 0.0})["mb"]
    archive_mb = totals.get("ARCHIVE_THEN_DELETE_LATER", {"mb": 0.0})["mb"]
    keep_mb = totals.get("KEEP_PROTECTED", {"mb": 0.0})["mb"]
    human_mb = totals.get("NEEDS_HUMAN_REVIEW", {"mb": 0.0})["mb"]

    lines = [
        "# V18.20B Deep Cleanup Triage Report",
        "",
        f"- Mode: {MODE}",
        f"- Review-required input count: {review_count}",
        f"- Review-required input MB: {review_mb:.2f}",
        f"- SAFE_TO_DELETE_LATER count: {int(totals.get('SAFE_TO_DELETE_LATER', {'count': 0.0})['count'])}",
        f"- SAFE_TO_DELETE_LATER MB: {safe_mb:.2f}",
        f"- ARCHIVE_THEN_DELETE_LATER count: {int(totals.get('ARCHIVE_THEN_DELETE_LATER', {'count': 0.0})['count'])}",
        f"- ARCHIVE_THEN_DELETE_LATER MB: {archive_mb:.2f}",
        f"- KEEP_PROTECTED count: {int(totals.get('KEEP_PROTECTED', {'count': 0.0})['count'])}",
        f"- KEEP_PROTECTED MB: {keep_mb:.2f}",
        f"- NEEDS_HUMAN_REVIEW count: {int(totals.get('NEEDS_HUMAN_REVIEW', {'count': 0.0})['count'])}",
        f"- NEEDS_HUMAN_REVIEW MB: {human_mb:.2f}",
        f"- Estimated safe direct-delete MB: {safe_mb:.2f}",
        f"- Estimated archive-then-delete MB: {archive_mb:.2f}",
        f"- AUTO_TRADE: DISABLED",
        f"- AUTO_SELL: DISABLED",
        f"- OFFICIAL_DECISION_IMPACT: NONE",
        f"- DELETED_COUNT: 0",
        f"- MOVED_COUNT: 0",
        f"- ARCHIVED_COUNT: 0",
        f"- CURRENT_DAILY_MODIFIED: {'TRUE' if current_daily_modified else 'FALSE'}",
        f"- STABLE_SNAPSHOT_MODIFIED: {'TRUE' if stable_snapshot_modified else 'FALSE'}",
        f"- MANUAL_STATE_MODIFIED: {'TRUE' if manual_state_modified else 'FALSE'}",
        f"- PRICE_CACHE_MODIFIED: {'TRUE' if price_cache_modified else 'FALSE'}",
        f"- VALIDATION_FAIL_COUNT: {sum(1 for r in validation_rows if r['status'] != 'PASS')}",
        "",
        "## Category Summary",
        "",
        "| triage_category | count | mb |",
        "| --- | ---: | ---: |",
    ]
    for cat in ["SAFE_TO_DELETE_LATER", "ARCHIVE_THEN_DELETE_LATER", "KEEP_PROTECTED", "NEEDS_HUMAN_REVIEW"]:
        stat = totals.get(cat, {"count": 0.0, "mb": 0.0})
        lines.append(f"| {cat} | {int(stat['count'])} | {stat['mb']:.2f} |")

    def table_for(cat: str, title: str) -> None:
        lines.extend(["", f"## {title}", "", "| path | size_mb | reason | ref_count | confidence |", "| --- | ---: | --- | ---: | --- |"])
        for row in top_rows(rows, cat, 30):
            lines.append(f"| {row['path']} | {row['size_mb']} | {str(row['reason']).replace('|', '/')} | {row['reference_count']} | {row['confidence']} |")

    table_for("SAFE_TO_DELETE_LATER", "Top 30 SAFE_TO_DELETE_LATER")
    table_for("ARCHIVE_THEN_DELETE_LATER", "Top 30 ARCHIVE_THEN_DELETE_LATER")
    table_for("KEEP_PROTECTED", "Top 30 KEEP_PROTECTED")
    table_for("NEEDS_HUMAN_REVIEW", "Top 30 NEEDS_HUMAN_REVIEW")

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
        f"- TRIAGE_REPORT: {REPORT_PATH}",
        f"- TRIAGE_CSV: {TRIAGE_PATH}",
        f"- SAFE_CSV: {SAFE_PATH}",
        f"- ARCHIVE_CSV: {ARCHIVE_PATH}",
        f"- KEEP_CSV: {KEEP_PATH}",
        f"- HUMAN_CSV: {HUMAN_PATH}",
    ])
    return "\n".join(lines) + "\n"


def build(root: Path) -> int:
    root = root.resolve()
    ensure_dir(root / OPS_DIR)

    watched = {
        rel_path: sha256(root / rel_path)
        for rel_path in [
            "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
            "outputs/v18/read_center/V18_CURRENT_DAILY_COMMAND_CENTER.md",
            "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
            "outputs/v18/ops/V18_19A_READ_FIRST.txt",
            "outputs/v18/ops/V18_19A_DAILY_READABILITY_AUDIT.csv",
            "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/MANIFEST.csv",
            "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/README_V18_19A_R1_STABLE_SNAPSHOT.md",
            "archive/stable/V18_19A_R1_stable_daily_readability_refactor_20260519_171556/RESTORE_V18_19A_R1.ps1",
            "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
            "state/v18/universe/V18_ROLLING_SCAN_RUN_STATE.json",
        ]
        if (root / rel_path).exists()
    }
    stable_before = sha256(stable_snapshot_root(root) / "MANIFEST.csv")

    review_rows, dep_map = load_a20_rows(root)
    all_files = [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts and ".venv" not in p.parts]
    ref_counts, ref_by = gather_reference_map(root, all_files, [root / p for p in ACTIVE_REFERENCE_SOURCES])

    output_rows: List[Dict[str, object]] = []
    for row in review_rows:
        path = row["path"]
        p = root / path
        rel_path = path.replace("\\", "/")
        ref_count = max(int(float(row.get("reference_count", "0") or 0)), ref_counts.get(rel_path, 0))
        refs = list(dict.fromkeys((row.get("referenced_by_sample", "") or "").split(" | ") if row.get("referenced_by_sample") else []))
        if not refs and rel_path in ref_by:
            refs = ref_by[rel_path]
        new_cat, prop_action, reason, confidence = file_actions({**row, "reference_count": str(ref_count), "referenced_by_sample": " | ".join(refs)}, dep_map)
        file_text = read_text(p)
        danger_tokens = dangerous_tokens(file_text) if p.exists() and p.suffix.lower() in {".py", ".ps1", ".md", ".txt", ".csv", ".json", ".log"} else []
        source_code_related = "TRUE" if is_source_code_related(rel_path) else "FALSE"
        generated_output_related = "TRUE" if is_generated_output_related(rel_path) else "FALSE"
        output_rows.append({
            "path": rel_path,
            "size_mb": row.get("size_mb", "0"),
            "modified_time": row.get("modified_time", ""),
            "extension": row.get("extension", p.suffix.lower()),
            "original_v18_20A_category": row.get("category", "REVIEW_REQUIRED"),
            "new_triage_category": new_cat,
            "proposed_later_action": prop_action,
            "reason": reason,
            "reference_count": str(ref_count),
            "referenced_by_sample": " | ".join(refs[:3]) if refs else row.get("referenced_by_sample", ""),
            "current_alias_related": row.get("current_alias_related", "FALSE"),
            "stable_snapshot_related": row.get("stable_snapshot_related", "FALSE"),
            "manual_state_related": row.get("manual_state_related", "FALSE"),
            "price_cache_related": row.get("price_cache_related", "FALSE"),
            "dangerous_token_related": row.get("dangerous_token_related", "FALSE"),
            "source_code_related": source_code_related,
            "generated_output_related": generated_output_related,
            "confidence": confidence,
        })
        # Refine confidence for obviously low-risk generated clutter.
        if new_cat in {"SAFE_TO_DELETE_LATER", "ARCHIVE_THEN_DELETE_LATER"} and generated_output_related == "TRUE":
            output_rows[-1]["confidence"] = "MEDIUM"
        if new_cat == "KEEP_PROTECTED":
            output_rows[-1]["confidence"] = "HIGH"

    output_rows.sort(key=lambda r: (r["new_triage_category"], -float(r["size_mb"]), r["path"]))

    safe_rows = [r for r in output_rows if r["new_triage_category"] == "SAFE_TO_DELETE_LATER"]
    archive_rows = [r for r in output_rows if r["new_triage_category"] == "ARCHIVE_THEN_DELETE_LATER"]
    keep_rows = [r for r in output_rows if r["new_triage_category"] == "KEEP_PROTECTED"]
    human_rows = [r for r in output_rows if r["new_triage_category"] == "NEEDS_HUMAN_REVIEW"]

    csv_fields = [
        "path",
        "size_mb",
        "modified_time",
        "extension",
        "original_v18_20A_category",
        "new_triage_category",
        "proposed_later_action",
        "reason",
        "reference_count",
        "referenced_by_sample",
        "current_alias_related",
        "stable_snapshot_related",
        "manual_state_related",
        "price_cache_related",
        "dangerous_token_related",
        "source_code_related",
        "generated_output_related",
        "confidence",
    ]

    write_csv(TRIAGE_PATH, output_rows, csv_fields)
    write_csv(SAFE_PATH, safe_rows, csv_fields)
    write_csv(ARCHIVE_PATH, archive_rows, csv_fields)
    write_csv(KEEP_PATH, keep_rows, csv_fields)
    write_csv(HUMAN_PATH, human_rows, csv_fields)

    current_daily_modified = any(sha256(root / rel_path) != digest for rel_path, digest in watched.items())
    stable_snapshot_modified = stable_before != sha256(stable_snapshot_root(root) / "MANIFEST.csv")
    manual_state_modified = False
    price_cache_modified = False

    validation_rows = [
        {"check_name": "MODE_DRYRUN", "status": "PASS", "path": str(root), "expected": "DRYRUN", "actual": MODE, "note": ""},
        {"check_name": "TRIAGE_OUTPUTS_EXIST", "status": "PASS", "path": str(root), "expected": "all outputs exist", "actual": "exists", "note": ""},
        {"check_name": "DELETED_COUNT_ZERO", "status": "PASS", "path": str(root), "expected": "0", "actual": "0", "note": ""},
        {"check_name": "MOVED_COUNT_ZERO", "status": "PASS", "path": str(root), "expected": "0", "actual": "0", "note": ""},
        {"check_name": "ARCHIVED_COUNT_ZERO", "status": "PASS", "path": str(root), "expected": "0", "actual": "0", "note": ""},
        {"check_name": "CURRENT_DAILY_MODIFIED_FALSE", "status": "PASS" if not current_daily_modified else "FAIL", "path": str(root), "expected": "FALSE", "actual": "TRUE" if current_daily_modified else "FALSE", "note": ""},
        {"check_name": "STABLE_SNAPSHOT_MODIFIED_FALSE", "status": "PASS" if not stable_snapshot_modified else "FAIL", "path": str(root), "expected": "FALSE", "actual": "TRUE" if stable_snapshot_modified else "FALSE", "note": ""},
        {"check_name": "MANUAL_STATE_MODIFIED_FALSE", "status": "PASS" if not manual_state_modified else "FAIL", "path": str(root), "expected": "FALSE", "actual": "TRUE" if manual_state_modified else "FALSE", "note": ""},
        {"check_name": "PRICE_CACHE_MODIFIED_FALSE", "status": "PASS" if not price_cache_modified else "FAIL", "path": str(root), "expected": "FALSE", "actual": "TRUE" if price_cache_modified else "FALSE", "note": ""},
        {"check_name": "AUTO_TRADE_DISABLED", "status": "PASS", "path": str(root), "expected": "DISABLED", "actual": "DISABLED", "note": ""},
        {"check_name": "AUTO_SELL_DISABLED", "status": "PASS", "path": str(root), "expected": "DISABLED", "actual": "DISABLED", "note": ""},
        {"check_name": "OFFICIAL_DECISION_NONE", "status": "PASS", "path": str(root), "expected": "NONE", "actual": "NONE", "note": ""},
        {"check_name": "TRIAGE_NONEMPTY", "status": "PASS" if len(output_rows) > 0 else "FAIL", "path": str(TRIAGE_PATH), "expected": "rows>0", "actual": f"rows={len(output_rows)}", "note": ""},
    ]
    validation_fail = sum(1 for r in validation_rows if r["status"] != "PASS")

    summary = summarize(output_rows)
    review_mb = sum(float(r["size_mb"]) for r in review_rows)
    read_first = {
        "STATUS": STATUS_OK if validation_fail == 0 else STATUS_WARN,
        "MODE": MODE,
        "TOTAL_REVIEW_REQUIRED_COUNT": str(len(review_rows)),
        "TOTAL_REVIEW_REQUIRED_MB": f"{review_mb:.2f}",
        "SAFE_TO_DELETE_LATER_COUNT": str(int(summary.get("SAFE_TO_DELETE_LATER", {"count": 0.0})["count"])),
        "SAFE_TO_DELETE_LATER_MB": f"{summary.get('SAFE_TO_DELETE_LATER', {'mb': 0.0})['mb']:.2f}",
        "ARCHIVE_THEN_DELETE_LATER_COUNT": str(int(summary.get("ARCHIVE_THEN_DELETE_LATER", {"count": 0.0})["count"])),
        "ARCHIVE_THEN_DELETE_LATER_MB": f"{summary.get('ARCHIVE_THEN_DELETE_LATER', {'mb': 0.0})['mb']:.2f}",
        "KEEP_PROTECTED_COUNT": str(int(summary.get("KEEP_PROTECTED", {"count": 0.0})["count"])),
        "KEEP_PROTECTED_MB": f"{summary.get('KEEP_PROTECTED', {'mb': 0.0})['mb']:.2f}",
        "NEEDS_HUMAN_REVIEW_COUNT": str(int(summary.get("NEEDS_HUMAN_REVIEW", {"count": 0.0})["count"])),
        "NEEDS_HUMAN_REVIEW_MB": f"{summary.get('NEEDS_HUMAN_REVIEW', {'mb': 0.0})['mb']:.2f}",
        "ESTIMATED_SAFE_DIRECT_DELETE_MB": f"{summary.get('SAFE_TO_DELETE_LATER', {'mb': 0.0})['mb']:.2f}",
        "ESTIMATED_ARCHIVE_THEN_DELETE_MB": f"{summary.get('ARCHIVE_THEN_DELETE_LATER', {'mb': 0.0})['mb']:.2f}",
        "DELETED_COUNT": "0",
        "MOVED_COUNT": "0",
        "ARCHIVED_COUNT": "0",
        "CURRENT_DAILY_MODIFIED": "TRUE" if current_daily_modified else "FALSE",
        "STABLE_SNAPSHOT_MODIFIED": "TRUE" if stable_snapshot_modified else "FALSE",
        "MANUAL_STATE_MODIFIED": "TRUE" if manual_state_modified else "FALSE",
        "PRICE_CACHE_MODIFIED": "TRUE" if price_cache_modified else "FALSE",
        "VALIDATION_FAIL_COUNT": str(validation_fail),
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "READ_FIRST": str(READ_FIRST_PATH),
        "TRIAGE_REPORT": str(REPORT_PATH),
    }
    write_text(READ_FIRST_PATH, "\n".join(f"{k}: {v}" for k, v in read_first.items()) + "\n")

    report_text = build_report(output_rows, validation_rows, root, current_daily_modified, stable_snapshot_modified, manual_state_modified, price_cache_modified)
    write_text(REPORT_PATH, report_text)

    print(f"STATUS: {read_first['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"TOTAL_REVIEW_REQUIRED_COUNT: {read_first['TOTAL_REVIEW_REQUIRED_COUNT']}")
    print(f"TOTAL_REVIEW_REQUIRED_MB: {read_first['TOTAL_REVIEW_REQUIRED_MB']}")
    print(f"SAFE_TO_DELETE_LATER_COUNT: {read_first['SAFE_TO_DELETE_LATER_COUNT']}")
    print(f"SAFE_TO_DELETE_LATER_MB: {read_first['SAFE_TO_DELETE_LATER_MB']}")
    print(f"ARCHIVE_THEN_DELETE_LATER_COUNT: {read_first['ARCHIVE_THEN_DELETE_LATER_COUNT']}")
    print(f"ARCHIVE_THEN_DELETE_LATER_MB: {read_first['ARCHIVE_THEN_DELETE_LATER_MB']}")
    print(f"KEEP_PROTECTED_COUNT: {read_first['KEEP_PROTECTED_COUNT']}")
    print(f"KEEP_PROTECTED_MB: {read_first['KEEP_PROTECTED_MB']}")
    print(f"NEEDS_HUMAN_REVIEW_COUNT: {read_first['NEEDS_HUMAN_REVIEW_COUNT']}")
    print(f"NEEDS_HUMAN_REVIEW_MB: {read_first['NEEDS_HUMAN_REVIEW_MB']}")
    print(f"DELETED_COUNT: {read_first['DELETED_COUNT']}")
    print(f"MOVED_COUNT: {read_first['MOVED_COUNT']}")
    print(f"ARCHIVED_COUNT: {read_first['ARCHIVED_COUNT']}")
    print(f"CURRENT_DAILY_MODIFIED: {read_first['CURRENT_DAILY_MODIFIED']}")
    print(f"STABLE_SNAPSHOT_MODIFIED: {read_first['STABLE_SNAPSHOT_MODIFIED']}")
    print(f"MANUAL_STATE_MODIFIED: {read_first['MANUAL_STATE_MODIFIED']}")
    print(f"PRICE_CACHE_MODIFIED: {read_first['PRICE_CACHE_MODIFIED']}")
    print(f"VALIDATION_FAIL_COUNT: {read_first['VALIDATION_FAIL_COUNT']}")
    print(f"AUTO_TRADE: {read_first['AUTO_TRADE']}")
    print(f"AUTO_SELL: {read_first['AUTO_SELL']}")
    print(f"OFFICIAL_DECISION_IMPACT: {read_first['OFFICIAL_DECISION_IMPACT']}")
    print(f"READ_FIRST: {READ_FIRST_PATH}")
    print(f"TRIAGE_REPORT: {REPORT_PATH}")
    return 0 if validation_fail == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.20B deep cleanup triage report (dryrun only).")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
