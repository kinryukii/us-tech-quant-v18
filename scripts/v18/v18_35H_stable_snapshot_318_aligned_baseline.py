from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


STATUS_OK = "OK_V18_35H_STABLE_SNAPSHOT_318_ALIGNED_READY"
STATUS_WARN = "WARN_V18_35H_STABLE_SNAPSHOT_318_ALIGNED_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_35H_STABLE_SNAPSHOT_318_ALIGNED_FAILED"

AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FORBIDDEN_MODIFIED = "FALSE"

UNIVERSE = "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv"
ROLLING = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"
FREEZE = "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv"
CURRENT_FULL = "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv"
CURRENT_RANKED = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
CURRENT_TOP = "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"
FACTOR_35D = "outputs/v18/factor_pack/V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv"
TECH_35D = "outputs/v18/technical_timing/V18_35D_FULL_UNIVERSE_TECHNICAL_TIMING.csv"
READ_A = "outputs/v18/ops/V18_35A_READ_FIRST.txt"
READ_D = "outputs/v18/ops/V18_35D_READ_FIRST.txt"
READ_E = "outputs/v18/ops/V18_35E_READ_FIRST.txt"
READ_F = "outputs/v18/ops/V18_35F_READ_FIRST.txt"
READ_G = "outputs/v18/ops/V18_35G_READ_FIRST.txt"
HOMEPAGE = "outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md"
FRESHNESS = "outputs/v18/read_center/V18_CURRENT_DAILY_OUTPUT_FRESHNESS.md"
AUDIT = "outputs/v18/read_center/V18_CURRENT_UNIVERSE_TO_CANDIDATE_AUDIT.md"
CMD_CENTER = "scripts/v18/run_v18_current_daily_command_center.ps1"

OUT_SUMMARY = "outputs/v18/ops/V18_35H_STABLE_SNAPSHOT_SUMMARY.csv"
OUT_REPORT = "outputs/v18/read_center/V18_35H_STABLE_SNAPSHOT_REPORT.md"
OUT_CURRENT = "outputs/v18/read_center/V18_CURRENT_318_ALIGNED_BASELINE.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_35H_READ_FIRST.txt"

SNAPSHOT_NAME_PREFIX = "V18_35H_318_aligned_universe_candidate_freeze"


CRITICAL_SOURCES = [
    UNIVERSE,
    ROLLING,
    FREEZE,
    CURRENT_FULL,
    CURRENT_RANKED,
    CURRENT_TOP,
    FACTOR_35D,
    TECH_35D,
]

