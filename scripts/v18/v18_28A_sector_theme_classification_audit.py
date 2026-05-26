from __future__ import annotations

import argparse
import csv
import datetime as dt
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_28A_THEME_CLASSIFICATION_READY"
STATUS_WARN = "WARN_V18_28A_THEME_CLASSIFICATION_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_28A_THEME_CLASSIFICATION_ERROR"

MODE = "READ_ONLY_THEME_CLASSIFICATION_AUDIT"

CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
THEME_MAP = "state/v18/reference/V18_TICKER_THEME_MAP.csv"

OUT_ENRICHED = "outputs/v18/candidates/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.csv"
OUT_AUDIT = "outputs/v18/candidates/V18_28A_THEME_CLASSIFICATION_AUDIT.csv"
OUT_REPORT = "outputs/v18/read_center/V18_CURRENT_CANDIDATE_THEME_CLASSIFICATION.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_28A_READ_FIRST.txt"

PROTECTED_FILES = [
    CURRENT_CANDIDATES,
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
    "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv",
]
PROTECTED_DIRS = ["state/v18/price_cache"]

THEME_FIELDS = [
    "ticker",
    "company_name",
    "primary_theme",
    "secondary_theme",
    "industry_group",
    "exposure_tags",
    "role_bucket",
    "cyclicality_bucket",
    "volatility_bucket",
    "liquidity_bucket",
    "manual_review_required",
    "notes",
]

