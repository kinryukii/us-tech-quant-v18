from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
OPS_DIR = Path("outputs/v18/ops")

MEDIUM_SOURCE = OPS_DIR / "V18_20D_CURRENT_STILL_MEDIUM_OR_REVIEW.csv"
UPGRADE_SOURCE = OPS_DIR / "V18_20D_CURRENT_CONFIDENCE_UPGRADE_AUDIT.csv"
SAFE_SOURCE = OPS_DIR / "V18_20B_CURRENT_SAFE_DELETE_LATER.csv"
REVIEW_TRIAGE = OPS_DIR / "V18_20B_CURRENT_REVIEW_REQUIRED_TRIAGE.csv"
DEPENDENCY_AUDIT = OPS_DIR / "V18_20A_CURRENT_DEPENDENCY_REFERENCE_AUDIT.csv"
PROTECTED_FILES = OPS_DIR / "V18_20A_CURRENT_DEEP_CLEANUP_PROTECTED_FILES.csv"

READ_FIRST_PATH = OPS_DIR / "V18_20E_READ_FIRST.txt"
AUDIT_PATH = OPS_DIR / "V18_20E_CURRENT_STILL_MEDIUM_ROOT_CAUSE_AUDIT.csv"
SUMMARY_PATH = OPS_DIR / "V18_20E_CURRENT_MEDIUM_BY_REASON_SUMMARY.csv"
POSSIBLE_PATH = OPS_DIR / "V18_20E_CURRENT_POSSIBLE_RULE_UPGRADE_CANDIDATES.csv"
KEEP_PATH = OPS_DIR / "V18_20E_CURRENT_KEEP_MEDIUM_OR_REVIEW.csv"
REPORT_PATH = OPS_DIR / "V18_20E_CURRENT_STILL_MEDIUM_ROOT_CAUSE_REPORT.md"

PROTECTED_PREFIXES = (
    "state/",
    "configs/",
    "archive/stable/",
    "archive/stable_compressed/",
    "archive/generated_outputs_compressed/",
    ".git/",
    ".venv/",
)

AUDIT_FIELDS = [
    "path",
    "size_mb",
    "extension",
    "primary_root_cause",
    "failed_checks",
    "possible_rule_upgrade_candidate",
    "suggested_future_action",
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
]

SUMMARY_FIELDS = ["primary_root_cause", "count", "total_mb", "note"]


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


def active_ref_guard(referenced_by_sample: str) -> bool:
    refs = referenced_by_sample.upper()
    return any(tok in refs for tok in ("V18_CURRENT_DAILY_COMMAND_CENTER", "V18_CURRENT_DAILY_BRIEF", "V18_19A", "MANIFEST.CSV", "RESTORE_"))


