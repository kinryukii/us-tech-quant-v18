#!/usr/bin/env python
"""V18.43A Top-N ranking explainer packet.

Read-only daily Top-N explainability packet. It summarizes why the current
Top-N candidates rank at the top using existing ranking outputs and descriptive
component/neighbor analysis only.
"""

from __future__ import annotations

import argparse
import csv
import math
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


PATCH_VERSION = "V18.43A"
PATCH_FIX_VERSION = "V18.43B_CURRENT_READ_FIRST_GUARD"
PATCH_NAME = "TOPN_RANKING_EXPLAINER_PACKET"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

PRIMARY_RANKING = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
SUPPORTING = [
    ("factor_pack", "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv", "SUPPORTING_CONTEXT"),
    ("technical_timing", "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv", "SUPPORTING_CONTEXT"),
    ("kdj_macd_shadow", "outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv", "SHADOW_ONLY"),
    ("v18_42a_attribution", "outputs/v18/ops/V18_42A_SINGLE_TICKER_RANKING_ATTRIBUTION.csv", "PROVENANCE_ONLY"),
    ("v18_42a_provenance", "outputs/v18/ops/V18_42A_SINGLE_TICKER_INPUT_PROVENANCE.csv", "PROVENANCE_ONLY"),
    ("v18_41a_summary", "outputs/v18/ops/V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_SUMMARY.csv", "PROVENANCE_ONLY"),
    ("v18_41a_read_first", "outputs/v18/ops/V18_41A_READ_FIRST.txt", "PROVENANCE_ONLY"),
    ("clean_operator_status", "outputs/v18/read_center/V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS.md", "PROVENANCE_ONLY"),
    ("daily_brief", "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md", "PROVENANCE_ONLY"),
    ("top_ranked_candidates_md", "outputs/v18/read_center/V18_CURRENT_TOP_RANKED_CANDIDATES.md", "PROVENANCE_ONLY"),
    ("signal_freeze_ledger", "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv", "SUPPORTING_CONTEXT"),
]

OUT_READ_FIRST = "outputs/v18/ops/V18_43A_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_43A_TOPN_RANKING_EXPLAINER_SUMMARY.csv"
OUT_MATRIX = "outputs/v18/ops/V18_43A_TOPN_RANKING_DRIVER_MATRIX.csv"
OUT_GAPS = "outputs/v18/ops/V18_43A_TOPN_CLOSE_RANK_GAPS.csv"
OUT_PROV = "outputs/v18/ops/V18_43A_TOPN_INPUT_PROVENANCE.csv"
OUT_REPORT = "outputs/v18/read_center/V18_43A_TOPN_RANKING_EXPLAINER_PACKET.md"

CUR_SUMMARY = "outputs/v18/ops/V18_CURRENT_TOPN_RANKING_EXPLAINER_SUMMARY.csv"
CUR_MATRIX = "outputs/v18/ops/V18_CURRENT_TOPN_RANKING_DRIVER_MATRIX.csv"
CUR_GAPS = "outputs/v18/ops/V18_CURRENT_TOPN_CLOSE_RANK_GAPS.csv"
CUR_PROV = "outputs/v18/ops/V18_CURRENT_TOPN_INPUT_PROVENANCE.csv"
CUR_READ_FIRST = "outputs/v18/ops/V18_CURRENT_TOPN_RANKING_EXPLAINER_READ_FIRST.txt"
CUR_REPORT = "outputs/v18/read_center/V18_CURRENT_TOPN_RANKING_EXPLAINER_PACKET.md"

SUMMARY_FIELDS = [
    "status",
    "patch_version",
    "patch_fix_version",
    "patch_name",
    "run_id",
    "generated_at",
    "top_n_requested",
    "top_n_effective",
    "ranking_source_path",
    "ranking_source_row_count",
    "score_column",
    "top_score",
    "bottom_score_within_topn",
    "topn_score_spread",
    "close_gap_count",
    "driver_matrix_row_count",
    "provenance_row_count",
    "report_path",
    "current_report_path",
    "write_current_requested",
    "current_alias_written",
    "current_read_first_written",
    "current_read_first_path",
    "official_decision_impact",
    "auto_trade",
    "auto_sell",
    "ranking_logic_changed",
    "factor_weights_changed",
    "signal_freeze_ledger_modified",
    "trading_execution_allowed",
]

