#!/usr/bin/env python
"""V18.37D stable snapshot for the LEAN-inspired research stack baseline.

This is a snapshot-only safety step. It reads the current V18.37A/B/C baseline
artifacts, copies the selected baseline files into a timestamped archive,
writes metadata outputs, and validates that no operational ledgers changed.
It does not modify official ranking, factor weights, candidate aliases, signal
freeze state, paper-trading state, account state, broker/API logic, or trading
execution logic.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable


STATUS_OK = "OK"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"

AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FACTOR_WEIGHTS_MODIFIED = "FALSE"
OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED = "FALSE"
PAPER_TRADING_LEDGER_MODIFIED = "FALSE"
SHADOW_PORTFOLIO_LEDGER_MODIFIED = "FALSE"
FORBIDDEN_MODIFIED = "FALSE"

ROOT_RELATIVE_SOURCES = [
    "scripts/v18/v18_37A_lean_inspired_strategy_motif_lab.py",
    "scripts/v18/run_v18_37A_lean_inspired_strategy_motif_lab.ps1",
    "scripts/v18/v18_37B_shadow_portfolio_construction_comparison.py",
    "scripts/v18/run_v18_37B_shadow_portfolio_construction_comparison.ps1",
    "scripts/v18/v18_37C_shadow_portfolio_daily_snapshot_forward_bridge.py",
    "scripts/v18/run_v18_37C_shadow_portfolio_daily_snapshot_forward_bridge.ps1",
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "outputs/v18/ops/V18_37A_LEAN_INSPIRED_STRATEGY_MOTIF_SUMMARY.csv",
    "outputs/v18/ops/V18_37A_STRATEGY_MOTIF_REGISTRY.csv",
    "outputs/v18/ops/V18_37A_STRATEGY_MOTIF_TO_FACTOR_MAP.csv",
    "outputs/v18/ops/V18_37A_SHADOW_STRATEGY_CANDIDATES.csv",
    "outputs/v18/ops/V18_37A_READ_FIRST.txt",
    "outputs/v18/read_center/V18_37A_LEAN_INSPIRED_STRATEGY_MOTIF_LAB_REPORT.md",
    "outputs/v18/read_center/V18_CURRENT_LEAN_INSPIRED_STRATEGY_LAB.md",
    "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_CONSTRUCTION_SUMMARY.csv",
    "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_REGISTRY.csv",
    "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_HOLDINGS.csv",
    "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_WEIGHTS.csv",
    "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_DIAGNOSTICS.csv",
    "outputs/v18/ops/V18_37B_READ_FIRST.txt",
    "outputs/v18/read_center/V18_37B_SHADOW_PORTFOLIO_CONSTRUCTION_REPORT.md",
    "outputs/v18/read_center/V18_CURRENT_SHADOW_PORTFOLIO_CONSTRUCTION.md",
    "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_SUMMARY.csv",
    "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_DETAIL.csv",
    "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_FORWARD_READINESS.csv",
    "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_ATTRIBUTION_PREVIEW.csv",
    "outputs/v18/ops/V18_37C_READ_FIRST.txt",
    "outputs/v18/read_center/V18_37C_SHADOW_PORTFOLIO_FORWARD_BRIDGE_REPORT.md",
    "outputs/v18/read_center/V18_CURRENT_SHADOW_PORTFOLIO_FORWARD_BRIDGE.md",
    "state/v18/shadow_portfolios/V18_SHADOW_PORTFOLIO_DAILY_SNAPSHOT_LEDGER.csv",
    "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
    "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
    "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
    "outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md",
    "outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md",
    "outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_RUNBOOK_CN.md",
    "outputs/v18/read_center/V18_CURRENT_DAILY_COMMAND_CENTER.md",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST.md",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST_WITH_TECHNICAL.md",
    "outputs/v18/read_center/V18_CURRENT_SHADOW_RESEARCH_DAILY.md",
    "outputs/v18/read_center/V18_CURRENT_SHADOW_RESEARCH_DAILY_READ_FIRST.txt",
]

CRITICAL_SOURCES = {
    "scripts/v18/v18_37A_lean_inspired_strategy_motif_lab.py",
    "scripts/v18/run_v18_37A_lean_inspired_strategy_motif_lab.ps1",
    "scripts/v18/v18_37B_shadow_portfolio_construction_comparison.py",
    "scripts/v18/run_v18_37B_shadow_portfolio_construction_comparison.ps1",
    "scripts/v18/v18_37C_shadow_portfolio_daily_snapshot_forward_bridge.py",
    "scripts/v18/run_v18_37C_shadow_portfolio_daily_snapshot_forward_bridge.ps1",
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "outputs/v18/ops/V18_37A_LEAN_INSPIRED_STRATEGY_MOTIF_SUMMARY.csv",
    "outputs/v18/ops/V18_37A_STRATEGY_MOTIF_REGISTRY.csv",
    "outputs/v18/ops/V18_37A_STRATEGY_MOTIF_TO_FACTOR_MAP.csv",
    "outputs/v18/ops/V18_37A_SHADOW_STRATEGY_CANDIDATES.csv",
    "outputs/v18/ops/V18_37A_READ_FIRST.txt",
    "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_CONSTRUCTION_SUMMARY.csv",
    "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_REGISTRY.csv",
    "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_HOLDINGS.csv",
    "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_WEIGHTS.csv",
    "outputs/v18/ops/V18_37B_SHADOW_PORTFOLIO_DIAGNOSTICS.csv",
    "outputs/v18/ops/V18_37B_READ_FIRST.txt",
    "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_SUMMARY.csv",
    "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_DETAIL.csv",
    "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_FORWARD_READINESS.csv",
    "outputs/v18/ops/V18_37C_SHADOW_PORTFOLIO_ATTRIBUTION_PREVIEW.csv",
    "outputs/v18/ops/V18_37C_READ_FIRST.txt",
    "state/v18/shadow_portfolios/V18_SHADOW_PORTFOLIO_DAILY_SNAPSHOT_LEDGER.csv",
    "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
    "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
    "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
    "outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md",
    "outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md",
    "outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_RUNBOOK_CN.md",
    "outputs/v18/read_center/V18_CURRENT_DAILY_COMMAND_CENTER.md",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST.md",
    "outputs/v18/read_center/V18_CURRENT_READ_FIRST_WITH_TECHNICAL.md",
}

OPTIONAL_SOURCES = [rel for rel in ROOT_RELATIVE_SOURCES if rel not in CRITICAL_SOURCES]

READ_FIRST_REQUIRED_MARKERS = {
    "V18_37A_READ_FIRST.txt": {
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "FORBIDDEN_MODIFIED": "FALSE",
    },
    "V18_37B_READ_FIRST.txt": {
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "FORBIDDEN_MODIFIED": "FALSE",
    },
    "V18_37C_READ_FIRST.txt": {
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED": "FALSE",
        "PAPER_TRADING_LEDGER_MODIFIED": "FALSE",
        "FORBIDDEN_MODIFIED": "FALSE",
    },
}

SUMMARY_PATH = "outputs/v18/ops/V18_37D_STABLE_SNAPSHOT_SUMMARY.csv"
REPORT_PATH = "outputs/v18/read_center/V18_37D_STABLE_SNAPSHOT_REPORT.md"
READ_FIRST_PATH = "outputs/v18/ops/V18_37D_READ_FIRST.txt"
SNAPSHOT_PREFIX = "V18_37D_lean_inspired_research_stack_baseline"
MANIFEST_NAME = "MANIFEST.csv"
VALIDATION_NAME = "VALIDATION.csv"
README_NAME = "README_V18_37D_LEAN_INSPIRED_RESEARCH_STACK_BASELINE.md"
RESTORE_NAME = "RESTORE_V18_37D.ps1"

HASH_FILES = {
    "official_signal_freeze_ledger": "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "paper_trading_ledger": "state/v18/paper_trading/V18_PAPER_TRADING_LEDGER.csv",
    "paper_portfolio_state": "state/v18/paper_trading/V18_PAPER_PORTFOLIO_STATE.csv",
    "shadow_portfolio_ledger": "state/v18/shadow_portfolios/V18_SHADOW_PORTFOLIO_DAILY_SNAPSHOT_LEDGER.csv",
}


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_status(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def latest_group_count(rows: list[dict[str, str]], key_field: str) -> tuple[str, int]:
    grouped: dict[str, int] = {}
    for row in rows:
        key = str(row.get(key_field, "")).strip()
        if key:
            grouped[key] = grouped.get(key, 0) + 1
    if not grouped:
        return "", 0
    latest_key = sorted(grouped)[-1]
    return latest_key, grouped[latest_key]


def first_non_empty(row: dict[str, str], fields: Iterable[str]) -> str:
    for field in fields:
        value = str(row.get(field, "")).strip()
        if value:
            return value
    return ""


def unique_ticker_count(rows: list[dict[str, str]]) -> int:
    tickers = {
        str(row.get("ticker", "")).strip().upper()
        for row in rows
        if str(row.get("ticker", "")).strip()
    }
    return len(tickers)


def snapshot_file_path(snapshot_root: Path, relative_path: str) -> Path:
    return snapshot_root / Path(relative_path)


def copy_snapshot_file(root: Path, snapshot_root: Path, relative_path: str, kind: str) -> dict[str, object] | None:
    source = root / relative_path
    if not source.exists():
        return None
    target = snapshot_file_path(snapshot_root, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    stat = source.stat()
    return {
        "source_path": relative_path.replace("\\", "/"),
        "snapshot_path": target.relative_to(snapshot_root).as_posix(),
        "kind": kind,
        "exists": "TRUE",
        "size_bytes": stat.st_size,
        "modified_time": datetime.fromtimestamp(stat.st_mtime).replace(microsecond=0).isoformat(),
        "sha256": sha256_file(source),
    }


def manifest_rows(root: Path, snapshot_root: Path) -> tuple[list[dict[str, object]], int, int]:
    rows: list[dict[str, object]] = []
    missing_optional = 0
    missing_critical = 0
    for relative_path in ROOT_RELATIVE_SOURCES:
        kind = "critical" if relative_path in CRITICAL_SOURCES else "optional"
        copied = copy_snapshot_file(root, snapshot_root, relative_path, kind)
        if copied is None:
            if kind == "critical":
                missing_critical += 1
            else:
                missing_optional += 1
            continue
        rows.append(copied)
    return rows, missing_optional, missing_critical


def build_validation(
    root: Path,
    snapshot_root: Path,
    hashes_before: dict[str, str],
    hashes_after: dict[str, str],
    current_full_count: int,
    latest_freeze_count: int,
    shadow_ledger_exists: bool,
    shadow_portfolio_count: int,
    shadow_snapshot_rows: int,
    entry_price_missing_count: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    def add_check(name: str, ok: bool, expected: object, actual: object, detail: str) -> None:
        rows.append(
            {
                "check_name": name,
                "status": "PASS" if ok else "FAIL",
                "expected": expected,
                "actual": actual,
                "detail": detail,
            }
        )

    for filename, markers in READ_FIRST_REQUIRED_MARKERS.items():
        path = root / "outputs/v18/ops" / filename
        status = read_status(path)
        ok = path.exists() and all(status.get(key, "") == value for key, value in markers.items())
        add_check(
            f"{filename.replace('.txt', '')}_EXISTS_AND_MARKERS",
            ok,
            ";".join([f"{k}={v}" for k, v in markers.items()]),
            ";".join([f"{k}={status.get(k, '')}" for k in markers.keys()]),
            str(path),
        )

    add_check(
        "CURRENT_FULL_CANDIDATE_COUNT_318",
        current_full_count == 318,
        318,
        current_full_count,
        "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
    )
    add_check(
        "LATEST_SIGNAL_FREEZE_COUNT_318",
        latest_freeze_count == 318,
        318,
        latest_freeze_count,
        "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    )
    add_check(
        "SHADOW_PORTFOLIO_LEDGER_EXISTS",
        shadow_ledger_exists,
        "TRUE",
        "TRUE" if shadow_ledger_exists else "FALSE",
        "state/v18/shadow_portfolios/V18_SHADOW_PORTFOLIO_DAILY_SNAPSHOT_LEDGER.csv",
    )
    add_check(
        "V18_37C_LATEST_SHADOW_PORTFOLIO_COUNT_10",
        shadow_portfolio_count == 10,
        10,
        shadow_portfolio_count,
        "outputs/v18/ops/V18_37C_READ_FIRST.txt or summary csv",
    )
    add_check(
        "V18_37C_LATEST_SHADOW_SNAPSHOT_ROWS_744",
        shadow_snapshot_rows == 744,
        744,
        shadow_snapshot_rows,
        "outputs/v18/ops/V18_37C_READ_FIRST.txt or summary csv",
    )
    add_check(
        "V18_37C_ENTRY_PRICE_MISSING_COUNT_0",
        entry_price_missing_count == 0,
        0,
        entry_price_missing_count,
        "outputs/v18/ops/V18_37C_READ_FIRST.txt or summary csv",
    )

    for label, rel_path in HASH_FILES.items():
        before = hashes_before.get(label, "")
        after = hashes_after.get(label, "")
        add_check(
            f"{label.upper()}_HASH_UNCHANGED",
            bool(before) and before == after,
            before or "MISSING",
            after or "MISSING",
            rel_path,
        )

    add_check(
        "RESTORE_SCRIPT_GENERATED",
        (snapshot_root / RESTORE_NAME).exists(),
        "TRUE",
        "TRUE" if (snapshot_root / RESTORE_NAME).exists() else "FALSE",
        str(snapshot_root / RESTORE_NAME),
    )
    add_check(
        "MANIFEST_GENERATED",
        (snapshot_root / MANIFEST_NAME).exists(),
        "TRUE",
        "TRUE" if (snapshot_root / MANIFEST_NAME).exists() else "FALSE",
        str(snapshot_root / MANIFEST_NAME),
    )

    return rows


def render_report(
    status: str,
    run_id: str,
    snapshot_root: Path,
    copied_file_count: int,
    missing_optional_count: int,
    missing_critical_count: int,
    validation_fail_count: int,
    current_full_count: int,
    latest_freeze_count: int,
    shadow_ledger_exists: bool,
    shadow_portfolio_count: int,
    shadow_snapshot_rows: int,
    entry_price_missing_count: int,
    hashes: dict[str, str],
    validation_rows: list[dict[str, object]],
) -> str:
    lines = [
        "# V18.37D Stable Snapshot / LEAN-Inspired Research Stack Baseline",
        "",
        f"- STATUS: `{status}`",
        f"- RUN_ID: `{run_id}`",
        f"- MODE: `SNAPSHOT_ONLY`",
        f"- SNAPSHOT_PATH: `{snapshot_root.as_posix()}`",
        f"- COPIED_FILE_COUNT: `{copied_file_count}`",
        f"- MISSING_OPTIONAL_COUNT: `{missing_optional_count}`",
        f"- MISSING_CRITICAL_COUNT: `{missing_critical_count}`",
        f"- VALIDATION_FAIL_COUNT: `{validation_fail_count}`",
        "",
        "## Baseline",
        "- V18.37A strategy motif lab",
        "- V18.37B shadow portfolio construction",
        "- V18.37C shadow portfolio daily snapshot / forward bridge",
        "- 318-aligned universe/candidate/freeze context",
        "- command-center integration flags and ordering",
        "- current read-center reports and READ_FIRST files",
        "",
        "## Counts",
        "| item | value |",
        "| --- | ---: |",
        f"| current full candidates | {current_full_count} |",
        f"| latest signal freeze rows | {latest_freeze_count} |",
        f"| shadow portfolio ledger exists | {str(shadow_ledger_exists).upper()} |",
        f"| latest shadow portfolio count | {shadow_portfolio_count} |",
        f"| latest shadow snapshot rows | {shadow_snapshot_rows} |",
        f"| entry price missing count | {entry_price_missing_count} |",
        "",
        "## Safety Flags",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- FACTOR_WEIGHTS_MODIFIED: FALSE",
        "- OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE",
        "- PAPER_TRADING_LEDGER_MODIFIED: FALSE",
        "- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE",
        "- FORBIDDEN_MODIFIED: FALSE",
        "",
        "## Hashes",
        "| file | sha256 |",
        "| --- | --- |",
        f"| official signal freeze ledger | `{hashes.get('official_signal_freeze_ledger', '')}` |",
        f"| paper trading ledger | `{hashes.get('paper_trading_ledger', '')}` |",
        f"| paper portfolio state | `{hashes.get('paper_portfolio_state', '')}` |",
        f"| shadow portfolio ledger | `{hashes.get('shadow_portfolio_ledger', '')}` |",
        "",
        "## Validation",
        "| check | status | expected | actual | detail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in validation_rows:
        lines.append(
            "| {check} | {status} | {expected} | {actual} | {detail} |".format(
                check=str(row.get("check_name", "")).replace("|", "/"),
                status=str(row.get("status", "")).replace("|", "/"),
                expected=str(row.get("expected", "")).replace("|", "/"),
                actual=str(row.get("actual", "")).replace("|", "/"),
                detail=str(row.get("detail", "")).replace("|", "/"),
            )
        )
    lines += [
        "",
        "## Archive",
        f"- Manifest: `{(snapshot_root / MANIFEST_NAME).as_posix()}`",
        f"- Validation: `{(snapshot_root / VALIDATION_NAME).as_posix()}`",
        f"- README: `{(snapshot_root / README_NAME).as_posix()}`",
        f"- Restore: `{(snapshot_root / RESTORE_NAME).as_posix()}`",
        "",
        "## Notes",
        "- This snapshot is metadata-only. It preserves the baseline by copying source artifacts into a timestamped archive and recording validation output.",
        "- It does not alter official ranking, factor weights, candidate aliases, signal freeze state, paper-trading state, account state, broker/API logic, or trading execution behavior.",
        "",
    ]
    return "\n".join(lines)


def render_readme(snapshot_root: Path, run_id: str, copied_file_count: int, missing_optional_count: int, missing_critical_count: int) -> str:
    return "\n".join(
        [
            "# V18.37D LEAN-Inspired Research Stack Baseline",
            "",
            "This archive is a stable snapshot of the completed V18.37A/B/C research stack.",
            "It is snapshot-only and exists to preserve the current baseline without changing operational behavior.",
            "",
            f"- RUN_ID: {run_id}",
            f"- SNAPSHOT_PATH: {snapshot_root.as_posix()}",
            f"- COPIED_FILE_COUNT: {copied_file_count}",
            f"- MISSING_OPTIONAL_COUNT: {missing_optional_count}",
            f"- MISSING_CRITICAL_COUNT: {missing_critical_count}",
            "- AUTO_TRADE: DISABLED",
            "- AUTO_SELL: DISABLED",
            "- OFFICIAL_DECISION_IMPACT: NONE",
            "- FACTOR_WEIGHTS_MODIFIED: FALSE",
            "- OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE",
            "- PAPER_TRADING_LEDGER_MODIFIED: FALSE",
            "- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE",
            "- FORBIDDEN_MODIFIED: FALSE",
            "",
            "Use RESTORE_V18_37D.ps1 from this archive root if the snapshot ever needs to be restored into the workspace.",
            "Do not execute the restore script unless rollback is explicitly required.",
            "",
        ]
    )


def render_restore_script() -> str:
    return """[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$Manifest = Join-Path $PSScriptRoot "MANIFEST.csv"

Write-Host "=== RESTORE V18.37D STABLE SNAPSHOT START ==="
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

Write-Host "=== RESTORE V18.37D STABLE SNAPSHOT DONE ==="
Write-Host "FILES_RESTORED: $($rows.Count)"
"""


def parse_v37c_snapshot(read_first_path: Path, summary_path: Path) -> tuple[int, int, int]:
    total_portfolio_count = 0
    total_snapshot_rows = 0
    entry_price_missing_count = 0

    if read_first_path.exists():
        status = read_status(read_first_path)
        total_portfolio_count = int(status.get("TOTAL_PORTFOLIO_COUNT", "0") or 0)
        total_snapshot_rows = int(status.get("TOTAL_SNAPSHOT_ROWS", "0") or 0)
        entry_price_missing_count = int(status.get("ENTRY_PRICE_MISSING_COUNT", "0") or 0)
        return total_portfolio_count, total_snapshot_rows, entry_price_missing_count

    rows = read_csv(summary_path)
    if rows:
        row = rows[0]
        total_portfolio_count = int(str(row.get("total_portfolio_count", "0") or "0"))
        total_snapshot_rows = int(str(row.get("total_snapshot_rows", "0") or "0"))
        entry_price_missing_count = int(str(row.get("entry_price_missing_count", "0") or "0"))
    return total_portfolio_count, total_snapshot_rows, entry_price_missing_count


def run(root: Path) -> int:
    ops_dir = root / "outputs/v18/ops"
    read_center_dir = root / "outputs/v18/read_center"
    snapshot_stamp = stamp()
    run_id = f"V18_37D_{snapshot_stamp}"
    generated_at = now_iso()
    snapshot_root = root / "archive/stable" / f"{SNAPSHOT_PREFIX}_{snapshot_stamp}"
    snapshot_root.mkdir(parents=True, exist_ok=True)

    hashes_before = {
        label: sha256_file(root / rel)
        for label, rel in HASH_FILES.items()
        if (root / rel).exists()
    }

    current_full_rows = read_csv(root / "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv")
    freeze_rows = read_csv(root / "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv")
    _, latest_freeze_count = latest_group_count(freeze_rows, "signal_date")
    shadow_ledger_path = root / "state/v18/shadow_portfolios/V18_SHADOW_PORTFOLIO_DAILY_SNAPSHOT_LEDGER.csv"
    shadow_ledger_exists = shadow_ledger_path.exists()
    v37c_portfolios, v37c_snapshot_rows, v37c_missing_entry_count = parse_v37c_snapshot(
        ops_dir / "V18_37C_READ_FIRST.txt",
        ops_dir / "V18_37C_SHADOW_PORTFOLIO_SNAPSHOT_SUMMARY.csv",
    )

    manifest_rows_data, missing_optional_count, missing_critical_count = manifest_rows(root, snapshot_root)
    copied_file_count = len(manifest_rows_data)

    manifest_path = snapshot_root / MANIFEST_NAME
    validation_path = snapshot_root / VALIDATION_NAME
    readme_path = snapshot_root / README_NAME
    restore_path = snapshot_root / RESTORE_NAME

    write_csv(manifest_path, manifest_rows_data, ["source_path", "snapshot_path", "kind", "exists", "size_bytes", "modified_time", "sha256"])
    write_text(restore_path, render_restore_script())
    write_text(readme_path, render_readme(snapshot_root, run_id, copied_file_count, missing_optional_count, missing_critical_count))

    state_hashes_after = {
        label: sha256_file(root / rel)
        for label, rel in HASH_FILES.items()
        if (root / rel).exists()
    }

    validation_rows = build_validation(
        root=root,
        snapshot_root=snapshot_root,
        hashes_before=hashes_before,
        hashes_after=state_hashes_after,
        current_full_count=unique_ticker_count(current_full_rows),
        latest_freeze_count=latest_freeze_count,
        shadow_ledger_exists=shadow_ledger_exists,
        shadow_portfolio_count=v37c_portfolios,
        shadow_snapshot_rows=v37c_snapshot_rows,
        entry_price_missing_count=v37c_missing_entry_count,
    )
    validation_fail_count = sum(1 for row in validation_rows if str(row.get("status", "")) == "FAIL")

    if missing_critical_count > 0 or validation_fail_count > 0:
        status = STATUS_FAIL
    elif missing_optional_count > 0:
        status = STATUS_WARN
    else:
        status = STATUS_OK

    write_csv(validation_path, validation_rows, ["check_name", "status", "expected", "actual", "detail"])

    hashes_final = {
        label: sha256_file(root / rel)
        for label, rel in HASH_FILES.items()
        if (root / rel).exists()
    }

    validation_rows = build_validation(
        root=root,
        snapshot_root=snapshot_root,
        hashes_before=hashes_before,
        hashes_after=hashes_final,
        current_full_count=unique_ticker_count(current_full_rows),
        latest_freeze_count=latest_freeze_count,
        shadow_ledger_exists=shadow_ledger_exists,
        shadow_portfolio_count=v37c_portfolios,
        shadow_snapshot_rows=v37c_snapshot_rows,
        entry_price_missing_count=v37c_missing_entry_count,
    )
    validation_fail_count = sum(1 for row in validation_rows if str(row.get("status", "")) == "FAIL")

    write_csv(validation_path, validation_rows, ["check_name", "status", "expected", "actual", "detail"])

    summary_rows = [
        {
            "status": status,
            "mode": "SNAPSHOT_ONLY",
            "run_id": run_id,
            "generated_at": generated_at,
            "snapshot_path": snapshot_root.as_posix(),
            "copied_file_count": copied_file_count,
            "missing_optional_count": missing_optional_count,
            "missing_critical_count": missing_critical_count,
            "validation_fail_count": validation_fail_count,
            "current_full_candidate_count": unique_ticker_count(current_full_rows),
            "latest_signal_freeze_count": latest_freeze_count,
            "shadow_portfolio_ledger_exists": "TRUE" if shadow_ledger_exists else "FALSE",
            "latest_shadow_portfolio_count": v37c_portfolios,
            "latest_shadow_snapshot_rows": v37c_snapshot_rows,
            "entry_price_missing_count": v37c_missing_entry_count,
            "auto_trade": AUTO_TRADE,
            "auto_sell": AUTO_SELL,
            "official_decision_impact": OFFICIAL_DECISION_IMPACT,
            "factor_weights_modified": FACTOR_WEIGHTS_MODIFIED,
            "official_signal_freeze_ledger_modified": OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED,
            "paper_trading_ledger_modified": PAPER_TRADING_LEDGER_MODIFIED,
            "shadow_portfolio_ledger_modified": SHADOW_PORTFOLIO_LEDGER_MODIFIED,
            "forbidden_modified": FORBIDDEN_MODIFIED,
            "official_signal_freeze_ledger_sha256": hashes_final.get("official_signal_freeze_ledger", ""),
            "paper_trading_ledger_sha256": hashes_final.get("paper_trading_ledger", ""),
            "paper_portfolio_state_sha256": hashes_final.get("paper_portfolio_state", ""),
            "shadow_portfolio_ledger_sha256": hashes_final.get("shadow_portfolio_ledger", ""),
            "manifest_path": manifest_path.as_posix(),
            "validation_path": validation_path.as_posix(),
            "readme_path": readme_path.as_posix(),
            "restore_script_path": restore_path.as_posix(),
        }
    ]
    summary_fields = list(summary_rows[0].keys())
    write_csv(root / SUMMARY_PATH, summary_rows, summary_fields)

    report = render_report(
        status=status,
        run_id=summary_rows[0]["run_id"],
        snapshot_root=snapshot_root,
        copied_file_count=copied_file_count,
        missing_optional_count=missing_optional_count,
        missing_critical_count=missing_critical_count,
        validation_fail_count=validation_fail_count,
        current_full_count=summary_rows[0]["current_full_candidate_count"],
        latest_freeze_count=latest_freeze_count,
        shadow_ledger_exists=shadow_ledger_exists,
        shadow_portfolio_count=v37c_portfolios,
        shadow_snapshot_rows=v37c_snapshot_rows,
        entry_price_missing_count=v37c_missing_entry_count,
        hashes=hashes_final,
        validation_rows=validation_rows,
    )
    write_text(root / REPORT_PATH, report)

    read_first_lines = [
        f"STATUS: {status}",
        "MODE: SNAPSHOT_ONLY",
        f"RUN_ID: {run_id}",
        f"GENERATED_AT: {generated_at}",
        f"SNAPSHOT_PATH: {snapshot_root.as_posix()}",
        f"COPIED_FILE_COUNT: {copied_file_count}",
        f"MISSING_OPTIONAL_COUNT: {missing_optional_count}",
        f"MISSING_CRITICAL_COUNT: {missing_critical_count}",
        f"VALIDATION_FAIL_COUNT: {validation_fail_count}",
        f"CURRENT_FULL_CANDIDATE_COUNT: {summary_rows[0]['current_full_candidate_count']}",
        f"LATEST_SIGNAL_FREEZE_COUNT: {latest_freeze_count}",
        f"SHADOW_PORTFOLIO_LEDGER_EXISTS: {'TRUE' if shadow_ledger_exists else 'FALSE'}",
        f"LATEST_SHADOW_PORTFOLIO_COUNT: {v37c_portfolios}",
        f"LATEST_SHADOW_SNAPSHOT_ROWS: {v37c_snapshot_rows}",
        f"ENTRY_PRICE_MISSING_COUNT: {v37c_missing_entry_count}",
        f"AUTO_TRADE: {AUTO_TRADE}",
        f"AUTO_SELL: {AUTO_SELL}",
        f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"FACTOR_WEIGHTS_MODIFIED: {FACTOR_WEIGHTS_MODIFIED}",
        f"OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED: {OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED}",
        f"PAPER_TRADING_LEDGER_MODIFIED: {PAPER_TRADING_LEDGER_MODIFIED}",
        f"SHADOW_PORTFOLIO_LEDGER_MODIFIED: {SHADOW_PORTFOLIO_LEDGER_MODIFIED}",
        f"FORBIDDEN_MODIFIED: {FORBIDDEN_MODIFIED}",
        f"OFFICIAL_SIGNAL_FREEZE_LEDGER_SHA256: {hashes_final.get('official_signal_freeze_ledger', '')}",
        f"PAPER_TRADING_LEDGER_SHA256: {hashes_final.get('paper_trading_ledger', '')}",
        f"PAPER_PORTFOLIO_STATE_SHA256: {hashes_final.get('paper_portfolio_state', '')}",
        f"SHADOW_PORTFOLIO_LEDGER_SHA256: {hashes_final.get('shadow_portfolio_ledger', '')}",
        f"MANIFEST_PATH: {manifest_path.as_posix()}",
        f"VALIDATION_PATH: {validation_path.as_posix()}",
        f"REPORT_PATH: {(root / REPORT_PATH).as_posix()}",
        "",
    ]
    write_text(root / READ_FIRST_PATH, "\n".join(read_first_lines))
    print("\n".join(read_first_lines), end="")

    return 1 if status == STATUS_FAIL else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.37D stable snapshot for the LEAN-inspired research stack baseline")
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