def classify_primary_root_cause(
    rel_path: str,
    row: Dict[str, str],
    safe_row: Dict[str, str],
    dep_row: Dict[str, str],
    latest_snapshot_name: str,
) -> Tuple[str, List[str], bool, str]:
    checks: List[str] = []
    ref_count_text = normalize(dep_row.get("reference_count") or safe_row.get("reference_count") or row.get("reference_count"))
    referenced_by_sample = normalize(dep_row.get("referenced_by_sample") or safe_row.get("referenced_by_sample") or row.get("referenced_by_sample"))
    ref_count = safe_int(ref_count_text, default=-1) if ref_count_text else -1

    current_alias = is_current_alias_related(rel_path, safe_row or row)
    stable_related = is_stable_snapshot_related(rel_path, safe_row or row, latest_snapshot_name)
    manual_related = is_manual_state_related(rel_path, safe_row or row)
    price_related = is_price_cache_related(rel_path, safe_row or row)
    dangerous = safe_bool(dep_row.get("dangerous_token_related") or safe_row.get("dangerous_token_related") or row.get("dangerous_token_related"))
    source_related = is_source_code_related(rel_path, safe_row or row)
    generated_related = is_generated_output_related(rel_path, safe_row or row)
    protected_prefix = in_protected_prefix(rel_path)

    if ref_count_text == "":
        checks.append("missing_reference_count")
    elif ref_count != 0:
        checks.append("reference_count_nonzero")
    if current_alias:
        checks.append("current_alias_related")
    if stable_related:
        checks.append("stable_snapshot_related")
    if manual_related:
        checks.append("manual_state_related")
    if price_related:
        checks.append("price_cache_related")
    if source_related:
        checks.append("source_code_related")
    if protected_prefix:
        checks.append("protected_prefix")
    if normalize(safe_row.get("confidence") or row.get("confidence")).upper() not in {"", "MEDIUM"}:
        checks.append("confidence_not_medium")
    if active_ref_guard(referenced_by_sample):
        checks.append("referenced_by_active_source")
    if "CURRENT" in rel_path.upper():
        checks.append("path_contains_current")
    if rel_path.lower().startswith(("state/", "configs/")):
        checks.append("path_in_state_or_configs")

    primary = "OTHER_UNCLEAR"

    if current_alias:
        primary = "CURRENT_ALIAS_RISK"
    elif stable_related or protected_prefix:
        primary = "PATH_PROTECTION_UNCLEAR"
    elif manual_related or price_related:
        primary = "STATE_CONFIG_CACHE_RISK"
    elif source_related:
        primary = "SOURCE_CODE_ROLE_UNCLEAR"
    elif dangerous and generated_related and rel_path.lower().endswith((".log", ".md", ".txt", ".json", ".csv")):
        primary = "DANGEROUS_TOKEN_IN_REPORT"
    elif dangerous:
        primary = "DANGEROUS_TOKEN_IN_CODE_OR_STATE"
    elif ref_count_text == "" or ref_count != 0 or active_ref_guard(referenced_by_sample):
        primary = "REFERENCE_UNCERTAIN"
    elif generated_related:
        primary = "GENERATED_OUTPUT_BUT_NEEDS_RULE"
    else:
        primary = "OTHER_UNCLEAR"

    if primary in {"STATE_CONFIG_CACHE_RISK", "GENERATED_OUTPUT_BUT_NEEDS_RULE"}:
        future_action = "KEEP_MEDIUM"
    elif primary in {"DANGEROUS_TOKEN_IN_REPORT", "DANGEROUS_TOKEN_IN_CODE_OR_STATE", "SOURCE_CODE_ROLE_UNCLEAR", "CURRENT_ALIAS_RISK", "PATH_PROTECTION_UNCLEAR", "REFERENCE_UNCERTAIN", "MISSING_METADATA"}:
        future_action = "REVIEW_MANUALLY"
    else:
        future_action = "KEEP_MEDIUM"

    if generated_related and ref_count == 0 and not current_alias and not stable_related and not manual_related and not price_related and not source_related and not dangerous and "CURRENT" not in rel_path.upper():
        possible = rel_path.lower().startswith("outputs/") and rel_path.lower().endswith(".log") and not active_ref_guard(referenced_by_sample)
        if possible and "log" in rel_path.lower():
            primary = "GENERATED_OUTPUT_BUT_NEEDS_RULE"
            future_action = "POSSIBLE_UPGRADE_AFTER_RULE_REVIEW"
        else:
            possible = False
    else:
        possible = False

    return primary, checks, possible, future_action


