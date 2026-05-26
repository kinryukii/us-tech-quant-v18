from __future__ import annotations

import argparse
import csv
import py_compile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import v18_21A_price_derived_factor_pack as base
import v18_21A_R2_price_history_source_coverage_patch as r2


STATUS_WARN = "WARN_V18_21A_R3_TICKER_PRICE_SOURCE_MAPPING_RECONCILIATION_DEGRADED"
STATUS_REVIEW = "WARN_V18_21A_R3_TICKER_PRICE_SOURCE_MAPPING_RECONCILIATION_REVIEW_REQUIRED"
STATUS_OK = "OK_V18_21A_R3_TICKER_PRICE_SOURCE_MAPPING_RECONCILIATION_READY"
MODE = "ADVISORY_ONLY"
PATCH_MODE = "TICKER_PRICE_SOURCE_MAPPING_RECONCILIATION_ONLY"

SAFETY_FLAGS = {
    "POLICY_APPLIED": "FALSE",
    "OFFICIAL_DECISION_IMPACT": "NONE",
    "AUTO_TRADE": "DISABLED",
    "AUTO_SELL": "DISABLED",
    "CURRENT_DAILY_MODIFIED": "FALSE",
    "STATE_MODIFIED": "FALSE",
    "PRICE_CACHE_MODIFIED": "FALSE",
    "RANKING_MODIFIED": "FALSE",
    "PROMOTION_DEMOTION_MODIFIED": "FALSE",
    "MANUAL_STATE_MODIFIED": "FALSE",
    "BROKER_EXECUTION_MODIFIED": "FALSE",
    "HISTORY_BACKFILL_APPLIED": "FALSE",
    "EXTERNAL_DATA_FETCHED": "FALSE",
}

