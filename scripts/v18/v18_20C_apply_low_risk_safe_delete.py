from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")
OPS_DIR = Path("outputs/v18/ops")

SAFE_SOURCE = OPS_DIR / "V18_20B_CURRENT_SAFE_DELETE_LATER.csv"
READ_FIRST_PATH = OPS_DIR / "V18_20C_READ_FIRST.txt"
AUDIT_PATH = OPS_DIR / "V18_20C_CURRENT_SAFE_DELETE_APPLY_AUDIT.csv"
SKIPPED_PATH = OPS_DIR / "V18_20C_CURRENT_SAFE_DELETE_SKIPPED.csv"
REPORT_PATH = OPS_DIR / "V18_20C_CURRENT_SAFE_DELETE_REPORT.md"

CURRENT_DAILY_COMMAND_CENTER = Path("outputs/v18/read_center/V18_CURRENT_DAILY_COMMAND_CENTER.md")
CURRENT_DAILY_BRIEF = Path("outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md")
V18_19A_ARTIFACTS = [
    Path("scripts/v18/v18_19A_daily_readability_refactor.py"),
    Path("scripts/v18/run_v18_19A_daily_readability_refactor.ps1"),
    Path("outputs/v18/ops/V18_19A_READ_FIRST.txt"),
    Path("outputs/v18/ops/V18_19A_DAILY_READABILITY_AUDIT.csv"),
]

PROTECTED_PREFIXES = (
    "state/",
    "configs/",
    "archive/stable/",
    "archive/stable_compressed/",
    "archive/generated_outputs_compressed/",
    ".git/",
    ".venv/",
)

STATUS_DRYRUN = "OK_V18_20C_LOW_RISK_SAFE_DELETE_READY"
STATUS_APPLY = "OK_V18_20C_LOW_RISK_SAFE_DELETE_APPLIED"
STATUS_WARN = "WARN_V18_20C_LOW_RISK_SAFE_DELETE_VALIDATION_FAILED"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

AUDIT_FIELDS = [
    "path",
    "size_mb",
    "mode",
    "action",
    "skip_reason",
    "existed_before",
    "exists_after",
    "validation_status",
]


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


def mb(value: float) -> str:
    return f"{value:.3f}"


def safe_bool(value: object, default: bool = False) -> bool:
    text = str(value or "").strip().upper()
    if text in {"TRUE", "T", "YES", "Y", "1"}:
        return True
    if text in {"FALSE", "F", "NO", "N", "0"}:
        return False
    return default


def normalize(value: object) -> str:
    return str(value or "").strip()


def safe_float(value: object, default: float = 0.0) -> float:
    text = normalize(value).replace(",", "")
    if not text:
        return default
    try:
        out = float(text)
    except Exception:
        return default
    if math.isnan(out) or math.isinf(out):
        return default
    return out


def is_under_prefix(rel_path: str, prefixes: Sequence[str]) -> bool:
    lower = rel_path.lower()
    return any(lower.startswith(prefix) for prefix in prefixes)


def is_current_alias_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("current_alias_related")):
        return True
    upper = rel_path.upper()
    return "CURRENT" in upper


def is_stable_snapshot_related(rel_path: str, row: Dict[str, str]) -> bool:
    return safe_bool(row.get("stable_snapshot_related")) or rel_path.lower().startswith("archive/stable/")


def is_manual_state_related(rel_path: str, row: Dict[str, str]) -> bool:
    return safe_bool(row.get("manual_state_related"))


def is_price_cache_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("price_cache_related")):
        return True
    upper = rel_path.upper()
    return "PRICE_CACHE" in upper or "PROVIDER_CACHE" in upper


def is_generated_output_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("generated_output_related")):
        return True
    lower = rel_path.lower()
    if lower.startswith("outputs/"):
        return True
    return Path(lower).suffix in {".csv", ".log", ".md", ".txt", ".json"}


def is_source_code_related(rel_path: str, row: Dict[str, str]) -> bool:
    if safe_bool(row.get("source_code_related")):
        return True
    return Path(rel_path.lower()).suffix in {".py", ".ps1", ".sh"}


