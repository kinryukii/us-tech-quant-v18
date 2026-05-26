from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import traceback
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_28A_R2_REMAINING_UNKNOWN_THEME_PATCH_READY"
STATUS_WARN = "WARN_V18_28A_R2_REMAINING_UNKNOWN_THEME_PATCH_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_28A_R2_REMAINING_UNKNOWN_THEME_PATCH_ERROR"
MODE = "REMAINING_UNKNOWN_THEME_PATCH"

THEME_MAP = "state/v18/reference/V18_TICKER_THEME_MAP.csv"
CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
R28A_READ_FIRST = "outputs/v18/ops/V18_28A_READ_FIRST.txt"

OUT_RESULT = "outputs/v18/candidates/V18_28A_R2_REMAINING_UNKNOWN_THEME_PATCH_RESULT.csv"
OUT_REPORT = "outputs/v18/read_center/V18_28A_R2_REMAINING_UNKNOWN_THEME_PATCH_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_28A_R2_READ_FIRST.txt"

PROTECTED_FILES = [
    CURRENT_CANDIDATES,
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
    "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv",
]
PROTECTED_DIRS = [
    "state/v18/price_cache",
    "state/v18/trading",
    "outputs/v18/official_daily",
]

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

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "THEME_MAP_ROW_COUNT_BEFORE",
    "THEME_MAP_ROW_COUNT_AFTER",
    "PATCH_TARGET_COUNT",
    "PATCHED_ROW_COUNT",
    "SKIPPED_ALREADY_CLASSIFIED_COUNT",
    "UNKNOWN_PRIMARY_THEME_COUNT_BEFORE",
    "UNKNOWN_PRIMARY_THEME_COUNT_AFTER",
    "DUPLICATE_THEME_TICKER_COUNT_AFTER",
    "REFRESHED_R28A_STATUS",
    "FORBIDDEN_MODIFIED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
]

RESULT_FIELDS = [
    "ticker",
    "found_in_theme_map",
    "primary_theme_before",
    "primary_theme_after",
    "manual_review_required_before",
    "manual_review_required_after",
    "patched",
    "skipped_reason",
    "notes",
]


def p(
    company_name: str,
    primary_theme: str,
    secondary_theme: str,
    industry_group: str,
    exposure_tags: str,
    role_bucket: str,
    cyclicality_bucket: str,
    volatility_bucket: str,
    liquidity_bucket: str,
    notes_extra: str = "",
) -> Dict[str, str]:
    notes = "V18.28A-R2 controlled remaining-UNKNOWN manual theme patch; no external fetch."
    if notes_extra:
        notes = f"{notes} {notes_extra}"
    return {
        "company_name": company_name,
        "primary_theme": primary_theme,
        "secondary_theme": secondary_theme,
        "industry_group": industry_group,
        "exposure_tags": exposure_tags,
        "role_bucket": role_bucket,
        "cyclicality_bucket": cyclicality_bucket,
        "volatility_bucket": volatility_bucket,
        "liquidity_bucket": liquidity_bucket,
        "manual_review_required": "FALSE",
        "notes": notes,
    }


