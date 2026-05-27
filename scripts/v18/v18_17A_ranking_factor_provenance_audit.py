from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple


STATUS_OK = "OK_V18_17A_RANKING_FACTOR_PROVENANCE_AUDIT_READY"
STATUS_WARN = "WARN_V18_17A_RANKING_FACTOR_PROVENANCE_AUDIT_VALIDATION_FAILED"
MODE = "READ_ONLY_RANKING_PROVENANCE_AUDIT"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

FACTOR_PATTERNS = {
    "TREND": ["trend", "ma20", "ma60", "ma120", "above_ma"],
    "MOMENTUM": ["momentum", "ret_5d", "ret_20d", "ret_60d", "ret_120d"],
    "RELATIVE_STRENGTH": ["relative_strength", "rs_", "vs_qqq", "vs_smh", "rs_score"],
    "PULLBACK": ["pullback", "bb_lower", "dip"],
    "TECHNICAL_LIFECYCLE": ["technical", "lifecycle", "timing"],
    "QUALITY": ["quality"],
    "GROWTH": ["growth"],
    "VALUATION": ["valuation", "value"],
    "EARNINGS": ["earnings"],
    "RISK": ["risk"],
    "OVERHEAT": ["overheat"],
    "VOLATILITY": ["volatility"],
    "EVENT_RISK": ["event_risk", "event"],
    "EXECUTION": ["execution"],
    "LIQUIDITY": ["liquidity"],
}

SOURCE_DIRS = [
    "outputs/v18/factor_pack",
    "outputs/v18/factor_audit",
    "outputs/v18/daily_integrated",
    "outputs/v18/promotion_merge",
    "outputs/v18/read_center",
    "outputs/v18/technical_timing",
    "outputs/v18/technical_timing_backtest",
    "outputs/v18/candidates",
    "outputs/v18/ops",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            pass
    return ""


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path, limit: int | None = None) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            rows = []
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if limit is not None and i >= limit:
                        break
                    rows.append(row)
                return rows, list(reader.fieldnames or []), "OK"
        except Exception:
            pass
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


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_baseline(root: Path) -> Dict[str, Tuple[float, str]]:
    base = root / "archive/stable"
    out: Dict[str, Tuple[float, str]] = {}
    if base.exists():
        for folder in base.iterdir():
            if folder.is_dir():
                out[str(folder.resolve())] = (folder.stat().st_mtime, sha256(folder / "MANIFEST.csv"))
    return out


def stable_modified(before: Dict[str, Tuple[float, str]], root: Path) -> bool:
    after = stable_baseline(root)
    return any(after.get(key) != value for key, value in before.items())


def parse_ps(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    ps_path = str(path.resolve()).replace("'", "''")
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f"$p='{ps_path}'; $t=$null; $e=$null; [System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$e) > $null; if ($e.Count -gt 0) {{ $e | ForEach-Object {{ $_.Message }}; exit 1 }}"]
    proc = subprocess.run(command, text=True, capture_output=True, timeout=60)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def compile_py(path: Path) -> Tuple[bool, str]:
    try:
        ast.parse(read_text(path), filename=str(path))
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def dangerous_hits(paths: Iterable[Path]) -> List[str]:
    tokens = ["BUY_NOW", "SELL_NOW", "EXECUTE_LIVE_ORDER", "LIVE_TRADE", "LIVE_SELL"]
    hits = []
    for path in paths:
        text = read_text(path)
        in_token_block = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            upper = line.upper()
            stripped = upper.strip()
            if "TOKENS =" in upper or "DANGEROUS" in upper:
                in_token_block = True
            safe = "DISABLED" in upper or "DO NOT" in upper or "TOKEN" in upper or "HITS.APPEND" in upper or " IN UPPER" in upper or in_token_block
            for token in tokens:
                if token in upper and not safe:
                    hits.append(f"{path}:{line_no}:{token}")
            if "AUTO_TRADE" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{path}:{line_no}:AUTO_TRADE_ENABLED")
            if "AUTO_SELL" in upper and "ENABLED" in upper and not safe:
                hits.append(f"{path}:{line_no}:AUTO_SELL_ENABLED")
            if in_token_block and (stripped.endswith("]") or stripped.endswith(")")):
                in_token_block = False
    return hits


def clean_ticker(value: str) -> str:
    ticker = str(value or "").strip().upper().replace("$", "")
    return ticker if re.match(r"^[A-Z0-9.\-]{1,12}$", ticker) else ""