OPTIONAL_SOURCES = [
    "scripts/v18/v18_35A_universe_to_candidate_diff_audit.py",
    "scripts/v18/run_v18_35A_universe_to_candidate_diff_audit.ps1",
    "scripts/v18/v18_35B_current_candidate_source_normalization.py",
    "scripts/v18/run_v18_35B_current_candidate_source_normalization.ps1",
    "scripts/v18/v18_35C_candidate_source_dependency_role_review.py",
    "scripts/v18/run_v18_35C_candidate_source_dependency_role_review.ps1",
    "scripts/v18/v18_35D_full_universe_factor_technical_recompute.py",
    "scripts/v18/run_v18_35D_full_universe_factor_technical_recompute.ps1",
    "scripts/v18/v18_35E_online_backfill_candidate_adoption_bridge.py",
    "scripts/v18/run_v18_35E_online_backfill_candidate_adoption_bridge.ps1",
    "scripts/v18/v18_35F_next_signal_freeze_expansion.py",
    "scripts/v18/run_v18_35F_next_signal_freeze_expansion.ps1",
    "scripts/v18/v18_35G_universe_invalid_ticker_prune.py",
    "scripts/v18/run_v18_35G_universe_invalid_ticker_prune.ps1",
    CMD_CENTER,
    READ_A,
    READ_D,
    READ_E,
    READ_F,
    READ_G,
    HOMEPAGE,
    FRESHNESS,
    AUDIT,
]


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def norm(v: object) -> str:
    return str(v or "").strip().upper()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as f:
                reader = csv.DictReader(f)
                return [dict(r) for r in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_status(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def ticker_set(rows: list[dict[str, str]]) -> set[str]:
    out = set()
    for row in rows:
        t = norm(row.get("ticker") or row.get("yf_ticker") or row.get("symbol"))
        if t:
            out.add(t)
    return out


def duplicate_count(rows: list[dict[str, str]], key_fields: Sequence[str]) -> int:
    counts: dict[tuple[str, ...], int] = {}
    for row in rows:
        key = tuple(norm(row.get(field)) for field in key_fields)
        if any(key):
            counts[key] = counts.get(key, 0) + 1
    return sum(1 for _, c in counts.items() if c > 1)


def latest_freeze(rows: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
    by_date: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        d = norm(row.get("signal_date"))
        if d:
            by_date.setdefault(d, []).append(row)
    if not by_date:
        return "", []
    d = sorted(by_date)[-1]
    return d, by_date[d]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_file(root: Path, snapshot: Path, rel: str) -> dict[str, object]:
    src = root / rel
    rel_path = Path(rel)
    dst = snapshot / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    stat = src.stat()
    return {
        "source_path": src.as_posix(),
        "snapshot_path": dst.relative_to(snapshot).as_posix(),
        "size_bytes": stat.st_size,
        "modified_time": datetime.fromtimestamp(stat.st_mtime).replace(microsecond=0).isoformat(),
        "sha256": sha256_file(src),
        "copied_at": iso_now(),
    }


def render_report(summary: dict[str, object], validation_rows: list[dict[str, object]], snapshot_path: str, restore_path: str) -> str:
    lines = [
        "# V18.35H 318 对齐稳定快照",
        "",
        f"- STATUS: `{summary['status']}`",
        f"- RUN_ID: `{summary['run_id']}`",
        f"- SNAPSHOT_PATH: `{snapshot_path}`",
        "",
        "## 说明",
        "V18.35A-G 已经把 active universe、current candidates、latest freeze 和 rank eligible 全部对齐到 318，并清理了 15 个无效 ticker。",
        "旧的 2026-05-22 / 252 freeze 历史仍保留在 ledger 中，新的 318 baseline 已经成为当前稳定快照参考。",
        "",
        "## Count Summary",
        "| item | value |",
        "| --- | ---: |",
        f"| total universe | {summary['total_universe_count']} |",
        f"| current full candidates | {summary['current_full_candidate_count']} |",
        f"| current ranked candidates | {summary['current_ranked_candidate_count']} |",
        f"| current top candidates | {summary['current_top_candidate_count']} |",
        f"| latest signal freeze | {summary['latest_signal_freeze_count']} |",
        f"| rank eligible | {summary['rank_eligible_count']} |",
        f"| rank ineligible | {summary['rank_ineligible_count']} |",
        f"| remaining uncomputed | {summary['remaining_uncomputed_count']} |",
        f"| new recomputed not in freeze | {summary['new_recomputed_not_in_freeze_count']} |",
        f"| duplicate universe tickers | {summary['duplicate_universe_ticker_count']} |",
        f"| duplicate candidate tickers | {summary['duplicate_candidate_ticker_count']} |",
        f"| duplicate latest signal_date+ticker | {summary['duplicate_latest_signal_date_ticker_count']} |",
        "",
        "## Validation",
        "| check | status | detail |",
        "| --- | --- | --- |",
    ]
    for row in validation_rows:
        lines.append(f"| {row.get('check_name')} | `{row.get('status')}` | {row.get('detail')} |")
    lines += [
        "",
        "## Archive",
        f"- Snapshot path: `{snapshot_path}`",
        f"- Restore script: `{restore_path}`",
        "",
        "## Operator Next Action",
        "- Keep this snapshot as the baseline for V18.36A paper trading / forward attribution work.",
        "- If a restore is ever needed, run the restore script from the snapshot root and then re-run the V18.35 validation chain.",
        "",
        "## Final Conclusion",
        "这是进入 paper trading 前的稳定封存。",
        "No trading/order/account logic was modified.",
        "AUTO_TRADE DISABLED, AUTO_SELL DISABLED, OFFICIAL_DECISION_IMPACT NONE.",
    ]
    return "\n".join(lines) + "\n"


def render_restore_script() -> str:
    return """[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$Manifest = Join-Path $PSScriptRoot "MANIFEST.csv"

Write-Host "=== RESTORE V18.35H STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "SNAPSHOT_ROOT: $PSScriptRoot"
Write-Host "MANIFEST: $Manifest"

if (-not (Test-Path $Manifest)) {
    throw "Missing MANIFEST.csv: $Manifest"
}

$rows = Import-Csv -Path $Manifest
foreach ($row in $rows) {
    $source = Join-Path $PSScriptRoot $row.snapshot_path
    $target = Join-Path $Root $row.source_path
    if (-not (Test-Path $source)) {
        throw "Missing snapshot file: $source"
    }
    $dir = Split-Path $target -Parent
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    Copy-Item -LiteralPath $source -Destination $target -Force
}

Write-Host "=== RESTORE V18.35H STABLE SNAPSHOT DONE ==="
Write-Host "FILES_RESTORED: $($rows.Count)"
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root)
    now = datetime.now().replace(microsecond=0)
    snapshot_stamp = stamp()
    run_id = f"V18_35H_{snapshot_stamp}"
    snapshot = root / "archive/stable" / f"{SNAPSHOT_NAME_PREFIX}_{snapshot_stamp}"
    snapshot.mkdir(parents=True, exist_ok=True)

    total_universe_rows, _ = read_csv(root / UNIVERSE)
    current_full_rows, _ = read_csv(root / CURRENT_FULL)
    current_ranked_rows, _ = read_csv(root / CURRENT_RANKED)
    current_top_rows, _ = read_csv(root / CURRENT_TOP)
    freeze_rows, _ = read_csv(root / FREEZE)
    rolling_rows, _ = read_csv(root / ROLLING)
    universe_set = ticker_set(total_universe_rows)
    full_set = ticker_set(current_full_rows)
    ranked_set = ticker_set(current_ranked_rows)
    top_set = ticker_set(current_top_rows)
    _, latest_freeze_rows = latest_freeze(freeze_rows)
    latest_freeze_set = ticker_set(latest_freeze_rows)

    d35 = read_status(root / READ_D)
    e35 = read_status(root / READ_E)
    f35 = read_status(root / READ_F)
    g35 = read_status(root / READ_G)
    a35 = read_status(root / READ_A)

    read_files = [
        root / READ_A,
        root / READ_D,
        root / READ_E,
        root / READ_F,
        root / READ_G,
    ]
    current_status_files = [
        root / HOMEPAGE,
        root / FRESHNESS,
        root / AUDIT,
    ]

    copied_rows: list[dict[str, object]] = []
    missing_optional = 0
    missing_critical = 0

    for rel in CRITICAL_SOURCES + OPTIONAL_SOURCES:
        src = root / rel
        if src.exists():
            copied_rows.append({"category": "source", **copy_file(root, snapshot, rel)})
        else:
            if rel in CRITICAL_SOURCES:
                missing_critical += 1
            else:
                missing_optional += 1

    if missing_critical:
        status = STATUS_FAIL
    else:
        validation_fail_count = 0
        validations = []

        def add_check(name: str, ok: bool, detail: str) -> None:
            nonlocal validation_fail_count
            validations.append({
                "check_name": name,
                "status": "PASS" if ok else "FAIL",
                "expected": "",
                "actual": "",
                "detail": detail,
            })
            if not ok:
                validation_fail_count += 1

        add_check("TOTAL_UNIVERSE_COUNT_318", len(universe_set) == 318, str(len(universe_set)))
        add_check("CURRENT_FULL_CANDIDATE_COUNT_318", len(full_set) == 318, str(len(full_set)))
        add_check("CURRENT_RANKED_CANDIDATE_COUNT_318", len(ranked_set) == 318, str(len(ranked_set)))
        add_check("CURRENT_TOP_CANDIDATE_COUNT_20", len(top_set) == 20, str(len(top_set)))
        add_check("LATEST_SIGNAL_FREEZE_COUNT_318", len(latest_freeze_set) == 318, str(len(latest_freeze_set)))
        add_check("RANK_ELIGIBLE_COUNT_318", norm(d35.get("RANK_ELIGIBLE_COUNT", "")) == "318", d35.get("RANK_ELIGIBLE_COUNT", ""))
        add_check("RANK_INELIGIBLE_COUNT_0", norm(d35.get("RANK_INELIGIBLE_COUNT", "")) == "0", d35.get("RANK_INELIGIBLE_COUNT", ""))
        add_check("REMAINING_UNCOMPUTED_COUNT_0", norm(e35.get("STILL_UNCOMPUTED_AFTER_BACKFILL_COUNT", "")) == "0", e35.get("STILL_UNCOMPUTED_AFTER_BACKFILL_COUNT", ""))
        add_check("NEW_RECOMPUTED_NOT_IN_FREEZE_0", norm(e35.get("NEW_RECOMPUTED_NOT_IN_FREEZE_COUNT", "")) == "0", e35.get("NEW_RECOMPUTED_NOT_IN_FREEZE_COUNT", ""))
        add_check("DUPLICATE_UNIVERSE_TICKER_COUNT_0", duplicate_count(total_universe_rows, ["ticker"]) == 0, str(duplicate_count(total_universe_rows, ["ticker"])))
        add_check("DUPLICATE_CANDIDATE_TICKER_COUNT_0", duplicate_count(current_full_rows, ["ticker"]) == 0, str(duplicate_count(current_full_rows, ["ticker"])))
        add_check("DUPLICATE_LATEST_SIGNAL_DATE_TICKER_COUNT_0", duplicate_count(latest_freeze_rows, ["signal_date", "ticker"]) == 0, str(duplicate_count(latest_freeze_rows, ["signal_date", "ticker"])))
        add_check("AUTO_TRADE_DISABLED", d35.get("AUTO_TRADE", "") == "DISABLED", d35.get("AUTO_TRADE", ""))
        add_check("AUTO_SELL_DISABLED", d35.get("AUTO_SELL", "") == "DISABLED", d35.get("AUTO_SELL", ""))
        add_check("OFFICIAL_DECISION_IMPACT_NONE", d35.get("OFFICIAL_DECISION_IMPACT", "") == "NONE", d35.get("OFFICIAL_DECISION_IMPACT", ""))
        add_check("FORBIDDEN_MODIFIED_FALSE", d35.get("FORBIDDEN_MODIFIED", "") == "FALSE", d35.get("FORBIDDEN_MODIFIED", ""))

        if validation_fail_count:
            status = STATUS_FAIL
        else:
            status = STATUS_OK if missing_optional == 0 else STATUS_WARN

        validation_rows = validations

    if missing_critical:
        validation_rows = [{
            "check_name": "CRITICAL_SOURCE_MISSING",
            "status": "FAIL",
            "expected": "",
            "actual": "",
            "detail": str(missing_critical),
        }]
        validation_fail_count = missing_critical

    snapshot_manifest_rows = []
    for rel in CRITICAL_SOURCES + OPTIONAL_SOURCES:
        src = root / rel
        if src.exists():
            snapshot_manifest_rows.append({
                "source_path": rel.replace("\\", "/"),
                "snapshot_path": rel.replace("\\", "/"),
                "kind": "critical" if rel in CRITICAL_SOURCES else "optional",
                "exists": "TRUE",
                "size_bytes": src.stat().st_size,
                "modified_time": datetime.fromtimestamp(src.stat().st_mtime).replace(microsecond=0).isoformat(),
                "sha256": sha256_file(src),
            })

    manifest_path = snapshot / "MANIFEST.csv"
    validation_path = snapshot / "VALIDATION.csv"
    readme_path = snapshot / "README_V18_35H_318_ALIGNED_BASELINE.md"
    restore_path = snapshot / "RESTORE_V18_35H.ps1"
    write_csv(manifest_path, snapshot_manifest_rows, ["source_path", "snapshot_path", "kind", "exists", "size_bytes", "modified_time", "sha256"])
    write_csv(validation_path, validation_rows, ["check_name", "status", "expected", "actual", "detail"])
    write_text(readme_path, f"""# V18.35H 318 Aligned Stable Snapshot

This snapshot captures the stabilized 318-aligned universe/candidate/freeze baseline after V18.35A-G.
It is intended as a read-only restore point before V18.36A paper trading / forward attribution work.

- RUN_ID: {run_id}
- SNAPSHOT_PATH: {snapshot.as_posix()}
- RESTORE_SCRIPT: RESTORE_V18_35H.ps1
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE

Do not edit the archived contents in place. Use the restore script if a workspace rollback is required.
""")
    write_text(restore_path, render_restore_script())

    summary = {
        "status": status,
        "run_id": run_id,
        "generated_at": now.isoformat(),
        "snapshot_path": snapshot.as_posix(),
        "total_universe_count": len(universe_set),
        "current_full_candidate_count": len(full_set),
        "current_ranked_candidate_count": len(ranked_set),
        "current_top_candidate_count": len(top_set),
        "latest_signal_freeze_count": len(latest_freeze_set),
        "rank_eligible_count": norm(d35.get("RANK_ELIGIBLE_COUNT", "")) or "",
        "rank_ineligible_count": norm(d35.get("RANK_INELIGIBLE_COUNT", "")) or "",
        "remaining_uncomputed_count": norm(e35.get("STILL_UNCOMPUTED_AFTER_BACKFILL_COUNT", "")) or "",
        "new_recomputed_not_in_freeze_count": norm(e35.get("NEW_RECOMPUTED_NOT_IN_FREEZE_COUNT", "")) or "",
        "duplicate_universe_ticker_count": duplicate_count(total_universe_rows, ["ticker"]),
        "duplicate_candidate_ticker_count": duplicate_count(current_full_rows, ["ticker"]),
        "duplicate_latest_signal_date_ticker_count": duplicate_count(latest_freeze_rows, ["signal_date", "ticker"]),
        "copied_file_count": len(snapshot_manifest_rows),
        "missing_optional_count": missing_optional,
        "missing_critical_count": missing_critical,
        "validation_fail_count": validation_fail_count if "validation_fail_count" in locals() else missing_critical,
        "report": OUT_REPORT,
        "current_report": OUT_CURRENT,
        "summary_csv": OUT_SUMMARY,
        "manifest": "MANIFEST.csv",
        "validation_csv": "VALIDATION.csv",
        "restore_script": "RESTORE_V18_35H.ps1",
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "forbidden_modified": FORBIDDEN_MODIFIED,
    }

    write_csv(root / OUT_SUMMARY, [summary], list(summary.keys()))
    report = render_report(summary, validation_rows, snapshot.as_posix(), restore_path.as_posix())
    write_text(root / OUT_REPORT, report)
    write_text(root / OUT_CURRENT, report)

    read_first = [
        f"STATUS: {summary['status']}",
        f"RUN_ID: {summary['run_id']}",
        f"SNAPSHOT_PATH: {summary['snapshot_path']}",
        f"TOTAL_UNIVERSE_COUNT: {summary['total_universe_count']}",
        f"CURRENT_FULL_CANDIDATE_COUNT: {summary['current_full_candidate_count']}",
        f"CURRENT_RANKED_CANDIDATE_COUNT: {summary['current_ranked_candidate_count']}",
        f"CURRENT_TOP_CANDIDATE_COUNT: {summary['current_top_candidate_count']}",
        f"LATEST_SIGNAL_FREEZE_COUNT: {summary['latest_signal_freeze_count']}",
        f"RANK_ELIGIBLE_COUNT: {summary['rank_eligible_count']}",
        f"RANK_INELIGIBLE_COUNT: {summary['rank_ineligible_count']}",
        f"REMAINING_UNCOMPUTED_COUNT: {summary['remaining_uncomputed_count']}",
        f"NEW_RECOMPUTED_NOT_IN_FREEZE_COUNT: {summary['new_recomputed_not_in_freeze_count']}",
        f"DUPLICATE_UNIVERSE_TICKER_COUNT: {summary['duplicate_universe_ticker_count']}",
        f"DUPLICATE_CANDIDATE_TICKER_COUNT: {summary['duplicate_candidate_ticker_count']}",
        f"DUPLICATE_LATEST_SIGNAL_DATE_TICKER_COUNT: {summary['duplicate_latest_signal_date_ticker_count']}",
        f"COPIED_FILE_COUNT: {summary['copied_file_count']}",
        f"MISSING_OPTIONAL_COUNT: {summary['missing_optional_count']}",
        f"MISSING_CRITICAL_COUNT: {summary['missing_critical_count']}",
        f"VALIDATION_FAIL_COUNT: {summary['validation_fail_count']}",
        f"REPORT: {OUT_REPORT}",
        f"CURRENT_REPORT: {OUT_CURRENT}",
        f"SUMMARY_CSV: {OUT_SUMMARY}",
        f"MANIFEST: {(snapshot / 'MANIFEST.csv').as_posix()}",
        f"VALIDATION_CSV: {(snapshot / 'VALIDATION.csv').as_posix()}",
        f"RESTORE_SCRIPT: {(snapshot / 'RESTORE_V18_35H.ps1').as_posix()}",
        "OFFICIAL_DECISION_IMPACT: NONE",
        "AUTO_TRADE: DISABLED",
        "AUTO_SELL: DISABLED",
        "FORBIDDEN_MODIFIED: FALSE",
        "",
    ]
    write_text(root / OUT_READ_FIRST, "\n".join(read_first))

    for key in ["status", "run_id", "snapshot_path", "copied_file_count", "missing_optional_count", "missing_critical_count", "validation_fail_count"]:
        print(f"{key.upper()}: {summary[key]}")
    print(f"REPORT: {root / OUT_CURRENT}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if str(summary["status"]).startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
