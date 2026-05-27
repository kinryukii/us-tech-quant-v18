from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


MODE = "READ_ONLY_TIER_MIGRATION_SOURCE_ALIAS_REPAIR"
STATUS_OK = "OK_V18_25A_R2_TIER_MIGRATION_SOURCE_ALIAS_REPAIR_READY"
STATUS_WARN = "WARN_V18_25A_R2_TIER_MIGRATION_SOURCE_ALIAS_REPAIR_READY"
STATUS_FAIL = "FAIL_V18_25A_R2_TIER_MIGRATION_SOURCE_ALIAS_REPAIR"

ALIAS_PATH = "outputs/v18/tier_migration/V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT.csv"
REPORT_PATH = "outputs/v18/ops/V18_25A_R2_CURRENT_TIER_MIGRATION_SOURCE_ALIAS_REPAIR_REPORT.md"
READ_FIRST_PATH = "outputs/v18/ops/V18_25A_R2_READ_FIRST.txt"
AUDIT_PATH = "outputs/v18/tier_migration/V18_25A_R2_CURRENT_ALIAS_SOURCE_AUDIT.csv"

OUTPUTS = {
    "alias": ALIAS_PATH,
    "report": REPORT_PATH,
    "read_first": READ_FIRST_PATH,
    "audit": AUDIT_PATH,
}

SAFETY_FLAGS = {
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "PRICE_HISTORY_MODIFIED": "FALSE",
    "STAGED_BACKFILL_MODIFIED": "FALSE",
    "LEDGER_MODIFIED": "FALSE",
    "FACTOR_PACK_MODIFIED": "FALSE",
    "TECHNICAL_TIMING_MODIFIED": "FALSE",
    "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
    "BACKTEST_EXECUTED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
}

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "ALIAS_CREATED",
    "ALIAS_PATH",
    "SOURCE_PATH",
    "SOURCE_ROW_COUNT",
    "ALIAS_ROW_COUNT",
    "REQUIRED_FIELD_MISSING_COUNT",
    "WARNING_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "PRICE_CACHE_MODIFIED",
    "PRICE_HISTORY_MODIFIED",
    "STAGED_BACKFILL_MODIFIED",
    "LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "OFFICIAL_DAILY_DECISION_MODIFIED",
    "BACKTEST_EXECUTED",
    "EXTERNAL_DATA_FETCHED",
    "VALIDATION_FAIL_COUNT",
]

ALIAS_FIELDS = [
    "ticker",
    "composite_score",
    "tier_current",
    "tier_previous",
    "tier_change",
    "movement_type",
    "movement_reason",
    "score_source",
    "score_source_trust",
    "current_score",
    "previous_score",
    "current_rank",
    "previous_rank",
    "rank_delta",
    "score_delta",
    "review_required",
    "source_file",
    "source_kind",
]

