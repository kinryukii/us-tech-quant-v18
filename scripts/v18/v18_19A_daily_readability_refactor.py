from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")

READ_CENTER_DIR = Path("outputs/v18/read_center")
DAILY_PACKET_DIR = READ_CENTER_DIR / "daily_packet"
OPS_DIR = Path("outputs/v18/ops")

BRIEF_PATH = READ_CENTER_DIR / "V18_CURRENT_DAILY_BRIEF.md"
TOP_CANDIDATES_PATH = DAILY_PACKET_DIR / "V18_CURRENT_TOP_RANKED_CANDIDATES.md"
UNIVERSE_CHANGES_PATH = DAILY_PACKET_DIR / "V18_CURRENT_UNIVERSE_CHANGES.md"
RISK_DASHBOARD_PATH = DAILY_PACKET_DIR / "V18_CURRENT_RISK_DASHBOARD.md"
COVERAGE_STATUS_PATH = DAILY_PACKET_DIR / "V18_CURRENT_COVERAGE_STATUS.md"
DATA_FRESHNESS_PATH = DAILY_PACKET_DIR / "V18_CURRENT_DATA_FRESHNESS.md"
READ_FIRST_PATH = OPS_DIR / "V18_19A_READ_FIRST.txt"
AUDIT_PATH = OPS_DIR / "V18_19A_DAILY_READABILITY_AUDIT.csv"