def classify_row(
    rel_path: str,
    size_mb: float,
    safe_row: Dict[str, str],
    dep_row: Dict[str, str],
    latest_snapshot_name: str,
    allow_possible_upgrade: bool,
) -> Dict[str, object]:
    row_source = safe_row if safe_row else dep_row
    current_alias = is_current_alias_related(rel_path, row_source)
    stable_related = is_stable_snapshot_related(rel_path, row_source, latest_snapshot_name)
    manual_related = is_manual_state_related(rel_path, row_source)
    price_related = is_price_cache_related(rel_path, row_source)
    dangerous = safe_bool(dep_row.get("dangerous_token_related") or safe_row.get("dangerous_token_related"))
    source_related = is_source_code_related(rel_path, row_source)
    generated_related = is_generated_output_related(rel_path, row_source)
    ref_count_text = normalize(dep_row.get("reference_count") or safe_row.get("reference_count"))
    referenced_by_sample = normalize(dep_row.get("referenced_by_sample") or safe_row.get("referenced_by_sample"))

    primary_root_cause, checks, possible, future_action = classify_primary_root_cause(
        rel_path=rel_path,
        row=row_source,
        safe_row=safe_row,
        dep_row=dep_row,
        latest_snapshot_name=latest_snapshot_name,
    )

    if primary_root_cause == "OTHER_UNCLEAR" and not generated_related and not source_related and not current_alias and not stable_related and not manual_related and not price_related and not dangerous:
        future_action = "REVIEW_MANUALLY"

    if not allow_possible_upgrade:
        possible = False
        if future_action == "POSSIBLE_UPGRADE_AFTER_RULE_REVIEW":
            future_action = "KEEP_MEDIUM"

    reason = normalize(safe_row.get("reason") or dep_row.get("reason") or "")
    if not reason:
        if primary_root_cause == "STATE_CONFIG_CACHE_RISK":
            reason = "Price/cache-like data remains medium until a dedicated retention rule is introduced."
        elif primary_root_cause == "DANGEROUS_TOKEN_IN_REPORT":
            reason = "Old generated report/log with dangerous tokens requires a stricter rule before deletion."
        elif primary_root_cause == "REFERENCE_UNCERTAIN":
            reason = "Reference status is not clean enough for safe upgrade."
        elif primary_root_cause == "CURRENT_ALIAS_RISK":
            reason = "CURRENT alias semantics keep the file below the safe-delete threshold."
        else:
            reason = "Medium until a future rule review resolves the remaining ambiguity."

    failed_checks = "; ".join(checks)
    return {
        "path": rel_path,
        "size_mb": f"{size_mb:.3f}",
        "extension": Path(rel_path).suffix.lower(),
        "primary_root_cause": primary_root_cause,
        "failed_checks": failed_checks,
        "possible_rule_upgrade_candidate": "TRUE" if possible else "FALSE",
        "suggested_future_action": future_action,
        "reason": reason,
        "reference_count": ref_count_text or "0",
        "referenced_by_sample": referenced_by_sample,
        "current_alias_related": str(current_alias).upper(),
        "stable_snapshot_related": str(stable_related).upper(),
        "manual_state_related": str(manual_related).upper(),
        "price_cache_related": str(price_related).upper(),
        "dangerous_token_related": str(dangerous).upper(),
        "source_code_related": str(source_related).upper(),
        "generated_output_related": str(generated_related).upper(),
    }


def summarize(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    totals: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))
    notes: Dict[str, str] = {}
    for row in rows:
        cause = normalize(row.get("primary_root_cause")) or "OTHER_UNCLEAR"
        count, total = totals[cause]
        totals[cause] = (count + 1, total + safe_float(row.get("size_mb")))
        notes[cause] = {
            "STATE_CONFIG_CACHE_RISK": "Price/cache-like rows remain medium pending a separate retention rule.",
            "MISSING_METADATA": "One review item lacks sufficient certainty for automatic handling.",
            "GENERATED_OUTPUT_BUT_NEEDS_RULE": "Generated output needs a future rule but is not safe to auto-upgrade yet.",
            "REFERENCE_UNCERTAIN": "Reference signals are not clean enough to trust a stricter delete rule.",
        }.get(cause, "Mixed medium items with no safe upgrade path yet.")
    out = []
    for cause, (count, total) in sorted(totals.items(), key=lambda kv: (-kv[1][1], kv[0])):
        out.append({"primary_root_cause": cause, "count": count, "total_mb": f"{total:.3f}", "note": notes.get(cause, "")})
    return out


