#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path


STATUS_OK = "OK_V18_35C_CANDIDATE_SOURCE_DEPENDENCY_REVIEW_READY"
STATUS_WARN = "WARN_V18_35C_CANDIDATE_SOURCE_DEPENDENCY_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_35C_CANDIDATE_SOURCE_DEPENDENCY_REVIEW_FAILED"

ORIGINAL = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
FULL = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
TOP = "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"
ORIGINAL_BASENAME = "V18_CURRENT_RANKED_CANDIDATES.csv"
FULL_BASENAME = "V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
TOP_BASENAME = "V18_CURRENT_TOP_RANKED_CANDIDATES.csv"

AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FORBIDDEN_MODIFIED = "FALSE"


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ticker_count(path: Path) -> int:
    rows = read_csv_rows(path)
    return len({str(row.get("ticker", "")).strip().upper() for row in rows if str(row.get("ticker", "")).strip()})


def iter_target_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for base in [root / "scripts/v18", root / "outputs/v18/read_center"]:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".py", ".ps1", ".md", ".txt"}:
                files.append(path)
    return sorted(files)


def replacement_for(reference: str, replacement_path: str) -> str:
    if reference == ORIGINAL_BASENAME:
        if replacement_path == FULL:
            return FULL_BASENAME
        if replacement_path == TOP:
            return TOP_BASENAME
    return replacement_path


def classify(path: Path, line: str, prev_line: str, next_line: str, reference: str) -> tuple[str, str, str, str]:
    rel_path = path.as_posix().lower()
    context = f"{prev_line}\n{line}\n{next_line}".lower()
    name = path.name.lower()

    if "v18_35c_candidate_source_dependency_role_review.py" in name:
        return "DO_NOT_PATCH", "", "self-reference for dependency review tool", "LOW"
    if "v18_35b_current_candidate_source_normalization.py" in name:
        return "DO_NOT_PATCH", "", "self-reference for alias normalization tool", "LOW"
    if "v18_35d_full_universe_factor_technical_recompute.py" in name:
        return "DO_NOT_PATCH", "", "V18.35D intentionally references current aliases for explicit backup/apply targets", "LOW"
    if "/outputs/v18/read_center/" in rel_path or "\\outputs\\v18\\read_center\\" in str(path).lower():
        return "TEXT_ONLY_REPORT_REFERENCE", "", "generated/read-center report text reference", "LOW"

    top_file_names = {
        "v18_14b_current_daily_command_center.py",
        "v18_25a_r26a_forward_test_factor_effectiveness_readiness_audit.py",
    }
    if name in top_file_names:
        return "TOP_DISPLAY_EXPECTED", replacement_for(reference, TOP), "script context uses second-stage/top display candidate rows", "LOW"

    if any(token in context for token in ["top_5", "second_stage", "display", "top ranked", "top candidate"]):
        return "TOP_DISPLAY_EXPECTED", replacement_for(reference, TOP), "line context clearly references top/display candidates", "LOW"

    full_file_names = {
        "v18_31f_full_daily_trade_readiness_runner.py",
        "v18_32b_codex_context_compression_pack.py",
        "v18_32c_compact_context_consistency_audit.py",
        "v18_32d_latest_supported_signal_date_freeze_repair.py",
        "v18_33a_chinese_daily_operator_homepage.py",
        "v18_34a_storage_inventory_safe_cleanup.py",
        "v18_34c_trade_readiness_current_refresh.py",
        "v18_35a_universe_to_candidate_diff_audit.py",
    }
    if name in full_file_names:
        return "FULL_SET_EXPECTED", replacement_for(reference, FULL), "script is a current full-context/freeze/readiness audit consumer", "LOW"

    if any(token in context for token in ["freeze", "full", "candidate_count", "ranked rows", "coverage", "readiness"]):
        if any(token in name for token in ["promote", "regeneration", "refresh_ranked_candidate", "preview"]):
            return "UNKNOWN_SCRIPT_REFERENCE", "", "candidate generation/promotion context; not safe to patch automatically", "MEDIUM"
        return "FULL_SET_EXPECTED", replacement_for(reference, FULL), "line context clearly expects full candidate coverage", "LOW"

    if any(token in name for token in ["stable_snapshot", "promotion", "merge", "regeneration", "ranked_candidates_preview"]):
        return "UNKNOWN_SCRIPT_REFERENCE", "", "historical/promotion/generation script context needs manual review", "MEDIUM"

    if path.suffix.lower() in {".py", ".ps1"}:
        return "UNKNOWN_SCRIPT_REFERENCE", "", "script reference could not be confidently classified", "MEDIUM"

    return "LEGACY_ALIAS_COMPATIBLE", "", "reference can remain on legacy alias", "LOW"


