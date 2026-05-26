from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
OPS_DIR = Path("outputs/v18/ops")

SAFE_SOURCE = OPS_DIR / "V18_20C_CURRENT_SAFE_DELETE_SKIPPED.csv"
SAFE_LIST = OPS_DIR / "V18_20B_CURRENT_SAFE_DELETE_LATER.csv"
REVIEW_TRIAGE = OPS_DIR / "V18_20B_CURRENT_REVIEW_REQUIRED_TRIAGE.csv"
DEPENDENCY_AUDIT = OPS_DIR / "V18_20A_CURRENT_DEPENDENCY_REFERENCE_AUDIT.csv"
PROTECTED_FILES = OPS_DIR / "V18_20A_CURRENT_DEEP_CLEANUP_PROTECTED_FILES.csv"

READ_FIRST_PATH = OPS_DIR / "V18_20D_READ_FIRST.txt"
AUDIT_PATH = OPS_DIR / "V18_20D_CURRENT_CONFIDENCE_UPGRADE_AUDIT.csv"
HIGH_PATH = OPS_DIR / "V18_20D_CURRENT_HIGH_CONFIDENCE_SAFE_DELETE.csv"
MEDIUM_PATH = OPS_DIR / "V18_20D_CURRENT_STILL_MEDIUM_OR_REVIEW.csv"
REPORT_PATH = OPS_DIR / "V18_20D_CURRENT_CONFIDENCE_UPGRADE_REPORT.md"

PROTECTED_PREFIXES = (
    "state/",
    "configs/",
    "archive/stable/",
    "archive/stable_compressed/",
    "archive/generated_outputs_compressed/",
    ".git/",
    ".venv/",
)

OUTPUT_FIELDS = [
    "path",
    "size_mb",
    "original_confidence",
    "upgraded_confidence",
    "upgrade_status",
    "reason",
    "failed_checks",
    "reference_count",
    "referenced_by_sample",
    "current_alias_related",
    "stable_snapshot_related",
    "manual_state_related",
    "price_cache_related",
    "dangerous_token_related",
    "source_code_related",
    "generated_output_related",
    "would_be_eligible_for_v18_20E_apply",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                return rows, list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "CSV_PARSE_FAILED"


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
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def normalize(value: object) -> str:
    return str(value or "").strip()


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


def safe_bool(value: object, default: bool = False) -> bool:
    text = normalize(value).upper()
    if text in {"TRUE", "T", "YES", "Y", "1"}:
        return True
    if text in {"FALSE", "F", "NO", "N", "0"}:
        return False
    return default


def mb(value: float) -> str:
    return f"{value:.3f}"


def latest_stable_snapshot_name(root: Path) -> str:
    base = root / "archive/stable"
    if not base.exists():
        return ""
    dirs = [p for p in base.iterdir() if p.is_dir()]
    if not dirs:
        return ""
    return max(dirs, key=lambda p: p.stat().st_mtime).name


def parse_map(path: Path, key_field: str = "path") -> Dict[str, Dict[str, str]]:
    rows, _, _ = read_csv_rows(path)
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        key = normalize(row.get(key_field)).replace("\\", "/")
        if key:
            out[key] = row
    return out


def in_protected_prefix(rel_path: str) -> bool:
    lower = rel_path.lower()
    return any(lower.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def is_generated_output_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("generated_output_related")):
        return True
    lower = rel_path.lower()
    return lower.startswith("outputs/") or lower.startswith("archive/") or Path(lower).suffix in {".csv", ".log", ".md", ".txt", ".json"}


def is_source_code_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("source_code_related")):
        return True
    return Path(rel_path.lower()).suffix in {".py", ".ps1", ".bat", ".sh"}


def is_current_alias_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("current_alias_related")):
        return True
    return "CURRENT" in rel_path.upper()


