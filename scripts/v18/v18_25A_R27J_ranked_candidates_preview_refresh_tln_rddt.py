from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUS_OK = "OK_V18_25A_R27J_RANKED_CANDIDATES_PREVIEW_READY"
STATUS_WARN = "WARN_V18_25A_R27J_PREVIEW_REFRESH_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_25A_R27J_FORBIDDEN_MODIFIED"

MODE = "PREVIEW_ONLY_RANKED_CANDIDATES_REFRESH"

TARGET_TICKERS = ["RDDT", "TLN"]
TARGET_SET = set(TARGET_TICKERS)
EXPECTED_R27I_STATUS = "OK_V18_25A_R27I_CANDIDATE_READINESS_AUDIT_READY"

R27I_READ_FIRST = "outputs/v18/ops/V18_25A_R27I_READ_FIRST.txt"
R27I_PLAN = "outputs/v18/candidates/V18_25A_R27I_CURRENT_RANKED_CANDIDATE_PREVIEW_REFRESH_PLAN.csv"
R27I_AUDIT = "outputs/v18/candidates/V18_25A_R27I_CURRENT_CANDIDATE_READINESS_AUDIT.csv"

FACTOR_PACK = "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
TECH_TIMING = "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv"
CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
PRICE_CACHE_DIR = "state/v18/price_cache"
ROLLING_LEDGER = "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv"

OUT_DIR = "outputs/v18/candidates"
OUT_PREVIEW = f"{OUT_DIR}/V18_25A_R27J_CURRENT_RANKED_CANDIDATES_PREVIEW.csv"
OUT_VALIDATION = f"{OUT_DIR}/V18_25A_R27J_CURRENT_RANKED_CANDIDATES_PREVIEW_VALIDATION.csv"
OUT_APPEND_ROWS = f"{OUT_DIR}/V18_25A_R27J_CURRENT_RANKED_CANDIDATE_APPEND_ROWS.csv"
OUT_PROMOTION_PLAN = f"{OUT_DIR}/V18_25A_R27J_CURRENT_PROMOTION_PLAN.csv"
OUT_SUMMARY = f"{OUT_DIR}/V18_25A_R27J_CURRENT_SUMMARY.csv"
OUT_READ_FIRST = "outputs/v18/ops/V18_25A_R27J_READ_FIRST.txt"
OUT_REPORT = "outputs/v18/ops/V18_25A_R27J_CURRENT_RANKED_CANDIDATES_PREVIEW_REFRESH_REPORT.md"

CANDIDATE_FIELDS = [
    "rank",
    "ticker",
    "composite_candidate_score",
    "ranking_source_policy",
    "primary_score_source_files",
    "audit_only_source_files",
    "score_source_status",
    "score_source_files",
    "score_source_columns",
    "latest_price_date",
    "latest_close",
    "technical_status",
    "event_risk_status",
    "overheat_status",
    "pullback_status",
    "execution_status",
    "final_action",
    "reason",
]

VALIDATION_FIELDS = [
    "ticker",
    "current_present",
    "preview_present",
    "factor_score_present",
    "technical_score_present",
    "preview_rank",
    "preview_score",
    "validation_status",
    "error_message",
]

APPEND_FIELDS = CANDIDATE_FIELDS

PROMOTION_FIELDS = [
    "ticker",
    "preview_rank",
    "preview_score",
    "promotion_action",
    "promotion_allowed",
    "blocker",
    "next_action",
]

SUMMARY_FIELDS = ["metric", "value", "expected", "status", "notes"]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "R27I_STATUS",
    "TARGET_TICKER_COUNT",
    "TARGET_TICKERS",
    "CURRENT_RANKED_CANDIDATE_ROW_COUNT",
    "PREVIEW_RANKED_CANDIDATE_ROW_COUNT",
    "APPEND_ROW_COUNT",
    "TARGETS_PRESENT_IN_PREVIEW_COUNT",
    "DUPLICATE_TICKER_COUNT",
    "SCHEMA_MATCH_CURRENT",
    "EXISTING_CURRENT_TICKERS_PRESERVED",
    "TARGET_SCORE_PRESENT_COUNT",
    "RANK_RECOMPUTED",
    "PROMOTION_TO_CURRENT_RECOMMENDED",
    "PRICE_CACHE_MODIFIED",
    "ROLLING_LEDGER_MODIFIED",
    "FACTOR_PACK_MODIFIED",
    "TECHNICAL_TIMING_MODIFIED",
    "CANDIDATES_CURRENT_MODIFIED",
    "EXTERNAL_FETCH_EXECUTED",
    "BACKTEST_EXECUTED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "VALIDATION_FAIL_COUNT",
    "FORBIDDEN_MODIFIED",
    "NEXT_RECOMMENDED_STEP",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    return [], []


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except Exception:
            continue
    return ""


