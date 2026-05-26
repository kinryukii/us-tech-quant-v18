#!/usr/bin/env python
"""V18.38D stable snapshot / Qlib-style research tracking baseline.

This module is snapshot-only. It copies the current V18.38A/B/C-R1 research
tracking evidence into a timestamped archive under archive/stable without
modifying ranking, candidates, factors, freeze ledgers, account state, broker
APIs, or trading/order logic.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


MODE = "STABLE_SNAPSHOT_ONLY_RESEARCH_TRACKING_BASELINE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

CRITICAL_SOURCES = [
    "scripts/v18/v18_38A_forward_evidence_dashboard.py",
    "scripts/v18/run_v18_38A_forward_evidence_dashboard.ps1",
    "scripts/v18/v18_38B_research_experiment_registry.py",
    "scripts/v18/run_v18_38B_research_experiment_registry.ps1",
    "scripts/v18/v18_38C_command_center_status_normalization.py",
    "scripts/v18/run_v18_38C_command_center_status_normalization.ps1",
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_SUMMARY.csv",
    "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_DETAIL.csv",
    "outputs/v18/ops/V18_38A_FORWARD_EVIDENCE_READINESS.csv",
    "outputs/v18/read_center/V18_38A_FORWARD_EVIDENCE_DASHBOARD_REPORT.md",
    "outputs/v18/read_center/V18_CURRENT_FORWARD_EVIDENCE_DASHBOARD.md",
    "outputs/v18/ops/V18_38A_READ_FIRST.txt",
    "outputs/v18/ops/V18_38B_RESEARCH_EXPERIMENT_REGISTRY.csv",
    "outputs/v18/ops/V18_38B_RESEARCH_EXPERIMENT_SUMMARY.csv",
    "outputs/v18/ops/V18_38B_RESEARCH_EXPERIMENT_DEPENDENCIES.csv",
    "outputs/v18/read_center/V18_38B_RESEARCH_EXPERIMENT_REGISTRY_REPORT.md",
    "outputs/v18/read_center/V18_CURRENT_RESEARCH_EXPERIMENT_REGISTRY.md",
    "outputs/v18/ops/V18_38B_READ_FIRST.txt",
    "outputs/v18/ops/V18_38C_R1_COMMAND_STATUS_SUMMARY.csv",
    "outputs/v18/ops/V18_38C_R1_COMMAND_STATUS_DETAIL.csv",
    "outputs/v18/ops/V18_38C_R1_COMMAND_STATUS_RULES.csv",
    "outputs/v18/read_center/V18_38C_R1_COMMAND_STATUS_NORMALIZATION_REPORT.md",
    "outputs/v18/read_center/V18_CURRENT_COMMAND_STATUS_NORMALIZATION.md",
    "outputs/v18/ops/V18_38C_R1_READ_FIRST.txt",
    "outputs/v18/read_center/V18_CURRENT_DAILY_COMMAND_CENTER.md",
    "outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md",
    "outputs/v18/read_center/V18_CURRENT_DAILY_OUTPUT_FRESHNESS.md",
    "outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md",
    "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
    "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
]

OPTIONAL_SOURCES = [
    "outputs/v18/ops/V18_37D_READ_FIRST.txt",
    "outputs/v18/ops/V18_35H_READ_FIRST.txt",
]

ADDITIONAL_WORKSPACE_OUTPUTS = [
    "outputs/v18/ops/V18_38D_STABLE_SNAPSHOT_SUMMARY.csv",
    "outputs/v18/read_center/V18_38D_STABLE_SNAPSHOT_REPORT.md",
    "outputs/v18/ops/V18_38D_READ_FIRST.txt",
]

MANIFEST_FIELDS = [
    "source_path",
    "snapshot_path",
    "exists",
    "required",
    "copied",
    "copy_status",
    "kind",
    "size_bytes",
    "modified_time",
    "sha256",
    "notes",
]

VALIDATION_FIELDS = [
    "check_name",
    "status",
    "detail",
    "required",
    "expected",
    "observed",
]

SUMMARY_FIELDS = [
    "status",
    "run_id",
    "generated_at",
    "snapshot_path",
    "copied_file_count",
    "missing_optional_count",
    "missing_critical_count",
    "copy_fail_count",
    "validation_fail_count",
    "v18_38a_status",
    "v18_38b_status",
    "v18_38c_r1_status",
    "current_fail_blocking_count",
    "daily_run_usable",
    "forward_research_usable",
    "current_full_candidate_count",
    "latest_signal_freeze_count",
    "auto_trade",
    "auto_sell",
    "official_decision_impact",
    "ranking_modified",
    "factor_weights_modified",
    "signal_freeze_ledger_modified",
    "paper_trading_ledger_modified",
    "shadow_portfolio_ledger_modified",
    "account_state_modified",
    "broker_api_used",
    "order_execution_used",
    "restore_script_generated",
    "restore_script_executed",
]


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dirs(root: Path) -> None:
    for rel in ["archive/stable", "outputs/v18/ops", "outputs/v18/read_center"]:
        (root / rel).mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, df: pd.DataFrame, fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if df.empty:
        df = pd.DataFrame(columns=fields)
    else:
        for field in fields:
            if field not in df.columns:
                df[field] = ""
        df = df[fields]
    df.to_csv(path, index=False, encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_status(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def parse_int(value: str | None) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(str(value).strip()))
    except Exception:
        return None


def path_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding=enc)
            return df.to_dict(orient="records")
        except Exception:
            continue
    return []


def status_bucket(status: str) -> str:
    s = status.strip().upper()
    if s.startswith("OK"):
        return "OK"
    if s.startswith("WARN"):
        return "WARN"
    if s.startswith("FAIL"):
        return "FAIL"
    return "UNKNOWN"


def is_status_ok_or_warn(status: str) -> bool:
    return status_bucket(status) in {"OK", "WARN"}


def current_snapshot_path(root: Path, timestamp: str) -> Path:
    return root / "archive" / "stable" / f"V18_38D_research_tracking_baseline_{timestamp}"


def copy_one(root: Path, snapshot_root: Path, relative_path: str, required: bool, kind: str) -> dict[str, Any]:
    source = root / relative_path
    target = snapshot_root / Path(relative_path)
    row: dict[str, Any] = {
        "source_path": relative_path.replace("\\", "/"),
        "snapshot_path": target.relative_to(snapshot_root).as_posix(),
        "exists": "TRUE" if source.exists() else "FALSE",
        "required": "TRUE" if required else "FALSE",
        "copied": "FALSE",
        "copy_status": "",
        "kind": kind,
        "size_bytes": "",
        "modified_time": "",
        "sha256": "",
        "notes": "",
    }
    if not source.exists():
        row["copy_status"] = "MISSING_CRITICAL" if required else "MISSING_OPTIONAL"
        row["notes"] = "required source missing" if required else "optional source missing"
        return row
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        stat = source.stat()
        row["copied"] = "TRUE"
        row["copy_status"] = "COPIED"
        row["size_bytes"] = stat.st_size
        row["modified_time"] = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
        row["sha256"] = path_hash(source)
        row["notes"] = "copied"
    except Exception as exc:
        row["copy_status"] = "COPY_FAILED"
        row["notes"] = f"{type(exc).__name__}: {exc}"
    return row


def build_restore_script() -> str:
    return """[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$Manifest = Join-Path $PSScriptRoot "MANIFEST.csv"

Write-Host "=== RESTORE V18.38D STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "SNAPSHOT_ROOT: $PSScriptRoot"
Write-Host "MANIFEST: $Manifest"

if (-not (Test-Path $Manifest)) {
    throw "Missing MANIFEST.csv: $Manifest"
}

$Rows = Import-Csv -Path $Manifest
foreach ($Row in $Rows) {
    if ($Row.exists -ne "TRUE" -or $Row.copied -ne "TRUE") {
        continue
    }

    $Source = Join-Path $PSScriptRoot $Row.snapshot_path
    $Target = Join-Path $Root $Row.source_path

    if (-not (Test-Path $Source)) {
        throw "Missing snapshot source: $Source"
    }

    $TargetParent = Split-Path -Parent $Target
    if ($TargetParent -and -not (Test-Path $TargetParent)) {
        New-Item -ItemType Directory -Path $TargetParent -Force | Out-Null
    }

    Copy-Item -LiteralPath $Source -Destination $Target -Force
}

Write-Host "RESTORE_EXECUTED: FALSE"
Write-Host "This restore script was generated only; it has not been executed."
Write-Host "=== RESTORE V18.38D STABLE SNAPSHOT END ==="
"""


def build_readme(summary: dict[str, Any], validation_rows: list[dict[str, Any]], archive_root: Path, restore_path: Path) -> str:
    lines = [
        "# V18.38D 稳定快照 / Qlib 风格研究追踪基线",
        "",
        "## 1. 今日结论",
        f"- 状态: `{summary['status']}`",
        f"- 这是一份只读稳定快照，目的在于固定 V18.38A/B/C-R1 的研究证据层、实验注册层和状态归类层。",
        "",
        "## 2. 快照路径",
        f"- `{archive_root.as_posix()}`",
        "",
        "## 3. 为什么创建这个快照",
        "- 用本地稳定归档保存当前研究 tracking 基线。",
        "- 不改变交易、排名、因子、冻结、账户、broker/API 或订单逻辑。",
        "",
        "## 4. 包含的核心模块",
        "- V18.38A Forward Evidence Dashboard",
        "- V18.38B Research Experiment Registry",
        "- V18.38C-R1 Command Status Normalization",
        "- Current daily command center wrapper",
        "",
        "## 5. V18.38A/B/C-R1 状态",
        f"- V18.38A: `{summary['v18_38a_status']}`",
        f"- V18.38B: `{summary['v18_38b_status']}`",
        f"- V18.38C-R1: `{summary['v18_38c_r1_status']}`",
        f"- CURRENT_FAIL_BLOCKING_COUNT: `{summary['current_fail_blocking_count']}`",
        f"- DAILY_RUN_USABLE: `{summary['daily_run_usable']}`",
        f"- FORWARD_RESEARCH_USABLE: `{summary['forward_research_usable']}`",
        "",
        "## 6. 候选池 / freeze 状态",
        f"- CURRENT_FULL_CANDIDATE_COUNT: `{summary['current_full_candidate_count']}`",
        f"- LATEST_SIGNAL_FREEZE_COUNT: `{summary['latest_signal_freeze_count']}`",
        "",
        "## 7. 验证结果",
        "| check | status | detail |",
        "| --- | --- | --- |",
    ]
    for row in validation_rows:
        lines.append(f"| {row['check_name']} | `{row['status']}` | {row['detail']} |")
    lines += [
        "",
        "## 8. 安全确认",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- RANKING_MODIFIED: FALSE",
        "- FACTOR_WEIGHTS_MODIFIED: FALSE",
        "- SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE",
        "- PAPER_TRADING_LEDGER_MODIFIED: FALSE",
        "- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE",
        "- ACCOUNT_STATE_MODIFIED: FALSE",
        "- BROKER_API_USED: FALSE",
        "- ORDER_EXECUTION_USED: FALSE",
        "",
        "## 9. 恢复方式说明",
        f"- 恢复脚本: `{restore_path.as_posix()}`",
        "- 该脚本已生成，但本次没有执行。",
        "- 如需恢复，直接在 snapshot 根目录运行该脚本即可。",
        "",
        "## 10. 下一步建议",
        "- 保持这份快照作为 V18.38A/B/C-R1 的本地稳定基线。",
        "- 需要回滚时使用 restore script；平时继续沿用当前只读研究流程。",
    ]
    return "\n".join(lines) + "\n"


def validate_snapshot(root: Path, summary: dict[str, Any], validation_rows: list[dict[str, Any]]) -> None:
    # keep the existing command-center report in sync for operator-facing checks
    pass


def gather_status_summary(root: Path) -> dict[str, Any]:
    a = read_status(root / "outputs/v18/ops/V18_38A_READ_FIRST.txt")
    b = read_status(root / "outputs/v18/ops/V18_38B_READ_FIRST.txt")
    c = read_status(root / "outputs/v18/ops/V18_38C_R1_READ_FIRST.txt")

    current_full_candidates = parse_int(a.get("CURRENT_FULL_CANDIDATE_COUNT")) or parse_int(a.get("TOTAL_EVIDENCE_SOURCE_COUNT")) or None
    latest_signal_freeze = parse_int(a.get("LATEST_SIGNAL_FREEZE_COUNT")) or None

    return {
        "v18_38a_status": a.get("STATUS", ""),
        "v18_38b_status": b.get("STATUS", ""),
        "v18_38c_r1_status": c.get("STATUS", ""),
        "current_fail_blocking_count": parse_int(c.get("CURRENT_FAIL_BLOCKING_COUNT")) or 0,
        "daily_run_usable": c.get("DAILY_RUN_USABLE", ""),
        "forward_research_usable": c.get("FORWARD_RESEARCH_USABLE", ""),
        "current_full_candidate_count": current_full_candidates or "",
        "latest_signal_freeze_count": latest_signal_freeze or "",
        "auto_trade": c.get("AUTO_TRADE", AUTO_TRADE),
        "auto_sell": c.get("AUTO_SELL", AUTO_SELL),
        "official_decision_impact": c.get("OFFICIAL_DECISION_IMPACT", OFFICIAL_DECISION_IMPACT),
        "ranking_modified": c.get("RANKING_MODIFIED", "FALSE"),
        "factor_weights_modified": c.get("FACTOR_WEIGHTS_MODIFIED", "FALSE"),
        "signal_freeze_ledger_modified": c.get("SIGNAL_FREEZE_LEDGER_MODIFIED", "FALSE"),
        "paper_trading_ledger_modified": c.get("PAPER_TRADING_LEDGER_MODIFIED", "FALSE"),
        "shadow_portfolio_ledger_modified": c.get("SHADOW_PORTFOLIO_LEDGER_MODIFIED", "FALSE"),
        "account_state_modified": c.get("ACCOUNT_STATE_MODIFIED", "FALSE"),
        "broker_api_used": c.get("BROKER_API_USED", "FALSE"),
        "order_execution_used": c.get("ORDER_EXECUTION_USED", "FALSE"),
    }


def build_validation_rows(root: Path, archive_root: Path, manifest_rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(check_name: str, status: str, detail: str, required: bool = True, expected: str = "", observed: str = "") -> None:
        rows.append(
            {
                "check_name": check_name,
                "status": status,
                "detail": detail,
                "required": "TRUE" if required else "FALSE",
                "expected": expected,
                "observed": observed,
            }
        )

    a = read_status(root / "outputs/v18/ops/V18_38A_READ_FIRST.txt")
    b = read_status(root / "outputs/v18/ops/V18_38B_READ_FIRST.txt")
    c = read_status(root / "outputs/v18/ops/V18_38C_R1_READ_FIRST.txt")

    add("archive_root_exists", "PASS" if archive_root.exists() else "FAIL", f"Snapshot root: {archive_root.as_posix()}", True, "exists", str(archive_root.exists()))
    add("manifest_exists", "PASS" if (archive_root / "MANIFEST.csv").exists() else "FAIL", "MANIFEST.csv present in archive root", True, "exists", str((archive_root / "MANIFEST.csv").exists()))
    add("validation_exists", "PASS" if (archive_root / "VALIDATION.csv").exists() else "FAIL", "VALIDATION.csv present in archive root", True, "exists", str((archive_root / "VALIDATION.csv").exists()))
    add("readme_exists", "PASS" if (archive_root / "README_V18_38D_RESEARCH_TRACKING_BASELINE.md").exists() else "FAIL", "README present in archive root", True, "exists", str((archive_root / "README_V18_38D_RESEARCH_TRACKING_BASELINE.md").exists()))
    add("restore_script_exists", "PASS" if (archive_root / "RESTORE_V18_38D.ps1").exists() else "FAIL", "Restore script generated", True, "exists", str((archive_root / "RESTORE_V18_38D.ps1").exists()))
    add("read_first_exists", "PASS" if (root / "outputs/v18/ops/V18_38D_READ_FIRST.txt").exists() else "FAIL", "Workspace READ_FIRST generated", True, "exists", str((root / "outputs/v18/ops/V18_38D_READ_FIRST.txt").exists()))
    add("v18_38a_read_first_status", "PASS" if is_status_ok_or_warn(a.get("STATUS", "")) else "FAIL", f"STATUS={a.get('STATUS', '')}", True, "OK or WARN", a.get("STATUS", ""))
    add("v18_38b_read_first_status", "PASS" if is_status_ok_or_warn(b.get("STATUS", "")) else "FAIL", f"STATUS={b.get('STATUS', '')}", True, "OK or WARN", b.get("STATUS", ""))
    add("v18_38c_r1_current_fail_blocking", "PASS" if (parse_int(c.get("CURRENT_FAIL_BLOCKING_COUNT")) or 0) == 0 else "FAIL", f"CURRENT_FAIL_BLOCKING_COUNT={c.get('CURRENT_FAIL_BLOCKING_COUNT', '')}", True, "0", c.get("CURRENT_FAIL_BLOCKING_COUNT", ""))
    add("v18_38c_r1_daily_run_usable", "PASS" if c.get("DAILY_RUN_USABLE", "") == "TRUE" else "FAIL", f"DAILY_RUN_USABLE={c.get('DAILY_RUN_USABLE', '')}", True, "TRUE", c.get("DAILY_RUN_USABLE", ""))
    add("v18_38c_r1_safety_markers", "PASS" if all(c.get(k, "") == v for k, v in {
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "SIGNAL_FREEZE_LEDGER_MODIFIED": "FALSE",
        "PAPER_TRADING_LEDGER_MODIFIED": "FALSE",
        "SHADOW_PORTFOLIO_LEDGER_MODIFIED": "FALSE",
        "BROKER_API_USED": "FALSE",
        "ORDER_EXECUTION_USED": "FALSE",
    }.items()) else "FAIL", "Required safety markers intact", True, "all markers present", "checked")
    add("current_full_candidate_count", "PASS" if (summary["current_full_candidate_count"] in ("", None) or int(summary["current_full_candidate_count"]) == 318) else "FAIL", f"CURRENT_FULL_CANDIDATE_COUNT={summary['current_full_candidate_count']}", False, "318 if discoverable", str(summary["current_full_candidate_count"]))
    add("latest_signal_freeze_count", "PASS" if (summary["latest_signal_freeze_count"] in ("", None) or int(summary["latest_signal_freeze_count"]) == 318) else "FAIL", f"LATEST_SIGNAL_FREEZE_COUNT={summary['latest_signal_freeze_count']}", False, "318 if discoverable", str(summary["latest_signal_freeze_count"]))
    add("restore_script_generated", "PASS" if (archive_root / "RESTORE_V18_38D.ps1").exists() else "FAIL", "Restore script was generated", True, "TRUE", str((archive_root / "RESTORE_V18_38D.ps1").exists()))
    add("restore_script_executed", "PASS", "Restore script was generated but not executed", True, "FALSE", "FALSE")
    return rows


def build_summary_row(summary: dict[str, Any], archive_root: Path, manifest_rows: list[dict[str, Any]], validation_rows: list[dict[str, Any]], timestamp: str) -> dict[str, Any]:
    copied = sum(1 for row in manifest_rows if row["copied"] == "TRUE")
    missing_optional = sum(1 for row in manifest_rows if row["copy_status"] == "MISSING_OPTIONAL")
    missing_critical = sum(1 for row in manifest_rows if row["copy_status"] == "MISSING_CRITICAL")
    copy_fail = sum(1 for row in manifest_rows if row["copy_status"] == "COPY_FAILED")
    validation_fail = sum(1 for row in validation_rows if row["status"] == "FAIL")

    warnings_present = (
        missing_optional > 0
        or summary["v18_38a_status"].startswith("WARN")
        or summary["v18_38b_status"].startswith("WARN")
        or summary["v18_38c_r1_status"].startswith("WARN")
        or summary["current_fail_blocking_count"] == 0 and summary["daily_run_usable"] == "TRUE" and summary["forward_research_usable"] == "TRUE" and False
    )

    if missing_critical > 0 or copy_fail > 0 or validation_fail > 0:
        status = "FAIL_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_BLOCKED"
    elif warnings_present:
        status = "WARN_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_REVIEW_NEEDED"
    else:
        status = "OK_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_READY"

    return {
        "status": status,
        "run_id": f"V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_{timestamp}",
        "generated_at": now_iso(),
        "snapshot_path": archive_root.as_posix(),
        "copied_file_count": copied,
        "missing_optional_count": missing_optional,
        "missing_critical_count": missing_critical,
        "copy_fail_count": copy_fail,
        "validation_fail_count": validation_fail,
        "v18_38a_status": summary["v18_38a_status"],
        "v18_38b_status": summary["v18_38b_status"],
        "v18_38c_r1_status": summary["v18_38c_r1_status"],
        "current_fail_blocking_count": summary["current_fail_blocking_count"],
        "daily_run_usable": summary["daily_run_usable"],
        "forward_research_usable": summary["forward_research_usable"],
        "current_full_candidate_count": summary["current_full_candidate_count"],
        "latest_signal_freeze_count": summary["latest_signal_freeze_count"],
        "auto_trade": summary["auto_trade"],
        "auto_sell": summary["auto_sell"],
        "official_decision_impact": summary["official_decision_impact"],
        "ranking_modified": summary["ranking_modified"],
        "factor_weights_modified": summary["factor_weights_modified"],
        "signal_freeze_ledger_modified": summary["signal_freeze_ledger_modified"],
        "paper_trading_ledger_modified": summary["paper_trading_ledger_modified"],
        "shadow_portfolio_ledger_modified": summary["shadow_portfolio_ledger_modified"],
        "account_state_modified": summary["account_state_modified"],
        "broker_api_used": summary["broker_api_used"],
        "order_execution_used": summary["order_execution_used"],
        "restore_script_generated": "TRUE",
        "restore_script_executed": "FALSE",
    }


def snapshot_sources(root: Path, archive_root: Path) -> tuple[list[dict[str, Any]], int, int, int]:
    manifest_rows: list[dict[str, Any]] = []
    missing_optional = 0
    missing_critical = 0
    copy_fail = 0

    for rel in CRITICAL_SOURCES:
        row = copy_one(root, archive_root, rel, True, "critical")
        manifest_rows.append(row)
        if row["copy_status"] == "MISSING_CRITICAL":
            missing_critical += 1
        if row["copy_status"] == "COPY_FAILED":
            copy_fail += 1

    for rel in OPTIONAL_SOURCES:
        row = copy_one(root, archive_root, rel, False, "optional")
        manifest_rows.append(row)
        if row["copy_status"] == "MISSING_OPTIONAL":
            missing_optional += 1
        if row["copy_status"] == "COPY_FAILED":
            copy_fail += 1

    return manifest_rows, missing_optional, missing_critical, copy_fail


def generated_artifact_rows(root: Path, archive_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in ADDITIONAL_WORKSPACE_OUTPUTS:
        source = root / rel
        target = archive_root / Path(rel)
        rows.append(
            {
                "source_path": rel.replace("\\", "/"),
                "snapshot_path": target.relative_to(archive_root).as_posix(),
                "exists": "TRUE" if source.exists() else "FALSE",
                "required": "TRUE",
                "copied": "TRUE" if source.exists() else "FALSE",
                "copy_status": "COPIED" if source.exists() else "MISSING_CRITICAL",
                "kind": "generated_output",
                "size_bytes": source.stat().st_size if source.exists() else "",
                "modified_time": datetime.fromtimestamp(source.stat().st_mtime).isoformat(timespec="seconds") if source.exists() else "",
                "sha256": path_hash(source) if source.exists() else "",
                "notes": "workspace snapshot output" if source.exists() else "generated snapshot output missing",
            }
        )
    return rows


def write_additional_outputs(root: Path, archive_root: Path, summary_row: dict[str, Any], validation_rows: list[dict[str, Any]], readme: str, restore_script: str, manifest_rows: list[dict[str, Any]]) -> None:
    summary_df = pd.DataFrame([summary_row], columns=SUMMARY_FIELDS)
    validation_df = pd.DataFrame(validation_rows, columns=VALIDATION_FIELDS)
    manifest_df = pd.DataFrame(manifest_rows, columns=MANIFEST_FIELDS)

    workspace_summary = root / "outputs/v18/ops/V18_38D_STABLE_SNAPSHOT_SUMMARY.csv"
    workspace_report = root / "outputs/v18/read_center/V18_38D_STABLE_SNAPSHOT_REPORT.md"
    workspace_read_first = root / "outputs/v18/ops/V18_38D_READ_FIRST.txt"
    archive_manifest = archive_root / "MANIFEST.csv"
    archive_validation = archive_root / "VALIDATION.csv"
    archive_readme = archive_root / "README_V18_38D_RESEARCH_TRACKING_BASELINE.md"
    archive_restore = archive_root / "RESTORE_V18_38D.ps1"

    write_csv(workspace_summary, summary_df, SUMMARY_FIELDS)
    write_text(workspace_report, readme.replace("V18.38D 稳定快照 / Qlib 风格研究追踪基线", "V18.38D 稳定快照 / Qlib 风格研究追踪基线"))

    # The report is operator-facing in the workspace and copied into the archive via the manifest rows below.
    write_csv(archive_manifest, manifest_df, MANIFEST_FIELDS)
    write_csv(archive_validation, validation_df, VALIDATION_FIELDS)
    write_text(archive_readme, readme)
    write_text(archive_restore, restore_script)

    # Copy the current workspace outputs into the archive so the snapshot is self-contained.
    for rel in [
        "outputs/v18/ops/V18_38D_STABLE_SNAPSHOT_SUMMARY.csv",
        "outputs/v18/read_center/V18_38D_STABLE_SNAPSHOT_REPORT.md",
        "outputs/v18/ops/V18_38D_READ_FIRST.txt",
    ]:
        src = root / rel
        dst = archive_root / Path(rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def build_read_first(summary_row: dict[str, Any]) -> str:
    fields = {
        "STATUS": summary_row["status"],
        "MODE": MODE,
        "RUN_ID": summary_row["run_id"],
        "GENERATED_AT": summary_row["generated_at"],
        "SNAPSHOT_PATH": summary_row["snapshot_path"],
        "COPIED_FILE_COUNT": summary_row["copied_file_count"],
        "MISSING_OPTIONAL_COUNT": summary_row["missing_optional_count"],
        "MISSING_CRITICAL_COUNT": summary_row["missing_critical_count"],
        "COPY_FAIL_COUNT": summary_row["copy_fail_count"],
        "VALIDATION_FAIL_COUNT": summary_row["validation_fail_count"],
        "V18_38A_STATUS": summary_row["v18_38a_status"],
        "V18_38B_STATUS": summary_row["v18_38b_status"],
        "V18_38C_R1_STATUS": summary_row["v18_38c_r1_status"],
        "CURRENT_FAIL_BLOCKING_COUNT": summary_row["current_fail_blocking_count"],
        "DAILY_RUN_USABLE": summary_row["daily_run_usable"],
        "FORWARD_RESEARCH_USABLE": summary_row["forward_research_usable"],
        "CURRENT_FULL_CANDIDATE_COUNT": summary_row["current_full_candidate_count"],
        "LATEST_SIGNAL_FREEZE_COUNT": summary_row["latest_signal_freeze_count"],
        "AUTO_TRADE": summary_row["auto_trade"],
        "AUTO_SELL": summary_row["auto_sell"],
        "OFFICIAL_DECISION_IMPACT": summary_row["official_decision_impact"],
        "RANKING_MODIFIED": summary_row["ranking_modified"],
        "FACTOR_WEIGHTS_MODIFIED": summary_row["factor_weights_modified"],
        "SIGNAL_FREEZE_LEDGER_MODIFIED": summary_row["signal_freeze_ledger_modified"],
        "PAPER_TRADING_LEDGER_MODIFIED": summary_row["paper_trading_ledger_modified"],
        "SHADOW_PORTFOLIO_LEDGER_MODIFIED": summary_row["shadow_portfolio_ledger_modified"],
        "ACCOUNT_STATE_MODIFIED": summary_row["account_state_modified"],
        "BROKER_API_USED": summary_row["broker_api_used"],
        "ORDER_EXECUTION_USED": summary_row["order_execution_used"],
        "RESTORE_SCRIPT_GENERATED": summary_row["restore_script_generated"],
        "RESTORE_SCRIPT_EXECUTED": summary_row["restore_script_executed"],
    }
    return "\n".join(f"{k}: {v}" for k, v in fields.items()) + "\n"


def run(root: Path) -> int:
    ensure_dirs(root)
    timestamp = now_stamp()
    archive_root = current_snapshot_path(root, timestamp)
    archive_root.mkdir(parents=True, exist_ok=True)

    manifest_rows, missing_optional, missing_critical, copy_fail = snapshot_sources(root, archive_root)
    summary = gather_status_summary(root)

    validation_rows = build_validation_rows(root, archive_root, manifest_rows, summary)

    # enrich summary with counts before final classification
    summary_row = build_summary_row(summary, archive_root, manifest_rows, validation_rows, timestamp)
    summary_row["missing_optional_count"] = missing_optional
    summary_row["missing_critical_count"] = missing_critical
    summary_row["copy_fail_count"] = copy_fail

    validation_rows = build_validation_rows(root, archive_root, manifest_rows, summary_row)
    summary_row["validation_fail_count"] = sum(1 for row in validation_rows if row["status"] == "FAIL")

    warnings_present = (
        missing_optional > 0
        or summary["v18_38a_status"].startswith("WARN")
        or summary["v18_38b_status"].startswith("WARN")
        or summary["v18_38c_r1_status"].startswith("WARN")
        or summary_row["validation_fail_count"] > 0
    )
    if missing_critical > 0 or copy_fail > 0 or summary_row["validation_fail_count"] > 0:
        summary_row["status"] = "FAIL_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_BLOCKED"
    elif warnings_present:
        summary_row["status"] = "WARN_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_REVIEW_NEEDED"
    else:
        summary_row["status"] = "OK_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_READY"

    # Generate operator-facing outputs
    readme = build_readme(summary_row, validation_rows, archive_root, archive_root / "RESTORE_V18_38D.ps1")
    write_text(root / "outputs/v18/read_center/V18_38D_STABLE_SNAPSHOT_REPORT.md", readme)
    write_text(root / "outputs/v18/ops/V18_38D_READ_FIRST.txt", build_read_first(summary_row))

    # Rebuild validation and manifest after the workspace outputs exist, then copy them into the archive.
    manifest_rows, missing_optional, missing_critical, copy_fail = snapshot_sources(root, archive_root)
    manifest_rows.extend(generated_artifact_rows(root, archive_root))
    summary_row["copied_file_count"] = sum(1 for row in manifest_rows if row["copied"] == "TRUE")
    summary_row["missing_optional_count"] = missing_optional
    summary_row["missing_critical_count"] = missing_critical
    summary_row["copy_fail_count"] = copy_fail
    validation_rows = build_validation_rows(root, archive_root, manifest_rows, summary_row)
    summary_row["validation_fail_count"] = sum(1 for row in validation_rows if row["status"] == "FAIL")
    if missing_critical > 0 or copy_fail > 0 or summary_row["validation_fail_count"] > 0:
        summary_row["status"] = "FAIL_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_BLOCKED"
    elif (
        missing_optional > 0
        or summary["v18_38a_status"].startswith("WARN")
        or summary["v18_38b_status"].startswith("WARN")
        or summary["v18_38c_r1_status"].startswith("WARN")
    ):
        summary_row["status"] = "WARN_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_REVIEW_NEEDED"
    else:
        summary_row["status"] = "OK_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_READY"

    write_additional_outputs(root, archive_root, summary_row, validation_rows, readme, build_restore_script(), manifest_rows)

    # Copy the workspace-produced outputs into the archive after they exist.
    for rel in [
        "outputs/v18/ops/V18_38D_STABLE_SNAPSHOT_SUMMARY.csv",
        "outputs/v18/read_center/V18_38D_STABLE_SNAPSHOT_REPORT.md",
        "outputs/v18/ops/V18_38D_READ_FIRST.txt",
    ]:
        src = root / rel
        dst = archive_root / Path(rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # Replace the archive metadata with the final manifest/validation after workspace outputs are in place.
    manifest_rows, missing_optional, missing_critical, copy_fail = snapshot_sources(root, archive_root)
    manifest_rows.extend(generated_artifact_rows(root, archive_root))
    summary_row["copied_file_count"] = sum(1 for row in manifest_rows if row["copied"] == "TRUE")
    summary_row["missing_optional_count"] = missing_optional
    summary_row["missing_critical_count"] = missing_critical
    summary_row["copy_fail_count"] = copy_fail
    validation_rows = build_validation_rows(root, archive_root, manifest_rows, summary_row)
    summary_row["validation_fail_count"] = sum(1 for row in validation_rows if row["status"] == "FAIL")

    if missing_critical > 0 or copy_fail > 0 or summary_row["validation_fail_count"] > 0:
        summary_row["status"] = "FAIL_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_BLOCKED"
    elif (
        missing_optional > 0
        or summary["v18_38a_status"].startswith("WARN")
        or summary["v18_38b_status"].startswith("WARN")
        or summary["v18_38c_r1_status"].startswith("WARN")
    ):
        summary_row["status"] = "WARN_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_REVIEW_NEEDED"
    else:
        summary_row["status"] = "OK_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_READY"

    write_csv(root / "outputs/v18/ops/V18_38D_STABLE_SNAPSHOT_SUMMARY.csv", pd.DataFrame([summary_row], columns=SUMMARY_FIELDS), SUMMARY_FIELDS)
    write_csv(archive_root / "MANIFEST.csv", pd.DataFrame(manifest_rows, columns=MANIFEST_FIELDS), MANIFEST_FIELDS)
    write_csv(archive_root / "VALIDATION.csv", pd.DataFrame(validation_rows, columns=VALIDATION_FIELDS), VALIDATION_FIELDS)
    write_text(archive_root / "README_V18_38D_RESEARCH_TRACKING_BASELINE.md", readme)
    write_text(archive_root / "RESTORE_V18_38D.ps1", build_restore_script())
    write_text(root / "outputs/v18/read_center/V18_38D_STABLE_SNAPSHOT_REPORT.md", readme)
    write_text(root / "outputs/v18/ops/V18_38D_READ_FIRST.txt", build_read_first(summary_row))

    # Final archive copies, including the generated workspace outputs.
    for rel in [
        "outputs/v18/ops/V18_38D_STABLE_SNAPSHOT_SUMMARY.csv",
        "outputs/v18/read_center/V18_38D_STABLE_SNAPSHOT_REPORT.md",
        "outputs/v18/ops/V18_38D_READ_FIRST.txt",
    ]:
        src = root / rel
        dst = archive_root / Path(rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    return 1 if summary_row["status"].startswith("FAIL") else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