MATRIX_FIELDS = [
    "rank",
    "ticker",
    "column_name",
    "ticker_value",
    "pool_median",
    "pool_percentile",
    "driver_class",
    "source_file",
    "role_label",
    "attribution_mode",
]

GAP_FIELDS = [
    "upper_rank",
    "lower_rank",
    "upper_ticker",
    "lower_ticker",
    "upper_score",
    "lower_score",
    "absolute_score_gap",
    "relative_score_gap",
    "reason_close",
]

PROV_FIELDS = ["input_name", "path", "exists", "row_count", "modified_time", "parse_status", "role", "trust_label"]

PATTERNS = [
    "score", "rank", "factor", "technical", "timing", "penalty", "overheat",
    "momentum", "quality", "growth", "value", "volatility", "risk", "earnings",
    "event", "liquidity", "kdj", "macd", "rsi", "bb", "bollinger",
]


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def clean(value: object) -> str:
    return str(value or "").strip()


def norm_ticker(value: object) -> str:
    return clean(value).upper().replace("-", ".")


def to_float(value: object) -> float | None:
    try:
        text = clean(value)
        if not text or text.upper() in {"NAN", "NONE", "NULL"}:
            return None
        number = float(text)
        if math.isnan(number) or math.isinf(number):
            return None
        return number
    except Exception:
        return None


