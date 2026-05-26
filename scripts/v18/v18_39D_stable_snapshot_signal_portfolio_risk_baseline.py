#!/usr/bin/env python
"""V18.39D stable snapshot / LEAN-inspired signal-portfolio-risk baseline.

This module is snapshot-only. It copies the current V18.39A/B/C bridge, the
current command center file, and adjacent status context into a timestamped
archive under archive/stable without modifying ranking, candidates, factors,
freeze ledgers, account state, broker APIs, or trading/order logic.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


MODE = "STABLE_SNAPSHOT_ONLY_SIGNAL_PORTFOLIO_RISK_BASELINE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

CRITICAL_SOURCES = [
    "scripts/v18/v18_39A_alpha_signal_object_layer.py",
    "scripts/v18/run_v18_39A_alpha_signal_object_layer.ps1",
    "outputs/v18/signals/V18_39A_ALPHA_SIGNAL_OBJECTS.csv",
    "outputs/v18/signals/V18_39A_ALPHA_SIGNAL_SUMMARY.csv",
    "outputs/v18/signals/V18_39A_ALPHA_SIGNAL_TAGS.csv",
    "outputs/v18/read_center/V18_39A_ALPHA_SIGNAL_OBJECT_LAYER_REPORT.md",
    "outputs/v18/read_center/V18_CURRENT_ALPHA_SIGNAL_OBJECTS.md",
    "outputs/v18/ops/V18_39A_READ_FIRST.txt",
    "scripts/v18/v18_39B_portfolio_target_preview.py",
    "scripts/v18/run_v18_39B_portfolio_target_preview.ps1",
    "outputs/v18/portfolio_preview/V18_39B_PORTFOLIO_TARGET_PREVIEW.csv",
    "outputs/v18/portfolio_preview/V18_39B_PORTFOLIO_TARGET_SUMMARY.csv",
    "outputs/v18/portfolio_preview/V18_39B_PORTFOLIO_TARGET_DIAGNOSTICS.csv",
    "outputs/v18/read_center/V18_39B_PORTFOLIO_TARGET_PREVIEW_REPORT.md",
    "outputs/v18/read_center/V18_CURRENT_PORTFOLIO_TARGET_PREVIEW.md",
    "outputs/v18/ops/V18_39B_READ_FIRST.txt",
    "scripts/v18/v18_39C_shadow_risk_model_preview.py",
    "scripts/v18/run_v18_39C_shadow_risk_model_preview.ps1",
    "outputs/v18/risk_preview/V18_39C_SHADOW_RISK_PREVIEW_SUMMARY.csv",
    "outputs/v18/risk_preview/V18_39C_SHADOW_RISK_PREVIEW_DETAIL.csv",
    "outputs/v18/risk_preview/V18_39C_SHADOW_RISK_RULES.csv",
    "outputs/v18/read_center/V18_39C_SHADOW_RISK_MODEL_PREVIEW_REPORT.md",
    "outputs/v18/read_center/V18_CURRENT_SHADOW_RISK_MODEL_PREVIEW.md",
    "outputs/v18/ops/V18_39C_READ_FIRST.txt",
    "scripts/v18/run_v18_current_daily_command_center.ps1",
]

OPTIONAL_SOURCES = [
    "outputs/v18/ops/V18_38C_R1_READ_FIRST.txt",
    "outputs/v18/ops/V18_38D_READ_FIRST.txt",
    "outputs/v18/ops/V18_38D_STABLE_SNAPSHOT_SUMMARY.csv",
    "outputs/v18/read_center/V18_38D_STABLE_SNAPSHOT_REPORT.md",
    "outputs/v18/read_center/V18_CURRENT_COMMAND_STATUS_NORMALIZATION.md",
    "outputs/v18/read_center/V18_CURRENT_FORWARD_EVIDENCE_DASHBOARD.md",
    "outputs/v18/read_center/V18_CURRENT_RESEARCH_EXPERIMENT_REGISTRY.md",
    "outputs/v18/candidates/V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
    "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
]

GENETATED_WORKSPACE_OUTPUTS = [
    "outputs/v18/ops/V18_39D_STABLE_SNAPSHOT_SUMMARY.csv",
    "outputs/v18/read_center/V18_39D_STABLE_SNAPSHOT_REPORT.md",
    "outputs/v18/ops/V18_39D_READ_FIRST.txt",
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
    "v18_39a_status",
    "v18_39b_status",
    "v18_39c_status",
    "total_signal_count",
    "total_preview_row_count",
    "total_scenario_capital_rows",
    "current_fail_blocking_count",
    "daily_run_usable",
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


def parse_int(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return int(float(text))
    except Exception:
        return None


def path_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def status_bucket(status: str) -> str:
    s = str(status or "").strip().upper()
    if s.startswith("OK"):
        return "OK"
    if s.startswith("WARN"):
        return "WARN"
    if s.startswith("FAIL"):
        return "FAIL"
    return "UNKNOWN"


def is_ok_or_warn(status: str) -> bool:
    return status_bucket(status) in {"OK", "WARN"}


def current_snapshot_path(root: Path, timestamp: str) -> Path:
    return root / "archive" / "stable" / f"V18_39D_signal_portfolio_risk_baseline_{timestamp}"


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


def source_copy_rows(root: Path, archive_root: Path) -> tuple[list[dict[str, Any]], int, int, int]:
    rows: list[dict[str, Any]] = []
    missing_optional = 0
    missing_critical = 0
    copy_fail = 0

    for rel in CRITICAL_SOURCES:
        row = copy_one(root, archive_root, rel, True, "critical")
        rows.append(row)
        if row["copy_status"] == "MISSING_CRITICAL":
            missing_critical += 1
        if row["copy_status"] == "MISSING_OPTIONAL":
            missing_optional += 1
        if row["copy_status"] == "COPY_FAILED":
            copy_fail += 1

    for rel in OPTIONAL_SOURCES:
        row = copy_one(root, archive_root, rel, False, "optional")
        rows.append(row)
        if row["copy_status"] == "MISSING_OPTIONAL":
            missing_optional += 1
        if row["copy_status"] == "COPY_FAILED":
            copy_fail += 1

    return rows, missing_optional, missing_critical, copy_fail


def generated_output_rows(root: Path, archive_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in GENETATED_WORKSPACE_OUTPUTS:
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
                "notes": "workspace generated snapshot output" if source.exists() else "generated snapshot output missing",
            }
        )
    return rows


def build_restore_script(snapshot_path: str) -> str:
    return f"""[CmdletBinding()]