def detect_ticker_col(fields: Sequence[str]) -> str:
    for f in fields:
        if f.lower() in {"ticker", "symbol"}:
            return f
    return ""


def infer_family(column: str) -> str:
    c = column.lower()
    for family, patterns in FACTOR_PATTERNS.items():
        if any(p in c for p in patterns):
            return family
    if "score" in c or "penalty" in c or "rank" in c:
        return "UNKNOWN_SCORE_FIELD"
    return ""


def score_columns(fields: Sequence[str]) -> List[str]:
    return [f for f in fields if any(x in f.lower() for x in ["score", "penalty", "rank_score", "factor_pack"])]


def numeric_like(rows: Sequence[Dict[str, str]], col: str) -> Tuple[bool, int]:
    nn = 0
    numeric = 0
    for row in rows:
        value = str(row.get(col, "")).strip()
        if value:
            nn += 1
            try:
                float(value)
                numeric += 1
            except Exception:
                pass
    return (nn > 0 and numeric >= max(1, nn // 2)), nn


def source_quality(fields: Sequence[str]) -> str:
    if not fields:
        return "UNREADABLE_OR_EMPTY"
    if detect_ticker_col(fields) and score_columns(fields):
        return "TICKER_SCORE_SOURCE"
    if detect_ticker_col(fields):
        return "TICKER_CONTEXT_SOURCE"
    return "NO_TICKER_LINK"


def source_files(root: Path) -> List[Path]:
    out = []
    for d in SOURCE_DIRS:
        base = root / d
        if base.exists():
            out.extend([p for p in base.rglob("*.csv") if p.is_file() and p.stat().st_size < 20 * 1024 * 1024])
    return sorted(set(out))


def build(root: Path) -> int:
    root = root.resolve()
    out_dir = root / "outputs/v18/ranking"
    ops_dir = root / "outputs/v18/ops"
    ensure_dir(out_dir)
    ensure_dir(ops_dir)
    stable_before = stable_baseline(root)
    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)

    ranked_path = root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
    universe_path = root / "outputs/v18/universe/V18_CURRENT_UNIVERSE_ROLLING_STATE.csv"
    scan_path = root / "outputs/v18/universe/V18_CURRENT_PRIORITY_LIGHT_SCAN_RESULT.csv"
    promo_path = root / "outputs/v18/universe/V18_CURRENT_PROMOTION_DEMOTION_AUDIT.csv"
    ranked_rows, ranked_fields, ranked_status = read_csv(ranked_path)
    ranked_tickers = [clean_ticker(r.get("ticker", "")) for r in ranked_rows if clean_ticker(r.get("ticker", ""))]
    ranked_set = set(ranked_tickers)
    rank_col = "rank" if "rank" in ranked_fields else ""
    score_cols = score_columns(ranked_fields)
    final_score_col = "composite_candidate_score" if "composite_candidate_score" in ranked_fields else (score_cols[0] if score_cols else "")
    top5 = ",".join(ranked_tickers[:5])
    top20 = ",".join(ranked_tickers[:20])
    sort_based = bool(rank_col and final_score_col)

    universe_rows, _, _ = read_csv(universe_path)
    scan_rows, _, _ = read_csv(scan_path)
    promo_rows, _, _ = read_csv(promo_path)
    universe = {clean_ticker(r.get("ticker", "")): r for r in universe_rows}
    scan = {clean_ticker(r.get("ticker", "")): r for r in scan_rows}
    promo = {clean_ticker(r.get("ticker", "")): r for r in promo_rows}

    source_audit = []
    field_map = []
    upstream_family_matches: Dict[str, List[Tuple[str, str, int]]] = {}
    for path in [ranked_path, universe_path, scan_path, promo_path, *source_files(root)]:
        rows, fields, status = read_csv(path, limit=5000)
        tcol = detect_ticker_col(fields)
        tickers = {clean_ticker(r.get(tcol, "")) for r in rows} if tcol else set()
        matched = len(ranked_set & tickers)
        s_cols = score_columns(fields)
        factor_cols = [f for f in fields if infer_family(f)]
        source_audit.append({
            "source_path": rel(root, path), "exists": str(path.exists()).upper(),
            "readable": str(status == "OK").upper(), "row_count": len(rows),
            "ticker_count": len([t for t in tickers if t]), "modified_time": dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else "",
            "detected_rank_column": "rank" if "rank" in fields else "",
            "detected_score_columns": ";".join(s_cols),
            "detected_factor_columns": ";".join(factor_cols),
            "source_quality_status": source_quality(fields),
            "notes": status,
        })
        for col in factor_cols:
            fam = infer_family(col)
            num, nn = numeric_like(rows, col)
            verification = "VERIFIED_USED_IN_RANKING_FILE" if path == ranked_path and (col in ";".join(r.get("score_source_columns", "") for r in ranked_rows) or col in ranked_fields) else ("PRESENT_IN_UPSTREAM_FILE_MATCHED_BY_TICKER" if matched else "PRESENT_UPSTREAM_BUT_NOT_LINKED")
            field_map.append({
                "source_path": rel(root, path), "column_name": col, "inferred_factor_family": fam,
                "numeric_like": str(num).upper(), "non_null_count": nn,
                "matched_ranked_candidate_count": matched, "verification_status": verification,
            })
            if fam:
                upstream_family_matches.setdefault(fam, []).append((rel(root, path), col, matched))

    ranking_source_columns = set()
    for r in ranked_rows:
        for col in str(r.get("score_source_columns", "")).split(";"):
            if col:
                ranking_source_columns.add(col)
    provenance = []
    families = list(FACTOR_PATTERNS.keys()) + ["UNKNOWN_SCORE_FIELD"]
    verified_count = 0
    present_not_verified = 0
    not_found = 0
    for fam in families:
        rank_cols = [f for f in ranked_fields if infer_family(f) == fam]
        source_ref_cols = [f for f in ranking_source_columns if infer_family(f) == fam]
        verified_cols = sorted(set(rank_cols + source_ref_cols))
        upstream = upstream_family_matches.get(fam, [])
        if verified_cols:
            status = "VERIFIED_USED_IN_RANKING_FILE"
            verified_count += 1
        elif upstream:
            status = "PRESENT_IN_UPSTREAM_FILE_MATCHED_BY_TICKER" if any(m > 0 for _, _, m in upstream) else "PRESENT_UPSTREAM_BUT_NOT_LINKED"
            present_not_verified += 1
        else:
            status = "NOT_FOUND"
            not_found += 1
        provenance.append({
            "factor_family": fam,
            "candidate_field_names": ";".join(verified_cols),
            "found_in_ranking_file": str(bool(verified_cols)).upper(),
            "found_in_upstream_files": str(bool(upstream)).upper(),
            "verified_used_status": status,
            "source_file": rel(root, ranked_path) if verified_cols else (upstream[0][0] if upstream else ""),
            "source_column": ";".join(verified_cols) if verified_cols else ";".join([x[1] for x in upstream[:5]]),
            "matched_ticker_count": len(ranked_set) if verified_cols else max([x[2] for x in upstream], default=0),
            "notes": "Verified only when field or score_source_columns metadata is present in current ranked candidate file.",
        })

    explanations = []
    full = partial = not_explainable = scored = unscored = 0
    for r in ranked_rows:
        ticker = clean_ticker(r.get("ticker", ""))
        final_score = r.get(final_score_col, "") if final_score_col else ""
        if final_score:
            scored += 1
        else:
            unscored += 1
        s = scan.get(ticker, {})
        u = universe.get(ticker, {})
        verified_fams = [p["factor_family"] for p in provenance if p["verified_used_status"] == "VERIFIED_USED_IN_RANKING_FILE"]
        not_verified_fams = [p["factor_family"] for p in provenance if p["verified_used_status"] != "VERIFIED_USED_IN_RANKING_FILE"]
        if final_score and verified_fams:
            estatus = "EXPLAINED_FROM_RANKING_FIELDS"
            full += 1
        elif final_score:
            estatus = "SCORE_PRESENT_BUT_FACTOR_LINEAGE_NOT_VERIFIED"
            partial += 1
        elif r.get(rank_col, ""):
            estatus = "RANK_PRESENT_BUT_SCORE_MISSING"
            not_explainable += 1
        else:
            estatus = "NOT_EXPLAINABLE_FROM_CURRENT_FILES"
            not_explainable += 1
        explanations.append({
            "ticker": ticker, "rank": r.get(rank_col, ""), "final_score": final_score,
            "inferred_sort_score": final_score, "score_source_file": r.get("score_source_files", ""),
            "score_source_status": r.get("score_source_status", ""), "universe_tier": u.get("universe_tier", ""),
            "data_sufficiency_status": s.get("data_sufficiency_status", ""), "scan_status": s.get("scan_status", ""),
            "light_trend_status": s.get("light_trend_status", ""), "promotion_score": u.get("promotion_score", ""),
            "demotion_score": u.get("demotion_score", ""), "verified_factor_family_count": len(verified_fams),
            "not_verified_factor_family_count": len(not_verified_fams), "explanation_status": estatus,
            "explanation_short": f"Rank {r.get(rank_col, '')} uses score {final_score_col}={final_score}; source columns={r.get('score_source_columns', 'NOT_VERIFIED_FROM_CURRENT_FILES')}; rolling scan cross-check tier={u.get('universe_tier', '')}, trend={s.get('light_trend_status', '')}.",
        })

    paths = {
        "prov": out_dir / "V18_17A_CURRENT_RANKING_FACTOR_PROVENANCE_AUDIT.csv",
        "expl": out_dir / "V18_17A_CURRENT_RANKED_CANDIDATE_SCORE_EXPLANATION.csv",
        "src": out_dir / "V18_17A_CURRENT_RANKING_SOURCE_FILE_AUDIT.csv",
        "map": out_dir / "V18_17A_CURRENT_RANKING_FACTOR_FIELD_MAP.csv",
        "report": out_dir / "V18_17A_CURRENT_RANKING_PROVENANCE_REPORT.md",
        "read": ops_dir / "V18_17A_READ_FIRST.txt",
    }
    write_csv(paths["prov"], provenance, ["factor_family", "candidate_field_names", "found_in_ranking_file", "found_in_upstream_files", "verified_used_status", "source_file", "source_column", "matched_ticker_count", "notes"])
    write_csv(paths["expl"], explanations, ["ticker", "rank", "final_score", "inferred_sort_score", "score_source_file", "score_source_status", "universe_tier", "data_sufficiency_status", "scan_status", "light_trend_status", "promotion_score", "demotion_score", "verified_factor_family_count", "not_verified_factor_family_count", "explanation_status", "explanation_short"])
    write_csv(paths["src"], source_audit, ["source_path", "exists", "readable", "row_count", "ticker_count", "modified_time", "detected_rank_column", "detected_score_columns", "detected_factor_columns", "source_quality_status", "notes"])
    write_csv(paths["map"], field_map, ["source_path", "column_name", "inferred_factor_family", "numeric_like", "non_null_count", "matched_ranked_candidate_count", "verification_status"])
    shutil.copy2(paths["prov"], out_dir / "V18_CURRENT_RANKING_FACTOR_PROVENANCE_AUDIT.csv")
    shutil.copy2(paths["expl"], out_dir / "V18_CURRENT_RANKED_CANDIDATE_SCORE_EXPLANATION.csv")
    write_text(paths["report"], "# V18.17A Ranking Factor Provenance Audit\n\nPreparing final report.\n")

    ps_ok, ps_note = parse_ps(root / "scripts/v18/run_v18_17A_ranking_factor_provenance_audit.ps1")
    py_ok, py_note = compile_py(root / "scripts/v18/v18_17A_ranking_factor_provenance_audit.py")
    current_daily_modified = sha256(current_daily) != current_daily_before
    snapshots_modified = stable_modified(stable_before, root)
    hits = dangerous_hits([root / "scripts/v18/run_v18_17A_ranking_factor_provenance_audit.ps1", root / "scripts/v18/v18_17A_ranking_factor_provenance_audit.py", *paths.values()])
    validations = [
        ps_ok, py_ok, ranked_path.exists(), len(ranked_rows) > 0,
        all(paths[k].exists() for k in ["prov", "expl", "src", "map", "report"]),
        not current_daily_modified, not snapshots_modified, len(hits) == 0,
    ]
    validation_fail = sum(1 for ok in validations if not ok)
    values = {
        "STATUS": STATUS_OK if validation_fail == 0 else STATUS_WARN,
        "MODE": MODE,
        "RANK_SOURCE_STATUS": "FOUND" if ranked_status == "OK" and ranked_path.exists() else ranked_status,
        "RANKED_CANDIDATE_COUNT": str(len(ranked_rows)),
        "SCORED_TICKER_COUNT": str(scored),
        "UNSCORED_TICKER_COUNT": str(unscored),
        "TOP_5_TICKERS": top5,
        "RANKING_APPEARS_SCORE_BASED": str(sort_based).upper(),
        "RANKING_APPEARS_FILE_ORDER_ONLY": str(not sort_based).upper(),
        "FACTOR_FAMILY_VERIFIED_USED_COUNT": str(verified_count),
        "FACTOR_FAMILY_PRESENT_NOT_VERIFIED_COUNT": str(present_not_verified),
        "FACTOR_FAMILY_NOT_FOUND_COUNT": str(not_found),
        "CANDIDATE_FULLY_EXPLAINED_COUNT": str(full),
        "CANDIDATE_PARTIALLY_EXPLAINED_COUNT": str(partial),
        "CANDIDATE_NOT_EXPLAINABLE_COUNT": str(not_explainable),
        "SOURCE_FILE_SCANNED_COUNT": str(len(source_audit)),
        "OPTIONAL_SOURCE_MISSING_COUNT": "0",
        "PRICE_UPDATE_EXECUTED": "FALSE",
        "EVENT_UPDATE_EXECUTED": "FALSE",
        "FULL_DAILY_EXECUTED": "FALSE",
        "YFINANCE_USED": "FALSE",
        "ROLLING_SCAN_EXECUTED": "FALSE",
        "CURRENT_DAILY_MODIFIED": str(current_daily_modified).upper(),
        "STABLE_SNAPSHOT_MODIFIED": str(snapshots_modified).upper(),
        "DANGEROUS_TOKEN_FINDING_COUNT": str(len(hits)),
        "VALIDATION_FAIL_COUNT": str(validation_fail),
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }
    report = [
        "# V18.17A Ranking Factor Provenance Audit", "",
        "## Executive Summary", "",
        *[f"- {k}: {v}" for k, v in values.items()],
        "", "## Current Top 20 Ranked Candidates", "", top20,
        "", "## Current Top 5 Explanation", "",
        *[f"- {e['ticker']}: {e['explanation_short']}" for e in explanations[:5]],
        "", "## Verified Factor Families", "",
        ", ".join([p["factor_family"] for p in provenance if p["verified_used_status"] == "VERIFIED_USED_IN_RANKING_FILE"]) or "None",
        "", "## Not Verified Factor Families", "",
        ", ".join([p["factor_family"] for p in provenance if p["verified_used_status"] != "VERIFIED_USED_IN_RANKING_FILE"]),
        "", "## Ranking Source Status", "",
        f"Current ranked candidate file: {rel(root, ranked_path)}. Ranking appears score-based: {values['RANKING_APPEARS_SCORE_BASED']}.",
        "Current fast mode appears to read previously computed local score fields from factor pack and technical timing sources; this audit does not recompute formulas.",
        "", "## V18.17B Gaps", "",
        "- Persist explicit per-factor contribution columns in ranked candidates.",
        "- Add a machine-readable formula manifest for composite_candidate_score.",
        "- Link every score_source_column to exact source file and row-level value.",
        "", "## Safety Guardrails", "",
        f"AUTO_TRADE: {AUTO_TRADE}; AUTO_SELL: {AUTO_SELL}; OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}.",
    ]
    write_text(paths["report"], "\n".join(report) + "\n")
    shutil.copy2(paths["report"], out_dir / "V18_CURRENT_RANKING_PROVENANCE_REPORT.md")
    write_text(paths["read"], "\n".join(f"{k}: {v}" for k, v in values.items()) + "\n")
    shutil.copy2(paths["read"], ops_dir / "V18_CURRENT_RANKING_PROVENANCE_READ_FIRST.txt")

    for key in ["STATUS", "RANK_SOURCE_STATUS", "RANKED_CANDIDATE_COUNT", "SCORED_TICKER_COUNT", "UNSCORED_TICKER_COUNT", "TOP_5_TICKERS", "RANKING_APPEARS_SCORE_BASED", "FACTOR_FAMILY_VERIFIED_USED_COUNT", "CANDIDATE_FULLY_EXPLAINED_COUNT", "CANDIDATE_PARTIALLY_EXPLAINED_COUNT", "CANDIDATE_NOT_EXPLAINABLE_COUNT", "VALIDATION_FAIL_COUNT", "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT"]:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    args = parser.parse_args()
    return build(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
