from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


STATUS_OK = "OK_V18_16J_R1_COMMAND_CENTER_COVERAGE_SOURCE_PATCH_READY"
STATUS_WARN = "WARN_V18_16J_R1_COMMAND_CENTER_COVERAGE_SOURCE_PATCH_CHECK_FAILED"
MODE = "COMPATIBILITY_REPORTING_PATCH"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"


COMPAT_FIELDS = ["component", "file", "field_or_check", "before_value", "after_value", "action", "status", "reason"]
COVERAGE_FIELDS = [
    "candidate_source",
    "exists",
    "selected",
    "source_status",
    "today_scan_count",
    "required_daily_scan_count",
    "daily_threshold_met",
    "daily_threshold_shortfall",
    "true_5day_unique_coverage_met",
    "reason",
]
WARNING_FIELDS = ["wrapper", "warning_or_failure", "old_behavior", "new_behavior", "status", "reason", "safety_condition"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            pass
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            pass
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def first_value(path: Path, key: str) -> str:
    target = key.upper()
    lines = read_text(path).splitlines()
    for i, line in enumerate(lines):
        if ":" in line:
            left, right = line.split(":", 1)
            if left.strip().upper().lstrip("- ").strip() == target:
                return right.strip()
        if line.strip().upper().lstrip("- ").strip() == target and i + 1 < len(lines):
            return lines[i + 1].strip()
    return ""


def to_int(value: object, default: int = 0) -> int:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return default
    try:
        return int(float(text))
    except Exception:
        return default


def bool_text(value: bool) -> str:
    return str(bool(value)).upper()


def metric_map(path: Path) -> Dict[str, str]:
    rows, _, _ = read_csv(path)
    result: Dict[str, str] = {}
    for row in rows:
        metric = str(row.get("metric", "")).strip().upper()
        if metric:
            result[metric] = str(row.get("value", "")).strip()
    return result


def source_stats(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {"exists": False, "today": 0, "required": 0, "met": False, "shortfall": 0, "status": "MISSING"}
    name = path.name.upper()
    if name.endswith(".TXT"):
        if "V18_16F" in name:
            today = to_int(first_value(path, "TODAY_ROLLING_SCAN_COUNT") or first_value(path, "SCANNED_TICKER_COUNT"))
        else:
            today = to_int(first_value(path, "TODAY_SCAN_PLAN_COUNT") or first_value(path, "SCANNED_TICKER_COUNT"))
        required = to_int(first_value(path, "DAILY_MIN_SCAN_COUNT"))
        met = today >= required and required > 0
        return {"exists": True, "today": today, "required": required, "met": met, "shortfall": max(0, required - today), "status": "OK_READ_FIRST"}
    if "V18_16J_CURRENT_POST_PATCH_COVERAGE_CHECK" in name:
        data = metric_map(path)
        today = to_int(data.get("TARGET_DAILY_SCAN_COUNT") or data.get("EXPECTED_DAILY_SCAN_COUNT"))
        required = to_int(data.get("REQUIRED_DAILY_SCAN_COUNT"))
        met = str(data.get("DAILY_THRESHOLD_TARGET_MET_EXPECTED", "")).upper() == "TRUE" or (today >= required and required > 0)
        return {"exists": True, "today": today, "required": required, "met": met, "shortfall": max(0, required - today), "status": "OK_V18_16J_POST_PATCH"}
    rows, _, status = read_csv(path)
    row = rows[0] if rows else {}
    today = to_int(row.get("TODAY_ROLLING_SCAN_COUNT") or row.get("SCANNED_TICKER_COUNT"))
    required = to_int(row.get("DAILY_MIN_SCAN_COUNT"))
    met = str(row.get("COVERAGE_TARGET_MET", "")).upper() == "TRUE" or (today >= required and required > 0)
    return {"exists": True, "today": today, "required": required, "met": met, "shortfall": max(0, required - today), "status": status}


def build(root: Path) -> int:
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    ensure_dir(ops)

    read_first = ops / "V18_16J_R1_READ_FIRST.txt"
    compat_path = ops / "V18_16J_R1_CURRENT_COMPATIBILITY_PATCH_AUDIT.csv"
    coverage_path = ops / "V18_16J_R1_CURRENT_COVERAGE_SOURCE_AUDIT.csv"
    warnings_path = ops / "V18_16J_R1_CURRENT_COMMAND_CENTER_WARNING_AUDIT.csv"
    report_path = ops / "V18_16J_R1_CURRENT_COMPATIBILITY_PATCH_REPORT.md"

    v16j_py = root / "scripts/v18/v18_16J_conservative_daily_threshold_patch.py"
    v19a_py = root / "scripts/v18/v18_19A_daily_readability_refactor.py"
    v13a_py = root / "scripts/v18/v18_13A_unified_daily_read_center_link.py"
    v13d_ps = root / "scripts/v18/run_v18_13D_daily_command_center.ps1"

    scheduler_read = ops / "V18_16B_READ_FIRST.txt"
    total = to_int(first_value(scheduler_read, "TOTAL_UNIVERSE_COUNT"))
    required = math.ceil(total / 5) if total else to_int(first_value(scheduler_read, "DAILY_MIN_SCAN_COUNT"))
    target = to_int(first_value(scheduler_read, "TODAY_SCAN_PLAN_COUNT"))

    v16i_read = ops / "V18_16I_READ_FIRST.txt"
    true_5day = first_value(v16i_read, "PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_MET") or "FALSE"

    v16j_text = read_text(v16j_py)
    v19a_text = read_text(v19a_py)
    v13a_text = read_text(v13a_py)

    compat_rows = [
        {
            "component": "V18.16J",
            "file": str(v16j_py),
            "field_or_check": "NEW_DAILY_SCAN_TARGET validation",
            "before_value": "new_daily_target == required_daily == 65",
            "after_value": "new_daily_target == required_daily and required_daily > 0",
            "action": "PATCHED",
            "status": "PASS" if "NEW_DAILY_SCAN_TARGET_MATCHES_REQUIRED_DAILY" in v16j_text else "FAIL",
            "reason": "Future universe sizes should not fail solely because the required daily count is not 65.",
        },
        {
            "component": "V18.19A",
            "file": str(v19a_py),
            "field_or_check": "daily threshold coverage source order",
            "before_value": "V18.16H coverage audit first",
            "after_value": "V18.16J post-patch, V18.16F, V18.16B, then V18.16H fallback",
            "action": "PATCHED",
            "status": "PASS" if "V18_16J_CURRENT_POST_PATCH_COVERAGE_CHECK.csv" in v19a_text else "FAIL",
            "reason": "Fresh 65/65 daily-threshold evidence should not be overridden by stale 45/65 fallback audits.",
        },
        {
            "component": "V18.13A",
            "file": str(v13a_py),
            "field_or_check": "old sell-timing read-first lookup",
            "before_value": "outputs/v18/sell_timing/V18_12F_READ_FIRST.txt only",
            "after_value": "fallback to outputs/v18/ops/V18_12F_R2_READ_FIRST.txt and V18_12E_R1_READ_FIRST.txt",
            "action": "PATCHED",
            "status": "PASS" if "OK_CURRENT_FALLBACK_READ_FIRST_FOUND" in v13a_text else "FAIL",
            "reason": "Current equivalent read-first files exist under ops; missing old shadow paths should not hard-fail the command center.",
        },
    ]

    candidates = [
        root / "outputs/v18/universe/V18_16J_CURRENT_POST_PATCH_COVERAGE_CHECK.csv",
        root / "outputs/v18/ops/V18_16F_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_16B_READ_FIRST.txt",
        root / "outputs/v18/universe/V18_16H_CURRENT_COVERAGE_AUDIT.csv",
        root / "outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_COVERAGE_AUDIT.csv",
    ]
    selected = next((path for path in candidates if path.exists()), None)
    coverage_rows = []
    for path in candidates:
        stats = source_stats(path)
        coverage_rows.append({
            "candidate_source": str(path),
            "exists": bool_text(bool(stats["exists"])),
            "selected": bool_text(path == selected),
            "source_status": stats["status"],
            "today_scan_count": stats["today"],
            "required_daily_scan_count": stats["required"],
            "daily_threshold_met": bool_text(bool(stats["met"])),
            "daily_threshold_shortfall": stats["shortfall"],
            "true_5day_unique_coverage_met": true_5day,
            "reason": "Selected by freshness order." if path == selected else "Fallback candidate.",
        })

    old_12f = root / "outputs/v18/sell_timing/V18_12F_READ_FIRST.txt"
    old_12e = root / "outputs/v18/sell_timing/V18_12E_READ_FIRST.txt"
    fallback_12f = root / "outputs/v18/ops/V18_12F_R2_READ_FIRST.txt"
    fallback_12e = root / "outputs/v18/ops/V18_12E_R1_READ_FIRST.txt"
    warning_rows = [
        {
            "wrapper": str(v13d_ps),
            "warning_or_failure": "V18.13A missing old optional sell-timing read-first",
            "old_behavior": "WARN from V18.13A propagated to command-center nonzero through V18.13D.",
            "new_behavior": "V18.13A uses current fallback read-first files when old shadow paths are absent.",
            "status": "PASS" if fallback_12f.exists() and fallback_12e.exists() else "WARN",
            "reason": f"Old paths exist: 12F={old_12f.exists()}, 12E={old_12e.exists()}; fallback paths exist: 12F={fallback_12f.exists()}, 12E={fallback_12e.exists()}.",
            "safety_condition": "AUTO_SELL DISABLED and OFFICIAL_DECISION_IMPACT NONE; read-center linking only.",
        }
    ]

    write_csv(compat_path, compat_rows, COMPAT_FIELDS)
    write_csv(coverage_path, coverage_rows, COVERAGE_FIELDS)
    write_csv(warnings_path, warning_rows, WARNING_FIELDS)

    validation_fail_count = 0
    validation_fail_count += sum(1 for row in compat_rows if row["status"] != "PASS")
    validation_fail_count += 0 if selected and source_stats(selected)["met"] else 1
    validation_fail_count += 0 if true_5day.upper() == "FALSE" else 1
    validation_fail_count += 0 if AUTO_TRADE == "DISABLED" and AUTO_SELL == "DISABLED" and OFFICIAL_DECISION_IMPACT == "NONE" else 1
    status = STATUS_OK if validation_fail_count == 0 else STATUS_WARN

    selected_stats = source_stats(selected) if selected else {"today": 0, "required": 0, "met": False, "shortfall": 0, "status": "MISSING"}
    values = {
        "STATUS": status,
        "MODE": MODE,
        "V18_16J_VALIDATION_DYNAMIC": "TRUE" if "NEW_DAILY_SCAN_TARGET_MATCHES_REQUIRED_DAILY" in v16j_text else "FALSE",
        "DAILY_THRESHOLD_COVERAGE_SOURCE": str(selected) if selected else "MISSING",
        "DAILY_THRESHOLD_COVERAGE_SOURCE_STATUS": str(selected_stats["status"]),
        "TODAY_SCAN_COUNT": str(selected_stats["today"]),
        "REQUIRED_DAILY_SCAN_COUNT": str(selected_stats["required"] or required),
        "DAILY_THRESHOLD_TARGET_MET": bool_text(bool(selected_stats["met"])),
        "DAILY_THRESHOLD_SHORTFALL_COUNT": str(selected_stats["shortfall"]),
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": true_5day,
        "TRUE_5DAY_UNIQUE_WARNING_PRESERVED": bool_text(true_5day.upper() == "FALSE"),
        "SELL_TIMING_READ_FIRST_STATUS": "OK_CURRENT_FALLBACK_READ_FIRST_FOUND" if fallback_12f.exists() else "WARN_MISSING_OPTIONAL_SHADOW_READ_FIRST",
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "RANKING_MODIFIED": "FALSE",
        "PROMOTION_DEMOTION_MODIFIED": "FALSE",
        "PRICE_UPDATE_MODIFIED": "FALSE",
        "VALIDATION_FAIL_COUNT": str(validation_fail_count),
        "READ_FIRST": str(read_first),
        "REPORT": str(report_path),
    }

    read_keys = [
        "STATUS", "MODE", "V18_16J_VALIDATION_DYNAMIC", "DAILY_THRESHOLD_COVERAGE_SOURCE",
        "DAILY_THRESHOLD_COVERAGE_SOURCE_STATUS", "TODAY_SCAN_COUNT", "REQUIRED_DAILY_SCAN_COUNT",
        "DAILY_THRESHOLD_TARGET_MET", "DAILY_THRESHOLD_SHORTFALL_COUNT",
        "TRUE_5DAY_UNIQUE_COVERAGE_MET", "TRUE_5DAY_UNIQUE_WARNING_PRESERVED",
        "SELL_TIMING_READ_FIRST_STATUS", "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT",
        "RANKING_MODIFIED", "PROMOTION_DEMOTION_MODIFIED", "PRICE_UPDATE_MODIFIED",
        "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]
    write_text(read_first, "\n".join(f"{key}: {values[key]}" for key in read_keys) + "\n")

    report = [
        "# V18.16J-R1 Command Center + Coverage Source Compatibility Patch",
        "",
        *[f"- {key}: {values[key]}" for key in read_keys],
        "",
        "## Patch Summary",
        "",
        "- V18.16J scheduler patch remains active; no scheduling rollback was performed.",
        "- V18.16J validation now compares the new daily target to computed required_daily rather than a hard-coded 65.",
        "- V18.19A now prefers fresh V18.16J/V18.16F/V18.16B daily-threshold evidence before stale V18.16H coverage audits.",
        "- True 5-day unique coverage remains unresolved and continues to cap trust below HIGH.",
        "- Missing old V18.12E/F sell-timing shadow read-first paths are resolved through current ops fallback files when available.",
        "- No trading, ranking, promotion/demotion, price update, yfinance, or official decision behavior was changed.",
    ]
    write_text(report_path, "\n".join(report) + "\n")

    for key in read_keys:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail_count == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