def is_stable_snapshot_related(rel_path: str, row: Dict[str, str], latest_snapshot_name: str) -> bool:
    if safe_bool(row.get("stable_snapshot_related")):
        return True
    lower = rel_path.lower()
    return lower.startswith("archive/stable/") or (latest_snapshot_name and latest_snapshot_name.lower() in lower)


def is_manual_state_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("manual_state_related")):
        return True
    lower = rel_path.lower()
    return "/state/" in f"/{lower}/" and any(tok in lower for tok in ("manual", "trade", "position", "feedback"))


def is_price_cache_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("price_cache_related")):
        return True
    lower = rel_path.lower()
    return "price_cache" in lower or "provider_cache" in lower or "price" in lower


def sort_rows(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    return sorted(rows, key=lambda row: (-safe_float(row.get("size_mb")), normalize(row.get("path"))))


def format_failed_checks(checks: Sequence[str]) -> str:
    return "; ".join(checks)


def classify_row(
    root: Path,
    skipped_row: Dict[str, str],
    safe_row: Dict[str, str],
    dep_row: Dict[str, str],
    protected_paths: set[str],
    safe_paths: set[str],
    latest_snapshot_name: str,
) -> Dict[str, object]:
    rel_path = normalize(skipped_row.get("path")).replace("\\", "/")
    size = safe_float(skipped_row.get("size_mb"))
    original_confidence = normalize(safe_row.get("confidence") or skipped_row.get("confidence") or "MEDIUM").upper()
    ref_count_text = normalize(dep_row.get("reference_count") or safe_row.get("reference_count") or skipped_row.get("reference_count"))
    ref_count = safe_int(ref_count_text, default=-1) if ref_count_text else -1
    referenced_by_sample = normalize(dep_row.get("referenced_by_sample") or safe_row.get("referenced_by_sample") or skipped_row.get("referenced_by_sample"))

    current_alias_related = is_current_alias_related(rel_path, safe_row or skipped_row)
    stable_snapshot_related = is_stable_snapshot_related(rel_path, safe_row or skipped_row, latest_snapshot_name)
    manual_state_related = is_manual_state_related(rel_path, safe_row or skipped_row)
    price_cache_related = is_price_cache_related(rel_path, safe_row or skipped_row)
    dangerous_token_related = safe_bool(dep_row.get("dangerous_token_related") or safe_row.get("dangerous_token_related") or skipped_row.get("dangerous_token_related"))
    source_code_related = is_source_code_related(rel_path, safe_row or skipped_row)
    generated_output_related = is_generated_output_related(rel_path, safe_row or skipped_row)

    failed_checks: List[str] = []

    abs_path = (root / rel_path).resolve()
    if not abs_path.exists() or not abs_path.is_file():
        failed_checks.append("missing_before_audit")
    try:
        abs_path.relative_to(root.resolve())
    except Exception:
        failed_checks.append("outside_repo_root")
    if rel_path not in safe_paths:
        failed_checks.append("not_in_v18_20B_safe_delete_list")
    if normalize(skipped_row.get("skip_reason")).lower() != "confidence_not_high:medium":
        failed_checks.append("not_skipped_only_for_medium_confidence")
    if ref_count_text == "":
        failed_checks.append("reference_count_missing")
    elif ref_count != 0:
        failed_checks.append("reference_count_nonzero")
    if in_protected_prefix(rel_path) or rel_path in protected_paths:
        failed_checks.append("protected_directory_or_file")
    if current_alias_related:
        failed_checks.append("current_alias_related")
    if stable_snapshot_related:
        failed_checks.append("stable_snapshot_related")
    if manual_state_related:
        failed_checks.append("manual_state_related")
    if price_cache_related:
        failed_checks.append("price_cache_related")
    if source_code_related:
        failed_checks.append("source_code_related")
    if "CURRENT" in rel_path.upper():
        failed_checks.append("path_contains_current")
    if rel_path.lower().startswith(("state/", "configs/")):
        failed_checks.append("protected_path_pattern")
    if rel_path.lower().endswith(".json"):
        failed_checks.append("config_like_json")
    if source_code_related and not rel_path.lower().endswith((".pyc", ".csv", ".log")):
        failed_checks.append("source_code_unclear")
    if dangerous_token_related:
        safe_generated_log = generated_output_related and rel_path.lower().endswith(".log") and not current_alias_related and not stable_snapshot_related and not manual_state_related and not price_cache_related and not source_code_related
        if not safe_generated_log:
            failed_checks.append("dangerous_token_not_safe_generated_log")

    eligible = len(failed_checks) == 0

    if eligible:
        upgrade_status = "UPGRADE_TO_HIGH"
        upgraded_confidence = "HIGH"
        reason = "Unreferenced generated log with no protected-role signals."
        would_be_eligible = "TRUE"
    elif rel_path.lower().endswith(".json"):
        upgrade_status = "REVIEW_REQUIRED"
        upgraded_confidence = "MEDIUM"
        reason = "Config-shaped JSON requires manual confirmation before any upgrade."
        would_be_eligible = "FALSE"
    elif price_cache_related or "price" in rel_path.lower():
        upgrade_status = "KEEP_MEDIUM"
        upgraded_confidence = "MEDIUM"
        reason = "Price-data path remains conservative medium."
        would_be_eligible = "FALSE"
    else:
        upgrade_status = "REVIEW_REQUIRED"
        upgraded_confidence = "MEDIUM"
        reason = "Ambiguous cleanup candidate needs manual confirmation."
        would_be_eligible = "FALSE"

    return {
        "path": rel_path,
        "size_mb": mb(size),
        "original_confidence": original_confidence,
        "upgraded_confidence": upgraded_confidence,
        "upgrade_status": upgrade_status,
        "reason": reason,
        "failed_checks": format_failed_checks(failed_checks),
        "reference_count": ref_count_text or "0",
        "referenced_by_sample": referenced_by_sample,
        "current_alias_related": str(current_alias_related).upper(),
        "stable_snapshot_related": str(stable_snapshot_related).upper(),
        "manual_state_related": str(manual_state_related).upper(),
        "price_cache_related": str(price_cache_related).upper(),
        "dangerous_token_related": str(dangerous_token_related).upper(),
        "source_code_related": str(source_code_related).upper(),
        "generated_output_related": str(generated_output_related).upper(),
        "would_be_eligible_for_v18_20E_apply": would_be_eligible,
    }


def render_report(
    root: Path,
    source_count: int,
    source_mb: float,
    high_rows: Sequence[Dict[str, object]],
    medium_rows: Sequence[Dict[str, object]],
    review_rows: Sequence[Dict[str, object]],
    latest_snapshot_name: str,
) -> str:
    high_mb = sum(safe_float(r.get("size_mb")) for r in high_rows)
    medium_mb = sum(safe_float(r.get("size_mb")) for r in medium_rows)
    review_mb = sum(safe_float(r.get("size_mb")) for r in review_rows)
    combined_review = sort_rows(list(medium_rows) + list(review_rows))
    lines = [
        "# V18.20D Safe Delete Confidence Upgrade Audit",
        "",
        "- STATUS: OK_V18_20D_SAFE_DELETE_CONFIDENCE_UPGRADE_AUDIT_READY",
        "- MODE: DRYRUN",
        f"- ROOT: {root}",
        f"- INPUT_SKIPPED_COUNT: {source_count}",
        f"- INPUT_SKIPPED_MB: {mb(source_mb)}",
        f"- UPGRADED_TO_HIGH_COUNT: {len(high_rows)}",
        f"- UPGRADED_TO_HIGH_MB: {mb(high_mb)}",
        f"- STILL_MEDIUM_COUNT: {len(medium_rows)}",
        f"- STILL_MEDIUM_MB: {mb(medium_mb)}",
        f"- REVIEW_REQUIRED_COUNT: {len(review_rows)}",
        f"- REVIEW_REQUIRED_MB: {mb(review_mb)}",
        "- DELETED_COUNT: 0",
        "- MOVED_COUNT: 0",
        "- ARCHIVED_COUNT: 0",
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
        "## Top 50 Upgraded Candidates By Size",
        "",
    ]
    if high_rows:
        for row in sort_rows(high_rows)[:50]:
            lines.append(f"- {row['path']} | {row['size_mb']} MB | {row['reason']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Top 50 Still-Medium-Or-Review Candidates By Size", ""])
    if combined_review:
        for row in combined_review[:50]:
            lines.append(f"- {row['path']} | {row['size_mb']} MB | {row['reason']}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Recommended Next Step",
            "",
            "- Use the HIGH-confidence log subset only for the next apply gate. Keep price-data CSVs and the config-shaped JSON below the threshold until a separate review confirms they are disposable.",
            "",
            f"- READ_FIRST: {rel(root, READ_FIRST_PATH)}",
            f"- AUDIT_CSV: {rel(root, AUDIT_PATH)}",
            f"- HIGH_CONFIDENCE_CSV: {rel(root, HIGH_PATH)}",
            f"- STILL_MEDIUM_OR_REVIEW_CSV: {rel(root, MEDIUM_PATH)}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.20D safe delete confidence upgrade audit")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    skipped_rows, _, _ = read_csv_rows(root / SAFE_SOURCE)
    safe_rows, _, _ = read_csv_rows(root / SAFE_LIST)
    protected_rows, _, _ = read_csv_rows(root / PROTECTED_FILES)
    dep_map = parse_map(root / DEPENDENCY_AUDIT)
    _review_map = parse_map(root / REVIEW_TRIAGE)
    latest_snapshot_name = latest_stable_snapshot_name(root)

    safe_map = {normalize(r.get("path")).replace("\\", "/"): r for r in safe_rows if normalize(r.get("path"))}
    protected_paths = {normalize(r.get("path")).replace("\\", "/") for r in protected_rows if normalize(r.get("path"))}
    safe_paths = set(safe_map.keys())

    audit_rows: List[Dict[str, object]] = []
    high_rows: List[Dict[str, object]] = []
    medium_rows: List[Dict[str, object]] = []
    review_rows: List[Dict[str, object]] = []

    for skipped_row in skipped_rows:
        rel_path = normalize(skipped_row.get("path")).replace("\\", "/")
        safe_row = safe_map.get(rel_path, {})
        dep_row = dep_map.get(rel_path, {})
        classified = classify_row(
            root=root,
            skipped_row=skipped_row,
            safe_row=safe_row,
            dep_row=dep_row,
            protected_paths=protected_paths,
            safe_paths=safe_paths,
            latest_snapshot_name=latest_snapshot_name,
        )
        audit_rows.append(classified)
        if classified["upgrade_status"] == "UPGRADE_TO_HIGH":
            high_rows.append(classified)
        elif classified["upgrade_status"] == "KEEP_MEDIUM":
            medium_rows.append(classified)
        else:
            review_rows.append(classified)

    audit_rows = sort_rows(audit_rows)
    high_rows = sort_rows(high_rows)
    medium_rows = sort_rows(medium_rows)
    review_rows = sort_rows(review_rows)

    write_csv(root / AUDIT_PATH, audit_rows, OUTPUT_FIELDS)
    write_csv(root / HIGH_PATH, high_rows, OUTPUT_FIELDS)
    write_csv(root / MEDIUM_PATH, medium_rows + review_rows, OUTPUT_FIELDS)

    source_count = len(skipped_rows)
    source_mb = sum(safe_float(r.get("size_mb")) for r in skipped_rows)
    high_mb = sum(safe_float(r.get("size_mb")) for r in high_rows)
    medium_mb = sum(safe_float(r.get("size_mb")) for r in medium_rows)
    review_mb = sum(safe_float(r.get("size_mb")) for r in review_rows)

    read_first = "\n".join(
        [
            "STATUS: OK_V18_20D_SAFE_DELETE_CONFIDENCE_UPGRADE_AUDIT_READY",
            "MODE: DRYRUN",
            f"ROOT: {root}",
            f"INPUT_SKIPPED_COUNT: {source_count}",
            f"INPUT_SKIPPED_MB: {mb(source_mb)}",
            f"UPGRADED_TO_HIGH_COUNT: {len(high_rows)}",
            f"UPGRADED_TO_HIGH_MB: {mb(high_mb)}",
            f"STILL_MEDIUM_COUNT: {len(medium_rows)}",
            f"STILL_MEDIUM_MB: {mb(medium_mb)}",
            f"REVIEW_REQUIRED_COUNT: {len(review_rows)}",
            f"REVIEW_REQUIRED_MB: {mb(review_mb)}",
            "DELETED_COUNT: 0",
            "MOVED_COUNT: 0",
            "ARCHIVED_COUNT: 0",
            "VALIDATION_FAIL_COUNT: 0",
            "AUTO_TRADE: DISABLED",
            "AUTO_SELL: DISABLED",
            "OFFICIAL_DECISION_IMPACT: NONE",
            "CURRENT_DAILY_MODIFIED: FALSE",
            "STABLE_SNAPSHOT_MODIFIED: FALSE",
            "MANUAL_STATE_MODIFIED: FALSE",
            "PRICE_CACHE_MODIFIED: FALSE",
            f"READ_FIRST: {rel(root, READ_FIRST_PATH)}",
            f"AUDIT_CSV: {rel(root, AUDIT_PATH)}",
            f"HIGH_CONFIDENCE_CSV: {rel(root, HIGH_PATH)}",
            f"STILL_MEDIUM_OR_REVIEW_CSV: {rel(root, MEDIUM_PATH)}",
            f"REPORT: {rel(root, REPORT_PATH)}",
        ]
    ) + "\n"
    write_text(root / READ_FIRST_PATH, read_first)
    write_text(root / REPORT_PATH, render_report(root, source_count, source_mb, high_rows, medium_rows, review_rows, latest_snapshot_name))

    print("STATUS: OK_V18_20D_SAFE_DELETE_CONFIDENCE_UPGRADE_AUDIT_READY")
    print("MODE: DRYRUN")
    print(f"INPUT_SKIPPED_COUNT: {source_count}")
    print(f"INPUT_SKIPPED_MB: {mb(source_mb)}")
    print(f"UPGRADED_TO_HIGH_COUNT: {len(high_rows)}")
    print(f"UPGRADED_TO_HIGH_MB: {mb(high_mb)}")
    print(f"STILL_MEDIUM_COUNT: {len(medium_rows)}")
    print(f"STILL_MEDIUM_MB: {mb(medium_mb)}")
    print(f"REVIEW_REQUIRED_COUNT: {len(review_rows)}")
    print(f"REVIEW_REQUIRED_MB: {mb(review_mb)}")
    print("DELETED_COUNT: 0")
    print("MOVED_COUNT: 0")
    print("ARCHIVED_COUNT: 0")
    print("VALIDATION_FAIL_COUNT: 0")
    print("AUTO_TRADE: DISABLED")
    print("AUTO_SELL: DISABLED")
    print("OFFICIAL_DECISION_IMPACT: NONE")
    print("CURRENT_DAILY_MODIFIED: FALSE")
    print("STABLE_SNAPSHOT_MODIFIED: FALSE")
    print("MANUAL_STATE_MODIFIED: FALSE")
    print("PRICE_CACHE_MODIFIED: FALSE")
    print(f"READ_FIRST: {rel(root, READ_FIRST_PATH)}")
    print(f"REPORT: {rel(root, REPORT_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