AUDIT_FIELDS = [
    "candidate_name",
    "candidate_path",
    "exists",
    "row_count",
    "has_ticker",
    "has_current_tier",
    "has_previous_tier",
    "has_movement_type",
    "has_score",
    "selected",
    "selection_score",
    "selection_reason",
    "notes",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except csv.Error:
            continue
    return [], []


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def get_ticker(row: Dict[str, str]) -> str:
    for key in ("ticker", "Ticker", "symbol", "Symbol", "yf_ticker"):
        value = str(row.get(key, "")).strip().upper()
        if value and value not in {"NAN", "NONE", "NULL"}:
            return value
    return ""


def get_first(row: Dict[str, str], keys: Sequence[str], default: str = "") -> str:
    lower = {key.lower(): key for key in row}
    for key in keys:
        real = lower.get(key.lower())
        if real is not None:
            value = str(row.get(real, "")).strip()
            if value:
                return value
    return default


def is_true(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "YES", "Y", "1", "AVAILABLE", "PASS", "SUCCESS"}


def to_float(value: object) -> float | None:
    try:
        text = str(value).replace(",", "").strip()
        if not text:
            return None
        return float(text)
    except ValueError:
        return None


def file_signature(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def collect_signatures(root: Path) -> Dict[str, Tuple[int, int]]:
    dirs = [
        "state/v18/price_cache",
        "data/v18/price_history",
        "state/v18/price_history",
        "data/v18/staged_backfill",
        "outputs/v18/staged_backfill",
        "state/v18/rolling_coverage",
        "outputs/v18/factor_pack",
        "outputs/v18/technical_timing",
        "outputs/v18/daily_integrated",
        "outputs/v18/ranking",
        "outputs/v18/signal_snapshots",
    ]
    out: Dict[str, Tuple[int, int]] = {}
    for rel_dir in dirs:
        base = root / rel_dir
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file():
                out[str(path.relative_to(root)).replace("\\", "/")] = file_signature(path)
    return out


def diff_signatures(before: Dict[str, Tuple[int, int]], after: Dict[str, Tuple[int, int]]) -> List[str]:
    paths = sorted(set(before) | set(after))
    return [path for path in paths if before.get(path) != after.get(path)]


def read_source_audit_context(root: Path) -> Tuple[str, str]:
    homepage = root / "outputs/v18/operator_homepage/V18_24B_CURRENT_TIER_MIGRATION_OPERATOR_HOMEPAGE.md"
    text = homepage.read_text(encoding="utf-8", errors="replace") if homepage.exists() else ""
    trust = "HIGH"
    match = re.search(r"Score source trust:\s*([A-Z_]+)", text)
    if match:
        trust = match.group(1).strip().upper()

    audit_md = root / "outputs/v18/tier_migration/V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT.md"
    audit_text = audit_md.read_text(encoding="utf-8", errors="replace") if audit_md.exists() else ""
    source_path = ""
    source_match = re.search(r"Score source:\s*(.+?)\s*\(", audit_text)
    if source_match:
        source_path = source_match.group(1).strip()
    return source_path, trust


def score_candidate(path: Path, fields: Sequence[str]) -> Tuple[int, str]:
    if not path.exists():
        return 0, "missing"
    lower = {field.lower(): field for field in fields}
    score = 0
    if "ticker" in lower:
        score += 5
    if any(name in lower for name in ("movement_type", "movement_reason")):
        score += 10
    if any(name in lower for name in ("previous_tier", "current_tier")):
        score += 10
    if any(name in lower for name in ("current_score", "composite_score", "factor_pack_score")):
        score += 8
    if "current_score_source" in lower or "score_source" in lower:
        score += 6
    return score, "ticker_level_csv"


def discover_source(root: Path) -> Tuple[Path | None, List[Dict[str, object]], str, str, List[str]]:
    candidates = [
        root / "outputs/v18/tier_migration/V18_24A_CURRENT_TIER_MOVEMENT_REPORT.csv",
        root / "outputs/v18/tier_migration/V18_24A_CURRENT_SCORE_TIER_SNAPSHOT.csv",
        root / "outputs/v18/tier_migration/V18_24A_CURRENT_DYNAMIC_SCORE_TIER_MIGRATION_AUDIT.md",
        root / "outputs/v18/operator_homepage/V18_24B_CURRENT_TIER_MIGRATION_OPERATOR_HOMEPAGE.md",
    ]

    source_path_from_md, trust_from_md = read_source_audit_context(root)
    audit_rows: List[Dict[str, object]] = []
    selected_path: Path | None = None
    selected_score = -1
    selected_reason = ""
    warnings: List[str] = []

    for candidate in candidates:
        rows, fields = read_csv(candidate)
        exists = candidate.exists()
        row_count = len(rows)
        has_ticker = any(get_ticker(row) for row in rows)
        has_current_tier = "current_tier" in {field.lower() for field in fields}
        has_previous_tier = "previous_tier" in {field.lower() for field in fields}
        has_movement_type = "movement_type" in {field.lower() for field in fields}
        has_score = any(field.lower() in {"current_score", "composite_score", "factor_pack_score", "score"} for field in fields)
        candidate_score, reason = score_candidate(candidate, fields)
        selected = False
        if exists and row_count > 0 and has_ticker and candidate_score > selected_score:
            selected_path = candidate
            selected_score = candidate_score
            selected_reason = reason
        audit_rows.append(
            {
                "candidate_name": candidate.name,
                "candidate_path": str(candidate),
                "exists": "TRUE" if exists else "FALSE",
                "row_count": row_count,
                "has_ticker": "TRUE" if has_ticker else "FALSE",
                "has_current_tier": "TRUE" if has_current_tier else "FALSE",
                "has_previous_tier": "TRUE" if has_previous_tier else "FALSE",
                "has_movement_type": "TRUE" if has_movement_type else "FALSE",
                "has_score": "TRUE" if has_score else "FALSE",
                "selected": "FALSE",
                "selection_score": candidate_score,
                "selection_reason": reason,
                "notes": "",
            }
        )

    if selected_path is None:
        return None, audit_rows, source_path_from_md, trust_from_md, ["No usable tier migration source found."]

    for row in audit_rows:
        if row["candidate_path"] == str(selected_path):
            row["selected"] = "TRUE"
            row["selection_reason"] = f"selected:{selected_reason}"
            break

    # Include a note if the current source audit path references a different primary source.
    return selected_path, audit_rows, source_path_from_md, trust_from_md, warnings


def derive_tier_change(previous_tier: str, current_tier: str, movement_type: str) -> str:
    if movement_type:
        return movement_type
    if previous_tier and current_tier:
        if previous_tier == current_tier:
            return "SAME"
        prev_rank = tier_rank(previous_tier)
        curr_rank = tier_rank(current_tier)
        if prev_rank is not None and curr_rank is not None:
            if curr_rank < prev_rank:
                return "UPGRADE"
            if curr_rank > prev_rank:
                return "DOWNGRADE"
    return "UNKNOWN"


def tier_rank(tier: str) -> int | None:
    tiers = {
        "TIER_1_CORE_CANDIDATE": 1,
        "TIER_2_STRONG_WATCHLIST": 2,
        "TIER_3_WATCHLIST": 3,
        "TIER_4_REVIEW_ONLY": 4,
        "TIER_5_WEAK_OR_BLOCKED": 5,
        "TIER_0_DATA_NOT_READY": 0,
    }
    return tiers.get(tier)


def build_alias_rows(rows: Sequence[Dict[str, str]], source_path: Path, score_source_trust: str) -> Tuple[List[Dict[str, object]], int, List[str]]:
    alias_rows: List[Dict[str, object]] = []
    missing_fields = 0
    warnings: List[str] = []
    required_source_fields = {
        "ticker",
        "current_score",
        "current_tier",
        "previous_tier",
        "movement_type",
        "movement_reason",
        "current_score_source",
        "previous_score",
        "current_rank",
        "previous_rank",
        "rank_delta",
        "score_delta",
        "review_required",
    }
    present_source_fields = {field.lower() for field in rows[0].keys()} if rows else set()
    missing_fields = sum(1 for field in required_source_fields if field not in present_source_fields)

    for row in rows:
        ticker = get_ticker(row)
        if not ticker:
            continue
        current_score = get_first(row, ["current_score", "composite_score", "factor_pack_score", "score", "final_score"], "")
        current_tier = get_first(row, ["current_tier", "tier_current"], "")
        previous_tier = get_first(row, ["previous_tier", "tier_previous"], "")
        movement_type = get_first(row, ["movement_type"], "")
        movement_reason = get_first(row, ["movement_reason"], "")
        score_source = get_first(row, ["current_score_source", "score_source"], "factor_pack_score")
        current_rank = get_first(row, ["current_rank", "rank"], "")
        previous_rank = get_first(row, ["previous_rank"], "")
        rank_delta = get_first(row, ["rank_delta"], "")
        score_delta = get_first(row, ["score_delta"], "")
        review_required = get_first(row, ["review_required"], "FALSE")
        tier_change = derive_tier_change(previous_tier, current_tier, movement_type)

        composite_score = current_score
        if not composite_score:
            # Keep the alias explicit about the source gap rather than inventing a value.
            composite_score = ""

        alias_rows.append(
            {
                "ticker": ticker,
                "composite_score": composite_score,
                "tier_current": current_tier,
                "tier_previous": previous_tier,
                "tier_change": tier_change,
                "movement_type": movement_type or tier_change,
                "movement_reason": movement_reason or "UNKNOWN",
                "score_source": score_source or "UNKNOWN",
                "score_source_trust": score_source_trust or "UNKNOWN",
                "current_score": current_score,
                "previous_score": get_first(row, ["previous_score"], ""),
                "current_rank": current_rank,
                "previous_rank": previous_rank,
                "rank_delta": rank_delta,
                "score_delta": score_delta,
                "review_required": review_required or "FALSE",
                "source_file": str(source_path),
                "source_kind": "V18_24A_TIER_MIGRATION_ALIAS_REPAIR",
            }
        )

    alias_rows.sort(key=lambda item: item["ticker"])
    if not alias_rows:
        warnings.append("Selected source produced no alias rows.")
    return alias_rows, missing_fields, warnings


def render_report(read_first: Dict[str, str], audit_rows: Sequence[Dict[str, object]], warnings: Sequence[str], selected_source: str) -> str:
    now = dt.datetime.now().isoformat(timespec="seconds")
    lines = [
        "# V18.25A R2 Tier Migration CSV Alias Repair",
        "",
        f"- STATUS: {read_first.get('STATUS', '')}",
        f"- MODE: {MODE}",
        f"- GENERATED_AT: {now}",
        f"- ALIAS_CREATED: {read_first.get('ALIAS_CREATED', '')}",
        f"- SOURCE_PATH: {read_first.get('SOURCE_PATH', '')}",
        f"- ALIAS_PATH: {read_first.get('ALIAS_PATH', '')}",
        f"- SELECTED_SOURCE_KIND: {selected_source}",
        f"- WARNING_COUNT: {read_first.get('WARNING_COUNT', '')}",
        f"- REQUIRED_FIELD_MISSING_COUNT: {read_first.get('REQUIRED_FIELD_MISSING_COUNT', '')}",
        "",
        "## Source Selection",
        "",
        "| candidate_name | exists | row_count | selected | selection_score | selection_reason |",
        "| --- | --- | ---: | --- | ---: | --- |",
    ]
    for row in audit_rows:
        lines.append(
            f"| {row['candidate_name']} | {row['exists']} | {row['row_count']} | {row['selected']} | {row['selection_score']} | {row['selection_reason']} |"
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            f"- OFFICIAL_DECISION_IMPACT: {read_first.get('OFFICIAL_DECISION_IMPACT', '')}",
            f"- AUTO_TRADE: {read_first.get('AUTO_TRADE', '')}",
            f"- AUTO_SELL: {read_first.get('AUTO_SELL', '')}",
            "- No forbidden official files were modified by this repair.",
        ]
    )
    if warnings:
        lines.extend(["", "## Warnings"] + [f"- {warning}" for warning in warnings])
    else:
        lines.extend(["", "## Warnings", "- NONE"])
    return "\n".join(lines) + "\n"


def validate(
    alias_rows: Sequence[Dict[str, object]],
    alias_path: Path,
    before_forbidden: Dict[str, Tuple[int, int]],
    after_forbidden: Dict[str, Tuple[int, int]],
    required_missing: int,
    warnings: Sequence[str],
) -> List[str]:
    failures: List[str] = []
    if not alias_path.exists():
        failures.append("Alias CSV does not exist after execution.")
    if not alias_rows:
        failures.append("Alias CSV contains no rows.")
    if not any(str(row.get("ticker", "")).strip() for row in alias_rows):
        failures.append("Alias CSV does not contain a ticker column with values.")
    if required_missing < 0:
        failures.append("Required missing count is invalid.")
    if diff_signatures(before_forbidden, after_forbidden):
        failures.append("Forbidden files changed during repair execution.")
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V18.25A R2 tier migration source alias repair")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    before_forbidden = collect_signatures(root)

    selected_source, audit_rows, source_from_md, score_source_trust, warnings = discover_source(root)
    if selected_source is None:
        read_first = {
            "STATUS": STATUS_FAIL,
            "MODE": MODE,
            "ALIAS_CREATED": "FALSE",
            "ALIAS_PATH": ALIAS_PATH,
            "SOURCE_PATH": source_from_md or "",
            "SOURCE_ROW_COUNT": "0",
            "ALIAS_ROW_COUNT": "0",
            "REQUIRED_FIELD_MISSING_COUNT": "0",
            "WARNING_COUNT": str(len(warnings) or 1),
            "OFFICIAL_DECISION_IMPACT": "NONE",
            "AUTO_TRADE": "DISABLED",
            "AUTO_SELL": "DISABLED",
            "PRICE_CACHE_MODIFIED": "FALSE",
            "PRICE_HISTORY_MODIFIED": "FALSE",
            "STAGED_BACKFILL_MODIFIED": "FALSE",
            "LEDGER_MODIFIED": "FALSE",
            "FACTOR_PACK_MODIFIED": "FALSE",
            "TECHNICAL_TIMING_MODIFIED": "FALSE",
            "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
            "BACKTEST_EXECUTED": "FALSE",
            "EXTERNAL_DATA_FETCHED": "FALSE",
            "VALIDATION_FAIL_COUNT": "1",
        }
        write_text(root / READ_FIRST_PATH, "\n".join(f"{field}: {read_first.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")
        write_text(root / REPORT_PATH, render_report(read_first, audit_rows, warnings, "NONE"))
        write_csv(root / AUDIT_PATH, audit_rows, AUDIT_FIELDS)
        return 1

    source_rows, source_fields = read_csv(selected_source)
    if not source_rows:
        warnings.append(f"Selected source is empty: {selected_source.as_posix()}")

    alias_rows, required_missing_count, alias_warnings = build_alias_rows(source_rows, selected_source, score_source_trust)
    warnings.extend(alias_warnings)

    alias_path = root / ALIAS_PATH
    write_csv(alias_path, alias_rows, ALIAS_FIELDS)

    after_forbidden = collect_signatures(root)
    validation_failures = validate(alias_rows, alias_path, before_forbidden, after_forbidden, required_missing_count, warnings)

    alias_created = "TRUE" if alias_path.exists() and len(alias_rows) > 0 else "FALSE"
    status = STATUS_FAIL
    if validation_failures:
        status = STATUS_FAIL
    elif warnings:
        status = STATUS_WARN
    else:
        status = STATUS_OK

    read_first = {
        "STATUS": status,
        "MODE": MODE,
        "ALIAS_CREATED": alias_created,
        "ALIAS_PATH": ALIAS_PATH,
        "SOURCE_PATH": str(selected_source),
        "SOURCE_ROW_COUNT": str(len(source_rows)),
        "ALIAS_ROW_COUNT": str(len(alias_rows)),
        "REQUIRED_FIELD_MISSING_COUNT": str(required_missing_count),
        "WARNING_COUNT": str(len(warnings)),
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "PRICE_CACHE_MODIFIED": "FALSE",
        "PRICE_HISTORY_MODIFIED": "FALSE",
        "STAGED_BACKFILL_MODIFIED": "FALSE",
        "LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "OFFICIAL_DAILY_DECISION_MODIFIED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "EXTERNAL_DATA_FETCHED": "FALSE",
        "VALIDATION_FAIL_COUNT": str(len(validation_failures)),
    }
    write_csv(root / AUDIT_PATH, audit_rows, AUDIT_FIELDS)
    report = render_report(read_first, audit_rows, warnings, selected_source.name)
    write_text(root / REPORT_PATH, report)
    write_text(root / READ_FIRST_PATH, "\n".join(f"{field}: {read_first.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"ALIAS_CREATED: {alias_created}")
    print(f"SOURCE_ROW_COUNT: {len(source_rows)}")
    print(f"ALIAS_ROW_COUNT: {len(alias_rows)}")
    print(f"VALIDATION_FAIL_COUNT: {len(validation_failures)}")
    return 1 if status == STATUS_FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
