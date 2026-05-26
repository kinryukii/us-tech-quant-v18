from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import traceback
from pathlib import Path
from typing import Dict, Tuple


STATUS_OK = "OK_V18_28D_RECOMMENDATION_TIER_RULE_CALIBRATION_READY"
STATUS_WARN = "WARN_V18_28D_RECOMMENDATION_TIER_RULE_CALIBRATION_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_28D_RECOMMENDATION_TIER_RULE_CALIBRATION_ERROR"
MODE = "RECOMMENDATION_TIER_RULE_CALIBRATION_PATCH"

R28B_SCRIPT = "scripts/v18/v18_28B_recommendation_tier_action_layer.py"
R28C_SCRIPT = "scripts/v18/v18_28C_recommendation_tier_calibration_audit.py"
R28B_READ_FIRST = "outputs/v18/ops/V18_28B_READ_FIRST.txt"
R28C_READ_FIRST = "outputs/v18/ops/V18_28C_READ_FIRST.txt"
R28D_READ_FIRST = "outputs/v18/ops/V18_28D_READ_FIRST.txt"
R28D_REPORT = "outputs/v18/read_center/V18_28D_RECOMMENDATION_TIER_RULE_CALIBRATION_REPORT.md"
RECOMMENDATIONS = "outputs/v18/recommendations/V18_CURRENT_RECOMMENDATION_TIERS.csv"

PROTECTED_FILES = [
    "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
    "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv",
    "state/v18/reference/V18_TICKER_THEME_MAP.csv",
    "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
    "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv",
]
PROTECTED_DIRS = [
    "state/v18/price_cache",
    "state/v18/trading",
    "outputs/v18/official_daily",
]

