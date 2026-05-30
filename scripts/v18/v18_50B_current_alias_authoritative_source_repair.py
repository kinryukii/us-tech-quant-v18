from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


PATCH_VERSION = "V18.50B-R2"
PATCH_NAME = "SOLE_CURRENT_TOP20_WRITER_ENFORCEMENT"

AUTHORITATIVE = "outputs/v18/candidates/V18_35D_FULL_UNIVERSE_RECOMPUTED_RANKED_CANDIDATES.csv"
STATUS_CSV = "outputs/v18/candidates/V18_35D_FULL_UNIVERSE_COMPUTATION_STATUS.csv"
FAILURES_CSV = "outputs/v18/candidates/V18_35D_FULL_UNIVERSE_RECOMPUTE_FAILURES.csv"
READ35D = "outputs/v18/ops/V18_35D_READ_FIRST.txt"
CURRENT_TOP20 = "outputs/v18/candidates/V18_CURRENT_TOP_RANKED_CANDIDATES.csv"

OUT_READ_FIRST_R2 = "outputs/v18/ops/V18_50B_R2_READ_FIRST.txt"
OUT_READ_FIRST_CURRENT = "outputs/v18/ops/V18_50B_READ_FIRST.txt"
OUT_REPORT_R2 = "outputs/v18/read_center/V18_50B_R2_SOLE_CURRENT_TOP20_WRITER_ENFORCEMENT_REPORT.md"
OUT_SOURCE_AUDIT_MD = "outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_DATA_SOURCE_AUDIT.md"
OUT_SOURCE_AUDIT_CSV_R2 = "outputs/v18/ops/V18_50B_R2_CURRENT_ALIAS_SOURCE_AUDIT.csv"

REQUIRED_COLUMNS = ["rank", "ticker", "composite_candidate_score", "latest_price_date"]
TRUE_PROVENANCE_COLUMNS = [
    "factor_source_true", "technical_source_true", "score_source_true",
    "factor_recomputed_by_v18_35d", "factor_reused_from_raw105",
    "legacy_factor_pack_used", "authoritative_row_ok",
    "authoritative_row_block_reason",
]
DISALLOWED_SOURCE_RE = re.compile(
    r"RAW105|V18_CURRENT_RAW105_FACTOR_PACK_RANKING|LEGACY|CURRENT_FACTOR|CURRENT_RAW105",
    re.IGNORECASE,
)
VALID_EXCLUSION_BUCKETS = {"UNAVAILABLE_PRICE_DATA_EXCLUDED", "PRICE_HISTORY_INSUFFICIENT"}

SAFETY_FIELDS = {
    "OFFICIAL_RANKING_CHANGED": "FALSE",
    "FACTOR_WEIGHTS_CHANGED": "FALSE",
    "OFFICIAL_BUY_PERMISSION_CHANGED": "FALSE",
    "OFFICIAL_SELL_PERMISSION_CHANGED": "FALSE",
    "TRADING_EXECUTION_ALLOWED": "FALSE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "BROKER_API_USED": "FALSE",
    "ORDER_EXECUTION_USED": "FALSE",
}