def fmt(value: float | None, digits: int = 4) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as f:
                reader = csv.DictReader(f)
                return [dict(row) for row in reader], list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "READ_ERROR"


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def file_mtime(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def ticker_col(fields: list[str]) -> str | None:
    for name in ("ticker", "yf_ticker", "symbol"):
        for field in fields:
            if field.lower() == name:
                return field
    return None


def rank_col(fields: list[str]) -> str | None:
    for name in ("rank", "candidate_rank", "source_rank"):
        for field in fields:
            if field.lower() == name:
                return field
    return None


def score_col(fields: list[str]) -> str | None:
    for name in ("composite_candidate_score", "candidate_score", "score"):
        for field in fields:
            if field.lower() == name:
                return field
    for field in fields:
        if "score" in field.lower():
            return field
    return None


def name_value(row: dict[str, str]) -> str:
    for field in ("company_name", "company_name_en", "company_name_zh", "chinese_name", "name", "security_name"):
        if clean(row.get(field)):
            return clean(row.get(field))
    return ""


def likely_component(field: str) -> bool:
    lower = field.lower()
    return any(pattern in lower for pattern in PATTERNS)


def median(values: list[float]) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    mid = len(vals) // 2
    if len(vals) % 2:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / 2.0


def percentile(values: list[float], value: float) -> float:
    if not values:
        return 0.0
    return sum(1 for item in values if item <= value) / len(values) * 100.0


def driver_class(field: str, value: str, pct: float | None) -> str:
    lower = field.lower()
    text = value.upper()
    if any(token in text for token in ["FAIL", "MISSING", "AVOID", "DEAD", "WARNING"]):
        return "STRONG_NEGATIVE"
    if any(token in text for token in ["OK", "READY", "GOLDEN", "POSITIVE", "MATCH"]):
        return "POSITIVE"
    if pct is None:
        return "UNKNOWN"
    lower_is_bad = any(token in lower for token in ["penalty", "risk", "overheat", "volatility"])
    p = 100.0 - pct if lower_is_bad else pct
    if p >= 85:
        return "STRONG_POSITIVE"
    if p >= 65:
        return "POSITIVE"
    if p <= 15:
        return "STRONG_NEGATIVE"
    if p <= 35:
        return "NEGATIVE"
    return "NEUTRAL"


def ranking_source(root: Path) -> tuple[Path | None, list[dict[str, str]], list[str], bool]:
    primary = root / PRIMARY_RANKING
    rows, fields, status = read_csv(primary)
    if status == "OK" and rows:
        return primary, rows, fields, False
    candidates_dir = root / "outputs/v18/candidates"
    if candidates_dir.exists():
        ranked = sorted(candidates_dir.glob("*RANKED_CANDIDATES*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        for path in ranked:
            rows, fields, status = read_csv(path)
            if status == "OK" and rows:
                return path, rows, fields, True
    return None, [], [], True


def sorted_rows(rows: list[dict[str, str]], fields: list[str]) -> list[dict[str, str]]:
    rc = rank_col(fields)
    sc = score_col(fields)
    if rc:
        return sorted(rows, key=lambda row: to_float(row.get(rc)) or 10**9)
    if sc:
        return sorted(rows, key=lambda row: -(to_float(row.get(sc)) or -10**9))
    return rows


def load_provenance(root: Path, ranking_path: Path | None, ranking_rows: list[dict[str, str]], fallback: bool) -> tuple[list[dict[str, object]], bool]:
    prov = []
    partial = False
    if ranking_path is not None:
        prov.append({
            "input_name": "primary_ranking",
            "path": str(ranking_path.relative_to(root)) if ranking_path.is_absolute() else str(ranking_path),
            "exists": "TRUE",
            "row_count": len(ranking_rows),
            "modified_time": file_mtime(ranking_path),
            "parse_status": "OK",
            "role": "OFFICIAL_RANKING_INPUT",
            "trust_label": "LOW" if fallback else "HIGH",
        })
    for name, rel, role in SUPPORTING:
        path = root / rel
        rows: list[dict[str, str]] = []
        status = "OK" if path.exists() else "MISSING_OPTIONAL"
        if path.suffix.lower() == ".csv":
            rows, _fields, status = read_csv(path)
            if status == "MISSING":
                status = "MISSING_OPTIONAL"
        if status != "OK":
            partial = True
        prov.append({
            "input_name": name,
            "path": rel,
            "exists": str(path.exists()).upper(),
            "row_count": len(rows) if rows else "",
            "modified_time": file_mtime(path),
            "parse_status": status,
            "role": role,
            "trust_label": "MEDIUM" if status == "OK" else "LOW",
        })
    return prov, partial


def matrix_rows(top_rows: list[dict[str, str]], all_rows: list[dict[str, str]], fields: list[str], source_path: str) -> list[dict[str, object]]:
    rc = rank_col(fields)
    tc = ticker_col(fields)
    out = []
    for row in top_rows:
        ticker = norm_ticker(row.get(tc or ""))
        rank = clean(row.get(rc)) if rc else ""
        for field in fields:
            if not likely_component(field):
                continue
            value = clean(row.get(field))
            nums = [num for num in (to_float(item.get(field)) for item in all_rows) if num is not None]
            val_num = to_float(value)
            med = median(nums)
            pct = percentile(nums, val_num) if val_num is not None and nums else None
            out.append({
                "rank": rank,
                "ticker": ticker,
                "column_name": field,
                "ticker_value": value,
                "pool_median": fmt(med),
                "pool_percentile": fmt(pct),
                "driver_class": driver_class(field, value, pct),
                "source_file": source_path,
                "role_label": "OFFICIAL_RANKING_INPUT",
                "attribution_mode": "DESCRIPTIVE_ONLY",
            })
    return out


def differing_columns(a: dict[str, str], b: dict[str, str], fields: list[str]) -> str:
    diffs = []
    for field in fields:
        if not likely_component(field):
            continue
        av = a.get(field, "")
        bv = b.get(field, "")
        an = to_float(av)
        bn = to_float(bv)
        if an is not None and bn is not None:
            delta = abs(an - bn)
            if delta:
                diffs.append((delta, f"{field}: {av} vs {bv}"))
        elif clean(av) != clean(bv):
            diffs.append((1.0, f"{field}: {av} vs {bv}"))
    diffs.sort(key=lambda x: x[0], reverse=True)
    return "; ".join(text for _delta, text in diffs[:5])


def close_gaps(top_rows: list[dict[str, str]], fields: list[str], score_field: str | None) -> list[dict[str, object]]:
    if not score_field:
        return []
    scores = [to_float(row.get(score_field)) for row in top_rows]
    gaps = []
    numeric_gaps = []
    for idx in range(len(top_rows) - 1):
        upper = scores[idx]
        lower = scores[idx + 1]
        if upper is not None and lower is not None:
            numeric_gaps.append(abs(upper - lower))
    if not numeric_gaps:
        return []
    threshold = max(0.25, median(numeric_gaps) or 0.0)
    tc = ticker_col(fields)
    rc = rank_col(fields)
    for idx in range(len(top_rows) - 1):
        upper_row = top_rows[idx]
        lower_row = top_rows[idx + 1]
        upper = scores[idx]
        lower = scores[idx + 1]
        if upper is None or lower is None:
            continue
        gap = abs(upper - lower)
        if gap <= threshold:
            rel = gap / abs(upper) if upper else None
            gaps.append({
                "upper_rank": clean(upper_row.get(rc)) if rc else idx + 1,
                "lower_rank": clean(lower_row.get(rc)) if rc else idx + 2,
                "upper_ticker": norm_ticker(upper_row.get(tc or "")),
                "lower_ticker": norm_ticker(lower_row.get(tc or "")),
                "upper_score": fmt(upper),
                "lower_score": fmt(lower),
                "absolute_score_gap": fmt(gap),
                "relative_score_gap": fmt(rel, 6),
                "reason_close": differing_columns(upper_row, lower_row, fields),
            })
    return gaps


def quick_label(row: dict[str, str]) -> tuple[str, str]:
    factor = to_float(row.get("factor_pack_score") or row.get("factor_score"))
    tech = to_float(row.get("technical_timing_score"))
    risk_text = " ".join(str(v) for k, v in row.items() if any(x in k.lower() for x in ["risk", "penalty", "overheat", "warning", "event"])).upper()
    if factor is not None and tech is not None:
        if factor >= tech + 5:
            driver = "FACTOR_DRIVEN"
        elif tech >= factor + 5:
            driver = "TECHNICAL_TIMING_DRIVEN"
        else:
            driver = "BALANCED_FACTOR_TECHNICAL"
    elif factor is not None:
        driver = "FACTOR_CONTEXT_AVAILABLE"
    elif tech is not None:
        driver = "TECHNICAL_CONTEXT_AVAILABLE"
    else:
        driver = "DESCRIPTIVE_SCORE_ONLY"
    risk = "RISK_OR_PENALTY_FLAG" if any(token in risk_text for token in ["RISK", "PENALTY", "OVERHEAT", "WARNING", "AVOID"]) else "NO_MAJOR_RISK_LABEL"
    return driver, risk


def drilldown_suggestions(top_rows: list[dict[str, str]], gap_rows: list[dict[str, object]], fields: list[str], limit: int = 5) -> list[str]:
    tc = ticker_col(fields)
    picks = []
    if top_rows:
        picks.append(norm_ticker(top_rows[0].get(tc or "")))
    for gap in gap_rows:
        for key in ("upper_ticker", "lower_ticker"):
            ticker = str(gap.get(key, ""))
            if ticker and ticker not in picks:
                picks.append(ticker)
            if len(picks) >= limit:
                return picks
    for row in top_rows:
        ticker = norm_ticker(row.get(tc or ""))
        text = " ".join(str(v) for v in row.values()).upper()
        if ticker and ticker not in picks and any(token in text for token in ["RISK", "PENALTY", "OVERHEAT", "MISSING"]):
            picks.append(ticker)
        if len(picks) >= limit:
            break
    return picks[:limit]


def render_report(summary: dict[str, object], top_rows: list[dict[str, str]], matrix: list[dict[str, object]], gaps: list[dict[str, object]], prov: list[dict[str, object]], include_hints: bool, fields: list[str]) -> str:
    tc = ticker_col(fields)
    rc = rank_col(fields)
    sc = score_col(fields)
    top_score = to_float(top_rows[0].get(sc)) if top_rows and sc else None
    rows_table = ["| rank | ticker | name | score | delta_prev | delta_rank1 | quick_driver_label | quick_risk_penalty_label | drilldown |", "| ---: | --- | --- | ---: | ---: | ---: | --- | --- | --- |"]
    prev_score = None
    for row in top_rows:
        score = to_float(row.get(sc)) if sc else None
        delta_prev = "" if prev_score is None or score is None else fmt(score - prev_score)
        delta_top = "" if top_score is None or score is None else fmt(score - top_score)
        driver, risk = quick_label(row)
        ticker = norm_ticker(row.get(tc or ""))
        hint = f'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "{ticker}" -NeighborWindow 3 -WriteCurrent' if include_hints else ""
        rows_table.append(f"| {clean(row.get(rc)) if rc else ''} | {ticker} | {name_value(row)} | {fmt(score)} | {delta_prev} | {delta_top} | {driver} | {risk} | `{hint}` |")
        prev_score = score
    common = {}
    for row in matrix:
        cls = str(row.get("driver_class"))
        common[cls] = common.get(cls, 0) + 1
    matrix_table = ["| rank | ticker | column_name | value | percentile | driver_class | role | mode |", "| ---: | --- | --- | --- | ---: | --- | --- | --- |"]
    for row in matrix[:120]:
        matrix_table.append(f"| {row.get('rank')} | {row.get('ticker')} | {row.get('column_name')} | {row.get('ticker_value')} | {row.get('pool_percentile')} | {row.get('driver_class')} | {row.get('role_label')} | {row.get('attribution_mode')} |")
    gap_table = ["| upper_rank | lower_rank | upper_ticker | lower_ticker | upper_score | lower_score | absolute_gap | relative_gap | reason |", "| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |"]
    for row in gaps:
        gap_table.append(f"| {row.get('upper_rank')} | {row.get('lower_rank')} | {row.get('upper_ticker')} | {row.get('lower_ticker')} | {row.get('upper_score')} | {row.get('lower_score')} | {row.get('absolute_score_gap')} | {row.get('relative_score_gap')} | {row.get('reason_close')} |")
    suggestions = drilldown_suggestions(top_rows, gaps, fields)
    suggestion_lines = [f'- `{ticker}`: `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\us-tech-quant\\scripts\\v18\\run_v18_42A_single_ticker_ranking_explainer.ps1" -Ticker "{ticker}" -NeighborWindow 3 -WriteCurrent`' for ticker in suggestions]
    prov_table = ["| input | exists | rows | parse_status | role | trust | path |", "| --- | --- | ---: | --- | --- | --- | --- |"]
    for row in prov:
        prov_table.append(f"| {row.get('input_name')} | {row.get('exists')} | {row.get('row_count')} | {row.get('parse_status')} | {row.get('role')} | {row.get('trust_label')} | {row.get('path')} |")
    return "\n".join([
        "# V18.43A Top-N Ranking Explainer Packet",
        "",
        "## 1. Operator Summary / 操作员摘要",
        f"- TopN requested: {summary.get('top_n_requested')}",
        f"- TopN effective: {summary.get('top_n_effective')}",
        f"- Ranking source file: {summary.get('ranking_source_path')}",
        f"- Candidate pool size: {summary.get('ranking_source_row_count')}",
        f"- Score column: {summary.get('score_column')}",
        f"- Highest score: {summary.get('top_score')}",
        f"- Lowest score inside TopN: {summary.get('bottom_score_within_topn')}",
        f"- TopN score spread: {summary.get('topn_score_spread')}",
        f"- Close rank gap count: {summary.get('close_gap_count')}",
        f"- Status: {summary.get('status')}",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "",
        "## 2. Top-N Ranking Table / Top-N 排名总览",
        *rows_table,
        "",
        "## 3. Why These Names Are Top Ranked / 为什么这些票在前面？",
        "这些候选排在前面，是因为它们在当前 ranking output 中拥有最高的 existing `composite_candidate_score` 或 score column 值。本 patch 不重算排名，只读取已有排名输出并解释可见字段。",
        f"- Common driver class counts: {common}",
        "",
        "## 4. Driver Matrix / 驱动矩阵",
        *matrix_table,
        "",
        "## 5. Close Rank Gaps / 排名接近区",
        *gap_table,
        "",
        "## 6. Factor / Technical / Shadow Context / 因子、技术面、影子信号上下文",
        "- `OFFICIAL_RANKING_INPUT`: 来自主 ranked candidate 文件。",
        "- `SUPPORTING_CONTEXT`: factor/technical/freeze 等辅助上下文。",
        "- `SHADOW_ONLY`: V18.40A KDJ/MACD shadow fields; unless present in official ranking fields, do not treat as official drivers.",
        "- `PROVENANCE_ONLY`: status/read-center provenance.",
        "",
        "## 7. Drilldown Suggestions / 单票深挖建议",
        *suggestion_lines,
        "",
        "## 8. Source Provenance and Trust / 来源与可信度",
        *prov_table,
        "",
        "## 9. Limitations / 限制",
        "- This patch does not recalculate official rank.",
        "- It reads existing current ranking output.",
        "- It does not invent factor weights.",
        "- If no current weight metadata is found, attribution is descriptive only.",
        "- It does not change trading decisions.",
        "- It does not allow trading execution.",
    ]) + "\n"


def run(root: Path, top_n: int, neighbor_window: int, write_current: bool, include_hints: bool, strict: bool) -> int:
    run_id = f"V18_43A_TOPN_RANKING_EXPLAINER_{now_ts()}"
    ranking_path, rows, fields, fallback = ranking_source(root)
    prov, partial = load_provenance(root, ranking_path, rows, fallback)
    if ranking_path is None:
        summary = base_summary("FAIL_V18_43A_NO_RANKING_SOURCE", run_id, top_n, 0, "", 0, "", "", "", "", 0, 0, len(prov), write_current, False)
        write_outputs(root, summary, [], [], prov, "# V18.43A failed: no ranking source\n", write_current)
        return 1
    if not rows:
        summary = base_summary("FAIL_V18_43A_EMPTY_RANKING_SOURCE", run_id, top_n, 0, str(ranking_path), 0, "", "", "", "", 0, 0, len(prov), write_current, False)
        write_outputs(root, summary, [], [], prov, "# V18.43A failed: empty ranking source\n", write_current)
        return 1
    ordered = sorted_rows(rows, fields)
    effective = min(max(top_n, 0), len(ordered))
    top_rows = ordered[:effective]
    sc = score_col(fields)
    top_score = to_float(top_rows[0].get(sc)) if top_rows and sc else None
    bottom_score = to_float(top_rows[-1].get(sc)) if top_rows and sc else None
    matrix = matrix_rows(top_rows, rows, fields, str(ranking_path.relative_to(root)) if ranking_path.is_absolute() else str(ranking_path))
    gaps = close_gaps(top_rows, fields, sc)
    status = "WARN_V18_43A_SUPPORTING_INPUTS_PARTIAL" if partial or fallback else "OK_V18_43A_TOPN_RANKING_EXPLAINER_READY"
    summary = base_summary(status, run_id, top_n, effective, str(ranking_path), len(rows), sc or "", fmt(top_score), fmt(bottom_score), fmt(top_score - bottom_score) if top_score is not None and bottom_score is not None else "", len(gaps), len(matrix), len(prov), write_current, write_current)
    report = render_report(summary, top_rows, matrix, gaps, prov, include_hints, fields)
    write_outputs(root, summary, matrix, gaps, prov, report, write_current)
    return 0


def base_summary(status: str, run_id: str, requested: int, effective: int, source: str, source_rows: int, score: str, top_score: str, bottom_score: str, spread: str, close_gap_count: int, matrix_count: int, prov_count: int, write_requested: bool, current_written: bool) -> dict[str, object]:
    return {
        "status": status,
        "patch_version": PATCH_VERSION,
        "patch_fix_version": PATCH_FIX_VERSION,
        "patch_name": PATCH_NAME,
        "run_id": run_id,
        "generated_at": now_iso(),
        "top_n_requested": requested,
        "top_n_effective": effective,
        "ranking_source_path": source,
        "ranking_source_row_count": source_rows,
        "score_column": score,
        "top_score": top_score,
        "bottom_score_within_topn": bottom_score,
        "topn_score_spread": spread,
        "close_gap_count": close_gap_count,
        "driver_matrix_row_count": matrix_count,
        "provenance_row_count": prov_count,
        "report_path": OUT_REPORT,
        "current_report_path": CUR_REPORT if current_written else "",
        "write_current_requested": str(bool(write_requested)).upper(),
        "current_alias_written": str(bool(current_written)).upper(),
        "current_read_first_written": str(bool(current_written)).upper(),
        "current_read_first_path": CUR_READ_FIRST if current_written else "",
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "ranking_logic_changed": "FALSE",
        "factor_weights_changed": "FALSE",
        "signal_freeze_ledger_modified": "FALSE",
        "trading_execution_allowed": "FALSE",
    }


def render_read_first(summary: dict[str, object]) -> str:
    keys = [
        "STATUS", "PATCH_VERSION", "PATCH_FIX_VERSION", "PATCH_NAME", "TOP_N_REQUESTED", "TOP_N_EFFECTIVE",
        "RANKING_SOURCE_PATH", "RANKING_SOURCE_ROW_COUNT", "SCORE_COLUMN", "TOP_SCORE",
        "BOTTOM_SCORE_WITHIN_TOPN", "TOPN_SCORE_SPREAD", "CLOSE_GAP_COUNT",
        "DRIVER_MATRIX_ROW_COUNT", "PROVENANCE_ROW_COUNT", "REPORT_PATH", "CURRENT_REPORT_PATH",
        "WRITE_CURRENT_REQUESTED", "CURRENT_ALIAS_WRITTEN", "CURRENT_READ_FIRST_WRITTEN",
        "CURRENT_READ_FIRST_PATH", "OFFICIAL_DECISION_IMPACT",
        "AUTO_TRADE", "AUTO_SELL", "RANKING_LOGIC_CHANGED", "FACTOR_WEIGHTS_CHANGED",
        "SIGNAL_FREEZE_LEDGER_MODIFIED", "TRADING_EXECUTION_ALLOWED",
    ]
    return "\n".join(f"{key}: {summary.get(key.lower(), '')}" for key in keys) + "\n"


def write_outputs(root: Path, summary: dict[str, object], matrix: list[dict[str, object]], gaps: list[dict[str, object]], prov: list[dict[str, object]], report: str, write_current: bool) -> None:
    read_first = render_read_first(summary)
    write_text(root / OUT_READ_FIRST, read_first)
    write_csv(root / OUT_SUMMARY, [summary], SUMMARY_FIELDS)
    write_csv(root / OUT_MATRIX, matrix, MATRIX_FIELDS)
    write_csv(root / OUT_GAPS, gaps, GAP_FIELDS)
    write_csv(root / OUT_PROV, prov, PROV_FIELDS)
    write_text(root / OUT_REPORT, report)
    if write_current:
        write_csv(root / CUR_SUMMARY, [summary], SUMMARY_FIELDS)
        write_csv(root / CUR_MATRIX, matrix, MATRIX_FIELDS)
        write_csv(root / CUR_GAPS, gaps, GAP_FIELDS)
        write_csv(root / CUR_PROV, prov, PROV_FIELDS)
        write_text(root / CUR_REPORT, report)
        write_text(root / CUR_READ_FIRST, read_first)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--neighbor-window", type=int, default=2)
    parser.add_argument("--write-current", action="store_true")
    parser.add_argument("--include-single-ticker-hints", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    return run(Path(args.root).resolve(), args.top_n, args.neighbor_window, args.write_current, args.include_single_ticker_hints, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