def read_first_value(path: Path, key: str) -> str:
    prefix = f"{key}:"
    for line in read_text(path).splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper()


def non_null(value: object) -> bool:
    return str(value or "").strip() not in {"", "nan", "NaN", "None", "NULL"}


def to_float(value: object) -> Optional[float]:
    try:
        text = str(value or "").strip().replace(",", "")
        return float(text) if text else None
    except Exception:
        return None


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


def build_ticker_map(rows: Sequence[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {norm_ticker(row.get("ticker")): row for row in rows if norm_ticker(row.get("ticker"))}


def header_matches_current(current_fields: Sequence[str], preview_fields: Sequence[str]) -> bool:
    return list(current_fields) == list(preview_fields)


def composite_score(factor_score: float, technical_score: float, overheat: Optional[float], volatility: Optional[float]) -> float:
    score = factor_score * 0.40 + technical_score * 0.30
    if overheat is not None:
        score -= abs(overheat)
    if volatility is not None:
        score -= abs(volatility)
    return round(score, 6)


def final_action(technical_status: str, overheat_status: str, pullback_status: str) -> str:
    status_text = " ".join([technical_status, overheat_status, pullback_status]).upper()
    if any(token in status_text for token in ("AVOID", "RISK", "EXIT", "OVERHEAT", "NO_TRADE")):
        return "NO_TRADE_REVIEW_ONLY"
    if any(token in status_text for token in ("PULLBACK", "LOWER", "WATCH")):
        return "WAIT_PULLBACK_REVIEW_ONLY"
    return "REVIEW_ONLY"


def safe_str(value: object) -> str:
    return str(value or "").strip()


def row_without_rank(row: Dict[str, str]) -> Dict[str, str]:
    return {k: v for k, v in row.items() if k != "rank"}


def render_read_first(values: Dict[str, object]) -> str:
    return "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n"


def render_report(values: Dict[str, object], validation_rows: Sequence[Dict[str, object]], promotion_rows: Sequence[Dict[str, object]]) -> str:
    validation_text = "\n".join(f"- {row['ticker']}: {row['validation_status']}" for row in validation_rows)
    promotion_text = "\n".join(f"- {row['ticker']}: {row['promotion_action']} -> {row['promotion_allowed']}" for row in promotion_rows)
    return "\n".join(
        [
            "# V18.25A-R27J Ranked Candidates Preview Refresh",
            "",
            f"- STATUS: {values['STATUS']}",
            f"- MODE: {values['MODE']}",
            f"- RUN_ID: {values['RUN_ID']}",
            f"- R27I_STATUS: {values['R27I_STATUS']}",
            "",
            "## Validation",
            "",
            validation_text if validation_text else "- None.",
            "",
            "## Promotion Plan",
            "",
            promotion_text if promotion_text else "- None.",
            "",
            "## Guardrails",
            "",
            f"- PRICE_CACHE_MODIFIED: {values['PRICE_CACHE_MODIFIED']}",
            f"- ROLLING_LEDGER_MODIFIED: {values['ROLLING_LEDGER_MODIFIED']}",
            f"- FACTOR_PACK_MODIFIED: {values['FACTOR_PACK_MODIFIED']}",
            f"- TECHNICAL_TIMING_MODIFIED: {values['TECHNICAL_TIMING_MODIFIED']}",
            f"- CANDIDATES_CURRENT_MODIFIED: {values['CANDIDATES_CURRENT_MODIFIED']}",
            f"- EXTERNAL_FETCH_EXECUTED: {values['EXTERNAL_FETCH_EXECUTED']}",
            f"- BACKTEST_EXECUTED: {values['BACKTEST_EXECUTED']}",
            f"- OFFICIAL_DECISION_IMPACT: {values['OFFICIAL_DECISION_IMPACT']}",
            f"- AUTO_TRADE: {values['AUTO_TRADE']}",
            f"- AUTO_SELL: {values['AUTO_SELL']}",
            f"- FORBIDDEN_MODIFIED: {values['FORBIDDEN_MODIFIED']}",
            "",
            f"NEXT_RECOMMENDED_STEP: {values['NEXT_RECOMMENDED_STEP']}",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = f"V18_25A_R27J_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    factor_before = file_sig(root / FACTOR_PACK)
    tech_before = file_sig(root / TECH_TIMING)
    current_before = file_sig(root / CURRENT_CANDIDATES)
    price_before = file_sig(root / PRICE_CACHE_DIR)
    ledger_before = file_sig(root / ROLLING_LEDGER)

    blockers: List[str] = []
    r27i_status = read_first_value(root / R27I_READ_FIRST, "STATUS")
    if not (root / R27I_READ_FIRST).exists():
        blockers.append(f"missing required input: {R27I_READ_FIRST}")
    if r27i_status != EXPECTED_R27I_STATUS:
        blockers.append(f"R27I status is {r27i_status or 'MISSING'}")
    if read_first_value(root / R27I_READ_FIRST, "READY_FOR_RANKED_CANDIDATE_PREVIEW_REFRESH_COUNT") != "2":
        blockers.append("R27I ready-for-preview count is not 2")
    if read_first_value(root / R27I_READ_FIRST, "BLOCKED_COUNT") != "0":
        blockers.append("R27I blocked count is not 0")
    if read_first_value(root / R27I_READ_FIRST, "RANKED_CANDIDATE_PREVIEW_REFRESH_RECOMMENDED") != "TRUE":
        blockers.append("R27I did not recommend preview refresh")
    if read_first_value(root / R27I_READ_FIRST, "FORBIDDEN_MODIFIED") != "FALSE":
        blockers.append("R27I forbidden modified flag was not FALSE")

    if not (root / R27I_PLAN).exists():
        blockers.append(f"missing required input: {R27I_PLAN}")
    if not (root / R27I_AUDIT).exists():
        blockers.append(f"missing required input: {R27I_AUDIT}")

    factor_rows, factor_fields = read_csv(root / FACTOR_PACK)
    tech_rows, tech_fields = read_csv(root / TECH_TIMING)
    current_rows, current_fields = read_csv(root / CURRENT_CANDIDATES)
    factor_by = build_ticker_map(factor_rows)
    tech_by = build_ticker_map(tech_rows)
    current_by = build_ticker_map(current_rows)

    factor_score_col = "factor_pack_score" if "factor_pack_score" in factor_fields else ("factor_score" if "factor_score" in factor_fields else "")
    factor_rank_col = "factor_pack_rank" if "factor_pack_rank" in factor_fields else ("rank" if "rank" in factor_fields else "")
    tech_score_col = "technical_timing_score" if "technical_timing_score" in tech_fields else ("technical_score" if "technical_score" in tech_fields else "")

    current_count = len(current_rows)
    current_tickers = [norm_ticker(row.get("ticker")) for row in current_rows]
    current_ticker_set = set(current_tickers)
    duplicate_count = len(current_tickers) - len(current_ticker_set)
    schema_match_current = header_matches_current(current_fields, CANDIDATE_FIELDS)

    append_rows: List[Dict[str, object]] = []
    validation_rows: List[Dict[str, object]] = []
    promotion_rows: List[Dict[str, object]] = []
    preview_blocks: List[str] = []
    targets_present_in_preview = 0
    target_score_present_count = 0
    blocked_count = 0

    scored_rows: List[Tuple[float, float, str, Dict[str, object]]] = []
    current_normalized: Dict[str, Dict[str, str]] = {}
    for row in current_rows:
        ticker = norm_ticker(row.get("ticker"))
        current_normalized[ticker] = dict(row)
        score = to_float(row.get("composite_candidate_score"))
        if score is None:
            blockers.append(f"current candidate row missing score: {ticker}")
            score = float("-inf")
        existing_rank = to_int(row.get("rank"), 999999)
        scored_rows.append((score, float(existing_rank), ticker, dict(row)))

    for ticker in TARGET_TICKERS:
        factor_row = factor_by.get(ticker, {})
        tech_row = tech_by.get(ticker, {})
        current_present = ticker in current_by
        factor_present = bool(factor_row)
        technical_present = bool(tech_row)
        factor_score_present = non_null(factor_row.get(factor_score_col))
        technical_score_present = non_null(tech_row.get(tech_score_col))
        if factor_present and technical_present and factor_score_present and technical_score_present:
            overheat = to_float(factor_row.get("overheat_penalty"))
            volatility = to_float(factor_row.get("volatility_penalty"))
            factor_score = to_float(factor_row.get(factor_score_col))
            technical_score = to_float(tech_row.get(tech_score_col))
            assert factor_score is not None and technical_score is not None
            comp = composite_score(factor_score, technical_score, overheat, volatility)
            technical_status = safe_str(tech_row.get("technical_signal") or tech_row.get("technical_status") or tech_row.get("technical_warning_label"))
            overheat_status = safe_str(tech_row.get("gamma_squeeze_risk_label") or factor_row.get("overheat_penalty"))
            pullback_status = safe_str(tech_row.get("bb_status"))
            new_row = {
                "rank": 0,
                "ticker": ticker,
                "composite_candidate_score": f"{comp:.6f}",
                "ranking_source_policy": "PRIMARY_CURRENT_ONLY_R25F_PREVIEW",
                "primary_score_source_files": f"{FACTOR_PACK};{TECH_TIMING}",
                "audit_only_source_files": "",
                "score_source_status": "OK_SCORE_SOURCE_FOUND",
                "score_source_files": f"{FACTOR_PACK};{TECH_TIMING}",
                "score_source_columns": f"{factor_score_col};{tech_score_col};factor_pack_rank;overheat_penalty;volatility_penalty",
                "latest_price_date": safe_str(factor_row.get("latest_price_date") or tech_row.get("price_date")),
                "latest_close": safe_str(factor_row.get("latest_close") or tech_row.get("close")),
                "technical_status": technical_status,
                "event_risk_status": "",
                "overheat_status": overheat_status,
                "pullback_status": pullback_status,
                "execution_status": "",
                "final_action": final_action(technical_status, overheat_status, pullback_status),
                "reason": "R27J preview refreshed from current official factor pack and technical timing only; no external fetch.",
            }
            append_rows.append(new_row)
            scored_rows.append((comp, float(999999), ticker, new_row))
            targets_present_in_preview += 1
            target_score_present_count += 1
            candidate_status = "ALREADY_IN_CURRENT_RANKED_CANDIDATES"
            if not current_present:
                candidate_status = "READY_FOR_RANKED_CANDIDATE_PREVIEW_REFRESH"
            next_action = "R27K_PROMOTE_RANKED_CANDIDATES_PREVIEW_TO_CURRENT"
            validation_status = "PASS" if not current_present else "PASS"
            preview_blocks.append(ticker)
        else:
            blocked_count += 1
            candidate_status = "BLOCKED"
            next_action = "REVIEW_R27H_POST_MERGE_VALIDATION"
            validation_status = "FAIL"
            errors: List[str] = []
            if not factor_present:
                errors.append("missing_factor_row")
            if not technical_present:
                errors.append("missing_technical_row")
            if not factor_score_present:
                errors.append("missing_factor_score")
            if not technical_score_present:
                errors.append("missing_technical_score")
            blockers.extend(errors)
        validation_rows.append(
            {
                "ticker": ticker,
                "current_present": str(current_present).upper(),
                "preview_present": str(factor_present and technical_present and factor_score_present and technical_score_present).upper(),
                "factor_score_present": str(factor_score_present).upper(),
                "technical_score_present": str(technical_score_present).upper(),
                "preview_rank": "",
                "preview_score": "",
                "validation_status": validation_status,
                "error_message": "" if validation_status == "PASS" else ";".join(sorted(set(blockers))),
            }
        )
        promotion_rows.append(
            {
                "ticker": ticker,
                "preview_rank": "",
                "preview_score": "",
                "promotion_action": "PROMOTE_PREVIEW_TO_CURRENT",
                "promotion_allowed": "TRUE" if validation_status == "PASS" else "FALSE",
                "blocker": "" if validation_status == "PASS" else ";".join(sorted(set(blockers))),
                "next_action": "R27K_PROMOTE_RANKED_CANDIDATES_PREVIEW_TO_CURRENT" if validation_status == "PASS" else "REVIEW_R27H_POST_MERGE_VALIDATION",
            }
        )

    # Compute preview ranks from the combined candidate set.
    scored_rows_sorted = sorted(scored_rows, key=lambda item: (-item[0], item[1], item[2]))
    preview_rows: List[Dict[str, object]] = []
    preview_by_ticker: Dict[str, Dict[str, object]] = {}
    for idx, (_, _, ticker, row) in enumerate(scored_rows_sorted, 1):
        out = dict(row)
        out["rank"] = idx
        preview_rows.append(out)
        preview_by_ticker[ticker] = out

    # Fill validation and promotion details with preview ranks/scores.
    for row in validation_rows:
        ticker = norm_ticker(row["ticker"])
        preview_row = preview_by_ticker.get(ticker, {})
        row["preview_rank"] = preview_row.get("rank", "")
        row["preview_score"] = preview_row.get("composite_candidate_score", "")
        row["validation_status"] = "PASS" if ticker in preview_by_ticker and row["preview_present"] == "TRUE" else "FAIL"
    for row in promotion_rows:
        ticker = norm_ticker(row["ticker"])
        preview_row = preview_by_ticker.get(ticker, {})
        row["preview_rank"] = preview_row.get("rank", "")
        row["preview_score"] = preview_row.get("composite_candidate_score", "")

    preview_count = len(preview_rows)
    append_row_count = len(append_rows)
    duplicate_ticker_count = preview_count - len({norm_ticker(row.get("ticker")) for row in preview_rows})
    targets_present_in_preview = sum(1 for ticker in TARGET_TICKERS if ticker in preview_by_ticker)
    target_score_present_count = sum(1 for ticker in TARGET_TICKERS if non_null(preview_by_ticker.get(ticker, {}).get("composite_candidate_score")))
    rank_recomputed = True

    # Existing current tickers preserved if the preview still contains all current tickers with non-rank fields unchanged.
    preview_by_ticker_non_rank = {ticker: row_without_rank(row) for ticker, row in preview_by_ticker.items()}
    existing_current_tickers_preserved = all(
        ticker in preview_by_ticker_non_rank and row_without_rank(current_normalized[ticker]) == preview_by_ticker_non_rank[ticker]
        for ticker in current_normalized
    )
    preview_schema_match = header_matches_current(current_fields, CANDIDATE_FIELDS)
    promotion_to_current_recommended = (
        preview_count == current_count + 2
        and duplicate_ticker_count == 0
        and targets_present_in_preview == 2
        and target_score_present_count == 2
        and existing_current_tickers_preserved
        and preview_schema_match
        and blocked_count == 0
    )

    write_csv(root / OUT_PREVIEW, preview_rows, CANDIDATE_FIELDS)
    write_csv(root / OUT_VALIDATION, validation_rows, VALIDATION_FIELDS)
    write_csv(root / OUT_APPEND_ROWS, append_rows, APPEND_FIELDS)
    write_csv(root / OUT_PROMOTION_PLAN, promotion_rows, PROMOTION_FIELDS)

    factor_modified = file_sig(root / FACTOR_PACK) != factor_before
    tech_modified = file_sig(root / TECH_TIMING) != tech_before
    current_modified = file_sig(root / CURRENT_CANDIDATES) != current_before
    price_modified = file_sig(root / PRICE_CACHE_DIR) != price_before
    ledger_modified = file_sig(root / ROLLING_LEDGER) != ledger_before
    forbidden_modified = factor_modified or tech_modified or current_modified or price_modified or ledger_modified

    status = STATUS_OK if promotion_to_current_recommended and blocked_count == 0 and duplicate_ticker_count == 0 and preview_schema_match else STATUS_WARN
    if blockers and status == STATUS_OK:
        status = STATUS_WARN
    if forbidden_modified:
        status = STATUS_FAIL

    values: Dict[str, object] = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "R27I_STATUS": r27i_status or "MISSING",
        "TARGET_TICKER_COUNT": len(TARGET_TICKERS),
        "TARGET_TICKERS": ",".join(TARGET_TICKERS),
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": current_count,
        "PREVIEW_RANKED_CANDIDATE_ROW_COUNT": preview_count,
        "APPEND_ROW_COUNT": append_row_count,
        "TARGETS_PRESENT_IN_PREVIEW_COUNT": targets_present_in_preview,
        "DUPLICATE_TICKER_COUNT": duplicate_ticker_count,
        "SCHEMA_MATCH_CURRENT": str(preview_schema_match).upper(),
        "EXISTING_CURRENT_TICKERS_PRESERVED": str(existing_current_tickers_preserved).upper(),
        "TARGET_SCORE_PRESENT_COUNT": target_score_present_count,
        "RANK_RECOMPUTED": str(rank_recomputed).upper(),
        "PROMOTION_TO_CURRENT_RECOMMENDED": str(promotion_to_current_recommended).upper(),
        "PRICE_CACHE_MODIFIED": "FALSE",
        "ROLLING_LEDGER_MODIFIED": "FALSE",
        "FACTOR_PACK_MODIFIED": "FALSE",
        "TECHNICAL_TIMING_MODIFIED": "FALSE",
        "CANDIDATES_CURRENT_MODIFIED": str(current_modified).upper(),
        "EXTERNAL_FETCH_EXECUTED": "FALSE",
        "BACKTEST_EXECUTED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
        "VALIDATION_FAIL_COUNT": 1 if status == STATUS_FAIL else 0,
        "FORBIDDEN_MODIFIED": str(forbidden_modified).upper(),
        "NEXT_RECOMMENDED_STEP": "R27K_PROMOTE_RANKED_CANDIDATES_PREVIEW_TO_CURRENT" if promotion_to_current_recommended else "REVIEW_R27H_POST_MERGE_VALIDATION",
    }

    summary_rows = [
        summary_row("R27I_STATUS", r27i_status or "MISSING", EXPECTED_R27I_STATUS, r27i_status == EXPECTED_R27I_STATUS),
        summary_row("CURRENT_RANKED_CANDIDATE_ROW_COUNT", current_count, 250, current_count == 250),
        summary_row("PREVIEW_RANKED_CANDIDATE_ROW_COUNT", preview_count, 252, preview_count == 252),
        summary_row("APPEND_ROW_COUNT", append_row_count, 2, append_row_count == 2),
        summary_row("TARGETS_PRESENT_IN_PREVIEW_COUNT", targets_present_in_preview, 2, targets_present_in_preview == 2),
        summary_row("DUPLICATE_TICKER_COUNT", duplicate_ticker_count, 0, duplicate_ticker_count == 0),
        summary_row("SCHEMA_MATCH_CURRENT", str(preview_schema_match).upper(), "TRUE", preview_schema_match),
        summary_row("TARGET_SCORE_PRESENT_COUNT", target_score_present_count, 2, target_score_present_count == 2),
        summary_row("RANK_RECOMPUTED", str(rank_recomputed).upper(), "TRUE", rank_recomputed),
        summary_row("PROMOTION_TO_CURRENT_RECOMMENDED", str(promotion_to_current_recommended).upper(), "TRUE", promotion_to_current_recommended),
    ]

    write_csv(root / OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_text(root / OUT_READ_FIRST, render_read_first(values))
    write_text(root / OUT_REPORT, render_report(values, validation_rows, promotion_rows))

    print(f"STATUS: {status}")
    print(f"MODE: {MODE}")
    print(f"READ_FIRST: {root / OUT_READ_FIRST}")
    return 1 if status == STATUS_FAIL else 0


def summary_row(metric: str, value: object, expected: object, ok: bool, notes: str = "") -> Dict[str, object]:
    return {"metric": metric, "value": value, "expected": expected, "status": "OK" if ok else "WARN", "notes": notes}


if __name__ == "__main__":
    raise SystemExit(main())