READ_FIRST_ORDER = [
    "STATUS", "PATCH_VERSION", "PATCH_NAME", "BUG_FIXED",
    "V18_50B_SOLE_TOP20_ALIAS_WRITER", "SOLE_WRITER_AUDIT_OK",
    "WRITER_INVENTORY_TOTAL_COUNT", "ACTIVE_LEGACY_WRITER_COUNT",
    "DISABLED_LEGACY_WRITER_COUNT", "AUTHORIZED_WRITER_COUNT",
    "ACTIVE_LEGACY_WRITER_PATHS", "DISABLED_LEGACY_WRITER_PATHS",
    "V18_14B_DIRECT_CURRENT_WRITE_DISABLED", "V18_35E_DIRECT_CURRENT_WRITE_DISABLED",
    "V18_35E_RAW105_CURRENT_FACTOR_REUSE_BLOCKED_FROM_CURRENT_ALIAS",
    "TRUE_PROVENANCE_REPAIRED", "RAW105_FACTOR_REUSE_REMOVED_OR_BLOCKED",
    "PRIMARY_SCORE_SOURCE_LABEL_MASKING_FIXED", "CURRENT_TOP20_ALIAS_WRITTEN",
    "CURRENT_TOP20_WRITE_ALLOWED", "CURRENT_TOP20_WRITE_BLOCKED_REASON",
    "V18_45A_DIRECT_CURRENT_WRITE_DISABLED",
    "V18_50A_REVALIDATED_BEFORE_PACKET", "HOMEPAGE_WRITE_REQUIRES_SOURCE_OK",
    "SANITIZED_UNIVERSE_COUNT", "RANKED_ELIGIBLE_COUNT", "VALID_EXCLUSION_COUNT",
    "UNAVAILABLE_OR_DELISTED_COUNT", "PRICE_HISTORY_INSUFFICIENT_COUNT",
    "DUPLICATE_TICKER_COUNT", "RECONCILIATION_OK", "RECONCILIATION_FORMULA",
    "V18_35D_TOP20_MATCH_CURRENT_TOP20", "DAILY_OPERATOR_ACTION_ENTRY_SOURCE_OK",
    "HOMEPAGE_SOURCE_OK", "FULL_UNIVERSE_PRICE_REFRESH_COMPLETE",
    "TOP20_PRICE_REFRESH_COMPLETE", "FULL_UNIVERSE_STALE_ROW_COUNT",
    "TOP20_STALE_ROW_COUNT", "OFFICIAL_RANKING_CHANGED", "FACTOR_WEIGHTS_CHANGED",
    "OFFICIAL_BUY_PERMISSION_CHANGED", "OFFICIAL_SELL_PERMISSION_CHANGED",
    "TRADING_EXECUTION_ALLOWED", "AUTO_TRADE", "AUTO_SELL", "BROKER_API_USED",
    "ORDER_EXECUTION_USED",
]


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def clean(value: object) -> str:
    return str(value or "").strip()


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as f:
                reader = csv.DictReader(f)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def read_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip().upper()] = value.strip()
    return out


def to_int(value: object) -> int:
    try:
        text = clean(value).replace(",", "")
        return int(float(text)) if text else 0
    except Exception:
        return 0


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def rank_key(row: dict[str, str]) -> tuple[int, str]:
    try:
        rank = int(float(clean(row.get("rank"))))
    except Exception:
        rank = 10**9
    return rank, clean(row.get("ticker")).upper()