def scan_references(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in iter_target_files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for idx, line in enumerate(lines, start=1):
            if ORIGINAL in line:
                references = [ORIGINAL]
            elif ORIGINAL_BASENAME in line:
                references = [ORIGINAL_BASENAME]
            else:
                references = []
            if not references:
                continue
            prev_line = lines[idx - 2] if idx >= 2 else ""
            next_line = lines[idx] if idx < len(lines) else ""
            for reference in references:
                role, replacement, reason, risk = classify(path, line, prev_line, next_line, reference)
                patch_recommended = role in {"FULL_SET_EXPECTED", "TOP_DISPLAY_EXPECTED"} and bool(replacement)
                rows.append(
                    {
                        "file_path": rel(root, path),
                        "line_number": idx,
                        "original_reference": reference,
                        "classified_role": role,
                        "proposed_replacement": replacement,
                        "patch_recommended": str(patch_recommended).upper(),
                        "patch_applied": "FALSE",
                        "reason": reason,
                        "risk_level": risk,
                    }
                )
    return rows


def backup_file(root: Path, backup_root: Path, rel_file: str) -> None:
    src = root / rel_file
    dst = backup_root / rel_file
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def apply_patches(root: Path, rows: list[dict[str, object]], backup_root: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    by_file: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        if row["patch_recommended"] == "TRUE":
            by_file.setdefault(str(row["file_path"]), []).append(row)

    applied_count = 0
    for rel_file, file_rows in by_file.items():
        path = root / rel_file
        try:
            backup_file(root, backup_root, rel_file)
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
            for row in file_rows:
                line_idx = int(row["line_number"]) - 1
                replacement = str(row["proposed_replacement"])
                original = str(row["original_reference"])
                if 0 <= line_idx < len(lines) and original in lines[line_idx]:
                    lines[line_idx] = lines[line_idx].replace(original, replacement)
                    row["patch_applied"] = "TRUE"
                    applied_count += 1
            path.write_text("".join(lines), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{rel_file}: {exc}")
    return applied_count, errors


def make_report(
    status: str,
    run_id: str,
    generated_at: str,
    summary: dict[str, object],
    rows: list[dict[str, object]],
    warnings: list[str],
    failures: list[str],
) -> str:
    counts = Counter(str(row["classified_role"]) for row in rows)
    applied = [row for row in rows if row["patch_applied"] == "TRUE"]
    unknown = [row for row in rows if row["classified_role"] == "UNKNOWN_SCRIPT_REFERENCE"]
    lines = [
        "# V18.35C 候选池引用依赖角色审计与安全补丁",
        "",
        f"- STATUS: `{status}`",
        f"- RUN_ID: `{run_id}`",
        f"- GENERATED_AT: `{generated_at}`",
        "",
        "## 为什么需要 V18.35C",
        "`V18_CURRENT_RANKED_CANDIDATES.csv` 已被 V18.35B 修复为 full 252-row alias，但代码和报告中仍有旧引用。",
        "本步骤逐行判断引用语义，把明确 full/top 的引用改到更明确的新文件名；不确定的脚本引用只报告，不强改。",
        "",
        "## 当前候选源状态",
        f"- Current canonical alias rows: `{summary['current_alias_count']}`",
        f"- Full candidate alias rows: `{summary['full_alias_count']}`",
        f"- Top display alias rows: `{summary['top_alias_count']}`",
        "",
        "## Role Count",
        "| role | count |",
        "| --- | ---: |",
    ]
    for role, count in counts.most_common():
        lines.append(f"| `{role}` | {count} |")
    lines.extend(
        [
            "",
            "## Patch Summary",
            f"- Apply requested: `{summary['apply_safe_reference_patches']}`",
            f"- Patch recommended: `{summary['patch_recommended_count']}`",
            f"- Patch applied: `{summary['patch_applied_count']}`",
            f"- Backup path: `{summary['backup_path']}`",
            "",
            "| file | line | role | replacement |",
            "| --- | ---: | --- | --- |",
        ]
    )
    if applied:
        for row in applied[:120]:
            lines.append(f"| `{row['file_path']}` | {row['line_number']} | `{row['classified_role']}` | `{row['proposed_replacement']}` |")
    else:
        lines.append("| NONE |  |  |  |")
    lines.extend(["", "## Remaining Unknown References Sample", "| file | line | reason |", "| --- | ---: | --- |"])
    if unknown:
        for row in unknown[:80]:
            lines.append(f"| `{row['file_path']}` | {row['line_number']} | {row['reason']} |")
    else:
        lines.append("| NONE |  |  |")
    lines.extend(["", "## Warnings"])
    lines.extend([f"- WARN: {item}" for item in warnings] if warnings else ["- NONE"])
    lines.extend(["", "## Failures"])
    lines.extend([f"- FAIL: {item}" for item in failures] if failures else ["- NONE"])
    lines.extend(
        [
            "",
            "## Operator Next Action",
            "- 对 `UNKNOWN_SCRIPT_REFERENCE` 保持人工复核，不要批量替换。",
            "- 如果 command center 后续仍会重写 top display alias 到 canonical alias，应优先修复对应 read-center alias 生成语义。",
            "- 日常 full candidate 消费优先使用 `V18_CURRENT_FULL_RANKED_CANDIDATES.csv`。",
            "- 日常 top display 消费优先使用 `V18_CURRENT_TOP_RANKED_CANDIDATES.csv`。",
            "",
            "## Final Conclusion",
            "This is dependency source normalization only.",
            "No ranking/factor/freeze/trading/account logic was changed.",
            "`AUTO_TRADE DISABLED`, `AUTO_SELL DISABLED`, `OFFICIAL_DECISION_IMPACT NONE`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--apply-safe-reference-patches", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    run_id = "V18_35C_" + now_stamp()
    generated_at = now_iso()

    current_alias = root / ORIGINAL
    full_alias = root / FULL
    top_alias = root / TOP
    detail_csv = root / "outputs/v18/ops/V18_35C_CANDIDATE_SOURCE_DEPENDENCY_REVIEW.csv"
    summary_csv = root / "outputs/v18/ops/V18_35C_CANDIDATE_SOURCE_DEPENDENCY_PATCH_SUMMARY.csv"
    report_path = root / "outputs/v18/read_center/V18_35C_CANDIDATE_SOURCE_DEPENDENCY_REVIEW_REPORT.md"
    current_report_path = root / "outputs/v18/read_center/V18_CURRENT_CANDIDATE_SOURCE_DEPENDENCY_REVIEW.md"
    read_first_path = root / "outputs/v18/ops/V18_35C_READ_FIRST.txt"

    failures: list[str] = []
    warnings: list[str] = []
    for required in [current_alias, full_alias, top_alias]:
        if not required.exists():
            failures.append(f"missing candidate source file: {rel(root, required)}")

    rows = scan_references(root)
    if not rows:
        failures.append("dependency input cannot be read and fallback scan found no references")

    patch_recommended = sum(1 for row in rows if row["patch_recommended"] == "TRUE")
    backup_root: Path | None = None
    patch_applied = 0
    if args.apply_safe_reference_patches and patch_recommended and not failures:
        backup_root = root / "archive/v18/candidate_dependency_patch_backups" / run_id
        try:
            backup_root.mkdir(parents=True, exist_ok=True)
            patch_applied, errors = apply_patches(root, rows, backup_root)
            failures.extend([f"patch failed: {item}" for item in errors])
        except Exception as exc:  # noqa: BLE001
            failures.append(f"patch backup or apply failed: {exc}")

    if not args.apply_safe_reference_patches and patch_recommended:
        warnings.append("audit-only mode used and safe patches are available but not applied")

    role_counts = Counter(str(row["classified_role"]) for row in rows)
    remaining_unknown = role_counts.get("UNKNOWN_SCRIPT_REFERENCE", 0)
    if remaining_unknown:
        warnings.append(f"unknown script references remain: {remaining_unknown}")

    if failures:
        status = STATUS_FAIL
    elif warnings:
        status = STATUS_WARN
    else:
        status = STATUS_OK

    summary = {
        "status": status,
        "run_id": run_id,
        "generated_at": generated_at,
        "apply_safe_reference_patches": str(args.apply_safe_reference_patches).upper(),
        "total_reference_count": len(rows),
        "full_set_expected_count": role_counts.get("FULL_SET_EXPECTED", 0),
        "top_display_expected_count": role_counts.get("TOP_DISPLAY_EXPECTED", 0),
        "legacy_alias_compatible_count": role_counts.get("LEGACY_ALIAS_COMPATIBLE", 0),
        "text_only_report_reference_count": role_counts.get("TEXT_ONLY_REPORT_REFERENCE", 0),
        "unknown_script_reference_count": role_counts.get("UNKNOWN_SCRIPT_REFERENCE", 0),
        "do_not_patch_count": role_counts.get("DO_NOT_PATCH", 0),
        "patch_recommended_count": patch_recommended,
        "patch_applied_count": patch_applied,
        "remaining_unknown_count": remaining_unknown,
        "backup_path": str(backup_root) if backup_root else "NONE",
        "warning_count": len(warnings),
        "fail_count": len(failures),
        "fail_reason": "; ".join(failures),
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "forbidden_modified": FORBIDDEN_MODIFIED,
        "current_alias_count": ticker_count(current_alias),
        "full_alias_count": ticker_count(full_alias),
        "top_alias_count": ticker_count(top_alias),
    }

    fields = [
        "file_path", "line_number", "original_reference", "classified_role", "proposed_replacement",
        "patch_recommended", "patch_applied", "reason", "risk_level",
    ]
    write_csv(detail_csv, fields, rows)
    write_csv(summary_csv, list(summary.keys()), [summary])
    report = make_report(status, run_id, generated_at, summary, rows, warnings, failures)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    current_report_path.write_text(report, encoding="utf-8")

    read_first = "\n".join(
        [
            f"STATUS: {status}",
            f"RUN_ID: {run_id}",
            f"APPLY_SAFE_REFERENCE_PATCHES: {str(args.apply_safe_reference_patches).upper()}",
            f"TOTAL_REFERENCE_COUNT: {len(rows)}",
            f"FULL_SET_EXPECTED_COUNT: {summary['full_set_expected_count']}",
            f"TOP_DISPLAY_EXPECTED_COUNT: {summary['top_display_expected_count']}",
            f"LEGACY_ALIAS_COMPATIBLE_COUNT: {summary['legacy_alias_compatible_count']}",
            f"TEXT_ONLY_REPORT_REFERENCE_COUNT: {summary['text_only_report_reference_count']}",
            f"UNKNOWN_SCRIPT_REFERENCE_COUNT: {summary['unknown_script_reference_count']}",
            f"PATCH_RECOMMENDED_COUNT: {patch_recommended}",
            f"PATCH_APPLIED_COUNT: {patch_applied}",
            f"REMAINING_UNKNOWN_COUNT: {remaining_unknown}",
            f"BACKUP_PATH: {str(backup_root) if backup_root else 'NONE'}",
            f"WARNING_COUNT: {len(warnings)}",
            f"FAIL_COUNT: {len(failures)}",
            f"REPORT: {rel(root, report_path)}",
            f"CURRENT_REPORT: {rel(root, current_report_path)}",
            f"DETAIL_CSV: {rel(root, detail_csv)}",
            f"SUMMARY_CSV: {rel(root, summary_csv)}",
            "OFFICIAL_DECISION_IMPACT: NONE",
            "AUTO_TRADE: DISABLED",
            "AUTO_SELL: DISABLED",
            f"FORBIDDEN_MODIFIED: {FORBIDDEN_MODIFIED}",
            "",
        ]
    )
    read_first_path.parent.mkdir(parents=True, exist_ok=True)
    read_first_path.write_text(read_first, encoding="utf-8")

    for key in [
        "status", "run_id", "apply_safe_reference_patches", "total_reference_count",
        "full_set_expected_count", "top_display_expected_count", "unknown_script_reference_count",
        "patch_recommended_count", "patch_applied_count", "remaining_unknown_count",
        "backup_path", "warning_count", "fail_count",
    ]:
        print(f"{key.upper()}: {summary[key]}")
    print(f"REPORT: {current_report_path}")
    print(f"READ_FIRST: {read_first_path}")
    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