PATCH_MAP: Dict[str, Dict[str, str]] = {
    "BLTE": p("Belite Bio Inc.", "HEALTHCARE", "Biotechnology / ophthalmology drug development", "Biotechnology", "biotech;ophthalmology;drug_development;clinical_stage", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME", "MEDIUM"),
    "TEVA": p("Teva Pharmaceutical Industries Limited", "HEALTHCARE", "Specialty and generic pharmaceuticals", "Pharmaceuticals", "generic_drugs;specialty_pharma;branded_drugs;healthcare", "DEFENSIVE_HEDGE", "DEFENSIVE", "MEDIUM", "HIGH"),
    "COGT": p("Cogent Biosciences Inc.", "HEALTHCARE", "Biotechnology / oncology pipeline", "Biotechnology", "biotech;oncology;clinical_stage", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME", "MEDIUM"),
    "RSP": p("Invesco S&P 500 Equal Weight ETF", "OTHER", "Broad-market equal-weight ETF", "ETF", "etf;sp500;equal_weight;broad_market", "NON_CORE", "HIGH_BETA_MACRO", "MEDIUM", "HIGH", "Non-single-stock instrument; exclude or separately bucket in single-stock factor backtests."),
    "INSM": p("Insmed Incorporated", "HEALTHCARE", "Rare disease biopharma", "Biotechnology", "biotech;rare_disease;respiratory;drug_development", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH", "HIGH"),
    "WVE": p("Wave Life Sciences Ltd.", "HEALTHCARE", "RNA medicines / biotechnology", "Biotechnology", "biotech;rna_medicine;genetic_medicine;clinical_stage", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME", "MEDIUM"),
    "PSIX": p("Power Solutions International Inc.", "POWER_INFRASTRUCTURE", "Fuel-agnostic power systems and engines", "Power Systems", "power_systems;engines;industrial;alternative_fuels", "TACTICAL_BETA", "CYCLICAL", "HIGH", "MEDIUM"),
    "RERE": p("ATRenew Inc.", "ECOMMERCE", "China pre-owned consumer electronics platform", "Internet Retail", "china;recommerce;consumer_electronics;internet_retail", "SPECULATIVE_SATELLITE", "CYCLICAL", "HIGH", "MEDIUM"),
    "STG": p("Sunlands Technology Group", "CONSUMER", "China online education", "Education Services", "china;online_education;consumer_services", "SPECULATIVE_SATELLITE", "CYCLICAL", "EXTREME", "LOW"),
    "RBLX": p("Roblox Corporation", "INTERNET_PLATFORM", "Gaming and user-generated content platform", "Interactive Entertainment", "gaming;ugc;metaverse;internet_platform", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH", "HIGH"),
    "OLMA": p("Olema Pharmaceuticals Inc.", "HEALTHCARE", "Women's oncology biotechnology", "Biotechnology", "biotech;oncology;womens_health;clinical_stage", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME", "MEDIUM"),
    "ARGT": p("Global X MSCI Argentina ETF", "OTHER", "Argentina country ETF", "ETF", "etf;argentina;country_beta;macro_beta", "TACTICAL_BETA", "HIGH_BETA_MACRO", "HIGH", "MEDIUM", "Non-single-stock instrument; exclude or separately bucket in single-stock factor backtests."),
    "APG": p("APi Group Corporation", "INDUSTRIAL", "Safety services and engineering/construction services", "Engineering & Construction", "industrial_services;fire_safety;security;engineering_construction", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM", "HIGH"),
    "ALM": p("Almonty Industries Inc.", "OTHER", "Critical minerals / tungsten mining", "Mining", "critical_minerals;tungsten;mining;materials", "TACTICAL_BETA", "COMMODITY_CYCLICAL", "EXTREME", "MEDIUM", "Consider adding MATERIALS or CRITICAL_MINERALS as a future primary_theme."),
    "NAMS": p("NewAmsterdam Pharma Company N.V.", "HEALTHCARE", "Metabolic disease biopharma", "Biotechnology", "biotech;metabolic_disease;clinical_stage;cardiometabolic", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH", "MEDIUM"),
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


def norm(value: object) -> str:
    return str(value or "").strip()


def ticker(value: object) -> str:
    return norm(value).upper()


def is_unknown(value: object) -> bool:
    return norm(value).upper() in {"", "UNKNOWN", "NAN", "NONE", "NULL"}


def bool_true(value: object) -> bool:
    return norm(value).upper() in {"TRUE", "T", "YES", "Y", "1"}


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


def unknown_count(rows: Sequence[Dict[str, str]]) -> int:
    return sum(1 for row in rows if is_unknown(row.get("primary_theme")))


def duplicate_count(rows: Sequence[Dict[str, str]]) -> int:
    counts = Counter(ticker(row.get("ticker")) for row in rows if ticker(row.get("ticker")))
    return sum(1 for count in counts.values() if count > 1)


def normalize_rows(rows: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    normalized = []
    for row in rows:
        out = {field: norm(row.get(field)) for field in THEME_FIELDS}
        out["ticker"] = ticker(out.get("ticker"))
        out["primary_theme"] = norm(out.get("primary_theme")).upper() or "UNKNOWN"
        out["manual_review_required"] = "TRUE" if bool_true(out.get("manual_review_required")) or is_unknown(out.get("primary_theme")) else "FALSE"
        normalized.append(out)
    return normalized


def refreshed_r28a_status(root: Path) -> str:
    for line in read_text(root / R28A_READ_FIRST).splitlines():
        if line.startswith("STATUS:"):
            return line.split(":", 1)[1].strip()
    return ""


def rerun_r28a(root: Path) -> str:
    module_path = root / "scripts/v18/v18_28A_sector_theme_classification_audit.py"
    spec = importlib.util.spec_from_file_location("v18_28A_sector_theme_classification_audit", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load R28A audit script: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.run(root)
    return str(result.get("STATUS") or refreshed_r28a_status(root))


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def table(rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> str:
    if not rows:
        return "_None._"
    header = "| " + " | ".join(fields) + " |"
    sep = "| " + " | ".join(["---"] * len(fields)) + " |"
    body = ["| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |" for row in rows]
    return "\n".join([header, sep] + body)


def build_report(values: Dict[str, object], result_rows: Sequence[Dict[str, object]], theme_rows: Sequence[Dict[str, str]]) -> str:
    counts = Counter(row.get("primary_theme", "UNKNOWN") for row in theme_rows)
    count_rows = [{"primary_theme": key, "count": count} for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
    lines = [
        "# V18.28A-R2 Remaining UNKNOWN Theme Patch",
        "",
        "## Read First",
        "",
    ]
    lines.extend([f"- {field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS])
    lines.extend(
        [
            "",
            "## Patch Results",
            "",
            table(result_rows, RESULT_FIELDS),
            "",
            "## Primary Theme Counts After",
            "",
            table(count_rows, ["primary_theme", "count"]),
            "",
            "## Safety",
            "",
            "- No external data fetch was performed.",
            "- Only UNKNOWN or blank rows for the 15 controlled target tickers were eligible for patching.",
            "- Existing non-UNKNOWN classifications were preserved.",
            "- R28A classification audit outputs were refreshed after patching.",
        ]
    )
    return "\n".join(lines) + "\n"


def run(root: Path) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)

    theme_path = root / THEME_MAP
    rows_raw, _fields = read_csv(theme_path)
    if not rows_raw:
        raise RuntimeError(f"No theme map rows found: {theme_path}")
    rows = normalize_rows(rows_raw)
    before_count = len(rows)
    before_unknown = unknown_count(rows)

    result_rows: List[Dict[str, object]] = []
    by_ticker = {ticker(row.get("ticker")): row for row in rows if ticker(row.get("ticker"))}
    patched = 0
    skipped_classified = 0

    for target, patch in PATCH_MAP.items():
        row = by_ticker.get(target)
        if row is None:
            result_rows.append(
                {
                    "ticker": target,
                    "found_in_theme_map": "FALSE",
                    "primary_theme_before": "",
                    "primary_theme_after": "",
                    "manual_review_required_before": "",
                    "manual_review_required_after": "",
                    "patched": "FALSE",
                    "skipped_reason": "MISSING_THEME_MAP_ROW",
                    "notes": "",
                }
            )
            continue

        before_theme = row.get("primary_theme", "")
        before_manual = row.get("manual_review_required", "")
        if is_unknown(before_theme):
            for field, value in patch.items():
                row[field] = value
            patched += 1
            skipped_reason = ""
            patched_flag = "TRUE"
        else:
            skipped_classified += 1
            skipped_reason = "ALREADY_CLASSIFIED_PRESERVED"
            patched_flag = "FALSE"

        result_rows.append(
            {
                "ticker": target,
                "found_in_theme_map": "TRUE",
                "primary_theme_before": before_theme,
                "primary_theme_after": row.get("primary_theme", ""),
                "manual_review_required_before": before_manual,
                "manual_review_required_after": row.get("manual_review_required", ""),
                "patched": patched_flag,
                "skipped_reason": skipped_reason,
                "notes": row.get("notes", ""),
            }
        )

    after_count = len(rows)
    if after_count != before_count:
        raise RuntimeError("Theme map row count changed during R2 patch")

    write_csv(theme_path, rows, THEME_FIELDS)
    refreshed_status = rerun_r28a(root)
    after_unknown = unknown_count(rows)
    dupes_after = duplicate_count(rows)
    forbidden_modified = protected_sig(root) != protected_before

    if after_count != before_count or forbidden_modified:
        status = STATUS_FAIL
    elif dupes_after == 0 and after_unknown < before_unknown and refreshed_status == "OK_V18_28A_THEME_CLASSIFICATION_READY":
        status = STATUS_OK
    elif dupes_after == 0:
        status = STATUS_WARN
    else:
        status = STATUS_FAIL

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "THEME_MAP_ROW_COUNT_BEFORE": before_count,
        "THEME_MAP_ROW_COUNT_AFTER": after_count,
        "PATCH_TARGET_COUNT": len(PATCH_MAP),
        "PATCHED_ROW_COUNT": patched,
        "SKIPPED_ALREADY_CLASSIFIED_COUNT": skipped_classified,
        "UNKNOWN_PRIMARY_THEME_COUNT_BEFORE": before_unknown,
        "UNKNOWN_PRIMARY_THEME_COUNT_AFTER": after_unknown,
        "DUPLICATE_THEME_TICKER_COUNT_AFTER": dupes_after,
        "REFRESHED_R28A_STATUS": refreshed_status,
        "FORBIDDEN_MODIFIED": "TRUE" if forbidden_modified else "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
    }
    write_csv(root / OUT_RESULT, result_rows, RESULT_FIELDS)
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, build_report(values, result_rows, rows))

    if status == STATUS_FAIL:
        raise RuntimeError(f"R2 patch failed status checks: {status}")
    return values


def write_failure(root: Path, error: BaseException) -> None:
    values = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "THEME_MAP_ROW_COUNT_BEFORE": 0,
        "THEME_MAP_ROW_COUNT_AFTER": 0,
        "PATCH_TARGET_COUNT": len(PATCH_MAP),
        "PATCHED_ROW_COUNT": 0,
        "SKIPPED_ALREADY_CLASSIFIED_COUNT": 0,
        "UNKNOWN_PRIMARY_THEME_COUNT_BEFORE": 0,
        "UNKNOWN_PRIMARY_THEME_COUNT_AFTER": 0,
        "DUPLICATE_THEME_TICKER_COUNT_AFTER": 0,
        "REFRESHED_R28A_STATUS": refreshed_r28a_status(root),
        "FORBIDDEN_MODIFIED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
    }
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, f"# V18.28A-R2 Remaining UNKNOWN Theme Patch Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.28A-R2 remaining UNKNOWN theme patch.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        values = run(root)
        print(f"STATUS: {values['STATUS']}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return 0
    except Exception as exc:
        write_failure(root, exc)
        print(f"STATUS: {STATUS_FAIL}")
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