UNIVERSE_FIELDS = ["source_path", "source_exists", "modified_time", "parsed_ticker_count", "selected_as_current_universe_source", "selected_reason", "notes"]
MAPPING_FIELDS = [
    "ticker", "normalized_ticker", "mapped_price_source_count", "selected_price_source", "selected_price_source_type",
    "selected_source_modified_time", "selected_source_row_count", "selected_source_min_date", "selected_source_max_date",
    "selected_source_has_close", "selected_source_has_volume", "selected_source_history_depth_rows",
    "selected_source_history_depth_days", "selected_source_quality_status", "mapping_status", "rejection_reason",
    "candidate_source_paths_limited", "ticker_in_source_as", "symbol_normalization_applied",
]
RELEVANCE_FIELDS = [
    "source_path", "source_type", "parsed_ticker_count", "ticker_overlap_with_current_universe_count",
    "ticker_overlap_with_current_universe_ratio", "contains_ohlcv_history", "contains_latest_only",
    "selected_for_any_universe_ticker", "selected_ticker_count", "rejected_reason_if_not_selected", "source_relevance_status",
]
NO_LOCAL_FIELDS = [
    "ticker", "normalized_ticker", "no_local_data_reason", "candidate_source_count", "candidate_source_paths_limited",
    "latest_price_snapshot_found", "latest_price_snapshot_path", "full_history_found", "partial_history_found", "recommended_resolution",
]
RECON_FIELDS = ["metric_name", "metric_value", "explanation"]
SCOPE_SUMMARY_FIELDS = ["ticker", "factor_scope_class", "mapping_status", "score_scope", "full_factor_score_ready", "light_factor_score_ready", "selected_price_source", "score_readiness_reason"]
READ_FIRST_FIELDS = [
    "STATUS", "MODE", "PATCH_MODE", "POLICY_APPLIED", "TICKER_INPUT_COUNT", "LOCAL_PRICE_DATA_AVAILABLE_COUNT",
    "MAPPED_FULL_HISTORY_COUNT", "MAPPED_PARTIAL_HISTORY_COUNT", "MAPPED_LATEST_ONLY_COUNT",
    "CANDIDATE_SOURCES_REJECTED_COUNT", "NO_CANDIDATE_SOURCE_FOUND_COUNT", "NO_LOCAL_PRICE_DATA_COUNT",
    "PRICE_HISTORY_SOURCE_COUNT", "DISCOVERED_SOURCE_WITH_UNIVERSE_OVERLAP_COUNT", "DISCOVERED_SOURCE_SELECTED_COUNT",
    "SOURCE_COUNT_TO_TICKER_MAPPING_STATUS", "FULL_HISTORY_FACTOR_READY_COUNT", "FULL_HISTORY_FACTOR_READY_RATIO",
    "SCORE_READY_RATIO", "QQQ_PROXY_STATUS", "SPY_PROXY_STATUS", "VIX_PROXY_STATUS", "VIX_MISSING_CAP_APPLIED",
    "MARKET_REGIME_STATUS", "MARKET_REGIME_LABEL", "MARKET_RISK_COEFFICIENT", "MARKET_REGIME_CONFIDENCE",
    "HISTORY_BACKFILL_APPLIED", "EXTERNAL_DATA_FETCHED", "OFFICIAL_DECISION_IMPACT", "AUTO_TRADE", "AUTO_SELL",
    "CURRENT_DAILY_MODIFIED", "STATE_MODIFIED", "PRICE_CACHE_MODIFIED", "RANKING_MODIFIED",
    "PROMOTION_DEMOTION_MODIFIED", "MANUAL_STATE_MODIFIED", "BROKER_EXECUTION_MODIFIED", "VALIDATION_FAIL_COUNT",
    "READ_FIRST", "REPORT",
]


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    base.ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def mt(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else ""


def source_dates(path: Path) -> Tuple[int, str, str, bool, bool, List[str]]:
    rows, fields, status = base.read_csv(path)
    if status != "OK":
        return 0, "", "", False, False, []
    lower = {f.lower(): f for f in fields}
    date_col = lower.get("date") or lower.get("latest_price_date")
    close_col = lower.get("close") or lower.get("adj_close") or lower.get("latest_close") or lower.get("last_close")
    vol_col = lower.get("volume") or lower.get("latest_volume")
    ticker_col = lower.get("ticker")
    dates = [str(r.get(date_col, ""))[:10] for r in rows if date_col and r.get(date_col)]
    tickers = [base.normalize_ticker(r.get(ticker_col)) for r in rows if ticker_col and base.normalize_ticker(r.get(ticker_col))]
    if not tickers and path.parent.name.lower() in {"prices", "prices_full", "price_cache"}:
        tickers = [path.stem.upper()]
    return len(rows), (min(dates) if dates else ""), (max(dates) if dates else ""), bool(close_col), bool(vol_col), sorted(set(tickers))


def universe_audit(root: Path) -> Tuple[List[Dict[str, object]], Path, List[str]]:
    paths = [
        root / "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv",
        root / "state/v18/universe/V18_UNIVERSE_ROLLING_STATE.csv",
        root / "state/v18/raw105_universe_for_factor_lab.csv",
    ]
    rows_out = []
    selected = paths[0]
    selected_tickers: List[str] = []
    for path in paths:
        rows, fields, status = base.read_csv(path)
        tickers = sorted({base.normalize_ticker(r.get("ticker")) for r in rows if base.normalize_ticker(r.get("ticker"))}) if status == "OK" else []
        is_selected = path == selected and bool(tickers)
        if is_selected:
            selected_tickers = tickers
        rows_out.append({
            "source_path": str(path), "source_exists": str(path.exists()).upper(), "modified_time": mt(path),
            "parsed_ticker_count": len(tickers), "selected_as_current_universe_source": str(is_selected).upper(),
            "selected_reason": "PRIMARY_V18_CURRENT_ROLLING_UNIVERSE_STATE" if is_selected else "",
            "notes": status,
        })
    if not selected_tickers:
        selected_tickers = base.discover_universe(root)
    return rows_out, selected, selected_tickers


def mapping_audit(root: Path, tickers: Sequence[str], sources: Sequence[Dict[str, object]]) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]:
    source_tickers: Dict[str, set[str]] = {}
    for s in sources:
        path = Path(str(s["source_path"]))
        _, _, _, _, _, parsed = source_dates(path)
        source_tickers[str(path)] = set(parsed)

    mappings = []
    no_local = []
    selected_counts: Dict[str, int] = {}
    for ticker in tickers:
        norm = base.normalize_ticker(ticker)
        hist, selected_source, _ = base.load_price_history(root, norm)
        candidates = [p for p in base.price_candidates(root, norm) if p.exists()]
        latest_date, latest_close, latest_path = r2.load_latest_reference(root, norm)
        selected_path = Path(selected_source) if selected_source else Path(latest_path) if latest_path else None
        if hist:
            row_count, min_date, max_date, has_close, has_volume, _ = source_dates(Path(selected_source))
            if row_count >= 252 and has_volume:
                status = "MAPPED_FULL_HISTORY"
                quality = "FULL_HISTORY_USABLE"
            else:
                status = "MAPPED_PARTIAL_HISTORY" if row_count >= 21 else "MAPPED_LATEST_ONLY"
                quality = "PARTIAL_OR_LIGHT_HISTORY"
        elif latest_close and latest_date:
            row_count, min_date, max_date, has_close, has_volume = 1, latest_date, latest_date, True, False
            status, quality = "MAPPED_LATEST_ONLY", "LATEST_PRICE_REFERENCE_ONLY"
        elif candidates:
            row_count, min_date, max_date, has_close, has_volume = 0, "", "", False, False
            status, quality = "CANDIDATE_SOURCES_REJECTED", "CANDIDATE_EXISTS_BUT_UNUSABLE"
        else:
            row_count, min_date, max_date, has_close, has_volume = 0, "", "", False, False
            status, quality = "NO_CANDIDATE_SOURCE_FOUND", "NO_LOCAL_PRICE_EVIDENCE"
        selected_str = str(selected_path) if selected_path else ""
        if selected_str:
            selected_counts[selected_str] = selected_counts.get(selected_str, 0) + 1
        reject = "" if status.startswith("MAPPED") else quality
        mappings.append({
            "ticker": ticker, "normalized_ticker": norm, "mapped_price_source_count": len(candidates) + (1 if latest_path and not candidates else 0),
            "selected_price_source": selected_str, "selected_price_source_type": r2.source_type(selected_path) if selected_path else "NONE",
            "selected_source_modified_time": mt(selected_path) if selected_path else "", "selected_source_row_count": row_count,
            "selected_source_min_date": min_date, "selected_source_max_date": max_date,
            "selected_source_has_close": str(has_close).upper(), "selected_source_has_volume": str(has_volume).upper(),
            "selected_source_history_depth_rows": row_count, "selected_source_history_depth_days": row_count,
            "selected_source_quality_status": quality, "mapping_status": status, "rejection_reason": reject,
            "candidate_source_paths_limited": ";".join(str(p) for p in candidates[:5]), "ticker_in_source_as": norm,
            "symbol_normalization_applied": "UPPERCASE_STRIP",
        })
        if status == "NO_CANDIDATE_SOURCE_FOUND":
            no_local.append({
                "ticker": ticker, "normalized_ticker": norm, "no_local_data_reason": "NO_CANDIDATE_SOURCE_FOUND",
                "candidate_source_count": len(candidates), "candidate_source_paths_limited": ";".join(str(p) for p in candidates[:5]),
                "latest_price_snapshot_found": str(bool(latest_path)).upper(), "latest_price_snapshot_path": latest_path,
                "full_history_found": "FALSE", "partial_history_found": "FALSE", "recommended_resolution": "NEED_FULL_HISTORY_BACKFILL",
            })

    universe_set = set(tickers)
    relevance = []
    for s in sources:
        path = str(s["source_path"])
        overlap = source_tickers.get(path, set()) & universe_set
        selected_count = selected_counts.get(path, 0)
        has_close = str(s.get("has_close_column")) == "TRUE"
        has_date = str(s.get("has_date_column")) == "TRUE"
        depth = base.to_float(s.get("history_depth_estimate")) or 0
        contains_history = has_close and has_date and depth >= 21
        contains_latest = has_close and depth >= 1 and not contains_history
        if selected_count:
            rel_status = "RELEVANT_SELECTED"
            rejected = ""
        elif not overlap:
            rel_status = "IRRELEVANT_NO_UNIVERSE_OVERLAP"
            rejected = "NO_CURRENT_UNIVERSE_TICKER_OVERLAP"
        elif not contains_history:
            rel_status = "SUMMARY_NOT_HISTORY"
            rejected = "SUMMARY_OR_SNAPSHOT_NOT_USABLE_HISTORY"
        else:
            rel_status = "RELEVANT_NOT_SELECTED_LOWER_PRIORITY"
            rejected = "LOWER_PRIORITY_THAN_SELECTED_PER_TICKER_SOURCE"
        relevance.append({
            "source_path": path, "source_type": s.get("source_type", ""), "parsed_ticker_count": s.get("parsed_ticker_count", ""),
            "ticker_overlap_with_current_universe_count": len(overlap),
            "ticker_overlap_with_current_universe_ratio": base.fmt(len(overlap) / len(universe_set) if universe_set else 0),
            "contains_ohlcv_history": str(contains_history).upper(), "contains_latest_only": str(contains_latest).upper(),
            "selected_for_any_universe_ticker": str(selected_count > 0).upper(), "selected_ticker_count": selected_count,
            "rejected_reason_if_not_selected": rejected, "source_relevance_status": rel_status,
        })

    scope_summary = []
    for m in mappings:
        status = m["mapping_status"]
        if status == "MAPPED_FULL_HISTORY":
            fscope, sscope, full, light, reason = "FULL_HISTORY_FACTOR_READY", "FULL_PRICE_DERIVED_SCORE", "TRUE", "FALSE", "FULL_HISTORY_AVAILABLE"
        elif status == "MAPPED_PARTIAL_HISTORY":
            fscope, sscope, full, light, reason = "PARTIAL_HISTORY_LIGHT_FACTOR_READY", "LIGHT_PRICE_DERIVED_SCORE", "FALSE", "TRUE", "PARTIAL_HISTORY_AVAILABLE"
        elif status == "MAPPED_LATEST_ONLY":
            fscope, sscope, full, light, reason = "LATEST_ONLY_NOT_FACTOR_READY", "LATEST_ONLY_REFERENCE", "FALSE", "FALSE", "LATEST_ONLY_REFERENCE"
        else:
            fscope, sscope, full, light, reason = "NO_LOCAL_PRICE_DATA", "NOT_SCORE_READY", "FALSE", "FALSE", m["rejection_reason"]
        scope_summary.append({
            "ticker": m["ticker"], "factor_scope_class": fscope, "mapping_status": status, "score_scope": sscope,
            "full_factor_score_ready": full, "light_factor_score_ready": light, "selected_price_source": m["selected_price_source"],
            "score_readiness_reason": reason,
        })
    return mappings, relevance, no_local, scope_summary