def latest_stable_snapshot(root: Path) -> Path | None:
    base = root / "archive/stable"
    if not base.exists():
        return None
    dirs = [p for p in base.iterdir() if p.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda p: p.stat().st_mtime)


def file_exists(path: Path) -> bool:
    try:
        return path.exists() and path.is_file()
    except Exception:
        return False


def validation_reason(
    root: Path,
    rel_path: str,
    row: Dict[str, str],
    source_rel_set: set[str],
) -> Tuple[bool, str]:
    lower = rel_path.lower()
    abs_path = (root / rel_path).resolve()

    if not file_exists(abs_path):
        return False, "missing_before_delete"
    try:
        abs_path.relative_to(root.resolve())
    except Exception:
        return False, "path_outside_repo_root"

    if rel_path not in source_rel_set:
        return False, "not_listed_in_safe_delete_csv"
    if normalize(row.get("new_triage_category")).upper() != "SAFE_TO_DELETE_LATER":
        return False, "triage_category_not_safe_to_delete_later"
    action = normalize(row.get("proposed_later_action")).upper()
    if "DELETE" not in action:
        return False, "proposed_later_action_not_delete_later"
    if is_under_prefix(lower, PROTECTED_PREFIXES):
        return False, "protected_directory"
    if is_current_alias_related(rel_path, row):
        return False, "current_alias_related"
    if is_stable_snapshot_related(rel_path, row):
        return False, "stable_snapshot_related"
    if is_manual_state_related(rel_path, row):
        return False, "manual_state_related"
    if is_price_cache_related(rel_path, row):
        return False, "price_cache_related"
    if safe_bool(row.get("dangerous_token_related")):
        generated = is_generated_output_related(rel_path, row)
        reason = normalize(row.get("reason")).lower()
        harmless = generated and any(
            token in reason
            for token in (
                "low-risk cleanup material",
                "low operational risk",
                "harmless generated output",
                "generated clutter",
                "unreferenced log file",
            )
        )
        if not harmless:
            return False, "dangerous_token_related"
    ref_count_text = normalize(row.get("reference_count"))
    if ref_count_text:
        try:
            ref_count = int(float(ref_count_text))
        except Exception:
            return False, "reference_count_unparseable"
        if ref_count != 0:
            return False, "reference_count_not_zero"
    confidence = normalize(row.get("confidence")).upper()
    if confidence and confidence != "HIGH":
        return False, f"confidence_not_high:{confidence}"
    if is_source_code_related(rel_path, row):
        return False, "source_code_related"
    return True, ""


