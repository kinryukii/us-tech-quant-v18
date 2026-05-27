from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, List, Sequence


STATUS_OK = "OK_V18_16J_R2_COVERAGE_SOURCE_FRESHNESS_PATCH_READY"
STATUS_WARN = "WARN_V18_16J_R2_COVERAGE_SOURCE_FRESHNESS_PATCH_CHECK_FAILED"
MODE = "COVERAGE_SOURCE_FRESHNESS_PATCH"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

AUDIT_FIELDS = [
    "candidate_source",
    "exists",
    "modified_time",
    "parse_status",
    "valid_daily_threshold_evidence",
    "selected",
    "today_scan_count",
    "required_daily_scan_count",
    "daily_threshold_met",
    "daily_threshold_shortfall",
    "stale_vs_selected",
    "reason",
]


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


def read_csv(path: Path) -> tuple[List[Dict[str, str]], str]:
    if not path.exists():
        return [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f)), "OK"
        except Exception:
            pass
    return [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def first_value(path: Path, key: str) -> str:
    target = key.upper()
    for raw in read_text(path).splitlines():
        if ":" not in raw:
            continue
        left, right = raw.split(":", 1)
        if left.strip().lstrip("- ").strip().upper() == target:
            return right.strip()
    return ""


def read_first_map(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for raw in read_text(path).splitlines():
        if ":" not in raw:
            continue
        left, right = raw.split(":", 1)
        data[left.strip().lstrip("- ").strip().upper()] = right.strip()
    return data


def to_int(value: object) -> int:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return 0
    try:
        return int(float(text))
    except Exception:
        return 0


def bool_text(value: bool) -> str:
    return str(bool(value)).upper()


def safe_bool(value: object, fallback: bool = False) -> bool:
    text = str(value or "").strip().upper()
    if text in {"TRUE", "YES", "1", "Y"}:
        return True
    if text in {"FALSE", "NO", "0", "N"}:
        return False
    return fallback


def metric_map(rows: Sequence[Dict[str, str]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for row in rows:
        metric = str(row.get("metric", "")).strip().upper()
        if metric:
            out[metric] = str(row.get("value", "")).strip()
    return out


def candidates(root: Path) -> List[Path]:
    return [
        root / "outputs/v18/ops/V18_16F_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_16B_READ_FIRST.txt",
        root / "outputs/v18/universe/V18_16J_CURRENT_POST_PATCH_COVERAGE_CHECK.csv",
        root / "outputs/v18/universe/V18_16H_CURRENT_COVERAGE_AUDIT.csv",
        root / "outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_COVERAGE_AUDIT.csv",
    ]


def inspect_candidate(path: Path) -> Dict[str, object]:
    exists = path.exists()
    modified = path.stat().st_mtime if exists else 0.0
    modified_text = dt.datetime.fromtimestamp(modified).isoformat(timespec="seconds") if exists else ""
    row: Dict[str, object] = {
        "candidate_source": str(path),
        "exists": bool_text(exists),
        "modified_epoch": modified,
        "modified_time": modified_text,
        "parse_status": "MISSING",
        "valid_daily_threshold_evidence": "FALSE",
        "selected": "FALSE",
        "today_scan_count": 0,
        "required_daily_scan_count": 0,
        "daily_threshold_met": "FALSE",
        "daily_threshold_shortfall": 0,
        "stale_vs_selected": "",
        "reason": "Source missing.",
    }
    if not exists:
        return row

    name = path.name.upper()
    if name.endswith(".TXT"):
        data = read_first_map(path)
        if not data:
            row.update({"parse_status": "WARN_EMPTY", "reason": "Read-first file had no parsed key/value fields."})
            return row
        today = to_int(data.get("TODAY_ROLLING_SCAN_COUNT") or data.get("SCANNED_TICKER_COUNT") or data.get("TODAY_SCAN_PLAN_COUNT"))
        required = to_int(data.get("DAILY_MIN_SCAN_COUNT"))
        valid = today > 0 and required > 0
        row.update({
            "parse_status": "OK_READ_FIRST",
            "valid_daily_threshold_evidence": bool_text(valid),
            "today_scan_count": today,
            "required_daily_scan_count": required,
            "daily_threshold_met": bool_text(valid and today >= required),
            "daily_threshold_shortfall": max(0, required - today) if valid else 0,
            "reason": "Valid read-first daily-threshold evidence." if valid else "Missing scan count or required daily count.",
        })
        return row

    rows, status = read_csv(path)
    row["parse_status"] = status
    if status != "OK" or not rows:
        row["reason"] = "CSV source could not be parsed or had no rows."
        return row
    if "V18_16J_CURRENT_POST_PATCH_COVERAGE_CHECK" in name:
        data = metric_map(rows)
        today = to_int(data.get("TARGET_DAILY_SCAN_COUNT") or data.get("EXPECTED_DAILY_SCAN_COUNT"))
        required = to_int(data.get("REQUIRED_DAILY_SCAN_COUNT"))
        met = safe_bool(data.get("DAILY_THRESHOLD_TARGET_MET_EXPECTED"), today >= required if required else False)
    else:
        first = rows[0]
        today = to_int(first.get("TODAY_ROLLING_SCAN_COUNT") or first.get("SCANNED_TICKER_COUNT"))
        required = to_int(first.get("DAILY_MIN_SCAN_COUNT"))
        met = safe_bool(first.get("COVERAGE_TARGET_MET"), today >= required if required else False)
    valid = today > 0 and required > 0
    row.update({
        "valid_daily_threshold_evidence": bool_text(valid),
        "today_scan_count": today,
        "required_daily_scan_count": required,
        "daily_threshold_met": bool_text(valid and met),
        "daily_threshold_shortfall": max(0, required - today) if valid else 0,
        "reason": "Valid CSV daily-threshold evidence." if valid else "Missing scan count or required daily count.",
    })
    return row


def build(root: Path) -> int:
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    ensure_dir(ops)
    read_first = ops / "V18_16J_R2_READ_FIRST.txt"
    audit_path = ops / "V18_16J_R2_CURRENT_COVERAGE_SOURCE_FRESHNESS_AUDIT.csv"
    report_path = ops / "V18_16J_R2_CURRENT_COVERAGE_SOURCE_FRESHNESS_REPORT.md"

    rows = [inspect_candidate(path) for path in candidates(root)]
    valid = [row for row in rows if row["valid_daily_threshold_evidence"] == "TRUE"]
    selected = max(valid, key=lambda row: float(row["modified_epoch"])) if valid else None
    selected_epoch = float(selected["modified_epoch"]) if selected else 0.0
    for row in rows:
        is_selected = selected is not None and row["candidate_source"] == selected["candidate_source"]
        row["selected"] = bool_text(is_selected)
        if selected is None:
            row["stale_vs_selected"] = "NO_VALID_SELECTED"
        elif is_selected:
            row["stale_vs_selected"] = "SELECTED_NEWEST_VALID"
        elif row["valid_daily_threshold_evidence"] != "TRUE":
            row["stale_vs_selected"] = "SKIPPED_INVALID"
        elif float(row["modified_epoch"]) < selected_epoch:
            row["stale_vs_selected"] = "OLDER_THAN_SELECTED"
        else:
            row["stale_vs_selected"] = "NOT_NEWER_THAN_SELECTED"
        row.pop("modified_epoch", None)

    write_csv(audit_path, rows, AUDIT_FIELDS)

    true_5day = first_value(root / "outputs/v18/ops/V18_16I_READ_FIRST.txt", "PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_MET") or "FALSE"
    selected_source = str(selected["candidate_source"]) if selected else "MISSING"
    selected_modified = str(selected["modified_time"]) if selected else ""
    selected_today = str(selected["today_scan_count"]) if selected else "0"
    selected_required = str(selected["required_daily_scan_count"]) if selected else "0"
    selected_met = str(selected["daily_threshold_met"]) if selected else "FALSE"
    selected_shortfall = str(selected["daily_threshold_shortfall"]) if selected else "0"

    validation_fail_count = 0
    if selected is None:
        validation_fail_count += 1
    if selected_met != "TRUE":
        validation_fail_count += 1
    if true_5day.upper() != "FALSE":
        validation_fail_count += 1
    status = STATUS_OK if validation_fail_count == 0 else STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": MODE,
        "SELECTED_COVERAGE_SOURCE": selected_source,
        "SELECTED_SOURCE_MODIFIED_TIME": selected_modified,
        "DAILY_THRESHOLD_TARGET_MET": selected_met,
        "TODAY_SCAN_COUNT": selected_today,
        "REQUIRED_DAILY_SCAN_COUNT": selected_required,
        "DAILY_THRESHOLD_SHORTFALL_COUNT": selected_shortfall,
        "TRUE_5DAY_UNIQUE_COVERAGE_MET": true_5day,
        "TRUE_5DAY_UNIQUE_WARNING_PRESERVED": bool_text(true_5day.upper() == "FALSE"),
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
    keys = [
        "STATUS", "MODE", "SELECTED_COVERAGE_SOURCE", "SELECTED_SOURCE_MODIFIED_TIME",
        "DAILY_THRESHOLD_TARGET_MET", "TODAY_SCAN_COUNT", "REQUIRED_DAILY_SCAN_COUNT",
        "DAILY_THRESHOLD_SHORTFALL_COUNT", "TRUE_5DAY_UNIQUE_COVERAGE_MET",
        "TRUE_5DAY_UNIQUE_WARNING_PRESERVED", "AUTO_TRADE", "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT", "RANKING_MODIFIED", "PROMOTION_DEMOTION_MODIFIED",
        "PRICE_UPDATE_MODIFIED", "VALIDATION_FAIL_COUNT", "READ_FIRST", "REPORT",
    ]
    write_text(read_first, "\n".join(f"{key}: {values[key]}" for key in keys) + "\n")

    skipped = [row for row in rows if row["selected"] != "TRUE"]
    report = [
        "# V18.16J-R2 Coverage Source Freshness Patch",
        "",
        *[f"- {key}: {values[key]}" for key in keys],
        "",
        "## Selection",
        "",
        f"- Selected source: {selected_source}",
        f"- Selected modified time: {selected_modified}",
        "- Selection rule: newest source with valid daily-threshold evidence.",
        "- True 5-day unique coverage remains a separate unresolved warning.",
        "",
        "## Skipped Sources",
        "",
        *[f"- {row['candidate_source']}: {row['stale_vs_selected']} ({row['reason']})" for row in skipped],
    ]
    write_text(report_path, "\n".join(report) + "\n")

    for key in keys:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail_count == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