AUDIT_FIELDS = ["audit_type", "key", "count", "tickers", "notes"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "CURRENT_RANKED_CANDIDATE_ROW_COUNT",
    "ENRICHED_ROW_COUNT",
    "THEME_MAP_ROW_COUNT",
    "MISSING_THEME_COUNT",
    "UNKNOWN_PRIMARY_THEME_COUNT",
    "DUPLICATE_THEME_TICKER_COUNT",
    "PRIMARY_THEME_COUNT",
    "MANUAL_REVIEW_REQUIRED_COUNT",
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


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    raise RuntimeError(f"Unable to read CSV: {path}")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def norm_text(value: object) -> str:
    return str(value or "").strip()


def norm_bool(value: object) -> bool:
    return norm_text(value).upper() in {"TRUE", "T", "YES", "Y", "1"}


def to_float(value: object, default: float = 0.0) -> float:
    try:
        text = norm_text(value)
        return float(text) if text else default
    except Exception:
        return default


def to_int(value: object, default: int = 0) -> int:
    try:
        text = norm_text(value)
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


def create_theme_map_if_missing(path: Path, candidate_rows: Sequence[Dict[str, str]]) -> bool:
    if path.exists():
        return False
    rows: List[Dict[str, str]] = []
    seen = set()
    for row in candidate_rows:
        ticker = norm_ticker(row.get("ticker"))
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        rows.append(
            {
                "ticker": ticker,
                "company_name": "",
                "primary_theme": "UNKNOWN",
                "secondary_theme": "",
                "industry_group": "",
                "exposure_tags": "",
                "role_bucket": "",
                "cyclicality_bucket": "",
                "volatility_bucket": "",
                "liquidity_bucket": "",
                "manual_review_required": "TRUE",
                "notes": "Seeded by V18.28A without external data; manual classification required.",
            }
        )
    write_csv(path, rows, THEME_FIELDS)
    return True


def normalize_theme_rows(rows: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    normalized = []
    for row in rows:
        out = {field: norm_text(row.get(field)) for field in THEME_FIELDS}
        out["ticker"] = norm_ticker(out.get("ticker"))
        out["primary_theme"] = norm_text(out.get("primary_theme")).upper() or "UNKNOWN"
        out["manual_review_required"] = "TRUE" if norm_bool(out.get("manual_review_required")) else "FALSE"
        normalized.append(out)
    return normalized


def duplicate_tickers(rows: Sequence[Dict[str, str]]) -> List[str]:
    counts = Counter(norm_ticker(row.get("ticker")) for row in rows if norm_ticker(row.get("ticker")))
    return sorted([ticker for ticker, count in counts.items() if count > 1])


def build_theme_lookup(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}
    for row in rows:
        ticker = norm_ticker(row.get("ticker"))
        if ticker and ticker not in lookup:
            lookup[ticker] = row
    return lookup


def candidate_sort_key(row: Dict[str, str]) -> Tuple[int, float, str]:
    rank = to_int(row.get("rank"), 0)
    if rank > 0:
        return (0, float(rank), norm_ticker(row.get("ticker")))
    return (1, -to_float(row.get("composite_candidate_score")), norm_ticker(row.get("ticker")))


def add_theme_ranks(rows: List[Dict[str, object]]) -> None:
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[norm_text(row.get("primary_theme")).upper() or "UNKNOWN"].append(row)

    for theme_rows in grouped.values():
        theme_rows.sort(key=candidate_sort_key)
        total = len(theme_rows)
        for idx, row in enumerate(theme_rows, start=1):
            row["theme_rank"] = idx
            if total <= 1:
                row["theme_percentile"] = "100.00"
            else:
                row["theme_percentile"] = f"{100.0 * (total - idx) / (total - 1):.2f}"


def join_theme_metadata(
    candidate_rows: Sequence[Dict[str, str]], theme_lookup: Dict[str, Dict[str, str]]
) -> Tuple[List[Dict[str, object]], List[str]]:
    enriched: List[Dict[str, object]] = []
    missing: List[str] = []
    for source_row in candidate_rows:
        row: Dict[str, object] = dict(source_row)
        ticker = norm_ticker(row.get("ticker"))
        row["ticker"] = ticker
        theme = theme_lookup.get(ticker)
        if theme is None:
            missing.append(ticker)
            theme = {
                "ticker": ticker,
                "company_name": "",
                "primary_theme": "UNKNOWN",
                "secondary_theme": "",
                "industry_group": "",
                "exposure_tags": "",
                "role_bucket": "",
                "cyclicality_bucket": "",
                "volatility_bucket": "",
                "liquidity_bucket": "",
                "manual_review_required": "TRUE",
                "notes": "Missing from V18_TICKER_THEME_MAP.csv; assigned UNKNOWN by V18.28A.",
            }
        for field in THEME_FIELDS:
            if field != "ticker":
                row[field] = theme.get(field, "")
        row["primary_theme"] = norm_text(row.get("primary_theme")).upper() or "UNKNOWN"
        row["manual_review_required"] = "TRUE" if norm_bool(row.get("manual_review_required")) else "FALSE"
        row["theme_map_present"] = "FALSE" if ticker in missing else "TRUE"
        row["theme_rank"] = ""
        row["theme_percentile"] = ""
        enriched.append(row)
    add_theme_ranks(enriched)
    return enriched, missing


def counter_rows(counter: Counter, audit_type: str) -> List[Dict[str, object]]:
    return [
        {"audit_type": audit_type, "key": key or "BLANK", "count": count, "tickers": "", "notes": ""}
        for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def build_audit_rows(
    enriched: Sequence[Dict[str, object]], missing: Sequence[str], unknown: Sequence[str], dupes: Sequence[str]
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    rows.append(
        {
            "audit_type": "MISSING_THEME_ROWS",
            "key": "MISSING_FROM_THEME_MAP",
            "count": len(missing),
            "tickers": ";".join(sorted(set(missing))),
            "notes": "Candidates absent from state/v18/reference/V18_TICKER_THEME_MAP.csv.",
        }
    )
    rows.append(
        {
            "audit_type": "UNKNOWN_PRIMARY_THEME_ROWS",
            "key": "UNKNOWN",
            "count": len(unknown),
            "tickers": ";".join(sorted(set(unknown))),
            "notes": "Candidates with primary_theme UNKNOWN after enrichment.",
        }
    )
    rows.append(
        {
            "audit_type": "DUPLICATE_THEME_TICKERS",
            "key": "DUPLICATE_IN_THEME_MAP",
            "count": len(dupes),
            "tickers": ";".join(dupes),
            "notes": "Duplicate ticker keys in the theme map; first row is used for enrichment.",
        }
    )
    rows.extend(counter_rows(Counter(norm_text(row.get("primary_theme")).upper() for row in enriched), "PRIMARY_THEME_COUNT"))
    rows.extend(counter_rows(Counter(norm_text(row.get("role_bucket")) for row in enriched), "ROLE_BUCKET_COUNT"))
    rows.extend(counter_rows(Counter(norm_text(row.get("volatility_bucket")) for row in enriched), "VOLATILITY_BUCKET_COUNT"))
    return rows


def top_table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: int) -> str:
    selected = list(rows[:limit])
    if not selected:
        return "_None._"
    header = "| " + " | ".join(fields) + " |"
    sep = "| " + " | ".join(["---"] * len(fields)) + " |"
    body = []
    for row in selected:
        body.append("| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |")
    return "\n".join([header, sep] + body)


def build_report(
    run_id: str,
    status: str,
    read_first: Dict[str, object],
    audit_rows: Sequence[Dict[str, object]],
    enriched: Sequence[Dict[str, object]],
) -> str:
    theme_rows = [row for row in audit_rows if row.get("audit_type") == "PRIMARY_THEME_COUNT"]
    role_rows = [row for row in audit_rows if row.get("audit_type") == "ROLE_BUCKET_COUNT"]
    vol_rows = [row for row in audit_rows if row.get("audit_type") == "VOLATILITY_BUCKET_COUNT"]
    unknown_rows = [row for row in enriched if norm_text(row.get("primary_theme")).upper() == "UNKNOWN"]

    lines = [
        "# V18 Current Candidate Theme Classification",
        "",
        "## Read First",
        "",
        f"- STATUS: {status}",
        f"- MODE: {MODE}",
        f"- RUN_ID: {run_id}",
        f"- CURRENT_RANKED_CANDIDATE_ROW_COUNT: {read_first['CURRENT_RANKED_CANDIDATE_ROW_COUNT']}",
        f"- ENRICHED_ROW_COUNT: {read_first['ENRICHED_ROW_COUNT']}",
        f"- THEME_MAP_ROW_COUNT: {read_first['THEME_MAP_ROW_COUNT']}",
        f"- MISSING_THEME_COUNT: {read_first['MISSING_THEME_COUNT']}",
        f"- UNKNOWN_PRIMARY_THEME_COUNT: {read_first['UNKNOWN_PRIMARY_THEME_COUNT']}",
        f"- DUPLICATE_THEME_TICKER_COUNT: {read_first['DUPLICATE_THEME_TICKER_COUNT']}",
        f"- MANUAL_REVIEW_REQUIRED_COUNT: {read_first['MANUAL_REVIEW_REQUIRED_COUNT']}",
        f"- OFFICIAL_DECISION_IMPACT: NONE",
        f"- AUTO_TRADE: DISABLED",
        f"- AUTO_SELL: DISABLED",
        "",
        "## Primary Theme Counts",
        "",
        top_table(theme_rows, ["key", "count"], 40),
        "",
        "## Role Bucket Counts",
        "",
        top_table(role_rows, ["key", "count"], 40),
        "",
        "## Volatility Bucket Counts",
        "",
        top_table(vol_rows, ["key", "count"], 40),
        "",
        "## Top Ranked Candidates With Theme Metadata",
        "",
        top_table(
            sorted(enriched, key=candidate_sort_key),
            ["rank", "ticker", "composite_candidate_score", "primary_theme", "role_bucket", "volatility_bucket", "theme_rank", "theme_percentile"],
            25,
        ),
        "",
        "## Missing Or UNKNOWN Classification Review",
        "",
        top_table(
            sorted(unknown_rows, key=candidate_sort_key),
            ["rank", "ticker", "primary_theme", "manual_review_required", "theme_map_present", "notes"],
            100,
        ),
        "",
        "## Safety",
        "",
        "- Read-only classification audit only.",
        "- No external data fetch was performed.",
        "- No official decision, trading state, price cache, signal freeze, factor pack, technical timing, or rolling coverage file was intentionally modified.",
    ]
    return "\n".join(lines) + "\n"


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def run(root: Path) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)

    candidate_path = root / CURRENT_CANDIDATES
    theme_map_path = root / THEME_MAP
    candidate_rows, candidate_fields = read_csv(candidate_path)
    if not candidate_rows:
        raise RuntimeError(f"No current ranked candidates found: {candidate_path}")
    if "ticker" not in candidate_fields:
        raise RuntimeError(f"Missing required ticker column in {candidate_path}")

    create_theme_map_if_missing(theme_map_path, candidate_rows)
    theme_rows_raw, _theme_fields = read_csv(theme_map_path)
    theme_rows = normalize_theme_rows(theme_rows_raw)
    dupes = duplicate_tickers(theme_rows)
    theme_lookup = build_theme_lookup(theme_rows)
    enriched, missing = join_theme_metadata(candidate_rows, theme_lookup)

    unknown = [norm_ticker(row.get("ticker")) for row in enriched if norm_text(row.get("primary_theme")).upper() == "UNKNOWN"]
    manual_review_count = sum(1 for row in enriched if norm_bool(row.get("manual_review_required")))
    primary_theme_count = len(set(norm_text(row.get("primary_theme")).upper() for row in enriched if norm_text(row.get("primary_theme"))))
    forbidden_modified = protected_sig(root) != protected_before

    status = STATUS_OK
    if missing or unknown or dupes or len(enriched) != len(candidate_rows):
        status = STATUS_WARN
    if forbidden_modified:
        status = STATUS_WARN

    audit_rows = build_audit_rows(enriched, missing, unknown, dupes)
    enriched_fields = list(candidate_fields)
    for field in THEME_FIELDS:
        if field != "ticker" and field not in enriched_fields:
            enriched_fields.append(field)
    for field in ["theme_map_present", "theme_rank", "theme_percentile"]:
        if field not in enriched_fields:
            enriched_fields.append(field)

    read_first = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": len(candidate_rows),
        "ENRICHED_ROW_COUNT": len(enriched),
        "THEME_MAP_ROW_COUNT": len(theme_rows),
        "MISSING_THEME_COUNT": len(set(missing)),
        "UNKNOWN_PRIMARY_THEME_COUNT": len(unknown),
        "DUPLICATE_THEME_TICKER_COUNT": len(dupes),
        "PRIMARY_THEME_COUNT": primary_theme_count,
        "MANUAL_REVIEW_REQUIRED_COUNT": manual_review_count,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "TRUE" if forbidden_modified else "FALSE",
    }

    write_csv(root / OUT_ENRICHED, enriched, enriched_fields)
    write_csv(root / OUT_AUDIT, audit_rows, AUDIT_FIELDS)
    write_text(root / OUT_REPORT, build_report(run_id, status, read_first, audit_rows, enriched))
    write_read_first(root / OUT_READ_FIRST, read_first)
    return read_first


def write_failure(root: Path, error: BaseException) -> None:
    values = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": 0,
        "ENRICHED_ROW_COUNT": 0,
        "THEME_MAP_ROW_COUNT": 0,
        "MISSING_THEME_COUNT": 0,
        "UNKNOWN_PRIMARY_THEME_COUNT": 0,
        "DUPLICATE_THEME_TICKER_COUNT": 0,
        "PRIMARY_THEME_COUNT": 0,
        "MANUAL_REVIEW_REQUIRED_COUNT": 0,
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "FORBIDDEN_MODIFIED": "FALSE",
    }
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, f"# V18.28A Theme Classification Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.28A sector and theme classification audit.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        result = run(root)
        print(f"STATUS: {result['STATUS']}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return 0
    except Exception as exc:
        write_failure(root, exc)
        print(f"STATUS: {STATUS_FAIL}")
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
