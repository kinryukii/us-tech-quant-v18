#!/usr/bin/env python
"""V18.42A single ticker ranking / score explainer.

Read-only explainer for an existing current ranked candidate pool. It explains
available fields, neighbor differences, and source provenance without changing
rankings, factor weights, candidates, ledgers, account state, or trading logic.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import math
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


PATCH_VERSION = "V18.42A"
PATCH_FIX_VERSION = "V18.42B_ALIAS_GUARD"
PATCH_NAME = "SINGLE_TICKER_RANKING_EXPLAINER"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

PRIMARY_RANKING = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
SUPPORTING = [
    ("factor_pack", "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv", "SUPPORTING_CONTEXT"),
    ("technical_timing", "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv", "SUPPORTING_CONTEXT"),
    ("kdj_macd_shadow", "outputs/v18/technical_timing/V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv", "SHADOW_ONLY"),
    ("v18_41a_summary", "outputs/v18/ops/V18_41A_DAILY_CLEAN_OPERATOR_PIPELINE_SUMMARY.csv", "PROVENANCE_ONLY"),
    ("v18_41a_read_first", "outputs/v18/ops/V18_41A_READ_FIRST.txt", "PROVENANCE_ONLY"),
    ("clean_operator_status", "outputs/v18/read_center/V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS.md", "PROVENANCE_ONLY"),
    ("daily_brief", "outputs/v18/read_center/V18_CURRENT_DAILY_BRIEF.md", "PROVENANCE_ONLY"),
    ("top_ranked_candidates_md", "outputs/v18/read_center/V18_CURRENT_TOP_RANKED_CANDIDATES.md", "PROVENANCE_ONLY"),
    ("signal_freeze_ledger", "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv", "SUPPORTING_CONTEXT"),
]

OUT_READ_FIRST = "outputs/v18/ops/V18_42A_READ_FIRST.txt"
OUT_SUMMARY = "outputs/v18/ops/V18_42A_SINGLE_TICKER_RANKING_EXPLAINER_SUMMARY.csv"
OUT_ATTRIBUTION = "outputs/v18/ops/V18_42A_SINGLE_TICKER_RANKING_ATTRIBUTION.csv"
OUT_NEIGHBORS = "outputs/v18/ops/V18_42A_SINGLE_TICKER_NEIGHBOR_COMPARISON.csv"
OUT_PROVENANCE = "outputs/v18/ops/V18_42A_SINGLE_TICKER_INPUT_PROVENANCE.csv"
OUT_REPORT = "outputs/v18/read_center/V18_42A_SINGLE_TICKER_RANKING_EXPLAINER_REPORT.md"

CURRENT_SUMMARY = "outputs/v18/ops/V18_CURRENT_SINGLE_TICKER_RANKING_EXPLAINER_SUMMARY.csv"
CURRENT_ATTRIBUTION = "outputs/v18/ops/V18_CURRENT_SINGLE_TICKER_RANKING_ATTRIBUTION.csv"
CURRENT_NEIGHBORS = "outputs/v18/ops/V18_CURRENT_SINGLE_TICKER_NEIGHBOR_COMPARISON.csv"
CURRENT_PROVENANCE = "outputs/v18/ops/V18_CURRENT_SINGLE_TICKER_INPUT_PROVENANCE.csv"
CURRENT_REPORT = "outputs/v18/read_center/V18_CURRENT_SINGLE_TICKER_RANKING_EXPLAINER.md"

SUMMARY_FIELDS = [
    "status",
    "patch_version",
    "patch_fix_version",
    "patch_name",
    "run_id",
    "generated_at",
    "ticker",
    "ticker_found",
    "ranking_source_path",
    "ranking_source_row_count",
    "target_rank",
    "target_score_column",
    "target_score_value",
    "neighbor_window",
    "attribution_row_count",
    "provenance_row_count",
    "report_path",
    "current_report_path",
    "write_current_requested",
    "current_alias_written",
    "current_alias_skip_reason",
    "official_decision_impact",
    "auto_trade",
    "auto_sell",
    "ranking_logic_changed",
    "factor_weights_changed",
    "signal_freeze_ledger_modified",
    "trading_execution_allowed",
    "next_recommended_step",
]

ATTR_FIELDS = [
    "ticker",
    "column_name",
    "ticker_value",
    "pool_median",
    "pool_percentile",
    "direction_label",
    "source_file",
    "role_label",
    "attribution_mode",
    "notes",
]

NEIGHBOR_FIELDS = [
    "target_ticker",
    "neighbor_rank",
    "neighbor_ticker",
    "company_name",
    "composite_score",
    "delta_score_vs_target",
    "top_differing_columns",
]

PROV_FIELDS = ["input_name", "path", "exists", "row_count", "modified_time", "parse_status", "role", "trust_label"]

PATTERNS = [
    "score",
    "rank",
    "factor",
    "technical",
    "timing",
    "penalty",
    "overheat",
    "momentum",
    "quality",
    "growth",
    "value",
    "volatility",
    "risk",
    "earnings",
    "event",
    "liquidity",
    "kdj",
    "macd",
    "rsi",
    "bb",
    "bollinger",
]


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def norm_ticker(value: object) -> str:
    return str(value or "").strip().upper().replace("-", ".")


def clean(value: object) -> str:
    return str(value or "").strip()


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


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def file_mtime(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def ticker_col(fields: list[str]) -> str | None:
    for candidate in ("ticker", "yf_ticker", "symbol"):
        for field in fields:
            if field.lower() == candidate:
                return field
    return None


def rank_col(fields: list[str]) -> str | None:
    for candidate in ("rank", "candidate_rank", "source_rank"):
        for field in fields:
            if field.lower() == candidate:
                return field
    return None


def score_col(fields: list[str]) -> str | None:
    preferred = ["composite_candidate_score", "candidate_score", "score"]
    for candidate in preferred:
        for field in fields:
            if field.lower() == candidate:
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


def by_ticker(rows: list[dict[str, str]], fields: list[str]) -> dict[str, dict[str, str]]:
    col = ticker_col(fields)
    out: dict[str, dict[str, str]] = {}
    if not col:
        return out
    for row in rows:
        ticker = norm_ticker(row.get(col))
        if ticker and ticker not in out:
            out[ticker] = row
    return out


def percentile(values: list[float], value: float) -> float:
    if not values:
        return 0.0
    below = sum(1 for x in values if x <= value)
    return below / len(values) * 100.0


def median(values: list[float]) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    mid = len(vals) // 2
    if len(vals) % 2:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / 2.0


def likely_component(field: str) -> bool:
    lower = field.lower()
    return any(pattern in lower for pattern in PATTERNS)


def direction_for(field: str, value: str, med: float | None, pct: float | None) -> str:
    lower = field.lower()
    text = value.upper()
    if any(token in text for token in ["FAIL", "MISSING", "AVOID", "RISK", "OVERHEAT", "DEAD", "WARNING"]):
        return "NEGATIVE"
    if any(token in text for token in ["OK", "READY", "POSITIVE", "GOLDEN", "MATCH", "WATCH"]):
        return "POSITIVE"
    if pct is None:
        return "UNKNOWN"
    lower_is_bad = any(token in lower for token in ["penalty", "risk", "overheat", "volatility"])
    if lower_is_bad:
        if pct <= 35:
            return "POSITIVE"
        if pct >= 65:
            return "NEGATIVE"
        return "NEUTRAL"
    if pct >= 65:
        return "POSITIVE"
    if pct <= 35:
        return "NEGATIVE"
    return "NEUTRAL"


def load_supporting(root: Path) -> tuple[dict[str, tuple[list[dict[str, str]], list[str], str, str, str]], list[dict[str, object]]]:
    loaded = {}
    prov = []
    for name, rel, role in SUPPORTING:
        path = root / rel
        rows: list[dict[str, str]] = []
        fields: list[str] = []
        if path.suffix.lower() == ".csv":
            rows, fields, status = read_csv(path)
        else:
            status = "OK" if path.exists() else "MISSING_OPTIONAL"
        if status == "MISSING":
            status = "MISSING_OPTIONAL"
        loaded[name] = (rows, fields, status, rel, role)
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
    return loaded, prov


def attribution_rows(ticker: str, ranking_rows: list[dict[str, str]], fields: list[str], target: dict[str, str], source_path: str, supporting: dict[str, tuple[list[dict[str, str]], list[str], str, str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for field in fields:
        if not likely_component(field):
            continue
        value = clean(target.get(field))
        nums = [x for x in (to_float(row.get(field)) for row in ranking_rows) if x is not None]
        val_num = to_float(value)
        med = median(nums)
        pct = percentile(nums, val_num) if val_num is not None and nums else None
        rows.append({
            "ticker": ticker,
            "column_name": field,
            "ticker_value": value,
            "pool_median": fmt(med),
            "pool_percentile": fmt(pct),
            "direction_label": direction_for(field, value, med, pct),
            "source_file": source_path,
            "role_label": "OFFICIAL_RANKING_INPUT",
            "attribution_mode": "DESCRIPTIVE_ONLY",
            "notes": "Primary ranking output column; no reliable current formula weight metadata parsed.",
        })

    for _name, (srows, sfields, status, rel, role) in supporting.items():
        if status != "OK" or not srows or not sfields:
            continue
        idx = by_ticker(srows, sfields)
        srow = idx.get(ticker)
        if not srow:
            continue
        for field in sfields:
            if field.lower() in {"ticker", "yf_ticker", "symbol"} or not likely_component(field):
                continue
            value = clean(srow.get(field))
            nums = [x for x in (to_float(row.get(field)) for row in srows) if x is not None]
            val_num = to_float(value)
            med = median(nums)
            pct = percentile(nums, val_num) if val_num is not None and nums else None
            rows.append({
                "ticker": ticker,
                "column_name": field,
                "ticker_value": value,
                "pool_median": fmt(med),
                "pool_percentile": fmt(pct),
                "direction_label": direction_for(field, value, med, pct),
                "source_file": rel,
                "role_label": role,
                "attribution_mode": "DESCRIPTIVE_ONLY",
                "notes": "Supporting/shadow/provenance context; not treated as official driver unless present in primary ranking output.",
            })
    return rows


def sorted_ranking(rows: list[dict[str, str]], fields: list[str]) -> list[dict[str, str]]:
    rc = rank_col(fields)
    sc = score_col(fields)
    if rc:
        return sorted(rows, key=lambda r: to_float(r.get(rc)) or 10**9)
    if sc:
        return sorted(rows, key=lambda r: -(to_float(r.get(sc)) or -10**9))
    return rows


def differing_columns(target: dict[str, str], neighbor: dict[str, str], fields: list[str]) -> str:
    diffs = []
    for field in fields:
        if field.lower() in {"ticker", "yf_ticker", "symbol"}:
            continue
        tv = target.get(field, "")
        nv = neighbor.get(field, "")
        tn = to_float(tv)
        nn = to_float(nv)
        if tn is not None and nn is not None:
            delta = abs(nn - tn)
            if delta:
                diffs.append((delta, f"{field}: {tv} -> {nv}"))
        elif clean(tv) != clean(nv) and likely_component(field):
            diffs.append((1.0, f"{field}: {tv} -> {nv}"))
    diffs.sort(key=lambda x: x[0], reverse=True)
    return "; ".join(text for _, text in diffs[:5])


def neighbor_rows(ticker: str, rows: list[dict[str, str]], fields: list[str], target_idx: int, window: int, sc: str | None) -> list[dict[str, object]]:
    target = rows[target_idx]
    target_score = to_float(target.get(sc)) if sc else None
    rc = rank_col(fields)
    out = []
    lo = max(0, target_idx - window)
    hi = min(len(rows), target_idx + window + 1)
    for idx in range(lo, hi):
        row = rows[idx]
        score = to_float(row.get(sc)) if sc else None
        out.append({
            "target_ticker": ticker,
            "neighbor_rank": clean(row.get(rc)) if rc else idx + 1,
            "neighbor_ticker": norm_ticker(row.get(ticker_col(fields) or "")),
            "company_name": name_value(row),
            "composite_score": fmt(score) if score is not None else clean(row.get(sc)) if sc else "",
            "delta_score_vs_target": fmt(score - target_score) if score is not None and target_score is not None else "",
            "top_differing_columns": "TARGET" if idx == target_idx else differing_columns(target, row, fields),
        })
    return out


def close_matches(ticker: str, candidates: list[str]) -> list[str]:
    prefix = [x for x in candidates if x.startswith(ticker)]
    substr = [x for x in candidates if ticker in x and x not in prefix]
    fuzzy = [x for x in difflib.get_close_matches(ticker, candidates, n=10, cutoff=0.4) if x not in prefix and x not in substr]
    return (prefix + substr + fuzzy)[:15]


def render_report(summary: dict[str, object], target: dict[str, str] | None, attribution: list[dict[str, object]], neighbors: list[dict[str, object]], prov: list[dict[str, object]], suggestions: list[str]) -> str:
    ticker = summary["ticker"]
    positives = [r for r in attribution if r.get("direction_label") == "POSITIVE"][:8]
    negatives = [r for r in attribution if r.get("direction_label") == "NEGATIVE"][:8]
    attr_table = ["| column_name | ticker_value | pool_median | pool_percentile | direction | source | role | mode |", "| --- | --- | ---: | ---: | --- | --- | --- | --- |"]
    for row in attribution[:80]:
        attr_table.append(f"| {row.get('column_name')} | {row.get('ticker_value')} | {row.get('pool_median')} | {row.get('pool_percentile')} | {row.get('direction_label')} | {row.get('source_file')} | {row.get('role_label')} | {row.get('attribution_mode')} |")
    neighbor_table = ["| rank | ticker | name | score | delta_vs_target | top_differing_columns |", "| ---: | --- | --- | ---: | ---: | --- |"]
    for row in neighbors:
        neighbor_table.append(f"| {row.get('neighbor_rank')} | {row.get('neighbor_ticker')} | {row.get('company_name')} | {row.get('composite_score')} | {row.get('delta_score_vs_target')} | {row.get('top_differing_columns')} |")
    prov_table = ["| input | exists | rows | parse_status | role | trust | path |", "| --- | --- | ---: | --- | --- | --- | --- |"]
    for row in prov:
        prov_table.append(f"| {row.get('input_name')} | {row.get('exists')} | {row.get('row_count')} | {row.get('parse_status')} | {row.get('role')} | {row.get('trust_label')} | {row.get('path')} |")

    if summary["ticker_found"] != "TRUE":
        top_table = ["| rank | ticker | name | score |", "| ---: | --- | --- | ---: |"]
        for row in neighbors:
            top_table.append(f"| {row.get('neighbor_rank')} | {row.get('neighbor_ticker')} | {row.get('company_name')} | {row.get('composite_score')} |")
        return "\n".join([
            "# V18.42A Single Ticker Ranking Explainer",
            "",
            "## 1. Operator Summary / 操作员摘要",
            f"- Ticker: `{ticker}`",
            "- TICKER_FOUND: FALSE",
            f"- Status: {summary['status']}",
            f"- Ranking source file: {summary['ranking_source_path']}",
            "- OFFICIAL_DECISION_IMPACT: NONE",
            "- AUTO_TRADE: DISABLED",
            "- AUTO_SELL: DISABLED",
            "",
            "## Missing Ticker / 未找到 ticker",
            "请求的 ticker 不在当前 ranked candidate pool 中。本报告没有崩溃，也没有修改任何候选池。",
            f"- Close matches: {', '.join(suggestions) if suggestions else 'NONE'}",
            "",
            "## Current Top Candidates / 当前 Top 候选",
            *top_table,
            "",
            "## Source Provenance and Trust / 来源与可信度",
            *prov_table,
            "",
            "## Limitations / 限制",
            "- This explainer does not recalculate the official rank.",
            "- It reads existing current ranking output.",
            "- It does not invent factor weights.",
        ]) + "\n"

    strongest_pos = "; ".join(f"{r.get('column_name')}={r.get('ticker_value')}" for r in positives) or "未发现明确正向字段"
    strongest_neg = "; ".join(f"{r.get('column_name')}={r.get('ticker_value')}" for r in negatives) or "未发现明确负向字段"
    return "\n".join([
        "# V18.42A Single Ticker Ranking Explainer",
        "",
        "## 1. Operator Summary / 操作员摘要",
        f"- Ticker: `{ticker}`",
        f"- Company/name: {name_value(target or {})}",
        f"- Current rank: {summary['target_rank']}",
        f"- Candidate pool size: {summary['ranking_source_row_count']}",
        f"- Composite score column/value: {summary['target_score_column']} = {summary['target_score_value']}",
        f"- Latest signal/as-of date: {summary.get('latest_signal_date', '')}",
        f"- Ranking source file: {summary['ranking_source_path']}",
        f"- Report status: {summary['status']}",
        "- OFFICIAL_DECISION_IMPACT: NONE",
        "- AUTO_TRADE: DISABLED",
        "- AUTO_SELL: DISABLED",
        "",
        "## 2. Why This Rank? / 为什么排在这里？",
        f"这个 ticker 排在当前名次，直接原因是当前 ranked candidate 输出中 `{summary['target_score_column']}` 为 `{summary['target_score_value']}`。本解释器不重算官方排名，只读取已有排名输出。",
        "它相对前后名候选的差异，主要来自下方 neighbor comparison 中差异最大的字段。",
        f"- Strongest positive descriptive drivers: {strongest_pos}",
        f"- Strongest negative/penalty descriptive drivers: {strongest_neg}",
        "- 未发现可靠当前权重文件时，所有 attribution 均标记为 DESCRIPTIVE_ONLY，不声称精确公式权重。",
        "",
        "## 3. Score Component Breakdown / 分数组件拆解",
        *attr_table,
        "",
        "## 4. Neighbor Comparison / 前后名对比",
        "为什么它没有排得更高：上方候选在 composite score 或若干组件字段上更强。为什么它没有排得更低：下方候选在这些字段上相对弱。",
        *neighbor_table,
        "",
        "## 5. Factor / Technical / Shadow Context / 因子、技术面、影子信号上下文",
        "- OFFICIAL_RANKING_INPUT: 来自主 ranked candidate 文件的字段。",
        "- SUPPORTING_CONTEXT: factor/technical/freeze 等辅助上下文。",
        "- SHADOW_ONLY: V18.40A KDJ/MACD shadow fields are research-only unless explicitly present in current ranking fields.",
        "- PROVENANCE_ONLY: read-center/status provenance only.",
        "",
        "## 6. Source Provenance and Trust / 来源与可信度",
        *prov_table,
        "",
        "## 7. Limitations / 限制",
        "- This explainer does not recalculate the official rank.",
        "- It reads existing current ranking output.",
        "- It explains available columns and relative differences.",
        "- It does not invent factor weights.",
        "- If no current weight metadata is found, attribution is descriptive only.",
    ]) + "\n"


def run(root: Path, ticker: str, top_n: int, neighbor_window: int, strict: bool, write_current: bool, allow_current_missing_overwrite: bool) -> int:
    run_id = f"V18_42A_SINGLE_TICKER_RANKING_EXPLAINER_{now_ts()}"
    generated_at = now_iso()
    requested = norm_ticker(ticker)
    ranking_path, ranking_rows, fields, used_fallback = ranking_source(root)
    supporting, prov = load_supporting(root)
    current_report_path = str(root / CURRENT_REPORT) if write_current else ""

    if ranking_path is None or not ranking_rows:
        status = "FAIL_V18_42A_NO_RANKING_SOURCE"
        summary = base_summary(status, run_id, generated_at, requested, "FALSE", "", 0, "", "", neighbor_window, 0, len(prov), current_report_path)
        if write_current:
            summary["write_current_requested"] = "TRUE"
            summary["current_alias_written"] = "FALSE"
            summary["current_alias_skip_reason"] = "NO_RANKING_SOURCE"
            summary["current_report_path"] = ""
        write_all(root, summary, [], [], prov, render_report(summary, None, [], [], prov, []), False)
        return 1

    tc = ticker_col(fields)
    idx = by_ticker(ranking_rows, fields)
    sorted_rows = sorted_ranking(ranking_rows, fields)
    sorted_idx = {norm_ticker(row.get(tc or "")): i for i, row in enumerate(sorted_rows)}
    target = idx.get(requested)
    sc = score_col(fields)
    rc = rank_col(fields)
    suggestions = close_matches(requested, list(idx))
    primary_prov = {
        "input_name": "primary_ranking",
        "path": str(ranking_path.relative_to(root)) if ranking_path.is_absolute() else str(ranking_path),
        "exists": "TRUE",
        "row_count": len(ranking_rows),
        "modified_time": file_mtime(ranking_path),
        "parse_status": "OK",
        "role": "OFFICIAL_RANKING_INPUT",
        "trust_label": "LOW" if used_fallback or target is None else "HIGH",
    }
    all_prov = [primary_prov] + prov

    if target is None:
        status = "FAIL_V18_42A_TICKER_NOT_FOUND_STRICT" if strict else "WARN_V18_42A_SINGLE_TICKER_NOT_FOUND"
        summary = base_summary(status, run_id, generated_at, requested, "FALSE", str(ranking_path), len(ranking_rows), "", sc or "", neighbor_window, 0, len(all_prov), current_report_path)
        if write_current:
            summary["write_current_requested"] = "TRUE"
            if allow_current_missing_overwrite:
                summary["current_alias_written"] = "TRUE"
                summary["current_alias_skip_reason"] = "ALLOW_CURRENT_MISSING_OVERWRITE"
            else:
                summary["current_alias_written"] = "FALSE"
                summary["current_alias_skip_reason"] = "TICKER_NOT_FOUND"
                summary["current_report_path"] = ""
        top_rows_for_report = neighbor_rows(requested, sorted_rows, fields, 0, max(top_n - 1, 0), sc) if sorted_rows else []
        report = render_report(summary, None, [], top_rows_for_report, all_prov, suggestions)
        write_all(root, summary, [], top_rows_for_report, all_prov, report, write_current and (allow_current_missing_overwrite or False))
        return 1 if strict else 0

    missing_important = any(row["parse_status"] != "OK" for row in prov)
    status = "WARN_V18_42A_SUPPORTING_INPUTS_PARTIAL" if missing_important else "OK_V18_42A_SINGLE_TICKER_RANKING_EXPLAINER_READY"
    target_rank = clean(target.get(rc)) if rc else str(sorted_idx.get(requested, 0) + 1)
    target_score = clean(target.get(sc)) if sc else ""
    attribution = attribution_rows(requested, ranking_rows, fields, target, str(ranking_path.relative_to(root)) if ranking_path.is_absolute() else str(ranking_path), supporting)
    neighbors = neighbor_rows(requested, sorted_rows, fields, sorted_idx[requested], neighbor_window, sc)
    summary = base_summary(status, run_id, generated_at, requested, "TRUE", str(ranking_path), len(ranking_rows), target_rank, sc or "", neighbor_window, len(attribution), len(all_prov), current_report_path, target_score)
    if write_current:
        summary["write_current_requested"] = "TRUE"
        summary["current_alias_written"] = "TRUE"
        summary["current_alias_skip_reason"] = ""
    read41a = parse_kv(root / "outputs/v18/ops/V18_41A_READ_FIRST.txt")
    summary["latest_signal_date"] = read41a.get("LATEST_SIGNAL_DATE", "")
    report = render_report(summary, target, attribution, neighbors, all_prov, [])
    write_all(root, summary, attribution, neighbors, all_prov, report, write_current)
    return 0


def base_summary(status: str, run_id: str, generated_at: str, ticker: str, found: str, source: str, row_count: int, rank: str, score_column: str, neighbor_window: int, attr_count: int, prov_count: int, current_report_path: str, score_value: str = "") -> dict[str, object]:
    return {
        "status": status,
        "patch_version": PATCH_VERSION,
        "patch_fix_version": PATCH_FIX_VERSION,
        "patch_name": PATCH_NAME,
        "run_id": run_id,
        "generated_at": generated_at,
        "ticker": ticker,
        "ticker_found": found,
        "ranking_source_path": source,
        "ranking_source_row_count": row_count,
        "target_rank": rank,
        "target_score_column": score_column,
        "target_score_value": score_value,
        "neighbor_window": neighbor_window,
        "attribution_row_count": attr_count,
        "provenance_row_count": prov_count,
        "report_path": "outputs/v18/read_center/V18_42A_SINGLE_TICKER_RANKING_EXPLAINER_REPORT.md",
        "current_report_path": current_report_path,
        "write_current_requested": "TRUE" if current_report_path else "FALSE",
        "current_alias_written": "FALSE",
        "current_alias_skip_reason": "" if current_report_path else "WRITE_CURRENT_NOT_REQUESTED",
        "official_decision_impact": OFFICIAL_DECISION_IMPACT,
        "auto_trade": AUTO_TRADE,
        "auto_sell": AUTO_SELL,
        "ranking_logic_changed": "FALSE",
        "factor_weights_changed": "FALSE",
        "signal_freeze_ledger_modified": "FALSE",
        "trading_execution_allowed": "FALSE",
        "next_recommended_step": "Read the generated ticker explainer report; no ranking/trading action is automated.",
    }


def render_read_first(summary: dict[str, object]) -> str:
    keys = [
        "STATUS", "PATCH_VERSION", "PATCH_FIX_VERSION", "PATCH_NAME", "TICKER", "TICKER_FOUND", "RANKING_SOURCE_PATH",
        "RANKING_SOURCE_ROW_COUNT", "TARGET_RANK", "TARGET_SCORE_COLUMN", "TARGET_SCORE_VALUE",
        "NEIGHBOR_WINDOW", "ATTRIBUTION_ROW_COUNT", "PROVENANCE_ROW_COUNT", "REPORT_PATH",
        "CURRENT_REPORT_PATH", "WRITE_CURRENT_REQUESTED", "CURRENT_ALIAS_WRITTEN",
        "CURRENT_ALIAS_SKIP_REASON", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL",
        "RANKING_LOGIC_CHANGED", "FACTOR_WEIGHTS_CHANGED", "SIGNAL_FREEZE_LEDGER_MODIFIED",
        "TRADING_EXECUTION_ALLOWED",
    ]
    return "\n".join(f"{key}: {summary.get(key.lower(), '')}" for key in keys) + "\n"


def write_all(root: Path, summary: dict[str, object], attribution: list[dict[str, object]], neighbors: list[dict[str, object]], prov: list[dict[str, object]], report: str, write_current: bool) -> None:
    write_text(root / OUT_READ_FIRST, render_read_first(summary))
    write_csv(root / OUT_SUMMARY, [summary], SUMMARY_FIELDS)
    write_csv(root / OUT_ATTRIBUTION, attribution, ATTR_FIELDS)
    write_csv(root / OUT_NEIGHBORS, neighbors, NEIGHBOR_FIELDS)
    write_csv(root / OUT_PROVENANCE, prov, PROV_FIELDS)
    write_text(root / OUT_REPORT, report)
    if write_current:
        write_csv(root / CURRENT_SUMMARY, [summary], SUMMARY_FIELDS)
        write_csv(root / CURRENT_ATTRIBUTION, attribution, ATTR_FIELDS)
        write_csv(root / CURRENT_NEIGHBORS, neighbors, NEIGHBOR_FIELDS)
        write_csv(root / CURRENT_PROVENANCE, prov, PROV_FIELDS)
        write_text(root / CURRENT_REPORT, report)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--neighbor-window", type=int, default=3)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--write-current", action="store_true")
    parser.add_argument("--allow-current-missing-overwrite", action="store_true")
    args = parser.parse_args()
    return run(Path(args.root).resolve(), args.ticker, args.top_n, args.neighbor_window, args.strict, args.write_current, args.allow_current_missing_overwrite)


if __name__ == "__main__":
    raise SystemExit(main())