BASELINE = {
    "POSSIBLE_CORE_REVIEW_COUNT": 4,
    "POSSIBLE_WATCHLIST_REVIEW_COUNT": 21,
    "OVERHEAT_RULE_REVIEW_COUNT": 8,
    "VOLATILITY_RULE_REVIEW_COUNT": 13,
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R28B_STATUS_AFTER_PATCH",
    "R28C_STATUS_AFTER_PATCH",
    "R28B_OUTPUT_ROW_COUNT",
    "R28C_INPUT_ROW_COUNT",
    "CORE_CANDIDATE_COUNT_AFTER",
    "WATCHLIST_STRONG_COUNT_AFTER",
    "TACTICAL_ENTRY_COUNT_AFTER",
    "OVERHEATED_WAIT_COUNT_AFTER",
    "SPECULATIVE_SATELLITE_COUNT_AFTER",
    "DO_NOT_PRIORITIZE_COUNT_AFTER",
    "TOP_30_SPECULATIVE_SATELLITE_COUNT_AFTER",
    "TOP_30_OVERHEATED_WAIT_COUNT_AFTER",
    "TOP_30_CORE_CANDIDATE_COUNT_AFTER",
    "POSSIBLE_CORE_REVIEW_COUNT_AFTER",
    "POSSIBLE_WATCHLIST_REVIEW_COUNT_AFTER",
    "OVERHEAT_RULE_REVIEW_COUNT_AFTER",
    "VOLATILITY_RULE_REVIEW_COUNT_AFTER",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "FORBIDDEN_MODIFIED",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def read_first(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else default
    except Exception:
        return default


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def protected_sig(root: Path) -> Dict[str, object]:
    sig: Dict[str, object] = {}
    for rel in PROTECTED_FILES:
        sig[rel] = file_sig(root / rel)
    for rel in PROTECTED_DIRS:
        sig[rel] = tree_sig(root / rel)
    return sig


def load_module(root: Path, rel: str, name: str):
    module_path = root / rel
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def recommendation_duplicate_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        counts: Dict[str, int] = {}
        for row in reader:
            ticker = str(row.get("ticker", "")).strip().upper()
            if ticker:
                counts[ticker] = counts.get(ticker, 0) + 1
    return sum(1 for count in counts.values() if count > 1)


def review_sum(values: Dict[str, str]) -> int:
    return sum(to_int(values.get(key)) for key in BASELINE)


def baseline_sum() -> int:
    return sum(BASELINE.values())


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def build_report(values: Dict[str, object], r28b: Dict[str, str], r28c: Dict[str, str]) -> str:
    lines = [
        "# V18.28D Recommendation Tier Rule Calibration Patch",
        "",
        "## Read First",
        "",
    ]
    lines.extend([f"- {field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS])
    lines.extend(
        [
            "",
            "## Baseline Versus After",
            "",
            "| metric | before_r28c | after_r28d |",
            "| --- | --- | --- |",
        ]
    )
    for key, before in BASELINE.items():
        lines.append(f"| {key} | {before} | {r28c.get(key, '')} |")
    lines.extend(
        [
            "",
            "## Calibration Notes",
            "",
            "- R28B now treats HIGH volatility as a risk label and reason code, not an automatic SPECULATIVE_SATELLITE downgrade.",
            "- EXTREME volatility remains strict.",
            "- OVERHEATED_WAIT now requires strong technical overheat evidence.",
            "- ETF/macro and DEFENSIVE_HEDGE priority remain unchanged.",
            "- This patch regenerates advisory outputs only; it has no official decision or trading impact.",
        ]
    )
    return "\n".join(lines) + "\n"


def run(root: Path) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)

    r28b_module = load_module(root, R28B_SCRIPT, "v18_28B_recommendation_tier_action_layer")
    r28c_module = load_module(root, R28C_SCRIPT, "v18_28C_recommendation_tier_calibration_audit")
    r28b_module.run(root)
    r28c_module.run(root)

    r28b = read_first(root / R28B_READ_FIRST)
    r28c = read_first(root / R28C_READ_FIRST)
    forbidden_modified = protected_sig(root) != protected_before
    duplicate_count = recommendation_duplicate_count(root / RECOMMENDATIONS)
    unknown_count = to_int(r28c.get("UNKNOWN_PRIMARY_THEME_COUNT"))
    missing_tier = to_int(r28c.get("MISSING_RECOMMENDATION_TIER_COUNT"))
    missing_action = to_int(r28c.get("MISSING_RECOMMENDATION_ACTION_COUNT"))
    output_count = to_int(r28b.get("OUTPUT_RECOMMENDATION_ROW_COUNT"))
    review_improved = review_sum(r28c) < baseline_sum()
    review_remaining = review_sum(r28c) > 0

    if (
        r28b.get("STATUS") != "OK_V18_28B_RECOMMENDATION_TIERS_READY"
        or output_count != 252
        or duplicate_count
        or unknown_count
        or missing_tier
        or missing_action
        or forbidden_modified
    ):
        status = STATUS_FAIL
    elif review_remaining:
        status = STATUS_WARN
    elif review_improved:
        status = STATUS_OK
    else:
        status = STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R28B_STATUS_AFTER_PATCH": r28b.get("STATUS", ""),
        "R28C_STATUS_AFTER_PATCH": r28c.get("STATUS", ""),
        "R28B_OUTPUT_ROW_COUNT": output_count,
        "R28C_INPUT_ROW_COUNT": r28c.get("INPUT_RECOMMENDATION_ROW_COUNT", ""),
        "CORE_CANDIDATE_COUNT_AFTER": r28b.get("CORE_CANDIDATE_COUNT", ""),
        "WATCHLIST_STRONG_COUNT_AFTER": r28b.get("WATCHLIST_STRONG_COUNT", ""),
        "TACTICAL_ENTRY_COUNT_AFTER": r28b.get("TACTICAL_ENTRY_COUNT", ""),
        "OVERHEATED_WAIT_COUNT_AFTER": r28b.get("OVERHEATED_WAIT_COUNT", ""),
        "SPECULATIVE_SATELLITE_COUNT_AFTER": r28b.get("SPECULATIVE_SATELLITE_COUNT", ""),
        "DO_NOT_PRIORITIZE_COUNT_AFTER": r28b.get("DO_NOT_PRIORITIZE_COUNT", ""),
        "TOP_30_SPECULATIVE_SATELLITE_COUNT_AFTER": r28c.get("TOP_30_SPECULATIVE_SATELLITE_COUNT", ""),
        "TOP_30_OVERHEATED_WAIT_COUNT_AFTER": r28c.get("TOP_30_OVERHEATED_WAIT_COUNT", ""),
        "TOP_30_CORE_CANDIDATE_COUNT_AFTER": r28c.get("TOP_30_CORE_CANDIDATE_COUNT", ""),
        "POSSIBLE_CORE_REVIEW_COUNT_AFTER": r28c.get("POSSIBLE_CORE_REVIEW_COUNT", ""),
        "POSSIBLE_WATCHLIST_REVIEW_COUNT_AFTER": r28c.get("POSSIBLE_WATCHLIST_REVIEW_COUNT", ""),
        "OVERHEAT_RULE_REVIEW_COUNT_AFTER": r28c.get("OVERHEAT_RULE_REVIEW_COUNT", ""),
        "VOLATILITY_RULE_REVIEW_COUNT_AFTER": r28c.get("VOLATILITY_RULE_REVIEW_COUNT", ""),
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "TRUE" if forbidden_modified else "FALSE",
    }
    write_read_first(root / R28D_READ_FIRST, values)
    write_text(root / R28D_REPORT, build_report(values, r28b, r28c))

    if status == STATUS_FAIL:
        raise RuntimeError(f"R28D calibration patch failed validation checks: {values}")
    return values


def write_failure(root: Path, error: BaseException) -> None:
    values = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "R28B_STATUS_AFTER_PATCH": read_first(root / R28B_READ_FIRST).get("STATUS", ""),
        "R28C_STATUS_AFTER_PATCH": read_first(root / R28C_READ_FIRST).get("STATUS", ""),
        "R28B_OUTPUT_ROW_COUNT": "",
        "R28C_INPUT_ROW_COUNT": "",
        "CORE_CANDIDATE_COUNT_AFTER": "",
        "WATCHLIST_STRONG_COUNT_AFTER": "",
        "TACTICAL_ENTRY_COUNT_AFTER": "",
        "OVERHEATED_WAIT_COUNT_AFTER": "",
        "SPECULATIVE_SATELLITE_COUNT_AFTER": "",
        "DO_NOT_PRIORITIZE_COUNT_AFTER": "",
        "TOP_30_SPECULATIVE_SATELLITE_COUNT_AFTER": "",
        "TOP_30_OVERHEATED_WAIT_COUNT_AFTER": "",
        "TOP_30_CORE_CANDIDATE_COUNT_AFTER": "",
        "POSSIBLE_CORE_REVIEW_COUNT_AFTER": "",
        "POSSIBLE_WATCHLIST_REVIEW_COUNT_AFTER": "",
        "OVERHEAT_RULE_REVIEW_COUNT_AFTER": "",
        "VOLATILITY_RULE_REVIEW_COUNT_AFTER": "",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "FALSE",
    }
    write_read_first(root / R28D_READ_FIRST, values)
    write_text(root / R28D_REPORT, f"# V18.28D Calibration Patch Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.28D recommendation tier rule calibration patch.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        values = run(root)
        print(f"STATUS: {values['STATUS']}")
        print(f"READ_FIRST: {root / R28D_READ_FIRST}")
        return 0
    except Exception as exc:
        write_failure(root, exc)
        print(f"STATUS: {STATUS_FAIL}")
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