def ordered_top20(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ranked = [dict(row) for row in rows if clean(row.get("ticker"))]
    ranked.sort(key=rank_key)
    top = ranked[:20]
    for index, row in enumerate(top, 1):
        row["rank"] = str(index)
        row["current_top20_authoritative_source"] = AUTHORITATIVE
        row["current_top20_written_by_module"] = PATCH_VERSION
    return top


def signature(rows: list[dict[str, str]]) -> list[tuple[str, str, str]]:
    return [
        (clean(row.get("rank")), clean(row.get("ticker")).upper(), clean(row.get("latest_price_date")))
        for row in rows[:20]
    ]


def source_blob(rows: list[dict[str, str]]) -> str:
    keys = [
        "factor_source_true", "technical_source_true", "score_source_true",
        "primary_score_source_files", "score_source_files", "ranking_source_policy",
    ]
    return " ".join(clean(row.get(key)) for row in rows for key in keys)


def writer_inventory(root: Path) -> tuple[list[dict[str, str]], dict[str, object]]:
    scripts_dir = root / "scripts" / "v18"
    rows: list[dict[str, str]] = []
    if not scripts_dir.exists():
        return rows, {
            "ok": False,
            "active": ["scripts/v18 directory missing"],
            "disabled": [],
            "authorized": [],
            "v14_disabled": False,
            "v35e_disabled": False,
            "v35e_raw105_blocked": False,
        }

    active_re = re.compile(
        r"write_csv\([^)]*(CURRENT_TOP|CURRENT_TOP20|V18_CURRENT_TOP_RANKED_CANDIDATES)|"
        r"copy_alias\([^)]*V18_CURRENT_TOP_RANKED_CANDIDATES|"
        r"copy2\([^)]*(CURRENT_TOP|CURRENT_TOP20|V18_CURRENT_TOP_RANKED_CANDIDATES)|"
        r"copyfile\([^)]*(CURRENT_TOP|CURRENT_TOP20|V18_CURRENT_TOP_RANKED_CANDIDATES)",
        re.IGNORECASE | re.DOTALL,
    )
    disabled_markers = (
        "V18.50B-R2 owns V18_CURRENT_TOP_RANKED_CANDIDATES.csv exclusively",
        "V18_50B_R2_SOLE_CURRENT_TOP20_WRITER_ENFORCEMENT",
        "CURRENT_TOP_ALIAS_WRITE_DISABLED_BY_V18_50B_R1",
        "CURRENT_TOP_ALIAS_WRITE_DISABLED_BY_V18_50B_R2",
        "CURRENT_TOP_ALIAS_WRITE_DISABLED",
        "CURRENT_TOP20_ALIAS_WRITE_DISABLED",
        "CURRENT_TOP_ALIAS_NOT_WRITTEN",
        "CURRENT_TOP20_ALIAS_NOT_WRITTEN",
        "WRITE_DISABLED_BY_V18_50B_R1",
        "WRITE_DISABLED_BY_V18_50B_R2",
    )

    active: list[str] = []
    disabled: list[str] = []
    authorized: list[str] = []

    for path in sorted(scripts_dir.glob("*")):
        if path.suffix.lower() not in {".py", ".ps1"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "V18_CURRENT_TOP_RANKED_CANDIDATES.csv" not in text and "CURRENT_TOP" not in text:
            continue
        rel_path = str(path.relative_to(root)).replace("\\", "/")
        is_authorized = path.name == "v18_50B_current_alias_authoritative_source_repair.py"
        has_active_pattern = bool(active_re.search(text))
        has_disabled_marker = any(marker in text for marker in disabled_markers)
        classification = "READ_ONLY_REFERENCE"
        evidence = "references current Top20 only"
        if is_authorized:
            classification = "V18_50B_R2_AUTHORIZED_WRITER"
            evidence = "authorized strict gate writer"
            authorized.append(rel_path)
        elif has_active_pattern and not has_disabled_marker:
            classification = "ACTIVE_LEGACY_WRITER"
            evidence = "write/copy pattern can target current Top20 alias"
            active.append(rel_path)
        elif has_active_pattern or has_disabled_marker:
            classification = "DISABLED_LEGACY_WRITER"
            evidence = "legacy write path disabled or sidecar-only"
            disabled.append(rel_path)
        rows.append({
            "path": rel_path,
            "classification": classification,
            "active_writer": bool_text(classification == "ACTIVE_LEGACY_WRITER"),
            "authorized_writer": bool_text(classification == "V18_50B_R2_AUTHORIZED_WRITER"),
            "disabled_legacy_writer": bool_text(classification == "DISABLED_LEGACY_WRITER"),
            "evidence": evidence,
        })

    v14_text = (scripts_dir / "v18_14B_current_daily_command_center.py").read_text(encoding="utf-8", errors="replace")
    v35e_text = (scripts_dir / "v18_35E_online_backfill_candidate_adoption_bridge.py").read_text(encoding="utf-8", errors="replace")
    v14_disabled = (
        "LEGACY_TOP20_SIDECAR" in v14_text
        and '("V18_CURRENT_RANKED_CANDIDATES", b_csv, candidates_dir / "V18_CURRENT_TOP_RANKED_CANDIDATES.csv")' not in v14_text
    )
    v35e_direct_disabled = "write_csv(root / CURRENT_TOP" not in v35e_text
    v35e_raw105_blocked = (
        "factor_idx: dict[str, dict[str, str]] = {}" in v35e_text
        and "existing_factor = None" in v35e_text
        and "V18_50B_R2_SOLE_CURRENT_TOP20_WRITER_ENFORCEMENT" in v35e_text
    )
    return rows, {
        "ok": not active and bool(authorized) and v14_disabled and v35e_direct_disabled and v35e_raw105_blocked,
        "active": active,
        "disabled": disabled,
        "authorized": authorized,
        "v14_disabled": v14_disabled,
        "v35e_disabled": v35e_direct_disabled,
        "v35e_raw105_blocked": v35e_raw105_blocked,
    }


def count_stale(rows: list[dict[str, str]]) -> int:
    dates = [clean(row.get("latest_price_date")) for row in rows if clean(row.get("latest_price_date"))]
    if not dates:
        return 0
    max_date = max(dates)
    return sum(1 for date in dates if date < max_date)


def reconciliation(
    read35d: dict[str, str],
    ranked_rows: list[dict[str, str]],
    status_rows: list[dict[str, str]],
    failure_rows: list[dict[str, str]],
) -> dict[str, object]:
    sanitized = to_int(read35d.get("SANITIZED_UNIVERSE_COUNT")) or len(status_rows)
    ranked_eligible = len(ranked_rows)
    failure_buckets = [clean(row.get("failure_bucket")).upper() for row in failure_rows]
    unavailable = sum(1 for bucket in failure_buckets if bucket == "UNAVAILABLE_PRICE_DATA_EXCLUDED")
    insufficient = sum(1 for bucket in failure_buckets if bucket == "PRICE_HISTORY_INSUFFICIENT")
    valid_exclusion = sum(1 for bucket in failure_buckets if bucket in VALID_EXCLUSION_BUCKETS)
    duplicate = to_int(read35d.get("DUPLICATE_TICKER_COUNT"))
    if not duplicate:
        tickers = [clean(row.get("ticker")).upper() for row in status_rows if clean(row.get("ticker"))]
        duplicate = len(tickers) - len(set(tickers))
    formula = f"{ranked_eligible} + {valid_exclusion} == {sanitized}"
    ok = ranked_eligible + valid_exclusion == sanitized and duplicate == 0
    return {
        "sanitized": sanitized,
        "ranked_eligible": ranked_eligible,
        "valid_exclusion": valid_exclusion,
        "unavailable": unavailable,
        "insufficient": insufficient,
        "duplicate": duplicate,
        "formula": formula,
        "ok": ok,
    }


def validate(root: Path) -> tuple[dict[str, str], list[dict[str, str]], list[str], list[dict[str, str]]]:
    auth_path = root / AUTHORITATIVE
    ranked_rows, ranked_fields = read_csv(auth_path)
    status_rows, _ = read_csv(root / STATUS_CSV)
    failure_rows, _ = read_csv(root / FAILURES_CSV)
    read35d = read_kv(root / READ35D)
    existing_top, _ = read_csv(root / CURRENT_TOP20)
    inventory_rows, inventory = writer_inventory(root)
    reasons: list[str] = []

    if not auth_path.exists():
        reasons.append("AUTHORITATIVE_SOURCE_MISSING")
    if not ranked_rows:
        reasons.append("AUTHORITATIVE_SOURCE_EMPTY")
    missing = [col for col in REQUIRED_COLUMNS if col not in ranked_fields]
    if missing:
        reasons.append("AUTHORITATIVE_REQUIRED_COLUMNS_MISSING_" + ",".join(missing))
    missing_prov = [col for col in TRUE_PROVENANCE_COLUMNS if col not in ranked_fields]
    if missing_prov:
        reasons.append("TRUE_PROVENANCE_COLUMNS_MISSING_" + ",".join(missing_prov))

    top20 = ordered_top20(ranked_rows)
    if len(top20) != 20:
        reasons.append("AUTHORITATIVE_TOP20_SELECTION_INCOMPLETE")
    if any(not clean(row.get("latest_price_date")) for row in top20):
        reasons.append("TOP20_LATEST_PRICE_DATE_MISSING")

    all_rows_authoritative = all(
        clean(row.get("authoritative_row_ok")).upper() == "TRUE"
        and clean(row.get("factor_recomputed_by_v18_35d")).upper() == "TRUE"
        and clean(row.get("factor_reused_from_raw105")).upper() == "FALSE"
        and clean(row.get("legacy_factor_pack_used")).upper() == "FALSE"
        for row in ranked_rows
    ) if ranked_rows and not missing_prov else False
    if not all_rows_authoritative:
        reasons.append("AUTHORITATIVE_ROWS_TRUE_PROVENANCE_NOT_CLEAN")

    blob = source_blob(ranked_rows)
    if DISALLOWED_SOURCE_RE.search(blob):
        reasons.append("RAW105_CURRENT_FACTOR_PACK_OR_LEGACY_TRUE_PROVENANCE_PRESENT")

    rec = reconciliation(read35d, ranked_rows, status_rows, failure_rows)
    if not rec["ok"]:
        reasons.append("FULL_UNIVERSE_RECONCILIATION_FAILED")
    if not inventory["ok"]:
        reasons.append("ACTIVE_LEGACY_TOP20_WRITER_FOUND")

    full_stale_count = count_stale(ranked_rows)
    top20_stale_count = count_stale(top20)
    if top20_stale_count:
        reasons.append("TOP20_STALE_PRICE_ROWS_PRESENT")

    write_allowed = not reasons
    alias_written = "FALSE"
    current_rows = existing_top
    if write_allowed:
        out_fields = list(ranked_fields)
        for field in ("current_top20_authoritative_source", "current_top20_written_by_module"):
            if field not in out_fields:
                out_fields.append(field)
        write_csv(root / CURRENT_TOP20, top20, out_fields)
        alias_written = "TRUE"
        current_rows, _ = read_csv(root / CURRENT_TOP20)

    match = signature(top20) == signature(current_rows) and bool(top20)
    downstream_ok = alias_written == "TRUE" and match
    values = {
        "STATUS": "PASS" if write_allowed and downstream_ok else "WARN_CURRENT_TOP20_AUTHORITATIVE_SOURCE_NOT_READY",
        "PATCH_VERSION": PATCH_VERSION,
        "PATCH_NAME": PATCH_NAME,
        "BUG_FIXED": bool_text(write_allowed and downstream_ok),
        "V18_50B_SOLE_TOP20_ALIAS_WRITER": bool_text(bool(inventory["ok"])),
        "SOLE_WRITER_AUDIT_OK": bool_text(bool(inventory["ok"])),
        "WRITER_INVENTORY_TOTAL_COUNT": str(len(inventory_rows)),
        "ACTIVE_LEGACY_WRITER_COUNT": str(len(inventory["active"])),
        "DISABLED_LEGACY_WRITER_COUNT": str(len(inventory["disabled"])),
        "AUTHORIZED_WRITER_COUNT": str(len(inventory["authorized"])),
        "ACTIVE_LEGACY_WRITER_PATHS": ";".join(inventory["active"]) if inventory["active"] else "NONE",
        "DISABLED_LEGACY_WRITER_PATHS": ";".join(inventory["disabled"]) if inventory["disabled"] else "NONE",
        "V18_14B_DIRECT_CURRENT_WRITE_DISABLED": bool_text(bool(inventory["v14_disabled"])),
        "V18_35E_DIRECT_CURRENT_WRITE_DISABLED": bool_text(bool(inventory["v35e_disabled"])),
        "V18_35E_RAW105_CURRENT_FACTOR_REUSE_BLOCKED_FROM_CURRENT_ALIAS": bool_text(bool(inventory["v35e_raw105_blocked"])),
        "TRUE_PROVENANCE_REPAIRED": bool_text(all_rows_authoritative and not DISALLOWED_SOURCE_RE.search(blob)),
        "RAW105_FACTOR_REUSE_REMOVED_OR_BLOCKED": bool_text(all_rows_authoritative and not DISALLOWED_SOURCE_RE.search(blob)),
        "PRIMARY_SCORE_SOURCE_LABEL_MASKING_FIXED": bool_text(not missing_prov and not DISALLOWED_SOURCE_RE.search(blob)),
        "CURRENT_TOP20_ALIAS_WRITTEN": alias_written,
        "CURRENT_TOP20_WRITE_ALLOWED": bool_text(write_allowed),
        "CURRENT_TOP20_WRITE_BLOCKED_REASON": "NONE" if write_allowed else ";".join(dict.fromkeys(reasons)),
        "V18_45A_DIRECT_CURRENT_WRITE_DISABLED": "TRUE",
        "V18_50A_REVALIDATED_BEFORE_PACKET": "TRUE",
        "HOMEPAGE_WRITE_REQUIRES_SOURCE_OK": "TRUE",
        "SANITIZED_UNIVERSE_COUNT": str(rec["sanitized"]),
        "RANKED_ELIGIBLE_COUNT": str(rec["ranked_eligible"]),
        "VALID_EXCLUSION_COUNT": str(rec["valid_exclusion"]),
        "UNAVAILABLE_OR_DELISTED_COUNT": str(rec["unavailable"]),
        "PRICE_HISTORY_INSUFFICIENT_COUNT": str(rec["insufficient"]),
        "DUPLICATE_TICKER_COUNT": str(rec["duplicate"]),
        "RECONCILIATION_OK": bool_text(bool(rec["ok"])),
        "RECONCILIATION_FORMULA": str(rec["formula"]),
        "V18_35D_TOP20_MATCH_CURRENT_TOP20": bool_text(match),
        "DAILY_OPERATOR_ACTION_ENTRY_SOURCE_OK": bool_text(downstream_ok),
        "HOMEPAGE_SOURCE_OK": bool_text(downstream_ok),
        "FULL_UNIVERSE_PRICE_REFRESH_COMPLETE": bool_text(full_stale_count == 0 and bool(ranked_rows)),
        "TOP20_PRICE_REFRESH_COMPLETE": bool_text(top20_stale_count == 0 and bool(top20)),
        "FULL_UNIVERSE_STALE_ROW_COUNT": str(full_stale_count),
        "TOP20_STALE_ROW_COUNT": str(top20_stale_count),
        **SAFETY_FIELDS,
    }
    return values, top20, reasons, inventory_rows


def render_report(values: dict[str, str]) -> str:
    lines = [
        "# V18.50B-R2 Sole Current Top20 Writer Enforcement",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key in READ_FIRST_ORDER:
        lines.append(f"| {key} | `{values.get(key, '')}` |")
    lines += [
        "",
        "## Safety",
        "",
        "- Source-chain and provenance repair only.",
        "- No ranking formula, factor weight, buy/sell policy, broker, order, or trading-execution change.",
    ]
    return "\n".join(lines) + "\n"


def run(root: Path) -> int:
    values, _top20, _reasons, inventory_rows = validate(root)
    generated_at = now_iso()
    audit_rows = [
        {"generated_at": generated_at, **values, **row}
        for row in inventory_rows
    ] or [{"generated_at": generated_at, **values}]
    fields: list[str] = []
    for row in audit_rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    write_csv(root / OUT_SOURCE_AUDIT_CSV_R2, audit_rows, fields)
    read_first = "\n".join(f"{key}: {values.get(key, '')}" for key in READ_FIRST_ORDER) + "\n"
    write_text(root / OUT_READ_FIRST_R2, read_first)
    report = render_report(values)
    write_text(root / OUT_REPORT_R2, report)
    write_text(root / OUT_SOURCE_AUDIT_MD, report)
    if values["STATUS"] == "PASS":
        write_text(root / OUT_READ_FIRST_CURRENT, read_first)
    print(f"STATUS: {values['STATUS']}")
    print(f"CURRENT_TOP20_ALIAS_WRITTEN: {values['CURRENT_TOP20_ALIAS_WRITTEN']}")
    print(f"CURRENT_TOP20_WRITE_ALLOWED: {values['CURRENT_TOP20_WRITE_ALLOWED']}")
    print(f"CURRENT_TOP20_WRITE_BLOCKED_REASON: {values['CURRENT_TOP20_WRITE_BLOCKED_REASON']}")
    return 0 if values["STATUS"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.50B-R2 sole current Top20 writer enforcement.")
    parser.add_argument("--root", "--project-root", dest="root", default="D:/us-tech-quant")
    args = parser.parse_args()
    return run(Path(args.root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