param(
    [string]$Root = "D:\\us-tech-quant",
    [string]$SnapshotPath = "{snapshot_path}"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SnapshotPath)) {{
    throw "Snapshot path not found: $SnapshotPath"
}}

$items = Get-ChildItem -Path $SnapshotPath -File -Recurse
foreach ($item in $items) {{
    $relative = $item.FullName.Substring($SnapshotPath.Length).TrimStart("\\", "/")
    if ([string]::IsNullOrWhiteSpace($relative)) {{
        continue
    }}
    $destination = Join-Path $Root $relative
    $destinationDir = Split-Path -Parent $destination
    if (-not (Test-Path $destinationDir)) {{
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    }}
    Copy-Item -Path $item.FullName -Destination $destination -Force
}}

Write-Host "RESTORE_SCRIPT_EXECUTED: FALSE"
Write-Host "SNAPSHOT_PATH: $SnapshotPath"
Write-Host "RESTORED_TO_ROOT: $Root"
"""


def parse_read_first(path: Path) -> dict[str, str]:
    return read_status(path)


def build_context(root: Path) -> dict[str, dict[str, str]]:
    return {
        "v39a": parse_read_first(root / "outputs/v18/ops/V18_39A_READ_FIRST.txt"),
        "v39b": parse_read_first(root / "outputs/v18/ops/V18_39B_READ_FIRST.txt"),
        "v39c": parse_read_first(root / "outputs/v18/ops/V18_39C_READ_FIRST.txt"),
        "v38c_r1": parse_read_first(root / "outputs/v18/ops/V18_38C_R1_READ_FIRST.txt"),
        "v38d": parse_read_first(root / "outputs/v18/ops/V18_38D_READ_FIRST.txt"),
    }


def get_count(ctx: dict[str, dict[str, str]], key: str, field: str) -> Any:
    return ctx.get(key, {}).get(field, "")


def build_validation_rows(root: Path, archive_root: Path, ctx: dict[str, dict[str, str]], generated_rows: list[dict[str, Any]], summary_row: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(check_name: str, status: str, required: bool, expected: Any, observed: Any, detail: str = "") -> None:
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

    add("critical_source_missing_count", "FAIL" if summary_row["missing_critical_count"] > 0 else "PASS", True, 0, summary_row["missing_critical_count"], "")
    add("copy_fail_count", "FAIL" if summary_row["copy_fail_count"] > 0 else "PASS", True, 0, summary_row["copy_fail_count"], "")
    add("optional_source_missing_count", "WARN" if summary_row["missing_optional_count"] > 0 else "PASS", False, 0, summary_row["missing_optional_count"], "")

    for key, label, count_field, expected_status in [
        ("v39a", "V18.39A", "TOTAL_SIGNAL_COUNT", 318),
        ("v39b", "V18.39B", "TOTAL_PREVIEW_ROW_COUNT", 1832),
        ("v39c", "V18.39C", "TOTAL_SCENARIO_CAPITAL_ROWS", 20),
    ]:
        status = ctx.get(key, {}).get("STATUS", "")
        add(
            f"{key}_status_ok_or_warn",
            "PASS" if is_ok_or_warn(status) else "FAIL",
            True,
            "OK or WARN",
            status,
            "",
        )
        count_value = parse_int(ctx.get(key, {}).get(count_field))
        add(
            f"{key}_{count_field.lower()}",
            "PASS" if count_value == expected_status else "FAIL",
            True,
            expected_status,
            count_value if count_value is not None else "",
            "",
        )

    safety_fields = [
        "AUTO_TRADE",
        "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT",
        "RANKING_MODIFIED",
        "FACTOR_WEIGHTS_MODIFIED",
        "SIGNAL_FREEZE_LEDGER_MODIFIED",
        "PAPER_TRADING_LEDGER_MODIFIED",
        "SHADOW_PORTFOLIO_LEDGER_MODIFIED",
        "ACCOUNT_STATE_MODIFIED",
        "BROKER_API_USED",
        "ORDER_EXECUTION_USED",
    ]
    for key in ("v39a", "v39b", "v39c"):
        for field in safety_fields:
            expected = {
                "AUTO_TRADE": "DISABLED",
                "AUTO_SELL": "DISABLED",
                "OFFICIAL_DECISION_IMPACT": "NONE",
                "RANKING_MODIFIED": "FALSE",
                "FACTOR_WEIGHTS_MODIFIED": "FALSE",
                "SIGNAL_FREEZE_LEDGER_MODIFIED": "FALSE",
                "PAPER_TRADING_LEDGER_MODIFIED": "FALSE",
                "SHADOW_PORTFOLIO_LEDGER_MODIFIED": "FALSE",
                "ACCOUNT_STATE_MODIFIED": "FALSE",
                "BROKER_API_USED": "FALSE",
                "ORDER_EXECUTION_USED": "FALSE",
            }[field]
            observed = ctx.get(key, {}).get(field, "")
            add(
                f"{key}_{field.lower()}",
                "PASS" if observed == expected else "FAIL",
                True,
                expected,
                observed,
                "",
            )

    add(
        "v38c_r1_current_fail_blocking_count_zero",
        "PASS" if parse_int(get_count(ctx, "v38c_r1", "CURRENT_FAIL_BLOCKING_COUNT")) in {None, 0} else "FAIL",
        True,
        0,
        parse_int(get_count(ctx, "v38c_r1", "CURRENT_FAIL_BLOCKING_COUNT")) if get_count(ctx, "v38c_r1", "CURRENT_FAIL_BLOCKING_COUNT") != "" else "",
        "",
    )
    add(
        "daily_run_usable_true",
        "PASS" if str(get_count(ctx, "v39a", "DAILY_RUN_USABLE")).upper() == "TRUE" else "FAIL",
        True,
        "TRUE",
        get_count(ctx, "v39a", "DAILY_RUN_USABLE"),
        "",
    )
    add(
        "restore_script_not_executed",
        "PASS",
        True,
        "FALSE",
        "FALSE",
        "",
    )
    add(
        "generated_rows_count",
        "PASS" if len(generated_rows) == 3 else "FAIL",
        True,
        3,
        len(generated_rows),
        "",
    )
    return rows


def build_summary_row(
    root: Path,
    archive_root: Path,
    ctx: dict[str, dict[str, str]],
    copied_file_count: int,
    missing_optional: int,
    missing_critical: int,
    copy_fail: int,
    validation_fail: int,
) -> dict[str, Any]:
    v39a = ctx.get("v39a", {})
    v39b = ctx.get("v39b", {})
    v39c = ctx.get("v39c", {})
    v38c_r1 = ctx.get("v38c_r1", {})
    v38d = ctx.get("v38d", {})

    total_signal_count = parse_int(v39a.get("TOTAL_SIGNAL_COUNT"))
    total_preview_row_count = parse_int(v39b.get("TOTAL_PREVIEW_ROW_COUNT"))
    total_scenario_rows = parse_int(v39c.get("TOTAL_SCENARIO_CAPITAL_ROWS"))
    current_fail_blocking = parse_int(v38c_r1.get("CURRENT_FAIL_BLOCKING_COUNT"))
    daily_run_usable = (v39a.get("DAILY_RUN_USABLE") or v39b.get("DAILY_RUN_USABLE") or v39c.get("DAILY_RUN_USABLE") or v38c_r1.get("DAILY_RUN_USABLE") or "UNKNOWN").strip().upper()
    current_full_candidate_count = parse_int(v39a.get("CURRENT_FULL_CANDIDATE_COUNT"))
    latest_signal_freeze_count = parse_int(v39a.get("LATEST_SIGNAL_FREEZE_COUNT"))

    statuses = [v39a.get("STATUS", ""), v39b.get("STATUS", ""), v39c.get("STATUS", ""), v38c_r1.get("STATUS", ""), v38d.get("STATUS", "")]
    inherited_warns = any(status_bucket(status) == "WARN" for status in statuses if status)

    if missing_critical > 0 or copy_fail > 0 or validation_fail > 0:
        status = "FAIL_V18_39D_STABLE_SNAPSHOT_SIGNAL_PORTFOLIO_RISK_BASELINE_BLOCKED"
    elif missing_optional > 0 or inherited_warns:
        status = "WARN_V18_39D_STABLE_SNAPSHOT_SIGNAL_PORTFOLIO_RISK_BASELINE_REVIEW_NEEDED"
    else:
        status = "OK_V18_39D_STABLE_SNAPSHOT_SIGNAL_PORTFOLIO_RISK_BASELINE_READY"

    return {
        "status": status,
        "run_id": f"V18_39D_STABLE_SNAPSHOT_SIGNAL_PORTFOLIO_RISK_BASELINE_{now_stamp()}",
        "generated_at": now_iso(),
        "snapshot_path": archive_root.as_posix(),
        "copied_file_count": copied_file_count,
        "missing_optional_count": missing_optional,
        "missing_critical_count": missing_critical,
        "copy_fail_count": copy_fail,
        "validation_fail_count": validation_fail,
        "v18_39a_status": v39a.get("STATUS", ""),
        "v18_39b_status": v39b.get("STATUS", ""),
        "v18_39c_status": v39c.get("STATUS", ""),
        "total_signal_count": total_signal_count if total_signal_count is not None else "",
        "total_preview_row_count": total_preview_row_count if total_preview_row_count is not None else "",
        "total_scenario_capital_rows": total_scenario_rows if total_scenario_rows is not None else "",
        "current_fail_blocking_count": current_fail_blocking if current_fail_blocking is not None else "",
        "daily_run_usable": "TRUE" if daily_run_usable == "TRUE" else ("FALSE" if daily_run_usable == "FALSE" else daily_run_usable),
        "current_full_candidate_count": current_full_candidate_count if current_full_candidate_count is not None else "",
        "latest_signal_freeze_count": latest_signal_freeze_count if latest_signal_freeze_count is not None else "",
        "auto_trade": "DISABLED",
        "auto_sell": "DISABLED",
        "official_decision_impact": "NONE",
        "ranking_modified": "FALSE",
        "factor_weights_modified": "FALSE",
        "signal_freeze_ledger_modified": "FALSE",
        "paper_trading_ledger_modified": "FALSE",
        "shadow_portfolio_ledger_modified": "FALSE",
        "account_state_modified": "FALSE",
        "broker_api_used": "FALSE",
        "order_execution_used": "FALSE",
        "restore_script_generated": "TRUE",
        "restore_script_executed": "FALSE",
    }


def build_readme(summary_row: dict[str, Any], validation_rows: list[dict[str, Any]], archive_root: Path) -> str:
    status = summary_row["status"]
    validation_fail_count = summary_row["validation_fail_count"]
    optional_missing = summary_row["missing_optional_count"]
    current_fail = summary_row["current_fail_blocking_count"]
    safe_lines = [
        f"- V18.39A: {summary_row['v18_39a_status']}",
        f"- V18.39B: {summary_row['v18_39b_status']}",
        f"- V18.39C: {summary_row['v18_39c_status']}",
    ]
    validation_notes = "\n".join(
        f"- {row['check_name']}: {row['status']} / expected={row['expected']} / observed={row['observed']}"
        for row in validation_rows[:20]
    )
    return f"""# V18.39D Stable Snapshot / Signal-Portfolio-Risk Baseline

