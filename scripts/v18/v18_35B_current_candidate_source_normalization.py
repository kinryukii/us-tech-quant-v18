#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable


STATUS_OK = "OK_V18_35B_CANDIDATE_SOURCE_NORMALIZATION_READY"
STATUS_WARN = "WARN_V18_35B_CANDIDATE_SOURCE_NORMALIZATION_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_35B_CANDIDATE_SOURCE_NORMALIZATION_FAILED"

AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FORBIDDEN_MODIFIED = "FALSE"


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def rel(root: Path, path: Path | None) -> str:
    if path is None:
        return "NONE"
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def read_csv_rows(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fieldnames(rows: list[dict[str, str]]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                keys.append(key)
                seen.add(key)
    return keys or ["ticker"]


def ticker_set(rows: list[dict[str, str]]) -> set[str]:
    return {norm_ticker(row.get("ticker") or row.get("yf_ticker")) for row in rows if norm_ticker(row.get("ticker") or row.get("yf_ticker"))}


def latest_freeze(rows: list[dict[str, str]]) -> tuple[str, set[str]]:
    by_date: dict[str, set[str]] = {}
    for row in rows:
        signal_date = str(row.get("signal_date", "")).strip()
        ticker = norm_ticker(row.get("ticker"))
        if signal_date and ticker:
            by_date.setdefault(signal_date, set()).add(ticker)
    if not by_date:
        return "UNKNOWN", set()
    date = sorted(by_date)[-1]
    return date, by_date[date]


def source_candidates(root: Path) -> list[Path]:
    rels = [
        "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
        "outputs/v18/candidates/V18_RESTORED_RANKED_CANDIDATES_FROM_R29C_SNAPSHOT.csv",
        "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
        "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
        "outputs/v18/candidates/V18_25A_R27J_CURRENT_RANKED_CANDIDATES_PREVIEW.csv",
        "outputs/v18/candidates/V18_25A_R25F_CURRENT_RANKED_CANDIDATES_PREVIEW.csv",
        "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
        "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
    ]
    return [root / item for item in rels if (root / item).exists()]


def is_candidate_source(path: Path) -> bool:
    text = path.as_posix()
    return "/outputs/v18/candidates/" in text or "\\outputs\\v18\\candidates\\" in str(path)


def classify_dependency(path: Path, text: str) -> tuple[str, str]:
    needle = "V18_CURRENT_RANKED_CANDIDATES.csv"
    idx = text.find(needle)
    if idx < 0:
        return "NONE", ""
    window = text[max(0, idx - 240): idx + len(needle) + 240].lower()
    if any(token in window for token in ["top", "display", "top_5", "second_stage", "ranked candidate read center"]):
        return "TOP_DISPLAY_EXPECTED", "Context contains display/top/second-stage language."
    if any(token in window for token in ["full", "freeze", "252", "candidate_count", "current candidate pool", "ranked rows"]):
        return "FULL_SET_EXPECTED", "Context contains full/freeze/candidate-count language."
    if path.suffix.lower() in {".py", ".ps1"}:
        return "UNKNOWN_SCRIPT_REFERENCE", "Script reference needs manual review before patching."
    return "UNKNOWN_REPORT_REFERENCE", "Report/reference context is ambiguous."


def dependency_scan(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    bases = [root / "scripts/v18", root / "outputs/v18/read_center"]
    for base in bases:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".ps1", ".md", ".txt"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "V18_CURRENT_RANKED_CANDIDATES.csv" not in text:
                continue
            role, notes = classify_dependency(path, text)
            rows.append(
                {
                    "path": rel(root, path),
                    "reference_role_guess": role,
                    "notes": notes,
                }
            )
    return rows


def source_role(path: Path, rows: list[dict[str, str]], tickers: set[str], freeze_set: set[str], current_alias: Path, selected_full: Path | None, selected_top: Path | None) -> str:
    if path == selected_full:
        return "FULL_CURRENT_CANDIDATE_SOURCE"
    if path == selected_top:
        return "TOP_DISPLAY_CANDIDATE_SOURCE"
    if path == current_alias and len(tickers) < len(freeze_set):
        return "LEGACY_CURRENT_ALIAS_TOP_DISPLAY"
    if tickers == freeze_set and freeze_set:
        return "FREEZE_MATCHED_CANDIDATE_EVIDENCE"
    if "factor_pack" in path.as_posix():
        return "FACTOR_PACK_EVIDENCE"
    if "technical_timing" in path.as_posix():
        return "TECHNICAL_TIMING_EVIDENCE"
    return "OTHER_CANDIDATE_EVIDENCE"


def copy_backup(src: Path, backup_dir: Path, root: Path) -> str:
    if not src.exists():
        return "MISSING"
    dst = backup_dir / rel(root, src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return str(dst)


def make_report(
    status: str,
    run_id: str,
    generated_at: str,
    summary: dict[str, object],
    source_map: list[dict[str, object]],
    deps: list[dict[str, str]],
    warnings: list[str],
    fails: list[str],
) -> str:
    lines = [
        "# V18.35B 当前候选池文件口径规范化",
        "",
        f"- STATUS: `{status}`",
        f"- RUN_ID: `{run_id}`",
        f"- GENERATED_AT: `{generated_at}`",
        "",
        "## 为什么 V18.35A 出现 WARN",
        "V18.35A 发现 `V18_CURRENT_RANKED_CANDIDATES.csv` 的行数与 current context / latest freeze 的 252 口径不一致。",
        "这个任务把 full current candidates、top display candidates 和 legacy/current alias 状态拆开，避免后续脚本误读。",
        "",
        "## 当前口径",
        f"- 修复前 `V18_CURRENT_RANKED_CANDIDATES.csv`: `{summary['current_ranked_candidates_count_before']}`",
        f"- 修复后 `V18_CURRENT_RANKED_CANDIDATES.csv`: `{summary['current_ranked_candidates_count_after']}`",
        f"- Full current candidates: `{summary['full_candidate_count']}`",
        f"- Top display candidates: `{summary['top_candidate_count']}`",
        f"- Latest signal freeze: `{summary['latest_signal_freeze_count']}`",
        f"- Full candidate matches freeze: `{summary['full_matches_freeze']}`",
        f"- Top is subset of full: `{summary['top_is_subset_of_full']}`",
        "",
        "## 是否执行 canonical alias repair",
        f"- Apply requested: `{summary['apply_canonical_alias_repair']}`",
        f"- Canonical alias repaired: `{summary['canonical_alias_repaired']}`",
        f"- Backup path: `{summary['backup_path']}`",
        "",
        "## Source Map",
        "| source | rows | unique_tickers | matches_latest_freeze | role | selected_full | selected_top |",
        "| --- | ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in source_map:
        lines.append(
            f"| `{row['source_file']}` | {row['row_count']} | {row['unique_ticker_count']} | "
            f"{row['matches_latest_freeze']} | `{row['source_role']}` | {row['selected_for_full']} | {row['selected_for_top']} |"
        )
    lines.extend(["", "## Dependency Scan"])
    lines.append(f"- Reference count: `{summary['dependency_reference_count']}`")
    lines.append(f"- Ambiguous reference count: `{summary['ambiguous_dependency_count']}`")
    if deps:
        lines.extend(["", "| file | role guess | notes |", "| --- | --- | --- |"])
        for row in deps[:80]:
            lines.append(f"| `{row['path']}` | `{row['reference_role_guess']}` | {row['notes']} |")
    else:
        lines.append("- No references found.")
    lines.extend(["", "## Warnings"])
    if warnings:
        lines.extend([f"- WARN: {item}" for item in warnings])
    else:
        lines.append("- NONE")
    lines.extend(["", "## Fail Reasons"])
    if fails:
        lines.extend([f"- FAIL: {item}" for item in fails])
    else:
        lines.append("- NONE")
    lines.extend(
        [
            "",
            "## Operator Next Action",
            "- 日常读完整候选池时优先使用 `outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv`。",
            "- 日常展示 top candidates 时使用 `outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv`。",
            "- 只有在确认需要恢复 canonical alias 为 full set 时，才运行 `-ApplyCanonicalAliasRepair`。",
            "- 若 command center 重新生成 20 行 alias，可再次运行 apply repair，或后续单独修复生成链路的 alias 语义。",
            "",
            "## Final Conclusion",
            "This is candidate source normalization only.",
            "No ranking/factor/freeze/trading/account logic was changed.",
            "`AUTO_TRADE DISABLED`, `AUTO_SELL DISABLED`, `OFFICIAL_DECISION_IMPACT NONE`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--apply-canonical-alias-repair", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    run_id = "V18_35B_" + stamp()
    generated_at = now_iso()

    current_alias = root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
    full_alias = root / "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
    top_alias = root / "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"
    source_map_path = root / "outputs/v18/candidates/V18_CURRENT_CANDIDATE_SOURCE_MAP.csv"
    summary_path = root / "outputs/v18/ops/V18_35B_CANDIDATE_SOURCE_NORMALIZATION_SUMMARY.csv"
    report_path = root / "outputs/v18/read_center/V18_35B_CANDIDATE_SOURCE_NORMALIZATION_REPORT.md"
    current_report_path = root / "outputs/v18/read_center/V18_CURRENT_CANDIDATE_SOURCE_NORMALIZATION.md"
    read_first_path = root / "outputs/v18/ops/V18_35B_READ_FIRST.txt"
    dependency_path = root / "outputs/v18/ops/V18_35B_CANDIDATE_SOURCE_DEPENDENCIES.csv"
    freeze_path = root / "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"

    warnings: list[str] = []
    fails: list[str] = []

    freeze_rows = read_csv_rows(freeze_path)
    latest_signal_date, freeze_set = latest_freeze(freeze_rows)
    if not freeze_set:
        fails.append("latest freeze cannot be read or is empty")

    current_rows_before = read_csv_rows(current_alias)
    current_set_before = ticker_set(current_rows_before)

    source_rows_by_path: dict[Path, list[dict[str, str]]] = {}
    source_sets: dict[Path, set[str]] = {}
    for path in source_candidates(root):
        rows = read_csv_rows(path)
        source_rows_by_path[path] = rows
        source_sets[path] = ticker_set(rows)

    full_source: Path | None = None
    for path, tickers in source_sets.items():
        if not is_candidate_source(path):
            continue
        if tickers == freeze_set and tickers:
            full_source = path
            break
    if full_source is None:
        fails.append("no usable full candidate source matching latest freeze was found")

    full_rows = source_rows_by_path.get(full_source, []) if full_source else []
    full_set = ticker_set(full_rows)

    top_source: Path | None = None
    if current_set_before and full_set and current_set_before.issubset(full_set) and len(current_set_before) < len(full_set):
        top_source = current_alias
    elif top_alias.exists():
        top_rows_existing = read_csv_rows(top_alias)
        if ticker_set(top_rows_existing).issubset(full_set):
            top_source = top_alias
    else:
        for path, tickers in source_sets.items():
            if tickers and full_set and tickers.issubset(full_set) and len(tickers) <= 50:
                top_source = path
                break
    top_rows = source_rows_by_path.get(top_source, read_csv_rows(top_source)) if top_source else []
    top_set = ticker_set(top_rows)

    full_matches_freeze = bool(full_set and full_set == freeze_set)
    top_is_subset = bool(top_set and full_set and top_set.issubset(full_set))
    candidate_freeze_mismatch = full_set.symmetric_difference(freeze_set) if full_set and freeze_set else set()
    if candidate_freeze_mismatch:
        fails.append(f"candidate/freeze mismatch count={len(candidate_freeze_mismatch)}")

    if not top_is_subset:
        warnings.append("top display candidate source is missing or not a subset of full candidate set")
    if current_set_before and full_set and len(current_set_before) != len(full_set):
        warnings.append("canonical current ranked candidate alias count differs from full current candidate count")

    deps = dependency_scan(root)
    ambiguous_deps = [
        row for row in deps
        if row["reference_role_guess"].startswith("UNKNOWN")
    ]
    if ambiguous_deps:
        warnings.append(f"dependency scan found ambiguous references: {len(ambiguous_deps)}")

    source_map_rows: list[dict[str, object]] = []
    for path, rows in source_rows_by_path.items():
        tickers = source_sets[path]
        role = source_role(path, rows, tickers, freeze_set, current_alias, full_source, top_source)
        notes = []
        if path == current_alias and len(tickers) != len(freeze_set):
            notes.append("canonical alias count differs from latest freeze")
        if tickers and freeze_set and tickers.issubset(freeze_set) and tickers != freeze_set:
            notes.append("ticker set is subset of freeze")
        source_map_rows.append(
            {
                "source_file": rel(root, path),
                "row_count": len(rows),
                "unique_ticker_count": len(tickers),
                "matches_latest_freeze": str(tickers == freeze_set and bool(tickers)).upper(),
                "source_role": role,
                "selected_for_full": str(path == full_source).upper(),
                "selected_for_top": str(path == top_source).upper(),
                "notes": "; ".join(notes) if notes else "",
            }
        )

    canonical_repaired = False
    backup_dir: Path | None = None

    try:
        if full_rows and full_source:
            write_csv(full_alias, fieldnames(full_rows), full_rows)
        if top_rows and top_source:
            write_csv(top_alias, fieldnames(top_rows), top_rows)

        if args.apply_canonical_alias_repair:
            if fails:
                raise RuntimeError("cannot apply alias repair while fail conditions exist: " + "; ".join(fails))
            if not full_matches_freeze:
                raise RuntimeError("full candidate source does not match latest freeze")
            if not top_is_subset:
                raise RuntimeError("top display alias is not a safe subset of full source")
            backup_dir = root / "archive/v18/candidate_alias_backups" / run_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            for target in [current_alias, full_alias, top_alias]:
                copy_backup(target, backup_dir, root)
            write_csv(current_alias, fieldnames(full_rows), full_rows)
            canonical_repaired = True
    except Exception as exc:  # noqa: BLE001
        fails.append(f"write/backup operation failed: {exc}")

    current_after_rows = read_csv_rows(current_alias)
    current_after_count = len(ticker_set(current_after_rows))
    if args.apply_canonical_alias_repair and not canonical_repaired:
        fails.append("apply mode requested but canonical alias was not repaired")
    if not args.apply_canonical_alias_repair and len(current_set_before) != len(full_set):
        warnings.append("canonical alias repair is available but was not applied")

    if fails:
        status = STATUS_FAIL
    elif warnings:
        status = STATUS_WARN
    else:
        status = STATUS_OK

    summary = {
        "status": status,
        "run_id": run_id,
        "generated_at": generated_at,
        "apply_canonical_alias_repair": str(args.apply_canonical_alias_repair).upper(),
        "canonical_alias_repaired": str(canonical_repaired).upper(),
        "current_ranked_candidates_count_before": len(current_set_before),
        "current_ranked_candidates_count_after": current_after_count,
        "full_candidate_count": len(full_set),
        "top_candidate_count": len(top_set),
        "latest_signal_freeze_count": len(freeze_set),
        "latest_signal_date": latest_signal_date,
        "full_matches_freeze": str(full_matches_freeze).upper(),
        "top_is_subset_of_full": str(top_is_subset).upper(),
        "backup_path": str(backup_dir) if backup_dir else "NONE",
        "selected_full_source_path": rel(root, full_source),
        "selected_top_source_path": rel(root, top_source),
        "source_map_path": rel(root, source_map_path),
        "dependency_reference_count": len(deps),
        "ambiguous_dependency_count": len(ambiguous_deps),
        "warning_count": len(warnings),
        "fail_count": len(fails),
        "fail_reason": "; ".join(fails),
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "forbidden_modified": FORBIDDEN_MODIFIED,
    }

    write_csv(
        source_map_path,
        ["source_file", "row_count", "unique_ticker_count", "matches_latest_freeze", "source_role", "selected_for_full", "selected_for_top", "notes"],
        source_map_rows,
    )
    write_csv(dependency_path, ["path", "reference_role_guess", "notes"], deps)
    write_csv(summary_path, list(summary.keys()), [summary])

    report = make_report(status, run_id, generated_at, summary, source_map_rows, deps, warnings, fails)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    current_report_path.write_text(report, encoding="utf-8")

    read_first = "\n".join(
        [
            f"STATUS: {status}",
            f"RUN_ID: {run_id}",
            f"APPLY_CANONICAL_ALIAS_REPAIR: {str(args.apply_canonical_alias_repair).upper()}",
            f"CANONICAL_ALIAS_REPAIRED: {str(canonical_repaired).upper()}",
            f"CURRENT_RANKED_CANDIDATES_COUNT_BEFORE: {len(current_set_before)}",
            f"CURRENT_RANKED_CANDIDATES_COUNT_AFTER: {current_after_count}",
            f"FULL_CANDIDATE_COUNT: {len(full_set)}",
            f"TOP_CANDIDATE_COUNT: {len(top_set)}",
            f"LATEST_SIGNAL_FREEZE_COUNT: {len(freeze_set)}",
            f"FULL_MATCHES_FREEZE: {str(full_matches_freeze).upper()}",
            f"TOP_IS_SUBSET_OF_FULL: {str(top_is_subset).upper()}",
            f"SELECTED_FULL_SOURCE: {rel(root, full_source)}",
            f"SELECTED_TOP_SOURCE: {rel(root, top_source)}",
            f"BACKUP_PATH: {str(backup_dir) if backup_dir else 'NONE'}",
            f"WARNING_COUNT: {len(warnings)}",
            f"FAIL_COUNT: {len(fails)}",
            f"REPORT: {rel(root, report_path)}",
            f"CURRENT_REPORT: {rel(root, current_report_path)}",
            f"SUMMARY_CSV: {rel(root, summary_path)}",
            f"SOURCE_MAP_CSV: {rel(root, source_map_path)}",
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
        "status",
        "run_id",
        "apply_canonical_alias_repair",
        "canonical_alias_repaired",
        "current_ranked_candidates_count_before",
        "current_ranked_candidates_count_after",
        "full_candidate_count",
        "top_candidate_count",
        "latest_signal_freeze_count",
        "full_matches_freeze",
        "top_is_subset_of_full",
        "backup_path",
        "warning_count",
        "fail_count",
    ]:
        print(f"{key.upper()}: {summary[key]}")
    print(f"REPORT: {current_report_path}")
    print(f"READ_FIRST: {read_first_path}")

    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