STATUS_OK = "OK_V18_19A_DAILY_READABILITY_READY"
STATUS_WARN = "WARN_V18_19A_DAILY_READABILITY_READY"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def read_csv_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                return rows, list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def pick_file(paths: Sequence[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def safe_int(value: object, default: int = 0) -> int:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return default
    try:
        return int(float(text))
    except Exception:
        return default


def safe_float(value: object) -> float | None:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        out = float(text)
    except Exception:
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def safe_bool(value: object, default: bool = False) -> bool:
    text = str(value or "").strip().upper()
    if text in {"TRUE", "T", "YES", "Y", "1"}:
        return True
    if text in {"FALSE", "F", "NO", "N", "0"}:
        return False
    return default


def normalize(text: object) -> str:
    return str(text or "").strip()


def shorten(text: object, limit: int = 120) -> str:
    value = normalize(text)
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def first_nonempty(*values: object) -> str:
    for value in values:
        text = normalize(value)
        if text:
            return text
    return ""


def first_value(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    target = key.upper()
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        if left.strip().lstrip("- ").strip().upper() == target:
            return right.strip()
    return ""


def read_first_map(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        key = left.strip().lstrip("- ").strip().upper()
        out[key] = right.strip()
    return out


def choose_first_alias_source(root: Path, candidates: Sequence[Path]) -> Tuple[Path | None, Dict[str, str], str]:
    first_existing: Tuple[Path, Dict[str, str], str] | None = None
    for path in candidates:
        if not path.exists():
            continue
        if path.suffix.lower() == ".md":
            if first_existing is None:
                first_existing = (path, {}, "TEXT_REFERENCE_ONLY")
            continue
        data = read_first_map(path)
        if data:
            return path, data, "OK"
        if first_existing is None:
            first_existing = (path, data, "WARN_EMPTY")
    if first_existing is not None:
        return first_existing
    return None, {}, "MISSING"


def write_markdown_table(rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> List[str]:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        vals = [normalize(row.get(field, "")).replace("|", "/") for field in fields]
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def load_rows(paths: Sequence[Path]) -> Tuple[Path | None, List[Dict[str, str]], List[str], str]:
    for path in paths:
        rows, fields, status = read_csv_rows(path)
        if status == "OK" and rows:
            return path, rows, fields, status
    for path in paths:
        if path.exists():
            rows, fields, status = read_csv_rows(path)
            return path, rows, fields, status
    return None, [], [], "MISSING"


def latest_by_key(rows: Sequence[Dict[str, str]], key: str) -> str:
    values: List[str] = []
    for row in rows:
        text = normalize(row.get(key, ""))
        if text:
            values.append(text)
    return max(values) if values else ""


def count_if(rows: Sequence[Dict[str, str]], predicate) -> int:
    return sum(1 for row in rows if predicate(row))


def tier_counts(rows: Sequence[Dict[str, str]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        tier = normalize(row.get("universe_tier", "")).upper()
        if tier:
            counts[tier] = counts.get(tier, 0) + 1
    return counts


def choose_candidate_rows(root: Path) -> Tuple[Path | None, List[Dict[str, str]], List[str], str]:
    paths = [
        root / "outputs/v18/ranking/V18_CURRENT_RANKED_CANDIDATE_SCORE_EXPLANATION.csv",
        root / "outputs/v18/ranking/V18_17A_CURRENT_RANKED_CANDIDATE_SCORE_EXPLANATION.csv",
        root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
        root / "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    ]
    return load_rows(paths)


def choose_universe_rows(root: Path) -> Tuple[Path | None, List[Dict[str, str]], List[str], str]:
    paths = [
        root / "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv",
        root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
    ]
    return load_rows(paths)


def choose_promotion_rows(root: Path) -> Tuple[Path | None, List[Dict[str, str]], List[str], str]:
    paths = [
        root / "outputs/v18/universe/V18_CURRENT_PROMOTION_DEMOTION_AUDIT.csv",
        root / "outputs/v18/universe/V18_16E_CURRENT_PROMOTION_DEMOTION_AUDIT.csv",
    ]
    return load_rows(paths)


def metric_rows_to_map(rows: Sequence[Dict[str, str]]) -> Dict[str, str]:
    mapped: Dict[str, str] = {}
    for row in rows:
        metric = normalize(row.get("metric", "")).upper()
        if metric:
            mapped[metric] = normalize(row.get("value", ""))
    return mapped


def coverage_candidate_paths(root: Path) -> List[Path]:
    return [
        root / "outputs/v18/ops/V18_16F_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt",
        root / "outputs/v18/ops/V18_16B_READ_FIRST.txt",
        root / "outputs/v18/universe/V18_16J_CURRENT_POST_PATCH_COVERAGE_CHECK.csv",
        root / "outputs/v18/universe/V18_16H_CURRENT_COVERAGE_AUDIT.csv",
        root / "outputs/v18/universe/V18_CURRENT_ROLLING_SCAN_COVERAGE_AUDIT.csv",
    ]


def coverage_candidate_info(path: Path) -> Dict[str, object]:
    exists = path.exists()
    modified = path.stat().st_mtime if exists else 0.0
    modified_text = dt.datetime.fromtimestamp(modified).isoformat(timespec="seconds") if exists else ""
    info: Dict[str, object] = {
        "path": path,
        "exists": exists,
        "modified": modified,
        "modified_text": modified_text,
        "parse_status": "MISSING",
        "source_status": "MISSING",
        "valid": False,
        "today": 0,
        "required": 0,
        "met": False,
        "shortfall": 0,
        "reason": "Source missing.",
    }
    if not exists:
        return info

    name = path.name.upper()
    if name.endswith(".TXT"):
        read_map = read_first_map(path)
        if not read_map:
            info.update({"parse_status": "WARN_EMPTY", "source_status": "WARN_EMPTY", "reason": "Read-first file was present but no key/value fields were parsed."})
            return info
        if "V18_16F" in name or "ROLLING_UNIVERSE_SCAN" in name:
            today = safe_int(first_nonempty(read_map.get("TODAY_ROLLING_SCAN_COUNT"), read_map.get("SCANNED_TICKER_COUNT")))
        else:
            today = safe_int(first_nonempty(read_map.get("TODAY_SCAN_PLAN_COUNT"), read_map.get("SCANNED_TICKER_COUNT")))
        required = safe_int(read_map.get("DAILY_MIN_SCAN_COUNT"))
        valid = today > 0 and required > 0
        info.update({
            "parse_status": "OK_READ_FIRST",
            "source_status": "OK_READ_FIRST" if valid else "WARN_MISSING_DAILY_THRESHOLD_FIELDS",
            "valid": valid,
            "today": today,
            "required": required,
            "met": valid and today >= required,
            "shortfall": max(0, required - today) if valid else 0,
            "reason": "Valid current-run read-first daily threshold evidence." if valid else "Missing scan count or daily minimum.",
        })
        return info

    rows, _, status = read_csv_rows(path)
    info["parse_status"] = status
    if status != "OK" or not rows:
        info.update({"source_status": "WARN_UNUSABLE", "reason": "CSV source missing rows or could not be parsed."})
        return info
    if "V18_16J_CURRENT_POST_PATCH_COVERAGE_CHECK" in name:
        mapped = metric_rows_to_map(rows)
        today = safe_int(first_nonempty(mapped.get("TARGET_DAILY_SCAN_COUNT"), mapped.get("EXPECTED_DAILY_SCAN_COUNT")))
        required = safe_int(mapped.get("REQUIRED_DAILY_SCAN_COUNT"))
        met = safe_bool(mapped.get("DAILY_THRESHOLD_TARGET_MET_EXPECTED"), today >= required if required else False)
        valid = today > 0 and required > 0
        info.update({
            "source_status": "OK_V18_16J_POST_PATCH" if valid else "WARN_MISSING_DAILY_THRESHOLD_FIELDS",
            "valid": valid,
            "today": today,
            "required": required,
            "met": valid and met,
            "shortfall": max(0, required - today) if valid else 0,
            "reason": "Valid V18.16J post-patch daily threshold evidence." if valid else "Missing target or required daily count.",
        })
        return info

    row = rows[0]
    today = safe_int(first_nonempty(row.get("TODAY_ROLLING_SCAN_COUNT"), row.get("SCANNED_TICKER_COUNT")))
    required = safe_int(row.get("DAILY_MIN_SCAN_COUNT"))
    met = safe_bool(row.get("COVERAGE_TARGET_MET"), today >= required if required else False)
    valid = today > 0 and required > 0
    info.update({
        "source_status": "OK_LEGACY_COVERAGE_AUDIT" if valid else "WARN_MISSING_DAILY_THRESHOLD_FIELDS",
        "valid": valid,
        "today": today,
        "required": required,
        "met": valid and met,
        "shortfall": max(0, required - today) if valid else 0,
        "reason": "Valid legacy coverage audit evidence." if valid else "Missing scan count or daily minimum.",
    })
    return info


def choose_coverage_rows(root: Path) -> Tuple[Path | None, List[Dict[str, str]], List[str], str]:
    candidates = [coverage_candidate_info(path) for path in coverage_candidate_paths(root)]
    valid = [item for item in candidates if item["valid"]]
    if valid:
        selected = max(valid, key=lambda item: float(item["modified"]))
        path = selected["path"]
        if isinstance(path, Path) and path.suffix.lower() == ".csv":
            rows, fields, status = read_csv_rows(path)
            return path, rows, fields, status
        return path if isinstance(path, Path) else None, [], [], str(selected["parse_status"])
    existing = [item for item in candidates if item["exists"]]
    if existing:
        selected = max(existing, key=lambda item: float(item["modified"]))
        path = selected["path"]
        if isinstance(path, Path) and path.suffix.lower() == ".csv":
            rows, fields, status = read_csv_rows(path)
            return path, rows, fields, status
        return path if isinstance(path, Path) else None, [], [], str(selected["parse_status"])
    return None, [], [], "MISSING"


def choose_price_rows(root: Path) -> Tuple[Path | None, List[Dict[str, str]], List[str], str]:
    paths = [
        root / "outputs/v18/data/V18_CURRENT_SCAN_SCOPED_PRICE_UPDATE_AUDIT.csv",
        root / "outputs/v18/data/V18_16C_CURRENT_SCAN_SCOPED_PRICE_UPDATE_AUDIT.csv",
    ]
    return load_rows(paths)


def choose_event_rows(root: Path) -> Tuple[Path | None, List[Dict[str, str]], List[str], str]:
    paths = [
        root / "outputs/v18/risk/V18_CURRENT_SCAN_SCOPED_EVENT_UPDATE_AUDIT.csv",
        root / "outputs/v18/risk/V18_16C_CURRENT_SCAN_SCOPED_EVENT_UPDATE_AUDIT.csv",
    ]
    return load_rows(paths)


def choose_data_audit_rows(root: Path) -> Dict[str, Tuple[Path | None, List[Dict[str, str]], List[str], str]]:
    return {
        "yfinance_preflight": load_rows([root / "outputs/v18/data/V18_16C_P1_SCOPED_YFINANCE_SMOKE_PRICE_AUDIT.csv"]),
        "yfinance_cache_repair": load_rows([root / "outputs/v18/data/V18_16C_P2_YFINANCE_CACHE_REPAIR_PRICE_AUDIT.csv"]),
        "local_cache_bootstrap": load_rows([root / "outputs/v18/data/V18_16C_P3_LOCAL_CACHE_BOOTSTRAP_AUDIT.csv"]),
        "local_source_discovery": load_rows([root / "outputs/v18/data/V18_16C_P3_LOCAL_PRICE_SOURCE_DISCOVERY.csv"]),
    }


def row_note(row: Dict[str, str], keys: Sequence[str]) -> str:
    for key in keys:
        text = normalize(row.get(key, ""))
        if text:
            return text
    return ""


def build_top_candidates(root: Path, universe_rows: Sequence[Dict[str, str]], warnings: List[str]) -> Tuple[str, List[Dict[str, object]], Dict[str, str]]:
    candidate_path, rows, fields, status = choose_candidate_rows(root)
    universe_map = {normalize(r.get("ticker", "")).upper(): r for r in universe_rows if normalize(r.get("ticker", ""))}
    if not candidate_path:
        warnings.append("No current ranking or factor-pack candidate source was available.")
        return (
            "# V18_CURRENT_TOP_RANKED_CANDIDATES\n\nNo ranking source file was found.\n",
            [],
            {"source": "MISSING"},
        )

    if status != "OK":
        warnings.append("Ranking source file was present but could not be parsed cleanly.")
    elif not rows:
        warnings.append("Ranking source file was present but contained no candidate rows.")

    order_keys = ["rank", "factor_pack_rank", "candidate_rank", "shadow_rank", "priority_rank"]
    scored_rows: List[Tuple[float, Dict[str, str]]] = []
    for idx, row in enumerate(rows):
        rank_value = None
        for key in order_keys:
            rank_value = safe_float(row.get(key))
            if rank_value is not None:
                break
        if rank_value is None:
            rank_value = float(idx + 1)
        scored_rows.append((rank_value, row))
    scored_rows.sort(key=lambda item: (item[0], normalize(item[1].get("ticker", "")).upper()))

    table_rows: List[Dict[str, object]] = []
    source_name = candidate_path.name
    for rank_value, row in scored_rows[:10]:
        ticker = first_nonempty(row.get("ticker"), row.get("symbol")).upper()
        uni = universe_map.get(ticker, {})
        tier = first_nonempty(row.get("universe_tier"), uni.get("universe_tier"), uni.get("tier"), "")
        score = first_nonempty(
            row.get("final_score"),
            row.get("composite_candidate_score"),
            row.get("factor_pack_score"),
            row.get("score"),
        )
        key_reason = shorten(
            first_nonempty(
                row.get("explanation_short"),
                row.get("reason"),
                row.get("shadow_side_hint"),
                row.get("promotion_reason"),
                row.get("demotion_reason"),
            ),
            110,
        )
        if not key_reason and source_name.lower().endswith(".csv"):
            key_reason = shorten(
                f"{first_nonempty(row.get('score_source_status'), row.get('scan_status'), row.get('data_sufficiency_status'))} from {source_name}",
                110,
            )
        data_status = first_nonempty(
            row.get("data_sufficiency_status"),
            row.get("score_source_status"),
            row.get("scan_status"),
            row.get("price_cache_status"),
            uni.get("data_depth_sufficient"),
            uni.get("price_cache_status"),
        )
        table_rows.append(
            {
                "Rank": int(rank_value),
                "Ticker": ticker,
                "Tier": tier,
                "Score": score,
                "Key Reason": key_reason,
                "Data Status": data_status,
            }
        )

    lines = [
        "# V18_CURRENT_TOP_RANKED_CANDIDATES",
        "",
        f"- Source file: {rel(root, candidate_path)}",
        f"- Row count: {len(rows)}",
        "",
    ]
    if table_rows:
        lines.extend(write_markdown_table(table_rows, ["Rank", "Ticker", "Tier", "Score", "Key Reason", "Data Status"]))
    else:
        lines.append("No candidate rows were available in the current source.")

    usable = status == "OK" and len(rows) > 0
    if usable:
        source_status = "OK"
    elif status == "OK" and not rows:
        source_status = "WARN_EMPTY"
    elif status != "OK":
        source_status = "WARN_UNUSABLE"
    else:
        source_status = "MISSING"
    return "\n".join(lines) + "\n", table_rows, {
        "source": rel(root, candidate_path),
        "status": status,
        "row_count": str(len(rows)),
        "usable": "TRUE" if usable else "FALSE",
        "source_status": source_status,
    }


def build_universe_changes(root: Path, universe_rows: Sequence[Dict[str, str]], warnings: List[str]) -> Tuple[str, Dict[str, object]]:
    path, rows, fields, status = choose_promotion_rows(root)
    if not path:
        warnings.append("No promotion/demotion audit was available.")
        return (
            "# V18_CURRENT_UNIVERSE_CHANGES\n\nNo promotion/demotion audit file was found.\n",
            {"source": "MISSING", "row_count": "0", "status": "MISSING", "source_status": "MISSING"},
        )

    action_rows = rows
    promotions = [r for r in action_rows if normalize(r.get("tier_action", "")).upper().startswith("PROMOTED_TO")]
    demotions = [r for r in action_rows if normalize(r.get("tier_action", "")).upper().startswith("DEMOTED_TO")]
    kept = [r for r in action_rows if normalize(r.get("tier_action", "")).upper() == "KEPT_SAME_TIER"]
    changed = promotions + demotions
    notable = changed[:8]
    tier_map = tier_counts(universe_rows)
    core_daily = tier_map.get("CORE_DAILY", safe_int(first_value(root / "outputs/v18/ops/V18_16F_READ_FIRST.txt", "CORE_DAILY_COUNT")))
    candidate = tier_map.get("CANDIDATE", safe_int(first_value(root / "outputs/v18/ops/V18_16F_READ_FIRST.txt", "CANDIDATE_COUNT")))
    watchlist = tier_map.get("WATCHLIST", safe_int(first_value(root / "outputs/v18/ops/V18_16F_READ_FIRST.txt", "WATCHLIST_COUNT")))
    research = tier_map.get("RESEARCH", safe_int(first_value(root / "outputs/v18/ops/V18_16F_READ_FIRST.txt", "RESEARCH_COUNT")))
    same_day_guard = first_nonempty(
        first_value(root / "outputs/v18/ops/V18_16F_READ_FIRST.txt", "SAME_DAY_PROMOTION_GUARD"),
        first_value(root / "outputs/v18/ops/V18_16H_READ_FIRST.txt", "SAME_DAY_PROMOTION_GUARD"),
        "UNKNOWN",
    )
    core_allowed = first_nonempty(
        first_value(root / "outputs/v18/ops/V18_16F_READ_FIRST.txt", "CORE_PROMOTION_ALLOWED_THIS_RUN"),
        "UNKNOWN",
    )

    lines = [
        "# V18_CURRENT_UNIVERSE_CHANGES",
        "",
        f"- Source file: {rel(root, path)}",
        f"- Audit rows: {len(action_rows)}",
        f"- Promotions: {len(promotions)}",
        f"- Demotions: {len(demotions)}",
        f"- Unchanged: {len(kept)}",
        f"- Same-day guard: {same_day_guard}",
        f"- Core promotion allowed this run: {core_allowed}",
        f"- Core Daily count: {core_daily}",
        f"- Candidate count: {candidate}",
        f"- Watchlist count: {watchlist}",
        f"- Research count: {research}",
        "",
        "## Notable Changes",
        "",
    ]
    if notable:
        for row in notable:
            lines.append(
                f"- {normalize(row.get('ticker', ''))}: {normalize(row.get('old_tier', ''))} -> {normalize(row.get('new_tier', ''))} "
                f"({normalize(row.get('tier_action', ''))})"
                + (f" | {shorten(row_note(row, ('promotion_reason', 'demotion_reason', 'failed_reason')), 120)}" if row_note(row, ('promotion_reason', 'demotion_reason', 'failed_reason')) else "")
            )
    else:
        lines.append("No major universe change detected from available audit files.")

    if not notable:
        summary = "No major universe change detected from available audit files."
    else:
        summary = f"{len(promotions)} promotion(s), {len(demotions)} demotion(s), {len(kept)} unchanged row(s)."
    if status == "OK" and len(rows) > 0:
        source_status = "OK"
    elif status == "OK" and not rows:
        source_status = "WARN_EMPTY"
    elif status != "OK":
        source_status = "WARN_UNUSABLE"
    else:
        source_status = "MISSING"
    return "\n".join(lines) + "\n", {
        "source": rel(root, path),
        "row_count": str(len(rows)),
        "status": status,
        "source_status": source_status,
        "promotions": len(promotions),
        "demotions": len(demotions),
        "unchanged": len(kept),
        "core_daily": core_daily,
        "candidate": candidate,
        "watchlist": watchlist,
        "research": research,
        "same_day_guard": same_day_guard,
        "core_allowed": core_allowed,
        "summary": summary,
    }


def build_coverage_status(root: Path, warnings: List[str]) -> Tuple[str, Dict[str, object]]:
    path, rows, fields, status = choose_coverage_rows(root)
    read_first = read_first_map(root / "outputs/v18/ops/V18_16H_READ_FIRST.txt")
    v16i_read = read_first_map(root / "outputs/v18/ops/V18_16I_READ_FIRST.txt")
    if not path:
        warnings.append("No rolling-scan coverage audit was available.")
        return (
            "# V18_CURRENT_COVERAGE_STATUS\n\nNo coverage audit file was found.\n",
            {"source": "MISSING", "row_count": "0", "status": "MISSING", "source_status": "MISSING"},
        )

    selected_info = coverage_candidate_info(path)
    source_modified_time = str(selected_info.get("modified_text", ""))
    source_selection_reason = str(selected_info.get("reason", "Selected by newest valid daily-threshold evidence."))
    row = rows[0] if rows else {}
    metric_map = metric_rows_to_map(rows)
    source_name = path.name.upper()
    if "V18_16J_CURRENT_POST_PATCH_COVERAGE_CHECK" in source_name:
        total_universe = first_nonempty(metric_map.get("TOTAL_UNIVERSE_COUNT"), read_first.get("TOTAL_UNIVERSE_COUNT"))
        daily_min = first_nonempty(metric_map.get("REQUIRED_DAILY_SCAN_COUNT"), read_first.get("DAILY_MIN_SCAN_COUNT"))
        today_scan = first_nonempty(metric_map.get("TARGET_DAILY_SCAN_COUNT"), metric_map.get("EXPECTED_DAILY_SCAN_COUNT"))
        coverage_target = first_nonempty(metric_map.get("DAILY_THRESHOLD_TARGET_MET_EXPECTED"), "UNKNOWN")
        shortfall = str(max(0, safe_int(daily_min) - safe_int(today_scan))) if daily_min and today_scan else "UNKNOWN"
        limit_reason = "V18_16J_DAILY_THRESHOLD_PATCH_SOURCE"
        coverage_source_status = "OK_FRESH_DAILY_THRESHOLD_SOURCE"
    elif "V18_16F_READ_FIRST" in source_name or "V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST" in source_name:
        read_map = read_first_map(path)
        total_universe = first_nonempty(read_map.get("TOTAL_UNIVERSE_COUNT"), read_first.get("TOTAL_UNIVERSE_COUNT"))
        daily_min = first_nonempty(read_map.get("DAILY_MIN_SCAN_COUNT"), read_first.get("DAILY_MIN_SCAN_COUNT"))
        today_scan = first_nonempty(read_map.get("TODAY_ROLLING_SCAN_COUNT"), read_map.get("SCANNED_TICKER_COUNT"))
        coverage_target = "TRUE" if safe_int(today_scan) >= safe_int(daily_min) and safe_int(daily_min) > 0 else "FALSE"
        shortfall = str(max(0, safe_int(daily_min) - safe_int(today_scan)))
        limit_reason = "V18_16F_CURRENT_DAILY_ROLLING_SCAN_SOURCE"
        coverage_source_status = "OK_FRESH_DAILY_SCAN_SOURCE"
    elif "V18_16B_READ_FIRST" in source_name:
        read_map = read_first_map(path)
        total_universe = first_nonempty(read_map.get("TOTAL_UNIVERSE_COUNT"), read_first.get("TOTAL_UNIVERSE_COUNT"))
        daily_min = first_nonempty(read_map.get("DAILY_MIN_SCAN_COUNT"), read_first.get("DAILY_MIN_SCAN_COUNT"))
        today_scan = first_nonempty(read_map.get("TODAY_SCAN_PLAN_COUNT"), read_map.get("SCANNED_TICKER_COUNT"))
        coverage_target = "TRUE" if safe_int(today_scan) >= safe_int(daily_min) and safe_int(daily_min) > 0 else "FALSE"
        shortfall = str(max(0, safe_int(daily_min) - safe_int(today_scan)))
        limit_reason = "V18_16B_SCHEDULER_PLAN_SOURCE"
        coverage_source_status = "OK_FRESH_SCHEDULER_SOURCE"
    else:
        total_universe = first_nonempty(row.get("TOTAL_UNIVERSE_COUNT"), read_first.get("TOTAL_UNIVERSE_COUNT"))
        daily_min = first_nonempty(row.get("DAILY_MIN_SCAN_COUNT"), read_first.get("DAILY_MIN_SCAN_COUNT"))
        today_scan = first_nonempty(row.get("TODAY_ROLLING_SCAN_COUNT"), read_first.get("TODAY_ROLLING_SCAN_COUNT"))
        coverage_target = first_nonempty(row.get("COVERAGE_TARGET_MET"), read_first.get("COVERAGE_TARGET_MET"))
        shortfall = first_nonempty(row.get("COVERAGE_SHORTFALL_COUNT"), read_first.get("COVERAGE_SHORTFALL_COUNT"))
        limit_reason = first_nonempty(row.get("SCAN_LIMIT_REASON"), read_first.get("SCAN_LIMIT_REASON"))
        coverage_source_status = "WARN_FALLBACK_LEGACY_COVERAGE_SOURCE"
    scanned_last_5d = first_nonempty(row.get("SCANNED_LAST_5D_COUNT"), read_first.get("SCANNED_LAST_5D_COUNT"))
    overdue = first_nonempty(row.get("OVERDUE_SCAN_COUNT"), read_first.get("OVERDUE_SCAN_COUNT"))
    true_5day_met = first_nonempty(v16i_read.get("PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_MET"), "FALSE")
    true_5day_count = first_nonempty(v16i_read.get("PROJECTED_TRUE_5DAY_UNIQUE_COVERAGE_COUNT"), "")
    true_5day_shortfall = first_nonempty(v16i_read.get("PROJECTED_TRUE_5DAY_UNIQUE_SHORTFALL_COUNT"), "")
    true_warning_preserved = normalize(true_5day_met).upper() == "FALSE"
    explanation = ""
    if safe_bool(coverage_target, False):
        explanation = "Daily threshold coverage target was met from fresh rolling scan evidence."
    else:
        explanation = (
            f"Today's rolling scan count is below the theoretical {daily_min}-name daily target."
            if daily_min else
            "Today's rolling scan count is below the required coverage target."
        )
        if limit_reason:
            explanation += f" Scan limit reason: {limit_reason}."
        if shortfall:
            explanation += f" Shortfall: {shortfall} names."
    if true_warning_preserved:
        warning_text = "True 5-day unique universe coverage remains unresolved; trust level is capped below HIGH."
        if warning_text not in warnings:
            warnings.append(warning_text)

    source_status = "OK" if (status == "OK" and rows) or str(status).startswith("OK_") else ("WARN_EMPTY" if status == "OK" else "WARN_UNUSABLE")
    lines = [
        "# V18_CURRENT_COVERAGE_STATUS",
        "",
        f"- Source file: {rel(root, path)}",
        f"- DAILY_THRESHOLD_COVERAGE_SOURCE: {rel(root, path)}",
        f"- DAILY_THRESHOLD_COVERAGE_SOURCE_STATUS: {coverage_source_status}",
        f"- DAILY_THRESHOLD_COVERAGE_SOURCE_MODIFIED_TIME: {source_modified_time}",
        f"- DAILY_THRESHOLD_COVERAGE_SOURCE_SELECTION_REASON: {source_selection_reason}",
        f"- TOTAL_UNIVERSE_COUNT: {total_universe}",
        f"- COVERAGE_WINDOW_TRADING_DAYS: {first_nonempty(row.get('COVERAGE_WINDOW_TRADING_DAYS'), read_first.get('COVERAGE_WINDOW_TRADING_DAYS'))}",
        f"- DAILY_MIN_SCAN_COUNT: {daily_min}",
        f"- TODAY_ROLLING_SCAN_COUNT: {today_scan}",
        f"- DAILY_THRESHOLD_TARGET_MET: {coverage_target}",
        f"- DAILY_THRESHOLD_SHORTFALL_COUNT: {shortfall}",
        f"- COVERAGE_TARGET_MET: {coverage_target}",
        f"- COVERAGE_SHORTFALL_COUNT: {shortfall}",
        f"- TRUE_5DAY_UNIQUE_COVERAGE_MET: {true_5day_met}",
        f"- TRUE_5DAY_UNIQUE_COVERAGE_COUNT: {true_5day_count}",
        f"- TRUE_5DAY_UNIQUE_SHORTFALL_COUNT: {true_5day_shortfall}",
        f"- TRUE_5DAY_UNIQUE_WARNING_PRESERVED: {'TRUE' if true_warning_preserved else 'FALSE'}",
        f"- SCAN_LIMIT_REASON: {limit_reason}",
        f"- SCANNED_LAST_5D_COUNT: {scanned_last_5d}",
        f"- OVERDUE_SCAN_COUNT: {overdue}",
        "",
        "## Human Explanation",
        "",
        explanation,
        "",
    ]
    return "\n".join(lines), {
        "source": rel(root, path),
        "row_count": str(len(rows)),
        "status": status,
        "source_status": coverage_source_status if source_status == "OK" else source_status,
        "daily_threshold_coverage_source": rel(root, path),
        "daily_threshold_coverage_source_status": coverage_source_status,
        "daily_threshold_coverage_source_modified_time": source_modified_time,
        "daily_threshold_coverage_source_selection_reason": source_selection_reason,
        "total_universe": total_universe,
        "daily_min": daily_min,
        "today_scan": today_scan,
        "coverage_target_met": coverage_target,
        "daily_threshold_target_met": coverage_target,
        "shortfall": shortfall,
        "daily_threshold_shortfall": shortfall,
        "true_5day_unique_coverage_met": true_5day_met,
        "true_5day_unique_coverage_count": true_5day_count,
        "true_5day_unique_shortfall_count": true_5day_shortfall,
        "true_5day_unique_warning_preserved": "TRUE" if true_warning_preserved else "FALSE",
        "limit_reason": limit_reason,
        "scanned_last_5d": scanned_last_5d,
        "overdue": overdue,
        "explanation": explanation,
    }


def build_data_freshness(root: Path, warnings: List[str]) -> Tuple[str, Dict[str, object]]:
    price_path, price_rows, price_fields, price_status = choose_price_rows(root)
    event_path, event_rows, event_fields, event_status = choose_event_rows(root)
    audits = choose_data_audit_rows(root)
    cmd_path, cmd_read, cmd_status = choose_first_alias_source(
        root,
        [
            root / "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
            root / "outputs/v18/ops/V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt",
            root / "outputs/v18/ops/V18_16F_READ_FIRST.txt",
            root / "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
        ],
    )

    if not price_path:
        warnings.append("No current scan-scoped price audit was available.")

    selected_rows = [r for r in price_rows if normalize(r.get("selected_this_run", "")).upper() == "TRUE"]
    local_source_rows = [r for r in price_rows if normalize(r.get("local_source_used", "")).upper() == "TRUE"]
    yfinance_used_rows = [r for r in price_rows if normalize(r.get("used_yfinance", "")).upper() == "TRUE"]
    cache_only_rows = [r for r in price_rows if normalize(r.get("update_status", "")).upper() in {"CACHE_ONLY", "LOCAL_CACHE_ONLY_SAFE_MODE"}]
    failed_price_rows = [r for r in price_rows if normalize(r.get("update_status", "")).upper().startswith("FAILED")]

    latest_price_dates = [normalize(r.get("latest_price_date", "")) for r in selected_rows if normalize(r.get("latest_price_date", ""))]
    latest_price_min = min(latest_price_dates) if latest_price_dates else ""
    latest_price_max = max(latest_price_dates) if latest_price_dates else ""
    selected_update_modes = sorted({normalize(r.get("update_mode", "")) for r in selected_rows if normalize(r.get("update_mode", ""))})
    selected_update_statuses = sorted({normalize(r.get("update_status", "")) for r in selected_rows if normalize(r.get("update_status", ""))})

    p1_path, p1_rows, _, p1_status = audits["yfinance_preflight"]
    p2_path, p2_rows, _, p2_status = audits["yfinance_cache_repair"]
    p3b_path, p3b_rows, _, p3b_status = audits["local_cache_bootstrap"]
    p3d_path, p3d_rows, _, p3d_parse = audits["local_source_discovery"]

    if not event_path:
        warnings.append("Event audit source missing; event-risk freshness could not be verified.")
    elif event_status != "OK":
        warnings.append("Event audit source was present but could not be parsed cleanly.")
    elif not event_rows:
        warnings.append("Event audit source was present but contained no rows.")

    p1_fail = sum(1 for r in p1_rows if normalize(r.get("update_status", "")).upper().startswith("FAILED"))
    p2_fail = sum(1 for r in p2_rows if normalize(r.get("update_status", "")).upper().startswith("FAILED"))
    p3_bootstrap_already = sum(1 for r in p3b_rows if normalize(r.get("bootstrap_status", "")).upper() == "CACHE_ALREADY_EXISTS")
    p3_local_source_used = sum(1 for r in p3b_rows if normalize(r.get("cache_exists_after", "")).upper() == "TRUE")
    event_disabled = sum(1 for r in event_rows if "SAFE_MODE" in normalize(r.get("event_update_status", "")).upper())
    event_missing_provider = sum(1 for r in event_rows if "NO_PROVIDER" in normalize(r.get("event_update_status", "")).upper())
    event_audit_available = bool(event_path and event_status == "OK" and event_rows)
    price_source_status = "OK" if price_status == "OK" and price_rows else ("WARN_EMPTY" if price_status == "OK" else "WARN_UNUSABLE")
    event_source_status = "OK" if event_audit_available else ("WARN_EMPTY" if event_status == "OK" and event_path and not event_rows else ("WARN_UNUSABLE" if event_path else "MISSING"))
    event_source_role = "missing"
    event_sentence = "Event audit source missing; event-risk freshness could not be verified."
    if event_path and event_status == "OK" and event_rows:
        primary_event_path = root / "outputs/v18/risk/V18_CURRENT_SCAN_SCOPED_EVENT_UPDATE_AUDIT.csv"
        if event_path.resolve() == primary_event_path.resolve():
            event_source_role = "primary"
            event_sentence = f"Primary event audit was found at {rel(root, event_path)}."
        else:
            event_source_role = "fallback"
            event_sentence = f"Fallback event audit was used from {rel(root, event_path)}."
    elif event_path and event_status == "OK" and not event_rows:
        event_source_role = "empty"
        event_sentence = f"Event audit source {rel(root, event_path)} was present but contained no rows."
    elif event_path and event_status != "OK":
        event_source_role = "unusable"
        event_sentence = f"Event audit source {rel(root, event_path)} was present but could not be parsed cleanly."

    current_mode_source_path = None
    current_mode_source_status = "MISSING"
    current_mode = first_nonempty(cmd_read.get("MODE"), cmd_read.get("RUN_MODE"))
    if current_mode:
        current_mode_source_path = cmd_path
        current_mode_source_status = cmd_status
    else:
        fallback_mode_path = root / "outputs/v18/ops/V18_16F_READ_FIRST.txt"
        fallback_mode_read = read_first_map(fallback_mode_path)
        current_mode = first_nonempty(fallback_mode_read.get("MODE"), fallback_mode_read.get("RUN_MODE"))
        if current_mode:
            current_mode_source_path = fallback_mode_path
            current_mode_source_status = "OK"
        else:
            current_mode_source_path = None
            current_mode_source_status = "UNKNOWN" if (cmd_path or fallback_mode_path.exists()) else "MISSING"
    current_mode = first_nonempty(current_mode, "UNKNOWN")
    current_price_mode = first_nonempty(*(selected_update_modes[:1]), "UNKNOWN")
    current_price_status = first_nonempty(*(selected_update_statuses[:1]), "UNKNOWN")

    preflight_pass = p1_fail == 0 and p2_fail == 0 and p1_status == "OK" and p2_status == "OK"
    local_cache_only = any("LOCAL_CACHE_ONLY" in mode.upper() for mode in selected_update_modes) or any("CACHE_ONLY" == status.upper() for status in selected_update_statuses)
    provider_issue = p1_fail > 0 or p2_fail > 0 or event_missing_provider > 0 or not event_audit_available

    lines = [
        "# V18_CURRENT_DATA_FRESHNESS",
        "",
        f"- Current price audit: {rel(root, price_path) if price_path else 'MISSING'}",
        f"- Event audit: {rel(root, event_path) if event_path else 'MISSING'}",
        f"- Selected rows: {len(selected_rows)}",
        f"- Local cache used rows: {len(local_source_rows)}",
        f"- yfinance used rows: {len(yfinance_used_rows)}",
        f"- Cache-only rows: {len(cache_only_rows)}",
        f"- Failed price rows: {len(failed_price_rows)}",
        f"- Selected update mode(s): {', '.join(selected_update_modes) if selected_update_modes else 'NONE'}",
        f"- Selected update status(es): {', '.join(selected_update_statuses) if selected_update_statuses else 'NONE'}",
        f"- Latest price date range observed: {latest_price_min or 'N/A'} -> {latest_price_max or 'N/A'}",
        f"- Command-center source used: {rel(root, cmd_path) if cmd_path else 'MISSING'}",
        f"- Command-center source status: {cmd_status}",
        f"- Current mode source used: {rel(root, current_mode_source_path) if current_mode_source_path else 'MISSING'}",
        f"- Current mode source status: {current_mode_source_status}",
        "",
        "## Provider Condition",
        "",
        f"- yfinance cache preflight pass/fail: {'PASS' if preflight_pass else 'FAIL'}",
        f"- yfinance preflight failures: {p1_fail}",
        f"- cache repair failures: {p2_fail}",
        f"- local cache bootstrap rows already present: {p3_bootstrap_already}",
        f"- local cache bootstrap rows with cache after: {p3_local_source_used}",
        f"- event provider safe-mode rows: {event_disabled}",
        f"- event provider no-provider rows: {event_missing_provider}",
        f"- event audit source available: {'YES' if event_audit_available else 'NO'}",
        f"- event audit sentence: {event_sentence}",
        "",
        "## Human Explanation",
        "",
    ]
    if local_cache_only or provider_issue:
        lines.append(
            "The current run is cache-backed and safe-mode friendly, but it is not a clean live-provider refresh. "
            "Historical yfinance preflight/caching audits show failures, while the current selected universe refresh stayed on local-cache-only paths."
        )
    else:
        lines.append(
            "The current run appears fresh enough for read-only review and does not show a provider fallback warning."
        )
    lines.append("")
    return "\n".join(lines), {
        "source_price": rel(root, price_path) if price_path else "MISSING",
        "source_price_row_count": str(len(price_rows)),
        "source_price_status": price_source_status,
        "source_event": rel(root, event_path) if event_path else "MISSING",
        "source_event_row_count": str(len(event_rows)),
        "source_event_status": event_source_status,
        "event_source_role": event_source_role,
        "event_sentence": event_sentence,
        "selected_rows": len(selected_rows),
        "local_cache_used_rows": len(local_source_rows),
        "yfinance_used_rows": len(yfinance_used_rows),
        "cache_only_rows": len(cache_only_rows),
        "failed_price_rows": len(failed_price_rows),
        "price_preflight": "PASS" if preflight_pass else "FAIL",
        "preflight_failures": p1_fail,
        "cache_repair_failures": p2_fail,
        "local_cache_bootstrap_rows": p3_local_source_used,
        "event_provider_no_provider_rows": event_missing_provider,
        "event_audit_available": "TRUE" if event_audit_available else "FALSE",
        "command_center_source": rel(root, cmd_path) if cmd_path else "MISSING",
        "command_center_source_status": cmd_status,
        "current_mode_source": rel(root, current_mode_source_path) if current_mode_source_path else "MISSING",
        "current_mode_source_status": current_mode_source_status,
        "current_mode": current_mode,
        "current_price_mode": current_price_mode,
        "current_price_status": current_price_status,
        "latest_price_min": latest_price_min,
        "latest_price_max": latest_price_max,
    }


def build_risk_dashboard(root: Path, warnings: List[str], coverage: Dict[str, object], freshness: Dict[str, object], rank_source_status: str) -> Tuple[str, Dict[str, object]]:
    cmd_path, cmd_read, cmd_status = choose_first_alias_source(
        root,
        [
            root / "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
            root / "outputs/v18/ops/V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt",
            root / "outputs/v18/ops/V18_16F_READ_FIRST.txt",
            root / "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
        ],
    )
    v16f_read = read_first_map(root / "outputs/v18/ops/V18_16F_READ_FIRST.txt")
    v16h_read = read_first_map(root / "outputs/v18/ops/V18_16H_READ_FIRST.txt")
    event_path, event_rows, event_fields, event_status = choose_event_rows(root)

    auto_trade = first_nonempty(cmd_read.get("AUTO_TRADE"), v16f_read.get("AUTO_TRADE"), "UNKNOWN")
    auto_sell = first_nonempty(cmd_read.get("AUTO_SELL"), v16f_read.get("AUTO_SELL"), "UNKNOWN")
    official = first_nonempty(cmd_read.get("OFFICIAL_DECISION_IMPACT"), v16f_read.get("OFFICIAL_DECISION_IMPACT"), "UNKNOWN")
    validation_fail_count = first_nonempty(v16f_read.get("VALIDATION_FAIL_COUNT"), cmd_read.get("VALIDATION_FAIL_COUNT"), "0")
    same_day_guard = first_nonempty(v16f_read.get("SAME_DAY_PROMOTION_GUARD"), v16h_read.get("SAME_DAY_PROMOTION_GUARD"), "UNKNOWN")
    core_allowed = first_nonempty(v16f_read.get("CORE_PROMOTION_ALLOWED_THIS_RUN"), v16h_read.get("CORE_PROMOTION_ALLOWED_THIS_RUN"), "UNKNOWN")
    rank_source = first_nonempty(rank_source_status, cmd_read.get("RANK_SOURCE_STATUS"), "UNKNOWN")
    coverage_target = first_nonempty(str(coverage.get("coverage_target_met", "")), "UNKNOWN")
    coverage_shortfall = first_nonempty(str(coverage.get("shortfall", "")), "0")
    daily_threshold_source = first_nonempty(str(coverage.get("daily_threshold_coverage_source", "")), "UNKNOWN")
    daily_threshold_source_status = first_nonempty(str(coverage.get("daily_threshold_coverage_source_status", "")), "UNKNOWN")
    daily_threshold_source_modified = first_nonempty(str(coverage.get("daily_threshold_coverage_source_modified_time", "")), "UNKNOWN")
    daily_threshold_source_reason = first_nonempty(str(coverage.get("daily_threshold_coverage_source_selection_reason", "")), "UNKNOWN")
    true_5day_met = first_nonempty(str(coverage.get("true_5day_unique_coverage_met", "")), "UNKNOWN")
    price_preflight = first_nonempty(str(freshness.get("price_preflight", "")), "UNKNOWN")
    current_mode = first_nonempty(str(freshness.get("current_mode", "")), "UNKNOWN")
    current_price_mode = first_nonempty(str(freshness.get("current_price_mode", "")), "UNKNOWN")
    event_audit_available = first_nonempty(str(freshness.get("event_audit_available", "")), "FALSE")

    same_day_guard_upper = same_day_guard.upper()
    same_day_guard_safe = same_day_guard_upper in {"TRUE", "ENABLED", "ON"}
    same_day_guard_unsafe = same_day_guard_upper in {"FALSE", "DISABLED", "OFF"}
    same_day_guard_unknown = same_day_guard_upper not in {"TRUE", "ENABLED", "ON", "FALSE", "DISABLED", "OFF"}

    event_warning = "No event warning discovered."
    if event_rows:
        counts: Dict[str, int] = {}
        for row in event_rows:
            status = normalize(row.get("event_update_status", "")).upper()
            if status:
                counts[status] = counts.get(status, 0) + 1
        top = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())[:3])
        event_warning = f"Event provider statuses: {top}" if top else event_warning
    elif event_audit_available != "TRUE":
        event_warning = "Event audit source missing; event-risk freshness could not be verified."

    lines = [
        "# V18_CURRENT_RISK_DASHBOARD",
        "",
        "| Field | Raw | Meaning | Impact |",
        "| --- | --- | --- | --- |",
        f"| AUTO_TRADE | {auto_trade} | Live trading remains disabled. | No execution path changes. |",
        f"| AUTO_SELL | {auto_sell} | Auto-selling remains disabled. | No automatic exit behavior is enabled. |",
        f"| OFFICIAL_DECISION_IMPACT | {official} | This layer does not alter official decisions. | Official daily logic is unchanged. |",
        f"| VALIDATION_FAIL_COUNT | {validation_fail_count} | Validation errors in current daily chain. | Zero is preferred; non-zero would lower trust. |",
        f"| SAME_DAY_PROMOTION_GUARD | {same_day_guard} | Same-day core promotion protection is active when TRUE/ENABLED/ON. | FALSE/DISABLED/OFF is unsafe; UNKNOWN is degraded. |",
        f"| CORE_PROMOTION_ALLOWED_THIS_RUN | {core_allowed} | Whether core promotion may proceed under the guard. | TRUE means the guard did not block the run. |",
        f"| RANK_SOURCE_STATUS | {rank_source} | Ranking input was found and read. | Missing ranking source would lower trust. |",
        f"| COVERAGE_TARGET_MET | {coverage_target} | Rolling scan coverage target status. | FALSE means the scan did not reach the theoretical target. |",
        f"| COVERAGE_SHORTFALL_COUNT | {coverage_shortfall} | How many names were not scanned versus target. | A shortfall leaves some names less recently refreshed. |",
        f"| DAILY_THRESHOLD_COVERAGE_SOURCE | {daily_threshold_source} | Source used for daily threshold coverage. | Fresh V18.16J/V18.16F evidence is preferred over stale V18.16H audits. |",
        f"| DAILY_THRESHOLD_COVERAGE_SOURCE_STATUS | {daily_threshold_source_status} | Freshness/provenance for daily threshold source. | Fallback or stale sources are reported explicitly. |",
        f"| DAILY_THRESHOLD_COVERAGE_SOURCE_MODIFIED_TIME | {daily_threshold_source_modified} | Filesystem modified time for selected coverage source. | Newest valid daily-threshold evidence is selected. |",
        f"| DAILY_THRESHOLD_COVERAGE_SOURCE_SELECTION_REASON | {shorten(daily_threshold_source_reason, 120)} | Why this daily-threshold source was selected. | Malformed newer candidates are skipped. |",
        f"| TRUE_5DAY_UNIQUE_COVERAGE_MET | {true_5day_met} | Separate true five-day unique universe coverage status. | FALSE caps trust below HIGH even if daily threshold is met. |",
        f"| PRICE_FRESHNESS_MODE | {current_price_mode} | Current price refresh used cache-only or cache-backed mode. | Cache-only mode is usable but not ideal for freshness. |",
        f"| PRICE_PREFLIGHT | {price_preflight} | Historical yfinance/caching preflight result. | FAIL indicates provider or cache repair issues were seen. |",
        f"| EVENT_AUDIT_AVAILABLE | {event_audit_available} | Whether event-risk freshness could be verified from an event audit. | Missing audit degrades freshness confidence. |",
        f"| EVENT_AUDIT_SENTENCE | {shorten(freshness.get('event_sentence', ''), 120)} | Human-readable event-risk summary. | Derived from loaded audit state. |",
        f"| COMMAND_CENTER_SOURCE | {freshness.get('command_center_source', rel(root, cmd_path) if cmd_path else 'MISSING')} | Current command-center alias source used for operator fields. | The human-facing status source is visible. |",
        f"| COMMAND_CENTER_SOURCE_STATUS | {freshness.get('command_center_source_status', cmd_status)} | Parse status for the selected command-center alias. | Missing or malformed aliases are visible. |",
        f"| CURRENT_MODE_SOURCE | {freshness.get('current_mode_source', rel(root, cmd_path) if cmd_path else 'MISSING')} | Current mode alias source used for freshness reporting. | The selected mode source is visible. |",
        f"| CURRENT_MODE_SOURCE_STATUS | {freshness.get('current_mode_source_status', cmd_status)} | Parse status for the selected mode alias. | Missing or malformed aliases are visible. |",
        "",
        "## Warnings",
        "",
        f"- {event_warning}",
        f"- Current data freshness mode: {current_mode}",
        f"- Current cache-backed price mode: {current_price_mode}",
        f"- Coverage target met: {coverage_target}",
        "",
    ]

    if normalize(validation_fail_count) not in {"0", ""}:
        warnings.append(f"Validation failures reported: {validation_fail_count}.")
    if normalize(official).upper() != "NONE":
        warnings.append(f"Official decision impact is not NONE: {official}.")
    if normalize(auto_trade).upper() != "DISABLED" or normalize(auto_sell).upper() != "DISABLED":
        warnings.append("Trading guardrails are not fully disabled as expected.")
    if normalize(rank_source).upper() in {"MISSING", "UNKNOWN", ""}:
        warnings.append("Ranking source status is missing or unknown.")
    if normalize(coverage_target).upper() == "FALSE":
        warnings.append(f"Coverage shortfall remains at {coverage_shortfall} names.")
    if normalize(true_5day_met).upper() == "FALSE":
        warning_text = "True 5-day unique universe coverage remains unresolved; trust level is capped below HIGH."
        if warning_text not in warnings:
            warnings.append(warning_text)
    if normalize(price_preflight).upper() == "FAIL":
        warnings.append("Historical yfinance preflight failed.")
    if same_day_guard_unknown:
        warnings.append("Same-day promotion guard status is unknown; trust level is capped below HIGH.")
    elif same_day_guard_unsafe:
        warnings.append("Same-day promotion guard is explicitly unsafe.")
    if event_audit_available != "TRUE":
        warnings.append("Event audit source missing; event-risk freshness could not be verified.")

    return "\n".join(lines), {
        "auto_trade": auto_trade,
        "auto_sell": auto_sell,
        "official": official,
        "validation_fail_count": validation_fail_count,
        "same_day_guard": same_day_guard,
        "same_day_guard_safe": "TRUE" if same_day_guard_safe else "FALSE",
        "same_day_guard_unknown": "TRUE" if same_day_guard_unknown else "FALSE",
        "core_allowed": core_allowed,
        "rank_source": rank_source,
        "event_audit_available": event_audit_available,
        "coverage_target_met": coverage_target,
        "coverage_shortfall": coverage_shortfall,
        "true_5day_unique_coverage_met": true_5day_met,
        "price_preflight": price_preflight,
        "current_mode": current_mode,
        "current_price_mode": current_price_mode,
        "command_center_source": freshness.get("command_center_source", rel(root, cmd_path) if cmd_path else "MISSING"),
        "command_center_source_status": freshness.get("command_center_source_status", cmd_status),
        "current_mode_source": freshness.get("current_mode_source", rel(root, cmd_path) if cmd_path else "MISSING"),
        "current_mode_source_status": freshness.get("current_mode_source_status", cmd_status),
    }


def build_daily_brief(root: Path, top: Dict[str, object], changes: Dict[str, object], risk: Dict[str, object], coverage: Dict[str, object], freshness: Dict[str, object], warnings: List[str], trust_level: str, today_action: str, main_reason: str) -> str:
    cmd_path, cmd_read, cmd_status = choose_first_alias_source(
        root,
        [
            root / "outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt",
            root / "outputs/v18/ops/V18_CURRENT_ROLLING_UNIVERSE_SCAN_READ_FIRST.txt",
            root / "outputs/v18/ops/V18_16F_READ_FIRST.txt",
            root / "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md",
        ],
    )
    v16f_read = read_first_map(root / "outputs/v18/ops/V18_16F_READ_FIRST.txt")
    auto_trade = first_nonempty(cmd_read.get("AUTO_TRADE"), v16f_read.get("AUTO_TRADE"), "UNKNOWN")
    auto_sell = first_nonempty(cmd_read.get("AUTO_SELL"), v16f_read.get("AUTO_SELL"), "UNKNOWN")
    official = first_nonempty(cmd_read.get("OFFICIAL_DECISION_IMPACT"), v16f_read.get("OFFICIAL_DECISION_IMPACT"), "UNKNOWN")
    validation_fail_count = first_nonempty(v16f_read.get("VALIDATION_FAIL_COUNT"), cmd_read.get("VALIDATION_FAIL_COUNT"), "0")
    coverage_target = first_nonempty(str(coverage.get("coverage_target_met", "")), "UNKNOWN")
    today_scan = first_nonempty(str(coverage.get("today_scan", "")), "UNKNOWN")
    daily_min = first_nonempty(str(coverage.get("daily_min", "")), "UNKNOWN")
    shortfall = first_nonempty(str(coverage.get("shortfall", "")), "UNKNOWN")
    daily_threshold_source = first_nonempty(str(coverage.get("daily_threshold_coverage_source", "")), "UNKNOWN")
    daily_threshold_source_status = first_nonempty(str(coverage.get("daily_threshold_coverage_source_status", "")), "UNKNOWN")
    daily_threshold_source_modified = first_nonempty(str(coverage.get("daily_threshold_coverage_source_modified_time", "")), "UNKNOWN")
    daily_threshold_source_reason = first_nonempty(str(coverage.get("daily_threshold_coverage_source_selection_reason", "")), "UNKNOWN")
    true_5day_met = first_nonempty(str(coverage.get("true_5day_unique_coverage_met", "")), "UNKNOWN")
    true_5day_shortfall = first_nonempty(str(coverage.get("true_5day_unique_shortfall_count", "")), "UNKNOWN")
    same_day_guard = first_nonempty(str(changes.get("same_day_guard", "")), "UNKNOWN")
    rank_source = first_nonempty(str(risk.get("rank_source", "")), "UNKNOWN")

    top_table_rows = []
    for row in top.get("rows", [])[:10]:
        top_table_rows.append({
            "Rank": row.get("Rank", ""),
            "Ticker": row.get("Ticker", ""),
            "Tier": row.get("Tier", ""),
            "Score": row.get("Score", ""),
            "Key Reason": row.get("Key Reason", ""),
            "Data Status": row.get("Data Status", ""),
        })

    if top_table_rows:
        top_table = "\n".join(write_markdown_table(top_table_rows, ["Rank", "Ticker", "Tier", "Score", "Key Reason", "Data Status"]))
    else:
        top_table = "No ranking data was available."

    changed_text = changes.get("summary", "No major universe change detected from available audit files.")
    coverage_text = coverage.get("explanation", "Coverage status unavailable.")
    freshness_text = "Current data is cache-backed and safe-mode oriented; yfinance preflight did not present a clean pass."
    if normalize(str(freshness.get("price_preflight", ""))).upper() == "PASS":
        freshness_text = "Current data appears operationally usable from the available audits."

    machine_status_lines = [
        "```text",
        f"AUTO_TRADE: {auto_trade}",
        f"AUTO_SELL: {auto_sell}",
        f"OFFICIAL_DECISION_IMPACT: {official}",
        f"VALIDATION_FAIL_COUNT: {validation_fail_count}",
        f"COVERAGE_TARGET_MET: {coverage_target}",
        f"DAILY_THRESHOLD_COVERAGE_SOURCE: {daily_threshold_source}",
        f"DAILY_THRESHOLD_COVERAGE_SOURCE_STATUS: {daily_threshold_source_status}",
        f"DAILY_THRESHOLD_COVERAGE_SOURCE_MODIFIED_TIME: {daily_threshold_source_modified}",
        f"DAILY_THRESHOLD_COVERAGE_SOURCE_SELECTION_REASON: {daily_threshold_source_reason}",
        f"DAILY_THRESHOLD_TARGET_MET: {coverage_target}",
        f"DAILY_THRESHOLD_SHORTFALL_COUNT: {shortfall}",
        f"TRUE_5DAY_UNIQUE_COVERAGE_MET: {true_5day_met}",
        f"TRUE_5DAY_UNIQUE_SHORTFALL_COUNT: {true_5day_shortfall}",
        f"TODAY_ROLLING_SCAN_COUNT: {today_scan}",
        f"DAILY_MIN_SCAN_COUNT: {daily_min}",
        f"COVERAGE_SHORTFALL_COUNT: {shortfall}",
        f"SAME_DAY_PROMOTION_GUARD: {same_day_guard}",
        f"RANK_SOURCE_STATUS: {rank_source}",
        "```",
    ]

    packet_refs = [
        "- [V18_CURRENT_TOP_RANKED_CANDIDATES.md](daily_packet/V18_CURRENT_TOP_RANKED_CANDIDATES.md)",
        "- [V18_CURRENT_UNIVERSE_CHANGES.md](daily_packet/V18_CURRENT_UNIVERSE_CHANGES.md)",
        "- [V18_CURRENT_RISK_DASHBOARD.md](daily_packet/V18_CURRENT_RISK_DASHBOARD.md)",
        "- [V18_CURRENT_COVERAGE_STATUS.md](daily_packet/V18_CURRENT_COVERAGE_STATUS.md)",
        "- [V18_CURRENT_DATA_FRESHNESS.md](daily_packet/V18_CURRENT_DATA_FRESHNESS.md)",
    ]

    lines = [
        "# Qutumn Daily Brief",
        "",
        "## 1. Today's Decision",
        f"- Today Action: {today_action}",
        f"- Trade Permission: {auto_trade} / {auto_sell}",
        f"- Daily Trust Level: {trust_level}",
        f"- Main Reason: {main_reason}",
        "",
        "## 2. Top Candidates",
        "",
        top_table,
        "",
        "## 3. Risk Dashboard",
        f"- Data Freshness: {freshness_text}",
        f"- Event Risk: {freshness.get('event_sentence', 'Event audit source missing; event-risk freshness could not be verified.')}",
        f"- Command Center Source: {freshness.get('command_center_source', rel(root, cmd_path) if cmd_path else 'MISSING')} ({freshness.get('command_center_source_status', cmd_status)})",
        f"- Current Mode Source: {freshness.get('current_mode_source', rel(root, cmd_path) if cmd_path else 'MISSING')} ({freshness.get('current_mode_source_status', cmd_status)})",
        f"- Coverage Risk: {coverage_text}",
        f"- Same-Day Promotion Guard: {same_day_guard}",
        f"- Validation Status: {validation_fail_count}",
        f"- Auto Trade / Auto Sell Status: {auto_trade} / {auto_sell}",
        "",
        "## 4. Universe Changes",
        f"- Promotions: {changes.get('promotions', 0)}",
        f"- Demotions: {changes.get('demotions', 0)}",
        f"- Core Daily count: {changes.get('core_daily', 0)}",
        f"- Candidate count: {changes.get('candidate', 0)}",
        f"- Watchlist count: {changes.get('watchlist', 0)}",
        f"- Research count: {changes.get('research', 0)}",
        "",
        "## 5. What Changed Today",
        changed_text if changed_text else "No major universe change detected from available audit files.",
        "",
        "## 6. What To Read Next",
        *packet_refs,
        "",
        "## 7. Machine Status",
        *machine_status_lines,
        "",
    ]
    return "\n".join(lines)


def derive_trust_level(warnings: Sequence[str], coverage: Dict[str, object], freshness: Dict[str, object], risk: Dict[str, object], changes: Dict[str, object]) -> Tuple[str, str, str]:
    validation_fail_count = safe_int(risk.get("validation_fail_count", 0))
    auto_trade = normalize(risk.get("auto_trade", ""))
    auto_sell = normalize(risk.get("auto_sell", ""))
    official = normalize(risk.get("official", ""))
    coverage_target = safe_bool(coverage.get("coverage_target_met", False), False)
    true_5day_unique_met = safe_bool(coverage.get("true_5day_unique_coverage_met", False), False)
    price_preflight = normalize(freshness.get("price_preflight", ""))
    rank_source = normalize(risk.get("rank_source", ""))
    same_day_guard = normalize(risk.get("same_day_guard", ""))
    event_audit_available = normalize(freshness.get("event_audit_available", "FALSE")).upper() == "TRUE"

    same_day_guard_upper = same_day_guard.upper()
    same_day_guard_safe = same_day_guard_upper in {"TRUE", "ENABLED", "ON"}
    same_day_guard_unknown = same_day_guard_upper not in {"TRUE", "ENABLED", "ON", "FALSE", "DISABLED", "OFF"}
    same_day_guard_unsafe = same_day_guard_upper in {"FALSE", "DISABLED", "OFF"}

    safety_ok = auto_trade.upper() == "DISABLED" and auto_sell.upper() == "DISABLED" and official.upper() == "NONE" and same_day_guard_safe
    freshness_ok = price_preflight.upper() == "PASS" and normalize(freshness.get("current_price_mode", "")).upper() not in {"LOCAL_CACHE_ONLY_SAFE_MODE", "CACHE_ONLY"}

    if validation_fail_count > 0 or rank_source.upper() in {"MISSING", "UNKNOWN", ""}:
        return "LOW", "Validation failures or missing ranking source were detected.", "One or more critical status fields are not clean."
    if same_day_guard_unknown:
        return "MEDIUM", "Same-day promotion guard status is unknown; trust level is capped below HIGH.", "The guard is not confirmed safe, so HIGH is not allowed."
    if same_day_guard_unsafe or not safety_ok:
        return "LOW", "A safety guardrail is missing or suspicious.", "Trading guardrails are not fully intact."
    if rank_source.upper().startswith("WARN_"):
        return "MEDIUM", "Ranking source was present but unusable; trust level is capped below HIGH.", "A degraded ranking source prevents HIGH trust."
    if not event_audit_available:
        return "MEDIUM", "Event audit source missing; event-risk freshness could not be verified.", "Missing event evidence prevents HIGH trust."
    if coverage_target and not true_5day_unique_met:
        return "MEDIUM", "Daily threshold coverage is met, but true 5-day unique universe coverage remains unresolved.", "Daily threshold alone is not sufficient for HIGH trust."
    if coverage_target and freshness_ok and validation_fail_count == 0:
        return "HIGH", "Validation is clean, guardrails are intact, coverage target is met, and data freshness appears OK.", "All required daily controls are green."
    if validation_fail_count == 0 and safety_ok and (not coverage_target or not freshness_ok):
        reason_parts: List[str] = []
        if not coverage_target:
            reason_parts.append("coverage target was not met")
        if not freshness_ok:
            reason_parts.append("data freshness is cache-backed or has provider warnings")
        if not event_audit_available:
            reason_parts.append("event-risk freshness could not be verified")
        if not reason_parts:
            reason_parts.append("some daily warning is present")
        return "MEDIUM", " and ".join(reason_parts).capitalize() + ".", "Guardrails are intact, but at least one operational warning remains."
    return "MEDIUM", "Daily status is usable, but a warning remains and the run is best treated conservatively.", "If uncertain, MEDIUM is the safer interpretation."


def build_audit_rows(root: Path, warnings: Sequence[str], top_meta: Dict[str, str], changes: Dict[str, object], coverage: Dict[str, object], freshness: Dict[str, object], risk: Dict[str, object], trust_level: str, today_action: str, main_reason: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    rows.extend([
        {
            "category": "source",
        "source_file": top_meta.get("source", "MISSING"),
        "exists": "YES" if top_meta.get("source", "MISSING") != "MISSING" else "NO",
        "parse_status": top_meta.get("status", "MISSING"),
        "row_count": top_meta.get("row_count", "0"),
        "source_status": top_meta.get("source_status", top_meta.get("status", "MISSING")),
        "used_for": "TOP_CANDIDATES",
        "metric": "",
        "value": "",
        "note": "",
        },
        {
            "category": "source",
            "source_file": changes.get("source", "MISSING"),
            "exists": "YES" if changes.get("source", "MISSING") != "MISSING" else "NO",
            "parse_status": changes.get("status", "MISSING"),
            "row_count": changes.get("row_count", "0"),
            "source_status": changes.get("source_status", changes.get("status", "MISSING")),
            "used_for": "UNIVERSE_CHANGES",
            "metric": "",
            "value": "",
            "note": "",
        },
        {
            "category": "source",
            "source_file": coverage.get("source", "MISSING"),
            "exists": "YES" if coverage.get("source", "MISSING") != "MISSING" else "NO",
            "parse_status": coverage.get("status", "MISSING"),
            "row_count": coverage.get("row_count", "0"),
            "source_status": coverage.get("source_status", coverage.get("status", "MISSING")),
            "used_for": "COVERAGE_STATUS",
            "metric": "",
            "value": "",
            "note": "",
        },
        {
            "category": "source",
            "source_file": freshness.get("source_price", "MISSING"),
            "exists": "YES" if freshness.get("source_price", "MISSING") != "MISSING" else "NO",
            "parse_status": freshness.get("source_price_status", "MISSING"),
            "row_count": freshness.get("source_price_row_count", "0"),
            "source_status": freshness.get("source_price_status", "MISSING"),
            "used_for": "DATA_FRESHNESS",
            "metric": "",
            "value": "",
            "note": "",
        },
        {
            "category": "source",
            "source_file": freshness.get("source_event", "MISSING"),
            "exists": "YES" if freshness.get("source_event", "MISSING") != "MISSING" else "NO",
            "parse_status": freshness.get("source_event_status", "MISSING"),
            "row_count": freshness.get("source_event_row_count", "0"),
            "source_status": freshness.get("source_event_status", "MISSING"),
            "used_for": "DATA_FRESHNESS",
            "metric": "",
            "value": "",
            "note": "",
        },
        {
            "category": "source",
            "source_file": freshness.get("source_event", "MISSING"),
            "exists": "YES" if freshness.get("source_event", "MISSING") != "MISSING" else "NO",
            "parse_status": freshness.get("source_event_status", "MISSING"),
            "row_count": freshness.get("source_event_row_count", "0"),
            "source_status": freshness.get("source_event_status", "MISSING"),
            "used_for": "DATA_FRESHNESS",
            "metric": "event_source_role",
            "value": freshness.get("event_source_role", ""),
            "note": "Visible fallback/origin marker for event audit.",
        },
    ])

    summary_pairs = [
        ("STATUS", STATUS_OK if not warnings else STATUS_WARN),
        ("DAILY_TRUST_LEVEL", trust_level),
        ("TODAY_ACTION", today_action),
        ("MAIN_REASON", main_reason),
        ("AUTO_TRADE", normalize(risk.get("auto_trade", ""))),
        ("AUTO_SELL", normalize(risk.get("auto_sell", ""))),
        ("OFFICIAL_DECISION_IMPACT", normalize(risk.get("official", ""))),
        ("VALIDATION_FAIL_COUNT", normalize(risk.get("validation_fail_count", ""))),
        ("COVERAGE_TARGET_MET", normalize(coverage.get("coverage_target_met", ""))),
        ("DAILY_THRESHOLD_COVERAGE_SOURCE", normalize(coverage.get("daily_threshold_coverage_source", ""))),
        ("DAILY_THRESHOLD_COVERAGE_SOURCE_STATUS", normalize(coverage.get("daily_threshold_coverage_source_status", ""))),
        ("DAILY_THRESHOLD_COVERAGE_SOURCE_MODIFIED_TIME", normalize(coverage.get("daily_threshold_coverage_source_modified_time", ""))),
        ("DAILY_THRESHOLD_COVERAGE_SOURCE_SELECTION_REASON", normalize(coverage.get("daily_threshold_coverage_source_selection_reason", ""))),
        ("DAILY_THRESHOLD_TARGET_MET", normalize(coverage.get("daily_threshold_target_met", ""))),
        ("DAILY_THRESHOLD_SHORTFALL_COUNT", normalize(coverage.get("daily_threshold_shortfall", ""))),
        ("TRUE_5DAY_UNIQUE_COVERAGE_MET", normalize(coverage.get("true_5day_unique_coverage_met", ""))),
        ("TRUE_5DAY_UNIQUE_WARNING_PRESERVED", normalize(coverage.get("true_5day_unique_warning_preserved", ""))),
        ("TODAY_ROLLING_SCAN_COUNT", normalize(coverage.get("today_scan", ""))),
        ("DAILY_MIN_SCAN_COUNT", normalize(coverage.get("daily_min", ""))),
        ("COVERAGE_SHORTFALL_COUNT", normalize(coverage.get("shortfall", ""))),
        ("RANK_SOURCE_STATUS", normalize(risk.get("rank_source", ""))),
        ("PRICE_PREFLIGHT", normalize(freshness.get("price_preflight", ""))),
        ("PRICE_MODE", normalize(freshness.get("current_price_mode", ""))),
        ("COMMAND_CENTER_SOURCE", normalize(freshness.get("command_center_source", ""))),
        ("COMMAND_CENTER_SOURCE_STATUS", normalize(freshness.get("command_center_source_status", ""))),
        ("CURRENT_MODE_SOURCE", normalize(freshness.get("current_mode_source", ""))),
        ("CURRENT_MODE_SOURCE_STATUS", normalize(freshness.get("current_mode_source_status", ""))),
        ("SOURCE_WARNINGS", "; ".join(warnings) if warnings else "NONE"),
    ]
    rows.extend(
        {
            "category": "summary",
            "source_file": "",
            "exists": "",
            "parse_status": "",
            "row_count": "",
            "used_for": "",
            "metric": metric,
            "value": value,
            "note": "",
        }
        for metric, value in summary_pairs
    )
    return rows


def build(root: Path) -> int:
    root = root.resolve()
    warnings: List[str] = []
    ensure_dir(root / READ_CENTER_DIR)
    ensure_dir(root / DAILY_PACKET_DIR)
    ensure_dir(root / OPS_DIR)

    universe_path, universe_rows, universe_fields, universe_status = choose_universe_rows(root)
    top_md, top_rows, top_meta = build_top_candidates(root, universe_rows, warnings)
    changes_md, changes_meta = build_universe_changes(root, universe_rows, warnings)
    coverage_md, coverage_meta = build_coverage_status(root, warnings)
    freshness_md, freshness_meta = build_data_freshness(root, warnings)
    rank_source_status = "OK_SCORE_SOURCE_FOUND" if top_meta.get("usable", "FALSE") == "TRUE" else (
        "WARN_SCORE_SOURCE_EMPTY" if top_meta.get("source", "MISSING") != "MISSING" and top_meta.get("row_count", "0") == "0" else (
            "WARN_SCORE_SOURCE_UNUSABLE" if top_meta.get("source", "MISSING") != "MISSING" else "MISSING"
        )
    )
    risk_md, risk_meta = build_risk_dashboard(root, warnings, coverage_meta, freshness_meta, rank_source_status)

    risk_auto_trade = normalize(risk_meta.get("auto_trade", ""))
    risk_auto_sell = normalize(risk_meta.get("auto_sell", ""))
    risk_official = normalize(risk_meta.get("official", ""))
    validation_fail_count = safe_int(risk_meta.get("validation_fail_count", 0))
    coverage_target = safe_bool(coverage_meta.get("coverage_target_met", False), False)

    trust_level, trust_reason, trust_main = derive_trust_level(warnings, coverage_meta, freshness_meta, risk_meta, changes_meta)
    if trust_level == "HIGH":
        today_action = "Read-only daily refresh with reporting-only outputs."
    elif coverage_target:
        today_action = "Read-only daily refresh; coverage is acceptable but other warnings remain."
    else:
        today_action = "Read-only daily refresh; scan coverage is below the target."

    main_reason = trust_reason
    if warnings and trust_level != "HIGH":
        main_reason = f"{trust_reason} {warnings[0]}"

    brief_md = build_daily_brief(root, {"rows": top_rows}, changes_meta, risk_meta, coverage_meta, freshness_meta, warnings, trust_level, today_action, main_reason)

    audit_rows = build_audit_rows(root, warnings, top_meta, changes_meta, coverage_meta, freshness_meta, risk_meta, trust_level, today_action, main_reason)
    audit_fields = ["category", "source_file", "exists", "parse_status", "row_count", "source_status", "used_for", "metric", "value", "note"]
    write_csv(root / AUDIT_PATH, audit_rows, audit_fields)
    write_text(root / READ_FIRST_PATH, "\n".join([
        f"STATUS: {STATUS_OK if not warnings else STATUS_WARN}",
        f"DAILY_TRUST_LEVEL: {trust_level}",
        f"TODAY_ACTION: {today_action}",
        f"MAIN_REASON: {main_reason}",
        f"AUTO_TRADE: {risk_auto_trade}",
        f"AUTO_SELL: {risk_auto_sell}",
        f"OFFICIAL_DECISION_IMPACT: {risk_official}",
        f"VALIDATION_FAIL_COUNT: {validation_fail_count}",
        f"COVERAGE_TARGET_MET: {coverage_meta.get('coverage_target_met', 'UNKNOWN')}",
        f"DAILY_THRESHOLD_COVERAGE_SOURCE: {coverage_meta.get('daily_threshold_coverage_source', 'UNKNOWN')}",
        f"DAILY_THRESHOLD_COVERAGE_SOURCE_STATUS: {coverage_meta.get('daily_threshold_coverage_source_status', 'UNKNOWN')}",
        f"DAILY_THRESHOLD_COVERAGE_SOURCE_MODIFIED_TIME: {coverage_meta.get('daily_threshold_coverage_source_modified_time', 'UNKNOWN')}",
        f"DAILY_THRESHOLD_COVERAGE_SOURCE_SELECTION_REASON: {coverage_meta.get('daily_threshold_coverage_source_selection_reason', 'UNKNOWN')}",
        f"DAILY_THRESHOLD_TARGET_MET: {coverage_meta.get('daily_threshold_target_met', 'UNKNOWN')}",
        f"DAILY_THRESHOLD_SHORTFALL_COUNT: {coverage_meta.get('daily_threshold_shortfall', 'UNKNOWN')}",
        f"TRUE_5DAY_UNIQUE_COVERAGE_MET: {coverage_meta.get('true_5day_unique_coverage_met', 'UNKNOWN')}",
        f"TRUE_5DAY_UNIQUE_WARNING_PRESERVED: {coverage_meta.get('true_5day_unique_warning_preserved', 'UNKNOWN')}",
        f"TODAY_ROLLING_SCAN_COUNT: {coverage_meta.get('today_scan', 'UNKNOWN')}",
        f"DAILY_MIN_SCAN_COUNT: {coverage_meta.get('daily_min', 'UNKNOWN')}",
        f"COVERAGE_SHORTFALL_COUNT: {coverage_meta.get('shortfall', 'UNKNOWN')}",
        f"WARNINGS: {'; '.join(warnings) if warnings else 'NONE'}",
        f"COMMAND_CENTER_SOURCE: {freshness_meta.get('command_center_source', 'MISSING')}",
        f"COMMAND_CENTER_SOURCE_STATUS: {freshness_meta.get('command_center_source_status', 'MISSING')}",
        f"CURRENT_MODE_SOURCE: {freshness_meta.get('current_mode_source', 'MISSING')}",
        f"CURRENT_MODE_SOURCE_STATUS: {freshness_meta.get('current_mode_source_status', 'MISSING')}",
        f"READ_FIRST: {rel(root, root / BRIEF_PATH)}",
        f"DETAIL_PACKET_DIR: {rel(root, root / DAILY_PACKET_DIR)}",
        "",
    ]))

    write_text(root / BRIEF_PATH, brief_md)
    write_text(root / TOP_CANDIDATES_PATH, top_md)
    write_text(root / UNIVERSE_CHANGES_PATH, changes_md)
    write_text(root / RISK_DASHBOARD_PATH, risk_md)
    write_text(root / COVERAGE_STATUS_PATH, coverage_md)
    write_text(root / DATA_FRESHNESS_PATH, freshness_md)

    print(f"STATUS: {STATUS_OK if not warnings else STATUS_WARN}")
    print(f"DAILY_TRUST_LEVEL: {trust_level}")
    print(f"READ_FIRST: {rel(root, root / BRIEF_PATH)}")
    print(f"PACKET_DIR: {rel(root, root / DAILY_PACKET_DIR)}")
    print(f"AUTO_TRADE: {risk_auto_trade}")
    print(f"AUTO_SELL: {risk_auto_sell}")
    print(f"OFFICIAL_DECISION_IMPACT: {risk_official}")
    print(f"VALIDATION_FAIL_COUNT: {validation_fail_count}")
    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.19A daily readability refactor.")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