## 1. 今日结论
- 状态: {status}
- 这是一个只读快照，不涉及交易、下单或账户变更。
- Validation fail count: {validation_fail_count}
- Optional missing count: {optional_missing}

## 2. 快照路径
- {archive_root.as_posix()}

## 3. 为什么创建这个快照
为了把 V18.39A/B/C 的 LEAN-inspired signal / portfolio / risk bridge 做成本地稳定基线，便于后续回看、恢复和审计。

## 4. 包含的核心模块
- V18.39A alpha signal object layer
- V18.39B portfolio target preview
- V18.39C shadow risk model preview
- 当前 command center 文件
- V18.38C-R1 与 V18.38D 状态上下文（如存在）

## 5. V18.39A/B/C 状态
{chr(10).join(safe_lines)}

## 6. Alpha signal / portfolio preview / risk preview 核心指标
- Total signal count: {summary_row['total_signal_count']}
- Total preview row count: {summary_row['total_preview_row_count']}
- Total scenario capital rows: {summary_row['total_scenario_capital_rows']}
- Current fail blocking count: {current_fail}
- Daily run usable: {summary_row['daily_run_usable']}

## 7. 候选池 / freeze 状态
- Current full candidate count: {summary_row['current_full_candidate_count']}
- Latest signal freeze count: {summary_row['latest_signal_freeze_count']}