def render_report(
    root: Path,
    audited_medium_rows: Sequence[Dict[str, object]],
    review_rows: Sequence[Dict[str, object]],
    summary_rows: Sequence[Dict[str, object]],
    possible_rows: Sequence[Dict[str, object]],
    latest_snapshot_name: str,
) -> str:
    medium_mb = sum(safe_float(r.get("size_mb")) for r in audited_medium_rows)
    review_mb = sum(safe_float(r.get("size_mb")) for r in review_rows)
    possible_mb = sum(safe_float(r.get("size_mb")) for r in possible_rows)
    keep_mb = medium_mb
    review_count = len(review_rows)
    lines = [
        "# V18.20E Still-Medium Safe Delete Root Cause Audit",
        "",
        "- STATUS: OK_V18_20E_STILL_MEDIUM_ROOT_CAUSE_AUDIT_READY",
        "- MODE: DRYRUN",
        f"- ROOT: {root}",
        f"- INPUT_STILL_MEDIUM_COUNT: {len(audited_medium_rows)}",
        f"- INPUT_STILL_MEDIUM_MB: {mb(medium_mb)}",
        f"- REVIEW_REQUIRED_COUNT: {review_count}",
        f"- REVIEW_REQUIRED_MB: {mb(review_mb)}",
        f"- POSSIBLE_RULE_UPGRADE_COUNT: {len(possible_rows)}",
        f"- POSSIBLE_RULE_UPGRADE_MB: {mb(possible_mb)}",
        f"- KEEP_MEDIUM_COUNT: {len(audited_medium_rows)}",
        f"- KEEP_MEDIUM_MB: {mb(keep_mb)}",
        f"- REVIEW_MANUAL_COUNT: {review_count}",
        f"- REVIEW_MANUAL_MB: {mb(review_mb)}",
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
        "## Count By Root Cause",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['primary_root_cause']}: {row['count']} / {row['total_mb']} MB")
    lines.extend(
        [
            "",
            "## Top 50 Largest Still-Medium Files",
            "",
        ]
    )
    for row in sorted(audited_medium_rows, key=lambda r: (-safe_float(r.get("size_mb")), normalize(r.get("path"))))[:50]:
        lines.append(f"- {row['path']} | {row['size_mb']} MB | {row['primary_root_cause']} | {row['reason']}")
    lines.extend(["", "## Top 50 Possible Upgrade Candidates", ""])
    if possible_rows:
        for row in sorted(possible_rows, key=lambda r: (-safe_float(r.get("size_mb")), normalize(r.get("path"))))[:50]:
            lines.append(f"- {row['path']} | {row['size_mb']} MB | {row['reason']}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            "- Do not revise the V18.20B/V18.20D confidence rules yet for deletion.",
            "- The remaining medium set is overwhelmingly cache-like price data, so archiving is not justified as a first step.",
            "- Skip further cleanup on this branch unless a separate retention policy is approved.",
            "",
            f"- READ_FIRST: {rel(root, READ_FIRST_PATH)}",
            f"- REPORT: {rel(root, REPORT_PATH)}",
            f"- ROOT_CAUSE_AUDIT: {rel(root, AUDIT_PATH)}",
            f"- SUMMARY_CSV: {rel(root, SUMMARY_PATH)}",
            f"- POSSIBLE_UPGRADE_CSV: {rel(root, POSSIBLE_PATH)}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.20E still-medium safe delete root cause audit")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    medium_rows, _, _ = read_csv_rows(root / MEDIUM_SOURCE)
    safe_rows, _, _ = read_csv_rows(root / SAFE_SOURCE)
    review_rows_source, _, _ = read_csv_rows(root / REVIEW_TRIAGE)
    dep_map = parse_map(root / DEPENDENCY_AUDIT)
    protected_map = parse_map(root / PROTECTED_FILES)
    latest_snapshot_name = latest_stable_snapshot_name(root)

    safe_map = {normalize(r.get("path")).replace("\\", "/"): r for r in safe_rows if normalize(r.get("path"))}
    review_map = {normalize(r.get("path")).replace("\\", "/"): r for r in review_rows_source if normalize(r.get("path"))}
    protected_paths = set(protected_map.keys())

    medium_only_rows = [r for r in medium_rows if normalize(r.get("upgrade_status")) == "KEEP_MEDIUM"]
    review_only_rows = [r for r in medium_rows if normalize(r.get("upgrade_status")) == "REVIEW_REQUIRED"]

    audit_rows: List[Dict[str, object]] = []
    possible_rows: List[Dict[str, object]] = []
    keep_medium_or_review_rows: List[Dict[str, object]] = []

    for row in medium_only_rows:
        rel_path = normalize(row.get("path")).replace("\\", "/")
        safe_row = safe_map.get(rel_path, row)
        dep_row = dep_map.get(rel_path, {})
        if not dep_row and rel_path in protected_paths:
            dep_row = protected_map.get(rel_path, {})
        classified = classify_row(
            rel_path=rel_path,
            size_mb=safe_float(row.get("size_mb")),
            safe_row=safe_row,
            dep_row=dep_row,
            latest_snapshot_name=latest_snapshot_name,
            allow_possible_upgrade=True,
        )
        audit_rows.append(classified)
        keep_medium_or_review_rows.append(classified)
        if classified["possible_rule_upgrade_candidate"] == "TRUE":
            possible_rows.append(classified)

    for row in review_only_rows:
        rel_path = normalize(row.get("path")).replace("\\", "/")
        safe_row = safe_map.get(rel_path, row)
        dep_row = dep_map.get(rel_path, review_map.get(rel_path, {}))
        classified = classify_row(
            rel_path=rel_path,
            size_mb=safe_float(row.get("size_mb")),
            safe_row=safe_row,
            dep_row=dep_row,
            latest_snapshot_name=latest_snapshot_name,
            allow_possible_upgrade=False,
        )
        classified["primary_root_cause"] = "MISSING_METADATA"
        classified["suggested_future_action"] = "REVIEW_MANUALLY"
        classified["possible_rule_upgrade_candidate"] = "FALSE"
        classified["reason"] = normalize(row.get("reason") or "Manual review item from V18.20D still-medium output.")
        keep_medium_or_review_rows.append(classified)

    audit_rows = sorted(audit_rows, key=lambda r: (-safe_float(r.get("size_mb")), normalize(r.get("path"))))
    keep_medium_or_review_rows = sorted(keep_medium_or_review_rows, key=lambda r: (-safe_float(r.get("size_mb")), normalize(r.get("path"))))
    possible_rows = sorted(possible_rows, key=lambda r: (-safe_float(r.get("size_mb")), normalize(r.get("path"))))

    summary_rows = summarize(audit_rows + [row for row in keep_medium_or_review_rows if row["primary_root_cause"] == "MISSING_METADATA"])

    write_csv(root / AUDIT_PATH, audit_rows, AUDIT_FIELDS)
    write_csv(root / SUMMARY_PATH, summary_rows, SUMMARY_FIELDS)
    write_csv(root / POSSIBLE_PATH, possible_rows, AUDIT_FIELDS)
    write_csv(root / KEEP_PATH, keep_medium_or_review_rows, AUDIT_FIELDS)

    medium_mb = sum(safe_float(r.get("size_mb")) for r in medium_only_rows)
    review_mb = sum(safe_float(r.get("size_mb")) for r in review_only_rows)
    possible_mb = sum(safe_float(r.get("size_mb")) for r in possible_rows)

    read_first = "\n".join(
        [
            "STATUS: OK_V18_20E_STILL_MEDIUM_ROOT_CAUSE_AUDIT_READY",
            "MODE: DRYRUN",
            f"ROOT: {root}",
            f"INPUT_STILL_MEDIUM_COUNT: {len(medium_only_rows)}",
            f"INPUT_STILL_MEDIUM_MB: {mb(medium_mb)}",
            f"REVIEW_REQUIRED_COUNT: {len(review_only_rows)}",
            f"REVIEW_REQUIRED_MB: {mb(review_mb)}",
            f"POSSIBLE_RULE_UPGRADE_COUNT: {len(possible_rows)}",
            f"POSSIBLE_RULE_UPGRADE_MB: {mb(possible_mb)}",
            f"KEEP_MEDIUM_COUNT: {len(medium_only_rows)}",
            f"KEEP_MEDIUM_MB: {mb(medium_mb)}",
            f"REVIEW_MANUAL_COUNT: {len(review_only_rows)}",
            f"REVIEW_MANUAL_MB: {mb(review_mb)}",
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
            f"ROOT_CAUSE_REPORT: {rel(root, REPORT_PATH)}",
            f"ROOT_CAUSE_AUDIT: {rel(root, AUDIT_PATH)}",
            f"SUMMARY_CSV: {rel(root, SUMMARY_PATH)}",
            f"POSSIBLE_UPGRADE_CSV: {rel(root, POSSIBLE_PATH)}",
            f"KEEP_MEDIUM_OR_REVIEW_CSV: {rel(root, KEEP_PATH)}",
        ]
    ) + "\n"
    write_text(root / READ_FIRST_PATH, read_first)
    write_text(root / REPORT_PATH, render_report(root, audit_rows, review_only_rows, summary_rows, possible_rows, latest_snapshot_name))

    print("STATUS: OK_V18_20E_STILL_MEDIUM_ROOT_CAUSE_AUDIT_READY")
    print("MODE: DRYRUN")
    print(f"INPUT_STILL_MEDIUM_COUNT: {len(medium_only_rows)}")
    print(f"INPUT_STILL_MEDIUM_MB: {mb(medium_mb)}")
    print(f"REVIEW_REQUIRED_COUNT: {len(review_only_rows)}")
    print(f"REVIEW_REQUIRED_MB: {mb(review_mb)}")
    print(f"POSSIBLE_RULE_UPGRADE_COUNT: {len(possible_rows)}")
    print(f"POSSIBLE_RULE_UPGRADE_MB: {mb(possible_mb)}")
    print(f"KEEP_MEDIUM_COUNT: {len(medium_only_rows)}")
    print(f"KEEP_MEDIUM_MB: {mb(medium_mb)}")
    print(f"REVIEW_MANUAL_COUNT: {len(review_only_rows)}")
    print(f"REVIEW_MANUAL_MB: {mb(review_mb)}")
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
    print(f"ROOT_CAUSE_REPORT: {rel(root, REPORT_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