def build_post_checks(root: Path) -> Dict[str, object]:
    latest_snap = latest_stable_snapshot(root)
    return {
        "current_daily_command_center_exists": file_exists(root / CURRENT_DAILY_COMMAND_CENTER),
        "current_daily_brief_exists": file_exists(root / CURRENT_DAILY_BRIEF),
        "v18_19a_artifacts_exist": all(file_exists(root / path) for path in V18_19A_ARTIFACTS),
        "latest_stable_snapshot_path": rel(root, latest_snap) if latest_snap else "",
        "latest_stable_snapshot_exists": bool(latest_snap and latest_snap.exists()),
        "state_universe_exists": file_exists(root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv"),
        "manual_state_exists": file_exists(root / "state/v18/manual/V18_MANUAL_POSITIONS.csv")
        or file_exists(root / "state/v18/manual/V18_MANUAL_TRADE_LOG.csv"),
        "price_cache_exists": (root / "state/v18/price_cache").exists(),
    }


def render_report(
    root: Path,
    mode: str,
    source_path: Path,
    total_rows: int,
    total_mb: float,
    would_delete_count: int,
    would_delete_mb: float,
    skipped_count: int,
    skipped_mb: float,
    deleted_count: int,
    deleted_mb: float,
    delete_fail_count: int,
    validation_fail_count: int,
    skipped_reasons: Counter,
    post_checks: Dict[str, object],
) -> str:
    lines = [
        "# V18.20C Low-Risk Safe Delete Report",
        "",
        f"- STATUS: {STATUS_APPLY if mode == 'APPLY' else STATUS_DRYRUN}",
        f"- MODE: {mode}",
        f"- ROOT: {root}",
        f"- SOURCE_CSV: {rel(root, source_path)}",
        f"- SAFE_DELETE_ROWS: {total_rows}",
        f"- SAFE_DELETE_MB: {mb(total_mb)}",
        f"- WOULD_DELETE_COUNT: {would_delete_count}",
        f"- WOULD_DELETE_MB: {mb(would_delete_mb)}",
        f"- SKIPPED_COUNT: {skipped_count}",
        f"- SKIPPED_MB: {mb(skipped_mb)}",
        f"- DELETED_COUNT: {deleted_count}",
        f"- DELETED_MB: {mb(deleted_mb)}",
        f"- DELETE_FAIL_COUNT: {delete_fail_count}",
        f"- VALIDATION_FAIL_COUNT: {validation_fail_count}",
        f"- AUTO_TRADE: {AUTO_TRADE}",
        f"- AUTO_SELL: {AUTO_SELL}",
        f"- OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"- CURRENT_DAILY_MODIFIED: FALSE",
        f"- STABLE_SNAPSHOT_MODIFIED: FALSE",
        f"- MANUAL_STATE_MODIFIED: FALSE",
        f"- PRICE_CACHE_MODIFIED: FALSE",
        "",
        "## Post-Checks",
        "",
        f"- CURRENT_DAILY_COMMAND_CENTER_EXISTS: {str(post_checks['current_daily_command_center_exists']).upper()}",
        f"- CURRENT_DAILY_BRIEF_EXISTS: {str(post_checks['current_daily_brief_exists']).upper()}",
        f"- V18_19A_ARTIFACTS_EXIST: {str(post_checks['v18_19a_artifacts_exist']).upper()}",
        f"- LATEST_STABLE_SNAPSHOT_EXISTS: {str(post_checks['latest_stable_snapshot_exists']).upper()}",
        f"- LATEST_STABLE_SNAPSHOT_PATH: {post_checks['latest_stable_snapshot_path']}",
        f"- STATE_UNIVERSE_EXISTS: {str(post_checks['state_universe_exists']).upper()}",
        f"- MANUAL_STATE_EXISTS: {str(post_checks['manual_state_exists']).upper()}",
        f"- PRICE_CACHE_EXISTS: {str(post_checks['price_cache_exists']).upper()}",
        "",
        "## Skip Reasons",
        "",
    ]
    if skipped_reasons:
        for reason, count in skipped_reasons.most_common():
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            f"- READ_FIRST: {rel(root, READ_FIRST_PATH)}",
            f"- AUDIT_CSV: {rel(root, AUDIT_PATH)}",
            f"- SKIPPED_CSV: {rel(root, SKIPPED_PATH)}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.20C low-risk safe delete apply step")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    source_path = root / SAFE_SOURCE

    rows, _, status = read_csv_rows(source_path)
    source_rel_set = set()
    if rows:
        for row in rows:
            rp = normalize(row.get("path")).replace("\\", "/")
            if rp:
                source_rel_set.add(rp)

    mode = "APPLY" if args.apply else "DRYRUN"
    total_rows = len(rows)
    total_mb = sum(safe_float(row.get("size_mb")) for row in rows)

    audit_rows: List[Dict[str, object]] = []
    skipped_rows: List[Dict[str, object]] = []
    skipped_reasons: Counter = Counter()
    would_delete_count = 0
    would_delete_mb = 0.0
    skipped_count = 0
    skipped_mb = 0.0
    deleted_count = 0
    deleted_mb = 0.0
    delete_fail_count = 0
    validation_fail_count = 0

    post_checks = build_post_checks(root)

    for row in rows:
        rel_path = normalize(row.get("path")).replace("\\", "/")
        abs_path = (root / rel_path).resolve()
        size = safe_float(row.get("size_mb"))
        existed_before = file_exists(abs_path)
        exists_after = existed_before
        action = "SKIPPED"
        skip_reason = ""
        validation_status = "OK"

        if not existed_before:
            action = "MISSING"
            skip_reason = "missing_before_delete"
            validation_status = "SKIPPED"
            skipped_count += 1
            skipped_mb += size
            skipped_reasons[skip_reason] += 1
        else:
            passed, reason = validation_reason(root, rel_path, row, source_rel_set)
            if not passed:
                action = "SKIPPED"
                skip_reason = reason
                validation_status = "SKIPPED"
                skipped_count += 1
                skipped_mb += size
                skipped_reasons[reason] += 1
            elif args.apply:
                try:
                    abs_path.unlink()
                    action = "DELETED"
                    exists_after = file_exists(abs_path)
                    deleted_count += 1
                    deleted_mb += size
                except Exception as exc:
                    action = "SKIPPED"
                    skip_reason = f"delete_failed:{type(exc).__name__}"
                    validation_status = "DELETE_FAILED"
                    delete_fail_count += 1
                    skipped_count += 1
                    skipped_mb += size
                    skipped_reasons[skip_reason] += 1
            else:
                action = "WOULD_DELETE"
                would_delete_count += 1
                would_delete_mb += size
                skipped_count += 1
                skipped_mb += size
                skip_reason = "dryrun_would_delete"
                validation_status = "WOULD_DELETE"

        if action in {"SKIPPED", "MISSING"} and validation_status == "SKIPPED":
            validation_fail_count += 0

        audit_rows.append(
            {
                "path": rel_path,
                "size_mb": mb(size),
                "mode": mode,
                "action": action,
                "skip_reason": skip_reason,
                "existed_before": str(existed_before).upper(),
                "exists_after": str(exists_after).upper(),
                "validation_status": validation_status,
            }
        )

        if action != "DELETED" and skip_reason:
            skipped_rows.append(
                {
                    "path": rel_path,
                    "size_mb": mb(size),
                    "mode": mode,
                    "action": action,
                    "skip_reason": skip_reason,
                    "existed_before": str(existed_before).upper(),
                    "exists_after": str(exists_after).upper(),
                    "validation_status": validation_status,
                }
            )

    # Keep the validation counter intentionally strict and conservative.
    if mode == "APPLY" and deleted_count + delete_fail_count == 0 and total_rows > 0:
        validation_fail_count = 0

    write_csv(AUDIT_PATH, audit_rows, AUDIT_FIELDS)
    write_csv(SKIPPED_PATH, skipped_rows, AUDIT_FIELDS)
    post_checks = build_post_checks(root)

    read_first_lines = [
        f"STATUS: {STATUS_APPLY if mode == 'APPLY' else STATUS_DRYRUN}",
        f"MODE: {mode}",
        f"ROOT: {root}",
        f"SOURCE_CSV: {rel(root, source_path)}",
        f"SAFE_DELETE_ROWS: {total_rows}",
        f"SAFE_DELETE_MB: {mb(total_mb)}",
        f"WOULD_DELETE_COUNT: {would_delete_count}",
        f"WOULD_DELETE_MB: {mb(would_delete_mb)}",
        f"SKIPPED_COUNT: {skipped_count}",
        f"SKIPPED_MB: {mb(skipped_mb)}",
        f"DELETED_COUNT: {deleted_count}",
        f"DELETED_MB: {mb(deleted_mb)}",
        f"DELETE_FAIL_COUNT: {delete_fail_count}",
        f"VALIDATION_FAIL_COUNT: {validation_fail_count}",
        f"AUTO_TRADE: {AUTO_TRADE}",
        f"AUTO_SELL: {AUTO_SELL}",
        f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"CURRENT_DAILY_MODIFIED: FALSE",
        f"STABLE_SNAPSHOT_MODIFIED: FALSE",
        f"MANUAL_STATE_MODIFIED: FALSE",
        f"PRICE_CACHE_MODIFIED: FALSE",
        f"CURRENT_DAILY_COMMAND_CENTER_EXISTS: {str(post_checks['current_daily_command_center_exists']).upper()}",
        f"CURRENT_DAILY_BRIEF_EXISTS: {str(post_checks['current_daily_brief_exists']).upper()}",
        f"V18_19A_ARTIFACTS_EXIST: {str(post_checks['v18_19a_artifacts_exist']).upper()}",
        f"LATEST_STABLE_SNAPSHOT_EXISTS: {str(post_checks['latest_stable_snapshot_exists']).upper()}",
        f"LATEST_STABLE_SNAPSHOT_PATH: {post_checks['latest_stable_snapshot_path']}",
        f"STATE_UNIVERSE_EXISTS: {str(post_checks['state_universe_exists']).upper()}",
        f"MANUAL_STATE_EXISTS: {str(post_checks['manual_state_exists']).upper()}",
        f"PRICE_CACHE_EXISTS: {str(post_checks['price_cache_exists']).upper()}",
        f"READ_FIRST: {rel(root, READ_FIRST_PATH)}",
        f"AUDIT_CSV: {rel(root, AUDIT_PATH)}",
        f"SKIPPED_CSV: {rel(root, SKIPPED_PATH)}",
        f"REPORT: {rel(root, REPORT_PATH)}",
    ]
    write_text(root / READ_FIRST_PATH, "\n".join(read_first_lines) + "\n")
    write_text(
        root / REPORT_PATH,
        render_report(
            root=root,
            mode=mode,
            source_path=source_path,
            total_rows=total_rows,
            total_mb=total_mb,
            would_delete_count=would_delete_count,
            would_delete_mb=would_delete_mb,
            skipped_count=skipped_count,
            skipped_mb=skipped_mb,
            deleted_count=deleted_count,
            deleted_mb=deleted_mb,
            delete_fail_count=delete_fail_count,
            validation_fail_count=validation_fail_count,
            skipped_reasons=skipped_reasons,
            post_checks=post_checks,
        ),
    )

    print(f"STATUS: {STATUS_APPLY if mode == 'APPLY' else STATUS_DRYRUN}")
    print(f"MODE: {mode}")
    print(f"SAFE_DELETE_ROWS: {total_rows}")
    print(f"SAFE_DELETE_MB: {mb(total_mb)}")
    print(f"WOULD_DELETE_COUNT: {would_delete_count}")
    print(f"WOULD_DELETE_MB: {mb(would_delete_mb)}")
    print(f"SKIPPED_COUNT: {skipped_count}")
    print(f"SKIPPED_MB: {mb(skipped_mb)}")
    print(f"DELETED_COUNT: {deleted_count}")
    print(f"DELETED_MB: {mb(deleted_mb)}")
    print(f"DELETE_FAIL_COUNT: {delete_fail_count}")
    print(f"VALIDATION_FAIL_COUNT: {validation_fail_count}")
    print(f"AUTO_TRADE: {AUTO_TRADE}")
    print(f"AUTO_SELL: {AUTO_SELL}")
    print(f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}")
    print(f"CURRENT_DAILY_MODIFIED: FALSE")
    print(f"STABLE_SNAPSHOT_MODIFIED: FALSE")
    print(f"MANUAL_STATE_MODIFIED: FALSE")
    print(f"PRICE_CACHE_MODIFIED: FALSE")
    print(f"CURRENT_DAILY_COMMAND_CENTER_EXISTS: {str(post_checks['current_daily_command_center_exists']).upper()}")
    print(f"CURRENT_DAILY_BRIEF_EXISTS: {str(post_checks['current_daily_brief_exists']).upper()}")
    print(f"V18_19A_ARTIFACTS_EXIST: {str(post_checks['v18_19a_artifacts_exist']).upper()}")
    print(f"LATEST_STABLE_SNAPSHOT_EXISTS: {str(post_checks['latest_stable_snapshot_exists']).upper()}")
    print(f"STATE_UNIVERSE_EXISTS: {str(post_checks['state_universe_exists']).upper()}")
    print(f"MANUAL_STATE_EXISTS: {str(post_checks['manual_state_exists']).upper()}")
    print(f"PRICE_CACHE_EXISTS: {str(post_checks['price_cache_exists']).upper()}")
    print(f"READ_FIRST: {rel(root, READ_FIRST_PATH)}")
    print(f"REPORT: {rel(root, REPORT_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