## 8. 验证结果
{validation_notes}

## 9. 安全确认
- AUTO_TRADE: DISABLED
- AUTO_SELL: DISABLED
- OFFICIAL_DECISION_IMPACT: NONE
- RANKING_MODIFIED: FALSE
- FACTOR_WEIGHTS_MODIFIED: FALSE
- SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE
- PAPER_TRADING_LEDGER_MODIFIED: FALSE
- SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE
- ACCOUNT_STATE_MODIFIED: FALSE
- BROKER_API_USED: FALSE
- ORDER_EXECUTION_USED: FALSE

## 10. 恢复方式说明
运行 archive/stable 下的 `RESTORE_V18_39D.ps1`，它会把快照里的文件复制回工作区。该脚本已生成，但本次没有执行。

## 11. 下一步建议
{summary_row['status'] if status.startswith('OK') else '保留该快照作为只读基线，必要时先查看 WARN 项再继续。'}
"""


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
        "V18_39A_STATUS": summary_row["v18_39a_status"],
        "V18_39B_STATUS": summary_row["v18_39b_status"],
        "V18_39C_STATUS": summary_row["v18_39c_status"],
        "TOTAL_SIGNAL_COUNT": summary_row["total_signal_count"],
        "TOTAL_PREVIEW_ROW_COUNT": summary_row["total_preview_row_count"],
        "TOTAL_SCENARIO_CAPITAL_ROWS": summary_row["total_scenario_capital_rows"],
        "CURRENT_FAIL_BLOCKING_COUNT": summary_row["current_fail_blocking_count"],
        "DAILY_RUN_USABLE": summary_row["daily_run_usable"],
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
    return "\n".join(f"{key}: {value}" for key, value in fields.items()) + "\n"


def run(root: Path) -> int:
    ensure_dirs(root)
    timestamp = now_stamp()
    archive_root = current_snapshot_path(root, timestamp)
    archive_root.mkdir(parents=True, exist_ok=True)

    source_rows, missing_optional, missing_critical, copy_fail = source_copy_rows(root, archive_root)
    ctx = build_context(root)
    generated_rows = generated_output_rows(root, archive_root)

    copied_file_count = sum(1 for row in source_rows if row["copied"] == "TRUE") + sum(1 for row in generated_rows if row["copied"] == "TRUE")
    summary_row = build_summary_row(
        root=root,
        archive_root=archive_root,
        ctx=ctx,
        copied_file_count=copied_file_count,
        missing_optional=missing_optional,
        missing_critical=missing_critical,
        copy_fail=copy_fail,
        validation_fail=0,
    )

    validation_rows = build_validation_rows(root, archive_root, ctx, generated_rows, summary_row)
    validation_fail_count = sum(1 for row in validation_rows if row["status"] == "FAIL")
    summary_row["validation_fail_count"] = validation_fail_count
    summary_row["status"] = build_summary_row(
        root=root,
        archive_root=archive_root,
        ctx=ctx,
        copied_file_count=copied_file_count,
        missing_optional=missing_optional,
        missing_critical=missing_critical,
        copy_fail=copy_fail,
        validation_fail=validation_fail_count,
    )["status"]

    summary_df = pd.DataFrame([summary_row], columns=SUMMARY_FIELDS)
    validation_df = pd.DataFrame(validation_rows, columns=VALIDATION_FIELDS)
    manifest_df = pd.DataFrame(source_rows + generated_rows, columns=MANIFEST_FIELDS)

    readme = build_readme(summary_row, validation_rows, archive_root)
    read_first = build_read_first(summary_row)

    write_csv(root / "outputs/v18/ops/V18_39D_STABLE_SNAPSHOT_SUMMARY.csv", summary_df, SUMMARY_FIELDS)
    write_text(root / "outputs/v18/read_center/V18_39D_STABLE_SNAPSHOT_REPORT.md", readme)
    write_text(root / "outputs/v18/ops/V18_39D_READ_FIRST.txt", read_first)

    # Copy generated workspace outputs into the archive so the snapshot is self-contained.
    for rel in GENETATED_WORKSPACE_OUTPUTS:
        src = root / rel
        dst = archive_root / Path(rel)
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # Archive metadata written after the workspace outputs exist.
    write_csv(archive_root / "MANIFEST.csv", manifest_df, MANIFEST_FIELDS)
    write_csv(archive_root / "VALIDATION.csv", validation_df, VALIDATION_FIELDS)
    write_text(archive_root / "README_V18_39D_SIGNAL_PORTFOLIO_RISK_BASELINE.md", readme)
    write_text(archive_root / "RESTORE_V18_39D.ps1", build_restore_script(archive_root.as_posix()))

    # Copy the workspace-produced outputs into the archive after they have been finalized.
    for rel in GENETATED_WORKSPACE_OUTPUTS:
        src = root / rel
        dst = archive_root / Path(rel)
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # Refresh the archive metadata to capture the final copied workspace outputs.
    source_rows, missing_optional, missing_critical, copy_fail = source_copy_rows(root, archive_root)
    generated_rows = generated_output_rows(root, archive_root)
    copied_file_count = sum(1 for row in source_rows if row["copied"] == "TRUE") + sum(1 for row in generated_rows if row["copied"] == "TRUE")
    summary_row = build_summary_row(
        root=root,
        archive_root=archive_root,
        ctx=ctx,
        copied_file_count=copied_file_count,
        missing_optional=missing_optional,
        missing_critical=missing_critical,
        copy_fail=copy_fail,
        validation_fail=validation_fail_count,
    )
    summary_df = pd.DataFrame([summary_row], columns=SUMMARY_FIELDS)
    validation_rows = build_validation_rows(root, archive_root, ctx, generated_rows, summary_row)
    validation_df = pd.DataFrame(validation_rows, columns=VALIDATION_FIELDS)
    manifest_df = pd.DataFrame(source_rows + generated_rows, columns=MANIFEST_FIELDS)
    readme = build_readme(summary_row, validation_rows, archive_root)
    read_first = build_read_first(summary_row)

    write_csv(root / "outputs/v18/ops/V18_39D_STABLE_SNAPSHOT_SUMMARY.csv", summary_df, SUMMARY_FIELDS)
    write_text(root / "outputs/v18/read_center/V18_39D_STABLE_SNAPSHOT_REPORT.md", readme)
    write_text(root / "outputs/v18/ops/V18_39D_READ_FIRST.txt", read_first)
    write_csv(archive_root / "MANIFEST.csv", manifest_df, MANIFEST_FIELDS)
    write_csv(archive_root / "VALIDATION.csv", validation_df, VALIDATION_FIELDS)
    write_text(archive_root / "README_V18_39D_SIGNAL_PORTFOLIO_RISK_BASELINE.md", readme)
    write_text(archive_root / "RESTORE_V18_39D.ps1", build_restore_script(archive_root.as_posix()))

    return 1 if summary_row["status"].startswith("FAIL_") else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