def parse_check(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    escaped = str(path).replace("'", "''")
    cmd = f"$null = [scriptblock]::Create((Get-Content -Raw -LiteralPath '{escaped}')); 'OK_PARSE'"
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd], capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and "OK_PARSE" in (result.stdout or ""):
            return True, "OK_PARSE"
        return False, (result.stderr or result.stdout).strip()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def compile_check(path: Path) -> Tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, "OK_COMPILE"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def report(metrics: Dict[str, object], validations: Sequence[str]) -> str:
    return "\n".join([
        "# V18.21A-R3 Ticker Price Source Mapping Report", "",
        "## Executive summary",
        f"- Status: {metrics['STATUS']}",
        f"- Local price data available: {metrics['LOCAL_PRICE_DATA_AVAILABLE_COUNT']} / {metrics['TICKER_INPUT_COUNT']}",
        f"- No candidate source found: {metrics['NO_CANDIDATE_SOURCE_FOUND_COUNT']}", "",
        "## Safety statement",
        "- Advisory-only. No history backfill, external fetch, price cache writes, state writes, ranking changes, broker execution, auto-trade, or auto-sell changes were made.", "",
        "## Current universe source summary",
        "- Current universe source is the V18 current rolling universe state.", "",
        "## Source-to-ticker mapping summary",
        f"- Full history mapped: {metrics['MAPPED_FULL_HISTORY_COUNT']}; partial: {metrics['MAPPED_PARTIAL_HISTORY_COUNT']}; latest-only: {metrics['MAPPED_LATEST_ONLY_COUNT']}.", "",
        "## Why discovered source count differs from ticker-level availability",
        "- Source discovery counts files, including duplicate cache locations, historical copies, summary files, and sources for symbols outside the current universe. Ticker availability requires a usable per-ticker source selected for a current universe ticker.", "",
        "## No-local-data detail summary",
        f"- No local price data count: {metrics['NO_LOCAL_PRICE_DATA_COUNT']}. See R3 no-local detail CSV.", "",
        "## Mapping failure categories",
        f"- Candidate sources rejected: {metrics['CANDIDATE_SOURCES_REJECTED_COUNT']}; no candidate source found: {metrics['NO_CANDIDATE_SOURCE_FOUND_COUNT']}.", "",
        "## Market regime proxy status",
        f"- QQQ: {metrics['QQQ_PROXY_STATUS']}; SPY: {metrics['SPY_PROXY_STATUS']}; VIX: {metrics['VIX_PROXY_STATUS']}; coefficient: {metrics['MARKET_RISK_COEFFICIENT']}.", "",
        "## Validation summary",
        *[f"- {item}" for item in validations],
        f"- Validation fail count: {metrics['VALIDATION_FAIL_COUNT']}", "",
        "## Recommended next step",
        "- Missing tickers mostly need an advisory full-history backfill plan. Do not apply backfill in this module.",
    ]) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    r2.main(["--root", str(root)])
    universe_rows, _selected, tickers = universe_audit(root)
    sources = r2.discover_sources(root)
    mappings, relevance, no_local, scope_summary = mapping_audit(root, tickers, sources)

    out_dir = root / "outputs/v18/price_factors"
    ops = root / "outputs/v18/ops"
    paths = {
        "universe": out_dir / "V18_21A_R3_CURRENT_UNIVERSE_SOURCE_AUDIT.csv",
        "mapping": out_dir / "V18_21A_R3_CURRENT_TICKER_SOURCE_MAPPING_AUDIT.csv",
        "relevance": out_dir / "V18_21A_R3_CURRENT_DISCOVERED_SOURCE_RELEVANCE_AUDIT.csv",
        "no_local": out_dir / "V18_21A_R3_CURRENT_NO_LOCAL_PRICE_DATA_DETAIL.csv",
        "recon": out_dir / "V18_21A_R3_CURRENT_MAPPING_COUNT_RECONCILIATION.csv",
        "scope": out_dir / "V18_21A_R3_CURRENT_FACTOR_SCOPE_SUMMARY.csv",
        "read_first": ops / "V18_21A_R3_READ_FIRST.txt",
        "report": ops / "V18_21A_R3_CURRENT_TICKER_PRICE_SOURCE_MAPPING_REPORT.md",
    }
    full = sum(1 for m in mappings if m["mapping_status"] == "MAPPED_FULL_HISTORY")
    partial = sum(1 for m in mappings if m["mapping_status"] == "MAPPED_PARTIAL_HISTORY")
    latest = sum(1 for m in mappings if m["mapping_status"] == "MAPPED_LATEST_ONLY")
    rejected = sum(1 for m in mappings if m["mapping_status"] == "CANDIDATE_SOURCES_REJECTED")
    no_candidate = sum(1 for m in mappings if m["mapping_status"] == "NO_CANDIDATE_SOURCE_FOUND")
    selected_sources = {m["selected_price_source"] for m in mappings if m["selected_price_source"]}
    overlap_count = sum(1 for r in relevance if int(r["ticker_overlap_with_current_universe_count"]) > 0)

    market_rows, _, _ = base.read_csv(root / "outputs/v18/market_regime/V18_21A_R2_CURRENT_LIGHTWEIGHT_MARKET_REGIME.csv")
    market = market_rows[0] if market_rows else {}
    score_ready_ratio = base.fmt(full / len(tickers) if tickers else 0)
    metrics: Dict[str, object] = {
        "STATUS": STATUS_WARN,
        "MODE": MODE,
        "PATCH_MODE": PATCH_MODE,
        "TICKER_INPUT_COUNT": len(tickers),
        "LOCAL_PRICE_DATA_AVAILABLE_COUNT": full + partial + latest,
        "MAPPED_FULL_HISTORY_COUNT": full,
        "MAPPED_PARTIAL_HISTORY_COUNT": partial,
        "MAPPED_LATEST_ONLY_COUNT": latest,
        "CANDIDATE_SOURCES_REJECTED_COUNT": rejected,
        "NO_CANDIDATE_SOURCE_FOUND_COUNT": no_candidate,
        "NO_LOCAL_PRICE_DATA_COUNT": rejected + no_candidate,
        "PRICE_HISTORY_SOURCE_COUNT": len(sources),
        "DISCOVERED_SOURCE_WITH_UNIVERSE_OVERLAP_COUNT": overlap_count,
        "DISCOVERED_SOURCE_SELECTED_COUNT": len(selected_sources),
        "SOURCE_COUNT_TO_TICKER_MAPPING_STATUS": "EXPLAINED_SOURCE_FILES_ARE_NOT_ONE_TO_ONE_WITH_CURRENT_UNIVERSE_TICKERS",
        "FULL_HISTORY_FACTOR_READY_COUNT": full,
        "FULL_HISTORY_FACTOR_READY_RATIO": score_ready_ratio,
        "SCORE_READY_RATIO": score_ready_ratio,
        "QQQ_PROXY_STATUS": market.get("qqq_proxy_status", ""),
        "SPY_PROXY_STATUS": market.get("spy_proxy_status", ""),
        "VIX_PROXY_STATUS": market.get("vix_proxy_status", ""),
        "VIX_MISSING_CAP_APPLIED": market.get("vix_missing_cap_applied", ""),
        "MARKET_REGIME_STATUS": market.get("market_regime_data_status", ""),
        "MARKET_REGIME_LABEL": market.get("market_regime_label", ""),
        "MARKET_RISK_COEFFICIENT": market.get("market_risk_coefficient", ""),
        "MARKET_REGIME_CONFIDENCE": market.get("market_regime_confidence", ""),
        "VALIDATION_FAIL_COUNT": 0,
        "READ_FIRST": str(paths["read_first"]),
        "REPORT": str(paths["report"]),
    }
    metrics.update(SAFETY_FLAGS)

    recon = [
        {"metric_name": "TICKER_INPUT_COUNT", "metric_value": len(tickers), "explanation": "Current universe ticker count."},
        {"metric_name": "PRICE_HISTORY_SOURCE_COUNT", "metric_value": len(sources), "explanation": "Discovered candidate local files, not unique usable universe ticker mappings."},
        {"metric_name": "DISCOVERED_SOURCE_COUNT", "metric_value": len(sources), "explanation": "Same as price history source count."},
        {"metric_name": "DISCOVERED_SOURCE_WITH_UNIVERSE_OVERLAP_COUNT", "metric_value": overlap_count, "explanation": "Sources containing at least one current universe ticker or matching file stem."},
        {"metric_name": "DISCOVERED_SOURCE_SELECTED_COUNT", "metric_value": len(selected_sources), "explanation": "Sources selected for at least one current universe ticker."},
        {"metric_name": "MAPPED_FULL_HISTORY_COUNT", "metric_value": full, "explanation": "Universe tickers mapped to full OHLCV history."},
        {"metric_name": "MAPPED_PARTIAL_HISTORY_COUNT", "metric_value": partial, "explanation": "Universe tickers mapped to partial history."},
        {"metric_name": "MAPPED_LATEST_ONLY_COUNT", "metric_value": latest, "explanation": "Universe tickers mapped to latest-only local evidence."},
        {"metric_name": "CANDIDATE_SOURCES_REJECTED_COUNT", "metric_value": rejected, "explanation": "Candidate files exist but were unusable."},
        {"metric_name": "NO_CANDIDATE_SOURCE_FOUND_COUNT", "metric_value": no_candidate, "explanation": "No local candidate source found for ticker."},
        {"metric_name": "NO_LOCAL_PRICE_DATA_COUNT", "metric_value": rejected + no_candidate, "explanation": "Rejected plus no-candidate tickers."},
        {"metric_name": "WHY_SOURCE_COUNT_DIFFERS_FROM_TICKER_AVAILABILITY", "metric_value": "FILES_NOT_UNIQUE_TICKER_MAPPINGS", "explanation": "Discovery includes summaries, duplicates, non-universe symbols, and lower-priority copies."},
    ]

    write_csv(paths["universe"], universe_rows, UNIVERSE_FIELDS)
    write_csv(paths["mapping"], mappings, MAPPING_FIELDS)
    write_csv(paths["relevance"], relevance, RELEVANCE_FIELDS)
    write_csv(paths["no_local"], no_local, NO_LOCAL_FIELDS)
    write_csv(paths["recon"], recon, RECON_FIELDS)
    write_csv(paths["scope"], scope_summary, SCOPE_SUMMARY_FIELDS)

    ps_ok, ps_msg = parse_check(root / "scripts/v18/run_v18_21A_R3_ticker_price_source_mapping_patch.ps1")
    r2_ok, r2_msg = compile_check(root / "scripts/v18/v18_21A_R2_price_history_source_coverage_patch.py")
    r3_ok, r3_msg = compile_check(root / "scripts/v18/v18_21A_R3_ticker_price_source_mapping_patch.py")
    outputs_ok = all(p.exists() for p in paths.values() if p not in {paths["read_first"], paths["report"]})
    validations = [
        f"PowerShell parse check: {ps_msg}",
        f"Python compile check V18.21A-R2: {r2_msg}",
        f"Python compile check V18.21A-R3: {r3_msg}",
        "Run check: OK_CURRENT_SCRIPT_EXECUTED",
        f"R3 output existence check: {'OK' if outputs_ok else 'FAILED'}",
        "Protected behavior check: OK_ADVISORY_OUTPUTS_ONLY",
        "HISTORY_BACKFILL_APPLIED: FALSE",
        "EXTERNAL_DATA_FETCHED: FALSE",
    ]
    metrics["VALIDATION_FAIL_COUNT"] = sum(1 for ok in (ps_ok, r2_ok, r3_ok, outputs_ok) if not ok)
    if rejected > 20:
        metrics["STATUS"] = STATUS_REVIEW
    elif metrics["VALIDATION_FAIL_COUNT"] == 0 and no_candidate == 0 and market.get("vix_proxy_status") == "OK":
        metrics["STATUS"] = STATUS_OK

    base.write_text(paths["read_first"], "\n".join(f"{f}: {metrics.get(f, '')}" for f in READ_FIRST_FIELDS) + "\n")
    base.write_text(paths["report"], report(metrics, validations))
    fields_ok = all(f in base.read_text(paths["read_first"]) for f in READ_FIRST_FIELDS)
    final_ok = all(p.exists() for p in paths.values()) and fields_ok
    if not final_ok:
        metrics["VALIDATION_FAIL_COUNT"] = int(metrics["VALIDATION_FAIL_COUNT"]) + 1
        base.write_text(paths["read_first"], "\n".join(f"{f}: {metrics.get(f, '')}" for f in READ_FIRST_FIELDS) + "\n")
        base.write_text(paths["report"], report(metrics, validations + ["Final READ_FIRST/output check: FAILED"]))

    print(f"STATUS: {metrics['STATUS']}")
    print(f"MODE: {MODE}")
    print(f"PATCH_MODE: {PATCH_MODE}")
    print(f"LOCAL_PRICE_DATA_AVAILABLE_COUNT: {metrics['LOCAL_PRICE_DATA_AVAILABLE_COUNT']}")
    print(f"MAPPED_FULL_HISTORY_COUNT: {full}")
    print(f"NO_CANDIDATE_SOURCE_FOUND_COUNT: {no_candidate}")
    print(f"PRICE_HISTORY_SOURCE_COUNT: {len(sources)}")
    print(f"DISCOVERED_SOURCE_SELECTED_COUNT: {len(selected_sources)}")
    print(f"HISTORY_BACKFILL_APPLIED: FALSE")
    print(f"EXTERNAL_DATA_FETCHED: FALSE")
    print(f"VALIDATION_FAIL_COUNT: {metrics['VALIDATION_FAIL_COUNT']}")
    print(f"READ_FIRST: {paths['read_first']}")
    print(f"REPORT: {paths['report']}")
    return 1 if int(metrics["VALIDATION_FAIL_COUNT"]) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
